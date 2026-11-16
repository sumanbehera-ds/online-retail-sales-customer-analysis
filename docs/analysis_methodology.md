# Analysis methodology

## Scope

This analysis uses the UCI Online Retail II transaction workbook and focuses on merchandise sales, customer behavior, cancellations, and repeat purchasing. The workbook contains two sheets covering December 2009 through December 2011.

## Row treatment

- Preserve every nonblank source row in the raw extract and add its `source_sheet` value.
- Remove exact cross-sheet overlap copies from the later worksheet, up to the number of matching rows in the earlier worksheet. Retain exact repeats within a worksheet, since the source does not prove those repeated lines are accidental duplicates.
- Record worksheet date ranges, overlap counts and within-sheet repeat counts separately.
- Trim only leading/trailing whitespace from descriptions in the clean extract; retain the source description text in raw.
- Retain cancellations and non-positive quantities or prices so they can be measured and reconciled.
- Flag guest transactions and non-merchandise codes instead of silently discarding them.
- Exclude flagged non-merchandise lines from merchandise revenue measures.
- Keep guest sales in transaction revenue metrics, but require a customer ID for registered customer metrics.
- Exclude the incomplete December 2011 period from full-month trend comparisons.
- Treat monetary values as GBP, matching UCI's definition of UnitPrice as sterling.
- Use five randomly selected whole invoices per observed invoice month for the tracked sample, with seed 42. The sample is useful for exercising the schema and date coverage, not a statistically weighted estimate.

## Revenue definition

Line revenue is quantity multiplied by unit price. Merchandise revenue includes merchandise-coded transactions after applying the query-specific treatment of cancellation invoices. Cancellation rates and canceled value are reported separately so gross sales and reversals are not conflated.

## Reproducibility

The raw workbook is not distributed in this repository. Download it from the UCI Machine Learning Repository and follow its CC BY 4.0 attribution terms. Run `python/prepare_data.py`, load the generated CSV files with `python/load_mysql.py`, and execute the numbered SQL files with `python/run_queries.py`.

## Limitations

- Customer IDs are absent on 243,007 rows (22.77% in the inspected workbook). Repeat-customer, RFM and cohort analyses therefore describe identified customers only; guest transactions remain available for transaction-level revenue metrics.
- The first observed purchase month is not necessarily the customer's true acquisition month. Customers who first appear in the December 2009 cohort may have purchased before the workbook starts, so that cohort is left-censored and should not be described as definitely new customers.
- Cancellation invoices are dated at the time the cancellation was recorded. The workbook does not provide a key linking each reversal to its original sale, so cancellation-by-month is not the same as original-sale-month reversal analysis.
- Repeat rate, recency and retention are limited to the observed window from December 2009 through December 2011; they do not establish lifetime customer behavior.
- December 2011 ends on the 9th and is partial. Trend queries exclude it; queries that retain partial months flag it for interpretation.
- Non-product codes are a manually reviewed list. A rule that flags every stock code containing letters would incorrectly classify valid products such as `85123A` and `85099B`.
- A repeated identical line within one worksheet is preserved. Without a transaction-line identifier, the data alone cannot prove whether it is a duplicate import or a genuine repeated scan.
- The deterministic sample uses five whole invoices per month with a fixed seed. It supports reproducible smoke checks but is not representative for estimating business metrics.
- Query totals and Power BI measures must be reconciled after execution; the SQL and DAX definitions are not a substitute for database/model validation.
