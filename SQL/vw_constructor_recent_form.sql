CREATE OR ALTER VIEW vw_constructor_recent_form AS
WITH constructor_race AS (
    SELECT
        res.raceId,
        res.constructorId,
        r.year,
        r.round,
        AVG(CAST(res.positionOrder AS FLOAT)) AS constructor_avg_finish,
        SUM(CAST(res.points AS FLOAT)) AS constructor_points,
        SUM(CASE WHEN res.positionOrder <= 3 THEN 1 ELSE 0 END) AS constructor_podiums
    FROM results res
    INNER JOIN races r
        ON res.raceId = r.raceId
    GROUP BY
        res.raceId,
        res.constructorId,
        r.year,
        r.round
)
SELECT
    raceId,
    constructorId,

    AVG(constructor_avg_finish) OVER (
        PARTITION BY constructorId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS constructor_avg_finish_last_5,

    SUM(constructor_points) OVER (
        PARTITION BY constructorId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS constructor_points_last_5,

    AVG(CAST(constructor_podiums AS FLOAT)) OVER (
        PARTITION BY constructorId
        ORDER BY year, round
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    ) AS constructor_podium_rate_last_5

FROM constructor_race;