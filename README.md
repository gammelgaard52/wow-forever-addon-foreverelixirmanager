# ForeverElixirManager

**One macro for your next missing elixir or scroll in World of Warcraft: Forever.**

![ForeverElixirManager artwork](assets/logo.jpg)

The addon checks six ranked effect groups first, then discovers additional elixirs
and scrolls directly from your bags using the client's consumable categories.
This includes Elixir of Minor Strength and new item IDs without a fixed allowlist.
Press your macro to use the next eligible item on yourself. Nothing is consumed
automatically, and selection pauses in combat. Enable or disable groups if needed.

**Experimental 0.6.0 local test candidate**, retaining Forever interface **16001**.
Buff recognition uses assumed names: English item names for the original groups,
and client item/use-spell names for discovered items. If an active buff is shown as
missing, disable that group. Live client compatibility remains **NOT VERIFIED**;
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

No aura-ID setup is needed. Outside combat, `/fem status` shows the next item;
press the macro once to attempt one use. The macro has no dynamic item tooltip.
If the client rejects the click, use the normal item action bar.

For the local test build, extract `dist/ForeverElixirManager-0.6.0.zip` into
`Interface/AddOns/`, replacing the previous addon folder while the client is closed.
The macro above is unchanged. With Elixir of Minor Strength in your bags, run
`/fem list` and `/fem status` outside combat, press the macro, then run `/fem buffs`.
Confirm that one item is used and its buff is recognized before pressing again.
Repeat with a stat scroll while targeting another unit: the scroll should buff you.
If it fails, report the exact status/buffs output, item name and client build.

## Commands

| Command | Effect |
|---|---|
| `/fem` | Refresh and show help |
| `/fem list` | Show eight group choices and discovered bag items (cached in combat) |
| `/fem enable N` / `/fem disable N` | Turn effect group N on or off, including all ranks |
| `/fem buffs` | Show tracked buffs as active or missing |
| `/fem status` | Show the next item or an unavailable-data diagnostic |

The fixed group order is: **1** Fortitude, **2** Cleric's,
**3** Mageblood, **4** Spirit, **5** Intellect, **6** Defense,
**7** Other elixirs, **8** Scrolls.
For example, `/fem disable 2` skips every Cleric's rank. Choices are saved per
character; configuration changes are unavailable in combat. Existing disabled
choices also disable higher ranks when upgrading from 0.4.0.

Within the original six groups, unavailable or over-level ranks fall back to the next eligible
rank. A recognized equal/stronger active buff blocks weaker replacements; a weaker
buff allows a manual upgrade. Strength follows the listed effect, not item level.
See the [supported ranks and evidence](docs/ELIXIR_RANKS.md).

Groups 7 and 8 are enabled by default, including on upgrades. They cover all carried
items classified by the client as Consumable/Elixir or Consumable/Scroll, with
readable item data and a use-spell name. They use ascending item ID order, not a
strength ranking. Any active matching item/use-spell name prevents reuse, including
other ranks sharing that name; automatic rank upgrades are not inferred for these
items. `/fem disable 7` or `/fem disable 8` skips the corresponding category.
The original group choices still apply to their items, which cannot reappear in 7.

## Limitations and upgrades

Item categories establish discovery, not verified buff behavior. Use-spell names
can differ from the resulting buff; they are a heuristic, not an aura-ID mapping.
The original six groups still assume English item labels. Cross-item stacking,
class buffs, combined effects and different names for ranks are not resolved.
Groups 7/8 do not guarantee the strongest item or prevent replacement of an
unrecognized buff. Disable affected groups with `/fem disable N`.

Flasks, potions, recipes, enchantments and quest items in other client categories
are excluded, even if their names contain "elixir" or "scroll". Discovery covers
the backpack and equipped bags, not the bank. Missing item/use-spell data or
insufficient level prevents selection; cooldowns and other restrictions remain
the client's responsibility. After an item-data load failure, reload once data
is available. `/fem buffs` shows the assumed use-spell names for discovered items.

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
Changes visible outside GitHub count toward the addon version and release notes,
including the installation package and CurseForge display names, notes, links and
metadata in administration or on the public project page. GitHub-only changes,
such as workflow updates, tests and repository documentation, do not bump the version.
The [repository instructions](AGENTS.md) define the version policy.

PR checks include a blocking **release-policy** check against the agent's
`release-plan.json` decision, plus an advisory **Addon version assessment** in the Actions
job summary. GitHub-only changes keep the current version. Addon and publication
changes get a proposal; packaging changes also require ZIP review. Nothing is written
or released by this check. Locally: `python scripts/version_plan.py --base origin/main`.
Use `--bump minor` or `--bump major` when reviewing features or breaking changes.

For reviewed release preparation, `scripts/prepare_release.py` can update the TOC
and prepend supplied release notes and record the semantic decision on a clean
branch. It compares against the latest release tag, defaults to a preview, and
never commits, tags or uploads.
GitHub-only changes do not write a new version. See the
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
