CREATE OR ALTER VIEW vw_pit_stop_features AS
WITH constructor_pit_race AS (
    SELECT
        ps.raceId,
        res.constructorId,
        r.year,
        r.round,
        STDEV(TRY_CAST(NULLIF(ps.milliseconds, '\N') AS FLOAT)) AS constructor_avg_pit_ms,
        STDEV(TRY_CAST(NULLIF(ps.milliseconds, '\N') AS FLOAT)) AS constructor_pit_consistency_ms,
        COUNT(*) AS total_pit_stops
    FROM pit_stops ps
    INNER JOIN results res
        ON ps.raceId = res.raceId
        AND ps.driverId = res.driverId
    INNER JOIN races r
        ON ps.raceId = r.raceId
    GROUP BY
        ps.raceId,
        res.constructorId,
        r.year,
        r.round
)
SELECT
    raceId,
    constructorId,

    AVG(constructor_avg_pit_ms) OVER (
        PARTITION BY constructorId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS avg_pit_ms_last_5,

    AVG(constructor_pit_consistency_ms) OVER (
        PARTITION BY constructorId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS pit_consistency_last_5,

    SUM(total_pit_stops) OVER (
        PARTITION BY constructorId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS total_pit_stops_last_5

FROM constructor_pit_race;