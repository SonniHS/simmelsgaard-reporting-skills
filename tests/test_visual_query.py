"""visual_query.py filters and to_pbir.py filter names (no network: only the generated query is checked)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DENEB = ROOT / "plugins/ibcs-power-bi/skills/ibcs-deneb"
VQ = DENEB / "scripts/visual_query.py"
TO_PBIR = DENEB / "scripts/to_pbir.py"


class VisualQueryFilters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = Path(self.tmp.name)
        (t / "ext.json").write_text(json.dumps({"entities": []}), encoding="utf-8")
        self.ext = t / "ext.json"
        self.visual = t / "v" / "visual.json"
        p = subprocess.run([sys.executable, "-I", "-B", str(TO_PBIR), str(DENEB / "assets/templates/waterfall-variance.vl.json"),
                            "--visual", str(self.visual), "--new", "--name", "wfMonth",
                            "--field", "Category=col:Date[Month]", "--field", "Value=m:M[Delta]",
                            "--filter", "col:Date[Year]=2026", "--extensions", str(self.ext)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def query(self, *filters):
        args = [a for f in filters for a in ("--filter", f)]
        p = subprocess.run([sys.executable, "-I", "-B", str(VQ), str(self.visual), "--extensions", str(self.ext), *args],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_simple_filters_become_treatas(self):
        q = self.query("'Customer'[Customer Name] = \"Name A\"", "'Date'[Year] = 2026",
                       "Product[Group] IN {\"A\", \"B\"}")
        self.assertIn("TREATAS ( { \"Name A\" }, 'Customer'[Customer Name] )", q)
        self.assertIn("TREATAS ( { 2026 }, 'Date'[Year] )", q)
        self.assertIn("TREATAS ( { \"A\", \"B\" }, Product[Group] )", q)
        self.assertNotIn("'Customer'[Customer Name] = ", q)

    def test_filter_tables_pass_through(self):
        f = "FILTER ( ALL ( 'Date'[Month] ), 'Date'[Month] <= \"2026-06\" )"
        self.assertIn(f, self.query(f))

    def test_to_pbir_filter_name_is_unique_per_visual(self):
        vis = json.loads(self.visual.read_text(encoding="utf-8"))
        self.assertEqual([f["name"] for f in vis["filterConfig"]["filters"]], ["wfMonth_filter1"])


if __name__ == "__main__":
    unittest.main()
