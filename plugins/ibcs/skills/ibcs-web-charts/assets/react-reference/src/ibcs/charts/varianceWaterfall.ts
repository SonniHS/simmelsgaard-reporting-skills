// Variance waterfall for a STRUCTURE decomposition, card A-29 (behaviour contract §6): one row per
// element, horizontal bars; the reference base bar on top, floating contributions coloured by
// impact (FC steps hatched), the AC (or FC) total bar at the bottom, connectors, and the total
// variance as a horizontal arrow below the total bar, from the model's Δ (never computed here).
// When the contributions are too small for the page scale, a magnifier (CH 4.5) draws them again in
// a steps-only panel at factor k: source frame → connectors → framed panel, the axis-break glyph on
// the panel's own origin line next to "Steps ×k"; base and total stay on the page scale. No label
// ever touches a line: a label that would is moved to the far side of its bar, or inside it.
import { tokens } from "../tokens.generated";
import { formatDelta, formatValue, roundsToZero, type NumberScale } from "../format";
import { impactFill, impactKey, impactText, type ColorMode, type Impact } from "../impact";
import { lineBox, markBox, overlaps, textWidth, fitLines, type Fill, type Layout, type Mark } from "./marks";
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
  /** OURS: magnify when the largest contribution is below this share of |base|. Default 0.05; 0 = never. */
  magnifyBelow?: number;
  /** Where the magnifier panel goes: beside the overview when it fits (default), or below it (phones). */
  magnifier?: "auto" | "below" | "off";
  /** Shrink the page scale to fit the width (default true): at phone width the bridge never overflows its card. */
  fit?: boolean;
};

/** Smallest of 1, 2, 5, 10, 20, 50, … that makes `px` at least `minPx`. */
export function magnifierFactor(px: number, minPx = 40): number {
  if (!(px > 0)) return 1;
  for (let e = 0; e < 12; e++) for (const m of [1, 2, 5]) if (px * m * 10 ** e >= minPx) return m * 10 ** e;
  return 1e12;
}

/** Roles of the lines no label may touch (axes, connectors, assisting lines, frames, the break glyph). */
export const LINE_ROLES = /^(axis|assisting-line|magnifier-connector|axis-break|zoom-box|magnifier-panel|variance-arrow)$/;

/** Boxes of every line a label must stay clear of; frames count by their four edges. */
export function lineBoxes(marks: Mark[]): { x: number; y: number; w: number; h: number }[] {
  const out: { x: number; y: number; w: number; h: number }[] = [];
  for (const m of marks) {
    if (!LINE_ROLES.test(m.role)) continue;
    if (m.kind === "rect") {
      out.push({ x: m.x, y: m.y, w: m.w, h: 0 }, { x: m.x, y: m.y + m.h, w: m.w, h: 0 }, { x: m.x, y: m.y, w: 0, h: m.h }, { x: m.x + m.w, y: m.y, w: 0, h: m.h });
    } else if (m.kind === "line" || m.kind === "path") out.push(markBox(m));
  }
  return out;
}

const T = tokens;
const C = T.color;
const PANEL_GAP = 24;

function layoutAt(b: Bridge, o: WaterfallOptions): Layout {
  const warnings: string[] = [];
  const size = o.fontSize ?? T.typography.size.label.px;
  const box = lineBox(size);
  // a name wider than its column (at most 35 % of the width) wraps to two lines: that needs a row step of
  // 2.2 × the font size; cut from the end only when even two lines do not fit
  const longName = [b.base.label, ...b.steps.map((s) => s.label), b.total.label].some((l) => textWidth(l, size) + 8 > o.width * 0.35);
  const step = o.rowStep ?? Math.max(T.geometry.categoryStepPx.structureRow, box + 6, longName ? Math.ceil(2.2 * size) : 0);
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

  // Magnifier trigger (CH 4.5; the 5 % threshold is OURS): steps too small next to the base.
  const largestAbs = Math.max(0, ...b.steps.map((s) => Math.abs(s.delta)));
  const magnify = o.magnifier !== "off" && b.steps.length > 0 && largestAbs < (o.magnifyBelow ?? 0.05) * Math.abs(b.base.value);
  const k = magnify ? magnifierFactor(largestAbs * o.ppu) : 1;
  if (!magnify && b.steps.length && largestAbs * o.ppu < 8) warnings.push("largest step below 8 px on the page scale: add a magnifying glass (CH 4.5)");

  const labels = [b.base.label, ...b.steps.map((s) => s.label), b.total.label];
  const valueLabels = [formatValue(b.base.value, o.scale), ...b.steps.map((s) => formatDelta(s.delta, o.scale)), formatValue(b.total.value, o.scale)];
  const room = Math.max(...valueLabels.map((l) => textWidth(l, size))) + 6;

  // Panel geometry: steps only, from the lowest to the highest running total, at k × the page scale.
  const runs = spans.flatMap((s) => [s.from, s.to]);
  const zLo = magnify ? Math.min(...runs) : 0;
  const zHi = magnify ? Math.max(...runs) : 0;
  const panelW = room + (zHi - zLo) * o.ppu * k + room;
  // the total-variance label sits right of the arrow at the AC level (left of it for a drop)
  const vTextW = textWidth(`${b.variance.code} ${formatDelta(b.variance.value, o.scale)}`, size) + 6;
  const geom = (labelCol: number) => {
    const x0 = labelCol + room - lo * o.ppu;
    const overviewRight = x0 + hi * o.ppu + Math.max(room, b.total.value >= b.base.value ? vTextW : 0);
    const beside = magnify && o.magnifier !== "below" && overviewRight + PANEL_GAP + panelW <= o.width;
    const need = magnify && beside ? overviewRight + PANEL_GAP + panelW : Math.max(overviewRight, magnify ? labelCol + panelW : 0);
    return { labelCol, x0, overviewRight, beside, need };
  };
  // Names use the free width first, then wrap to two lines, and are cut only as a last resort.
  const nameW = Math.max(...labels.map((l) => textWidth(l, size))) + 8;
  let g = geom(Math.min(nameW, o.width * 0.35));
  if (g.labelCol < nameW && g.need < o.width) {
    const g2 = geom(g.labelCol + Math.min(o.width - g.need, nameW - g.labelCol));
    if (g2.beside === g.beside) g = g2;
  }
  const { labelCol, x0, overviewRight, beside, need } = g;
  if (need > o.width) warnings.push(`waterfall needs ${Math.ceil(need)} px but has ${o.width} px`);
  const X = (v: number) => x0 + v * o.ppu;

  const header = magnify && !beside ? box + 6 : 2;
  const rowY = (i: number) => header + step * (i + 0.5);
  const back: Mark[] = [];
  const marks: Mark[] = [];
  const hatch = (stripe: string): Fill => ({ hatch: stripe });
  const n = b.steps.length + 2;
  const markerY = rowY(n) + 2;
  const overviewBottom = markerY + box / 2 + 4;

  back.push({ kind: "line", role: "axis", x1: X(0), x2: X(0), y1: header, y2: rowY(n - 1) + step / 2, stroke: C.axis.category, strokeWidth: T.stroke.categoryAxisPx });

  const bar = (role: string, i: number, x1: number, x2: number, y: number, fill: Fill | undefined, stroke?: string, impact?: Mark["impact"], group?: "zoom") =>
    marks.push({ kind: "rect", role, impact, group, category: labels[i], x: Math.min(x1, x2), y: y - B / 2, w: Math.max(1, Math.abs(x2 - x1)), h: B, fill, stroke, strokeWidth: stroke ? 1 : undefined });
  const baseFill = b.base.scenario === "PY" ? { fill: C.scenario.py as Fill } : b.base.scenario === "FC" ? { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke } : { fill: C.scenario.pl.fill as Fill, stroke: C.scenario.pl.stroke };
  bar(`bar-${b.base.scenario}`, 0, X(0), X(b.base.value), rowY(0), baseFill.fill, "stroke" in baseFill ? baseFill.stroke : undefined);

  const stepKey = (s: Bridge["steps"][number]) => {
    const zero = roundsToZero(s.delta, o.scale);
    return { zero, key: impactKey(s.delta, { impact: s.impact, polarity: o.polarity, isZero: zero }) };
  };
  b.steps.forEach((s, j) => {
    const i = j + 1;
    const { from, to } = spans[j]!;
    const { zero, key } = stepKey(s);
    back.push({ kind: "line", role: "assisting-line", x1: X(from), x2: X(from), y1: rowY(i - 1) + B / 2, y2: rowY(i) - B / 2, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
    if (!zero) {
      const fill = impactFill(key, mode)!;
      bar("variance", i, X(from), X(to), rowY(i), s.fc ? hatch(fill) : fill, s.fc ? fill : undefined, key);
    }
  });
  back.push({ kind: "line", role: "assisting-line", x1: X(run), x2: X(run), y1: rowY(n - 2) + B / 2, y2: rowY(n - 1) - B / 2, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });

  const totalFill = b.total.scenario === "AC" ? { fill: C.scenario.ac as Fill } : { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke };
  bar(`bar-${b.total.scenario}`, n - 1, X(0), X(b.total.value), rowY(n - 1), totalFill.fill, "stroke" in totalFill ? totalFill.stroke : undefined);

  const category = (i: number, x: number, y: number, group?: "zoom") => {
    const lines = fitLines(labels[i]!, size, labelCol - 8, step);
    marks.push({ kind: "text", role: "category", group, category: labels[i], x, y, text: lines.length > 1 ? labels[i]! : lines[0]!, lines: lines.length > 1 ? lines : undefined, anchor: "end", size, fill: C.text.primary, weight: i === n - 1 ? T.typography.weight.emphasis : undefined });
  };
  // Step labels: right of the bar's far end for growth, left for a drop; placed last, clear of every line.
  type StepLabel = { j: number; Xf: (v: number) => number; y: number; group?: "zoom" };
  const stepLabels: StepLabel[] = [];
  for (let i = 0; i < n; i++) {
    category(i, labelCol - 8, rowY(i));
    if (i === 0 || i === n - 1) {
      const v = i === 0 ? b.base.value : b.total.value;
      marks.push({ kind: "text", role: "label", category: labels[i], x: X(Math.max(v, 0)) + 3, y: rowY(i), text: valueLabels[i]!, anchor: "start", size, fill: C.text.primary, weight: i === n - 1 ? T.typography.weight.emphasis : undefined });
    } else if (!magnify) stepLabels.push({ j: i - 1, Xf: X, y: rowY(i) });
  }

  // Total variance: a horizontal arrow below the total bar, from the base value to the total value.
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

  let height = overviewBottom + 2;
  if (magnify) {
    // Source frame around the steps' range in the overview (the zoomed part is marked, CH 4.5).
    const zx1 = X(zLo) - 3;
    const zx2 = X(zHi) + 3;
    const zy1 = rowY(1) - B / 2 - 2;
    const zy2 = rowY(n - 2) + B / 2 + 2;
    back.push({ kind: "rect", role: "zoom-box", x: zx1, y: zy1, w: zx2 - zx1, h: zy2 - zy1, stroke: C.marker.highlight, strokeWidth: 1 });

    // Panel rows: beside (same y as the overview rows) or below (own rows, names repeated).
    const pLeft = beside ? overviewRight + PANEL_GAP : labelCol;
    const pTop = beside ? 0 : overviewBottom + 8;
    const pRowY = (j: number) => (beside ? rowY(j + 1) : pTop + header + step * (j + 0.5));
    const pX0 = pLeft + room;
    const Xp = (v: number) => pX0 + (v - zLo) * o.ppu * k;
    const fTop = pRowY(0) - B / 2 - 2;
    const fBottom = pRowY(b.steps.length - 1) + B / 2 + 2;
    const rowsTop = fTop;
    const pRight = Xp(zHi) + room;

    // The framed panel; its origin line carries the axis-break glyph at the top, next to the caption.
    back.push({ kind: "rect", role: "magnifier-panel", group: "zoom", x: pLeft, y: fTop, w: pRight - pLeft, h: fBottom - fTop, stroke: C.marker.highlight, strokeWidth: 1 });
    back.push({ kind: "line", role: "axis", group: "zoom", x1: pX0, x2: pX0, y1: rowsTop, y2: fBottom, stroke: C.axis.category, strokeWidth: T.stroke.categoryAxisPx });
    const gy = rowsTop - 1;
    back.push({ kind: "path", role: "axis-break", group: "zoom", d: `M${pX0 - 3} ${gy - 8} L${pX0 + 3} ${gy - 6} L${pX0 - 3} ${gy - 3} L${pX0 + 3} ${gy - 1}`, stroke: C.axis.category, strokeWidth: 1 });
    marks.push({ kind: "text", role: "magnifier-caption", group: "zoom", x: pX0 + 7, y: rowsTop - box / 2 - 1, text: `Steps ×${k}`, anchor: "start", size, fill: C.text.secondary });
    b.steps.forEach((s, j) => {
      const { from, to } = spans[j]!;
      const { zero, key } = stepKey(s);
      const y = pRowY(j);
      if (j > 0) back.push({ kind: "line", role: "assisting-line", group: "zoom", x1: Xp(from), x2: Xp(from), y1: pRowY(j - 1) + B / 2, y2: y - B / 2, stroke: C.marker.assistingLine, strokeWidth: T.stroke.assistingLinePx });
      if (!zero) {
        const fill = impactFill(key, mode)!;
        bar("variance", j + 1, Xp(from), Xp(to), y, s.fc ? hatch(fill) : fill, s.fc ? fill : undefined, key, "zoom");
      }
      stepLabels.push({ j, Xf: Xp, y, group: "zoom" });
      if (!beside) category(j + 1, labelCol - 8, y, "zoom");
    });
    // Connectors join the two frames: beside, the source frame's right corners to the panel's left
    // corners (rows are aligned); below, the source frame's left edge down to the panel frame.
    // dashed, so the two links never read as a third, empty box between the frames
    const conn = (x1: number, y1: number, x2: number, y2: number) =>
      back.push({ kind: "line", role: "magnifier-connector", group: "zoom", x1, y1, x2, y2, stroke: C.marker.highlight, strokeWidth: 0.75, dash: "3 2" });
    if (beside) {
      conn(zx2, zy1, pLeft, fTop);
      conn(zx2, zy2, pLeft, fBottom);
    } else {
      conn(zx1, zy2, zx1, fTop);
      if (zx1 < pLeft || zx1 > pRight) conn(Math.min(zx1, pLeft), fTop, Math.max(zx1, pRight), fTop);
    }
    if (!beside) height = fBottom + 6;
  }

  // Step labels last: the natural side, else the far side of the bar, else inside the bar; a label
  // never touches an axis, connector, frame or assisting line.
  const lines = lineBoxes([...back, ...marks]);
  const clear = (m: Extract<Mark, { kind: "text" }>) => !lines.some((l) => overlaps(markBox(m), l, 0));
  for (const sl of stepLabels) {
    const s = b.steps[sl.j]!;
    const { key } = stepKey(s);
    const { from, to } = spans[sl.j]!;
    const xMin = sl.Xf(Math.min(from, to));
    const xMax = sl.Xf(Math.max(from, to));
    const text = valueLabels[sl.j + 1]!;
    const base = { kind: "text" as const, role: "variance-label", impact: key, group: sl.group, category: labels[sl.j + 1], y: sl.y, text, size, fill: impactText(key, mode) };
    const natural = s.delta >= 0 ? { ...base, x: xMax + 3, anchor: "start" as const } : { ...base, x: xMin - 3, anchor: "end" as const };
    const far = s.delta >= 0 ? { ...base, x: xMin - 3, anchor: "end" as const } : { ...base, x: xMax + 3, anchor: "start" as const };
    const inside = { ...base, x: (xMin + xMax) / 2, anchor: "middle" as const, fill: C.text.onAc };
    const fitsInside = textWidth(text, size) + 4 <= xMax - xMin;
    const pick = [natural, far, ...(fitsInside ? [inside] : [])].find(clear);
    if (!pick) warnings.push(`${labels[sl.j + 1]}: step label touches a line in every position`);
    marks.push(pick ?? natural);
  }

  const table = [["Row", "Value"], ...labels.map((l, i) => [l, valueLabels[i]!]), [b.variance.code, formatDelta(b.variance.value, o.scale)]];
  return { width: o.width, height, marks: [...back, ...marks], warnings, table, ppu: o.ppu };
}

const overflows = (l: Layout) => l.warnings.some((w) => w.startsWith("waterfall needs"));

/**
 * The largest px per unit (≤ o.ppu) at which the bridge fits its width, with the magnifier below the
 * overview once it no longer fits beside it. Use the smallest result of all bridges that are read
 * together (fitWaterfalls) so they keep one scale.
 */
export function fitWaterfallPpu(b: Bridge, o: WaterfallOptions): number {
  if (!overflows(layoutAt(b, o))) return o.ppu;
  const below = { ...o, magnifier: o.magnifier === "off" ? ("off" as const) : ("below" as const) };
  if (!overflows(layoutAt(b, below))) return o.ppu;
  let lo = 0;
  let hi = o.ppu;
  for (let i = 0; i < 30; i++) {
    const mid = (lo + hi) / 2;
    if (overflows(layoutAt(b, { ...below, ppu: mid }))) hi = mid;
    else lo = mid;
  }
  return lo;
}

/** One shared px per unit for bridges read together (e.g. two bridges on one phone page). */
export function fitWaterfalls(bridges: Bridge[], o: WaterfallOptions): number {
  return Math.min(o.ppu, ...bridges.map((b) => fitWaterfallPpu(b, o)));
}

/**
 * Variance waterfall (A-29). When it does not fit its width at the page scale, it shrinks the scale
 * (OURS; `fit: false` keeps the page scale and reports the overflow) and moves the magnifier below;
 * the result's `ppu` says which scale was drawn, and a warning names the change.
 */
export function layoutVarianceWaterfall(b: Bridge, o: WaterfallOptions): Layout {
  const first = layoutAt(b, o);
  if (o.fit === false || !overflows(first)) return first;
  const ppu = fitWaterfallPpu(b, o);
  // it overflowed beside: the magnifier goes below (unless it is switched off)
  const magnifier = o.magnifier === "off" ? "off" : "below";
  const l = layoutAt(b, { ...o, ppu, magnifier });
  if (ppu < o.ppu) l.warnings.push(`scale shrunk to ${Math.round((ppu / o.ppu) * 100)} % of the page scale to fit ${o.width} px: use the same px per unit for every bridge read with it (fitWaterfalls)`);
  return l;
}
