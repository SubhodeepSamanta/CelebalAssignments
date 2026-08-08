WITH customer_revenue AS (
    SELECT
        customer_id,
        ROUND(SUM(line_revenue), 2) AS revenue
    FROM revenue_lines
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (ORDER BY revenue DESC)                      AS revenue_rank,
        SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING) AS cumulative_revenue,
        SUM(revenue) OVER ()                                           AS total_revenue,
        COUNT(*)     OVER ()                                           AS customer_count
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue_rank,
    revenue,
    ROUND(cumulative_revenue, 2)                              AS cumulative_revenue,
    ROUND(100.0 * cumulative_revenue / total_revenue, 2)      AS cumulative_percent,
    ROUND(100.0 * revenue_rank / customer_count, 2)           AS top_percent_of_customers
FROM ranked
ORDER BY revenue_rank;
