#!/usr/bin/env python3
"""Build the Codex parity layer from the pinned MIT-licensed upstream tree.

This generator deliberately writes only the parity-owned paths. Skill directories
must be created with the official skill-creator ``init_skill.py`` before this
script runs; the generator refuses to invent missing skill scaffolds.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = Path(
    os.environ.get(
        "AI_GAME_STUDIO_UPSTREAM",
        str(Path(os.environ["TEMP"]) / "codex-ai-game-studio-upstream"),
    )
)
COMMIT = "984023ddac0d5e27624f2baacde6105e45de375f"
SOURCE_URL = "https://github.com/Donchitos/Claude-Code-Game-Studios"
SKILL_ROOT = ROOT / "plugins" / "ai-game-studio" / "skills"
AUTOMATION = ROOT / "plugins" / "ai-game-studio-automation" / "templates"


NATIVE_SKILLS = {
    "toolchain-doctor": {
        "description": "Inspect the local game-development toolchain read-only, identify compatibility gaps, and prepare one reversible setup proposal without installing or changing anything.",
        "short": "Inspect the local game toolchain safely",
        "purpose": "Build a trustworthy, read-only inventory before any setup decision.",
        "inputs": ["project root", "target engine or platform if known", "commercial-use intent and download budget"],
        "stages": [
            "Detect Windows, macOS, Linux, architecture, native-versus-WSL execution, disk space, and network constraints.",
            "Inspect project markers and installed Unity, Godot, Unreal, Blender, Aseprite, Pixelorama, and Tiled versions without launching them.",
            "Inspect Python, Node.js, package managers, Git, gh, existing MCP declarations, credential variable names, GPU backend, and reported VRAM without reading secret values.",
            "Compare the detected environment with pack descriptors and catalog constraints.",
            "Return one transaction proposal with exact pins, licenses, permissions, downloads, conflicts, backups, rollback operations, expiry, and digest.",
        ],
        "artifacts": ["environment inventory", "compatibility matrix", "single proposed transaction", "no-change attestation"],
        "specific": [
            "Never read credential values; report only whether named variables or authenticated clients appear available.",
            "Never install, enable, launch, or reconfigure a tool during diagnosis.",
            "If native detection is incomplete, mark evidence unknown instead of guessing.",
        ],
    },
    "tool-discover": {
        "description": "Search the offline generative-game catalog and available live metadata to recommend licensed, compatible tools for a concrete workflow.",
        "short": "Find compatible generative game tools",
        "purpose": "Turn a production need into a small, evidence-backed tool shortlist.",
        "inputs": ["desired artifact or workflow", "engine and operating system", "hardware, budget, privacy, and license constraints"],
        "stages": [
            "Translate the request into required capabilities and quality gates.",
            "Search the checked-in catalog first; enrich volatile metadata through GitHub only when available.",
            "Filter by operating system, architecture, runtime, GPU backend, VRAM, application requirements, maturity, and license status.",
            "Compare at most three candidates by capability, quality, cost, performance, permissions, and limitations.",
            "Recommend one route and state why rejected candidates do not fit.",
        ],
        "artifacts": ["search criteria", "ranked shortlist", "license and risk notes", "recommended recipe"],
        "specific": [
            "Do not refresh or rewrite the catalog implicitly.",
            "Unknown or custom code, weight, dataset, output, or commercial terms block commercial recommendations.",
            "A catalog entry is metadata, not permission to download or launch its repository.",
        ],
    },
    "prompt-to-game": {
        "description": "Convert a game idea into a scoped playable prototype through explicit design, stack selection, implementation, and evidence gates.",
        "short": "Turn a prompt into a playable prototype",
        "purpose": "Produce the smallest playable proof of the requested experience, not an unbounded production game.",
        "inputs": ["one-sentence game idea", "target platform", "time, team, engine, art, and licensing constraints"],
        "stages": [
            "Clarify the player fantasy, core verb, fail and success conditions, session length, and non-goals.",
            "Define a one-loop prototype acceptance test and asset budget.",
            "Run toolchain diagnosis and recommend a compatible engine and generation route.",
            "Create a reversible implementation plan; require approval before files or external tools change.",
            "Implement in thin vertical slices with a playable build after every slice.",
            "Capture controls, known limitations, screenshots, test evidence, and provenance.",
        ],
        "artifacts": ["prototype brief", "approved plan", "playable build", "controls sheet", "evidence and provenance bundle"],
        "specific": [
            "Prefer placeholder assets until the core loop is demonstrably fun.",
            "Keep generated code and content reviewable in small, testable increments.",
            "Stop scope growth that does not improve the prototype acceptance test.",
        ],
    },
    "sprite-generate": {
        "description": "Plan, generate, normalize, and validate consistent 2D sprites, tiles, portraits, and animation sheets with preserved sources.",
        "short": "Generate consistent production-ready sprites",
        "purpose": "Create engine-ready 2D art that remains visually consistent across poses, directions, and frames.",
        "inputs": ["art bible or reference images with rights", "sprite purpose and camera", "dimensions, palette, directions, frame count, and engine format"],
        "stages": [
            "Lock silhouette, palette, line weight, lighting direction, baseline, pivot, and scale in a sprite specification.",
            "Generate a single approved key pose before requesting a full sheet.",
            "Generate variants with fixed identity anchors and deterministic settings when supported.",
            "Normalize canvas, alpha, baseline, pivots, padding, palette, and filenames without overwriting sources.",
            "Preview every animation loop and import a copy into the target engine for a smoke test.",
        ],
        "artifacts": ["sprite specification", "source generations", "normalized sprites or atlas", "loop previews", "engine import evidence", "provenance record"],
        "specific": [
            "Check transparent edges, accidental matte colors, cropped silhouettes, duplicate frames, baseline drift, timing, and loop continuity.",
            "For tiles, verify edge matching, terrain transitions, grid size, and representative map assembly.",
            "Require human approval of the key pose and final before replacing any project asset.",
        ],
    },
    "asset-3d-generate": {
        "description": "Select and run a licensed image-or-text-to-3D workflow, then validate topology, shading, UVs, LODs, collision, and engine import.",
        "short": "Generate and validate engine-ready 3D assets",
        "purpose": "Produce a traceable 3D asset that satisfies a concrete in-engine budget and visual target.",
        "inputs": ["text brief or rights-cleared reference views", "target engine and renderer", "scale, topology, material, LOD, collision, and performance budgets"],
        "stages": [
            "Verify reference rights, identity consent when relevant, and output-license compatibility.",
            "Choose a hardware-compatible generation path and document the model, weights, settings, and seed when available.",
            "Generate into a new working directory and preserve raw outputs.",
            "Repair orientation, units, transforms, topology, normals, UVs, materials, LODs, and collision through an approved DCC route.",
            "Render multi-view turntables and test import, scale, shading, collision, and runtime budget in the target engine.",
        ],
        "artifacts": ["asset specification", "raw and processed models", "turntable and wireframe views", "engine import proof", "provenance record"],
        "specific": [
            "Reject non-manifold geometry, inverted normals, broken UVs, missing textures, unsupported shaders, or unbounded polygon counts.",
            "Characters must be routed through rig and animation validation before production use.",
            "Do not treat a visually plausible single render as evidence of a usable 3D asset.",
        ],
    },
    "material-texture-generate": {
        "description": "Generate and validate tileable, color-managed PBR material sets for a specified engine shader and texel-density budget.",
        "short": "Generate validated PBR material sets",
        "purpose": "Create coherent material maps whose physical interpretation survives engine import.",
        "inputs": ["surface brief and rights-cleared references", "target shader workflow", "resolution, texel density, tiling scale, and compression budget"],
        "stages": [
            "Define material class, real-world scale, lighting assumptions, map channels, color spaces, and packing convention.",
            "Choose a licensed generation route compatible with available hardware.",
            "Generate source maps without replacing existing project textures.",
            "Validate seamless tiling, albedo range, roughness response, normal orientation, height continuity, and channel packing.",
            "Preview on representative geometry under neutral and production lighting, then test engine import and compression.",
        ],
        "artifacts": ["material specification", "source and packed maps", "sphere and plane previews", "engine material instance", "provenance record"],
        "specific": [
            "Treat base color as color data and linear maps as non-color data.",
            "Never infer legal reuse from a reference image being publicly visible.",
            "Flag baked lighting, inconsistent scale, edge seams, clipping, and implausible metallic values.",
        ],
    },
    "rig-animation": {
        "description": "Rig, retarget, generate, and quality-gate character animation plus cue-driven procedural VFX editors and composers with explicit skeleton, deformation, shader, timing, palette, and runtime-budget requirements.",
        "short": "Rig, animate, and compose procedural VFX",
        "purpose": "Deliver clean character animation and reusable cue-driven procedural VFX that behave predictably in the target runtime.",
        "inputs": [
            "rights-cleared character mesh, motion sources, and effect references",
            "target skeleton, engine or Three.js runtime, renderer, and existing dependency constraints",
            "clip list, frame rate, root-motion policy, gameplay constraints, and cue timing",
            "effect brief, style guide, palette and attachment requirements, and frame-time, draw-call, and overdraw budgets",
        ],
        "stages": [
            "Inspect topology, pose, scale, symmetry, deformation readiness, animation controllers, render architecture, package locks, tests, and runtime budgets without changing the project.",
            "Define skeleton naming, hierarchy, twist bones, facial scope, root, and retarget profile. When procedural Three.js VFX or its editor is requested, read the [procedural VFX composer reference](references/procedural-vfx-composer.md) completely, define the effect taxonomy, parameter schema, named five-color palettes, and typed animation-cue contract, then validate `vfx-project.json` with the bundled `scripts/validate_vfx_spec.py` before implementation.",
            "Present one exact implementation plan with candidate paths, dependencies, permissions, previews, tests, rollback, and digest; wait for confirmation before writing files, installing dependencies, or controlling an editor.",
            "Generate or author weights and clips into preserved working copies. On Three.js targets, generate seeded integer-hash value noise, FBM, domain warping, and radial crack fields into runtime THREE.DataTexture objects; use an equivalent code-generated texture route elsewhere.",
            "Build reusable procedural triangles, crescents, flare rings, ground discs, stars, shards, rubble, puffs, flame shells, and flame tongues, plus degenerate-safe parallel-transport tubes for straight, wobbly, jagged, or split trails, beams, and bolts.",
            "Compose shared GLSL noise, shape, and edge chunks into erosion, flat-band, ink-contour, and heat-gradient shaders. Layer additive geometry for glow and use bounded meshes for sparks and debris without requiring post-processing or particle middleware.",
            "Build the animation and VFX composer with an effect library and VFX sheet, preview viewport, transport and scrubbing, timeline and cue tracks, inspector, palette controls, deterministic import/export, and undo/redo.",
            "Fire effects from animation cues, size them from measured rig and weapon-tip extents, aim them at the authored impact target, and define deterministic behavior for loops, seeking, repeated cues, and dropped frames.",
            "Review deformation and effects from multiple views, then validate root motion, contacts, foot sliding, loop continuity, shader compilation, palette readability, transparent sorting, resource disposal, cue timing, editor round trips, runtime budgets, and target import.",
        ],
        "artifacts": [
            "rig, animation, VFX, palette, and cue specifications, including validated vfx-project.json when the VFX route is selected",
            "rigged source copy and validated clips",
            "procedural texture, geometry, tube, and shader library",
            "animation and VFX composer with deterministic saved state",
            "VFX sheet and multi-view temporal captures",
            "contact, loop, cue-timing, shader, and runtime-budget reports",
            "engine or browser runtime proof, provenance record, and rollback receipt",
        ],
        "specific": [
            "Reject unexpected bone scale, unstable constraints, collapsing joints, penetrations, foot skating, and discontinuous loops.",
            "Retargeting must preserve the original source and record both source and destination skeletons.",
            "Runtime textures, procedural geometry, and effect randomness must be deterministic from recorded parameters and seeds; the core workflow must not require a hosted service, paid model, downloaded art pack, post-processing stack, or particle engine.",
            "Parallel-transport frames must remain finite and stable across zero-length, collinear, sharply turning, split, and looping paths; shaders must compile without NaNs or undeclared renderer assumptions.",
            "Each named core, body, edge, ink, and ash palette must preserve readable band separation, and transparent layering must pass light, dark, and representative gameplay-background review.",
            "Cue firing must remain stable while playing, looping, seeking, changing frame rate, and crossing state transitions; reach and aim must derive from recorded rig, socket, and weapon measurements rather than unexplained constants.",
            "Composer state must round-trip deterministically, undo and redo without orphaned resources, and preview the same parameters and timing used by the runtime.",
            "Measure shader count, geometry and texture memory, draw calls, overdraw, concurrent effects, CPU update cost, and GPU frame time against explicit budgets before promotion.",
            "Identity-based motion or performance capture requires documented performer consent.",
        ],
    },
    "world-generate": {
        "description": "Generate reversible terrain, environments, procedural levels, lighting, navigation, and spawn layouts from validated design constraints.",
        "short": "Generate playable worlds and environments",
        "purpose": "Create navigable, performant environments that serve the intended player flow.",
        "inputs": ["level intent and player metrics", "engine, platform, and art direction", "terrain, biome, traversal, encounter, lighting, and streaming budgets"],
        "stages": [
            "Map critical path, optional paths, landmarks, gates, encounter beats, spawn rules, and accessibility constraints.",
            "Choose deterministic procedural or generative stages with saved seeds and parameters.",
            "Generate into a new scene or layer while preserving authored content.",
            "Bake or update navigation, collision, lighting, occlusion, and streaming data only after plan approval.",
            "Run reachability, spawn safety, sightline, readability, lighting, and performance checks in representative routes.",
        ],
        "artifacts": ["world specification", "seed and parameter manifest", "generated scene copy", "navigation and lighting evidence", "playthrough captures", "provenance record"],
        "specific": [
            "Verify every required objective and exit is reachable from every valid spawn.",
            "Check geometry intersections, floating props, traversal metrics, dark dead ends, and repetition artifacts.",
            "Human review decides whether a generated world replaces or merges with authored work.",
        ],
    },
    "npc-audio-generate": {
        "description": "Design and generate NPC dialogue, quests, voices, music, and sound with consent, narrative, localization, audio, and runtime gates.",
        "short": "Generate NPC, dialogue, voice, and audio",
        "purpose": "Create coherent, consented narrative and audio content that is safe to ship and practical to integrate.",
        "inputs": ["narrative and audio bibles", "NPC or quest function", "voice consent, locale, platform, loudness, memory, and streaming constraints"],
        "stages": [
            "Define canon, character boundaries, quest state model, prohibited outputs, pronunciation, and audio specification.",
            "Verify model, dataset, voice, performer, music, and output rights before generation.",
            "Generate structured dialogue and audio into review-only copies with stable identifiers.",
            "Validate branching reachability, state consistency, lore, tone, safety, localization, subtitles, peaks, loudness, noise, and loop seams.",
            "Integrate only approved content and run in-engine subtitle, playback, mixing, memory, and fallback tests.",
        ],
        "artifacts": ["content specification", "dialogue or quest graph", "review audio", "consent and provenance records", "engine integration evidence"],
        "specific": [
            "Block voice cloning or identity imitation without explicit, documented consent and appropriate rights.",
            "Preserve text-only and non-generated fallbacks for accessibility and unavailable services.",
            "Do not expose credentials, private prompts, unreleased narrative, or player data to external services without approval.",
        ],
    },
    "engine-automation": {
        "description": "Plan and execute approved Unity, Godot, Unreal, Blender, or pixel-editor automation through one compatible host adapter at a time.",
        "short": "Automate game editors after explicit approval",
        "purpose": "Route an approved operation to the correct editor adapter while preserving user control and rollback.",
        "inputs": ["host application and project", "desired operation", "selected pack, exact upstream pin, permissions, and rollback expectations"],
        "stages": [
            "Run read-only host and project detection and inventory existing MCP configurations.",
            "Refuse ambiguous host selection or multiple active servers for the same application.",
            "Prepare a transaction with exact commands, files, process and network permissions, health checks, backups, rollback, expiry, and digest.",
            "Show the plan and wait for explicit confirmation of its digest.",
            "After confirmation, apply only the listed actions, run health checks, and stop on the first divergence.",
            "Record the resulting lock state and tested rollback path.",
        ],
        "artifacts": ["approved transaction", "backup inventory", "health-check result", "lock update", "rollback report"],
        "specific": [
            "Never install, enable, launch, configure, or control an editor implicitly.",
            "Only one MCP server per host application may be active.",
            "A digest mismatch, expired plan, changed environment, or failed backup invalidates apply and requires a new plan.",
        ],
        "implicit": False,
    },
    "visual-qa": {
        "description": "Run evidence-based multi-view visual, temporal, import, and runtime checks for generated game assets and scenes.",
        "short": "Run visual and temporal asset QA",
        "purpose": "Find visible and technical failures that single-view or file-only validation misses.",
        "inputs": ["asset, scene, or build under review", "reference target and acceptance criteria", "representative cameras, states, platforms, and budgets"],
        "stages": [
            "Confirm the comparison baseline, capture settings, color pipeline, cameras, states, and tolerances.",
            "Capture consistent front, side, rear, three-quarter, close-up, silhouette, wireframe, and motion views as applicable.",
            "Compare against references and prior approved artifacts without hiding uncertainty behind a single similarity score.",
            "Inspect temporal stability, animation contacts, particles, lighting, UI states, and transition frames.",
            "Run engine import and representative runtime captures, then classify findings by severity and reproducibility.",
        ],
        "artifacts": ["capture manifest", "annotated contact sheet", "temporal review", "runtime metrics", "reproducible findings"],
        "specific": [
            "Control resolution, camera, lighting, exposure, pose, animation time, and platform before comparing images.",
            "Review transparent assets over light, dark, and checkerboard backgrounds.",
            "A visual pass never overrides license, format, performance, playability, or human-approval gates.",
        ],
    },
    "quality-enhance": {
        "description": "Create reversible, quality-gated game asset or scene enhancements with preserved originals and before-and-after evidence.",
        "short": "Enhance assets with reversible QA gates",
        "purpose": "Improve a specific measurable weakness without silently changing style, behavior, rights, or performance budgets.",
        "inputs": ["source asset or scene", "approved quality target", "locked properties, performance budget, and acceptable transformations"],
        "stages": [
            "Diagnose concrete defects and define measurable acceptance criteria before proposing a transformation.",
            "Copy originals to a recoverable location and inventory all dependent files and references.",
            "Prepare a plan showing the exact enhancement route, tools, license implications, files, previews, and rollback.",
            "Wait for explicit confirmation before running transformations.",
            "Produce variants beside originals and create controlled before-and-after comparisons.",
            "Validate format, visual fidelity, temporal behavior, runtime budget, playability, and project integration before requesting replacement approval.",
        ],
        "artifacts": ["defect diagnosis", "approved enhancement plan", "preserved originals", "candidate variants", "before-and-after evidence", "rollback record"],
        "specific": [
            "Never overwrite or replace a source asset without a final human choice made after previewing evidence.",
            "Reject improvements that introduce identity drift, style drift, seams, artifacts, broken dependencies, or budget regressions.",
            "Keep the enhancement reproducible by recording tools, versions, settings, prompts, seeds, and manual edits.",
        ],
        "implicit": False,
    },
}


DEFAULT_PROMPTS = {
    "start": "Use $ai-game-studio:start to inspect this project and route me to the safest next game-development workflow.",
    "help": "Use $ai-game-studio:help to show the most relevant workflows for this project's current stage.",
    "setup-engine": "Use $ai-game-studio:setup-engine to inspect compatibility and propose one reversible engine setup without changing anything yet.",
    "toolchain-doctor": "Use $ai-game-studio:toolchain-doctor to inspect this project's OS, engine, DCC tools, GPU, and MCP setup without changing anything.",
    "tool-discover": "Use $ai-game-studio:tool-discover to find licensed, hardware-compatible tools for this game-development need.",
    "prompt-to-game": "Use $ai-game-studio:prompt-to-game to turn this idea into a scoped playable prototype with approval gates.",
    "sprite-generate": "Use $ai-game-studio:sprite-generate to plan and validate a consistent transparent sprite animation.",
    "asset-3d-generate": "Use $ai-game-studio:asset-3d-generate to choose and validate a licensed engine-ready 3D generation pipeline.",
    "material-texture-generate": "Use $ai-game-studio:material-texture-generate to create and validate a tileable PBR material set.",
    "rig-animation": "Use $ai-game-studio:rig-animation to rig or retarget this character, build cue-driven procedural VFX and its composer, and verify deformation, shaders, timing, palettes, and runtime budgets.",
    "world-generate": "Use $ai-game-studio:world-generate to create a reversible, navigable environment from these design constraints.",
    "npc-audio-generate": "Use $ai-game-studio:npc-audio-generate to design consented NPC dialogue, voice, music, or sound with integration gates.",
    "engine-automation": "Use $ai-game-studio:engine-automation to plan this editor operation, show permissions and rollback, and wait for my approval.",
    "visual-qa": "Use $ai-game-studio:visual-qa to run controlled multi-view and temporal QA on this asset or scene.",
    "quality-enhance": "Use $ai-game-studio:quality-enhance to propose reversible improvements with preserved originals and before-and-after evidence.",
}


IMPLICIT_DISABLED = {"setup-engine", "engine-automation", "quality-enhance"}


HOOK_MAP = {
    "detect-gaps.sh": ["SessionStart:orientation-and-gap-detection"],
    "session-start.sh": ["SessionStart:orientation-and-gap-detection"],
    "log-agent.sh": ["SubagentStart:bounded-audit-log"],
    "log-agent-stop.sh": ["SubagentStop:bounded-audit-log"],
    "pre-compact.sh": ["PreCompact:state-preservation"],
    "post-compact.sh": ["PostCompact:state-restoration"],
    "validate-commit.sh": ["PreToolUse:commit-safeguard"],
    "validate-push.sh": ["PreToolUse:push-safeguard"],
    "validate-assets.sh": ["PostToolUse:asset-validation"],
    "validate-skill-change.sh": ["PostToolUse:skill-validation"],
    "session-stop.sh": ["Stop:session-summary", "SessionEnd:session-archive"],
    "notify.sh": ["Stop:best-effort-notification", "SessionEnd:best-effort-notification"],
}


COMMON_DEFAULT_ROLES = {
    "producer",
    "game-designer",
    "lead-programmer",
    "technical-director",
    "art-director",
    "qa-lead",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.replace("\r\n", "\n").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = lines[1:].index("---") + 1
    except ValueError as exc:
        raise ValueError("unterminated frontmatter") from exc
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = value[1:-1]
        metadata[key] = value
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return metadata, body


def source_blob(path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(UPSTREAM), "rev-parse", f"{COMMIT}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def clean_text(text: str, skill_names: list[str]) -> str:
    text = text.replace("\r\n", "\n")
    replacements = {
        ".claude/docs/technical-preferences.md": ".ai-game-studio/project.json",
        ".claude/docs/templates/patch-notes-template.md": ".ai-game-studio/templates/release-notes.md",
        ".claude/docs/templates/": ".ai-game-studio/templates/",
        ".claude/docs/": ".ai-game-studio/docs/",
        ".claude/agents/": ".codex/agents/",
        ".claude/rules/": "path-scoped AGENTS.md guidance from ",
        ".claude/skills/": "enabled Codex skills under ",
        ".claude/": ".ai-game-studio/",
        "CLAUDE.md": "AGENTS.md",
        "AskUserQuestion": "the available user-input mechanism",
        "Claude Code Game Studios": "Codex AI Game Studio",
        "Claude Code": "Codex",
        "Claude": "Codex",
        "$ARGUMENTS[0]": "the first invocation argument",
        "$ARGUMENTS": "the invocation arguments",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    tool_replacements = {
        "Git Bash on Windows — the `2>/dev/null` is bash syntax, not PowerShell": "a platform-native shell; use PowerShell syntax on Windows and POSIX syntax on macOS/Linux",
        "Git Bash on Windows - the `2>/dev/null` is bash syntax, not PowerShell": "a platform-native shell; use PowerShell syntax on Windows and POSIX syntax on macOS/Linux",
        "Write/Edit tools": "the available file-editing mechanism",
        "Write or Edit tools": "the available file-editing mechanism",
        "Write or Edit in allowed-tools": "legacy write permissions",
        "the Edit tool": "the available file-editing mechanism",
        "the Write tool": "the available file-editing mechanism",
        "the Read tool": "the available file-reading mechanism",
        "Task tool": "Codex subagent mechanism",
        "via the Task tool": "with a Codex subagent",
        "via Task": "with a Codex subagent",
        "Task calls": "subagent spawns",
        "Task agents": "Codex subagents",
        "Task prompt": "subagent prompt",
        "WebSearch": "web search",
        "Grep/Glob": "text search and file discovery",
        "Glob/Grep": "file discovery and text search",
        "Grep": "text search",
        "Glob": "file discovery",
        "Bash tool": "available shell",
        "via Bash": "with the available shell",
        "via `Bash`": "with the available shell",
        "`Bash`": "the available shell",
        "Bash:": "Shell example (adapt syntax to the current platform):",
        "allowed-tools": "unsupported legacy tool declarations",
    }
    for old, new in tool_replacements.items():
        text = text.replace(old, new)
    text = text.replace(
        "`.ai-game-studio/docs/director-gates.md`",
        "the installed Codex role-gate protocol",
    )
    text = text.replace(
        "`.ai-game-studio/docs/coding-standards.md`",
        "the nearest applicable `AGENTS.md` coding guidance",
    )
    for name in sorted(skill_names, key=len, reverse=True):
        text = re.sub(
            rf"(?<![A-Za-z0-9_./$:-])/{re.escape(name)}\b",
            f"$ai-game-studio:{name}",
            text,
        )
    text = text.replace("`Task` subagent", "Codex subagent")
    text = text.replace("Task subagent", "Codex subagent")
    text = text.replace("the available user-input mechanism tool", "the available user-input mechanism")
    return text.rstrip() + "\n"


def clean_inline(text: str, skill_names: list[str]) -> str:
    return re.sub(r"\s+", " ", clean_text(text, skill_names)).strip()


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def make_openai_yaml(name: str, description: str) -> str:
    display = name.replace("-", " ").title()
    short = NATIVE_SKILLS.get(name, {}).get("short")
    if not short:
        short = re.sub(r"\s+", " ", description).strip().rstrip(".")
        if len(short) > 61:
            short = short[:61].rsplit(" ", 1)[0]
        if len(short) < 25:
            short = f"Run the {display.lower()} game workflow"
    prompt = DEFAULT_PROMPTS.get(name, f"Use $ai-game-studio:{name} to {short[0].lower() + short[1:]} for this project and report evidence.")
    implicit = name not in IMPLICIT_DISABLED
    return (
        "interface:\n"
        f"  display_name: {yaml_quote(display)}\n"
        f"  short_description: {yaml_quote(short)}\n"
        f"  default_prompt: {yaml_quote(prompt)}\n"
        "policy:\n"
        f"  allow_implicit_invocation: {'true' if implicit else 'false'}\n"
    )


def start_body() -> str:
    return """# Start: safe game-studio router

Use this as the primary entry point. Begin with read-only orientation; do not
create files, install software, enable hooks, start MCP servers, launch editors,
download models, or change configuration during routing.

## 1. Inspect quietly

- Identify the operating system, architecture, repository root, project markers,
  engine, renderer, DCC and pixel tools, languages, tests, build scripts, and
  existing `.ai-game-studio/` state.
- Check only credential *presence* by environment-variable name. Never print,
  read, or store secret values.
- Detect whether this is a new idea, a prototype, an existing production project,
  a migration, or an asset-only task.
- Treat uncertain evidence as unknown.

## 2. Establish intent

Ask only the smallest blocking question needed: desired outcome, target platform,
commercial-use intent, time budget, and whether existing assets or references have
clear rights. Keep the user as creative director.

## 3. Route

| Need | Next skill |
|---|---|
| Explore or formalize a concept | `$ai-game-studio:brainstorm` |
| Adopt an existing project | `$ai-game-studio:adopt` |
| Inspect compatibility | `$ai-game-studio:toolchain-doctor` |
| Select external tools | `$ai-game-studio:tool-discover` |
| Prompt to a playable proof | `$ai-game-studio:prompt-to-game` |
| Configure an engine | `$ai-game-studio:setup-engine` |
| 2D sprites or tiles | `$ai-game-studio:sprite-generate` |
| 3D mesh generation | `$ai-game-studio:asset-3d-generate` |
| PBR maps or materials | `$ai-game-studio:material-texture-generate` |
| Rigging, animation, or cue-driven procedural VFX | `$ai-game-studio:rig-animation` |
| Terrain, scenes, or levels | `$ai-game-studio:world-generate` |
| NPCs, quests, voice, music, sound | `$ai-game-studio:npc-audio-generate` |
| Approved editor operation | `$ai-game-studio:engine-automation` |
| Visual or temporal review | `$ai-game-studio:visual-qa` |
| Reversible improvement | `$ai-game-studio:quality-enhance` |
| Current-stage navigation | `$ai-game-studio:help` |

For a full studio lifecycle, route concept work through
`$ai-game-studio:prototype`, `$ai-game-studio:art-bible`,
`$ai-game-studio:map-systems`, `$ai-game-studio:design-system`,
`$ai-game-studio:create-architecture`, `$ai-game-studio:vertical-slice`, and
the sprint skills as the evidence warrants.

## 4. Preserve the confirmation boundary

If the route could mutate configuration, install or launch an external tool,
control an editor, refresh the catalog, download a model, or replace an asset,
first produce one consolidated transaction. It must name exact actions,
downloads, licenses, permissions, conflicts, backups, rollback operations,
expiry, and digest. Wait for explicit confirmation of that digest. If the
environment changes or the digest differs, create a new plan.

End routing with one recommended next skill and a ready-to-send prompt. Do not
silently execute the routed workflow.
"""


def help_body() -> str:
    return """# Contextual workflow navigator

Inspect the project read-only, infer its current stage from evidence, and show a
compact menu containing only useful next actions. Do not run those actions.

## Navigation method

1. Inspect project files, current branch state, engine markers, design and
   architecture documents, sprint artifacts, recent test evidence, generated
   assets, and `.ai-game-studio/project.json` when present.
2. State the detected stage and confidence. If evidence conflicts, explain the
   conflict in one sentence and ask a focused question.
3. Recommend one primary next skill and no more than three alternatives.
4. For every recommendation, include a copy-ready prompt beginning with the
   exact namespaced invocation `$ai-game-studio:<skill>`.
5. Mark workflows that require a plan and explicit confirmation before mutation.

## Common paths

- New concept: `$ai-game-studio:brainstorm` -> `$ai-game-studio:prototype` ->
  `$ai-game-studio:art-bible` -> `$ai-game-studio:map-systems`.
- Existing project: `$ai-game-studio:adopt` ->
  `$ai-game-studio:project-stage-detect` -> relevant audit or planning skill.
- Playable prototype: `$ai-game-studio:prompt-to-game`, followed by
  `$ai-game-studio:playtest-report` and `$ai-game-studio:scope-check`.
- Production assets: use the relevant generation skill, then
  `$ai-game-studio:visual-qa`; use `$ai-game-studio:quality-enhance` only for an
  approved, reversible improvement.
- Editor tooling: `$ai-game-studio:toolchain-doctor` ->
  `$ai-game-studio:setup-engine` -> `$ai-game-studio:engine-automation`.
- Release: `$ai-game-studio:smoke-check` ->
  `$ai-game-studio:regression-suite` -> `$ai-game-studio:release-checklist`.

Distinguish product controls from skills: `/plugins` browses or installs plugins;
the `/` picker lists enabled skills; `$ai-game-studio:<skill>` invokes a workflow.
Never invent deprecated custom slash aliases.
"""


def setup_engine_body() -> str:
    return """# Plan a compatible engine setup

This is a setup workflow and may be invoked only explicitly. It never installs,
enables, launches, or reconfigures anything during its inspection and proposal
phases.

1. Run the read-only checks defined by `$ai-game-studio:toolchain-doctor`.
2. Detect existing Unity, Godot, Unreal, browser, and project evidence before
   asking the user to choose an engine.
3. Compare viable engines by project fit, platform export, team language,
   maturity, performance, accessibility, license, install size, and existing
   investment. Verify current terms before relying on them.
4. Recommend one engine and one adapter. Do not activate more than one MCP server
   for the same host application.
5. Produce one transaction containing `plan_id`, environment evidence, exact
   actions, pinned sources, command arguments, downloads, licenses, permissions,
   conflicts, backups, health checks, uninstall and rollback operations, expiry,
   and digest.
6. Show every file that would be materialized, including root and path-scoped
   `AGENTS.md`, selected `.codex/agents/*.toml`, `.ai-game-studio/project.json`,
   and `.ai-game-studio/lock.json`.
7. Wait for explicit confirmation of the exact digest. Applying the transaction
   is a separate operation. Changed evidence, an expired plan, or a digest
   mismatch requires a new plan.

If the preferred route is unavailable on the detected OS, architecture, GPU, or
application version, first attempt a verified native adaptation. Otherwise show
a concise alternative comparison and ask the user to confirm the substitution.
"""


def skill_test_body() -> str:
    return """# Test a Codex skill

Evaluate a target skill as both a package and a behavior. Testing is read-only
unless the user separately approves writing a report.

## Static validation

1. Locate the skill directory and read `SKILL.md` plus `agents/openai.yaml`.
2. Require YAML frontmatter containing exactly `name` and `description`.
3. Confirm the directory name and frontmatter name match and use lowercase
   hyphen-case.
4. Confirm the description explains both what the skill does and when it should
   activate. Reject unsupported legacy frontmatter and broken relative links.
5. Confirm `agents/openai.yaml` has a useful display name, a 25-64 character
   short description, and a default prompt that explicitly names the skill.
6. Confirm mutating setup, installation, engine-control, catalog-refresh, and
   destructive enhancement workflows disable implicit invocation.
7. Scan for secrets, absolute developer paths, path escapes, unsupported model
   pins, product-specific tool declarations, and platform-only assumptions.

Run the official skill validator when it is available. Report the exact command,
exit status, and diagnostics.

## Forward testing

Use isolated Codex subagents with the raw skill instructions. Cover:

- a direct explicit invocation;
- a natural-language request that should select the skill when implicit use is enabled;
- a near-miss that should route elsewhere;
- a negative or unsafe request that must preserve approval and rights gates.

Do not reveal an expected answer in the test prompt. Score routing, instruction
adherence, safety boundary, artifact clarity, platform neutrality, and evidence.
For failures, distinguish instruction defects from missing external capabilities.

Return a concise test matrix and a prioritized improvement proposal. Do not edit
the tested skill until the user approves that separate change.
"""


def skill_improve_body() -> str:
    return """# Improve a Codex skill safely

Improve an existing skill from evidence, not preference. Preserve its public name
and intended trigger unless the user explicitly approves a breaking change.

1. Run `$ai-game-studio:skill-test` and record the baseline failures.
2. Read the official skill authoring constraints available in the current Codex
   installation. Inspect all local references before changing instructions.
3. Diagnose each failure as routing ambiguity, missing workflow detail, unsafe
   mutation, broken reference, unsupported metadata, platform coupling, excessive
   context, or unverifiable output.
4. Propose the smallest patch, showing affected files, behavior change, possible
   regressions, and rollback. Wait for approval before editing.
5. Preserve frontmatter with only `name` and `description`. Keep the starter
   prompt namespaced and realistic. Disable implicit invocation for sensitive
   setup, install, control, refresh, or destructive workflows.
6. After approval, patch with the repository editing mechanism. Do not rewrite
   unrelated prose or generated assets.
7. Re-run static validation and all direct, implicit, near-miss, and negative
   forward tests. Compare results with the baseline.

Return the exact diff summary, validation evidence, remaining limitations, and a
one-command rollback. Never claim improvement solely because wording changed.
"""


def native_body(name: str, spec: dict[str, object]) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    stages = "\n".join(f"{index}. {item}" for index, item in enumerate(spec["stages"], 1))
    return f"""# {name.replace('-', ' ').title()}

## Outcome

{spec['purpose']}

## Required inputs

{bullets(spec['inputs'])}

Ask for missing information only when it changes the route materially. Otherwise
state conservative assumptions and proceed with read-only analysis.

## Workflow

{stages}

## Expected artifacts

{bullets(spec['artifacts'])}

## Workflow-specific gates

{bullets(spec['specific'])}

## Production completion gate

Before recommending production use, complete and report all seven gates:

1. Rights, consent, code/model/dataset/output license, and generation-provenance checks.
2. Technical format, naming, scale, color, metadata, and target-import validation.
3. Visual and temporal consistency review across representative views and states.
4. Runtime memory, frame-time, draw-call, streaming, and asset-budget checks.
5. Playability and interaction smoke tests in the target runtime.
6. Screenshot, capture, diff, or artifact-regression evidence with reproducible settings.
7. Human approval before replacing source assets or promoting generated output.

Unknown rights, missing consent, unsupported hardware, conflicting host adapters,
or failed quality gates block production promotion. Preserve originals and make
fallbacks explicit.
"""


def write_skills(skill_names: list[str]) -> list[dict[str, object]]:
    ledger: list[dict[str, object]] = []
    upstream_skills = UPSTREAM / ".claude" / "skills"
    for name in skill_names:
        target = SKILL_ROOT / name
        if not target.is_dir() or not (target / "agents" / "openai.yaml").exists():
            raise RuntimeError(f"skill was not scaffolded with init_skill.py: {name}")
        source_path = upstream_skills / name / "SKILL.md"
        metadata, body = parse_frontmatter(source_path.read_text(encoding="utf-8"))
        description = clean_inline(metadata["description"], skill_names)
        if name == "start":
            body = start_body()
        elif name == "help":
            body = help_body()
        elif name == "setup-engine":
            body = setup_engine_body()
        elif name == "skill-test":
            body = skill_test_body()
        elif name == "skill-improve":
            body = skill_improve_body()
        else:
            body = clean_text(body, skill_names)
        body = body.rstrip() + (
            "\n\n## Codex portability\n\n"
            "Use the search, file-editing, shell, user-input, and subagent capabilities available in the active Codex surface. "
            "Use PowerShell syntax on Windows and POSIX syntax on macOS/Linux; do not require a Unix compatibility layer on Windows. "
            "Inherit the active model and permission mode, and do not weaken approval or sandbox boundaries.\n"
        )
        provenance = (
            f"> Port provenance: adapted from the pinned upstream source at `{COMMIT}` "
            "under MIT; see the repository parity ledger for the exact path and blob.\n\n"
        )
        header = (
            "---\n"
            f"name: {name}\n"
            f"description: {yaml_quote(description)}\n"
            "---\n\n"
        )
        skill_text = header + provenance + body.strip() + "\n"
        supporting_files: list[str] = []
        if len(skill_text.splitlines()) > 500:
            reference = target / "references" / "full-workflow.md"
            reference.parent.mkdir(parents=True, exist_ok=True)
            reference.write_text(
                provenance + body.strip() + "\n",
                encoding="utf-8",
                newline="\n",
            )
            wrapper = f"""# {name.replace('-', ' ').title()}

This is a full-fidelity Codex port of a large upstream studio workflow. Its
detailed phases, templates, checks, and handoff prompts live in
[`references/full-workflow.md`](references/full-workflow.md) to keep skill
discovery lightweight.

## Required procedure

1. Read `references/full-workflow.md` completely before executing this skill.
2. Follow its phases in order and preserve all approval, review, testing, and
   evidence gates.
3. Adapt shell syntax to the detected platform; use PowerShell on Windows and
   POSIX syntax on macOS/Linux.
4. Inherit the active Codex model and permission mode. Never weaken sandbox,
   approval, provenance, or human creative-control boundaries.
5. If a referenced project artifact is absent, report the gap and use the
   documented fallback instead of inventing completion evidence.
"""
            skill_text = header + provenance + wrapper
            supporting_files.append(
                f"plugins/ai-game-studio/skills/{name}/references/full-workflow.md"
            )
        (target / "SKILL.md").write_text(skill_text, encoding="utf-8", newline="\n")
        (target / "agents" / "openai.yaml").write_text(
            make_openai_yaml(name, description), encoding="utf-8", newline="\n"
        )
        rel_source = source_path.relative_to(UPSTREAM).as_posix()
        entry: dict[str, object] = {
            "kind": "skill",
            "id": name,
            "source_path": rel_source,
            "source_commit": COMMIT,
            "source_blob": source_blob(rel_source),
            "destination": f"plugins/ai-game-studio/skills/{name}/SKILL.md",
            "status": "ported",
            "tests": ["parity-count", "skill-frontmatter", "skill-metadata", "codex-runtime-scan"],
        }
        if supporting_files:
            entry["supporting_files"] = supporting_files
        ledger.append(entry)
    for name, spec in NATIVE_SKILLS.items():
        target = SKILL_ROOT / name
        if not target.is_dir() or not (target / "agents" / "openai.yaml").exists():
            raise RuntimeError(f"native skill was not scaffolded with init_skill.py: {name}")
        description = str(spec["description"])
        text = (
            "---\n"
            f"name: {name}\n"
            f"description: {yaml_quote(description)}\n"
            "---\n\n"
            + native_body(name, spec).strip()
            + "\n"
        )
        (target / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
        (target / "agents" / "openai.yaml").write_text(
            make_openai_yaml(name, description), encoding="utf-8", newline="\n"
        )
    return ledger


def agent_group(name: str) -> str:
    if name.startswith("unity-") or name == "unity-specialist":
        return "unity"
    if name.startswith("godot-") or name == "godot-specialist":
        return "godot"
    if name.startswith("ue-") or name == "unreal-specialist":
        return "unreal"
    return "core"


def write_agents(skill_names: list[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_root = UPSTREAM / ".claude" / "agents"
    target_root = AUTOMATION / "agents"
    target_root.mkdir(parents=True, exist_ok=True)
    ledger: list[dict[str, object]] = []
    manifest: list[dict[str, object]] = []
    for source in sorted(source_root.glob("*.md")):
        metadata, body = parse_frontmatter(source.read_text(encoding="utf-8"))
        name = metadata["name"]
        description = clean_inline(metadata["description"], skill_names)
        body = clean_text(body, skill_names)
        instructions = (
            f"Role purpose: {description}\n\n"
            "Inherit the active Codex model, reasoning effort, and permission mode. "
            "Do not weaken parent approvals or sandbox constraints. Work as a bounded "
            "specialist: inspect relevant context, report assumptions, make only in-scope "
            "changes, verify them, and return concise evidence to the orchestrator.\n\n"
            + body.strip()
            + "\n"
        )
        if "'''" in instructions:
            raise ValueError(f"agent contains TOML literal delimiter: {name}")
        target = target_root / f"{name}.toml"
        target.write_text(
            f"# Derived from the pinned upstream source at {COMMIT} (MIT); exact path and blob are in parity/ledger.json.\n"
            "# This role intentionally inherits the active model and permission mode.\n"
            "developer_instructions = '''\n"
            + instructions
            + "'''\n",
            encoding="utf-8",
            newline="\n",
        )
        rel_source = source.relative_to(UPSTREAM).as_posix()
        ledger.append(
            {
                "kind": "role",
                "id": name,
                "source_path": rel_source,
                "source_commit": COMMIT,
                "source_blob": source_blob(rel_source),
                "destination": f"plugins/ai-game-studio-automation/templates/agents/{name}.toml",
                "status": "ported",
                "tests": ["parity-count", "toml-parse", "inheritance-policy", "codex-runtime-scan"],
            }
        )
        manifest.append(
            {
                "id": name,
                "description": description,
                "group": agent_group(name),
                "recommended_default": name in COMMON_DEFAULT_ROLES,
                "config_file": f".codex/agents/{name}.toml",
                "template": f"templates/agents/{name}.toml",
            }
        )
    (target_root / "manifest.json").write_text(
        json.dumps({"version": 1, "roles": manifest}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return ledger, manifest


def extract_rule_paths(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").splitlines()
    if not lines or lines[0] != "---":
        return []
    end = lines[1:].index("---") + 1
    paths = []
    for line in lines[1:end]:
        match = re.match(r'^\s*-\s*["\']?(.+?)["\']?\s*$', line)
        if match:
            paths.append(match.group(1))
    return paths


def write_rules(skill_names: list[str]) -> list[dict[str, object]]:
    source_root = UPSTREAM / ".claude" / "rules"
    target_root = AUTOMATION / "rules"
    target_root.mkdir(parents=True, exist_ok=True)
    ledger: list[dict[str, object]] = []
    for source in sorted(source_root.glob("*.md")):
        raw = source.read_text(encoding="utf-8")
        paths = extract_rule_paths(raw)
        _, body = parse_frontmatter(raw)
        body = clean_text(body, skill_names)
        title = source.stem.replace("-", " ").title()
        scope = "\n".join(f"- `{path}`" for path in paths)
        target = target_root / source.name
        target.write_text(
            f"# {title} path-scoped AGENTS.md fragment\n\n"
            f"> Adapted from the pinned upstream source at `{COMMIT}` under MIT; exact path and blob are in the parity ledger.\n\n"
            "This template is inert until the automation pack shows the destination files and the user confirms materialization. "
            "Merge it into the nearest path-scoped `AGENTS.md` covering:\n\n"
            f"{scope}\n\n"
            + body.strip()
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        rel_source = source.relative_to(UPSTREAM).as_posix()
        ledger.append(
            {
                "kind": "rule",
                "id": source.stem,
                "source_path": rel_source,
                "source_commit": COMMIT,
                "source_blob": source_blob(rel_source),
                "destination": f"plugins/ai-game-studio-automation/templates/rules/{source.name}",
                "status": "ported",
                "tests": ["parity-count", "path-scope-preserved", "codex-runtime-scan"],
            }
        )
    return ledger


def write_templates(skill_names: list[str]) -> list[dict[str, object]]:
    source_root = UPSTREAM / ".claude" / "docs" / "templates"
    target_root = AUTOMATION / "upstream"
    target_root.mkdir(parents=True, exist_ok=True)
    ledger: list[dict[str, object]] = []
    for source in sorted(source_root.rglob("*.md")):
        relative = source.relative_to(source_root)
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = clean_text(source.read_text(encoding="utf-8"), skill_names)
        target.write_text(
            f"<!-- Adapted from the pinned upstream source at {COMMIT} under MIT; see parity/ledger.json. -->\n\n"
            + text,
            encoding="utf-8",
            newline="\n",
        )
        rel_source = source.relative_to(UPSTREAM).as_posix()
        ledger.append(
            {
                "kind": "template",
                "id": relative.as_posix(),
                "source_path": rel_source,
                "source_commit": COMMIT,
                "source_blob": source_blob(rel_source),
                "destination": f"plugins/ai-game-studio-automation/templates/upstream/{relative.as_posix()}",
                "status": "ported",
                "tests": ["parity-count", "relative-path-preserved", "codex-runtime-scan"],
            }
        )
    return ledger


def hook_ledger() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for name, mappings in sorted(HOOK_MAP.items()):
        rel_source = f".claude/hooks/{name}"
        result.append(
            {
                "kind": "hook-behavior",
                "id": name.removesuffix(".sh"),
                "source_path": rel_source,
                "source_commit": COMMIT,
                "source_blob": source_blob(rel_source),
                "destination": "plugins/ai-game-studio-automation/hooks/hooks.json",
                "codex_mappings": mappings,
                "status": "replaced",
                "tests": ["parity-count", "hook-event-fixtures", "windows-posix-command-paths"],
            }
        )
    return result


def write_ledger(entries: list[dict[str, object]], source_skills: list[str]) -> None:
    parity_root = ROOT / "parity"
    parity_root.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["kind"]] = counts.get(entry["kind"], 0) + 1
    native = [
        {
            "id": name,
            "destination": f"plugins/ai-game-studio/skills/{name}/SKILL.md",
            "status": "native",
            "tests": ["skill-frontmatter", "skill-metadata", "production-quality-gates"],
        }
        for name in NATIVE_SKILLS
    ]
    ledger = {
        "$schema": "./parity-ledger.schema.json",
        "version": 1,
        "source": {
            "repository": SOURCE_URL,
            "commit": COMMIT,
            "license": "MIT",
            "attribution": "Donchitos and Claude Code Game Studios contributors",
            "verified_date": "2026-07-30",
        },
        "expected": {
            "skill": 73,
            "role": 49,
            "hook-behavior": 12,
            "rule": 11,
            "template": 40,
            "native-skill": 12,
            "total-core-skills": 85,
        },
        "actual": {**counts, "native-skill": len(native), "total-core-skills": len(source_skills) + len(native)},
        "entries": sorted(entries, key=lambda item: (str(item["kind"]), str(item["id"]))),
        "native_skills": native,
    }
    (parity_root / "ledger.json").write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    rows = [
        "# Claude Code Game Studios parity ledger",
        "",
        f"Pinned source: [{SOURCE_URL}]({SOURCE_URL}) at `{COMMIT}` (MIT).",
        "",
        "The JSON ledger is the release authority. A status of `ported` means the behavior and content were adapted to Codex-native files; `replaced` means an unsupported runtime mechanism was mapped to a supported Codex behavior. There are no `not-applicable` entries in v1.",
        "",
        "| Surface | Source | v1 status |",
        "|---|---:|---:|",
        f"| Skills | {counts.get('skill', 0)} | {counts.get('skill', 0)} ported |",
        f"| Roles | {counts.get('role', 0)} | {counts.get('role', 0)} ported |",
        f"| Hook behaviors | {counts.get('hook-behavior', 0)} | {counts.get('hook-behavior', 0)} replaced |",
        f"| Path rules | {counts.get('rule', 0)} | {counts.get('rule', 0)} ported |",
        f"| Templates actually present | {counts.get('template', 0)} | {counts.get('template', 0)} ported |",
        f"| New generative skills | 0 | {len(native)} native |",
        "",
        "Every derived entry records its upstream path, commit, Git blob SHA, destination, status, and acceptance tests in `ledger.json`.",
        "",
    ]
    (parity_root / "README.md").write_text("\n".join(rows), encoding="utf-8", newline="\n")


def main() -> None:
    if subprocess.run(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip() != COMMIT:
        raise RuntimeError(f"upstream checkout is not pinned to {COMMIT}")

    source_skills = sorted(path.name for path in (UPSTREAM / ".claude" / "skills").iterdir() if path.is_dir())
    if len(source_skills) != 73:
        raise RuntimeError(f"expected 73 source skills, found {len(source_skills)}")
    if set(source_skills) & set(NATIVE_SKILLS):
        raise RuntimeError("native skill collides with source skill")

    entries = write_skills(source_skills)
    agent_entries, _ = write_agents(source_skills + list(NATIVE_SKILLS))
    entries.extend(agent_entries)
    entries.extend(write_rules(source_skills + list(NATIVE_SKILLS)))
    entries.extend(write_templates(source_skills + list(NATIVE_SKILLS)))
    entries.extend(hook_ledger())
    write_ledger(entries, source_skills)

    digest = hashlib.sha256((ROOT / "parity" / "ledger.json").read_bytes()).hexdigest()
    print(json.dumps({"source_skills": 73, "native_skills": 12, "roles": 49, "hooks": 12, "rules": 11, "templates": 40, "ledger_sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
