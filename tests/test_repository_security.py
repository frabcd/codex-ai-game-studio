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

    def test_workflow_scan_rejects_privileged_pr_triggers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-privileged-pr-") as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "target.yml").write_text("on:\n  pull_request_target:\n", encoding="utf-8")
            (workflows / "handoff.yml").write_text("on:\n  workflow_run:\n", encoding="utf-8")
            validator = Validator(root)
            validator.validate_workflows()
            codes = {problem.code for problem in validator.problems}
            self.assertIn("workflow-privileged-pr", codes)
            self.assertIn("workflow-privileged-handoff", codes)

    def test_workflow_scan_rejects_unsafe_fork_permissions_and_runner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-fork-workflow-") as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "unsafe.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: write\n"
                "jobs:\n"
                "  unsafe:\n"
                "    runs-on: [self-hosted, linux]\n"
                "    steps:\n"
                "      - run: echo '${{ secrets.PRIVATE_TOKEN }}'\n",
                encoding="utf-8",
            )
            validator = Validator(root)
            validator.validate_workflows()
            codes = {problem.code for problem in validator.problems}
            self.assertIn("workflow-pr-secret", codes)
            self.assertIn("workflow-pr-self-hosted", codes)
            self.assertIn("workflow-pr-write", codes)

    def test_workflow_scan_requires_checkout_credentials_to_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-checkout-workflow-") as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "checkout.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  validate:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - name: Checkout\n"
                "        uses: actions/checkout@" + "1" * 40 + "\n",
                encoding="utf-8",
            )
            validator = Validator(root)
            validator.validate_workflows()
            codes = {problem.code for problem in validator.problems}
            self.assertIn("workflow-checkout-credentials", codes)

    def test_workflow_scan_allows_read_only_pr_and_codeql_permission(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-safe-pr-workflow-") as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "codeql.yml").write_text(
                "on:\n"
                "  pull_request:\n"
                "permissions:\n"
                "  contents: read\n"
                "  security-events: write\n"
                "jobs:\n"
                "  analyze:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - name: Checkout\n"
                "        uses: actions/checkout@" + "1" * 40 + "\n"
                "        with:\n"
                "          persist-credentials: false\n",
                encoding="utf-8",
            )
            validator = Validator(root)
            validator.validate_workflows()
            blocked = {
                "workflow-pr-secret",
                "workflow-pr-self-hosted",
                "workflow-pr-write",
                "workflow-checkout-credentials",
            }
            self.assertFalse(blocked & {problem.code for problem in validator.problems})


if __name__ == "__main__":
    unittest.main()
