# Security policy

## Reporting a vulnerability

Please report security problems **privately**, not in a public issue, discussion or pull request.

Use GitHub's private vulnerability reporting: open the repository's
[Security tab](https://github.com/SonniHS/simmelsgaard-reporting-skills/security) and choose
**Report a vulnerability** (the direct link is
<https://github.com/SonniHS/simmelsgaard-reporting-skills/security/advisories/new>). The report stays
visible only to you and the maintainer until an advisory is published.

Include what you can of:

- the plugin, skill and file affected, and the commit or version;
- what an attacker could do, and under which conditions;
- steps or a minimal input to reproduce it;
- a suggested fix, if you have one.

This is a small project; reports are handled on a best-effort basis and acknowledged once read. Fixes are released on `main` and listed in
[CHANGELOG.md](CHANGELOG.md); a GitHub security advisory credits the reporter unless you ask not to be named.

## Scope

In scope:

- **Scripts** shipped in the plugins (`plugins/*/skills/*/scripts/`), e.g. a script that writes outside the
  folder it was given, executes content from its input, or can be made to leak data.
- **Templates and assets** (Deneb/Vega-Lite templates, SVG-in-DAX skeletons, SQL, TMDL, token files)
  that could inject script or markup into a report, an app or a browser.
- **Generated code** and code in the skills' instructions: guidance that leads an agent to produce
  insecure code or configuration, such as a stored identity reading data that should be read as the
  signed-in user, row-level security being bypassed, secrets placed in source files, or workflows with
  more permissions than they need.
- The marketplace and plugin manifests, and this repository's CI workflow.

Out of scope: vulnerabilities in Claude Code, Power BI, Microsoft Fabric, Deneb, Vega-Lite, Node.js or
other upstream products. Report those to their vendors. If a skill here makes such a problem worse, that
part is in scope.

## No secrets in issues

Never paste secrets, tokens, connection strings, tenant, workspace or item ids, host names of your
environments, or real business data into an issue, discussion or pull request, including in
screenshots and logs. Replace them with placeholders such as `<workspace-id>`. If you posted one by
mistake, revoke or rotate it first, then edit or delete the post.
