# IBCS visual spec — tool-agnostic page hand-off (format 1.0)

The visual spec is the **contract** between the designer (the `ibcs-visual-designer` agent,
`ibcs-composition` + `ibcs-notation` skills) and the builders (Power BI report or app, web app
with React/SVG/Vega-Lite, Fabric app). It fixes *what* every page shows and *which IBCS
notation* applies; it never says *how* a tool draws it. A builder must be able to implement a
page from the spec alone, and a reviewer must be able to check the built page against it.

> Built on the IBCS Standards v2.0; the format itself is ours. CC BY-SA 4.0, see the repository
> NOTICE. Card IDs point to the [chart catalogue](../../ibcs-notation/references/chart-catalogue.md)
> (A-n) and the [table catalogue](../../ibcs-notation/references/table-catalogue.md) (B-…).

## Contents
1. File conventions
2. Top-level structure
3. `page` fields
4. `scaleGroups`
5. `visuals[]` fields
6. Value references, scenarios, variances
7. Chart `type` vocabulary (with card IDs)
8. Markers, annotations, labels
9. Interactions
10. Validation rules (designer and builder), deviation entries
11. Worked example 1 — monthly P&L variance page
12. Worked example 2 — sales by region structure page
13. Snippets — KPI cards, AC&FC with a full-year extension, tall page, deviations

## 1. File conventions

- One YAML file per page, named `<page-id>.visual-spec.yaml`, in a folder per report. Where that
  folder lives is the project's choice (for example `./specs/<report-id>/` next to the report
  source); a report may add a `report.yaml` with the storyline (page order, pyramid) in the same
  folder. Ask the user if the project has no convention yet. A file or folder the user names
  always wins over this naming default.
- UTF-8. Use the real symbols Δ (U+0394), Ø, "..", "_" in labels.
- Field references use DAX-style names as they appear in the semantic model (`'Date'[Month]`,
  `[Net Sales]`); for a non-Power-BI source give the column name the query returns.
- Unknown or undecided items are written `TBD` with a note — never silently omitted.
- Colours, widths and fonts are **never** written as values; they follow from `type`, scenarios,
  variances and the design tokens (the bundled `ibcs-tokens.json` of the `ibcs-notation` skill
  plus the project's `ibcs-tokens.overrides.json`). If a page needs a deviation,
  record it under `deviations` with the IBCS rule it breaks.

## 2. Top-level structure

```yaml
ibcsVisualSpec: "1.0"
page: { … }            # §3 — identity, objective, message, title, context, footer, layout
scaleGroups: [ … ]     # §4 — one per unit that appears in more than one place
visuals: [ … ]         # §5 — every chart and table on the page
interactions: { … }    # §9 — filters, drill, tooltips (interactive media only)
deviations: [ … ]      # §10 — documented departures from IBCS {rule, visual, what, reason, mitigation, acceptedBy}
openQuestions: [ … ]   # things the designer could not decide
```

## 3. `page` fields

| Field | Type | Req. | Meaning |
|---|---|---|---|
| `id` | slug | ✓ | stable page id |
| `name` | string | ✓ | navigation name — grammatically parallel with sibling pages (ST 1.3) |
| `kind` | `message` \| `analysis` | ✓ | message page proves a key message; analysis page supports exploration (p. v) |
| `media` | list of `web-app`, `fabric-app`, `powerbi-report`, `powerbi-org-app`, `pdf`, `slides`, `mobile` | ✓ | where it will be shown; drives footnote/source rules |
| `canvas` | `{width, height, scroll}` px or `preset` | ✓ | default `{width: 1280, height: 720}` (`layout.canvas` token), `scroll: none`; taller pages: see "Tall and scrolling pages" below |
| `objective.goal` | `inform` \| `understand` \| `decide` | ✓ | SA 1.1 |
| `objective.audience` | string | ✓ | role, prior knowledge |
| `objective.question` | string | ✓ | the audience's question this page answers (SA 2.3) |
| `objective.objections` | list | – | who may disagree and why (SA 1.2) |
| `storyline` | `{report, parent, position}` | – | pyramid node this page proves (ST 4) |
| `model` | `{semanticModel, dateTable, scenarioSource, varianceSource}` | ✓ | where values come from, e.g. `scenarioSource: calc group 'Scenario Analysis'` |
| `context.reportingUnit` | string | ✓ | fixed part of title line 1 |
| `context.fixedFilters` | list of `{field, value}` | – | filters baked into the page |
| `context.slicers` | list of `{id, field, default, multi, titleLine, label}` | – | user filters; `titleLine: 1` (structure) or `3` (time/scenario) says where they surface; `label: span \| ytd` for period slicers (see `title.when`) |
| `context.period` | `{type, default, asOf}` | ✓ | e.g. `{type: month, default: latest-closed, asOf: "'Date'[IsClosedPeriod]"}`. `default`: `latest-closed`, `ytd-latest-closed` (first period of the year .. last closed), or an explicit span. `asOf` names the **last closed period** (a flag column or a measure): it sets the AC→FC switch of `AC&FC` and the `separator at: asOf` marker. It is not the data timestamp (refresh time, reference date) — that is `footer.asOf` |
| `message.type` | `detection` \| `explanation` \| `suggestion` \| `none` | ✓ | `none` only on analysis pages |
| `message.source` | `static` \| `template` \| `commentary` | ✓ | `template` = generated from measures (detection only); `commentary` = governed text table keyed by period/entity |
| `message.text` | string | ✓ | the sentence as of design time (with real or sample numbers) |
| `message.template` | string with `{placeholders}` | if template | e.g. `"{ns.AC} mEUR, {dpy} mEUR ({dpyp}) vs PY"` |
| `message.bindings` | map placeholder → value ref (§6) + format | if template | a verdict word ("in line with", "on plan", "above", "below") is a binding too: `{rule: "\|dbup\| < 0.5 %", then: "in line with", else: "{dbu} vs BU"}`, and the threshold is stated in a footnote |
| `message.scope` | string | ✓ | what context the sentence is valid for ("Group, 2026-09"); builders hide/re-scope it when filters move outside |
| `message.highlights` | list of marker refs (§8) | ✓ for message pages | where the cited values are highlighted (SA 4.3) |
| `title.who` | string with `{slicer-id}` placeholders | ✓ | line 1: reporting unit + all active filters. In `who`, `{slicer-id}` expands to `", <selection>"` when the slicer is filtered and to nothing at its default ("all") |
| `title.what` | list of `{measure, unit, by, sort, note}` or `{set, unit}` | ✓ | line 2: measure bold, unit regular |
| `title.when` | string | ✓ | line 3: period(s), then scenarios/variances (`&` vs `and`). `{<slicer-id>}` expands to the slicer's selection as an IBCS period label: one member → its label (`2026-09`); a contiguous range → a span (`Jan..Sep 2026`, token `date.notation.span`); with `label: ytd` a range from the year's first period → YTD (`_Sep 2026`); otherwise a comma list. `{<slicer-id>-11}` = 11 periods before the selection's end; `_{<slicer-id>}` = YTD notation of a single period; `{<slicer-id>.year}` = the year of the selection's last period. The examples use the slicer ids `month`, `quarter` and `period` |
| `footer.sources` | list | ✓ | system, model, table |
| `footer.asOf` | value ref or field | ✓ | data timestamp (refresh time or reference date); the last closed period is `context.period.asOf` |
| `footer.footnotes` | list of `{marker, text}` | – | definitions ("*Currency adjusted") |
| `layout.grid` | `{columns, rows, margin, gutter}` | ✓ | default 12 columns, tokens `layout.*` |
| `layout.header` | `messagePosition: above-title \| right-of-title` | ✓ | identical on every page of the report |
| `layout.responsive` | notes for phone/tablet | – | e.g. one-line title, panel reflow |

**Compare-with selector in title line 3.** A selector that switches the comparison (BU ↔ PY) is a
slicer with `titleLine: 3`, e.g. `{id: compare, field: "'Compare'[Scenario]", default: BU, multi:
false, titleLine: 3, options: [BU, PY]}`, so lint V3 requires its placeholder in `title.when`.
`{compare}` expands to the scenario list of the selection, `{compare.delta}` to its variance codes:

| Selection | `{compare}` | `{compare.delta}` |
|---|---|---|
| BU (default) | `AC and BU` (`AC&FC and BU` on an AC&FC chart) | `ΔBU and ΔBU%` |
| PY | `AC and PY` | `ΔPY and ΔPY%` |
| BU and PY | `AC and BU and PY` | `ΔBU and ΔPY` (plus the % codes of the shown tiers) |

Example: `when: "_{month} {compare}, {compare.delta}"` → "_Sep 2026 AC and BU, ΔBU and ΔBU%". The
selector switches the notation, not only the numbers: the variance tiers, their axes (reference
notation), the Δ codes on KPI cards and the headline clauses follow it (report-shell §5). A
variance id stays bound to its meaning (§6): use one id per selection (`dbu`, `dpy`) and let the
selector pick which one a tier shows.

**Variance to BU and PY on one month chart.** Default: one comparison per chart (the selector's
default, BU on a budget page), with the other one a selector away. When the spec asks for both at
once, stack two absolute tiers above the base (`ΔBU` then `ΔPY`, both on the base px per unit, each
with its own reference axis) and leave out the Δ% tiers, or keep Δ% only for the default
comparison; never draw both pins and both bars in one cell.

**Tall and scrolling pages.** One screen (1280 × 720) is the default and the IBCS ideal (CO 5:
everything needed on one page). A taller canvas (e.g. `{width: 1280, height: 1120, scroll:
vertical}`) is allowed only for media that scroll — web and Fabric apps, a Power BI page with a
custom page size — never horizontal scroll. Rules: the first screen (top 720 px) holds the key
message, the title, the slicers and the visual that proves the message — with a two-clause
message ("…, and Germany has the largest gap"), at least the visual proving the **first** clause; a
later clause may be proved below the fold if its highlight is there and the message names where
("see Revenue by company"), otherwise split the message or move that visual up; keep the grid row height
the same as on a one-screen page (raise `layout.grid.rows` with the height, e.g. 12 rows for
1120 px) so placements stay comparable; scale groups span the whole canvas; footnotes, sources
and as-of sit at the end of the canvas. Say in `layout.responsive` how print/PDF handles the
height (two pages, or split into two specs).

## 4. `scaleGroups`

Every unit that appears in more than one visual or tier gets **one** scale group; all members
render the **same value per pixel** (CH 4.1, ISO 24896). The group is defined by its **px per
unit**, not by a shared domain: each member's plot extent = its own data range × px per unit
(CH 4.2), so a member with smaller values gets a shorter (or narrower) plot, never the larger
member's domain max at the same size. Builders compute the px per unit once from the current
filter context and size each member's plot and container from its own range plus the fixed
overhead of the chart (labels, tiers, padding).

```yaml
scaleGroups:
  - id: meur                 # referenced by visuals/tiers
    unit: mEUR
    kind: absolute           # absolute | relative
    members: [v1.dpl-bars, v2, v3.base, v3.dpl]   # visual id or visual.tier id
    pxPerUnit: null          # optional, px per unit (relative: per percentage point); null = derived
    domain: shared           # shared (ranges computed jointly, include 0) | fixed {min, max}
    sizing: identical        # identical | size-to-data (panel length ∝ max) | scale-band
    scaleBand: null          # for sizing: scale-band → {value: 10, label: "10"}
    note: "ΔPL table bars use the same px per mEUR as the waterfall"
```

`pxPerUnit` omitted: the builder derives it from the member with the largest range and the extent
its grid cell allows ((extent − fixed overhead) ÷ range), then gives every member that px per unit
and sizes each one to its own range. A fixed `domain: {min, max}` is for one member's own range
(e.g. an indexed zoom), not for aligning members.

Rules: `includeZero` is implied (CH 1.1). Relative variances (ΔPY%, ΔPL%) as pins get a `"%"` group
per set of charts read together (e.g. `pct-bu` for the months and their Total), each sized to its
pin tier (OURS: the largest |Δ%| fills about 90 % of a 48 px column tier or a 90 px bar tier). When
a page has more than one such group, their scales differ: declare each with `sizing: scale-band`
and a `scaleBand: {value: 0.1, label: "10%"}` (a round value 25–60 % of the tier, the same within
the group), add the marker to every member and a footnote; no `deviations` entry is needed, the
marker is the documented rule (OURS, UN 5.2 / CH 4.3). Why: one −55 % structure variance on one
page-wide % scale would squash every other pin below readability. Indexed zoom (domain not including 0) is allowed only for
`kind: relative` index data near 100 % and must be declared with `domain: {min, max}` and
`deviations` note. A full-year total next to months (an extension, §7) stays in the months'
group if it fits; otherwise follow ibcs-notation §8 (full-year total next to months): own group
only with a scale band in both groups and a `deviations` entry.

**Check px per unit against the cells before declaring a group (ours).** One group may span a
vertical column chart and a horizontal bar chart in cells of very different size, e.g. monthly
columns in a short wide cell and YTD bars by member in a narrow one, whose values differ about
10×. Before writing the group, compute (cell extent − fixed overhead) ÷ range for each member,
take the smallest, and check every member at that px per unit: the bars, pins and variances in
**each tier** must stay readable (OURS: the largest bar of each chart ≥ 24 px; steps shorter than
8 px need a magnifying glass). If one member flattens the others, do not declare the group: give
that member its own group with a scale band and a `deviations` entry, or change the cell sizes.

## 5. `visuals[]` fields

| Field | Type | Req. | Meaning |
|---|---|---|---|
| `id` | slug | ✓ | unique on the page |
| `type` | enum §7 | ✓ | chart/table/container kind |
| `card` | string | ✓ | IBCS card(s): `A-23`, `A-23+A-24`, `B-T-VAR`, plus pattern refs `CO 4.2` |
| `question` | string | ✓ | what this visual answers (must support the page message) |
| `subtitle` | string | if > 1 visual | one line, only what differs from the page title ("**EBIT** by division"; "\|" separates items) |
| `grid` | `{col, row, colSpan, rowSpan}` | ✓ | placement on the page grid |
| `data.grain` | list | ✓ | grain of the result set ("one row per country") |
| `data.category` | object | for charts | `{field, kind: time\|structure, periodType, labelField, sort, topN, scope, extension}`; `scope` says which slicers the axis ignores (e.g. "all months of the year of the period slicer") |
| `data.category.sort` | `{by: <value ref> \| field, order: asc\|desc}` | ✓ | structure: usually primary scenario desc; time: always ascending |
| `data.category.topN` | `{n, by, remainder: {label, position: last, excludeFromRank: true}}` | – | keeps structure exhaustive (ST 3.2, A-30) |
| `data.category.extension` | `{label, period, gap, values, tiers, scaleGroup}` | – | extended chart (CO 4.3): one extra category after the last member, e.g. a full-year total next to months. `values` = the base tier's value refs for it (`[ns.AC&FC, ns.BU, ns.PY]`); `tiers` = per tier id the value refs it shows there (`{dbu: [dbu], dbup: [dbup]}`, `none` = empty); `period` = what it covers ("year of the period slicer"); `gap: true` = wider gap before it; `scaleGroup` only if it differs from the base tier's (name it `<visual>.extension` in `scaleGroups.members`) — then a scale band in both groups and a `deviations` entry (see ibcs-notation §8, full-year total next to months) |
| `data.rows` / `data.columns` | for tables | ✓ | row/column types (B cards). Rows: a field entry `{field, sort, type, polarityField}` plus optional per-line entries `{line, type: total\|ofwhich\|percentof\|remainder, polarity}`; or, for multi-measure tables and `kpi-cards` (B-R-MEAS), **measure rows** `{line, type: measure, measure: <measure id>, unit, variances: [variance ids], polarity?}` — one row per measure, each with its own unit (from the measure's `display`) and the variances it shows, in display order (a % measure shows its pp variance, not a Δ%; a variance a measure lacks is left out, not printed N/A). Columns: items `{type: scenario\|variance\|time\|measure\|structure\|total\|embedded-chart, …}`, optionally inside `group: {period, label}` blocks (nested columns) |
| `data.series` | object | stacked | `{field, order, keySeriesAtAxis}` |
| `data.measures` | list | ✓ | `{id, name, field, kind: absolute\|relative, unit, display: {prefix, decimals, format}, polarity: 1\|-1\|0\|by-line, polarityField}` (`by-line`: per row, see §6). `polarityField` = a model column or measure returning +1/−1/0 (e.g. `[Net Sales Polarity]`); when present builders bind to it and `polarity` records the design-time value (they must agree). `display` is an explicit setting and **wins over the automatic scaling rule**; decimals are fixed per scale group; `format` names a token (`number.format.plainRatio` for ratios such as book-to-bill, `number.format.ratio` for %) |
| `data.scenarios` | list in display order | ✓ | subset of `AC, PY, PL, BU, FC, AC&FC, AC*` with `{code, source, period}` if not default; `source` names the model measure when there is no scenario calc group |
| `data.variances` | list | – | `{id, code, measure, minuend, subtrahend, kind: absolute\|relative\|pp, field, display}`. `field` = the explicit model measure returning this variance (`[Net Sales ΔPY]`); when `measure` lists several ids (`[ns, oi]`), `field` is a map `{ns: "[Net Sales ΔPY]", oi: "[Order Intake ΔPY]"}`. Without `field` builders use `page.model.varianceSource`. `display: {format: number.format.relativeVariance1}` for one-decimal Δ%. Variances of plain ratios are `kind: absolute` with the ratio's decimals |
| `data.shape` | list of column names | ✓ | the tidy result set the model must return (feeds model/query authors) |
| `cards` | `{perRow, phonePerRow, sparkline: none\|monthly, deltaOrder: absolute-first\|relative-first}` | – | `kpi-cards` only: cards per row on desktop and phone, optional monthly sparkline (§7), order of Δ and Δ% on each line (default absolute-first unless the page's reference design shows otherwise; one order per page) |
| `tiers` | list | multi-tier | `{id, type, values: [value refs], draw, scaleGroup, position: base\|above\|right}` in drawing order. `draw` maps each value ref of a scenario tier to `primary` (AC, FC, AC&FC — in front), `overlap` (reference behind, shifted) or `triangle` (reference as scenario triangle). Defaults: one value → primary; two → first overlap, second primary. Three scenarios ⇒ `draw` required: one primary, one overlap, one triangle (UN 4.1) |
| `scaleGroup` | id | single-tier charts | omit for tables without embedded charts |
| `labels` | object | ✓ | `{data: all\|primary-only\|selective\|none, selective: [first,last,min,max,current], legend: integrated\|title\|none}` |
| `markers` | list | – | §8 |
| `annotations` | list | – | `{n, target, heading, text}` paired numbered references |
| `interaction` | object | – | per-visual overrides of §9 (tooltip page, drill target, cross-filter) |
| `notes` | string | – | anything a builder must know (e.g. "AC&FC: months > asOf hatched") |

Small multiples and trees are containers:

```yaml
- id: v2
  type: small-multiples
  card: CO 5.1 + A-1
  facet: {field: "'Geography'[Country]", order: same-as v1, maxPanels: 25,
          others: {label: "Rest of Europe", position: last}}
  panel: { type: column, data: { … }, labels: { … } }   # same schema as a visual, minus grid
  scaleGroup: meur
  sizing: size-to-data        # outsized panel gets more space, never another scale
- id: v4
  type: ratio-tree
  card: CO 5.2 + EX 5.1
  root: {node: roi}
  nodes:
    - {id: roi, measure: roi, panel: column, children: [ros, ct], operator: "×"}
    - {id: ros, measure: ros, panel: column, children: [ebit, ns], operator: ":"}
```

## 6. Value references, scenarios, variances

- A **value ref** is `<measureId>.<scenario>` (`ns.AC`, `ebit.PL`) or a variance id (`dpl`,
  `dplp`). Value refs are used in `tiers.values`, `sort.by`, markers, message bindings.
- **Variance ids are page-unique by meaning**: one id = one code, minuend, subtrahend and kind
  (the measure follows the visual). The same id in two visuals means the same comparison;
  AC − BU on the cards and AC&FC − BU in a monthly chart need two ids (`dbu`, `dbu-fc`).
- Outside its own visual (message bindings, page highlights) a variance ref names the visual and,
  if the variance covers several measures, the measure: `{ref: dbu, visual: k1, measure: ns}`, or
  the short form `k1.dbu`. A bare id is allowed only when one visual defines it.
- Scenario codes and their notation are fixed (`ibcs-notation` §2). `AC&FC` = one series that is AC
  for every **closed** period up to `context.period.asOf` (the last closed period, not the data
  timestamp) and FC after it: the open period already shows FC and its partial AC is not drawn.
  Each element keeps its own notation (AC solid, FC hatched; variances with minuend FC hatched).
  Models may call the same series "AC+FC"; in specs and visuals it is always `AC&FC` (value ref
  `ns.AC&FC`). PY next to FC periods and in a full-year extension is the **full**-period PY, never
  cut like-for-like at the reference date — name that measure in `scenarios[].source`.
- Variance codes follow IBCS: `ΔPY`, `ΔPL`, `ΔBU`, `ΔPY%`, `ΔPL%`, explicit `AC-PL`/`FC-PL` when
  ambiguous; variances of % measures are `kind: pp`.
- `polarity` (+1 more is better, −1 less is better, 0 neutral) decides the impact colour only,
  never the geometry. It lives on the measure; a measure whose rows mix revenue, cost and result
  lines (a P&L) sets `polarity: by-line`, and the rows give it per line: `polarityField` on the
  row field entry (a model column with +1/−1/0, e.g. `'Report line'[VarianceDirection]`) and/or
  `polarity` on a per-line entry (wins over the field). A measure (or a measure row) may carry
  its own `polarityField` too (§5). Variances are computed on the
  **displayed** values (costs shown positive), so a cost line is −1 and revenue/result lines +1.

## 7. Chart `type` vocabulary (with card IDs)

| `type` | Card | Category axis | Typical values |
|---|---|---|---|
| `column` | A-1 | time | one scenario |
| `stacked-column` | A-2 | time | ≤ 5 same-sign series |
| `normalized-column` | A-3 | time | shares |
| `indexed-column` | A-4 | time | index vs base period |
| `grouped-column` | A-5 | time | reference behind AC/FC (overlapped) |
| `column-triangles` | A-6 | time | AC columns + reference triangles |
| `variance-column` | A-7 | time | ΔPY / ΔPL |
| `pin-time` | A-8 | time | ΔPY% / ΔPL% (IBCS "horizontal pin chart") |
| `column-waterfall` | A-9 | time | contributions between base and total |
| `growth-waterfall` | A-10 | time | stock + changes |
| `variance-waterfall-time` | A-11 | time | reference → periodic Δ → AC |
| `line` / `line-selective` / `line-indexed` / `line-grouped` | A-12 / 13 / 14 / 15 | time | many periods, ≤ 3 crossing lines |
| `variance-area` | A-16 | time | Δ over many periods |
| `stacked-area` | A-17 | time | accumulation pattern |
| `bar` | A-19 | structure | one scenario, sorted |
| `stacked-bar` / `normalized-bar` / `indexed-bar` | A-20 / 21 / 22 | structure | composition / shares / index |
| `grouped-bar` | A-23 | structure | reference behind AC (overlapped) |
| `bar-triangles` | A-24 | structure | AC bars + reference triangles |
| `variance-bar` | A-25 | structure | ΔPY / ΔPL |
| `pin-structure` | A-26 | structure | ΔPY% / ΔPL% (IBCS "vertical pin chart") |
| `bar-waterfall` | A-27 | structure | contributions to a total |
| `calculation-waterfall` | A-28 | structure (report lines) | P&L calculation scheme |
| `variance-waterfall-structure` | A-29 | structure | reference → Δ by element → AC |
| `scatter` / `bubble` | A-32 / 33 | two value axes | correlation / portfolio |
| `table-time` / `table-variance` / `table-cross` / `table-combined` | B-T-TIME / T-VAR / T-CROSS / T-COMB | table | |
| `kpi-cards` | B-T-KPI (B-T-VAR transposed) | none — measure rows | AC per measure + Δ% and Δ per comparison |
| `small-multiples` / `ratio-tree` / `chart-table` | CO 5.1 / CO 5.2 / CO 5.3 | container | |

Remainder bars (A-30) are expressed with `data.category.topN.remainder`; multi-tier charts
(CO 4.2) with `tiers`; extended charts (CO 4.3) with `data.category.extension:
{label, value, gap: true}`.

**KPI cards** (`kpi-cards`) are a variance table turned on its side, so they need no deviation:
`data.rows` are measure rows (one card each, in row order), `data.columns` holds the AC scenario
item, and each row's `variances` lists what its card shows. A card = label (measure name), unit
line ("in mEUR", "in %", "ratio"), the AC value in the key-message size or larger, then one line
per comparison with the scenario code — by default the absolute Δ first, then Δ% (`+8.3  +5.8%  ΔPY`;
`cards.deltaOrder: absolute-first`); `relative-first` when the page's reference design shows it, one
order per page (report-shell §6, behaviour contract §10).
Impact colour by polarity on the variance numbers only, with the contrast-safe text tokens
(`color.variance.*Text`, ibcs-notation §3); a Δ that rounds to zero at the displayed decimals
is unsigned and uncoloured; N/A uncoloured. Optional `cards: {perRow, phonePerRow, sparkline:
none|monthly}`; a sparkline shows monthly values on a shared or scale-banded scale. No icons,
traffic lights or gauges.

Not in the vocabulary on purpose: pie, donut, gauge, funnel, radar, treemap, traffic-light
icons, 3-D. If a stakeholder insists, record it under `deviations` with the EX 2 rule.

## 8. Markers, annotations, labels

```yaml
markers:
  - {kind: ellipse, target: {visual: v2, category: Retail, value: dpl}, reason: message}
  - {kind: difference, from: ns.PY, to: ns.AC, target: {visual: v1, category: Germany}}
  - {kind: trend, from: "2024-Q4", to: "2026-Q3", value: ns.AC, method: CAGR}
  - {kind: reference-arrowhead, at: {category: "Ø", value: ns.AC}, label: "Ø"}
  - {kind: scale-band, scaleGroup: meur, value: 10}
  - {kind: outlier, value: dplp, threshold: "> 1.5 × 2nd largest |value|"}
  - {kind: separator, at: asOf}        # AC→FC change on a time axis, after the last closed period
  - {kind: assisting-area, target: {visual: v1, category: "{month}"}, reason: selection}
annotations:
  - {n: 1, target: {visual: v2, category: Retail}, heading: "Retail", text: "…"}
```

`assisting-area` is a light area (`color.marker.assistingArea`, UN 5.1) behind one category band
— the selected or current period/entity — drawn before all marks; scenarios are never recoloured
or dimmed to show a selection. `reason: selection | current-period | group`.

`target` addresses an element by `visual`, optional `tier`, `category` (member label,
`latest`, or a message placeholder such as `{topCountry}`), and `value` (value ref); in tables by
`visual`, `row` (row label) and `column` (`<group label>.<item>`, e.g. `Sep.ΔPL%`); on
`kpi-cards` by `visual`, `row` (the card's measure row) and `variance` (the variance id on that
card), e.g. `{visual: k1, row: "Net sales", variance: dpy}`. Annotation numbers are page-unique and appear twice (at the
element and before the text).

## 9. Interactions

```yaml
interactions:
  crossFilter: filter            # filter | none   (avoid highlight-dimming: collides with scenario fills)
  slicerPlacement: collapsed-pane # never over the title; hidden in print/export
  scaleRecompute: per-filter-context   # every scale group recomputed jointly
  tooltips:
    - {visual: v1, content: "monthly AC, PY, ΔPY for the hovered country", page: tooltip-country}
  drill:
    - {from: v1, field: "'Geography'[Country]", to: country-detail, keeps: [period, channel]}
  messageOnFilter: re-scope       # re-scope (template recalculates) | hide (static/commentary text) | keep (only if still valid)
  emptyState: "No data for the selection — show title + 'No values for {who}, {when}'"
```

## 10. Validation rules

Designer must ensure, builder must reject a spec that violates:

1. `kind: message` ⇒ `message.type ≠ none`, `message.text` is a complete sentence with numbers
   and a comparison, and at least one `highlights` entry exists.
2. `message.source: template` ⇒ `message.type: detection`.
3. Title: `who`, `what`, `when` present; every `context.slicers[].titleLine` has a placeholder in
   that line; no evaluative words in title or subtitles.
4. Time category ⇒ a horizontal-axis type (column/line/pin-time/…); structure category ⇒ a
   vertical-axis type (bar/pin-structure/…). Tables put time, scenarios and variances in columns.
5. Every absolute measure value that appears in > 1 visual/tier with the same unit is in **one**
   scale group; absolute variance tiers are in the **same** group as their base tier. Members of
   one group share px per unit; a member's size in `layout` must follow from its own range (a
   member with a much smaller range in a cell as tall as the largest one is an error, CH 4.2).
6. `kind: relative` measures use relative widths/thin lines; relative variances use `pin-*`.
7. Every variance names `minuend`, `subtrahend`; every measure with a variance has `polarity` or
   `polarityField` (`by-line` ⇒ every row line resolves to 1, −1 or 0 via `polarityField` or a
   per-line entry).
8. Structure with `topN` has a `remainder`; part-of-whole visuals reconcile to the total.
9. Small multiples: same panel type, one scale group, `maxPanels ≤ 25` plus `others`.
10. `footer.sources` and `footer.asOf` present for every medium except pure `slides`.
11. No table column/row merely repeats a chart's numbers (CO 5.3).
12. Every `deviations` entry has `rule`, `what`, `reason` and `acceptedBy` (below); `acceptedBy:
    TBD` ⇒ the same item is in `openQuestions`.
13. `kpi-cards`: every row is a measure row; every variance it lists exists and has `field` or a
    computable minuend/subtrahend.
14. A tier with three scenario values sets `draw` with exactly one `primary`, one `overlap`, one
    `triangle`.
15. `AC&FC` anywhere ⇒ `context.period.asOf` names the last closed period, and time charts with
    it carry a `separator at: asOf` marker.
16. `data.category.extension` with its own `scaleGroup` ⇒ `scale-band` markers for both groups
    and a `deviations` entry (CH 4.1).
17. A variance id defined in more than one visual has the same `code`, `minuend`, `subtrahend`
    and `kind` everywhere (§6); otherwise one of them gets another id.

The mechanical rules (1–5, 7–10, 12–17) run with the ibcs-review linter:
`python3 -I <ibcs-review skill>/scripts/ibcs_lint.py spec page.visual-spec.yaml` (rule IDs V1…V17;
YAML needs PyYAML — e.g. `uv run --no-project --with pyyaml python3 …` — or a JSON copy of the
spec). Rules 6 and 11 and the meaning of every entry stay a human check.

**Deviation entries.** One per departure from an IBCS rule, written so the reviewer can accept
or reject it:

| Field | Req. | Meaning |
|---|---|---|
| `rule` | ✓ | IBCS rule ID(s) broken, e.g. `CH 4.1`, `UN 3.2` |
| `visual` | – | visual id(s) it applies to; omit for the whole page |
| `medium` | – | `powerbi`, `web` or `all` (default): a deviation forced by one tool (e.g. a Power BI hatch compromise) does not bind the other builds of the same spec. A builder may instead keep its own entries in a sibling file `<spec>.deviations.<medium>.yaml` (a list of entries) |
| `what` | ✓ | what differs from the rule, concretely |
| `reason` | ✓ | why (data, tool limit, stakeholder decision) |
| `mitigation` | – | what keeps the reader safe (scale band, footnote, label) |
| `acceptedBy` | ✓ | role or name of who accepted it; `TBD` until then |

A non-empty example is in §13.

---

## 11. Worked example 1 — monthly P&L variance page

Context: CFO monthly pack in a web app (also exported to PDF). Group P&L for the closed month
and YTD vs plan; explain the EBIT gap. Sample numbers are illustrative and reconcile.

```yaml
ibcsVisualSpec: "1.0"
page:
  id: pnl-variance-month
  name: Income statement vs plan
  kind: message
  media: [web-app, pdf]
  canvas: {width: 1280, height: 720}
  objective:
    goal: understand
    audience: CFO and division heads; know the plan, read monthly
    question: "Why is EBIT below plan this month?"
    objections: ["Retail head may attribute the gap to timing, not volume"]
  storyline: {report: monthly-pack, parent: summary, position: 2}
  model:
    semanticModel: Finance
    dateTable: "'Date'"
    scenarioSource: "calc group 'Scenario Analysis' (AC, PL, ΔPL, ΔPL%)"
    varianceSource: "calc group 'Scenario Analysis'"
  context:
    reportingUnit: ABC Group
    fixedFilters: []
    slicers:
      - {id: division, field: "'Organisation'[Division]", default: all, multi: true, titleLine: 1}
      - {id: month, field: "'Date'[Month]", default: latest-closed, multi: false, titleLine: 3}
    period: {type: month, default: latest-closed, asOf: "'Date'[IsClosedPeriod]"}
  message:
    type: explanation
    source: commentary
    text: "EBIT in 2026-09 is 4.1 mEUR, -0.9 mEUR (-18%) below plan, mainly because of Retail (-0.8 mEUR)."
    scope: "ABC Group, all divisions, 2026-09"
    highlights:
      - {kind: ellipse, target: {visual: v2, category: Retail, value: dpl}}
      - {kind: ellipse, target: {visual: v1, row: EBIT, column: "Sep.ΔPL%"}}
  title:
    who: "ABC Group{division}"
    what: [{set: "Income statement", unit: mEUR}]
    when: "{month} and _{month}, PL and AC"
  footer:
    sources: ["ERP general ledger (warehouse table fact_financials)", "Plan 2026 v3 (approved 2025-12-10)"]
    asOf: "'Refresh'[LastRefresh]"
    footnotes:
      - {marker: "*", text: "EBIT = earnings before interest and taxes; costs shown with negative sign"}
  layout:
    grid: {columns: 12, rows: 6, margin: 16, gutter: 12}
    header: {messagePosition: right-of-title}
    responsive: "Phone: title in one line with ' | '; v1 full width first, then v2, v3 stacked."

scaleGroups:
  - id: meur
    unit: mEUR
    kind: absolute
    members: [v1.dpl-bars, v2, v3.base, v3.dpl]
    domain: shared
    sizing: identical
    note: "Table bars, waterfall and monthly tiers use one px-per-mEUR."
  - id: pct-pl
    unit: "%"
    kind: relative
    members: [v3.dplp]
    domain: shared
    sizing: identical

visuals:
  - id: v1
    type: table-combined
    card: B-T-COMB + B-R-MEAS + B-T-VAR + CO 4.4
    question: "Which P&L lines deviate from plan this month and year to date?"
    subtitle: "**Income statement** | {month} and _{month}"
    grid: {col: 1, row: 1, colSpan: 7, rowSpan: 6}
    data:
      grain: [report line]
      rows:
        - {field: "'Report line'[Line]", sort: "'Report line'[Sort]", type: measure,
           polarityField: "'Report line'[VarianceDirection]"}   # +1 revenue/result, -1 cost
        - {line: EBITDA, type: total, polarity: 1}      # bold, solid line above, gap below
        - {line: EBIT, type: total, polarity: 1}
      columns:
        - group: {period: "{month}", label: "Sep"}
          items:
            - {type: scenario, code: PL}
            - {type: scenario, code: AC}
            - {type: variance, ref: dpl}
            - {type: variance, ref: dplp}
            - {type: embedded-chart, id: dpl-bars, chart: variance-bar, value: dpl, scaleGroup: meur}
        - group: {period: "_{month}", label: "_Sep"}
          items:
            - {type: scenario, code: PL}
            - {type: scenario, code: AC}
            - {type: variance, ref: dpl}
            - {type: variance, ref: dplp}
      measures:
        - {id: pnl, name: "P&L value", field: "[Report Value]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: by-line}
      scenarios: [{code: PL}, {code: AC}]
      variances:
        - {id: dpl, code: ΔPL, measure: pnl, minuend: AC, subtrahend: PL, kind: absolute}
        - {id: dplp, code: ΔPL%, measure: pnl, minuend: AC, subtrahend: PL, kind: relative}
      shape: [Line, LineSort, LineType, Period, PL, AC, ΔPL, ΔPL%]
    labels: {data: all, legend: none}
    notes: >
      Lines: Net sales; Material costs; Personnel costs; Other operating costs; EBITDA (result);
      Depreciation; EBIT (result). Values are displayed as an IBCS P&L shows them (costs
      positive; stored in P&L sign and multiplied by the line's display sign), and ΔPL and ΔPL%
      are computed on these displayed values. Polarity per line: -1 for cost lines, +1 for
      revenue and result lines. ΔPL% = (AC−PL)/PL with the signed PL (never ABS); N/A when the
      reference is ≤ 0 or blank (our derivation of UN 4.1 p. 54: PL 100 / AC -20 → -120 %
      shown; PL -30 / AC -10 → N/A). Bars follow the arithmetic sign of ΔPL; polarity only
      colours them. Sample (Sep, PL → AC, ΔPL, ΔPL%, impact): Net sales 52.0 → 50.8 (-1.2,
      -2.3 %, bad); Material 20.8 → 20.0 (-0.8, -3.8 %, good); Personnel 15.2 → 15.6 (+0.4,
      +2.6 %, bad); Other 6.0 → 6.1 (+0.1, +1.7 %, bad); EBITDA 10.0 → 9.1 (-0.9, -9.0 %, bad);
      Depreciation 5.0 → 5.0 (0.0, 0.0 %, no impact colour); EBIT 5.0 → 4.1 (-0.9, -18.0 %, bad).

  - id: v2
    type: variance-waterfall-structure
    card: A-29
    question: "Which divisions explain the EBIT gap?"
    subtitle: "**EBIT** by division | {month}"
    grid: {col: 8, row: 1, colSpan: 5, rowSpan: 3}
    data:
      grain: [division]
      category:
        field: "'Organisation'[Division]"
        kind: structure
        sort: {by: "'Organisation'[DivisionSort]", order: asc}
        topN: {n: 4, by: dpl, remainder: {label: Other, position: last, excludeFromRank: true}}
      measures:
        - {id: ebit, name: EBIT, field: "[EBIT]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: 1}
      scenarios: [{code: PL}, {code: AC}]
      variances:
        - {id: dpl, code: ΔPL, measure: ebit, minuend: AC, subtrahend: PL, kind: absolute}
      shape: [Order, Division, Kind, Value]   # Kind ∈ Base(PL) | Variance | Total(AC)
    scaleGroup: meur
    labels: {data: all, legend: integrated}
    markers:
      - {kind: ellipse, target: {visual: v2, category: Retail, value: dpl}, reason: message}
    annotations:
      - {n: 1, target: {visual: v2, category: Retail}, heading: "Retail",
         text: "Two store openings moved to 2026-11 (commentary from division controlling)."}
    notes: >
      Base bar = ABC Group PL (outlined), contributions green/red by impact, total bar = AC
      (solid dark), total-variance arrow "ΔPL -0.9" below the AC bar. Sample: PL 5.0; Retail -0.8;
      Wholesale +0.1; Online -0.1; Other -0.1; AC 4.1.

  - id: v3
    type: column-triangles
    card: A-6 + A-7 + A-8 + CO 4.2
    question: "Is this month's gap a one-off or a trend?"
    subtitle: "**EBIT** | {month-11}..{month}"
    grid: {col: 8, row: 4, colSpan: 5, rowSpan: 3}
    data:
      grain: [month]
      category: {field: "'Date'[Month]", kind: time, periodType: month,
                 labelField: "'Date'[MonthShort]", sort: {by: "'Date'[MonthKey]", order: asc}}
      measures:
        - {id: ebit, name: EBIT, field: "[EBIT]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: 1}
      scenarios: [{code: PL}, {code: AC}]
      variances:
        - {id: dpl, code: ΔPL, measure: ebit, minuend: AC, subtrahend: PL, kind: absolute}
        - {id: dplp, code: ΔPL%, measure: ebit, minuend: AC, subtrahend: PL, kind: relative}
      shape: [MonthKey, MonthShort, PL, AC, ΔPL, ΔPL%]
    tiers:
      - {id: base, type: column-triangles, values: [ebit.AC, ebit.PL], scaleGroup: meur, position: base}
      - {id: dpl, type: variance-column, values: [dpl], scaleGroup: meur, position: above}
      - {id: dplp, type: pin-time, values: [dplp], scaleGroup: pct-pl, position: above}
    labels: {data: primary-only, legend: integrated}
    markers:
      - {kind: separator, at: year-change}
    notes: "12 closed months ending at {month}; PL as outlined right-pointing triangles; ΔPL tiers on a double-line (PL) axis; year label under Jan."

interactions:
  crossFilter: filter
  slicerPlacement: collapsed-pane
  scaleRecompute: per-filter-context
  tooltips:
    - {visual: v1, content: "account-level detail of the hovered line", page: tooltip-accounts}
  drill:
    - {from: v2, field: "'Organisation'[Division]", to: division-pnl, keeps: [month]}
  messageOnFilter: hide    # commentary is valid only for the full group and the commented month
  emptyState: "Title stays; table shows 'No postings for {who}, {month}'."

deviations: []
openQuestions:
  - "Show BU in addition to PL once the 2026 budget is loaded? (would add a third scenario as triangles)"
```

Why these choices: the table is the lookup (all lines, month and YTD), the waterfall carries the
explanation (where the −0.9 comes from), the multi-tier chart rules out "one-off"; the three
visuals share one mEUR scale so the −0.8 bar is comparable everywhere; the message cites
values that are circled.

## 12. Worked example 2 — sales by region structure page

Context: sales director, quarterly, Power BI org app. Detection message; analysis-friendly but
still a message page.

```yaml
ibcsVisualSpec: "1.0"
page:
  id: sales-by-country-quarter
  name: Net sales by country
  kind: message
  media: [powerbi-org-app]
  canvas: {width: 1280, height: 720}
  objective:
    goal: inform
    audience: Sales director and country managers
    question: "Where did net sales grow versus last year this quarter?"
  storyline: {report: sales-review, parent: summary, position: 1}
  model:
    semanticModel: Sales
    dateTable: "'Date'"
    scenarioSource: "calc group 'Scenario Analysis' (AC, PY, ΔPY, ΔPY%)"
    varianceSource: "calc group 'Scenario Analysis'"
  context:
    reportingUnit: ABC Corporation, Europe
    slicers:
      - {id: channel, field: "'Channel'[Channel]", default: all, multi: true, titleLine: 1}
      - {id: quarter, field: "'Date'[Quarter]", default: latest-closed, multi: false, titleLine: 3}
    period: {type: quarter, default: latest-closed, asOf: "'Date'[IsClosedPeriod]"}
  message:
    type: detection
    source: template
    text: "Net sales in 2026-Q3 are 148.2 mEUR, +6.4 mEUR (+5%) vs PY; Germany contributes +4.1 mEUR."
    template: "Net sales in {quarter} are {ns.AC} mEUR, {dpy} mEUR ({dpyp}) vs PY; {topCountry} contributes {topCountryDpy} mEUR."
    bindings:
      ns.AC: {ref: ns.AC, format: number.format.absolute}
      dpy: {ref: dpy, format: number.format.variance}
      dpyp: {ref: dpyp, format: number.format.relativeVariance}
      topCountry: {ref: "TOPN(1, countries, dpy).Country"}
      topCountryDpy: {ref: "TOPN(1, countries, dpy).dpy", format: number.format.variance}
    scope: "follows the slicers"
    highlights:
      - {kind: ellipse, target: {visual: v1, tier: dpy, category: "{topCountry}", value: dpy}}
  title:
    who: "ABC Corporation, Europe{channel}"
    what: [{measure: "Net sales", unit: mEUR, by: countries, sort: "AC ↓"}]
    when: "{quarter} AC and PY and ΔPY"
  footer:
    sources: ["CRM invoices (lakehouse table fact_sales)"]
    asOf: "'Refresh'[LastRefresh]"
    footnotes:
      - {marker: "*", text: "Net sales after discounts and returns, intercompany excluded"}
  layout:
    grid: {columns: 12, rows: 6, margin: 16, gutter: 12}
    header: {messagePosition: right-of-title}
    responsive: "Phone layout: v1 only (tiers side by side, scrolls vertically); v2 on its own page."

scaleGroups:
  - id: meur
    unit: mEUR
    kind: absolute
    members: [v1.base, v1.dpy, v2]
    domain: shared
    sizing: identical
  - id: pct-py
    unit: "%"
    kind: relative
    members: [v1.dpyp]
    domain: shared
    sizing: identical

visuals:
  - id: v1
    type: grouped-bar
    card: A-23 + A-25 + A-26 + A-30 + CO 4.2
    question: "Which countries grew, by how much and how fast?"
    subtitle: null          # page title already says it all
    grid: {col: 1, row: 1, colSpan: 6, rowSpan: 6}
    data:
      grain: [country]
      category:
        field: "'Geography'[Country]"
        kind: structure
        sort: {by: ns.AC, order: desc}
        topN: {n: 8, by: ns.AC, remainder: {label: "Rest of Europe", position: last, excludeFromRank: true}}
      measures:
        - {id: ns, name: "Net sales", field: "[Net Sales]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: 1}
      scenarios: [{code: PY}, {code: AC}]
      variances:
        - {id: dpy, code: ΔPY, measure: ns, minuend: AC, subtrahend: PY, kind: absolute}
        - {id: dpyp, code: ΔPY%, measure: ns, minuend: AC, subtrahend: PY, kind: relative}
      shape: [Country, SortKey, IsRemainder, PY, AC, ΔPY, ΔPY%]
    tiers:
      - {id: base, type: grouped-bar, values: [ns.PY, ns.AC], scaleGroup: meur, position: base}
      - {id: dpy, type: variance-bar, values: [dpy], scaleGroup: meur, position: right}
      - {id: dpyp, type: pin-structure, values: [dpyp], scaleGroup: pct-py, position: right}
    labels: {data: primary-only, legend: integrated}
    markers:
      - {kind: ellipse, target: {visual: v1, tier: dpy, category: "{topCountry}", value: dpy}, reason: message}
    notes: >
      PY bar light solid behind AC, shifted up; tiers left→right AC|ΔPY|ΔPY% with tier titles
      above; ΔPY axes solid light; "Rest of Europe" after a wider gap and excluded from the sort;
      bold Europe total row is NOT drawn (total is in the message) — add as extended category if
      the report owner wants it.

  - id: v2
    type: small-multiples
    card: CO 5.1 + A-1
    question: "Is the growth steady or concentrated in this quarter?"
    subtitle: "**Net sales** by country | {quarter-7}..{quarter}"
    grid: {col: 7, row: 1, colSpan: 6, rowSpan: 6}
    facet:
      field: "'Geography'[Country]"
      order: same-as v1
      maxPanels: 25
      others: {label: "Rest of Europe", position: last}
    panel:
      type: column
      data:
        grain: [country, quarter]
        category: {field: "'Date'[Quarter]", kind: time, periodType: quarter,
                   labelField: "'Date'[QuarterShort]", sort: {by: "'Date'[QuarterKey]", order: asc}}
        measures: [{id: ns, name: "Net sales", field: "[Net Sales]", kind: absolute, unit: EUR,
                    display: {prefix: m, decimals: 0}, polarity: 1}]
        scenarios: [{code: AC}]
        shape: [Country, QuarterKey, QuarterShort, AC]
      labels: {data: selective, selective: [first, last, max], legend: title}
    scaleGroup: meur
    sizing: size-to-data
    markers:
      - {kind: separator, at: year-change}
    notes: "Germany panel double height at the same scale (size to data, CH 4.2); light gridlines allowed in panels (SI 3.1 exception); quarter labels only on the bottom row of panels."

interactions:
  crossFilter: filter
  slicerPlacement: collapsed-pane
  scaleRecompute: per-filter-context
  tooltips:
    - {visual: v1, content: "monthly AC and PY of the hovered country", page: tooltip-country-months}
  drill:
    - {from: v1, field: "'Geography'[Country]", to: country-detail, keeps: [quarter, channel]}
  messageOnFilter: re-scope
  emptyState: "If a channel has no sales in a country, the country stays in the list with 0 (MECE), not dropped."

deviations: []
openQuestions:
  - "Should the remainder be 'Rest of Europe' (ST 3.2) or is a fixed country list required by the board?"
```

Why these choices: structure on the vertical axis with PY/AC overlapped and both variance tiers
answers "where and how much"; small multiples on the same mEUR scale answer "steady or one-off"
without a spaghetti chart; the template message is a detection, so it may follow the slicers.

## 13. Snippets — KPI cards, AC&FC with a full-year extension, tall page, deviations

Excerpts, not a complete page: a sales cockpit for a web app and a Power BI report on a model
with explicit measures (no scenario calc group). Generic sample numbers.

```yaml
page:
  canvas: {width: 1280, height: 1120, scroll: vertical}      # tall page: see §3
  context:
    slicers:
      - {id: period, field: "'Date'[Month]", default: ytd-latest-closed, multi: true, titleLine: 3, label: span}
    period: {type: month, default: ytd-latest-closed, asOf: "'Date'[IsClosedPeriod]"}   # last closed month
  title:
    when: "{period} PY and BU and AC, ΔPY and ΔBU"           # → "Jan..Sep 2026 PY and BU and AC, ΔPY and ΔBU"
  footer:
    asOf: "[Reference Date]"                                  # data timestamp, not the AC→FC switch
  layout:
    grid: {columns: 12, rows: 12, margin: 16, gutter: 12}
    responsive: "Phone: two cards per row; v2 scrolls inside its own frame. PDF: two A4 pages, k1 + v2 first."

scaleGroups:
  - {id: meur, unit: mEUR, kind: absolute, members: [v2.base, v2.dbu], domain: shared, sizing: scale-band,
     scaleBand: {value: 10, label: "10"}}
  - {id: meur-fy, unit: mEUR, kind: absolute, members: [v2.extension], domain: shared, sizing: scale-band,
     scaleBand: {value: 10, label: "10"}}
  - {id: pct-bu, unit: "%", kind: relative, members: [v2.dbup], domain: shared, sizing: identical}

visuals:
  - id: k1
    type: kpi-cards
    card: B-T-KPI + B-R-MEAS
    question: "Where do the key sales figures stand vs PY and budget?"
    subtitle: null
    grid: {col: 1, row: 1, colSpan: 12, rowSpan: 2}
    cards: {perRow: 4, phonePerRow: 2, sparkline: none}
    data:
      grain: [measure]
      rows:
        - {line: "Net sales", type: measure, measure: ns, unit: mEUR, variances: [dpyp, dpy, dbup, dbu]}
        - {line: "Gross margin %", type: measure, measure: gm, unit: "%", variances: [dpy-pp]}
        - {line: "Order intake", type: measure, measure: oi, unit: mEUR, variances: [dpyp, dpy]}
        - {line: "Book-to-bill", type: measure, measure: b2b, unit: ratio, variances: [dpy-b2b]}
      columns:
        - {type: scenario, code: AC}
      measures:
        - {id: ns, name: "Net sales", field: "[Net Sales]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: 1, polarityField: "[Net Sales Polarity]"}
        - {id: gm, name: "Gross margin %", field: "[Gross Margin %]", kind: relative, unit: "%",
           display: {decimals: 1, format: number.format.ratio}, polarity: 1}
        - {id: oi, name: "Order intake", field: "[Order Intake]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: 1}
        - {id: b2b, name: "Book-to-bill", field: "[Book To Bill]", kind: relative, unit: ratio,
           display: {decimals: 2, format: number.format.plainRatio}, polarity: 1}
      scenarios:
        - {code: AC}
        - {code: PY, source: "[<Measure> PY] (like-for-like)"}
        - {code: BU, source: "[Net Sales BU] (net sales only)"}
      variances:
        - {id: dpy, code: ΔPY, measure: [ns, oi], minuend: AC, subtrahend: PY, kind: absolute,
           field: {ns: "[Net Sales ΔPY]", oi: "[Order Intake ΔPY]"}}
        - {id: dpyp, code: ΔPY%, measure: [ns, oi], minuend: AC, subtrahend: PY, kind: relative,
           field: {ns: "[Net Sales ΔPY%]", oi: "[Order Intake ΔPY%]"},
           display: {format: number.format.relativeVariance1}}
        - {id: dpy-pp, code: ΔPY, measure: gm, minuend: AC, subtrahend: PY, kind: pp, field: "[Gross Margin % ΔPY]"}
        - {id: dpy-b2b, code: ΔPY, measure: b2b, minuend: AC, subtrahend: PY, kind: absolute, field: "[Book To Bill ΔPY]"}
        - {id: dbu, code: ΔBU, measure: ns, minuend: AC, subtrahend: BU, kind: absolute, field: "[Net Sales ΔBU]"}
        - {id: dbup, code: ΔBU%, measure: ns, minuend: AC, subtrahend: BU, kind: relative, field: "[Net Sales ΔBU%]",
           display: {format: number.format.relativeVariance1}}
      shape: [Measure, MeasureSort, Unit, AC, ΔPY, ΔPY%, ΔBU, ΔBU%, ImpactΔPY, ImpactΔBU]
    labels: {data: all, legend: none}
    notes: >
      Sample: Net sales 152.3 | ΔPY% +5.8% ΔPY +8.3 | ΔBU% +0.3% ΔBU +0.5; Gross margin % 45.5% |
      ΔPY +1.5pp; Book-to-bill 1.01 | ΔPY 0.00 (+0.0005 rounds to zero: unsigned, uncoloured).

  - id: v2
    type: grouped-column
    card: A-5 + A-6 + A-7 + A-8 + CO 4.2 + CO 4.3
    question: "How does net sales develop by month against budget, and where will the year end?"
    subtitle: "**Net sales** by month | {period.year} AC&FC and BU and PY, ΔBU and ΔBU%"
    grid: {col: 1, row: 3, colSpan: 12, rowSpan: 6}
    data:
      grain: [month]
      category:
        field: "'Date'[Month]"
        kind: time
        periodType: month
        labelField: "'Date'[MonthShort]"
        sort: {by: "'Date'[MonthKey]", order: asc}
        scope: "all months of the year of the period slicer; keeps the other slicers"
        extension: {label: "{period.year}", period: "year of the period slicer", gap: true,
                    values: [ns.AC&FC, ns.BU, ns.PY], tiers: {dbu: [dbu-fc], dbup: [dbup-fc]}, scaleGroup: meur-fy}
      measures:
        - {id: ns, name: "Net sales", field: "[Net Sales]", kind: absolute, unit: EUR,
           display: {prefix: m, decimals: 1}, polarity: 1}
      scenarios:
        - {code: PY, source: "[Net Sales PY Full] (full period: FC months and the year are not cut)"}
        - {code: BU, source: "[Net Sales BU]"}
        - {code: AC&FC, source: "[Net Sales AC&FC] (AC for closed months, FC from the open month on)"}
      variances:
        - {id: dbu-fc, code: ΔBU, measure: ns, minuend: AC&FC, subtrahend: BU, kind: absolute, field: "[Net Sales AC&FC ΔBU]"}
        - {id: dbup-fc, code: ΔBU%, measure: ns, minuend: AC&FC, subtrahend: BU, kind: relative, field: "[Net Sales AC&FC ΔBU%]"}
      shape: [MonthKey, MonthShort, IsClosedPeriod, AC&FC, BU, PY, ΔBU, ΔBU%, ImpactΔBU]
    tiers:
      - {id: base, type: grouped-column, values: [ns.BU, ns.AC&FC, ns.PY], scaleGroup: meur, position: base,
         draw: {ns.BU: overlap, ns.AC&FC: primary, ns.PY: triangle}}
      - {id: dbu, type: variance-column, values: [dbu-fc], scaleGroup: meur, position: above}   # dbu-fc: AC&FC − BU, not the cards' AC − BU
      - {id: dbup, type: pin-time, values: [dbup-fc], scaleGroup: pct-bu, position: above}
    labels: {data: primary-only, legend: integrated}
    markers:
      - {kind: separator, at: asOf}
      - {kind: separator, at: year-change}
      - {kind: scale-band, scaleGroup: meur, value: 10}
      - {kind: scale-band, scaleGroup: meur-fy, value: 10}
      - {kind: assisting-area, target: {visual: v2, category: latest}, reason: current-period}

deviations:
  - rule: "CH 4.1"
    visual: v2
    what: "The full-year extension of v2 (base tier) is drawn on its own scale meur-fy, not on the months' scale."
    reason: "The year (≈ 216 mEUR) is about 10× a month; on one scale the months would flatten."
    mitigation: "10 mEUR scale band in both groups; footnote 3 names the two scales; the ΔBU tiers of the year stay on the months' scales."
    acceptedBy: TBD (report owner)

openQuestions:
  - "Deviation CH 4.1 (own scale for the full-year extension of v2): accepted by the report owner?"
```
