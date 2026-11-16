-- Business question: What are merchandise revenue, orders, customers, average order value, and cancellations?
-- KPI definitions: gross and cancelled values both exclude flagged non-product lines; net revenue subtracts cancelled merchandise value from gross merchandise revenue. Orders count distinct positive merchandise sales invoices. Registered customers exclude guest rows.
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
cancelled AS (
    SELECT SUM(ABS(line_revenue)) AS cancelled_value,
           COUNT(DISTINCT invoice) AS cancelled_invoices
    FROM online_retail_clean
    WHERE is_cancellation = 1
      AND is_non_product = 0
),
all_invoices AS (
    SELECT COUNT(DISTINCT invoice) AS invoice_count
    FROM online_retail_clean
)
SELECT g.gross_merchandise_revenue,
       g.gross_merchandise_revenue - COALESCE(c.cancelled_value, 0) AS net_revenue,
       g.orders,
       g.registered_customers,
       g.gross_merchandise_revenue / NULLIF(g.orders, 0) AS average_order_value,
       c.cancelled_invoices,
       c.cancelled_invoices / NULLIF(a.invoice_count, 0) AS cancellation_rate
FROM gross g
CROSS JOIN cancelled c
CROSS JOIN all_invoices a;
-- Result: Pending execution when MySQL is available.
