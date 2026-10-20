# Report shell: the frame around every page *(ours)*

The IBCS rules fix what happens **inside** a chart or table. This reference fixes the frame around
it, so that a builder who uses only these skills gets a finished page: header row, filter bar,
page head, KPI cards, chart cards and footer. It extends [app-patterns.md](app-patterns.md) (grid,
selectors, URL contract), [chart-layer.md](chart-layer.md) (the charts) and
[page-quality.md](page-quality.md) (the rubric; the shell checks are its §4). Everything here is
*ours* unless a rule code is given.

**Cards are UI chrome, notation stays IBCS.** The shell may put each visual on a white card on a
lightly tinted canvas, with a small radius and a 1 px elevation. That is chrome, like the selectors:
inside a card the chart keeps its IBCS notation (no colour fills, no gradients, no shadows on
marks), and the shell never adds a status colour or a frame around a single number. Print and PDF
drop the canvas tint (white page, cards as plain blocks).

## Contents
- [1. Anatomy at 1280 px](#1-anatomy-at-1280-px)
- [2. Required and optional elements](#2-required-and-optional-elements)
- [3. State: what lives where](#3-state-what-lives-where)
- [4. Header row and filter bar](#4-header-row-and-filter-bar)
- [5. Page head](#5-page-head)
- [6. KPI cards](#6-kpi-cards)
- [7. Chart cards](#7-chart-cards)
- [8. Footer](#8-footer)
- [9. Layout tokens](#9-layout-tokens)
- [10. Breakpoints](#10-breakpoints)
- [11. Recipe: the Key figures page from scratch](#11-recipe-the-key-figures-page-from-scratch)

## 1. Anatomy at 1280 px

```
┌ header row (sticky) ──────────────────────────────────────────────────────────────────────┐
│ [logo] │ Sales  [Key figures] Budget  Margin  Customers …   [IBCS|Showcase] (i) [Compact▾] [Theme▾] │
├ filter bar ───────────────────────────────────────────────────────────────────────────────┤
│ COMPANY [All companies▾]  PERIOD [Jan..Sep 2026 · YTD (last closed)▾]  COMPARE WITH [Budget and PY▾]   [Reset filters] │
└───────────────────────────────────────────────────────────────────────────────────────────┘
  Revenue Jan..Sep 2026 is 152.3 mEUR, +8.3 mEUR (+5.8%) vs PY and in line with BU …   ← headline
  ───────────────────────────────────────────────────────────────────────────── 1.5 px rule
  Group, sum of six companies (not consolidated)                      ← title line 1 (muted)
  Sales key figures in mEUR, % and ratio                              ← line 2, measure bold
  Jan..Sep 2026 PY and BU and AC, ΔPY and ΔBU                         ← line 3
  (Intercompany sales included ①) (Budget and forecast for revenue only ④)  ← scope chips

  ┌ KPI ──────────┐ ┌ KPI ────┐ ┌ KPI ────┐ ┌ KPI ────┐ ┌ KPI ────┐      ← one row, equal widths
  │ Revenue   (i) │ │ …       │ │ …       │ │ …       │ │ …       │
  │ in mEUR       │ └─────────┘ └─────────┘ └─────────┘ └─────────┘
  │ 152.3         │
  │ +5.8% (+8.3) ΔPY │                                                 ← ring = cited in headline
  └───────────────┘
  ┌ chart card: Revenue by month, <who> ────────────────────────────┬ Total ┐
  │ ΔBU% pins                                                         │ pin   │
  │ ΔBU bars                                                          │ bar   │
  │ AC&FC columns, BU outline, PY triangles  [selected-month band]  PY│ col   │
  │ Jan … Sep │ Oct … Dec (hatched)                          BU AC&FC │ Total │
  └───────────────────────────────────────────────────────────────────┴───────┘
  ┌ chart card: Revenue by company ──────────────────────────────────────────┐
  │ bars AC, BU outline, PY triangle    │ ΔBU │ ΔBU%   (ring on the cited row) │
  │ E1 Company name · E2 Company name · …   (name legend under the chart)       │
  └────────────────────────────────────────────────────────────────────────────┘
  ┌ footer (full width): ① … ⑧ numbered footnotes · Source … · Data as of … ───┐
```

## 2. Required and optional elements

| Element | Status | Notes |
|---|---|---|
| Header row: logo slot, report-area name, page tabs | required | Logo as a local asset (no CDN), a light and a dark lockup if a theme switch exists. Area name after a thin divider. Tabs = the report outline (ST 5.1), hash routes |
| Notation toggle (IBCS / Showcase) | optional | Only if the app has a second presentation on the same adapters. Default IBCS; the URL carries it (§3) |
| Card style (Charts / Compact) | optional | Shown only while the page has cards that change with it |
| Theme select | optional | Light by default; a dark theme only around a white paper surface (SKILL.md §0) |
| How to read (i) | recommended | Popover: scenario notation, variance colours, what chips mean, interactions, the report's purpose and audience |
| Filter bar: entity, period, compare with, Reset | required | Every active value surfaces in title lines 1 and 3 ([app-patterns.md](app-patterns.md) §3) |
| Headline (key message) and rule | required on message pages | Detection template only ([app-patterns.md](app-patterns.md) §4) |
| Title lines 1–3 | required | UN 2.2 |
| Scope chips with footnote numbers | required when the page has caveats | Each chip links to its footnote |
| KPI cards | required on a Key figures page | §6 |
| Chart cards | required | §7 |
| Footer: numbered footnotes, source, data as of, last closed month | required | UN 2.5, SA 4.4 |
| Diagnostics link | recommended | Shows raw column types and first rows (`debug=1` in the hash) |
| Refresh | recommended | Bypasses the query cache; the footer shows the new as-of date |

## 3. State: what lives where

| State | Where | Why |
|---|---|---|
| Page (route) | hash path `#/key-figures` | Back, reload and bookmarks inside the portal frame |
| Entity, period, comparison, page extras | hash query `?co=E1&p=ytd&cmp=bu` | They change what the page shows: the view must be reproducible from the link |
| Notation variant (IBCS / Showcase) | hash query `variant=showcase` | Changes what is shown |
| Theme, card style, density | `localStorage` per app (`<app>.theme`, …), read in `try/catch` | Viewer preference, not part of the view: a shared link opens in the receiver's own preference |

- Parse the hash once per change into one typed state object; unknown or malformed values fall
  back to the defaults (never an error page). Write the hash only when it changes (no loop with
  `hashchange`).
- **Reset filters** sets entity, period and comparison back to the defaults; it keeps the route,
  the variant and the viewer preferences.
- Changing the page keeps entity, period and comparison (tab links carry them).

## 4. Header row and filter bar

- **Tabs**: one row at 1280 px and at the portal's ≈ 1050 px content width. Measure tabs + tools;
  when they do not fit, first hide the text of icon buttons, then narrow the selects, then reduce
  the tab padding. The active tab is an inverted chip (ink background, light text) at the **same
  font weight** as the others, so selecting a tab never widens the row.
- **Company**: "All companies" first, then one option per entity the user may see (code and name;
  RLS decides). The selected entity replaces the group label in title line 1 ("E1 Company name").
- **Period**: one control. The button shows the span in time-span notation and its kind
  ("Jan..Sep 2026 · YTD (last closed)"); the popover offers the dynamic periods (YTD, last closed
  month, rolling 12) and a from..to month range (period grammar in
  [app-patterns.md](app-patterns.md) §3). Open months are disabled in the range picker or marked FC.
- **Compare with** switches the notation of the reference tiers, not only the numbers:

  | Option | Charts | KPI Δ lines | Title line 3 | Headline |
  |---|---|---|---|---|
  | Budget and PY (default where a budget exists) | BU outline behind AC, PY triangles; ΔBU and ΔBU% tiers | ΔPY and ΔBU | `PY and BU and AC, ΔPY and ΔBU` | PY clause and BU clause |
  | PY only | PY light column behind AC; ΔPY tiers | ΔPY | `PY and AC, ΔPY` | PY clause |
  | Budget only | BU outline; ΔBU tiers | ΔBU | `BU and AC, ΔBU` | BU clause |
  | FC (if the model has forecast versions) | FC as reference: AC only as primary, ΔFC on a hatched axis | ΔFC | `FC and AC, ΔFC` | FC clause |

  Offer only what the model supports; a measure without a budget falls back to PY and a chip says so.
- Field labels small and uppercase above their control; each control as wide as its longest
  option, never cut. **Reset filters** at the right end of the bar.

## 5. Page head

- **Headline**: one sentence, bold (weight ≈ 650), numbers a step bolder and tabular. Impact
  colour only on the variance numbers the sentence states (text tokens `goodText`/`badText`,
  never the graphic green), the measure value in ink. A 1.5 px rule in ink under it.
- **Materiality**: a comparison below the page's threshold reads "in line with BU (+0.5 mEUR,
  +0.3%)" instead of "+0.5 mEUR vs BU". The threshold comes from the visual spec (e.g. |Δ%| <
  0.5 %); until the owner confirms it, the footer says it is proposed.
- At most two findings: the headline measure and the single largest material mover ("E2 has the
  largest gap to BU (−3.4 mEUR)"). The mover is ringed where it appears (§6, §7).
- Title lines: line 1 muted (who, with every active filter), line 2 measure bold and unit, line 3
  period and scenarios. Dates and spans never break inside.
- **Chips**: rounded, muted background, small text; each ends in a circled footnote number that
  links to `#note-n` in the footer (the targeted note is emphasised). Numbers match both ways
  ([page-quality.md](page-quality.md) §2).

## 6. KPI cards

Numbers and notation follow the KPI card contract of the `ibcs-web-charts` skill (plugin `ibcs`,
behaviour contract §10). The shell adds:

- One row of equal cards (`repeat(auto-fit, minmax(168px, 1fr))`), each on a card surface.
- Centred inside: **name** (semi-bold) with an **(i)** button at the top right; the **unit line**
  ("in mEUR", "in %", "ratio", "in mEUR, month end"); the **value** large (≈ 24 px, weight 650,
  tabular); then one Δ line per comparison, relative before absolute, then the code
  (`+5.8%  +8.3 ΔPY`).
- **(i)** opens a popover with the measure's definition and a link to its footnote. Definitions
  live in one glossary object, the same text as the footnote.
- **Highlight ring** (the highlight marker token, UN 5.1) around the Δ number the headline cites,
  only when that comparison is material; at most two rings per page.
- Optional card style "Charts": a small chart of the monthly values under the Δ lines; each card
  on its own scale with a scale band at one round value across the row (behaviour contract §10).
- An impact glyph beside a Δ number is optional and only redundant with its sign and colour;
  strict IBCS pages leave it out.

## 7. Chart cards

- Card head inside the card: title "**Revenue** by month, <who>" (measure bold), subtitle = the
  chart's own title line 3 ("2026-01..2026-09 AC, 2026-10..2026-12 FC, BU and PY, ΔBU").
- **Month chart** (column chart with ΔBU% pins and ΔBU bars stacked above, [chart-layer.md](chart-layer.md)):
  columns fill 2/3 of their category, the reporting month (or the clicked month) gets an assisting
  area behind its full category band through all tiers, the AC → FC switch gets a tick, FC hatched.
- **Total column** in its own narrow cell at the right, after a thin vertical rule, on its own
  scale; a scale band at the same round value (e.g. 10 mEUR) in the months and in the Total shows
  the factor (CH 4.3, UN 5.2), and a footnote says so. Its variance tiers align with the months'.
- **Series labels** (PY, BU, AC&FC) at the **end** of the series: right of the last month, before
  the Total rule, stacked in the order of the marks they name (`ibcs-web-charts` behaviour
  contract §1, §2). Never a legend box, never at both ends.
- Optional **difference marker** (UN 5.1) right of the last month: a bracket from the first to the
  last month with Δ and Δ%; shift-click two months to choose them.
- **Company bars** (structure chart with ΔBU and ΔBU% tiers): sorted, the cited company ringed in
  its Δ tier, scenario names once at the top bar, the name legend ("E1 Company name · E2 …") as one
  muted line under the chart. Bars use the same px per mEUR as the month columns.
- Clicking a company sets the entity filter, clicking a month sets the reporting month; both
  through the URL, so Back undoes them.

## 8. Footer

- Full width under the grid: the numbered footnotes in chip order, then "Source: <model and
  tables>. Data as of <date>; last closed month <month>." and the diagnostics link. Every footnote
  shows its whole text: no scroll box, no ellipsis, no footnote column squeezed beside a chart.
- Long or many notes go into the How-to-read popover or a details page, with a one-line pointer.

## 9. Layout tokens

Define these once in the shell stylesheet as CSS custom properties **derived from the generated
IBCS token CSS** (colours from the tokens via `color-mix`, never hex here). Values that worked at
1280 px:

| Token | Value | Use |
|---|---|---|
| `--shell-canvas` | text-primary 5 % mixed into the page background | page background behind the cards |
| `--shell-surface` | page background | cards, header row, filter bar |
| `--shell-line` | the light table-rule colour | dividers, control borders |
| `--shell-radius`, `--shell-radius-sm` | 10 px, 8 px (controls 6 px) | cards, popovers |
| `--shell-elev-1` | `0 1px 2px` ink 7 % plus `0 0 0 1px` ink 4 % | cards |
| Header row | padding 10 × 28 px, logo 26 px high, area name 15 px semi-bold | sticky at the top |
| Tabs | padding 7 × 9 px, radius 6 px, gap 2 px | |
| Filter bar | padding 8–14 × 28 px, gaps 8–14 px, field labels 11 px uppercase | |
| Page | padding 22 × 28 px, max width 1400 px | |
| Headline | 18 px, weight 650, line height 1.35, 1.5 px ink rule, 8 px below | |
| Title lines | 12 px, line height 1.45 | |
| Chips | 11.5 px, padding 3 × 10 px, fully rounded | |
| Grid | 12 columns `minmax(0, 1fr)`, gap 16 px, each card as tall as its content | |
| Card | padding 18 × 20 × 20 px; title 13.5 px; subtitle 12 px muted | |
| KPI card | padding 14 × 16 px; value 24 px weight 650; Δ lines 12.5 px; row gap 12 px | |
| Footer | 11.5 px muted, 22 px above, a rule on top | |
| Base text | 13 px, token font stack | |

## 10. Breakpoints

| Width | What changes |
|---|---|
| ≥ 1280 px | Tabs and tools on one header line, all filters on one line, five KPI cards in one row, month chart and Total side by side |
| ≈ 1050 px (Fabric portal content width) | Compact tools: icon buttons without text, selects ≈ 112–136 px, tab padding 5 px; the tab row stays one line. Filters may wrap to a second row (never cut a control). KPI cards may wrap 3 + 2. Charts redraw for their width (label thinning by measured width, `ibcs-web-charts`) |
| ≤ 760 px (phone; test at 390) | Header in two rows: brand, then a page select with the tools (tools wrap, never cut). The filter bar collapses to one toggle with a summary of the active filters. Page padding 14 × 12 px, one grid column, 12 px gap, card padding 12 px, headline 15.5 px. KPI cards two per row, a lone last card spans the row. The Total moves under the months (same scale band); structure tiers stack under the bars (behaviour contract §4) |
| Print | Header row, filter bar, tools and the canvas tint hidden; title lines show the state; cards do not break across pages |

## 11. Recipe: the Key figures page from scratch

For any sales model with revenue (AC, BU, FC, PY), a margin, order intake and backlog. Adapt the
names to the model; the visual spec stays the source of truth.

**Files**

```
src/app/config.ts                   routes (name + purpose), footnote registry, glossary, group label,
                                    defaults (period ytd, compare "bu+py"), materiality threshold
src/app/url-state.ts                parse / format the hash (§3), reset, page change keeping filters
src/shell/HeaderRow.tsx             logo, area name, tabs, tools (§4)
src/shell/FilterBar.tsx             entity, period control, compare with, reset (§4)
src/shell/PageFrame.tsx             headline, title lines, chips, grid, footer (§5, §8)
src/shell/Card.tsx, KpiCard.tsx     card surfaces (§6, §7)
src/shell/shell.css                 §9 tokens and §10 breakpoints
src/queries/boot/reference.dax      data-as-of date and last closed month
src/queries/boot/months.dax         months with data and their closed flag
src/queries/boot/entities.dax       entities (code, name) the user may see
src/queries/key-figures/kpis.dax              one row per KPI for the period: AC, PY, BU, Δ, Δ%
src/queries/key-figures/revenue-by-month.dax  months of the year: AC, FC, BU, PY, ΔBU, ΔBU%, closed
src/queries/key-figures/revenue-total.dax     the year: AC&FC, BU, PY, ΔBU, ΔBU%
src/queries/key-figures/revenue-by-entity.dax entities in the period: AC, BU, PY, ΔBU, ΔBU%
src/queries/key-figures/kpi-months.dax        optional: monthly values per KPI for the card charts
src/pages/key-figures/{adapters.ts,KeyFiguresView.tsx,KeyFiguresPage.tsx}
```

**Steps**

1. Boot queries first; until they resolve the page shows its frame (headline placeholder, cards at
   their final height). Defaults come from them: period = YTD up to the last closed month.
2. Shell (header row, filter bar, page frame) with the URL state; unit-test parse and format
   (unknown values fall back, Reset keeps the route).
3. Write and test each `.dax` from the terminal ([queries-and-data.md](queries-and-data.md));
   variances from the model or query-scoped measures, never in TypeScript. The compare-with option
   decides which reference columns the queries return (or which the adapter picks).
4. Adapters turn rows into the chart roles of `ibcs-web-charts` (scenario columns, variance tiers,
   structure rows, KPI rows); the headline facts (largest material mover, materiality) come from
   the same rows.
5. One scale registry for the page: month columns, company bars and absolute Δ tiers share one px
   per mEUR; the Total has its own scale with a scale band; the Δ% pins share one % scale.
6. Page: headline, KPI row, month card with Total, company card, footer with the footnotes the
   chips cite.
7. States (SKILL.md §5) for every card; the headline hides when its query failed.
8. Check at 390, ≈ 1050 and 1280 px ([chart-layer.md](chart-layer.md) harness, then the portal):
   [page-quality.md](page-quality.md) including the shell checks, `ibcs-review` on the DOM, no
   clipped label anywhere.
