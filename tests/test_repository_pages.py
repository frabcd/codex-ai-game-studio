from __future__ import annotations

import html
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from tools.build_pages import (
    SITE_DESCRIPTION,
    SITE_URL,
    build,
    markdown_to_html,
    split_frontmatter,
)


ROOT = Path(__file__).resolve().parents[1]
SITE_BASE = "/codex-ai-game-studio"
HTML_TARGET = re.compile(r"""(?:href|src)=["']([^"']+)["']""")


class PagesBuilderTests(unittest.TestCase):
    def test_markdown_renderer_escapes_source_html(self) -> None:
        rendered = markdown_to_html("# Safe\n\n<script>alert(1)</script>\n")
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_frontmatter_is_metadata_not_page_content(self) -> None:
        metadata, body = split_frontmatter("---\ntitle: Example\npermalink: /example/\n---\n# Body\n")
        self.assertEqual(metadata["title"], "Example")
        self.assertEqual(metadata["permalink"], "/example/")
        self.assertEqual(body, "# Body")

    def test_pages_include_legal_and_support_routes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-pages-") as temporary:
            output_root = Path(temporary).resolve()
            written = build(ROOT, output_root)
            relative = {path.relative_to(output_root).as_posix() for path in written}
            for expected in (
                "index.html",
                "privacy/index.html",
                "terms/index.html",
                "support/index.html",
                "tutorials/index.html",
                "validation/index.html",
                "packs/unity/index.html",
                "packs/img2threejs/index.html",
                "platforms/windows/index.html",
                "platforms/macos/index.html",
                "assets/site.css",
                "sitemap.xml",
                "robots.txt",
                ".nojekyll",
            ):
                self.assertIn(expected, relative)
            home = (output_root / "index.html").read_text(encoding="utf-8")
            self.assertIn(
                'href="/codex-ai-game-studio/platforms/windows/"',
                home,
            )
            self.assertIn(
                'src="/codex-ai-game-studio/assets/branding/hero.png"',
                home,
            )
            pack_index = (
                output_root / "docs" / "packs" / "index" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn(
                'href="/codex-ai-game-studio/packs/img2threejs/"',
                pack_index,
            )

    def test_pages_include_canonical_social_and_structured_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-pages-metadata-") as temporary:
            output_root = Path(temporary).resolve()
            build(ROOT, output_root)
            home = (output_root / "index.html").read_text(encoding="utf-8")
            tutorial = (output_root / "tutorials" / "index.html").read_text(encoding="utf-8")

            self.assertIn(f'<link rel="canonical" href="{SITE_URL}/">', home)
            self.assertIn(
                f'<link rel="canonical" href="{SITE_URL}/tutorials/">',
                tutorial,
            )
            self.assertIn(f'<meta property="og:url" content="{SITE_URL}/">', home)
            self.assertIn(
                f'<meta property="og:image" content="{SITE_URL}/assets/branding/hero.png">',
                home,
            )
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', home)
            self.assertIn(
                '<link rel="icon" type="image/png" '
                'href="/codex-ai-game-studio/assets/branding/icon.png">',
                home,
            )
            self.assertIn(f'<meta name="description" content="{SITE_DESCRIPTION}">', home)

            match = re.search(
                r'<script type="application/ld\+json">(.+)</script>',
                tutorial,
            )
            self.assertIsNotNone(match)
            metadata = json.loads(match.group(1))
            self.assertEqual(metadata["@type"], "SoftwareSourceCode")
            self.assertEqual(
                metadata["codeRepository"],
                "https://github.com/frabcd/codex-ai-game-studio",
            )
            self.assertEqual(metadata["mainEntityOfPage"], f"{SITE_URL}/tutorials/")

    def test_sitemap_and_robots_cover_generated_routes_deterministically(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-pages-discovery-") as temporary:
            output_root = Path(temporary).resolve()
            written = build(ROOT, output_root)
            generated_pages = sorted(
                path.relative_to(output_root).as_posix()
                for path in written
                if path.name == "index.html"
            )
            expected_urls = [
                f"{SITE_URL}/"
                if relative == "index.html"
                else f"{SITE_URL}/{relative.removesuffix('index.html')}"
                for relative in generated_pages
            ]

            sitemap_path = output_root / "sitemap.xml"
            root = ET.fromstring(sitemap_path.read_text(encoding="utf-8"))
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            actual_urls = [
                element.text
                for element in root.findall("sitemap:url/sitemap:loc", namespace)
            ]
            self.assertEqual(sorted(expected_urls), actual_urls)
            self.assertEqual(len(actual_urls), len(set(actual_urls)))

            self.assertEqual(
                "User-agent: *\n"
                "Allow: /codex-ai-game-studio/\n"
                f"Sitemap: {SITE_URL}/sitemap.xml\n",
                (output_root / "robots.txt").read_text(encoding="utf-8"),
            )

    def test_build_content_is_deterministic(self) -> None:
        with (
            tempfile.TemporaryDirectory(prefix="ags-pages-first-") as first,
            tempfile.TemporaryDirectory(prefix="ags-pages-second-") as second,
        ):
            first_root = Path(first).resolve()
            second_root = Path(second).resolve()
            build(ROOT, first_root)
            build(ROOT, second_root)

            def contents(root: Path) -> dict[str, bytes]:
                return {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in sorted(root.rglob("*"))
                    if path.is_file()
                }

            self.assertEqual(contents(first_root), contents(second_root))

    def test_every_generated_internal_link_resolves(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-pages-crawl-") as temporary:
            output_root = Path(temporary).resolve()
            build(ROOT, output_root)
            broken: list[str] = []
            for page_path in sorted(output_root.rglob("*.html")):
                source = page_path.read_text(encoding="utf-8")
                for raw_target in HTML_TARGET.findall(source):
                    target = html.unescape(raw_target)
                    parsed = urlsplit(target)
                    if (
                        parsed.scheme
                        or parsed.netloc
                        or target.startswith(("#", "mailto:", "data:"))
                    ):
                        continue
                    path_text = parsed.path
                    if path_text.startswith(SITE_BASE + "/"):
                        relative_text = path_text[len(SITE_BASE) + 1 :]
                        candidate = output_root / relative_text
                    elif path_text == SITE_BASE:
                        candidate = output_root
                    elif path_text.startswith("/"):
                        broken.append(f"{page_path.relative_to(output_root)} -> {target}")
                        continue
                    else:
                        candidate = page_path.parent / path_text
                    if path_text.endswith("/") or candidate.is_dir():
                        candidate = candidate / "index.html"
                    if not candidate.is_file():
                        broken.append(f"{page_path.relative_to(output_root)} -> {target}")
            self.assertEqual([], broken)


if __name__ == "__main__":
    unittest.main()
