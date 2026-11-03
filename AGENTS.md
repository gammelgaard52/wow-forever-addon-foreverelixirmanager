# Repository Agent Instructions

## Purpose
Maintain the **ForeverElixirManager** World of Warcraft: Forever addon. This repository does not control a running WoW client or CurseForge publication. Never assume a Classic Era API or item value applies unchanged to Forever.

## Branch workflow
- Use a dedicated branch and pull request for improvements by default.
- Commit directly to `main` only when explicitly requested.
- Preserve unrelated edits; do not merge a PR, publish to CurseForge, or deploy an addon without instruction.
- The approved release workflow creates tags `vX.Y.Z`. Tag pushes alone do not
  publish. Do not create a release tag without approval.
- The manual `publish.yml` workflow combines tag creation, GitHub publication and
  CurseForge submission only after the owner selects Alpha/Beta/Release and
  explicitly approves the run. CurseForge then publishes after moderation. Building
  or merging this automation does not authorize executing a release.
- Addon versions describe changes to the installed addon. Management-only changes (workflows, scripts, tests, documentation, agent instructions, issue templates and unshipped artwork) must not bump the TOC version, add an addon release-note section, create a release tag or publish a new addon package.
- CI may rebuild and validate the existing version without releasing it. Version automation must compare shipped content and require an agent-reviewed release decision; commit types or merges alone must not trigger a version bump. Packaging changes require comparing actual ZIPs; never replace a published asset with different bytes.
- The agent owns semantic classification: inspect the complete shipped diff since
  the previous release and choose patch for compatible fixes, minor for compatible
  features, or major for breaking behavior/settings/command contracts. Record the
  highest applicable impact and its reason in release-plan.json, prepare the exact
  next version and notes, bind the decision to the shipped content digest, and run
  release_policy.py. Do not ask the owner to classify
  code changes. Alpha/Beta/Release is their distribution choice, independent of SemVer.
- Apply the same patch/minor/major contract before 1.0. Preserve an already prepared
  version when its increment still covers all unreleased changes.

## Before changes
1. Read this file, README, TOC, Lua source, and relevant workflow files.
2. Review the current branch and diffs; prefer minimal changes.
3. Verify spell/item IDs, aura names and client API behavior from Forever sources or label assumptions clearly.
4. Respect protected-action restrictions: no automated item use, combat decisions, input broadcasting or attempts to circumvent secure execution.
5. Before changing client behavior, record the relevant Forever source/build and distinguish source evidence, observed client behavior and assumptions. If evidence is missing, keep the uncertainty visible rather than inventing compatibility. Management-only changes do not require unrelated client research.
6. Implement only the requested behavior with the simplest adequate code. Prefer the existing lightweight approach; add abstractions, dependencies or configuration only for a demonstrated need.

## Validation
- Review the full patch and run syntax/static checks where tooling exists.
- Confirm the TOC lists included files and the interface number matches the intended Forever client.
- Verify that the release ZIP has one top-level `ForeverElixirManager/` folder and no repository metadata or credentials.
- Test secure-button click behavior, bag refresh, aura names, item priority and combat lockdown in-game before claiming compatibility.
- Document PASS / FAIL / NOT VERIFIED clearly; CI cannot replace in-game validation.
- Check GitHub Actions results after pushing when a workflow should run.

## Security and distribution
- Keep permissions minimal (GitHub Actions releases require contents:write).
- Do not commit credentials, tokens, personal logs or local account information.
- Assets should be original or appropriately licensed; never commit fonts.
- Use versioned tags for GitHub releases. Publication requires explicit approval
  through the manual release workflow and configured credentials. Never treat a
  merge or monitor rebuild as approval. Any partial-failure recovery needs explicit
  approval after inspecting the existing tag, release and upload state.

## Documentation
- Keep only maintained source, assets, tests, configuration and operational documentation
  in Git. Keep issue priorities and progress in GitHub; do not add repository work logs,
  copied issue reports or duplicate project descriptions. Use ignored `dist/` or a
  system temporary directory for downloads, build output and scratch files.
- Keep installation, macro setup, commands, limitations and rollback instructions in README.
- Describe API assumptions separately from confirmed client behavior.
- Include release notes for user-facing changes; keep core addon lightweight.
- Report what changed, what was actually validated, and what remains to be tested.
