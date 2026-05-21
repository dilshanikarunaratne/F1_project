import os
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

from preprocessing import preprocess_data


# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "raw", "podium_prediction_dataset.csv"
)

MODELS_DIR = os.path.join(BASE_DIR, "models")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

MODEL_PATH = os.path.join(MODELS_DIR, "race_outcome_prediction_models.pkl")
FEATURES_PATH = os.path.join(MODELS_DIR, "feature_columns.pkl")
OUTPUT_DATA_PATH = os.path.join(PROCESSED_DIR, "race_outcome_predictions_output.csv")



FEATURES = [
    "grid",
    "qualifying_position",
    "qualifying_gap_to_pole_ms",
    "teammate_qualifying_gap_ms",
    "avg_finish_last_5",
    "podiums_last_5",
    "avg_qualifying_last_5",
    "dnf_rate_last_10",
    "constructor_avg_finish_last_5",
    "constructor_points_last_5",
    "constructor_podium_rate_last_5",
    "avg_pit_ms_last_5",
    "pit_consistency_last_5",
    "total_pit_stops_last_5",
    "driver_dnf_rate_last_10",
    "constructor_dnf_rate_last_20",
]

TARGETS = [
    "podium_finish",
    "top_10_finish",
    "dnf",
]


# Target creations
def create_targets(df):
    df = df.copy()

    if "finish_position" not in df.columns:
        raise ValueError("Column 'finish_position' is required to create targets.")

    df["podium_finish"] = (df["finish_position"] <= 3).astype("int64")
    df["top_10_finish"] = (df["finish_position"] <= 10).astype("int64")

    if "dnf" in df.columns:
        df["dnf"] = df["dnf"].astype("int64")
    elif "status" in df.columns:
        finished_statuses = {
            "Finished",
            "+1 Lap",
            "+2 Laps",
            "+3 Laps",
            "+4 Laps",
            "+5 Laps",
            "+6 Laps",
            "+7 Laps",
            "+8 Laps",
            "+9 Laps",
            "+10 Laps",
        }
        df["dnf"] = (~df["status"].isin(finished_statuses)).astype("int64")
    else:
        raise ValueError(
            "Could not create DNF target. Add either a 'dnf' column or a 'status' column."
        )

    return df

# Building RF model
def build_model():
    return Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            random_state=42,
            class_weight="balanced",
        )),
    ])


# Main training function
def train_model():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    df = preprocess_data(df)
    df = create_targets(df)

    missing_features = [col for col in FEATURES if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")

    missing_targets = [col for col in TARGETS if col not in df.columns]
    if missing_targets:
        raise ValueError(f"Missing target columns: {missing_targets}")

    train_df = df[df["year"] < 2022].copy()
    test_df = df[df["year"] >= 2022].copy()

    X_train = train_df[FEATURES]
    X_test = test_df[FEATURES]

    print("Training shape:", X_train.shape)
    print("Testing shape:", X_test.shape)

    models = {}
    results = test_df.copy()

    for target in TARGETS:
        print(f"Training target: {target}")

        y_train = train_df[target]
        y_test = test_df[target]

        model = build_model()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        models[target] = model

        probability_col = f"{target}_probability"
        prediction_col = f"predicted_{target}"

        results[probability_col] = y_proba
        results[prediction_col] = y_pred

        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        if y_test.nunique() > 1:
            print("ROC-AUC:", roc_auc_score(y_test, y_proba))
        else:
            print("ROC-AUC skipped: only one class present in test data.")

        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))

    # podium probability should not exceed top 10 probability.
    results["top_10_finish_probability"] = results[
        ["top_10_finish_probability", "podium_finish_probability"]
    ].max(axis=1)

    preview_cols = [
        "year",
        "round",
        "race_name",
        "driver_name",
        "constructor_name",
        "qualifying_position",
        "finish_position",
        "podium_finish",
        "top_10_finish",
        "dnf",
        "podium_finish_probability",
        "top_10_finish_probability",
        "dnf_probability",
        "predicted_podium_finish",
        "predicted_top_10_finish",
        "predicted_dnf",
    ]

    preview_cols = [col for col in preview_cols if col in results.columns]

    print("\nPrediction Preview:")
    print(
        results[preview_cols]
        .sort_values(
            by=["year", "round", "podium_finish_probability"],
            ascending=[True, True, False],
        )
        .head(30)
    )

    joblib.dump(
        {
            "models": models,
            "features": FEATURES,
            "targets": TARGETS,
        },
        MODEL_PATH,
    )

    joblib.dump(FEATURES, FEATURES_PATH)
    results.to_csv(OUTPUT_DATA_PATH, index=False)

    print("\nModels saved successfully:")
    print(MODEL_PATH)

    print("\nFeature columns saved successfully:")
    print(FEATURES_PATH)

    print("\nPredictions saved successfully:")
    print(OUTPUT_DATA_PATH)


if __name__ == "__main__":
    train_model()