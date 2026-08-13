SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    COUNT(*)                 AS orders_placed,
    MAX(DATE(o.order_date))  AS last_order_date,
    GROUP_CONCAT(DISTINCT o.status) AS statuses_seen
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_type
HAVING SUM(CASE WHEN o.status = 'DELIVERED' THEN 1 ELSE 0 END) = 0
ORDER BY orders_placed DESC, c.customer_id;
