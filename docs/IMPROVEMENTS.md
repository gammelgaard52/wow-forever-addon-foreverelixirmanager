# Issue priorities and version policy

Reviewed on 3 November 2026, including merged PRs #11 and #12. Each issue was
checked against existing code before implementation. Issues #5, #3 and #8 are now
closed with evidence. The follow-up implementation for #4 and #7 is described below.

## Prioritized issues

| Order | Issue | Addon relevance | Management relevance | Recommended next step |
|---|---|---|---|---|
| 1 / P1 | [#5: Forever research and simple code](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/issues/5) | High: prevents incorrect API/item assumptions and unnecessary complexity | High: guides every future change | Existing instructions already require Forever evidence. Make source/build evidence, visible uncertainty and minimal implementation explicit in AGENTS.md; this documentation change does that. |
| 2 / P1 | [#8: CurseForge integration](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/issues/8) | Indirect: reliable distribution | High: completes the release path | Connection/catalog check is PASS. Finish a separately approved first upload, record its file ID and verify the downloaded artifact. Keep public release a separate decision. |
| 3 / P2 | [#4: Forever test frameworks](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/issues/4) | High: better regression coverage | Medium: less repeated manual work | Evaluate a small development-only prototype against the existing 18 Lua scenarios. Keep it only if it detects a concrete gap. Do not replace actual secure-click/client testing with emulator results. |
| 4 / P2 | [#7: Semantic version management](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/issues/7) | Low direct impact | High once releases become frequent | Establish the policy below now. Later automate a version proposal for shipped changes; do not auto-tag every merge or infer releases solely from commit prefixes. |
| 5 / P3 | [#3: New WoW version lookup](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/issues/3) | Medium: compatibility awareness | Medium | Start with a read-only notification or review PR for Forever updates. Do not automatically change Interface, claim compatibility or publish. Lua packaging is not recompilation for a new WoW client. |

The most important addon release prerequisite is outside these issue titles:
record real client results for the current 0.4.0 behavior. Secure macro clicks,
combat transitions, actual buff names, item priority, bag refresh and settings
persistence remain NOT VERIFIED. Use the [existing checklist](VALIDATION.md).
Neither a new test framework nor a successful upload proves these work.

## Execution update

- #5: completed by PR #11; the requested research and simplicity rules already
  exist in AGENTS.md. No duplicate implementation was needed.
- #3: completed by PR #12. The first live monitor check
  ([run 41700402569](https://github.com/gammelgaard52/wow-forever-addon-foreverelixirmanager/actions/runs/41700402569))
  passed with no new untracked version; rebuild and issue creation were skipped.
- #4: wowlua 0.13.8 was evaluated against a disposable copy. The two original
  failures were caused by advancing timers without running frames. Corrected
  tests and an independent clock control now pass all five probes, including
  bag removal and combat exit. Keep this supplementary suite optional; see
  VALIDATION.md for source evidence and the remaining real-client limitations.
- #7: PR CI now calculates an advisory semantic-version proposal from committed
  installed content, preserving versions for management-only changes. A local
  preparation command now applies a reviewed proposal and supplied notes on a
  clean branch, with no automatic commit/tag/publication. See below.
- #8: the upload path and credentials already exist. On 3 November the owner
  explicitly authorized releasing 0.4.0 as Alpha without live-client testing,
  because they cannot test the game yet. The upload succeeded (file 9426340) and
  #8 is closed with run/ZIP evidence. Moderation and manual publication remain
  external follow-up; this is not a client compatibility claim.

## Test framework evidence for #4

- [WoWUnit](https://github.com/Jaliborc/WoWUnit/blob/master/README.md) runs unit tests
  on game events and supports temporary mocks. Its README does not establish
  compatibility with our exact Forever build; that needs a development test.
- [wowlua](https://wowlua.dev/changelog) documents an emulated client, a test runner
  and Forever/camelot support. This is a candidate for a bounded experiment,
  not verified execution of this addon. Pin a released version and measure the
  benefit before adding it to CI or adopting any new language/build workflow.
- Keep test tooling outside the distributed addon. The current Lua 5.1 harness
  and Python distribution checks already cover logic and packaging. Additional
  tools should target missing evidence, not duplicate those checks.

## Addon version policy

The TOC version identifies the installed addon, not the repository revision.
Management revisions are identified by commits, PRs and workflow runs.

| Change | Addon version consequence |
|---|---|
| Workflows, scripts, tests, docs, AGENTS.md, issue templates or unshipped artwork only | No version bump, addon changelog section, release tag or publication |
| Lua behavior, bundled data/assets, load metadata or supported Interface changes | Review a version proposal and addon release notes; validate before release |
| Packaging/license changes that alter the distributed ZIP | Review the distribution impact explicitly; do not silently replace an existing release asset |
| Rebuild/check of unchanged shipped content | Same addon version; CI validation is not publication |

The current ZIP contains only the addon Lua file, TOC and LICENSE. Compare actual
shipped content as well as paths: a packaging-script change can affect the output.
Unchanged addon content must not receive a new version just because management
files changed. Never overwrite an existing published version with different bytes.
An already prepared, unreleased version can be released later without another
bump solely to incorporate management work.

Current workflow separation:

- `validate.yml`: PRs and pushes to main run checks, without changing versions,
  creating tags or publishing.
- `release.yml`: manual dispatch builds an artifact only. An explicitly approved
  `vX.Y.Z` tag push publishes the GitHub release after checking TOC/tag agreement.
- `curseforge.yml`: manual dispatch only; check mode is read-only. Upload requires
  main, upload mode, explicit approval and an existing GitHub release.
- `publish.yml`: the recommended combined release path, manual dispatch only on
  main with a prepared TOC version, selected Alpha/Beta/Release and approval. After
  validation it creates the tag and GitHub release and submits to CurseForge for
  automatic publication after moderation. It never writes addon versions and
  rejects already-tagged versions or management-only version increments.

`scripts/version_plan.py` compares the PR base/head commits and writes an Actions
summary without modifying files. It compares the addon directory and LICENSE,
normalizing only the TOC Version line. A newer already-prepared version is kept;
regressions fail. A version-only change requests intentional release-preparation
review. Unchanged installed content produces no bump. Changes to the package
builder or release workflow require actual ZIP review, not an automatic increment.

The advisory patch proposal is a minimum, not inferred compatibility. The agent
must inspect all shipped changes since the previous release and select the highest
applicable impact: patch for compatible fixes, minor for compatible features, major
for breaking behavior/settings/command contracts. This repository uses that explicit
contract even before 1.0. The owner chooses distribution type, not code semantics.
The preparation tool supports
`--bump patch|minor|major`. It does not infer these semantics from commit messages.
Tests use real temporary Git histories to cover management-only and mixed changes,
and exercise existing bumps, packaging changes, additions/deletions and regressions.
The assessment job is advisory. The **release-policy** CI job and both publication
paths enforce the recorded decision: the base tag must be the newest prior tag,
the TOC and release-plan.json must agree, and the version must be exactly the
declared patch/minor/major increment. The decision includes a digest of all shipped
content, so later addon edits require a new agent review even before the tag exists.
Version skips, regressions, management-only
bumps, missing decisions and changes to shipped content under an existing tag
fail. This checks the agent's recorded semantic judgment; it cannot infer whether
arbitrary Lua changes are breaking. The agent remains responsible for that judgment.

The preparation command writes files only with `--apply`; tags and publication
remain separate. Management-only edits preserve the current decision and version.

## Reviewed release preparation

After committing the intended addon changes on a dedicated branch, fetch release
tags and compare with the latest reachable release (currently `v0.4.0`):

```text
git fetch origin --tags
python scripts/prepare_release.py --base v0.4.0 --bump minor
python scripts/prepare_release.py --base v0.4.0 --bump minor --notes-file /path/to/reviewed-notes.txt --reason "Add compatible rank selection" --apply
git diff -- ForeverElixirManager/ForeverElixirManager.toc CHANGELOG.md release-plan.json
python scripts/validate.py
python -m unittest discover -s tests -p "test_*.py"
```

The agent chooses patch/minor/major by reviewing behavior; the tool does not infer
semantics from commit titles. Supply the release-note body without a version
heading in a file outside the working tree (or an ignored development location).
The preview writes nothing. Applying writes the TOC version, a new CHANGELOG
section and release-plan.json with the reviewed reason, for a PR review. It never
commits, pushes, tags or publishes.

Guards require a clean working tree, matching base tag/TOC, an ancestor baseline
with no newer reachable release tag, and an unused target tag. Application also
requires a named branch other than main and nonempty reviewed notes. An already
prepared newer version is kept. Management-only, version-only and packaging-only
changes produce a decision for review without writes; packaging changes still
need explicit ZIP comparison. Fetching tags is necessary because this local tool
cannot detect remote tags it has not fetched.

## First automated CurseForge upload

The token/catalog check passed and the owner reports manual 0.3.0 approval.
At the initial review there were no GitHub releases or remote tags. The owner
subsequently approved 0.4.0 as Alpha: tag/prerelease `v0.4.0` now exists and the
automated upload returned CurseForge file 9426340. See [the recorded result](CURSEFORGE.md).
No additional addon-version bump was made for management work.

Recommended order:

1. Record the 0.4.0 client checklist results, or document an explicit experimental
   distribution exception. The owner approved that exception on 3 November 2026.
   Local validation passes mocked Lua and Python tests, but is not a live test.
2. Approve the existing 0.4.0 candidate and the specific `v0.4.0` tag separately.
   Inspect the generated GitHub release and ZIP after release CI succeeds.
3. Approve one upload to project 1780660 with tag `v0.4.0`, type `alpha`, and
   manual release enabled. This submits a real file for moderation; it is not
   a dry run. Do not duplicate the manually uploaded 0.3.0.
4. Record the returned file ID; check version 1.60.1, Alpha classification,
   manual-release status and downloaded ZIP contents before considering publication.
   On an uncertain response, inspect project files before any retry.

The [CurseForge Upload API](https://support.curseforge.com/support/solutions/articles/9000197321-curseforge-upload-api)
documents a real multipart upload and a manual-release flag, but no upload dry-run
parameter. A connection check has already tested authentication. The next useful
integration test is therefore a real approved candidate, not a dummy version.
See [publication setup](CURSEFORGE.md) for exact workflow inputs and identifiers.
