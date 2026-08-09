# Data quality report

Generated 2026-08-09 12:21:04 | reference date 2026-08-01

## Row counts

| Table | Raw | Clean | Dropped |
|---|---:|---:|---:|
| customers | 800 | 800 | 0 |
| products | 500 | 500 | 0 |
| orders | 4,758 | 4,748 | 10 |
| order_items | 11,016 | 10,958 | 58 |

## Issues found

| Table | Issue | Rows | Action taken |
|---|---|---:|---|
| customers | invalid email address | 16 | value kept, ids listed in the JSON report |
| products | product_name needed trimming or re-casing | 60 | normalised to Title Case |
| orders | customer_id missing or the literal text 'NULL' | 237 | kept as SQL NULL |
| orders | order_date not in YYYY-MM-DD HH:MM:SS | 190 | re-parsed and rewritten as ISO |
| orders | order_date in the future | 10 | row dropped |
| order_items | order_id never existed in the raw orders file | 15 | row dropped (subset of the check below) |
| order_items | order_id not present in cleaned orders | 38 | row dropped |
| order_items | quantity is zero or unreadable | 20 | row dropped |
| order_items | discount_percent outside 0-100 | 12 | clamped into 0-100 (missing treated as 0) |
| order_items | negative quantity (return lines) | 316 | kept and flagged with is_return = 1 |

**914 problem rows across 10 distinct issues.**
