# Geometry, a minimal SVG example, and porting to chart libraries

All numbers come from the token file `../ibcs-notation/assets/ibcs-tokens.json`, relative to this
skill's directory (`${CLAUDE_SKILL_DIR}` in SKILL.md), plus the user's
`ibcs-tokens.overrides.json`, deep-merged. Load the tokens once (import the JSON, or generate a
TS module / CSS custom properties with the ibcs-notation skill's `gen_tokens.mjs` in your build)
and read values from there.
A = category width (columns) or row step (bars); B = bar width.

## Contents
- [Shared geometry](#shared-geometry)
- [Shared scale](#shared-scale)
- [Minimal React + SVG example (overlapped AC/FC over PL)](#minimal-react--svg-example-overlapped-acfc-over-pl)
- [D3](#d3)
- [Vega-Lite](#vega-lite)
- [ECharts](#echarts)
- [visx / Recharts / Nivo](#visx--recharts--nivo)
- [What generic libraries get wrong by default](#what-generic-libraries-get-wrong-by-default)
- [Evaluating a library that claims IBCS support](#evaluating-a-library-that-claims-ibcs-support)

## Shared geometry

| Element | Rule | Token |
|---|---|---|
| Absolute column/bar | B = 2/3 A | `geometry.barWidthRatio.absolute` |
| Relative measure (%) column/bar | B = 1/3 A | `geometry.barWidthRatio.relative` |
| Absolute variance bar | same width and same px per unit as the base | `geometry.barWidthRatio.variance` |
| Overlapped reference | behind; shifted left 0.2 B (columns) / up 0.25 B (bars) | `geometry.referenceOffsetRatio.*` |
| Scenario triangle | ≈ 0.33 B high, clamped to 6–12 px; columns: points right, tip on the left edge; bars: points down, tip on the top edge | `geometry.triangleSizeRatio`, `geometry.triangleSizePx.{min,max}` |
| Pin | stem ≈ 0.3 B clamped to 2–4 px, square head ≈ 0.85 B clamped to 6–10 px (B = absolute bar thickness) | `geometry.pin.*`, `geometry.pin.stemPx`, `geometry.pin.headPx` |
| Variance axis | PY: one light thick line; PL/BU: two thin lines with a gap; FC: hatched band | `stroke.varianceAxis.*`, `color.axis.*` |
| Category axis | thin, dark, drawn **before** the marks | `stroke.categoryAxisPx`, `color.axis.category` |
| FC hatching | 45° stripes, small period, dark on white, with a thin outline; hatched FC **variance** marks stripe in their impact colour: one pattern per stripe colour (absolute grey, good, bad, neutral), ids unique per chart (`${id}-fc`, `${id}-fc-good`, …) | `pattern.fcHatch.*` (`svgTemplate`) |
| Remainder gap | one extra row step before "Other" | `geometry.remainderGapRatio` |
| Lines | absolute thick, relative half; square markers ≈ 2.5 × line | `stroke.line.*` |
| Category width by period | year > quarter > month > week > day | `geometry.categoryWidthByPeriod`, `geometry.categoryStepPx` |

Colours: scenario fills `color.scenario.*` (AC `ac`, PY `py`, PL/BU `fill` + `stroke`, FC
`stripe`/`ground`/`stroke`); impact `color.variance.{good,bad,neutral}` with `.cvd` and `.bw`
variants; labels `color.text.primary`; label on a dark AC bar `color.text.onAc`.

Clamp after the ratio, the same way in every renderer:
`size = Math.min(max, Math.max(min, ratio * B))`, e.g. head = clamp(0.85 × 60 px) = 10 px on a
wide month column instead of 51 px.

Impact colour = `good` if Δ × polarity > 0, `bad` if < 0, `neutral` if polarity is 0 — or the
model's Impact. Δ = 0 (or rounding to 0 at the displayed decimals) → no mark. Geometry always
uses the signed Δ. Tinted variance numbers use `color.variance.*Text`, not the graphic colours.

## Shared scale

```ts
// One px-per-unit per unit key on the page.
type Request = { unit: string; min: number; max: number; availablePx: number };
function pxPerUnit(requests: Request[]): Map<string, number> {
  const out = new Map<string, number>();
  for (const r of requests) {
    const span = Math.max(r.max, 0) - Math.min(r.min, 0);   // zero always included
    if (span <= 0) continue;
    const ppu = r.availablePx / span;
    out.set(r.unit, Math.min(out.get(r.unit) ?? Infinity, ppu));
  }
  return out;
}
// availablePx = the most plot px the chart may use (container minus its labels, tier gaps, padding).
// Each chart: plot height = span * ppu (sized to its data) + its fixed px; never stretch to fill,
// never hand a smaller chart the larger chart's max.
```

In React, hold the registry in a context: charts report their request in a layout effect, the
provider recomputes and re-renders. For server rendering, accept fixed values (`{ EUR: 40 / 1e6 }`).

## Minimal React + SVG example (overlapped AC/FC over PL)

Illustrative only; a real component adds labels, accessibility (see
`formatting-a11y-print.md`), selection and warnings.

```tsx
import tokens from "./ibcs-tokens.json";            // copy or generate from the skill's asset
import { useId } from "react";

const v = (t: { $value: any }) => t.$value;
const AC = v(tokens.color.scenario.ac);
const PL_FILL = v(tokens.color.scenario.pl.fill);
const B_RATIO = v(tokens.geometry.barWidthRatio.absolute);
const OFFSET = v(tokens.geometry.referenceOffsetRatio.column);
// Positive values only, for brevity. Note: token values like "{color.scenario.ac}" are aliases; resolve them when you load the file.

type Row = { period: string; AC: number | null; FC: number | null; PL: number | null };

export function ColumnsVsPlan({ rows, ppu, title }: { rows: Row[]; ppu: number; title: string }) {
  const id = useId().replace(/:/g, "_");             // unique pattern id per chart instance
  const A = 40, B = A * B_RATIO, off = B * OFFSET;
  const max = Math.max(0, ...rows.flatMap(r => [r.AC ?? r.FC ?? 0, r.PL ?? 0]));
  const h = max * ppu, zeroY = h + 4;
  return (
    <svg role="img" aria-labelledby={`${id}-t`} width={rows.length * A} height={zeroY + 16}>
      <title id={`${id}-t`}>{title}</title>
      <defs>
        <pattern id={`${id}-fc`} patternUnits="userSpaceOnUse" width="4" height="4"
                 patternTransform="rotate(45)">
          <rect width="4" height="4" fill={PL_FILL} />
          <rect width="1.8" height="4" fill={AC} />
        </pattern>
      </defs>
      <line x1={0} x2={rows.length * A} y1={zeroY} y2={zeroY} stroke={AC} strokeWidth={1} />
      {rows.map((r, i) => {
        const x = i * A + (A - B) / 2;
        const primary = r.AC ?? r.FC;
        return (
          <g key={r.period}>
            {r.PL != null && (                         /* reference: behind, shifted left */
              <rect x={x - off / 2} width={B} y={zeroY - r.PL * ppu} height={r.PL * ppu}
                    fill={PL_FILL} stroke={AC} strokeWidth={1} />
            )}
            {primary != null && (                      /* AC solid, FC hatched with outline */
              <rect x={x + off / 2} width={B} y={zeroY - primary * ppu} height={primary * ppu}
                    fill={r.AC != null ? AC : `url(#${id}-fc)`}
                    stroke={r.AC != null ? undefined : AC} strokeWidth={1} />
            )}
          </g>
        );
      })}
    </svg>
  );
}
```

Keep the pattern `<defs>` in the **same** SVG (or at least the same document tree — Shadow DOM
and iframes break `url(#…)`), with an id unique per chart instance.

## D3

Share one px-per-unit, not one `scaleLinear` with a fixed range per chart. Draw the reference
`rect`s first, then the primary; fill the primary with the AC colour or `url(#fc-id)` per datum;
draw the category axis before the marks. Use `d3.scaleBand` only for category positions and cap
the band width.

## Vega-Lite

- Use the **SVG renderer**; pattern fills via `url(#…)` need a `<defs>` in the same document.
  If the host renders to canvas, draw FC hatching as a layer of thin clipped `rule` marks instead.
- One scale across views: `resolve.scale` shared inside one concat/facet, otherwise compute
  domains and heights up front (`height = span × ppu`).
- Overlap: two `bar` layers with `xOffset`. Triangles: `point` with `shape: "triangle-right"` /
  `"triangle-down"`. Pins: `rule` + `square` point. Waterfalls: precompute start/end and use
  `bar` with `x`/`x2` (or `y`/`y2`).
- Set explicit colours from tokens; do not let a host CSS theme recolour scenario marks.
- The `ibcs-deneb` skill (plugin `ibcs-power-bi`) has token-driven Vega-Lite templates for these
  chart types; the grammar is the same outside Power BI once you replace host-specific data
  binding and format functions.

## ECharts

Negative `barGap` overlaps series; `decal` patterns give hatching (enable `aria.decal` and set
`decal: { symbol: "none" }` on series that must stay solid); `scatter` with `symbol: "triangle"`
and rotation for triangles; pins as a thin `bar` plus a `rect` scatter symbol; `renderer: "svg"`
for print. A variance tier is a second grid; give the grids the same px per unit through
explicit `min`/`max` and proportional heights.

## visx / Recharts / Nivo

visx: pattern primitives or the token template in `<defs>`; layout as with D3. Recharts: `<defs>`
inside the chart, a per-datum `Cell` fill, negative `barGap` for overlap, a custom `shape` for
triangles and pins. Nivo: pattern definitions plus fill rules. In all of them switch off
gridlines, value axes and legends, and label marks directly.

## What generic libraries get wrong by default

Auto-scaled axes per chart; value axes and gridlines instead of labels; legend boxes; a hue per
scenario; green/red by sign instead of impact; `ABS()` in relative variances; side-by-side
instead of overlapped columns; rounded corners; animation; tooltips as the only way to read
values; rotated category labels.

## Evaluating a library that claims IBCS support

Check it against this contract before adopting it — install it in a sandbox and read any setup
scripts before running them. Questions to answer with a rendered example:

1. Scenario notation by fill only (AC solid dark, PY solid light, PL/BU outlined, FC hatched) —
   no palette presets that colour scenarios by hue?
2. Three impact states (good, bad, **neutral blue** for polarity 0), polarity or model Impact
   driving colour only, geometry by sign? A colour-vision-deficiency variant that changes green,
   not red?
3. Variance axis in reference notation (PY light line, PL double line, FC hatched)? Scenario
   triangles for a third scenario?
4. One scale per unit across separate components on a page, not only inside one small-multiples
   component?
5. Relative variance with the signed reference and N/A when not interpretable?
6. Units once in the title (`mEUR`), bare numbers in labels — no currency symbols or compact
   "4.5M" in labels?
7. Square pin heads in the minuend's notation; totals with a single rule; no animation by
   default; white background for reports?
8. Title line 1 able to show active filters?
9. Accessibility: role/title/desc, data-table alternative, keyboard focus?

Where it deviates, either override per item or keep your own components. Lint its output with the
`ibcs-review` checklist, not only with the library's own checker.
