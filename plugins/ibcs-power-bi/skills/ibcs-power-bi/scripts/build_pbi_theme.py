#!/usr/bin/env python3
"""Generate an IBCS Power BI report theme from the IBCS design tokens.

    python3 -I scripts/build_pbi_theme.py                         # writes ./ibcs-pbi-theme.json and -cvd.json
    python3 -I scripts/build_pbi_theme.py --out-dir ./theme --overrides ibcs-tokens.overrides.json
    python3 -I scripts/build_pbi_theme.py --check --out-dir ./theme   # exit 1 if the files are stale (CI)
    python3 -I scripts/build_pbi_theme.py --theme-overrides my-theme-fragment.json
    python3 scripts/build_pbi_theme.py --validate --schema reportThemeSchema-2.157.json   # needs jsonschema

Paths to this script are relative to the ibcs-power-bi skill; run it from your project directory.
--tokens defaults to the token file bundled with the sibling ibcs-deneb skill
(../ibcs-deneb/assets/ibcs-tokens.json); --overrides is your organisation's ibcs-tokens.overrides.json.

Outputs (one per colour variant, UN 4.1):
    ibcs-pbi-theme.json       standard impact colours
    ibcs-pbi-theme-cvd.json   colour-vision-deficiency adaptation (good = blue-green)
    ibcs-pbi-theme-bw.json    greys only (--variants standard,cvd,bw)

Token overrides are deep-merged over the tokens before aliases are resolved. --theme-overrides is
a Power BI theme *fragment* deep-merged over the generated theme at the very end (objects merge,
arrays replace) for Power BI-only choices that have no token (e.g. visualHeader). Never put a
colour there that a token already defines.

What the theme can and cannot do for IBCS (see references/theme.md):
- it sets scenario greys as dataColors[0..2] (AC, PY, PL fill), impact colours as good/bad/neutral,
  one font family, no gridlines / value axes / legends / backgrounds / borders / shadows, data
  labels on, overlapped clustered columns/bars, 2/3 bar width via category inner padding;
- it can NOT give PL its outline or FC its hatch (per-series formatting in visual.json, SVG, Deneb).

Stdlib only; --validate needs `jsonschema` (pip) and the schema file or URL.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # leave no __pycache__ inside the plugin
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ibcs-deneb" / "scripts"))
import ibcs_tokens  # noqa: E402

SCHEMA_VERSION = "2.157"
SCHEMA_URL = (
    "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/"
    f"Report%20Theme%20JSON%20Schema/reportThemeSchema-{SCHEMA_VERSION}.json"
)
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def solid(color: str) -> dict:
    return {"solid": {"color": color}}


def build_theme(t: dict, variant: str = "standard", file_name: str | None = None) -> dict:
    """file_name: the theme's file name including .json. Microsoft's PBIR validator requires the
    theme's "name" to equal the file name that report.json registers (PBIR_THEME_FILE_NAME_MISMATCH),
    so the name is the file name, not a display label."""
    g = ibcs_tokens.get
    sc = g(t, "color.scenario")
    var = g(t, "color.variance")
    impact = {"standard": var, "cvd": var["cvd"], "bw": var["bw"]}[variant]

    fam_regular, fam_emph = (g(t, "typography.family.powerbi") + [None, None])[:2]
    fam_emph = fam_emph or fam_regular
    size = lambda role: g(t, f"typography.size.{role}.pt")  # noqa: E731
    text = g(t, "color.text.primary")
    text2 = g(t, "color.text.secondary")
    page_bg = g(t, "color.background.page")
    rule = g(t, "color.table.rule")
    rule_light = g(t, "color.table.ruleLight")

    # dataColors: scenario greys first (AC, PY, PL fill), then the remaining stack greys.
    data_colors: list[str] = []
    for c in [sc["ac"], sc["py"], sc["pl"]["fill"], *sc["stackGrays"]]:
        if c.upper() not in (x.upper() for x in data_colors):
            data_colors.append(c)

    abs_pad = round((1 - g(t, "geometry.barWidthRatio.absolute")) * 100)  # 2/3 width -> 33 % gap
    col_offset = round(g(t, "geometry.referenceOffsetRatio.column") * 100)
    bar_offset = round(g(t, "geometry.referenceOffsetRatio.bar") * 100)
    line_px = g(t, "stroke.line.absolutePx")
    marker = max(2, round(line_px * g(t, "stroke.line.markerToLineRatio") / 2))
    row_px = g(t, "layout.table.rowHeightPx")

    no_chrome = {
        "background": [{"show": False}],
        "border": [{"show": False}],
        "dropShadow": [{"show": False}],
    }
    labels = {
        "show": True,
        "fontFamily": fam_regular,
        "fontSize": size("label"),
        "color": solid(text),
        "labelDisplayUnits": 1,  # 1 = None (0 = Auto): scale in the model / title unit, not "K" suffixes
    }

    visual_styles: dict = {
        "*": {
            "*": {
                **no_chrome,
                "legend": [{"show": False, "fontFamily": fam_regular, "fontSize": size("label")}],
                "valueAxis": [{"show": False, "gridlineShow": False, "showAxisTitle": False}],
                "categoryAxis": [{
                    "show": True, "gridlineShow": False, "showAxisTitle": False,
                    "fontFamily": fam_regular, "fontSize": size("label"), "labelColor": solid(text),
                }],
                "labels": [labels],
                "title": [{
                    "show": True, "fontFamily": fam_regular, "fontSize": size("subtitle"),
                    "fontColor": solid(text), "bold": False, "alignment": "left",
                }],
                "subTitle": [{"fontFamily": fam_regular, "fontSize": size("label"), "fontColor": solid(text2)}],
                "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}],
            }
        },
        "page": {
            "*": {
                "background": [{"color": solid(page_bg), "transparency": 0}],
                "outspace": [{"color": solid(page_bg), "transparency": 0}],
            }
        },
        "columnChart": {"*": {"categoryAxis": [{"innerPadding": abs_pad}],
                              "labels": [{"labelPosition": "OutsideEnd"}]}},
        "barChart": {"*": {"categoryAxis": [{"innerPadding": abs_pad}],
                           "labels": [{"labelPosition": "OutsideEnd"}]}},
        "clusteredColumnChart": {"*": {
            # Overlap: the LAST measure in the Y well is drawn in front -> put AC/FC last (UN 4.1).
            "layout": [{"clusteredGapOverlaps": True, "clusteredGapSize": col_offset}],
            "categoryAxis": [{"innerPadding": abs_pad}],
            "dataPoint": [{"borderShow": False}],
            "labels": [{"labelPosition": "OutsideEnd"}],
        }},
        "clusteredBarChart": {"*": {
            "layout": [{"clusteredGapOverlaps": True, "clusteredGapSize": bar_offset}],
            "categoryAxis": [{"innerPadding": abs_pad}],
            "labels": [{"labelPosition": "OutsideEnd"}],
        }},
        "lineChart": {"*": {
            "lineStyles": [{"strokeWidth": line_px, "showMarker": True, "markerShape": "square",
                            "markerSize": marker, "lineStyle": "solid"}],
            "seriesLabels": [{"show": True}],  # series name at the line end instead of a legend
            "labels": [{"show": False}],       # dense lines: label selectively per series in visual.json
        }},
        "lineClusteredColumnComboChart": {"*": {
            "categoryAxis": [{"innerPadding": abs_pad}],
            "valueAxis": [{"show": False, "secShow": False, "gridlineShow": False}],  # overlay, CO 4.1
        }},
        "waterfallChart": {"*": {
            "sentimentColors": [{
                "increaseFill": solid(impact["good"]),
                "decreaseFill": solid(impact["bad"]),
                "totalFill": solid(sc["ac"]),
                "otherFill": solid(sc["py"]),
            }],
            "categoryAxis": [{"innerPadding": abs_pad}],
        }},
        "pivotTable": {"*": _table_styles(t, fam_regular, fam_emph, text, rule, rule_light, row_px, matrix=True)},
        "tableEx": {"*": _table_styles(t, fam_regular, fam_emph, text, rule, rule_light, row_px, matrix=False)},
        "textbox": {"*": {**no_chrome}},
        "cardVisual": {"*": {**no_chrome}},
    }

    theme = {
        "$schema": SCHEMA_URL,
        "name": file_name or ("ibcs-pbi-theme" + {"standard": "", "cvd": "-cvd", "bw": "-bw"}[variant] + ".json"),
        "dataColors": data_colors,
        "good": impact["good"],
        "bad": impact["bad"],
        "neutral": impact["neutral"],
        # Gradient defaults stay grey: colour is reserved for impact (SI 2.2, UN 4.1)
        "maximum": sc["ac"],
        "center": sc["py"],
        "minimum": sc["stackGrays"][-1],
        "foreground": text,
        "foregroundNeutralSecondary": text2,
        "background": page_bg,
        "backgroundLight": page_bg,
        "secondaryBackground": g(t, "color.marker.assistingArea"),
        "tableAccent": sc["ac"],
        "hyperlink": g(t, "color.marker.highlight"),
        "visitedHyperlink": g(t, "color.marker.highlight"),
        "textClasses": {
            # Key message / page title (UN 2.1-2.2)
            "largeTitle": {"fontFace": fam_emph, "fontSize": size("keyMessage"), "color": text},
            "title": {"fontFace": fam_regular, "fontSize": size("title"), "color": text},
            "header": {"fontFace": fam_emph, "fontSize": size("label"), "color": text},
            "label": {"fontFace": fam_regular, "fontSize": size("label"), "color": text},
            "semiboldLabel": {"fontFace": fam_emph, "fontSize": size("label"), "color": text},
            "boldLabel": {"fontFace": fam_emph, "fontSize": size("label"), "color": text},
            "smallLabel": {"fontFace": fam_regular, "fontSize": size("footnote"), "color": text2},
            "smallDataLabel": {"fontFace": fam_regular, "fontSize": size("footnote"), "color": text},
            "callout": {"fontFace": fam_emph, "fontSize": size("keyMessage"), "color": text},
        },
        "visualStyles": visual_styles,
    }
    return theme


def _table_styles(t, fam, fam_emph, text, rule, rule_light, row_px, matrix: bool) -> dict:
    g = ibcs_tokens.get
    s = g(t, "typography.size.label.pt")
    styles = {
        "background": [{"show": False}],
        "border": [{"show": False}],
        "dropShadow": [{"show": False}],
        # Thin light row separators, no vertical grid (EX 1.2, notation-spec rule_light)
        "grid": [{
            "gridHorizontal": True, "gridHorizontalColor": solid(rule_light),
            "gridHorizontalWeight": g(t, "stroke.tableHeader.rowRulePx"),
            "gridVertical": False, "rowPadding": 2, "textSize": s,
            "imageHeight": row_px,  # SVG-in-DAX cells: one row high (ibcs-svg-dax skill)
        }],
        "columnHeaders": [{
            "fontFamily": fam_emph, "fontSize": s, "fontColor": solid(text),
            "backColor": solid(g(t, "color.background.page")), "alignment": "Right", "wordWrap": True,
        }],
        "values": [{
            "fontFamily": fam, "fontSize": s, "fontColor": solid(text),
            "backColor": solid(g(t, "color.background.page")),
            "backColorPrimary": solid(g(t, "color.background.page")),
            "backColorSecondary": solid(g(t, "color.background.page")),  # no zebra banding (SI 1.2)
        }],
        "total": [{"bold": True, "fontFamily": fam_emph, "fontColor": solid(text)}],
    }
    if matrix:
        styles["rowHeaders"] = [{"fontFamily": fam, "fontSize": s, "fontColor": solid(text), "stepped": False}]
        # Totals/subtotals below their children, bold (EX 1.2 pp. 128-129)
        styles["subTotals"] = [{"bold": True, "rowSubtotalsPosition": "Bottom"}]
    return styles


def deep_merge(base, over):
    return ibcs_tokens.deep_merge(base, over)


# ---------- checks ---------------------------------------------------------------------------

REQUIRED_TOP = ["name", "dataColors", "good", "bad", "neutral", "foreground", "background",
                "textClasses", "visualStyles"]


def key_check(theme: dict) -> list[str]:
    errs: list[str] = []
    for k in REQUIRED_TOP:
        if k not in theme:
            errs.append(f"missing top-level key: {k}")
    for i, c in enumerate(theme.get("dataColors", [])):
        if not HEX.match(c):
            errs.append(f"dataColors[{i}] not #RRGGBB: {c}")
    if len(theme.get("dataColors", [])) < 3:
        errs.append("dataColors needs AC, PY, PL at least")
    for k in ("good", "bad", "neutral", "foreground", "background", "tableAccent"):
        if k in theme and not HEX.match(theme[k]):
            errs.append(f"{k} not #RRGGBB: {theme[k]}")
    if theme.get("good", "").upper() == theme.get("bad", "").upper():
        errs.append("good == bad")
    star = theme.get("visualStyles", {}).get("*", {}).get("*", {})
    expect = {
        ("legend", "show"): False,
        ("valueAxis", "show"): False,
        ("valueAxis", "gridlineShow"): False,
        ("categoryAxis", "gridlineShow"): False,
        ("labels", "show"): True,
        ("labels", "labelDisplayUnits"): 1,  # 1 = None; 0 would be Auto ("K"/"M" suffixes)
        ("background", "show"): False,
        ("border", "show"): False,
        ("dropShadow", "show"): False,
    }
    for (obj, prop), want in expect.items():
        got = (star.get(obj) or [{}])[0].get(prop)
        if type(got) is not type(want) or got != want:
            errs.append(f"visualStyles.*.*.{obj}.{prop} should be {want}, is {got}")
    for name, tc in theme.get("textClasses", {}).items():
        if not tc.get("fontFace") or not isinstance(tc.get("fontSize"), (int, float)):
            errs.append(f"textClasses.{name} needs fontFace + numeric fontSize")
    return errs


def schema_validate(theme: dict, schema_src: str) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return ["--validate needs `pip install jsonschema` (skipped)"]
    if re.match(r"^https?://", schema_src):
        import urllib.request
        with urllib.request.urlopen(schema_src, timeout=30) as r:  # noqa: S310 (fixed MS URL)
            schema = json.loads(r.read().decode("utf-8"))
    else:
        schema = json.loads(Path(schema_src).read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errs = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message[:300]}"
            for e in sorted(validator.iter_errors(theme), key=lambda e: list(e.absolute_path))]
    return errs + strict_names(theme, schema)


def strict_names(theme: dict, schema: dict) -> list[str]:
    """The schema allows unknown properties inside objects; catch typos ourselves.

    Every visualStyles.<visual>.*.<object>[].<property> must exist in the schema's
    definitions/visual-<visual> (the "*" visual is generic and is skipped).
    """
    defs = schema.get("definitions", {})

    def resolve(n):
        while isinstance(n, dict) and "$ref" in n:
            n = defs[n["$ref"].split("/")[-1]]
        return n

    def props(n):
        n = resolve(n)
        out = {}
        for part in n.get("allOf", []):
            out.update(props(part))
        out.update(n.get("properties", {}))
        return out

    errs = []
    for vis, presets in theme.get("visualStyles", {}).items():
        if vis == "*":
            continue
        vdef = defs.get(f"visual-{vis}")
        if vdef is None:
            if vis not in schema.get("properties", {}).get("visualStyles", {}).get("properties", {}):
                errs.append(f"unknown visual type in visualStyles: {vis}")
            vdef = resolve(schema["properties"]["visualStyles"]["properties"].get(vis, {}).get("properties", {}).get("*", {}))
        objs = props(vdef)
        for preset, objects in presets.items():
            for obj, items in objects.items():
                if obj not in objs:
                    errs.append(f"visualStyles.{vis}.{preset}: unknown object '{obj}'")
                    continue
                known = props(resolve(objs[obj]).get("items", {}))
                for item in items:
                    for p in item:
                        if known and p not in known:
                            errs.append(f"visualStyles.{vis}.{preset}.{obj}: unknown property '{p}'")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokens", help="token file (default: the bundled ibcs-tokens.json)")
    ap.add_argument("--overrides", help="your ibcs-tokens.overrides.json (optional)")
    ap.add_argument("--theme-overrides", help="Power BI theme fragment merged over the result")
    ap.add_argument("--out-dir", default=".", help="output directory (default: current directory)")
    ap.add_argument("--name", default="ibcs-pbi-theme",
                    help="file stem (default ibcs-pbi-theme); the theme's \"name\" is set to the file name")
    ap.add_argument("--variants", default="standard,cvd", help="comma list of standard,cvd,bw")
    ap.add_argument("--check", action="store_true", help="exit 1 if generated files are stale")
    ap.add_argument("--validate", action="store_true", help="validate against the theme JSON schema")
    ap.add_argument("--schema", default=SCHEMA_URL, help="schema path or URL for --validate")
    a = ap.parse_args()

    srcs = [str(p) for p in ibcs_tokens.source_paths(a.tokens, a.overrides)]
    tok = ibcs_tokens.load(a.tokens, a.overrides)
    frag = json.loads(Path(a.theme_overrides).read_text(encoding="utf-8")) if a.theme_overrides else None
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]

    out_dir = Path(a.out_dir)
    status = 0
    for variant in variants:
        suffix = "" if variant == "standard" else f"-{variant}"
        path = out_dir / f"{a.name}{suffix}.json"
        theme = build_theme(tok, variant, path.name)
        if frag:
            theme = deep_merge(theme, frag)
            theme["name"] = path.name  # a fragment must not break the name = file name rule
        errs = key_check(theme)
        if a.validate:
            errs += [f"schema: {e}" for e in schema_validate(theme, a.schema)]
        body = json.dumps(theme, indent=2, ensure_ascii=False) + "\n"
        if errs:
            status = 1
            print(f"[{variant}] {len(errs)} problem(s):", *errs, sep="\n  ", file=sys.stderr)
        if a.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                print(f"stale: {path} (run build_pbi_theme.py)", file=sys.stderr)
                status = 1
            continue
        if errs:
            print(f"not written: {path}", file=sys.stderr)
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path}  (from {', '.join(srcs)}{', ' + a.theme_overrides if frag else ''})")
    return status


if __name__ == "__main__":
    sys.exit(main())
