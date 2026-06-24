CREATE OR ALTER VIEW vw_driver_recent_form AS
WITH driver_race AS (
    SELECT
        res.raceId,
        res.driverId,
        r.year,
        r.round,
        res.positionOrder AS finish_position,
        res.points,
        q.position AS qualifying_position,
        CASE 
            WHEN res.positionOrder <= 3 THEN 1 
            ELSE 0 
        END AS podium_flag,
        CASE
            WHEN s.status = 'Finished' OR s.status LIKE '+%Lap%' OR s.status LIKE '+%Laps%'
            THEN 0
            ELSE 1
        END AS dnf_flag
    FROM results res
    INNER JOIN races r
        ON res.raceId = r.raceId
    LEFT JOIN qualifying q
        ON res.raceId = q.raceId
        AND res.driverId = q.driverId
        AND res.constructorId = q.constructorId
    LEFT JOIN status s
        ON res.statusId = s.statusId
)
SELECT
    raceId,
    driverId,

    AVG(CAST(finish_position AS FLOAT)) OVER (
        PARTITION BY driverId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS avg_finish_last_5,

    SUM(podium_flag) OVER (
        PARTITION BY driverId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS podiums_last_5,

    AVG(CAST(qualifying_position AS FLOAT)) OVER (
        PARTITION BY driverId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS avg_qualifying_last_5,

    AVG(CAST(dnf_flag AS FLOAT)) OVER (
        PARTITION BY driverId
        ORDER BY year, round
        ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
    ) AS dnf_rate_last_10

FROM driver_race;