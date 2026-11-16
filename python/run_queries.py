"""Run the numbered SQL files and save result CSVs plus query previews."""

from __future__ import annotations

import csv
import getpass
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pymysql


ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
RESULTS_DIR = ROOT / "docs" / "query_results"


def show_value(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return "" if value is None else str(value)


def main() -> None:
    username = input("MySQL user [root]: ").strip() or "root"
    password = getpass.getpass("MySQL password (input is hidden): ")
    host = input("MySQL host [127.0.0.1]: ").strip() or "127.0.0.1"
    port_text = input("MySQL port [3306]: ").strip() or "3306"
    connection = pymysql.connect(
        user=username, password=password, host=host, port=int(port_text),
        database="online_retail", charset="utf8mb4", autocommit=True,
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        for sql_file in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
            if sql_file.name == "00_schema.sql":
                continue
            source = sql_file.read_text(encoding="utf-8")
            statement = "\n".join(
                line for line in source.splitlines()
                if not line.lstrip().startswith("--")
            ).strip()
            if not statement:
                continue
            with connection.cursor() as cursor:
                cursor.execute(statement)
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

            output_file = RESULTS_DIR / f"{sql_file.stem}.csv"
            with output_file.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(columns)
                writer.writerows([[show_value(value) for value in row] for row in rows])

            preview = [dict(zip(columns, [show_value(value) for value in row])) for row in rows[:3]]
            result_comment = (
                f"-- Result: {len(rows)} rows returned; first rows: "
                + json.dumps(preview, ensure_ascii=True, separators=(",", ":"))
            )
            lines = [line for line in source.splitlines() if not line.lstrip().startswith("-- Result:")]
            lines.append(result_comment)
            sql_file.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            print(f"{sql_file.name}: {len(rows):,} rows -> {output_file.relative_to(ROOT)}", flush=True)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
