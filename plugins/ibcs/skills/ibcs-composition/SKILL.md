---
name: ibcs-composition
description: >
  Plans report pages, dashboards, Power BI pages and web/app screens so that their composition
  follows the IBCS® Standards (SAY · STRUCTURE · EXPRESS · CONDENSE); use it whenever the user
  wants to plan, design, restructure or storyboard a report, dashboard, management pack or app
  page — overview, summary, landing, executive, KPI or P&L variance page — asks "what should this
  page show", "write the headline/key message", or needs a spec for a Power BI or web-app builder,
  even if IBCS is not mentioned. Covers objective and audience, key message (detection /
  explanation / suggestion), MECE pyramid storyline, page pattern and density (multi-tier, small
  multiples, ratio tree, variance table), three-line titles, interactive behaviour (filters,
  drill, tooltips, dynamic messages), and a YAML visual spec as hand-off to builders.
---

# IBCS composition — from question to page spec

Composition is the authoring half of IBCS: deciding **what to say** and **how to arrange it** so
the page proves one message. Notation (how each element looks) lives in
[ibcs-notation](../ibcs-notation/SKILL.md); load it too whenever you pick chart details. The
output of this skill is usually a **visual spec** (YAML) that builders implement without
re-deciding the design.

Basis: IBCS Standards v2.0 (2026), composition part — SAY (pp. 77–86), STRUCTURE (pp. 87–95),
EXPRESS (pp. 96–142), CONDENSE (pp. 143–156). This skill is our own condensed restatement under
CC BY-SA 4.0 (see the repository NOTICE); it follows the IBCS® Standards and is not certified by
IBCS Institute. Items marked *(ours)* are our practice, not IBCS rules. Rule index with pages:
[references/composition-rules.md](references/composition-rules.md).

## The flow

```
Objective & audience → Key message → Storyline (MECE pyramid) → Page plan → Visuals → Check
     SA 1                 SA 2–4          ST 1–5                CO 1–5      EX, UN     review
```

Work top-down. Do not open the chart gallery before you can write the page's message as a
sentence — unless the page is deliberately an exploratory **analysis** page (§1.3). Charts
chosen first end up showing what the data has instead of what the reader needs.

## 1. Objective and audience (SA 1)

1. **Goal level** — one per page: *inform* (→ detection message), *understand* (→ explanation,
   "…because…"), *decide/act* (→ suggestion, "…therefore we should…"). Higher levels create more
   value; pick the highest the author can honestly support.
2. **Audience** — role, prior knowledge, what they accept as fact, what they want (informed /
   explained / willing to decide), **who could disagree and why** (decides evidence and
   deductive vs inductive). Medium: written/dashboard vs live slides (slides may drop sources,
   annotations, footnotes; written reports and dashboards must keep them).
3. **Page kind** — `message` page (predetermined message to prove; full SAY applies) or
   `analysis` page (statistic for exploration; no forced message, but titles, notation,
   integrity and density still apply). *(ours)* An app's entry page is a message page.

## 2. Key message (SA 2–4, UN 2.1)

- Frame it: **Situation** (agreed facts/goal) → **Complication** (what threatens it) →
  **Question** (from the audience's view) → **answer = key message**.
- Write a **complete sentence** with precise numbers, unit and comparison, signed variances, no
  vague words ("significant", "strong", "around", "much better"). One message per page/visual.
  A verdict word ("in line with", "on plan", "above/below plan") is allowed only with a declared
  threshold: put the rule in `message.bindings` (e.g. `|ΔBU%| < 0.5 %` → "in line with") and state
  it in a footnote, so the sentence changes when the numbers do.
- Templates (fill from the glossary; numbers per UN 1.2):
  - Detection: `{Measure} {is/was/will be} {value unit} {in period}, {±Δ unit} ({±Δ%}) vs {reference}.`
  - Explanation: `{Detection}, mainly because of {driver} ({±Δ unit}).`
  - Suggestion: `We should {verb + object} {by when}, because {reason with number}.`
  More templates and bad→good rewrites: [references/message-and-title-templates.md](references/message-and-title-templates.md).
- **Position:** a fixed slot at the top — above the title, or right of it on landscape pages —
  identical on every page (UN 2.1). Message first, evidence after (SA 3.2); caution with bad news
  in live presentations.
- **Prove and highlight it:** every claim must be visible on the page, and the value it cites is
  marked (blue ellipse, difference marker, trend arrow — SA 4.3). A page without any highlight is
  usually a statistic, not a message.
- **Sources and timestamp** on every written/dashboard page (SA 4.4); numbered, paired annotations
  for explanations (SA 4.5).

## 3. Storyline structure (ST)

- Build a **pyramid**: report message → 2–5 supporting arguments → facts. One page ↔ one node;
  the page's message is the node's statement, its visuals are the child facts.
- Make every list **MECE**: no overlaps ("Nordics" next to "Norway", "Costs" next to "Expenses",
  a subtotal next to its own component) and exhaustive (add "Other"/"Rest of …" last, after a gap;
  structures add up to 100 %).
- A **variance waterfall reconciles**: base + Σ steps = total. When the decomposition measures
  (e.g. price, volume, mix) do not add up to the total variance, add an explicit, named remainder
  step ("Other effects") with its own value, never a silent balancing bar, and say in the footnote
  what it contains (ours).
- Keep lists **consistent**: same item type, same statement type (all detections or all
  suggestions), same grammar (imperative verb + noun for actions), same icon style.
- **Inductive** (parallel MECE arguments) by default — dashboards, monthly reports. **Deductive**
  (statement → comment → conclusion) only for controversial need-for-action documents.
- Make structure visible: summary page first, navigation/sections mirror the pyramid, page names
  grammatically parallel; tables show hierarchy (bold totals below children).

## 4. Page plan and density (CO)

The page must contain **everything needed to understand its message** without flipping pages —
or, in an app, without clicking (tooltips and drill add depth only). Then:

1. Remove clutter (backgrounds, frames, shadows, logos, decorative colour, gridlines/value axes).
2. Shrink to the smallest legible size (fonts, components, visuals); narrow margins.
3. Add context: more periods (36 months beat 12), scenarios (PL, PY, FC) and their variances.
4. Add components/visuals using a pattern:

| Situation | Pattern | Rule |
|---|---|---|
| One measure, scenario comparison | **multi-tier chart**: base + ΔPL + ΔPL% tiers (time: tiers above; structure: tiers to the right) | CO 4.2 |
| Same measure for many entities | **small multiples**, same type, identical scale, ≤ ~25 + "Others" panel, enlarge outsized panels | CO 5.1 |
| Explain a ratio or result | **ratio / calculation tree** left→right, equal-size charts, operators on connectors | CO 5.2, EX 5.1 |
| Explain a variance | **variance waterfall** (by structure: vertical; by period: horizontal) | EX 1.1, cards A-29 / A-11 |
| P&L lines vs plan/PY | **variance table** with embedded variance bars/pins; result rows bold | EX 1.2, CO 4.4 |
| Context value (average, benchmark) | **extended chart**: extra category after a gap, same value axis | CO 4.3 |
| Detail lookup + message | **chart-table combination** with *complementary* data, never the chart's numbers again | CO 5.3 |
| Two measures, little space | overlay (columns + line) — prefer multi-tier when space allows | CO 4.1 |

5. Verify integrity: one scale per unit across the page (scale groups), scale bands where scales
   must differ, outlier markers only for irrelevant relative outliers.

Choose each visual from the [chart catalogue](../ibcs-notation/references/chart-catalogue.md)
(cards A-n) and [table catalogue](../ibcs-notation/references/table-catalogue.md) (cards B-…).
Layout grids, header/footer bands, phone/tablet reflow and page archetypes:
[references/page-patterns.md](references/page-patterns.md).

## 5. Titles (UN 2.2)

Three descriptive lines, top-left, under (or left of) the key message:

```
Line 1  who   ABC Corporation, Europe, Wholesale, top ten clients     ← every active filter
Line 2  what  **Net sales** in mEUR, by countries, sorted by AC ↓      ← measure bold, unit regular
Line 3  when  2026-Q3 AC and PY and ΔPY                               ← period, then scenarios
```

Page-wide aspects in the page title, per-visual differences in one-line subtitles; title +
subtitle always give who/what/when. Titles never evaluate — the message does.

## 6. Interactive dashboards and apps *(mostly ours, grounded in IBCS)*

- The **default state** is a complete message page: message, title, sources and timestamp
  visible, no filter needed to make sense.
- **Filters/slicers** → reflected in title line 1 (dynamic text from the same filter context).
  Hide or collapse controls that overlap the title; hide them in print/export.
- **Dynamic messages may only detect** (generated from the same measures as the visuals). An
  explanation or suggestion needs an author or a governed commentary table — and must disappear
  or be re-scoped when filters move the data away from what it describes. Otherwise mark the page
  `analysis`.
- **Scales under filtering:** recompute each scale group's px per unit once from the filtered
  context and apply it to all members, each sized to its own range; never let each visual
  auto-scale.
- **Top N** recomputes with filters and keeps a remainder ("Other") so totals reconcile.
- **Cross-filter vs cross-highlight:** prefer filtering. Highlight-dimming changes fill
  lightness, which collides with scenario notation (dimmed AC reads like PY). Where a selection
  must show, mark it with an assisting area (`color.marker.assistingArea`) behind the category.
- **Tooltips/drill-through** add depth (monthly detail, account lines) but never hold information
  the message depends on; tooltips are not printable. Drill pages are `analysis` pages with full
  titles.
- **Responsive:** small screens may write the title in one line with " | "; reflow small
  multiples by column count, never by rescaling; keep labels horizontal.
- No meaningless animation or transitions (SI 1.3).

## 7. Hand-off: the visual spec

Write the design as a YAML **visual spec** per page — the contract for builders. Where the spec
files live is the user's choice (for example a `specs` folder in the report repository); ask if
the project has no convention yet. Format, field definitions, validation rules and two worked
examples (monthly P&L variance page; sales-by-country structure page):
**[references/visual-spec-format.md](references/visual-spec-format.md)** — read it before writing
any spec, and cite a chart/table card for every visual.

Builders implement the spec with: [ibcs-web-charts](../ibcs-web-charts/SKILL.md) (SVG/React
chart components for web pages and apps, this plugin); the `ibcs-power-bi` (native Power BI
pages, theme, PBIR), `ibcs-deneb` (Deneb templates for multi-tier same-scale charts, pins,
triangles, hatched FC, waterfalls) and `ibcs-svg-dax` (variance bars/pins in tables) skills of
plugin `ibcs-power-bi`; and the `ibcs-fabric-app` skill of plugin `fabric-apps`. The data
shape each visual needs goes to the model author (the `semantic-model-ibcs` skill of plugin
`reporting-data`). Point builders at the spec file; they should not re-decide the design. The
`ibcs-visual-designer` agent of this plugin runs this whole flow.

## 8. Composition checklist (run before hand-off)

- [ ] Goal level, audience, page kind (`message`/`analysis`) recorded — SA 1
- [ ] Key message: complete sentence, precise numbers + comparison, right type, top slot — SA 3, UN 2.1
- [ ] Every claim visible on the page; cited value highlighted — SA 4.1, SA 4.3
- [ ] Sources + data timestamp + footnotes on the page: full width, sized to the text, short; long
      definitions on a details page or tooltip — SA 4.4, UN 2.5
- [ ] Three-line title; filters in line 1; descriptive only; subtitles carry only differences — UN 2.2
- [ ] Pyramid storyline; MECE lists with remainder; consistent wording — ST 1–4
- [ ] Everything needed is on this page/screen without clicking — CO 5
- [ ] Context: enough periods, scenarios and their variances — CO 3, EX 4
- [ ] Pattern fits the question (multi-tier, small multiples, tree, waterfall, variance table) — CO 4–5
- [ ] One scale per unit (scale groups declared); scale bands where unavoidable — CH 4
- [ ] No table repeating a chart's numbers — CO 5.3
- [ ] Interactive: default state complete, dynamic message detects only, filters in title — §6
- [ ] Notation spot-check with [ibcs-notation](../ibcs-notation/SKILL.md); full audit with [ibcs-review](../ibcs-review/SKILL.md)

## References in this skill

- [references/visual-spec-format.md](references/visual-spec-format.md) — the YAML hand-off format + 2 worked examples.
- [references/page-patterns.md](references/page-patterns.md) — page grids, archetypes (summary, variance, structure, small multiples, ratio tree, detail table), interactive app patterns.
- [references/message-and-title-templates.md](references/message-and-title-templates.md) — message and title templates, rewrites, page-name patterns.
- [references/composition-rules.md](references/composition-rules.md) — SA/ST/EX/CO rule index with pages, plus the medium-dependent rules.
