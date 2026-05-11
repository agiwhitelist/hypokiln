"""External skill packs as composable system-prompt extensions.

HypoKiln runs each stage as a single CLI prompt (see `runners/cli_runner.py`).
The base prompt is the agent's own `instructions.md`. This module attaches
*external* skill packs to that prompt by:

  1. Reading each pack's markdown content from disk.
  2. Appending it under an `[ATTACHED SKILL PACKS]` section.

Skills are inert text — codex / claude / gemini already follow prose, so no
framework API is needed.

Configuration:
  HYPOKILN_SKILLS_DIR     override the on-disk cache location
  HYPOKILN_SKIP_SKILLS=1  short-circuit; do not fetch or attach skills
                          (used by tests and air-gapped runs).
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from . import REPO_ROOT

log = logging.getLogger(__name__)


# ──────────────── registry ────────────────


# Upstream URLs for external packs. Resolution order in `ensure_skill`:
#   1. LOCAL_SKILLS    — first-party packs authored inside this repo.
#   2. VENDORED_SKILLS — pinned snapshots committed under `vendor/skills/`.
#   3. SKILL_REGISTRY  — fallback to fresh `git clone --depth 1`. Only used
#                        if a pack is registered externally but not yet
#                        vendored.
SKILL_REGISTRY: dict[str, str] = {
    "obra/superpowers": "https://github.com/obra/superpowers",
    "ncklrs/startup-os-skills": "https://github.com/ncklrs/startup-os-skills",
}


VENDORED_SKILLS: dict[str, str] = {
    "obra/superpowers":         "vendor/skills/obra__superpowers",
    "ncklrs/startup-os-skills": "vendor/skills/ncklrs__startup-os-skills",
}


# First-party skill packs maintained inside this repo at `skills/hypokiln-skills/`.
# Paths are relative to REPO_ROOT.
LOCAL_SKILLS: dict[str, str] = {
    # The four packs that govern the idea-kiln pipeline.
    #
    # capability-radar          → Stage 1 + Stage 4: defines what counts as a
    #                              fresh AI capability wedge.
    # anti-patterns             → Stage 3 + Stage 4 + Stage 6: seven mortality
    #                              patterns (trust, clone, incumbency, …) that
    #                              kill execution-strong hypotheses.
    # architecture-and-virality → Stage 6: form_factor / archetype / wow_moment
    #                              / viral_mechanic contract.
    # domain-patterns           → Stage 3 + Stage 6: archetype-specific
    #                              pricing, audience, retention norms.
    "hypokiln/capability-radar":          "skills/hypokiln-skills/capability-radar",
    "hypokiln/anti-patterns":             "skills/hypokiln-skills/anti-patterns",
    "hypokiln/architecture-and-virality": "skills/hypokiln-skills/architecture-and-virality",
    "hypokiln/domain-patterns":           "skills/hypokiln-skills/domain-patterns",
}


# Per-delegate skill attachments. Keyed on agent display name (same string
# `pipeline.STAGES[].delegate` uses).
DELEGATE_SKILLS: dict[str, tuple[str, ...]] = {
    "Trend Scout Agent": (
        "obra/superpowers:skills/brainstorming",
        "obra/superpowers:skills/verification-before-completion",
        "hypokiln/capability-radar",
    ),
    "Product Strategist Agent": (
        # Stages 3 (Hypothesis Generator) + 6 (Selection Score)
        "ncklrs/startup-os-skills:skills/product-discovery",
        "ncklrs/startup-os-skills:skills/product-specs-writer",
        "ncklrs/startup-os-skills:skills/pricing-strategist",
        "ncklrs/startup-os-skills:skills/competitive-strategist",
        "hypokiln/capability-radar",
        "hypokiln/architecture-and-virality",
        "hypokiln/domain-patterns",
        "hypokiln/anti-patterns",
    ),
    "Market Skeptic Agent": (
        "obra/superpowers:skills/brainstorming",
        "obra/superpowers:skills/verification-before-completion",
        "ncklrs/startup-os-skills:skills/competitive-strategist",
        "hypokiln/capability-radar",
        "hypokiln/architecture-and-virality",
        "hypokiln/anti-patterns",
    ),
    "Founder Agent": (
        # G1 pre-flight reads anti-patterns to score the 10-question
        # checklist. Brainstorming + verification keep the agent honest.
        "obra/superpowers:skills/brainstorming",
        "obra/superpowers:skills/verification-before-completion",
        "hypokiln/anti-patterns",
        "hypokiln/architecture-and-virality",
    ),
}


# ──────────────── paths + spec parsing ────────────────


def skills_dir() -> Path:
    return REPO_ROOT / os.environ.get("HYPOKILN_SKILLS_DIR", ".hypokiln/skills")


def _local_path(name: str) -> Path:
    return skills_dir() / name.replace("/", "__")


def _resolve_spec(spec: str) -> tuple[str, str | None]:
    """Parse a DELEGATE_SKILLS entry into ``(pack_name, sub_path_or_none)``.

    Syntax: ``"<owner>/<pack>"`` for the whole pack, or
    ``"<owner>/<pack>:<relative/sub/path>"`` to scope content collection
    to a subdirectory.
    """
    if ":" in spec:
        name, sub = spec.split(":", 1)
        sub = sub.strip().strip("/")
        return name, sub or None
    return spec, None


# ──────────────── clone / cache ────────────────


def _git_clone(url: str, target: Path, *, timeout: int = 180) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target)],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"git not on PATH; required to clone skill pack {url!r}: {exc}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"git clone failed for {url}: {exc.stderr.strip() or exc.stdout.strip()}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git clone timed out for {url}: {exc}") from exc


def ensure_skill(name_or_spec: str) -> Path:
    """Return the on-disk path for `name_or_spec`.

    Resolution order:
      1. `LOCAL_SKILLS`    — first-party packs (no network).
      2. `VENDORED_SKILLS` — pinned snapshots in `vendor/skills/`.
      3. `SKILL_REGISTRY`  — `git clone --depth 1` into `.hypokiln/skills/`.
    """
    name, _sub = _resolve_spec(name_or_spec)
    if name in LOCAL_SKILLS:
        target = REPO_ROOT / LOCAL_SKILLS[name]
        if not target.is_dir():
            raise FileNotFoundError(
                f"Local skill {name!r} expected at {target}; missing on disk."
            )
        return target
    if name in VENDORED_SKILLS:
        target = REPO_ROOT / VENDORED_SKILLS[name]
        if not target.is_dir():
            raise FileNotFoundError(
                f"Vendored skill {name!r} expected at {target}; missing on disk. "
                f"Re-run the vendor script or fall back to "
                f"`git clone {SKILL_REGISTRY.get(name, '<unknown>')}`."
            )
        return target
    if name not in SKILL_REGISTRY:
        raise KeyError(
            f"Unknown skill pack {name!r}; not in LOCAL_SKILLS, "
            "VENDORED_SKILLS, or SKILL_REGISTRY."
        )
    target = _local_path(name)
    if (target / ".git").is_dir():
        return target
    _git_clone(SKILL_REGISTRY[name], target)
    return target


def ensure_all_for_pipeline() -> dict[str, Path]:
    """Pre-flight: ensure every pack referenced by DELEGATE_SKILLS is local."""
    if os.environ.get("HYPOKILN_SKIP_SKILLS") == "1":
        return {}
    out: dict[str, Path] = {}
    failures: list[tuple[str, str, str]] = []
    for skills in DELEGATE_SKILLS.values():
        for s in skills:
            if s in out:
                continue
            try:
                out[s] = ensure_skill(s)
            except Exception as exc:  # noqa: BLE001
                failures.append((s, SKILL_REGISTRY.get(s, "<unknown>"), str(exc)))
    if failures:
        lines = "\n".join(
            f"  - {name}  ({url})\n      {err}" for name, url, err in failures
        )
        raise RuntimeError(
            "Could not ensure all required skill packs:\n"
            f"{lines}\n"
            "Fix the underlying git access (network, auth, repo URL) or set "
            "HYPOKILN_SKIP_SKILLS=1 to bypass."
        )
    return out


# ──────────────── prompt composition ────────────────


_PRIMARY_GLOBS: tuple[str, ...] = ("SKILL.md", "skill.md")

_REFERENCE_GLOBS: tuple[str, ...] = (
    "reference/*.md",
    "references/*.md",
    "rules/*.md",
    "RULES.md",
    "PATTERNS.md",
    "*-PATTERNS.md",
    "CHECKLIST.md",
    "*-CHECKLIST.md",
)

_FALLBACK_GLOBS: tuple[str, ...] = ("README.md", "AGENTS.md", "CLAUDE.md")

_ALLOWED_DOTDIRS: frozenset[str] = frozenset({".agents"})


def _is_dotdir_duplicate(rel_path: Path) -> bool:
    parts = rel_path.parts
    if not parts:
        return False
    head = parts[0]
    return head.startswith(".") and head not in _ALLOWED_DOTDIRS


def _iter_skill_files(root: Path) -> list[Path]:
    """Pick the files most likely to carry actual skill instructions."""
    seen: set[Path] = set()
    deduped: list[Path] = []

    def _add(paths):
        for p in paths:
            if p in seen or not p.is_file():
                continue
            try:
                rel = p.relative_to(root)
            except ValueError:
                rel = Path(p.name)
            if _is_dotdir_duplicate(rel):
                continue
            seen.add(p)
            deduped.append(p)

    for pat in _PRIMARY_GLOBS:
        _add(sorted(root.rglob(pat)))
    for pat in _REFERENCE_GLOBS:
        _add(sorted(root.rglob(pat)))
    for pat in _FALLBACK_GLOBS:
        _add(sorted(root.rglob(pat)))
    return deduped


_DEFAULT_PACK_BUDGET = 131072


def _pack_budget() -> int:
    raw = (os.environ.get("HYPOKILN_SKILL_BUDGET") or "").strip()
    if not raw:
        return _DEFAULT_PACK_BUDGET
    try:
        return max(1024, int(raw))
    except ValueError:
        return _DEFAULT_PACK_BUDGET


def _collect_skill_text(
    skill_root: Path,
    *,
    sub_path: str | None = None,
    max_chars: int | None = None,
) -> str:
    """Inline up to ``max_chars`` of markdown content from the pack."""
    if max_chars is None:
        max_chars = _pack_budget()

    if sub_path:
        scoped = (skill_root / sub_path).resolve()
        try:
            scoped.relative_to(skill_root.resolve())
        except ValueError:
            return f"(invalid sub-path {sub_path!r}: escapes pack root)"
        if not scoped.is_dir():
            return (
                f"(sub-path {sub_path!r} not found in pack at "
                f"{skill_root.name}; check DELEGATE_SKILLS spelling)"
            )
        iter_root = scoped
    else:
        iter_root = skill_root

    chunks: list[str] = []
    total = 0
    for p in _iter_skill_files(iter_root):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if not text:
            continue
        try:
            rel = p.relative_to(skill_root)
        except ValueError:
            rel = Path(p.name)
        header = f"\n\n--- {rel.as_posix()} ---\n"
        budget = max_chars - total - len(header)
        if budget <= 0:
            break
        body = text if len(text) <= budget else text[:budget] + "\n…[truncated]"
        chunks.append(header + body)
        total += len(header) + len(body)
        if total >= max_chars:
            break
    return "".join(chunks).strip()


def instructions_for(stage_delegate: str, *, base_instructions: str) -> str:
    """Compose `base_instructions` + every attached skill pack's content.

    Soft-fails: if a skill cannot be read, it is recorded inline as
    `(unavailable: …)` and the rest of the prompt still ships.
    """
    if os.environ.get("HYPOKILN_SKIP_SKILLS") == "1":
        return base_instructions

    skills = DELEGATE_SKILLS.get(stage_delegate, ())
    if not skills:
        return base_instructions

    pieces: list[str] = [base_instructions, "\n\n[ATTACHED SKILL PACKS]"]
    for s in skills:
        pieces.append(f"\n\n## Skill: {s}")
        try:
            root = ensure_skill(s)
            _name, sub = _resolve_spec(s)
            text = _collect_skill_text(root, sub_path=sub)
            pieces.append("\n" + (text or "(empty skill pack)"))
        except Exception as exc:  # noqa: BLE001
            log.warning("skill %s unavailable: %s", s, exc)
            pieces.append(f"\n(unavailable: {exc})")
    return "".join(pieces)


# ──────────────── ops helpers (CLI subcommands) ────────────────


def list_skills() -> list[tuple[str, str, bool]]:
    """Return every registered pack with its source URL/path and on-disk state."""
    out: list[tuple[str, str, bool]] = []
    for name, rel in LOCAL_SKILLS.items():
        out.append((name, f"local:{rel}", (REPO_ROOT / rel).is_dir()))
    for name, url in SKILL_REGISTRY.items():
        vendored_rel = VENDORED_SKILLS.get(name)
        if vendored_rel and (REPO_ROOT / vendored_rel).is_dir():
            out.append((name, f"vendored:{vendored_rel}", True))
            continue
        cached = (skills_dir() / name.replace("/", "__") / ".git").is_dir()
        out.append((name, url, cached))
    return out


def update_skills(names: list[str] | None = None) -> dict[str, str]:
    target_names = names or list(SKILL_REGISTRY.keys())
    results: dict[str, str] = {}
    for name in target_names:
        if name not in SKILL_REGISTRY:
            results[name] = "unknown skill"
            continue
        local = _local_path(name)
        if not (local / ".git").is_dir():
            try:
                ensure_skill(name)
                results[name] = "cloned"
            except Exception as exc:  # noqa: BLE001
                results[name] = f"failed: {exc}"
            continue
        try:
            subprocess.run(
                ["git", "-C", str(local), "pull", "--ff-only"],
                check=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
            results[name] = "updated"
        except subprocess.CalledProcessError as exc:
            results[name] = f"failed: {(exc.stderr or exc.stdout).strip()}"
        except Exception as exc:  # noqa: BLE001
            results[name] = f"failed: {exc}"
    return results


def clean_skills() -> int:
    base = skills_dir()
    if not base.exists():
        return 0
    removed = 0
    for entry in base.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    return removed


__all__ = [
    "DELEGATE_SKILLS",
    "LOCAL_SKILLS",
    "SKILL_REGISTRY",
    "VENDORED_SKILLS",
    "clean_skills",
    "ensure_all_for_pipeline",
    "ensure_skill",
    "instructions_for",
    "list_skills",
    "skills_dir",
    "update_skills",
]
