CREATE OR ALTER VIEW vw_reliability_features AS
WITH reliability_base AS (
    SELECT
        res.raceId,
        res.driverId,
        res.constructorId,
        r.year,
        r.round,
        CASE
            WHEN s.status = 'Finished' OR s.status LIKE '+%Lap%' OR s.status LIKE '+%Laps%'
            THEN 0
            ELSE 1
        END AS dnf_flag
    FROM results res
    INNER JOIN races r
        ON res.raceId = r.raceId
    LEFT JOIN status s
        ON res.statusId = s.statusId
),
driver_reliability AS (
    SELECT
        raceId,
        driverId,

        AVG(CAST(dnf_flag AS FLOAT)) OVER (
            PARTITION BY driverId
            ORDER BY year, round
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS driver_dnf_rate_last_10
    FROM reliability_base
),
constructor_reliability AS (
    SELECT
        raceId,
        constructorId,

        AVG(CAST(dnf_flag AS FLOAT)) OVER (
            PARTITION BY constructorId
            ORDER BY year, round
            ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS constructor_dnf_rate_last_20
    FROM reliability_base
)
SELECT
    rb.raceId,
    rb.driverId,
    rb.constructorId,
    dr.driver_dnf_rate_last_10,
    cr.constructor_dnf_rate_last_20
FROM reliability_base rb
LEFT JOIN driver_reliability dr
    ON rb.raceId = dr.raceId
    AND rb.driverId = dr.driverId
LEFT JOIN constructor_reliability cr
    ON rb.raceId = cr.raceId
    AND rb.constructorId = cr.constructorId;