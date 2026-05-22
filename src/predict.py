import os
import joblib
import pandas as pd
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.preprocessing import preprocess_data

RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "podium_prediction_dataset.csv")

df = pd.read_csv(RAW_DATA_PATH)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "race_outcome_prediction_models.pkl"
)

FEATURES_PATH = os.path.join(
    BASE_DIR, "models", "feature_columns.pkl"
)


def make_predictions(new_data):
    model_bundle = joblib.load(MODEL_PATH)

    models = model_bundle["models"]
    feature_columns = model_bundle.get("features")

    if feature_columns is None:
        feature_columns = joblib.load(FEATURES_PATH)

    processed_data = preprocess_data(new_data.copy())

    # Drop target/result columns if they exist in incoming data.
    target_columns = [
        "finish_position",
        "position",
        "podium_finish",
        "top_10_finish",
        "dnf",
    ]

    processed_data = processed_data.drop(
        columns=[col for col in target_columns if col in processed_data.columns],
        errors="ignore",
    )

    processed_data = processed_data.reindex(
        columns=feature_columns,
        fill_value=0,
    )

    results = new_data.copy()

    for target, model_info in models.items():
        model = model_info["model"]

        predictions = model.predict(processed_data)
        probabilities = model.predict_proba(processed_data)[:, 1]

        results[f"{target}_prediction"] = predictions
        results[f"{target}_probability"] = probabilities.round(4)

    if {
        "podium_finish_probability",
        "top_10_finish_probability",
    }.issubset(results.columns):
        results["top_10_finish_probability"] = results[
            ["top_10_finish_probability", "podium_finish_probability"]
        ].max(axis=1)

    return results