#!/usr/bin/env python3
"""Build a dependency-free static documentation site for GitHub Pages."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import shutil
from urllib.parse import quote


SITE_BASE = "/codex-ai-game-studio"
GITHUB_SOURCE = "https://github.com/frabcd/codex-ai-game-studio"
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
IMAGE_LINK = re.compile(r"\[(!\[[^\]]*\]\([^)]+\))\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"`([^`]+)`")


def split_frontmatter(source: str) -> tuple[dict[str, str], str]:
    """Return simple scalar frontmatter and the Markdown body.

    The checked-in documentation uses only scalar keys for routing metadata.
    Keeping this parser deliberately small avoids adding a YAML dependency to
    the deterministic Pages build.
    """

    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, source
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, source
    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, "\n".join(lines[closing + 1 :])


def frontmatter_route(source_path: Path, fallback: str) -> str:
    metadata, _ = split_frontmatter(source_path.read_text(encoding="utf-8"))
    permalink = metadata.get("permalink")
    if not permalink:
        return fallback
    if not re.fullmatch(r"/?[A-Za-z0-9][A-Za-z0-9/_-]*/?", permalink):
        raise ValueError(f"unsafe documentation permalink in {source_path}: {permalink}")
    route = permalink.strip("/")
    if any(part in (".", "..") for part in route.split("/")):
        raise ValueError(f"unsafe documentation permalink in {source_path}: {permalink}")
    return route


def inline(value: str) -> str:
    escaped = html.escape(value, quote=True)
    escaped = INLINE_CODE.sub(lambda match: f"<code>{match.group(1)}</code>", escaped)

    def image_link(match: re.Match[str]) -> str:
        label, target = match.groups()
        decoded = html.unescape(target)
        if decoded.startswith(("https://", "http://", "/")) or not re.match(
            r"^[A-Za-z][A-Za-z0-9+.-]*:", decoded
        ):
            return (
                f'<img src="{html.escape(decoded, quote=True)}" '
                f'alt="{html.escape(html.unescape(label), quote=True)}">'
            )
        return html.escape(html.unescape(label))

    def link(match: re.Match[str]) -> str:
        label, target = match.groups()
        decoded = html.unescape(target)
        if decoded.startswith(("https://", "http://", "#", "/")) or not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", decoded):
            href = html.escape(decoded, quote=True)
            return f'<a href="{href}">{label}</a>'
        return label

    return LINK.sub(link, IMAGE.sub(image_link, escaped))


def rewrite_local_targets(
    source: str,
    *,
    source_path: Path,
    root: Path,
    routes: dict[Path, str],
) -> str:
    """Map checked-in Markdown links to their generated Pages routes."""

    def rewrite(match: re.Match[str]) -> str:
        prefix = "!" if match.group(0).startswith("!") else ""
        label, target = match.groups()
        if target.startswith(("https://", "http://", "mailto:", "#")):
            return match.group(0)
        if target.startswith("/"):
            mapped = target if target.startswith(SITE_BASE + "/") else SITE_BASE + target
            return f"{prefix}[{label}]({mapped})"
        path_text, marker, fragment = target.partition("#")
        repository_target = (source_path.parent / path_text).resolve()
        candidate = repository_target / "index.md" if repository_target.is_dir() else repository_target
        route = routes.get(candidate)
        if route is not None:
            href = f"{SITE_BASE}/{route}/" if route else f"{SITE_BASE}/"
            if marker:
                href += f"#{fragment}"
            return f"{prefix}[{label}]({href})"
        for assets_root in ((root / "assets").resolve(), (root / "docs" / "assets").resolve()):
            try:
                asset_relative = candidate.relative_to(assets_root)
            except ValueError:
                continue
            if candidate.is_file():
                href = f"{SITE_BASE}/assets/{asset_relative.as_posix()}"
                return f"{prefix}[{label}]({href})"
        try:
            repository_relative = repository_target.relative_to(root.resolve())
        except ValueError:
            return match.group(0)
        if repository_target.exists():
            source_kind = "tree" if repository_target.is_dir() else "blob"
            href = (
                f"{GITHUB_SOURCE}/{source_kind}/main/"
                f"{quote(repository_relative.as_posix(), safe='/')}"
            )
            if marker:
                href += f"#{fragment}"
            return f"{prefix}[{label}]({href})"
        return match.group(0)

    source = IMAGE_LINK.sub(rewrite, source)
    return IMAGE.sub(rewrite, LINK.sub(rewrite, source))


def markdown_to_html(source: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            title = heading.group(2).strip(" #")
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            output.append(f'<h{level} id="{slug}">{inline(title)}</h{level}>')
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet or ordered:
            flush_paragraph()
            kind = "ul" if bullet else "ol"
            if list_kind != kind:
                close_list()
                output.append(f"<{kind}>")
                list_kind = kind
            output.append(f"<li>{inline((bullet or ordered).group(1))}</li>")
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            output.append(f"<blockquote>{inline(stripped.lstrip('> '))}</blockquote>")
            continue
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        paragraph.append(stripped)
    if in_code:
        output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    flush_paragraph()
    close_list()
    return "\n".join(output)


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Codex AI Game Studio documentation">
  <title>{html.escape(title)} · Codex AI Game Studio</title>
  <link rel="stylesheet" href="/codex-ai-game-studio/assets/site.css">
</head>
<body>
  <header><a class="brand" href="/codex-ai-game-studio/">Codex AI Game Studio</a>
    <nav aria-label="Primary"><a href="/codex-ai-game-studio/tutorials/">Tutorials</a><a href="/codex-ai-game-studio/validation/">Validation</a><a href="/codex-ai-game-studio/privacy/">Privacy</a><a href="/codex-ai-game-studio/support/">Support</a></nav>
  </header>
  <main>{body}</main>
  <footer>MIT licensed · No hosted backend in the core plugin · <a href="https://github.com/frabcd/codex-ai-game-studio">GitHub</a></footer>
</body>
</html>
"""


def title_from(source: str, fallback: str) -> str:
    for line in source.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def write_page(
    output: Path,
    route: str,
    source_path: Path,
    *,
    root: Path,
    routes: dict[Path, str],
) -> None:
    source = source_path.read_text(encoding="utf-8")
    metadata, body = split_frontmatter(source)
    body = rewrite_local_targets(
        body,
        source_path=source_path,
        root=root,
        routes=routes,
    )
    target = output / route / "index.html" if route else output / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    title = metadata.get("title") or title_from(body, source_path.stem)
    target.write_text(page(title, markdown_to_html(body)), encoding="utf-8", newline="\n")


def build(root: Path, output: Path) -> list[Path]:
    root = root.resolve()
    output = output.resolve()
    def choose(*paths: str) -> Path:
        candidates = [root / value for value in paths]
        return next((path for path in candidates if path.is_file()), candidates[0])

    required = {
        "": root / "README.md",
        "tutorials": root / "docs" / "TUTORIALS.md",
        "validation": root / "docs" / "VALIDATION.md",
        "privacy": choose("docs/PRIVACY.md", "docs/privacy/index.md"),
        "terms": choose("docs/TERMS.md", "docs/terms/index.md"),
        "support": choose("SUPPORT.md", "docs/support/index.md"),
        "security": root / "SECURITY.md",
        "contributing": root / "CONTRIBUTING.md",
    }
    missing = [str(path.relative_to(root)) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("required Pages sources are missing: " + ", ".join(missing))
    if output == root or output in root.parents:
        raise ValueError("output must not contain or replace the repository root")
    output.mkdir(parents=True, exist_ok=True)
    docs_root = root / "docs"
    routed_sources = {path.resolve() for path in required.values()}
    route_aliases = {
        "docs/PRIVACY.md": "privacy",
        "docs/privacy/index.md": "privacy",
        "docs/TERMS.md": "terms",
        "docs/terms/index.md": "terms",
        "SUPPORT.md": "support",
        "docs/support/index.md": "support",
    }
    for alias in route_aliases:
        candidate = root / alias
        if candidate.is_file():
            routed_sources.add(candidate.resolve())
    pages = list(required.items())
    for source in sorted(docs_root.rglob("*.md")):
        if source.resolve() in routed_sources:
            continue
        fallback = (Path("docs") / source.relative_to(docs_root).with_suffix("")).as_posix().lower()
        route = frontmatter_route(source, fallback)
        pages.append((route, source))
    routes = {source.resolve(): route for route, source in pages}
    if len(routes) != len(pages) or len(set(routes.values())) != len(pages):
        raise ValueError("documentation sources and routes must be unique")
    for alias, route in route_aliases.items():
        candidate = (root / alias).resolve()
        if candidate.is_file():
            routes[candidate] = route

    written: list[Path] = []
    for route, source in pages:
        write_page(output, route, source, root=root, routes=routes)
        written.append(output / route / "index.html")

    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    css = """:root{color-scheme:dark;--bg:#07111d;--panel:#0e2132;--text:#eaf7ff;--muted:#9fc2d8;--accent:#08c7f7;--accent2:#8a65ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,#123754,var(--bg) 35rem);color:var(--text);font:16px/1.65 system-ui,sans-serif}header,main,footer{max-width:1080px;margin:auto;padding:1.25rem}header{display:flex;gap:1rem;align-items:center;justify-content:space-between}.brand{font-weight:800;color:var(--text);text-decoration:none}nav{display:flex;gap:1rem;flex-wrap:wrap}a{color:var(--accent)}main{background:color-mix(in srgb,var(--panel) 86%,transparent);border:1px solid #24455d;border-radius:18px;margin-top:1rem;padding:clamp(1.2rem,4vw,3rem);box-shadow:0 24px 80px #0008}h1,h2,h3{line-height:1.2}h1{font-size:clamp(2rem,6vw,4.2rem);background:linear-gradient(90deg,var(--accent),var(--accent2));color:transparent;background-clip:text}pre{overflow:auto;padding:1rem;border-radius:10px;background:#02070d;border:1px solid #24455d}code{font-family:ui-monospace,monospace}blockquote{border-left:4px solid var(--accent2);margin-left:0;padding-left:1rem;color:var(--muted)}footer{color:var(--muted);font-size:.9rem}@media(max-width:700px){header{align-items:flex-start;flex-direction:column}}"""
    (assets / "site.css").write_text(css + "\n", encoding="utf-8", newline="\n")
    written.append(assets / "site.css")
    for source_assets in (root / "assets", docs_root / "assets"):
        if source_assets.is_dir():
            for source in source_assets.rglob("*"):
                if source.is_file():
                    relative = source.relative_to(source_assets)
                    target = assets / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    written.append(target)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    written.append(output / ".nojekyll")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("_site"))
    args = parser.parse_args()
    written = build(args.root, args.output)
    print(f"Built {len(written)} Pages files in {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
