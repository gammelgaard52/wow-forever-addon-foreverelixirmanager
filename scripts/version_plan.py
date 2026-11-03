"""Propose addon versions from committed content. Never write versions or tags."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

TOC = "ForeverElixirManager/ForeverElixirManager.toc"
# Workflows are GitHub-only. Review the output of packaging/publication code,
# including metadata visible in CurseForge administration and on the project page.
PACKAGING = ("scripts/validate.py",)
PUBLICATION = ("scripts/publish_release.py", "scripts/curseforge.py", "CHANGELOG.md")
DISTRIBUTION = PACKAGING + PUBLICATION
VERSION = re.compile(rb"(?m)^## Version: ((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))\r?$")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def snapshot(ref):
    # Resolve first: never interpolate caller-controlled refs into git paths/options.
    commit = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    names = git("ls-tree", "-r", "--name-only", "-z", commit, "--",
                "ForeverElixirManager", "LICENSE", *DISTRIBUTION).decode().split("\0")
    files = {name: git("show", commit + ":" + name) for name in names if name}
    if TOC not in files or "LICENSE" not in files:
        raise ValueError("Comparison requires the addon TOC and LICENSE in both revisions")
    matches = VERSION.findall(files[TOC])
    if len(matches) != 1:
        raise ValueError("Expected exactly one numeric TOC version")
    version = matches[0].decode()
    files[TOC] = VERSION.sub(b"## Version: <version>", files[TOC])
    return commit, version, files


def next_version(version, bump):
    major, minor, patch = map(int, version.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def shipped_digest(files):
    """Bind a semantic decision to installed content, with the TOC version normalized."""
    digest = hashlib.sha256()
    for name in sorted(files):
        if name not in DISTRIBUTION:
            data = files[name]
            digest.update(name.encode("utf-8") + b"\0" + str(len(data)).encode() + b"\0" + data)
    return digest.hexdigest()


def publication_digest(files):
    """Bind the review to packaging, publication code and release notes separately."""
    digest = hashlib.sha256()
    for name in sorted(files):
        if name in DISTRIBUTION:
            # These inputs are text; Git checkouts may use CRLF on Windows.
            data = files[name].replace(b"\r\n", b"\n")
            digest.update(name.encode("utf-8") + b"\0" + str(len(data)).encode() + b"\0" + data)
    return digest.hexdigest()


def plan(base_version, head_version, base_files, head_files, bump="patch"):
    base_key, head_key = tuple(map(int, base_version.split("."))), tuple(map(int, head_version.split(".")))
    if head_key < base_key:
        raise ValueError("Addon version must not go backwards")
    changed = sorted(name for name in base_files.keys() | head_files.keys()
                     if base_files.get(name) != head_files.get(name))
    content = [name for name in changed if name not in DISTRIBUTION]
    packaging = [name for name in changed if name in PACKAGING]
    publication = [name for name in changed if name in PUBLICATION]
    result = {"base_version": base_version, "current_version": head_version,
              "content_changes": content, "packaging_changes": packaging,
              "publication_changes": publication,
              "suggested_version": head_version, "bump": "none"}
    if content or packaging or publication:
        result["decision"] = "addon-change" if content else "publication-change"
        if head_key == base_key:
            result.update(suggested_version=next_version(base_version, bump), bump=bump)
            result["reason"] = "Addon or publication changed; review the semantic increment and compare ZIPs for packaging changes."
        else:
            result["reason"] = "A newer addon version is already prepared; do not bump it again."
    elif head_key != base_key:
        result["decision"] = "version-only-review"
        result["reason"] = "Only the version changed in installed content. Verify an intentional release preparation; management work does not justify this bump."
    else:
        result["decision"] = "management-only"
        result["reason"] = "Addon, packaging and publication are unchanged. Keep the addon version; no release is needed."
    return result


def summary(result, base, head):
    changed = result["content_changes"] + result["packaging_changes"] + result["publication_changes"]
    paths = "\n".join("- `" + name + "`" for name in changed) or "- No addon or publication changes."
    return f"""## Addon version assessment

Comparison: `{base[:12]}` to `{head[:12]}`.

| Decision | Current addon | Suggested addon | Bump |
|---|---|---|---|
| {result['decision']} | {result['current_version']} | {result['suggested_version']} | {result['bump']} |

{result['reason']}

{paths}

This is an advisory proposal, not a version write or release authorization.
The default patch proposal is a minimum; the agent must choose minor/major for
new features or breaking changes, including the project's pre-1.0 policy.
Packaging changes require ZIP comparison, even when addon source is unchanged.
The owner selects Alpha/Beta/Release and approves the combined publication workflow.
"""


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--bump", choices=("patch", "minor", "major"), default="patch")
    args = parser.parse_args(argv)
    base, base_version, base_files = snapshot(args.base)
    head, head_version, head_files = snapshot(args.head)
    result = plan(base_version, head_version, base_files, head_files, args.bump)
    print(json.dumps(result, indent=2))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
            stream.write(summary(result, base, head))


if __name__ == "__main__":
    main()
