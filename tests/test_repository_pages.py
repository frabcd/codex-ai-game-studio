from __future__ import annotations

import html
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import urlsplit

from tools.build_pages import build, markdown_to_html, split_frontmatter


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
