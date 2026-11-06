# Release notes

## 0.6.0

- Discover all carried items classified by the client as elixirs or scrolls, including Elixir of Minor Strength, with new Other elixirs and Scrolls on/off groups.
- Aim scrolls at your own character and skip discovered items with an active matching item or use-spell name.
- Show discovered items and their assumed buff names through `/fem list` and `/fem buffs`, keeping the original six groups and saved choices.
- Make CurseForge release-note navigation clearer: link the version heading to its source and show Full Changelog and Previous Releases on separate lines.

Local test candidate. New categories are
enabled by default and use item-ID order, without inferred rank strength or stacking
rules. Buff names, secure clicks and live Forever compatibility remain NOT VERIFIED.

## 0.5.2

- Make CurseForge release-note navigation clearer: link the version heading to its source and show Full Changelog and Previous Releases on separate lines.

Addon behavior and saved settings are unchanged from 0.5.1. Live Forever compatibility remains NOT VERIFIED.

## 0.5.1

- Use `ForeverElixirManager-v0.5.1` as the release display name, with the release type appended on GitHub.

Owner-requested patch release for the corrected name. Addon behavior and saved
settings are unchanged from 0.5.0. Live Forever compatibility remains NOT VERIFIED.

## 0.5.0

- Select the strongest carried elixir you can use across six effect groups and 24 supported items, with fallback to lower ranks.
- Avoid replacing recognized equal or stronger buffs; offer stronger ranks as manual upgrades.
- Keep existing group priority and saved on/off choices, now covering every rank in each group. Manual clicks and combat restrictions remain in place.

Experimental: live Forever compatibility remains NOT VERIFIED. Buff recognition
assumes English item names. Disable a group if /fem buffs misidentifies its active effect.

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
