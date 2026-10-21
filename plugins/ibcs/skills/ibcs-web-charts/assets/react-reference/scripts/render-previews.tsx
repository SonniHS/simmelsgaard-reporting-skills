// Renders the previews from generic sample data: one SVG per chart and previews/page.html, a
// Key-figures style page (KPI row, months + Total aligned on their own scales, structure bars,
// bridge) in Fluent cards. `npm run previews`; screenshot page.html for a PNG.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import type { ReactNode } from "react";
import {
  KpiCard, MarksSvg, alignTiers, cardSurface, columnTiersExtents, layoutColumnTiers, layoutStructureBars,
  layoutTimeWaterfall, layoutVarianceWaterfall, pagePinScales, pickScale, pxPerUnit, structureExtents, tokens, type Layout, type PeriodRow,
} from "../src/ibcs";

const out = join(fileURLToPath(new URL(".", import.meta.url)), "../previews");
mkdirSync(out, { recursive: true });

// Generic sample: revenue by month (Jan–Sep closed, Oct–Dec forecast) against budget, PY as triangle.
const ac = [3.62, 3.48, 3.95, 3.71, 3.88, 4.05, 3.52, 3.4, 4.12];
const fc = [4.05, 4.2, 4.6];
const bu = [3.5, 3.55, 3.8, 3.8, 3.9, 3.95, 3.6, 3.5, 4.0, 4.1, 4.25, 4.5];
const py = [3.3, 3.35, 3.6, 3.55, 3.7, 3.8, 3.4, 3.2, 3.85, 3.9, 4.0, 4.3];
const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const months: PeriodRow[] = names.map((period, i) => {
  const v = (i < 9 ? ac[i]! : fc[i - 9]!) * 1e6;
  const b = bu[i]! * 1e6;
  return { period, closed: i < 9, AC: i < 9 ? v : null, FC: i >= 9 ? v : null, BU: b, PY: py[i]! * 1e6, delta: v - b, deltaPct: (v - b) / b };
});
const sum = (k: "AC" | "FC" | "BU" | "PY") => months.reduce((s, r) => s + (r[k] ?? 0), 0);
const totAF = sum("AC") + sum("FC");
const total: PeriodRow[] = [{ period: "Total", closed: false, FC: totAF, BU: sum("BU"), PY: sum("PY"), delta: totAF - sum("BU"), deltaPct: (totAF - sum("BU")) / sum("BU") }];

const regions = [
  { category: "Region North", AC: 12.4e6, BU: 11.8e6 },
  { category: "Region West", AC: 9.1e6, BU: 9.6e6 },
  { category: "Region South", AC: 7.6e6, BU: 7.2e6 },
  { category: "Region East", AC: 4.2e6, BU: 4.5e6 },
  { category: "Other", AC: 0.4e6, BU: 0.9e6, remainder: true },
].map((r) => ({ ...r, delta: r.AC - r.BU, deltaPct: (r.AC - r.BU) / r.BU }));
const regionTotal = { category: "Total", total: true, AC: regions.reduce((s, r) => s + r.AC, 0), BU: regions.reduce((s, r) => s + r.BU, 0) };
const structure = [...regions, { ...regionTotal, delta: regionTotal.AC - regionTotal.BU, deltaPct: (regionTotal.AC - regionTotal.BU) / regionTotal.BU }];

const bridge = {
  base: { label: "PY", scenario: "PY" as const, value: 31.2e6 },
  steps: [
    { label: "Volume", delta: 2.1e6 },
    { label: "Price", delta: 0.9e6 },
    { label: "Mix", delta: -0.6e6 },
    { label: "Currency", delta: -0.3e6 },
  ],
  total: { label: "AC", scenario: "AC" as const, value: 33.3e6 },
  variance: { code: "ΔPY", value: 2.1e6 },
};

// Page registry: months share "EUR"; the Total has its own group "EUR:total" (scale band + footnote
// in a real page); structure and bridge share "EUR:ytd"; pins share "%".
const W = { months: 860, total: 150, half: 560 };
const mExt = columnTiersExtents(months, { reference: "BU", triangle: "PY" });
const tExt = columnTiersExtents(total, { reference: "BU", triangle: "PY" });
const sExt = structureExtents(structure, { reference: "BU" });
const ppu = pxPerUnit([
  // the largest month column about 1.5 × the month pitch (behaviour contract §5)
  { unit: "EUR", ...mExt.base, availablePx: Math.round(1.5 * (W.months / 12)) },
  { unit: "EUR", ...mExt.delta, availablePx: 50 },
  { unit: "EUR:total", ...tExt.base, availablePx: Math.round(1.5 * (W.months / 12)) },
  { unit: "EUR:ytd", ...sExt.base, availablePx: 140 },
  { unit: "EUR:ytd", min: 0, max: 33.6e6, availablePx: 300 }, // the bridge
  // pins: 1 px per percentage point, shrunk only when a cell cannot fit it
]);
const scale = pickScale(months.flatMap((r) => [r.AC, r.FC, r.BU]));
const ytdScale = pickScale([regionTotal.AC]);
// pin tiers have their own scale, sized to the tier; charts read together (months and their Total)
// share one, so their pins compare; the structure chart sizes its own pins (pctTierPx 90)
// pagePinScales: the months and their Total are read together (one group); the structure chart has its
// own pin scale, so the scales differ and every pin tier gets a scaling marker (OURS, UN 5.2 / CH 4.3)
const pins = pagePinScales([
  { id: "months", ...mExt.pct, tierPx: 48, group: "months" },
  { id: "total", ...tExt.pct, tierPx: 48, group: "months" },
  { id: "regions", ...structureExtents(structure, { reference: "BU" }).pct, tierPx: 90 },
]);
const pct = pins.get("months")!.ppu;
const pctBand = pins.get("months")!.band ?? undefined;
const base = { reference: "BU" as const, triangle: "PY" as const, pctPpu: pct, pctScaleBand: pctBand, scale, polarity: 1 };
const regionPins = { pctPpu: pins.get("regions")!.ppu, pctScaleBand: pins.get("regions")!.band ?? undefined };
const m1 = layoutColumnTiers(months, { ...base, width: W.months, ppu: ppu.get("EUR")!, selected: "Sep", highlight: { category: "Sep", tier: "delta" } });
const t1 = layoutColumnTiers(total, { ...base, width: W.total, ppu: ppu.get("EUR:total")!, scale: pickScale([totAF]), primaryLabel: "AC&FC" });
const align = alignTiers(m1, t1);
const monthsL = layoutColumnTiers(months, { ...base, width: W.months, ppu: ppu.get("EUR")!, selected: "Sep", highlight: { category: "Sep", tier: "delta" }, minTierPx: align, scaleBand: 2e6, deltaScaleBand: 0.5e6, keep: ["Sep"] });
const totalL = layoutColumnTiers(total, { ...base, width: W.total, ppu: ppu.get("EUR:total")!, scale: pickScale([totAF]), minTierPx: align, scaleBand: 2e6, deltaScaleBand: 0.5e6, primaryLabel: "AC&FC" });
const structL = layoutStructureBars(structure, { width: W.half, reference: "BU", ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: 1, highlight: { category: "Region West", tier: "delta" }, ...regionPins });
const bridgeL = layoutVarianceWaterfall(bridge, { width: W.half, ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: 1 });

// Small contributions next to a large base: the magnifier case (CH 4.5). Costs: polarity -1.
const costBridge = {
  base: { label: "BU", scenario: "BU" as const, value: 7.70e6 },
  steps: [
    { label: "Personnel", delta: 0.21e6 },
    { label: "Rent", delta: -0.04e6 },
    { label: "IT services", delta: 0.09e6 },
    { label: "Travel", delta: -0.11e6 },
  ],
  total: { label: "AC", scenario: "AC" as const, value: 7.85e6 },
  variance: { code: "ΔBU", value: 0.15e6 },
};
const costL = layoutVarianceWaterfall(costBridge, { width: W.half, ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: -1 });
// A time decomposition (A-11): PY → ΔPY by quarter → AC, small steps, magnifier tier below.
const quarterBridge = {
  base: { label: "PY", scenario: "PY" as const, value: 30.0e6 },
  steps: [{ label: "Q1", delta: 0.42e6 }, { label: "Q2", delta: -0.13e6 }, { label: "Q3", delta: 0.47e6 }],
  total: { label: "AC", scenario: "AC" as const, value: 30.76e6 },
  variance: { code: "ΔPY", value: 0.76e6 },
};
const quarterL = layoutTimeWaterfall(quarterBridge, { width: W.half, ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: 1 });

const charts: [string, Layout, string][] = [
  ["column-tiers", monthsL, "Revenue in mEUR, 2026 AC&FC vs BU and PY, by month"],
  ["column-tiers-total", totalL, "Revenue in mEUR, 2026 AC&FC vs BU and PY, total (own scale)"],
  ["structure-bars", structL, "Revenue in mEUR, Jan..Sep 2026 AC vs BU, by region"],
  ["variance-waterfall", bridgeL, "Revenue in mEUR, Jan..Sep 2026 PY to AC"],
  ["variance-waterfall-magnifier", costL, "Operating costs in mEUR, Jan..Sep 2026 BU to AC, by cost type"],
  ["time-waterfall", quarterL, "Revenue in mEUR, Jan..Sep 2026 PY to AC, by quarter"],
];
for (const [name, layout, title] of charts) {
  for (const w of layout.warnings) console.warn(`${name}: ${w}`);
  writeFileSync(join(out, `${name}.svg`), renderToStaticMarkup(<MarksSvg layout={layout} title={title} standalone />) + "\n");
}

const fmt = { factor: 1e6, prefix: "m", decimals: 1 };
const Card = ({ title, sub, children }: { title: string; sub?: string; children: ReactNode }) => (
  <section style={{ ...cardSurface("fluent"), padding: 16, minWidth: 0 }}>
    <div style={{ fontSize: 13.5, fontWeight: 600 }}>{title}</div>
    {sub && <div style={{ fontSize: 12, color: tokens.color.text.secondary, marginBottom: 8 }}>{sub}</div>}
    {children}
  </section>
);
const page = (
  <main style={{ background: "rgba(0,0,0,0.05)", padding: 16, display: "grid", gap: 16, width: 1248, fontFamily: tokens.typography.family.web.join(", ") }}>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
      <KpiCard label="Revenue" unit="in mEUR" value={33.3e6} scale={fmt} definition="Net revenue after discounts." highlight="ΔBU"
        variances={[{ code: "ΔBU", absolute: 0.3e6, relative: 0.009 }, { code: "ΔPY", absolute: 2.1e6, relative: 0.067 }]} />
      <KpiCard label="Gross margin" unit="in %" ratio value={0.412} scale={{ factor: 1, prefix: "", decimals: 1 }}
        variances={[{ code: "ΔBU", absolute: -0.008 }, { code: "ΔPY", absolute: 0.011 }]} />
      <KpiCard label="Operating costs" unit="in mEUR" value={9.8e6} scale={fmt}
        variances={[{ code: "ΔBU", absolute: 0.4e6, relative: 0.043, polarity: -1 }, { code: "ΔPY", absolute: 0.00002e6, relative: 0.00002, polarity: -1 }]} />
      <KpiCard label="Orders" unit="in k#" value={41.2e3} scale={{ factor: 1e3, prefix: "k", decimals: 1 }}
        variances={[{ code: "ΔBU", absolute: -1.3e3, relative: -0.031 }, { code: "ΔPY", absolute: 2.4e3, relative: 0.062 }]} />
    </div>
    <Card title="Revenue in mEUR" sub="2026 AC&FC vs BU and PY, by month · Total on its own scale¹">
      <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
        <MarksSvg layout={monthsL} title={charts[0]![2]} />
        <MarksSvg layout={totalL} title={charts[1]![2]} />
      </div>
    </Card>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <Card title="Revenue in mEUR" sub="Jan..Sep 2026 AC vs BU, by region"><MarksSvg layout={structL} title={charts[2]![2]} /></Card>
      <Card title="Revenue in mEUR" sub="Jan..Sep 2026, PY to AC"><MarksSvg layout={bridgeL} title={charts[3]![2]} /></Card>
    </div>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <Card title="Operating costs in mEUR" sub="Jan..Sep 2026, BU to AC, by cost type (steps magnified)"><MarksSvg layout={costL} title={charts[4]![2]} /></Card>
      <Card title="Revenue in mEUR" sub="Jan..Sep 2026, PY to AC, by quarter (steps magnified)"><MarksSvg layout={quarterL} title={charts[5]![2]} /></Card>
    </div>
    <footer style={{ fontSize: 12, color: tokens.color.text.secondary }}>¹ The Total has its own scale; the blue scale band is 2.0 mEUR in both charts (0.5 mEUR in the ΔBU tiers). The ΔBU% tiers of the months and of the regions are on different scales, each sized to its tier; the blue mark in each shows its round value. Sample data.</footer>
  </main>
);
writeFileSync(
  join(out, "page.html"),
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>IBCS reference components</title></head><body style="margin:0">${renderToStaticMarkup(page)}</body></html>\n`,
);
// Phone check (390 px viewport, 16 px gutters): the same data redrawn for the width, not shrunk.
const PW = 390 - 2 * 16 - 2 * 16; // viewport − page gutters − card padding
const pMonths = layoutColumnTiers(months, { ...base, width: PW, ppu: ppu.get("EUR")!, selected: "Sep", keep: ["Sep"], scaleBand: 2e6 });
const pStruct = layoutStructureBars(structure, { width: PW, reference: "BU", stack: "auto", ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: 1, ...regionPins });
const pCost = layoutVarianceWaterfall(costBridge, { width: PW, ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: -1, magnifier: "below" });
const pQuarter = layoutTimeWaterfall(quarterBridge, { width: PW, ppu: ppu.get("EUR:ytd")!, scale: ytdScale, polarity: 1 });
const phone = (
  <main style={{ background: "rgba(0,0,0,0.05)", padding: 16, display: "grid", gap: 12, width: 390 - 2 * 16, fontFamily: tokens.typography.family.web.join(", ") }}>
    {([[pMonths, "Revenue by month"], [pStruct, "Revenue by region"], [pCost, "Operating costs, BU to AC"], [pQuarter, "Revenue by quarter, PY to AC"]] as const).map(([l, t]) => (
      <Card key={t} title={t}><MarksSvg layout={l} title={t} /></Card>
    ))}
  </main>
);
for (const [name, l] of [["phone months", pMonths], ["phone structure", pStruct], ["phone cost bridge", pCost], ["phone quarter bridge", pQuarter]] as const)
  for (const w of l.warnings) console.warn(`${name}: ${w}`);
writeFileSync(
  join(out, "phone.html"),
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>IBCS reference components (phone)</title></head><body style="margin:0">${renderToStaticMarkup(phone)}</body></html>\n`,
);
console.log(`previews written to ${out}`);
