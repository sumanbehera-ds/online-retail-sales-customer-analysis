# Project status

Updated: 2026-11-16

## Completed

- Prepared raw and clean CSV extracts with Python's built-in `csv` module and `openpyxl`.
- Removed 22,523 exact cross-sheet overlap copies while preserving 12,133 exact within-sheet repeats.
- Validated the generated files: 1,067,371 raw rows, 1,044,848 clean rows, and 1,731 sample rows across 125 complete invoices.
- Reconciled CSV revenue totals: GBP 19,287,250.568 raw and GBP 18,909,762.118 clean.
- Added a stock-code review audit, deterministic month-stratified invoice sample, data-quality JSON summary, and standard-library unit tests.
- Authored twelve SQL analyses, canonical MySQL schema, and a DAX model/measures reference.

## Remaining work

- Loaded and published MySQL tables with verified counts: 1,067,371 raw rows and 1,044,848 clean rows; raw and clean revenue sums match the CSV extracts.
- Executed all twelve SQL analyses and retained CSV outputs under `docs/query_results/`.
- Reconciled headline revenue across the KPI, monthly, and country queries; RFM segment counts also reconcile to registered-customer totals.
- Documented findings and interpretation limits in `docs/analysis_findings.md`.
- Build and validate the Power BI report after Power BI Desktop is available; no `.pbix`, PDF preview, or screenshots are currently present.
- Reconcile selected SQL and DAX metrics in Power BI before treating the DAX reference as validated.

## Attribution

The source workbook is the UCI Online Retail II dataset, licensed under CC BY 4.0. The workbook itself is excluded from this repository; users should download it from the UCI dataset page and retain the required attribution. The stock-code audit is a review aid: a nonstandard code shape is not enough to classify a row as non-product.
