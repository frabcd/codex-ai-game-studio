# Catalog contribution guide

The catalog is a curation database, not an install list. A record describes what a repository can do, where it can run, which rights are known, and what executing it would expose.

## Source of truth

- Stable records: `plugins/ai-game-studio/catalog/catalog.json`
- Volatile snapshots: `plugins/ai-game-studio/catalog/snapshots/`
- Schemas: `plugins/ai-game-studio/catalog/schemas/`
- Deterministic generator: `plugins/ai-game-studio/catalog/tools/generate_catalog.py`
- Immutable input snapshot: `sources/AI_GAME_GENERATION_GITHUB_LANDSCAPE.md`
- Excluded from that snapshot's repository counts and catalog records: the landscape section "External references — pricing and licensing"

Do not put stars, recent activity, latest release, archive state, or current default-branch SHA into stable curation. Do not let a metadata refresh rewrite summaries, capability decisions, risks, or licenses.

## Required review

1. Confirm canonical owner/name and repository URL.
2. Read the repository license and any model cards/dataset/output terms.
3. Separate code, weights, datasets, outputs, and commercial rights. An absent license is not permission.
4. Verify setup/usage documentation and a source release/tag/commit suitable for pinning.
5. Record claimed versus verified OS/architecture support.
6. Record runtimes, host applications, GPU backend/VRAM, disk, network, and authentication variable names.
7. Identify filesystem, process, network, editor, credential, and downloaded-code permissions.
8. Classify maturity and integration mode. Indexes, surveys, and benchmarks are usually reference-only.
9. Add or update tests and run catalog validation.

## License policy

`licenses.commercial_status` must be:

- `reviewed`: the catalog evidence supports the stated intended use.
- `conditional`: allowed only under recorded conditions.
- `blocked`: known terms conflict with the requested use.
- `unknown`: evidence is incomplete; commercial recommendation is blocked.

Never flatten a permissive code license into a claim about model weights, training datasets, outputs, faces, voices, trademarks, or input references.

## Pins and commands

Executable integrations need a release/tag/commit pin. Commands are token arrays, not interpolated shell strings. Package-manager resolution such as `latest`, floating Git branches, unverified curl-pipe-shell setup, and commands containing secrets fail validation.

## Authentication and privacy

List only environment-variable names such as `PROVIDER_API_KEY`; never values, examples that resemble live credentials, local `.env` contents, or headers. State whether inputs/outputs leave the machine and link the external privacy policy when hosted processing is possible.

## Add a repository

Edit the deterministic generator's curated input, regenerate, inspect the diff, and run:

```text
python plugins/ai-game-studio/catalog/tools/generate_catalog.py --check
python plugins/ai-game-studio/scripts/ai_game_studio.py validate catalog
python -m unittest tests.test_catalog -v
```

The pull request should explain evidence, unknowns, and why the capability mapping is useful. Screenshots are welcome but are not substitutes for license or platform evidence.

## Metadata refreshes

The scheduled workflow writes a new volatile snapshot on a dedicated branch and opens a review pull request. Maintainers review anomalies such as archival, ownership transfer, license changes, deleted tags, suspicious releases, or long inactivity. Automation never changes stable curation and never pushes a refresh directly to `main`.
