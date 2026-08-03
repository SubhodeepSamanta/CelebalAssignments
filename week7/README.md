# Assignment 7 — Incremental Data Processing with Delta Lake

Load a customer dataset into a Delta table, clean it, simulate an incremental change feed, apply a
**`MERGE`** to upsert the changes, validate the result, and publish a final dataset with a summary.

Implemented twice — **SCD Type 1** (overwrite in place) and **SCD Type 2** (full history with
effective dates) — on the `Sample - Superstore` dataset.

| | |
|---|---|
| **Status** | Notebook executed end to end, **0 errors** |
| **Validation** | **31 / 31 assertions pass** |
| **Engine** | `deltalake` 1.6.2 — delta-rs, the native Delta Lake implementation |
| **Also included** | A PySpark + Delta Spark version for Databricks / Colab |

---

## Results at a glance

| Stage | Rows | Distinct customers |
|---|---:|---:|
| `customer_master.csv` (raw) | 866 | 793 |
| `silver_customer_master` (cleaned) | 793 | 793 |
| `customer_incremental.csv` (raw) | 162 | 157 |
| `gold_customer_scd1` after `MERGE` | **838** | 838 |
| `gold_customer_scd2` (all versions) | **939** | 838 |
| &nbsp;&nbsp;• current versions | 838 | |
| &nbsp;&nbsp;• expired versions | 101 | |

**Incremental batch classification** — 45 `NEW`, 101 `CHANGED`, 11 `UNCHANGED`.

**SCD1 `MERGE`** → 112 rows updated (101 changed + 11 identical), 45 inserted, `v0 → v1`.
**SCD2 `MERGE`** → 101 versions closed out, 146 rows inserted (101 new versions + 45 new customers).

Every number above is asserted in the notebook and written to `output/run_summary.json`.

---

## Project structure

```
Assignment7/
├── data/
│   ├── superstore_raw.csv                    source export (9,994 order lines)
│   ├── customer_master.csv                   866-row snapshot (nulls, dupes, dirty strings)
│   └── customer_incremental.csv              162-row change feed
│
├── notebooks/
│   ├── delta_scd_assignment.ipynb            ← MAIN submission, executed with outputs
│   └── delta_scd_assignment_pyspark.ipynb    PySpark / Databricks variant
│
├── screenshots/
│   ├── 01_data_loading/        (5)
│   ├── 02_data_cleaning/       (6)
│   ├── 03_scd1/                (5)
│   ├── 04_scd2/                (5)
│   ├── 05_validation/          (4)
│   └── 06_final_output/        (5, incl. the matplotlib summary figure)
│
├── report/
│   └── assignment_summary.pdf                5-page write-up
│
├── output/                                   produced by running the notebook
│   ├── delta_lake/                           the actual Delta tables + _delta_log
│   ├── final_customer_scd1.csv
│   ├── final_customer_scd2.csv
│   ├── summary_by_region.csv
│   ├── incremental_change_classification.csv
│   └── run_summary.json
│
├── scripts/
│   ├── generate_datasets.py                  rebuilds the two CSVs from the Superstore export
│   ├── capture_screenshots.py                re-renders screenshots/ from the executed notebook
│   └── build_report.py                       rebuilds the PDF from run_summary.json
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## How to run it

```bash
pip install -r requirements.txt
jupyter notebook notebooks/delta_scd_assignment.ipynb   # then Run All
```

Or headless:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/delta_scd_assignment.ipynb
python scripts/capture_screenshots.py     # re-render the screenshots
python scripts/build_report.py            # rebuild the PDF
```

No Java, no Spark cluster, no Maven download — `pip install deltalake` is the only requirement.
The notebook is **idempotent**: `RESET_LAKE = True` drops and rebuilds every Delta table on each
run, so re-executing always reproduces the numbers above.

### Running the PySpark version instead

| Environment | What to do |
|---|---|
| **Databricks** (Community Edition is fine) | Import the notebook, upload the two CSVs, set `DATA_DIR`, skip the SparkSession cell |
| **Google Colab** | Run the first cell — it installs Java 17, `pyspark` and `delta-spark` |
| **Local** | Needs Java 8/11/17 on `PATH` and outbound access to Maven Central for the Delta JARs |

---

## Why delta-rs is the primary engine

Delta Lake has two official engines: **Delta Spark** (JVM) and **delta-rs** (native Rust).
Both write the *same* Delta transaction log, so a table created by one is fully readable by the
other — including by Databricks.

delta-rs was chosen for the main notebook because it installs with a single `pip install` and needs
no JVM, no `JAVA_HOME`, and no Maven download at session start. That means it runs identically on a
laptop, in Colab, and in a grading environment, with nothing to configure and nothing to break.
The tables it produces here sit at **Delta reader v1 / writer v2** — the most compatible protocol
level — because timestamps are stored timezone-aware and date-only columns as `date32`.

The Spark notebook expresses the same pipeline with `DeltaTable.merge(...)`,
`whenMatchedUpdateAll()` / `whenNotMatchedInsertAll()`, window functions and `DESCRIBE HISTORY`,
for anyone who needs to see it in Spark.

---

## What the pipeline does

### 1 · Load into a Delta table (bronze)

The CSV is read **entirely as text** (`dtype=str`) and landed verbatim. This is the standard bronze
contract — don't let the reader silently guess types or strip leading zeros off postal codes.
`write_deltalake(...)` writes the Parquet files *and* commits
`_delta_log/00000000000000000000.json`, which is what makes it a Delta table rather than a folder of
Parquet: ACID commits, schema enforcement, versioning, time travel.

### 2 · Cleaning (silver)

One shared function cleans **both** the master snapshot and the incremental feed, which guarantees
they are normalised identically. If they weren't, the change-detection hash would report false
differences and the merge key could fail to match.

| # | Rule | Effect on the master snapshot |
|---|---|---|
| 1 | Trim whitespace, collapse spaces, standardise case | `"  CONSUMER "` and `"Consumer"` stop being two segments |
| 2 | Empty string → `NULL` | `""` is not a value |
| 3 | Drop rows with a null business key | 3 rows removed |
| 4 | Drop exact duplicate rows | 45 rows removed |
| 5 | Keep the newest row per `customer_id` | 25 rows removed |
| 6 | Cast to int / float / date / timestamp | enables arithmetic, range filters, schema enforcement |
| 7 | Impute remaining nulls with documented defaults | 123 null cells filled |

Rule 5 is not cosmetic. **`MERGE` fails outright if one source row matches the same target row more
than once** (`multiple source rows matched the same target row`), so de-duplicating the source is a
hard requirement. The incremental feed ships with 5 duplicated rows specifically to demonstrate it.

### 3 · Classify the batch before merging

Each incoming row is compared against the target with an MD5 hash over the tracked attributes:

* **NEW** — key absent → will be `INSERT`ed
* **CHANGED** — key present, hash differs → `UPDATE` (SCD1) / new version (SCD2)
* **UNCHANGED** — key present, hash identical → no-op

These three numbers become the expected values that the validation step asserts against, so the
merge metrics are checked against an independently computed expectation rather than against
themselves.

### 4 · `MERGE` — SCD Type 1

```sql
MERGE INTO gold_customer_scd1 AS t
USING incremental_batch        AS s
   ON t.customer_id = s.customer_id
WHEN MATCHED     THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

One row per customer, overwritten in place. The whole batch lands as a **single atomic Delta
transaction** — readers see either all of it or none of it.

### 5 · `MERGE` — SCD Type 2

Adds `customer_sk`, `record_hash`, `effective_start_date`, `effective_end_date`, `is_current`.

A single `MERGE` cannot both *close* an old row and *insert* its replacement, because one source row
can only act on one target row. The standard Delta pattern feeds `MERGE` a **union**:

* **Part A** — every incoming row, `merge_key = customer_id`.
  Matches the current row and closes it when the hash differs; new customers fall through to `INSERT`.
* **Part B** — the *changed* rows only, `merge_key = NULL`.
  `NULL` never equals anything, so these are always `NOT MATCHED` and are inserted as the new version.

```sql
MERGE INTO gold_customer_scd2 AS t
USING staged_source            AS s
   ON t.customer_id = s.merge_key AND t.is_current = true
WHEN MATCHED AND t.record_hash <> s.record_hash
     THEN UPDATE SET is_current = false, effective_end_date = s.effective_start_date
WHEN NOT MATCHED
     THEN INSERT *
```

The `record_hash` is what makes Type 2 behave. Without it, a feed that re-sends identical rows would
create a new version for every customer every day — here it correctly left the 11 unchanged rows alone.

### 6 · Validation

31 assertions, all run against the **persisted Delta tables read back from disk**, not against the
in-memory DataFrames:

* row counts reconcile at every stage (raw → clean → merged)
* no duplicate business keys, no duplicate rows, no null cells
* merge metrics match the independent change classification exactly
* SCD2: unique surrogate key, exactly one current row per customer, current rows have a `NULL` end
  date, expired rows have one, no gaps or overlaps in the effective-date ranges
* SCD1 and SCD2's current view agree on customer set and totals
* **time travel** — reading `versionAsOf 0` reproduces the pre-merge state exactly, and the customers
  present only in v1 are exactly the 45 inserts

### 7 · Final output

Final datasets, a business summary by region / segment / loyalty tier, a four-panel matplotlib
figure, CSV exports, and `run_summary.json` — which the report PDF is generated from, so the write-up
can never drift from what actually ran.

---

## Screenshots

All 29 images in `screenshots/` are renders of cells from the **executed** notebook — the code shown
and the output beneath it are exactly what ran. They are produced by
`scripts/capture_screenshots.py`, which reads the tagged cells straight out of the `.ipynb`, so they
regenerate automatically and can never go stale.

---

## Notes and trade-offs

* Tables are **unpartitioned** — fine at this size, but at production volume they'd want partitioning
  (by `region`, say) plus periodic `OPTIMIZE` / `Z-ORDER`.
* Surrogate keys are allocated in blocks, so the sequence has **gaps**. Harmless — a surrogate key
  only has to be unique, not gapless.
* `effective_end_date` uses `NULL` for open-ended rows rather than a `9999-12-31` sentinel, which
  avoids the pandas nanosecond timestamp range limit (max year 2262) entirely.
* A production version would enable **Change Data Feed** for downstream consumers, schedule `VACUUM`
  once the time-travel retention window passes, and quarantine bad rows into a rejects table instead
  of imputing them.
