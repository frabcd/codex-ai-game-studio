"""Safe cross-platform fallback decoding for the stdlib PNG image loaders.

The img2threejs pixel tools intentionally keep their small, dependency-free PNG
readers.  This module provides one conversion boundary for common non-PNG
inputs without making the installed skill writable or invoking a shell.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias
from urllib.parse import urlsplit

RgbaPixel: TypeAlias = tuple[int, int, int, int]
DecodedImage: TypeAlias = tuple[int, int, list[RgbaPixel]]
PngReader: TypeAlias = Callable[[Path], DecodedImage]

_CONVERTIBLE_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".jfif", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
)
_POWERSHELL_SOURCE_ENV = "AI_GAME_STUDIO_IMAGE_SOURCE"
_POWERSHELL_DESTINATION_ENV = "AI_GAME_STUDIO_IMAGE_DESTINATION"
_IMAGEMAGICK_MANIFEST_ENV = "AI_GAME_STUDIO_IMAGEMAGICK_MANIFEST"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_MANIFEST_BYTES = 64 * 1024
_POWERSHELL_CONVERTER = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$source = [System.IO.Path]::GetFullPath(
    [System.Environment]::GetEnvironmentVariable('AI_GAME_STUDIO_IMAGE_SOURCE')
)
$destination = [System.IO.Path]::GetFullPath(
    [System.Environment]::GetEnvironmentVariable('AI_GAME_STUDIO_IMAGE_DESTINATION')
)
$image = [System.Drawing.Image]::FromFile($source)
try {
    $bitmap = New-Object System.Drawing.Bitmap $image
    try {
        $bitmap.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $bitmap.Dispose()
    }
}
finally {
    $image.Dispose()
}
""".strip()


class ImageDecodeError(ValueError):
    """Raised when neither the PNG reader nor a safe platform converter works."""


def _run(
    command: list[str],
    *,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a fixed argv command without a shell."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        shell=False,
        env=environment,
    )


def _result_error(result: subprocess.CompletedProcess[str], fallback: str) -> str:
    return (result.stderr or result.stdout).strip() or fallback


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _convert_windows(source: Path, destination: Path) -> str:
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    executable = (
        system_root
        / "System32"
        / "WindowsPowerShell"
        / "v1.0"
        / "powershell.exe"
    )
    if not executable.is_file():
        raise ImageDecodeError("Windows PowerShell with System.Drawing is unavailable")
    environment = os.environ.copy()
    environment[_POWERSHELL_SOURCE_ENV] = str(source)
    environment[_POWERSHELL_DESTINATION_ENV] = str(destination)
    result = _run(
        [
            str(executable),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            _POWERSHELL_CONVERTER,
        ],
        environment=environment,
    )
    if result.returncode != 0 or not destination.is_file():
        raise ImageDecodeError(_result_error(result, "Windows System.Drawing conversion failed"))
    return "Windows System.Drawing"


def _convert_macos(source: Path, destination: Path) -> str:
    executable = Path("/usr/bin/sips")
    if not executable.is_file():
        raise ImageDecodeError("macOS sips is unavailable")
    result = _run(
        [str(executable), "-s", "format", "png", str(source), "--out", str(destination)]
    )
    if result.returncode != 0 or not destination.is_file():
        raise ImageDecodeError(_result_error(result, "macOS sips conversion failed"))
    return "macOS sips"


def _configured_imagemagick() -> tuple[Path, dict[str, str]]:
    manifest_value = os.environ.get(_IMAGEMAGICK_MANIFEST_ENV)
    if not manifest_value:
        raise ImageDecodeError(
            "no confirmed ImageMagick manifest is configured in "
            f"{_IMAGEMAGICK_MANIFEST_ENV}"
        )
    manifest_path = Path(manifest_value).expanduser().resolve()
    if not manifest_path.is_file() or manifest_path.stat().st_size > _MAX_MANIFEST_BYTES:
        raise ImageDecodeError("ImageMagick manifest is missing or too large")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ImageDecodeError(f"ImageMagick manifest is invalid: {error}") from error
    if not isinstance(payload, dict):
        raise ImageDecodeError("ImageMagick manifest must be a JSON object")
    required = {
        "executable",
        "sha256",
        "version",
        "license",
        "source_url",
        "confirmed_plan_digest",
    }
    if required - set(payload):
        raise ImageDecodeError("ImageMagick manifest is missing required provenance fields")
    executable = Path(str(payload["executable"])).expanduser()
    expected_hash = str(payload["sha256"]).lower()
    if not executable.is_absolute() or not executable.is_file():
        raise ImageDecodeError("ImageMagick executable must be an existing absolute path")
    executable = executable.resolve()
    if not _SHA256.fullmatch(expected_hash) or _file_sha256(executable) != expected_hash:
        raise ImageDecodeError("ImageMagick executable SHA-256 does not match its manifest")
    source = urlsplit(str(payload["source_url"]))
    if source.scheme != "https" or not source.hostname:
        raise ImageDecodeError("ImageMagick source_url must be HTTPS")
    if str(payload["license"]).strip().lower() in {"", "unknown", "custom", "unreviewed"}:
        raise ImageDecodeError("ImageMagick license must be explicitly reviewed")
    if not str(payload["version"]).strip():
        raise ImageDecodeError("ImageMagick version must not be empty")
    if not _SHA256.fullmatch(str(payload["confirmed_plan_digest"]).lower()):
        raise ImageDecodeError("ImageMagick confirmed_plan_digest must be a full SHA-256")
    return executable, {key: str(payload[key]) for key in required}


def _convert_imagemagick(source: Path, destination: Path) -> str:
    executable, manifest = _configured_imagemagick()
    version = _run([str(executable), "-version"])
    identity = f"{version.stdout}\n{version.stderr}"
    if (
        version.returncode != 0
        or "ImageMagick" not in identity
        or manifest["version"] not in identity
    ):
        raise ImageDecodeError("the discovered 'magick' executable is not verified ImageMagick")
    result = _run([str(executable), str(source), "-auto-orient", str(destination)])
    if result.returncode != 0 or not destination.is_file():
        raise ImageDecodeError(_result_error(result, "ImageMagick conversion failed"))
    return "verified ImageMagick"


def _convert_to_png(source: Path, destination: Path) -> str:
    failures: list[str] = []
    native_converter: Callable[[Path, Path], str] | None = None
    if os.name == "nt" or sys.platform == "win32":
        native_converter = _convert_windows
    elif sys.platform == "darwin":
        native_converter = _convert_macos

    if native_converter is not None:
        try:
            return native_converter(source, destination)
        except (ImageDecodeError, OSError, subprocess.SubprocessError) as error:
            failures.append(str(error))

    try:
        return _convert_imagemagick(source, destination)
    except (ImageDecodeError, OSError, subprocess.SubprocessError) as error:
        failures.append(str(error))

    detail = "; ".join(item for item in failures if item)
    raise ImageDecodeError(
        "no safe platform image converter succeeded"
        + (f": {detail}" if detail else "")
    )


def load_rgba_image(
    path: Path,
    png_reader: PngReader,
) -> tuple[int, int, list[RgbaPixel], list[str]]:
    """Decode *path* with ``png_reader`` or a safe temporary PNG conversion.

    The source is never modified. Conversion output lives in the OS temporary
    directory and is removed before this function returns.
    """
    source = path.expanduser().resolve()
    try:
        width, height, pixels = png_reader(source)
        return width, height, pixels, []
    except Exception as direct_error:
        suffix = source.suffix.lower()
        if suffix not in _CONVERTIBLE_SUFFIXES:
            supported = ", ".join(sorted(_CONVERTIBLE_SUFFIXES))
            raise ImageDecodeError(
                f"unsupported image format {suffix or '<none>'!r} for {source.name}; "
                f"supported inputs are: {supported}"
            ) from direct_error
        with tempfile.TemporaryDirectory(prefix="img2threejs-decode-") as temporary:
            converted = Path(temporary) / "converted.png"
            try:
                backend = _convert_to_png(source, converted)
                width, height, pixels = png_reader(converted)
            except Exception as conversion_error:
                raise ImageDecodeError(
                    f"could not decode {source.name}: built-in PNG decoding failed "
                    f"({direct_error}); conversion failed ({conversion_error})"
                ) from conversion_error
        return (
            width,
            height,
            pixels,
            [f"source image was converted to PNG with {backend} before pixel extraction"],
        )
