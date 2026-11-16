-- Business question: Which products lead in merchandise revenue and units sold?
WITH eligible_sales AS (
    SELECT *
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
),
description_counts AS (
    SELECT stock_code,
           TRIM(description) AS product_description,
           COUNT(*) AS description_rows,
           ROW_NUMBER() OVER (
               PARTITION BY stock_code
               ORDER BY COUNT(*) DESC, TRIM(description) ASC
           ) AS description_rank
    FROM eligible_sales
    WHERE description IS NOT NULL AND TRIM(description) <> ''
    GROUP BY stock_code, TRIM(description)
),
product_sales AS (
    SELECT stock_code,
           SUM(line_revenue) AS revenue,
           SUM(quantity) AS units_sold
    FROM eligible_sales
    GROUP BY stock_code
),
chosen_description AS (
    SELECT stock_code, product_description
    FROM description_counts
    WHERE description_rank = 1
),
ranked AS (
    SELECT p.stock_code,
           d.product_description,
           p.revenue,
           p.units_sold,
           DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
           DENSE_RANK() OVER (ORDER BY units_sold DESC) AS quantity_rank
    FROM product_sales p
    LEFT JOIN chosen_description d USING (stock_code)
)
SELECT *
FROM ranked
WHERE revenue_rank <= 10 OR quantity_rank <= 10
ORDER BY revenue_rank, quantity_rank, stock_code;
-- Result: Pending execution when MySQL is available.
