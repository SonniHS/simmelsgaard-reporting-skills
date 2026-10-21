## What and why

<!-- What does this change, and which problem or issue does it address? -->

## Checklist

- [ ] `python3 -m unittest discover -s tests -v` passes
- [ ] `claude plugin validate --strict .` and `claude plugin validate --strict plugins/<plugin>` pass for the plugins I changed
- [ ] Licences: prose stays CC BY-SA 4.0, code and data MIT; any third-party material is attributed in NOTICE, and NOTICE / LICENSE copies in every plugin are identical
- [ ] IBCS content cites pages and copies no figures or passages from the Standards
- [ ] No private data: no secrets, ids, hosts, e-mail addresses, names or local paths (the leak scan passes)
- [ ] CHANGELOG.md has an entry under `## [Unreleased]` (or this change is invisible to users)
