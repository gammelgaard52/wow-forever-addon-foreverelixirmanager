# ForeverElixirManager

**One macro for your next missing elixir in World of Warcraft: Forever.**

![ForeverElixirManager artwork](assets/logo.jpg)

The addon checks your buffs and bags in a fixed order and prepares one elixir.
Press your macro to use it. Nothing is consumed automatically, and selection
pauses in combat. Enable or disable individual elixirs if needed.

**Experimental 0.4.0**, targeting Forever beta interface **16001**. The original
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
| `/fem list` | Show the fixed list and on/off choices |
| `/fem enable N` / `/fem disable N` | Turn elixir number N on or off |
| `/fem buffs` | Show tracked buffs as active or missing |
| `/fem status` | Show the next elixir |

The fixed order is: **1** Minor Fortitude, **2** Minor Cleric's,
**3** Minor Mageblood, **4** Minor Spirit, **5** Wisdom, **6** Lesser Defense.
For example, `/fem disable 2` skips Minor Cleric's Elixir. Choices are saved per
character; configuration changes are unavailable in combat.

## Limitations and upgrades

Buff detection uses the original English item labels as exact buff names. Different
aura names, other locales, stronger buffs and replacement effects are not handled.
Disable affected entries with `/fem disable N`. Item IDs and stacking also need
in-game verification. Unavailable client data or insufficient level prevents an
item from being queued; cooldowns and other use restrictions remain the client's
responsibility. After an item-data load failure, reload once data is available.

Upgrading from 0.3.0 keeps on/off choices. Custom priorities, aura mappings and
blockers are no longer used; their saved data is retained for rollback. Older
account-wide on/off choices are copied on first use for each character.

## Development

Run `python scripts/validate.py` and
`python -m unittest discover -s tests -p "test_*.py"`.
See [release notes](CHANGELOG.md), [validation](docs/VALIDATION.md) and
[repository instructions](AGENTS.md). CI tests the Lua logic and installation ZIP;
it cannot verify actual secure clicks or client behavior.

GitHub releases require explicitly approved version tags. CurseForge publishing
is separate; see [publishing setup](docs/CURSEFORGE.md).

## Forever version monitoring

After merge to main, **Monitor Forever versions** checks CurseForge's configured
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
