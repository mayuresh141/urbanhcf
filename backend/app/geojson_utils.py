import numpy as np
from shapely.geometry import box, mapping

def ndarrays_to_geojson(data_dict):
    import numpy as np
    from shapely.geometry import box, mapping

    lst = np.array(data_dict.get("lst"))
    uhi = np.array(data_dict.get("uhi"))
    counterfactual_uhi = data_dict.get("counterfactual_uhi")
    if counterfactual_uhi is not None:
        counterfactual_uhi = np.array(counterfactual_uhi)
    delta_uhi = data_dict.get("delta_uhi")
    if delta_uhi is not None:
        delta_uhi = np.array(delta_uhi)
    bbox = data_dict.get("bbox")

    H, W = lst.shape
    min_lon, min_lat, max_lon, max_lat = bbox
    lon_step = (max_lon - min_lon) / W
    lat_step = (max_lat - min_lat) / H

    features = []

    for i in range(H):
        for j in range(W):
            cell_min_lon = min_lon + j * lon_step
            cell_max_lon = cell_min_lon + lon_step
            cell_max_lat = max_lat - i * lat_step
            cell_min_lat = cell_max_lat - lat_step

            geom = box(cell_min_lon, cell_min_lat, cell_max_lon, cell_max_lat)

            feature = {
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {
                    "lst": float(lst[i, j]),
                    "uhi": float(uhi[i, j]),
                    "counterfactual_uhi": float(counterfactual_uhi[i, j]) if counterfactual_uhi is not None else None,
                    "delta_uhi": float(delta_uhi[i, j]) if delta_uhi is not None else None,
                },
            }
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }

def format_backend_response(geojson_fc):
    """
    geojson_fc: FeatureCollection returned by ndarrays_to_geojson
    """

    if not isinstance(geojson_fc, dict) or geojson_fc.get("type") != "FeatureCollection":
        return {
            "geojson": None
        }
    
    return {
        "geojson": geojson_fc
    }
