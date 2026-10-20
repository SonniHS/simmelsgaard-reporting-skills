# Visual data contract: the DAX query each IBCS chart and table needs

One contract, three consumers:

- **Power BI visuals** issue these queries themselves. Each section gives the *field-well
  binding* that makes a visual issue the equivalent query. For IBCS notation in Power BI use
  the `ibcs-deneb` skill (plugin `ibcs-power-bi`).
- **Fabric Apps** send DAX through the semantic-model connector (`executeQueries`). Each
  section gives the `EVALUATE` text to put in a `.dax` file (one grain per file); see the
  `ibcs-fabric-app` skill (plugin `fabric-apps`).
- **Web charts** (any front end calling the REST API) consume the same result shapes; the
  `ibcs-web-charts` skill (plugin `ibcs`) renders them.

The visual rules behind each chart and table (scenario notation, variance colours, scaling,
titles) are in the `ibcs-notation` skill and the page rules in the `ibcs-composition` skill
(both plugin `ibcs`). This file only defines *what data* each one needs.

All queries run against the reference model ([reference-model-tmdl.md](reference-model-tmdl.md)).
For a different model, keep the shape and swap names. Dates (`2026-09`) are examples.

## Contents
0. Conventions (parameters, result shapes, sign contract, value kinds, impact, AC&FC naming,
   explicit-measure models)
1. Time-series charts
2. Structure charts
3. Calculation waterfall and P&L rows
4. Two-value-axis charts
5. Tables: variance, time series, cross table, combined
6. KPI tiles and small multiples
7. Checklist before you ship a query

---

## 0. Conventions

### 0.1 Parameters (always the same three)

| Parameter | DAX | Why |
|---|---|---|
| Reporting month | `TREATAS ( { "2026-09" }, 'Date'[MonthLabel] )` | Time Calc items (YTD, FY, R12, YTG) derive everything from the **last period in context**. One month in, every period view out. Default = `[fx Last Closed Month]`. |
| Period view | `TREATAS ( { "YTD" }, 'Time Calc'[Period] )` | Omit for "Period" (the month itself). |
| KPI | `TREATAS ( { "REV" }, 'Report Line'[LineCode] )` + measure `[Report Value]` | Using `[Report Value]` + a line filter (instead of `[Revenue]`) keeps the colour/impact helpers working for every KPI. |

A rolling window of months for time series:

```dax
DEFINE
    VAR __End = DATE ( 2026, 9, 30 )   // or MAX('Date'[Date]) of the reporting month
    VAR __Months =
        CALCULATETABLE ( VALUES ( 'Date'[MonthLabel] ), DATESINPERIOD ( 'Date'[Date], __End, -12, MONTH ) )
```

For a full fiscal year axis use `TREATAS ( { 2026 }, 'Date'[FiscalYearNo] )` instead.

### 0.2 Two result shapes

| Shape | How | Use for |
|---|---|---|
| **Wide** (one column per scenario/variance) | `"AC", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" )`, … | Charts: each series is a column; Vega-Lite folds them if needed |
| **Long** (one row per scenario/variance) | Group by `'Scenario Analysis'[Ordinal]`, `'Scenario Analysis'[Scenario]` + `TREATAS ( {…}, 'Scenario Analysis'[Scenario] )` + `"Value", [Report Value]` | Tables: column order = Ordinal = IBCS order |

`SUMMARIZECOLUMNS` drops rows where every measure is blank. That is what you want for payload
size. Fill gaps (months without data) in the app from the dimension list, never by `+ 0` in
DAX.

### 0.3 Sign contract: variances on displayed values

| Layer | Sign |
|---|---|
| Stored (`Finance[AmountGC]`) | P&L sign: revenue +, costs − (subtotals = plain sums) |
| **Displayed and compared** (`[Report Value]`) | `'Report Line'[DisplaySign] × amount`: revenue, costs **and** profit subtotals as an IBCS P&L shows them (costs positive); a loss subtotal stays negative |
| Absolute Δ | displayed minuend − displayed subtrahend |
| Relative Δ% | Δ / displayed reference; **N/A when the reference is blank, 0 or negative** |
| Good / bad | sign(Δ) × `'Report Line'[VarianceDirection]` (revenue/profit +1, costs −1, neutral 0); colour only |

**Worked example** (cost line *Material*, displayed positive, `VarianceDirection = −1`):

| | PL | AC | ΔPL | ΔPL% | Impact | Shown |
|---|---|---|---|---|---|---|
| Material | 20.8 | 20.0 | −0.8 | −0.8 / 20.8 = **−3.8 %** | sign(−0.8) × −1 = **+1** | bar/pin to the **left/down** (arithmetic sign), **green** |
| Revenue | 50.0 | 48.0 | −2.0 | −4.0 % | sign(−2.0) × +1 = −1 | left/down, red |
| EBIT (loss) | −3.0 | 1.0 | +4.0 | N/A (reference < 0) | +1 | right/up, green; Δ% printed `N/A` |

The waterfall is the one exception: its bar **positions** (`WF Start`/`WF End`) are in stored
P&L sign so costs go down; its **labels** use `[Report Value]` (costs positive, no minus sign).

### 0.4 Value kinds and how to format them in an app

`executeQueries` returns raw numbers. Model format strings (including the calc-item format
string expressions) are **not applied**, so the app must format by value kind, in the user's
locale:

| Item / column | Kind | Display rule |
|---|---|---|
| AC, PY, PL, BU, FC, AC+FC | value | scale once per object (k/m/bn, ≤ 3 digits in charts, ≤ 4 in tables), unit in the title (`mEUR`) |
| ΔPY, ΔPL, ΔBU, ΔFC, (AC+FC)-BU | absolute variance (minuend AC; **AC+FC** under the FY and YTG period views) | same scale as the values, **always signed** (`+1.2`, `−0.4`); structure and bridge rows use `Ibcs.DeltaMember` so a discontinued member shows 0 − REF ([dax-patterns.md](dax-patterns.md) §10) |
| Δ… of a ratio measure (`EBIT Margin %`, ratio report lines) | percentage points | the model already returns **pp** (×100): `+2.1 pp` |
| ΔPY%, ΔPL%, ΔBU%, ΔFC% | relative variance | signed percent (`+3.2%`); **BLANK next to a present AC means "N/A"** (reference blank, 0 or negative): print `N/A`, never 0 or empty; BLANK with AC blank too = no row. Same table as ibcs-web-charts `behaviour-contract.md` §1 |
| `Impact` | −1 / 0 / +1 / BLANK | colour only: +1 good (green), −1 bad (red), 0 neutral (blue), BLANK = Δ blank or exactly 0 → no colour |
| `IbcsNotation` (from `Scenario`) | text | solid / outlined / hatched fill of the scenario |

Plot variances with their **arithmetic sign** (a positive Δ goes up/right). Polarity changes
the colour, never the geometry, never the value.

### 0.5 Impact for colour

Ask the model, not the app: `"Impact", CALCULATE ( [fx Variance Impact], 'Scenario Analysis'[Scenario] = "ΔPY" )`.
It maps ΔPY and ΔPY% to the absolute ΔPY and multiplies its sign by
`'Report Line'[VarianceDirection]` (+1 / −1 / 0); a Δ of exactly 0 returns BLANK (no colour).
It evaluates `[Report Value]` only, so select KPIs by `'Report Line'[LineCode]`. Power BI:
bind `[fx Variance Colour]` as *field value* conditional formatting on the bars/cells (it is
evaluated per cell under the Δ item in context).

Deneb templates (the `ibcs-deneb` skill, plugin `ibcs-power-bi`) take a `Polarity` field
(1 / −1 / 0) and multiply the Δ by it themselves. Bind `Polarity` to
`'Report Line'[VarianceDirection]` (column, or `SELECTEDVALUE` of it as a measure), **not** to
`Impact`: `Impact` is already sign(Δ) × direction, so binding it would apply the direction twice.

### 0.6 AC&FC and AC+FC are the same thing

`AC&FC` is the IBCS notation for "actual for closed periods, forecast for the rest"; use it as
the **series label and in title line 3** in every visual. The calculation item in this model is
named `AC+FC` (and `(AC+FC)-BU` for its variance) because `&` is awkward in DAX names and URLs.
Both names mean the same scenario; never show `AC+FC` to readers. A new model may name the item
`AC&FC` directly.

### 0.7 Models with explicit measures instead of the calculation groups

Many shared models have `Revenue`, `Revenue PY`, `Revenue ΔPY`, `Revenue ΔPY%`, `Revenue
Polarity`, … as explicit measures (often built on the same `Ibcs.*` functions) and no
`Scenario Analysis` group. The result shapes stay the same; only the column expressions change.

**Wide shape** (charts): one measure per column, impact from the function and the measure's
polarity:

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[YearMonth], 'Date'[MonthLabel],
    TREATAS ( { 2026 }, 'Date'[FiscalYearNo] ),
    "AC", [Revenue], "PY", [Revenue PY], "ΔPY", [Revenue ΔPY], "ΔPY%", [Revenue ΔPY%],
    "ImpactΔPY", Ibcs.Impact ( [Revenue ΔPY], [Revenue Polarity] )
)
ORDER BY 'Date'[YearMonth]
```

**Long shape for KPI rows** (KPI cards, multi-measure tables with mixed units): one `ROW` per
measure, combined with `UNION`, filtered once by `CALCULATETABLE`. Every `ROW` must have the same
columns in the same order; put `BLANK ()` where a measure has no such comparison.

```dax
EVALUATE
CALCULATETABLE (
    UNION (
        ROW ( "Sort", 1, "Measure", "Revenue", "Kind", "amount",
              "AC", [Revenue], "PY", [Revenue PY], "ΔPY", [Revenue ΔPY], "ΔPY%", [Revenue ΔPY%],
              "BU", [Revenue BU], "ΔBU", [Revenue ΔBU], "ΔBU%", [Revenue ΔBU%],
              "ImpactΔPY", Ibcs.Impact ( [Revenue ΔPY], [Revenue Polarity] ),
              "ImpactΔBU", Ibcs.Impact ( [Revenue ΔBU], [Revenue Polarity] ) ),
        ROW ( "Sort", 2, "Measure", "Gross margin %", "Kind", "percent",
              "AC", [Gross Margin %], "PY", [Gross Margin % PY],
              "ΔPY", [Gross Margin % ΔPY], "ΔPY%", BLANK (),            -- Δ in pp; no Δ% of a ratio here
              "BU", BLANK (), "ΔBU", BLANK (), "ΔBU%", BLANK (),
              "ImpactΔPY", Ibcs.Impact ( [Gross Margin % ΔPY], [Gross Margin % Polarity] ),
              "ImpactΔBU", BLANK () )
    ),
    TREATAS ( { "2026-07", "2026-08", "2026-09" }, 'Date'[MonthLabel] )
)
ORDER BY [Sort]
```

`Kind` tells the app how to format the row (amount scaled, percent, ratio `0.00`); `Sort` keeps
the spec's order. Polarity per measure (`[X Polarity]`, +1/−1/0) replaces
`'Report Line'[VarianceDirection]`.

**AC&FC and full-period PY with explicit measures**: decide **per month**, then sum, so a
multi-month total mixes AC months and FC months correctly:

```dax
DEFINE
    MEASURE 'Measures'[Revenue AC&FC] =
        SUMX ( VALUES ( 'Date'[YearMonth] ),
            IF ( CALCULATE ( SELECTEDVALUE ( 'Date'[IsClosedPeriod] ) ), [Revenue], [Revenue FC] ) )
    MEASURE 'Measures'[Revenue PY AC&FC] =              -- like-for-like only where AC is shown
        SUMX ( VALUES ( 'Date'[YearMonth] ),
            IF ( CALCULATE ( SELECTEDVALUE ( 'Date'[IsClosedPeriod] ) ),
                [Revenue PY],                                                       -- the model's PY for closed months
                CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) ) ) )    -- full month for FC months
    MEASURE 'Measures'[Revenue AC&FC ΔBU] = Ibcs.Delta ( [Revenue AC&FC], [Revenue BU] )
```

The per-month SUMX is for additive measures; for a ratio, compute numerator and denominator this
way and divide once. Put these in the model when you can; when the model must not change, they
work unchanged as query-scoped `DEFINE MEASURE` (Fabric Apps, any DAX client) or as report-level
measures in Power BI, flagged in a footnote.

**Selector lists (entities, months) from a dimension.** `VALUES ( 'Company'[Company Code] )` or
`SUMMARIZECOLUMNS` on the dimension alone also returns the blank member (fact rows without a
match) and members that never had data. Filter the list with a measure, so it only offers what
the page can show:

```dax
EVALUATE
FILTER ( SUMMARIZECOLUMNS ( 'Company'[Company Code], "n", [Revenue] ),
         NOT ISBLANK ( 'Company'[Company Code] ) )
ORDER BY 'Company'[Company Code]
```

The same blank member, and every empty member, appears whenever a constant measure (a scale or
label measure) is in the same `SUMMARIZECOLUMNS` or visual: a row stays when any expression is
non-blank. Filter the blank category explicitly (as above, or a visual or spec filter), and keep
constants out of the grouping query (`IGNORE ( [Scale Max] )`, or a separate one-row query).

---

## 1. Time-series charts (time on the horizontal axis)

### Single column chart (AC per month)

```dax
DEFINE
    VAR __End = DATE ( 2026, 9, 30 )
    VAR __Months = CALCULATETABLE ( VALUES ( 'Date'[MonthLabel] ), DATESINPERIOD ( 'Date'[Date], __End, -12, MONTH ) )
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[YearMonth], 'Date'[MonthLabel], 'Date'[MonthShort],
    __Months,
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "AC", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" )
)
ORDER BY 'Date'[YearMonth]
```

Power BI: clustered column; X = `Date[MonthLabel]`, Y = `Report Value`, filter
`Scenario Analysis = AC`, `Report Line[LineCode] = REV`.

### Stacked column (AC per month by entity)

Add `Entity[EntityName]` to the group-by; one value column `"AC"`. Sort segments in the app
so the series of interest sits on the axis. Totals: sum in the app (safe, additive).

### Overlapping columns / scenario triangles (AC vs PY, BU)

```dax
DEFINE
    VAR __End = DATE ( 2026, 9, 30 )
    VAR __Months = CALCULATETABLE ( VALUES ( 'Date'[MonthLabel] ), DATESINPERIOD ( 'Date'[Date], __End, -12, MONTH ) )
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[YearMonth], 'Date'[MonthLabel],
    __Months,
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "AC", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" ),
    "PY", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "PY" ),
    "BU", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "BU" )
)
ORDER BY 'Date'[YearMonth]
```

Reference column (PY grey, BU outlined) behind AC; the third scenario as triangles.

### AC&FC series (one series that switches from AC to FC)

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[YearMonth], 'Date'[MonthLabel], 'Date'[IsClosedPeriod],
    TREATAS ( { 2026 }, 'Date'[FiscalYearNo] ),
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "Value", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC+FC" ),
    "PY",    CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "PY" )
)
ORDER BY 'Date'[YearMonth]
```

`IsClosedPeriod = TRUE` → AC notation (solid), `FALSE` → FC notation (hatched). Title line 3:
`2026 AC&FC and PY`. The FC version follows the `'FC Version'` selection; default = latest.

Rules for this series:

- **The switch is the last closed period**, not the data timestamp. The month that is still open
  (some AC already booked) is an **FC** month; its partial AC is not drawn and not added. Keep
  `'Date'[IsClosedPeriod]` driven by the ERP period status (or the reporting calendar), never by
  `MAX` of the fact date.
- **PY of an FC month is the full-period PY.** The PY item here is the whole month of last year,
  which is right: it is compared with a full-month FC. A like-for-like PY that cuts last year at
  the same day as the data timestamp (measures named like `LikeForLikeEndWithForecast`) is
  **wrong for FC months**; it is only right for an open month shown as partial AC, which IBCS
  pages do not do. If a model only has a like-for-like PY, switch per month: like-for-like (or
  plain PY) for closed months, full-period PY for FC months (pattern in §0.7).

### Absolute variance columns (ΔPY per month)

```dax
DEFINE
    VAR __End = DATE ( 2026, 9, 30 )
    VAR __Months = CALCULATETABLE ( VALUES ( 'Date'[MonthLabel] ), DATESINPERIOD ( 'Date'[Date], __End, -12, MONTH ) )
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[YearMonth], 'Date'[MonthLabel],
    __Months,
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "ΔPY",    CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "ΔPY" ),
    "Impact", CALCULATE ( [fx Variance Impact], 'Scenario Analysis'[Scenario] = "ΔPY" )
)
ORDER BY 'Date'[YearMonth]
```

Variance chart **on the same scale** as the base chart (absolute variances only). Axis
notation = the subtrahend (PY: solid light axis; BU/PL: double line). Minuend notation = fill
(AC solid, FC hatched).

### Horizontal pins (ΔPY% per month)

The previous query (with its `DEFINE` block) with `"ΔPY%"` and
`CALCULATE ( [fx Variance Impact], … = "ΔPY%" )`. BLANK = N/A: draw no pin, print `N/A`.
Relative variances use their own % scale.

### Horizontal variance waterfall (PY → quarters → AC)

Two queries (two grains), stitched in the app:

```dax
// a) totals: reference and result for the year to date
EVALUATE
SUMMARIZECOLUMNS (
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "PY", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "PY" ),
    "AC", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" )
)

// b) contributions: ΔPY per quarter (quarters of the same YTD window)
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[FiscalYearQuarter],
    TREATAS ( { 2026 }, 'Date'[FiscalYearNo] ),
    FILTER ( ALL ( 'Date'[FiscalPeriodSeq] ), 'Date'[FiscalPeriodSeq] <= 2026 * 12 + 9 ),
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "ΔPY",    CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "ΔPY" ),
    "Impact", CALCULATE ( [fx Variance Impact], 'Scenario Analysis'[Scenario] = "ΔPY" )
)
ORDER BY 'Date'[FiscalYearQuarter]
```

Check in the app: `PY + Σ ΔPY = AC` (fails → the windows differ). Start/End are a running sum
in the app (few rows). The native Power BI waterfall can't do this correctly (it colours by
sign); use Deneb or a certified custom visual.

### Line chart (AC, PY, BU over time)

The overlapping-columns query; add `"FC"` for forecast months. Lines: AC and FC on one
continuous line, FC points with **hatched markers**; PL/BU hollow markers; PY light.

### Indexed line (base period = 100 %)

```dax
DEFINE
    VAR __End = DATE ( 2026, 9, 30 )
    VAR __Months = CALCULATETABLE ( VALUES ( 'Date'[MonthLabel] ), DATESINPERIOD ( 'Date'[Date], __End, -12, MONTH ) )
    VAR __Base = CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC",
                             TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
                             TREATAS ( { "2025-10" }, 'Date'[MonthLabel] ) )
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[YearMonth], 'Date'[MonthLabel], __Months,
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "Index", DIVIDE ( CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" ), __Base )
)
ORDER BY 'Date'[YearMonth]
```

---

## 2. Structure charts (categories on the vertical axis)

Structure axis: entity, region, account, report line, product, customer. In Power BI bind the
`Structure` field parameter so one slicer switches the category.

### Single bar (AC by entity, sorted)

```dax
EVALUATE
SUMMARIZECOLUMNS (
    Entity[EntityCode], Entity[EntityName],
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "AC", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" )
)
ORDER BY [AC] DESC
```

`ORDER BY` here is for stable diffs; the app owns presentation sort (sort ↓ by AC, the
remainder last).

### Stacked bar

Add the series column (e.g. `Account[AccountName]`) to the group-by.

### Overlapping bars / triangles (AC vs PY, BU by entity)

The single-bar query plus `"PY"` and `"BU"` columns (wide shape).

### Absolute variance bars (ΔBU by entity)

```dax
EVALUATE
SUMMARIZECOLUMNS (
    Entity[EntityCode], Entity[EntityName],
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "ΔBU",    CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "ΔBU" ),
    "Impact", CALCULATE ( [fx Variance Impact], 'Scenario Analysis'[Scenario] = "ΔBU" )
)
```

Align rows with the base bar chart (same categories, same order, same height); same scale.

### Vertical pins (ΔBU% by entity)

The previous query with `"ΔBU%"`. BLANK → `N/A`.

### Vertical variance waterfall (PY → entities → AC)

Totals query (horizontal waterfall a) + contribution query (variance bars with ΔPY). Running
sums, the remainder row and the total-variance arrow are app logic. Sort contributions by the
structure's standard order or by |Δ| descending, remainder last.

### Remainder bar ("Top N + others")

Low cardinality (< ~200 members): fetch all with the single-bar query, group the tail into
`Other …` in the app, exclude it from ranks and averages. High cardinality: rank in DAX and
return the top N plus one remainder row:

```dax
DEFINE
    VAR __N = 5
    VAR __Line = { "OPEX" }                       // one report line: ranking mixed signs is meaningless
    VAR __Ranked =
        FILTER (
            ADDCOLUMNS (
                CALCULATETABLE ( VALUES ( Account[AccountName] ), TREATAS ( __Line, 'Report Line'[LineCode] ) ),
                "@AC", CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC",
                                   TREATAS ( __Line, 'Report Line'[LineCode] ),
                                   TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
                                   TREATAS ( { "YTD" }, 'Time Calc'[Period] ) )
            ),
            NOT ISBLANK ( [@AC] )
        )
    VAR __Top = TOPN ( __N, __Ranked, ABS ( [@AC] ), DESC, Account[AccountName], ASC )   // tiebreak keeps N rows
    VAR __Rest = EXCEPT ( __Ranked, __Top )
EVALUATE
UNION (
    SELECTCOLUMNS ( __Top, "Category", Account[AccountName], "AC", [@AC], "IsRemainder", FALSE () ),
    ROW ( "Category", "Other accounts", "AC", SUMX ( __Rest, [@AC] ), "IsRemainder", TRUE () )
)
```

(`[Report Value]` needs exactly one line in context, hence the line filter inside the measure
call; the bridge restricts the account list to that line. The remainder row is blank when
there is no rest.)

---

## 3. Calculation waterfall and P&L rows

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Report Line'[SortOrder], 'Report Line'[LineCode], 'Report Line'[LineName],
    'Report Line'[LineType], 'Report Line'[IsBold],
    TREATAS ( { "Detail", "Subtotal", "Total" }, 'Report Line'[LineType] ),
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "AC" }, 'Scenario Analysis'[Scenario] ),
    "Value", [Report Value],
    "Start", [WF Start],
    "End",   [WF End]
)
ORDER BY 'Report Line'[SortOrder]
```

- Detail bars float from `Start` to `End` (positions in stored P&L sign, so costs go down);
  subtotal/total bars start at 0 (`Start = 0`). Labels print `Value` (display sign: costs
  positive).
- Additions (End > Start) mid grey, subtractions dark; **no green/red** (not variances).
- Labels: right of additions, left of subtractions, printed **without minus sign** (the line
  name says "costs"); subtotal rows bold with a line above.
- Reconciliation the app can assert: every subtotal's `End` equals the previous detail's
  `End`. If not, the bridge is wrong (see the bridge check in
  [05_checks.sql](../../sql-reporting-backend/assets/sql/05_checks.sql)).
- Power BI: matrix with `Report Line[LineName]` on rows, `Report Value` and an SVG measure
  built from `WF Start`/`WF End`, or Deneb (the `ibcs-deneb` skill, plugin `ibcs-power-bi`,
  mapping below), or a certified custom visual. The native waterfall visual is columns-only
  and can't do subtotals.

**Deneb `waterfall-calculation` template.** Its input contract is `Line`, a **signed** `Value`
(+ addition, − subtraction) and `Kind` (`base | delta | subtotal | total`). Do not bind
`Value` above (`[Report Value]`, display sign: costs positive would be *added*). Map instead:

| Template field | From the model |
|---|---|
| `Line` | `'Report Line'[LineName]` (visual sorted by `'Report Line'[SortOrder]`) |
| `Value` | `[WF End] − [WF Start]`: the contribution in stored P&L sign (revenue +, costs −); on subtotal/total rows (`Start = 0`) their result, so a loss arrives negative |
| `Kind` | first detail line → `base`, other `Detail` → `delta`, `Subtotal` → `subtotal`, `Total` → `total` |

```dax
DEFINE
    MEASURE _Measures[WF Kind] =
        VAR lineType = SELECTEDVALUE ( 'Report Line'[LineType] )
        VAR firstDetail = CALCULATE ( MIN ( 'Report Line'[SortOrder] ), REMOVEFILTERS ( 'Report Line' ),
                                      'Report Line'[LineType] = "Detail" )
        RETURN SWITCH ( TRUE (),
            lineType = "Detail" && SELECTEDVALUE ( 'Report Line'[SortOrder] ) = firstDetail, "base",
            lineType = "Detail", "delta",
            lineType = "Subtotal", "subtotal",
            lineType = "Total", "total" )
EVALUATE
SUMMARIZECOLUMNS (
    'Report Line'[SortOrder], 'Report Line'[LineName],
    TREATAS ( { "Detail", "Subtotal", "Total" }, 'Report Line'[LineType] ),
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "AC" }, 'Scenario Analysis'[Scenario] ),
    "Value", [WF End] - [WF Start],
    "Kind",  [WF Kind]
)
ORDER BY 'Report Line'[SortOrder]
```

In the Power BI model, add `WF Kind` and `WF Value = [WF End] - [WF Start]` to the `3 Waterfall`
folder and bind those.

---

## 4. Two value axes (scatter and bubble)

```dax
EVALUATE
SUMMARIZECOLUMNS (
    Entity[EntityName], Entity[Region],
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "AC" }, 'Scenario Analysis'[Scenario] ),
    "Margin", [EBIT Margin %],
    "Revenue", [Revenue],
    "EBIT", [EBIT]
)
```

Ratio on X, absolute on Y, size = third absolute measure (bubble). Labels next to symbols
instead of a separate legend.

---

## 5. Tables

### Variance table (PY | BU | AC ‖ ΔPY ΔPY% ‖ ΔBU ΔBU%) by report line

Long shape; the app pivots on `Scenario` in `Ordinal` order:

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Report Line'[SortOrder], 'Report Line'[LineName], 'Report Line'[LineType],
    'Report Line'[IsBold], 'Report Line'[Indent],
    'Scenario Analysis'[Ordinal], 'Scenario Analysis'[Scenario],
    TREATAS ( { "PY", "BU", "AC", "ΔPY", "ΔPY%", "ΔBU", "ΔBU%" }, 'Scenario Analysis'[Scenario] ),
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    "Value",  [Report Value],
    "Impact", [fx Variance Impact]
)
ORDER BY 'Report Line'[SortOrder], 'Scenario Analysis'[Ordinal]
```

- The EBIT margin row comes back as a ratio: values in 0.0–1.0, Δ columns in **pp**, Δ%
  normal relative.
- Cost lines come back positive (display sign) with their own Δ% and `Impact` from
  `VarianceDirection = −1`; a loss subtotal (negative) has Δ% BLANK = N/A.
- Power BI matrix: rows `Report Line[LineName]`, columns `Scenario Analysis[Scenario]`
  (filtered to the 7 items), values `Report Value`; font colour = field value
  `fx Variance Colour`; column subtotals off; scenario notation in headers is not native (see
  the `ibcs-notation` skill, plugin `ibcs`).
- By entity instead of by line: replace the `Report Line` group-by columns with
  `Entity[EntityName]` and add `TREATAS ( { "EBIT" }, 'Report Line'[LineCode] )`.

### Time-series table (past years AC, current year AC+FC, next year PL)

```dax
DEFINE
    MEASURE _Measures[T Value] =
        VAR y = SELECTEDVALUE ( 'Date'[FiscalYearNo] )
        RETURN
            SWITCH (
                TRUE (),
                y <= 2025, CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC" ),
                y = 2026,  CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "AC+FC" ),
                CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = "PL" )
            )
    MEASURE _Measures[T Scenario] =
        VAR y = SELECTEDVALUE ( 'Date'[FiscalYearNo] )
        RETURN IF ( NOT ISBLANK ( [T Value] ), SWITCH ( TRUE (), y <= 2025, "AC", y = 2026, "AC&FC", "PL" ) )
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[FiscalYearNo], 'Date'[FiscalYear],
    Entity[EntityName],
    TREATAS ( { 2024, 2025, 2026, 2027 }, 'Date'[FiscalYearNo] ),
    TREATAS ( { "REV" }, 'Report Line'[LineCode] ),
    "Value", [T Value],
    "Scenario", [T Scenario]
)
ORDER BY Entity[EntityName], 'Date'[FiscalYearNo]
```

Derive the year boundaries from `'Date'[IsClosedPeriod]` in production, not literals. The
header notation per year follows `Scenario` (solid / solid+hatched / outlined).

### Cross table (entity × report line)

```dax
EVALUATE
SUMMARIZECOLUMNS (
    Entity[EntityName], 'Report Line'[SortOrder], 'Report Line'[LineName],
    TREATAS ( { "REV", "GP", "EBIT" }, 'Report Line'[LineCode] ),
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "AC" }, 'Scenario Analysis'[Scenario] ),
    "AC", [Report Value]
)
```

Row and column totals: the group total of an additive line is a sum in the app; for a ratio
line, issue a second query without the `Entity` group-by.

### Combined table (Month | YTD) × (PY BU AC ΔPY ΔPY% ΔBU ΔBU%)

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Report Line'[SortOrder], 'Report Line'[LineName], 'Report Line'[IsBold],
    'Time Calc'[Ordinal], 'Time Calc'[Period],
    'Scenario Analysis'[Ordinal], 'Scenario Analysis'[Scenario],
    TREATAS ( { "Period", "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "PY", "BU", "AC", "ΔPY", "ΔPY%", "ΔBU", "ΔBU%" }, 'Scenario Analysis'[Scenario] ),
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    "Value",  [Report Value],
    "Impact", [fx Variance Impact]
)
ORDER BY 'Report Line'[SortOrder], 'Time Calc'[Ordinal], 'Scenario Analysis'[Ordinal]
```

Two calc groups: Scenario Analysis (20) wraps Time Calc (10), so every variance is computed
**within** its period block. Power BI matrix: columns `Time Calc[Period]` >
`Scenario Analysis[Scenario]`.

---

## 6. KPI tiles and small multiples

- **KPI tile** (value + ΔPY + ΔPY% + ΔBU% for one line): the variance-table query with one
  `LineCode` and no `Report Line` group-by. A row of KPI cards for measures with different units
  is the long shape in §0.7 (one row per measure). Plus a sparkline query (single column chart,
  12 months).
- **Small multiples** (one chart per entity, shared scale): the overlapping-columns query with
  `Entity[EntityName]` added. The app computes **one** value-axis domain across all panels
  (same scale in every panel).

---

## 7. Checklist before you ship a query

- [ ] Exactly one reporting month in context (or an explicit month window); never a whole
      year plus a Time Calc item.
- [ ] Scenario/variance via the calc group (or the explicit measures, §0.7), never by slicing `Scenario[ScenarioType]` on its
      own (the PY/AC+FC/FC-version logic lives in the items).
- [ ] KPI chosen by `'Report Line'[LineCode]` with `[Report Value]`, so `fx Variance Impact`
      works.
- [ ] Δ% BLANK rendered as `N/A`; Δ of ratios labelled `pp`.
- [ ] Colour from `Impact` (−1/0/+1); geometry from the signed value.
- [ ] One grain per query; totals of non-additive values (ratios) from a second query.
- [ ] No `FORMAT()` in DAX; raw numbers out, formatting (locale, scale, unit) in the app.
- [ ] Results reconcile with totals computed directly in SQL for the same month and scenario.
