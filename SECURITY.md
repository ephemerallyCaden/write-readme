# Security Policy

## Reporting a vulnerability

Report it privately from the repository's Security tab: Security → Report a vulnerability, which opens [this form](https://github.com/ephemerallyCaden/write-readme/security/advisories/new). Please don't open a public issue for it.

## Scope

Everything write-readme runs on your machine:

- the Python checkers and generators in `scripts/`
- `scripts/detect-project-type.sh`
- the Playwright and VHS capture scripts (`capture-web-app.py`, `capture-terminal.py`, `generate-tape.py`)
- the instructions in `SKILL.md`, `references/`, and `skills/` that make the agent run commands

## Response time

write-readme has one maintainer, so there is no guaranteed response time.
