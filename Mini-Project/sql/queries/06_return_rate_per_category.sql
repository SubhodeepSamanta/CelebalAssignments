-- 6. Return rate per category = returned items / total items.
-- ABS() is what makes the denominator "total items moved": without it the
-- returns would cancel out part of the purchases and inflate the rate.

SELECT
    p.category,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS units_returned,
    SUM(ABS(oi.quantity))                                       AS units_total,
    ROUND(
        100.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
              / SUM(ABS(oi.quantity)), 2)                       AS return_rate_percent
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate_percent DESC;
