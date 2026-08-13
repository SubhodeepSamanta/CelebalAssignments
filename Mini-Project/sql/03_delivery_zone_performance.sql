SELECT 
    zone,
    total_deliveries,
    successful_deliveries,
    failed_deliveries,
    avg_delivery_time_mins,
    failure_rate_pct
FROM gold.delivery_zone_performance
ORDER BY failure_rate_pct DESC, total_deliveries DESC;
