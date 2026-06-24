DROP TABLE IF EXISTS podium_prediction_dataset;

SELECT *
INTO podium_prediction_dataset
FROM vw_prediction_dataset;