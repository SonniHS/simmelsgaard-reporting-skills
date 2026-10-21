"""ibcs-power-bi scripts: Deneb registration, a safe --force, generators that never write on --help.

Run from the repo root:  python3 -m unittest discover -s tests
Each script runs in a subprocess (-I -B) against a scaffold in a temporary directory.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins/ibcs-power-bi/skills"
NEW_PBIP = SKILLS / "ibcs-power-bi/scripts/new_pbip.py"
THEME = SKILLS / "ibcs-power-bi/scripts/build_pbi_theme.py"
MEASURES = SKILLS / "ibcs-power-bi/scripts/report_measures.py"
TO_PBIR = SKILLS / "ibcs-deneb/scripts/to_pbir.py"
GEN_REF = SKILLS / "ibcs-deneb/scripts/gen_reference.py"
TEMPLATE = SKILLS / "ibcs-deneb/assets/templates/column-two-tier-variance.vl.json"
TOKENS = ROOT / "plugins/ibcs/skills/ibcs-notation/assets/ibcs-tokens.json"
DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"


def run(*args):
    return subprocess.run([sys.executable, "-I", "-B", *map(str, args)], capture_output=True, text=True)


def scaffold(tmp: Path, *extra) -> Path:
    r = run(NEW_PBIP, "--out", tmp, "--name", "R", "--semantic-model-id", "00000000-0000-0000-0000-000000000000",
            "--page-name", "pg", *extra)
    assert r.returncode == 0, r.stderr
    return tmp / "R.Report" / "definition"


def add_deneb(d: Path, *extra):
    return run(TO_PBIR, TEMPLATE, "--visual", d / "pages/pg/visuals/v1/visual.json", "--new",
               "--field", "Period=col:Date[Month]", "--field", "AC=m:Measures[AC]", *extra)


class DenebRegistration(unittest.TestCase):
    def test_new_visual_registers_deneb_without_report_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = scaffold(Path(tmp))
            r = add_deneb(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            report = json.loads((d / "report.json").read_text())
            self.assertIn(DENEB, report["publicCustomVisuals"])

    def test_warns_when_no_report_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(TO_PBIR, TEMPLATE, "--visual", Path(tmp) / "loose/visual.json", "--new",
                    "--field", "AC=m:Measures[AC]")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("not registered", r.stderr)

    def test_report_measures_check_finds_and_fixes_unregistered_deneb(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = scaffold(Path(tmp))
            add_deneb(d)
            report = json.loads((d / "report.json").read_text())
            report["publicCustomVisuals"] = []
            (d / "report.json").write_text(json.dumps(report))
            r = run(MEASURES, d.parent, "--check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("publicCustomVisuals", r.stdout)
            self.assertEqual(run(MEASURES, d.parent, "--fix").returncode, 0)
            self.assertIn(DENEB, json.loads((d / "report.json").read_text())["publicCustomVisuals"])

    def test_vega_object_has_version_and_closed_dialog(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = scaffold(Path(tmp))
            add_deneb(d)
            v = json.loads((d / "pages/pg/visuals/v1/visual.json").read_text())
            props = v["visual"]["objects"]["vega"][0]["properties"]
            self.assertEqual(props["isNewDialogOpen"]["expr"]["Literal"]["Value"], "false")
            self.assertEqual(props["version"]["expr"]["Literal"]["Value"], "'6.4.3'")


class ScaffoldForce(unittest.TestCase):
    def test_force_keeps_measures_pages_logical_id_and_deneb(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = scaffold(Path(tmp))
            add_deneb(d)
            ext = d / "reportExtensions.json"
            data = json.loads(ext.read_text())
            data["entities"] = [{"name": "Measures", "measures": [{"name": "X", "expression": "1"}]}]
            ext.write_text(json.dumps(data))
            platform = d.parent / ".platform"
            logical_id = json.loads(platform.read_text())["config"]["logicalId"]
            r = run(NEW_PBIP, "--out", tmp, "--name", "R", "--workspace", "W", "--model", "M", "--force")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(ext.read_text())["entities"][0]["measures"][0]["name"], "X")
            self.assertEqual(json.loads((d / "pages/pages.json").read_text())["pageOrder"], ["pg"])
            self.assertEqual([p.name for p in (d / "pages").iterdir() if p.is_dir()], ["pg"])
            self.assertTrue((d / "pages/pg/visuals/v1/visual.json").exists())
            self.assertEqual(json.loads(platform.read_text())["config"]["logicalId"], logical_id)
            self.assertIn(DENEB, json.loads((d / "report.json").read_text())["publicCustomVisuals"])
            self.assertIn("Data Source=", (d.parent / "definition.pbir").read_text())


class Generators(unittest.TestCase):
    def test_gen_reference_help_and_unknown_flags_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "templates.md"
            for flag in ("--help", "--bogus"):
                run(GEN_REF, flag, "--out", out)
                self.assertFalse(out.exists(), flag)
            self.assertEqual(run(GEN_REF, "--bogus").returncode, 2)
            self.assertEqual(run(GEN_REF, "--out", out).returncode, 0)
            self.assertEqual(run(GEN_REF, "--check", "--out", out).returncode, 0)

    @unittest.skipIf(importlib.util.find_spec("jsonschema"), "jsonschema is installed here")
    def test_theme_validate_without_jsonschema_fails_early(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(THEME, "--validate", "--out-dir", tmp)
            self.assertEqual(r.returncode, 2)
            self.assertIn("jsonschema", r.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_theme_text_colours_use_text_tokens(self):
        tokens = json.loads(TOKENS.read_text())
        theme = json.loads((SKILLS / "ibcs-power-bi/assets/ibcs-pbi-theme.json").read_text())
        self.assertEqual(theme["good"].upper(), tokens["color"]["variance"]["goodText"]["$value"].upper())
        self.assertEqual(theme["bad"].upper(), tokens["color"]["variance"]["badText"]["$value"].upper())


if __name__ == "__main__":
    unittest.main()


class Rev4Defaults(unittest.TestCase):
    def test_deneb_visuals_default_above_the_card_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = scaffold(Path(tmp))
            r = add_deneb(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            v = json.loads((d / "pages/pg/visuals/v1/visual.json").read_text())
            self.assertEqual(v["position"]["z"], 1000)

    def test_column_template_cross_tool_knobs(self):
        t = json.loads(TEMPLATE.read_text())
        params = {p["name"]: p.get("value") for p in t["params"]}
        self.assertEqual(params["pinPxPerUnit"], 0)          # pins on their own scale, sized to the tier
        self.assertEqual(params["pinTierPx"], 48)
        self.assertEqual(params["pinDecimals"], 1)
        self.assertEqual(params["pinClip"], 1)               # outliers clip at ±100 %
        self.assertIs(params["markLastClosed"], True)        # band behind the last closed month
        self.assertNotIn("legendSide", params)               # one legend placement: at the end
        self.assertNotIn("legendSide", TEMPLATE.read_text())
        pins = json.loads((TEMPLATE.parent / "pin-relative-variance.vl.json").read_text())
        self.assertEqual({p["name"]: p.get("value") for p in pins["params"]}["clipPct"], 1)


class Waterfalls(unittest.TestCase):
    """S1: one form per waterfall card, the total variance as an arrow, a CH 4.5 magnifier."""

    TEMPLATES = SKILLS / "ibcs-deneb/assets/templates"
    SCALE_LAYOUT = SKILLS / "ibcs-power-bi/scripts/scale_layout.py"

    def spec(self, name):
        return json.loads((self.TEMPLATES / f"{name}.vl.json").read_text(encoding="utf-8"))

    def test_both_variance_waterfalls_have_an_arrow_and_a_magnifier(self):
        for name, card in (("waterfall-variance", "EX 1.1 card 29"), ("waterfall-variance-time", "EX 1.1 card 11")):
            s = self.spec(name)
            meta = s["usermeta"]["ibcs"]
            self.assertIn(card, meta["cards"])
            self.assertIn("CH 4.5", meta["cards"])
            params = {p["name"]: p.get("value") for p in s["params"]}
            self.assertEqual(params["magnifyBelow"], 0.05, name)   # OURS, a knob
            self.assertIn("magnifyBelow", meta["knobs"])
            descs = " | ".join(layer.get("description", "") for layer in s["layer"])
            self.assertIn("arrow", descs, name)
            self.assertIn("zigzag", descs, name)
            self.assertNotIn("variance bar", descs.lower(), name)   # never an extra bar/column
            # the overview's step labels move into the panel when magnified
            self.assertIn("datum._mag", json.dumps(s["layer"]))

    def test_magnified_waterfalls_reserve_the_panel(self):
        def size(member):
            with tempfile.TemporaryDirectory() as tmp:
                g = Path(tmp) / "g.json"
                g.write_text(json.dumps({"pxPerUnit": 3, "members": [member]}))
                p = subprocess.run([sys.executable, "-I", "-B", str(self.SCALE_LAYOUT), str(g), "--json"],
                                   capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            return json.loads(p.stdout)["members"][0]["containerPx"]

        bar = {"id": "b", "template": "waterfall-variance", "tiers": {"waterfall": [0, 165]}, "longestLabel": "North"}
        self.assertEqual(size(dict(bar, magnify=True)) - size(bar), 170 + 24)
        col = {"id": "t", "template": "waterfall-variance-time", "tiers": {"waterfall": [0, 52]}}
        self.assertEqual(size(dict(col, magnify=True)) - size(col), 150 + 24 + 42)


class ProofRun1(unittest.TestCase):
    """Proof run 1 blockers: pins carry magnitude, no label on a line, no ellipsis on periods, Σ Δ = total."""

    TEMPLATES = SKILLS / "ibcs-deneb/assets/templates"
    SCALE_LAYOUT = SKILLS / "ibcs-power-bi/scripts/scale_layout.py"

    def spec(self, name):
        return json.loads((self.TEMPLATES / f"{name}.vl.json").read_text(encoding="utf-8"))

    def layout(self, group):
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp) / "g.json"
            g.write_text(json.dumps(group))
            p = subprocess.run([sys.executable, "-I", "-B", str(self.SCALE_LAYOUT), str(g), "--json"],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout), p.stderr

    def test_each_pin_tier_gets_its_own_scale_and_aligned_charts_share_it(self):
        out, err = self.layout({"pxPerUnit": 4, "alignTiers": [["m", "t"]], "members": [
            {"id": "m", "template": "column-two-tier-variance", "params": {"pinTier": True},
             "tiers": {"base": [0, 23], "variance": [-2, 3], "pins": [-7.7, 5.6]}},
            {"id": "t", "template": "column-two-tier-variance", "own": True, "basePxPerUnit": 0.4,
             "params": {"pinTier": True}, "tiers": {"base": [0, 216], "variance": [0, 2.5], "pins": [0, 1.3]}},
            {"id": "c", "template": "pin-relative-variance", "pinTierPx": 90, "tiers": {"pins": [-55.6, 8.7]}}]})
        pins = out["pinPxPerUnit"]
        self.assertAlmostEqual(pins["m"], 0.9 * 48 / 13.3, places=1)   # the months fill their own tier
        self.assertEqual(pins["m"], pins["t"])                          # months + Total share one pin scale
        self.assertAlmostEqual(pins["c"], 0.9 * 90 / 64.3, places=1)   # the -55.6 % chart does not shrink the months
        self.assertNotIn("warning", err)

    def test_differing_pin_scales_get_a_scaling_marker(self):
        out, _ = self.layout({"pxPerUnit": 4, "alignTiers": [["m", "t"]], "members": [
            {"id": "m", "template": "column-two-tier-variance", "params": {"pinTier": True},
             "tiers": {"base": [0, 23], "variance": [-2, 3], "pins": [-7.7, 5.6]}},
            {"id": "t", "template": "column-two-tier-variance", "own": True, "basePxPerUnit": 0.4,
             "params": {"pinTier": True}, "tiers": {"base": [0, 216], "variance": [0, 2.5], "pins": [0, 1.3]}},
            {"id": "c", "template": "pin-relative-variance", "pinTierPx": 90, "tiers": {"pins": [-55.6, 8.7]}}]})
        marks = {r["id"]: (r.get("setParams") or {}).get("pinScaleBand") for r in out["members"]}
        self.assertEqual(marks, {"m": -1, "t": -1, "c": -1})
        alone, _ = self.layout({"pxPerUnit": 4, "members": [
            {"id": "m", "template": "column-two-tier-variance", "params": {"pinTier": True},
             "tiers": {"base": [0, 23], "variance": [-2, 3], "pins": [-7.7, 5.6]}}]})
        self.assertNotIn("pinScaleBand", alone["members"][0].get("setParams") or {})

    def test_pin_templates_draw_the_scaling_marker(self):
        for name in ("column-two-tier-variance", "pin-relative-variance"):
            s = self.spec(name)
            params = {p["name"]: p for p in s["params"]}
            self.assertEqual(params["pinScaleBand"]["value"], 0)
            self.assertIn("pinScaleBand", s["usermeta"]["ibcs"]["knobs"])
            band = [l for l in s["layer"] if l.get("description", "").startswith(("pin tier scaling marker", "scaling marker"))]
            self.assertEqual(len(band), 3, name)   # band, its line at the round value, its label
            self.assertTrue(any(l["mark"]["type"] == "text" and "ibcsTextSecondary" in json.dumps(l["mark"]) for l in band))

    def test_a_fixed_stub_pin_scale_warns(self):
        _, err = self.layout({"pxPerUnit": 4, "members": [
            {"id": "m", "template": "column-two-tier-variance", "params": {"pinTier": True, "pinPxPerUnit": 0.5},
             "tiers": {"base": [0, 23], "variance": [-2, 3], "pins": [-7.7, 5.6]}}]})
        self.assertIn("40%", err)

    def test_pins_have_small_heads_and_a_zero_marker(self):
        s = self.spec("column-two-tier-variance")
        params = {p["name"]: p for p in s["params"]}
        self.assertEqual(params["headPx"]["expr"], "ibcsPinHeadMin")
        heads = [layer for layer in s["layer"] if "pin head" in layer.get("description", "")]
        self.assertTrue(heads)
        for layer in heads:   # the head is drawn for a rounded-zero Δ% too (on the axis, as the baseline marker)
            self.assertNotIn("_pZero", json.dumps(layer["transform"]))

    def test_separators_are_ticks_not_lines_through_the_tiers(self):
        for name in ("column-two-tier-variance", "pin-relative-variance", "line-scenarios"):
            sep = [layer for layer in self.spec(name)["layer"] if "AC -> FC separator" in layer.get("description", "")]
            self.assertEqual(len(sep), 1, name)
            self.assertIn("y2", sep[0]["encoding"], name)   # a tick with both ends, not a full-height rule

    def test_one_magnifier_form(self):
        s = self.spec("waterfall-variance")
        t = {x.get("as"): x for x in s["transform"] if isinstance(x.get("as"), str)}
        self.assertIn("+ 27", t["_PL"]["calculate"])   # the panel sits right after the overview (frame 3 px + 24 px gap)
        conn = next(layer for layer in s["layer"] if "connectors" in layer.get("description", ""))
        self.assertTrue(conn["mark"].get("strokeDash"))
        caption = next(layer for layer in s["layer"] if "caption" in layer.get("description", ""))
        self.assertEqual(caption["mark"]["align"], "left")              # next to the zigzag on the origin line
        self.assertIn("_pRight", json.dumps(s["layer"]))                 # a drop's label never reaches the origin line

    def test_period_labels_never_get_an_ellipsis(self):
        for name in ("column-two-tier-variance", "pin-relative-variance", "stacked-columns", "line-scenarios"):
            ax = self.spec(name)["encoding"]["x"]["axis"]
            self.assertEqual(ax.get("labelLimit"), 0, name)
            self.assertIn("substring(", ax["labelExpr"], name)          # Jan -> J
            self.assertIn("Q[1-4]", ax["labelExpr"], name)              # quarters skip the letter step

    def test_structure_rows_count_a_missing_ac_as_zero_and_check_the_total(self):
        s = self.spec("bar-structure-variance")
        t = json.dumps(s["transform"])
        self.assertIn("!isValid(datum._v) && isValid(datum._r) && datum._nV > 0 ? 0 : datum._v", t)
        self.assertIn("TotalDelta", s["usermeta"]["ibcs"]["fields"])
        self.assertIn("_dMis", json.dumps(s["layer"]))

    def test_to_pbir_writes_the_visual_padding(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = scaffold(Path(tmp))
            r = add_deneb(d, "--padding", "12,16,16,8")
            self.assertEqual(r.returncode, 0, r.stderr)
            v = json.loads((d / "pages/pg/visuals/v1/visual.json").read_text())
            props = v["visual"]["visualContainerObjects"]["padding"][0]["properties"]
            self.assertEqual({k: props[k]["expr"]["Literal"]["Value"] for k in props},
                             {"top": "12D", "bottom": "16D", "left": "16D", "right": "8D"})
            bad = add_deneb(scaffold(Path(tmp) / "b"), "--padding", "12,16")
            self.assertNotEqual(bad.returncode, 0)

