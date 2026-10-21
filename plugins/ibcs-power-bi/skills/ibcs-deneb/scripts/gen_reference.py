#!/usr/bin/env python3
"""Regenerate references/templates.md from each template's usermeta.ibcs (fields, knobs, notes).

    python3 -I scripts/gen_reference.py [--check] [--out PATH]      (path relative to this skill)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent



def cell(text: str) -> str:
    """A Markdown table cell: a literal | would end the cell."""
    return str(text).replace("|", "\\|")

def build() -> str:
    specs = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted((ROOT / "assets" / "templates").glob("*.v[lg].json"))]
    out = ["# Template reference", "",
           "Generated from each template's `usermeta.ibcs` by `scripts/gen_reference.py`; edit the templates, not this file.",
           "Paths are relative to this skill's directory.", "",
           "## Contents"]
    # template names are already lower-case slugs, so they double as heading anchors
    out += [f"- [{s['usermeta']['ibcs']['template']}](#{s['usermeta']['ibcs']['template']})" for s in specs]
    out += [""]
    for s in specs:
        m = s["usermeta"]["ibcs"]
        out += [f"## {m['template']}", "", s.get("description", ""), "",
                f"- IBCS: {', '.join(m['cards'])}", f"- Sample data: `assets/sample-data/{m['sampleData']}`", "",
                "| Field | Meaning |", "|---|---|"]
        out += [f"| `{k}` | {cell(v)} |" for k, v in m["fields"].items()]
        if m.get("requiredFields"):
            any_of = m.get("requiredAnyOf") or []
            out += ["", "Required fields: " + ", ".join(f"`{f}`" for f in m["requiredFields"])
                    + (", and one of " + " or ".join(" + ".join(f"`{f}`" for f in g) for g in any_of) if any_of else "")
                    + ("; the scenario fields that " + ", ".join(sk) + " name" if (sk := [
                        x["name"] for x in s.get("params", []) if x.get("name") in ("refScenario", "minuend", "triangleScenario")
                        and any(c in m["fields"] for c in ("AC", "FC", "PY", "PL", "BU"))]) else "")
                    + "; the others may stay unbound."]
        knobs = [x for x in s.get("params", []) if x["name"] in m.get("knobs", []) and "expr" not in x]
        if knobs:
            out += ["", "| Knob | Default | Meaning |", "|---|---|---|"]
            out += [f"| `{k['name']}` | `{json.dumps(k['value'], ensure_ascii=False)}` | {cell(k.get('description', ''))} |"
                    for k in knobs]
        if m.get("notes"):
            out += ["", f"Notes: {m['notes']}"]
        if m.get("layout"):
            lay = m["layout"]
            pads = lambda t: "; ".join(f"{k} {' + '.join(f'`{n}`' for n in t[k])}"
                                       for k in ("padHigh", "padLow", "padLowIfNegative") if t.get(k))
            out += ["", f"Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = {lay['valueAxis']}; "
                    f"fixed {lay['fixedPx']} px"
                    + (f" ({lay['fixedPxNoCategoryLabels']} px without category labels)" if "fixedPxNoCategoryLabels" in lay else "")
                    + (f", plus the category labels: {lay['plusCategoryLabels']}" if "plusCategoryLabels" in lay else "")
                    + ". Tiers: " + "; ".join(f"{t['id']} = {t['range']}" + (f" ({pads(t)})" if pads(t) else "")
                                               for t in lay["tiers"])
                    + f". {lay['rule']}."]
        out += [""]
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 when the file is out of date; write nothing")
    ap.add_argument("--out", default=str(ROOT / "references" / "templates.md"), help="file to write or check")
    a = ap.parse_args()
    target = Path(a.out)
    body = build()
    if a.check:
        sys.exit(0 if target.exists() and target.read_text(encoding="utf-8") == body else 1)
    target.write_text(body, encoding="utf-8")
    print(f"wrote {target}")
