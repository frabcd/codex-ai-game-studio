# Procedural Three.js VFX Composer

Use this reference only for the optional browser/Three.js route of
`rig-animation`. The route authors stylized combat effects, binds them to
animation cues, and provides a local cue/effect editor. It does not replace the
skill's normal rigging, retargeting, deformation, contact, or loop checks.

## Non-negotiable boundary

- Work local-first with the target project's existing `three` dependency.
- Do not install packages, download media, contact hosted services, or add
  telemetry, CDNs, remote assets, `EffectComposer`, bloom, or a particle engine.
- Preserve source meshes and clips. Generate only in a candidate directory.
- Complete read-only detection and present one exact path-and-digest plan before
  copying starter assets or changing project files.
- Use a synthetic procedural mannequin, weapon, and clips when rights-cleared
  production inputs are unavailable.
- Require human approval before candidate output replaces production content.

## Inputs

Collect or conservatively derive:

- target Three.js revision, build/test commands, renderer, coordinate axes, and
  units per metre;
- rights-cleared rig, clips, bone map, weapon-base socket, and weapon-tip socket;
- effect list, style guide, five-role palettes, cue timing, and target hardware
  budgets;
- capture resolution, representative cameras, backgrounds, and sample times.

An approved art bible's color, shape, VFX, animation, and accessibility rules
take precedence over starter values.

## Reusable resources

The sibling `assets/procedural-vfx-composer/` directory contains a versioned
example manifest and JSON Schema. Copy them only after the candidate plan is
confirmed, then adapt values without adding executable code or URLs to the
manifest.

Resolve `<rig-animation-skill-root>` from the installed or checked-out skill;
do not assume the game project's working directory contains the validator. Then
validate a manifest read-only with:

```text
python <rig-animation-skill-root>/scripts/validate_vfx_spec.py path/to/vfx-project.json
python <rig-animation-skill-root>/scripts/validate_vfx_spec.py path/to/vfx-project.json --json
```

The validator uses only the Python standard library, reads at most one MiB,
rejects duplicate JSON keys and non-finite values, bounds collection sizes and
numeric work, rejects known network/file/data/executable URI schemes plus
absolute paths and parent traversal, forbids executable fields, and writes no
files.
The input root must be one JSON object. A valid text run exits `0` and prints
`PASS sha256:<canonical-digest>`; an invalid run exits `1` and prints bounded
`ERROR` lines. With `--json`, stdout is one object containing only `valid`,
`digest`, and `errors`.

## Manifest contract

`vfx-project.json` defines:

- deterministic seed, units, Three.js revision, and style parameters;
- exactly eight named palettes with `core`, `body`, `edge`, `ink`, and `ash`;
- bounded effect presets, geometry/shader layers, durations, and local budgets;
- normalized point or window cues bound to clips and rig sockets;
- rig axes, semantic bone map, weapon sockets, and scale metrics;
- global active-effect, layer, vertex, draw-call, texture, shader, and frame-time
  budgets;
- deterministic camera, DPR, background, and sample-time capture settings.

The JSON contains data only. It has no fields for shader source, scripts,
network locations, or arbitrary file paths.

## Runtime architecture

### Computed texture

Create one seeded RGBA `THREE.DataTexture` from a bounded `Uint8Array`:

- R: periodic integer-hash value noise;
- G: bounded-octave FBM;
- B: domain-warped FBM;
- A: radial crack field.

Treat it as non-color data, disable mip generation, select explicit wrap and
filter modes, and upload only at creation or an explicit reseed. Never regenerate
it each frame.

### Geometry

Provide ten bounded `BufferGeometry` factories: triangle, crescent, flare ring,
ground disc, star, shard, rubble, puff, flame shell, and flame tongue. Provide a
separate dynamic tube for trails, beams, and bolts.

Build the tube with preallocated typed arrays and rotation-minimizing parallel
transport frames. Reject duplicate samples and near-180-degree tangent turns.
Update existing dynamic attributes rather than allocating new geometry each
frame. Path parameters may produce straight, wobbly, jagged, or split forms.

### Shading and palettes

Compose a fixed registry of approximately 29 GLSL blocks: shared hash/noise,
shape, edge, erosion, band, palette, contour, and heat helpers; vertex/frame and
lifetime helpers; and effect assemblies. Do not accept shader strings from JSON.

Drive all palette roles through uniforms so palette changes do not create shader
variants. Use normal alpha blending for dark body/ink layers and additive,
`depthWrite=false` geometry for outer glow. Sparks and rubble are bounded pooled
mesh instances, not points and not a general particle system.

### Rig-scaled cues

Measure weapon length from the current world-space base and tip sockets. Sample
tip velocity around the cue to orient slashes toward the actual blow. Allow scale
by weapon length, rig height, named bone distance, or a fixed multiplier.

Evaluate cue crossings against normalized clip time. A gameplay cue fires once
per forward crossing, including loop wrap and crossfade. Pause does nothing;
reverse or seek updates preview state without emitting a gameplay event. Keep
point cues and continuous cue windows distinct.

### Local editor/composer

The generated project interface should expose a viewport, clip selector,
transport, cue timeline, effect-layer tree, palette/noise/shape inspector,
compile log, and live renderer metrics. Support undo/redo, explicit JSON
import/export, deterministic capture, and an effect-sheet view. Keep state local
and make no network requests.

The editor must be keyboard operable, visibly focused, labelled, pausable, and
respect reduced motion. Prevent unsafe flash rates. Here, "composer" means an
effect-layer and animation-cue editor; it never refers to Three.js postprocessing.

## Blocking quality gates

| Gate | Pass condition |
| --- | --- |
| Manifest | Validator returns zero errors and the canonical manifest digest is recorded. |
| Noise | Same seed/config gives identical bytes; channels are finite, non-flat, bounded, and periodic. |
| Geometry | No non-finite values, invalid indices, empty triangles, bad bounds, or declared-budget overflow. |
| Tube | No zero tangent, frame flip, seam split, steady-state allocation, or attribute-size change. |
| Shader | Every approved layer combination compiles and links with shader checks enabled. |
| Architecture | No postprocessing, bloom, particle package, remote asset, network call, or telemetry. |
| Cue | Forward, pause, loop, crossfade, speed, reverse, and seek tests pass without duplicate gameplay fires. |
| Attachment | Socket alignment error is no more than the larger of 1 cm or 1% of measured weapon length. |
| Visual | Fixed-time effect sheets pass on light, dark, and checker backgrounds from representative views. |
| Temporal | No trail twist, popping, lifetime discontinuity, clipping, z-fighting, or band collapse. |
| Runtime | Target-hardware measurements meet declared budgets and resource counts return to baseline after recycling. |
| Accessibility | Pause, reduced motion, keyboard/focus/labels, and flash-safety checks pass. |
| Production | Rights/provenance evidence and explicit human approval are present. |

Exact screenshot hashes are appropriate only on the same renderer/GPU setup.
Across different GPUs, use controlled captures and visual review rather than
claiming pixel-identical output.

## Primary references

- [Three.js DataTexture](https://threejs.org/docs/pages/DataTexture.html)
- [Three.js ShaderMaterial](https://threejs.org/docs/pages/ShaderMaterial.html)
- [Three.js BufferAttribute](https://threejs.org/docs/pages/BufferAttribute.html)
- [Three.js InstancedMesh](https://threejs.org/docs/pages/InstancedMesh.html)
- [Three.js AnimationMixer](https://threejs.org/docs/pages/AnimationMixer.html)
- [Three.js MIT license](https://github.com/mrdoob/three.js/blob/dev/LICENSE)
- [Wang et al., Computation of Rotation Minimizing Frames](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/Computation-of-rotation-minimizing-frames.pdf)
- [W3C Three Flashes or Below Threshold](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)
