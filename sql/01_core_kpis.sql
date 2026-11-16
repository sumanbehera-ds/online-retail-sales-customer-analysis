-- Business question: What are merchandise revenue, orders, customers, average order value, and cancellations?
-- KPI definitions: gross and cancelled merchandise values both exclude flagged non-product lines; net revenue subtracts cancelled merchandise value from gross merchandise revenue. Cancellation invoice rate counts all cancellation invoices over all invoices, matching query 06 and the DAX measure. Orders count distinct positive merchandise sales invoices. Registered customers exclude guest rows.
WITH sales AS (
    SELECT *
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
),
gross AS (
    SELECT SUM(line_revenue) AS gross_merchandise_revenue,
           COUNT(DISTINCT invoice) AS orders,
           COUNT(DISTINCT customer_id) AS registered_customers
    FROM sales
),
cancelled_value AS (
    SELECT SUM(ABS(line_revenue)) AS cancelled_merchandise_value
    FROM online_retail_clean
    WHERE is_cancellation = 1
      AND is_non_product = 0
),
cancelled_invoices AS (
    SELECT COUNT(DISTINCT invoice) AS cancelled_invoice_count
    FROM online_retail_clean
    WHERE is_cancellation = 1
),
all_invoices AS (
    SELECT COUNT(DISTINCT invoice) AS invoice_count
    FROM online_retail_clean
)
SELECT g.gross_merchandise_revenue,
       COALESCE(cv.cancelled_merchandise_value, 0) AS cancelled_merchandise_value,
       g.gross_merchandise_revenue - COALESCE(cv.cancelled_merchandise_value, 0) AS net_revenue,
       g.orders,
       g.registered_customers,
       g.gross_merchandise_revenue / NULLIF(g.orders, 0) AS average_order_value,
       ci.cancelled_invoice_count AS cancelled_invoices,
       ci.cancelled_invoice_count / NULLIF(a.invoice_count, 0) AS cancellation_rate
FROM gross g
CROSS JOIN cancelled_value cv
CROSS JOIN cancelled_invoices ci
CROSS JOIN all_invoices a;
-- Result: 1 rows returned; first rows: [{"gross_merchandise_revenue":"19700954.457000","cancelled_merchandise_value":"719692.940000","net_revenue":"18981261.517000","orders":"39516","registered_customers":"5852","average_order_value":"498.5563937899","cancelled_invoices":"8292","cancellation_rate":"0.1546"}]
