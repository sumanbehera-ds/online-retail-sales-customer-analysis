-- Business question: How did revenue for each calendar month compare with the same month in the prior year?
-- The partial December 2011 is excluded from trend comparisons.
WITH monthly AS (
    SELECT YEAR(invoice_date) AS sales_year,
           MONTH(invoice_date) AS sales_month,
           SUM(line_revenue) AS gross_merchandise_revenue
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
      AND invoice_date < '2011-12-01'
    GROUP BY YEAR(invoice_date), MONTH(invoice_date)
),
with_previous_year AS (
    SELECT sales_year,
           sales_month,
           gross_merchandise_revenue,
           LAG(gross_merchandise_revenue) OVER (PARTITION BY sales_month ORDER BY sales_year) AS previous_year_revenue,
           LAG(sales_year) OVER (PARTITION BY sales_month ORDER BY sales_year) AS previous_year
    FROM monthly
)
SELECT sales_year,
       sales_month,
       previous_year,
       gross_merchandise_revenue,
       previous_year_revenue,
       (gross_merchandise_revenue - previous_year_revenue) / NULLIF(previous_year_revenue, 0) AS yoy_growth_rate
FROM with_previous_year
WHERE previous_year = sales_year - 1
ORDER BY sales_month, sales_year;
-- Result: 12 rows returned; first rows: [{"sales_year":"2011","sales_month":"1","previous_year":"2010","gross_merchandise_revenue":"671933.190000","previous_year_revenue":"613850.812000","yoy_growth_rate":"0.0946196973"},{"sales_year":"2011","sales_month":"2","previous_year":"2010","gross_merchandise_revenue":"508886.200000","previous_year_revenue":"539744.686000","yoy_growth_rate":"-0.0571723758"},{"sales_year":"2011","sales_month":"3","previous_year":"2010","gross_merchandise_revenue":"691257.610000","previous_year_revenue":"764333.851000","yoy_growth_rate":"-0.0956077516"}]
