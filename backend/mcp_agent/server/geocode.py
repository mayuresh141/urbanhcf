import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from typing import Any
import requests
import rasterio
from rasterio.windows import from_bounds
from mcp.server.fastmcp import FastMCP
from pyproj import Transformer
import math
import lightgbm as lgb
from mcp_agent.agents.counterfactual import apply_counterfactuals
import numpy as np
import pandas as pd
import os
import json
import pickle
import shutil
from app.redis_client import get_redis_client

import logging
import traceback

logger = logging.getLogger("mcp.tools.analyze_uhi_effect")
logger.setLevel(logging.DEBUG)

# Initialize FastMCP server
mcp = FastMCP("geocode")    
model = lgb.Booster(model_file="models/lst_model.txt")


def bbox_from_point(lat, lon, buffer_km=5):

    lat_buffer = buffer_km / 111.0
    lon_buffer = buffer_km / (111.0 * math.cos(math.radians(lat)))

    min_lon = lon - lon_buffer
    min_lat = lat - lat_buffer
    max_lon = lon + lon_buffer
    max_lat = lat + lat_buffer
    return {
        "type": "Polygon",
        "coordinates": [min_lon, min_lat, max_lon, max_lat]
    }

def load_urban_mask(mask_path):
    with rasterio.open(mask_path) as src:
        mask = src.read(1)
    return mask

def compute_urban_mean_lst(lst_preds, urban_mask_path, bbox):
    # Ensure numpy arrays
    lst_preds = np.asarray(lst_preds)

    # Squeeze singleton dimensions
    if lst_preds.ndim == 3:
        lst_preds = np.squeeze(lst_preds)

    with rasterio.open(urban_mask_path) as src:
        window = from_bounds(
            *bbox,
            transform=src.transform
        )
        urban_mask_data = src.read(1, window=window)

    if lst_preds.shape != urban_mask_data.shape:
        raise ValueError(
            f"Shape mismatch after clipping: "
            f"lst_preds {lst_preds.shape}, "
            f"urban_mask {urban_mask_data.shape}"
        )

    rural_pixels = urban_mask_data > 0
    urban_pixels = urban_mask_data==0
    
    if rural_pixels.size==0:
        urban_mean = float(np.nanmean(lst_preds[rural_pixels]))
    else:
        urban_mean = np.percentile(lst_preds[urban_pixels], 25),
    return urban_mean

def prepare_geojson_layer(arr, name="Layer"):
    """
    Converts an ndarray to GeoJSON (or keeps as GeoJSON if already) 
    and adds summary stats for LLM context.
    """
    # Here arr is your ndarray or already geojson
    geojson_data = arr  # convert to geojson if needed
    
    # Compute stats
    mean_val = np.nanmean(arr)
    max_val = np.nanmax(arr)
    min_val = np.nanmin(arr)
    
    return {
        "data": geojson_data,
        "mean": float(mean_val),
        "max": float(max_val),
        "min": float(min_val),
        "name": name
    }

def compute_uhi(lst_preds, urban_mask, bbox):
    """
    Computes UHI for the bbox region if the urbanmask
    and lst predictions are given.
    This is called if UHI map is needed.
    """
    urban_mean = compute_urban_mean_lst(lst_preds, urban_mask, bbox)
    uhi_map = lst_preds - urban_mean
    return uhi_map


@mcp.tool()
def get_geometry(location: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if "results" not in data:
        return {"error": "Location not found"}

    loc = data["results"][0]
    return {
        "lat": loc["latitude"],
        "lon": loc["longitude"],
        "name": loc["name"],
        "country": loc.get("country"),
        "admin1": loc.get("admin1")
    }

def bbox_from_latlon(lat: float, lon: float, buffer_km: float = 5) -> Any:
    # Increase buffer by 2, if the  compute_urban_mean_lst fails
    return bbox_from_point(lat, lon, buffer_km)

@mcp.tool()
def get_feature_info(lat: float, lon: float) -> Any:
    # Example feature info retrieval (mocked for demonstration)
    tif_path = "data/LA_NDVI_SPH_2022_2023.tif"
    bbox_dict = bbox_from_latlon(lat, lon)
    bbox = bbox_dict['coordinates']
    with rasterio.open(tif_path) as src:
        window = from_bounds(
            left=bbox[0],
            bottom=bbox[1],
            right=bbox[2],
            top=bbox[3],
            transform=src.transform
        )

        # Read only the bbox region
        data = src.read(window=window)
        feature_info = {
        'NDVI': float(np.nanmean(data[0])),
        'EVI': float(np.nanmean(data[1])),
        'sph': float(np.nanmean(data[2])),
        'pr': float(np.nanmean(data[3])),
        'impervious_descriptor': float(np.nanmean(data[4])),
        'landcover': float(np.nanmean(data[5])),
        'forecast_albedo': float(np.nanmean(data[6])),
        'built_height': float(np.nanmean(data[7])),
        'elevation': float(np.nanmean(data[8])),
        'LST_1KM': float(np.nanmean(data[9]))
        }

        return feature_info, data, bbox

@mcp.tool()
def run_lst_model(feature_data: dict, feature_bands_info: dict):
    """
    Run trained LST model on extracted regional features.
    """
    feature_order = [
        "NDVI", "EVI", "sph", "pr",
        "impervious_descriptor", "landcover", "forecast_albedo", "built_height", "elevation"
    ]
    X = feature_data[:-1,:,:]
    num_features, H, W = X.shape # Exclude LST band
    X_feat = X.reshape(num_features, -1).T
    missing = set(feature_order) - set(feature_bands_info.keys())

    if missing:
        raise ValueError(f"Missing required features: {missing}")
    
    pred = model.predict(X_feat)
    pred_map = pred.reshape(H, W)
    
    return {
    "data": pred_map,  # 2D list of values
    "crs": "EPSG:3857",  # coordinate reference system
    "units": "Kelvin"     # very important
    }

def save_numpy(path: str, array):
    if array is None:
        return
    np.save(path, array)

@mcp.tool()
def analyze_uhi_effect(lat: float, lon: float, run_id: str, redis_url: str, feature_name: str='none', change_value: dict=None, cf_data:bool=False) -> dict:
    """
    This is the final tool, any valid result should be returned, no further calling needed.
    This tool is used to calculate the Urban Heat Island(UHI) effect
    by running a baseline and counterfactual LST prediction based on
    modifying a specific feature at the given latitude and longitude.
    This will return the UHI data for that region. If no feature name to
    modify is provided, it will only return the baseline UHI data and cf_data will be False.
    For eg: if feature name and change_value is None, then only cf_data= and change_value is None.
    
    :param lat: latitude of the location
    :param lon: longitude of the location
    :param feature_name: name of the feature to modify
    :param run_id: run id of the the job started.
    :param redis_url: the redis client url.
    change_value: None or {
            "type": "divide | "multiply",
            "value": percentage of change (e.g., 1.2 for 20% increase)
        }
        :param cf_data: True if counterfactual data is available(e.g., feature_name and change_value provided)
    Returns:
    dict:
        "geojson":
            "lst": nd.array,
            "uhi": nd.array
            "counterfactual_uhi":nd.array
            "delta_uhi":nd.array
        "bbox" : list(floats)
    """
    try:
        bands_info, features_data, bbox = get_feature_info(lat, lon)
        urb_mask_path = "data/Rural_mask_4326.tif"

        lst_base = run_lst_model(features_data, bands_info)
        uhi_base = compute_uhi(lst_base['data'], urb_mask_path, bbox)
        if cf_data:
            cf_features = apply_counterfactuals(features_data, feature_name, change_value)
            lst_cf = run_lst_model(cf_features, bands_info)
            uhi_cf = compute_uhi(lst_cf['data'], urb_mask_path, bbox)
            delta_uhi = uhi_cf - uhi_base
        else:
            uhi_cf = None
            delta_uhi = None
        
        payload = {
        "lst": lst_base['data'].tolist(),      # convert numpy arrays to lists
        "uhi": uhi_base.tolist(),
        "counterfactual_uhi": uhi_cf.tolist() if uhi_cf is not None else None,
        "delta_uhi": delta_uhi.tolist() if delta_uhi is not None else None,      # scalar, ok
        "bbox": bbox                           # dict, ok
         }
        print("redis url inside geocode", os.getenv("REDIS_URL"))
        redis_client = get_redis_client(redis_url)
        redis_client.setex(
            f"uhi:{run_id}",
            900,  # TTL = 15 minutes
            json.dumps(payload)
        )
            
        return {
            "geojson": {
                "lst": np.nanmean(lst_base['data']) if lst_base['data'] is not None else np.nan,
                "uhi": np.nanmean(uhi_base) if uhi_base is not None else np.nan,
                "counterfactual_uhi": np.nanmean(uhi_cf) if uhi_cf is not None else np.nan,
                "delta_uhi": np.nanmean(delta_uhi) if delta_uhi is not None else np.nan
            },
            "bbox": bbox
        }
    except Exception as e:
        logger.error("❌ analyze_uhi_effect failed")
        logger.error(str(e))
        logger.error(traceback.format_exc())
        raise


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")
    # mcp.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()