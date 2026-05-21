import os
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
)

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from preprocessing import preprocess_data


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


# Target creation
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


# Building models
def build_candidate_models():
    random_forest = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(
            n_estimators=500,
            max_depth=8,
            min_samples_leaf=5,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        )),
    ])

    xgboost = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", XGBClassifier(
            n_estimators=500,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    lightgbm = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", LGBMClassifier(
            n_estimators=500,
            max_depth=5,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.85,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )),
    ])

    catboost = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", CatBoostClassifier(
            iterations=500,
            depth=5,
            learning_rate=0.03,
            loss_function="Logloss",
            verbose=False,
            random_seed=42,
            auto_class_weights="Balanced",
        )),
    ])

    voting_ensemble = VotingClassifier(
        estimators=[
            ("rf", random_forest),
            ("xgb", xgboost),
            ("lgbm", lightgbm),
            ("cat", catboost),
        ],
        voting="soft",
        n_jobs=-1,
    )

    return {
        "random_forest": random_forest,
        "xgboost": xgboost,
        "lightgbm": lightgbm,
        "catboost": catboost,
        "voting_ensemble": voting_ensemble,
    }


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

    best_models = {}
    model_scores = {}
    results = test_df.copy()

    for target in TARGETS:
        print(f"Training models for target: {target}")

        y_train = train_df[target]
        y_test = test_df[target]

        candidate_models = build_candidate_models()

        best_model = None
        best_model_name = None
        best_score = -1

        model_scores[target] = {}

        for model_name, model in candidate_models.items():
            print(f"\nModel: {model_name}")

            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            if y_test.nunique() > 1:
                roc_auc = roc_auc_score(y_test, y_proba)
                pr_auc = average_precision_score(y_test, y_proba)
            else:
                roc_auc = None
                pr_auc = None

            model_scores[target][model_name] = {
                "roc_auc": roc_auc,
                "pr_auc": pr_auc,
            }

            print("ROC-AUC:", roc_auc)
            print("PR-AUC:", pr_auc)

            print("\nClassification Report:")
            print(classification_report(y_test, y_pred))

            print("Confusion Matrix:")
            print(confusion_matrix(y_test, y_pred))

            # PR-AUC is better for imbalanced targets like podium and DNF.
            score = pr_auc if pr_auc is not None else -1

            if score > best_score:
                best_score = score
                best_model = model
                best_model_name = model_name

        print(f"\nBest model for {target}: {best_model_name}")
        print(f"Best PR-AUC: {best_score}")

        best_models[target] = {
            "model_name": best_model_name,
            "model": best_model,
            "score": best_score,
        }

        target_predictions = best_model.predict(X_test)
        target_probabilities = best_model.predict_proba(X_test)[:, 1]

        results[f"{target}_prediction"] = target_predictions
        results[f"{target}_probability"] = target_probabilities.round(4)

    # podium probability should not be higher than top 10 probability.
    if {
        "podium_finish_probability",
        "top_10_finish_probability",
    }.issubset(results.columns):
        results["top_10_finish_probability"] = results[
            ["top_10_finish_probability", "podium_finish_probability"]
        ].max(axis=1)

    joblib.dump(
        {
            "models": best_models,
            "features": FEATURES,
            "targets": TARGETS,
            "model_scores": model_scores,
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