# Assessment and validation

Assessment baseline: main at be3fac1, 2 November 2026. Clean checkout; PRs #1 and
#2 already merged; no open PRs at assessment. TOC version 0.2.0, interface 16001.
The original implementation used item names as aura names, an unguarded global
GetItemCount, account-wide settings and no level or replacement filtering.
Events could run before settings initialization. AnyUp depended on the user's
ActionButtonUseKeyDown setting. Combat left an old action armed. CI checked file
presence and SVG syntax but neither Lua behavior nor an actual ZIP.
The MIT license and original JPEG/SVG assets have been retained.

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
are labels from the existing project. Runtime eligibility uses client item data.

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

No guessed aura IDs, English name fallbacks, rank groups or shared elixir
categories are shipped. Each character starts without aura mappings and therefore
without an actionable queue. User mappings and blockers are explicit local
observations, not automatically promoted to verified project data. A valid spell
ID only establishes that a spell exists; it cannot prove the item applies it.
Unknown conflicts cannot be detected. Leave an entry unmapped/disabled until its
effects and interactions have been checked.

## Automated validation

Run from the repository root:

```text
python scripts/validate.py
python scripts/validate.py --tag v0.3.0
python -m unittest discover -s tests -p "test_*.py"
```

Use Lua 5.1 on PATH (CI installs lua5.1). Windows can instead install the optional
development dependency with `python -m pip install lupa==2.8`; the runner
explicitly loads lupa.lua51. Nothing is bundled with the addon.

The Lua harness covers missing/present buffs and items, priorities, level changes,
configured conflicts, bag/aura events, combat, secure attribute updates, startup,
per-character persistence/migration, reset, malformed settings, invalid/missing
APIs, secret-value rejection, item-cache completion and event coalescing.
Secure state snippets are executed in a mock, not a real protected environment.
Python validates exact TOC entries, metadata, tag/version agreement and actual ZIP
members/bytes. The package is an allowlist with one ForeverElixirManager/ root;
LICENSE is included to satisfy MIT redistribution requirements.

Local development results (2 November 2026):

| Check | Result |
|---|---|
| Lua 5.1 parse/load and 19 mocked scenarios | PASS (Lupa Lua 5.1 runtime) |
| Nine Python distribution/guard tests | PASS |
| TOC version/interface structure and referenced file | PASS; actual current client interface NOT VERIFIED |
| ZIP root, exact members, byte integrity and repeatability | PASS |
| Workflow YAML parsing and embedded Bash syntax | PASS |
| Real secure clicks, combat transitions, item/aura/stacking data and taint | NOT VERIFIED |
| CurseForge authenticated catalog and upload | BLOCKED pending configuration/approval |

GitHub Actions results are reported on the pull request. Release/upload workflows
must not be executed merely to test publication.

## In-game checklist — all NOT VERIFIED until a tester records results

Record date, locale, exact GetBuildInfo() output and PASS / FAIL for each step.
Use a clean addon profile first, then repeat relevant checks with normal addons.

1. Confirm interface 16001 matches the intended Forever build and the addon loads.
2. Login, reload, relog and change characters. Verify settings persist independently.
   Check legacy disabled entries migrate without changing the account table.
3. Confirm item IDs, localized names, required levels and durations for all six
   candidates using the actual client. Record evidence in the ledger.
4. Manually use each item from a normal bag/action-bar slot in a controlled test.
   Compare /fem buffs before/after; record the resulting aura ID and name.
   Set /fem aura N SPELLID only after observing the actual applied aura.
5. Test equal effects, all higher ranks, relevant class buffs and other elixirs.
   Record which replace, coexist or reject. Add observed blocking IDs with
   /fem block N SPELLID, or disable the entry. Confirm no needless replacement.
6. With a missing mapped effect and an available item, test the documented macro.
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
