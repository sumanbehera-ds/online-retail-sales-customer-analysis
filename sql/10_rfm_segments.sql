-- Business question: How do registered customers segment by recency, frequency, and monetary value?
-- PERCENT_RANK keeps identical metric values tied; it may create uneven-sized score groups.
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
           LEAST(5, 1 + FLOOR(5 * PERCENT_RANK() OVER (ORDER BY recency_days DESC))) AS recency_score,
           LEAST(5, 1 + FLOOR(5 * PERCENT_RANK() OVER (ORDER BY frequency))) AS frequency_score,
           LEAST(5, 1 + FLOOR(5 * PERCENT_RANK() OVER (ORDER BY monetary_value))) AS monetary_score
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
-- Result: 5 rows returned; first rows: [{"segment":"Champions","customers":"1249","revenue":"11550770.495000","average_recency_days":"18.6541","average_orders":"17.3251"},{"segment":"Loyal","customers":"857","revenue":"2722878.876000","average_recency_days":"165.0105","average_orders":"8.5204"},{"segment":"Potential","customers":"1676","revenue":"1572442.934000","average_recency_days":"60.7977","average_orders":"2.3878"}]
