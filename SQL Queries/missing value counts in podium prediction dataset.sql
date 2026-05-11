SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN qualifying_position IS NULL THEN 1 ELSE 0 END) AS missing_qualifying_position,
    SUM(CASE WHEN avg_finish_last_5 IS NULL THEN 1 ELSE 0 END) AS missing_avg_finish_last_5,
    SUM(CASE WHEN constructor_avg_finish_last_5 IS NULL THEN 1 ELSE 0 END) AS missing_constructor_form,
    SUM(CASE WHEN avg_pit_ms_last_5 IS NULL THEN 1 ELSE 0 END) AS missing_pit_features
FROM vw_podium_prediction_dataset;