# Chart catalogue and selection matrix

> Our summary of the chart part of IBCS Standards v2.0 EXPRESS (EX 1.1, pp. 96–115) and of the
> replacement and enrichment rules EX 2–EX 5 (pp. 136–142); CC BY-SA 4.0, see the repository
> NOTICE. Card numbers **A-1…A-35** follow the order of the IBCS chart catalogue and are the IDs
> used in visual specs (`card: A-23`). Feasibility notes are ours.

## Contents
1. Ground rules shared by all charts
2. Selection matrix (analysis × data shape → card)
3. Card list A-0…A-35
4. Feasibility by technology
5. Replace X with Y (EX 2, EX 3)
6. Enrich: scenarios, variances, causes (EX 4, EX 5)

## 1. Ground rules shared by all charts

- **Charts prove, tables look up.** A chart is chosen, cut and highlighted to make a message; a
  table is dense and neutral. A chart carrying a key message cannot be replaced by a table (EX 1).
- **Three families**: horizontal category axis (time: columns, pins, column waterfalls, lines),
  vertical category axis (structure: bars, pins, bar waterfalls — **no lines or areas**), and two
  value axes (scatter, bubble).
- **Widths**: absolute 2/3, relative 1/3 of the category; pins are very thin; category width
  grows with period length and stays fixed per page (time) or identical across corresponding
  structure charts.
- **No value axis** when everything is labelled; columns/bars/pins in front of the axis line.
- **Scenarios**: AC solid dark, PY solid light, PL/BU outlined, FC hatched; AC/FC in front.
- **Variances**: green/red/blue by impact (polarity), direction by sign; axis in the reference
  scenario's notation (PY solid light, PL double line).
- **Labels**: positive above / right, negative below / left; segment labels inside; single
  series → name in the title; legends integrated.
- **Year change** on a month axis: a separator tick and a two-line label on the first month.

## 2. Selection matrix

| Analysis | Minimal data shape | Recommended chart | Card |
|---|---|---|---|
| Time series, one measure, few periods | `Period, Value` | single columns | A-1 |
| Time series, pattern over many periods | `Period, Series, Value` (≤ 3 crossing lines) | line chart, legend at line ends | A-12 |
| Time series, dense (daily) | `Date, Series, Value, LabelFlag` | line with selective labels (first, last, min, max) | A-13 |
| Time series, parts that add up | `Period, Series, Value` (same sign, ≤ 5 series) | stacked columns (key series on the axis) / stacked area | A-2 / A-17 |
| Time series, part-to-whole | `Period, Series, Share` | 100 % stacked columns / normalised area | A-3 / A-17 |
| Time series vs a base period | `Period, Value, Index` | indexed columns / indexed lines (arrowhead at 100 %) | A-4 / A-14 |
| Time series, scenario comparison | `Period, AC, PL` | overlapped columns, or AC columns + reference triangles | A-5 / A-6 |
| Time series, scenario comparison, many periods | `Period, AC, PY` | grouped lines (PY light; PL hollow, FC hatched markers) | A-15 |
| Time series, three scenarios | `Period, AC, PY, PL` | overlapped pair + triangle for the third | A-5 + A-6 |
| Time series, absolute variance | `Period, ΔPY, Polarity` | variance columns; many periods → variance area | A-7 / A-16 |
| Time series, relative variance | `Period, ΔPY%, Polarity` | pins on a horizontal category axis | A-8 |
| Stock measure, changes between dates | `Period, Kind(Stock/Change), Value` | growth waterfall (horizontal only) | A-10 |
| Variance PY → AC explained by period | `Item, Kind(Base/Variance/Total), Value, Polarity` | horizontal variance waterfall + ΔPY arrow | A-11 |
| Distribution over time | `Period, Min, Q1, Median, Q3, Max` | boxplot / range chart (no IBCS notation yet) | A-18 |
| Structure, one measure | `Category, Value` | single bars, sorted | A-19 |
| Structure, too many categories | `Category, Value, IsRemainder, SortKey` | top N bars + remainder bar after a wider gap | A-30 |
| Structure, composition | `Category, Series, Value` (same sign, ≤ 5 series) | stacked bars (key series on the axis) | A-20 |
| Structure, part-to-whole | `Category, Series, Share` | 100 % stacked bars | A-21 |
| Structure vs a reference element | `Category, Value, Index` | indexed bars with reference line | A-22 |
| Structure, scenario comparison | `Category, AC, PL` | overlapped bars, or AC bars + reference triangles | A-23 / A-24 |
| Structure, absolute variance | `Category, ΔPL, Polarity` | variance bars | A-25 |
| Structure, relative variance | `Category, ΔPL%, Polarity` | pins on a vertical category axis | A-26 |
| Structure, contributions to a total | `Category, Value` + total | bar waterfall (gray shades) | A-27 |
| Calculation scheme (P&L) | `Order, Line, Kind(Base/Delta/Subtotal/Total), Sign, Value` | calculation waterfall (vertical only) | A-28 |
| Variance PY → AC explained by structure | `Order, Category, Kind(Base/Variance/Total), Value, Polarity` | vertical variance waterfall (+ remainder, ΔPY arrow) | A-29 |
| Distribution by category | `Category, Min, Q1, Median, Q3, Max` | vertical boxplot (no IBCS notation yet) | A-31 |
| Correlation of two measures | `Item, Group, X, Y` | scattergram | A-32 |
| Portfolio, three measures | `Item, Group, X, Y, Size` | bubble chart (area = value) | A-33 |
| Portfolio, four measures | `Item, X, Y, Size, Segment, Share` | bubble pie (sparingly) | A-34 |
| Continuous time / variable width | `Date, Value` / `Item, Width, Height` | continuous time axis / variable-width columns | A-35 |

Combined forms (CO 4) are built from these cards: a multi-tier chart is e.g. `A-6 + A-7 + A-8`,
an extended chart adds an average or benchmark category after a gap, a remainder bar is A-30.

## 3. Card list

| Card | Name | Axis | Notes |
|---|---|---|---|
| A-0 | Chart selection matrix | — | the overview above |
| A-1 | Single column chart | time | one scenario; labels above/below |
| A-2 | Stacked column chart | time | ≤ 5 same-sign series; legend left/right of the stack; key series at the axis |
| A-3 | Normalised (100 %) column chart | time | shares; 100 % reference arrowhead |
| A-4 | Indexed column chart | time | base period = 100 %, arrowhead |
| A-5 | Grouped (overlapping) column chart | time | reference behind, shifted left; AC/FC in front |
| A-6 | Column chart with reference triangles | time | right-pointing triangles at the reference value |
| A-7 | Absolute variance column chart | time | same width and scale as base; axis in reference notation |
| A-8 | Pin chart, horizontal category axis | time | relative variances; head = minuend |
| A-9 | Column waterfall (contribution) | time | contributions between base and total |
| A-10 | Growth waterfall | time | stock measure; changes mid gray / dark; no vertical form |
| A-11 | Horizontal variance waterfall | time | reference → periodic variances → AC, total-variance arrow |
| A-12 | Line chart | time | ≤ 3 crossing lines; scenario in the markers |
| A-13 | Line chart with selective labels | time | dense data; light grid allowed |
| A-14 | Indexed line chart | time | arrowhead at 100 % |
| A-15 | Grouped line chart (series comparison) | time | PY light line, PL hollow markers, FC hatched markers |
| A-16 | Absolute variance area | time | green/red area switching at zero crossings |
| A-17 | Stacked / normalised area chart | time | accumulation or share pattern |
| A-18 | Other horizontal charts (boxplot, range) | time | no IBCS notation yet |
| A-19 | Single bar chart | structure | sorted by AC descending |
| A-20 | Stacked bar chart | structure | legend above the top (or below the bottom) bar |
| A-21 | Normalised (100 %) bar chart | structure | shares |
| A-22 | Indexed bar chart | structure | reference element = 100 % |
| A-23 | Grouped (overlapping) bar chart | structure | reference behind, shifted up |
| A-24 | Bar chart with reference triangles | structure | down-pointing triangles above the bar |
| A-25 | Absolute variance bar chart | structure | same width and scale as base |
| A-26 | Pin chart, vertical category axis | structure | relative variances |
| A-27 | Bar waterfall (structural contribution) | structure | gray shades, total at the end |
| A-28 | Calculation waterfall | report lines | additions mid gray, subtractions dark, bold subtotals; no horizontal form |
| A-29 | Vertical variance waterfall | structure | reference → Δ per element (+ remainder) → AC |
| A-30 | Remainder bar ("Rest of …") | structure | last, after a wider gap, outside the ranking |
| A-31 | Other vertical charts (boxplot, range) | structure | no IBCS notation yet |
| A-32 | Scattergram | two value axes | external legend allowed; label typical points |
| A-33 | Bubble chart (portfolio) | two value axes | bubble **area** encodes the value |
| A-34 | Bubble pie chart | two value axes | sparingly; few segments |
| A-35 | Other two-value-axis charts | — | continuous time axis, variable-width columns |

## 4. Feasibility by technology

| Chart | Power BI native | Deneb / Vega-Lite | SVG in a table cell | Web (SVG/React) |
|---|---|---|---|---|
| Single / stacked / 100 % columns and bars | good | full | bars: very good | full |
| Overlapped columns/bars | side by side only (overlap setting) | full (`xOffset` / `yOffset`) | bars: very good | full |
| Reference triangles | columns: marker-only line series; bars: no | full | very good | full |
| Variance columns/bars (by polarity) | good (colour measure) | full | very good | full |
| Pins | workaround only | full (`rule` + square `point`) | excellent | full |
| Growth / horizontal variance waterfall | partial (no subtotals, colour by sign) | full | per-row floating bars | full |
| Calculation / vertical variance waterfall | not suitable | full | good (no connectors) | full |
| Lines with end / selective labels | good | full | sparklines only | full |
| Variance area | approximate | full (Vega) | — | full |
| Remainder bar with gap | Top N + Others pattern, spacer row | full | easy | full |
| Scatter / bubble | good | full | — | full |
| FC hatch | not native | stripe layer or Vega/SVG pattern | SVG pattern | SVG pattern |

Commercial custom visuals certified by IBCS Institute cover most cards out of the box; the list
is published on ibcs.com.

## 5. Replace X with Y (EX 2, EX 3)

| Replace | With | Rule | Keep the original only if |
|---|---|---|---|
| Pie chart | sorted bar chart, focus item in the highlight colour | EX 2.1 | pies as point markers on a map, 2–3 values each |
| Several ring/donut charts | 100 % stacked columns, one per period/entity | EX 2.1 | — |
| Gauge / speedometer | variance columns over time as small multiples (with trend arrow) | EX 2.2 | real-time monitoring **and** colour shows the current deviation from an obvious target |
| Radar / spider chart | bar charts side by side, same category order | EX 2.3 | circular order is meaningful (compass) |
| Funnel, spheres, 3-D volumes | bar chart of step values; line of conversion rates | EX 2.3 | area exactly proportional to values |
| Spaghetti chart (> 3–4 crossing lines) | small multiples, one line each, shared scale | EX 2.4 | exact cross-line height comparison is the task |
| Traffic lights / RAG dots | variance bars (ΔPY, ΔPL) coloured by impact | EX 2.5 | binary status or threshold compliance where the size of the miss is irrelevant |
| Box-and-arrow concept diagram | a quantitative chart, photo or map (few concept visuals per hour) | EX 3.1 | essential for comprehension |
| Projected text/bullet slide | spoken text + chart; bullets in the handout | EX 3.2 | definitions, quotes under discussion |

## 6. Enrich: scenarios, variances, causes (EX 4, EX 5)

| Before | After | Rule |
|---|---|---|
| AC-only chart | add PL / PY / FC in scenario notation | EX 4.1 |
| scenarios without variances | add ΔPL / ΔPY tiers or columns | EX 4.2 |
| a single result chart | calculation tree of driver charts with operators | EX 5.1 |
| an undifferentiated scatter cloud | clusters marked by colour | EX 5.2 |
| paired bars in arbitrary order | paired bars sorted by one measure (+ trend line) | EX 5.3 |
| time / scenarios / variances in table rows | put them in columns | EX 1.2 |
| parents above children in a stepped table | totals below their children, bold, solid line | EX 1.2, ST 5.2 |
