#!/usr/bin/env python3
"""Generate an IBCS Power BI report theme from the IBCS design tokens.

    python3 -I scripts/build_pbi_theme.py                         # writes ./ibcs-pbi-theme.json and -cvd.json
    python3 -I scripts/build_pbi_theme.py --out-dir ./theme --overrides ibcs-tokens.overrides.json
    python3 -I scripts/build_pbi_theme.py --check --out-dir ./theme   # exit 1 if the files are stale (CI)
    python3 -I scripts/build_pbi_theme.py --theme-overrides my-theme-fragment.json
    python3 scripts/build_pbi_theme.py --validate --schema reportThemeSchema-2.157.json   # needs jsonschema
    python3 -I scripts/build_pbi_theme.py --shell                 # page shell: rounded cards (fluent-cards)
    python3 -I scripts/build_pbi_theme.py --shell cards           # page shell, square cards

Page shell (references/page-shell.md). Both modes: the page background becomes a neutral light
canvas and every visual gets --card-padding px left and right (default 16; top/bottom 0 so the
visuals of one card stack seamlessly).
--shell fluent-cards (the default when --shell has no value): canvas = 5 % ink (color.text.primary)
  over the page colour. One `shape` visual per card, behind its content (z below the content), is
  the card: white fill, a 1 px ring at 10 % ink, radius 8, soft shadow (distance 2, blur 4,
  transparency 88). Content visuals have no background, so the ring and corners show; shapes
  are the only visuals with an outline or shadow (house style for the chrome outside the content,
  ours, not stated by IBCS; every content rule holds inside the card).
--shell cards: square cards: canvas --canvas (default #F3F3F3), every visual white
  (color.background.page), no borders, shadows or rounded corners.

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


CANVAS = "#F3F3F3"      # page shell canvas: neutral (no hue), light enough to read as "paper" behind white cards
CARD_PADDING_PX = 16
FLUENT = {"canvasInk": 0.05, "ringInk": 0.10, "radius": 8, "shadowDistance": 2, "shadowBlur": 4,
          "shadowTransparency": 88}   # fluent-cards shell: chrome tokens (page-shell.md §1)


def mix(ink: str, paper: str, share: float) -> str:
    """`share` of ink over paper, as #RRGGBB (neutral when both are greys)."""
    a = [int(ink[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(paper[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * share + y * (1 - share)):02X}" for x, y in zip(a, b))


def build_theme(t: dict, variant: str = "standard", file_name: str | None = None,
                shell: dict | None = None) -> dict:
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
    fluent = (shell or {}).get("mode") == "fluent-cards"
    canvas = mix(text, page_bg, FLUENT["canvasInk"]) if fluent else (shell or {}).get("canvas", page_bg)
    pad = (shell or {}).get("padding", 0)

    card = shell is not None
    white_visuals = card and not fluent   # fluent: the card shape is the white sheet, content is transparent
    no_chrome = {
        "background": [{"show": True, "color": solid(page_bg), "transparency": 0}] if white_visuals
        else [{"show": False}],
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
                "padding": [{"top": 0, "bottom": 0, "left": pad, "right": pad}],
            }
        },
        "page": {
            "*": {
                "background": [{"color": solid(canvas), "transparency": 0}],
                "outspace": [{"color": solid(canvas), "transparency": 0}],
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
        "pivotTable": {"*": _table_styles(t, fam_regular, fam_emph, text, rule, rule_light, row_px, matrix=True,
                                          card=white_visuals)},
        "tableEx": {"*": _table_styles(t, fam_regular, fam_emph, text, rule, rule_light, row_px, matrix=False,
                                       card=white_visuals)},
        "textbox": {"*": {**no_chrome}},
        "cardVisual": {"*": {**no_chrome}},
    }
    if fluent:
        ring = mix(text, page_bg, FLUENT["ringInk"])
        card_shape = {
            "background": [{"show": False}],
            "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}],
            "fill": [{"fillColor": solid(page_bg), "transparency": 0}],
            "outline": [{"show": True, "lineColor": solid(ring), "weight": 1}],
            "shape": [{"tileShape": "rectangleRounded", "roundEdge": FLUENT["radius"]}],
            "border": [{"show": False}],
            "dropShadow": [{"show": True, "preset": "Custom", "position": "Outer", "color": solid(text),
                            "transparency": FLUENT["shadowTransparency"], "shadowDistance": FLUENT["shadowDistance"],
                            "shadowBlur": FLUENT["shadowBlur"], "shadowSpread": 0, "angle": 90}],
        }
        visual_styles["shape"] = {"*": card_shape}
        visual_styles["basicShape"] = {"*": card_shape}

    theme = {
        "$schema": SCHEMA_URL,
        "name": file_name or ("ibcs-pbi-theme" + {"standard": "", "cvd": "-cvd", "bw": "-bw"}[variant] + ".json"),
        "dataColors": data_colors,
        # good/bad/neutral colour TEXT in Power BI (new card reference labels, KPI status, font-colour
        # rules), so they take the contrast-safe *Text tokens (>= 4.5:1); marks keep the graphic
        # colours (waterfall fills above, colour measures). The bw build has no text variants.
        "good": impact.get("goodText", impact["good"]),
        "bad": impact.get("badText", impact["bad"]),
        "neutral": impact.get("neutralText", impact["neutral"]),
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


def _table_styles(t, fam, fam_emph, text, rule, rule_light, row_px, matrix: bool, card: bool = False) -> dict:
    g = ibcs_tokens.get
    s = g(t, "typography.size.label.pt")
    styles = {
        # page shell: tables are cards too, so their rows never sit on the grey canvas
        "background": [{"show": True, "color": solid(g(t, "color.background.page")), "transparency": 0}]
        if card else [{"show": False}],
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


def key_check(theme: dict, shell: bool | str = False) -> list[str]:
    """shell: False, "cards" (or True) or "fluent-cards"."""
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
        # square shell: white visuals; fluent shell: the card shape is white, content transparent
        ("background", "show"): bool(shell) and shell != "fluent-cards",
        ("border", "show"): False,
        ("dropShadow", "show"): False,
    }
    for (obj, prop), want in expect.items():
        got = (star.get(obj) or [{}])[0].get(prop)
        if type(got) is not type(want) or got != want:
            errs.append(f"visualStyles.*.*.{obj}.{prop} should be {want}, is {got}")
    if shell == "fluent-cards":
        sh = (theme.get("visualStyles", {}).get("shape", {}).get("*", {}))
        if (sh.get("dropShadow") or [{}])[0].get("show") is not True or \
                (sh.get("outline") or [{}])[0].get("show") is not True:
            errs.append("fluent-cards: visualStyles.shape needs the ring (outline) and the soft shadow")
    for name, tc in theme.get("textClasses", {}).items():
        if not tc.get("fontFace") or not isinstance(tc.get("fontSize"), (int, float)):
            errs.append(f"textClasses.{name} needs fontFace + numeric fontSize")
    return errs


def schema_validate(theme: dict, schema_src: str) -> list[str]:
    import jsonschema  # type: ignore  # presence checked in main() before anything is generated
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
    ap.add_argument("--shell", nargs="?", const="fluent-cards", choices=["none", "fluent-cards", "cards"],
                    default="none",
                    help="page shell (references/page-shell.md): fluent-cards (default when given without a value) = "
                         "rounded card shapes behind transparent content; cards = square white visuals")
    ap.add_argument("--canvas", default=CANVAS, help=f"--shell cards: page canvas colour (default {CANVAS})")
    ap.add_argument("--card-padding", type=int, default=CARD_PADDING_PX,
                    help=f"page shell: left/right padding of every visual in px (default {CARD_PADDING_PX})")
    ap.add_argument("--check", action="store_true", help="exit 1 if generated files are stale")
    ap.add_argument("--validate", action="store_true", help="validate against the theme JSON schema")
    ap.add_argument("--schema", default=SCHEMA_URL, help="schema path or URL for --validate")
    a = ap.parse_args()
    if a.validate:
        try:
            import jsonschema  # type: ignore  # noqa: F401
        except ImportError:
            print("--validate needs the jsonschema package: run with `uv run --with jsonschema python3 "
                  "build_pbi_theme.py --validate …` or `pip install jsonschema`; nothing was written.", file=sys.stderr)
            return 2

    srcs = [str(p) for p in ibcs_tokens.source_paths(a.tokens, a.overrides)]
    tok = ibcs_tokens.load(a.tokens, a.overrides)
    frag = json.loads(Path(a.theme_overrides).read_text(encoding="utf-8")) if a.theme_overrides else None
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]

    shell = None
    if a.shell in ("cards", "fluent-cards"):
        if not HEX.match(a.canvas):
            sys.exit(f"--canvas must be #RRGGBB, is {a.canvas}")
        shell = {"canvas": a.canvas, "padding": a.card_padding, "mode": a.shell}
    out_dir = Path(a.out_dir)
    status = 0
    for variant in variants:
        suffix = "" if variant == "standard" else f"-{variant}"
        path = out_dir / f"{a.name}{suffix}.json"
        theme = build_theme(tok, variant, path.name, shell)
        if frag:
            theme = deep_merge(theme, frag)
            theme["name"] = path.name  # a fragment must not break the name = file name rule
        errs = key_check(theme, a.shell if shell is not None else False)
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
