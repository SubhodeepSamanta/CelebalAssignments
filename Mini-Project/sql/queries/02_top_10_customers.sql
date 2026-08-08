-- 2. Top 10 customers by total order value.

SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(DISTINCT r.order_id)    AS orders,
    ROUND(SUM(r.line_revenue), 2) AS total_order_value
FROM revenue_lines r
JOIN customers c ON c.customer_id = r.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_type
ORDER BY total_order_value DESC
LIMIT 10;
