---
name: semantic-model-ibcs
description: >
  Designs, builds and reviews IBCS-ready Power BI / Fabric semantic models for finance and
  management reporting; use it whenever someone builds or changes a semantic model, TMDL, measures
  or calc groups for budget-vs-actual, forecast, variance, P&L or KPI reporting, asks how to model
  scenarios or variances, or writes DAX for an IBCS visual or Fabric App, even if they don't say
  "IBCS". Covers star schema with a Scenario dimension (AC, BU, PL, FC versions; PY derived),
  fiscal date table, calculation groups for scenarios and variances (ΔPY, ΔPL, ΔBU, ΔFC, ΔPY% …)
  with signed, scaled format-string expressions, variance polarity for good/bad colouring,
  report-line dimension for P&L tables and calculation waterfalls, unit scaling, DAX UDFs, field
  parameters, RLS/OLS, Direct Lake vs Import, and the exact DAX query shape each IBCS chart or
  table needs (Power BI visuals and Fabric Apps).
---

# IBCS semantic models

This skill is the IBCS-and-finance layer of a semantic model: *what* to build so that reports
on top can follow the IBCS® Standards. For generic syntax and tooling, use whatever you have
installed; these are good companions:

| Need | Where |
|---|---|
| TMDL syntax, indentation, file layout | a TMDL/PBIP skill (e.g. `pbip:tmdl`), Microsoft Learn *TMDL overview* |
| DAX language, optimisation | a DAX skill (e.g. `semantic-models:dax`), Learn DAX reference |
| Review / audit a model | Tabular Editor Best Practice Analyzer rules, a model-audit skill or agent |
| Bulk changes (generate explicit measures, folders) | Tabular Editor C# scripts |
| Create/deploy/refresh a model in Fabric | Microsoft's Fabric skills or the Fabric CLI (https://github.com/microsoft/fabric-cli) |
| Fabric App queries and visuals | the `ibcs-fabric-app` skill (plugin `fabric-apps`) |
| IBCS notation (colours, scenario fills, titles) | the `ibcs-notation` skill (plugin `ibcs`); page layout: `ibcs-composition` (plugin `ibcs`) |
| Power BI visuals with IBCS notation | the `ibcs-deneb` skill (plugin `ibcs-power-bi`) |
| SQL gold layer feeding the model | [sql-reporting-backend](../sql-reporting-backend/SKILL.md) |
| Dynamics ERP sources | [dynamics-erp-reporting](../dynamics-erp-reporting/SKILL.md) |

Reference design: [references/reference-model-tmdl.md](references/reference-model-tmdl.md)
describes a complete finance model (tables, UDFs, calc groups, roles) file by file; its SQL star
is bundled with the SQL skill in
[`${CLAUDE_SKILL_DIR}/../sql-reporting-backend/assets/sql/`](../sql-reporting-backend/assets/sql/01_schema.sql).

## Settings to agree first

- **Group currency and unit label** (examples here use EUR and `mEUR`; use yours).
- **Model culture / locale** (examples use `en-US`; number and date formats follow it).
- **Fiscal year start** (calendar year in the examples; any start month works).
- **Language for ERP labels** (enum/option-set decoding in silver).

## Non-negotiable IBCS rules in the model

These are where models usually go wrong. Each one exists because a report built on the model
would otherwise show something the IBCS Standards advise against.

1. **PY is derived, never stored.** PY = AC shifted one year; storing it goes stale after
   restatements.
2. **Δ = minuend − subtrahend, signed.** ΔPY = AC − PY, ΔBU = AC − BU; FC as minuend is named
   `FC-PL` / `(AC+FC)-BU`. BLANK when either side is blank (no variance against nothing).
   `AC+FC` (item name) and `AC&FC` (IBCS series label in visuals) are the same scenario: AC up
   to the **last closed period**, FC from the open month on, compared with full-period PY
   ([visual-data-contract.md](references/visual-data-contract.md) §0.6, §0.7).
3. **Δ% uses the signed reference:** (AC − PY) / PY, no `ABS()`. BLANK (shown "N/A") when the
   reference is blank, 0 or **negative** (OURS: our generalisation of IBCS v2.0, UN 4.1,
   p. 54). Plan 100 → actual −20 = −120 % is shown; plan −30 → actual −10 is N/A. See
   [dax-patterns.md](references/dax-patterns.md) §1.
4. **Δ of a ratio is in percentage points** (50 % − 40 % = +10 pp); Δ% of a ratio is the
   normal relative variance.
5. **Polarity selects colour only.** `VarianceDirection` +1 (more is better), −1 (less is
   better), 0 (neutral → blue). Never multiply a plotted value by it; geometry follows the
   arithmetic sign of the displayed variance. A variance of exactly 0 gets no colour.
6. **Store in P&L sign, compare in display sign.** Amounts are stored revenue +, cost − (so
   subtotals are plain sums); `[Report Value]` multiplies by `'Report Line'[DisplaySign]` so
   revenue, cost and profit lines appear as an IBCS P&L shows them (costs positive). All Δ
   and Δ% are computed on these displayed values; polarity says costs −1. Example: Material
   PL 20.8, AC 20.0 → ΔPL −0.8, ΔPL% −3.8 %, impact good (green), bar drawn to the left.
7. **One scale per object**, values unscaled; scaling happens in format strings; unit in the
   title (`mEUR`).
8. **Variances always signed** in format strings (`+#,0;-#,0;0`).
9. **Every visible number is an explicit measure**; `discourageImplicitMeasures` on.
10. **IBCS column order**: PY, PL/BU, FC, AC, then variances (calc-item ordinals).

## Workflow

1. **Pin the reporting questions.** Which scenarios (AC, BU, PL, FC versions), which period
   views (month, YTD, R12, FY, YTG), which structures (entity, cost centre, product), which
   KPIs/ratios, which currencies, who sees what. Write them down; they decide the grain.
2. **Pick the storage mode** ([design-decisions.md](references/design-decisions.md) §1).
   Default: Direct Lake on OneLake when gold is in Fabric; Import otherwise. Avoid
   DirectQuery for IBCS matrices without a hard reason.
3. **Agree the SQL contract** with [sql-reporting-backend](../sql-reporting-backend/SKILL.md):
   tables (Direct Lake) or `rpt` views (Import), surrogate int keys, unknown members, P&L
   sign, `VarianceDirection`, `IsClosedPeriod`, `FiscalPeriodSeq`. Derived columns live in
   SQL, not in DAX.
4. **Build the star**: `Date` (marked), `Scenario`, `FC Version`, conformed dimensions,
   `Finance` at month grain, `Report Line` + bridge, security table. At most one
   bidirectional relationship (the bridge).
5. **Add the IBCS machinery**: `functions.tmdl` (UDFs), `Amount` with the AC default,
   `Report Value`, KPI measures, calc groups `Scenario Analysis` (precedence 20) and
   `Time Calc` (10), `Scale`, `Structure`, `fx` helpers for colour/impact/units.
6. **Security**: dynamic RLS on dimensions; OLS only for whole objects.
7. **Describe everything** (`///` on tables, columns, measures, functions, roles). Fabric App
   builders and Copilot read these descriptions.
8. **Validate** (below), then hand over the visual data contract
   ([visual-data-contract.md](references/visual-data-contract.md)) to report/app builders.

## Choosing between options (short form)

| Question | Default | Deviate when |
|---|---|---|
| One fact + Scenario dim, or separate plan facts? | One fact at month grain | AC detail dominates, plan very sparse → separate facts + grain guards |
| Scenario/variance logic | Calc group | Excel/fixed exports → thin explicit measures that call the calc items |
| Period views | Second calc group, lower precedence | Calendar-based time intelligence once GA (preview as of Oct 2026) |
| PY | `SAMEPERIODLASTYEAR` (Gregorian/shifted) | 4-4-5, 13 periods → `FiscalPeriodSeq` offset |
| Variance colour | `fx Variance Colour` measure (field-value formatting) | Custom IBCS visuals that read `VarianceDirection` themselves |
| P&L table rows | `Report Line` + bridge + `Report Value` | Pure account drill → flattened account hierarchy |
| Scale | `Scale` slicer + format expressions | No slicer wanted → `fx Auto Scale` per visual |
| Forecast | Latest version by default, `FC Version` picker | Several FC series at once → items per version or a FC-version column on the visual |

Detail and reasoning: [design-decisions.md](references/design-decisions.md).

## Naming and folders

- Tables: business nouns (`Date`, `Scenario`, `Entity`, `Account`, `Report Line`,
  `Finance`); calc groups `Scenario Analysis`, `Time Calc`; measures table `_Measures`.
- Columns: same names as the SQL contract (PascalCase) so SQL, TMDL and DAX queries match;
  hide keys and technical columns.
- Measures: business names only (`Revenue`, `EBIT Margin %`); scenarios come from the calc
  group. Explicit variance measures, if needed: `<KPI> <item>` (`Revenue ΔPY%`) in
  `2 KPIs\<KPI>\Variances`.
- Helper measures that return text/colours start with `fx ` (calc items pass them through).
- Folders: `0 Base` (hidden), `1 Report lines`, `2 KPIs`, `3 Waterfall`, `9 Helpers`.
- Calc items use IBCS names with Unicode Δ (U+0394): `ΔPY`, `ΔPY%`.

## Validate before handing over

1. Structure: run your TMDL validator (PBIP tooling, Tabular Editor, or open the project in
   Power BI Desktop).
2. Semantics: deploy to a test workspace (or open in Desktop) and run the test query in
   [dax-patterns.md](references/dax-patterns.md) §14; compare with totals computed directly in
   SQL (keep a small expected-results file for your own test data).
3. Invariants: ΔX = AC − X; subtotal = Σ details; bare `[Amount]` = AC only; model total =
   SQL total per entity and month; an RLS user sees only their entities.
4. Best practice: BPA rules or a model auditor (implicit measures, descriptions,
   summarizeBy on keys, bidirectional relationships).

## Gotchas

- A filter on the marked `'Date'[Date]` column inside CALCULATE removes all Date filters;
  put cut-offs on non-key or fact columns ([dax-patterns.md](references/dax-patterns.md) §4).
- Calc items hit every measure, including text/colour helpers: the `fx ` bypass.
- `executeQueries` (Fabric Apps, REST) returns raw numbers: calc-item format strings are not
  applied; the app formats by value kind.
- `SUMMARIZECOLUMNS` drops all-blank rows: fill gaps in the app, never with `+ 0`.
- The highest-precedence calc group's format string wins; give Time Calc none.
- UDFs need compatibility level 1702; composite models can't call the source model's UDFs.
- Not verified against an engine by the author: detection of ratio measures through
  `SELECTEDMEASUREFORMATSTRING()` for measures with a *dynamic* format string, the TMDL OLS
  and calendar snippets, and the Direct Lake OneLake expression form. Test them in your build.

## References

- [references/visual-data-contract.md](references/visual-data-contract.md) — DAX query per
  IBCS chart/table, result shapes, value kinds and formatting rules for Fabric Apps, Power BI
  field-well bindings.
- [references/dax-patterns.md](references/dax-patterns.md) — UDFs, scenario/time/variance
  items, AC+FC, polarity, scaling, report lines, waterfall, Top N, grain guards, currency,
  tests and traps.
- [references/reference-model-tmdl.md](references/reference-model-tmdl.md) — the reference
  model explained file by file, Direct Lake conversion, roles/OLS, optional objects, TMDL
  rules that bite.
- [references/design-decisions.md](references/design-decisions.md) — storage mode, scenario
  design, grain, calendars, calc groups vs measures, security, currency, consumers.
