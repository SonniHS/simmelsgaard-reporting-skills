// Column chart over time with variance tiers (behaviour contract §2 and §3): scenario columns with
// an overlapped reference and an optional triangle, an absolute Δ tier on the same px per unit, a
// relative Δ% pin tier on the "%" group, end legend at the marks, and px-extent alignment for a
// Total chart beside it. Pure: rows + px per unit in, marks out.
import { tokens } from "../tokens.generated";
import { formatDelta, formatPercentDelta, formatValue, roundsToZero, type NumberScale } from "../format";
import { impactFill, impactKey, impactText, type ColorMode, type Impact } from "../impact";
import { clamp, lineBox, markBox, overlaps, periodLabels, shortPinWarning, spreadLabels, textWidth, type Fill, type Layout, type Mark } from "./marks";
import { pinClip, pinScale, pinScaleBand } from "../scale";

export type Scenario = "AC" | "FC" | "PY" | "PL" | "BU";

export type PeriodRow = {
  period: string;
  /** Second label line, e.g. the year; drawn under the first period and where it changes, only when it varies. */
  period2?: string;
  /** A Total (or full-year) category inside this chart: its labels win every collision. */
  total?: boolean;
  /** True up to and including the last closed period; omit to use AC where present, else FC. */
  closed?: boolean;
  AC?: number | null;
  FC?: number | null;
  PY?: number | null;
  PL?: number | null;
  BU?: number | null;
  /** Absolute variance from the model (e.g. AC&FC − BU). Never computed here. */
  delta?: number | null;
  deltaImpact?: Impact | null;
  /** Relative variance from the model as a fraction; null = N/A (no pin). */
  deltaPct?: number | null;
  deltaPctImpact?: Impact | null;
  /** A second absolute variance (e.g. AC&FC − PY) for the `delta2` tier, from the model. */
  delta2?: number | null;
  delta2Impact?: Impact | null;
};

export type TierKey = "pct" | "delta" | "delta2" | "base";
export type TierPx = { up: number; down: number };

export type ColumnTiersOptions = {
  width: number;
  /** Overlapped reference column behind the primary. With "FC" the primary is AC only. */
  reference: Exclude<Scenario, "AC">;
  /** A third scenario drawn as a triangle at the primary column's left edge. */
  triangle?: Exclude<Scenario, "AC" | "FC">;
  /**
   * Variance tiers above the base, top to bottom. Default: Δ% and Δ. `delta2` adds a second absolute
   * tier against `reference2` (e.g. ΔBU and ΔPY on one month chart), on the base px per unit.
   */
  tiers?: ("pct" | "delta" | "delta2")[];
  /** Reference of the `delta2` tier (its axis notation and name, e.g. "PY"). */
  reference2?: Exclude<Scenario, "AC">;
  /** px per raw unit from the page registry; the base and the Δ tier share it. */
  ppu: number;
  /**
   * px per 1.0 (= 100 %) from the page's "%" group (`pinScale` over every pin tier of the page).
   * Default: this chart's own pin tier, so the largest |Δ%| fills 90 % of `pctTierPx`.
   */
  pctPpu?: number;
  /** Extent of the pin tier in px (OURS default 48 for column charts). */
  pctTierPx?: number;
  scale: NumberScale;
  pctDecimals?: number;
  polarity?: number;
  colorMode?: ColorMode;
  /** Category behind which the assisting band runs through all tiers (default in a page: the last closed month). */
  selected?: string;
  /** Categories whose labels the key message cites: never thinned. */
  keep?: string[];
  /** Ring the value label the key message cites (UN 5.1). */
  highlight?: { category: string; tier: TierKey };
  /** Pins beyond ±limit (fraction) are truncated with an outlier marker. Default 1 (±100 %). */
  outlierLimit?: number;
  /** A pin over `outlierRatio` × the next-largest |Δ%| is an outlier: clipped, the tier scaled from the others (OURS, default 3; 0 = off). */
  outlierRatio?: number;
  /** Minimum px above and below each tier's zero line: pass the union with a Total chart. */
  minTierPx?: Partial<Record<TierKey, TierPx>>;
  /** Draw a scale band (UN 5.2) at this round raw value: required on every chart of the unit when one chart has its own scale. */
  scaleBand?: number;
  /** The same for the absolute Δ tier (a smaller round value that fits it): a Total on its own scale shows it in every tier. */
  deltaScaleBand?: number;
  /**
   * Scaling marker of the pin tier (UN 5.2 / CH 4.3), required when this tier's % scale differs from
   * the page's other % tiers (OURS): a round value as a fraction (0.1 = 10 %), or "auto" for the
   * value `pinScaleBand` picks (25–60 % of the tier). `pagePinScales` says when scales differ.
   */
  pctScaleBand?: number | "auto";
  /** Name of the primary series in the end legend, e.g. "AC&FC" for a Total of closed and open months. */
  primaryLabel?: string;
  /** Scenario names at the end of the series. Default true. */
  legend?: boolean;
  fontSize?: number;
};

export type ColumnTiersLayout = Layout & {
  tiers: Record<TierKey, TierPx & { y0: number }>;
  step: number;
};

const T = tokens;
const PIN_ROLES = new Set(["pin", "pin-head", "outlier"]);
const TIER_GAP = 8;

type Primary = { scenario: "AC" | "FC"; value: number } | null;

export function layoutColumnTiers(input: PeriodRow[], o: ColumnTiersOptions): ColumnTiersLayout {
  const warnings: string[] = [];
  const size = o.fontSize ?? T.typography.size.label.px;
  const box = lineBox(size);
  const room = box + 2;
  const pctDec = o.pctDecimals ?? 1; // one decimal by default, in every route
  const limit = pinClip(input.map((r) => r.deltaPct), o.outlierLimit ?? 1, o.outlierRatio ?? 3);
  const mode = o.colorMode ?? "color";
  const tierList = o.tiers ?? ["pct", "delta"];
  if (tierList.includes("delta2") && !o.reference2) warnings.push("delta2 tier without reference2");
  const order: TierKey[] = [...(["pct", "delta", "delta2"] as const).filter((t) => tierList.includes(t) && (t !== "delta2" || o.reference2)), "base"];
  const refCode = `Δ${o.reference}`;
  const ref2Code = o.reference2 ? `Δ${o.reference2}` : "";
  const tierName: Record<TierKey, string> = { pct: `${refCode}%`, delta: refCode, delta2: ref2Code, base: "" };
  const refOf = (t: TierKey) => (t === "delta2" ? o.reference2! : o.reference);

  const finite = (v: number | null | undefined): number | null => {
    if (v == null) return null;
    if (Number.isFinite(v)) return v;
    warnings.push("non-finite value dropped");
    return null;
  };
  const rows = input.map((r) => ({
    ...r,
    AC: finite(r.AC), FC: finite(r.FC), PY: finite(r.PY), PL: finite(r.PL), BU: finite(r.BU),
    delta: finite(r.delta), deltaPct: finite(r.deltaPct), delta2: finite(r.delta2),
  }));
  const hasClosed = rows.some((r) => r.closed != null);
  const primaryOf = (r: (typeof rows)[number]): Primary => {
    if (o.reference === "FC") return r.AC != null && (!hasClosed || r.closed) ? { scenario: "AC", value: r.AC } : null;
    if (hasClosed) {
      if (r.closed) return r.AC != null ? { scenario: "AC", value: r.AC } : null;
      return r.FC != null ? { scenario: "FC", value: r.FC } : null; // a partial AC of the open period is not drawn
    }
    if (r.AC != null) return { scenario: "AC", value: r.AC };
    return r.FC != null ? { scenario: "FC", value: r.FC } : null;
  };
  const prim = rows.map(primaryOf);
  const n = Math.max(rows.length, 1);

  // Labels decide the margins, never the plot width (contract §1, label clearance).
  const lastPrim = [...prim].reverse().find((p) => p != null) ?? null;
  const anyAC = prim.some((p) => p?.scenario === "AC");
  const primaryName = o.primaryLabel ?? (lastPrim?.scenario === "FC" ? (anyAC ? "AC&FC" : "FC") : "AC");
  const legendOn = o.legend !== false && rows.length > 0;
  const legendNames = legendOn ? [primaryName, o.reference, ...(o.triangle ? [o.triangle] : [])] : [];
  const legendW = legendNames.length ? Math.max(...legendNames.map((s) => textWidth(s, size))) + 10 : 0;
  const tierNameW = order.length > 1 ? Math.max(...order.map((t) => textWidth(tierName[t], size))) + 8 : 0;

  const valueLabel = (i: number) => formatValue(prim[i]?.value, o.scale);
  const deltaLabel = (i: number) => (rows[i]!.delta == null ? "" : formatDelta(rows[i]!.delta, o.scale));
  const delta2Label = (i: number) => (rows[i]!.delta2 == null ? "" : formatDelta(rows[i]!.delta2, o.scale));
  const pctLabel = (i: number) => formatPercentDelta(rows[i]!.deltaPct, pctDec);
  const edgeW = (i: number) =>
    Math.max(
      textWidth(valueLabel(i), size),
      order.includes("delta") ? textWidth(deltaLabel(i), size) : 0,
      order.includes("delta2") ? textWidth(delta2Label(i), size) : 0,
      order.includes("pct") ? textWidth(pctLabel(i), size) : 0,
    );
  const bandLabel = o.scaleBand ? formatValue(o.scaleBand, o.scale) : "";
  let left = Math.max(tierNameW, o.scaleBand ? textWidth(bandLabel, size) + 4 : 0);
  let right = legendW;
  let step = (o.width - left - right) / n;
  left += Math.max(0, edgeW(0) / 2 - step / 2);
  right = Math.max(right, Math.max(0, edgeW(n - 1) / 2 - step / 2));
  step = Math.max(1, (o.width - left - right) / n);
  const plotW = step * n;
  const B = step * T.geometry.barWidthRatio.absolute;
  const off = T.geometry.referenceOffsetRatio.column * B;
  const cx = (i: number) => left + step * (i + 0.5);

  // Tier extents in px (sized to the data, then the union passed in for alignment).
  const ext = (vals: (number | null | undefined)[], ppu: number): TierPx => {
    let up = 0;
    let down = 0;
    for (const v of vals) if (v != null) { up = Math.max(up, v * ppu); down = Math.max(down, -v * ppu); }
    return { up, down };
  };
  // the pin tier has its own scale: the largest |Δ%| fills 90 % of the tier (shared across the page
  // through pinScale); the head is small (headPx.min) and sits at the stem end
  const pctTierPx = o.pctTierPx ?? 48;
  const pctPpu = o.pctPpu ?? pinScale([{ ...columnTiersExtents(rows, o).pct, tierPx: pctTierPx }]);
  const headPx = T.geometry.pin.headPx.min;
  // a pin that does not round to zero is at least head/2 + 2 px long, so its head never sits on the axis
  const pinLen = (v: number) => {
    const len = Math.abs(clamp(v, -limit, limit)) * pctPpu;
    return roundsToZero(v, { factor: 0.01, decimals: pctDec }) ? 0 : Math.max(len, headPx / 2 + 2);
  };
  const raw: Record<TierKey, TierPx> = {
    base: ext([...rows.flatMap((r, i) => [prim[i]?.value, r[o.reference], o.triangle ? r[o.triangle] : null]), o.scaleBand], o.ppu),
    delta: ext(rows.map((r) => r.delta), o.ppu),
    delta2: ext(rows.map((r) => r.delta2), o.ppu),
    pct: ext(rows.map((r) => (r.deltaPct == null ? null : Math.sign(r.deltaPct) * pinLen(r.deltaPct))), 1),
  };
  // a triangle reaches half its size above (and below) its value
  const triHalf = clamp(T.geometry.triangleSizeRatio * B, T.geometry.triangleSizePx.min, T.geometry.triangleSizePx.max) / 2;
  if (o.triangle)
    for (const r of rows) {
      const v = r[o.triangle];
      if (v != null) { raw.base.up = Math.max(raw.base.up, v * o.ppu + triHalf); raw.base.down = Math.max(raw.base.down, -v * o.ppu + triHalf); }
    }
  const tiers = {} as ColumnTiersLayout["tiers"];
  let cursor = 0;
  for (const t of order) {
    const min = o.minTierPx?.[t];
    const up = Math.max(raw[t].up, min?.up ?? 0);
    const down = Math.max(raw[t].down, min?.down ?? 0);
    // pin labels sit beyond the head (or the outlier marker): their tier needs that much more room
    const r = t === "pct" ? room + 9 : room;
    const y0 = cursor + r + up;
    tiers[t] = { up, down, y0 };
    cursor = y0 + down + r + (t === "base" ? 0 : TIER_GAP);
  }
  for (const t of ["pct", "delta", "delta2"] as const) if (!tiers[t]) tiers[t] = { up: 0, down: 0, y0: tiers.base.y0 };
  const catY = cursor + box / 2 + 2;
  const years = rows.map((r) => r.period2 ?? "");
  const twoYears = new Set(years.filter(Boolean)).size > 1;
  const catRows = periodLabels(rows.map((r) => r.period), size, step).rows;
  const height = cursor + box * (catRows + (twoYears ? 1 : 0)) + 4;
  if (tiers.base.up + tiers.base.down < 24) warnings.push("base tier below 24 px: give this chart its own scale group with a scale band");

  const marks: Mark[] = [];
  const back: Mark[] = [];
  const C = T.color;
  const hatch = (stripe: string): Fill => ({ hatch: stripe });
  const notation = (sc: Scenario): { fill: Fill; stroke?: string } =>
    sc === "AC" ? { fill: C.scenario.ac }
      : sc === "PY" ? { fill: C.scenario.py }
      : sc === "FC" ? { fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke }
      : { fill: C.scenario.pl.fill, stroke: C.scenario.pl.stroke };

  // 1. assisting area behind the selected category, through all tiers
  const selIdx = rows.findIndex((r) => r.period === o.selected);
  if (selIdx >= 0) back.push({ kind: "rect", role: "assisting-area", x: cx(selIdx) - step / 2, y: 0, w: step, h: height, fill: C.marker.assistingArea, category: o.selected });

  // 2. axes, before the marks
  back.push({ kind: "line", role: "axis", x1: left, x2: left + plotW, y1: tiers.base.y0, y2: tiers.base.y0, stroke: C.axis.category, strokeWidth: T.stroke.categoryAxisPx });
  for (const t of order) {
    if (t === "base") continue;
    const y = tiers[t].y0;
    const tref = refOf(t);
    const role = `axis-${tref}`;
    if (tref === "PY") back.push({ kind: "line", role, x1: left, x2: left + plotW, y1: y, y2: y, stroke: C.axis.pyReference, strokeWidth: T.stroke.varianceAxis.pyWidthPx });
    else if (tref === "FC") back.push({ kind: "rect", role, x: left, y: y - 2, w: plotW, h: 4, fill: hatch(C.scenario.fc.stripe), stroke: C.scenario.fc.stroke, strokeWidth: 0.5 });
    else {
      const d = (T.stroke.varianceAxis.plGapPx + T.stroke.varianceAxis.plLinePx) / 2;
      for (const dy of [-d, d]) back.push({ kind: "line", role, x1: left, x2: left + plotW, y1: y + dy, y2: y + dy, stroke: C.axis.plReference, strokeWidth: T.stroke.varianceAxis.plLinePx });
    }
    marks.push({ kind: "text", role: "tier-name", x: left - 8, y, text: tierName[t], anchor: "end", size, fill: C.text.primary });
  }

  const valueLabels = rows.map((_, i) => valueLabel(i));
  // Label candidates per tier; placed after all marks exist (collision test against every mark of the tier).
  type Cand = { i: number; t: TierKey; m: Extract<Mark, { kind: "text" }>; above: boolean };
  const cands: Cand[] = [];
  const label = (i: number, t: TierKey, m: Extract<Mark, { kind: "text" }>, above: boolean) => cands.push({ i, t, m, above });

  const ring = (cxL: number, cyL: number, text: string, category: string) =>
    marks.push({ kind: "ellipse", role: "marker-ellipse", cx: cxL, cy: cyL, rx: textWidth(text, size) / 2 + 6, ry: box / 2 + 3, stroke: C.marker.highlight, strokeWidth: T.stroke.highlightEllipsePx, category });

  const triSize = clamp(T.geometry.triangleSizeRatio * B, T.geometry.triangleSizePx.min, T.geometry.triangleSizePx.max);
  const y0 = tiers.base.y0;
  const yOf = (v: number) => y0 - v * o.ppu;
  rows.forEach((r, i) => {
    const c = cx(i);
    const p = prim[i];
    const refV = r[o.reference];
    // 3. reference behind, shifted left
    if (refV != null && !(o.reference === "FC" && p?.scenario === "FC")) {
      const nt = notation(o.reference);
      marks.push({ kind: "rect", role: `col-${o.reference}`, category: r.period, x: c - B / 2 - off / 2, y: Math.min(yOf(refV), y0), w: B, h: Math.abs(refV) * o.ppu, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? T.stroke.outlinePx : undefined });
    }
    // primary in front, shifted right
    if (p) {
      const nt = notation(p.scenario);
      marks.push({ kind: "rect", role: `col-${p.scenario}`, category: r.period, x: c - B / 2 + off / 2, y: Math.min(yOf(p.value), y0), w: B, h: Math.abs(p.value) * o.ppu, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? T.stroke.outlinePx : undefined });
    }
    // triangle: tip on the primary column's left edge, pointing right
    const triV = o.triangle ? r[o.triangle] : null;
    if (o.triangle && triV != null) {
      const xl = c - B / 2 + off / 2;
      const y = yOf(triV);
      const w = triSize * 0.87;
      const nt = notation(o.triangle);
      marks.push({ kind: "path", role: `triangle-${o.triangle}`, category: r.period, d: `M${xl} ${y} L${xl - w} ${y - triSize / 2} L${xl - w} ${y + triSize / 2} Z`, fill: nt.fill, stroke: nt.stroke ?? C.scenario.ac, strokeWidth: 0.75 });
    }
    // value label above the taller of primary and reference (below for negatives)
    if (p) {
      const tops = [p.value, refV ?? 0, triV == null ? 0 : triV + triHalf / o.ppu];
      const bottoms = [p.value, refV ?? 0, triV == null ? 0 : triV - triHalf / o.ppu];
      const y = p.value >= 0 ? yOf(Math.max(...tops)) - box / 2 - 1 : yOf(Math.min(...bottoms)) + box / 2 + 1;
      label(i, "base", { kind: "text", role: "label", category: r.period, x: c + off / 2, y, text: valueLabels[i]!, anchor: "middle", size, fill: C.text.primary }, p.value >= 0);
    }
    // 5. absolute variances (Δ, and Δ2 against reference2): same width and px per unit as the base
    for (const t of ["delta", "delta2"] as const) {
      const d = t === "delta" ? r.delta : r.delta2;
      if (!order.includes(t) || d == null) continue;
      const zero = roundsToZero(d, o.scale);
      const key = impactKey(d, { impact: t === "delta" ? r.deltaImpact : r.delta2Impact, polarity: o.polarity, isZero: zero });
      const ty = tiers[t].y0;
      if (!zero) {
        const fill = impactFill(key, mode)!;
        marks.push({ kind: "rect", role: "variance", impact: key, category: r.period, x: c - B / 2, y: d > 0 ? ty - d * o.ppu : ty, w: B, h: Math.max(1, Math.abs(d) * o.ppu), fill: p?.scenario === "FC" ? hatch(fill) : fill, stroke: p?.scenario === "FC" ? fill : undefined, strokeWidth: p?.scenario === "FC" ? 0.75 : undefined });
      }
      const text = formatDelta(d, o.scale);
      const y = d >= 0 || zero ? ty - Math.max(0, d) * o.ppu - box / 2 - 1 : ty - d * o.ppu + box / 2 + 1;
      label(i, t, { kind: "text", role: "variance-label", impact: key, category: r.period, x: c, y, text, anchor: "middle", size, fill: impactText(key, mode) }, d >= 0 || zero);
    }
    // 6. relative variance pins on the "%" group; N/A draws no pin but keeps its label
    if (order.includes("pct")) {
      const v = r.deltaPct;
      const ty = tiers.pct.y0;
      const text = pctLabel(i);
      if (v == null) {
        label(i, "pct", { kind: "text", role: "variance-label", impact: "none", category: r.period, x: c, y: ty - box / 2 - 2, text, anchor: "middle", size, fill: C.text.primary }, true);
      } else {
        const zero = roundsToZero(v, { factor: 0.01, decimals: pctDec });
        const key = impactKey(v, { impact: r.deltaPctImpact, polarity: o.polarity, isZero: zero });
        const outlier = Math.abs(v) > limit;
        const end = ty - Math.sign(v) * pinLen(v);
        if (zero && p) {
          // a Δ% that rounds to zero keeps a baseline marker: the head on the axis, uncoloured
          const nt = notation(p.scenario);
          marks.push({ kind: "rect", role: "pin-head", impact: "none", category: r.period, x: c - headPx / 2, y: ty - headPx / 2, w: headPx, h: headPx, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? T.stroke.outlinePx : undefined });
        }
        if (!zero) {
          const stem = clamp(T.geometry.pin.thicknessRatio * B, T.geometry.pin.stemPx.min, T.geometry.pin.stemPx.max);
          const fill = impactFill(key, mode)!;
          marks.push({ kind: "rect", role: "pin", impact: key, category: r.period, x: c - stem / 2, y: Math.min(ty, end), w: stem, h: Math.abs(end - ty), fill });
          if (outlier) {
            warnings.push(`${r.period}: ${refCode}% ${text} truncated as an outlier`);
            const dir = v > 0 ? -1 : 1;
            marks.push({ kind: "path", role: "outlier", impact: key, category: r.period, d: `M${c - 5} ${end} L${c + 5} ${end} L${c} ${end + dir * 7} Z`, fill });
          } else if (p) {
            const head = headPx;
            const nt = notation(p.scenario);
            marks.push({ kind: "rect", role: "pin-head", category: r.period, x: c - head / 2, y: end - head / 2, w: head, h: head, fill: nt.fill, stroke: nt.stroke, strokeWidth: nt.stroke ? T.stroke.outlinePx : undefined });
          }
        }
        const reach = (outlier ? 8 : headPx / 2) + (zero ? headPx / 2 : 0) + 1;
        const y = v >= 0 || zero ? Math.min(end, ty) - reach - box / 2 : end + reach + box / 2;
        label(i, "pct", { kind: "text", role: "variance-label", impact: key, category: r.period, x: c, y, text, anchor: "middle", size, fill: impactText(key, mode) }, v >= 0 || zero);
      }
    }
  });

  // 7. place the labels: by priority (Total, extremes, cited, selected, last AC, first/last, rest), each
  // tested against every mark of its tier (columns, triangles, pins, heads) and the labels already
  // placed; a label that hits a mark moves past it once, else it is left out (its value stays in the
  // hidden table and the tooltip).
  const cited = new Set([...(o.keep ?? []), ...(o.highlight ? [o.highlight.category] : [])]);
  const extremes = (vals: (number | null | undefined)[]) => {
    const idx = vals.map((v, i) => ({ v, i })).filter((x): x is { v: number; i: number } => x.v != null);
    return idx.length ? [idx.reduce((a, b) => (b.v > a.v ? b : a)).i, idx.reduce((a, b) => (b.v < a.v ? b : a)).i] : [];
  };
  const ext3: Record<TierKey, number[]> = {
    base: extremes(prim.map((p) => p?.value)),
    delta: extremes(rows.map((r) => r.delta)),
    delta2: extremes(rows.map((r) => r.delta2)),
    pct: extremes(rows.map((r) => r.deltaPct)),
  };
  const lastAc = prim.map((p) => p?.scenario).lastIndexOf("AC");
  // placing order: Total, the extremes of each tier (largest and smallest Δ, Δ%, value), cited,
  // selected, last AC, first and last, rest; the Total and cited values are never left out
  const keepAlways = (c: Cand) => !!rows[c.i]!.total || cited.has(rows[c.i]!.period);
  const rank = (c: Cand) => {
    const r = rows[c.i]!;
    if (r.total) return 0;
    if (ext3[c.t].includes(c.i)) return 1;
    if (cited.has(r.period)) return 2;
    if (c.i === selIdx) return 3;
    if (c.i === lastAc) return 4;
    if (c.i === 0 || c.i === rows.length - 1) return 5;
    return 6;
  };
  const band = (t: TierKey) => ({ top: tiers[t].y0 - tiers[t].up - (t === "pct" ? room + 9 : room), bottom: tiers[t].y0 + tiers[t].down + (t === "pct" ? room + 9 : room) });
  const obstacleRoles = /^(col-|triangle-|pin|pin-head|variance$|outlier)/;
  const obstacles = marks.filter((m) => m.kind !== "text" && obstacleRoles.test(m.role)).map(markBox);
  const placed: { x: number; y: number; w: number; h: number }[] = [];
  let dropped = 0;
  for (const c of [...cands].sort((a, b) => rank(a) - rank(b) || a.i - b.i)) {
    const { top, bottom } = band(c.t);
    const inside = (bx: ReturnType<typeof markBox>) => bx.y >= top - 0.5 && bx.y + bx.h <= bottom + 0.5 && bx.x >= -0.5 && bx.x + bx.w <= o.width + 0.5;
    let bx = markBox(c.m);
    const hits = obstacles.filter((ob) => overlaps(bx, ob));
    if (hits.length) {
      // move past the marks it hits, on its own side (above for positive values, below for negative)
      const y = c.above ? Math.min(...hits.map((h) => h.y)) - box / 2 - 1 : Math.max(...hits.map((h) => h.y + h.h)) + box / 2 + 1;
      c.m = { ...c.m, y };
      bx = markBox(c.m);
    }
    // neighbouring labels keep at least 2 px between them ("4.14.0" reads as one number)
    const padded = { x: bx.x - 2, y: bx.y, w: bx.w + 4, h: bx.h };
    const free = inside(bx) && !obstacles.some((ob) => overlaps(bx, ob)) && !placed.some((pl) => overlaps(padded, pl, 0));
    if (!free && !keepAlways(c)) { dropped++; continue; }
    placed.push(bx);
    marks.push(c.m);
    if (o.highlight?.category === rows[c.i]!.period && o.highlight.tier === c.t) ring(c.m.x, c.m.y, c.m.text, rows[c.i]!.period);
  }
  if (dropped) warnings.push(`${dropped} labels left out to avoid collisions (priority: Total, extremes, cited, selected, last AC, first and last)`);

  // 8. category labels, never with an ellipsis: the full period (Jan), else its first letter (J; the
  // year is in the title), else two staggered rows
  const cats = periodLabels(rows.map((r) => r.period), size, step);
  rows.forEach((r, i) => {
    const y = catY + (cats.rows === 2 && i % 2 ? box : 0);
    marks.push({ kind: "text", role: "category", category: r.period, x: cx(i), y, text: cats.texts[i]!, anchor: "middle", size, fill: C.text.primary });
    if (twoYears && years[i] && (i === 0 || years[i] !== years[i - 1]))
      marks.push({ kind: "text", role: "category", category: r.period, x: cx(i), y: catY + box * cats.rows, text: years[i]!, anchor: "middle", size, fill: C.text.secondary });
  });

  // scale band: a light band left of the plot, as tall as the round value on this chart's scale
  // with its value above it, at the left edge (never near the end legend)
  if (o.scaleBand) {
    back.push({ kind: "rect", role: "scale-band", x: left - 7, y: y0 - o.scaleBand * o.ppu, w: 5, h: o.scaleBand * o.ppu, fill: C.marker.scaleBandFill, stroke: C.marker.scaleBandLine, strokeWidth: 0.5 });
    marks.push({ kind: "text", role: "scale-band-label", x: left - 2, y: y0 - o.scaleBand * o.ppu - box / 2 - 1, text: bandLabel, anchor: "end", size, fill: C.text.secondary });
  }
  // pin-tier scaling marker: this tier's % scale differs from the page's other % tiers (OURS); the band
  // grows to the side the pins use most, its label beyond its end, the tier name stays on the axis
  const pctBand = o.pctScaleBand === "auto" ? pinScaleBand(pctTierPx, pctPpu) : o.pctScaleBand;
  if (pctBand && order.includes("pct")) {
    const py = tiers.pct.y0;
    const h = pctBand * pctPpu;
    const up = tiers.pct.up >= tiers.pct.down;
    const text = `${+(pctBand * 100).toFixed(0)}%`;
    back.push({ kind: "rect", role: "scale-band", tier: "pct", x: left - 7, y: up ? py - h : py, w: 5, h, fill: C.marker.scaleBandFill, stroke: C.marker.scaleBandLine, strokeWidth: 0.5 });
    marks.push({ kind: "text", role: "scale-band-label", tier: "pct", x: left - 2, y: up ? py - h - box / 2 - 1 : py + h + box / 2 + 1, text, anchor: "end", size, fill: C.text.secondary });
  }
  if (o.deltaScaleBand && order.includes("delta")) {
    const dy = tiers.delta.y0;
    const h = o.deltaScaleBand * o.ppu; // the true round value, never clipped to fit
    if (h > tiers.delta.up + room) warnings.push("deltaScaleBand is taller than the Δ tier: pick a smaller round value");
    back.push({ kind: "rect", role: "scale-band", x: left - 7, y: dy - h, w: 5, h, fill: C.marker.scaleBandFill, stroke: C.marker.scaleBandLine, strokeWidth: 0.5 });
  }

  // 4. a tick on the category axis where AC switches to FC
  const firstFc = prim.findIndex((p) => p?.scenario === "FC");
  if (anyAC && firstFc > 0) back.push({ kind: "line", role: "axis", x1: left + step * firstFc, x2: left + step * firstFc, y1: y0, y2: y0 + 5, stroke: C.axis.category, strokeWidth: 1 });

  // 9. end legend: each name level with its mark at the last period, spread by font + 2 px
  if (legendOn) {
    const li = rows.length - 1;
    const r = rows[li]!;
    const p = prim[li];
    const xRight = cx(li) + B / 2 + off / 2;
    const items: { text: string; y: number }[] = [];
    if (p) items.push({ text: primaryName, y: yOf(p.value / 2) });
    const refV = r[o.reference];
    // an outlined reference (BU, PL) is named at the upper part of its column, clear of the primary's name
    const outlined = o.reference === "BU" || o.reference === "PL";
    if (refV != null && !(o.reference === "FC" && p?.scenario === "FC")) items.push({ text: o.reference, y: yOf(outlined ? refV * 0.75 : refV / 2) });
    const triV = o.triangle ? r[o.triangle] : null;
    if (o.triangle && triV != null) items.push({ text: o.triangle, y: yOf(triV) });
    const top = y0 - tiers.base.up - room + box / 2;
    const bottom = y0 + tiers.base.down + room - box / 2;
    const ys = spreadLabels(items.map((it) => it.y), size + 2, top, bottom);
    items.forEach((it, k) => {
      const y = ys[k]!;
      const x = left + plotW + 6;
      if (Math.abs(y - it.y) > size / 2) back.push({ kind: "line", role: "legend-leader", x1: xRight + 1, y1: it.y, x2: x - 2, y2: y, stroke: C.marker.assistingLine, strokeWidth: 0.75 });
      marks.push({ kind: "text", role: "legend", x, y, text: it.text, anchor: "start", size, fill: C.text.primary });
    });
  }

  // 10. hit zones, one per category band through all tiers (rendered only with onSelect)
  rows.forEach((r, i) => {
    const parts = [`${r.period}:`, prim[i] ? `${prim[i]!.scenario} ${valueLabels[i]}` : "", r[o.reference] != null ? `${o.reference} ${formatValue(r[o.reference], o.scale)}` : ""];
    marks.push({ kind: "rect", role: "hit", category: r.period, x: cx(i) - step / 2, y: 0, w: step, h: height, tooltip: parts.filter(Boolean).join(" ") });
  });

  const header = ["Period", primaryName, o.reference, ...(o.triangle ? [o.triangle] : []), ...(order.includes("delta") ? [refCode] : []), ...(order.includes("delta2") ? [ref2Code] : []), ...(order.includes("pct") ? [`${refCode}%`] : [])];
  const table = [header, ...rows.map((r, i) => [
    r.period, valueLabels[i]!, formatValue(r[o.reference], o.scale), ...(o.triangle ? [formatValue(r[o.triangle], o.scale)] : []),
    ...(order.includes("delta") ? [deltaLabel(i)] : []), ...(order.includes("delta2") ? [delta2Label(i)] : []), ...(order.includes("pct") ? [pctLabel(i)] : []),
  ])];

  // pin marks carry their tier's px per 1.0, so a page check can see differing % scales (data-ppu)
  const tagPins = (m: Mark): Mark => (PIN_ROLES.has(m.role) && m.category != null && m.ppu == null ? { ...m, ppu: pctPpu } : m);
  const short = shortPinWarning(marks);
  if (short) warnings.push(short);
  return { width: o.width, height, marks: [...back, ...marks].map(tagPins), warnings, table, tiers, step };
}

/**
 * Union of two charts' tier extents in px (months and Total, each at its own px per unit). Lay both
 * out again with this as `minTierPx`: baselines and tier axes then sit at the same y.
 */
export function alignTiers(...layouts: ColumnTiersLayout[]): Record<TierKey, TierPx> {
  const out = { pct: { up: 0, down: 0 }, delta: { up: 0, down: 0 }, delta2: { up: 0, down: 0 }, base: { up: 0, down: 0 } };
  for (const l of layouts)
    for (const t of ["pct", "delta", "delta2", "base"] as const) {
      out[t].up = Math.max(out[t].up, l.tiers[t].up);
      out[t].down = Math.max(out[t].down, l.tiers[t].down);
    }
  return out;
}

/**
 * Extents for the page registry, one request per tier: the base and the Δ tier both join the
 * chart's unit (each with the px its tier may use), the pins join "%".
 */
export function columnTiersExtents(rows: PeriodRow[], o: Pick<ColumnTiersOptions, "reference" | "triangle" | "outlierLimit" | "outlierRatio">) {
  const span = (vals: (number | null | undefined)[]) => {
    const nums = vals.filter((v): v is number => v != null && Number.isFinite(v));
    return { min: Math.min(0, ...nums), max: Math.max(0, ...nums) };
  };
  const lim = pinClip(rows.map((r) => r.deltaPct), o.outlierLimit ?? 1, o.outlierRatio ?? 3);
  return {
    base: span(rows.flatMap((r) => [r.AC, r.FC, r[o.reference], o.triangle ? r[o.triangle] : null])),
    delta: span(rows.map((r) => r.delta)),
    delta2: span(rows.map((r) => r.delta2)),
    pct: span(rows.map((r) => (r.deltaPct == null ? null : clamp(r.deltaPct, -lim, lim)))),
  };
}
