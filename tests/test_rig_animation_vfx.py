from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "ai-game-studio" / "skills" / "rig-animation"
REFERENCE = SKILL / "references" / "procedural-vfx-composer.md"
ASSETS = SKILL / "assets" / "procedural-vfx-composer"
EXAMPLE = ASSETS / "vfx-project.example.json"
SCHEMA = ASSETS / "vfx-project.schema.json"
SCRIPT = SKILL / "scripts" / "validate_vfx_spec.py"
START_SKILL = ROOT / "plugins" / "ai-game-studio" / "skills" / "start" / "SKILL.md"
PLUGIN_MANIFEST = ROOT / "plugins" / "ai-game-studio" / ".codex-plugin" / "plugin.json"
CANONICAL_GENERATOR = ROOT / "parity" / "tools" / "generate_parity.py"
CATALOG_GENERATOR = (
    ROOT / "plugins" / "ai-game-studio" / "catalog" / "tools" / "generate_catalog.py"
)
COMPOSER_SVG = ROOT / "assets" / "examples" / "procedural-vfx-composer.svg"
SOCIAL_PREVIEW = ROOT / "assets" / "branding" / "social-preview.png"

MODULE_SPEC = importlib.util.spec_from_file_location("ags_validate_vfx_spec", SCRIPT)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError(f"cannot load validator at {SCRIPT}")
VALIDATOR = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(VALIDATOR)


def load_example() -> dict[str, object]:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def all_strings(value: object) -> list[str]:
    found: list[str] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            found.extend(str(key) for key in item)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, str):
            found.append(item)
    return found


class RigAnimationVfxTests(unittest.TestCase):
    def test_skill_and_canonical_routes_link_the_vfx_resources(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/procedural-vfx-composer.md", skill_text)
        self.assertIn("scripts/validate_vfx_spec.py", skill_text)

        generator_text = CANONICAL_GENERATOR.read_text(encoding="utf-8")
        self.assertIn('"rig-animation": {', generator_text)
        self.assertIn("cue-driven procedural VFX", generator_text)
        self.assertIn("references/procedural-vfx-composer.md", generator_text)
        self.assertIn("scripts/validate_vfx_spec.py", generator_text)

        catalog_text = CATALOG_GENERATOR.read_text(encoding="utf-8")
        self.assertIn("Rig, animate, compose, and validate procedural VFX", catalog_text)
        self.assertIn("validate vfx-project.json", catalog_text)

        start_text = START_SKILL.read_text(encoding="utf-8")
        self.assertIn(
            "Rigging, animation, or cue-driven procedural VFX", start_text
        )
        self.assertIn("`$ai-game-studio:rig-animation`", start_text)

    def test_plugin_listing_is_compact_contrasting_and_has_no_screenshots(self) -> None:
        manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        interface = manifest["interface"]
        subtitle = interface["shortDescription"]
        self.assertLessEqual(len(subtitle), 30)
        self.assertNotIn("screenshots", interface)
        brand_color = interface["brandColor"]
        self.assertRegex(brand_color, r"^#[0-9A-Fa-f]{6}$")
        contrast_against_white = (1.0 + 0.05) / (
            VALIDATOR.relative_luminance(brand_color) + 0.05
        )
        self.assertGreaterEqual(contrast_against_white, 2.0)

    def test_composer_svg_is_accessible_1280_by_640_xml(self) -> None:
        svg = ET.parse(COMPOSER_SVG).getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(svg.attrib["width"], "1280")
        self.assertEqual(svg.attrib["height"], "640")
        self.assertEqual(svg.attrib["viewBox"], "0 0 1280 640")
        self.assertEqual(svg.attrib["role"], "img")
        self.assertIsNotNone(svg.find("svg:title", namespace))
        self.assertIsNotNone(svg.find("svg:desc", namespace))

    def test_social_preview_is_1280_by_640_and_under_one_megabyte(self) -> None:
        payload = SOCIAL_PREVIEW.read_bytes()
        self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(payload[12:16], b"IHDR")
        self.assertEqual(int.from_bytes(payload[16:20], "big"), 1280)
        self.assertEqual(int.from_bytes(payload[20:24], "big"), 640)
        self.assertLess(len(payload), 1_000_000)

    def test_resources_exist_and_json_files_parse(self) -> None:
        for path in (REFERENCE, EXAMPLE, SCHEMA, SCRIPT):
            self.assertTrue(path.is_file(), path)
        example = load_example()
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(example["schemaVersion"], "1.0.0")
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(
            {"registries", "rendering", "editor"}.issubset(schema["required"])
        )
        cue_track = schema["$defs"]["cueTrack"]
        self.assertEqual(
            cue_track["properties"]["clip"]["$ref"], "#/$defs/nodeName"
        )
        backgrounds = schema["$defs"]["capture"]["properties"]["backgrounds"]
        self.assertEqual(backgrounds["minItems"], 3)
        self.assertEqual(backgrounds["maxItems"], 3)

    def test_shipped_example_passes_and_digest_is_stable(self) -> None:
        document = VALIDATOR.load_document(EXAMPLE)
        self.assertEqual(VALIDATOR.validate_document(document), [])
        first = VALIDATOR.canonical_digest(document)
        second = VALIDATOR.canonical_digest(load_example())
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertEqual(first, second)

    def test_manifest_pins_exact_geometry_tube_and_shader_registries(self) -> None:
        example = load_example()
        registries = example["registries"]
        self.assertEqual(
            registries["geometryGenerators"], list(VALIDATOR.GEOMETRY_GENERATORS)
        )
        self.assertEqual(len(registries["geometryGenerators"]), 10)
        self.assertEqual(registries["shaderBlocks"], list(VALIDATOR.SHADER_BLOCKS))
        self.assertEqual(len(registries["shaderBlocks"]), 29)
        tube = registries["transportTube"]
        self.assertEqual(tube["frameMethod"], "double-reflection")
        self.assertEqual(tube["modes"], list(VALIDATOR.TRANSPORT_MODES))
        self.assertTrue(tube["preallocated"])
        self.assertTrue(tube["dynamicDraw"])

    def test_manifest_pins_rendering_editor_and_beam_contracts(self) -> None:
        example = load_example()
        rendering = example["rendering"]
        self.assertFalse(rendering["postprocessing"])
        self.assertFalse(rendering["particleEngine"])
        self.assertTrue(rendering["layeredAdditiveGlow"])
        self.assertTrue(rendering["meshPooling"])
        self.assertEqual(rendering["sparks"], "instanced-mesh")
        self.assertEqual(rendering["debris"], "instanced-mesh")
        self.assertFalse(rendering["additiveDepthWrite"])
        self.assertEqual(
            rendering["computedTextureChannels"], list(VALIDATOR.TEXTURE_CHANNELS)
        )

        editor = example["editor"]
        self.assertTrue(editor["localOnly"])
        self.assertEqual(editor["panels"], list(VALIDATOR.EDITOR_PANELS))
        self.assertEqual(editor["history"], {"undo": True, "redo": True})
        self.assertEqual(
            editor["projectIo"], {"jsonImport": True, "jsonExport": True}
        )
        self.assertTrue(editor["deterministicCapture"])
        self.assertEqual(
            editor["accessibility"],
            {"keyboard": True, "reducedMotion": True, "pausable": True},
        )
        self.assertFalse(editor["network"])
        self.assertFalse(editor["telemetry"])

        beam_ids = {
            effect["id"]
            for effect in example["effects"]
            if effect["preset"] == "beam-bolt"
        }
        self.assertTrue(beam_ids)
        referenced = {
            cue["effectId"]
            for track in example["cueTracks"]
            for cue in track["cues"]
        }
        self.assertTrue(beam_ids.issubset(referenced))

    def test_example_is_data_only_and_contains_no_remote_or_media_values(self) -> None:
        serialized = "\n".join(all_strings(load_example())).lower()
        for forbidden in (
            "http://",
            "https://",
            "data:",
            "file:",
            "package.json",
            "node_modules",
            "cdn",
            ".ts",
            ".png",
            ".jpg",
            ".gif",
            ".mp4",
            ".webm",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_validator_rejects_registry_rendering_and_editor_drift(self) -> None:
        document = load_example()
        document["registries"]["geometryGenerators"].pop()
        document["registries"]["shaderBlocks"][0] = "custom-shader"
        document["rendering"]["postprocessing"] = True
        document["rendering"]["particleEngine"] = True
        document["editor"]["panels"].remove("shader-log")
        document["editor"]["network"] = True
        errors = VALIDATOR.validate_document(document)
        joined = "\n".join(errors)
        self.assertIn("$.registries.geometryGenerators", joined)
        self.assertIn("$.registries.shaderBlocks", joined)
        self.assertIn("$.rendering.postprocessing", joined)
        self.assertIn("$.rendering.particleEngine", joined)
        self.assertIn("$.editor.panels", joined)
        self.assertIn("$.editor.network", joined)

    def test_validator_requires_a_beam_bolt_and_additive_geometry(self) -> None:
        document = load_example()
        document["effects"] = [
            effect for effect in document["effects"] if effect["preset"] != "beam-bolt"
        ]
        document["cueTracks"][0]["cues"] = [document["cueTracks"][0]["cues"][0]]
        for layer in document["effects"][0]["layers"]:
            layer["blend"] = "normal"
        errors = "\n".join(VALIDATOR.validate_document(document))
        self.assertIn("must include at least one beam-bolt effect", errors)
        self.assertIn("must include an additive geometry layer", errors)

    def test_validator_rejects_palette_value_collapse_without_duplicate_hex(self) -> None:
        document = load_example()
        document["palettes"]["steel"] = {
            "core": "#FFFFFF",
            "body": "#FEFEFE",
            "edge": "#FDFDFD",
            "ink": "#FCFCFC",
            "ash": "#FBFBFB",
        }
        errors = "\n".join(VALIDATOR.validate_document(document))
        self.assertIn("relative luminance must descend", errors)

    def test_validator_rejects_bad_cues_and_cross_budget_overflow(self) -> None:
        document = load_example()
        cue = document["cueTracks"][1]["cues"][0]
        cue["normalizedWindow"] = [0.8, 0.2]
        cue["effectId"] = "missing-effect"
        cue["socket"] = "missing-socket"
        document["budgets"]["maxLayersPerEffect"] = 1
        document["effects"][0]["budgets"]["maxVertices"] = (
            document["budgets"]["maxVertices"] + 1
        )
        errors = "\n".join(VALIDATOR.validate_document(document))
        self.assertIn("start must be less than end", errors)
        self.assertIn("references an unknown effect", errors)
        self.assertIn("references an unknown rig socket", errors)
        self.assertIn("global limit is 1", errors)
        self.assertIn("exceeds the global maxVertices budget", errors)

    def test_validator_rejects_uri_and_executable_fields(self) -> None:
        document = load_example()
        document["threeRevision"] = "project-provided"
        document["style"]["silhouette"] = "javascript:alert(1)"
        document["effects"][0]["shaderSource"] = "void main() {}"
        errors = "\n".join(VALIDATOR.validate_document(document))
        self.assertIn("must be a concrete rNNN", errors)
        self.assertIn("URI values are forbidden", errors)
        self.assertIn("executable or external field is forbidden", errors)
        self.assertIn("unknown field 'shaderSource'", errors)

        document = load_example()
        document["style"]["silhouette"] = "../outside/style"
        errors = "\n".join(VALIDATOR.validate_document(document))
        self.assertIn("absolute paths and parent traversal are forbidden", errors)

    def test_clip_name_contract_and_capture_background_coverage(self) -> None:
        document = load_example()
        document["cueTracks"][0]["clip"] = "Attack.Combo.01"
        self.assertEqual(VALIDATOR.validate_document(document), [])

        document["capture"]["backgrounds"] = ["dark"]
        errors = "\n".join(VALIDATOR.validate_document(document))
        self.assertIn("between 3 and 3 items", errors)
        self.assertIn("must include", errors)

    def test_loader_rejects_duplicate_keys_non_object_root_and_oversize(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-vfx-validator-") as temporary:
            root = Path(temporary)
            duplicate = root / "duplicate.json"
            duplicate.write_text(
                '{"schemaVersion":"1.0.0","schemaVersion":"1.0.0"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.SpecReadError, "duplicate object key"):
                VALIDATOR.load_document(duplicate)

            array_root = root / "array.json"
            array_root.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(VALIDATOR.SpecReadError, "root must be an object"):
                VALIDATOR.load_document(array_root)

            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (VALIDATOR.MAX_FILE_BYTES + 1))
            with self.assertRaisesRegex(VALIDATOR.SpecReadError, "maximum"):
                VALIDATOR.load_document(oversized)

    def test_cli_reports_digest_and_does_not_mutate_manifest_or_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-vfx-cli-") as temporary:
            root = Path(temporary)
            manifest = root / "vfx-project.json"
            manifest.write_bytes(EXAMPLE.read_bytes())
            before_bytes = manifest.read_bytes()
            before_names = sorted(path.name for path in root.iterdir())
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(manifest), "--json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(set(payload), {"valid", "digest", "errors"})
            self.assertTrue(payload["valid"])
            self.assertRegex(payload["digest"], r"^[0-9a-f]{64}$")
            self.assertEqual(payload["errors"], [])
            self.assertEqual(manifest.read_bytes(), before_bytes)
            self.assertEqual(sorted(path.name for path in root.iterdir()), before_names)

    def test_cli_rejects_hostile_numbers_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-vfx-number-") as temporary:
            root = Path(temporary)
            cases = {
                "huge-integer.json": '{"seed":' + ("9" * 5000) + "}",
                "overflow-float.json": '{"seed":1e9999}',
            }
            for name, payload in cases.items():
                with self.subTest(name=name):
                    manifest = root / name
                    manifest.write_text(payload, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), str(manifest), "--json"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    self.assertEqual(result.returncode, 1)
                    response = json.loads(result.stdout)
                    self.assertFalse(response["valid"])
                    self.assertTrue(response["errors"])
                    self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_validator_source_is_stdlib_only_and_has_no_write_or_network_surface(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        self.assertTrue(
            imported.issubset(
                {
                    "__future__",
                    "argparse",
                    "hashlib",
                    "json",
                    "math",
                    "pathlib",
                    "re",
                    "sys",
                    "typing",
                }
            ),
            imported,
        )
        for forbidden in (
            "subprocess",
            "urllib",
            "requests",
            "urlopen",
            "write_text",
            "write_bytes",
            "open(\"w",
            "open('w",
        ):
            self.assertNotIn(forbidden, source)

    def test_schema_uses_only_local_refs(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        refs: list[str] = []
        stack: list[object] = [schema]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                if "$ref" in value:
                    refs.append(value["$ref"])
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
        self.assertTrue(refs)
        self.assertTrue(all(ref.startswith("#/") for ref in refs), refs)


if __name__ == "__main__":
    unittest.main()
