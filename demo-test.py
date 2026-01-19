import rasterio
import joblib
import backend.utils as utils
import pandas as pd
import lightgbm as lgb
import numpy as np
import numpy as np
import folium
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import base64
from io import BytesIO
from mcp.server.geocode import compute_uhi, load_urban_mask, compute_urban_mean_lst, get_feature_info, analyze_uhi_effect
from mcp.agents.counterfactual import apply_counterfactuals

model = lgb.Booster(model_file="models/lst_model.txt")

def compute_uhi(lst_preds, urban_mask):
    urban_mean = compute_urban_mean_lst(lst_preds, urban_mask)
    uhi_map = lst_preds - urban_mean
    return uhi_map

def run_lst_model(feature_data: dict) -> dict:
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
    print(X_feat.shape)
    # missing = set(feature_order) - set(feature_info.keys())
    # if missing:
    #     raise ValueError(f"Missing required features: {missing}")
    
    pred = model.predict(X_feat)
    pred_map = pred.reshape(H, W)
    print(pred_map.shape)
    return {
    "data": pred_map,  # 2D list of values
    "crs": "EPSG:4326",  # coordinate reference system
    "units": "Kelvin"     # very important
    }

def visualize_uhi_folium(
    uhi_map,
    uhi_cf,
    reference_tif,
    output_html="outputs/maps/uhi_comparison.html"
):
    delta_uhi = uhi_cf - uhi_map

    with rasterio.open(reference_tif) as src:
        bounds = src.bounds
        center = [(bounds.top + bounds.bottom) / 2,
                  (bounds.left + bounds.right) / 2]

    m = folium.Map(location=center, zoom_start=9, tiles="cartodbpositron")

    layers = {
        "Baseline UHI (°C)": (uhi_map, "YlOrRd"),
        "Counterfactual UHI (°C)": (uhi_cf, "YlOrRd"),
        "ΔUHI (CF − Base) (°C)": (delta_uhi, "RdYlBu_r")
    }

    for name, (arr, cmap) in layers.items():
        png = array_to_png(arr, cmap=cmap)

        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{png}",
            bounds=[
                [bounds.bottom, bounds.left],
                [bounds.top, bounds.right],
            ],
            opacity=0.7,
            name=name,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(output_html)

def array_to_png(arr, vmin=None, vmax=None, cmap="RdYlBu_r"):
    arr = np.ma.masked_invalid(arr)

    if vmin is None:
        vmin = np.nanpercentile(arr, 5)
    if vmax is None:
        vmax = np.nanpercentile(arr, 95)

    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    cmap = cm.get_cmap(cmap)

    rgba = cmap(norm(arr))

    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    ax.axis("off")
    ax.imshow(rgba)

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    return base64.b64encode(buf.read()).decode("utf-8")


if __name__ == "__main__":
    # Initialize and run the server
    lat, lon = 33.7455, -117.8677  # Los Angeles coordinates
    # bands_info, features_data = get_feature_info(lat, lon)

    # print(bands_info, features_data)
    # features_data = utils.rasterio_open('data/LA_NDVI_SPH_2022_2023.tif')
    # lst_base = run_lst_model(features_data.data)
    # # print(lst_base['data'].shape)
    # urb_mask_path = "data/LA_urban_mask_4326.tif"
    # urban_mask = load_urban_mask(urb_mask_path)
    # uhi_base = compute_uhi(lst_base['data'], urban_mask)
    # # print(result['data'].nanmean())
    # print(np.nanmean(uhi_base))

    # cf_features = apply_counterfactuals(features_data.data, 'NDVI', {"type": 'multiply', "value": 1.1})
    # lst_cf = run_lst_model(cf_features)
    # print("lst_cf", lst_cf['data'].shape)
    # uhi_cf = compute_uhi(lst_cf['data'], urban_mask)
    # delta_uhi = uhi_cf - uhi_base

    # print(np.nanmean(delta_uhi))
    result = analyze_uhi_effect(lat, lon, "abcd")
    print(result)
    
    # visualize_uhi_folium(uhi_base, uhi_cf, 'data/LA_NDVI_SPH_2022_2023.tif')