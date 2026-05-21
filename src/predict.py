import os
import joblib
from preprocessing import preprocess_data
import pandas as pd

# get root project folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# path to the saved trained model
MODEL_PATH = os.path.join(BASE_DIR, "models", "podium_prediction_model.pkl")
# path to saved feature column names
FEATURES_PATH = os.path.join(BASE_DIR, "models", "feature_columns.pkl")

# ------------------------
# main prediction function 
# ------------------------
def make_predictions(new_data):
    model = joblib.load(MODEL_PATH) # load saved trained model
    feature_columns = joblib.load(FEATURES_PATH) # load saved feature column names

    processed_data = preprocess_data(new_data.copy()) # runs same preprocessing pipeline. copy() is to prevent modifying original data

    if "podium_finish" in processed_data.columns:
        processed_data = processed_data.drop("podium_finish", axis=1)

    processed_data = processed_data.reindex(columns=feature_columns, fill_value=0) # to ensure exact same columns, exact same order

    predictions = model.predict(processed_data)
    probabilities = model.predict_proba(processed_data)[:, 1]

    results = new_data.copy()

    results["podium_prediction"] = predictions
    results["podium_probability"] = probabilities.round(4)

    return results