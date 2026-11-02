# CurseForge description

ForeverElixirManager is a lightweight, priority-based elixir addon for World of Warcraft: Forever. It checks your active buffs and bag inventory, then queues the next missing and available elixir for manual use. Designed for efficient leveling and group play, with combat-safe updates, clear chat feedback, and no automatic consumption.

## Highlights

- Prioritizes missing elixir effects.
- Skips consumables that are not available in the player's bags.
- Prepares a single manual item-use action.
- Selection code never changes protected attributes in combat; a fixed secure driver disables the action.
- Reports the queued consumable in chat.

**Status: experimental.** Client compatibility, item IDs, aura spell IDs and stacking must be validated before public distribution. Version 0.3.0 requires per-character, user-observed aura mappings before an item can queue. Level requirements come from the client; conflicting effects must be configured from observed behavior. Includes priority, enable/disable and reset commands. Selection pauses in combat and a standard secure state driver disables the prepared action. No input broadcasting or automatic gameplay. Open source under the MIT License. Not affiliated with Blizzard Entertainment.
