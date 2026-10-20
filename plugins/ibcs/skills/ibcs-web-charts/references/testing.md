# Testing IBCS web charts

Test the notation, the arithmetic and the scale — not pixels — wherever possible. Pure layout
functions (`layout(data, options) → { marks, warnings }` with a `role` on every mark) make most
tests DOM-free.

## Unit tests on layout functions

Write at least one test per rule; each is a few lines with any test runner (Vitest, Jest, node:test).

| Rule | Assertion |
|---|---|
| Scenario notation | AC marks filled with the AC token; PL marks white fill with AC stroke; FC marks filled with a pattern reference and outlined; PY marks light. |
| Overlap | The reference mark is drawn **before** the primary and shifted left (columns) / up (bars) by the token ratio. |
| AC → FC | Closed periods use AC, the open period and later use FC hatched — a partial AC of the open period is not drawn; FC is never drawn twice when FC is the reference. |
| Relative variance | `(AC − REF) / REF` with the signed reference; REF ≤ 0 → `null` → label `N/A`, no pin. |
| Δ = 0 | No mark, no colour, unsigned `0` label — also for a Δ that rounds to zero at the visual's decimals (`0.0005` at 2 decimals → `0.00`). |
| Tinted numbers | Variance numbers use `color.variance.*Text` (or black), never the graphic `good`/`bad`; the text colour has ≥ 4.5:1 against the background. |
| Pins and triangles | Stem, head and triangle sizes stay inside the px clamps (`geometry.pin.stemPx`, `.headPx`, `geometry.triangleSizePx`) for a very wide and a very narrow column. |
| Polarity | Cost increase: geometry up/right, colour bad. Polarity 0: neutral. Model impact overrides polarity. |
| Non-finite | NaN / ±∞ → no mark and a warning; lines break. |
| Shared scale | Two charts of one unit with different extents get the same px per unit; the smaller chart is shorter. Absolute variance tier uses the base unit; pins use `"%"`. |
| Fixed scale | A fixed px per unit is used exactly; the chart grows and warns. |
| Outliers | A flagged relative value (pin) does not set the extent, is truncated with a marker, keeps its full label. An `outlier` flag on an absolute bar or total is ignored with a warning. |
| Waterfalls | Running totals; subtotal mismatch and bridge mismatch raise warnings. |
| Formatting | One factor and decimals per scale group; an explicit spec `display` wins over the automatic rule; signed variances; `pp`; separators from the tokens or the chosen locale. |
| Labels | Thinning keeps first, last, highest, lowest. |

## DOM tests

Render the component (Testing Library, or server-render to a string) and assert:

- every chart `svg` has `role`, a `<title>` and a hidden table whose cells match the data;
- FC elements use `fill="url(#…)"` that resolves to a `<pattern>` in the same SVG, with a unique
  id per instance (render two charts and compare ids);
- variance marks carry the impact colour from the tokens for given polarity / impact, and
  variance numbers the text variant (`color.variance.*Text`), queried by `data-role` /
  `data-impact` (SKILL §8);
- interactive marks are focusable and respond to Enter and Space;
- `null` produces no element, not a zero-height one.

The same checks on a whole page: save the rendered HTML (or one chart's `<svg>`) and run the
ibcs-review linter on it — `python3 -I <ibcs-review skill>/scripts/ibcs_lint.py dom page.html`
(exit 1 = a failed must-rule). It needs the `data-role` attributes; it cannot see colours set
only in a stylesheet class.

## Visual regression

Snapshot each component and a representative page at **390 px and 1280 px** in a headless
browser, plus the **content width of the host** that embeds the page (a Fabric portal item
leaves ≈ 1050 px beside its navigation; an iframe, a SharePoint column). Label collisions show up
first between the breakpoints: a check at 390 and 1280 alone passed a chart whose axis labels
collided at 1050. Along with screenshots, assert:

- `document.documentElement.scrollWidth === clientWidth` (no horizontal page scroll);
- no chart below a minimum height, no console errors, no `NaN`/`undefined` in the page text;
- **no text collides and no text is clipped** in any chart (below) — page scroll and console
  checks alone pass a page whose legend sits on its labels;
- the print media rendering (PDF) still contains hatching and the footnote.

Review new snapshots by eye next to the matching figures in your copy of the IBCS Standards
before accepting them.

### Phone screenshots at 390 px

Emulate the device viewport. A headless browser started with `--window-size=390,844` does not
give a 390 px layout: the window has a minimum width, so the page lays out wider and the
screenshot hides horizontal-scroll bugs. Set the viewport instead and assert it took effect:

```js
// Playwright (Node)
import { chromium } from "playwright";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
// or, on an existing page: await page.setViewportSize({ width: 390, height: 844 });
await page.goto(url, { waitUntil: "networkidle" });
const m = await page.evaluate(() => ({
  inner: window.innerWidth,
  scroll: document.documentElement.scrollWidth,
  client: document.documentElement.clientWidth,
}));
if (m.inner !== 390) throw new Error(`viewport not emulated: ${m.inner}px`);
if (m.scroll > m.client) throw new Error(`horizontal page scroll: ${m.scroll} > ${m.client}`);
await page.screenshot({ path: "page-390.png", fullPage: true });
await browser.close();
```

### Label collisions and clipping

Run this in the page after it has settled, at both widths, and fail on any hit. It compares the
rendered boxes of every `<text>` inside each chart: two labels whose boxes overlap, or a label
outside its `<svg>` (clipped at the edge), is a defect even when the screenshot looks fine at a
glance.

```js
const textIssues = await page.evaluate(() => {
  const hits = [];
  for (const svg of document.querySelectorAll("svg[role=img]")) {
    const frame = svg.getBoundingClientRect();
    const t = [...svg.querySelectorAll("text")]
      .filter((el) => el.textContent.trim())
      .map((el) => ({ el, b: el.getBoundingClientRect(), id: `${el.dataset.role ?? "text"}:${el.textContent}` }));
    for (const x of t) {
      if (x.b.left < frame.left - 1 || x.b.right > frame.right + 1 ||
          x.b.top < frame.top - 1 || x.b.bottom > frame.bottom + 1) hits.push(`clipped ${x.id}`);
    }
    for (let i = 0; i < t.length; i++) for (let j = i + 1; j < t.length; j++) {
      const a = t[i].b, b = t[j].b;
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 1.5 && oy > 2) hits.push(`overlap ${t[i].id} × ${t[j].id}`);   // 1-2 px tolerance for glyph boxes
    }
  }
  return hits;
});
if (textIssues.length) throw new Error(textIssues.join("\n"));
```

Run it for every route and for the loading, empty and error states too (drive them with a
test-only query parameter or the layout harness), and save the page HTML of each passing run for
the `dom` lint.

With the Chrome DevTools Protocol directly (Puppeteer, a CDP client, or a DevTools automation
tool), send `Emulation.setDeviceMetricsOverride` with `{ width: 390, height: 844,
deviceScaleFactor: 2, mobile: true }` before loading the page, then run the same assertions and
take the screenshot. Repeat at the host's content width (e.g. 1050 × 720) and at 1280 × 720 (`mobile: false`). Look at both images before
accepting them.

## Accessibility tests

Run axe (e.g. `@axe-core/playwright`) on the pages in CI; check keyboard flow manually once per
component; test with a screen reader that the title and the hidden table are announced.

## Before hand-over

1. Type check and unit tests green.
2. Screenshots at both widths inspected.
3. Run the [ibcs-review](../../ibcs-review/SKILL.md) skill on the page and fix its findings.
