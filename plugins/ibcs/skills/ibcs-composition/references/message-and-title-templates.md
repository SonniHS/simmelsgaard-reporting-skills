# Message and title templates

> Built on IBCS Standards v2.0 — SAY (SA 3.1, SA 4.2), UNIFY (UN 2.1, UN 2.2), STRUCTURE (ST 1);
> our restatement and our own examples, CC BY-SA 4.0 (see the repository NOTICE). Number formats
> per UN 1.2 (signed variances, kEUR/mEUR, narrow-space thousands). All names and numbers in the
> examples are invented.

## 1. Key message templates

**Detection** (verifiable fact; as precise as possible)
- `{Measure} {is/was/will be} {v unit} in {period}, {±Δ unit} ({±Δ%}) vs {PL|PY|FC}.`
  → "Net sales are 12.4 mEUR in 2026-Q3, -1.1 mEUR (-8%) vs plan."
- `{Measure} {rose/fell} from {v1} to {v2} {between p1 and p2}.`
  → "Gross margin fell from 41.0% to 38.2% between 2026-Q1 and 2026-Q3."
- `{Entity} is the only {entity type} with {condition} {in period}.`
  → "Plant North is the only plant with costs below plan in every month of 2026."
- `{n} of {m} {entities} are below {reference}; together {±Δ unit}.`
  → "3 of 12 plants are below plan; together -2.4 mEUR."
- Trend: `{Measure} grew by {CAGR} a year from {p1} to {p2}.`

**Explanation** (detection + reason)
- `{Detection}, mainly because of {driver} ({±Δ unit}).`
  → "EBIT 2026 FC is 7.0 mEUR (-15%) below plan, mainly because of Retail volume (-4.8 mEUR)."
- `{Detection} because {cause 1}, {cause 2} and {cause 3}.` — causes MECE (ST 2–3).
- `Despite {positive fact}, {measure} {fell} because {cause}.`

**Suggestion** (what to do)
- `We should {imperative verb + object} {by when}, because {reason with number}.`
  → "We should stop Project B by 2026-12: costs are 0.8 mEUR above budget."
- `Therefore, we should {action} to {expected effect with number}.`

**Rewrites (SA 4.2)**

| Don't | Do |
|---|---|
| Sales overview | Net sales are 148.2 mEUR in 2026-Q3, +6.4 mEUR (+5%) vs PY. |
| Margin pressure | Gross margin fell from 41.0% to 38.2% (-2.8pp) since 2026-Q1. |
| Significant cost variance | Personnel costs are 0.4 mEUR (+3%) above plan. |
| Sales developed well | Net sales are 3% above plan in every month since April. |
| Roughly 50 new customers | 47 new customers in 2026-Q3, +9 vs PY. |
| Major savings | Savings of 1.2 mEUR in 2026, +0.3 mEUR vs plan. |

Signal words: detection "is/are/was", explanation "because/mainly due to", suggestion
"therefore we should". One message per page; complete sentence; ≤ 2 lines.

## 2. Title templates (three lines, descriptive)

| Line | Template | Examples |
|---|---|---|
| 1 who | `{Reporting unit}[, {structure filter}…][, {value filter}]` | ABC Corporation · ABC Corporation, Europe, Wholesale · ABC Corporation, top ten clients · …, divisions with negative EBIT in 2026 |
| 2 what | `**{Measure}** in {unit}[, **{measure 2}** in {unit}][, by {dimension}][, sorted by {x} (↓)][, indexed ({base} = 100%)]` or `**{Set name}** in {unit}` | **Net sales** in mEUR · **Net sales** in mEUR, **margin** in % · **Headcount** in #, by offices · **Income statement** in kEUR · **ROI tree** |
| 3 when | `{period(s)} [{scenarios}] [{variances}]` with `&` = one series, `and` = parallel | 2026 · 2026-Q3 AC and PL · 2026 AC&FC and PY · 2023..2030 AC&PL · _Sep 2026 AC and ΔPY · 2026-01..10 |

Subtitles (multi-visual pages): one line, only the differing identifiers —
`**Revenue** in mEUR | **Sales** in SKU | **Avg. price** in EUR/SKU`; `Apples | Pears`;
`2022..2026 | 2026-Q1..Q3`.

Footnote marker for qualifiers: `**Net sales*** in mEUR` + footnote "*without intercompany sales".

**Plain sums.** When the reporting unit's figures are a plain sum of its entities (no
consolidation: no intercompany eliminations, no currency or ownership adjustments), line 1 says so:
`{Group}, sum of {n} {entities} (not consolidated)` (e.g. "ABC Group, sum of six companies (not
consolidated)"). The group name alone reads as a consolidated figure. A filtered line 1 keeps the
qualifier for the remaining members ("ABC Group, sum of two companies (not consolidated): A, B"),
and the footnote that defines the measure repeats it.

Forbidden in titles: evaluation ("strong", "below expectations"), "Total", "Sum of", "Full
year", obvious terms ("analysis", "overview", "report", "dashboard", "chart", "table",
"development", "trend", "statistics", "structure", "comment"), units in brackets "[mEUR]",
words repeated across all labels.

## 3. Dynamic title and message text (interactive)

- Line 1 = fixed reporting unit + `", " + selected members` for each filtered slicer
  (a concatenation of the selected values; "top N" when a Top-N filter is active; nothing when
  the slicer is at "all").
- Line 3 = the selected period label in IBCS notation (`2026-Q3`, `_Sep 2026`, `Jan..Sep 2026`)
  + the scenario codes shown.
- Detection templates are filled from the same measures the visuals use, formatted with the
  token formats (`number.format.variance` for Δ, `number.format.relativeVariance` for Δ%). If a
  value is blank or N/A, drop the clause rather than printing "N/A" in a sentence.

## 4. Page and list naming (ST 1)

- Navigation/page names: nouns of the same kind ("Net sales", "Gross margin", "Costs",
  "Cash") or imperative actions for decision pages ("Close plant C", "Reprice range B") — never
  mixed.
- Lists of findings: all detections; lists of actions: all imperative verb + noun.
- Non-overlapping: no "Costs" and "Expenses" pages; no "Germany" and "DACH" siblings.
