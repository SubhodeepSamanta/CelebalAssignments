SELECT
    category,
    COUNT(DISTINCT order_id)    AS orders,
    SUM(quantity)               AS net_units,
    ROUND(SUM(line_revenue), 2) AS total_revenue
FROM revenue_lines
GROUP BY category
ORDER BY total_revenue DESC;
