// Variance waterfall, as horizontal bars (behaviour contract §6): the base in reference notation,
// steps coloured by impact (FC steps hatched), the total in AC or FC notation, connectors, and a
// total-variance marker from the model's Δ. Never computes the total Δ itself.
import { tokens } from "../tokens.generated";
import { formatDelta, formatValue, roundsToZero, type NumberScale } from "../format";
import { impactFill, impactKey, impactText, type ColorMode, type Impact } from "../impact";
import { lineBox, textWidth, fitLines, type Fill, type Layout, type Mark } from "./marks";
import type { Scenario } from "./columnTiers";

export type Bridge = {
  base: { label: string; scenario: Exclude<Scenario, "AC">; value: number };
  steps: { label: string; delta: number; impact?: Impact | null; fc?: boolean; remainder?: boolean }[];
  total: { label: string; scenario: "AC" | "FC"; value: number };
  /** The model's total variance (e.g. ΔPY with its impact), from the same query. */
  variance: { code: string; value: number; impact?: Impact | null };
};

export type WaterfallOptions = {
  width: number;
  ppu: number;
  scale: NumberScale;
  polarity?: number;
  colorMode?: ColorMode;
  rowStep?: number;
  fontSize?: number;
  /** Reconciliation tolerance as a share of the total. Default 0.5 %. */
  tolerance?: number;
};

const T = tokens;
const C = T.color;

export function layoutVarianceWaterfall(b: Bridge, o: WaterfallOptions): Layout {
  const warnings: string[] = [];
  const size = o.fontSize ?? T.typography.size.label.px;
  const box = lineBox(size);
  const step = o.rowStep ?? Math.max(T.geometry.categoryStepPx.structureRow, box + 6);
  const B = step * T.geometry.barWidthRatio.absolute;
  const mode = o.colorMode ?? "color";
  const tol = (o.tolerance ?? 0.005) * Math.max(Math.abs(b.total.value), 1e-9);

  const sum = b.steps.reduce((s, x) => s + x.delta, b.base.value);
  if (Math.abs(sum - b.total.value) > tol) warnings.push(`base + steps = ${sum} ≠ total ${b.total.value}: add a remainder step`);
  if (Math.abs(b.variance.value - (b.total.value - b.base.value)) > tol) warnings.push(`${b.variance.code} ${b.variance.value} ≠ total − base`);

  // Running totals: every step floats from the previous end.
  let run = b.base.value;
  const spans = b.steps.map((s) => {
    const from = run;
    run += s.delta;
    return { from, to: run };
  });
  const all = [0, b.base.value, b.total.value, ...spans.flatMap((s) => [s.from, s.to])];
  const lo = Math.min(...all);
  const hi = Math.max(...all);

  const labels = [b.base.label, ...b.steps.map((s) => s.label), b.total.label];
  const labelCol = Math.min(Math.max(...labels.map((l) => textWidth(l, size))) + 8, o.width * 0.35);
  const valueLabels = [formatValue(b.base.value, o.scale), ...b.steps.map((s) => formatDelta(s.delta, o.scale)), formatValue(b.total.value, o.scale)];
  const room = Math.max(...valueLabels.map((l) => textWidth(l, size))) + 6;
  const x0 = labelCol + room - lo * o.ppu;
  const need = x0 + hi * o.ppu + room;
  if (need > o.width) warnings.push(`waterfall needs ${Math.ceil(need)} px but has ${o.width} px`);
  const X = (v: number) => x0 + v * o.ppu;
  const largest = Math.max(0, ...b.steps.map((s) => Math.abs(s.delta) * o.ppu));
  if (b.steps.length && largest < 8) warnings.push("largest step below 8 px on the page scale: add a magnifying glass (CH 4.5)");

  const header = 2;
  const rowY = (i: number) => header + step * (i + 0.5);
  const back: Mark[] = [];
  const marks: Mark[] = [];
  const hatch = (stripe: string): Fill => ({ hatch: stripe });
  const n = b.steps.length + 2;
  const markerY = rowY(n) + 2;
  const height = markerY + box + 6;

  back.push({ kind: "line", role: "axis", x1: X(0), x2: X(0), y1: header, y2: rowY(n - 1) + step / 2, stroke: C.axis.category, strokeWidth: T.stroke.categoryAxisPx });

  // base in reference notation
  const baseFill = b.base.scenario === "PY" ? { fill: C.scenario.py as Fill } : b.base.scenario === "FC" ? { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke } : { fill: C.scenario.pl.fill as Fill, stroke: C.scenario.pl.stroke };
  const bar = (role: string, i: number, from: number, to: number, fill: Fill | undefined, stroke?: string, impact?: Mark["impact"]) =>
    marks.push({ kind: "rect", role, impact, category: labels[i], x: Math.min(X(from), X(to)), y: rowY(i) - B / 2, w: Math.max(1, Math.abs(X(to) - X(from))), h: B, fill, stroke, strokeWidth: stroke ? 1 : undefined });
  bar(`bar-${b.base.scenario}`, 0, 0, b.base.value, baseFill.fill, "stroke" in baseFill ? baseFill.stroke : undefined);

  b.steps.forEach((s, k) => {
    const i = k + 1;
    const { from, to } = spans[k]!;
    const zero = roundsToZero(s.delta, o.scale);
    const key = impactKey(s.delta, { impact: s.impact, polarity: o.polarity, isZero: zero });
    // connector from the previous end to this step
    back.push({ kind: "line", role: "assisting-line", x1: X(from), x2: X(from), y1: rowY(i - 1) + B / 2, y2: rowY(i) - B / 2, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
    if (!zero) {
      const fill = impactFill(key, mode)!;
      bar("variance", i, from, to, s.fc ? hatch(fill) : fill, s.fc ? fill : undefined, key);
    }
  });
  back.push({ kind: "line", role: "assisting-line", x1: X(run), x2: X(run), y1: rowY(n - 2) + B / 2, y2: rowY(n - 1) - B / 2, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });

  const totalFill = b.total.scenario === "AC" ? { fill: C.scenario.ac as Fill } : { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke };
  bar(`bar-${b.total.scenario}`, n - 1, 0, b.total.value, totalFill.fill, "stroke" in totalFill ? totalFill.stroke : undefined);

  // labels: right of the bar's far end for growth, left for a drop; never on a connector
  for (let i = 0; i < n; i++) {
    const isStep = i > 0 && i < n - 1;
    const s = isStep ? b.steps[i - 1]! : null;
    const end = i === 0 ? b.base.value : i === n - 1 ? b.total.value : Math.max(spans[i - 1]!.from, spans[i - 1]!.to);
    const start = isStep ? Math.min(spans[i - 1]!.from, spans[i - 1]!.to) : 0;
    const right = !s || s.delta >= 0;
    const zero = s ? roundsToZero(s.delta, o.scale) : false;
    const key = s ? impactKey(s.delta, { impact: s.impact, polarity: o.polarity, isZero: zero }) : undefined;
    marks.push({
      kind: "text", role: isStep ? "variance-label" : "label", impact: key, category: labels[i],
      x: right ? X(end) + 3 : X(start) - 3, y: rowY(i), text: valueLabels[i]!, anchor: right ? "start" : "end",
      size, fill: isStep ? impactText(key!, mode) : C.text.primary, weight: i === n - 1 ? T.typography.weight.emphasis : undefined,
    });
    marks.push({ kind: "text", role: "category", category: labels[i], x: labelCol - 8, y: rowY(i), ...(() => { const lines = fitLines(labels[i]!, size, labelCol - 8, step); return { text: lines.length > 1 ? labels[i]! : lines[0]!, lines: lines.length > 1 ? lines : undefined }; })(), anchor: "end", size, fill: C.text.primary, weight: i === n - 1 ? T.typography.weight.emphasis : undefined });
  }

  // total-variance marker: an arrow from the base value to the total value, with the model's Δ
  const vKey = impactKey(b.variance.value, { impact: b.variance.impact, polarity: o.polarity, isZero: roundsToZero(b.variance.value, o.scale) });
  const xa = X(b.base.value);
  const xb = X(b.total.value);
  const dir = xb >= xa ? 1 : -1;
  const vFill = impactFill(vKey, mode) ?? C.text.primary;
  back.push({ kind: "line", role: "assisting-line", x1: xa, x2: xa, y1: rowY(0) + B / 2, y2: markerY, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
  marks.push({ kind: "line", role: "variance", impact: vKey, x1: xa, x2: xb - dir * 5, y1: markerY, y2: markerY, stroke: vFill, strokeWidth: 2 });
  marks.push({ kind: "path", role: "variance", impact: vKey, d: `M${xb} ${markerY} L${xb - dir * 6} ${markerY - 4} L${xb - dir * 6} ${markerY + 4} Z`, fill: vFill });
  const vText = `${b.variance.code} ${formatDelta(b.variance.value, o.scale)}`;
  marks.push({ kind: "text", role: "variance-label", impact: vKey, x: dir > 0 ? xb + 4 : xb - 4, y: markerY, text: vText, anchor: dir > 0 ? "start" : "end", size, fill: impactText(vKey, mode) });

  const table = [["Row", "Value"], ...labels.map((l, i) => [l, valueLabels[i]!]), [b.variance.code, formatDelta(b.variance.value, o.scale)]];
  return { width: o.width, height, marks: [...back, ...marks], warnings, table };
}
