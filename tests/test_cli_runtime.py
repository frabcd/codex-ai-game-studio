from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "plugins" / "ai-game-studio" / "scripts" / "ai_game_studio.py"


class CliSurfaceTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CLI), *args], cwd=REPO, capture_output=True, text=True, check=False, timeout=30)

    def test_version(self) -> None:
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "1.1.0")

    def test_native_launcher_for_current_platform(self) -> None:
        scripts = CLI.parent
        if os.name == "nt":
            powershell = shutil.which("powershell")
            self.assertIsNotNone(powershell)
            command = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(scripts / "ai-game-studio.ps1"), "--version"]
        else:
            command = ["/bin/sh", str(scripts / "ai-game-studio.sh"), "--version"]
        result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "1.1.0")

    def test_required_command_surface(self) -> None:
        root_help = self.run_cli("--help")
        self.assertEqual(root_help.returncode, 0)
        for command in ("doctor", "catalog", "pack", "migrate", "validate"):
            self.assertIn(command, root_help.stdout)
        pack_help = self.run_cli("pack", "--help")
        for command in ("doctor", "plan", "apply", "disable", "rollback"):
            self.assertIn(command, pack_help.stdout)

    def test_catalog_search_is_machine_readable(self) -> None:
        result = self.run_cli("catalog", "search", "sprite", "--limit", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["query"], "sprite")
        self.assertIsInstance(payload["results"], list)
        self.assertGreater(len(payload["results"]), 0)

    def test_commercial_recommendation_blocks_unknown_license_scopes(self) -> None:
        result = self.run_cli("catalog", "recommend", "--capability", "agent-skills", "--commercial", "--limit", "5")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreater(len(payload["results"]), 0)
        blocking = {"unknown", "custom", "restricted", "prohibited"}
        for recommendation in payload["results"]:
            licenses = recommendation["record"]["licenses"]
            statuses = {licenses[scope]["status"] for scope in ("code", "model_weights", "dataset", "generated_output")}
            self.assertFalse(statuses.intersection(blocking))
            self.assertIn("license:human-review-required", recommendation["reasons"])

    def test_unknown_pack_returns_json_error(self) -> None:
        result = self.run_cli("pack", "plan", "not-a-pack", "--project", str(REPO))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))

    def test_checked_in_parity_ledger_validates(self) -> None:
        result = self.run_cli("validate", "parity", str(REPO))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_checked_in_core_plugin_validates(self) -> None:
        result = self.run_cli("validate", "plugin", str(REPO / "plugins" / "ai-game-studio"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_checked_in_core_skills_validate(self) -> None:
        result = self.run_cli("validate", "skills", str(REPO / "plugins" / "ai-game-studio" / "skills"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
