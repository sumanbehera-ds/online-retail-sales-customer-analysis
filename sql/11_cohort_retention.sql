-- Business question: How many registered customers return in each month after their first purchase?
WITH customer_months AS (
    SELECT DISTINCT customer_id,
           DATE_FORMAT(invoice_date, '%Y-%m-01') AS activity_month
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
      AND customer_id IS NOT NULL
      AND invoice_date IS NOT NULL
),
first_purchase AS (
    SELECT customer_id,
           MIN(activity_month) AS cohort_month
    FROM customer_months
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT f.cohort_month,
           m.activity_month,
           TIMESTAMPDIFF(MONTH, f.cohort_month, m.activity_month) AS month_number,
           COUNT(DISTINCT m.customer_id) AS active_customers
    FROM first_purchase f
    JOIN customer_months m ON m.customer_id = f.customer_id
    GROUP BY f.cohort_month, m.activity_month, month_number
),
cohort_sizes AS (
    SELECT cohort_month,
           COUNT(*) AS cohort_customers
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT a.cohort_month,
       a.activity_month,
       a.activity_month = '2011-12-01' AS is_partial_activity_month,
       a.cohort_month = '2011-12-01' AS is_partial_cohort_month,
       a.month_number,
       s.cohort_customers,
       a.active_customers,
       a.active_customers / NULLIF(s.cohort_customers, 0) AS retention_rate
FROM cohort_activity a
JOIN cohort_sizes s USING (cohort_month)
ORDER BY a.cohort_month, a.month_number;
-- Result: Pending execution when MySQL is available.
