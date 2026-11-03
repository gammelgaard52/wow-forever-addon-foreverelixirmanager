# Assessment and validation

The 0.5.0 candidate adds strongest-eligible-rank selection within the six existing
effect groups. It retains modern item APIs, level checks, per-character toggles,
combat protection and English-name matching. The name matching remains an explicit
assumption, not confirmed client behavior. See [rank evidence](ELIXIR_RANKS.md)
for the 24 supported items, source builds, fallback and equal/stronger-effect policy.
Live-client behavior remains NOT VERIFIED.

## API evidence and limits

The retained Blizzard Forever UI source at commit
[aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16](https://github.com/Gethe/wow-ui-source/tree/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns)
was inspected on 2 November 2026:

- [SecureTemplates.lua](https://github.com/Gethe/wow-ui-source/blob/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua)
  contains the item action, item attribute parsing and useOnKeyDown handling.
- [SlashCommands.lua](https://github.com/Gethe/wow-ui-source/blob/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns/Blizzard_ChatFrameBase/Shared/SlashCommands.lua)
  resolves named buttons for /click, checks access constraints and forbidden
  scripted input, then forwards the requested click phase. The engine may still
  reject a click. Source presence is not proof of successful item use.
- [ItemDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns/Blizzard_APIDocumentationGenerated/ItemDocumentation.lua)
  documents C_Item.GetItemCount with separate bank/reagent/account flags,
  GetItemInfo's fifth result as required level, and GetItemSpell. A use spell
  does not establish the resulting aura ID; the addon does not equate them.
- [UnitAuraDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitAuraDocumentation.lua)
  documents aura queries and secret-value restrictions. The addon does not read
  auras in combat and stops selection when a required value is unreadable.
- [SecureStateDriver.lua](https://github.com/Gethe/wow-ui-source/blob/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns/Blizzard_RestrictedAddOnEnvironment/SecureStateDriver.lua)
  and its SecureHandlerStateTemplate support macro-condition-driven attributes.
  State changes run on the client's next driver update, not synchronously inside
  this addon's event handler. Keep the macro's /stopmacro [combat] guard and test
  transitions; do not assume a zero-latency driver.
- A [client-generated API capture](https://github.com/Atraeau/WoW-Addons/blob/main/docs/api/README.md)
  identifies build 70170 / interface 16001. This supports the retained beta
  target; the installed/current launch build remains NOT VERIFIED.

The existing secure button architecture is retained. A fixed secure state driver
only enables/disables its prepared action for combat. Insecure code never calls
item-use functions or updates protected attributes during combat. pcall contains
ordinary API failures; it does not grant access to protected data or actions.
The invisible button is alpha-zero and off-screen, not explicitly hidden.
Whether the engine permits its macro-triggered click remains NOT VERIFIED.

## Item and aura assumptions

The maintained [rank ledger](ELIXIR_RANKS.md) records all supported items and their
Forever sources. Required levels come from client item data. Each group's original
item ID remains its saved setting key.

Aura recognition assumes the exact English item labels in that ledger. Localized
item names and use-spell names do not establish the resulting aura names. There is
no Classic API fallback or spell-ID mapping. Equal/stronger recognized effects
prevent downgrades; a stronger carried rank may be offered as a manual upgrade.
Disable a group if `/fem buffs` misidentifies its active effect or its replacement
behavior is unverified.

## Automated validation

The 0.5.2 candidate corrects links in the release notes shown on CurseForge;
addon behavior and the client-validation requirements above are unchanged.

Run from the repository root:

```text
python scripts/validate.py
python scripts/validate.py --tag v0.5.2
python -m unittest discover -s tests -p "test_*.py"
```

Use Lua 5.1 on PATH (CI installs lua5.1). Windows can instead install the optional
development dependency with `python -m pip install lupa==2.8`; the runner
explicitly loads lupa.lua51. Nothing is bundled with the addon.

The Lua harness covers missing/present buffs and items, priorities, level changes,
fixed-order toggles, bag/aura events, combat, secure attribute updates, startup,
per-character persistence/migration, ignored legacy configuration, invalid/missing
APIs, secret-value rejection, item-cache completion and event coalescing.
Secure state snippets are executed in a mock, not a real protected environment.
Python validates exact TOC entries, metadata, tag/version agreement and actual ZIP
members/bytes. The package is an allowlist with one ForeverElixirManager/ root;
LICENSE is included to satisfy MIT redistribution requirements.

GitHub Actions reports current results on each pull request. Do not execute
release/upload workflows merely to test publication. Passing automated tests does
not verify real secure clicks, combat transitions, item/aura data, stacking or taint.

## Optional wowlua tests

The supplementary suite uses [wowlua v0.13.8](https://github.com/DomenikIrrgang/wowlua/releases/tag/v0.13.8)
and Blizzard UI to test startup, commands, bag refresh, combat transitions and
frame scheduling. It remains outside required CI and the distributed addon.
The reviewed Windows x86_64 ZIP has SHA-256
`a150e84df47d15e3878624cd3137afa20f15165aff4d3e07f6ce604208e22ec4`.

Run with that binary installed outside the repository:

```text
python scripts/probe_wowlua.py --binary /path/to/wowlua
```

The runner requires exactly 0.13.8, creates a disposable addon copy, enables the
Blizzard UI and runs `tests/wowlua/*.test.wowlua`. UI data is cached under ignored
`dist/wowlua-cache`; later runs can add `--offline`. Tests use separate emulator
worlds and the runner returns the failing exit status.

Use `mock.nextFrame()` for frame-driven behavior. `mock.advanceTime()` advances
timers without running `OnUpdate`, which the addon's refresh and the Blizzard
state driver require. See the pinned [clock implementation](https://github.com/DomenikIrrgang/wowlua/blob/v0.13.8/crates/wowlua-engine/src/clock.rs)
and [testing guide](https://github.com/DomenikIrrgang/wowlua/blob/v0.13.8/docs/guide/testing.md).
The reviewed UI source revision is `172a387e3ab8`. Emulator results cannot certify
secure execution or real item/aura data; use the client checklist below.

## In-game checklist - all NOT VERIFIED until a tester records results

Record date, locale, exact GetBuildInfo() output and PASS / FAIL for each step.
Use a clean addon profile first, then repeat relevant checks with normal addons.

1. Confirm interface 16001 matches the intended Forever build and the addon loads.
2. Login, reload, relog and change characters. Verify settings persist independently.
   Check legacy disabled entries migrate without changing the account table.
   Upgrade from 0.3.0: toggles persist, while old priorities, mappings and blockers
   are ignored and remain stored for rollback.
3. Confirm item IDs, localized names, required levels and durations for the listed
   ranks in all six groups using the actual client. Record evidence in the ledger.
4. Manually use each item from a normal bag/action-bar slot in a controlled test.
   Compare `/fem buffs` before/after with the actual player buffs. Record the real
   aura name. Disable entries whose assumed name does not match.
5. Test equal effects, higher ranks, relevant class buffs and other elixirs.
   Record which replace, coexist or reject. Verify recognized equal/stronger ranks
   prevent downgrades and weaker ranks allow manual upgrades. Disable groups with
   unwanted replacement behavior or mismatched aura names.
6. With a missing tracked effect and an available item, test the documented macro.
   Test ActionButtonUseKeyDown both enabled and disabled, repeated presses,
   modifiers and key holds. Exactly one manual activation may attempt one use.
7. Confirm the alpha-zero/off-screen button accepts the authorized click. If the
   engine rejects it, stop; use the normal item action bar pending an approved
   architecture decision. Do not try alternative protected execution tricks.
8. Move/split/sell/delete the queued stack, bank it, buy another stack and consume
   the last item. Confirm ID-based targeting and prompt clearing/refreshing.
9. Gain/lose a buff, level up, zone and encounter an uncached item. Confirm refresh.
10. Enter combat with a queued item, then change bags/buffs. Verify the secure state
    driver removes the action type, the macro does nothing, and configuration and
    aura inspection pause. After combat, verify the freshly eligible item.
    Also test /reload while already in combat.
11. Check Lua errors, taint logs and blocked-action messages. Record exact errors
    without committing personal logs. Confirm no automatic consumption, chat
    flooding or persistent OnUpdate handler.
12. Install the produced ZIP in a clean AddOns directory and test rollback.

Until these pass, the addon remains experimental. CI cannot certify item data,
stacking, engine timing, secret restrictions or secure execution.
