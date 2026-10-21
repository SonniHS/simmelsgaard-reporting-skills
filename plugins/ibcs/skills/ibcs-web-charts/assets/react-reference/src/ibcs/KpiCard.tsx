// KPI card (behaviour contract §10): a variance table turned on its side. Name with an (i)
// definition, unit line, AC value, one line per comparison with impact-coloured text tokens.
// The card surface is UI chrome (Fluent rounded card by default); its content keeps the contract.
import { useId, useState, type CSSProperties } from "react";
import { tokens } from "./tokens.generated";
import { formatDelta, formatPercentDelta, formatPp, formatRatio, formatValue, roundsToZero, type NumberScale } from "./format";
import { impactKey, impactText, type ColorMode, type Impact } from "./impact";

export type KpiVariance = {
  /** Scenario code of the comparison: "ΔPY", "ΔBU". */
  code: string;
  /** Raw absolute Δ, or for kind "pp" the difference of two fractions. */
  absolute?: number | null;
  /**
   * Relative Δ as a fraction. Omitted (`undefined`): the card shows no Δ% for this comparison.
   * `null` prints N/A only when `reference` is given and ≤ 0 (not interpretable); a `null` without
   * a reference, or with a positive one, is treated as missing and left out. Not used for kind "pp".
   */
  relative?: number | null;
  /** The comparison's reference value (e.g. BU); decides whether a null Δ% is N/A. */
  reference?: number | null;
  kind?: "absolute" | "pp";
  impact?: Impact | null;
  polarity?: number;
};

export type KpiCardProps = {
  label: string;
  /** The unit line: "in mEUR", "in %", "ratio". */
  unit: string;
  value: number | null;
  scale: NumberScale;
  /** The value is a fraction shown as a percentage; its variances are pp. */
  ratio?: boolean;
  variances: KpiVariance[];
  /** One order per page; the spec decides. Default absolute first. */
  deltaOrder?: "absolute-first" | "relative-first";
  pctDecimals?: number;
  /** Ring the Δ the key message cites (only when material). */
  highlight?: string;
  definition?: string;
  colorMode?: ColorMode;
  cardStyle?: "fluent" | "square";
  /** Content alignment: centred (default, as the report shell) or left. */
  align?: "center" | "start";
};

const C = tokens.color;
const ink = (a: number) => `rgba(0, 0, 0, ${a})`;

export const cardSurface = (style: "fluent" | "square" = "fluent"): CSSProperties =>
  style === "fluent"
    ? { background: C.background.page, borderRadius: 8, boxShadow: `0 0 0 1px ${ink(0.1)}, 0 2px 4px ${ink(0.12)}` }
    : { background: C.background.page };

export function KpiCard(p: KpiCardProps) {
  const [open, setOpen] = useState(false);
  const defId = useId();
  const mode = p.colorMode ?? "color";
  const valueText = p.ratio ? formatRatio(p.value, p.scale.decimals) : formatValue(p.value, p.scale);
  const pctDec = p.pctDecimals ?? 1; // one decimal by default, in every route

  const align = p.align ?? "center";
  // N/A only for a null Δ% whose reference is known and ≤ 0; undefined (or null without that) is left out
  const relState = (v: KpiVariance): "value" | "na" | "none" =>
    typeof v.relative === "number" ? "value" : v.relative === null && v.reference != null && v.reference <= 0 ? "na" : "none";
  const lines = p.variances
    .filter((v) => v.absolute != null || (v.kind !== "pp" && relState(v) !== "none")) // a variance the measure lacks is left out
    .map((v) => {
      const pp = v.kind === "pp" || p.ratio;
      const absZero = v.absolute == null ? true : pp ? roundsToZero(v.absolute, { factor: 0.01, decimals: 1 }) : roundsToZero(v.absolute, p.scale);
      const absKey = impactKey(v.absolute, { impact: v.impact, polarity: v.polarity, isZero: absZero });
      const parts: { text: string; key: ReturnType<typeof impactKey> }[] = [];
      if (pp) parts.push({ text: formatPp(v.absolute), key: absKey });
      else {
        const abs = { text: v.absolute == null ? "" : formatDelta(v.absolute, p.scale), key: absKey };
        const state = relState(v);
        const relZero = state !== "value" || roundsToZero(v.relative!, { factor: 0.01, decimals: pctDec });
        const rel = { text: state === "none" ? "" : formatPercentDelta(state === "na" ? null : v.relative, pctDec), key: impactKey(state === "value" ? v.relative : null, { impact: v.impact, polarity: v.polarity, isZero: relZero }) };
        const pair = p.deltaOrder === "relative-first" ? [rel, abs] : [abs, rel];
        parts.push(...pair.filter((x) => x.text));
      }
      return { code: v.code, parts };
    });

  return (
    <div data-align={align} style={{ ...cardSurface(p.cardStyle), padding: "14px 16px", minWidth: 0, position: "relative", textAlign: align === "center" ? "center" : "left", fontFamily: tokens.typography.family.web.join(", "), color: C.text.primary }}>
      <div style={{ display: "flex", justifyContent: align === "center" ? "center" : "space-between", alignItems: "baseline", gap: 8, paddingRight: align === "center" && p.definition ? 22 : 0, paddingLeft: align === "center" && p.definition ? 22 : 0 }}>
        <span style={{ fontWeight: tokens.typography.weight.emphasis, fontSize: 13.5 }}>{p.label}</span>
        {p.definition && (
          <button type="button" aria-expanded={open} aria-controls={defId} aria-label={`About ${p.label}`} onClick={() => setOpen(!open)}
            style={{ ...(align === "center" ? { position: "absolute", top: 14, right: 16 } : {}), border: `1px solid ${ink(0.25)}`, borderRadius: "50%", width: 18, height: 18, fontSize: 11, lineHeight: "16px", padding: 0, background: "transparent", cursor: "pointer" }}>
            i
          </button>
        )}
      </div>
      <div style={{ fontSize: 12, color: C.text.secondary }}>{p.unit}</div>
      <div style={{ fontSize: 24, fontWeight: 650, fontVariantNumeric: "tabular-nums", margin: "6px 0 4px" }}>{valueText}</div>
      {lines.map((l) => (
        <div key={l.code} style={{ fontSize: 12.5, fontVariantNumeric: "tabular-nums", display: "flex", gap: 6, alignItems: "baseline", justifyContent: align === "center" ? "center" : "flex-start" }}>
          {l.parts.map((part, k) => {
            const ringed = p.highlight === l.code && k === 0;
            return (
              <span key={k} data-role="variance-label" data-impact={part.key} style={{ color: impactText(part.key, mode), ...(ringed ? { border: `${tokens.stroke.highlightEllipsePx}px solid ${C.marker.highlight}`, borderRadius: "50%", padding: "0 6px" } : {}) }}>
                {part.text}
              </span>
            );
          })}
          <span style={{ color: C.text.secondary }}>{l.code}</span>
        </div>
      ))}
      {p.definition && open && (
        <p id={defId} role="note" style={{ fontSize: 12, margin: "8px 0 0", color: C.text.secondary }}>{p.definition}</p>
      )}
    </div>
  );
}
