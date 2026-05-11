# Contributing to HypoKiln

## Quick start

```bash
git clone <repo>
cd hypokiln
make install        # python venv + npm install
make test           # 26 unit tests, should pass
make dev            # FastAPI :8765 + Next.js :3000
```

## What kind of changes are in scope

HypoKiln's scope is **the idea kiln** — six stages from frontier-AI signals to a ranked top-3, with one human gate. PRs that improve quality within that scope are welcome:

- New deterministic gates / audits (e.g. tighter T-rules, H-rules, M-rules)
- New skill packs under `skills/hypokiln-skills/`
- Better Market Skeptic kill rules (named, with concrete detection logic)
- New capability sources for the radar
- UI polish on the web dashboard
- Test coverage on the orchestrator + audits

## Style

- **Python** — ruff, line length 100, target 3.12. No type-stubs for now.
- **TypeScript** — `npm run typecheck && npm run lint`. The Next.js dashboard is intentionally small; do not add component libraries.
- **Markdown** — fenced code blocks with language tags; tables for matrices.
- **Tests** — every new audit rule, kill filter, or pipeline branch needs a unit test under `tests/unit/`. Use the `isolated_repo` fixture in `conftest.py`.

## Skill packs

If you want to add a new skill pack, see [SKILLS.md](./SKILLS.md). One `SKILL.md` per pack, ≤500 words. Hard rules are numbered and imperative so a coding CLI can grep them.

## Commit messages

```
type(scope): short imperative summary

Longer body if the why isn't obvious from the diff. Wrap at 72 chars.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

## Reporting bugs

Open an issue with:

- The exact `kiln <subcommand>` invocation
- Whether you're on the API runtime or CLI runtime, with which `--cli-bin`
- The contents of `.hypokiln/state/<slug>/logs/stage-NN.log` for the failing stage (with secrets redacted)
- A description of what you expected vs what happened

## Security

If you find something security-sensitive (credential exposure, RCE-class bug, prompt-injection on the live pipeline), do not open a public issue. See [SECURITY.md](./SECURITY.md).
