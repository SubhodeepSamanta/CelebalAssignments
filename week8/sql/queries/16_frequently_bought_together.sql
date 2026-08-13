WITH basket AS (
    SELECT DISTINCT oi.order_id, oi.product_id
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.status <> 'CANCELLED'
),
pairs AS (
    SELECT
        a.product_id AS product_a_id,
        b.product_id AS product_b_id,
        COUNT(*)     AS times_bought_together
    FROM basket a
    JOIN basket b
      ON b.order_id = a.order_id
     AND a.product_id < b.product_id
    GROUP BY a.product_id, b.product_id
)
SELECT
    pa.product_name AS product_a,
    pb.product_name AS product_b,
    p.times_bought_together,
    DENSE_RANK() OVER (ORDER BY p.times_bought_together DESC) AS pair_rank
FROM pairs p
JOIN products pa ON pa.product_id = p.product_a_id
JOIN products pb ON pb.product_id = p.product_b_id
WHERE p.times_bought_together > 1
ORDER BY p.times_bought_together DESC, product_a, product_b
LIMIT 50;
