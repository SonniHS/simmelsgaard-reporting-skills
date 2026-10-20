# PBIP/PBIR skeleton for a live-connected IBCS report

What a minimal report project contains, how it connects to a published semantic model, where the
IBCS theme goes, and the report-level pieces a live-connected report needs (report measures,
dynamic texts, slicer defaults, tall pages). File formats from Microsoft Learn (*Power BI Desktop
project report folder*, *Report definition*), as of 2026-10; items marked (verify) come from an
end-to-end test or are not documented and should be checked in Desktop once.

## Contents
1. Scaffold
2. Files
3. `definition.pbir`: the connection
4. Theme registration
5. Report measures (`reportExtensions.json`)
6. Dynamic text
7. Slicer defaults that move with the data
8. Tall pages
9. Verified visual.json for native helpers (slicer, text box, tableEx, interactions)
10. Verify after publishing

## 1. Scaffold

```sh
python3 -I "${CLAUDE_SKILL_DIR}/scripts/build_pbi_theme.py" --out-dir ./theme [--overrides ibcs-tokens.overrides.json]
python3 -I "${CLAUDE_SKILL_DIR}/scripts/new_pbip.py" --out ./powerbi --name "<report>" \
    --semantic-model-id <model-id> --theme ./theme/ibcs-pbi-theme.json \
    --page-display "<page>" --canvas 1280x720
```

Ids, workspace and model names are arguments; never commit them into a public skill. The script
writes only local files and never publishes. Then add visuals (`ibcs-deneb/scripts/to_pbir.py`
for Deneb, `visual.json` recipes from `card-routes.md` for native visuals), validate, and open
the `.pbip` in Desktop.

## 2. Files

```
<out>/<name>.pbip                                   points at <name>.Report
<out>/<name>.Report/.platform                       type Report, displayName, logicalId (keep it stable)
<out>/<name>.Report/definition.pbir                 datasetReference (§3)
<out>/<name>.Report/definition/version.json         PBIR format version
<out>/<name>.Report/definition/report.json          theme, resource packages, settings, publicCustomVisuals
<out>/<name>.Report/definition/reportExtensions.json   report-level measures (§5)
<out>/<name>.Report/definition/pages/pages.json     pageOrder, activePageName
<out>/<name>.Report/definition/pages/<page>/page.json   name, displayName, displayOption, width, height
<out>/<name>.Report/definition/pages/<page>/visuals/<visual>/visual.json
<out>/<name>.Report/StaticResources/RegisteredResources/ibcs-pbi-theme.json
```

`.gitignore`: `**/.pbi/localSettings.json` and `**/.pbi/cache.abf`. LF line endings, UTF-8.

A visual's size is `position.width` / `height` in its `visual.json` (`to_pbir.py --pos
x,y,width,height`). For the members of a scale group it is computed, not picked from the grid:
`python3 -I "${CLAUDE_SKILL_DIR}/scripts/scale_layout.py" group.json` gives each member's
container size at the group's px per unit (SKILL.md §3); snap the position to the grid, keep the
computed size.

## 3. `definition.pbir`: the connection

`datasetReference` is either `byPath` (a local `<model>.SemanticModel` folder; Desktop opens the
model in edit mode) or `byConnection` (a published model; live connection, model read-only).

| Form | `connectionString` | Use |
|---|---|---|
| REST / Fabric deployment | `semanticmodelid=<model-id>` | Documented on Learn for the Fabric REST API (and so `fab import`): only the id is needed |
| Desktop | `Data Source="powerbi://api.powerbi.com/v1.0/myorg/<workspace>";initial catalog=<model>;access mode=readonly;integrated security=ClaimsToken;semanticmodelid=<model-id>` | The string Desktop writes for a live connection (from an end-to-end test; verify against a file Desktop saved) |

`new_pbip.py` writes the REST form with `--semantic-model-id` alone and the Desktop form when
`--workspace` and `--model` are given. Learn also allows several `*.pbir` files side by side
(e.g. `definition-liveConnect.pbir` next to a `byPath` `definition.pbir`); Git integration reads
only `definition.pbir`. A report needs `byConnection` to carry report-level measures.

## 4. Theme registration

`build_pbi_theme.py` writes `ibcs-pbi-theme.json` (and `-cvd`). Copy it to
`StaticResources/RegisteredResources/` and reference it in `report.json`:

```json
"themeCollection": {"customTheme": {"name": "ibcs-pbi-theme.json",
  "reportVersionAtImport": {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"},
  "type": "RegisteredResources"}},
"resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
  "items": [{"name": "ibcs-pbi-theme.json", "path": "ibcs-pbi-theme.json", "type": "CustomTheme"}]}]
```

The `name` **inside** the theme file must equal that file name, `.json` included
(`"name": "ibcs-pbi-theme.json"`): Microsoft's PBIR validator reports a mismatch as
`PBIR_THEME_FILE_NAME_MISMATCH`, and Desktop caches themes by that name. `build_pbi_theme.py` writes
the file name into `name` (also for `--name`), and `new_pbip.py` sets it on the copy it registers.
After renaming a theme file, change `name` too.

Desktop usually also writes a `baseTheme` under `SharedResources`; the report renders without it
(verify after the first save in Desktop, then keep what Desktop writes). Re-run the theme script
and copy again after a token change; never edit the copy.

## 5. Report measures (`reportExtensions.json`)

When the shared model must not change, the report carries its own measures:

```json
{"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json",
 "name": "extension",
 "entities": [{"name": "<existing model table>", "measures": [
   {"name": "Revenue AC&FC", "dataType": "Double", "expression": "…", "formatString": "#,0.0",
    "displayFolder": "Report measures", "description": "MODEL GAP: …"},
   {"name": "SVG KPI Card Revenue", "dataType": "Text", "expression": "…", "dataCategory": "ImageUrl",
    "displayFolder": "Report measures"}]}]}
```

- `entities[].name` is a table of the model the measures attach to; `new_pbip.py` writes an empty
  `entities` list (verify that Desktop accepts it; delete the file otherwise).
- **Bind a report measure with `"Schema": "extension"`** in every `SourceRef` that points at it
  (projections, `sortDefinition`, filters, conditional-formatting expressions):
  `{"Measure": {"Expression": {"SourceRef": {"Schema": "extension", "Entity": "<table>"}},
  "Property": "<report measure>"}}`. Without it the service looks the name up in the model and
  every visual using it fails with "Something's wrong with one or more fields", technical detail
  `Missing_References` (found in an end-to-end test, as of 2026-10). `queryRef` and `columnWidth`
  / `dataPoint` selector `metadata` stay `"<table>.<measure>"`. `ibcs-deneb/scripts/to_pbir.py`
  writes it for Deneb fields; for everything else run
  `python3 -I "${CLAUDE_SKILL_DIR}/scripts/report_measures.py" <name>.Report --fix [--model <model>/definition/tables]`
  after editing visuals and `--check` before publishing. It also writes each measure's
  `references` (the measures it uses, report measures with `"schema": "extension"`, as Desktop
  saves them), removes `hidden` flags and stray `active` flags.
- **Never set `"hidden": true`** on a report measure. In the Power BI service every visual that
  uses a hidden report measure, or a visible one that references a hidden one, fails with
  "Something's wrong with one or more fields" (found in an end-to-end test, as of 2026-10). Put
  helpers in a `displayFolder` instead.
- **No dynamic format strings**: Learn states that report measures in a live-connect report
  cannot have them. Use a static `formatString`; for a unit picker (thousands / millions), divide
  in the measure and keep the format static, or fix the unit with a page filter.
- SVG measures: `"dataType": "Text"`, `"dataCategory": "ImageUrl"`.
- Mark each one as a report measure (description or a footnote on the page) and list it for the
  model owner: report measures are a bridge, model measures are the goal.
- **Test them before writing the report**: report measures run as query-scoped measures. In
  DAX query view (live connected) use *Define with references and evaluate*, or send
  `DEFINE MEASURE '<table>'[<name>] = <expression> … EVALUATE …` with the REST API *Datasets –
  Execute Queries* (the preview harness of `ibcs-svg-dax`). The same `DEFINE` block serves a
  Fabric App or any other DAX client.

## 6. Dynamic text

Key message, title lines (who / when), subtitles and "data as of" are text measures.

1. **Text box with a value** (Learn: *Add dynamic values to a text box*, Format → Values → fx):
   mixes typed text and a measure value. Its PBIR JSON is not documented: author one in Desktop,
   copy its `visual.json`, then reuse (verify).
2. **Card on a text measure** (proven in an end-to-end test): the new card (`cardVisual`) with one
   text measure in the `Data` role, label, accent bar, outline and fill off, value left-aligned,
   no padding. Microsoft's report skill marks `card` and `multiRowCard` deprecated
   (as of 2026-10); use `cardVisual`. Every `cardVisual` object takes the selector `{"id": "default"}`:
   ```json
   {"visualType": "cardVisual",
    "query": {"queryState": {"Data": {"projections": [{"field": {"Measure": {"Expression":
      {"SourceRef": {"Schema": "extension", "Entity": "<table>"}}, "Property": "Key Message"}},
      "queryRef": "<table>.Key Message", "nativeQueryRef": "Key Message"}]}}},
    "objects": {
      "value": [{"properties": {
        "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
        "horizontalAlignment": {"expr": {"Literal": {"Value": "'left'"}}},
        "textWrap": {"expr": {"Literal": {"Value": "true"}}}}, "selector": {"id": "default"}}],
      "label": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}, "selector": {"id": "default"}}],
      "accentBar": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}, "selector": {"id": "default"}}],
      "outline": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}, "selector": {"id": "default"}}],
      "fillCustom": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}, "selector": {"id": "default"}}],
      "padding": [{"properties": {"paddingUniform": {"expr": {"Literal": {"Value": "0D"}}}}, "selector": {"id": "default"}}],
      "layout": [{"properties": {"paddingUniform": {"expr": {"Literal": {"Value": "0D"}}},
        "alignment": {"expr": {"Literal": {"Value": "'left'"}}}}, "selector": {"id": "default"}}]}}
   ```
   Drop `"Schema": "extension"` for a model measure. Font family and colour come from the theme or
   `value.fontFamily` / `value.fontColor`; a bold key message: `value.bold` true. Older reports with
   a `multiRowCard` (category labels and card bar off) still render; move them to `cardVisual`.

Static parts of a title (line 2: the measure in bold and its unit) stay a plain text box.

## 7. Slicer defaults that move with the data

A slicer's saved selection (`objects.general.filter` in its `visual.json`) is static: "January
to the last closed month" saved today is wrong next month. Options, best first:

1. **A flag column in the model**, refreshed with the data, e.g. `'Date'[Relative Period]` =
   "YTD closed" / "Last closed month" / "Open month" (from the closed-period flag of the
   AC→FC switch). The slicer default selects the label, which keeps its meaning after every
   refresh.
2. **Without a model change** (proven in an end-to-end test): no slicer default; the slicer's
   empty state means "January to the last closed month". Every period measure computes its own
   effective period: the selected months if the slicer narrows `'Date'[Month]`, else the closed
   months of the current year. The pattern (one per base measure; `[Last Closed Month]` is the
   model's `yyyy-mm` of the last closed period):
   ```dax
   Revenue AC Period =
   VAR __lcm  = [Last Closed Month]
   VAR __selM = CALCULATETABLE ( VALUES ( 'Date'[Month] ), ALLSELECTED ( 'Date' ) )
   VAR __sel  = COUNTROWS ( __selM ) < COUNTROWS ( ALL ( 'Date'[Month] ) )
   VAR __P    = FILTER ( ALL ( 'Date'[Month] ),
                   IF ( __sel, 'Date'[Month] IN __selM,
                        'Date'[Month] <= __lcm && LEFT ( 'Date'[Month], 4 ) = LEFT ( __lcm, 4 ) ) )
   RETURN CALCULATE ( [Revenue], REMOVEFILTERS ( 'Date' ), __P )
   ```
   A matching `Period Label` text measure ("Jan..Sep 2026") feeds the title's when-line and the
   slicer header says what "none selected" means. Visuals that always show the whole year (a
   monthly chart with AC to the last closed month and FC after) must ignore the slicer: set the
   interaction to `NoFilter` (§9) instead of fighting the filter in DAX.
   This option makes the period slicer a **multi-select "months to include"** slicer. "Pick one
   month, show its YTD" does not work on a slicer over the date table: selecting one month filters
   the date table to that month, so a monthly chart on the page keeps only that one column (or,
   with `NoFilter`, ignores the slicer altogether). A single-month YTD selector with an intact time
   axis needs a model change: a disconnected period table (or a flag column, option 1) that the
   measures read with `SELECTEDVALUE`, while the chart's axis comes from the date table. A
   live-connected report cannot add that table; record it as a model gap.
3. **Relative date filter** on the date column ("in the last N months / this year"): calendar
   based, it cannot know the closing state; footnote it.

`to_pbir.py --filter` writes static basic filters only.

## 8. Tall pages

The 16:9 canvas (1280×720) is the default for screens and slides. A page with more content
(header, slicers, KPI cards and two chart blocks) may be taller, e.g. 1280×1120:
`page.json` `height` > 720 and `displayOption` `FitToWidth`, so readers scroll vertically. Keep
the key message and title at the top, the footer (footnotes, source, data as of) at the bottom,
and the same grid. Check PDF/PowerPoint export and the mobile layout at that size before
publishing (verify how the export splits a tall page).

## 9. Verified visual.json for native helpers

Taken from a report that rendered in the service (end-to-end test, as of 2026-10); names are
placeholders. `visualContainerObjects.title.show = false` on all of them.

**Slicer** (dropdown, multi-select). `"active": true` is what Desktop writes for a slicer field;
never copy it to other visuals. Font sizes are `textSize` (points) on `header` and `items`;
Microsoft's PBIR validator rejects `fontSize` there (end-to-end test, as of 2026-10):
```json
{"visualType": "slicer",
 "query": {"queryState": {"Values": {"projections": [{"field": {"Column": {"Expression":
   {"SourceRef": {"Entity": "Date"}}, "Property": "Month"}}, "queryRef": "Date.Month",
   "nativeQueryRef": "Month", "active": true}]}}},
 "objects": {
   "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
   "selection": [{"properties": {"singleSelect": {"expr": {"Literal": {"Value": "false"}}},
     "selectAllCheckboxEnabled": {"expr": {"Literal": {"Value": "true"}}}}}],
   "header": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
     "text": {"expr": {"Literal": {"Value": "'Period (months; none = Jan..last closed month)'"}}},
     "textSize": {"expr": {"Literal": {"Value": "9D"}}}}}],
   "items": [{"properties": {"textSize": {"expr": {"Literal": {"Value": "9D"}}}}}]}}
```

- **No "(Blank)" or unknown member in the list.** A dimension slicer lists every member of its
  column, including blank (rows of the fact without a match) and the model's unknown member
  ("Unknown", "N/A", key −1). Give the slicer a visual-level filter that excludes them: a
  `filterConfig` at the top level of its `visual.json` (sibling of `"visual"`), a `Not` around an
  `In` list, blank as the literal `null` (filter syntax from Microsoft's PBIR filter reference,
  as of 2026-10; verify once in the service):
  ```json
  "filterConfig": {"filters": [{"name": "excludeBlankUnknown",
    "field": {"Column": {"Expression": {"SourceRef": {"Entity": "Customer"}}, "Property": "Customer Group"}},
    "type": "Categorical", "howCreated": "User",
    "filter": {"Version": 2, "From": [{"Name": "c", "Entity": "Customer", "Type": 0}],
      "Where": [{"Condition": {"Not": {"Expression": {"In": {
        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Customer Group"}}],
        "Values": [[{"Literal": {"Value": "null"}}], [{"Literal": {"Value": "'Unknown'"}}]]}}}}}]}}]}
  ```
  Inside `Where` the column refers to the `From` alias (`"Source": "c"`), not the entity. Use the
  unknown member's exact label from the model. Charts keep showing the unknown member's values
  (totals must reconcile); only the slicer list hides it.
- **The same slicer on several pages is synced**, so a selection carries across pages like an
  app's URL state: give each copy the same `syncGroup` inside `"visual"` (sibling of
  `visualType`), the same `visualType` and the same bound column:
  ```json
  "syncGroup": {"groupName": "PeriodSync", "fieldChanges": true, "filterChanges": true}
  ```
  `filterChanges` carries the selection, `fieldChanges` a change of the bound field. Microsoft's
  skill notes that the published `visualContainer` schemas do not list `syncGroup` while Desktop
  reads and writes it (as of 2026-10); a strict schema check may flag it. Verify in the service
  that a selection on page 1 shows on page 2. One group per slicer field (period, company, …).

**Text box** with mixed runs (title line 2: measure in bold, unit regular). `textStyle` values are
plain strings, not literals:
```json
{"visualType": "textbox",
 "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [
   {"value": "Revenue", "textStyle": {"fontSize": "10pt", "fontFamily": "Segoe UI", "fontWeight": "bold"}},
   {"value": " in mEUR", "textStyle": {"fontSize": "10pt", "fontFamily": "Segoe UI"}}]}]}}]}}
```

**tableEx with SVG measures** (KPI cards in one row, or a category column plus SVG columns):
```json
{"visualType": "tableEx",
 "query": {"queryState": {"Values": {"projections": [
   {"field": {"Column": {"Expression": {"SourceRef": {"Entity": "Company"}}, "Property": "Company Code"}},
    "queryRef": "Company.Company Code", "nativeQueryRef": "Company Code", "displayName": " "},
   {"field": {"Measure": {"Expression": {"SourceRef": {"Schema": "extension", "Entity": "<table>"}},
    "Property": "SVG Bar"}}, "queryRef": "<table>.SVG Bar", "nativeQueryRef": "SVG Bar",
    "displayName": "BU ▭  PY ▼  AC ■"}]}},
   "sortDefinition": {"sort": [{"field": {"Measure": {"Expression": {"SourceRef": {"Schema": "extension",
     "Entity": "<table>"}}, "Property": "SVG Bar"}}, "direction": "Descending"}], "isDefaultSort": true}},
 "objects": {
   "grid": [{"properties": {"imageHeight": {"expr": {"Literal": {"Value": "28D"}}},
     "imageWidth": {"expr": {"Literal": {"Value": "250D"}}},
     "gridHorizontal": {"expr": {"Literal": {"Value": "false"}}},
     "gridVertical": {"expr": {"Literal": {"Value": "false"}}},
     "rowPadding": {"expr": {"Literal": {"Value": "0D"}}}}}],
   "total": [{"properties": {"totals": {"expr": {"Literal": {"Value": "false"}}}}}],
   "columnHeaders": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "9D"}}},
     "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}}}],
   "values": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "9D"}}},
     "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}}}],
   "columnWidth": [
     {"properties": {"value": {"expr": {"Literal": {"Value": "260D"}}}}, "selector": {"metadata": "<table>.SVG Bar"}},
     {"properties": {"value": {"expr": {"Literal": {"Value": "44D"}}}}, "selector": {"metadata": "Company.Company Code"}}]}}
```
- `grid.imageWidth` / `imageHeight` apply to **every** image column of the table: an SVG narrower
  than `imageWidth` is stretched to it and then clipped by a narrower column. Give all SVG columns
  of one table the same SVG width = `imageWidth`, and each image column width ≥ `imageWidth` +
  20 px, or split them into separate tables. With less room the cell clips the image and the
  service draws a stray truncation mark (".") at the right end of every row (end-to-end test, as
  of 2026-10).
- Several chart tiers per row (bars + Δ bars + Δ% pins, card 26): draw them in **one** SVG per row
  with one shared GEOM block, not as one SVG column per tier, because all image columns share
  `imageWidth`. The tier names and the legend go into a static header image above the table (an
  `image` visual with an SVG from `RegisteredResources`, its x aligned with the image column and
  the same width as the SVG); hide the column header with `displayName: " "`.
- Never put `"active": true` on a table column: it collapsed the measure columns to 1 px and added
  a blank (N/A) row in the service.
- Sort the rows with a numeric sort key embedded in the SVG (e.g. a zero-padded `<desc>` value) or
  by a numeric measure: sorting an SVG text measure sorts its text.
- `sortDefinition` must name a **projected** field: a sort on a measure that is not in the table's
  `Values` is silently ignored and the rows come back sorted by the first column (alphabetically).
  Sort by the SVG measure itself (with its embedded sort key) or project the sort measure as a
  (narrow) column.
- `displayName: " "` hides a header; the KPI-card row has no header at all.

**Interactions** live in `page.json`, one entry per source → target pair that differs from the
default (filter):
```json
"visualInteractions": [{"source": "<slicer visual name>", "target": "<chart visual name>", "type": "NoFilter"}]
```
Types: `DataFilter` (cross-filter), `HighlightFilter` (highlight), `NoFilter`; the names
`Filter` and `Highlight` fail schema validation. Without an entry visuals cross-filter each other,
so add entries only to override that. Tiers of one chart get the same entries.

## 10. Verify after publishing

The service is stricter than a JSON check: a report can import cleanly and still fail every
visual (hidden or unmarked report measures). After each publish, look at the rendered page:

- **Browser**: open the report; on an error, *See details* shows the underlying error
  (`Missing_References`, …) and the fields concerned.
- **Without a browser**: the REST API *Reports – Export To File* (`format: PDF`; PNG may be disabled
  by the tenant) renders the page server-side with the same engine:
  `POST groups/<ws>/reports/<id>/ExportTo` `{"format": "PDF"}`, poll `…/exports/<exportId>` until
  `Succeeded`, then GET `…/exports/<exportId>/file`. `"powerBIReportConfiguration": {"pages":
  [{"pageName": "<page name>"}]}` in the POST body limits the export to pages. Needs the
  Fabric/Premium capacity the workspace already runs on.
  `fab api -A powerbi` works for the POST and the polling (JSON) but cannot save the binary file,
  so download it with a plain HTTP client and a Power BI token (audience
  `https://analysis.windows.net/powerbi/api`):
  `az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv`,
  then `curl -sf -o report.pdf -H "Authorization: Bearer $TOKEN" "https://api.powerbi.com/v1.0/myorg/groups/<ws>/reports/<id>/exports/<exportId>/file"`.
  Without the Azure CLI, the signed-in `fab` session can mint one from the Python environment fab
  is installed in: `from fabric_cli.core.fab_auth import FabAuth;
  print(FabAuth().get_access_token(["https://analysis.windows.net/powerbi/api/.default"], interactive_renew=False))`
  (an internal fab API, not a documented interface: check it after fab updates). Never print or
  log the token. Export a known-good report the same way as a control: if it renders
  and yours does not, the fault is in your report, not in the export.
- A Deneb visual can be checked before publishing with live data: `ibcs-deneb/scripts/render-previews.mjs
  --visual <visual.json>=<rows.json>` (rows from *Execute Queries* in the page's filter context).
