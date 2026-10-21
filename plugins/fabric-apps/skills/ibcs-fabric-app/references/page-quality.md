# Page quality rubric *(ours)*

The IBCS rules (the `ibcs-review` skill, plugin `ibcs`) are the floor. This rubric adds page-level
judgement: a page is done when every element earns its place and the page reads as one composition
at phone and desktop width.

## 1. Value: every element earns its place

- The page answers one question, stated by its key message; every visual supports or explains it.
- Each visual answers the next question a reader would ask (what moved, where, why, what next). A
  visual that repeats another at a different grain without a new insight goes, or moves to a detail
  page.
- No filler: no chart drawn because the data exists, no KPI card without a comparison, no table
  that restates a chart.
- Every visual has a finding you can say in one sentence; if not, it is the wrong visual or page.

## 2. Proportions: one composition

- Hierarchy by size: the message visual is the largest, supporting visuals smaller, detail last.
- Rows align: equal card heights in a row; plot areas start and end on the same lines; tables and
  charts in one row share a baseline.
- No dead space: no half-empty cards, no chart squeezed into a strip inside a tall card. Content
  height decides card height, not the grid.
- In a fixed cell the month categories fill the cell's width and columns take 2/3 of each
  category (`ibcs-web-charts` behaviour contract §2); thin columns with wide gaps are a defect.
  Only a chart that sizes itself caps its step; then size the card to the chart, give the row a
  second visual, or use the width for the Total column and the series labels. Never break the
  shared scale to fill a card.
- The plot area dominates its card: titles, legends and notes take at most about a third.
- Bars, columns and rows keep the token weights; same unit, same scale across the page; scale
  bands where scales must differ.
- Text sizes from the type scale only; tabular numbers; labels never overlap or get cut (shorten from
  the end with an ellipsis, or wrap to two lines), tab and title rows never wrap at 1280–1600 px.
- Footnote markers match both ways: every ¹ in a title, chip or label has the same number in the
  footnote list, and every numbered footnote is referenced. An unnumbered footnote list next to
  numbered chips is a defect.
- Series and scenario labels (AC, PY, BU, FC) once per chart, never repeated above and below.
- Impact-coloured **text** (KPI deltas, coloured labels) uses the text tokens `goodText`/`badText`;
  the graphic green and red are for marks only.

## 3. Looks right at both widths

- 1280 px: the first screen shows the message and the main visual without scrolling.
- 390 px: one column, no horizontal page scroll, charts redrawn for the width (fewer labels, not
  shrunk), every number readable.
- Consistent chrome across apps: top bar, filter bar, page frame, cards, footer.

## 4. Shell checks

The frame of [report-shell.md](report-shell.md), at 390, ≈ 1050 and 1280 px:

- [ ] Header row: logo, area name and tabs on one line at 1280 and ≈ 1050 px; the active tab does
      not change the row width; tools never cut.
- [ ] Filter bar: entity, period, compare with and Reset present; every control as wide as its
      longest option; each active value appears in title line 1 or 3; Reset keeps the page.
- [ ] Compare with switches the notation (reference tiers, Δ codes, title line 3, headline
      clauses), not only the numbers.
- [ ] Headline bold with impact-coloured variance numbers (text tokens) and the rule under it;
      "in line with" below the materiality threshold; at most two findings, the mover ringed.
- [ ] Chips end in footnote numbers that link to the footer; numbers match both ways.
- [ ] KPI cards: one equal row, (i) opens the definition, a ring only on numbers the headline
      cites; values tabular and never cut.
- [ ] Chart cards: title inside; selected month band through all tiers; Total in its own cell
      with its own scale and a scale band; series labels at the end of the series, once.
- [ ] Header card with the shared rhythm (headline 17/22 px → 12 → title lines 14/19 px → 12 →
      chips) and a footnote card full width at the end (report-shell §5, §8).
- [ ] Footer full width: every footnote complete (no scroll box, no ellipsis), source, data as
      of, last closed month.
- [ ] Card shape: rounded cards by default (radius 8, 1 px ring, soft shadow on a 5 % canvas) or
      square by option; cards in one row equally tall, content top-aligned; no card taller than
      its content + padding; no frame, shadow or radius on charts, tables or text inside a card.
- [ ] Pins carry magnitude: the largest |Δ%| has a stem of at least 40 % of its tier, heads are
      6 px at the stem end, a rounded-zero Δ% keeps a baseline marker, labels one decimal.
- [ ] No ellipsis on month names (Jan → J → two rows); long names use the free width first; no
      label touches an axis, baseline, frame, connector or assisting line (waterfalls included).
- [ ] Rows that explain a total add up to it: a member without AC but with a reference shows
      `0.0` and its Δ (member items); Σ row Δ = the total's Δ.
- [ ] Total next to the months: its base and Δ tiers on its own scale (a scale band in the base
      and in the Δ tier of both charts, footnote), baselines and tier axes at the months' y; tiny Δ drawn (≥ 1 px) with its label.
- [ ] End legends right of the last month and right of the Total only, top to bottom, BU at the
      upper part of its column; no label over a bar or a triangle (collision rule, chart-layer.md).
- [ ] End legends at their marks' y with ≥ font + 2 px between names; a zero Δ printed unsigned.
- [ ] In the portal (not only the harness): footnote numbers are visible as text; a tab change
      opens the new page at the top; every chart fills its card's content width.
- [ ] Theme, card style and density survive a reload (viewer preference); a reload and Back
      inside the portal keep page, entity, period and comparison (shareable deep links from the
      portal were not available as of 2026-10: [app-patterns.md](app-patterns.md) §6).
- [ ] Phone: header in two rows, filters behind one toggle with a summary, KPI cards two per
      row, no horizontal page scroll.

## 5. How to check

- Screenshot every page at 1280, ≈ 1050 (the portal's content width) and 390 px (default state
  plus one filter change); review against
  the three sections; fix; screenshot again.
- Have an independent reviewer (a fresh agent or a colleague) score each page 1–5 on value,
  proportions and looks, with the worst three findings; rework pages under 4.
