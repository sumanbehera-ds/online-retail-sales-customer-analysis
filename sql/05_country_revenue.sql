-- Business question: How is merchandise revenue distributed by country, and how does the UK compare with other countries?
WITH country_sales AS (
    SELECT country,
           SUM(line_revenue) AS revenue
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
    GROUP BY country
),
with_totals AS (
    SELECT country,
           revenue,
           SUM(revenue) OVER () AS total_revenue,
           SUM(CASE WHEN country = 'United Kingdom' THEN revenue ELSE 0 END) OVER () AS uk_revenue
    FROM country_sales
)
SELECT country,
       revenue,
       revenue / NULLIF(total_revenue, 0) AS share_of_total,
       uk_revenue,
       total_revenue - uk_revenue AS rest_of_world_revenue
FROM with_totals
ORDER BY revenue DESC;
-- Result: 43 rows returned; first rows: [{"country":"United Kingdom","revenue":"16856330.956000","share_of_total":"0.8556098636","uk_revenue":"16856330.956000","rest_of_world_revenue":"2844623.501000"},{"country":"EIRE","revenue":"623795.850000","share_of_total":"0.0316632299","uk_revenue":"16856330.956000","rest_of_world_revenue":"2844623.501000"},{"country":"Netherlands","revenue":"549775.060000","share_of_total":"0.0279060114","uk_revenue":"16856330.956000","rest_of_world_revenue":"2844623.501000"}]
