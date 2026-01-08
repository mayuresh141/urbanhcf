import sys
sys.path.append("/Users/mayureshmuley/Desktop/Urban_hcf")

from typing import Any
import requests
import rasterio
from mcp.server.fastmcp import FastMCP
from pyproj import Transformer
import math
import lightgbm as lgb
from agents.counterfactual import apply_counterfactuals
import numpy as np
import pandas as pd
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
        "coordinates": [[
            [min_lon, min_lat],
            [min_lon, max_lat],
            [max_lon, max_lat],
            [max_lon, min_lat],
            [min_lon, min_lat]
        ]]
    }

def load_urban_mask(mask_path):
    with rasterio.open(mask_path) as src:
        mask = src.read(1)
    return mask

def compute_urban_mean_lst(lst_preds, urban_mask_data):
    # Ensure numpy arrays
    lst_preds = np.asarray(lst_preds)
    urban_mask_data = np.asarray(urban_mask_data)

    # Squeeze singleton dimensions
    if lst_preds.ndim == 3:
        lst_preds = np.squeeze(lst_preds)

    if lst_preds.shape != urban_mask_data.shape:
        raise ValueError(
            f"Shape mismatch: lst_preds {lst_preds.shape}, "
            f"urban_mask {urban_mask_data.shape}"
        )

    # Convert mask to boolean
    urban_pixels = urban_mask_data > 0

    if not np.any(urban_pixels):
        raise ValueError("Urban mask contains no urban pixels")

    urban_mean = np.nanmean(lst_preds[urban_pixels])
    return urban_mean

def compute_uhi(lst_preds, urban_mask):
    urb_mask_path = "data/LA_urban_mask.tif"
    urban_mask = load_urban_mask(urb_mask_path)
    urban_mean = compute_urban_mean_lst(lst_preds, urban_mask)
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

@mcp.tool()
def bbox_from_latlon(lat: float, lon: float, buffer_km: float = 5) -> Any:
    return bbox_from_point(lat, lon, buffer_km)

@mcp.tool()
def get_feature_info(lat: float, lon: float) -> Any:
    # Example feature info retrieval (mocked for demonstration)
    tif_path = "data/LA_NDVI_SPH_2022_2023.tif"
    with rasterio.open(tif_path) as src:
        # Convert lat/lon → row/col
        row, col = src.index(lon, lat)

        data = src.read()
        feature_info = {
            'NDVI': data[0][row, col],
            'EVI': data[1][row, col],
            'sph': data[2][row, col],
            'pr': data[3][row, col],
            'impervious_descriptor': data[4][row, col],
            'landcover': data[5][row, col],
            'forecast_albedo': data[6][row, col],
            'built_height': data[7][row, col],
            'elevation': data[8][row, col],
            'LST_1KM': data[9][row, col]
        }

        return feature_info, data

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
    "data": pred_map.tolist(),  # 2D list of values
    "crs": "EPSG:3857",  # coordinate reference system
    "units": "Kelvin"     # very important
    }

# TO DO: write a Compute UHI effect tool

@mcp.tool()
def analyze_uhi_effect(lat: float, lon: float, feature_name: str='none', change_value: dict=None, cf_data:bool=False) -> Any:
    """
    This tool is used to calculate the Urban Heat Island(UHI) effect
    by running a baseline and counterfactual LST prediction based on
    modifying a specific feature at the given latitude and longitude.
    This will return the UHI data for that region. If no feature name to
    modify is provided, it will only return the baseline UHI data.
    
    :param lat: latitude of the location
    :param lon: longitude of the location
    :param feature_name: name of the feature to modify
    change_value: {
            "type": "divide | "multiply",
            "value": percentage of change (e.g., 1.2 for 20% increase)
        }
        :param cf_data: True if counterfactual data is available(e.g., feature_name and change_value provided)
    :return: dict with baseline and counterfactual UHI data(if cf_data is True)
             else only baseline UHI data
    """
    bands_info, features_data = get_feature_info(lat, lon)
    urb_mask_path = "data/LA_urban_mask.tif"
    urban_mask = load_urban_mask(urb_mask_path)

    lst_base = run_lst_model(features_data, bands_info)
    uhi_base = compute_uhi(lst_base, urban_mask)
    if cf_data:
        cf_features = apply_counterfactuals(features_data, feature_name, change_value)
        lst_cf = run_lst_model(cf_features, bands_info)
        uhi_cf = compute_uhi(lst_cf, urban_mask)
        delta_uhi = uhi_cf - uhi_base
    else:
        uhi_cf = None
        delta_uhi = None
    return {
        "lst": np.nanmean(lst_base['data']),
        "uhi": np.nanmean(uhi_base),
        "counterfactual_uhi": np.nanmean(uhi_cf) if uhi_cf is not None else None,
        "delta_uhi": np.nanmean(delta_uhi) if delta_uhi is not None else None,
    }

def main():
    # Initialize and run the server
    mcp.run(transport="stdio")
    # mcp.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()