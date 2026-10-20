# Template reference

Generated from each template's `usermeta.ibcs` by `scripts/gen_reference.py`; edit the templates, not this file.
Paths are relative to this skill's directory.

## Contents
- [bar-structure-variance](#bar-structure-variance)
- [column-two-tier-variance](#column-two-tier-variance)
- [column-version-axis](#column-version-axis)
- [line-scenarios](#line-scenarios)
- [pin-relative-variance](#pin-relative-variance)
- [scatter-relative](#scatter-relative)
- [small-multiples-columns](#small-multiples-columns)
- [stacked-columns](#stacked-columns)
- [waterfall-calculation](#waterfall-calculation)
- [waterfall-variance](#waterfall-variance)

## bar-structure-variance

IBCS vertical two-tier bar chart (EX 4.2, CO 4.2, UN 4.1): structure on the vertical axis, AC bars with the reference scenario as down-pointing triangles (or an overlapped bar behind, shifted up), absolute variance bars ΔPL / ΔPY to the right on the SAME scale, variance axis in the reference notation.

- IBCS: EX 1.1 cards 23, 24, 25, EX 4.2, CO 4.2-2
- Sample data: `assets/sample-data/structure-ac-py-pl.json`

| Field | Meaning |
|---|---|
| `Category` | text, structure element (row); sort the visual as the analysis needs (e.g. AC descending) |
| `AC` | measure, actual (or FC for a forecast analysis: set minuend to 'FC') |
| `FC` | optional measure, forecast: bind it and set minuend to 'FC' for a forecast analysis (hatched bars) |
| `PY` | measure, previous year (refScenario 'PY') |
| `PL` | measure, plan/budget (refScenario 'PL'); any other code works the same way, e.g. BU: bind it under that name and set refScenario = 'BU' (plan notation: outlined) |
| `Polarity` | optional measure 1 / -1 / 0 per row; else the polarity knob |
| `BU` | measure, budget (refScenario or triangleScenario 'BU'); plan notation like PL |
| `XMax` | optional measure, same value on every row: right end of the base tier (measures' unit); wins over xMax |
| `VarMin` | optional measure: lowest variance the tier must show (≤ 0); wins over varMin |
| `VarMax` | optional measure: highest variance the tier must show (≥ 0); wins over varMax |
| `PxPerUnit` | optional measure, same value on every row: px per display unit for the page's scale group; wins over pxPerUnit |
| `ScaleBand` | optional measure, same value on every row: scale band value in data units (before unitDivisor); wins over scaleBand |

Required fields: `Category`; the scenario fields that refScenario, minuend, triangleScenario name; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `refScenario` | `"PL"` | reference scenario: 'PY' or a plan code such as 'PL' or 'BU' (any code except PY gets the plan notation); the field of that name must be bound |
| `decimals` | `0` | decimals for value and absolute-variance labels (the token formats with this precision); IBCS: at most 3 digits in charts |
| `refMark` | `"triangle"` | 'triangle' (card 24) or 'bar' (overlapped reference bar behind, card 23) |
| `minuend` | `"AC"` | 'AC' (solid) or 'FC' (hatched bars and hatched variance bars) |
| `polarity` | `1` | used when the Polarity field is absent |
| `stepScale` | `1.5` | screen scaling of the token row step; keep identical on every page |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `xMax` | `0` | right end of the base tier in display units (after unitDivisor); 0 = from the data. A shared DOMAIN, not a shared scale: same xMax gives the same px per unit only on visuals of the same width. For a same-unit scale group use pxPerUnit instead |
| `varMin` | `0` | lowest value of the variance tier (≤ 0); 0 = from the data |
| `varMax` | `0` | highest value of the variance tier (≥ 0); 0 = from the data |
| `pxPerUnit` | `0` | px per display unit (after unitDivisor) on the value axis; 0 = off. When set, the value domain is the plot extent ÷ pxPerUnit, anchored at the baseline, so values render at exactly this px per unit. The container must then be sized to the data (usermeta.ibcs.layout, scripts/scale_layout.py of the ibcs-power-bi skill): a chart with smaller values gets a smaller visual, never a larger empty domain (CH 4.1 + CH 4.2). If the container is too small, the data wins and the px per unit shrinks: nothing is cut |
| `triangleScenario` | `""` | a third scenario drawn as a down-pointing triangle above the bars when refMark is 'bar' (e.g. AC in front of BU, PY as triangle); its field must exist; '' = none |
| `showCategoryLabels` | `true` | false hides the category labels, e.g. for a tier stacked directly above another visual that already shows them |
| `scaleBand` | `0` | common positive scale-band value in display units (after unitDivisor); 0 = off; overridden by a positive ScaleBand field in data units |
| `ibcsTierGap` | `0.08` | gap between the tiers, as a share of the largest absolute base value (pxPerUnit = 0) |
| `ibcsLabelPx` | `40` | label room in px beyond a bar end, both tiers (pxPerUnit > 0; scripts/scale_layout.py sizes the container with it); the room grows to the widest value / variance label (character count × ibcsFontSize × ibcsCharWidth + 6 px). With pxPerUnit = 0 the room is the measured label width alone, so labels are never cut at the visual edge at any width |
| `ibcsCharWidth` | `0.6` | estimated width of one label character as a share of ibcsFontSize (Segoe UI digits ≈ 0.55–0.6); used to reserve label room |
| `ibcsTierGapPx` | `8` | gap between the tiers in px (pxPerUnit > 0 only; else ibcsTierGap) |

Notes: Same unit, same scale (CH 4.1) means the same px per unit: give every chart of a scale group the same pxPerUnit (or the PxPerUnit field) and size each visual's width to its own data (usermeta.ibcs.layout; scripts/scale_layout.py in the ibcs-power-bi skill). xMax, varMin, varMax only share a domain: use them for visuals of the same width that must show the same range. A Total row on another scale belongs in a separate visual with a scaling indicator or a footnote. Bind scaled measures or set unitDivisor so labels never show raw values. Rows with a blank Category or no value in AC, FC, PY, PL, BU, or the selected scenario fields are dropped; constant scale/polarity measures do not keep unknown members alive. Rows with any scenario value, including PY-only rows, remain. The base range includes negative values and reserves label room below zero; value labels sit outside the bar pair in the direction of the AC/FC value, in dark text. When a reference bar and a third-scenario triangle are both named, their top labels occupy separate vertical levels. Rounded-zero rule: a variance that rounds to 0 at `decimals` is labelled 0 without sign and gets no impact colour. Scale band (CH 4.3): when charts of one unit must use different scales, set scaleBand (display units, e.g. 10) to the same round value in each of them: a light area from the axis to that value and a labelled line make the scales comparable. 0 = off. Label room is measured from the label text (character count × ibcsFontSize × ibcsCharWidth + 6 px) for the value labels and for the variance labels on each side that has them, so a narrow visual shrinks the bars, never cuts a label; with pxPerUnit the room is at least ibcsLabelPx.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = width; fixed 37 px (38 px without category labels), plus the category labels: width of the longest category label in px + 6 (Vega measures the text; about 7 px per character at 12 px Segoe UI), at most categoryLabelLimitPx + 6: longer labels are cut with an ellipsis. Tiers: base = min(AC/FC, reference, triangle scenario, 0) … max(AC/FC, reference, triangle scenario, xMax/XMax, scaleBand, 0) (padHigh `ibcsLabelPx` + `ibcsTierGapPx`; padLowIfNegative `ibcsLabelPx`); variance = min(Δ, 0) … max(Δ, 0) (padHigh `ibcsLabelPx`; padLowIfNegative `ibcsLabelPx`). container width = fixedPx + category labels + Σ over tiers of ((hi − lo) × pxPerUnit + padHigh + padLow); measured with Vega-Lite 6.4.3 at ibcsFontSize 12.

## column-two-tier-variance

IBCS two-tier column chart (CO 4.2, UN 4.1): AC/FC columns with the reference scenario (PY or PL) overlapped behind and offset left, absolute variance tier above on the SAME value scale, variance axis in the reference scenario's notation. Options: pinTier adds the relative variance as pins in a third tier on their own % scale (card 8), showBase false draws the variance tier alone.

- IBCS: EX 1.1 card 5, EX 1.1 card 7, EX 1.1 card 8, CO 4.2
- Sample data: `assets/sample-data/time-series-ac-fc-py-pl.json`

| Field | Meaning |
|---|---|
| `Period` | text, category axis label (e.g. Jan); use YYYY-MM for periodLabel 'month' or 'short'; sort the visual by period ascending |
| `AC` | measure, actual; BLANK for periods without actuals |
| `FC` | measure, forecast; BLANK for periods with actuals (optional) |
| `PY` | measure, previous year (needed when refScenario = 'PY') |
| `PL` | measure, plan/budget (needed when refScenario = 'PL'); any other code works the same way, e.g. BU: bind the field under that name and set refScenario = 'BU' (every code except PY gets the plan notation: outlined column, two-line axis) |
| `Polarity` | optional measure: 1 higher is better, -1 lower is better, 0 neutral; else the polarity knob |
| `BU` | measure, budget (refScenario or triangleScenario 'BU'); plan notation like PL |
| `YMax` | optional measure, same value on every row: upper end of the base tier in the measures' unit (before unitDivisor); wins over the yMax knob |
| `VarMin` | optional measure: lowest variance the tier must show (≤ 0); wins over varMin |
| `VarMax` | optional measure: highest variance the tier must show (≥ 0); wins over varMax |
| `PxPerUnit` | optional measure, same value on every row: px per display unit for the page's scale group; wins over pxPerUnit |
| `ScaleBand` | optional measure, same value on every row: scale band value in data units (before unitDivisor); wins over scaleBand |
| `Comment` | optional text/number per row: comment number shown in a circle above that period (blank = none) |

Required fields: `Period`; the scenario fields that refScenario, triangleScenario name; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `refScenario` | `"PY"` | reference scenario (subtrahend): 'PY' (solid light) or a plan code such as 'PL' or 'BU' (any code except PY gets the plan notation: outlined column, two-line variance axis); the field of that name must be bound |
| `decimals` | `1` | decimals for value and absolute-variance labels (the token formats with this precision); IBCS: at most 3 digits in charts |
| `polarity` | `1` | used when the Polarity field is absent: 1, -1 or 0 |
| `periodType` | `"month"` | year \| quarter \| month \| week \| day: category width per period type (UN 3.3) |
| `periodLabel` | `"auto"` | auto = unchanged category labels; month = YYYY-MM as Jan..Dec with a second line naming the year under its first visible month and a thin year separator; short = YYYY-MM as mm. Other category formats stay unchanged; showCategoryLabels hides both label lines and year separators. |
| `stepScale` | `1.5` | screen scaling of the token category step; keep it identical on every page |
| `barPx` | `0` | column width in px; 0 = 2/3 of the category slot. Set the same value in every visual of one period type on a page (e.g. 2/3 of the month slot) so their columns have the same width |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `yMax` | `0` | upper end of the base tier in display units (after unitDivisor); 0 = from the data. A shared DOMAIN, not a shared scale: same yMax gives the same px per unit only on visuals of the same height. For a same-unit scale group use pxPerUnit instead (CH 4.2: a chart with smaller values gets a shorter plot, never a taller empty domain). The larger of knob and data wins, so nothing is ever cut |
| `varMin` | `0` | lowest value of the variance tier (≤ 0); 0 = from the data |
| `varMax` | `0` | highest value of the variance tier (≥ 0); 0 = from the data |
| `pxPerUnit` | `0` | px per display unit (after unitDivisor) on the value axis; 0 = off. When set, the value domain is the plot extent ÷ pxPerUnit, anchored at the baseline, so values render at exactly this px per unit. The container must then be sized to the data (usermeta.ibcs.layout, scripts/scale_layout.py of the ibcs-power-bi skill): a chart with smaller values gets a smaller visual, never a larger empty domain (CH 4.1 + CH 4.2). If the container is too small, the data wins and the px per unit shrinks: nothing is cut |
| `varPxPerUnit` | `0` | px per display unit for the variance tier only; 0 = the same as pxPerUnit. Use it on a Total / extension visual whose base tier has its own scale while its variance tier keeps the months' px per unit (needs pxPerUnit > 0). Labels still show the true variance. |
| `triangleScenario` | `""` | a third scenario drawn as a triangle at its value (e.g. 'PY' when refScenario is 'BU' or 'PL'); its field must exist; '' = none. PY solid light, AC solid dark, any other code outlined (plan notation) |
| `showCategoryLabels` | `true` | false hides the category labels, e.g. for a tier stacked directly above another visual that already shows them |
| `scaleBand` | `0` | scale band (CH 4.3) in display units: a light area from the axis to this value and a labelled line, the same round value in every chart of the unit whose scales differ; 0 = off (field ScaleBand wins) |
| `fcLabel` | `"FC"` | integrated-legend name of the hatched (forecast) columns: 'FC' for forecast months; 'AC&FC' on a Total / extension visual whose column is the year of actual plus forecast (bind that measure as FC so it is hatched) |
| `legendSide` | `"end"` | where the integrated scenario legend sits: 'end' = right of the last column, each name at its own mark (triangle, reference, AC/FC), spread so names never overlap; a series of AC then FC months is named AC&FC there; 'start' = AC and the reference left of the first column, FC right of the last (previous behaviour) |
| `showBase` | `true` | false draws only the variance tier: no base columns, value labels, scenario legend, triangles, comment markers, scale band or category axis line. Use it for a second variance tier (e.g. ΔPY above an AC vs BU chart that already shows ΔBU) so the base is not drawn twice; with pinTier the visual is a ΔX + ΔX% pair |
| `pinTier` | `false` | true adds the relative variance (ΔX% = (AC&FC − REF) / REF, signed reference) as pins in a third tier above the absolute variance tier, in the same view, so all tiers move together under filtering and share one category axis (CO 4.2). The pins have their own % scale (pinPxPerUnit) |
| `pinPxPerUnit` | `0` | px per percentage point of the pin tier; set the same value on every pin tier and pin-relative-variance chart of the page (one % scale). Needs pxPerUnit > 0; 0 (or pxPerUnit 0) = the pin tier gets pinShare of the base tier's extent |
| `pinShare` | `0.5` | without pinPxPerUnit: extent of the pin tier as a share of the base tier (of the variance tier with showBase false) |
| `pinDecimals` | `0` | decimals of the pin labels (percent) |
| `naOnNegativeRef` | `true` | pin tier: N/A when the reference is negative (IBCS UN 4.1); a zero or blank reference is always N/A |
| `ibcsLabelPad` | `0.13` | label room, as a share of the largest value (pxPerUnit = 0) |
| `ibcsTierGap` | `0.06` | gap between the tiers, as a share of the largest value (pxPerUnit = 0) |
| `ibcsLabelPx` | `18` | label room in px beyond a bar end (pxPerUnit > 0 only; else ibcsLabelPad) |
| `ibcsTierGapPx` | `8` | gap between the tiers in px (pxPerUnit > 0 only; else ibcsTierGap) |

Notes: Same unit, same scale (CH 4.1) means the same px per unit, not the same domain: give every chart of a scale group the same pxPerUnit (or the PxPerUnit field from one DAX measure) and size each visual's height to its own data (usermeta.ibcs.layout; scripts/scale_layout.py in the ibcs-power-bi skill computes it), so a chart with smaller values is shorter (CH 4.2). yMax, varMin, varMax only share a domain: use them for visuals of the same height that must show the same range, never to align a smaller chart with a larger one. A Total / extension column (e.g. the year next to its months) is a separate visual with periodType 'year'; when its values need another scale, mark it with a scaling indicator or a footnote. Same column width across visuals (e.g. the month chart and its total): set barPx. Values are drawn as delivered: bind scaled measures or set unitDivisor so labels never show raw values. Rows with a blank Period or no value in AC, FC, PY, PL, BU, refScenario or triangleScenario are dropped, even if constant scale measures are present; reference-only periods remain. The integrated reference legend names the first period with a nonblank reference value, including zero. periodLabel: auto preserves category labels unchanged; month formats YYYY-MM as Jan..Dec with the year below the first visible month of each year and a thin separator at subsequent year boundaries; short formats YYYY-MM as mm. Other category formats are left unchanged. When showCategoryLabels is false, year labels and year separators are hidden too. Rounded-zero rule: a variance that rounds to 0 at `decimals` is labelled 0 without sign and gets no impact colour. Scale band (CH 4.3): when charts of one unit must use different scales, set scaleBand (display units, e.g. 10) to the same round value in each of them: a light area from the axis to that value and a labelled line make the scales comparable. 0 = off. Comment markers (UN 2.4): bind Comment (e.g. a DAX SWITCH returning 1, 2 … for the periods the comments explain) and print the same numbers in circles in the comment text box; the marker sits above the value label, so keep ibcsTierGapPx large enough when a variance tier is stacked above. Variance-only tier (showBase false): only the variance axis, variance columns and labels and the tier label are drawn; stack it above a chart that shows the base, with showCategoryLabels false when the visual below shows them. Pin tier (pinTier true): ΔX% = (AC&FC − REF) / REF with the signed reference, N/A when REF is blank or 0, or negative while naOnNegativeRef is true; drawn as pins above the absolute variance tier in the same view, so base, ΔX and ΔX% always share the category axis and stay together when a filter changes the data (separate stacked visuals each anchor their own plot and drift apart). The pins have their own % scale: pinPxPerUnit px per percentage point (the same on every pin tier and pin chart of the page), else pinShare of the base tier. Outlier clipping (clipPct) exists only in pin-relative-variance. Integrated legend (legendSide, default 'end'): the scenario names sit right of the last column at their own marks (triangle tip, upper part of the reference column, middle of the AC/FC column), spread at least ibcsFontSize + 2 px apart and kept inside the base tier; a series of AC months followed by FC months is named AC&FC; the right padding (46 px) holds 'AC&FC'. legendSide 'start' keeps AC and the reference left of the first column and FC right of the last. Names are taken from the last row: a scenario without a value in the last period is not named.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = height; fixed 24 px (10 px without category labels). Tiers: base = 0 … max(AC/FC, reference, triangle scenario, scaleBand) (padHigh `ibcsLabelPx` + `ibcsTierGapPx`); variance = min(Δ, 0) … max(Δ, 0) (padHigh `ibcsLabelPx`; padLowIfNegative `ibcsLabelPx`); pins = min(Δ%, 0) … max(Δ%, 0) in percentage points (padHigh `ibcsLabelPx`; padLow `ibcsTierGapPx` + `ibcsLabelPx`). container height = fixedPx + Σ over tiers of ((hi − lo) × pxPerUnit + padHigh + padLow); measured with Vega-Lite 6.4.3 at ibcsFontSize 12; with varPxPerUnit the variance tier contributes (hi − lo) × varPxPerUnit instead (scale_layout.py: member tierPxPerUnit); with Comment markers add ibcsFontSize + 18 px to the base tier's padHigh; periodLabel 'month' with visible category labels uses fixedPxMonthLabels instead of fixedPx for the second label line (at ibcsFontSize 12); tiers with onlyIf count only when that knob is true (showBase false drops the base tier and its padHigh; pinTier true adds the pin tier at pinPxPerUnit px per percentage point); with pxPerUnit the space the data does not need stays ABOVE the top tier, so the tiers never drift apart when a filter shrinks the data.

## column-version-axis

IBCS scenario columns on a version axis (forecast evolution): each version is a full-period value, with absolute deltas above on the SAME linear scale (CO 4.2, UN 4.1). Reference axis notation is local to each subtrahend.

- IBCS: EX 1.1 card 1, EX 1.1 card 7, CO 4.2, UN 4.1
- Sample data: `assets/sample-data/column-version-axis.json`

| Field | Meaning |
|---|---|
| `Version` | text, unique version label: e.g. PY, BU, FC Jan, FC Feb, AC. One full-period value per version; blank/null/whitespace categories are dropped before ordering or window calculations. |
| `VersionOrder` | optional numeric column, ascending chronology; bind on every row or omit entirely to keep query order. Ties keep query order. The final AC must sort last; no alphabetical sort is imposed. |
| `Scenario` | text, AC \| FC \| PL \| BU \| PY per version: AC solid dark, FC hatched, PL/BU outlined, PY solid light. Scenario is independent of the Version label. |
| `Value` | measure, full-period value of that version; raw values are divided by unitDivisor before drawing and labelling. BLANK stays in the version sequence, gets no column, and invalidates deltas that use it. |
| `Polarity` | optional measure: 1 higher is better, -1 lower is better, 0 neutral blue; wins over the polarity knob per minuend row. Colour only; direction always follows the arithmetic sign. |
| `PxPerUnit` | optional measure, same positive value on every row: px per display unit for the value axis of both tiers; wins over pxPerUnit. Size the container to the data using layout. |

Required fields: `Version`, `Scenario`, `Value`; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `deltaBase` | `"previous"` | 'previous' = value minus the immediately preceding version; 'first' = value minus the first version. The first version has no delta. Blank values stay in the sequence; never skip them to find a reference. |
| `polarity` | `1` | 1 higher is better, -1 lower is better, 0 neutral; an optional Polarity field wins per row. Polarity affects colour only, never arithmetic or geometry. |
| `decimals` | `1` | decimals for value and absolute-variance labels (the token formats with this precision); IBCS: at most 3 digits in charts |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `periodType` | `"month"` | year \| quarter \| month \| week \| day: category width per period type (UN 3.3) |
| `stepScale` | `1.5` | screen scaling of the token category step; keep it identical on every page |
| `barPx` | `0` | column width in px; 0 = 2/3 of the category slot. Set the same value in every visual of one period type on a page (e.g. 2/3 of the month slot) so their columns have the same width |
| `pxPerUnit` | `0` | Px per display unit (after unitDivisor), on the shared value axis of BOTH tiers; 0 = fit the data. The positive PxPerUnit field wins (one scale measure, same on every row). Size the container to the data using usermeta.ibcs.layout; if too small, data wins and px per unit shrinks so nothing is cut. |
| `showCategoryLabels` | `true` | false hides the category labels, e.g. for a tier stacked directly above another visual that already shows them |
| `labelPad` | `0.13` | Label room as a share of the larger tier range (pxPerUnit = 0). |
| `tierGap` | `0.06` | Gap between tiers as a share of the larger tier range (pxPerUnit = 0). |
| `labelPx` | `18` | Label room beyond each tier maximum and below negative minima, in px (pxPerUnit > 0). |
| `tierGapPx` | `8` | Gap between tiers in px (pxPerUnit > 0). |

Notes: Follows the IBCS® Standards. Values compare versions of ONE full period, not successive monthly amounts. deltaBase 'previous' subtracts the immediately preceding version (including a blank one); 'first' subtracts the first version, e.g. PL/BU. The first version has no delta. Absolute Δ = Value − reference remains valid for negative or zero references. Relative Δ% (tooltip only) = (Value − reference) / reference using the SIGNED reference, never ABS; reference <= 0 or blank (or blank Value) gives null and the ibcsNA label, with no relative mark. Variance-axis segments use the subtrahend's Scenario: PL/BU two thin lines, PY solid light, FC/AC one thin line without hatch. The minuend's Scenario determines FC hatch on delta bars. A delta rounding to 0 at decimals gets no colour, no hatch and a signless zero label. Polarity changes colour only. Values and deltas share one view and one scale, including negative values. Set the same pxPerUnit on all members of a scale group and size each visual to its own ranges (layout; scale_layout.py in the ibcs-power-bi skill); a too-small container lets data win. Unit goes in the title. Use the synced Deneb config for font family and number locale; SVG render mode for pbiPatternSVG. One unique Version per row is required; aggregate duplicates upstream. No multi-period grouping or automatic placement of AC; query order / VersionOrder must express the desired chronology. Labels do not automatically de-overlap. Render-checked outside Power BI; not yet verified in Desktop. Columns fill 2/3 of their slot; same column width across visuals (e.g. the month chart and its total): set barPx.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = height; fixed 24 px (12 px without category labels). Tiers: base = min(Value / unitDivisor, 0) … max(Value / unitDivisor, 0) (padHigh `labelPx` + `tierGapPx`; padLowIfNegative `labelPx`); variance = min(Δ, 0) … max(Δ, 0), in display units for deltaBase (padHigh `labelPx`; padLowIfNegative `labelPx`). container height = fixedPx + Σ tiers ((hi − lo) × pxPerUnit + padHigh + padLowIfNegative when lo < 0); one shared value axis, anchored at the signed base minimum with label room. Measured with Vega-Lite 6.4.3 at ibcsFontSize 12; recompute variance range when deltaBase changes..

## line-scenarios

IBCS line chart with scenario notation (EX 1.1 cards 12 and 15, UN 3.2): one continuous AC&FC line with filled dark square markers for AC and HATCHED markers for FC; PY light grey line with light markers; Plan (planLabel, default PL) dark line with HOLLOW (outlined) markers. Line thickness encodes the measure type (absolute = thick), not the scenario. Scenario names and values paired at the line ends with a minimum vertical gap; other primary values labelled above peaks and below valleys. Optional pxPerUnit joins a shared scale group.

- IBCS: EX 1.1 card 12, EX 1.1 card 15, UN 3.2, UN 5.1 trend arrow
- Sample data: `assets/sample-data/line-12-months.json`

| Field | Meaning |
|---|---|
| `Period` | text, category label; sort by period ascending |
| `AC` | measure, actual |
| `FC` | measure, forecast (optional; continues the AC line) |
| `PY` | measure, previous year (optional, shown when showPY) |
| `PL` | measure, plan/budget (optional, shown when showPL); bind the plan measure as PL and set planLabel for its displayed name |

Required fields: `Period`; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `showPY` | `true` | draw the PY line (solid light) when PY is bound |
| `showPL` | `true` | draw the plan line (outlined markers, named by planLabel) when PL is bound |
| `planLabel` | `"PL"` | Displayed name of the plan measure bound as PL, e.g. BU; used in the line-end label, tooltip and notation footnote. Plan markers remain hollow/outlined. |
| `measureType` | `"absolute"` | 'absolute' (thick line) or 'relative' (thin line) |
| `decimals` | `0` | decimals for labels and tooltips (absolute: number format; relative: % format); IBCS: at most 3 digits in charts |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `pxPerUnit` | `0` | Pixels per display unit after unitDivisor (per fraction for relative measures); 0 = fit. Use the same positive value on a scale group and size each container from usermeta.ibcs.layout. A too-small container lets the data win and reduces the actual pixels per unit. |
| `trendArrow` | `false` | draw a trend arrow (UN 5.1) from the first to the last value above the lines, coloured by polarity |
| `trendLabel` | `""` | '' hides the label; delta = relative change for absolute measures, arithmetic pp change for relative measures; cagr = CAGR for absolute measures, pp delta fallback for relative measures. |
| `polarity` | `1` | 1 higher is better, -1 lower is better, 0 neutral (blue): impact colour only, never the direction (a Polarity field per row wins where the template reads one) |
| `trendLiftPx` | `0` | extra px between the highest point and the trend arrow |

Notes: Follows the IBCS® Standards. planLabel names the measure bound as PL in the end label, tooltip and notation footnote; its markers stay hollow/outlined. For a relative measure (%, ratio) set measureType = 'relative': thin lines and % labels/tooltips (fractions, 0.42 = 42%). More than three crossing lines: use small multiples (EX 2.4). Blank Period rows and rows with AC, FC, PY and PL all null are dropped before ordering; a PY-only or PL-only row remains. End labels pair each scenario name with its last value in a shared right-hand column, separated by at least ibcsFontSize + 4 px; the last primary value is omitted from the peak/valley labels. pxPerUnit is pixels per display unit after unitDivisor (also per fraction for relative measures); 0 fits the data. For a scale group use the same positive pxPerUnit and size each container to its data range using layout; if too small, data wins and the actual scale shrinks. Trend arrow (UN 5.1): from the first to the last valid AC&FC value, parallel to the arithmetic change, lifted above all visible series. Polarity chooses colour only (1 / -1 / 0 = higher better / lower better / neutral). For absolute measures, 'delta' is relative change on the signed start (N/A when start <= 0 or blank); 'cagr' uses period steps (only meaningful for years; N/A unless both ends > 0). For relative measures, both 'delta' and 'cagr' show the arithmetic change in percentage points (pp), including zero/negative starts; CAGR falls back to pp delta. A trend rounding to zero at the displayed precision is unsigned and uncoloured. Raise trendLiftPx if needed. Render-checked outside Power BI; not verified in Desktop.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = height; fixed 46 px. Tiers: base = min(0, visible AC/FC/PY/PL divided by unitDivisor) … max(0, visible AC/FC/PY/PL divided by unitDivisor); with trendArrow use the envelope described in rule (padHigh `ibcsFontSize`; padLow `ibcsFontSize`). At ibcsFontSize 12 with the plan footnote visible: container height = 46 + (hi - lo) * pxPerUnit + 2 * ibcsFontSize. Without the plan footnote (showPL false or no PL bound) subtract 24 px: fixedPxNoPlanFootnote; scale_layout.py uses it for a member with "planFootnote": false or params showPL false. Deneb uses a fixed container: size it from this data range, then the y domain spans plot height / pxPerUnit, with label padding in data units. A too-small container lets data win. With trendArrow and at least two primary values, let v0/v1 be its endpoints, e = max(0, max(visible row maximum - interpolated primary trend)); hi = max(base hi, max(v0,v1) + e + (ibcsFontSize + 10 + trendLiftPx + (trendLabel is nonempty ? ibcsFontSize + 10 : 4)) / pxPerUnit). Minimum plot height for three stacked end labels is 3 * (ibcsFontSize + 4). Recompute the fixed overhead for changed fonts..

## pin-relative-variance

IBCS horizontal pin chart (EX 1.1 card 8, UN 4.1): relative variance ΔPY% / ΔPL% per period as thin pins with square heads (AC solid, FC hatched), colour = impact (good / bad / neutral), variance axis in the reference scenario's notation, N/A where the relative variance cannot be interpreted.

- IBCS: EX 1.1 card 8, UN 4.1 relative variances
- Sample data: `assets/sample-data/time-series-ac-fc-py-pl.json`

| Field | Meaning |
|---|---|
| `Period` | text, category label; sort the visual by period ascending |
| `AC` | measure, actual; BLANK where there is no actual |
| `FC` | measure, forecast (optional) |
| `PY` | measure, previous year (refScenario 'PY') |
| `PL` | measure, plan/budget (refScenario 'PL'); any other code works the same way, e.g. BU: bind it under that name and set refScenario = 'BU' (plan notation: two-line axis) |
| `Polarity` | optional measure 1 / -1 / 0; else the polarity knob |
| `BU` | measure, budget (refScenario 'BU'); plan notation like PL |
| `YMin` | optional measure (fraction, ≤ 0), same on every row: lowest Δ% the axis must show; wins over yMin |
| `YMax` | optional measure (fraction, ≥ 0): highest Δ% the axis must show; wins over yMax |
| `PxPerUnit` | optional measure, same value on every row: px per percentage point for the page's Δ% scale group; wins over pxPerUnit |
| `ClipPct` | optional measure (fraction > 0), same on every row: \|Δ%\| beyond which a pin is an outlier; wins over clipPct |

Required fields: `Period`; the scenario fields that refScenario name; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `refScenario` | `"PY"` | reference scenario: 'PY' or a plan code such as 'PL' or 'BU' (any code except PY gets the two-line plan axis); the field of that name must be bound |
| `decimals` | `0` | decimals for the relative-variance labels (the token format with this precision); IBCS: at most 3 digits in charts |
| `polarity` | `1` | used when the Polarity field is absent: 1, -1 or 0. Overridden per row by a Polarity field. |
| `periodType` | `"month"` | year \| quarter \| month \| week \| day: category width per period type (UN 3.3) |
| `stepScale` | `1.5` | screen scaling of the token category step; keep it identical on every page |
| `yMin` | `0` | lowest relative variance the scale must show, as a fraction (-0.3 = -30%); 0 = from the data |
| `yMax` | `0` | highest relative variance as a fraction (0.3 = +30%); 0 = from the data. A shared DOMAIN: same yMin/yMax gives the same % scale only on pin charts of the same height. For the page's Δ% scale group use pxPerUnit instead |
| `pxPerUnit` | `0` | px per percentage point (1% = 0.01) on the value axis; 0 = off. When set, the domain is the plot height ÷ pxPerUnit, anchored at the lowest pin (plus label room), so every pin chart of the page shows the same px per % point. Size the container to the data (usermeta.ibcs.layout, scripts/scale_layout.py of the ibcs-power-bi skill). If the container is too small, the data wins and the px per point shrinks: nothing is cut |
| `showCategoryLabels` | `true` | false hides the category labels, e.g. for a tier stacked directly above another visual that already shows them |
| `clipPct` | `0` | relative outlier cut (UN 5.3, CH 4.4) as a fraction, e.g. 0.5 = 50%: pins beyond it are cut, have no head, keep their full label and get a growth triangle; 0 = off (field ClipPct wins) |
| `naOnNegativeRef` | `true` | show N/A when the reference is negative |
| `ibcsLabelPad` | `0.3` | label room beyond the longest pin, as a share of it (pxPerUnit = 0) |
| `ibcsLabelPx` | `18` | label room in px beyond a pin head, both directions (pxPerUnit > 0 only; else ibcsLabelPad) |

Notes: ΔX% = (AC-REF)/REF with the SIGNED reference (never ABS). N/A when REF is blank or 0, or when REF < 0 and naOnNegativeRef is true (IBCS UN 4.1 p.54). If you pass a precomputed ΔPY% measure instead, keep the same rule in DAX. Same % scale on the page: the same pxPerUnit (px per percentage point) on every pin chart and each visual's height sized to its own Δ% range (usermeta.ibcs.layout), not the same yMin/yMax on visuals of one height. Rows with a blank Period are dropped (a constant measure such as a scale field would otherwise add a blank category). Rounded-zero rule: a variance that rounds to 0 at `decimals` is labelled 0 without sign and gets no impact colour. Outliers (UN 5.3, CH 4.4): set clipPct (fraction, e.g. 0.5 = 50%) or bind ClipPct for business-irrelevant relative outliers: the pin is cut at that value, has no head, keeps its full label, and a small triangle beyond the label points in the growth direction. Only for relative variances; never cut absolute columns or bars (CH 2.1).

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = height; fixed 24 px (12 px without category labels). Tiers: pins = min(Δ%, 0) … max(Δ%, 0) in percentage points (padHigh `ibcsLabelPx`; padLow `ibcsLabelPx`). container height = fixedPx + (hi − lo) × pxPerUnit + padHigh + padLow; measured with Vega-Lite 6.4.3 at ibcsFontSize 12 ; with an outlier (clipPct) add ibcsFontSize + ibcsPinHeadMax + 6 px to padHigh and padLow (the triangle beyond the label).

## scatter-relative

IBCS scatter of two supplied relative measures (G5 / portfolio; cards 32, 33), with one percentage scale on both axes, zero-crossing axes, a 45-degree diagonal and a tolerance band. Follows the IBCS® Standards.

- IBCS: G5, EX 1.1 card 32, EX 1.1 card 33, UN 4.1, CH 4.1
- Sample data: `assets/sample-data/scatter-relative.json`

| Field | Meaning |
|---|---|
| `Element` | text, element name; blank/null/whitespace categories are dropped by the first transform. Rows with X, Y and Size all blank/null are also dropped; constant control measures do not keep them. |
| `X` | measure, relative measure 1; fraction by default (0.05 = 5%). Compute upstream as (AC - REF) / REF using the SIGNED reference; return BLANK/null when REF <= 0 or blank. No raw reference fields are needed. |
| `Y` | measure, relative measure 2, same input units as X and same signed-reference/N/A rule. A blank or nonnumeric X or Y drops the point and contributes once to the n not shown note. |
| `Size` | optional non-negative measure, proportional bubble AREA; missing/negative/nonnumeric uses a fixed dot. Zero has zero bubble area; maximum area is sizeMaxPx square pixels. Also ranks labels when labelTop > 0. |
| `Polarity` | optional measure 1/-1/0, wins over polarity: impact colour of y - x only in colourMode = polarity; never changes coordinates. Zero stays neutral. |
| `Scenario` | optional text AC (default), FC (hatched), PY (solid light), PL/BU (outlined). Inside-band points use muted grey tokens; outside-band scenario fills are preserved, with any polarity colour on non-AC outlines. |
| `PxPerUnit` | optional positive measure, same value on every row: pixels per displayed percentage point on both axes; wins over pxPerPoint and pxPerUnit. If inconsistent, the largest value is used. |
| `XRef` | optional provenance only, present in the sample to demonstrate negative/zero/blank references; not read by this template. X must already be BLANK/null when its reference is not positive. |
| `YRef` | optional provenance only; not read by this template. Y must already be BLANK/null when its reference is not positive. |

Required fields: `Element`, `X`, `Y`; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `polarity` | `1` | Fallback impact polarity: 1 higher is better, -1 lower is better, 0 neutral; a row Polarity of 1/-1/0 wins. Changes colour only, never X/Y geometry. |
| `decimals` | `0` | Decimal places for percentage axes, percentage tooltips and Size labels; a y - x difference rounding to zero percentage points has no impact colour. |
| `unitDivisor` | `1` | Positive divisor for X and Y before drawing and formatting: 1 for fractions (0.05 = 5%, preferred), 100 for inputs in percentage points (5 = 5%). Size is independent and is not divided. Tolerance and pixel scales always use displayed percentage points. |
| `tolerance` | `2` | Half-width of the diagonal band in displayed percentage points: abs(y - x) <= tolerance / 100. Non-negative; default 2 pp. This is a vertical/horizontal difference, not perpendicular distance. |
| `colourMode` | `"neutral"` | Point highlighting: 'neutral' (default) uses AC dark outside the tolerance band and muted grey inside. 'polarity' explicitly enables good/bad colour for outside-band y - x, using row Polarity or polarity. Polarity 0 and rounded-zero differences remain uncoloured; scenario fills are preserved. |
| `sizeMaxPx` | `600` | Maximum bubble area in square pixels (Vega symbol size), proportional to Size with a zero origin. Missing, negative or nonnumeric Size uses a fixed dot; Size = 0 has zero area. |
| `labelTop` | `0` | 0 labels every outside-band point; positive N labels the N largest outside-band Size values, ties broken by input order. Missing/invalid Size sorts last; if no outside-band Size exists, label all outside-band points. Nearby labels receive a vertical rank nudge. |
| `labelRoomPx` | `18` | Pixel room beyond data bounds on each side of the square, before fitting. At least the largest bubble radius is also reserved. Nearby labels receive a simple vertical rank nudge; dense clusters or long names can still need more room. |
| `pxPerPoint` | `0` | Pixels per displayed percentage point on BOTH axes; 0 derives the scale from the square plot. PxPerUnit wins, then pxPerPoint, then the pxPerUnit alias. Too-small containers reduce both scales together so data and point radii fit. |
| `pxPerUnit` | `0` | Compatibility alias for the scale-group convention: pixels per displayed percentage point. Used only when neither PxPerUnit nor pxPerPoint is positive; layout requires a square value plot. |
| `xTitle` | `"X (%)"` | Short name of relative measure 1, e.g. ΔPY%; rename for the bound measure. |
| `yTitle` | `"Y (%)"` | Short name of relative measure 2, e.g. ΔBU%; rename for the bound measure. |

Notes: X and Y are supplied relative measures, not raw actual/reference amounts. Compute (AC - REF) / REF upstream with the signed REF, never abs(REF), and return BLANK/null (N/A, no mark) for REF <= 0 or blank. After the blank-category filter, drop rows with X, Y and Size all blank/null, ignoring constant control measures. Retained rows missing either coordinate count once in the corner note, including rows with only one coordinate or Size; the note still renders when every retained row is N/A. Fractions are preferred; unitDivisor = 100 accepts percentage-point inputs. Both axes include zero explicitly, share the same symmetric linear domain and have a square physical range; rectangular containers add space around the square. The band is abs(y - x) <= tolerance pp, clipped to that square. Default colourMode = neutral highlights outside-band AC points in ibcsAC and mutes inside-band points with ibcsPY. Only explicit colourMode = polarity permits good/bad impact colours outside the band, using y - x and row Polarity or polarity; polarity 0 and differences rounding to zero at decimals remain uncoloured. Geometry never depends on polarity. FC hatch uses Deneb pbiPatternSVG and requires SVG render mode. Only outside-band points are labelled, subject to labelTop. Labels for nearby consecutive points in vertical order are spread vertically by rank away from the diagonal, with an extra nudge near the horizontal zero axis; this is a simple local nudge, not a general collision solver for dense clusters or long names. Size is an independent area measure and is not divided by unitDivisor. No Power BI Desktop validation is claimed.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = height; fixed 24 px. Tiers: portfolio = -max(abs(X / unitDivisor), abs(Y / unitDivisor), tolerance / 100, 0.01) … +max(...) on BOTH axes; includes 0 explicitly with zero: true (padHigh `labelRoomPx`; padLow `labelRoomPx`). Both axes use the same symmetric domain and a square range of side min(width, height) after Vega autosize fitting. For target p pixels per displayed percentage point, allow container width and height >= fixedPx + 200 * extent * p + 2 * max(labelRoomPx, sqrt(sizeMaxPx) / 2 + ibcsOutline), where extent is max(abs(X / unitDivisor), abs(Y / unitDivisor), tolerance / 100, 0.01). fixedPx = 24 conservatively covers container padding and tick-label overhang at ibcsFontSize = 12. PxPerUnit > pxPerPoint > pxPerUnit; absent a target, derive p from the container. If the target cannot fit, reduce both scales together. This square layout needs explicit container sizing; the generic one-axis scale_layout.py does not compute portfolio bounds..

## small-multiples-columns

IBCS small multiples (CO 5.1, CH 4.1): one column chart per structure element, all on the identical value scale (shared y), AC solid / FC hatched with the reference scenario overlapped behind. Data-driven panel dimensions, period-qualified end labels, and selective scenario-labelled totals.

- IBCS: CO 5.1, CH 4.1, EX 1.1 card 5
- Sample data: `assets/sample-data/small-multiples.json`

| Field | Meaning |
|---|---|
| `Panel` | text, structure element per panel (≤ 25 panels; aggregate the rest into an 'Others' panel in DAX) |
| `Period` | text, category label; supply rows in period order within each panel; month1 uses the first letter of this label |
| `AC` | measure, actual |
| `FC` | measure, forecast (optional) |
| `PY` | measure (refScenario 'PY') |
| `PL` | measure (refScenario 'PL') |
| `BU` | measure (refScenario 'BU'): budget, outlined like PL |
| `PxPerUnit` | optional measure, same positive value on every populated row: px per display unit for the scale group; overrides pxPerUnit and sizes panel plots automatically |
| `ShowTotal` | optional measure/column 1/0 (or true/false) per row: show this panel's total when panelTotals = 'field' |

Required fields: `Panel`, `Period`; the scenario fields that refScenario name; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `refScenario` | `"PY"` | reference scenario drawn behind the columns: PY (solid light) or PL / BU (outlined) |
| `decimals` | `0` | decimals of every value label (display units); also the precision of the rounded-zero rule |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `yMax` | `0` | 0 = from the data; a number fixes the panels' domain (shared DOMAIN: the same px per unit only at the same panel height). To share the page's scale group use pxPerUnit |
| `panelHeight` | `0` | Panel plot height in px; 0 = auto (70 with pxPerUnit off; data range × effective pxPerUnit + ibcsLabelPx with it on). With pxPerUnit on, a positive value is a minimum height; data and label room win if taller. |
| `panelWidth` | `0` | Panel plot width in px; 0 = auto: max(150, distinct Period count × ibcsCategoryStep[periodType] × stepScale). A positive value fixes the width. |
| `periodLabel` | `"auto"` | auto = full labels, or first letters for crowded month panels; month1 = first letter of each Period (J F M … for month names); none = hide period labels. |
| `pxPerUnit` | `0` | Pixels per display unit after unitDivisor; 0 = off. A positive PxPerUnit field overrides this knob. Automatically sizes every panel plot from the displayed data range plus ibcsLabelPx, preserving the exact scale; panelHeight can add room without changing it. See usermeta.ibcs.layout for container sizing. |
| `ibcsLabelPx` | `16` | label room in px above the tallest column (pxPerUnit > 0 only) |
| `showGrid` | `false` | light gridlines are allowed in small multiples (SI 3.1) |
| `panelTotals` | `"none"` | none \| all \| field \| comma-separated panel names: selected panels show only their scenario-labelled total (AC, FC or AC&FC); other panels retain a period-qualified last-value label. |
| `stepScale` | `1.0` | screen scaling of the token category step; keep it identical on every page |
| `periodType` | `"month"` | year \| quarter \| month \| week \| day: column width per period type (UN 3.3) |

Notes: Never set resolve.scale.y to independent. All panels in this facet have the same plot height and shared y domain, using the maximum across the displayed panels. For an element that needs a different plot height at the same scale (CO 5.1), use a separate Deneb visual with the same pxPerUnit; its height now derives from its own data. panelHeight / panelWidth = 0 select automatic sizing; no spec.height edit is needed. Blank Panel/Period rows and rows with AC, FC, PY and PL all null are dropped, even when constant PxPerUnit/ShowTotal measures are present; reference-only and zero-valued rows remain. Facets fill left to right, then the next row, in first-appearance Panel order. Periods retain source order. periodLabel = auto keeps full labels when they fit and uses initials for crowded month panels; month1 always uses initials; none hides labels. Selective totals: panelTotals = none (default), all, field (any ShowTotal = 1 in that panel), or a comma-separated list of panel names. A selected panel shows only its AC, FC or AC&FC total; its last-value label is suppressed. Other panels show a period-qualified last value. Reference-only panel totals are N/A. Totals are labels, never extra columns; a year total next to months needs its own scale. Internal width/height expression params use the first transformed dataset (data_0 in the bundled Vega-Lite version); spec.name must remain an empty string so these built-in size params control the facet plots.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = panelHeight; fixed 0 px. Tiers: panel = 0 … max(AC/FC, selected reference) across all displayed panels; include negative minima when present (padHigh `ibcsLabelPx`). With pxPerUnit > 0 (or positive PxPerUnit field), auto panel plot height = (hi - lo) × effective pxPerUnit + ibcsLabelPx, where lo = min(0, data minimum), hi = max(0, data maximum) across all displayed panels after unitDivisor. For nonnegative data this is max data value × pxPerUnit + label room. panelHeight > 0 is a minimum plot height in this mode: extra height extends the domain at the same px per unit; a smaller height cannot compress the data. With pxPerUnit off, panelHeight > 0 is the fixed plot height, otherwise 70 px. panelWidth > 0 is the fixed plot width; otherwise max(150, distinct Period count × ibcsCategoryStep[periodType] × stepScale)..

## stacked-columns

IBCS stacked columns (D9, CO 1.1): periods on x, up to six ordered structure elements, scenario notation on the first segment, lighter grays above, inside segment values, net totals and an integrated end legend.

- IBCS: D9, CO 1.1, UN 3.2, EX 1.1 card 2
- Sample data: `assets/sample-data/stacked-columns.json`

| Field | Meaning |
|---|---|
| `Period` | text, period on the x axis; sort the visual by period ascending (query order is retained) |
| `Segment` | text, structure element; at most 6 across the visual, with one row per Period/Segment; aggregate the rest upstream |
| `SegmentOrder` | optional numeric field, consistent per Segment: ascending stack order, first element at zero; absent elements sort by Segment name after ordered elements |
| `Value` | measure, additive segment value; negative values stack below zero; zero has no mark, BLANK has no mark or segment label |
| `Scenario` | text, AC \| FC \| PY \| PL \| BU; identical on every row of a Period; only the first drawable ordered segment carries this notation |
| `PxPerUnit` | optional measure, same positive value on every row: px per display unit for the page scale group; wins over pxPerUnit |

Required fields: `Period`, `Segment`, `Value`; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `decimals` | `0` | label precision applied to ibcsFmtAbs; bind scaled measures so chart labels need at most 3 digits |
| `unitDivisor` | `1` | divides Value before drawing and labelling; 1 = already scaled measures, 1000 = thousands, 1000000 = millions; put the unit in the title |
| `periodType` | `"month"` | year \| quarter \| month \| week \| day: category width per period type (UN 3.3) |
| `stepScale` | `1.5` | screen scaling of the token category step; default 1.5 matches the other column templates; keep identical across the page |
| `barPx` | `0` | column width in px; 0 = 2/3 of the category slot. Set the same value in every visual of one period type on a page (e.g. 2/3 of the month slot) so their columns have the same width |
| `pxPerUnit` | `0` | px per display unit after unitDivisor; 0 = auto. A positive PxPerUnit field wins. Size the container to its own signed stack range using usermeta.ibcs.layout; if too small, the data wins and the scale shrinks |
| `minLabelPx` | `20` | minimum segment height in rendered pixels for an inside value label; the font height plus separators is also respected |
| `legendGapPx` | `16` | minimum vertical centre-to-centre gap in pixels between end-legend names; at least ibcsFontSize + 2 is always respected |
| `legendOffsetPx` | `18` | horizontal distance in pixels from the last column edge to the end of each legend leader; names start another 4 px to the right; minimum 4 px |
| `labelPad` | `0.13` | total-label room as a share of the signed data range when pxPerUnit = 0 |
| `labelPx` | `18` | total-label room in pixels when pxPerUnit > 0 |
| `showCategoryLabels` | `true` | false hides period labels, e.g. when another aligned visual already shows them |

Notes: Follows the IBCS® Standards. The first drawable structure element per period in the global SegmentOrder (or Segment name order) carries the column scenario in the stack: AC solid dark, PY light, PL/BU outlined, FC hatched. The five upper shades interpolate between the existing ibcsGray2 and ibcsAssistArea tokens; no independent palette. Thin white separators use ibcsBackground (the default page background). SegmentOrder and Scenario must be consistent; aggregate duplicate Period/Segment rows upstream. Negative segment values stack below the baseline independently of positives, in the same segment order (the first element remains at zero); totals are the signed net sum and sit above the positive stack, or below an all-negative stack. Null Value is omitted, not converted to zero; totals sum available values, and entirely blank periods are dropped. This composition template has no reference comparison, relative variance or polarity colours; the PY sample periods exercise negative, zero and null inputs without division. Rows with a blank Period or Segment, or no valid Value, are dropped; Scenario and PxPerUnit alone do not retain unknown members. FC inside labels have an ibcsBackground halo over the hatch. Inside labels need at least minLabelPx of actual rendered height; very narrow columns may need fewer decimals, scaled measures or a larger stepScale/container. The integrated legend connects the last period’s segment midpoints to names separated by at least max(legendGapPx, ibcsFontSize + 2) pixels; legendOffsetPx reserves horizontal leader room. Supply every segment in the last period; zero/blank segments there cannot be labelled. Reserve enough plot height for the legend names at this gap. One value scale spans both signs: equal pxPerUnit across visuals plus container heights sized to each visual's own signed stack range (CH 4.1/4.2); an undersized container shrinks the scale without clipping. stepScale defaults to 1.5, matching the other column templates; keep it identical across the page. Font family and number locale come from the synced Deneb config. SVG rendering is required for FC. stacked bars: use structure orientation later. Desktop interaction and hatch rendering still need verification in Deneb. Columns fill 2/3 of their slot; same column width across visuals (e.g. the month chart and its total): set barPx.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = height; fixed 24 px (14 px without category labels). Tiers: base = min(0, sum of negative Value per Period) … max(0, sum of positive Value per Period), after unitDivisor (padHigh `labelPx`; padLowIfNegative `labelPx`). container height = fixedPx + (hi − lo) × pxPerUnit + labelPx (+ labelPx again when lo < 0); fixedPx measured with Vega-Lite 6.4.3 at ibcsFontSize 12; use fixedPxNoCategoryLabels when showCategoryLabels = false; stepScale = 1.5 by default; columns fill 2/3 of their slot (barPx for one width across visuals); reserve right padding for legendOffsetPx + 4 px + the widest segment name, and plot height at least ibcsFontSize + (visible legend names − 1) × max(legendGapPx, ibcsFontSize + 2).

## waterfall-calculation

IBCS calculation waterfall (EX 1.1 card 28): a P&L or additive calculation, dark base/results from the axis, grey additions/subtractions with signed labels and assisting lines, subtotal rows bold with a calculation line above. Supports explicit Kind rows and element-only rows with BaseValue/TotalValue anchors.

- IBCS: EX 1.1 card 28
- Sample data: `assets/sample-data/pnl-calculation.json`

| Field | Meaning |
|---|---|
| `Line` | text, row label; sort the visual in the intended element/report order (blank labels are dropped) |
| `Value` | measure, SIGNED contribution (+ addition, − subtraction); Kind base supplies the start value. For explicit subtotal/total rows supply the expected result for reconciliation (or repeat an anchor measure to retain a null-Value result row) |
| `Kind` | optional text: base \| delta (or element) \| subtotal \| total. Omit for element-only input with BaseValue/TotalValue; omitted/blank Kind means delta |
| `PxPerUnit` | optional measure, same value on every row: px per display unit for the page's scale group; wins over pxPerUnit |
| `BaseValue` | optional measure on element rows: starting/reference value; the first non-null value in visual row order synthesizes a base bar unless an explicit Kind base row exists. Values are before unitDivisor |
| `TotalValue` | optional measure on element rows: primary/result value; the first non-null value in visual row order synthesizes a total bar unless an explicit Kind total row exists. Values are before unitDivisor |
| `ScaleBand` | optional positive measure, same value on every row: common scale-band value in data units before unitDivisor; wins over scaleBand |

Required fields: `Line`, `Value`, and one of `Kind` or `BaseValue` + `TotalValue`; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `baseLabel` | `"Base"` | row label of the synthesized BaseValue bar; explicit Kind base rows keep their own label |
| `totalLabel` | `"Total"` | row label of the synthesized TotalValue bar; explicit Kind total rows keep their own label |
| `scaleBand` | `0` | common positive reference in display units for charts of one unit that use different scales: area from zero to the value plus a labelled line; 0 = off. The ScaleBand field overrides this in data units before unitDivisor |
| `decimals` | `1` | decimals of every value label (display units); also the precision of the rounded-zero rule |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `xMax` | `0` | right end of the value scale in display units; 0 = from the data. A shared DOMAIN: same xMax gives the same px per unit only on waterfalls of the same width and labelWidth. For a same-unit scale group use pxPerUnit instead |
| `pxPerUnit` | `0` | px per display unit (after unitDivisor) on the value axis; 0 = off. When set, the domain is the plot width ÷ pxPerUnit, anchored at the left end (zero, or the loss label room), so two waterfalls of one unit show the same px per unit. Size the container to the data (usermeta.ibcs.layout, scripts/scale_layout.py of the ibcs-power-bi skill). If the container is too small, the data wins and the px per unit shrinks: nothing is cut |
| `labelWidth` | `120` | px reserved left of the axis for the report-line names |
| `labelRoom` | `30` | minimum px reserved inside the value domain beyond the bar ends; automatically enlarged for long value labels. Also used as right outer padding |
| `stepScale` | `1.5` | multiplies the category step (ibcsCategoryStep), keep it identical for every chart of the page |

Notes: Additions and subtractions are not variances: results and additions mid grey, subtractions dark (FIG EX 1.1-14), never green/red. Labels are unsigned (the fill shows the direction); a negative result (a loss) is drawn left of the axis and keeps its sign. Rounded-zero rule: abs(value) × 10^decimals < 0.5 is labelled 0 without a sign. These calculation steps are not variances and never use impact colour. The template recomputes subtotals/results as running sums; if a supplied result differs by more than 0.5 of the last decimal, its label shows the supplied magnitude with a '!' to expose the mismatch. Two waterfalls of one unit: the same pxPerUnit, labelWidth and labelRoom, with each visual sized to its own range (usermeta.ibcs.layout). Label room is reserved inside the domain, automatically enlarged for longer labels, so the rightmost result label fits even without pxPerUnit. Scale band (CH 4.3): set the same positive scaleBand value (display units) in charts of one unit that must use different scales; a light area from zero to the value, a line and a label provide the common reference. 0 = off; ScaleBand is in data units before unitDivisor. Input formats: (1) explicit Kind rows, with base/total values in Value; (2) one model row per element, Value as the signed contribution, optional Kind omitted, and BaseValue/TotalValue measures repeated on element rows. The template uses the first non-null value of each anchor independently in visual row order, creates each missing anchor once, and keeps explicit base/total rows when present. baseLabel/totalLabel name only the synthesized bars. Repeated anchor measures must be constant in the current filter context. Blank categories and rows whose Value, BaseValue and TotalValue are all null are dropped; zero is a value, and an anchor-only row is retained. PxPerUnit/ScaleBand alone do not retain an unknown N/A member.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = width; fixed 3 px, plus the category labels: width of the longest report-line name in px + 6 (Vega measures the text; about 7 px per character at 12 px Segoe UI); labelWidth does not reserve it. Tiers: waterfall = min(0, lowest bar end) … max(highest bar end, scaleBand) (padHigh `labelRoom`; padLowIfNegative `labelRoom`). container width = fixedPx + report-line names + (hi − lo) × pxPerUnit + padHigh + padLow; value-label pads are at least labelRoom and grow to fit formatted labels.

## waterfall-variance

IBCS vertical variance waterfall (EX 1.1 card 29): reference total (PY/PL) at the top from the axis, the variance by structure element as floating bars (impact colour, signed labels outside), the primary total (AC/FC) at the bottom, assisting lines, and the total variance arrow under the result. Options: scale band (CH 4.3) and a highlighting ellipse on one value (UN 5.1).

- IBCS: EX 1.1 card 29, UN 4.1
- Sample data: `assets/sample-data/variance-waterfall.json`

| Field | Meaning |
|---|---|
| `Category` | text, row label; sort the visual in the intended element/report order (blank labels are dropped) |
| `Kind` | optional text: base \| variance (or element) \| total. Omit for element-only input with BaseValue/TotalValue; omitted/blank Kind means variance |
| `Value` | measure: base = reference value; variance/element = SIGNED CONTRIBUTION to the total; total = primary value. For a cost line in a margin bridge bind −ΔCOS with Polarity +1, not raw ΔCOS |
| `Polarity` | optional measure 1 / -1 / 0; else the polarity knob |
| `PxPerUnit` | optional measure, same value on every row: px per display unit for the page's scale group; wins over pxPerUnit |
| `BaseValue` | optional measure on element rows: starting/reference value; the first non-null value in visual row order synthesizes a base bar unless an explicit Kind base row exists. Values are before unitDivisor |
| `TotalValue` | optional measure on element rows: primary/result value; the first non-null value in visual row order synthesizes a total bar unless an explicit Kind total row exists. Values are before unitDivisor |
| `ScaleBand` | optional measure, same value on every row: scale band value in data units (before unitDivisor); wins over scaleBand |
| `Highlight` | optional measure: 1 on the row whose value label gets the highlighting ellipse (the value the key message cites); blank or 0 = none |

Required fields: `Category`, `Value`, and one of `Kind` or `BaseValue` + `TotalValue`; the others may stay unbound.

| Knob | Default | Meaning |
|---|---|---|
| `baseLabel` | `"Reference"` | row label of the synthesized BaseValue bar; explicit Kind base rows keep their own label |
| `totalLabel` | `"Total"` | row label of the synthesized TotalValue bar; explicit Kind total rows keep their own label |
| `refScenario` | `"PY"` | name and notation of the base bar: 'PY' (solid light) or a plan code such as 'PL' or 'BU' (outlined) |
| `minuend` | `"AC"` | name and notation of the total bar: 'AC' (solid) or 'FC' (hatched) |
| `polarity` | `1` | 1 higher is better, -1 lower is better, 0 neutral (blue): impact colour only, never the direction (a Polarity field per row wins where the template reads one) |
| `decimals` | `1` | decimals of every value label (display units); also the precision of the rounded-zero rule |
| `unitDivisor` | `1` | divides every value before drawing and labelling: 1 = the measures are already scaled (preferred, e.g. a scaled measure or a Scale picker), 1000 = thousands, 1000000 = millions. The unit belongs in the title (UN 2.2), never as K/M suffixes |
| `xMax` | `0` | right end of the value scale in display units; 0 = from the data. A shared DOMAIN: same xMax gives the same px per unit only on waterfalls of the same width and labelWidth. For a same-unit scale group use pxPerUnit instead |
| `pxPerUnit` | `0` | px per display unit (after unitDivisor) on the value axis; 0 = off. When set, the domain is the plot width ÷ pxPerUnit, anchored at the left end (zero), so two waterfalls of one unit show the same px per unit. Size the container to the data (usermeta.ibcs.layout, scripts/scale_layout.py of the ibcs-power-bi skill). If the container is too small, the data wins and the px per unit shrinks: nothing is cut |
| `ibcsLabelPx` | `30` | label room in px right of the longest bar (pxPerUnit > 0 only) |
| `labelWidth` | `70` | px reserved for the row labels when the container is narrow; the label column is measured from the text, pass its width to scale_layout.py |
| `scaleBand` | `0` | scale band (CH 4.3) in display units: a light area from the axis to this value and a labelled line, the same round value in every chart of the unit whose scales differ; 0 = off (field ScaleBand wins, in data units before unitDivisor) |
| `highlight` | `""` | row label (Category, or baseLabel / totalLabel for the synthesized bars) whose value label gets the blue highlighting ellipse (UN 5.1): the value the key message cites; '' = none. The field Highlight (1 on the row) does the same from the model |
| `stepScale` | `1.5` | multiplies the category step (ibcsCategoryStep), keep it identical for every chart of the page |

Notes: Value is the contribution to the total, not necessarily the source measure delta: for a cost line in a margin bridge bind −ΔCOS with Polarity +1. A cost increase therefore contributes a negative step (unfavourable), and a cost reduction contributes a positive step (favourable). Polarity changes only impact colour; geometry always follows the contribution sign. Include a remainder row (e.g. Rest) so base + Σ contribution = total. If they do not reconcile, the arrow label shows the difference with a '!'. Two waterfalls of one unit: the same pxPerUnit and labelWidth, and each visual's width sized to its own range (usermeta.ibcs.layout). Rounded-zero rule: abs(value) × 10^decimals < 0.5 is labelled 0 without sign and gets no impact colour. Input formats: (1) explicit Kind rows, with base/total values in Value; (2) one model row per element, Value as the signed contribution, optional Kind omitted, and BaseValue/TotalValue measures repeated on element rows. The template uses the first non-null value of each anchor independently in visual row order, creates each missing anchor once, and keeps explicit base/total rows when present. baseLabel/totalLabel name only the synthesized bars. Repeated anchor measures must be constant in the current filter context. Blank categories and rows whose Value, BaseValue and TotalValue are all null are dropped; zero is a value, and an anchor-only row is retained. PxPerUnit alone do not retain an unknown N/A member. Scale band (CH 4.3): set scaleBand (or bind ScaleBand) to the same round value in every chart of the unit whose scales differ (e.g. a waterfall by month next to one by entity at another px per unit). Highlight (UN 5.1): knob highlight = the row label, or field Highlight = 1 on that row, draws the blue ellipse around its value label; one highlighted value per chart, the one the key message names. With pxPerUnit = 0 the scale leaves room for the widest label (measured like bar-structure-variance) beyond the 34 px right padding, so labels are never cut at the visual edge.

Layout for `pxPerUnit` sizing (`usermeta.ibcs.layout`): computed size = width; fixed 37 px, plus the category labels: width of the longest row label in px + 6 (Vega measures the text; about 7 px per character at 12 px Segoe UI); labelWidth does not reserve it. Tiers: waterfall = 0 … max(base, running sum, total, scaleBand) (padHigh `ibcsLabelPx`). container width = fixedPx + row labels + (hi − lo) × pxPerUnit + padHigh; measured with Vega-Lite 6.4.3 at ibcsFontSize 12; a highlighting ellipse reaches 5 px beyond its label on each side: keep ibcsLabelPx (right pad) large enough when the highlighted label is the rightmost one.
