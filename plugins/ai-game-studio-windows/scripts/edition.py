#!/usr/bin/env python3
"""Run this plugin's edition commands through the matching installed core."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ALLOWED_COMMANDS = {"doctor", "plan", "apply", "disable", "rollback"}
EXPECTED_EDITION_ID = "windows"
EXPECTED_PLUGIN_NAME = "ai-game-studio-windows"
MAX_DESCRIPTOR_BYTES = 1024 * 1024


def load_edition(plugin_root: Path) -> tuple[str, str, Path]:
    root = plugin_root.resolve()
    editions_root = (root / "editions").resolve(strict=True)
    descriptors = sorted(path for path in editions_root.glob("*.json") if path.is_file())
    if len(descriptors) != 1:
        raise RuntimeError("The edition plugin must contain exactly one descriptor")
    descriptor = descriptors[0].resolve(strict=True)
    if descriptor.parent != editions_root or descriptor.name != f"{EXPECTED_EDITION_ID}.json":
        raise RuntimeError("The edition descriptor escapes its plugin or has an unexpected name")
    if descriptor.stat().st_size > MAX_DESCRIPTOR_BYTES:
        raise RuntimeError("The edition descriptor is too large")
    payload = json.loads(descriptor.read_text(encoding="utf-8"))
    edition_id = payload.get("id")
    version = payload.get("version")
    if (
        edition_id != EXPECTED_EDITION_ID
        or payload.get("plugin") != EXPECTED_PLUGIN_NAME
        or not isinstance(version, str)
    ):
        raise RuntimeError("The edition descriptor does not match this platform plugin")
    manifest_path = (root / ".codex-plugin" / "plugin.json").resolve(strict=True)
    try:
        manifest_path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("The edition plugin manifest escapes its plugin") from exc
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("name") != EXPECTED_PLUGIN_NAME
        or manifest.get("version") != version
        or manifest.get("license") != "MIT"
    ):
        raise RuntimeError("The edition plugin manifest does not match its descriptor")
    return edition_id, version, descriptor


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


def forwarded_arguments(
    edition_id: str,
    descriptor_path: Path,
    arguments: Sequence[str],
) -> list[str]:
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
        if any(
            argument == "--descriptor" or argument.startswith("--descriptor=")
            for argument in rest
        ):
            raise RuntimeError("The edition descriptor is fixed by the installed platform plugin")
        return [
            "edition",
            command,
            edition_id,
            *rest,
            "--descriptor",
            str(descriptor_path),
        ]
    return ["edition", command, *rest]


def main(argv: Sequence[str] | None = None) -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    edition_id, version, descriptor_path = load_edition(plugin_root)
    core_cli = find_core_cli(plugin_root, version)
    command = [
        sys.executable,
        str(core_cli),
        *forwarded_arguments(edition_id, descriptor_path, argv or sys.argv[1:]),
    ]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
