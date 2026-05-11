SELECT
    r.raceId,
    r.year,
    r.round,
    r.name AS race_name,
    r.date AS race_date,

    res.resultId,
    res.driverId,
    res.constructorId,

    d.forename + ' ' + d.surname AS driver_name,
    c.name AS constructor_name,

    res.grid,
    q.position AS qualifying_position,

    res.positionOrder AS finish_position,
    res.points,
    res.laps,
    res.statusId,

    CASE
        WHEN res.positionOrder <= 3 THEN 1
        ELSE 0
    END AS podium_finish

INTO podium_base
FROM results res
LEFT JOIN races r
    ON res.raceId = r.raceId
LEFT JOIN drivers d
    ON res.driverId = d.driverId
LEFT JOIN constructors c
    ON res.constructorId = c.constructorId
LEFT JOIN qualifying q
    ON res.raceId = q.raceId
    AND res.driverId = q.driverId
    AND res.constructorId = q.constructorId;