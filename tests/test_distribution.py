import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


cf = module("curseforge")
validation = module("validate")


class DistributionTests(unittest.TestCase):
    def test_invalid_or_mismatched_tag_is_rejected_before_packaging(self):
        for tag in ["v99.0.0", "v0.3.0-extra", "v00.3.0", "main", "v0.3.0/path"]:
            with patch("sys.argv", ["validate.py", "--tag", tag]), patch.object(validation, "package") as package:
                with self.assertRaises(AssertionError):
                    validation.main()
                package.assert_not_called()

    def test_archive_allowlist_and_reproducibility(self):
        version = validation.metadata()
        archive = validation.package(version)
        before = archive.read_bytes()
        self.assertEqual(before, validation.package(version).read_bytes())
        cf.validate_archive(archive, "v" + version)
        with self.assertRaises(ValueError):
            cf.validate_archive(archive, "v99.0.0")

    def test_unexpected_archive_member_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../credentials", "fixture")
            with self.assertRaises(ValueError):
                cf.validate_archive(path, "v0.3.0")

    def test_no_approval_means_no_network(self):
        with patch.object(cf, "api") as api:
            with self.assertRaisesRegex(ValueError, "explicit"):
                cf.main([])
            api.assert_not_called()

    def test_no_token_means_no_network(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(cf, "api") as api:
            with self.assertRaisesRegex(ValueError, "secret"):
                cf.main(["--approve-upload"])
            api.assert_not_called()

    def test_live_catalog_identity_and_metadata(self):
        rows = [{"id": 123, "name": "test-version", "gameVersionTypeID": 456}]
        result = cf.upload_metadata(rows, "123", "test-version", "456", "v0.3.0", "alpha", "Changes")
        self.assertEqual(result["gameVersions"], [123])
        self.assertTrue(result["isMarkedForManualRelease"])
        self.assertEqual(result["changelogType"], "markdown")
        for version, name, kind, tag in [
            ("999", "test-version", "456", "v0.3.0"),
            ("123", "wrong", "456", "v0.3.0"),
            ("123", "test-version", "999", "v0.3.0"),
            ("123", "test-version", "456", "v0.3.0/other"),
        ]:
            with self.assertRaises(ValueError):
                cf.upload_metadata(rows, version, name, kind, tag, "alpha", "Changes")

    def test_multipart_contains_actual_zip_and_metadata(self):
        path = validation.package(validation.metadata())
        body, content_type = cf.multipart({"releaseType": "alpha"}, path)
        self.assertIn(b'name="metadata"', body)
        self.assertIn(b'name="file"', body)
        self.assertIn(path.read_bytes(), body)
        self.assertIn(b'"releaseType": "alpha"', body)
        self.assertIn("boundary=fem-", content_type)

    def test_approved_upload_contract_with_mocked_network(self):
        path = validation.package(validation.metadata())
        config = {
            "CURSEFORGE_API_TOKEN": "test-only",
            "CURSEFORGE_PROJECT_ID": "42",
            "CURSEFORGE_GAME_VERSION_ID": "123",
            "CURSEFORGE_GAME_VERSION_NAME": "test-version",
            "CURSEFORGE_GAME_VERSION_TYPE_ID": "456",
        }
        rows = [{"id": 123, "name": "test-version", "gameVersionTypeID": 456}]
        with patch.dict(os.environ, config), patch.object(cf, "api", side_effect=[rows, {"id": 99}]) as api, patch("builtins.print"):
            cf.main(["--approve-upload", "--tag", "v0.3.0", "--archive", str(path),
                     "--changelog", str(ROOT / "CHANGELOG.md")])
            self.assertEqual(api.call_count, 2)
            self.assertEqual(api.call_args.args[:2], ("/projects/42/upload-file", "test-only"))

    def test_token_header_and_no_redirect_policy(self):
        with patch.object(cf.urllib.request, "build_opener") as build:
            build.return_value.open.return_value.__enter__.return_value.read.return_value = b'{"id":99}'
            self.assertEqual(cf.api("/game/versions", "test-only"), {"id":99})
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header("X-api-token"), "test-only")
            self.assertNotIn("test-only", request.full_url)
        with self.assertRaises(ValueError):
            cf.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")


if __name__ == "__main__":
    unittest.main()
