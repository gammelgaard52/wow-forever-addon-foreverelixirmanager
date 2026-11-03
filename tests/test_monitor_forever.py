import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import monitor_forever as monitor

BASE = {"id": 17053, "name": "1.60.1", "gameVersionTypeID": 88568}
NEW = {"id": 17054, "name": "1.60.2", "gameVersionTypeID": 88568}
CONFIG = {
    "GITHUB_REPOSITORY": "example/addon",
    "GITHUB_RUN_ID": "123",
    "CURSEFORGE_API_TOKEN": "test-only",
    "CURSEFORGE_GAME_VERSION_ID": "17053",
    "CURSEFORGE_GAME_VERSION_NAME": "1.60.1",
    "CURSEFORGE_GAME_VERSION_TYPE_ID": "88568",
}


class MonitorTests(unittest.TestCase):
    def detect(self, rows):
        return monitor.latest_version(rows, "17053", "1.60.1", "88568")

    def test_filters_flavor_and_compares_numeric_versions_not_ids_or_order(self):
        rows = [NEW, {**NEW, "id": 1, "name": "1.60.10"}, BASE,
                {**NEW, "id": 99999, "name": "99.0.0", "gameVersionTypeID": 99}]
        self.assertEqual(self.detect(rows), {"id": 1, "name": "1.60.10"})
        self.assertIsNone(self.detect([BASE, {**NEW, "name": "1.59.9"}]))
        self.assertIsNone(self.detect([BASE, rows[-1]]))

    def test_missing_changed_or_ambiguous_baseline_fails(self):
        for rows in [[], [NEW], [BASE, BASE], [{**BASE, "id": 99}],
                     [{**BASE, "gameVersionTypeID": 99}], ["bad"], {}]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.detect(rows)

    def test_malformed_or_duplicate_forever_entries_fail(self):
        for row in [{**NEW, "name": "1.60.2-beta"}, {**NEW, "name": "1.60.02"},
                    {**NEW, "name": "1.60.2\nchanged=true"}, {**NEW, "id": -1},
                    {**NEW, "id": BASE["id"]}]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.detect([BASE, row])
        with self.assertRaises(ValueError):
            self.detect([BASE, NEW, {**NEW, "id": 999}])

    def test_pagination_closed_issue_dedup_and_pr_exclusion(self):
        key = monitor.marker(88568, "1.60.2")
        first_page = [{"number": i, "body": "unrelated"} for i in range(100)]
        first_page[0] = {"number": 1, "body": key + "\n", "pull_request": {}}
        with patch.object(monitor, "github", side_effect=[first_page,
                          [{"number": 101, "state": "closed", "body": key + "\r\nreviewed"}]]) as api:
            self.assertEqual(monitor.existing_issue("example/addon", key), 101)
            self.assertIn("state=all", api.call_args_list[0].args[0])
            self.assertIn("page=2", api.call_args_list[1].args[0])

    def test_detection_get_only_outputs_new_version_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.dict(os.environ, {**CONFIG, "GITHUB_OUTPUT": str(output)}, clear=True), \
                    patch.object(monitor.curseforge, "api", return_value=[NEW, BASE]) as cf, \
                    patch.object(monitor, "github", return_value=[]) as gh, patch("builtins.print"):
                monitor.main(["detect"])
            cf.assert_called_once_with("/game/versions", "test-only")
            self.assertTrue(all(len(call.args) == 1 for call in gh.call_args_list))
            self.assertEqual(output.read_text(), "changed=true\nname=1.60.2\nversion_id=17054\n")

    def test_existing_issue_or_unchanged_version_prevents_rebuild(self):
        for rows, issues in [([BASE], []), ([BASE, NEW], [{"number": 4,
                            "body": monitor.marker(88568, "1.60.2") + "\n", "state": "closed"}])]:
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "output"
                with patch.dict(os.environ, {**CONFIG, "GITHUB_OUTPUT": str(output)}, clear=True), \
                        patch.object(monitor.curseforge, "api", return_value=rows), \
                        patch.object(monitor, "github", return_value=issues), patch("builtins.print"):
                    monitor.main(["detect"])
                self.assertEqual(output.read_text(), "changed=false\n")

    def test_catalog_failure_does_not_emit_success_or_create_issue(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.dict(os.environ, {**CONFIG, "GITHUB_OUTPUT": str(output)}, clear=True), \
                    patch.object(monitor.curseforge, "api", side_effect=OSError("offline")), \
                    patch.object(monitor, "github") as gh:
                with self.assertRaises(OSError):
                    monitor.main(["detect"])
            gh.assert_not_called()
            self.assertFalse(output.exists())

    def test_report_records_failed_build_without_claiming_compatibility(self):
        with patch.dict(os.environ, CONFIG, clear=True), \
                patch.object(monitor, "github", side_effect=[[], {"number": 5}]) as gh, \
                patch.object(monitor.curseforge, "api") as cf, patch("builtins.print"):
            monitor.main(["report", "--name", "1.60.2", "--version-id", "17054", "--result", "failure"])
        cf.assert_not_called()
        path, payload = gh.call_args.args
        self.assertEqual(path, "repos/example/addon/issues")
        self.assertIn("NOT PASSED (failure)", payload["body"])
        self.assertIn("NOT VERIFIED", payload["body"])
        self.assertIn("https://github.com/example/addon/actions/runs/123", payload["body"])
        self.assertTrue(payload["body"].startswith(monitor.marker(88568, "1.60.2") + "\n"))

    def test_report_rechecks_for_existing_issue_before_post(self):
        with patch.object(monitor, "github", return_value=[{"number": 7,
                          "body": monitor.marker(88568, "1.60.2") + "\n"}]) as gh, patch("builtins.print"):
            monitor.report("example/addon", "1.60.2", 17054, 88568, "success", "test-run")
        self.assertEqual(len(gh.call_args_list), 1)
        self.assertEqual(len(gh.call_args.args), 1)

    def test_github_payload_uses_stdin_and_failures_are_not_retried(self):
        payload = {"title": "Version", "body": "Line 1\nLine 2 with `literal` $text"}
        with patch.object(monitor.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"number":7}')) as run:
            self.assertEqual(monitor.github("repos/example/addon/issues", payload), {"number": 7})
            self.assertEqual(json.loads(run.call_args.kwargs["input"]), payload)
            self.assertEqual(run.call_args.args[0][-4:], ["--method", "POST", "--input", "-"])
        with patch.object(monitor.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 60)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                monitor.github("repos/example/addon/issues", payload)
            run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
