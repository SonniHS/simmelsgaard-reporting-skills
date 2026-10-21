# Getting started

From a semantic model to a reviewed IBCS®-style page, as a Power BI report or a Microsoft Fabric
App. Each step is one prompt in Claude Code. The [sample](../examples/sample-sales/README.md) gives
you a small semantic model and a ready visual spec, so you can run the whole path before you point
it at your own model.

```
semantic model ──► visual spec ──► Power BI report  ─┐
 (reporting-data)   (ibcs)          (ibcs-power-bi)  ├─► review ──► deploy
                                    Fabric App       ─┘   (ibcs)
                                    (fabric-apps)
```

Before you start, check the [prerequisites](prerequisites.md): Claude Code, and for each route
Power BI Desktop with the Deneb visual, or a Fabric capacity with Fabric Apps enabled, plus
Microsoft's skills for Fabric and Power BI file mechanics.

## 1. Install the plugins

```
/plugin marketplace add SonniHS/simmelsgaard-reporting-skills
/plugin install ibcs@simmelsgaard-reporting-skills
/plugin install ibcs-power-bi@simmelsgaard-reporting-skills     # for Power BI reports
/plugin install fabric-apps@simmelsgaard-reporting-skills       # for Fabric Apps
/plugin install reporting-data@simmelsgaard-reporting-skills    # for building or changing the model
```

Restart Claude Code so the agents load. `/agents` should list `ibcs-visual-designer`,
`ibcs-reviewer` and the builders of the plugins you installed.

## 2. Have a semantic model

Use your own model, or deploy the sample model `Sample Sales` from
[examples/sample-sales](../examples/sample-sales/README.md) to a workspace you can write to (the
README there has the steps). An IBCS page works best on a model with a Scenario dimension and
variance measures; for a model that lacks them, ask the `semantic-model-architect` agent:

> Use the semantic-model-architect agent to review the semantic model `<path>/<Model>.SemanticModel`
> for IBCS reporting: scenarios AC, BU, PY, the variances ΔBU, ΔBU%, ΔPY, ΔPY% with impact, and the
> query shape a monthly column chart with a Total and a structure chart by region need. List the
> gaps and propose the TMDL changes; do not edit yet.

## 3. Design the page: the visual spec

The visual spec is a YAML file that fixes the message, title, charts, scenarios, variances and
scale groups before anyone builds. Both builders read it.

> Use the ibcs-visual-designer agent to design a Key figures page for the semantic model
> `Sample Sales`, for a management audience. Question: how does revenue develop against budget
> and prior year this year, and which regions drive the gap? KPI cards for the main measures,
> revenue by month with ΔBU and ΔBU% and a Total, revenue by region with ΔBU and ΔBU%. Write it to
> `./specs/sample-sales/key-figures.visual-spec.yaml`.

To skip this step, copy the sample spec from `examples/sample-sales/specs/`.

## 4a. Build a Power BI report

> Use the powerbi-report-builder agent to build a Power BI report (PBIP, live-connected to the
> semantic model `Sample Sales` in workspace `<workspace>`) from
> `./specs/sample-sales/key-figures.visual-spec.yaml`, into `./powerbi/SampleSales.Report`. Use
> the IBCS theme with rounded cards, Deneb for the column and structure charts, and validate the
> report before you stop. Do not publish.

Open the `.pbip` in Power BI Desktop to check it, or ask the agent to publish it once you are
satisfied (it never publishes on its own).

## 4b. Build a Fabric App

> Use the fabric-app-builder agent to build a Fabric App with the Key figures page from
> `./specs/sample-sales/key-figures.visual-spec.yaml` on the semantic model `Sample Sales` in
> workspace `<workspace>`, in `./app`. Start the chart layer from the ibcs-web-charts reference
> components. Use the Vite-only dev server (`npm run dev:frontend`), never `npm run dev`, which is
> `rayfin dev` in the dataapp template. Run the layout harness at 390, 1050 and 1280 px and the
> tests. Prepare the deployment, but do not run it.

The agent tells you the deploy command when the page is ready, for example
`npx rayfin up --workspace "<workspace>" --item-name "Sample Sales"`. Run it yourself, then open
the app item in the portal to check it there (some failures show only in the portal; see
[troubleshooting](troubleshooting.md)).

## 5. Review

> Use the ibcs-reviewer agent to review `./powerbi/SampleSales.Report` (or `./app` and its
> screenshots in `./app/screenshots/`) against the visual spec
> `./specs/sample-sales/key-figures.visual-spec.yaml`.

The reviewer returns a findings table (rule, severity, location, evidence, fix) and never edits
files. Hand the findings back to the builder:

> Fix the must-findings from the review above.

## 6. Deploy and share

- Power BI: publish from Desktop, or ask the builder to publish to a named workspace. To share
  reports and apps as an org app, use the `fabric-org-apps` skill (plugin `fabric-apps`).
- Fabric App: `npx rayfin up` with `--item-name`, as above; the `ibcs-fabric-app` skill covers
  CI/CD and environments.

## Next

- Point the same prompts at your own model and page.
- See what the skills draw in the [gallery](gallery.md).
- Something fails? See [troubleshooting](troubleshooting.md).
