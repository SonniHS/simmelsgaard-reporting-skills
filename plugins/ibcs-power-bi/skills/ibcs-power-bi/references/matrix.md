# IBCS tables as a native Power BI matrix

How each IBCS table element (EX 1.2) maps to a native matrix, what the semantic model must
provide, and the workaround where the matrix cannot do it natively. Model patterns (scenario
measures, variance calculation group, report-line tables) belong to the `semantic-model-ibcs`
skill (plugin `reporting-data`).

| IBCS element | Native matrix setting | Model needs | Not native → workaround |
|---|---|---|---|
| Scenario columns PY / PL / AC / FC | calculation-group column on Columns | `Scenario` calculation group with ordinals | header rules (thick light / thick dark / double / hatched) → SVG header measure or a footnote |
| Variance columns ΔPY, ΔPY% | calculation items on Columns | variance items + dynamic format strings | embedded variance bars and pins → SVG measures (data category Image URL) |
| Time columns | date attributes on Columns | date table; AC/FC switch at the cut-off date | FC/PL notation in the headers → SVG or footnote |
| Nested columns | two column fields, subtotals off | two calculation groups with precedence | group gap between column groups |
| Hierarchical columns | column hierarchy + column subtotals (right) | — | group gap |
| Totals column / row | subtotals; row subtotals at the bottom | — | — |
| Results rows (P&L) | a report-line dimension on rows | report-line table + a measure that switches per line | bold with a solid rule and extra spacing → custom visual or SVG |
| "Of which" row / column | separate line or measure | excluded from totals in DAX | smaller font, indented label |
| "Percent of" row / column | separate line or measure | base-line lookup, format string per line | italic or smaller font |
| Remainder row / column ("Others") | mapped group in the dimension | Top-N + Others pattern; excluded from ranks | — |
| Row header in the middle | — | — | two visuals, a custom visual or an HTML/SVG rendering |

Rules that stay the same as in charts:

- Δ% from the signed reference, N/A where it cannot be interpreted.
- Polarity selects the colour only (good / bad / neutral blue), never the sign.
- Light-grey fill is allowed for totals rows/columns and results rows; no decorative fills.
- Bold for totals is a common default, not the only allowed emphasis.
