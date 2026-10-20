# IBCS chart/table type → Power BI route, with visual.json properties

Property names were checked against the Power BI report theme schema 2.157 object definitions
(as of 2026-10; `visual.json` `objects` use the same object/property names). Values in
`visual.json` are PBIR literals (`'text'`, `true`, `25D`, `'#404040'`). Colours shown as
`{color.…}` are token paths: write the value from your effective tokens (bundled
`ibcs-tokens.json` plus your overrides), never a freely typed hex. **Not yet verified in
Desktop**: author one visual in Desktop, compare its JSON, then reuse. The slicer, text box,
`tableEx` and interaction JSON in [pbir-skeleton.md](pbir-skeleton.md) §9 rendered in the service.
A measure in these recipes that is a report-level measure needs `"Schema": "extension"` in its
`SourceRef` ([pbir-skeleton.md](pbir-skeleton.md) §5).

Card numbers ("card 5") are the chart cards of the IBCS chart overview, EX 1.1.

## Contents
1. Decision table
2. What core visuals can and cannot do
3. Native recipes (overlap, PL outline, colour measure, scale, small multiples, lines, triangles)
4. Tables and matrices
5. Deneb and SVG hand-offs
6. Certified visuals and licensing

## 1. Decision table

| Card / spec `type` | Native | Deneb | SVG-in-DAX | Certified | **Pick** |
|---|---|---|---|---|---|
| card 1 `column` | full | — | — | — | native `columnChart` |
| card 5 `grouped-column`, AC vs PY | full (overlap) | `column-two-tier-variance` | card/button only | yes | native unless FC periods |
| card 5, AC vs PL | full (PL outline via `dataPoint` border) | yes | — | yes | native unless FC |
| card 6 `column-triangles` | ✗ (error-bar triangle points up, centred) | yes | — | yes | Deneb |
| card 7 `variance-column` | full (colour measure) | tier in `column-two-tier-variance`; alone or as a second variance tier: `showBase: false` | — | yes | native alone; Deneb as a tier |
| card 8 `pin-time` | ~ (error-bar workaround, no N/A, no head notation) | `pin-relative-variance`; as a tier of a column chart: `column-two-tier-variance` `pinTier: true` | — | yes | Deneb; pins above columns in the same visual (`pinTier`) |
| cards 12/15 `line`, `line-grouped` | AC/PY full; hatched FC / hollow PL markers ✗ | `line-scenarios` | — | yes | native without FC/PL, else Deneb |
| card 19 `bar` | full | — | yes | — | native `barChart` |
| card 23 `grouped-bar` | full (overlap) | `bar-structure-variance` (`refMark: bar`) | very good | yes | native / SVG in a table |
| card 24 `bar-triangles` | ✗ | `bar-structure-variance` | very good | yes | Deneb (chart) / SVG (table) |
| card 23 + third scenario as triangle (AC vs BU, PY triangle; tier `draw: triangle`) | ✗ | `bar-structure-variance` `refMark: bar`, `triangleScenario: PY` (column chart: `column-two-tier-variance`) | very good (skeleton 5) | yes | Deneb (chart) / SVG (table) |
| card 25 `variance-bar` | full | tier | very good | yes | native alone; Deneb/SVG as a tier |
| card 26 `pin-structure`; a structure chart with a Δ% pin tier (bars + ΔBU + ΔBU%) | ✗ (no head) | not built (no structure pin template) | excellent | yes | **SVG table**: category column + **one** SVG measure per row holding all tiers (skeletons 5 bars + 1 Δ bars + 2 Δ% pins in one GEOM block, [svg-skeletons](../../ibcs-svg-dax/references/svg-skeletons.md)) + a static header image with the tier names and legend; not one SVG column per tier, because a table's image columns share `imageWidth`. Image column ≥ SVG width + 20 px. tableEx JSON in [pbir-skeleton.md](pbir-skeleton.md) §9 |
| card 28 `calculation-waterfall` | ✗ (column-only, one total) | `waterfall-calculation` | good | yes | Deneb |
| card 29 `variance-waterfall-structure` | ✗ (wrong orientation, colours by sign) | `waterfall-variance` | good | yes | Deneb |
| A-2 `stacked-column` (scenario on the lowest segment, grays above, D9) | ~ (stacked column; no hatch, no per-segment scenario) | `stacked-columns` | — | yes | native for AC-only; Deneb with FC/PL |
| A-32/33 `scatter` / `bubble` of two relative measures (G5 diagonal, tolerance band) | ~ (scatter, no diagonal/band; analytics line only for a constant) | `scatter-relative` | — | yes | Deneb |
| forecast evolution: columns on a version axis with ΔFC per version | ✗ (no hatch, no per-category scenario) | `column-version-axis` | — | yes | Deneb |
| budget progress (BAC outlined, AC to date, budget-to-date tick) | ~ (bullet-like overlap) | — | skeleton 6 | yes | SVG in a table |
| CO 4.2 multi-tier | ~ (separate aligned visuals + shared scale measure) | yes, one scale guaranteed; base + ΔX + ΔX% pins in ONE visual (`column-two-tier-variance` `pinTier`) | — | yes | Deneb, all tiers in one visual |
| CO 5.1 `small-multiples` | full (shared axis) | `small-multiples-columns` | — | yes | native unless FC |
| `table-variance` (EX 1.2) | matrix + calculation group | — | variance bars, pins | yes | matrix + SVG |
| `table-time` (EX 1.2) | matrix | — | sparklines (indexed) | yes | matrix |
| `kpi-cards` (B-T-KPI) | ~ (new card, no polarity colouring per measure) | — | KPI card (skeleton 4) | yes (cards) | SVG cards in one `tableEx` (JSON: [pbir-skeleton.md](pbir-skeleton.md) §9) |
| statement with write-back, or certification required | — | — | — | Inforiver / Zebra BI / Fabric Planning | certified |

## 2. What core visuals can and cannot do (as of 2026-10)

| IBCS element | Native? | How / workaround |
|---|---|---|
| AC solid dark, PY solid light | yes | two measures on a clustered column/bar; series colours from theme or `dataPoint` |
| AC in front of PY, offset overlap | yes | `layout.clusteredGapOverlaps`, offset via `clusteredGapSize`; AC is the **last** measure (drawn in front); `clusteredGapOverlapReverse` flips the order |
| PL / BU outlined | yes | PL series: fill = PL fill token, `borderShow`, `borderColor`, `borderSize` |
| FC hatched | **no** | no pattern fills in core visuals. A mid-grey FC with a border is a common compromise but not IBCS: footnote it, or use Deneb / SVG |
| Scenario triangles | partly | error bars with upper = lower = reference and a triangle marker; points up only, centred on the column |
| Absolute variance columns by impact colour | yes | separate visual on `[ΔPY]`, `dataPoint.fill` bound to a colour measure |
| Relative variance pins | partly | column chart of `[ΔPY%]` with transparent fill plus error bars from 0 to value; no N/A, no head notation; SVG or Deneb are cleaner |
| Variance on the same scale as the base chart | partly | identical value-axis `start`/`end` across visuals through an fx scale measure |
| Variance axis notation (PY solid light, PL double line) | **no** | Deneb or SVG, or footnote |
| Integrated variance | **no** | Deneb or a certified visual |
| P&L vertical waterfall with subtotals | partly | native waterfall has breakdown and totals but no scenario notation or polarity |
| Small multiples on an identical scale | yes | shared axis is the default; keep independent axes off |
| Signed data labels (`+13`) | yes | format string `+#,0;-#,0;0` (dynamic format strings or calculation-group format expressions). A value that rounds to 0 (0.004 at 2 decimals) still takes the + or − section (`+0.00`): for the zero-variance rule use a dynamic format string `IF ( ROUND ( SELECTEDMEASURE (), 2 ) = 0, "0.00", "+#,0.00;-#,0.00;0.00" )` |
| Variance bars inside a matrix | simple only | conditional-formatting data bars: each column scales on its own, no reference axis notation; strict IBCS needs SVG |
| Sparklines in a matrix | basic | no scenario coding; hatched FC needs SVG |
| KPI card with ΔPY / ΔPY% (`kpi-cards`) | partly | the new card (`cardVisual`) shows reference labels coloured from theme `good`/`bad`, but not by polarity per measure, without the rounded-zero rule and with no fixed layout for several comparisons. **Route: SVG KPI cards** in one `tableEx` (ibcs-svg-dax skeleton 4); the new card only as a footnoted compromise |
| Title who / what / when | yes | text box or dynamic title measure (UN 2.2) |

**Visual calculations** (GA as of 2026-10) add per-visual variance logic without growing the
model: `ΔPY = [AC] - [PY]`, `ΔPY% = DIVIDE([AC] - [PY], [PY])` (signed reference; show N/A when
the reference is ≤ 0), `RUNNINGSUM([ΔPL])` for a bridge. Keep **reusable** variances in the model
(a calculation group): a visual calculation exists only in its visual.

## 3. Native recipes

### Overlapped AC vs PY / PL (cards 5, 23)

`clusteredColumnChart` (time) or `clusteredBarChart` (structure). Measures in the Y/X well in the
order **reference first, AC last** (the last series is drawn in front).

```json
"objects": {
  "layout": [{ "properties": {
    "clusteredGapOverlaps": { "expr": { "Literal": { "Value": "true" } } },
    "clusteredGapSize":     { "expr": { "Literal": { "Value": "20D" } } } } }],
  "categoryAxis": [{ "properties": {
    "innerPadding": { "expr": { "Literal": { "Value": "33L" } } } } }],
  "dataPoint": [
    { "selector": { "metadata": "Measures.PY" },
      "properties": { "fill": { "solid": { "color": { "expr": { "Literal": { "Value": "'{color.scenario.py}'" } } } } } } },
    { "selector": { "metadata": "Measures.PL" },
      "properties": {
        "fill":        { "solid": { "color": { "expr": { "Literal": { "Value": "'{color.scenario.pl.fill}'" } } } } },
        "borderShow":  { "expr": { "Literal": { "Value": "true" } } },
        "borderColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'{color.scenario.pl.stroke}'" } } } } },
        "borderSize":  { "expr": { "Literal": { "Value": "1D" } } } } },
    { "selector": { "metadata": "Measures.AC" },
      "properties": { "fill": { "solid": { "color": { "expr": { "Literal": { "Value": "'{color.scenario.ac}'" } } } } } } }
  ],
  "labels": [{ "selector": { "metadata": "Measures.AC" },
               "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }]
}
```

`clusteredGapSize` = `geometry.referenceOffsetRatio.column × 100` (20) or `.bar` (25); the
generated theme already sets these defaults. `innerPadding` = `(1 − barWidthRatio.absolute) × 100`
(33). Check which literal suffix Desktop writes for `innerPadding` (`L` integer or `D` double) and
copy it. Show labels for AC only; series names as an integrated legend need a text box or Deneb
(the legend is off).

### Variance colour by polarity (cards 7, 25)

A model measure with three states, colours from the tokens:

```dax
ΔPY Color =
VAR _ac = [AC]
VAR _py = [PY]
VAR _p = SELECTEDVALUE ( 'Account'[Polarity], 1 )      -- 1 = higher is better, -1 = lower is better, 0 = neutral
RETURN SWITCH ( TRUE (),
    ISBLANK ( _ac ) || ISBLANK ( _py ), BLANK (),       -- both operands needed: a BLANK AC is no variance
    _ac = _py, BLANK (),                                -- Δ = 0: no impact colour
    _p = 0, "{color.variance.neutral}",
    ( _ac - _py ) * _p > 0, "{color.variance.good}", "{color.variance.bad}" )
```

Bind it with a `Measure` expression and a wildcard selector:

```json
"dataPoint": [
  { "properties": { "fill": { "solid": { "color": { "expr": {
      "Measure": { "Expression": { "SourceRef": { "Entity": "Measures" } }, "Property": "ΔPY Color" } } } } } },
    "selector": { "data": [ { "dataViewWildcard": { "matchingOption": 1 } } ] } }
]
```

Plot `[ΔPY]` itself (arithmetic sign), never `[ΔPY] * polarity`. Format string
`+#,0.0;-#,0.0;0.0` (token `number.format.variance.excel`); for values that round to 0 the dynamic
format string of the row above (zero-variance rule: unsigned `0.0`, ibcs-notation). The variance axis notation is not
available natively: footnote it or use the Deneb tier.

### Same scale across visuals (UN 4.1, CH 4.1)

Same scale means the same px per unit, not the same start and not the same max. Deneb and SVG
members get one px per unit (`pxPerUnit` / the SVG scale input) and each visual is sized to its
own range: `scripts/scale_layout.py` turns the members' ranges into container sizes for
`to_pbir.py --pos` (or `position.height` / `width` in `visual.json`), so a chart with smaller
values is shorter instead of showing a larger chart's max over an empty plot (CH 4.2).

Native charts cannot size their plot to the data, so their fallback is the same span
(`end − start`) at the same plot height, each chart starting at its own minimum so negative
variances are not cut off. That is right for tiers of one chart (equal heights by design); for
native members of very different range give the smaller one a proportionally shorter visual
(height ≈ span × px per unit + the visual's own chrome, checked by eye) or use Deneb.

```dax
Scale Min AC  = MIN ( 0, MINX ( ALLSELECTED ( 'Date'[Month] ), MIN ( [AC], [PY] ) ) )
Scale Max AC  = MAX ( 0, MAXX ( ALLSELECTED ( 'Date'[Month] ), MAX ( [AC], [PY] ) ) )
Scale Min ΔPY = MIN ( 0, MINX ( ALLSELECTED ( 'Date'[Month] ), [ΔPY] ) )
Scale Max ΔPY = MAX ( 0, MAXX ( ALLSELECTED ( 'Date'[Month] ), [ΔPY] ) )
Scale Span    = MAX ( [Scale Max AC] - [Scale Min AC], [Scale Max ΔPY] - [Scale Min ΔPY] ) * 1.15
```

Bind with fx: the AC/PY chart `valueAxis.start` = `[Scale Min AC]` (0 for positive data),
`valueAxis.end` = `[Scale Min AC] + [Scale Span]`; the absolute-variance chart
`valueAxis.start` = `[Scale Min ΔPY]`, `valueAxis.end` = `[Scale Min ΔPY] + [Scale Span]`. Give
both visuals the same plot height. Relative variances are on their own % scale.

### Query roles of the native charts (visual.json `query.queryState`)

Verified in the service (test report, 2026-10): the well names in visual.json are not the names
shown in the field pane.

| Visual (`visualType`) | Category / axis | Values | Legend | Small multiples |
|---|---|---|---|---|
| `clusteredColumnChart`, `columnChart`, `barChart`, `clusteredBarChart` | `Category` | `Y` | `Series` | `Rows` |
| `lineChart` | `Category` | `Y` | `Series` | `Rows` |
| `tableEx` | `Values` (columns and measures, in order) | | | |
| `pivotTable` (matrix) | `Rows` | `Values` | | (`Columns` = column headers) |

Each projection needs `field`, `queryRef` (`Table.Column`, `_Measures.Name`) and
`nativeQueryRef`; a report-level measure needs `"Schema": "extension"` in its `SourceRef`
(`report_measures.py --fix` adds it). Never set `"active": true` except on slicers and drill
hierarchy levels.

A `tableEx` `sortDefinition` works only on a field that is projected in `Values`: a sort on a
measure the table does not show is silently ignored and the rows come back alphabetically (found
in an end-to-end test, as of 2026-10). Sort by a projected measure, e.g. the SVG measure with its
embedded numeric sort key ([pbir-skeleton.md](pbir-skeleton.md) §9).

### Small multiples (CO 5.1)

Column, bar or line with the `Rows` role; keep `valueAxis.sharedAxis = true` (never independent
axes) and fix the grid in `smallMultiplesLayout` (`rowCount`, `columnCount`; rows × columns ≥
panels, so nothing scrolls). Size the visual for the panels, the test report's six panels in one
row of 1 280 px were squashed into the top third and scrolled: each panel needs about 120 px of
height plus its header and axis (visual height ≈ rows × 150 px) and about 46 px per category
for three-letter month labels (width ≈ columns × categories × 46 px; measured in the service:
labels rotate below ~27 px per category and are horizontal from ~46 px). One-letter labels
(J F M …) need about 20 px. Bind a short label column so the axis never rotates; with more
categories than fit, use Deneb `small-multiples-columns`
(one px per unit, `panelHeight`) instead. At most ~25 panels; a Top-N + "Others" member needs an
Others row in the model (a calculated table or a disconnected category with a measure), which a
live-connected report cannot add. Gridlines are allowed here. The layout values above are a
starting point: check them in the service (PDF export, `pbir-skeleton.md` §10).

Turn the data labels on (IBCS charts label values instead of relying on an axis); in
`visual.objects`:

```json
"labels": [{"properties": {
  "show": {"expr": {"Literal": {"Value": "true"}}},
  "labelDisplayUnits": {"expr": {"Literal": {"Value": "1D"}}},
  "labelPrecision": {"expr": {"Literal": {"Value": "0L"}}}
}}]
```

Keep the display units at 1 when the measure already returns the page unit (mEUR), so labels stay
at ≤ 3 digits; with crowded panels show only the last value or the panel total in the header.

### Titles of native visuals

The title rule (UN 2.2) applies to every visual: **measure** in **unit** by **dimension**,
scenarios, e.g. "Revenue in mEUR by business unit, AC" (bold measure via the theme's title font or
a text box above the visual). The unit is never left out, also when the page title names it.

### Lines (cards 12, 15)

`lineChart`: the theme gives `lineStyles.strokeWidth` (absolute measures), `showMarker`,
`markerShape square`, and `seriesLabels.show` (names at the line end). Per series: PY
`strokeColor` / `markerColor` = `{color.scenario.py}`. Hollow PL markers and hatched FC markers
are not reliably available: use Deneb. Relative measures: `strokeWidth` = `stroke.line.relativePx`.

### Error-bar triangles (compromise only)

`error` object on the AC series (metadata selector): `enabled`, `barShow false`,
`markerShow true`, `markerShape 'triangle'`, `markerSize`; upper = lower = the reference measure
(data-bound: author once in Desktop and copy the JSON). The marker points up and sits centred on
the column, which is not the IBCS triangle (card 6). Footnote it, or use Deneb.

## 4. Tables and matrices (EX 1.2, CO 4.4)

See [matrix.md](matrix.md) for the element-by-element mapping.

- `pivotTable` with scenario measures in columns in the order PY · PL · AC │ ΔPY · ΔPY% │ ΔPL ·
  ΔPL% (variance calculation group in the model). The theme sets light row rules, no banding,
  bold totals, subtotals at the bottom, non-stepped row headers.
- Scenario header rules (thick light under PY, thick dark under AC, double under PL, hatched under
  FC) are not native: SVG header measures ([ibcs-svg-dax](../../ibcs-svg-dax/SKILL.md)) or a footnote.
- Variance columns as chart components: SVG measures; native data bars only with minimum 0, a
  common maximum and a footnote about the missing axis notation.
- A light-grey fill on totals rows/columns is allowed (token `color.table.totalFill`).
- Δ% cells: N/A where the reference is ≤ 0 (signed reference, UN 4.1).

## 5. Deneb and SVG hand-offs

- Deneb: [ibcs-deneb](../../ibcs-deneb/SKILL.md) and its `to_pbir.py` script (spec + config into
  `visual.json`, Deneb registered in `report.json` `publicCustomVisuals`, SVG render mode for
  hatching).
- SVG: [ibcs-svg-dax](../../ibcs-svg-dax/SKILL.md) (skeletons; or the community PowerofBI.IBCS
  DAX library; check its licence before use).

## 6. Certified visuals and licensing (as of 2026-10; confirm with the vendor, terms change)

| Option | Licensing model | Fit | Watch out |
|---|---|---|---|
| Zebra BI Charts / Tables / Cards | every builder **and every viewer** licensed (tiers by user count) | finance teams, fast | cost at broad distribution; opaque config |
| Inforiver Analytics+ / Reporting Matrix | per creator, domain-wide options | P&L matrices, write-back | pricing model changes; opaque config |
| Fabric Planning (planning sheets) | Fabric capacity consumption per active session, viewers included | first-party, write-back | a separate item type: not mixable with PBIR pages |
| other certified tools (e.g. graphomate) | quoted | mixed BI estates | watermark until licensed |

Before choosing any custom or certified visual, check: the tenant admin allows it; it works in
your embedding mode; PDF/PowerPoint export and subscriptions render it; you accept an opaque
configuration blob in Git. IBCS certification status of a product is listed on ibcs.com.
