# ibcs

The core of this marketplace: skills and agents for business reports, dashboards and app pages
that follow the IBCS® Standards (v2.0, aligned with ISO 24896). `ibcs-notation` fixes what every
element looks like — scenarios (AC solid, PY light, PL outlined, FC hatched), variances coloured
by business impact, widths, titles, number formats, identical scales — and ships the design
tokens all other plugins consume. `ibcs-composition` turns a question into a page: key message,
MECE storyline, page pattern and a tool-agnostic YAML visual spec for builders. `ibcs-review`
audits screenshots, Power BI reports, Vega-Lite specs, web pages and specs with a rule-cited
checklist and a read-only linter. `ibcs-web-charts` gives the behaviour contract for chart components in web pages and apps, and
ships tested React + SVG reference components to copy and extend.

## Install

```
/plugin marketplace add SonniHS/simmelsgaard-reporting-skills
/plugin install ibcs@simmelsgaard-reporting-skills
```

## Skills and agents

- [`ibcs-notation`](skills/ibcs-notation/SKILL.md) — the notation rules, chart and table
  catalogues, glossary, and the bundled `ibcs-tokens.json` (override with your own
  `ibcs-tokens.overrides.json`); `scripts/gen_tokens.mjs` writes the effective tokens as a
  TypeScript, JSON or CSS module for web apps.
- [`ibcs-composition`](skills/ibcs-composition/SKILL.md) — objective, key message, storyline,
  page patterns, interactive behaviour, and the visual spec format.
- [`ibcs-review`](skills/ibcs-review/SKILL.md) — audit procedure, checklist (A–K) and
  `scripts/ibcs_lint.py` (PBIR folders incl. report-level measures, Power BI themes, Vega-Lite
  specs, token files).
- [`ibcs-web-charts`](skills/ibcs-web-charts/SKILL.md) — IBCS chart components for web pages, with [reference components](skills/ibcs-web-charts/assets/react-reference/README.md)
  and apps (SVG/React), driven by the same tokens.
- Agent `ibcs-visual-designer` — designs pages and writes visual specs; does not build.
- Agent `ibcs-reviewer` — read-only reviewer that returns a findings table.

## Examples

- "Design a monthly P&L variance page for the CFO: actual vs plan, month and YTD."
- "What colour should the forecast be in this column chart?" (answer: none — it is hatched)
- "Review this dashboard screenshot for IBCS problems."
- "Lint our Power BI report folder and our theme JSON."
- "Write the key message and three-line title for this net sales by country chart."

## Works with

- `ibcs-power-bi` — the `ibcs-power-bi`, `ibcs-deneb` and `ibcs-svg-dax` skills build specs in
  Power BI (theme, Deneb templates, SVG measures in tables).
- `fabric-apps` — the `ibcs-fabric-app` skill builds specs as Microsoft Fabric apps.
- `reporting-data` — the `semantic-model-ibcs` skill provides the scenarios, variances and
  polarity the visuals need.
- Upstream tools that are only described, not bundled: Microsoft Power BI, Deneb, Vega-Lite,
  React. For Microsoft Fabric use Microsoft's Fabric skills
  (`fabric-skills@fabric-collection` from https://github.com/microsoft/skills-for-fabric).

## Licence

Prose (SKILL.md, references, agents, this README) is licensed CC BY-SA 4.0; code and data
(scripts, token files) are MIT. See NOTICE, LICENSE-CC-BY-SA-4.0 and LICENSE-MIT in this
plugin. The prose is our own
condensed restatement of the IBCS Standards v2.0 by the IBCS Association (CC BY-SA 4.0), with
rule and page citations. These skills follow the IBCS® Standards; IBCS® is a registered
trademark of IBCS Institute; not affiliated with or certified by IBCS Institute.
