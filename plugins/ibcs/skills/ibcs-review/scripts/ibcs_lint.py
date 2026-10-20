#!/usr/bin/env python3
"""ibcs_lint.py - read-only lint for obvious IBCS notation violations.

Targets
  pbir      a Power BI PBIR report folder (<name>.Report or its definition/ folder), including
            its report-level measures (definition/reportExtensions.json), the bindings to them,
            table image columns, the Deneb specs embedded in visual.json and their scale groups
            (--layout: scale_layout.py --json output; each visual must have that size and px per
            unit), slicer headers / titles that would be cut, and a page shell's canvas
  theme     a Power BI report theme JSON
  vegalite  a Vega-Lite spec JSON (Fabric App / Deneb)
  tokens    an ibcs-tokens.json (+ --overrides) guardrail check
  spec      an IBCS visual spec (*.visual-spec.yaml or .json): the mechanical rules of
            visual-spec-format §10 (YAML needs PyYAML; otherwise convert it to JSON first)
  dom       a rendered web page or chart (.html / .svg snapshot) whose marks carry data-role
            attributes (ibcs-web-charts §8): scenario fills, impact colours, label rotation
  auto      (default) detect from the path

Usage
  python3 -I ibcs_lint.py [auto|pbir|theme|vegalite|tokens|spec|dom] PATH
                          [--tokens TOKENS.json] [--overrides OVERRIDES.json]
                          [--format md|json] [--layout LAYOUT.json ...]

The script never writes, renames or deletes anything. It flags only what metadata can
show; a clean result does not mean the page is IBCS-compliant (see the ibcs-review skill
for the full manual checklist). Exit code: 0 = no failed must-rule, 1 = at least one
failed must-rule (severity M, status fail), 2 = usage/parse error.

Tokens default to the bundled ../../ibcs-notation/assets/ibcs-tokens.json (relative to this
script). Overrides default to the first ibcs-tokens.overrides.json found in the current
directory or one of its parents; pass --overrides to choose another file (or --no-overrides).

Rule IDs are the checklist IDs of the ibcs-review skill's references/checklist.md (A..G notation,
H/J/K composition, e.g. K9 = EX 2 chart replacements), V1..V17 for the numbered validation rules
of the visual spec format (§10), plus LINT for a part the linter could not read (review it
manually) or a technical defect that breaks the page (e.g. a hidden report-level measure, or a
binding to one without "Schema": "extension"); the 'ibcs' column cites the IBCS Standards v2.0
(SI/UN/CH/EX).
Follows the IBCS(R) Standards; not an IBCS certification. MIT.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# ----------------------------------------------------------------------------- findings

FINDINGS: list[dict] = []


def add(rule, ibcs, sev, status, location, evidence, fix):
    FINDINGS.append(dict(rule=rule, ibcs=ibcs, sev=sev, status=status,
                         location=str(location), evidence=evidence, fix=fix))


# ----------------------------------------------------------------------------- helpers

def load_json(path: Path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def hex_to_rgb(h: str):
    h = h.strip().strip("'\"").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:  # ARGB/RGBA - take RGB part heuristically
        h = h[:6]
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        return None
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_of(c, where: str):
    """hex_to_rgb that refuses a non-colour (bad override, unresolved alias) with a clear message."""
    rgb = hex_to_rgb(c) if isinstance(c, str) else None
    if rgb is None:
        raise ValueError(f"{where} = {c!r} is not a hex colour")
    return rgb


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def saturation(h: str) -> float:
    rgb = hex_to_rgb(h)
    if rgb is None:
        return 0.0
    _, s, v = colorsys.rgb_to_hsv(*rgb)
    return s if v > 0.15 else 0.0


def rel_lum(h: str) -> float:
    rgb = hex_to_rgb(h)
    if rgb is None:
        return 0.0
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def is_white(h: str) -> bool:
    rgb = hex_to_rgb(h)
    return rgb is not None and min(rgb) >= 0.98


def literal(v):
    """Decode a PBIR {'expr': {'Literal': {'Value': ...}}} (or a plain value)."""
    if isinstance(v, dict):
        if "expr" in v:
            v = v["expr"]
        if "Literal" in v:
            v = v["Literal"].get("Value")
        elif "solid" in v:
            return literal(v["solid"].get("color"))
        else:
            return None
    if isinstance(v, str):
        s = v
        if s in ("true", "false"):
            return s == "true"
        m = re.fullmatch(r"(-?\d+(?:\.\d+)?)[DLM]?", s)
        if m:
            return float(m.group(1))
        if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
            return s[1:-1].replace("''", "'")
    return v


def obj_prop(objects: dict, obj: str, prop: str):
    """First value of objects[obj][i].properties[prop] (selector-less entry preferred)."""
    entries = (objects or {}).get(obj) or []
    ordered = sorted(entries, key=lambda e: 0 if "selector" not in e else 1)
    for e in ordered:
        props = e.get("properties", {})
        if prop in props:
            return literal(props[prop])
    return None


def colours_in(node) -> list[str]:
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "color" and isinstance(v, dict):
                lv = literal(v)
                if isinstance(lv, str) and lv.startswith("#"):
                    out.append(lv)
            out.extend(colours_in(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(colours_in(v))
    return out


BANNED_TITLE = re.compile(r"\b(analysis|analyses|overview|development|trend|report|dashboard|"
                          r"table|chart|visuali[sz]ation|statistics|structure|comment)\b", re.I)
SUPERFLUOUS = re.compile(r"\b(sum of|total|full year|count of|average of)\b", re.I)
DATE_ENTITY = re.compile(r"date|calendar|time|period|fiscal", re.I)
DATE_PROP = re.compile(r"date|day|week|month|quarter|year|period|yyyy|fy\b", re.I)
DECORATIVE_FONT = re.compile(r"comic|script|brush|impact|papyrus|chiller|jokerman|curlz|"
                             r"times|georgia|garamond|cambria|palatino|bookman|courier|"
                             r"stencil|algerian|showcard|broadway|bauhaus|cooper|rockwell", re.I)

TYPE_RULES = {
    "piechart": ("K9", "EX 2.1", "S", "fail", "Pie chart", "Sorted bar chart (A-19) or 100 % stacked columns."),
    "donutchart": ("K9", "EX 2.1", "S", "fail", "Donut chart", "Sorted bar chart or 100 % stacked columns."),
    "gauge": ("K9", "EX 2.2", "S", "fail", "Gauge", "Variance columns over time (A-7) with AC/FC notation."),
    "funnel": ("K9", "EX 2.3", "S", "fail", "Funnel", "Bar chart of step values; line of conversion rates."),
    "treemap": ("G5", "CH 3.1, EX 2.1", "M", "check", "Treemap (area encoding)", "Sorted bar chart with remainder (A-19/A-30)."),
    "filledmap": ("G7", "CH 3.3", "M", "check", "Filled (choropleth) map", "Only for area-related measures; else bars or one-scale symbols."),
    "shapemap": ("G7", "CH 3.3", "M", "check", "Shape map", "Only for area-related measures; else bars."),
    "kpi": ("K6", "EX 2.5, CO 4.4", "S", "check", "KPI visual (status indicator)", "Variance bars unless the state is binary."),
    "ribbonchart": ("D9", "UN 3.2, EX 1.1", "S", "check", "Ribbon chart (no IBCS layout)", "Stacked columns with gray shades."),
}
CUSTOM_PATTERNS = [
    (re.compile(r"radar|spider", re.I), ("K9", "EX 2.3", "S", "fail", "Radar chart", "Bar charts side by side, same order.")),
    (re.compile(r"gauge|speedo|dial|bullet.?gauge|liquid", re.I), ("K9", "EX 2.2", "S", "fail", "Gauge-like visual", "Variance columns over time.")),
    (re.compile(r"pie|donut|doughnut|sunburst", re.I), ("K9", "EX 2.1", "S", "fail", "Pie/donut-like visual", "Sorted bars.")),
    (re.compile(r"funnel", re.I), ("K9", "EX 2.3", "S", "fail", "Funnel visual", "Bars / conversion line.")),
    (re.compile(r"3d|threed", re.I), ("G6", "CH 3.2, SI 2.1", "M", "fail", "3-D visual", "Flat 2-D bars/columns.")),
    (re.compile(r"play.?axis", re.I), ("A3", "SI 1.3", "S", "check", "Play-axis animation", "Static small multiples over time.")),
]
BAR_TYPES = {"clusteredbarchart", "barchart", "hundredpercentstackedbarchart"}
COLUMN_TYPES = {"clusteredcolumnchart", "columnchart", "hundredpercentstackedcolumnchart",
                "linechart", "areachart", "stackedareachart", "hundredpercentstackedareachart",
                "lineclusteredcolumncombochart", "linestackedcolumncombochart", "waterfallchart"}
TWO_VALUE_AXES = {"scatterchart", "bubblechart"}   # external legends next to symbols allowed (UN 2.3)
CHART_TYPES = BAR_TYPES | COLUMN_TYPES | TWO_VALUE_AXES | {"piechart", "donutchart", "ribbonchart", "treemap", "funnel"}
DATA_LABELLED_OK = TWO_VALUE_AXES


# ----------------------------------------------------------------------------- tokens

def deep_merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = deep_merge(base[k], v) if k in base else v
        return out
    return over


def token_get(tokens, path):
    node = tokens
    for p in path.split("."):
        node = node[p]
    return node


def token_value(tokens, path, depth=0):
    v = token_get(tokens, path)["$value"]
    if isinstance(v, str) and re.fullmatch(r"\{[^{}]+\}", v) and depth < 10:
        return token_value(tokens, v[1:-1], depth + 1)
    return v


def load_tokens(tokens_path, overrides_path):
    if not tokens_path or not Path(tokens_path).exists():
        return None
    t = load_json(Path(tokens_path))
    if overrides_path and Path(overrides_path).exists():
        t = deep_merge(t, load_json(Path(overrides_path)))
    return t


def palette_from_tokens(tokens) -> set[str]:
    found = set()
    def walk(node, path):
        if isinstance(node, dict):
            if "$value" in node and path.startswith("color."):
                try:
                    v = token_value(tokens, path)
                except Exception:
                    v = None
                for c in (v if isinstance(v, list) else [v]):
                    if isinstance(c, str) and c.startswith("#"):
                        found.add(c.upper())
            for k, v in node.items():
                if not k.startswith("$"):
                    walk(v, f"{path}.{k}" if path else k)
    walk(tokens, "")
    return found


def impact_hue_ok(variant: str, kind: str, c: str) -> bool:
    """Hue family of an impact colour: green good (CVD: blue-green), red bad, blue neutral."""
    hue = colorsys.rgb_to_hsv(*rgb_of(c, f"color.variance.{variant}{kind}"))[0] * 360
    if variant and kind == "good":
        return 165 <= hue <= 200
    if kind == "good":
        return 60 <= hue <= 165
    if kind == "bad":
        return hue <= 30 or hue >= 330
    return 200 <= hue <= 260


def lint_tokens(tokens, loc):
    def tv(p):
        return token_value(tokens, p)
    ac, py, pl, bg = tv("color.scenario.ac"), tv("color.scenario.py"), tv("color.scenario.pl.fill"), tv("color.background.page")
    for p in ("color.scenario.ac", "color.scenario.py", "color.scenario.pl.fill", "color.scenario.bu.fill",
              "color.scenario.fc.ground", "color.background.page", "color.text.primary", "color.text.secondary",
              "color.text.onAc", *(f"color.variance.{v}{k}" for v in ("", "cvd.") for k in ("good", "bad", "neutral"))):
        rgb_of(tv(p), p)
    for i, c in enumerate(tv("color.scenario.stackGrays")):
        rgb_of(c, f"color.scenario.stackGrays[{i}]")
    meta = tokens.get("$extensions", {}).get("theme", {})
    mode = meta.get("mode", "light")   # optional: a dark-mode token layer may set "dark"
    for name, c in (("ac", ac), ("py", py)):
        if saturation(c) <= 0.15:
            continue
        rgb = hex_to_rgb(c)
        chroma = max(rgb) - min(rgb) if rgb else 1.0
        documented = token_get(tokens, f"color.scenario.{name}").get("$extensions", {}).get("ibcs", {}).get("src") == "ORG"
        if documented and chroma <= 0.2:
            # A documented, low-chroma organisational ink (e.g. a blue-black) may still read as neutral.
            add("D8", "UN 3.2", "S", "check", f"{loc}:color.scenario.{name}", f"{c} is a tinted ink (chroma {chroma:.2f}, src ORG)",
                "Confirm it reads as neutral next to the impact colours and is documented in the notation manual.")
        else:
            add("D8", "UN 3.2", "M", "fail", f"{loc}:color.scenario.{name}", f"{c} is a hue, not a gray",
                "Use neutral scenario ink; a tinted ink must stay low-chroma and be documented (src ORG).")
    if contrast(ac, bg) < contrast(py, bg) * 1.5:
        add("D5", "UN 3.2", "M", "fail", f"{loc}:color.scenario.py", f"AC/PY contrast {contrast(ac, bg):.2f}/{contrast(py, bg):.2f}",
            "AC contrast against page must be at least 1.5 times PY contrast.")
    for i, c in enumerate(tv("color.scenario.stackGrays")):
        if contrast(c, bg) > contrast(ac, bg) + 0.001:
            add("D5", "UN 3.2", "M", "fail", f"{loc}:color.scenario.stackGrays[{i}]", "Stack fill exceeds AC contrast", "AC has highest fill contrast.")
    for scenario in ("pl", "bu"):
        if tv(f"color.scenario.{scenario}.fill").upper() != bg.upper():
            add("D6", "UN 3.2", "M", "fail", f"{loc}:color.scenario.{scenario}.fill", "Fill differs from page", "Outlined scenarios have empty fills.")
    if tv("color.scenario.fc.ground").upper() != bg.upper():
        add("D6", "UN 3.2", "M", "fail", f"{loc}:color.scenario.fc.ground", "FC ground differs from page", "Hatched scenario ground equals page.")
    for variant in ("", "cvd."):
        g, b = tv(f"color.variance.{variant}good"), tv(f"color.variance.{variant}bad")
        lg, lb = rel_lum(g), rel_lum(b)
        if (mode == "light" and lg <= lb) or (mode == "dark" and abs(lg - lb) < 0.08):
            add("E7", "UN 4.1", "M", "fail", f"{loc}:color.variance.{variant}good", f"good/bad luminance {lg:.3f}/{lb:.3f}",
                "Light: good brighter than bad. Dark: luminance gap >= 0.08 for grayscale reading.")
        for k in ("good", "bad", "neutral"):
            c = tv(f"color.variance.{variant}{k}")
            hue = colorsys.rgb_to_hsv(*rgb_of(c, f"color.variance.{variant}{k}"))[0] * 360
            allowed = impact_hue_ok(variant, k, c)
            if saturation(c) < 0.15:
                # A gray has no meaningful hue (colorsys reports 0 = red); it cannot carry impact.
                add("E6", "UN 4.1", "M", "fail", f"{loc}:color.variance.{variant}{k}", f"{c} is gray (no hue)",
                    "Impact colours need their hue family; grays are for bw.* (no-colour output) only.")
            elif not allowed:
                add("E6", "UN 4.1", "M", "fail", f"{loc}:color.variance.{variant}{k}", f"hue {hue:.0f} degrees",
                    "Keep green desirable, red undesirable, blue neutral; CVD desirable is blue-green.")
            if contrast(c, bg) < 3:
                # The bundled default green (measured from the IBCS figures) is kept as a known exception.
                default = mode == "light" and variant == "" and k == "good" and c.upper() == "#8CB400" and bg.upper() == "#FFFFFF"
                add("E6", "WCAG 1.4.11", "S" if default else "M", "check" if default else "fail",
                    f"{loc}:color.variance.{variant}{k}", f"contrast {contrast(c, bg):.2f}:1" + ("; bundled default" if default else ""),
                    "Variance graphics need >= 3:1 against the background; consider a darker green override (keep it brighter than bad).")
    for variant in ("", "cvd."):
        for k in ("good", "bad", "neutral"):
            p = f"color.variance.{variant}{k}Text"
            try:
                c = tv(p)
            except KeyError:
                continue   # a token set without text colours: variance numbers stay color.text.primary
            rgb_of(c, p)
            if contrast(c, bg) < 4.5:
                add("E6", "UN 4.1, WCAG 1.4.3", "M", "fail", f"{loc}:{p}", f"contrast {contrast(c, bg):.2f}:1",
                    "A tinted variance number needs >= 4.5:1 on the background: darken the text colour within its hue "
                    "family, or print variance numbers in color.text.primary.")
            if not impact_hue_ok(variant, k, c):
                add("E6", "UN 4.1", "M", "fail", f"{loc}:{p}", f"{c} leaves the {k} hue family",
                    "Text variants keep the hue of their impact colour (green / red / blue; CVD good blue-green).")
    for k in ("good", "bad", "neutral"):
        c = tv(f"color.variance.{k}")
        if 0.15 <= saturation(c) < 0.3:
            add("E6", "UN 4.1", "S", "check", f"{loc}:color.variance.{k}", f"{c} is nearly gray", "Impact colours must be distinguishable from scenario grays (use bw.* only for no-colour output).")
    for k in ("primary", "secondary"):
        c = tv(f"color.text.{k}")
        if contrast(c, bg) < 4.5:
            add("A2", "SI 1.2, WCAG 2.2", "M", "fail", f"{loc}:color.text.{k}", f"contrast {contrast(c, bg):.1f}:1", "Text needs ≥ 4.5:1 on the background.")
    on_ac = tv("color.text.onAc")
    if contrast(on_ac, ac) < 4.5:
        add("A2", "WCAG 2.2", "M", "fail", f"{loc}:color.text.onAc", f"contrast {contrast(on_ac, ac):.2f}:1 on AC", "Text on an AC-filled bar needs >= 4.5:1.")
    a, r = float(tv("geometry.barWidthRatio.absolute")), float(tv("geometry.barWidthRatio.relative"))
    if abs(a - 2 / 3) > 0.01 or abs(r - 1 / 3) > 0.01:
        add("D1", "UN 3.1", "M", "fail", f"{loc}:geometry.barWidthRatio", f"absolute {a}, relative {r}", "ISO 24896: 2/3 and 1/3 of category width.")
    if tv("number.sign.plus") != "+":
        add("B5", "UN 1.2", "M", "fail", f"{loc}:number.sign.plus", "plus sign changed", "Variances carry '+'.")
    if tv("number.maxDigits.chart") > 3 or tv("number.maxDigits.table") > 4:
        add("A14", "SI 5.2", "M", "fail", f"{loc}:number.maxDigits", "limit raised", "≤ 3 digits in charts, ≤ 4 in tables.")


# ----------------------------------------------------------------------------- theme

def lint_theme(theme: dict, loc, tokens=None):
    dc = theme.get("dataColors") or []
    sat = [c for c in dc if saturation(c) > 0.25]
    if len(sat) >= 3:
        add("A5", "SI 2.2", "M", "fail", f"{loc}:dataColors", f"{len(sat)} saturated series colours: {', '.join(sat[:6])}",
            "Series colours = grays (AC dark, PY light, PL white+outline, stack grays); colour only for impact/highlight.")
    elif sat:
        add("A5", "SI 2.2", "M", "check", f"{loc}:dataColors", f"saturated series colour(s): {', '.join(sat)}",
            "Confirm each has an analytical meaning (highlight), else make it gray.")
    bg = theme.get("background")
    if isinstance(bg, str) and not is_white(bg):
        add("A2", "SI 1.2", "S", "fail", f"{loc}:background", bg, "White background (color.background.page).")
    if tokens:
        for k in ("good", "bad", "neutral"):
            if k in theme:
                want = token_value(tokens, f"color.variance.{k}")
                if str(theme[k]).upper() != str(want).upper():
                    add("E6", "UN 4.1", "I", "check", f"{loc}:{k}", f"theme {theme[k]} ≠ token {want}",
                        "Generate the theme from the effective tokens (or record an ORG override).")
            else:
                add("E6", "UN 4.1", "I", "check", f"{loc}:{k}", "not set", "Set good/bad/neutral from color.variance.*.")
    for cls, spec in (theme.get("textClasses") or {}).items():
        face = (spec or {}).get("fontFace", "")
        if face and DECORATIVE_FONT.search(face):
            add("A6", "SI 2.3", "S", "fail", f"{loc}:textClasses.{cls}", face, "Plain sans-serif (typography.family.powerbi).")
    vs = (theme.get("visualStyles") or {})
    for vtype, by_style in vs.items():
        for style, objs in (by_style or {}).items():
            where = f"{loc}:visualStyles.{vtype}.{style}"
            def tprop(obj, prop):
                for e in (objs or {}).get(obj, []) or []:
                    if isinstance(e, dict) and prop in e:
                        return e[prop]
                return None
            if tprop("legend", "show") is True and vtype.lower() not in TWO_VALUE_AXES:
                add("C10", "UN 2.3", "S", "fail", where, "legend.show = true", "Integrate legends (labels at series), legend off.")
            for ax in ("valueAxis", "categoryAxis"):
                if tprop(ax, "gridlineShow") is True and vtype.lower() not in TWO_VALUE_AXES:
                    add("A8", "SI 3.1", "S", "check", where, f"{ax}.gridlineShow = true as default",
                        "Default gridlines off; keep them only where helpful (small multiples, dense charts).")
            for obj in ("border", "dropShadow"):
                # card chrome (page shell, fluent-cards): shapes behind the content may carry ring and shadow
                if tprop(obj, "show") is True and vtype.lower() not in BACKGROUND_TYPES:
                    add("A4", "SI 2.1", "S", "fail", where, f"{obj}.show = true",
                        "No frames or shadows on content visuals (card chrome belongs on the card shape behind it).")
            if tprop("background", "show") is True:
                add("A2", "SI 1.2", "S", "check", where, "visual background on", "Visual backgrounds off or white.")
            if tprop("labels", "labelDisplayUnits") == 0:
                add("A14", "SI 5.2, UN 1.2", "M", "check", where, "labelDisplayUnits = 0 (Auto)",
                    "Fix display units per scale group; Auto mixes k/m across visuals.")


# ----------------------------------------------------------------------------- vega-lite

DATUM_FIELD = re.compile(r"datum\[\s*['\"]([^'\"]+)['\"]\s*\]|datum\.([A-Za-z_]\w*)")
# optional input: read only behind a fallback, "isValid(datum['X']) ? datum['X'] : default"
OPTIONAL_FIELD = re.compile(r"^\s*optional\b|\(optional\b", re.I)
GUARDED_FIELD = re.compile(r"isValid\(\s*datum(?:\[\s*['\"]([^'\"]+)['\"]\s*\]|\.([A-Za-z_]\w*))\s*\)\s*\?")


DAX_VAR = re.compile(r"\bVAR\s+(\w+)\s*=\s*(.*?)(?=\bVAR\s+\w+\s*=|\bRETURN\b|$)", re.S | re.I)
TEXT_FILL = re.compile(r"<(?:text|tspan)\b[^>]*?fill=['\"]\s*(?:\"\s*&\s*(\w+)|(#[0-9A-Fa-f]{3,8}))", re.S)


def text_fill_hexes(expr: str) -> set[str]:
    """Hex colours that can reach the fill of a <text> in an SVG-in-DAX measure: literal fills and the
    VARs the fill references (followed through other VARs). Bars and pins may use graphic colours."""
    defs = {name.lower(): body for name, body in DAX_VAR.findall(expr)}
    out, seen = set(), set()
    def follow(name):
        if name in seen or name not in defs:
            return
        seen.add(name)
        body = defs[name]
        out.update(full_hex(h) for h in HEX_IN_TEXT.findall(body))
        for ref in re.findall(r"\b(_\w+)\b", body):
            follow(ref.lower())
    for var, lit in TEXT_FILL.findall(expr):
        if lit:
            out.add(full_hex(lit))
        else:
            follow(var.lower())
    return out


def produced_fields(node, out=None) -> set[str]:
    """Field names a spec creates itself: every transform 'as' and fold defaults (params are signals, not fields)."""
    out = set() if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "as":
                for n in (v if isinstance(v, list) else [v]):
                    if isinstance(n, str):
                        out.add(n)
            elif k == "fold" and "as" not in node:
                out.update(("key", "value"))
            produced_fields(v, out)
    elif isinstance(node, list):
        for v in node:
            produced_fields(v, out)
    return out


def used_fields(spec) -> set[str]:
    """Field names read from the data: encoding/transform 'field', 'groupby', and datum['x'] / datum.x."""
    out = set()
    def walk(node, in_data):
        if isinstance(node, dict):
            for k, v in node.items():
                if in_data and k == "field" and isinstance(v, str):
                    out.add(v.replace("\\.", "."))
                if in_data and k in ("groupby", "fold") and isinstance(v, list):
                    out.update(x for x in v if isinstance(x, str))
                walk(v, in_data or k in ("encoding", "transform"))
        elif isinstance(node, list):
            for v in node:
                walk(v, in_data)
    walk(spec, False)
    for text in spec_texts(spec, skip=PROSE_KEYS):
        for a, b in DATUM_FIELD.findall(text):
            out.add(a or b)
    # datum.label / datum.value / datum.index in axis, legend and header expressions are Vega's own
    # guide datum, not data fields: drop those names unless the spec also reads them elsewhere
    guide = {(a or b) for node in guide_nodes(spec) for text in spec_texts(node, skip=PROSE_KEYS)
             for a, b in DATUM_FIELD.findall(text)} & GUIDE_DATUM
    if guide:
        rest = {(a or b) for text in spec_texts(spec, skip=PROSE_KEYS | GUIDE_KEYS)
                for a, b in DATUM_FIELD.findall(text)}
        out -= guide - rest - field_names(spec)
    return out


def upstream_fields(spec) -> set[str]:
    """Fields a top-level transform creates before any top-level transform reads them: a fold or
    calculate prepended to a template's own transforms supplies those fields like the dataset does."""
    out, read = set(), set()
    for t in spec.get("transform") or []:
        if not isinstance(t, dict):
            continue
        out |= produced_fields(t) - read
        read |= used_fields({"transform": [t]})
    return out


def guide_nodes(node):
    """Every axis / legend / header object of a spec (their expressions see a guide datum)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in GUIDE_KEYS and isinstance(v, dict):
                yield v
            else:
                yield from guide_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from guide_nodes(v)


def field_names(spec) -> set[str]:
    """Names used as encoding/transform 'field' values (never guide datums)."""
    out = set()
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "field" and isinstance(v, str):
                    out.add(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(spec)
    return out


def lint_vegalite(spec, loc, palette=None, dataset_fields=None):
    """dataset_fields: the column names the host supplies (a Deneb visual's dataset), if known."""
    if not isinstance(spec, dict):
        return
    if dataset_fields:
        optional = {a or b for t in spec_texts(spec, skip=PROSE_KEYS) for a, b in GUARDED_FIELD.findall(t)}
        # fields the template documents as optional (usermeta.ibcs.fields: "optional …"): unbound is fine
        declared = ((spec.get("usermeta") or {}).get("ibcs") or {}).get("fields") or {}
        optional |= {k for k, v in declared.items() if isinstance(v, str) and OPTIONAL_FIELD.search(v)}
        # a template that lists requiredFields declares every other documented field optional
        # (scenario measures such as BU, FC or PL that this visual does not bind)
        ibcs = (spec.get("usermeta") or {}).get("ibcs") or {}
        required = ibcs.get("requiredFields")
        if isinstance(required, list):
            # scenario knobs name fields too: refScenario 'PY' needs PY bound, minuend 'FC' needs FC
            chosen = {p.get("value") for p in spec.get("params", []) if isinstance(p, dict)
                      and p.get("name") in SCENARIO_KNOBS and isinstance(p.get("value"), str)}
            optional |= set(declared) - set(required) - chosen
        groups = [g for g in ibcs.get("requiredAnyOf") or [] if isinstance(g, list)]
        supplied = set(dataset_fields) | upstream_fields(spec)
        if groups and not any(set(g) <= supplied for g in groups):
            add("LINT", "-", "S", "check", f"{loc}:fields",
                "none of the field sets " + " | ".join("+".join(g) for g in groups) + " is bound",
                "The template needs one of these sets (see its field table); without it the chart has no base or total.")
        missing = sorted(f for f in used_fields(spec) - produced_fields(spec) - set(dataset_fields) - optional
                         if not f.startswith("__"))
        if missing:
            add("LINT", "-", "S", "check", f"{loc}:fields", f"field(s) not in the visual's dataset: {', '.join(missing[:6])}",
                "Deneb names dataset fields by the projection's display name; a filter or encoding on another name "
                "silently drops rows (an empty chart) or draws nothing.")
    if palette:
        hexes = sorted({full_hex(h) for h in HEX_IN_TEXT.findall(json.dumps(spec))})
        stray = [h for h in hexes if h not in palette and saturation(h) > 0.25]
        if stray:
            add("A5", "SI 2.2", "M", "check", f"{loc}:colours", f"non-token colours {', '.join(stray[:5])}",
                "Colours (also in params and mark properties) only from tokens and only with analytical meaning.")
    cfg = spec.get("config") or {}
    bg = spec.get("background", cfg.get("background"))
    if isinstance(bg, str) and bg.startswith("#") and not is_white(bg):
        add("A2", "SI 1.2", "S", "fail", f"{loc}:background", bg, "White background.")
    view = cfg.get("view", {}) if isinstance(cfg.get("view"), dict) else {}
    if "stroke" not in view and "view" not in spec:
        add("A4", "SI 2.1", "S", "check", f"{loc}:config.view.stroke", "default view frame (#ddd) not disabled",
            "Set config.view.stroke: null.")
    axis_cfg = cfg.get("axis", {}) if isinstance(cfg.get("axis"), dict) else {}
    if axis_cfg.get("grid") is True:
        add("A8", "SI 3.1", "S", "check", f"{loc}:config.axis.grid", "grid on by default",
            "Grid off unless helpful (small multiples, dense series, scatter/bubble); label the data.")
    rng = cfg.get("range", {}) if isinstance(cfg.get("range"), dict) else {}
    if isinstance(rng.get("category"), (dict, str)):
        add("A5", "SI 2.2", "M", "check", f"{loc}:config.range.category", str(rng.get("category"))[:60], "No categorical palettes; grays + meaning-bound colours.")

    def walk(node, path):
        if not isinstance(node, dict):
            return
        mark = node.get("mark")
        mtype = mark.get("type") if isinstance(mark, dict) else mark
        if mtype == "arc":
            add("K9", "EX 2.1", "S", "fail", f"{loc}:{path}.mark", "arc mark (pie/donut)", "Sorted bars or 100 % stacked columns.")
        enc = node.get("encoding") or {}
        for ch, e in enc.items():
            if not isinstance(e, dict):
                continue
            sc = e.get("scale") or {}
            if isinstance(sc, dict):
                value_axis = ch in ("x", "y", "x2", "y2") and is_value_channel(e)
                indexed = is_indexed(e, sc)
                dom0 = sc.get("domain")
                spans_zero = (isinstance(dom0, list) and len(dom0) == 2 and all(is_number(x) for x in dom0)
                              and min(dom0) <= 0 <= max(dom0)) or sc.get("domainMid") == 0
                if sc.get("zero") is False and value_axis and not spans_zero:
                    add("G1", "CH 1.1", "M", "check" if indexed else "fail", f"{loc}:{path}.encoding.{ch}.scale.zero", "zero: false",
                        "Indexed zoom near 100 % is allowed with category labels on the 100 % line" if indexed else "Value axes start at zero.")
                if str(sc.get("type", "")).lower() in ("log", "symlog"):
                    add("G2", "CH 1.2", "M", "check", f"{loc}:{path}.encoding.{ch}.scale.type", sc.get("type"),
                        "Linear scale, unless relative growth over orders of magnitude, clearly indicated, audience familiar.")
                dom = sc.get("domain")
                if value_axis and isinstance(dom, list) and len(dom) == 2 and all(is_number(x) for x in dom) \
                        and (min(dom) > 0 or max(dom) < 0):   # the domain excludes 0
                    add("G1", "CH 1.1", "M", "check" if indexed else "fail", f"{loc}:{path}.encoding.{ch}.scale.domain", str(dom),
                        "Indexed zoom near 100 % is allowed with category labels on the 100 % line" if indexed else "Domain must include 0.")
                if sc.get("scheme"):
                    add("A5", "SI 2.2", "M", "check", f"{loc}:{path}.encoding.{ch}.scale.scheme", sc.get("scheme"), "No decorative schemes; tokens only.")
            ax = e.get("axis")
            if isinstance(ax, dict):
                ang = ax.get("labelAngle")
                if isinstance(ang, (int, float)) and ang % 360 != 0:
                    add("C12", "UN 2.3", "M", "fail", f"{loc}:{path}.encoding.{ch}.axis.labelAngle", str(ang), "Labels horizontal; use bars for long labels.")
                if ax.get("grid") is True:
                    add("A8", "SI 3.1", "S", "check", f"{loc}:{path}.encoding.{ch}.axis.grid", "grid on",
                        "Grid off unless helpful (small multiples, dense series, scatter/bubble).")
            two_value_axes = all(isinstance(enc.get(k), dict) and enc[k].get("type") == "quantitative" for k in ("x", "y"))
            if ch == "color" and e.get("field") and e.get("type") == "nominal":
                if e.get("legend", "default") is not None and not two_value_axes:
                    add("C10", "UN 2.3", "S", "check", f"{loc}:{path}.encoding.color.legend", "legend not null", "Integrate legends; legend: null.")
                rng2 = (sc or {}).get("range") if isinstance(sc, dict) else None
                if not rng2:
                    add("A5", "SI 2.2", "M", "check", f"{loc}:{path}.encoding.color", f"nominal colour by {e.get('field')} without explicit range",
                        "Map scenarios/series to token grays explicitly.")
                # stray colours in an explicit range are reported once per spec (see the top of lint_vegalite)
        for key in ("layer", "hconcat", "vconcat", "concat"):
            for i, child in enumerate(node.get(key) or []):
                walk(child, f"{path}.{key}[{i}]")
        if isinstance(node.get("spec"), dict):
            walk(node["spec"], f"{path}.spec")
    walk(spec, "$")


# ----------------------------------------------------------------------------- pbir

TITLE_BAND_PX = 120   # textboxes whose top edge lies in the header band are treated as title text


def looks_like_title(line: str) -> bool:
    """Title lines are short labels; key messages are sentences (end with '.', or > 12 words)."""
    s = line.strip()
    return bool(s) and not s.endswith((".", "!", "?")) and len(s.split()) <= 12


TIME_FIELD = re.compile(r"year|date|month|quarter|week|day|period|time", re.I)


def is_value_channel(e: dict) -> bool:
    """A positional channel is a value axis only if quantitative and not a disguised time field."""
    if e.get("type") != "quantitative" and not e.get("aggregate"):
        return False
    return not TIME_FIELD.search(str(e.get("field", "")))


def is_indexed(e: dict, sc: dict) -> bool:
    dom = sc.get("domain") if isinstance(sc, dict) else None
    near100 = isinstance(dom, list) and len(dom) == 2 and all(isinstance(x, (int, float)) for x in dom) \
        and dom[0] < 100 < dom[1] and dom[0] >= 50 or (isinstance(dom, list) and len(dom) == 2
        and all(isinstance(x, (int, float)) for x in dom) and dom[0] < 1 < dom[1] and dom[0] >= 0.5)
    return bool(near100 or re.search(r"index", str(e.get("field", "")) + str(e.get("title", "")), re.I))


def query_fields(visual: dict):
    """Yield (role, entity, property, nativeQueryRef/displayName) from visual.query.queryState."""
    qs = ((visual.get("query") or {}).get("queryState") or {})
    for role, block in qs.items():
        for proj in (block or {}).get("projections", []) or []:
            f = proj.get("field", {})
            ent = prop = None
            for kind in ("Column", "Measure", "Aggregation", "HierarchyLevel"):
                if kind in f:
                    node = f[kind]
                    if kind == "Aggregation":
                        node = node.get("Expression", {}).get("Column", {})
                    if kind == "HierarchyLevel":
                        prop = node.get("Level")
                        node = node.get("Expression", {}).get("Hierarchy", {})
                        ent = node.get("Expression", {}).get("SourceRef", {}).get("Entity")
                        break
                    ent = node.get("Expression", {}).get("SourceRef", {}).get("Entity")
                    prop = node.get("Property")
                    break
            label = proj.get("displayName") or proj.get("nativeQueryRef") or proj.get("queryRef") or ""
            yield role, ent or "", prop or "", label


def textbox_text(visual: dict) -> str:
    out = []
    for e in (visual.get("objects") or {}).get("general", []) or []:
        for para in (e.get("properties", {}).get("paragraphs") or []):
            for run in para.get("textRuns", []) or []:
                out.append(run.get("value", ""))
            out.append("\n")
    return "".join(out).strip()


def find_definition(path: Path):
    path = path.resolve()   # so that report_root = d.parent also works for "." inside definition/
    for cand in (path, path / "definition"):
        if (cand / "report.json").exists() and (cand / "pages").is_dir():
            return cand
    hits = sorted(path.glob("**/definition/report.json"))
    return hits[0].parent if hits else None


HEX_IN_TEXT = re.compile(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Za-z])")
ABS_CALL = re.compile(r"\bABS\s*\(", re.I)
VARIANCE_ARG = re.compile(r"Δ|delta|variance|\bvar\b|\bdiff|\bd(?:py|pl|bu|fc)\b|impact", re.I)
ABS_DENOMINATOR = re.compile(r"(?:/\s*|\bDIVIDE\s*\((?:[^(),]|\([^()]*\))*,\s*)ABS\s*\(", re.I)


def call_argument(text: str, open_paren: int) -> str:
    """Text between the parenthesis at open_paren and its matching closing one."""
    depth = 0
    for i in range(open_paren, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i]
    return text[open_paren + 1:]


def full_hex(h: str) -> str:
    h = h.lstrip("#")
    return "#" + ("".join(c * 2 for c in h) if len(h) == 3 else h).upper()


def lint_report_extensions(d: Path, palette, tokens=None) -> dict:
    """Report-level measures (definition/reportExtensions.json) of a report on a shared model.

    Returns {(entity, measure name): measure dict} for the binding checks of lint_pbir."""
    f = d / "reportExtensions.json"
    if not f.is_file():
        return {}
    try:
        ext = load_json(f)
    except json.JSONDecodeError:
        add("LINT", "-", "I", "check", f.name, "reportExtensions.json is not parseable JSON", "Review the report measures manually.")
        return {}
    index = {(ent.get("name"), m.get("name")): m for ent in ext.get("entities") or [] for m in ent.get("measures") or []}
    no_refs = sorted(name for (_, name), m in index.items() if "references" not in m)
    if no_refs:
        add("LINT", "-", "I", "check", f.name, f"{len(no_refs)} report measure(s) without 'references': {', '.join(no_refs[:5])}",
            "Power BI Desktop writes 'references' (the measures each one uses; report measures with "
            "\"schema\": \"extension\"). ibcs-power-bi scripts/report_measures.py --fix writes them; not proven required by the service.")
    bg = token_value(tokens, "color.background.page") if tokens else "#FFFFFF"
    graphic = {}
    if tokens:
        for variant in ("", "cvd."):
            for k in ("good", "bad", "neutral"):
                try:
                    graphic[full_hex(token_value(tokens, f"color.variance.{variant}{k}"))] = f"color.variance.{variant}{k}"
                except (KeyError, TypeError):
                    pass
    for ent in ext.get("entities") or []:
        for m in ent.get("measures") or []:
            mloc = f"{f.name}:{ent.get('name', '?')}[{m.get('name', '?')}]"
            if m.get("hidden") is True:
                add("LINT", "-", "M", "fail", mloc, '"hidden": true on a report-level measure',
                    "Remove it: in the Power BI service every visual that uses a hidden report-level measure (or a "
                    "measure referencing one) fails with \"Something's wrong with one or more fields\". Group helper "
                    "measures in a displayFolder instead.")
            expr = m.get("expression") or ""
            if isinstance(expr, list):
                expr = "\n".join(map(str, expr))
            hexes = sorted({full_hex(h) for h in HEX_IN_TEXT.findall(expr)})
            if palette:
                stray = [h for h in hexes if h not in palette and saturation(h) > 0.25]
                if stray:
                    add("A5", "SI 2.2", "M", "check", mloc, f"non-token colours {', '.join(stray[:5])}",
                        "Colours only from tokens (generate the measure from the effective tokens) and only with analytical meaning.")
            if "<text" in expr.lower():
                text_hexes = text_fill_hexes(expr)
                weak = [f"{h} ({graphic[h]}, {contrast(h, bg):.1f}:1)" for h in text_hexes if h in graphic and contrast(h, bg) < 4.5]
                if weak:
                    add("E6", "UN 4.1, WCAG 1.4.3", "S", "check", mloc, f"impact colour below 4.5:1 in a measure that draws text: {'; '.join(weak)}",
                        "If it colours a variance number, use color.variance.*Text (>= 4.5:1) or color.text.primary; bars and pins keep the graphic colour.")
            for mm in ABS_CALL.finditer(expr):
                arg = call_argument(expr, mm.end() - 1)
                if VARIANCE_ARG.search(arg):
                    add("E14", "UN 4.1", "S", "check", mloc, f"ABS({' '.join(arg.split())[:50]})",
                        "ABS of a variance is fine for a bar or pin length only; sign, impact colour and labels use the signed variance.")
            if ABS_DENOMINATOR.search(expr):
                add("E14", "UN 4.1", "M", "check", mloc, "division by ABS(...)",
                    "Relative variances divide by the signed reference; reference <= 0 or blank -> N/A (never ABS).")
    return index


def measure_refs(node):
    """Yield every {'Measure': {...}} node of a visual.json (projections, sort, filters, objects)."""
    if isinstance(node, dict):
        m = node.get("Measure")
        if isinstance(m, dict) and "Property" in m:
            yield m
        for v in node.values():
            yield from measure_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from measure_refs(v)


def lint_visual_bindings(vfile: dict, v: dict, vloc: str, report_measures: dict):
    """Bindings that break a visual in the service although the measures themselves are fine."""
    if report_measures:
        unmarked = []
        for m in measure_refs(vfile):
            src = (m.get("Expression") or {}).get("SourceRef") or {}
            if (src.get("Entity"), m.get("Property")) in report_measures and src.get("Schema") != "extension":
                unmarked.append(m["Property"])
        if unmarked:
            names = sorted(set(unmarked))
            add("LINT", "-", "M", "fail", vloc,
                f"{len(unmarked)} binding(s) to report measure(s) without \"Schema\": \"extension\": {', '.join(names[:4])}",
                "Write SourceRef {\"Schema\": \"extension\", \"Entity\": ...} for every report-level measure (projections, "
                "sort, filters) — ibcs-power-bi scripts/report_measures.py --fix does it; without it the service looks "
                "the name up in the model and the visual fails with Missing_References.")
    qs = ((v.get("query") or {}).get("queryState") or {})
    for role, block in qs.items():
        for proj in (block or {}).get("projections", []) or []:
            vtype = str(v.get("visualType", "")).lower()
            if proj.get("active") is True and "slicer" not in vtype and "HierarchyLevel" not in (proj.get("field") or {}):
                # slicers (Desktop writes it) and drill hierarchy levels may be active
                add("LINT", "-", "M", "fail", vloc, f"\"active\": true on {proj.get('queryRef', '?')} ({role})",
                    "Remove it (ibcs-power-bi scripts/report_measures.py --fix): 'active' belongs to slicers and drill "
                    "hierarchies. On a table column it collapses the measure columns and adds a blank row.")
    if str(v.get("visualType", "")).lower() in ("tableex", "pivottable"):
        objects = v.get("objects") or {}
        img_w = obj_prop(objects, "grid", "imageWidth")
        if is_number(img_w):
            image_cols = {f"{e}.{n}" for (e, n), m in report_measures.items() if str(m.get("dataCategory", "")).lower() == "imageurl"}
            for e in objects.get("columnWidth") or []:
                ref = ((e.get("selector") or {}).get("metadata")) or ""
                w = literal((e.get("properties") or {}).get("value"))
                if ref in image_cols and is_number(w) and w < img_w + 20:
                    add("LINT", "-", "S", "fail" if w >= img_w else "check", vloc,
                        f"image column {ref} is {w:g} px wide, grid.imageWidth {img_w:g} px",
                        "grid.imageWidth applies to every image column: give the SVGs of one table the same width "
                        "and make each image column at least imageWidth + 20 px, or the images are clipped and the "
                        "service draws a stray '.' at the right end of every row (KPI cards: one card per visual).")


SCALE_FIELD = re.compile(r"max|min|scale|pxperunit|divisor", re.I)


def lint_deneb_scale(spec: dict, loc: str, dataset: list):
    """Scale knobs of the bundled Deneb templates (ibcs-deneb): one scale mechanism, no blank category."""
    params = {p.get("name"): p.get("value") for p in spec.get("params") or [] if isinstance(p, dict)}
    if params.get("pxPerUnit") not in (None, 0) and any(params.get(k) not in (None, 0) for k in ("yMax", "xMax")):
        add("G8", "CH 4.1", "S", "check", f"{loc}:params", "pxPerUnit and yMax/xMax both set",
            "A scale group is px per unit (each chart sized to its own data); yMax/xMax only for equally sized visuals.")
    if any(SCALE_FIELD.search(f or "") for f in dataset):
        first = (spec.get("transform") or [{}])[0]
        if not (isinstance(first, dict) and "isValid(" in str(first.get("filter", ""))):
            add("LINT", "-", "S", "check", f"{loc}:transform[0]", "constant scale field bound without a blank-category filter",
                "A constant measure (YMax, PxPerUnit, …) returns a value for the blank category row too: make the first "
                "transform filter the blank category (\"isValid(datum['Period']) && datum['Period'] !== ''\").")


# value axis of the bundled ibcs-deneb templates (usermeta.ibcs.template); relative templates (pins,
# scatter) have their own % scale and are not members of a unit scale group
DENEB_VALUE_AXIS = {"column-two-tier-variance": "height", "column-version-axis": "height",
                    "stacked-columns": "height", "line-scenarios": "height",
                    "small-multiples-columns": "height", "bar-structure-variance": "width",
                    "waterfall-variance": "width", "waterfall-calculation": "width"}
DOMAIN_FIELD = re.compile(r"^(?:YMax|YMin|XMax|XMin|VarMin|VarMax)$")
DOMAIN_KNOBS = ("yMax", "xMax", "varMin", "varMax")
CHAR_PX = 7          # ≈ px per character at 9–12 pt Segoe UI (scale_layout.py uses the same estimate)
SIZE_TOLERANCE_PX = 2


def deneb_info(vfile: dict, spec: dict, dataset_fields: list) -> dict:
    """What the scale-group checks need from one embedded Deneb spec."""
    ibcs = (spec.get("usermeta") or {}).get("ibcs") or {}
    params = {p.get("name"): p.get("value") for p in spec.get("params") or [] if isinstance(p, dict)}
    pos = vfile.get("position") or {}
    domains = sorted(f"{e}[{p}]" for lbl, e, p in dataset_fields if DOMAIN_FIELD.match(lbl or ""))
    domains += [f"{k}={params[k]:g}" for k in DOMAIN_KNOBS if is_number(params.get(k)) and params[k] != 0]
    ppu = params.get("pxPerUnit") if is_number(params.get("pxPerUnit")) and params.get("pxPerUnit") else None
    ppu_field = next((f"{e}[{p}]" for lbl, e, p in dataset_fields if (lbl or "").lower() == "pxperunit"), None)
    # the visual's own padding (visualContainerObjects.padding) is inside its position: the Deneb
    # container is position minus padding (a theme-level padding is not visible here)
    vco = ((vfile.get("visual") or {}).get("visualContainerObjects")) or {}
    padv = {k: obj_prop(vco, "padding", k) for k in ("top", "bottom", "left", "right")}
    padv = {k: float(v) if is_number(v) else 0.0 for k, v in padv.items()}
    return {"template": str(ibcs.get("template") or ""), "params": params,
            "height": pos.get("height"), "width": pos.get("width"), "domains": domains,
            "padH": padv["top"] + padv["bottom"], "padW": padv["left"] + padv["right"],
            "ppu": ppu, "ppuField": ppu_field,
            "own": params.get("periodType") == "year" or bool(params.get("scaleBand"))}


def lint_scale_groups(infos: dict, ploc: str, layout_rows: dict):
    """CH 4.1 / UN 4.1 for the bundled Deneb templates on one page: one px per unit per unit and
    every visual sized to its own data. The linter cannot see the queried data, so it checks the
    mechanism: domain knobs are not a scale, px per unit is set and equal, and (with --layout) each
    visual has the size scale_layout.py computed."""
    absolute = {n: i for n, i in infos.items() if i["template"] in DENEB_VALUE_AXIS}
    # 1. a shared domain (YMax field or yMax knob) on visuals of different size = different scales
    by_domain: dict[str, list[str]] = {}
    for n, i in absolute.items():
        for d in i["domains"]:
            by_domain.setdefault(d, []).append(n)
    for d, names in sorted(by_domain.items()):
        no_ppu = [n for n in names if not (absolute[n]["ppu"] or absolute[n]["ppuField"])]
        if not no_ppu:
            continue
        ext = {n: absolute[n][DENEB_VALUE_AXIS[absolute[n]["template"]]] for n in names}
        if len(names) > 1 and len({round(float(v or 0)) for v in ext.values()}) > 1:
            add("G8", "CH 4.1, CH 4.2", "M", "fail", f"{ploc}: {', '.join(names)}",
                f"domain {d} shared by visuals of different size ({', '.join(f'{n} {v:g} px' for n, v in ext.items())})",
                "A shared domain is not a shared scale: set one pxPerUnit (knob or PxPerUnit field) on every member "
                "and size each visual with scale_layout.py.")
        else:
            add("G8", "CH 4.1, CH 4.2", "S", "fail", f"{ploc}: {', '.join(no_ppu)}",
                f"value domain {d} without pxPerUnit",
                "A domain is not a scale: with SVG measures, native visuals or Deneb visuals of another size on the "
                "same unit the charts are on different scales (and a small chart is mostly empty). Use pxPerUnit "
                "and size each visual with scale_layout.py; keep a domain only for visuals of identical size.")
    # 2. px per unit set and equal across the group (own-scale members excepted)
    plain = {n: i for n, i in absolute.items() if not i["own"]}
    missing = [n for n, i in plain.items() if not (i["ppu"] or i["ppuField"]) and not i["domains"]]
    if len(absolute) > 1 and missing:
        add("G8", "CH 4.1", "S", "check", f"{ploc}: {', '.join(missing)}",
            "absolute Deneb visuals without pxPerUnit: each fits its own data (auto scale)",
            "Same unit on the page = one px per unit on every member (scale_layout.py); different units: ignore.")
    values = {i["ppu"] for i in plain.values() if i["ppu"]}
    fields = {i["ppuField"] for i in plain.values() if i["ppuField"]}
    if len(values) > 1 or len(fields) > 1:
        add("G8", "CH 4.1", "S", "check", ploc,
            "different px per unit: " + ", ".join(f"{n} {i['ppu'] or i['ppuField']}" for n, i in plain.items()
                                                    if i["ppu"] or i["ppuField"]),
            "Members of one unit share one px per unit; a different unit is a different group (confirm).")
    # 3. a Total / year visual on its own scale is marked (scale band or footnote)
    group_ppu = values | fields
    for n, i in absolute.items():
        if i["params"].get("periodType") == "year" and group_ppu and \
                (i["ppu"] or i["ppuField"]) not in group_ppu and not i["params"].get("scaleBand"):
            add("F6", "UN 5.2, CH 4.3", "S", "check", f"{ploc} / {n}",
                "Total/year visual on its own scale without a scale band",
                "Mark the different scale: the same scaleBand value here and in the months, or a footnote.")
    # 4. sizes computed by scale_layout.py (--layout)
    for n, row in layout_rows.items():
        if n not in infos:
            continue
        i = infos[n]
        dim = row.get("dimension")
        dim = "height" if dim in ("height", "panelHeight") and "visualHeightPx" not in row else dim
        want = row.get("visualHeightPx") or row.get("containerPx")
        is_h = dim in ("height", "panelHeight")
        have = i.get("height") if is_h else i.get("width")
        pad = (i.get("padH") if is_h else i.get("padW")) or 0
        if is_number(want) and is_number(have) and abs(float(have) - pad - float(want)) > SIZE_TOLERANCE_PX:
            shown = f"{dim} {have:g} px" + (f" − padding {pad:g} = {float(have) - pad:g} px" if pad else "")
            add("G8", "CH 4.1, CH 4.2", "M", "fail", f"{ploc} / {n}",
                f"{shown}, scale_layout.py computed {want:g} px",
                "Set the visual's position to the computed size + its padding (to_pbir.py --pos), or recompute the group.")
        lppu = row.get("_pxPerUnit")
        if lppu and not row.get("own") and i["ppu"] and abs(float(i["ppu"]) - float(lppu)) > 1e-6:
            add("G8", "CH 4.1", "M", "fail", f"{ploc} / {n}", f"pxPerUnit {i['ppu']:g}, the group's is {lppu:g}",
                "Set the group's px per unit on every member.")
        for k, v in (row.get("setParams") or {}).items():
            if is_number(i["params"].get(k)) and float(i["params"][k]) < float(v):
                add("LINT", "-", "S", "fail", f"{ploc} / {n}", f"knob {k} = {i['params'][k]:g}, labels need {v}",
                    f"Set {k} = {v} (scale_layout.py setParams): value labels are cut otherwise.")
    for n in layout_rows:
        if n not in infos and not layout_rows[n].get("_page_mismatch"):
            layout_rows[n]["_unseen"] = layout_rows[n].get("_unseen", 0) + 1


def header_text(objects: dict) -> str | None:
    t = obj_prop(objects, "header", "text")
    return t if isinstance(t, str) else None


def lint_truncation(vfile: dict, v: dict, vt: str, vloc: str, objects: dict, vco: dict):
    """Slicer headers and visual titles that do not fit their visual are cut with an ellipsis."""
    width = (vfile.get("position") or {}).get("width")
    if not is_number(width):
        return
    texts = []
    if vt == "slicer":
        texts.append(("slicer header", header_text(objects)))
    title = obj_prop(vco, "title", "text")
    if obj_prop(vco, "title", "show") is not False:
        texts.append(("title", title if isinstance(title, str) else None))
    for what, text in texts:
        if text and CHAR_PX * len(text) + 16 > float(width):
            add("LINT", "UN 2.2", "S", "fail", vloc,
                f"{what} '{text[:60]}' ({len(text)} chars) is cut at {width:g} px",
                "Short slicer titles (Company, Period); the explanation ('all = …', 'none = …') goes into the scope "
                f"chips or a footnote. Fits about {int((float(width) - 16) // CHAR_PX)} characters.")


TEXT_TYPES = {"textbox", "card", "cardvisual", "multirowcard"}
BACKGROUND_TYPES = {"shape", "basicshape"}
RHYTHM_GAP_PX = 12        # page shell: ≥ 12 px between the last title line and the slicer labels
EMPTY_BOTTOM_PX = 24      # page shell: more empty space than this at a card's bottom is a hole


def visual_box(vfile: dict, vtl: str, vloc: str, vco: dict) -> dict:
    """Position and own padding of one visual (padding set in the theme only is not visible here)."""
    pos = vfile.get("position") or {}
    pad = {k: obj_prop(vco, "padding", k) for k in ("top", "bottom", "left", "right")}
    pad = {k: float(v) if is_number(v) else 0.0 for k, v in pad.items()}
    num = {k: float(pos[k]) if is_number(pos.get(k)) else None for k in ("x", "y", "width", "height")}
    return {"type": vtl, "loc": vloc, "pad": pad, **num}


def lint_page_geometry(boxes: list[dict]):
    """Page-shell rhythm: slicer labels clear of the title lines; no empty bottom inside a card."""
    ok = [b for b in boxes if None not in (b["x"], b["y"], b["width"], b["height"])]
    shapes = [b for b in ok if b["type"] in BACKGROUND_TYPES]

    def within(c, bg):
        return c["x"] >= bg["x"] - 1 and c["y"] >= bg["y"] - 1 and \
            c["x"] + c["width"] <= bg["x"] + bg["width"] + 1 and c["y"] + c["height"] <= bg["y"] + bg["height"] + 1

    for b in (b for b in boxes if b.get("needsCard")):
        if not any(None not in (b["x"], b["y"]) and within(b, s) for s in shapes):
            add("A2", "SI 1.2", "S", "fail", b["loc"], "visual without a white background on a grey canvas",
                "Page shell: content sits on a white card: a card shape behind it (--shell fluent-cards) or a white "
                "visual background (--shell cards), so data never sits on grey.")

    def overlap_x(a, b):
        return min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"]) > 0

    for s in (b for b in ok if b["type"] == "slicer"):
        top = s["y"] + s["pad"]["top"]
        above = [t for t in ok if t["type"] in TEXT_TYPES and overlap_x(t, s)
                 and t["y"] + t["height"] - t["pad"]["bottom"] <= top + 1 and t["y"] < s["y"]]
        if not above:
            continue
        t = max(above, key=lambda b: b["y"] + b["height"] - b["pad"]["bottom"])
        gap = top - (t["y"] + t["height"] - t["pad"]["bottom"])
        if gap < RHYTHM_GAP_PX:
            add("LINT", "UN 2.2", "S", "fail", s["loc"],
                f"slicer labels {gap:g} px below the title text box above ({t['loc'].split(' / ')[-1]})",
                f"Header rhythm: message, 12 px, three title lines, at least {RHYTHM_GAP_PX} px, slicer labels "
                "(page-shell.md §3): give the slicer padding top 12 or move it down.")
    for bg in shapes:
        inside = [c for c in ok if c is not bg and c["type"] not in BACKGROUND_TYPES and within(c, bg)]
        if len(inside) < 2:
            continue
        empty = bg["y"] + bg["height"] - max(c["y"] + c["height"] for c in inside)
        if empty > EMPTY_BOTTOM_PX:
            add("LINT", "SI 1.2", "S", "fail", bg["loc"],
                f"card background ends {empty:g} px below its last visual",
                "Card height = content + its bottom padding (page-shell.md §5): shorten the card background, "
                f"or the visuals' own bottom padding takes the space (more than {EMPTY_BOTTOM_PX} px is a hole).")


def lint_pbir(path: Path, tokens=None, layouts=None):
    d = find_definition(path)
    if d is None:
        print(f"error: no PBIR definition/report.json under {path}", file=sys.stderr)
        sys.exit(2)
    report_root = d.parent
    palette = palette_from_tokens(tokens) if tokens else set()
    rep = load_json(d / "report.json")
    custom = ((rep.get("themeCollection") or {}).get("customTheme") or {})
    if custom.get("name"):
        name = custom["name"]
        cands = list((report_root / "StaticResources").glob(f"**/{name}")) + \
            list((report_root / "StaticResources").glob(f"**/{name}.json"))
        if cands:
            theme_doc = load_json(cands[0])
            lint_theme(theme_doc, cands[0].relative_to(report_root.parent), tokens)
        else:
            add("A5", "SI 2.2", "I", "check", "report.json:themeCollection", f"custom theme '{name}' not found", "Check StaticResources/RegisteredResources.")
    else:
        add("A5", "SI 2.2", "S", "check", "report.json:themeCollection", "no custom theme",
            "Default theme = rainbow palette; apply a theme generated from the IBCS tokens.")

    report_measures = lint_report_extensions(d, palette, tokens)
    theme_doc = locals().get("theme_doc") or {}
    star = ((theme_doc.get("visualStyles") or {}).get("*") or {}).get("*") or {}
    theme_card = any(e.get("show") is True for e in star.get("background", []) or [] if isinstance(e, dict)) and \
        all(is_white(e.get("color", {}).get("solid", {}).get("color", "#FFFFFF"))
            for e in star.get("background", []) or [] if isinstance(e, dict))
    layout_rows: dict[str, dict] = {}
    for lf in layouts or []:
        doc = load_json(Path(lf))
        for r in doc.get("members", []):
            if r.get("visual"):
                layout_rows[r["visual"]] = dict(r, _pxPerUnit=doc.get("pxPerUnit"),
                                                own=r.get("own") or r.get("dataRange") == 0)

    for page_json in sorted((d / "pages").glob("*/page.json")):
        page = load_json(page_json)
        pname = page.get("displayName") or page_json.parent.name
        ploc = f"page '{pname}'"
        canvas = False   # page shell: neutral light canvas behind white cards
        for obj in ("background", "outspace"):
            col = obj_prop(page.get("objects") or {}, obj, "color")
            transp = obj_prop(page.get("objects") or {}, obj, "transparency") or 0
            if isinstance(col, str) and col.startswith("#") and not is_white(col) and transp < 100:
                if hex_to_rgb(col) and saturation(col) < 0.06 and rel_lum(col) > 0.75:
                    canvas = True
                    add("A2", "SI 1.2", "I", "check", f"{ploc}:{obj}", f"neutral canvas {col}",
                        "Page shell (cards): every visual needs a white background so no data sits on the canvas.")
                else:
                    add("A2", "SI 1.2", "S", "fail", f"{ploc}:{obj}", f"{col} (transparency {transp:g}%)",
                        "White page, or a neutral light canvas behind white cards (page shell); no wallpaper.")
        deneb_infos: dict[str, dict] = {}
        has_text = False
        boxes: list[dict] = []
        for vj in sorted(page_json.parent.glob("visuals/*/visual.json")):
            vfile = load_json(vj)
            v = vfile.get("visual") or {}
            vt = str(v.get("visualType", "")).strip()
            vtl = vt.lower()
            vloc = f"{ploc} / {vj.parent.name} ({vt or 'group'})"
            objects = v.get("objects") or {}
            vco = v.get("visualContainerObjects") or vfile.get("visualContainerObjects") or {}
            if not vt:
                continue
            boxes.append(visual_box(vfile, vtl, vloc, vco))
            lint_visual_bindings(vfile, v, vloc, report_measures)
            lint_truncation(vfile, v, vtl, vloc, objects, vco)
            if canvas and vtl not in ("shape", "basicshape", "image", "actionbutton"):
                bg_show = obj_prop(vco, "background", "show")
                bg_col = obj_prop(vco, "background", "color")
                white = bg_show is True and (not isinstance(bg_col, str) or is_white(bg_col)) or \
                    (bg_show is None and theme_card)
                boxes[-1]["needsCard"] = not white   # fine only on a card shape (checked per page below)
            if vtl == "textbox":
                has_text = True
                txt = textbox_text(v)
                y = ((vfile.get("position") or {}).get("y")) or 0
                if y > TITLE_BAND_PX:      # body text: narrative, annotations, footnotes — not a title
                    continue
                for line in txt.splitlines():
                    if not looks_like_title(line):   # key-message sentences may say "total", "trend"
                        continue
                    if BANNED_TITLE.search(line):
                        add("A11", "SI 4.2", "S", "fail", vloc, f"'{line.strip()[:70]}'", "Drop obvious terms; title = who / what / when.")
                    if SUPERFLUOUS.search(line):
                        add("A10", "SI 4.1", "S", "fail", vloc, f"'{line.strip()[:70]}'", "Drop 'Total'/'Sum of'; bold signals totals.")
                continue
            if vtl in ("image",):
                add("A1", "SI 1, SI 1.1", "S", "check", vloc, "image on report page", "Remove logos/pictures that do not aid comprehension.")
            if vtl in ("shape", "basicshape"):
                if any(not is_white(c) and saturation(c) > 0.1 for c in colours_in(objects)):
                    add("A1", "SI 1.1", "S", "check", vloc, "coloured shape", "No decorative shapes/bands; assisting lines only.")
            if vtl in TYPE_RULES:
                r = TYPE_RULES[vtl]
                add(r[0], r[1], r[2], r[3], vloc, r[4], r[5])
            elif vtl not in CHART_TYPES and not vtl.startswith("deneb"):
                for pat, r in CUSTOM_PATTERNS:
                    if pat.search(vt):
                        add(r[0], r[1], r[2], r[3], vloc, f"{r[4]} ({vt})", r[5])
                        break
            fields = list(query_fields(v))
            roles = {f[0] for f in fields}
            if "Play" in roles:
                add("A3", "SI 1.3", "S", "fail", vloc, "Play axis", "No animation; small multiples over time.")
            for role, ent, prop, label in fields:
                if SUPERFLUOUS.search(label or ""):
                    add("A10", "SI 4.1, UN 1.1", "S", "fail", vloc, f"field label '{label}'",
                        "Rename to the glossary measure name (no 'Sum of'); use explicit measures.")
            cats = [(e, p) for r, e, p, _ in fields if r in ("Category", "Axis")]
            if cats:
                e, p = cats[0]
                time_like = bool(DATE_ENTITY.search(e) or DATE_PROP.search(p))
                if vtl in BAR_TYPES and time_like:
                    add("D11", "UN 3.3", "M", "fail", vloc, f"time field {e}[{p}] on a vertical category axis",
                        "Time → columns/lines on a horizontal axis.")
                if vtl in COLUMN_TYPES and not time_like:
                    add("D13", "UN 3.4", "M", "check", vloc, f"non-time field {e}[{p}] on a horizontal category axis",
                        "Structure → bars on a vertical axis (calculation waterfalls are vertical).")
            # legends, axes, labels (scatter: external legend next to symbols is allowed)
            if vtl in CHART_TYPES and obj_prop(objects, "legend", "show") is True and vtl not in TWO_VALUE_AXES:
                add("C10", "UN 2.3", "S", "fail", vloc, "legend.show = true", "Integrate legends (title / series labels).")
            if vtl in CHART_TYPES - DATA_LABELLED_OK:
                labels_on = obj_prop(objects, "labels", "show") is True
                if labels_on and obj_prop(objects, "valueAxis", "show") is True:
                    add("A8", "SI 3.1", "S", "fail", vloc, "value axis shown although data labels are on", "Value axis off.")
                for ax in ("valueAxis", "categoryAxis"):
                    if obj_prop(objects, ax, "gridlineShow") is True:
                        add("A8", "SI 3.1", "S", "check", vloc, f"{ax}.gridlineShow = true",
                            "Gridlines off unless small multiples / dense chart.")
            if vtl in CHART_TYPES:
                start = obj_prop(objects, "valueAxis", "start")
                end = obj_prop(objects, "valueAxis", "end")
                # Fail only when the configured range excludes zero (a negative start or a positive
                # end still shows the baseline). Booleans are not axis bounds.
                bad = [f"valueAxis.start = {start:g}"] if is_number(start) and start > 0 else []
                bad += [f"valueAxis.end = {end:g}"] if is_number(end) and end < 0 else []
                if bad:
                    indexed = any(re.search(r"index", f"{e} {p} {lbl}", re.I) for r, e, p, lbl in fields if r == "Y")
                    add("G1", "CH 1.1", "M", "check" if indexed else "fail", vloc, "; ".join(bad),
                        "Indexed zoom near 100 % allowed with category labels on the 100 % line" if indexed else "Start value axes at 0.")
                scale = obj_prop(objects, "valueAxis", "axisScale")
                if isinstance(scale, str) and "log" in scale.lower():
                    add("G2", "CH 1.2", "M", "check", vloc, f"axisScale = {scale}",
                        "Linear axis, unless growth over orders of magnitude, labelled 'log', audience familiar.")
                if obj_prop(objects, "labels", "labelDisplayUnits") == 0:
                    add("A14", "SI 5.2", "M", "check", vloc, "display units Auto", "Fix display units per scale group.")
            # container chrome (card shapes of the page shell may have ring and shadow: they are not content)
            for obj in ("border", "dropShadow"):
                if obj_prop(vco, obj, "show") is True and vtl not in BACKGROUND_TYPES:
                    add("A4", "SI 2.1", "S", "fail", vloc, f"{obj}.show = true",
                        "No frames/shadows on content visuals; card chrome goes on the card shape behind them.")
            if obj_prop(vco, "background", "show") is True:
                col = obj_prop(vco, "background", "color")
                transp = obj_prop(vco, "background", "transparency") or 0
                if isinstance(col, str) and not is_white(col) and transp < 100:
                    add("A2", "SI 1.2", "S", "fail", vloc, f"background {col}", "Visual background off/white.")
            title = obj_prop(vco, "title", "text")
            if isinstance(title, str):
                has_text = True
                if BANNED_TITLE.search(title):
                    add("A11", "SI 4.2", "S", "fail", vloc, f"title '{title[:70]}'", "Descriptive who/what/when, no obvious terms.")
                if SUPERFLUOUS.search(title):
                    add("A10", "SI 4.1", "S", "fail", vloc, f"title '{title[:70]}'", "Drop 'Total'/'Sum of'.")
            # literal colours
            if palette:
                stray = sorted({c.upper() for c in colours_in(objects) if c.upper() not in palette and saturation(c) > 0.25})
                if stray:
                    add("A5", "SI 2.2", "M", "check", vloc, f"non-token colours {', '.join(stray[:5])}",
                        "Colours only from tokens and only with analytical meaning.")
            # deneb
            if vtl.startswith("deneb"):
                raw = obj_prop(objects, "vega", "jsonSpec")
                provider = obj_prop(objects, "vega", "provider")
                # Deneb names each dataset column by the projection's display name (else its native name)
                dataset = [lbl for r, _, _, lbl in fields if r == "dataset"]
                if not isinstance(raw, str):
                    add("LINT", "-", "I", "check", vloc, "Deneb visual without objects.vega.jsonSpec",
                        "The spec is stored elsewhere or the visual is empty: review it manually.")
                elif isinstance(provider, str) and provider.lower() == "vega":
                    add("LINT", "-", "I", "check", vloc, "Deneb spec is full Vega (not Vega-Lite)", "Review the spec manually.")
                else:
                    try:
                        dspec = json.loads(raw)
                        lint_vegalite(dspec, f"{vloc} deneb", palette, dataset)
                        lint_deneb_scale(dspec, f"{vloc} deneb", dataset)
                        deneb_infos[vj.parent.name] = deneb_info(
                            vfile, dspec, [(lbl, e, p) for r, e, p, lbl in fields if r == "dataset"])
                    except json.JSONDecodeError:
                        add("LINT", "-", "I", "check", vloc, "Deneb spec not parseable JSON", "Review the spec manually.")
        if not has_text:
            add("C2", "UN 2.2", "M", "check", ploc, "no text box or visual title found", "Add the three-line page title (who / what / when).")
        lint_page_geometry(boxes)
        lint_scale_groups(deneb_infos, ploc, {n: r for n, r in layout_rows.items() if n in deneb_infos})
        for n in deneb_infos:
            if n in layout_rows:
                layout_rows[n]["_seen"] = True
    for n, r in layout_rows.items():
        if not r.get("_seen"):
            add("LINT", "-", "I", "check", f"--layout member {r.get('id')}", f"visual '{n}' not found among the Deneb visuals",
                "Check the member's \"visual\" name (the visual folder name).")


# ----------------------------------------------------------------------------- visual spec

HORIZONTAL_TYPES = {"column", "stacked-column", "normalized-column", "indexed-column", "grouped-column",
                    "column-triangles", "variance-column", "pin-time", "column-waterfall", "growth-waterfall",
                    "variance-waterfall-time", "line", "line-selective", "line-indexed", "line-grouped",
                    "variance-area", "stacked-area"}
VERTICAL_TYPES = {"bar", "stacked-bar", "normalized-bar", "indexed-bar", "grouped-bar", "bar-triangles",
                  "variance-bar", "pin-structure", "bar-waterfall", "calculation-waterfall",
                  "variance-waterfall-structure"}
ABS_VARIANCE_TIERS = {"variance-column", "variance-bar"}
SCENARIO_REF = re.compile(r"^[^.]+\.(AC&FC|AC\*|AC|PY|PL|BU|FC)$")


def load_spec(path: Path):
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml   # optional: PyYAML
        except ImportError:
            print("error: reading YAML needs PyYAML (pip install pyyaml), or convert the spec to JSON", file=sys.stderr)
            sys.exit(2)
        with open(path, encoding="utf-8-sig") as fh:
            return yaml.safe_load(fh)
    return load_json(path)


# free text: never parsed as fields, scenarios or code
GUIDE_KEYS = frozenset({"axis", "legend", "header"})
GUIDE_DATUM = frozenset({"label", "value", "index"})
SCENARIO_KNOBS = frozenset({"refScenario", "minuend", "triangleScenario"})
PROSE_KEYS = frozenset({"description", "usermeta", "notes", "note", "question", "openQuestions", "reason", "what", "$schema"})


def spec_texts(node, skip=frozenset()):
    """Every string in a spec subtree (for placeholder and AC&FC searches); keys in `skip` are left out."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in skip:
                continue
            yield str(k)
            yield from spec_texts(v, skip)
    elif isinstance(node, list):
        for v in node:
            yield from spec_texts(v, skip)


def deviation_covers(d: dict, vid) -> bool:
    """A deviation without 'visual' covers the page; else 'visual' is one id or a list of ids (exact match)."""
    vs = d.get("visual")
    if vs is None:
        return True
    return vid in (vs if isinstance(vs, list) else [vs])


def dicts(x) -> list:
    """The dict items of a YAML list that may be null or hold null items."""
    return [i for i in x if isinstance(i, dict)] if isinstance(x, list) else []


def lint_spec(spec: dict, loc):
    """The mechanical rules of visual-spec-format §10 (numbered V1..V17 like the list there)."""
    if not isinstance(spec, dict) or "page" not in spec:
        add("LINT", "-", "M", "fail", loc, "no 'page' block", "Not an IBCS visual spec (visual-spec-format §2).")
        return
    page = spec.get("page") if isinstance(spec.get("page"), dict) else {}
    visuals = [v for v in spec.get("visuals") or [] if isinstance(v, dict)]
    vids = {v.get("id") for v in visuals}
    groups = {g.get("id"): g for g in spec.get("scaleGroups") or [] if isinstance(g, dict)}
    msg = page.get("message") if isinstance(page.get("message"), dict) else {}
    title = page.get("title") if isinstance(page.get("title"), dict) else {}

    def fail(rule, where, evidence, fix, sev="M", status="fail"):
        add(rule, "visual-spec §10", sev, status, f"{loc}:{where}", evidence, fix)

    def targets():
        for i, h in enumerate(msg.get("highlights") or []):
            yield f"page.message.highlights[{i}]", h
        for v in visuals:
            for i, m in enumerate(dicts(v.get("markers"))):
                yield f"{v.get('id')}.markers[{i}]", m

    # V1 message pages carry a sentence with numbers and at least one highlight on an existing visual
    if page.get("kind") == "message":
        text = str(msg.get("text") or "").strip()
        if msg.get("type") in (None, "none"):
            fail("V1", "page.message.type", f"type {msg.get('type')!r} on a message page", "Detection, explanation or suggestion.")
        if not text.endswith(".") or not re.search(r"\d", text):
            fail("V1", "page.message.text", f"'{text[:60]}'", "A complete sentence with numbers and a comparison.")
        if not msg.get("highlights"):
            fail("V1", "page.message.highlights", "no highlight", "Mark the value(s) the message cites (SA 4.3).")
    for where, m in targets():
        t = (m or {}).get("target") if isinstance(m, dict) else None
        if isinstance(t, dict) and t.get("visual") and t["visual"] not in vids:
            fail("V1", where, f"target visual '{t['visual']}' does not exist", "Point the marker at a visual id of this page.")
    # V2 template messages are detections
    if msg.get("source") == "template" and msg.get("type") != "detection":
        fail("V2", "page.message.source", f"template message of type {msg.get('type')!r}", "Only detections may be generated.")
    # V3 title lines and slicer placeholders
    for line in ("who", "what", "when"):
        if not title.get(line):
            fail("V3", f"page.title.{line}", "missing", "Three-line title: who / what / when.")
    for s in dicts((page.get("context") or {}).get("slicers")):
        line = {1: "who", 3: "when"}.get(s.get("titleLine"))
        if line and s.get("id") and "{" + str(s["id"]) not in str(title.get(line) or ""):
            fail("V3", f"page.title.{line}", f"no {{{s['id']}}} placeholder for slicer '{s['id']}'",
                 f"Every slicer with titleLine {s.get('titleLine')} surfaces in title.{line}.")
    # V5 scale groups exist; absolute variance tiers share the base tier's group
    for v in visuals:
        refs = [(f"{v.get('id')}.scaleGroup", v.get("scaleGroup"))] + \
               [(f"{v.get('id')}.tiers.{t.get('id')}", t.get("scaleGroup")) for t in dicts(v.get("tiers"))]
        for where, g in refs:
            if g and g not in groups:
                fail("V5", where, f"scale group '{g}' is not defined", "Declare it in scaleGroups.")
        tiers = dicts(v.get("tiers"))
        base = next((t for t in tiers if t.get("position") == "base"), tiers[0] if tiers else None)
        for t in tiers:
            if base and t is not base and t.get("type") in ABS_VARIANCE_TIERS and t.get("scaleGroup") != base.get("scaleGroup"):
                fail("V5", f"{v.get('id')}.tiers.{t.get('id')}", f"{t.get('scaleGroup')} ≠ base {base.get('scaleGroup')}",
                     "Absolute variance tiers use the same px per unit as their base tier (UN 4.1).")
    for gid, g in groups.items():
        for mem in g.get("members") or []:
            # a member is a visual id or <visual>.<tier, column or variance id>; the visual must exist
            if str(mem).split(".")[0] not in vids:
                fail("V5", f"scaleGroups.{gid}.members", f"member '{mem}' names no visual of this page",
                     "List existing visual ids (or <visual>.<part>).")
    by_unit = {}
    for gid, g in groups.items():
        if g.get("kind", "absolute") == "absolute" and g.get("unit"):
            by_unit.setdefault(str(g["unit"]), []).append(gid)
    ch41 = any(isinstance(d, dict) and "CH 4.1" in str(d.get("rule")) for d in spec.get("deviations") or [])
    for unit, gids in by_unit.items():
        if len(gids) > 1 and not ch41:
            fail("V5", "scaleGroups", f"{len(gids)} absolute groups in {unit}: {', '.join(map(str, gids))}",
                 "One scale group per absolute unit on a page, or record the CH 4.1 deviation.")
    # small-multiples panels get the per-visual checks too (same schema as a visual)
    checked = list(visuals)
    for v in visuals:
        panel = v.get("panel")
        if v.get("type") == "small-multiples" and isinstance(panel, dict):
            checked.append({**panel, "id": f"{v.get('id')}.panel",
                            # without its own data the panel only needs the category (V4); avoids double rows
                            "data": panel.get("data") or {"category": (v.get("data") or {}).get("category") or {}}})
    # V4, V7, V8, V9, V13, V14, V16 per visual; V17 across visuals
    variance_defs = {}
    for v in checked:
        vid, vtype = v.get("id"), v.get("type")
        data = v.get("data") or {}
        cat = data.get("category") or {}
        if cat.get("kind") == "time" and vtype in VERTICAL_TYPES:
            fail("V4", f"{vid}.type", f"time category on {vtype}", "Time runs on a horizontal axis (columns, lines, pin-time).")
        if cat.get("kind") == "structure" and vtype in HORIZONTAL_TYPES:
            fail("V4", f"{vid}.type", f"structure category on {vtype}", "Structure runs on a vertical axis (bars, pin-structure).")
        for t in dicts(v.get("tiers")):
            wrong = VERTICAL_TYPES if cat.get("kind") == "time" else HORIZONTAL_TYPES if cat.get("kind") == "structure" else set()
            if t.get("type") in wrong:
                fail("V4", f"{vid}.tiers.{t.get('id')}", f"{cat.get('kind')} category with a {t.get('type')} tier",
                     "Tiers follow the category axis of their chart.")
        measures = {m.get("id"): m for m in data.get("measures") or [] if isinstance(m, dict)}
        variances = {x.get("id"): x for x in data.get("variances") or [] if isinstance(x, dict)}
        for xid, x in variances.items():
            if not x.get("minuend") or not x.get("subtrahend"):
                fail("V7", f"{vid}.variances.{xid}", "minuend or subtrahend missing", "Name both scenarios.")
            for mid in (x.get("measure") if isinstance(x.get("measure"), list) else [x.get("measure")]):
                m = measures.get(mid)
                if m is not None and m.get("polarity") is None and not m.get("polarityField"):
                    fail("V7", f"{vid}.measures.{mid}", "variance without polarity", "Set polarity (1 / -1 / 0 / by-line) or polarityField.")
                if m is not None and m.get("polarity") == "by-line" and not m.get("polarityField"):
                    rows = [r for r in data.get("rows") or [] if isinstance(r, dict)]
                    lines = [r for r in rows if "line" in r and r.get("type") != "measure"]
                    unresolved = [str(r.get("line")) for r in lines if r.get("polarity") is None]
                    if not any(r.get("polarityField") for r in rows) and (not lines or unresolved):
                        fail("V7", f"{vid}.data.rows", f"measure {mid} is by-line but "
                             + (f"lines {', '.join(unresolved[:4])} have no polarity" if unresolved else "no row gives a polarity"),
                             "Add polarityField on the row field entry, or a polarity on every line.")
            key = (x.get("code"), x.get("minuend"), x.get("subtrahend"), x.get("kind"))   # the measure follows the visual
            if xid in variance_defs and variance_defs[xid][1] != key:
                fail("V17", f"{vid}.variances.{xid}", f"id '{xid}' also defined in {variance_defs[xid][0]} with another meaning",
                     "Variance ids are page-unique: give the other variance its own id (e.g. dbu-fc), or qualify refs as <visual>.<id>.")
            variance_defs.setdefault(xid, (vid, key))
        topn = cat.get("topN") or {}
        if topn and not topn.get("remainder"):
            fail("V8", f"{vid}.data.category.topN", "topN without remainder", "Keep the structure exhaustive (A-30).")
        if vtype == "small-multiples":
            facet = v.get("facet") or {}
            mp = facet.get("maxPanels")
            if not is_number(mp) or mp > 25 or not facet.get("others"):
                fail("V9", f"{vid}.facet", f"maxPanels {mp!r}, others {'set' if facet.get('others') else 'missing'}",
                     "maxPanels ≤ 25 plus an 'others' panel.")
            if not v.get("scaleGroup"):
                fail("V9", f"{vid}.scaleGroup", "small multiples without a scale group", "One scale group for all panels.")
        if vtype == "kpi-cards":
            for i, r in enumerate(data.get("rows") or []):
                if not isinstance(r, dict) or r.get("type") != "measure":
                    fail("V13", f"{vid}.data.rows[{i}]", "not a measure row", "kpi-cards rows are measure rows.")
                    continue
                if r.get("measure") not in measures:
                    fail("V13", f"{vid}.data.rows[{i}]", f"measure '{r.get('measure')}' is not defined", "Define it in data.measures.")
                for xid in r.get("variances") or []:
                    x = variances.get(xid)
                    if x is None:
                        fail("V13", f"{vid}.data.rows[{i}]", f"variance '{xid}' is not defined", "Define it in data.variances.")
                    elif not x.get("field") and not (x.get("minuend") and x.get("subtrahend")):
                        fail("V13", f"{vid}.variances.{xid}", "no field and no minuend/subtrahend", "Give the model measure or the scenarios.")
        for t in dicts(v.get("tiers")):
            scen = [r for r in t.get("values") or [] if isinstance(r, str) and SCENARIO_REF.match(r)]
            if len(scen) == 3:
                draw = t.get("draw") or {}
                roles = sorted(draw.get(r) for r in scen if draw.get(r))
                if roles != ["overlap", "primary", "triangle"]:
                    fail("V14", f"{vid}.tiers.{t.get('id')}.draw", f"draw {draw or 'missing'}",
                         "Three scenarios: exactly one primary, one overlap, one triangle.")
        ext = cat.get("extension") or {}
        if isinstance(ext, dict) and ext.get("scaleGroup"):
            base_g = next((t.get("scaleGroup") for t in dicts(v.get("tiers")) if t.get("position") == "base"), v.get("scaleGroup"))
            bands = {m.get("scaleGroup") for m in dicts(v.get("markers")) if isinstance(m, dict) and m.get("kind") == "scale-band"}
            if not {ext["scaleGroup"], base_g} <= bands:
                fail("V16", f"{vid}.markers", f"scale bands for {sorted(bands - {None}) or 'none'}",
                     f"An extension on its own scale needs scale-band markers in {base_g} and {ext['scaleGroup']}.")
            if not any(isinstance(d, dict) and "CH 4.1" in str(d.get("rule")) and deviation_covers(d, vid)
                       for d in spec.get("deviations") or []):
                fail("V16", f"{vid}.data.category.extension", "own scale without a deviations entry", "Record the CH 4.1 deviation.")
    # V10 footer
    media = page.get("media") or []
    footer = page.get("footer") or {}
    if media and set(media) != {"slides"}:
        for k in ("sources", "asOf"):
            if not footer.get(k):
                fail("V10", f"page.footer.{k}", "missing", "Sources and as-of on every medium except live slides (SA 4.4).")
    # V12 deviations
    oq = " ".join(map(str, spec.get("openQuestions") or []))
    for i, d in enumerate(spec.get("deviations") or []):
        if not isinstance(d, dict):
            fail("V12", f"deviations[{i}]", f"not an entry: {str(d)[:40]!r}", "Each deviation is {rule, what, reason, acceptedBy, …}.")
            continue
        missing = [k for k in ("rule", "what", "reason", "acceptedBy") if not d.get(k)]
        if missing:
            fail("V12", f"deviations[{i}]", f"missing {', '.join(missing)}", "rule, what, reason and acceptedBy are required.")
        elif str(d["acceptedBy"]).upper().startswith("TBD") and str(d["rule"]) not in oq:
            fail("V12", f"deviations[{i}]", f"acceptedBy TBD but {d['rule']} not in openQuestions", "Ask for the acceptance in openQuestions.")
    # V15 AC&FC needs the last closed period and a separator on time charts
    asof = ((page.get("context") or {}).get("period") or {}).get("asOf")
    if any("AC&FC" in s for s in spec_texts(visuals, skip=PROSE_KEYS)):
        if not asof:
            fail("V15", "page.context.period.asOf", "AC&FC without asOf", "Name the last closed period (the AC→FC switch).")
        for v in visuals:
            cat = (v.get("data") or {}).get("category") or {}
            if cat.get("kind") == "time" and any("AC&FC" in s for s in spec_texts(v, skip=PROSE_KEYS)):
                if not any(isinstance(m, dict) and m.get("kind") == "separator" and m.get("at") == "asOf" for m in dicts(v.get("markers"))):
                    fail("V15", f"{v.get('id')}.markers", "no separator at asOf", "Add {kind: separator, at: asOf}.")


# ----------------------------------------------------------------------------- dom (rendered web charts)

SCENARIO_ROLE = re.compile(r"^(?:col|bar|triangle|line|dot|marker|area)-(AC|PY|PL|BU|FC)\b")
CSS_FILL = re.compile(r"(?:^|;)\s*(fill|stroke|color)\s*:\s*([^;]+)")
# SVG graphics elements; every other element with data-role (HTML span/td/div, SVG text) is a text mark
SVG_GRAPHIC = frozenset({"rect", "line", "path", "circle", "ellipse", "polygon", "polyline", "use", "g", "image", "svg"})
CSS_VAR = re.compile(r"var\(\s*--([A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)")


class _MarkCollector(HTMLParser):
    """Collect elements with data-role and their effective fill/stroke (inherited from <g>)."""
    VOID = {"rect", "line", "path", "circle", "ellipse", "polygon", "polyline", "use", "img", "br", "input", "meta", "link"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.marks, self.patterns = [], [], set()

    def _paint(self, attrs):
        d = dict(attrs)
        paint = {k: d[k] for k in ("fill", "stroke", "color") if d.get(k)}
        for k, val in CSS_FILL.findall(d.get("style") or ""):
            paint[k] = val.strip()
        return d, paint

    def handle_starttag(self, tag, attrs, closed=False):
        d, paint = self._paint(attrs)
        if tag == "pattern" and d.get("id"):
            self.patterns.add(d["id"])
        inherited = {}
        for _, p in self.stack:
            inherited.update(p)
        eff = {**inherited, **paint}
        if d.get("data-role"):
            text = tag not in SVG_GRAPHIC   # SVG <text>/<tspan> and HTML numbers (span, td, div …)
            self.marks.append({"tag": tag, "role": d["data-role"], "impact": d.get("data-impact"), "text": text,
                               "kind": d.get("data-kind"),
                               # HTML text is painted by CSS color; SVG text by fill
                               "fill": (eff.get("color") or eff.get("fill")) if text and tag not in ("text", "tspan")
                               else eff.get("fill"),
                               "stroke": eff.get("stroke"),
                               "transform": d.get("transform") or "", "id": d.get("id")})
        if not closed and tag not in self.VOID:
            self.stack.append((tag, paint))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def lint_dom(text: str, loc, tokens):
    """Rendered marks (data-role on each SVG mark, ibcs-web-charts §8) against the effective tokens."""
    p = _MarkCollector()
    p.feed(text)
    if not p.marks:
        add("LINT", "-", "I", "check", loc, "no element with data-role found",
            "Render every mark with data-role (and data-impact on variances), see ibcs-web-charts §8.")
        return
    flat = {}
    def walk(node, path):
        if isinstance(node, dict):
            if "$value" in node:
                try:
                    flat[path] = token_value(tokens, path)
                except Exception:
                    pass
            for k, v in node.items():
                if not k.startswith("$"):
                    walk(v, f"{path}.{k}" if path else k)
    walk(tokens, "")
    css = {"ibcs-" + k.replace(".", "-"): v for k, v in flat.items()}

    def colour(val):
        if not isinstance(val, str):
            return None
        m = CSS_VAR.search(val)
        if m:
            val = css.get(m.group(1), val)
        val = str(val).strip()
        rgb = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)", val, re.I)
        if rgb:
            val = "#" + "".join(f"{int(c):02X}" for c in rgb.groups())
        val = {"white": "#FFFFFF", "black": "#000000"}.get(val.lower(), val)
        u = re.fullmatch(r"url\(\s*['\"]?#([^'\")]+)['\"]?\s*\)", val, re.I)
        if u:   # a hatch is a <pattern> defined in the same document; gradients and missing ids are not
            return "url" if u.group(1) in p.patterns else f"url(#{u.group(1)}) (no <pattern>)"
        if val.lower().startswith("url("):
            return val
        if val.lower() in ("none", "transparent"):
            return "none"
        return full_hex(val) if hex_to_rgb(val) else val.lower()

    tv = lambda p: full_hex(flat[p]) if isinstance(flat.get(p), str) and hex_to_rgb(flat[p]) else None
    bg = tv("color.background.page") or "#FFFFFF"
    sc = {k: tv(f"color.scenario.{k}") for k in ("ac", "py")}
    sc["pl"] = tv("color.scenario.pl.stroke") or sc["ac"]
    impact = {k: {tv(f"color.variance.{v}{k}") for v in ("", "cvd.", "bw.")} - {None} for k in ("good", "bad", "neutral")}
    text_ok = {k: {tv(f"color.variance.{v}{k}Text") for v in ("", "cvd.")} - {None} for k in ("good", "bad", "neutral")}
    palette = palette_from_tokens(tokens)
    seen = set()

    def once(key, *a):
        key = (a[0],) + key   # one row per rule, role and colour
        if key not in seen:
            seen.add(key)
            add(*a)

    for m in p.marks:
        role, fill, stroke = m["role"], colour(m["fill"]), colour(m["stroke"])
        where = f"{loc}:[data-role={role}]"
        s = SCENARIO_ROLE.match(role)
        if s:
            code, shape = s.group(1), role.split("-")[0]
            filled = shape in ("col", "bar", "triangle", "dot", "marker")
            if code == "AC" and ((filled and fill != sc["ac"]) or (shape == "line" and stroke != sc["ac"])):
                once((role, fill, stroke), "D4", "UN 3.2", "M", "fail", where, f"fill {fill}, stroke {stroke}",
                     f"AC is solid {sc['ac']} (lines: a {sc['ac']} stroke).")
            if code == "PY" and ((filled and fill != sc["py"]) or (shape == "line" and stroke != sc["py"])):
                once((role, fill, stroke), "D5", "UN 3.2", "M", "fail", where, f"fill {fill}, stroke {stroke}",
                     f"PY is solid light {sc['py']} (lines: a {sc['py']} stroke).")
            if code in ("PL", "BU") and filled:
                if fill not in ("none", bg) or stroke != sc["pl"]:
                    once((role, fill, stroke), "D6", "UN 3.2", "M", "fail", where, f"fill {fill}, stroke {stroke}",
                         f"PL/BU are outlined (markers hollow): page-coloured (or no) fill and a {sc['pl']} stroke.")
            if code in ("PL", "BU") and shape == "line" and stroke != sc["pl"]:
                once((role, stroke), "D6", "UN 3.2", "M", "fail", where, f"stroke {stroke}",
                     f"A PL/BU line is drawn in the plan stroke {sc['pl']}.")
            if code == "FC" and shape in ("col", "bar", "dot", "marker") and fill != "url":
                once((role, fill), "D7", "UN 3.2", "M", "fail", where, f"fill {fill}",
                     "FC is hatched: a fill url(#id) pointing at a <pattern> in the page.")
        if role == "step" and not m["text"]:   # calculation waterfall (ibcs-web-charts §8)
            all_impact = {c for c in set().union(*impact.values()) if saturation(c) > 0.25}   # bw.* greys are not impact
            if m["kind"] in ("base", "subtotal", "total") and fill != sc["ac"]:
                once((role, m["kind"], fill), "D4", "UN 3.2", "M", "fail", where, f"{m['kind']} step filled {fill}",
                     f"Base, subtotal and total bars of a calculation waterfall are AC: {sc['ac']}.")
            elif m["kind"] in ("add", "sub") and fill in all_impact:
                once((role, m["kind"], fill), "E6", "UN 4.1", "M", "fail", where, f"{m['kind']} step in impact colour {fill}",
                     "Calculation steps are not variances: grey additions, subtractions as the skill says, never good/bad.")
            elif m["kind"] not in ("base", "add", "sub", "subtotal", "total"):
                once((role, "kind"), "LINT", "-", "S", "check", where, f"data-kind {m['kind']!r}",
                     "A step needs data-kind base|add|sub|subtotal|total.")
        if re.fullmatch(r"segment-\d+", role) and not m["text"]:   # stacked segments above the lowest
            if fill == sc["ac"] or fill in {c for c in set().union(*impact.values()) if saturation(c) > 0.25}:
                once((role, fill), "D9", "UN 3.2", "M", "fail", where, f"segment filled {fill}",
                     "Only the lowest segment carries the scenario notation; the segments above are greys.")
        kind = m["impact"]
        if kind in impact:
            if m["text"]:
                if fill in impact[kind] and fill not in text_ok[kind] and contrast(fill, bg) < 4.5:
                    once((role, fill), "E6", "UN 4.1, WCAG 1.4.3", "M", "fail", where,
                         f"variance number in the graphic colour {fill} ({contrast(fill, bg):.1f}:1)",
                         "Variance numbers use color.variance.*Text (or color.text.primary); bars and pins keep the graphic colour.")
                elif fill not in text_ok[kind] | impact[kind] | {tv("color.text.primary"), None}:
                    once((role, fill), "E6", "UN 4.1", "M", "check", where, f"{kind} number in {fill}", f"Use color.variance.{kind}Text.")
            else:
                paint = stroke if m["tag"] in ("line", "polyline") or fill in (None, "none") else fill
                if paint not in impact[kind] | {"url"}:
                    once((role, kind, paint), "E6", "UN 4.1", "M", "fail", where, f"{kind} impact drawn in {paint}",
                         f"Use color.variance.{kind} (or its cvd / bw variant).")
        rot = re.search(r"rotate\(\s*(-?[\d.]+)", m["transform"])
        if m["text"] and rot and float(rot.group(1)) % 360 != 0:
            once((role, "rot"), "C12", "UN 2.3", "M", "fail", where, m["transform"], "Labels horizontal.")
        for c in (fill, stroke):
            if isinstance(c, str) and c.startswith("#") and c not in palette and saturation(c) > 0.25:
                once((role, c), "A5", "SI 2.2", "M", "check", where, f"non-token colour {c}", "Colours only from tokens.")


# ----------------------------------------------------------------------------- output

def render(fmt):
    sev_order = {"M": 0, "S": 1, "I": 2}
    FINDINGS.sort(key=lambda f: (sev_order.get(f["sev"], 3), f["status"] != "fail", f["location"]))
    if fmt == "json":
        print(json.dumps(FINDINGS, ensure_ascii=False, indent=2))
        return
    if not FINDINGS:
        print("No automatic findings. Run the manual checklist (ibcs-review) — metadata cannot show everything.")
        return
    print("| # | Sev | Status | Rule | IBCS | Location | Evidence | Fix |")
    print("|---|---|---|---|---|---|---|---|")
    for i, f in enumerate(FINDINGS, 1):
        cells = [str(i), f["sev"], f["status"], f["rule"], f["ibcs"], f["location"], f["evidence"], f["fix"]]
        print("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    m = sum(1 for f in FINDINGS if f["sev"] == "M" and f["status"] == "fail")
    print(f"\n{len(FINDINGS)} findings; {m} failed must-rule(s). 'check' = needs human confirmation.")


OVERRIDES_NAME = "ibcs-tokens.overrides.json"


def default_tokens_path():
    """The token file bundled with the ibcs-notation skill of this plugin."""
    cand = Path(__file__).resolve().parent.parent.parent / "ibcs-notation" / "assets" / "ibcs-tokens.json"
    return cand if cand.exists() else None


def default_overrides_path(start: Path):
    """First ibcs-tokens.overrides.json in start or one of its parents (None if there is none)."""
    start = start.resolve()
    for d in (start, *start.parents):
        cand = d / OVERRIDES_NAME
        if cand.is_file():
            return cand
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only IBCS lint (PBIR, theme, Vega-Lite, tokens, visual spec, rendered DOM).")
    ap.add_argument("target", nargs="?", default="auto", choices=["auto", "pbir", "theme", "vegalite", "tokens", "spec", "dom"])
    ap.add_argument("path")
    ap.add_argument("--tokens", default=None,
                    help="token file (default: the bundled ../../ibcs-notation/assets/ibcs-tokens.json)")
    ap.add_argument("--overrides", default=None,
                    help=f"organisation overrides (default: the first {OVERRIDES_NAME} in the current directory or a parent)")
    ap.add_argument("--no-overrides", action="store_true", help="ignore any overrides file")
    ap.add_argument("--theme", help="extra token layer (e.g. a dark-mode variant), merged after --overrides")
    ap.add_argument("--format", default="md", choices=["md", "json"])
    ap.add_argument("--layout", action="append", default=[], metavar="LAYOUT.json",
                    help="pbir: scale_layout.py --json output (members with \"visual\"); each visual must have "
                         "the computed size and px per unit (repeat per scale group)")
    a = ap.parse_args(argv)
    path = Path(a.path)
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 2
    tok_path = Path(a.tokens) if a.tokens else default_tokens_path()
    if a.no_overrides:
        ovr = None
    elif a.overrides:
        ovr = Path(a.overrides)
        if not ovr.exists():
            print(f"error: {ovr} does not exist", file=sys.stderr)
            return 2
    else:
        ovr = default_overrides_path(Path.cwd())
    target = a.target
    try:
        if target == "auto":
            if path.is_dir():
                target = "pbir"
            elif path.suffix.lower() in (".yaml", ".yml"):
                target = "spec"
            elif path.suffix.lower() in (".html", ".htm", ".svg"):
                target = "dom"
            else:
                data = load_json(path)
                if "ibcsVisualSpec" in data or "page" in data and "visuals" in data:
                    target = "spec"
                elif "$schema" in data and "vega" in str(data.get("$schema")):
                    target = "vegalite"
                elif "color" in data and "geometry" in data:
                    target = "tokens"
                else:
                    target = "theme"
        if target == "tokens":
            if ovr is None and not a.no_overrides and not a.overrides:
                ovr = default_overrides_path(path.parent)
            if ovr is not None and ovr.resolve() == path.resolve():
                ovr = None
            tokens = load_tokens(path, ovr)
            if a.theme:
                tokens = deep_merge(tokens, load_json(Path(a.theme)))
            lint_tokens(tokens, path.name)
        elif target == "spec":
            lint_spec(load_spec(path), path.name)
        else:
            tokens = load_tokens(tok_path, ovr) if tok_path else None
            if target == "pbir":
                lint_pbir(path, tokens, a.layout)
            elif target == "theme":
                lint_theme(load_json(path), path.name, tokens)
            elif target == "vegalite":
                lint_vegalite(load_json(path), path.name, palette_from_tokens(tokens) if tokens else None)
            elif target == "dom":
                if not tokens:
                    print("error: the dom target needs the token file (--tokens)", file=sys.stderr)
                    return 2
                lint_dom(path.read_text(encoding="utf-8-sig"), path.name, tokens)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"error: cannot parse {path}: {e}", file=sys.stderr)
        return 2
    except ValueError as e:   # e.g. a token or override that is not a colour
        print(f"error: {e}", file=sys.stderr)
        return 2
    render(a.format)
    return 1 if any(f["sev"] == "M" and f["status"] == "fail" for f in FINDINGS) else 0


if __name__ == "__main__":
    sys.exit(main())
