from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_release.py"
TOC = "ForeverElixirManager/ForeverElixirManager.toc"


class ReleasePreparationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "-b", "main")
        self.write(TOC, "## Version: 0.4.0\n## Interface: 16001\n")
        self.write("ForeverElixirManager/ForeverElixirManager.lua", "original\n")
        self.write("LICENSE", "license\n")
        self.write("CHANGELOG.md", "# Release notes\n\n## 0.4.0\n\nOriginal notes.\n")
        self.commit()
        self.git("tag", "v0.4.0")
        self.git("switch", "-c", "prepare")
        self.notes = self.root / "notes.txt"
        self.write("notes.txt", "- Reviewed new behavior.\n")
        self.commit()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True).stdout

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode())

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "fixture")

    def change_addon(self):
        self.write("ForeverElixirManager/ForeverElixirManager.lua", "new behavior\n")
        self.commit()

    def run_prepare(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--base", "v0.4.0",
                                 "--bump", "minor", *args], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_management_and_packaging_never_write_versions(self):
        for path in ["README.md", "scripts/validate.py"]:
            self.write(path, "management\n")
            self.commit()
            self.run_prepare("--apply", "--notes-file", str(self.notes))
            self.assertEqual(self.git("status", "--porcelain"), b"")
            self.assertIn("0.4.0", (self.root / TOC).read_text())

    def test_preview_and_apply_change_only_version_and_notes_without_git_mutations(self):
        self.change_addon()
        head, tags = self.git("rev-parse", "HEAD"), self.git("tag")
        result = self.run_prepare()
        self.assertIn('"suggested_version": "0.5.0"', result.stdout)
        self.assertEqual(self.git("status", "--porcelain"), b"")
        self.run_prepare("--apply", "--notes-file", str(self.notes))
        self.assertEqual(set(self.git("diff", "--name-only").decode().splitlines()),
                         {TOC, "CHANGELOG.md"})
        self.assertIn("## Version: 0.5.0", (self.root / TOC).read_text())
        self.assertIn("## 0.5.0\n\n- Reviewed new behavior.", (self.root / "CHANGELOG.md").read_text())
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("tag"), tags)
        self.commit()
        self.run_prepare("--apply", "--notes-file", str(self.notes))
        self.assertEqual(self.git("status", "--porcelain"), b"")

    def test_dirty_tree_is_preserved(self):
        self.change_addon()
        self.write("README.md", "user's uncommitted work\n")
        before = self.git("status", "--porcelain")
        self.run_prepare("--apply", "--notes-file", str(self.notes), success=False)
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertIn("0.4.0", (self.root / TOC).read_text())

    def test_main_detached_and_missing_notes_are_rejected(self):
        self.change_addon()
        self.run_prepare("--apply", success=False)
        self.git("branch", "-M", "main")
        self.run_prepare("--apply", "--notes-file", str(self.notes), success=False)
        self.git("checkout", "--detach")
        self.run_prepare("--apply", "--notes-file", str(self.notes), success=False)
        self.assertEqual(self.git("status", "--porcelain"), b"")

    def test_stale_baseline_existing_target_and_tag_mismatch_are_rejected(self):
        self.change_addon()
        self.git("tag", "v0.5.0")
        self.run_prepare(success=False)
        self.git("tag", "-d", "v0.5.0")
        self.git("tag", "-f", "v0.4.0", "HEAD")
        self.write(TOC, "## Version: 0.4.1\n## Interface: 16001\n")
        self.commit()
        self.git("tag", "-f", "v0.4.0", "HEAD")
        self.run_prepare(success=False)
        self.assertEqual(self.git("status", "--porcelain"), b"")

    def test_duplicate_notes_and_invalid_baseline_are_rejected_without_writes(self):
        self.change_addon()
        self.write("CHANGELOG.md", "# Release notes\n\n## 0.5.0\n\nExisting.\n")
        self.commit()
        self.run_prepare("--apply", "--notes-file", str(self.notes), success=False)
        self.run_prepare("--base", "main", success=False)
        self.assertEqual(self.git("status", "--porcelain"), b"")


if __name__ == "__main__":
    unittest.main()
