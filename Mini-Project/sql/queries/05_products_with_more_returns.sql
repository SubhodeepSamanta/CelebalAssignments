WITH movement AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(CASE WHEN oi.quantity > 0 THEN  oi.quantity ELSE 0 END) AS units_purchased,
        SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS units_returned
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT
    product_id,
    product_name,
    category,
    units_purchased,
    units_returned,
    units_returned - units_purchased AS excess_returns
FROM movement
WHERE units_purchased > 0
  AND units_returned > units_purchased
ORDER BY excess_returns DESC;
