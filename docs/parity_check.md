# SQL and Power BI parity check

## Status

The SQL reference values below are verified in `docs/query_results/01_core_kpis.csv` and `08_repeat_customer_rate.csv`, and are independently reproduced by `notebooks/01_crosscheck.ipynb`. Power BI parity is **not verified**: the saved `.pbix` currently contains one page with one Gross Revenue card, and Power BI Desktop could not be inspected in this session. No match is claimed until each measure is read from the full-data report and compared.

Compare the values with no slicers or page filters active. Currency values are GBP. Use a tolerance of GBP 0.01 for displayed currency values and exact equality for counts; rates are rounded to the precision shown.

| Measure | SQL reference | Power BI value | Match |
| --- | ---: | ---: | --- |
| Gross Revenue | GBP 19,700,954.46 | Pending | Not checked |
| Cancelled Value | GBP 719,692.94 | Pending | Not checked |
| Net Revenue | GBP 18,981,261.52 | Pending | Not checked |
| Orders | 39,516 | Pending | Not checked |
| Registered Customers | 5,852 | Pending | Not checked |
| Average Order Value | GBP 498.56 | Pending | Not checked |
| Cancellation Rate | 15.46% | Pending | Not checked |
| Repeat Customer Rate | 72.35% | Pending | Not checked |

When the interactive report is available, record the displayed value, then mark the row `Yes` only if it matches the SQL reference under the stated tolerance. If it differs, check the table row count, model relationships, active filters, measure definition, and data types before changing anything.
