import os
import sys
import joblib
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import urllib


# -------------------------------------------------------
# Paths
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.predict import make_predictions

SERVER = r"localhost"
DATABASE = "f1_data"
DRIVER = "ODBC Driver 17 for SQL Server"

connection_string = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"
)

query = """
SELECT *
FROM [podium_prediction_dataset]
"""

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
    return pd.read_sql(query, engine)


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

    Future race metadata such as round and race_date comes from
    FUTURE_RACE_CALENDAR.
    """

    year_data = df[df["season"] == selected_year].copy()

    if year_data.empty:
        year_data = df.copy()

    latest_rows = (
        year_data
        .sort_values(["season", "round"])
        .groupby(["driver_name", "constructor_name"], as_index=False)
        .tail(1)
        .copy()
    )

    race_info = FUTURE_RACE_CALENDAR.get(selected_race)

    if race_info is None:
        latest_round = year_data["round"].max()
        latest_rows["round"] = latest_round + 1
        latest_rows["race_date"] = None
    else:
        latest_rows["round"] = race_info["round"]
        latest_rows["race_date"] = race_info["race_date"]

    latest_rows["season"] = selected_year
    latest_rows["race_name"] = selected_race

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

year_options = sorted(df["season"].dropna().unique())

selected_year = st.sidebar.selectbox(
    "Select Year",
    year_options,
    index=len(year_options) - 1
)

existing_races = sorted(
    df[df["season"] == selected_year]["race_name"].dropna().unique()
)

FUTURE_RACE_CALENDAR = {
    "Austrian Grand Prix": {"round": 11, "race_date": "2026-06-28"},
    "British Grand Prix": {"round": 12, "race_date": "2026-07-05"},
    "Belgian Grand Prix": {"round": 13, "race_date": "2026-07-19"},
    "Hungarian Grand Prix": {"round": 14, "race_date": "2026-07-26"},
    "Dutch Grand Prix": {"round": 15, "race_date": "2026-08-23"},
    "Italian Grand Prix": {"round": 16, "race_date": "2026-09-06"},
    "Azerbaijan Grand Prix": {"round": 17, "race_date": "2026-09-20"},
    "Singapore Grand Prix": {"round": 18, "race_date": "2026-10-04"},
    "United States Grand Prix": {"round": 19, "race_date": "2026-10-18"},
    "Mexico City Grand Prix": {"round": 20, "race_date": "2026-10-25"},
    "São Paulo Grand Prix": {"round": 21, "race_date": "2026-11-08"},
    "Las Vegas Grand Prix": {"round": 22, "race_date": "2026-11-21"},
    "Qatar Grand Prix": {"round": 23, "race_date": "2026-11-29"},
    "Abu Dhabi Grand Prix": {"round": 24, "race_date": "2026-12-06"},
}

future_races = list(FUTURE_RACE_CALENDAR.keys())

race_options = existing_races + [
    race for race in future_races
    if race not in existing_races
]

default_race = "Australian Grand Prix"

selected_race = st.sidebar.selectbox(
    "Select Grand Prix",
    race_options,
    index=race_options.index(default_race)
)


# -------------------------------------------------------
# Select or create race dataframe
# -------------------------------------------------------
race_df = df[
    (df["season"] == selected_year) &
    (df["race_name"] == selected_race)
].copy()

is_future_race = race_df.empty

if is_future_race:
    race_info = FUTURE_RACE_CALENDAR.get(selected_race)

    if race_info:
        st.info(
            f"""
**Future Grand Prix Prediction**

**Race:** {selected_race} {selected_year}  
**Round:** {race_info["round"]}  
**Race Date:** {race_info["race_date"]}

Creating pre-race prediction rows from the latest available driver and constructor form.
"""
        )
    else:
        st.warning(
            f"{selected_race} is not in the future race calendar. "
            "Using latest available data as fallback."
        )

    race_df = create_future_race_features(
        df=df,
        selected_year=selected_year,
        selected_race=selected_race
    )

    if race_df.empty:
        st.error("Future race records could not be created.")
        st.stop()



# -------------------------------------------------------
# Generate predictions
# -------------------------------------------------------


race_df = race_df.drop_duplicates(
    subset=["season", "round", "race_name", "driver_name", "constructor_name"],
    keep="last"
).copy()

print(race_df.columns.tolist())

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
# Predticted Vs Actual
# -------------------------------------------------------

if not is_future_race:
    st.divider()
    st.subheader(f"Prediction vs Actual Result - {selected_race} {selected_year}")

    comparison_columns = [
        "driver_name",
        "constructor_name",

        "finish_position",
        "podium_finish",
        "podium_finish_prediction",
        "podium_finish_probability",

        "top_10_finish",
        "top_10_finish_prediction",
        "top_10_finish_probability",

        "dnf",
        "dnf_prediction",
        "dnf_probability",
    ]

    available_comparison_columns = [
        col for col in comparison_columns
        if col in prediction_df.columns
    ]

    comparison_df = prediction_df[available_comparison_columns].copy()

    if {
        "podium_finish",
        "podium_finish_prediction"
    }.issubset(comparison_df.columns):
        comparison_df["podium_correct"] = (
            comparison_df["podium_finish"] ==
            comparison_df["podium_finish_prediction"]
        )

    if {
        "top_10_finish",
        "top_10_finish_prediction"
    }.issubset(comparison_df.columns):
        comparison_df["top_10_correct"] = (
            comparison_df["top_10_finish"] ==
            comparison_df["top_10_finish_prediction"]
        )

    if {
        "dnf",
        "dnf_prediction"
    }.issubset(comparison_df.columns):
        comparison_df["dnf_correct"] = (
            comparison_df["dnf"] ==
            comparison_df["dnf_prediction"]
        )

    st.dataframe(
        comparison_df.sort_values("finish_position"),
        use_container_width=True
    )

if not is_future_race:
    st.subheader("Prediction Accuracy Breakdown")

    accuracy_summary = pd.DataFrame({
        "Target": ["Podium", "Top 10", "DNF"],
        "Correct Predictions": [
            (prediction_df["podium_finish"] == prediction_df["podium_finish_prediction"]).sum(),
            (prediction_df["top_10_finish"] == prediction_df["top_10_finish_prediction"]).sum(),
            (prediction_df["dnf"] == prediction_df["dnf_prediction"]).sum(),
        ],
        "Incorrect Predictions": [
            (prediction_df["podium_finish"] != prediction_df["podium_finish_prediction"]).sum(),
            (prediction_df["top_10_finish"] != prediction_df["top_10_finish_prediction"]).sum(),
            (prediction_df["dnf"] != prediction_df["dnf_prediction"]).sum(),
        ],
    })

    accuracy_long = accuracy_summary.melt(
        id_vars="Target",
        value_vars=["Correct Predictions", "Incorrect Predictions"],
        var_name="Prediction Result",
        value_name="Count"
    )

    fig_accuracy = px.bar(
        accuracy_long,
        x="Target",
        y="Count",
        color="Prediction Result",
        barmode="stack",
        title="Correct vs Incorrect Predictions by Target"
    )

    st.plotly_chart(fig_accuracy, use_container_width=True)

# -------------------------------------------------------
# Metrics
# -------------------------------------------------------
st.divider()
st.subheader("Race Prediction Summary")

total_drivers = len(prediction_df)
predicted_podiums = prediction_df["podium_finish_prediction"].sum()
predicted_top_10 = prediction_df["top_10_finish_prediction"].sum()
predicted_dnfs = prediction_df["dnf_prediction"].sum()

if not is_future_race:
    actual_podiums = prediction_df["podium_finish"].sum()
    actual_top_10 = prediction_df["top_10_finish"].sum()
    actual_dnfs = prediction_df["dnf"].sum()

    podium_correct = (
        prediction_df["podium_finish"] ==
        prediction_df["podium_finish_prediction"]
    ).sum()

    top_10_correct = (
        prediction_df["top_10_finish"] ==
        prediction_df["top_10_finish_prediction"]
    ).sum()

    dnf_correct = (
        prediction_df["dnf"] ==
        prediction_df["dnf_prediction"]
    ).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Driver Entries", total_drivers)
    col2.metric(
        "Podium Predictions Correct",
        f"{podium_correct}/{total_drivers}",
        delta=f"Actual podiums: {int(actual_podiums)}"
    )
    col3.metric(
        "Top 10 Predictions Correct",
        f"{top_10_correct}/{total_drivers}",
        delta=f"Actual top 10: {int(actual_top_10)}"
    )
    col4.metric(
        "DNF Predictions Correct",
        f"{dnf_correct}/{total_drivers}",
        delta=f"Actual DNFs: {int(actual_dnfs)}"
    )

else:
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