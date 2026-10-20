# Reference finance model in TMDL

This file describes a complete IBCS finance model (`FinanceIBCS.SemanticModel`, TMDL folder
format) part by part, with the snippets you need to build your own. Its SQL star is bundled
with the SQL skill ([01_schema.sql](../../sql-reporting-backend/assets/sql/01_schema.sql)).
Generic TMDL syntax (indentation, quoting, property order): Microsoft Learn
(https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview) or a TMDL skill.

## Contents
1. File map
2. database / model / expressions
3. Dimension and fact tables (Import partitions)
4. functions.tmdl (IBCS UDFs)
5. Calculation groups: Scenario Analysis and Time Calc
6. Measures table
7. Relationships and the report-line bridge
8. Switching to Direct Lake on OneLake / on SQL
9. Roles: RLS, OLS
10. Optional objects: calendars (preview), selection expressions, perspectives, cultures
11. TMDL rules that bite in this model

---

## 1. File map

```
FinanceIBCS.SemanticModel/
├── .platform                  type SemanticModel, logicalId (never edit after first deploy)
├── definition.pbism           {"version": "4.0"}  → TMDL folder format
└── definition/
    ├── database.tmdl          compatibilityLevel: 1702 (UDFs)
    ├── model.tmdl             discourageImplicitMeasures, ref table / ref role order
    ├── expressions.tmdl       SqlServer, SqlDatabase parameters
    ├── functions.tmdl         Ibcs.* UDFs
    ├── relationships.tmdl     6 relationships, 1 bidirectional (bridge → Account)
    ├── tables/  Date, Scenario, 'FC Version', Entity, Account, 'Report Line',
    │            'Report Line Account', Finance, 'Sec User Entity', _Measures,
    │            'Scenario Analysis', 'Time Calc', Scale, Structure
    └── roles/   'Entity Controller', 'Group Finance'
```

lineageTags can be omitted when you write TMDL by hand; Desktop and Tabular Editor add them
on the next save. Keep them once they exist (reports bind through them).

## 2. database, model, expressions

```tmdl
database FinanceIBCS
	compatibilityLevel: 1702
	compatibilityMode: powerBI
	language: 1033
```

```tmdl
model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: powerBI_V3
	discourageImplicitMeasures
	sourceQueryCulture: en-US
	dataAccessOptions
		legacyRedirects
		returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

ref table Date
…
```

- `culture` / `sourceQueryCulture` / `language` are your locale choice (en-US / 1033 above;
  e.g. de-DE / 1031). They affect format strings and parsing, so set them once, early.
- `discourageImplicitMeasures` is required by calculation groups.
- `__PBI_TimeIntelligenceEnabled = 0` turns auto date/time off (one shared Date table).
- Import parameters (`expressions.tmdl`) let one model point at SQL Server, Azure SQL or a
  Fabric Warehouse SQL endpoint; deployment tools (`fabric-cicd` parameter files,
  deployment-pipeline rules) replace them per stage:

```tmdl
/// SQL Server / Azure SQL / Fabric Warehouse SQL endpoint host, e.g. <your-warehouse-endpoint>
expression SqlServer = "localhost" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]

	annotation PBI_ResultType = Text

/// Database (or Fabric Warehouse) that holds the gold schema
expression SqlDatabase = "IbcsFinance" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]

	annotation PBI_ResultType = Text
```

## 3. Dimension and fact tables

Date table: `dataCategory: Time` on the table plus `isKey` on the `Date` column marks it.
Contiguous days, all scenario years covered.

```tmdl
table Date
	dataCategory: Time

	column Date
		dataType: dateTime
		isKey
		formatString: yyyy-mm-dd
		summarizeBy: none
		sourceColumn: Date

	/// Running period number (FiscalYearNo * 12 + FiscalPeriod). PY = Seq - 12, R12 = Seq-11..Seq.
	column FiscalPeriodSeq
		dataType: int64
		isHidden
		formatString: 0
		summarizeBy: none
		sourceColumn: FiscalPeriodSeq

	partition Date = m
		mode: import
		source =
				let
				    Source = Sql.Database(SqlServer, SqlDatabase),
				    Data = Source{[Schema = "gold", Item = "DimDate"]}[Data]
				in
				    Data
```

Rules applied across tables:

- Keys `int64`, hidden, `summarizeBy: none`. Every dimension has a `-1` unknown member (SQL).
- Amounts `decimal` (fixed decimal): the M step `Table.TransformColumnTypes(…, Currency.Type)`
  makes the type explicit and folds.
- Text attributes that need an order get `sortByColumn` (`MonthShort` by `MonthNo`,
  `LineName` by `SortOrder`).
- The fact is visible as a table but every column is hidden: users use measures only.
- `'FC Version'` is a filtered copy of `DimScenario` (`Table.SelectRows … "FC"`): a
  disconnected picker, so slicing it never filters the fact directly.
- `Scale` and `Structure` are calculated tables (DATATABLE, field parameter). They contain no
  Direct Lake columns, so they are also allowed in Direct Lake models.

Field parameter (copy the three-column shape exactly; `ParameterMetadata` makes Power BI
treat it as a field parameter):

```tmdl
table Structure

	column Structure
		summarizeBy: none
		sourceColumn: [Value1]
		sortByColumn: 'Structure Order'

		relatedColumnDetails
			groupByColumn: 'Structure Fields'

	column 'Structure Fields'
		isHidden
		summarizeBy: none
		sourceColumn: [Value2]
		sortByColumn: 'Structure Order'

		extendedProperty ParameterMetadata =
				{
				  "version": 3,
				  "kind": 2
				}

	column 'Structure Order'
		isHidden
		formatString: 0
		summarizeBy: sum
		sourceColumn: [Value3]

	partition Structure = calculated
		mode: import
		source =
				{
				    ( "Entity", NAMEOF ( 'Entity'[EntityName] ), 0 ),
				    ( "Region", NAMEOF ( 'Entity'[Region] ), 1 )
				}
```

A KPI switcher is the same shape over measures (`NAMEOF ( [Revenue] )`, `NAMEOF ( [EBIT] )`).

## 4. functions.tmdl

Root-level objects, body two tabs deep, declaration name quoted because of the dot:

```tmdl
/// IBCS relative variance (actual - reference) / reference, signed reference, no ABS. BLANK (show N/A) when the reference is blank, 0 or negative.
function 'Ibcs.DeltaPct' =
		( actual, reference ) =>
		IF (
			NOT ISBLANK ( actual ) && NOT ISBLANK ( reference ) && reference > 0,
			DIVIDE ( actual - reference, reference )
		)
```

Functions in the model: `Ibcs.Delta`, `Ibcs.DeltaMember`, `Ibcs.DeltaPct`, `Ibcs.Impact`, `Ibcs.ImpactColour`,
`Ibcs.IsHelper`, `Ibcs.IsRatioFormat`, `Ibcs.PointsIfRatio`, `Ibcs.ScaleFormat`,
`Ibcs.ValueFormat`, `Ibcs.DeltaFormat`, `Ibcs.DeltaPctFormat`, `Ibcs.Minuend`. Calls inside DAX
are unquoted (`Ibcs.Delta ( a, b )`). Parameters that may be BLANK are left **untyped**
(`AnyVal val`) so no implicit cast can turn BLANK into 0; `STRING`/`BOOLEAN` hints are used
for format helpers. Use `EXPR`/`MEASUREREF`/`COLUMNREF` only when the function must evaluate
the argument in its own context. The bodies of all twelve functions are in
[dax-patterns.md](dax-patterns.md) §1 (in TMDL: `function 'Ibcs.Name' =` with the same parameter
list and body).

## 5. Calculation groups

```tmdl
table 'Scenario Analysis'

	calculationGroup
		precedence: 20

		calculationItem 'ΔPY' =
				VAR minuend = Ibcs.Minuend ( SELECTEDVALUE ( 'Time Calc'[Period] ) )   -- AC, or AC+FC under FY/YTG
				RETURN
				IF (
				    Ibcs.IsHelper ( SELECTEDMEASURENAME () ),
				    SELECTEDMEASURE (),
				    Ibcs.PointsIfRatio (
				        Ibcs.Delta (
				            CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = minuend ),
				            CALCULATE ( SELECTEDMEASURE (), 'Scenario Analysis'[Scenario] = "PY" )
				        ),
				        SELECTEDMEASUREFORMATSTRING ()
				    )
				)
			ordinal: 6

			formatStringDefinition = Ibcs.DeltaFormat ( SELECTEDMEASURENAME (), SELECTEDMEASUREFORMATSTRING (), SELECTEDVALUE ( Scale[Scale], "k" ) )

	column Scenario
		dataType: string
		summarizeBy: none
		sourceColumn: Name
		sortByColumn: Ordinal

	column Ordinal
		dataType: int64
		isHidden
		formatString: 0
		summarizeBy: sum
		sourceColumn: Ordinal
```

The group also sets `multipleOrEmptySelectionExpression = BLANK ()` (several items selected
without an axis → BLANK instead of a silent AC), and the Δ/Δ% items take their minuend from
`Ibcs.Minuend ( SELECTEDVALUE ( 'Time Calc'[Period] ) )` (AC+FC under FY/YTG): ΔPY, ΔPL, ΔBU and
their % items as above; ΔFC and ΔFC% keep `"AC"` (AC+FC − FC would be 0 under YTG).

Depths: `calculationGroup` 1, `calculationItem` 2, item properties (`ordinal`,
`formatStringDefinition`) 3, DAX bodies 4. The two columns are mandatory: `Name` → the item
column, `Ordinal` → its sort.

Items and ordinals (IBCS order: PY first, then PL, BU, FC, AC; variances after):

| Ordinal | Item | Format expression |
|---|---|---|
| 0–5 | PY, PL, BU, FC, AC, AC+FC | `Ibcs.ValueFormat` (scaled, unsigned; ratios keep `0.0%`) |
| 6, 8, 10, 12, 14 | ΔPY, ΔPL, ΔBU, ΔFC, (AC+FC)-BU | `Ibcs.DeltaFormat` (scaled, signed; ratios `+0.0" pp";-0.0" pp";0.0" pp"`, value ×100 by `Ibcs.PointsIfRatio`) |
| 7, 9, 11, 13 | ΔPY%, ΔPL%, ΔBU%, ΔFC% | `Ibcs.DeltaPctFormat` (`+0.0%;-0.0%;0.0%`) |

`Time Calc` (precedence 10): Period, YTD, QTD, R12, FY, YTG, no format strings, column
`Period`. See [dax-patterns.md](dax-patterns.md) §5 for the bodies and why the precedence
order matters.

A new budget version is a row in `DimScenario`, not a model change. A new *scenario type*
(e.g. `PL` next to `BU`) needs one value item and its Δ/Δ% pair.

## 6. Measures table

`_Measures` is a calculated one-row table (`partition _Measures = calculated`, `source = {1}`,
a hidden `Value` column). Display folders: `0 Base` (hidden `Amount`, `Amount LC`),
`1 Report lines` (`Report Value`), `2 KPIs` (Revenue, Gross Profit, EBIT, Net Income,
EBIT Margin %), `3 Waterfall` (`WF Start`, `WF End`), `9 Helpers` (`fx …`).

```tmdl
	/// DISPLAY-signed value of one P&L report line (costs positive) …
	measure 'Report Value' =
			VAR lineType = SELECTEDVALUE ( 'Report Line'[LineType] )
			VAR displaySign = SELECTEDVALUE ( 'Report Line'[DisplaySign], 1 )
			…   displaySign * [Amount]   (ratio lines: DIVIDE of two lines)
		displayFolder: 1 Report lines

		formatStringDefinition = IF ( SELECTEDVALUE ( 'Report Line'[LineType] ) = "Ratio", "0.0%", Ibcs.ScaleFormat ( SELECTEDVALUE ( Scale[Scale], "k" ), FALSE ) )
```

Naming: KPI measures carry business names only (`Revenue`, never `Revenue AC`); scenarios
come from the calc group; helper measures start with `fx ` so calc items pass them through.
`///` descriptions become the tooltips in the field list and the `INFO.VIEW.MEASURES()`
description that Fabric App builders read.

## 7. Relationships

```tmdl
relationship Finance_PeriodDate_Date
	fromColumn: Finance.PeriodDate
	toColumn: Date.Date

relationship ReportLineAccount_Account
	crossFilteringBehavior: bothDirections
	fromColumn: 'Report Line Account'.AccountKey
	toColumn: Account.AccountKey
```

The relationship name is an identifier; tools generate GUIDs, readable names work as well.
`from` = many side. Defaults: single direction, active, many-to-one. The bridge pair
(`'Report Line' 1→* 'Report Line Account' *↔1 Account 1→* Finance`) is the only
bidirectional relationship; keep RLS off the bridge path (it is on Entity). Comments (`//`)
between root objects are rejected by TMDL linters; put rationale in docs.

## 8. Switching to Direct Lake

### On OneLake (recommended for new Fabric models)

Replace the parameters with one shared expression and turn each table partition into an
`entity` partition. Calculated tables (`Scale`, `Structure`, `_Measures`) and calc groups
stay as they are. `'FC Version'` (an M query) either becomes a Delta table/view materialised
in gold, or stays an **Import** table (Direct Lake on OneLake allows Import tables in the
same model).

```tmdl
expression DatabaseQuery =
		let
		    Source = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<workspace-id>/<lakehouse-or-warehouse-id>", [HierarchicalNavigation = true])
		in
		    Source
```

```tmdl
	partition Finance = entity
		mode: directLake
		source
			entityName: FactFinance
			schemaName: gold
			expressionSource: DatabaseQuery
```

- Lakehouse **without schemas**: drop `schemaName`.
- Column `sourceColumn` = Delta column name. Types must match the Delta types (decimal →
  `decimal`, date → `dateTime`, boolean → `boolean`); no GUID/binary columns.
- Set `directLakeBehavior: directLakeOnly` on the model during development (Direct Lake on
  SQL) so fallback errors instead of silently going to DirectQuery.
- After deploy: bind a **fixed-identity** cloud connection, turn off automatic updates, frame
  from the pipeline after the gold load.
- The `AzureStorage.DataLake` expression form and the `HierarchicalNavigation` option follow
  what Desktop generated in Oct 2026; script your own model once in TMDL view and copy its
  expression rather than typing ids by hand.

### On SQL endpoint

`expression DatabaseQuery = let database = Sql.Database("<your-warehouse-endpoint>", "<sql-endpoint-id>") in database`
(use the SQL endpoint id, not the friendly name, so Edit tables and refresh work in Desktop).
Views fall back to DirectQuery; SQL-endpoint RLS forces DirectQuery. Prefer OneLake for new
models.

## 9. Roles

```tmdl
/// Dynamic RLS: a user sees the entities mapped to their UPN in 'Sec User Entity'. Filter the dimension, never the fact.
role 'Entity Controller'
	modelPermission: read

	tablePermission Entity = Entity[EntityKey] IN CALCULATETABLE ( VALUES ( 'Sec User Entity'[EntityKey] ), 'Sec User Entity'[UserPrincipalName] = USERPRINCIPALNAME () )

	tablePermission 'Sec User Entity' = 'Sec User Entity'[UserPrincipalName] = USERPRINCIPALNAME ()
```

- Filter dimensions, not facts; the fact inherits through the relationship.
- Members are assigned in the service (Entra groups), not in TMDL committed to Git.
- PY and Time Calc are unaffected by entity RLS (they move dates, not entities).
- A second role `'Group Finance'` with `modelPermission: read` and no filters gives group
  controlling unrestricted read access.

**OLS** (hide a column or table from a role; visuals using it error for that role). Syntax as
serialised by recent tools (verify in your Desktop/Tabular Editor build before committing):

```tmdl
role 'Entity Controller'
	modelPermission: read

	tablePermission Finance
		columnPermission AmountLC = none
```

OLS can't hide rows (use RLS on Account for sensitive accounts) and doesn't propagate to UDFs
that reference a secured object.

## 10. Optional objects

**Calendar-based time intelligence (preview as of Oct 2026)** on the Date table, for 4-4-5 or
13-period calendars. Not in live-connected/composite models; keep the offset pattern as the
production default.

```tmdl
ref table Date
	calendar Fiscal
		calendarColumnGroup = year
			primaryColumn: FiscalYear
		calendarColumnGroup = month
			primaryColumn: FiscalYearPeriod
		calendarColumnGroup = date
			primaryColumn: Date
```

(Unverified shape; confirm against a model saved by Desktop before relying on it.)

**Selection expressions** on a calc group (compatibility level 1605+): `noSelectionExpression`
returns AC when the group is unfiltered, an alternative to the `Amount` guard:

```tmdl
	calculationGroup
		precedence: 20
		noSelectionExpression = CALCULATE ( SELECTEDMEASURE (), REMOVEFILTERS ( Scenario ), Scenario[ScenarioType] = "AC" )
```

**Perspectives** (author convenience, not security): `perspectives/PnL.tmdl` with
`perspectiveTable` / `perspectiveMeasure` entries. **Cultures**: `cultures/<locale>.tmdl` for
metadata translations; data translations (account names) as columns per language
(`AccountName_de`, `AccountName_fr` …), picked by a measure with `USERCULTURE ()`.

## 11. TMDL rules that bite in this model

- Indent with tabs (many validators reject spaces in `.SemanticModel` folders).
- `///` only directly above a declaration that has a Description (table, column, measure,
  expression, function, role); not above relationships.
- Names with spaces, dots, `%`, `+`, `(` or Δ need single quotes: `'ΔPY%'`, `'AC+FC'`,
  `'(AC+FC)-BU'`, `'Ibcs.Delta'`.
- Escape `"` inside DAX strings by doubling: `"+0.0"" pp"""`.
- Boolean column format strings as Desktop writes them: `"""TRUE"";""TRUE"";""FALSE"""`.
- A calculated table's columns use `sourceColumn: [Name]` (with brackets) and
  `isNameInferred`.
- Validate structurally (PBIP/TMDL validator), then open in Desktop or deploy to a test
  workspace. Structural validity is not DAX validity: run the test queries in
  [dax-patterns.md](dax-patterns.md) §14.
