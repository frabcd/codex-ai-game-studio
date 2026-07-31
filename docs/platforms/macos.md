---
layout: default
title: macOS Edition
permalink: /platforms/macos/
---

# Codex AI Game Studio for macOS

The macOS edition selects a native, reversible platform policy for Apple Silicon and Intel Macs. Selection does not install Homebrew, MacPorts, Rosetta, an engine, a DCC application, an MCP server, a model, or a runtime.

Invoke the setup skill explicitly:

```text
Use $ai-game-studio-macos:setup-macos-edition to inspect this Mac and propose one native game-studio setup. Do not change anything until I repeat the complete plan digest.
```

## Safety contract

The workflow has five separate phases:

1. The native launcher's `doctor` command performs read-only macOS detection.
2. Its `plan` command creates one digest-bound macOS proposal.
3. You review the environment, actions, license, permissions, backups, expiry, and rollback.
4. Its `apply` command runs only after you repeat that exact full digest.
5. Doctor and project-state checks provide evidence; external tools remain unchanged.

The edition recognizes Darwin on `arm64` and `x86_64`, zsh/POSIX shells, Homebrew and MacPorts, Metal/MPS/Core ML/CPU, and Unity, Godot, Unreal, Blender, Aseprite, Pixelorama, and Tiled. Detection checks presence and metadata; it does not launch applications, update package managers, or read credential values.

Resolve `<macos-plugin-root>` to the installed `ai-game-studio-macos` plugin.
Its native launcher finds only the exact matching core patch beside the
extracted edition or in the same Codex marketplace cache. When Codex caches the
plugins independently, the launcher supplies its canonical descriptor path;
the core validates the containing plugin identity, version, license, target OS,
activation scope, and confirmation rules before reading it in place:

```text
"<macos-plugin-root>/scripts/ai-game-studio-macos.sh" doctor --project <root>
"<macos-plugin-root>/scripts/ai-game-studio-macos.sh" plan --project <root> --output <plan.json>
"<macos-plugin-root>/scripts/ai-game-studio-macos.sh" apply --project <root> --plan <plan.json> --confirmed-digest <digest>
```

Expected artifacts after confirmed selection:

- a read-only doctor report in the task output;
- the saved, digest-bound plan at the path you chose;
- `.ai-game-studio/project.json` with the selected macOS edition;
- `.ai-game-studio/lock.json` with version and descriptor digest;
- a bounded transaction record usable for rollback.

## What to say: adopt an existing Mac game project

Copy and paste:

```text
Use $ai-game-studio-macos:setup-macos-edition on this existing project. Inspect Darwin version, Apple Silicon or Intel architecture, shell, GPU backends, disk, engine/DCC installations, project files, worktree state, and existing MCP servers without changing anything. Propose exactly one native setup with licenses, permissions, downloads, expected artifacts, quality checks, and rollback. Wait for me to repeat the full digest.
```

Codex inspects read-only system and project metadata. It may ask which engine/project is authoritative when markers conflict and whether local-only processing is required. It proposes edition selection plus separate optional engine or DCC plans. The edition apply may change only the two `.ai-game-studio` state files. Roll back with the transaction workflow below; source assets and installed applications stay untouched.

## What to say: adapt a Windows, PowerShell, CUDA, or DirectML workflow

Copy and paste:

```text
Use $ai-game-studio-macos:setup-macos-edition to adapt this Windows-oriented game-generation workflow for macOS. Classify every EXE/DLL, Windows PowerShell, registry/COM/UI-automation, CUDA, and DirectML dependency. Prefer a verified native source adaptation, then compare capability-equivalent macOS alternatives, then propose a hosted or manual fallback. Do not claim binary compatibility. Show license, privacy, cost, quality, performance, limitations, test evidence, and rollback for every substitution, and wait for my confirmation.
```

Codex inspects dependency manifests, scripts, model formats, output formats, licenses, and quality gates. It asks which outputs and performance limits are non-negotiable. The proposal records a deterministic route for each incompatible capability. No port, download, model conversion, hosted upload, or tool replacement occurs in edition selection. Expected artifacts are an adaptation matrix, validation criteria, and one or more later digest-bound implementation plans.

## What to say: build an Apple Silicon local-generation pipeline

Copy and paste:

```text
Use $ai-game-studio-macos:setup-macos-edition for an Apple Silicon local AI game-art pipeline. Inspect unified memory, Metal/MPS/Core ML support, disk, model and output licenses, Blender and engine versions, and current tools without running a model. Propose one local-first pipeline for my required 2D, 3D, texture, or animation artifacts, with memory estimates, quality gates, fallbacks, and rollback. Wait for full-digest confirmation before any install or download.
```

Codex asks for artifact types, quality target, commercial-use requirement, maximum download size, and acceptable generation time. It distinguishes Metal/MPS/Core ML implementations from CUDA implementations and blocks unknown commercial model terms. Expected artifacts include a capability report, memory/download estimates, exact dependency pins, provenance fields, and asset-quality gates. External components require separate plans and retain their own uninstall instructions.

## What to say: handle an Intel-only application on Apple Silicon

Copy and paste:

```text
Use $ai-game-studio-macos:setup-macos-edition to evaluate this Intel-only macOS application on Apple Silicon. Look first for a verified universal or arm64 build, then compare native alternatives. Offer Rosetta only if no native route satisfies the requirement. Disclose publisher verification, signature/notarization evidence, performance, extension and driver limits, system permissions, uninstall implications, and rollback. Do not install or invoke Rosetta until I confirm a separate plan.
```

Codex asks which application feature is essential and whether a native substitute is acceptable. Rosetta is never presented as native or automatically installed. Expected artifacts are a publisher/source record, architecture evidence, capability comparison, risk disclosure, test plan, and a separate transaction if you choose the fallback.

## What to say: choose an engine and DCC route

Copy and replace the bracketed values:

```text
Use $ai-game-studio-macos:setup-macos-edition for my [Unity/Godot/Unreal] project with [Blender/Aseprite/Pixelorama/Tiled]. Inspect the existing versions and plugins without launching them. Propose the matching native editor and DCC packs, allow only one MCP server per host application, include exact pins and health checks, and keep generated assets separate until format, visual, runtime, rights, and human-review gates pass. Wait for confirmation before setup or editor control.
```

Codex asks which application versions and source assets are authoritative. Edition selection changes no editor. Confirmed later pack transactions may add scoped configuration or invoke a user-approved local adapter; their plans must list exact actions, application permissions, backups, and rollback. Expected artifacts include version evidence, selected pack descriptors, import checks, screenshots or artifact regressions, and preserved originals.

## Native adaptation rules

| Source constraint | Preferred route | Important limit |
|---|---|---|
| Windows EXE, DLL, MSI, or Win32 dependency | Verified source build for macOS, when the source and APIs support it | A rebuild is a new tested implementation, not binary compatibility |
| Windows PowerShell with registry, COM, or Win32 dependencies | Python standard library, tokenized POSIX commands, or an application-native API | PowerShell 7 does not make Windows APIs portable |
| CUDA-only pipeline | Verified Metal or MPS implementation with the same rights and quality gates | Operations, numerics, memory, and performance may differ |
| DirectML-only pipeline | Verified Core ML, Metal, or MPS route | Model conversion can change supported layers and output |
| Windows desktop automation | Application CLI/plugin/API/MCP; scoped Accessibility automation only after approval | macOS permissions are high trust and version-sensitive |
| Intel-only macOS app on Apple Silicon | Signed universal/arm64 build; Rosetta only as disclosed fallback | Rosetta may not support drivers or architecture-specific plugins |

When no verified equivalent exists, Codex must say so and keep the step hosted or manual. Hosted fallbacks require data-transfer, retention, privacy, rights, cost, and reproducibility review.

## Disable and rollback

Create a disable proposal without applying it:

```text
"<macos-plugin-root>/scripts/ai-game-studio-macos.sh" disable --project <root> --output <disable-plan.json>
```

Create a rollback proposal for a completed transaction:

```text
"<macos-plugin-root>/scripts/ai-game-studio-macos.sh" rollback <transaction_id> --project <root> --output <rollback-plan.json>
```

Review the new proposal and apply it with its own exact digest. Rollback restores `.ai-game-studio/project.json` and `.ai-game-studio/lock.json`. It does not remove Homebrew, MacPorts, Rosetta, applications, MCP servers, models, or other tools installed through separately approved transactions; roll those back with their own recorded plans.
