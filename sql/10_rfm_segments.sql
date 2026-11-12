-- Business question: How do registered customers segment by recency, frequency, and monetary value?
WITH eligible_sales AS (
    SELECT *
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
      AND customer_id IS NOT NULL
),
customer_rfm AS (
    SELECT customer_id,
           DATEDIFF((SELECT MAX(invoice_date) FROM eligible_sales), MAX(invoice_date)) AS recency_days,
           COUNT(DISTINCT invoice) AS frequency,
           SUM(line_revenue) AS monetary_value
    FROM eligible_sales
    GROUP BY customer_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC, customer_id) AS recency_score,
           6 - NTILE(5) OVER (ORDER BY frequency DESC, customer_id) AS frequency_score,
           6 - NTILE(5) OVER (ORDER BY monetary_value DESC, customer_id) AS monetary_score
    FROM customer_rfm
),
segments AS (
    SELECT *,
           CASE
               WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
               WHEN frequency_score >= 4 AND monetary_score >= 3 THEN 'Loyal'
               WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
               WHEN recency_score <= 2 THEN 'Hibernating'
               ELSE 'Potential'
           END AS segment
    FROM scored
)
SELECT segment,
       COUNT(*) AS customers,
       SUM(monetary_value) AS revenue,
       AVG(recency_days) AS average_recency_days,
       AVG(frequency) AS average_orders
FROM segments
GROUP BY segment
ORDER BY revenue DESC;
-- Result: Pending execution when MySQL is available.
