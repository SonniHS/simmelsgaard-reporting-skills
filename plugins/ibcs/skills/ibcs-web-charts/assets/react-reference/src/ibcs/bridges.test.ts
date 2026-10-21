// @vitest-environment node
// Bridges fit their card (proof run 2): at phone width the scale shrinks, both bridges keep one scale.
import { describe, expect, it } from "vitest";
import { fitWaterfalls, layoutVarianceWaterfall, markBox, pickScale, type Bridge } from "./index";

const scale = pickScale([33e6]);
const revenue: Bridge = {
  base: { label: "PY", scenario: "PY", value: 31.2e6 },
  steps: [{ label: "Volume", delta: 2.1e6 }, { label: "Price", delta: 0.9e6 }, { label: "Product mix and services", delta: -0.6e6 }, { label: "Currency", delta: -0.3e6 }],
  total: { label: "AC", scenario: "AC", value: 33.3e6 },
  variance: { code: "ΔPY", value: 2.1e6 },
};
const costs: Bridge = {
  base: { label: "BU", scenario: "BU", value: 7.7e6 },
  steps: [{ label: "Personnel", delta: 0.2e6 }, { label: "Rent", delta: 0 }, { label: "IT services", delta: 0.1e6 }, { label: "Travel", delta: -0.1e6 }],
  total: { label: "AC", scenario: "AC", value: 7.9e6 },
  variance: { code: "ΔBU", value: 0.2e6 },
};
const desktopPpu = 30 / 1e6; // about 1000 px for the revenue bridge: far too wide for a phone
const inside = (l: ReturnType<typeof layoutVarianceWaterfall>) =>
  l.marks.every((m) => { const b = markBox(m); return b.x >= -0.5 && b.x + b.w <= l.width + 0.5; });

describe("bridges at phone width", () => {
  for (const width of [326, 390]) {
    it(`never overflow the card at ${width} px`, () => {
      const l = layoutVarianceWaterfall(revenue, { width, ppu: desktopPpu, scale });
      expect(l.warnings.join()).not.toMatch(/waterfall needs/);
      expect(l.ppu!).toBeLessThan(desktopPpu);
      expect(inside(l)).toBe(true);
    });
  }
  it("two bridges read together share one fitted scale", () => {
    const ppu = fitWaterfalls([revenue, costs], { width: 326, ppu: desktopPpu, scale });
    const a = layoutVarianceWaterfall(revenue, { width: 326, ppu, scale });
    const b = layoutVarianceWaterfall(costs, { width: 326, ppu, scale, polarity: -1 });
    expect(a.ppu).toBeCloseTo(ppu);
    expect(b.ppu).toBeCloseTo(ppu);
    expect(inside(a) && inside(b)).toBe(true);
  });
  it("keeps the page scale with fit: false and reports the overflow", () => {
    const l = layoutVarianceWaterfall(revenue, { width: 326, ppu: desktopPpu, scale, fit: false });
    expect(l.warnings.join()).toMatch(/waterfall needs/);
  });
  it("wraps long names before cutting them", () => {
    const l = layoutVarianceWaterfall(revenue, { width: 326, ppu: desktopPpu, scale });
    const names = l.marks.filter((m) => m.kind === "text" && m.role === "category").map((m) => (m.kind === "text" ? m.text : ""));
    expect(names.some((t) => t.includes("…"))).toBe(false);
  });
});
