CREATE OR ALTER VIEW vw_driver_recent_form AS
WITH driver_race AS (
    SELECT
        res.race_id,
        res.driver_id,
        r.season,
        r.round,
        res.position AS finish_position,
        res.points,
        q.qualifying_position,
        CASE 
            WHEN res.position <= 3 THEN 1 
            ELSE 0 
        END AS podium_flag,
        CASE
            WHEN res.status = 'Finished' OR res.status LIKE '+%Lap%' OR res.status LIKE '+%Laps%'
            THEN 0
            ELSE 1
        END AS dnf_flag
    FROM raw_results res
    INNER JOIN raw_races r
        ON res.race_id = r.race_id
    LEFT JOIN raw_qualifying q
        ON res.race_id = q.race_id
        AND res.driver_id = q.driver_id
        AND res.constructor_id = q.constructor_id
)
SELECT
    race_id,
    driver_id,

    AVG(CAST(finish_position AS FLOAT)) OVER (
        PARTITION BY driver_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS avg_finish_last_5,

    SUM(podium_flag) OVER (
        PARTITION BY driver_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS podiums_last_5,

    AVG(CAST(qualifying_position AS FLOAT)) OVER (
        PARTITION BY driver_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS avg_qualifying_last_5,

    AVG(CAST(dnf_flag AS FLOAT)) OVER (
        PARTITION BY driver_id
        ORDER BY season, round
        ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
    ) AS dnf_rate_last_10

FROM driver_race;