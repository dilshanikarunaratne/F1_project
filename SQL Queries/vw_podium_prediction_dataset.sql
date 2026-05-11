CREATE OR ALTER VIEW vw_podium_prediction_dataset AS
SELECT
    -- identifiers
    pb.raceId,
    pb.year,
    pb.round,
    pb.race_name,
    pb.race_date,
    pb.resultId,
    pb.driverId,
    pb.constructorId,
    pb.driver_name,
    pb.constructor_name,

    -- current race features
    pb.grid,
    qf.qualifying_position,
    qf.best_quali_ms,
    qf.qualifying_gap_to_pole_ms,
    qf.teammate_qualifying_gap_ms,

    -- driver recent form
    drf.avg_finish_last_5,
    drf.podiums_last_5,
    drf.avg_qualifying_last_5,
    drf.dnf_rate_last_10,

    -- constructor recent form
    crf.constructor_avg_finish_last_5,
    crf.constructor_points_last_5,
    crf.constructor_podium_rate_last_5,

    -- pit stop features
    psf.avg_pit_ms_last_5,
    psf.pit_consistency_last_5,
    psf.total_pit_stops_last_5,

    -- reliability features
    rf.driver_dnf_rate_last_10,
    rf.constructor_dnf_rate_last_20,

    -- target
    pb.finish_position,
    pb.points,
    pb.podium_finish

FROM podium_base pb

LEFT JOIN vw_qualifying_features qf
    ON pb.raceId = qf.raceId
    AND pb.driverId = qf.driverId
    AND pb.constructorId = qf.constructorId

LEFT JOIN vw_driver_recent_form drf
    ON pb.raceId = drf.raceId
    AND pb.driverId = drf.driverId

LEFT JOIN vw_constructor_recent_form crf
    ON pb.raceId = crf.raceId
    AND pb.constructorId = crf.constructorId

LEFT JOIN vw_pit_stop_features psf
    ON pb.raceId = psf.raceId
    AND pb.constructorId = psf.constructorId

LEFT JOIN vw_reliability_features rf
    ON pb.raceId = rf.raceId
    AND pb.driverId = rf.driverId
    AND pb.constructorId = rf.constructorId;