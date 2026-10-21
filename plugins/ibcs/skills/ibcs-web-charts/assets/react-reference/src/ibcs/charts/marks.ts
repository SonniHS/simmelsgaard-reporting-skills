// The mark primitives every layout function returns (SKILL §8). The renderer maps them to SVG and
// writes `role` as data-role, `impact` as data-impact; tests and the ibcs-review linter query them.
import type { ImpactKey } from "../impact";

/** A solid colour, or the FC hatch with its stripe colour (one pattern per stripe colour). */
export type Fill = string | { hatch: string };

type Base = { role: string; category?: string; impact?: ImpactKey };

export type Mark =
  | (Base & { kind: "rect"; x: number; y: number; w: number; h: number; fill?: Fill; stroke?: string; strokeWidth?: number; tooltip?: string })
  | (Base & { kind: "line"; x1: number; y1: number; x2: number; y2: number; stroke: string; strokeWidth: number })
  | (Base & { kind: "path"; d: string; fill?: Fill; stroke?: string; strokeWidth?: number })
  | (Base & { kind: "ellipse"; cx: number; cy: number; rx: number; ry: number; stroke: string; strokeWidth: number })
  | (Base & {
      kind: "text";
      x: number;
      y: number;
      text: string;
      anchor: "start" | "middle" | "end";
      size: number;
      fill: string;
      weight?: number;
    });

export type Layout = {
  width: number;
  height: number;
  marks: Mark[];
  warnings: string[];
  /** Every plotted number for the visually hidden data table (first row = header). */
  table: string[][];
};

/** Bounding box of a mark; text boxes are 1.2 em high and ≈ 0.6 em per character wide. */
export function markBox(m: Mark): { x: number; y: number; w: number; h: number } {
  switch (m.kind) {
    case "rect":
      return { x: m.x, y: m.y, w: m.w, h: m.h };
    case "line":
      return { x: Math.min(m.x1, m.x2), y: Math.min(m.y1, m.y2), w: Math.abs(m.x2 - m.x1), h: Math.abs(m.y2 - m.y1) };
    case "ellipse":
      return { x: m.cx - m.rx, y: m.cy - m.ry, w: 2 * m.rx, h: 2 * m.ry };
    case "path": {
      const n = m.d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [0, 0];
      const xs = n.filter((_, i) => i % 2 === 0);
      const ys = n.filter((_, i) => i % 2 === 1);
      return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
    }
    case "text": {
      const w = textWidth(m.text, m.size);
      const x = m.anchor === "start" ? m.x : m.anchor === "end" ? m.x - w : m.x - w / 2;
      return { x, y: m.y - 0.6 * m.size, w, h: 1.2 * m.size };
    }
  }
}

/**
 * Estimated label width: ≈ 0.6 em per digit, wider for capitals, %, Δ and &, narrower for lower
 * case. Prefer getBBox() where a browser is available.
 */
export function textWidth(text: string, size: number): number {
  let em = 0;
  for (const ch of text) em += /[A-Z%Δ&@#mw]/.test(ch) ? 0.75 : /[a-z]/.test(ch) ? 0.55 : /[ .,:;|'’]/.test(ch) ? 0.32 : 0.6;
  return em * size;
}

/** Label line box height: 1.2 × the font size, never the font size alone. */
export const lineBox = (size: number) => 1.2 * size;

/** Cut a category name from the end with an ellipsis so it fits `maxPx` (never a middle ellipsis). */
export function truncateEnd(text: string, size: number, maxPx: number): string {
  if (textWidth(text, size) <= maxPx) return text;
  const chars = [...text];
  while (chars.length > 1 && textWidth(chars.join("") + "…", size) > maxPx) chars.pop();
  return chars.join("") + "…";
}

/** Shorten a name in the middle (structure-chart rows), keeping its start and end readable. */
export function truncateMiddle(text: string, size: number, maxPx: number): string {
  if (textWidth(text, size) <= maxPx) return text;
  const chars = [...text];
  const keep = Math.max(2, Math.floor(maxPx / (0.6 * size)) - 1);
  const head = Math.ceil(keep / 2);
  return chars.slice(0, head).join("") + "…" + chars.slice(chars.length - (keep - head)).join("");
}

export const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

/**
 * Spread labels (centre y values) so neighbours are at least `gap` apart, keeping each as close to
 * its mark as possible and inside [lo, hi]. Returns the new centres in the input order.
 */
export function spreadLabels(ys: number[], gap: number, lo: number, hi: number): number[] {
  const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
  const pos = order.map((o) => o.y);
  for (let pass = 0; pass < 50; pass++) {
    let moved = false;
    for (let k = 1; k < pos.length; k++) {
      const d = pos[k]! - pos[k - 1]!;
      if (d < gap - 1e-6) {
        const push = (gap - d) / 2;
        pos[k - 1]! -= push;
        pos[k]! += push;
        moved = true;
      }
    }
    for (let k = 0; k < pos.length; k++) pos[k] = clamp(pos[k]!, lo, hi);
    if (!moved) break;
  }
  const out = new Array<number>(ys.length);
  order.forEach((o, k) => (out[o.i] = pos[k]!));
  return out;
}
