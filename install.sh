#!/usr/bin/env bash
# HypoKiln one-line installer.
#
# Usage (from inside a cloned repo):
#   ./install.sh
#
# Or one-shot from the web:
#   curl -fsSL https://raw.githubusercontent.com/agiwhitelist/hypokiln/main/install.sh | bash
#
# When invoked outside a clone, the script auto-clones into ./hypokiln/ and
# re-execs itself from inside the clone before doing the rest of setup.
#
# What it does (idempotent):
#   0. clones the repo if invoked via curl|bash outside a checkout
#   1. checks Python 3.12+, Node 20+, and a logged-in coding CLI
#   2. creates .venv and installs Python deps including [control]
#   3. installs Node deps for web/
#   4. copies .env.example → .env if missing
#   5. seeds four demo runs so the dashboard has something to render
#   6. tells you what to run next
#
# Exits 0 on full success, 1 on any prerequisite or step failure.

set -euo pipefail

HYPOKILN_REPO_URL="${HYPOKILN_REPO_URL:-https://github.com/agiwhitelist/hypokiln.git}"
HYPOKILN_BRANCH="${HYPOKILN_BRANCH:-main}"
HYPOKILN_CLONE_DIR="${HYPOKILN_CLONE_DIR:-hypokiln}"

# ── 0. self-bootstrap from curl | bash ─────────
# If we were piped from curl (no local repo at $PWD), clone first.
if [ ! -f "pyproject.toml" ] || [ ! -d ".github" ] || ! grep -q '"hypokiln"' pyproject.toml 2>/dev/null; then
  if ! command -v git >/dev/null 2>&1; then
    printf '\033[31m✗\033[0m git is required to bootstrap HypoKiln.\n' >&2
    exit 1
  fi
  if [ -d "$HYPOKILN_CLONE_DIR/.git" ]; then
    printf '\033[90m  reusing existing clone at ./%s\033[0m\n' "$HYPOKILN_CLONE_DIR"
  else
    printf '\033[1mCloning %s → ./%s\033[0m\n' "$HYPOKILN_REPO_URL" "$HYPOKILN_CLONE_DIR"
    git clone --depth=1 --branch "$HYPOKILN_BRANCH" "$HYPOKILN_REPO_URL" "$HYPOKILN_CLONE_DIR"
  fi
  cd "$HYPOKILN_CLONE_DIR"
  exec bash ./install.sh "$@"
fi

# ── colors ─────────────────────────────────────
BOLD=$(printf '\033[1m'); RESET=$(printf '\033[0m')
RED=$(printf '\033[31m'); GREEN=$(printf '\033[32m'); AMBER=$(printf '\033[33m'); ASH=$(printf '\033[90m')
say()   { printf "%s%s%s\n" "$ASH" "  $*" "$RESET"; }
ok()    { printf "%s✓%s %s\n" "$GREEN" "$RESET" "$*"; }
warn()  { printf "%s!%s %s\n" "$AMBER" "$RESET" "$*"; }
fail()  { printf "%s✗%s %s\n" "$RED" "$RESET" "$*"; exit 1; }
title() { printf "\n%s%s%s\n" "$BOLD" "$*" "$RESET"; }

# ── 0. resolve repo root ───────────────────────
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# ── 1. preflight ───────────────────────────────
title "1/6  Checking prerequisites"

PYTHON_BIN=""
for cand in python3.12 python3.13 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    ver=$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
    major=${ver%%.*}; minor=${ver##*.}
    if [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; then
      PYTHON_BIN="$cand"
      ok "python: $cand ($ver)"
      break
    fi
  fi
done
[ -n "$PYTHON_BIN" ] || fail "Python 3.12+ not found. Install from https://www.python.org/downloads/"

if ! command -v node >/dev/null 2>&1; then
  fail "node not found. Install Node 20+ from https://nodejs.org/"
fi
node_ver=$(node --version | sed 's/^v//')
node_major=${node_ver%%.*}
[ "$node_major" -ge 20 ] || fail "Node $node_ver is too old; need Node 20+."
ok "node: v$node_ver"

if ! command -v npm >/dev/null 2>&1; then
  fail "npm not found (ships with Node)."
fi

# Optional: detect at least one logged-in coding CLI (warn only).
cli_found=""
for bin in codex claude gemini; do
  if command -v "$bin" >/dev/null 2>&1; then
    cli_found="$cli_found $bin"
  fi
done
if [ -z "$cli_found" ]; then
  warn "No coding CLI found on PATH (codex / claude / gemini). HypoKiln will still install,"
  warn "but \`kiln build\` needs one of them. See README for login instructions."
else
  ok "coding CLI:$cli_found"
fi

# ── 2. python venv + deps ──────────────────────
title "2/6  Setting up Python virtualenv"
if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
  ok "created .venv/"
else
  ok ".venv/ already exists"
fi

# shellcheck disable=SC1091
. .venv/bin/activate
say "upgrading pip"
pip install --quiet --upgrade pip
say "installing hypokiln + control plane deps"
pip install --quiet -e ".[dev,control]"
ok "python deps installed"

# ── 3. node deps for web/ ──────────────────────
title "3/6  Installing web dashboard deps"
( cd web && npm install --no-audit --no-fund --loglevel=error )
ok "web/ deps installed"

# ── 4. .env ────────────────────────────────────
title "4/6  Bootstrapping .env"
if [ ! -f .env ]; then
  cp .env.example .env
  ok ".env created from template"
else
  ok ".env already exists (not overwritten)"
fi

# ── 5. seed demo runs ──────────────────────────
title "5/6  Seeding demo ideas"
HYPOKILN_SKIP_SKILLS=1 python scripts/seed_demo.py
ok "demo ideas seeded under .hypokiln/state/"

# ── 6. final message ──────────────────────────
title "6/6  Done."
cat <<'EOF'

  Next steps:

    make dev                          start FastAPI + Next.js in parallel
                                        FastAPI on   http://localhost:8765
                                        dashboard on http://localhost:3000

    kiln build "<your idea here>"     spawn a new pipeline from the CLI
    kiln capability-scan              browse fresh AI wedges
    kiln status                       list every idea + stage progress

  Activate the venv in new shells with:  source .venv/bin/activate

EOF
