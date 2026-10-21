"""Tests for plugins/ibcs/skills/ibcs-review/scripts/ibcs_lint.py against synthetic fixtures.

Run from the repo root:  python3 -m unittest discover -s tests
Stdlib only. The linter runs in a subprocess (-I -B: isolated, no bytecode) from an empty
temporary working directory, so no ibcs-tokens.overrides.json is discovered unless a test puts
one there, and no __pycache__ is written.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
LINT = ROOT / "plugins/ibcs/skills/ibcs-review/scripts/ibcs_lint.py"
ASSETS = ROOT / "plugins/ibcs/skills/ibcs-notation/assets"
TOKENS = ASSETS / "ibcs-tokens.json"
EXAMPLE_OVERRIDES = ASSETS / "ibcs-tokens.overrides.example.json"
FIX = ROOT / "tests/fixtures/ibcs_lint"
OVERRIDES_NAME = "ibcs-tokens.overrides.json"


def run(*args, cwd=None, fmt="json"):
    """Run the linter; return (exit code, findings list, stderr)."""
    with tempfile.TemporaryDirectory() as tmp:
        p = subprocess.run([sys.executable, "-I", "-B", str(LINT), *map(str, args), "--format", fmt],
                           capture_output=True, text=True, cwd=cwd or tmp)
    out = p.stdout.strip()
    return p.returncode, (json.loads(out) if out.startswith("[") else []), p.stderr


def keys(findings):
    return {(f["rule"], f["status"]) for f in findings}


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class PbirSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.f, _ = run("pbir", FIX / "pbir-ibcs-sample")

    def test_exit_code_signals_must_failures(self):
        self.assertEqual(self.code, 1)

    def test_expected_rules(self):
        k = keys(self.f)
        for expected in [("K9", "fail"), ("D11", "fail"), ("G1", "fail"), ("C12", "fail"),
                         ("A5", "fail"), ("A6", "fail"), ("A4", "fail"), ("A2", "fail"),
                         ("A3", "fail"), ("A10", "fail"), ("A11", "fail"), ("C10", "fail"),
                         ("G2", "check")]:
            self.assertIn(expected, k)

    def test_clean_visual_has_no_findings(self):
        self.assertFalse([f for f in self.f if "colOk" in f["location"]])

    def test_scatter_legend_and_log_are_not_hard_failures(self):
        scatter = [f for f in self.f if "scatter1" in f["location"]]
        self.assertFalse([f for f in scatter if f["rule"] == "C10"])
        self.assertTrue(all(f["status"] == "check" for f in scatter if f["rule"] == "G2"))

    def test_rule_ids_are_checklist_ids(self):
        self.assertFalse([f for f in self.f if f["rule"].startswith("EX")])
        self.assertTrue(all(re.fullmatch(r"[A-K]\d+|LINT", f["rule"]) for f in self.f))

    def test_bubble_chart_legend_allowed(self):
        self.assertFalse([f for f in self.f if "bubble1" in f["location"] and f["rule"] == "C10"])

    def test_banned_words_only_in_titles(self):
        # body textbox (below the header band) and the key-message sentence are not titles
        self.assertFalse([f for f in self.f if ("body1" in f["location"] or "msg1" in f["location"])
                          and f["rule"] in ("A10", "A11")])
        self.assertIn(("A11", "fail"), keys(f for f in self.f if "title1" in f["location"]))

    def test_a14_auto_units_is_must_check(self):
        a14 = [f for f in self.f if f["rule"] == "A14"]
        self.assertTrue(a14)
        self.assertTrue(all(f["sev"] == "M" and f["status"] == "check" for f in a14))

    def test_markdown_output(self):
        code, _, _ = run("pbir", FIX / "pbir-ibcs-sample", fmt="md")
        self.assertEqual(code, 1)


class PbirValueAxis(unittest.TestCase):
    """G1 fails only when the configured value-axis range excludes zero."""

    COL_OK = FIX / "pbir-ibcs-sample/Sample.Report/definition/pages/p1/visuals/colOk/visual.json"

    def lint_axis(self, props):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "A.Report/definition"
            (d / "pages/p1/visuals/v1").mkdir(parents=True)
            write_json(d / "report.json", {})
            write_json(d / "pages/p1/page.json", {"name": "p1", "displayName": "P"})
            visual = json.loads(self.COL_OK.read_text(encoding="utf-8"))
            visual["visual"]["objects"]["valueAxis"] = [{"properties": {
                k: {"expr": {"Literal": {"Value": v}}} for k, v in props.items()}}]
            write_json(d / "pages/p1/visuals/v1/visual.json", visual)
            _, f, _ = run("pbir", Path(tmp) / "A.Report")
        return [x for x in f if x["rule"] == "G1"]

    def test_range_including_zero_passes(self):
        for props in ({"start": "-20D"}, {"end": "50D"}, {"start": "-20D", "end": "-0D"},
                      {"start": "true", "end": "false"}):
            with self.subTest(props=props):
                self.assertEqual(self.lint_axis(props), [])

    def test_range_excluding_zero_fails(self):
        for props in ({"start": "10D"}, {"start": "-50D", "end": "-10D"}):
            with self.subTest(props=props):
                self.assertEqual([(x["sev"], x["status"]) for x in self.lint_axis(props)], [("M", "fail")])

    def test_dot_inside_definition_finds_theme(self):
        definition = FIX / "pbir-ibcs-sample/Sample.Report/definition"
        _, f, _ = run("pbir", ".", cwd=definition)
        self.assertIn(("A5", "fail"), keys(f))
        self.assertFalse([x for x in f if "not found" in x["evidence"]])


class VegaLite(unittest.TestCase):
    def test_grid_is_check_and_time_x_not_g1(self):
        code, f, _ = run("vegalite", FIX / "vegalite/time-x-grid.json")
        self.assertEqual(code, 0)
        self.assertEqual(keys(f), {("A8", "check")})

    def test_indexed_zoom_is_check(self):
        code, f, _ = run("vegalite", FIX / "vegalite/indexed-zoom.json")
        self.assertEqual(code, 0)
        self.assertEqual(keys(f), {("G1", "check")})

    def test_truncated_value_axis_fails(self):
        code, f, _ = run("vegalite", FIX / "vegalite/truncated.json")
        self.assertEqual(code, 1)
        self.assertIn(("G1", "fail"), keys(f))

    def test_auto_detects_vegalite(self):
        code, f, _ = run(FIX / "vegalite/truncated.json")
        self.assertEqual(code, 1)
        self.assertIn(("G1", "fail"), keys(f))


class ThemeAndTokens(unittest.TestCase):
    def test_clean_theme(self):
        code, f, _ = run("theme", FIX / "themes/ibcs-clean-theme.json")
        self.assertEqual((code, f), (0, []))

    def test_bundled_tokens_only_report_default_green_as_check(self):
        code, f, _ = run("tokens", TOKENS)
        self.assertEqual(code, 0)
        self.assertEqual(keys(f), {("E6", "check")})
        (green,) = f
        self.assertEqual((green["sev"], green["location"].split(":")[-1]), ("S", "color.variance.good"))
        self.assertIn("bundled default", green["evidence"])

    def test_default_token_path_is_bundled_file(self):
        # A theme lint without --tokens compares good/bad/neutral against the bundled tokens.
        code, f, _ = run("theme", FIX / "themes/ibcs-clean-theme.json", "--no-overrides")
        self.assertEqual((code, f), (0, []))

    def test_example_overrides_pass(self):
        code, f, _ = run("tokens", TOKENS, "--overrides", EXAMPLE_OVERRIDES)
        self.assertEqual((code, f), (0, []))

    def test_bad_overrides_fail(self):
        code, f, _ = run("tokens", TOKENS, "--overrides", FIX / "tokens/overrides-bad.json")
        self.assertEqual(code, 1)
        for expected in [("D8", "fail"), ("D5", "fail"), ("E7", "fail"), ("D1", "fail")]:
            self.assertIn(expected, keys(f))

    def test_wrong_impact_hue_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            ovr = write_json(Path(tmp) / "o.json", {"color": {"variance": {"bad": {"$value": "#2F6DB5"}}}})
            code, f, _ = run("tokens", TOKENS, "--overrides", ovr)
        self.assertEqual(code, 1)
        self.assertTrue(any(x["rule"] == "E6" and "hue" in x["evidence"] for x in f))


    def test_gray_impact_colour_fails(self):
        for path in ("bad", "cvd.bad"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                node = {"$value": "#808080"}
                for key in reversed(path.split(".")):
                    node = {key: node}
                ovr = write_json(Path(tmp) / "o.json", {"color": {"variance": node}})
                code, f, _ = run("tokens", TOKENS, "--overrides", ovr)
                self.assertEqual(code, 1)
                self.assertTrue(any(x["rule"] == "E6" and x["status"] == "fail" and "gray" in x["evidence"]
                                    and x["location"].endswith(f"color.variance.{path}") for x in f))

    def test_malformed_colour_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            ovr = write_json(Path(tmp) / "o.json", {"color": {"variance": {"good": {"$value": "#GGG"}}}})
            code, f, err = run("tokens", TOKENS, "--overrides", ovr)
        self.assertEqual((code, f), (2, []))
        self.assertIn("not a hex colour", err)
        self.assertNotIn("Traceback", err)


class VarianceTextColours(unittest.TestCase):
    """color.variance.*Text tint variance numbers and must meet 4.5:1 text contrast in their hue family."""

    def lint(self, overrides):
        with tempfile.TemporaryDirectory() as tmp:
            return run("tokens", TOKENS, "--overrides", write_json(Path(tmp) / "o.json", overrides))

    def test_bundled_text_colours_meet_text_contrast(self):
        _, f, _ = run("tokens", TOKENS, "--no-overrides")
        self.assertFalse([x for x in f if "Text" in x["location"]])

    def test_bright_green_as_text_fails(self):
        code, f, _ = self.lint({"color": {"variance": {"goodText": {"$value": "#8CB400"}}}})
        self.assertEqual(code, 1)
        self.assertTrue(any(x["rule"] == "E6" and x["status"] == "fail" and "WCAG 1.4.3" in x["ibcs"]
                            and x["location"].endswith("color.variance.goodText") for x in f))

    def test_text_colour_outside_hue_family_fails(self):
        code, f, _ = self.lint({"color": {"variance": {"badText": {"$value": "#1F4FA0"}}}})
        self.assertEqual(code, 1)
        self.assertTrue(any(x["location"].endswith("color.variance.badText") and "hue family" in x["evidence"] for x in f))

    def test_new_format_and_clamp_tokens_exist(self):
        t = json.loads(TOKENS.read_text(encoding="utf-8"))
        fmt = t["number"]["format"]
        self.assertEqual(fmt["relativeVariance1"]["d3"]["$value"], "+.1%")
        self.assertEqual(fmt["plainRatio"]["excel"]["$value"], "#,0.00")
        g = t["geometry"]
        for node, lo, hi in ((g["pin"]["stemPx"], 2, 4), (g["pin"]["headPx"], 6, 10), (g["triangleSizePx"], 6, 12)):
            self.assertEqual((node["min"]["$value"], node["max"]["$value"]), (lo, hi))


class ReportMeasures(unittest.TestCase):
    """Report-level measures in definition/reportExtensions.json (reports on a shared model)."""

    @classmethod
    def setUpClass(cls):
        cls.code, cls.f, _ = run("pbir", FIX / "pbir-report-measures", "--no-overrides")

    def of(self, measure):
        return [x for x in self.f if x["location"].endswith(f"[{measure}]")]

    def test_hidden_report_measure_fails(self):
        self.assertEqual(self.code, 1)
        (hidden,) = self.of("Helper Hidden")
        self.assertEqual((hidden["rule"], hidden["sev"], hidden["status"]), ("LINT", "M", "fail"))
        self.assertIn("Something's wrong", hidden["fix"])

    def test_visible_plain_measure_is_clean(self):
        self.assertEqual(self.of("Sales AC&FC"), [])

    def test_non_token_colours_in_expression(self):
        (stray,) = self.of("SVG Bars Rainbow")
        self.assertEqual((stray["rule"], stray["status"]), ("A5", "check"))
        self.assertIn("#FF8800", stray["evidence"])
        self.assertIn("#4400FF", stray["evidence"])   # 3-digit hex expanded

    def test_bright_impact_colour_on_text_is_check(self):
        (tint,) = self.of("SVG Card Sales")
        self.assertEqual((tint["rule"], tint["sev"], tint["status"]), ("E6", "S", "check"))
        self.assertIn("color.variance.good", tint["evidence"])
        self.assertNotIn("#D00000", tint["evidence"])   # badText is a token and meets 4.5:1

    def test_abs_of_variance_is_check(self):
        (pin,) = self.of("SVG Pin Length")
        self.assertEqual((pin["rule"], pin["sev"], pin["status"]), ("E14", "S", "check"))

    def test_abs_in_denominator_is_must_check(self):
        (rel,) = self.of("Sales ΔPY% Wrong")
        self.assertEqual((rel["rule"], rel["sev"], rel["status"]), ("E14", "M", "check"))

    def test_unguarded_relative_divide_is_must_check(self):
        (rel,) = self.of("Sales ΔPY% Unguarded")
        self.assertEqual((rel["rule"], rel["sev"], rel["status"]), ("E14", "M", "check"))
        self.assertEqual(self.of("Sales ΔPY% Guarded"), [])

    def test_abs_of_plain_value_is_not_flagged(self):
        self.assertEqual(self.of("Sales Total"), [])


class ScenarioInk(unittest.TestCase):
    """Generic rule: scenario inks must be gray; a documented (src ORG) low-chroma ink is a check."""

    def lint_ink(self, value, src=None):
        node = {"$value": value}
        if src:
            node["$extensions"] = {"ibcs": {"src": src, "ref": "Notation manual, test"}}
        with tempfile.TemporaryDirectory() as tmp:
            ovr = write_json(Path(tmp) / "o.json", {"color": {"scenario": {"ac": node}}})
            return run("tokens", TOKENS, "--overrides", ovr)

    def ac_findings(self, findings):
        return [f for f in findings if f["rule"] == "D8" and f["location"].endswith("color.scenario.ac")]

    def test_saturated_ink_fails(self):
        code, f, _ = self.lint_ink("#1F5FBF", src="ORG")
        self.assertEqual(code, 1)
        self.assertEqual([(x["sev"], x["status"]) for x in self.ac_findings(f)], [("M", "fail")])

    def test_tinted_ink_without_org_provenance_fails(self):
        code, f, _ = self.lint_ink("#1F2A44")
        self.assertEqual(code, 1)
        self.assertEqual([(x["sev"], x["status"]) for x in self.ac_findings(f)], [("M", "fail")])

    def test_documented_low_chroma_ink_is_check(self):
        code, f, _ = self.lint_ink("#1F2A44", src="ORG")
        self.assertEqual(code, 0)
        self.assertEqual([(x["sev"], x["status"]) for x in self.ac_findings(f)], [("S", "check")])

    def test_gray_ink_passes(self):
        code, f, _ = self.lint_ink("#333333")
        self.assertEqual(code, 0)
        self.assertEqual(self.ac_findings(f), [])


class OverridesDiscovery(unittest.TestCase):
    BAD = {"color": {"scenario": {"ac": {"$value": "#1F5FBF"}}}}

    def test_overrides_found_in_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_json(Path(tmp) / OVERRIDES_NAME, self.BAD)
            code, f, _ = run("tokens", TOKENS, cwd=tmp)
        self.assertEqual(code, 1)
        self.assertIn(("D8", "fail"), keys(f))

    def test_overrides_found_in_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_json(Path(tmp) / OVERRIDES_NAME, self.BAD)
            sub = Path(tmp) / "report" / "pages"
            sub.mkdir(parents=True)
            code, f, _ = run("tokens", TOKENS, cwd=sub)
        self.assertEqual(code, 1)
        self.assertIn(("D8", "fail"), keys(f))

    def test_overrides_found_next_to_linted_token_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tokdir = Path(tmp) / "design"
            tokdir.mkdir()
            shutil.copy(TOKENS, tokdir / "ibcs-tokens.json")
            write_json(tokdir / OVERRIDES_NAME, self.BAD)
            code, f, _ = run("tokens", tokdir / "ibcs-tokens.json")
        self.assertEqual(code, 1)
        self.assertIn(("D8", "fail"), keys(f))

    def test_no_overrides_ignores_discovered_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_json(Path(tmp) / OVERRIDES_NAME, self.BAD)
            code, f, _ = run("tokens", TOKENS, "--no-overrides", cwd=tmp)
        self.assertEqual(code, 0)
        self.assertEqual(keys(f), {("E6", "check")})

    def test_explicit_overrides_win_over_discovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_json(Path(tmp) / OVERRIDES_NAME, self.BAD)
            code, f, _ = run("tokens", TOKENS, "--overrides", EXAMPLE_OVERRIDES, cwd=tmp)
        self.assertEqual((code, f), (0, []))

    def test_missing_explicit_overrides_exits_2(self):
        code, f, err = run("tokens", TOKENS, "--overrides", FIX / "tokens/does-not-exist.json")
        self.assertEqual(code, 2)
        self.assertEqual(f, [])
        self.assertIn("does not exist", err)

    def test_missing_target_exits_2(self):
        code, _, err = run("tokens", FIX / "tokens/does-not-exist.json")
        self.assertEqual(code, 2)
        self.assertIn("does not exist", err)


class DarkLayer(unittest.TestCase):
    """A token layer passed with --theme (here a generic dark mode) is checked with dark rules."""

    LAYER = FIX / "tokens/dark-layer.json"

    def test_dark_layer_passes(self):
        code, f, _ = run("tokens", TOKENS, "--theme", self.LAYER, "--no-overrides")
        self.assertEqual((code, f), (0, []))

    def test_dark_failures(self):
        base = json.loads(self.LAYER.read_text(encoding="utf-8"))
        for path, value, expected in [("scenario.ac", "#252525", "D5"), ("variance.bad", "#303030", "E6"),
                                      ("text.secondary", "#404040", "A2"), ("variance.good", "#FF4D4D", "E7")]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                layer = json.loads(json.dumps(base))
                node = layer["color"]
                for key in path.split("."):
                    node = node[key]
                node["$value"] = value
                file = write_json(Path(tmp) / "layer.json", layer)
                code, f, _ = run("tokens", TOKENS, "--theme", file, "--no-overrides")
                self.assertEqual(code, 1)
                self.assertIn((expected, "fail"), keys(f))


GEN_TOKENS = ROOT / "plugins/ibcs/skills/ibcs-notation/scripts/gen_tokens.mjs"


@unittest.skipUnless(shutil.which("node"), "node not installed")
class GenTokensScript(unittest.TestCase):
    """The JS/TS token generator resolves the same values as the Python resolver of the linter."""

    def gen(self, out_name, *args):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / out_name
            p = subprocess.run(["node", str(GEN_TOKENS), "--out", str(out), *map(str, args)],
                               capture_output=True, text=True, cwd=tmp)
            return p.returncode, (out.read_text(encoding="utf-8") if out.exists() else ""), p.stderr

    def test_json_matches_python_resolution_with_overrides(self):
        sys.path.insert(0, str(LINT.parent))
        try:
            import ibcs_lint
        finally:
            sys.path.pop(0)
        code, text, err = self.gen("t.json", "--overrides", EXAMPLE_OVERRIDES)
        self.assertEqual(code, 0, err)
        out = json.loads(text)
        tokens = ibcs_lint.load_tokens(TOKENS, EXAMPLE_OVERRIDES)
        for path in ("color.variance.good", "color.scenario.pl.stroke", "color.variance.cvd.badText",
                     "typography.family.web", "geometry.pin.headPx.max", "number.format.plainRatio.d3"):
            node = out
            for part in path.split("."):
                node = node[part]
            self.assertEqual(node, ibcs_lint.token_value(tokens, path), path)

    def test_ts_module_is_const_and_has_no_metadata(self):
        code, text, err = self.gen("t.ts", "--no-overrides")
        self.assertEqual(code, 0, err)
        self.assertIn("export const tokens = {", text)
        self.assertIn("} as const;", text)
        self.assertNotIn("$description", text)
        self.assertNotIn("$value", text)

    def test_css_and_bad_extension(self):
        code, text, _ = self.gen("t.css", "--no-overrides")
        self.assertEqual(code, 0)
        self.assertIn("--ibcs-color-variance-goodText: #5A7A00;", text)
        self.assertIn("--ibcs-typography-size-label-px: 12px;", text)
        code, _, err = self.gen("t.txt", "--no-overrides")
        self.assertEqual(code, 2)
        self.assertIn(".ts, .json or .css", err)

    def test_broken_alias_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            ovr = write_json(Path(tmp) / "o.json", {"color": {"scenario": {"ac": {"$value": "{color.nope}"}}}})
            code, _, err = self.gen("t.json", "--overrides", ovr)
        self.assertEqual(code, 2)
        self.assertIn("token not found: color.nope", err)


class NoBytecode(unittest.TestCase):
    def test_no_pycache_next_to_linter(self):
        run("tokens", TOKENS)
        self.assertFalse((LINT.parent / "__pycache__").exists())


class PbirBindings(unittest.TestCase):
    """Bindings that break a Power BI visual in the service although every measure is fine."""

    @classmethod
    def setUpClass(cls):
        cls.code, cls.f, _ = run("pbir", FIX / "pbir-bindings", "--no-overrides")

    def at(self, visual):
        return [x for x in self.f if f"/ {visual} (" in x["location"]]

    def test_report_measure_without_extension_schema_fails(self):
        self.assertEqual(self.code, 1)
        rows = [x for x in self.at("tblBad") if "Schema" in x["evidence"]]
        self.assertEqual([(x["rule"], x["sev"], x["status"]) for x in rows], [("LINT", "M", "fail")])
        self.assertIn("2 binding(s)", rows[0]["evidence"])   # projection and sort
        self.assertIn("Missing_References", rows[0]["fix"])

    def test_active_flag_on_table_column_fails_but_not_on_slicer(self):
        rows = [x for x in self.at("tblBad") if "active" in x["evidence"]]
        self.assertEqual([(x["sev"], x["status"]) for x in rows], [("M", "fail")])
        self.assertEqual(self.at("slicer1"), [])

    def test_image_column_narrower_than_image_width_is_check(self):
        rows = [x for x in self.at("tblBad") if "imageWidth" in x["evidence"]]
        self.assertEqual(len(rows), 1)
        self.assertIn("SVG Pin", rows[0]["evidence"])
        self.assertEqual((rows[0]["sev"], rows[0]["status"]), ("S", "check"))

    def test_clean_table_has_no_findings(self):
        self.assertEqual(self.at("tblOk"), [])

    def test_measures_without_references_are_one_info_row(self):
        rows = [x for x in self.f if "without 'references'" in x["evidence"]]
        self.assertEqual([(x["sev"], x["status"]) for x in rows], [("I", "check")])
        self.assertIn("SVG Bar", rows[0]["evidence"])
        self.assertNotIn("SVG Pin", rows[0]["evidence"])

    def test_deneb_field_outside_dataset_and_stray_colour(self):
        rows = self.at("deneb2")
        fields = [x for x in rows if "not in the visual's dataset" in x["evidence"]]
        self.assertEqual(len(fields), 1)
        self.assertIn("Month Short", fields[0]["evidence"])     # native name, the dataset calls it Period
        self.assertNotIn("Polarity", fields[0]["evidence"])     # optional: isValid(...) ? ... : default
        self.assertTrue(any(x["rule"] == "A5" and "#FF8800" in x["evidence"] for x in rows))


class VisualSpec(unittest.TestCase):
    """The mechanical §10 rules of the visual spec format (JSON fixtures; YAML needs PyYAML)."""

    def test_valid_spec_is_clean(self):
        code, f, err = run("spec", FIX / "spec/good.json")
        self.assertEqual((code, f), (0, []), err)

    def test_auto_detects_a_spec(self):
        code, f, _ = run(FIX / "spec/bad.json")
        self.assertEqual(code, 1)
        self.assertTrue(f and all(re.fullmatch(r"V\d+", x["rule"]) for x in f))

    def test_each_broken_rule_is_reported(self):
        _, f, _ = run("spec", FIX / "spec/bad.json")
        rules = {x["rule"] for x in f}
        for rule in ("V1", "V2", "V3", "V4", "V5", "V7", "V10", "V12", "V13", "V14", "V15", "V17"):
            self.assertIn(rule, rules)
        self.assertTrue(any("'v9'" in x["evidence"] for x in f))   # highlight on an unknown visual

    def test_worked_examples_pass(self):
        try:
            import yaml   # noqa: F401
        except ImportError:
            self.skipTest("PyYAML not installed")
        text = (ROOT / "plugins/ibcs/skills/ibcs-composition/references/visual-spec-format.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```yaml\n(ibcsVisualSpec: \"1.0\"\npage:\n  id: .*?)```", text, re.S)
        self.assertEqual(len(blocks), 2)
        for b in blocks:
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "example.yaml"
                p.write_text(b, encoding="utf-8")
                code, f, err = run("spec", p)
            self.assertEqual((code, f), (0, []), err)


class RenderedDom(unittest.TestCase):
    """data-role marks of a rendered web chart against the tokens."""

    @classmethod
    def setUpClass(cls):
        cls.code, cls.f, _ = run("dom", FIX / "dom/page.html", "--no-overrides")

    def test_notation_and_colour_failures(self):
        self.assertEqual(self.code, 1)
        k = {(x["rule"], x["status"]) for x in self.f}
        for expected in [("D4", "fail"), ("D6", "fail"), ("D7", "fail"), ("E6", "fail"), ("C12", "fail"), ("A5", "check")]:
            self.assertIn(expected, k)

    def test_graphic_green_on_a_number_fails(self):
        self.assertTrue(any(x["rule"] == "E6" and "variance number" in x["evidence"] and "#8CB400" in x["evidence"]
                            for x in self.f))

    def test_correct_marks_are_clean(self):
        # the first group uses AC/PY/BU/FC, a CSS-variable impact fill and goodText correctly
        self.assertFalse([x for x in self.f if "#5A7A00" in x["evidence"] or "#A6A6A6" in x["evidence"]])
        self.assertFalse([x for x in self.f if x["rule"] == "D5"])

    def test_page_without_roles_is_one_info_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "plain.html"
            p.write_text("<svg><rect fill='#404040'/></svg>", encoding="utf-8")
            code, f, _ = run("dom", p, "--no-overrides")
        self.assertEqual(code, 0)
        self.assertEqual([(x["rule"], x["sev"]) for x in f], [("LINT", "I")])



class CrossReviewRegressions(unittest.TestCase):
    """False passes and false failures found in the round-2 cross review."""

    def lint_spec_dict(self, spec):
        with tempfile.TemporaryDirectory() as tmp:
            return run("spec", write_json(Path(tmp) / "s.json", spec))

    def base_spec(self):
        return json.loads((FIX / "spec/good.json").read_text(encoding="utf-8"))

    def test_v16_deviation_for_another_visual_does_not_count(self):
        spec = self.base_spec()
        v = spec["visuals"][1]
        v["id"] = "v1"
        v["data"]["category"]["extension"] = {"scaleGroup": "own"}
        spec["scaleGroups"].append({"id": "own", "unit": "mEUR", "kind": "absolute", "members": ["v1"]})
        spec["deviations"] = [{"rule": "CH 4.1", "what": "x", "reason": "y", "acceptedBy": "owner", "visual": "v10"}]
        _, f, _ = self.lint_spec_dict(spec)
        self.assertTrue(any(x["rule"] == "V16" and "deviations" in x["evidence"] for x in f))

    def test_v5_two_absolute_groups_of_one_unit_fail(self):
        spec = self.base_spec()
        spec["scaleGroups"].append({"id": "meur2", "unit": "mEUR", "kind": "absolute", "members": ["k1"]})
        _, f, _ = self.lint_spec_dict(spec)
        self.assertTrue(any(x["rule"] == "V5" and "absolute groups in mEUR" in x["evidence"] for x in f))

    def test_v5_member_of_unknown_visual_fails(self):
        spec = self.base_spec()
        spec["scaleGroups"][0]["members"].append("v9.base")
        _, f, _ = self.lint_spec_dict(spec)
        self.assertTrue(any(x["rule"] == "V5" and "'v9.base'" in x["evidence"] for x in f))

    def test_v7_by_line_needs_every_line(self):
        spec = self.base_spec()
        d = spec["visuals"][1]["data"]
        d["measures"][0]["polarity"] = "by-line"
        d["rows"] = [{"line": "Revenue", "type": "total", "polarity": 1}, {"line": "Costs", "type": "total"}]
        _, f, _ = self.lint_spec_dict(spec)
        self.assertTrue(any(x["rule"] == "V7" and "Costs" in x["evidence"] for x in f))

    def test_small_multiples_panel_is_checked(self):
        spec = self.base_spec()
        spec["visuals"].append({"id": "sm", "type": "small-multiples", "scaleGroup": "meur",
                                "facet": {"maxPanels": 6, "others": True},
                                "data": {"category": {"field": "'Date'[Month]", "kind": "time"}},
                                "panel": {"type": "bar"}})
        _, f, _ = self.lint_spec_dict(spec)
        self.assertTrue(any(x["rule"] == "V4" and "sm.panel" in x["location"] for x in f))

    def test_v15_ignores_ac_fc_in_notes(self):
        spec = self.base_spec()
        spec["visuals"] = [spec["visuals"][0]]          # the kpi cards only: no AC&FC scenario plotted
        spec["scaleGroups"] = []
        spec["page"]["context"]["period"].pop("asOf", None)
        spec["visuals"][0]["notes"] = "AC&FC is shown on the next page"
        _, f, _ = self.lint_spec_dict(spec)
        self.assertFalse([x for x in f if x["rule"] == "V15"], f)

    def test_null_yaml_items_do_not_crash(self):
        spec = self.base_spec()
        spec["visuals"][1]["tiers"].append(None)
        spec["visuals"][1]["markers"] = [None]
        spec["page"]["context"]["slicers"].append(None)
        code, _, err = self.lint_spec_dict(spec)
        self.assertIn(code, (0, 1), err)

    def test_deneb_params_and_prose_are_not_fields(self):
        vl = {"$schema": "https://vega.github.io/schema/vega-lite/v6.json",
              "description": "reads datum['Period'] in prose only",
              "usermeta": {"note": "datum.Ghost"},
              "params": [{"name": "Missing", "value": 42}],
              "data": {"name": "dataset"}, "mark": "bar",
              "encoding": {"x": {"field": "Missing", "type": "nominal"}, "y": {"field": "AC", "type": "quantitative"}}}
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(FIX / "pbir-bindings/Sample.Report", Path(tmp) / "Sample.Report")
            vis = Path(tmp) / "Sample.Report/definition/pages/p1/visuals"
            for d in vis.iterdir():
                if d.name.startswith("deneb"):
                    shutil.rmtree(d)
            (vis / "dn").mkdir()
            write_json(vis / "dn/visual.json", {"name": "dn", "position": {"x": 0, "y": 0, "width": 100, "height": 100}, "visual": {
                "visualType": "deneb7E15AEF80B9E4D4F8E12924291ECE89A",
                "query": {"queryState": {"dataset": {"projections": [
                    {"field": {"Column": {"Expression": {"SourceRef": {"Entity": "Date"}}, "Property": "Month"}},
                     "queryRef": "Date.Month", "nativeQueryRef": "Month", "displayName": "AC"}]}}},
                "objects": {"vega": [{"properties": {"jsonSpec": {"expr": {"Literal": {"Value": "'" + json.dumps(vl).replace("'", "''") + "'"}}}}}]}}})
            _, f, _ = run("pbir", Path(tmp) / "Sample.Report")
        fields = [x for x in f if x["rule"] == "LINT" and "not in the visual's dataset" in x["evidence"]]
        self.assertTrue(fields and "Missing" in fields[0]["evidence"], f)
        self.assertFalse(any("Period" in x["evidence"] or "Ghost" in x["evidence"] for x in fields))

    def dom(self, svg):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "p.html"
            p.write_text(svg, encoding="utf-8")
            return run("dom", p, "--no-overrides")[1]

    def test_dom_py_triangle_and_lines_are_checked(self):
        f = self.dom("<svg><polygon data-role='triangle-PY' fill='#404040'/>"
                     "<path data-role='line-AC' stroke='#A6A6A6' fill='none'/></svg>")
        self.assertTrue(any(x["rule"] == "D5" for x in f))
        self.assertTrue(any(x["rule"] == "D4" for x in f))

    def test_dom_plan_stroke_must_be_the_token(self):
        f = self.dom("<svg><rect data-role='col-PL' fill='#FFFFFF' stroke='#0064FF'/></svg>")
        self.assertTrue(any(x["rule"] == "D6" for x in f))

    def test_dom_forecast_url_must_point_at_a_pattern(self):
        bad = self.dom("<svg><defs><linearGradient id='g'/></defs><rect data-role='col-FC' fill='url(#g)'/>"
                       "<rect data-role='col-FC' fill='url(#missing)'/></svg>")
        self.assertEqual(len([x for x in bad if x["rule"] == "D7"]), 2)
        good = self.dom("<svg><defs><pattern id='h'/></defs><rect data-role='col-FC' fill='url(#h)'/></svg>")
        self.assertFalse([x for x in good if x["rule"] == "D7"])

class RoundThreeRegressions(unittest.TestCase):
    """False passes and false failures found in the round-3 release test."""

    def dom(self, html):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "p.html"
            page.write_text(html, encoding="utf-8")
            return run("dom", page, "--no-overrides")[1]

    def test_zero_variance_label_is_unsigned_and_uncoloured(self):
        bad = self.dom("<svg><text data-role='variance-label' data-impact='good' fill='#5A7A00'>+0.0</text>"
                       "<text data-role='variance-label' data-impact='bad' fill='#D00000'>\u22120.0</text></svg>")
        self.assertEqual(sorted({(x["rule"], x["status"]) for x in bad}), [("B5", "fail"), ("E6", "fail")])
        ok = self.dom("<svg><text data-role='variance-label' data-impact='none' fill='#000000'>0.0</text>"
                      "<text data-role='variance-label' data-impact='good' fill='#5A7A00'>+0.1</text></svg>")
        self.assertFalse([x for x in ok if x["rule"] in ("B5", "E6")])

    def test_html_variance_numbers_use_css_color(self):
        good = self.dom("<div><span data-role='variance-label' data-impact='good' style='color: rgb(90, 122, 0)'>"
                        "+8.3</span><td data-role='variance-label' data-impact='bad' style='color:#D00000'>-1</td></div>")
        self.assertFalse([x for x in good if x["rule"] == "E6"])
        bad = self.dom("<div><span data-role='variance-label' data-impact='good' style='color:#8CB400'>+8.3</span></div>")
        self.assertTrue(any(x["rule"] == "E6" and x["status"] == "fail" for x in bad))
        inherited = self.dom("<div style='color:#8CB400'><span data-role='variance-label' data-impact='good'>+1</span></div>")
        self.assertTrue(any(x["rule"] == "E6" for x in inherited))

    def test_line_markers_and_plan_lines(self):
        f = self.dom("<svg><defs><pattern id='h'/></defs>"
                     "<rect data-role='marker-BU' fill='#404040' stroke='#404040'/>"
                     "<rect data-role='marker-FC' fill='#404040'/>"
                     "<path data-role='line-PL' stroke='#A6A6A6' fill='none'/></svg>")
        self.assertEqual(len([x for x in f if x["rule"] == "D6"]), 2)
        self.assertTrue(any(x["rule"] == "D7" for x in f))
        ok = self.dom("<svg><defs><pattern id='h'/></defs>"
                      "<rect data-role='marker-BU' fill='#FFFFFF' stroke='#404040'/>"
                      "<rect data-role='marker-FC' fill='url(#h)'/>"
                      "<path data-role='line-BU' stroke='#404040' fill='none'/></svg>")
        self.assertFalse([x for x in ok if x["rule"] in ("D6", "D7")])

    def test_waterfall_steps_and_stacked_segments(self):
        ok = self.dom("<svg><rect data-role='step' data-kind='base' fill='#404040'/>"
                      "<rect data-role='step' data-kind='add' fill='#A6A6A6'/>"
                      "<rect data-role='step' data-kind='sub' fill='#404040'/>"
                      "<rect data-role='col-AC' fill='#404040'/><rect data-role='segment-1' fill='#A6A6A6'/>"
                      "<rect data-role='segment-2' fill='#D9D9D9'/></svg>")
        self.assertFalse([x for x in ok if x["rule"] in ("D4", "D9", "E6", "LINT") and x["status"] == "fail"])
        bad = self.dom("<svg><rect data-role='step' data-kind='total' fill='#A6A6A6'/>"
                       "<rect data-role='step' data-kind='add' fill='#8CB400'/>"
                       "<rect data-role='segment-1' fill='#404040'/></svg>")
        self.assertTrue(any(x["rule"] == "D4" for x in bad))
        self.assertTrue(any(x["rule"] == "E6" for x in bad))
        self.assertTrue(any(x["rule"] == "D9" for x in bad))

    def test_svg_measure_e6_only_for_text_fills(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("ibcs_lint_mod", LINT)
        mod = importlib.util.module_from_spec(spec)
        sys.dont_write_bytecode = True
        spec.loader.exec_module(mod)
        expr = ("VAR _Good = \"#8CB400\" VAR _Text = \"#000000\" VAR _Col = IF ( 1, _Good, _Good ) "
                "RETURN \"<svg><rect fill='\" & _Col & \"'/><text fill='\" & _Text & \"'>1</text></svg>\"")
        self.assertEqual(mod.text_fill_hexes(expr), {"#000000"})
        self.assertIn("#8CB400", mod.text_fill_hexes(expr.replace("& _Text &", "& _Col &")))

    def test_bundled_templates_pass_g1_and_optional_fields(self):
        tdir = ROOT / "plugins/ibcs-power-bi/skills/ibcs-deneb/assets/templates"
        for t in sorted(tdir.glob("*.vl.json")):
            code, f, _ = run(t, "--no-overrides")
            self.assertFalse([x for x in f if x["rule"] == "G1" and x["status"] == "fail"], t.name)



class FinalRetestRegressions(unittest.TestCase):
    """Defects left after the final Power BI retest."""

    TEMPLATES = ROOT / "plugins/ibcs-power-bi/skills/ibcs-deneb/assets/templates"
    TO_PBIR = ROOT / "plugins/ibcs-power-bi/skills/ibcs-deneb/scripts/to_pbir.py"
    SCALE_LAYOUT = ROOT / "plugins/ibcs-power-bi/skills/ibcs-power-bi/scripts/scale_layout.py"

    def field_findings(self, spec, dataset):
        sys.path.insert(0, str(LINT.parent))
        try:
            import ibcs_lint as L
        finally:
            sys.path.pop(0)
        L.FINDINGS.clear()
        L.lint_vegalite(spec, "t", dataset_fields=dataset)
        return [f for f in L.FINDINGS if f["location"].endswith(":fields")]

    def test_required_fields_only_bound_is_clean_for_every_template(self):
        for t in sorted(self.TEMPLATES.glob("*.vl.json")):
            spec = json.loads(t.read_text(encoding="utf-8"))
            u = spec["usermeta"]["ibcs"]
            self.assertTrue(set(u["requiredFields"]) <= set(u["fields"]), t.name)
            chosen = {p["value"] for p in spec["params"] if p.get("name") in ("refScenario", "minuend", "triangleScenario")
                      and p.get("value") in u["fields"]}
            bound = set(u["requiredFields"]) | chosen | set((u.get("requiredAnyOf") or [[]])[0])
            self.assertEqual(self.field_findings(spec, sorted(bound)), [], t.name)

    def test_scenario_knob_field_and_any_of_sets_are_required(self):
        spec = json.loads((self.TEMPLATES / "bar-structure-variance.vl.json").read_text(encoding="utf-8"))
        # refScenario defaults to PL: Category + AC + PY leaves the reference unbound
        self.assertTrue(any("PL" in f["evidence"] for f in self.field_findings(spec, ["Category", "AC", "PY"])))
        wf = json.loads((self.TEMPLATES / "waterfall-variance.vl.json").read_text(encoding="utf-8"))
        self.assertTrue(self.field_findings(wf, ["Category", "Value"]))
        self.assertFalse(self.field_findings(wf, ["Category", "Value", "BaseValue", "TotalValue"]))

    def test_prepended_transform_supplies_required_fields(self):
        wf = json.loads((self.TEMPLATES / "waterfall-variance.vl.json").read_text(encoding="utf-8"))
        # a fold before the template's own transforms creates Kind and Value from separate measures
        folded = dict(wf, transform=[{"fold": ["Base", "Step", "Total"], "as": ["Kind", "Value"]},
                                     {"calculate": "datum.Kind", "as": "Category"}] + wf["transform"])
        self.assertEqual(self.field_findings(folded, ["Base", "Step", "Total"]), [])
        calc = dict(wf, transform=[{"calculate": "datum.Category === 'Start' ? 'base' : 'variance'", "as": "Kind"}]
                    + wf["transform"])
        self.assertEqual(self.field_findings(calc, ["Category", "Value"]), [])
        # a field read before a transform creates it is still the dataset's: unbound Kind is reported
        late = dict(wf, transform=[{"filter": "isValid(datum['Kind'])"},
                                   {"calculate": "'variance'", "as": "Kind"}] + wf["transform"])
        self.assertTrue(any("Kind" in f["evidence"] for f in self.field_findings(late, ["Category", "Value"])))

    def test_misnamed_required_field_is_still_reported(self):
        spec = json.loads((self.TEMPLATES / "bar-structure-variance.vl.json").read_text(encoding="utf-8"))
        found = self.field_findings(spec, ["Cat", "AC"])
        self.assertTrue(found and "Category" in found[0]["evidence"])

    def test_axis_label_datum_is_not_a_field(self):
        spec = {"data": {"name": "dataset"}, "mark": "bar",
                "encoding": {"x": {"field": "Period", "type": "nominal",
                                   "axis": {"labelExpr": "datum.label + ' ' + datum.value"}}}}
        self.assertEqual(self.field_findings(spec, ["Period"]), [])
        # a real data field read inside a guide expression is still checked
        spec["encoding"]["x"]["axis"]["labelColor"] = {"expr": "datum['Unbound'] > 0 ? 'red' : 'black'"}
        self.assertTrue(any("Unbound" in f["evidence"] for f in self.field_findings(spec, ["Period"])))

    def test_prepend_transform_folds_separate_measures(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            fold = write_json(tmp / "fold.json", [{"fold": ["Base", "Step", "Total"], "as": ["__key", "__val"]},
                                                  {"calculate": "datum.__key", "as": "Category"},
                                                  {"calculate": "datum.__val", "as": "Value"}])
            ext = write_json(tmp / "ext.json", {"entities": []})
            out = tmp / "v" / "visual.json"
            p = subprocess.run([sys.executable, "-I", "-B", str(self.TO_PBIR), str(self.TEMPLATES / "waterfall-variance.vl.json"),
                                "--visual", str(out), "--new", "--field", "Base=m:M[Base]", "--field", "Step=m:M[Step]",
                                "--field", "Total=m:M[Total]", "--prepend-transform", str(fold), "--extensions", str(ext)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn("not a documented field", p.stderr)
            lit = json.loads(out.read_text(encoding="utf-8"))["visual"]["objects"]["vega"][0]["properties"]["jsonSpec"]
            spec = json.loads(lit["expr"]["Literal"]["Value"][1:-1].replace("''", "'"))
            self.assertEqual(spec["transform"][0], {"fold": ["Base", "Step", "Total"], "as": ["__key", "__val"]})
            bad = write_json(tmp / "bad.json", {"fold": ["x"]})
            p = subprocess.run([sys.executable, "-I", "-B", str(self.TO_PBIR), str(self.TEMPLATES / "waterfall-variance.vl.json"),
                                "--visual", str(tmp / "w" / "visual.json"), "--new", "--prepend-transform", str(bad),
                                "--extensions", str(ext)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)

    def test_scale_layout_caps_labels_and_adds_trend_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = write_json(Path(tmp) / "g.json", {"pxPerUnit": 10, "members": [
                {"id": "short", "template": "bar-structure-variance", "tiers": {"base": [0, 10], "variance": [-1, 1]},
                 "longestLabel": "x" * 40},
                {"id": "long", "template": "bar-structure-variance", "tiers": {"base": [0, 10], "variance": [-1, 1]},
                 "longestLabel": "x" * 80},
                {"id": "plain", "template": "line-scenarios", "tiers": {"base": [0, 20]}},
                {"id": "trend", "template": "line-scenarios", "tiers": {"base": [0, 20]},
                 "trend": {"ends": [18, 19], "excess": 3}, "params": {"trendArrow": True}},
                {"id": "off", "template": "line-scenarios", "tiers": {"base": [0, 20]},
                 "trend": {"ends": [18, 19], "excess": 3}}]})
            p = subprocess.run([sys.executable, "-I", "-B", str(self.SCALE_LAYOUT), str(g), "--json"],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            rows = {r["id"]: r for r in json.loads(p.stdout)["members"]}
            self.assertEqual(rows["short"]["containerPx"], rows["long"]["containerPx"])   # both capped at 180 + 6
            self.assertEqual(rows["trend"]["containerPx"] - rows["plain"]["containerPx"], 2 * 10 + 12 + 10 + 4)
            self.assertEqual(rows["off"]["containerPx"], rows["plain"]["containerPx"])   # trendArrow off: no envelope


if __name__ == "__main__":
    unittest.main()
