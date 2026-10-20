#!/usr/bin/env python3
"""Write the IBCS design tokens into the Deneb templates and the Deneb config.

    python3 -I scripts/sync_tokens.py                                   # rewrite the bundled assets in place
    python3 -I scripts/sync_tokens.py --check                           # exit 1 if stale (CI)
    python3 -I scripts/sync_tokens.py --overrides ibcs-tokens.overrides.json --out ./deneb-ibcs
    python3 -I scripts/sync_tokens.py --variant cvd --out ./deneb-ibcs-cvd   # CVD-safe impact colours

Paths are relative to this skill's directory in the examples; run it from anywhere.
--tokens defaults to the bundled ../assets/ibcs-tokens.json; --overrides is your organisation's
ibcs-tokens.overrides.json (optional). With --out, the synced templates and config are written to
that directory (templates/ and config/) and the bundled assets stay untouched: use this for
organisation-specific builds, so a plugin update never overwrites them.

Every template keeps its token values as top-level Vega-Lite `params` (Vega: `signals`) whose
names start with `ibcs` (table PARAMS below). This script only replaces the `value` of those
params, so each template stays a valid, Deneb-ready spec you can paste as is, and nothing in the
specs is a second hard-coded palette. Template-specific knobs (refScenario, polarity, label
gaps) are not tokens and are left alone.

It also generates config/deneb-config.json (font, sizes, locale with the IBCS thousands
separator, no view stroke, no axis chrome) from the same tokens.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
sys.dont_write_bytecode = True  # leave no __pycache__ inside the plugin
sys.path.insert(0, str(HERE))
import ibcs_tokens  # noqa: E402

# param name -> token path (or a callable on the resolved tokens)
PARAMS = {
    "ibcsAC": "color.scenario.ac",
    "ibcsPY": "color.scenario.py",
    "ibcsPLFill": "color.scenario.pl.fill",
    "ibcsPLStroke": "color.scenario.pl.stroke",
    "ibcsFCStripe": "color.scenario.fc.stripe",
    "ibcsFCGround": "color.scenario.fc.ground",
    "ibcsFCStroke": "color.scenario.fc.stroke",
    "ibcsGray2": lambda t, v: ibcs_tokens.get(t, "color.scenario.stackGrays")[1],
    "ibcsGood": lambda t, v: _impact(t, v)["good"],
    "ibcsBad": lambda t, v: _impact(t, v)["bad"],
    "ibcsNeutral": lambda t, v: _impact(t, v)["neutral"],
    "ibcsText": "color.text.primary",
    "ibcsTextSecondary": "color.text.secondary",
    "ibcsTextOnDark": "color.text.onDark",
    "ibcsBackground": "color.background.page",
    "ibcsAxis": "color.axis.category",
    "ibcsAxisPY": "color.axis.pyReference",
    "ibcsAxisPL": "color.axis.plReference",
    "ibcsGrid": "color.axis.grid",
    "ibcsAssist": "color.marker.assistingLine",
    "ibcsAssistArea": "color.marker.assistingArea",
    "ibcsHighlight": "color.marker.highlight",
    "ibcsHighlightWidth": "stroke.highlightEllipsePx",
    "ibcsAnnotation": "color.marker.annotationRef",
    "ibcsScaleBandFill": "color.marker.scaleBandFill",
    "ibcsScaleBandLine": "color.marker.scaleBandLine",
    "ibcsBarRatio": "geometry.barWidthRatio.absolute",
    "ibcsCategoryStep": "geometry.categoryStepPx",
    "ibcsRelBarRatio": "geometry.barWidthRatio.relative",
    "ibcsPinRatio": "geometry.pin.thicknessRatio",
    "ibcsPinHeadRatio": "geometry.pin.headRatio",
    "ibcsOffsetCol": "geometry.referenceOffsetRatio.column",
    "ibcsOffsetBar": "geometry.referenceOffsetRatio.bar",
    "ibcsTriangleRatio": "geometry.triangleSizeRatio",
    "ibcsTriMin": "geometry.triangleSizePx.min",
    "ibcsTriMax": "geometry.triangleSizePx.max",
    "ibcsPinStemMin": "geometry.pin.stemPx.min",
    "ibcsPinStemMax": "geometry.pin.stemPx.max",
    "ibcsPinHeadMin": "geometry.pin.headPx.min",
    "ibcsPinHeadMax": "geometry.pin.headPx.max",
    "ibcsLineAbs": "stroke.line.absolutePx",
    "ibcsLineRel": "stroke.line.relativePx",
    "ibcsMarkerRatio": "stroke.line.markerToLineRatio",
    "ibcsOutline": "stroke.outlinePx",
    "ibcsAxisWidth": "stroke.categoryAxisPx",
    "ibcsPYAxisWidth": "stroke.varianceAxis.pyWidthPx",
    "ibcsPLAxisLine": "stroke.varianceAxis.plLinePx",
    "ibcsPLAxisGap": "stroke.varianceAxis.plGapPx",
    "ibcsAssistWidth": "stroke.assistingLinePx",
    "ibcsFont": lambda t, v: ibcs_tokens.get(t, "typography.family.powerbi")[0],
    "ibcsFontSize": "typography.size.label.px",
    "ibcsTitleSize": "typography.size.subtitle.px",
    "ibcsBold": "typography.weight.emphasis",
    "ibcsFmtAbs": "number.format.absolute.d3",
    "ibcsFmtVar": "number.format.variance.d3",
    "ibcsFmtRelVar": "number.format.relativeVariance.d3",
    "ibcsFmtRatio": "number.format.ratio.d3",
    "ibcsNA": "number.sign.notApplicable",
    "ibcsHatch": lambda t, v: hatch_pattern_id(t),
}


def _impact(t: dict, variant: str) -> dict:
    v = ibcs_tokens.get(t, "color.variance")
    return {"standard": v, "cvd": v["cvd"], "bw": v["bw"]}[variant]


def hatch_pattern_id(t: dict) -> str:
    """Pick the Deneb built-in hatch closest to the token hatch.

    Deneb ships diagonal-stripe-1..6 (10x10 tile => stripe period 10/sqrt(2) ~ 7.07 px, stroke N px),
    rising bottom-left -> top-right like the IBCS figures. Deneb cannot draw the token period
    (pattern.fcHatch.periodPx); we match the stripe share instead.
    """
    share = ibcs_tokens.get(t, "pattern.fcHatch.stripeShare")
    period = 10 / math.sqrt(2)
    n = min(range(1, 7), key=lambda k: abs(k / period - share))
    return f"diagonal-stripe-{n}"


def token_value(t: dict, key, variant: str):
    return key(t, variant) if callable(key) else ibcs_tokens.get(t, key)


def deneb_config(t: dict) -> dict:
    g = ibcs_tokens.get
    font = g(t, "typography.family.powerbi")[0]
    fs = g(t, "typography.size.label.px")
    text = g(t, "color.text.primary")
    return {
        "autosize": {"type": "fit", "contains": "padding"},
        "background": None,  # transparent: the Power BI page shows through (SI 1.2)
        "font": font,
        "view": {"stroke": "transparent"},
        "padding": 4,
        "locale": {
            "number": {
                "decimal": g(t, "number.separator.decimal"),
                "thousands": g(t, "number.separator.thousands"),
                "grouping": [3],
                "currency": ["", ""],
                "minus": g(t, "number.sign.negative"),
                "nan": g(t, "number.sign.notApplicable"),
            }
        },
        "axis": {
            "grid": False, "domain": False, "ticks": False, "title": None,
            "labelFont": font, "labelFontSize": fs, "labelColor": text, "labelPadding": 4,
        },
        "legend": {"disable": True},
        "text": {"font": font, "fontSize": fs, "fill": text},
        "header": {"labelFont": font, "labelFontSize": g(t, "typography.size.subtitle.px"),
                   "labelColor": text, "labelAnchor": "start", "labelPadding": 2, "title": None},
        "title": {"font": font, "fontSize": g(t, "typography.size.subtitle.px"), "color": text,
                  "anchor": "start", "fontWeight": "normal"},
        "bar": {"stroke": None},
        "line": {"strokeWidth": g(t, "stroke.line.absolutePx")},
    }


def sync_spec(spec: dict, t: dict, variant: str) -> tuple[dict, list[str]]:
    used = []
    key = "signals" if "signals" in spec and "marks" in spec else "params"
    for p in spec.get(key, []):
        name = p.get("name", "")
        if name.startswith("ibcs") and name in PARAMS:
            p["value"] = token_value(t, PARAMS[name], variant)
            used.append(name)
        elif name.startswith("ibcs") and "value" in p and "bind" not in p:
            # ibcs-prefixed but not a token: a template knob. Fine, but flag typos.
            pass
    return spec, used


def dump(o) -> str:
    return json.dumps(o, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokens", help="token file (default: the bundled ../assets/ibcs-tokens.json)")
    ap.add_argument("--overrides", help="your ibcs-tokens.overrides.json (optional)")
    ap.add_argument("--variant", default="standard", choices=["standard", "cvd", "bw"])
    ap.add_argument("--assets", default=str(ASSETS), help="source assets dir with templates/ (default: bundled)")
    ap.add_argument("--out", help="write templates/ and config/ here instead of in place")
    ap.add_argument("--check", action="store_true", help="exit 1 if the outputs are stale; write nothing")
    a = ap.parse_args()

    t = ibcs_tokens.load(a.tokens, a.overrides)
    assets = Path(a.assets)
    out = Path(a.out) if a.out else assets
    stale = []
    outputs = {out / "config" / "deneb-config.json": dump(deneb_config(t))}
    for f in sorted((assets / "templates").glob("*.v[lg].json")):
        spec = json.loads(f.read_text(encoding="utf-8"))
        spec, used = sync_spec(spec, t, a.variant)
        outputs[out / "templates" / f.name] = dump(spec)
        unknown = [p["name"] for p in spec.get("params", spec.get("signals", []))
                   if p.get("name", "").startswith("ibcs") and p["name"] not in PARAMS
                   and p["name"] not in spec.get("usermeta", {}).get("ibcs", {}).get("knobs", [])]
        if unknown:
            print(f"warning {f.name}: ibcs* params that are neither tokens nor declared knobs: {unknown}",
                  file=sys.stderr)
    for path, body in outputs.items():
        if a.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path}")
    if stale:
        print("stale (run sync_tokens.py):", *[str(p) for p in stale], sep="\n  ", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
