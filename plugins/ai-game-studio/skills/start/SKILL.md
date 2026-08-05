---
name: start
description: "First-time onboarding — asks where you are, then guides you to the right workflow. No assumptions."
---

> Port provenance: adapted from the pinned upstream source at `984023ddac0d5e27624f2baacde6105e45de375f` under MIT; see the repository parity ledger for the exact path and blob.

# Start: safe game-studio router

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

## Codex portability

Use the search, file-editing, shell, user-input, and subagent capabilities available in the active Codex surface. Use PowerShell syntax on Windows and POSIX syntax on macOS/Linux; do not require a Unix compatibility layer on Windows. Inherit the active model and permission mode, and do not weaken approval or sandbox boundaries.
