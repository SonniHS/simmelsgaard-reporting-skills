# Contributing

Thanks for helping improve simmelsgaard-reporting-skills. This repository is a Claude Code plugin
marketplace: skills, agents, references, scripts and templates for business reporting that follows
the IBCS® Standards. Bug reports, wrong or missing guidance, and pull requests are all welcome.

## Proposing a change

1. **Small fixes** (a typo, a broken link, a wrong number in a reference): open a pull request directly.
2. **A skill gave wrong or insufficient guidance**: open a
   [skill gap issue](https://github.com/SonniHS/simmelsgaard-reporting-skills/issues/new?template=skill_gap.yml)
   with the prompt you used and what happened. That is the most useful feedback for this project.
3. **Bugs in scripts, templates or generated code**: open a
   [bug report](https://github.com/SonniHS/simmelsgaard-reporting-skills/issues/new?template=bug_report.yml).
4. **Larger changes** (a new skill, a new plugin, a change to the notation or the token format): open an
   issue first and describe the problem it solves, so the design can be agreed before you write it.

The flow is a plain GitHub pull request: fork, branch, commit, open a PR against `main`. There is no
CLA and no DCO sign-off. By opening a pull request you agree that your contribution is licensed under
the same terms as the files it changes (see [Licences](#licences)).

## Layout

```
.claude-plugin/marketplace.json            the marketplace: one entry per plugin
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md   plus references/, scripts/, assets/
plugins/<plugin>/agents/<agent>.md
plugins/<plugin>/NOTICE, LICENSE-*         identical copies of the root files
tests/                                     validation and leak scan
```

An installed plugin contains only its own directory. A skill must work in any repository: bundle what
it needs under its own `references/`, `scripts/` or `assets/`, and link only inside its plugin. A skill
from another plugin is named in prose, and that plugin is declared in the plugin's README.

## Running the tests and the validator

Requirements: Python 3 (the tests use the standard library only; CI runs 3.12) and, for validation,
the Claude Code CLI.

```
python3 -m unittest discover -s tests -v     # manifests, frontmatter, links, plugin boundaries, scripts, leak scan
claude plugin validate --strict .            # the marketplace
claude plugin validate --strict plugins/<plugin>
```

When the `claude` CLI is on your `PATH`, the unit tests also run `claude plugin validate --strict` on the
marketplace and every plugin. CI runs both on every push and pull request to `main`.

If you change a script, template or token file, run that skill's own checks as described in its
`SKILL.md` (for example the Deneb preview renderer or the IBCS linter) and say in the PR what you ran.

## Licences

The licence depends on the file type, the same in every plugin. Read [NOTICE](NOTICE) before you
contribute.

- **Prose** (SKILL.md, agents, references, README files): CC BY-SA 4.0 ([LICENSE-CC-BY-SA-4.0](LICENSE-CC-BY-SA-4.0)).
- **Code and data** (scripts, templates, token files, sample data, tests, JSON manifests, and code in
  fenced blocks inside Markdown): MIT ([LICENSE-MIT](LICENSE-MIT)).

Third-party material is accepted only with a compatible licence, and its source and licence go into
NOTICE. Prefer linking to upstream over copying. If you change NOTICE or a LICENSE file, copy it into
every plugin directory as well; a test checks that the copies are identical.

## IBCS research

The prose is our own restatement of the IBCS Standards v2.0 (published under CC BY-SA 4.0), not a copy.

- Cite the page for every rule or value taken from the Standards, e.g. "IBCS v2.0, p. 42".
- Say what kind of fact it is: what the Standards **state** (with a page), what was **measured from a
  figure**, or what is **our own** default where the Standards are silent.
- Never copy figures, page images or longer passages from the Standards document, and never add the
  PDF itself or any licence stamp from a downloaded copy.
- Write "follows the IBCS® Standards". Never claim certification or affiliation with IBCS Institute.

## No private data

Everything in this repository is public. Do not add secrets, tenant, workspace or item ids, host names
of real environments, e-mail addresses, people's names, client or company data, or local file paths.
Use placeholders such as `<workspace-id>` and invented sample data.

The leak scan in `tests/test_repo.py` fails on e-mail addresses, GUIDs (other than the all-zero one),
tenant-specific host names, home directory paths and similar patterns. Maintainers additionally run a
private denylist that is not part of the repository, so a pull request can still be asked to remove a
name the public scan cannot know about.

## Pull request checklist

The pull request template repeats this list:

- `python3 -m unittest discover -s tests -v` passes.
- `claude plugin validate --strict` passes for the marketplace and the plugins you changed.
- Licences respected: new third-party material is attributed in NOTICE, copies are in sync.
- No private data (the leak scan passes).
- A line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for anything a user would notice.

## Security

Do not report vulnerabilities in public issues; see [SECURITY.md](SECURITY.md).
