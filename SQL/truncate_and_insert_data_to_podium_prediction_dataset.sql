BEGIN TRANSACTION;

-- Step 1: Clear existing data
TRUNCATE TABLE dbo.podium_prediction_dataset;

-- Step 2: Insert fresh data from the view
INSERT INTO dbo.podium_prediction_dataset (
    race_id, season, round, race_name, race_date,
    driver_id, constructor_id, driver_name, constructor_name,
    grid, qualifying_position, best_quali_ms, qualifying_gap_to_pole_ms,
    teammate_qualifying_gap_ms, avg_finish_last_5, podiums_last_5,
    avg_qualifying_last_5, dnf_rate_last_10, constructor_avg_finish_last_5,
    constructor_points_last_5, constructor_podium_rate_last_5,
    avg_pit_ms_last_5, pit_consistency_last_5, total_pit_stops_last_5,
    driver_dnf_rate_last_10, constructor_dnf_rate_last_20,
    finish_position, points, laps, status,
    podium_finish, top_10_finish, dnf
)
SELECT
    race_id, season, round, race_name, race_date,
    driver_id, constructor_id, driver_name, constructor_name,
    grid, qualifying_position, best_quali_ms, qualifying_gap_to_pole_ms,
    teammate_qualifying_gap_ms, avg_finish_last_5, podiums_last_5,
    avg_qualifying_last_5, dnf_rate_last_10, constructor_avg_finish_last_5,
    constructor_points_last_5, constructor_podium_rate_last_5,
    avg_pit_ms_last_5, pit_consistency_last_5, total_pit_stops_last_5,
    driver_dnf_rate_last_10, constructor_dnf_rate_last_20,
    finish_position, points, laps, status,
    podium_finish, top_10_finish, dnf
FROM dbo.vw_prediction_dataset;

COMMIT TRANSACTION;
