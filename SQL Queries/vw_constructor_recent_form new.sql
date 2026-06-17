
CREATE OR ALTER VIEW vw_constructor_recent_form AS
WITH constructor_race AS (
    SELECT
        res.race_id,
        res.constructor_id,
        r.season,
        r.round,
        AVG(CAST(res.position AS FLOAT)) AS constructor_avg_finish,
        SUM(CAST(res.points AS FLOAT)) AS constructor_points,
        SUM(CASE WHEN res.position <= 3 THEN 1 ELSE 0 END) AS constructor_podiums
    FROM raw_results res
    INNER JOIN raw_races r
        ON res.race_id = r.race_id
    GROUP BY
        res.race_id,
        res.constructor_id,
        r.season,
        r.round
)
SELECT
    race_id,
    constructor_id,

    AVG(constructor_avg_finish) OVER (
        PARTITION BY constructor_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS constructor_avg_finish_last_5,

    SUM(constructor_points) OVER (
        PARTITION BY constructor_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS constructor_points_last_5,

    AVG(CAST(constructor_podiums AS FLOAT)) OVER (
        PARTITION BY constructor_id
        ORDER BY season, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS constructor_podium_rate_last_5

FROM constructor_race;