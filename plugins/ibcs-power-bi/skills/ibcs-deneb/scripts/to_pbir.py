#!/usr/bin/env python3
"""Put an IBCS Deneb template into a PBIR visual.json (new visual or update in place).

    # new Deneb visual on a page
    python3 -I to_pbir.py assets/templates/column-two-tier-variance.vl.json \
        --visual "MyReport.Report/definition/pages/<page>/visuals/<name>/visual.json" --new \
        --field "Period=col:Date[Month Short]" --field "AC=m:Measures[AC]" \
        --field "FC=m:Measures[FC]" --field "PY=m:Measures[PY]" \
        --param refScenario=PY --pos 16,96,620,300 [--report MyReport.Report/definition/report.json]

    # update the spec/config of an existing Deneb visual (field bindings untouched)
    python3 -I to_pbir.py assets/templates/pin-relative-variance.vl.json --visual .../visual.json

    # sort by a bound field, a static visual-level filter, a visual title
    ... --sort Period:asc --filter "col:Date[Year]=2026" --filter "col:Company[Code]=A1,B2" \
        --title "Revenue by month"

--sort <template field>[:asc|desc]: the field must be bound (--field, or already in the visual);
sort a month name by its number through the model's "sort by column". Deneb keeps the query order.
--filter <col>:<Table>[<Column>]=<v1>,<v2>…: a basic (In) filter in the visual's filterConfig;
values are typed like PBIR literals: 2026 -> 2026L, 1.5 -> 1.5D, true/false, anything else a text.
Text values containing a comma cannot be written with this option. For "last closed month" style
defaults use a flag column in the model (see ibcs-power-bi §4) and filter on it here.
Not written: Top N and measure (advanced) filters. Top N in a live-connected report = bind measures
that return BLANK beyond rank N (e.g. VAR r = RANKX ( ALLSELECTED ( 'Customer'[Customer] ), [AC] )
RETURN IF ( r <= 25, [AC] )): rows without values drop out. An "Others" remainder row needs a
category member that only the model can add (calculated table / disconnected category).
--title "text" shows the visual title with that text (theme font); --title "" hides it.
--prepend-transform FILE: a JSON list of Vega-Lite transforms put before the template's own
transforms, e.g. a fold that turns one row of separate measures (PY, Price, Volume, ..., AC) into
the template's rows (Category, Kind, Value). Fields the prepended transforms read (fold, field,
groupby, datum[...] in expressions) count as
bound fields; see references/templates.md "Bridges from separate measures".

Field syntax: <template field>=<col|m>:<Table>[<Column or Measure>]. The template field name
becomes the projection's displayName, which is the name Deneb exposes to the spec, so the spec
never needs editing for your model's names.

Report-level measures (definition/reportExtensions.json) must be bound with
"SourceRef": {"Schema": "extension", "Entity": …}; without it the service looks the name up in
the model and the visual fails with Missing_References. The script finds reportExtensions.json
next to the visual's pages folder (or --extensions PATH) and marks those measures itself.

Encoding (PBIR literals): the spec and config are minified JSON inside a single-quoted literal;
single quotes inside are doubled ('') as PBIR/DAX string literals require. Desktop reads them
back to the original spec. --param values are written into the spec's params before encoding.

Run the token sync first (sync_tokens.py) so the spec carries the current token values.
Validate afterwards: `jq empty visual.json`, then the pbip-validator agent where available.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"
CONTAINER_SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
                    "visualContainer/2.4.0/schema.json")
FIELD = re.compile(r"^(?P<name>[^=]+)=(?P<kind>col|m):(?P<table>[^\[]+)\[(?P<prop>[^\]]+)\]$")
FILTER = re.compile(r"^col:(?P<table>[^\[]+)\[(?P<prop>[^\]]+)\]=(?P<values>.*)$")


def literal(s: str) -> dict:
    return {"expr": {"Literal": {"Value": "'" + s.replace("'", "''") + "'"}}}


def lit_bool(b: bool) -> dict:
    return {"expr": {"Literal": {"Value": "true" if b else "false"}}}


def parse_value(v: str):
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def report_measures(path: Path | None) -> set[tuple[str, str]]:
    """(entity, measure) pairs defined in reportExtensions.json; empty when there is none."""
    if not path or not path.exists():
        return set()
    ext = json.loads(path.read_text(encoding="utf-8"))
    return {(e["name"], m["name"]) for e in ext.get("entities", []) for m in e.get("measures", [])}


def find_extensions(visual: Path) -> Path | None:
    """definition/reportExtensions.json for definition/pages/<page>/visuals/<v>/visual.json."""
    for parent in visual.resolve().parents:
        if parent.name == "definition" and (parent / "pages").is_dir():
            return parent / "reportExtensions.json"
    return None


def projection(spec_field: str, kind: str, table: str, prop: str, extension: bool = False) -> dict:
    source = {"Schema": "extension", "Entity": table} if extension else {"Entity": table}
    ref = {"Expression": {"SourceRef": source}, "Property": prop}
    p = {
        "field": {"Column": ref} if kind == "col" else {"Measure": ref},
        "queryRef": f"{table}.{prop}",
        "nativeQueryRef": prop,
    }
    if spec_field != prop:
        p["displayName"] = spec_field
    return p


def pbir_literal(v: str) -> str:
    """A filter value as a PBIR literal: 2026 -> 2026L, 1.5 -> 1.5D, true/false, else 'text'."""
    v = v.strip()
    if re.fullmatch(r"-?\d+", v):
        return f"{v}L"
    if re.fullmatch(r"-?\d+\.\d+", v):
        return f"{v}D"
    if v in ("true", "false"):
        return v
    return "'" + v.replace("'", "''") + "'"


def basic_filter(spec: str, n: int) -> dict:
    m = FILTER.match(spec.strip())
    if not m:
        raise ValueError(f"bad --filter {spec!r} (expected col:Table[Column]=v1,v2)")
    table, prop = m["table"].strip().strip("'"), m["prop"]
    alias = "f"
    col = {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}
    return {
        "name": f"filter{n}",
        "field": col,
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
                "Values": [[{"Literal": {"Value": pbir_literal(v)}}] for v in m["values"].split(",")],
            }}}],
        },
    }


def sort_definition(arg: str, projections: list) -> dict:
    name, _, direction = arg.partition(":")
    direction = {"": "Ascending", "asc": "Ascending", "desc": "Descending"}.get(direction.lower())
    if direction is None:
        raise ValueError(f"bad --sort {arg!r} (expected <field>[:asc|desc])")
    hit = [p for p in projections if p.get("displayName", p.get("nativeQueryRef")) == name]
    if not hit:
        names = [p.get("displayName", p.get("nativeQueryRef")) for p in projections]
        raise ValueError(f"--sort {name}: not a bound field ({names})")
    return {"sort": [{"field": hit[0]["field"], "direction": direction}], "isDefaultSort": True}


def build_objects(spec: dict, config: dict, provider: str, tooltips: bool, selection: bool) -> dict:
    return {
        "vega": [{
            "properties": {
                "jsonSpec": literal(json.dumps(spec, ensure_ascii=False, separators=(",", ":"))),
                "jsonConfig": literal(json.dumps(config, ensure_ascii=False, separators=(",", ":"))),
                "provider": literal(provider),
                "renderMode": literal("svg"),  # pattern fills (FC hatch) need the SVG renderer
                "enableTooltips": lit_bool(tooltips),
                "enableContextMenu": lit_bool(True),
                "enableSelection": lit_bool(selection),
                "enableHighlight": lit_bool(False),
            }
        }]
    }


def apply_extras(visual: dict, a) -> None:
    """--sort, --filter, --title on a new or existing visual container."""
    v = visual["visual"]
    if a.sort:
        projections = v.get("query", {}).get("queryState", {}).get("dataset", {}).get("projections", [])
        v.setdefault("query", {})["sortDefinition"] = sort_definition(a.sort, projections)
    if a.filter:
        existing = visual.setdefault("filterConfig", {}).setdefault("filters", [])
        start = len(existing)
        existing += [basic_filter(f, start + i + 1) for i, f in enumerate(a.filter)]
    if a.title is not None:
        props = {"show": lit_bool(bool(a.title))}
        if a.title:
            props["text"] = literal(a.title)
        v.setdefault("visualContainerObjects", {})["title"] = [{"properties": props}]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("--visual", required=True, help="visual.json to create or update")
    ap.add_argument("--new", action="store_true", help="create a new visual container")
    ap.add_argument("--field", action="append", default=[], help="Template=col|m:Table[Name]")
    ap.add_argument("--param", action="append", default=[], help="knob=value (JSON or text)")
    ap.add_argument("--config", default=str(HERE.parent / "assets" / "config" / "deneb-config.json"))
    ap.add_argument("--pos", help="x,y,width,height (new visuals; default 16,96,600,300)")
    ap.add_argument("--z", type=int, default=0)
    ap.add_argument("--name", help="visual name (new visuals; default random 20-hex)")
    ap.add_argument("--selection", action="store_true", help="enable Deneb cross-filtering (__selected__)")
    ap.add_argument("--no-tooltips", action="store_true")
    ap.add_argument("--report", help="report.json: register Deneb in publicCustomVisuals")
    ap.add_argument("--sort", help="<template field>[:asc|desc]: sort the visual's query by a bound field")
    ap.add_argument("--filter", action="append", default=[],
                    help="col:Table[Column]=v1,v2: static basic filter on the visual (repeatable)")
    ap.add_argument("--title", help="visual title text; '' hides the title")
    ap.add_argument("--extensions", help="reportExtensions.json (default: found from --visual)")
    ap.add_argument("--prepend-transform", help="JSON file: list of transforms put before the template's")
    a = ap.parse_args()

    tpath = Path(a.template)
    spec = json.loads(tpath.read_text(encoding="utf-8"))
    prepended: set[str] = set()
    if a.prepend_transform:
        pre = json.loads(Path(a.prepend_transform).read_text(encoding="utf-8"))
        if not isinstance(pre, list) or not all(isinstance(t, dict) for t in pre):
            print("--prepend-transform must hold a JSON list of transform objects", file=sys.stderr)
            return 2
        if "transform" not in spec:
            print("this template has no top-level transform list to prepend to", file=sys.stderr)
            return 2
        spec["transform"] = pre + spec["transform"]
        text = json.dumps(pre)
        prepended.update(a or b for a, b in re.findall(r"datum\[\s*\\?['\"]([^'\"\\]+)\\?['\"]\s*\]|datum\.([A-Za-z_]\w*)", text))
        for t in pre:
            prepended.update(f for f in t.get("fold", []) + t.get("groupby", []) if isinstance(f, str))
            if isinstance(t.get("field"), str):
                prepended.add(t["field"])
    provider = "vega" if tpath.name.endswith(".vg.json") else "vegaLite"
    params = spec.get("signals" if provider == "vega" else "params", [])
    for kv in a.param:
        k, _, v = kv.partition("=")
        hit = [p for p in params if p.get("name") == k]
        if not hit:
            print(f"unknown param {k}; template knobs: {spec.get('usermeta', {}).get('ibcs', {}).get('knobs')}",
                  file=sys.stderr)
            return 2
        if "expr" in hit[0]:
            print(f"param {k} is computed (expr: {hit[0]['expr']}); it cannot be set with --param. "
                  f"Change its inputs instead (template knobs: "
                  f"{spec.get('usermeta', {}).get('ibcs', {}).get('knobs')})", file=sys.stderr)
            return 2
        hit[0]["value"] = parse_value(v)
    unsynced = [p["name"] for p in params if p.get("name", "").startswith("ibcs") and p.get("value") is None
                and "expr" not in p]
    if unsynced:
        print(f"token params without values (run sync_tokens.py): {unsynced}", file=sys.stderr)
        return 2
    config = json.loads(Path(a.config).read_text(encoding="utf-8"))
    objects = build_objects(spec, config, provider, not a.no_tooltips, a.selection)

    vpath = Path(a.visual)
    if a.new:
        if vpath.exists():
            print(f"{vpath} exists; drop --new to update it", file=sys.stderr)
            return 2
        fields = []
        ext = report_measures(Path(a.extensions) if a.extensions else find_extensions(vpath))
        declared = set(spec.get("usermeta", {}).get("ibcs", {}).get("fields", {}))
        for f in a.field:
            m = FIELD.match(f.strip())
            if not m:
                print(f"bad --field {f!r}", file=sys.stderr)
                return 2
            if declared and m["name"] not in declared and m["name"] not in prepended:
                print(f"warning: {m['name']} is not a documented field of this template ({sorted(declared)})",
                      file=sys.stderr)
            table = m["table"].strip().strip("'")
            fields.append(projection(m["name"], m["kind"], table, m["prop"],
                                     m["kind"] == "m" and (table, m["prop"]) in ext))
        x, y, w, h = [float(v) for v in (a.pos or "16,96,600,300").split(",")]
        name = a.name or secrets.token_hex(10)
        visual = {
            "$schema": CONTAINER_SCHEMA,
            "name": name,
            "position": {"x": x, "y": y, "z": a.z, "width": w, "height": h, "tabOrder": a.z},
            "visual": {
                "visualType": DENEB,
                "query": {"queryState": {"dataset": {"projections": fields}}},
                "objects": objects,
                "drillFilterOtherVisuals": True,
            },
        }
        vpath.parent.mkdir(parents=True, exist_ok=True)
    else:
        visual = json.loads(vpath.read_text(encoding="utf-8"))
        if visual.get("visual", {}).get("visualType") != DENEB:
            print(f"{vpath} is not a Deneb visual", file=sys.stderr)
            return 2
        visual["visual"].setdefault("objects", {})["vega"] = objects["vega"]
    try:
        apply_extras(visual, a)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    vpath.write_text(json.dumps(visual, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {vpath}")

    if a.report:
        rpath = Path(a.report)
        report = json.loads(rpath.read_text(encoding="utf-8"))
        pcv = report.setdefault("publicCustomVisuals", [])
        if DENEB not in pcv:
            pcv.append(DENEB)
            rpath.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"registered Deneb in {rpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
