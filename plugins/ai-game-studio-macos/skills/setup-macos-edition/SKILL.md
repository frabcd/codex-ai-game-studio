---
name: setup-macos-edition
description: Inspect a macOS game project and propose one native Apple Silicon or Intel Codex AI Game Studio setup, including deterministic alternatives for Windows, PowerShell, CUDA, or DirectML-only tooling. Use explicitly for macOS edition selection or cross-platform adaptation; never install, activate, download, or change configuration before full-digest confirmation.
---

# Set up the macOS edition

Use the core standard-library Python CLI and the installed plugin's validated
`macos` edition descriptor. Treat detection, planning, applying, disabling, and
rollback as separate phases.

## Detect without changing the host

Resolve `PLUGIN_ROOT` to this plugin's installed root, then run its native launcher:

```text
"${PLUGIN_ROOT}/scripts/ai-game-studio-macos.sh" doctor --project <root>
```

Confirm that the host reports Darwin and either `arm64` or `x86_64`. Inspect only OS and architecture metadata, zsh/POSIX availability, Homebrew or MacPorts presence, Metal/MPS/Core ML/CPU capability, free disk space, project markers, existing MCP configuration, and installed Unity, Godot, Unreal, Blender, Aseprite, Pixelorama, or Tiled applications. Check credential environment-variable names only; never read secret values. Detection must report `mutation_performed: false`.

Stop if the host is not Darwin or its architecture is unsupported. Do not apply the macOS edition from Windows, Linux, or WSL.

## Produce one exact proposal

Run:

```text
"${PLUGIN_ROOT}/scripts/ai-game-studio-macos.sh" plan --project <root> --output <plan.json>
```

Present the complete transaction: detected environment, exact state-file actions, MIT license, permissions, backups, rollback operations, expiry, and canonical digest. Explain that edition selection installs no editor, package manager, MCP server, model, or Rosetta component. Wait for the user to repeat the full digest verbatim.

Any external tool, editor, runtime, model, hosted service, or MCP setup needs its own later proposal with exact source pin, license, download size, permissions, privacy implications, health checks, and rollback. Never combine that proposal with edition selection.

## Adapt platform-bound tooling

Apply the descriptor's rules in this order:

1. Prefer a native source adaptation only when the source, license, build system, architecture, and required application APIs support it. Preserve tokenized arguments, bounded paths, output formats, and equivalent quality gates.
2. Otherwise compare verified capability-equivalent native alternatives by capability, quality, cost, performance, license, privacy, and limitations.
3. Otherwise propose a hosted or manual fallback and disclose network transfer, data retention, rights, cost, and reproducibility limits.

Require confirmation before every substitution. Never label an `.exe`, DLL, Win32/COM module, Windows-only PowerShell module, CUDA implementation, or DirectML implementation as macOS-compatible. A behavioral port is a new implementation that must be tested; it is not binary compatibility.

For CUDA or DirectML constraints, prefer a verified Metal, MPS, or Core ML implementation of the same operation and model format. Use CPU only when expected time and memory are acceptable. If no equivalent exists, propose a hosted or manual route rather than silently changing output semantics.

For Windows PowerShell logic, port portable behavior to Python 3 standard library or POSIX tooling. Do not port registry, COM, Win32, drive-letter, or Windows credential-store behavior by textual shell substitution; use a documented macOS API or an application-native CLI/API, or keep the step manual.

Use Rosetta only as a clearly disclosed fallback for a verified x86_64 macOS application when no native or universal build satisfies the requirement. State the source, signature/notarization evidence, performance and security limits, and uninstall implications. Installing or invoking Rosetta requires a separate confirmation.

## Apply and verify

After exact digest confirmation, run:

```text
"${PLUGIN_ROOT}/scripts/ai-game-studio-macos.sh" apply --project <root> --plan <plan.json> --confirmed-digest <digest>
```

Verify `.ai-game-studio/project.json` and `.ai-game-studio/lock.json`, then rerun the native launcher with `doctor --project <root>`. Report the selected edition, descriptor digest, architecture match, and that no external installation occurred. Continue to the relevant Unity, Godot, Unreal, Blender, or pixel pack only when the user requests it and confirms its separate plan.

## Disable or roll back

Disabling is also planned first:

```text
"${PLUGIN_ROOT}/scripts/ai-game-studio-macos.sh" disable --project <root> --output <disable-plan.json>
```

For a completed transaction, create a rollback proposal:

```text
"${PLUGIN_ROOT}/scripts/ai-game-studio-macos.sh" rollback <transaction_id> --project <root> --output <rollback-plan.json>
```

Review either plan and apply it only with that plan's confirmed digest. Edition rollback restores project state; it does not silently uninstall separately approved external tools.
