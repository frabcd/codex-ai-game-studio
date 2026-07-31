#!/usr/bin/env python3
"""Resolve CS2 skin metadata (paint index, float range, rarity, CDN image) from the CSGO-API
skins index -- an optional exactness upgrade over the image-only default. Never guesses: a
no-match or an ambiguous multi-match is an error, not a silent pick. See
grimoire/intake/cs2_texture_acquisition.md and openspec add-cs2-item-reconstruction task 5.2.

The index is the public CSGO-API `skins.json` shape: a list of records like
    {"name": "Karambit | Doppler (Phase 2)", "weapon": {"name": "Karambit"},
     "paint_index": 419, "min_float": 0.0, "max_float": 0.08,
     "rarity": {"name": "Covert"}, "image": "https://.../419.png"}
Load it locally with --index-file (no network) or fetch it with --index-url.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import sys
import urllib.request
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit


MAX_INDEX_BYTES = 64 * 1024 * 1024
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_REDIRECTS = 3
MAX_PAINT_INDEX = 999_999
NETWORK_TIMEOUT_SECONDS = 30

DEFAULT_INDEX_HOSTS = frozenset({
    "cdn.jsdelivr.net",
    "raw.githubusercontent.com",
})
DEFAULT_IMAGE_HOSTS = frozenset({
    "cdn.jsdelivr.net",
    "cdn.steamstatic.com",
    "community.akamai.steamstatic.com",
    "community.cloudflare.steamstatic.com",
    "raw.githubusercontent.com",
    "steamcdn-a.akamaihd.net",
    "steamcommunity-a.akamaihd.net",
})
LOCAL_HOST_NAMES = frozenset({"localhost", "localhost.localdomain", "ip6-localhost"})
LOCAL_HOST_SUFFIXES = (".internal", ".lan", ".local", ".localhost", ".home")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class NetworkPolicyError(ValueError):
    """A URL violates the downloader's explicit network policy."""


def normalize_host(value: str) -> str:
    """Normalize one exact host name; wildcards, URLs, credentials, and ports are rejected."""
    candidate = value.strip().rstrip(".")
    if not candidate or any(character in candidate for character in "/\\@?#"):
        raise NetworkPolicyError(f"invalid confirmed host: {value!r}")
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    try:
        address = ipaddress.ip_address(candidate.split("%", 1)[0])
    except ValueError:
        if ":" in candidate:
            raise NetworkPolicyError(f"confirmed host must not include a port: {value!r}")
        try:
            candidate = candidate.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise NetworkPolicyError(f"invalid confirmed host: {value!r}") from exc
        if (
            len(candidate) > 253
            or "." not in candidate
            or any(
                not label
                or len(label) > 63
                or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
                for label in candidate.split(".")
            )
        ):
            raise NetworkPolicyError(f"invalid confirmed host: {value!r}")
        return candidate
    return address.compressed.lower()


def normalize_confirmed_hosts(values: Iterable[str]) -> frozenset[str]:
    """Return exact public-host overrides that the user explicitly reviewed and confirmed."""
    return frozenset(normalize_host(value) for value in values)


def resolved_addresses(host: str, port: int = 443) -> frozenset[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Resolve all current addresses for a host so private/link-local destinations can be blocked."""
    try:
        rows = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise NetworkPolicyError(f"could not resolve network host {host!r}") from exc
    addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for row in rows:
        raw = str(row[4][0]).split("%", 1)[0]
        try:
            addresses.add(ipaddress.ip_address(raw))
        except ValueError as exc:
            raise NetworkPolicyError(f"host {host!r} resolved to an invalid address") from exc
    if not addresses:
        raise NetworkPolicyError(f"host {host!r} resolved to no addresses")
    return frozenset(addresses)


def ensure_public_host(host: str) -> None:
    """Reject localhost, private, link-local, reserved, multicast, and otherwise non-global hosts."""
    normalized = normalize_host(host)
    if normalized in LOCAL_HOST_NAMES or normalized.endswith(LOCAL_HOST_SUFFIXES):
        raise NetworkPolicyError(f"local network host is not allowed: {normalized}")
    try:
        literal = ipaddress.ip_address(normalized)
    except ValueError:
        addresses = resolved_addresses(normalized)
    else:
        addresses = frozenset({literal})
    blocked = sorted(str(address) for address in addresses if not address.is_global)
    if blocked:
        raise NetworkPolicyError(
            f"host {normalized!r} resolves to a blocked non-public address: {', '.join(blocked)}"
        )


def validate_https_url(
    url: str,
    *,
    allowed_hosts: frozenset[str],
    confirmed_hosts: frozenset[str],
    purpose: str,
) -> str:
    """Validate one request or redirect URL against scheme, host, port, and SSRF policy."""
    if not isinstance(url, str) or not url.strip():
        raise NetworkPolicyError(f"{purpose} URL must be a non-empty string")
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise NetworkPolicyError(f"{purpose} URL must use HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise NetworkPolicyError(f"{purpose} URL must not contain credentials")
    if parsed.hostname is None:
        raise NetworkPolicyError(f"{purpose} URL has no host")
    try:
        port = parsed.port
    except ValueError as exc:
        raise NetworkPolicyError(f"{purpose} URL has an invalid port") from exc
    if port not in (None, 443):
        raise NetworkPolicyError(f"{purpose} URL must use the default HTTPS port")
    host = normalize_host(parsed.hostname)
    if host not in allowed_hosts and host not in confirmed_hosts:
        raise NetworkPolicyError(
            f"{purpose} host {host!r} is not approved; use --confirmed-host only after explicit user review"
        )
    ensure_public_host(host)
    return url


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Apply the same URL policy to every redirect and stop after a small fixed limit."""

    def __init__(
        self,
        *,
        allowed_hosts: frozenset[str],
        confirmed_hosts: frozenset[str],
        purpose: str,
    ) -> None:
        super().__init__()
        self.allowed_hosts = allowed_hosts
        self.confirmed_hosts = confirmed_hosts
        self.purpose = purpose
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise NetworkPolicyError(f"{self.purpose} exceeded {MAX_REDIRECTS} redirects")
        validate_https_url(
            newurl,
            allowed_hosts=self.allowed_hosts,
            confirmed_hosts=self.confirmed_hosts,
            purpose=f"{self.purpose} redirect",
        )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_bounded(response, *, maximum_bytes: int, purpose: str) -> bytes:  # type: ignore[no-untyped-def]
    """Read at most maximum_bytes and reject oversized declared or streamed responses."""
    declared = response.headers.get("Content-Length") if response.headers is not None else None
    if declared is not None:
        try:
            declared_size = int(declared)
        except (TypeError, ValueError) as exc:
            raise NetworkPolicyError(f"{purpose} returned an invalid Content-Length") from exc
        if declared_size < 0 or declared_size > maximum_bytes:
            raise NetworkPolicyError(f"{purpose} exceeds the {maximum_bytes}-byte limit")
    payload = response.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise NetworkPolicyError(f"{purpose} exceeds the {maximum_bytes}-byte limit")
    return payload


def fetch_url_bytes(
    url: str,
    *,
    allowed_hosts: frozenset[str],
    confirmed_hosts: frozenset[str],
    maximum_bytes: int,
    purpose: str,
    accept: str,
) -> bytes:
    """Fetch one bounded public HTTPS resource with validated redirects."""
    validate_https_url(
        url,
        allowed_hosts=allowed_hosts,
        confirmed_hosts=confirmed_hosts,
        purpose=purpose,
    )
    handler = SafeRedirectHandler(
        allowed_hosts=allowed_hosts,
        confirmed_hosts=confirmed_hosts,
        purpose=purpose,
    )
    opener = urllib.request.build_opener(handler)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "Accept-Encoding": "identity",
            "User-Agent": "codex-ai-game-studio-img2threejs/1.1",
        },
    )
    with opener.open(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
        validate_https_url(
            response.geturl(),
            allowed_hosts=allowed_hosts,
            confirmed_hosts=confirmed_hosts,
            purpose=f"{purpose} final response",
        )
        return read_bounded(response, maximum_bytes=maximum_bytes, purpose=purpose)


def parse_paint_index(value: object) -> int:
    """Accept the API's integer or canonical decimal string within a conservative bound."""
    if isinstance(value, bool):
        raise ValueError("paint_index must be an integer")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and re.fullmatch(r"(?:0|[1-9][0-9]{0,5})", value):
        parsed = int(value)
    else:
        raise ValueError("paint_index must be a canonical decimal integer")
    if not 0 <= parsed <= MAX_PAINT_INDEX:
        raise ValueError(f"paint_index must be between 0 and {MAX_PAINT_INDEX}")
    return parsed


def contained_image_target(directory: Path, paint_index: int) -> Path:
    """Derive a fixed numeric filename and prove it remains directly under the approved directory."""
    root = directory.expanduser().resolve()
    target = (root / f"{parse_paint_index(paint_index)}.png").resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("resolved image output escapes the approved directory") from exc
    if target.parent != root:
        raise ValueError("resolved image output must be directly inside the approved directory")
    return target


def load_index(
    index_file: Path | None,
    index_url: str | None,
    confirmed_hosts: frozenset[str] = frozenset(),
) -> list[dict]:
    if index_file is not None:
        path = index_file.expanduser()
        if path.stat().st_size > MAX_INDEX_BYTES:
            raise ValueError(f"local index exceeds the {MAX_INDEX_BYTES}-byte limit")
        data = json.loads(path.read_text(encoding="utf-8"))
    elif index_url is not None:
        payload = fetch_url_bytes(
            index_url,
            allowed_hosts=DEFAULT_INDEX_HOSTS,
            confirmed_hosts=confirmed_hosts,
            maximum_bytes=MAX_INDEX_BYTES,
            purpose="skin index",
            accept="application/json,text/plain;q=0.9",
        )
        data = json.loads(payload.decode("utf-8"))
    else:
        raise ValueError("provide --index-file or --index-url")
    if isinstance(data, dict):  # some CSGO-API mirrors key by id
        data = list(data.values())
    if not isinstance(data, list):
        raise ValueError("index must be a JSON list (or id-keyed object) of skin records")
    return [record for record in data if isinstance(record, dict)]


def _weapon_name(record: dict) -> str:
    weapon = record.get("weapon")
    if isinstance(weapon, dict):
        return str(weapon.get("name") or "")
    return str(weapon or "")


def _rarity_name(record: dict) -> str:
    rarity = record.get("rarity")
    if isinstance(rarity, dict):
        return str(rarity.get("name") or "")
    return str(rarity or "")


def match_records(records: list[dict], weapon: str, skin: str, phase: str | None,
                  paint_index: int | None = None) -> list[dict]:
    weapon_l, skin_l = weapon.lower(), skin.lower()
    phase_l = phase.lower() if phase else None
    matches = []
    for record in records:
        name_l = str(record.get("name") or "").lower()
        if _weapon_name(record).lower() != weapon_l:
            continue
        if skin_l not in name_l:
            continue
        if phase_l is not None and phase_l not in name_l:
            continue
        if paint_index is not None and str(record.get("paint_index")) != str(paint_index):
            continue
        matches.append(record)
    return matches


def to_metadata(record: dict, source: str | None = None) -> dict:
    paint_index = parse_paint_index(record.get("paint_index"))
    image_url = record.get("image")
    if image_url is not None and not isinstance(image_url, str):
        raise ValueError("image URL must be a string when present")
    metadata = {
        "name": record.get("name"),
        "weapon": _weapon_name(record),
        "paintIndex": paint_index,
        "minFloat": record.get("min_float"),
        "maxFloat": record.get("max_float"),
        "floatRange": {"min": record.get("min_float"), "max": record.get("max_float")},
        "rarity": _rarity_name(record),
        "imageUrl": image_url,
    }
    if source:
        metadata["source"] = source
    metadata["provenance"] = {"kind": "metadata-index", "source": source or "unspecified"}
    return metadata


def download_cdn_image(
    image_url: str,
    directory: Path,
    paint_index: int,
    confirmed_hosts: frozenset[str] = frozenset(),
    *,
    overwrite: bool = False,
) -> Path:
    """Download one bounded PNG from the normal CS2 image hosts or a confirmed public host."""
    target = contained_image_target(directory, paint_index)
    if target.exists() and not overwrite:
        raise ValueError(f"skin image already exists: {target}; use --force-image to replace it")
    payload = fetch_url_bytes(
        image_url,
        allowed_hosts=DEFAULT_IMAGE_HOSTS,
        confirmed_hosts=confirmed_hosts,
        maximum_bytes=MAX_IMAGE_BYTES,
        purpose="skin image",
        accept="image/png,image/*;q=0.8",
    )
    if not payload.startswith(PNG_SIGNATURE):
        raise ValueError("skin image response is not a PNG")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weapon", required=True, help="Weapon name, e.g. 'Karambit'")
    parser.add_argument("--skin", required=True, help="Skin/paint kit name substring, e.g. 'Doppler'")
    parser.add_argument("--phase", help="Disambiguating phase substring, e.g. 'Phase 2' or 'Emerald'")
    parser.add_argument("--paint-index", type=parse_paint_index, dest="paint_index",
                        help="Exact paint_index to disambiguate when names collide (e.g. CSGO-API lists "
                             "every Doppler phase as the same name; --paint-index 419 picks Phase 2).")
    parser.add_argument("--index-file", type=Path, help="Local CSGO-API skins JSON")
    parser.add_argument("--index-url", help="Remote CSGO-API skins JSON URL")
    parser.add_argument(
        "--confirmed-host",
        action="append",
        default=[],
        help=(
            "Exact public HTTPS host explicitly reviewed and confirmed by the user; repeat only "
            "when an index or image host is not in the built-in CSGO-API/Steam allowlist"
        ),
    )
    parser.add_argument("--out", type=Path, help="Write the resolved metadata JSON here")
    parser.add_argument("--force", action="store_true", help="Overwrite --out if it exists")
    parser.add_argument("--download-image", type=Path,
                        help="Directory to download the resolved CDN image into (optional)")
    parser.add_argument(
        "--force-image",
        action="store_true",
        help="Replace an existing contained <paint-index>.png download",
    )
    args = parser.parse_args(argv)

    try:
        confirmed_hosts = normalize_confirmed_hosts(args.confirmed_host)
        records = load_index(args.index_file, args.index_url, confirmed_hosts)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: could not load skin index: {exc}", file=sys.stderr)
        return 2

    matches = match_records(records, args.weapon, args.skin, args.phase, args.paint_index)
    if not matches:
        print(f"error: no match for weapon={args.weapon!r} skin={args.skin!r} "
              f"phase={args.phase!r}; refine the query (nothing guessed)", file=sys.stderr)
        return 2
    if len(matches) > 1:
        names = "; ".join(f"{m.get('name')} (paint_index={m.get('paint_index')})" for m in matches)
        print(f"error: ambiguous match ({len(matches)}): {names}. Add --phase or --paint-index to "
              "disambiguate (nothing guessed).", file=sys.stderr)
        return 2

    source = str(args.index_file.expanduser().resolve()) if args.index_file else args.index_url
    try:
        metadata = to_metadata(matches[0], source)
    except ValueError as exc:
        print(f"error: invalid matched skin metadata: {exc}", file=sys.stderr)
        return 2

    if args.download_image and metadata.get("imageUrl"):
        try:
            target = download_cdn_image(
                metadata["imageUrl"],
                args.download_image,
                metadata["paintIndex"],
                confirmed_hosts,
                overwrite=args.force_image,
            )
            metadata["imagePath"] = str(target)
        except (ValueError, OSError) as exc:
            print(f"warning: image download failed ({exc}); metadata still resolved", file=sys.stderr)

    payload = json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        output = args.out.expanduser().resolve()
        if output.exists() and not args.force:
            print(f"error: {output} exists (use --force)", file=sys.stderr)
            return 2
        output.write_text(payload, encoding="utf-8")
        print(f"wrote {output}")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
