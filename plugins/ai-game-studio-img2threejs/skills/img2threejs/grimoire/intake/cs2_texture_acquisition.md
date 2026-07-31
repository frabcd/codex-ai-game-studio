# CS2 Texture Acquisition (optional exactness upgrade)

This is **not** part of the default image-first path. It is an optional Tier-3 upgrade for exact
texture likeness, driven autonomously by the host agent from the **user's own legal CS2 install**.
The user performs no manual step beyond, at most, pointing at the install / VPK path. If nothing is
found the agent falls back to the image-only reconstruction — it never fabricates a wrong render.

**IP boundary (hard rule):** extracted textures are Valve IP. They stay in the local, gitignored
`cs2_textures/` workspace and are **never** committed or redistributed. The MIT repo ships code
only. `.gitignore` excludes `cs2_textures/`; a test asserts nothing under it is
tracked.

## Steps

### 1. Metadata (optional, no install needed) — `forge/stage1_intake/fetch_cs2_metadata.py`

Resolve the skin's paint index, float range, rarity, and CDN image URL from the public CSGO-API
skins index (`--index-file` local, or `--index-url` live). The index is the community-maintained
[`ByMykel/CSGO-API`](https://github.com/ByMykel/CSGO-API) `skins.json` — fetch it straight from
GitHub during a run (metadata only; not Valve's texture files):

```
# live from GitHub through an approved host; replace <commit> with an immutable SHA
fetch_cs2_metadata.py --weapon Karambit --skin Doppler --paint-index 419 \
    --index-url "https://cdn.jsdelivr.net/gh/ByMykel/CSGO-API@<commit>/public/api/en/skins.json" \
    --out metadata.json

# or fully offline from a saved copy
fetch_cs2_metadata.py --weapon Karambit --skin Doppler --phase "Phase 2" \
    --index-file skins.json --out metadata.json
```

A no-match or an ambiguous multi-match is an **error** (nonzero exit), never a silent guess. Add
`--phase` to disambiguate by name — **but** this dataset lists every Doppler phase under the *same*
name (`★ Karambit | Doppler`), differing only by `paint_index`; there, `--phase` can't help and the
ambiguity error lists each candidate's `paint_index` so you can re-run with `--paint-index N`
(e.g. `419` = Phase 2). This gives the precise paint index for a Tier-2 descriptor even without
extracting textures.

Network mode accepts only HTTPS CSGO-API and Steam image hosts, revalidates up
to three redirects, blocks local/private/reserved destinations, caps indexes at
64 MiB and images at 16 MiB, validates bounded numeric paint indexes, and writes
only a contained `<paint-index>.png`. Prefer `--index-file`. Use
`--confirmed-host <exact-public-host>` only after explicit user review; it never
overrides the public-address check.

> Reproducibility & IP: `@main` is a moving target — pin a commit/tag for deterministic runs. The
> metadata and the `image` preview (Steam CDN) are community data; Valve's actual paint textures are
> **not** distributed via this source (use the local VPK path below, and never commit `cs2_textures/`).

### 2. Locate the VPK — `forge/stage1_intake/locate_cs2_vpk.py`

```
locate_cs2_vpk.py --json          # or --root <steam-root> (repeatable) to override
```

Searches the per-OS default Steam roots (override or add more with repeatable `--root`) for
`.../Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk`. Best-effort and non-fatal:
prints `{"found": false, ...}` and exits 1 when nothing is located (never raises). `--root` is
dependency-injectable for offline testing.

### 3. Extract + classify — `forge/stage1_intake/extract_cs2_textures.py`

Never execute a `Source2Viewer-CLI` selected from `PATH`. Treat it as an
external tool requiring a separate confirmed transaction. That transaction
must create a JSON manifest containing its absolute executable path, SHA-256,
version, reviewed license, HTTPS publisher source URL, and confirmed plan
digest. The script rechecks that manifest immediately before execution, uses an
argument array and timeout, then extracts into the approved gitignored
workspace and buckets maps by filename convention (`color` / `normal` /
`roughness_metalness` / `mask` / `other`):

```
extract_cs2_textures.py --out cs2_textures \
  --extractor-manifest <confirmed-extractor.json> --json
```

On any failure — no VPK, missing or hash-mismatched manifest, subprocess error,
timeout, or non-zero exit — it returns
`{"status": "fallback", "reason": ...}` and exits 1, so the pipeline degrades to the image-only
path with an explicit notice that exact texture likeness is unavailable. Use
`--vpk <path>` to skip locating the local VPK. Never adapt flags against an
unpinned executable; create and confirm a new tool plan, update the manifest,
retest the wrapper, and fall back rather than guessing.

## Using the result

Feed the classified maps into the finish material's PBR channels (color → albedo, normal → normal,
packed → roughness/metalness, mask → wear/pattern) to raise fidelity above the procedural
image-only recipe. The finish-style machinery (PBR ranges, environment, wear) in
`grimoire/build/cs2_finishes.md` still applies — it drives *realism* independent of whether exact
textures were acquired.
