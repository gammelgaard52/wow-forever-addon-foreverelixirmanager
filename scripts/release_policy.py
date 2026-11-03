"""Enforce the agent-reviewed SemVer decision against committed shipped content."""
import json
from pathlib import Path
import re

import validate
from version_plan import git, next_version, plan, shipped_digest, snapshot

ROOT = Path(__file__).resolve().parents[1]


def check_policy():
    version = validate.metadata()
    decision = json.loads((ROOT / "release-plan.json").read_text(encoding="utf-8"))
    required = {"base_tag", "version", "bump", "reason", "content_sha256"}
    if not isinstance(decision, dict) or set(decision) not in (required, required | {"version_only_approval"}):
        raise ValueError("A reviewed release-plan.json with base_tag/version/bump/reason/content_sha256 is required")
    base = decision["base_tag"]
    if not isinstance(base, str) or not re.fullmatch("v" + validate.VERSION_RE, base):
        raise ValueError("Release decision needs a numeric base tag vX.Y.Z")
    if decision["version"] != version or decision["bump"] not in ("patch", "minor", "major"):
        raise ValueError("Release decision must match the TOC and declare patch/minor/major")
    if not isinstance(decision["reason"], str) or not decision["reason"].strip():
        raise ValueError("The agent must record why this semantic increment is appropriate")
    expected = next_version(base[1:], decision["bump"])
    if version != expected:
        raise ValueError(f"SemVer decision requires exactly {expected}, not {version}")
    head, head_version, head_files = snapshot("HEAD")
    if head_version != version:
        raise ValueError("Commit the prepared version before checking release policy")
    tags = git("tag", "--list", "v*").decode().splitlines()
    tags = [t for t in tags if re.fullmatch("v" + validate.VERSION_RE, t)]
    previous = [t for t in tags if t != "v" + version]
    if not previous or base != max(previous, key=lambda t: tuple(map(int, t[1:].split(".")))):
        raise ValueError("Release decision must use the newest previous release tag; fetch all tags")
    base_sha, base_version, base_files = snapshot("refs/tags/" + base)
    if base != "v" + base_version:
        raise ValueError("Baseline tag and its TOC version disagree")
    git("merge-base", "--is-ancestor", base_sha, head)
    result = plan(base_version, head_version, base_files, head_files, decision["bump"])
    if "version_only_approval" in decision:
        approval = decision["version_only_approval"]
        if (not isinstance(approval, str) or not approval.strip()
                or decision["bump"] != "patch" or result["decision"] != "version-only-review"):
            raise ValueError("Owner-approved version-only releases require a documented request, patch increment and unchanged addon content")
    elif result["decision"] != "addon-change":
        raise ValueError("A new addon version requires changed shipped content, not management work")
    if "v" + version in tags:
        tagged_sha, tagged_version, tagged_files = snapshot("refs/tags/v" + version)
        git("merge-base", "--is-ancestor", tagged_sha, head)
        changes = plan(tagged_version, head_version, tagged_files, head_files)
        if changes["content_changes"]:
            raise ValueError("Shipped content changed after this version was tagged; prepare a new version")
    if decision["content_sha256"] != shipped_digest(head_files):
        raise ValueError("Shipped content differs from the agent-reviewed decision; review the full diff again")
    return decision


if __name__ == "__main__":
    print(json.dumps(check_policy(), indent=2))
