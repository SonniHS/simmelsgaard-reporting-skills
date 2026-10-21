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
| `onSelect`, `selectedIndex` | Category zones become focusable buttons. Default selection on a page: the **last closed month**. The selected category gets an assisting area (token `color.marker.assistingArea`) behind its category band, drawn before all marks; every mark keeps full opacity (no dimming: a dimmed AC reads like PY). Filtering stays the preferred interaction. |
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
label height + 2 px, push them apart symmetrically and draw a short leader to the mark. Only two
places, one rule for every route (web, Deneb): right of the last month, and right of a Total
column; never left of the first month. A bar chart names its scenarios once above the top bar. Variance tiers keep their tier name
(`ΔBU`, `ΔBU%`) at the left of the tier's axis.

Label clearance at the chart edge: plot margins come from **measured** label boxes (value
labels at the first and last category, variance labels of the outermost bars and pins, the end
series labels), never from a fixed padding; no label box may extend outside the chart's own
box. A label that does not fit is shortened (fewer decimals, then the unit factor), never cut.
A label's box is its **line box, ≈ 1.2 × the font size high** (with `dominant-baseline: central`
it extends 0.6 em above and below `y`), and ≈ 0.6 em per character wide for digits: reserve
`1.2 × size` of label room, never the font size, or a label placed at `y = size / 2` loses its top
pixel. Prefer the measured `getBBox()` where the layout can run in a browser.

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
- **End legend** (the series names right of the last column, and right of a Total): each name at
  its mark's y, never a fixed list, ordered top to bottom: PY at the triangle tip (or the PY
  column's middle), an outlined reference (BU, PL) at the **upper part** of its column (top + about
  a quarter of its height: the middle collides with the primary's name), AC or FC at the middle of
  the last bar; "AC&FC"
  only when the series runs from AC into FC, plain "AC" when the last column is AC. Collision
  shift: names at least font size + 2 px apart (centre to centre), kept inside the base tier,
  each with a short leader when moved far from its mark. One rule for web charts and the Deneb
  template (`column-two-tier-variance` legendSide "end").
- **Label collisions** (every width, decisive on a phone): each label is a box 1.2 em high and
  as wide as its measured text (≈ 0.6 em per digit). Place the labels of a tier in priority order
  — a Total, **the extremes** (the largest and smallest value, Δ and Δ% of the tier), the values the
  key message cites, the selected period, the last AC period, first and last, the rest — and test each against **every mark of its tier** (columns, the reference behind,
  triangles including the category's own PY triangle, which reaches half its size above its
  value, variance bars, pins and heads) and against the labels already placed. A label that hits
  a mark moves once past it on its own side (above for positive values, below for negative);
  if it still collides or leaves the tier's label room it is left out (the value stays in the
  hidden table and the tooltip). The Total and the cited values are always drawn; the extremes
  win every collision with lower-priority labels (a phone chart that dropped Aug +12.4 % lost the
  month the reader looks for). Never draw a label over a
  bar. Reference implementation: `layoutColumnTiers` in
  `assets/react-reference` (test "no placed label overlaps …").
- **Category axis** (proof run, OURS): period names **never** get an ellipsis ("J… F… M…" is
  ambiguous). Fallback chain: the full name (Jan) → for month names the first letter (J; the year
  is in title line 3) → two staggered rows. Quarters and other codes skip the letter step
  (Q1 → two rows). Value labels thin by the priority above (Total, extremes, cited, selected, last
  AC, first and last); neighbouring labels keep at least 2 px between them. A second line (`period2`, e.g. the year) under the first
  period and where it changes, **only** when the periods span two values.

## 3. Variance chart (absolute bars, relative pins)

Data: variance rows `{ category, value, scenario, impact?, outlier? }`. `value` is raw for
absolute variances and a fraction for relative ones; `null` = N/A.

- **Two references on one chart** (OURS): one comparison per chart by default, switched by a
  compare-with selector; when a spec asks for the variance to BU **and** PY on one month chart,
  stack two absolute tiers (ΔBU, then ΔPY), both on the base px per unit, each with its own
  reference axis; keep the Δ% pins for the default comparison only (reference `delta2` tier).
- **Absolute** (`kind: "absolute"`): bars of the same width as the base columns, on the **same**
  unit and px per unit as the base chart. Colour by impact.
- **Relative** (`kind: "relative"`): pins — a thin stem in the impact colour plus a square head
  in the minuend's notation (AC solid, FC hatched, PL outlined). Pins join the `"%"` scale group.
  Stem = `geometry.pin.thicknessRatio` × bar width clamped to `geometry.pin.stemPx` (2–4 px);
  head = `geometry.pin.headPx.min` (6 px), at the **stem end**, never centred on the axis.
  Scale (one rule for every route; replaces the earlier 1 px per percentage point, which left
  1–3 px stems): the pin tier has **its own scale, sized to the tier** — tier height for vertical
  pins, tier width for horizontal ones (OURS defaults: 48 px in column charts, 90 px in bar
  charts) — so the largest clipped |Δ%| fills about 90 % of it. Charts read together (the months
  and their Total, small multiples) share one pin scale: the smallest px per unit of their tiers
  (`pinScale` in the reference components). Check: the stem of the largest |Δ%| is at least 40 %
  of its tier. **Differing % scales are marked (OURS).** Pin tiers share one % scale wherever
  charts are read together (the months and their Total, small multiples); every other pin tier
  keeps its own scale, because one large relative variance (e.g. −55 % in a structure chart) on a
  page-wide scale would squash every other pin below readability. That is a deviation from "same
  unit, same scale" (CH 4.1), so it must be visible: each pin tier whose scale differs from the
  page's other pin tiers carries a **scaling marker** in the scale-band style (UN 5.2, CH 4.3;
  tokens `color.marker.scaleBandFill` / `scaleBandLine`, label in `color.text.secondary`): a band
  of a round value (1/2/5 × 10ⁿ %, 25–60 % of the tier) at the tier's start with its value
  (`10%`), clear of the tier name, pins and labels, the same value for charts read together; the
  page footnote says the % tiers are on different scales. An unmarked differing % scale fails the
  review (ibcs-review linter F6: `pbir --layout` and `dom`). Reference components: `pagePinScales`
  says per tier whether scales differ and which marker value to use; `pctScaleBand` draws it; pin
  marks carry `data-ppu`, the marker `data-tier="pct"`. The domain is the clipped range (± the
  outlier limit). A pin that does not round
  to zero is at least head/2 + 2 px long; a Δ% that **rounds to zero keeps a baseline marker**
  (the head on the axis, minuend notation, uncoloured) next to its unsigned label. Pin labels
  have **one decimal** (`+5.6%`) by default, the same in every route and on the KPI cards. FC
  heads are hatched with the token period and stripe share at any size.
- **Percentage points** (`kind: "pp"`): bar geometry, label `+2.1pp`, joins the `"%"` group.
- The variance axis shows the **reference** scenario (UN 4.1): PY = solid light thick line, PL/BU
  = two thin parallel lines, FC = hatched band. Tokens `stroke.varianceAxis.*`, `color.axis.*`.
- Orientation: columns (time, vertical) or bars (structure, horizontal, labels on the left).
- Labels are signed (`+12`, `-3`, `+13%`); zero — and a value that rounds to zero at the
  visual's decimals — is unsigned, uncoloured and draws no mark.
- **Outliers** (UN 5.3), the one rule for every route (web, Deneb, SVG): relative pins beyond
  an `outlierLimit` (OURS default ±100 %) are clipped at the limit without a head and get an
  outlier triangle in growth direction at the clip point; the label shows the full value.
  **A pin over 3 × the next-largest |Δ%| of its tier is an outlier too** (OURS, `outlierRatio`,
  default 3; 0 = off): the tier is scaled from the other pins (clip just beyond the largest regular
  pin) and the outlier is clipped at the tier edge with its triangle and full label. Reason: one
  immaterial reference (AC 0 against a budget that rounds to 0, so −100 %) must not flatten every
  other pin of the chart to 0–4 px. Check (OURS): a tier where more than half of the pins carry
  less than 4 px beyond the minimum stem fails (`shortPinWarning`, `ibcs_lint.py dom` E12). Only business-irrelevant relative values may be truncated this way (CH 2.1,
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
- Scenario names (AC, PY, BU) once, at the first row's marks (PY at its triangle, BU at the end of
  its outline, AC at the bar), never a crowded header line: at least 1 em between names and clear
  of the first row's markers; when they would collide, apply the end-legend collision shift (§2)
  or name AC below the last bar.
- With FC as reference the tiers are ΔFC and ΔFC% on a hatched axis, and the primary is AC only.
- Optional, all off by default: per-row polarity (rows of different nature, e.g. absence types),
  grouping brackets (UN 5.1 assisting lines) with a label such as "Top 3 = 62%", a scale band
  (UN 5.2), an "of which" part from the axis, a short muted text after the bar, a row that shows a
  text instead of bars ("not applicable").
- Narrow screens (phone rule for a base + ΔPL + ΔPL% structure chart): the base bars keep at
  least half of the plot width; the variance tiers share the rest, each at least its label room
  (≈ 60 px). Below that width, stack the tiers under the base chart (same row order, category
  labels repeated, each tier keeps its scale; reference `stack: "auto"`) or let the chart scroll horizontally inside its
  own frame — never the page, and never by shrinking one tier's px per unit on its own. Long
  category names first take the free width of the chart (the label column grows into spare
  space: "Services and oth…" with 90 px free is a defect), then wrap to two lines when the row
  step is at least 2.2 × the font size (split at the space nearest the middle, one `<tspan>` per
  line), and only then are cut from the end; never a middle ellipsis.
- **A member with no AC and a reference** (discontinued, REF > 0): AC counts as 0 — the bar is
  labelled `0.0` and the absolute Δ is 0 − REF, from the model's member items
  (`Ibcs.DeltaMember`, semantic-model-ibcs), never blank; Δ% is −100 % (N/A only when REF ≤ 0 or
  blank). The layout warns when a member with a reference has no Δ, and when the members' Δ do
  not add up to the total row's Δ (OURS tolerance 0.5 %).

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
- Labels never cross a line (axis, baseline, assisting line, connector, frame): a label that would
  reach one moves to the far side of its bar, or inside the bar when it fits, else it warns. The
  same rule and test for every waterfall (§6).

## 6. Variance waterfall (bridge)

Data: `{ base: { label, scenario, value }, steps: [{ label, delta, impact?, remainder?, fc? }], total: { label, scenario, value }, variance: { code, value, impact } }`.

`variance` is the model's total Δ (e.g. ΔPY with its impact) from the same query; the chart never
computes it as total − base (the data contract forbids client-side variances).

**Fit to the width (OURS).** A structure bridge (A-29) never overflows its card: when it needs more
width than it has at the page scale, it shrinks its px per unit until it fits (the total-variance
label and the value labels included), moves a magnifier below the overview, and wraps long names to
two lines (a taller row step) before cutting them. Bridges read together keep one scale: fit them
together (`fitWaterfalls`) and draw both at the smaller px per unit. The layout returns the px per
unit it drew (`ppu`) and a warning; `fit: false` keeps the page scale and reports the overflow.
Test at 390 px: no mark outside the chart box.

**One canonical form per decomposition, chosen by the category type** (the same in every renderer:
web, Deneb, SVG-DAX). Tags: STD = stated by IBCS v2.0 (page), FIG = measured from an IBCS figure,
OURS = our default.

| Decomposition | Card | Form |
|---|---|---|
| Structure (companies, products, drivers such as price / volume / mix) | A-29 (STD, p. 112) | Vertical: one row per element, horizontal bars |
| Time (ΔPY by month or quarter) | A-11 (STD, p. 104) | Horizontal: columns over a broken category axis |
| Calculation (P&L lines) | A-28 | §5: grey additions, AC-coloured subtractions, never impact colours |
| Growth / stock (opening, changes, closing) | A-10 | Its own card, grey and black, never impact colours |

**A-29, structure** (`layoutVarianceWaterfall`):

- The reference base bar on top in its scenario notation (PY light, PL/BU outlined, FC hatched),
  the AC (or FC) total bar at the bottom; their names in the category column (STD).
- Contributions float from the running total, coloured by impact (FC steps hatched in the impact
  colour), signed labels left of negative bars and right of positive ones (STD); a remainder row
  when the elements do not add up (OURS: warn above 0.5 % and offer it).
- Assisting lines join the bar ends (STD).
- The total variance is a **horizontal arrow below the total bar**, from the reference level to the
  AC level, labelled with the code and value ("ΔPY −2.1"), in the impact colour (STD). Never an
  extra bar or column.
- Steps come from `Ibcs.DeltaMember` (or the same query-scoped member rule) so discontinued and new
  members count.

**A-11, time** (`layoutTimeWaterfall`):

- Columns: the reference column, the floating periodic Δ columns, then the AC column (STD); the
  category axis is **broken** into the groups reference | periods | AC, with a gap between the
  groups (STD; gap of half a step, OURS).
- Signed Δ labels above rising and below falling columns; value labels above the two end columns.
- The total variance is a **vertical arrow right of the AC column**, from the reference level to
  the AC level, with its label to the right (STD).

**Magnifier (CH 4.5, STD p. 74).** IBCS asks to mark the zoomed part, link it to a second chart at a
larger scale, and state that chart's scale. Our implementation:

- Trigger (OURS, knob `magnifyBelow`): the largest contribution is below **5 % of the base**. Also
  warn when the largest step is below 8 px on the page scale and no magnifier is drawn.
- Factor `k` (OURS): the smallest of 1, 2, 5, 10, 20, 50 … that makes the largest step ≥ 40 px.
- The overview keeps base, total and the steps on the **page** px per unit (never enlarge steps
  inside it: two scales in one plot). One form in every route: **source frame → connectors →
  framed panel**. The zoomed range is outlined (`zoom-box`, the highlight colour), the panel has
  its own frame (`magnifier-panel`), and two dashed connectors (`magnifier-connector`) join the
  frames — no third, empty box between them.
- The panel draws the **steps only**, at k × the page scale, from the lowest running total. Its
  own origin line (baseline) carries the axis-break zigzag, **next to the caption "Steps ×k"**
  (STD: state the scale). Step labels sit in the panel only.
- A-29: the panel goes **beside** the overview with its rows on the same y (names once, at the left)
  when the cell is wide enough; otherwise (phone) **below**, with the names repeated. A-11: a steps
  tier **below** the overview, each column under its period.
- No label touches a line: the axes and baselines, the panel's origin line, the frames, the
  connectors and the assisting lines. A step label that would goes to the far side of its bar
  start, or inside the bar (`color.text.onAc`) when it fits. Test: no label box intersects any of
  these lines, at 390 px and at desktop widths.
- Without room for any panel, keep the page scale, rely on the step labels and warn.

- Warn when base + Σ steps ≠ total, or `variance.value` ≠ total − base (OURS tolerance 0.5 %).
- Hatched FC steps in impact colours: one pattern per stripe colour, ids unique per chart.

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
  then one line per comparison with the scenario code. **Order of Δ and Δ%:** the visual spec
  decides (`deltaOrder`: `absolute-first` | `relative-first`); without a spec setting follow the
  page's reference design, and only when neither says otherwise use absolute first
  (`+8.3  +5.8%  ΔPY`: the absolute Δ is the number the message usually cites). One order per page.
  A % measure shows pp only; a variance the measure lacks is left out
  (no "N/A" line): an omitted Δ% (`undefined`) is never printed as N/A; N/A only for a Δ% the model
  returned blank while the reference is ≤ 0. Cards are centred by default (report shell), left
  aligned on request; Δ% with one decimal.
- Formats per measure from the spec (`display`): decimals fixed per measure row, plain ratios
  with `number.format.plainRatio`, one-decimal Δ% with `number.format.relativeVariance1`.
- Variance numbers coloured by impact (model impact, else sign × polarity) with the text tokens
  `color.variance.*Text`; Δ = 0, Δ that rounds to zero at the displayed decimals, and N/A are
  unsigned/uncoloured (the zero-variance rule of ibcs-notation: `0.00`, never `+0.00`). Never the graphic `color.variance.good` on a number (2.4:1 — the most
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
