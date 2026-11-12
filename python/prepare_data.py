"""Stream Online Retail II workbook sheets into raw and cleaned CSV files."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "data" / "raw" / "online_retail_II.xlsx"
OUTPUT_DIR = ROOT / "data" / "processed"
RAW_CSV = OUTPUT_DIR / "online_retail_raw.csv"
CLEAN_CSV = OUTPUT_DIR / "online_retail_clean.csv"
SAMPLE_CSV = ROOT / "data" / "sample" / "online_retail_sample_1000.csv"
REPORT = ROOT / "docs" / "data_quality_report.md"

EXPECTED_COLUMNS = (
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
)

# These identifiers are used by the workbook for shipping, adjustments,
# discounts, samples, and service fees rather than ordinary merchandise.
NON_PRODUCT_CODES = {
    "POST", "DOT", "M", "m", "C2", "D", "S", "B",
    "BANK CHARGES", "AMAZONFEE", "ADJUST", "ADJUST2",
}


def is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def csv_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, float):
        return repr(value)
    return value


def canonical_row(row: tuple[Any, ...]) -> bytes:
    values = [csv_value(value) for value in row]
    return json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def line_revenue(quantity: Any, price: Any) -> str:
    if is_missing(quantity) or is_missing(price):
        return ""
    try:
        return format(Decimal(str(quantity)) * Decimal(str(price)), "f")
    except (InvalidOperation, ValueError):
        return ""


def write_quality_report(stats: dict[str, Any]) -> None:
    missing_rows_pct = 100 * stats["guest_rows"] / stats["source_rows"] if stats["source_rows"] else 0
    header = [
        "# Data quality report",
        "",
        "Generated from the downloaded UCI workbook by `python/prepare_data.py`. The workbook is streamed one row at a time with openpyxl; CSV files are written with Python's built-in `csv` module.",
        "",
        "## Source and row counts",
        "",
        f"- Workbook: `{WORKBOOK.name}`",
        f"- Worksheets: {', '.join(stats['sheets'])}",
        *[f"- Rows in `{sheet}`: {count:,}" for sheet, count in stats["rows_by_sheet"].items()],
        f"- Source rows: {stats['source_rows']:,}",
        f"- Exact duplicate rows removed from the clean output: {stats['duplicates']:,}",
        f"- Rows in clean output: {stats['clean_rows']:,}",
        "",
        "## Missing values and data checks",
        "",
        "| Column | Missing rows |",
        "| --- | ---: |",
        *[f"| `{column}` | {count:,} |" for column, count in stats["missing_by_column"].items()],
        "",
        f"- Date range: {stats['min_date']} to {stats['max_date']}",
        f"- Cancellation rows (invoice starts with `C`, case-insensitive): {stats['cancellation_rows']:,}",
        f"- Distinct cancellation invoices: {stats['cancellation_invoices']:,}",
        f"- Rows with `Quantity <= 0`: {stats['quantity_nonpositive']:,}",
        f"- Rows with `Price <= 0`: {stats['price_nonpositive']:,}",
        f"- Guest rows (missing `Customer ID`): {stats['guest_rows']:,} ({missing_rows_pct:.2f}%)",
        f"- Rows flagged as non-product: {stats['non_product_rows']:,}",
        "",
        "## Cleaning decisions",
        "",
        "- The raw CSV retains every source row and original column value.",
        "- The clean CSV removes only exact duplicate source rows. Cancellation rows, guest transactions, non-positive quantities or prices, and non-product rows remain in the file and are marked with flags for later analysis.",
        "- `is_cancellation` is based on invoice values beginning with `C`.",
        "- `is_guest` is based on a blank or missing `Customer ID`.",
        "- `is_non_product` uses observed workbook codes for postage, manual adjustments, carriage, discounts, samples, bad-debt adjustments, bank charges, and fees. Codes: " + ", ".join(f"`{code}`" for code in sorted(NON_PRODUCT_CODES)) + ".",
        "- `line_revenue` is `Quantity * Price`, calculated with decimal arithmetic. It is not filtered by cancellation, guest, or non-product status.",
        "- Duplicate detection fingerprints the serialized values of every source column with SHA-256.",
        "",
        "## Outputs",
        "",
        f"- Raw CSV: `{RAW_CSV.relative_to(ROOT).as_posix()}`",
        f"- Clean CSV: `{CLEAN_CSV.relative_to(ROOT).as_posix()}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(header), encoding="utf-8")


def write_sample() -> None:
    SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CLEAN_CSV.open("r", encoding="utf-8-sig", newline="") as source:
        with SAMPLE_CSV.open("w", encoding="utf-8-sig", newline="") as target:
            reader = csv.reader(source)
            writer = csv.writer(target)
            for index, row in enumerate(reader):
                if index > 1_000:
                    break
                writer.writerow(row)


def main() -> None:
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Expected workbook at {WORKBOOK}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_tmp = RAW_CSV.with_suffix(RAW_CSV.suffix + ".tmp")
    clean_tmp = CLEAN_CSV.with_suffix(CLEAN_CSV.suffix + ".tmp")

    stats: dict[str, Any] = {
        "sheets": [],
        "rows_by_sheet": Counter(),
        "source_rows": 0,
        "clean_rows": 0,
        "duplicates": 0,
        "missing_by_column": Counter(),
        "cancellation_rows": 0,
        "cancellation_invoices_set": set(),
        "quantity_nonpositive": 0,
        "price_nonpositive": 0,
        "guest_rows": 0,
        "non_product_rows": 0,
        "min_date": None,
        "max_date": None,
    }
    seen_hashes: set[bytes] = set()
    raw_stream = None
    clean_stream = None
    workbook = load_workbook(WORKBOOK, read_only=True, data_only=True)
    try:
        raw_stream = raw_tmp.open("w", encoding="utf-8-sig", newline="")
        clean_stream = clean_tmp.open("w", encoding="utf-8-sig", newline="")
        raw_writer = csv.writer(raw_stream)
        clean_writer = csv.writer(clean_stream)
        raw_writer.writerow(EXPECTED_COLUMNS)
        clean_writer.writerow((*EXPECTED_COLUMNS, "is_cancellation", "is_guest", "is_non_product", "line_revenue"))

        for worksheet in workbook.worksheets:
            stats["sheets"].append(worksheet.title)
            rows = worksheet.iter_rows(values_only=True)
            headers = next(rows, None)
            if tuple(headers or ()) != EXPECTED_COLUMNS:
                raise ValueError(f"Unexpected headers in {worksheet.title}: {headers!r}")

            for row in rows:
                if row is None or all(is_missing(value) for value in row):
                    continue
                row = tuple(row)
                stats["source_rows"] += 1
                stats["rows_by_sheet"][worksheet.title] += 1
                raw_writer.writerow([csv_value(value) for value in row])

                for column, value in zip(EXPECTED_COLUMNS, row):
                    if is_missing(value):
                        stats["missing_by_column"][column] += 1

                invoice, stock_code, description, quantity, invoice_date, price, customer_id, country = row
                invoice_text = str(invoice or "").strip()
                code_text = str(stock_code or "").strip()
                cancellation = invoice_text.upper().startswith("C")
                guest = is_missing(customer_id)
                non_product = code_text in NON_PRODUCT_CODES

                if cancellation:
                    stats["cancellation_rows"] += 1
                    stats["cancellation_invoices_set"].add(invoice_text)
                if guest:
                    stats["guest_rows"] += 1
                if non_product:
                    stats["non_product_rows"] += 1
                try:
                    if not is_missing(quantity) and float(quantity) <= 0:
                        stats["quantity_nonpositive"] += 1
                except (TypeError, ValueError):
                    pass
                try:
                    if not is_missing(price) and float(price) <= 0:
                        stats["price_nonpositive"] += 1
                except (TypeError, ValueError):
                    pass

                if isinstance(invoice_date, datetime):
                    d = invoice_date.date()
                    stats["min_date"] = d if stats["min_date"] is None else min(stats["min_date"], d)
                    stats["max_date"] = d if stats["max_date"] is None else max(stats["max_date"], d)

                fingerprint = hashlib.sha256(canonical_row(row)).digest()
                if fingerprint in seen_hashes:
                    stats["duplicates"] += 1
                    continue
                seen_hashes.add(fingerprint)
                stats["clean_rows"] += 1
                clean_writer.writerow(
                    [csv_value(value) for value in row]
                    + [int(cancellation), int(guest), int(non_product), line_revenue(quantity, price)]
                )
            raw_stream.flush()
            clean_stream.flush()
            print(f"Finished worksheet {worksheet.title}: {stats['rows_by_sheet'][worksheet.title]:,} rows", flush=True)
    except Exception:
        raw_stream.close()
        clean_stream.close()
        raw_tmp.unlink(missing_ok=True)
        clean_tmp.unlink(missing_ok=True)
        raise
    finally:
        if not raw_stream.closed:
            raw_stream.close()
        if not clean_stream.closed:
            clean_stream.close()
        workbook.close()

    os.replace(raw_tmp, RAW_CSV)
    os.replace(clean_tmp, CLEAN_CSV)
    write_sample()
    stats["cancellation_invoices"] = len(stats.pop("cancellation_invoices_set"))
    stats["min_date"] = stats["min_date"].isoformat() if stats["min_date"] else "unknown"
    stats["max_date"] = stats["max_date"].isoformat() if stats["max_date"] else "unknown"
    write_quality_report(stats)
    print(f"Raw rows: {stats['source_rows']:,}; clean rows: {stats['clean_rows']:,}; duplicates removed: {stats['duplicates']:,}")
    print(f"Wrote {RAW_CSV.relative_to(ROOT)}")
    print(f"Wrote {CLEAN_CSV.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
