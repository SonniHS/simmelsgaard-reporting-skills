# Page shell: canvas, cards, header, KPI row, footnotes

A report page is easier to scan when its parts sit on separate white "sheets": a header card with
the key message and title, a row of KPI cards, one card per chart block, and a footnote card, on
a light neutral canvas. **Default: rounded cards** (`--shell fluent-cards`): white, a 1 px ring,
radius 8 and a soft shadow. Square white cards without ring or shadow (`--shell cards`) are the
option. The card shape is **chrome outside the content** (house style, ours: not stated by IBCS,
grounded in SI 1 and UN 2 as a layout grouping); inside a card every IBCS rule for a white page
holds: no frames, shadows, colour or decoration on charts, tables or text. Numbers below are for
a 1280 px wide page (`FitToWidth`, height = content): margin 16, gap between cards 16, card
padding 16. Status: both shells rendered in the service (2026-10, PDF export). The first
fluent-cards render taught three things now built into the theme: the card look must sit on the
shape visual's **container** (background, border with radius in px, shadow), not on the shape
object (its fill was ignored and the cards came out dark grey; `roundEdge` 8 rendered at about
20 % of the card height); `basicShape` is not styled at all (Microsoft's validator rejects its
`outline` and `shape` objects); and content visuals sit at z ≥ 1000 or the card hides them.
Check the first page after publishing (SKILL.md §6 step 7).

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
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme --shell [--card-padding 16]
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme --shell cards [--canvas '#F3F3F3']
```

Chrome tokens (both routes; the app uses the same values, ibcs-fabric-app report-shell.md §9):

| Token | Value |
|---|---|
| canvas | 5 % ink (`color.text.primary`) over the page colour (#F2F2F2 with black ink on white) |
| card | white (`color.background.page`) |
| ring | 1 px, 10 % ink (#E6E6E6) |
| radius | 8 px |
| shadow | distance 2, blur 4, transparency 88 (ink colour), outer, downwards |
| card padding / gap / margin | 16 / 16 / 16 px |

- **fluent-cards (default).** Every card is one `shape` visual (rectangle) placed behind its
  content (lower z: shapes 0–999, content 1000+; `to_pbir.py` places Deneb visuals at z 1000 by
  default and the linter fails a content visual below a shape it overlaps), exactly the card's
  rectangle. The theme styles the shape's **visual container** as the card (background white,
  border 1 px ring with radius 8 px, shadow) and the shape object itself transparent without
  outline; it gives content visuals **no background** (so the ring and the rounded corners stay
  visible) and padding left/right 16. Inset content that fills its cell edge to edge (tables) by
  the radius (8 px) at the card's corners, or it covers the ring and the rounded corner. Only shapes carry an outline or
  shadow; the linter fails a border or shadow on any content visual (A4) and content on the grey
  canvas outside a card shape (A2). Chosen over border + radius + shadow on the content visuals:
  a card is several visuals stacked edge to edge, and per-visual borders would draw seams and a
  shadow under every piece.
- **cards (square).** No shapes; every visual, tables included, has a white background and padding
  left/right 16; the white visuals stacked edge to edge form the sheet. Canvas `#F3F3F3` (any
  `--canvas` must stay neutral and light; the linter fails a coloured one).
- A card is a column of visuals stacked **edge to edge** (no gap). Gaps (16 px) exist only between
  cards, so the canvas shows only there.
- Padding is inside the visual: a Deneb or SVG visual's position = the size from
  `scale_layout.py` + its padding (left + right for width, top + bottom for height).

## 2. Grid

| Part | x | y | width | height |
|---|---|---|---|---|
| margin (all sides) | 16 | 16 | — | — |
| content | 16 | — | 1248 | — |
| gap between cards (both directions) | — | — | 16 | 16 |
| card padding (inside, via visual padding) | 16 | 16 | — | — |
| header card (two-line message) | 16 | 16 | 1248 | 215 (one-line message: 193) |
| KPI cards (5) | 16, 268, 520, 772, 1024 | 247 | 236 (last 240) | 131 |
| first chart card | 16 | 394 | 1248 | title 40 + subtitle 24 + charts + 16 |
| next card | 16 | previous bottom + 16 | 1248 (or 616 + 16 + 616 for two side by side) | — |
| page height | — | — | — | last card bottom + 16 |

Four KPI cards: width (1248 − 3 × 16) / 4 = 300; three: 405 (last 406). Two chart cards side by
side: 616 each. With a one-line message every y below the header moves up by 22 (KPI row 225,
first chart card 372). In fluent-cards mode add one shape per card at exactly these rectangles.

Cards in one row have **equal heights**: the row height is its tallest card's content + padding,
and every card of the row gets that height (content top-aligned; the extra space sits at the
bottom of the shorter cards, the only allowed empty bottom).

## 3. Header card

All visuals white, stacked edge to edge with no canvas showing between them (spans touch: a visual
ends where the next begins), x = 16 unless stated:

| Visual | Position (x, y, w, h) | Content |
|---|---|---|
**Vertical rhythm** (fixed, top to bottom): key message → 12 px → the three title lines at
consecutive line height (no blank line between them) → at least 12 px → the slicer labels. The
message visual ends where its text ends (no spare image height), and the 12 px gaps are the
**top padding** of the next visual, never canvas. Positions for a two-line message:

| Visual | Position (x, y, w, h) | Content |
|---|---|---|
| key message | 16, 16, 1076, 65 | `tableEx` with the SVG key message (ibcs-svg-dax skeleton 7): one image column, `displayName: " "`, column header font 8 pt. Its empty header strip renders **about 17 px** high (measured in the service, 2026-10) and is the card's top padding. Column width 1030, SVG and `grid.imageWidth` 1010, `imageHeight` = lines × 22 + 4 (two lines of 17 px bold at 22 px line height: 48; one line: 26). Height = 17 + `imageHeight` (65; one line 43) |
| logo (optional) | 1092, 16, 172, 65 | `image` visual, the organisation's logo at most 148 × 40, right-aligned, padding 16; the linter lists it (A1) for review: one logo in the header card's corner, nowhere else |
| title lines | 16, 81, 1248, 70 | one text box (or three text cards edge to edge, the first one with the padding) with **padding top 12** (the rhythm gap; left/right 16): who / **what** in unit / when, 10–11 pt, 19 px per line: 12 + 3 × 19 + 1 = 70 |
| slicers | 16, 151, 212, 80 / 228, 151, 272, 80 | dropdown slicers with **padding top 12** (the gap below title line 3) and bottom 16 (the card's bottom padding): 12 + 52 + 16 = 80; spans 16–228 and 228–500 |
| scope chips | 500, 151, 764, 38 (+ a second line 500, 189, 764, 38) | text from the **slicer label top** (padding top 12): what the selection means ("all companies, intercompany included ¹", "none = Jan..last closed month ²"), 9 pt grey, footnote numbers; span 500–1264 |

The card ends at y 231 (151 + 80); with a one-line message 22 px higher (message 43, titles at 59,
slicers at 129, card end 209). Never leave a gap between two visuals of one card: the grey canvas
shows through as a hole in the sheet. The linter fails slicer labels less than 12 px below the
text box above them (it compares visual boxes and their own padding, not the rendered text).

**No rules in image tables.** A `tableEx` draws a line under its (empty) column header and between
rows. In every image table of the shell set `grid` `outlineColor` white with `outlineWeight` 0 (and
`gridHorizontal` / `gridVertical` off). Do **not** set `columnHeaders` or `values` `outline` to
`'None'`: Microsoft's PBIR validator rejects that value. A column exactly as wide as the visual's
content width scrolls: keep column width = `imageWidth` + 20 and the visual at least column width +
its left/right padding + 2.

**Slicer headers.** Default: the short form with its meaning in brackets when it fits the slicer,
e.g. "Company (all = <group>)" or "Period (none = <default>)"; otherwise just "Company" /
"Period". It fits when (characters × 7) + 16 ≤ the slicer width (the linter's truncation rule: a
longer header is cut with an ellipsis and fails). The full rule ("none selected = Jan..last closed
month; several months = their sum") goes into a footnote, never into the header or a two-line
help text beside the slicer.

Fallback for the message when the SVG route is not wanted: a `cardVisual` on the plain-text
message measure with `value.bold` true and 13 pt (pbir-skeleton.md §6): bold, numbers black.

## 4. KPI row

One visual per KPI, so the canvas shows between the cards (one `tableEx` holding all cards would
be one white strip, and with column width < `imageWidth` + 20 it draws a stray "." per card):

- `tableEx` (x, 247, 236, 131), one image column bound to the card's SVG measure
  (ibcs-svg-dax skeleton 4), `displayName: " "`, column header 8 pt (its empty header strip,
  about 17 px, is the top padding); no rules (§3).
- Visual padding left 14, right 0, top 0, bottom 0 (236 ≥ 14 + column 220 + 2); column width 220;
  `grid.imageWidth` 200, `imageHeight` 104 (17 + 104 + 10 = 131).
- The card SVG at **200 × 104**: in skeleton 4 set `width='200'` and `viewBox='0 0 200 104'` and
  move the x positions: centre 120 → 100, Δ% end 100 → 84, Δ end 176 → 147, scenario code 184 → 154.
  Text sizes stay 12 / 28 px (never scale the SVG to fit: the labels would shrink below 12 px).
- Inside a card: label (measure name, semibold) and unit, the big AC value, then one line per
  comparison: Δ% and Δ in the text impact colours, the scenario code (ΔPY, ΔBU) in black. No
  separators, icons or backgrounds; a value the message names gets the highlight ellipse.

## 5. Chart cards

- **Title inside the card:** two visuals: a text box (16, y, card width, 40) with padding top 16,
  the measure in bold and the dimension ("**Revenue** by month"), 11 pt; below it (y + 40, height
  24) the scenarios, period and variances, 9 pt grey. One box for both lines scrolls in the
  service. No visual titles on the charts below it.
- **Card height from content:** the card ends at its last visual's content + the bottom padding
  16; nothing else. More than 24 px of empty space at a card's bottom is a hole (the linter fails
  a card background that ends more than 24 px below its last visual). Exception: equal heights
  in one row (§2).
- **Charts** directly below (y + 64), sized by `scale_layout.py` (SKILL.md §3) plus their padding.
  The first chart of a row gets padding left 16, the last padding right 16; charts between them
  0. The bottom visual of the card gets padding bottom 16 (its position height = computed + 16).
- A Total / year column of a monthly chart is its own visual in the **same** card, right of the
  months, without a gap. It has its own scale, and so do its Δ tiers: base and Δ tier of the
  Total use the **Total's** px per unit (ibcs-composition: one scale per column block), shown by a
  scale band in both visuals (Deneb `scaleBand`) and a footnote ("the Total has its own scale").
  A Δ that is tiny on that scale (1–2 px) is still drawn at its true height with its label; never
  inflate it to be visible (the label carries the value).
- **Tier proportions (one rule for Power BI and web apps).** Absolute Δ tiers always use the
  base tier's px per unit. Relative-variance pins use the page's `"%"` scale group at **1 px per
  percentage point** by default (Deneb knob `pinPxPerUnit`, default 1), lowered only when the cell
  cannot hold the pin range at that scale; the pin range is the clipped range (outliers beyond
  ±100 % are clipped with an outlier triangle at the clip point, the label keeps the full value). A
  pin that does not round to zero is drawn at least head/2 + 2 px long so its colour shows. Size
  the base tier so its largest column is about **1.5 × the category pitch** high when the cell
  allows (`scale_layout.py` `maxExtentPx`); the web reference components use the same rules
  (ibcs-web-charts `react-reference`).
- **Data-bound ranges under a selection.** Give `scale_layout.py` the largest tier range any single
  selection produces (the largest company's months, not only the group's) and, where a selection
  may exceed it, a per-tier `reservePx`; the container then never clips a selection.
- **Alignment with the months.** The Total's baseline and tiers sit at the same y as the months':
  - same visual top and same height for months and Total;
  - the category-label band has an explicit height in both (Deneb knob `categoryLabelPx`: months
    with a year line need 28 px at 12 px type, a single "Total" label 14 px, so give both 28; the
    fixed height is then 38 px in both), and `scale_layout.py` uses it in the fixed height;
  - each tier's **height** is the union of the months' and the Total's px extents for that tier,
    each at its own px per unit: list both in `"alignTiers": [["months", "total"]]` of the
    `scale_layout.py` group; it prints the same height for both and the tier ranges per visual
    (`setParams`: `yMax`, `varMin`/`varMax`, `pinMin`/`pinMax`). Under filters bind the fields
    `YMax`, `VarMin`/`VarMax`, `PinMin`/`PinMax` to union measures computed the same way
    (column-two-tier-variance notes give the DAX); they win over the knobs, like `PxPerUnit`, so a
    filter that grows the months' tiers grows the Total's too. Fixed knobs suit an unfiltered page
    only.
- **End names at a very short Total column.** When the Total's column is shorter than the stacked
  end names need (names font + 2 px apart), the names sit above the column top, still in mark
  order, never on the scale band or its line (column-two-tier-variance does this by itself).
- **Waterfalls** have a fixed bottom band (category axis and its labels, about 27 px) that is part
  of the template's layout metadata, so `scale_layout.py` includes it; do not add it again.
- Value labels need room at the right end of bars (and left of negative ones): give
  `scale_layout.py` the longest formatted label (`longestValueLabel`); it names the knob to raise.
- Two-column blocks (e.g. bars by company left, Δ and Δ% right) stay in one card: one Deneb
  visual with all tiers, or visuals edge to edge on one baseline.

## 6. Footnote card

- One text box, full width (16, y, 1248, h), padding 16 top and left/right, 8 pt (≈ 11 px; it renders
  at about 17 px per line), grey `color.text.secondary`. Height = 32 + lines × 17, where lines = Σ over notes of
  ceil(characters × 5.5 / 1216): sized to its text, **never a scroll box** (a scrolled note is not
  printed and not read).
- Last line: source and data as of (`YYYY-MM-DD hh:mm`), so the card is also the page footer. As a
  separate text card below the notes (height 38, padding bottom 16) it closes the card; use the
  same 8 pt as the notes.
- Short: one line per note where possible, at most about eight notes. Longer definitions (KPI
  formulas, company names, model compromises) go to a glossary / details page linked from the
  card ("Definitions: page Notes") or into the tooltip of the visual they explain.
- The page footnotes follow the numbered references in the title, chips and charts (¹ ² …).

## 7. Checks

`python3 -I <ibcs-review skill dir>/scripts/ibcs_lint.py pbir <name>.Report --layout layout.json` (load the `ibcs-review` skill of plugin `ibcs` with the Skill tool; it prints its base directory) checks the shell mechanics:
neutral canvas, content on a white card shape or with a white background (A2), no border or
shadow on content visuals while card shapes may have them (A4), content visuals at a z below the card shape
behind them (hidden by the card; LINT), slicer labels at least 12 px below
the title text box above them, card backgrounds that end more than 24 px below their last visual,
slicer headers and titles that would be cut, image columns at least `imageWidth` + 20 (LINT),
Deneb sizes and px per unit against `scale_layout.py --json` (G8). What it cannot see: the rendered result. Export the page to PDF
(pbir-skeleton.md §10) and compare it with the spec and this grid.
