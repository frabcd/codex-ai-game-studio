#!/usr/bin/env python3
"""Build deterministic marketplace and plugin release archives plus an SPDX SBOM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
PLUGIN_NAMES = (
    "ai-game-studio",
    "ai-game-studio-automation",
    "ai-game-studio-blender",
    "ai-game-studio-godot",
    "ai-game-studio-img2threejs",
    "ai-game-studio-macos",
    "ai-game-studio-pixel",
    "ai-game-studio-unity",
    "ai-game-studio-unreal",
    "ai-game-studio-windows",
)
SHARED_EDITION_PLUGINS = (
    "ai-game-studio",
    "ai-game-studio-automation",
    "ai-game-studio-blender",
    "ai-game-studio-godot",
    "ai-game-studio-img2threejs",
    "ai-game-studio-pixel",
    "ai-game-studio-unity",
    "ai-game-studio-unreal",
)
EDITION_PLUGINS = {
    "windows": (*SHARED_EDITION_PLUGINS, "ai-game-studio-windows"),
    "macos": (*SHARED_EDITION_PLUGINS, "ai-game-studio-macos"),
}
EXCLUDED_PARTS = {
    ".git",
    ".official",
    ".pytest_cache",
    ".tmp",
    ".venv",
    "__pycache__",
    "_site",
    "htmlcov",
    "venv",
}
EXCLUDED_TOP_LEVEL_PARTS = {"build", "dist"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".coverage", ".DS_Store", "Thumbs.db"}
LF_TEXT_SUFFIXES = {
    ".cff",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".scss",
    ".sh",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
LF_TEXT_NAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CODEOWNERS",
    "LICENSE",
}
CRLF_TEXT_SUFFIXES = {".ps1"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_file_bytes(path: Path) -> bytes:
    """Return checkout-independent bytes for one shipped source file."""

    payload = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix not in LF_TEXT_SUFFIXES | CRLF_TEXT_SUFFIXES and path.name not in LF_TEXT_NAMES:
        return payload
    text = payload.decode("utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if suffix in CRLF_TEXT_SUFFIXES:
        normalized = normalized.replace("\n", "\r\n")
    return normalized.encode("utf-8")


def release_files(root: Path, *, output: Path | None = None) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.parts and relative.parts[0] in EXCLUDED_TOP_LEVEL_PARTS:
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if output is not None and output in (path, *path.parents):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def plugin_files(plugin_root: Path) -> list[Path]:
    return [
        path
        for path in sorted(plugin_root.rglob("*"), key=lambda item: item.relative_to(plugin_root).as_posix())
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(plugin_root).parts)
        and (
            not path.relative_to(plugin_root).parts
            or path.relative_to(plugin_root).parts[0] not in EXCLUDED_TOP_LEVEL_PARTS
        )
        and path.suffix.lower() not in EXCLUDED_SUFFIXES
    ]


def add_file(archive: zipfile.ZipFile, source: Path, archive_name: str) -> None:
    pure = PurePosixPath(archive_name)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"unsafe archive path: {archive_name}")
    info = zipfile.ZipInfo(pure.as_posix(), FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if source.suffix.lower() in {".py", ".ps1", ".sh"} else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.flag_bits |= 0x800
    archive.writestr(
        info,
        canonical_file_bytes(source),
        compress_type=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    )


def add_bytes(
    archive: zipfile.ZipFile,
    content: bytes,
    archive_name: str,
    *,
    executable: bool = False,
) -> None:
    pure = PurePosixPath(archive_name)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"unsafe archive path: {archive_name}")
    info = zipfile.ZipInfo(pure.as_posix(), FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
    info.flag_bits |= 0x800
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_zip(output: Path, files: list[Path], base: Path, prefix: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for path in files:
            relative = path.relative_to(base).as_posix()
            add_file(archive, path, f"{prefix}/{relative}")


def edition_marketplace(root: Path, edition: str) -> bytes:
    source = json.loads(
        (root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    selected = set(EDITION_PLUGINS[edition])
    entries = [
        item
        for item in source.get("plugins", [])
        if isinstance(item, dict) and item.get("name") in selected
    ]
    if {item["name"] for item in entries} != selected:
        missing = sorted(selected - {item["name"] for item in entries})
        raise ValueError(f"{edition} edition marketplace is missing plugins: {missing}")
    payload = {
        "name": f"frabcd-ai-game-studio-{edition}",
        "interface": {
            "displayName": f"frabcd AI Game Studio ({'Windows' if edition == 'windows' else 'macOS'})"
        },
        "plugins": entries,
    }
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def edition_readme(root: Path, edition: str, version: str) -> bytes:
    guide = (root / "docs" / "platforms" / f"{edition}.md").read_text(encoding="utf-8")
    if guide.startswith("---\n"):
        _, _, guide = guide.partition("\n---\n")
    marketplace = f"frabcd-ai-game-studio-{edition}"
    platform_plugin = f"ai-game-studio-{edition}"
    heading = "Windows" if edition == "windows" else "macOS"
    install = f"""# Install the extracted {heading} edition

This archive is a self-contained local Codex marketplace for v{version}. Extract
it, open a terminal in this directory, and run:

```text
codex plugin marketplace add .
codex plugin add ai-game-studio@{marketplace}
codex plugin add {platform_plugin}@{marketplace}
codex plugin add ai-game-studio-img2threejs@{marketplace}
```

The remaining editor, DCC, pixel, and automation plugins are bundled but
optional. Adding this marketplace and these three plugins does not install an
engine, model, MCP server, or external application. Start a new Codex task after
installation.

---

"""
    return (install + guide.lstrip()).encode("utf-8")


def build_edition_zip(root: Path, output: Path, edition: str, version: str) -> None:
    if edition not in EDITION_PLUGINS:
        raise ValueError(f"unknown edition: {edition}")
    prefix = f"codex-ai-game-studio-{edition}-v{version}"
    guide = root / "docs" / "platforms" / f"{edition}.md"
    if not guide.is_file():
        raise FileNotFoundError(f"missing edition guide: {guide}")
    entries: list[tuple[str, Path | bytes]] = [
        (f"{prefix}/README.md", edition_readme(root, edition, version)),
        (
            f"{prefix}/.agents/plugins/marketplace.json",
            edition_marketplace(root, edition),
        ),
    ]
    entries.extend(
        (f"{prefix}/{name}", root / name)
        for name in ("LICENSE", "NOTICE.md", "SECURITY.md", "SUPPORT.md")
    )
    for plugin_name in EDITION_PLUGINS[edition]:
        plugin_root = root / "plugins" / plugin_name
        if not plugin_root.is_dir():
            raise FileNotFoundError(f"missing plugin: {plugin_root}")
        entries.extend(
            (
                f"{prefix}/plugins/{plugin_name}/{path.relative_to(plugin_root).as_posix()}",
                path,
            )
            for path in plugin_files(plugin_root)
        )
    with zipfile.ZipFile(output, "w") as archive:
        for archive_name, source in sorted(entries, key=lambda item: item[0]):
            if isinstance(source, bytes):
                add_bytes(archive, source, archive_name)
            else:
                add_file(archive, source, archive_name)


def spdx_document(root: Path, version: str, files: list[Path]) -> dict[str, object]:
    checksums = [
        {
            "SPDXID": f"SPDXRef-File-{index:04d}",
            "fileName": f"./{path.relative_to(root).as_posix()}",
            "checksums": [
                {
                    "algorithm": "SHA256",
                    "checksumValue": sha256_bytes(canonical_file_bytes(path)),
                }
            ],
            "licenseConcluded": "NOASSERTION",
            "copyrightText": "NOASSERTION",
        }
        for index, path in enumerate(files, start=1)
    ]
    manifest_digest = sha256_bytes(
        "\n".join(
            f"{item['checksums'][0]['checksumValue']}  {item['fileName']}" for item in checksums
        ).encode("utf-8")
    )
    relationships = [
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": "SPDXRef-Package-Root",
        }
    ]
    relationships.extend(
        {
            "spdxElementId": "SPDXRef-Package-Root",
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": item["SPDXID"],
        }
        for item in checksums
    )
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"codex-ai-game-studio-{version}",
        "documentNamespace": f"https://github.com/frabcd/codex-ai-game-studio/sbom/{version}/{manifest_digest}",
        "creationInfo": {
            "created": "1980-01-01T00:00:00Z",
            "creators": ["Tool: tools/build_release.py"],
            "licenseListVersion": "3.25",
        },
        "packages": [
            {
                "name": "codex-ai-game-studio",
                "SPDXID": "SPDXRef-Package-Root",
                "versionInfo": version,
                "downloadLocation": f"https://github.com/frabcd/codex-ai-game-studio/releases/tag/v{version}",
                "filesAnalyzed": True,
                "licenseConcluded": "MIT AND Apache-2.0",
                "licenseDeclared": "MIT AND Apache-2.0",
                "copyrightText": "NOASSERTION",
            }
        ],
        "files": checksums,
        "relationships": relationships,
    }


def build(root: Path, output: Path, version: str) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents and output.name in {".git", "plugins"}:
        raise ValueError("release output must not overwrite repository inputs")
    output.mkdir(parents=True, exist_ok=True)

    full_files = release_files(root, output=output)
    artifacts: list[Path] = []
    full_archive = output / f"codex-ai-game-studio-v{version}.zip"
    build_zip(full_archive, full_files, root, f"codex-ai-game-studio-v{version}")
    artifacts.append(full_archive)

    for plugin_name in PLUGIN_NAMES:
        plugin_root = root / "plugins" / plugin_name
        if not plugin_root.is_dir():
            raise FileNotFoundError(f"missing plugin: {plugin_root}")
        archive_path = output / f"{plugin_name}-v{version}.zip"
        build_zip(archive_path, plugin_files(plugin_root), plugin_root, plugin_name)
        artifacts.append(archive_path)

    for edition in sorted(EDITION_PLUGINS):
        archive_path = output / f"codex-ai-game-studio-{edition}-v{version}.zip"
        build_edition_zip(root, archive_path, edition, version)
        artifacts.append(archive_path)

    sbom_path = output / f"codex-ai-game-studio-v{version}.spdx.json"
    sbom_path.write_text(
        json.dumps(spdx_document(root, version, full_files), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    artifacts.append(sbom_path)

    entries = [
        {"name": path.name, "sha256": sha256_file(path), "size": path.stat().st_size}
        for path in sorted(artifacts, key=lambda item: item.name)
    ]
    manifest = {
        "schema_version": 1,
        "version": version,
        "source_repository": "https://github.com/frabcd/codex-ai-game-studio",
        "reproducible_zip_timestamp": "1980-01-01T00:00:00Z",
        "editions": {
            edition: {
                "artifact": f"codex-ai-game-studio-{edition}-v{version}.zip",
                "plugins": list(EDITION_PLUGINS[edition]),
            }
            for edition in sorted(EDITION_PLUGINS)
        },
        "artifacts": entries,
    }
    manifest_path = output / "release-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    artifacts.append(manifest_path)

    checksum_path = output / "SHA256SUMS"
    checksum_path.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in sorted(artifacts, key=lambda item: item.name)),
        encoding="utf-8",
        newline="\n",
    )
    manifest["checksum_file"] = checksum_path.name
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--version", default="1.1.0")
    args = parser.parse_args()
    if not re_semver(args.version):
        parser.error("--version must be a strict semantic version")
    manifest = build(args.root, args.output, args.version)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def re_semver(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 3 and all(part.isdigit() and (part == "0" or not part.startswith("0")) for part in parts)


if __name__ == "__main__":
    raise SystemExit(main())
