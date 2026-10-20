# Notation rules — index (SIMPLIFY, UNIFY, CHECK)

> One line per rule of the IBCS Standards v2.0 notation part, in our own words, with the book
> page for citation ("IBCS v2.0, UN 4.1, p. 52"). Rule IDs and short names are those of the
> Standards; the summaries are ours (CC BY-SA 4.0, see the repository NOTICE). In v2.0 the
> notation part is presented as an application of ISO 24896 ("Notation for business
> reporting"); rules marked **ISO** are ones IBCS describes as ISO requirements. Implementation
> hints are ours.

Principles in one sentence each:
- **SIMPLIFY** — leave out whatever is redundant, distracting or only decorative (pp. 16–23).
- **UNIFY** — the same meaning gets the same visual form, everywhere (pp. 24–67).
- **CHECK** — no visual representation may mislead (pp. 68–75).

## Contents
- [SIMPLIFY (SI)](#simplify-si)
- [UNIFY (UN)](#unify-un)
- [CHECK (CH)](#check-ch)
- [Our additions (not IBCS rules)](#our-additions-not-ibcs-rules)

## SIMPLIFY (SI)

| ID | Rule | p. | In short |
|---|---|---|---|
| SI 1 | Avoid unnecessary elements | 16 | Drop pictures, backgrounds and logos that do not help understanding. |
| SI 1.1 | Avoid cluttered layouts | 16 | No corporate bands, clip-art or decorative shapes; branding belongs to the shell, not the page. |
| SI 1.2 | Avoid colored or filled backgrounds | 16–17 | Black text on white; no header bands, banded rows or cell fills (light-gray totals are the exception, EX 1.2). |
| SI 1.3 | Avoid animation and transition effects | 17 | No motion unless the motion is the analysis; honour reduced-motion settings. |
| SI 2 | Avoid decorative styles | 17 | Use the simplest style for every component. |
| SI 2.1 | Avoid frames, shades, pseudo-3D | 17–18 | Flat 2-D, no borders, shadows, bevels, gradients (PL outlines are notation, not frames). |
| SI 2.2 | Avoid decorative colors | 18 | Colour only with analytical meaning; otherwise grays. One highlight colour for the element the message is about. |
| SI 2.3 | Avoid decorative fonts | 18–19 | One plain, widely available sans-serif; bold/italic only for semantic distinctions (measure in title, totals, shares). |
| SI 3 | Replace with cleaner layout | 19 | Convey the same with less ink. |
| SI 3.1 | Replace grid lines and value axes with data labels | 19–20 | Labelled charts need no value axis, ticks or grid; grids stay where reference points are missing (dense charts, small multiples). |
| SI 3.2 | Avoid vertical lines by right-aligning data | 20 | Tables: right-align numbers and their headers, no vertical rules. |
| SI 4 | Avoid redundancies | 20 | Remove words that repeat what is already clear. |
| SI 4.1 | Avoid superfluous words | 20–21 | No "Total", "Sum of", "Full year"; bold already marks a total. |
| SI 4.2 | Avoid obvious terms | 21 | No "analysis", "overview", "development", "trend", "report", "chart", "table", "statistics", "structure", "comment". |
| SI 4.3 | Avoid repeated words | 21 | Move words repeated on every label (the year, "Division") into the title. |
| SI 5 | Avoid distracting details | 22 | Leave out detail that does not support the message. |
| SI 5.1 | Avoid labels for small values | 22 | Tiny segments stay unlabelled unless discussed; then use leader lines. |
| SI 5.2 | Avoid long numbers | 22 | At most 3 digits in charts and 4 in tables; scale with k/m/b. |
| SI 5.3 | Avoid unnecessary labels | 22–23 | In dense series label only significant points (first, last, min, max, current). |

## UNIFY (UN)

| ID | Rule | p. | In short |
|---|---|---|---|
| UN 1 | Unify terminology | 25 | **ISO** One organisation-wide vocabulary. |
| UN 1.1 | Unify terms and abbreviations | 25 | A shared glossary; short abbreviations in column headers, long forms in row headers. |
| UN 1.2 | Unify numbers, units, and dates | 26–27 | **ISO** One number format (narrow-space thousands, one decimal sign, one negative style), "+" only on variances, ISO 4217 codes with k/m/b prefixes (kEUR), SI prefixes k/M/G otherwise, ISO 8601 dates. |
| UN 2 | Unify text elements | 27 | **ISO** Distinguish descriptive elements (titles, legends, labels, footnotes) from explanatory ones (messages, annotations). |
| UN 2.1 | Unify key messages | 27–28 | Key message at one fixed position on every page — at the top, above or right of the title. |
| UN 2.2 | Unify titles and subtitles | 28–33 | **ISO** Three descriptive title lines: who (unit + filters) / what (**measure** + unit) / when (period, scenarios, variances); subtitles carry only what differs between visuals. |
| UN 2.3 | Unify the position of legends and labels | 33–38 | **ISO** Legends integrated at the data, labels next to their element, all text horizontal; external legends acceptable for two-value-axis charts. |
| UN 2.4 | Unify annotations | 38–39 | **ISO** Annotations inside the visual where possible, linked by paired numbered references. |
| UN 2.5 | Unify footnotes | 39 | Definitions, sources and dates at the page bottom; required in written material. |
| UN 3 | Unify dimensions | 40 | **ISO** Measures, scenarios, periods and structure each have a fixed visual language. |
| UN 3.1 | Unify measures | 40–42 | **ISO** Absolute: 2/3 category width, thick lines. Relative: 1/3 width, half-thickness lines. |
| UN 3.2 | Unify scenarios | 42–46 | **ISO** AC solid dark, PY solid light, PL/BU outlined, FC hatched; stacked: notation on the lowest segment, grays above. |
| UN 3.3 | Unify time periods, use horizontal axes | 46–48 | **ISO** Time runs left → right on a horizontal axis (table columns); longer periods get wider categories, fixed per page. |
| UN 3.4 | Unify structure dimensions, use vertical axes | 48–49 | **ISO** Structure runs top → bottom on a vertical axis (table rows); exceptions for interval scales such as histograms. |
| UN 4 | Unify analyses | 49 | **ISO** Scenario, time and structure analyses have a fixed notation. |
| UN 4.1 | Unify scenario analyses | 49–55 | **ISO** Overlap or triangles for comparisons; ΔPY/ΔPL with the base's width and scale; impact colours green/red/blue by polarity; minuend in the fill, subtrahend on the axis; pins and N/A for relative variances; pp for % variances. |
| UN 4.2 | Unify time series analyses | 55–58 | **ISO** YTD "_x", YTG "x_", moving "~x" (MAT/MAA), temporal index with a black arrowhead at 100 %. |
| UN 4.3 | Unify structure analyses | 58–60 | **ISO** Average "Ø", ranking arrows, top N with a remainder, structural index and normalising markers (selecting not yet in ISO). |
| UN 4.4 | Unify adjustment analyses | 61 | Adjusted values (currency, inflation, seasonality) marked, e.g. "AC*" + footnote (no ISO notation yet). |
| UN 5 | Unify markers | 61 | **ISO** Every marker has one documented design. |
| UN 5.1 | Unify highlighting markers | 61–66 | **ISO** Assisting lines/areas, difference markers, trend arrows, blue highlighting ellipse, black reference arrowheads, paired annotation references. |
| UN 5.2 | Unify scaling markers | 66–67 | **ISO** Scale bands — a light area up to the same numeric value in every chart — when scales must differ. |
| UN 5.3 | Unify outlier markers | 67 | **ISO** Values beyond the visible scale are marked consistently; a headless pin with a growth-direction triangle works well. |

## CHECK (CH)

| ID | Rule | p. | In short |
|---|---|---|---|
| CH 1 | Avoid manipulated axes | 68 | Axes must let values be compared truthfully. |
| CH 1.1 | Avoid truncated axes | 68 | **ISO** Value axes start at zero; indexed data near 100 % may zoom if category labels sit on the 100 % line. |
| CH 1.2 | Avoid logarithmic axes | 69 | Linear by default; log only for relative growth across orders of magnitude, clearly marked, for an audience used to it. |
| CH 1.3 | Avoid different class sizes | 69 | Ordered classes (histograms) have equal widths. |
| CH 2 | Avoid manipulated visual components | 70 | Do not distort components to fit extremes. |
| CH 2.1 | Avoid clipped visual components | 70 | **ISO** No broken columns or bars (outlier markers for irrelevant relative values excepted). |
| CH 2.2 | Use creative solutions for challenging scaling issues | 70 | Extreme ranges may use unit grids or bent columns whose length stays proportional. |
| CH 3 | Avoid misleading representations | 71 | The visual impression must match the values. |
| CH 3.1 | Use correct area comparisons, prefer linear ones | 71 | Encode by area (never diameter or icon height); prefer bars. |
| CH 3.2 | Use correct volume comparisons, prefer linear ones | 71 | Avoid 3-D volumes; prefer bars. |
| CH 3.3 | Avoid misleading colored areas in maps | 72 | Filled maps only for area-related measures; otherwise symbols of one scale (or small pies) on the map, or no map. |
| CH 4 | Use the same scales | 72 | Same unit, same scale — or show clearly that it differs. |
| CH 4.1 | Use identical scale for the same unit | 72 | **ISO** All charts of one unit on a page share the scale; in extreme cases different scales with scaling markers. |
| CH 4.2 | Size charts to given data | 73 | Make the chart with the big values bigger instead of changing its scale. |
| CH 4.3 | Use scaling markers if necessary | 73 | Scale bands at the same value (typically a power of 10) in all compared charts. |
| CH 4.4 | Use outlier markers if necessary | 73–74 | Do not scale a chart to a business-irrelevant outlier; mark it instead. |
| CH 4.5 | Use magnifying glasses | 74 | Mark a region and link it to a zoomed chart. |
| CH 5 | Show data adjustments | 74 | Make distorting effects in long series visible. |
| CH 5.1 | Show the impact of inflation | 74 | Show real values and the inflation share separately. |
| CH 5.2 | Show the currency impact | 75 | Compare at constant rates ("AC*", footnoted) where currency moves distort. |

## Our additions (not IBCS rules)

- **N/A threshold** (`OURS`, derived from UN 4.1, p. 54, `STD`): IBCS marks a relative variance
  N/A when it cannot be interpreted, e.g. a positive AC against a negative reference; we make that
  operational as "reference ≤ 0 or blank → N/A". It protects the hard rule beside it: divide by
  the signed reference, never by its absolute value.
- **Δ% near zero** (`OURS`, optional): also N/A when the reference rounds to zero at the displayed
  precision; IBCS states no such threshold.
- **Scale group**: the set of visuals/tiers that share one unit and therefore one px per unit,
  recomputed once per filter context; each member's plot extent = its own data range × px per
  unit (CH 4.1 with CH 4.2), never a shared domain max on a smaller chart.
- **Default order** for orders-of-magnitude problems: size to data → scale bands → magnifying
  glass (IBCS lists the options without a priority).
