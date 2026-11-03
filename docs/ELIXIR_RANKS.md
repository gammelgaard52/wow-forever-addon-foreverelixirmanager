# Elixir rank evidence and selection

Issue #19 adds rank selection to the six existing groups. This is an experimental
candidate, not a claim of live-client compatibility. Reviewed 3 November 2026.

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
flasks, stacking and unnamed/new ranks are outside this six-group policy.

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
