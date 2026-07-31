from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.validate_repository import Validator, parse_frontmatter, safe_resolve


class RepositorySecurityTests(unittest.TestCase):
    def test_frontmatter_accepts_only_scalar_pairs_for_later_policy_check(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-frontmatter-") as temporary:
            skill = Path(temporary) / "SKILL.md"
            skill.write_text('---\nname: demo\ndescription: "Safe: demo"\n---\n# Demo\n', encoding="utf-8")
            parsed, problem = parse_frontmatter(skill)
            self.assertIsNone(problem)
            self.assertEqual({"name": "demo", "description": "Safe: demo"}, parsed)

    def test_safe_resolve_rejects_absolute_and_parent_escape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-path-") as temporary:
            root = Path(temporary).resolve()
            self.assertIsNone(safe_resolve(root, "../escape"))
            self.assertIsNone(safe_resolve(root, str((root.parent / "absolute").resolve())))
            self.assertEqual(root / "inside" / "file.json", safe_resolve(root, "inside/file.json"))

    def test_security_scan_detects_secret_and_unsafe_shell(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-security-") as temporary:
            root = Path(temporary)
            script = root / "tools" / "bad.py"
            script.parent.mkdir(parents=True)
            script.write_text(
                'import subprocess\nTOKEN = "' + "ghp_" + "1" * 36 + '"\nsubprocess.run("echo bad", shell' + '=True)\n',
                encoding="utf-8",
            )
            validator = Validator(root)
            validator.validate_source_safety()
            codes = {problem.code for problem in validator.problems}
            self.assertIn("credential-leak", codes)
            self.assertIn("unsafe-command", codes)

    def test_workflow_scan_rejects_mutable_action_tag(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-workflow-") as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("steps:\n  - uses: actions/checkout@v4\n", encoding="utf-8")
            validator = Validator(root)
            validator.validate_workflows()
            messages = [problem.render() for problem in validator.problems]
            self.assertTrue(any("workflow-unpinned" in message for message in messages))

    def test_workflow_scan_rejects_release_asset_replacement(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-workflow-") as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "release.yml").write_text(
                "steps:\n"
                "  - run: gh release upload \"$RELEASE_TAG\" dist/* --clobber\n",
                encoding="utf-8",
            )
            validator = Validator(root)
            validator.validate_workflows()
            codes = {problem.code for problem in validator.problems}
            self.assertIn("release-mutable-assets", codes)
            self.assertIn("release-immutability-guard", codes)


if __name__ == "__main__":
    unittest.main()
