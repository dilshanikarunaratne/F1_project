SELECT 
    podium_finish,
    COUNT(*) AS count_rows
FROM podium_base
GROUP BY podium_finish;