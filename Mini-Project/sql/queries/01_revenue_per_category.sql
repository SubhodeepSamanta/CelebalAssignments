-- 1. Total revenue per category.
-- revenue = quantity * unit_price * (1 - discount_percent / 100), summed per line.
-- Return lines are negative, so this is net revenue rather than gross sales.

SELECT
    category,
    COUNT(DISTINCT order_id)    AS orders,
    SUM(quantity)               AS net_units,
    ROUND(SUM(line_revenue), 2) AS total_revenue
FROM revenue_lines
GROUP BY category
ORDER BY total_revenue DESC;
