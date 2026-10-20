# Table catalogue — column, row and table types

> Our summary of the table part of IBCS Standards v2.0 EXPRESS (EX 1.2, pp. 115–135) with
> STRUCTURE in tables (ST 5.2) and table components (CO 4.4); CC BY-SA 4.0, see the repository
> NOTICE. The **B-** card IDs are ours and are used in visual specs (`card: B-T-VAR`).

## 1. Rules for every table

- **Width:** all columns of one type have the same width, sized to the digits, not to the header
  text. Rows of one type have the same height; thin light lines between rows.
- **Alignment:** numbers and their headers right-aligned, text left-aligned; headers of grouping
  columns centred or left.
- **No vertical rules:** narrow gap between columns of one type, wider gap between groups and
  after the row header column.
- **Time, scenarios and variances go into columns**, never rows (p. 124). Periods left → right.
- **Scenario header marker:** a short bar under each scenario column header in its notation — AC
  thick dark, PY thick light, PL/BU double thin line (outlined), FC hatched; variance, measure
  and structure headers get a thin single line.
- **Hierarchy is visible:** totals and results bold, below their children (rows) or right of
  them (columns), with a solid line above; optional light-gray fill on totals.
- **Digits:** at most 4 per cell; unit and prefix in the title, not in cells.
- **Embedded charts** (CO 4.4): table bars, pins and waterfall bars aligned to the rows, one scale
  per column (absolute variance bars on the same scale as any chart of that unit on the page);
  sparklines only on a common or indexed scale; traffic lights only for ≤ 3 binary or
  compliance states.

## 2. Column types

| Card | Column type | Rule |
|---|---|---|
| B-C-HDR | Row header column | far left (or between two blocks), wider; short texts, abbreviations from the glossary |
| B-C-SCN | Scenario columns | equal width; order PY, PL, AC (FC by time); header marker in scenario notation |
| B-C-VAR | Variance columns | ΔPY, ΔPY%, ΔPL, ΔPL% in pairs (narrow gap within, wide between); signed; may embed variance bars/pins |
| B-C-TIME | Time columns | periods (flow) or dates (stock), chronological left → right; header marker shows the scenario of the period (e.g. past years AC, future PL) |
| B-C-MEAS | Measure columns | measures in calculation order; wider gap after intermediate results, which are bold |
| B-C-STR | Structure columns | structure elements as columns — allowed in tables (cross tables) |
| B-C-OFW | "Of which" column | right of its mother column without a gap, narrower/smaller font; not summed |
| B-C-REM | Remainder column | "Other" / "Rest of …" last before the total, excluded from ranks and averages |
| B-C-PCT | "Percent of" column | right of the referenced figure, smaller (italic), one decimal |
| B-C-TOT | Totals column | right of its group, bold, optional light-gray fill |
| B-C-HIER | Hierarchical columns | e.g. quarters then the bold year total to their right |
| B-C-NEST | Nested columns | outer group (period, scenario, market) over inner items; same inner order in every group |

## 3. Row types

| Card | Row type | Rule |
|---|---|---|
| B-R-HDR | Column header row | one or more lines; scenario markers on the lowest |
| B-R-MEAS | Measure and results rows | calculation scheme (P&L): result rows bold with a solid line above and a gap after |
| B-R-STR | Structure rows | elements of a structure dimension, sorted (by AC) or in a fixed order |
| B-R-OFW | "Of which" row | below the aggregated row, smaller, right-aligned label, not summed |
| B-R-REM | Remainder row | last before the total, after a gap; excluded from rank/average/top N |
| B-R-PCT | "Percent of" row | below the referenced figure, smaller/italic, e.g. "in % of net sales" |
| B-R-TOT | Totals row | below its group, bold, solid line above, optional light-gray fill; no "Total" word |
| B-R-HIER | Hierarchical rows | parents below their children (details → subtotal → total), bold by level |
| B-R-NEST | Nested rows | an outer structure repeated with inner rows; consistent inner order |

## 4. Table types

| Card | Type | Columns × rows | Typical question |
|---|---|---|---|
| B-T-TIME | Time series table | periods × structure or measures, remainder row, bold total | How did it develop per element? |
| B-T-VAR | Variance table | PY · PL · AC │ ΔPY · ΔPY% │ ΔPL · ΔPL% × structure or measures | Where are we vs plan and last year? |
| B-T-CROSS | Cross table | structure × structure (or measures), totals and remainders on both axes | How is a total split across two dimensions? |
| B-T-KPI | KPI cards (transposed variance table, ours) | one card per measure row: label, unit, AC value, then one line per comparison (Δ% and Δ with the scenario code) | Where do the key figures stand at a glance? |
| B-T-COMB | Combined table | several column/row types side by side or nested (e.g. month and YTD blocks × scenarios and variances; P&L × years > quarters) | Several analyses at once |

KPI cards (B-T-KPI) are a B-T-VAR turned on its side, not a gauge or traffic light: the same
numbers, order and notation (impact colour by polarity, Δ = 0 and Δ rounding to zero unsigned
and uncoloured, N/A for non-interpretable Δ%), cards in row order, one unit line per card. No
icons, no status lights, no count-up animation; a sparkline only with monthly values on a
shared or scale-banded scale.

## 5. Data shapes and computation

- Long fact: `Date | Scenario | <Structure keys> | Value`; variances are calculated, never stored.
- ΔPY% = (AC − PY) / PY with the **signed** reference; N/A when the reference is ≤ 0 or blank
  (our rule); never `ABS()`.
- Calculation schemes need a report-line dimension: `LineKey, LineName, Sort, LineType (detail |
  result | ofwhich | percentof | total), Level, ParentKey, Sign`. `LineType` drives both the
  calculation and the formatting.
- With a P&L sign convention (costs negative) every line has polarity +1; with display signs
  (costs positive) cost lines have polarity −1. Pick one and document it.

## 6. Common mistakes

Column widths fitted to header text; heavy vertical gridlines; centred numbers; scenario columns
out of order; variance pairs not grouped; "Total"/"Sum of" labels; parents above children in a
stepped layout; a remainder that is sorted into the ranking; relative variances on a negative
base "fixed" with ABS; a table that repeats the numbers of a chart next to it (CO 5.3).
