"""Prepare reviewed version/notes on a clean branch; never commit, tag or publish."""
import argparse
import json
from pathlib import Path
import re

from version_plan import TOC, VERSION, git, next_version, plan, shipped_digest, snapshot


def prepare(base, bump, notes_file=None, apply=False, reason=None):
    # A release tag is the baseline, not main: main may already contain new code.
    if not re.fullmatch(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", base):
        raise ValueError("Base must be an existing release tag vX.Y.Z")
    root = Path(git("rev-parse", "--show-toplevel").decode().strip())
    if git("status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("Commit or preserve working-tree changes before release preparation")
    base_sha, base_version, base_files = snapshot("refs/tags/" + base)
    head_sha, head_version, head_files = snapshot("HEAD")
    if base != "v" + base_version:
        raise ValueError("Base tag and its TOC version disagree")
    git("merge-base", "--is-ancestor", base_sha, head_sha)
    # Refuse a stale baseline: it can mistake an already released change for new work.
    tags = git("tag", "--merged", "HEAD", "--list", "v*").decode().splitlines()
    numeric = [t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    if any(tuple(map(int, t[1:].split("."))) > tuple(map(int, base_version.split(".")))
           for t in numeric):
        raise ValueError("Use the newest release tag reachable from HEAD as the baseline")
    result = plan(base_version, head_version, base_files, head_files, bump)
    if (result["decision"] == "addon-change" and head_version != base_version
            and head_version != next_version(base_version, bump)):
        raise ValueError("Prepared version differs from the reviewed increment; reconcile the release decision")
    result["written"] = False
    if result["decision"] != "addon-change" or result["bump"] == "none":
        return result
    version = result["suggested_version"]
    if git("tag", "--list", "v" + version).strip():
        raise ValueError("Target version already has a tag; published versions are immutable")
    if not apply:
        return result
    branch = git("branch", "--show-current").decode().strip()
    if not branch or branch == "main":
        raise ValueError("Apply release preparation on a dedicated branch")
    if notes_file is None:
        raise ValueError("--apply requires --notes-file with reviewed addon release notes")
    if not reason or not reason.strip():
        raise ValueError("--apply requires --reason explaining the reviewed semantic increment")
    notes = Path(notes_file).read_text(encoding="utf-8-sig").strip()
    if not notes or re.search(r"(?m)^#{1,2}\s", notes):
        raise ValueError("Provide nonempty notes without a document/version heading")
    toc_path, changelog_path = root / TOC, root / "CHANGELOG.md"
    toc, changelog = toc_path.read_bytes(), changelog_path.read_bytes()
    if VERSION.findall(toc) != [head_version.encode()]:
        raise ValueError("Working TOC does not match the committed version")
    text = changelog.decode("utf-8-sig").replace("\r\n", "\n")
    if not text.startswith("# Release notes\n\n"):
        raise ValueError("Expected the existing release-notes heading")
    if re.search(r"(?m)^## " + re.escape(version) + r"(?:\s|$)", text):
        raise ValueError("Target version already has release notes; review them manually")
    newline = "\r\n" if b"\r\n" in changelog else "\n"
    new_log = ("# Release notes\n\n## " + version + "\n\n" + notes + "\n\n"
               + text[len("# Release notes\n\n"):]).replace("\n", newline).encode("utf-8")
    new_toc = VERSION.sub(lambda m: m.group(0).replace(m.group(1), version.encode()), toc)
    decision_path = root / "release-plan.json"
    old_decision = decision_path.read_bytes() if decision_path.exists() else None
    decision = {"base_tag": base, "version": version, "bump": bump, "reason": reason.strip(),
                "content_sha256": shipped_digest(head_files)}
    # Prepare all outputs first; restore the originals if a write fails.
    try:
        toc_path.write_bytes(new_toc)
        changelog_path.write_bytes(new_log)
        decision_path.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    except OSError:
        toc_path.write_bytes(toc)
        changelog_path.write_bytes(changelog)
        if old_decision is None:
            decision_path.unlink(missing_ok=True)
        else:
            decision_path.write_bytes(old_decision)
        raise
    result["written"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Latest reachable release tag; fetch tags first")
    parser.add_argument("--bump", required=True, choices=("patch", "minor", "major"))
    parser.add_argument("--notes-file", type=Path)
    parser.add_argument("--apply", action="store_true", help="Write reviewed TOC/notes on a clean branch")
    parser.add_argument("--reason", help="Agent-reviewed justification for patch/minor/major")
    args = parser.parse_args()
    result = prepare(args.base, args.bump, args.notes_file, args.apply, args.reason)
    print(json.dumps(result, indent=2))
    print("Review the diff and run validation. No commit, tag, GitHub release or upload was created.")


if __name__ == "__main__":
    main()
