-- 8. Rank products by total revenue within each category.
-- DENSE_RANK is required by the brief: products on the same revenue must share
-- a rank, and the next product must not have its rank skipped.

WITH product_revenue AS (
    SELECT
        category,
        product_id,
        product_name,
        ROUND(SUM(line_revenue), 2) AS total_revenue
    FROM revenue_lines
    GROUP BY category, product_id, product_name
)
SELECT
    category,
    product_name,
    total_revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category, product_name;
