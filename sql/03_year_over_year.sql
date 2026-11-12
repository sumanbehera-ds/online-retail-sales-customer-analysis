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
-- Result: Pending execution when MySQL is available.
