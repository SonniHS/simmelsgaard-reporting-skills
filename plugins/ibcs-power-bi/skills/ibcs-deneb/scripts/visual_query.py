#!/usr/bin/env python3
"""Write the DAX query a Deneb visual sends, for live-data previews (render-previews.mjs --visual).

    python3 -I visual_query.py <…/visuals/<v>/visual.json> [--extensions <…/reportExtensions.json>]
        [--sort-by "Month Short=Month No"] [--filter "'Date'[Year] = 2026"]
        [--filter "'Customer'[Country] IN {\"DE\", \"AT\"}"] [--body out.json]

It reads the visual's dataset projections, its basic (In) visual filters and its sort, and prints
an EVALUATE SUMMARIZECOLUMNS over the columns with the measures named as the visual binds them.
Every report-level measure of reportExtensions.json (found next to the pages folder, or
--extensions) is defined with DEFINE MEASURE, so the query runs against the published model
without the report. --sort-by maps a category column to the model's sort-by column
("Month Short=Month No": adds 'Date'[Month No] to the query and orders by it), as the service does.
--filter adds page or slicer context the visual does not hold itself (repeatable): the visual's
query alone ignores slicers and page filters. `'Table'[Column] = value` and
`'Table'[Column] IN {v1, v2}` become TREATAS ( { … }, 'Table'[Column] ), a filter table, as the
service sends slicer context; a boolean `col = value` argument inside SUMMARIZECOLUMNS works for a
number column but fails on a text column ("a single value for column … cannot be determined").
Write literals in the column's type (2026 for a number, "Name" for text). Anything else is passed
through unchanged and must be a filter TABLE expression, e.g. FILTER ( ALL ( 'Date'[Month] ),
'Date'[Month] <= "2026-06" ) or KEEPFILTERS ( TREATAS ( … ) ).
--body writes the executeQueries request body instead of printing the query; run it with
    fab api -A powerbi -X post "groups/<ws>/datasets/<model>/executeQueries" -i out.json > rows.json
and pass rows.json to render-previews.mjs --visual <visual.json>=rows.json. Nothing is sent by
this script.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def ref(field: dict) -> tuple[str, bool]:
    """('Table'[Column], True) or ([Measure], False)."""
    if "Column" in field:
        c = field["Column"]
        return f"'{c['Expression']['SourceRef']['Entity']}'[{c['Property']}]", True
    if "Measure" in field:
        return f"[{field['Measure']['Property']}]", False
    sys.exit(f"unsupported field (only columns and measures): {json.dumps(field)[:200]}")


def literal(v: dict) -> str:
    """PBIR literal -> DAX literal: 2026L -> 2026, 1.5D -> 1.5, 'text' -> "text", true/false."""
    raw = v["Literal"]["Value"]
    if raw in ("true", "false"):
        return raw.upper() + "()"
    if raw[-1:] in ("L", "D") and raw[:-1].replace(".", "", 1).lstrip("-").isdigit():
        return raw[:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return '"' + raw[1:-1].replace("''", "'").replace('"', '""') + '"'
    return raw


def visual_filters(vis: dict) -> list[str]:
    out = []
    for f in (vis.get("filterConfig") or {}).get("filters") or []:
        cond = ((f.get("filter") or {}).get("Where") or [{}])[0].get("Condition", {})
        if "In" not in cond or "Column" not in f.get("field", {}):
            print(f"note: filter {f.get('name', '?')} is not a basic In filter; add it with --filter", file=sys.stderr)
            continue
        col, _ = ref(f["field"])
        vals = [literal(row[0]) for row in cond["In"]["Values"]]
        out.append(f"TREATAS ( {{ {', '.join(vals)} }}, {col} )")
    return out


_SIMPLE = re.compile(r"^\s*((?:'(?:[^']|'')+'|[A-Za-z_][\w ]*?)\s*\[[^\]]+\])\s*(=|IN\b)\s*(.+?)\s*$",
                     re.IGNORECASE | re.DOTALL)


def filter_table(expr: str) -> str:
    """`col = v` / `col IN {v1, v2}` -> TREATAS ( { … }, col ); anything else unchanged (a filter table).

    A boolean `'T'[Text] = "x"` argument in SUMMARIZECOLUMNS fails on text columns; TREATAS works
    for every column type and is what the service sends for slicer selections."""
    m = _SIMPLE.match(expr)
    if not m:
        return expr.strip()
    col, op, rhs = m.group(1).strip(), m.group(2).upper(), m.group(3)
    if "&&" in rhs or "||" in rhs:   # a compound condition: leave it to the caller
        return expr.strip()
    if op == "IN":
        if not (rhs.startswith("{") and rhs.endswith("}")):
            return expr.strip()
        rhs = rhs[1:-1].strip()
    return f"TREATAS ( {{ {rhs} }}, {col} )"


def report_measures(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    ext = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for ent in ext.get("entities") or []:
        for m in ent.get("measures") or []:
            expr = m.get("expression") or ""
            if isinstance(expr, list):
                expr = "\n".join(expr)
            out.append(f"MEASURE '{ent['name']}'[{m['name']}] =\n    {expr}")
    return out


def build(vis: dict, ext: Path | None, sort_by: dict[str, str], extra: list[str]) -> str:
    v = vis["visual"]
    projs = v["query"]["queryState"].get("dataset", {}).get("projections") or \
        [p for role in v["query"]["queryState"].values() for p in role.get("projections", [])]
    cols, meas = [], []
    for p in projs:
        r, is_col = ref(p["field"])
        if is_col:
            cols.append(r)
        else:
            # the displayName is the template field name Deneb exposes (unique per visual, even when one
            # model measure is bound to two roles); render-previews keeps such names as they are
            meas.append((p.get("displayName") or p.get("nativeQueryRef") or p["field"]["Measure"]["Property"], r))
    for c in list(cols):
        prop = c.split("[", 1)[1].rstrip("]")
        if prop in sort_by:
            cols.append(c.split("[", 1)[0] + f"[{sort_by[prop]}]")
    order = ""
    sort = (v["query"].get("sortDefinition") or {}).get("sort") or []
    if sort:
        r, is_col = ref(sort[0]["field"])
        prop = r.split("[", 1)[1].rstrip("]")
        if is_col and prop in sort_by:
            r = r.split("[", 1)[0] + f"[{sort_by[prop]}]"
        if is_col and r not in cols:   # ORDER BY needs the column in the result
            cols.append(r)
        if not is_col:   # a measure is ordered by its output column name
            name = next((n for n, mr in meas if mr == r), prop)
            r = f"[{name}]"
        order = f"\nORDER BY {r} {'DESC' if sort[0].get('direction') == 'Descending' else 'ASC'}"
    body = ",\n    ".join(f'"{n}", {r}' for n, r in meas)
    filters = visual_filters(vis) + [filter_table(f) for f in extra]
    if cols:
        query = "EVALUATE SUMMARIZECOLUMNS (\n    " + ",\n    ".join(cols + filters + [body]) + "\n)" + order
    elif filters:
        query = f"EVALUATE CALCULATETABLE ( ROW ( {body} ), {', '.join(filters)} )"
    else:
        query = f"EVALUATE ROW ( {body} )"
    defs = report_measures(ext)
    return ("DEFINE\n" + "\n".join(defs) + "\n" if defs else "") + query


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("visual")
    ap.add_argument("--extensions", help="reportExtensions.json (default: found next to the pages folder)")
    ap.add_argument("--sort-by", action="append", default=[], metavar="COL=SORTCOL")
    ap.add_argument("--filter", action="append", default=[], metavar="DAX",
                    help="'T'[Col] = value, 'T'[Col] IN {v1, v2} (both become TREATAS) or a DAX filter table")
    ap.add_argument("--body", help="write the executeQueries request body to this file")
    a = ap.parse_args()
    vpath = Path(a.visual)
    vis = json.loads(vpath.read_text(encoding="utf-8"))
    ext = Path(a.extensions) if a.extensions else next(
        (p / "reportExtensions.json" for p in vpath.resolve().parents if (p / "reportExtensions.json").exists()), None)
    sort_by = dict(s.split("=", 1) for s in a.sort_by)
    query = build(vis, ext, sort_by, a.filter)
    if a.body:
        Path(a.body).write_text(json.dumps({"queries": [{"query": query}],
                                            "serializerSettings": {"includeNulls": True}}, ensure_ascii=False),
                                encoding="utf-8")
        print(f"wrote {a.body}")
    else:
        print(query)
    return 0


if __name__ == "__main__":
    sys.exit(main())
