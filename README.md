# ForeverElixirManager

**Smart elixir management for World of Warcraft: Forever.**

![ForeverElixirManager artwork](assets/logo.jpg)

ForeverElixirManager is a lightweight, priority-based elixir addon for World of Warcraft: Forever. It checks your active buffs and bag inventory, then queues the next missing and available elixir for manual use. Designed for efficient leveling and group play, with combat-safe updates, clear chat feedback, and no automatic consumption.

> **Experimental / in-game verification required.** Forever-specific aura names, item IDs, elixir stacking and secure `/click` support have not yet been validated on the live client. This project is not affiliated with Blizzard Entertainment.

## Features

- **Priority-based:** chooses the first elixir whose buff is missing.
- **Inventory-aware:** skips any elixir not currently in your bags.
- **Player-controlled:** only a manual button press attempts consumption.
- **Combat-safe configuration:** protected button attributes update only outside combat.
- **Lightweight:** no external addon dependencies; simple chat status feedback.

Originally built for a Discipline Priest supporting a Protection Paladin, but suitable for other characters using supported elixirs.

## Installation

Download a versioned [GitHub release](../../releases) and extract the ZIP into `Interface/AddOns/` so it contains:

```text
ForeverElixirManager/
  ForeverElixirManager.toc
  ForeverElixirManager.lua
```

Enable the addon, then create this in-game macro:

```lua
#showtooltip
/click ForeverElixirSecureBtn
```

Bind it to a key. **The secure click must be tested in Forever**, as the client may restrict macro-triggered clicks.

## Commands

- `/fem` — refresh selection
- `/fem buffs` — show tracked buff and bag status
- `/fem status` — show queued item
- `/fem list` — view configured elixirs (improvement version)
- `/fem enable N` / `/fem disable N` — control selection (improvement version)

## Initial priority

Elixir of Minor Fortitude; Minor Cleric's Elixir; Minor Mageblood Elixir; Elixir of Minor Spirit; Elixir of Wisdom; Elixir of Lesser Defense.

These are development defaults, **not** a verified claim that every elixir stacks. Incorrect aura naming can cause redundant item selection. Do not use valuable elixirs until this has been tested.

## Releases and development

Version tags `vX.Y.Z` trigger the GitHub Actions ZIP release workflow. Read [AGENTS.md](AGENTS.md) for review, security and testing conventions.

## License

Copyright © 2026 Martin Gammelgård Rasmussen. Released under the **[MIT License](LICENSE)**, including original repository artwork. World of Warcraft and Blizzard are trademarks of their respective owners.
