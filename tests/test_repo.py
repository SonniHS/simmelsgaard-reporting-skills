"""Validation for the marketplace: manifests, frontmatter, links, plugin boundaries and a leak scan.

Run from the repo root:  python3 -m unittest discover -s tests -v
Stdlib only. Optional: tests/private-denylist.txt (gitignored), one case-insensitive entry per line
(`term`, `re:<regex>` or `warn:<term>`, see load_denylist), for names that must never appear but
cannot be listed in a public file. Without it that check is
skipped; before publishing run with REQUIRE_PRIVATE_DENYLIST=1 so a missing list fails.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
DENYLIST = ROOT / "tests" / "private-denylist.txt"

SKIP_SCAN = {"LICENSE-CC-BY-SA-4.0", "LICENSE-MIT"}
LICENCE_FILES = ["NOTICE", "LICENSE-MIT", "LICENSE-CC-BY-SA-4.0"]
PRIVATE_DIRS = r"(?:vault|packages|apps|specs|erp-demo|design/tokens)/"

# Patterns that must not appear anywhere in the repo. Each is (label, regex, allowed-match predicate).
ZERO_GUID = "00000000-0000-0000-0000-000000000000"
LEAK_PATTERNS = [
    ("e-mail address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
     lambda m: m.split("@")[1].startswith("example.") or m.startswith("noreply@anthropic")),
    ("GUID", re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
     lambda m: m == ZERO_GUID),
    ("tenant-specific host", re.compile(
        r"\b[\w-]+\.(?:datawarehouse\.fabric\.microsoft\.com|database\.windows\.net|"
        r"crm\d*\.dynamics\.com|operations\.dynamics\.com|sharepoint\.com)\b", re.I),
     lambda m: False),
    ("licence line of the IBCS PDF", re.compile(r"licensed\s+for", re.I), lambda m: False),
    ("home directory path", re.compile(r"(?:/Users/|/home/|[A-Z]:\\Users\\)[\w.-]+"), lambda m: False),
    ("private repo path", re.compile(r"(?<![\w/{}<.$-])" + PRIVATE_DIRS), lambda m: False),
    # the same, after ./ ../ ~/ or a leading / (a path inside another project, such as src/apps/, stays allowed);
    # ./specs/ is the public convention for visual specs in the user's own repo
    ("private repo path", re.compile(r"(?:^|(?<=[\s(\[`'\"=:]))(?:\.\.?/|~/|/)+" + PRIVATE_DIRS),
     lambda m: m == "./specs/"),
]
# AGENTS.md (and its CLAUDE.md symlink) names these patterns in order to forbid them.
RULE_FILES = {"AGENTS.md", "CLAUDE.md"}
RULE_LABELS = {"private repo path", "licence line of the IBCS PDF"}


def repo_files():
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if path.is_file() and not rel.parts[0].startswith(".git") and ".remember" not in rel.parts \
                and "__pycache__" not in rel.parts and "node_modules" not in rel.parts and rel.name not in {DENYLIST.name, "CLAUDE.local.md"}:
            yield path


def md_files(base):
    """Markdown under base, without installed dependencies (node_modules of a reference package)."""
    return (p for p in base.rglob("*.md") if "node_modules" not in p.parts)


def text_files():
    """Every file that decodes as UTF-8 (any suffix: .html, .css, .csv, .pbir, .platform …), except the licence texts."""
    for path in repo_files():
        if path.name in SKIP_SCAN:
            continue
        try:
            path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue  # binary (images)
        yield path


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fields, key = {}, None
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fields[key] = "" if value in {">", "|", ">-", "|-"} else value
        elif key and line.startswith((" ", "\t")):  # continuation of a block scalar or folded value
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def plugin_dirs():
    return sorted(p for p in PLUGINS.iterdir() if p.is_dir())


def skills_of(plugin):
    return sorted(p.parent for p in (plugin / "skills").glob("*/SKILL.md"))


class Manifests(unittest.TestCase):
    def test_marketplace_lists_every_plugin(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        listed = {p["name"]: p["source"] for p in market["plugins"]}
        on_disk = {p.name for p in plugin_dirs()}
        self.assertEqual(set(listed), on_disk)
        for name, source in listed.items():
            self.assertEqual(source, f"./plugins/{name}")

    def test_plugin_manifest_names_match_dirs(self):
        for plugin in plugin_dirs():
            manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
            self.assertEqual(manifest["name"], plugin.name)
            self.assertTrue(manifest.get("description"))

    def test_every_plugin_ships_identical_licence_files(self):
        # An installed plugin contains only its own directory, so each carries NOTICE and both licences.
        for plugin in plugin_dirs():
            for name in LICENCE_FILES:
                copy = plugin / name
                self.assertTrue(copy.is_file(), f"{plugin.name} has no {name}")
                self.assertEqual(copy.read_bytes(), (ROOT / name).read_bytes(), f"{copy} differs from /{name}")

    def test_dependencies_are_plugins_of_this_marketplace(self):
        names = {p.name for p in plugin_dirs()}
        for plugin in plugin_dirs():
            manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
            for dep in manifest.get("dependencies", []):
                self.assertIn(dep, names - {plugin.name}, f"{plugin.name}: unknown dependency {dep}")

    def test_every_plugin_has_readme(self):
        for plugin in plugin_dirs():
            self.assertTrue((plugin / "README.md").is_file(), f"{plugin.name} has no README.md")

    @unittest.skipUnless(shutil.which("claude"), "claude CLI not installed")
    def test_claude_plugin_validate_strict(self):
        for target in [ROOT, *plugin_dirs()]:
            r = subprocess.run(["claude", "plugin", "validate", "--strict", str(target)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{target}:\n{r.stdout}{r.stderr}")


class Frontmatter(unittest.TestCase):
    def test_skills_have_name_and_description(self):
        for plugin in plugin_dirs():
            for skill in skills_of(plugin):
                fm = frontmatter(skill / "SKILL.md")
                self.assertIsNotNone(fm, f"{skill}: no frontmatter")
                self.assertEqual(fm.get("name"), skill.name, f"{skill}: name must match the directory")
                self.assertTrue(fm.get("description"), f"{skill}: empty description")

    def test_frontmatter_is_strict_yaml_safe_and_descriptions_fit(self):
        # Strict YAML loaders (claude.ai upload, other agents) reject ": " or " #" inside a plain scalar;
        # the Agent Skills spec caps description at 1024 characters.
        files = [s / "SKILL.md" for p in plugin_dirs() for s in skills_of(p)] + list(PLUGINS.glob("*/agents/*.md"))
        for f in files:
            text = f.read_text(encoding="utf-8")
            head = text[4:text.find("\n---", 4)]
            for n, line in enumerate(head.splitlines(), 2):
                m = re.match(r"^([A-Za-z_-]+):\s+(.+)$", line)
                if m and m.group(2)[0] not in "'\"|>[{":
                    self.assertNotRegex(m.group(2), r": | #", f"{f.relative_to(ROOT)}:{n}: quote it or use a block scalar")
            desc = frontmatter(f).get("description", "")
            self.assertLessEqual(len(desc), 1024, f"{f.relative_to(ROOT)}: description is {len(desc)} chars")

    def test_agents_have_name_and_description(self):
        for agent in PLUGINS.glob("*/agents/*.md"):
            fm = frontmatter(agent)
            self.assertIsNotNone(fm, f"{agent}: no frontmatter")
            self.assertEqual(fm.get("name"), agent.stem, f"{agent}: name must match the file name")
            self.assertTrue(fm.get("description"), f"{agent}: empty description")

    def test_agent_preloaded_skills_are_in_the_same_plugin(self):
        # A skill from another plugin may not be installed; name it in the agent's body instead.
        for agent in PLUGINS.glob("*/agents/*.md"):
            plugin = agent.parent.parent
            own = {s.name for s in skills_of(plugin)}
            listed = [s.strip() for s in (frontmatter(agent).get("skills") or "").split(",") if s.strip()]
            self.assertTrue(listed, f"{agent.relative_to(ROOT)}: no skills: frontmatter (preload its plugin's skills)")
            for skill in listed:
                self.assertIn(skill, own, f"{agent.relative_to(ROOT)}: skills: lists {skill}, not in {plugin.name}")


MD_LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
BARE_REF = re.compile(r"`((?:\.\./)*(?:references|scripts|assets)/[^`*<>{}\s]+)`")


class Links(unittest.TestCase):
    def test_relative_links_resolve_inside_their_plugin(self):
        problems = []
        for plugin in plugin_dirs():
            for md in md_files(plugin):
                text = md.read_text(encoding="utf-8")
                for target in MD_LINK.findall(text):
                    if re.match(r"^[a-z]+:", target):
                        continue  # absolute URL
                    resolved = (md.parent / target).resolve()
                    if not resolved.exists():
                        problems.append(f"{md.relative_to(ROOT)}: broken link {target}")
                    elif plugin.resolve() not in resolved.parents and resolved != plugin.resolve():
                        problems.append(f"{md.relative_to(ROOT)}: link leaves the plugin: {target}")
                # `references/x.md` style mentions are relative to the skill (or agent) directory
                base = next((p for p in md.parents if p.parent.name == "skills"), None)
                bases = [base] if base else skills_of(plugin)  # agents and READMEs may name any skill's files
                for target in BARE_REF.findall(text):
                    if not (md.parent / target).exists() and not any((b / target).exists() for b in bases):
                        problems.append(f"{md.relative_to(ROOT)}: missing file {target}")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_cross_plugin_skill_mentions_are_declared(self):
        owner = {s.name: p.name for p in plugin_dirs() for s in skills_of(p)}
        problems = []
        for plugin in plugin_dirs():
            readme = plugin / "README.md"
            declared = readme.read_text(encoding="utf-8") if readme.exists() else ""
            for f in md_files(plugin):
                text = f.read_text(encoding="utf-8")
                for skill, other in owner.items():
                    if other != plugin.name and re.search(rf"(?<![\w-]){re.escape(skill)}(?![\w-])", text) \
                            and f"`{other}`" not in declared:
                        problems.append(f"{f.relative_to(ROOT)} mentions {skill} (plugin {other}), "
                                        f"but {plugin.name}/README.md does not declare `{other}`")
        self.assertEqual(sorted(set(problems)), [], "\n".join(sorted(set(problems))))

    def test_bundled_token_files_are_identical(self):
        copies = sorted(PLUGINS.rglob("ibcs-tokens.json"))
        if len(copies) > 1:
            first = copies[0].read_bytes()
            for c in copies[1:]:
                self.assertEqual(c.read_bytes(), first, f"{c} differs from {copies[0]}")


def load_denylist():
    """Lines: `term` (case-insensitive substring), `re:<regex>` (case-insensitive), `warn:<term>` (reported, not failed).

    Returns a list of (kind, matcher, label); kind is "error" or "warn". Labels never echo the term itself.
    """
    if not DENYLIST.exists():
        return []
    entries = []
    for n, raw in enumerate(DENYLIST.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        kind = "error"
        if line.startswith("warn:"):
            kind, line = "warn", line[5:].strip()
        source = line[3:].strip() if line.startswith("re:") else re.escape(line)
        # str pattern for text (Unicode case folding: Æ/æ), bytes pattern for binary files such as image metadata
        rx = (re.compile(source, re.I), re.compile(source.encode("utf-8"), re.I))
        entries.append((kind, rx, f"{DENYLIST.name} line {n}"))
    return entries


class LeakScan(unittest.TestCase):
    def test_no_private_data(self):
        hits = []
        for path in text_files():
            rel = path.relative_to(ROOT)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                for label, rx, allowed in LEAK_PATTERNS:
                    if label in RULE_LABELS and str(rel) in RULE_FILES:
                        continue
                    for m in rx.finditer(line):
                        if not allowed(m.group(0)):
                            hits.append(f"{rel}:{n}: {label}: {m.group(0)}")
        self.assertEqual(hits, [], "\n".join(hits))

    def test_no_denylisted_terms(self):
        """Private names, in any file (bytes, so image metadata counts too) and in paths.

        Without the local list this test is skipped, not passed; set REQUIRE_PRIVATE_DENYLIST=1 for the
        pre-publish run so a missing or empty list fails instead.
        """
        deny = load_denylist()
        if not deny:
            if os.environ.get("REQUIRE_PRIVATE_DENYLIST") == "1":
                self.fail(f"{DENYLIST.relative_to(ROOT)} is missing or empty but REQUIRE_PRIVATE_DENYLIST=1")
            self.skipTest(f"{DENYLIST.relative_to(ROOT)} not present: private-name scan NOT run")
        hits, warnings = [], []
        for path in repo_files():
            rel = path.relative_to(ROOT)
            if path.name in SKIP_SCAN:
                continue
            data = path.read_bytes()
            try:
                data = data.decode("utf-8")
            except UnicodeDecodeError:
                pass
            for kind, (rx_text, rx_bytes), label in deny:
                rx = rx_text if isinstance(data, str) else rx_bytes
                found = [f"{rel}: matches {label}"] if rx.search(data) else []
                if rx_text.search(str(rel)):
                    found.append(f"{rel}: path matches {label}")
                (hits if kind == "error" else warnings).extend(found)
        for w in sorted(set(warnings)):
            print(f"\nWARNING (review by hand): {w}", file=sys.stderr)
        self.assertEqual(sorted(set(hits)), [], "\n".join(sorted(set(hits))))

    def test_no_binary_ibcs_material(self):
        for path in repo_files():
            self.assertNotEqual(path.suffix.lower(), ".pdf", f"{path}: PDFs are not shipped")


class SkillDocs(unittest.TestCase):
    def test_rayfin_up_commands_name_the_item(self):
        """A pasted `rayfin up` without --item-name deploys under the project id to a recorded target."""
        bad = []
        for path in md_files(PLUGINS):
            for block in re.findall(r"```[a-z]*\n(.*?)```", path.read_text(encoding="utf-8"), re.S):
                for line in re.sub(r"\\\n\s*", " ", block).splitlines():   # join \ continuations
                    if "rayfin up" in line and "--item-name" not in line:
                        bad.append(f"{path.relative_to(ROOT)}: {line.strip()}")
        self.assertEqual(bad, [])


PBI_SKILLS = PLUGINS / "ibcs-power-bi" / "skills"


def run_script(*args, cwd=None):
    return subprocess.run([sys.executable, "-I", "-B", *map(str, args)], capture_output=True, text=True, cwd=cwd)


class PowerBiScripts(unittest.TestCase):
    """Generators keep Deneb visuals and report measures loadable in the Power BI service."""

    def test_deneb_templates_filter_the_blank_category_first(self):
        for path in sorted((PBI_SKILLS / "ibcs-deneb/assets/templates").glob("*.vl.json")):
            spec = json.loads(path.read_text(encoding="utf-8"))
            first = (spec.get("transform") or [{}])[0]
            self.assertIn("isValid(datum[", str(first.get("filter", "")), f"{path.name}: first transform")

    def test_report_measures_check_and_fix(self):
        script = PBI_SKILLS / "ibcs-power-bi/scripts/report_measures.py"
        with tempfile.TemporaryDirectory() as tmp:
            rep = Path(tmp) / "Sample.Report"
            shutil.copytree(ROOT / "tests/fixtures/ibcs_lint/pbir-bindings/Sample.Report", rep)
            before = run_script(script, rep, "--check")
            self.assertEqual(before.returncode, 1, before.stdout + before.stderr)
            self.assertIn("extension", before.stdout + before.stderr)
            self.assertIn("active", before.stdout + before.stderr)
            fixed = run_script(script, rep, "--fix")
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            self.assertEqual(run_script(script, rep, "--check").returncode, 0)

    def test_report_measures_model_path_resolved_or_rejected(self):
        script = PBI_SKILLS / "ibcs-power-bi/scripts/report_measures.py"
        with tempfile.TemporaryDirectory() as tmp:
            rep = Path(tmp) / "Sample.Report"
            shutil.copytree(ROOT / "tests/fixtures/ibcs_lint/pbir-bindings/Sample.Report", rep)
            model = Path(tmp) / "Sample.SemanticModel"
            (model / "definition" / "tables").mkdir(parents=True)
            # a folder without TMDL tables is an error, never a silent "ok" without model references
            empty = run_script(script, rep, "--check", "--model", model)
            self.assertEqual(empty.returncode, 2, empty.stdout + empty.stderr)
            self.assertIn("no TMDL tables", empty.stderr)
            (model / "definition" / "tables" / "Sales.tmdl").write_text(
                "table Sales\n\tmeasure Revenue = SUM ( Sales[Amount] )\n", encoding="utf-8")
            for arg in (model, model / "definition", model / "definition" / "tables"):
                res = run_script(script, rep, "--check", "--model", arg)
                self.assertNotIn("no TMDL tables", res.stderr, arg)
                self.assertIn(res.returncode, (0, 1), res.stdout + res.stderr)

    def test_to_pbir_marks_report_measures_as_extension(self):
        script = PBI_SKILLS / "ibcs-deneb/scripts/to_pbir.py"
        template = PBI_SKILLS / "ibcs-deneb/assets/templates/column-two-tier-variance.vl.json"
        with tempfile.TemporaryDirectory() as tmp:
            rep = Path(tmp) / "Sample.Report"
            shutil.copytree(ROOT / "tests/fixtures/ibcs_lint/pbir-bindings/Sample.Report", rep)
            vis = rep / "definition/pages/p1/visuals/newCols/visual.json"
            r = run_script(script, template, "--visual", vis, "--new", "--field", "Period=col:Date[Month]",
                           "--field", "AC=m:_Measures[Sales Period]", "--field", "PY=m:_Measures[Sales]")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            refs = {}
            def walk(node):
                if isinstance(node, dict):
                    m = node.get("Measure")
                    if isinstance(m, dict):
                        refs[m.get("Property")] = (m.get("Expression") or {}).get("SourceRef", {}).get("Schema")
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(json.loads(vis.read_text(encoding="utf-8")))
            self.assertEqual(refs.get("Sales Period"), "extension")   # a report measure
            self.assertIsNone(refs.get("Sales"))                       # a model measure


if __name__ == "__main__":
    unittest.main()
