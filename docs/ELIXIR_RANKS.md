# Elixir rank evidence and selection

Rank selection covers six effect groups; 0.6.0 additionally discovers elixirs and
scrolls outside this ranked list from the player's bags. The rank observations below were
reviewed on 3 November 2026; live-client compatibility remains unverified.

## Selection contract

Groups keep the existing order: Fortitude, Cleric's, Mageblood, Spirit, Intellect,
Defense. Each group's original item ID remains its saved on/off key, so existing
per-character and legacy disabled choices also disable the group's higher ranks.

Within a group, prefer the strongest listed effect whose item is carried and whose
required level is met. Bag counts and required levels come from `C_Item`, with
banks excluded; database levels below are evidence, not hardcoded eligibility.
Missing, uncached or failed item data allows fallback to a lower known rank.
Arrival of item data, bag changes and level changes cause the usual refresh.

An active recognized equal/stronger effect blocks replacement by a weaker one,
even if the active effect's item is no longer carried. A weaker recognized effect
allows a stronger candidate. The player still activates each use manually;
selection and configuration pause in combat. No automatic consumption is added.

Strength compares effect magnitude, not item level or a word such as "Greater".
For example the retrieved Forever records give Greater Intellect +25 at level 37
and Intellect +10 at level 45. Wisdom and Lesser Intellect both give +6; prefer
Wisdom when both are available because its listed duration is longer. Either
recognized active effect blocks the other. Combined-stat elixirs, class buffs,
flasks, stacking and unnamed/new ranks are outside this six-group rank policy.
Additional elixirs and scrolls use the discovery policy below.

## Bag discovery in the 0.6.0 local test candidate

Reviewed on 6 November 2026 before implementation. API source evidence is the
retained Forever UI snapshot
[`aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16`](https://github.com/Gethe/wow-ui-source/tree/aff0d8cd53bf4d9ef1c1dd2786b94461a276fb16/Interface/AddOns),
not a capture of the tester's installed build:

- `Blizzard_APIDocumentationGenerated/ItemConstantsDocumentation.lua` defines
  Consumable class 0, Elixir subclass 2 and Scroll subclass 4. The addon uses those
  numeric categories, not English-name pattern matching or Classic item IDs.
- `ItemDocumentation.lua` documents GetItemInfo's minimum level and class/subclass
  results, and GetItemSpell's name. The use-spell ID is deliberately not treated as
  the resulting aura ID.
- `ContainerDocumentation.lua` documents C_Container.GetContainerNumSlots and
  GetContainerItemID. Scan bag 0 through NUM_BAG_SLOTS only. The cached Forever UI
  revision `172a387e3ab8`, `Blizzard_FrameXMLBase/Constants.lua`, assigns
  NUM_BAG_SLOTS from Constants.InventoryConstants.NumBagSlots. No bank bags are scanned.
- `Blizzard_FrameXML/SecureTemplates.lua` passes the secure item action's unit to
  SecureCmdUseItem. The button now explicitly sets unit to `player` for scrolls.
  This supports the intended self-target, but is not evidence of a successful click.

Concrete client-derived examples:

| Item | Forever evidence | Use-spell name evidence |
|---|---|---|
| 2454 Elixir of Minor Strength | [Icy Veins datamined record, build 1.60.1.70532](https://db.icy-veins.com/wow-forever/items/2454): Consumable/Elixir, +4 Strength | Lesser Strength (2367); not a verified resulting aura |
| 954 Scroll of Strength | [ForeverDB client observations](https://foreverdb.net/item/954): Scroll, required level 10, +5 Strength to target | Strength; not a verified resulting aura |

Observed locally: the user carried Elixir of Minor Strength and the old macro did
nothing; the old allowlist excludes it. Successful consumption, actual aura names
and the installed build have not yet been observed for 0.6.0.

Discovery covers every carried item that the client classifies as an elixir or a
scroll, once its name, required level and use-spell name are readable. It is not a
claim that every database item exists, drops or works in the current client.
Other categories (including flasks, potions, recipes and quest items) are excluded.
Uncached item data is requested once and refreshed on receipt; failed loads need
a reload. Missing APIs or incomplete data are reported when nothing can be queued.

The original 24 items keep their groups and toggles and are never rediscovered as
"other" items. Group 7 (Other elixirs) precedes group 8 (Scrolls); both are on by
default, including for existing characters. Within each new group, use ascending
item ID, independent of bag position. This is deterministic, not a strength ranking.
No proxy based on item level, required level or name infers relative effect strength.

**Assumption:** for discovered items only, an exact active aura name equal to the
client's localized item name or use-spell name means the effect is present. Any
such match blocks reuse, even when multiple ranks share a name. This avoids guessing
an upgrade, but does not recognize different buff names, overlapping combined
effects or stacking rules. Different names may still cause replacement. The
original six groups retain their separately documented English-name assumptions.
Use `/fem buffs` to inspect the assumed name and `/fem disable 7` or `8` if it does
not match the client. Confirm scroll self-targeting and one use per manual click
in-game before treating either as compatible.

## Source ledger

The linked database pages reproduce Forever item records. The retrieved 60.tools
pages identify beta builds 1.60.1.70245, 70425 and 70532; the Minor Fortitude page
was retrieved from the current 1.60.1 index. These are snapshots from different
beta builds, not one verified launch dataset. Mageblood uses the ForeverDB
client-extracted record (beta 1.60.1.70009; also corroborated by RaidDex's Forever
1.60.1 record). Higher-level availability remains unverified. No Classic-only
item data is used as proof of a Forever rank.

| Group | Item and source | Effect magnitude | Listed required level |
|---|---|---|---|
| Fortitude | [250335 Greater Fortitude](https://www.60.tools/items/250335-elixir-of-greater-fortitude) | 400 health | 55 |
| Fortitude | [250334 Fortitude](https://www.60.tools/items/250334-elixir-of-fortitude) | 200 health | 45 |
| Fortitude | [3825 Lesser Fortitude](https://www.60.tools/items/3825-elixir-of-lesser-fortitude) | 120 health | 25 |
| Fortitude | [2458 Minor Fortitude](https://www.60.tools/items/2458-elixir-of-minor-fortitude) | 27 health | 2 |
| Cleric's | [250333 Greater Cleric's](https://www.60.tools/items/250333-greater-clerics-elixir) | 40 healing | 55 |
| Cleric's | [250332 Cleric's](https://www.60.tools/items/250332-clerics-elixir) | 30 healing | 45 |
| Cleric's | [250331 Lesser Cleric's](https://www.60.tools/items/250331-lesser-clerics-elixir) | 20 healing | 25 |
| Cleric's | [250330 Minor Cleric's](https://www.60.tools/items/250330-minor-clerics-elixir) | 10 healing | 5 |
| Mageblood | [250341 Greater Mageblood](https://www.60.tools/items/250341-greater-mageblood-elixir) | 20 mana/5 s | 55 |
| Mageblood | [20007 Mageblood](https://foreverdb.net/es/item/20007) | 12 mana/5 s | 40 |
| Mageblood | [250340 Lesser Mageblood](https://www.60.tools/items/250340-lesser-mageblood-elixir) | 6 mana/5 s | 25 |
| Mageblood | [250339 Minor Mageblood](https://www.60.tools/items/250339-minor-mageblood-elixir) | 3 mana/5 s | 5 |
| Spirit | [250347 Greater Spirit](https://www.60.tools/items/250347-elixir-of-greater-spirit) | 18 spirit | 55 |
| Spirit | [250346 Spirit](https://www.60.tools/items/250346-elixir-of-spirit) | 10 spirit | 45 |
| Spirit | [250345 Lesser Spirit](https://www.60.tools/items/250345-elixir-of-lesser-spirit) | 6 spirit | 25 |
| Spirit | [250344 Minor Spirit](https://www.60.tools/items/250344-elixir-of-minor-spirit) | 3 spirit | 5 |
| Intellect | [9179 Greater Intellect](https://www.60.tools/items/9179-elixir-of-greater-intellect) | 25 intellect | 37 |
| Intellect | [250354 Intellect](https://www.60.tools/items/250354-elixir-of-intellect) | 10 intellect | 45 |
| Intellect | [3383 Wisdom](https://www.60.tools/items/3383-elixir-of-wisdom) | 6 intellect (1 hour) | 10 |
| Intellect | [250353 Lesser Intellect](https://www.60.tools/items/250353-elixir-of-lesser-intellect) | 6 intellect (30 min) | 25 |
| Defense | [13445 Greater Defense](https://www.60.tools/items/13445-elixir-of-greater-defense) | 450 armor | 43 |
| Defense | [8951 Defense](https://www.60.tools/items/8951-elixir-of-defense) | 250 armor | 29 |
| Defense | [3389 Lesser Defense](https://www.60.tools/items/3389-elixir-of-lesser-defense) | 150 armor | 16 |
| Defense | [5997 Minor Defense](https://www.60.tools/items/5997-elixir-of-minor-defense) | 50 armor | 1 (index) |

## Assumptions and validation limits

Aura recognition retains the original exact English item-label assumption. An
item effect/use-spell name is not proof of the resulting aura name or spell ID.
Some effects may use a different name (for example "Greater Intellect" or "Mana
Regeneration"); no unverified use-spell-to-aura mapping is added. If `/fem buffs`
reports an active effect as MISSING, disable its group. The rank comparison only
protects recognized effects; it cannot prevent replacement when recognition fails.

The effect groups and magnitude order are a deliberate selection policy inferred
from these records, not proof of in-game mutual exclusion or stacking. Client
observations must confirm item IDs, actual aura names, replacement behavior,
durations, rank strengths, level requirements, secure clicks and combat handling.

The Lua harness uses synthetic bag, level and aura data to test all six groups,
fallback, upgrades, equal-strength suppression, settings persistence, cache refresh,
group priority and combat suspension. Passing these tests validates that policy's
logic only. Keep the live checklist in [VALIDATION.md](VALIDATION.md).
