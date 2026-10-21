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
        self.assertEqual(params["pinPxPerUnit"], 1)          # one % scale: 1 px per percentage point
        self.assertEqual(params["pinClip"], 1)               # outliers clip at ±100 %
        self.assertIs(params["markLastClosed"], True)        # band behind the last closed month
        self.assertNotIn("legendSide", params)               # one legend placement: at the end
        self.assertNotIn("legendSide", TEMPLATE.read_text())
        pins = json.loads((TEMPLATE.parent / "pin-relative-variance.vl.json").read_text())
        self.assertEqual({p["name"]: p.get("value") for p in pins["params"]}["clipPct"], 1)
