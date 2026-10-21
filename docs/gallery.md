# Gallery

What the plugins produce, rendered from **generic sample data**. Every picture here is regenerated
by a script in the repository, so it shows what the skills draw today.

## A Key figures page from the reference components

The `ibcs-web-charts` reference components (plugin `ibcs`): KPI cards, months with a Total on its
own scale (scale band, aligned tiers), structure bars with ΔBU and ΔBU%, and a bridge from PY to
AC, on rounded cards. Source and tests:
[react-reference](../plugins/ibcs/skills/ibcs-web-charts/assets/react-reference/README.md).

![Key figures page built with the reference components](../plugins/ibcs/skills/ibcs-web-charts/assets/react-reference/previews/page.png)

## Deneb templates for Power BI

The `ibcs-deneb` skill (plugin `ibcs-power-bi`): eleven token-driven Vega-Lite templates, previewed
with the Vega version that Deneb 2.0 bundles. More variants (narrow, all-negative, outliers, scale
bands) are in [the previews folder](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/),
and the knobs of each template are in
[templates.md](../plugins/ibcs-power-bi/skills/ibcs-deneb/references/templates.md).

| Preview | Template |
|---|---|
| ![Column chart over time with ΔBU and ΔBU% tiers, PY triangles](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/column-two-tier-variance-bu-py-triangle.png) | Column chart over time with ΔBU and ΔBU% tiers, PY triangles |
| ![Two charts in one scale group: the smaller one is shorter, never stretched](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/column-two-tier-variance-scale-group.png) | Months and a Total on their own scales with aligned tiers |
| ![Structure bars with triangles, ΔBU bars and ΔBU% pins](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/bar-structure-variance-bu-py-triangle.png) | Structure bars with triangles, ΔBU bars and ΔBU% pins |
| ![Variance waterfall (bridge) from PY to AC](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/waterfall-variance.png) | Variance waterfall (bridge) from PY to AC |
| ![Bridge with a magnifier](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/waterfall-variance-magnifier.png) | Bridge whose steps are under 5 % of the base: a steps-only panel at ×k (CH 4.5) |
| ![Time bridge](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/waterfall-variance-time.png) | Variance waterfall over time (card A-11): PY, monthly Δ, AC |
| ![Calculation waterfall (P&L)](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/waterfall-calculation.png) | Calculation waterfall (P&L) |
| ![Line chart: AC&FC with PY and BU](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/line-scenarios.png) | Line chart: AC&FC with PY and BU |
| ![Relative variance pins](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/pin-relative-variance.png) | Relative variance pins |
| ![Relative variance scatter](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/scatter-relative.png) | Relative variance scatter |
| ![Small multiples on one shared scale](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/small-multiples-columns.png) | Small multiples on one shared scale |
| ![Stacked columns](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/stacked-columns.png) | Stacked columns |
| ![Columns by forecast version](../plugins/ibcs-power-bi/skills/ibcs-deneb/assets/previews/column-version-axis.png) | Columns by forecast version |

## Reports and apps built end to end

Screenshots of the sample report and app from the [getting-started](getting-started.md) run will
follow here with the 1.0.0 release.
