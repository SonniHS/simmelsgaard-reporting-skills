"""Page layout checks: scale groups, label room, truncated titles, the page shell, the message measure.

Run from the repo root:  python3 -m unittest discover -s tests
Synthetic PBIR reports are written to a temporary directory; the linter and scale_layout.py run in
subprocesses (-I -B), like tests/test_ibcs_lint.py.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
LINT = ROOT / "plugins/ibcs/skills/ibcs-review/scripts/ibcs_lint.py"
SCALE_LAYOUT = ROOT / "plugins/ibcs-power-bi/skills/ibcs-power-bi/scripts/scale_layout.py"
THEME = ROOT / "plugins/ibcs-power-bi/skills/ibcs-power-bi/scripts/build_pbi_theme.py"
DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def measure(name, display):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_M"}}, "Property": name}},
            "queryRef": f"_M.{name}", "nativeQueryRef": name, "displayName": display}


def deneb(name, template, pos, params=None, fields=()):
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v6.json", "data": {"name": "dataset"},
            "usermeta": {"ibcs": {"template": template}},
            "params": [{"name": k, "value": v} for k, v in (params or {}).items()],
            "transform": [{"filter": "isValid(datum['Period']) && datum['Period'] !== ''"}],
            "mark": "bar", "encoding": {"x": {"field": "Period", "type": "nominal"},
                                        "y": {"field": "AC", "type": "quantitative"}}}
    projs = [measure("AC", "AC")] + [measure(m, d) for d, m in fields]
    x, y, w, h = pos
    return name, {"name": name, "position": {"x": x, "y": y, "width": w, "height": h},
                  "visual": {"visualType": DENEB, "query": {"queryState": {"dataset": {"projections": projs}}},
                             "objects": {"vega": [{"properties": {
                                 "jsonSpec": lit("'" + json.dumps(spec).replace("'", "''") + "'"),
                                 "provider": lit("'vegaLite'")}}]}}}


def slicer(name, header, width):
    return name, {"name": name, "position": {"x": 0, "y": 140, "width": width, "height": 54},
                  "visual": {"visualType": "slicer",
                             "query": {"queryState": {"Values": {"projections": [
                                 {"field": {"Column": {"Expression": {"SourceRef": {"Entity": "Date"}},
                                                       "Property": "Month"}},
                                  "queryRef": "Date.Month", "nativeQueryRef": "Month", "active": True}]}}},
                             "objects": {"header": [{"properties": {"text": lit("'" + header + "'")}}]}}}


def textbox(name, text, y=10, background=None):
    v = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": text, "textStyle": {"fontSize": "10pt"}}]}]}}]}}
    if background is not None:
        v["visualContainerObjects"] = {"background": [{"properties": {
            "show": lit("true"), "color": {"solid": {"color": lit(f"'{background}'")}}}}]}
    return name, {"name": name, "position": {"x": 16, "y": y, "width": 600, "height": 24}, "visual": v}


def report(root: Path, pages: dict, canvas=None):
    d = root / "T.Report" / "definition"
    (d / "pages").mkdir(parents=True)
    (d / "report.json").write_text(json.dumps({"themeCollection": {"baseTheme": {"name": "CY24SU10"}}}))
    for pname, visuals in pages.items():
        pd = d / "pages" / pname
        (pd / "visuals").mkdir(parents=True)
        page = {"name": pname, "displayName": pname, "width": 1280, "height": 720}
        if canvas:
            page["objects"] = {"background": [{"properties": {"color": {"solid": {"color": lit(f"'{canvas}'")}},
                                                              "transparency": lit("0D")}}]}
        (pd / "page.json").write_text(json.dumps(page))
        for name, v in visuals:
            (pd / "visuals" / name).mkdir()
            (pd / "visuals" / name / "visual.json").write_text(json.dumps(v))
    return root / "T.Report"


def lint(path, *extra):
    p = subprocess.run([sys.executable, "-I", "-B", str(LINT), "pbir", str(path), "--no-overrides",
                        "--format", "json", *map(str, extra)], capture_output=True, text=True)
    out = p.stdout.strip()
    return p.returncode, (json.loads(out) if out.startswith("[") else []), p.stderr


def rows(findings, rule, visual=None):
    return [f for f in findings if f["rule"] == rule and (visual is None or visual in f["location"])]


class ScaleGroups(unittest.TestCase):
    def test_domain_shared_by_visuals_of_different_size_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [
                textbox("title", "Sales in mEUR"),
                deneb("months", "column-two-tier-variance", (16, 300, 1000, 330), fields=[("YMax", "Scale Max")]),
                deneb("entities", "bar-structure-variance", (16, 660, 500, 200))]})
            # the only Deneb user of the domain: it may be shared with SVG measures the linter cannot see
            code, f, err = lint(r)
            self.assertEqual(err, "")
            g8 = rows(f, "G8")
            self.assertTrue(any(x["sev"] == "S" and x["status"] == "fail" and "without pxPerUnit" in x["evidence"]
                                for x in g8), g8)

    def test_one_domain_on_two_sizes_is_a_must_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [
                textbox("title", "Sales in mEUR"),
                deneb("months", "column-two-tier-variance", (16, 300, 1000, 330), fields=[("YMax", "Scale Max")]),
                deneb("total", "column-two-tier-variance", (1030, 300, 200, 200), fields=[("YMax", "Scale Max")])]})
            code, f, _ = lint(r)
            must = [x for x in rows(f, "G8") if x["sev"] == "M" and x["status"] == "fail"]
            self.assertEqual(len(must), 1, rows(f, "G8"))
            self.assertIn("different size", must[0]["evidence"])
            self.assertEqual(code, 1)

    def test_px_per_unit_with_layout_checks_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            r = report(tmp, {"p1": [
                textbox("title", "Sales in mEUR"),
                deneb("months", "column-two-tier-variance", (16, 300, 1000, 200), {"pxPerUnit": 8}),
                deneb("entities", "bar-structure-variance", (16, 520, 640, 220), {"pxPerUnit": 8, "ibcsLabelPx": 40}),
                deneb("total", "column-two-tier-variance", (1030, 300, 200, 200), {"pxPerUnit": 1, "periodType": "year"})]})
            layout = tmp / "layout.json"
            layout.write_text(json.dumps({"pxPerUnit": 8, "members": [
                {"id": "m", "visual": "months", "dimension": "height", "containerPx": 200},
                {"id": "e", "visual": "entities", "dimension": "width", "containerPx": 600,
                 "setParams": {"ibcsLabelPx": 48}}]}))
            code, f, _ = lint(r, "--layout", layout)
            self.assertEqual(code, 1)
            sizes = [x for x in rows(f, "G8", "entities") if x["sev"] == "M"]
            self.assertEqual(len(sizes), 1)
            self.assertIn("width 640 px, scale_layout.py computed 600 px", sizes[0]["evidence"])
            self.assertEqual(rows(f, "G8", "months"), [])
            self.assertTrue(any("ibcsLabelPx" in x["evidence"] for x in rows(f, "LINT", "entities")))
            # the Total keeps its own scale but must be marked
            self.assertEqual([x["status"] for x in rows(f, "F6", "total")], ["check"])

    def test_own_scale_member_is_checked_against_its_own_px_per_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            r = report(tmp, {"p1": [
                deneb("months", "column-two-tier-variance", (16, 300, 1000, 200), {"pxPerUnit": 8, "scaleBand": 5}),
                deneb("total", "column-two-tier-variance", (1030, 300, 200, 200),
                      {"pxPerUnit": 0.4, "periodType": "year", "scaleBand": 5})]})
            layout = tmp / "layout.json"
            def write(own_ppu):
                layout.write_text(json.dumps({"pxPerUnit": 8, "members": [
                    {"id": "m", "visual": "months", "dimension": "height", "containerPx": 200},
                    {"id": "t", "visual": "total", "dimension": "height", "containerPx": 200, "dataRange": 218.5,
                     "ownScale": True, "ownPxPerUnit": own_ppu}]}))
            write(0.4)
            _, f, _ = lint(r, "--layout", layout)
            self.assertEqual([x for x in rows(f, "G8", "total") if x["sev"] == "M"], [])
            write(0.5)
            _, f, _ = lint(r, "--layout", layout)
            self.assertTrue(any("its own scale is 0.5" in x["evidence"] for x in rows(f, "G8", "total")))

    def test_layout_size_excludes_the_visual_padding(self):
        """page-shell.md §1: position = computed size + padding; the check compares the inner size."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            name, months = deneb("months", "column-two-tier-variance", (16, 300, 1000, 466), {"pxPerUnit": 9})
            months["visual"]["visualContainerObjects"] = {"padding": [{"properties": {
                "top": lit("0D"), "bottom": lit("12D"), "left": lit("12D"), "right": lit("0D")}}]}
            r = report(tmp, {"p1": [textbox("title", "Sales in mEUR"), (name, months)]})
            layout = tmp / "layout.json"
            layout.write_text(json.dumps({"pxPerUnit": 9, "members": [
                {"id": "m", "visual": "months", "dimension": "height", "containerPx": 454}]}))
            _, f, _ = lint(r, "--layout", layout)
            self.assertEqual([x for x in rows(f, "G8", "months") if x["sev"] == "M"], [])
            # without the padding the same position is 12 px too tall
            layout.write_text(json.dumps({"pxPerUnit": 9, "members": [
                {"id": "m", "visual": "months", "dimension": "height", "containerPx": 440}]}))
            _, f, _ = lint(r, "--layout", layout)
            must = [x for x in rows(f, "G8", "months") if x["sev"] == "M"]
            self.assertEqual(len(must), 1, rows(f, "G8"))
            self.assertIn("padding 12 = 454 px", must[0]["evidence"])

    def test_unknown_layout_visual_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            r = report(tmp, {"p1": [textbox("title", "Sales in mEUR"),
                                    deneb("months", "column-two-tier-variance", (16, 300, 1000, 200), {"pxPerUnit": 8})]})
            layout = tmp / "layout.json"
            layout.write_text(json.dumps({"pxPerUnit": 8, "members": [{"id": "x", "visual": "nope", "containerPx": 1}]}))
            _, f, _ = lint(r, "--layout", layout)
            self.assertTrue(any("'nope' not found" in x["evidence"] for x in rows(f, "LINT")))


class PinScale(unittest.TestCase):
    def test_a_fixed_stub_pin_scale_and_whole_percent_labels_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = deneb("stub", "column-two-tier-variance", (16, 400, 600, 300),
                         {"pinTier": True, "pinPxPerUnit": 1, "pinDecimals": 0})
            own = deneb("own", "column-two-tier-variance", (640, 400, 600, 300),
                        {"pinTier": True, "pinPxPerUnit": 0, "pinDecimals": 1})
            _, f, _ = lint(report(Path(tmp), {"p": [stub, own]}))
        self.assertEqual(len(rows(f, "E12", "stub")), 1)
        self.assertEqual(len(rows(f, "B5", "stub")), 1)
        self.assertEqual(rows(f, "E12", "own") + rows(f, "B5", "own"), [])


class PinScaleMarker(unittest.TestCase):
    """OURS: pin tiers on different % scales each carry a scaling marker (pinScaleBand), UN 5.2 / CH 4.3."""

    def page(self, a, b):
        with tempfile.TemporaryDirectory() as tmp:
            _, f, _ = lint(report(Path(tmp), {"p": [deneb("months", "column-two-tier-variance", (16, 400, 600, 300), a),
                                                    deneb("regions", "pin-relative-variance", (640, 400, 600, 300), b)]}))
        return rows(f, "F6")

    def test_own_pin_scales_without_a_marker_fail(self):
        f = self.page({"pinTier": True, "pinPxPerUnit": 0}, {})
        self.assertEqual({r["location"].split(" / ")[-1] for r in f}, {"months", "regions"})
        self.assertTrue(all(r["sev"] == "M" and r["status"] == "fail" for r in f))

    def test_marked_or_shared_pin_scales_pass(self):
        self.assertEqual(self.page({"pinTier": True, "pinScaleBand": -1}, {"pinScaleBand": 0.1}), [])
        self.assertEqual(self.page({"pinTier": True, "pinPxPerUnit": 2}, {"pxPerUnit": 2}), [])
        one = self.page({"pinTier": True, "pinScaleBand": -1}, {})
        self.assertEqual([r["location"].split(" / ")[-1] for r in one], ["regions"])


class PinOutliers(unittest.TestCase):
    """OURS: a pin beyond 3 × the next-largest |Δ%| is clipped and does not set the tier's scale; a tier
    where most non-zero pins get stems under 4 px fails E12 (proof run 2: one −100 % flattened the rest)."""
    LEGACY = [-1.8, -1.8, 1.7, -100, -1.7, 1.6, -1.8, -1.7]

    def layout(self, params):
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp) / "g.json"
            g.write_text(json.dumps({"maxExtentPx": 300, "members": [
                {"id": "m", "template": "column-two-tier-variance", "params": {"pinTier": True, **params},
                 "tiers": {"base": [0, 6.2], "variance": [-0.1, 0.1]}, "pinValues": self.LEGACY}]}))
            p = subprocess.run([sys.executable, "-I", "-B", str(SCALE_LAYOUT), str(g), "--json"],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)["members"][0], p.stderr

    def test_one_extreme_pin_does_not_flatten_the_others(self):
        row, err = self.layout({})
        self.assertEqual(row["pinStemsShort"], {"short": 0, "total": 7})
        self.assertNotIn("carry no magnitude", err)

    def test_without_the_outlier_rule_the_short_stems_warn(self):
        row, err = self.layout({"pinOutlierFactor": 0})
        self.assertEqual(row["pinStemsShort"]["short"], 7)
        self.assertIn("carry no magnitude", err)

    def test_a_one_pin_total_aligned_with_the_months_is_not_judged_alone(self):
        """Proof run 3: a Total whose single pin shares the months' pin scale failed "1 of 1 pins under 4 px"."""
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp) / "g.json"
            g.write_text(json.dumps({"maxExtentPx": 300, "alignTiers": [["m", "t"]], "members": [
                {"id": "m", "template": "column-two-tier-variance", "params": {"pinTier": True},
                 "tiers": {"base": [0, 6.2], "variance": [-0.1, 0.1]}, "pinValues": [-2.4, 3.1, -1.2, 2.0, 1.4]},
                {"id": "t", "template": "column-two-tier-variance", "params": {"pinTier": True},
                 "tiers": {"base": [0, 60], "variance": [-1, 1]}, "pinValues": [0.2]}]}))
            p = subprocess.run([sys.executable, "-I", "-B", str(SCALE_LAYOUT), str(g), "--json"],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = {r["id"]: r for r in json.loads(p.stdout)["members"]}
        self.assertNotIn("pinStemsShort", rows["t"])
        self.assertEqual(rows["m"]["pinStemsShort"]["total"], 6)   # judged as one group
        self.assertNotIn("carry no magnitude", p.stderr)

    def test_a_scale_band_larger_than_the_data_warns(self):
        """Proof run 3: a 50 mEUR band on a chart whose data peaks at 23 doubled its plot without a warning."""
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp) / "g.json"
            g.write_text(json.dumps({"maxExtentPx": 300, "members": [
                {"id": "m", "template": "column-two-tier-variance", "params": {"scaleBand": 50},
                 "tiers": {"base": [0, 23], "variance": [-1, 1]}}]}))
            p = subprocess.run([sys.executable, "-I", "-B", str(SCALE_LAYOUT), str(g), "--json"],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("scaleBand 50 exceeds", p.stderr)

    def test_templates_default_to_the_outlier_factor(self):
        for name in ("column-two-tier-variance", "pin-relative-variance"):
            spec = json.loads((ROOT / f"plugins/ibcs-power-bi/skills/ibcs-deneb/assets/templates/{name}.vl.json")
                              .read_text(encoding="utf-8"))
            params = {q["name"]: q.get("value") for q in spec["params"]}
            self.assertEqual(params.get("pinOutlierFactor"), 3, name)
            self.assertIn("pinOutlierFactor", json.dumps(spec["transform"]), name)

    def test_lint_fails_a_pin_tier_with_mostly_short_stems(self):
        with tempfile.TemporaryDirectory() as tmp:
            rep = report(Path(tmp), {"p": [deneb("months", "column-two-tier-variance", (16, 400, 600, 300),
                                                 {"pinTier": True})]})
            lay = Path(tmp) / "layout.json"
            lay.write_text(json.dumps({"pxPerUnit": 10, "members": [
                {"id": "m", "visual": "months", "template": "column-two-tier-variance", "dimension": "height",
                 "pinStemsShort": {"short": 6, "total": 7}}]}))
            _, f, _ = lint(rep, "--layout", lay)
        bad = rows(f, "E12", "months")
        self.assertTrue(any(r["sev"] == "M" and r["status"] == "fail" for r in bad), f)

    def test_variance_only_total_is_not_asked_for_a_scale_band(self):
        with tempfile.TemporaryDirectory() as tmp:
            months = deneb("months", "column-two-tier-variance", (16, 400, 600, 300), {"pxPerUnit": 10})
            total = deneb("total", "column-two-tier-variance", (640, 400, 120, 120),
                          {"pxPerUnit": 3, "periodType": "year", "showBase": False})
            _, f, _ = lint(report(Path(tmp), {"p": [months, total]}))
        self.assertEqual(rows(f, "F6", "total"), [])


class Truncation(unittest.TestCase):
    def test_long_slicer_header_fails_short_one_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [textbox("title", "Sales in mEUR"),
                                          slicer("long", "Company (all = the whole group of companies)", 220),
                                          slicer("short", "Company", 220)]})
            _, f, _ = lint(r)
            self.assertEqual(len([x for x in rows(f, "LINT", "long (") if "is cut" in x["evidence"]]), 1)
            self.assertEqual([x for x in rows(f, "LINT", "short (") if "is cut" in x["evidence"]], [])


def placed(item, x, y, w, h, pad_top=None):
    name, v = item
    v = json.loads(json.dumps(v))
    v["position"] = {"x": x, "y": y, "width": w, "height": h}
    if pad_top is not None:
        v["visual"].setdefault("visualContainerObjects", {})["padding"] = [{"properties": {"top": lit(f"{pad_top}D")}}]
    return name, v


def shape(name, x, y, w, h):
    return name, {"name": name, "position": {"x": x, "y": y, "width": w, "height": h},
                  "visual": {"visualType": "shape", "visualContainerObjects": {}}}


class HeaderRhythm(unittest.TestCase):
    def test_slicer_touching_the_title_lines_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            title = placed(textbox("title", "Sales in mEUR"), 16, 100, 1248, 58)
            r = report(Path(tmp), {"p1": [title, placed(slicer("touch", "Company", 212), 16, 158, 212, 64)]})
            _, f, _ = lint(r)
            self.assertEqual(len([x for x in rows(f, "LINT", "touch (") if "below the title" in x["evidence"]]), 1)

    def test_slicer_with_padding_top_12_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            title = placed(textbox("title", "Sales in mEUR"), 16, 92, 1248, 70)
            s = placed(slicer("padded", "Company", 212), 16, 162, 212, 76, pad_top=12)
            _, f, _ = lint(report(Path(tmp), {"p1": [title, s]}))
            self.assertEqual([x for x in rows(f, "LINT", "padded (") if "below the title" in x["evidence"]], [])


class TitleLines(unittest.TestCase):
    """page-shell §3: one visual type for the three title lines (cards bottom-align text, text boxes top-align)."""

    def lines(self, types):
        items = []
        for k, (t, y, h) in enumerate(zip(types, (88, 122, 144), (34, 22, 22))):
            name, v = placed(textbox(f"line{k}", "x"), 16, y, 1248, h)
            v["visual"]["visualType"] = t
            items.append((name, v))
        with tempfile.TemporaryDirectory() as tmp:
            _, f, _ = lint(report(Path(tmp), {"p1": items}))
        return [x for x in rows(f, "LINT") if "title lines mix" in x["evidence"]]

    def test_mixed_title_line_types_fail(self):
        self.assertEqual(len(self.lines(["cardVisual", "textbox", "cardVisual"])), 1)

    def test_one_type_passes(self):
        self.assertEqual(self.lines(["cardVisual", "cardVisual", "cardVisual"]), [])

    def test_chart_card_title_with_card_subtitle_passes(self):
        """Proof run 3: a chart card's text-box title over a cardVisual subtitle is not a page title stack."""
        header = [shape("hdr", 16, 16, 1248, 200)]
        for k, (t, y, h) in enumerate(zip(["cardVisual"] * 3, (88, 122, 144), (34, 22, 22))):
            name, v = placed(textbox(f"line{k}", "x"), 16, y, 1248, h)
            v["visual"]["visualType"] = t
            header.append((name, v))
        title = placed(textbox("chartTitle", "Revenue in mEUR"), 32, 420, 600, 22)
        sub_name, sub = placed(textbox("chartSub", "x"), 32, 442, 600, 20)
        sub["visual"]["visualType"] = "cardVisual"
        page = [*header, shape("chartCard", 16, 409, 1248, 300), title, (sub_name, sub)]
        with tempfile.TemporaryDirectory() as tmp:
            _, f, _ = lint(report(Path(tmp), {"p1": page}))
        self.assertEqual([x for x in rows(f, "LINT") if "title lines mix" in x["evidence"]], [])


class CardBottom(unittest.TestCase):
    def test_card_background_with_empty_bottom_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = placed(textbox("a", "Revenue by month"), 20, 400, 600, 36)
            b = placed(textbox("b", "AC and PY"), 20, 436, 600, 24)
            _, f, _ = lint(report(Path(tmp), {"p1": [shape("bgLoose", 16, 396, 1248, 160), a, b]}))
            self.assertEqual(len([x for x in rows(f, "LINT", "bgLoose (") if "below its last visual" in x["evidence"]]), 1)
            _, f, _ = lint(report(Path(tmp) / "t2", {"p1": [shape("bgTight", 16, 396, 1248, 76), a, b]}))
            self.assertEqual([x for x in rows(f, "LINT", "bgTight (") if "below its last visual" in x["evidence"]], [])

    def test_equal_height_row_is_measured_against_its_deepest_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            # two cards of one row, 200 px tall: the left one's content is 180 px deep, the right one's 60 px
            left = [placed(textbox("l1", "Revenue"), 20, 400, 600, 36), placed(textbox("l2", "AC"), 20, 436, 600, 144)]
            right = [placed(textbox("r1", "Orders"), 660, 400, 600, 36), placed(textbox("r2", "AC"), 660, 436, 600, 24)]
            page = [shape("bgL", 16, 396, 620, 200), shape("bgR", 656, 396, 620, 200), *left, *right]
            _, f, _ = lint(report(Path(tmp), {"p1": page}))
            self.assertEqual([x for x in rows(f, "LINT", "bgR (") if "below its last visual" in x["evidence"]], [])


class PageShell(unittest.TestCase):
    def test_grey_canvas_needs_white_visuals(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [textbox("bare", "Sales in mEUR"),
                                          textbox("card", "Sales in mEUR", y=40, background="#FFFFFF")]},
                       canvas="#F3F3F3")
            _, f, _ = lint(r)
            a2 = rows(f, "A2")
            self.assertTrue(any(x["sev"] == "I" and "neutral canvas" in x["evidence"] for x in a2))
            self.assertEqual(len([x for x in a2 if "bare (" in x["location"]]), 1)
            self.assertEqual([x for x in a2 if "card (" in x["location"]], [])

    def test_coloured_canvas_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [textbox("t", "Sales in mEUR")]}, canvas="#DDEEFF")
            _, f, _ = lint(r)
            self.assertTrue(any(x["status"] == "fail" and x["sev"] == "S" for x in rows(f, "A2")))

    def test_shell_theme_sets_canvas_and_white_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run([sys.executable, "-I", "-B", str(THEME), "--out-dir", tmp, "--shell", "cards",
                                "--variants", "standard"], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            theme = json.loads((Path(tmp) / "ibcs-pbi-theme.json").read_text())
            page = theme["visualStyles"]["page"]["*"]["background"][0]["color"]["solid"]["color"]
            self.assertEqual(page.upper(), "#F3F3F3")
            bg = theme["visualStyles"]["*"]["*"]["background"][0]
            self.assertEqual((bg["show"], bg["color"]["solid"]["color"].upper()), (True, "#FFFFFF"))
            self.assertFalse(theme["visualStyles"]["*"]["*"]["border"][0]["show"])
            self.assertFalse(theme["visualStyles"]["*"]["*"]["dropShadow"][0]["show"])


    def test_fluent_cards_is_the_default_shell_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run([sys.executable, "-I", "-B", str(THEME), "--out-dir", tmp, "--shell",
                                "--variants", "standard"], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            theme = json.loads((Path(tmp) / "ibcs-pbi-theme.json").read_text())
            vs = theme["visualStyles"]
            self.assertEqual(vs["page"]["*"]["background"][0]["color"]["solid"]["color"].upper(), "#F2F2F2")
            self.assertFalse(vs["*"]["*"]["background"][0]["show"])        # content transparent
            self.assertFalse(vs["*"]["*"]["dropShadow"][0]["show"])        # no shadow on content
            # the card look sits on the shape's container (rendered in the service, rev 4): the shape
            # object's fill and roundEdge did not render as intended, basicShape fails the validator
            shape = vs["shape"]["*"]
            self.assertEqual(shape["background"][0]["color"]["solid"]["color"].upper(), "#FFFFFF")
            self.assertEqual(shape["border"][0]["radius"], 8)
            self.assertEqual(shape["border"][0]["color"]["solid"]["color"].upper(), "#E6E6E6")
            self.assertTrue(shape["dropShadow"][0]["show"])
            self.assertEqual(shape["dropShadow"][0]["transparency"], 88)
            self.assertFalse(shape["outline"][0]["show"])
            self.assertFalse(shape["fill"][0]["show"])
            self.assertNotIn("shape", shape)
            self.assertNotIn("basicShape", vs)


def shadowed(item, on=True):
    name, v = item
    v["visual"].setdefault("visualContainerObjects", {})["dropShadow"] = [{"properties": {"show": lit(str(on).lower())}}]
    return name, v


class CardChrome(unittest.TestCase):
    def test_shadow_allowed_on_card_shape_not_on_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [shadowed(shape("card", 16, 0, 1248, 120)),
                                          textbox("title", "Sales in mEUR"),
                                          shadowed(placed(slicer("sl", "Company", 212), 16, 30, 212, 64))]})
            _, f, _ = lint(r)
            a4 = rows(f, "A4")
            self.assertEqual([x for x in a4 if "card (" in x["location"]], [])
            self.assertEqual(len([x for x in a4 if "sl (" in x["location"]]), 1)

    def test_transparent_content_on_a_card_shape_passes_on_grey_canvas(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [shape("card", 16, 0, 1248, 120),
                                          placed(textbox("inside", "Sales in mEUR"), 16, 10, 600, 24),
                                          placed(textbox("outside", "Notes"), 16, 300, 600, 24)]},
                       canvas="#F2F2F2")
            _, f, _ = lint(r)
            a2 = [x for x in rows(f, "A2") if x["status"] == "fail"]
            self.assertEqual([x for x in a2 if "inside (" in x["location"]], [])
            self.assertEqual(len([x for x in a2 if "outside (" in x["location"]]), 1)


class ZOrder(unittest.TestCase):
    def test_content_below_its_card_shape_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            card = shape("card", 16, 0, 1248, 400)
            card[1]["position"]["z"] = 0
            low = deneb("low", "column-two-tier-variance", (32, 40, 600, 300))
            low[1]["position"]["z"] = 0
            high = deneb("high", "column-two-tier-variance", (640, 40, 600, 300))
            high[1]["position"]["z"] = 1000
            r = report(Path(tmp), {"p1": [card, textbox("title", "Sales in mEUR"), low, high]})
            _, f, _ = lint(r)
            hidden = [x for x in rows(f, "LINT") if "not above its card shape" in x["evidence"]]
            self.assertEqual(len(hidden), 1, hidden)
            self.assertIn("low (", hidden[0]["location"])


class AlignedKnobs(unittest.TestCase):
    def test_px_per_unit_with_y_max_is_fine_on_an_aligned_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [
                textbox("title", "Sales in mEUR"),
                deneb("plain", "column-two-tier-variance", (16, 300, 600, 300), {"pxPerUnit": 4, "yMax": 30}),
                deneb("aligned", "column-two-tier-variance", (640, 300, 200, 300),
                      {"pxPerUnit": 4, "yMax": 230, "varMin": -21, "varMax": 34})]})
            _, f, _ = lint(r)
            both = [x for x in rows(f, "G8") if "both set" in x["evidence"]]
            self.assertEqual([x["location"].split(" / ")[-1].split(" ")[0] for x in both], ["plain"])


class LabelRoom(unittest.TestCase):
    def layout(self, group):
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp) / "g.json"
            g.write_text(json.dumps(group))
            p = subprocess.run([sys.executable, "-I", "-B", str(SCALE_LAYOUT), str(g), "--json"],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout), p.stderr

    def test_bar_label_room_grows_and_names_the_knob(self):
        base = {"id": "e", "visual": "bars", "template": "bar-structure-variance",
                "tiers": {"base": [0, 63], "variance": [-3.4, 2.9]}, "longestLabel": "AB01"}
        plain, _ = self.layout({"pxPerUnit": 8, "members": [base]})
        wide, err = self.layout({"pxPerUnit": 8, "members": [dict(base, longestValueLabel="-10.9%")]})
        row = wide["members"][0]
        self.assertEqual(row["visual"], "bars")
        self.assertEqual(row["setParams"], {"ibcsLabelPx": 48})
        self.assertGreater(row["containerPx"], plain["members"][0]["containerPx"])
        self.assertIn("set ibcsLabelPx = 48", err)

    def test_column_labels_wider_than_their_slot_warn(self):
        out, err = self.layout({"pxPerUnit": 8, "members": [
            {"id": "m", "template": "column-two-tier-variance", "tiers": {"base": [0, 23], "variance": [-2, 2]},
             "categoryCount": 24, "widthPx": 400, "longestValueLabel": "+12.4"}]})
        self.assertIn("category slot", err)
        self.assertIn("columns are squashed", err)
        self.assertEqual(len(out["members"][0]["warnings"]), 2)

    def test_per_member_max_px_lets_the_tightest_member_set_the_scale(self):
        out, _ = self.layout({"members": [
            {"id": "m", "template": "column-two-tier-variance", "tiers": {"base": [0, 23.3], "variance": [-1.4, 1.8]},
             "maxPx": 330},
            {"id": "e", "template": "bar-structure-variance", "tiers": {"base": [0, 63], "variance": [-3.4, 2.9]},
             "longestLabel": "AB01", "maxPx": 640}]})
        m, e = out["members"]
        self.assertLessEqual(m["containerPx"], 330)
        self.assertLessEqual(e["containerPx"], 640)
        self.assertGreater(out["pxPerUnit"], 5)   # not squeezed by the bars' range alone

    def test_align_tiers_gives_months_and_total_the_same_height_and_px_ranges(self):
        out, _ = self.layout({"pxPerUnit": 9, "alignTiers": [["m", "t"]], "members": [
            {"id": "m", "template": "column-two-tier-variance",
             "params": {"periodLabel": "month", "categoryLabelPx": 28},
             "tiers": {"base": [0, 23.3], "variance": [-1.4, 1.8]}},
            {"id": "t", "template": "column-two-tier-variance", "own": True, "basePxPerUnit": 1,
             "params": {"periodType": "year", "categoryLabelPx": 28},
             "tiers": {"base": [0, 216], "variance": [0, 2.5]}}]})
        m, t = out["members"]
        self.assertEqual(m["containerPx"], t["containerPx"])
        self.assertAlmostEqual(m["setParams"]["yMax"] * 9, t["setParams"]["yMax"] * 1, places=3)
        self.assertAlmostEqual(m["setParams"]["varMin"] * 9, t["setParams"]["varMin"], places=3)
        self.assertAlmostEqual(m["setParams"]["varMax"] * 9, t["setParams"]["varMax"], places=3)

    def test_own_member_reports_its_range_and_reserve_adds_px(self):
        group = {"pxPerUnit": 4, "members": [
            {"id": "m", "template": "column-two-tier-variance", "tiers": {"base": [0, 23], "variance": [-2, 3]}},
            {"id": "t", "template": "column-two-tier-variance", "own": True, "basePxPerUnit": 0.4,
             "tiers": {"base": [0, 216], "variance": [0, 2.5]}}]}
        out, _ = self.layout(group)
        t = out["members"][1]
        self.assertAlmostEqual(t["dataRange"], 218.5)
        self.assertAlmostEqual(t["dataPx"], 87.4)
        self.assertTrue(t["ownScale"])
        group["members"][0]["reservePx"] = {"variance": 10}
        more, _ = self.layout(group)
        self.assertEqual(more["members"][0]["containerPx"], out["members"][0]["containerPx"] + 10)

    def test_own_member_scale_is_derived_from_its_cell_or_its_alignment(self):
        cell, _ = self.layout({"pxPerUnit": 9, "members": [
            {"id": "m", "template": "column-two-tier-variance", "tiers": {"base": [0, 23.3], "variance": [-1.4, 1.8]}},
            {"id": "t", "template": "column-two-tier-variance", "own": True, "maxPx": 300,
             "tiers": {"base": [0, 216], "variance": [0, 2.5]}}]})
        t = cell["members"][1]
        self.assertTrue(t["ownScale"])
        self.assertLessEqual(t["containerPx"], 300)
        self.assertGreater(t["containerPx"], 280)               # it fills its cell
        self.assertEqual(t["setParams"]["pxPerUnit"], t["ownPxPerUnit"])
        aligned, _ = self.layout({"pxPerUnit": 9, "alignTiers": [["m", "t"]], "members": [
            {"id": "m", "template": "column-two-tier-variance", "params": {"categoryLabelPx": 28},
             "tiers": {"base": [0, 23.3], "variance": [-1.4, 1.8]}},
            {"id": "t", "template": "column-two-tier-variance", "own": True, "params": {"categoryLabelPx": 28},
             "tiers": {"base": [0, 216], "variance": [0, 2.5]}}]})
        m, t = aligned["members"]
        self.assertEqual(m["containerPx"], t["containerPx"])     # same height as the months
        self.assertLess(t["ownPxPerUnit"], 9)

    def test_waterfall_height_includes_its_fixed_bands(self):
        out, _ = self.layout({"pxPerUnit": 5, "members": [
            {"id": "w", "template": "waterfall-variance", "tiers": {"waterfall": [0, 40]},
             "longestLabel": "Volume", "categoryCount": 6}]})
        w = out["members"][0]
        self.assertGreaterEqual(w["crossPx"], 50)

    def test_category_label_band_sets_the_fixed_height(self):
        a, _ = self.layout({"pxPerUnit": 9, "members": [
            {"id": "a", "template": "column-two-tier-variance", "params": {"categoryLabelPx": 28},
             "tiers": {"base": [0, 10], "variance": [0, 1]}}]})
        b, _ = self.layout({"pxPerUnit": 9, "members": [
            {"id": "b", "template": "column-two-tier-variance", "params": {"periodLabel": "month"},
             "tiers": {"base": [0, 10], "variance": [0, 1]}}]})
        self.assertEqual(a["members"][0]["containerPx"], b["members"][0]["containerPx"])


if __name__ == "__main__":
    unittest.main()


class PublicCopyPbir(unittest.TestCase):
    """OURS (C16): textbox runs and quoted literals in visual.json are public copy."""

    def test_internal_note_in_a_textbox_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [textbox("note", "In line: |ΔBU%| below 0.5 % (proposed)"),
                                          textbox("src", "Source: Sales model")]})
            _, f, _ = lint(r)
            hits = rows(f, "C16")
            self.assertEqual(len(hits), 1)
            self.assertIn("note", hits[0]["location"])

    def test_internal_note_in_a_text_measure_literal_fails(self):
        """Proof run 3: dynamic page text comes from report-level text measures; their literals are public copy."""
        with tempfile.TemporaryDirectory() as tmp:
            r = report(Path(tmp), {"p1": [textbox("src", "Source: Sales model")]})
            (r / "definition" / "reportExtensions.json").write_text(json.dumps({"entities": [{"name": "_Measures", "measures": [
                {"name": "Footnote 3", "expression": '"Gross margin after discounts; change requested"', "references": {}},
                {"name": "Title 1", "expression": '"Sales | " & SELECTEDVALUE ( Region[Region], "All regions" )', "references": {}},
                {"name": "Todo", "expression": '"TODO: wording"', "references": {}}]}]}))
            _, f, _ = lint(r)
            hits = sorted(h["location"].split("[")[-1] for h in rows(f, "C16"))
            self.assertEqual(hits, ["Footnote 3]", "Todo]"])
