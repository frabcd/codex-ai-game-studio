from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
SCRIPT = (
    ROOT
    / "plugins"
    / "ai-game-studio-img2threejs"
    / "skills"
    / "img2threejs"
    / "forge"
    / "stage1_intake"
    / "extract_cs2_textures.py"
)


def load_module():
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("ags_extract_cs2_textures", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Img2ThreeJsExtractorSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temporary = tempfile.TemporaryDirectory(prefix="ags-extractor-")
        self.root = Path(self.temporary.name)
        self.executable = self.root / "Source2Viewer-CLI.exe"
        self.executable.write_bytes(b"synthetic extractor fixture")
        self.digest = hashlib.sha256(self.executable.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_manifest(self, **changes: str) -> Path:
        payload = {
            "executable": str(self.executable.resolve()),
            "sha256": self.digest,
            "version": "fixture-1",
            "license": "MIT",
            "source_url": "https://github.com/ValveResourceFormat/ValveResourceFormat",
            "confirmed_plan_digest": "a" * 64,
        }
        payload.update(changes)
        path = self.root / f"manifest-{len(list(self.root.glob('manifest-*.json')))}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_manifest_requires_absolute_hash_locked_reviewed_executable(self) -> None:
        accepted = self.module.load_extractor_manifest(self.write_manifest())
        self.assertEqual(accepted["sha256"], self.digest)
        for change in (
            {"executable": "Source2Viewer-CLI"},
            {"sha256": "0" * 64},
            {"license": "unknown"},
            {"source_url": "http://example.test/tool"},
            {"confirmed_plan_digest": "short"},
        ):
            with self.assertRaises(ValueError):
                self.module.load_extractor_manifest(self.write_manifest(**change))

    def test_missing_or_invalid_manifest_never_executes_path_binary(self) -> None:
        vpk = self.root / "pak01_dir.vpk"
        vpk.write_bytes(b"fixture")
        with mock.patch.object(self.module, "run_source2viewer") as run:
            result = self.module.extract(
                self.root / "output",
                vpk,
                None,
                None,
                None,
            )
            self.assertEqual(result["status"], "fallback")
            run.assert_not_called()

            result = self.module.extract(
                self.root / "output",
                vpk,
                None,
                None,
                self.write_manifest(sha256="0" * 64),
            )
            self.assertEqual(result["status"], "fallback")
            run.assert_not_called()

    def test_subprocess_uses_absolute_argument_array_and_timeout(self) -> None:
        vpk = self.root / "pak01_dir.vpk"
        output = self.root / "output"
        with mock.patch.object(self.module.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.module.run_source2viewer(self.executable.resolve(), vpk, output, "paint")
        command = run.call_args.args[0]
        self.assertEqual(command[0], str(self.executable.resolve()))
        self.assertIn(str(vpk), command)
        self.assertIn(str(output), command)
        self.assertFalse(run.call_args.kwargs["check"])
        self.assertEqual(run.call_args.kwargs["timeout"], 300)


if __name__ == "__main__":
    unittest.main()
