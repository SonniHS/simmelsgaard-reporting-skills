# ibcs-power-bi

Build Power BI reports that follow the IBCS® Standards. The plugin decides, per chart or table,
the cheapest route that reaches the IBCS notation — a native visual with exact `visual.json`
properties, a Deneb (Vega-Lite) template, an SVG-in-DAX measure, or a certified visual — and ships
the pieces: a report theme generated from the IBCS design tokens, seven token-driven Deneb
templates with previews (two-tier variance columns, pins, structure bars with triangles,
calculation and variance waterfalls, small multiples, scenario lines), scripts to sync your
organisation's token overrides and inject templates into PBIR, a scaffold for a live-connected
PBIP report, report-level measure rules for shared models that must not change, SVG measure
skeletons (KPI cards, bars with triangles, variance bars) with a preview harness, page layout
rules and a build checklist. Status as of 2026-10: rendered and checked outside Power BI and used
in an end-to-end test in the Power BI service; not yet verified in Power BI Desktop.

## Install

```
/plugin marketplace add SonniHS/simmelsgaard-reporting-skills
/plugin install ibcs-power-bi@simmelsgaard-reporting-skills
```

This also installs the `ibcs` plugin, a declared dependency (its notation, composition and review
skills). `reporting-data` is optional; install it for the semantic-model skills.

Scripts need Python 3 (stdlib only); preview rendering needs Node.js and, for PNGs, Chrome.

## Skills and agents

- `ibcs-power-bi` (skill) — theme, `new_pbip.py` scaffold, `scale_layout.py` (visual sizes of a scale group at one px per unit), `report_measures.py` (report-level measures the service can load: `"Schema": "extension"` bindings, `references`, no `hidden` / stray `active`), routing per IBCS chart/table type, `visual.json` recipes (slicer, text box, `tableEx` and interactions verified in the service), report measures, page layout, dynamic texts, slicer defaults, interactions, spec → PBIR procedure, checking the published page, checklist.
- `ibcs-deneb` (skill) — IBCS Deneb templates (px-per-unit scale groups, unit divisor, third-scenario triangles, Total-column knobs), token sync (`--tokens` / `--overrides` / `--out`), preview renderer (sample data, or a report's Deneb visual with live query rows), `to_pbir.py` (fields incl. report-level measures, knobs, sort, filter, title).
- `ibcs-svg-dax` (skill) — rules and skeletons for KPI cards, AC/BU/PY bars, variance bars, pins and columns as SVG measures, plus `svg_preview.py` (executeQueries result → HTML/PNG).
- `powerbi-report-builder` (agent) — builds or updates a PBIR report from an IBCS visual spec and reports routes, deviations and missing measures.

## Examples

- "Can Power BI draw an IBCS column chart with hatched forecast months natively? If not, what should I use?"
- "Generate the IBCS Power BI theme with our overrides file and add it to this PBIP report."
- "Put the two-tier AC/FC vs PL variance chart on the Sales page, bound to Measures[AC], [FC], [PL] and Date[Month Short]."
- "Add ΔPY bars and ΔPY% pins as SVG measures to this product matrix, same scale on every row."
- "Build the Overview page from `./specs/sales/overview.visual-spec.yaml` and list every compromise as a footnote."

## Works with

- `ibcs` — the `ibcs-notation` skill defines the notation and the token format (overrides),
  `ibcs-composition` the page layout and the visual-spec format, `ibcs-review` / `ibcs-reviewer`
  the review of the finished page.
- `reporting-data` — the `semantic-model-ibcs` skill for scenario measures, variance calculation
  groups and polarity in the model.
- `fabric-apps` — the `fabric-org-apps` skill for distributing reports as org apps (audiences,
  dev/test/prod).
- Upstream tools: Microsoft's Power BI agent skills (PBIR/PBIP file format, theme JSON, Deneb and
  SVG visuals) for file mechanics; [Deneb](https://deneb.guide/) (custom visual); the community
  PowerofBI.IBCS DAX library ([daxlib.org](https://daxlib.org/) registry, source at
  [github.com/avatorl/dax-udf-svg-ibcs](https://github.com/avatorl/dax-udf-svg-ibcs); check its
  licence before use).

## Licence

Prose (SKILL.md, references, README) is shared under CC BY-SA 4.0; code and data (scripts,
templates, token files, sample data, generated theme) under the MIT License. See NOTICE, LICENSE-CC-BY-SA-4.0 and LICENSE-MIT in this
plugin.

Follows the IBCS® Standards; IBCS® is a registered trademark of IBCS Institute. Not affiliated
with or certified by IBCS Institute.
