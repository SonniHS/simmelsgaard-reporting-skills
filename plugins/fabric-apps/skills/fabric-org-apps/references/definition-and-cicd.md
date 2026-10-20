# Org app definition, Git layout and automation

Based on Microsoft Learn "Org app definition" (Fabric REST item definitions) and "CI/CD for org
apps in Fabric", as of 2026-10. Schemas:
`https://developer.microsoft.com/json-schemas/fabric/item/orgapp/definition/orgAppDefinition/2.0.0/schema.json`
and `…/orgappaudience/definition/orgAppAudienceDefinition/1.0.0/schema.json`. Use **2.0.0** for the
app (1.0.0 has no audiences) and at least one audience.

## Contents
- [Git folder](#git-folder)
- [`definition.json` (org app)](#definitionjson-org-app)
- [Audience `definition.json`](#audience-definitionjson)
- [Including a Fabric App](#including-a-fabric-app)
- [Promotion options](#promotion-options)
- [Gotchas](#gotchas)

## Git folder

```text
Management pack.OrgApp/
├── .platform                     # type OrgApp, config.logicalId (never edit)
├── definition.json               # settings + elements (hierarchical)
└── .children/
    ├── Executives.OrgAppAudience/
    │   ├── .platform             # type OrgAppAudience, own logicalId
    │   └── definition.json       # parentAppId + settings + elementReferences (flat)
    └── Controllers.OrgAppAudience/
        └── …
Sales.SemanticModel/  Management pack.Report/  …
```

## `definition.json` (org app)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/orgapp/definition/orgAppDefinition/2.0.0/schema.json",
  "settings": {
    "theme": { "background": "#FFFFFF", "foreground": "#000000", "backgroundHover": "#F2F2F2",
               "backgroundSelected": "#D9D9D9", "backgroundPressed": "#BFBFBF" },
    "experienceSettings": { "navigationPane": { "isHidden": false, "isCollapsed": false, "independentPageNavigation": true } },
    "itemTypeSettings": { "report": { "hidePagePane": false } },
    "audienceSettings": { "hideAudienceTabs": false, "hideAllTab": true }
  },
  "elements": [
    { "elementType": "overview", "elementId": "<guid-1>", "displayName": "Overview",
      "header": { "title": "Management pack", "body": "Monthly reporting, data as of the last closed month.", "showTheme": false } },
    { "elementType": "section", "elementId": "<guid-2>", "displayName": "Results",
      "elements": [
        { "elementType": "item", "elementId": "<guid-3>", "itemType": "Report", "itemLogicalId": "<report logicalId>", "displayName": "Income statement" }
      ] },
    { "elementType": "link", "elementId": "<guid-4>", "displayName": "Notation manual", "url": "https://…", "linkType": "newtab" }
  ]
}
```

- The theme is neutral grey: it is app chrome, not chart colour. To make it token-driven, take the
  values from the table/grey groups of your IBCS token file.
- `elementId`s are your own GUIDs and must stay stable (audiences and bookmarks reference them).
- Item elements use `itemLogicalId` (Git) **or** `itemId` + `folderObjectId` (service ids).

## Audience `definition.json`

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/orgappaudience/definition/orgAppAudienceDefinition/1.0.0/schema.json",
  "settings": { "hasAccessToHiddenContent": false, "tabOrder": 0 },
  "parentAppId": "<org app .platform logicalId>",
  "elementReferences": [
    { "elementId": "<guid-1>" },
    { "elementId": "<guid-3>", "itemType": "Report", "itemLogicalId": "<report logicalId>" }
  ]
}
```

Audience **members** (users, groups) are not part of this file in the documented format; manage
them in the Fabric portal (org app **Share > Manage access**, choosing the audiences per
recipient), per stage. As of 2026-10 no REST API for audience membership was documented on
Microsoft Learn *(verify before scripting it)*.

## Including a Fabric App

1. Deploy the app to the stage workspace (`rayfin up`).
2. Add it to the dev org app in the UI, commit via Git integration, and read the generated element
   (its `itemType` value and whether it uses `itemLogicalId` or `itemId` / `folderObjectId`).
3. If the ids are stage-specific, parameterise them (deployment rule, fabric-cicd `parameter.yml`
   find/replace, or a REST `updateDefinition` step after `rayfin up`).
4. Grant semantic-model access (and SQL database access if the app writes) to the audience groups.

## Promotion options

| Option | Identity | Works for org apps (as of 2026-10) | Notes |
|---|---|---|---|
| Deployment pipeline (dev → test → prod) | **user** | yes, with deployment rules | not with a service principal; Direct Lake models need a data-source rule to rebind |
| Git integration per stage (branch per workspace) | user or service principal for Git operations | yes (preview) | update from Git per workspace; ids differ per workspace unless logical ids are used |
| fabric-cicd / `fab deploy` | service principal or user | **verify**: OrgApp was not in fabric-cicd's published item-type list | `parameter.yml` for ids and URLs |
| REST (create/update org app, audiences CRUD, `updateDefinition`) | service principal or user | yes for the definition; check principal support per endpoint | base64 `definition.json` + `.platform` parts |

REST sketch with the Fabric CLI (`fab`):

```bash
fab export "<domain>-dev.Workspace/Management pack.OrgApp" -o ./export
fab import "<domain>-test.Workspace/Management pack.OrgApp" -i "./export/Management pack.OrgApp" -f
# or: fab api -X post "workspaces/<workspace-id>/items/<item-id>/updateDefinition" -i body.json
```

Check exact commands with `fab --help` or Microsoft's Fabric CLI skills
(<https://github.com/microsoft/fabric-cli>); the item type in `fab` paths is `OrgApp`.

## Gotchas

- Commit with LF line endings; never edit `logicalId`.
- Sensitivity-labelled items may block export to Git unless the admin setting allows it.
- Unsupported items (Fabric Apps, dashboards) are ignored by Git, not deleted.
- Workspace inbound access protection disables deployment pipelines.
- An org app cannot be moved between workspaces; recreate it in the target workspace.
