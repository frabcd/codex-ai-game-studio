# Validation evidence

This page separates the current v1.1.1 hotfix candidate from the published
v1.1.0 and v1.0.0 historical records. Local evidence was reproduced on Windows
on 2026-07-31. Hosted and public-install evidence is updated only after the
exact candidate commit runs.

## v1.1.1 hotfix candidate record

| Gate | Local evidence on 2026-07-31 | Status |
|---|---|---|
| Repository contract | 85 core skills, 95 bundled skills, 49 roles, 12 mapped hook behaviors, 11 rules, 40 upstream templates, 163 catalog records, two edition descriptors, and pinned img2threejs provenance | **Pass** |
| Official validators | Every marketplace plugin and skill | **10/10 plugins and 95/95 skills pass** |
| Runtime unit tests | Detection, transactions, rollback scope, offline routing, release archives, Pages, security, and real separate-cache edition launcher subprocesses | **113/113 pass locally** |
| Installed edition boundary | Windows and macOS wrappers hand off only their canonical descriptor; core validates plugin identity, exact version, license, target OS, activation scope, and confirmation-gated rules; no copy or project-state write during doctor | **Pass** |
| Clean local Codex installation | Installed the core, Windows edition, and img2threejs plugins through the marketplace CLI into independent `1.1.1` cache roots; discovered 85 + 1 + 1 skills; the installed Windows doctor exited 0 from an empty project with no state file, descriptor copy, or descriptor hash change; all test entries were then removed | **Pass** |
| img2threejs portability and security | Native image conversion, external cache routing, CP1252-safe output, public HTTPS allowlists, download bounds, and hash-locked optional executables | **Pass** |
| Documentation build | Legal/support, tutorials, img2threejs, Windows, and macOS routes plus rewritten internal links and copied assets | **43 files; zero broken internal links** |
| Deterministic release | Two independent out-of-tree builds with identical filenames and SHA-256 values | **16/16 output files identical; 14 artifacts recorded** |
| Release immutability | Builder rejects a tag/package version mismatch; workflow serializes by requested tag and refuses an existing release before build or attestation | **Pass locally** |
| Hosted OS matrix | Windows, macOS, and Linux GitHub Actions | **Pending hotfix push** |
| Clean public installation | Marketplace install of core + matching platform + img2threejs from public `main` at v1.1.1 | **Pending hotfix publication** |

## v1.1.0 published and affected record

- Protected CI passed 109 tests on Windows, macOS, and Linux, all 15 pack jobs,
  official validators, CodeQL, and dependency review in
  [CI run 30603433632](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30603433632).
- [Release run 30603599328](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30603599328)
  published 16 checksummed and attested
  [v1.1.0 assets](https://github.com/frabcd/codex-ai-game-studio/releases/tag/v1.1.0).
- The extracted Windows edition sibling layout passed, but a clean public
  marketplace install reproduced `Unknown edition 'windows'. Available: none`
  with exit code 2 because Codex cached the platform and core plugins
  independently. The failed read-only doctor created no project state.

### v1.1.0 extracted-edition capture

The Windows edition ZIP was expanded outside the repository and used exactly as
a local marketplace. The test installed only the three plugins below, ran the
installed edition launcher, and removed the plugins, marketplace, cache entries,
and extraction directory afterward.

```text
marketplace: frabcd-ai-game-studio-windows
version: 1.1.0
coreSkills: 85
windowsEditionSkills: 1
img2threejsSkills: 1
doctorTargetMatches: true
doctorReadOnly: true
cleanup: complete
```

## Reproduce locally

```text
python tools/validate_repository.py
python tools/run_official_validators.py --require
python -m unittest discover -s tests -p "test_*.py"
python tools/build_release.py --version 1.1.1 --output dist
```

Run the pack transaction smoke test once per pack:

```text
python tools/mock_pack_matrix.py --pack unity
python tools/mock_pack_matrix.py --pack godot
python tools/mock_pack_matrix.py --pack unreal
python tools/mock_pack_matrix.py --pack blender
python tools/mock_pack_matrix.py --pack pixel
```

## v1.0.0 historical record

The linked workflows below ran against tagged commit
`304986f24b8d3bdb544c8ee97e70134c8c278c00` on 2026-07-30.

| Gate | Expected evidence | Status |
|---|---|---|
| Repository contract | Validator log with 85 skills, 49 roles, 12 hook behaviors, 11 rules, 40 templates, and 163 catalog records | **Pass locally** |
| Official plugin validator | Seven validator logs from the pinned official Codex source | **7/7 pass locally** |
| Official skill validator | 85 core logs plus optional-pack skill logs | **92/92 pass locally** |
| Runtime unit tests | Windows, macOS, and Linux CI links | **62/62 pass locally and on all three hosted operating systems** in [CI run 30561936522](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561936522) |
| Hook fixtures | Every supported event fixture on Windows and POSIX command paths | **9/9 pass on Windows, macOS, and Linux** in [CI run 30561936522](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561936522) |
| Pack transaction mocks | Plan, confirmed apply, health check, disable, and rollback for five host packs on three OS runners | **15/15 pass** in [CI run 30561936522](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561936522) |
| Catalog offline fallback | Network-disabled test log and snapshot digest | **Pass locally**; 163 records, source SHA-256 `acdfbb53d66400127f68529e447cc22872a7bc71e5cd994b0f4e32b10c2355a6` |
| Sprite fixture | Transparency, baseline, frame, loop, provenance, and preview evidence | **Pass locally** |
| 3D/PBR fixture | Topology, normals, UV, texture channels, LOD, collision, budget, and multi-view evidence | **Pass locally** |
| Animation fixture | Rig weights, root motion, foot sliding, loop continuity, and preview evidence | **Pass locally** |
| Audio fixture | Peaks, loudness, loop seam, consent, and provenance evidence | **Pass locally** |
| Scene/gameplay fixture | Navigation, lighting, reachable spawn, interaction smoke, frame time, draw calls, and screenshot regression | **Pass locally** |
| Code scanning | Python and GitHub Actions CodeQL analyses | **2/2 pass** in [CodeQL run 30561936424](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561936424) |
| Documentation deployment | Pages build and deployment with public legal/support routes | **Pass** in [Pages run 30561936448](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561936448); documentation, privacy, terms, and support routes return HTTP 200 |
| Deterministic release | Two independent build digests, `SHA256SUMS`, SPDX SBOM, and GitHub attestation | **Pass** in [release run 30562203287](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30562203287): 11 public assets, 10/10 checksum entries matched, and 11/11 provenance attestations present in [v1.0.0](https://github.com/frabcd/codex-ai-game-studio/releases/tag/v1.0.0) |
| Clean installation | Codex CLI and Desktop marketplace install capture | **Pass** from the public `main` snapshot: version `1.0.0`, enabled, **85 skills discovered**; test plugin and marketplace then removed cleanly |

## Clean-install capture

The README's exact commands were run from the Codex Desktop environment against
the public repository. No local-path marketplace was used.

```text
codexVersion: codex-cli 0.146.0-alpha.3.1
marketplaceName: frabcd-ai-game-studio
alreadyAdded: false
pluginId: ai-game-studio@frabcd-ai-game-studio
version: 1.0.0
enabled: true
skillCount: 85
explicitInvocation: AI_GAME_STUDIO_START_LOADED
publicSnapshot: 304986f24b8d3bdb544c8ee97e70134c8c278c00
bundleWarnings: 0
cleanup marketplacePresent: false
cleanup pluginPresent: false
```

## Before/after asset QA template

Record immutable source and candidate paths. Do not replace the source asset
until a human marks approval.

| Field | Source | Candidate |
|---|---|---|
| Artifact SHA-256 | Pending | Pending |
| Rights/provenance record | Pending | Pending |
| Technical validator output | Pending | Pending |
| Visual/temporal review | Pending | Pending |
| Runtime budget | Pending | Pending |
| Screenshot or preview | Pending | Pending |
| Human decision | Preserve | Pending |

## Universal-directory cases

Attach transcripts for the five positive and three negative review cases listed
in the repository's submission guide. Each transcript must show read-only
detection, one consolidated proposal, license/download/permission disclosure,
explicit digest confirmation, and rollback where a mutation is approved.
