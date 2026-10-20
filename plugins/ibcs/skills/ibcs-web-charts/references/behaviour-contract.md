# Behaviour contract for IBCS web chart components

What a conforming chart or table component does, independent of framework. Names of fields are
suggestions; the behaviour is the contract. Rule codes refer to the IBCS® Standards v2.0
(summarised in our own words). Token paths refer to the token file
`../ibcs-notation/assets/ibcs-tokens.json`, relative to this skill's directory
(`${CLAUDE_SKILL_DIR}` in SKILL.md).

## Contents

1. Shared behaviour of every chart
2. Column chart over time (scenario columns)
3. Variance chart (absolute bars, relative pins)
4. Structure bar chart with variance tiers
5. Calculation waterfall
6. Variance waterfall (bridge)
7. Line chart
8. Small multiples
9. Tables (variance table, statement table)
10. KPI card
11. Title block, footnote
12. Warnings a component must raise

## 1. Shared behaviour of every chart

| Input | Behaviour |
|---|---|
| `title` (required) | Accessible name; use the IBCS title lines (who, what + unit, when + scenarios — UN 2.2). |
| `unit` | Scale group key in raw units (`"EUR"`, `"t"`, `"%"`). Same key on one page ⇒ same px per unit; the chart sizes its own plot (its range × px per unit + its fixed px), never a shared domain max. |
| `format` | Factor (1e3/1e6), decimals, locale, decimal sign, negative style. Fixed per scale group; an explicit setting from the visual spec (`display`) wins over the automatic choice. |
| `width` | Fixed px, else the container width (observe resizes). |
| `polarity` / per-row `impact` | Colour of variances only. Row `impact` from the model wins over row polarity, which wins over chart polarity. |
| `colorMode` | `color` (default), `cvd` (green → blue-green), `bw` (greys). Affects impact colours only. |
| `onSelect`, `selectedIndex` | Category zones become focusable buttons. The selected category gets an assisting area (token `color.marker.assistingArea`) behind its category band, drawn before all marks; every mark keeps full opacity (no dimming: a dimmed AC reads like PY). Filtering stays the preferred interaction. |
| `highlight` | A highlighting ellipse (UN 5.1, token `color.marker.highlight`) around the **value label** the key message cites — never around a whole column. One ring per number. Only for numbers that appear in the key message. |
| hidden data table | On by default; every plotted number, including N/A values. |

Hover and focus: one hit zone per category band (full cross extent), so thin pins are as easy to
hit as thick bars. Tooltips show scenario values and variances coloured by impact, but are never
the only way to read a value — labels are.

Labels: direct value labels, horizontal, in the label token size; only on the primary scenario by
default. When space runs out, shrink to the minimum size, then thin labels while always keeping
the first, last, highest and lowest. Scenario names ("AC", "PL") label the series once — at the
first or last column, or the line end — instead of a legend box. Exactly once per chart: not at
both ends, and not again above and below a bar chart (a bar chart names its scenarios at the top
bar only). Variance numbers that carry an impact colour use the text tokens
(`color.variance.*Text`); bars, pins and markers use the graphic colours.

Series-label placement (OURS): a column or line chart over time names its scenarios at the
**end**, right of the last period (before a separated Total column), each label level with the
mark it names at that period and in the same vertical order; when two would come closer than the
label height + 2 px, push them apart symmetrically and draw a short leader to the mark. Use the
first period only when the right side has no room (a phone chart that keeps its full width). A
bar chart names its scenarios once above the top bar. Variance tiers keep their tier name
(`ΔBU`, `ΔBU%`) at the left of the tier's axis.

Label clearance at the chart edge: plot margins come from **measured** label boxes (value
labels at the first and last category, variance labels of the outermost bars and pins, the end
series labels), never from a fixed padding; no label box may extend outside the chart's own
box. A label that does not fit is shortened (fewer decimals, then the unit factor), never cut.

Missing data: `null` draws nothing (no zero column, no zero-length bar, a gap in lines). One rule
for variances, the same as ibcs-notation §3 and the data contract (`visual-data-contract.md`
§0.4):

| Minuend (AC) | Reference | Absolute Δ | Relative Δ% |
|---|---|---|---|
| present | present, > 0 | AC − REF | (AC − REF) / REF |
| present | ≤ 0 | AC − REF | `N/A` (no pin) |
| present | blank | nothing; in structure and bridge rows AC − 0 when the reference scenario has data for the period (new member) | `N/A` (no pin) |
| blank, member had a reference (discontinued) | present | 0 − REF (never blank: structure rows must add up to the total Δ) | −100 % (or `N/A` if REF ≤ 0) |
| blank | blank | nothing — the category has no row | nothing |

The adapter decides from the **values**, not from a blank Δ%: the model returns BLANK for every
N/A case, so a blank Δ% next to a present AC prints `N/A`, never 0 and never empty.

## 2. Column chart over time (scenario columns)

Data: period rows `{ period, period2?, closed?, AC?, FC?, PY?, PL?, BU? }`.

- Primary series = AC for **closed** periods (up to and including the last closed period), FC
  (hatched) after it. The open period shows FC even when a partial AC exists — the partial AC is
  not drawn. Without a `closed` flag: AC where present, else FC. The switch gets a tick on the
  category axis; the series label is "AC&FC". PY next to FC periods must be the full period.
- `reference` (PY, PL, BU or FC): an overlapped column **behind** the primary, shifted left
  (token `geometry.referenceOffsetRatio.column`), in its scenario notation. When FC is the
  reference, the primary is AC only — FC is never drawn twice.
- `triangle` (a third scenario): a triangle at the reference value, pointing right with its tip on
  the column's left edge. Its size is `geometry.triangleSizeRatio` × column width, clamped to
  `geometry.triangleSizePx` (6–12 px). Draw triangles only next to a column; a triangle far beyond
  the columns' range is drawn at the edge with an outlier marker and does not set the scale.
- `measure: "relative"` (a % measure such as margin): columns 1/3 of the category width instead
  of 2/3 (UN 3.1).
- Category width depends on the period type (UN 3.3; tokens `geometry.categoryWidthByPeriod`,
  `geometry.categoryStepPx`). In a fixed layout cell the categories **fill the cell's width** — no
  dead space; stacked tiers align because they share the same step, not because of a cap. A
  maximum step (OURS: 56 px) applies only when the chart sizes itself (no fixed cell): then the
  chart gets narrower and the layout gives the freed width to its neighbours; never pad a chart
  with empty space. Wide steps keep bars at 2/3 of the step, but pins and triangles use their
  px clamps (below), not the ratio alone.
- Height follows the data at the page's px per unit; small multiples may switch this off to keep
  frames aligned.
- A positive label sits above the taller of the column and the reference behind it.

## 3. Variance chart (absolute bars, relative pins)

Data: variance rows `{ category, value, scenario, impact?, outlier? }`. `value` is raw for
absolute variances and a fraction for relative ones; `null` = N/A.

- **Absolute** (`kind: "absolute"`): bars of the same width as the base columns, on the **same**
  unit and px per unit as the base chart. Colour by impact.
- **Relative** (`kind: "relative"`): pins — a thin stem in the impact colour plus a square head
  in the minuend's notation (AC solid, FC hatched, PL outlined). Pins join the `"%"` scale group.
  Stem = `geometry.pin.thicknessRatio` × bar width clamped to `geometry.pin.stemPx` (2–4 px);
  head = `geometry.pin.headRatio` × bar width clamped to `geometry.pin.headPx` (6–10 px).
- **Percentage points** (`kind: "pp"`): bar geometry, label `+2.1pp`, joins the `"%"` group.
- The variance axis shows the **reference** scenario (UN 4.1): PY = solid light thick line, PL/BU
  = two thin parallel lines, FC = hatched band. Tokens `stroke.varianceAxis.*`, `color.axis.*`.
- Orientation: columns (time, vertical) or bars (structure, horizontal, labels on the left).
- Labels are signed (`+12`, `-3`, `+13%`); zero — and a value that rounds to zero at the
  visual's decimals — is unsigned, uncoloured and draws no mark.
- **Outliers** (UN 5.3): relative pins beyond an `outlierLimit` (OURS default ±100 %) are
  truncated without a head and get an outlier triangle in growth direction; the label shows the
  full value. Only business-irrelevant relative values may be truncated this way (CH 2.1,
  CH 4.4). Absolute variance bars, totals and "Other" are never truncated: the extent is sized
  to the data, or a scale band or magnifying glass is used (CH 4.2–4.5). State truncation in a
  footnote.

## 4. Structure bar chart with variance tiers

Data: structure rows `{ category, AC?, FC?, PY?, PL?, BU?, variances?, impact?/impacts?, remainder?, total?, outlier? }`.

- Sort in the data layer (primary descending), remainder ("Other") last with a gap before it
  (token `geometry.remainderGapRatio`), total bold.
- The remainder is a row like any other: value label, variances and pins. When the remainder (or
  any member) has a reference but no actual (e.g. a discontinued member), the query returns AC = 0
  and Δ = 0 − reference (`Ibcs.DeltaMember`; a model without it: the query-scoped pattern in
  `semantic-model-ibcs` `visual-data-contract.md` §2), never blank, so the rows reconcile with the total.
- Reference as an overlapped bar behind, shifted up (`geometry.referenceOffsetRatio.bar`), or as
  a downward triangle with its tip on the bar's top edge.
- Variance tiers to the right of the base bars, in this order by default: absolute (ΔPL) on the
  **same** px per unit as the base bars, then relative (ΔPL%) pins on the `"%"` scale. Tier names
  above each tier. Model-supplied variances win over computed ones; a key present with `null` is
  N/A.
- With FC as reference the tiers are ΔFC and ΔFC% on a hatched axis, and the primary is AC only.
- Optional, all off by default: per-row polarity (rows of different nature, e.g. absence types),
  grouping brackets (UN 5.1 assisting lines) with a label such as "Top 3 = 62%", a scale band
  (UN 5.2), an "of which" part from the axis, a short muted text after the bar, a row that shows a
  text instead of bars ("not applicable").
- Narrow screens (phone rule for a base + ΔPL + ΔPL% structure chart): the base bars keep at
  least half of the plot width; the variance tiers share the rest, each at least its label room
  (≈ 60 px). Below that width, stack the tiers under the base chart (same row order, category
  labels repeated, each tier keeps its scale) or let the chart scroll horizontally inside its
  own frame — never the page, and never by shrinking one tier's px per unit on its own. Long
  category labels are shortened in the middle.

## 5. Calculation waterfall

Data: `{ label, kind: "base" | "delta" | "subtotal" | "total", value }`, delta `value` = the
**signed** effect on the running total (query: amount × sign of the line).

- Base, subtotals and total stand on the axis, bold, with a calculation line above.
- Additions in a mid grey (`color.scenario.stackGrays[1]`), subtractions in the AC colour; labels
  without minus sign, subtraction labels left of the bar (the IBCS rule: the fill says add or
  subtract). Fill by the row's **effect**, not its name: a cost line whose value lowers cost (e.g. a
  favourable variance to standard) is an addition and grey. Option for cash-flow style "Change in …"
  lines: signed delta labels.
- Option for bridges between two scenarios: base/total rows painted in scenario notation and
  delta steps coloured by impact (`sign(value) × polarity`, or the model's impact); then delta
  labels are signed.
- Warn when a subtotal does not reconcile with the running total (OURS tolerance 0.5 %).
- Labels never cross an assisting line (connectors, the base-value line of a total-variance
  marker): a label that would reach one moves to the other side of its bar.

## 6. Variance waterfall (bridge)

Data: `{ base: { label, scenario, value }, steps: [{ label, delta, impact?, remainder? }], total: { label, scenario, value }, variance: { code, value, impact } }`.

`variance` is the model's total Δ (e.g. ΔPY with its impact) from the same query; the chart never
computes it as total − base (the data contract forbids client-side variances).

- Base in reference notation (e.g. PY), steps coloured by impact (FC steps hatched), total in AC
  (or FC) notation. Variance bridges colour by impact; only calculation waterfalls use greys.
- A total-variance marker (arrow plus "ΔPY −2.1") between base and total, from `variance`.
- Orientation bars (structure contributions) or columns (time, PY → Q1..Q4 → AC).
- Warn when base + Σ steps ≠ total, or `variance.value` ≠ total − base (OURS tolerance 0.5 %);
  offer a remainder step. Steps come from `Ibcs.DeltaMember` (or the same query-scoped member
  rule) so discontinued and new members count.
- Magnifying glass (CH 4.5) when the largest step is shorter than the minimum readable bar
  (OURS: 8 px) on the page scale. Geometry: the overview keeps base, total and the steps on the
  page px/unit; beside it (columns) or below it (bars) a detail panel draws only the steps on a
  factor scale `k` = the smallest of 1, 2, 5, 10, 20, 50 … that makes the largest step ≥ 40 px,
  starting from the running total at the first step (cut axis: a zigzag break mark on the value
  axis, the panel header "Steps ×k"). Connector lines join each step in the overview to its row
  in the panel; labels sit in the panel only. Bars: when the cell is wide enough for the overview
  plus the panel with its label rooms, put the panel **beside** the overview with its step rows on
  the same y as the overview rows (category labels once, at the left; OURS) — the default "below"
  repeats every label and leaves a wide cell half empty. At phone width the panel goes below the
  overview.
  Without room for a panel, keep the page scale and rely on the step labels; never enlarge steps
  inside the overview (two scales in one plot).

## 7. Line chart

Data: period rows. Series: `AC&FC`, `AC`, `FC`, `PY`, `PL`, `BU`.

- `AC&FC`: one continuous dark line; AC for closed periods, from the open period on FC with
  **hatched square markers** (UN 3.2). If a closed row carries both, AC wins; for the open period
  FC wins. The line-end label names the last point's scenario.
- `AC` and `FC` listed separately: two lines (e.g. a full-year forecast across all months).
- PY light line; PL/BU hollow square markers. References behind, AC&FC in front.
- Line weight from tokens (`stroke.line.*`): absolute measures thick, relative half. Fill-coded
  markers (hollow, hatched) need a minimum size (OURS: 7 px) to be readable.
- Labels `all | last | none`, each above or below its point, whichever is clear of every other
  point at that period (reference markers included) **and of the line segments into and out of
  that period** (every series), with at least 2 px between the label box and any marker box or
  line. Try in this order: above, below, above the topmost point of that period, beside the point
  (away from the incoming segment, then the other side), one line higher; the first clear place
  wins. A thinned interior label with no clear place is left out (the value stays in the table or
  tooltip); the last label is always drawn. A label is never drawn on a marker or a line — check
  the last point: a line falling into it runs through "above", and the line-end legend crowds it
  too.
- Optional trend arrow (UN 5.1) for a trend the key message names, in the impact colour.
- Keep to AC&FC plus one reference; monthly flows read better as columns.

## 8. Small multiples

- Panels in a responsive grid; the same chart type and the **same scale** in every panel (CO 5.1),
  through the page's scale registry.
- Panel height from the panel's own data at the shared px per unit (span × px/unit + fixed label
  px), like every other chart (ibcs-fabric-app `chart-layer.md`, ibcs-power-bi px-per-unit
  rule): a panel with smaller values is shorter. Panels of one grid row align on a common
  **baseline** (zero line at the same y, the row as tall as its tallest panel), so frames still
  read as a grid; never stretch a small panel's axis to fill the row. Labels typically on the last
  value only.
- Wrap the grid without holes: fill rows left to right; a last row with fewer panels stays
  left-aligned and nothing else moves into the gap.
- Warn above the token limit `layout.smallMultiples.maxPanels`; add an "Others" panel.
- Own scale per panel only with a scale band in every panel and a footnote.

## 9. Tables

Variance table / time-series table:

- Columns typed as value (with a scenario header marker), absolute variance, relative variance,
  in-cell bar or pin. Rows typed as detail, subtotal, total, remainder, of-which, ratio.
- Header markers: AC solid, PY light, PL/BU outlined (double line), FC hatched, others a thin rule
  (tokens `stroke.tableHeader.*`). The FC hatch must read at header size: OURS ≥ 4 px inside the
  outline with a stripe period ≥ 4 px; at the 3 px solid-rule height it looks like a dark bar.
- Column gaps (tokens `layout.table.*`): narrow between columns of one type, wide between groups.
- One px per unit for all absolute in-cell bars of the table, one for all pins; both join the
  page's registry.
- Variance numbers black, or tinted by impact with `color.variance.*Text` only (≥ 4.5:1 text
  contrast; ibcs-notation §3). Δ = 0, Δ rounding to zero and N/A: never tinted.
- Cross tables: optional row and column totals (from model values where a sum would be wrong),
  a dash for empty cells, `N/A` for non-interpretable relative variances.

Statement table (P&L, balance sheet, cash flow):

- The table never computes variances: pass ΔREF (display-signed) and ΔREF% as a fraction.
- Ratio rows (margins): values as fractions shown as `42.1%`, variance cells in pp, no bars.
- Hierarchy with expand/collapse (controlled or uncontrolled), keyboard: Enter/Space select,
  Left/Right collapse/expand, Up/Down move.
- Phone: either a reduced column set below a container width, or horizontal scroll inside the
  wrapper with a sticky label column and a cue that more columns are off screen. The cue never
  covers data: no CSS mask or gradient over the scrolling cells (it fades in-cell bars and pins,
  a gradient on data, A4). Use a thin shadow on the sticky label column's edge, or a text cue in
  the caption ("scroll for ΔPY%").
- Totals are never truncated or excluded from the bar scale (CH 2.1). If a total is many times
  its members, size the bars to the data, show the total row without an in-cell bar, or use a
  magnifying glass for the members (CH 4.5); the numbers stay complete.

## 10. KPI card

The visual-spec type `kpi-cards` (card B-T-KPI) is a variance table turned on its side: one card
per measure row, in row order, with the table's numbers and notation.

Data: measure rows `{ label, unit, value, format, variances: [{ code, scenario, absolute,
relative, kind, polarity?, impact? }], series? }`.

- Label, unit line ("in mEUR", "in %", "ratio"), the AC value in the key-message size or larger,
  then one line per comparison with the scenario code, relative before absolute
  (`ΔPY% +5.8%  ΔPY +8.3`); a % measure shows pp only; a variance the measure lacks is left out
  (no "N/A" line).
- Formats per measure from the spec (`display`): decimals fixed per measure row, plain ratios
  with `number.format.plainRatio`, one-decimal Δ% with `number.format.relativeVariance1`.
- Variance numbers coloured by impact (model impact, else sign × polarity) with the text tokens
  `color.variance.*Text`; Δ = 0, Δ that rounds to zero at the displayed decimals, and N/A are
  unsigned/uncoloured. Never the graphic `color.variance.good` on a number (2.4:1 — the most
  common slip); the graphic colours are for bars, pins and markers only. Render the number with
  `data-role="variance-label"` and `data-impact` so the ibcs-review `dom` lint can check it.
- Cards in a responsive row (e.g. 4–5 per row on desktop, 2 on a phone); equal card widths; no
  frames or shadows beyond a thin rule, no status lights. An app shell may set each card on a
  white card surface (UI chrome: small radius, 1 px elevation); the card's content keeps this
  contract. An impact glyph next to a Δ number is optional and only redundant with its sign and
  colour, never the only cue.
- The Δ number the page's key message cites gets the highlight ellipse (UN 5.1), only when that
  comparison is material.
- A small chart of the **monthly** values (not running totals, which hide the variance), with
  the reference as a light line or outlined columns. Each card may have its own scale only if
  every card in the row shows a scale band at the same round value (UN 5.2) — or join the page
  scale.
- No count-up animation, no gauges.

## 11. Title block, footnote

- Key message as its own line above the title (UN 2.1). Title lines: who (with all active
  filters), what (measure in bold) and unit, when (period and scenarios) (UN 2.2). Keep dates and
  ranges unbroken.
- Footnote with sources and data timestamp; mention any truncation, own scales or deviations.

## 12. Warnings a component must raise

Return warnings from the layout function (and surface them in development builds):

- subtotals or bridge steps that do not reconcile;
- a relative value truncated as an outlier, or an `outlier` flag on an absolute value (ignored);
- a fixed (pinned) scale that does not fit, so the chart grew;
- more panels than the small-multiples limit;
- duplicate or conflicting series (e.g. `AC&FC` and `FC`);
- non-finite or out-of-range values dropped;
- a value labelled in a format that differs from the visual's.
