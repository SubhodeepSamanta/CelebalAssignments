WITH daily AS (
    SELECT
        region_code,
        order_day                   AS order_date,
        ROUND(SUM(line_revenue), 2) AS daily_revenue
    FROM revenue_lines
    GROUP BY region_code, order_day
)
SELECT
    region_code,
    order_date,
    daily_revenue,
    ROUND(
        SUM(daily_revenue) OVER (
            PARTITION BY region_code
            ORDER BY order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2) AS running_total
FROM daily
ORDER BY region_code, order_date;
