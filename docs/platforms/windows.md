---
layout: default
title: Windows Edition
permalink: /platforms/windows/
---

# Codex AI Game Studio for Windows

The Windows edition adds native-first environment detection and deterministic adaptation rules to the universal core. It does not install an engine, editor, MCP server, package, model, or GPU runtime by itself.

```text
codex plugin add ai-game-studio-windows@frabcd-ai-game-studio
```

Start a new Codex task, type `/`, and select **Set up the Windows edition**, or invoke `$ai-game-studio-windows:setup-windows-edition` explicitly. The skill is explicit-only so ordinary Windows questions cannot start setup.

## Safety contract

The workflow always uses this sequence:

1. The installed plugin's native launcher runs `doctor --project <root>` read-only.
2. The same launcher runs `plan --project <root> --output <plan.json>` to create one reviewable proposal.
3. Codex shows exact actions, immutable pins, downloads, licenses, permissions, backups, rollback, expiry, and a SHA-256 digest.
4. You repeat that digest verbatim.
5. Only then may `apply --project <root> --plan <plan.json> --confirmed-digest <digest>` change the approved state files.

General approval is not digest confirmation. Preview-only requests stop after the proposal. Disabling or rolling back is a new transaction with a new digest.

Resolve `<windows-plugin-root>` to the installed
`ai-game-studio-windows` plugin. Its launcher finds only the exact matching
core patch beside the extracted edition or in the same Codex marketplace cache.
When Codex caches the plugins independently, the launcher supplies its
canonical descriptor path; the core validates the containing plugin identity,
version, license, target OS, activation scope, and confirmation rules before
reading it in place:

```text
& "<windows-plugin-root>\scripts\ai-game-studio-windows.ps1" doctor --project <root>
& "<windows-plugin-root>\scripts\ai-game-studio-windows.ps1" plan --project <root> --output <plan.json>
& "<windows-plugin-root>\scripts\ai-game-studio-windows.ps1" apply --project <root> --plan <plan.json> --confirmed-digest <digest>
```

## Native compatibility

| Area | Native routes | Guardrail |
|---|---|---|
| Architecture | Windows `amd64` and `arm64` | Executable architecture and hash must match the plan |
| Shell | PowerShell 7; Windows PowerShell 5.1 fallback | Prefer standard-library Python for portable helpers; no nested command-string evaluation |
| Packages | winget, Chocolatey, Scoop | Verify package identity, publisher, exact version, checksum, and license |
| GPU | CUDA, DirectML, CPU, WARP | Backend capability is tested; no backend is called binary-compatible with Metal |
| Engines | Unity, Godot, Unreal Engine | Discover without launching or importing a project |
| DCC and 2D | Blender, Aseprite, Pixelorama, Tiled | Confirm native executable, license, version, and project format |
| WSL | Confirmed command-line fallback only | Do not use for GUI editor control or silent cross-filesystem writes |

When a useful upstream tool is macOS-, POSIX-, Apple-Silicon-, Homebrew-, or Metal-bound, Codex tries a licensed native source adaptation first. If that cannot be tested, it compares verified Windows capability equivalents. A hosted service or manual interchange handoff is the last route. Every substitution states capability, output quality, cost, performance, privacy, license, and limitations before asking for confirmation.

## Tutorial 1: Adopt an existing Windows game project

### What to say

```text
$ai-game-studio-windows:setup-windows-edition Inspect this existing Windows
game project read-only. Detect its engine and version, amd64 or arm64, native
PowerShell and Python, installed editors and DCC tools, active MCP servers,
GPU/VRAM and CUDA/DirectML/CPU options, package managers, disk space, and Git
state. Propose one native setup with exact pins, licenses, permissions,
downloads, health checks, expected artifacts, and rollback. Do not install,
download, launch an editor, enable an MCP, or write project configuration until
I repeat the transaction digest.
```

### What Codex inspects

- Project markers such as `ProjectVersion.txt`, `project.godot`, `.uproject`, `.blend`, `.aseprite`, `.pxo`, `.tmx`, and `.world`.
- Native Windows architecture, shells, runtimes, package managers, editor paths, GPU/driver metadata, free disk space, MCP host names, and Git state.
- Credential environment-variable names only; it does not read secret values.

### What it asks

- Which installed engine version is authoritative, whether editor launch is permitted after confirmation, target hardware, commercial-use requirements, and the maximum acceptable downloads.

### What it proposes

- The universal core plus only the compatible Windows, engine, DCC, pixel, or automation packs.
- Exactly one MCP server per host application, immutable dependency pins, quality gates, permissions, backups, and a rollback transaction.

### What it may change after confirmation

- Only the transaction-listed Codex/MCP configuration, `.ai-game-studio/project.json`, `.ai-game-studio/lock.json`, approved adapter files, and narrowly scoped project/editor integration files.

### Expected artifacts and rollback

- Doctor report, proposal JSON, lock state, health-check results, transaction receipt, and evidence paths.
- Run the launcher with `disable` to propose deactivation or `rollback <transaction-id>` to propose restoration. Both require a new digest. Pre-existing applications and files remain untouched unless their exact removal is separately approved.

## Tutorial 2: Plan a new Windows game workstation

### What to say

```text
$ai-game-studio-windows:setup-windows-edition Plan a Windows-native toolchain
for a new [2D/3D] game in [Unity/Godot/Unreal/browser] targeting [platform].
My priorities are [quality/speed/local privacy/low cost], my download limit is
[size], and commercial use is [required/not required]. Inspect this machine
read-only, prefer already-installed tools, select one GPU route, and explain
every license and permission. Propose the smallest reversible setup and wait
for the exact digest before any download, install, login, process launch, or
configuration change.
```

### What Codex inspects

- `amd64` or `arm64`, Windows and PowerShell versions, Python/Node/Git, installed package managers, engines, DCC tools, GPU providers, VRAM evidence, disk, and existing Codex MCP configuration.

### What it asks

- Game engine and target constraints, local versus hosted preference, asset rights, acceptable package sources, editor-control needs, and quality/performance budgets.

### What it proposes

- One minimal native toolchain, one GPU backend, verified sources and exact pins, download estimates, licenses, security scopes, health checks, and rollback.

### What it may change after confirmation

- Only explicitly listed packages, adapters, environment entries, Codex configuration, and project-state files. Editors and external applications remain external dependencies unless their installation is named in the plan.

### Expected artifacts and rollback

- Machine capability report, compatibility decision, confirmed lockfile, application/version inventory, smoke-test evidence, and transaction receipt.
- Disable removes active edition routing; rollback restores backed-up configuration and transaction-owned files. Package or application removal requires its own explicit proposal.

## Tutorial 3: Adapt a macOS-, POSIX-, or Metal-only workflow

### What to say

```text
$ai-game-studio-windows:setup-windows-edition This workflow currently depends
on [tool and pinned source], which is [macOS app/POSIX launcher/Homebrew
package/Apple-Silicon binary/Metal backend]. Determine whether its licensed
source can be adapted to native Windows without changing its artifact contract.
If not, compare verified Windows capability-equivalent alternatives by
features, output quality, cost, performance, privacy, license, and limitations.
Use hosted, manual, or WSL fallback only if native routes fail. Never claim
binary compatibility. Show tests, expected artifacts, permissions, and rollback,
then wait for my transaction digest before changing anything.
```

### What Codex inspects

- The pinned upstream source, license, build graph, artifact formats, tests, required frameworks, native Windows releases, and hardware/runtime requirements.
- Windows architecture, GPU backends, available interchange tools, and whether the workflow needs GUI editor control.

### What it asks

- Which capabilities and quality thresholds are non-negotiable, whether source compilation is acceptable, data privacy boundaries, hosted-service budget, and whether WSL filesystem/process limits are acceptable.

### What it proposes

- First: a testable standard-library Python or argument-array PowerShell adaptation from portable source.
- Second: a verified native alternative with a side-by-side capability and evidence table.
- Last: a hosted, manual, or WSL handoff with every boundary and limitation disclosed.

### What it may change after confirmation

- A new Windows launcher or adapter, pinned dependencies, test fixtures, interchange scripts, and edition lock state. Originals remain preserved until human approval of before/after evidence.

### Expected artifacts and rollback

- Source/license decision, adaptation patch or alternative-selection record, format and quality comparison, performance capture, provenance record, and reversible transaction receipt.
- Rollback restores the previous launcher, dependency pins, host selection, and configuration. Generated alternatives stay beside originals unless replacement was explicitly approved.

## Tutorial 4: Choose a Windows GPU route for generation

### What to say

```text
$ai-game-studio-windows:setup-windows-edition Inspect this Windows machine
read-only for a local [sprite/3D/texture/animation] generation workflow. Verify
the GPU, driver, VRAM, architecture, and the selected tool's exact CUDA,
DirectML, or CPU support. Compare quality, determinism, memory, throughput,
license, model-weight terms, and download size. Treat WARP as validation-only.
Propose one route and a smaller fallback, with representative quality and
performance gates. Wait for the digest before downloads or configuration.
```

### What Codex inspects

- GPU and driver metadata, tool/backend compatibility, model and weight licenses, VRAM and disk requirements, existing caches, and representative output fixtures.

### What it asks

- Required output resolution and volume, maximum latency, acceptable precision/determinism changes, commercial rights, and whether a hosted fallback may receive project data.

### What it proposes

- One verified backend, exact model/tool pins, estimated downloads and memory, quality/performance gates, fallback thresholds, permissions, and rollback.

### What it may change after confirmation

- Approved runtime packages, model cache entries, adapter configuration, lock state, and evidence fixtures. Source assets are never replaced automatically.

### Expected artifacts and rollback

- Backend capability report, benchmark and representative outputs, license/provenance record, visual QA evidence, lockfile, and receipt.
- Rollback restores environment and adapter configuration and removes only transaction-owned caches when their exact paths and ownership were confirmed.

## Troubleshooting boundaries

- If doctor reports WSL, rerun from native Codex on Windows for GUI editor workflows.
- If a package-manager name matches but provenance does not, use the pinned upstream release or stop for review.
- If CUDA is unavailable, verify DirectML support for the exact tool; do not infer it from the GPU alone.
- If only an Apple-Silicon or macOS build exists, treat it as unavailable until portable source or a verified Windows equivalent passes the artifact and quality gates.
- If rollback ownership is uncertain, preserve the file and report it instead of deleting it.
