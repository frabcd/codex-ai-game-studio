## Outcome

Describe the user-visible result and the exact surfaces changed.

## Evidence

- [ ] `python tools/validate_repository.py`
- [ ] `python tools/run_official_validators.py --require` (when plugins or skills changed)
- [ ] `python -m unittest discover -s tests -p "test_*.py" -v`
- [ ] Windows, macOS, and Linux impact considered
- [ ] Before/after screenshots or artifact evidence attached when visual output changed

## Contributor certification and provenance

- [ ] Every non-bot commit has my DCO 1.1 `Signed-off-by` line
- [ ] I have the right to submit this contribution under the license that applies to the changed files
- [ ] I personally reviewed any AI-assisted output and accept responsibility for its correctness, licensing, and safety
- [ ] Third-party sources, immutable refs, licenses, destinations, and transformations are listed below or are not applicable
- [ ] `NOTICE.md`, `UPSTREAM.json`, or the applicable provenance ledger was updated when required

Origin: original / adapted / AI-assisted / mixed

Tools used:

Third-party sources and immutable refs:

License and commercial-use findings:

## Safety and provenance

- [ ] Detection remains read-only and every mutation begins with a plan
- [ ] Apply requires the user-confirmed digest; rollback was tested when transaction behavior changed
- [ ] No credentials or secret values are present
- [ ] Executable dependencies and GitHub Actions use immutable pins
- [ ] Code, model-weight, dataset, output, and commercial-use rights are recorded separately
- [ ] Source assets are preserved until human approval
- [ ] Derived Claude Code Game Studios files retain pinned-source attribution and parity-ledger coverage

## Catalog changes

- [ ] Not applicable, or stable curation is separate from volatile metadata
- [ ] Unknown/custom licensing blocks commercial recommendations
- [ ] No catalog repository, model, engine, or application is vendored or auto-launched
