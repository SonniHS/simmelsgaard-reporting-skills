---
name: ibcs-review
description: >
  Audits a business report, dashboard page, Power BI report (PBIR folder, visual.json, theme
  JSON), web/React page, Vega-Lite or Deneb spec, screenshot, PDF page or visual spec against the
  IBCS® Standards (ISO 24896 notation) and for composition quality, whenever the user asks to
  review, check, audit, critique, QA or "IBCS-check" a report, chart, dashboard, theme or spec,
  asks "is this IBCS compliant" or "what's wrong with this chart", or before shipping / merging
  any reporting page — even if IBCS is not named. Returns a findings table with rule ID, severity,
  location, evidence and fix. Works with the ibcs-notation skill (rules, design tokens) and
  ibcs-composition (message, structure, density). Read-only: it reports, it never edits the
  artefact.
---

# IBCS review — audit procedure

A review is useful only if every finding is **verifiable** (rule ID + evidence + location) and
**actionable** (a concrete fix), and if the reviewer is honest about what could not be checked.
Work read-only: never edit the artefact under review; the findings table is the deliverable.

Rules come from the IBCS Standards v2.0 (2026); this skill is our own restatement under CC BY-SA
4.0 (see the repository NOTICE). It follows the IBCS® Standards; a passing review is not an IBCS
certification. Checklist IDs (A–G notation, H/J/K composition) are defined in
[references/checklist.md](references/checklist.md). For the rules themselves load
[ibcs-notation](../ibcs-notation/SKILL.md) (and [ibcs-composition](../ibcs-composition/SKILL.md)
for message/structure/density).

## 1. Procedure

1. **Scope.** Identify the artefact type(s), the pages in scope, and the context: medium
   (dashboard, written, slides), page kind (message vs analysis), the organisation's notation
   manual or token overrides (the project's `ibcs-tokens.overrides.json`, if any) — documented
   deviations are not findings. If a visual spec exists for the page (`*.visual-spec.yaml`,
   wherever the project keeps them), also check the build against it.
2. **Automatic pass (if machine-readable).** Run the read-only linter:

   ```sh
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/ibcs_lint.py" <path> --format md \
       [--tokens ibcs-tokens.json] [--overrides ibcs-tokens.overrides.json] [--layout layout.json]
   #   <path> = PBIR folder (*.Report: report measures in reportExtensions.json, bindings to
   #              them, table image columns, embedded Deneb specs, scale groups of the Deneb
   #              templates, slicer headers / titles that would be cut, the page shell canvas)
   #   --layout = `scale_layout.py --json` output of a scale group (ibcs-power-bi, members with
   #              "visual"): each Deneb visual must have that size and px per unit (repeatable)
   #            | theme .json | Vega-Lite .json | tokens .json
   #            | visual spec .yaml/.json (target `spec`: visual-spec-format §10, rule IDs V1..V17)
   #            | rendered page .html/.svg (target `dom`: marks with data-role, see below)
   #   tokens default to the bundled ${CLAUDE_SKILL_DIR}/../ibcs-notation/assets/ibcs-tokens.json;
   #   overrides default to ibcs-tokens.overrides.json in the current directory or a parent
   #   exit 1 = at least one failed must-rule; 'check' rows need your confirmation
   ```

   For a web or Fabric app page, save a snapshot of the rendered page (in the browser console:
   `copy(document.documentElement.outerHTML)`, or the chart's `<svg>` from a test render) and lint
   it with the `dom` target: it reads `data-role` / `data-impact` on the marks and checks scenario
   fills (AC solid, PY light, PL/BU outlined, FC hatched), impact colours by `data-impact`,
   variance numbers in the contrast-safe text colours, and rotated labels. Marks without
   `data-role` are invisible to it — a page with none gets a single `LINT` row.

   Known limits (check by hand): Deneb field names are resolved for the whole spec, not per view
   or layer, and a field read once behind `isValid(…) ?` counts as optional everywhere; prose keys
   (`description`, `usermeta`, `notes`) are never read as fields. The `dom` target resolves
   `var(--x)` to the token but not fallbacks containing parentheses, nor `currentColor`. A
   small-multiples `panel` without its own `data` only gets the axis rule (V4).

   Treat its output as leads: confirm or dismiss each `check` row with evidence, and never
   report a lint row you did not look at.
3. **Manual pass.** Inspect each page/visual per artefact type (§2) and walk the checklist (§3).
   Record N/A explicitly for elements that do not occur.
4. **Compose findings** (§4), most severe first, grouped by page. Merge duplicates (one finding
   per root cause, listing all locations).
5. **Verdict and limits.** Page fails if any **M** item fails. State what you could not verify
   (e.g. "bar width ratio estimated from screenshot", "polarity not visible without the model").

## 2. How to inspect each artefact type

Details, file paths and grep patterns: [references/artefact-inspection.md](references/artefact-inspection.md).

| Artefact | How | Strong for | Weak for |
|---|---|---|---|
| **Screenshot / PDF page** | `Read` the image (PDF: `pages`); zoom mentally per visual; estimate ratios from pixel extents | layout, titles, labels, colours, scenario fills, highlights, clutter | exact widths, scales across visuals (estimate px per unit from labelled values), polarity |
| **PBIR folder** | linter, then `Read` `definition/pages/*/page.json`, `visuals/*/visual.json`, theme under `StaticResources/RegisteredResources/` | visual types, axis/legend/gridline settings, field roles, container chrome, fixed colours, titles | rendered result, dynamic text, conditional-format measures (open the DAX in the model) |
| **Theme JSON** | linter + read `dataColors`, `good/bad/neutral`, `textClasses`, `visualStyles` | palette, fonts, defaults | per-visual overrides |
| **Vega-Lite / Deneb spec** | linter + read marks, encodings, scales, config | zero baseline, log, label angle, legends, palettes, band padding (width ratio), shared scales (`resolve`) | data-driven colour logic correctness (trace the `condition`) |
| **Web / React page** | `Grep` for chart libs and props (patterns in reference), read the page/layout components and token usage; run the app only if the user asks | hard-coded colours, legends, gridlines, animation, domains, header/footer layout component | rendering — ask for a screenshot if the verdict depends on it |
| **Visual spec (YAML)** | read against the [visual spec format](../ibcs-composition/references/visual-spec-format.md) §10 | message, titles, scale groups, chart choice, data shape | rendering (not built yet) |

When an item is not decidable from the artefact, mark it `unverified` rather than guessing.

## 3. Checklist and severity

Severity: **M** = must (ISO 24896 requirement or IBCS "shall/must"), **S** = should (IBCS
recommendation; acceptable if the notation manual defines an equally consistent alternative),
**I** = info (improvement, heuristic). Status: `fail`, `check` (needs human confirmation),
`pass`, `n/a`, `unverified`.

Top must-items (full list with how-to-detect per artefact in
[references/checklist.md](references/checklist.md)):

| ID | Must | Rule |
|---|---|---|
| A5 | colour only with analytical meaning; no per-category palettes | SI 2.2 |
| A14 | ≤ 3 digits in charts, ≤ 4 in tables (scaled k/m/b) | SI 5.2 |
| B3–B5 | one number format; one negative style; "+" on all variances and nothing else | UN 1.2 |
| C2–C7 | title present (position: consistent, top-left recommended = S); three lines (who + all filters / **measure** + unit / period + scenarios), descriptive only | UN 2.2 |
| C12 | labels horizontal | UN 2.3 |
| D1–D3 | 2/3 width absolute, 1/3 relative; thick vs thin lines | UN 3.1 |
| D4–D8 | AC solid dark, PY solid light (comparisons only), PL/BU outlined, FC hatched; no scenario by hue | UN 3.2 |
| D11, D13 | time horizontal (tables: columns), structure vertical (charts) | UN 3.3, UN 3.4 |
| E5, E6, E8, E9, E11, E12, E14 | absolute variance bars same width + scale as base; three impact colours by polarity (geometry by sign); minuend in fill, subtrahend on axis; pp for % variances; relative variances as pins with signed reference; N/A | UN 4.1 |
| F6, F7 | scale bands where same-unit scales differ; outliers beyond the scale only for irrelevant relative values, clearly marked (headless pin + triangle recommended, S) | UN 5.2, UN 5.3 |
| G1, G4–G8 | zero baseline; no clipped bars; area not diameter; no 3-D; choropleth only for densities; identical scale per unit | CH 1–4 |
| H1, H3, H6 | message page has a complete-sentence key message at a fixed position; sources + timestamp on dashboards/written pages | SA 3, SA 4.4 |

**Allowed exceptions — never report these as failures** (IBCS permits them):
totals distinguished by bold or light-gray fills on rows/columns (pp. 121, 125, 128); missing separate CVD/B&W report variants (organisational policy); 2-D/3-D components as a creative solution for orders-of-magnitude comparisons (CH 2.2); gridlines where they help
(small multiples, dense charts, scatter/bubble — SI 3.1, p. 19); different scales in extreme cases
**with** scaling markers (CH 4.1, p. 72); external legends next to symbols in two-value-axis
charts (UN 2.3); stacked-bar legends above the top **or** below the bottom bar (pp. 36, 108);
structure columns and cross tables in **tables** (pp. 119, 133); log axes that are clearly
indicated, justified (growth across orders of magnitude) and aimed at a familiar audience
(CH 1.2, p. 69); square pin heads and top-left titles are illustrated defaults — consistency is
the rule; any deviation documented in the organisation's notation manual / token overrides.

**A14 against a spec's explicit decimals (ours).** When the page's visual spec sets `display`
(prefix, decimals) for a measure and the build follows it, the spec wins: values with more than 3
digits in a chart are not a build failure. Report A14 as `check` with the spec's setting as
evidence, record it as a deviation (and ask the designer to add it to the spec's `deviations` if it
is not there), and suggest a larger scaling prefix only as an improvement.

## 4. Output format

Always use this structure:

```markdown
# IBCS review — <artefact name>, <page(s)>
Scope: <files/pages>; medium <…>; page kind <message|analysis>; overrides <yes/no>.
Verdict: **FAIL** (n must-failures) | **PASS with warnings** | **PASS**

## Findings
| # | Sev | Status | Rule | IBCS | Location | Evidence | Fix |
|---|---|---|---|---|---|---|---|
| 1 | M | fail | E6 | UN 4.1 | p. "Costs" / visual "ΔPY by cost centre" | cost increases drawn green (#8CB400) | colour by polarity −1: increase → bad (red); keep bars pointing up |

## Not verified
- <item> — <why> — <what would settle it>

## Passed / N/A (short)
A1–A4 pass · D7 n/a (no forecast) · …
```

Rules for findings: `Location` precise enough to find it (page, visual name/id, file path +
JSON path or line, screenshot region). `Evidence` is an observation, not a judgement (a value,
a setting, a quote, a measured ratio). `Fix` names the target state and, where known, the token
or setting (`geometry.barWidthRatio.absolute`, `valueAxis.start = 0`). Group repeated issues into
one row with all locations. Keep composition findings (H/J/K) after notation findings of equal
severity. Do not pad: a short table of real findings beats a long one of guesses.

## 5. Reviewing against a visual spec

If the page was built from a spec, add a section **Spec conformance**: every visual present with
the specified type/card, scenarios, variances, sort, scale group membership (same px per unit),
title lines, message and highlights, interactions (filters in title line 1, message re-scoping).
Deviations from the spec are findings even when IBCS-compliant (rule ID `SPEC`).

## References in this skill

- [references/checklist.md](references/checklist.md) — full checklist: A–G notation items with
  severity and detection hints per artefact, plus H (SAY), J (STRUCTURE), K (CONDENSE) composition
  items.
- [references/artefact-inspection.md](references/artefact-inspection.md) — PBIR layout and JSON
  paths, theme keys, Vega-Lite paths, web/React grep patterns, screenshot heuristics.
- `${CLAUDE_SKILL_DIR}/scripts/ibcs_lint.py` — read-only linter (PBIR, theme, Vega-Lite, tokens); stdlib only,
  `--help` for options.
