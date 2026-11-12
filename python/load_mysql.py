"""Load the raw and deduplicated CSVs into MySQL using PyMySQL."""

from __future__ import annotations

import csv
import getpass
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql


ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "processed" / "online_retail_raw.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "online_retail_clean.csv"
CHUNK_SIZE = 5_000

RAW_COLUMNS = (
    "invoice", "stock_code", "description", "quantity", "invoice_date",
    "price", "customer_id", "country",
)
CLEAN_COLUMNS = (*RAW_COLUMNS, "is_cancellation", "is_guest", "is_non_product", "line_revenue")

RAW_SCHEMA = """
CREATE TABLE online_retail_raw_staging (
    row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    invoice VARCHAR(24) NULL,
    stock_code VARCHAR(40) NULL,
    description TEXT NULL,
    quantity INT NULL,
    invoice_date DATETIME NULL,
    price DECIMAL(18, 6) NULL,
    customer_id BIGINT NULL,
    country VARCHAR(100) NULL,
    INDEX ix_raw_invoice (invoice),
    INDEX ix_raw_customer (customer_id),
    INDEX ix_raw_date (invoice_date),
    INDEX ix_raw_product (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

CLEAN_SCHEMA = """
CREATE TABLE online_retail_clean_staging (
    row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    invoice VARCHAR(24) NULL,
    stock_code VARCHAR(40) NULL,
    description TEXT NULL,
    quantity INT NULL,
    invoice_date DATETIME NULL,
    price DECIMAL(18, 6) NULL,
    customer_id BIGINT NULL,
    country VARCHAR(100) NULL,
    is_cancellation TINYINT(1) NOT NULL,
    is_guest TINYINT(1) NOT NULL,
    is_non_product TINYINT(1) NOT NULL,
    line_revenue DECIMAL(24, 6) NULL,
    INDEX ix_clean_invoice (invoice),
    INDEX ix_clean_customer (customer_id),
    INDEX ix_clean_date (invoice_date),
    INDEX ix_clean_product (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


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
    return (*raw_values(record), int(record["is_cancellation"]), int(record["is_guest"]), int(record["is_non_product"]), parse_decimal(record["line_revenue"]))


def insert_csv(connection: Any, filename: Path, table: str, columns: tuple[str, ...], transform: Any) -> int:
    names = ", ".join(f"`{column}`" for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    statement = f"INSERT INTO `{table}` ({names}) VALUES ({placeholders})"
    count = 0
    batch: list[tuple[Any, ...]] = []
    cursor = connection.cursor()
    try:
        with filename.open("r", encoding="utf-8-sig", newline="") as stream:
            for record in csv.DictReader(stream):
                batch.append(transform(record))
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
    return count


def main() -> None:
    if not RAW_CSV.exists() or not CLEAN_CSV.exists():
        raise FileNotFoundError("Run python/prepare_data.py before loading the tables.")

    username = input("MySQL user [root]: ").strip() or "root"
    password = getpass.getpass("MySQL password (input is hidden): ")
    host = input("MySQL host [127.0.0.1]: ").strip() or "127.0.0.1"
    port = int(input("MySQL port [3306]: ").strip() or "3306")
    connection_settings = dict(host=host, port=port, user=username, password=password,
                               charset="utf8mb4", autocommit=False)

    server_connection = pymysql.connect(**connection_settings)
    try:
        with server_connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS online_retail CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
        server_connection.commit()
    finally:
        server_connection.close()

    connection = pymysql.connect(**connection_settings, database="online_retail")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'online_retail' AND table_name IN ('online_retail_raw', 'online_retail_clean')")
            existing = [row[0] for row in cursor.fetchall()]
            if existing:
                raise RuntimeError(
                    "Target table(s) already exist: " + ", ".join(existing) + ". "
                    "Inspect them before loading again; this script never drops or truncates tables."
                )
            # These two staging tables are owned by this loader. Removing them
            # makes a rerun safe after an interrupted staging load.
            cursor.execute("DROP TABLE IF EXISTS online_retail_raw_staging, online_retail_clean_staging")
            cursor.execute(RAW_SCHEMA)
            cursor.execute(CLEAN_SCHEMA)
        connection.commit()

        raw_count = insert_csv(connection, RAW_CSV, "online_retail_raw_staging", RAW_COLUMNS, raw_values)
        clean_count = insert_csv(connection, CLEAN_CSV, "online_retail_clean_staging", CLEAN_COLUMNS, clean_values)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM online_retail_raw_staging")
            stored_raw = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM online_retail_clean_staging")
            stored_clean = cursor.fetchone()[0]
        if (raw_count, clean_count) != (stored_raw, stored_clean):
            raise RuntimeError(
                f"Staging row counts do not match: raw {raw_count:,}/{stored_raw:,}, "
                f"clean {clean_count:,}/{stored_clean:,}."
            )
        with connection.cursor() as cursor:
            cursor.execute("RENAME TABLE online_retail_raw_staging TO online_retail_raw, online_retail_clean_staging TO online_retail_clean")
        connection.commit()
        print(f"Verified and published MySQL row counts: raw={stored_raw:,}, clean={stored_clean:,}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
