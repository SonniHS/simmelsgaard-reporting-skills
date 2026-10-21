# IBCS notation — detailed reference

> Our condensed restatement of the IBCS Standards v2.0 notation (pp. 16–75) and the chart and
> table parts of EXPRESS (pp. 96–142); CC BY-SA 4.0, see the repository NOTICE. Column `src`:
> `STD` stated by IBCS / ISO 24896, `REC` recommended by IBCS, `FIG` measured from an IBCS figure
> (not normative), `OURS` our default where IBCS is silent. Token paths refer to
> `assets/ibcs-tokens.json`, relative to this skill's directory (`${CLAUDE_SKILL_DIR}` in
> SKILL.md), plus the user's `ibcs-tokens.overrides.json`.

## Contents
1. Scenario rendering geometry
2. Variance chart anatomy
3. Multi-tier, overlay and extended charts
4. Markers
5. Label and legend positions by chart type
6. Period, date and analysis notation
7. Abbreviations
8. Table notation
9. Measure and structure analyses (index, average, ranking, remainder)

## 1. Scenario rendering geometry

| Element | Rule | src | Token |
|---|---|---|---|
| Absolute column/bar width | 2/3 of category width, gap 1/3 | STD | `geometry.barWidthRatio.absolute` |
| Relative column/bar width | 1/3 of category width | STD | `geometry.barWidthRatio.relative` |
| Reference column offset (overlapped) | reference behind, shifted **left** ≈20 % of width | FIG | `geometry.referenceOffsetRatio.column` |
| Reference bar offset (overlapped) | reference behind, shifted **up** ≈25 % of thickness | FIG | `geometry.referenceOffsetRatio.bar` |
| Scenario triangle | height ≈1/3 of column width; columns: points right, tip touching the column's left edge, at the reference value; bars: points down, just above the bar, at the reference value; clamped to 6–12 px (OURS) | FIG | `geometry.triangleSizeRatio`, `geometry.triangleSizePx` |
| Triangle fill | reference notation: PY light solid, PL hollow outlined | STD | `color.scenario.*` |
| Thick line (absolute) | ≈2 pt print / 3 px screen | FIG/OURS | `stroke.line.absolutePt` / `absolutePx` |
| Thin line (relative) | 50 % of thick | STD | `stroke.line.relativeRatio` |
| Line markers | the scenario lives in the markers on a continuous line: AC filled, PL hollow/outlined, FC hatched — never dashed lines; line thickness encodes absolute vs relative only; marker ≈2.5× line width | STD/FIG | `stroke.line.markerToLineRatio` |
| PL outline | dark, ≈1 px on screen | OURS | `stroke.outlinePx` |
| FC hatch | 45°, stripes bottom-left → top-right, period ≈1 mm / 4 px, stripe share 0.45 | FIG/OURS | `pattern.fcHatch.*` |
| Foreground | AC and FC in front of other scenarios; all marks in front of the axis line | STD | — |
| AC → FC change | short vertical separator tick on the category axis | FIG | `color.marker.assistingLine` |
| Year change in a month axis | separator tick between Dec and Jan; first month of the new year labelled on two lines ("Jan / 2026") | FIG | — |

Do-not list: PL as a coloured or dashed line across months; FC as a lighter fill without hatch
(a common native-tool compromise — document it as a deviation if unavoidable); a triangle centred
on, or pointing up from, the column; a black filled triangle for a plan (black arrowheads mean
index or benchmark).

## 2. Variance chart anatomy

| Part | Absolute variance (ΔPY, ΔPL) | Relative variance (ΔPY%, ΔPL%) |
|---|---|---|
| Mark | column (time) / bar (structure) | pin: thin column/bar + head (square = illustrated default) |
| Width | = base column width (`geometry.barWidthRatio.variance`) | body ≈30 %, head ≈85 % of base bar thickness, clamped to 2–4 px and 6–10 px (OURS) (`geometry.pin.*`) |
| Scale | **identical** to the base chart (same value per px) | own % scale (the same-scale rule is for absolute variances), shared across the page's Δ% visuals |
| Fill | minuend notation in impact colour: AC solid, FC hatched (+ colour outline), PL outlined | body in impact colour; head = minuend (AC dark solid, FC hatched) |
| Axis | subtrahend notation: PY → solid light thick (`stroke.varianceAxis.pyWidthPx`); PL/BU → two thin parallel lines (`plLinePx`, `plGapPx`) | same |
| Colour | Δ = 0 (also rounded) → no colour; otherwise three states: `good` if Δ × polarity > 0, `bad` if < 0, `neutral` (blue) if polarity is 0; colour only — direction follows the sign of Δ | same |
| Label | outside, in the direction of change, signed ("+34", "-18") | outside, signed ("+12%"); outliers: no head, triangle |
| Zero | Δ = 0, or Δ that rounds to 0 at the displayed decimals: no mark, unsigned label ("0.0"), default text colour | same |
| Variance of a % measure | pp ("+2.1pp") | ordinary % |

**Variance area** (many periods): green/red area between the variance curve and the reference
axis, switching at zero crossings (interpolate the crossing). **Variance waterfalls**: base =
reference scenario (PY light / PL outlined), contributions green/red floating, total = AC dark,
total-variance arrow ("ΔPY +120") beside the total, assisting connector lines; the vertical
(structure) variant ends with a remainder contribution.

**Calculation waterfall** (P&L): base and subtotals/totals from the axis in gray; additions mid
gray, subtractions dark — **not** green/red (they are not variances); subtraction labels without
minus sign; bold subtotal labels with a thin line above; vertical only. **Growth waterfall**
(stock measure): stocks from the axis, changes mid gray (up) / dark (down); horizontal only.

## 3. Multi-tier, overlay and extended charts (CO 4)

| Type | Geometry | Scale |
|---|---|---|
| Multi-tier, time | extra tiers **above** the primary: AC(+PL/PY) → ΔPL → ΔPL% (bottom → top) | each tier its own axis; same unit ⇒ identical scale (same px per unit; each tier as tall as its own range) |
| Multi-tier, structure | extra tiers **right** of the primary: AC → ΔPL → ΔPL% (left → right); category labels once | same |
| Overlay | same category axis; e.g. columns + line, or integrated variance inside the column | integrated variance: same value axis; prefer multi-tier when space allows (CO 4.1) |
| Extended | extra category (Ø, benchmark, competitor) on a virtual extension of the axis after a gap: right/left for time, below/above for structure | same value axis |

## 4. Markers

| Marker | Shape | Colour token | Placement | src |
|---|---|---|---|---|
| Highlighting ellipse | thin outline ellipse around a label/value | `color.marker.highlight`, `stroke.highlightEllipsePx` | the value the key message cites (further values sparingly) | STD |
| Difference marker | two parallel assisting lines projecting the two lengths + a bar (≈ pin width) between them, optional arrowhead; value label next to it | impact colour | beside the compared columns/bars | STD |
| Trend arrow | thick arrow from first to last period of the trend, head in time direction; optional "CAGR: 10.8%" | impact colour, `stroke.trendArrowPx` | above the series | STD |
| Reference arrowhead | solid black triangle (+ optional thin assisting line) | `color.marker.referenceArrowhead` | temporal index: left of the index point pointing right, "100%" left of it; structural index/benchmark: close to the point, label next to it; normalising: at one end of a 100 % assisting line | STD |
| Annotation reference | numbered circle, in pairs (at the value and at the text) | `color.marker.annotationRef` | at the referenced element and before the annotation text (bold heading + text) | STD/FIG |
| Assisting line / area | thin gray line / light area | `color.marker.assistingLine` / `assistingArea` | separate, group, connect charts (ratio trees), project differences | STD |
| YTD / moving marker | short tick (underscore) / tilde at the column top-left or bar end | dark | each YTD/moving column/bar | REC |
| Scale band | light area from the axis to a common value (power of 10) + labelled line, in every compared chart; optional dotted link between charts | `color.marker.scaleBandFill` / `scaleBandLine` | all charts of the same unit with different scales | STD |
| Outlier marker | pin truncated at the edge, **no head**, full value label, small triangle beyond the label pointing in growth direction | impact colour | only business-irrelevant relative outliers | STD (consistent design) / REC (this design) |
| Magnifying glass | marked zoom area in the main chart linked to a zoomed chart | assisting line + scale band | — | STD |

## 5. Label and legend positions by chart type

| Chart | Legend | Data labels |
|---|---|---|
| Single column/bar | series name in the title | above/below columns; right/left of bars; negative bar → category label right of the axis |
| Stacked columns | left of the first or right of the last column, at segment mid-height | centred in segments that fit (white on dark, black on light); totals above |
| Stacked bars | centred above the top bar (or below the bottom bar), one per segment | centred in segments; total at the bar end |
| Overlapped columns | reference code left of the first pair, AC right of the last column | primary scenario only |
| Overlapped bars | reference code above the first reference bar, AC below the last bar | primary only, right of bar |
| Lines | right of the line end (left-aligned) or left of the start (right-aligned) | peaks above, valleys below; dense → first/last/min/max only |
| Scatter/bubble | external legend next to symbols allowed; label typical points directly | next to points; large bubbles centred |
| Overlay columns + line | series name at the right end of each series (measure bold, unit regular) | all points; secondary series gray |

Always horizontal text. Leader lines when a label cannot sit next to its element.

## 6. Period, date and analysis notation

| Item | Long | Short | Within year | Token |
|---|---|---|---|---|
| Year | 2026 | '26 | — | `date.year`, `date.shortYear` |
| Quarter | 2026-Q2 | '26-Q2 | Q2 | `date.quarter` |
| Month | 2026-01 (or Jan 2026) | '26-01 / Jan '26 | Jan | `date.month` |
| Week | 2026-W37 | '26-W37 | W37 | `date.week` |
| Day | 2026-06-29 | '26-06-29 | Jun 29 | `date.day` |

| Analysis | Notation | Example |
|---|---|---|
| Span | a..b | Jan..Mar, 2023..2025, 2026-01..10 |
| First / last day | .x / x. | .2026, Jun. |
| Year to date / to go | _x / x_ | _Jun 2026 / Jun 2026_ |
| YTD average / last-date value | _xØ / _x. | _Jun 2026Ø / _Jun 2026. |
| Moving (12 months), MAT, MAA | ~x | ~Jun 2026, ~JunØ |
| Average (time or structure) | Ø | Ø'26, EuropeØ, Ø464 |
| Difference of scenarios | a-b | AC'26-AC'25 |
| Ranking | arrow appended | net sales↓ |
| Temporal / structural index | "100%" next to a black arrowhead | 2022 = 100% |
| Histogram class | lo_hi | 16_20 |

Month names, decimal sign and separators follow the organisation's locale, set once in the token
overrides (`number.separator.*`) and in the date dimension's label columns.

## 7. Abbreviations

AC Actual · PY Previous year · PL Plan · BU Budget · FC Forecast · AC* adjusted actual
(footnoted) · ΔPY, ΔPL, ΔBU absolute variances · ΔPY%, ΔPL% relative · AC-PL, FC-PL, (AC-PL)%
explicit forms · pp percentage points · N/A not applicable · YTD, YTG, MAT, MAA · CAGR · Ø
average · RoW rest of world. Monetary prefixes k, m, b (kEUR); SI prefixes k, M, G (kt, MWh); "#"
counts. Short abbreviations in column headers, long forms in row headers; all defined in the
organisation's glossary (UN 1.1). Token group: `abbreviation.*`.

## 8. Table notation

| Element | Rule |
|---|---|
| Column order | row header │ PY · PL · AC │ ΔPY · ΔPY% │ ΔPL · ΔPL% (wide gap between groups, narrow within) |
| Header underline | AC thick dark, PY thick light, PL/BU double thin, FC hatched; variances/structure thin single line |
| Alignment | numbers + headers right, text left; equal width per column type, independent of header length |
| Rules | no vertical lines; thin light row separators; solid line above totals/results |
| Totals / results | bold; rows below their group, columns right of their group; optional light-gray fill (allowed, pp. 121–128) |
| Hierarchy | parents below children (details → total), bold; extra gap between groups; "of which" exception: parent above, of-which row smaller, right-aligned label, not summed |
| "Percent of" | below/right of the referenced figure, smaller (italic), one decimal |
| Remainder | "Other" / "Rest of …" last before the total; excluded from rank, average, top N |
| Variance numbers | black by default; tinted by impact only with a contrast-safe text colour (`color.variance.*Text`, ≥ 4.5:1); Δ = 0 (also rounded) and N/A never tinted |
| Embedded charts | table bars/pins/waterfall bars share one scale per column; sparklines only indexed or on a common scale; traffic lights only for ≤ 3 binary/compliance states |

More: [table-catalogue.md](table-catalogue.md).

## 9. Measure and structure analyses (UN 4.2–4.4)

- **Temporal index:** all periods relative to a base period = 100 %; arrowhead + "100%"; title
  names the base ("indexed, 2022 = 100%").
- **Structural average:** "Ø" + value; assisting line with a small black arrowhead.
- **Ranking:** sort descending by the primary scenario (AC), not by the reference; arrow in title
  line 2 ("sorted by net sales ↓"). The remainder stays last regardless of size.
- **Selecting (top N):** no ISO notation yet — name it in title line 1 ("…, top ten clients") and
  keep the structure exhaustive with a remainder.
- **Normalising (100 %):** 100 % assisting line with an arrowhead and "100%".
- **Adjustment (currency/inflation):** "AC*" with a footnote; inflation share as a light-blue
  segment on top of real values (CH 5.1). No ISO notation yet (UN 4.4).
