# Contributing

Thanks for helping make AI-assisted game development safer and more reproducible. Contributions are welcome as issues, Discussions, documentation, catalog records, recipes, tests, or code.

## Can I contribute?

Yes. The project verifies the proposed change rather than using account age,
followers, employer, or private identity as a trust score. External contributors
work through forks and pull requests; only a maintainer can merge. Read the
[contributor verification policy](docs/CONTRIBUTOR_VERIFICATION.md) for the exact
automated, provenance, and human-review gates.

## First contribution in 10 minutes

1. Choose an open [`good first issue`](https://github.com/frabcd/codex-ai-game-studio/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22) or a [`help wanted`](https://github.com/frabcd/codex-ai-game-studio/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22help%20wanted%22) task. Comment before starting so two people do not duplicate work.
2. Fork the repository, clone your fork, and create a focused branch from `main`.
3. Make the smallest complete change that satisfies the issue's acceptance checks.
4. Run `python tools/validate_repository.py` and the focused test named in the issue. The full standard-library suite usually completes without installing project dependencies.
5. Commit with a DCO sign-off: `git commit -s -m "docs: describe the change"`.
6. Open a pull request, complete the provenance section, and link the issue with `Closes #NUMBER`.

Python 3.11 or newer and Git are sufficient for repository validation. Plugin or
skill changes additionally need the pinned official validators used by CI.
Large integrations or security-sensitive changes should start with the
[contribution proposal form](https://github.com/frabcd/codex-ai-game-studio/issues/new?template=contribution.yml).

## Certification, licensing, and AI assistance

Every non-bot commit must certify the [Developer Certificate of Origin 1.1](DCO)
with a `Signed-off-by` line:

```text
git commit -s -m "catalog: verify an engine adapter"
```

To repair the latest local commit, run `git commit --amend --no-edit --signoff`
and then `git push --force-with-lease`. A sign-off certifies the right to submit;
it does not transfer your copyright. Contributions remain under the license that
applies to their destination: MIT for original project surfaces, Apache-2.0 for
the retained img2threejs snapshot, or another license explicitly identified in
the file.

AI-assisted work is welcome when the contributor reviews it personally and
accepts responsibility for the result. Disclose the tool or model when known and
list relevant source material, licenses, immutable revisions, and transformations.
Never submit private prompts, secret values, proprietary project content, or
identity/voice material without the required rights and consent.

## Before opening a pull request

1. Search existing issues and Discussions.
2. Keep the core plugin portable and free of required hosted MCP services.
3. Do not vendor external repositories, model weights, engines, DCC applications, or datasets.
4. Pin executable dependencies to a release, tag, commit, and integrity value where the upstream supports it.
5. Preserve the inspect → plan → digest confirmation → apply → verify → rollback contract.
6. Add tests proportional to the risk and run the full validation command.

```text
python plugins/ai-game-studio/scripts/ai_game_studio.py validate plugin
python plugins/ai-game-studio/scripts/ai_game_studio.py validate skills
python plugins/ai-game-studio/scripts/ai_game_studio.py validate catalog
python plugins/ai-game-studio/scripts/ai_game_studio.py validate parity
python plugins/ai-game-studio/scripts/ai_game_studio.py validate platform
python -m unittest discover -s tests -v
```

## Catalog contributions

A catalog pull request must include:

- Canonical `owner/repository` identity and documentation URLs.
- A stable summary, kind, capabilities, engines, workflows, and maturity.
- Verified or explicitly claimed OS/architecture support.
- Runtime, host-application, GPU backend, VRAM, disk, and network requirements.
- Authentication environment-variable **names only**.
- Separate findings for code, weights, datasets, outputs, and commercial use.
- Filesystem, network, process, editor, and credential permissions.
- A pin and verification date; never use an unbounded executable `latest` dependency.

Unknown/custom commercial terms must remain blocked. Do not infer permissive rights from an absent license. See [the full catalog guide](docs/CATALOG_CONTRIBUTING.md).

## Skills and recipes

- `SKILL.md` YAML frontmatter must contain only `name` and `description`.
- Every skill needs `agents/openai.yaml` with realistic metadata and a starter prompt that names the skill.
- Setup, installation, engine-control, refresh, and destructive workflows must disable implicit invocation.
- Keep `SKILL.md` focused; move long examples and references into adjacent files.
- Every production recipe must end with rights/provenance, technical, visual/temporal, performance, playability, regression-evidence, and human-approval gates.

## Hooks and automation

Hook commands must work on native Windows and POSIX systems, use `PLUGIN_ROOT` and `PLUGIN_DATA`, accept the official JSON event on standard input, return bounded JSON, and never log secret values. Plugin hooks remain untrusted until reviewed through `/hooks`.

All mutations need a deterministic plan, backup, explicit confirmed digest, and tested rollback. Tests may mock editors and MCP servers; they must never install external software on a contributor's machine.

## Attribution

If you adapt third-party material, add its source, license, pinned revision, destination, and transformation to `NOTICE.md` or the relevant ledger. Do not copy code or documentation with incompatible or unknown terms.

## Pull request checklist

- [ ] The change is scoped and described.
- [ ] Licenses and permissions were reviewed.
- [ ] No credential values or private data are present.
- [ ] Pins and rollback are included for executable dependencies.
- [ ] Windows, macOS, and Linux behavior is truthful.
- [ ] Tests and validators pass.
- [ ] User-facing docs and changelog are updated.
