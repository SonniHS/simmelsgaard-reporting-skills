---
name: ibcs-power-bi
description: >
  Builds Power BI reports (PBIR/PBIP) that follow the IBCS® Standards; use it when building or
  editing a Power BI report to IBCS, when turning an IBCS visual spec into PBIR, when someone asks
  "can Power BI do this IBCS chart natively", or when choosing between native visuals, Deneb, SVG
  measures and certified visuals such as Zebra BI or Inforiver. Provides a theme generated from
  the IBCS design tokens, a routing rule per IBCS chart/table type (native visual with exact
  visual.json properties → Deneb template → SVG-in-DAX measure → certified visual, with licensing
  caveats), a scaffold for a live-connected PBIP report, report-level measures when the shared
  model must not change, page layout (canvas, grid, title block, key message, dynamic texts,
  footnotes, source and data-as-of), slicer defaults, interactions and tooltips, a spec-to-PBIR
  procedure and a build checklist.
---

# IBCS in Power BI reports

Status (as of 2026-10): the theme generator, the PBIP scaffold (`scripts/new_pbip.py`), the
decision rules, the Deneb template library ([ibcs-deneb](../ibcs-deneb/SKILL.md)) and the
checklists are done. An end-to-end test built a live-connected report with these pieces (theme,
report measures, Deneb, SVG measures) and ran it in the service. **Not verified in Power BI
Desktop yet:** the native `visual.json` recipes were checked against the theme schema, not
opened in Desktop. Spec → PBIR is a procedure (§6), not one script.

The notation itself (scenarios, variances, colours, scales, titles) is defined by the
`ibcs-notation` skill (plugin `ibcs`); page and storyline logic by `ibcs-composition`; review by
`ibcs-review` / the `ibcs-reviewer` agent. This skill only says how to reach that notation in
Power BI. File mechanics (visual.json, page.json, report.json, theme serialisation, Deneb
escaping, SVG measures) come from Microsoft's own Power BI agent skills where installed (PBIR
format, PBIP, theme JSON, Deneb and SVG visuals); do not duplicate them here.

References:
- [references/card-routes.md](references/card-routes.md) — route per chart/table type, native
  `visual.json` recipes, certified visuals and licensing.
- [references/theme.md](references/theme.md) — what the generated theme sets and cannot set.
- [references/matrix.md](references/matrix.md) — IBCS tables as a native matrix.
- [references/feature-status.md](references/feature-status.md) — Power BI features this relies on, dated.
- [references/pbir-skeleton.md](references/pbir-skeleton.md) — PBIP files, `definition.pbir`
  connection forms, theme registration, report measures, dynamic text, slicer defaults, tall
  pages, verified JSON for slicer / text box / `tableEx` / interactions, verifying after publishing.

## 1. Theme first (every report)

```sh
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme                  # ibcs-pbi-theme.json (+ -cvd)
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme --overrides ibcs-tokens.overrides.json
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme --check          # CI: stale?
python3 "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --validate --schema reportThemeSchema-2.157.json   # needs jsonschema
```

Run them from the project root; `${CLAUDE_SKILL_DIR}` is this skill's directory. The script
reads the token file bundled with `ibcs-deneb` (IBCS default palette); corporate changes go only
into your own `ibcs-tokens.overrides.json` (format: the `ibcs-notation` skill). A ready-made
default build is in `${CLAUDE_SKILL_DIR}/assets/ibcs-pbi-theme.json` and
`${CLAUDE_SKILL_DIR}/assets/ibcs-pbi-theme-cvd.json`. Apply it as a custom theme
(registered resource + `report.json` reference). What it sets and what it cannot set:
[references/theme.md](references/theme.md). In short, it cannot give PL its outline, FC its hatch,
the variance axis its notation, or colour by polarity: those need per-visual formatting, Deneb or
SVG.

## 2. Route per visual: the cheapest route that is fully IBCS

Decide per visual in this order; take the first route that reaches the notation without a
footnoted compromise:

1. **Native visual**: keeps native interactivity, export, accessibility; no custom-visual policy.
2. **Deneb template** ([ibcs-deneb](../ibcs-deneb/SKILL.md)): hatching, offsets, triangles,
   variance axes, multi-tier charts on one scale, vertical waterfalls. Needs the Deneb visual
   allowed in the tenant.
3. **SVG-in-DAX measure** in a table/matrix ([ibcs-svg-dax](../ibcs-svg-dax/SKILL.md)): chart
   components per row (CO 4.4).
4. **Certified visual** (Zebra BI, Inforiver) or **Fabric Planning** sheets: licensing per viewer
   or per capacity; opaque configuration in PBIR.

| Visual-spec `type` | Route | Why |
|---|---|---|
| `column`, `bar`, `variance-column`, `variance-bar` | native | colour measure returns the token hex by Δ and polarity; signed format string |
| `grouped-column` / `grouped-bar` with PY or PL | native (overlap, AC last) or Deneb | native overlap and PL outline work; FC hatch does not |
| any chart with **FC** periods | Deneb | no hatch in core visuals (as of 2026-10) |
| `column-triangles`, `bar-triangles` | Deneb | native error-bar triangles point up only, centred |
| a **third scenario** as triangle (tier `draw: triangle`, e.g. AC vs BU with PY) | Deneb `column-two-tier-variance` / `bar-structure-variance` (`refMark: bar`) with `triangleScenario`; in a table SVG skeleton 5 | no native triangle at a value |
| `kpi-cards` (B-T-KPI) | SVG KPI card measures in one `tableEx` ([ibcs-svg-dax](../ibcs-svg-dax/SKILL.md) skeleton 4) | the new card cannot colour Δ and Δ% by polarity with a rounded-zero rule, nor lay out several comparisons per card |
| `pin-time`, `pin-structure` | Deneb (chart) / SVG (table) | no native pin head, no N/A rule |
| multi-tier (CO 4.2) | Deneb `column-two-tier-variance` / `bar-structure-variance` | one scale guaranteed |
| `calculation-waterfall`, `variance-waterfall-structure` | Deneb | native waterfall is column-only and colours by sign |
| `small-multiples` | native (shared axis) or Deneb | native is fine without FC |
| `line`, `line-grouped` | native for AC/PY; Deneb when FC/PL markers matter | no hatched or hollow markers natively |
| `table-variance`, `table-time` | native matrix + SVG columns | scenario header rules need SVG or a footnote |
| statement with write-back, or certification is a requirement | certified visual / Fabric Planning | — |

Full table, `visual.json` properties and licensing: [references/card-routes.md](references/card-routes.md).

## 3. Pages

Layout logic comes from `ibcs-composition`. Power BI specifics (values from the `layout.*` tokens):

- Canvas 1280×720 (16:9) by default; a taller page (e.g. 1280×1120, `displayOption`
  `FitToWidth`, readers scroll) when the spec asks for it ([pbir-skeleton.md](references/pbir-skeleton.md) §8).
  Page `background` and wallpaper = the token page colour.
- Header band ~64 px: the **key message** (a separate text box: the evaluation lives here), then
  the **title block** (UN 2.2) as a text box or dynamic-title measure: line 1 who (unit and
  filters), line 2 what (**measure in bold** + unit), line 3 when (period, scenarios,
  variances). The title is descriptive only.
- Grid: margin 16 px, gutter 12 px; visuals snapped to it; tiers of one chart aligned and the same
  width (or one Deneb visual).
- Footer band ~20 px: footnotes (definitions, `*` notes, compromises such as "FC not hatched"),
  **source**, and **data as of** (a measure on the model's refresh/as-of table, ISO 8601
  `YYYY-MM-DD hh:mm`). Mandatory when the page is exported or printed.
- Same unit, same scale (UN 4.1, CH 4.1) = the same **px per unit**, each chart sized to its own
  data (CH 4.2): a chart with smaller values gets a smaller visual, never the larger chart's
  domain max at the same size (that leaves the small chart's plot mostly empty). For the scale
  group's members: pick the px per unit (the spec's `pxPerUnit`, or derived from the member with
  the largest range and the space it may take), set it on every Deneb member (knob `pxPerUnit`,
  or field `PxPerUnit` bound to one DAX measure) and on SVG measures, then size each visual with
  `python3 -I "${CLAUDE_SKILL_DIR}/scripts/scale_layout.py" group.json [--max-extent PX]`
  (ranges per member and tier in, container height/width per member out, from each template's
  `usermeta.ibcs.layout`); pass the size to `to_pbir.py --pos`. Use the ranges of the widest
  filter context the page allows, so slicers never need a bigger visual. The Deneb domain knobs
  (`yMax`, `xMax`, `varMin`, `varMax`, `yMin`, fields `YMax`, …) only share a domain: use them for
  visuals of the same size that must show the same range, never across a same-unit scale group.
  Native charts cannot size their plot to the data: fx-bound axis `start`/`end` with the same span
  at the same plot height (card-routes.md) is their fallback; for members of very different range
  prefer Deneb/SVG or size the native visual's height by the span. Relative variances (%) have
  their own scale group (pins: px per percentage point). Where identical scales are not sensible
  (extreme differences, a Total column next to its months), use scale bands (Deneb knob
  `scaleBand`, the same round value in each chart), clear scaling indicators or a footnote instead.
- Number formats from the tokens; at most 3 significant digits in charts, 4 in tables; units in
  the title, not as "K/M" suffixes on labels. Charts never show raw values: bind scaled measures
  or set the Deneb `unitDivisor`. A spec's explicit display setting (unit, decimals) wins over the
  automatic scaling; decimals are fixed per scale group. Variance numbers stay black, or are
  tinted only with the text variants `color.variance.goodText` / `badText` / `neutralText`.
  Locale and currency are your setting (tokens).
- Scenario names in visuals follow the notation: the combined actual-plus-forecast series is
  **AC&FC** (a calculation item may be called "AC+FC" in the model; it is the same thing).
- Visual headers off in reading view only if users do not need focus mode or export; tooltips on.

## 4. Interactions

- The page carries its message **without clicking** (CO 5); tooltips, drill-through and
  bookmarks add depth only.
- Tooltips: minimal, scenario abbreviations (AC, PY, ΔPY%), the same number formats. Report-page
  tooltips use the same theme and notation.
- Slicers feed the title's who/when lines: drive the dynamic title from the same selections.
  Dynamic texts (key message, title lines, data as of): a text box with a value, or a card on a
  text measure ([pbir-skeleton.md](references/pbir-skeleton.md) §6).
- Slicer defaults are saved selections and do not move with the data: a default such as "YTD to
  the last closed month" needs a relative-period flag column in the model, or (no model change)
  an empty slicer plus period measures that compute their own effective period, with `NoFilter`
  interactions for visuals that always show the full year
  ([pbir-skeleton.md](references/pbir-skeleton.md) §7, §9).
- Drill-through pages use the same page layout; keep a back button.
- Prefer filtering to cross-highlighting. Never recolour or dim scenarios (a dimmed AC reads
  like PY): marks keep full opacity, and the selected category gets an assisting-area band
  (`color.marker.assistingArea`) behind its marks. Deneb templates draw that band for
  `__selected__ == 'on'`.
- Edit interactions so variance tiers filter together with their base chart, never independently.

## 5. Report measures in a live-connected report

When the report is live-connected to a shared model that must not change, write what the model
lacks (AC&FC, full-period PY, scaled Deneb fields, dynamic texts, SVG measures) as **report-level
measures** in `definition/reportExtensions.json`. Rules (details and format:
[pbir-skeleton.md](references/pbir-skeleton.md) §5):

- Bind every report measure with `"SourceRef": {"Schema": "extension", "Entity": …}` in visuals
  (projections, sort, filters, conditional formatting). Without it the service resolves the name
  in the model and every visual using it fails with "Something's wrong with one or more fields"
  (`Missing_References`; verified in an end-to-end test, as of 2026-10). `to_pbir.py` does it for
  Deneb; `python3 -I "${CLAUDE_SKILL_DIR}/scripts/report_measures.py" <name>.Report --fix` does it
  for every visual and writes each measure's `references`; `--check` before every publish.
- Never set `"hidden": true` on a report measure: in the service every visual using it (or a
  measure that references it) then fails with the same error (verified in an end-to-end test).
  Group helpers in a `displayFolder`.
- No dynamic format strings on report measures in a live-connect report (Learn): static format
  strings; scale by dividing in the measure.
- Test every report measure first as a query-scoped `DEFINE MEASURE` (DAX query view, or the REST
  API *Execute Queries*); the same block serves a Fabric App.
- Footnote that the page uses report measures, and list them for the model owner.

A spec's open question that is only a **model gap** (a missing measure that can be built from the
model's existing measures and columns) is not a blocker: solve it with a report measure and
record it. A question about meaning (polarity, which forecast, the closing date) still blocks.

## 6. Spec → PBIR

Input: a visual spec file per page in your project (for example
`./specs/<report>/<page>.visual-spec.yaml`; format defined by `ibcs-composition`).

1. Read the spec; resolve each visual's `type`, scenarios, variances, `scaleGroups`, `tiers`.
2. Choose the route (§2). Write missing measures (scenario, Δ, Δ%, colour, scale-max, title) in
   the semantic model (`semantic-model-ibcs`, plugin `reporting-data`), or as report measures
   when the model must not change (§5). Δ% divides by the
   **signed** reference and returns N/A when it cannot be interpreted (reference ≤ 0); geometry
   follows the arithmetic sign, polarity only selects the colour (good / bad / neutral blue).
3. New report: `python3 -I "${CLAUDE_SKILL_DIR}/scripts/new_pbip.py" --out <dir> --name <report>
   --semantic-model-id <id> --canvas <WxH> [--theme <generated theme>]` (live connection, theme
   registered, one page). Then the header and footer texts, then each visual at its grid position.
4. Native: apply the properties from [references/card-routes.md](references/card-routes.md).
   Deneb: `${CLAUDE_SKILL_DIR}/../ibcs-deneb/scripts/to_pbir.py` with `--field` mappings, the
   spec's knobs, `--sort` (period order), `--filter` (static visual filters) and `--title`;
   scale-group members get `--param pxPerUnit=…` and `--pos` with the size from
   `scripts/scale_layout.py` (§3).
5. Record every compromise in the page footnote and in the spec's `deviations`.
6. Validate (`jq empty` on changed JSON, or `python3 -m json.tool <file> > /dev/null` if jq is not
   installed; `scripts/report_measures.py <name>.Report --check`; a PBIP validator where
   available), preview each Deneb visual with live data (`render-previews.mjs --visual`), open in
   Desktop, compare with the spec, then run the `ibcs-review` skill.
7. After publishing (only when the user asks), look at the rendered page: in a browser (*See
   details* on an error names the fields), or without one through *Export To File* as PDF with a
   known-good report as control ([pbir-skeleton.md](references/pbir-skeleton.md) §10). A clean
   import does not mean the visuals load.

## 7. Distribution

Workspaces, org apps, audiences and dev/test/prod promotion are covered by the `fabric-org-apps`
skill (plugin `fabric-apps`). What matters for the report builder:

- Saving an org app publishes it immediately and without versioning: build and check reports in a
  dev/test workspace, never edit the production app directly.
- Row-level security does not apply to workspace Admins/Members/Contributors: test it as a user
  who only has app access.
- Custom visuals (Deneb, certified visuals) must be allowed by the tenant for every audience, and
  must render in PDF/PowerPoint export and subscriptions if those are used.

## 8. Build checklist

- [ ] Theme generated from the tokens (no hand-edited colours); `--check` clean.
- [ ] Scenarios: AC solid dark, PY solid light, PL/BU outlined, FC hatched; AC/FC in front.
- [ ] Variances: geometry by arithmetic sign; colour by polarity (good / bad / neutral blue); `+`
      on positive values; Δ% from the signed reference with N/A; FC variances hatched; variance
      axis in the reference scenario's notation (or footnoted).
- [ ] Same scale for the same unit on the page (absolute variances included): one px per unit,
      each visual sized to its own range (no empty domain above a small chart), or scaling
      indicators where that is not sensible.
- [ ] Bar width 2/3 (absolute) and 1/3 (relative); category width fixed per period type on the page.
- [ ] Title block (who / what / when), separate key message, footnotes, source, data as of.
- [ ] No legend boxes, value axes, 3-D, shadows or decorative colour; gridlines only where they
      help (dense charts, small multiples).
- [ ] Numbers: token formats, digit limits, units in the title.
- [ ] Every compromise footnoted and listed under `deviations`; report measures footnoted and
      listed for the model owner, none of them `hidden`, all bound with `"Schema": "extension"`
      (`report_measures.py --check` clean); no `"active"` outside slicers.
- [ ] After publishing: every visual renders in the service (browser or PDF export).
- [ ] Checked at the target size, exported to PDF, and with the CVD theme.
- [ ] Custom visuals allowed by the tenant; licences confirmed for every viewer group.
- [ ] Published only when the user asks for it.
