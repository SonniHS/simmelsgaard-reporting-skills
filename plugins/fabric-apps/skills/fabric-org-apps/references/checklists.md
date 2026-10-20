# Org app checklists

## A. Design (before creating the app)

- [ ] Audiences listed by reader role; each has an Entra security group (separate test and prod groups).
- [ ] Navigation = storyline: overview first, MECE sections, parallel names, links for the notation
      manual, glossary and methods.
- [ ] Every included report or app passes the `ibcs-review` checklist (plugin `ibcs`); titles carry active filters.
- [ ] Theme neutral (chrome only), logo ≤ 45 KB.
- [ ] "All" tab hidden if audiences are disjoint; no audience with access to hidden content.
- [ ] Data dependencies listed per item: semantic models, Fabric App data items, paginated sub-reports.

## B. Release (per stage)

- [ ] Models deployed and refreshed; connections bound (the first deploy usually needs a manual
      connection unless your deployment tool binds it).
- [ ] Warehouse / SQL database schema deployed separately (DACPAC, dbt, …) where the deployment
      tool only creates empty items.
- [ ] Translytical task-flow buttons re-pointed to this stage's function (they don't rebind).
- [ ] Reports and paginated reports deployed and rebound to the stage's models.
- [ ] Fabric App deployed with `rayfin up` (dry run reviewed); in-portal validation done.
- [ ] Org-app definition updated (Git, pipeline or REST); element ids stable; the Fabric App
      element points at this stage's app item.
- [ ] Audiences: membership and per-audience element visibility checked.
- [ ] Permissions the org app does not grant given to the audience groups: the Fabric App's
      semantic model, its SQL database (if it writes), RDL-referenced paginated reports.
- [ ] Smoke test with a **test account per audience** that has only app access: every item opens,
      data visible, RLS slice correct, Fabric App queries succeed (no 401/403).
- [ ] Subscriptions and bookmarks still valid (element ids unchanged).
- [ ] Release note: items changed, audiences changed, permission changes, rollback plan
      (re-import the previous definition from a Git tag).

## C. Access review (quarterly)

- [ ] Audience groups match current roles; leavers removed.
- [ ] No direct user grants on items or models (groups only).
- [ ] No audience with "access to hidden content".
- [ ] RLS roles mapped to groups; one test account per role still works.
- [ ] B2B guests reviewed.

## D. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Fabric App opens, every visual shows an access error | model access not granted (the org app doesn't propagate it for Fabric Apps) | grant it to the audience group; check the tenant setting for the Execute Queries REST API |
| User sees the app but an item is missing | item hidden for that audience | tick the item for the audience (propagates access) |
| Admin sees all rows, users see few | RLS doesn't apply to workspace Admin/Member/Contributor | test with app-only accounts |
| Report visuals fail only for some users | chained model / Direct Lake source permissions | grant along the chain |
| "Can't change permissions" | editor is a Contributor | Admin or Member with reshare on items and models |
| A change appeared in prod immediately | org apps have no versioning | edit only in dev; promote |
| Deployment pipeline fails as a service principal | pipelines can't deploy org apps as a service principal | user identity or REST |
| Bookmarks or subscriptions broke after redeploy | element ids regenerated | keep `elementId`s stable in Git |
