-- Business question: Who are the ten highest-spending registered customers, and what share of revenue comes from the top spending decile?
WITH customer_sales AS (
    SELECT customer_id,
           SUM(line_revenue) AS revenue,
           COUNT(DISTINCT invoice) AS orders
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
      AND customer_id IS NOT NULL
    GROUP BY customer_id
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY revenue DESC, customer_id) AS customer_rank,
           NTILE(10) OVER (ORDER BY revenue DESC, customer_id) AS spending_decile
    FROM customer_sales
),
totals AS (
    SELECT SUM(revenue) AS all_customer_revenue,
           SUM(CASE WHEN spending_decile = 1 THEN revenue ELSE 0 END) AS top_decile_revenue
    FROM ranked
)
SELECT r.revenue,
       r.orders,
       r.customer_rank,
       t.top_decile_revenue,
       t.top_decile_revenue / NULLIF(t.all_customer_revenue, 0) AS top_decile_revenue_share
FROM ranked r
CROSS JOIN totals t
WHERE r.customer_rank <= 10
ORDER BY r.customer_rank;
-- Result: Pending execution when MySQL is available.
