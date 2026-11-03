# Issue priorities and version policy

Reviewed on 3 November 2026 against main at `c321554` and all five open issues.
Priorities below are recommendations; issue states have not been changed.

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

No automatic semantic-version writer is currently installed. Keep this separation
when implementing #7. Acceptance tests for future automation must cover docs-only,
CI-only, tests-only and tooling-only changes with unchanged output producing no
bump, as well as mixed changes and packaging changes that alter shipped output.
An eligible version proposal still requires release approval.

## First automated CurseForge upload

The token/catalog check passed and the owner reports manual 0.3.0 approval.
On this review date, GitHub has no release objects and no remote tags. The upload
workflow requires both an approved tag and its published GitHub ZIP, so it cannot
yet submit 0.4.0. No new version is needed for the management work in this review.

Recommended order:

1. Record the 0.4.0 client checklist results. Local validation currently passes
   18 mocked Lua scenarios and 12 Python distribution tests, but is not a live test.
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
