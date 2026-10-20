# Page patterns, grids and interactive behaviour

> Built on IBCS Standards v2.0 — CONDENSE (CO), SAY (SA), UNIFY (UN 2); our restatement under
> CC BY-SA 4.0 (see the repository NOTICE). IBCS sets **no** pixel values: all numbers here are
> *(ours)* and come from the bundled tokens (`layout.*`, `typography.size.*` in the
> [ibcs-notation](../../ibcs-notation/SKILL.md) skill). Standardise them per page type in the
> organisation's notation manual — IBCS asks for corporate page sizes and template grids (p. v).

## Contents
1. Page anatomy and grid
2. Page archetypes
3. Choosing between archetypes
4. Interactive dashboards and apps
5. Responsive and print

## 1. Page anatomy and grid

```
┌ margin 16 ───────────────────────────────────────────────────────────────┐
│ Title line 1 (who)               │ Key message — complete sentence,      │ header band ≈64 px
│ **Measure** in unit (what)       │ ≤ 2 lines, same slot on every page    │
│ Period, scenarios (when)         │                                       │
├──────────────────────────────────────────────────────────────────────────┤ thin rule
│ subtitle v1            │ subtitle v2                                     │
│ visual v1              │ visual v2                  ① annotation area    │ 12-col grid,
│                        │                                                 │ gutter 12 px
├──────────────────────────────────────────────────────────────────────────┤
│ Sources · data as of 2026-10-12 06:00 · *footnotes                       │ footer ≈20 px
└──────────────────────────────────────────────────────────────────────────┘
```

- Canvas 1280×720 (16:9) for Power BI and app screens; message **right of** the title on
  landscape screens, **above** it on portrait/A4 — pick one per report type and never mix.
- Key message 13 pt/17 px, title lines 11 pt/14 px (same size, measure bold), data labels
  9 pt/12 px. Smallest legible size, then use the space for context (CO 1–3).
- Slicers in a collapsible pane or a slim strip **below** the header, never over the title.
- No logo, background band, frame or shadow; branding belongs to the app shell.

## 2. Page archetypes

### A. Summary page (report entry)
Message = the report's key message (answer to the SCQ). Left: the one chart that proves it
(often a variance waterfall PL → drivers → AC/FC). Right: 2–5 MECE supporting points, each a
one-line detection with its number and a link to its page. Decisions requested / next steps at
the bottom for decision documents (SA 5.2).

### B. Variance page — one measure over time
Multi-tier horizontal chart: AC (+FC) columns with PL/PY (overlapped or triangles) at the bottom,
ΔPL columns above, ΔPL% pins on top; 13–36 periods; separator at AC→FC; trend arrow if the
message is about a trend. Optional extended "Ø" or "FY" column after a gap.

### C. Variance page — one measure by structure
Multi-tier vertical chart: AC bars with PY/PL, ΔPY/ΔPL bars to the right, Δ% pins further right;
top N + remainder; sorted by AC (or by Δ when the message is about deviations). Pair it with a
small-multiples time view (archetype D) or a vertical variance waterfall.

### D. Small multiples — one measure, many entities
Up to ~25 panels + "Others"; identical scale; an outsized entity gets a bigger panel (size to
data), never its own scale; same panel order as the sibling structure chart; axis labels only on
the outer row/column; a reference panel (e.g. average) on a light area.

### E. Explanation tree — ratio or result
Result chart on the left, driver charts to the right in tree form, operators (×, :, +, −) on
the connectors; equal-size charts; same scale for the same unit or scale bands; highlight the
driver the message names.

### F. P&L / statement table
Variance table or combined table (month | YTD blocks × PY · PL · AC · ΔPY · ΔPY% · ΔPL · ΔPL%),
report lines in rows, results bold with a line above; embedded variance bars/pins in one column
group on the page's scale. Pair with a chart only if it adds complementary data (CO 5.3).

### G. Detail / lookup (analysis page)
Dense table or cross table, sortable, no forced message, full three-line title, sources, footer;
used as a drill-through target.

## 3. Choosing between archetypes

| Audience question | Archetype | Message type |
|---|---|---|
| "Are we on plan overall?" | A or B | detection |
| "Where are we off plan?" | C (+ F) | detection / explanation |
| "Why is the result off?" | E or variance waterfall in A | explanation |
| "How do units compare over time?" | D | detection |
| "What should we do?" | A with suggestion + decision list | suggestion |
| "Show me the numbers" | F or G | none (analysis) or detection |

## 4. Interactive dashboards and apps

| Concern | Rule | Basis |
|---|---|---|
| Default state | complete message page: message, title, sources visible without interaction | CO 5, SA 4.4 |
| Filters | every active filter appears in title line 1 (period selections in line 3); dynamic title text from the same filter context | UN 2.2 |
| Dynamic messages | generated sentences may only *detect*; explanations/suggestions come from a governed commentary table keyed by period + entity and are hidden or re-scoped when filters leave that scope | SA 3.1 *(ours)* |
| Scales | recompute each scale group's px per unit once per filter context, apply to all members (each plot sized to its own range); no per-visual auto-scale | CH 4.1, 4.2 |
| Top N | recompute with filters, keep the remainder so the structure adds up | ST 3.2 |
| Cross-interaction | filter, don't highlight (highlight dims fills and imitates the light PY notation) | UN 3.2 *(ours)* |
| Tooltips | depth only (monthly detail, definitions); never the only home of message-critical numbers; not printable | CO 5 *(ours)* |
| Drill-through | to analysis pages with full titles and a back link; keeps period and unit context | UN 2.2 |
| Selection state | a selected period/entity may be marked with an assisting area or highlight ellipse, not by recolouring scenarios | UN 5.1 |
| Personalisation | bookmarks may toggle "annotated" vs "clean" view; never change notation | UN |
| Motion | no transitions or animated entry; honour reduced-motion | SI 1.3 |
| Glossary | definitions available (help page / tooltip) and footnoted where used | UN 1.1 |
| Empty / partial data | keep categories with 0 instead of dropping them; mark incomplete periods in a footnote | ST 3.2 |
| Export / print | slicers hidden, title lines fully expanded, footer with print date | UN 2.2, UN 2.5 |

Web and app specifics *(ours)*: one layout component owns the header (message + title) and the
footer so the slot is identical on every route; the route tree mirrors the storyline;
scale-group domains are computed in one place per page and passed to every chart; message
templates are rendered from the same query results as the charts (single source of truth).

## 5. Responsive and print

- Phone (≤ 430 px): title in one line with " | " is allowed; message first, then the main
  visual full width; structure charts keep bars (scroll vertically); small multiples reflow
  4 → 2 → 1 columns at the **same** scale; side gutter 16 px; labels ≥ 12 px, horizontal.
- Tablet: keep the desktop grid if labels stay legible, else stack visuals in storyline order.
- PDF/print: footnotes and sources mandatory, print date in the footer, interactive controls
  hidden, hatch pattern checked at print resolution.
