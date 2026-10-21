# SVG-in-DAX skeletons

Starting points, not a library. Test status per skeleton (as of 2026-10):

| Skeleton | Status |
|---|---|
| 1 Absolute variance bar | SVG markup render-checked with sample values (harness below); DAX not run in Desktop |
| 2 Relative variance pin | written for illustration; **untested** |
| 3 AC/FC columns (slicer or card) | written for illustration; **untested** |
| 4 KPI card (absolute, percentage-point and ratio variants, highlight ellipse) | ran against a live model and rendered in the Power BI service in an end-to-end test |
| 5 AC bar, BU outlined behind, PY triangle | SVG markup render-checked with sample values; the same pattern ran against a live model in an end-to-end test |
| 7 Key message (bold, impact-coloured numbers, two lines) | Rendered in the service in a page-shell header (2026-10, PDF export), two lines, coloured numbers |
| 8 Category row with all tiers (bars, Δ bar, Δ% pin) + header row | Rendered in the service as a company block (2026-10, PDF export): six rows, shared px per unit with the month chart, highlight ellipse |

"Render-checked" means: the string the DAX builds was reproduced with literal sample values and
drawn with `scripts/svg_preview.py` in headless Chrome. Before use, evaluate each measure against
your model with the preview harness (last section) and open it in Desktop.

Table and column names (`'Company'[Company]`, `'Account'[Polarity]`, `'Date'[Month Index]`,
`[Revenue]`, `[Revenue PY]`, `[Revenue BU]`) are placeholders for your model. The hex values in the
`-- TOKENS` blocks are the defaults of the bundled `ibcs-tokens.json`; replace them with your
effective token values (or generate the block from the tokens).

Shared conventions:
- `Polarity` per account: 1 = higher is better, −1 = lower is better, 0 = neutral/ambiguous.
- Geometry follows the arithmetic sign of the variance; polarity only selects the colour.
- No variance unless both operands are non-blank: a BLANK AC draws no mark (not −PY).
- **Scaled values only:** every printed number is divided by the display unit (`_Div`, e.g. 1E6
  for millions) and rounded to the fixed decimals of its scale group; never print raw values.
  The unit goes in the title or the card's unit line.
- **Rounded zero:** a Δ that rounds to 0 at display precision gets no impact colour, no sign and
  the default text colour (`0.0`, `0.0%`, `0.00` for ratios), the zero-variance rule of
  ibcs-notation: compare the ROUNDed value with 0 (`_D1 = 0`), never the raw value, and never print
  `+0.00`.
- **Variance numbers as text** may be tinted only with the text variants of the impact colours
  (`color.variance.goodText` / `badText` / `neutralText`, ≥ 4.5:1 contrast); otherwise black.
  Bars, pins and markers keep the graphic colours.
- The axis is drawn first, so every mark sits in front of it.
- Δ% divides by the **signed** reference; N/A when the reference is 0 or negative (a sign
  change makes the percentage uninterpretable).
- Pins and triangles: sizes are clamped in px (pin stem 2–4, head 6–10, triangle 6–12; tokens
  `geometry.pin.stemPx`, `geometry.pin.headPx`, `geometry.triangleSizePx`).
- `FORMAT ( x, "0.0", "en-US" )` for every coordinate (locale-safe); labels use en-US and then
  swap the thousands separator for the token one (`UNICHAR ( 8239 )`, narrow no-break space).

## Contents
- [1. Absolute variance bar, shared scale, PY or BU axis](#1-absolute-variance-bar-shared-scale-py-or-bu-axis)
- [2. Relative variance pin with N/A](#2-relative-variance-pin-with-na)
- [3. AC/FC columns with hatched FC and PY behind (button slicer or card)](#3-acfc-columns-with-hatched-fc-and-py-behind-button-slicer-or-card)
- [4. KPI card (one card per measure)](#4-kpi-card-one-card-per-measure)
- [5. AC bar in front of an outlined BU bar, PY triangle](#5-ac-bar-in-front-of-an-outlined-bu-bar-py-triangle)
- [6. Budget progress bar (BAC, budget to date, AC to date)](#6-budget-progress-bar-bac-budget-to-date-ac-to-date)
- [7. Key message with impact-coloured numbers](#7-key-message-with-impact-coloured-numbers)
- [8. One row per category with all tiers, plus a header row](#8-one-row-per-category-with-all-tiers-plus-a-header-row)
- [9. Variance waterfall with a magnifying glass (two visuals)](#9-variance-waterfall-with-a-magnifying-glass-two-visuals)
- [Shared row geometry (GEOM) and px per unit](#shared-row-geometry-geom-and-px-per-unit)
- [Preview harness](#preview-harness)

## 1. Absolute variance bar, shared scale, PY or BU axis

```dax
SVG ΔPY Bar =
-- TOKENS
VAR _Good = "#8CB400"  VAR _Bad = "#FF0000"  VAR _Neutral = "#0064FF"
VAR _AxisPY = "#A6A6A6"  VAR _Text = "#000000"  VAR _Font = "Segoe UI"  VAR _Thou = UNICHAR ( 8239 )
-- CONFIG
VAR _Rows   = ALLSELECTED ( 'Company'[Company] )
VAR _InRow  = ISINSCOPE ( 'Company'[Company] )                  -- totals row: no bar (other scale)
VAR _AC     = [Revenue]
VAR _PY     = [Revenue PY]
VAR _Div    = 1E6                                               -- display unit (millions)
VAR _Var    = IF ( NOT ISBLANK ( _AC ) && NOT ISBLANK ( _PY ), _AC - _PY )   -- BLANK AC: no mark
VAR _R      = ROUND ( _Var / _Div, 1 )                          -- value at display precision
VAR _Pol    = SELECTEDVALUE ( 'Account'[Polarity], 1 )
VAR _W = 200  VAR _H = 20  VAR _Pad = 40                        -- room for labels
-- SCALE: same maximum for every row (UN 4.1)
VAR _MaxAbs = MAXX ( _Rows, VAR a = [Revenue] VAR p = [Revenue PY] RETURN IF ( NOT ISBLANK ( a ) && NOT ISBLANK ( p ), ABS ( a - p ) ) )
VAR _Axis   = _W / 2
VAR _Len    = DIVIDE ( ABS ( _Var ), _MaxAbs ) * ( _W / 2 - _Pad )
VAR _X      = IF ( _Var >= 0, _Axis, _Axis - _Len )
VAR _Col    = SWITCH ( TRUE (), _R = 0, "none", _Pol = 0, _Neutral, _Var * _Pol > 0, _Good, _Bad )   -- rounds to 0: no colour
VAR _Lbl    = IF ( _R = 0, "0.0", SUBSTITUTE ( FORMAT ( _R, "+#,0.0;-#,0.0", "en-US" ), ",", _Thou ) )
VAR _LblX   = IF ( _Var >= 0, _Axis + _Len + 3, _Axis - _Len - 3 )
VAR _Anchor = IF ( _Var >= 0, "start", "end" )
RETURN
IF ( _InRow && NOT ISBLANK ( _Var ),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W & "' height='" & _H
    & "' viewBox='0 0 " & _W & " " & _H & "'>"
    & "<desc>" & FORMAT ( _Var / _Div + 1E9, "0000000000.000", "en-US" ) & "</desc>"      -- sort key
    & "<rect x='" & FORMAT ( _Axis - 1.5, "0.0", "en-US" ) & "' y='0' width='3' height='" & _H
    & "' fill='" & _AxisPY & "'/>"                                                        -- PY axis: solid light
    & IF ( _R <> 0, "<rect x='" & FORMAT ( _X, "0.0", "en-US" ) & "' y='3' width='" & FORMAT ( _Len, "0.0", "en-US" )
        & "' height='" & ( _H - 6 ) & "' fill='" & _Col & "'/>" )
    & "<text x='" & FORMAT ( _LblX, "0.0", "en-US" ) & "' y='" & FORMAT ( _H / 2 + 4, "0.0", "en-US" )
    & "' font-family='" & _Font & "' font-size='11' fill='" & _Text & "' text-anchor='" & _Anchor & "'>"
    & _Lbl & "</text></svg>"
)
```

For a **PL or BU reference axis** (outlined), replace the PY axis rect with two 1-px rects at
`_Axis - 2.5` and `_Axis + 1.5` (token `stroke.varianceAxis.plGapPx` 3 between them) in the PL
stroke colour, and start the bars outside the double line so they never cover it: positive bars at
`_Axis + 2.5`, negative bars end at `_Axis - 2.5` (`_X = IF ( _Var >= 0, _Axis + 2.5, _Axis - 2.5 - _Len )`,
labels shifted by the same 2.5 px). The totals row returns BLANK (`ISINSCOPE` guard): a total on the
rows' scale would overflow; show it as a number, or as its own visual with its own scale. To put the variance bars **on the same px per unit as an AC bar column**
(skeleton 5), replace the `_MaxAbs` scaling with that column's px per unit (`_S` of skeleton 5,
or the page scale group's px per unit, the value Deneb members get as `pxPerUnit`): bar length =
`ABS ( _Var ) * _S`, and the column's own width = its own range × `_S` + label room. Do not give
the variance column the AC column's max at its own width: that is a shared domain, not a shared
scale. For an **FC variance**, fill the bar with a hatch `<pattern>` (see §3) in the
good/bad colour.

## 2. Relative variance pin with N/A

```dax
SVG ΔPY% Pin =
-- TOKENS
VAR _Good = "#8CB400"  VAR _Bad = "#FF0000"  VAR _Neutral = "#0064FF"
VAR _AxisPY = "#A6A6A6"  VAR _HeadAC = "#404040"  VAR _Font = "Segoe UI"
-- CONFIG
VAR _Rows = ALLSELECTED ( 'Company'[Company] )
VAR _AC   = [Revenue]
VAR _Ref  = [Revenue PY]
VAR _NA   = NOT ISBLANK ( _AC ) && ( ISBLANK ( _Ref ) || _Ref <= 0 )      -- signed reference: N/A when ≤ 0
VAR _Pct  = IF ( NOT _NA && NOT ISBLANK ( _AC ), DIVIDE ( _AC - _Ref, _Ref ) )   -- BLANK AC: no mark
VAR _R    = ROUND ( _Pct, 2 )                                          -- whole percent (use 3 for +0.0%)
VAR _Pol  = SELECTEDVALUE ( 'Account'[Polarity], 1 )
VAR _Max  = MAXX ( _Rows, VAR a = [Revenue] VAR r = [Revenue PY] RETURN IF ( NOT ISBLANK ( a ) && r > 0, ABS ( DIVIDE ( a - r, r ) ) ) )
VAR _W = 160  VAR _H = 20  VAR _Axis = _W / 2
VAR _Len  = DIVIDE ( ABS ( _Pct ), _Max ) * ( _W / 2 - 38 )
VAR _End  = IF ( _Pct >= 0, _Axis + _Len, _Axis - _Len )
VAR _Col  = SWITCH ( TRUE (), _R = 0, "none", _Pol = 0, _Neutral, _Pct * _Pol > 0, _Good, _Bad )   -- rounds to 0: no colour
VAR _Stem = 2                                                          -- clamp 2–4 px
VAR _Head = 6                                                          -- clamp 6–10 px
RETURN
SWITCH ( TRUE (),
    _NA,
        "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 " & _W & " " & _H & "'>"
        & "<text x='" & _Axis & "' y='14' font-family='" & _Font & "' font-size='10' text-anchor='middle'>N/A</text></svg>",
    ISBLANK ( _Pct ), BLANK (),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 " & _W & " " & _H & "'>"
    & "<desc>" & FORMAT ( _Pct + 1E6, "0000000.000000", "en-US" ) & "</desc>"
    & "<rect x='" & FORMAT ( _Axis - 1.5, "0.0", "en-US" ) & "' y='0' width='3' height='" & _H & "' fill='" & _AxisPY & "'/>"
    & "<line x1='" & FORMAT ( _Axis, "0.0", "en-US" ) & "' x2='" & FORMAT ( _End, "0.0", "en-US" )
    & "' y1='10' y2='10' stroke='" & _Col & "' stroke-width='" & _Stem & "'/>"
    & "<rect x='" & FORMAT ( _End - _Head / 2, "0.0", "en-US" ) & "' y='7' width='" & _Head & "' height='" & _Head
    & "' fill='" & _HeadAC & "'/>"                                                         -- head in the minuend's (AC) notation
    & "<text x='" & FORMAT ( IF ( _Pct >= 0, _End + 6, _End - 6 ), "0.0", "en-US" ) & "' y='13.5' font-family='" & _Font
    & "' font-size='10' text-anchor='" & IF ( _Pct >= 0, "start", "end" ) & "'>"
    & IF ( _R = 0, "0%", FORMAT ( _R, "+0%;-0%", "en-US" ) ) & "</text></svg>"
)
```

The pin's stem carries the impact colour; the head carries the minuend's scenario notation
(solid dark for AC, hatched for FC). Squares are the design shown in the IBCS figures; any
consistent head shape works.

## 3. AC/FC columns with hatched FC and PY behind (button slicer or card)

```dax
SVG AC FC PY Columns =
-- TOKENS
VAR _AC = "#404040"  VAR _PY = "#A6A6A6"  VAR _Ground = "#FFFFFF"  VAR _Font = "Segoe UI"
-- DATA
VAR _Div = 1E6                                                    -- display unit
-- CONFIG: 'Date'[Month Index] = your date table's month sort column; 'Company'[Company] = the
-- matrix row column (one chart per row). Replace both.
VAR _Months = SUMMARIZE ( ALLSELECTED ( 'Date' ), 'Date'[Month Index], 'Date'[Month Short] )
VAR _T =
    ADDCOLUMNS ( _Months, "@AC", [Revenue], "@FC", [Revenue FC], "@PY", [Revenue PY] )
VAR _W = 360  VAR _H = 140  VAR _Base = 120
VAR _N    = COUNTROWS ( _T )
VAR _Min  = MINX ( _T, 'Date'[Month Index] )
-- SCALE: one maximum over EVERY row of the matrix and every month (CO 4.4: a sparkline scaled to
-- its own row is not comparable). With a page scale group use GEOM _S instead: _K = _S.
VAR _Max  =
    MAXX (
        CROSSJOIN ( ALLSELECTED ( 'Company'[Company] ), _Months ),
        MAX ( MAX ( [Revenue], [Revenue FC] ), [Revenue PY] )
    )
VAR _HasData = NOT ISBLANK ( MAXX ( _T, MAX ( [@AC], [@FC] ) ) )   -- unknown member / no data: no chart
VAR _Step = DIVIDE ( _W, _N )
VAR _CW   = _Step * 2 / 3 * 0.8                                   -- 2/3 band, minus the overlap offset
VAR _K    = DIVIDE ( _Base - 18, _Max )
VAR _Defs =
    "<defs><pattern id='h' patternUnits='userSpaceOnUse' width='4' height='4' patternTransform='rotate(45)'>"
    & "<rect width='4' height='4' fill='" & _Ground & "'/><rect width='1.6' height='4' fill='" & _AC & "'/></pattern></defs>"
VAR _Bars =
    CONCATENATEX (
        _T,
        VAR _x    = ( 'Date'[Month Index] - _Min ) * _Step + ( _Step - _CW ) / 2
        VAR _isFC = ISBLANK ( [@AC] ) && NOT ISBLANK ( [@FC] )
        VAR _v    = IF ( _isFC, [@FC], [@AC] )
        VAR _hP   = [@PY] * _K
        VAR _hA   = _v * _K
        RETURN
            IF ( NOT ISBLANK ( [@PY] ),                                -- no PY (data start): no PY column
                "<rect x='" & FORMAT ( _x - 3, "0.0", "en-US" ) & "' y='" & FORMAT ( _Base - _hP, "0.0", "en-US" )
                & "' width='" & FORMAT ( _CW, "0.0", "en-US" ) & "' height='" & FORMAT ( _hP, "0.0", "en-US" ) & "' fill='" & _PY & "'/>" )
            & IF ( NOT ISBLANK ( _v ),                                 -- no AC and no FC: no column, no label
                "<rect x='" & FORMAT ( _x + 3, "0.0", "en-US" ) & "' y='" & FORMAT ( _Base - _hA, "0.0", "en-US" )
                & "' width='" & FORMAT ( _CW, "0.0", "en-US" ) & "' height='" & FORMAT ( _hA, "0.0", "en-US" )
                & "' fill='" & IF ( _isFC, "url(#h)", _AC ) & "' stroke='" & _AC & "' stroke-width='0.8'/>"
                & "<text x='" & FORMAT ( _x + 3 + _CW / 2, "0.0", "en-US" ) & "' y='" & FORMAT ( _Base - _hA - 3, "0.0", "en-US" )
                & "' font-family='" & _Font & "' font-size='8' text-anchor='middle'>" & FORMAT ( _v / _Div, "0.0", "en-US" ) & "</text>" )
            & "<text x='" & FORMAT ( _x + _CW / 2, "0.0", "en-US" ) & "' y='" & ( _Base + 12 )
            & "' font-family='" & _Font & "' font-size='8' text-anchor='middle'>" & 'Date'[Month Short] & "</text>",
        "",
        'Date'[Month Index], ASC
    )
RETURN
IF ( _HasData && NOT ISBLANK ( _Max ),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 " & _W & " " & _H & "'>"
    & _Defs
    & "<line x1='0' x2='" & _W & "' y1='" & _Base & "' y2='" & _Base & "' stroke='#000000' stroke-width='1'/>"   -- axis first
    & _Bars & "</svg>"
)
```

AC and FC are drawn after PY, so they sit in front (UN 4.1); the baseline is drawn before both.
Every row shares one scale (`_Max` over all rows and months, or GEOM `_S`), so a small entity's
chart is lower, never stretched to the same height (CO 4.4). A row without AC or FC (an unknown
member, an empty company) returns BLANK instead of an empty chart.
For a single large chart prefer a Deneb template; SVG suits small multiples of the same chart in
a matrix or a slicer.

## 4. KPI card (one card per measure)

The visual-spec type `kpi-cards` is a transposed variance table: one card per measure with
label, unit, the AC value, then one line per comparison with Δ% and Δ and the scenario code.
Power BI route: one SVG measure per card, all cards as image columns of one `tableEx` (one
row, `grid.imageWidth` / `imageHeight` = the card size, column headers off or the measure name),
so the cards share one visual, one font and one baseline. In the page shell
([page-shell.md](../../ibcs-power-bi/references/page-shell.md) §4) each card is its own `tableEx`
on its own white card instead (SVG 200 × 104, coordinates there), so the canvas shows between them.

```dax
SVG KPI Card Revenue =
-- TOKENS
VAR _Text = "#000000"  VAR _Text2 = "#595959"
VAR _GoodT = "#5A7A00"  VAR _BadT = "#D00000"  VAR _NeutralT = "#0064FF"   -- color.variance.*Text (≥ 4.5:1)
VAR _Font = "Segoe UI"  VAR _FontEm = "Segoe UI Semibold"
VAR _Thou = UNICHAR ( 8239 )  VAR _NA = "N/A"
-- CONFIG
VAR _Label = "Revenue"  VAR _Unit = "mEUR"
VAR _Div = 1E6                                   -- display unit: never print raw values
VAR _Fmt = "#,0.0"                               -- fixed decimals of the scale group (spec display setting wins)
VAR _Dec = 1                                     -- the same decimals for ROUND
VAR _Pol = 1                                     -- or a polarity measure: 1 / -1 / 0
VAR _AC  = [Revenue]
VAR _R1 = [Revenue PY]  VAR _C1 = "PY"
VAR _R2 = [Revenue BU]  VAR _C2 = "BU"
-- COMPARISONS (rounded at display precision: a Δ that rounds to 0 is unsigned and uncoloured)
VAR _D1 = IF ( NOT ISBLANK ( _AC ) && NOT ISBLANK ( _R1 ), ROUND ( ( _AC - _R1 ) / _Div, _Dec ) )
VAR _P1 = IF ( NOT ISBLANK ( _D1 ) && _R1 > 0, ROUND ( DIVIDE ( _AC - _R1, _R1 ), 3 ) )   -- BLANK = N/A
VAR _D2 = IF ( NOT ISBLANK ( _AC ) && NOT ISBLANK ( _R2 ), ROUND ( ( _AC - _R2 ) / _Div, _Dec ) )
VAR _P2 = IF ( NOT ISBLANK ( _D2 ) && _R2 > 0, ROUND ( DIVIDE ( _AC - _R2, _R2 ), 3 ) )
VAR _K1  = SWITCH ( TRUE (), _D1 = 0, _Text, _Pol = 0, _NeutralT, _D1 * _Pol > 0, _GoodT, _BadT )
VAR _KP1 = SWITCH ( TRUE (), ISBLANK ( _P1 ) || _P1 = 0, _Text, _Pol = 0, _NeutralT, _P1 * _Pol > 0, _GoodT, _BadT )
VAR _K2  = SWITCH ( TRUE (), _D2 = 0, _Text, _Pol = 0, _NeutralT, _D2 * _Pol > 0, _GoodT, _BadT )
VAR _KP2 = SWITCH ( TRUE (), ISBLANK ( _P2 ) || _P2 = 0, _Text, _Pol = 0, _NeutralT, _P2 * _Pol > 0, _GoodT, _BadT )
VAR _T1  = IF ( _D1 = 0, FORMAT ( 0, _Fmt, "en-US" ), SUBSTITUTE ( FORMAT ( _D1, "+" & _Fmt & ";-" & _Fmt, "en-US" ), ",", _Thou ) )
VAR _Q1  = IF ( ISBLANK ( _P1 ), _NA, IF ( _P1 = 0, "0.0%", FORMAT ( _P1, "+0.0%;-0.0%", "en-US" ) ) )
VAR _T2  = IF ( _D2 = 0, FORMAT ( 0, _Fmt, "en-US" ), SUBSTITUTE ( FORMAT ( _D2, "+" & _Fmt & ";-" & _Fmt, "en-US" ), ",", _Thou ) )
VAR _Q2  = IF ( ISBLANK ( _P2 ), _NA, IF ( _P2 = 0, "0.0%", FORMAT ( _P2, "+0.0%;-0.0%", "en-US" ) ) )
VAR _ACt = IF ( ISBLANK ( _AC ), "–", SUBSTITUTE ( FORMAT ( _AC / _Div, _Fmt, "en-US" ), ",", _Thou ) )
VAR _Row1 = IF ( NOT ISBLANK ( _D1 ),
    "<text x='100' y='78' text-anchor='end' fill='" & _KP1 & "'>" & _Q1 & "</text>"
    & "<text x='176' y='78' text-anchor='end' fill='" & _K1 & "'>" & _T1 & "</text>"
    & "<text x='184' y='78' fill='" & _Text & "'>Δ" & _C1 & "</text>" )
VAR _Row2 = IF ( NOT ISBLANK ( _D2 ),
    "<text x='100' y='96' text-anchor='end' fill='" & _KP2 & "'>" & _Q2 & "</text>"
    & "<text x='176' y='96' text-anchor='end' fill='" & _K2 & "'>" & _T2 & "</text>"
    & "<text x='184' y='96' fill='" & _Text & "'>Δ" & _C2 & "</text>" )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='104' viewBox='0 0 240 104'>"
    & "<g font-family='" & _Font & "' font-size='12'>"
    & "<text x='120' y='15' text-anchor='middle' fill='" & _Text & "'><tspan font-family='" & _FontEm & "'>"
    & _Label & "</tspan><tspan fill='" & _Text2 & "'> in " & _Unit & "</tspan></text>"
    & "<text x='120' y='52' text-anchor='middle' font-size='28' fill='" & _Text & "'>" & _ACt & "</text>"
    & _Row1 & _Row2 & "</g></svg>"
```

Model measures behind the card (polarity, Δ, Δ%) are preferred where they exist; the card only
formats. Cards of one row share `width`/`height` (= the `tableEx` `grid.imageWidth` /
`imageHeight`).

The variants below replace everything between `-- CONFIG` and `RETURN` of the card above; the
TOKENS block and the RETURN (title, unit line, AC value, `_Row1`, `_Row2`) stay as they are.

**Percentage card** (e.g. gross margin %): no Δ%, the Δ is in percentage points:
```dax
-- CONFIG
VAR _Label = "Gross margin %"  VAR _Unit = "%"
VAR _Pol = 1
VAR _AC  = [Gross Margin %] * 100                -- in percent
VAR _R1  = [Gross Margin % PY] * 100  VAR _C1 = "PY"
-- COMPARISON (percentage points, rounded at display precision)
VAR _ACt = IF ( ISBLANK ( _AC ), "–", FORMAT ( _AC, "0.0", "en-US" ) & "%" )
VAR _D1  = IF ( NOT ISBLANK ( _AC ) && NOT ISBLANK ( _R1 ), ROUND ( _AC - _R1, 1 ) )
VAR _T1  = IF ( _D1 = 0, "0.0pp", FORMAT ( _D1, "+0.0;-0.0", "en-US" ) & "pp" )
VAR _K1  = SWITCH ( TRUE (), _D1 = 0, _Text, _Pol = 0, _NeutralT, _D1 * _Pol > 0, _GoodT, _BadT )
VAR _Row1 = IF ( NOT ISBLANK ( _D1 ),
    "<text x='176' y='78' text-anchor='end' fill='" & _K1 & "'>" & _T1 & "</text>"
    & "<text x='184' y='78' fill='" & _Text & "'>Δ" & _C1 & "</text>" )
VAR _Row2 = ""
```

**Ratio card** (e.g. book-to-bill; token `number.format.plainRatio`): no unit divisor, no Δ%, the
Δ in ratio points at the ratio's decimals:
```dax
-- CONFIG
VAR _Label = "Book-to-bill"  VAR _Unit = "ratio"
VAR _Pol = 1
VAR _AC  = [Book To Bill]
VAR _R1  = [Book To Bill PY]  VAR _C1 = "PY"
-- COMPARISON (ratio points, rounded at display precision)
VAR _ACt = IF ( ISBLANK ( _AC ), "–", FORMAT ( _AC, "0.00", "en-US" ) )
VAR _D1  = IF ( NOT ISBLANK ( _AC ) && NOT ISBLANK ( _R1 ), ROUND ( _AC - _R1, 2 ) )
VAR _T1  = IF ( _D1 = 0, "0.00", FORMAT ( _D1, "+0.00;-0.00", "en-US" ) )
VAR _K1  = SWITCH ( TRUE (), _D1 = 0, _Text, _Pol = 0, _NeutralT, _D1 * _Pol > 0, _GoodT, _BadT )
VAR _Row1 = IF ( NOT ISBLANK ( _D1 ),
    "<text x='176' y='78' text-anchor='end' fill='" & _K1 & "'>" & _T1 & "</text>"
    & "<text x='184' y='78' fill='" & _Text & "'>Δ" & _C1 & "</text>" )
VAR _Row2 = ""
```
The RETURN's title line reads "… in ratio" here; write `_Unit = ""` and drop the `in` tspan if the
label alone says it.

**Highlight ellipse** (a value the key message names, SA 4.3): drawn before the text it circles,
sized from the label length (≈ 3.4 px per character at 12 px):
```dax
VAR _HL = "#0064FF"                              -- color.marker.highlight
VAR _Ell = "<ellipse cx='" & FORMAT ( 176 - LEN ( _T1 ) * 3.4, "0.0", "en-US" ) & "' cy='74' rx='"
    & FORMAT ( LEN ( _T1 ) * 3.4 + 6, "0.0", "en-US" ) & "' ry='9' fill='none' stroke='" & _HL
    & "' stroke-width='1.5'/>"
-- _Row1 = _Ell & "<text x='176' …>" & _T1 & …   (cx = the text's end x − half its width)
```

## 5. AC bar in front of an outlined BU bar, PY triangle

One row of a structure table (bars per company, card 23 with a third scenario as triangle). Its
px per unit `_S` also drives the ΔBU column (skeleton 1 with the BU axis, bar length = Δ × `_S`,
column width = its own Δ range × `_S` + label room), so both columns have the same px per unit.
In a page scale group, replace `_S` with the group's px per unit.

```dax
SVG AC BU PY Bar =
-- TOKENS
VAR _ACc = "#404040"  VAR _PYc = "#A6A6A6"  VAR _PLFill = "#FFFFFF"  VAR _PLStroke = "#404040"
VAR _Axis = "#404040"  VAR _Text = "#000000"  VAR _Font = "Segoe UI"  VAR _Thou = UNICHAR ( 8239 )
VAR _OffsetRatio = 0.25                                       -- geometry.referenceOffsetRatio.bar
VAR _TriRatio = 0.33  VAR _TriMin = 6  VAR _TriMax = 12       -- geometry.triangleSizeRatio / triangleSizePx
-- CONFIG
VAR _Rows = ALLSELECTED ( 'Company'[Company] )
VAR _AC = [Revenue]  VAR _BU = [Revenue BU]  VAR _PY = [Revenue PY]
VAR _Div = 1E6  VAR _Fmt = "#,0.0"
VAR _W = 360  VAR _H = 28  VAR _Room = 46                     -- label room right of the longest bar
-- SCALE: one px per unit for every row (UN 4.1)
VAR _Max = MAXX ( _Rows, MAX ( MAX ( [Revenue], [Revenue BU] ), [Revenue PY] ) )
VAR _S   = DIVIDE ( _W - _Room - 1, _Max )
VAR _T   = _H * 0.5                                           -- bar thickness
VAR _Off = _T * _OffsetRatio                                  -- BU shifted up behind AC
VAR _Tri = MIN ( MAX ( _TriRatio * _T, _TriMin ), _TriMax )   -- triangle height, clamped in px
VAR _Top = _Tri + 1                                           -- BU bar top; the triangle sits above it
VAR _TW  = _Tri * 1.15                                        -- triangle width
VAR _LX  = MAX ( COALESCE ( _AC, 0 ), COALESCE ( _BU, 0 ) ) * _S + 5
RETURN
IF ( NOT ISBLANK ( _AC ) || NOT ISBLANK ( _BU ),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W & "' height='" & _H
    & "' viewBox='0 0 " & _W & " " & _H & "'>"
    & "<desc>" & FORMAT ( COALESCE ( _AC, 0 ) / _Div + 1E9, "0000000000.000", "en-US" ) & "</desc>"   -- sort key
    & "<g font-family='" & _Font & "' font-size='11'>"
    & IF ( NOT ISBLANK ( _BU ), "<rect x='1' y='" & FORMAT ( _Top, "0.0", "en-US" ) & "' width='"
        & FORMAT ( _BU * _S, "0.0", "en-US" ) & "' height='" & FORMAT ( _T, "0.0", "en-US" )
        & "' fill='" & _PLFill & "' stroke='" & _PLStroke & "' stroke-width='1'/>" )                  -- BU outlined, behind
    & IF ( NOT ISBLANK ( _AC ), "<rect x='1' y='" & FORMAT ( _Top + _Off, "0.0", "en-US" ) & "' width='"
        & FORMAT ( _AC * _S, "0.0", "en-US" ) & "' height='" & FORMAT ( _T, "0.0", "en-US" )
        & "' fill='" & _ACc & "'/>" )                                                                 -- AC solid, in front
    & IF ( NOT ISBLANK ( _PY ), "<path d='M" & FORMAT ( _PY * _S + 1 - _TW / 2, "0.0", "en-US" ) & " "
        & FORMAT ( _Top - 1 - _Tri, "0.0", "en-US" ) & " L" & FORMAT ( _PY * _S + 1 + _TW / 2, "0.0", "en-US" ) & " "
        & FORMAT ( _Top - 1 - _Tri, "0.0", "en-US" ) & " L" & FORMAT ( _PY * _S + 1, "0.0", "en-US" ) & " "
        & FORMAT ( _Top - 1, "0.0", "en-US" ) & " Z' fill='" & _PYc & "'/>" )                         -- PY triangle, tip at PY
    & "<line x1='0.5' y1='0' x2='0.5' y2='" & _H & "' stroke='" & _Axis & "' stroke-width='1'/>"
    & IF ( NOT ISBLANK ( _AC ), "<text x='" & FORMAT ( _LX, "0.0", "en-US" ) & "' y='"
        & FORMAT ( _Top + _Off + _T / 2 + 4, "0.0", "en-US" ) & "' fill='" & _Text & "'>"
        & SUBSTITUTE ( FORMAT ( _AC / _Div, _Fmt, "en-US" ), ",", _Thou ) & "</text>" )
    & "</g></svg>"
)
```

The integrated legend (AC, BU, PY names) goes into the column header or the first row's
tooltip; a structure table rarely has room for it inside a 28 px row.

## 6. Budget progress bar (BAC, budget to date, AC to date)

One row of a project or cost-centre table: the outlined bar is the budget at completion (BAC),
the solid bar the actual inception to date (ITD), and a thin black tick the budget to date (what
should have been spent by now). The variance AC − budget to date is a separate skeleton-1 column
on the same `_S` (polarity −1 for costs: overspend red, bar to the right). The label shows the
actual (a dash when it is blank, never a false 0) and its share of BAC; the share is N/A when
BAC ≤ 0 or blank (signed reference). In a table with the shared GEOM block, `_S` is the group's
px per display unit and every length is value ÷ `_Div` × `_S`.

```dax
SVG Budget Progress =
-- TOKENS
VAR _ACc = "#404040"  VAR _PLFill = "#FFFFFF"  VAR _PLStroke = "#404040"  VAR _Tick = "#000000"
VAR _Axis = "#404040"  VAR _Text = "#000000"  VAR _Font = "Segoe UI"  VAR _Thou = UNICHAR ( 8239 )
VAR _NA = "N/A"
-- CONFIG
VAR _Rows = ALLSELECTED ( 'Project'[Project] )
VAR _BAC = [Budget At Completion]  VAR _BTD = [Budget To Date]  VAR _AC = [Actual ITD]
VAR _Div = 1E3  VAR _Fmt = "#,0"
-- GEOM (or paste the table's shared GEOM block)
VAR _W = 300  VAR _H = 28  VAR _Room = 84                     -- label room: "1 234 (56%)"
VAR _Max = MAXX ( _Rows, MAX ( MAX ( [Budget At Completion], [Budget To Date] ), [Actual ITD] ) ) / _Div
VAR _S   = DIVIDE ( _W - _Room - 1, _Max )                    -- px per display unit (after _Div), every row
VAR _T   = _H * 0.5
VAR _Y   = ( _H - _T ) / 2
VAR _Share = IF ( _BAC > 0 && NOT ISBLANK ( _AC ), DIVIDE ( _AC, _BAC ) )
VAR _LX  = MAX ( MAX ( COALESCE ( _AC, 0 ), COALESCE ( _BAC, 0 ) ), COALESCE ( _BTD, 0 ) ) / _Div * _S + 5
RETURN
IF ( NOT ISBLANK ( _AC ) || NOT ISBLANK ( _BAC ),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W & "' height='" & _H
    & "' viewBox='0 0 " & _W & " " & _H & "'>"
    & "<desc>" & FORMAT ( COALESCE ( _AC, 0 ) / _Div + 1E9, "0000000000.000", "en-US" ) & "</desc>"   -- sort key
    & "<g font-family='" & _Font & "' font-size='11'>"
    & IF ( _BAC > 0, "<rect x='1' y='" & FORMAT ( _Y, "0.0", "en-US" ) & "' width='"
        & FORMAT ( _BAC / _Div * _S, "0.0", "en-US" ) & "' height='" & FORMAT ( _T, "0.0", "en-US" )
        & "' fill='" & _PLFill & "' stroke='" & _PLStroke & "' stroke-width='1'/>" )                  -- BAC outlined
    & IF ( _AC > 0, "<rect x='1' y='" & FORMAT ( _Y + 3, "0.0", "en-US" ) & "' width='"
        & FORMAT ( _AC / _Div * _S, "0.0", "en-US" ) & "' height='" & FORMAT ( _T - 6, "0.0", "en-US" )
        & "' fill='" & _ACc & "'/>" )                                                                 -- AC to date, inside
    & IF ( _BTD > 0, "<line x1='" & FORMAT ( _BTD / _Div * _S + 1, "0.0", "en-US" ) & "' y1='"
        & FORMAT ( _Y - 3, "0.0", "en-US" ) & "' x2='" & FORMAT ( _BTD / _Div * _S + 1, "0.0", "en-US" ) & "' y2='"
        & FORMAT ( _Y + _T + 3, "0.0", "en-US" ) & "' stroke='" & _Tick & "' stroke-width='2'/>" )   -- budget to date
    & "<line x1='0.5' y1='0' x2='0.5' y2='" & _H & "' stroke='" & _Axis & "' stroke-width='1'/>"
    & "<text x='" & FORMAT ( _LX, "0.0", "en-US" ) & "' y='" & FORMAT ( _Y + _T / 2 + 4, "0.0", "en-US" )
    & "' fill='" & _Text & "'>" & IF ( ISBLANK ( _AC ), "–", SUBSTITUTE ( FORMAT ( _AC / _Div, _Fmt, "en-US" ), ",", _Thou ) )
    & " (" & IF ( ISBLANK ( _Share ), _NA, FORMAT ( _Share, "0%", "en-US" ) ) & ")</text>"
    & "</g></svg>"
)
```

Column header: "AC ■ BAC ▭ budget to date |" so the legend stays integrated. Negative actuals
(credits) draw no AC bar; show them in the variance column instead.

## 7. Key message with impact-coloured numbers

The key message (UN 2.1) as one bold sentence whose variance numbers carry the text impact
colours (`color.variance.goodText` / `badText` / `neutralText`), the rest black: the reader sees
at a glance which numbers are good or bad. A Power BI text box cannot colour a value by its sign,
and the new card colours a whole value, not parts of a sentence (as of 2026-10), so the sentence
is an SVG text with one `<tspan>` per part. It wraps at part boundaries onto at most `_Lines`
lines; a message that needs more ends in "…" (visible, so it gets shortened, never silently cut:
UN 2.1 wants at most two lines). Placement and size: the header card of
[page-shell.md](../../ibcs-power-bi/references/page-shell.md) (one image column in a `tableEx`,
`grid.imageWidth` = `_W`, `imageHeight` = `_Lines × _LineH + 4`, column width ≥ `_W` + 20).

Parts are the template slots of the message (`ibcs-composition`): text parts in `_Text`, each
signed variance its own part with `_Imp ( Δ )`. Line breaks happen only between parts, so keep a
number and its unit in one part. A part that starts a new line loses its leading space. A part
that starts with `)`, `,`, `.` or `;` never starts a line (it stays on the line it closes, even if
that line runs a few characters over `_Budget`): a line must not begin with punctuation.

```dax
SVG Key Message =
-- TOKENS
VAR _Text = "#000000"  VAR _GoodT = "#5A7A00"  VAR _BadT = "#D00000"  VAR _NeutralT = "#0064FF"   -- *Text variants
VAR _FontEm = "Segoe UI Semibold"
-- CONFIG
VAR _W = 1010  VAR _Size = 17  VAR _Lines = 2    -- width px, key message 13 pt ≈ 17 px, max lines (UN 2.1)
VAR _LineH = ROUND ( _Size * 1.3, 0 )
VAR _Budget = INT ( _W / ( _Size * 0.58 ) )      -- characters per line (Segoe UI Semibold ≈ 0.58 em per char)
VAR _Pol = 1  VAR _Div = 1E6  VAR _Fmt = "#,0.0"  VAR _Dec = 1
VAR _AC = [Revenue]  VAR _DPY = ROUND ( ( _AC - [Revenue PY] ) / _Div, _Dec )
VAR _PPY = IF ( [Revenue PY] > 0, ROUND ( DIVIDE ( _AC - [Revenue PY], [Revenue PY] ), 3 ) )   -- BLANK = N/A
-- impact text colour of a rounded variance (rounded zero: black)
VAR _K1 = SWITCH ( TRUE (), _DPY = 0, _Text, _Pol = 0, _NeutralT, _DPY * _Pol > 0, _GoodT, _BadT )
VAR _Num = IF ( _DPY = 0, "0.0", FORMAT ( _DPY, "+" & _Fmt & ";-" & _Fmt, "en-US" ) ) & " mEUR ("
    & IF ( ISBLANK ( _PPY ), "N/A", IF ( _PPY = 0, "0.0%", FORMAT ( _PPY, "+0.0%;-0.0%", "en-US" ) ) ) & ")"
    -- a rounded 0 is unsigned (a two-section format string would print +0.0%)
-- PARTS (text, colour); add or drop blocks of three VARs as the template needs
VAR _T1 = "Revenue " & [Period Label] & " is " & FORMAT ( _AC / _Div, _Fmt, "en-US" ) & " mEUR, "
VAR _T2 = _Num                                       VAR _C2 = _K1
VAR _T3 = " vs PY; " & [Largest Gap Entity] & " has the largest gap to BU ("   VAR _C3 = _Text
VAR _T4 = [Largest Gap Text]                         VAR _C4 = [Largest Gap Colour]
VAR _T5 = ")."                                       VAR _C5 = _Text
-- LAYOUT (greedy: a part goes to the next line when it does not fit)
VAR _E1 = SUBSTITUTE ( SUBSTITUTE ( _T1, "&", "&amp;" ), "<", "&lt;" )
VAR _L1 = LEN ( _T1 )  VAR _N1 = 1
VAR _X1 = "<tspan fill='" & _Text & "'>" & _E1 & "</tspan>"
VAR _B2 = _L1 + LEN ( _T2 ) > _Budget && NOT ( LEFT ( _T2, 1 ) IN { ")", ",", ".", ";" } )
VAR _S2 = IF ( _B2 && LEFT ( _T2, 1 ) = " ", MID ( _T2, 2, 999 ), _T2 )
VAR _L2 = IF ( _B2, 0, _L1 ) + LEN ( _S2 )  VAR _N2 = _N1 + IF ( _B2, 1 )
VAR _X2 = IF ( _N2 <= _Lines, IF ( _B2, "<tspan x='0' dy='" & _LineH & "'", "<tspan" ) & " fill='" & _C2 & "'>"
    & SUBSTITUTE ( SUBSTITUTE ( _S2, "&", "&amp;" ), "<", "&lt;" ) & "</tspan>" )
VAR _B3 = _L2 + LEN ( _T3 ) > _Budget && NOT ( LEFT ( _T3, 1 ) IN { ")", ",", ".", ";" } )
VAR _S3 = IF ( _B3 && LEFT ( _T3, 1 ) = " ", MID ( _T3, 2, 999 ), _T3 )
VAR _L3 = IF ( _B3, 0, _L2 ) + LEN ( _S3 )  VAR _N3 = _N2 + IF ( _B3, 1 )
VAR _X3 = IF ( _N3 <= _Lines, IF ( _B3, "<tspan x='0' dy='" & _LineH & "'", "<tspan" ) & " fill='" & _C3 & "'>"
    & SUBSTITUTE ( SUBSTITUTE ( _S3, "&", "&amp;" ), "<", "&lt;" ) & "</tspan>" )
VAR _B4 = _L3 + LEN ( _T4 ) > _Budget && NOT ( LEFT ( _T4, 1 ) IN { ")", ",", ".", ";" } )
VAR _S4 = IF ( _B4 && LEFT ( _T4, 1 ) = " ", MID ( _T4, 2, 999 ), _T4 )
VAR _L4 = IF ( _B4, 0, _L3 ) + LEN ( _S4 )  VAR _N4 = _N3 + IF ( _B4, 1 )
VAR _X4 = IF ( _N4 <= _Lines, IF ( _B4, "<tspan x='0' dy='" & _LineH & "'", "<tspan" ) & " fill='" & _C4 & "'>"
    & SUBSTITUTE ( SUBSTITUTE ( _S4, "&", "&amp;" ), "<", "&lt;" ) & "</tspan>" )
VAR _B5 = _L4 + LEN ( _T5 ) > _Budget && NOT ( LEFT ( _T5, 1 ) IN { ")", ",", ".", ";" } )
VAR _S5 = IF ( _B5 && LEFT ( _T5, 1 ) = " ", MID ( _T5, 2, 999 ), _T5 )
VAR _N5 = _N4 + IF ( _B5, 1 )
VAR _X5 = IF ( _N5 <= _Lines, IF ( _B5, "<tspan x='0' dy='" & _LineH & "'", "<tspan" ) & " fill='" & _C5 & "'>"
    & SUBSTITUTE ( SUBSTITUTE ( _S5, "&", "&amp;" ), "<", "&lt;" ) & "</tspan>" )
VAR _Cut = IF ( _N5 > _Lines, "<tspan fill='" & _Text & "'>…</tspan>" )
VAR _H = _Lines * _LineH + 4
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W & "' height='" & _H
    & "' viewBox='0 0 " & _W & " " & _H & "'><text x='0' y='" & _Size & "' font-family='" & _FontEm
    & "' font-weight='600' font-size='" & _Size & "' xml:space='preserve'>"
    & _X1 & _X2 & _X3 & _X4 & _X5 & _Cut & "</text></svg>"
```

- `[Period Label]`, `[Largest Gap Entity]`, `[Largest Gap Text]` ("-3.4 mEUR") and
  `[Largest Gap Colour]` (the same `SWITCH` as `_K1` on that gap) are placeholders for your
  message bindings; a verdict word ("in line with") needs its declared threshold (`ibcs-composition` §2).
- The width estimate (0.58 em per character) is a little generous for Segoe UI Semibold; check
  the longest real message once in the preview harness and lower `_Budget` if a line runs out.
- Avoid a `%` directly followed by two hex digits in the text (`%20` would be URL-decoded in the
  data URI); a `%` followed by a space, `)` or `<` is safe (skeleton 4 prints `+5.8%` this way).
- Accessibility: an image is not read as text. Bind the plain-text message measure to the
  table's alt text (Format → General → Alt text → fx in Desktop; copy the resulting JSON) and keep
  it as the tooltip.
- **Fallback** (proven in an end-to-end test): the plain-text message in a `cardVisual` with
  `value.bold` true ([pbir-skeleton.md](../../ibcs-power-bi/references/pbir-skeleton.md) §6):
  bold, but every number black.

## 8. One row per category with all tiers, plus a header row

A structure block "by company" (or product, region) as **one SVG per row** that draws every tier
side by side: AC bar in front of the outlined BU bar with a PY triangle (skeleton 5), the ΔBU bar
at the **same px per unit** (skeleton 1), and the ΔBU% pin on its own % scale (skeleton 2), plus a
highlight ellipse on the row the key message names. A second measure draws the header row: tier
names and the integrated legend (AC, BU, PY) at the first row's marks. Both share one GEOM block,
so every row and the header agree on the x offsets of the tiers. Why one SVG per row: every image
column of a `tableEx` shares `imageWidth`, so tiers in separate columns cannot get their own widths.

Power BI route:
- Two `tableEx` visuals stacked edge to edge in one chart card (page-shell.md §5): the header table
  (one row, columns: a blank text measure as wide as the category column + `SVG Rows Header`) and
  the rows table (columns: the category + `SVG Row`, sorted by `SVG Row`, which leads with a sortable
  `<desc>` holding AC).
- `grid.imageWidth` = `_W`, `imageHeight` = `_H` (rows) / 30 (header); image column width = `_W` + 20;
  no rules (page-shell.md §3); the rows table's height = 17 (its empty header strip) + rows × (`_H` + 2) + 24.
- `_S` = the page scale group's px per unit (`scale_layout.py`, the same value as the Deneb month
  chart's `pxPerUnit`), so a company bar of 10 mEUR is as long as a month column of 10 mEUR is high.

```dax
-- GEOM (identical in SVG Row and SVG Rows Header)
VAR _S = 9  VAR _SP = 3  VAR _W = 1000  VAR _H = 28      -- px per unit, px per pp, SVG size
VAR _T = _H * 0.5  VAR _Off = _T * 0.25                   -- bar thickness, BU outline offset
VAR _Tri = MIN ( MAX ( 0.33 * _T, 6 ), 12 )  VAR _Top = _Tri + 1  VAR _Yc = _Top + _Off + _T / 2
VAR _All = FILTER (
    ADDCOLUMNS ( ALLSELECTED ( 'Company'[Company] ),
        "@ac", [Revenue] / 1E6, "@bu", [Revenue BU] / 1E6, "@py", [Revenue PY] / 1E6,
        "@d", IF ( NOT ISBLANK ( [Revenue] ) && NOT ISBLANK ( [Revenue BU] ), ( [Revenue] - [Revenue BU] ) / 1E6 ),
        "@p", IF ( NOT ISBLANK ( [Revenue] ) && [Revenue BU] > 0, DIVIDE ( [Revenue] - [Revenue BU], [Revenue BU] ) * 100 ) ),
    NOT ISBLANK ( [@ac] ) || NOT ISBLANK ( [@bu] ) )
VAR _BMax = MAXX ( _All, MAX ( MAX ( COALESCE ( [@ac], 0 ), COALESCE ( [@bu], 0 ) ), COALESCE ( [@py], 0 ) ) )
VAR _DNeg = MAXX ( _All, MAX ( 0, - [@d] ) )  VAR _DPos = MAXX ( _All, MAX ( 0, [@d] ) )
VAR _PNeg = MAXX ( _All, MAX ( 0, - [@p] ) )
VAR _LabV = 46  VAR _LabD = 44  VAR _LabP = 56  VAR _Gap = 20     -- label room per tier (7 px/char + 6), gap between tiers
VAR _X2 = 1 + _BMax * _S + _LabV + _Gap + _DNeg * _S + _LabD     -- ΔBU axis
VAR _X3 = _X2 + _DPos * _S + _LabD + _Gap + _PNeg * _SP + _LabP  -- ΔBU% axis
VAR _GapRow = MAXX ( TOPN ( 1, FILTER ( _All, NOT ISBLANK ( [@d] ) ), ABS ( [@d] ), DESC, 'Company'[Company], ASC ), 'Company'[Company] )
```

`SVG Row` (one row; tokens as in skeletons 1, 2, 5):

```dax
SVG Row =
-- TOKENS
VAR _ACc = "#404040"  VAR _PYc = "#A6A6A6"  VAR _PLFill = "#FFFFFF"  VAR _PLStroke = "#404040"
VAR _Good = "#8CB400"  VAR _Bad = "#FF0000"  VAR _Neutral = "#0064FF"  VAR _HL = "#0064FF"
VAR _Text = "#000000"  VAR _Font = "Segoe UI"
-- GEOM (block above)
VAR _AC = [Revenue] / 1E6  VAR _BU = [Revenue BU] / 1E6  VAR _PY = [Revenue PY] / 1E6  VAR _Pol = 1
VAR _D = IF ( NOT ISBLANK ( _AC ) && NOT ISBLANK ( _BU ), _AC - _BU )  VAR _R = ROUND ( _D, 1 )
VAR _P = IF ( NOT ISBLANK ( _AC ) && _BU > 0, DIVIDE ( _AC - _BU, _BU ) * 100 )  VAR _RP = ROUND ( _P, 1 )
VAR _KD = SWITCH ( TRUE (), _R = 0, _Text, _Pol = 0, _Neutral, _D * _Pol > 0, _Good, _Bad )
VAR _KP = SWITCH ( TRUE (), _RP = 0, _Text, _Pol = 0, _Neutral, _P * _Pol > 0, _Good, _Bad )
VAR _DLen = ABS ( _D ) * _S  VAR _DX = IF ( _D >= 0, _X2, _X2 - _DLen )
VAR _DL = IF ( _R = 0, "0.0", FORMAT ( _R, "+0.0;-0.0", "en-US" ) )
VAR _DLX = IF ( _D >= 0, _X2 + _DLen + 4, _X2 - _DLen - 4 )
VAR _PLen = ABS ( _P ) * _SP  VAR _PE = IF ( _P >= 0, _X3 + _PLen, _X3 - _PLen )
VAR _PL = IF ( _RP = 0, "0.0%", FORMAT ( _RP / 100, "+0.0%;-0.0%", "en-US" ) )
VAR _IsGap = COUNTROWS ( _All ) > 1 && SELECTEDVALUE ( 'Company'[Company] ) = _GapRow
VAR _EW = LEN ( _DL ) * 3.4 + 6                                  -- ellipse half-width around the Δ label
RETURN
IF ( HASONEVALUE ( 'Company'[Company] ) && ( NOT ISBLANK ( _AC ) || NOT ISBLANK ( _BU ) ),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W & "' height='" & _H & "' viewBox='0 0 " & _W & " " & _H & "'>"
    & "<desc>" & FORMAT ( COALESCE ( _AC, 0 ) + 1E9, "0000000000.000", "en-US" ) & "</desc>"   -- sort key
    & "<g font-family='" & _Font & "' font-size='11'>"
    -- tier 1: BU outlined bar behind, AC bar, PY triangle (skeleton 5), value label right of max(AC, BU)
    & IF ( NOT ISBLANK ( _BU ), "<rect x='1' y='" & FORMAT ( _Top, "0.0", "en-US" ) & "' width='" & FORMAT ( _BU * _S, "0.0", "en-US" )
        & "' height='" & FORMAT ( _T, "0.0", "en-US" ) & "' fill='" & _PLFill & "' stroke='" & _PLStroke & "' stroke-width='1'/>" )
    & IF ( NOT ISBLANK ( _AC ), "<rect x='1' y='" & FORMAT ( _Top + _Off, "0.0", "en-US" ) & "' width='" & FORMAT ( _AC * _S, "0.0", "en-US" )
        & "' height='" & FORMAT ( _T, "0.0", "en-US" ) & "' fill='" & _ACc & "'/>" )
    & IF ( NOT ISBLANK ( _PY ), "<path d='M" & FORMAT ( _PY * _S + 1 - _Tri * 0.575, "0.0", "en-US" ) & " " & FORMAT ( _Top - 1 - _Tri, "0.0", "en-US" )
        & " L" & FORMAT ( _PY * _S + 1 + _Tri * 0.575, "0.0", "en-US" ) & " " & FORMAT ( _Top - 1 - _Tri, "0.0", "en-US" )
        & " L" & FORMAT ( _PY * _S + 1, "0.0", "en-US" ) & " " & FORMAT ( _Top - 1, "0.0", "en-US" ) & " Z' fill='" & _PYc & "'/>" )
    & "<line x1='0.5' y1='0' x2='0.5' y2='" & _H & "' stroke='" & _ACc & "' stroke-width='1'/>"
    & IF ( NOT ISBLANK ( _AC ), "<text x='" & FORMAT ( MAX ( COALESCE ( _AC, 0 ), COALESCE ( _BU, 0 ) ) * _S + 5, "0.0", "en-US" )
        & "' y='" & FORMAT ( _Yc + 4, "0.0", "en-US" ) & "' fill='" & _Text & "'>" & FORMAT ( _AC, "#,0.0", "en-US" ) & "</text>" )
    -- tier 2: ΔBU bar at the same px per unit, plan-notation axis (double line), highlight ellipse
    & "<rect x='" & FORMAT ( _X2 - 2.5, "0.0", "en-US" ) & "' y='0' width='1' height='" & _H & "' fill='" & _PLStroke & "'/>"
    & "<rect x='" & FORMAT ( _X2 + 1.5, "0.0", "en-US" ) & "' y='0' width='1' height='" & _H & "' fill='" & _PLStroke & "'/>"
    & IF ( NOT ISBLANK ( _D ),
        IF ( _R <> 0, "<rect x='" & FORMAT ( _DX, "0.0", "en-US" ) & "' y='" & FORMAT ( _Top + _Off, "0.0", "en-US" ) & "' width='" & FORMAT ( _DLen, "0.0", "en-US" )
            & "' height='" & FORMAT ( _T, "0.0", "en-US" ) & "' fill='" & _KD & "'/>" )
        & "<text x='" & FORMAT ( _DLX, "0.0", "en-US" ) & "' y='" & FORMAT ( _Yc + 4, "0.0", "en-US" ) & "' text-anchor='" & IF ( _D >= 0, "start", "end" )
            & "' fill='" & _Text & "'>" & _DL & "</text>"
        & IF ( _IsGap, "<ellipse cx='" & FORMAT ( IF ( _D >= 0, _DLX + _EW - 6, _DLX - _EW + 6 ), "0.0", "en-US" ) & "' cy='" & FORMAT ( _Yc, "0.0", "en-US" )
            & "' rx='" & FORMAT ( _EW, "0.0", "en-US" ) & "' ry='9' fill='none' stroke='" & _HL & "' stroke-width='1.5'/>" ) )
    -- tier 3: ΔBU% pin on its own % scale, N/A when BU <= 0 or blank
    & "<rect x='" & FORMAT ( _X3 - 2.5, "0.0", "en-US" ) & "' y='0' width='1' height='" & _H & "' fill='" & _PLStroke & "'/>"
    & "<rect x='" & FORMAT ( _X3 + 1.5, "0.0", "en-US" ) & "' y='0' width='1' height='" & _H & "' fill='" & _PLStroke & "'/>"
    & IF ( ISBLANK ( _P ),
        "<text x='" & FORMAT ( _X3 + 8, "0.0", "en-US" ) & "' y='" & FORMAT ( _Yc + 4, "0.0", "en-US" ) & "' fill='" & _Text & "'>N/A</text>",
        IF ( _RP <> 0, "<rect x='" & FORMAT ( MIN ( _X3, _PE ), "0.0", "en-US" ) & "' y='" & FORMAT ( _Yc - 1, "0.0", "en-US" ) & "' width='" & FORMAT ( _PLen, "0.0", "en-US" )
            & "' height='2' fill='" & _KP & "'/>"
            & "<rect x='" & FORMAT ( _PE - 3, "0.0", "en-US" ) & "' y='" & FORMAT ( _Yc - 3, "0.0", "en-US" ) & "' width='6' height='6' fill='" & _ACc & "'/>" )
        & "<text x='" & FORMAT ( IF ( _P >= 0, _PE + 7, _PE - 7 ), "0.0", "en-US" ) & "' y='" & FORMAT ( _Yc + 4, "0.0", "en-US" ) & "' text-anchor='"
            & IF ( _P >= 0, "start", "end" ) & "' fill='" & _Text & "'>" & _PL & "</text>" )
    & "</g></svg>" )
```

`SVG Rows Header` (one row, height 30): `AC` at x 1 (y 26); `BU` right-aligned at the first
(largest) row's BU end and `PY` centred above its triangle (y 14; move it 26 px left when the two
would touch); `ΔBU` centred on `_X2` and `ΔBU%` on `_X3` in the semibold font. No separate legend
line ("BU □ PY ▼ AC ■"): the names sit at the marks they explain.

Rules:
- One GEOM in both measures; extents come from `ALLSELECTED` over the category, so every row of
  the current filter context uses the same tier offsets and the header matches the rows.
- Label room per tier is part of the x offsets (`_LabV`, `_LabD`, `_LabP` ≈ 7 px per character of
  the longest label + 6): a label never runs into the next tier and never leaves the SVG. Check
  `_X3 + _PPos × _SP + _LabP ≤ _W` once with the largest positive Δ% (add `_PPos` like `_PNeg`), and
  widen `_W` (and `imageWidth`) rather than shrinking `_S`.
- `_S` is the page's px per unit, never a per-measure `MAXX` fit: the block must read on the same
  scale as the month chart (UN 4.1). Δ% pins have their own scale `_SP` (one per page).
- Rows sort by AC descending via the `<desc>` sort key (`sort_measure` in the table recipe).

## 9. Variance waterfall with a magnifying glass (two visuals)

The form and the rule are the Deneb templates' (`ibcs-deneb` SKILL.md, "Variance waterfalls"): a
structure bridge is card 29 (IBCS v2.0 p. 112, STD), the total variance an arrow below the result
bar. When the steps are too short to read on the page scale (OURS: the largest step < 5 % of the
base, the Deneb knob `magnifyBelow`), CH 4.5 (p. 74, STD) asks to mark the zoomed part, connect it to
a second chart at a bigger scale and state that scale. In SVG-in-DAX that second chart is a
**second image column of the same rows**, so the zoomed steps sit on the same row y as the overview:

- Visual 1, the overview: the bridge rows table of skeleton 8's shape (one SVG per row:
  base, steps, total) at the page px per unit `_S`, steps without labels when magnified.
- Visual 2, the magnifier: a second image column (or a second `tableEx` placed edge to edge on the
  right, same row height) whose SVG draws only the steps at `_S × _K`, from the lowest running total
  `_Lo`, with the signed label; base and total rows stay empty. A header row above it states the
  scale: "Steps ×k" in `color.text.secondary`, and draws the zigzag axis break at the origin.
- The marker: every step row draws its part of a 1 px box in the highlight colour around the steps'
  range ± 3 px in the overview (left and right edges in every step row, the top edge in the first
  step row, the bottom edge in the last); connectors (0.75 px) run from the box's top and bottom
  edges to the magnifier's frame in the first and last step rows. Set the table's row padding and
  grid to 0 (page-shell.md §3) so the row SVGs touch and the box reads as one shape.
- `_K`: the smallest of 1, 2, 5, 10, 20, 50 … with `_MaxStep × _S × _K ≥ 40` px (OURS), lowered to the
  next such value when the steps' span would not fit the magnifier's width.

```dax
-- GEOM of the magnifier (identical in the row and header measures). 'Bridge'[Kind] = base | variance | total;
-- [Bridge Value] = base/total value or the SIGNED step; [Bridge Start] = running total before the row.
VAR _S = 2.2  VAR _W = 170  VAR _H = 28  VAR _Lab = 36           -- page px per unit, panel width, row height, label room
VAR _Base = CALCULATE ( [Bridge Value], REMOVEFILTERS ( 'Bridge' ), 'Bridge'[Kind] = "base" )
VAR _Steps =
    CALCULATETABLE (
        ADDCOLUMNS ( VALUES ( 'Bridge'[Element] ), "@v", [Bridge Value], "@s", [Bridge Start] ),
        REMOVEFILTERS ( 'Bridge' ), 'Bridge'[Kind] = "variance" )
VAR _MaxStep = MAXX ( _Steps, ABS ( [@v] ) )
VAR _Lo = MINX ( _Steps, MIN ( [@s], [@s] + [@v] ) )
VAR _Hi = MAXX ( _Steps, MAX ( [@s], [@s] + [@v] ) )
VAR _Mag = NOT ISBLANK ( _Base ) && _MaxStep > 0 && _MaxStep < 0.05 * ABS ( _Base )   -- OURS: magnifyBelow
VAR _Need = 40 / ( _MaxStep * _S )
VAR _E = POWER ( 10, FLOOR ( LOG10 ( _Need ), 1 ) )
VAR _F = _Need / _E
VAR _KUp = _E * SWITCH ( TRUE (), _F <= 1, 1, _F <= 2, 2, _F <= 5, 5, 10 )
VAR _Cap = ( _W - 2 * _Lab ) / ( ( _Hi - _Lo ) * _S )
VAR _E2 = POWER ( 10, FLOOR ( LOG10 ( _Cap ), 1 ) )
VAR _KDown = _E2 * SWITCH ( TRUE (), _Cap / _E2 >= 5, 5, _Cap / _E2 >= 2, 2, 1 )
VAR _K = MAX ( 1, IF ( _KUp <= _Cap, _KUp, _KDown ) )

-- SVG Magnifier Row: one step at ×_K; base/total rows and _Mag = FALSE return BLANK
VAR _Kind = SELECTEDVALUE ( 'Bridge'[Kind] )
VAR _V = [Bridge Value]  VAR _St = [Bridge Start]
VAR _X0 = _Lab + ( MIN ( _St, _St + _V ) - _Lo ) * _S * _K
VAR _X1 = _Lab + ( MAX ( _St, _St + _V ) - _Lo ) * _S * _K
VAR _T = _H * 0.5
VAR _Lbl = <the signed label of skeleton 1: a step that rounds to 0 is "0.0", unsigned and uncoloured>
VAR _Fill = <the impact colour of skeleton 1; no rect when the step rounds to 0>
RETURN
    IF ( _Mag && _Kind = "variance",
        "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='" & _W & "' height='" & _H & "'>"
            & "<line x1='" & _Lab & "' y1='0' x2='" & _Lab & "' y2='" & _H & "' stroke='#404040'/>"     -- origin at _Lo
            & "<rect x='" & _X0 & "' y='" & ( _H - _T ) / 2 & "' width='" & MAX ( 1, _X1 - _X0 ) & "' height='" & _T & "' fill='" & _Fill & "'/>"
            & "<text x='" & IF ( _V >= 0, _X1 + 3, _X0 - 3 ) & "' y='" & _H / 2 & "' dominant-baseline='central' text-anchor='"
            & IF ( _V >= 0, "start", "end" ) & "' font-size='12' font-family='Segoe UI'>" & _Lbl & "</text></svg>" )
```

The header measure draws the caption `"Steps ×" & FORMAT ( _K, "#,0" )` right-aligned and a zigzag
(`<polyline points='…'>`) on the origin line. Not verified in the Power BI service (as of 2026-10):
whether stacked `tableEx` rows render without a gap at every zoom level; prefer the Deneb templates
(`waterfall-variance`, `waterfall-variance-time`), which draw overview and magnifier in one visual.

## Shared row geometry (GEOM) and px per unit

Every SVG column of one table row (skeletons 1, 2, 5, and any further bar column) uses one GEOM
block, so the bars of all columns have the same thickness and baseline and the absolute columns
the same px per unit. Paste it into each measure in place of its own sizes and scale lines:

```dax
-- GEOM (identical in every SVG column of the table; values from the page scale group)
VAR _S    = 3.1                     -- px per display unit (after _Div): the page scale group's pxPerUnit
VAR _SP   = 1.2                     -- px per percentage point for pin columns (their own scale group)
VAR _H    = 28                      -- row height = grid.imageHeight
VAR _T    = _H * 0.5                -- bar thickness (2/3 rule: bar band ≈ 0.75 of the row)
VAR _Mid  = _H * 0.625              -- vertical centre of the AC bar / pin
VAR _Room = 46                      -- label room beyond the longest bar
```

- Column width (= the SVG `width`, = `grid.imageWidth` of the table, one value for every image
  column) = the largest column's range × `_S` (pins: × `_SP` × 100) + `_Room` + axis offset. When
  the columns' ranges differ a lot, put them in separate tables rather than stretching one width.
- **Several tiers per row** (bars + Δ bars + Δ% pins, card 26): one SVG measure per row that draws
  all tiers side by side (x offsets per tier inside the SVG, one GEOM block) is more robust than
  one image column per tier, because every image column of a table shares `imageWidth`. The tier
  names and the integrated legend go into a header row drawn by a second measure with the same
  GEOM (skeleton 8).
- The table's image column must be at least ~20 px wider than `imageWidth`: narrower, the cell
  clips the image and the service shows a stray truncation mark (".") at the right end of each
  row (end-to-end test, as of 2026-10).
- Bar length = value ÷ `_Div` × `_S`; pin length = Δ% × 100 × `_SP`. The `MAXX` scaling in
  skeletons 1, 2 and 5 fits a column that stands alone; in a table with several bar columns, or
  next to Deneb members of a scale group, use GEOM instead (a per-column `MAXX` gives every
  column its own px per unit).
- **Alignment with Deneb members of the same scale group**: Deneb `pxPerUnit` is in CSS px of the
  visual container at 100 % report zoom; a `tableEx` draws the SVG at `imageWidth` × `imageHeight`
  px. With SVG `width` = `imageWidth` (viewBox the same size) one SVG unit is one px, so
  `_S = pxPerUnit` (both per display unit, after `unitDivisor` / `_Div`). If the SVG must be drawn
  at another width, `_S = pxPerUnit × svgWidth ÷ imageWidth`. Check both at 100 % zoom; page zoom
  (`FitToWidth`) scales both visuals alike.

## Preview harness

Evaluate the measure against the model **without changing it**, write the SVG strings to a file,
render them in headless Chrome:

1. Query file (`svg-query.json`; the measure as a query-scoped `DEFINE MEASURE`, exactly as you
   would put it in `reportExtensions.json` or the model):
   ```json
   {"queries": [{"query": "DEFINE MEASURE 'Sales'[SVG KPI Card Revenue] = <expression> EVALUATE ROW ( \"svg\", [SVG KPI Card Revenue] )"}],
    "serializerSettings": {"includeNulls": true}}
   ```
   For a table column: `EVALUATE SUMMARIZECOLUMNS ( 'Company'[Company], "svg", [SVG AC BU PY Bar] )`.
   Report measures that the expression references are added as further `DEFINE MEASURE` lines.
2. Run it with the Power BI REST API **Datasets – Execute Queries** (JSON; needs Build permission
   on the model and the tenant setting *Dataset Execute Queries REST API*), e.g. with the Fabric
   CLI: `fab api -A powerbi -X post "groups/<workspace-id>/datasets/<model-id>/executeQueries" -i svg-query.json > result.json`
   (or DAX query view in Desktop and copy the cells into a JSON list).
3. `python3 -I "${CLAUDE_SKILL_DIR}/scripts/svg_preview.py" result.json --out ./svg-preview --png`
   writes `preview.html` (every SVG cell inline, labelled with its row) and `preview.png`.
   The script also takes a plain JSON list of SVG strings, e.g. to check markup with sample values.
4. Look at the PNG: scale shared across rows, colours by polarity, rounded zeros uncoloured, N/A,
   no raw values, labels inside the cell.
