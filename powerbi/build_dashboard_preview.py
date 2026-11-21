"""Build a static, reproducible dashboard PDF from verified SQL result CSVs."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "docs" / "query_results"
OUTPUT = ROOT / "powerbi" / "retail_dashboard_preview.pdf"
PAGE_W, PAGE_H = landscape(A4)
NAVY = colors.HexColor("#111A35")
PANEL = colors.HexColor("#182443")
PANEL2 = colors.HexColor("#202F55")
CYAN = colors.HexColor("#40D6E7")
PURPLE = colors.HexColor("#A879FF")
WHITE = colors.HexColor("#F4F7FF")
MUTED = colors.HexColor("#AEBBD4")
GRID = colors.HexColor("#344365")
GREEN = colors.HexColor("#61D6A8")


def rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def money(value: float) -> str:
    return f"GBP {value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def text(c: canvas.Canvas, x: float, y: float, value: str, size: int = 10,
         color: colors.Color = WHITE, font: str = "Helvetica") -> None:
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, value)


def page_base(c: canvas.Canvas, page: int, subtitle: str) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    text(c, 34, PAGE_H - 36, "ONLINE RETAIL  /  SALES & CUSTOMER ANALYSIS", 9, CYAN, "Helvetica-Bold")
    text(c, 34, PAGE_H - 63, subtitle, 22, WHITE, "Helvetica-Bold")
    c.setStrokeColor(GRID)
    c.line(34, PAGE_H - 75, PAGE_W - 34, PAGE_H - 75)
    c.setStrokeColor(GRID)
    c.line(34, 27, PAGE_W - 34, 27)
    text(c, 34, 13, "Source: verified MySQL query CSVs in docs/query_results/  |  Currency: GBP", 7, MUTED)
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_W - 34, 13, f"{page} / 2")


def panel(c: canvas.Canvas, x: float, y: float, w: float, h: float,
          title: str, accent: colors.Color = CYAN) -> None:
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=0)
    text(c, x + 14, y + h - 22, title, 10, accent, "Helvetica-Bold")


def draw_line_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float,
                    monthly: list[dict[str, str]]) -> None:
    panel(c, x, y, w, h, "MONTHLY GROSS MERCHANDISE REVENUE", PURPLE)
    px, py, pw, ph = x + 40, y + 35, w - 58, h - 75
    values = [float(r["gross_merchandise_revenue"]) for r in monthly]
    dates = [r["month_start"] for r in monthly]
    low, high = 0, max(values) * 1.12
    c.setStrokeColor(GRID)
    for i in range(4):
        gy = py + i * ph / 3
        c.line(px, gy, px + pw, gy)
        text(c, x + 6, gy - 3, f"{max(values) * i / 3 / 1000:.0f}k", 7, MUTED)
    points = []
    for i, value in enumerate(values):
        xx = px + (pw * i / max(len(values) - 1, 1))
        yy = py + ph * (value - low) / (high - low)
        points.append((xx, yy))
    c.setStrokeColor(CYAN)
    c.setLineWidth(2)
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    c.drawPath(path)
    for i, (xx, yy) in enumerate(points):
        c.setFillColor(PURPLE if i == len(points) - 1 else CYAN)
        c.circle(xx, yy, 2.8, fill=1, stroke=0)
    for i in sorted({0, len(dates)//3, 2*len(dates)//3, len(dates)-1}):
        text(c, points[i][0] - 12, py - 14, dates[i][:7], 7, MUTED)
    text(c, x + 14, y + 10, f"Purple point = latest full month ({dates[-1][:7]})", 7, MUTED)


def draw_country_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float,
                       countries: list[dict[str, str]]) -> None:
    panel(c, x, y, w, h, "TOP COUNTRIES BY REVENUE")
    subset = sorted(countries, key=lambda r: float(r["revenue"]), reverse=True)[:8]
    max_value = max(float(r["revenue"]) for r in subset)
    top_y = y + h - 49
    gap = (h - 67) / len(subset)
    for i, row in enumerate(subset):
        yy = top_y - i * gap
        label = row["country"][:18]
        text(c, x + 13, yy, label, 7, WHITE)
        bx = x + 105
        bw = w - 175
        c.setFillColor(PANEL2)
        c.roundRect(bx, yy - 2, bw, 8, 4, fill=1, stroke=0)
        c.setFillColor(CYAN if i == 0 else PURPLE)
        c.roundRect(bx, yy - 2, bw * float(row["revenue"]) / max_value, 8, 4, fill=1, stroke=0)
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawRightString(x + w - 12, yy, money(float(row["revenue"])))


def draw_product_table(c: canvas.Canvas, x: float, y: float, w: float, h: float,
                       products: list[dict[str, str]]) -> None:
    panel(c, x, y, w, h, "TOP PRODUCTS BY REVENUE", PURPLE)
    top = y + h - 40
    text(c, x + 14, top, "#", 7, MUTED, "Helvetica-Bold")
    text(c, x + 43, top, "Product", 7, MUTED, "Helvetica-Bold")
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(MUTED)
    c.drawRightString(x + w - 126, top, "Revenue")
    c.drawRightString(x + w - 18, top, "Units")
    subset = sorted(products, key=lambda r: float(r["revenue"]), reverse=True)[:5]
    for i, r in enumerate(subset):
        yy = top - 18 - i * 15
        c.setStrokeColor(GRID)
        c.line(x + 12, yy - 5, x + w - 12, yy - 5)
        text(c, x + 14, yy, str(i + 1).zfill(2), 8, CYAN, "Helvetica-Bold")
        desc = r["product_description"].strip()
        text(c, x + 43, yy, (desc[:54] + ("..." if len(desc) > 54 else "")), 8)
        c.setFont("Helvetica", 8)
        c.setFillColor(WHITE)
        c.drawRightString(x + w - 126, yy, money(float(r["revenue"])))
        c.drawRightString(x + w - 18, yy, f"{float(r['units_sold']):,.0f}")


def draw_rfm(c: canvas.Canvas, x: float, y: float, w: float, h: float,
             rfm: list[dict[str, str]]) -> None:
    panel(c, x, y, w, h, "RFM CUSTOMER SEGMENTS", PURPLE)
    top = y + h - 43
    headers = [(x+14,"Segment"),(x+170,"Customers"),(x+280,"Revenue"),(x+415,"Avg recency"),(x+550,"Avg orders")]
    for xx, label in headers:
        text(c, xx, top, label, 8, MUTED, "Helvetica-Bold")
    max_customers = max(int(float(r["customers"])) for r in rfm)
    for i, r in enumerate(rfm):
        yy = top - 22 - i * 17
        c.setStrokeColor(GRID)
        c.line(x + 12, yy - 7, x + w - 12, yy - 7)
        text(c, x + 14, yy, r["segment"], 9, WHITE, "Helvetica-Bold")
        text(c, x + 170, yy, f"{int(float(r['customers'])):,}", 9)
        c.setFillColor(PANEL2)
        c.roundRect(x + 219, yy, 41, 7, 3, fill=1, stroke=0)
        c.setFillColor(CYAN if i < 2 else PURPLE)
        c.roundRect(x + 219, yy, 41 * int(float(r["customers"])) / max_customers, 7, 3, fill=1, stroke=0)
        text(c, x + 280, yy, money(float(r["revenue"])), 9)
        text(c, x + 415, yy, f"{float(r['average_recency_days']):.0f} days", 9)
        text(c, x + 550, yy, f"{float(r['average_orders']):.2f}", 9)


def draw_cohort(c: canvas.Canvas, x: float, y: float, w: float, h: float,
                cohort: list[dict[str, str]]) -> None:
    panel(c, x, y, w, h, "COHORT RETENTION  /  SHARE OF COHORT ACTIVE IN MONTH N")
    # Recent 16 cohorts keep the grid readable while preserving the SQL's exact values.
    def cohort_date(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d")

    cohort_names = sorted({r["cohort_month"] for r in cohort}, key=cohort_date)[-16:]
    subset = [r for r in cohort if r["cohort_month"] in cohort_names and int(r["month_number"]) <= 12]
    lookup = {(r["cohort_month"], int(r["month_number"])): r for r in subset}
    left = x + 74
    top = y + h - 48
    cell_w = min(42, (w - 100) / 13)
    row_h = min(10.3, (h - 68) / len(cohort_names))
    for m in range(13):
        text(c, left + m * cell_w + 6, top + 7, str(m), 7, MUTED, "Helvetica-Bold")
    for i, month in enumerate(cohort_names):
        yy = top - 7 - (i + 1) * row_h
        text(c, x + 14, yy + 2, cohort_date(month).strftime("%Y-%m"), 7, WHITE)
        for m in range(13):
            xx = left + m * cell_w
            r = lookup.get((month, m))
            if not r:
                continue
            value = float(r["retention_rate"])
            shade = max(0.12, min(1.0, value))
            c.setFillColor(colors.Color(0.25 * shade, 0.84 * shade, 0.90 * shade))
            c.rect(xx, yy, cell_w - 2, row_h - 1, fill=1, stroke=0)
            if row_h >= 9:
                c.setFillColor(NAVY)
                c.setFont("Helvetica", 5)
                marker = "*" if r.get("is_partial_activity_month") == "1" or r.get("is_partial_cohort_month") == "1" else ""
                c.drawCentredString(xx + (cell_w - 2) / 2, yy + 1.7, f"{value:.0%}{marker}")
    text(c, x + 14, y + 11, "Month 0 is the cohort month. * marks a partial cohort or activity month per the SQL output.", 7, MUTED)


def build() -> None:
    kpi = rows("01_core_kpis.csv")[0]
    monthly = rows("02_monthly_revenue_mom.csv")
    products = rows("04_top_products.csv")
    countries = rows("05_country_revenue.csv")
    rfm = rows("10_rfm_segments.csv")
    cohorts = rows("11_cohort_retention.csv")
    repeats = rows("08_repeat_customer_rate.csv")[0]

    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(A4), pageCompression=1)
    c.setTitle("Online Retail Sales and Customer Analysis - Dashboard Preview")
    c.setAuthor("Online Retail Sales and Customer Analysis")

    page_base(c, 1, "Executive overview")
    cards = [
        ("GROSS MERCHANDISE", money(float(kpi["gross_merchandise_revenue"]))),
        ("NET REVENUE", money(float(kpi["net_revenue"]))),
        ("ORDERS", f"{int(float(kpi['orders'])):,}"),
        ("REGISTERED CUSTOMERS", f"{int(float(kpi['registered_customers'])):,}"),
        ("CANCELLATION RATE", pct(float(kpi["cancellation_rate"]))),
    ]
    gap, card_y, card_h = 9, PAGE_H - 158, 58
    card_w = (PAGE_W - 68 - gap * 4) / 5
    for i, (label, value) in enumerate(cards):
        xx = 34 + i * (card_w + gap)
        c.setFillColor(PANEL)
        c.roundRect(xx, card_y, card_w, card_h, 9, fill=1, stroke=0)
        text(c, xx + 12, card_y + card_h - 18, label, 7, MUTED, "Helvetica-Bold")
        text(c, xx + 12, card_y + 17, value, 13 if len(value) < 17 else 11, CYAN if i != 4 else PURPLE, "Helvetica-Bold")

    draw_line_chart(c, 34, 194, 465, 191, monthly)
    draw_country_chart(c, 510, 194, PAGE_W - 544, 191, countries)
    draw_product_table(c, 34, 53, PAGE_W - 68, 126, products)
    text(c, 34, 36, f"Registered-customer repeat rate: {pct(float(repeats['repeat_customer_rate']))}  |  Query-defined gross/net revenue excludes non-product rows.", 7, MUTED)
    c.showPage()

    page_base(c, 2, "Customer segments & retention")
    draw_rfm(c, 34, 344, PAGE_W - 68, 143, rfm)
    draw_cohort(c, 34, 48, PAGE_W - 68, 281, cohorts)
    text(c, 34, 37, "RFM segments and cohort retention are SQL outputs; they are descriptive, window-bound summaries, not predictive models.", 7, MUTED)
    c.save()


if __name__ == "__main__":
    build()
