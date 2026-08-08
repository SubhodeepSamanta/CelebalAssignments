-- 12. Year-over-year revenue comparison by calendar month.
-- A LEFT JOIN of the monthly totals onto themselves, offset by one year.
-- Months with no prior-year row return NULL rather than being dropped, and the
-- growth percentage guards against a zero denominator.

WITH monthly AS (
    SELECT
        CAST(STRFTIME('%Y', order_date) AS INTEGER) AS year,
        CAST(STRFTIME('%m', order_date) AS INTEGER) AS month,
        ROUND(SUM(line_revenue), 2)                 AS revenue
    FROM revenue_lines
    GROUP BY year, month
)
SELECT
    this_year.year,
    this_year.month,
    this_year.revenue,
    last_year.revenue AS prev_year_revenue,
    CASE
        WHEN last_year.revenue IS NULL OR last_year.revenue = 0 THEN NULL
        ELSE ROUND(100.0 * (this_year.revenue - last_year.revenue) / last_year.revenue, 2)
    END AS yoy_growth_percent
FROM monthly this_year
LEFT JOIN monthly last_year
       ON last_year.year  = this_year.year - 1
      AND last_year.month = this_year.month
ORDER BY this_year.year, this_year.month;
