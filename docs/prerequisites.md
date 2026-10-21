# Prerequisites

What you need to use each plugin, **as of 2026-10**. Power BI and Microsoft Fabric change monthly and
Fabric Apps are in preview, so re-check anything marked preview against Microsoft Learn before you
depend on it. Facts come from the plugins' own skills (file named in each row) and, for Microsoft
products, were checked against Microsoft Learn in 2026-10 (article linked).

## All plugins

| Need | Detail | Source |
|---|---|---|
| Claude Code with plugin support | The `/plugin` command or `claude plugin` CLI, to add this marketplace and install plugins. `ibcs-power-bi` and `fabric-apps` declare `ibcs` as a dependency, which is installed with them. | [README](../README.md) |
| Python 3 | Runs the bundled scripts (standard library only, run as `python3 -I`). The repository's tests run on Python 3.12 in CI. | each skill's `scripts/` |
| Node.js (some skills) | Token generation for web apps (`ibcs-notation`), the Deneb preview renderer (`ibcs-deneb`) and everything in `fabric-apps`. | see per plugin below |

## ibcs

Nothing beyond the above. The skills work on screenshots, specs, Vega-Lite files, PBIR folders and
web pages you give them. `scripts/gen_tokens.mjs` (writes the tokens as a TypeScript, JSON or CSS
module) needs Node.js; the linter `scripts/ibcs_lint.py` needs only Python.
Source: [ibcs-notation/SKILL.md](../plugins/ibcs/skills/ibcs-notation/SKILL.md),
[ibcs-review/SKILL.md](../plugins/ibcs/skills/ibcs-review/SKILL.md).

## ibcs-power-bi

| Need | Detail | Source |
|---|---|---|
| Power BI Desktop (Windows) | To open, check and publish the reports. Reports are written as a **Power BI Project (PBIP)** in the **enhanced report format (PBIR)**. Microsoft Learn states PBIP and PBIR are generally available and PBIR is the default format, in Power BI Desktop from the September 2026 release; on an older Desktop, save as PBIP with PBIR enabled. Detecting and reloading PBIP files changed outside Desktop is a preview feature (August 2026 release or later; *Options > Preview features > Detect and reload external PBIP changes*). The plugin's native `visual.json` recipes were checked against the schema and in the Power BI service, not yet opened in Desktop. | [feature-status.md](../plugins/ibcs-power-bi/skills/ibcs-power-bi/references/feature-status.md), [ibcs-power-bi/SKILL.md](../plugins/ibcs-power-bi/skills/ibcs-power-bi/SKILL.md); Learn: [Power BI Desktop projects](https://learn.microsoft.com/power-bi/developer/projects/projects-overview), [Edit PBIP files outside Power BI Desktop](https://learn.microsoft.com/power-bi/developer/projects/projects-external-editing) |
| Deneb custom visual | From AppSource. The templates target **Deneb 2.0** (Vega 6.4.0 / Vega-Lite 6.4.3, the versions Deneb 2.0 bundles). FC hatching uses `pbiPatternSVG()`, which needs Deneb's SVG renderer. | [ibcs-deneb/SKILL.md](../plugins/ibcs-power-bi/skills/ibcs-deneb/SKILL.md), [feature-status.md](../plugins/ibcs-power-bi/skills/ibcs-power-bi/references/feature-status.md) |
| A Power BI / Fabric workspace | Only to publish and to check the rendered page; the plugin writes local files and never publishes on its own. A live-connected report needs the semantic model's workspace and model to be reachable. | [pbir-skeleton.md](../plugins/ibcs-power-bi/skills/ibcs-power-bi/references/pbir-skeleton.md) |
| Fabric CLI `fab` (optional) | `fab api -A powerbi … executeQueries` fetches live rows for Deneb and SVG previews. Install with `pip install ms-fabric-cli` and sign in with `fab auth login`. | [ibcs-deneb/SKILL.md](../plugins/ibcs-power-bi/skills/ibcs-deneb/SKILL.md), [svg-skeletons.md](../plugins/ibcs-power-bi/skills/ibcs-svg-dax/references/svg-skeletons.md) |
| Node.js and Chrome (optional) | Node.js renders Deneb previews (Vega and Vega-Lite are installed into a scratch folder, not globally); a Chrome or Chromium binary turns previews into PNGs. | [ibcs-deneb/SKILL.md](../plugins/ibcs-power-bi/skills/ibcs-deneb/SKILL.md) |

## fabric-apps

| Need | Detail | Source |
|---|---|---|
| Fabric capacity | The app's workspace must have a **Fabric capacity** assigned; the skill's tested baseline is **F2 or larger, or a Fabric Trial**. Fabric Apps are **not available in every region**: some regions are Power BI-only (e.g. Denmark East), so put the app workspace on a capacity in a supported region; the semantic model may stay where it is. Query load is billed to the semantic model's capacity. | [ibcs-fabric-app/SKILL.md](../plugins/fabric-apps/skills/ibcs-fabric-app/SKILL.md) §1, [deploy-and-operate.md](../plugins/fabric-apps/skills/ibcs-fabric-app/references/deploy-and-operate.md) §3; Learn: [What is Fabric Apps (Preview)?](https://learn.microsoft.com/fabric/apps/overview), [Fabric region availability](https://learn.microsoft.com/fabric/admin/region-availability) |
| Tenant settings | A Fabric admin enables **Fabric Apps (preview)** (for the organisation or for security groups) and the **Semantic Model Execute Queries REST API** setting. For deployment from CI with a service principal, the tenant must also allow service principals to use Fabric APIs. | [ibcs-fabric-app/SKILL.md](../plugins/fabric-apps/skills/ibcs-fabric-app/SKILL.md) §1; Learn: [Create your first Fabric app](https://learn.microsoft.com/fabric/apps/create-app), [Create an app connected to a semantic model](https://learn.microsoft.com/fabric/apps/data-apps-template) |
| Permissions | Author: Contributor, Member or Admin on the app workspace, and **Build + Read** on the semantic model (Learn lists both for the data app template). Readers: access to the app and to the model; an org app does not grant model access. | as above |
| Microsoft's `rayfin` plugin | Authoritative for the Fabric Apps SDK and Rayfin CLI; this plugin builds on it. `/plugin marketplace add microsoft/rayfin`, then `/plugin install rayfin@rayfin-skills`. | [fabric-apps README](../plugins/fabric-apps/README.md) |
| Node.js LTS | Learn says "Node.js 20 or later"; the `create-rayfin` 1.36.2 package declares Node.js 20, 22 or 24. Node.js 20 reached end of life on 2026-04-30, so use 22 or 24 (LTS). | [ibcs-fabric-app/SKILL.md](../plugins/fabric-apps/skills/ibcs-fabric-app/SKILL.md) §1; Learn: [Create your first Fabric app](https://learn.microsoft.com/fabric/apps/create-app) |
| Fabric CLI `fab` | Used by `fabric-org-apps` to export and import org app definitions between workspaces, and for REST calls. Install with `pip install ms-fabric-cli`. | [definition-and-cicd.md](../plugins/fabric-apps/skills/fabric-org-apps/references/definition-and-cicd.md) |
| A semantic model | One the app can query as the signed-in user (RLS/OLS apply), ideally IBCS-ready (`reporting-data`). | [ibcs-fabric-app/SKILL.md](../plugins/fabric-apps/skills/ibcs-fabric-app/SKILL.md) §1 |

Viewer licensing for Fabric Apps below F64 was not documented as of 2026-10; test with a free-licence
account before you promise access
([deploy-and-operate.md](../plugins/fabric-apps/skills/ibcs-fabric-app/references/deploy-and-operate.md) §3).

## reporting-data

| Need | Detail | Source |
|---|---|---|
| Semantic model access | A Power BI or Fabric semantic model you can change (Contributor or higher on its workspace, or the PBIP/TMDL files in your repository), or **Build + Read** if you only query it. Tooling of your choice for TMDL: Power BI Desktop with PBIP, Tabular Editor, or Fabric Git integration. DAX user-defined functions need compatibility level 1702. | [semantic-model-ibcs/SKILL.md](../plugins/reporting-data/skills/semantic-model-ibcs/SKILL.md); Learn: [Build permission for shared semantic models](https://learn.microsoft.com/power-bi/connect-data/service-datasets-build-permissions) |
| A SQL target | One of: Fabric Warehouse, Lakehouse SQL analytics endpoint, SQL database in Fabric, Azure SQL Database / Managed Instance, or SQL Server 2019–2025 (some functions, such as `GENERATE_SERIES`, need SQL Server 2022 or later). A client to run T-SQL: `sqlcmd`, the Fabric portal, or Microsoft's Fabric skills. | [sql-reporting-backend/SKILL.md](../plugins/reporting-data/skills/sql-reporting-backend/SKILL.md), [platform-cheatsheet.md](../plugins/reporting-data/skills/sql-reporting-backend/references/platform-cheatsheet.md) |
| Dynamics 365 sources (optional) | For `dynamics-erp-reporting`: Finance & Operations or Dataverse via **Link to Fabric** (Fabric capacity in the same region as the Dataverse environment; the replica counts toward Dataverse capacity), or Business Central via bc2adls / open mirroring. Export to Data Lake reaches end of service on 30 November 2026. | [dynamics-erp-reporting/SKILL.md](../plugins/reporting-data/skills/dynamics-erp-reporting/SKILL.md) |

## Microsoft's Fabric skills

Two Microsoft repositories carry agent skills for Fabric (checked 2026-10):

| | [microsoft/fabric-cli](https://github.com/microsoft/fabric-cli) | [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) |
|---|---|---|
| What it is | The Fabric CLI (`fab`) itself, a Python package (`pip install ms-fabric-cli`) | A skill collection for coding agents, published as the marketplace **`fabric-collection`** |
| Skills | `.ai-assets/skills/`: `fabric-cli-core` and `fabric-cli-powerbi` (how to drive `fab`), plus context files and a prompt | `fabric-skills`: one bundle of 24 skills (warehouse, SQL database, Spark, eventhouse, dataflows, deployment pipelines, Git integration, semantic model authoring, cost estimation, migrations …), 4 agents and 3 remote MCP servers; `powerbi-authoring`: semantic model authoring and Power BI report skills |
| Claude Code install | No marketplace manifest: copy the skill folders into your skills directory by hand and update them by hand | `/plugin marketplace add microsoft/skills-for-fabric`, then `/plugin install …@fabric-collection` |
| Other plugin ids | – | `skills-for-fabric`, `fabric-authoring`, `fabric-consumption` and `fabric-operations` are **deprecated aliases** of `fabric-skills` (the persona bundles were retired) |

**Recommended for Claude Code users:**

```
/plugin marketplace add microsoft/skills-for-fabric
/plugin install fabric-skills@fabric-collection
```

Why: it is the only one of the two that installs and updates as a Claude Code plugin, it is Microsoft's
current, complete bundle (the other ids are deprecated aliases of it), and it covers the Fabric work
around these plugins: the SQL gold layer, semantic models, deployment pipelines and Git integration.
Its skills call the Fabric REST APIs through the Azure CLI (`az`), and its MCP servers reuse your Azure
CLI sign-in, so install the Azure CLI and run `az login` first. Enable auto-update for the
`fabric-collection` marketplace in `/plugin` > **Marketplaces** if you want new releases automatically.

If you script Fabric with `fab` (as some skills here do for previews and org app promotion), you can
add the two `fab` skills from microsoft/fabric-cli's `.ai-assets/skills/` by hand; they are not
packaged as a plugin.
