#!/usr/bin/env python3
"""Validate the Codex AI Game Studio repository without third-party packages.

The official Codex validators remain authoritative for individual plugin and
skill packaging.  This validator adds repository-wide invariants that those
tools intentionally do not cover: parity counts, catalog integrity, safe local
references, immutable executable dependencies, and release hygiene.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import unquote


PARITY_SKILLS = frozenset(
    """adopt architecture-decision architecture-review art-bible asset-audit
    asset-spec balance-check brainstorm bug-report bug-triage changelog
    code-review consistency-check content-audit create-architecture
    create-control-manifest create-epics create-stories day-one-patch
    design-review design-system dev-story estimate gate-check help hotfix
    launch-checklist localize map-systems milestone-review onboard patch-notes
    perf-profile playtest-report project-stage-detect propagate-design-change
    prototype qa-plan quick-design regression-suite release-checklist
    retrospective reverse-document review-all-gdds scope-check security-audit
    setup-engine skill-improve skill-test smoke-check soak-test sprint-plan
    sprint-status start story-done story-readiness team-audio team-combat
    team-level team-live-ops team-narrative team-polish team-qa team-release
    team-ui tech-debt test-evidence-review test-flakiness test-helpers
    test-setup ux-design ux-review vertical-slice""".split()
)

NATIVE_SKILLS = frozenset(
    """toolchain-doctor tool-discover prompt-to-game sprite-generate
    asset-3d-generate material-texture-generate rig-animation world-generate
    npc-audio-generate engine-automation visual-qa quality-enhance""".split()
)

ROLE_NAMES = frozenset(
    """accessibility-specialist ai-programmer analytics-engineer art-director
    audio-director community-manager creative-director devops-engineer
    economy-designer engine-programmer game-designer gameplay-programmer
    godot-csharp-specialist godot-gdextension-specialist
    godot-gdscript-specialist godot-shader-specialist godot-specialist
    lead-programmer level-designer live-ops-designer localization-lead
    narrative-director network-programmer performance-analyst producer
    prototyper qa-lead qa-tester release-manager security-engineer
    sound-designer systems-designer technical-artist technical-director
    tools-programmer ue-blueprint-specialist ue-gas-specialist
    ue-replication-specialist ue-umg-specialist ui-programmer
    unity-addressables-specialist unity-dots-specialist unity-shader-specialist
    unity-specialist unity-ui-specialist unreal-specialist ux-designer
    world-builder writer""".split()
)

HOOK_BEHAVIORS = frozenset(
    """detect-gaps log-agent log-agent-stop notify post-compact pre-compact
    session-start session-stop validate-assets validate-commit validate-push
    validate-skill-change""".split()
)

RULE_NAMES = frozenset(
    """ai-code data-files design-docs engine-code gameplay-code narrative
    network-code prototype-code shader-code test-standards ui-code""".split()
)

EXPECTED_PLUGINS = frozenset(
    {
        "ai-game-studio",
        "ai-game-studio-automation",
        "ai-game-studio-blender",
        "ai-game-studio-godot",
        "ai-game-studio-img2threejs",
        "ai-game-studio-macos",
        "ai-game-studio-pixel",
        "ai-game-studio-unity",
        "ai-game-studio-unreal",
        "ai-game-studio-windows",
    }
)
EXPECTED_PLUGIN_SKILLS = {
    "ai-game-studio": PARITY_SKILLS | NATIVE_SKILLS,
    "ai-game-studio-automation": frozenset({"migrate-claude", "setup-automation"}),
    "ai-game-studio-blender": frozenset({"setup-blender"}),
    "ai-game-studio-godot": frozenset({"setup-godot"}),
    "ai-game-studio-img2threejs": frozenset({"img2threejs"}),
    "ai-game-studio-macos": frozenset({"setup-macos-edition"}),
    "ai-game-studio-pixel": frozenset({"setup-pixel"}),
    "ai-game-studio-unity": frozenset({"setup-unity"}),
    "ai-game-studio-unreal": frozenset({"setup-unreal"}),
    "ai-game-studio-windows": frozenset({"setup-windows-edition"}),
}
PLUGIN_LICENSES = {
    name: "Apache-2.0" if name == "ai-game-studio-img2threejs" else "MIT"
    for name in EXPECTED_PLUGINS
}
EXPECTED_EDITIONS = {
    "windows": ("Windows", "ai-game-studio-windows"),
    "macos": ("Darwin", "ai-game-studio-macos"),
}

EXPECTED_HOOK_EVENTS = frozenset(
    {
        "SessionStart",
        "SubagentStart",
        "SubagentStop",
        "PreCompact",
        "PostCompact",
        "PreToolUse",
        "PostToolUse",
        "Stop",
        "SessionEnd",
    }
)

PINNED_UPSTREAM_COMMIT = "984023ddac0d5e27624f2baacde6105e45de375f"
PINNED_IMG2THREEJS_COMMIT = "9a8ecf129a58c1b557a1f03f7727f6295672cd51"
RELEASE_VERSION = "1.1.1"
HEX_SHA = re.compile(r"^[0-9a-f]{40}$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
ACTION_USE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

UNSAFE_CODE_PATTERNS = (
    (re.compile(r"\bshell\s*=\s*True\b"), "Python subprocess shell" + "=True"),
    (re.compile(r"\bos\.system\s*\("), "Python os.system"),
    (re.compile(r"\bInvoke" + r"-Expression\b", re.IGNORECASE), "PowerShell Invoke" + "-Expression"),
    (re.compile(r"\b(?:eval|exec)\s*\("), "dynamic eval/exec"),
    (re.compile(r"\b(?:cmd(?:\.exe)?\s+/c|sh\s+-c|bash\s+-c)\b", re.IGNORECASE), "nested shell command"),
)

TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".ps1",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Problem:
    code: str
    path: str
    message: str

    def render(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"{self.code}{location}: {self.message}"


class Validator:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.problems: list[Problem] = []

    def error(self, code: str, path: Path | str, message: str) -> None:
        if isinstance(path, Path):
            try:
                shown = path.resolve().relative_to(self.root).as_posix()
            except ValueError:
                shown = str(path)
        else:
            shown = path
        self.problems.append(Problem(code, shown, message))

    def load_json(self, path: Path) -> object | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self.error("malformed-json", path, str(exc))
            return None

    def run(self) -> list[Problem]:
        self.validate_configs()
        self.validate_plugins()
        self.validate_skills()
        self.validate_parity()
        self.validate_catalog()
        self.validate_packs()
        self.validate_editions()
        self.validate_img2threejs()
        self.validate_hooks()
        self.validate_markdown_links()
        self.validate_workflows()
        self.validate_source_safety()
        self.validate_release_layout()
        return sorted(self.problems, key=lambda item: (item.path, item.code, item.message))

    def validate_configs(self) -> None:
        ignored = {".git", ".official", "dist", "__pycache__", ".pytest_cache"}
        for path in self.root.rglob("*"):
            if not path.is_file() or any(part in ignored for part in path.parts):
                continue
            if path.suffix == ".json":
                self.load_json(path)
            elif path.suffix == ".toml":
                try:
                    tomllib.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
                    self.error("malformed-toml", path, str(exc))

    def validate_plugins(self) -> None:
        plugins_root = self.root / "plugins"
        plugin_dirs = {path.name: path for path in plugins_root.iterdir() if path.is_dir()} if plugins_root.is_dir() else {}
        if set(plugin_dirs) != EXPECTED_PLUGINS:
            self.error(
                "plugin-set",
                plugins_root,
                f"expected {sorted(EXPECTED_PLUGINS)}, found {sorted(plugin_dirs)}",
            )

        for name, plugin_dir in sorted(plugin_dirs.items()):
            manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
            manifest = self.load_json(manifest_path) if manifest_path.is_file() else None
            if not isinstance(manifest, dict):
                if not manifest_path.is_file():
                    self.error("plugin-manifest", manifest_path, "missing plugin manifest")
                continue
            if manifest.get("name") != name:
                self.error("plugin-name", manifest_path, f"manifest name must be {name!r}")
            if not SEMVER.fullmatch(str(manifest.get("version", ""))):
                self.error("plugin-version", manifest_path, "version must be strict semantic versioning")
            elif manifest.get("version") != RELEASE_VERSION:
                self.error(
                    "plugin-version",
                    manifest_path,
                    f"manifest version must be the release version {RELEASE_VERSION}",
                )
            expected_license = PLUGIN_LICENSES.get(name)
            if manifest.get("license") != expected_license:
                self.error(
                    "plugin-license",
                    manifest_path,
                    f"license must be {expected_license}",
                )
            author = manifest.get("author")
            if not isinstance(author, dict) or author.get("name") != "frabcd":
                self.error("plugin-author", manifest_path, "author.name must be frabcd")
            interface = manifest.get("interface")
            if not isinstance(interface, dict):
                self.error("plugin-interface", manifest_path, "interface must be an object")
                continue
            for key in ("displayName", "shortDescription", "developerName", "category"):
                if not isinstance(interface.get(key), str) or not interface[key].strip():
                    self.error("plugin-interface", manifest_path, f"interface.{key} is required")
            default_prompt = interface.get("defaultPrompt")
            if not isinstance(default_prompt, str) or not default_prompt.strip():
                self.error("plugin-interface", manifest_path, "interface.defaultPrompt is required")
            elif len(default_prompt) > 128:
                self.error(
                    "plugin-interface",
                    manifest_path,
                    f"interface.defaultPrompt must be at most 128 characters, found {len(default_prompt)}",
                )
            self._validate_manifest_assets(plugin_dir, manifest_path, manifest)

        marketplace_path = self.root / ".agents" / "plugins" / "marketplace.json"
        marketplace = self.load_json(marketplace_path) if marketplace_path.is_file() else None
        if not isinstance(marketplace, dict):
            self.error("marketplace", marketplace_path, "marketplace must be a JSON object")
            return
        if marketplace.get("name") != "frabcd-ai-game-studio":
            self.error("marketplace-name", marketplace_path, "marketplace name must be frabcd-ai-game-studio")
        entries = marketplace.get("plugins")
        if not isinstance(entries, list):
            self.error("marketplace", marketplace_path, "plugins must be an array")
            return
        names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
        if len(names) != len(set(names)):
            self.error("marketplace-duplicate", marketplace_path, "plugin names must be unique")
        if set(names) != EXPECTED_PLUGINS:
            self.error("marketplace-set", marketplace_path, f"expected exactly {sorted(EXPECTED_PLUGINS)}")
        for entry in entries:
            if not isinstance(entry, dict):
                self.error("marketplace-entry", marketplace_path, "every plugin entry must be an object")
                continue
            source = entry.get("source")
            if not isinstance(source, dict) or source.get("source") != "local":
                self.error("marketplace-source", marketplace_path, f"{entry.get('name')}: source must be local")
                continue
            rel = source.get("path")
            resolved = safe_resolve(self.root, rel) if isinstance(rel, str) else None
            if resolved is None or not resolved.is_dir():
                self.error("marketplace-path", marketplace_path, f"{entry.get('name')}: invalid or escaping source path {rel!r}")

    def _validate_manifest_assets(self, plugin_dir: Path, manifest_path: Path, manifest: dict[str, object]) -> None:
        local_fields: list[tuple[str, object]] = [
            ("skills", manifest.get("skills")),
            ("mcpServers", manifest.get("mcpServers")),
            ("apps", manifest.get("apps")),
        ]
        interface = manifest.get("interface")
        if isinstance(interface, dict):
            for key in ("composerIcon", "logo", "logoDark"):
                local_fields.append((f"interface.{key}", interface.get(key)))
            screenshots = interface.get("screenshots", [])
            if isinstance(screenshots, list):
                local_fields.extend(("interface.screenshots", item) for item in screenshots)
            elif screenshots is not None:
                self.error("plugin-asset", manifest_path, "interface.screenshots must be an array")

        for key, value in local_fields:
            if value is None:
                continue
            if not isinstance(value, str):
                self.error("plugin-path", manifest_path, f"{key} must be a string path")
                continue
            resolved = safe_resolve(plugin_dir, value)
            if resolved is None or not resolved.exists():
                self.error("plugin-path", manifest_path, f"{key} is missing or escapes plugin: {value!r}")

    def validate_skills(self) -> None:
        total = 0
        for plugin_name, expected in EXPECTED_PLUGIN_SKILLS.items():
            skills_root = self.root / "plugins" / plugin_name / "skills"
            found: dict[str, Path] = {
                path.parent.name: path for path in skills_root.glob("*/SKILL.md")
            }
            total += len(found)
            if set(found) != expected:
                self.error(
                    "skill-set",
                    skills_root,
                    f"missing={sorted(expected - set(found))}, extra={sorted(set(found) - expected)}",
                )
            for directory_name, skill_path in sorted(found.items()):
                frontmatter, issue = parse_frontmatter(skill_path)
                if issue:
                    self.error("skill-frontmatter", skill_path, issue)
                    continue
                if set(frontmatter) != {"name", "description"}:
                    self.error(
                        "skill-frontmatter",
                        skill_path,
                        f"only name and description are allowed, found {sorted(frontmatter)}",
                    )
                if frontmatter.get("name") != directory_name:
                    self.error("skill-name", skill_path, f"name must match directory {directory_name!r}")
                if not frontmatter.get("description", "").strip():
                    self.error("skill-description", skill_path, "description must not be empty")
                yaml_path = skill_path.parent / "agents" / "openai.yaml"
                if not yaml_path.is_file():
                    self.error("skill-metadata", yaml_path, "missing agents/openai.yaml")
                else:
                    text = yaml_path.read_text(encoding="utf-8")
                    expected_invocation = f"${plugin_name}:{directory_name}"
                    if "default_prompt:" not in text or expected_invocation not in text:
                        self.error(
                            "skill-prompt",
                            yaml_path,
                            f"default_prompt must mention {expected_invocation}",
                        )
        if total != 95:
            self.error("skill-count", self.root / "plugins", f"expected 95 bundled skills, found {total}")

    def validate_parity(self) -> None:
        ledger_path = self.root / "parity" / "ledger.json"
        ledger = self.load_json(ledger_path) if ledger_path.is_file() else None
        if not isinstance(ledger, dict):
            self.error("parity-ledger", ledger_path, "missing parity ledger")
            return
        source = ledger.get("source")
        if not isinstance(source, dict) or source.get("commit") != PINNED_UPSTREAM_COMMIT:
            self.error("parity-source", ledger_path, f"source commit must be {PINNED_UPSTREAM_COMMIT}")
        entries = ledger.get("entries")
        if not isinstance(entries, list):
            self.error("parity-ledger", ledger_path, "entries must be an array")
            return
        expected_sets = {
            "skill": PARITY_SKILLS,
            "role": ROLE_NAMES,
            "hook-behavior": HOOK_BEHAVIORS,
            "rule": RULE_NAMES,
        }
        by_kind: dict[str, list[dict[str, object]]] = {}
        seen_pairs: set[tuple[object, object]] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                self.error("parity-entry", ledger_path, "each entry must be an object")
                continue
            pair = (entry.get("kind"), entry.get("id"))
            if pair in seen_pairs:
                self.error("parity-duplicate", ledger_path, f"duplicate {pair}")
            seen_pairs.add(pair)
            by_kind.setdefault(str(entry.get("kind")), []).append(entry)
            if entry.get("status") not in {"ported", "replaced", "not-applicable"}:
                self.error("parity-status", ledger_path, f"{pair}: invalid status")
            if entry.get("source_commit") != PINNED_UPSTREAM_COMMIT:
                self.error("parity-source", ledger_path, f"{pair}: incorrect source_commit")
            for required in ("source_path", "destination", "tests"):
                if not entry.get(required):
                    self.error("parity-entry", ledger_path, f"{pair}: missing {required}")
            destination = entry.get("destination")
            if isinstance(destination, str) and destination != "not-applicable":
                resolved = safe_resolve(self.root, destination)
                if resolved is None or not resolved.exists():
                    self.error("parity-destination", ledger_path, f"{pair}: missing or escaping destination {destination!r}")

        for kind, expected in expected_sets.items():
            found = {str(item.get("id")) for item in by_kind.get(kind, [])}
            if found != expected:
                self.error("parity-set", ledger_path, f"{kind}: missing={sorted(expected-found)}, extra={sorted(found-expected)}")
        if len(by_kind.get("template", [])) != 40:
            self.error("template-count", ledger_path, f"expected 40 template ledger entries, found {len(by_kind.get('template', []))}")

        agents_dir = self.root / "plugins" / "ai-game-studio-automation" / "templates" / "agents"
        actual_roles = {path.stem for path in agents_dir.glob("*.toml") if path.name != "manifest.toml"}
        if actual_roles != ROLE_NAMES:
            self.error("role-set", agents_dir, f"missing={sorted(ROLE_NAMES-actual_roles)}, extra={sorted(actual_roles-ROLE_NAMES)}")
        rules_dir = self.root / "plugins" / "ai-game-studio-automation" / "templates" / "rules"
        actual_rules = {path.stem for path in rules_dir.glob("*.md")}
        if actual_rules != RULE_NAMES:
            self.error("rule-set", rules_dir, f"missing={sorted(RULE_NAMES-actual_rules)}, extra={sorted(actual_rules-RULE_NAMES)}")
        templates_dir = self.root / "plugins" / "ai-game-studio-automation" / "templates" / "upstream"
        actual_templates = list(templates_dir.rglob("*.md"))
        if len(actual_templates) != 40:
            self.error("template-count", templates_dir, f"expected 40 Markdown templates, found {len(actual_templates)}")

    def validate_catalog(self) -> None:
        catalog_path = self.root / "plugins" / "ai-game-studio" / "catalog" / "catalog.json"
        catalog = self.load_json(catalog_path) if catalog_path.is_file() else None
        if not isinstance(catalog, dict):
            self.error("catalog", catalog_path, "catalog must be an object")
            return
        records = catalog.get("records")
        if not isinstance(records, list):
            self.error("catalog", catalog_path, "records must be an array")
            return
        if len(records) != 163:
            self.error("catalog-count", catalog_path, f"expected 163 records, found {len(records)}")
        ids: list[object] = []
        urls: list[object] = []
        required = {
            "id",
            "repository",
            "summary",
            "kind",
            "maturity",
            "capabilities",
            "engines",
            "workflows",
        }
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                self.error("catalog-record", catalog_path, f"record {index} must be an object")
                continue
            missing = required - record.keys()
            if missing:
                self.error("catalog-record", catalog_path, f"record {index} missing {sorted(missing)}")
            ids.append(record.get("id"))
            repo = record.get("repository")
            url = repo.get("canonical_url") if isinstance(repo, dict) else None
            urls.append(url)
            if not isinstance(url, str) or not url.startswith("https://github.com/"):
                self.error("catalog-url", catalog_path, f"record {index} has invalid canonical URL")
        if len(ids) != len(set(ids)):
            self.error("catalog-duplicate-id", catalog_path, "catalog IDs must be unique")
        if len(urls) != len(set(urls)):
            self.error("catalog-duplicate-url", catalog_path, "canonical repository URLs must be unique")

    def validate_packs(self) -> None:
        expected = {"unity", "godot", "unreal", "blender", "pixel"}
        descriptors: dict[str, tuple[Path, dict[str, object]]] = {}
        for path in sorted((self.root / "plugins").glob("ai-game-studio-*/packs/*.json")):
            payload = self.load_json(path)
            if not isinstance(payload, dict):
                continue
            pack_id = payload.get("id")
            if not isinstance(pack_id, str):
                self.error("pack-id", path, "descriptor id must be a string")
                continue
            if pack_id in descriptors:
                self.error("pack-duplicate", path, f"duplicate pack ID {pack_id!r}")
            descriptors[pack_id] = (path, payload)
        if set(descriptors) != expected:
            self.error("pack-set", self.root / "plugins", f"expected {sorted(expected)}, found {sorted(descriptors)}")
        required_lists = (
            "supported_os",
            "supported_architectures",
            "command_arguments",
            "conflicts",
            "permissions",
            "health_checks",
            "uninstall",
            "rollback",
        )
        for pack_id, (path, descriptor) in sorted(descriptors.items()):
            for key in ("plugin", "host_application", "version", "upstream", "activation", "adapter"):
                if key not in descriptor:
                    self.error("pack-field", path, f"missing {key}")
            for key in required_lists:
                value = descriptor.get(key)
                if not isinstance(value, list) or not value:
                    self.error("pack-field", path, f"{key} must be a non-empty array")
            upstream = descriptor.get("upstream")
            if not isinstance(upstream, dict):
                self.error("pack-upstream", path, "upstream must be an object")
            else:
                if not HEX_SHA.fullmatch(str(upstream.get("ref", ""))):
                    self.error("pack-unpinned", path, "upstream.ref must be a full 40-character commit SHA")
                if not str(upstream.get("url", "")).startswith("https://github.com/"):
                    self.error("pack-upstream", path, "upstream.url must be a canonical HTTPS GitHub URL")
                if not upstream.get("license"):
                    self.error("pack-license", path, "upstream.license is required")
            for alternative in descriptor.get("alternatives", []):
                file_only = isinstance(alternative, dict) and alternative.get("kind") == "non-mcp-editor"
                if not file_only and (not isinstance(alternative, dict) or not HEX_SHA.fullmatch(str(alternative.get("ref", "")))):
                    self.error("pack-unpinned", path, "every alternative must use a full 40-character commit SHA")
                if isinstance(alternative, dict) and alternative.get("active") is not False:
                    self.error("pack-conflict", path, "alternatives must remain inactive until confirmed substitution")
            activation = descriptor.get("activation")
            if not isinstance(activation, dict) or activation.get("mode") != "confirmed-transaction-only":
                self.error("pack-confirmation", path, "activation.mode must be confirmed-transaction-only")
            if not isinstance(activation, dict) or activation.get("single_server_per_host") is not True:
                self.error("pack-conflict", path, "activation must enforce one server per host")
            adapter = descriptor.get("adapter")
            if not isinstance(adapter, dict) or adapter.get("shell") is not False:
                self.error("pack-command", path, "adapter.shell must be false")
            if not isinstance(adapter, dict) or adapter.get("external_executable_sha256_required") is not True:
                self.error("pack-pin", path, "external executable SHA-256 must be required")
            launcher = adapter.get("launcher") if isinstance(adapter, dict) else None
            launcher_path = safe_resolve(path.parents[1], launcher)
            if launcher_path is None or not launcher_path.is_file():
                self.error("pack-path", path, f"adapter launcher is missing or escapes the plugin: {launcher!r}")
            for download in descriptor.get("downloads", []):
                if not isinstance(download, dict) or download.get("automatic") is not False:
                    self.error("pack-download", path, "downloads must remain non-automatic")
                if not isinstance(download, dict) or not HEX_SHA.fullmatch(str(download.get("ref", ""))):
                    self.error("pack-unpinned", path, "download ref must be a full 40-character commit SHA")

            plugin_root = path.parents[1]
            mcp_path = plugin_root / ".mcp.json"
            mcp = self.load_json(mcp_path) if mcp_path.is_file() else None
            servers = mcp.get("mcpServers") if isinstance(mcp, dict) else None
            if not isinstance(servers, dict) or len(servers) != 1:
                self.error("pack-mcp", mcp_path, "pack must declare exactly one gated local MCP adapter")
            elif isinstance(servers, dict):
                server = next(iter(servers.values()))
                if not isinstance(server, dict) or server.get("command") not in {"python", "python3", "py"}:
                    self.error("pack-mcp", mcp_path, "MCP must launch the bundled Python gate directly")
                args = server.get("args") if isinstance(server, dict) else None
                if not isinstance(args, list) or not any("${PLUGIN_ROOT}/scripts/" in str(item) for item in args):
                    self.error("pack-mcp", mcp_path, "MCP args must use a PLUGIN_ROOT script path")

    def validate_editions(self) -> None:
        descriptors: dict[str, tuple[Path, dict[str, object]]] = {}
        for path in sorted((self.root / "plugins").glob("ai-game-studio-*/editions/*.json")):
            payload = self.load_json(path)
            if not isinstance(payload, dict):
                continue
            edition_id = payload.get("id")
            if not isinstance(edition_id, str):
                self.error("edition-id", path, "descriptor id must be a string")
                continue
            if edition_id in descriptors:
                self.error("edition-duplicate", path, f"duplicate edition ID {edition_id!r}")
            descriptors[edition_id] = (path, payload)
        if set(descriptors) != set(EXPECTED_EDITIONS):
            self.error(
                "edition-set",
                self.root / "plugins",
                f"expected {sorted(EXPECTED_EDITIONS)}, found {sorted(descriptors)}",
            )
        required_lists = (
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
        )
        for edition_id, (path, descriptor) in sorted(descriptors.items()):
            expected = EXPECTED_EDITIONS.get(edition_id)
            if expected is None:
                continue
            target_os, plugin_name = expected
            for key in ("plugin", "display_name", "target_os", "version", "license", "activation"):
                if key not in descriptor:
                    self.error("edition-field", path, f"missing {key}")
            if descriptor.get("plugin") != plugin_name:
                self.error("edition-plugin", path, f"plugin must be {plugin_name}")
            if descriptor.get("target_os") != target_os:
                self.error("edition-os", path, f"target_os must be {target_os}")
            if descriptor.get("version") != RELEASE_VERSION:
                self.error("edition-version", path, f"version must be {RELEASE_VERSION}")
            if descriptor.get("license") != "MIT":
                self.error("edition-license", path, "license must be MIT")
            for key in required_lists:
                value = descriptor.get(key)
                if not isinstance(value, list) or not value:
                    self.error("edition-field", path, f"{key} must be a non-empty array")
            for key in ("shells", "package_managers", "gpu_backends", "applications"):
                values = descriptor.get(key)
                if isinstance(values, list) and any(
                    not isinstance(item, dict) or not isinstance(item.get("id"), str)
                    for item in values
                ):
                    self.error(
                        "edition-field",
                        path,
                        f"{key} entries must be objects with string IDs",
                    )
            activation = descriptor.get("activation")
            if not isinstance(activation, dict) or activation.get("mode") != "confirmed-transaction-only":
                self.error("edition-confirmation", path, "activation.mode must be confirmed-transaction-only")
            if not isinstance(activation, dict) or activation.get("project_state") != ".ai-game-studio/project.json":
                self.error("edition-state", path, "activation.project_state must use the scoped project state")
            if not isinstance(activation, dict) or activation.get("lock_file") != ".ai-game-studio/lock.json":
                self.error("edition-state", path, "activation.lock_file must use the scoped lock file")
            for rule in descriptor.get("adaptation_rules", []):
                if not isinstance(rule, dict):
                    self.error("edition-rule", path, "adaptation rules must be objects")
                    continue
                missing = {
                    "id",
                    "source_constraint",
                    "preferred_native",
                    "alternatives",
                    "limitations",
                    "requires_confirmation",
                } - set(rule)
                if missing:
                    self.error("edition-rule", path, f"adaptation rule missing {sorted(missing)}")
                if rule.get("requires_confirmation") is not True:
                    self.error("edition-rule", path, "every substitution must require confirmation")
                if not rule.get("limitations"):
                    self.error("edition-rule", path, "every adaptation must disclose limitations")
            expected_launcher = (
                "ai-game-studio-windows.ps1"
                if edition_id == "windows"
                else "ai-game-studio-macos.sh"
            )
            plugin_root = self.root / "plugins" / plugin_name
            if not (plugin_root / "scripts" / "edition.py").is_file():
                self.error("edition-launcher", plugin_root, "missing scripts/edition.py")
            if not (plugin_root / "scripts" / expected_launcher).is_file():
                self.error(
                    "edition-launcher",
                    plugin_root,
                    f"missing scripts/{expected_launcher}",
                )
            if edition_id == "macos" and (self.root / ".git").exists():
                launcher_path = plugin_root / "scripts" / expected_launcher
                try:
                    relative_launcher = launcher_path.relative_to(self.root).as_posix()
                    result = subprocess.run(
                        ["git", "ls-files", "--stage", "--", relative_launcher],
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10,
                    )
                except (OSError, subprocess.SubprocessError) as error:
                    self.error(
                        "edition-launcher-mode",
                        launcher_path,
                        f"could not inspect Git executable mode: {error}",
                    )
                else:
                    fields = result.stdout.strip().split(maxsplit=3)
                    if result.returncode != 0 or len(fields) != 4 or fields[0] != "100755":
                        self.error(
                            "edition-launcher-mode",
                            launcher_path,
                            "macOS launcher must be tracked with Git mode 100755",
                        )

    def validate_img2threejs(self) -> None:
        plugin_root = self.root / "plugins" / "ai-game-studio-img2threejs"
        provenance_path = plugin_root / "UPSTREAM.json"
        provenance = self.load_json(provenance_path) if provenance_path.is_file() else None
        if not isinstance(provenance, dict):
            self.error("img2threejs-provenance", provenance_path, "missing upstream provenance")
        else:
            expected = {
                "repository": "img2threejs/img2threejs",
                "url": "https://github.com/img2threejs/img2threejs",
                "tag": "v1.4.3",
                "commit": PINNED_IMG2THREEJS_COMMIT,
                "license": "Apache-2.0",
            }
            for key, value in expected.items():
                if provenance.get(key) != value:
                    self.error("img2threejs-provenance", provenance_path, f"{key} must be {value}")
        skill_root = plugin_root / "skills" / "img2threejs"
        for relative in (
            "LICENSE",
            "forge/next.py",
            "forge/_shared/image_decode.py",
            "forge/_shared/spec_search.py",
            "forge/stage1_intake/fetch_cs2_metadata.py",
            "forge/stage1_intake/extract_cs2_textures.py",
            "forge/stage2_spec/validate_sculpt_spec.py",
            "forge/stage4_review/divine_eye.py",
            "grimoire/intake/validation_rubric.md",
            "grimoire/build/cs2_finishes.md",
            "grimoire/build/geometry_patterns.md",
            "grimoire/build/threejs_texture_reference.md",
        ):
            path = skill_root / relative
            if not path.is_file():
                self.error("img2threejs-resource", path, "required vendored runtime resource is missing")
            elif (self.root / ".git").exists():
                relative_path = path.relative_to(self.root).as_posix()
                try:
                    tracked = subprocess.run(
                        ["git", "ls-files", "--error-unmatch", "--", relative_path],
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10,
                    )
                except (OSError, subprocess.SubprocessError) as error:
                    self.error(
                        "img2threejs-tracking",
                        path,
                        f"could not inspect Git tracking state: {error}",
                    )
                else:
                    if tracked.returncode != 0:
                        self.error(
                            "img2threejs-tracking",
                            path,
                            "required vendored runtime resource must be tracked by Git",
                        )
        hardened_sources = {
            "forge/_shared/image_decode.py": (
                (
                    "AI_GAME_STUDIO_IMAGEMAGICK_MANIFEST",
                    "/usr/bin/sips",
                    "WindowsPowerShell",
                    "confirmed_plan_digest",
                    "shell=False",
                ),
                ("shutil.which(", "shell" + "=True"),
            ),
            "forge/_shared/spec_search.py": (
                ("AI_GAME_STUDIO_CACHE_DIR", "default_cache_root", "cache_root"),
                (),
            ),
            "forge/stage1_intake/fetch_cs2_metadata.py": (
                (
                    "DEFAULT_INDEX_HOSTS",
                    "DEFAULT_IMAGE_HOSTS",
                    "MAX_INDEX_BYTES",
                    "MAX_IMAGE_BYTES",
                    "--confirmed-host",
                    "--force-image",
                    "ensure_public_host",
                ),
                (),
            ),
            "forge/stage1_intake/extract_cs2_textures.py": (
                (
                    "--extractor-manifest",
                    "confirmed_plan_digest",
                    "timeout=300",
                ),
                ("SOURCE2VIEWER_BINARY", "shutil.which("),
            ),
        }
        for relative, (required_tokens, forbidden_tokens) in hardened_sources.items():
            path = skill_root / relative
            if not path.is_file():
                continue
            source = path.read_text(encoding="utf-8")
            for token in required_tokens:
                if token not in source:
                    self.error(
                        "img2threejs-hardening",
                        path,
                        f"required portability or security control is missing: {token}",
                    )
            for token in forbidden_tokens:
                if token in source:
                    self.error(
                        "img2threejs-hardening",
                        path,
                        f"unsafe or unpinned runtime behavior is present: {token}",
                    )
        for path in plugin_root.rglob("*"):
            if "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"}:
                self.error("img2threejs-cache", path, "generated Python cache must not be vendored")

    def validate_hooks(self) -> None:
        hooks_path = self.root / "plugins" / "ai-game-studio-automation" / "hooks" / "hooks.json"
        hooks = self.load_json(hooks_path) if hooks_path.is_file() else None
        if not isinstance(hooks, dict):
            self.error("hooks", hooks_path, "missing hooks configuration")
            return
        configured = hooks.get("hooks", hooks)
        if not isinstance(configured, dict):
            self.error("hooks", hooks_path, "hooks must be an object keyed by event")
            return
        events = set(configured)
        if not EXPECTED_HOOK_EVENTS <= events:
            self.error("hook-events", hooks_path, f"missing events {sorted(EXPECTED_HOOK_EVENTS-events)}")
        raw = hooks_path.read_text(encoding="utf-8")
        if "${PLUGIN_ROOT}" not in raw and "$PLUGIN_ROOT" not in raw:
            self.error("hook-portability", hooks_path, "hook commands must use PLUGIN_ROOT")
        if "commandWindows" not in raw:
            self.error("hook-platform", hooks_path, "hook commands must define commandWindows")

    def validate_markdown_links(self) -> None:
        ignored_parts = {".git", ".official", "dist", "sources", "__pycache__"}
        for path in self.root.rglob("*.md"):
            if any(part in ignored_parts for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError as exc:
                self.error("markdown-encoding", path, str(exc))
                continue
            for match in MD_LINK.finditer(text):
                target = match.group(1).strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                target = target.split(maxsplit=1)[0].strip("'\"")
                if not target or target.startswith(("#", "http://", "https://", "mailto:", "codex:")):
                    continue
                target = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if target.lower() in {"link", "url", "path"}:
                    continue
                resolved = (path.parent / target).resolve()
                if self.root not in (resolved, *resolved.parents):
                    self.error("markdown-path-escape", path, f"link escapes repository: {target!r}")
                elif not resolved.exists():
                    self.error("markdown-broken-link", path, f"missing local target {target!r}")

    def validate_workflows(self) -> None:
        workflow_root = self.root / ".github" / "workflows"
        workflow_files = sorted((*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml"))) if workflow_root.is_dir() else []
        expected = {
            "ci.yml",
            "catalog-refresh.yml",
            "pages.yml",
            "release.yml",
            "codeql.yml",
            "dependency-review.yml",
        }
        names = {path.name for path in workflow_files}
        if not expected <= names:
            self.error("workflow-set", workflow_root, f"missing workflows {sorted(expected-names)}")
        for path in workflow_files:
            text = path.read_text(encoding="utf-8")
            for use in ACTION_USE.findall(text):
                if use.startswith("./"):
                    resolved = safe_resolve(self.root, use)
                    if resolved is None or not resolved.exists():
                        self.error("workflow-local-action", path, f"missing or escaping local action {use!r}")
                    continue
                if "@" not in use:
                    self.error("workflow-unpinned", path, f"action has no immutable revision: {use}")
                    continue
                revision = use.rsplit("@", 1)[1]
                if not HEX_SHA.fullmatch(revision):
                    self.error("workflow-unpinned", path, f"action must use a 40-character commit SHA: {use}")
            if path.name == "release.yml":
                forbidden = ("gh release upload", "--clobber")
                if any(token in text for token in forbidden):
                    self.error(
                        "release-mutable-assets",
                        path,
                        "release workflow must never replace assets for an existing tag",
                    )
                required = (
                    "group: release-${{ inputs.version || github.ref_name }}",
                    "gh release view \"$RELEASE_TAG\"",
                    "refusing to replace immutable assets",
                    "gh release create \"$RELEASE_TAG\"",
                )
                missing = [token for token in required if token not in text]
                if missing:
                    self.error(
                        "release-immutability-guard",
                        path,
                        f"release workflow is missing immutable publication guards: {missing}",
                    )

    def validate_source_safety(self) -> None:
        ignored_parts = {".git", ".official", "dist", "sources", "__pycache__"}
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if any(part in ignored_parts for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    self.error("credential-leak", path, f"matches secret pattern {pattern.pattern!r}")
            if path.suffix.lower() in {".py", ".ps1", ".sh"} and is_executable_surface(self.root, path):
                for pattern, label in UNSAFE_CODE_PATTERNS:
                    if pattern.search(text):
                        self.error("unsafe-command", path, label)
            if is_runtime_file(self.root, path):
                patterns = (r"\.claude[/\\]", r"\bCLAUDE\.md\b", r"\bclaude-(?:2|3|opus|sonnet|haiku)\b")
                migration_ranges = allowed_migration_ranges(path, text)
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if any(start <= line_number <= end for start, end in migration_ranges):
                        continue
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.error("claude-runtime", path, f"line {line_number} contains Claude-only token matching {pattern}")

    def validate_release_layout(self) -> None:
        required = {
            self.root / "tools" / "build_release.py",
            self.root / "release" / "README.md",
            self.root / "docs" / "VALIDATION.md",
        }
        for path in required:
            if not path.is_file():
                self.error("release-layout", path, "required release or validation file is missing")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {}, str(exc)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "frontmatter must start on the first line"
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}, "frontmatter closing delimiter is missing"
    result: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):\s*(.*)", line)
        if not match:
            return {}, f"frontmatter line {number} is not a scalar key/value"
        key, value = match.groups()
        if key in result:
            return {}, f"duplicate frontmatter key {key!r}"
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[key] = value
    return result, None


def safe_resolve(base: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        return None
    candidate = Path(relative)
    if candidate.is_absolute():
        return None
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        return None
    return resolved


def is_runtime_file(root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    if "migrate-claude" in parts:
        return False
    if not parts or parts[0] != "plugins":
        return False
    return any(part in {"scripts", "hooks"} for part in parts) or path.name in {".mcp.json", "pack.json"}


def is_executable_surface(root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    return bool(parts and parts[0] == "tools") or (
        bool(parts and parts[0] == "plugins") and any(part in {"scripts", "hooks"} for part in parts)
    )


def allowed_migration_ranges(path: Path, source: str) -> list[tuple[int, int]]:
    """Return line ranges where Claude path detection is explicitly a migration behavior."""
    if path.suffix.lower() != ".py" or "claude" not in source.lower():
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    return [
        (node.lineno, node.end_lineno or node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and "claude" in node.name.lower()
    ]


def emit(problems: Iterable[Problem], output_format: str) -> int:
    collected = list(problems)
    if output_format == "json":
        print(json.dumps({"ok": not collected, "problems": [item.__dict__ for item in collected]}, indent=2))
    elif collected:
        print(f"Repository validation failed with {len(collected)} problem(s):")
        for item in collected:
            print(f"- {item.render()}")
    else:
        print("Repository validation passed.")
    return 1 if collected else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    return emit(Validator(args.root).run(), args.format)


if __name__ == "__main__":
    raise SystemExit(main())
