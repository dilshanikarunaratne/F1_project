CREATE OR ALTER VIEW vw_podium_base AS
SELECT
    res.race_id,
    TRY_CONVERT(INT, res.season) AS season,
    TRY_CONVERT(INT, res.round) AS round,

    res.race_name,
    TRY_CONVERT(DATE, res.race_date) AS race_date,

    res.driver_id,
    res.constructor_id,

    res.driver_name,
    res.constructor_name,

    TRY_CONVERT(INT, res.grid) AS grid,
    TRY_CONVERT(INT, q.qualifying_position) AS qualifying_position,

    TRY_CONVERT(INT, res.position) AS finish_position,
    TRY_CONVERT(FLOAT, res.points) AS points,
    TRY_CONVERT(INT, res.laps) AS laps,

    res.status,

    CASE 
        WHEN TRY_CONVERT(INT, res.position) <= 3 THEN 1 
        ELSE 0 
    END AS podium_finish,

    CASE 
        WHEN TRY_CONVERT(INT, res.position) <= 10 THEN 1 
        ELSE 0 
    END AS top_10_finish,

    CASE
        WHEN res.status = 'Finished'
          OR res.status LIKE '+%Lap%'
          OR res.status LIKE '+%Laps%'
        THEN 0
        ELSE 1
    END AS dnf

FROM raw_results res
LEFT JOIN raw_qualifying q
    ON res.race_id = q.race_id
    AND res.driver_id = q.driver_id
    AND res.constructor_id = q.constructor_id;