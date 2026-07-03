# Superstore Sales Analysis (SQL)

SQL analysis of the Superstore dataset using subqueries, CTEs and window functions,
run through SQLite from a Jupyter notebook.

## Folder layout

```
Superstore_SQL_Analysis/
├── data/        superstore.csv        (raw dataset)
├── sql/         queries.sql           (all queries as a plain SQL script)
├── output/      query CSVs + superstore.db   (created/refreshed on run)
└── Superstore_SQL_Analysis.ipynb
```

## How to run

Open this folder and launch Jupyter from here, then open the notebook and run the
cells top to bottom:

```
pip install pandas jupyter
jupyter notebook
```

Only `pandas` is needed on top of the standard library (`sqlite3` ships with Python).
Running the notebook rebuilds `output/superstore.db` and writes one CSV per query into
`output/`.

## What it covers

- Step 1: load the CSV into `superstore_raw`, then build `customers`, `orders` and
  `products` with `SELECT DISTINCT`.
- Step 2: the seven required queries (above-average sales, highest sale per customer,
  totals per customer, above-average customers, customer ranking, row numbers per
  customer, top 3).
- Step 3: combined customer / total sales / rank query.
- Mini project: top 5, bottom 5, single-order customers, above-average customers,
  highest order value per customer.

Each row in `orders` is one order line. Questions about an *order value* roll lines up
to the order id; questions about a single sale use the line value.

## Results

### Mini project answers

**1. Top 5 customers** (`output/09_top5_customers.csv`)
Sean Miller (25,043.05), Tamara Chand (19,052.22), Raymond Buch (15,117.34),
Tom Ashbrook (14,595.62), Adrian Barton (14,473.57).

**2. Bottom 5 customers** (`output/10_bottom5_customers.csv`)
Thais Sissman (4.83), Lela Donovan (5.30), Carl Jackson (16.52),
Mitch Gastineau (16.74), Roy Skaria (22.33).

**3. Customers with only one order** (`output/11_single_order_customers.csv`)
12 customers: Anemone Ratner, Anthony O'Donnell, Carl Jackson, Jenna Caffey,
Jocasta Rupert, Lela Donovan, Mitch Gastineau, Patricia Hirasaki, Ricardo Emerson,
Roland Murray, Susan MacKendrick, Theresa Coyne. Counted by distinct order ids.

**4. Customers with above-average sales** (`output/12_above_average_customers.csv`)
294 of 793 customers are above the average total of ~2,897.

**5. Highest order value per customer** (`output/13_highest_order_value.csv`)
Largest is Sean Miller at 23,661.23, then Tamara Chand (18,336.74) and
Raymond Buch (14,052.48). One row per customer.

### Required-query results at a glance

| # | Question | Result | Output file |
|---|----------|--------|-------------|
| 2.1 | Orders above the average sale | 2,360 order lines exceed the ~229.86 average | `01_orders_above_average.csv` |
| 2.2 | Highest single sale per customer | one row per customer | `02_highest_sale_per_customer.csv` |
| 2.3 | Total sales per customer | 793 customers, ranked | `03_total_sales_per_customer.csv` |
| 2.4 | Customers above the average total | 294 customers | `04_above_average_customers.csv` |
| 2.5 | Customer ranking by total sales | full ranking | `05_customer_rank.csv` |
| 2.6 | Row number per line within a customer | partitioned per customer | `06_line_number_within_customer.csv` |
| 2.7 | Top 3 customers | Sean Miller, Tamara Chand, Raymond Buch | `07_top3_customers.csv` |
| 3 | Final: customer, total sales, rank | combined JOIN + CTE + window | `08_final_customer_rank.csv` |

### Short read

Sales are heavily top-weighted: the top three customers alone clear 15k each, while the
average total (~2,897) sits above the median because a few large accounts pull it up,
which is why only 294 customers land above average. Repeat buyers dominate; only 12
customers ordered once.
