#!/usr/bin/env python3
"""Scaffold a PBIP report project that is live-connected to a published semantic model.

    # REST / fab import form (only the semantic model id)
    python3 -I new_pbip.py --out ./powerbi --name "Sales report" --semantic-model-id <model-id>

    # Power BI Desktop form (workspace + model name; the id is added when given)
    python3 -I new_pbip.py --out ./powerbi --name "Sales report" \
        --workspace "<workspace name>" --model "<semantic model name>" [--semantic-model-id <model-id>]

    # options
        --page-display "Key figures" --page-name keyFigures --canvas 1280x1120 --display-option FitToWidth
        --theme ./theme/ibcs-pbi-theme.json     (default: the bundled IBCS theme of this skill)
        --logical-id <guid>                     (default: a new random one; keep it stable afterwards)
        --force                                 (overwrite generated files of an existing project)

Writes (nothing else, never publishes):
    <out>/<name>.pbip
    <out>/<name>.Report/.platform
    <out>/<name>.Report/definition.pbir                       byConnection (or --by-path)
    <out>/<name>.Report/definition/version.json
    <out>/<name>.Report/definition/report.json                IBCS theme registered as a custom theme
    <out>/<name>.Report/definition/reportExtensions.json      empty: add report-level measures here
    <out>/<name>.Report/definition/pages/pages.json
    <out>/<name>.Report/definition/pages/<page>/page.json     one empty page at the given canvas size,
                                                              canvas and wallpaper in the theme page colour
    <out>/<name>.Report/StaticResources/RegisteredResources/<theme file>
    <out>/.gitignore                                          (only if missing)

Ids, names and workspaces are arguments only; nothing tenant-specific is stored in this script.
Formats and their sources: references/pbir-skeleton.md. Validate afterwards (jq empty, a PBIP
validator where available) and open the .pbip in Power BI Desktop.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_THEME = HERE.parent / "assets" / "ibcs-pbi-theme.json"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
PBIP_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
PLATFORM_SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                   "platformProperties/2.0.0/schema.json")
PBIR_SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/report/"
               "definitionProperties/2.0.0/schema.json")
EXT_SCHEMA = f"{SCHEMA}/reportExtension/1.0.0/schema.json"
SERVICE = "powerbi://api.powerbi.com/v1.0/myorg/"  # public Power BI service endpoint (Desktop form)


def write(path: Path, obj, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"{path} exists; use --force to overwrite generated files")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = obj if isinstance(obj, str) else json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {path}")


def page_objects(theme: Path) -> dict:
    """Canvas (background) and wallpaper (outspace) in the theme's page colour, written on the page
    too, so the page does not depend on the theme's page style being applied (verify in Desktop)."""
    t = json.loads(theme.read_text(encoding="utf-8"))
    style = t.get("visualStyles", {}).get("page", {}).get("*", {})
    color = (style.get("background") or [{}])[0].get("color", {}).get("solid", {}).get("color") \
        or t.get("background", "#FFFFFF")
    solid = {"color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{color}'"}}}}}}
    zero = {"transparency": {"expr": {"Literal": {"Value": "0D"}}}}
    return {"background": [{"properties": {**solid, **zero}}], "outspace": [{"properties": {**solid, **zero}}]}


def dataset_reference(a) -> dict:
    if a.by_path:
        return {"byPath": {"path": a.by_path}}
    if a.workspace and a.model:
        cs = (f'Data Source="{SERVICE}{a.workspace}";initial catalog={a.model};'
              "access mode=readonly;integrated security=ClaimsToken")
        if a.semantic_model_id:
            cs += f";semanticmodelid={a.semantic_model_id}"
        return {"byConnection": {"connectionString": cs}}
    if a.semantic_model_id:
        return {"byConnection": {"connectionString": f"semanticmodelid={a.semantic_model_id}"}}
    raise SystemExit("give --semantic-model-id, or --workspace and --model, or --by-path")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="folder that receives <name>.pbip and <name>.Report/")
    ap.add_argument("--name", required=True, help="report name (file and display name)")
    ap.add_argument("--semantic-model-id", help="id of the published semantic model")
    ap.add_argument("--workspace", help="workspace name (Desktop connection-string form)")
    ap.add_argument("--model", help="semantic model name (Desktop connection-string form)")
    ap.add_argument("--by-path", help="relative path to a local <model>.SemanticModel folder instead")
    ap.add_argument("--theme", default=str(DEFAULT_THEME), help="theme JSON (default: bundled IBCS theme)")
    ap.add_argument("--page-name", help="page folder/name (default: random 20-hex like Desktop)")
    ap.add_argument("--page-display", default="Page 1", help="page display name")
    ap.add_argument("--canvas", default="1280x720", help="WIDTHxHEIGHT in px (taller pages scroll)")
    ap.add_argument("--display-option", default="FitToPage", choices=["FitToPage", "FitToWidth", "ActualSize"],
                    help="page view; FitToWidth for tall (scrolling) pages")
    ap.add_argument("--logical-id", help="the .platform logicalId (default: new uuid4)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    m = re.fullmatch(r"(\d+)x(\d+)", a.canvas)
    if not m:
        raise SystemExit("--canvas must be WIDTHxHEIGHT, e.g. 1280x720")
    width, height = int(m[1]), int(m[2])
    theme_src = Path(a.theme)
    if not theme_src.is_file():
        raise SystemExit(f"theme not found: {theme_src} (build it with build_pbi_theme.py)")
    if "/" in a.name or "\\" in a.name:
        raise SystemExit("--name must not contain path separators")

    out = Path(a.out)
    rep = out / f"{a.name}.Report"
    d = rep / "definition"
    page = a.page_name or secrets.token_hex(10)
    theme_file = theme_src.name

    write(out / f"{a.name}.pbip", {
        "$schema": PBIP_SCHEMA, "version": "1.0",
        "artifacts": [{"report": {"path": f"{a.name}.Report"}}],
        "settings": {"enableAutoRecovery": True}}, a.force)
    write(rep / ".platform", {
        "$schema": PLATFORM_SCHEMA,
        "metadata": {"type": "Report", "displayName": a.name},
        "config": {"version": "2.0", "logicalId": a.logical_id or str(uuid.uuid4())}}, a.force)
    write(rep / "definition.pbir", {"$schema": PBIR_SCHEMA, "version": "4.0",
                                    "datasetReference": dataset_reference(a)}, a.force)
    write(d / "version.json", {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
          a.force)
    write(d / "report.json", {
        "$schema": f"{SCHEMA}/report/3.0.0/schema.json",
        "themeCollection": {"customTheme": {
            "name": theme_file,
            "reportVersionAtImport": {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"},
            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": theme_file, "path": theme_file, "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True}}, a.force)
    write(d / "reportExtensions.json", {"$schema": EXT_SCHEMA, "name": "extension", "entities": []}, a.force)
    write(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
                                       "pageOrder": [page], "activePageName": page}, a.force)
    write(d / "pages" / page / "page.json", {
        "$schema": f"{SCHEMA}/page/2.0.0/schema.json",
        "name": page, "displayName": a.page_display, "displayOption": a.display_option,
        "height": height, "width": width, "objects": page_objects(theme_src)}, a.force)
    target = rep / "StaticResources" / "RegisteredResources" / theme_file
    if target.exists() and not a.force:
        raise SystemExit(f"{target} exists; use --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(theme_src, target)
    print(f"wrote {target}")
    gi = out / ".gitignore"
    if not gi.exists():
        gi.write_text("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n", encoding="utf-8", newline="\n")
        print(f"wrote {gi}")
    print(f"page folder: {d / 'pages' / page} (add visuals under visuals/<name>/visual.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
