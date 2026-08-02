# Contributor verification

Codex AI Game Studio verifies **contributions**, not private identities. Anyone
who follows the Code of Conduct may propose a change. Account age, follower
count, location, employer, and popularity are not acceptance criteria, and the
project never asks contributors for government ID, credentials, private prompts,
or secret values.

## The verification path

| Stage | What is checked | Result |
|---|---|---|
| Before CI | A maintainer inspects every external fork change before allowing workflows to run | Untrusted code never runs automatically merely because an account contributed before |
| Certification | Every non-bot commit carries a DCO 1.1 `Signed-off-by` line | The contributor certifies the right to submit the work under the applicable license |
| Automated checks | Read-only CI validates repository contracts, pins, links, tests, releases, and common secret or unsafe-command patterns | Objective failures are visible on the pull request |
| Provenance review | Sources, immutable revisions, licenses, AI assistance, model/data/output terms, identity or voice consent, and transformations are reviewed where applicable | Unknown rights block merge rather than being guessed |
| Maintainer review | Scope, correctness, platform claims, safety boundaries, quality evidence, and sensitive paths are reviewed | Only a repository maintainer can merge |

A DCO is a rights declaration, not a background check or a guarantee that code
is safe. Passing it does not replace code review, provenance review, CI, or human
judgment.

## Fork workflow boundary

Pull-request workflows use the ordinary `pull_request` event with read-only
repository permissions. They do not use `pull_request_target` or privileged
`workflow_run` handoffs, expose secrets, persist checkout credentials, or run
fork code on self-hosted machines. Third-party Actions are pinned to full commit
SHAs. GitHub's repository policy requires approval before workflows from any
external fork run.

The repository validator rejects regressions in these controls. CodeQL's narrow
`security-events: write` permission is the only write permission allowed in an
ordinary pull-request workflow.

## DCO sign-off

Read [DCO](../DCO), then add a sign-off using the name and email associated with
your commit:

```text
git commit -s -m "docs: clarify the Godot quickstart"
```

To repair the latest local commit:

```text
git commit --amend --no-edit --signoff
git push --force-with-lease
```

For several commits, use an interactive rebase and amend each one. Do not paste
another person's sign-off. The repository-side DCO policy is ready for the
[DCO GitHub App](https://github.com/apps/dco); until its check is enabled and
made required, the maintainer reviews sign-offs manually.

## AI-assisted and adapted work

AI assistance is allowed, but the submitting human remains responsible for the
result. In the pull request:

- State whether the work is original, adapted, AI-assisted, or a combination.
- Name the tool or model when known; never include private prompts or tokens.
- List every relevant third-party source, canonical URL, immutable revision,
  license, destination, and transformation.
- Record code, model-weight, dataset, generated-output, and commercial-use terms
  separately when those surfaces exist.
- Confirm the result was reviewed and tested by a human.
- Provide consent evidence for identity or voice work without publishing private
  personal data.

Unknown or incompatible rights, unverifiable consent, credential material, or a
request to bypass the inspect/plan/confirm/rollback contract blocks merge.

## Sensitive paths

Changes to workflows, hooks, release tooling, pack descriptors, executable
scripts, security policy, licenses, catalog curation, or provenance ledgers need
explicit maintainer review. A first-time contributor may change them, but the
evidence and review burden is intentionally higher.

Direct write or merge access is never granted automatically. It is considered
only after sustained, constructive contributions and a separate maintainer
decision.

## What contributors can expect

The maintainer aims to acknowledge a pull request within three business days,
even when a full review takes longer. If a contribution does not fit, the reason
should be recorded publicly and respectfully. Security reports and Code of
Conduct reports remain private through their dedicated channels.
