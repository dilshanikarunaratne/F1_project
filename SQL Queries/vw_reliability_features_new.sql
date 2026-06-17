CREATE OR ALTER VIEW vw_reliability_features AS
WITH reliability_base AS (
    SELECT
        res.race_id,
        res.driver_id,
        res.constructor_id,
        r.season,
        r.round,
        CASE
            WHEN res.status = 'Finished' OR res.status LIKE '+%Lap%' OR res.status LIKE '+%Laps%'
            THEN 0
            ELSE 1
        END AS dnf_flag
    FROM raw_results res
    INNER JOIN raw_races r
        ON res.race_id = r.race_id
),
driver_reliability AS (
    SELECT
        race_id,
        driver_id,

        AVG(CAST(dnf_flag AS FLOAT)) OVER (
            PARTITION BY driver_id
            ORDER BY season, round
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS driver_dnf_rate_last_10
    FROM reliability_base
),
constructor_reliability AS (
    SELECT
        race_id,
        constructor_id,

        AVG(CAST(dnf_flag AS FLOAT)) OVER (
            PARTITION BY constructor_id
            ORDER BY season, round
            ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS constructor_dnf_rate_last_20
    FROM reliability_base
)
SELECT
    rb.race_id,
    rb.driver_id,
    rb.constructor_id,
    dr.driver_dnf_rate_last_10,
    cr.constructor_dnf_rate_last_20
FROM reliability_base rb
LEFT JOIN driver_reliability dr
    ON rb.race_id = dr.race_id
    AND rb.driver_id = dr.driver_id
LEFT JOIN constructor_reliability cr
    ON rb.race_id = cr.race_id
    AND rb.constructor_id = cr.constructor_id;