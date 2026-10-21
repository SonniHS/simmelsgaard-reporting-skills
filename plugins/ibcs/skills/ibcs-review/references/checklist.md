# IBCS review checklist

> A–G are notation checks (IBCS Standards v2.0, pp. 16–75); H/J/K are composition checks from
> SAY, STRUCTURE, EXPRESS, CONDENSE (pp. 77–156). The IDs and wording are ours; CC BY-SA 4.0, see
> the repository NOTICE. Sev: M must, S should, I info. Detect: `lint` = covered by
> `scripts/ibcs_lint.py` (at least partly), `meta` = report/visual JSON or spec, `model` = DAX /
> semantic model, `img` = screenshot, `text` = strings, `human` = judgement.
> **Exceptions** listed per item are allowed by IBCS and must not be reported as failures.
> The linter also emits `LINT` (sev I, status check) for a part it could not read, such as an
> unparsable Deneb spec; that is not a checklist item, review the part manually.

## Contents
- [A. Page and layout (SIMPLIFY)](#a-page-and-layout-simplify)
- [B. Terminology and formats (UN 1)](#b-terminology-and-formats-un-1)
- [C. Text elements (UN 2)](#c-text-elements-un-2)
- [D. Dimensions (UN 3)](#d-dimensions-un-3)
- [E. Analyses (UN 4)](#e-analyses-un-4)
- [F. Markers (UN 5)](#f-markers-un-5)
- [G. Visual integrity (CHECK)](#g-visual-integrity-check)
- [H. Message (SAY)](#h-message-say)
- [J. Structure (STRUCTURE)](#j-structure-structure)
- [K. Density (CONDENSE)](#k-density-condense)

## A. Page and layout (SIMPLIFY)

| ID | Pass if … | Rule | Sev | Detect | Exceptions / notes |
|---|---|---|---|---|---|
| A1 | no logos, pictures, decorative shapes/bands | SI 1.1 | S | lint(image/shape), img | branding in the app shell is fine; one logo in the corner of a page shell's header card *(ours)* |
| A2 | white page and visual backgrounds; no coloured headers, banded rows, cell fills | SI 1.2 | S | lint, img | light-gray fill on totals/result rows & columns is allowed (pp. 121–128); light assisting areas with meaning; a page shell *(ours)*: neutral light canvas between white cards (a card shape behind the content, or white visuals in the square mode; lint fails content on the canvas outside a card) |
| A3 | no meaningless animation, play axes, transitions | SI 1.3 | S | lint(Play), meta | animation that *is* the analysis |
| A4 | no frames, shadows, rounded containers, gradients, pseudo-3D on content (charts, tables, text) | SI 2.1 | S | lint, img | PL outlines are notation, not frames; page-shell card chrome *(ours, house style)*: the card shape behind the content may have radius 8, a 1 px ring and a soft shadow (lint exempts shapes) |
| A5 | every colour has analytical meaning; no per-category palette | SI 2.2 | M | lint, img | one highlight colour for the element the message is about |
| A6 | one plain sans-serif family | SI 2.3 | S | lint(theme), img | serif for multi-line flow text |
| A7 | bold/italic only for semantics (measure in title, totals, defined rows) | SI 2.3 | S | img | totals may be distinguished by bold **or** a light-gray fill (pp. 121, 128) |
| A8 | fully labelled charts have no value axis/ticks/gridlines | SI 3.1 | S | lint, img | gridlines where helpful: small multiples, dense charts, scatter/bubble (p. 19) |
| A9 | tables: no vertical rules; numbers + headers right-aligned | SI 3.2 | S | meta, img | very light separators/white gaps |
| A10 | no "Sum of", "Total", "Full year" in titles/headers/labels | SI 4.1 | S | lint, text | — |
| A11 | no obvious terms in titles (analysis, overview, dashboard, report, chart, table, trend, development, statistics, structure, comment) | SI 4.2 | S | lint, text | — |
| A12 | no word repeated across all labels (year on every month) | SI 4.3 | S | text | — |
| A13 | small segments unlabelled (or leader lines) | SI 5.1 | S | img | explicitly discussed values |
| A14 | ≤ 3 digits in charts, ≤ 4 in tables | SI 5.2 | M | lint(Auto units), text | — |
| A15 | dense series label only significant points | SI 5.3 | S | img | — |

## B. Terminology and formats (UN 1)

| ID | Pass if … | Rule | Sev | Detect |
|---|---|---|---|---|
| B1 | measure names from the glossary, same concept = same term everywhere | UN 1.1 | M | model, text |
| B2 | abbreviations defined; short in column headers, long in row headers | UN 1.1 | S | text |
| B3 | one number format (thousands separator, decimal sign) | UN 1.2 | M | text |
| B4 | one negative style | UN 1.2 | M | text |
| B5 | "+" on every positive variance except one that rounds to 0 at the displayed decimals (printed unsigned, e.g. `0.0`); no "+" anywhere else; never `+0.0` / `-0.0` | UN 1.2, 4.1 | M | text, model (format strings) |
| B6 | ISO 4217 codes; no symbols when currencies mix | UN 1.2 | S | text |
| B7 | prefixes kEUR/mEUR/bEUR; SI units k/M/G | UN 1.2 | S | text |
| B8 | ISO dates and periods (2026-Q2, 2026-06) or documented short forms | UN 1.2, 3.3 | S | text |
| B9 | spans with "..", first/last day with "." | UN 3.3 | S | text |

## C. Text elements (UN 2)

| ID | Pass if … | Rule | Sev | Detect | Exceptions / notes |
|---|---|---|---|---|---|
| C1 | key message at the organisation's fixed position, same on all pages | UN 2.1 | M | img | position is an org choice; consistency is the rule |
| C2 | page title present (M), at the organisation's consistent position (S; top-left recommended, "may vary from organization to organization", p. 31) | UN 2.2 | M/S | lint(check), img | other consistent positions are fine |
| C3 | line 1 = reporting unit + every active filter (incl. top N) | UN 2.2 | M | meta, text | — |
| C4 | line 2 = **measure** bold + unit regular; set name if > 2 measures | UN 2.2 | M | img, text | — |
| C5 | line 3 = period(s), then scenarios/variances; "&" vs "and" correct | UN 2.2 | M | text | AC may be omitted if only actuals |
| C6 | title + subtitle give who/what/when for every visual | UN 2.2 | M | text | — |
| C7 | titles purely descriptive | UN 2.2 | M | human | — |
| C8 | subtitles above visuals, only differing identifiers | UN 2.2 | S | img | — |
| C9 | controls do not overlap titles; hidden when unused/printing | UN 2.2 | S | meta, img | — |
| C10 | legends integrated, horizontal | UN 2.3 | S | lint, img | external legend next to symbols in scatter/bubble charts |
| C11 | legend position fits chart type | UN 2.3 | S | img | stacked bars: above the top **or** below the bottom bar (pp. 36, 108) |
| C12 | category and data labels horizontal | UN 2.3 | M | lint, img | — |
| C13 | data labels next to their element (leader lines otherwise) | UN 2.3 | S | img | — |
| C14 | annotations linked by paired numbered references | UN 2.4 | S | img | — |
| C15 | footnotes at page bottom (sources, definitions, dates) | UN 2.5 | S | img | may be omitted on live slides |

## D. Dimensions (UN 3)

| ID | Pass if … | Rule | Sev | Detect | Exceptions / notes |
|---|---|---|---|---|---|
| D1 | absolute columns/bars = 2/3 of category width | UN 3.1 | M | meta (padding), img (estimate) | — |
| D2 | relative columns/bars = 1/3 of category width | UN 3.1 | M | meta, img | — |
| D3 | lines: thick absolute, thin (50 %) relative | UN 3.1 | M | meta | — |
| D4 | AC solid dark | UN 3.2 | M | img, meta | — |
| D5 | PY solid light, only in comparisons | UN 3.2 | M | img | — |
| D6 | PL/BU outlined; hollow line markers; double header rule | UN 3.2 | M | img | — |
| D7 | FC hatched; hatched line markers (continuous line, not dashed) | UN 3.2 | M | img | documented native-tool compromise = deviation, report as S |
| D8 | no scenario distinguished by hue | UN 3.2 | M | lint(tokens), img | — |
| D9 | stacked: notation on lowest segment, upper segments gray shades | UN 3.2 | S | img | — |
| D10 | scenario codes AC/PY/PL/BU/FC consistent | UN 3.2 | S | text | — |
| D11 | time on horizontal axes and in table columns, left → right | UN 3.3 | M | lint, meta | — |
| D12 | category width by period type, constant per type on the page | UN 3.3 | S | img | — |
| D13 | structure on vertical axes (bars) / table rows | UN 3.4 | M | lint(check), meta | histograms/interval scales; **tables** may have structure columns and cross tables (pp. 119, 133) |

## E. Analyses (UN 4)

| ID | Pass if … | Rule | Sev | Detect | Notes |
|---|---|---|---|---|---|
| E1 | scenario order: periods ascending; same period PL → FC → AC | UN 4.1 | S | meta | — |
| E2 | measured comparisons labelled AC/PY, not years | UN 4.1 | S | text | — |
| E3 | comparisons by overlap (AC/FC in front) or scenario triangles | UN 4.1 | S | img | — |
| E4 | absolute variances named ΔPY/ΔPL (or AC-PL …) | UN 4.1 | S | text | — |
| E5 | **absolute** variance bars same width and same scale as base | UN 4.1 | M | meta, img | relative variances use their own % scale |
| E6 | three impact colours by polarity: desirable green, undesirable red, neutral/ambiguous blue; geometry follows the sign; Δ = 0, or a Δ that rounds to 0 at the displayed decimals, has no colour and no mark (never green, red or blue) | UN 4.1 | M | model, img | exact codes are an org choice; hue families are not |
| E7 | where colour is unavailable, grays are used (red → dark, green → light, blue → medium gray); for colour-deficient readers green → blue-green where helpful (p. 52) | UN 4.1 | S | lint(tokens), meta | separate CVD/B&W report variants are organisational policy, not IBCS — never fail a page for lacking them |
| E8 | variance fill shows minuend (AC solid, FC hatched, PL outlined) | UN 4.1 | M | img | — |
| E9 | variance axis shows subtrahend (PY solid light, PL/BU double line) | UN 4.1 | M | img | — |
| E10 | variance labels outside, in direction of change | UN 4.1 | S | img | — |
| E11 | absolute variance of percentages in pp | UN 4.1 | M | text | — |
| E12 | relative variances named ΔPY%/ΔPL%, shown as pins, computed with the **signed** reference; the pin length carries the value: the pin tier has its own scale sized to the tier, so a chart's largest \|Δ%\| fills most of it (stem ≥ 40 % of the tier, OURS), heads small (6 px) at the stem end, a Δ% that rounds to zero keeps a baseline marker | UN 4.1 | M | img, model | head shape: square is the default, not a mandate; LINT: a fixed pin scale of ≤ 1 px per point |
| E13 | pin heads show the minuend | UN 4.1 | S | img | — |
| E14 | uninterpretable relative variance shown as N/A (never via ABS); our rule: reference ≤ 0 or blank → N/A | UN 4.1 (rule OURS) | M | model | PL 100 / AC −20 → −120 % is valid |
| E15–E18 | YTD/YTG/moving/Ø notation; index arrowheads; ranking arrows; adjusted values AC* footnoted | UN 4.2–4.4 | S | text, img | — |

## F. Markers (UN 5)

| ID | Pass if … | Rule | Sev | Detect |
|---|---|---|---|---|
| F1 | value the message refers to is highlighted | UN 5.1, SA 4.3 | S | img |
| F2 | difference markers between parallel assisting lines, impact-coloured | UN 5.1 | S | img |
| F3 | trend arrows first → last period, impact-coloured | UN 5.1 | S | img |
| F4 | reference arrowheads black, label next to them | UN 5.1 | S | img |
| F5 | marker designs identical across pages, documented | UN 5.1 | M | human |
| F6 | same-unit charts with different scales carry scale bands | UN 5.2, CH 4.3 | M | img |
| F7 | outliers that exceed the scale are only business-irrelevant relative values, consistently marked and clearly shown as exceeding the visible scale (M); recommended design: pin without head + triangle in growth direction, full value labelled (S, "a good choice", p. 67) | UN 5.3, CH 4.4 | M/S | img, human |

## G. Visual integrity (CHECK)

| ID | Pass if … | Rule | Sev | Detect | Exceptions |
|---|---|---|---|---|---|
| G1 | value axes start at zero (the axis range includes 0; lint fails start > 0 or end < 0) | CH 1.1 | M | lint, meta | indexed data near 100 % with category labels on the 100 % line |
| G2 | linear axes | CH 1.2 | M | lint(check) | log for relative growth across orders of magnitude, clearly indicated, familiar audience (p. 69) |
| G3 | equal class widths | CH 1.3 | M | model | — |
| G4 | no broken/clipped columns, bars, axes | CH 2.1 | M | img | outlier markers (F7) |
| G5 | areas encode by area, never diameter/height | CH 3.1 | M | lint(treemap), meta | — |
| G6 | volume (3-D) encodings avoided, prefer linear comparisons; if used, volume corresponds to the value | CH 3.2 | M | lint, img | 2-D/3-D components as a creative solution for values differing by orders of magnitude (CH 2.2, p. 70); decorative pseudo-3D is never allowed (SI 2.1) |
| G7 | filled maps only for area-related measures | CH 3.3 | M | lint(check), human | densities |
| G8 | same unit on a page ⇒ identical scale (small multiples, tiers, separate visuals) | CH 4.1 | M | meta (fixed/shared axes), img (px per unit), lint (Deneb: shared domain on visuals of different size, missing or unequal pxPerUnit; with `--layout` the sizes from scale_layout.py) | extreme cases with scaling markers (p. 72) |
| G9 | orders-of-magnitude differences handled by size-to-data, scale bands or magnifying glass | CH 4.2–4.5 | S | img | — |
| G10 | inflation/currency effects shown where they distort long series | CH 5 | S | human | — |

## H. Message (SAY)

| ID | Pass if … | Rule | Sev | Detect |
|---|---|---|---|---|
| H1 | message page carries a key message as a complete sentence | SA 3.1 | M | img, text |
| H2 | message is precise: number, unit, comparison; no vague qualifiers | SA 4.2 | S | text |
| H3 | message first (top slot), same layout on all pages | SA 3.2, UN 2.1 | M | img |
| H4 | every claim in the message is visible on the page | SA 4.1 | S | human |
| H5 | the cited value is highlighted | SA 4.3 | S | img |
| H6 | sources and data timestamp on written/dashboard pages | SA 4.4 | M | img |
| H7 | dynamic (generated) messages only detect; explanation/suggestion text is scoped to its context | SA 3.1 *(ours)* | S | meta |
| H8 | decks end with message + decisions, not "Thank you" | SA 5 | S | img |

## J. Structure (STRUCTURE)

| ID | Pass if … | Rule | Sev | Detect |
|---|---|---|---|---|
| J1 | list items of one type, statement type and grammar (pages, KPIs, findings, actions) | ST 1 | S | text |
| J2 | no overlapping pages, measures or members (Nordics next to Norway) | ST 2 | S | text, model |
| J3 | structures exhaustive: remainder category, parts add up to the total | ST 3 | S | model, img |
| J4 | remainder last, after a gap, excluded from rank/average | ST 3.2, EX 1.1 | S | img |
| J5 | storyline visible: summary first, navigation mirrors the pyramid | ST 4, ST 5.1 | S | meta |
| J6 | tables show hierarchy: totals bold below children, results rows marked | ST 5.2 | S | img |

## K. Density (CONDENSE)

| ID | Pass if … | Rule | Sev | Detect |
|---|---|---|---|---|
| K1 | all information needed for the message on the page, without clicking | CO 5 | S | human |
| K2 | small legible fonts/visuals; no oversized cards or titles | CO 1 | S | img |
| K3 | narrow margins, no empty panels (structuring whitespace is fine) | CO 2 | S | img |
| K4 | enough context: periods, scenarios, variances | CO 3, EX 4 | S | img |
| K5 | combined charts used correctly (tiers above/right; extension on same axis; overlay shares category axis) | CO 4 | S | img |
| K6 | table bars aligned to rows; sparklines on a common/indexed scale; traffic lights only ≤ 3 binary states | CO 4.4, EX 2.5 | S | img |
| K7 | small multiples: same type, identical scale, ≤ ~25 + Others | CO 5.1 | M | meta, img |
| K8 | no table repeating a chart's numbers | CO 5.3 | S | img |
| K9 | replace pie/donut, gauge, radar, funnel, spaghetti (> 3–4 lines) | EX 2 | S | lint, img |
