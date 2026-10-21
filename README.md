# simmelsgaard-reporting-skills

A public Claude Code plugin marketplace with skills and agents for business reporting: IBCS®-style notation,
report and dashboard design, Power BI, Microsoft Fabric Apps, semantic models and the SQL behind them.

Status: early release (0.1). Tested against a Power BI report and a Fabric App; issues and feedback are welcome.

## Install

In Claude Code, add the marketplace once, then install the plugins you want:

```
/plugin marketplace add SonniHS/simmelsgaard-reporting-skills
/plugin install ibcs@simmelsgaard-reporting-skills
/plugin install ibcs-power-bi@simmelsgaard-reporting-skills
/plugin install fabric-apps@simmelsgaard-reporting-skills
/plugin install reporting-data@simmelsgaard-reporting-skills
```

Or from a shell:

```
claude plugin marketplace add SonniHS/simmelsgaard-reporting-skills
claude plugin install ibcs@simmelsgaard-reporting-skills
```

`ibcs-power-bi` and `fabric-apps` depend on `ibcs`, which is installed with them.
`/plugin marketplace update simmelsgaard-reporting-skills` fetches new versions. If new skills or agents do not show up,
restart Claude Code.

## Plugins

| Plugin | What it gives you | Builds on |
|---|---|---|
| [`ibcs`](plugins/ibcs/README.md) | Notation (scenarios, variances, colours, design tokens), page composition with a visual spec, web chart behaviour, review checklist and linter | – |
| [`ibcs-power-bi`](plugins/ibcs-power-bi/README.md) | IBCS-style Power BI reports: a route per visual, Deneb (Vega-Lite) templates with token sync, SVG-in-DAX tables | `ibcs` |
| [`fabric-apps`](plugins/fabric-apps/README.md) | Reporting apps on Microsoft Fabric, and Power BI org apps | `ibcs`, Microsoft's `rayfin` plugin |
| [`reporting-data`](plugins/reporting-data/README.md) | Semantic model for IBCS visuals, SQL gold layer, Dynamics 365 ERP source mappings | `ibcs` (optional) |

Start with `ibcs`; the others refer to its notation and composition skills.
For the Microsoft Fabric CLI, use Microsoft's own skills from [microsoft/fabric-cli](https://github.com/microsoft/fabric-cli).

## Licence

Prose (skills, agents, references) is CC BY-SA 4.0; code and data (scripts, templates, token files, tests) are MIT.
See [NOTICE](NOTICE), [LICENSE-CC-BY-SA-4.0](LICENSE-CC-BY-SA-4.0) and [LICENSE-MIT](LICENSE-MIT).

The skills follow the IBCS® Standards. IBCS® is a registered trademark of IBCS Institute; this project is not
affiliated with or certified by IBCS Institute.

## Development

```
python3 -m unittest discover -s tests -v     # manifests, frontmatter, links, plugin boundaries, leak scan
claude plugin validate --strict plugins/<plugin>
```
