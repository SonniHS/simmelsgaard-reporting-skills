// @vitest-environment node
// Pin outliers (OURS): one pin over 3 × the next-largest |Δ%| is clipped and must not flatten the others.
import { describe, expect, it } from "vitest";
import { layoutColumnTiers, layoutStructureBars, markBox, pickScale, pinClip, shortPinWarning, type Mark } from "./index";

const scale = pickScale([12e6]);
const stems = (marks: Mark[]) =>
  marks.filter((m): m is Extract<Mark, { kind: "rect" }> => m.kind === "rect" && m.role === "pin").map((p) => ({ c: p.category, len: Math.max(p.w, p.h) }));

describe("pinClip", () => {
  it("keeps ±100 % when no pin stands out", () => {
    expect(pinClip([0.05, -0.04, 0.03])).toBe(1);
    expect(pinClip([0.5])).toBe(1);
  });
  it("clips just beyond the largest regular pin when one is over 3 × the next", () => {
    expect(pinClip([-1, -0.024, -0.023, 0.01])).toBeCloseTo(0.024 * 1.15);
    expect(pinClip([-1, -0.024, -0.023], 1, 0)).toBe(1); // rule off
  });
  it("handles two outliers in a row", () => {
    expect(pinClip([0.9, -0.5, 0.02, 0.01])).toBeCloseTo(0.02 * 1.15);
  });
});

describe("structure pins with a −100 % member (the Legacy case)", () => {
  const rows = [
    { category: "Heat", AC: 9e6, BU: 9.22e6, delta: -0.22e6, deltaPct: -0.024 },
    { category: "Ctrl", AC: 6e6, BU: 6.14e6, delta: -0.14e6, deltaPct: -0.023 },
    { category: "Pumps", AC: 4e6, BU: 3.93e6, delta: 0.07e6, deltaPct: 0.018 },
    { category: "Service", AC: 2e6, BU: 2.02e6, delta: -0.02e6, deltaPct: -0.01 },
    { category: "Legacy", AC: 0, BU: 0.004e6, delta: -0.004e6, deltaPct: -1 },
  ];
  const opts = { width: 760, reference: "BU" as const, ppu: 20 / 1e6, scale, pctTierPx: 90 };

  it("scales the tier from the other pins: their stems are at least 40 % of the tier", () => {
    const l = layoutStructureBars(rows, opts);
    for (const s of stems(l.marks).filter((s) => s.c !== "Legacy" && s.c !== "Service")) expect(s.len).toBeGreaterThanOrEqual(0.4 * 90);
    expect(l.marks.some((m) => m.role === "outlier" && m.category === "Legacy")).toBe(true);
    expect(l.marks.some((m) => m.kind === "text" && m.category === "Legacy" && m.text === "-100.0%")).toBe(true);
    expect(l.warnings.join()).not.toMatch(/under 4 px/);
  });

  it("without the rule most pins are under 4 px and the layout warns", () => {
    const l = layoutStructureBars(rows, { ...opts, outlierRatio: 0 });
    expect(l.warnings.join()).toMatch(/pins are under 4 px beyond the minimum stem/);
  });

  it("applies to month pins too", () => {
    const months = ["Jan", "Feb", "Mar", "Apr"].map((period, i) => ({ period, AC: 4e6, BU: 4e6, delta: 0.1e6, deltaPct: [0.02, -0.015, 0.012, -0.95][i] }));
    const l = layoutColumnTiers(months, { width: 520, reference: "BU", ppu: 30 / 1e6, scale, pctTierPx: 48 });
    for (const s of stems(l.marks).filter((s) => s.c !== "Apr")) expect(s.len).toBeGreaterThanOrEqual(0.4 * 48 * 0.6);
    expect(l.marks.some((m) => m.role === "outlier" && m.category === "Apr")).toBe(true);
  });
});

describe("shortPinWarning", () => {
  it("flags a tier where more than half of the pins are under 4 px", () => {
    const pin = (h: number): Mark => ({ kind: "rect", role: "pin", x: 0, y: 0, w: 3, h });
    expect(shortPinWarning([pin(5), pin(6), pin(30)])).toMatch(/2 of 3/);
    expect(shortPinWarning([pin(5), pin(30), pin(30)])).toBeNull();
  });
});

describe("thinning at phone width keeps the extremes first (proof run 2)", () => {
  it("keeps the largest Δ and Δ% of a 12-month chart at 326 px", () => {
    const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const pct = [0.021, -0.013, 0.034, 0.018, -0.022, 0.011, 0.026, 0.124, -0.031, 0.015, 0.009, -0.017];
    const months = names.map((period, i) => ({ period, closed: i < 9, AC: i < 9 ? 4e6 : null, FC: i >= 9 ? 4e6 : null, BU: 4e6 / (1 + pct[i]!), delta: 4e6 - 4e6 / (1 + pct[i]!), deltaPct: pct[i] }));
    const l = layoutColumnTiers(months, { width: 326, reference: "BU", ppu: 25 / 1e6, scale: pickScale([4e6]), pctTierPx: 48 });
    const kept = (t: string) => l.marks.some((m) => m.kind === "text" && m.role === "variance-label" && m.category === "Aug" && m.text === t);
    expect(kept("+12.4%")).toBe(true);
    expect(l.marks.some((m) => m.kind === "text" && m.role === "variance-label" && m.category === "Sep" && m.text === "-3.1%")).toBe(true);
  });
});

describe("structure pin band label", () => {
  it("never overlaps the tier name", () => {
    const rows = [
      { category: "North", AC: 5e6, BU: 4.6e6, delta: 0.4e6, deltaPct: 0.087 },
      { category: "West", AC: 3e6, BU: 3.3e6, delta: -0.3e6, deltaPct: -0.091 },
      { category: "Other", AC: 0.4e6, BU: 0.9e6, delta: -0.5e6, deltaPct: -0.556, remainder: true },
    ];
    const l = layoutStructureBars(rows, { width: 640, reference: "BU", ppu: 40 / 1e6, scale: pickScale([5e6]), pctTierPx: 60, pctScaleBand: "auto" });
    const label = l.marks.find((m) => m.role === "scale-band-label");
    const name = l.marks.find((m) => m.role === "tier-name" && m.kind === "text" && m.text === "ΔBU%");
    expect(label && name).toBeTruthy();
    const a = markBox(label!), b = markBox(name!);
    const overlap = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
    expect(overlap).toBe(false);
  });
});
