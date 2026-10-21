// Number formatting per the behaviour contract §4: one factor and fixed decimals per scale group,
// signed variances, N/A, pp, and the rounded-zero rule (a Δ that rounds to 0 is printed unsigned).
import { tokens } from "./tokens.generated";

const N = tokens.number;

export type NumberScale = {
  /** Divisor applied before printing (1, 1e3, 1e6, 1e9). */
  factor: number;
  /** Prefix for the unit in the title, e.g. "m" → "mEUR". Empty for factor 1. */
  prefix: string;
  /** Fixed decimals for every label of the scale group. */
  decimals: number;
};

const MONETARY: [number, string][] = [
  [1e9, N.scaling.monetary.billion],
  [1e6, N.scaling.monetary.million],
  [1e3, N.scaling.monetary.thousand],
];
const SI: [number, string][] = [
  [1e9, N.scaling.si.billion],
  [1e6, N.scaling.si.million],
  [1e3, N.scaling.si.thousand],
];

/**
 * The automatic rule: the smallest factor that keeps the largest |value| at ≤ maxDigits integer
 * digits, one decimal below 100. An explicit display setting from the visual spec wins: pass it
 * as `explicit` and only the fields it leaves open are filled.
 */
export function pickScale(
  values: Iterable<number | null | undefined>,
  opts: { monetary?: boolean; maxDigits?: number; explicit?: Partial<NumberScale> } = {},
): NumberScale {
  let maxAbs = 0;
  for (const v of values) if (v != null && Number.isFinite(v)) maxAbs = Math.max(maxAbs, Math.abs(v));
  const limit = 10 ** (opts.maxDigits ?? N.maxDigits.chart);
  let factor = 1;
  let prefix = "";
  for (const [f, p] of [...(opts.monetary === false ? SI : MONETARY)].reverse()) {
    if (maxAbs / factor < limit) break;
    factor = f;
    prefix = p;
  }
  const e = opts.explicit ?? {};
  if (e.factor != null) {
    factor = e.factor;
    prefix = e.prefix ?? [...MONETARY, ...SI].find(([f]) => f === factor)?.[1] ?? "";
  }
  const decimals = e.decimals ?? (maxAbs / factor < 100 ? 1 : 0);
  return { factor, prefix, decimals };
}

function group(intPart: string): string {
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, N.separator.thousands);
}

function fixed(abs: number, decimals: number): string {
  const [i = "0", d] = abs.toFixed(decimals).split(".");
  return d ? `${group(i)}${N.separator.decimal}${d}` : group(i);
}

/** True when `value` prints as zero at the scale's factor and decimals (0.0005 at 2 → "0.00"). */
export function roundsToZero(value: number, scale: Pick<NumberScale, "factor" | "decimals">): boolean {
  return Math.round(Math.abs(value / scale.factor) * 10 ** scale.decimals) === 0;
}

/** A plain value label: no plus sign; empty for null; "" plus a warning-worthy marker for non-finite. */
export function formatValue(value: number | null | undefined, scale: NumberScale): string {
  if (value == null || !Number.isFinite(value)) return "";
  if (roundsToZero(value, scale)) return fixed(0, scale.decimals);
  const s = fixed(Math.abs(value / scale.factor), scale.decimals);
  return value < 0 ? `${N.sign.negative}${s}` : s;
}

/** A signed absolute variance; null → N/A; a Δ that rounds to zero is unsigned. */
export function formatDelta(value: number | null | undefined, scale: NumberScale): string {
  if (value == null || !Number.isFinite(value)) return N.sign.notApplicable;
  if (roundsToZero(value, scale)) return fixed(0, scale.decimals);
  const s = fixed(Math.abs(value / scale.factor), scale.decimals);
  return `${value < 0 ? N.sign.negative : N.sign.plus}${s}`;
}

/** A signed relative variance from a fraction (0.058 → "+6%"); null → N/A. */
export function formatPercentDelta(fraction: number | null | undefined, decimals = 0): string {
  if (fraction == null || !Number.isFinite(fraction)) return N.sign.notApplicable;
  const pct = { factor: 0.01, decimals };
  if (roundsToZero(fraction, pct)) return `${fixed(0, decimals)}%`;
  const s = fixed(Math.abs(fraction * 100), decimals);
  return `${fraction < 0 ? N.sign.negative : N.sign.plus}${s}%`;
}

/** A variance of a ratio in percentage points from a fraction difference (0.021 → "+2.1pp"). */
export function formatPp(fraction: number | null | undefined, decimals = 1): string {
  const s = formatPercentDelta(fraction, decimals);
  return s === N.sign.notApplicable ? s : s.replace("%", N.scaling.percentagePoint);
}

/** A ratio value as a percentage (0.421 → "42.1%"). */
export function formatRatio(fraction: number | null | undefined, decimals = 1): string {
  if (fraction == null || !Number.isFinite(fraction)) return "";
  return formatValue(fraction * 100, { factor: 1, prefix: "", decimals }) + "%";
}

/** The unit as written once in the title: prefix + ISO code ("m" + "EUR" → "mEUR"). */
export function unitLabel(scale: NumberScale, unit: string): string {
  return `${scale.prefix}${unit}`;
}
