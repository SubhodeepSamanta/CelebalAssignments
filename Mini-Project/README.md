# Mini Project — E-Commerce Order Analytics System

Raw order data arrives from four separate sources and it is messy. This project generates that
raw data, cleans it, loads it into SQLite behind a constrained schema, answers sixteen business
questions in SQL, and ships a command-line tool that prints a period report on demand.

Python and SQL only, everything local, no cloud services.

| | |
|---|---|
| **Status** | All five parts complete, full pipeline runs in **~2.3 s** |
| **Edge case tests** | **4 / 4 pass** |
| **Data** | 800 customers, 500 products, **4,758 orders**, **11,016 order lines** |
| **Issues found and handled** | **914 problem rows** across 10 distinct issue types |
| **Dependencies** | `pandas` for the cleaning and analysis stages; everything else is standard library |

---

## Results at a glance

After cleaning, the warehouse holds **4,748 orders** and **10,958 order lines** worth
**4,089,789.78** in net revenue between 2024-08-30 and 2026-08-01.

| Question | Answer |
|---|---|
| Revenue by category | Electronics 2.18M, Home 1.44M, Clothing 392K, Books 75K |
| Return rate | Electronics 3.92%, Home 3.24%, Books 2.27%, Clothing 2.07% |
| Revenue concentration | The top **10%** of customers produce **30.1%** of revenue; the top 20% produce 48.3% |
| Churn risk (avg gap > 30 days) | 478 At Risk, 174 Healthy, 52 single-order customers |
| Category loyalty | 506 of 693 buying customers have shifted category since their first purchase |
| Problem SKUs | 5 products were returned more often than they were bought |
| Never delivered | 49 customers placed orders but never received one |

Every figure above is produced by a file in `sql/queries/` and written to `output/query_results/`.

---

## Project structure

```
Mini-Project/
├── run_pipeline.py                  one command, runs all five stages
├── requirements.txt
├── README.md
│
├── src/
│   ├── config.py                    paths, volumes, the pinned reference date
│   ├── generate_data.py             Part 1 - builds the four raw CSVs
│   ├── clean_data.py                Part 2 - cleaning, validation, issue report
│   ├── database.py                  loads the clean CSVs into SQLite
│   ├── run_analysis.py              Part 3 - executes every query, exports results
│   └── report_tool.py               Part 4 - the CLI report (sqlite3 only)
│
├── sql/
│   ├── schema.sql                   tables, keys, CHECK constraints, two views
│   └── queries/                     the 16 analysis queries, one per file
│
├── tests/
│   └── test_edge_cases.py           Part 5 - the four edge cases
│
├── data/
│   ├── raw/                         generated, deliberately messy
│   ├── clean/                       cleaning output, what gets loaded
│   └── quarantine/                  rows that were dropped, with the reason
│
└── output/
    ├── ecommerce.db                 the SQLite database
    ├── data_quality_report.md       human-readable issue report
    ├── data_quality_report.json     the same report, machine-readable
    └── query_results/               one CSV per query
```

---

## How to run it

### Setup

```bash
cd Mini-Project

python -m venv .venv                  # Windows
.venv\Scripts\activate

python3 -m venv .venv                 # macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Everything at once

```bash
python run_pipeline.py
```

That runs generate → clean → load → analyse → test and prints each stage as it goes.

### One stage at a time

```bash
python -m src.generate_data     # writes data/raw/
python -m src.clean_data        # writes data/clean/ + the quality report
python -m src.database          # builds output/ecommerce.db
python -m src.run_analysis      # runs all 16 queries
python -m src.run_analysis 7 9  # or just these two
python tests/test_edge_cases.py # the four edge cases
```

Stages can also be chained selectively: `python run_pipeline.py clean load analyse`.

### The reporting tool

```bash
python -m src.report_tool --type monthly --start 2026-02-01 --end 2026-07-31
python -m src.report_tool --type weekly  --start 2026-06-01 --end 2026-06-30
python -m src.report_tool                # prompts for all three inputs
```

```
MONTHLY REPORT   2026-02-01 to 2026-07-31   (181 days)
==============================================================================
Month    Orders  Revenue     Customers
-------  ------  ----------  ---------
2026-02     254  264,530.63        199
2026-03     361  358,722.11        252
...

Summary vs previous 181 days (2025-08-04 to 2026-01-31)
------------------------------------------------------------------------------
Metric            This period   Previous      Change
----------------  ------------  ------------  ------
Total orders             2,165         1,182  +83.2%
Revenue           2,172,981.84  1,159,304.60  +87.4%
Unique customers           619           456  +35.7%
```

### Showing it to someone in five minutes

```bash
python run_pipeline.py generate                 # 1. the mess arrives
head -3 data/raw/orders.csv                     #    note the NULL / blank customer_id
python -m src.clean_data                        # 2. every issue named and counted
cat output/data_quality_report.md               #    the audit trail
python -m src.database                          # 3. constrained schema accepts the clean data
python -m src.run_analysis 5 9 15               # 4. three of the harder queries
python -m src.report_tool --type monthly --start 2026-05-01 --end 2026-07-31
python tests/test_edge_cases.py                 # 5. the four edge cases
```

On Windows use `Get-Content -TotalCount 3` instead of `head -3`.

---

## Part 1 — Data generation

`src/generate_data.py`, standard library only. One seeded `random.Random(42)` drives everything, so
the same CSVs come out on every machine.

The data is shaped so the analysis has something real to find rather than uniform noise:

- Order dates never precede the customer's registration date, which is what makes the cohort
  query meaningful.
- Product popularity follows a long tail, so revenue concentrates the way it does in reality.
- Thirty product pairs are seeded as bundles, so "frequently bought together" finds genuine
  affinity instead of coincidence.
- Twelve SKUs are rarely bought but heavily returned, which is what query 5 detects.
- `RETURNED` orders are credit notes: every line on them carries a negative quantity.

**Referential integrity** is guaranteed by construction. `build_order_items()` only ever reads
`order_id` values out of the `orders` list it was handed, so it is not possible for it to invent a
reference. The broken references that the cleaning stage has to catch are added deliberately
afterwards, by `inject_item_defects()`.

Every defect is injected in one place and counted:

| Defect | Count | Share |
|---|---:|---|
| `customer_id` missing (half `NULL`, half empty) | 237 | 5.0% of orders |
| `order_date` written as DD-MM-YYYY | 190 | 4.0% of orders |
| `order_date` set in the future | 10 | — |
| Product names with extra spaces or wrong case | 60 | 12.0% of products |
| Emails missing `@` or missing the domain | 16 | 2.0% of customers |
| Negative quantity (returns) | 316 | 2.9% of order lines |
| `discount_percent` above 100 | 12 | — |
| `quantity` of zero | 20 | — |
| `order_items` pointing at an order that does not exist | 15 | — |

---

## Part 2 — Data cleaning

`src/clean_data.py`. Everything is read with `dtype=str, keep_default_na=False`, so pandas never
gets to guess a type or decide for itself that `"NULL"` means something. The four functions the
brief asks for are `clean_orders()`, `clean_products()`, `validate_emails()` and
`check_referential_integrity()`; `clean_customers()` and `clean_order_items()` are there because
all four tables have to be written out.

| Rule | Applied to | Action |
|---|---|---|
| Trim, collapse repeated spaces | every text column | normalised in place |
| Mixed date formats | `order_date`, `registration_date` | five formats tried in order, rewritten as ISO |
| `""`, `"NULL"`, `"nan"`, `"n/a"` | every text column | becomes a real null |
| Missing `customer_id` | orders | **kept** as SQL `NULL` |
| Future `order_date` | orders | dropped and quarantined |
| Product names | products | trimmed, collapsed, Title Cased |
| Invalid email | customers | **kept**, customer_id listed in the report |
| `order_id` not in orders | order_items | dropped and quarantined |
| `quantity = 0` | order_items | dropped and quarantined |
| `discount_percent` outside 0–100 | order_items | clamped into range |
| Negative quantity | order_items | **kept**, flagged `is_return = 1` |

Three of those decisions are worth defending:

**Orders with no customer_id are kept, not deleted.** The money was still taken. Deleting 5% of
orders would understate revenue by roughly the same amount. Turning the id into a real `NULL`
means every join to `customers` excludes them automatically, so customer-level analysis stays
correct while the revenue totals stay whole.

**Invalid emails are kept, not nulled.** A malformed address is a CRM problem, not an analytics
one. Overwriting it with `NULL` would destroy the only evidence that the record needs fixing.
`validate_emails()` returns the affected `customer_id`s and they are listed in the JSON report.

**Future-dated orders are dropped.** There is no way to know whether the year, the month or the
whole row is wrong, and a single row dated 2027 silently corrupts every "last 12 months" and
year-over-year figure in the project. `config.REFERENCE_DATE` defines "now" as a fixed constant
rather than `datetime.now()`, so the generator, the cleaner and the tests always agree.

Nothing is deleted silently: every dropped row is written to `data/quarantine/` with the reason
attached, and the counts land in `output/data_quality_report.md`.

---

## Part 3 — SQL analysis

`sql/schema.sql` defines the tables with primary keys, foreign keys and `CHECK` constraints, so the
load in `src/database.py` doubles as a test — if cleaning ever regresses, the insert raises
`IntegrityError` instead of quietly storing bad data.

Two views sit on top:

- **`order_lines`** — every line item joined to its order and its product, with the revenue formula
  `quantity * unit_price * (1 - discount_percent / 100)` written **once**. Return lines are
  negative, so their revenue is negative and nets off against the sale automatically.
- **`revenue_lines`** — `order_lines` minus cancelled orders. A cancelled order never billed, so it
  is excluded from anything that reports money. Queries about volume or status use `order_lines`
  instead.

| # | File | Question | Technique |
|---:|---|---|---|
| 1 | `01_revenue_per_category.sql` | Total revenue per category | `GROUP BY`, revenue formula |
| 2 | `02_top_10_customers.sql` | Top 10 customers by order value | join + `LIMIT` |
| 3 | `03_monthly_order_count.sql` | Order count, last 12 months | `STRFTIME`, date arithmetic in a CTE |
| 4 | `04_customers_never_delivered.sql` | Ordered but never delivered | `HAVING SUM(CASE …) = 0` |
| 5 | `05_products_with_more_returns.sql` | More returns than purchases | conditional `SUM` on the sign of quantity |
| 6 | `06_return_rate_per_category.sql` | Return rate per category | `ABS()` for the denominator |
| 7 | `07_running_total_by_region.sql` | Running revenue total per region | `SUM() OVER (PARTITION BY … ORDER BY …)` |
| 8 | `08_product_rank_in_category.sql` | Product rank within category | `DENSE_RANK()` |
| 9 | `09_customer_order_gaps.sql` | Days between consecutive orders | `LAG()`, `JULIANDAY`, second window for the average |
| 10 | `10_monthly_customer_value_bands.sql` | High / Medium / Low per month | three-level CTE chain |
| 11 | `11_customer_quartiles.sql` | Platinum / Gold / Silver / Bronze | `NTILE(4)` |
| 12 | `12_year_over_year_revenue.sql` | Revenue vs the same month last year | self `LEFT JOIN` offset by a year |
| 13 | `13_first_last_category.sql` | First vs most recent category | `FIRST_VALUE` / `LAST_VALUE` with a named `WINDOW` |
| 14 | `14_cumulative_revenue_share.sql` | Pareto curve of revenue | three windows over one ordering |
| 15 | `15_cohort_retention.sql` | Retention by registration cohort | four CTEs + conditional pivot |
| 16 | `16_frequently_bought_together.sql` | Product affinity pairs | self-join with `a.product_id < b.product_id` |

Four details in there are the ones that usually go wrong:

- **`LAST_VALUE` needs an explicit frame.** The default frame ends at the current row, so without
  `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` it returns the current row every time.
- **The running total aggregates to one row per region per day first.** Run the window straight
  over line items and the total steps several times within the same day.
- **`a.product_id < b.product_id`** in the self-join does two jobs at once: it removes the
  self-pairs (A–A) and keeps only one direction of each pair, so A–B appears and B–A does not.
- **Year-over-year uses a `LEFT JOIN`**, so the twelve months with no prior-year data return `NULL`
  rather than disappearing, and the growth calculation guards against a zero denominator.

---

## Part 4 — Reporting tool

`src/report_tool.py`. **Standard library only** — `sqlite3`, `argparse`, `datetime`, no pandas.

Takes a report type (`daily` / `weekly` / `monthly`) and a date range, either as flags or as
interactive prompts, and prints:

- a breakdown at the chosen grain
- total orders, revenue and unique customers
- the top 3 products by revenue
- the same three totals for the immediately preceding window of equal length, with the % change

The comparison window is derived as *the window of identical length ending the day before the
start date*, so comparing a 6-month range compares it against the previous 6 months rather than
against a calendar month.

---

## Part 5 — Edge cases

`tests/test_edge_cases.py`. Four plain Python functions, runnable with `python
tests/test_edge_cases.py` or with `pytest`. Each one checks its case **twice**: against the
cleaning function, and against the database constraint that would catch it if cleaning regressed.

| Case | What happens |
|---|---|
| `order_items.order_id` not in `orders` | `check_referential_integrity()` reports it, cleaning drops it, and the foreign key rejects it |
| `discount_percent > 100` | clamped to 100, so the line is free rather than a refund; the `CHECK` rejects the raw value |
| `quantity = 0` | dropped — a line for zero units is not a transaction; the `CHECK` rejects it |
| `order_date` in the future | dropped and quarantined, and its order lines go with it |

The negative-quantity case is asserted alongside `quantity = 0` to prove the two are treated
differently: zero is an error, negative is a return.

---

## Notes and trade-offs

- **Revenue is net, not gross.** Return lines are negative and reduce it; cancelled orders are
  excluded entirely. Both rules live in `revenue_lines` rather than being repeated in every query.
- **`config.REFERENCE_DATE` is pinned** to `2026-08-01 23:59:59` instead of `datetime.now()`.
  Production code would use the real clock; a fixed value keeps the whole pipeline reproducible and
  keeps the "future date" tests meaningful a year from now.
- **`is_return` is a derived column** added during cleaning. It duplicates `quantity < 0`, which is
  redundant, but it makes the return queries readable and costs one integer per row.
- **The database is rebuilt from scratch** every run (`DROP TABLE IF EXISTS` at the top of
  `schema.sql`), so re-running is always safe and always reproduces the same numbers.
- **At production volume** the line-item table would want partitioning by month and the report tool
  would query a pre-aggregated daily summary rather than scanning the fact table each time. At
  11k rows and a 1.9 MB database, neither is worth the complexity here.
