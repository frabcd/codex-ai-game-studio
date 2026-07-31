# Notices and provenance

Codex AI Game Studio is Copyright (c) 2026 frabcd and is licensed under the MIT License.

## Claude Code Game Studios adaptation

This distribution includes adapted workflow instructions and templates derived from:

- Project: [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios)
- Pinned source commit: `984023ddac0d5e27624f2baacde6105e45de375f`
- Source license: MIT
- Source author/copyright holder: as stated in the upstream repository and its license history

The adaptation preserves the 73 source workflow names and ports 49 roles, 12 hook behaviors, 11 scoped rules, and the 40 Markdown template files actually present at the pinned commit. Codex-specific changes include supported `SKILL.md` metadata, `agents/openai.yaml`, TOML role definitions, plugin lifecycle hooks, namespaced `$plugin:skill` references, generated `AGENTS.md` guidance, inherited model/permission behavior, and cross-platform Python launchers.

The complete derived-file mapping, status, test, source path, and destination is recorded in `parity/ledger.json`. This notice and that ledger must remain with redistributed derived files.

## img2threejs

The optional `ai-game-studio-img2threejs` plugin includes a modified,
runtime-focused snapshot of:

- Project: [img2threejs/img2threejs](https://github.com/img2threejs/img2threejs)
- Release tag: `v1.4.3`
- Pinned source commit: `9a8ecf129a58c1b557a1f03f7727f6295672cd51`
- Source license: Apache License 2.0
- Source copyright: the img2threejs contributors and copyright holders stated
  by the upstream project

The snapshot preserves the reconstruction forge, quality gates, and required
reference material. Packaging changes remove repository-development files and
generated caches, reduce `SKILL.md` frontmatter to Codex-supported fields, add
Codex UI metadata, and replace host-specific path assumptions with
plugin-relative guidance. Runtime hardening moves indexes outside the installed
plugin, adds Windows/macOS native image conversion with hash-locked external
fallbacks, bounds and validates optional metadata downloads, and requires a
confirmed absolute path and SHA-256 before an external texture extractor can
run. The exact source and modification record is stored in
`plugins/ai-game-studio-img2threejs/UPSTREAM.json`; the upstream Apache-2.0
license remains in the plugin and skill distribution.

## Repository catalog

`sources/AI_GAME_GENERATION_GITHUB_LANDSCAPE.md` is the immutable source snapshot used to produce the 163-record offline catalog. Its SHA-256 is:

`ACDFBB53D66400127F68529E447CC22872A7BC71E5CD994B0F4E32B10C2355A6`

Catalog entries are factual metadata and links. Listed repositories, source code, model weights, datasets, documentation, trademarks, and outputs remain the property of their respective owners and are governed by their own licenses and terms. Inclusion is not endorsement.

## Other references

Existing Codex ports and OpenAI's browser-focused Game Studio plugin informed compatibility research only; their source files were not copied into this project. Optional MCP servers are referenced by pinned metadata and remain external dependencies unless a user explicitly approves their installation.

## Generated artwork

The project hero and icon were generated for this repository with OpenAI image generation on 2026-07-30 from original project-specific prompts. They depict generic game-production concepts and intentionally contain no third-party logos or copyrighted game characters.
