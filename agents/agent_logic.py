import sys
sys.path.append("/Users/mayureshmuley/Desktop/Urban_hcf")
from server.geocode import run_lst_model, get_feature_info
from agents.counterfactual import apply_counterfactuals

def run_urbanhcf_query(lat, lon, feature_name, change_value):
    """
    This functions runs the query to modify the feature at the given lat, lon
    and returns the baseline and counterfactual LST predictions.
    We use this to calculate the Urban heat island effect of the feature change,
    in that particular location.
    
    :param lat: latitude of the location
    :param lon: longitude of the location
    :param feature_name: name of the feature to modify
    :param change_value: value to apply to the feature
    """
    bands_info, features_data = get_feature_info(lat, lon)
    base_pred = run_lst_model(features_data, bands_info)

    cf_features = apply_counterfactuals(features_data, feature_name, change_value)
    cf_pred = run_lst_model(cf_features, bands_info)
    return {
        "baseline": base_pred,
        "counterfactual": cf_pred,
        "delta": [[cf - bp for cf, bp in zip(cf_row, bp_row)] for cf_row, bp_row in zip(cf_pred['data'], base_pred['data'])]
    }

# if __name__ == "__main__":
#     # Example usage
#     lat, lon = 34.0522, -118.2437  # Los Angeles
#     feature_name = "NDVI"
#     change_value = {"type": "add", "value": 0.1}

#     result = run_urbanhcf_query(lat, lon, feature_name, change_value)
#     print(result)