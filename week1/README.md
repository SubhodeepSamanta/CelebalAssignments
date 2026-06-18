# Shopping Dataset — EDA & Data Cleaning

Exploratory data analysis and cleaning on a Myntra e-commerce product dataset containing 1000 products across 96 categories.

## Dataset
Source: [Kaggle — anvitkumar/shopping-dataset](https://www.kaggle.com/datasets/anvitkumar/shopping-dataset)  
File used: `Combined_dataset.csv` (1000 rows × 24 columns)

## What this project covers
- Data loading and shape exploration
- Type inspection, null analysis, and `.describe()` statistics
- Price column cleaning (stripping ₹ symbols and string formatting)
- Handling missing values (discount, seller_name, metadata columns)
- Duplicate removal and filtering unrated products
- Feature engineering: `price_difference`, `popularity_metric`, `total_amount`
- Univariate, bivariate, and category-level analysis
- Visualizations: histograms, scatter plots, bar charts, boxplots
- Business insights from the data

## Folder Structure
```
shopping-analysis/
├── data/
│   ├── Combined_dataset.csv
│   └── Combined_dataset_cleaned.csv
├── notebook/
│   └── analysis.ipynb
└── README.md
```

## How to run
```bash
pip install pandas numpy matplotlib seaborn notebook
cd notebook
jupyter notebook analysis.ipynb
```
