// Structure bar chart with variance tiers (behaviour contract §4): bars by category (sorted in the
// data layer), the reference as a downward triangle or an overlapped bar, an absolute Δ tier on
// the same px per unit, a relative Δ% pin tier on the "%" group, remainder gap, bold total.
import { tokens } from "../tokens.generated";
import { formatDelta, formatPercentDelta, formatValue, roundsToZero, type NumberScale } from "../format";
import { impactFill, impactKey, impactText, type ColorMode, type Impact } from "../impact";
import { clamp, lineBox, textWidth, fitLines, type Fill, type Layout, type Mark } from "./marks";
import type { Scenario } from "./columnTiers";

export type StructureRow = {
  category: string;
  AC?: number | null;
  FC?: number | null;
  PY?: number | null;
  PL?: number | null;
  BU?: number | null;
  /** Absolute variance from the model (Δ = 0 − reference for a discontinued member, never blank). */
  delta?: number | null;
  deltaImpact?: Impact | null;
  deltaPct?: number | null;
  deltaPctImpact?: Impact | null;
  /** "Other": drawn after a one-row gap. */
  remainder?: boolean;
  /** Bold, with a rule above. */
  total?: boolean;
};

export type StructureBarsOptions = {
  width: number;
  primary?: "AC" | "FC";
  reference?: Exclude<Scenario, "AC">;
  /** "triangle" (default): tip on the bar's top edge; "bar": overlapped behind, shifted up. */
  referenceStyle?: "triangle" | "bar";
  tiers?: ("delta" | "pct")[];
  ppu: number;
  pctPpu?: number;
  scale: NumberScale;
  pctDecimals?: number;
  polarity?: number;
  colorMode?: ColorMode;
  selected?: string;
  highlight?: { category: string; tier: "base" | "delta" | "pct" };
  outlierLimit?: number;
  rowStep?: number;
  fontSize?: number;
};

const T = tokens;
const C = T.color;
const TIER_GAP = 16;

export function layoutStructureBars(input: StructureRow[], o: StructureBarsOptions): Layout {
  const warnings: string[] = [];
  const size = o.fontSize ?? T.typography.size.label.px;
  const box = lineBox(size);
  const step = o.rowStep ?? Math.max(T.geometry.categoryStepPx.structureRow, box + 6);
  const B = step * T.geometry.barWidthRatio.absolute;
  const mode = o.colorMode ?? "color";
  const primary = o.primary ?? "AC";
  const ref = o.reference;
  const style = o.referenceStyle ?? "triangle";
  const tiers = ref ? (o.tiers ?? ["delta", "pct"]) : [];
  const pctDec = o.pctDecimals ?? 0;
  const limit = o.outlierLimit ?? 1;
  const pctPpu = o.pctPpu ?? 0;
  const refCode = ref ? `Δ${ref}` : "";
  const fin = (v: number | null | undefined) => {
    if (v == null) return null;
    if (Number.isFinite(v)) return v;
    warnings.push("non-finite value dropped");
    return null;
  };
  const rows = input.map((r) => ({ ...r, P: fin(r[primary]), R: ref ? fin(r[ref]) : null, delta: fin(r.delta), deltaPct: fin(r.deltaPct) }));

  // Rows top to bottom: remainder after a one-row gap, total after half a row with a rule.
  const ys: number[] = [];
  const header = box + 6;
  let y = header;
  rows.forEach((r, i) => {
    if (r.remainder && i > 0) y += step * T.geometry.remainderGapRatio;
    if (r.total && i > 0) y += step / 2;
    ys.push(y + step / 2);
    y += step;
  });
  const height = y + 4;

  // Horizontal extents per tier in px, each with label room on the side its bars grow.
  const labelsP = rows.map((r) => formatValue(r.P, o.scale));
  const labelsD = rows.map((r) => (r.delta == null ? "" : formatDelta(r.delta, o.scale)));
  const labelsPct = rows.map((r) => formatPercentDelta(r.deltaPct, pctDec));
  const span = (vals: (number | null)[], ppu: number) => ({
    right: Math.max(0, ...vals.map((v) => (v == null ? 0 : v * ppu))),
    left: Math.max(0, ...vals.map((v) => (v == null ? 0 : -v * ppu))),
  });
  const wMax = (labels: string[]) => Math.max(0, ...labels.map((s) => textWidth(s, size))) + 4;
  const labelCol = Math.min(Math.max(0, ...rows.map((r) => textWidth(r.category, size))) + 8, o.width * 0.3);
  const base = span(rows.flatMap((r) => [r.P, r.R]), o.ppu);
  const delta = span(rows.map((r) => r.delta), o.ppu);
  const pct = span(rows.map((r) => (r.deltaPct == null ? null : clamp(r.deltaPct, -limit, limit))), pctPpu);
  // label room only on the side where a tier's labels go (N/A and zero labels sit right of the axis)
  const sides = (vals: (number | null)[], ext: { left: number; right: number }, labels: string[], head: number) => {
    const neg = labels.filter((_, i) => (vals[i] ?? 0) < 0);
    const pos = labels.filter((_, i) => (vals[i] ?? 0) >= 0);
    return { left: ext.left + (neg.length ? wMax(neg) + head : 0), right: ext.right + (pos.length ? wMax(pos) + head : 0) };
  };
  const parts = [
    { key: "base" as const, left: base.left + (base.left ? wMax(labelsP) : 0), right: base.right + wMax(labelsP) },
    ...(tiers.includes("delta") ? [{ key: "delta" as const, ...sides(rows.map((r) => r.delta), delta, labelsD, 0) }] : []),
    ...(tiers.includes("pct") ? [{ key: "pct" as const, ...sides(rows.map((r) => r.deltaPct), pct, labelsPct, 8) }] : []),
  ];
  const need = labelCol + parts.reduce((s, p) => s + p.left + p.right, 0) + TIER_GAP * (parts.length - 1);
  const spare = o.width - need;
  if (spare < 0) warnings.push(`tiers need ${Math.ceil(need)} px but the chart has ${o.width} px: stack the tiers under the bars`);
  const gap = TIER_GAP + (parts.length > 1 ? Math.max(0, spare) / (parts.length - 1) : 0);
  const x0: Record<string, number> = {};
  let x = labelCol;
  parts.forEach((p, k) => {
    x0[p.key] = x + p.left;
    x += p.left + p.right + (k < parts.length - 1 ? gap : 0);
  });

  const back: Mark[] = [];
  const marks: Mark[] = [];
  const hatch = (stripe: string): Fill => ({ hatch: stripe });
  const notation = (sc: Scenario) =>
    sc === "AC" ? { fill: C.scenario.ac as Fill, stroke: undefined as string | undefined }
      : sc === "PY" ? { fill: C.scenario.py as Fill, stroke: undefined }
      : sc === "FC" ? { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke as string }
      : { fill: C.scenario.pl.fill as Fill, stroke: C.scenario.pl.stroke as string };
  const top = header;
  const bottom = height - 4;

  const sel = rows.findIndex((r) => r.category === o.selected);
  if (sel >= 0) back.push({ kind: "rect", role: "assisting-area", x: 0, y: ys[sel]! - step / 2, w: o.width, h: step, fill: C.marker.assistingArea, category: o.selected });
  back.push({ kind: "line", role: "axis", x1: x0.base!, x2: x0.base!, y1: top, y2: bottom, stroke: C.axis.category, strokeWidth: T.stroke.categoryAxisPx });
  for (const t of ["delta", "pct"] as const) {
    if (x0[t] == null || !ref) continue;
    const ax = x0[t]!;
    const role = `axis-${ref}`;
    if (ref === "PY") back.push({ kind: "line", role, x1: ax, x2: ax, y1: top, y2: bottom, stroke: C.axis.pyReference, strokeWidth: T.stroke.varianceAxis.pyWidthPx });
    else if (ref === "FC") back.push({ kind: "rect", role, x: ax - 2, y: top, w: 4, h: bottom - top, fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke, strokeWidth: 0.5 });
    else {
      const d = (T.stroke.varianceAxis.plGapPx + T.stroke.varianceAxis.plLinePx) / 2;
      for (const dx of [-d, d]) back.push({ kind: "line", role, x1: ax + dx, x2: ax + dx, y1: top, y2: bottom, stroke: C.axis.plReference, strokeWidth: T.stroke.varianceAxis.plLinePx });
    }
    marks.push({ kind: "text", role: "tier-name", x: ax, y: box / 2 + 1, text: t === "delta" ? refCode : `${refCode}%`, anchor: "middle", size, fill: C.text.primary });
  }

  const ring = (cx: number, cy: number, text: string, category: string) =>
    marks.push({ kind: "ellipse", role: "marker-ellipse", cx, cy, rx: textWidth(text, size) / 2 + 6, ry: box / 2 + 3, stroke: C.marker.highlight, strokeWidth: T.stroke.highlightEllipsePx, category });
  const tri = clamp(T.geometry.triangleSizeRatio * B, T.geometry.triangleSizePx.min, T.geometry.triangleSizePx.max);
  const off = T.geometry.referenceOffsetRatio.bar * B;
  const legend: { text: string; x: number }[] = [];

  rows.forEach((r, i) => {
    const cy = ys[i]!;
    const bx = x0.base!;
    const weight = r.total ? T.typography.weight.emphasis : undefined;
    if (r.total) back.push({ kind: "line", role: "axis", x1: 0, x2: o.width, y1: cy - step / 2 - 1, y2: cy - step / 2 - 1, stroke: C.table.rule, strokeWidth: 1 });
    // reference: overlapped bar behind (shifted up) or triangle pointing down onto the bar's top edge
    if (ref && r.R != null) {
      const nt = notation(ref);
      if (style === "bar") marks.push({ kind: "rect", role: `bar-${ref}`, category: r.category, x: Math.min(bx, bx + r.R * o.ppu), y: cy - B / 2 - off, w: Math.abs(r.R) * o.ppu, h: B, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? 1 : undefined });
    }
    if (r.P != null) {
      const nt = notation(primary);
      marks.push({ kind: "rect", role: `bar-${primary}`, category: r.category, x: Math.min(bx, bx + r.P * o.ppu), y: cy - B / 2, w: Math.abs(r.P) * o.ppu, h: B, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? 1 : undefined });
    }
    if (ref && r.R != null && style === "triangle") {
      const tx = bx + r.R * o.ppu;
      const ty = cy - B / 2;
      const nt = notation(ref);
      marks.push({ kind: "path", role: `triangle-${ref}`, category: r.category, d: `M${tx} ${ty} L${tx - tri / 2} ${ty - tri * 0.87} L${tx + tri / 2} ${ty - tri * 0.87} Z`, fill: nt.fill, stroke: nt.stroke ?? C.scenario.ac, strokeWidth: 0.75 });
    }
    if (i === 0) {
      if (r.P != null) legend.push({ text: primary, x: bx + (r.P * o.ppu) / 2 });
      if (ref && r.R != null) legend.push({ text: ref, x: bx + r.R * o.ppu });
    }
    const reach = Math.max(r.P ?? 0, r.R ?? 0) * o.ppu;
    const neg = Math.min(r.P ?? 0, r.R ?? 0) * o.ppu;
    if (r.P != null) {
      const text = labelsP[i]!;
      const lx = r.P >= 0 ? bx + reach + 3 : bx + neg - 3;
      marks.push({ kind: "text", role: "label", category: r.category, x: lx, y: cy, text, anchor: r.P >= 0 ? "start" : "end", size, fill: C.text.primary, weight });
      if (o.highlight?.category === r.category && o.highlight.tier === "base") ring(lx + (r.P >= 0 ? 1 : -1) * textWidth(text, size) / 2, cy, text, r.category);
    }
    if (x0.delta != null && r.delta != null) {
      const d = r.delta;
      const zero = roundsToZero(d, o.scale);
      const key = impactKey(d, { impact: r.deltaImpact, polarity: o.polarity, isZero: zero });
      const ax = x0.delta;
      if (!zero) marks.push({ kind: "rect", role: "variance", impact: key, category: r.category, x: d > 0 ? ax : ax + d * o.ppu, y: cy - B / 2, w: Math.max(1, Math.abs(d) * o.ppu), h: B, fill: primary === "FC" ? hatch(impactFill(key, mode)!) : impactFill(key, mode) });
      const text = labelsD[i]!;
      const lx = d >= 0 || zero ? ax + Math.max(0, d) * o.ppu + 3 : ax + d * o.ppu - 3;
      marks.push({ kind: "text", role: "variance-label", impact: key, category: r.category, x: lx, y: cy, text, anchor: d >= 0 || zero ? "start" : "end", size, fill: impactText(key, mode), weight });
      if (o.highlight?.category === r.category && o.highlight.tier === "delta") ring(lx + (d >= 0 ? 1 : -1) * textWidth(text, size) / 2, cy, text, r.category);
    }
    if (x0.pct != null) {
      const ax = x0.pct;
      const v = r.deltaPct;
      const text = labelsPct[i]!;
      if (v == null) {
        marks.push({ kind: "text", role: "variance-label", impact: "none", category: r.category, x: ax + 4, y: cy, text, anchor: "start", size, fill: C.text.primary, weight });
      } else {
        const zero = roundsToZero(v, { factor: 0.01, decimals: pctDec });
        const key = impactKey(v, { impact: r.deltaPctImpact, polarity: o.polarity, isZero: zero });
        const end = ax + clamp(v, -limit, limit) * pctPpu;
        const outlier = Math.abs(v) > limit;
        const head = clamp(T.geometry.pin.headRatio * B, T.geometry.pin.headPx.min, T.geometry.pin.headPx.max);
        if (!zero) {
          const stem = clamp(T.geometry.pin.thicknessRatio * B, T.geometry.pin.stemPx.min, T.geometry.pin.stemPx.max);
          const fill = impactFill(key, mode)!;
          marks.push({ kind: "rect", role: "pin", impact: key, category: r.category, x: Math.min(ax, end), y: cy - stem / 2, w: Math.abs(end - ax), h: stem, fill });
          if (outlier) {
            warnings.push(`${r.category}: ${refCode}% ${text} truncated as an outlier`);
            const dir = v > 0 ? 1 : -1;
            marks.push({ kind: "path", role: "outlier", impact: key, category: r.category, d: `M${end} ${cy - 5} L${end} ${cy + 5} L${end + dir * 7} ${cy} Z`, fill });
          } else {
            const nt = notation(primary);
            marks.push({ kind: "rect", role: "pin-head", category: r.category, x: end - head / 2, y: cy - head / 2, w: head, h: head, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? 1 : undefined });
          }
        }
        const reachPx = (outlier ? 8 : head / 2) + 3;
        const pos = v >= 0 || zero;
        const lx = pos ? Math.max(end, ax) + reachPx : end - reachPx;
        marks.push({ kind: "text", role: "variance-label", impact: key, category: r.category, x: lx, y: cy, text, anchor: pos ? "start" : "end", size, fill: impactText(key, mode), weight });
        if (o.highlight?.category === r.category && o.highlight.tier === "pct") ring(lx + (pos ? 1 : -1) * textWidth(text, size) / 2, cy, text, r.category);
      }
    }
    { const lines = fitLines(r.category, size, labelCol - 8, step); marks.push({ kind: "text", role: "category", category: r.category, x: labelCol - 8, y: cy, text: lines.length > 1 ? r.category : lines[0]!, lines: lines.length > 1 ? lines : undefined, anchor: "end", size, fill: C.text.primary, weight }); }
    marks.push({ kind: "rect", role: "hit", category: r.category, x: 0, y: cy - step / 2, w: o.width, h: step, tooltip: `${r.category}: ${primary} ${labelsP[i]}${ref ? `, ${refCode} ${labelsD[i]}, ${refCode}% ${labelsPct[i]}` : ""}` });
  });

  // Scenario names once, above the top row at its marks, at least 1 em apart.
  legend.sort((a, b) => a.x - b.x);
  let lastRight = -Infinity;
  for (const l of legend) {
    const w = textWidth(l.text, size);
    const cx = Math.max(l.x, lastRight + size + w / 2);
    lastRight = cx + w / 2;
    marks.push({ kind: "text", role: "legend", x: cx, y: box / 2 + 1, text: l.text, anchor: "middle", size, fill: C.text.primary });
  }

  const table = [
    ["Category", primary, ...(ref ? [ref] : []), ...(tiers.includes("delta") ? [refCode] : []), ...(tiers.includes("pct") ? [`${refCode}%`] : [])],
    ...rows.map((r, i) => [r.category, labelsP[i]!, ...(ref ? [formatValue(r.R, o.scale)] : []), ...(tiers.includes("delta") ? [labelsD[i]!] : []), ...(tiers.includes("pct") ? [labelsPct[i]!] : [])]),
  ];
  return { width: o.width, height, marks: [...back, ...marks], warnings, table };
}

/** Extents for the page registry: bars and Δ join the unit, pins join "%". */
export function structureExtents(rows: StructureRow[], o: Pick<StructureBarsOptions, "primary" | "reference" | "outlierLimit">) {
  const span = (vals: (number | null | undefined)[]) => {
    const nums = vals.filter((v): v is number => v != null && Number.isFinite(v));
    return { min: Math.min(0, ...nums), max: Math.max(0, ...nums) };
  };
  const lim = o.outlierLimit ?? 1;
  return {
    base: span(rows.flatMap((r) => [r[o.primary ?? "AC"], o.reference ? r[o.reference] : null])),
    delta: span(rows.map((r) => r.delta)),
    pct: span(rows.map((r) => (r.deltaPct == null ? null : clamp(r.deltaPct, -lim, lim)))),
  };
}
