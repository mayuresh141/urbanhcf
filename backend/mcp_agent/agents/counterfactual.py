import numpy as np
import rasterio

def apply_counterfactuals(data:np.ndarray, feature_name: str, change_value: dict) -> np.ndarray:
    """
    Apply counterfactual change to a feature slice in a 3D feature tensor.

    Args:
        data: np.ndarray of shape (F, H, W)
        feature_map: dict mapping feature_name -> index
        feature_name: feature to modify
        change_value: {
            "type": "divide" | "multiply",
            "value": float
        }

    Returns:
        New np.ndarray with counterfactual applied
    """
    feature_map = {
            'NDVI': 0,
            'EVI': 1,
            'sph': 2,
            'pr': 3,
            'impervious_descriptor': 4,
            'landcover': 5,
            'forecast_albedo': 6,
            'built_height': 7,
            'elevation': 8,
            'LST_1KM': 9
        }

    if data.ndim != 3:
        raise ValueError("data must be a 3D array (F, H, W)")

    if feature_name not in feature_map:
        raise ValueError(f"Feature '{feature_name}' not found in feature_map")

    if "type" not in change_value or "value" not in change_value:
        raise ValueError("change_value must contain 'type' and 'value'")
       
    cf_type = change_value["type"]
    value = change_value["value"]
    feature_idx = feature_map[feature_name]

    # Copy to avoid in-place modification
    new_data = data.copy()

    feature_slice = new_data[feature_idx, :, :]


    if cf_type == "divide":
        new_data[feature_idx, :, :] = feature_slice / value

    elif cf_type == "multiply":
        new_data[feature_idx, :, :] = feature_slice * value

    else:
        raise ValueError(f"Unsupported counterfactual type: {cf_type}")

    return new_data

# if __name__ == "__main__":
#     # Example usage
#     tif_path = "data/LA_NDVI_SPH_2022_2023.tif"
#     with rasterio.open(tif_path) as src:
#         data = src.read()

#     change = {"type": "add", "value": 0.1}
#     new_data = apply_counterfactuals(data, "NDVI", change)
#     print("Original NDVI mean:", np.nanmean(data[0]))
#     print("Counterfactual NDVI mean:", np.nanmean(new_data[0]))