# Tutorial workbook: what to say to Codex

These tutorials are designed to be pasted into a **new Codex task** after the plugin is enabled. Replace text in `[brackets]`; attach references only when you have permission to use them.

Every tutorial follows the same contract:

1. Codex inspects the active project and relevant machine capabilities read-only.
2. It asks only questions whose answers materially change the workflow, rights, cost, or output.
3. It proposes one compatible route, plus alternatives only when a constraint blocks the preferred route.
4. It discloses files, processes, downloads, licenses, credentials-by-variable-name, permissions, and rollback.
5. Nothing mutating happens until you confirm the transaction digest.
6. Generated output stays beside the original until visual/technical evidence and human approval permit replacement.

## 1. Start a new game

### What to say

```text
$ai-game-studio:start I want to make [one-sentence game idea] for [platform]
with [session length or scope]. Treat this as a new project. Help me choose the
smallest stack that can prove the core loop in [time budget]. Inspect my OS,
installed tools, GPU, disk, and existing Codex integrations read-only. Propose
one vertical-slice plan with licenses, downloads, permissions, quality gates,
and rollback. Wait for my confirmation before creating files or installing anything.
```

### What Codex inspects

- OS, CPU architecture, native/WSL/container context, free disk, GPU backend, and reported VRAM.
- Installed Git, Python, Node, package managers, engines, DCC tools, pixel editors, and known MCP configuration names.
- The current directory for existing project markers so a “new” project does not overwrite a real one.

### What it asks

- Target platform, camera/control style, multiplayer requirement, content rating, accessibility needs, and the single mechanic that must feel good.
- Whether references are inspiration, licensed production inputs, or identity-sensitive material.
- Hard constraints: delivery date, download budget, hosted-service cost, offline requirement, and commercial intent.

### What it proposes

- One engine/stack, a two-to-five minute vertical slice, acceptance criteria, risk register, and asset budgets.
- A transaction with the exact starter files, optional pack, external dependencies, versions/pins, downloads, permissions, backups, and rollback.

### What it may change after confirmation

- A new project directory, project manifest, minimal playable scene, tests, `.ai-game-studio/project.json`, and `.ai-game-studio/lock.json`.
- It does not activate editor MCPs or download weights unless those exact actions were in the confirmed digest.

### Expected artifacts and rollback

- Concept brief, quick design, architecture decision, milestone backlog, playable loop, screenshots, smoke-test results, provenance manifest, and performance baseline.
- Rollback removes only generated files listed in the transaction and restores backed-up configuration byte-for-byte.

## 2. Adopt an existing game repository

### What to say

```text
$ai-game-studio:start Adopt this existing game without rewriting its architecture.
Read its AGENTS.md, documentation, engine metadata, tests, asset conventions,
budgets, and current Git state. Identify the most valuable reversible milestone,
show every proposed file change and external dependency, and wait for my approval.
```

### What Codex inspects

- Repository instructions, dirty worktree state, engine/project version, build/test commands, folder conventions, LFS usage, asset import settings, CI, and current quality evidence.
- Existing MCP servers and project automation so it does not create duplicate editor control.

### What it asks

- Which uncommitted work belongs to you, what areas are off limits, the supported release branch, and the production definition of done.
- Whether it may create a branch or whether all work must remain local.

### What it proposes

- A non-invasive gap map, prioritized milestone, bounded file scope, tests, optional role materialization, and an explicit “leave unchanged” list.

### What it may change after confirmation

- Only paths named in the confirmed transaction. Existing dirty files are preserved unless you explicitly include them.

### Expected artifacts and rollback

- Adoption report, project-stage detection, architecture map, test baseline, selected workflow, plan/lock files, and rollback receipt.
- Backups are restored before generated files are removed; Git history is never rewritten automatically.

## 3. Prompt to a playable prototype

### What to say

```text
$ai-game-studio:prompt-to-game Build a playable prototype from this idea:
[idea]. The player must be able to [core verb], understand success/failure,
restart, and finish a two-minute run. Use placeholder or rights-cleared assets.
Set measurable feel, frame-time, input, and playability gates. Plan first and
wait for the digest confirmation.
```

### What Codex inspects

- Existing project stack, available build/test/browser tools, input system, scene conventions, and target hardware.

### What it asks

- The core verb, win/loss condition, input method, audience, visual direction, and whether speed or fidelity matters more for this prototype.

### What it proposes

- A minimal loop, one scene/level, placeholder asset strategy, instrumentation, smoke tests, and explicit exclusions that prevent scope creep.

### What it may change after confirmation

- Gameplay code, a minimal UI, one level, generated placeholders, tests, and local evidence directories.

### Expected artifacts and rollback

- Runnable build, short design brief, input map, automated smoke test, playtest checklist, performance capture, and screenshots.
- Rollback restores replaced configuration and removes only transaction-owned prototype files.

## 4. Unity workflow

### What to say

```text
$ai-game-studio:engine-automation Inspect this Unity project and installed Unity
editors. Detect existing MCP servers and packages. Propose exactly one compatible
Unity integration, preferring the pinned CoplayDev adapter, with its source pin,
license, command, package/editor changes, network/process permissions, health
check, uninstall, and rollback. Do not install, launch Unity, or edit the project
until I confirm the transaction digest.
```

### What Codex inspects

- `ProjectVersion.txt`, `Packages/manifest.json`, assembly definitions, render pipeline, input/test frameworks, Unity Hub/editor locations, and existing MCP names.
- Native Windows/macOS/Linux versus WSL execution; GUI editor control must remain native.

### What it asks

- Which installed editor version is authoritative, whether the editor may be launched, and whether package manifest changes are acceptable.

### What it proposes

- Core-only workflow if no live editor control is needed; otherwise the Unity pack with one MCP, exact upstream pin, local binding, tool approvals, connection test, and scene smoke test.

### What it may change after confirmation

- Approved Codex MCP configuration, a narrowly scoped Unity package/editor companion, `.ai-game-studio` lock state, and test fixtures.

### Expected artifacts and rollback

- Detection report, editor handshake, package compilation result, play-mode/edit-mode smoke tests, screenshot, and transaction receipt.
- Disable stops the server; rollback restores configuration and package manifests and removes only installed companion files.

## 5. Godot workflow

### What to say

```text
$ai-game-studio:engine-automation Inspect this Godot project, project.godot,
addons, language mix, and installed editor versions. Prefer the pinned Coding-Solo
Godot adapter and native GDScript when consistent with the repository. Propose one
MCP, its permissions and health test, then wait for confirmation before setup or
editor control.
```

### What Codex inspects

- Godot version/features, renderer, main scene, autoloads, GDScript/C#/GDExtension use, plugins, test setup, editor installation, and existing MCPs.

### What it asks

- Whether C#/.NET is required, which renderer/target matters, and whether the editor may import assets during setup.

### What it proposes

- One language-compatible route, one MCP at most, project import/parse check, scene launch test, and rollback.

### What it may change after confirmation

- Approved adapter configuration and explicitly listed project/plugin files. `.godot/` generated import data is never treated as source truth.

### Expected artifacts and rollback

- Parser/import report, main-scene smoke test, screenshot, test output, lockfile, and adapter health result.
- Rollback restores settings and removes the approved adapter while leaving pre-existing addons untouched.

## 6. Unreal Engine workflow

### What to say

```text
$ai-game-studio:engine-automation Inspect this Unreal project, engine association,
plugins, modules, Blueprint/C++ split, and existing remote-control or MCP tooling.
Propose one pinned IvanMurzak Unreal adapter or explain why the GenOrca alternative
is safer here. Include build cost, editor permissions, ports, health checks, and
rollback. Wait before installation, compilation, or editor launch.
```

### What Codex inspects

- `.uproject`, engine association, plugin descriptors, module build files, target platforms, maps, automation tests, source-control status, and installed editors/toolchains.

### What it asks

- Blueprint-only versus C++ authority, permitted compile time, target configuration, whether editor restart is acceptable, and the test map.

### What it proposes

- One MCP, exact plugin/config changes, localhost/stdio transport, build and editor smoke tests, and a time/space estimate.

### What it may change after confirmation

- Approved plugin/config files, generated project metadata, narrowly scoped test content, and `.ai-game-studio` state.

### Expected artifacts and rollback

- Successful module/plugin load, test-map open, automation result, screenshot, log excerpt without secrets, and performance baseline.
- Rollback disables/removes only the installed plugin, restores descriptors/config, and reports files Unreal regenerated.

## 7. Browser game workflow

### What to say

```text
$ai-game-studio:prototype Use this repository's current browser stack to build
[prototype]. Preserve its package manager and code style. Add keyboard and pointer
controls, deterministic restart, responsive layout, a browser smoke test, and
screenshot regression evidence. Propose dependencies and file changes before writing.
```

### What Codex inspects

- Package manager/lockfile, framework (Canvas, Phaser, Three.js, React Three Fiber, or other), build scripts, browser support, asset loading, and existing Playwright/test setup.

### What it asks

- Supported browsers/devices, input methods, accessibility requirements, desired capture sizes, and asset-loading constraints.

### What it proposes

- A route within the existing framework, a minimal dependency delta, interaction tests, visual baselines, and performance budgets.

### What it may change after confirmation

- Source, styles, public assets, tests, and lockfile entries explicitly named in the plan.

### Expected artifacts and rollback

- Local build, browser test, screenshots at representative viewports, console-error check, and frame/memory evidence.
- Rollback restores package/lock files and removes generated source/tests/assets.

## 8. 2D sprites, animation sheets, and tiles

### What to say

```text
$ai-game-studio:sprite-generate From these rights-cleared references, create a
[dimensions] [palette/style] character with [directions] and [animations/frames].
Keep a transparent background, consistent pivots and baselines, edge padding,
palette, proportions, light direction, and silhouette. Generate a contact sheet
and in-engine loop preview. Do not replace any source sprite until I approve the
before/after evidence.
```

### What Codex inspects

- Reference rights/provenance, current palette, pixel density, alpha mode, atlas/import settings, pivot convention, tile grid, animation timing, and target engine limits.

### What it asks

- Production-use rights, exact sheet layout, palette restrictions, anchor point, facing directions, animation names/timing, and nearest-neighbor versus filtered sampling.

### What it proposes

- A compatible external or manual generation route, prompt/seed record, intermediate format, cleanup tool, atlas layout, validation, and fallback if the preferred model/tool is unavailable.

### What it may change after confirmation

- New files in an isolated generated-assets directory, metadata/import sidecars, and opt-in test fixtures. Originals remain unchanged.

### Expected artifacts and rollback

- Individual frames, packed sheet, machine-readable frame map, palette swatch, contact sheet, animated preview, alpha/baseline/loop report, provenance JSON, and engine-import screenshot.
- Rejecting the result removes generated candidates; approving replacement still creates a backup and reversible mapping.

## 9. Image/text-to-3D asset and PBR materials

### What to say

```text
$ai-game-studio:asset-3d-generate Reconstruct [asset] from these licensed views
for [engine/platform]. Target [triangle budget], real-world scale, clean normals,
non-overlapping UVs, [texture size], PBR channels, collision, and [LOD count].
Use my available GPU only if the model and licenses fit. Produce turntable and
wireframe evidence and wait before replacing any production asset.

$ai-game-studio:material-texture-generate Create a tileable [material] set with
base color, normal, roughness, metallic, ambient occlusion, and height channels.
State color space and packing, prove seams at multiple scales, and record licenses
and prompts.
```

### What Codex inspects

- Reference coverage/rights, unit scale, engine import conventions, mesh/texture budgets, existing DCC tools, GPU backend/VRAM, disk/network budget, and catalog license fields.

### What it asks

- Fidelity versus runtime budget, collision/LOD needs, skeleton compatibility, texture channel packing, commercial intent, and whether hosted processing is allowed.

### What it proposes

- One hardware- and license-compatible pipeline, downloads and weight sizes, intermediate formats, cleanup/retopo/UV/bake stages, engine import settings, and a CPU/hosted/manual fallback.

### What it may change after confirmation

- Candidate meshes/materials/textures, DCC scripts, import metadata, preview scenes, and validation reports in isolated output paths.

### Expected artifacts and rollback

- Source/interchange file, engine-ready export, topology/normals/UV report, PBR-channel manifest, texture seam preview, collision/LOD evidence, multi-view turntable, provenance, and import smoke test.
- Originals remain. Approval copies a validated candidate into production only after backup; rollback restores the prior asset and metadata.

## 10. Rigging, retargeting, and animation

### What to say

```text
$ai-game-studio:rig-animation Rig this rights-cleared character for [engine],
retarget [motion source], and export [animations]. Preserve the source mesh.
Validate hierarchy, bind pose, deformation weights, root motion, foot contacts,
hand/face requirements, scale, loop continuity, and engine import. Create slow-
motion and contact overlays before asking me to approve production replacement.
```

### What Codex inspects

- Mesh topology, symmetry, transforms, existing skeleton/avatar, motion license, target-engine humanoid rules, Blender/DCC availability, and runtime bone budgets.

### What it asks

- Humanoid versus custom rig, root-motion policy, IK requirements, target frame rate, required clips, additive layers, and facial/hand detail.

### What it proposes

- Auto-rig/manual/hosted options compared by license, privacy, quality, cost, hardware, and limitations; one selected route with cleanup and validation.

### What it may change after confirmation

- Candidate rigged scene, exported skeleton/animation files, retarget maps, engine import metadata, and preview/tests. The original mesh and motions remain untouched.

### Expected artifacts and rollback

- Skeleton map, weight heatmaps, deformation poses, root trajectory, foot-slide metrics, loop seam report, preview video/contact sheet, provenance, and engine animation-controller smoke test.
- Rollback removes candidates or restores the backed-up production rig/controller.

## 11. Generated environments and procedural levels

### What to say

```text
$ai-game-studio:world-generate Build a deterministic [genre] level from this
brief: [brief]. Start with a greybox. Enforce [dimensions/budgets], spawn-to-goal
reachability, navigation, encounter pacing, sight lines, collision, lighting,
and seeded regeneration. Prove playability before proposing an art pass.
```

### What Codex inspects

- Engine/world representation, nav system, player dimensions/abilities, spawn and checkpoint conventions, tile/modular kits, lighting pipeline, world partition/streaming, and performance budgets.

### What it asks

- Player verbs, critical path, target session length, generation seed policy, failure recovery, art direction, and what must be handcrafted.

### What it proposes

- A deterministic layout grammar, seed and parameters, greybox milestones, reachability/nav tests, encounter gates, art pass, and fallbacks for invalid generation.

### What it may change after confirmation

- Generated greybox scenes/maps, procedural scripts/data, navigation data, tests, captures, and provenance. Existing authored maps are preserved.

### Expected artifacts and rollback

- Seeded level, generation manifest, path/reachability proof, nav/collision report, lighting captures, playthrough smoke test, and performance profile.
- Rollback removes generated worlds and restores any explicitly modified scene/index configuration.

## 12. NPC dialogue, quests, voices, music, and sound

### What to say

```text
$ai-game-studio:npc-audio-generate Design an NPC encounter for [context]. Create
the dialogue state graph, quest states, failure/recovery paths, placeholder voice,
music, ambience, and SFX plan. Use no real person's identity or voice without
documented consent. Separate local and hosted options, list all licenses/costs,
and validate loudness, peaks, loop seams, subtitles, and in-game triggers.
```

### What Codex inspects

- Narrative bible, localization format, quest/state system, audio middleware/import settings, loudness target, existing characters/voice consent records, and available local/hosted tooling.

### What it asks

- Canon/character constraints, content rating, supported languages, consent and identity rights, voice style without impersonation, music-use rights, and service/privacy limits.

### What it proposes

- State machine and script first, then consent-safe voice/music/SFX routes; one preferred pipeline plus a non-voice or local placeholder fallback.

### What it may change after confirmation

- Dialogue/quest data, placeholder or approved audio candidates, subtitle files, integration scripts, test scene, and provenance. It will not clone a voice from an unverified recording.

### Expected artifacts and rollback

- Dialogue graph, quest matrix, localization keys, consent/license record, audio cue sheet, WAV/engine-ready candidates, peak/loudness/seam report, subtitle sync, trigger smoke test, and mix preview.
- Rollback restores previous data/import settings and removes generated candidates; published audio requires human approval.

## 13. Visual QA, playtesting, performance, and quality enhancement

### What to say

```text
$ai-game-studio:visual-qa Capture representative views and gameplay states for
this build. Compare them with [references or prior baseline], separate camera,
lighting, geometry, material, animation, UI, and post-process differences, and
report severity with evidence. Also run interaction smoke tests and collect frame
time, memory, draw calls, and asset-budget results. Do not modify the build.

$ai-game-studio:quality-enhance Using the accepted QA report, preserve all source
assets and create reversible candidates only for [approved defect IDs]. Produce
before/after images or animation previews, rerun every affected gate, and wait
for human approval before replacement.
```

### What Codex inspects

- Testable build path, capture tooling, baseline/reference provenance, view/camera definitions, golden tolerances, gameplay paths, profiler availability, budgets, source assets, and Git state.

### What it asks

- Which references are authoritative, acceptable perceptual/metric tolerance, representative devices, nondeterministic effects to mask, and which defect IDs may be enhanced.

### What it proposes

- A capture matrix, deterministic states, pixel/perceptual comparison, human visual rubric, interaction tests, performance capture, defect classification, and isolated enhancement transaction.

### What it may change after confirmation

- QA-only work creates evidence and reports. Enhancement creates candidate assets/settings beside originals; production replacement is a second explicit approval.

### Expected artifacts and rollback

- Baseline/current/diff images, multi-view contact sheet, animation timing evidence, smoke-test logs, budget table, severity-ranked QA report, candidate before/after previews, provenance, and approval record.
- Rejecting candidates leaves production unchanged. Approved replacement uses backups and a rollback map for every file and setting.

## 14. Migrate a Claude game-studio project

### What to say

```text
$ai-game-studio-automation:migrate-claude Inspect this Claude-oriented project
read-only. Map CLAUDE.md, scoped instructions, agents, commands, skills, hooks,
tool declarations, model names, memory fields, and shell assumptions to supported
Codex forms. Show every destination, replacement, not-applicable item, test, and
rollback in one transaction. Do not remove Claude files or write Codex files
until I confirm the digest.
```

### What Codex inspects

- `CLAUDE.md`, `.claude/`, commands, skills, agents, hooks/settings, path rules, scripts, OS assumptions, and existing `AGENTS.md`/`.codex` content.

### What it asks

- Whether dual Claude/Codex support must remain, which agent roles are needed, target engines, and whether hooks may be proposed.

### What it proposes

- Root/path-scoped `AGENTS.md`, supported `.codex/agents/*.toml`, namespaced skill references, event-mapped hooks, cross-platform launchers, and a coverage report. Unsupported tool declarations, fixed Claude models, memory fields, and fixed turn limits are replaced with runtime-inherited behavior.

### What it may change after confirmation

- New Codex files and explicitly approved updates to shared documentation. Claude files remain unless a separate removal transaction is confirmed.

### Expected artifacts and rollback

- Migration map, parity report, generated instructions/agents/hooks, validation output, negative scan for Claude-only runtime references, and a backup manifest.
- Rollback removes generated Codex files and restores any shared docs; it does not rewrite history or delete Claude assets by default.

## 15. Reference image to procedural Three.js code

Install the optional Apache-2.0 pack first:

```text
codex plugin add ai-game-studio-img2threejs@frabcd-ai-game-studio
```

### What to say

```text
Use $ai-game-studio-img2threejs:img2threejs with this reference image.
Validate the reference, ask for my intended game use and quality target, and
write a quality contract before code. Reconstruct it as procedural Three.js in
ordered passes, review deterministic multi-view captures at every gate, state
what still differs, and keep generated work in my approved project directory.
Never claim unseen geometry or an approximation is exact.
```

### What Codex inspects

- The supplied image, visible silhouette and components, material cues, hidden-view uncertainty, reference rights, existing Three.js project conventions, animation or interaction needs, and target runtime budget.

### What it asks

- Intended use, fidelity versus stylization, missing views, action anchors, animation expectations, supported device class, acceptable correction budget, output directory, and whether the reference depicts a real person's likeness or protected design.

### What it proposes

- An observation record, quality contract, component/material specification, ordered blockout-to-optimization passes, capture matrix, per-pass acceptance gates, provenance, performance limits, and bounded correction loop.

### What it may change after confirmation

- Specifications, procedural Three.js source, renders, and review evidence in the approved project directory. The pack does not install dependencies, upload references, replace production assets, or control an editor by itself.

### Expected artifacts and rollback

- Image probe, specification, pass ledger, Three.js source, deterministic multi-view captures, visual comparison, performance evidence, known limitations, and provenance.
- Keep prior accepted passes. Rollback restores the last accepted specification/source and removes only named candidates; it never alters the input reference.

See the complete [img2threejs pack guide](https://frabcd.github.io/codex-ai-game-studio/packs/img2threejs/).

## 16. Choose the native Windows or macOS edition

### What to say

On Windows:

```text
Use $ai-game-studio-windows:setup-windows-edition to inspect this project and
propose one native Windows setup. Adapt incompatible POSIX, Metal, or macOS-only
steps by capability, disclose limitations, and wait for my full plan digest.
```

On macOS:

```text
Use $ai-game-studio-macos:setup-macos-edition to inspect this project and
propose one native macOS setup. Adapt incompatible EXE, PowerShell, CUDA, or
DirectML-only steps by capability, disclose limitations, and wait for my full
plan digest.
```

### What Codex inspects, asks, and proposes

- It reads OS, architecture, native versus translated execution, shell, package-manager presence, GPU backends, disk, project markers, editor/DCC installations, and existing MCP configuration without launching or installing anything.
- It asks which outputs and constraints are non-negotiable, then proposes one native-first route, exact limitations, licenses, permissions, tests, downloads, fallbacks, backups, and rollback.
- Edition apply changes only `.ai-game-studio/project.json` and `.ai-game-studio/lock.json` after the exact digest is confirmed. Engine packs, external tools, Rosetta, WSL, hosted services, and model downloads require separate plans.

### Expected artifacts and rollback

- Read-only doctor report, adaptation matrix, digest-bound edition plan, selected-edition state and lock, health-check evidence, and a rollback transaction.
- Disable or rollback restores the two project-state files. It never silently removes independently installed applications or tools.

Use the detailed [Windows guide](https://frabcd.github.io/codex-ai-game-studio/platforms/windows/) or [macOS guide](https://frabcd.github.io/codex-ai-game-studio/platforms/macos/) for native alternatives, exact commands, and platform-specific prompts.

## If a preferred tool cannot run

Say:

```text
The preferred tool is incompatible. Compare only verified alternatives by the
required capability, output quality, code/weight/dataset/output licenses,
commercial status, privacy, cost, download size, performance, GPU/VRAM, OS,
host application, permissions, and known limitations. Recommend one substitution
and wait for a new confirmation; do not silently change the plan.
```

This is mandatory for CUDA-only software on incompatible hardware, unsupported host applications, conflicting MCP servers, unknown commercial terms, large downloads, or hosted services that violate the project's privacy constraint.
