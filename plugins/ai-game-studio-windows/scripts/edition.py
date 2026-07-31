#!/usr/bin/env python3
"""Run this plugin's edition commands through the matching installed core."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ALLOWED_COMMANDS = {"doctor", "plan", "apply", "disable", "rollback"}


def load_edition(plugin_root: Path) -> tuple[str, str]:
    descriptors = sorted((plugin_root / "editions").glob("*.json"))
    if len(descriptors) != 1:
        raise RuntimeError("The edition plugin must contain exactly one descriptor")
    payload = json.loads(descriptors[0].read_text(encoding="utf-8"))
    edition_id = payload.get("id")
    version = payload.get("version")
    if not isinstance(edition_id, str) or not isinstance(version, str):
        raise RuntimeError("The edition descriptor must contain string id and version fields")
    return edition_id, version


def is_matching_core(candidate: Path, required_version: str) -> bool:
    manifest = candidate.parents[1] / ".codex-plugin" / "plugin.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        payload.get("name") == "ai-game-studio"
        and payload.get("version") == required_version
        and candidate.is_file()
    )


def find_core_cli(plugin_root: Path, required_version: str) -> Path:
    candidates: set[Path] = set()
    for ancestor in (plugin_root.parent, plugin_root.parent.parent):
        candidates.add(ancestor / "ai-game-studio" / "scripts" / "ai_game_studio.py")
        core_cache = ancestor / "ai-game-studio"
        if core_cache.is_dir():
            candidates.update(core_cache.glob("*/scripts/ai_game_studio.py"))
    matches = [
        candidate.resolve()
        for candidate in sorted(candidates)
        if is_matching_core(candidate, required_version)
    ]
    if not matches:
        raise RuntimeError(
            "Codex AI Game Studio core "
            f"{required_version} was not found beside this plugin or in its marketplace cache. "
            "Install ai-game-studio@frabcd-ai-game-studio first."
        )
    return matches[-1]


def forwarded_arguments(edition_id: str, arguments: Sequence[str]) -> list[str]:
    if not arguments or arguments[0] in {"-h", "--help"}:
        return ["edition", "--help"]
    if arguments[0] == "--version":
        return ["--version"]
    command = arguments[0]
    if command not in ALLOWED_COMMANDS:
        raise RuntimeError(
            f"Unknown edition command {command!r}; choose doctor, plan, apply, disable, or rollback"
        )
    rest = list(arguments[1:])
    if command in {"doctor", "plan", "disable"}:
        return ["edition", command, edition_id, *rest]
    return ["edition", command, *rest]


def main(argv: Sequence[str] | None = None) -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    edition_id, version = load_edition(plugin_root)
    core_cli = find_core_cli(plugin_root, version)
    command = [sys.executable, str(core_cli), *forwarded_arguments(edition_id, argv or sys.argv[1:])]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
