from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_ROOT = ROOT / "plugins" / "ai-game-studio" / "catalog"
RECIPE_ROOT = ROOT / "plugins" / "ai-game-studio" / "recipes"
EXPECTED_SOURCE_SHA256 = "cc348551c912736f3d5f6c3f275ee5b14e5e7e0154159ad5e711abe2011275e9"
EXPECTED_SCHEMA_PREFIX = "https://frabcd.github.io/codex-ai-game-studio/schemas/"
BLOCKING_LICENSE_STATES = {"unknown", "custom", "restricted", "prohibited"}
SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog_path = CATALOG_ROOT / "catalog.json"
        cls.catalog = load_json(cls.catalog_path)
        cls.records = cls.catalog["records"]
        cls.snapshot = load_json(CATALOG_ROOT / "snapshots" / "github-2026-07-30.json")

    def test_exactly_163_unique_repository_records(self) -> None:
        self.assertEqual(163, len(self.records))
        self.assertEqual(163, len({record["id"] for record in self.records}))
        canonical_urls = [record["repository"]["canonical_url"].casefold() for record in self.records]
        self.assertEqual(163, len(set(canonical_urls)))
        self.assertTrue(all(url.startswith("https://github.com/") for url in canonical_urls))

    def test_source_provenance_is_fixed_and_reproducible(self) -> None:
        provenance = self.catalog["provenance"]
        self.assertEqual(EXPECTED_SOURCE_SHA256, provenance["source_sha256"])
        self.assertEqual("2026-07-30", provenance["snapshot_date"])
        self.assertEqual(163, provenance["record_count"])
        self.assertEqual(provenance, load_json(CATALOG_ROOT / "provenance.json"))
        self.assertFalse(Path(provenance["source_path"]).is_absolute())

    def test_every_record_has_selection_and_safety_fields(self) -> None:
        required = {
            "id", "repository", "summary", "kind", "maturity", "curation",
            "capabilities", "engines", "workflows", "platform_support",
            "requirements", "authentication", "licenses", "security", "install",
            "verification", "documentation_urls",
        }
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertTrue(required <= record.keys())
                self.assertTrue(record["capabilities"])
                self.assertTrue(record["workflows"])
                self.assertTrue(record["curation"]["contexts"])
                self.assertIn("operating_systems", record["platform_support"])
                self.assertIn("architectures", record["platform_support"])
                self.assertIn("gpu", record["requirements"])
                self.assertIn("backends", record["requirements"]["gpu"])
                self.assertIn("minimum_vram_gb", record["requirements"]["gpu"])
                self.assertIn("permissions", record["security"])
                self.assertIn("pinned_source", record["install"])
                self.assertIn("date", record["verification"])

    def test_catalog_is_metadata_only_and_offline_usable(self) -> None:
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertEqual("external-metadata-only", record["install"]["mode"])
                self.assertIs(record["install"]["bundled"], False)
                self.assertEqual("unresolved", record["install"]["pinned_source"]["pin_status"])
                self.assertNotIn("command", record["install"])
                self.assertNotIn("download", record["install"])

    def test_unknown_or_custom_licenses_block_commercial_recommendation(self) -> None:
        scopes = ("code", "model_weights", "dataset", "generated_output")
        for record in self.records:
            statuses = {record["licenses"][scope]["status"] for scope in scopes}
            if statuses & BLOCKING_LICENSE_STATES:
                self.assertEqual("blocked", record["licenses"]["commercial_use"]["status"], record["id"])

    def test_auth_metadata_contains_names_only_and_no_secret_values(self) -> None:
        serialized = self.catalog_path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            self.assertIsNone(pattern.search(serialized), pattern.pattern)
        for record in self.records:
            auth = record["authentication"]
            self.assertNotIn("values", auth)
            self.assertNotIn("secrets", auth)
            for name in auth["environment_variables"]:
                self.assertRegex(name, r"^[A-Z][A-Z0-9_]*$")

    def test_volatile_metadata_is_not_in_stable_records(self) -> None:
        volatile = {"stars", "forks", "watchers", "archived", "latest_release", "last_activity"}
        for record in self.records:
            self.assertFalse(volatile & record.keys(), record["id"])
        self.assertEqual(163, len(self.snapshot["records"]))
        self.assertEqual({record["id"] for record in self.records}, {record["id"] for record in self.snapshot["records"]})

    def test_schema_documents_identify_json_schema_2020_12(self) -> None:
        schema_paths = [
            CATALOG_ROOT / "schemas" / "catalog.schema.json",
            CATALOG_ROOT / "schemas" / "catalog-snapshot.schema.json",
            RECIPE_ROOT / "schema" / "recipe.schema.json",
        ]
        for path in schema_paths:
            with self.subTest(path=path.name):
                schema = load_json(path)
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertTrue(schema["$id"].startswith(EXPECTED_SCHEMA_PREFIX))
        self.assertEqual(f"{EXPECTED_SCHEMA_PREFIX}catalog.schema.json", self.catalog["$schema"])
        self.assertEqual(f"{EXPECTED_SCHEMA_PREFIX}catalog-snapshot.schema.json", self.snapshot["$schema"])

    def test_respawnstack_stays_outside_repository_counts(self) -> None:
        landscape_path = ROOT / "sources" / "AI_GAME_GENERATION_GITHUB_LANDSCAPE.md"
        data = landscape_path.read_bytes()
        self.assertEqual(EXPECTED_SOURCE_SHA256, hashlib.sha256(data).hexdigest())
        text = data.decode("utf-8")
        section_1 = text.split("## 1. Master indexes", 1)[1].split("## 2. ", 1)[0]
        external = text.split("## External references — pricing and licensing", 1)[1]
        bullet = (
            "[RespawnStack](https://respawnstack.com/) — **External reference**. "
            "Free-to-read directory of AI game-tool pricing, commercial-use terms, and output ownership, "
            "with dated vendor quotes where verified and explicit unverified entries. "
            "Advertising/affiliate-supported; recheck original vendor terms before commercial use."
        )
        self.assertNotIn("respawnstack", section_1.casefold())
        self.assertIn(bullet, external)
        self.assertIn("outside repository counts and outside the installable catalog", text)
        serialized = json.dumps(self.catalog).casefold()
        self.assertNotIn("respawnstack", serialized)
        self.assertTrue(all(url.startswith("https://github.com/") for url in (
            record["repository"]["canonical_url"] for record in self.records
        )))

    def test_external_reference_section_cannot_add_catalog_records(self) -> None:
        generator_path = ROOT / "plugins" / "ai-game-studio" / "catalog" / "tools" / "generate_catalog.py"
        spec = importlib.util.spec_from_file_location("generate_catalog_under_test", generator_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixture = "\n".join((
            "## 1. Master indexes, surveys, and agent skills",
            "",
            "- [example/kept](https://github.com/example/kept) — **Index**. Kept repository.",
            "",
            "## External references — pricing and licensing",
            "",
            "- [RespawnStack](https://respawnstack.com/) — **External reference**. Standalone website.",
            "- [example/excluded](https://github.com/example/excluded) — **Index**. Must stay out of the catalog.",
            "",
        ))
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "landscape.md"
            source.write_text(fixture, encoding="utf-8")
            module.EXPECTED_SHA256 = hashlib.sha256(source.read_bytes()).hexdigest()
            records, _stars = module.parse_source(source)
        names = {record["repository"]["full_name"] for record in records}
        self.assertEqual({"example/kept"}, names)


class RecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = load_json(RECIPE_ROOT / "index.json")
        cls.recipes = [load_json(RECIPE_ROOT / entry["path"]) for entry in cls.index["recipes"]]

    def test_twelve_unique_production_recipes_are_offline(self) -> None:
        self.assertEqual(12, self.index["recipe_count"])
        self.assertEqual(12, len(self.recipes))
        self.assertEqual(12, len({recipe["id"] for recipe in self.recipes}))

    def test_recipe_stage_and_quality_contract(self) -> None:
        required_gate_ids = {
            "rights", "technical-format", "visual-temporal", "runtime-budget",
            "playability", "regression-evidence", "human-approval",
        }
        for recipe in self.recipes:
            with self.subTest(recipe=recipe["id"]):
                stages = recipe["ordered_stages"]
                self.assertEqual(list(range(1, len(stages) + 1)), [stage["order"] for stage in stages])
                self.assertTrue(recipe["required_capabilities"])
                self.assertTrue(recipe["expected_artifacts"])
                self.assertTrue(recipe["fallbacks"])
                self.assertEqual("plan-confirmed-digest-before-apply", recipe["mutation_policy"])
                self.assertTrue(required_gate_ids <= {gate["id"] for gate in recipe["quality_gates"]})
                self.assertIn("human-approval.json", recipe["provenance_outputs"])

    def test_every_recipe_capability_can_route_to_offline_catalog_entries(self) -> None:
        catalog = load_json(CATALOG_ROOT / "catalog.json")
        available = {capability for record in catalog["records"] for capability in record["capabilities"]}
        required = {capability for recipe in self.recipes for capability in recipe["required_capabilities"]}
        self.assertFalse(required - available, f"unroutable recipe capabilities: {sorted(required - available)}")

    def test_voice_recipe_requires_consent_and_blocks_unlicensed_cloning(self) -> None:
        recipe = next(recipe for recipe in self.recipes if recipe["id"] == "npc-audio-generation")
        text = json.dumps(recipe).lower()
        self.assertIn("consent", text)
        self.assertIn("voice cloning without consent block", text)


if __name__ == "__main__":
    unittest.main()
