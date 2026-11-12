# Analysis methodology

## Scope

This analysis uses the UCI Online Retail II transaction workbook and focuses on merchandise sales, customer behavior, cancellations, and repeat purchasing. The workbook contains two sheets covering December 2009 through December 2011.

## Row treatment

- Preserve the source rows in the raw extract.
- Remove exact duplicate rows from the clean extract and record the removal count.
- Retain cancellations and non-positive quantities or prices so they can be measured and reconciled.
- Flag guest transactions and non-merchandise codes instead of silently discarding them.
- Exclude flagged non-merchandise lines from merchandise revenue measures.
- Keep guest sales in transaction revenue metrics, but require a customer ID for registered customer metrics.
- Exclude the incomplete December 2011 period from full-month trend comparisons.

## Revenue definition

Line revenue is quantity multiplied by unit price. Merchandise revenue includes merchandise-coded transactions after applying the query-specific treatment of cancellation invoices. Cancellation rates and canceled value are reported separately so gross sales and reversals are not conflated.

## Reproducibility

The raw workbook is not distributed in this repository. Download it from the UCI Machine Learning Repository and follow its CC BY 4.0 attribution terms. Run `python/prepare_data.py`, load the generated CSV files with `python/load_mysql.py`, and execute the numbered SQL files with `python/run_queries.py`.
