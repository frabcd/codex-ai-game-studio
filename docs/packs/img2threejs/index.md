---
layout: default
title: img2threejs Pack
permalink: /packs/img2threejs/
---

# img2threejs pack

The optional `ai-game-studio-img2threejs` plugin vendors the Apache-2.0
`img2threejs` v1.4.3 workflow at commit
`9a8ecf129a58c1b557a1f03f7727f6295672cd51`. It turns a supplied object or
character reference into procedural Three.js code through an intake,
specification, staged build, multi-view review, and bounded correction loop.
It is reconstruction by code, not photogrammetry, mesh extraction, or an
automatic promise of unseen geometry.

Install it after adding the repository marketplace:

```text
codex plugin add ai-game-studio-img2threejs@frabcd-ai-game-studio
```

Then start a new Codex task and say:

```text
Use $ai-game-studio-img2threejs:img2threejs with this reference image.
First validate that the reference is usable, ask me for the intended game use
and quality target, write a quality contract, and propose the staged build.
Preserve uncertainty about hidden views. Build only in my approved project
directory, show evidence at every gate, and do not call an approximation exact.
```

## What Codex inspects

- the supplied image path, screenshot, URL, or attachment;
- intended use, interaction and animation requirements, target frame budget,
  and permitted output directory;
- the repository's existing Three.js toolchain and asset conventions;
- reference rights, identity and consent constraints, and any commercial-use
  requirement;
- visible silhouette, component hierarchy, proportions, materials, pivots,
  sockets, action anchors, and features hidden by the available views.

## What Codex asks and proposes

Codex asks for missing reference views, intended use, fidelity target, topology
or animation expectations, platform budget, and whether a stylized
approximation is acceptable. It then proposes a quality contract, component
specification, ordered passes, per-pass acceptance criteria, capture angles,
performance limits, provenance fields, and a bounded correction budget.

## What it may change

The skill writes specifications, generated Three.js source, renders, and review
evidence only inside the user-approved project or output directory. The
installed plugin remains read-only. A local BM25 index uses an explicit
`--cache-root`, `AI_GAME_STUDIO_CACHE_DIR`, or the bounded OS user cache, never
the plugin source. It does not install npm packages, download models, replace
production assets, upload the reference, or control an editor unless those
actions are separately proposed and confirmed.

PNG decoding is dependency-free. Windows System.Drawing and macOS `sips` cover
common native conversions. ImageMagick and Source2Viewer are never selected
from `PATH`: either tool needs a separate confirmed manifest with an absolute
executable, SHA-256, version, reviewed license, HTTPS source, and transaction
digest. Unsupported image formats stop for an approved conversion.

## Expected artifacts and rollback

Expected artifacts include an image probe, observation record, quality
contract, component/material/interaction specification, pass ledger,
procedural Three.js source, deterministic multi-view captures, visual review,
performance evidence, known limitations, and provenance. Keep each pass in
version control or beside the prior pass. Rollback restores the last accepted
source/specification and removes only explicitly identified generated
candidates; the reference and accepted production assets remain untouched.

The vendored source, exclusions, and six Codex portability adaptations are
recorded in `plugins/ai-game-studio-img2threejs/UPSTREAM.json`. The plugin keeps
the upstream Apache-2.0 license; the rest of Codex AI Game Studio remains MIT
unless a bundled component says otherwise.
