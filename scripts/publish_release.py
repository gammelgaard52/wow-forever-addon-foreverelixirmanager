"""Explicit Actions release: validate first, tag once, publish and submit to CurseForge."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

import curseforge as cf
import validate
from release_policy import check_policy
from version_plan import git, snapshot

REPOSITORY = "gammelgaard52/wow-forever-addon-foreverelixirmanager"
ROOT = Path(__file__).resolve().parents[1]


def release_plan(version, release_type):
    if not re.fullmatch(validate.VERSION_RE, version):
        raise ValueError("Enter the prepared addon version as X.Y.Z, without v")
    if release_type not in ("alpha", "beta", "release"):
        raise ValueError("Choose alpha, beta or release")
    if validate.metadata() != version:
        raise ValueError("Requested version must match the prepared TOC; this workflow never bumps it")
    decision = check_policy()
    tag = "v" + version
    if git("tag", "--list", tag).strip():
        raise ValueError("Version already tagged. Inspect the existing release/upload; do not re-submit")
    head = snapshot("HEAD")[0]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8-sig")
    notes = cf.release_notes(changelog, tag, decision["base_tag"])
    return {"version": version, "tag": tag, "sha": head, "release_type": release_type,
            "prerelease": release_type != "release", "notes": notes}


def github(path, payload=None, missing_ok=False):
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("GitHub Actions token is missing")
    request = urllib.request.Request(
        "https://api.github.com/repos/" + REPOSITORY + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.build_opener(cf.NoRedirect()).open(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and missing_ok:
            return None
        raise ValueError(f"GitHub API HTTP {exc.code}; no automatic retry") from None


def gh(*args):
    result = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise ValueError("GitHub release command failed; inspect tag/release state before recovery")
    return result.stdout


def publish(version, release_type, approved=False):
    if not approved:
        raise ValueError("Publication requires explicit --approve-release")
    if (os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY):
        raise ValueError("Publication must be manually started on this repository's main branch")
    proposal = release_plan(version, release_type)
    if proposal["sha"] != os.environ.get("GITHUB_SHA"):
        raise ValueError("Checkout differs from the approved workflow commit")
    archive = ROOT / "dist" / f"ForeverElixirManager-{version}.zip"
    cf.validate_archive(archive, proposal["tag"])
    validated_bytes = archive.read_bytes()
    # Reconstruct from the pinned checkout and compare the artifact tested by CI.
    if validate.package(version).read_bytes() != validated_bytes:
        raise ValueError("Validated artifact differs from the approved source")
    tag = proposal["tag"]
    if (github("/git/ref/tags/" + tag, missing_ok=True) is not None
            or github("/releases/tags/" + tag, missing_ok=True) is not None):
        raise ValueError("Tag/release already exists; refusing replacement or duplicate upload")
    token = os.environ.get("CURSEFORGE_API_TOKEN")
    if not token:
        raise ValueError("Configure the CURSEFORGE_API_TOKEN Actions secret")
    project = cf.positive_id(os.environ.get("CURSEFORGE_PROJECT_ID", ""))
    # Check credentials/catalog identity before making any GitHub release changes.
    metadata = cf.upload_metadata(
        cf.api("/game/versions", token),
        os.environ.get("CURSEFORGE_GAME_VERSION_ID", ""),
        os.environ.get("CURSEFORGE_GAME_VERSION_NAME", ""),
        os.environ.get("CURSEFORGE_GAME_VERSION_TYPE_ID", ""),
        tag, release_type, proposal["notes"], manual_release=False,
    )
    github("/git/refs", {"ref": "refs/tags/" + tag, "sha": proposal["sha"]})
    notes = ROOT / "dist" / "approved-release-notes.md"
    notes.write_text(proposal["notes"], encoding="utf-8")
    flags = ["--prerelease", "--latest=false"] if proposal["prerelease"] else ["--latest"]
    # Tag, GitHub release and CurseForge submission belong to the same approved run.
    gh("release", "create", tag, str(archive), "--verify-tag", "--title",
       f"ForeverElixirManager-{tag} ({release_type.title()})", "--notes-file", str(notes), *flags)
    with tempfile.TemporaryDirectory(prefix="fem-published-") as directory:
        gh("release", "download", tag, "--pattern", archive.name, "--dir", directory)
        if (Path(directory) / archive.name).read_bytes() != validated_bytes:
            raise ValueError("Published GitHub ZIP differs from validated ZIP; CurseForge upload stopped")
    # No retry: a timeout may mean the server accepted the file. The tag guards reruns.
    body, content_type = cf.multipart(metadata, archive)
    result = cf.api(f"/projects/{project}/upload-file", token, body, content_type)
    if not isinstance(result, dict) or type(result.get("id")) is not int or result["id"] <= 0:
        raise ValueError("Upload result uncertain; inspect CurseForge files before any recovery")
    message = (f"Released {tag} as {release_type} from {proposal['sha']}.\n"
               f"ZIP SHA-256: {hashlib.sha256(validated_bytes).hexdigest()}\n"
               f"CurseForge file: {result['id']}; automatic publication after moderation.\n")
    print(message)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
            stream.write(message)
    return result["id"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="", help="Optional check against the prepared TOC version")
    parser.add_argument("--release-type", required=True, choices=("alpha", "beta", "release"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Local validation only; no API calls")
    mode.add_argument("--approve-release", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    version = args.version or validate.metadata()
    if args.check:
        print(json.dumps(release_plan(version, args.release_type), indent=2))
        if os.environ.get("GITHUB_OUTPUT"):
            with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
                stream.write("version=" + version + "\n")
    else:
        publish(version, args.release_type, args.approve_release)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        sys.exit(f"HTTP {exc.code}; inspect release/upload state before recovery. Response body omitted.")
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"STOPPED: {exc}")
