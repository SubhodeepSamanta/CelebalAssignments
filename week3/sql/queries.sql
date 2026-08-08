DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS orders;

CREATE TABLE customers (
    customer_id   TEXT PRIMARY KEY,
    customer_name TEXT,
    segment       TEXT
);

CREATE TABLE products (
    product_id   TEXT,
    category     TEXT,
    sub_category TEXT,
    product_name TEXT
);

CREATE TABLE orders (
    row_id      INTEGER PRIMARY KEY,
    order_id    TEXT,
    order_date  TEXT,
    ship_date   TEXT,
    ship_mode   TEXT,
    customer_id TEXT,
    product_id  TEXT,
    region      TEXT,
    city        TEXT,
    state       TEXT,
    postal_code TEXT,
    sales       REAL,
    quantity    INTEGER,
    discount    REAL,
    profit      REAL
);

INSERT INTO customers
SELECT DISTINCT customer_id, customer_name, segment
FROM superstore_raw;

INSERT INTO products
SELECT DISTINCT product_id, category, sub_category, product_name
FROM superstore_raw;

INSERT INTO orders
SELECT DISTINCT row_id, order_id, order_date, ship_date, ship_mode,
       customer_id, product_id, region, city, state, postal_code,
       sales, quantity, discount, profit
FROM superstore_raw;


SELECT row_id, order_id, customer_id, ROUND(sales, 2) AS sales
FROM orders
WHERE sales > (SELECT AVG(sales) FROM orders)
ORDER BY sales DESC;

SELECT o.customer_id, c.customer_name, o.order_id, ROUND(o.sales, 2) AS sales
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.sales = (
    SELECT MAX(o2.sales) FROM orders o2 WHERE o2.customer_id = o.customer_id
)
ORDER BY o.sales DESC;

WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
)
SELECT ct.customer_id, c.customer_name, ROUND(ct.total_sales, 2) AS total_sales
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
ORDER BY ct.total_sales DESC;

WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
)
SELECT ct.customer_id, c.customer_name, ROUND(ct.total_sales, 2) AS total_sales
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
WHERE ct.total_sales > (SELECT AVG(total_sales) FROM customer_totals)
ORDER BY ct.total_sales DESC;

WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
)
SELECT c.customer_name,
       ROUND(ct.total_sales, 2) AS total_sales,
       RANK() OVER (ORDER BY ct.total_sales DESC) AS sales_rank
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
ORDER BY sales_rank;

SELECT customer_id, order_id, row_id, ROUND(sales, 2) AS sales,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY sales DESC) AS line_no
FROM orders
ORDER BY customer_id, line_no;

WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
),
ranked AS (
    SELECT c.customer_name, ct.total_sales,
           RANK() OVER (ORDER BY ct.total_sales DESC) AS sales_rank
    FROM customer_totals ct
    JOIN customers c ON c.customer_id = ct.customer_id
)
SELECT customer_name, ROUND(total_sales, 2) AS total_sales, sales_rank
FROM ranked
WHERE sales_rank <= 3
ORDER BY sales_rank;


WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
)
SELECT c.customer_name,
       ROUND(ct.total_sales, 2) AS total_sales,
       RANK() OVER (ORDER BY ct.total_sales DESC) AS sales_rank
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
ORDER BY sales_rank;


WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders GROUP BY customer_id
)
SELECT c.customer_name, ROUND(ct.total_sales, 2) AS total_sales
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
ORDER BY ct.total_sales DESC
LIMIT 5;

WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders GROUP BY customer_id
)
SELECT c.customer_name, ROUND(ct.total_sales, 2) AS total_sales
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
ORDER BY ct.total_sales ASC
LIMIT 5;

SELECT c.customer_name, COUNT(DISTINCT o.order_id) AS order_count
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY o.customer_id, c.customer_name
HAVING COUNT(DISTINCT o.order_id) = 1
ORDER BY c.customer_name;

WITH customer_totals AS (
    SELECT customer_id, SUM(sales) AS total_sales
    FROM orders GROUP BY customer_id
)
SELECT c.customer_name, ROUND(ct.total_sales, 2) AS total_sales
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
WHERE ct.total_sales > (SELECT AVG(total_sales) FROM customer_totals)
ORDER BY ct.total_sales DESC;

WITH order_values AS (
    SELECT customer_id, order_id, SUM(sales) AS order_value
    FROM orders
    GROUP BY customer_id, order_id
)
SELECT c.customer_name, ROUND(MAX(ov.order_value), 2) AS highest_order_value
FROM order_values ov
JOIN customers c ON c.customer_id = ov.customer_id
GROUP BY ov.customer_id, c.customer_name
ORDER BY highest_order_value DESC;
