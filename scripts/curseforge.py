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


def upload_metadata(versions, version_id, version_name, type_id, tag, release_type, changelog):
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
        "displayName": "ForeverElixirManager " + tag,
        "gameVersions": [version_id],
        "releaseType": release_type,
        "isMarkedForManualRelease": True,
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
    parser.add_argument("--list-versions", action="store_true")
    parser.add_argument("--approve-upload", action="store_true")
    parser.add_argument("--tag")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--changelog", type=Path)
    parser.add_argument("--release-type", choices=("alpha", "beta", "release"), default="alpha")
    args = parser.parse_args(argv)
    if not args.list_versions and not args.approve_upload:
        raise ValueError("Upload requires explicit --approve-upload authorization")
    token = os.environ.get("CURSEFORGE_API_TOKEN")
    if not token:
        raise ValueError("Configure the CURSEFORGE_API_TOKEN Actions secret")
    if args.list_versions:
        print(json.dumps(api("/game/versions", token), indent=2))
        return
    if not args.tag or not args.archive or not args.changelog:
        raise ValueError("Upload requires tag, archive and changelog")
    project = positive_id(os.environ.get("CURSEFORGE_PROJECT_ID", ""))
    validate_archive(args.archive, args.tag)
    metadata = upload_metadata(
        api("/game/versions", token),
        os.environ.get("CURSEFORGE_GAME_VERSION_ID", ""),
        os.environ.get("CURSEFORGE_GAME_VERSION_NAME", ""),
        os.environ.get("CURSEFORGE_GAME_VERSION_TYPE_ID", ""),
        args.tag, args.release_type, args.changelog.read_text(encoding="utf-8"),
    )
    body, content_type = multipart(metadata, args.archive)
    result = api(f"/projects/{project}/upload-file", token, body, content_type)
    if not isinstance(result, dict) or type(result.get("id")) is not int or result["id"] <= 0:
        raise ValueError("Upload result uncertain; inspect project files before retrying")
    print(f"PASS: uploaded CurseForge file {result['id']}; moderation/manual release still required")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        sys.exit(f"CurseForge HTTP {exc.code}; inspect project files before retrying. Response body omitted.")
    except (ValueError, OSError, urllib.error.URLError, zipfile.BadZipFile) as exc:
        sys.exit(f"BLOCKED: {exc}")
