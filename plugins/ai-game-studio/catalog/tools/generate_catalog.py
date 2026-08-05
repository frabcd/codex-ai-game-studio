#!/usr/bin/env python3
"""Build the checked-in offline catalog from the verified Markdown landscape.

The generator deliberately uses only the Python standard library. It preserves
human curation separately from volatile GitHub metadata and never downloads,
installs, imports, or executes any catalog entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


EXPECTED_SHA256 = "acdfbb53d66400127f68529e447cc22872a7bc71e5cd994b0f4e32b10c2355a6"
VERIFIED_DATE = "2026-07-30"
SCHEMA_BASE = "https://frabcd.github.io/codex-ai-game-studio/schemas"

LINK_RE = re.compile(r"\[([^\]]+)]\((https://github\.com/[^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
TYPE_RE = re.compile(r"\*\*([^*]+)\*\*")

WORKFLOW_BY_SECTION = {
    "1": ["tool-discovery", "studio-workflows"],
    "2": ["prompt-to-game", "studio-workflows"],
    "3": ["world-generation", "interactive-worlds"],
    "4": ["engine-automation", "dcc-automation"],
    "5": ["asset-3d-generation", "mesh-processing"],
    "6": ["material-texture-generation", "pbr-authoring"],
    "7": ["rigging", "animation"],
    "8": ["sprite-generation", "pixel-art", "tiles"],
    "9": ["procedural-generation", "level-design"],
    "10": ["npc-generation", "dialogue", "quests"],
    "11": ["audio-generation", "voice"],
    "12": ["playtesting", "functional-qa"],
    "13": ["visual-qa", "quality-scoring"],
    "14": ["quality-enhancement", "restoration"],
    "15": ["technical-validation", "asset-optimization"],
}

CAPABILITY_KEYWORDS = {
    "agent-skills": ("skill", "agent workflow", "studio roles"),
    "prompt-to-game": ("prompt to", "prompt-driven", "generated game", "gamecoder"),
    "engine-control": ("editor control", "mcp", "editor integration", "automation"),
    "image-generation": ("image generation", "stable diffusion", "concept art"),
    "sprite-generation": ("sprite", "pixel-art", "pixel art", "spritesheet"),
    "tile-generation": ("tilemap", "tileset", "dungeon tile"),
    "mesh-generation": ("mesh generation", "image-to-3d", "text-to-3d", "text/image to 3d"),
    "mesh-processing": ("topology", "mesh simplification", "mesh optimizer", "decimation"),
    "texture-generation": ("texture", "pbr", "material"),
    "rigging": ("rigging", "skeleton", "skin-weight", "skinning"),
    "animation": ("animation", "motion", "mocap", "pose"),
    "world-generation": ("world generation", "world model", "3d scene", "terrain"),
    "procedural-generation": ("procedural", "level generation", "pcgrl"),
    "npc-dialogue": ("npc", "dialogue", "game master", "quest", "narrative"),
    "audio-generation": ("audio", "music", "sound effect", "foley"),
    "voice-generation": ("voice", "speech", "text-to-speech", "tts"),
    "playtesting": ("playtest", "gameplay", "unit-test", "behavioral validation"),
    "visual-quality": ("image quality", "visual quality", "aesthetic", "visual regression"),
    "restoration": ("restoration", "upscal", "super-resolution", "denoising"),
    "asset-validation": ("validator", "validation", "import/export checks"),
}

RECIPE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "tool-discovery",
        "title": "Discover a compatible game-production toolchain",
        "inputs": ["project_path", "target_platforms", "budget", "commercial_intent"],
        "capabilities": ["tool-discovery"],
        "stages": [
            ("detect", "Read project, OS, engine, DCC, GPU, and existing MCP metadata without mutation."),
            ("filter", "Filter candidates by license, platform, hardware, application, and security constraints."),
            ("compare", "Compare compatible candidates by capability, quality, cost, performance, and limitations."),
            ("plan", "Produce one digest-bound transaction with exact pins, permissions, backups, and rollback."),
            ("confirm", "Wait for explicit human confirmation before any installation or configuration change."),
        ],
        "artifacts": ["environment-report.json", "toolchain-comparison.md", "transaction-plan.json"],
        "specific_gates": ["No unresolved license may be presented as commercially cleared.", "Only one MCP server per host application may be active."],
        "fallbacks": ["Use the checked-in offline catalog when GitHub metadata is unavailable.", "Offer a verified native or hosted alternative when hardware is incompatible."],
    },
    {
        "id": "prompt-to-game",
        "title": "Prompt to playable vertical slice",
        "inputs": ["game_brief", "target_engine", "target_platform", "scope_budget"],
        "capabilities": ["prompt-to-game", "engine-control", "playtesting"],
        "stages": [
            ("brief", "Turn the prompt into testable pillars, constraints, and a minimal playable loop."),
            ("prototype", "Create the smallest reversible implementation using placeholders first."),
            ("integrate", "Integrate generated assets only after format and provenance checks."),
            ("playtest", "Run deterministic smoke checks and representative player journeys."),
            ("review", "Present build evidence and request human approval for the vertical slice."),
        ],
        "artifacts": ["game-brief.md", "vertical-slice/", "playtest-report.json", "screenshots/"],
        "specific_gates": ["The core loop must be playable in a clean build.", "Generated assets must not silently replace source assets."],
        "fallbacks": ["Reduce scope to one mechanic and one level.", "Keep placeholder art when generation rights or quality are unresolved."],
    },
    {
        "id": "sprite-animation",
        "title": "Generate and validate a 2D sprite animation",
        "inputs": ["character_brief", "style_reference", "frame_count", "engine_import_target"],
        "capabilities": ["sprite-generation", "image-generation", "visual-quality"],
        "stages": [
            ("spec", "Lock canvas, palette, silhouette, pivot, baseline, directions, and frame timing."),
            ("generate", "Generate candidates with seed, model, prompt, and reference provenance."),
            ("normalize", "Normalize transparency, bounds, alignment, palette, and frame dimensions."),
            ("animate", "Assemble the loop and inspect temporal continuity at target speed."),
            ("import", "Import a copy into the target engine and capture runtime evidence."),
        ],
        "artifacts": ["sprite-spec.json", "frames/*.png", "sprite-sheet.png", "preview.gif", "import-report.json"],
        "specific_gates": ["Alpha edges are clean and every frame shares a stable baseline.", "Loop endpoints, timing, proportions, and identity remain consistent."],
        "fallbacks": ["Repair frames deterministically in Aseprite or Pixelorama.", "Retain approved frames and regenerate only failing poses."],
    },
    {
        "id": "asset-3d-generation",
        "title": "Generate an engine-ready 3D asset",
        "inputs": ["asset_brief", "reference_images", "triangle_budget", "engine_import_target"],
        "capabilities": ["mesh-generation", "mesh-processing", "asset-validation"],
        "stages": [
            ("spec", "Define silhouette, scale, axes, topology, UV, LOD, collision, and material budgets."),
            ("generate", "Generate isolated candidates and record source model, weights, seed, and references."),
            ("repair", "Repair topology, normals, UVs, transforms, holes, intersections, and non-manifold geometry."),
            ("optimize", "Create collision and LODs while preserving silhouette and shading."),
            ("import", "Validate the exported copy and inspect it from multiple engine views."),
        ],
        "artifacts": ["asset-spec.json", "source-model/", "optimized.glb", "lods/", "engine-import-report.json"],
        "specific_gates": ["Topology, normals, UVs, scale, axes, PBR slots, LODs, and collision validate.", "Triangle, texture-memory, draw-call, and load-time budgets pass."],
        "fallbacks": ["Use a conventional modeled placeholder when weights or output terms are unclear.", "Decimate or retopologize a preserved copy instead of modifying the source."],
    },
    {
        "id": "pbr-material-generation",
        "title": "Generate and validate PBR materials",
        "inputs": ["material_brief", "mesh_uvs", "resolution_budget", "render_pipeline"],
        "capabilities": ["texture-generation", "visual-quality", "asset-validation"],
        "stages": [
            ("spec", "Define texel density, channels, color space, tiling, packing, and engine shader target."),
            ("generate", "Generate albedo, normal, roughness, metallic, AO, and height candidates."),
            ("sanitize", "Remove baked lighting, correct normal orientation, clamp values, and repair seams."),
            ("pack", "Resize and pack channels without overwriting source maps."),
            ("review", "Render neutral-light turntables and inspect at gameplay distances."),
        ],
        "artifacts": ["material-spec.json", "source-maps/", "packed-maps/", "turntable/", "material-report.json"],
        "specific_gates": ["Maps use the expected color spaces and channel conventions.", "Seams, tiling, energy response, texel density, and memory budget pass."],
        "fallbacks": ["Bake a conventional material in Blender.", "Ship a neutral verified material while generated maps remain under review."],
    },
    {
        "id": "rig-animation",
        "title": "Rig, animate, compose, and validate procedural VFX",
        "inputs": ["source_mesh_or_effect_anchor", "target_skeleton_and_runtime", "motion_and_cue_brief", "vfx_style_guide", "runtime_budget"],
        "capabilities": ["rigging", "animation", "procedural-generation", "engine-control", "visual-qa"],
        "stages": [
            ("prepare", "Inspect the rig, animation controller, renderer, dependencies, tests, target runtime, and budgets read-only; validate neutral pose, transforms, topology, scale, and skeleton requirements."),
            ("specify", "For the VFX route, read the bundled procedural VFX composer reference completely, define the effect taxonomy, style guide, named five-color palettes, parameter schema, animation-cue contract, editor interface, and acceptance captures, then validate vfx-project.json before presenting the exact digest-confirmed implementation plan."),
            ("rig", "After confirmation, create a candidate skeleton and skin weights on a copy, then map bones, root motion, contacts, sockets, weapon-tip measurements, and animation curves."),
            ("generate", "Generate seeded runtime DataTextures for integer-hash value noise, FBM, domain warping, and radial cracks; build procedural effect meshes and degenerate-safe parallel-transport tubes for trails, beams, and bolts."),
            ("shade", "Compose shared GLSL noise, shape, and edge chunks into eroded, banded, inked, and heat-gradient effects using palette-driven layered additive geometry without required post-processing or particle middleware."),
            ("compose", "Build an animation and VFX composer with effect library and VFX sheet, preview viewport, transport, scrubbing, timeline, cue tracks, inspector, palette controls, deterministic import/export, and undo/redo."),
            ("cue", "Fire effects from typed animation cues, sizing from rig and weapon measurements and aiming at authored impact targets with deterministic play, loop, seek, repeat, and dropped-frame behavior."),
            ("inspect", "Review deformation, foot sliding, penetration, loops, shader compilation, tube stability, palette readability, transparent sorting, cue timing, state round trips, resource disposal, and runtime budgets."),
            ("import", "Test clips, effects, composer state, and representative transitions in the target engine or browser runtime and capture reproducible multi-view temporal evidence."),
        ],
        "artifacts": ["rig-map.json", "rigged-source.fbx", "clips/", "vfx-style-guide.md", "vfx-project.json", "vfx-palettes.json", "vfx-cues.json", "procedural-vfx/", "composer-state.json", "vfx-sheet/", "deformation-review/", "animation-vfx-report.json"],
        "specific_gates": [
            "Weights and deformations pass extreme-pose review; root motion, contacts, foot sliding, loop continuity, and state transitions pass.",
            "Runtime texture and geometry generation is deterministic from recorded seeds and parameters, parallel-transport tubes stay finite on degenerate paths, and shaders compile without NaNs.",
            "Named core, body, edge, ink, and ash palettes preserve readable bands; layered transparency, sorting, disposal, overdraw, draw calls, memory, and frame time pass explicit budgets.",
            "Animation cues remain stable during play, loop, seek, repeat, dropped frames, and transitions; reach and aim derive from recorded rig and weapon measurements.",
            "Composer state round-trips deterministically, undo and redo release resources, and editor previews match runtime parameters, timing, and captures.",
        ],
        "fallbacks": [
            "Use a known compatible skeleton and manual weight cleanup while keeping source motion and only verified clips.",
            "Use a smaller CPU-generated texture field, reduced procedural geometry subdivisions, and a compact shared shader set before adding middleware.",
            "Reduce effect layers, tube segments, debris, concurrent instances, and update frequency before changing animation-critical cue timing.",
        ],
    },
    {
        "id": "world-generation",
        "title": "Generate a playable environment or procedural level",
        "inputs": ["world_brief", "navigation_rules", "encounter_plan", "runtime_budget"],
        "capabilities": ["world-generation", "procedural-generation", "playtesting"],
        "stages": [
            ("constraints", "Define bounds, traversal metrics, landmarks, spawn rules, and performance budgets."),
            ("layout", "Generate candidate layout data separately from art dressing."),
            ("validate", "Validate connectivity, collision, navigation, reachability, and encounter constraints."),
            ("dress", "Add lighting and assets while preserving gameplay readability."),
            ("playtest", "Exercise spawn-to-goal routes and capture frame-time and visual evidence."),
        ],
        "artifacts": ["world-spec.json", "layout/", "navigation-report.json", "performance-capture.json", "walkthrough/"],
        "specific_gates": ["All required spawns and objectives are reachable.", "Navigation, lighting, collision, streaming, and runtime budgets pass."],
        "fallbacks": ["Use a deterministic procedural layout seed.", "Reduce dressing density before changing navigation-critical geometry."],
    },
    {
        "id": "npc-audio-generation",
        "title": "Generate NPC dialogue, quests, voice, music, and sound",
        "inputs": ["narrative_bible", "npc_profile", "consent_records", "audio_budget"],
        "capabilities": ["npc-dialogue", "audio-generation", "voice-generation"],
        "stages": [
            ("rights", "Verify identity, voice, music, dataset, and output rights before generation."),
            ("design", "Define state constraints, safety boundaries, quest invariants, and fallback lines."),
            ("generate", "Generate structured dialogue and audio candidates with provenance."),
            ("validate", "Check state consistency, pronunciation, peaks, loudness, duration, and loop seams."),
            ("integrate", "Import approved copies and test interruption, replay, localization, and fallback behavior."),
        ],
        "artifacts": ["consent-record.json", "dialogue-graph.json", "audio/", "loudness-report.json", "npc-test-report.json"],
        "specific_gates": ["Unlicensed identity references or voice cloning without consent block production use.", "Audio peaks, loudness, loop seams, dialogue state, and quest invariants pass."],
        "fallbacks": ["Use text-only dialogue or a licensed synthetic stock voice.", "Use deterministic authored fallback lines when generation is unavailable."],
    },
    {
        "id": "engine-automation",
        "title": "Plan and run reversible engine automation",
        "inputs": ["project_path", "engine", "requested_changes", "test_target"],
        "capabilities": ["engine-control", "asset-validation"],
        "stages": [
            ("detect", "Read engine version, project state, existing MCP configuration, and repository status."),
            ("plan", "Describe exact files, editor operations, permissions, backups, health checks, and rollback."),
            ("confirm", "Require the human-confirmed plan digest before editor control or configuration mutation."),
            ("apply", "Apply only scoped actions through one MCP server for the host application."),
            ("verify", "Run editor health checks, tests, screenshots, and rollback rehearsal."),
        ],
        "artifacts": ["engine-detection.json", "transaction-plan.json", "change-log.json", "health-check.json", "rollback-report.json"],
        "specific_gates": ["No mutation occurs before digest confirmation.", "Only one active MCP server controls a given host application."],
        "fallbacks": ["Provide manual editor steps when no compatible MCP is available.", "Disable the pack and restore backed-up configuration if health checks fail."],
    },
    {
        "id": "visual-qa",
        "title": "Run multi-view visual and temporal QA",
        "inputs": ["reference_set", "candidate_artifacts", "capture_matrix", "acceptance_thresholds"],
        "capabilities": ["visual-quality", "playtesting", "asset-validation"],
        "stages": [
            ("baseline", "Lock references, views, camera, lighting, resolution, and tolerances."),
            ("capture", "Capture deterministic stills and temporal samples across the matrix."),
            ("measure", "Run format-aware metrics without treating any single score as authoritative."),
            ("review", "Inspect silhouette, palette, identity, artifacts, motion, and gameplay readability."),
            ("report", "Store annotated comparisons and request a human accept, revise, or reject decision."),
        ],
        "artifacts": ["capture-matrix.json", "baseline/", "candidate/", "diffs/", "visual-qa-report.html"],
        "specific_gates": ["Multiple gameplay-relevant views and temporal samples are reviewed.", "Automated metrics are corroborated by artifact evidence and human review."],
        "fallbacks": ["Use deterministic screenshot diffs when learned metrics are unavailable.", "Escalate ambiguous changes to side-by-side human review."],
    },
    {
        "id": "quality-enhancement",
        "title": "Enhance assets without losing approved sources",
        "inputs": ["source_assets", "defect_list", "target_spec", "replacement_policy"],
        "capabilities": ["restoration", "visual-quality", "asset-validation"],
        "stages": [
            ("preserve", "Hash and copy source assets into a read-only comparison set."),
            ("plan", "Choose the smallest reversible enhancement for each measured defect."),
            ("enhance", "Produce new candidates without overwriting originals."),
            ("compare", "Generate before/after technical, visual, temporal, and runtime evidence."),
            ("approve", "Replace production references only after explicit human approval."),
        ],
        "artifacts": ["source-hashes.json", "enhanced/", "before-after/", "quality-report.json", "replacement-plan.json"],
        "specific_gates": ["Originals remain recoverable and bit-identical.", "Enhancement does not introduce identity drift, temporal artifacts, or budget regressions."],
        "fallbacks": ["Reject the candidate and retain the source asset.", "Apply a deterministic editor correction instead of a generative enhancement."],
    },
    {
        "id": "existing-project-adoption",
        "title": "Adopt the studio workflows in an existing game",
        "inputs": ["project_path", "team_constraints", "target_workflows", "commercial_intent"],
        "capabilities": ["studio-workflows", "tool-discovery", "engine-control"],
        "stages": [
            ("inventory", "Read project structure, conventions, generated files, tools, and repository state."),
            ("gaps", "Map requested workflows to existing capabilities without replacing working tools."),
            ("proposal", "Show one scoped setup, exact generated files, conflicts, permissions, and rollback."),
            ("confirm", "Wait for explicit confirmation of the transaction digest."),
            ("validate", "Apply approved additions and prove that build, tests, and rollback still work."),
        ],
        "artifacts": ["project-inventory.json", "gap-analysis.md", "transaction-plan.json", "adoption-report.json"],
        "specific_gates": ["Existing project conventions and unrelated changes remain intact.", "New automation can be disabled and rolled back without damaging project state."],
        "fallbacks": ["Use the core skills without editor automation.", "Adopt one workflow at a time when conflicts cannot be resolved safely."],
    },
]

COMMON_GATES = [
    {"id": "rights", "description": "Verify rights, consent, code, weights, datasets, output terms, and generation provenance.", "human_required": True},
    {"id": "technical-format", "description": "Validate formats and domain-specific technical constraints.", "human_required": False},
    {"id": "visual-temporal", "description": "Check visual identity and temporal consistency across relevant views and frames.", "human_required": False},
    {"id": "runtime-budget", "description": "Check memory, frame time, draw calls, load time, and asset budgets.", "human_required": False},
    {"id": "playability", "description": "Run interaction and playability smoke tests in the target runtime.", "human_required": False},
    {"id": "regression-evidence", "description": "Store screenshots, artifacts, logs, versions, and comparison evidence.", "human_required": False},
    {"id": "human-approval", "description": "Require human approval before replacing any source or production asset.", "human_required": True},
]


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def canonical_parts(url: str) -> tuple[str, str, str | None]:
    path = urlsplit(url).path.strip("/").split("/")
    if len(path) < 2:
        raise ValueError(f"not a repository URL: {url}")
    owner, repo = path[0], path[1].removesuffix(".git")
    subpath = "/".join(path[2:]) or None
    return owner, repo, subpath


def slug(owner: str, repo: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", f"{owner}-{repo}".lower()).strip("-")


def parse_stars(value: str) -> int | None:
    value = value.strip().lower().replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(k)?", value)
    if not match:
        return None
    result = float(match.group(1))
    if match.group(2):
        result *= 1000
    return int(round(result))


def clean_summary(line: str, match: re.Match[str]) -> str:
    tail = line[match.end():].strip()
    # The source contains a damaged dash sequence on some bullets. Strip any
    # leading separator bytes without carrying that workstation encoding into
    # the public registry.
    tail = re.sub(r"^[^*A-Za-z0-9]+", "", tail)
    tail = re.sub(r"^\*\*[^*]+\*\*\.?\s*", "", tail)
    if line.startswith("|"):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        return cells[-1].rstrip(".") + "." if cells else "Cataloged game-development repository."
    return tail.rstrip(".") + "." if tail else "Cataloged game-development repository."


def choose_kind(type_label: str, summary: str) -> str:
    value = f"{type_label} {summary}".lower()
    if "index" in value or "survey" in value:
        return "index"
    if "skills" in value:
        return "skills"
    if "benchmark" in value:
        return "benchmark"
    if "reference architecture" in value or "archived reference" in value:
        return "reference"
    if "framework" in value or "building block" in value:
        return "building-block"
    if "research" in value and "tool" not in value and "production" not in value:
        return "research"
    if "starter" in value or "generated experience" in value or "demo" in value:
        return "starter"
    return "tool"


def choose_maturity(type_label: str, summary: str) -> str:
    value = f"{type_label} {summary}".lower()
    if "archived" in value:
        return "archived"
    if "production" in value:
        return "production"
    if "very early" in value:
        return "experimental"
    if "emerging" in value or "prototype" in value:
        return "emerging"
    if "research" in value or "benchmark" in value:
        return "research"
    if "reference" in value or "index" in value or "survey" in value or "skills" in value:
        return "reference"
    return "unknown"


def infer_capabilities(section: str, subsection: str | None, summary: str, full_name: str) -> list[str]:
    haystack = f"{section} {subsection or ''} {summary} {full_name}".lower()
    values = [capability for capability, needles in CAPABILITY_KEYWORDS.items() if any(needle in haystack for needle in needles)]
    section_number = section.split(".", 1)[0].strip()
    values.extend(WORKFLOW_BY_SECTION.get(section_number, []))
    return sorted(set(values or ["game-development-resource"]))


def infer_engines(section: str, subsection: str | None, summary: str, full_name: str) -> list[str]:
    haystack = f"{section} {subsection or ''} {summary} {full_name}".lower()
    engines: list[str] = []
    for token, engine in (("unity", "unity"), ("godot", "godot"), ("unreal", "unreal-engine"), ("browser", "web"), ("three.js", "web"), ("roblox", "roblox"), ("minecraft", "minecraft")):
        if token in haystack:
            engines.append(engine)
    return sorted(set(engines))


def infer_requirements(section: str, subsection: str | None, summary: str, full_name: str, kind: str) -> dict[str, Any]:
    haystack = f"{section} {subsection or ''} {summary} {full_name}".lower()
    applications = []
    for token, app in (("unity", "Unity Editor"), ("godot", "Godot Editor"), ("unreal", "Unreal Editor"), ("blender", "Blender"), ("aseprite", "Aseprite"), ("pixelorama", "Pixelorama"), ("tiled", "Tiled"), ("comfyui", "ComfyUI")):
        if token in haystack:
            applications.append(app)
    runtimes = []
    if kind in {"research", "building-block", "benchmark"} or any(token in haystack for token in ("diffusion", "pytorch", "python")):
        runtimes.append("Python (version not verified in offline snapshot)")
    if any(token in haystack for token in ("browser", "web ui", "typescript", "javascript", "node")):
        runtimes.append("Node.js or browser runtime (version not verified)")
    gpu_likely = any(token in haystack for token in ("diffusion", "generation", "world model", "nerf", "gaussian", "training", "inference", "mocap"))
    return {
        "runtimes": sorted(set(runtimes)),
        "applications": sorted(set(applications)),
        "gpu": {
            "required": "unknown" if gpu_likely else "not-detected",
            "backends": [],
            "minimum_vram_gb": None,
            "notes": "Consult the pinned upstream documentation before selection; the offline source does not verify a backend or VRAM floor." if gpu_likely else "No GPU requirement was established by the offline source.",
        },
        "network": "required-for-install-only",
    }


def infer_security(capabilities: list[str], kind: str, summary: str) -> dict[str, Any]:
    high = any(cap in capabilities for cap in ("voice-generation", "npc-dialogue")) or "identity" in summary.lower()
    low = kind in {"index", "reference"}
    permissions = {
        "filesystem": ["read-project", "write-generated-output"] if not low else [],
        "network": ["outbound-upstream-and-model-downloads"] if not low else ["outbound-documentation"],
        "process": ["spawn-external-tool"] if kind in {"tool", "building-block", "research", "benchmark", "starter"} else [],
    }
    return {
        "risk_level": "high" if high else ("low" if low else "medium"),
        "permissions": permissions,
        "trust_notes": [
            "Catalog metadata is not an authorization to install or execute this repository.",
            "Review the pinned revision, dependencies, scripts, network behavior, and requested permissions before use.",
        ],
    }


def parse_license_cell(value: str) -> tuple[str, str | None, str]:
    normalized = value.strip()
    lower = normalized.lower()
    if lower in {"verify", "unknown", ""}:
        return "unknown", None, "The source snapshot requires license verification."
    if lower.startswith("custom"):
        return "custom", None, normalized
    if lower.startswith("mit code"):
        return "reported", "MIT", "Code reported as MIT; model weights require separate review."
    return "reported", normalized, "Detected repository license reported by the verified source snapshot; verify at the pinned revision."


def license_bundle(kind: str, capabilities: list[str], reported: str | None, summary: str) -> dict[str, Any]:
    code_status, code_expression, code_notes = parse_license_cell(reported or "unknown")
    if "mit-licensed" in summary.lower():
        code_status, code_expression, code_notes = "reported", "MIT", "MIT is stated in the curated source summary; verify at the pinned revision."
    if "source-available" in summary.lower():
        code_status, code_expression, code_notes = "custom", None, "Source-available terms require direct review."
    summary_lower = summary.lower()
    generation_language = any(token in summary_lower for token in ("generate", "generation", "text-to", "image-to", "diffusion", "model", "inference"))
    generates = kind not in {"index", "skills", "reference"} and generation_language and not ("editor" in summary_lower and "ai" not in summary_lower)
    model_based = (
        generates
        or kind in {"research", "benchmark"}
        or ("prompt-to-game" in capabilities and "prompt" in summary_lower)
        or any(token in summary_lower for token in ("llm", "world model", "foundation model"))
    )
    weights = {"status": "unknown" if model_based else "not_applicable", "expression": None, "notes": "Review every selected model and checkpoint." if model_based else "No model weights were identified for this entry."}
    dataset = {"status": "unknown" if model_based else "not_applicable", "expression": None, "notes": "Training-data rights were not verified by the offline snapshot." if model_based else "No dataset dependency was identified for this entry."}
    output = {"status": "unknown" if generates else "not_applicable", "expression": None, "notes": "Generated-output terms depend on the selected model, service, references, and jurisdiction." if generates else "This entry was not classified as an asset generator."}
    statuses = [code_status, weights["status"], dataset["status"], output["status"]]
    blocked = any(status in {"unknown", "custom", "restricted", "prohibited"} for status in statuses)
    commercial = {
        "status": "blocked" if blocked else "review_required",
        "notes": "Unknown, custom, or restricted terms block commercial recommendation until a qualified human reviews the exact pin and dependencies." if blocked else "No automatic commercial clearance is granted; verify the exact pin, dependencies, and intended use.",
    }
    return {
        "code": {"status": code_status, "expression": code_expression, "notes": code_notes},
        "model_weights": weights,
        "dataset": dataset,
        "generated_output": output,
        "commercial_use": commercial,
    }


def parse_source(source: Path) -> tuple[list[dict[str, Any]], dict[str, int | None]]:
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"source SHA256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    text = data.decode("utf-8-sig")
    h2 = "Uncategorized"
    h3: str | None = None
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reported_licenses: dict[str, str] = {}
    approximate_stars: dict[str, int | None] = {}

    for line_number, line in enumerate(text.splitlines(), start=1):
        heading = HEADING_RE.match(line)
        if heading:
            if len(heading.group(1)) == 2:
                h2, h3 = heading.group(2), None
            else:
                h3 = heading.group(2)
            continue
        for match in LINK_RE.finditer(line):
            source_url = match.group(2).rstrip(".,;")
            owner, repo, subpath = canonical_parts(source_url)
            key = f"{owner}/{repo}".lower()
            type_match = TYPE_RE.search(line[match.end():])
            type_label = type_match.group(1).strip() if type_match else "Tool"
            occurrence = {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "canonical_url": f"https://github.com/{owner}/{repo}",
                "source_url": source_url,
                "subpath": subpath,
                "section": h2,
                "subsection": h3,
                "type_label": type_label,
                "summary": clean_summary(line, match),
                "line": line_number,
                "is_bullet": line.startswith("- "),
            }
            occurrences[key].append(occurrence)
            if h2 == "Best starting points" and line.startswith("|"):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) >= 6 and cells[0] != "Need" and not set(cells[0]) <= {"-", ":"}:
                    approximate_stars[key] = parse_stars(cells[3])
                    reported_licenses[key] = cells[4]

    records: list[dict[str, Any]] = []
    for key, choices in occurrences.items():
        detailed = max(
            choices,
            key=lambda item: (
                20 if re.match(r"\d+\.", item["section"]) else 0,
                10 if item["is_bullet"] else 0,
                2 if item["summary"] != "Cataloged game-development repository." else 0,
                -item["line"],
            ),
        )
        section = detailed["section"]
        subsection = detailed["subsection"]
        summary = detailed["summary"]
        full_name = detailed["full_name"]
        kind = choose_kind(detailed["type_label"], summary)
        maturity = choose_maturity(detailed["type_label"], summary)
        numbered_choices = [choice for choice in choices if re.match(r"\d+\.", choice["section"])] or [detailed]
        context_text = " ".join(
            f"{choice['section']} {choice['subsection'] or ''} {choice['summary']}"
            for choice in numbered_choices
        )
        capabilities = infer_capabilities(context_text, None, summary, full_name)
        workflows = sorted({
            workflow
            for choice in numbered_choices
            for workflow in WORKFLOW_BY_SECTION.get(choice["section"].split(".", 1)[0].strip(), ["tool-discovery"])
        })
        contexts = []
        seen_contexts: set[tuple[str, str | None]] = set()
        for choice in numbered_choices:
            context_key = (choice["section"], choice["subsection"])
            if context_key in seen_contexts:
                continue
            seen_contexts.add(context_key)
            contexts.append({
                "section": choice["section"],
                "subsection": choice["subsection"],
                "source_line": choice["line"],
                "type_label": choice["type_label"],
            })
        repository_id = slug(detailed["owner"], detailed["repo"])
        licenses = license_bundle(kind, capabilities, reported_licenses.get(key), summary)
        docs = sorted({choice["source_url"] for choice in choices} | {detailed["canonical_url"]})
        records.append({
            "id": repository_id,
            "repository": {
                "owner": detailed["owner"],
                "name": detailed["repo"],
                "full_name": full_name,
                "canonical_url": detailed["canonical_url"],
                "source_url": detailed["source_url"],
                "subpath": detailed["subpath"],
            },
            "summary": summary,
            "kind": kind,
            "maturity": maturity,
            "curation": {
                "section": section,
                "subsection": subsection,
                "source_line": detailed["line"],
                "source_occurrences": len(choices),
                "type_label": detailed["type_label"],
                "contexts": contexts,
            },
            "capabilities": capabilities,
            "engines": infer_engines(context_text, None, summary, full_name),
            "workflows": workflows,
            "platform_support": {
                "operating_systems": ["unknown"],
                "architectures": ["unknown"],
                "execution": "external",
                "notes": "Resolve support from the pinned upstream documentation during planning.",
            },
            "requirements": infer_requirements(context_text, None, summary, full_name, kind),
            "authentication": {
                "required": "unknown",
                "environment_variables": [],
                "notes": "Only environment-variable names may be recorded. Never store credential values in the catalog.",
            },
            "licenses": licenses,
            "security": infer_security(capabilities, kind, summary),
            "install": {
                "mode": "external-metadata-only",
                "bundled": False,
                "pinned_source": {
                    "repository_url": detailed["canonical_url"],
                    "ref": None,
                    "pin_status": "unresolved",
                },
                "notes": "The catalog does not vendor, install, download, import, or launch this repository.",
            },
            "verification": {
                "date": VERIFIED_DATE,
                "method": "verified-curated-source-snapshot",
                "repository_presence": "verified-by-source",
                "license_scope": "source-reported-or-unverified",
            },
            "documentation_urls": docs,
        })

    records.sort(key=lambda item: item["id"])
    return records, approximate_stars


def catalog_schema() -> dict[str, Any]:
    license_scope = {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "expression", "notes"],
        "properties": {
            "status": {"enum": ["reported", "unknown", "custom", "restricted", "prohibited", "not_applicable"]},
            "expression": {"type": ["string", "null"]},
            "notes": {"type": "string", "minLength": 1},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/catalog.schema.json",
        "title": "Codex AI Game Studio offline repository catalog",
        "type": "object",
        "additionalProperties": False,
        "required": ["$schema", "schema_version", "catalog_version", "provenance", "records"],
        "properties": {
            "$schema": {"const": f"{SCHEMA_BASE}/catalog.schema.json"},
            "schema_version": {"const": "1.0.0"},
            "catalog_version": {"type": "string"},
            "provenance": {
                "type": "object",
                "additionalProperties": False,
                "required": ["source_path", "source_sha256", "snapshot_date", "record_count", "policy"],
                "properties": {
                    "source_path": {"type": "string"},
                    "source_sha256": {"pattern": "^[a-f0-9]{64}$"},
                    "snapshot_date": {"type": "string", "format": "date"},
                    "record_count": {"const": 163},
                    "policy": {"type": "string"},
                },
            },
            "records": {
                "type": "array",
                "minItems": 163,
                "maxItems": 163,
                "items": {"$ref": "#/$defs/record"},
            },
        },
        "$defs": {
            "record": {
                "type": "object",
                "required": ["id", "repository", "summary", "kind", "maturity", "curation", "capabilities", "engines", "workflows", "platform_support", "requirements", "authentication", "licenses", "security", "install", "verification", "documentation_urls"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
                    "repository": {
                        "type": "object",
                        "required": ["owner", "name", "full_name", "canonical_url", "source_url", "subpath"],
                        "properties": {
                            "owner": {"type": "string"}, "name": {"type": "string"}, "full_name": {"type": "string"},
                            "canonical_url": {"type": "string", "pattern": "^https://github\\.com/[^/]+/[^/]+$"},
                            "source_url": {"type": "string", "pattern": "^https://github\\.com/"},
                            "subpath": {"type": ["string", "null"]},
                        },
                    },
                    "summary": {"type": "string", "minLength": 1},
                    "kind": {"enum": ["index", "skills", "benchmark", "reference", "building-block", "research", "starter", "tool"]},
                    "maturity": {"enum": ["production", "research", "emerging", "experimental", "reference", "archived", "unknown"]},
                    "curation": {"type": "object"},
                    "capabilities": {"type": "array", "minItems": 1, "items": {"type": "string"}, "uniqueItems": True},
                    "engines": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
                    "workflows": {"type": "array", "minItems": 1, "items": {"type": "string"}, "uniqueItems": True},
                    "platform_support": {"type": "object"},
                    "requirements": {"type": "object"},
                    "authentication": {"type": "object"},
                    "licenses": {
                        "type": "object",
                        "required": ["code", "model_weights", "dataset", "generated_output", "commercial_use"],
                        "properties": {
                            "code": license_scope,
                            "model_weights": license_scope,
                            "dataset": license_scope,
                            "generated_output": license_scope,
                            "commercial_use": {
                                "type": "object",
                                "required": ["status", "notes"],
                                "properties": {"status": {"enum": ["blocked", "review_required", "allowed"]}, "notes": {"type": "string"}},
                            },
                        },
                    },
                    "security": {"type": "object"},
                    "install": {"type": "object"},
                    "verification": {"type": "object"},
                    "documentation_urls": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": "^https://"}, "uniqueItems": True},
                },
            }
        },
    }


def snapshot_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/catalog-snapshot.schema.json",
        "title": "Volatile GitHub metadata snapshot",
        "type": "object",
        "additionalProperties": False,
        "required": ["$schema", "schema_version", "snapshot_date", "source", "records"],
        "properties": {
            "$schema": {"const": f"{SCHEMA_BASE}/catalog-snapshot.schema.json"},
            "schema_version": {"const": "1.0.0"},
            "snapshot_date": {"type": "string", "format": "date"},
            "source": {"type": "string"},
            "records": {
                "type": "array",
                "minItems": 163,
                "maxItems": 163,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "stars", "archived", "latest_release", "last_activity", "retrieval"],
                    "properties": {
                        "id": {"type": "string"},
                        "stars": {"type": ["integer", "null"], "minimum": 0},
                        "archived": {"type": ["boolean", "null"]},
                        "latest_release": {"type": ["string", "null"]},
                        "last_activity": {"type": ["string", "null"]},
                        "retrieval": {
                            "enum": [
                                "approximate-source-snapshot",
                                "github-api",
                                "not-recorded",
                            ]
                        },
                    },
                },
            },
        },
    }


def recipe_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/recipe.schema.json",
        "title": "Codex AI Game Studio production recipe",
        "type": "object",
        "additionalProperties": False,
        "required": ["$schema", "schema_version", "id", "title", "description", "inputs", "ordered_stages", "required_capabilities", "expected_artifacts", "quality_gates", "fallbacks", "provenance_outputs", "mutation_policy"],
        "properties": {
            "$schema": {"const": f"{SCHEMA_BASE}/recipe.schema.json"},
            "schema_version": {"const": "1.0.0"},
            "id": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "inputs": {"type": "array", "minItems": 1, "items": {"type": "string"}, "uniqueItems": True},
            "ordered_stages": {"type": "array", "minItems": 2, "items": {"type": "object", "required": ["order", "id", "action"], "properties": {"order": {"type": "integer", "minimum": 1}, "id": {"type": "string"}, "action": {"type": "string"}}}},
            "required_capabilities": {"type": "array", "minItems": 1, "items": {"type": "string"}, "uniqueItems": True},
            "expected_artifacts": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "quality_gates": {"type": "array", "minItems": 7, "items": {"type": "object", "required": ["id", "description", "human_required"], "properties": {"id": {"type": "string"}, "description": {"type": "string"}, "human_required": {"type": "boolean"}}}},
            "fallbacks": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "provenance_outputs": {"type": "array", "minItems": 1, "items": {"type": "string"}, "uniqueItems": True},
            "mutation_policy": {"const": "plan-confirmed-digest-before-apply"},
        },
    }


def write_recipes(output_root: Path) -> None:
    recipe_root = output_root.parent / "recipes"
    dump(recipe_root / "schema" / "recipe.schema.json", recipe_schema())
    index_entries = []
    for definition in RECIPE_DEFINITIONS:
        quality_gates = list(COMMON_GATES)
        quality_gates.extend({"id": f"specific-{index + 1}", "description": gate, "human_required": False} for index, gate in enumerate(definition["specific_gates"]))
        recipe = {
            "$schema": f"{SCHEMA_BASE}/recipe.schema.json",
            "schema_version": "1.0.0",
            "id": definition["id"],
            "title": definition["title"],
            "description": f"A reversible, evidence-producing workflow for {definition['title'].lower()}.",
            "inputs": definition["inputs"],
            "ordered_stages": [{"order": index, "id": stage_id, "action": action} for index, (stage_id, action) in enumerate(definition["stages"], start=1)],
            "required_capabilities": definition["capabilities"],
            "expected_artifacts": definition["artifacts"],
            "quality_gates": quality_gates,
            "fallbacks": definition["fallbacks"],
            "provenance_outputs": ["source-input-hashes.json", "generation-settings.json", "dependency-pins.json", "quality-evidence/", "human-approval.json"],
            "mutation_policy": "plan-confirmed-digest-before-apply",
        }
        filename = f"{definition['id']}.recipe.json"
        dump(recipe_root / filename, recipe)
        index_entries.append({"id": definition["id"], "title": definition["title"], "path": filename})
    dump(recipe_root / "index.json", {"schema_version": "1.0.0", "recipe_count": len(index_entries), "recipes": index_entries})


def main() -> int:
    parser = argparse.ArgumentParser()
    default_source = Path(__file__).resolve().parents[4] / "sources" / "AI_GAME_GENERATION_GITHUB_LANDSCAPE.md"
    parser.add_argument("--source", type=Path, default=default_source, help="Verified Markdown landscape")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1], help="Catalog output directory")
    parser.add_argument("--check", action="store_true", help="Regenerate in a temporary directory and fail if checked-in outputs differ")
    args = parser.parse_args()
    if not args.source.is_file():
        raise SystemExit(f"verified source snapshot not found: {args.source}")
    records, approximate_stars = parse_source(args.source)
    if len(records) != 163:
        raise SystemExit(f"expected 163 unique repositories, found {len(records)}")
    checked_in_output = args.output.resolve()
    temporary = tempfile.TemporaryDirectory(prefix="ai-game-studio-catalog-") if args.check else None
    output = Path(temporary.name) / "catalog" if temporary is not None else checked_in_output
    catalog = {
        "$schema": f"{SCHEMA_BASE}/catalog.schema.json",
        "schema_version": "1.0.0",
        "catalog_version": f"{VERIFIED_DATE}.1",
        "provenance": {
            "source_path": "workspace-source:docs/AI_GAME_GENERATION_GITHUB_LANDSCAPE.md",
            "source_sha256": EXPECTED_SHA256,
            "snapshot_date": VERIFIED_DATE,
            "record_count": 163,
            "policy": "Stable human curation only. Volatile GitHub metadata is stored in snapshots/ and is never used as a license grant or installation authorization.",
        },
        "records": records,
    }
    snapshot_records = []
    for record in records:
        key = record["repository"]["full_name"].lower()
        stars = approximate_stars.get(key)
        snapshot_records.append({
            "id": record["id"],
            "stars": stars,
            "archived": True if record["maturity"] == "archived" else None,
            "latest_release": None,
            "last_activity": None,
            "retrieval": "approximate-source-snapshot" if stars is not None else "not-recorded",
        })
    snapshot = {
        "$schema": f"{SCHEMA_BASE}/catalog-snapshot.schema.json",
        "schema_version": "1.0.0",
        "snapshot_date": VERIFIED_DATE,
        "source": "Approximate values explicitly present in the verified landscape; missing fields remain null until a reviewed refresh.",
        "records": snapshot_records,
    }
    dump(output / "schemas" / "catalog.schema.json", catalog_schema())
    dump(output / "schemas" / "catalog-snapshot.schema.json", snapshot_schema())
    dump(output / "catalog.json", catalog)
    dump(output / "snapshots" / f"github-{VERIFIED_DATE}.json", snapshot)
    dump(output / "provenance.json", catalog["provenance"])
    write_recipes(output)
    if temporary is not None:
        mismatches: list[str] = []
        for generated_root, checked_in_root in (
            (output, checked_in_output),
            (output.parent / "recipes", checked_in_output.parent / "recipes"),
        ):
            for generated_path in sorted(path for path in generated_root.rglob("*") if path.is_file()):
                relative = generated_path.relative_to(generated_root)
                checked_in_path = checked_in_root / relative
                if not checked_in_path.is_file():
                    mismatches.append(f"missing checked-in file: {checked_in_path}")
                elif generated_path.read_bytes() != checked_in_path.read_bytes():
                    mismatches.append(f"generated output differs: {checked_in_path}")
        temporary.cleanup()
        if mismatches:
            raise SystemExit("catalog determinism check failed:\n- " + "\n- ".join(mismatches))
        print(f"catalog determinism check passed for {len(records)} records and {len(RECIPE_DEFINITIONS)} recipes")
        return 0
    print(f"wrote {len(records)} stable records, {len(snapshot_records)} snapshot records, and {len(RECIPE_DEFINITIONS)} recipes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
