-- Business question: Which products lead in merchandise revenue and units sold?
WITH product_sales AS (
    SELECT stock_code,
           MAX(description) AS product_description,
           SUM(line_revenue) AS revenue,
           SUM(quantity) AS units_sold
    FROM online_retail_clean
    WHERE is_cancellation = 0
      AND is_non_product = 0
      AND quantity > 0
      AND price > 0
    GROUP BY stock_code
),
ranked AS (
    SELECT *,
           DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
           DENSE_RANK() OVER (ORDER BY units_sold DESC) AS quantity_rank
    FROM product_sales
)
SELECT *
FROM ranked
WHERE revenue_rank <= 10 OR quantity_rank <= 10
ORDER BY revenue_rank, quantity_rank, stock_code;
-- Result: Pending execution when MySQL is available.
