-- Business question: What share of invoices were cancellations in each month?
WITH monthly_invoices AS (
    SELECT DATE_FORMAT(invoice_date, '%Y-%m-01') AS month_start,
           COUNT(DISTINCT invoice) AS all_invoices,
           COUNT(DISTINCT CASE WHEN is_cancellation = 1 THEN invoice END) AS cancelled_invoices
    FROM online_retail_clean
    WHERE invoice IS NOT NULL
      AND invoice_date IS NOT NULL
    GROUP BY DATE_FORMAT(invoice_date, '%Y-%m-01')
)
SELECT month_start,
       month_start = '2011-12-01' AS is_partial_month,
       all_invoices,
       cancelled_invoices,
       cancelled_invoices / NULLIF(all_invoices, 0) AS cancellation_rate
FROM monthly_invoices
ORDER BY month_start;
-- Result: 25 rows returned; first rows: [{"month_start":"2009-12-01","is_partial_month":"0","all_invoices":"2330","cancelled_invoices":"401","cancellation_rate":"0.1721"},{"month_start":"2010-01-01","is_partial_month":"0","all_invoices":"1633","cancelled_invoices":"300","cancellation_rate":"0.1837"},{"month_start":"2010-02-01","is_partial_month":"0","all_invoices":"1969","cancelled_invoices":"240","cancellation_rate":"0.1219"}]
