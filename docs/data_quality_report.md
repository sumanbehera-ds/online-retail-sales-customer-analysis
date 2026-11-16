# Data quality report

Generated from the downloaded UCI workbook by `python/prepare_data.py`. The workbook is streamed one row at a time with openpyxl; CSV files are written with Python's built-in `csv` module.

## Source and row counts

- Workbook: `online_retail_II.xlsx`
- Worksheets: Year 2009-2010, Year 2010-2011
- Rows in `Year 2009-2010`: 525,461
- Rows in `Year 2010-2011`: 541,910
- Source rows: 1,067,371
- Exact cross-sheet overlap rows removed: 22,523
- Exact within-sheet repeats retained: 12,133
- Rows in clean output: 1,044,848

## Worksheet coverage

| Worksheet | Source rows | First date | Last date | Within-sheet repeats retained | Cross-sheet overlaps removed |
| --- | ---: | --- | --- | ---: | ---: |
| `Year 2009-2010` | 525,461 | 2009-12-01 | 2010-12-09 | 6,865 | 0 |
| `Year 2010-2011` | 541,910 | 2010-12-01 | 2011-12-09 | 5,268 | 22,523 |

- Source line revenue total: GBP 19287250.568
- Clean line revenue total: GBP 18909762.118

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
- Rows flagged as non-product: 5,911

## Cleaning decisions

- The raw CSV retains every nonblank source row, its worksheet name, and original column values.
- The clean CSV removes repeated exact records only where the same source record overlaps across the two worksheets. Exact repeats within one worksheet are preserved because they may represent real repeated scans.
- `source_sheet` records the worksheet for each row so overlap handling can be audited.
- `is_cancellation` is based on invoice values beginning with `C`.
- `is_guest` is based on a blank or missing `Customer ID`.
- `is_non_product` uses observed workbook codes for postage, manual adjustments, carriage, discounts, samples, bad-debt adjustments, bank charges, fees, charity commission, test products, and gift vouchers. Codes: `ADJUST`, `ADJUST2`, `AMAZONFEE`, `B`, `BANK CHARGES`, `C2`, `CRUK`, `D`, `DOT`, `M`, `POST`, `S`, `TEST001`, `TEST002`; gift voucher codes match `gift_0001_<amount>`.
- `line_revenue` is `Quantity * Price`, calculated with decimal arithmetic. It is not filtered by cancellation, guest, or non-product status.
- Cross-sheet overlap matching fingerprints the serialized values of every original source column with SHA-256. The matching copies in the later sheet are removed up to the multiplicity present in the earlier sheet; excess same-sheet occurrences remain.
- Product descriptions in the clean output have leading/trailing whitespace removed; raw descriptions are preserved.
- `docs/stock_code_audit.csv` lists every code, row count, revenue, and most common description. Nonstandard code shapes are review candidates only; the audit does not automatically classify them as non-products.
- The sample is a deterministic random sample of five whole invoices per observed invoice month (seed 42), rather than the first 1,000 rows.

## Outputs

- Raw CSV: `data/processed/online_retail_raw.csv`
- Clean CSV: `data/processed/online_retail_clean.csv`
- Seeded invoice sample: `data/sample/online_retail_sample_invoices.csv`
- Machine-readable quality summary: `docs/data_quality_report.json`
- Stock-code review: `docs/stock_code_audit.csv` (generated separately by `python/audit_stock_codes.py`)
