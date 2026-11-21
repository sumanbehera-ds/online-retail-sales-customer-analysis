# Project status

Updated: 2026-11-21

## Completed

- Prepared auditable raw and clean CSV extracts with Python's built-in `csv` module and `openpyxl`.
- Removed 22,523 exact cross-sheet overlap copies while preserving 12,133 exact within-sheet repeats.
- Validated 1,067,371 raw rows, 1,044,848 clean rows, and 1,731 sample rows across 125 complete invoices.
- Reconciled CSV revenue totals: GBP 19,287,250.568 raw and GBP 18,909,762.118 clean.
- Loaded and published MySQL tables with verified counts and revenue totals.
- Executed all twelve SQL analyses; their CSV outputs are retained under `docs/query_results/`.
- Reconciled headline revenue across the KPI, monthly, and country queries; RFM segment counts reconcile to registered-customer totals.
- Documented query findings and interpretation limits in `docs/analysis_findings.md`.
- Reproduced ten SQL headline values from the clean CSV in `notebooks/01_crosscheck.ipynb`; the notebook contains three saved charts and no customer-level output.
- Added `docs/parity_check.md` with SQL reference values and explicit pending statuses for Power BI values.
- Reorganized the README around the project outcomes, five findings, and three recommendations.
- Created and pushed the `finish-dashboard` branch with the notebook and documentation updates; it remains separate from `main` until the Power BI report work is complete.
- Updated the GitHub repository description and topics to match the current implementation.
- Saved a Power BI Desktop draft at `powerbi/online-retail-sales-customer-analysis.pbix`. The current PBIX contains one report page with a Gross Revenue card.
- Created a two-page static dashboard preview from verified SQL CSVs at `powerbi/retail_dashboard_preview.pdf`; rebuild it with `python powerbi/build_dashboard_preview.py`.

## Remaining work

- Power BI Desktop was not controllable in the latest session. In Desktop, expand the draft with executive trend/product/country visuals, a customer RFM/cohort page, and useful date filters; then export the completed report.
- Compare selected DAX measures against the verified SQL outputs before describing them as reconciled.
- The static PDF presents SQL outputs; it is not an export of the PBIX and does not support interactive filtering.
- Add page screenshots and a genuine Power BI PDF export after the interactive report is finished.
- Pin the repository to the GitHub profile and review it in a private browser window after the report is complete; browser control was unavailable in this session.

## Attribution

The source workbook is the UCI Online Retail II dataset, licensed under CC BY 4.0. The workbook itself is excluded from this repository; users should download it from the UCI dataset page and retain the required attribution. The stock-code audit is a review aid: a nonstandard code shape is not enough to classify a row as non-product.
