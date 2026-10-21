// Proof run 3, M1 fixture (generic sample values): twelve months of ΔBU in mEUR, Sep highlighted, Aug the
// largest |Δ|. Shared by the M1 test and the phone previews; not part of the components' API.
import type { PeriodRow } from "./charts/columnTiers";

const DBU = [-0.7, -0.5, -0.6, 0.2, -1.4, 0.5, -0.1, 1.8, 1.3, 0.6, 0.1, 1.3];
const NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const m1Months: PeriodRow[] = NAMES.map((period, i) => {
  const bu = (30 + (i % 5) + i * 0.4) * 1e6;
  const v = bu + DBU[i]! * 1e6;
  const closed = i < 9;
  return { period, closed, AC: closed ? v : null, FC: closed ? null : v, BU: bu, PY: bu * 0.96, delta: DBU[i]! * 1e6, deltaPct: (DBU[i]! * 1e6) / bu };
});

const sum = (k: "AC" | "FC" | "BU" | "PY" | "delta") => m1Months.reduce((s, r) => s + (r[k] ?? 0), 0);
export const m1Total: PeriodRow[] = [{
  period: "Total", closed: false, FC: sum("AC") + sum("FC"), BU: sum("BU"), PY: sum("PY"), delta: sum("delta"), deltaPct: sum("delta") / sum("BU"),
}];
