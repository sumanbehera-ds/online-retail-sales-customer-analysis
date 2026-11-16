-- Business question: How large was canceled merchandise value compared with positive merchandise sales?
WITH monthly_values AS (
    SELECT DATE_FORMAT(invoice_date, '%Y-%m-01') AS month_start,
           SUM(CASE WHEN is_cancellation = 0 AND is_non_product = 0 AND quantity > 0 AND price > 0 THEN line_revenue ELSE 0 END) AS gross_merchandise_revenue,
           SUM(CASE WHEN is_cancellation = 1 AND is_non_product = 0 THEN ABS(line_revenue) ELSE 0 END) AS cancelled_value
    FROM online_retail_clean
    WHERE invoice_date IS NOT NULL
    GROUP BY DATE_FORMAT(invoice_date, '%Y-%m-01')
)
SELECT month_start,
       month_start = '2011-12-01' AS is_partial_month,
       gross_merchandise_revenue,
       cancelled_value,
       cancelled_value / NULLIF(gross_merchandise_revenue, 0) AS cancelled_value_share
FROM monthly_values
ORDER BY month_start;
-- Result: Pending execution when MySQL is available.
