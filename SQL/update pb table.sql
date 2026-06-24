ALTER TABLE podium_base
ADD status VARCHAR(255);

UPDATE pb
SET
    pb.status = s.status
FROM podium_base pb
LEFT JOIN results res
    ON pb.resultId = res.resultId
LEFT JOIN status s
    ON res.statusId = s.statusId;