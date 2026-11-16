"""Stream Online Retail II workbook sheets into raw and cleaned CSV files."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
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
SAMPLE_CSV = ROOT / "data" / "sample" / "online_retail_sample_invoices.csv"
REPORT = ROOT / "docs" / "data_quality_report.md"
REPORT_JSON = ROOT / "docs" / "data_quality_report.json"
SAMPLE_SEED = 42
SAMPLE_INVOICES_PER_MONTH = 5

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
    "POST", "DOT", "M", "C2", "D", "S", "B",
    "BANK CHARGES", "AMAZONFEE", "ADJUST", "ADJUST2",
    "CRUK", "TEST001", "TEST002",
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


def is_non_product_code(code: Any) -> bool:
    normalized = str(code or "").strip()
    return normalized.upper() in NON_PRODUCT_CODES or bool(
        re.fullmatch(r"gift_0001_\d+", normalized, flags=re.IGNORECASE)
    )


def normalize_description(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def is_cross_sheet_overlap(current_occurrence: int, earlier_sheet_occurrences: int) -> bool:
    """Remove only the later-sheet copies covered by an earlier-sheet multiplicity."""
    return current_occurrence <= earlier_sheet_occurrences


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
        f"- Exact cross-sheet overlap rows removed: {stats['cross_sheet_duplicate_rows']:,}",
        f"- Exact within-sheet repeats retained: {sum(stats['within_sheet_repeats'].values()):,}",
        f"- Rows in clean output: {stats['clean_rows']:,}",
        "",
        "## Worksheet coverage",
        "",
        "| Worksheet | Source rows | First date | Last date | Within-sheet repeats retained | Cross-sheet overlaps removed |",
        "| --- | ---: | --- | --- | ---: | ---: |",
        *[
            f"| `{sheet}` | {stats['rows_by_sheet'][sheet]:,} | {stats['date_ranges_by_sheet'][sheet]['min']} | {stats['date_ranges_by_sheet'][sheet]['max']} | {stats['within_sheet_repeats'][sheet]:,} | {stats['cross_sheet_duplicates_by_sheet'][sheet]:,} |"
            for sheet in stats["sheets"]
        ],
        "",
        f"- Source line revenue total: GBP {stats['source_line_revenue_total']}",
        f"- Clean line revenue total: GBP {stats['clean_line_revenue_total']}",
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
        "- The raw CSV retains every nonblank source row, its worksheet name, and original column values.",
        "- The clean CSV removes repeated exact records only where the same source record overlaps across the two worksheets. Exact repeats within one worksheet are preserved because they may represent real repeated scans.",
        "- `source_sheet` records the worksheet for each row so overlap handling can be audited.",
        "- `is_cancellation` is based on invoice values beginning with `C`.",
        "- `is_guest` is based on a blank or missing `Customer ID`.",
        "- `is_non_product` uses observed workbook codes for postage, manual adjustments, carriage, discounts, samples, bad-debt adjustments, bank charges, fees, charity commission, test products, and gift vouchers. Codes: " + ", ".join(f"`{code}`" for code in sorted(NON_PRODUCT_CODES)) + "; gift voucher codes match `gift_0001_<amount>`.",
        "- `line_revenue` is `Quantity * Price`, calculated with decimal arithmetic. It is not filtered by cancellation, guest, or non-product status.",
        "- Cross-sheet overlap matching fingerprints the serialized values of every original source column with SHA-256. The matching copies in the later sheet are removed up to the multiplicity present in the earlier sheet; excess same-sheet occurrences remain.",
        "- Product descriptions in the clean output have leading/trailing whitespace removed; raw descriptions are preserved.",
        "- `docs/stock_code_audit.csv` lists every code, row count, revenue, and most common description. Nonstandard code shapes are review candidates only; the audit does not automatically classify them as non-products.",
        "- The sample is a deterministic random sample of five whole invoices per observed invoice month (seed 42), rather than the first 1,000 rows.",
        "",
        "## Outputs",
        "",
        f"- Raw CSV: `{RAW_CSV.relative_to(ROOT).as_posix()}`",
        f"- Clean CSV: `{CLEAN_CSV.relative_to(ROOT).as_posix()}`",
        f"- Seeded invoice sample: `{SAMPLE_CSV.relative_to(ROOT).as_posix()}`",
        f"- Machine-readable quality summary: `{REPORT_JSON.relative_to(ROOT).as_posix()}`",
        "- Stock-code review: `docs/stock_code_audit.csv` (generated separately by `python/audit_stock_codes.py`)",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(header), encoding="utf-8")
    json_stats = {
        "source_rows": stats["source_rows"],
        "rows_by_sheet": dict(stats["rows_by_sheet"]),
        "date_ranges_by_sheet": stats["date_ranges_by_sheet"],
        "cross_sheet_duplicate_rows": stats["cross_sheet_duplicate_rows"],
        "cross_sheet_duplicates_by_sheet": dict(stats["cross_sheet_duplicates_by_sheet"]),
        "within_sheet_repeats_retained": dict(stats["within_sheet_repeats"]),
        "clean_rows": stats["clean_rows"],
        "missing_by_column": dict(stats["missing_by_column"]),
        "cancellation_rows": stats["cancellation_rows"],
        "cancellation_invoices": stats["cancellation_invoices"],
        "quantity_nonpositive": stats["quantity_nonpositive"],
        "price_nonpositive": stats["price_nonpositive"],
        "guest_rows": stats["guest_rows"],
        "non_product_rows": stats["non_product_rows"],
        "min_date": stats["min_date"],
        "max_date": stats["max_date"],
        "source_line_revenue_total": stats["source_line_revenue_total"],
        "clean_line_revenue_total": stats["clean_line_revenue_total"],
        "sample_seed": SAMPLE_SEED,
        "sample_invoices_per_month": SAMPLE_INVOICES_PER_MONTH,
    }
    REPORT_JSON.write_text(json.dumps(json_stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_sample() -> int:
    SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SAMPLE_SEED)
    reservoirs: dict[str, list[str]] = {}
    seen_invoices: dict[str, set[str]] = {}
    invoice_counts: Counter[str] = Counter()
    with CLEAN_CSV.open("r", encoding="utf-8-sig", newline="") as source:
        for record in csv.DictReader(source):
            invoice = (record.get("Invoice") or "").strip()
            month = (record.get("InvoiceDate") or "")[:7]
            if not invoice or len(month) != 7:
                continue
            seen = seen_invoices.setdefault(month, set())
            if invoice in seen:
                continue
            seen.add(invoice)
            invoice_counts[month] += 1
            reservoir = reservoirs.setdefault(month, [])
            if len(reservoir) < SAMPLE_INVOICES_PER_MONTH:
                reservoir.append(invoice)
            else:
                position = rng.randrange(invoice_counts[month])
                if position < SAMPLE_INVOICES_PER_MONTH:
                    reservoir[position] = invoice
    selected = {invoice for invoices in reservoirs.values() for invoice in invoices}
    with CLEAN_CSV.open("r", encoding="utf-8-sig", newline="") as source:
        with SAMPLE_CSV.open("w", encoding="utf-8-sig", newline="") as target:
            reader = csv.DictReader(source)
            writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
            writer.writeheader()
            for record in reader:
                if (record.get("Invoice") or "").strip() in selected:
                    writer.writerow(record)
    return len(selected)


def main() -> None:
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Expected workbook at {WORKBOOK}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_tmp = RAW_CSV.with_suffix(RAW_CSV.suffix + ".tmp")
    clean_tmp = CLEAN_CSV.with_suffix(CLEAN_CSV.suffix + ".tmp")

    stats: dict[str, Any] = {
        "sheets": [],
        "rows_by_sheet": Counter(),
        "date_ranges_by_sheet": {},
        "source_rows": 0,
        "clean_rows": 0,
        "cross_sheet_duplicate_rows": 0,
        "cross_sheet_duplicates_by_sheet": Counter(),
        "within_sheet_repeats": Counter(),
        "missing_by_column": Counter(),
        "cancellation_rows": 0,
        "cancellation_invoices_set": set(),
        "quantity_nonpositive": 0,
        "price_nonpositive": 0,
        "guest_rows": 0,
        "non_product_rows": 0,
        "source_line_revenue_total": Decimal("0"),
        "clean_line_revenue_total": Decimal("0"),
        "min_date": None,
        "max_date": None,
    }
    first_sheet_hash_counts: Counter[bytes] = Counter()
    raw_stream = None
    clean_stream = None
    workbook = load_workbook(WORKBOOK, read_only=True, data_only=True)
    try:
        if len(workbook.worksheets) != 2:
            raise ValueError(f"Expected two source worksheets, found {len(workbook.worksheets)}")
        raw_stream = raw_tmp.open("w", encoding="utf-8-sig", newline="")
        clean_stream = clean_tmp.open("w", encoding="utf-8-sig", newline="")
        raw_writer = csv.writer(raw_stream)
        clean_writer = csv.writer(clean_stream)
        raw_writer.writerow(("source_sheet", *EXPECTED_COLUMNS))
        clean_writer.writerow(("source_sheet", *EXPECTED_COLUMNS, "is_cancellation", "is_guest", "is_non_product", "line_revenue"))

        for worksheet_index, worksheet in enumerate(workbook.worksheets):
            stats["sheets"].append(worksheet.title)
            current_sheet_hash_counts: Counter[bytes] = Counter()
            sheet_min_date = None
            sheet_max_date = None
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
                raw_writer.writerow([worksheet.title, *[csv_value(value) for value in row]])

                for column, value in zip(EXPECTED_COLUMNS, row):
                    if is_missing(value):
                        stats["missing_by_column"][column] += 1

                invoice, stock_code, description, quantity, invoice_date, price, customer_id, country = row
                invoice_text = str(invoice or "").strip()
                code_text = str(stock_code or "").strip()
                cancellation = invoice_text.upper().startswith("C")
                guest = is_missing(customer_id)
                non_product = is_non_product_code(code_text)

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
                    sheet_min_date = d if sheet_min_date is None else min(sheet_min_date, d)
                    sheet_max_date = d if sheet_max_date is None else max(sheet_max_date, d)

                line_value = line_revenue(quantity, price)
                if line_value:
                    stats["source_line_revenue_total"] += Decimal(line_value)

                fingerprint = hashlib.sha256(canonical_row(row)).digest()
                current_sheet_hash_counts[fingerprint] += 1
                if current_sheet_hash_counts[fingerprint] > 1:
                    stats["within_sheet_repeats"][worksheet.title] += 1
                if worksheet_index > 0 and is_cross_sheet_overlap(
                    current_sheet_hash_counts[fingerprint], first_sheet_hash_counts[fingerprint]
                ):
                    stats["cross_sheet_duplicate_rows"] += 1
                    stats["cross_sheet_duplicates_by_sheet"][worksheet.title] += 1
                    continue
                stats["clean_rows"] += 1
                clean_values = [csv_value(value) for value in row]
                if isinstance(description, str):
                    clean_values[2] = normalize_description(description)
                if line_value:
                    stats["clean_line_revenue_total"] += Decimal(line_value)
                clean_writer.writerow(
                    [worksheet.title, *clean_values]
                    + [int(cancellation), int(guest), int(non_product), line_value]
                )
            raw_stream.flush()
            clean_stream.flush()
            print(f"Finished worksheet {worksheet.title}: {stats['rows_by_sheet'][worksheet.title]:,} rows", flush=True)
            stats["date_ranges_by_sheet"][worksheet.title] = {
                "min": sheet_min_date.isoformat() if sheet_min_date else "unknown",
                "max": sheet_max_date.isoformat() if sheet_max_date else "unknown",
            }
            if worksheet_index == 0:
                first_sheet_hash_counts = current_sheet_hash_counts
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
    stats["cancellation_invoices"] = len(stats.pop("cancellation_invoices_set"))
    stats["min_date"] = stats["min_date"].isoformat() if stats["min_date"] else "unknown"
    stats["max_date"] = stats["max_date"].isoformat() if stats["max_date"] else "unknown"
    stats["source_line_revenue_total"] = format(stats["source_line_revenue_total"], "f")
    stats["clean_line_revenue_total"] = format(stats["clean_line_revenue_total"], "f")
    write_quality_report(stats)
    sample_invoice_count = write_sample()
    print(f"Raw rows: {stats['source_rows']:,}; clean rows: {stats['clean_rows']:,}; cross-sheet overlaps removed: {stats['cross_sheet_duplicate_rows']:,}")
    print(f"Retained within-sheet exact repeats: {sum(stats['within_sheet_repeats'].values()):,}; sampled invoices: {sample_invoice_count:,}")
    print(f"Wrote {RAW_CSV.relative_to(ROOT)}")
    print(f"Wrote {CLEAN_CSV.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
