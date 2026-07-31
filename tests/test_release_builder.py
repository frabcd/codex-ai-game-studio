from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools import build_release


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseBuilderTests(unittest.TestCase):
    def test_release_version_must_match_checked_in_packages(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-version-") as temporary:
            output = Path(temporary) / "dist"
            with self.assertRaisesRegex(
                ValueError,
                "does not match checked-in package versions",
            ):
                build_release.build(ROOT, output, "9.9.9")
            self.assertFalse(output.exists())

    def test_source_payloads_have_checkout_independent_line_endings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-lines-") as temporary:
            root = Path(temporary)
            lf_file = root / "sample.svg"
            crlf_file = root / "sample.ps1"
            binary_file = root / "sample.bin"
            lf_file.write_bytes(b"<svg>\r\n</svg>\r\n")
            crlf_file.write_bytes(b"Write-Output 'ok'\nexit 0\n")
            binary_file.write_bytes(b"\x00\r\n\xff")
            self.assertEqual(b"<svg>\n</svg>\n", build_release.canonical_file_bytes(lf_file))
            self.assertEqual(
                b"Write-Output 'ok'\r\nexit 0\r\n",
                build_release.canonical_file_bytes(crlf_file),
            )
            self.assertEqual(binary_file.read_bytes(), build_release.canonical_file_bytes(binary_file))

    def test_release_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-a-") as first, tempfile.TemporaryDirectory(
            prefix="ags-release-b-"
        ) as second:
            first_dir, second_dir = Path(first), Path(second)
            build_release.build(ROOT, first_dir, "1.1.1")
            build_release.build(ROOT, second_dir, "1.1.1")
            first_files = sorted(path.name for path in first_dir.iterdir())
            second_files = sorted(path.name for path in second_dir.iterdir())
            self.assertEqual(first_files, second_files)
            self.assertEqual(16, len(first_files))
            for name in first_files:
                self.assertEqual(digest(first_dir / name), digest(second_dir / name), name)

            manifest = json.loads((first_dir / "release-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("1.1.1", manifest["version"])
            self.assertEqual({"macos", "windows"}, set(manifest["editions"]))
            self.assertEqual(14, len(manifest["artifacts"]))
            sbom = json.loads((first_dir / "codex-ai-game-studio-v1.1.1.spdx.json").read_text(encoding="utf-8"))
            self.assertEqual("SPDX-2.3", sbom["spdxVersion"])
            self.assertEqual("MIT AND Apache-2.0", sbom["packages"][0]["licenseDeclared"])
            self.assertGreater(len(sbom["files"]), 100)

    def test_archives_use_safe_sorted_paths_and_fixed_timestamps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-zip-") as temporary:
            output = Path(temporary)
            build_release.build(ROOT, output, "1.1.1")
            for archive_path in output.glob("*.zip"):
                with zipfile.ZipFile(archive_path) as archive:
                    names = archive.namelist()
                    self.assertEqual(sorted(names), names, archive_path.name)
                    self.assertTrue(names)
                    for info in archive.infolist():
                        self.assertEqual(build_release.FIXED_ZIP_TIME, info.date_time)
                        self.assertFalse(info.filename.startswith("/"))
                        self.assertNotIn("..", Path(info.filename).parts)

    def test_release_excludes_ignored_temp_and_custom_output_trees(self) -> None:
        ignored_root = ROOT / ".tmp"
        ignored_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="release-input-", dir=ignored_root) as ignored, tempfile.TemporaryDirectory(
            prefix="release-output-", dir=ROOT
        ) as output:
            ignored_sentinel = Path(ignored) / "must-not-ship.txt"
            output_sentinel = Path(output) / "must-not-recurse.txt"
            ignored_sentinel.write_text("ignored", encoding="utf-8")
            output_sentinel.write_text("old output", encoding="utf-8")
            selected = build_release.release_files(ROOT, output=Path(output).resolve())
            self.assertNotIn(ignored_sentinel, selected)
            self.assertNotIn(output_sentinel, selected)
            build_release.build(ROOT, Path(output), "1.1.1")
            with zipfile.ZipFile(Path(output) / "codex-ai-game-studio-v1.1.1.zip") as archive:
                names = archive.namelist()
                self.assertFalse(any("must-not-ship.txt" in name for name in names))
                self.assertFalse(any("must-not-recurse.txt" in name for name in names))

    def test_platform_editions_contain_only_the_matching_platform_plugin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-editions-") as temporary:
            output = Path(temporary)
            build_release.build(ROOT, output, "1.1.1")
            required_img_references = {
                "cs2_finishes.md",
                "geometry_patterns.md",
                "threejs_texture_reference.md",
            }
            for edition, included, excluded in (
                ("windows", "ai-game-studio-windows", "ai-game-studio-macos"),
                ("macos", "ai-game-studio-macos", "ai-game-studio-windows"),
            ):
                archive_path = output / f"codex-ai-game-studio-{edition}-v1.1.1.zip"
                prefix = f"codex-ai-game-studio-{edition}-v1.1.1"
                with zipfile.ZipFile(archive_path) as archive:
                    names = archive.namelist()
                    self.assertIn(f"{prefix}/README.md", names)
                    readme = archive.read(f"{prefix}/README.md").decode("utf-8")
                    marketplace_id = f"frabcd-ai-game-studio-{edition}"
                    self.assertIn("codex plugin marketplace add .", readme)
                    self.assertIn(
                        f"ai-game-studio@{marketplace_id}",
                        readme,
                    )
                    self.assertIn(
                        f"{included}@{marketplace_id}",
                        readme,
                    )
                    marketplace_name = f"{prefix}/.agents/plugins/marketplace.json"
                    marketplace = json.loads(archive.read(marketplace_name))
                    self.assertEqual(marketplace["name"], marketplace_id)
                    plugin_names = {entry["name"] for entry in marketplace["plugins"]}
                    self.assertIn("ai-game-studio", plugin_names)
                    self.assertIn("ai-game-studio-img2threejs", plugin_names)
                    self.assertIn(included, plugin_names)
                    self.assertNotIn(excluded, plugin_names)
                    self.assertTrue(
                        any(f"/plugins/{included}/" in name for name in names)
                    )
                    self.assertFalse(
                        any(f"/plugins/{excluded}/" in name for name in names)
                    )
                    for reference in required_img_references:
                        self.assertIn(
                            f"{prefix}/plugins/ai-game-studio-img2threejs/"
                            f"skills/img2threejs/grimoire/build/{reference}",
                            names,
                        )

            for archive_name, prefix in (
                (
                    "ai-game-studio-img2threejs-v1.1.1.zip",
                    "ai-game-studio-img2threejs",
                ),
                (
                    "codex-ai-game-studio-v1.1.1.zip",
                    "codex-ai-game-studio-v1.1.1/plugins/ai-game-studio-img2threejs",
                ),
            ):
                with zipfile.ZipFile(output / archive_name) as archive:
                    names = set(archive.namelist())
                    for reference in required_img_references:
                        self.assertIn(
                            f"{prefix}/skills/img2threejs/grimoire/build/{reference}",
                            names,
                        )


if __name__ == "__main__":
    unittest.main()
