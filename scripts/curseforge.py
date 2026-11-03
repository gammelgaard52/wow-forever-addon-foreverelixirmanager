"""CurseForge author Upload API. No upload without --approve-upload."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
import uuid
import zipfile

BASE = "https://wow.curseforge.com/api"
REPOSITORY_URL = "https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager"
TAG_RE = r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def release_notes(changelog, tag, previous_tag=None):
    """Render one version's notes with links to its source and full changelog."""
    if not re.fullmatch(TAG_RE, tag):
        raise ValueError("Tag must be vX.Y.Z")
    if previous_tag is not None:
        if (not re.fullmatch(TAG_RE, previous_tag)
                or tuple(map(int, previous_tag[1:].split("."))) >= tuple(map(int, tag[1:].split(".")))):
            raise ValueError("Previous tag must be an earlier version vX.Y.Z")
    sections = re.findall(
        r"(?ms)^##[ \t]+" + re.escape(tag[1:]) + r"[ \t]*\r?\n(.*?)(?=^##[ \t]|\Z)",
        changelog,
    )
    if len(sections) != 1 or not sections[0].strip():
        raise ValueError("Changelog must contain exactly one nonempty section for " + tag)
    full = (f"{REPOSITORY_URL}/compare/{previous_tag}...{tag}" if previous_tag
            else f"{REPOSITORY_URL}/blob/{tag}/CHANGELOG.md")
    return (f"## [{tag[1:]}]({REPOSITORY_URL}/tree/{tag})\n\n"
            f"[Full Changelog]({full})\n\n"
            + sections[0].strip())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("API redirected; verify the official endpoint before retrying")


def api(path, token, body=None, content_type=None):
    headers = {"X-Api-Token": token, "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(BASE + path, data=body, headers=headers)
    # Never forward a token through redirects or print response bodies on error.
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
        return json.load(response)


def positive_id(value):
    if not re.fullmatch(r"[1-9][0-9]*", str(value)):
        raise ValueError("Project and version identifiers must be positive integers")
    return int(value)


def check_version(versions, name):
    if not name or not isinstance(versions, list) or any(not isinstance(row, dict) for row in versions):
        raise ValueError("Expected a version name and a game-version catalog")
    matching = [row for row in versions if row.get("name") == name]
    if len(matching) != 1:
        raise ValueError("Game version name is missing or ambiguous in the live catalog")
    row = matching[0]
    return {
        "CURSEFORGE_GAME_VERSION_ID": positive_id(row.get("id", "")),
        "CURSEFORGE_GAME_VERSION_NAME": name,
        "CURSEFORGE_GAME_VERSION_TYPE_ID": positive_id(row.get("gameVersionTypeID", "")),
    }


def upload_metadata(versions, version_id, version_name, type_id, tag, release_type, changelog,
                    manual_release=True):
    version_id, type_id = positive_id(version_id), positive_id(type_id)
    if not isinstance(versions, list) or any(not isinstance(row, dict) for row in versions):
        raise ValueError("Unexpected game-version API response")
    matching = [row for row in versions if row.get("id") == version_id]
    if len(matching) != 1:
        raise ValueError("Configured game version does not exist uniquely in the live catalog")
    row = matching[0]
    if row.get("name") != version_name or row.get("gameVersionTypeID") != type_id:
        raise ValueError("Game version name/type mismatch; verify Forever identifiers")
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("Tag must be vX.Y.Z")
    if release_type not in ("alpha", "beta", "release"):
        raise ValueError("Invalid release type")
    if not changelog.strip():
        raise ValueError("Changelog must not be empty")
    return {
        "changelog": changelog,
        "changelogType": "markdown",
        "displayName": "ForeverElixirManager-" + tag,
        "gameVersions": [version_id],
        "releaseType": release_type,
        "isMarkedForManualRelease": manual_release,
    }


def validate_archive(path, tag):
    expected = {
        "ForeverElixirManager/ForeverElixirManager.toc",
        "ForeverElixirManager/ForeverElixirManager.lua",
        "ForeverElixirManager/LICENSE",
    }
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(expected) or set(names) != expected or archive.testzip() is not None:
            raise ValueError("Invalid installation archive")
        toc = archive.read("ForeverElixirManager/ForeverElixirManager.toc").decode("utf-8-sig")
        if not re.search(r"^## Version: " + re.escape(tag[1:]) + r"\r?$", toc, re.M):
            raise ValueError("Archive version does not match tag")


def multipart(metadata, archive):
    boundary = "fem-" + uuid.uuid4().hex
    header = (
        "--" + boundary + '\r\nContent-Disposition: form-data; name="metadata"\r\n'
        "Content-Type: application/json\r\n\r\n" + json.dumps(metadata) +
        "\r\n--" + boundary + '\r\nContent-Disposition: form-data; name="file"; '
        'filename="ForeverElixirManager.zip"\r\nContent-Type: application/zip\r\n\r\n'
    ).encode("utf-8")
    return header + archive.read_bytes() + ("\r\n--" + boundary + "--\r\n").encode(), (
        "multipart/form-data; boundary=" + boundary
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list-versions", action="store_true")
    mode.add_argument("--check-version", metavar="NAME")
    mode.add_argument("--approve-upload", action="store_true")
    parser.add_argument("--tag")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--changelog", type=Path)
    parser.add_argument("--previous-tag", help="Existing previous release tag for the comparison link")
    parser.add_argument("--release-type", choices=("alpha", "beta", "release"), default="alpha")
    parser.add_argument("--publish-on-approval", action="store_true",
                        help="Authorize automatic CurseForge publication after moderation")
    args = parser.parse_args(argv)
    if not args.list_versions and args.check_version is None and not args.approve_upload:
        raise ValueError("Upload requires explicit --approve-upload authorization")
    token = os.environ.get("CURSEFORGE_API_TOKEN")
    if not token:
        raise ValueError("Configure the CURSEFORGE_API_TOKEN Actions secret")
    if args.check_version is not None:
        result = check_version(api("/game/versions", token), args.check_version)
        print("PASS: authenticated catalog GET; no file uploaded. Project upload permission is not tested.")
        print(json.dumps(result, indent=2))
        return
    if args.list_versions:
        print(json.dumps(api("/game/versions", token), indent=2))
        return
    if not args.tag or not args.archive or not args.changelog:
        raise ValueError("Upload requires tag, archive and changelog")
    project = positive_id(os.environ.get("CURSEFORGE_PROJECT_ID", ""))
    validate_archive(args.archive, args.tag)
    notes = release_notes(args.changelog.read_text(encoding="utf-8-sig"), args.tag, args.previous_tag)
    metadata = upload_metadata(
        api("/game/versions", token),
        os.environ.get("CURSEFORGE_GAME_VERSION_ID", ""),
        os.environ.get("CURSEFORGE_GAME_VERSION_NAME", ""),
        os.environ.get("CURSEFORGE_GAME_VERSION_TYPE_ID", ""),
        args.tag, args.release_type, notes,
        manual_release=not args.publish_on_approval,
    )
    body, content_type = multipart(metadata, args.archive)
    result = api(f"/projects/{project}/upload-file", token, body, content_type)
    if not isinstance(result, dict) or type(result.get("id")) is not int or result["id"] <= 0:
        raise ValueError("Upload result uncertain; inspect project files before retrying")
    publication = "automatic publication after moderation" if args.publish_on_approval else "moderation/manual release still required"
    print(f"PASS: uploaded CurseForge file {result['id']}; {publication}")
    return result["id"]


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        sys.exit(f"CurseForge HTTP {exc.code}; inspect project files before retrying. Response body omitted.")
    except (ValueError, OSError, urllib.error.URLError, zipfile.BadZipFile) as exc:
        sys.exit(f"BLOCKED: {exc}")
