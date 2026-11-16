"""Validate generated CSVs against the quality summary and sample rules."""

from __future__ import annotations

import argparse
import csv
import getpass
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pymysql


ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "processed" / "online_retail_raw.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "online_retail_clean.csv"
SAMPLE_CSV = ROOT / "data" / "sample" / "online_retail_sample_invoices.csv"
SUMMARY_JSON = ROOT / "docs" / "data_quality_report.json"


def read_csv_summary(path: Path, *, clean: bool) -> tuple[int, Decimal, Counter[str], Counter[str]]:
    rows = 0
    revenue = Decimal("0")
    sheet_counts: Counter[str] = Counter()
    invoice_rows: Counter[str] = Counter()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"source_sheet", "Invoice", "InvoiceDate", "Quantity", "Price"}
        if clean:
            required |= {"line_revenue", "Description", "is_non_product"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path.name} is missing required columns: {sorted(required - set(reader.fieldnames or []))}")
        for record in reader:
            rows += 1
            sheet_counts[record["source_sheet"]] += 1
            invoice = (record.get("Invoice") or "").strip()
            if invoice:
                invoice_rows[invoice] += 1
            if clean:
                revenue += Decimal(record["line_revenue"]) if record["line_revenue"] else Decimal("0")
            elif record["Quantity"] and record["Price"]:
                revenue += Decimal(record["Quantity"]) * Decimal(record["Price"])
    return rows, revenue, sheet_counts, invoice_rows


def validate_sample(clean_csv: Path, sample_csv: Path, expected_per_month: int) -> tuple[int, int]:
    full_invoice_counts: Counter[str] = Counter()
    full_invoice_months: dict[str, str] = {}
    with clean_csv.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            invoice = (row.get("Invoice") or "").strip()
            month = (row.get("InvoiceDate") or "")[:7]
            if invoice:
                full_invoice_counts[invoice] += 1
                full_invoice_months.setdefault(invoice, month)

    sample_invoice_counts: Counter[str] = Counter()
    sample_months: Counter[str] = Counter()
    with sample_csv.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            invoice = (row.get("Invoice") or "").strip()
            if invoice:
                sample_invoice_counts[invoice] += 1
                sample_months[(row.get("InvoiceDate") or "")[:7]] += 0
    for invoice, rows in sample_invoice_counts.items():
        if invoice not in full_invoice_counts or rows != full_invoice_counts[invoice]:
            raise ValueError(f"Sample invoice {invoice!r} is missing or does not contain every clean line")
        sample_months[full_invoice_months[invoice]] += 1
    expected_months = {month for month in full_invoice_months.values()}
    if set(sample_months) != expected_months:
        raise ValueError(f"Sample month coverage differs: missing {sorted(expected_months - set(sample_months))}")
    if any(count > expected_per_month for count in sample_months.values()):
        raise ValueError("Sample exceeds the configured invoice count in one or more months")
    sample_rows = sum(sample_invoice_counts.values())
    return len(sample_invoice_counts), sample_rows


def validate_mysql(summary: dict) -> None:
    user = input("MySQL user [root]: ").strip() or "root"
    password = getpass.getpass("MySQL password (input is hidden): ")
    host = input("MySQL host [127.0.0.1]: ").strip() or "127.0.0.1"
    port = int(input("MySQL port [3306]: ").strip() or "3306")
    connection = pymysql.connect(host=host, port=port, user=user, password=password,
                                 database="online_retail", charset="utf8mb4")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity * price), 0) FROM online_retail_raw")
            raw_count, raw_revenue = cursor.fetchone()
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(line_revenue), 0) FROM online_retail_clean")
            clean_count, clean_revenue = cursor.fetchone()
        expected = {
            "raw rows": (raw_count, summary["source_rows"]),
            "clean rows": (clean_count, summary["clean_rows"]),
            "raw revenue": (Decimal(raw_revenue), Decimal(summary["source_line_revenue_total"])),
            "clean revenue": (Decimal(clean_revenue), Decimal(summary["clean_line_revenue_total"])),
        }
        mismatches = [f"{label}: {actual!s} != {wanted!s}" for label, (actual, wanted) in expected.items() if actual != wanted]
        if mismatches:
            raise RuntimeError("MySQL validation failed:\n" + "\n".join(mismatches))
        print(f"MySQL validated: raw={raw_count:,}, clean={clean_count:,}, raw/clean revenues match CSV summary")
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysql", action="store_true", help="also compare the published MySQL tables")
    args = parser.parse_args()
    for path in (RAW_CSV, CLEAN_CSV, SAMPLE_CSV, SUMMARY_JSON):
        if not path.exists():
            raise FileNotFoundError(f"Required file is missing: {path.relative_to(ROOT)}")
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    raw_rows, raw_revenue, raw_sheets, _ = read_csv_summary(RAW_CSV, clean=False)
    clean_rows, clean_revenue, clean_sheets, _ = read_csv_summary(CLEAN_CSV, clean=True)
    checks = {
        "raw rows": (raw_rows, int(summary["source_rows"])),
        "clean rows": (clean_rows, int(summary["clean_rows"])),
        "raw revenue": (raw_revenue, Decimal(summary["source_line_revenue_total"])),
        "clean revenue": (clean_revenue, Decimal(summary["clean_line_revenue_total"])),
        "raw rows by sheet": (dict(raw_sheets), dict(summary["rows_by_sheet"])),
        "clean rows by sheet": (dict(clean_sheets), {
            name: int(count) - int(summary["cross_sheet_duplicates_by_sheet"].get(name, 0))
            for name, count in summary["rows_by_sheet"].items()
        }),
    }
    failures = [f"{label}: {actual!s} != {wanted!s}" for label, (actual, wanted) in checks.items() if actual != wanted]
    if failures:
        raise RuntimeError("CSV validation failed:\n" + "\n".join(failures))
    sample_invoices, sample_rows = validate_sample(CLEAN_CSV, SAMPLE_CSV, int(summary["sample_invoices_per_month"]))
    print(f"CSV validation passed: raw={raw_rows:,}, clean={clean_rows:,}, sample={sample_rows:,} rows across {sample_invoices:,} whole invoices")
    print(f"Revenue totals match: raw GBP {raw_revenue}, clean GBP {clean_revenue}")
    if args.mysql:
        validate_mysql(summary)


if __name__ == "__main__":
    main()
