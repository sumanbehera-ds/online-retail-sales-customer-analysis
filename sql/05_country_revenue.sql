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
-- Result: Pending execution when MySQL is available.
