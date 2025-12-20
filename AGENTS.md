# Agent Guidelines (Codex / LLMs)

This repository already defines contribution and quality expectations. Before changing anything, read:
- `CONTRIBUTING.md` (branching + atomic commit discipline)
- `DEVELOPMENT.md` (local workflow)
- `.github/workflows/python-quality.yml` (CI checks)
- `pyproject.toml`, `.pre-commit-config.yaml`, `.flake8` (format/lint/type rules)

## Defaults
- Prefer Python for tooling/automation/glue unless there is a clear technical reason not to.
- Protect public contracts: CLI flags, env vars, config schema, file formats, and documented behavior.
- Keep diffs small and reviewer-friendly; avoid churn and “pretty refactors”.
- Do not execute the application or run tests unless explicitly requested; prefer static reasoning and file-level analysis first.

## Change Discipline
- One topic per branch.
- One logical change per commit; keep commits revert-safe.
- If the same file needs multiple unrelated edits, split them into separate commits.

Commit message format in this repo is `<scope>: <precise technical justification>`.
To apply strict “type + scope” discipline without breaking the convention, embed the type in the scope:
`fix(config): …`, `refactor(driver): …`, `policy(docs): …`.

Suggested types: `fix`, `safety`, `validation`, `refactor`, `structure`, `tooling`, `policy`, `docs`, `visuals`, `chore`.
