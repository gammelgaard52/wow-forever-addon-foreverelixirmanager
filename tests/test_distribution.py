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
    def test_release_notes_only_include_selected_version_with_project_links(self):
        changelog = "# Release notes\n\n## 0.6.0\n\nFuture\n\n## 0.5.0\n\n- Current fix\n\n### Details\nKeep this.\n\n## 0.4.0\n\nOlder\n"
        for source in (changelog, changelog.replace("\n", "\r\n")):
            notes = cf.release_notes(source, "v0.5.0", "v0.4.0")
            self.assertTrue(notes.startswith(f"## [0.5.0]({cf.REPOSITORY_URL}/releases/tag/v0.5.0)"))
            self.assertIn(f"[Full Changelog]({cf.REPOSITORY_URL}/compare/v0.4.0...v0.5.0)", notes)
            self.assertNotIn("Previous Releases", notes)
            self.assertIn("- Current fix", notes)
            self.assertIn("v0.4.0...v0.5.0)\n\n- Current fix", notes)
            self.assertIn("### Details", notes)
            self.assertNotIn("Future", notes)
            self.assertNotIn("Older", notes)

    def test_release_notes_without_previous_tag_link_to_tagged_changelog(self):
        notes = cf.release_notes("## 0.5.0\n\n- Fix", "v0.5.0")
        self.assertIn(f"[Full Changelog]({cf.REPOSITORY_URL}/blob/v0.5.0/CHANGELOG.md)", notes)
        self.assertNotIn("/compare/", notes)

    def test_release_notes_reject_missing_empty_duplicate_or_invalid_versions(self):
        for source in ("Notes without version", "## 0.4.0\nOlder", "## 0.5.0\n\n## 0.4.0\nOlder",
                       "## 0.5.0\nOne\n## 0.5.0\nTwo"):
            with self.assertRaises(ValueError):
                cf.release_notes(source, "v0.5.0")
        for tag, previous in (("v00.5.0", None), ("v0.5.0/path", None),
                              ("v0.5.0", "main"), ("v0.5.0", "v0.5.0"), ("v0.5.0", "v0.6.0")):
            with self.assertRaises(ValueError):
                cf.release_notes("## 0.5.0\nNotes", tag, previous)

    def test_connection_check_only_reads_catalog(self):
        rows = [{"id": 123, "name": "1.60.1", "gameVersionTypeID": 456}]
        with patch.dict(os.environ, {"CURSEFORGE_API_TOKEN": "test-only"}), patch.object(cf, "api", return_value=rows) as api, patch("builtins.print"):
            cf.main(["--check-version", "1.60.1"])
            api.assert_called_once_with("/game/versions", "test-only")
        self.assertEqual(cf.check_version(rows, "1.60.1"), {
            "CURSEFORGE_GAME_VERSION_ID": 123, "CURSEFORGE_GAME_VERSION_NAME": "1.60.1",
            "CURSEFORGE_GAME_VERSION_TYPE_ID": 456,
        })

    def test_connection_check_rejects_missing_ambiguous_or_invalid_version(self):
        row = {"id": 123, "name": "1.60.1", "gameVersionTypeID": 456}
        for rows in [[], [row, row], ["bad"], [{**row, "id": -1}], [{**row, "gameVersionTypeID": None}]]:
            with self.assertRaises(ValueError):
                cf.check_version(rows, "1.60.1")

    def test_connection_check_cannot_be_combined_with_upload(self):
        with patch.object(cf, "api") as api, patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                cf.main(["--check-version", "1.60.1", "--approve-upload"])
            api.assert_not_called()

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

    def test_automatic_publication_requires_explicit_selection(self):
        rows = [{"id": 123, "name": "test-version", "gameVersionTypeID": 456}]
        for channel in ("alpha", "beta", "release"):
            held = cf.upload_metadata(rows, "123", "test-version", "456", "v0.5.0", channel, "Notes")
            automatic = cf.upload_metadata(rows, "123", "test-version", "456", "v0.5.0", channel,
                                           "Notes", manual_release=False)
            self.assertTrue(held["isMarkedForManualRelease"])
            self.assertFalse(automatic["isMarkedForManualRelease"])
            self.assertEqual(automatic["releaseType"], channel)

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
            cf.main(["--approve-upload", "--tag", "v" + validation.metadata(), "--archive", str(path),
                     "--changelog", str(ROOT / "CHANGELOG.md")])
            self.assertEqual(api.call_count, 2)
            self.assertEqual(api.call_args.args[:2], ("/projects/42/upload-file", "test-only"))
            body = api.call_args.args[2]
            self.assertIn(b"[Full Changelog]", body)
            self.assertIn(f"/releases/tag/v{validation.metadata()}".encode(), body)
            self.assertNotIn(b"[Previous Releases]", body)
            self.assertNotIn(b"## 0.4.0", body)

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
