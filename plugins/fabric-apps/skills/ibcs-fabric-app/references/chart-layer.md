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
- Layout functions never compute variances or impact; they draw what the query returned
  (`queries-and-data.md` §3).
- Hatch pattern ids are unique per chart instance (`useId`), because `url(#id)` breaks across
  iframes and shadow roots, and the Fabric portal hosts the app in an iframe.
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
