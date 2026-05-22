import os
import sys
import joblib
import pandas as pd
import streamlit as st
import plotly.express as px


# -------------------------------------------------------
# Paths
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.predict import make_predictions

RAW_DATA_PATH = os.path.join(
    BASE_DIR, "data", "raw", "podium_prediction_dataset.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "race_outcome_prediction_models.pkl"
)


# -------------------------------------------------------
# Streamlit page config
# -------------------------------------------------------
st.set_page_config(
    page_title="F1 Strategy Intelligence Platform",
    layout="wide"
)

st.title("F1 Strategy Intelligence Platform")


# -------------------------------------------------------
# Load data/model
# -------------------------------------------------------
@st.cache_data
def load_raw_data():
    return pd.read_csv(RAW_DATA_PATH)


@st.cache_resource
def load_model_bundle():
    return joblib.load(MODEL_PATH)


df = load_raw_data()
model_bundle = load_model_bundle()


# -------------------------------------------------------
# Future race feature creation
# -------------------------------------------------------
def create_future_race_features(df, selected_year, selected_race):
    """
    Creates pre-race future Grand Prix rows using the latest available
    data for each driver/constructor in the selected year.

    This is for BEFORE qualifying, so the model should NOT use:
    grid, qualifying_position, qualifying_gap_to_pole_ms,
    teammate_qualifying_gap_ms.
    """

    year_data = df[df["year"] == selected_year].copy()

    if year_data.empty:
        year_data = df.copy()

    latest_rows = (
        year_data
        .sort_values(["year", "round"])
        .groupby(["driverId", "constructorId"], as_index=False)
        .tail(1)
        .copy()
    )

    latest_round = year_data["round"].max()

    latest_rows["year"] = selected_year
    latest_rows["round"] = latest_round + 1
    latest_rows["race_name"] = selected_race

    # Clear future result/target columns
    cols_to_clear = [
        "raceId",
        "resultId",
        "finish_position",
        "points",
        "podium_finish",
        "top_10_finish",
        "dnf",
        "status",
        "statusId",
    ]

    for col in cols_to_clear:
        if col in latest_rows.columns:
            latest_rows[col] = None

    return latest_rows


# -------------------------------------------------------
# Sidebar filters
# -------------------------------------------------------
st.sidebar.header("Race Selection")

year_options = sorted(df["year"].dropna().unique())

selected_year = st.sidebar.selectbox(
    "Select Year",
    year_options,
    index=len(year_options) - 1
)

existing_races = sorted(
    df[df["year"] == selected_year]["race_name"].dropna().unique()
)

future_races = [
    "Canadian Grand Prix",
    "Spanish Grand Prix",
    "Austrian Grand Prix",
    "British Grand Prix",
    "Belgian Grand Prix",
    "Hungarian Grand Prix",
    "Dutch Grand Prix",
    "Italian Grand Prix",
    "Azerbaijan Grand Prix",
    "Singapore Grand Prix",
    "United States Grand Prix",
    "Mexico City Grand Prix",
    "São Paulo Grand Prix",
    "Las Vegas Grand Prix",
    "Qatar Grand Prix",
    "Abu Dhabi Grand Prix",
]

race_options = existing_races + [
    race for race in future_races if race not in existing_races
]

selected_race = st.sidebar.selectbox(
    "Select Grand Prix",
    race_options,
    index=len(race_options) - 1
)


# -------------------------------------------------------
# Select or create race dataframe
# -------------------------------------------------------
race_df = df[
    (df["year"] == selected_year) &
    (df["race_name"] == selected_race)
].copy()

is_future_race = race_df.empty

if is_future_race:
    st.info(
        f"{selected_race} {selected_year} is not in the dataset yet. "
        "Creating pre-race prediction rows from the latest available driver and constructor form."
    )

    race_df = create_future_race_features(
        df=df,
        selected_year=selected_year,
        selected_race=selected_race
    )


# -------------------------------------------------------
# Generate predictions
# -------------------------------------------------------
prediction_df = make_predictions(race_df)

prediction_df = prediction_df.sort_values(
    "podium_finish_probability",
    ascending=False
)


# -------------------------------------------------------
# Prediction table
# -------------------------------------------------------
st.subheader(f"Predictions - {selected_race} {selected_year}")

display_columns = [
    "race_name",
    "driver_name",
    "constructor_name",
    "podium_finish_probability",
    "top_10_finish_probability",
    "dnf_probability",
    "podium_finish_prediction",
    "top_10_finish_prediction",
    "dnf_prediction",
]

available_columns = [
    col for col in display_columns if col in prediction_df.columns
]

st.dataframe(
    prediction_df[available_columns],
    use_container_width=True
)


# -------------------------------------------------------
# Metrics
# -------------------------------------------------------
st.divider()

total_drivers = len(prediction_df)
predicted_podiums = prediction_df["podium_finish_prediction"].sum()
predicted_top_10 = prediction_df["top_10_finish_prediction"].sum()
predicted_dnfs = prediction_df["dnf_prediction"].sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Driver Entries", total_drivers)
col2.metric("Predicted Podiums", int(predicted_podiums))
col3.metric("Predicted Top 10", int(predicted_top_10))
col4.metric("Predicted DNFs", int(predicted_dnfs))


# -------------------------------------------------------
# Model evaluation metrics
# -------------------------------------------------------
st.divider()

st.subheader("Best Model Evaluation Metrics")

models = model_bundle["models"]
model_scores = model_bundle["model_scores"]

metrics_rows = []

for target, model_info in models.items():
    best_model_name = model_info["model_name"]
    scores = model_scores[target][best_model_name]

    metrics_rows.append({
        "Target": target,
        "Best Model": best_model_name,
        "PR-AUC": scores["pr_auc"],
        "ROC-AUC": scores["roc_auc"],
    })

metrics_df = pd.DataFrame(metrics_rows)

st.dataframe(metrics_df, use_container_width=True)


# -------------------------------------------------------
# Predicted podium finishers
# -------------------------------------------------------
st.divider()

st.subheader(f"Predicted Podium Finishers - {selected_race}")

podium_predictions = prediction_df[
    prediction_df["podium_finish_prediction"] == 1
].copy()

podium_predictions = podium_predictions.sort_values(
    "podium_finish_probability",
    ascending=False
)

podium_display_columns = [
    "driver_name",
    "constructor_name",
    "podium_finish_probability",
    "top_10_finish_probability",
    "dnf_probability",
]

podium_display_columns = [
    col for col in podium_display_columns if col in podium_predictions.columns
]

st.dataframe(
    podium_predictions[podium_display_columns],
    use_container_width=True
)


# -------------------------------------------------------
# Constructor podium probability chart
# -------------------------------------------------------
st.divider()

st.subheader(f"Predicted Podium Probability by Constructor - {selected_race}")

constructor_podium = (
    prediction_df
    .groupby("constructor_name", as_index=False)["podium_finish_probability"]
    .mean()
    .sort_values("podium_finish_probability", ascending=False)
)

fig_constructor_podium = px.bar(
    constructor_podium,
    x="constructor_name",
    y="podium_finish_probability",
    title=f"Average Predicted Podium Probability by Constructor - {selected_race}",
)

st.plotly_chart(fig_constructor_podium, use_container_width=True)


# -------------------------------------------------------
# DNF risk chart
# -------------------------------------------------------
st.divider()

st.subheader(f"Predicted DNF Risk - {selected_race}")

dnf_risk = prediction_df.sort_values(
    "dnf_probability",
    ascending=False
)

fig_dnf = px.bar(
    dnf_risk,
    x="driver_name",
    y="dnf_probability",
    color="constructor_name",
    title=f"Predicted DNF Probability by Driver - {selected_race}",
)

st.plotly_chart(fig_dnf, use_container_width=True)