---
name: fabric-org-apps
description: >
  Packages Power BI reports, paginated reports and Fabric Apps into Microsoft Fabric org apps
  (item types OrgApp + OrgAppAudience) and runs them through dev/test/prod; use it whenever
  someone wants to publish, distribute, share or "make an app" of reports or a Fabric App for an
  audience, even if they just say "Power BI app". Covers navigation (overview, sections, items,
  links), audiences, permissions (what is granted automatically, such as Read on report semantic
  models even across workspaces, and what is not, such as the data items a Fabric App reads),
  RLS/OLS behaviour, no versioning (save = live), Git integration of the definition (schema
  v2.0.0) and audiences, deployment pipelines, fabric-cicd, REST APIs, and release and access
  checklists. Also for migrating a workspace app to an org app, setting up audiences, fixing
  "users can't see data in the app" and automating org app deployment.
---

# Fabric org apps: packaging and distribution

Facts as of 2026-10: org apps are GA, audiences GA since July 2026; several adjacent pieces (Git
integration of org apps, Fabric Apps) are preview. Re-check Microsoft Learn before promising
behaviour. Companion: [ibcs-fabric-app](../ibcs-fabric-app/SKILL.md) (building the Fabric App).
For Fabric CLI mechanics (`fab`, Git integration, deployment pipelines) use Microsoft's own skills
from <https://github.com/microsoft/fabric-cli>.

## 1. When an org app, and when not

| Need | Use |
|---|---|
| Curated set of reports, paginated reports, Fabric Apps, notebooks, maps or real-time dashboards for internal (Entra, incl. B2B guest) users | **Org app** (many per workspace, with audiences) |
| Existing workspace app | keep it or recreate it as an org app (no automatic migration); workspace apps are legacy but supported |
| External customers without Entra accounts | Power BI Embedded (app owns data), not org apps, not Fabric Apps |
| Dashboards (tiles) or scorecards | not eligible in org apps |

All included items must live in the **same workspace** as the org app. The workspace needs Pro,
Trial, Premium or Fabric capacity (Fabric Apps need Fabric capacity).

## 2. Design the app (IBCS view)

- **Navigation = storyline** (IBCS v2.0, ST 5.1): `overview` (landing page with header title and
  body) → `section`s that are MECE and grammatically parallel ("Sales", "Margin", "Costs") →
  `item`s (reports, the Fabric App, paginated packs) → `link`s (embedded or new tab) for methods,
  glossary and the notation manual.
- The org-app **theme colours only the chrome** (background, foreground, hover, selected,
  pressed). Keep it neutral grey/white so it never competes with scenario notation or impact
  colours; IBCS notation lives in the reports and apps. Logo ≤ 45 KB (data URL in the definition).
- Show report pages in the navigation when pages are the storyline
  (`independentPageNavigation`); hide the page pane (`hidePagePane`) when a report has its own
  navigation.
- Audiences = reader roles (executive pack, division heads, controllers), not one per person.
  Audiences exist only in **new** org apps, which always keep at least one audience. Hide the
  "All" tab (`hideAllTab`) when audiences are disjoint, so readers don't see a confusing union.
- A Fabric App is one item; its internal pages keep their own navigation. Don't duplicate them as
  org-app sections.

## 3. Permissions: the part that breaks

| Grant | What users get (as of 2026-10) |
|---|---|
| Org-app access (via audience) | **Read** on visible items; **Read on the semantic models behind reports and paginated reports, also across workspaces**; **Read + Execute** on included Fabric Apps |
| Not propagated | paginated reports referenced by RDL visuals; **the items a Fabric App reads or writes (its semantic model, SQL database, lakehouse)** |
| "Access to hidden content" on any audience | every app user gets access to **all** items: avoid |
| Removing a user / hiding an item | org-app-derived access is revoked automatically |

So for a Fabric App, grant model access (see [ibcs-fabric-app](../ibcs-fabric-app/SKILL.md) §1 on
Read vs Build + Read) and, if it writes commentary, access to its SQL database to the **same Entra
groups** as the audience. Otherwise users open the app and every query fails with 401/403. Prefer
groups over individuals everywhere.

Who may change access: write + reshare on the included items and their models, so in practice
workspace Admin or Member. Contributors can edit content but not access, and the workspace setting
"allow contributors to update the app" does not apply to org apps.

RLS/OLS: org-app users get Read, so model roles apply to them. RLS does **not** apply to workspace
Admin/Member/Contributor; test with an account that has only app access (or "View as" / "Test as
role" on the model). Direct Lake or DirectQuery chains need access along the chain.

## 4. Lifecycle: no versioning, so one workspace per stage

**Save = live** in an org app: there is no "publish update". Staging is a workspace per stage
(`<domain>-dev` → `<domain>-test` → `<domain>-prod`), each with its own org app.

| Mechanism | Org apps (as of 2026-10) | Notes |
|---|---|---|
| Git integration | supported (preview): `<name>.OrgApp/` with `.platform`, `definition.json` (schema v2.0.0), `.children/<audience>.OrgAppAudience/` | items referenced by `itemLogicalId`; audience `parentAppId` = the org app's `logicalId`; audience element references are flat |
| Deployment pipelines | supported with deployment rules | **not with a service principal**: promote with a user identity (or REST) |
| fabric-cicd | named by Learn as able to consume org-app definitions, but `OrgApp` was not in its published item-type list | verify the changelog before relying on it |
| REST | CRUD for org apps and audiences, plus `getDefinition` / `updateDefinition` (base64 parts) | fallback for automation; `fab import` / `fab api` wrap it |
| Fabric Apps | **not** in Git integration or pipelines | deploy with `rayfin up` per stage first, then reference the app from the org app |

Order per stage: semantic model → reports / paginated reports → Fabric App (`rayfin up`) → org-app
definition → audiences → permissions on models and app data items.

Because Fabric App items are not Git-synced, an org-app element pointing at one may need the
stage-specific `itemId` + `folderObjectId` instead of `itemLogicalId`. Verify by committing a dev
org app that includes the Fabric App and inspecting `definition.json`; parameterise the ids per
stage. Details and file examples: [references/definition-and-cicd.md](references/definition-and-cicd.md).

## 5. Checklists

Design, release and access-review checklists plus troubleshooting ("users see the app but no
data", "item missing for an audience", "bookmarks broke"):
[references/checklists.md](references/checklists.md).

## Guardrails

- Never change audiences, permissions or a production org app without an explicit request; every
  save is live.
- Never grant "access to hidden content" or individual-user permissions as a shortcut.
- Never print or commit service-principal secrets. Org-app promotion by a service principal isn't
  supported through pipelines; don't work around it with stored user credentials.
