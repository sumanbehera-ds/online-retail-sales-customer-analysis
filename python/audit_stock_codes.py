"""Build an aggregate stock-code review file from the clean CSV."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from prepare_data import CLEAN_CSV, is_non_product_code


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "stock_code_audit.csv"
STANDARD_CODE = re.compile(r"^[0-9]{5}[A-Za-z]*$")


def main() -> None:
    counts: Counter[str] = Counter()
    revenue: Counter[str] = Counter()
    descriptions: dict[str, Counter[str]] = defaultdict(Counter)
    with CLEAN_CSV.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            code = (row.get("StockCode") or "").strip()
            if not code:
                continue
            counts[code] += 1
            if row.get("line_revenue"):
                revenue[code] += Decimal(row["line_revenue"])
            description = (row.get("Description") or "").strip()
            if description:
                descriptions[code][description] += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("stock_code", "row_count", "line_revenue_gbp", "is_non_product", "review_status", "most_common_description"))
        for code in sorted(counts, key=lambda value: (-counts[value], value)):
            flagged = is_non_product_code(code)
            status = "configured non-product" if flagged else (
                "standard product-code shape" if STANDARD_CODE.fullmatch(code) else "review candidate; not auto-excluded"
            )
            description = descriptions[code].most_common(1)[0][0] if descriptions[code] else ""
            writer.writerow((code, counts[code], format(revenue[code], "f"), int(flagged), status, description))
    candidate_count = sum(
        1 for code in counts if not is_non_product_code(code) and not STANDARD_CODE.fullmatch(code)
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(counts):,} stock codes; {candidate_count:,} nonstandard unflagged codes are review candidates, not automatic exclusions.")


if __name__ == "__main__":
    main()
