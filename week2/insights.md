# Superstore SQL Analysis - Insights

Dataset: Sample Superstore, 9994 order line records, Jan 2014 to Dec 2017.

- Technology has the highest total sales (~836k) of the three categories despite having the fewest orders, since it includes high ticket items like copiers and phones. Office Supplies has the most orders by far (6026) and the most units sold, mostly low value, high frequency purchases.
- East and West are the strongest regions overall, Central is consistently the weakest across all three categories.
- Sales peak heavily toward year end - November and December are the strongest months in almost every year, and November 2017 is the single best month in the dataset (~118k in sales).
- Spend is concentrated in a small group of repeat customers. The top 10 customers each bring in 12k-25k in lifetime sales, well above the average.
- Copiers and Phones are disproportionately profitable sub-categories given their volume, while several other sub-categories sell a lot but contribute far less profit.
- 1871 out of 9994 orders (about 19%) are loss making. These are concentrated in orders with discount rates above 30%, suggesting the discounting strategy on certain products is cutting directly into margin rather than driving profitable volume.
- Data quality is solid - no missing values in any key column, and no exact duplicate order/product/amount rows. A handful of Order_ID + Product_ID pairs repeat, but with different quantities or discounts, so they look like separate legitimate line items rather than duplicate entries.
