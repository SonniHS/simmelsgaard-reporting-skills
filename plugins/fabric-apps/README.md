# fabric-apps

Build reporting apps on Microsoft Fabric that follow the IBCS® Standards, and ship them to readers.
The `ibcs-fabric-app` skill covers a Fabric App (React + TypeScript, DAX against a Power BI semantic
model as the signed-in user) from visual spec to deployment: page patterns, the query → chart data
contract, states, RLS/OLS testing, performance, CI and capacity notes. The `fabric-org-apps` skill
packages reports, paginated reports and Fabric Apps into org apps with audiences, permissions and
dev/test/prod promotion. This plugin **builds on Microsoft's `rayfin` plugin** for the Fabric Apps
SDK and CLI mechanics rather than replacing it: install both, and the Rayfin skills stay
authoritative for SDK and CLI questions while this plugin adds the IBCS presentation and the
operational decisions. Product facts are dated (as of 2026-10); Fabric Apps were in preview then.

## Install

```
/plugin marketplace add SonniHS/simmelsgaard-skills
/plugin install fabric-apps@simmelsgaard-skills
```

This also installs the `ibcs` plugin, a declared dependency (its notation, composition and review
skills). `reporting-data` is optional; install it for the semantic-model skills.

Recommended alongside it:

```
/plugin marketplace add microsoft/rayfin
/plugin install rayfin@rayfin-skills
```

## Skills and agents

- `ibcs-fabric-app` (skill): build, review and deploy an IBCS Fabric App on a semantic model; replaces the data-app template's design guidance with IBCS rules.
- `fabric-org-apps` (skill): package and distribute reports and Fabric Apps as org apps; audiences, permissions, Git/pipelines/REST, checklists.
- `fabric-app-builder` (agent): implements app pages from a visual spec, tests queries and screenshots, and prepares but never runs deployment.

## Examples

- "Build a Fabric App page from `./specs/sales/overview.visual-spec.yaml` on our Sales semantic model."
- "Our Fabric App shows blank amounts in the portal but works locally. Why?"
- "Set up GitHub Actions to deploy this Fabric App to test on merge and to prod with approval."
- "Package the finance reports and our Fabric App into an org app with audiences for executives and controllers."
- "Users can open the org app but every visual in the Fabric App fails with an access error."

## Works with

- `ibcs`: the `ibcs-web-charts` skill (chart behaviour contract), `ibcs-composition` (visual spec), `ibcs-notation` (token file), `ibcs-review`, and the `ibcs-visual-designer` agent.
- `reporting-data`: the `semantic-model-ibcs` skill (IBCS-ready model and per-card DAX).
- `ibcs-power-bi`: for Power BI reports in the same org app.
- Microsoft's `rayfin` plugin (<https://github.com/microsoft/rayfin>) and the in-project skills its scaffold installs: authoritative for Fabric Apps SDK/CLI mechanics.
- Fabric CLI (`fab`): install Microsoft's own skills from <https://github.com/microsoft/fabric-cli>; this marketplace does not ship Fabric CLI skills.

## Licence

Prose is shared under CC BY-SA 4.0; code and data under MIT; see NOTICE and the two LICENSE files in this plugin. This plugin follows the
IBCS® Standards; IBCS® is a registered trademark of IBCS Institute. Not affiliated with or
certified by IBCS Institute. Microsoft, Fabric and Power BI are trademarks of the Microsoft group
of companies.
