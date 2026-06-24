CREATE OR ALTER VIEW vw_prediction_dataset AS
SELECT
    pb.race_id,
    pb.season,
    pb.round,
    pb.race_name,
    pb.race_date,

    pb.driver_id,
    pb.constructor_id,
    pb.driver_name,
    pb.constructor_name,

    pb.grid,
    qf.qualifying_position,
    qf.best_quali_ms,
    qf.qualifying_gap_to_pole_ms,
    qf.teammate_qualifying_gap_ms,

    drf.avg_finish_last_5,
    drf.podiums_last_5,
    drf.avg_qualifying_last_5,
    drf.dnf_rate_last_10,

    crf.constructor_avg_finish_last_5,
    crf.constructor_points_last_5,
    crf.constructor_podium_rate_last_5,

    psf.avg_pit_ms_last_5,
    psf.pit_consistency_last_5,
    psf.total_pit_stops_last_5,

    rf.driver_dnf_rate_last_10,
    rf.constructor_dnf_rate_last_20,

    pb.finish_position,
    pb.points,
    pb.laps,
    pb.status,

    pb.podium_finish,
    pb.top_10_finish,
    pb.dnf

FROM vw_podium_base pb

LEFT JOIN vw_qualifying_features qf
    ON pb.race_id = qf.race_id
    AND pb.driver_id = qf.driver_id
    AND pb.constructor_id = qf.constructor_id

LEFT JOIN vw_driver_recent_form drf
    ON pb.race_id = drf.race_id
    AND pb.driver_id = drf.driver_id

LEFT JOIN vw_constructor_recent_form crf
    ON pb.race_id = crf.race_id
    AND pb.constructor_id = crf.constructor_id

LEFT JOIN vw_pit_stop_features psf
    ON pb.race_id = psf.race_id
    AND pb.constructor_id = psf.constructor_id

LEFT JOIN vw_reliability_features rf
    ON pb.race_id = rf.race_id
    AND pb.driver_id = rf.driver_id
    AND pb.constructor_id = rf.constructor_id;