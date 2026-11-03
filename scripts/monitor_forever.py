"""Watch the configured Forever catalog; never modify or publish the addon."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error

import curseforge


def version_key(name):
    if not isinstance(name, str) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", name):
        raise ValueError("Expected a numeric game version X.Y.Z; review catalog format")
    return tuple(map(int, name.split(".")))


def latest_version(rows, baseline_id, baseline_name, type_id):
    baseline_id, type_id = curseforge.positive_id(baseline_id), curseforge.positive_id(type_id)
    baseline = version_key(baseline_name)
    # Validate the configured identity before trusting any other row in its type.
    identity = curseforge.check_version(rows, baseline_name)
    if identity["CURSEFORGE_GAME_VERSION_ID"] != baseline_id or identity["CURSEFORGE_GAME_VERSION_TYPE_ID"] != type_id:
        raise ValueError("Configured Forever baseline does not match the live catalog")
    versions, ids = {}, set()
    for row in rows:
        if row.get("gameVersionTypeID") != type_id:
            continue
        key = version_key(row.get("name"))
        version_id = curseforge.positive_id(row.get("id", ""))
        if key in versions or version_id in ids:
            raise ValueError("Duplicate Forever name or ID in catalog")
        versions[key] = {"name": row["name"], "id": version_id}
        ids.add(version_id)
    latest = max(versions)
    return versions[latest] if latest > baseline else None


def marker(type_id, name):
    version_key(name)
    return f"<!-- forever-version:{curseforge.positive_id(type_id)}:{name} -->"


def github(path, payload=None):
    command = ["gh", "api", path]
    if payload is not None:
        command += ["--method", "POST", "--input", "-"]
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True, check=True, timeout=60)
    return json.loads(result.stdout)


def existing_issue(repo, key):
    # List all states directly: closed issues count, and search-index lag must not
    # create duplicates. A full page may contain PRs; filter only after pagination.
    page = 1
    while True:
        rows = github(f"repos/{repo}/issues?state=all&per_page=100&page={page}")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Unexpected GitHub issues response")
        for row in rows:
            lines = (row.get("body") or "").splitlines()
            if "pull_request" not in row and lines and lines[0] == key:
                return row["number"]
        if len(rows) < 100:
            return None
        page += 1


def report(repo, name, version_id, type_id, result, run_url):
    key = marker(type_id, name)
    version_id = curseforge.positive_id(version_id)
    prior = existing_issue(repo, key)
    if prior is not None:
        print(f"Already tracked in issue #{prior}; no duplicate created")
        return
    status = "PASS" if result == "success" else "NOT PASSED (" + result + ")"
    body = f"""{key}
CurseForge lists **Forever {name}**, game version ID {version_id}, type {type_id}.
This is a catalog observation, not confirmation of the installed client build.

Rebuild and existing automated checks: **{status}**.
[Workflow run, logs and any successful ZIP artifact]({run_url}).
Actual compatibility with this Forever version: **NOT VERIFIED**.

- [ ] Verify the actual Forever build and Interface value from client evidence.
- [ ] Complete docs/VALIDATION.md: secure clicks, combat, buffs, bags and settings.
- [ ] Propose only required addon changes in a separate PR; keep the implementation simple.
- [ ] After verification, review the configured CurseForge version ID/name/type together.
- [ ] Obtain separate approval for any release tag and CurseForge upload.

The rebuild keeps the current addon version and Interface. No release tag,
GitHub release or CurseForge upload was created. Closing this issue suppresses
repeat notifications for this game version. Related: #3.
"""
    created = github(f"repos/{repo}/issues", {"title": f"Review Forever {name} compatibility", "body": body})
    print(f"Created compatibility issue #{created['number']}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("detect", "report"))
    parser.add_argument("--name")
    parser.add_argument("--version-id")
    parser.add_argument("--result", choices=("success", "failure", "cancelled", "skipped"))
    args = parser.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("GITHUB_REPOSITORY must identify the target repository")
    type_id = curseforge.positive_id(os.environ.get("CURSEFORGE_GAME_VERSION_TYPE_ID", ""))
    if args.mode == "report":
        if not args.name or not args.version_id or not args.result:
            raise ValueError("Report requires name, version ID and rebuild result")
        run_id = curseforge.positive_id(os.environ.get("GITHUB_RUN_ID", ""))
        report(repo, args.name, args.version_id, type_id, args.result,
               f"https://github.com/{repo}/actions/runs/{run_id}")
        return
    token = os.environ.get("CURSEFORGE_API_TOKEN")
    if not token:
        raise ValueError("Configure the CURSEFORGE_API_TOKEN Actions secret")
    candidate = latest_version(curseforge.api("/game/versions", token),
                               os.environ.get("CURSEFORGE_GAME_VERSION_ID", ""),
                               os.environ.get("CURSEFORGE_GAME_VERSION_NAME", ""), type_id)
    if candidate and existing_issue(repo, marker(type_id, candidate["name"])) is not None:
        print(f"Forever {candidate['name']} is already tracked (open or closed)")
        candidate = None
    output = "changed=false\n"
    if candidate:
        output = f"changed=true\nname={candidate['name']}\nversion_id={candidate['id']}\n"
    print(output, end="")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            stream.write(output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
        # Subprocess/HTTP response bodies can contain account details; omit them.
        sys.exit(f"FAIL: Forever monitor ({type(exc).__name__}); check configuration and service availability")
