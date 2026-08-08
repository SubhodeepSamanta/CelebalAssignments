-- 3. Month-wise order count for the last 12 months.
-- The window is derived from the newest order in the data, not from today's
-- date, so the result stays stable however long after loading it is run.

WITH window_start AS (
    SELECT DATE(MAX(order_date), 'start of month', '-11 months') AS first_month
    FROM orders
)
SELECT
    STRFTIME('%Y-%m', o.order_date) AS order_month,
    COUNT(*)                        AS order_count,
    COUNT(DISTINCT o.customer_id)   AS active_customers
FROM orders o
CROSS JOIN window_start w
WHERE DATE(o.order_date) >= w.first_month
GROUP BY order_month
ORDER BY order_month;
