from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("week5-superstore").master("local[*]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.csv("data/Sample - Superstore.csv", header=True, inferSchema=True, escape='"')

print("rows:", df.count(), "| columns:", len(df.columns))
df.printSchema()

deduped = df.dropDuplicates(["Order ID", "Product ID"])
print("after dedup on Order ID + Product ID:", deduped.count())

null_counts = deduped.select(
    [F.count(F.when(F.col(c).isNull(), 1)).alias(c) for c in deduped.columns]
)
null_counts.show(vertical=True, truncate=False)

cleaned = deduped.na.fill({"Sales": 0, "Profit": 0})
cleaned = cleaned.filter(F.col("Order ID").isNotNull() & (F.trim(F.col("Region")) != ""))

cleaned = (
    cleaned
    .withColumn("Order Date", F.to_timestamp("Order Date", "M/d/yyyy"))
    .withColumnRenamed("Order Date", "order_ts")
    .withColumn("Ship Date", F.to_timestamp("Ship Date", "M/d/yyyy"))
)
cleaned.select("order_ts", "Ship Date").show(3)

print("West region, avg sales per category")
west_avg = (
    cleaned.filter(F.col("Region") == "West")
    .groupBy("Category")
    .agg(F.round(F.avg("Sales"), 2).alias("avg_sales"))
    .orderBy(F.desc("avg_sales"))
)
west_avg.show()

print("corporate orders with 10-30% discount")
corp = cleaned.filter((F.col("Discount").between(0.1, 0.3)) & (F.col("Segment") == "Corporate"))
print("matching rows:", corp.count())
corp.select("Customer Name", "Category", "Sales", "Discount").show(5)

print("overall sales stats")
cleaned.agg(
    F.count("Sales").alias("orders"),
    F.round(F.sum("Sales"), 2).alias("total"),
    F.round(F.avg("Sales"), 2).alias("mean"),
    F.round(F.min("Sales"), 2).alias("lowest"),
    F.round(F.max("Sales"), 2).alias("highest"),
).show()

print("cities with more than 100 orders")
busy_cities = cleaned.groupBy("City").count().filter(F.col("count") > 100).orderBy(F.desc("count"))
busy_cities.show()

print("revenue by state")
revenue = (
    df.dropDuplicates(["Order ID", "Product ID"])
    .na.fill({"Sales": 0})
    .groupBy("State")
    .agg(F.round(F.sum("Sales"), 2).alias("total_revenue"))
    .orderBy(F.desc("total_revenue"))
)
revenue.show(15)

revenue.toPandas().to_csv("output/state_revenue.csv", index=False)
print("saved to output/state_revenue.csv")

spark.stop()
