# Validation evidence

This page separates the current v1.1 release-candidate evidence from the
published v1.0 historical record. Local v1.1 evidence was reproduced on Windows
on 2026-07-31; hosted Windows, macOS, and Linux evidence will be linked after
the candidate commit runs through CI.

## v1.1 release-candidate record

| Gate | Local evidence on 2026-07-31 | Status |
|---|---|---|
| Repository contract | 85 core skills, 95 bundled skills, 49 roles, 12 mapped hook behaviors, 11 rules, 40 upstream templates, 163 catalog records, two edition descriptors, and pinned img2threejs provenance | **Pass** |
| Official plugin validator | Every marketplace plugin, including img2threejs, Windows, and macOS | **10/10 pass** |
| Official skill validator | Core, automation, editor packs, img2threejs, Windows, and macOS skills | **95/95 pass** |
| Runtime unit tests | Detection, transactions, rollback scope, offline routing, release archives, Pages, both edition launchers, security fixtures, and checkout-independent text normalization | **108/108 pass** |
| Windows/macOS edition boundary | Repository and marketplace-cache launcher layouts; real host probes; OS mismatch rejection; digest-bound apply/disable/rollback; no external installation during edition selection | **Pass** |
| img2threejs portability | Native Windows and macOS image-conversion routes, external user cache routing, and plugin-source write rejection | **Pass** |
| img2threejs security | Public HTTPS allowlists, redirect and size limits, safe numeric outputs, preserve-existing behavior, hash-locked ImageMagick and Source2Viewer manifests, and bounded subprocesses | **Pass** |
| Documentation build | Legal/support, tutorials, img2threejs, Windows, and macOS routes plus rewritten internal links and copied assets | **43 files; zero broken internal links** |
| Deterministic release | Two independent out-of-tree builds with identical filenames and SHA-256 values | **16/16 output files identical; 14 artifacts recorded** |
| Extracted Windows edition installation | Add the packaged local marketplace, install core + Windows + img2threejs, run the installed native doctor, then remove all test state | **Pass; 85 + 1 + 1 skills, v1.1.0, read-only host match, clean removal** |
| Hosted OS matrix | Windows, macOS, and Linux GitHub Actions | **Pending candidate push** |
| Clean public installation | Marketplace install from the public v1.1 tag | **Pending candidate publication** |

### v1.1 extracted-edition capture

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
python tools/build_release.py --version 1.1.0 --output dist
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
