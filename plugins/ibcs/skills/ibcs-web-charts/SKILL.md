---
name: ibcs-web-charts
description: >
  Builds or reviews business charts and tables in a browser app (React + SVG, or D3, Vega-Lite,
  ECharts, visx, Recharts) so that they follow the IBCS® Standards; use it whenever someone writes
  or reviews chart or table code for management reporting in a web app — variance charts, bridges,
  AC vs PL/PY/FC columns, P&L tables, KPI cards, small multiples — even if they do not say "IBCS",
  and before accepting a generic chart library's defaults. Gives the behaviour contract any
  implementation must meet: the tidy data shape per chart type, number and date formatting with
  Intl (one scaling prefix per visual, signed variances, N/A, pp), one scale per unit across a
  page, scenario notation in SVG (AC solid, PY light, PL outlined, FC hatched), variance charts
  with three impact colours by polarity, pins, triangles, waterfalls, small multiples, labels,
  accessibility, phone and print layouts, and how to test it.
---

# IBCS charts in web apps — the behaviour contract

This skill is the **browser implementation** layer. The notation itself (what AC, PY, PL, FC
look like and why) is in the [ibcs-notation](../ibcs-notation/SKILL.md) skill; page layout and
the visual spec are in [ibcs-composition](../ibcs-composition/SKILL.md); checking a finished page
is [ibcs-review](../ibcs-review/SKILL.md).

It does not ship a chart library. It describes **what a conforming chart component does**, so
you can build one with any React/SVG stack or bend an existing library into shape. All colours,
widths and patterns come from the token file
`${CLAUDE_SKILL_DIR}/../ibcs-notation/assets/ibcs-tokens.json` (users override in their own
`ibcs-tokens.overrides.json`); never retype a hex.

> Follows the IBCS® Standards v2.0. IBCS-derived rules are summarised in our own words and shared
> under CC BY-SA 4.0 (see NOTICE). Provenance labels: STD = stated by IBCS, REC = IBCS
> recommendation, FIG = measured from an IBCS figure, OURS = our default.

## 1. Pick the rendering route

| Situation | Route |
|---|---|
| React/Vue/Svelte app, you own the code | Hand-written SVG components driven by pure layout functions (§8). Best control over notation, scales and accessibility. |
| Host or existing codebase uses Vega-Lite | Vega-Lite with the **SVG renderer** (pattern fills need it); compute shared scales up front. See `references/geometry-and-porting.md`. |
| D3, visx, ECharts, Recharts, Nivo | Port the geometry rules; switch off every default listed in §9. |
| Large lookup grids (sorting, paging, thousands of rows) | A data grid is fine — it is not a variance table. Anything with scenario or variance columns follows §6. |
| Pie, donut, gauge, radar, funnel, traffic lights, 3-D | Don't. Replace with bars, columns or a table (IBCS v2.0, EX 2). |

If you evaluate a third-party "IBCS" component library, test it against this contract (§9 and
`references/geometry-and-porting.md`, "Evaluating a library") rather than its own marketing.

## 2. Chart types and the data each one takes

Compute scenarios, variances and impact **in the data model** (DAX, SQL); the browser only
shapes and draws. Every shape carries **raw** numbers (EUR, not mEUR; fractions for percentages)
and `null` for "no value". Full field lists and edge cases: `references/behaviour-contract.md`.

| IBCS chart (IBCS v2.0 EX 1.1 / EX 1.2) | Data shape |
|---|---|
| Column chart over time, with an overlapped reference (PY/PL/BU/FC) or reference triangles | **Period rows**: `period`, optional second label line (year), one number per scenario (`AC`, `FC`, `PY`, `PL`, `BU`) |
| Variance columns (ΔPY, ΔPL) and vertical pins (ΔPY%) | **Variance rows**: `category`, `value` (absolute raw, or relative as a fraction, `null` = N/A), minuend scenario, optional `impact` (−1/0/+1) |
| Bar chart by structure (countries, products) with variance tiers | **Structure rows**: `category`, scenarios, optional model variances per tier, `impact`, flags for remainder ("Other") and total |
| Calculation waterfall (P&L) | **Calculation rows**: `label`, `kind` (base / delta / subtotal / total), **signed** `value` |
| Variance waterfall (bridge PY → AC) | `base` (scenario + value), `steps` (label, signed delta, impact), `total` |
| Line chart | Period rows; the AC&FC series switches from AC to FC after the last closed period |
| Small multiples | A list of panels, each with its own period or structure rows, **one shared scale** |
| Variance table, time-series table, statement (P&L) | **Table rows**: `id`, `label`, `kind` (detail / subtotal / total / remainder / of-which / ratio), `level`, values per column key, `polarity`, `impacts` |
| KPI cards (visual-spec type `kpi-cards`, a transposed variance table) | **Measure rows**: label, unit, AC value, decimals/format, a list of variances (scenario code, absolute, relative, polarity or impact), optional monthly series |

AC&FC from a model usually arrives as one value column plus an "is closed period" flag: split it
into AC (closed, solid) and FC (open, hatched) when shaping the rows. The switch is the **last
closed period**, not the data timestamp: the open month is drawn as FC and its partial AC is
dropped; PY next to FC months is the full period (not cut like-for-like). Label the series
"AC&FC" (a model may call it "AC+FC").

## 3. Variance arithmetic and colour (the rules that keep web and BI tools in agreement)

- **Absolute variance** = minuend − reference (AC − PL, AC − PY, FC − PL).
- **Relative variance** = (minuend − reference) / reference with the **signed** reference; never
  divide by `ABS(reference)`. A reference ≤ 0 is not interpretable (OURS, our operational form of
  IBCS v2.0, UN 4.1, p. 54, which marks uninterpretable results N/A): `null`, printed **N/A**,
  no pin drawn, label kept visible. Optional house rule (OURS): also N/A when the reference
  prints as 0 at the table's decimals.
- **Percentage points** for variances of ratios (margin AC − margin PL): label `+2.1pp`; drawn on
  the `"%"` scale so 1 pp is as long as 1 %.
- **Polarity selects the colour only** (IBCS v2.0, UN 4.1). Geometry follows the arithmetic
  sign: a cost increase still points up/right — in red. Never plot `Δ × polarity`.
- **Three impact states** (STD): good = bright green, bad = red, neutral or ambiguous (polarity 0)
  = blue. Tokens `color.variance.{good,bad,neutral}`, plus a `cvd` set (green → blue-green) and a
  `bw` set (greys).
- Prefer the model's **Impact** column (−1/0/+1 per row and variance) over a polarity hard-coded
  in the app; fall back to `sign(Δ) × polarity`.
- **Δ = 0** draws no mark and no colour; its label `0` is unsigned and black. The same for a Δ
  that **rounds to zero** at the visual's factor and decimals (`+0.0005` at two decimals → `0.00`).
- Non-finite values (NaN, ±∞) are missing: no mark, lines break, the component warns.
- `null` stays `null` end to end. Fill missing periods from the dimension list; never `+ 0` in
  the query to force rows.

For the DAX side of this contract (one query per card, Impact column, BLANK handling), the
`semantic-model-ibcs` skill (plugin `reporting-data`) has the matching patterns.

## 4. Numbers and dates

- Defaults from tokens: thousands separator U+202F (narrow no-break space), decimal sign
  `number.separator.decimal`, minus `-`, plus only on variances, `N/A`, `pp`. Locale and currency
  are **settings**: pick one decimal convention per organisation (e.g. `en-US`, `de-DE`) and set it
  once; format with `Intl.NumberFormat` and then apply the token separators if you keep them.
- **One scaling prefix per visual** (per scale group): choose the factor from the largest
  absolute value so labels need ≤ 3 significant digits in charts, ≤ 4 in tables. Put the unit
  once in the title (`mEUR`, ISO 4217 code with lower-case prefix k/m/b), never in labels.
- Decimals are fixed **per scale group** (one setting for every visual of the group), not per
  label. Precedence: an explicit display setting (a visual spec's `display: {prefix, decimals,
  format}`) wins over the automatic rule (`pickScale`: ≤ 3 digits, 1 decimal below 100); the
  automatic rule only fills what the spec leaves open. One-decimal Δ% uses
  `number.format.relativeVariance1`, plain ratios (book-to-bill) `number.format.plainRatio`.
- Charts receive raw values and a format; formatting happens at the label. Never format in the
  query (`FORMAT()` breaks sorting and scaling) and never feed formatted strings to geometry.
- Periods (tokens `date.*`): `2026-06`, `2026-Q2`, `2026-W17`; within a year `Jun`, `Q2`; spans
  `Jan..Mar`; year-to-date `_Jun 2026`. Strip a trailing full stop from locale month
  abbreviations (`Jun.` → `Jun`): IBCS uses a trailing `.` to mean "last day of".
- Dates from many BI APIs arrive as ISO strings without a time zone; parse calendar fields
  yourself. `new Date("2026-03-01")` is UTC and shifts the day west of Greenwich.

Recipes: `references/formatting-a11y-print.md`.

## 5. One scale per unit on a page

The most common IBCS breach in web apps is each chart auto-scaling on its own (IBCS v2.0, CH 4.1).

- Keep a **scale registry per page** (a React context, a store, or a plain object built before
  render): unit key (`"EUR"`, `"t"`, `"%"`) → px per unit. Each chart registers its value extent
  and the plot pixels it may use at most (after its own labels, tier gaps and padding); every
  chart of a unit uses the **smallest** px-per-unit. The registry hands out px per unit, never a
  domain: each chart sizes its own plot = its own range × px per unit, so a chart with smaller
  values becomes **shorter**; it never takes another chart's max or stretches its axis to fill a
  fixed box.
- Absolute variance tiers join the **same** unit as their base chart. Relative variances (pins),
  pp tiers and %-measures share one `"%"` group. Tables with in-cell bars join too.
- Small multiples join the page's registry (a panel's 100 EUR is as tall as anywhere else). A
  deliberate own scale needs a visible **scale band** (UN 5.2) at a round value drawn on every
  chart of that unit, and a footnote.
- Server rendering and print: allow a **fixed** px-per-unit per group (e.g. 40 px per mEUR). A
  fixed scale is honoured exactly; a chart grows and warns rather than shrinking the scale.
- Outliers (UN 5.3): only a business-irrelevant **relative** value (a pin) flagged as an outlier
  may be left out of the scale; it is drawn truncated with an outlier marker and keeps its full
  value in the label. Never truncate absolute bars, totals or the remainder (CH 2.1).
- **A remainder must not flatten the page.** When a top-N remainder ("Others") or a total is so
  large that the shared px/unit leaves the other charts of the unit unreadable (OURS: any chart's
  largest bar < 24 px), give that ranking its own scale group and draw a **scale band** at the
  same round value on every chart of the unit, with a footnote ("Customers on their own scale");
  or move the long-tail ranking to its own page. Never truncate the remainder to fit, never let
  it set the scale silently.
- **Mixed orientations and cell sizes.** A group that spans a vertical column chart (height per
  unit) and a horizontal bar chart (width per unit) shares one px per unit across both
  directions, so a monthly chart in a short cell and a YTD chart about 10× larger in value in a
  narrow cell can flatten each other. The readability rule above applies per tier, in every
  member; when it fails, split the group with a scale band as above (ibcs-composition
  `visual-spec-format.md` §4).

## 6. Tables

Real `<table>` with `<caption>` and `<th scope>`. Scenario header markers (AC solid bar, PY light,
PL/BU outlined, FC hatched); totals and subtotals bold with a single rule above; remainder before
the total; "of which" rows smaller; hierarchy by indent with parents below their children in
calculation order. Absolute variance columns use the value columns' decimals, relative ones
whole percents (or one decimal, OURS) with `%`. In-cell bars share one px-per-unit per column
group and join the page scale. Variance **numbers** may be tinted by impact only with the
contrast-safe text tokens `color.variance.goodText` / `badText` / `neutralText` (≥ 4.5:1 —
the rule is in the ibcs-notation skill, §3); never with the bright graphic green (2.4:1). Without
those tokens they stay black and the bars and pins carry the colour. Δ = 0 (also rounded) and
N/A are never tinted.

## 7. Accessibility, phone, print (summary)

- Each chart is `<svg role="img" aria-labelledby>` with `<title>` (the IBCS title lines) and
  `<desc>`, plus a visually hidden data table holding every plotted number. Interactive charts:
  focusable marks (`tabindex=0`, `role="button"`, an accessible name such as "Feb: AC 380, PL
  395"), Enter/Space activate, visible `:focus-visible` outline.
- Colour is never the only cue: signed labels, direction and hatching carry the same meaning.
- No animation (IBCS v2.0, SI 1.3); respect `prefers-reduced-motion` anyway.
- Phone (≈ 390 px): no horizontal page scroll; labels stay horizontal, shrink, then thin out
  (keep first, last, highest, lowest); ≤ 12 periods per chart or switch to quarters; tables scroll
  inside their own wrapper with a sticky label column. Screenshot it with device emulation, not
  a 390 px window (`references/testing.md`).
- Charts are white "paper": `color.background.page`. A dark app shell may surround it; no dark
  chart theme.
- Print/PDF: SVG keeps hatching crisp; hide controls; keep charts unbroken across pages; show
  active filters in title line 1 and sources plus data timestamp in a footnote.

Checklists: `references/formatting-a11y-print.md`.

## 8. Build components as pure layout + thin renderer

Structure each chart as `layout(data, options) → { width, height, marks[], warnings[] }`, where
each mark is a primitive (rect, line, path, text) tagged with a **role** (`col-AC`, `col-PL`,
`variance`, `pin`, `pin-head`, `triangle-PY`, `axis`, `label`, …). The React (or other) renderer
only maps marks to SVG. Benefits: unit tests without a DOM, the same layout feeds print and
server rendering, and notation can be asserted by role. The renderer writes the role on the SVG
element as `data-role` (plus `data-impact="good|bad|neutral|none"` on variance bars, pins and
variance numbers): role names are `<shape>-<scenario>` for scenario marks (`col-AC`, `col-FC`,
`bar-PY`, `triangle-PY`, `line-AC`), `variance`, `pin`, `pin-head`, `label`, `variance-label`,
`axis`, `axis-<scenario>`, `marker-ellipse`, `assisting-area`, `scale-band`, `step` for
calculation-waterfall steps (with `data-kind="base|add|sub|subtotal|total"`: additions grey,
subtractions in the AC colour, never a scenario role) and `segment-<n>` for stacked segments above
the lowest one (the lowest carries the scenario role, e.g. `col-AC`). Tests query them,
and the ibcs-review linter checks a saved page snapshot with them (`ibcs_lint.py dom page.html`).
A minimal token-driven example and the geometry numbers: `references/geometry-and-porting.md`. Clamp pin stems, pin heads and scenario
triangles in px (`geometry.pin.stemPx`, `.headPx`, `geometry.triangleSizePx`) after applying the
ratios, so wide columns do not get oversized pins. Generate the token module instead of
hand-copying values:
`node "${CLAUDE_SKILL_DIR}/../ibcs-notation/scripts/gen_tokens.mjs" --out src/ibcs/tokens.generated.ts`
(base tokens + the project's overrides, aliases resolved; `.json` and `.css` outputs too). To
regenerate without the plugin (CI, other developers), copy the script **and** the token file
into the project and pass `--tokens` (the default path is relative to the script's own
folder), e.g. in `package.json`:
`"tokens": "node scripts/gen_tokens.mjs --tokens design/ibcs-tokens.json --out src/ibcs/tokens.generated.ts"`
(token copy in `design/`, as in the `ibcs-fabric-app` chart layer; add `--overrides` and a `.css` run when you use them),
then `npm run tokens`. Keep the script's name `gen_tokens.mjs` so the docs stay searchable.

## 9. Defaults to switch off in any generic library

Per-chart auto-scaled axes; value axes and gridlines instead of direct labels; legend boxes
(label series at the end of the series instead, right of the last period); a hue per scenario; green/red by
sign instead of by impact; `ABS()` in relative variances; side-by-side instead of overlapped
comparison columns; rounded corners, shadows, gradients on marks (an app's card surfaces are UI chrome, not marks); animation; tooltips as the only way to
read values; category labels rotated 45°.

## 10. Verify before you hand over

1. Unit tests on the layout functions (notation by role, variance arithmetic, N/A, Δ = 0, shared
   scale, outliers) — `references/testing.md`.
2. Render at **390 px, the host's content width and 1280 px** with device emulation (CDP
   `Emulation.setDeviceMetricsOverride` or Playwright `setViewportSize`; a headless
   `--window-size=390,…` lays out wider): `scrollWidth == clientWidth`, no chart collapsed, no
   console errors; assert notation in the DOM; run axe.
3. Compare screenshots with the matching figures in your copy of the IBCS Standards.
4. Run the [ibcs-review](../ibcs-review/SKILL.md) skill on the page.

## References

- `references/behaviour-contract.md` — per chart and table type: data, notation, labels, edge cases, warnings.
- `references/geometry-and-porting.md` — geometry numbers from the tokens, a React/SVG example, porting to D3/Vega-Lite/ECharts/visx/Recharts, evaluating a library.
- `references/formatting-a11y-print.md` — formatting recipes, accessibility, phone and print checklists.
- `references/testing.md` — unit, DOM, visual-regression and accessibility tests.
