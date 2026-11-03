# ForeverElixirManager

**One macro for your next missing elixir in World of Warcraft: Forever.**

![ForeverElixirManager artwork](assets/logo.jpg)

The addon checks six effect groups in a fixed order and prepares the strongest
listed elixir you carry and meet the level requirement for.
Press your macro to use it. Nothing is consumed automatically, and selection
pauses in combat. Enable or disable effect groups if needed.

**Experimental 0.5.0 candidate**, targeting Forever beta interface **16001**. The original
English buff names are assumed, not verified. If an active buff is shown as
missing, disable that entry. Live client compatibility remains **NOT VERIFIED**;
see [validation and limitations](docs/VALIDATION.md).

## Installation and macro

Download an approved [GitHub release](../../releases) and extract its
`ForeverElixirManager` folder into your Forever client's `Interface/AddOns/`.
The folder should contain the `.toc`, `.lua` and `LICENSE` files. For development,
copy the two files from this repository's `ForeverElixirManager` folder.

Create a macro, place it on your action bar and bind a key:

```text
#showtooltip
/stopmacro [combat]
/click ForeverElixirSecureBtn LeftButton 0
```

No aura-ID setup is needed. Outside combat, `/fem status` shows the next elixir;
press the macro once to attempt one use. The macro has no dynamic item tooltip.
If the client rejects the click, use the normal item action bar.

## Commands

| Command | Effect |
|---|---|
| `/fem` | Refresh and show help |
| `/fem list` | Show the six effect groups and on/off choices |
| `/fem enable N` / `/fem disable N` | Turn effect group N on or off, including all ranks |
| `/fem buffs` | Show tracked buffs as active or missing |
| `/fem status` | Show the next elixir |

The fixed group order is: **1** Fortitude, **2** Cleric's,
**3** Mageblood, **4** Spirit, **5** Intellect, **6** Defense.
For example, `/fem disable 2` skips every Cleric's rank. Choices are saved per
character; configuration changes are unavailable in combat. Existing disabled
choices also disable higher ranks when upgrading from 0.4.0.

Within each group, unavailable or over-level ranks fall back to the next eligible
rank. A recognized equal/stronger active buff blocks weaker replacements; a weaker
buff allows a manual upgrade. Strength follows the listed effect, not item level.
See the [supported ranks and evidence](docs/ELIXIR_RANKS.md).

## Limitations and upgrades

Buff detection uses English item labels as exact buff names. Different aura names,
other locales, unlisted ranks, class buffs and combined-stat effects are not handled.
Disable affected groups with `/fem disable N`. Item IDs and stacking also need
in-game verification. Unavailable client data or insufficient level prevents an
item from being queued; cooldowns and other use restrictions remain the client's
responsibility. After an item-data load failure, reload once data is available.

Upgrading from 0.3.0 or 0.4.0 keeps on/off choices. Custom priorities, aura mappings and
blockers are no longer used; their saved data is retained for rollback. Older
account-wide on/off choices are copied on first use for each character.

## Development

Run `python scripts/validate.py` and
`python -m unittest discover -s tests -p "test_*.py"`.
See [release notes](CHANGELOG.md), [validation](docs/VALIDATION.md) and
[repository instructions](AGENTS.md). CI tests the Lua logic and installation ZIP;
it cannot verify actual secure clicks or client behavior.

To release a prepared version, run **Release addon (Alpha, Beta or Release)**
manually on `main`, select the type and click **Run workflow** to approve publication. The workflow
uses the version prepared by the agent, validates, creates the tag and GitHub
release, and uploads to CurseForge for automatic publication after moderation.
Alpha/Beta are GitHub prereleases; Release is stable. See
[publishing setup and recovery](docs/CURSEFORGE.md#release-a-prepared-version).
This is the only publication workflow. **Validate addon** runs automatically on
PRs and main; **Monitor Forever versions** performs compatibility checks.
Changes to CI, tests, scripts, documentation or repository management do not bump
the addon version or publish a release. The [repository instructions](AGENTS.md)
define the version policy.

PR checks include a blocking **release-policy** check against the agent's
`release-plan.json` decision, plus an advisory **Addon version assessment** in the Actions
job summary. Management-only changes keep the current version. Installed-content
changes get a proposal; packaging changes require ZIP review. Nothing is written
or released by this check. Locally: `python scripts/version_plan.py --base origin/main`.
Use `--bump minor` or `--bump major` when reviewing features or breaking changes.

For reviewed release preparation, `scripts/prepare_release.py` can update the TOC
and prepend supplied release notes and record the semantic decision on a clean
branch. It compares against the latest release tag, defaults to a preview, and
never commits, tags or uploads.
Management-only changes do not write a new version. See the
[preparation commands](docs/CURSEFORGE.md#agent-release-preparation).

An optional [wowlua test suite](docs/VALIDATION.md#optional-wowlua-tests)
checks startup, commands, bag refresh and combat transitions against Blizzard UI.
It is separate from required CI and cannot establish live-client compatibility.

## Forever version monitoring

**Monitor Forever versions** checks CurseForge's configured
Forever category every six hours. A newer, untracked game version triggers tests,
a rebuild of the existing addon version and a compatibility-review issue with the
result. The ZIP is a temporary Actions artifact, not a release. Addon version,
Interface and publication settings remain unchanged.

Run the workflow manually on main for a check; issue creation is off by default
for manual runs. See [monitor operation and limitations](docs/CURSEFORGE.md#forever-version-monitor).

## Rollback

Exit the game and back up this addon's account and per-character SavedVariables
files under `WTF`. Replace only `Interface/AddOns/ForeverElixirManager` with the
previous release, restoring this addon's saved files if needed. Version 0.2.0 uses
the preserved account-wide choices. To stop using the addon, disable it in the
AddOns menu. Do not delete the whole `WTF` directory.

## License

Copyright © 2026 Martin Gammelgård Rasmussen. **[MIT License](LICENSE)**,
including original repository artwork. World of Warcraft and Blizzard are
trademarks of their respective owners. Not affiliated with Blizzard Entertainment.
