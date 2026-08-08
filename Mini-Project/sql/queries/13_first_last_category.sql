WITH purchases AS (
    SELECT customer_id, order_date, item_id, category
    FROM revenue_lines
    WHERE customer_id IS NOT NULL
      AND quantity > 0
),
edges AS (
    SELECT DISTINCT
        customer_id,
        FIRST_VALUE(category) OVER w AS first_category,
        LAST_VALUE(category)  OVER w AS latest_category
    FROM purchases
    WINDOW w AS (
        PARTITION BY customer_id
        ORDER BY order_date, item_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
)
SELECT
    customer_id,
    first_category,
    latest_category,
    CASE WHEN first_category = latest_category THEN 'No' ELSE 'Yes' END AS category_shift
FROM edges
ORDER BY customer_id;
