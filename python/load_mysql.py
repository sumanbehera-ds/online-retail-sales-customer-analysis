"""Load CSV extracts into MySQL, validate counts/totals, and publish safely."""

from __future__ import annotations

import argparse
import csv
import getpass
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import pymysql


ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "processed" / "online_retail_raw.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "online_retail_clean.csv"
REPORT_JSON = ROOT / "docs" / "data_quality_report.json"
SCHEMA_FILE = ROOT / "sql" / "00_schema.sql"
CHUNK_SIZE = 5_000

RAW_COLUMNS = (
    "source_sheet", "invoice", "stock_code", "description", "quantity",
    "invoice_date", "price", "customer_id", "country",
)
CLEAN_COLUMNS = (*RAW_COLUMNS, "is_cancellation", "is_guest", "is_non_product", "line_revenue")


def parse_datetime(value: str) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def parse_decimal(value: str) -> Decimal | None:
    return Decimal(value) if value else None


def parse_customer_id(value: str) -> int | None:
    if not value:
        return None
    number = Decimal(value)
    if number != number.to_integral_value():
        raise ValueError(f"Customer ID is not an integer: {value!r}")
    return int(number)


def raw_values(record: dict[str, str]) -> tuple[Any, ...]:
    return (
        record["source_sheet"] or None,
        record["Invoice"] or None,
        record["StockCode"] or None,
        record["Description"] or None,
        int(record["Quantity"]) if record["Quantity"] else None,
        parse_datetime(record["InvoiceDate"]),
        parse_decimal(record["Price"]),
        parse_customer_id(record["Customer ID"]),
        record["Country"] or None,
    )


def clean_values(record: dict[str, str]) -> tuple[Any, ...]:
    return (
        *raw_values(record),
        int(record["is_cancellation"]),
        int(record["is_guest"]),
        int(record["is_non_product"]),
        parse_decimal(record["line_revenue"]),
    )


def schema_statements(table_raw: str, table_clean: str) -> tuple[list[str], list[str]]:
    source = SCHEMA_FILE.read_text(encoding="utf-8")
    rendered = source.replace("{{RAW_TABLE}}", f"`{table_raw}`").replace(
        "{{CLEAN_TABLE}}", f"`{table_clean}`"
    )
    table_ddl: list[str] = []
    index_ddl: list[str] = []
    for statement in rendered.split(";"):
        statement = "\n".join(line for line in statement.splitlines() if not line.lstrip().startswith("--")).strip()
        if not statement:
            continue
        if statement.upper().startswith("CREATE TABLE"):
            table_ddl.append(statement)
        elif statement.upper().startswith("CREATE INDEX"):
            index_ddl.append(statement)
        else:
            raise ValueError(f"Unsupported statement in {SCHEMA_FILE.name}: {statement[:60]!r}")
    if len(table_ddl) != 2 or len(index_ddl) != 8:
        raise ValueError(f"Expected 2 CREATE TABLE and 8 CREATE INDEX statements in {SCHEMA_FILE}")
    return table_ddl, index_ddl


def row_revenue(values: tuple[Any, ...], clean: bool) -> Decimal:
    if clean:
        return values[-1] or Decimal("0")
    quantity, price = values[4], values[6]
    return Decimal(quantity) * price if quantity is not None and price is not None else Decimal("0")


def insert_csv(
    connection: Any,
    filename: Path,
    table: str,
    columns: tuple[str, ...],
    transform: Callable[[dict[str, str]], tuple[Any, ...]],
    clean: bool,
) -> tuple[int, Decimal]:
    names = ", ".join(f"`{column}`" for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    statement = f"INSERT INTO `{table}` ({names}) VALUES ({placeholders})"
    count = 0
    revenue_total = Decimal("0")
    batch: list[tuple[Any, ...]] = []
    cursor = connection.cursor()
    try:
        with filename.open("r", encoding="utf-8-sig", newline="") as stream:
            for record in csv.DictReader(stream):
                values = transform(record)
                batch.append(values)
                revenue_total += row_revenue(values, clean)
                if len(batch) == CHUNK_SIZE:
                    cursor.executemany(statement, batch)
                    connection.commit()
                    count += len(batch)
                    batch.clear()
                    print(f"Loaded {count:,} rows into {table}", flush=True)
        if batch:
            cursor.executemany(statement, batch)
            connection.commit()
            count += len(batch)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
    return count, revenue_total


def validate_staging(connection: Any, raw_inserted: int, clean_inserted: int,
                     raw_csv_revenue: Decimal, clean_csv_revenue: Decimal,
                     expected: dict[str, Any]) -> tuple[int, int]:
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity * price), 0) FROM online_retail_raw_staging")
        stored_raw, stored_raw_revenue = cursor.fetchone()
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(line_revenue), 0) FROM online_retail_clean_staging")
        stored_clean, stored_clean_revenue = cursor.fetchone()
    finally:
        cursor.close()

    expected_raw = int(expected["source_rows"])
    expected_clean = int(expected["clean_rows"])
    checks = {
        "raw CSV rows vs report": (raw_inserted, expected_raw),
        "clean CSV rows vs report": (clean_inserted, expected_clean),
        "raw CSV rows vs MySQL": (raw_inserted, stored_raw),
        "clean CSV rows vs MySQL": (clean_inserted, stored_clean),
        "raw CSV revenue vs MySQL": (raw_csv_revenue, Decimal(stored_raw_revenue)),
        "clean CSV revenue vs report": (clean_csv_revenue, Decimal(expected["clean_line_revenue_total"])),
        "clean CSV revenue vs MySQL": (clean_csv_revenue, Decimal(stored_clean_revenue)),
    }
    mismatches = [f"{label}: {left!s} != {right!s}" for label, (left, right) in checks.items() if left != right]
    if mismatches:
        raise RuntimeError("Validation failed; staging tables were not published:\n" + "\n".join(mismatches))
    return int(stored_raw), int(stored_clean)


def publish_tables(connection: Any, replace_existing: bool, existing: set[str]) -> list[str]:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    pairs = [
        ("online_retail_raw_staging", "online_retail_raw"),
        ("online_retail_clean_staging", "online_retail_clean"),
    ]
    clauses = []
    backups = []
    for staging, final in pairs:
        if final in existing:
            if not replace_existing:
                raise RuntimeError(f"Target table {final!r} already exists. Re-run with --replace to replace it safely.")
            backup = f"{final}_previous_{timestamp}"
            clauses.append(f"`{final}` TO `{backup}`")
            backups.append(backup)
        clauses.append(f"`{staging}` TO `{final}`")
    cursor = connection.cursor()
    try:
        cursor.execute("RENAME TABLE " + ", ".join(clauses))
        connection.commit()
        if backups:
            cursor.execute("DROP TABLE " + ", ".join(f"`{name}`" for name in backups))
            connection.commit()
    finally:
        cursor.close()
    return backups


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="replace existing final tables after staging checks pass")
    args = parser.parse_args()

    for path in (RAW_CSV, CLEAN_CSV, REPORT_JSON, SCHEMA_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required file is missing: {path.relative_to(ROOT)}")
    expected = json.loads(REPORT_JSON.read_text(encoding="utf-8"))

    username = input("MySQL user [root]: ").strip() or "root"
    password = getpass.getpass("MySQL password (input is hidden): ")
    host = input("MySQL host [127.0.0.1]: ").strip() or "127.0.0.1"
    port = int(input("MySQL port [3306]: ").strip() or "3306")
    settings = dict(host=host, port=port, user=username, password=password, charset="utf8mb4", autocommit=False)

    server = pymysql.connect(**settings)
    try:
        with server.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS online_retail CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
        server.commit()
    finally:
        server.close()

    connection = pymysql.connect(**settings, database="online_retail")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='online_retail' AND table_name IN ('online_retail_raw','online_retail_clean')")
            existing = {row[0] for row in cursor.fetchall()}
        if existing and not args.replace:
            raise RuntimeError("Final table(s) already exist: " + ", ".join(sorted(existing)) + ". Use --replace after reviewing them.")
        if existing - {"online_retail_raw", "online_retail_clean"}:
            raise RuntimeError("Unexpected final table state; inspect the database before loading.")

        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS online_retail_raw_staging, online_retail_clean_staging")
            table_ddl, index_ddl = schema_statements("online_retail_raw_staging", "online_retail_clean_staging")
            for statement in table_ddl:
                cursor.execute(statement)
        connection.commit()

        raw_count, raw_revenue = insert_csv(connection, RAW_CSV, "online_retail_raw_staging", RAW_COLUMNS, raw_values, clean=False)
        clean_count, clean_revenue = insert_csv(connection, CLEAN_CSV, "online_retail_clean_staging", CLEAN_COLUMNS, clean_values, clean=True)
        stored_raw, stored_clean = validate_staging(connection, raw_count, clean_count, raw_revenue, clean_revenue, expected)

        with connection.cursor() as cursor:
            _, index_ddl = schema_statements("online_retail_raw_staging", "online_retail_clean_staging")
            for statement in index_ddl:
                cursor.execute(statement)
        connection.commit()

        publish_tables(connection, args.replace, existing)
        print(f"Validated and published MySQL row counts: raw={stored_raw:,}, clean={stored_clean:,}")
        print(f"Validated revenue totals: raw GBP {raw_revenue}, clean GBP {clean_revenue}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
