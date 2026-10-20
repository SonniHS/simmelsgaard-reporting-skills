# Inspecting each artefact type

> Companion to the ibcs-review skill. Rule IDs: [checklist.md](checklist.md). Our text, CC BY-SA
> 4.0 (see the repository NOTICE). Read-only throughout.

## Contents
1. Screenshot / PDF page
2. PBIR report folder
3. Power BI theme JSON
4. Vega-Lite / Deneb spec
5. Web / React page
6. Visual spec (YAML)

## 1. Screenshot / PDF page

Open with `Read` (PDF: `pages: "n"`). Work visual by visual, top-left to bottom-right.

- **Header:** key message present? sentence with number + comparison? title three lines (who /
  **what** / when)? filters named? evaluative words?
- **Ink:** list every hue you see and assign a meaning (scenario gray, impact, highlight, scale
  band). A hue without meaning → A5. Blue/orange series, brand colours, rainbow bars → A5/D8.
- **Scenarios:** dark solid = AC, light solid = PY, outlined = PL/BU, hatched = FC. A dashed line,
  a lighter fill or a coloured plan → D6/D7/D8.
- **Geometry estimates:** bar width / category pitch ≈ 0.67 (absolute) or ≈ 0.33 (relative);
  variance bars as thick as base bars; pins thin. Measure in pixels from the image; report the
  estimate ("≈0.45 of pitch") as evidence.
- **Same scale:** for two visuals of one unit, compute px per unit from a labelled bar in each
  (bar length ÷ label value); ratio ≠ 1 (±10 %) → G8, unless a scale band is shown. A chart
  whose tallest mark fills only a fraction of its plot while another chart of the unit fills its
  own (a shared domain max at the same size) is a sizing finding (CH 4.2): the smaller chart
  should be shorter.
- **Zero baseline:** short bars with large labels, labels that do not scale with length → G1.
- **Variance colour:** find a cost/expense measure; is an increase red? Is the bar still drawn
  upward/right (geometry follows sign)? Neutral items blue?
- **Text:** count digits per number (A14), "+" on variances only (B5), date formats (B8), units in
  title not on every label, repeated words (A12), rotated labels (C12).
- **Footer:** sources, timestamp, footnotes (H6, C15).
- Mark as `unverified` what pixels cannot prove (polarity, hatch vs. fine texture at low DPI).

## 2. PBIR report folder

Layout (Power BI Project, enhanced report format):

```
<Name>.Report/
  definition/report.json                     themeCollection.{baseTheme,customTheme}
  definition/pages/pages.json                pageOrder
  definition/pages/<page>/page.json          displayName, width/height, objects.background/outspace
  definition/pages/<page>/visuals/<v>/visual.json
  definition/reportExtensions.json           report-level measures (reports on a shared model)
  StaticResources/RegisteredResources/<theme>.json
```

`reportExtensions.json` → `entities[].measures[]` (`name`, `expression`, `hidden`, `displayFolder`):
`"hidden": true` on a report-level measure breaks every visual that uses it (or a measure that
references it) in the Power BI service — fail it, helpers go in a display folder (LINT); hex
colours in SVG/image measures must be token colours (A5); impact colours on SVG `<text>` need the
contrast-safe `color.variance.*Text` tokens (E6); `ABS()` of a variance is only for a bar or pin
length, never in a relative-variance denominator (E14). The linter checks these four.

In `visual.json` → `visual`:

| JSON path | What to check | IDs |
|---|---|---|
| `visualType` | `pieChart`, `donutChart`, `gauge`, `funnel`, `treemap`, `filledMap`, `shapeMap`, `kpi`; custom visuals by name (radar, gauge, 3D, play axis); `deneb…` → lint its spec | EX 2, G5–G7 |
| `query.queryState.Category.projections[].field` | time field (Date/Calendar entity, Month/Year/Quarter property) in a bar chart → D11; non-time field in a column/line/waterfall chart → D13 check | D11, D13 |
| `query.queryState.*.projections[].nativeQueryRef/displayName` | "Sum of …", "Count of …" → implicit measures, glossary names | A10, B1 |
| `query.queryState.Play` | play axis | A3 |
| `objects.legend[].properties.show` | true on category charts | C10 |
| `objects.valueAxis[].properties.{show,start,end,axisScale,gridlineShow}` | value axis with labels on; range excludes 0 (start > 0 or end < 0); log; gridlines | A8, G1, G2 |
| `objects.categoryAxis[].properties.gridlineShow` | gridlines | A8 |
| `objects.labels[].properties.{show,labelDisplayUnits,labelPrecision}` | labels off; Auto units (0) | A14 |
| `objects.layout[].properties.{clusteredGapOverlaps,clusteredGapSize}` | overlapped scenarios | E3 |
| `objects.dataPoint[]` fill / border by `selector.metadata` | AC #404040-ish, PY light, PL white + border; colour literals vs tokens; conditional fill measure (open its DAX: polarity, three states) | D4–D8, E6 |
| `objects.error[]` | error-bar triangles/pins | E3, E12 |
| `visualContainerObjects.{background,border,dropShadow}` | chrome | A2, A4 |
| `visualContainerObjects.title[].properties.text` | evaluative/obvious words, totals | A10, A11, C7 |
| textbox `objects.general[].properties.paragraphs[].textRuns[].value` | page title lines, key message | C1–C7, H1 |
| `objects.vega[].properties.jsonSpec` (Deneb) | embedded Vega-Lite → §4 | — |

Shared scales: compare `valueAxis.start/end` across visuals of one unit; fx-bound min/max
measures (`expr.Measure`) are good — open the measure to confirm it is shared. Display units
fixed per scale group. In the model (`*.SemanticModel/definition/*.tmdl`) check variance format
strings (`+#,0;-#,0;0`), ΔPY% using `DIVIDE(AC - PY, PY)` (signed, no ABS), polarity attribute,
colour measure returning three states.

## 3. Power BI theme JSON

| Key | Check | IDs |
|---|---|---|
| `dataColors` | grays first (AC, PY, white, stack grays); saturated series colours → A5 | A5, D8 |
| `good`, `bad`, `neutral` | present, equal to effective tokens (`color.variance.*`) or a documented ORG override; three states | E6, E7 |
| `background`, `foreground` | white / black | A2 |
| `textClasses.*.fontFace` | one plain sans-serif | A6 |
| `visualStyles["*"]["*"]` | legend off, gridlines off by default, background/border/dropShadow off, labels on with fixed units | A2, A4, A8, A14, C10 |

## 4. Vega-Lite / Deneb spec

| Path | Check | IDs |
|---|---|---|
| `mark` / `layer[].mark` | `arc` (pie/donut) | EX 2.1 |
| `encoding.{x,y}.scale.zero/domain/type` | zero false, domain excluding 0, log | G1, G2 |
| `encoding.*.axis.labelAngle`, `axis.grid`, `config.axis.grid` | rotation, gridlines | C12, A8 |
| `encoding.color` | nominal field without explicit token range; `scheme`; legend not null (except scatter/bubble) | A5, C10 |
| `encoding.color.condition` / transforms | impact colour from polarity (three states), not from sign; bar geometry from the raw Δ | E6 |
| `scale.paddingInner` / `size.band` | 0.333 abs / 0.667 rel padding | D1, D2 |
| `resolve.scale` in facet/concat | `shared` for same unit | G8 |
| `config.background`, `config.view.stroke` | white; frame off | A2, A4 |
| pattern fills | FC needs SVG/Vega pattern or stripe layer — a plain lighter fill is a deviation | D7 |

## 5. Web / React page

Start from the layout component (header/footer slot) and the page component, then the chart
components. Useful read-only searches (`Grep`, case-insensitive):

| Pattern | Meaning | IDs |
|---|---|---|
| `PieChart\|<Pie\b\|Donut\|arc` | pie/donut | EX 2.1 |
| `Gauge\|RadialBar\|Funnel\|Radar` | replaced chart types | EX 2.2/2.3 |
| `CartesianGrid\|gridLines\|grid:\s*true\|"grid":\s*true` | gridlines | A8 |
| `<Legend\|legend:\s*\{\|"legend":\s*\{` | external legends | C10 |
| `domain=\{\[\s*['"]auto\|zero:\s*false\|scale.*log\|scaleLog` | non-zero / log axes | G1, G2 |
| `#[0-9a-fA-F]{6}\|rgb\(\|hsl\(` outside the token module | hard-coded colours | A5 |
| `schemeCategory\|tableau10\|category10\|interpolate` | categorical palettes | A5 |
| `box-shadow\|drop-shadow\|linear-gradient\|border-radius` on chart containers | chrome | A4 |
| `animation\|transition\|framer-motion\|animate` | motion | A3 |
| `labelAngle\|rotate\(\|angle=` | rotated labels | C12 |
| `Math.abs\(.*(PY\|PL\|prior\|plan)` in variance code | ABS in relative variance | E12, E14 |
| `toLocaleString\|Intl.NumberFormat` | separators, signs, prefixes per tokens | B3–B7 |

Then confirm: one shared domain per unit per page (look for a helper computing domains once),
title component producing three lines from filter state, message component bound to the same
data as the charts, footer with sources and timestamp, tokens imported from the generated token
module rather than literals. Rendering questions → ask for a screenshot.

## 6. Visual spec (YAML)

Validate against the [visual spec format](../../ibcs-composition/references/visual-spec-format.md) §10 (12 rules). Typical
findings: message page without highlights; template message of type explanation; time category
with a bar type; same unit in two visuals but two scale groups; variance without polarity;
top N without remainder; missing sources/asOf; title line 1 without slicer placeholders.
