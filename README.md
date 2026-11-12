# Online Retail Sales and Customer Analysis

This portfolio project analyzes the UCI Online Retail II dataset with Python, MySQL, and Power BI. It is being built as an original, reproducible analysis: cleaning decisions, SQL queries, DAX measures, findings, and recommendations will be documented from work performed on the dataset. The Python data phase uses openpyxl and Python's built-in CSV module.

## Project status

Python profiling and CSV preparation are complete. The local MySQL load was reported with matching row counts: 1,067,371 raw rows and 1,033,036 deduplicated rows. Query execution, the Power BI report, and evidence based business findings remain in progress.

## Data source

Online Retail II, UCI Machine Learning Repository: https://archive.ics.uci.edu/dataset/502/online+retail+ii

Dataset license: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit the UCI Machine Learning Repository when redistributing dataset-derived material. The raw workbook is kept out of Git; follow the UCI link to obtain it.

A 1,000-row clean sample is included at [`data/sample/online_retail_sample_1000.csv`](data/sample/online_retail_sample_1000.csv).

## Planned workflow

- Validate and clean the workbook in Python.
- Load raw and clean tables into MySQL.
- Analyze sales, customers, cancellations, RFM segments, and cohorts with SQL.
- Build a two-page Power BI report and export a PDF preview.
- Add findings and recommendations only after checking the actual query results.

## SQL questions

1. Core sales and customer KPIs
2. Monthly revenue and month-over-month growth
3. Year-over-year revenue by calendar month
4. Top products by revenue and quantity
5. Revenue by country and UK share
6. Monthly cancellation rate
7. Canceled value as a share of gross merchandise revenue
8. Repeat customer rate
9. Top customers and top-decile revenue share
10. RFM scores and customer segments
11. Cohort retention
12. Orders by weekday and hour

## Data cleaning decisions

- Keep rows with a missing customer ID in transaction-level sales analysis; exclude them only from registered-customer metrics.
- Flag cancellation invoices instead of deleting them, so cancellation counts and value can be analyzed.
- Count and remove exact duplicate source rows from the clean table; retain the complete original workbook rows in the raw CSV.
- Flag observed postage, carriage, fee, discount, manual adjustment, sample, and bad-debt codes. Keep those rows for reconciliation and filter them from merchandise-only queries.
- Keep non-positive quantities and prices, then report and inspect them instead of silently dropping them.
- Exclude the partial December 2011 from month-over-month and year-over-year trend comparisons.

## Prepare the data

From the repository root on Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python python\prepare_data.py
```

The preparation script reads `data/raw/online_retail_II.xlsx` and writes the raw CSV, clean CSV, and data quality report. Raw and processed data stay out of Git; the small sample CSV remains tracked. Install dependencies with openpyxl and PyMySQL; this project does not require pandas or SQLAlchemy.

After MySQL 8.4 is running, load both tables with:

```powershell
python python\load_mysql.py
```

The loader prompts for the local MySQL username and password; the password input is hidden and is not written to the repository. It loads through staging tables and publishes the final tables only after the inserted row counts match.

Run and export all numbered analysis queries with:

```powershell
python python\run_queries.py
```

The runner saves CSV result files under the ignored `data/query_results/` folder and writes a small result preview into each SQL file's result comment.

## Repository layout

- `data/`: local raw and processed data; excluded from Git.
- `python/`: data validation, cleaning, and loading scripts.
- `sql/`: numbered MySQL analysis queries.
- `powerbi/`: DAX model and measures, plus the Power BI report when built.
- `docs/`: data quality report and project notes.
- `images/`: dashboard previews.

## Tools

Python, openpyxl, the built-in CSV module, PyMySQL, MySQL 8.4 LTS, and Power BI Desktop.
