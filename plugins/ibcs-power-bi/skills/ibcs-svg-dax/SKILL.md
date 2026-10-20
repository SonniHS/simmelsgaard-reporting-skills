---
name: ibcs-svg-dax
description: >
  Provides IBCS® chart components as SVG-in-DAX measures for Power BI tables and matrices; use it
  when someone needs IBCS variance bars or pins inside a Power BI matrix, table, button slicer or
  card, or asks how to draw IBCS notation with SVG measures. Components: variance bars on a shared
  scale with the reference-scenario axis, relative-variance pins with N/A, KPI cards (spec type
  kpi-cards), AC bars with an outlined BU bar and a PY triangle, budget progress bars (BAC,
  budget to date, AC to date), scenario triangles, indexed
  sparklines and scenario header markers, with colours from the IBCS design tokens, scaled and
  locale-safe numbers, and a preview harness (executeQueries plus headless Chrome). Early stage:
  skeleton measures, no finished library.
---

# IBCS SVG-in-DAX measures

Status (as of 2026-10): **no finished measure library.** This skill fixes the scope and the rules
and gives seven skeleton measures ([references/svg-skeletons.md](references/svg-skeletons.md)):
the KPI card, the AC/BU/PY bar, the absolute variance bar and the budget progress bar are
render-checked with sample values
(their pattern ran against a live model in an end-to-end test); the pin and the column skeletons
are untested. None was opened in Power BI Desktop by this plugin. Preview every measure with real
values before use (preview harness below).

The notation rules are those of the `ibcs-notation` skill (plugin `ibcs`); where a component
belongs in a chart rather than a table, use [ibcs-deneb](../ibcs-deneb/SKILL.md); routing per
visual is in [ibcs-power-bi](../ibcs-power-bi/SKILL.md).

## Use today

1. **PowerofBI.IBCS** (community DAX library, published in the [daxlib.org](https://daxlib.org/)
   registry, source at [github.com/avatorl/dax-udf-svg-ibcs](https://github.com/avatorl/dax-udf-svg-ibcs);
   check its licence before use; version 0.x as of 2026-10; pin the version, 0.x releases change
   signatures): bar, variance, pin, column,
   waterfall and small-multiple SVG functions for matrix, table, button slicer and new card.
   Before relying on it, check that its colours match your tokens and that its Δ% divides by the
   **signed** reference with N/A.
2. The skeletons in [references/svg-skeletons.md](references/svg-skeletons.md).
3. Mechanics (data category Image URL, `grid.imageHeight` / `imageWidth`, report-extension
   measures, SVG review): Microsoft's Power BI SVG-visuals agent skill where installed.

## How SVG-in-DAX works

A measure returns `data:image/svg+xml;utf8,<svg …>…</svg>`, has **data category Image URL**, and
is shown in a table or matrix (`grid.imageHeight` / `imageWidth`; the generated IBCS theme sets
the image height to one row), a button slicer, the new card or an image visual. Each cell is its
own SVG document, so `<defs>` ids such as `url(#h)` never clash between cells.

## Scope

| Measure family | IBCS rule |
|---|---|
| Absolute variance bar, shared scale across rows (and with the AC bar column) | UN 4.1 same scale; geometry by sign, colour by polarity (good / bad / neutral); axis in the reference notation (PY solid light, PL two thin lines); FC hatched |
| Relative variance pin | (AC − REF) / REF with the signed reference; N/A when REF ≤ 0 or blank; head in the minuend's notation (squares are the illustrated design) |
| AC bar with PL/PY triangle or overlapped reference bar; AC in front of an outlined BU bar with a PY triangle (third scenario) | EX 1.1 cards 23, 24 |
| KPI card (`kpi-cards`, B-T-KPI): label, unit, AC, then Δ% and Δ per comparison | a transposed variance table; impact colour by polarity, a Δ that rounds to 0 unsigned and uncoloured |
| Budget progress bar: BAC outlined, AC to date solid inside, budget-to-date tick, "AC (share of BAC)" | share N/A when BAC ≤ 0 or blank; the AC − budget-to-date variance is a skeleton-1 column on the same scale |
| Waterfall bar per report line | cards 28, 29 in a matrix |
| Indexed sparkline on a shared scale | CO 4.4: omit sparklines that are not scaled properly |
| Scenario header marker (thick light / thick dark / double / hatched rule) | EX 1.2 column headers |
| Key message with impact-coloured numbers (skeleton 7): bold sentence, variance numbers in the text impact colours, ≤ 2 lines | UN 2.1, SA 4.3; a text box cannot colour a value by its sign |
| Structure block, one SVG row per category with all tiers (skeleton 8): AC/BU/PY bars, Δ bar on the same px per unit, Δ% pin, highlight ellipse, plus a header row with tier names and the integrated legend | UN 4.1 same scale across the page; one GEOM so the tiers line up; EX 1.1 cards 24, 26 |

## Preview harness

Evaluate the measure against the model as a query-scoped `DEFINE MEASURE` (the model stays
unchanged) with the REST API *Datasets – Execute Queries*, save the JSON response, then
`python3 -I "${CLAUDE_SKILL_DIR}/scripts/svg_preview.py" result.json --out ./svg-preview --png`
draws every SVG cell inline in an HTML page and screenshots it with headless Chrome. It also
accepts a JSON list of SVG strings (sample values). Steps and the query body:
[references/svg-skeletons.md](references/svg-skeletons.md#preview-harness).

## Rules

- **Colours and geometry from the tokens.** Generate a block of DAX user-defined functions
  (`Svg.*`; UDFs are GA as of 2026-10, compatibility level ≥ 1702) or plain measures from the
  token file with a script, the way `build_pbi_theme.py` generates the theme. Never maintain a
  second palette by hand.
- **Scaled numbers.** Divide every printed value by the display unit (thousands, millions) and
  round to the fixed decimals of its scale group; never print raw values. A Δ that rounds to 0 at
  that precision shows unsigned in the default text colour. Variance numbers may be tinted only
  with `color.variance.goodText` / `badText` / `neutralText` (≥ 4.5:1), otherwise black.
- **Clamped sizes.** Pin stem 2–4 px, pin head 6–10 px, triangle 6–12 px (tokens
  `geometry.pin.stemPx`, `geometry.pin.headPx`, `geometry.triangleSizePx`).
- **Blank guards.** No mark without both operands; BLANK instead of an empty SVG where nothing is
  drawn; N/A only when AC exists and the reference is ≤ 0 or blank.
- **Locale-safe numbers.** Wrap every computed coordinate in `FORMAT ( x, "0.0", "en-US" )` or a
  `Svg.Num` UDF: culture-dependent conversion (e.g. a decimal-comma locale) breaks the SVG.
  Format labels with the token separators (`SUBSTITUTE` for the thousands separator), and the
  locale you configure in the tokens.
- **Shared scale** via `ALLSELECTED ( <row column> )` = one **px per unit**, not one max. When two
  SVG columns share a scale (AC bar and ΔPY bar), compute the px per unit once (from the column
  with the largest range and its width) and give each column its own width = its own range ×
  px per unit + label room; a narrow ΔPY column with the AC max would waste its width. When the
  SVG column belongs to a page scale group with Deneb charts, pass the group's px per unit (one
  measure, the value given to the templates' `pxPerUnit`) instead of a shared max. Keep it in a
  short `-- GEOM` block at the top of the measure (px per unit, widths, label room) so every
  skeleton derives its lengths the same way.
- **Sortable:** a `<desc>` sort key at the start of the SVG keeps the column sortable.
- **Subtotal rows:** guard with `ISINSCOPE` / `HASONEVALUE`.
- Hex colours with `#`, single-quoted attributes, no scripts.
- **Performance:** each SVG measure is evaluated per cell. Reuse model measures, avoid nested
  `ALLSELECTED` iterations per row, keep strings short (CONCATENATEX over 100+ points gets
  heavy), and check timings in Performance Analyzer.

## TODO

- [ ] Token → DAX generator emitting a UDF TMDL file.
- [ ] Measures for the scope table, tested in Desktop with a decimal-comma culture and en-US.
- [x] Preview harness (`scripts/svg_preview.py`, executeQueries + headless Chrome).
- [ ] Pin and column skeletons render-checked; pin-structure (card 26) skeleton.
- [ ] Compare PowerofBI.IBCS output with the tokens and the signed-reference rule; document deltas.
