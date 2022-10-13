-- (1) For each exchange, provide the count of distinct coins traded 
-- and the median task_run of those coins.
WITH coins_cte AS (
    SELECT *,
        UNNEST(exchanges) AS exchanges_unnest
    FROM coins
) 
SELECT exchanges_unnest,
       COUNT(DISTINCT id) AS count_of_distinct_coins,
       PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY task_run) AS median
FROM coins_cte
GROUP BY exchanges_unnest
;




-- (2) Show all exchanges containing the letter 'x'
WITH coins_cte AS (
    SELECT *,
        UNNEST(exchanges) AS exchanges_unnest
    FROM coins
) 
SELECT DISTINCT exchanges_unnest
FROM coins_cte
WHERE exchanges_unnest LIKE '%x%'
;

