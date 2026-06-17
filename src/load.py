import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")


# -----------------------------
# SQL Server connection
# -----------------------------


def get_sqlserver_engine():
    server = "localhost"
    database = "f1_data"

    engine = create_engine(
        f"mssql+pyodbc://@{server}/{database}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
        "&trusted_connection=yes"
    )

    return engine

engine = get_sqlserver_engine()

# -----------------------------
# CSV to SQL mapping
# -----------------------------
TABLES = {
    "raw_races.csv": "raw_races",
    "raw_drivers.csv": "raw_drivers",
    "raw_constructors.csv": "raw_constructors",
    "raw_results.csv": "raw_results",
    "raw_qualifying.csv": "raw_qualifying",
    "raw_pitstops.csv": "raw_pitstops",
    "raw_driver_standings.csv": "raw_driver_standings",
    "raw_constructor_standings.csv": "raw_constructor_standings",
    "raw_sprint_results.csv": "raw_sprint_results",
    "raw_lap_times.csv": "raw_lap_times",
    "raw_status.csv": "raw_status",
}


def load_csv_to_sql(filename, table_name):
    file_path = os.path.join(RAW_DIR, filename)

    if not os.path.exists(file_path):
        print(f"Skipped: {filename} not found")
        return

    print(f"\nLoading {filename} into {table_name}...")

    df = pd.read_csv(file_path)

    if df.empty:
        print(f"Skipped: {filename} is empty")
        return

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000
    )

    print(f"Loaded {len(df)} rows into {table_name}")


def test_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DB_NAME()"))
        db_name = result.scalar()
        print(f"Connected to database: {db_name}")


def load_all_raw_tables():
    test_connection()

    for filename, table_name in TABLES.items():
        load_csv_to_sql(filename, table_name)

    print("\nAll raw tables loaded successfully.")


if __name__ == "__main__":
    load_all_raw_tables()