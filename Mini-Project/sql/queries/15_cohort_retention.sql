-- 15. Cohort analysis: retention by registration month, months 0 to 3.
-- Customers are grouped by the month they registered, then counted in each of
-- the first four months in which they placed an order.
-- month_index is calendar months apart, computed as
--   (year difference * 12) + month difference
-- rather than days / 30, so a cohort boundary is a real month boundary.

WITH cohort AS (
    SELECT
        customer_id,
        registration_date,
        STRFTIME('%Y-%m', registration_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT
        c.cohort_month,
        c.customer_id,
        (CAST(STRFTIME('%Y', o.order_date) AS INTEGER)
       - CAST(STRFTIME('%Y', c.registration_date) AS INTEGER)) * 12
      + (CAST(STRFTIME('%m', o.order_date) AS INTEGER)
       - CAST(STRFTIME('%m', c.registration_date) AS INTEGER)) AS month_index
    FROM cohort c
    JOIN orders o ON o.customer_id = c.customer_id
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM cohort
    GROUP BY cohort_month
),
active AS (
    SELECT cohort_month, month_index, COUNT(DISTINCT customer_id) AS active_customers
    FROM activity
    WHERE month_index BETWEEN 0 AND 3
    GROUP BY cohort_month, month_index
)
SELECT
    s.cohort_month,
    s.cohort_size,
    COALESCE(MAX(CASE WHEN a.month_index = 0 THEN a.active_customers END), 0) AS month_0,
    COALESCE(MAX(CASE WHEN a.month_index = 1 THEN a.active_customers END), 0) AS month_1,
    COALESCE(MAX(CASE WHEN a.month_index = 2 THEN a.active_customers END), 0) AS month_2,
    COALESCE(MAX(CASE WHEN a.month_index = 3 THEN a.active_customers END), 0) AS month_3,
    ROUND(100.0 * COALESCE(MAX(CASE WHEN a.month_index = 1 THEN a.active_customers END), 0)
          / s.cohort_size, 1) AS retention_month_1_percent,
    ROUND(100.0 * COALESCE(MAX(CASE WHEN a.month_index = 3 THEN a.active_customers END), 0)
          / s.cohort_size, 1) AS retention_month_3_percent
FROM sizes s
LEFT JOIN active a ON a.cohort_month = s.cohort_month
GROUP BY s.cohort_month, s.cohort_size
ORDER BY s.cohort_month;
