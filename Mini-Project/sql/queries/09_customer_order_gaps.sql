-- 9. Days between consecutive orders per customer, with an "At Risk" flag.
-- LAG pulls the previous order date onto the current row; JULIANDAY turns the
-- two text dates into numbers that can be subtracted.
-- The average is a second window over the same partition, so the per-order
-- detail and the customer-level verdict come back in one result set.

WITH ordered AS (
    SELECT
        customer_id,
        DATE(order_date) AS order_date,
        LAG(DATE(order_date)) OVER (PARTITION BY customer_id ORDER BY order_date)
            AS previous_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        previous_order_date,
        CAST(JULIANDAY(order_date) - JULIANDAY(previous_order_date) AS INTEGER) AS days_gap
    FROM ordered
)
SELECT
    customer_id,
    order_date,
    previous_order_date,
    days_gap,
    ROUND(AVG(days_gap) OVER (PARTITION BY customer_id), 1) AS avg_gap_days,
    CASE
        WHEN AVG(days_gap) OVER (PARTITION BY customer_id) IS NULL THEN 'Single Order'
        WHEN AVG(days_gap) OVER (PARTITION BY customer_id) > 30   THEN 'At Risk'
        ELSE 'Healthy'
    END AS risk_flag
FROM gaps
ORDER BY customer_id, order_date;
