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

## Five findings

1. The United Kingdom accounts for GBP 16,856,330.96, or 85.56% of merchandise revenue. EIRE and the Netherlands follow at GBP 623,795.85 and GBP 549,775.06 (`05_country_revenue.csv`).
2. The top spending decile contributes GBP 10,927,073.97, or 63.81% of registered-customer revenue. The query reports ranks and spend without customer IDs (`09_top_customers_and_decile.csv`).
3. September through November generated GBP 3,405,576.13 of GBP 9,406,350.19 in full-year 2010 revenue (36.21%). Those months generated GBP 3,594,890.71 of GBP 8,878,008.02 in January-November 2011 revenue (40.49%). December 2011 is excluded as an incomplete month (`02_monthly_revenue_mom.csv`).
4. The cancellation invoice rate is 15.46% (8,292 of 53,628 invoices), while cancelled merchandise value is 3.65% of gross merchandise revenue (GBP 719,692.94 of GBP 19,700,954.46). January 2011 has the largest complete-month cancelled-value share at 13.62% (`01_core_kpis.csv`, `06_cancellation_rate_by_month.csv`, `07_cancelled_value_share.csv`).
5. Repeat customers are 4,234 of 5,852 identified customers (72.35%). Hibernating and At Risk segments include 2,070 customers and GBP 1,278,848.69 in revenue combined. These segments are rule-based descriptions, not predictions (`08_repeat_customer_rate.csv`, `10_rfm_segments.csv`).

Additional query evidence remains available in `docs/query_results/`. For example, the highest-revenue product is `REGENCY CAKESTAND 3 TIER` (GBP 331,084.27), while the busiest weekday/hour cell is Wednesday at 12:00 (1,212 eligible invoices) (`04_top_products.csv`, `12_orders_by_weekday_hour.csv`). The latter describes observed timestamps and does not establish an ideal staffing schedule.

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
- The DAX file is a reference, not an executable model. A `.pbix` is present, but it currently contains one page with one Gross Revenue card. Measure parity, the two-page report, and screenshots remain unverified; see `docs/parity_check.md`.
- The SQL queries are descriptive and do not include statistical significance tests, causal methods, or forecasting.

## Three recommendations

1. Track recency among Champions and At Risk customers, then evaluate retention actions with a controlled test before scaling them.
2. Use the observed September-November concentration to inform inventory and staffing reviews, while treating the values as historical description rather than a forecast.
3. Record cancellation reasons and establish a defensible link to original invoices before attributing cancellations to the original sale month. The current source contains no reason codes or reversal links.
