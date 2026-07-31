from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ai-game-studio-windows"
DESCRIPTOR = PLUGIN / "editions" / "windows.json"


class WindowsEditionTests(unittest.TestCase):
    def test_manifest_and_explicit_skill_contract(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "ai-game-studio-windows")
        self.assertEqual(manifest["version"], "1.1.1")
        self.assertEqual(manifest["license"], "MIT")
        self.assertLessEqual(len(manifest["interface"]["defaultPrompt"]), 128)

        skill_path = PLUGIN / "skills" / "setup-windows-edition" / "SKILL.md"
        skill = skill_path.read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        keys = {
            line.split(":", 1)[0].strip()
            for line in frontmatter.splitlines()
            if ":" in line
        }
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: setup-windows-edition", frontmatter)

        metadata = (
            skill_path.parent / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn(
            "$ai-game-studio-windows:setup-windows-edition", metadata
        )

    def test_descriptor_has_complete_native_and_adaptation_surface(self) -> None:
        descriptor = json.loads(DESCRIPTOR.read_text(encoding="utf-8"))
        required = {
            "id",
            "plugin",
            "display_name",
            "target_os",
            "version",
            "supported_architectures",
            "shells",
            "package_managers",
            "gpu_backends",
            "applications",
            "native_capabilities",
            "adaptation_rules",
            "permissions",
            "health_checks",
            "uninstall",
            "rollback",
            "activation",
        }
        self.assertTrue(required.issubset(descriptor))
        self.assertEqual(descriptor["id"], "windows")
        self.assertEqual(descriptor["plugin"], "ai-game-studio-windows")
        self.assertEqual(descriptor["target_os"], "Windows")
        self.assertEqual(descriptor["version"], "1.1.1")
        self.assertEqual(descriptor["license"], "MIT")
        self.assertEqual(
            set(descriptor["supported_architectures"]), {"amd64", "arm64"}
        )
        self.assertEqual(
            {item["id"] for item in descriptor["package_managers"]},
            {"winget", "chocolatey", "scoop"},
        )
        self.assertEqual(
            {item["id"] for item in descriptor["gpu_backends"]},
            {"cuda", "directml", "cpu", "warp"},
        )
        self.assertEqual(
            {item["id"] for item in descriptor["applications"]},
            {
                "unity",
                "godot",
                "unreal",
                "blender",
                "aseprite",
                "pixelorama",
                "tiled",
            },
        )
        self.assertFalse(descriptor["wsl_fallback"]["default"])
        self.assertTrue(descriptor["wsl_fallback"]["requires_confirmation"])
        self.assertEqual(
            descriptor["activation"],
            {
                "mode": "confirmed-transaction-only",
                "project_state": ".ai-game-studio/project.json",
                "lock_file": ".ai-game-studio/lock.json",
            },
        )

    def test_adaptation_rules_are_deterministic_and_never_empty(self) -> None:
        descriptor = json.loads(DESCRIPTOR.read_text(encoding="utf-8"))

        def reject_empty_lists(value: object, path: str = "descriptor") -> None:
            if isinstance(value, list):
                self.assertTrue(value, f"{path} must not be an empty list")
                for index, item in enumerate(value):
                    reject_empty_lists(item, f"{path}[{index}]")
            elif isinstance(value, dict):
                for key, item in value.items():
                    reject_empty_lists(item, f"{path}.{key}")

        reject_empty_lists(descriptor)
        required_rule_keys = {
            "id",
            "source_constraint",
            "preferred_native",
            "alternatives",
            "limitations",
            "requires_confirmation",
        }
        rules = descriptor["adaptation_rules"]
        self.assertEqual(len({rule["id"] for rule in rules}), len(rules))
        for rule in rules:
            self.assertTrue(required_rule_keys.issubset(rule))
            self.assertTrue(rule["requires_confirmation"])
            self.assertTrue(rule["alternatives"])
            self.assertTrue(rule["limitations"])

        combined = json.dumps(rules).lower()
        for constraint in ("posix", "macos", "homebrew", "metal", "apple-silicon"):
            self.assertIn(constraint, combined)
        self.assertIn("not binary-compatible", combined)

    def test_documentation_exposes_commands_artifacts_and_rollback(self) -> None:
        docs = (ROOT / "docs" / "platforms" / "windows.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "$ai-game-studio-windows:setup-windows-edition", docs
        )
        self.assertIn("ai-game-studio-windows.ps1", docs)
        self.assertIn("doctor --project", docs)
        self.assertIn("plan --project", docs)
        self.assertIn("apply --project", docs)
        self.assertGreaterEqual(docs.count("### What to say"), 4)
        self.assertGreaterEqual(
            docs.count("### Expected artifacts and rollback"), 4
        )
        self.assertIn("Never claim", docs)


if __name__ == "__main__":
    unittest.main()
