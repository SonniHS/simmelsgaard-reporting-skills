# Page shell: canvas, cards, header, KPI row, footnotes

A report page is easier to scan when its parts sit on separate white "sheets": a header card with
the key message and title, a row of KPI cards, one card per chart block, and a footnote card, on
a light neutral canvas. The cards are a **layout grouping only** (ours, grounded in IBCS SI 1 and
UN 2): no borders, shadows, rounded corners or colour; inside a card every IBCS rule for a white
page holds. Numbers below are for a 1280 px wide page (`FitToWidth`, height = content), with the
`layout.*` tokens (margin 16, gutter 12). Status: the theme switch and the numbers are built and
lint-checked, and a full page built from them rendered in the service as specified (2026-10, PDF
export). Check the first page after publishing anyway (SKILL.md §6 step 7).

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
| header card | 16 | 16 | 1248 | 206 |
| KPI cards (5) | 16, 268, 520, 772, 1024 | 234 | 240 | 142 |
| first chart card | 16 | 388 | 1248 | title 36 + subtitle 24 + charts + 12 |
| next card | 16 | previous bottom + 12 | 1248 (or 618 + 12 + 618 for two side by side) | — |
| page height | — | — | — | last card bottom + 16 |

Four KPI cards: width (1248 − 3 × 12) / 4 = 303; three: 408. Two chart cards side by side: 618 each.

## 3. Header card

All visuals white, stacked edge to edge with no canvas showing between them (spans touch: a visual
ends where the next begins), x = 16 unless stated:

| Visual | Position (x, y, w, h) | Content |
|---|---|---|
| key message | 16, 16, 1076, 84 | `tableEx` with the SVG key message (ibcs-svg-dax skeleton 7): one image column, `displayName: " "`, column header font 8 pt. Its empty header strip renders **about 28 px** high and is the card's top padding. Column width 1030, SVG and `grid.imageWidth` 1010, `imageHeight` 48 (two lines of 17 px bold at 22 px line height + 4): 28 + 48 + 8 = 84 |
| logo (optional) | 1092, 16, 172, 84 | `image` visual, the organisation's logo at most 148 × 40, right-aligned, padding 12 (top 14); the linter lists it (A1) for review: one logo in the header card's corner, nowhere else |
| title lines | 16, 100, 1248, 58 | three text cards or one text box: who / **what** in unit / when, 10–11 pt, about 19 px per line |
| slicers | 16, 158, 212, 64 / 228, 158, 272, 64 | dropdown slicers with **short headers** ("Company", "Period"), padding bottom 12 (the card's bottom padding); spans 16–228 and 228–500 |
| scope chips | 500, 158, 764, 32 (+ a second line 500, 190, 764, 32) | text from the **slicer top**: what the selection means ("all companies, intercompany included ¹", "none = Jan..last closed month ²"), 9 pt grey, footnote numbers; span 500–1264 |

The card ends at y 222 (158 + 64). Never leave a gap between two visuals of one card: the grey
canvas shows through as a hole in the sheet.

**No rules in image tables.** A `tableEx` draws a line under its (empty) column header and between
rows. In every image table of the shell set `columnHeaders` and `values` `outline` to `'None'`,
and `grid` `outlineColor` white with `outlineWeight` 0. A column exactly as wide as the visual's
content width scrolls: keep column width = `imageWidth` + 20 and the visual at least column
width + its left/right padding + 2.

The explanation of a slicer's empty state goes into the scope chips or a footnote, never into the
slicer header: a header longer than about (width − 16) / 7 characters is cut with an ellipsis
(the linter fails it).

Fallback for the message when the SVG route is not wanted: a `cardVisual` on the plain-text
message measure with `value.bold` true and 13 pt (pbir-skeleton.md §6): bold, numbers black.

## 4. KPI row

One visual per KPI, so the canvas shows between the cards (one `tableEx` holding all cards would
be one white strip, and with column width < `imageWidth` + 20 it draws a stray "." per card):

- `tableEx` (x, 234, 240, 142), one image column bound to the card's SVG measure
  (ibcs-svg-dax skeleton 4), `displayName: " "`, column header 8 pt (its empty header strip,
  about 28 px, is the top padding); no rules (§3).
- Visual padding left 10, right 0, top 0, bottom 0; column width 220; `grid.imageWidth` 200,
  `imageHeight` 104 (28 + 104 + 10 = 142).
- The card SVG at **200 × 104**: in skeleton 4 set `width='200'` and `viewBox='0 0 200 104'` and
  move the x positions: centre 120 → 100, Δ% end 100 → 84, Δ end 176 → 147, scenario code 184 → 154.
  Text sizes stay 12 / 28 px (never scale the SVG to fit: the labels would shrink below 12 px).
- Inside a card: label (measure name, semibold) and unit, the big AC value, then one line per
  comparison: Δ% and Δ in the text impact colours, the scenario code (ΔPY, ΔBU) in black. No
  separators, icons or backgrounds; a value the message names gets the highlight ellipse.

## 5. Chart cards

- **Title inside the card:** two visuals: a text box (16, y, card width, 36) with padding top 12,
  the measure in bold and the dimension ("**Revenue** by month"), 11 pt; below it (y + 36, height
  24) the scenarios, period and variances, 9 pt grey. One 52 px box for both lines scrolls in the
  service. No visual titles on the charts below it.
- **Charts** directly below (y + 60), sized by `scale_layout.py` (SKILL.md §3) plus their padding.
  The first chart of a row gets padding left 12, the last padding right 12; charts between them
  0. The bottom visual of the card gets padding bottom 12 (its position height = computed + 12).
- A Total / year column of a monthly chart is its own visual in the **same** card, right of the
  months, without a gap; it has its own scale only with a scale band in both (Deneb `scaleBand`)
  or a footnote.
  Its tiers line up with the months' only with the same tier ranges: set the same `varMin` /
  `varMax` (Δ tier) and `pinMin` / `pinMax` (Δ% pins) on both visuals and give `scale_layout.py`
  the union ranges; the Δ tier then uses the months' px per unit (`varPxPerUnit`).
- Value labels need room at the right end of bars (and left of negative ones): give
  `scale_layout.py` the longest formatted label (`longestValueLabel`); it names the knob to raise.
- Two-column blocks (e.g. bars by company left, Δ and Δ% right) stay in one card: one Deneb
  visual with all tiers, or visuals edge to edge on one baseline.

## 6. Footnote card

- One text box, full width (16, y, 1248, h), padding 12 top and left/right, 8 pt (≈ 11 px; it renders
  at about 17 px per line), grey `color.text.secondary`. Height = 28 + lines × 17, where lines = Σ over notes of
  ceil(characters × 5.5 / 1224): sized to its text, **never a scroll box** (a scrolled note is not
  printed and not read).
- Last line: source and data as of (`YYYY-MM-DD hh:mm`), so the card is also the page footer. As a
  separate text card below the notes (height 34, padding bottom 12) it closes the card; use the
  same 8 pt as the notes.
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
