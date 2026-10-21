---
name: ibcs-notation
description: >
  Provides the notation for business charts, tables and pages that follows the IBCS® Standards
  (ISO 24896), with the bundled design tokens; use it whenever designing, building, styling or
  fixing any business chart, table, KPI card, dashboard, Power BI visual or theme, Vega-Lite spec
  or web/React chart — even without the word IBCS, e.g. "variance chart", "budget vs actual by
  region", "what colour is the forecast", "forecast hatching", "format this P&L matrix".
  Scenarios: Actual (AC) solid dark, Previous year (PY) solid light, Plan (PL) and Budget (BU)
  outlined, Forecast (FC) hatched; patterns, never scenario colours (no "forecast colour").
  Variances ΔPY/ΔPL/ΔPL% and pins with good/bad/neutral colours by business impact; time
  horizontal, structure vertical; 2/3 vs 1/3 bar widths; units and scaling (kEUR, mEUR, max 3
  digits); number/date formats; three-line titles; integrated legends; markers; identical scales
  and the CHECK integrity rules.
---

# IBCS notation (SIMPLIFY · UNIFY · CHECK)

Notation is the semantic layer of a report: **what looks the same means the same**. A reader
who knows the notation recognises actual vs plan, absolute vs relative, good vs bad without
reading a legend. That only works if every visual follows the same rules — treat the rules
below as a contract, not as style suggestions.

Basis: IBCS Standards v2.0 (2026), notation part (SIMPLIFY, UNIFY, CHECK; pp. 16–75), which is
aligned with ISO 24896. This skill is our own condensed restatement, shared under CC BY-SA 4.0
(see the repository NOTICE); it follows the IBCS® Standards and is not certified by IBCS
Institute. Rule IDs (SI/UN/CH x.y) and page numbers refer to IBCS v2.0; a rule index is in
[references/notation-rules.md](references/notation-rules.md).

**Lane:** this skill says *what* the notation is. Page composition (message, storyline,
layout, visual spec) → [ibcs-composition](../ibcs-composition/SKILL.md). Auditing an existing
artefact → [ibcs-review](../ibcs-review/SKILL.md). Building: SVG/React chart components for web
pages → [ibcs-web-charts](../ibcs-web-charts/SKILL.md); Power BI → the `ibcs-power-bi`
(native visuals, theme), `ibcs-deneb` (Deneb/Vega-Lite templates: hatched FC, overlapped
scenarios, triangles, pins, multi-tier same-scale charts, waterfalls) and `ibcs-svg-dax` (SVG
measures in tables) skills of plugin `ibcs-power-bi`; Fabric apps → the `ibcs-fabric-app` skill
(plugin `fabric-apps`). All of them consume the same tokens.

## 0. Tokens first

All concrete values (hex, ratios, line widths, font sizes, format strings, abbreviations) come
from the bundled **`${CLAUDE_SKILL_DIR}/assets/ibcs-tokens.json`** (DTCG format), deep-merged
with the user's own `ibcs-tokens.overrides.json` if the project has one (override wins). Never
hard-code a colour or ratio in a visual; reference the token path. Defaults, for orientation only:

| Role | Token path | Default |
|---|---|---|
| AC fill / dark ink | `color.scenario.ac` | #404040 |
| PY fill | `color.scenario.py` | #A6A6A6 |
| PL/BU fill + outline | `color.scenario.pl.fill` / `.stroke` | #FFFFFF / #404040 |
| FC hatch | `pattern.fcHatch` + `color.scenario.fc.*` | 45° dark stripes, dark outline |
| Good / bad / neutral | `color.variance.good` / `.bad` / `.neutral` | #8CB400 / #FF0000 / #0064FF |
| Tinted variance numbers (text) | `color.variance.goodText` / `.badText` / `.neutralText` | #5A7A00 / #D00000 / #0064FF (≥ 4.5:1) |
| CVD good; B&W good/neutral/bad | `color.variance.cvd.good`; `color.variance.bw.*` | #008E96; #BFBFBF/#808080/#404040 |
| Highlight ellipse, annotation refs | `color.marker.highlight` | #0064FF |
| Scale band | `color.marker.scaleBandFill` | #DCE8FA |
| Bar width abs / rel | `geometry.barWidthRatio.absolute` / `.relative` | 2/3 / 1/3 of category |
| Pin stem / head, triangle (px clamps) | `geometry.pin.stemPx` / `.headPx`, `geometry.triangleSizePx` | 2–4 / 6–10, 6–12 px |

Every token carries a provenance label: `STD` (stated by IBCS), `REC` (IBCS recommendation),
`FIG` (measured from an IBCS figure), `OURS` (our default where IBCS is silent), `ORG` (your
override). `STD` values are requirements; the others may change in the organisation's notation
manual — but then consistently everywhere. Structure, overriding and use from CSS/JS/Power BI:
[references/tokens-in-practice.md](references/tokens-in-practice.md).

## 1. Decide before drawing

For every visual answer these five questions; the answers determine almost everything else.

1. **Category axis — time or structure?** Time (years, quarters, months, days) → horizontal
   category axis: columns, lines, horizontal-axis pins, column waterfalls; tables put periods in
   columns, left → right. Structure (regions, products, accounts, customers) → vertical category
   axis: bars, vertical-axis pins, bar waterfalls; tables put structure in rows. Never lines or
   areas across structure categories. (UN 3.3, UN 3.4; exception: histograms and other
   interval scales.) *IBCS names charts by the category axis*: a "horizontal chart" is a column
   chart.
2. **Measure — absolute or relative?** Absolute (currency, units, counts) → columns/bars 2/3 of
   category width, thick lines. Relative (%, ratio, share) → 1/3 width, thin lines (50 %),
   relative variances as pins. (UN 3.1)
3. **Which scenarios?** AC, PY, PL/BU, FC — each has a fixed notation (§2). Add PL/PY/FC
   whenever they exist (EX 4.1).
4. **Which variances, with which polarity?** ΔPY/ΔPL absolute, ΔPY%/ΔPL% relative; the measure's
   polarity (+1 more is better, −1 less is better, 0 neutral) decides the colour (§3).
5. **Which unit and scale group?** Pick the unit/prefix (§5) and decide which visuals on the page
   share the unit — they must share one scale (§8).

Chart choice itself: [references/chart-catalogue.md](references/chart-catalogue.md) (analysis
type × data shape → chart card A-n); tables: [references/table-catalogue.md](references/table-catalogue.md).

## 2. Scenarios (UN 3.2, UN 4.1)

| Code | Meaning | Columns / bars | Line chart | Table header rule | As variance axis (subtrahend) |
|---|---|---|---|---|---|
| **AC** | Actual (measured) | solid dark | dark line, filled square markers | thick dark | — |
| **PY** | Previous year/period (measured) | solid **light** — only in scenario comparisons | light line/markers | thick light gray | **solid light** thick axis |
| **PL / BU** | Plan / Budget (fictitious) | **outlined**: white fill, dark border | dark line, **hollow** square markers | **double** thin dark line | **two parallel thin lines** |
| **FC** | Forecast (expected) | **hatched** dark stripes + dark outline | dark line, **hatched** markers | hatched | hatched (rare) |

- Scenarios are coded by **fill pattern, never by hue**. A blue plan line or an orange forecast
  is a notation error. In a plain time series, earlier periods are *not* lightened — PY light
  is for comparisons.
- Label measured comparisons **AC / PY**, not "2026 / 2025"; the period goes into title line 3,
  a legend or the header.
- **Order** of scenario columns/bars: different periods ascending in time (PY, FC 2026, PL 2027);
  same period by creation time **PL → FC → AC**. Tables: PY | PL | AC | ΔPY | ΔPY% | ΔPL | ΔPL%.
- **Comparison drawing:** either overlapped grouping (reference behind AC/FC, columns shifted
  left ≈20 % of width, bars shifted up ≈25 %), or **scenario triangles** in the reference
  scenario's notation (columns: right-pointing, at the column's left edge; bars: down-pointing,
  above the bar). A third scenario = triangle on an overlapped pair. AC and FC always in front.
- Stacked/multi-series: scenario notation on the **lowest segment**, upper segments in different
  grays (`color.scenario.stackGrays`), plus outline/hatch if PL/FC; the key series sits on the axis.
- AC months followed by FC months in one series: each column keeps its own notation; series label
  and title line 3 "AC&FC" (data models may name the same series "AC+FC"); a short vertical
  separator on the axis at the change. The switch is the **last closed period** (not the data
  timestamp): the open month already shows FC and its partial AC is not drawn. PY next to FC
  months is the **full** period (never cut like-for-like at the reference date).

## 3. Variances (UN 4.1)

- **Names:** "Δ" + subtrahend: ΔPY = AC−PY, ΔPL = AC−PL (or FC−…); write "AC-PL", "FC-PL" when
  the minuend is ambiguous. Relative: ΔPY% = (AC−PY)/PY×100 with the **signed** reference (never
  ABS). Variance of percentages = **pp** (50 % − 40 % = +10pp); relative variance of percentages
  is ordinary % (+25%).
- **Sign:** every positive variance carries "+" (+13, +13%); nothing else does. A relative
  variance that cannot be interpreted is shown as **N/A** (IBCS v2.0, pp. 53–54). Our operational
  rule (`OURS`): reference ≤ 0 or blank → N/A (PL 100 / AC −20 → −120 % is shown; PL −30 /
  AC −10 → N/A). Δ = 0 → no bar, default text colour. The same holds for a Δ that **rounds to
  zero at the displayed precision** (OURS): book-to-bill +0.0005 at two decimals prints `0.00`
  unsigned, in the default text colour, with no mark — never "+0.00" in green or "-0.0" in red.
- **Shapes:** absolute variances = columns/bars with the **same width and same scale** as the base
  chart (ISO 24896). Relative variances = **pins** on their own % scale (thin body ≈30 % of bar
  thickness, head ≈85 %; a square head is the illustrated default, not a mandate). Ratios give
  absurd sizes on very wide or narrow columns: clamp stem, head and scenario triangles in px
  (`geometry.pin.stemPx`, `.headPx`, `geometry.triangleSizePx`, OURS) in every renderer.
- **Colour = business impact, three states:** desirable bright green, undesirable dark red,
  neutral/ambiguous blue (polarity 0 → blue); a Δ that is 0 or rounds to 0 at the displayed
  decimals gets no colour at all, checked first. IBCS fixes the hues and meanings; only the exact
  codes are an organisational choice. Polarity selects the **colour only** — geometry follows the
  arithmetic sign: a cost increase is drawn up/right *and* red. Never plot Δ × polarity. These are
  *not* traffic lights.
- **Tinted variance numbers** (one rule for web, Power BI and print): a variance number in a
  table or card may carry its impact colour only if that colour meets **4.5:1 text contrast** on
  the background (WCAG 1.4.3) — use the text variants `color.variance.goodText` / `badText` /
  `neutralText` (OURS), never the bright graphic green (2.4:1). Without a contrast-safe variant
  the number stays black (`color.text.primary`) and the bar or pin next to it carries the colour.
  Δ = 0 (also rounded) and N/A are never tinted.
- **Fill = minuend:** AC solid colour, FC hatched colour (with colour outline), PL outlined
  colour. Pin head: solid dark for AC, hatched for FC.
- **Axis = subtrahend:** vs PY a thick solid light axis; vs PL/BU two parallel thin lines.
- **Labels outside**, in the direction of change: positive column → above, negative bar → left.
- Fallbacks (p. 52): colour-vision deficiency → green becomes blue-green, keep good bright / bad
  dark; no colour → good light gray, neutral medium gray, bad dark gray.

## 4. Axes, widths, orientation (UN 3, CH 1)

- Value axes **start at zero**. Only exception: indexed data close to 100 % may zoom, with category
  labels on the 100 % line. Linear axes by default; log only for relative growth across orders of
  magnitude, clearly indicated, and only for an audience familiar with log scales. Histogram
  classes of equal width. No broken/clipped columns or axes.
- Every element labelled → **no value axis, no ticks, no gridlines** — gridlines stay allowed where
  they help (dense charts, small multiples, scatter/bubble). Keep the category baseline.
- Category width grows with period length (year > quarter > month > week > day) and is fixed per
  period type on the page (`geometry.categoryWidthByPeriod`, `geometry.categoryStepPx`).
- Columns/bars/pins in front of the axis line; negative columns put their category label above
  the axis, negative bars put it right of the axis.

## 5. Units, scaling, numbers, dates (UN 1.2, SI 5.2, UN 3.3, UN 4.2)

- ≤ **3 digits in charts, ≤ 4 in tables** — scale with a prefix: monetary lower-case attached to
  the ISO 4217 code (**kEUR, mEUR, bEUR**); physical/SI units k, M, G; counts "#". The unit goes in
  title line 2 or the subtitle, not on every number. One prefix per scale group.
- One organisation-wide format: thousands separator narrow space (`1 234`), one decimal sign, one
  negative style (−123 or (123)).
- **Zero variance (one rule everywhere: charts, tables, KPI cards, messages):** a Δ that rounds to 0
  at the displayed decimals is printed without sign and in the default text colour, with the
  usual decimals (`0.00`, `0.0%`, `0.0pp`), and gets no mark. Every other Δ carries its sign
  ("+" or "−"), taken from the unrounded value. Never `+0.00` or `-0.0`. Codes, not symbols, when currencies mix (EUR, not €). Locale,
  currency and decimal sign are settings in the token overrides, not hard-coded.
- Dates ISO 8601: `2026-06-30`, `2026-Q2`, `2026-06`, `2026-W17`; within a year `Q2`, `Jun`,
  `W17` (year in the title, not repeated on every label — SI 4.3). Spans `Jan..Mar`,
  `2023..2025` (two dots, no blanks). First/last day `.Jun` / `Jun.`. YTD `_Jun 2026`, YTG
  `Jun 2026_`, moving `~Jun 2026` (MAT/MAA), average `Ø`, ranking arrow `sales↓`.
- Decimals are fixed **per scale group**, not per label. An explicit display setting (unit +
  decimals, e.g. a visual spec's `display`) wins over the automatic "≤ 3 digits" scaling rule;
  one-decimal relative variances use `number.format.relativeVariance1` (+5.8%), plain ratios
  that are not percentages (book-to-bill 1.01) `number.format.plainRatio`, their variances the
  same decimals with a sign (+0.03).
- Full date/abbreviation tables: [references/notation-reference.md](references/notation-reference.md).

## 6. Text: titles, legends, labels, annotations, footnotes (UN 2, SI 4)

**Page title = three lines, purely descriptive (ISO 24896); top-left is the general
recommendation — consistency across pages is the rule:**

```
Line 1  WHO   reporting unit + every active filter     ABC Corporation, Europe, top ten clients
Line 2  WHAT  **Measure** in unit (+ by …, sorted …)    **Net sales** in mEUR, by countries
Line 3  WHEN  period(s), then scenario(s)/variance(s)   2026-Q3 AC and PY and ΔPY
```

- Measure **bold**, unit regular. "&" joins scenarios forming one series (`2026 AC&FC`); "and"
  lists parallel scenarios (`AC and PL`). Omit AC if it is the only scenario. > 2 measures → a set
  name ("**Income statement** in kEUR").
- No evaluation in titles ("Strong Q3" belongs in the key message). No "Total", "Sum of", "Full
  year"; no obvious words ("analysis", "overview", "dashboard", "chart", "report", "trend",
  "development", "statistics", "structure").
- Multi-visual pages: shared parts in the page title; differing parts in one-line **subtitles**
  above each visual ("Revenue in mEUR | Sales in SKU"). Title + subtitle always yield who/what/when.
- Small screens may write the three lines in one line with " | ". Hide slicers/controls that
  collide with the title when not in use or when printing.

**Legends and labels:** integrate legends — single series → in the title; stacked columns → left
of the first / right of the last column; stacked bars → centred above the top bar; lines → at the
line end; grouped scenarios → scenario code next to its column. Exceptions: stacked bars may
put legends below the bottom bar instead; two-value-axis charts (scatter/bubble) may use an
external legend next to the symbols. Everything **horizontal**, never rotated (use bars if labels
are long). Data labels next to their element (columns/lines above or below, bars right or left,
stacked segments centred if they fit); omit labels on tiny segments; in dense series label only
first, last, min, max, current. No legend boxes.

**Annotations** sit in the visual or a fixed annotation area, linked by **paired numbered markers**
(①). **Footnotes** at the page bottom: definitions, sources, data timestamp — mandatory in
written reports and dashboards.

## 7. Markers and colours (UN 5, SI 2.2)

- Default ink is **gray**. Colour only with analytical meaning: impact (variances, difference
  markers, trend arrows, outlier triangles), highlight (blue ellipse / one highlighted element the
  message is about), scale bands (light blue). No per-category palettes, no brand-coloured bars,
  no coloured backgrounds, no fills behind numbers, no frames/shadows/3-D/gradients, no decorative
  fonts (one plain sans-serif; bold/italic only for semantics: measure in title, totals).
- **Highlighting ellipse** (blue) around the value the key message refers to.
- **Difference marker**: two parallel assisting lines from the compared columns/bars, a bar
  between them in impact colour, labelled (+12.2).
- **Trend arrow** from first to last period of the trend, head in time direction, impact colour,
  optional "CAGR: 10.8%".
- **Reference arrowhead** (black triangle) for index points ("100%") and benchmarks.
- **Annotation references**: numbered circles, always in pairs.
- **Scale band** and **outlier marker**: §8. Document any further marker in the notation manual.
- Geometry of all markers: [references/notation-reference.md](references/notation-reference.md#4-markers).

## 8. Same scale and visual integrity (CH)

- **Same unit on a page ⇒ identical scale** (same value per pixel) — across separate visuals,
  small multiples, absolute-variance tiers and extended charts (ISO 24896). Relative variances use
  a % scale. In extreme cases different scales are allowed **with scaling markers**. Define a *scale
  group* per unit and compute it once for the whole group from the same filter context.
- **A scale group is defined by px per unit, not by a shared domain.** Each member's plot extent =
  its own data range × px per unit (CH 4.2 size charts to the data): a chart with smaller values
  gets a **shorter** plot. Never align scales by giving a smaller chart the larger chart's domain
  max at the same size; that leaves dead space and hides the small chart's variation. Derive the
  px per unit from the member with the largest range and the extent it may use; if the page then
  cannot fit, use scale bands / scaling markers (CH 4.3) or a magnifying glass (CH 4.5) as below.
- Values differing by orders of magnitude: IBCS offers **size charts to the data**, **scale
  bands** and a **magnifying glass** without ranking them (CH 4.2–4.5). Our default order: 1st
  size the panels (length ∝ max value, enlarge the outsized small multiple), 2nd scale bands (same
  numeric value, e.g. a power of 10, drawn as a light area in every chart), 3rd magnifying glass
  (marked zoom area linked to a zoomed chart). Never independent auto-scaled axes.
- **Full-year total next to months** (an extended category, CO 4.3): the FY value is ~12× a
  month and flattens the months on one scale. In order of preference: (1) leave the absolute FY
  columns out of the chart and show the FY values in the message, a KPI card or a table next to
  it; (2) keep the FY **variances** (ΔBU, ΔBU%) as an extension on the months' variance tiers
  when they fit the same scale; (3) draw the FY columns in their own scale group with a **scale
  band** of the same round value in both groups, a footnote and a recorded deviation (CH 4.1
  "extreme cases"). Never silently auto-scale the Total. Averages (Ø) and single reference
  values are comparable with a month and stay on the months' scale.
- **Outlier markers** only for business-irrelevant outliers in relative values/variances: pin
  truncated at the plot edge, no head, full value labelled, small triangle in growth direction
  (impact colour).
- Areas encode values by **area** (bubbles), never by diameter or icon height; no 3-D volumes;
  prefer bars. Filled maps only for area-related measures (densities); otherwise bars or symbols of
  one scale on the map.
- Long time series: show inflation or currency effects where they distort (AC* + footnote).
- Replace pies/donuts (sorted bars, 100 % stacked columns), gauges (variance columns over time),
  radar/funnel (bars side by side; conversion-rate line), spaghetti > 3–4 lines (small multiples),
  traffic lights for > 3 states (variance bars). (EX 2)

## 9. Tables in one paragraph (SI 3.2, UN 3.2, EX 1.2)

Time, scenarios and variances in **columns**; structure and measures in rows. Numbers and their
headers right-aligned, text left; no vertical rules — narrow gaps between columns of a type,
wider gaps between groups. Scenario columns underlined in their notation (AC thick dark, PY thick
light, PL double, FC hatched). Totals/results **bold** below their children (or right of their
columns) with a solid line above, optionally on a light-gray fill; remainder row ("Other", "Rest
of …") last before the total, excluded from ranks and averages. "Of which" rows/columns smaller
and not summed. Variance columns may embed table bars/pins on the same scale. ≤ 4 digits per
cell. Column, row and table types: [references/table-catalogue.md](references/table-catalogue.md).

## 10. Self-check before you hand over

Run the checklist of the [ibcs-review](../ibcs-review/SKILL.md) skill (IDs A1–K9). The
must-items that most often fail: no zero baseline (G1), independent scales for the same unit
(G8), scenario by hue (D8), variance colour by sign instead of impact (E6), variance bars not on
the base scale (E5), time on a vertical axis / structure on a horizontal axis (D11/D13), long
numbers (A14), missing title lines (C3–C5), decorative colour (A5).

## References in this skill

- [references/notation-reference.md](references/notation-reference.md) — detailed tables:
  scenario rendering geometry, variance chart anatomy, marker specs, label positions, date and
  abbreviation catalogue, table notation. Read when building a specific element.
- [references/tokens-in-practice.md](references/tokens-in-practice.md) — token file structure,
  provenance labels, overriding, and use from CSS, JavaScript, Vega-Lite and Power BI.
- [references/notation-rules.md](references/notation-rules.md) — rule index SI/UN/CH with pages
  and a one-line summary each; read when you need to cite a rule.
- [references/chart-catalogue.md](references/chart-catalogue.md) — chart cards A-1…A-35, chart
  selection matrix, "replace X with Y".
- [references/table-catalogue.md](references/table-catalogue.md) — table column, row and table
  types (B cards).
- [references/glossary.md](references/glossary.md) — IBCS terms in short.
- `${CLAUDE_SKILL_DIR}/assets/ibcs-tokens.json` (canonical tokens) and
  `${CLAUDE_SKILL_DIR}/assets/ibcs-tokens.overrides.example.json`.
- `${CLAUDE_SKILL_DIR}/scripts/gen_tokens.mjs` — writes the effective tokens (base + overrides,
  aliases resolved) as a TypeScript, JSON or CSS module for web apps:
  `node "${CLAUDE_SKILL_DIR}/scripts/gen_tokens.mjs" --out src/ibcs/tokens.generated.ts`.
