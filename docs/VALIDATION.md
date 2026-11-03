# Assessment and validation

Version 0.4.0 restores the 0.2.0 command set, fixed priority and English-name
buff matching. It retains modern item APIs, level checks, per-character toggles,
combat protection and packaging checks from 0.3.0. The original name matching is
an explicit assumption, not confirmed client behavior. There is no mandatory
aura mapping or conflict configuration.

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

## Candidate data ledger

All six IDs are retained as candidates, not a certified database. The names below
are labels from the existing project and are also the assumed exact aura names.
Required levels come from client item data.

| Candidate ID | Label | Required level / duration evidence | Aura name / spell ID | Stacking / higher ranks |
|---|---|---|---|---|
| 2458 | Elixir of Minor Fortitude | Forever database reports 2 / 1 hour | NOT VERIFIED | NOT VERIFIED |
| 250330 | Minor Cleric's Elixir | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |
| 250339 | Minor Mageblood Elixir | Forever database reports 5 / 30 minutes | NOT VERIFIED | NOT VERIFIED |
| 250344 | Elixir of Minor Spirit | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |
| 3383 | Elixir of Wisdom | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |
| 3389 | Elixir of Lesser Defense | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |

The [Forever Fortitude entry](https://www.wowhead.com/forever/item=2458/elixir-of-minor-fortitude)
and [Forever Mageblood entry](https://www.wowhead.com/forever/item=250339/minor-mageblood-elixir)
provided those two item-level observations. Other database requests were
inaccessible or insufficient to establish aura/replacement rules. Old Classic
comments and Classic database fields were not accepted as Forever verification.
Even those two entries have no in-game PASS. Duration is not used for selection:
an existing effect is retained until it actually disappears.

The addon assumes each buff has exactly the English item label shown above,
as in 0.2.0. This is NOT VERIFIED and may fail even on an English client. A
localized item name is used for chat feedback, not as proof of an aura name.
There is no Classic API fallback, spell-ID mapping or replacement filtering.
If `/fem buffs` shows an active effect as MISSING, disable that entry. Likewise,
disable entries whose stronger/replacement interactions have not been checked.
The simplified version can otherwise queue an unnecessary replacement.

## Automated validation

Run from the repository root:

```text
python scripts/validate.py
python scripts/validate.py --tag v0.4.0
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

Local development results (2 November 2026):

| Check | Result |
|---|---|
| Lua 5.1 parse/load and 18 mocked scenarios | PASS (Lupa Lua 5.1 runtime) |
| Nine Python distribution/guard tests | PASS |
| TOC version/interface structure and referenced file | PASS; actual current client interface NOT VERIFIED |
| ZIP root, exact members, byte integrity and repeatability | PASS |
| Release/upload workflow definitions | Unchanged; not executed for this change |
| Real secure clicks, combat transitions, item/aura/stacking data and taint | NOT VERIFIED |
| CurseForge authenticated catalog and upload | BLOCKED pending configuration/approval |

GitHub Actions results are reported on the pull request. Release/upload workflows
must not be executed merely to test publication.

Update, 3 November 2026: local validation passes 18 mocked Lua scenarios and
12 Python distribution tests. The authenticated CurseForge catalog check is now
PASS; see [the recorded run and configuration](CURSEFORGE.md). The older table
above records the 2 November state. Project upload permission, actual automated
upload and all live-client results remain NOT VERIFIED.

## In-game checklist - all NOT VERIFIED until a tester records results

Record date, locale, exact GetBuildInfo() output and PASS / FAIL for each step.
Use a clean addon profile first, then repeat relevant checks with normal addons.

1. Confirm interface 16001 matches the intended Forever build and the addon loads.
2. Login, reload, relog and change characters. Verify settings persist independently.
   Check legacy disabled entries migrate without changing the account table.
   Upgrade from 0.3.0: toggles persist, while old priorities, mappings and blockers
   are ignored and remain stored for rollback.
3. Confirm item IDs, localized names, required levels and durations for all six
   candidates using the actual client. Record evidence in the ledger.
4. Manually use each item from a normal bag/action-bar slot in a controlled test.
   Compare `/fem buffs` before/after with the actual player buffs. Record the real
   aura name. Disable entries whose assumed name does not match.
5. Test equal effects, higher ranks, relevant class buffs and other elixirs.
   Record which replace, coexist or reject. There are no blocking rules: disable
   entries with unwanted replacement behavior.
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
