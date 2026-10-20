# Glossary

> Short definitions, in our own words, of the terms used in the IBCS Standards v2.0 and in this
> plugin; page numbers refer to IBCS v2.0. Entries marked *(ours)* are this plugin's terms.
> CC BY-SA 4.0, see the repository NOTICE.

## Framework

| Term | Meaning | p. |
|---|---|---|
| IBCS® | International Business Communication Standards: rules for the notation and composition of reports, presentations and dashboards, published by the IBCS Association under CC BY-SA 4.0. IBCS® is a registered trademark of IBCS Institute. | iii–iv |
| ISO 24896 | International standard "Notation for business reporting"; IBCS v2.0 treats it as the normative basis of SIMPLIFY, UNIFY and CHECK. | iii, 15 |
| SUCCESS | The seven areas: SAY, UNIFY, CONDENSE, CHECK, EXPRESS, SIMPLIFY, STRUCTURE. | iii |
| Notation | Agreed syntax and meaning of visual elements (terms, text elements, layouts, scenario and variance design); SIMPLIFY, UNIFY, CHECK. | vii, 15 |
| Composition | The authoring side: what to say and how to arrange it; SAY, STRUCTURE, EXPRESS, CONDENSE. | iv, 77 |
| Notation manual | The organisation's own document fixing colours, fonts, page grids and any choices IBCS leaves open. | v–vii |
| Semantic notation | Same meaning → same look; different meaning → different look. | 24 |

## Reporting objects

| Term | Meaning | p. |
|---|---|---|
| Report | One or more pages or screens: written report, presentation, dashboard; static or interactive. | v |
| Report page | One sheet, slide or screen; its content can be read without turning to another page. | v–vi, 153 |
| Message page vs statistic | A message page proves a predetermined message; a statistic (analysis page) supports exploration without one. | v |
| Visual | A chart, table or image on a page. | vi |
| Visual component | A part of a visual (bars, labels, axes) or a general element (title, message, footnote, annotation). | vi |
| Chart | A graphical visual; always selective, used to prove a message. | 96 |
| Table | Data in columns and rows with headers; for looking up, not for highlighting. | 96, 115 |

## Data

| Term | Meaning | p. |
|---|---|---|
| Dimension / category | A set of elements that classify data points (measures, scenarios, periods, structure) / one element of it. | vi, 40 |
| Measure | A quantitative business figure (net sales, headcount, return on sales). | vi, 40 |
| Absolute / relative measure | Absolute: currency, physical unit, count. Relative: quotient of two absolute measures (ratio, %, share). | 40–42 |
| Flow / stock measure | Flow covers a period (sales); stock is a point in time (inventory). | 42 |
| Scenario | A data version to compare: AC actual, PY previous year, PL plan, BU budget, FC forecast; external benchmarks can be scenarios. | 42–46 |
| Structure dimension | Any dimension other than measures, scenarios and time (regions, products, accounts). | vi, 48 |
| Reporting unit | The "who" of a page (entity, unit, project) plus its filters — title line 1. | 29 |
| Polarity *(ours)* | Per-measure attribute: +1 more is better, −1 less is better, 0 neutral; selects the impact colour only. | — |
| Scale group *(ours)* | All visuals/tiers of one unit on a page, sharing one px per unit; each plot is sized to its own data range. | — |

## Text elements

| Term | Meaning | p. |
|---|---|---|
| Key message | The sentence the page is meant to convey (detection, explanation or suggestion); first, at a fixed position. | 27–28, 78–82 |
| Detection / explanation / suggestion | A checkable fact / its reason ("because") / what to do ("therefore"). | 80–81 |
| Title | Purely descriptive three lines: who, what, when. | 28–31 |
| Subtitle | One line above a visual with only what differs from the page title. | 32–33 |
| Legend / label | Name of a series / of a category or value, placed at the data. | 33–38 |
| Annotation | Explanatory text linked to an element by paired numbered references. | 38, 84 |
| Footnote | Definitions, sources, dates at the page bottom. | 39 |
| Glossary | The organisation's list of terms and abbreviations. | 25 |

## Analyses

| Term | Meaning | p. |
|---|---|---|
| Absolute variance (Δ) | Difference of two scenarios of one measure, named after the subtrahend: ΔPL = AC − PL. | 51 |
| Relative variance (Δ%) | Absolute variance in % of the (signed) reference; N/A when not interpretable. | 53–54 |
| Percentage points (pp) | Absolute variance of two percentages. | 53 |
| Impact colours | Bright green desirable, dark red undesirable, blue neutral/ambiguous. | 52–54 |
| YTD / YTG / MAT / MAA | Year to date / to go, moving annual total / average. | 55–58 |
| Index | Values relative to a base period or element = 100 %. | 57, 60 |
| Remainder | "Other", "Rest of …", "RoW": makes a structure exhaustive; shown last after a gap. | 92, 113 |
| MECE | Mutually exclusive, collectively exhaustive. | 89–91 |
| Adjustment | Recalculating a scenario to neutralise currency, inflation or seasonal effects (AC*). | 61 |

## Markers and chart forms

| Term | Meaning | p. |
|---|---|---|
| Scenario triangle | Small triangle in the reference scenario's notation at the reference value. | 50 |
| Pin | Very thin column/bar with a head; used for relative variances. | 54 |
| Highlighting ellipse | Blue ellipse around the value the message refers to. | 64 |
| Difference marker | Bar between two parallel assisting lines showing a difference, in impact colour. | 62 |
| Trend arrow | Arrow from first to last period of a trend, optionally with CAGR. | 63 |
| Reference arrowhead | Black triangle marking an index (100 %) or a benchmark. | 65 |
| Scale band | Light area up to the same value in charts with different scales. | 66–67 |
| Outlier marker | Marks a value beyond the visible scale (e.g. headless pin + triangle). | 67 |
| Magnifying glass | A marked region linked to a zoomed chart. | 74 |
| Horizontal / vertical chart | Named after the **category axis**: horizontal = columns over time; vertical = bars by structure. | 99, 107 |
| Waterfall | Base and total with contributions in between: column, growth, variance, calculation waterfall. | 103–112 |
| Overlay / multi-tier / extended chart | Combined charts: on top of each other / tiers along the category axis / extra category on an extended axis. | 146–151 |
| Small multiples | Charts of one type and one scale, up to about 25 plus "Others". | 153–154 |
| Ratio tree | Related charts arranged as a calculation tree, usually left → right. | 155–156 |
| Table bar / sparkline | Bar chart aligned to table rows / small line in a cell (only properly scaled). | 152 |
