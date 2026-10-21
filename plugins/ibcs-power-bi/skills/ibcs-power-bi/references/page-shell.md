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
- [7. Phone (mobile layout)](#7-phone-mobile-layout)
- [8. Checks](#8-checks)

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
| header card (two-line message) | 16 | 16 | 1248 | 230 (one-line message: 208) |
| KPI cards (5) | 16, 268, 520, 772, 1024 | 262 | 236 (last 240) | 131 |
| first chart card | 16 | 409 | 1248 | title 40 + subtitle 24 + charts + 16 |
| next card | 16 | previous bottom + 16 | 1248 (or 616 + 16 + 616 for two side by side) | — |
| page height | — | — | — | last card bottom + 16 |

Four KPI cards: width (1248 − 3 × 16) / 4 = 300; three: 405 (last 406). Two chart cards side by
side: 616 each. With a one-line message every y below the header moves up by 22 (KPI row 240,
first chart card 387). In fluent-cards mode add one shape per card at exactly these rectangles.

Cards in one row have **equal heights**: the row height is its tallest card's content + padding,
and every card of the row gets that height (content top-aligned; the extra space sits at the
bottom of the shorter cards, the only allowed empty bottom).

## 3. Header card

All visuals white, stacked edge to edge with no canvas showing between them (spans touch: a visual
ends where the next begins), x = 16 unless stated:

**Vertical rhythm** (fixed, top to bottom): key message → 12 px → the three title lines at
consecutive line height (no blank line between them) → at least 12 px → the slicer labels. The
message visual ends where its text ends (no spare image height), and the 12 px gaps are the
**top padding** of the next visual, never canvas. Positions for a two-line message:

| Visual | Position (x, y, w, h) | Content |
|---|---|---|
| key message | 16, 16, 1076, 72 | `tableEx` with the SVG key message (ibcs-svg-dax skeleton 7): one image column, `displayName: " "`, column header font 8 pt. Its empty header strip renders **about 17 px** high (measured in the service, 2026-10) and is the card's top padding. Column width 1030, SVG and `grid.imageWidth` 1010, `imageHeight` = lines × 22 + 4 (two lines of 17 px bold at 22 px line height: 48; one line: 26). Height = 17 + `imageHeight` + 7 (72; one line 50): at 17 + `imageHeight` exactly (65) the table scrolls in the service (proof run, 2026-10), the 7 px reserve stops it |
| logo (optional) | 1092, 16, 172, 72 | `image` visual on a registered resource (recipe: pbir-skeleton.md §4, Logo image), the organisation's logo at most 148 × 40, right-aligned, padding 16; the linter lists it (A1) for review: one logo in the header card's corner, nowhere else |
| title lines | 16, 88, 1248, 78 | three `cardVisual` text measures edge to edge (dynamic lines: who with the active filters / **what** in unit / when), or, for static titles, one text box with the three lines. **One visual type for all three lines, never mixed**: a `cardVisual` sets its text at the bottom of its box and a text box at the top, so mixed lines sit unevenly and an overlap hides text (proof run, 2026-10). Each box is exactly its line: 10–11 pt, **22 px per line** (at 19–21 px a card clips descenders); line 1 has **padding top 12** (the rhythm gap): line 1 at 16, 88, 1248, 34 (12 + 22), line 2 at 16, 122, 1248, 22, line 3 at 16, 144, 1248, 22; left/right padding 16, top/bottom 0 on lines 2 and 3; with the text at the bottom of each box every line lands on the 22 px grid: 12 + 3 × 22 = 78. The linter fails mixed types |
| slicers | 16, 166, 212, 80 / 228, 166, 272, 80 | dropdown slicers with **padding top 12** (the gap below title line 3) and bottom 16 (the card's bottom padding): 12 + 52 + 16 = 80; spans 16–228 and 228–500 |
| scope chips | 500, 166, 764, 38 (+ a second line 500, 204, 764, 38) | text from the **slicer label top** (padding top 12): what the selection means ("all companies, intercompany included ¹", "none = Jan..last closed month ²"), 9 pt grey, footnote numbers; span 500–1264 |

The card ends at y 246 (166 + 80); with a one-line message 22 px higher (message 50, titles at 66,
slicers at 144, card end 224). Never leave a gap between two visuals of one card: the grey canvas
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

- `tableEx` (x, 262, 236, 131), one image column bound to the card's SVG measure
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
  Show that own scale in the Total's variance tiers too: the same scale band value drawn in its
  base tier, and a footnote marker on its Δ tier name ("ΔPY¹"), because its Δ bars are on the
  Total's scale, not the months'.
  A Δ that is tiny on that scale (1–2 px) is still drawn at its true height with its label; never
  inflate it to be visible (the label carries the value).
- **Tier proportions (one rule for Power BI and web apps).** Absolute Δ tiers always use the
  base tier's px per unit. Relative-variance pins have **their own % scale per chart, sized to the
  tier**, so the pin length carries the relative variance (proof run 2026-10: pins at a fixed
  1 px per point were 1–3 px stubs on the axis): the tier extent is `pinTierPx` (ours: 48 px for
  column tiers, 90 px for horizontal pin columns) and the clipped pin range fills about 90 % of it
  (Deneb `pinPxPerUnit` 0 = this rule; `scale_layout.py` prints the value per member). No page-wide
  % group: one −55 % structure variance would shrink the month pins to a few px. Only charts read
  together share a pin scale: months and their Total (`alignTiers`). **Differing % scales are
  marked (OURS):** every pin tier whose px per point differs from the page's other pin tiers
  carries a scaling marker in the scale-band style (UN 5.2, CH 4.3): Deneb knob `pinScaleBand`
  (−1 = a round value 1/2/5 × 10ⁿ % that is 25–60 % of the tier, chosen by the template; a
  fraction such as 0.1 = that value; 0 = off), a band at the tier's start with its value label,
  the same value for charts read together; `scale_layout.py` sets `pinScaleBand` -1 in
  `setParams` whenever the page's pin scales differ (list every pin chart of the page in one
  group file), and the page footnote says the % tiers are on different scales. Why: one −55 %
  structure variance on a page-wide % scale squashes every other pin below readability. The
  linter fails an unmarked differing % scale (F6 with `--layout`). The pin range is the clipped
  range (outliers beyond ±100 %, or beyond 3 × the next-largest |Δ%| of the tier, are clipped with an outlier
  triangle at the clip point, the label keeps the full value; OURS: one immaterial reference, AC 0 against a
  budget that rounds to 0 = −100 %, must not flatten every other pin; give scale_layout.py the chart's
  `pinValues` and it applies the rule and fails a tier with mostly < 4 px stems, linter E12). The head is 6 px (token minimum) at the stem end; a pin that does not
  round to zero is at least head + 2 px long; a Δ% that rounds to zero keeps its head on the axis
  as a baseline marker (no stem, no colour); pin labels have one decimal (`+5.8%`). Check: a
  chart's largest |Δ%| has a stem of at least 40 % of its tier (`scale_layout.py` warns). Size the
  base tier so its largest column is about **1.5 × the category pitch** high when the cell allows
  (`scale_layout.py` `maxExtentPx`); the web reference components use the same rules
  (ibcs-web-charts `react-reference`).
- **No label on a line.** A value label never crosses an axis, a baseline, an assisting line, a
  scale-band line or a magnifier frame or connector: a drop's label that would reach a line goes
  to the far side of its bar start (or right of the bar), the AC→FC separator is a short tick on
  the category axis, the base-level line of a bridge runs only from below the total bar to the
  arrow, and a waterfall's scale-band line is a cap above the first row. The Deneb preview
  renderer fails (WARN) on any label box that crosses a solid rule; check new templates with it.
- **Period labels never get an ellipsis** ("J… F…" is ambiguous): a period label wider than its
  step becomes its first letter (Jan → J, the year stays in the title), then the labels stagger
  in two rows; quarters skip the letter step (Q1 is already short). Dimension names use the free
  label room first, then wrap to two lines, and are cut only as a last resort.
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
  When the magnifying glass is active (largest step < 5 % of the base, OURS), give the member
  `"magnify": true`: `waterfall-variance` grows by `magnifyPx` + 24 px in width (the panel beside),
  `waterfall-variance-time` by `magnifyPx` + 66 px in height (the tier below). A bridge on the page
  scale whose steps would be 1–9 px is exactly this case: magnify it, never give it its own scale.
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

## 7. Phone (mobile layout)

**Power BI phone layout: not supported in 1.0.0.** A headless builder cannot author or capture a Power BI mobile layout (it needs the mobile layout view in Desktop or the service and a capture through the mobile app or a MobilePortrait embed), so no 390 px view is required of a Power BI report, and a review does not fail one for lacking it. The guidance below is unverified and for authors who build the layout by hand; a tested `mobile.json` recipe is planned for 1.1. Phone-first pages: build them as a Fabric App (plugin `fabric-apps`).

The desktop page shrunk to a phone screen is about 30 % of its size and unreadable (proof run
2026-10). A Power BI page gets a phone view only through its **mobile layout**, which the Power BI
mobile apps show in portrait orientation; a web browser always shows the desktop layout (Learn:
[Create mobile-optimized reports](https://learn.microsoft.com/power-bi/create-reports/power-bi-create-mobile-optimized-report-about)).

- Author it in the **mobile layout view** (Desktop: View → Mobile layout, or the layout switcher;
  the service: Edit → Mobile layout) by dragging the page's visuals onto the phone canvas. PBIR
  stores it per visual in `visuals/<name>/mobile.json` (schema `visualContainerMobileState`, Learn:
  [report folder](https://learn.microsoft.com/power-bi/developer/projects/projects-report#pbir-format));
  let Desktop or Microsoft's `powerbi-authoring` skills write those files.
- What to place, top to bottom (the same order as a web app at 390 px, report-shell.md of
  ibcs-fabric-app): the header text box (message and title lines, the message at 11–12 pt), the
  KPI cards two per row, the month chart at the phone width (the same Deneb visual: it fills its
  container and redraws for it, period labels shorten Jan → J, value labels thin but keep first,
  last, the extremes and the last AC), the Total under the months (same scale band), the
  structure chart, the footnote card. A mobile layout can only place the page's own visuals:
  a chart that does not work at 360 px (a structure chart with three tiers side by side) needs
  a phone variant on the desktop page (e.g. the tiers stacked) or stays off the phone view, with
  a note. Slicers go in one row at the top. Fonts never below 9 pt.
- **Capture it at 390 px for real**, not as a resampled PDF: a screenshot from the Power BI mobile
  app on a phone (or a simulator), or the report embedded with `layoutType: MobilePortrait`
  (powerbi-client, Learn: [Embed with mobile layout](https://learn.microsoft.com/javascript/api/overview/powerbi/mobile))
  in a browser emulating a 390 × 844 device (CDP `Emulation.setDeviceMetricsOverride`). The
  export API renders the desktop layout only.

## 8. Checks

`python3 -I <ibcs-review skill dir>/scripts/ibcs_lint.py pbir <name>.Report --layout layout.json` (load the `ibcs-review` skill of plugin `ibcs` with the Skill tool; it prints its base directory) checks the shell mechanics:
neutral canvas, content on a white card shape or with a white background (A2), no border or
shadow on content visuals while card shapes may have them (A4), content visuals at a z below the card shape
behind them (hidden by the card; LINT), slicer labels at least 12 px below
the title text box above them, card backgrounds that end more than 24 px below their last visual,
slicer headers and titles that would be cut, image columns at least `imageWidth` + 20 (LINT),
Deneb sizes and px per unit against `scale_layout.py --json` (G8). What it cannot see: the rendered result. Export the page to PDF
(pbir-skeleton.md §10) and compare it with the spec and this grid.
