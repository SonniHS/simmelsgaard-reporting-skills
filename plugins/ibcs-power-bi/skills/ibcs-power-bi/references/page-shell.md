# Page shell: canvas, cards, header, KPI row, footnotes

A report page is easier to scan when its parts sit on separate white "sheets": a header card with
the key message and title, a row of KPI cards, one card per chart block, and a footnote card, on
a light neutral canvas. The cards are a **layout grouping only** (ours, grounded in IBCS SI 1 and
UN 2): no borders, shadows, rounded corners or colour; inside a card every IBCS rule for a white
page holds. Numbers below are for a 1280 px wide page (`FitToWidth`, height = content), with the
`layout.*` tokens (margin 16, gutter 12). Status: the theme switch and the numbers are built and
lint-checked; the whole shell has **not yet been rendered in the service** (as of 2026-10). Check
the first page after publishing (SKILL.md §6 step 7).

## Contents
- [1. Theme](#1-theme)
- [2. Grid](#2-grid)
- [3. Header card](#3-header-card)
- [4. KPI row](#4-kpi-row)
- [5. Chart cards](#5-chart-cards)
- [6. Footnote card](#6-footnote-card)
- [7. Checks](#7-checks)

## 1. Theme

```sh
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme --shell cards [--canvas '#F3F3F3'] [--card-padding 12]
```

- Page background and outspace: the canvas `#F3F3F3` (neutral grey, no hue; any `--canvas` must
  stay neutral and light, the linter fails a coloured one).
- Every visual, tables included: background white (`color.background.page`), transparency 0,
  padding left/right 12 px, top/bottom 0. Border, shadow and radius stay off.
- A card is a column of visuals stacked **edge to edge** (no gap): their white backgrounds merge
  into one sheet. Gaps (12 px) exist only between cards, so the canvas shows only there.
- Padding is inside the visual: a Deneb or SVG visual's position = the size from
  `scale_layout.py` + its padding (left + right for width, top + bottom for height).

## 2. Grid

| Part | x | y | width | height |
|---|---|---|---|---|
| margin (all sides) | 16 | 16 | — | — |
| content | 16 | — | 1248 | — |
| gutter between cards (both directions) | — | — | 12 | 12 |
| card padding (inside, via visual padding) | 12 | 12 | — | — |
| header card | 16 | 16 | 1248 | 194 |
| KPI cards (5) | 16, 268, 520, 772, 1024 | 222 | 240 | 128 |
| first chart card | 16 | 362 | 1248 | title 52 + charts + 12 |
| next card | 16 | previous bottom + 12 | 1248 (or 618 + 12 + 618 for two side by side) | — |
| page height | — | — | — | last card bottom + 16 |

Four KPI cards: width (1248 − 3 × 12) / 4 = 303; three: 408. Two chart cards side by side: 618 each.

## 3. Header card

All visuals white, stacked edge to edge, x = 16 unless stated:

| Visual | Position (x, y, w, h) | Content |
|---|---|---|
| key message | 16, 16, 1076, 72 | `tableEx` with the SVG key message (ibcs-svg-dax skeleton 7): one image column, `displayName: " "`, column header font 8 pt (its empty header strip, about 20 px, is the card's top padding), column width 1052, `grid.imageWidth` 1032, `imageHeight` 48 (two lines of 17 px bold at 22 px line height + 4) |
| logo (optional) | 1092, 16, 172, 72 | `image` visual, the organisation's logo at most 148 × 40, right-aligned, padding 12; the linter lists it (A1) for review: one logo in the header card's corner, nowhere else |
| title lines | 16, 88, 1248, 58 | text box (or three text cards): who / **what** in unit / when, 11 pt (14 px font, 18 px lines) |
| slicers | 16, 146, 200, 64 / 228, 146, 260, 64 | dropdown slicers with **short headers** ("Company", "Period"), padding bottom 12 (the card's bottom padding) |
| scope chips | 500, 170, 764, 40 | text: what the selection means ("all companies, intercompany included ¹", "none = Jan..last closed month ²"), 9 pt grey, footnote numbers |

The explanation of a slicer's empty state goes into the scope chips or a footnote, never into the
slicer header: a header longer than about (width − 16) / 7 characters is cut with an ellipsis
(the linter fails it).

Fallback for the message when the SVG route is not wanted: a `cardVisual` on the plain-text
message measure with `value.bold` true and 13 pt (pbir-skeleton.md §6): bold, numbers black.

## 4. KPI row

One visual per KPI, so the canvas shows between the cards (one `tableEx` holding all cards would
be one white strip, and with column width < `imageWidth` + 20 it draws a stray "." per card):

- `tableEx` (x, 222, 240, 128), one image column bound to the card's SVG measure
  (ibcs-svg-dax skeleton 4), `displayName: " "`, column header 8 pt (its empty header strip,
  about 20 px, is the top padding).
- Visual padding left 10, right 0, top 0, bottom 0; column width 230; `grid.imageWidth` 210,
  `imageHeight` 104 (20 + 104 + 4 = 128).
- The card SVG at **210 × 104**: in skeleton 4 set `width='210'` and `viewBox='0 0 210 104'` and
  move the x positions: centre 120 → 105, Δ% end 100 → 88, Δ end 176 → 154, scenario code 184 → 161.
  Text sizes stay 12 / 28 px (never scale the SVG to fit: the labels would shrink below 12 px).
- Inside a card: label (measure name, semibold) and unit, the big AC value, then one line per
  comparison: Δ% and Δ in the text impact colours, the scenario code (ΔPY, ΔBU) in black. No
  separators, icons or backgrounds; a value the message names gets the highlight ellipse.

## 5. Chart cards

- **Title inside the card:** a text box (16, y, card width, 52) with padding top 12: line 1 the
  measure in bold and the dimension ("**Revenue** by month"), 11 pt; line 2 the scenarios,
  period and variances, 9 pt grey. No visual titles on the charts below it.
- **Charts** directly below (y + 52), sized by `scale_layout.py` (SKILL.md §3) plus their padding.
  The first chart of a row gets padding left 12, the last padding right 12; charts between them
  0. The bottom visual of the card gets padding bottom 12 (its position height = computed + 12).
- A Total / year column of a monthly chart is its own visual in the **same** card, right of the
  months, without a gap; it has its own scale only with a scale band in both (Deneb `scaleBand`)
  or a footnote.
- Value labels need room at the right end of bars (and left of negative ones): give
  `scale_layout.py` the longest formatted label (`longestValueLabel`); it names the knob to raise.
- Two-column blocks (e.g. bars by company left, Δ and Δ% right) stay in one card: one Deneb
  visual with all tiers, or visuals edge to edge on one baseline.

## 6. Footnote card

- One text box, full width (16, y, 1248, h), padding 12 on all sides, 8 pt (≈ 11 px, 14 px lines),
  grey `color.text.secondary`. Height = 24 + lines × 14, where lines = Σ over notes of
  ceil(characters × 5.5 / 1224): sized to its text, **never a scroll box** (a scrolled note is not
  printed and not read).
- Last line: source and data as of (`YYYY-MM-DD hh:mm`), so the card is also the page footer.
- Short: one line per note where possible, at most about eight notes. Longer definitions (KPI
  formulas, company names, model compromises) go to a glossary / details page linked from the
  card ("Definitions: page Notes") or into the tooltip of the visual they explain.
- The page footnotes follow the numbered references in the title, chips and charts (¹ ² …).

## 7. Checks

`ibcs_lint.py pbir <name>.Report --layout layout.json` (ibcs-review) checks the shell mechanics:
neutral canvas only with white visuals (A2), slicer headers and titles that would be cut (LINT),
image columns at least `imageWidth` + 20 (LINT), Deneb sizes and px per unit against
`scale_layout.py --json` (G8). What it cannot see: the rendered result. Export the page to PDF
(pbir-skeleton.md §10) and compare it with the spec and this grid.
