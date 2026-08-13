SELECT 
    category,
    product_id,
    product_name,
    total_units_sold,
    returned_units,
    return_rate_pct
FROM gold.product_return_summary
ORDER BY return_rate_pct DESC, returned_units DESC;
