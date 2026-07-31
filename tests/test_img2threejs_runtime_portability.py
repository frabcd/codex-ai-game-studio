from __future__ import annotations

import base64
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    REPO_ROOT
    / "plugins"
    / "ai-game-studio-img2threejs"
    / "skills"
    / "img2threejs"
)
FORGE_ROOT = SKILL_ROOT / "forge"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

image_decode = importlib.import_module("forge._shared.image_decode")
spec_search = importlib.import_module("forge._shared.spec_search")
detail_inventory = importlib.import_module("forge.stage1_intake.build_detail_inventory")


# Standards-complete one-pixel baseline JPEG with one sequential scan. It is
# decoded by the native Windows/macOS converter in the platform integration
# test, never by a Python image package.
JPEG_1X1 = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQ"
    "DQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQU"
    "FBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEB"
    "AQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKB"
    "kaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1"
    "dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl"
    "5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcF"
    "BAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5"
    "OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0"
    "tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD8/KKKK908"
    "Q//Z"
)


class SpecSearchCachePortabilityTests(unittest.TestCase):
    def test_default_cache_root_uses_approved_environment_outside_skill(self) -> None:
        profile = spec_search.load_profile("core_3d")
        with tempfile.TemporaryDirectory() as temporary:
            approved = Path(temporary) / "approved-cache"
            with mock.patch.dict(
                os.environ,
                {"AI_GAME_STUDIO_CACHE_DIR": str(approved)},
                clear=False,
            ):
                path = spec_search._cache_path(
                    spec_search.IndexRequest(SKILL_ROOT, "core_3d", profile)
                )

            path.relative_to(approved.resolve())
            with self.assertRaises(ValueError):
                path.relative_to(SKILL_ROOT.resolve())
            self.assertFalse((SKILL_ROOT / ".cache").exists())

    def test_cache_root_inside_installed_skill_is_rejected_before_write(self) -> None:
        profile = spec_search.load_profile("core_3d")
        forbidden = SKILL_ROOT / "runtime-cache"
        with self.assertRaises(spec_search.CacheValidationError) as raised:
            spec_search._cache_path(
                spec_search.IndexRequest(
                    SKILL_ROOT,
                    "core_3d",
                    profile,
                    cache_root=forbidden,
                )
            )
        self.assertIn("outside the installed img2threejs source tree", str(raised.exception))
        self.assertFalse(forbidden.exists())

    def test_search_cli_writes_only_to_explicit_cache_root(self) -> None:
        script = FORGE_ROOT / "stage1_intake" / "search_specs.py"
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary) / "search-cache"
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "surface topology",
                    "--collection",
                    "core_3d",
                    "--cache-root",
                    str(cache_root),
                    "--json",
                ],
                cwd=SKILL_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
                check=False,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            cache_path = Path(payload["index"]["cache_path"]).resolve()
            cache_path.relative_to(cache_root.resolve())
            self.assertTrue(cache_path.is_file())
            self.assertFalse((SKILL_ROOT / ".cache").exists())


class ImageDecodePortabilityTests(unittest.TestCase):
    def test_all_five_pixel_loaders_use_shared_decoder(self) -> None:
        loaders = [
            FORGE_ROOT / "stage1_intake" / "build_detail_inventory.py",
            FORGE_ROOT / "stage1_intake" / "delight_albedo.py",
            FORGE_ROOT / "stage1_intake" / "extract_landmarks.py",
            FORGE_ROOT / "stage1_intake" / "extract_pbr_evidence.py",
            FORGE_ROOT / "stage4_review" / "make_comparison_sheet.py",
        ]
        for path in loaders:
            source = path.read_text(encoding="utf-8")
            self.assertIn("load_rgba_image", source, path.name)
            self.assertNotIn('shutil.which("sips")', source, path.name)
            self.assertNotIn("shell=True", source, path.name)

    def test_unsupported_format_has_clear_error_without_launching_converter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "reference.avif"
            source.write_bytes(b"not-an-image")
            with mock.patch.object(image_decode, "_convert_to_png") as converter:
                with self.assertRaises(image_decode.ImageDecodeError) as raised:
                    image_decode.load_rgba_image(
                        source,
                        lambda _path: (_ for _ in ()).throw(ValueError("not PNG")),
                    )
            converter.assert_not_called()
        self.assertIn("unsupported image format '.avif'", str(raised.exception))

    def test_process_boundary_passes_argv_and_disables_shell(self) -> None:
        completed = subprocess.CompletedProcess(["tool"], 0, "", "")
        with mock.patch.object(
            image_decode.subprocess,
            "run",
            return_value=completed,
        ) as run:
            image_decode._run(["tool", "argument with spaces"])
        self.assertEqual(run.call_args.args[0], ["tool", "argument with spaces"])
        self.assertIs(run.call_args.kwargs["shell"], False)

    def test_imagemagick_is_verified_before_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "input.jpg"
            destination = Path(temporary) / "output.png"
            executable = Path(temporary) / "magick"
            executable.write_bytes(b"synthetic ImageMagick fixture")
            manifest = Path(temporary) / "imagemagick.json"
            manifest.write_text(
                json.dumps(
                    {
                        "executable": str(executable.resolve()),
                        "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                        "version": "7.1.1",
                        "license": "Apache-2.0",
                        "source_url": "https://imagemagick.org/",
                        "confirmed_plan_digest": "b" * 64,
                    }
                ),
                encoding="utf-8",
            )
            source.write_bytes(JPEG_1X1)
            calls: list[list[str]] = []

            def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                if command[-1] == "-version":
                    return subprocess.CompletedProcess(command, 0, "ImageMagick 7.1.1", "")
                destination.write_bytes(b"converted")
                return subprocess.CompletedProcess(command, 0, "", "")

            with (
                mock.patch.dict(
                    os.environ,
                    {"AI_GAME_STUDIO_IMAGEMAGICK_MANIFEST": str(manifest)},
                    clear=False,
                ),
                mock.patch.object(image_decode, "_run", side_effect=fake_run),
            ):
                backend = image_decode._convert_imagemagick(source, destination)

        self.assertEqual(backend, "verified ImageMagick")
        self.assertEqual(calls[0], [str(executable.resolve()), "-version"])
        self.assertEqual(
            calls[1],
            [str(executable.resolve()), str(source), "-auto-orient", str(destination)],
        )

    def test_imagemagick_path_lookup_is_never_used_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "input.webp"
            destination = Path(temporary) / "output.png"
            source.write_bytes(b"fixture")
            with mock.patch.dict(
                os.environ,
                {"AI_GAME_STUDIO_IMAGEMAGICK_MANIFEST": ""},
                clear=False,
            ):
                with self.assertRaises(image_decode.ImageDecodeError):
                    image_decode._convert_imagemagick(source, destination)

    @unittest.skipUnless(
        sys.platform == "win32" or sys.platform == "darwin",
        "native JPEG integration is available on Windows and macOS",
    )
    def test_common_jpeg_decodes_with_native_platform_converter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "one-pixel.jpg"
            source.write_bytes(JPEG_1X1)
            width, height, pixels, warnings = image_decode.load_rgba_image(
                source,
                detail_inventory.read_png,
            )
        self.assertEqual((width, height), (1, 1))
        self.assertEqual(len(pixels), 1)
        self.assertTrue(warnings)


if __name__ == "__main__":
    unittest.main()
