# CurseForge publication setup

Project: [ForeverElixirManager](https://www.curseforge.com/wow/addons/foreverelixirmanager),
ID **1780660**. Tags and ZIP filenames use the addon's own version (`vX.Y.Z` and
`ForeverElixirManager-X.Y.Z.zip`). WoW versions are compatibility metadata.

The [CurseForge Upload API](https://support.curseforge.com/support/solutions/articles/9000197321-curseforge-upload-api)
uses author tokens in `X-Api-Token`, a multipart ZIP and JSON metadata. Workflows
use `https://wow.curseforge.com/api`, validate the live version catalog and submit
to `/projects/{projectId}/upload-file`. Redirects are rejected to protect credentials.
An uploaded file ID confirms submission, not moderation or public availability.

## Configure GitHub Actions

In this repository's **Settings → Secrets and variables → Actions**, configure:

| Kind | Name | Value |
|---|---|---|
| Secret | `CURSEFORGE_API_TOKEN` | Author token generated at [CurseForge API Tokens](https://authors.curseforge.com/account/api-tokens), with access to this project |
| Variable | `CURSEFORGE_PROJECT_ID` | `1780660` |
| Variable | `CURSEFORGE_GAME_VERSION_ID` | `17053` |
| Variable | `CURSEFORGE_GAME_VERSION_NAME` | `1.60.1` |
| Variable | `CURSEFORGE_GAME_VERSION_TYPE_ID` | `88568` |

These environment-variable names are local workflow conventions. The actual API
authentication field is **X-Api-Token**. Do not paste the token in source files,
issues, PR comments or chat.

**Monitor Forever versions** checks the stored token and configured catalog tuple
without uploading. Run it on main with **notify** unchecked; it may also rebuild
the addon if a newer version is detected. Publication performs its own catalog
check before creating a tag. Neither catalog check establishes upload permission,
moderation or live-client compatibility.

A maintainer can securely provide the token in their local environment and run:

```text
python scripts/curseforge.py --list-versions
```

This performs only `GET /game/versions`. Check the returned entries against the
project's supported Forever versions in CurseForge. Do not substitute the TOC
interface number (16001) for a CurseForge version ID, or select a Classic/retail
entry with a similar name. No Forever numeric IDs are invented or hardcoded here.
The upload validates the ID, exact name and type tuple; the maintainer must first
establish that this tuple denotes Forever. Missing catalog support blocks upload.

## Forever version monitor

`.github/workflows/forever-monitor.yml` provides scheduled detection,
validation and review, independently of addon releases. It uses the existing
token and version variables above; no additional credentials are needed.

- Schedule: 00:23, 06:23, 12:23 and 18:23 UTC on main.
  GitHub schedules can be delayed and can be disabled after repository inactivity;
  this is periodic checking, not an immediate Blizzard release webhook.
- Source: authenticated GET of the CurseForge game-version catalog. The configured
  baseline ID/name/type must match. Only that Forever type is considered; version
  components are compared numerically, independently of catalog order and IDs.
- A newer latest version triggers Lua syntax checks, the existing mocked tests,
  distribution tests and a ZIP rebuild without changing the TOC or addon version.
  A successful ZIP is retained as an Actions artifact for 14 days.
- An issue records the candidate, workflow link and rebuild result, including a
  failed rebuild. It requests actual client evidence and any needed change PR.
  This workflow never commits, tags, creates releases or uploads to CurseForge.
- Existing open AND closed issues are checked with pagination and an exact hidden
  marker. Preserve that marker. The same version is not reported/rebuilt again;
  if several versions appeared between runs, only the newest gets a review issue.
  Runs are serialized, and the report job rechecks before creating an issue.
- Errors fetching or validating catalog/issue data fail the workflow. They do not
  mean "no update". Inspect failed Actions runs; the detector does not create a
  speculative compatibility issue without a valid catalog observation.

Manual operation: select **Monitor Forever versions**, branch **main**, and leave
**notify** unchecked for GET-only detection plus a rebuild if a newer untracked
version exists. Check notify to allow issue creation. Manual runs on other branches
are skipped. GitHub issue-write permission is limited to the report job; the
CurseForge token is only exposed to the catalog GET step.

This monitors CurseForge version entries, not every Blizzard client build/hotfix.
It may lag the client release, and a hotfix under the same version is invisible.
New type IDs or unexpected version-name formats require manual review. A catalog
entry is not proof of a supported Interface, API or item behavior. Automated
results remain separate from the live-client checklist in VALIDATION.md.

After reviewing a new version, update the three configured version variables
together only when supported by client evidence. The monitor never updates them.
Closing the issue intentionally suppresses repeats, including after a failed build.
For another build, rerun the relevant failed job or run `python scripts/validate.py`
locally; record the result in the existing issue. Do not delete issues to force
duplicate reports. Disable the monitor in
Actions to stop scheduled runs; this has no effect on the installed addon.

References: [catalog API](https://support.curseforge.com/support/solutions/articles/9000197321-curseforge-upload-api),
[GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
and [issue pagination/state](https://docs.github.com/en/rest/issues/issues#list-repository-issues).

## Release a prepared version

Use **Actions → Release addon (Alpha, Beta or Release) → Run workflow**:

1. Select branch `main`.
2. Select `alpha`, `beta` or `release`.
3. Tick `approve_release` and run the workflow. This authorizes the tag, GitHub
   publication and automatic CurseForge publication after moderation together.

Without the approval checkbox, GitHub still accepts the manual run. It finishes
with a notice that the release was skipped; validation and publication jobs do not
run. No source checkout, build, tag, release or upload occurs. Such a request also
cannot displace an approved release waiting in the publication queue.

The agent determines patch/minor/major from the shipped changes, prepares the
version and release notes, and records the decision in release-plan.json. The owner
does not enter a version or classify code changes. The workflow automatically uses
the prepared version. A blocking release-policy check verifies the exact increment,
source digest, baseline tag and immutable released content. Any later shipped
change invalidates the recorded decision until the agent reviews it again.

| Selected type | GitHub | CurseForge |
|---|---|---|
| Alpha | Prerelease, not latest; title includes Alpha | Alpha, publish after moderation |
| Beta | Prerelease, not latest; title includes Beta | Beta, publish after moderation |
| Release | Stable release, marked latest | Release, publish after moderation |

This mapping follows the explicit selection even for 0.x versions. Channel and
semantic version are separate: the numeric tag remains `vX.Y.Z`. A different type
does not permit another upload under an existing tag. Promotion of an existing
file is a separate reviewed metadata operation, not another run of this workflow.

The pipeline pins the workflow commit, validates source/tests and the allowlisted
ZIP, then verifies the configured Forever catalog tuple before creating anything
on GitHub. It creates the tag on that exact commit and publishes the selected
version's release notes and ZIP. It downloads the GitHub asset and compares bytes
before submitting to CurseForge. `isMarkedForManualRelease=false` requests automatic
publication once CurseForge approves the file; an upload response is still not
proof that moderation or public availability is complete. The run summary records
the source commit, ZIP hash and CurseForge file ID.

The GitHub token receives contents:write only in the publication job. The
CurseForge secret is exposed only to its publication step. Approved runs share
a concurrency group. This is the only publication workflow; tag pushes, PRs,
schedules and GitHub release events do not trigger publication.

## Partial failure and recovery

The pipeline never retries an upload or replaces an existing tag/release. A
second run stops if the tag exists, even if the first run failed later. This is
intentional: a timeout after the CurseForge POST may hide an accepted upload.

- Before tag creation: correct the reported validation/configuration error, then
  start a new approved run.
- Tag/GitHub release exists but CurseForge upload did not run: preserve the tag
  and exact ZIP. Inspect the failed step and repair missing GitHub assets only
  from the validated artifact; do not overwrite an existing asset. The agent must
  verify tagged source, release type and exact asset bytes, then obtain approval
  for a targeted recovery using `scripts/curseforge.py --approve-upload` with the
  existing tag, verified archive and release notes. Use `--publish-on-approval`
  only when automatic publication is included in that recovery approval.
- CurseForge upload was attempted or the result is uncertain: inspect project
  files and the run logs first. If a file exists, use that file. Do not rerun the
  POST or delete/recreate the GitHub tag to bypass the duplicate guard.

## Agent release preparation

The agent reviews the entire shipped diff against the latest release tag and
selects patch for compatible fixes, minor for compatible features or major for
breaking contracts, including before 1.0. See [AGENTS.md](../AGENTS.md). Management
changes preserve the addon version and existing release decision. Packaging changes
require comparing ZIP contents; published assets must never be replaced.

On a clean development branch, fetch tags and use the latest release as the base.
For example, when the latest release is v0.4.0 and the change is a compatible feature:

```text
git fetch origin --tags
python scripts/prepare_release.py --base v0.4.0 --bump minor
python scripts/prepare_release.py --base v0.4.0 --bump minor --notes-file /path/to/notes.txt --reason "Add compatible functionality" --apply
```

Keep the notes input outside Git or under ignored `dist/`. The command previews by
default; applying writes the TOC, CHANGELOG and release-plan.json without committing,
tagging or publishing. Review and commit those files, then run:

```text
python scripts/release_policy.py
python scripts/validate.py
python -m unittest discover -s tests -p "test_*.py"
```

The policy checks the exact version increment, baseline, source digest and tagged
content. The agent remains responsible for interpreting behavioral compatibility.

## Moderation and app visibility

CurseForge's [project submission guide](https://support.curseforge.com/support/solutions/articles/9000197241-creating-and-submitting-a-project)
describes moderator review and the requirement for an approved Release file before
a project syncs to the app. Upload success and Alpha/Beta classification do not
establish app visibility or live-client compatibility.
