# Week 6 - Spark Assignment

This repository contains the solution for **Week 6: Spark Architecture & Data Processing Assignment**. It covers core distributed computing architecture, PySpark DataFrame operations, lazy evaluation mechanics, fault tolerance via DAG lineage, columnar vs row-based file format performance, and schema handling.

---

## Directory Structure

```
week6/
├── data/
│   ├── Sample - Superstore.csv      # Primary Superstore dataset
│   ├── source.csv                   # Synthetic transactional CSV dataset
│   └── input_parquet/
│       └── data.parquet             # Partitioned Parquet source file
├── output/
│   ├── electronics_products.csv     # Results for Q5 (Electronics category filter)
│   ├── filtered_users.csv           # Results for Q12 (Non-null user_id filter)
│   ├── high_value_orders.csv        # Results for Q8 (Completed orders > $1000)
│   ├── region_priority_orders.csv   # Results for Q14 (North region OR High priority)
│   ├── revised_dataset.csv          # Results for Q6 (Renamed column + cast price)
│   ├── superstore_category_summary.csv # Aggregated metrics on Superstore data
│   └── taxed_products.csv           # Results for Q10 (18% tax calculation)
├── Spark_Assignment.ipynb           # Complete Jupyter Notebook with code & outputs
└── README.md                        # Documentation and written answers
```

---

## Questions & Detailed Answers

### Q1: Explain the roles of the Driver, Cluster Manager, and Executor in a Spark application.

A Spark application relies on three distinct process layers to manage compute workload and physical hardware resources:

1. **Driver Process**:
   The central master node process that executes the main function of the application and initializes the `SparkSession`. It converts user transformation code into a Directed Acyclic Graph (DAG), splits the graph into execution stages and tasks, schedules these tasks across worker nodes, and tracks application completion metrics.

2. **Cluster Manager**:
   An external infrastructure service (such as YARN, Kubernetes, Mesos, or Spark's Standalone manager) responsible for physical resource allocation across the cluster. It provisions hardware containers (CPU cores and RAM) requested by the Driver and monitors worker node connectivity.

3. **Executor**:
   Worker processes spawned on cluster nodes that execute assigned tasks concurrently across data partitions. Executors store cached data blocks in memory or on disk and send execution status updates and results back to the Driver. They remain active for the lifespan of the application.

---

### Q2: How does Spark's Lazy Evaluation strategy improve performance when chain-processing large datasets?

**Lazy Evaluation** means Spark defers executing DataFrame transformations (`.filter()`, `.select()`, `.withColumn()`, `.groupBy()`) when they are declared in code. Instead of running immediately, transformations build a logical Directed Acyclic Graph (DAG) execution plan.

Computation only occurs when an **Action** (such as `.show()`, `.count()`, `.collect()`, or `.write()`) is triggered.

#### Key Performance Advantages:
- **Catalyst Optimizer Query Planning**: Spark analyzes the entire pipeline before executing a single byte. It reorders operations, collapses adjacent transformations, and removes unneeded columns (projection pruning).
- **Predicate Pushdown**: Filter criteria are pushed directly down to file format readers (e.g., Parquet), allowing Spark to skip reading non-matching disk blocks into memory.
- **Pipelined Execution**: Transformations execute in a single streaming pass through worker RAM without generating temporary intermediate files on disk between steps.

---

### Q3: Write a Spark command to read a CSV file located at `"data/source.csv"`, ensuring the first row is treated as a header and `inferSchema` is enabled.

```python
df = (
    spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .load("data/source.csv")
)
```

---

### Q4: What is the difference between CSV and Parquet in terms of storage (row-based vs. columnar) and why does it matter for performance?

#### Comparison Overview

| Feature | CSV (Row-Based) | Parquet (Columnar) |
|---|---|---|
| **Storage Structure** | Stores records row-by-row as plain text lines | Groups data into row groups and stores values column-by-column |
| **Compression** | Poor (mixed data types per line limit compression) | Excellent (homogeneous column data enables RLE & Snappy compression) |
| **Metadata** | None (requires full scan to inspect schema/min-max) | Built-in footer metadata (stores schema, block ranges, min/max metrics) |

#### Why It Matters for Performance:
1. **Column Pruning**: If a query requests 2 columns from a 50-column dataset, Parquet reads only the specific byte offsets for those 2 columns from disk, skipping 96% of disk I/O. CSV forces the engine to read every character on every line.
2. **Predicate Pushdown**: Parquet file footers maintain min/max value bounds for every row group. If a query filters for `amount > 1000`, Spark skips reading entire row groups whose `max(amount)` is under 1000.

---

### Q5: Given a DataFrame `df`, write a query to select the columns `product_id` and `price` where the `category` is `'Electronics'`.

```python
df_electronics = df.filter(F.col("category") == "Electronics").select(
    "product_id", "price"
)
```

---

### Q6: Write the code to "revise" a DataFrame by renaming the column `old_name` to `new_name` and casting the `price` column from a String to a Double.

```python
df_revised = df.withColumnRenamed("old_name", "new_name").withColumn(
    "price", F.col("price").cast("double")
)
```

---

### Q7: How does Spark use the Lineage Graph (DAG) to provide fault tolerance if a worker node fails?

Spark DataFrames and RDDs are **immutable**. Rather than writing costly disk snapshots or replicating data across nodes after every operation, Spark records every transformation in a Directed Acyclic Graph (DAG) known as the **Lineage Graph**.

When a worker node crashes and an in-memory partition is lost:
1. The Driver identifies the exact partition that went missing.
2. It consults the Lineage Graph to trace the exact chain of transformations required to rebuild that partition.
3. The Driver schedules recomputation of *only* the missing partition on an active worker node, starting from the original source file or nearest cached checkpoint.

---

### Q8: Write a query to filter a DataFrame `df_orders` for rows where the `status` is `'Completed'` AND the `amount` is greater than 1000.

```python
df_filtered = df_orders.filter(
    (F.col("status") == "Completed") & (F.col("amount") > 1000)
)
```

---

### Q9: Explain the concept of Predicate Pushdown in Parquet and how it affects the amount of data loaded into memory.

**Predicate Pushdown** is an optimization technique where filtering conditions (`WHERE` / `.filter()`) are pushed down to the physical file reader level before data is loaded into Spark Executor RAM.

Parquet files divide data into **Row Groups** (typically 128MB chunks) and store metadata footers containing minimum and maximum values for each column in that group.

When executing `.filter(F.col("amount") > 1000)`:
1. Spark reads the Parquet file footer before fetching data blocks.
2. If a Row Group's footer indicates `max(amount) = 850`, Spark bypasses reading that entire 128MB chunk from disk.
3. Disk read throughput is drastically reduced and Executor memory is preserved exclusively for matching records.

---

### Q10: Write a code snippet to add a new column `final_price` which is the `base_price` multiplied by 1.18 (18% tax).

```python
df_taxed = df.withColumn("final_price", F.round(F.col("base_price") * 1.18, 2))
```

---

### Q11: What is the difference between Transformations and Actions? Provide two examples of each.

- **Transformations**: Operations that define a new DataFrame from an existing one without modifying data. They are **lazy** and only append steps to the DAG execution plan.
  - *Examples*: `.filter()`, `.select()`, `.withColumn()`, `.groupBy()`
- **Actions**: Operations that evaluate the DAG, execute tasks across worker nodes, and return concrete output to the Driver or write data to disk.
  - *Examples*: `.show()`, `.collect()`, `.count()`, `.write.csv()`

---

### Q12: Write the Spark command to load a Parquet file from `"path/to/input"`, filter out any rows where `user_id` is null, and save the result as a CSV at `"path/to/output"`.

```python
(
    spark.read.parquet("path/to/input")
    .filter(F.col("user_id").isNotNull())
    .write.mode("overwrite")
    .option("header", "true")
    .csv("path/to/output")
)
```

---

### Q13: In Spark Architecture, what is the difference between Client Mode and Cluster Mode?

- **Client Mode**:
  - The **Driver process** runs directly on the submitting host machine (e.g., local computer, Jupyter gateway node).
  - Executor processes run on cluster worker nodes.
  - **Use Case**: Interactive querying, quick prototyping, and local debugging where log outputs must be displayed immediately on the client console.
- **Cluster Mode**:
  - The client machine submits the job request to the Cluster Manager and can immediately disconnect.
  - The Cluster Manager selects a worker node inside the cluster and launches the **Driver process** inside an Application Master container.
  - **Use Case**: Production scheduled batch jobs (e.g., via Airflow or cron) where execution stability must not depend on local machine network connectivity.

---

### Q14: Write a query to filter a dataset for rows where the `region` is `'North'` OR the `priority` is `'High'`.

```python
df_filtered = df.filter(
    (F.col("region") == "North") | (F.col("priority") == "High")
)
```

---

### Q15: When exploring a dataset, why is it safer to use `.show(5)` instead of `.collect()` on a multi-terabyte dataset?

- **`.collect()`**: Transports **every single row** across all distributed partitions from worker nodes across the network into a single Python list in Driver RAM. On multi-terabyte datasets, this immediately causes an `OutOfMemoryError` (OOM crash) on the Driver node.
- **`.show(5)`**: Reads only the first 5 records from the first active partition and displays them as an formatted ASCII table. It requires minimal network transfer and memory overhead.

---

## Running the Code

### Prerequisites
Ensure Python and PySpark are installed:
```bash
pip install pyspark pandas pyarrow jupyter
```

### Running the Notebook
Open Jupyter Notebook from inside the `week6` directory:
```bash
cd week6
jupyter notebook Spark_Assignment.ipynb
```
Run cells from top to bottom. The first cell automatically handles Python executable path configuration for PySpark workers.

---

## Output Summary

All generated CSV output files reside in the `output/` directory:
- `electronics_products.csv`: Products filtered by category = Electronics.
- `filtered_users.csv`: Parquet data filtered for non-null `user_id`.
- `high_value_orders.csv`: Completed orders with value > $1000.
- `region_priority_orders.csv`: Orders from North region OR marked High priority.
- `revised_dataset.csv`: Dataset with renamed column and double-casted price.
- `taxed_products.csv`: Dataset containing computed 18% tax `final_price`.
- `superstore_category_summary.csv`: Revenue metrics per category on Superstore dataset.
