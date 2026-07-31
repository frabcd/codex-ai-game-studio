from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ai-game-studio-img2threejs"
SKILL = PLUGIN / "skills" / "img2threejs"
UPSTREAM_COMMIT = "9a8ecf129a58c1b557a1f03f7727f6295672cd51"
UPSTREAM_TAG_OBJECT = "82a1c24812a728781ae89fc4a5a7231b367ae02f"
LICENSE_SHA256 = "4595055948a67e91177115c57e154804046878e77ff223de22accc880012827a"


def normalized_text_sha256(path: Path) -> str:
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def write_test_png(path: Path, width: int = 512, height: int = 512) -> None:
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    scanline = b"\x00" + (b"\x80\x70\x60" * width)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(scanline * height, level=9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def run_python(script: Path, *arguments: object, cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(script), *(str(argument) for argument in arguments)],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
    )


class Img2ThreeJsPluginTests(unittest.TestCase):
    def test_provenance_is_pinned_to_dereferenced_release_tag(self) -> None:
        provenance = json.loads((PLUGIN / "UPSTREAM.json").read_text(encoding="utf-8"))
        self.assertEqual("img2threejs/img2threejs", provenance["repository"])
        self.assertEqual("https://github.com/img2threejs/img2threejs", provenance["url"])
        self.assertEqual("v1.4.3", provenance["tag"])
        self.assertEqual(UPSTREAM_TAG_OBJECT, provenance["tag_object"])
        self.assertEqual(UPSTREAM_COMMIT, provenance["commit"])
        self.assertEqual("Apache-2.0", provenance["license"])
        self.assertEqual("2026-07-31", provenance["retrieved_at"])
        self.assertTrue(provenance["modifications"])
        self.assertTrue(all(item.get("path") and item.get("summary") for item in provenance["modifications"]))

    def test_upstream_license_is_preserved_at_plugin_and_skill_roots(self) -> None:
        self.assertEqual(LICENSE_SHA256, normalized_text_sha256(PLUGIN / "LICENSE"))
        self.assertEqual(LICENSE_SHA256, normalized_text_sha256(SKILL / "LICENSE"))

    def test_vendor_tree_excludes_repository_and_generated_junk(self) -> None:
        forbidden_parts = {".git", ".github", ".cache", "__pycache__", ".pytest_cache"}
        forbidden_suffixes = {".pyc", ".pyo"}
        for path in PLUGIN.rglob("*"):
            relative = path.relative_to(PLUGIN)
            self.assertTrue(forbidden_parts.isdisjoint(relative.parts), relative.as_posix())
            if path.is_file():
                self.assertNotIn(path.suffix.lower(), forbidden_suffixes, relative.as_posix())

        for name in (
            ".gitignore",
            "README.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "ROADMAP.md",
        ):
            self.assertFalse((PLUGIN / name).exists(), name)

        upstream_test_files = {
            path.relative_to(SKILL / "forge" / "tests").as_posix()
            for path in (SKILL / "forge" / "tests").rglob("*")
            if path.is_file()
        }
        self.assertEqual({"fixtures/knife_review_scene.json"}, upstream_test_files)

    def test_skill_frontmatter_metadata_and_runtime_resources_are_complete(self) -> None:
        lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual("---", lines[0])
        closing = lines.index("---", 1)
        keys = [line.split(":", 1)[0] for line in lines[1:closing] if line.strip()]
        self.assertEqual(["name", "description"], keys)
        self.assertEqual("name: img2threejs", lines[1])

        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$ai-game-studio-img2threejs:img2threejs", metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)

        required = (
            "forge/next.py",
            "forge/requirements.txt",
            "forge/stage1_intake/probe_image.py",
            "forge/stage1_intake/search_specs.py",
            "forge/stage2_spec/new_pre_spec_assessment.py",
            "forge/stage2_spec/new_sculpt_spec.py",
            "forge/stage2_spec/validate_sculpt_spec.py",
            "forge/stage3_build/generate_threejs_factory.py",
            "forge/stage4_review/divine_eye.py",
            "forge/stage4_review/correction_loop.py",
            "grimoire/intake/validation_rubric.md",
            "grimoire/build/geometry_patterns.md",
            "docs/specs/vocabulary/core_3d.jsonl",
            "docs/raw/img2threejs-skill-dataset.json",
        )
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)

        runtime_guidance = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SKILL / "SKILL.md", SKILL / "grimoire" / "feedback" / "render_capture.md")
        )
        self.assertNotIn("Claude Code", runtime_guidance)
        next_script = (SKILL / "forge" / "next.py").read_text(encoding="utf-8")
        self.assertIn("sys.executable", next_script)
        self.assertIn("subprocess.list2cmdline", next_script)
        self.assertIn("shlex.join", next_script)

    def test_probe_runs_from_an_unrelated_working_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-img2threejs-probe-") as temporary:
            work = Path(temporary)
            image = work / "reference.png"
            write_test_png(image)
            completed = run_python(
                SKILL / "forge" / "stage1_intake" / "probe_image.py",
                image,
                cwd=work,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual("png", payload["type"])
            self.assertEqual(512, payload["width"])
            self.assertEqual(512, payload["height"])
            self.assertEqual("pass", payload["technicalSuitability"])

    def test_search_output_is_safe_under_a_cp1252_console(self) -> None:
        query = "độ nhám"
        for json_output in (False, True):
            with self.subTest(json_output=json_output):
                with tempfile.TemporaryDirectory(
                    prefix="ags-img2threejs-cp1252-"
                ) as temporary:
                    work = Path(temporary)
                    environment = os.environ.copy()
                    environment["PYTHONIOENCODING"] = "cp1252:strict"
                    environment["PYTHONDONTWRITEBYTECODE"] = "1"
                    arguments = [
                        sys.executable,
                        str(SKILL / "forge" / "stage1_intake" / "search_specs.py"),
                        query,
                        "--collection",
                        "core_3d",
                        "--cache-root",
                        str(work / "cache"),
                    ]
                    if json_output:
                        arguments.append("--json")
                    completed = subprocess.run(
                        arguments,
                        cwd=work,
                        env=environment,
                        capture_output=True,
                        text=True,
                        encoding="cp1252",
                        timeout=30,
                        check=False,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    if json_output:
                        self.assertTrue(completed.stdout.isascii())
                        self.assertEqual(query, json.loads(completed.stdout)["query"])
                    else:
                        self.assertIn("Query:", completed.stdout)
                        self.assertIn("\\u0111", completed.stdout)

    def test_local_search_spec_generation_and_next_router_smoke(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-img2threejs-pipeline-") as temporary:
            work = Path(temporary)
            copied_skill = work / "img2threejs"
            shutil.copytree(SKILL, copied_skill)
            image = work / "reference.png"
            write_test_png(image)
            assessment_path = work / "assessment.json"
            assessment = run_python(
                copied_skill / "forge" / "stage2_spec" / "new_pre_spec_assessment.py",
                "Test Crate",
                "--image",
                image,
                "--complexity",
                "simple",
                "--spec-query",
                "painted wood roughness",
                "--out",
                assessment_path,
                cwd=work,
            )
            self.assertEqual(0, assessment.returncode, assessment.stderr)
            assessment_payload = json.loads(assessment_path.read_text(encoding="utf-8"))
            self.assertEqual("core_3d", assessment_payload["localSpecSearch"]["collection"])
            self.assertTrue(assessment_payload["localSpecSearch"]["matches"])

            spec_path = work / "object-sculpt-spec.json"
            spec = run_python(
                copied_skill / "forge" / "stage2_spec" / "new_sculpt_spec.py",
                "Test Crate",
                "--image",
                image,
                "--assessment",
                assessment_path,
                "--out",
                spec_path,
                cwd=work,
            )
            self.assertEqual(0, spec.returncode, spec.stderr)
            self.assertTrue(spec_path.is_file())

            routed = run_python(copied_skill / "forge" / "next.py", spec_path, cwd=work)
            self.assertEqual(0, routed.returncode, routed.stderr)
            self.assertIn("current pass:", routed.stdout)
            self.assertIn(str(sys.executable), routed.stdout)
            expected_orchestrator = (
                copied_skill / "forge" / "stage3_build" / "orchestrate_passes.py"
            ).resolve()
            self.assertIn(str(expected_orchestrator), routed.stdout)
            self.assertTrue((copied_skill / ".cache").is_dir())
            self.assertFalse((SKILL / ".cache").exists())


if __name__ == "__main__":
    unittest.main()
