# Online Retail Sales and Customer Analysis

An analytics project for the UCI Online Retail II transaction dataset. Python prepares auditable raw and clean extracts, PyMySQL loads them into MySQL, twelve SQL analyses produce verified CSV results, and Power BI assets provide a saved report draft plus a static dashboard preview generated from those SQL outputs.

## Project at a glance

- Prepared and validated **1,044,848 clean transaction rows**; removed 22,523 exact cross-sheet overlap copies while preserving within-sheet repeats.
- Verified gross merchandise revenue of **GBP 19.70 million**, **39,516** eligible sales invoices, and **5,852** registered customers.
- Implemented the pipeline with Python, MySQL 8.4, SQL, and Power BI assets. The interactive PBIX is currently a one-card draft; Power BI parity has not been verified.
- The [two-page dashboard preview](powerbi/retail_dashboard_preview.pdf) is a static document generated from the verified SQL CSVs, not an export from Power BI. Rebuild with `python powerbi/build_dashboard_preview.py`.
- The [pandas cross-check notebook](notebooks/01_crosscheck.ipynb) independently checks headline SQL totals and includes three exploratory charts.

## Five findings

1. The United Kingdom contributes **85.56%** of merchandise revenue (GBP 16.86 million); EIRE and the Netherlands are the next largest markets. ([country results](docs/query_results/05_country_revenue.csv))
2. The top spending decile of registered customers contributes **63.81%** of registered-customer revenue. ([customer ranking](docs/query_results/09_top_customers_and_decile.csv))
3. Revenue is concentrated in September through November: **36.2%** of full-year 2010 revenue and **40.5%** of January-November 2011 revenue fell in those three months. ([monthly results](docs/query_results/02_monthly_revenue_mom.csv))
4. **15.46%** of invoices are cancellation invoices, while cancelled merchandise value is **3.65%** of gross merchandise revenue. Cancellation timing uses the recorded cancellation date. ([KPI and cancellation results](docs/query_results/01_core_kpis.csv), [monthly value share](docs/query_results/07_cancelled_value_share.csv))
5. **72.35%** of identified customers placed at least two orders in the observation window. The Hibernating and At Risk segments contain 2,070 customers; these are descriptive, rule-based groups, not predictions. ([repeat rate](docs/query_results/08_repeat_customer_rate.csv), [RFM results](docs/query_results/10_rfm_segments.csv))

## Three recommendations

1. Track recency for Champions and At Risk customers, then test retention actions before scaling them.
2. Use the observed autumn revenue concentration to inform inventory and staffing reviews; treat it as historical seasonality, not a forecast.
3. Record cancellation reasons.

Detailed definitions, supporting results, and limitations are in [the analysis findings](docs/analysis_findings.md). The eight SQL reference values and current Power BI verification status are recorded in [the parity check](docs/parity_check.md).

## Data source and attribution

The source is [Online Retail II from the UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii), created by Daqing Chen. UCI identifies the unit price as sterling and licenses the dataset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [DATA_LICENSE.md](DATA_LICENSE.md) for attribution and scope. Do not commit the downloaded workbook; it is excluded from Git.

Download `online_retail_II.xlsx` from UCI and save it as `data/raw/online_retail_II.xlsx`.

The tracked sample at [`data/sample/online_retail_sample_invoices.csv`](data/sample/online_retail_sample_invoices.csv) contains a deterministic, month-stratified selection of five whole invoices per observed month (seed 42). It retains all clean transaction lines for each selected invoice, so row count varies and it covers more than the beginning of the workbook.

## Current status

- Python profiling and CSV generation are implemented.
- Exact record overlap between the two worksheets is removed from the later sheet; exact repeated lines within a worksheet are retained.
- MySQL staging load, count/revenue checks and explicit `--replace` workflow are implemented.
- Twelve SQL analyses and a DAX model/measures reference are present.
- Twelve MySQL analyses have been executed; their CSV evidence and verified findings are included under `docs/`.
- `powerbi/online-retail-sales-customer-analysis.pbix` is a saved Power BI draft. It currently contains one report page with a Gross Revenue card; the full interactive two-page report and SQL/DAX parity check remain to be completed in Power BI Desktop.
- `powerbi/retail_dashboard_preview.pdf` is a two-page static preview generated from the verified SQL result CSVs. Rebuild it with `python powerbi/build_dashboard_preview.py`.
- `notebooks/01_crosscheck.ipynb` reproduces the query 01 headline KPIs and query 08 repeat-customer count/rate from the clean CSV.

See [docs/project_status.md](docs/project_status.md) and [docs/data_quality_report.md](docs/data_quality_report.md) for the latest verified counts and remaining work.

## Setup

Python 3.12 is the project environment used for development. MySQL 8.4 and Power BI Desktop are separate applications; Power BI Desktop is needed only for the manual report stage.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### macOS / Linux shell

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the pipeline

Run commands from the repository root.

### 1. Prepare the data

```text
python python/prepare_data.py
```

The script streams both worksheets with openpyxl. It writes `data/processed/online_retail_raw.csv`, `data/processed/online_retail_clean.csv`, `docs/data_quality_report.md`, and `docs/data_quality_report.json`. The clean table includes `source_sheet`, cancellation/guest/non-product flags, and `line_revenue`. Raw and processed CSVs are local and ignored by Git. The generated invoice sample is kept under `data/sample/`.

### 2. Validate prepared files

```text
python python/validate_data.py
```

This compares raw/clean CSV row counts and revenue sums with the generated JSON quality summary, reconciles clean row counts by worksheet, and checks that the sample includes complete invoices across all observed months.

### 3. Load MySQL

Start MySQL 8.4, then run:

```text
python python/load_mysql.py
```

The script prompts for the database user, hidden password, host and port. It reads canonical table definitions from [`sql/00_schema.sql`](sql/00_schema.sql), creates staging tables without secondary indexes, loads 5,000-row batches, compares counts to the quality summary, and verifies raw/clean revenue sums against MySQL. It creates the secondary indexes after bulk insertion and publishes the tables with a rename only after checks pass.

The default behavior refuses to overwrite final tables. To replace them after reviewing the existing data:

```text
python python/load_mysql.py --replace
```

Replacement keeps the existing final tables until the new staged tables pass checks, then atomically renames the old tables to temporary backup names and publishes the new ones.

### 4. Validate published tables (optional)

```text
python python/validate_data.py --mysql
```

This compares both published table counts and revenue sums with the generated quality summary. Credentials are prompted locally and are never written into the repository.

### 5. Run the SQL analyses

```text
python python/run_queries.py
```

The runner executes numbered analysis files `01` through `12` in order, writes CSV outputs to `docs/query_results/` for review and version control, and replaces each SQL file's `-- Result:` comment with the row count and first three output rows. Query 09 reports ranked customer revenue and order counts without exporting customer IDs. Review `git diff sql/` before committing after query runs. `sql/00_schema.sql` is excluded from the analysis runner.

## Analysis questions

1. Core revenue, orders, registered customers, average order value and cancellation rate.
2. Monthly revenue and month-over-month growth.
3. Year-over-year revenue by calendar month.
4. Top products by revenue and quantity, using the most frequent trimmed description.
5. Country revenue and UK share.
6. Monthly cancellation invoice rate.
7. Cancelled value as a share of positive merchandise sales.
8. Registered repeat customer rate.
9. Top customers and top-decile revenue share.
10. RFM scores and heuristic segments.
11. Registered-customer cohort retention.
12. Orders by weekday and hour.

All twelve SQL queries have been executed against the verified tables. Review [`docs/analysis_findings.md`](docs/analysis_findings.md) for results and limitations, and `docs/query_results/` for the full CSV outputs.

## Data handling rules

- Keep every nonblank source row in the raw extract and record its worksheet in `source_sheet`.
- Remove only cross-worksheet exact overlap copies, up to the repeated-row count in the earlier worksheet. Retain same-worksheet identical lines because they may be real repeated scans.
- Trim leading/trailing whitespace from clean product descriptions; raw descriptions remain unchanged.
- Preserve cancellations, guest rows, non-positive quantities/prices and non-product lines. Flag them for analysis instead of silently deleting them.
- Use the observed fee/service/test/voucher codes in `python/prepare_data.py`; review the data-quality audit before adding new exclusions. A numeric-only stock-code rule is unsafe because valid product codes include letter suffixes.
- Keep guest sales in transaction revenue metrics but exclude missing customer IDs from registered-customer metrics. The quality report records 22.77% guest rows in the observed workbook.
- Cancellation activity is dated by the cancellation transaction date; this source does not link reversals back to their original sale date.
- The first observed purchase month is not necessarily a customer's true acquisition month. The sample spans a two-year observation window, so repeat and retention metrics are window-dependent.
- UCI labels unit price as sterling; this project reports monetary values in GBP.
- Exclude the incomplete December 2011 from full-month revenue trends; queries that include it mark it as partial.

## Repository layout

- `data/`: local source/processed extracts (ignored) and tracked sample data.
- `python/`: preparation, MySQL loading, SQL execution and validation scripts.
- `sql/`: canonical schema and twelve analysis queries.
- `powerbi/`: Power BI report draft, DAX reference, static dashboard PDF and its reproducible generator.
- `notebooks/`: pandas SQL cross-check notebook with saved outputs.
- `docs/`: methodology, quality report, machine-readable summary, stock-code audit, query results, status and licensing notes.
- `tests/`: standard-library unit tests for transformation and dedupe rules.

## Validation

Run helper tests with:

```text
python -m unittest discover -s tests -v
```

The tests cover data helper rules on small examples. Full-workbook and MySQL checks are performed by the preparation/validation scripts; there is no CI pipeline configured.
