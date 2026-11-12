-- Business question: What share of registered customers placed more than one order?
WITH customer_orders AS (
    SELECT customer_id,
           COUNT(DISTINCT invoice) AS order_count
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
      AND customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT COUNT(*) AS registered_customers,
       SUM(order_count >= 2) AS repeat_customers,
       SUM(order_count >= 2) / NULLIF(COUNT(*), 0) AS repeat_customer_rate
FROM customer_orders;
-- Result: Pending execution when MySQL is available.
