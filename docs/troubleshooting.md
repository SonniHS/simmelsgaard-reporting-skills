# Troubleshooting

Failures seen while building IBCS®-style reports and apps with these plugins, with their causes and
fixes. Each entry links to the skill reference that covers it in depth. Dates mark when a behaviour
was observed; products change, so check the linked reference for the current state.

## Contents

- [Plugins and skills](#plugins-and-skills)
- [Power BI reports](#power-bi-reports)
- [Deneb visuals](#deneb-visuals)
- [Fabric Apps: failures only in the portal](#fabric-apps-failures-only-in-the-portal)
- [Fabric Apps: local development loop](#fabric-apps-local-development-loop)
- [Org apps and access](#org-apps-and-access)
- [Web charts](#web-charts)

## Plugins and skills

| Symptom | Cause and fix |
|---|---|
| A skill or agent does not show up after an update | Run `/plugin marketplace update simmelsgaard-reporting-skills`, then restart Claude Code. |
| `/plugin install …@simmelsgaard-skills` fails | The marketplace was renamed. Remove the old one (`/plugin marketplace remove simmelsgaard-skills`), add `SonniHS/simmelsgaard-reporting-skills`, and install with `<plugin>@simmelsgaard-reporting-skills`. |
| Claude builds a chart with a legend box, gridlines or a hue per scenario | The IBCS skills were not loaded for the task. Name the skill or agent in the prompt (`ibcs-visual-designer`, `ibcs-web-charts`, `ibcs-deneb`), or start from a visual spec ([getting started](getting-started.md)). |
| A review passes but the page still looks wrong | The linter checks metadata only. Run the manual checklist of `ibcs-review` on a screenshot as well (the `ibcs-reviewer` agent does both). |

## Power BI reports

| Symptom | Cause and fix |
|---|---|
| Every visual using a report-level measure shows "Something's wrong with one or more fields" (`Missing_References`) in the service, but works in Desktop | The visual binds the measure without `"Schema": "extension"`, or the measure lacks its `references` list. Run `report_measures.py <name>.Report --fix`, then `--check` before every publish (ibcs-power-bi skill, `pbir-skeleton.md` §5; observed 2026-10). |
| The same error after you hid a helper measure | Never set `"hidden": true` on a report-level measure; in the service that breaks every visual that uses it or a measure built on it. Use a `displayFolder` instead. `--fix` removes the flag. |
| Microsoft's PBIR validator rejects a slicer | Slicer font sizes are `textSize` on `header` and `items`; `fontSize` there is rejected (`pbir-skeleton.md`). |
| The validator rejects an image table | Do not set `columnHeaders` or `values` `outline` to `'None'`; hide the rules with a white `grid` outline of weight 0 (`page-shell.md`). |
| An image column scrolls inside its table | Keep the column width at `imageWidth` + 20 and the visual at least the column width + its padding + 2 (`page-shell.md`; the linter checks it). |
| Charts on one page use different scales | Every chart of one unit must share one px per unit. Build the page from `scale_layout.py` output (`layout.json`) and run `ibcs_lint.py pbir … --layout layout.json` (ibcs-power-bi skill). |
| A dynamic format string is ignored in a live-connected report | Report-level measures in a live-connect report take static format strings only (Learn); keep dynamic formats in the semantic model. |

To see what the service renders without opening a browser, export the page to PDF with the REST
`ExportTo` call and look at the PNG (`pbir-skeleton.md`, verification).

## Deneb visuals

| Symptom | Cause and fix |
|---|---|
| FC columns are solid instead of hatched | Deneb must render in **SVG** mode; the hatch uses `pbiPatternSVG`. Set the renderer to SVG in the visual's settings. |
| Months appear in alphabetical order | Deneb keeps the query order. Sort the visual by the period field (`to_pbir.py --sort`). |
| A template preview differs from Power BI | The preview renderer uses the Vega and Vega-Lite versions bundled with Deneb 2.0 (Vega 6.4.0, Vega-Lite 6.4.3). Check the Deneb version in your report; older Deneb builds bundle older Vega. |
| A tiny Total or a small entity flattens the other charts | The shared scale is working as intended. Give that chart its own scale group with a scale band and a footnote (ibcs-deneb Total-column knobs; `ibcs-composition` visual spec §4). |

## Fabric Apps: failures only in the portal

The portal runs the app in nested cross-origin frames and hands it query results in a different
shape than the terminal does. A page that works in `npm run dev` or with the CLI can still fail
there. Debug it through the dev-URI embed below.

| Symptom | Cause and fix |
|---|---|
| Amounts are blank (or 10 000 times too small) in the portal, correct locally | Currency values arrive as unscaled strings in union-typed columns, for example a "one row per KPI" query that mixes amounts and ratios. Give every value column one type in the query (`CONVERT ( [Revenue], DOUBLE )`, `CONVERT ( BLANK (), DOUBLE )`) and normalise centrally by column type (ibcs-fabric-app `queries-and-data.md`; observed 2026-10). |
| A query fails with a DAX syntax error in the portal only | A selection substitution matched a comment line and inserted a `VAR` above `DEFINE`. Match only the tagged line, anchored (`queries-and-data.md`, factory-output test). |
| Footnote numbers are missing, a tab change keeps the scroll position, or charts are narrow in the portal | Known shell issues, fixed in the `ibcs-fabric-app` report shell (`report-shell.md`): footnote numbers as text, scroll to top on route change, charts filling the card width. Check in the portal, not only in the harness. |
| The browser console shows nothing useful | The app's console is not readable from the portal tab. In dev builds show the raw error under the user-facing message (`queries-and-data.md`). |

## Fabric Apps: local development loop

| Symptom | Cause and fix |
|---|---|
| The portal does not load your local build with `&devUri=http://localhost:<port>` | Chrome's Local Network Access check blocks a public site from framing localhost. Allow local-network access when the browser asks; an automated browser needs the flag from Microsoft's `app-validation` skill (`queries-and-data.md`). |
| Sign-in fails with a redirect error | The port is not the same in all three places. Pin it in `vite.config.ts` (`strictPort: true`), under `services.auth.allowedRedirectUris` in `rayfin/rayfin.yml`, and in the `&devUri=` value; the redirect list reaches the tenant on the next `rayfin up`. |
| `npx rayfin dev` asked for tenant changes | It provisions a backend in the tenant. Use `npm run dev` plus the dev-URI embed instead, and deploy only with approval (`deploy-and-operate.md`). |
| There is no app item yet, but you need to test queries | Run them from the terminal: `npx fabric-app-data query <alias> --file src/queries/<page>/<viz>.dax`. |

## Org apps and access

| Symptom | Cause and fix |
|---|---|
| Users open the org app, but every query in the Fabric App fails with 401/403 | The audience has no access to the semantic model (Read, or Build + Read, depending on how the app queries; `ibcs-fabric-app` §1), or to the app's SQL database if it writes commentary. Grant it to the same Entra groups as the app audience (`fabric-org-apps` skill). |
| Service principals cannot query the model | Not supported against models with RLS or SSO; Fabric Apps query as the signed-in user (`queries-and-data.md`). |

## Web charts

| Symptom | Cause and fix |
|---|---|
| FC hatching disappears in an iframe or shadow root | `url(#id)` must resolve inside the same document. Keep each chart's `<pattern>` in its own SVG with an id unique per instance; the reference renderer does this (`ibcs-web-charts` reference components). |
| The page scrolls sideways at 390 px for no visible reason | A visually hidden `<table>` ignores its 1 px width. Put the hidden class on a wrapping `<div>` (`ibcs-web-charts` `testing.md`). |
| A 390 px screenshot looks fine, but phones scroll | `--window-size=390,…` lays the page out wider. Emulate the device viewport (Playwright `setViewportSize`, CDP `Emulation.setDeviceMetricsOverride`). |
| Labels collide at about 1050 px but not at 390 or 1280 | Test at the host's content width too (the Fabric portal leaves about 1050 px). |
