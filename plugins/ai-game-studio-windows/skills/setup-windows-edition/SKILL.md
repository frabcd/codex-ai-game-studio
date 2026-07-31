---
name: setup-windows-edition
description: Inspect a native Windows game-development environment and propose one compatible Codex AI Game Studio edition with architecture, shell, package-manager, editor, GPU, MCP, permission, license, and rollback details. Use explicitly for Windows edition setup or for adapting a macOS-, POSIX-, Apple-Silicon-, or Metal-bound workflow; never install, download, activate, substitute, or configure anything before exact digest confirmation.
---

# Set up the Windows edition

Keep discovery read-only and prefer native Windows execution. Do not launch an editor, trust a hook, install a package, download a model, enable an MCP server, write project configuration, or cross the WSL boundary during discovery.

1. Resolve `PLUGIN_ROOT` to this plugin's installed root, resolve the project
   root, preserve its current Git state, and run the native launcher:

   ```text
   & "${PLUGIN_ROOT}\scripts\ai-game-studio-windows.ps1" doctor --project <root>
   ```

   Verify native Windows versus WSL, `amd64` versus `arm64`, PowerShell availability, `winget`/Chocolatey/Scoop presence, installed engines and DCC tools, active MCP host selections, GPU vendor, CUDA/DirectML/CPU/WARP options, disk space, network needs, and credential variable names without reading secret values.

2. Read the bundled descriptor at `${PLUGIN_ROOT}/editions/windows.json`. Reject the Windows edition if the target is not native Windows. Treat WSL as a disclosed fallback only; do not use it for GUI editor control, project files on a cross-boundary filesystem, or a capability that has a verified native route.

3. Select one route in this order:

   - Adapt portable source and launchers to native PowerShell or standard-library Python when the upstream license, architecture, and tests support it.
   - Select a verified capability-equivalent Windows alternative and compare capability, output quality, cost, performance, privacy, license, and limitations.
   - Offer a hosted or manual handoff only when neither native route works.

   Never describe a macOS application bundle, POSIX executable, Apple-Silicon binary, or Metal implementation as Windows-compatible. Every substitution requires confirmation.

4. Create the proposal:

   ```text
   & "${PLUGIN_ROOT}\scripts\ai-game-studio-windows.ps1" plan --project <root> --output <plan.json>
   ```

   Use a user-approved temporary plan path outside the project for preview-only work. Present the detected environment, exact actions, immutable pins, downloads, licenses, permissions, conflicts, expected artifacts, backups, rollback operations, expiry, and SHA-256 digest. State which checks are evidence and which capabilities remain unverified.

5. Stop and wait for the user to repeat the displayed digest verbatim. Do not interpret general approval as digest confirmation. Apply only the unexpired, unchanged proposal:

   ```text
   & "${PLUGIN_ROOT}\scripts\ai-game-studio-windows.ps1" apply --project <root> --plan <plan.json> --confirmed-digest <digest>
   ```

6. Run the descriptor health checks after apply. Confirm exact executable paths and hashes, one active MCP server per host application, editor/version compatibility, GPU backend availability, project parse/import status, and transaction-owned files. Do not launch editors or generated content unless those actions were in the confirmed proposal.

7. Report the transaction ID, evidence paths, limitations, and rollback route. Generate disable or rollback as a new proposal and require a new digest:

   ```text
   & "${PLUGIN_ROOT}\scripts\ai-game-studio-windows.ps1" disable --project <root> --output <disable-plan.json>
   & "${PLUGIN_ROOT}\scripts\ai-game-studio-windows.ps1" rollback <transaction-id> --project <root> --output <rollback-plan.json>
   ```

For a preview request, stop after presenting the plan. Do not write `.ai-game-studio/project.json`, `.ai-game-studio/lock.json`, editor configuration, MCP configuration, or package state.
