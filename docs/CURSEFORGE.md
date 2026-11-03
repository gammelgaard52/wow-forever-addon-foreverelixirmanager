# CurseForge publication setup

Project: **1780660**, ForeverElixirManager. The owner reports that 0.3.0 was
uploaded manually and approved. Do not upload another copy of 0.3.0.
The repository secret CURSEFORGE_API_TOKEN and project-ID variable are configured.
The first automated upload succeeded on 3 November 2026: addon 0.4.0, Alpha,
target WoW 1.60.1, CurseForge file **9426340**. Future uploads still require explicit approval.

- [GitHub prerelease v0.4.0](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/releases/tag/v0.4.0)
- [Successful upload run 41703210547](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/actions/runs/41703210547)
- [CurseForge file 9426340](https://www.curseforge.com/wow/addons/foreverelixirmanager/files/9426340)

The upload requests manual release after moderation. API acceptance is confirmed;
moderator approval, public availability and a download from CurseForge are not yet
verified. Do not submit this version again. The published GitHub ZIP was downloaded,
checked against the tagged source and allowlist, and compared byte-for-byte by the
upload workflow. Its SHA-256 is
`e91bbe184d72bb96efa5d587155050405422248e8a7c0cffc83b9c685fdd2d71`.

## Supported API

The filename and GitHub tag use the addon's own version. WoW versions are
compatibility metadata, not a replacement for addon versioning. The owner
withdrew the WoW-version filename proposal in issue #13 before any release.

| Addon version | ZIP filename | Target WoW version | Interface | Evidence |
|---|---|---|---|---|
| 0.3.0 | `ForeverElixirManager-0.3.0.zip` | 1.60.1 | 16001 | Manual upload approved, per owner |
| 0.4.0 | `ForeverElixirManager-0.4.0.zip` | 1.60.1 | 16001 | Alpha authorized; actual client compatibility NOT VERIFIED |

The official [CurseForge Upload API](https://support.curseforge.com/support/solutions/articles/9000197321-curseforge-upload-api)
documents author tokens in the `X-Api-Token` header, multipart file submission,
version catalogs, release types and Markdown changelogs. This is the author upload
service, not the separate API-key-based client download API. The workflow uses the
WoW site at `https://wow.curseforge.com/api`, verifies the selected version against
its live catalog and submits to `/projects/{projectId}/upload-file`.

The script sends the ZIP as `file` and JSON as `metadata`. It chooses `alpha`,
`beta` or `release`, includes the changelog, and requests manual release after
moderation. It rejects redirects rather than forwarding credentials elsewhere.
A successful response is an uploaded file ID, not proof of approval or visibility.
**PASS, 3 November 2026:** the authenticated catalog check succeeded in
[GitHub Actions run 41695903589](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/actions/runs/41695903589).
The unique 1.60.1 entry (matching the owner's manually uploaded Forever file)
returned version ID 17053 and type ID 88568. The upload job was skipped.
That catalog run alone did not prove project upload permission. The later
successful file submission recorded above now verifies that permission and the
automated upload path, but not live addon compatibility or public availability.

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
issues, PR comments or chat. No repository security settings are changed by this PR.

To test the stored token without uploading, run **Check or upload to CurseForge**
in GitHub Actions with mode **check** and game_version **1.60.1** (the version
shown on the manually uploaded file). Leave upload authorization unchecked.
This mode performs only an authenticated catalog GET and prints the matching
version variables. It rejects missing/ambiguous version names. It cannot verify
permission to upload to the project, moderation or actual addon compatibility.
The check also works on a reviewed feature branch; uploads remain main-only.

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

`.github/workflows/forever-monitor.yml` implements issue #3 as scheduled detection,
validation and review, independently of addon releases. It uses the existing
token and version variables above; no additional credentials are needed.

- Schedule: 00:23, 06:23, 12:23 and 18:23 UTC on main, after the workflow is merged.
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
For another build, rerun the relevant failed job or manually run **Release WoW
addon** on main (artifact only, no release); record the result in the existing
issue. Do not delete issues to force duplicate reports. Disable the monitor in
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

The agent determines patch/minor/major from the shipped changes, prepares the
version and release notes, and records the decision in release-plan.json. The owner
does not enter a version or classify code changes. The workflow automatically uses
the prepared version. A blocking release-policy check verifies the exact increment,
source digest, baseline tag and immutable released content. Any later shipped
change invalidates the recorded decision until the agent reviews it again.
The current decision is 0.4.0 → 0.5.0, a minor increment for the rank-selection
feature; the management automation does not increment it again.

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
CurseForge secret is exposed only to its publication step. All publication
workflows share a concurrency group. The new workflow explicitly creates the
GitHub release because [tags created with GITHUB_TOKEN do not trigger another
workflow](https://docs.github.com/en/actions/concepts/security/github_token).
There is no push, PR, schedule or release-event trigger for this workflow.

## Partial failure and recovery

The pipeline never retries an upload or replaces an existing tag/release. A
second run stops if the tag exists, even if the first run failed later. This is
intentional: a timeout after the CurseForge POST may hide an accepted upload.

- Before tag creation: correct the reported validation/configuration error, then
  start a new approved run.
- Tag/GitHub release exists but CurseForge upload did not run: preserve the tag
  and exact ZIP. Inspect the failed step and repair missing GitHub assets only
  from the validated artifact; do not overwrite an existing asset. Once verified,
  the existing CurseForge-only workflow can upload that release separately.
- CurseForge upload was attempted or the result is uncertain: inspect project
  files and the run logs first. If a file exists, use that file. Do not rerun the
  POST or delete/recreate the GitHub tag to bypass the duplicate guard.

## Legacy separate publication procedure

The older workflows remain available for connection checks, artifact-only builds
and reviewed recovery. Their behavior is different from the combined workflow:
the old tag workflow marks pre-1.0 as prereleases, and the old CurseForge workflow
still requests manual publication. Use the combined workflow for new releases.

1. Finish the live-client checklist, review the PR, and approve merging separately.
   Exception: the owner explicitly authorized 0.4.0 as an unverified Alpha on
   3 November 2026 because live testing is unavailable. Keep that limitation and
   the unresolved emulator probes in its release notes; do not claim compatibility.
2. Obtain explicit approval for the specific GitHub release tag. Ensure the TOC
   version and release notes agree before creating that tag. Keep an already
   prepared, unreleased addon version when only management files changed; those
   changes do not need a version bump. A tag push runs
   validation and publishes the installable GitHub release archive.
   Pre-1.0 tags create GitHub prereleases and are not marked latest/stable.
3. Obtain separate approval to upload that version to CurseForge. In Actions,
   select **Check or upload to CurseForge**, run from **main**, select **upload**, supply
   the existing release tag and release type, and tick the upload-authorization
   input. An ordinary push, PR, or GitHub release event never runs this workflow.
4. The workflow requires a tag reachable from main and a non-draft GitHub release.
   It validates tagged source, reconstructs the deterministic package, and compares
   it byte-for-byte with the GitHub release asset before exposing the token to the
   upload step. Legacy tags without these scripts/packaging cannot use this path.
5. Review the returned file ID in the project dashboard. The workflow requests
   manual release after moderation; make it public only with publication approval.

Do not re-run a timed-out or uncertain upload without checking the project files:
the API does not document an idempotency key, and another POST can duplicate a file.
Publication workflows serialize all runs, and the script does not retry POSTs.
In the legacy upload-only workflow, the token is scoped to the upload step and
GitHub permissions are read-only.

## Moderation and first submission

CurseForge's [project submission guide](https://support.curseforge.com/support/solutions/articles/9000197241-creating-and-submitting-a-project)
says the first file submits the project for moderator review. Automation does not
bypass that review. Alpha/beta/release classification and review approval are
separate. The guide also says a project needs an approved Release file before it
syncs to the CurseForge app; do not label an untested build Release just for visibility.

The token and all four repository variables are configured. The first authorized
Alpha submission is complete. Future publication still needs an approved version;
the owner must review file 9426340 in the dashboard and publish it after moderation
to make this manually held upload public.
