ALTER TABLE podium_prediction_dataset
ADD status VARCHAR(255);

DELETE FROM podium_prediction_dataset;

INSERT INTO podium_prediction_dataset (
    raceId,
    year,
    round,
    race_name,
    race_date,
    resultId,
    driverId,
    constructorId,
    driver_name,
    constructor_name,

    grid,
    qualifying_position,
    best_quali_ms,
    qualifying_gap_to_pole_ms,
    teammate_qualifying_gap_ms,
    status,

    avg_finish_last_5,
    podiums_last_5,
    avg_qualifying_last_5,
    dnf_rate_last_10,

    constructor_avg_finish_last_5,
    constructor_points_last_5,
    constructor_podium_rate_last_5,

    avg_pit_ms_last_5,
    pit_consistency_last_5,
    total_pit_stops_last_5,

    driver_dnf_rate_last_10,
    constructor_dnf_rate_last_20,

    finish_position,
    points,
    podium_finish
)
SELECT
    raceId,
    year,
    round,
    race_name,
    race_date,
    resultId,
    driverId,
    constructorId,
    driver_name,
    constructor_name,

    grid,
    qualifying_position,
    best_quali_ms,
    qualifying_gap_to_pole_ms,
    teammate_qualifying_gap_ms,
    status,

    avg_finish_last_5,
    podiums_last_5,
    avg_qualifying_last_5,
    dnf_rate_last_10,

    constructor_avg_finish_last_5,
    constructor_points_last_5,
    constructor_podium_rate_last_5,

    avg_pit_ms_last_5,
    pit_consistency_last_5,
    total_pit_stops_last_5,

    driver_dnf_rate_last_10,
    constructor_dnf_rate_last_20,

    finish_position,
    points,
    podium_finish

FROM vw_podium_prediction_dataset;