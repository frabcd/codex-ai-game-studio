# AI Game Studio prompt cookbook

Use these patterns after installing the plugin. A strong request names the desired player-visible outcome, relevant constraints, permitted source material, target runtime, evidence, and the safety boundary.

## Prompt formula

```text
$ai-game-studio:[skill] [Outcome]. Context: [project/engine/audience].
Constraints: [scope, platform, budget, style, hardware, privacy, commercial use].
Inputs I have rights to use: [references/assets/data].
Acceptance: [playability, visual, technical, performance, accessibility gates].
Safety: inspect first, preserve originals, disclose licenses/downloads/permissions,
plan exact changes and rollback, then wait for my confirmation.
```

## Discovery and setup

### Unknown project

```text
$ai-game-studio:toolchain-doctor Inspect this project and machine read-only.
Report OS/architecture/WSL, engine and version, DCC/pixel tools, Python/Node/package
managers, Git/gh, existing MCP server names, credential variable names that exist,
GPU backend/VRAM, free disk, and likely network/download needs. Do not install,
launch, edit, or read secret values.
```

### Find a compatible tool

```text
$ai-game-studio:tool-discover Find tools for [capability]. Hard constraints:
[OS/architecture], [engine/application], [GPU/VRAM], [local-only or hosted],
[commercial status], and [maximum download/cost]. Compare compatible candidates by
quality, maturity, performance, permissions, separate code/weight/dataset/output
licenses, and limitations. Recommend one; do not install it.
```

### Plan optional automation

```text
$ai-game-studio:engine-automation Detect the host application and every existing
server that can control it. Select at most one compatible MCP. Show the exact pin,
commands, permissions, conflicts, downloads, health checks, uninstall, backups,
and rollback in one transaction. Wait for the digest confirmation.
```

## Design and production

### Scope a concept

```text
$ai-game-studio:brainstorm Explore three materially different versions of [idea]
for [audience/platform]. Compare the core verb, novelty, production risk, content
burden, accessibility, and a two-minute proof. Recommend one but keep discarded
options and assumptions visible.
```

### Quick design into backlog

```text
$ai-game-studio:quick-design Turn [concept] into a concise design with player
promise, core loop, controls, rules, feedback, difficulty, failure/recovery,
content scope, non-goals, budgets, and measurable prototype acceptance. Then use
$ai-game-studio:create-epics and $ai-game-studio:create-stories only after I approve.
```

### Vertical slice

```text
$ai-game-studio:vertical-slice Define the smallest content-complete slice that
proves [core experience]. Include representative art/audio/UI, one end-to-end
level, saving/settings if release-critical, performance budgets, QA evidence,
risks, and exit criteria. Preserve the current architecture and dirty files.
```

## Generated assets

### Style-consistent sprite revision

```text
$ai-game-studio:sprite-generate Match the attached rights-cleared sprite's palette,
pixel density, proportions, outline, light direction, pivot, and baseline while
creating [frames]. Keep alpha transparent and padding consistent. Generate isolated
candidates, a contact sheet, animated preview, frame map, provenance, and alpha/
baseline/loop checks. Do not replace the source.
```

### Tile set

```text
$ai-game-studio:sprite-generate Create a [tile size] tileset for [terrain set]
with [autotile convention]. Prove edge/corner coverage, grid alignment, palette,
seam-free repetition, collision annotations, and engine import. Include a test map
that exercises every adjacency; keep sources and candidates separate.
```

### Stylized 3D prop

```text
$ai-game-studio:asset-3d-generate Create a [style] real-time [prop] at [scale]
for [engine]. Budget [triangles/material slots/texture size/LODs]. Require manifold
geometry where applicable, clean normals, UVs, PBR channels, collision, origin and
axis conventions. Produce wireframe, turntable, validation, provenance, and engine
import evidence before approval.
```

### Character likeness boundary

```text
$ai-game-studio:asset-3d-generate Create an original stylized character from these
references, which I confirm I may use. Do not reproduce an unlicensed real person's
identity. Identify any resemblance/consent risk before production, keep an audit
record, and offer a non-identifying design if rights are uncertain.
```

### PBR material repair

```text
$ai-game-studio:material-texture-generate Diagnose [material] under neutral,
grazing, and representative game lighting. Separate albedo/color-space, normal
orientation, roughness, metallic, AO, height, seam, texel-density, and compression
issues. Repair only confirmed defects in a candidate set and show before/after
spheres plus tiled planes.
```

### Retargeted locomotion

```text
$ai-game-studio:rig-animation Retarget [licensed motion set] to this character.
Preserve source rig and motion. Validate bind pose, scale, hierarchy mapping,
deformation, root trajectory, foot contacts/sliding, loop seam, blend transitions,
and engine avatar import. Provide slow-motion overlays and metrics.
```

### Procedural animation-cued VFX

```text
$ai-game-studio:rig-animation Build a project-local Three.js VFX pass for this
rights-cleared rig and licensed animation set. Use [effect breakdown], [style
guide], [palette], and [performance budget]. First inspect the renderer, rig,
weapon reach, cue timeline, and existing effects. Then propose deterministic
runtime noise, procedural geometry or tubes, shared GLSL chunks, palette-driven
bands, and additive mesh layers that do not require a new post-processing or
particle pipeline. After confirmation, preserve sources, create isolated
candidates plus a VFX sheet, bind effects to measured animation cues, and
validate shader compilation, timing, readability, draw calls, frame budget,
degradation tiers, and rollback. Do not download or copy an unlicensed reference
video; use its textual breakdown only as functional inspiration.
```

## Worlds, narrative, and audio

### Deterministic procedural level

```text
$ai-game-studio:world-generate Generate a seeded greybox for [gameplay brief].
Every seed must preserve spawn-to-goal reachability, critical-path width, player
clearance, encounter pacing, checkpoint recovery, navigation, collision, and [time]
completion. Reject invalid seeds with reasons and save the generator parameters.
```

### NPC with bounded memory

```text
$ai-game-studio:npc-audio-generate Design [NPC] with canon, goals, knowledge
boundaries, dialogue states, quest transitions, safety/content limits, localization
keys, and deterministic fallbacks. If runtime language generation is proposed,
separate authored truth from generated phrasing and disclose privacy/cost/moderation.
```

### Consent-safe voice

```text
$ai-game-studio:npc-audio-generate Produce a voice-direction sheet and placeholder
voice for [original character]. Do not imitate any named living or deceased person.
Require documented performer/voice-model consent before production synthesis. Report
service privacy, license, costs, loudness, peaks, noise, and subtitle alignment.
```

### Seamless ambience and music

```text
$ai-game-studio:npc-audio-generate Create candidate ambience/music for [scene]
with [duration/stems/intensity states]. Validate license and provenance, peak and
integrated loudness, DC offset, sample rate, loop seam, transitions, in-engine
triggering, and mix headroom. Preserve masters and export settings.
```

## QA and release

### Bug reproduction

```text
$ai-game-studio:bug-triage Reproduce [symptom] from a clean state. Record build,
platform, seed/save/input, minimum steps, expected/actual result, frequency, logs,
screenshots/video, and suspected subsystem. Diagnose only; do not implement a fix
until I ask.
```

### Visual regression

```text
$ai-game-studio:visual-qa Capture [views/states/resolutions] with deterministic
camera, seed, time, quality, and masking. Compare baseline/current/diff, then classify
camera, geometry, material, lighting, animation, UI, and post-process changes.
Use metrics as signals and require human review for perceptual acceptability.
```

### Performance gate

```text
$ai-game-studio:perf-profile Measure this representative sequence on [device/build]
against [frame-time, memory, draw-call, load, asset] budgets. Capture warm-up and
steady-state evidence, separate CPU/GPU/IO stalls, identify the top regression,
and propose a reversible experiment before optimizing.
```

### Release decision

```text
$ai-game-studio:launch-checklist Build a release evidence table for [version]:
scope, blockers, known issues, platform certification, rights/provenance, security,
accessibility, localization, saves/migration, performance, crash/soak, rollback,
support, and ownership. Mark missing evidence; never convert an unknown into pass.
```

## Safety redirects

Use these when a request should not be followed literally.

```text
Do not install every catalog entry. Turn my request into the smallest compatible
plan, explain what was excluded and why, and require confirmation.
```

```text
Do not use an incompatible CUDA-only pipeline. Compare verified native, CPU, or
hosted alternatives and wait for me to accept the quality/cost/privacy tradeoff.
```

```text
Block production use if identity, voice consent, code/weight/dataset/output rights,
or commercial terms are missing. Offer a rights-cleared placeholder route.
```
