#!/usr/bin/env python3
"""Size the visuals of one scale group to their data at one px per unit (CH 4.1 + CH 4.2).

    python3 -I scale_layout.py group.json [--px-per-unit 3.5 | --max-extent 320] [--json]
        [--templates DIR]        (default: the bundled ibcs-deneb templates; a synced --out copy works too)

Same unit, same scale means the same px per unit, not the same domain: each member's plot extent is
its own data range × px per unit, so a chart with smaller values gets a SHORTER visual, never a
taller empty domain. This script prints, per member, the container size to give the visual
(`to_pbir.py --pos`, or `position.height` / `width` in visual.json) and the px per unit to set on
every member (Deneb knob `pxPerUnit` or field `PxPerUnit`; SVG measures: their px-per-unit input).

group.json (ranges in display units after unitDivisor; pin charts in percentage points):

    {
      "pxPerUnit": 3.5,                  optional; else derived from maxExtentPx
      "maxExtentPx": 320,                optional: container extent available to the member with
                                         the largest data range (the tightest member wins)
      "members": [
        {"id": "monthly", "template": "column-two-tier-variance",
         "tiers": {"base": [0, 23], "variance": [-2.1, 3.4]}},
        {"id": "entities", "template": "bar-structure-variance",
         "tiers": {"base": [0, 63], "variance": [-5, 4]}, "categoryLabelsPx": 80},
        {"id": "table-bars", "template": "svg", "range": [-5, 4], "fixedPx": 0},
        {"id": "...", "template": "...", "params": {"showCategoryLabels": false}, "maxPx": 400},
        {"id": "total", "template": "column-two-tier-variance", "own": true,
         "tiers": {"base": [0, 216], "variance": [0, 2.5]}, "basePxPerUnit": 1,
         "tierPxPerUnit": {"variance": "group"}}
      ]
    }

Tiers that exist only with a knob (`onlyIf` in the template layout) count only when the member's params
set it: column-two-tier-variance with "params": {"showBase": false} has no base tier, with
{"pinTier": true, "pinPxPerUnit": 2} it has a "pins" tier (range in percentage points) sized at
pinPxPerUnit px per point (the tier's own scale), e.g.
        {"id": "monthly", "template": "column-two-tier-variance",
         "params": {"pinTier": true, "pinPxPerUnit": 2},
         "tiers": {"base": [0, 23], "variance": [-2.1, 3.4], "pins": [-12, 20]}}

Visuals side by side whose tiers must line up (a month chart and its Total) need the SAME variance and
pin ranges: give both members the union range here and set it as varMin/varMax (display units) and
pinMin/pinMax (fractions: -0.12 for -12 points) on both visuals, so each tier's axis sits at the same
height even when one visual's own data spans less.

Optional per template member (the docs' extra paddings, so nothing is cut or squashed):
    "comment": true          Comment markers bound: + ibcsFontSize + 18 px on the first tier's padHigh
    "clipPct": true          pin outliers cut (clipPct / ClipPct): + ibcsFontSize + ibcsPinHeadMax + 6 px
                             on padHigh and padLow of the pin tier (the triangle beyond the label)
    "categoryCount": 25      number of categories (bars, periods): also prints the OTHER dimension,
                             categoryCount × ibcsCategoryStep[grain] × stepScale + crossFixedPx, so 25
                             bars are not squashed into a 260 px visual; grain = "periodType" param for
                             column templates (default month), structureRow for horizontal ones
    "crossFixedPx": 30       fixed px of that other dimension (axis, legend row); default 30
    "planFootnote": false    line-scenarios without its plan footnote (also params showPL false)
    "trend": {"ends": [v0, v1], "excess": e}
                             line-scenarios with trendArrow: v0/v1 = first and last AC&FC value, e = how
                             far the highest visible value rises above the straight line between them
                             (0 if never). The base tier's hi becomes max(hi, max(v0, v1) + e) and the
                             arrow and its label add ibcsFontSize + 10 + trendLiftPx (+ ibcsFontSize + 10
                             with a trendLabel, else 4) px (an upper bound: exact when the arrow is the top)
Label room and width (gap: clipped value labels, squashed columns):
    "visual": "v2Columns"    the visual folder name; passed through to the output (--json), so
                             `ibcs_lint.py pbir <Report> --layout out.json` can check each visual's size
    "longestValueLabel": "+12.4%"
                             the longest formatted value label of the member (or "valueLabelChars": 6);
                             needs 7 px per character + 6 px. Horizontal templates (value axis = width):
                             the label room right of the bars (and left of negative ones) is the tier's
                             first padHigh knob (ibcsLabelPx, labelPx, labelRoom); when it is smaller the
                             member is sized with the larger value and the output says which knob to set
                             ("setParams"). Column templates: compared with the category slot
                             ((widthPx − crossFixedPx) / categoryCount) when widthPx and categoryCount
                             are given; a label wider than its slot collides with its neighbours.
                             svg members: compared with "labelRoomPx" (the px the SVG keeps for labels)
    "widthPx": 1040          the visual's current size in the other dimension: warns when it is smaller
                             than the computed other dimension (categoryCount), i.e. columns squashed
Warnings go to stderr and into "warnings" of the --json output; treat every warning as a defect.

Small multiples (template small-multiples-columns, value axis = panel height): the container value is
the panel height (set knob panelHeight to it, or pxPerUnit on the visual); give "panels" and "columns"
(default 3), optionally "panelTotals": true, to also get the visual height = panel rows × (panel +
header + axis) + gaps (usermeta.ibcs.layout.container of the template).

A Total / extension visual with its own base scale ("own": true, scaling indicator or footnote)
keeps its variance tier on the group's scale: `tierPxPerUnit` maps a tier to "group" (the group's
px per unit) or a number; the other tiers use `basePxPerUnit`. Set the Deneb knobs
pxPerUnit = basePxPerUnit and varPxPerUnit = the group's px per unit (column-two-tier-variance).
Members with "own": true never set the group's px per unit.

Template members read `usermeta.ibcs.layout` of the template: fixedPx (padding, category labels,
marker overflow; measured with the Vega-Lite version Deneb bundles), and per tier the data range
plus padHigh / padLow / padLowIfNegative (template params in px). Horizontal templates (value axis =
width) also need the category label column: `categoryLabelsPx`, or `longestLabel` (estimated at
7 px per character + 6), capped at the template's categoryLabelLimitPx + 6 (the axis labelLimit:
longer labels are cut with an ellipsis). The waterfalls keep their row labels in the knob
labelWidth (padding.left): the container uses that knob (or its default), and the script warns when
the labels need more; set labelWidth to the printed value. `svg` members (SVG measures, other
tools) give `range` and `fixedPx`.
Container = fixedPx + category labels + Σ tiers ((hi − lo) × px per unit + pads), rounded up.
Re-run when the filter context changes the ranges (slicers): use the ranges of the widest
selection the page allows, or recompute with the page's scale measures.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
TEMPLATES = Path(__file__).resolve().parents[2] / "ibcs-deneb" / "assets" / "templates"


def load_template(name: str, tdir: Path) -> dict:
    path = tdir / f"{name}.vl.json"
    if not path.exists():
        sys.exit(f"unknown template {name!r} (no {path})")
    spec = json.loads(path.read_text(encoding="utf-8"))
    layout = spec.get("usermeta", {}).get("ibcs", {}).get("layout")
    if not layout:
        sys.exit(f"template {name!r} has no usermeta.ibcs.layout: it does not support pxPerUnit")
    params = {p["name"]: p.get("value") for p in spec.get("params", []) if "value" in p}
    return {"layout": layout, "params": params}


def label_need_px(m: dict) -> float | None:
    """Width of the member's longest value label: 7 px per character + 6 (12 px Segoe UI)."""
    if "longestValueLabel" in m:
        return 7.0 * len(str(m["longestValueLabel"])) + 6
    if "valueLabelChars" in m:
        return 7.0 * int(m["valueLabelChars"]) + 6
    return None


def label_room(m: dict, tdir: Path) -> tuple[dict, list[str]]:
    """Knob values a horizontal member needs so its value labels fit, plus warnings."""
    need = label_need_px(m)
    if need is None or m.get("template", "svg") == "svg":
        if need is not None and "labelRoomPx" in m and float(m["labelRoomPx"]) < need:
            return {}, [f"member {m['id']}: value labels need {math.ceil(need)} px, the SVG keeps "
                        f"{m['labelRoomPx']} px (labelRoomPx): widen the SVG's label room"]
        return {}, []
    t = load_template(m["template"], tdir)
    lay, params = t["layout"], {**t["params"], **m.get("params", {})}
    if lay["valueAxis"] != "width":
        return {}, []
    out, warns = {}, []
    for tier in lay["tiers"]:
        knob = (tier.get("padHigh") or [None])[0]
        if knob and float(params.get(knob) or 0) < need and knob not in out:
            out[knob] = math.ceil(need)
            warns.append(f"member {m['id']}: value labels need {math.ceil(need)} px, knob {knob} is "
                         f"{params.get(knob)}: set {knob} = {math.ceil(need)} (sized with it)")
    return out, warns


def px_sum(names, params) -> float:
    return float(sum(params[n] for n in names or []))


def member_parts(m: dict, tdir: Path, group_ppu: float | None = None) -> dict:
    """Data range (units) and fixed px of one member: extent = range × ppu + fixed.

    Tiers on their own px per unit (tierPxPerUnit) add their extent to the fixed px; an "own"
    member's remaining tiers use basePxPerUnit and are folded into fixed px as well."""
    if m.get("template", "svg") == "svg":
        lo, hi = m["range"]
        return {"dim": m.get("dimension", "plot"), "range": hi - lo, "fixed": float(m.get("fixedPx", 0))}
    t = load_template(m["template"], tdir)
    lay, params = t["layout"], {**t["params"], **m.get("params", {})}
    labels = params.get("showCategoryLabels", True) is not False
    fixed = float(lay["fixedPx"] if labels else lay.get("fixedPxNoCategoryLabels", lay["fixedPx"]))
    if labels and params.get("periodLabel") == "month" and "fixedPxMonthLabels" in lay:
        fixed = float(lay["fixedPxMonthLabels"])   # second label line with the year
    if "fixedPxNoPlanFootnote" in lay and (params.get("showPL") is False or m.get("planFootnote") is False):
        fixed = float(lay["fixedPxNoPlanFootnote"])   # line chart without the plan footnote
    if "plusCategoryLabels" in lay and labels:
        limit = lay.get("categoryLabelLimitPx")  # the axis labelLimit: longer labels get an ellipsis
        cap = float(limit) + 6 if limit else float("inf")
        if "categoryLabelsPx" in m:
            label_px = min(float(m["categoryLabelsPx"]), cap)
        elif "longestLabel" in m:
            label_px = min(7 * len(m["longestLabel"]) + 6, cap)
        elif "labelWidth" in m.get("params", {}):
            label_px = float(m["params"]["labelWidth"])
        else:
            sys.exit(f"member {m['id']}: give categoryLabelsPx or longestLabel ({lay['plusCategoryLabels']})")
        if "labelWidth" in t["params"]:
            # the waterfalls keep their row labels in padding.left = knob labelWidth: that knob IS the
            # label column, so the container uses it; set labelWidth to at least the labels' width
            column = float(m.get("params", {}).get("labelWidth", t["params"]["labelWidth"]))
            if column < label_px:
                print(f"member {m['id']}: set knob labelWidth = {math.ceil(label_px)} (row labels); "
                      f"sized with {column:g}", file=sys.stderr)
            label_px = column
        fixed += label_px
    rng = 0.0
    given = m.get("tiers", {})
    unknown = set(given) - {tier["id"] for tier in lay["tiers"]}
    if unknown:
        sys.exit(f"member {m['id']}: unknown tiers {sorted(unknown)}; {m['template']} has "
                 f"{[tier['id'] for tier in lay['tiers']]}")
    extra_high = {}  # tier id -> extra padHigh px; pins also get it below
    if m.get("comment"):
        extra_high[lay["tiers"][0]["id"]] = float(params.get("ibcsFontSize", 12)) + 18
    clip_pad = 0.0
    if m.get("clipPct"):
        clip_pad = float(params.get("ibcsFontSize", 12)) + float(params.get("ibcsPinHeadMax", 8)) + 6
    trend_top, trend_px = None, 0.0
    if m.get("trend") and params.get("trendArrow") is True:
        v0, v1 = m["trend"]["ends"]
        trend_top = max(v0, v1) + max(0.0, float(m["trend"].get("excess", 0)))
        fs = float(params.get("ibcsFontSize", 12))
        trend_px = fs + 10 + float(params.get("trendLiftPx", 0) or 0) + (fs + 10 if params.get("trendLabel") else 4)
    for tier in lay["tiers"]:
        if tier.get("onlyIf") and params.get(tier["onlyIf"]) is not True:
            continue   # e.g. base tier with showBase false, pin tier without pinTier
        if tier["id"] not in given:
            sys.exit(f"member {m['id']}: missing tier {tier['id']!r} ({tier['range']})")
        lo, hi = given[tier["id"]]
        if trend_top is not None and tier is lay["tiers"][0]:
            hi = max(hi, trend_top)
            fixed += trend_px
        lo, hi = min(lo, 0.0), max(hi, 0.0)  # every tier includes its baseline (CH 1.1)
        tppu = m.get("tierPxPerUnit", {}).get(tier["id"])
        if tppu == "group":
            tppu = group_ppu
        if tppu is None and tier.get("pxPerUnitParam"):
            # a tier on its own scale inside the visual (pin tier: px per percentage point)
            tppu = float(params.get(tier["pxPerUnitParam"]) or 0) or sys.exit(
                f"member {m['id']}: tier {tier['id']!r} needs knob {tier['pxPerUnitParam']} > 0 to be sized")
        if tppu is None and m.get("own"):
            tppu = m.get("basePxPerUnit") or sys.exit(f"member {m['id']}: own scale needs basePxPerUnit")
        if tppu is not None:
            if not tppu:
                return {"dim": lay["valueAxis"], "range": None, "fixed": fixed, "pending": True}
            fixed += (hi - lo) * float(tppu)
        else:
            rng += hi - lo
        fixed += px_sum(tier.get("padHigh"), params) + px_sum(tier.get("padLow"), params)
        fixed += extra_high.get(tier["id"], 0.0) + (2 * clip_pad if tier["id"] == "pins" else 0.0)
        if lo < 0:
            fixed += px_sum(tier.get("padLowIfNegative"), params)
    out = {"dim": lay["valueAxis"], "range": rng, "fixed": fixed}
    if "categoryCount" in m:
        steps = params.get("ibcsCategoryStep") or {}
        grain = "structureRow" if lay["valueAxis"] == "width" else str(params.get("periodType", "month"))
        step = float(steps.get(grain, 24)) * float(params.get("stepScale", 1.5))
        out["cross"] = math.ceil(int(m["categoryCount"]) * step + float(m.get("crossFixedPx", 30)))
    if lay["valueAxis"] == "panelHeight" and m.get("panels"):
        rows = math.ceil(int(m["panels"]) / max(1, int(m.get("columns", 3))))
        header = float(lay.get("panelHeaderTotalsPx" if m.get("panelTotals") else "panelHeaderPx", 16))
        axis = 0.0 if params.get("periodLabel") == "none" else float(lay.get("panelCategoryLabelsPx", 18))
        out["panelRows"] = rows
        out["panelExtra"] = header + axis
        out["panelFixed"] = (rows - 1) * float(lay.get("panelGapPx", 10)) + float(lay.get("outerPadPx", 10))
    return out


def floor_sig(x: float, sig: int = 3) -> float:
    if x <= 0:
        return x
    step = 10 ** (math.floor(math.log10(x)) - sig + 1)
    return math.floor(x / step + 1e-9) * step


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("group", help="scale-group JSON (see above)")
    ap.add_argument("--px-per-unit", type=float, help="overrides pxPerUnit in the file")
    ap.add_argument("--max-extent", type=float, help="overrides maxExtentPx in the file")
    ap.add_argument("--templates", default=str(TEMPLATES), help="Deneb templates dir (default: bundled)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a table")
    a = ap.parse_args()

    g = json.loads(Path(a.group).read_text(encoding="utf-8"))
    tdir = Path(a.templates)
    members = g.get("members") or sys.exit("no members")
    warnings: dict[str, list[str]] = {m["id"]: [] for m in members}
    set_params: dict[str, dict] = {}
    for m in members:
        knobs, warns = label_room(m, tdir)
        if knobs:
            set_params[m["id"]] = knobs
            m["params"] = {**m.get("params", {}), **knobs}   # size with the label room it needs
        warnings[m["id"]] += warns
    parts = {m["id"]: member_parts(m, tdir) for m in members}
    shared = [m for m in members if not parts[m["id"]].get("pending") and parts[m["id"]]["range"]]

    ppu = a.px_per_unit or g.get("pxPerUnit")
    if not ppu:
        caps = []
        max_extent = a.max_extent or g.get("maxExtentPx")
        if max_extent:
            largest = max(shared, key=lambda m: parts[m["id"]]["range"])
            caps.append((max_extent, largest["id"]))
        caps += [(m["maxPx"], m["id"]) for m in shared if m.get("maxPx")]
        if not caps:
            sys.exit("give pxPerUnit, maxExtentPx or a member maxPx")
        ppu = floor_sig(min((ext - parts[i]["fixed"]) / parts[i]["range"] for ext, i in caps if parts[i]["range"] > 0))
        if ppu <= 0:
            sys.exit("the available extent does not even hold the fixed px of the largest member")

    parts = {m["id"]: member_parts(m, tdir, ppu) for m in members}  # resolve "group" tiers
    rows = []
    for m in members:
        p = parts[m["id"]]
        plot = p["range"] * ppu
        row = {"id": m["id"], "template": m.get("template", "svg"), "dimension": p["dim"],
               "dataRange": round(p["range"], 6), "dataPx": round(plot, 1),
               "containerPx": math.ceil(plot + p["fixed"] - 1e-6),
               "fitsMaxPx": (math.ceil(plot + p["fixed"] - 1e-6) <= m["maxPx"]) if m.get("maxPx") else None}
        if m.get("visual"):
            row["visual"] = m["visual"]
        if set_params.get(m["id"]):
            row["setParams"] = set_params[m["id"]]
        if "cross" in p:
            row["crossPx"] = p["cross"]
            if m.get("widthPx") is not None and float(m["widthPx"]) < p["cross"]:
                warnings[m["id"]].append(f"member {m['id']}: the visual is {m['widthPx']} px, its "
                                         f"{m['categoryCount']} categories need {p['cross']} px: columns are squashed")
        need = label_need_px(m)
        if need is not None and p["dim"] == "height" and m.get("widthPx") and m.get("categoryCount"):
            slot = (float(m["widthPx"]) - float(m.get("crossFixedPx", 30))) / int(m["categoryCount"])
            if need > slot:
                warnings[m["id"]].append(f"member {m['id']}: value labels need {math.ceil(need)} px, a "
                                         f"category slot is {slot:.0f} px: widen the visual, use fewer "
                                         f"decimals or a larger unit")
        if warnings[m["id"]]:
            row["warnings"] = warnings[m["id"]]
        if "panelRows" in p:
            row["visualHeightPx"] = math.ceil(p["panelRows"] * (row["containerPx"] + p["panelExtra"]) + p["panelFixed"])
        rows.append(row)
    for r in rows:
        for w in r.get("warnings", []):
            print(f"warning: {w}", file=sys.stderr)
    if a.json:
        print(json.dumps({"pxPerUnit": ppu, "members": rows}, indent=2))
        return 0
    print(f"pxPerUnit = {ppu:g}   (Deneb: knob pxPerUnit or field PxPerUnit on every member; "
          f"SVG measures: the same px per unit)")
    print(f"{'member':<18}{'template':<28}{'size':<13}{'range':>9}{'data px':>9}{'container px':>14}")
    for r in rows:
        warn = "  > maxPx!" if r["fitsMaxPx"] is False else ""
        more = (f"   other dimension {r['crossPx']} px" if "crossPx" in r else "") + \
               (f"   visual height {r['visualHeightPx']} px" if "visualHeightPx" in r else "")
        print(f"{r['id']:<18}{r['template']:<28}{r['dimension']:<13}{r['dataRange']:>9g}{r['dataPx']:>9g}"
              f"{r['containerPx']:>14}{warn}{more}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
