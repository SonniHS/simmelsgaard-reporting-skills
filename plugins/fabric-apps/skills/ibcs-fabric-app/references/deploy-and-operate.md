# Deploy and operate a Fabric App

Status as of 2026-10: Fabric Apps are in **preview** (since June 2026). Re-check Microsoft Learn
before relying on any limit below, and verify flags with `rayfin --help` / `rayfin docs` in the
project: the in-project Rayfin skills are authoritative.

## Contents
- [1. Environments](#1-environments)
- [2. GitHub Actions with a service principal](#2-github-actions-with-a-service-principal)
- [3. Capacity, region, licensing (as of 2026-10)](#3-capacity-region-licensing-as-of-2026-10)
- [4. Release checklist](#4-release-checklist)
- [5. Operate](#5-operate)

## 1. Environments

**Approval first.** Every `rayfin up` is a deployment, **including `--dry-run`**: the dry run signs
in, checks the licence and resolves the workspace and target in the tenant (Rayfin CLI 1.36,
2026-10). The in-project `rayfin` skill tells agents to run the full deploy; this skill overrides
it: run neither without the user's explicit approval in the current task, and the same for
`npx rayfin dev` (it provisions a backend) and for any npm script that calls `rayfin dev` or
`rayfin up` (in the `dataapp` template `npm run dev` **is** `rayfin dev`; read the `scripts` in
`package.json` first). Without approval, hand the user the exact command.

**Name the target.** Without flags, `rayfin up` picks its target in this order (Rayfin CLI 1.36,
2026-10): `--workspace` / `--workspace-id`, then the `RAYFIN_WORKSPACE_ID` environment variable,
then the recorded deployment in `rayfin/.deployments.json` (which may be production), then a
prompt that offers a new workspace (a non-interactive run fails). The item is named after the
project `id` in `rayfin.yml`. `rayfin/.deployments.json` and `rayfin/.env` are gitignored by the
template; keep them that way, because a shared registry whose recorded target is prod turns every
untargeted deploy into a prod deploy. Always pass both:

```bash
npx rayfin up --workspace "<workspace name>" --item-name "<item name>"
```

`--workspace-id <guid>` instead of `--workspace` when names are ambiguous; the CLI sanitises the
workspace name it prints (`"My Test" → my-test`), which is cosmetic.

**Commands for the user to paste: one line, or a script.** A command wrapped over two lines in the
chat arrives as two commands when pasted (`error: option '--item-name <name>' argument missing`,
then the item name runs as a command; hit twice in the 2026-10 test). Give one-line commands, never
a `\` continuation; for anything longer, write a small script into the project (`deploy.sh` with
`cd "$(dirname "$0")"`) and give `sh <path>/deploy.sh`.

**Which URL users open.** With the scaffold's Fabric data client (path A in
[queries-and-data.md](queries-and-data.md) §0), users open the **app item in the Fabric portal**
(the portal URL `rayfin up` prints). The static-hosting URL it also prints signs in but never
loads data (the data proxy needs the portal frame). Share the portal URL, or package the item in an
org app ([fabric-org-apps](../../fabric-org-apps/SKILL.md)).

**Check in the portal after each deploy.** It needs a browser signed in to the tenant that the
agent can drive; without one, report the check as not run and hand the user the item URL and the
list of checks. A failure that shows only in the portal is debugged through the dev-URI embed with
the raw error shown in dev builds ([queries-and-data.md](queries-and-data.md) §0).

| Env | Workspace | Who deploys | How |
|---|---|---|---|
| dev | `<app>-dev` (per developer or shared) | developer, with approval | `npx rayfin up --workspace "<app>-dev" --item-name "<app>"` |
| test | `<app>-test` | CI on merge to `main`, or manually | PRs: `npx rayfin up --workspace "<app>-test" --item-name "<app>" --dry-run`; merge: `npx rayfin up --workspace "<app>-test" --item-name "<app>" --yes` |
| prod | `<app>-prod` | CI with manual approval (GitHub environment protection) | `npx rayfin up --workspace "<app>-prod" --item-name "<app>" --yes` |

`--yes` skips the prompts: it approves an automatic capacity assignment **and** the reuse of an
existing item with the same name in the target workspace (Rayfin deploy docs, 2026-10). Use it
only in CI against a workspace created for that environment, never on a first deploy into a
shared workspace.

- No versioning in the service: the repo and its tags are the history; roll back by redeploying a tag.
- Schema apply refuses destructive changes unless `--force`. Pass `--force` only from a manual,
  reviewed run with the planned operations pasted into the PR.
- The CLI writes deployment ids to `rayfin/.deployments.json` and `rayfin/.env`; both are
  gitignored by the template, keep them out of Git. Secrets never go in the repo.
- Point dev/test apps at test copies of the semantic model and prod at the certified model; keep
  connection ids per environment in the CLI's environment files, not in source.

## 2. GitHub Actions with a service principal

Adapted from Microsoft Learn "Deploy a Fabric app with GitHub Actions" (check the current version);
pin the CLI version instead of `latest`. Changed from the upstream sample: `cancel-in-progress:
false` (upstream `true`; a cancelled `rayfin up` can stop a schema apply halfway) and the `force`
input passed through `env:` instead of `${{ }}` inside `run:`.

```yaml
name: Deploy to Fabric
on:
  push: { branches: [main] }
  workflow_dispatch:
    inputs:
      force: { description: "Allow destructive schema changes (data loss)", type: boolean, default: false }
concurrency: { group: "${{ github.workflow }}-${{ github.ref }}", cancel-in-progress: false }   # queue, never cancel a schema apply midway
permissions: { contents: read }
env:
  RAYFIN_ENCRYPTION_FALLBACK_ENABLED: "true"   # hosted Linux runners have no OS keychain; the runner is ephemeral
jobs:
  deploy-test:
    runs-on: ubuntu-latest
    environment: test
    env:
      CLIENT_ID: ${{ secrets.CLIENT_ID }}
      TENANT_ID: ${{ secrets.TENANT_ID }}
      CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
      FABRIC_WORKSPACE_NAME: ${{ vars.FABRIC_WORKSPACE_NAME }}   # <app>-test in the test environment
      FABRIC_APP_NAME: ${{ vars.FABRIC_APP_NAME }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22", cache: "npm" }
      - run: npm ci
      - run: npm run typecheck && npm test
      - name: Login (service principal)
        run: npx rayfin login --service-principal --tenant "$TENANT_ID" --client-id "$CLIENT_ID" --client-secret "$CLIENT_SECRET"
      - name: Deploy to test
        run: npx rayfin up --workspace "$FABRIC_WORKSPACE_NAME" --item-name "$FABRIC_APP_NAME" --yes
      - if: always()
        run: npx rayfin logout
  deploy-prod:
    needs: deploy-test
    runs-on: ubuntu-latest
    environment: prod                      # protection rule = manual approval
    env:
      CLIENT_ID: ${{ secrets.CLIENT_ID }}
      TENANT_ID: ${{ secrets.TENANT_ID }}
      CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
      FABRIC_WORKSPACE_NAME: ${{ vars.FABRIC_WORKSPACE_NAME }}   # <app>-prod in the prod environment
      FABRIC_APP_NAME: ${{ vars.FABRIC_APP_NAME }}
      FORCE: ${{ inputs.force }}           # via env, not interpolated into the script
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22", cache: "npm" }
      - run: npm ci
      - name: Login (service principal)
        run: npx rayfin login --service-principal --tenant "$TENANT_ID" --client-id "$CLIENT_ID" --client-secret "$CLIENT_SECRET"
      - name: Deploy to prod
        run: |
          EXTRA=""
          if [[ "$FORCE" == "true" ]]; then EXTRA="--force"; fi
          npx rayfin up --workspace "$FABRIC_WORKSPACE_NAME" --item-name "$FABRIC_APP_NAME" --yes $EXTRA
      - if: always()
        run: npx rayfin logout
```

PR workflow (a separate file, `on: pull_request`): one job with `environment: test`, the same
setup, login and logout steps, and
`npx rayfin up --workspace "$FABRIC_WORKSPACE_NAME" --item-name "$FABRIC_APP_NAME" --dry-run`
(no `--yes`).

- `npm run typecheck` does not exist in the `dataapp` scaffold (`create-rayfin` 1.36.2): its
  `build` runs `tsc -b --noCheck`, so type errors never fail a build. Add
  `"typecheck": "fabric-app-data generate -o src/fabric.generated.ts && tsc -b"` to `package.json`
  scripts first: the generated client is gitignored, so a clean CI checkout needs it generated
  before `tsc`.
- Use the CLI version from the project's `devDependencies` (`npx rayfin …`) so CI and local match.
- Service-principal prerequisites: tenant setting allowing service principals to use Fabric APIs,
  the principal as **Contributor or higher** on the target workspace, workspaces created beforehand.
- Prefer federated credentials (OIDC) over a client secret where the CLI supports it
  (`rayfin login --help`). `RAYFIN_TOKEN` (a pre-acquired bearer token) is the documented
  alternative to `rayfin login` in a pipeline.
- **Service-principal sign-in is not settled (2026-10).** The Learn CLI reference
  (`fabric/apps/cli-reference`) lists `--service-principal` as "not currently supported", while the
  Learn GitHub Actions article and the Rayfin docs (`app-backend/deploy.md`, CLI 1.36) document it
  with `--client-id`, `--client-secret` and `--tenant`. Verify with a `--dry-run` into a test
  workspace before relying on CI; the manual `rayfin up` by a person with deploy rights stays the
  fallback.
- `RAYFIN_ENCRYPTION_FALLBACK_ENABLED=true` lets the CLI keep its token cache in plain text on a
  machine without OS credential storage (Rayfin docs: development only). Hosted Linux runners have
  no keychain, so the login fails without it; the runner is discarded after the job and the final
  `rayfin logout` clears the cache. Never set it on a shared or self-hosted runner.

## 3. Capacity, region, licensing (as of 2026-10)

- An F SKU is required (F2+, Trial works), billed in capacity units from the workspace's capacity.
  Query load is billed to the **semantic model's** capacity.
- Fabric Apps (preview) are not available in every region: not in the Power BI-only regions
  (e.g. Denmark East) and, as of 2026-10, not in several full-Fabric regions either (e.g. UK South
  and West, Canada Central and East, Brazil South, Australia Southeast). Check the capacity's
  region against the "Unavailable Fabric features" column of
  [Fabric region availability](https://learn.microsoft.com/fabric/admin/region-availability), put
  the app workspace on a capacity in a supported region, and check data-residency requirements
  before moving anything.
- Viewer licensing below F64 was not documented for Fabric Apps (the F64 free-viewer rule is
  written for Power BI items). Microsoft announced Pro/PPU inclusion in 2026-09. Test in the
  tenant with a free-licence account before promising access.
- F-SKU capacity overage is on by default for new capacities and is billed at a premium; set a
  threshold or switch it off when a customer's capacity is budgeted.
- External users: Entra B2B guests. Never expose report data anonymously; customer portals on
  report data → Power BI Embedded (app owns data).

## 4. Release checklist

Known defects of the fresh `dataapp` scaffold (`create-rayfin` 1.36.2, 2026-10), so a red run on
day one is not your change: the template's `validate-visual.spec.mjs` fails before any edit, and
`npm run lint` reports an error in the template's `use-semantic-model-query.ts`. Record both as
template defects in the report (or fix them in a separate commit) instead of silencing the
checks. Node versions outside the `engines` range (20, 22, 24) installed and ran in the test, but
stay inside it.

- [ ] `npm run typecheck && npm test` green (typecheck script added, §2); generated token CSS up to date with the token file.
- [ ] Users get the **portal** URL of the item (or the org app), not the static-hosting URL (§1).
- [ ] Every page leaves the skeletons within its load timeout ([queries-and-data.md](queries-and-data.md) §0).
- [ ] In-portal validation (dev-URI embed) per the in-project validation skill; no console errors.
- [ ] Screenshots at 390 / ≈ 1050 (portal) / 1280 px reviewed, in the portal after deploying; `ibcs-review` findings fixed or recorded as deviations.
- [ ] RLS matrix passed with test accounts; OLS views degrade gracefully.
- [ ] `rayfin up --dry-run` output reviewed; no destructive schema operations (or an approved `--force` run).
- [ ] Org-app audiences updated; semantic-model access granted to the same groups.
- [ ] Release notes: what changed on which page, data/model dependencies, rollback tag.

## 5. Operate

- Monitor: Fabric capacity metrics (CU by item), app usage metrics (preview as of 2026-10), model
  query durations; alert on 429s.
- Rollback: redeploy the previous tag; schema rollbacks need a forward migration (no `--force`
  drop of user data).
- Never deploy, change audiences or grant permissions without being asked; never mint tokens for
  or impersonate real users when debugging; use test accounts.
