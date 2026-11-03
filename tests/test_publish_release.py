import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import publish_release as publication
    import version_plan as versions
    import release_policy as policy
finally:
    sys.path.pop(0)


class ReleasePipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.archive = self.root / "dist/ForeverElixirManager-0.5.0.zip"
        self.archive.parent.mkdir()
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("ForeverElixirManager/ForeverElixirManager.toc", "## Version: 0.5.0\n")
            archive.writestr("ForeverElixirManager/ForeverElixirManager.lua", "fixture")
            archive.writestr("ForeverElixirManager/LICENSE", "fixture")
        self.original = self.archive.read_bytes()
        self.calls, self.tagged, self.uploads = [], False, 0
        self.env = {
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": publication.REPOSITORY, "GITHUB_SHA": "a" * 40,
            "GH_TOKEN": "test-gh", "CURSEFORGE_API_TOKEN": "test-cf",
            "CURSEFORGE_PROJECT_ID": "42", "CURSEFORGE_GAME_VERSION_ID": "123",
            "CURSEFORGE_GAME_VERSION_NAME": "1.60.1", "CURSEFORGE_GAME_VERSION_TYPE_ID": "456",
        }
        self.proposal = {"version": "0.5.0", "tag": "v0.5.0", "sha": "a" * 40,
                         "release_type": "alpha", "prerelease": True,
                         "notes": publication.cf.release_notes(
                             "## 0.5.0\n\nReviewed notes\n\n## 0.4.0\n\nOlder notes",
                             "v0.5.0", "v0.4.0")}
        self.addCleanup(patch.stopall)
        patch.object(publication, "ROOT", self.root).start()
        patch.dict(os.environ, self.env, clear=True).start()
        self.planner = patch.object(publication, "release_plan", return_value=self.proposal).start()
        self.github = patch.object(publication, "github", side_effect=self.github_api).start()
        self.gh = patch.object(publication, "gh", side_effect=self.cli).start()
        self.api = patch.object(publication.cf, "api", side_effect=self.curseforge_api).start()
        patch.object(publication.validate, "package", return_value=self.archive).start()
        patch("builtins.print").start()

    def github_api(self, path, payload=None, missing_ok=False):
        self.calls.append(("github", path, payload))
        if payload is not None:
            if self.tagged:
                raise ValueError("duplicate tag")
            self.tagged = True
            self.assertEqual(payload, {"ref": "refs/tags/v0.5.0", "sha": "a" * 40})
            return {"ref": payload["ref"]}
        return {"ref": "existing"} if self.tagged else None

    def cli(self, *args):
        self.calls.append(("gh", *args))
        if args[:2] == ("release", "download"):
            directory = Path(args[args.index("--dir") + 1])
            (directory / self.archive.name).write_bytes(self.original)

    def curseforge_api(self, path, token, body=None, content_type=None):
        self.calls.append(("cf", path))
        if path == "/game/versions":
            return [{"id": 123, "name": "1.60.1", "gameVersionTypeID": 456}]
        self.uploads += 1
        self.assertIn(b'"isMarkedForManualRelease": false', body)
        self.assertIn(b'"displayName": "ForeverElixirManager-v0.5.0"', body)
        self.assertIn(b'"releaseType": "' + self.proposal["release_type"].encode() + b'"', body)
        self.assertIn(self.original, body)
        self.assertIn(json.dumps(self.proposal["notes"]).encode(), body)
        self.assertEqual((self.root / "dist/approved-release-notes.md").read_text(), self.proposal["notes"])
        return {"id": 99}

    def test_channels_and_order_publish_exact_bytes_with_automatic_curseforge_release(self):
        for channel in ("alpha", "beta", "release"):
            with self.subTest(channel=channel):
                self.calls, self.tagged, self.uploads = [], False, 0
                self.proposal.update(release_type=channel, prerelease=channel != "release")
                self.assertEqual(publication.publish("0.5.0", channel, True), 99)
                self.assertEqual(self.uploads, 1)
                create = next(c for c in self.calls if c[:3] == ("gh", "release", "create"))
                self.assertEqual(create[create.index("--title") + 1],
                                 f"ForeverElixirManager-v0.5.0 ({channel.title()})")
                self.assertEqual("--prerelease" in create, channel != "release")
                self.assertEqual("--latest" in create, channel == "release")
                preflight = self.calls.index(("cf", "/game/versions"))
                tag = next(i for i, c in enumerate(self.calls) if c[:2] == ("github", "/git/refs"))
                download = next(i for i, c in enumerate(self.calls) if c[:3] == ("gh", "release", "download"))
                self.assertLess(preflight, tag)
                self.assertLess(tag, download)
                self.assertLess(download, self.calls.index(("cf", "/projects/42/upload-file")))

    def test_no_approval_or_wrong_context_never_calls_network(self):
        with self.assertRaises(ValueError):
            publication.publish("0.5.0", "alpha")
        for key, value in [("GITHUB_EVENT_NAME", "push"), ("GITHUB_REF", "refs/heads/feature"),
                           ("GITHUB_REPOSITORY", "someone/fork"), ("GITHUB_SHA", "b" * 40)]:
            with patch.dict(os.environ, {key: value}), self.assertRaises(ValueError):
                publication.publish("0.5.0", "alpha", True)
        self.github.assert_not_called()
        self.api.assert_not_called()

    def test_existing_tag_or_release_stops_before_upload(self):
        self.tagged = True
        with self.assertRaises(ValueError):
            publication.publish("0.5.0", "alpha", True)
        self.api.assert_not_called()
        self.gh.assert_not_called()
        self.github.side_effect = [None, {"id": 12}]
        with self.assertRaises(ValueError):
            publication.publish("0.5.0", "alpha", True)
        self.api.assert_not_called()

    def test_catalog_mismatch_stops_before_tagging(self):
        with patch.dict(os.environ, {"CURSEFORGE_GAME_VERSION_TYPE_ID": "999"}):
            with self.assertRaises(ValueError):
                publication.publish("0.5.0", "alpha", True)
        self.assertFalse(self.tagged)
        self.gh.assert_not_called()

    def test_artifact_and_download_mismatches_stop_publication(self):
        different = self.root / "different.zip"
        different.write_bytes(b"different")
        with patch.object(publication.validate, "package", return_value=different):
            with self.assertRaisesRegex(ValueError, "artifact differs"):
                publication.publish("0.5.0", "alpha", True)
        self.github.assert_not_called()
        def bad_download(*args):
            self.cli(*args)
            if args[:2] == ("release", "download"):
                (Path(args[-1]) / self.archive.name).write_bytes(b"changed")
        self.gh.side_effect = bad_download
        with self.assertRaisesRegex(ValueError, "Published GitHub ZIP differs"):
            publication.publish("0.5.0", "alpha", True)
        self.assertEqual(self.uploads, 0)

    def test_uncertain_upload_is_not_retried_and_rerun_is_blocked(self):
        def timeout(path, token, body=None, content_type=None):
            result = self.curseforge_api(path, token, body, content_type)
            if body is not None:
                raise TimeoutError("response lost")
            return result
        self.api.side_effect = timeout
        with self.assertRaises(TimeoutError):
            publication.publish("0.5.0", "alpha", True)
        self.assertEqual(self.uploads, 1)
        with self.assertRaises(ValueError):
            publication.publish("0.5.0", "alpha", True)
        self.assertEqual(self.uploads, 1)

    def test_github_failure_never_uploads(self):
        self.gh.side_effect = ValueError("GitHub unavailable")
        with self.assertRaises(ValueError):
            publication.publish("0.5.0", "alpha", True)
        self.assertTrue(self.tagged)
        self.assertEqual(self.uploads, 0)


class ReleasePlanTests(unittest.TestCase):
    def test_real_history_blocks_management_bumps_but_accepts_prepared_addon_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", directory, *args], check=True, capture_output=True).stdout
            def commit():
                git("add", ".")
                git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
            git("init", "-b", "main")
            (root / versions.TOC).parent.mkdir()
            (root / versions.TOC).write_text("## Version: 0.4.0\n")
            (root / "LICENSE").write_text("license")
            (root / "ForeverElixirManager/ForeverElixirManager.lua").write_text("original")
            (root / "CHANGELOG.md").write_text("# Release notes\n\n## 0.4.0\n\nOld notes\n")
            commit()
            git("tag", "v0.4.0")
            (root / versions.TOC).write_text("## Version: 0.5.0\n")
            (root / "CHANGELOG.md").write_text("# Release notes\n\n## 0.5.0\n\nNew notes\n\n## 0.4.0\n\nOld\n")
            (root / "README.md").write_text("management only")
            (root / "release-plan.json").write_text(json.dumps({"base_tag": "v0.4.0", "version": "0.5.0",
                "bump": "minor", "reason": "Reviewed feature", "content_sha256": "pending"}))
            commit()
            with patch.object(publication, "ROOT", root), patch.object(publication, "git", side_effect=git), \
                    patch.object(versions, "git", side_effect=git), patch.object(policy, "git", side_effect=git), \
                    patch.object(policy, "ROOT", root), patch.object(publication.validate, "metadata", return_value="0.5.0"):
                with self.assertRaisesRegex(ValueError, "changed shipped content"):
                    publication.release_plan("0.5.0", "alpha")
                (root / "ForeverElixirManager/ForeverElixirManager.lua").write_text("new behavior")
                commit()
                decision_path = root / "release-plan.json"
                decision = json.loads(decision_path.read_text())
                decision["content_sha256"] = versions.shipped_digest(versions.snapshot("HEAD")[2])
                decision_path.write_text(json.dumps(decision))
                commit()
                result = publication.release_plan("0.5.0", "beta")
                self.assertTrue(result["prerelease"])
                self.assertTrue(result["notes"].endswith("New notes"))
                self.assertNotIn("Old", result["notes"])
                self.assertIn("[0.5.0]", result["notes"])
                self.assertIn("/releases/tag/v0.5.0", result["notes"])
                self.assertIn("/compare/v0.4.0...v0.5.0", result["notes"])
                self.assertNotIn("Previous Releases", result["notes"])
                for version in ("v0.5.0", "0.6.0", "0.5.0;echo", "00.5.0"):
                    with self.assertRaises(ValueError):
                        publication.release_plan(version, "alpha")
                git("tag", "v0.5.0")
                with self.assertRaisesRegex(ValueError, "already tagged"):
                    publication.release_plan("0.5.0", "alpha")

    def test_github_only_treats_404_as_missing(self):
        with patch.dict(os.environ, {"GH_TOKEN": "fixture"}), \
                patch.object(publication.urllib.request, "build_opener") as opener:
            for status in (401, 403, 500):
                opener.return_value.open.side_effect = urllib.error.HTTPError("url", status, "", {}, None)
                with self.assertRaises(ValueError):
                    publication.github("/releases/tags/v0.5.0", missing_ok=True)
            opener.return_value.open.side_effect = urllib.error.HTTPError("url", 404, "", {}, None)
            self.assertIsNone(publication.github("/releases/tags/v0.5.0", missing_ok=True))


if __name__ == "__main__":
    unittest.main()
