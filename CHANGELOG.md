# Changelog

All notable changes are recorded here. The project follows Semantic Versioning.

## [1.1.0] - 2026-07-31

### Added

- Optional Apache-2.0 `ai-game-studio-img2threejs` plugin pinned to upstream
  `v1.4.3` for quality-gated, procedural image-to-Three.js reconstruction.
- First-class `ai-game-studio-windows` and `ai-game-studio-macos` plugins with
  native detection, explicit setup skills, capability-equivalent adaptation
  rules, and digest-confirmed edition selection.
- Curated Windows and macOS release archives that include the universal core,
  compatible editor packs, the img2threejs workflow, and exactly one matching
  platform plugin.
- Deterministic `edition doctor|plan|apply|disable|rollback` runtime commands.

### Changed

- Expanded the marketplace from seven to ten plugins and from 92 to 95 bundled
  skills while preserving the 85-skill universal core and all v1 parity counts.
- Declared mixed MIT and Apache-2.0 provenance in release metadata and the SBOM.
- Normalized nested `.gitignore` files to LF for byte-identical release builds
  across Windows and POSIX checkouts.
- Added marketplace-cache-aware native edition launchers, frontmatter-aware
  Pages routing, and self-installing local marketplace instructions inside both
  platform archives.

### Safety

- Platform-bound tools are never described as binary-compatible substitutes.
  Codex tries a licensed native source adaptation, then a verified
  capability-equivalent alternative, then a disclosed hosted/manual fallback;
  every substitution still requires confirmation.
- Edition selection records no external installation. Package, model, editor,
  MCP, Rosetta, WSL, hosted-service, or application-control changes remain
  separate reviewable transactions.
- img2threejs keeps runtime caches outside the installed plugin, converts common
  images through native Windows/macOS routes, blocks unsafe/private metadata
  targets, caps downloads, and refuses unpinned ImageMagick or Source2Viewer
  executables.
- `edition apply` accepts only edition state plans and rejects other plan kinds
  or targets outside the two scoped `.ai-game-studio` state files.

## [1.0.0] - 2026-07-30

### Added

- Universal core plugin with 85 Codex-native skills and `agents/openai.yaml` metadata.
- Full pinned parity coverage for 73 source workflows, 49 roles, 12 hook behaviors, 11 path rules, and 40 upstream templates.
- Twelve generative-game workflows for discovery, prompt-to-game, 2D, 3D, materials, rigs, animation, worlds, NPC/audio, engine automation, visual QA, and reversible enhancement.
- Offline, schema-backed catalog of 163 verified GitHub repositories and production recipes.
- Cross-platform standard-library Python doctor, catalog, pack, migration, and validation commands.
- Digest-confirmed transaction planning, backups, health checks, disable, and rollback.
- Optional automation, Unity, Godot, Unreal, Blender, and pixel-art marketplace packs.
- Tutorials, prompt cookbook, compatibility matrices, security/privacy/legal pages, CI, weekly metadata refresh, deterministic releases, checksums, and SBOM generation.

### Safety

- No mutation, external installation, model download, or source-asset replacement before explicit digest confirmation.
- Unknown/custom commercial terms, unlicensed identity references, and non-consensual voice cloning block production workflows.
