# Security policy

## Scope

HypoKiln spawns a logged-in coding CLI (codex / claude / gemini) as a subprocess per stage. Authentication is whatever the CLI established locally — HypoKiln does **not** read your session token, does **not** make outbound network calls on your behalf, and does **not** persist any auth material.

The kiln's threat model in scope:

- **Prompt injection via factory templates or skill packs.** A malicious change to `factory/` or `skills/` could redirect what the coding CLI does. Treat both as code; gate PRs behind review.
- **Path traversal in artifact reads.** The web dashboard's `/api/runs/<slug>/artifacts/<path>` rejects paths that escape `products/<slug>/`.
- **Subprocess argv injection.** The CLI runner uses `subprocess.Popen` with `shell=False` and an explicit argv list. Do not refactor it to use `shell=True`.
- **Skill-pack supply chain.** External packs are pulled by URL from `SKILL_REGISTRY`. Pin commit SHAs in `VENDORED_SKILLS` for reproducible builds; the loader falls back to `git clone --depth 1` only when the vendored snapshot is missing.

## Reporting a vulnerability

Email the maintainer privately (see the repo's README contact section) with:

- A short description of the issue
- Steps to reproduce, ideally with a minimal `kiln build` invocation
- The affected commit SHA / version

Please do **not** open a public issue for security-sensitive reports. We'll acknowledge within 72 hours.

## Disclosure timeline

- 72 hours: acknowledged
- 14 days: fix in main + new tagged release
- 30 days: public disclosure (security advisory)

For critical issues (RCE-class, credential exposure) the timeline collapses to days, not weeks.

## What HypoKiln doesn't protect against

- A compromised coding CLI binary (codex / claude / gemini). If the binary itself is malicious, HypoKiln has no defense — it spawns whatever you point it at.
- Bugs in your skill pack contents. Skill packs are inert text but they steer the coding CLI's behavior; a careless rule can produce dangerous code.
- Operator misconfiguration (`HYPOKILN_AUTONOMOUS=1` with an unaudited prompt).
