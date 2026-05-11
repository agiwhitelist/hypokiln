<!--
Thanks for the PR. Quick checklist below — don't delete it, tick what applies.
-->

## What

<!-- One paragraph. What does this change and why? -->

## Why this lives upstream of G1

<!-- HypoKiln stops at the idea decision. If your change adds scope past G1, justify it. Otherwise delete this section. -->

## Checklist

- [ ] `make test` passes locally
- [ ] `make lint` passes locally
- [ ] If web/ touched: `cd web && npm run typecheck && npm run build` passes
- [ ] New env vars are documented in `.env.example` AND `README.md`
- [ ] If a new stage / gate / skill pack: added a unit test in `tests/`
- [ ] If a user-visible change: updated `CHANGELOG.md` under `## [Unreleased]`

## Screenshots / output

<!-- Drop terminal output, screenshots, or artifact paths. -->

## Closes

<!-- Closes #123 / Refs #456 -->
