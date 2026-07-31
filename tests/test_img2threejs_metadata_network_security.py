from __future__ import annotations

import importlib.util
import ipaddress
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "plugins"
    / "ai-game-studio-img2threejs"
    / "skills"
    / "img2threejs"
    / "forge"
    / "stage1_intake"
    / "fetch_cs2_metadata.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("ags_fetch_cs2_metadata", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload: bytes, *, url: str, content_length: str | None = None) -> None:
        self.payload = payload
        self.url = url
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = content_length
        self.read_limit: int | None = None

    def read(self, limit: int = -1) -> bytes:
        self.read_limit = limit
        return self.payload if limit < 0 else self.payload[:limit]

    def geturl(self) -> str:
        return self.url


class Img2ThreeJsMetadataNetworkSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.public_address = frozenset({ipaddress.ip_address("93.184.216.34")})

    def validate(self, url: str, *, confirmed: tuple[str, ...] = ()) -> str:
        with mock.patch.object(self.module, "resolved_addresses", return_value=self.public_address):
            return self.module.validate_https_url(
                url,
                allowed_hosts=self.module.DEFAULT_INDEX_HOSTS,
                confirmed_hosts=self.module.normalize_confirmed_hosts(confirmed),
                purpose="test index",
            )

    def test_url_policy_blocks_ssrf_schemes_local_hosts_and_unapproved_hosts(self) -> None:
        self.assertEqual(
            "https://cdn.jsdelivr.net/gh/ByMykel/CSGO-API@main/public/api/en/skins.json",
            self.validate(
                "https://cdn.jsdelivr.net/gh/ByMykel/CSGO-API@main/public/api/en/skins.json"
            ),
        )
        for url in (
            "file:///etc/passwd",
            "http://cdn.jsdelivr.net/index.json",
            "https://localhost/index.json",
            "https://127.0.0.1/index.json",
            "https://169.254.169.254/latest/meta-data",
            "https://10.10.10.10/index.json",
            "https://cdn.jsdelivr.net:8443/index.json",
            "https://user:password@cdn.jsdelivr.net/index.json",
        ):
            with self.assertRaises(self.module.NetworkPolicyError, msg=url):
                self.validate(url)
        with self.assertRaisesRegex(self.module.NetworkPolicyError, "not approved"):
            self.validate("https://downloads.example.com/index.json")

    def test_confirmed_host_override_never_bypasses_public_address_requirement(self) -> None:
        self.assertEqual(
            "https://downloads.example.com/index.json",
            self.validate(
                "https://downloads.example.com/index.json",
                confirmed=("downloads.example.com",),
            ),
        )
        with mock.patch.object(
            self.module,
            "resolved_addresses",
            return_value=frozenset({ipaddress.ip_address("192.168.1.20")}),
        ):
            with self.assertRaisesRegex(self.module.NetworkPolicyError, "non-public"):
                self.module.validate_https_url(
                    "https://downloads.example.com/index.json",
                    allowed_hosts=self.module.DEFAULT_INDEX_HOSTS,
                    confirmed_hosts=frozenset({"downloads.example.com"}),
                    purpose="test index",
                )

    def test_redirects_revalidate_destinations_and_have_a_hard_limit(self) -> None:
        handler = self.module.SafeRedirectHandler(
            allowed_hosts=self.module.DEFAULT_INDEX_HOSTS,
            confirmed_hosts=frozenset(),
            purpose="test index",
        )
        request = urllib.request.Request("https://cdn.jsdelivr.net/index.json")
        with self.assertRaises(self.module.NetworkPolicyError):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://127.0.0.1/private",
            )

        handler = self.module.SafeRedirectHandler(
            allowed_hosts=self.module.DEFAULT_INDEX_HOSTS,
            confirmed_hosts=frozenset(),
            purpose="test index",
        )
        with mock.patch.object(self.module, "resolved_addresses", return_value=self.public_address):
            for _ in range(self.module.MAX_REDIRECTS):
                redirected = handler.redirect_request(
                    request,
                    None,
                    302,
                    "Found",
                    {},
                    "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/index.json",
                )
                self.assertIsNotNone(redirected)
            with self.assertRaisesRegex(self.module.NetworkPolicyError, "exceeded"):
                handler.redirect_request(
                    request,
                    None,
                    302,
                    "Found",
                    {},
                    "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/index.json",
                )

    def test_bounded_reads_reject_declared_and_streamed_oversize_payloads(self) -> None:
        declared = FakeResponse(b"small", url="https://cdn.jsdelivr.net/index.json", content_length="11")
        with self.assertRaisesRegex(self.module.NetworkPolicyError, "exceeds"):
            self.module.read_bounded(declared, maximum_bytes=10, purpose="test")
        self.assertIsNone(declared.read_limit)

        streamed = FakeResponse(b"x" * 11, url="https://cdn.jsdelivr.net/index.json")
        with self.assertRaisesRegex(self.module.NetworkPolicyError, "exceeds"):
            self.module.read_bounded(streamed, maximum_bytes=10, purpose="test")
        self.assertEqual(streamed.read_limit, 11)

        accepted = FakeResponse(b"x" * 10, url="https://cdn.jsdelivr.net/index.json")
        self.assertEqual(
            b"x" * 10,
            self.module.read_bounded(accepted, maximum_bytes=10, purpose="test"),
        )

    def test_paint_index_is_bounded_numeric_and_output_stays_contained(self) -> None:
        self.assertEqual(419, self.module.parse_paint_index("419"))
        self.assertEqual(0, self.module.parse_paint_index(0))
        for value in (True, -1, self.module.MAX_PAINT_INDEX + 1, "../escape", "00419", None):
            with self.assertRaises(ValueError, msg=repr(value)):
                self.module.parse_paint_index(value)

        with tempfile.TemporaryDirectory(prefix="ags-metadata-target-") as temporary:
            root = Path(temporary).resolve()
            target = self.module.contained_image_target(root, 419)
            self.assertEqual(root / "419.png", target)
            self.assertEqual(root, target.parent)

    def test_normal_api_and_steam_image_hosts_remain_approved(self) -> None:
        record = {
            "name": "Karambit | Doppler",
            "weapon": {"name": "Karambit"},
            "paint_index": "419",
            "image": "https://community.akamai.steamstatic.com/economy/image/example",
        }
        metadata = self.module.to_metadata(record, "local-fixture")
        self.assertEqual(419, metadata["paintIndex"])
        with mock.patch.object(self.module, "resolved_addresses", return_value=self.public_address):
            self.module.validate_https_url(
                metadata["imageUrl"],
                allowed_hosts=self.module.DEFAULT_IMAGE_HOSTS,
                confirmed_hosts=frozenset(),
                purpose="skin image",
            )

    def test_existing_download_is_preserved_without_explicit_force(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-metadata-existing-") as temporary:
            target = Path(temporary) / "419.png"
            target.write_bytes(b"preserve")
            with mock.patch.object(self.module, "fetch_url_bytes") as fetch:
                with self.assertRaisesRegex(ValueError, "force-image"):
                    self.module.download_cdn_image(
                        "https://cdn.steamstatic.com/example.png",
                        Path(temporary),
                        419,
                    )
            fetch.assert_not_called()
            self.assertEqual(target.read_bytes(), b"preserve")


if __name__ == "__main__":
    unittest.main()
