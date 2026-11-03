import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("version_plan", ROOT / "scripts/version_plan.py")
versions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versions)


class VersionPlanTests(unittest.TestCase):
    def setUp(self):
        self.files = {versions.TOC: b"## Version: <version>\n## Interface: 16001\n",
                      "ForeverElixirManager/ForeverElixirManager.lua": b"original",
                      "LICENSE": b"license", "scripts/validate.py": b"packager"}

    def test_management_only_changes_do_not_propose_new_version(self):
        # snapshot only passes installed files and packaging code into the planner.
        result = versions.plan("0.4.0", "0.4.0", self.files, dict(self.files))
        self.assertEqual(result["decision"], "management-only")
        self.assertEqual(result["suggested_version"], "0.4.0")
        self.assertEqual(result["bump"], "none")

    def test_content_change_proposes_semantic_increment(self):
        changed = {**self.files, "ForeverElixirManager/ForeverElixirManager.lua": b"new"}
        for bump, expected in [("patch", "0.4.1"), ("minor", "0.5.0"), ("major", "1.0.0")]:
            with self.subTest(bump=bump):
                result = versions.plan("0.4.0", "0.4.0", self.files, changed, bump)
                self.assertEqual(result["suggested_version"], expected)
                self.assertEqual(result["decision"], "addon-change")

    def test_already_prepared_version_is_not_incremented_again(self):
        changed = {**self.files, "ForeverElixirManager/ForeverElixirManager.lua": b"new"}
        result = versions.plan("0.3.0", "0.4.0", self.files, changed)
        self.assertEqual(result["suggested_version"], "0.4.0")
        self.assertEqual(result["bump"], "none")

    def test_packaging_changes_require_review_instead_of_auto_bump(self):
        for path in versions.PACKAGING:
            result = versions.plan("0.4.0", "0.4.0", self.files, {**self.files, path: b"new"})
            self.assertEqual(result["decision"], "packaging-review")
            self.assertEqual(result["suggested_version"], "0.4.0")

    def test_version_only_and_regression_are_not_treated_as_features(self):
        result = versions.plan("0.4.0", "0.4.1", self.files, self.files)
        self.assertEqual(result["decision"], "version-only-review")
        with self.assertRaises(ValueError):
            versions.plan("0.4.0", "0.3.9", self.files, self.files)

    def test_toc_license_additions_and_deletions_are_distribution_changes(self):
        for path in [versions.TOC, "LICENSE", "ForeverElixirManager/extra.lua"]:
            result = versions.plan("0.4.0", "0.4.0", self.files, {**self.files, path: b"changed"})
            self.assertEqual(result["decision"], "addon-change")
        removed = dict(self.files)
        del removed["ForeverElixirManager/ForeverElixirManager.lua"]
        self.assertEqual(versions.plan("0.4.0", "0.4.0", self.files, removed)["decision"], "addon-change")

    def test_real_git_history_ignores_management_but_detects_mixed_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", directory, *args], check=True, capture_output=True).stdout
            def commit():
                git("add", ".")
                git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
                return git("rev-parse", "HEAD").decode().strip()
            git("init")
            for name, data in self.files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data.replace(b"<version>", b"0.4.0"))
            base = commit()
            for name in ["README.md", "AGENTS.md", "tests/check.py", "scripts/monitor.py", ".github/workflows/validate.yml"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("management change", encoding="utf-8")
            management = commit()
            (root / "ForeverElixirManager/ForeverElixirManager.lua").write_text("new behavior")
            mixed = commit()
            with patch.object(versions, "git", side_effect=git):
                _, bv, bf = versions.snapshot(base)
                _, hv, hf = versions.snapshot(management)
                self.assertEqual(versions.plan(bv, hv, bf, hf)["decision"], "management-only")
                _, hv, hf = versions.snapshot(mixed)
                self.assertEqual(versions.plan(bv, hv, bf, hf)["suggested_version"], "0.4.1")
                with self.assertRaises(subprocess.CalledProcessError):
                    versions.snapshot("--not-a-ref")
            self.assertEqual(git("status", "--porcelain"), b"")


if __name__ == "__main__":
    unittest.main()
