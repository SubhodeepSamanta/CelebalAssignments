# Week 5 - Spark DataFrames

Data cleaning, transformation and aggregation with PySpark on the Superstore sales dataset (9,994 orders, 21 columns).

## Files

```
Assignment5/
├── data/
│   └── Sample - Superstore.csv     dataset
├── output/
│   └── state_revenue.csv           final pipeline result
├── superstore_pipeline.py          full cleaning + aggregation pipeline as a script
├── week5_spark_dataframes.ipynb    answers to Q1-Q15 with outputs
└── README.md
```

## Running it

Needs Java and `pyspark` installed (`pip install pyspark`).

```
python superstore_pipeline.py
```

or open the notebook and run all cells. The first cell sets `PYSPARK_PYTHON` because on Windows the executors don't always pick the right interpreter inside Jupyter.

## Questions & Answers

### Q1. What are the key limitations of MapReduce that make Spark preferred?

MapReduce writes intermediate results to disk after every map and reduce phase, so multi-stage jobs keep hitting HDFS over and over. On top of that: every problem has to be forced into a map + reduce shape, it's batch only with high latency, iterative algorithms reread the same input from disk on every pass, and the API is verbose enough that you need extra tools like Hive or Pig. Spark keeps data in memory between stages, builds a DAG of operations instead of rigid map/reduce pairs, and gives one engine for SQL, streaming and ML - typically 10-100x faster.

### Q2. How does in-memory computing speed up iterative ML?

Algorithms like gradient descent or k-means pass over the same training data many times. On MapReduce each iteration is a fresh job: read HDFS, compute, write HDFS - disk I/O dominates. In Spark you load the data once, `.cache()` it, and every pass after the first reads from RAM. Fault tolerance still works because Spark tracks lineage and can recompute a lost partition instead of depending on disk copies.

### Q3. Remove duplicates based on user_id and transaction_date

```python
df.dropDuplicates(["user_id", "transaction_date"])
```

On Superstore the equivalent (one row per customer per order date) cut 9,994 rows down to 4,992.

### Q4. Filter region 'West', group by category, average sale amount

```python
df_sales.filter(F.col("region") == "West") \
    .groupBy("product_category") \
    .agg(F.avg("sale_amount"))
```

Result on Superstore: Technology 420.69, Furniture 357.30, Office Supplies 116.42.

### Q5. .na.drop() vs .na.fill()

`.na.drop()` removes rows containing nulls, `.na.fill()` keeps them and substitutes a value. Drop when the row is useless without the value, fill when a default makes sense.

```python
df.na.fill({"status": "Unknown"})
```

### Q6. Count per city, only where count > 100

```python
df.groupBy("city").count().filter(F.col("count") > 100)
```

13 cities qualify - New York City (915), Los Angeles (747) and Philadelphia (537) on top.

### Q7. How does immutability affect cleaning steps?

DataFrames can't be changed in place. Dropping or renaming a column returns a new DataFrame, so you always reassign: `df = df.drop("junk").withColumnRenamed("old", "new")`. Cleaning becomes a chain of transformations, each producing a new frame, and nothing runs until an action triggers it. The original frame stays intact, which is handy when a cleaning step goes wrong.

### Q8. Age between 18-30 and subscription 'Premium'

```python
df.filter((F.col("age").between(18, 30)) & (F.col("subscription") == "Premium"))
```

Same pattern on our data (Discount 0.1-0.3, Segment Corporate) matches 1,228 rows.

### Q9. Why handle nulls before aggregating?

`sum()` and `avg()` silently skip nulls. `avg` divides by the count of non-null values, not total rows, so a column with many nulls gives a misleading average, and different aggregations can end up computed over different row counts. Handling nulls first means you know exactly what the numbers are based on. (Superstore turned out to have zero nulls in every column.)

### Q10. Cast raw_timestamp to timestamp, rename to event_time

```python
df.withColumn("raw_timestamp", F.col("raw_timestamp").cast("timestamp")) \
  .withColumnRenamed("raw_timestamp", "event_time")
```

Our dates are strings like `11/8/2016`, so they need the format spelled out: `F.to_timestamp("Order Date", "M/d/yyyy")`, then `withColumnRenamed`.

### Q11. The shuffle, and why groupBy is a wide transformation

groupBy needs all rows with the same key on the same executor. Since matching keys are spread across partitions, each task writes its rows into buckets by key, the buckets move over the network, and the next stage reads its bucket from every task - that exchange is the shuffle. It's "wide" because one output partition depends on many input partitions (a filter, by contrast, is narrow: one input partition, one output partition). Wide transformations force a stage boundary and cost disk + network, which makes them the expensive part of a job.

### Q12. Remove rows where email is null OR username is empty

Removing those means keeping rows where email exists AND username is non-empty:

```python
df.filter(F.col("email").isNotNull() & (F.col("username") != ""))
```

### Q13. Multiple statistics at once with .agg()

```python
df.agg(
    F.min("price").alias("min_price"),
    F.max("price").alias("max_price"),
    F.mean("price").alias("mean_price"),
)
```

On Sales: min 0.44, max 22,638.48, mean 229.86.

### Q14. Risk of inferSchema=true with messy data

inferSchema samples the data and picks whatever type fits; inconsistent date formats make the column fall back to string, or values that don't parse turn into nulls with no warning. This dataset actually demonstrated it - some product names contain quote characters, and on a default read the parser broke those rows, so Sales got inferred as *string*. Adding `escape='"'` fixed the parse and Sales came back as double. For messy sources it's safer to read dates as strings and convert explicitly, or define the schema yourself.

### Q15. Final pipeline: dedupe, fill null prices with 0, revenue by store

```python
(df.dropDuplicates()
   .na.fill({"price": 0})
   .groupBy("store_id")
   .agg(F.sum("price").alias("total_revenue")))
```

On Superstore (dedupe on Order ID + Product ID, fill Sales, group by State): California leads at 457,687.63, then New York 310,827.15 and Texas 170,188.05. Full table in `output/state_revenue.csv`.

## Main takeaways

- California (~$458k) and New York (~$311k) lead revenue by a big margin, total revenue is about $2.29M
- Technology has the highest average order value in the West (~$421), Office Supplies the lowest (~$116)
- New York City, Los Angeles and Philadelphia are the busiest cities by order count
- the dataset has no nulls at all, the only real cleaning problem was the CSV parsing, which is a schema issue rather than a data value issue
