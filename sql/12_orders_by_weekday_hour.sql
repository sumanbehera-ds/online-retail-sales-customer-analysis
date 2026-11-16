-- Business question: On which weekdays and hours were invoices most common?
SELECT DAYNAME(invoice_date) AS weekday_name,
       DAYOFWEEK(invoice_date) AS weekday_number,
       HOUR(invoice_date) AS order_hour,
       COUNT(DISTINCT invoice) AS orders
FROM online_retail_clean
WHERE is_cancellation = 0
  AND is_non_product = 0
  AND quantity > 0
  AND price > 0
  AND invoice_date IS NOT NULL
GROUP BY DAYNAME(invoice_date), DAYOFWEEK(invoice_date), HOUR(invoice_date)
ORDER BY weekday_number, order_hour;
-- Result: 85 rows returned; first rows: [{"weekday_name":"Sunday","weekday_number":"1","order_hour":"9","orders":"6"},{"weekday_name":"Sunday","weekday_number":"1","order_hour":"10","orders":"520"},{"weekday_name":"Sunday","weekday_number":"1","order_hour":"11","orders":"848"}]
