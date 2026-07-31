"""Deterministic, standard-library runtime for Codex AI Game Studio.

The module deliberately separates inspection/planning from mutation.  A plan is
canonical JSON protected by SHA-256; apply refuses expired, changed, replayed,
or out-of-project actions.  No installer or MCP process is launched here.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


VERSION = "1.1.0"
STATE_DIR = ".ai-game-studio"
PLAN_TTL_MINUTES = 30
MAX_SCAN_DEPTH = 5
MAX_SCAN_FILES = 20_000
MAX_JSON_BYTES = 16 * 1024 * 1024
SUPPORTED_OS = {"Windows", "Darwin", "Linux"}
KNOWN_CREDENTIALS = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "OPENAI_API_KEY",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "ELEVENLABS_API_KEY",
    "REPLICATE_API_TOKEN",
    "STABILITY_API_KEY",
)
HOST_FILES = {
    "unity": ("ProjectSettings/ProjectVersion.txt",),
    "godot": ("project.godot",),
    "unreal": ("*.uproject",),
    "blender": ("*.blend",),
    "browser": ("package.json", "index.html"),
}


class StudioError(RuntimeError):
    """Expected command-line failure with a concise user-facing message."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_z(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_json_load(path: Path, *, default: Any = None) -> Any:
    if not path.exists():
        return default
    if path.stat().st_size > MAX_JSON_BYTES:
        raise StudioError(f"JSON file is too large: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StudioError(f"Cannot read valid JSON from {path}: {exc}") from exc


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False)
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def resolve_under(root: Path, relative: str) -> Path:
    candidate_text = relative.replace("\\", "/")
    candidate = Path(candidate_text)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise StudioError(f"Unsafe action target: {relative}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise StudioError(f"Action escapes project root: {relative}") from exc
    return resolved


def run_probe(command: Sequence[str], timeout: float = 3.0) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False, "command": command[0]}
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": True, "command": executable, "error": type(exc).__name__}
    combined = (result.stdout or result.stderr).strip().splitlines()
    version = combined[0][:240] if combined else None
    return {"available": True, "command": executable, "version": version, "exit_code": result.returncode}


def iter_project_files(root: Path, *, max_depth: int = MAX_SCAN_DEPTH) -> Iterable[Path]:
    ignored = {".git", "Library", "Temp", "obj", "bin", "node_modules", "Binaries", "Intermediate", ".cache"}
    root = root.resolve()
    seen = 0
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        try:
            depth = len(current_path.relative_to(root).parts)
        except ValueError:
            continue
        dirs[:] = sorted(d for d in dirs if d not in ignored and not d.startswith("."))
        if depth >= max_depth:
            dirs[:] = []
        for name in sorted(files):
            seen += 1
            if seen > MAX_SCAN_FILES:
                return
            yield current_path / name


def detect_projects(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    files = list(iter_project_files(root))
    by_name: dict[str, list[Path]] = {}
    for path in files:
        by_name.setdefault(path.name.lower(), []).append(path)
    for marker in by_name.get("projectversion.txt", []):
        if marker.parent.name == "ProjectSettings":
            version = None
            try:
                match = re.search(r"m_EditorVersion:\s*([^\r\n]+)", marker.read_text(encoding="utf-8", errors="replace"))
                version = match.group(1).strip() if match else None
            except OSError:
                pass
            findings.append({"engine": "unity", "root": str(marker.parent.parent), "version": version})
    for marker in by_name.get("project.godot", []):
        findings.append({"engine": "godot", "root": str(marker.parent), "version": None})
    for path in files:
        if path.suffix.lower() == ".uproject":
            payload = safe_json_load(path, default={})
            version = payload.get("EngineAssociation") if isinstance(payload, dict) else None
            findings.append({"engine": "unreal", "root": str(path.parent), "version": version, "project_file": path.name})
    package = root / "package.json"
    if package.is_file():
        payload = safe_json_load(package, default={})
        deps: dict[str, Any] = {}
        if isinstance(payload, dict):
            deps.update(payload.get("dependencies") or {})
            deps.update(payload.get("devDependencies") or {})
        frameworks = sorted(name for name in ("three", "babylonjs", "@babylonjs/core", "phaser", "pixi.js") if name in deps)
        findings.append({"engine": "browser", "root": str(root), "version": None, "frameworks": frameworks})
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for item in findings:
        unique[(item["engine"], item["root"])] = item
    return sorted(unique.values(), key=lambda item: (item["engine"], item["root"]))


def detect_apps() -> dict[str, Any]:
    probes = {
        "blender": ("blender", "--version"),
        "godot": ("godot", "--version"),
        "godot4": ("godot4", "--version"),
        "aseprite": ("aseprite", "--version"),
        "tiled": ("tiled", "--version"),
    }
    result = {name: run_probe(command, timeout=2.0) for name, command in probes.items()}
    common: dict[str, list[str]] = {}
    if platform.system() == "Windows":
        common = {
            "unity_hub": [r"C:\Program Files\Unity Hub\Unity Hub.exe"],
            "unreal": [r"C:\Program Files\Epic Games"],
            "pixelorama": [str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Pixelorama")],
        }
    elif platform.system() == "Darwin":
        common = {
            "unity_hub": ["/Applications/Unity Hub.app"],
            "unreal": ["/Users/Shared/Epic Games"],
            "pixelorama": ["/Applications/Pixelorama.app"],
        }
    else:
        common = {
            "unity_hub": [str(Path.home() / "Unity" / "Hub")],
            "unreal": [str(Path.home() / "UnrealEngine")],
            "pixelorama": [str(Path.home() / ".local" / "share" / "applications" / "pixelorama.desktop")],
        }
    for name, paths in common.items():
        result[name] = {"available": any(Path(path).exists() for path in paths), "checked_paths": paths}
    if platform.system() == "Windows":
        try:
            import winreg  # type: ignore[import-not-found]

            registry_apps: list[dict[str, str | None]] = []
            locations = (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            )
            for hive, key_name in locations:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        for index in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, index)) as child:
                                    display, _ = winreg.QueryValueEx(child, "DisplayName")
                                    try:
                                        version, _ = winreg.QueryValueEx(child, "DisplayVersion")
                                    except OSError:
                                        version = None
                                    try:
                                        location, _ = winreg.QueryValueEx(child, "InstallLocation")
                                    except OSError:
                                        location = None
                                    registry_apps.append({"name": str(display), "version": str(version) if version else None, "location": str(location) if location else None})
                            except OSError:
                                continue
                except OSError:
                    continue
            patterns = {
                "unity_hub": r"Unity Hub|^Unity\b",
                "unreal": r"Unreal Engine|Epic Games Launcher",
                "blender": r"^Blender\b",
                "godot": r"^Godot\b",
                "aseprite": r"^Aseprite\b",
                "pixelorama": r"^Pixelorama\b",
                "tiled": r"^Tiled\b",
            }
            for key, pattern in patterns.items():
                matches = [item for item in registry_apps if re.search(pattern, str(item["name"]), re.I)]
                if matches:
                    existing = result.setdefault(key, {"available": False})
                    existing["available"] = True
                    existing["registry_matches"] = matches
        except (ImportError, OSError):
            pass
    return result


def detect_mcp(root: Path) -> dict[str, Any]:
    files: list[Path] = []
    for candidate in (root / ".mcp.json", root / ".codex" / "mcp.json", root / ".codex" / "config.toml"):
        if candidate.is_file():
            files.append(candidate)
    names: set[str] = set()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if path.suffix == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                servers = payload.get("mcpServers") or payload.get("mcp_servers") or {}
                if isinstance(servers, dict):
                    names.update(str(name) for name in servers)
        else:
            names.update(match.group(1) for match in re.finditer(r"(?m)^\[mcp_servers\.([A-Za-z0-9_.-]+)\]", text))
    return {"configuration_files": [str(path) for path in files], "server_names": sorted(names)}


def detect_gpu() -> dict[str, Any]:
    result: dict[str, Any] = {"vendor": None, "devices": [], "backends": []}
    system = platform.system()
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            probe = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
                errors="replace",
            )
            if probe.returncode == 0:
                for line in probe.stdout.splitlines():
                    parts = [part.strip() for part in line.split(",")]
                    if not parts or not parts[0]:
                        continue
                    memory = None
                    if len(parts) > 1:
                        try:
                            memory = int(float(parts[-1]))
                        except ValueError:
                            pass
                    result["devices"].append({"name": parts[0], "vendor": "NVIDIA", "vram_mib": memory})
                if result["devices"]:
                    result["vendor"] = "NVIDIA"
                    result["backends"].append("CUDA")
        except (OSError, subprocess.SubprocessError):
            pass
    if system == "Windows" and result["vendor"] is None:
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if powershell:
            try:
                probe = subprocess.run(
                    [powershell, "-NoProfile", "-NonInteractive", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                    errors="replace",
                )
                if probe.returncode == 0 and probe.stdout.strip():
                    payload = json.loads(probe.stdout)
                    values = payload if isinstance(payload, list) else [payload]
                    for item in values:
                        if not isinstance(item, dict) or not item.get("Name"):
                            continue
                        name = str(item["Name"])
                        vendor = "AMD" if re.search(r"AMD|Radeon", name, re.I) else "Intel" if re.search(r"Intel", name, re.I) else "Unknown"
                        memory = item.get("AdapterRAM")
                        result["devices"].append({"name": name, "vendor": vendor, "vram_mib": int(memory) // (1024 * 1024) if isinstance(memory, int) else None})
                    vendors = sorted({item["vendor"] for item in result["devices"] if item.get("vendor") != "Unknown"})
                    result["vendor"] = "+".join(vendors) if vendors else ("Unknown" if result["devices"] else None)
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
                pass
    if system == "Darwin":
        result["backends"].append("Metal")
        if result["vendor"] is None:
            result["vendor"] = "Apple-or-AMD"
            system_profiler = shutil.which("system_profiler")
            if system_profiler:
                try:
                    probe = subprocess.run([system_profiler, "SPDisplaysDataType", "-json"], capture_output=True, text=True, timeout=6, check=False, errors="replace")
                    payload = json.loads(probe.stdout) if probe.returncode == 0 else {}
                    for item in payload.get("SPDisplaysDataType", []):
                        name = item.get("sppci_model") or item.get("_name")
                        if name:
                            result["devices"].append({"name": str(name), "vendor": "Apple-or-AMD", "vram_mib": None})
                except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
                    pass
    elif system == "Windows":
        result["backends"].append("DirectML")
    elif system == "Linux" and result["vendor"] is None:
        lspci = shutil.which("lspci")
        if lspci:
            try:
                probe = subprocess.run([lspci], capture_output=True, text=True, timeout=4, check=False, errors="replace")
                for line in probe.stdout.splitlines():
                    if re.search(r"VGA|3D controller|Display controller", line, re.I):
                        vendor = "AMD" if re.search(r"AMD|ATI|Radeon", line, re.I) else "Intel" if "Intel" in line else "NVIDIA" if "NVIDIA" in line else "Unknown"
                        result["devices"].append({"name": line.split(":", 2)[-1].strip(), "vendor": vendor, "vram_mib": None})
                vendors = sorted({item["vendor"] for item in result["devices"] if item.get("vendor") != "Unknown"})
                result["vendor"] = "+".join(vendors) if vendors else ("Unknown" if result["devices"] else None)
            except (OSError, subprocess.SubprocessError):
                pass
    result["backends"] = sorted(set(result["backends"]))
    return result


def doctor(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    system = platform.system()
    wsl = bool(os.environ.get("WSL_DISTRO_NAME"))
    if not wsl and system == "Linux":
        try:
            wsl = "microsoft" in Path("/proc/version").read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            pass
    runtime_commands = {
        "python": (sys.executable, "--version"),
        "node": ("node", "--version"),
        "npm": ("npm", "--version"),
        "pnpm": ("pnpm", "--version"),
        "yarn": ("yarn", "--version"),
        "bun": ("bun", "--version"),
        "uv": ("uv", "--version"),
        "git": ("git", "--version"),
        "gh": ("gh", "--version"),
        "powershell": ("pwsh", "--version"),
    }
    runtimes = {name: run_probe(command) for name, command in runtime_commands.items()}
    usage = shutil.disk_usage(root)
    return {
        "schema_version": 1,
        "generated_at": iso_z(utc_now()),
        "read_only": True,
        "project_root": str(root),
        "platform": {
            "os": system,
            "release": platform.release(),
            "architecture": platform.machine().lower(),
            "execution": "wsl" if wsl else "native",
            "wsl_distribution": os.environ.get("WSL_DISTRO_NAME") if wsl else None,
        },
        "projects": detect_projects(root),
        "applications": detect_apps(),
        "runtimes": runtimes,
        "mcp": detect_mcp(root),
        "credentials": {"available_variable_names": sorted(name for name in KNOWN_CREDENTIALS if name in os.environ), "values_read": False},
        "gpu": detect_gpu(),
        "storage": {"free_bytes": usage.free, "total_bytes": usage.total},
        "network": {"performed": False, "required_for": ["catalog refresh --online", "external pack downloads after confirmation"]},
    }


def plan_digest(plan: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in plan.items() if key != "digest"}
    return sha256_bytes(canonical_json(unsigned))


def make_plan(
    *,
    kind: str,
    project_root: Path,
    actions: list[dict[str, Any]],
    downloads: list[dict[str, Any]] | None = None,
    licenses: list[dict[str, Any]] | None = None,
    permissions: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    detected_environment: dict[str, Any] | None = None,
    ttl_minutes: int = PLAN_TTL_MINUTES,
) -> dict[str, Any]:
    root = project_root.resolve()
    created = utc_now()
    backups: list[dict[str, Any]] = []
    rollbacks: list[dict[str, Any]] = []
    normalized_actions: list[dict[str, Any]] = []
    for raw in actions:
        action = dict(raw)
        target = str(action.get("target", ""))
        resolved = resolve_under(root, target)
        action["target"] = Path(target.replace("\\", "/")).as_posix()
        action["expected_before_sha256"] = file_sha256(resolved)
        normalized_actions.append(action)
        backups.append({"target": action["target"], "required": resolved.exists()})
        rollbacks.append({"operation": "restore-backup" if resolved.exists() else "remove-created", "target": action["target"]})
    plan: dict[str, Any] = {
        "schema_version": 1,
        "plan_id": str(uuid.uuid4()),
        "kind": kind,
        "created_at": iso_z(created),
        "expiry": iso_z(created + dt.timedelta(minutes=ttl_minutes)),
        "project_root": str(root),
        "detected_environment": detected_environment if detected_environment is not None else doctor(root),
        "exact_actions": normalized_actions,
        "downloads": downloads or [],
        "licenses": licenses or [],
        "permissions": permissions or [],
        "backups": backups,
        "rollback_operations": rollbacks,
        "metadata": metadata or {},
    }
    plan["digest"] = plan_digest(plan)
    return plan


def encode_action_json(value: Any) -> str:
    return base64.b64encode(json_bytes(value)).decode("ascii")


def decode_action_content(action: Mapping[str, Any]) -> bytes:
    encoded = action.get("content_base64")
    if not isinstance(encoded, str):
        raise StudioError("Action has no base64 content")
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise StudioError("Action content is not valid base64") from exc


def verify_plan(plan: Mapping[str, Any], *, project_root: Path, confirmed_digest: str) -> None:
    required = {
        "plan_id", "detected_environment", "exact_actions", "downloads", "licenses", "permissions",
        "backups", "rollback_operations", "expiry", "digest", "project_root",
    }
    missing = sorted(required.difference(plan))
    if missing:
        raise StudioError(f"Plan is missing required fields: {', '.join(missing)}")
    actual = plan_digest(plan)
    if not hmac.compare_digest(str(plan["digest"]), actual):
        raise StudioError("Plan was changed after its digest was calculated")
    if not hmac.compare_digest(str(plan["digest"]), confirmed_digest):
        raise StudioError("Confirmed digest does not match the proposed plan")
    if parse_time(str(plan["expiry"])) <= utc_now():
        raise StudioError("Plan has expired; run plan again")
    if Path(str(plan["project_root"])).resolve() != project_root.resolve():
        raise StudioError("Plan project root does not match --project")
    try:
        normalized_plan_id = str(uuid.UUID(str(plan["plan_id"])))
    except (ValueError, AttributeError) as exc:
        raise StudioError("Plan id must be a UUID") from exc
    if normalized_plan_id != str(plan["plan_id"]).lower():
        raise StudioError("Plan id is not in canonical UUID form")
    transaction = project_root / STATE_DIR / "transactions" / f"{normalized_plan_id}.json"
    if transaction.exists():
        raise StudioError("Plan has already been applied and cannot be replayed")


def apply_plan(plan: Mapping[str, Any], *, project_root: Path, confirmed_digest: str) -> dict[str, Any]:
    root = project_root.resolve()
    verify_plan(plan, project_root=root, confirmed_digest=confirmed_digest)
    plan_id = str(plan["plan_id"])
    backup_root = root / STATE_DIR / "backups" / plan_id
    journal_actions: list[dict[str, Any]] = []
    actions = plan.get("exact_actions")
    if not isinstance(actions, list):
        raise StudioError("Plan actions must be an array")
    # Preflight every action before making the first change.
    for action in actions:
        if not isinstance(action, dict) or action.get("operation") not in {"write-file", "remove-file", "restore-backup"}:
            raise StudioError("Plan contains an unsupported action")
        target = resolve_under(root, str(action.get("target", "")))
        if file_sha256(target) != action.get("expected_before_sha256"):
            raise StudioError(f"Target changed since planning: {action.get('target')}")
        if action["operation"] == "write-file":
            decode_action_content(action)
        if action["operation"] == "restore-backup":
            source = resolve_under(root, str(action.get("backup", "")))
            if not source.is_file():
                raise StudioError(f"Rollback backup is missing: {action.get('backup')}")
    try:
        for index, action in enumerate(actions):
            target = resolve_under(root, str(action["target"]))
            existed = target.is_file()
            backup_relative = None
            if existed:
                backup_relative = f"{STATE_DIR}/backups/{plan_id}/{index:04d}-{target.name}"
                backup = resolve_under(root, backup_relative)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            if action["operation"] == "write-file":
                atomic_write(target, decode_action_content(action))
            elif action["operation"] == "remove-file":
                if target.exists():
                    target.unlink()
            else:
                source = resolve_under(root, str(action["backup"]))
                atomic_write(target, source.read_bytes())
            journal_actions.append({
                "target": str(action["target"]),
                "operation": action["operation"],
                "before_sha256": action.get("expected_before_sha256"),
                "after_sha256": file_sha256(target),
                "backup": backup_relative,
                "created": not existed,
            })
    except Exception:
        # Best-effort immediate recovery of already executed actions.
        for item in reversed(journal_actions):
            target = resolve_under(root, item["target"])
            if item["backup"]:
                source = resolve_under(root, item["backup"])
                if source.is_file():
                    atomic_write(target, source.read_bytes())
            elif item["created"] and target.is_file():
                target.unlink()
        raise
    journal = {
        "schema_version": 1,
        "transaction_id": plan_id,
        "plan_digest": plan["digest"],
        "kind": plan.get("kind"),
        "applied_at": iso_z(utc_now()),
        "project_root": str(root),
        "actions": journal_actions,
        "status": "applied",
    }
    journal_path = root / STATE_DIR / "transactions" / f"{plan_id}.json"
    atomic_write(journal_path, json_bytes(journal))
    return journal


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repository_root() -> Path:
    root = plugin_root()
    for candidate in (root, *root.parents):
        if (candidate / ".agents" / "plugins" / "marketplace.json").is_file():
            return candidate
    return root


def descriptor_paths() -> list[Path]:
    roots = [plugin_root().parent, repository_root() / "plugins"]
    found: set[Path] = set()
    for root in roots:
        if root.is_dir():
            found.update(path.resolve() for path in root.glob("ai-game-studio-*/packs/*.json") if path.is_file())
    return sorted(found)


def load_descriptors() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in descriptor_paths():
        payload = safe_json_load(path)
        if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
            continue
        payload["_descriptor_path"] = str(path)
        result[payload["id"]] = payload
    return result


def edition_descriptor_paths() -> list[Path]:
    roots = [plugin_root().parent, repository_root() / "plugins"]
    found: set[Path] = set()
    for root in roots:
        if root.is_dir():
            found.update(path.resolve() for path in root.glob("ai-game-studio-*/editions/*.json") if path.is_file())
    return sorted(found)


def load_edition_descriptors() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in edition_descriptor_paths():
        payload = safe_json_load(path)
        if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
            continue
        payload["_descriptor_path"] = str(path)
        result[payload["id"]] = payload
    return result


def edition_host_detection(edition_id: str, environment: Mapping[str, Any]) -> dict[str, Any]:
    """Run fixed, read-only probes for the selected platform descriptor.

    Descriptor prose is never executed. Every process call below is a
    hard-coded argument array, and backend entries distinguish host evidence
    from compatibility with a later selected model or application.
    """

    platform_data = environment.get("platform")
    system = str(platform_data.get("os", "")) if isinstance(platform_data, Mapping) else ""
    gpu_data = environment.get("gpu")
    declared_backends = {
        str(value).lower()
        for value in (gpu_data.get("backends", []) if isinstance(gpu_data, Mapping) else [])
    }
    if edition_id == "windows":
        host_matches = system == "Windows"
        shells = {
            "powershell-7": run_probe(("pwsh.exe", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
            "windows-powershell": (
                run_probe(
                    (
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        "$PSVersionTable.PSVersion.ToString()",
                    )
                )
                if host_matches
                else {"available": False, "reason": "wrong-host"}
            ),
        }
        package_managers = {
            "winget": run_probe(("winget.exe", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
            "chocolatey": run_probe(("choco.exe", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
            "scoop": run_probe(("scoop", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
        }
        backends = {
            "cuda": {
                "available": host_matches and "cuda" in declared_backends,
                "verified_for_selected_tool": False,
                "evidence": "nvidia-smi device evidence" if "cuda" in declared_backends else "no CUDA device evidence",
            },
            "directml": {
                "available": host_matches and "directml" in declared_backends,
                "verified_for_selected_tool": False,
                "evidence": "Windows capability route; exact DirectX 12 and tool support require a later health check",
            },
            "cpu": {
                "available": host_matches,
                "verified_for_selected_tool": False,
                "evidence": "native Windows CPU route; performance and operation support remain unverified",
            },
            "warp": {
                "available": host_matches and shutil.which("dxdiag.exe") is not None,
                "verified_for_selected_tool": False,
                "evidence": "validation-only Windows software graphics route",
            },
        }
    elif edition_id == "macos":
        host_matches = system == "Darwin"
        shells = {
            "zsh": run_probe(("zsh", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
            "bash": run_probe(("bash", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
            "posix-sh": run_probe(("sh", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
        }
        package_managers = {
            "homebrew": run_probe(("brew", "--version")) if host_matches else {"available": False, "reason": "wrong-host"},
            "macports": run_probe(("port", "version")) if host_matches else {"available": False, "reason": "wrong-host"},
        }
        mps_probe = (
            run_probe(
                (
                    sys.executable,
                    "-c",
                    "import torch; print('available' if torch.backends.mps.is_available() else 'unavailable')",
                ),
                timeout=5.0,
            )
            if host_matches and importlib.util.find_spec("torch") is not None
            else {"available": False}
        )
        mps_available = (
            mps_probe.get("exit_code") == 0 and str(mps_probe.get("version", "")).strip() == "available"
        )
        coreml_available = host_matches and importlib.util.find_spec("coremltools") is not None
        backends = {
            "metal": {
                "available": host_matches and "metal" in declared_backends,
                "verified_for_selected_tool": False,
                "evidence": "Darwin graphics capability; exact tool support requires a later health check",
            },
            "mps": {
                "available": mps_available,
                "verified_for_selected_tool": False,
                "evidence": "active Python torch.backends.mps probe",
            },
            "core-ml": {
                "available": coreml_available,
                "verified_for_selected_tool": False,
                "evidence": "coremltools module presence; model operation compatibility remains unverified",
            },
            "cpu": {
                "available": host_matches,
                "verified_for_selected_tool": False,
                "evidence": "native macOS CPU route; performance and operation support remain unverified",
            },
        }
    else:
        raise StudioError(f"Unknown edition '{edition_id}'")
    return {
        "host_matches": host_matches,
        "shells": shells,
        "package_managers": package_managers,
        "gpu_backends": backends,
        "applications": environment.get("applications", {}),
        "mutations_performed": False,
    }


def state_documents(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project_file = project_root / STATE_DIR / "project.json"
    lock_file = project_root / STATE_DIR / "lock.json"
    project = safe_json_load(project_file, default={})
    lock = safe_json_load(lock_file, default={})
    if not isinstance(project, dict) or not isinstance(lock, dict):
        raise StudioError("Project state files must contain JSON objects")
    project.setdefault("schema_version", 1)
    project.setdefault("active_packs", {})
    project.setdefault("host_selection", {})
    lock.setdefault("schema_version", 1)
    lock.setdefault("dependencies", {})
    return project, lock


def write_action(target: str, value: Any) -> dict[str, Any]:
    return {"operation": "write-file", "target": target, "content_base64": encode_action_json(value)}


def edition_doctor(edition_id: str, *, project_root: Path) -> dict[str, Any]:
    descriptors = load_edition_descriptors()
    if edition_id not in descriptors:
        raise StudioError(
            f"Unknown edition '{edition_id}'. Available: {', '.join(sorted(descriptors)) or 'none'}"
        )
    descriptor = descriptors[edition_id]
    environment = doctor(project_root)
    environment["edition_detection"] = edition_host_detection(edition_id, environment)
    detected_platform = environment.get("platform") if isinstance(environment, dict) else {}
    system = str((detected_platform or {}).get("os", platform.system()))
    machine = str((detected_platform or {}).get("architecture", platform.machine())).lower()
    supported_architectures = [str(item).lower() for item in descriptor.get("supported_architectures", [])]
    target_os = str(descriptor.get("target_os", ""))
    return {
        "schema_version": 1,
        "read_only": True,
        "edition": edition_id,
        "display_name": descriptor.get("display_name"),
        "target_os": target_os,
        "target_matches_host": system == target_os,
        "architecture_supported": not supported_architectures or machine in supported_architectures,
        "detected_environment": environment,
        "native_capabilities": descriptor.get("native_capabilities", []),
        "adaptation_rules": descriptor.get("adaptation_rules", []),
        "health_checks": descriptor.get("health_checks", []),
        "limitations": descriptor.get("limitations", []),
        "mutation_performed": False,
    }


def edition_plan(edition_id: str, *, project_root: Path) -> dict[str, Any]:
    descriptors = load_edition_descriptors()
    if edition_id not in descriptors:
        raise StudioError(
            f"Unknown edition '{edition_id}'. Available: {', '.join(sorted(descriptors)) or 'none'}"
        )
    descriptor = descriptors[edition_id]
    system = platform.system()
    machine = platform.machine().lower()
    target_os = str(descriptor.get("target_os", ""))
    if system != target_os:
        raise StudioError(
            f"Edition {edition_id} targets {target_os}, but this host is {system}; "
            "use the matching edition or inspect its documented adaptation rules without applying it"
        )
    supported_architectures = [str(item).lower() for item in descriptor.get("supported_architectures", [])]
    if supported_architectures and machine not in supported_architectures:
        raise StudioError(
            f"Edition {edition_id} does not declare support for architecture {machine}"
        )
    project, lock = state_documents(project_root)
    stamp = iso_z(utc_now())
    descriptor_path = Path(str(descriptor["_descriptor_path"]))
    project["updated_at"] = stamp
    project["platform_edition"] = {
        "id": edition_id,
        "plugin": descriptor["plugin"],
        "target_os": target_os,
        "version": descriptor["version"],
        "status": "selected",
        "external_tools_installed": False,
    }
    lock["updated_at"] = stamp
    lock["dependencies"][f"edition:{edition_id}"] = {
        "plugin": descriptor["plugin"],
        "version": descriptor["version"],
        "license": descriptor.get("license", "MIT"),
        "descriptor_sha256": file_sha256(descriptor_path),
    }
    actions = [
        write_action(f"{STATE_DIR}/project.json", project),
        write_action(f"{STATE_DIR}/lock.json", lock),
    ]
    environment = doctor(project_root)
    environment["edition_detection"] = edition_host_detection(edition_id, environment)
    return make_plan(
        kind="edition-select",
        project_root=project_root,
        actions=actions,
        licenses=[
            {
                "component": descriptor["plugin"],
                "spdx": descriptor.get("license", "MIT"),
            }
        ],
        permissions=list(descriptor.get("permissions", [])),
        metadata={
            "edition": edition_id,
            "target_os": target_os,
            "architecture": machine,
            "descriptor_sha256": file_sha256(descriptor_path),
            "adaptation_rule_ids": [
                str(item.get("id"))
                for item in descriptor.get("adaptation_rules", [])
                if isinstance(item, dict) and item.get("id")
            ],
            "external_installation_performed": False,
        },
        detected_environment=environment,
    )


def edition_disable_plan(edition_id: str, *, project_root: Path) -> dict[str, Any]:
    descriptors = load_edition_descriptors()
    if edition_id not in descriptors:
        raise StudioError(f"Unknown edition '{edition_id}'")
    project, lock = state_documents(project_root)
    selected = project.get("platform_edition")
    if not isinstance(selected, dict) or selected.get("id") != edition_id:
        raise StudioError(f"Edition '{edition_id}' is not selected")
    project.pop("platform_edition", None)
    lock["dependencies"].pop(f"edition:{edition_id}", None)
    stamp = iso_z(utc_now())
    project["updated_at"] = stamp
    lock["updated_at"] = stamp
    actions = [
        write_action(f"{STATE_DIR}/project.json", project),
        write_action(f"{STATE_DIR}/lock.json", lock),
    ]
    return make_plan(
        kind="edition-disable",
        project_root=project_root,
        actions=actions,
        metadata={"edition": edition_id, "external_uninstall_performed": False},
    )


def pack_plan(
    pack_id: str,
    *,
    project_root: Path,
    replace: bool = False,
    provider: str | None = None,
    executable: str | None = None,
    executable_sha256: str | None = None,
    server_args: Sequence[str] = (),
) -> dict[str, Any]:
    descriptors = load_descriptors()
    if pack_id not in descriptors:
        raise StudioError(f"Unknown pack '{pack_id}'. Available: {', '.join(sorted(descriptors)) or 'none'}")
    descriptor = descriptors[pack_id]
    selected_upstream = dict(descriptor["upstream"])
    if provider and provider.lower() != "default":
        selectable = [item for item in descriptor.get("alternatives", []) if isinstance(item, dict) and item.get("repository") and item.get("ref")]
        match = next((item for item in selectable if str(item["repository"]).lower() == provider.lower()), None)
        if match is None:
            names = [str(item["repository"]) for item in selectable]
            raise StudioError(f"Provider '{provider}' is not selectable for {pack_id}. Available: default ({selected_upstream['repository']})" + (", " + ", ".join(names) if names else ""))
        selected_upstream = {
            "repository": match["repository"],
            "url": match.get("url") or f"https://github.com/{match['repository']}",
            "ref": match["ref"],
            "license": match["license"],
            "verified_at": match.get("verified_at") or descriptor["upstream"].get("verified_at"),
        }
    system = platform.system()
    machine = platform.machine().lower()
    if system not in descriptor.get("supported_os", []):
        raise StudioError(f"Pack {pack_id} does not support {system}")
    supported_arch = [item.lower() for item in descriptor.get("supported_architectures", [])]
    if supported_arch and machine not in supported_arch:
        raise StudioError(f"Pack {pack_id} does not declare support for architecture {machine}")
    project, lock = state_documents(project_root)
    host = str(descriptor["host_application"])
    current = project["host_selection"].get(host)
    if current and current != pack_id and not replace:
        raise StudioError(f"Host '{host}' already uses pack '{current}'. Re-run with --replace to propose a substitution")
    server: dict[str, Any] = {"enabled": False, "status": "awaiting-external-server"}
    if executable:
        path = Path(executable).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise StudioError("--server-executable must be an existing absolute file")
        actual = file_sha256(path)
        if not executable_sha256 or not hmac.compare_digest(actual or "", executable_sha256.lower()):
            raise StudioError("--server-sha256 must match the selected executable")
        server = {
            "enabled": True,
            "status": "configured",
            "executable": str(path.resolve()),
            "sha256": actual,
            "args": list(server_args),
        }
    project["updated_at"] = iso_z(utc_now())
    project["active_packs"][pack_id] = {
        "host_application": host,
        "descriptor_version": descriptor["version"],
        "provider": selected_upstream["repository"],
        "server": server,
    }
    project["host_selection"][host] = pack_id
    if current and current != pack_id:
        project["active_packs"].pop(current, None)
        lock["dependencies"].pop(current, None)
    lock["updated_at"] = project["updated_at"]
    lock["dependencies"][pack_id] = {
        "repository": selected_upstream["repository"],
        "ref": selected_upstream["ref"],
        "license": selected_upstream["license"],
        "descriptor_sha256": file_sha256(Path(descriptor["_descriptor_path"])),
    }
    actions = [write_action(f"{STATE_DIR}/project.json", project), write_action(f"{STATE_DIR}/lock.json", lock)]
    return make_plan(
        kind="pack-enable",
        project_root=project_root,
        actions=actions,
        downloads=[{
            "url": f"{selected_upstream['url']}/archive/{selected_upstream['ref']}.zip",
            "ref": selected_upstream["ref"],
            "automatic": False,
            "expected_size_bytes": None,
            "reason": "External source reference; download only after proposal confirmation and license review.",
        }],
        licenses=[{"component": selected_upstream["repository"], "spdx": selected_upstream["license"]}],
        permissions=list(descriptor.get("permissions", [])),
        metadata={"pack_id": pack_id, "host_application": host, "provider": selected_upstream["repository"], "replaces": current if current != pack_id else None},
    )


def pack_disable_plan(pack_id: str, *, project_root: Path) -> dict[str, Any]:
    descriptors = load_descriptors()
    if pack_id not in descriptors:
        raise StudioError(f"Unknown pack '{pack_id}'")
    project, lock = state_documents(project_root)
    existing = project["active_packs"].get(pack_id)
    if not existing:
        raise StudioError(f"Pack '{pack_id}' is not active")
    host = existing.get("host_application")
    project["active_packs"].pop(pack_id, None)
    if project["host_selection"].get(host) == pack_id:
        project["host_selection"].pop(host, None)
    lock["dependencies"].pop(pack_id, None)
    stamp = iso_z(utc_now())
    project["updated_at"] = stamp
    lock["updated_at"] = stamp
    actions = [write_action(f"{STATE_DIR}/project.json", project), write_action(f"{STATE_DIR}/lock.json", lock)]
    return make_plan(kind="pack-disable", project_root=project_root, actions=actions, metadata={"pack_id": pack_id, "host_application": host})


def rollback_plan(
    transaction_id: str,
    *,
    project_root: Path,
    allowed_original_kinds: set[str] | None = None,
) -> dict[str, Any]:
    try:
        normalized_transaction_id = str(uuid.UUID(transaction_id))
    except (ValueError, AttributeError) as exc:
        raise StudioError("Transaction id must be a UUID") from exc
    if normalized_transaction_id != transaction_id.lower():
        raise StudioError("Transaction id is not in canonical UUID form")
    journal_path = project_root / STATE_DIR / "transactions" / f"{normalized_transaction_id}.json"
    journal = safe_json_load(journal_path)
    if not isinstance(journal, dict) or journal.get("status") != "applied":
        raise StudioError(f"Applied transaction not found: {transaction_id}")
    original_kind = str(journal.get("kind", ""))
    if allowed_original_kinds is not None and original_kind not in allowed_original_kinds:
        raise StudioError(
            f"Transaction kind {original_kind!r} cannot be rolled back through this command"
        )
    actions: list[dict[str, Any]] = []
    for item in reversed(journal.get("actions", [])):
        target = str(item["target"])
        current = resolve_under(project_root, target)
        if item.get("backup"):
            actions.append({"operation": "restore-backup", "target": target, "backup": item["backup"]})
        elif item.get("created"):
            actions.append({"operation": "remove-file", "target": target})
        else:
            raise StudioError(f"Transaction has no rollback source for {target}")
        actions[-1]["expected_before_sha256"] = file_sha256(current)
    plan = make_plan(
        kind="rollback",
        project_root=project_root,
        actions=[],
        metadata={"transaction_id": transaction_id, "original_kind": original_kind},
    )
    # make_plan cannot infer the previous transaction's backups, so install the
    # validated rollback actions and recompute all derived fields.
    plan["exact_actions"] = actions
    plan["backups"] = [{"target": item["target"], "required": resolve_under(project_root, item["target"]).exists()} for item in actions]
    plan["rollback_operations"] = [{"operation": "restore-rollback-attempt", "target": item["target"]} for item in actions]
    plan["digest"] = plan_digest(plan)
    return plan


def validate_edition_apply_plan(plan: Mapping[str, Any]) -> None:
    kind = str(plan.get("kind", ""))
    if kind not in {"edition-select", "edition-disable", "rollback"}:
        raise StudioError(f"Plan kind {kind!r} cannot be applied through edition apply")
    metadata = plan.get("metadata")
    if kind == "rollback" and (
        not isinstance(metadata, Mapping)
        or metadata.get("original_kind") not in {"edition-select", "edition-disable"}
    ):
        raise StudioError("Edition rollback plan does not reference an edition transaction")
    actions = plan.get("exact_actions")
    if not isinstance(actions, list):
        raise StudioError("Edition plan actions must be an array")
    allowed_targets = {
        f"{STATE_DIR}/project.json",
        f"{STATE_DIR}/lock.json",
    }
    for action in actions:
        target = str(action.get("target", "")) if isinstance(action, Mapping) else ""
        if target not in allowed_targets:
            raise StudioError(f"Edition plan may not change {target or 'an unnamed target'}")


def pack_doctor(project_root: Path) -> dict[str, Any]:
    descriptors = load_descriptors()
    project, lock = state_documents(project_root)
    findings: list[dict[str, Any]] = []
    host_seen: dict[str, str] = {}
    for pack_id, selection in sorted(project.get("active_packs", {}).items()):
        errors: list[str] = []
        descriptor = descriptors.get(pack_id)
        if descriptor is None:
            errors.append("descriptor-missing")
        host = str(selection.get("host_application"))
        if host in host_seen and host_seen[host] != pack_id:
            errors.append(f"host-conflict:{host_seen[host]}")
        host_seen[host] = pack_id
        server = selection.get("server") or {}
        if server.get("enabled"):
            executable = Path(str(server.get("executable", "")))
            if not executable.is_absolute() or not executable.is_file():
                errors.append("server-executable-missing")
            elif file_sha256(executable) != server.get("sha256"):
                errors.append("server-executable-hash-mismatch")
        else:
            errors.append("server-not-enabled")
        pin = lock.get("dependencies", {}).get(pack_id)
        if not pin:
            errors.append("lock-pin-missing")
        elif descriptor is not None:
            allowed = [descriptor.get("upstream"), *descriptor.get("alternatives", [])]
            allowed_pins = {
                (str(item.get("repository")), str(item.get("ref")), str(item.get("license")))
                for item in allowed
                if isinstance(item, dict) and item.get("repository") and item.get("ref")
            }
            actual_pin = (str(pin.get("repository")), str(pin.get("ref")), str(pin.get("license")))
            if actual_pin not in allowed_pins:
                errors.append("lock-pin-not-declared")
            if selection.get("provider") != pin.get("repository"):
                errors.append("provider-lock-mismatch")
            if pin.get("descriptor_sha256") != file_sha256(Path(descriptor["_descriptor_path"])):
                errors.append("descriptor-hash-mismatch")
        findings.append({"pack_id": pack_id, "host_application": host, "healthy": not errors, "errors": errors, "server_enabled": bool(server.get("enabled"))})
    return {"project_root": str(project_root.resolve()), "healthy": all(item["healthy"] for item in findings), "packs": findings, "available_descriptors": sorted(descriptors)}


def catalog_records() -> list[dict[str, Any]]:
    candidates = [plugin_root() / "catalog", plugin_root() / "references" / "catalog", repository_root() / "catalog"]
    records: list[dict[str, Any]] = []
    seen_files: set[Path] = set()
    for root in candidates:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json")):
            resolved = path.resolve()
            if resolved in seen_files or path.name.endswith("schema.json") or "snapshots" in path.parts:
                continue
            seen_files.add(resolved)
            try:
                payload = safe_json_load(path)
            except StudioError:
                continue
            values = payload if isinstance(payload, list) else (payload.get("records") or payload.get("repositories") or []) if isinstance(payload, dict) else []
            if isinstance(values, list):
                records.extend(item for item in values if isinstance(item, dict) and (item.get("id") or item.get("repository") or item.get("canonical_url")))
    unique: dict[str, dict[str, Any]] = {}
    for record in records:
        repository = record.get("repository")
        nested_url = repository.get("canonical_url") if isinstance(repository, dict) else None
        key = str(record.get("id") or record.get("canonical_url") or nested_url or repository)
        unique[key] = record
    return list(unique.values())


def record_text(record: Mapping[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True).lower()


def catalog_search(query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    terms = [term for term in re.split(r"\s+", query.lower().strip()) if term]
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in catalog_records():
        text = record_text(record)
        score = sum(4 if term in str(record.get("id", "")).lower() else 1 for term in terms if term in text)
        if not terms or score:
            scored.append((score, record))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
    return [record for _, record in scored[:limit]]


def catalog_recommend(*, capability: Sequence[str], engine: str | None, commercial: bool, limit: int) -> list[dict[str, Any]]:
    system = platform.system().lower()
    gpu = detect_gpu()
    backends = {str(item).lower() for item in gpu.get("backends", [])}
    available_vram = max((item.get("vram_mib") or 0 for item in gpu.get("devices", []) if isinstance(item, dict)), default=0) / 1024
    results: list[tuple[int, dict[str, Any], list[str]]] = []
    for record in catalog_records():
        text = record_text(record)
        reasons: list[str] = []
        score = 0
        for item in capability:
            if item.lower() in text:
                score += 3
                reasons.append(f"capability:{item}")
        if engine and engine.lower() in text:
            score += 2
            reasons.append(f"engine:{engine}")
        platform_support = record.get("platform_support") if isinstance(record.get("platform_support"), dict) else {}
        os_declared = [str(item).lower() for item in platform_support.get("operating_systems", [])]
        known_os = [item for item in os_declared if item not in {"unknown", "cross-platform", "any"}]
        if known_os and system not in known_os:
            continue
        if system in os_declared or "cross-platform" in os_declared:
            score += 1
            reasons.append(f"os:{system}")
        elif "unknown" in os_declared:
            reasons.append("os:verification-required")
        requirements = record.get("requirements") if isinstance(record.get("requirements"), dict) else {}
        gpu_requirement = requirements.get("gpu") if isinstance(requirements.get("gpu"), dict) else {}
        required_backends = {str(item).lower() for item in gpu_requirement.get("backends", [])}
        minimum_vram = gpu_requirement.get("minimum_vram_gb")
        if required_backends and not required_backends.intersection(backends):
            continue
        if isinstance(minimum_vram, (int, float)) and minimum_vram > available_vram:
            continue
        if required_backends:
            reasons.append("gpu-backend:" + ",".join(sorted(required_backends.intersection(backends))))
            score += 1
        if isinstance(minimum_vram, (int, float)):
            reasons.append(f"vram:{minimum_vram:g}GB-required/{available_vram:g}GB-available")
        license_value = record.get("licenses") or record.get("license")
        if commercial:
            if not license_value:
                continue
            if isinstance(license_value, dict):
                blocking_states = {"unknown", "custom", "restricted", "prohibited"}
                scoped_statuses = {
                    str(license_value.get(scope, {}).get("status", ""))
                    for scope in ("code", "model_weights", "dataset", "generated_output")
                    if isinstance(license_value.get(scope), dict)
                }
                commercial_status = str((license_value.get("commercial_use") or {}).get("status", "")) if isinstance(license_value.get("commercial_use"), dict) else ""
                if blocking_states.intersection(scoped_statuses) or commercial_status == "blocked":
                    continue
                if commercial_status == "review_required":
                    reasons.append("license:human-review-required")
            else:
                licenses_text = str(license_value).lower()
                if any(token in licenses_text for token in ("unknown", "custom", "restricted", "prohibited")):
                    continue
        if score:
            results.append((score, record, reasons))
    results.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
    return [{"score": score, "reasons": reasons, "record": record} for score, record, reasons in results[:limit]]


def github_identity(record: Mapping[str, Any]) -> tuple[str, str] | None:
    repository = record.get("repository")
    if isinstance(repository, dict):
        value = str(repository.get("canonical_url") or repository.get("full_name") or "")
    else:
        value = str(record.get("canonical_url") or record.get("url") or repository or "")
    match = re.search(r"github\.com/([^/]+)/([^/#?]+)", value)
    if not match and re.fullmatch(r"[^/]+/[^/]+", value):
        return tuple(value.split("/", 1))  # type: ignore[return-value]
    return (match.group(1), match.group(2).removesuffix(".git")) if match else None


def catalog_refresh_plan(project_root: Path, *, online: bool, limit: int | None = None) -> dict[str, Any]:
    snapshot: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    records = catalog_records()
    if limit is not None:
        records = records[:limit]
    for record in records:
        identity = github_identity(record)
        if not identity:
            continue
        owner, repo = identity
        item: dict[str, Any] = {"repository": f"{owner}/{repo}", "source": "offline", "refreshed_at": iso_z(utc_now())}
        if online:
            request = Request(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Accept": "application/vnd.github+json", "User-Agent": "codex-ai-game-studio/1.0"},
            )
            token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
            if token:
                request.add_header("Authorization", f"Bearer {token}")
            try:
                with urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read(MAX_JSON_BYTES))
                item.update({
                    "source": "github-api",
                    "stars": payload.get("stargazers_count"),
                    "archived": payload.get("archived"),
                    "pushed_at": payload.get("pushed_at"),
                    "default_branch": payload.get("default_branch"),
                })
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                errors.append({"repository": item["repository"], "error": type(exc).__name__})
        snapshot.append(item)
    value = {"schema_version": 1, "generated_at": iso_z(utc_now()), "records": snapshot, "errors": errors, "offline_fallback": not online or bool(errors)}
    action = write_action(f"{STATE_DIR}/catalog/volatile.json", value)
    return make_plan(
        kind="catalog-refresh",
        project_root=project_root,
        actions=[action],
        permissions=["read GitHub repository metadata over HTTPS"] if online else [],
        metadata={"online": online, "record_count": len(snapshot), "error_count": len(errors)},
    )


def migrate_claude_plan(project_root: Path) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    source = project_root / "CLAUDE.md"
    source_files = [str(path.relative_to(project_root)).replace("\\", "/") for path in sorted(project_root.glob(".claude/**/*")) if path.is_file()][:500]
    unresolved: list[str] = []
    if source.is_file():
        text = source.read_text(encoding="utf-8-sig", errors="replace")
        text = text.replace("Claude Code", "Codex").replace("CLAUDE.md", "AGENTS.md").replace(".claude/", ".codex/").replace(".claude\\", ".codex\\")
        text = re.sub(r"\bClaude\b", "Codex", text)
        text = re.sub(r"(?m)(?<![\w$])/(?!/)([a-z][a-z0-9-]+)\b", r"$ai-game-studio:\1", text)
        # Agent frontmatter keys from Claude projects are not valid project
        # guidance and would accidentally pin runtime behavior in Codex.
        text = re.sub(r"(?im)^\s*(?:model|tools|max[_ -]?turns|memory)\s*:\s*.*(?:\r?\n|$)", "", text)
        actions.append({"operation": "write-file", "target": "AGENTS.md", "content_base64": base64.b64encode(text.encode("utf-8")).decode("ascii")})
    for relative in source_files:
        if relative.endswith(("settings.json", "settings.local.json")) or "/hooks/" in relative or "/agents/" in relative:
            unresolved.append(relative)
    report = {
        "schema_version": 1,
        "source": "claude",
        "generated_at": iso_z(utc_now()),
        "source_files": source_files,
        "converted": ["CLAUDE.md -> AGENTS.md"] if source.is_file() else [],
        "review_required": unresolved,
        "notes": [
            "Original Claude files are preserved.",
            "Review hook and agent files against Codex schemas before materializing them.",
            "Use namespaced $ai-game-studio:<skill> references instead of legacy slash handoffs.",
        ],
    }
    actions.append(write_action(f"{STATE_DIR}/migration-report.json", report))
    project, lock = state_documents(project_root)
    project["migration"] = {
        "source": "claude",
        "planned_at": iso_z(utc_now()),
        "source_files": source_files,
        "review_required": unresolved,
    }
    lock["migration_source"] = "claude"
    actions.extend([write_action(f"{STATE_DIR}/project.json", project), write_action(f"{STATE_DIR}/lock.json", lock)])
    return make_plan(
        kind="migrate-claude",
        project_root=project_root,
        actions=actions,
        metadata={"source_present": source.is_file(), "claude_directory_present": (project_root / ".claude").is_dir(), "review_required": unresolved},
    )


def validate_plugin(path: Path) -> list[str]:
    errors: list[str] = []
    manifest = path / ".codex-plugin" / "plugin.json"
    payload = safe_json_load(manifest, default=None)
    if not isinstance(payload, dict):
        return ["missing-or-invalid-plugin-manifest"]
    for key in ("name", "version", "description", "author", "license"):
        if key not in payload:
            errors.append(f"manifest-missing:{key}")
    interface = payload.get("interface")
    if not isinstance(interface, dict) or not isinstance(interface.get("displayName"), str) or not interface["displayName"].strip():
        errors.append("manifest-missing:interface.displayName")
    if "hooks" in payload:
        errors.append("manifest-hooks-field-not-allowed-use-auto-discovery")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(payload.get("version", ""))):
        errors.append("manifest-version-not-semver")
    return errors


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, text[end + 5 :]


def validate_skills(path: Path) -> list[str]:
    errors: list[str] = []
    for skill in sorted(path.rglob("SKILL.md")):
        fields, _body = parse_frontmatter(skill)
        if set(fields) != {"name", "description"}:
            errors.append(f"{skill}:frontmatter-must-only-name-description")
        if fields.get("name") != skill.parent.name:
            errors.append(f"{skill}:name-directory-mismatch")
        metadata = skill.parent / "agents" / "openai.yaml"
        if not metadata.is_file():
            errors.append(f"{skill}:missing-agents/openai.yaml")
        else:
            meta_text = metadata.read_text(encoding="utf-8-sig", errors="replace")
            raw_invocation = "$" + skill.parent.name
            namespaced_invocation = re.search(rf"\$[a-z0-9-]+:{re.escape(skill.parent.name)}\b", meta_text)
            if raw_invocation not in meta_text and not namespaced_invocation:
                errors.append(f"{metadata}:default_prompt-must-name-skill")
    return errors


def validate_catalog(path: Path) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    urls: set[str] = set()
    for file in sorted(path.rglob("*.json")):
        ignored_parts = {"snapshots", ".tmp", ".git", "__pycache__", "release", "dist", "build"}
        if file.name.endswith("schema.json") or ignored_parts.intersection(file.parts):
            continue
        try:
            payload = safe_json_load(file)
        except StudioError as exc:
            errors.append(str(exc))
            continue
        values = payload if isinstance(payload, list) else (payload.get("records") or payload.get("repositories") or []) if isinstance(payload, dict) else []
        if not isinstance(values, list):
            continue
        for index, record in enumerate(values):
            if not isinstance(record, dict):
                errors.append(f"{file}:{index}:record-not-object")
                continue
            identifier = str(record.get("id", ""))
            repository = record.get("repository")
            nested_url = repository.get("canonical_url") if isinstance(repository, dict) else ""
            url = str(record.get("canonical_url") or nested_url or "")
            if identifier and identifier in ids:
                errors.append(f"duplicate-catalog-id:{identifier}")
            if url and url in urls:
                errors.append(f"duplicate-canonical-url:{url}")
            ids.add(identifier)
            urls.add(url)
            raw = json.dumps(record)
            for credential in KNOWN_CREDENTIALS:
                if re.search(rf'"{re.escape(credential)}"\s*:\s*"[^"$][^"]+"', raw):
                    errors.append(f"{file}:{identifier}:credential-value-present:{credential}")
    return errors


def validate_parity(path: Path) -> list[str]:
    if path.is_dir():
        candidates = (path / "parity" / "ledger.json", path / "ledger.json")
        path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    payload = safe_json_load(path, default=None)
    if not isinstance(payload, dict):
        return ["parity-ledger-missing-or-invalid"]
    expected = {"skill": 73, "role": 49, "hook-behavior": 12, "rule": 11, "template": 40}
    errors: list[str] = []
    entries = payload.get("entries")
    if isinstance(entries, list):
        by_kind: dict[str, list[dict[str, Any]]] = {key: [] for key in expected}
        seen: set[tuple[str, str]] = set()
        for item in entries:
            if not isinstance(item, dict):
                errors.append("parity-entry-not-object")
                continue
            kind = str(item.get("kind", ""))
            identifier = str(item.get("id", ""))
            if kind in by_kind:
                by_kind[kind].append(item)
            key = (kind, identifier)
            if key in seen:
                errors.append(f"parity-duplicate:{kind}:{identifier}")
            seen.add(key)
            if item.get("status") not in {"ported", "replaced", "not-applicable"}:
                errors.append(f"parity-status:{kind}:{identifier}")
            for field in ("source_path", "source_commit", "destination", "tests"):
                if field not in item:
                    errors.append(f"parity-entry-missing:{kind}:{identifier}:{field}")
        for kind, count in expected.items():
            actual = len(by_kind[kind])
            if actual != count:
                errors.append(f"parity-count:{kind}:expected-{count}:actual-{actual}")
        native = payload.get("native_skills", [])
        if not isinstance(native, list) or len(native) != 12:
            errors.append(f"parity-count:native-skill:expected-12:actual-{len(native) if isinstance(native, list) else 'invalid'}")
        declared = payload.get("actual", {})
        if isinstance(declared, dict):
            for kind, count in {**expected, "native-skill": 12, "total-core-skills": 85}.items():
                if declared.get(kind) != count:
                    errors.append(f"parity-declared-actual:{kind}:expected-{count}:actual-{declared.get(kind)}")
    else:
        # Also accept the simpler category-array representation used by early
        # development ledgers.
        aliases = {"skill": "skills", "role": "roles", "hook-behavior": "hook_behaviors", "rule": "rules", "template": "templates"}
        for kind, count in expected.items():
            value = payload.get(aliases[kind], [])
            if isinstance(value, dict):
                value = list(value.values())
            if not isinstance(value, list) or len(value) != count:
                errors.append(f"parity-count:{kind}:expected-{count}:actual-{len(value) if isinstance(value, list) else 'invalid'}")
            elif any(item.get("status") not in {"ported", "replaced", "not-applicable"} for item in value if isinstance(item, dict)):
                errors.append(f"parity-status:{kind}")
    return errors


def validate_platform(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for descriptor_path in sorted((repo_root / "plugins").glob("ai-game-studio-*/packs/*.json")):
        descriptor = safe_json_load(descriptor_path, default={})
        for key in ("id", "version", "host_application", "supported_os", "supported_architectures", "upstream", "permissions", "health_checks", "uninstall", "rollback"):
            if key not in descriptor:
                errors.append(f"{descriptor_path}:missing:{key}")
        if not set(descriptor.get("supported_os", [])).issubset(SUPPORTED_OS):
            errors.append(f"{descriptor_path}:unsupported-os-value")
        ref = str((descriptor.get("upstream") or {}).get("ref", ""))
        if not re.fullmatch(r"[0-9a-f]{40}|v?\d+\.\d+\.\d+(?:[-.][0-9A-Za-z.-]+)?", ref):
            errors.append(f"{descriptor_path}:unpinned-upstream-ref")
    expected_editions = {"windows": "Windows", "macos": "Darwin"}
    found_editions: set[str] = set()
    for descriptor_path in sorted((repo_root / "plugins").glob("ai-game-studio-*/editions/*.json")):
        descriptor = safe_json_load(descriptor_path, default={})
        edition_id = str(descriptor.get("id", ""))
        found_editions.add(edition_id)
        for key in (
            "id",
            "plugin",
            "version",
            "license",
            "target_os",
            "supported_architectures",
            "native_capabilities",
            "adaptation_rules",
            "permissions",
            "health_checks",
            "uninstall",
            "rollback",
            "activation",
        ):
            if key not in descriptor:
                errors.append(f"{descriptor_path}:missing:{key}")
        if descriptor.get("target_os") != expected_editions.get(edition_id):
            errors.append(f"{descriptor_path}:edition-target-os-mismatch")
        if descriptor.get("license") != "MIT":
            errors.append(f"{descriptor_path}:unsupported-edition-license")
        activation = descriptor.get("activation")
        if not isinstance(activation, dict) or activation.get("mode") != "confirmed-transaction-only":
            errors.append(f"{descriptor_path}:edition-confirmation-required")
        for rule in descriptor.get("adaptation_rules", []):
            if not isinstance(rule, dict) or rule.get("requires_confirmation") is not True:
                errors.append(f"{descriptor_path}:unconfirmed-adaptation-rule")
    if found_editions != set(expected_editions):
        errors.append(
            f"edition-set:expected-{sorted(expected_editions)}:actual-{sorted(found_editions)}"
        )
    for launcher in (repo_root / "plugins" / "ai-game-studio" / "scripts" / "ai-game-studio.sh", repo_root / "plugins" / "ai-game-studio" / "scripts" / "ai-game-studio.ps1"):
        if not launcher.is_file():
            errors.append(f"missing-launcher:{launcher}")
    return errors


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def maybe_write_plan(plan: dict[str, Any], output: str | None) -> None:
    if output:
        atomic_write(Path(output).expanduser().resolve(), json_bytes(plan))
    emit(plan)


def add_project_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", default=".", help="Project root (default: current directory)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-game-studio", description="Codex AI Game Studio deterministic runtime")
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor_parser = commands.add_parser("doctor", help="Inspect the environment without changing it")
    add_project_argument(doctor_parser)

    catalog = commands.add_parser("catalog", help="Search, recommend, or plan a metadata refresh").add_subparsers(dest="catalog_command", required=True)
    search = catalog.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    recommend = catalog.add_parser("recommend")
    recommend.add_argument("--capability", action="append", default=[])
    recommend.add_argument("--engine")
    recommend.add_argument("--commercial", action="store_true")
    recommend.add_argument("--limit", type=int, default=10)
    refresh = catalog.add_parser("refresh")
    add_project_argument(refresh)
    refresh.add_argument("--online", action="store_true", help="Read public GitHub metadata while building the proposal")
    refresh.add_argument("--limit", type=int)
    refresh.add_argument("--output", help="Optional plan file; no catalog data is changed")

    pack = commands.add_parser("pack", help="Inspect and transact optional packs").add_subparsers(dest="pack_command", required=True)
    pack_doctor_parser = pack.add_parser("doctor")
    add_project_argument(pack_doctor_parser)
    plan = pack.add_parser("plan")
    plan.add_argument("pack_id")
    add_project_argument(plan)
    plan.add_argument("--replace", action="store_true")
    plan.add_argument("--provider", help="Exact selectable upstream repository; omit for the pinned default")
    plan.add_argument("--server-executable")
    plan.add_argument("--server-sha256")
    plan.add_argument("--server-arg", action="append", default=[])
    plan.add_argument("--output")
    apply_parser = pack.add_parser("apply")
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--confirmed-digest", required=True)
    add_project_argument(apply_parser)
    disable = pack.add_parser("disable")
    disable.add_argument("pack_id")
    add_project_argument(disable)
    disable.add_argument("--output")
    rollback = pack.add_parser("rollback")
    rollback.add_argument("transaction_id")
    add_project_argument(rollback)
    rollback.add_argument("--output")

    edition = commands.add_parser(
        "edition", help="Inspect and select a Windows or macOS compatibility edition"
    ).add_subparsers(dest="edition_command", required=True)
    edition_doctor_parser = edition.add_parser("doctor")
    edition_doctor_parser.add_argument("edition_id", choices=("windows", "macos"))
    add_project_argument(edition_doctor_parser)
    edition_plan_parser = edition.add_parser("plan")
    edition_plan_parser.add_argument("edition_id", choices=("windows", "macos"))
    add_project_argument(edition_plan_parser)
    edition_plan_parser.add_argument("--output")
    edition_apply_parser = edition.add_parser("apply")
    edition_apply_parser.add_argument("--plan", required=True)
    edition_apply_parser.add_argument("--confirmed-digest", required=True)
    add_project_argument(edition_apply_parser)
    edition_disable_parser = edition.add_parser("disable")
    edition_disable_parser.add_argument("edition_id", choices=("windows", "macos"))
    add_project_argument(edition_disable_parser)
    edition_disable_parser.add_argument("--output")
    edition_rollback_parser = edition.add_parser("rollback")
    edition_rollback_parser.add_argument("transaction_id")
    add_project_argument(edition_rollback_parser)
    edition_rollback_parser.add_argument("--output")

    migrate = commands.add_parser("migrate", help="Plan a migration").add_subparsers(dest="migrate_command", required=True)
    claude = migrate.add_parser("claude")
    add_project_argument(claude)
    claude.add_argument("--output")

    validate = commands.add_parser("validate", help="Run deterministic validators").add_subparsers(dest="validate_command", required=True)
    for name in ("plugin", "skills", "catalog", "parity", "platform"):
        child = validate.add_parser(name)
        child.add_argument("path", nargs="?", default=".")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            emit(doctor(Path(args.project)))
        elif args.command == "catalog":
            if args.catalog_command == "search":
                emit({"query": args.query, "results": catalog_search(args.query, limit=max(1, args.limit))})
            elif args.catalog_command == "recommend":
                emit({"results": catalog_recommend(capability=args.capability, engine=args.engine, commercial=args.commercial, limit=max(1, args.limit))})
            else:
                maybe_write_plan(catalog_refresh_plan(Path(args.project), online=args.online, limit=args.limit), args.output)
        elif args.command == "pack":
            root = Path(args.project)
            if args.pack_command == "doctor":
                emit(pack_doctor(root))
            elif args.pack_command == "plan":
                plan = pack_plan(
                    args.pack_id,
                    project_root=root,
                    replace=args.replace,
                    provider=args.provider,
                    executable=args.server_executable,
                    executable_sha256=args.server_sha256,
                    server_args=args.server_arg,
                )
                maybe_write_plan(plan, args.output)
            elif args.pack_command == "apply":
                plan = safe_json_load(Path(args.plan).expanduser().resolve())
                if not isinstance(plan, dict):
                    raise StudioError("Plan file must contain a JSON object")
                emit(apply_plan(plan, project_root=root, confirmed_digest=args.confirmed_digest))
            elif args.pack_command == "disable":
                maybe_write_plan(pack_disable_plan(args.pack_id, project_root=root), args.output)
            else:
                maybe_write_plan(rollback_plan(args.transaction_id, project_root=root), args.output)
        elif args.command == "edition":
            root = Path(args.project)
            if args.edition_command == "doctor":
                emit(edition_doctor(args.edition_id, project_root=root))
            elif args.edition_command == "plan":
                maybe_write_plan(edition_plan(args.edition_id, project_root=root), args.output)
            elif args.edition_command == "apply":
                plan = safe_json_load(Path(args.plan).expanduser().resolve())
                if not isinstance(plan, dict):
                    raise StudioError("Plan file must contain a JSON object")
                validate_edition_apply_plan(plan)
                emit(apply_plan(plan, project_root=root, confirmed_digest=args.confirmed_digest))
            elif args.edition_command == "disable":
                maybe_write_plan(edition_disable_plan(args.edition_id, project_root=root), args.output)
            else:
                maybe_write_plan(
                    rollback_plan(
                        args.transaction_id,
                        project_root=root,
                        allowed_original_kinds={"edition-select", "edition-disable"},
                    ),
                    args.output,
                )
        elif args.command == "migrate":
            maybe_write_plan(migrate_claude_plan(Path(args.project)), args.output)
        else:
            path = Path(args.path).resolve()
            validators = {
                "plugin": validate_plugin,
                "skills": validate_skills,
                "catalog": validate_catalog,
                "parity": validate_parity,
                "platform": validate_platform,
            }
            errors = validators[args.validate_command](path)
            emit({"validator": args.validate_command, "path": str(path), "valid": not errors, "errors": errors})
            return 0 if not errors else 1
    except (StudioError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
