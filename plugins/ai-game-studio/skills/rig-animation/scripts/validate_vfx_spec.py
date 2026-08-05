#!/usr/bin/env python3
"""Read-only validator for procedural Three.js VFX project manifests.

The validator is intentionally standard-library-only and bounded. It never
loads code, resolves external references, accesses the network, or writes files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


MAX_FILE_BYTES = 1_048_576
MAX_DEPTH = 24
MAX_NODES = 20_000
MAX_ERRORS = 256
MAX_STRING_LENGTH = 2_048
MAX_CAPTURE_PIXELS = 33_554_432
MIN_PALETTE_LUMINANCE_DELTA = 0.015

IDENTIFIER_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NODE_NAME_RE = re.compile(r"^[A-Za-z0-9_.:+-]+$")
PARAMETER_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
URI_RE = re.compile(
    r"(?:https?|ftp|file|data|ssh|git|s3|ws|wss|mailto|javascript|blob|ipfs):",
    re.IGNORECASE,
)
PATH_LIKE_RE = re.compile(
    r"(?:^|[\\/])\.\.(?:[\\/]|$)|^(?:[A-Za-z]:[\\/]|\\\\|/)",
)

PALETTE_ROLES = ("core", "body", "edge", "ink", "ash")
GEOMETRY_GENERATORS = (
    "triangle",
    "crescent",
    "flare-ring",
    "ground-disc",
    "star",
    "shard",
    "rubble",
    "puff",
    "flame-shell",
    "flame-tongue",
)
TRANSPORT_MODES = ("straight", "wobbly", "jagged", "split")
SHADER_BLOCKS = (
    "precision",
    "constants",
    "safe-math",
    "hash11",
    "hash22",
    "value-noise-2d",
    "fbm-2d",
    "domain-warp-2d",
    "radial-cracks",
    "shape-sdf",
    "palette-bands",
    "erosion",
    "ink-contour",
    "heat-gradient",
    "uv-polar",
    "billboard",
    "radial-expand",
    "trail-frame",
    "lifetime-deform",
    "slash",
    "flare-ring",
    "ground-disc",
    "starburst",
    "shard",
    "rubble",
    "puff",
    "flame-shell",
    "flame-tongue",
    "tube-energy",
)
TEXTURE_CHANNELS = ("value-noise", "fbm", "domain-warp", "radial-cracks")
EDITOR_PANELS = (
    "viewport",
    "effect-sheet",
    "effect-browser",
    "transport",
    "cue-timeline",
    "inspector",
    "shader-log",
    "metrics",
)
REQUIRED_FORBIDDEN_FEATURES = {
    "particle-engine",
    "postprocessing",
    "remote-assets",
}
PRESETS = {
    "slash-trail",
    "impact-burst",
    "ground-rupture",
    "beam-bolt",
    "fire-burst",
}
GEOMETRY_SHADERS = {
    "triangle": {"starburst", "shard"},
    "crescent": {"slash"},
    "flare-ring": {"flare-ring"},
    "ground-disc": {"ground-disc"},
    "star": {"starburst"},
    "shard": {"shard"},
    "rubble": {"rubble"},
    "puff": {"puff"},
    "flame-shell": {"flame-shell"},
    "flame-tongue": {"flame-tongue"},
    "transport-tube": {"tube-energy"},
}
BLENDS = {"normal", "additive"}
AIM_MODES = {"tip-velocity", "target", "character-forward"}
SCALE_METRICS = {"weapon-length", "rig-height", "bone-distance", "fixed"}
PREVIEW_POLICIES = {"scrub-no-gameplay-fire", "scrub-preview-window"}
AXES = {"+x", "-x", "+y", "-y", "+z", "-z"}
BACKGROUNDS = {"dark", "light", "checker"}
FORBIDDEN_FIELD_NAMES = {
    "code",
    "endpoint",
    "remoteasset",
    "script",
    "shadersource",
    "uri",
    "url",
}


class SpecReadError(ValueError):
    """Raised when a manifest cannot be safely decoded."""


class DuplicateKeyError(ValueError):
    """Raised when JSON object keys are repeated."""


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise SpecReadError(f"non-finite JSON number {value!r} is not allowed")


def _parse_bounded_int(value: str) -> int:
    digits = value.lstrip("-")
    if len(digits) > 32:
        raise SpecReadError("JSON integer exceeds 32 digits")
    try:
        return int(value)
    except ValueError as exc:
        raise SpecReadError("invalid JSON integer") from exc


def _parse_bounded_float(value: str) -> float:
    if len(value) > 64:
        raise SpecReadError("JSON number exceeds 64 characters")
    try:
        number = float(value)
    except ValueError as exc:
        raise SpecReadError("invalid JSON number") from exc
    if not math.isfinite(number):
        raise SpecReadError("non-finite JSON number is not allowed")
    return number


def load_document(path: Path) -> dict[str, Any]:
    """Load one bounded UTF-8 JSON object without mutating the input."""

    try:
        if not path.is_file():
            raise SpecReadError("manifest is not a regular file")
        size = path.stat().st_size
    except OSError as exc:
        raise SpecReadError(f"cannot inspect manifest: {exc}") from exc
    if size > MAX_FILE_BYTES:
        raise SpecReadError(
            f"manifest is {size} bytes; maximum is {MAX_FILE_BYTES} bytes"
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SpecReadError(f"cannot read manifest: {exc}") from exc
    if len(raw) > MAX_FILE_BYTES:
        raise SpecReadError(f"manifest exceeds {MAX_FILE_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise SpecReadError(f"manifest is not valid UTF-8: {exc}") from exc
    try:
        document = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_int=_parse_bounded_int,
            parse_float=_parse_bounded_float,
            parse_constant=_reject_non_finite_constant,
        )
    except (
        json.JSONDecodeError,
        DuplicateKeyError,
        RecursionError,
        SpecReadError,
        ValueError,
    ) as exc:
        raise SpecReadError(f"invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise SpecReadError("manifest root must be an object")
    return document


def canonical_digest(document: dict[str, Any]) -> str:
    """Return a stable SHA-256 for a decoded manifest."""

    canonical = json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def relative_luminance(color: str) -> float:
    """Return WCAG-style relative luminance for a six-digit sRGB color."""

    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]

    def linear(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        if len(self.errors) < MAX_ERRORS:
            self.errors.append(f"{path}: {message}")

    def object(
        self,
        value: Any,
        path: str,
        required: set[str],
        allowed: set[str],
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return {}
        for key in sorted(required - set(value)):
            self.error(path, f"missing required field {key!r}")
        for key in sorted(set(value) - allowed):
            self.error(path, f"unknown field {key!r}")
        return value

    def array(
        self,
        value: Any,
        path: str,
        minimum: int,
        maximum: int,
    ) -> list[Any]:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        if not minimum <= len(value) <= maximum:
            self.error(path, f"must contain between {minimum} and {maximum} items")
        return value

    def string(
        self,
        value: Any,
        path: str,
        minimum: int = 1,
        maximum: int = 128,
    ) -> str | None:
        if not isinstance(value, str):
            self.error(path, "must be a string")
            return None
        if not minimum <= len(value) <= maximum:
            self.error(path, f"length must be between {minimum} and {maximum}")
            return None
        return value

    def identifier(self, value: Any, path: str) -> str | None:
        text = self.string(value, path, maximum=64)
        if text is not None and not IDENTIFIER_RE.fullmatch(text):
            self.error(path, "must be a lowercase hyphen-case identifier")
            return None
        return text

    def node_name(self, value: Any, path: str) -> str | None:
        text = self.string(value, path, maximum=128)
        if text is not None and not NODE_NAME_RE.fullmatch(text):
            self.error(path, "contains unsupported node-name characters")
            return None
        return text

    def number(
        self,
        value: Any,
        path: str,
        minimum: float,
        maximum: float,
    ) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self.error(path, "must be a number")
            return None
        number = float(value)
        if not math.isfinite(number):
            self.error(path, "must be finite")
            return None
        if not minimum <= number <= maximum:
            self.error(path, f"must be between {minimum} and {maximum}")
            return None
        return number

    def integer(
        self,
        value: Any,
        path: str,
        minimum: int,
        maximum: int,
    ) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int):
            self.error(path, "must be an integer")
            return None
        if not minimum <= value <= maximum:
            self.error(path, f"must be between {minimum} and {maximum}")
            return None
        return value

    def field_number(
        self,
        obj: dict[str, Any],
        key: str,
        path: str,
        minimum: float,
        maximum: float,
    ) -> float | None:
        if key not in obj:
            return None
        return self.number(obj[key], f"{path}.{key}", minimum, maximum)

    def field_integer(
        self,
        obj: dict[str, Any],
        key: str,
        path: str,
        minimum: int,
        maximum: int,
    ) -> int | None:
        if key not in obj:
            return None
        return self.integer(obj[key], f"{path}.{key}", minimum, maximum)

    def exact_array(self, value: Any, path: str, expected: tuple[str, ...]) -> None:
        items = self.array(value, path, len(expected), len(expected))
        if items != list(expected):
            self.error(path, f"must exactly equal {list(expected)}")

    def scan_bounds(self, document: dict[str, Any]) -> None:
        stack: list[tuple[str, Any, int]] = [("$", document, 0)]
        nodes = 0
        while stack:
            path, value, depth = stack.pop()
            nodes += 1
            if nodes > MAX_NODES:
                self.error("$", f"document exceeds {MAX_NODES} values")
                return
            if depth > MAX_DEPTH:
                self.error(path, f"nesting exceeds {MAX_DEPTH} levels")
                continue
            if isinstance(value, dict):
                if len(value) > 256:
                    self.error(path, "object contains more than 256 fields")
                for key, child in value.items():
                    normalized = key.replace("-", "").replace("_", "").lower()
                    if normalized in FORBIDDEN_FIELD_NAMES:
                        self.error(f"{path}.{key}", "executable or external field is forbidden")
                    if len(key) > 128:
                        self.error(path, "object key exceeds 128 characters")
                    stack.append((f"{path}.{key}", child, depth + 1))
            elif isinstance(value, list):
                if len(value) > 512:
                    self.error(path, "array contains more than 512 items")
                for index, child in enumerate(value):
                    stack.append((f"{path}[{index}]", child, depth + 1))
            elif isinstance(value, str):
                if len(value) > MAX_STRING_LENGTH:
                    self.error(path, f"string exceeds {MAX_STRING_LENGTH} characters")
                if URI_RE.search(value):
                    self.error(
                        path,
                        "network, file, data, or executable URI values are forbidden",
                    )
                if PATH_LIKE_RE.search(value):
                    self.error(path, "absolute paths and parent traversal are forbidden")
            elif isinstance(value, float) and not math.isfinite(value):
                self.error(path, "number must be finite")

    def validate_style(self, value: Any) -> None:
        path = "$.style"
        fields = {
            "silhouette",
            "banding",
            "erosion",
            "contour",
            "heat",
            "glow",
            "forbiddenFeatures",
        }
        style = self.object(value, path, fields, fields)
        if "silhouette" in style:
            self.string(style["silhouette"], f"{path}.silhouette", maximum=128)

        banding = self.object(
            style.get("banding"),
            f"{path}.banding",
            {"steps", "softness"},
            {"steps", "softness"},
        )
        self.field_integer(banding, "steps", f"{path}.banding", 2, 8)
        self.field_number(banding, "softness", f"{path}.banding", 0, 0.5)

        erosion = self.object(
            style.get("erosion"),
            f"{path}.erosion",
            {"strength", "scale"},
            {"strength", "scale"},
        )
        self.field_number(erosion, "strength", f"{path}.erosion", 0, 1)
        self.field_number(erosion, "scale", f"{path}.erosion", 0.1, 64)

        contour = self.object(
            style.get("contour"),
            f"{path}.contour",
            {"width"},
            {"width"},
        )
        self.field_number(contour, "width", f"{path}.contour", 0, 0.5)

        heat = self.object(
            style.get("heat"),
            f"{path}.heat",
            {"bias"},
            {"bias"},
        )
        self.field_number(heat, "bias", f"{path}.heat", 0, 1)

        glow = self.object(
            style.get("glow"),
            f"{path}.glow",
            {"layers", "intensity"},
            {"layers", "intensity"},
        )
        self.field_integer(glow, "layers", f"{path}.glow", 1, 4)
        self.field_number(glow, "intensity", f"{path}.glow", 0, 4)

        forbidden = self.array(
            style.get("forbiddenFeatures"),
            f"{path}.forbiddenFeatures",
            3,
            16,
        )
        values: set[str] = set()
        for index, item in enumerate(forbidden):
            name = self.identifier(item, f"{path}.forbiddenFeatures[{index}]")
            if name is not None:
                if name in values:
                    self.error(f"{path}.forbiddenFeatures[{index}]", "duplicate value")
                values.add(name)
        missing = REQUIRED_FORBIDDEN_FEATURES - values
        if missing:
            self.error(
                f"{path}.forbiddenFeatures",
                f"must include {sorted(missing)}",
            )

    def validate_palettes(self, value: Any) -> set[str]:
        path = "$.palettes"
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return set()
        if len(value) != 8:
            self.error(path, "must define exactly eight palettes")
        names: set[str] = set()
        for raw_name, raw_palette in value.items():
            name = self.identifier(raw_name, f"{path} key")
            if name is None:
                continue
            names.add(name)
            palette_path = f"{path}.{name}"
            roles = set(PALETTE_ROLES)
            palette = self.object(raw_palette, palette_path, roles, roles)
            colors: list[str] = []
            for role in PALETTE_ROLES:
                if role not in palette:
                    continue
                color = self.string(palette[role], f"{palette_path}.{role}", 7, 7)
                if color is not None:
                    if not COLOR_RE.fullmatch(color):
                        self.error(f"{palette_path}.{role}", "must be a six-digit hex color")
                    else:
                        colors.append(color.lower())
            if len(colors) == len(PALETTE_ROLES) and len(set(colors)) != len(colors):
                self.error(palette_path, "palette roles must use five distinct colors")
            if len(colors) == len(PALETTE_ROLES):
                luminances = [relative_luminance(color) for color in colors]
                for role_index in range(len(PALETTE_ROLES) - 1):
                    delta = luminances[role_index] - luminances[role_index + 1]
                    if delta < MIN_PALETTE_LUMINANCE_DELTA:
                        first = PALETTE_ROLES[role_index]
                        second = PALETTE_ROLES[role_index + 1]
                        self.error(
                            palette_path,
                            f"relative luminance must descend from {first} to {second} "
                            f"by at least {MIN_PALETTE_LUMINANCE_DELTA}",
                        )
        return names

    def validate_registries(self, value: Any) -> None:
        path = "$.registries"
        fields = {"geometryGenerators", "transportTube", "shaderBlocks"}
        registries = self.object(value, path, fields, fields)
        self.exact_array(
            registries.get("geometryGenerators"),
            f"{path}.geometryGenerators",
            GEOMETRY_GENERATORS,
        )
        self.exact_array(
            registries.get("shaderBlocks"),
            f"{path}.shaderBlocks",
            SHADER_BLOCKS,
        )
        tube_fields = {
            "frameMethod",
            "modes",
            "maxPathSamples",
            "radialSegments",
            "preallocated",
            "dynamicDraw",
        }
        tube = self.object(
            registries.get("transportTube"),
            f"{path}.transportTube",
            tube_fields,
            tube_fields,
        )
        if tube.get("frameMethod") != "double-reflection":
            self.error(
                f"{path}.transportTube.frameMethod",
                "must equal 'double-reflection'",
            )
        self.exact_array(
            tube.get("modes"),
            f"{path}.transportTube.modes",
            TRANSPORT_MODES,
        )
        self.field_integer(tube, "maxPathSamples", f"{path}.transportTube", 4, 256)
        self.field_integer(tube, "radialSegments", f"{path}.transportTube", 3, 32)
        if tube.get("preallocated") is not True:
            self.error(f"{path}.transportTube.preallocated", "must be true")
        if tube.get("dynamicDraw") is not True:
            self.error(f"{path}.transportTube.dynamicDraw", "must be true")

    def validate_rendering(self, value: Any) -> None:
        path = "$.rendering"
        fields = {
            "postprocessing",
            "particleEngine",
            "layeredAdditiveGlow",
            "meshPooling",
            "sparks",
            "debris",
            "additiveDepthWrite",
            "computedTextureChannels",
        }
        rendering = self.object(value, path, fields, fields)
        required_booleans = {
            "postprocessing": False,
            "particleEngine": False,
            "layeredAdditiveGlow": True,
            "meshPooling": True,
            "additiveDepthWrite": False,
        }
        for key, expected in required_booleans.items():
            if rendering.get(key) is not expected:
                self.error(f"{path}.{key}", f"must be {str(expected).lower()}")
        for key in ("sparks", "debris"):
            if rendering.get(key) != "instanced-mesh":
                self.error(f"{path}.{key}", "must equal 'instanced-mesh'")
        self.exact_array(
            rendering.get("computedTextureChannels"),
            f"{path}.computedTextureChannels",
            TEXTURE_CHANNELS,
        )

    def validate_editor(self, value: Any) -> None:
        path = "$.editor"
        fields = {
            "localOnly",
            "panels",
            "history",
            "projectIo",
            "deterministicCapture",
            "accessibility",
            "network",
            "telemetry",
        }
        editor = self.object(value, path, fields, fields)
        if editor.get("localOnly") is not True:
            self.error(f"{path}.localOnly", "must be true")
        self.exact_array(editor.get("panels"), f"{path}.panels", EDITOR_PANELS)

        history = self.object(
            editor.get("history"),
            f"{path}.history",
            {"undo", "redo"},
            {"undo", "redo"},
        )
        for key in ("undo", "redo"):
            if history.get(key) is not True:
                self.error(f"{path}.history.{key}", "must be true")

        project_io = self.object(
            editor.get("projectIo"),
            f"{path}.projectIo",
            {"jsonImport", "jsonExport"},
            {"jsonImport", "jsonExport"},
        )
        for key in ("jsonImport", "jsonExport"):
            if project_io.get(key) is not True:
                self.error(f"{path}.projectIo.{key}", "must be true")

        if editor.get("deterministicCapture") is not True:
            self.error(f"{path}.deterministicCapture", "must be true")
        accessibility = self.object(
            editor.get("accessibility"),
            f"{path}.accessibility",
            {"keyboard", "reducedMotion", "pausable"},
            {"keyboard", "reducedMotion", "pausable"},
        )
        for key in ("keyboard", "reducedMotion", "pausable"):
            if accessibility.get(key) is not True:
                self.error(f"{path}.accessibility.{key}", "must be true")
        if editor.get("network") is not False:
            self.error(f"{path}.network", "must be false")
        if editor.get("telemetry") is not False:
            self.error(f"{path}.telemetry", "must be false")

    def validate_parameters(self, value: Any, path: str) -> None:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return
        if len(value) > 32:
            self.error(path, "must contain at most 32 parameters")
        for key, item in value.items():
            if not PARAMETER_NAME_RE.fullmatch(key):
                self.error(f"{path}.{key}", "invalid parameter name")
            if isinstance(item, bool):
                continue
            self.number(item, f"{path}.{key}", -10000, 10000)

    def validate_global_budgets(self, value: Any) -> dict[str, float | int | None]:
        path = "$.budgets"
        fields = {
            "maxActiveEffects",
            "maxLayersPerEffect",
            "maxVertices",
            "maxDrawCalls",
            "maxTextures",
            "maxShaderPrograms",
            "frameTimeDeltaMs",
        }
        budgets = self.object(value, path, fields, fields)
        return {
            "maxActiveEffects": self.field_integer(budgets, "maxActiveEffects", path, 1, 128),
            "maxLayersPerEffect": self.field_integer(budgets, "maxLayersPerEffect", path, 1, 16),
            "maxVertices": self.field_integer(budgets, "maxVertices", path, 3, 1_000_000),
            "maxDrawCalls": self.field_integer(budgets, "maxDrawCalls", path, 1, 4096),
            "maxTextures": self.field_integer(budgets, "maxTextures", path, 1, 256),
            "maxShaderPrograms": self.field_integer(budgets, "maxShaderPrograms", path, 1, 256),
            "frameTimeDeltaMs": self.field_number(budgets, "frameTimeDeltaMs", path, 0.1, 50),
        }

    def validate_effects(
        self,
        value: Any,
        palettes: set[str],
        global_budgets: dict[str, float | int | None],
    ) -> set[str]:
        path = "$.effects"
        effects = self.array(value, path, 1, 64)
        effect_ids: set[str] = set()
        has_beam_bolt = False
        for index, raw_effect in enumerate(effects):
            effect_path = f"{path}[{index}]"
            fields = {
                "id",
                "preset",
                "duration",
                "palette",
                "seedOffset",
                "layers",
                "parameters",
                "budgets",
            }
            effect = self.object(raw_effect, effect_path, fields, fields)
            effect_id = self.identifier(effect.get("id"), f"{effect_path}.id")
            if effect_id is not None:
                if effect_id in effect_ids:
                    self.error(f"{effect_path}.id", "duplicate effect id")
                effect_ids.add(effect_id)
            preset = effect.get("preset")
            if preset not in PRESETS:
                self.error(f"{effect_path}.preset", f"must be one of {sorted(PRESETS)}")
            elif preset == "beam-bolt":
                has_beam_bolt = True
            self.field_number(effect, "duration", effect_path, 0.01, 10)
            palette = self.identifier(effect.get("palette"), f"{effect_path}.palette")
            if palette is not None and palette not in palettes:
                self.error(f"{effect_path}.palette", "references an unknown palette")
            self.field_integer(effect, "seedOffset", effect_path, 0, 4_294_967_295)
            self.validate_parameters(effect.get("parameters"), f"{effect_path}.parameters")

            layers = self.array(effect.get("layers"), f"{effect_path}.layers", 1, 16)
            layer_limit = global_budgets.get("maxLayersPerEffect")
            if isinstance(layer_limit, int) and len(layers) > layer_limit:
                self.error(
                    f"{effect_path}.layers",
                    f"contains {len(layers)} layers; global limit is {layer_limit}",
                )
            layer_ids: set[str] = set()
            has_additive = False
            for layer_index, raw_layer in enumerate(layers):
                layer_path = f"{effect_path}.layers[{layer_index}]"
                layer_fields = {"id", "geometry", "shader", "blend", "parameters"}
                layer = self.object(raw_layer, layer_path, layer_fields, layer_fields)
                layer_id = self.identifier(layer.get("id"), f"{layer_path}.id")
                if layer_id is not None:
                    if layer_id in layer_ids:
                        self.error(f"{layer_path}.id", "duplicate layer id in effect")
                    layer_ids.add(layer_id)
                geometry = layer.get("geometry")
                shader = layer.get("shader")
                if geometry not in GEOMETRY_SHADERS:
                    self.error(
                        f"{layer_path}.geometry",
                        f"must be one of {sorted(GEOMETRY_SHADERS)}",
                    )
                elif shader not in GEOMETRY_SHADERS[geometry]:
                    self.error(
                        f"{layer_path}.shader",
                        f"shader {shader!r} is incompatible with geometry {geometry!r}",
                    )
                blend = layer.get("blend")
                if blend not in BLENDS:
                    self.error(f"{layer_path}.blend", f"must be one of {sorted(BLENDS)}")
                elif blend == "additive":
                    has_additive = True
                self.validate_parameters(layer.get("parameters"), f"{layer_path}.parameters")
            if layers and not has_additive:
                self.error(f"{effect_path}.layers", "must include an additive geometry layer")

            budget_fields = {"maxVertices", "maxDrawCalls"}
            budgets = self.object(
                effect.get("budgets"),
                f"{effect_path}.budgets",
                budget_fields,
                budget_fields,
            )
            max_vertices = self.field_integer(
                budgets, "maxVertices", f"{effect_path}.budgets", 3, 1_000_000
            )
            max_draw_calls = self.field_integer(
                budgets, "maxDrawCalls", f"{effect_path}.budgets", 1, 4096
            )
            global_vertices = global_budgets.get("maxVertices")
            if (
                max_vertices is not None
                and isinstance(global_vertices, int)
                and max_vertices > global_vertices
            ):
                self.error(
                    f"{effect_path}.budgets.maxVertices",
                    "exceeds the global maxVertices budget",
                )
            global_draw_calls = global_budgets.get("maxDrawCalls")
            if (
                max_draw_calls is not None
                and isinstance(global_draw_calls, int)
                and max_draw_calls > global_draw_calls
            ):
                self.error(
                    f"{effect_path}.budgets.maxDrawCalls",
                    "exceeds the global maxDrawCalls budget",
                )
        if effects and not has_beam_bolt:
            self.error(path, "must include at least one beam-bolt effect")
        return effect_ids

    def validate_rig(self, value: Any) -> set[str]:
        path = "$.rig"
        fields = {
            "boneMap",
            "weaponBaseSocket",
            "weaponTipSocket",
            "forwardAxis",
            "upAxis",
        }
        rig = self.object(value, path, fields, fields)
        bone_map = rig.get("boneMap")
        if not isinstance(bone_map, dict):
            self.error(f"{path}.boneMap", "must be an object")
        else:
            if not 1 <= len(bone_map) <= 128:
                self.error(f"{path}.boneMap", "must contain between 1 and 128 bones")
            bone_names: set[str] = set()
            for semantic, node in bone_map.items():
                if not PARAMETER_NAME_RE.fullmatch(semantic):
                    self.error(f"{path}.boneMap.{semantic}", "invalid semantic bone key")
                name = self.node_name(node, f"{path}.boneMap.{semantic}")
                if name is not None:
                    if name in bone_names:
                        self.error(f"{path}.boneMap.{semantic}", "bone node is mapped twice")
                    bone_names.add(name)
        base = self.identifier(rig.get("weaponBaseSocket"), f"{path}.weaponBaseSocket")
        tip = self.identifier(rig.get("weaponTipSocket"), f"{path}.weaponTipSocket")
        if base is not None and tip is not None and base == tip:
            self.error(path, "weapon base and tip sockets must differ")
        forward = rig.get("forwardAxis")
        up = rig.get("upAxis")
        if forward not in AXES:
            self.error(f"{path}.forwardAxis", f"must be one of {sorted(AXES)}")
        if up not in AXES:
            self.error(f"{path}.upAxis", f"must be one of {sorted(AXES)}")
        if forward in AXES and up in AXES and forward[-1] == up[-1]:
            self.error(path, "forwardAxis and upAxis must use different dimensions")
        return {socket for socket in (base, tip) if socket is not None}

    def validate_cue_tracks(
        self,
        value: Any,
        effect_ids: set[str],
        sockets: set[str],
    ) -> None:
        path = "$.cueTracks"
        tracks = self.array(value, path, 1, 64)
        clip_names: set[str] = set()
        cue_ids: set[str] = set()
        cue_total = 0
        for track_index, raw_track in enumerate(tracks):
            track_path = f"{path}[{track_index}]"
            fields = {"clip", "sourceFps", "cues"}
            track = self.object(raw_track, track_path, fields, fields)
            clip = self.node_name(track.get("clip"), f"{track_path}.clip")
            if clip is not None:
                if clip in clip_names:
                    self.error(f"{track_path}.clip", "duplicate clip track")
                clip_names.add(clip)
            self.field_integer(track, "sourceFps", track_path, 1, 240)
            cues = self.array(track.get("cues"), f"{track_path}.cues", 1, 64)
            cue_total += len(cues)
            for cue_index, raw_cue in enumerate(cues):
                cue_path = f"{track_path}.cues[{cue_index}]"
                required = {
                    "id",
                    "effectId",
                    "socket",
                    "aimMode",
                    "scaleMetric",
                    "multiplier",
                    "previewPolicy",
                }
                allowed = required | {"normalizedTime", "normalizedWindow"}
                cue = self.object(raw_cue, cue_path, required, allowed)
                cue_id = self.identifier(cue.get("id"), f"{cue_path}.id")
                if cue_id is not None:
                    if cue_id in cue_ids:
                        self.error(f"{cue_path}.id", "duplicate cue id")
                    cue_ids.add(cue_id)
                has_time = "normalizedTime" in cue
                has_window = "normalizedWindow" in cue
                if has_time == has_window:
                    self.error(
                        cue_path,
                        "must define exactly one of normalizedTime or normalizedWindow",
                    )
                if has_time:
                    self.field_number(cue, "normalizedTime", cue_path, 0, 1)
                if has_window:
                    window = self.array(
                        cue.get("normalizedWindow"),
                        f"{cue_path}.normalizedWindow",
                        2,
                        2,
                    )
                    if len(window) == 2:
                        start = self.number(window[0], f"{cue_path}.normalizedWindow[0]", 0, 1)
                        end = self.number(window[1], f"{cue_path}.normalizedWindow[1]", 0, 1)
                        if start is not None and end is not None and start >= end:
                            self.error(
                                f"{cue_path}.normalizedWindow",
                                "start must be less than end",
                            )
                effect_id = self.identifier(cue.get("effectId"), f"{cue_path}.effectId")
                if effect_id is not None and effect_id not in effect_ids:
                    self.error(f"{cue_path}.effectId", "references an unknown effect")
                socket = self.identifier(cue.get("socket"), f"{cue_path}.socket")
                if socket is not None and socket not in sockets:
                    self.error(f"{cue_path}.socket", "references an unknown rig socket")
                if cue.get("aimMode") not in AIM_MODES:
                    self.error(f"{cue_path}.aimMode", f"must be one of {sorted(AIM_MODES)}")
                if cue.get("scaleMetric") not in SCALE_METRICS:
                    self.error(
                        f"{cue_path}.scaleMetric",
                        f"must be one of {sorted(SCALE_METRICS)}",
                    )
                multiplier = self.field_number(cue, "multiplier", cue_path, 0, 100)
                if multiplier == 0:
                    self.error(f"{cue_path}.multiplier", "must be greater than zero")
                if cue.get("previewPolicy") not in PREVIEW_POLICIES:
                    self.error(
                        f"{cue_path}.previewPolicy",
                        f"must be one of {sorted(PREVIEW_POLICIES)}",
                    )
        if cue_total > 512:
            self.error(path, "project contains more than 512 cues")

    def vector3(self, value: Any, path: str) -> tuple[float, float, float] | None:
        items = self.array(value, path, 3, 3)
        if len(items) != 3:
            return None
        values = [self.number(item, f"{path}[{index}]", -10000, 10000) for index, item in enumerate(items)]
        if any(item is None for item in values):
            return None
        return (values[0], values[1], values[2])  # type: ignore[return-value]

    def validate_capture(self, value: Any) -> None:
        path = "$.capture"
        fields = {
            "resolution",
            "devicePixelRatio",
            "camera",
            "backgrounds",
            "sampleTimes",
        }
        capture = self.object(value, path, fields, fields)
        resolution = self.array(capture.get("resolution"), f"{path}.resolution", 2, 2)
        width: int | None = None
        height: int | None = None
        if len(resolution) == 2:
            width = self.integer(resolution[0], f"{path}.resolution[0]", 64, 8192)
            height = self.integer(resolution[1], f"{path}.resolution[1]", 64, 8192)
        dpr = self.field_number(capture, "devicePixelRatio", path, 0.5, 4)
        if width is not None and height is not None and dpr is not None:
            pixels = width * height * dpr * dpr
            if pixels > MAX_CAPTURE_PIXELS:
                self.error(
                    f"{path}.resolution",
                    f"effective capture exceeds {MAX_CAPTURE_PIXELS} pixels",
                )

        camera = self.object(
            capture.get("camera"),
            f"{path}.camera",
            {"position", "target"},
            {"position", "target"},
        )
        position = self.vector3(camera.get("position"), f"{path}.camera.position")
        target = self.vector3(camera.get("target"), f"{path}.camera.target")
        if position is not None and target is not None and position == target:
            self.error(f"{path}.camera", "camera position and target must differ")

        backgrounds = self.array(capture.get("backgrounds"), f"{path}.backgrounds", 3, 3)
        seen_backgrounds: set[str] = set()
        for index, background in enumerate(backgrounds):
            if background not in BACKGROUNDS:
                self.error(
                    f"{path}.backgrounds[{index}]",
                    f"must be one of {sorted(BACKGROUNDS)}",
                )
            elif background in seen_backgrounds:
                self.error(f"{path}.backgrounds[{index}]", "duplicate background")
            else:
                seen_backgrounds.add(background)
        missing_backgrounds = BACKGROUNDS - seen_backgrounds
        if missing_backgrounds:
            self.error(
                f"{path}.backgrounds",
                f"must include {sorted(missing_backgrounds)}",
            )

        sample_times = self.array(capture.get("sampleTimes"), f"{path}.sampleTimes", 1, 32)
        parsed_times: list[float] = []
        for index, sample in enumerate(sample_times):
            parsed = self.number(sample, f"{path}.sampleTimes[{index}]", 0, 1)
            if parsed is not None:
                parsed_times.append(parsed)
        if parsed_times != sorted(set(parsed_times)):
            self.error(f"{path}.sampleTimes", "must be unique and sorted ascending")

    def validate(self, document: dict[str, Any]) -> list[str]:
        self.scan_bounds(document)
        top_fields = {
            "schemaVersion",
            "threeRevision",
            "unitsPerMeter",
            "seed",
            "style",
            "registries",
            "rendering",
            "palettes",
            "effects",
            "cueTracks",
            "rig",
            "budgets",
            "editor",
            "capture",
        }
        root = self.object(document, "$", top_fields, top_fields)
        if root.get("schemaVersion") != "1.0.0":
            self.error("$.schemaVersion", "must equal '1.0.0'")
        revision = self.string(root.get("threeRevision"), "$.threeRevision", maximum=64)
        if revision is not None and not re.fullmatch(
            r"(?:r[0-9]{2,4}|[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)",
            revision,
        ):
            self.error(
                "$.threeRevision",
                "must be a concrete rNNN or semantic-version-style revision",
            )
        self.field_number(root, "unitsPerMeter", "$", 0.001, 10000)
        self.field_integer(root, "seed", "$", 0, 4_294_967_295)
        self.validate_style(root.get("style"))
        self.validate_registries(root.get("registries"))
        self.validate_rendering(root.get("rendering"))
        palettes = self.validate_palettes(root.get("palettes"))
        budgets = self.validate_global_budgets(root.get("budgets"))
        effects = self.validate_effects(root.get("effects"), palettes, budgets)
        sockets = self.validate_rig(root.get("rig"))
        self.validate_cue_tracks(root.get("cueTracks"), effects, sockets)
        self.validate_editor(root.get("editor"))
        self.validate_capture(root.get("capture"))
        if len(self.errors) == MAX_ERRORS:
            self.errors.append("$: additional diagnostics suppressed")
        return self.errors


def validate_document(document: dict[str, Any]) -> list[str]:
    """Validate a decoded document and return stable, human-readable errors."""

    return Validator().validate(document)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a bounded, offline procedural VFX project manifest."
    )
    parser.add_argument("manifest", type=Path, help="UTF-8 vfx-project.json file")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="emit one JSON result to standard output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    document: dict[str, Any] | None = None
    try:
        document = load_document(arguments.manifest)
        errors = validate_document(document)
    except SpecReadError as exc:
        errors = [f"$: {exc}"]
    digest = canonical_digest(document) if document is not None else None
    if arguments.json_output:
        payload = {
            "valid": not errors,
            "digest": digest,
            "errors": errors,
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR {error}")
    else:
        print(f"PASS sha256:{digest}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
