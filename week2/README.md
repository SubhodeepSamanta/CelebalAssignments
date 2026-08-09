# Week 2 — Superstore Sales SQL Analysis & Data Insights

Exploratory data analysis and relational SQL queries on the classic **Sample Superstore dataset** containing 9,994 transactional order line records spanning from January 2014 to December 2017.

---

## Dataset Overview

- **Source**: `superstore.csv` (9,994 rows × 21 columns)
- **Timeframe**: 2014-01-03 to 2017-12-30
- **Granularity**: Each row represents an individual order line item.
- **Key Fields**: `Order_ID`, `Order_Date`, `Ship_Date`, `Ship_Mode`, `Customer_ID`, `Customer_Name`, `Segment`, `Country`, `City`, `State`, `Postal_Code`, `Region`, `Product_ID`, `Category`, `Sub_Category`, `Product_Name`, `Sales`, `Quantity`, `Discount`, `Profit`.

---

## Directory Structure

```
week2/
├── superstore.csv                  Raw transactional dataset
├── superstore_sql_analysis.ipynb   Jupyter Notebook containing SQL queries & visualizations
├── insights.md                     Key analytical findings and business summary
└── README.md                       Assignment documentation
```

---

## Key SQL Queries & Analysis Covered

1. **Category & Sub-Category Performance**:
   - Total sales, total profit, and average discount grouped by product category (`Technology`, `Furniture`, `Office Supplies`).
   - Identifying top revenue drivers vs volume drivers.

2. **Regional & Temporal Trends**:
   - Aggregating sales across `East`, `West`, `Central`, and `South` regions.
   - Monthly and yearly trend analysis using date extraction functions.

3. **Customer Concentration Analysis**:
   - Lifetime value calculation per `Customer_ID`.
   - Identifying top 10 customers and spending distribution.

4. **Discount Impact & Margin Analysis**:
   - Filtering loss-making order lines (`Profit < 0`).
   - Analyzing profit margins relative to discount tiers (e.g. 0–10%, 10–30%, >30%).

---

## Summary of Findings & Business Insights

- **Category Revenue Dynamics**: **Technology** generated the highest total sales (~$836k) despite having the lowest total order count, driven by high-ticket items like copiers and smartphones. **Office Supplies** accounted for the largest volume by far (6,026 order lines), representing low-value, high-frequency purchases.
- **Regional Performance**: The **East** and **West** regions consistently outperformed all other territories. The **Central** region exhibited the weakest sales performance across all three major categories.
- **Seasonality**: Sales show strong year-end seasonality. November and December were consistently the highest-performing months each year, with November 2017 recording the single highest monthly sales volume (~$118k).
- **Customer Revenue Concentration**: Revenue is heavily concentrated among repeat buyers. The top 10 customers contributed between $12k and $25k each in lifetime sales, significantly above the account average.
- **Discount & Profitability Warning**: **1,871 out of 9,994 order lines (~19%) were loss-making**. These unprofitable sales were heavily concentrated in orders carrying discounts exceeding **30%**, demonstrating that aggressive discounting damaged overall margins without generating sufficient volume to compensate.

---

## How to Run

1. Open Jupyter Notebook in the `week2` folder:
   ```bash
   cd week2
   jupyter notebook superstore_sql_analysis.ipynb
   ```
2. Execute cells top-to-bottom to build the in-memory SQLite database and view query outputs.
