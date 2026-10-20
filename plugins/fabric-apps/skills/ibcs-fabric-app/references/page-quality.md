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
- Capped category widths (the `ibcs-web-charts` behaviour contract caps column categories so
  stacked tiers align) can leave a chart narrower than its card. That is not dead space to fill
  by stretching columns past the cap: size the card to the chart, give the row a second visual,
  or use the width for the extended Total column and the series labels. Never break the cap or
  the shared scale to fill a card.
- The plot area dominates its card: titles, legends and notes take at most about a third.
- Bars, columns and rows keep the token weights; same unit, same scale across the page; scale
  bands where scales must differ.
- Text sizes from the type scale only; tabular numbers; labels never overlap or get cut (shorten in
  the middle), tab and title rows never wrap at 1280–1600 px.
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

## 4. How to check

- Screenshot every page at 1280, ≈ 1050 (the portal's content width) and 390 px (default state
  plus one filter change); review against
  the three sections; fix; screenshot again.
- Have an independent reviewer (a fresh agent or a colleague) score each page 1–5 on value,
  proportions and looks, with the worst three findings; rework pages under 4.
