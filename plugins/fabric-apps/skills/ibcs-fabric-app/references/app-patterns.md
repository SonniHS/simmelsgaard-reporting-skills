# Page archetypes, selectors and state

Builds on the page patterns and visual spec format of the `ibcs-composition` skill (plugin `ibcs`).
Rules cited as IBCS v2.0 codes; *(ours)* marks our defaults, which you may change.

## Contents
- [1. App structure](#1-app-structure)
- [2. Page grid (1280 × 720 reference canvas)](#2-page-grid-1280--720-reference-canvas)
- [3. Selectors and how they surface](#3-selectors-and-how-they-surface)
- [4. Key message sources](#4-key-message-sources)
- [5. Chart roles per region](#5-chart-roles-per-region)
- [6. Hub page and links *(ours)*](#6-hub-page-and-links-ours)
- [7. Interaction checklist](#7-interaction-checklist)

## 1. App structure

```
Overview (message page)      → Driver pages (one argument each)   → Detail (lookup)
key message + 2–3 visuals       small multiples / waterfalls          variance table, grid
"EBIT FC −7.0 mEUR vs PL,       "Segment B volume −4.8 mEUR"          rows = entities/accounts
 mainly volume in segment B"
```

- The entry page is always a **message page** (SA 3.1); drill pages answer "why?" for one node of
  the storyline (ST 4); detail pages are `analysis` pages (no forced message, same notation).
- Navigation names are grammatically parallel and MECE (ST 1.3, ST 2, ST 3): "Sales", "Margin", "Costs",
  not "Overview", "Deep dive", "Misc". Tabs or left navigation = the report's outline (ST 5.1).
- Every page is complete without a click: tooltips and drill only add depth.
- One app = one notation; several apps in one org app share header, footer and selectors.

## 2. Page grid (1280 × 720 reference canvas)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ key message (one sentence, numbers + comparison)        [selectors: period  │
│ Reporting unit, filters               (title line 1)      comparison  ▾]   │
│ Measure in unit, by …                 (title line 2)                        │
│ period scenarios variances            (title line 3)                        │
├──────────────────────────────────────┬───────────────────────────────────────┤
│ multi-tier time chart (CO 4.2)       │ structure bars + ΔPL + ΔPL%           │
│  ΔPL% pins / ΔPL bars / AC&FC+PL+PY  │ sorted, remainder last                │
├──────────────────────────────────────┴───────────────────────────────────────┤
│ variance table or small multiples (optional)                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ Sources: … · Data as of <timestamp> · ¹ footnotes                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

Layout values come from the token file's `layout` group (margin, gutter, header band, footer). The
key message position (above or beside the title) is fixed for the whole app (UN 2.1). CSS: a
12-column grid with `minmax(0,1fr)`; charts measure their cell. Phone (390 px): one column in spec
order, the title may collapse to one line, selectors move into a sheet, at most about 12 periods
(or switch to quarters), small multiples reflow by column count, never by rescaling.

## 3. Selectors and how they surface

| Selector | Values | Default | Query effect | Title |
|---|---|---|---|---|
| Reporting period | closed months, ranges | last closed month | month list or `TREATAS` on the date table | line 3 |
| Period view | month, YTD, FY, rolling 12 | month or YTD | time-intelligence item in the model | line 3 |
| Comparison | PL, PY, FC (and budget) | PL | which Δ items and reference column | line 3: `AC and PL, ΔPL, ΔPL%` |
| AC&FC | on for FY views | on | AC+FC item + closed-period flag | line 3 |
| Entity filters | members | all | push to DAX if high cardinality, else widen grain | line 1 |
| Currency / unit | model currencies | model default | model currency switch | line 2 unit |

- The selection lives in the URL. Deep links, back button, bookmarks and print all reproduce the
  view. Validate values against the dimension list; fall back to defaults for unknown values (no
  error page).
- Changing the comparison switches **notation**, not just data: reference outlined (PL) vs light
  (PY), variance axis per reference, labels `ΔPL` vs `ΔPY`.
- No "chart type" switch; the spec fixes the chart per question.
- Selecting a structure bar may cross-filter the other visuals (filter, never highlight-dimming,
  which collides with scenario fills: a dimmed AC reads like PY). Fills keep full opacity; mark
  the selected category with an assisting area (token `color.marker.assistingArea`) behind its
  category band, or the highlight ellipse for a single point. Show the selection in title line 1.

### Period grammar *(ours)*

One URL key for the period keeps links short and stable:

- **Explicit** periods never move: `2026`, `2024..2026`, `2026-Q2`, `2026-09`, `2025-04..2026-09`.
- **Dynamic** periods follow the last closed month: `lcm`, `qtd`, `ytd`, `fy`, `lfy` (last full year).
- **Relative**: `rN` = last N closed months, optionally ending at a fixed month (`r12:2026-06`).
- AC covers closed months only; later months are open (FC where the app has a forecast). Invalid
  values fall back to the app default.
- An explicit period that is not closed yet keeps its URL value (the bookmark works once the month
  closes); the page shows the fallback and says so ("Nov 2026 is not closed yet: showing Jan..Sep 2026").
- Labels use the IBCS time-span notation with `..` (`Jan..Sep 2026`, `Apr 2025..Sep 2026`). Writing
  spans out instead of prefix notation for to-date or moving totals is a readability choice *(ours)*.
- PY = the same months a year earlier. If part of the period has no PY data, ΔPY and ΔPY% of the
  **period totals** are N/A (never "compare only the months with PY"); monthly values keep their PY
  where it exists, and a note says why.
- Flows sum the period; states (balances, headcount) take the value at the period's end month.

## 4. Key message sources

| Source | When | Implementation |
|---|---|---|
| `template` (detection only) | KPI pages refreshed monthly | a string template filled from measures, e.g. `"{measure} {when} is {AC} {unit}, {ΔPL} ({ΔPL%}) vs plan."`; re-scoped with filters; hidden if any bound value is BLANK |
| `commentary` (explanation, suggestion) | management packs | governed text keyed by (page, period, entity) in a Fabric App data entity or written via a translytical task flow; shows author and timestamp; hidden when filters leave its scope |
| `static` | one-off decision documents | literal text in the spec |

Never generate an explanation sentence automatically from numbers. A detected message cites at most
two findings (e.g. the headline measure and the single largest material mover).

## 5. Chart roles per region

Role names follow the `ibcs-web-charts` contract; use whatever components implement it.

| Region | Role |
|---|---|
| Header | title block (message, who, measure, unit, what, when); compact on phones |
| Multi-tier time chart | relative variance tier (%) + absolute variance tier + scenario columns, same width, one scale registry |
| Structure with variances | sorted structure bars with variance tiers |
| Bridge | variance waterfall (structure: bars; periods: columns) |
| P&L | calculation waterfall or variance table, not the same numbers twice (CO 5.3) |
| Many entities | small multiples (about 25 + Others), one shared scale |
| Footer | footnote with sources, as-of timestamp, definitions |

## 6. Hub page and links *(ours)*

A landing page that links to several reporting apps works best as a message page too: a detected
key message, then one tile per app with the question it answers, two or three headline KPIs with
their variances, and links to its pages. Tiles in a row share the same internal rows (CSS subgrid),
so values, charts and links line up. Links carry the selection (period, entity).

A Fabric App runs in a portal iframe and the portal owns the address bar, so a portal link does not
carry the page or the selection. As of 2026-10 the SDK's deep-link support was not generally
available. The app's direct (static-hosting) URL keeps route and query, but with the scaffold's
Fabric data client it loads no data outside the portal frame (deployed test, 2026-10; see
`queries-and-data.md` §0): link to the app item in the portal, and use direct-URL deep links only
with a data path verified to work there (the Rayfin connector is the candidate; test sign-in and data on it first).

**Routing inside the app: hash routes.** Inside the portal frame the app still owns its own
`location.hash`, and hash changes need no server rewrite on static hosting. Route between pages
with `#/time`, `#/structure` and put the selection in the hash's query string
(`#/time?entity=E1&from=2026-01&to=2026-09`), so back/forward and reload inside the frame keep
page and selection. Path routes (`/time`) break on reload when the host has no fallback rewrite.
Keep the nav a plain list of links in the title block area; the selection survives page changes.

## 7. Interaction checklist

- [ ] Default state is a complete message page; no click needed to understand it.
- [ ] All active filters visible in title line 1; period and scenarios in line 3.
- [ ] Selection, drill and back preserve the URL state (hash route + query string inside the portal).
- [ ] Keyboard: selectors, tabs and interactive marks reachable; focus visible.
- [ ] Print/PDF: controls hidden, title shows the state, footnote present.
- [ ] No animation, no auto-rotating carousels, no tooltip as the only source of a number.
