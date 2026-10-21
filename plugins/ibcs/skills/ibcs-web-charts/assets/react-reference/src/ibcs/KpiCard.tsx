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
  /** Relative Δ as a fraction; null = N/A. Not used for kind "pp". */
  relative?: number | null;
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
  const pctDec = p.pctDecimals ?? 0;

  const lines = p.variances
    .filter((v) => v.absolute != null || (v.kind !== "pp" && v.relative != null)) // a variance the measure lacks is left out
    .map((v) => {
      const pp = v.kind === "pp" || p.ratio;
      const absZero = v.absolute == null ? true : pp ? roundsToZero(v.absolute, { factor: 0.01, decimals: 1 }) : roundsToZero(v.absolute, p.scale);
      const absKey = impactKey(v.absolute, { impact: v.impact, polarity: v.polarity, isZero: absZero });
      const parts: { text: string; key: ReturnType<typeof impactKey> }[] = [];
      if (pp) parts.push({ text: formatPp(v.absolute), key: absKey });
      else {
        const abs = { text: v.absolute == null ? "" : formatDelta(v.absolute, p.scale), key: absKey };
        const relZero = v.relative == null || roundsToZero(v.relative, { factor: 0.01, decimals: pctDec });
        const rel = { text: formatPercentDelta(v.relative, pctDec), key: impactKey(v.relative, { impact: v.impact, polarity: v.polarity, isZero: relZero }) };
        const pair = p.deltaOrder === "relative-first" ? [rel, abs] : [abs, rel];
        parts.push(...pair.filter((x) => x.text));
      }
      return { code: v.code, parts };
    });

  return (
    <div style={{ ...cardSurface(p.cardStyle), padding: "14px 16px", minWidth: 0, position: "relative", fontFamily: tokens.typography.family.web.join(", "), color: C.text.primary }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontWeight: tokens.typography.weight.emphasis, fontSize: 13.5 }}>{p.label}</span>
        {p.definition && (
          <button type="button" aria-expanded={open} aria-controls={defId} aria-label={`About ${p.label}`} onClick={() => setOpen(!open)}
            style={{ border: `1px solid ${ink(0.25)}`, borderRadius: "50%", width: 18, height: 18, fontSize: 11, lineHeight: "16px", padding: 0, background: "transparent", cursor: "pointer" }}>
            i
          </button>
        )}
      </div>
      <div style={{ fontSize: 12, color: C.text.secondary }}>{p.unit}</div>
      <div style={{ fontSize: 24, fontWeight: 650, fontVariantNumeric: "tabular-nums", margin: "6px 0 4px" }}>{valueText}</div>
      {lines.map((l) => (
        <div key={l.code} style={{ fontSize: 12.5, fontVariantNumeric: "tabular-nums", display: "flex", gap: 6, alignItems: "baseline" }}>
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
