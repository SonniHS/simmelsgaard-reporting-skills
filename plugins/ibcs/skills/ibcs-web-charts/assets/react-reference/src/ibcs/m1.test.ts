// Proof run 3, M1: at phone width the month chart dropped the ΔBU labels of the highlighted month (Sep)
// and of others. Highlighted, selected and each tier's largest |Δ| are never dropped; colliding labels
// stagger to the other side of the axis or step one px smaller first; Δ% keeps one decimal.
import { describe, expect, it } from "vitest";
import { layoutColumnTiers, layoutStructureBars, markBox, overlaps, pickScale, type Mark } from "./index";
import { m1Months } from "./m1Fixture";

const texts = (l: { marks: Mark[] }) => l.marks.filter((m): m is Extract<Mark, { kind: "text" }> => m.kind === "text");

describe("M1: phone labels on the month chart", () => {
  for (const width of [326, 390]) {
    it(`keeps Sep (highlighted) and Aug (largest |Δ|) labelled, nothing collides, Δ% one decimal at ${width} px`, () => {
      const l = layoutColumnTiers(m1Months, {
        width, reference: "BU", triangle: "PY", ppu: 120 / 36e6, pctTierPx: 48, scale: pickScale([36e6]),
        polarity: 1, selected: "Sep", highlight: { category: "Sep", tier: "delta" },
      });
      const dLabels = texts(l).filter((m) => m.role === "variance-label" && !m.text.endsWith("%"));
      const labelled = new Set(dLabels.map((m) => m.category));
      expect(labelled.has("Sep")).toBe(true);
      expect(labelled.has("Aug")).toBe(true);
      const pct = texts(l).filter((m) => m.role === "variance-label" && m.text.endsWith("%"));
      for (const m of pct) expect(m.text).toMatch(/^(?:[+-]\d+\.\d|0\.0)%$/);
      const lab = texts(l).filter((m) => m.role === "label" || m.role === "variance-label");
      const obstacles = l.marks.filter((m) => m.kind !== "text" && /^(col-|triangle-|pin|pin-head|variance$|outlier)/.test(m.role)).map(markBox);
      for (let a = 0; a < lab.length; a++) {
        const ba = markBox(lab[a]!);
        for (let b = a + 1; b < lab.length; b++) expect(overlaps(ba, markBox(lab[b]!))).toBe(false);
        for (const ob of obstacles) expect(overlaps(ba, ob)).toBe(false);
      }
      for (const m of lab) expect(m.size).toBeGreaterThanOrEqual(10);
    });
  }
});

describe("Drivers at phone width (regression check)", () => {
  for (const width of [262, 326]) {
    it(`wraps a long driver name instead of cutting it at ${width} px`, () => {
      const rows = [
        { category: "Volume", AC: 18.4e6, BU: 17.1e6, delta: 1.3e6, deltaPct: 1.3 / 17.1 },
        { category: "Services and other income", AC: 4.1e6, BU: 4.3e6, delta: -0.2e6, deltaPct: -0.2 / 4.3 },
      ];
      const l = layoutStructureBars(rows, { width, reference: "BU", stack: "auto", ppu: 8 / 1e6, scale: pickScale([20e6]), polarity: 1 });
      const name = texts(l).find((m) => m.role === "category" && m.category === "Services and other income")!;
      expect(name.lines?.length ?? 1).toBe(2);
      expect((name.lines ?? [name.text]).join(" ")).not.toContain("…");
    });
  }
});
