# ForeverElixirManager

**Manual elixir selection for World of Warcraft: Forever.**

![ForeverElixirManager artwork](assets/logo.jpg)

A lightweight, priority-based addon that checks player buffs, bag inventory and
level requirements, then prepares one elixir for a manual secure click. Nothing
is consumed automatically. Originally intended for a Discipline Priest supporting
a Protection Paladin; configuration is independent for every character and class.

**Experimental 0.3.0.** The target is Forever beta interface **16001**. Compatibility
with your current build, secure clicks and elixir stacking are **NOT VERIFIED**.
There are no preset aura mappings: unmapped items never queue. See the
[evidence ledger and in-game checklist](docs/VALIDATION.md).

## Installation and first setup

Download a versioned [GitHub release](../../releases) when one has been approved.
Extract it under the intended Forever client's `Interface/AddOns/` directory:

```text
ForeverElixirManager/
  ForeverElixirManager.toc
  ForeverElixirManager.lua
  LICENSE
```

For development, copy the two source addon files into that directory. Do not
install the whole repository ZIP. Check the client build before enabling it.

1. Run `/fem list` to see the candidates and current priority numbers.
2. In a controlled out-of-combat test, inspect `/fem buffs` before and after using
   an elixir manually from a normal bag or action-bar slot. Record its actual aura
   spell ID. Item-use spell IDs are not necessarily aura IDs.
3. Set `/fem aura N SPELLID` using the observed ID. This is a user-supplied mapping,
   not proof of compatibility. Verify the item ID, level and replacement rules.
4. Add any observed stronger/replacement effects using `/fem block N SPELLID`.
   Disable entries with unresolved interactions. Unknown conflicts are not detected.
5. Check `/fem status`, then test this macro with an inexpensive elixir:

```text
#showtooltip
/stopmacro [combat]
/click ForeverElixirSecureBtn LeftButton 0
```

Bind the macro to a key. The explicit release phase matches `AnyUp` and the
button's `useOnKeyDown=false`. The secure state driver also disables the prepared
item action during combat. These protections require live testing, including with
other addons enabled. If the client rejects the click, use your normal item action
bar and report the failure; do not try to bypass the restriction. The macro does
not provide a dynamic tooltip for the selected item; use `/fem status`.

## Commands

`N` is the current priority position shown by `/fem list`, not an item ID. Positions
change after a move. All settings mutations are rejected during combat.

| Command | Effect |
|---|---|
| `/fem` or `/fem help` | Refresh selection and display help |
| `/fem list` | Priority, candidate IDs, enabled state, mapped aura and eligibility reason |
| `/fem status` | Refresh and display the next item, or combat/unavailable status |
| `/fem buffs` | Inspect readable player aura names and spell IDs outside combat |
| `/fem enable N` / `/fem disable N` | Include/exclude a candidate |
| `/fem move N POSITION` | Move a candidate to a new priority position |
| `/fem aura N SPELLID` | Record an observed aura ID; use 0 to clear it |
| `/fem block N SPELLID` | Skip this elixir while that conflicting/stronger aura is active |
| `/fem unblock N SPELLID` | Remove a blocking rule |
| `/fem reset` | Reset this character's priority, toggles, aura mappings and blockers |

Defaults, in order: Elixir of Minor Fortitude (2458), Minor Cleric's Elixir
(250330), Minor Mageblood Elixir (250339), Elixir of Minor Spirit (250344), Elixir
of Wisdom (3383), Elixir of Lesser Defense (3389). These IDs remain candidates.

Settings use `SavedVariablesPerCharacter`. On first use, legacy account-wide
on/off settings are copied once into that character's settings. The old account
table is preserved for rollback; subsequent changes do not affect other characters.

## Selection and limitations

Outside combat, selection skips disabled/unmapped entries, active mapped auras,
configured blocking effects, absent items, unknown item/spell data and items above
the player's level. The first eligible entry wins; otherwise the queue clears.
The addon reads localized item names and required levels from `C_Item.GetItemInfo`
and matches auras by spell ID. It excludes bank, reagent-bank and account-bank
counts. It waits for relevant events and coalesces event bursts into one refresh.

Missing or restricted aura data stops selection. No Classic API fallback, guessed
buff name, guessed rank/stacking group or combat aura inspection is used. Cache
failures skip the affected item; `/fem list` explains the result. A failed item-data
request is not retried in a loop; retry after client data becomes available or reload.
Cooldowns and other use restrictions remain the client's responsibility. The
prepared queue is a snapshot; verify your status before clicking, especially
immediately after consumption or inventory changes. Mock tests cannot establish
engine event timing, taint safety or whether the invisible button is clickable.

## Development and releases

Read [AGENTS.md](AGENTS.md), [release notes](CHANGELOG.md), and the
[validation guide](docs/VALIDATION.md). Run `python scripts/validate.py` and
`python -m unittest discover -s tests -p "test_*.py"`. Use Lua 5.1 or the optional
Windows Lupa runner described in the validation guide.

Pull requests run Lua syntax checks, mocked tests, TOC checks and actual archive
validation. Only explicitly approved `vX.Y.Z` tags publish GitHub releases; the
tag must match the TOC version. A manual release-workflow run only builds an
artifact. Packaging includes only the two addon files and the MIT license under
one `ForeverElixirManager/` directory.

CurseForge publication is separate and manual. The prepared workflow requires an
existing non-draft GitHub release, explicit upload authorization and configured
credentials/version identifiers. See [CurseForge setup](docs/CURSEFORGE.md).
Neither normal commits nor pull requests upload to CurseForge.

## Rollback

Exit the game. Back up this addon's account and per-character SavedVariables files
under the client's `WTF` directory. Replace only `Interface/AddOns/ForeverElixirManager`
with a previously validated release. Version 0.2.0 reads the preserved account-wide
settings and does not understand 0.3.0's character mappings. To stop immediately,
disable the addon in the character-selection AddOns menu. Do not delete the whole
WTF directory. Restore only this addon's backed-up files while the game is closed.

## License

Copyright © 2026 Martin Gammelgård Rasmussen. Released under the **[MIT License](LICENSE)**,
including original repository artwork. World of Warcraft and Blizzard are
trademarks of their respective owners. This project is not affiliated with Blizzard Entertainment.
