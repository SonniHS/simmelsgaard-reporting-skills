# Formatting, accessibility, phone and print — recipes and checklists

## Contents
- [Formatting](#formatting)
- [Accessibility checklist (WCAG 2.2 AA)](#accessibility-checklist-wcag-22-aa)
- [Phone layout (≈ 390 px)](#phone-layout--390-px)
- [Print / PDF checklist](#print--pdf-checklist)

## Formatting

| Decision | Default (tokens) | Setting |
|---|---|---|
| Thousands separator | U+202F narrow no-break space (`number.separator.thousands`) | per organisation |
| Decimal sign | `number.separator.decimal` | or the locale's sign — one choice per organisation |
| Negative | `-123` (`number.sign.negative`) | parentheses `(123)` if the organisation insists |
| Plus sign | variances only | — |
| Significant digits | ≤ 3 in charts, ≤ 4 in tables (`number.maxDigits.*`) | — |
| Scaling prefix | k / m / b for money (`number.scaling.monetary`), SI k / M / G for physical units | one per scale group |
| Decimals | automatic rule below, unless the spec sets them | fixed per scale group; the spec's `display` wins |
| Relative variance | whole percent (`number.format.relativeVariance`); one decimal (`relativeVariance1`) if the spec asks | per scale group |
| Plain ratio (book-to-bill) | two decimals, no % (`number.format.plainRatio`) | per measure |
| Not applicable | `N/A` (`number.sign.notApplicable`) | — |
| Percentage points | `pp` (`number.scaling.percentagePoint`) | — |
| Currency | ISO 4217 code with prefix in the title (`mEUR`); never `€` or `M` in labels | currency is a setting |

A small, framework-free formatter is enough:

```ts
type Fmt = { factor?: number; decimals?: number; locale?: string; thousands?: string; decimal?: string };

export function pickScale(values: (number | null)[], maxDigits = 3) {
  const finite = values.filter((x): x is number => x != null && Number.isFinite(x));
  const m = finite.reduce((a, x) => Math.max(a, Math.abs(x)), 0);
  const steps = [ [1e9, "b"], [1e6, "m"], [1e3, "k"], [1, ""]] as const;
  let i = steps.findIndex(([f]) => m / f >= 1);
  if (i < 0) i = steps.length - 1;
  if (i > 0 && Math.round(m / steps[i][0]) >= 10 ** maxDigits) i--; // 999.6k rounds to 1,000k: use m
  const [factor, prefix] = steps[i];
  // token number.scaling.rule: 1 decimal if the largest |value| < 100, else 0 (tested on the
  // value rounded to 1 decimal, so 99.96 → 100 gets 0), never more digits than maxDigits.
  const scaled = Math.round((m / factor) * 10) / 10;
  const intDigits = Math.max(1, Math.floor(Math.log10(Math.max(scaled, 1))) + 1);
  return { factor, prefix, decimals: scaled < 100 && intDigits < maxDigits ? 1 : 0 };
}

// null and non-finite print nothing (a table may show its dash token); N/A is only for a relative
// variance that cannot be interpreted (formatRelative)
export function formatValue(x: number | null, o: Fmt = {}, signed = false): string {
  if (x == null || !Number.isFinite(x)) return "";
  const s = new Intl.NumberFormat(o.locale ?? "en-US", {
    minimumFractionDigits: o.decimals ?? 0, maximumFractionDigits: o.decimals ?? 0,
  }).formatToParts(Math.abs(x / (o.factor ?? 1)))
    .map(p => p.type === "group" ? (o.thousands ?? " ")
            : p.type === "decimal" ? (o.decimal ?? p.value) : p.value).join("");
  if (Math.round(Math.abs(x / (o.factor ?? 1)) * 10 ** (o.decimals ?? 0)) === 0) return s; // zero: no sign
  return (x < 0 ? "-" : signed ? "+" : "") + s;
}

export const formatRelative = (f: number | null, decimals = 0) =>
  f == null ? "N/A" : formatValue(f * 100, { decimals }, true) + "%";
export const formatPp = (points: number | null) =>
  points == null ? "N/A" : formatValue(points, { decimals: 1 }, true) + "pp";

// Precedence: an explicit display setting from the visual spec wins; the automatic rule only
// fills what the spec leaves open. Call once per scale group with all its values.
const FACTOR: Record<string, number> = { "": 1, k: 1e3, m: 1e6, b: 1e9 };
export function resolveFormat(groupValues: (number | null)[], display?: { prefix?: string; decimals?: number }) {
  const auto = pickScale(groupValues);
  const prefix = display?.prefix ?? auto.prefix;
  return { prefix, factor: FACTOR[prefix] ?? auto.factor, decimals: display?.decimals ?? auto.decimals };
}

// Impact key for colour; null = no colour. A delta that rounds to zero at the displayed
// precision is treated like zero (unsigned label, default text colour, no mark).
export function impactKey(delta: number | null, polarity: -1 | 0 | 1, o: { factor?: number; decimals?: number } = {},
                          modelImpact?: -1 | 0 | 1 | null): "good" | "bad" | "neutral" | null {
  if (delta == null || !Number.isFinite(delta)) return null;
  if (Math.round(Math.abs(delta / (o.factor ?? 1)) * 10 ** (o.decimals ?? 0)) === 0) return null;
  if (modelImpact != null) return modelImpact > 0 ? "good" : modelImpact < 0 ? "bad" : "neutral";
  if (polarity === 0) return "neutral";
  return delta * polarity > 0 ? "good" : "bad";
}
// graphics: tokens.color.variance[key]; a tinted NUMBER: tokens.color.variance[`${key}Text`]
// (>= 4.5:1), or color.text.primary when the token set has no text variants.
```

Rules:

- The factor and decimals are fixed once per scale group (`resolveFormat` over all its values,
  with the spec's `display` taking precedence), then applied to every label. The title carries
  `unitPrefix + currency` (`mEUR`). Example: the automatic rule gives 0 decimals for 152.3 mEUR,
  but a spec with `display: {prefix: m, decimals: 1}` prints `152.3`.
- Variance labels are signed; zero — including a value that rounds to zero — is unsigned and
  uncoloured. Relative variance `null` → `N/A`.
- Coordinates are always numbers; formatted strings are for text only.
- Periods follow the token patterns `date.*`; month abbreviations come from `Intl.DateTimeFormat`
  for the chosen locale with any trailing full stop removed.
- Dates arriving as `"2026-03-01T00:00:00"` without a zone: split the string into year, month,
  day; do not pass a date-only string to `new Date()`.

## Accessibility checklist (WCAG 2.2 AA)

- [ ] Each chart: `role="img"` with `<title>` (the title lines) and `<desc>` (what is compared,
      which notation). Interactive charts: `role="group"` with named, focusable marks.
- [ ] A hidden data table (or a visible table) carries every plotted number, N/A included.
- [ ] Keyboard: Tab reaches each interactive mark, Enter/Space activates, focus outline visible
      (`:focus-visible`); selection changes announced (`aria-live="polite"`).
- [ ] Text contrast ≥ 4.5:1: black on white. Variance numbers are black, or tinted with the
      text tokens `color.variance.goodText` / `badText` / `neutralText` (≥ 4.5:1; the rule is in
      the ibcs-notation skill, §3). Never print a number in the bright graphic green (2.4:1);
      bars and pins keep the graphic colours.
- [ ] Colour never alone: signs, direction and hatching carry the same information. Offer the
      `cvd` and `bw` variance colour sets.
- [ ] Tables: `<caption>`, `<th scope="col|row">`; total rows marked for screen readers (row type, e.g. `aria-describedby` or a visually hidden "total"), not only bold; no "Total" in the visible label (SI 4.1).
- [ ] No animation; honour `prefers-reduced-motion` for anything that moves.
- [ ] 200 % zoom and 320 px reflow: no horizontal page scroll; wide tables scroll in their own
      container.

## Phone layout (≈ 390 px)

- Charts measure their container; give grid children `min-width: 0` so they can shrink.
- Check it with device emulation at 390 px, not a 390 px headless window (see `testing.md`).
- Labels stay horizontal; shrink to the minimum label size, then thin out (keep first, last,
  highest, lowest; anchor thinning on the latest period).
- Category-axis thinning goes by **measured label width** with a minimum gap (OURS 6 px), never by
  count alone. A label that must stay (a period carrying the year line, first, last) is placed
  first and every other label must clear it — otherwise "Dec Jan Feb" collide around a year break.
  This applies at every width, not only on the phone.
- Prefer ≤ 12 periods per chart, or switch to quarters.
- Variance tiers stacked above columns keep the same category width and margins so they align.
- Tables: a reduced column set below a breakpoint, or horizontal scroll inside the wrapper with a
  sticky label column and an edge fade while columns are hidden.
- Title block may collapse to one line with separators; dates and ranges never break.

## Print / PDF checklist

- [ ] White page, no shadows or card frames on the report surface.
- [ ] Interactive controls hidden (`@media print`); active filters shown in title line 1.
- [ ] Charts and tables not split across pages (`break-inside: avoid`).
- [ ] Footnote with sources and data timestamp.
- [ ] Same scales as on screen — fix the px per unit when the print width differs.
- [ ] Generate with a headless browser in print media (e.g. Playwright `page.emulateMedia({ media:
      "print" })` then `page.pdf({ format: "A4", landscape: true, printBackground: true })`);
      open the PDF and look at it.
- [ ] Fonts: a system stack (`typography.family.web`) or a self-hosted brand font; no fonts from a
      third-party CDN in reports that must render offline.
