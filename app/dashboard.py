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
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .main-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(90deg, #111827, #dc2626);
        padding: 18px 28px;
        border-radius: 0 0 18px 18px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.35);
    }

    .main-header h1 {
        color: white;
        font-size: 34px;
        margin: 0;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    .main-header p {
        color: #f3f4f6;
        margin: 4px 0 0 0;
        font-size: 15px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827, #1f2937);
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    .sidebar-card {
        background: rgba(255,255,255,0.08);
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 18px;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }

    .sidebar-title {
        font-size: 22px;
        font-weight: 800;
        color: #facc15;
        margin-bottom: 4px;
    }

    .sidebar-subtitle {
        font-size: 13px;
        color: #e5e7eb;
    }
    </style>

    <div class="main-header">
        <h1>🏎️ F1 Strategy Intelligence Platform</h1>
        <p>Race outcome prediction · podium probability · DNF risk · constructor insights</p>
    </div>
    """,
    unsafe_allow_html=True
)

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
st.sidebar.markdown(
    """
    <div class="sidebar-card">
        <div class="sidebar-title">🏁 Race Control</div>
        <div class="sidebar-subtitle">
            Select a season and Grand Prix to generate race predictions.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

year_options = sorted(df["season"].dropna().unique())

selected_year = st.sidebar.selectbox(
    "Season",
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
**Future Grand Prix:** {selected_race} {selected_year}, **Round:** {race_info["round"]}, **Race Date:** {race_info["race_date"]}

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
# Metrics
# -------------------------------------------------------

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
        f"{podium_correct}/{total_drivers}"
    )
    col3.metric(
        "Top 10 Predictions Correct",
        f"{top_10_correct}/{total_drivers}"
    )
    col4.metric(
        "DNF Predictions Correct",
        f"{dnf_correct}/{total_drivers}"
    )

else:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Driver Entries", total_drivers)
    col2.metric("Predicted Podiums", int(predicted_podiums))
    col3.metric("Predicted Top 10", int(predicted_top_10))
    col4.metric("Predicted DNFs", int(predicted_dnfs))


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
    use_container_width=True,
    height=350
)

col1, col2 = st.columns([1, 1])

# -------------------------------------------------------
# Predticted Vs Actual
# -------------------------------------------------------
with col1:
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

with col2:
    if not is_future_race:
        st.divider()
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


col1, col2 = st.columns([1, 1])

# -------------------------------------------------------
# Predicted podium finishers
# -------------------------------------------------------
with col1:
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
with col2:
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


col1, col2 = st.columns([1, 1])

# -------------------------------------------------------
# Podium probability ranking
# -------------------------------------------------------
with col1:
    st.divider()
    st.subheader(f"Podium Probability Ranking - {selected_race}")

    podium_ranking = (
        prediction_df
        .sort_values("podium_finish_probability", ascending=False)
        .head(10)
    )

    fig_podium_ranking = px.bar(
        podium_ranking,
        x="podium_finish_probability",
        y="driver_name",
        color="constructor_name",
        orientation="h",
        text="podium_finish_probability",
        title=f"Top 10 Drivers Most Likely to Finish on the Podium - {selected_race}",
    )

    fig_podium_ranking.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside"
    )

    fig_podium_ranking.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_tickformat=".0%",
        xaxis_title="Podium Probability",
        yaxis_title="Driver"
    )

    st.plotly_chart(fig_podium_ranking, use_container_width=True)


# -------------------------------------------------------
# Top 10 confidence chart
# -------------------------------------------------------
with col2:
    st.divider()
    st.subheader(f"Top 10 Confidence - {selected_race}")

    top_10_confidence = (
        prediction_df
        .sort_values("top_10_finish_probability", ascending=False)
        .head(12)
    )

    fig_top_10 = px.bar(
        top_10_confidence,
        x="top_10_finish_probability",
        y="driver_name",
        color="constructor_name",
        orientation="h",
        text="top_10_finish_probability",
        title=f"Safest Points Finishers - {selected_race}",
    )

    fig_top_10.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside"
    )

    fig_top_10.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_tickformat=".0%",
        xaxis_title="Top 10 Probability",
        yaxis_title="Driver"
    )

    st.plotly_chart(fig_top_10, use_container_width=True)


col1, col2 = st.columns([1, 1])

# -------------------------------------------------------
# DNF risk chart
# -------------------------------------------------------
with col1:
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

# -------------------------------------------------------
# DNF risk ranking
# -------------------------------------------------------
with col2:
    st.divider()
    st.subheader(f"DNF Risk Ranking - {selected_race}")

    dnf_risk = (
        prediction_df
        .sort_values("dnf_probability", ascending=False)
        .head(10)
    )

    fig_dnf = px.bar(
        dnf_risk,
        x="dnf_probability",
        y="driver_name",
        color="constructor_name",
        orientation="h",
        text="dnf_probability",
        title=f"Highest Reliability Risk Drivers - {selected_race}",
    )

    fig_dnf.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside"
    )

    fig_dnf.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_tickformat=".0%",
        xaxis_title="DNF Probability",
        yaxis_title="Driver"
    )

    st.plotly_chart(fig_dnf, use_container_width=True)

# -------------------------------------------------------
# Surprise / miss analysis
# -------------------------------------------------------
if not is_future_race:
    st.divider()
    st.subheader(f"Surprise / Miss Analysis - {selected_race}")

    surprise_df = prediction_df.copy()

    surprise_df["podium_miss"] = (
        (surprise_df["podium_finish_prediction"] == 1) &
        (surprise_df["podium_finish"] == 0)
    )

    surprise_df["unexpected_podium"] = (
        (surprise_df["podium_finish_prediction"] == 0) &
        (surprise_df["podium_finish"] == 1)
    )

    surprise_df["top_10_miss"] = (
        (surprise_df["top_10_finish_prediction"] == 1) &
        (surprise_df["top_10_finish"] == 0)
    )

    surprise_df["unexpected_top_10"] = (
        (surprise_df["top_10_finish_prediction"] == 0) &
        (surprise_df["top_10_finish"] == 1)
    )

    surprise_cases = surprise_df[
        surprise_df[
            [
                "podium_miss",
                "unexpected_podium",
                "top_10_miss",
                "unexpected_top_10",
            ]
        ].any(axis=1)
    ].copy()

    def classify_surprise(row):
        if row["podium_miss"]:
            return "Predicted podium but missed"
        elif row["unexpected_podium"]:
            return "Unexpected podium"
        elif row["top_10_miss"]:
            return "Predicted top 10 but missed"
        elif row["unexpected_top_10"]:
            return "Unexpected top 10"
        else:
            return "No surprise"

    surprise_cases["surprise_type"] = surprise_cases.apply(
        classify_surprise,
        axis=1
    )

    surprise_cases["surprise_score"] = surprise_cases[
        [
            "podium_finish_probability",
            "top_10_finish_probability",
            "dnf_probability",
        ]
    ].max(axis=1)

    if surprise_cases.empty:
        st.success("No major prediction surprises for this race.")
    else:
        fig_surprise = px.scatter(
            surprise_cases,
            x="podium_finish_probability",
            y="finish_position",
            color="surprise_type",
            size="top_10_finish_probability",
            hover_data=[
                "driver_name",
                "constructor_name",
                "finish_position",
                "podium_finish_probability",
                "top_10_finish_probability",
                "dnf_probability",
            ],
            title=f"Prediction Misses and Surprises - {selected_race}",
        )

        fig_surprise.update_layout(
            xaxis_tickformat=".0%",
            xaxis_title="Predicted Podium Probability",
            yaxis_title="Actual Finish Position",
            yaxis=dict(autorange="reversed")
        )

        st.plotly_chart(fig_surprise, use_container_width=True)

        st.dataframe(
            surprise_cases[
                [
                    "driver_name",
                    "constructor_name",
                    "finish_position",
                    "surprise_type",
                    "podium_finish_probability",
                    "top_10_finish_probability",
                    "dnf_probability",
                ]
            ].sort_values("finish_position"),
            use_container_width=True
        )



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