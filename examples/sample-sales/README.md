# Sample Sales: a small IBCS-ready semantic model and a visual spec

Generic sample data for the [getting-started guide](../../docs/getting-started.md): five regions
(North, West, South, East, Other) in EUR, monthly revenue, cost of sales, operating costs and
orders. The model follows the `semantic-model-ibcs` skill (plugin `reporting-data`), so the
report and app builders can run against it unchanged.

| Scenario | Stored | Covers |
|---|---|---|
| AC | yes | 2025-01 to the last closed month **2026-09** |
| BU | yes | 2025 and 2026, one version per year |
| FC | yes | 2026, one 9+3 version (months 1–9 copied from AC) |
| PY | **no** | derived from AC by the calculation group (`SAMEPERIODLASTYEAR`) |

```
SampleSales.SemanticModel/   TMDL model (PBIP / Fabric item folder), no data source: every table is calculated
./specs/key-figures.visual-spec.yaml the Key figures page the getting-started design prompt should produce
csv/                         the same rows for a Lakehouse load (Region, Scenario, Sales)
expected_results.csv         numbers a correct model must reproduce (EUR; ratios and Δ% as fractions; pp as points)
scripts/generate_sample.py   single source of Sales.tmdl, Region.tmdl, Scenario.tmdl, csv/ and expected_results.csv
```

## The model

Compatibility level 1702 (DAX user-defined functions). Every table is a calculated table with its
rows in the TMDL (`DATATABLE`), so the model needs no connection or gateway.

| Object | What it holds |
|---|---|
| `Date` | Calendar 2025–2026 (`CALENDAR`), marked as date table; `MonthLabel` (`2026-09`), `MonthShort`, `IsClosedPeriod` (up to 2026-09) |
| `Region`, `Scenario`, `Sales` | Dimensions and the month-grain fact; keys and fact columns hidden |
| `_Measures` | Revenue, Cost of Sales, Gross Profit, Gross Margin %, Operating Costs (polarity −1), Operating Result, Orders, `fx Last Closed Month` |
| `Scenario Analysis` (precedence 20) | PY, BU, FC, AC, AC+FC, ΔPY, ΔPY%, ΔBU, ΔBU%, ΔFC, ΔFC%, and ΔBU member / ΔBU% member for rows that explain a total (regions); signed, scaled format strings that print a rounded zero unsigned; pp for ratios; Δ% N/A when the reference ≤ 0 |
| `Time Calc` (precedence 10) | Period, YTD, QTD, R12, FY, YTG, relative to the reporting month in context |
| `Scale`, `FC Version` | Unit picker for the format strings (default k; builders scale charts themselves), forecast-version picker |
| `functions.tmdl` | `Ibcs.Delta`, `Ibcs.DeltaMember`, `Ibcs.DeltaPct`, `Ibcs.Impact`, colour and format helpers |

Use **one reporting month** in the filter context (for example `'Date'[MonthLabel] = "2026-09"`);
the Time Calc items derive YTD and FY from it. The visuals label the `AC+FC` item `AC&FC`.

## Deploy it

Into a Fabric or Power BI workspace you can write to, with the Fabric CLI (`pip install
ms-fabric-cli`, `fab auth login`):

```sh
fab import "<workspace>.Workspace/Sample Sales.SemanticModel" -i ./SampleSales.SemanticModel
```

Then refresh the model once (workspace → Sample Sales → Refresh now): calculated tables are
computed on refresh. Fabric Git integration works too: commit the folder to a connected
repository and update the workspace from Git.

## Check it

Run this in DAX query view or with `fab api -A powerbi … executeQueries`, and compare with
`expected_results.csv` (View `YTD`, Measure `Revenue`):

```dax
EVALUATE
SUMMARIZECOLUMNS (
    'Scenario Analysis'[Scenario],
    TREATAS ( { "2026-09" }, 'Date'[MonthLabel] ),
    TREATAS ( { "YTD" }, 'Time Calc'[Period] ),
    TREATAS ( { "AC", "PY", "BU", "ΔPY", "ΔPY%", "ΔBU", "ΔBU%" }, 'Scenario Analysis'[Scenario] ),
    "Revenue", [Revenue]
)
```

Expected: AC 30 763 348.68, PY 29 999 955.00, BU 31 607 352.00, ΔPY +763 393.68 (+2.5 %),
ΔBU −844 003.32 (−2.7 %).

## Regenerate

```sh
python3 -I scripts/generate_sample.py           # rewrite the generated files
python3 -I scripts/generate_sample.py --check   # fail if they are out of date (CI)
```

Only the standard library is used, and the output is byte-for-byte reproducible. Change the
constants at the top of the script, never the generated files.
