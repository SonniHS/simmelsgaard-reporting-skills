---
name: ibcs-deneb
description: >
  Provides a library of Deneb (Vega-Lite) chart templates for Power BI that follow the IBCS®
  Standards, driven by design tokens; use it whenever an IBCS chart in a Power BI report needs
  something core visuals cannot draw (hatched FC, overlapped scenarios, scenario triangles,
  variance axis notation, pins, same-scale tiers, waterfalls), when a visual spec names one of
  these chart types for a Power BI page, or when someone asks for an "IBCS Deneb template".
  Templates: two-tier AC/FC vs PY/PL/BU columns, pin charts, structure bars with variance bars,
  calculation and variance waterfalls, small multiples, scenario lines with trend arrows,
  stacked columns, scatters of two relative measures and forecast-version columns; knobs for
  outlier pins, scale bands, comment markers and a px-per-unit scale shared across visuals.
  Scripts sync tokens, render previews and inject a template into a PBIR visual.json.
---

# IBCS Deneb templates

Status (as of 2026-10): **10 templates done and render-checked** against the IBCS v2.0 figures
(previews in `${CLAUDE_SKILL_DIR}/assets/previews/`). An end-to-end test ran the column and pin
templates in a live-connected report in the Power BI service; not opened in Desktop by this
plugin; see "Not verified".

Deneb mechanics (escaping, interactivity, PBIR files) come from Microsoft's Power BI agent skills
where installed (Deneb visuals, PBIR format). The notation rules come from the `ibcs-notation`
skill (plugin `ibcs`). The templates apply them as follows: relative variance divides by the
**signed** reference and shows `N/A` when it cannot be interpreted; geometry follows the
arithmetic sign, polarity only selects the colour (good / bad / **neutral blue**); FC is hatched
(bars, variance bars, line markers); the variance axis carries the reference scenario's notation
(PY solid light, PL/BU two thin lines).

## Templates (`assets/templates/`)

| File | Visual-spec `type` | IBCS | Preview |
|---|---|---|---|
| `column-two-tier-variance.vl.json` | `grouped-column` (+ triangle tier) + `variance-column` tier (+ `pin-time` tier) | EX 1.1 cards 5, 6, 7, 8; CO 4.2 | `column-two-tier-variance{,-pl,-bu-py-triangle,-scale-group,-scale-band,-comments,-pins,-pins-px,-variance-only,-variance-only-pins}.png` |
| `pin-relative-variance.vl.json` | `pin-time` | card 8; UN 4.1 | `pin-relative-variance{,-pl,-cost,-wide,-outlier}.png` |
| `bar-structure-variance.vl.json` | `bar-triangles` / `grouped-bar` (+ triangle tier) + `variance-bar` tier | cards 23–25; EX 4.2; CO 4.2 | `bar-structure-variance{,-py-overlap,-bu-py-triangle,-scale-band}.png` |
| `waterfall-calculation.vl.json` | `calculation-waterfall` | card 28 | `waterfall-calculation.png` |
| `waterfall-variance.vl.json` | `variance-waterfall-structure` | card 29 | `waterfall-variance{,-scale-band-highlight}.png` |
| `small-multiples-columns.vl.json` | `small-multiples` of `grouped-column` | CO 5.1; CH 4.1 | `small-multiples-columns{,-totals}.png` |
| `line-scenarios.vl.json` | `line` / `line-grouped` | cards 12, 15; UN 3.2 | `line-scenarios{,-trend}.png` |
| `stacked-columns.vl.json` | `stacked-column` | A-2; D9 (scenario on the lowest segment) | `stacked-columns.png` |
| `scatter-relative.vl.json` | `scatter` / `bubble` of two relative measures | A-32 / 33; G5 diagonal + tolerance band | `scatter-relative.png` |
| `column-version-axis.vl.json` | `grouped-column` on a version axis (forecast evolution) | C3; FC per snapshot, ΔFC per version | `column-version-axis.png` |

Fields, knobs and notes per template are in each file's `usermeta.ibcs` and in
[references/templates.md](references/templates.md) (regenerate with
`python3 -I -B "${CLAUDE_SKILL_DIR}/scripts/gen_reference.py"`). Sample data (neutral, invented):
`${CLAUDE_SKILL_DIR}/assets/sample-data/`.

## How a template is built (read before editing one)

- **Tokens, not hex.** Every colour, ratio, stroke, font size and number format is a top-level
  param named `ibcs*`; `scripts/sync_tokens.py` writes their values from the token file
  (`assets/ibcs-tokens.json`, plus your overrides). Never type a colour into a template; add a
  token mapping to `PARAMS` in `sync_tokens.py` instead (maintainers of this plugin only; users
  write a synced copy, see Workflow step 1). Non-token params are **knobs**
  (`refScenario`, `polarity`, `decimals`, …) listed in `usermeta.ibcs.knobs`.
- **Same scale across tiers in ONE view.** Vega-Lite `vconcat` tiers get independent scales, so
  the multi-tier templates draw all tiers in a single layered view on one linear scale; the
  variance tier's baseline is offset in data units. Absolute variances therefore always have the
  same units per pixel as the base values (UN 4.1, CO 4.2). Relative variances (pins) use their
  own % scale.
- **Category width per period type.** Bar width = 2/3 of the band, capped at
  `geometry.categoryStepPx[periodType] × stepScale`, so every chart of a period type on a page has
  the same column width (UN 3.3). Keep `stepScale` identical across a page.
  Exception: the column templates (`column-two-tier-variance`, `stacked-columns`,
  `column-version-axis`) fill 2/3 of their slot (space 1/3), because a Power BI
  visual is usually wider than the token layout and the cap left the columns at a third of their
  slot. For the same width across visuals of one period type, pass the same `barPx`; markers beside
  the columns keep the token size via `tokBw`.
- **FC hatch** uses Deneb's `pbiPatternSVG(ibcsHatch, stripe, ground)`; `ibcsHatch` is the
  built-in `diagonal-stripe-N` closest to the token `pattern.fcHatch.stripeShare` (Deneb's tiles
  are fixed at 10 px, so the token's stripe period cannot be matched exactly). SVG render mode is
  required. Line-chart FC markers are drawn as a hatched symbol path, because a 10 px tile is
  larger than a marker.
- **Scenario codes:** `refScenario` (and `triangleScenario`) name a bound field. `PY` gets the
  PY notation; every other code (`PL`, `BU`, a forecast version used as plan) gets the plan
  notation (outlined, two-line variance axis). Bind a budget as field `BU` and set
  `refScenario=BU`. The combined actual-plus-forecast series is labelled **AC&FC** (notation;
  "AC+FC" in a model's calculation group is the same thing).
- **Third scenario:** `triangleScenario` (e.g. `PY` while `refScenario` is `BU`; tier
  `draw: triangle` in the visual spec) draws triangles at that scenario's values: right-pointing
  left of the columns, down-pointing above the bars (`bar-structure-variance` with `refMark: bar`).
- **One scale across visuals** (UN 4.1, CH 4.1) = the same **px per unit**, with each chart
  sized to its own data (CH 4.2). Set the knob `pxPerUnit` (pins: px per percentage point) or bind
  the optional field `PxPerUnit` (one DAX measure, same value on every row) on every member of the
  scale group: the value domain becomes the plot extent ÷ pxPerUnit, anchored at the baseline, so
  values render at exactly that px per unit. Deneb fills a fixed container, so **the container
  must then be sized to the data**: height (width for bars and waterfalls) = data range ×
  pxPerUnit + the template's fixed px, from `usermeta.ibcs.layout` (`fixedPx`, per tier
  `padHigh` / `padLow` in px). `ibcs-power-bi/scripts/scale_layout.py` computes it. A container
  that is too small makes the data win (smaller px per unit, nothing cut).
  The domain knobs `yMax` / `varMin` / `varMax`, `xMax`, `yMin` (and fields `YMax`, `XMax`,
  `VarMin`, `VarMax`, `YMin`) only share a **domain**: right for visuals of the same size that
  must show the same range, **wrong** for a same-unit scale group with different ranges (a
  smaller chart with the larger chart's max at the same height wastes its plot).
- **Total / extension column:** not part of a template. Put it in a separate visual next to the
  chart (`periodType: year`); when it fits, give it the same `pxPerUnit`. When its base needs its
  own scale (a year next to its months), give it its own `pxPerUnit`: its base **and** its Δ tiers
  use that scale (ibcs-composition), shown by `scaleBand` in both visuals and a footnote. Align it
  with the months by px extent: the same visual top, height and `categoryLabelPx`, and the tier
  ranges from `scale_layout.py` `alignTiers` (knobs `yMax`, `varMin`/`varMax`, `pinMin`/`pinMax`,
  or under filters the fields `YMax`, `VarMin`/`VarMax`, `PinMin`/`PinMax` from union measures,
  `column-two-tier-variance` notes). A tiny Δ on the Total's scale is drawn at its true height with
  its label. `varPxPerUnit` (the Δ tier on the months' scale) remains only for a page that states
  that compromise in a footnote. Bind the year's actual-plus-forecast as `FC` so it is hatched and set
  `fcLabel: AC&FC` for its legend name.
- **Blank categories and unknown members:** every template drops rows whose category field is
  blank, so a constant field (a scale measure such as `PxPerUnit` or `YMax`) cannot add a blank
  "null" category, and rows whose value fields are all blank. An unknown member ('N/A' company,
  "(Blank)" product) still comes back when a constant or text measure (Scenario text, an
  ALLSELECTED total, a segment order, `ShowTotal`) returns a value for it: write those measures to
  return BLANK when the row's data measure is blank (`IF ( NOT ISBLANK ( [AC] ), … )`).
- **Units:** values are drawn as delivered. Bind scaled measures (preferred) or set
  `unitDivisor` (1000, 1000000) so labels never show raw values; the unit goes in the title.
- **Outliers** (UN 5.3, CH 4.4): `pin-relative-variance` knob `clipPct` (or field `ClipPct`)
  cuts a business-irrelevant relative outlier at that value: no head, full label, a small
  triangle beyond the label in the growth direction. Absolute columns and bars are never cut
  (CH 2.1): give them their own scale with a **scale band** instead.
- **Scale band** (CH 4.3): `column-two-tier-variance`, `bar-structure-variance` and
  `waterfall-variance` knob `scaleBand` (or field `ScaleBand`) draws a light area from the axis to
  that value with a labelled line; set the same round value in every chart of the unit whose
  scales differ (`waterfall-calculation` has the same knob).
- **Highlighting ellipse** (UN 5.1): `waterfall-variance` knob `highlight` (the row label) or field
  `Highlight` (1 on that row) circles the value label the key message cites. When the base and
  total bars carry the same label, use the field.
  **A `Highlight` measure that picks the "worst" row must not iterate the axis table under
  `ALLSELECTED`.** A measure of the shape `FILTER ( ADDCOLUMNS ( ALLSELECTED ( 'Date' ), "@d",
  [ΔBU] ), [@d] < 0 )` → `TOPN ( 1, … )` flagged the right month in an *Execute Queries* preview
  but EVERY negative month in the Power BI service (end-to-end test, as of 2026-10). `ALLSELECTED`
  restores a shadow filter context that depends on how the query is wrapped, and the service wraps
  slicer and visual filters differently from a hand-written query. Working pattern: build the
  candidate list as plain axis **values** of the effective period (the same period logic the
  chart's value measure uses), evaluate each candidate with an explicit filter that replaces the
  axis filter, pick one winner with a tie-break, compare:
  ```dax
  VAR __P = <the effective period: a one-column table of 'Date'[Month] values, as the value measure filters>
  VAR __cand = FILTER (
      ADDCOLUMNS ( __P, "@d",
          VAR __m = 'Date'[Month]
          RETURN ROUND ( CALCULATE ( [ΔBU], REMOVEFILTERS ( 'Date' ), 'Date'[Month] = __m ), 1 ) ),
      [@d] < 0 )   -- rounded as labelled, so a label of 0.0 is never "worst"
  VAR __w = MAXX ( TOPN ( 1, __cand, [@d], ASC, 'Date'[Month], ASC ), 'Date'[Month] )
  RETURN IF ( NOT ISBLANK ( [ΔBU] ) && SELECTEDVALUE ( 'Date'[Month] ) = __w, 1 )
  ```
  When the period comes from a slicer on the axis column, read the selection once as a list
  (`CALCULATETABLE ( VALUES ( 'Date'[Month] ), ALLSELECTED ( 'Date' ) )`) and use it as `__P`;
  never evaluate the measure by context transition over `ALLSELECTED` table rows. A structure axis
  works the same way over `VALUES` of its column (e.g. `'Customer'[Customer]`) with
  `REMOVEFILTERS ( 'Customer' )` inside. **Check highlights in the published report**, with and
  without a slicer selection, not only in the preview: exactly one circled label.
- **All tiers of a time chart in ONE visual** (CO 4.2): `column-two-tier-variance` knob `pinTier`
  adds ΔX% pins as a third tier above the absolute variance tier, on their own % scale
  (`pinPxPerUnit` px per percentage point, the same on every pin tier and `pin-relative-variance`
  chart of the page; without it the pins take `pinShare` of the base tier). Prefer it to stacking a
  pin visual on a column visual: separate visuals each anchor their own plot, so when a filter
  shrinks the data under a fixed `pxPerUnit` the base visual's plot drops to its bottom while the
  pin visual stays at its top, and a gap opens between the tiers. In one view the space the data
  does not need stays above the top tier and the tiers never drift apart. `scale_layout.py` sizes
  it with tier `pins` (member params `pinTier`, `pinPxPerUnit`). Outlier clipping (`clipPct`) is
  only in `pin-relative-variance`.
- **Variance-only tier:** `column-two-tier-variance` knob `showBase: false` draws only the
  variance tier (axis, columns, labels, tier name; with `pinTier` a ΔX + ΔX% pair), e.g. a ΔPY tier
  above an AC vs BU chart that already shows ΔBU, so the base is not drawn twice. Size it with
  `scale_layout.py` (no `base` tier) and stack it with `showCategoryLabels: false` when the visual
  below shows the categories; the drift warning above applies to every stacked pair of visuals.
- **Stacked visuals line up:** `column-two-tier-variance` and `pin-relative-variance` use the same
  plot padding (left 40, right 30 px), so a pin or variance-only visual stacked on a column visual
  takes the same x and width; no pixel offset between them.
- **Trend arrow** (UN 5.1): `line-scenarios` knobs `trendArrow`, `trendLabel` (`cagr` / `delta`),
  `polarity`, `trendLiftPx`.
- **Comment markers** (UN 2.4): `column-two-tier-variance` field `Comment` puts a numbered circle
  above that period; repeat the numbers in the comment text.
- **Selective totals** (CO 5.1): `small-multiples-columns` knob `panelTotals` (`all`, `field` with
  `ShowTotal`, or a list of panel names) prints a panel's AC&FC sum on its header line.
- **Small-multiples size:** with `pxPerUnit` the panel height follows the data (`panelHeight` /
  `panelWidth` override, 0 = auto); `scale_layout.py` prints the panel height and, with `panels` and
  `columns`, the visual height. `periodLabel` `month1` prints J F M … under each panel.
- **Period labels:** `column-two-tier-variance` knob `periodLabel` `month` turns `YYYY-MM` into
  Jan … Dec with the year under its first month and a thin year separator (24-month charts);
  `short` prints the month number. The reference name is anchored to the first period that has a
  reference value, so a series starting without PY still names PY.
- **Plan name:** `line-scenarios` knob `planLabel` names the plan line (`BU`, `PL`); the line also
  takes `pxPerUnit`. A trend on a relative measure is printed in pp.
- **Negative structure:** `bar-structure-variance` draws negative values to the left with labels
  outside the bar end; an all-negative structure (a cost variance) needs no extra knob.
- **Scatter highlight:** `scatter-relative` knob `colourMode` `neutral` (default: points outside the
  tolerance band dark, inside grey) or `polarity` (impact colours by polarity, only when good/bad
  is meant).
- **Waterfall input from a model:** `waterfall-variance` accepts one row per element with
  `BaseValue` / `TotalValue` columns (the template adds the base and total bars), besides `Kind`
  rows. `Value` is the element's **contribution** to the total: a cost line in a margin bridge is
  bound as −ΔCost with polarity +1, so the bridge reconciles. `waterfall-calculation` takes the
  same one-row input and `scaleBand`; its notation is unchanged (results and additions grey,
  subtractions dark, unsigned labels).
- **Bridges from separate measures** (a price-volume-mix bridge, a P&L calculation): the model
  returns one row with one measure per element, not one row per element. Bind each measure under
  its own name and fold it into the template's rows with `to_pbir.py --prepend-transform fold.json`:

  ```json
  [
    {"fold": ["GMPY", "Price", "Volume", "Mix", "COSDelta", "GMAC"], "as": ["__key", "__val"]},
    {"calculate": "{'GMPY': 'PY', 'Price': 'Price', 'Volume': 'Volume', 'Mix': 'Mix', 'COSDelta': 'Cost of sales', 'GMAC': 'AC'}[datum.__key]", "as": "Category"},
    {"calculate": "datum.__key == 'GMPY' ? 'base' : datum.__key == 'GMAC' ? 'total' : 'variance'", "as": "Kind"},
    {"calculate": "datum.__key == 'COSDelta' ? -datum.__val : datum.__val", "as": "Value"}
  ]
  ```

  The fold order is the row order. Negate cost elements so `Value` is the contribution (−ΔCOS).
  For `waterfall-calculation` produce `Line` instead of `Category` and the kinds base / delta /
  subtotal / total; subtractions (standard cost, cost variance) are negated the same way. Fields
  named in a prepended `fold` count as bound, so `to_pbir.py` does not warn about them.
- **Pins and triangles are clamped in px** (tokens `geometry.pin.stemPx`, `geometry.pin.headPx`,
  `geometry.triangleSizePx`), so a large `stepScale` widens columns without blowing pins up.
- **`showCategoryLabels: false`** hides the category labels of a tier stacked on another visual
  that already shows them (prefer `pinTier` / one visual where possible, see above).
- **Polarity:** a `Polarity` field per row (1 / −1 / 0) wins over the `polarity` knob.
- **Labels** use `number.format.*.d3` with `decimals` precision; the Deneb config sets the locale
  from the tokens (thousands separator, minus sign, `N/A`). Change locale via token overrides.
- **Interactivity:** tooltips on the main marks. With cross-filtering enabled
  (`to_pbir.py --selection`) no mark is dimmed (a dimmed AC reads like PY): rows with
  `__selected__ == 'on'` get an assisting-area band (`ibcsAssistArea`) behind all marks of their
  category. Filtering stays the preferred interaction.

## Workflow

Run the commands from your project root; `${CLAUDE_SKILL_DIR}` is this skill's directory.

1. Sync tokens. With the IBCS defaults the bundled templates are already in sync. For your
   organisation's palette, locale or fonts, write a synced copy instead of editing the plugin:
   `python3 -I "${CLAUDE_SKILL_DIR}/scripts/sync_tokens.py" --overrides ibcs-tokens.overrides.json
   --out ./deneb-ibcs`
   (`--tokens PATH` for a different token file, `--variant cvd` for a colour-vision-deficiency
   build, `--check` in CI). Use the templates and config from `--out` in the next steps.
2. Pick the template from the visual spec's `type` (in `--out`, or the bundled
   `${CLAUDE_SKILL_DIR}/assets/templates/`); map the model fields to the template's field
   names via `--field` (they become `displayName`s, so the template stays unchanged).
3. `python3 -I "${CLAUDE_SKILL_DIR}/scripts/to_pbir.py" <template> --visual <…/visual.json> --new
   --field "Period=col:Date[Month Short]" --field "AC=m:Measures[AC]" … --param refScenario=PL
   --sort Period --filter "col:Date[Year]=2026" --title "" --report <…/report.json>
   [--config ./deneb-ibcs/config/deneb-config.json]` (registers Deneb in `publicCustomVisuals`).
   Without `--new` it replaces only the spec/config of an existing Deneb visual (and applies
   `--sort`, `--filter`, `--title` if given).
4. Sort order: Deneb keeps the query order, so `--sort` the period / report-line field (a month
   name sorts by its number through the model's "sort by column"); check it in Desktop.
   Report-level measures (`reportExtensions.json`) are bound with `"Schema": "extension"`;
   `to_pbir.py` finds the report's `reportExtensions.json` and does it (`--extensions` to point
   elsewhere). Create the report measures before the visual.
5. Validate: `jq empty` (or `python3 -m json.tool <file> > /dev/null` if jq is not installed), a
   PBIP validator where available, then open in Desktop and compare with the preview PNG.

### Previews (after changing a template)

```sh
VEGA_HOME="$TMPDIR/vega"   # a scratch dir, never a global install
VG=6.4.0; VL=6.4.3          # the Vega / Vega-Lite versions Deneb 2.0 bundles
npm install --prefix "$VEGA_HOME" --no-audit --no-fund --ignore-scripts "vega@$VG" "vega-lite@$VL"
VEGA_HOME="$VEGA_HOME" node "${CLAUDE_SKILL_DIR}/scripts/render-previews.mjs" --png [--out DIR] [template …]
```

**With live data** (after `to_pbir.py`, before or after publishing): query the visual's fields in
the page's filter context with *Execute Queries* (report measures as `DEFINE MEASURE`).
`python3 -I "${CLAUDE_SKILL_DIR}/scripts/visual_query.py" <…/visual.json> --sort-by "Month Short=Month No"
[--filter "'Date'[Year] = 2026"] --body q.json` writes that query (fields, visual filters, sort,
every report measure defined; add slicer/page context with `--filter`: `'T'[Col] = value` and
`'T'[Col] IN {v1, v2}` become `TREATAS ( { … }, 'T'[Col] )` like the service's slicer filters, so
text columns work too; anything else must be a filter table such as `FILTER ( ALL ( 'T'[Col] ), … )`);
run it with
`fab api -A powerbi -X post "groups/<ws>/datasets/<model>/executeQueries" -i q.json > rows.json`, then
`VEGA_HOME="$VEGA_HOME" node "${CLAUDE_SKILL_DIR}/scripts/render-previews.mjs" --visual
<…/visual.json>=<rows.json> [--visual …] --out ./deneb-preview --png`. It decodes the spec and
config from `visual.json`, maps the query columns to the field names Deneb exposes and renders at
the visual's size; several `--visual` pairs give one composite at their page positions (scale
groups, stacked tiers). Rows such as a blank category show up here exactly as in the service.

The renderer emulates Deneb's `dataset`, config, `pbiPatternSVG` and container size, renders SVG
with the Vega version Deneb 2.0 bundles, and screenshots a PNG with headless Chrome (`--chrome
PATH` or `CHROME=…` off macOS). Compare the PNG with the IBCS figure named in the template's
`cards` before committing.

## Not verified / TODO

- Not yet opened in Power BI Desktop / Deneb 2.0: check `pbiPatternSVG` with signal arguments,
  ExprRef scale padding, `scale()` / `height` inside expressions, and the doubled-quote literal
  encoding written by `to_pbir.py` (Desktop may write single quotes undoubled; both should load).
- Small multiples cannot fit the container (Vega-Lite facets ignore `autosize: fit`): the panel
  size is a number in the spec. An outlier panel at double size needs a second visual with the
  same `pxPerUnit` and a taller panel. Its `pxPerUnit` reads Vega-Lite's internal `child_height`
  signal (render-checked with Vega-Lite 6.4.3 only).
- `pinTier`, `showBase: false` and the `waterfall-variance` scale band and highlight are
  render-checked outside Power BI only (previews), not yet in Desktop or the service.
- `pxPerUnit` and `usermeta.ibcs.layout` are render-checked outside Power BI (previews; the
  renderer checks the px per unit of every `pxPerUnit` member); not yet checked in Desktop or at a
  report zoom other than 100 % (`FitToPage` / `FitToWidth` may scale the container but not the px
  pads). The layout's fixed px assume the 12 px label font. Per-side padding exprs
  (`labelWidth`, `labelRoom` on the waterfalls) are not applied by Vega: the label columns are
  measured from the text, so pass their width to `scale_layout.py`.
- Not built: integrated variance (CO 4.1), horizontal variance/growth waterfalls (cards 10/11),
  normalised (100 %) columns and bars, stacked bars, remainder-row gap, outlier markers on
  absolute charts (by design: CH 2.1), index and ranking marks (E16, E17), a structure chart with a Δ% pin tier (card 26;
  route: one SVG table, skeletons 5 + 1 + 2 of `ibcs-svg-dax`), a Total/extension category inside
  a template, a Vega port for web apps.
- Label collision handling is basic: line end labels, stacked-column legends and scatter point
  labels are de-overlapped; value labels inside column and bar charts are not.
- `waterfall-variance` sizes its value axis from 0 (or the base) up: a bridge whose running sum
  falls below zero is cut on the left; use `waterfall-calculation` for results that turn negative.
  Scatter label de-overlap nudges a close group in one direction and can push a label across the
  diagonal band.
