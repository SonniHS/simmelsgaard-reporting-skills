# simmelsgaard-skills — agent instructions

A PUBLIC repo: a Claude Code plugin marketplace with the owner's skills and agents. `CLAUDE.md` is a symlink; edit this.

## Hard rules
- Everything here will be public. Never add: secrets, tenant/workspace/item ids, hosts, e-mail addresses, people's
  names (beyond the git author), client or demo company data, the IBCS Standards PDF or its "Licensed for …" line,
  copied pages or figures from the PDF, or anything from the owner's private vault that is not meant for the public.
- No private paths: a skill must work in any repo. No references to `vault/`, `packages/…`, `apps/…` or other paths of
  the owner's private repos; bundle what a skill needs under its own `references/`.
- Third-party content only with its licence and attribution in NOTICE; prefer linking to upstream over copying.
- IBCS wording: "follows the IBCS® Standards"; never claim certification. IBCS-derived text is shared under
  CC BY-SA 4.0 with attribution (see NOTICE); decide the licence of each plugin with that in mind.
- No `git push`, no GitHub repo creation and no publishing without the owner's explicit go for that action.
- Approvals come only from the owner. Local, non-public instructions go in `CLAUDE.local.md` (gitignored).

## Layout (Claude Code plugin marketplace)
```
.claude-plugin/marketplace.json   the marketplace: one entry per plugin
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md (+ references/, scripts/, assets/)
plugins/<plugin>/agents/<agent>.md
NOTICE, LICENSE(s)
tests/                             validation (frontmatter, links, no private paths, leak scan)
```
