import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import release_policy as policy
    import version_plan as versions
finally:
    sys.path.pop(0)


class SemanticPolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "-b", "main")
        (self.root / versions.TOC).parent.mkdir()
        self.lua = self.root / "ForeverElixirManager/ForeverElixirManager.lua"
        self.lua.write_text("original")
        (self.root / "LICENSE").write_text("license")
        (self.root / versions.TOC).write_text("## Version: 0.4.0\n")
        self.commit()
        self.git("tag", "v0.4.0")
        self.lua.write_text("feature")
        self.decision()
        self.commit()
        for mocker in (patch.object(policy, "ROOT", self.root),
                       patch.object(policy, "git", side_effect=self.git),
                       patch.object(versions, "git", side_effect=self.git),
                       patch.object(policy.validate, "metadata", side_effect=self.version)):
            mocker.start()
            self.addCleanup(mocker.stop)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True).stdout

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "fixture")

    def version(self):
        return (self.root / versions.TOC).read_text().split(": ")[1].strip()

    def decision(self, version="0.5.0", bump="minor", reason="Reviewed feature", base="v0.4.0"):
        (self.root / versions.TOC).write_text("## Version: " + version + "\n")
        files = {name: (self.root / name).read_bytes() for name in
                 (versions.TOC, "ForeverElixirManager/ForeverElixirManager.lua", "LICENSE")}
        files[versions.TOC] = versions.VERSION.sub(b"## Version: <version>", files[versions.TOC])
        (self.root / "release-plan.json").write_text(json.dumps(
            {"base_tag": base, "version": version, "bump": bump, "reason": reason,
             "content_sha256": versions.shipped_digest(files)}))

    def test_additional_unreleased_code_requires_new_agent_review(self):
        self.lua.write_text("another feature after the previous review")
        self.commit()
        with self.assertRaisesRegex(ValueError, "agent-reviewed decision"):
            policy.check_policy()
        self.decision(reason="Reviewed both compatible features together")
        self.commit()
        self.assertEqual(policy.check_policy()["version"], "0.5.0")

    def test_exact_patch_minor_and_major_increments_pass(self):
        for version, bump in (("0.4.1", "patch"), ("0.5.0", "minor"), ("1.0.0", "major")):
            self.decision(version, bump)
            self.commit()
            self.assertEqual(policy.check_policy()["version"], version)

    def test_skips_regressions_and_wrong_increment_fail(self):
        for version, bump in (("0.4.2", "patch"), ("0.6.0", "minor"), ("1.1.0", "major"),
                              ("0.3.0", "minor"), ("0.5.0", "patch")):
            self.decision(version, bump)
            self.commit()
            with self.assertRaisesRegex(ValueError, "SemVer decision requires exactly"):
                policy.check_policy()

    def test_management_only_bump_is_rejected(self):
        self.lua.write_text("original")
        (self.root / "README.md").write_text("management")
        self.commit()
        with self.assertRaisesRegex(ValueError, "changed shipped content"):
            policy.check_policy()

    def prepare_version_only(self, approval="Owner requests version 0.5.1 for corrected release names"):
        self.git("tag", "v0.5.0")
        self.decision("0.5.1", "patch", "Correct release names", base="v0.5.0")
        path = self.root / "release-plan.json"
        decision = json.loads(path.read_text())
        decision["version_only_approval"] = approval
        path.write_text(json.dumps(decision))
        self.commit()

    def test_owner_requested_patch_passes_before_and_after_tagging(self):
        self.prepare_version_only()
        self.assertEqual(policy.check_policy()["version"], "0.5.1")
        self.git("tag", "v0.5.1")
        (self.root / "README.md").write_text("management")
        self.commit()
        self.assertEqual(policy.check_policy()["version"], "0.5.1")
        self.lua.write_text("unreviewed change")
        self.commit()
        with self.assertRaisesRegex(ValueError, "unchanged addon content"):
            policy.check_policy()

    def test_version_only_exception_requires_request_and_patch_increment(self):
        self.prepare_version_only()
        path = self.root / "release-plan.json"
        original = json.loads(path.read_text())
        for approval in ("", "  ", True, None):
            with self.subTest(approval=approval):
                path.write_text(json.dumps({**original, "version_only_approval": approval}))
                self.commit()
                with self.assertRaisesRegex(ValueError, "documented request"):
                    policy.check_policy()
        for version, bump in (("0.6.0", "minor"), ("1.0.0", "major")):
            path.write_text(json.dumps({**original, "version": version, "bump": bump}))
            (self.root / versions.TOC).write_text("## Version: " + version + "\n")
            self.commit()
            with self.assertRaisesRegex(ValueError, "patch increment"):
                policy.check_policy()

    def test_version_only_exception_remains_bound_to_content_digest(self):
        self.prepare_version_only()
        path = self.root / "release-plan.json"
        decision = json.loads(path.read_text())
        decision["content_sha256"] = "unreviewed"
        path.write_text(json.dumps(decision))
        self.commit()
        with self.assertRaisesRegex(ValueError, "agent-reviewed decision"):
            policy.check_policy()

    def test_tagged_version_allows_management_but_not_addon_changes(self):
        self.git("tag", "v0.5.0")
        (self.root / "README.md").write_text("management")
        self.commit()
        self.assertEqual(policy.check_policy()["version"], "0.5.0")
        self.lua.write_text("later fix without bump")
        self.commit()
        with self.assertRaisesRegex(ValueError, "Shipped content changed after"):
            policy.check_policy()

    def test_missing_reason_version_disagreement_and_unknown_fields_fail(self):
        self.decision(reason="")
        with self.assertRaisesRegex(ValueError, "record why"):
            policy.check_policy()
        self.decision()
        (self.root / versions.TOC).write_text("## Version: 0.4.1\n")
        with self.assertRaisesRegex(ValueError, "match the TOC"):
            policy.check_policy()
        self.decision()
        (self.root / "release-plan.json").write_text('{"unreviewed": true}')
        with self.assertRaisesRegex(ValueError, "reviewed release-plan"):
            policy.check_policy()

    def test_stale_baseline_fails(self):
        self.decision("0.4.1", "patch")
        self.commit()
        self.git("tag", "v0.4.1")
        self.decision()
        self.commit()
        with self.assertRaisesRegex(ValueError, "newest previous release tag"):
            policy.check_policy()


if __name__ == "__main__":
    unittest.main()
