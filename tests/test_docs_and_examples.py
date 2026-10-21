"""Top-level docs and the Sample Sales example: links resolve, generated files are current, the
sample spec passes the linter, and the TMDL keeps the shape the getting-started guide relies on.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import csv
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "examples/sample-sales"
MODEL = SAMPLE / "SampleSales.SemanticModel/definition"
LINT = ROOT / "plugins/ibcs/skills/ibcs-review/scripts/ibcs_lint.py"
MD_LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")

try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


def run(*args):
    return subprocess.run([sys.executable, "-I", "-B", *map(str, args)], capture_output=True, text=True)


class DocsLinks(unittest.TestCase):
    def test_relative_links_resolve(self):
        files = [*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md"), *SAMPLE.rglob("*.md")]
        broken = []
        for md in files:
            for target in MD_LINK.findall(md.read_text(encoding="utf-8")):
                if not re.match(r"^[a-z]+:", target) and not (md.parent / target).exists():
                    broken.append(f"{md.relative_to(ROOT)}: {target}")
        self.assertEqual(broken, [])


class SampleSales(unittest.TestCase):
    def test_generated_files_are_current(self):
        r = run(SAMPLE / "scripts/generate_sample.py", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_sample_spec_passes_the_linter(self):
        r = run(LINT, "spec", SAMPLE / "specs" / "key-figures.visual-spec.yaml")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_tmdl_uses_tabs_and_declares_every_table(self):
        model = (MODEL / "model.tmdl").read_text(encoding="utf-8")
        for f in [*MODEL.glob("*.tmdl"), *(MODEL / "tables").glob("*.tmdl")]:
            text = f.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?m)^ +\S", f"{f.name}: indent with tabs")
            m = re.search(r"(?m)^table (.+)$", text)
            if m:
                self.assertIn(f"ref table {m.group(1)}", model, f"{f.name} missing in model.tmdl")

    def test_py_is_derived_never_stored(self):
        types = {row["ScenarioType"] for row in csv.DictReader((SAMPLE / "csv/Scenario.csv").open(encoding="utf-8"))}
        self.assertEqual(types, {"AC", "BU", "FC"})

    def test_expected_results_match_the_readme_check(self):
        rows = {(r["View"], r["Measure"], r["Scenario"]): r["Value"]
                for r in csv.DictReader((SAMPLE / "expected_results.csv").open(encoding="utf-8")) if not r["Member"]}
        readme = (SAMPLE / "README.md").read_text(encoding="utf-8").replace(" ", "").replace(" ", "")
        for scen in ("AC", "PY", "BU"):
            value = rows[("YTD", "Revenue", scen)]
            self.assertIn(f"{scen}{value}", readme, f"README check value for {scen}")


if __name__ == "__main__":
    unittest.main()
