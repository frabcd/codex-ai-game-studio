---
name: rig-animation
description: "Rig, retarget, generate, and quality-gate character animation plus cue-driven procedural VFX editors and composers with explicit skeleton, deformation, shader, timing, palette, and runtime-budget requirements."
---

# Rig Animation

## Outcome

Deliver clean character animation and reusable cue-driven procedural VFX that behave predictably in the target runtime.

## Required inputs

- rights-cleared character mesh, motion sources, and effect references
- target skeleton, engine or Three.js runtime, renderer, and existing dependency constraints
- clip list, frame rate, root-motion policy, gameplay constraints, and cue timing
- effect brief, style guide, palette and attachment requirements, and frame-time, draw-call, and overdraw budgets

Ask for missing information only when it changes the route materially. Otherwise
state conservative assumptions and proceed with read-only analysis.

## Workflow

1. Inspect topology, pose, scale, symmetry, deformation readiness, animation controllers, render architecture, package locks, tests, and runtime budgets without changing the project.
2. Define skeleton naming, hierarchy, twist bones, facial scope, root, and retarget profile. When procedural Three.js VFX or its editor is requested, read the [procedural VFX composer reference](references/procedural-vfx-composer.md) completely, define the effect taxonomy, parameter schema, named five-color palettes, and typed animation-cue contract, then validate `vfx-project.json` with the bundled `scripts/validate_vfx_spec.py` before implementation.
3. Present one exact implementation plan with candidate paths, dependencies, permissions, previews, tests, rollback, and digest; wait for confirmation before writing files, installing dependencies, or controlling an editor.
4. Generate or author weights and clips into preserved working copies. On Three.js targets, generate seeded integer-hash value noise, FBM, domain warping, and radial crack fields into runtime THREE.DataTexture objects; use an equivalent code-generated texture route elsewhere.
5. Build reusable procedural triangles, crescents, flare rings, ground discs, stars, shards, rubble, puffs, flame shells, and flame tongues, plus degenerate-safe parallel-transport tubes for straight, wobbly, jagged, or split trails, beams, and bolts.
6. Compose shared GLSL noise, shape, and edge chunks into erosion, flat-band, ink-contour, and heat-gradient shaders. Layer additive geometry for glow and use bounded meshes for sparks and debris without requiring post-processing or particle middleware.
7. Build the animation and VFX composer with an effect library and VFX sheet, preview viewport, transport and scrubbing, timeline and cue tracks, inspector, palette controls, deterministic import/export, and undo/redo.
8. Fire effects from animation cues, size them from measured rig and weapon-tip extents, aim them at the authored impact target, and define deterministic behavior for loops, seeking, repeated cues, and dropped frames.
9. Review deformation and effects from multiple views, then validate root motion, contacts, foot sliding, loop continuity, shader compilation, palette readability, transparent sorting, resource disposal, cue timing, editor round trips, runtime budgets, and target import.

## Expected artifacts

- rig, animation, VFX, palette, and cue specifications, including validated vfx-project.json when the VFX route is selected
- rigged source copy and validated clips
- procedural texture, geometry, tube, and shader library
- animation and VFX composer with deterministic saved state
- VFX sheet and multi-view temporal captures
- contact, loop, cue-timing, shader, and runtime-budget reports
- engine or browser runtime proof, provenance record, and rollback receipt

## Workflow-specific gates

- Reject unexpected bone scale, unstable constraints, collapsing joints, penetrations, foot skating, and discontinuous loops.
- Retargeting must preserve the original source and record both source and destination skeletons.
- Runtime textures, procedural geometry, and effect randomness must be deterministic from recorded parameters and seeds; the core workflow must not require a hosted service, paid model, downloaded art pack, post-processing stack, or particle engine.
- Parallel-transport frames must remain finite and stable across zero-length, collinear, sharply turning, split, and looping paths; shaders must compile without NaNs or undeclared renderer assumptions.
- Each named core, body, edge, ink, and ash palette must preserve readable band separation, and transparent layering must pass light, dark, and representative gameplay-background review.
- Cue firing must remain stable while playing, looping, seeking, changing frame rate, and crossing state transitions; reach and aim must derive from recorded rig, socket, and weapon measurements rather than unexplained constants.
- Composer state must round-trip deterministically, undo and redo without orphaned resources, and preview the same parameters and timing used by the runtime.
- Measure shader count, geometry and texture memory, draw calls, overdraw, concurrent effects, CPU update cost, and GPU frame time against explicit budgets before promotion.
- Identity-based motion or performance capture requires documented performer consent.

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
