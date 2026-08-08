PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS revenue_lines;
DROP VIEW  IF EXISTS order_lines;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id       TEXT PRIMARY KEY,
    customer_name     TEXT NOT NULL,
    email             TEXT,
    registration_date TEXT NOT NULL,
    customer_type     TEXT NOT NULL CHECK (customer_type IN ('REGULAR', 'PREMIUM', 'VIP'))
);

CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    subcategory  TEXT NOT NULL,
    cost_price   REAL NOT NULL CHECK (cost_price > 0)
);

CREATE TABLE orders (
    order_id    TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers (customer_id),
    order_date  TEXT NOT NULL,
    status      TEXT NOT NULL
                CHECK (status IN ('PLACED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED')),
    region_code TEXT NOT NULL
);

CREATE TABLE order_items (
    item_id          TEXT PRIMARY KEY,
    order_id         TEXT NOT NULL REFERENCES orders (order_id),
    product_id       TEXT NOT NULL REFERENCES products (product_id),
    quantity         INTEGER NOT NULL CHECK (quantity <> 0),
    unit_price       REAL NOT NULL CHECK (unit_price > 0),
    discount_percent REAL NOT NULL CHECK (discount_percent BETWEEN 0 AND 100),
    is_return        INTEGER NOT NULL CHECK (is_return IN (0, 1))
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_date     ON orders (order_date);
CREATE INDEX idx_items_order     ON order_items (order_id);
CREATE INDEX idx_items_product   ON order_items (product_id);

CREATE VIEW order_lines AS
SELECT
    oi.item_id,
    oi.order_id,
    oi.product_id,
    o.customer_id,
    o.order_date,
    DATE(o.order_date)              AS order_day,
    STRFTIME('%Y-%m', o.order_date) AS order_month,
    o.status,
    o.region_code,
    p.product_name,
    p.category,
    p.subcategory,
    oi.quantity,
    oi.unit_price,
    oi.discount_percent,
    oi.is_return,
    ROUND(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0), 2) AS line_revenue
FROM order_items oi
JOIN orders   o ON o.order_id   = oi.order_id
JOIN products p ON p.product_id = oi.product_id;

CREATE VIEW revenue_lines AS
SELECT * FROM order_lines WHERE status <> 'CANCELLED';
