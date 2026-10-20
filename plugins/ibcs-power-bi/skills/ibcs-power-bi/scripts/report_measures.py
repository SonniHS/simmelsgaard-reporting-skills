#!/usr/bin/env python3
"""Keep report-level measures (definition/reportExtensions.json) loadable in the Power BI service.

    python3 -I report_measures.py <Report folder> --check     # list problems, exit 1 if any
    python3 -I report_measures.py <Report folder> --fix       # write the fixes, then re-check
        [--model <SemanticModel>/definition/tables]           # model measures for `references`

What the service needs (found in an end-to-end test, as of 2026-10):
  1. Every binding of a report measure in a visual (projections, sort, filters, conditional
     formatting) carries "SourceRef": {"Schema": "extension", "Entity": …}. Without it the service
     resolves the name in the model and the visual fails with "Something's wrong with one or more
     fields" (Missing_References). --fix adds it.
  2. Each report measure lists the measures it uses in "references": report measures with
     "schema": "extension", model measures with their table (Desktop writes this; the service fix
     above did not need it, but write it so the file matches what Desktop saves). --fix writes it;
     model measures are recognised only with --model (else they are left out).
  3. No "hidden": true on a report measure (every visual using it fails in the service). --fix
     removes the flag.
  4. No "active": true on a projection except in a slicer (on a tableEx column it collapsed every
     measure column to 1 px and added a blank row). --fix removes it.
Nothing is published; only files under the given Report folder change.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ACTIVE_OK = {"slicer", "advancedSlicerVisual"}  # Desktop writes "active" on slicer fields


def model_measures(tables: Path | None) -> dict[str, str]:
    """measure name -> table, from TMDL table files."""
    found: dict[str, str] = {}
    for f in sorted(tables.glob("*.tmdl")) if tables else []:
        for name in re.findall(r"^\s*measure\s+'?([^'=\n]+?)'?\s*=", f.read_text(encoding="utf-8"), re.M):
            found.setdefault(name.strip(), f.stem)
    return found


DAX_NOISE = re.compile(r'"(?:[^"]|"")*"|--[^\n]*|//[^\n]*|/\*.*?\*/', re.S)  # strings, comments
DAX_REF = re.compile(r"(?:'((?:[^']|'')+)'|([A-Za-z_][\w]*))?\[([^\]]+)\]")


def references(expr: str, own: str, ext: dict[str, str], model: dict[str, str]) -> list[dict]:
    """Measures a DAX expression uses: [Name], 'Table'[Name] or Table[Name] where Name is a report
    measure (ext: name -> entity) or a model measure (model: name -> table). Strings and comments
    are skipped; a qualified name counts only when its table matches."""
    out, seen = [], set()
    for quoted, bare, name in DAX_REF.findall(DAX_NOISE.sub(" ", expr)):
        table = (quoted or bare).replace("''", "'")
        if name in seen or name == own:
            continue
        if name in ext and (not table or table == ext[name]):
            out.append({"schema": "extension", "entity": ext[name], "name": name})
        elif name in model and (not table or table == model[name]):
            out.append({"entity": model[name], "name": name})
        else:
            continue
        seen.add(name)
    return out


def walk_bindings(node, ext_pairs: set[tuple[str, str]], fix: bool, problems: list, where: str) -> None:
    if isinstance(node, dict):
        m = node.get("Measure")
        if isinstance(m, dict):
            src = m.get("Expression", {}).get("SourceRef", {})
            if (src.get("Entity"), m.get("Property")) in ext_pairs and src.get("Schema") != "extension":
                problems.append(f"{where}: [{m.get('Property')}] bound without \"Schema\": \"extension\"")
                if fix:
                    m["Expression"]["SourceRef"] = {**src, "Schema": "extension"}
        for v in node.values():
            walk_bindings(v, ext_pairs, fix, problems, where)
    elif isinstance(node, list):
        for v in node:
            walk_bindings(v, ext_pairs, fix, problems, where)


def run(report: Path, model: dict[str, str], fix: bool) -> list[str]:
    problems: list[str] = []
    definition = report / "definition"
    ext_path = definition / "reportExtensions.json"
    ext = json.loads(ext_path.read_text(encoding="utf-8")) if ext_path.exists() else {"entities": []}
    pairs = {(e["name"], m["name"]) for e in ext["entities"] for m in e.get("measures", [])}
    changed_ext = False
    ext_index = {m["name"]: e["name"] for e in ext["entities"] for m in e.get("measures", [])}
    for e in ext["entities"]:
        for m in e.get("measures", []):
            if m.get("hidden"):
                problems.append(f"reportExtensions.json: [{m['name']}] is hidden")
                if fix:
                    del m["hidden"]
                    changed_ext = True
            want = references(m.get("expression", ""), m["name"], ext_index, model)
            have = (m.get("references") or {}).get("measures")
            if not model and have is not None:
                # without the model, keep the model references already there; check the rest
                want = [r for r in have if r.get("schema") != "extension"] + want
            if have is None or sorted(map(json.dumps, have)) != sorted(map(json.dumps, want)):
                hint = "" if model else " (without --model, model measures are not added)"
                problems.append(f"reportExtensions.json: [{m['name']}] references missing or stale{hint}")
                if fix:
                    m["references"] = {"measures": want}
                    changed_ext = True
    if fix and changed_ext:
        ext_path.write_text(json.dumps(ext, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for f in sorted(definition.glob("pages/**/*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        where = str(f.relative_to(definition))
        before = len(problems)
        walk_bindings(doc, pairs, fix, problems, where)
        vis = doc.get("visual", {})
        if vis.get("visualType") not in ACTIVE_OK:
            for well in vis.get("query", {}).get("queryState", {}).values():
                for p in well.get("projections", []):
                    if p.get("active"):
                        problems.append(f"{where}: \"active\": true on {p.get('queryRef')} ({vis.get('visualType')})")
                        if fix:
                            del p["active"]
        if fix and len(problems) > before:
            f.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="the <name>.Report folder")
    ap.add_argument("--model", help="<model>.SemanticModel/definition/tables (TMDL), for model measure references")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    report = Path(a.report)
    if not (report / "definition").is_dir():
        print(f"{report}: no definition/ folder (pass the .Report folder)", file=sys.stderr)
        return 2
    model = model_measures(Path(a.model) if a.model else None)
    problems = run(report, model, a.fix)
    for p in problems:
        print(("fixed: " if a.fix else "") + p)
    if a.fix:
        left = run(report, model, False)
        for p in left:
            print(f"left: {p}")
        return 1 if left else 0
    print(f"{len(problems)} problem(s)" if problems else "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
