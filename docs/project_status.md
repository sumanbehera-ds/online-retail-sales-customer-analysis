# Project status

Updated: 2026-11-12

## Completed

- Prepared raw and deduplicated CSV extracts with Python's built-in `csv` module and `openpyxl`.
- Recorded source and data-quality counts in `data_quality_report.md`.
- Loaded the files into local MySQL; the reported stored row counts match the extracts: 1,067,371 raw and 1,033,036 clean.
- Authored twelve SQL analyses and a Power BI model/measures reference.

## Remaining work

- Run all twelve SQL analyses against the loaded MySQL tables and retain the resulting CSV evidence.
- Build the two-page Power BI report, export a PDF preview, and add screenshots.
- Write findings and recommendations from the verified query outputs.
- Update the selected CV after the report and findings are complete.

## Attribution

The source workbook is the UCI Online Retail II dataset, licensed under CC BY 4.0. The workbook itself is excluded from this repository; users should download it from the UCI dataset page and retain the required attribution.
