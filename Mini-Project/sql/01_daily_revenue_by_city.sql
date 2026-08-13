SELECT 
    order_day,
    city,
    total_revenue,
    total_orders,
    avg_basket_size
FROM gold.daily_revenue_by_city
ORDER BY order_day DESC, city ASC;
