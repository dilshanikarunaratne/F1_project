CREATE OR ALTER VIEW vw_qualifying_features AS
WITH quali_clean AS (
    SELECT
        q.raceId,
        q.driverId,
        q.constructorId,
        q.position AS qualifying_position,

        CASE 
            WHEN q.q3 IS NOT NULL AND q.q3 <> '\N' THEN q.q3
            WHEN q.q2 IS NOT NULL AND q.q2 <> '\N' THEN q.q2
            WHEN q.q1 IS NOT NULL AND q.q1 <> '\N' THEN q.q1
            ELSE NULL
        END AS best_quali_time
    FROM qualifying q
),
quali_ms AS (
    SELECT
        raceId,
        driverId,
        constructorId,
        qualifying_position,
        best_quali_time,

        CASE
            WHEN best_quali_time IS NULL THEN NULL
            ELSE
                TRY_CAST(LEFT(best_quali_time, CHARINDEX(':', best_quali_time) - 1) AS FLOAT) * 60000
                +
                TRY_CAST(SUBSTRING(
                    best_quali_time,
                    CHARINDEX(':', best_quali_time) + 1,
                    LEN(best_quali_time)
                ) AS FLOAT) * 1000
        END AS best_quali_ms
    FROM quali_clean
    WHERE best_quali_time IS NULL OR CHARINDEX(':', best_quali_time) > 0
),
quali_features AS (
    SELECT
        raceId,
        driverId,
        constructorId,
        qualifying_position,
        best_quali_ms,

        MIN(best_quali_ms) OVER (
            PARTITION BY raceId
        ) AS pole_time_ms,

        AVG(best_quali_ms) OVER (
            PARTITION BY raceId, constructorId
        ) AS constructor_avg_quali_ms
    FROM quali_ms
)
SELECT
    raceId,
    driverId,
    constructorId,
    qualifying_position,

    best_quali_ms,

    best_quali_ms - pole_time_ms AS qualifying_gap_to_pole_ms,

    best_quali_ms - constructor_avg_quali_ms AS teammate_qualifying_gap_ms

FROM quali_features;