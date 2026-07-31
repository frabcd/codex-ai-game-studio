from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ai-game-studio-macos"
DESCRIPTOR = PLUGIN / "editions" / "macos.json"


class MacOSEditionTests(unittest.TestCase):
    def test_manifest_and_explicit_skill_contract(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "ai-game-studio-macos")
        self.assertEqual(manifest["version"], "1.1.1")
        self.assertEqual(manifest["license"], "MIT")
        self.assertLessEqual(len(manifest["interface"]["defaultPrompt"]), 128)

        skill_path = PLUGIN / "skills" / "setup-macos-edition" / "SKILL.md"
        skill = skill_path.read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        keys = {
            line.split(":", 1)[0].strip()
            for line in frontmatter.splitlines()
            if ":" in line
        }
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: setup-macos-edition", frontmatter)

        metadata = (skill_path.parent / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("$ai-game-studio-macos:setup-macos-edition", metadata)

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
        self.assertEqual(descriptor["id"], "macos")
        self.assertEqual(descriptor["plugin"], "ai-game-studio-macos")
        self.assertEqual(descriptor["target_os"], "Darwin")
        self.assertEqual(descriptor["version"], "1.1.1")
        self.assertEqual(descriptor["license"], "MIT")
        self.assertEqual(
            set(descriptor["supported_architectures"]), {"arm64", "x86_64"}
        )
        self.assertEqual(
            {item["id"] for item in descriptor["shells"]},
            {"zsh", "posix-sh", "bash"},
        )
        self.assertEqual(
            {item["id"] for item in descriptor["package_managers"]},
            {"homebrew", "macports"},
        )
        self.assertEqual(
            {item["id"] for item in descriptor["gpu_backends"]},
            {"metal", "mps", "core-ml", "cpu"},
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
        self.assertFalse(descriptor["rosetta"]["automatic"])
        self.assertTrue(descriptor["rosetta"]["disclosure_required"])
        self.assertEqual(
            descriptor["activation"],
            {
                "mode": "confirmed-transaction-only",
                "project_state": ".ai-game-studio/project.json",
                "lock_file": ".ai-game-studio/lock.json",
            },
        )

    def test_adaptation_rules_are_complete_and_confirmation_gated(self) -> None:
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
        for constraint in ("windows", "powershell", "cuda", "directml", "rosetta"):
            self.assertIn(constraint, combined)
        self.assertIn("not macos binaries", combined)

    def test_documentation_exposes_commands_artifacts_and_rollback(self) -> None:
        docs = (ROOT / "docs" / "platforms" / "macos.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("$ai-game-studio-macos:setup-macos-edition", docs)
        self.assertIn("ai-game-studio-macos.sh", docs)
        self.assertIn("doctor --project", docs)
        self.assertIn("plan --project", docs)
        self.assertIn("apply --project", docs)
        self.assertGreaterEqual(docs.count("## What to say"), 5)
        self.assertIn("Expected artifacts", docs)
        self.assertIn("Do not claim binary compatibility", docs)


if __name__ == "__main__":
    unittest.main()
