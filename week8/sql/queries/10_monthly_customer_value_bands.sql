WITH monthly_revenue AS (
    SELECT
        customer_id,
        order_month,
        ROUND(SUM(line_revenue), 2) AS revenue
    FROM revenue_lines
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, order_month
),
banded AS (
    SELECT
        order_month,
        customer_id,
        revenue,
        CASE
            WHEN revenue > 10000 THEN 'High'
            WHEN revenue >= 5000 THEN 'Medium'
            ELSE 'Low'
        END AS value_band
    FROM monthly_revenue
)
SELECT
    order_month,
    value_band,
    COUNT(*)                 AS customers,
    ROUND(SUM(revenue), 2)   AS band_revenue
FROM banded
GROUP BY order_month, value_band
ORDER BY
    order_month,
    CASE value_band WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;
