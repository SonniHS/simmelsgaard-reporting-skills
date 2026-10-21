# DAX pattern library for IBCS models

Names follow the reference model ([reference-model-tmdl.md](reference-model-tmdl.md)). Generic
DAX syntax and optimisation: the Learn DAX reference or a DAX skill; Fabric App query
construction: the `ibcs-fabric-app` skill (plugin `fabric-apps`).

## Contents
1. IBCS variance rules as UDFs
2. Base measure that defaults to AC
3. Scenario items: AC, BU/PL, FC version picker, PY (three variants)
4. AC+FC (year-end projection) without breaking ratios or Time Calc
5. Time Calc items (offset-based, any fiscal calendar)
6. Variance items, percentage points for ratios
7. Polarity, impact and colour
8. Unit scaling and title helpers
9. Report lines: Report Value, ratio lines, calculation waterfall
10. Structure analyses: Top N + remainder, field parameters
11. Grain guards (plan below month, dimensions the plan lacks)
12. Currency: constant currency, FX-neutral ΔBU
13. Explicit measures when a calc group is not an option
14. Test queries and traps

---

## 1. IBCS variance rules as UDFs (compatibility level ≥ 1702)

```dax
DEFINE
    /// Δ = minuend − subtrahend; BLANK if either side is blank (no variance against nothing)
    FUNCTION Ibcs.Delta = ( actual, reference ) =>
        IF ( NOT ISBLANK ( actual ) && NOT ISBLANK ( reference ), actual - reference )

    /// Δ for STRUCTURE and BRIDGE rows: a member with a reference but no actual (discontinued
    /// product, closed company) keeps 0 − reference, a new member keeps actual − 0, so the rows
    /// reconcile with the total Δ. referenceExists = the reference scenario has data for the
    /// period at all (e.g. NOT ISBLANK ( CALCULATE ( [PY], REMOVEFILTERS ( 'Product' ) ) )); without
    /// it a period before the reference history would turn every AC into a variance.
    /// Use it wherever rows are summed or stacked to explain a total; Ibcs.Delta elsewhere.
    FUNCTION Ibcs.DeltaMember = ( actual, reference, referenceExists : BOOLEAN ) =>
        IF (
            referenceExists && NOT ( ISBLANK ( actual ) && ISBLANK ( reference ) ),
            COALESCE ( actual, 0 ) - COALESCE ( reference, 0 )
        )

    /// Δ% = (actual − reference) / reference with the SIGNED reference (IBCS v2.0, UN 4.1).
    /// BLANK = "N/A" when the reference is blank, 0 or negative (OURS, generalising UN 4.1 p. 54).
    FUNCTION Ibcs.DeltaPct = ( actual, reference ) =>
        IF (
            NOT ISBLANK ( actual ) && NOT ISBLANK ( reference ) && reference > 0,
            DIVIDE ( actual - reference, reference )
        )

    /// Impact for COLOUR only: +1 good, −1 bad, 0 neutral (direction 0); BLANK for no or zero variance
    FUNCTION Ibcs.Impact = ( delta, direction ) =>
        IF ( NOT ISBLANK ( delta ) && delta <> 0, SIGN ( delta * direction ) )

    /// GRAPHIC colour of an impact, for bars, pins and markers only: +1 good, −1 bad, 0 neutral;
    /// BLANK (no or zero variance) stays BLANK. Hex values: the default ibcs-notation tokens
    /// color.variance.{good,bad,neutral}; use your overrides. Never as a font colour: the graphic
    /// green is about 2.4:1 on white.
    FUNCTION Ibcs.ImpactColour = ( impact ) =>
        IF ( NOT ISBLANK ( impact ),                 -- guard first: in DAX BLANK = 0 would match "neutral"
            SWITCH ( impact, 1, "#8CB400", -1, "#FF0000", 0, "#0064FF" ) )

    /// TEXT colour of an impact, for tinted variance NUMBERS (matrix and table font colour, labels):
    /// the contrast-safe tokens color.variance.{goodText,badText,neutralText} (≥ 4.5:1 on white).
    /// BLANK stays BLANK = default (black) text.
    FUNCTION Ibcs.ImpactTextColour = ( impact ) =>
        IF ( NOT ISBLANK ( impact ),
            SWITCH ( impact, 1, "#5A7A00", -1, "#D00000", 0, "#0064FF" ) )

    /// Helper measures (named "fx …") pass through every calc item unchanged
    FUNCTION Ibcs.IsHelper = ( measureName : STRING ) =>
        LEFT ( measureName, 3 ) = "fx "

    /// Ratio measures are detected by a "%" in their format string (see §6 for the caveat)
    FUNCTION Ibcs.IsRatioFormat = ( formatString : STRING ) =>
        CONTAINSSTRING ( formatString, "%" )

    /// Δ of a ratio in percentage points: 0.012 → 1.2, shown with the pp format below (that
    /// format does not scale, so the ×100 happens here). Other measures pass unchanged.
    FUNCTION Ibcs.PointsIfRatio = ( delta, formatString : STRING ) =>
        IF ( Ibcs.IsRatioFormat ( formatString ), delta * 100, delta )

    /// Divisor and fixed decimals of a scale "1" | "k" | "m" | "bn" (as printed by Ibcs.ScaleFormat)
    FUNCTION Ibcs.ScaleDivisor = ( scale : STRING ) =>
        SWITCH ( scale, "bn", 1e9, "m", 1e6, "k", 1e3, 1 )
    FUNCTION Ibcs.ScaleDecimals = ( scale : STRING ) =>
        IF ( scale IN { "bn", "m", "k" }, 1, 0 )

    /// Scaled number format for "1" | "k" | "m" | "bn" (each "," = ÷1 000 in en-US format
    /// strings); signed = TRUE gives the variance form +x;−x;0
    FUNCTION Ibcs.ScaleFormat = ( scale : STRING, signed : BOOLEAN ) =>
        VAR body = SWITCH ( scale, "bn", "#,0.0,,,", "m", "#,0.0,,", "k", "#,0.0,", "#,0" )
        VAR zero = IF ( scale IN { "bn", "m", "k" }, "0.0", "0" )
        RETURN IF ( signed, "+" & body & ";-" & body & ";" & zero, body )

    /// Format of the value items (PY, PL, BU, FC, AC, AC+FC): scaled and unsigned; ratios and
    /// helpers keep their own format
    FUNCTION Ibcs.ValueFormat = ( measureName : STRING, formatString : STRING, scale : STRING ) =>
        IF ( Ibcs.IsHelper ( measureName ) || Ibcs.IsRatioFormat ( formatString ),
            formatString, Ibcs.ScaleFormat ( scale, FALSE ) )

    /// Format of the absolute variance items: scaled and signed; ratios in signed percentage points.
    /// value = the item's result (pass SELECTEDMEASURE ()). A variance that ROUNDS to zero at the
    /// printed scale and decimals gets the unsigned zero section: "0.0", never "+0.0" or "-0.0"
    /// (a format string picks its section by the unrounded sign).
    FUNCTION Ibcs.DeltaFormat = ( value, measureName : STRING, formatString : STRING, scale : STRING ) =>
        VAR isRatio = Ibcs.IsRatioFormat ( formatString )
        VAR shown = IF ( isRatio, ROUND ( value, 1 ), ROUND ( value / Ibcs.ScaleDivisor ( scale ), Ibcs.ScaleDecimals ( scale ) ) )
        RETURN
            SWITCH ( TRUE (),
                Ibcs.IsHelper ( measureName ), formatString,
                isRatio && shown = 0, "0.0"" pp""",
                isRatio, "+0.0"" pp"";-0.0"" pp"";0.0"" pp""",
                shown = 0, IF ( scale IN { "bn", "m", "k" }, "0.0", "0" ),
                Ibcs.ScaleFormat ( scale, TRUE ) )

    /// Format of the relative variance items (Δ%); a Δ% that rounds to 0.0 % is unsigned
    FUNCTION Ibcs.DeltaPctFormat = ( value, measureName : STRING, formatString : STRING ) =>
        SWITCH ( TRUE (),
            Ibcs.IsHelper ( measureName ), formatString,
            ROUND ( value, 3 ) = 0, "0.0%",
            "+0.0%;-0.0%;0.0%" )
```

Signatures follow the Learn general form
`FUNCTION <name> = ( <param> [: <type>], … ) => <body>`; `STRING`/`BOOLEAN` are scalar subtype
hints. The calls with these signatures are in §3, §6, §7 and the calc group in
[reference-model-tmdl.md](reference-model-tmdl.md) §5.

Why this rule (the same rule is used by the `ibcs-web-charts` skill in plugin `ibcs` and the
`ibcs-deneb` skill in plugin `ibcs-power-bi`, so model and visuals agree): IBCS defines the
relative variance against the signed reference and notes that a result compared with a
negative reference cannot be interpreted (IBCS v2.0, UN 4.1, p. 54). We generalise that to
**every reference ≤ 0** (OURS):

| Reference | Actual | Result | Why |
|---|---|---|---|
| 100 | −20 | −120 % | interpretable: shown |
| 100 | 110 | +10 % | normal case |
| −30 | −10 | N/A | (−10 + 30)/−30 = −66.7 % would read as a decline although the result improved |
| 0 / blank | any | N/A | division by nothing |

Consequence: compute variances on **display-signed** values, not on the stored P&L sign.
Revenue, costs and profit subtotals are compared as an IBCS P&L shows them (costs positive),
via `'Report Line'[DisplaySign]` in `Report Value` (§9). Good/bad comes from polarity (costs
−1). Example: Material PL 20.8, AC 20.0 → ΔPL = −0.8, ΔPL% = −3.8 %, polarity −1 → good.
Only genuinely negative references (a loss) give N/A. An `ABS()` in the denominator is never
the fix.

The value parameters are deliberately **untyped** (`AnyVal`): a `NUMERIC` hint casts
implicitly and Learn doesn't state that BLANK survives the cast; if it became 0 the
`ISBLANK` guards would stop working. Colour always comes from the absolute Δ, never from the
sign of a Δ%. A Δ of exactly 0 gets no colour.

In TMDL (`functions.tmdl`) the declaration name is quoted (`function 'Ibcs.Delta' = …`), the
call is not (`Ibcs.Delta ( a, b )`). UDF caveats (Learn, Oct 2026): no display folders or
hiding; composite-model measures can't call UDFs of the source model; OLS does not propagate
to functions.

## 2. Base measure that defaults to AC

```dax
Amount =
IF (
    ISFILTERED ( Scenario ),
    SUM ( Finance[AmountGC] ),
    CALCULATE ( SUM ( Finance[AmountGC] ), Scenario[ScenarioType] = "AC" )
)
```

Without the guard a bare card shows AC + BU + FC + PL summed. Also set
`multipleOrEmptySelectionExpression = BLANK ()` on the calc group: when a slicer selects
several items without putting them on an axis (or a matrix subtotals across items), the group
would otherwise not apply and the visual would silently show AC. A user slicing
`Scenario[ScenarioType]` to two types still sums them: keep `Scenario` attributes hidden from
report authors or out of slicers. Every calc item filters `Scenario`, so inside an item the
plain `SUM` runs. Alternative: the calc group's `noSelectionExpression` (TMDL property of
`calculationGroup`), which is cleaner but applies only when the group is unfiltered, not when
a user slices `Scenario` directly.

## 3. Scenario items

Every item starts with a helper bypass so string/colour measures survive:
`IF ( Ibcs.IsHelper ( SELECTEDMEASURENAME () ), SELECTEDMEASURE (), … )` (helpers are named
`fx …`). Without it, a ΔPY item applied to a colour measure tries to subtract two strings.

```dax
-- AC / BU / PL
CALCULATE ( SELECTEDMEASURE (), REMOVEFILTERS ( Scenario ), Scenario[ScenarioType] = "BU" )
-- add Scenario[IsCurrent] = TRUE () when several budget revisions cover the same year

-- FC with a disconnected version picker; no selection = latest
VAR latestFc =
    CALCULATE ( MAX ( Scenario[ScenarioKey] ), REMOVEFILTERS ( Scenario ),
                Scenario[ScenarioType] = "FC", Scenario[IsLatestFC] = TRUE () )
VAR fcKey = SELECTEDVALUE ( 'FC Version'[ScenarioKey], latestFc )
RETURN CALCULATE ( SELECTEDMEASURE (), REMOVEFILTERS ( Scenario ), Scenario[ScenarioKey] = fcKey )
```

**PY**, pick by calendar type:

| Calendar | PY item body |
|---|---|
| Gregorian or shifted Gregorian (Jul–Jun) | `CALCULATE ( SELECTEDMEASURE (), REMOVEFILTERS ( Scenario ), Scenario[ScenarioType] = "AC", SAMEPERIODLASTYEAR ( 'Date'[Date] ) )` |
| 4-4-5, 13 periods, any custom periods | offset on `FiscalPeriodSeq` (below) |
| Calendar-based time intelligence (**preview**) | `SAMEPERIODLASTYEAR ( 'Fiscal' )` with a calendar defined on `Date`; not in live/composite models |

```dax
VAR periodsPerYear = 12                      -- 13 for 13-period calendars
VAR pySeq = SELECTCOLUMNS ( VALUES ( 'Date'[FiscalPeriodSeq] ), "s", 'Date'[FiscalPeriodSeq] - periodsPerYear )
RETURN
    CALCULATE ( SELECTEDMEASURE (), REMOVEFILTERS ( Scenario ), Scenario[ScenarioType] = "AC",
                REMOVEFILTERS ( 'Date' ), TREATAS ( pySeq, 'Date'[FiscalPeriodSeq] ) )
```

PY means "AC shifted", so it follows restatements of last year automatically. Never store it.

## 4. AC+FC without breaking ratios or Time Calc

```dax
VAR acKey = CALCULATE ( MAX ( Scenario[ScenarioKey] ), REMOVEFILTERS ( Scenario ), Scenario[ScenarioType] = "AC" )
VAR fcKey = …                                   -- as in the FC item
VAR lastClosed = CALCULATE ( MAX ( 'Date'[Date] ), REMOVEFILTERS ( 'Date' ), 'Date'[IsClosedPeriod] = TRUE () )
RETURN
    CALCULATE (
        SELECTEDMEASURE (),
        REMOVEFILTERS ( Scenario ),
        Scenario[ScenarioKey] IN { acKey, fcKey },
        KEEPFILTERS ( FILTER ( ALL ( Finance[ScenarioKey], Finance[PeriodDate] ),
            ( Finance[ScenarioKey] = acKey && Finance[PeriodDate] <= lastClosed )
                || ( Finance[ScenarioKey] = fcKey && Finance[PeriodDate] > lastClosed ) ) )
    )
```

Why this shape and not `[AC before cut-off] + [FC after cut-off]`:

1. **Ratios**: adding two margins is wrong; one CALCULATE computes the ratio of the combined
   numerator and denominator.
2. **Time Calc**: the inner YTD/FY items do `REMOVEFILTERS ( 'Date' )`. A cut-off placed on a
   `Date` column would be wiped; a cut-off on the **fact** date column survives.
3. **Marked date table**: a filter on `'Date'[Date]` inside CALCULATE adds an implicit
   `REMOVEFILTERS ( 'Date' )`, which can silently drop the month filter. Filter non-key date
   columns or the fact column instead.

With "n+m" forecast versions (months 1..n copied from AC), the FC version already *is* the
projection at forecast time; AC+FC differs only when AC was corrected afterwards.

`lastClosed` comes from the **closed-period flag** (ERP period status), never from the latest
fact date: the open month, with some AC already booked, is an FC month and its partial AC is
neither drawn nor added. PY for those FC months is the **full** month of last year (the PY item
of §3 already is); a like-for-like PY cut at the data timestamp is wrong there. `AC+FC` is the
item name; visuals label the series `AC&FC` (the IBCS notation), same scenario. For models with
explicit measures instead of this item, use the per-month `SUMX` pattern in
[visual-data-contract.md](visual-data-contract.md) §0.7.

## 5. Time Calc items (precedence below Scenario Analysis)

Offset-based so they work for any fiscal calendar. The reporting month in context is the
anchor; read `MAX` values **before** removing filters.

```dax
-- YTD
VAR fy = MAX ( 'Date'[FiscalYearNo] )
VAR lastSeq = MAX ( 'Date'[FiscalPeriodSeq] )
RETURN CALCULATE ( SELECTEDMEASURE (), REMOVEFILTERS ( 'Date' ),
                   'Date'[FiscalYearNo] = fy, 'Date'[FiscalPeriodSeq] <= lastSeq )
-- R12:  'Date'[FiscalPeriodSeq] > lastSeq - 12 && <= lastSeq
-- FY:   'Date'[FiscalYearNo] = fy
-- YTG:  'Date'[FiscalYearNo] = fy, 'Date'[FiscalPeriodSeq] > lastSeq
-- QTD:  + 'Date'[FiscalQuarterNo] = MAX ( 'Date'[FiscalQuarterNo] )
```

Precedence: higher precedence = outer wrapper. Scenario Analysis 20 wraps Time Calc 10, so
`PY × YTD` = YTD evaluated in the shifted (PY) context = PY YTD to the same month, and
`ΔPY% × YTD` = (AC YTD − PY YTD) / PY YTD. The format string of the highest-precedence item
that defines one wins; give Time Calc items no format string.

**Anchor without a month.** With no Date filter `MAX ( FiscalPeriodSeq )` is the last
calendar row (end of the date table) and YTD comes back BLANK. Fall back to the last closed
period: `IF ( ISFILTERED ( 'Date' ), MAX ( … ), CALCULATE ( MAX ( … ), REMOVEFILTERS ( 'Date' ), 'Date'[IsClosedPeriod] = TRUE () ) )`.

**Whole-year views.** Under FY and YTG the AC side covers only closed months while BU/PY/FC
cover the full year. The variance items therefore use **AC+FC as their minuend, always** (§6):
AC for every closed month and FC after it. For Period, YTD, QTD and R12 views that end in a
closed month this is exactly AC; under FY and YTG it is the IBCS year-end view. ΔFC keeps AC as
minuend (under YTG, AC+FC minus FC is 0). R12 vs FC stays partial when FC versions only cover
the current year: show ΔFC on YTD views.

Do **not** pick the minuend from the Time Calc selection inside the Scenario Analysis items
(`IF ( SELECTEDVALUE ( 'Time Calc'[Period] ) IN { "FY", "YTG" }, "AC+FC", "AC" )`): in a tested
model in the Fabric engine (2026-10) reading the lower-precedence group inside the items
exhausted query memory. The constant AC+FC minuend gives the same numbers for closed periods
and needs no such read.

**Reporting-month rule.** Users pick one month (slicer on `Date[MonthLabel]`, default
`[fx Last Closed Month]`). If a whole year is in context, "YTD" means the full year for AC but
also for PY, so AC Jan–Sep would be compared with PY Jan–Dec. Either force a single month or
cap YTD with a dynamic "comparable periods" flag.

## 6. Variance items

```dax
-- ΔPY (absolute), percentage points for ratio measures; minuend AC+FC (= AC for closed periods)
-- (wrap in the §3 helper bypass, as in reference-model-tmdl.md §5)
Ibcs.PointsIfRatio (
    Ibcs.Delta (
        CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "AC+FC" ),
        CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "PY" ) ),
    SELECTEDMEASUREFORMATSTRING () )
-- formatStringDefinition = Ibcs.DeltaFormat ( SELECTEDMEASURE (), SELECTEDMEASURENAME (),
--                              SELECTEDMEASUREFORMATSTRING (), SELECTEDVALUE ( Scale[Scale], "k" ) )

-- ΔPY% (relative): same minuend
Ibcs.DeltaPct (
    CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "AC+FC" ),
    CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "PY" ) )
-- formatStringDefinition = Ibcs.DeltaPctFormat ( SELECTEDMEASURE (), SELECTEDMEASURENAME (), SELECTEDMEASUREFORMATSTRING () )

-- ΔPL / ΔBU (and their %): same, with "PL" / "BU" as subtrahend.
-- ΔFC / ΔFC%: minuend "AC" (AC+FC − FC would be 0 under YTG).
```

- An item may apply **another item of the same group** by filtering the group column; direct
  self-reference is blocked. This keeps each scenario defined once.
- FC as minuend: `FC-PL`, `(AC+FC)-BU`: same pattern with the other item names. Name an
  ambiguous minuend explicitly: "FC-PL", "(FC-PL)%".
- Format string expressions: values `Ibcs.ScaleFormat ( scale, FALSE )`; absolute variances
  signed `+#,0.0,,;-#,0.0,,;0.0` (m); ratios `+0.0" pp";-0.0" pp";0.0" pp"` (the value is already ×100, see
  `Ibcs.PointsIfRatio`); Δ% `+0.0%;-0.0%;0.0%`. The `,`
  scaling and `.`/`,` separators follow the model culture.
- **Rounded zero is unsigned.** A format string chooses its `+`/`-` section by the *unrounded*
  sign, so a ΔPY of 20 000 at scale m would print `+0.0`. `Ibcs.DeltaFormat` and
  `Ibcs.DeltaPctFormat` therefore take the item's value (`SELECTEDMEASURE ()`, which Learn
  documents for "expressions for calculation items or dynamic format strings":
  https://learn.microsoft.com/dax/selectedmeasure-function-dax) and return the unsigned zero
  format when the value rounds to zero at the printed scale and decimals (ibcs-notation, the
  zero-variance rule). Keep `Ibcs.ScaleDecimals` and `Ibcs.ScaleFormat` in step.
- Ratio detection by format string (`CONTAINSSTRING ( SELECTEDMEASUREFORMATSTRING (), "%" )`)
  keeps the calc group generic. Verify it in your build for measures with a *dynamic* format
  string (`Report Value`); if it misfires, test `SELECTEDVALUE ( 'Report Line'[LineType] ) = "Ratio"`
  instead. A measure name can't tell them apart: `Report Value` is one measure for ratio and
  currency lines alike.

## 7. Polarity, impact and colour

- Attribute `VarianceDirection` (+1 / −1 / 0) lives on the report line (or KPI table), set in
  SQL, and refers to the **displayed** value: revenue and profit lines +1, cost lines (shown
  positive) −1, statistical or balance-sheet movements 0 (neutral, blue).
- A Δ of exactly 0 gets no colour (`Ibcs.Impact` returns BLANK), never "bad". A Δ that
  **rounds** to zero at the displayed scale and decimals gets no colour either: `Ibcs.Impact`
  only sees the raw value, so the measure that knows the scale (below) blanks it, and an app or
  visual that knows its own decimals does the same (the `ibcs-web-charts` reference `impact.ts`).
- Polarity decides **colour only**. The plotted value and its direction stay arithmetic.
- Subtotal lines use their own direction; never aggregate directions of children.

```dax
fx Variance Impact =
VAR scenarioItem = SELECTEDVALUE ( 'Scenario Analysis'[Scenario] )
VAR absItem = SWITCH ( TRUE (),
    scenarioItem IN { "ΔPY", "ΔPY%" }, "ΔPY",  scenarioItem IN { "ΔPL", "ΔPL%" }, "ΔPL",
    scenarioItem IN { "ΔBU", "ΔBU%" }, "ΔBU",  scenarioItem IN { "ΔFC", "ΔFC%" }, "ΔFC",
    scenarioItem IN { "(AC+FC)-BU", "(AC+FC)-BU%" }, "(AC+FC)-BU",
    scenarioItem IN { "FC-PL", "(FC-PL)%" }, "FC-PL",
    scenarioItem IN { "ΔPY member", "ΔPY% member" }, "ΔPY member",
    scenarioItem IN { "ΔBU member", "ΔBU% member" }, "ΔBU member" )
VAR delta = IF ( NOT ISBLANK ( absItem ), CALCULATE ( [Report Value], 'Scenario Analysis'[Scenario] = absItem ) )
VAR scale = SELECTEDVALUE ( Scale[Scale], "k" )
VAR shown =                                    -- the Δ as printed: ratio lines in pp (×100 by PointsIfRatio)
    IF ( SELECTEDVALUE ( 'Report Line'[LineType] ) = "Ratio",
        ROUND ( delta, 1 ),
        ROUND ( delta / Ibcs.ScaleDivisor ( scale ), Ibcs.ScaleDecimals ( scale ) ) )
RETURN IF ( shown <> 0, Ibcs.Impact ( delta, SELECTEDVALUE ( 'Report Line'[VarianceDirection], 1 ) ) )

fx Variance Colour      = Ibcs.ImpactColour ( [fx Variance Impact] )       -- bars, pins, markers only
fx Variance Text Colour = Ibcs.ImpactTextColour ( [fx Variance Impact] )   -- font colour of variance numbers
```

Bind `fx Variance Text Colour` to font colour (matrix and table cells, data labels) and
`fx Variance Colour` to bar and marker fills only: the graphic green is about 2.4:1 on white,
the text tokens are at least 4.5:1 (ibcs-notation, tinted numbers).

Hex values come from the organisation's notation tokens (the `ibcs-notation` skill in plugin
`ibcs` ships a default token file and an overrides mechanism); the green/red/blue roles are
the IBCS convention. Accessible variant: green → blue-green; no colour: good light grey,
neutral medium grey, bad dark grey.

## 8. Unit scaling and titles

- One scale per object, stated in the title (`mEUR`). Values stay unscaled; only the format
  string divides (`,` = ÷1 000 in en-US format strings).
- Disconnected `Scale` table (`1`, `k`, `m`, `bn`) and the format expressions in §6.
- Automatic scale per visual (no slicer):

```dax
fx Auto Scale =
VAR maxAbs = MAXX ( ALLSELECTED ( 'Report Line'[LineCode] ), ABS ( [Report Value] ) )
RETURN SWITCH ( TRUE (), maxAbs >= 1e9, "bn", maxAbs >= 1e6, "m", maxAbs >= 1e3, "k", "1" )
```

- Title helpers: `fx Unit Label` (scale + group currency, e.g. `mEUR`), `fx Last Closed Month`
  (`2026-09`). Title line 3 text such as `2026-09 YTD AC, PY, BU` belongs to the report/app,
  built from the selected items; keep titles descriptive (the message goes in the
  key-message element, see the `ibcs-composition` skill in plugin `ibcs`).

## 9. Report lines and the calculation waterfall

```dax
Report Value =                                   -- DISPLAY-signed: costs positive
VAR lineType = SELECTEDVALUE ( 'Report Line'[LineType] )
VAR lineCode = SELECTEDVALUE ( 'Report Line'[LineCode] )
VAR displaySign = SELECTEDVALUE ( 'Report Line'[DisplaySign], 1 )
RETURN
    IF ( HASONEVALUE ( 'Report Line'[LineCode] ),
        IF ( lineType = "Ratio",
            SWITCH ( lineCode,
                "EBIT_M", DIVIDE (
                    CALCULATE ( [Amount], REMOVEFILTERS ( 'Report Line' ), 'Report Line'[LineCode] = "EBIT" ),
                    CALCULATE ( [Amount], REMOVEFILTERS ( 'Report Line' ), 'Report Line'[LineCode] = "REV" ) ) ),
            displaySign * [Amount] ) )
-- formatStringDefinition: IF ( … = "Ratio", "0.0%", Ibcs.ScaleFormat ( SELECTEDVALUE ( Scale[Scale], "k" ), FALSE ) )
```

- `REMOVEFILTERS ( 'Report Line' )`, not just a new `LineCode` filter: matrix rows filter
  `LineName`, which would intersect to nothing.
- Subtotals are plain sums because the bridge maps a subtotal to every account above it and
  amounts are **stored** in P&L sign; `DisplaySign` (+1 for profit lines, −1 for cost lines)
  turns them into what the P&L shows. A loss subtotal stays negative (its Δ% is N/A).
- "Of which" and "percent of" rows: add `LineType` values `OfWhich` (sum of a subset,
  excluded from running sums) and `PercentOf` (DIVIDE by a `BaseLineCode`).

Calculation waterfall (detail bars float, subtotals from the axis). Bar **positions** are in
stored P&L sign so costs go down; labels use `Report Value`:

```dax
WF Start =
VAR lineType = SELECTEDVALUE ( 'Report Line'[LineType] )
VAR sortNo   = SELECTEDVALUE ( 'Report Line'[SortOrder] )
RETURN SWITCH ( lineType,
    "Detail", COALESCE ( CALCULATE ( [Amount], REMOVEFILTERS ( 'Report Line' ),
                         'Report Line'[LineType] = "Detail", 'Report Line'[SortOrder] < sortNo ), 0 ),
    "Subtotal", 0, "Total", 0 )

WF End = IF ( SELECTEDVALUE ( 'Report Line'[LineType] ) IN { "Detail", "Subtotal", "Total" },
              [WF Start] + [Amount] )                -- [Amount] = stored P&L-sign line amount
```

Variance waterfall (PY → contributions → AC) needs `PY + Σ Δ = AC`; compute running sums in
the visual/app from ordered rows, or with `WINDOW`/visual calculations
(`RUNNINGSUM ( [ΔPY] )`).

## 10. Structure analyses

- **Variances of structure rows reconcile.** Rows that explain a total (bars by member, bridge
  steps, stacked segments) use `Ibcs.DeltaMember` (§1): a discontinued member (reference but no
  actual) keeps 0 − reference and a new member actual − 0. With `Ibcs.Delta` those rows are BLANK
  and the rows no longer add up to the total Δ. The remainder ("Others") row is the total minus the shown members, never a sum
  of blanks.
  In the calc group these are their own items, so the plain ΔPY/ΔBU items keep the
  "no variance against nothing" rule for KPIs and time series:

```dax
-- 'ΔBU member' (ordinal after ΔBU%): rows that must add up to the total ΔBU
IF ( Ibcs.IsHelper ( SELECTEDMEASURENAME () ), SELECTEDMEASURE (),
    VAR ac  = CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "AC+FC" )
    VAR ref = CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "BU" )
    -- the reference has data for this period at all: remove the STRUCTURE dimensions only
    -- (list yours; never 'Date' or the measure's own filters such as 'Report Line')
    VAR refExists = NOT ISBLANK ( CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "BU",
                                              REMOVEFILTERS ( Entity ), REMOVEFILTERS ( Account ) ) )
    RETURN Ibcs.PointsIfRatio ( Ibcs.DeltaMember ( ac, ref, refExists ), SELECTEDMEASUREFORMATSTRING () ) )
-- formatStringDefinition: as ΔBU

-- 'ΔBU% member': a discontinued member is −100 %, a new member N/A (reference blank)
IF ( Ibcs.IsHelper ( SELECTEDMEASURENAME () ), SELECTEDMEASURE (),
    VAR ac  = CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "AC+FC" )
    VAR ref = CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "BU" )
    RETURN IF ( NOT ( ISBLANK ( ac ) && ISBLANK ( ref ) ), Ibcs.DeltaPct ( COALESCE ( ac, 0 ), ref ) ) )
-- formatStringDefinition: as ΔBU%
-- 'ΔPY member' / 'ΔPY% member': the same with "PY".
```

  Use the member items in structure bars, bridge steps and stacked segments (the queries in
  [visual-data-contract.md](visual-data-contract.md) §2); keep ΔBU/ΔPY for KPI cards, tables and
  time series. `fx Variance Impact` maps `ΔBU member` and `ΔBU% member` to `ΔBU member` (§7).
- **Field parameter** `Structure` over `Entity[EntityName]`, `Entity[Region]`,
  `Account[AccountName]`, `'Report Line'[LineName]`: one slicer, one bar chart. Field
  parameters are report-level objects: Fabric Apps can't use them (send the column instead).
- **Top N + remainder** in a Power BI visual: disconnected category table with an extra
  "Other" member, or visual calculations:

```dax
-- visual calculation on a bar chart sorted by AC
Rank = RANK ( DENSE, ROWS, ORDERBY ( [AC], DESC ) )
```

  The model-side pattern (needed when the remainder must also appear in exports):

```dax
AC TopN with Other =
VAR n = 10
VAR cat = SELECTEDVALUE ( 'Account Group'[Category] )          -- disconnected: accounts + "Other"
VAR ranked = FILTER ( ADDCOLUMNS ( ALLSELECTED ( Account[AccountName] ), "@v", [Report Value] ),
                     NOT ISBLANK ( [@v] ) )                    -- blanks never take a top slot
VAR topSet = TOPN ( n, ranked, [@v], DESC, Account[AccountName], ASC )
-- TOPN returns every row tied at rank n; the unique name as second sort key breaks the tie,
-- so exactly n members are returned
RETURN
    IF ( cat = "Other",
        SUMX ( EXCEPT ( ranked, topSet ), [@v] ),
        IF ( cat IN SELECTCOLUMNS ( topSet, "c", Account[AccountName] ),
             CALCULATE ( [Report Value], TREATAS ( { cat }, Account[AccountName] ) ) ) )
```

  Exclude the remainder from ranks, averages and selections.

## 11. Grain guards (option B models with separate plan facts)

```dax
-- plan stored per month: hide below month
BU (guarded) =
VAR daysSelected = COUNTROWS ( 'Date' )
VAR daysInMonths = CALCULATE ( COUNTROWS ( 'Date' ), REMOVEFILTERS ( 'Date' ), VALUES ( 'Date'[YearMonth] ) )
-- (ALLEXCEPT would drop a filter placed on MonthLabel and blank the plan at month level)
RETURN IF ( daysSelected = daysInMonths, [BU] )

-- plan without a Customer dimension: only at "all customers"
BU (no customer) = IF ( NOT ISCROSSFILTERED ( Customer ), [BU] )
```

With the one-fact design (option A) put plan rows on the `-2 Not applicable` member of
dimensions the plan lacks, and keep the fact at month grain, so no guards are needed.

## 12. Currency

- Standard conversion happens in SQL (AmountGC at average/closing/budget rate). The model
  sums.
- **FX-neutral ΔBU**: store `AmountGC_BudgetRate` for AC in the fact; add an item
  `ΔBU (FX-neutral)` that swaps the AC side to that column via a second base measure.
- **Constant-currency ΔPY**: store `AmountGC_CYRate` (PY converted at current-year rates).
- Dynamic report currency (rare): see the currency-conversion UDF example on Learn.

## 13. Explicit measures when a calc group is not an option

Excel users on old clients, some custom visuals, or a Fabric App that wants fixed columns:
create `Revenue AC`, `Revenue ΔPY`, … as thin wrappers over the calc items, so there is still
one definition:

```dax
Revenue ΔPY% = CALCULATE ( [Revenue], 'Scenario Analysis'[Scenario] = "ΔPY%" )
-- formatString: +0.0%;-0.0%;0.0%   displayFolder: 2 KPIs\Revenue\Variances
```

Generate them with a Tabular Editor C# script rather than by hand. Query shapes for models that only have explicit
measures (wide columns, long KPI rows with `UNION ( ROW … )`, impact via
`Ibcs.Impact ( Δ, [X Polarity] )`): [visual-data-contract.md](visual-data-contract.md) §0.7.

## 14. Test queries and traps

Unit test in DAX query view (or `executeQueries` in CI) against totals you computed in SQL
for your test data:

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Report Line'[LineCode],
    'Scenario Analysis'[Scenario],
    TREATAS ( { "REV", "GP", "EBIT", "NET", "EBIT_M" }, 'Report Line'[LineCode] ),
    TREATAS ( { "AC", "PY", "BU", "ΔPY", "ΔPY%", "ΔBU", "ΔBU%" }, 'Scenario Analysis'[Scenario] ),
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    "Value", [Report Value]
)
```

Invariants worth asserting in CI:

| Invariant | Query idea |
|---|---|
| ΔPY = AC − PY on every line | compare item values |
| Subtotal = Σ details above | `WF End` of the last detail = `Report Value` of the subtotal |
| Σ AC (model) = Σ AC (SQL gold) per entity/month | DAX vs the SQL load checks ([05_checks.sql](../../sql-reporting-backend/assets/sql/05_checks.sql)) |
| No scenario summing | `[Amount]` with no filters = AC only |
| RLS | `EVALUATE` under `Entity Controller` with a test user (e.g. `controller@example.com`) mapped to one entity returns that entity only |

Traps:

- Filter on the marked date column inside CALCULATE (§4).
- Calc items applied to text/colour measures (§3 helper bypass).
- `SELECTEDMEASUREFORMATSTRING ()` returns the measure's format; the calc-group format of the
  **highest precedence** item wins.
- `SUMMARIZECOLUMNS` drops all-blank rows; never "fix" with `+ 0`.
- Calendar-based time intelligence was **preview** in Oct 2026: not in live-connected or
  composite models; nested calendar time-intelligence functions need `CALCULATETABLE`.
- Direct Lake on SQL with SQL-endpoint RLS falls back to DirectQuery: define RLS in the model.
