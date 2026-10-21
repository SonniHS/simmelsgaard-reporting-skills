// One test per contract rule (references/testing.md). DOM-free on the layouts; the renderer and
// the KPI card are server-rendered to strings.
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import {
  KpiCard, MarksSvg, alignTiers, formatDelta, formatPercentDelta, formatPp, formatValue, impactFill, impactKey, impactText,
  layoutColumnTiers, layoutStructureBars, layoutVarianceWaterfall, markBox, pickScale, pxPerUnit, tokens,
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
    expect(byRole(o, "variance-label").some((m) => m.kind === "text" && m.text === "+250%")).toBe(true);
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
  it("end legend names sit at least font + 2 px apart", () => {
    const crowd = layoutColumnTiers([{ period: "Jan", AC: 4e6, BU: 4.01e6, PY: 3.99e6 }], { ...opts, tiers: [] });
    const ys = byRole(crowd, "legend").map((m) => (m.kind === "text" ? m.y : 0)).sort((a, b) => a - b);
    for (let k = 1; k < ys.length; k++) expect(ys[k]! - ys[k - 1]!).toBeGreaterThanOrEqual(tokens.typography.size.label.px + 2 - 1e-6);
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
    expect(html.indexOf("+1.0")).toBeLessThan(html.indexOf("+7%"));
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
