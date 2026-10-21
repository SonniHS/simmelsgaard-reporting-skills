# IBCS® reference components (React + TypeScript + SVG)

A lean, tested starting point for IBCS-style charts in a web app, written to the
[behaviour contract](../../references/behaviour-contract.md) of the `ibcs-web-charts` skill. **Copy
`src/ibcs/` into your app and extend it**; do not rewrite the rules it already implements. MIT
licensed (see the plugin's NOTICE). It follows the IBCS® Standards; it is not certified by IBCS
Institute.

![Preview: KPI cards, months with an aligned Total on its own scale, structure bars, a bridge](previews/page.png)

## What is inside

| File | What it does | Contract |
|---|---|---|
| `src/ibcs/tokens.generated.ts` | The token file as a typed object (generated, never edited) | SKILL §8 |
| `src/ibcs/format.ts` | `pickScale` (one factor and fixed decimals per scale group, explicit spec wins), `formatValue`, `formatDelta`, `formatPercentDelta`, `formatPp`, `roundsToZero` (a Δ that rounds to zero prints unsigned: `0.00`) | §4 |
| `src/ibcs/impact.ts` | `impactKey` (model impact wins, polarity is the fallback, zero → none), `impactFill` for marks, `impactText` for numbers (the contrast-safe `*Text` tokens) | §3 |
| `src/ibcs/scale.tsx` | `pxPerUnit` and a React `ScaleProvider` / `useScale`: one px per unit per group, the smallest wins, fixed values for print; `pinScale` sizes pin tiers to their extent (the largest \|Δ%\| fills 90 %) for charts read together; `pinClip` scales a tier from its non-outlier pins (one pin over 3 × the next-largest is clipped) | §5 |
| `src/ibcs/charts/marks.ts` | Mark primitives with roles, text boxes (1.2 em), end-cut and middle-cut names, label spreading | §8 |
| `src/ibcs/charts/columnTiers.ts` | Columns over time: AC solid, FC hatched after the last closed period, overlapped reference, triangle, ΔREF bars on the base px per unit, ΔREF% pins on a scale sized to their tier (6 px heads, baseline marker for a rounded zero, one-decimal labels) and outliers, month names without an ellipsis (`periodLabels`), end legend at the marks, selection band, highlight ring, scale band, and `alignTiers` for a Total on its own scale | contract §2–3 |
| `src/ibcs/charts/structureBars.ts` | Bars by category: triangle or overlapped reference, Δ and Δ% tiers, remainder gap, bold total, legend once above the top row; a member with a reference but no AC drawn as 0.0, a warning when Σ row Δ ≠ the total; `stack: "auto"` (phones) puts the tiers under the bars, same row order, names repeated | contract §4 |
| `src/ibcs/charts/varianceWaterfall.ts` | Structure bridge (A-29, rows): base in reference notation, steps by impact (FC hatched), connectors, the total-variance arrow below AC from the model's Δ, reconciliation warnings, the CH 4.5 magnifier (`magnifyBelow`, `magnifierFactor`), and fit to the width (`fitWaterfalls` for bridges read together) | contract §6 |
| `src/ibcs/charts/timeWaterfall.ts` | Time bridge (A-11, columns): reference \| periods \| AC on a broken axis, the vertical total-variance arrow right of AC, magnifier tier below | contract §6 |
| `src/ibcs/charts/MarksSvg.tsx` | Thin renderer: hatch patterns per stripe colour with ids unique per instance, `data-role` / `data-impact`, title, hidden data table, focusable category zones | §7–8 |
| `src/ibcs/KpiCard.tsx` | KPI card on a Fluent card surface (or square): centred by default (`align: "start"` for left), name with (i), unit line, value, Δ lines with text tokens and one-decimal Δ%, pp for ratios, ring on the cited Δ; an omitted Δ% is left out, N/A only for a null Δ% with a reference ≤ 0 | contract §10 |
| `src/ibcs/ibcs.test.tsx` | One test per rule of `references/testing.md` (47 tests) | testing |
| `scripts/render-previews.tsx` | Renders `previews/*.svg` and `previews/page.html` from generic sample data | |

Layout functions are pure: `layout(rows, options) → { width, height, marks, warnings, table }`. They
never compute variances or impact; pass what the model returned (the `semantic-model-ibcs` skill
in plugin `reporting-data` has the query patterns).

## Use it in an app

```sh
cp -R <this folder>/src/ibcs src/ibcs                     # the components and their tests
cp <ibcs-notation skill>/assets/ibcs-tokens.json design/   # then regenerate tokens.generated.ts
cp <ibcs-notation skill>/scripts/gen_tokens.mjs scripts/   # with your overrides (chart-layer below)
npm i react react-dom && npm i -D vitest typescript @types/react @types/react-dom react-test-renderer @types/react-test-renderer
# react-test-renderer must match the React major: 18.3.1 here; with React 19 use react-test-renderer@19
```

```tsx
import { MarksSvg, alignTiers, columnTiersExtents, layoutColumnTiers, pickScale, useScale } from "./ibcs";

const ext = columnTiersExtents(rows, { reference: "BU", triangle: "PY" });
const ppu = useScale([
  { unit: "EUR", ...ext.base, availablePx: 140 },
  { unit: "EUR", ...ext.delta, availablePx: 50 },
  { unit: "%", ...ext.pct, availablePx: 40 },
]);
if (!ppu.get("EUR") || !ppu.get("%")) return null;          // first layout pass
const layout = layoutColumnTiers(rows, {
  width, reference: "BU", triangle: "PY", ppu: ppu.get("EUR")!, pctPpu: ppu.get("%")!,
  scale: pickScale(rows.flatMap((r) => [r.AC, r.FC, r.BU])), selected, polarity: 1,
});
return <MarksSvg layout={layout} title="Revenue in mEUR, 2026 AC&FC vs BU" onSelect={setSelected} />;
```

A Total beside the months: lay out both, then lay them out again with
`minTierPx: alignTiers(months, total)` so their baselines and tier axes sit at the same y; give the
Total its own scale group, `scaleBand` on both and a footnote.

For a Fabric app, the `ibcs-fabric-app` skill (plugin `fabric-apps`) says where these files go
(its `chart-layer.md` reference) and how the report shell places them.

## Extend, do not fork the rules

Add chart types (line chart, small multiples, tables) as new layout functions next to these, with
tests by role. What is deliberately left out: line charts, tables, small multiples, calculation and
growth waterfalls. Column charts take a second absolute tier (`tiers: ["delta", "delta2"]`,
`reference2: "PY"`) when one month chart must show the variance to BU and to PY.

The tests import `describe`/`it`/`expect` from `vitest` and set `// @vitest-environment node`, so
they run unchanged in an app whose vitest defaults to jsdom and whose tsconfig has no vitest globals.

## Develop

```sh
npm ci
npm test            # vitest: layouts, renderer, KPI card, token sync
npm run typecheck
npm run previews    # rewrite previews/; screenshot previews/page.html for page.png and check
                    # previews/phone.html at a 390 px viewport (charts redrawn for 326 px)
```

Lint a rendered page with the ibcs-review linter:
`python3 -I <ibcs-review skill>/scripts/ibcs_lint.py dom previews/page.html`.
