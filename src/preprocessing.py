import pandas as pd
import numpy as np


def preprocess_data(df):
    df = df.copy()

    # -----------------------------
    # 1. Handle date column
    # -----------------------------
    if "race_date" in df.columns:
        df["race_date"] = pd.to_datetime(df["race_date"], errors="coerce")

        # optional useful date features
        df["race_month"] = df["race_date"].dt.month
        df["race_dayofweek"] = df["race_date"].dt.dayofweek

    # -----------------------------
    # 2. Handle target variable
    # -----------------------------
    if "podium_finish" in df.columns:
        df["podium_finish"] = pd.to_numeric(df["podium_finish"], errors="coerce").fillna(0).astype("int64")

    # -----------------------------
    # 3. Clean grid column
    # -----------------------------
    if "grid" in df.columns:
        # create flag for non-start / missing grid
        df["grid_missing_flag"] = df["grid"].astype(str).str.upper().isin(["N", "\\N", "NAN", "NONE", ""])

        # convert grid to numeric
        df["grid"] = pd.to_numeric(df["grid"], errors="coerce")

        # fill missing grid with a large value
        # this means "started from back / unknown"
        df["grid"] = df["grid"].fillna(99)

    # -----------------------------
    # 4. Convert numeric columns
    # -----------------------------
    numeric_cols = [
        "year",
        "round",
        "grid",
        "qualifying_position",
        "best_quali_ms",
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
        "race_month",
        "race_dayofweek",
        "grid_missing_flag"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # 5. Add missing-value indicators
    # -----------------------------
    important_cols = [
        "qualifying_position",
        "qualifying_gap_to_pole_ms",
        "avg_finish_last_5",
        "constructor_avg_finish_last_5",
        "avg_pit_ms_last_5",
        "driver_dnf_rate_last_10"
    ]

    for col in important_cols:
        if col in df.columns:
            df[f"{col}_missing"] = df[col].isna().astype(int)

    # -----------------------------
    # 6. Fill missing numerical values
    # -----------------------------
    for col in df.select_dtypes(include=["number", "bool"]).columns:
        if col != "podium_finish":
            df[col] = df[col].fillna(df[col].median())

    # -----------------------------
    # 7. Fill categorical columns
    # -----------------------------
    categorical_cols = [
        "race_name",
        "driver_name",
        "constructor_name"
    ]

    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    return df