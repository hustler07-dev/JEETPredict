import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

# Globals for artifacts
__columns = None             # original column names (list)
__columns_lower = None       # lowercase for lookups
__locations = None           # location names (original case)
__locations_lower = None     # lowercase locations for lookup
__model = None

def load_artifacts(columns_path: str = './Columnsnew.json', model_path: str = './Real Estate Data V21.pickle'):
    """
    Load columns.json and the pickled model into module globals.
    Safe to call multiple times.
    """
    global __columns, __columns_lower, __locations, __locations_lower, __model

    if __columns is not None and __model is not None:
        # already loaded
        return

    print('Loading saved artifacts...')

    # validate paths
    if not Path(columns_path).exists():
        raise FileNotFoundError(f"columns.json not found at {columns_path}")
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model pickle not found at {model_path}")

    with open(columns_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # store original column names (case preserved)
        __columns = data.get('data_columns', [])
        if not isinstance(__columns, list) or len(__columns) < 4:
            raise ValueError("columns.json 'data_columns' missing or malformed")

        # lowercase helper lists for reliable user input lookup
        __columns_lower = [c.lower() for c in __columns]
        # locations are expected to start from index 3
        __locations = __columns[3:]
        __locations_lower = [c.lower() for c in __locations]

    with open(model_path, 'rb') as f:
        __model = pickle.load(f)

    print('Artifacts loaded successfully.')


def get_location_names():
    """
    Return the location list (original case). Lazy-load artifacts if needed.
    """
    global __locations
    if __locations is None:
        load_artifacts()
    return __locations or []


def predict_price(location: str, sqft: float, bhk: int, baths: int):
    """
    Predict price for given inputs.
    Returns a formatted string (Rs. X Lakhs / Rs. Y Crs).
    Lazy-loads artifacts if necessary.
    Assumes the model's output is in rupees.
    """
    global __columns, __columns_lower, __model

    # lazy load
    if __columns is None or __model is None:
        load_artifacts()

    if __model is None or __columns is None:
        raise RuntimeError("Model or columns not loaded. Call load_artifacts() first.")

    # normalize location for lookup
    loc = (location or "").strip().lower()

    try:
        loc_index = __columns_lower.index(loc)
    except ValueError:
        loc_index = -1  # not found

    # prepare feature vector (float dtype)
    x_array = np.zeros(len(__columns), dtype=float)

    # NOTE: this assumes the first three columns are [total_sqft, bhk, bath]
    x_array[0] = float(sqft)
    x_array[1] = int(bhk)
    x_array[2] = int(baths)

    if loc_index >= 0:
        x_array[loc_index] = 1.0

    # IMPORTANT: build DataFrame with the original column names so sklearn sees valid feature names
    x_df = pd.DataFrame([x_array], columns=__columns)

    # predict
    predicted_price = __model.predict(x_df)[0]

    # format (assuming model outputs rupees)
    if predicted_price >= 1e7:  # >= 1 crore
        formatted_price = f"Estimated Price is: Rs. {predicted_price / 1e7:.2f} Crs"
    else:
        formatted_price = f"Estimated Price is: Rs. {predicted_price / 1e5:.2f} Lakhs"

    return formatted_price


if __name__ == '__main__':
    load_artifacts()
    print("Locations count:", len(get_location_names()))
    print(predict_price('7th Phase, JP Nagar,Bangalore', 700, 3, 3))
    print(predict_price('Yashvant Viva TownShip, Nalasopara East,Mumbai', 800, 2, 2))
    print(predict_price('Yerawada, Pune', 900, 2, 2))
    print(predict_price('Yesvantpur Industrial Suburb, Yeshwanthpur,Bangalore', 1000, 2, 2))