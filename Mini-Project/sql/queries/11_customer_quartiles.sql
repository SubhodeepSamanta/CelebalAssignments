-- 11. NTILE segmentation: customers split into four quartiles by lifetime value.
-- NTILE fills groups by position, not by value, so the quartiles always come
-- out the same size even if the money is lopsided.
-- The label is applied in a second step because a window function cannot be
-- referenced by alias inside the same SELECT.

WITH lifetime AS (
    SELECT
        customer_id,
        ROUND(SUM(line_revenue), 2) AS total_value
    FROM revenue_lines
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
quartiles AS (
    SELECT
        customer_id,
        total_value,
        NTILE(4) OVER (ORDER BY total_value DESC) AS quartile
    FROM lifetime
)
SELECT
    q.customer_id,
    c.customer_name,
    q.total_value,
    q.quartile,
    CASE q.quartile
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        ELSE        'Bronze'
    END AS quartile_label
FROM quartiles q
JOIN customers c ON c.customer_id = q.customer_id
ORDER BY q.total_value DESC;
