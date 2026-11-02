# Release notes

## 0.3.0

Experimental development version; live Forever compatibility is NOT VERIFIED.

- Match player auras by user-observed spell IDs. Unmapped items are not queued.
- Use modern client APIs for bag counts, localized item names and required levels.
- Add per-character configuration, priority movement, reset and explicit blocking aura IDs.
- Import legacy enabled/disabled settings once per character without changing the old account table.
- Disable the prepared action with a standard secure combat state driver; refresh after combat.
- Pin secure activation to key release and coalesce inventory/aura event bursts.
- Stop selection on unavailable, malformed or restricted aura data.
- Add mocked Lua 5.1 tests and validated, allowlisted release ZIPs, including the MIT license.
- Prepare a separate, explicitly authorized manual CurseForge upload workflow.

Upgrade: existing installations must configure observed aura IDs before any item
can queue. Use the README validation procedure. No hardcoded stacking or rank
rules have been claimed as verified.

## 0.2.0

- Add persistent enabled/disabled elixir settings and basic PR validation.
