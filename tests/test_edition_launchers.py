from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_launcher(edition: str):
    path = (
        ROOT
        / "plugins"
        / f"ai-game-studio-{edition}"
        / "scripts"
        / "edition.py"
    )
    spec = importlib.util.spec_from_file_location(f"ags_{edition}_launcher", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_fake_core(plugin_root: Path, version: str = "1.1.0") -> Path:
    cli = plugin_root / "scripts" / "ai_game_studio.py"
    cli.parent.mkdir(parents=True)
    cli.write_text("print('fake core')\n", encoding="utf-8")
    manifest = plugin_root / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "ai-game-studio", "version": version}),
        encoding="utf-8",
    )
    return cli.resolve()


class EditionLauncherTests(unittest.TestCase):
    def test_arguments_are_namespaced_without_command_strings(self) -> None:
        for edition in ("windows", "macos"):
            launcher = load_launcher(edition)
            self.assertEqual(
                launcher.forwarded_arguments(edition, ["doctor", "--project", "game"]),
                ["edition", "doctor", edition, "--project", "game"],
            )
            self.assertEqual(
                launcher.forwarded_arguments(
                    edition,
                    ["apply", "--project", "game", "--plan", "plan.json"],
                ),
                ["edition", "apply", "--project", "game", "--plan", "plan.json"],
            )
            with self.assertRaises(RuntimeError):
                launcher.forwarded_arguments(edition, ["install-everything"])

    def test_core_is_found_in_repository_and_marketplace_cache_layouts(self) -> None:
        launcher = load_launcher("windows")
        with tempfile.TemporaryDirectory(prefix="ags-launcher-") as temporary:
            root = Path(temporary)
            repository_plugins = root / "repo" / "plugins"
            repository_platform = repository_plugins / "ai-game-studio-windows"
            repository_platform.mkdir(parents=True)
            direct_core = make_fake_core(repository_plugins / "ai-game-studio")
            self.assertEqual(
                launcher.find_core_cli(repository_platform, "1.1.0"), direct_core
            )

            marketplace = root / "cache" / "frabcd-ai-game-studio"
            cached_platform = (
                marketplace / "ai-game-studio-windows" / "source-snapshot"
            )
            cached_platform.mkdir(parents=True)
            cached_core = make_fake_core(
                marketplace / "ai-game-studio" / "source-snapshot"
            )
            self.assertEqual(
                launcher.find_core_cli(cached_platform, "1.1.0"), cached_core
            )
            with self.assertRaises(RuntimeError):
                launcher.find_core_cli(cached_platform, "9.9.9")

    def test_native_launcher_reaches_checked_in_core(self) -> None:
        system = platform.system()
        if system == "Windows":
            command = [
                "powershell.exe",
                "-NoProfile",
                "-File",
                str(
                    ROOT
                    / "plugins"
                    / "ai-game-studio-windows"
                    / "scripts"
                    / "ai-game-studio-windows.ps1"
                ),
                "--version",
            ]
        elif system == "Darwin":
            command = [
                "sh",
                str(
                    ROOT
                    / "plugins"
                    / "ai-game-studio-macos"
                    / "scripts"
                    / "ai-game-studio-macos.sh"
                ),
                "--version",
            ]
        else:
            self.skipTest("native launcher smoke test runs on Windows and macOS")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1.1.0", result.stdout)


if __name__ == "__main__":
    unittest.main()
