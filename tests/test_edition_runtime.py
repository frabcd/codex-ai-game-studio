from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "plugins" / "ai-game-studio" / "scripts"
sys.path.insert(0, str(CORE_DIR))
import ags_core as core  # noqa: E402


class EditionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        self.doctor_patch = mock.patch.object(
            core,
            "doctor",
            return_value={
                "read_only": True,
                "platform": {
                    "os": "Windows",
                    "architecture": "amd64",
                    "execution": "native",
                },
            },
        )
        self.doctor_patch.start()

    def tearDown(self) -> None:
        self.doctor_patch.stop()
        self.temporary.cleanup()

    def test_both_edition_descriptors_are_discoverable_and_confirmation_gated(self) -> None:
        descriptors = core.load_edition_descriptors()
        self.assertEqual(set(descriptors), {"windows", "macos"})
        for edition_id, descriptor in descriptors.items():
            self.assertEqual(descriptor["id"], edition_id)
            self.assertEqual(descriptor["version"], "1.1.0")
            self.assertEqual(descriptor["license"], "MIT")
            self.assertEqual(descriptor["activation"]["mode"], "confirmed-transaction-only")
            self.assertTrue(descriptor["adaptation_rules"])
            for rule in descriptor["adaptation_rules"]:
                self.assertTrue(rule["requires_confirmation"])
                self.assertTrue(rule["limitations"])

    def test_edition_doctor_is_read_only_and_exposes_adaptations(self) -> None:
        report = core.edition_doctor("windows", project_root=self.project)
        self.assertTrue(report["read_only"])
        self.assertTrue(report["target_matches_host"])
        self.assertTrue(report["architecture_supported"])
        self.assertTrue(report["adaptation_rules"])
        self.assertFalse(report["mutation_performed"])
        detection = report["detected_environment"]["edition_detection"]
        self.assertTrue(detection["host_matches"])
        self.assertEqual(
            set(detection["package_managers"]),
            {"winget", "chocolatey", "scoop"},
        )
        self.assertEqual(
            set(detection["gpu_backends"]),
            {"cuda", "directml", "cpu", "warp"},
        )
        for backend in detection["gpu_backends"].values():
            self.assertFalse(backend["verified_for_selected_tool"])
        self.assertFalse((self.project / core.STATE_DIR).exists())

    def test_plan_apply_disable_and_rollback_are_digest_gated(self) -> None:
        with mock.patch.object(core.platform, "system", return_value="Windows"), mock.patch.object(
            core.platform, "machine", return_value="AMD64"
        ):
            plan = core.edition_plan("windows", project_root=self.project)
        self.assertEqual(plan["kind"], "edition-select")
        self.assertEqual(plan["metadata"]["edition"], "windows")
        self.assertFalse(plan["metadata"]["external_installation_performed"])
        self.assertEqual(plan["downloads"], [])
        self.assertFalse((self.project / core.STATE_DIR).exists())

        with self.assertRaises(core.StudioError):
            core.apply_plan(plan, project_root=self.project, confirmed_digest="0" * 64)
        transaction = core.apply_plan(
            plan,
            project_root=self.project,
            confirmed_digest=plan["digest"],
        )
        project_state = json.loads(
            (self.project / core.STATE_DIR / "project.json").read_text(encoding="utf-8")
        )
        self.assertEqual(project_state["platform_edition"]["id"], "windows")
        self.assertFalse(project_state["platform_edition"]["external_tools_installed"])

        disable = core.edition_disable_plan("windows", project_root=self.project)
        disabled_transaction = core.apply_plan(
            disable,
            project_root=self.project,
            confirmed_digest=disable["digest"],
        )
        disabled_state = json.loads(
            (self.project / core.STATE_DIR / "project.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("platform_edition", disabled_state)

        rollback = core.rollback_plan(
            disabled_transaction["transaction_id"],
            project_root=self.project,
        )
        core.apply_plan(
            rollback,
            project_root=self.project,
            confirmed_digest=rollback["digest"],
        )
        restored_state = json.loads(
            (self.project / core.STATE_DIR / "project.json").read_text(encoding="utf-8")
        )
        self.assertEqual(restored_state["platform_edition"]["id"], "windows")
        self.assertEqual(transaction["kind"], "edition-select")

    def test_edition_apply_rejects_other_plan_kinds_and_targets(self) -> None:
        foreign = core.make_plan(
            kind="pack-enable",
            project_root=self.project,
            actions=[],
        )
        with self.assertRaisesRegex(core.StudioError, "cannot be applied"):
            core.validate_edition_apply_plan(foreign)

        escaped_scope = core.make_plan(
            kind="edition-select",
            project_root=self.project,
            actions=[
                core.write_action(
                    ".codex/config.toml",
                    {"unexpected": True},
                )
            ],
        )
        with self.assertRaisesRegex(core.StudioError, "may not change"):
            core.validate_edition_apply_plan(escaped_scope)

    def test_edition_rollback_rejects_non_edition_transaction(self) -> None:
        foreign = core.make_plan(
            kind="pack-enable",
            project_root=self.project,
            actions=[],
        )
        transaction = core.apply_plan(
            foreign,
            project_root=self.project,
            confirmed_digest=foreign["digest"],
        )
        with self.assertRaisesRegex(core.StudioError, "cannot be rolled back"):
            core.rollback_plan(
                transaction["transaction_id"],
                project_root=self.project,
                allowed_original_kinds={"edition-select", "edition-disable"},
            )

    def test_cross_platform_apply_is_rejected_instead_of_faking_compatibility(self) -> None:
        with mock.patch.object(core.platform, "system", return_value="Darwin"), mock.patch.object(
            core.platform, "machine", return_value="arm64"
        ):
            with self.assertRaisesRegex(core.StudioError, "targets Windows"):
                core.edition_plan("windows", project_root=self.project)


if __name__ == "__main__":
    unittest.main()
