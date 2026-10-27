# Offline repository catalog

`catalog.json` is the stable, curated registry shipped with the core plugin. It
contains exactly 163 GitHub repositories from the verified 2026-07-30 source
snapshot. The landscape section "External references — pricing and licensing"
is not imported. The registry is metadata only: it does not vendor, install,
download, import, launch, or authorize any listed project.

Volatile GitHub signals live under `snapshots/`. Keeping stars, releases,
archive status, and activity out of stable records lets Codex search and
recommend from the checked-in catalog without network access while treating a
refresh as reviewable data rather than an implicit curation change.

Each record separates code, model-weight, dataset, generated-output, and
commercial-use license status. Unknown, custom, restricted, or prohibited
terms set commercial use to `blocked`. A reported SPDX identifier is not legal
clearance: the exact upstream revision, dependencies, weights, services,
references, output terms, consent, and intended use still require review.

The reproducible importer is `tools/generate_catalog.py`. It verifies the
source SHA-256 before writing output and uses only the Python standard library.
The public registry retains a logical source locator rather than a developer's
absolute workstation path.
