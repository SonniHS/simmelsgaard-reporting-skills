# The IBCS chart layer in an app

As of 2026-10 there is **no shipped IBCS chart library**: neither this plugin nor the
`ibcs-web-charts` skill (plugin `ibcs`) ships one, and the data-app template's visuals (Vega-Lite
specs rendered by `@microsoft/fabric-visuals`) have no IBCS scenario notation, overlapped
references, variance pins or a page-wide scale registry. Until a library exists, each app writes a
small layer to the `ibcs-web-charts` contract. In an end-to-end test one page (multi-tier time
chart with a Total column, a structure chart with variances, KPI cards) took about 600 lines of
TypeScript including tests with the layout below. Reuse it from your previous app before writing it
again.

## Module layout (proven in a test)

```
design/ibcs-tokens.json            copy of the ibcs-notation token file (never edited)
ibcs-tokens.overrides.json         your organisation's overrides
scripts/gen_tokens.mjs             copy of the ibcs-notation skill's scripts/gen_tokens.mjs (base + overrides → the two files below)
src/ibcs/tokens.generated.ts       typed token object (colours, geometry ratios + px clamps, type scale)
src/ibcs/tokens.generated.css      the same tokens as CSS custom properties for page chrome
src/ibcs/format.ts                 scale factor, fixed decimals per scale group, signs, pp, N/A, roundsToZero
src/ibcs/impact.ts                 impact (−1/0/+1/null) → token colour (marks: good/bad; text: goodText/badText); never polarity logic
src/ibcs/scale.ts                  page scale registry: scale group → px per unit (smallest one wins)
src/ibcs/charts/marks.ts           Mark type: rect | line | path | text, each with a role and a category
src/ibcs/charts/<chart>.ts         pure layout functions: (rows, width, px per unit, format) → { width, height, marks, warnings }
src/ibcs/charts/MarksSvg.tsx       thin renderer: marks → <svg>, hatch patterns in its own <defs>, title/desc for a11y
src/ibcs/charts/charts.spec.ts     layout unit tests (below)
```

Rules:

- **Tokens → scale registry → pure layout → thin renderer**, one direction only. Layout functions
  have no DOM, no React and no data fetching; they take raw values plus px per unit from the
  registry and return marks. The renderer has no logic beyond mapping marks to SVG elements.
- **The registry hands out px per unit, never a domain.** Each layout function sizes its own plot
  from its own range (span × px per unit, plus its fixed px for labels and tier gaps) and returns
  that height; the page places it. A chart with smaller values is shorter; no chart receives
  another chart's max or stretches its axis to fill a fixed box (CH 4.1 with CH 4.2).
- **Every scale request stays positive** (ours, 2026-10). A chart that requests px per unit from a
  cell height subtracts its fixed px first (label rooms above and below each tier, tier gaps,
  category labels). With several pin tiers the label rooms can exceed the cell or the share given
  to a tier: the request turns zero or negative, a registry that drops non-positive requests skips
  it silently, and the chart draws on another chart's scale and clips. Floor the plot height
  (`plot = max(minPlotPx, cellPx − overheadPx)`, about 40 px), give each tier at least a minimum
  plot, return a warning when the floor applies, and unit-test a short cell with many tiers: no
  request ≤ 0, no mark outside the returned height.
- **Total next to the months** (own scale, ibcs-composition): the Total's base and its Δ tiers use
  the Total's px per unit from the registry (its own scale group), never the months'. They line up
  with the months by **px extents**, not units: the Total's base cell gets the months' base height
  (union of both base extents in px), and every tier's height is the union of the months' and the
  Total's px extents for that tier (each at its own px per unit); both charts get the same
  category-label band height and the same top, so baselines and tier axes sit at the same y. A Δ
  that is tiny on the Total's scale is drawn at its true height (a minimum of 1 px so it stays
  visible, never inflated to "look right") with its label carrying the value; the scale band in
  both charts and a footnote name the separate scale. Unit-test: months and Total tier axes at
  the same y for a filter that changes either range.
- Layout functions never compute variances or impact; they draw what the query returned
  (`queries-and-data.md` §3).
- Hatch pattern ids are unique per chart instance (`useId`), because `url(#id)` breaks across
  iframes and shadow roots, and the Fabric portal hosts the app in an iframe. Hatched FC
  **variance** marks in impact colours need one pattern per stripe colour (good, bad, neutral, and
  the grey of absolute FC), each with its own id (`${chartId}-hatch-good`, …): one shared pattern
  would draw every hatched variance in the same colour.
- **End legends** (scenario names right of the last column, and right of the Total) sit at their
  marks' y, never as a fixed list: PY at the triangle tip, BU (or another outlined reference) at
  the middle of the outline, AC or FC at the middle of the bar; "AC&FC" when the series runs from
  AC into FC, plain "AC" when the last column is AC. Spread them with a collision shift (minimum
  gap font size + 2 px between centres, kept inside the base tier). The same rule as the Deneb
  end legend (`column-two-tier-variance` legendSide "end") and `ibcs-web-charts` behaviour
  contract §2.
- **Structure-chart legend header** (scenario names above the bars): at least 1 em between names
  and clear of the first row's markers (triangle, outline end); when crowded, use the end-legend
  rule instead (names at the first or last row's marks).
- **Waterfall magnifier** (a zoom box on a part of the bars): the end-bar labels never sit on the
  zoom box's corner or on a connector: reserve label room outside the box (or put the labels
  above it) and route connectors around the labels.
- Generate the token module from the token file with a script; never hand-copy hex values. The
  copied script's default `--tokens` path points into the skill folder, so always pass the paths
  in a `tokens` npm script:
  `"tokens": "node scripts/gen_tokens.mjs --tokens design/ibcs-tokens.json --overrides ibcs-tokens.overrides.json --out src/ibcs/tokens.generated.ts && node scripts/gen_tokens.mjs --tokens design/ibcs-tokens.json --overrides ibcs-tokens.overrides.json --out src/ibcs/tokens.generated.css"`
  and run `npm run tokens` after every token change. Create `ibcs-tokens.overrides.json` at setup
  (`{}` when there are no overrides yet), because the explicit `--overrides` path must exist. Clamp
  token ratios that turn into pixels (pin stems and heads, triangles) to the px limits stated in
  the token file, so wide categories do not produce absurd marks.
- Return `warnings` (label collisions, outliers drawn at the edge) from layout and surface them in
  tests and the diagnostics toggle, not in the page.
- **Text in an impact colour uses the text tokens** (`goodText`, `badText`), never the graphic
  `good`/`bad` used for bars and pins: the graphic green fails text contrast on white. This covers
  KPI-card deltas, coloured labels and message highlights. Export two functions from `impact.ts`
  (`impactFill`, `impactText`) so the choice is made once.
- **One label per series or scenario per chart.** Name AC, PY, BU, FC once, at the right end or on
  the first category; never above and below the same bars.
- **Width from measured text.** Every layout function sizes its margins from its own text boxes
  (end series labels, the value label of the last point, the widest variance label at either
  end; boxes ≈ 0.6 em per digit × 1.2 em high, `ibcs-web-charts` label clearance) and returns the
  width it needs; a line chart's end value label is inside the returned width, never past it. The
  card hands in its content width ([report-shell.md](report-shell.md) §9); when the chart needs
  more, it shortens labels first and reports a warning, it does not overflow.
  The measured text sets the **margins**, never the plot width: the plot fills the content width
  the card hands in (minus those margins), for line charts as for columns. A line chart sized to
  its labels alone used about 40 % of its card in the portal and left the rest empty.

### Interaction: selectable categories

The report shell selects a month or a company by click ([report-shell.md](report-shell.md) §7).
Layout functions emit one transparent `rect` mark per category with role `"hit"` (the full
category band through all tiers); the renderer turns them into controls when it gets a callback:

```tsx
<MarksSvg layout={layout} title="…" onSelect={(category) => setUrlState({ month: category })} />
// in the renderer, for m.role === "hit" && onSelect:
<rect role="button" tabIndex={0} aria-label={m.tooltip ?? m.category} fill="transparent"
      onClick={() => onSelect(m.category)}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(m.category); } }} />
```

Rules: the selection lives in the URL (Back undoes it) and comes back into the layout as
`selected`, which draws the assisting band behind that category; hit zones are drawn last (on top),
focusable in reading order, with a visible focus outline from the page CSS; no hover-only
behaviour. Without `onSelect` the hit marks render nothing, so static charts stay unchanged.

### Phone layouts (≤ 760 px)

- **Month chart**: redraw for the card width, never scroll sideways. Order of reduction: Δ%
  labels to 0 decimals; then absolute labels to the scale's decimals − 1 (never below 0); then
  thin value labels by measured width (keep first, last, selected, extremes); the category step
  never drops below ≈ 22 px (12 months in ≈ 300 px). One-decimal labels need a step of ≈ 40 px at
  11 px type.
- **Total**: a Total-only chart under the months: one category, its own scale with the same
  scale band value, its tiers aligned to the months' tier order, tier names left of the column
  inside the chart width (not at the far left of a wide box).
- **Label collisions at narrow steps**: before drawing, test each value label's box against the
  neighbouring bars' boxes and labels (1.2 em high, measured width); a label that would touch the
  next bar is shifted (above the bar end, or to the free side) or dropped by the thinning order
  above, never drawn over a bar. Long category names are cut **from the end** with an ellipsis or
  wrapped to two lines, never with a middle ellipsis.
- **Structure chart** (companies): stack the variance tiers under the bars (`ibcs-web-charts`
  behaviour contract §4: bars, then ΔBU, then ΔBU%, each full width on the same category order and
  scale), instead of a horizontally scrolling row.
- Test each at 390 px in the layout check: no SVG wider than its card, every label box inside the
  viewBox.

## Layout check before any deployment

The page cannot load data before an app item exists (`queries-and-data.md` §0), but its layout
can be checked without one:

1. Split each page into a **pure view** (`<Page>View`: props = query states, selection, width;
   no hooks that fetch) and a thin container that runs the queries and passes the states.
2. Capture fixtures from **real** query output (`npx fabric-app-data query <alias> --file …`,
   saved into `src/test/fixtures/`; up to 1,000 rows), with the real column names. These are the
   CLI's JSON values: add a few portal-shaped rows (queries §6) to the `normalizeValue` tests.
3. Add a **test-only Vite harness** (`vite.harness.config.ts` with its own `root` under
   `src/test/harness/`, its own pinned port, a `harness` npm script; never part of `vite build`)
   that renders the view with the fixtures, plus `?state=loading|error|empty` for the state views.
4. Screenshot the harness at 390 px, ≈ 1050 px (the portal's content width beside its navigation)
   and 1280 px (device-width emulation) and run the page quality
   rubric on it. After the deployment, repeat the screenshots inside the portal: the harness does
   not show portal value shapes or sign-in.

Fixtures stay in tests and the harness; the app has no fixture mode (`queries-and-data.md` §0).

## Verification that replaces `validate:visual`

The template's `npm run validate:visual` renders **Vega-Lite query factories** headlessly and fails
when no data marks appear. It does not see custom SVG charts. Keep it for any Vega-Lite visual that
stays; for the IBCS layer use:

1. **Layout unit tests** on fixture rows with the real query column names: mark roles and order
   (reference drawn before the primary, shifted left), heights = value × px per unit on the shared
   scale, FC marks hatched, exactly one AC → FC separator, a Δ that rounds to zero at display
   precision gets no mark and an unsigned label, N/A gets no pin, no `NaN` in any coordinate.
2. **DOM checks** (component test with jsdom): counts of rendered elements per role, accessible
   title and description present, no `NaN`/`undefined` in SVG attributes.
3. **Screenshots** at 390 px and at the portal's own width (≈ 1050 px content) of the running page inside the portal (`&devUri=…`, see
   `queries-and-data.md` §0), inspected by eye and by the `ibcs-review` checklist. Use the
   screenshot recipe in the testing reference of the `ibcs-web-charts` skill: emulate the device
   width (Playwright viewport or CDP `Emulation.setDeviceMetricsOverride`); headless
   `--window-size=390,…` lays the page out wider than 390 px.
