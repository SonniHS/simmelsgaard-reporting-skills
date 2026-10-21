// @vitest-environment node
// One test per contract rule (references/testing.md). DOM-free on the layouts; the renderer and
// the KPI card are server-rendered to strings. Runs in an app's vitest too: the environment is set
// per file (an app's jsdom default breaks `new URL(".", import.meta.url)`), and describe/it/expect
// are imported, so no vitest globals are needed in the app's tsconfig.
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import { act, create } from "react-test-renderer";
import { describe, expect, it } from "vitest";
import {
  KpiCard, MarksSvg, alignTiers, fitLines, overlaps, formatDelta, formatPercentDelta, formatPp, formatValue, impactFill, impactKey, impactText,
  layoutColumnTiers, layoutStructureBars, periodLabels, pinScale, layoutTimeWaterfall, layoutVarianceWaterfall, lineBoxes, magnifierFactor, markBox, pagePinScales, pickScale, pinScaleBand, pxPerUnit, ScaleProvider, tokens, useScale,
  type ColumnTiersOptions, type Layout, type Mark, type PeriodRow,
} from "./index";

const C = tokens.color;
const scale = pickScale([4_200_000]); // mEUR, 1 decimal
const months: PeriodRow[] = [
  { period: "Jan", closed: true, AC: 3.8e6, BU: 3.6e6, PY: 3.5e6, delta: 0.2e6, deltaPct: 0.0556 },
  { period: "Feb", closed: true, AC: 3.9e6, BU: 4.1e6, PY: 3.7e6, delta: -0.2e6, deltaPct: -0.0488 },
  { period: "Mar", closed: true, AC: 4.0e6, BU: 4.0e6, PY: 3.8e6, delta: 400, deltaPct: 0.0001 },
  { period: "Apr", closed: false, AC: 1.1e6, FC: 4.2e6, BU: 4.0e6, PY: 3.9e6, delta: 0.2e6, deltaPct: 0.05 },
];
const opts: ColumnTiersOptions = { width: 520, reference: "BU", triangle: "PY", ppu: 30 / 1e6, pctPpu: 200, scale };
const byRole = (l: Layout, role: string) => l.marks.filter((m) => m.role === role);
const rect = (m: Mark | undefined) => (m?.kind === "rect" ? m : undefined)!;

describe("format", () => {
  it("one factor and fixed decimals per scale group", () => {
    expect(scale).toEqual({ factor: 1e6, prefix: "m", decimals: 1 });
    expect(pickScale([250_000_000]).decimals).toBe(0);
    expect(pickScale([4_200_000], { explicit: { decimals: 2 } })).toMatchObject({ factor: 1e6, decimals: 2 });
  });
  it("signs variances, prints N/A and pp, keeps the thousands separator token", () => {
    expect(formatDelta(1.25e6, scale)).toBe("+1.3");
    expect(formatDelta(-0.3e6, scale)).toBe("-0.3");
    expect(formatDelta(null, scale)).toBe("N/A");
    expect(formatPercentDelta(0.058)).toBe("+6%");
    expect(formatPp(0.021)).toBe("+2.1pp");
    expect(formatValue(12_345, { factor: 1, prefix: "", decimals: 0 })).toBe(`12${tokens.number.separator.thousands}345`);
  });
  it("a Δ that rounds to zero is unsigned (0.00, never +0.00)", () => {
    expect(formatDelta(0.0005, { factor: 1, prefix: "", decimals: 2 })).toBe("0.00");
    expect(formatDelta(-0.0004, { factor: 1, prefix: "", decimals: 2 })).toBe("0.00");
    expect(formatPercentDelta(0.001)).toBe("0%");
  });
});

describe("impact", () => {
  it("polarity selects the colour only; model impact wins; polarity 0 is neutral", () => {
    expect(impactKey(5, { polarity: -1 })).toBe("bad"); // a cost increase
    expect(impactKey(5, { polarity: -1, impact: 1 })).toBe("good");
    expect(impactKey(5, { polarity: 0 })).toBe("neutral");
    expect(impactKey(0)).toBe("none");
    expect(impactKey(5, { isZero: true })).toBe("none");
  });
  it("text uses the *Text tokens, never the graphic green", () => {
    expect(impactText("good")).toBe(C.variance.goodText);
    expect(impactText("good")).not.toBe(C.variance.good);
    expect(impactFill("good", "cvd")).toBe(C.variance.cvd.good);
    expect(impactText("none")).toBe(C.text.primary);
  });
});

describe("shared scale", () => {
  it("the smallest px per unit wins; the smaller chart becomes shorter", () => {
    const ppu = pxPerUnit([
      { unit: "EUR", min: 0, max: 4e6, availablePx: 120 },
      { unit: "EUR", min: 0, max: 1e6, availablePx: 120 },
      { unit: "%", min: -0.1, max: 0.1, availablePx: 40 },
      { unit: "EUR", min: 0, max: 1, availablePx: -5 }, // non-positive request is skipped
    ]);
    expect(ppu.get("EUR")).toBeCloseTo(30 / 1e6);
    const big = layoutColumnTiers(months, { ...opts, tiers: [] });
    const small = layoutColumnTiers(months.map((r) => ({ ...r, AC: (r.AC ?? 0) / 2, FC: r.FC && r.FC / 2, BU: r.BU! / 2, PY: r.PY! / 2 })), { ...opts, tiers: [] });
    expect(small.height).toBeLessThan(big.height);
  });
});

describe("column chart with tiers", () => {
  const l = layoutColumnTiers(months, opts);
  it("draws the reference before the primary, shifted left", () => {
    const i = l.marks.findIndex((m) => m.role === "col-BU" && m.category === "Jan");
    const j = l.marks.findIndex((m) => m.role === "col-AC" && m.category === "Jan");
    expect(i).toBeLessThan(j);
    expect(rect(l.marks[i]).x).toBeLessThan(rect(l.marks[j]).x);
    expect(rect(l.marks[i]).fill).toBe(C.scenario.pl.fill);
    expect(rect(l.marks[i]).stroke).toBe(C.scenario.pl.stroke);
  });
  it("the open period is FC hatched; its partial AC is not drawn", () => {
    const apr = l.marks.filter((m) => m.category === "Apr" && m.role.startsWith("col-"));
    expect(apr.map((m) => m.role).sort()).toEqual(["col-BU", "col-FC"]);
    expect(rect(apr.find((m) => m.role === "col-FC")).fill).toEqual({ hatch: C.scenario.fc.stripe });
    expect(byRole(l, "legend").map((m) => (m.kind === "text" ? m.text : ""))).toContain("AC&FC");
  });
  it("names AC alone when the last column is AC", () => {
    const ac = layoutColumnTiers(months.slice(0, 3), opts);
    expect(byRole(ac, "legend").map((m) => (m.kind === "text" ? m.text : ""))).toContain("AC");
    expect(byRole(ac, "legend").map((m) => (m.kind === "text" ? m.text : ""))).not.toContain("AC&FC");
  });
  it("a Δ that rounds to zero draws no mark and an unsigned, uncoloured label", () => {
    expect(l.marks.some((m) => m.role === "variance" && m.category === "Mar")).toBe(false);
    const lab = l.marks.find((m) => m.role === "variance-label" && m.category === "Mar" && m.kind === "text" && !m.text.endsWith("%"));
    expect(lab).toMatchObject({ text: "0.0", impact: "none", fill: C.text.primary });
  });
  it("absolute Δ bars use the base px per unit and impact colours", () => {
    const jan = rect(l.marks.find((m) => m.role === "variance" && m.category === "Jan"));
    expect(jan.h).toBeCloseTo(0.2e6 * opts.ppu);
    expect(jan.fill).toBe(C.variance.good);
    const apr = rect(l.marks.find((m) => m.role === "variance" && m.category === "Apr"));
    expect(apr.fill).toEqual({ hatch: C.variance.good }); // FC period: hatched in the impact colour
  });
  it("N/A draws no pin but keeps its label", () => {
    const na = layoutColumnTiers([{ ...months[0]!, deltaPct: null }], opts);
    expect(byRole(na, "pin")).toHaveLength(0);
    expect(byRole(na, "variance-label").some((m) => m.kind === "text" && m.text === "N/A")).toBe(true);
  });
  it("pins and triangles stay inside their px clamps on wide and narrow columns", () => {
    for (const width of [220, 2400]) {
      const w = layoutColumnTiers(months, { ...opts, width });
      for (const m of byRole(w, "pin")) expect(rect(m).w).toBeGreaterThanOrEqual(tokens.geometry.pin.stemPx.min - 1e-9);
      for (const m of byRole(w, "pin")) expect(rect(m).w).toBeLessThanOrEqual(tokens.geometry.pin.stemPx.max + 1e-9);
      for (const m of byRole(w, "pin-head")) expect(rect(m).w).toBeLessThanOrEqual(tokens.geometry.pin.headPx.max + 1e-9);
      for (const m of byRole(w, "triangle-PY")) expect(markBox(m).h).toBeLessThanOrEqual(tokens.geometry.triangleSizePx.max + 1e-9);
    }
  });
  it("truncates an outlier pin with a marker and keeps the full label", () => {
    const o = layoutColumnTiers([{ ...months[0]!, deltaPct: 2.5 }], opts);
    expect(byRole(o, "outlier")).toHaveLength(1);
    expect(byRole(o, "pin-head")).toHaveLength(0);
    expect(byRole(o, "variance-label").some((m) => m.kind === "text" && m.text === "+250.0%")).toBe(true);
    expect(o.warnings.join()).toMatch(/outlier/);
  });
  it("drops non-finite values with a warning and no NaN anywhere", () => {
    const bad = layoutColumnTiers([{ ...months[0]!, AC: Number.NaN }], opts);
    expect(bad.warnings.join()).toMatch(/non-finite/);
    expect(JSON.stringify(bad.marks)).not.toMatch(/NaN|null,"y"/);
  });
  it("keeps every label inside the chart box", () => {
    for (const width of [300, 520, 1000]) {
      const w = layoutColumnTiers(months, { ...opts, width });
      for (const m of w.marks.filter((x) => x.kind === "text")) {
        const b = markBox(m);
        expect(b.x).toBeGreaterThanOrEqual(-0.5);
        expect(b.y).toBeGreaterThanOrEqual(-0.5);
        expect(b.x + b.w).toBeLessThanOrEqual(w.width + 0.5);
        expect(b.y + b.h).toBeLessThanOrEqual(w.height + 0.5);
      }
    }
  });
  it("end legend names sit at least one line box (1.2 em) + 2 px apart", () => {
    const crowd = layoutColumnTiers([{ period: "Jan", AC: 4e6, BU: 4.01e6, PY: 3.99e6 }], { ...opts, tiers: [] });
    const ys = byRole(crowd, "legend").map((m) => (m.kind === "text" ? m.y : 0)).sort((a, b) => a - b);
    for (let k = 1; k < ys.length; k++) expect(ys[k]! - ys[k - 1]!).toBeGreaterThanOrEqual(1.2 * tokens.typography.size.label.px + 2 - 1e-6);
  });
  it("aligns a Total chart on its own scale with the months: same baselines and tier axes", () => {
    const total: PeriodRow[] = [{ period: "Total", closed: false, AC: 15.9e6, BU: 15.7e6, PY: 14.9e6, delta: 0.2e6, deltaPct: 0.013 }];
    const tOpts = { ...opts, width: 120, ppu: 8 / 1e6, legend: true };
    const a = alignTiers(layoutColumnTiers(months, opts), layoutColumnTiers(total, tOpts));
    const m2 = layoutColumnTiers(months, { ...opts, minTierPx: a });
    const t2 = layoutColumnTiers(total, { ...tOpts, minTierPx: a });
    for (const t of ["pct", "delta", "base"] as const) expect(t2.tiers[t].y0).toBeCloseTo(m2.tiers[t].y0);
    expect(t2.height).toBeCloseTo(m2.height);
    // a tiny Δ on the Total's scale is still drawn, at ≥ 1 px
    expect(rect(t2.marks.find((m) => m.role === "variance")).h).toBeGreaterThanOrEqual(1);
  });
  it("rings only the cited value label", () => {
    const h = layoutColumnTiers(months, { ...opts, highlight: { category: "Feb", tier: "delta" } });
    expect(byRole(h, "marker-ellipse")).toHaveLength(1);
  });
});

describe("rev-4: labels, legend, pins, bands", () => {
  const months12: PeriodRow[] = Array.from({ length: 12 }, (_, i) => ({
    period: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i]!,
    period2: i < 6 ? "2025" : "2026",
    closed: i < 9, AC: i < 9 ? (3.5 + (i % 3) * 0.2) * 1e6 : null, FC: i >= 9 ? 3.9e6 : null,
    BU: 3.7e6, PY: (3.4 + (i % 4) * 0.25) * 1e6, delta: ((i % 5) - 2) * 0.11e6, deltaPct: ((i % 5) - 2) * 0.03,
  }));
  const base = { ...opts, ppu: 30 / 1e6 };
  it("no placed label overlaps a column, triangle, pin or another label of its tier", () => {
    for (const width of [300, 390, 520, 1000]) {
      const l = layoutColumnTiers(months12, { ...base, width });
      const obstacles = l.marks.filter((m) => m.kind !== "text" && /^(col-|triangle-|pin|variance$|outlier)/.test(m.role)).map(markBox);
      const labels = l.marks.filter((m) => m.kind === "text" && (m.role === "label" || m.role === "variance-label")).map(markBox);
      for (const b of labels) for (const ob of obstacles) expect(overlaps(b, ob)).toBe(false);
      for (let a = 0; a < labels.length; a++) for (let b = a + 1; b < labels.length; b++) expect(overlaps(labels[a]!, labels[b]!, 0)).toBe(false);
    }
  });
  it("thinning keeps cited, first and last labels at phone width", () => {
    const l = layoutColumnTiers(months12, { ...base, width: 300, keep: ["May"] });
    const cats = new Set(l.marks.filter((m) => m.role === "label").map((m) => m.category));
    for (const c of ["Jan", "May", "Dec"]) expect(cats.has(c)).toBe(true);
  });
  it("category labels thin to a regular rhythm", () => {
    const long = months12.map((r) => ({ ...r, period: `${r.period} 2026` }));
    const l = layoutColumnTiers(long, { ...base, width: 300 });
    const idx = l.marks.filter((m) => m.role === "category" && m.kind === "text" && !/^\d{4}$/.test(m.text)).map((m) => long.findIndex((r) => r.period === m.category));
    const gaps = new Set(idx.slice(1).map((v, k) => v - idx[k]!));
    expect(idx[0]).toBe(0);
    expect(gaps.size).toBe(1);
  });
  it("names an outlined reference at the upper part of its column", () => {
    const l = layoutColumnTiers([{ period: "Jan", AC: 4e6, BU: 4e6 }], { ...base, tiers: [] });
    const y = (t: string) => (l.marks.find((m) => m.role === "legend" && m.kind === "text" && m.text === t) as { y: number }).y;
    expect(y("BU")).toBeLessThan(y("AC"));
  });
  it("draws a pin that does not round to zero at least head/2 + 2 px long", () => {
    const l = layoutColumnTiers([{ ...months[0]!, deltaPct: 0.006 }], { ...base, pctPpu: 100 });
    const pin = rect(l.marks.find((m) => m.role === "pin"));
    const head = rect(l.marks.find((m) => m.role === "pin-head"));
    expect(pin.h).toBeGreaterThanOrEqual(head.h / 2 + 2 - 1e-9);
  });
  it("sizes the pin tier to its extent: the largest |Δ%| has a stem of at least 40 % of the tier (proof run 1)", () => {
    for (const tierPx of [48, 80]) {
      const l = layoutColumnTiers(months, { ...opts, pctPpu: undefined, pctTierPx: tierPx });
      const longest = Math.max(...byRole(l, "pin").map((m) => rect(m).h));
      expect(longest).toBeGreaterThanOrEqual(0.4 * tierPx);
      expect(longest).toBeLessThanOrEqual(0.9 * tierPx + 1e-6);
    }
    // the page's "%" group: the smallest px per unit of its pin tiers wins
    expect(pinScale([{ min: -0.05, max: 0.1, tierPx: 48 }, { min: -0.5, max: 0.2, tierPx: 90 }])).toBeCloseTo((0.9 * 90) / 0.5);
  });
  it("pins have a small head at the stem end and a zero pin keeps a baseline marker", () => {
    const l = layoutColumnTiers(months, { ...opts, pctPpu: undefined });
    for (const h of byRole(l, "pin-head")) expect(rect(h).w).toBe(tokens.geometry.pin.headPx.min);
    const mar = l.marks.filter((m) => m.role === "pin-head" && m.category === "Mar"); // +0.01 % rounds to zero
    expect(mar).toHaveLength(1);
    expect(mar[0]!.impact).toBe("none");
    expect(rect(mar[0]).y + rect(mar[0]).h / 2).toBeCloseTo(l.tiers.pct.y0);
    expect(l.marks.some((m) => m.role === "pin" && m.category === "Mar")).toBe(false);
    expect(byRole(l, "variance-label").some((m) => m.kind === "text" && m.text === "+5.6%")).toBe(true); // one decimal
  });
  it("month names never get an ellipsis: Jan, then J, then two rows", () => {
    const year = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((period) => ({ period, AC: 1e6, BU: 1e6 }));
    for (const width of [900, 300, 150]) {
      const l = layoutColumnTiers(year, { ...opts, width, tiers: [] });
      const cats = byRole(l, "category").map((m) => (m.kind === "text" ? m.text : ""));
      expect(cats.join("")).not.toContain("…");
      expect(cats).toHaveLength(12);
    }
    expect(periodLabels(["Jan", "Feb"], 12, 20).texts).toEqual(["J", "F"]);
    expect(periodLabels(["Jan", "Feb"], 12, 6).rows).toBe(2);
    expect(periodLabels(["Q1", "Q2"], 12, 12).texts).toEqual(["Q1", "Q2"]); // no ambiguous single letter
  });
  it("neighbouring value labels keep a 2 px gap at phone width", () => {
    const l = layoutColumnTiers(months.concat(months.map((r) => ({ ...r, period: r.period + "2" }))), { ...opts, width: 326 });
    const boxes = byRole(l, "label").map(markBox).sort((a, b) => a.x - b.x);
    for (let k = 1; k < boxes.length; k++) if (Math.abs(boxes[k]!.y - boxes[k - 1]!.y) < boxes[k]!.h) expect(boxes[k]!.x - (boxes[k - 1]!.x + boxes[k - 1]!.w)).toBeGreaterThanOrEqual(2 - 1e-6);
  });
  it("keeps the extremes first, then the last AC month, when labels are thinned", () => {
    const narrow = byRole(layoutColumnTiers(months, { ...opts, width: 170 }), "label").map((m) => m.category);
    expect(narrow).toEqual(expect.arrayContaining(["Jan", "Apr"])); // smallest and largest value
    for (const width of [200, 230, 260, 300]) {
      const base = byRole(layoutColumnTiers(months, { ...opts, width }), "label").map((m) => m.category);
      if (base.length >= 3) { expect(base).toContain("Mar"); return; } // last AC once there is room for a third
    }
    throw new Error("no width placed three labels");
  });
  it("labels the scale band above it at the left edge, inside the box, in the secondary text colour", () => {
    const l = layoutColumnTiers(months, { ...base, scaleBand: 2e6 });
    const lab = l.marks.find((m) => m.role === "scale-band-label")!;
    const band = rect(l.marks.find((m) => m.role === "scale-band"));
    const b = markBox(lab);
    expect(lab).toMatchObject({ text: "2.0", fill: tokens.color.text.secondary });
    expect(b.y + b.h).toBeLessThanOrEqual(band.y + 0.5);
    expect(b.x).toBeGreaterThanOrEqual(-0.5);
  });
  it("prints the year under the first month and where it changes, only when it varies", () => {
    const l = layoutColumnTiers(months12, base);
    expect(l.marks.filter((m) => m.kind === "text" && /^20\d\d$/.test(m.text)).map((m) => (m as { text: string }).text)).toEqual(["2025", "2026"]);
    const one = layoutColumnTiers(months12.map((r) => ({ ...r, period2: "2026" })), base);
    expect(one.marks.some((m) => m.kind === "text" && m.text === "2026")).toBe(false);
  });
  it("wraps a long name to two lines only when the row step allows it", () => {
    expect(fitLines("Region North West", 12, 70, 28)).toHaveLength(2);
    expect(fitLines("Region North West", 12, 70, 20)).toHaveLength(1);
    expect(fitLines("Region North West", 12, 70, 20)[0]).toMatch(/…$/);
  });
});

describe("structure bars", () => {
  const rows = [
    { category: "North", AC: 5e6, BU: 4.6e6, delta: 0.4e6, deltaPct: 0.087 },
    { category: "South", AC: 3e6, BU: 3.3e6, delta: -0.3e6, deltaPct: -0.091 },
    { category: "Other", AC: 0, BU: 0.4e6, delta: -0.4e6, deltaPct: -1, remainder: true },
    { category: "Total", AC: 8e6, BU: 8.3e6, delta: -0.3e6, deltaPct: -0.036, total: true },
  ];
  const l = layoutStructureBars(rows, { width: 640, reference: "BU", ppu: 40 / 1e6, pctPpu: 120, scale, polarity: 1 });
  it("draws triangles, Δ bars on the base px per unit and pins", () => {
    expect(byRole(l, "triangle-BU")).toHaveLength(4);
    const north = rect(l.marks.find((m) => m.role === "variance" && m.category === "North"));
    expect(north.w).toBeCloseTo(0.4e6 * 40 / 1e6);
    expect(byRole(l, "pin")).toHaveLength(4);
  });
  it("a discontinued member keeps its Δ (0 − reference) and its label", () => {
    expect(l.marks.some((m) => m.role === "variance" && m.category === "Other")).toBe(true);
  });
  it("names scenarios once, above the top row", () => {
    expect(byRole(l, "legend").map((m) => (m.kind === "text" ? m.text : ""))).toEqual(["AC", "BU"]);
  });
  it("warns when the tiers do not fit", () => {
    expect(layoutStructureBars(rows, { width: 200, reference: "BU", ppu: 40 / 1e6, pctPpu: 120, scale }).warnings.join()).toMatch(/stack the tiers/);
  });
});

describe("variance waterfall", () => {
  const bridge = {
    base: { label: "PY", scenario: "PY" as const, value: 10e6 },
    steps: [{ label: "Volume", delta: 1.2e6 }, { label: "Price", delta: -0.4e6, impact: -1 as const }, { label: "Mix", delta: 0.2e6, fc: true }],
    total: { label: "AC", scenario: "AC" as const, value: 11e6 },
    variance: { code: "ΔPY", value: 1e6, impact: 1 as const },
  };
  it("floats steps on running totals and colours them by impact", () => {
    const l = layoutVarianceWaterfall(bridge, { width: 520, ppu: 30 / 1e6, scale });
    expect(l.warnings).toEqual([]);
    const v = l.marks.filter((m) => m.role === "variance" && m.kind === "rect").map(rect);
    expect(v[1]!.fill).toBe(C.variance.bad);
    expect(v[2]!.fill).toEqual({ hatch: C.variance.good });
    expect(v[1]!.x).toBeCloseTo(v[0]!.x + v[0]!.w - 0.4e6 * 30 / 1e6);
  });
  it("warns when the bridge does not reconcile", () => {
    const l = layoutVarianceWaterfall({ ...bridge, total: { ...bridge.total, value: 12e6 } }, { width: 520, ppu: 30 / 1e6, scale });
    expect(l.warnings.join()).toMatch(/remainder/);
  });

  // Small contributions next to a large base: the magnifier case (CH 4.5; 5 % trigger is OURS).
  const small = {
    base: { label: "PY", scenario: "PY" as const, value: 40e6 },
    steps: [{ label: "Volume", delta: 0.6e6 }, { label: "Price", delta: 0.3e6 }, { label: "Mix", delta: -0.2e6 }, { label: "Currency", delta: -0.1e6 }],
    total: { label: "AC", scenario: "AC" as const, value: 40.6e6 },
    variance: { code: "ΔPY", value: 0.6e6 },
  };
  const zo = { ppu: 8 / 1e6, scale };
  const inZoom = (l: Layout) => l.marks.filter((m) => m.group === "zoom");
  it("magnifies when the largest step is below 5 % of the base, with the smallest k from 1, 2, 5, 10 …", () => {
    expect(magnifierFactor(0.6e6 * zo.ppu)).toBe(10); // 4.8 px → ×10 = 48 px ≥ 40
    expect(magnifierFactor(25)).toBe(2);
    expect(magnifierFactor(40)).toBe(1);
    const l = layoutVarianceWaterfall(small, { width: 760, ...zo });
    expect(byRole(l, "zoom-box")).toHaveLength(1);
    expect(byRole(l, "magnifier-caption").map((m) => (m.kind === "text" ? m.text : ""))).toEqual(["Steps ×10"]);
    expect(byRole(l, "magnifier-connector")).toHaveLength(2);
    expect(layoutVarianceWaterfall(bridge, { width: 520, ppu: 30 / 1e6, scale }).marks.some((m) => m.role === "zoom-box")).toBe(false);
    expect(layoutVarianceWaterfall(small, { width: 760, ...zo, magnifyBelow: 0 }).marks.some((m) => m.role === "zoom-box")).toBe(false);
  });
  it("keeps base and total on the page scale and draws the steps ×k in the panel only", () => {
    const l = layoutVarianceWaterfall(small, { width: 760, ...zo });
    expect(rect(l.marks.find((m) => m.role === "bar-PY")).w).toBeCloseTo(40e6 * zo.ppu);
    expect(rect(l.marks.find((m) => m.role === "bar-AC")).w).toBeCloseTo(40.6e6 * zo.ppu);
    const panelVol = rect(inZoom(l).find((m) => m.role === "variance" && m.category === "Volume"));
    expect(panelVol.w).toBeCloseTo(0.6e6 * zo.ppu * 10);
    // step labels only in the panel
    const stepLabels = l.marks.filter((m) => m.role === "variance-label" && m.category && m.category !== "AC" && m.category !== "PY");
    expect(stepLabels.every((m) => m.group === "zoom")).toBe(true);
  });
  it("aligns the panel rows with the overview rows when it sits beside, and moves it below on a phone", () => {
    const l = layoutVarianceWaterfall(small, { width: 760, ...zo });
    for (const cat of ["Volume", "Price", "Mix", "Currency"]) {
      const ov = rect(l.marks.find((m) => m.role === "variance" && m.category === cat && !m.group));
      const pz = rect(inZoom(l).find((m) => m.role === "variance" && m.category === cat));
      expect(pz.y).toBeCloseTo(ov.y);
      expect(pz.x).toBeGreaterThan(ov.x);
    }
    const phone = layoutVarianceWaterfall(small, { width: 390, ppu: 5 / 1e6, scale });
    expect(phone.warnings).toEqual([]);
    const box = rect(phone.marks.find((m) => m.role === "zoom-box"));
    const pz = rect(inZoom(phone).find((m) => m.role === "variance" && m.category === "Volume"));
    expect(pz.y).toBeGreaterThan(box.y + box.h);
    expect(inZoom(phone).some((m) => m.role === "category")).toBe(true); // names repeated below
  });
  it("puts no label on the zoom box outline or a connector, and keeps labels inside the chart", () => {
    for (const [width, ppu] of [[390, 5 / 1e6], [760, zo.ppu]] as const) {
      const l = layoutVarianceWaterfall(small, { width, ppu, scale });
      expect(l.warnings).toEqual([]);
      const zb = rect(l.marks.find((m) => m.role === "zoom-box"));
      const edges = [
        { x: zb.x, y: zb.y, w: zb.w, h: 0 }, { x: zb.x, y: zb.y + zb.h, w: zb.w, h: 0 },
        { x: zb.x, y: zb.y, w: 0, h: zb.h }, { x: zb.x + zb.w, y: zb.y, w: 0, h: zb.h },
        ...byRole(l, "magnifier-connector").map(markBox),
      ];
      for (const t of l.marks.filter((m) => m.kind === "text")) {
        const b = markBox(t);
        for (const e of edges) expect(overlaps(b, e), `${(t as { text: string }).text} at ${width}`).toBe(false);
        expect(b.x).toBeGreaterThanOrEqual(-0.5);
        expect(b.x + b.w).toBeLessThanOrEqual(l.width + 0.5);
        expect(b.y + b.h).toBeLessThanOrEqual(l.height + 0.5);
      }
    }
  });
});

describe("time waterfall (A-11)", () => {
  const byQuarter = {
    base: { label: "PY", scenario: "PY" as const, value: 10e6 },
    steps: [{ label: "Q1", delta: 0.8e6 }, { label: "Q2", delta: -0.3e6 }, { label: "Q3", delta: 0.5e6 }, { label: "Q4", delta: 0.0002e6 }],
    total: { label: "AC", scenario: "AC" as const, value: 11.0002e6 },
    variance: { code: "ΔPY", value: 1.0002e6 },
  };
  const l = layoutTimeWaterfall(byQuarter, { width: 520, ppu: 12 / 1e6, scale });
  it("draws reference | periods | AC on a broken axis with floating Δ columns", () => {
    expect(byRole(l, "axis")).toHaveLength(3);
    expect(byRole(l, "col-PY")).toHaveLength(1);
    expect(byRole(l, "col-AC")).toHaveLength(1);
    const q2 = rect(l.marks.find((m) => m.role === "variance" && m.category === "Q2"));
    expect(q2.fill).toBe(C.variance.bad);
    expect(q2.h).toBeCloseTo(0.3e6 * 12 / 1e6);
    // Q4 rounds to zero: no column, an unsigned label
    expect(l.marks.some((m) => m.role === "variance" && m.category === "Q4" && m.kind === "rect")).toBe(false);
    expect(l.marks.find((m) => m.role === "variance-label" && m.category === "Q4")).toMatchObject({ text: "0.0", impact: "none" });
  });
  it("draws the total variance as a vertical arrow right of the AC column", () => {
    const ac = rect(l.marks.find((m) => m.role === "col-AC"));
    const arrow = l.marks.find((m) => m.role === "variance" && m.kind === "line");
    expect(arrow?.kind === "line" && arrow.x1 === arrow.x2 && arrow.x1 > ac.x + ac.w).toBe(true);
    expect(byRole(l, "variance-label").some((m) => m.kind === "text" && m.text === "ΔPY +1.0")).toBe(true);
  });
  const tinyQ = { ...byQuarter, base: { ...byQuarter.base, value: 100e6 }, total: { ...byQuarter.total, value: 101.0002e6 }, variance: { code: "ΔPY", value: 1.0002e6 } };
  const tiny = layoutTimeWaterfall(tinyQ, { width: 520, ppu: 1.2 / 1e6, scale });
  it("keeps every label inside the chart, clear of the zoom box and the connectors", () => {
    for (const lay of [l, tiny]) {
      expect(lay.warnings).toEqual([]);
      const zb = lay.marks.find((m) => m.role === "zoom-box");
      const edges = zb && zb.kind === "rect"
        ? [{ x: zb.x, y: zb.y, w: zb.w, h: 0 }, { x: zb.x, y: zb.y + zb.h, w: zb.w, h: 0 }, { x: zb.x, y: zb.y, w: 0, h: zb.h }, { x: zb.x + zb.w, y: zb.y, w: 0, h: zb.h }, ...byRole(lay, "magnifier-connector").map(markBox)]
        : [];
      for (const m of lay.marks.filter((x) => x.kind === "text")) {
        const b = markBox(m);
        expect(b.x).toBeGreaterThanOrEqual(-0.5);
        expect(b.x + b.w).toBeLessThanOrEqual(lay.width + 0.5);
        expect(b.y).toBeGreaterThanOrEqual(-0.5);
        expect(b.y + b.h).toBeLessThanOrEqual(lay.height + 0.5);
        for (const e of edges) expect(overlaps(b, e), (m as { text: string }).text).toBe(false);
      }
    }
  });
  it("magnifies small periodic Δ in a tier below, each column under its period, base and AC on the page scale", () => {
    expect(byRole(tiny, "magnifier-caption").map((m) => (m.kind === "text" ? m.text : ""))).toEqual([`Steps ×${magnifierFactor(0.8e6 * 1.2 / 1e6)}`]);
    const k = magnifierFactor(0.8e6 * 1.2 / 1e6);
    const ov = rect(tiny.marks.find((m) => m.role === "variance" && m.category === "Q1" && !m.group));
    const pz = rect(tiny.marks.find((m) => m.role === "variance" && m.category === "Q1" && m.group === "zoom"));
    expect(pz.x).toBeCloseTo(ov.x);
    expect(pz.h).toBeCloseTo(0.8e6 * 1.2 / 1e6 * k);
    expect(pz.y).toBeGreaterThan(ov.y + ov.h);
    expect(rect(tiny.marks.find((m) => m.role === "col-PY")).h).toBeCloseTo(100e6 * 1.2 / 1e6);
    expect(tiny.marks.filter((m) => m.role === "variance-label" && /^Q/.test(m.category ?? "")).every((m) => m.group === "zoom")).toBe(true);
  });
});

describe("proof run 1: sums, names, labels clear of lines, one magnifier form", () => {
  const rows = [
    { category: "Services and other income", AC: 5e6, BU: 4.6e6, delta: 0.4e6, deltaPct: 0.087 },
    { category: "Boilers", AC: null, BU: 0.4e6, delta: -0.4e6, deltaPct: -1 }, // discontinued: AC blank
    { category: "Total", AC: 5e6, BU: 5.0e6, delta: 0, deltaPct: 0, total: true },
  ];
  it("a blank AC with a reference is drawn and labelled 0.0, and Σ row Δ is checked against the total", () => {
    const l = layoutStructureBars(rows, { width: 640, reference: "BU", ppu: 40 / 1e6, scale });
    expect(l.marks.some((m) => m.role === "label" && m.category === "Boilers" && m.kind === "text" && m.text === "0.0")).toBe(true);
    expect(l.warnings.join()).not.toMatch(/Σ row/);
    const broken = layoutStructureBars([rows[0]!, { ...rows[1]!, delta: null }, rows[2]!], { width: 640, reference: "BU", ppu: 40 / 1e6, scale });
    expect(broken.warnings.join()).toMatch(/Σ row ΔBU/);
    expect(broken.warnings.join()).toMatch(/member items/);
  });
  it("uses the free width for long names before cutting them", () => {
    const l = layoutStructureBars(rows, { width: 640, reference: "BU", ppu: 40 / 1e6, scale });
    const name = l.marks.find((m) => m.role === "category" && m.category === "Services and other income");
    expect(name && name.kind === "text" && (name.lines ?? [name.text]).join(" ")).toBe("Services and other income");
  });
  it("structure pins fill their tier and use one decimal", () => {
    const l = layoutStructureBars(rows, { width: 640, reference: "BU", ppu: 40 / 1e6, scale, pctTierPx: 90 });
    const longest = Math.max(...byRole(l, "pin").map((m) => rect(m).w));
    expect(longest).toBeGreaterThanOrEqual(0.4 * 90);
    expect(byRole(l, "variance-label").some((m) => m.kind === "text" && m.text === "+8.7%")).toBe(true);
  });
  const small = {
    base: { label: "PY", scenario: "PY" as const, value: 162.4e6 },
    steps: [{ label: "North", delta: 2.1e6 }, { label: "West", delta: -3.4e6 }, { label: "South", delta: 1.2e6 }, { label: "Direct", delta: -1.3e6 }],
    total: { label: "AC", scenario: "AC" as const, value: 161.0e6 },
    variance: { code: "ΔPY", value: -1.4e6 },
  };
  for (const width of [390, 640, 1000]) {
    it(`bridge at ${width} px: one magnifier form and no label on any line`, () => {
      const l = layoutVarianceWaterfall(small, { width, ppu: 2.5 / 1e6, scale });
      expect(byRole(l, "zoom-box")).toHaveLength(1);
      expect(byRole(l, "magnifier-panel")).toHaveLength(1);
      expect(byRole(l, "axis-break")).toHaveLength(1);
      const panel = rect(l.marks.find((m) => m.role === "magnifier-panel"));
      const glyph = markBox(l.marks.find((m) => m.role === "axis-break")!);
      const cap = markBox(l.marks.find((m) => m.role === "magnifier-caption")!);
      expect(glyph.y + glyph.h).toBeLessThanOrEqual(panel.y + 0.5); // on the panel's origin line, at its top
      expect(Math.abs(cap.x - (glyph.x + glyph.w))).toBeLessThan(8); // next to the caption
      // every connector is dashed and ends on the panel frame (no empty box in between)
      for (const c of byRole(l, "magnifier-connector")) {
        if (c.kind !== "line") continue;
        expect(c.dash).toBeTruthy();
        const onFrame = (x: number, y: number) => (Math.abs(x - panel.x) < 0.5 || Math.abs(x - panel.x - panel.w) < 0.5 || Math.abs(y - panel.y) < 0.5 || Math.abs(y - panel.y - panel.h) < 0.5);
        expect(onFrame(c.x1, c.y1) || onFrame(c.x2, c.y2)).toBe(true);
      }
      const lines = lineBoxes(l.marks);
      for (const t of l.marks.filter((m) => m.kind === "text" && /label/.test(m.role)))
        for (const ln of lines) expect(overlaps(markBox(t), ln), `${t.kind === "text" ? t.text : ""} touches a line`).toBe(false);
    });
  }
  it("time bridge at 390 px: period names without an ellipsis and labels clear of lines", () => {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const bridge = { base: { label: "PY", scenario: "PY" as const, value: 40e6 }, steps: months.map((label, i) => ({ label, delta: (i % 3 - 1) * 0.3e6 })), total: { label: "AC", scenario: "AC" as const, value: 40e6 }, variance: { code: "ΔPY", value: 0 } };
    const l = layoutTimeWaterfall(bridge, { width: 390, ppu: 3 / 1e6, scale });
    expect(byRole(l, "category").map((m) => (m.kind === "text" ? m.text : "")).join("")).not.toContain("…");
    const lines = lineBoxes(l.marks);
    for (const t of l.marks.filter((m) => m.kind === "text" && m.role === "variance-label" && m.category !== undefined))
      for (const ln of lines) expect(overlaps(markBox(t), ln)).toBe(false);
  });
});

describe("renderer", () => {
  it("pattern ids are unique per chart and resolve inside the same svg", () => {
    const l = layoutColumnTiers(months, opts);
    const html = renderToStaticMarkup(<><MarksSvg layout={l} title="A" /><MarksSvg layout={l} title="B" /></>);
    const ids = [...html.matchAll(/<pattern id="([^"]+)"/g)].map((m) => m[1]);
    expect(new Set(ids).size).toBe(ids.length);
    for (const svg of html.split("</svg>").slice(0, 2)) {
      for (const [, ref] of svg.matchAll(/url\(#([^)]+)\)/g)) expect(svg).toContain(`<pattern id="${ref}"`);
    }
  });
  it("has role, title, a hidden data table, data-role and data-impact; no NaN", () => {
    const html = renderToStaticMarkup(<MarksSvg layout={layoutColumnTiers(months, opts)} title="Revenue in mEUR" onSelect={() => {}} />);
    expect(html).toMatch(/<svg[^>]*role="img"/);
    expect(html).toContain("<title");
    expect(html).toContain("<caption>Revenue in mEUR</caption>");
    expect(html).toMatch(/data-role="variance" data-impact="good"/);
    expect(html).toMatch(/role="button" tabindex="0"/);
    expect(html).not.toMatch(/NaN|undefined/);
  });
});

describe("KPI card", () => {
  it("absolute first, text tokens, rounded zero unsigned, missing variance left out", () => {
    const html = renderToStaticMarkup(
      <KpiCard label="Revenue" unit="in mEUR" value={15.9e6} scale={scale}
        variances={[{ code: "ΔPY", absolute: 1.0e6, relative: 0.067 }, { code: "ΔBU", absolute: 20, relative: 0.0001 }, { code: "ΔFC", absolute: null, relative: null }]} />,
    );
    expect(html.indexOf("+1.0")).toBeLessThan(html.indexOf("+6.7%"));
    expect(html).toContain(`color:${C.variance.goodText}`);
    expect(html).not.toContain(`color:${C.variance.good};`);
    expect(html).toContain(">0.0<");
    expect(html).not.toContain("ΔFC");
  });
  it("a ratio shows pp only", () => {
    const html = renderToStaticMarkup(<KpiCard label="Margin" unit="in %" ratio value={0.421} scale={{ factor: 1, prefix: "", decimals: 1 }} variances={[{ code: "ΔPY", absolute: 0.021 }]} />);
    expect(html).toContain("42.1%");
    expect(html).toContain("+2.1pp");
  });
});

describe("tokens", () => {
  // Where the generator and the token file live: inside the skill (this reference package), or in
  // an app laid out as the ibcs-fabric-app chart layer says (scripts/ and design/ at the app root).
  const here = fileURLToPath(new URL(".", import.meta.url));
  const skills = join(here, "../../../../..");
  const app = join(here, "../..");
  const source = [
    { script: join(skills, "ibcs-notation/scripts/gen_tokens.mjs"), tokens: join(skills, "ibcs-notation/assets/ibcs-tokens.json"), overrides: null },
    { script: join(app, "scripts/gen_tokens.mjs"), tokens: join(app, "design/ibcs-tokens.json"), overrides: join(app, "ibcs-tokens.overrides.json") },
  ].find((c) => existsSync(c.script) && existsSync(c.tokens));

  it.skipIf(!source)("tokens.generated.ts matches the token file (and overrides)", () => {
    const out = join(mkdtempSync(join(tmpdir(), "ibcs-")), "t.ts");
    const args = [source!.script, "--tokens", source!.tokens, "--out", out];
    if (source!.overrides && existsSync(source!.overrides)) args.push("--overrides", source!.overrides);
    execFileSync("node", args);
    expect(readFileSync(join(here, "tokens.generated.ts"), "utf8")).toBe(readFileSync(out, "utf8"));
  });
});

describe("scale provider", () => {
  function Chart({ max, sink }: { max: number; sink: (ppu: number | undefined) => void }) {
    const ppu = useScale([{ unit: "EUR", min: 0, max, availablePx: 100 }]);
    sink(ppu.get("EUR"));
    return null;
  }
  it("two charts in one provider settle on the smallest px per unit without an update loop", () => {
    const seen: Record<string, number | undefined> = {};
    let root: ReturnType<typeof create> | undefined;
    act(() => {
      root = create(
        <ScaleProvider>
          <Chart max={4e6} sink={(v) => (seen.a = v)} />
          <Chart max={1e6} sink={(v) => (seen.b = v)} />
          <Chart max={2e6} sink={(v) => (seen.c = v)} />
        </ScaleProvider>,
      );
    });
    expect(seen.a).toBeCloseTo(100 / 4e6);
    expect(seen.b).toBeCloseTo(100 / 4e6);
    expect(seen.c).toBeCloseTo(100 / 4e6);
    act(() => root!.unmount());
  });
  it("server rendering without a provider uses the chart's own request", () => {
    let got: number | undefined;
    renderToStaticMarkup(<Chart max={2e6} sink={(v) => (got = v)} />);
    expect(got).toBeCloseTo(100 / 2e6);
  });
});

describe("builder gaps (proof run 1)", () => {
  const rows = [
    { category: "North", AC: 5e6, BU: 1.7e6, delta: 3.3e6, deltaPct: 1.948 },
    { category: "South", AC: 3e6, BU: 3.3e6, delta: -0.3e6, deltaPct: -0.091 },
    { category: "East", AC: 0.2e6, BU: 1.1e6, delta: -0.9e6, deltaPct: -0.818 },
  ];
  const inside = (l: Layout) => {
    for (const m of l.marks.filter((x) => x.kind === "text")) {
      const b = markBox(m);
      expect(b.x, `${m.kind === "text" ? m.text : ""} cut at the left`).toBeGreaterThanOrEqual(-0.5);
      expect(b.x + b.w, `${m.kind === "text" ? m.text : ""} cut at the right`).toBeLessThanOrEqual(l.width + 0.5);
    }
  };
  it("time bridge at 390 px keeps the base and total labels inside the box", () => {
    const months12 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const b = { base: { label: "PY", scenario: "PY" as const, value: 151.8e6 }, steps: months12.map((label, i) => ({ label, delta: ((i % 3) - 1) * 1.1e6 })), total: { label: "AC", scenario: "AC" as const, value: 151.8e6 }, variance: { code: "ΔPY", value: 0 } };
    for (const width of [326, 390]) {
      const l = layoutTimeWaterfall(b, { width, ppu: 1 / 1e6, scale: pickScale([151.8e6]) });
      inside(l);
      expect(l.marks.some((m) => m.kind === "text" && m.role === "label" && m.text === "152")).toBe(true);
    }
  });
  it("stacks structure tiers under the bars on phones: same row order, names repeated", () => {
    const opts = { width: 326, reference: "BU" as const, ppu: 15 / 1e6, scale };
    const side = layoutStructureBars(rows, opts);
    expect(side.warnings.join()).toMatch(/stack the tiers/);
    const l = layoutStructureBars(rows, { ...opts, stack: "auto" });
    expect(l.warnings.join()).not.toMatch(/tiers need/);
    inside(l);
    const names = byRole(l, "category").map((m) => m.category);
    expect(names).toEqual([...rows, ...rows, ...rows].map((r) => r.category)); // three blocks, same order
    expect(byRole(l, "tier-name").map((m) => (m.kind === "text" ? m.text : ""))).toEqual(["ΔBU", "ΔBU%"]);
    expect(byRole(l, "bar-AC")).toHaveLength(3); // bars drawn once
    const ys = byRole(l, "tier-name").map((m) => markBox(m).y);
    expect(ys[1]!).toBeGreaterThan(ys[0]!); // the Δ% block sits under the Δ block
    // wide enough: "auto" keeps the tiers side by side
    expect(byRole(layoutStructureBars(rows, { ...opts, width: 900, stack: "auto" }), "category")).toHaveLength(3);
  });
  it("KPI card: centred by default, left on request; undefined Δ% omitted, N/A only for a null Δ% with reference ≤ 0", () => {
    const sc = { factor: 1e6, prefix: "m", decimals: 1 };
    const centred = renderToStaticMarkup(<KpiCard label="Revenue" unit="in mEUR" value={10e6} scale={sc} variances={[{ code: "ΔBU", absolute: 0.3e6 }]} />);
    expect(centred).toContain('data-align="center"');
    expect(centred).toContain("text-align:center");
    expect(renderToStaticMarkup(<KpiCard label="R" unit="u" value={1e6} scale={sc} align="start" variances={[]} />)).toContain('data-align="start"');
    // relative undefined: no Δ% part, never N/A
    const omitted = renderToStaticMarkup(<KpiCard label="R" unit="u" value={1e6} scale={sc} variances={[{ code: "ΔBU", absolute: 0.3e6, relative: undefined }]} />);
    expect(omitted).not.toContain("N/A");
    expect(omitted).not.toContain("%<");
    // null with a reference ≤ 0: N/A; null with a positive or missing reference: left out
    const na = renderToStaticMarkup(<KpiCard label="R" unit="u" value={1e6} scale={sc} variances={[{ code: "ΔPY", absolute: 1.2e6, relative: null, reference: -0.2e6 }]} />);
    expect(na).toContain(">N/A<");
    const missing = renderToStaticMarkup(<KpiCard label="R" unit="u" value={1e6} scale={sc} variances={[{ code: "ΔPY", absolute: 1.2e6, relative: null, reference: 0.8e6 }, { code: "ΔFC", absolute: 0.1e6, relative: null }]} />);
    expect(missing).not.toContain("N/A");
  });
  it("variance to BU and PY on one month chart: two absolute tiers on the base scale, each with its axis", () => {
    const both = months.map((r) => ({ ...r, delta2: (r.AC ?? r.FC ?? 0) - (r.PY ?? 0) }));
    const l = layoutColumnTiers(both, { ...opts, tiers: ["delta", "delta2"], reference2: "PY" });
    expect(byRole(l, "tier-name").map((m) => (m.kind === "text" ? m.text : ""))).toEqual(["ΔBU", "ΔPY"]);
    expect(byRole(l, "axis-BU").length).toBeGreaterThan(0);
    expect(byRole(l, "axis-PY")).toHaveLength(1);
    expect(l.tiers.delta.y0).toBeLessThan(l.tiers.delta2.y0); // ΔBU above ΔPY, both above the base
    expect(l.tiers.delta2.y0).toBeLessThan(l.tiers.base.y0);
    const jan = l.marks.filter((m) => m.role === "variance" && m.category === "Jan").map(rect);
    expect(jan.map((b) => b.h).sort((a, b) => a - b)[1]).toBeCloseTo(0.3e6 * opts.ppu); // AC 3.8 − PY 3.5 on the base px per unit
    expect(l.table[0]).toEqual(["Period", "AC&FC", "BU", "PY", "ΔBU", "ΔPY"]);
    // the default stays one comparison: no ΔPY tier unless asked
    expect(byRole(layoutColumnTiers(both, opts), "axis-PY")).toHaveLength(0);
  });
  it("structure bars keep outlier pin labels inside the chart", () => {
    for (const pctPpu of [undefined, 60, 120]) {
      const l = layoutStructureBars(rows, { width: 640, reference: "BU", ppu: 15 / 1e6, pctPpu, scale });
      expect(l.warnings.join()).not.toMatch(/tiers need/);
      inside(l);
      // the outlier label sits beyond its marker with a gap
      const lab = markBox(l.marks.find((m) => m.kind === "text" && m.text === "+194.8%")!);
      const tri = markBox(l.marks.find((m) => m.role === "outlier")!);
      expect(lab.x).toBeGreaterThanOrEqual(tri.x + tri.w + 2);
    }
  });
});

describe("pin tiers on different % scales are marked (OURS, UN 5.2 / CH 4.3)", () => {
  const regions = [
    { category: "North", AC: 5e6, BU: 4.6e6, delta: 0.4e6, deltaPct: 0.087 },
    { category: "Other", AC: 0.2e6, BU: 0.45e6, delta: -0.25e6, deltaPct: -0.556, remainder: true },
  ];
  const tiers = [
    { id: "months", min: -0.0488, max: 0.0556, tierPx: 48 },
    { id: "regions", min: -0.556, max: 0.087, tierPx: 90 },
  ];
  it("pinScaleBand picks a round value 25–60 % of the tier", () => {
    for (const [tierPx, ppu] of [[48, 0.9 * 48 / 0.0556], [90, 0.9 * 90 / 0.556], [48, 100]] as const) {
      const band = pinScaleBand(tierPx, ppu);
      expect([0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1]).toContain(band);
      expect(band * ppu).toBeLessThanOrEqual(0.6 * tierPx + 1e-9);
    }
    expect(pinScaleBand(48, 0.9 * 48 / 0.0556) * (0.9 * 48 / 0.0556)).toBeGreaterThanOrEqual(0.25 * 48);
  });
  it("pagePinScales: charts read together share one scale; differing scales get a band each", () => {
    const one = pagePinScales([{ ...tiers[0]!, group: "m" }, { id: "total", min: 0, max: 0.013, tierPx: 48, group: "m" }]);
    expect(one.get("months")!.differs).toBe(false);
    expect(one.get("months")!.band).toBeNull();
    expect(one.get("total")!.ppu).toBe(one.get("months")!.ppu);
    const page = pagePinScales(tiers);
    expect(page.get("months")!.differs).toBe(true);
    expect(page.get("months")!.band).not.toBeNull();
    expect(page.get("regions")!.band).not.toBeNull();
  });
  it("a page with two pin tiers at different scales draws a scaling marker in each, with data-ppu on the pins", () => {
    const page = pagePinScales(tiers);
    const m = layoutColumnTiers(months, { ...opts, pctPpu: page.get("months")!.ppu, pctScaleBand: page.get("months")!.band! });
    const r = layoutStructureBars(regions, { width: 640, reference: "BU", ppu: 40 / 1e6, pctPpu: page.get("regions")!.ppu, pctScaleBand: page.get("regions")!.band!, scale });
    for (const l of [m, r]) {
      const bands = l.marks.filter((x) => x.role === "scale-band" && x.tier === "pct");
      expect(bands).toHaveLength(1);
      expect(l.marks.some((x) => x.role === "scale-band-label" && x.tier === "pct")).toBe(true);
      const ppus = new Set(l.marks.filter((x) => x.role === "pin").map((x) => x.ppu));
      expect(ppus.size).toBe(1);
    }
    expect(m.marks.find((x) => x.role === "pin")!.ppu).not.toBeCloseTo(r.marks.find((x) => x.role === "pin")!.ppu!);
    // the marker's label stays inside the box and clear of the tier name and of every pin label
    for (const l of [m, r]) {
      const label = l.marks.find((x) => x.role === "scale-band-label")!;
      const b = markBox(label);
      expect(b.x).toBeGreaterThanOrEqual(-0.5);
      expect(b.y).toBeGreaterThanOrEqual(-0.5);
      expect(b.x + b.w).toBeLessThanOrEqual(l.width + 0.5);
      for (const other of l.marks.filter((x) => x.kind === "text" && x !== label && (x.role === "tier-name" || x.role === "variance-label")))
        expect(overlaps(b, markBox(other))).toBe(false);
    }
    const html = renderToStaticMarkup(<MarksSvg layout={m} title="ΔBU%" />);
    expect(html).toMatch(/data-role="pin"[^>]*data-ppu="/);
    expect(html).toMatch(/data-role="scale-band"[^>]*data-tier="pct"/);
  });
});

