# Repository Agent Instructions

## Purpose
Maintain the **ForeverElixirManager** World of Warcraft: Forever addon. This repository does not control a running WoW client or CurseForge publication. Never assume a Classic Era API or item value applies unchanged to Forever.

## Branch workflow
- Use a dedicated branch and pull request for improvements by default.
- Commit directly to `main` only when explicitly requested.
- Preserve unrelated edits; do not merge a PR, publish to CurseForge, or deploy an addon without instruction.
- Tags `vX.Y.Z` initiate GitHub release packaging. Do not create a release tag without approval.

## Before changes
1. Read this file, README, TOC, Lua source, and relevant workflow files.
2. Review the current branch and diffs; prefer minimal changes.
3. Verify spell/item IDs, aura names and client API behavior from Forever sources or label assumptions clearly.
4. Respect protected-action restrictions: no automated item use, combat decisions, input broadcasting or attempts to circumvent secure execution.

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
- Use versioned tags for GitHub releases; CurseForge publishing requires a separate explicitly approved workflow and credentials.

## Documentation
- Keep installation, macro setup, commands, limitations and rollback instructions in README.
- Describe API assumptions separately from confirmed client behavior.
- Include release notes for user-facing changes; keep core addon lightweight.
- Report what changed, what was actually validated, and what remains to be tested.
