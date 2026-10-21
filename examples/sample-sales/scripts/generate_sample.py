#!/usr/bin/env python3
"""Generate the deterministic data of the Sample Sales model.

One source of truth for three outputs, so they can never drift apart:
  ../SampleSales.SemanticModel/definition/tables/Sales.tmdl   the fact rows as a DATATABLE
  ../csv/*.csv                                               the same rows, for a Lakehouse load
  ../expected_results.csv                                    numbers a correct model must reproduce

Generic sample data: five regions in EUR, AC from 2025-01 to the last closed month 2026-09, a
budget for 2025 and 2026, and one forecast (9+3) for 2026. PY is not stored: the model derives
it from AC.

Run:  python3 -I examples/sample-sales/scripts/generate_sample.py [--check]
Only the standard library is used. Output is byte-for-byte reproducible.
"""
from __future__ import annotations

import csv
import io
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "SampleSales.SemanticModel" / "definition" / "tables"
CSV_DIR = ROOT / "csv"

YEARS = (2025, 2026)
LAST_CLOSED = (2026, 9)  # AC exists up to and including this month
REPORT_MONTH = "2026-09"

# key, name, sort, is remainder, monthly revenue base (EUR), AC growth 2026, BU uplift 2026, cost-of-sales ratio
REGIONS = [
    (1, "North", 1, False, 1_250_000, 1.07, 1.06, 0.58),
    (2, "West", 2, False, 950_000, 0.96, 1.04, 0.61),
    (3, "South", 3, False, 780_000, 1.05, 1.05, 0.60),
    (4, "East", 4, False, 420_000, 1.03, 1.08, 0.63),
    (5, "Other", 5, True, 60_000, 0.80, 1.00, 0.66),
]
# key, type, version code, version label, is latest FC, FC actual months, sort, notation
SCENARIOS = [
    (1, "AC", "AC", "Actual", False, 0, 1, "solid"),
    (2, "BU", "BU2025", "Budget 2025", False, 0, 2, "outlined"),
    (3, "BU", "BU2026", "Budget 2026", False, 0, 3, "outlined"),
    (4, "FC", "FC2026-9+3", "Forecast 2026 (9+3)", True, 9, 4, "hatched"),
]
SEASON = [0.92, 0.88, 1.00, 0.97, 1.02, 1.05, 0.93, 0.86, 1.04, 1.06, 1.08, 1.19]
OPEX_SHARE = 0.24       # operating costs per month as a share of the region's revenue base
ORDER_VALUE = 820       # average order value in EUR

C2 = Decimal("0.01")


def money(x: float) -> Decimal:
    return Decimal(repr(x)).quantize(C2, rounding=ROUND_HALF_UP)


def noise(*seed: int) -> float:
    """Deterministic ±4 % wobble."""
    h = 0
    for s in seed:
        h = (h * 31 + s * 17 + 7) % 9973
    return ((h % 9) - 4) / 100


def closed(year: int, month: int) -> bool:
    return (year, month) <= LAST_CLOSED


def rows():
    """Fact rows: (period date, region key, scenario key, revenue, cost of sales, operating costs, orders)."""
    out = []
    ac: dict[tuple[int, int, int], tuple] = {}
    for key, _, _, _, base, growth, bu_up, cos in REGIONS:
        for year in YEARS:
            for m in range(1, 13):
                season = SEASON[m - 1]
                trend = growth if year == 2026 else 1.0
                if closed(year, m):
                    rev = base * season * trend * (1 + noise(key, year, m))
                    vals = (money(rev), money(rev * (cos + noise(key, m, year) / 4)),
                            money(base * OPEX_SHARE * (1.05 if year == 2026 else 1.0) * (1 + noise(m, key, year) / 2)),
                            round(rev / ORDER_VALUE))
                    ac[(key, year, m)] = vals
                    out.append((f"{year}-{m:02d}-01", key, 1, *vals))
                bu_scale = 1.03 if year == 2025 else bu_up
                rev = base * season * bu_scale
                out.append((f"{year}-{m:02d}-01", key, 2 if year == 2025 else 3,
                            money(rev), money(rev * cos), money(base * OPEX_SHARE * (1.02 if year == 2025 else 1.03)),
                            round(rev / ORDER_VALUE)))
                if year == 2026:  # FC 9+3: months 1..9 copied from AC, 10..12 projected
                    if m <= 9:
                        vals = ac[(key, year, m)]
                    else:
                        rev = base * season * growth * 0.99
                        vals = (money(rev), money(rev * cos), money(base * OPEX_SHARE * 1.05), round(rev / ORDER_VALUE))
                    out.append((f"{year}-{m:02d}-01", key, 4, *vals))
    return sorted(out, key=lambda r: (r[2], r[0], r[1]))


# --------------------------------------------------------------------------- expected results
def expected(fact):
    """Key figures for the report month: Period, YTD and FY; by month; by region (YTD)."""
    def total(field, scen, months, regions=None):
        idx = {"Revenue": 3, "Cost of Sales": 4, "Operating Costs": 5, "Orders": 6}
        s = Decimal(0)
        found = False
        for row in fact:
            d, rk, sk = row[:3]
            if (int(d[:4]), int(d[5:7])) in months and sk in scen and (regions is None or rk in regions):
                s += Decimal(row[idx[field]])
                found = True
        return s if found else None

    def ac_fc(field, months, regions=None):
        a = total(field, {1}, {mm for mm in months if closed(*mm)}, regions)
        f = total(field, {4}, {mm for mm in months if not closed(*mm)}, regions)
        return None if a is None and f is None else (a or 0) + (f or 0)

    def kpi(measure, months, scen_fn):
        if measure == "Gross Profit":
            r, c = scen_fn("Revenue", months), scen_fn("Cost of Sales", months)
            return None if r is None else r - c
        if measure == "Gross Margin %":
            r, c = scen_fn("Revenue", months), scen_fn("Cost of Sales", months)
            return None if not r else (r - c) / r
        return scen_fn(measure, months)

    out = []
    y, mth = LAST_CLOSED
    views = {
        "Period": {(y, mth)},
        "YTD": {(y, k) for k in range(1, mth + 1)},
        "FY": {(y, k) for k in range(1, 13)},
    }
    measures = ["Revenue", "Gross Profit", "Gross Margin %", "Operating Costs", "Orders"]
    for view, months in views.items():
        py_months = {(yy - 1, mm) for yy, mm in months}
        for meas in measures:
            minuend = kpi(meas, months, lambda f, ms: ac_fc(f, ms))
            py = kpi(meas, py_months, lambda f, ms: total(f, {1}, ms))
            bu = kpi(meas, months, lambda f, ms: total(f, {2, 3}, ms))
            out += [(view, meas, "", "AC+FC" if view == "FY" else "AC", minuend), (view, meas, "", "PY", py), (view, meas, "", "BU", bu)]
            for code, ref in (("PY", py), ("BU", bu)):
                if meas == "Gross Margin %":
                    out.append((view, meas, "", f"Δ{code}", (minuend - ref) * 100))  # pp
                else:
                    out.append((view, meas, "", f"Δ{code}", minuend - ref))
                    out.append((view, meas, "", f"Δ{code}%", (minuend - ref) / ref if ref and ref > 0 else None))
    for m in range(1, 13):
        ms = {(y, m)}
        out += [("Month", "Revenue", f"{y}-{m:02d}", "AC+FC", ac_fc("Revenue", ms)),
                ("Month", "Revenue", f"{y}-{m:02d}", "BU", total("Revenue", {3}, ms)),
                ("Month", "Revenue", f"{y}-{m:02d}", "PY", total("Revenue", {1}, {(y - 1, m)}))]
    for key, name, *_ in REGIONS:
        ms = views["YTD"]
        a, b = ac_fc("Revenue", ms, {key}), total("Revenue", {3}, ms, {key})
        out += [("YTD by region", "Revenue", name, "AC", a), ("YTD by region", "Revenue", name, "BU", b),
                ("YTD by region", "Revenue", name, "ΔBU", a - b), ("YTD by region", "Revenue", name, "ΔBU%", (a - b) / b)]
    return out


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):  # amounts to the cent, ratios and pp to six decimals
        return str(v.quantize(C2 if abs(v) >= 100 else Decimal("0.000001"), rounding=ROUND_HALF_UP))
    return str(v)


# --------------------------------------------------------------------------- writers
def sales_tmdl(fact) -> str:
    body = ",\n".join(
        f'\t\t\t\t\t\t{{ "{d}", {rk}, {sk}, {rev}, {cos}, {opex}, {orders} }}' for d, rk, sk, rev, cos, opex, orders in fact
    )
    cols = [
        ("PeriodDate", "dateTime", "yyyy-mm-dd", True, "First day of the month; the fact is at month grain."),
        ("RegionKey", "int64", "0", True, None),
        ("ScenarioKey", "int64", "0", True, None),
        ("Revenue", "decimal", "#,0", True, None),
        ("CostOfSales", "decimal", "#,0", True, None),
        ("OperatingCosts", "decimal", "#,0", True, None),
        ("Orders", "int64", "#,0", True, None),
    ]
    out = ["/// Sales fact at month grain: AC to the last closed month, BU per year, FC versions. Every column is hidden: use the measures.",
           "/// GENERATED by scripts/generate_sample.py. Do not edit; change the script and regenerate.",
           "table Sales", ""]
    for name, typ, fmt_, hidden, desc in cols:
        if desc:
            out.append(f"\t/// {desc}")
        out += [f"\tcolumn {name}", f"\t\tdataType: {typ}"]
        if hidden:
            out.append("\t\tisHidden")
        out += [f"\t\tformatString: {fmt_}", "\t\tsummarizeBy: none", "\t\tisNameInferred", f"\t\tsourceColumn: [{name}]", ""]
    out += ["\tpartition Sales = calculated", "\t\tmode: import", "\t\tsource =", "\t\t\t\tDATATABLE (",
            '\t\t\t\t\t"PeriodDate", DATETIME,', '\t\t\t\t\t"RegionKey", INTEGER,', '\t\t\t\t\t"ScenarioKey", INTEGER,',
            '\t\t\t\t\t"Revenue", CURRENCY,', '\t\t\t\t\t"CostOfSales", CURRENCY,', '\t\t\t\t\t"OperatingCosts", CURRENCY,',
            '\t\t\t\t\t"Orders", INTEGER,', "\t\t\t\t\t{", body, "\t\t\t\t\t}", "\t\t\t\t)", ""]
    return "\n".join(out)


def dim_tmdl(name, desc, cols, rows_) -> str:
    """A small dimension as a calculated DATATABLE; cols: (name, dataType, DAX type, hidden, sortBy, description)."""
    lit = lambda v: f'"{v}"' if isinstance(v, str) else ("TRUE" if v is True else "FALSE" if v is False else str(v))
    out = [f"/// {desc}", "/// GENERATED by scripts/generate_sample.py. Do not edit; change the script and regenerate.", f"table {name}", ""]
    for c, typ, _, hidden, sort_by, cdesc in cols:
        if cdesc:
            out.append(f"\t/// {cdesc}")
        out += [f"\tcolumn {c}", f"\t\tdataType: {typ}"]
        if hidden:
            out.append("\t\tisHidden")
        if typ == "int64":
            out.append("\t\tformatString: 0")
        if typ == "boolean":
            out.append('\t\tformatString: """TRUE"";""TRUE"";""FALSE"""')
        out += ["\t\tsummarizeBy: none", "\t\tisNameInferred", f"\t\tsourceColumn: [{c}]"]
        if sort_by:
            out.append(f"\t\tsortByColumn: {sort_by}")
        out.append("")
    header = ",\n".join(f'\t\t\t\t\t"{c}", {dax},' if False else f'\t\t\t\t\t"{c}", {dax}' for c, _, dax, *_ in cols)
    body = ",\n".join("\t\t\t\t\t\t{ " + ", ".join(lit(v) for v in r) + " }" for r in rows_)
    out += [f"\tpartition {name} = calculated", "\t\tmode: import", "\t\tsource =", "\t\t\t\tDATATABLE (",
            header + ",", "\t\t\t\t\t{", body, "\t\t\t\t\t}", "\t\t\t\t)", ""]
    return "\n".join(out)


def csv_text(header, data) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(data)
    return buf.getvalue()


def outputs() -> dict[Path, str]:
    fact = rows()
    regions = [(k, n, s, str(rem).upper()) for k, n, s, rem, *_ in REGIONS]
    scenarios = [(k, t, c, l, str(lf).upper(), n, s, nt) for k, t, c, l, lf, n, s, nt in SCENARIOS]
    region_cols = [
        ("RegionKey", "int64", "INTEGER", True, None, None),
        ("Region", "string", "STRING", False, "SortOrder", None),
        ("SortOrder", "int64", "INTEGER", True, None, None),
        ("IsRemainder", "boolean", "BOOLEAN", True, None, "TRUE for the remainder (Other): sorted last, excluded from rankings."),
    ]
    scenario_cols = [
        ("ScenarioKey", "int64", "INTEGER", True, None, None),
        ("ScenarioType", "string", "STRING", False, None, "IBCS scenario code: AC, BU or FC."),
        ("VersionCode", "string", "STRING", False, "SortOrder", None),
        ("VersionLabel", "string", "STRING", False, "SortOrder", None),
        ("IsLatestFC", "boolean", "BOOLEAN", True, None, None),
        ("FcActualMonths", "int64", "INTEGER", False, None, "n of an n+m forecast: months 1..n were copied from AC."),
        ("SortOrder", "int64", "INTEGER", True, None, None),
        ("IbcsNotation", "string", "STRING", False, None, "IBCS fill notation (solid, outlined, hatched) for custom visuals and SVG measures."),
    ]
    region_rows = [(k, n, s, rem) for k, n, s, rem, *_ in REGIONS]
    return {
        TABLES / "Region.tmdl": dim_tmdl("Region", "Sales regions; Other is the remainder and sorts last.", region_cols, region_rows),
        TABLES / "Scenario.tmdl": dim_tmdl("Scenario", "One row per scenario version. PY is not stored: it is AC shifted in time. Use the Scenario Analysis calculation group, do not slice this table.", scenario_cols, SCENARIOS),
        TABLES / "Sales.tmdl": sales_tmdl(fact),
        CSV_DIR / "Sales.csv": csv_text(["PeriodDate", "RegionKey", "ScenarioKey", "Revenue", "CostOfSales", "OperatingCosts", "Orders"], fact),
        CSV_DIR / "Region.csv": csv_text(["RegionKey", "Region", "SortOrder", "IsRemainder"], regions),
        CSV_DIR / "Scenario.csv": csv_text(["ScenarioKey", "ScenarioType", "VersionCode", "VersionLabel", "IsLatestFC", "FcActualMonths", "SortOrder", "IbcsNotation"], scenarios),
        ROOT / "expected_results.csv": csv_text(["View", "Measure", "Member", "Scenario", "Value"], [(*r[:4], fmt(r[4])) for r in expected(fact)]),
    }


def main() -> int:
    check = "--check" in sys.argv[1:]
    stale = []
    for path, text in outputs().items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(path.relative_to(ROOT))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if stale:
        print("out of date, run scripts/generate_sample.py:", *stale, sep="\n  ")
        return 1
    print("checked" if check else "written", len(outputs()), "files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
