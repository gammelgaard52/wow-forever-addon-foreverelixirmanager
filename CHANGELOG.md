# Release notes

## 0.5.0

Experimental candidate; live Forever compatibility remains NOT VERIFIED.

- Choose the strongest carried, level-eligible elixir within each of the six existing effect groups, falling back when a higher rank is unavailable.
- Track 24 candidate items with Forever-specific source evidence; runtime client data controls required levels.
- Avoid replacing a recognized equal or stronger active rank with a weaker one, and offer stronger ranks as manual upgrades.
- Preserve existing group priority and saved on/off choices. Each choice now covers every rank in that group.
- Keep manual clicks and combat restrictions. Exact English aura-name assumptions, actual stacking and secure execution still require in-game verification.

Upgrade: existing disabled choices remain disabled for the whole group. Use /fem list to see the group labels; disable a group if /fem buffs misidentifies an active effect.

## 0.4.0

Experimental Alpha. The owner approved distribution without live-client testing
on 3 November 2026 because the game is not yet available for their testing.
Actual Forever compatibility, secure clicks and combat behavior remain NOT VERIFIED.
An optional emulator experiment also exposes unresolved bag-refresh and state-driver
discrepancies; these are not confirmed client bugs. Use the documented combat-guarded
macro and treat this build as a test candidate, not a validated stable release.

- Add a vector SVG version of the current elixir logo.
- Restore the simple 0.2.0 controls: list, enable/disable, buffs and status.
- Restore the original fixed priority and English buff-name matching. No aura-ID
  setup is required; item and buff-name assumptions still need in-game validation.
- Remove priority movement, aura mapping, blocking rules and reset commands.
- Keep per-character on/off choices, level checks, bag refresh and combat protection.
- Shorten installation and macro setup. Keep automated tests and ZIP validation.

Upgrade: existing on/off choices are retained. Old priority, aura and blocker
settings are ignored but preserved for rollback. Stronger/replacement effects are
no longer filtered; disable an entry if its buff name or interactions do not match.
Live Forever compatibility remains NOT VERIFIED.

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
