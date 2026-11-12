-- Business question: How did monthly merchandise revenue change, and what was month-over-month growth?
-- The partial December 2011 is excluded from trend comparisons.
WITH monthly AS (
    SELECT DATE_FORMAT(invoice_date, '%Y-%m-01') AS month_start,
           SUM(line_revenue) AS gross_merchandise_revenue
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
      AND invoice_date < '2011-12-01'
    GROUP BY DATE_FORMAT(invoice_date, '%Y-%m-01')
),
with_previous AS (
    SELECT month_start,
           gross_merchandise_revenue,
           LAG(gross_merchandise_revenue) OVER (ORDER BY month_start) AS previous_month_revenue
    FROM monthly
)
SELECT month_start,
       gross_merchandise_revenue,
       previous_month_revenue,
       (gross_merchandise_revenue - previous_month_revenue) / NULLIF(previous_month_revenue, 0) AS mom_growth_rate
FROM with_previous
ORDER BY month_start;
-- Result: Pending execution when MySQL is available.
