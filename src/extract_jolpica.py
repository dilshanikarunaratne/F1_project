import os
import time
import requests
import pandas as pd


BASE_URL = "https://api.jolpi.ca/ergast/f1"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

os.makedirs(RAW_DIR, exist_ok=True)


# -----------------------------
# Helpers
# -----------------------------
def fetch_json(url):
    print(f"Fetching: {url}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    time.sleep(3)
    return response.json()


def fetch_all_pages(base_url, table_key):
    all_items = []
    offset = 0
    limit = 100

    while True:
        separator = "&" if "?" in base_url else "?"
        url = f"{base_url}{separator}limit={limit}&offset={offset}"

        data = fetch_json(url)

        mrdata = data["MRData"]
        total = int(mrdata.get("total", 0))

        if table_key == "RaceTable":
            items = mrdata.get("RaceTable", {}).get("Races", [])
        elif table_key == "DriverTable":
            items = mrdata.get("DriverTable", {}).get("Drivers", [])
        elif table_key == "ConstructorTable":
            items = mrdata.get("ConstructorTable", {}).get("Constructors", [])
        elif table_key == "StandingsTable":
            items = mrdata.get("StandingsTable", {}).get("StandingsLists", [])
        else:
            items = []

        all_items.extend(items)

        offset += limit

        if offset >= total:
            break

    return all_items


def save_csv(df, filename):
    path = os.path.join(RAW_DIR, filename)
    df.to_csv(path, index=False)
    print(f"Saved: {path}")


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# -----------------------------
# Extractors
# -----------------------------
def extract_races(season):
    races = fetch_all_pages(f"{BASE_URL}/{season}.json", "RaceTable")

    rows = []

    for race in races:
        circuit = race.get("Circuit", {})
        location = circuit.get("Location", {})

        rows.append({
            "season": season,
            "round": safe_int(race.get("round")),
            "race_id": f"{season}_{race.get('round')}",
            "race_name": race.get("raceName"),
            "race_date": race.get("date"),
            "race_time": race.get("time"),
            "circuit_id": circuit.get("circuitId"),
            "circuit_name": circuit.get("circuitName"),
            "locality": location.get("locality"),
            "country": location.get("country"),
            "lat": location.get("lat"),
            "long": location.get("long"),
        })

    return pd.DataFrame(rows)


def extract_drivers(season):
    drivers = fetch_all_pages(f"{BASE_URL}/{season}/drivers.json", "DriverTable")

    rows = []

    for driver in drivers:
        rows.append({
            "season": season,
            "driver_id": driver.get("driverId"),
            "driver_code": driver.get("code"),
            "driver_number": driver.get("permanentNumber"),
            "given_name": driver.get("givenName"),
            "family_name": driver.get("familyName"),
            "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
            "date_of_birth": driver.get("dateOfBirth"),
            "nationality": driver.get("nationality"),
            "url": driver.get("url"),
        })

    return pd.DataFrame(rows)


def extract_constructors(season):
    constructors = fetch_all_pages(f"{BASE_URL}/{season}/constructors.json", "ConstructorTable")

    rows = []

    for constructor in constructors:
        rows.append({
            "season": season,
            "constructor_id": constructor.get("constructorId"),
            "constructor_name": constructor.get("name"),
            "nationality": constructor.get("nationality"),
            "url": constructor.get("url"),
        })

    return pd.DataFrame(rows)


def extract_results(season):
    races = fetch_all_pages(f"{BASE_URL}/{season}/results.json", "RaceTable")

    rows = []

    for race in races:
        for result in race.get("Results", []):
            driver = result.get("Driver", {})
            constructor = result.get("Constructor", {})
            fastest_lap = result.get("FastestLap", {})
            fastest_lap_time = fastest_lap.get("Time", {})
            fastest_lap_speed = fastest_lap.get("AverageSpeed", {})

            rows.append({
                "season": season,
                "round": safe_int(race.get("round")),
                "race_id": f"{season}_{race.get('round')}",
                "race_name": race.get("raceName"),
                "race_date": race.get("date"),

                "driver_id": driver.get("driverId"),
                "driver_code": driver.get("code"),
                "driver_number": driver.get("permanentNumber"),
                "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                "driver_dob": driver.get("dateOfBirth"),
                "driver_nationality": driver.get("nationality"),

                "constructor_id": constructor.get("constructorId"),
                "constructor_name": constructor.get("name"),
                "constructor_nationality": constructor.get("nationality"),

                "position": result.get("position"),
                "position_text": result.get("positionText"),
                "grid": result.get("grid"),
                "laps": result.get("laps"),
                "status": result.get("status"),
                "points": result.get("points"),

                "fastest_lap_rank": fastest_lap.get("rank"),
                "fastest_lap_lap": fastest_lap.get("lap"),
                "fastest_lap_time": fastest_lap_time.get("time"),
                "fastest_lap_speed": fastest_lap_speed.get("speed"),
            })

    return pd.DataFrame(rows)


def extract_qualifying(season):
    races = fetch_all_pages(f"{BASE_URL}/{season}/qualifying.json", "RaceTable")

    rows = []

    for race in races:
        for quali in race.get("QualifyingResults", []):
            driver = quali.get("Driver", {})
            constructor = quali.get("Constructor", {})

            rows.append({
                "season": season,
                "round": safe_int(race.get("round")),
                "race_id": f"{season}_{race.get('round')}",
                "race_name": race.get("raceName"),
                "race_date": race.get("date"),

                "driver_id": driver.get("driverId"),
                "driver_code": driver.get("code"),
                "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),

                "constructor_id": constructor.get("constructorId"),
                "constructor_name": constructor.get("name"),

                "qualifying_position": quali.get("position"),
                "q1": quali.get("Q1"),
                "q2": quali.get("Q2"),
                "q3": quali.get("Q3"),
            })

    return pd.DataFrame(rows)


def extract_pitstops(season, races_df):
    rows = []

    for _, race in races_df.iterrows():
        round_no = race["round"]

        races = fetch_all_pages(
            f"{BASE_URL}/{season}/{round_no}/pitstops.json",
            "RaceTable"
        )

        for race_data in races:
            for stop in race_data.get("PitStops", []):
                rows.append({
                    "season": season,
                    "round": safe_int(round_no),
                    "race_id": f"{season}_{round_no}",
                    "driver_id": stop.get("driverId"),
                    "stop_number": stop.get("stop"),
                    "lap": stop.get("lap"),
                    "time": stop.get("time"),
                    "duration": stop.get("duration"),
                    "milliseconds": stop.get("milliseconds"),
                })

    return pd.DataFrame(rows)


def extract_driver_standings(season):
    standings_lists = fetch_all_pages(
        f"{BASE_URL}/{season}/driverstandings.json",
        "StandingsTable"
    )

    rows = []

    for standings_list in standings_lists:
        round_no = standings_list.get("round")

        for standing in standings_list.get("DriverStandings", []):
            driver = standing.get("Driver", {})
            constructors = standing.get("Constructors", [])
            constructor = constructors[0] if constructors else {}

            rows.append({
                "season": season,
                "round": safe_int(round_no),
                "driver_id": driver.get("driverId"),
                "driver_code": driver.get("code"),
                "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                "constructor_id": constructor.get("constructorId"),
                "constructor_name": constructor.get("name"),
                "standing_position": standing.get("position"),
                "standing_position_text": standing.get("positionText"),
                "points": standing.get("points"),
                "wins": standing.get("wins"),
            })

    return pd.DataFrame(rows)


def extract_constructor_standings(season):
    standings_lists = fetch_all_pages(
        f"{BASE_URL}/{season}/constructorstandings.json",
        "StandingsTable"
    )

    rows = []

    for standings_list in standings_lists:
        round_no = standings_list.get("round")

        for standing in standings_list.get("ConstructorStandings", []):
            constructor = standing.get("Constructor", {})

            rows.append({
                "season": season,
                "round": safe_int(round_no),
                "constructor_id": constructor.get("constructorId"),
                "constructor_name": constructor.get("name"),
                "constructor_nationality": constructor.get("nationality"),
                "standing_position": standing.get("position"),
                "standing_position_text": standing.get("positionText"),
                "points": standing.get("points"),
                "wins": standing.get("wins"),
            })

    return pd.DataFrame(rows)


def extract_sprint_results(season):
    races = fetch_all_pages(f"{BASE_URL}/{season}/sprint.json", "RaceTable")

    rows = []

    for race in races:
        for result in race.get("SprintResults", []):
            driver = result.get("Driver", {})
            constructor = result.get("Constructor", {})

            rows.append({
                "season": season,
                "round": safe_int(race.get("round")),
                "race_id": f"{season}_{race.get('round')}",
                "race_name": race.get("raceName"),
                "race_date": race.get("date"),

                "driver_id": driver.get("driverId"),
                "driver_code": driver.get("code"),
                "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),

                "constructor_id": constructor.get("constructorId"),
                "constructor_name": constructor.get("name"),

                "position": result.get("position"),
                "position_text": result.get("positionText"),
                "grid": result.get("grid"),
                "laps": result.get("laps"),
                "status": result.get("status"),
                "points": result.get("points"),
            })

    return pd.DataFrame(rows)


def extract_status(results_df):
    if results_df.empty or "status" not in results_df.columns:
        return pd.DataFrame(columns=["status"])

    return (
        results_df[["status"]]
        .dropna()
        .drop_duplicates()
        .sort_values("status")
        .reset_index(drop=True)
    )


def extract_lap_times(season, races_df):
    rows = []

    for _, race in races_df.iterrows():
        round_no = race["round"]

        races = fetch_all_pages(
            f"{BASE_URL}/{season}/{round_no}/laps.json",
            "RaceTable"
        )

        for race_data in races:
            for lap in race_data.get("Laps", []):
                lap_number = lap.get("number")

                for timing in lap.get("Timings", []):
                    rows.append({
                        "season": season,
                        "round": safe_int(round_no),
                        "race_id": f"{season}_{round_no}",
                        "lap_number": lap_number,
                        "driver_id": timing.get("driverId"),
                        "position": timing.get("position"),
                        "lap_time": timing.get("time"),
                    })

    return pd.DataFrame(rows)


def print_round_check(season, name, df):
    if df.empty or "round" not in df.columns:
        print(f"{season} - {name}: no round data")
        return

    rounds = sorted(df["round"].dropna().unique())
    print(f"{season} - {name}: {len(rounds)} rounds -> {rounds}")


def extract_season(season):
    print(f"\nExtracting season: {season}")

    races_df = extract_races(season)
    drivers_df = extract_drivers(season)
    constructors_df = extract_constructors(season)
    results_df = extract_results(season)
    qualifying_df = extract_qualifying(season)
    pitstops_df = extract_pitstops(season, races_df)
    driver_standings_df = extract_driver_standings(season)
    constructor_standings_df = extract_constructor_standings(season)
    sprint_results_df = extract_sprint_results(season)
    lap_times_df = extract_lap_times(season, races_df)

    print_round_check(season, "races", races_df)
    print_round_check(season, "results", results_df)
    print_round_check(season, "qualifying", qualifying_df)
    print_round_check(season, "pitstops", pitstops_df)
    print_round_check(season, "driver_standings", driver_standings_df)
    print_round_check(season, "constructor_standings", constructor_standings_df)
    print_round_check(season, "sprint_results", sprint_results_df)
    print_round_check(season, "lap_times", lap_times_df)

    print(f"Finished extracting season: {season}")

    return {
        "races": races_df,
        "drivers": drivers_df,
        "constructors": constructors_df,
        "results": results_df,
        "qualifying": qualifying_df,
        "pitstops": pitstops_df,
        "driver_standings": driver_standings_df,
        "constructor_standings": constructor_standings_df,
        "sprint_results": sprint_results_df,
        "lap_times": lap_times_df,
    }


def run_extraction(start_season=2025, end_season=2026):
    all_data = {
        "races": [],
        "drivers": [],
        "constructors": [],
        "results": [],
        "qualifying": [],
        "pitstops": [],
        "driver_standings": [],
        "constructor_standings": [],
        "sprint_results": [],
        "lap_times": [],
    }

    for season in range(start_season, end_season + 1):
        season_data = extract_season(season)

        for key, df in season_data.items():
            if not df.empty:
                all_data[key].append(df)

    final_dfs = {}

    for key, dfs in all_data.items():
        if dfs:
            final_dfs[key] = pd.concat(dfs, ignore_index=True)
        else:
            final_dfs[key] = pd.DataFrame()

    final_dfs["status"] = extract_status(final_dfs["results"])

    save_csv(final_dfs["races"], "raw_races.csv")
    save_csv(final_dfs["drivers"], "raw_drivers.csv")
    save_csv(final_dfs["constructors"], "raw_constructors.csv")
    save_csv(final_dfs["results"], "raw_results.csv")
    save_csv(final_dfs["qualifying"], "raw_qualifying.csv")
    save_csv(final_dfs["pitstops"], "raw_pitstops.csv")
    save_csv(final_dfs["driver_standings"], "raw_driver_standings.csv")
    save_csv(final_dfs["constructor_standings"], "raw_constructor_standings.csv")
    save_csv(final_dfs["sprint_results"], "raw_sprint_results.csv")
    save_csv(final_dfs["lap_times"], "raw_lap_times.csv")
    save_csv(final_dfs["status"], "raw_status.csv")

    print("\nAll extraction completed successfully.")


if __name__ == "__main__":
    run_extraction(start_season=2025, end_season=2026)