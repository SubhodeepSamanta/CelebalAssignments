SELECT 
    customer_id,
    name,
    city,
    loyalty_points,
    total_orders,
    total_spend,
    avg_order_value,
    last_order_date
FROM gold.customer_summary
ORDER BY total_spend DESC;
