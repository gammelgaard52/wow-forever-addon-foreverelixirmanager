# Proposed enhancements (not yet merged)

This branch adds configurable elixir eligibility while keeping one-click manual consumption and out-of-combat secure attribute updates.

- `/fem list` lists elixirs and their enabled/disabled state.
- `/fem disable 1` excludes the first elixir from selection, avoiding repeated queues of unsupported or conflicting effects.
- `/fem enable 1` restores it.
- Settings persist across sessions with `SavedVariables`.
- Separate pull request validation checks TOC metadata, mandatory Lua source and ZIP structure. Tests do **not** assert in-game API compatibility.

## Before merging

1. Test whether the secure `/click` command works in the live Forever build.
2. Verify each item ID, item name and buff name. The current version compares visible aura names to item names.
3. Confirm which elixirs can stack and disable conflicting entries.
4. Test combat lockdown and actual bag/aura events on character login, consumption, and reload.
5. Consider replacing aura names with verified spell IDs, plus explicit UI status, in a later release.
