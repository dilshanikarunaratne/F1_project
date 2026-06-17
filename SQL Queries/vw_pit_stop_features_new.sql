CREATE OR ALTER VIEW vw_pit_stop_features AS
WITH clean_pitstops AS (
    SELECT
        race_id,
        driver_id,
        TRY_CONVERT(FLOAT, duration) * 1000 AS pit_ms
    FROM raw_pitstops
),
constructor_pit_race AS (
    SELECT
        ps.race_id,
        res.constructor_id,
        TRY_CONVERT(INT, r.season) AS season,
        TRY_CONVERT(INT, r.round) AS round,

        AVG(ps.pit_ms) AS constructor_avg_pit_ms,
        STDEV(ps.pit_ms) AS constructor_pit_consistency_ms,
        COUNT(ps.pit_ms) AS total_pit_stops

    FROM clean_pitstops ps
    INNER JOIN raw_results res
        ON ps.race_id = res.race_id
        AND ps.driver_id = res.driver_id
    INNER JOIN raw_races r
        ON ps.race_id = r.race_id
    WHERE ps.pit_ms IS NOT NULL
    GROUP BY
        ps.race_id,
        res.constructor_id,
        TRY_CONVERT(INT, r.season),
        TRY_CONVERT(INT, r.round)
)
SELECT
    race_id,
    constructor_id,

    AVG(constructor_avg_pit_ms) OVER (
        PARTITION BY constructor_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS avg_pit_ms_last_5,

    AVG(constructor_pit_consistency_ms) OVER (
        PARTITION BY constructor_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS pit_consistency_last_5,

    SUM(total_pit_stops) OVER (
        PARTITION BY constructor_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS total_pit_stops_last_5

FROM constructor_pit_race;