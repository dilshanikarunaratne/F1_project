from extract_jolpica import run_extraction
from load import load_all_raw_tables
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(BASE_DIR, "sql")


SERVER = r"localhost\SQLEXPRESS"
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


def run_sql_file(filename):
    path = os.path.join(SQL_DIR, filename)

    with open(path, "r", encoding="utf-8") as file:
        sql_script = file.read()

    statements = sql_script.split("GO")

    with engine.begin() as conn:
        for statement in statements:
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

    print(f"Executed: {filename}")


def validate_prediction_dataset():
    query = """
    SELECT COUNT(*) AS row_count
    FROM vw_prediction_dataset
    """

    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
        print(f"vw_prediction_dataset row count: {result.row_count}")


def run_etl():
    print("Starting F1 ETL pipeline...")

    # 1. Extract API data
    run_extraction(start_season=2023, end_season=2025)

    # 2. Load raw CSV files into SQL raw tables
    load_all_raw_tables()

    # 3. Create / refresh SQL views
    run_sql_file("02_create_podium_base.sql")
    run_sql_file("03_create_feature_views.sql")
    run_sql_file("04_create_prediction_dataset.sql")

    # 4. Validate final ML dataset
    validate_prediction_dataset()

    print("ETL pipeline completed successfully.")


if __name__ == "__main__":
    run_etl()