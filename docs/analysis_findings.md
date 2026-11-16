# Verified SQL findings

Generated from the twelve MySQL analysis queries in `sql/` after the staged replacement load. The CSV evidence is stored beside this document in `docs/query_results/`. Monetary amounts are GBP. These are descriptive results for the observed dataset, not forecasts or causal claims.

## Headline results

| Measure | Result | Definition / source |
| --- | ---: | --- |
| Gross merchandise revenue | GBP 19,700,954.46 | Positive, non-cancelled merchandise lines; excludes configured non-product codes (`01_core_kpis.sql`). |
| Cancelled merchandise value | GBP 719,692.94 | Absolute value of cancellation merchandise lines (`01_core_kpis.sql`, reconciled to `07_cancelled_value_share.csv`). |
| Net merchandise revenue | GBP 18,981,261.52 | Gross merchandise revenue less cancelled merchandise value. |
| Sales invoices | 39,516 | Distinct eligible positive sales invoices. |
| Average order value | GBP 498.56 | Gross merchandise revenue divided by eligible sales invoices. |
| Registered customers | 5,852 | Distinct nonblank customer IDs on eligible sales lines. |
| Cancelled invoices | 8,292 | All distinct cancellation invoices, including invoices that contain only non-product lines. |
| Cancellation invoice rate | 15.46% | All cancellation invoices divided by all 53,628 distinct invoice IDs in the clean table; this matches the monthly cancellation query and DAX measure. |
| Repeat customers | 4,234 of 5,852 (72.35%) | Registered customers with at least two eligible sales invoices in this observation window. |

The headline money reconciles: monthly gross merchandise revenue in query 07 sums to query 01 gross revenue; monthly cancelled value sums to the query 01 gross-minus-net difference. Country revenue in query 05 also sums to gross merchandise revenue. RFM segment counts sum to the 5,852 registered customers.

## Customer, product, and geography patterns

- The top spending decile contributes GBP 10,927,073.97, or 63.81% of registered-customer revenue (`09_top_customers_and_decile.csv`). The result reports ranks and spend only; it does not export customer IDs.
- RFM scoring assigns 1,249 customers to Champions (GBP 11.55m), 857 to Loyal (GBP 2.72m), 1,676 to Potential (GBP 1.57m), 1,632 to Hibernating (GBP 0.70m), and 438 to At Risk (GBP 0.58m) (`10_rfm_segments.csv`). These are rule-based segments, not a trained predictive model.
- The United Kingdom accounts for GBP 16,856,330.96, or 85.56% of merchandise revenue. EIRE and the Netherlands follow at GBP 623,795.85 and GBP 549,775.06 (`05_country_revenue.csv`).
- `REGENCY CAKESTAND 3 TIER` is the highest-revenue product at GBP 331,084.27. `WORLD WAR 2 GLIDERS ASSTD DESIGNS` ranks first by units (106,379), but only 158th by revenue (`04_top_products.csv`). This illustrates why unit volume and revenue rankings answer different questions.
- The most positive month-over-month change is May 2011 (+43.58%); the largest decline is December 2010 (-45.81%) (`02_monthly_revenue_mom.csv`). Among complete same-calendar-month comparisons, September 2011 has the strongest year-over-year growth (+18.19%) and April 2011 the weakest (-20.46%) (`03_year_over_year.csv`). December 2011 is partial and excluded from full-month revenue comparisons.
- The highest complete-month cancellation invoice rate is January 2010 (18.37%); the lowest is February 2010 (12.19%) (`06_cancellation_rate_by_month.csv`). The largest complete-month cancelled-value share is January 2011 (13.62%), while the lowest is May 2011 (1.21%) (`07_cancelled_value_share.csv`). Invoice rates and value shares are different measures.
- The busiest weekday/hour cell is Wednesday at 12:00, with 1,212 eligible invoices (`12_orders_by_weekday_hour.csv`). It measures invoice concentration in the source timestamps and does not establish an ideal staffing schedule.
- In the first observed cohort, 333 of 951 identified customers appear again in January 2010 (35.02% month-1 activity). The cohort begins at the workbook's observation boundary, so it is left-censored and cannot be assumed to consist entirely of newly acquired customers (`11_cohort_retention.csv`).

## Data and validation evidence

- MySQL published 1,067,371 raw rows and 1,044,848 clean rows. Stored raw and clean line-revenue totals match the CSV totals: GBP 19,287,250.568 and GBP 18,909,762.118.
- The clean extract removes 22,523 exact cross-sheet overlap copies and preserves 12,133 exact within-sheet repeats. This matters because repeated identical lines in one worksheet are not provably accidental duplicates.
- The source has 243,007 guest rows (22.77%), 19,494 cancellation rows, 4,382 missing descriptions, 22,950 non-positive-quantity rows, and 6,207 non-positive-price rows. Cleaning retains these rows and flags them for query-specific treatment.
- Six standard-library unit tests passed; the CSV validator passed row, revenue, worksheet, and complete-invoice sample checks. The database loader reported row and revenue validation before publishing the replacement tables.

## Interpretation limits

- The observation window is December 2009 through December 9, 2011. Repeat rate, recency, RFM, and cohort activity are window-limited and do not measure lifetime behavior.
- Customer IDs are missing for 22.77% of source rows. Customer metrics cover identified customers; transaction-level merchandise metrics can include guest rows.
- The workbook records cancellation dates but does not link each reversal to its original sale. Monthly cancellation patterns therefore describe recorded cancellation activity, not the month of the original order.
- December 2011 is incomplete. The trend queries exclude it, while cancellation and cohort outputs label the partial month.
- The first observed month may include pre-existing customers. Cohorts identify first purchase *within this workbook*, not necessarily customer acquisition.
- Non-product codes are manually configured from this dataset. The stock-code audit includes 38 nonstandard-shape review candidates; shape alone does not prove a code is non-product.
- The DAX file is a reference, not a `.pbix` model. Power BI Desktop is not installed in the current environment, so SQL/DAX parity, report visuals, and screenshots remain unverified.
- The SQL queries are descriptive and do not include statistical significance tests, causal methods, or forecasting.

## Recommendations for the next iteration

1. Build the Power BI model, mark `DimDate` as the date table, sort month labels by month number, and reconcile revenue, orders, cancellation rate, repeat rate, RFM counts, and cohort retention against these CSV results.
2. Review the 38 nonstandard stock-code candidates against source descriptions before changing the configured non-product list; do not exclude codes based only on a regular expression.
3. If the business question is cancellation impact by original sale, add a defensible linkage from cancellation line to original invoice before attributing reversals to sale months.
4. For future repeat/retention reporting, refresh the analysis with a longer observation window and explicitly separate identified customers from guest transactions.
5. Treat the top-decile share and RFM segments as prioritization signals for investigation, then validate any business action with a controlled experiment or additional operational data.
