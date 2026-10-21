// The mark primitives every layout function returns (SKILL §8). The renderer maps them to SVG and
// writes `role` as data-role, `impact` as data-impact; tests and the ibcs-review linter query them.
import type { ImpactKey } from "../impact";

/** A solid colour, or the FC hatch with its stripe colour (one pattern per stripe colour). */
export type Fill = string | { hatch: string };

/** `group: "zoom"` marks the magnifier panel of a waterfall (rendered as data-group). */
type Base = { role: string; category?: string; impact?: ImpactKey; group?: "zoom" };

export type Mark =
  | (Base & { kind: "rect"; x: number; y: number; w: number; h: number; fill?: Fill; stroke?: string; strokeWidth?: number; tooltip?: string })
  | (Base & { kind: "line"; x1: number; y1: number; x2: number; y2: number; stroke: string; strokeWidth: number; dash?: string })
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
      /** Two-line labels: the lines replace `text` (which keeps the full name), centred on `y`. */
      lines?: string[];
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
      const lines = m.lines ?? [m.text];
      const w = Math.max(...lines.map((l) => textWidth(l, m.size)));
      const x = m.anchor === "start" ? m.x : m.anchor === "end" ? m.x - w : m.x - w / 2;
      return { x, y: m.y - 0.6 * m.size * lines.length, w, h: 1.2 * m.size * lines.length };
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

/**
 * Fit a category name into `maxPx`: one line when it fits; two lines (split at the space nearest the
 * middle, each cut from the end) when the row step allows them (step ≥ 2.2 × font); else cut from
 * the end. Never a middle ellipsis.
 */
export function fitLines(text: string, size: number, maxPx: number, rowStep: number): string[] {
  if (textWidth(text, size) <= maxPx) return [text];
  if (rowStep >= 2.2 * size) {
    const spaces = [...text.matchAll(/ /g)].map((m) => m.index!);
    if (spaces.length) {
      const mid = text.length / 2;
      const at = spaces.reduce((a, b) => (Math.abs(b - mid) < Math.abs(a - mid) ? b : a));
      return [truncateEnd(text.slice(0, at), size, maxPx), truncateEnd(text.slice(at + 1), size, maxPx)];
    }
  }
  return [truncateEnd(text, size, maxPx)];
}

/**
 * Period labels that fit a category step, never with an ellipsis (an "J…" is ambiguous): the full
 * label (Jan); else, for month names, the first letter (J; the year is in the title); else two
 * staggered rows (every second label one line lower), full labels when they fit two steps.
 */
export function periodLabels(labels: string[], size: number, step: number): { texts: string[]; rows: 1 | 2 } {
  const fits = (ts: string[], w: number) => ts.every((t) => textWidth(t, size) <= w - 2);
  if (fits(labels, step)) return { texts: labels, rows: 1 };
  const months = labels.every((l) => /^[A-Za-zÀ-ž]{3,}\.?$/.test(l));
  const letters = months ? labels.map((l) => [...l][0]!.toUpperCase()) : labels;
  if (months && fits(letters, step)) return { texts: letters, rows: 1 };
  return { texts: fits(labels, 2 * step) ? labels : letters, rows: 2 };
}

/** Do two boxes overlap (by more than `tol` px)? */
export function overlaps(a: { x: number; y: number; w: number; h: number }, b: { x: number; y: number; w: number; h: number }, tol = 0.5): boolean {
  return a.x + a.w - tol > b.x && b.x + b.w - tol > a.x && a.y + a.h - tol > b.y && b.y + b.h - tol > a.y;
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
