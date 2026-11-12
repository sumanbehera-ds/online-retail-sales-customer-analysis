# Data quality report

Generated from the downloaded UCI workbook by `python/prepare_data.py`. The workbook is streamed one row at a time with openpyxl; CSV files are written with Python's built-in `csv` module.

## Source and row counts

- Workbook: `online_retail_II.xlsx`
- Worksheets: Year 2009-2010, Year 2010-2011
- Rows in `Year 2009-2010`: 525,461
- Rows in `Year 2010-2011`: 541,910
- Source rows: 1,067,371
- Exact duplicate rows removed from the clean output: 34,335
- Rows in clean output: 1,033,036

## Missing values and data checks

| Column | Missing rows |
| --- | ---: |
| `Customer ID` | 243,007 |
| `Description` | 4,382 |

- Date range: 2009-12-01 to 2011-12-09
- Cancellation rows (invoice starts with `C`, case-insensitive): 19,494
- Distinct cancellation invoices: 8,292
- Rows with `Quantity <= 0`: 22,950
- Rows with `Price <= 0`: 6,207
- Guest rows (missing `Customer ID`): 243,007 (22.77%)
- Rows flagged as non-product: 5,778

## Cleaning decisions

- The raw CSV retains every source row and original column value.
- The clean CSV removes only exact duplicate source rows. Cancellation rows, guest transactions, non-positive quantities or prices, and non-product rows remain in the file and are marked with flags for later analysis.
- `is_cancellation` is based on invoice values beginning with `C`.
- `is_guest` is based on a blank or missing `Customer ID`.
- `is_non_product` uses observed workbook codes for postage, manual adjustments, carriage, discounts, samples, bad-debt adjustments, bank charges, and fees. Codes: `ADJUST`, `ADJUST2`, `AMAZONFEE`, `B`, `BANK CHARGES`, `C2`, `D`, `DOT`, `M`, `POST`, `S`, `m`.
- `line_revenue` is `Quantity * Price`, calculated with decimal arithmetic. It is not filtered by cancellation, guest, or non-product status.
- Duplicate detection fingerprints the serialized values of every source column with SHA-256.

## Outputs

- Raw CSV: `data/processed/online_retail_raw.csv`
- Clean CSV: `data/processed/online_retail_clean.csv`
