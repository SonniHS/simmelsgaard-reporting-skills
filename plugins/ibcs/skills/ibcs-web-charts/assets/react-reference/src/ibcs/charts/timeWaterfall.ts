// Variance waterfall for a TIME decomposition, card A-11 (behaviour contract §6): columns — the
// reference column, the floating periodic Δ columns, then the AC (or FC) column — on a category
// axis broken into the groups reference | periods | AC, and the total variance as a vertical arrow
// right of the AC column, from the model's Δ (never computed here). When the periodic Δ are small
// next to the base (CH 4.5; the 5 % trigger is OURS), a magnifier tier below repeats them at
// factor k, each column under its period, with a "Steps ×k" caption; base and AC stay on the page
// scale and the zoomed range is outlined.
import { tokens } from "../tokens.generated";
import { formatDelta, formatValue, roundsToZero } from "../format";
import { impactFill, impactKey, impactText } from "../impact";
import { lineBox, textWidth, truncateEnd, type Fill, type Layout, type Mark } from "./marks";
import { magnifierFactor, type Bridge, type WaterfallOptions } from "./varianceWaterfall";

const T = tokens;
const C = T.color;

export function layoutTimeWaterfall(b: Bridge, o: Omit<WaterfallOptions, "rowStep">): Layout {
  const warnings: string[] = [];
  const size = o.fontSize ?? T.typography.size.label.px;
  const box = lineBox(size);
  const mode = o.colorMode ?? "color";
  const tol = (o.tolerance ?? 0.005) * Math.max(Math.abs(b.total.value), 1e-9);
  const sum = b.steps.reduce((s, x) => s + x.delta, b.base.value);
  if (Math.abs(sum - b.total.value) > tol) warnings.push(`base + steps = ${sum} ≠ total ${b.total.value}: add a remainder step`);
  if (Math.abs(b.variance.value - (b.total.value - b.base.value)) > tol) warnings.push(`${b.variance.code} ${b.variance.value} ≠ total − base`);

  let run = b.base.value;
  const spans = b.steps.map((s) => {
    const from = run;
    run += s.delta;
    return { from, to: run };
  });
  const largestAbs = Math.max(0, ...b.steps.map((s) => Math.abs(s.delta)));
  const magnify = o.magnifier !== "off" && b.steps.length > 0 && largestAbs < (o.magnifyBelow ?? 0.05) * Math.abs(b.base.value);
  const k = magnify ? magnifierFactor(largestAbs * o.ppu) : 1;
  if (!magnify && b.steps.length && largestAbs * o.ppu < 8) warnings.push("largest step below 8 px on the page scale: add a magnifying glass (CH 4.5)");

  const all = [0, b.base.value, b.total.value, ...spans.flatMap((s) => [s.from, s.to])];
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  const labels = [b.base.label, ...b.steps.map((s) => s.label), b.total.label];
  const valueLabels = [formatValue(b.base.value, o.scale), ...b.steps.map((s) => formatDelta(s.delta, o.scale)), formatValue(b.total.value, o.scale)];
  const vText = `${b.variance.code} ${formatDelta(b.variance.value, o.scale)}`;

  // Horizontal: reference | gap | periods | gap | AC | arrow and its label.
  const n = labels.length;
  const gap = 0.5; // in category steps, between the axis groups
  const arrowRoom = 12 + textWidth(vText, size) + 4;
  const step = (o.width - arrowRoom) / (n + 2 * gap);
  const B = step * T.geometry.barWidthRatio.absolute;
  const cx = (i: number) => step * (i + 0.5 + (i > 0 ? gap : 0) + (i === n - 1 ? gap : 0));
  if (Math.max(...valueLabels.map((l) => textWidth(l, size))) > step - 2) warnings.push("value labels wider than a column: widen the chart or thin the periods");

  const room = box + 2;
  const y0 = room + hi * o.ppu;
  const Y = (v: number) => y0 - v * o.ppu;
  const catY = y0 + Math.max(0, -lo) * o.ppu + room + box / 2;
  let height = catY + box / 2 + 4;

  const back: Mark[] = [];
  const marks: Mark[] = [];
  const hatch = (stripe: string): Fill => ({ hatch: stripe });

  // Broken category axis: one segment per group.
  const seg = (i1: number, i2: number) => back.push({ kind: "line", role: "axis", x1: cx(i1) - step / 2, x2: cx(i2) + step / 2, y1: y0, y2: y0, stroke: C.axis.category, strokeWidth: T.stroke.categoryAxisPx });
  seg(0, 0);
  if (n > 2) seg(1, n - 2);
  seg(n - 1, n - 1);

  const col = (role: string, i: number, v1: number, v2: number, fill: Fill | undefined, stroke?: string, impact?: Mark["impact"]) =>
    marks.push({ kind: "rect", role, impact, category: labels[i], x: cx(i) - B / 2, y: Math.min(Y(v1), Y(v2)), w: B, h: Math.max(1, Math.abs(Y(v1) - Y(v2))), fill, stroke, strokeWidth: stroke ? 1 : undefined });
  const baseFill = b.base.scenario === "PY" ? { fill: C.scenario.py as Fill } : b.base.scenario === "FC" ? { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke } : { fill: C.scenario.pl.fill as Fill, stroke: C.scenario.pl.stroke };
  col(`col-${b.base.scenario}`, 0, 0, b.base.value, baseFill.fill, "stroke" in baseFill ? baseFill.stroke : undefined);

  b.steps.forEach((s, j) => {
    const i = j + 1;
    const { from, to } = spans[j]!;
    const zero = roundsToZero(s.delta, o.scale);
    const key = impactKey(s.delta, { impact: s.impact, polarity: o.polarity, isZero: zero });
    back.push({ kind: "line", role: "assisting-line", x1: cx(i - 1) + B / 2, x2: cx(i) - B / 2, y1: Y(from), y2: Y(from), stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
    if (!zero) {
      const fill = impactFill(key, mode)!;
      col("variance", i, from, to, s.fc ? hatch(fill) : fill, s.fc ? fill : undefined, key);
    }
    const up = s.delta >= 0 || zero;
    if (!magnify) marks.push({ kind: "text", role: "variance-label", impact: key, category: labels[i], x: cx(i), y: up ? Y(Math.max(from, to)) - box / 2 - 1 : Y(Math.min(from, to)) + box / 2 + 1, text: valueLabels[i]!, anchor: "middle", size, fill: impactText(key, mode) });
  });
  back.push({ kind: "line", role: "assisting-line", x1: cx(n - 2) + B / 2, x2: cx(n - 1) - B / 2, y1: Y(run), y2: Y(run), stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
  const totalFill = b.total.scenario === "AC" ? { fill: C.scenario.ac as Fill } : { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke };
  col(`col-${b.total.scenario}`, n - 1, 0, b.total.value, totalFill.fill, "stroke" in totalFill ? totalFill.stroke : undefined);
  for (const i of [0, n - 1]) {
    const v = i === 0 ? b.base.value : b.total.value;
    marks.push({ kind: "text", role: "label", category: labels[i], x: cx(i), y: Y(Math.max(v, 0)) - box / 2 - 1, text: valueLabels[i]!, anchor: "middle", size, fill: C.text.primary, weight: i === n - 1 ? T.typography.weight.emphasis : undefined });
  }
  labels.forEach((l, i) => marks.push({ kind: "text", role: "category", category: l, x: cx(i), y: catY, text: truncateEnd(l, size, step - 2), anchor: "middle", size, fill: C.text.primary }));

  // Total variance: a vertical arrow right of the AC column, from the reference level to the AC level.
  const vKey = impactKey(b.variance.value, { impact: b.variance.impact, polarity: o.polarity, isZero: roundsToZero(b.variance.value, o.scale) });
  const vFill = impactFill(vKey, mode) ?? C.text.primary;
  const xArrow = cx(n - 1) + B / 2 + 8;
  const ya = Y(b.base.value);
  const yb = Y(b.total.value);
  const dir = yb <= ya ? -1 : 1;
  back.push({ kind: "line", role: "assisting-line", x1: cx(0) + B / 2, x2: xArrow, y1: ya, y2: ya, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
  marks.push({ kind: "line", role: "variance", impact: vKey, x1: xArrow, x2: xArrow, y1: ya, y2: yb - dir * 5, stroke: vFill, strokeWidth: 2 });
  marks.push({ kind: "path", role: "variance", impact: vKey, d: `M${xArrow} ${yb} L${xArrow - 4} ${yb - dir * 6} L${xArrow + 4} ${yb - dir * 6} Z`, fill: vFill });
  marks.push({ kind: "text", role: "variance-label", impact: vKey, x: xArrow + 6, y: (ya + yb) / 2, text: vText, anchor: "start", size, fill: impactText(vKey, mode) });

  if (magnify) {
    // Magnifier tier below the overview: steps only, at k × the page scale, under their periods.
    const runs = spans.flatMap((x) => [x.from, x.to]);
    const zLo = Math.min(...runs);
    const zHi = Math.max(...runs);
    const zx1 = cx(1) - step / 2;
    const zx2 = cx(n - 2) + step / 2;
    back.push({ kind: "rect", role: "zoom-box", x: zx1, y: Y(zHi) - 3, w: zx2 - zx1, h: Y(zLo) - Y(zHi) + 6, stroke: C.marker.highlight, strokeWidth: 1 });
    const pTop = height + 4;
    const pBase = pTop + box + 4 + room + (zHi - zLo) * o.ppu * k; // the panel's value origin (zLo)
    const Yp = (v: number) => pBase - (v - zLo) * o.ppu * k;
    marks.push({ kind: "text", role: "magnifier-caption", group: "zoom", x: zx1, y: pTop + box / 2, text: `Steps ×${k}`, anchor: "start", size, fill: C.text.secondary });
    back.push({ kind: "path", role: "axis-break", group: "zoom", d: `M${zx1 - 6} ${pBase - 6} L${zx1 - 2} ${pBase - 2} L${zx1 - 6} ${pBase + 2} L${zx1 - 2} ${pBase + 6}`, stroke: C.axis.category, strokeWidth: 1 });
    b.steps.forEach((s, j) => {
      const i = j + 1;
      const { from, to } = spans[j]!;
      const zero = roundsToZero(s.delta, o.scale);
      const key = impactKey(s.delta, { impact: s.impact, polarity: o.polarity, isZero: zero });
      if (j > 0) back.push({ kind: "line", role: "assisting-line", group: "zoom", x1: cx(i - 1) + B / 2, x2: cx(i) - B / 2, y1: Yp(from), y2: Yp(from), stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
      if (!zero) {
        const fill = impactFill(key, mode)!;
        marks.push({ kind: "rect", role: "variance", impact: key, group: "zoom", category: labels[i], x: cx(i) - B / 2, y: Math.min(Yp(from), Yp(to)), w: B, h: Math.max(1, Math.abs(Yp(from) - Yp(to))), fill: s.fc ? hatch(fill) : fill, stroke: s.fc ? fill : undefined, strokeWidth: s.fc ? 0.75 : undefined });
      }
      const up = s.delta >= 0 || zero;
      marks.push({ kind: "text", role: "variance-label", impact: key, group: "zoom", category: labels[i], x: cx(i), y: up ? Yp(Math.max(from, to)) - box / 2 - 1 : Yp(Math.min(from, to)) + box / 2 + 1, text: valueLabels[i]!, anchor: "middle", size, fill: impactText(key, mode) });
    });
    // Connectors down the zoom box's edges to the panel (category names are cut to fit their step, so they stay clear).
    for (const x of [zx1, zx2]) back.push({ kind: "line", role: "magnifier-connector", group: "zoom", x1: x, y1: Y(zLo) + 3, x2: x, y2: pTop + box + 2, stroke: C.marker.highlight, strokeWidth: 0.75 });
    height = pBase + room + 4;
  }

  const table = [["Period", "Value"], ...labels.map((l, i) => [l, valueLabels[i]!]), [b.variance.code, formatDelta(b.variance.value, o.scale)]];
  return { width: o.width, height, marks: [...back, ...marks], warnings, table };
}
