// Impact → colour (behaviour contract §3). The model's impact wins; polarity is only the
// fallback. Marks use the graphic colours, text uses the contrast-safe *Text tokens.
import { tokens } from "./tokens.generated";

/** −1 bad, 0 neutral (ambiguous), +1 good, as returned by the model's Impact column. */
export type Impact = -1 | 0 | 1;
export type ImpactKey = "good" | "bad" | "neutral" | "none";
export type ColorMode = "color" | "cvd" | "bw";

/**
 * The impact state of one variance. `isZero` is true for Δ = 0 and for a Δ that rounds to zero
 * at the visual's decimals: no mark, no colour. Geometry always uses the signed Δ; never Δ × polarity.
 */
export function impactKey(
  delta: number | null | undefined,
  opts: { impact?: Impact | null; polarity?: number; isZero?: boolean } = {},
): ImpactKey {
  if (delta == null || !Number.isFinite(delta) || delta === 0 || opts.isZero) return "none";
  if (opts.impact != null) return opts.impact > 0 ? "good" : opts.impact < 0 ? "bad" : "neutral";
  const polarity = opts.polarity ?? 1;
  if (polarity === 0) return "neutral";
  return Math.sign(delta) * polarity > 0 ? "good" : "bad";
}

const V = tokens.color.variance;

/** Fill for bars, pins and markers; undefined for "none" (no mark is drawn). */
export function impactFill(key: ImpactKey, mode: ColorMode = "color"): string | undefined {
  if (key === "none") return undefined;
  if (mode === "bw") return V.bw[key];
  if (mode === "cvd") return V.cvd[key];
  return V[key];
}

/** Colour for variance numbers: the *Text tokens (≥ 4.5:1), black for "none" and in bw mode. */
export function impactText(key: ImpactKey, mode: ColorMode = "color"): string {
  if (key === "none" || mode === "bw") return tokens.color.text.primary;
  const set = mode === "cvd" ? V.cvd : V;
  return key === "good" ? set.goodText : key === "bad" ? set.badText : set.neutralText;
}
