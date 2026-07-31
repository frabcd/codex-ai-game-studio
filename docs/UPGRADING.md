# Upgrade guide

## Before upgrading

1. Finish or rollback active transactions.
2. Commit or otherwise back up project-owned `.ai-game-studio/project.json` and `lock.json` if your team tracks them.
3. Record enabled optional packs and run `doctor`.
4. Review the release notes for schema, hook, pack-pin, permission, and migration changes.

Use `/plugins` to refresh the `frabcd-ai-game-studio` marketplace and update selected plugins. Start a new task afterward so skill and hook metadata reload.

## Upgrade from 1.0.0 to 1.1.0

The 1.1 release preserves the 85-skill core and schema version 1 project files.
It adds three optional plugins and does not select a platform automatically.

```text
codex plugin marketplace upgrade frabcd-ai-game-studio
codex plugin add ai-game-studio@frabcd-ai-game-studio
codex plugin add ai-game-studio-windows@frabcd-ai-game-studio
# On macOS, install ai-game-studio-macos instead.
codex plugin add ai-game-studio-img2threejs@frabcd-ai-game-studio
```

Start a new task and invoke the matching explicit setup skill. It resolves its
installed native launcher, runs `doctor`, then presents `plan`. Edition
selection does not install applications, packages, MCPs, models, Rosetta, or
WSL. Applying the selection still requires the exact digest.

The img2threejs plugin is Apache-2.0 and pinned to upstream `v1.4.3`. Review
`NOTICE.md` and the plugin's `UPSTREAM.json` before redistribution. It is
separate from the MIT core so teams can opt into its third-party license
deliberately.

The img2threejs runtime no longer writes search indexes into its installed
plugin. Use `--cache-root`, `AI_GAME_STUDIO_CACHE_DIR`, or the bounded OS user
cache. ImageMagick and Source2Viewer fallbacks require confirmed, hash-locked
tool manifests; an executable discovered only through `PATH` is rejected.

## Core compatibility

Patch releases preserve schemas and command behavior. Minor releases may add optional fields and skills. A major release may require a generated migration plan. The CLI refuses to rewrite a newer unknown project/lock schema.

## Hook changes

Codex trust is tied to a hook definition's hash. After an automation-pack update, use `/hooks` to review changed commands before trusting them. An update does not preserve trust for modified hook code.

## Pack pin changes

Plugin updates can recommend a newer upstream MCP but cannot silently change a project's lock. Run `pack doctor` and `pack plan`; review upstream license, permissions, download, and compatibility differences, then confirm the new digest. Rollback retains the prior pin and config backup.

## Catalog changes

Volatile metadata snapshots do not change a project's locked dependency. Stable curation changes are reviewed in pull requests and can make a prior commercial recommendation conditional or blocked. Re-run recommendation before a release milestone.

## Downgrade

Use `/plugins` to select a prior marketplace/plugin release where available, then restore compatible project/lock files from version control. Do not hand-edit schema versions or transaction digests. Optional external tools may require their own supported downgrade procedure.
