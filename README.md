# ForeverElixirManager

Lightweight, experimental elixir manager for **World of Warcraft: Forever**.

![ForeverElixirManager logo](assets/logo.svg)

It queues the **first missing elixir buff whose item is present in your bags** on a secure action button. Consumption requires a manual keypress. Secure button behavior and Forever-specific aura IDs remain **NOT VERIFIED in-game**.

## Install

Download a tagged [GitHub Release](../../releases) and extract it to your WoW `Interface/AddOns/` directory. The folder must be `Interface/AddOns/ForeverElixirManager/`, with the `.toc` and `.lua` inside. Restart the client and enable the addon.

Create this WoW macro and bind it to a key:

```text
#showtooltip
/click ForeverElixirSecureBtn
```

## Commands

- `/fem` — rescan and show commands
- `/fem buffs` — show aura-name check and bag quantities
- `/fem status` — show queued item

## Known limitations

- Elixir item IDs and buff names require live Forever verification before public release.
- The secure `/click` path may not work in every Forever client build.
- No consumables are used automatically; the button is only updated outside combat.
- The addon does not yet account for mutually exclusive elixir effects or character level.
- The item selected before combat remains queued until the next safe refresh.
- A failed, missing, or incompatible aura lookup may queue redundant consumables.

## Release process

After a reviewed merge, update the TOC version, then create and push a tag `vX.Y.Z` matching `## Version: X.Y.Z`. GitHub Actions produces an installable ZIP and a GitHub Release. Manual workflow dispatch builds an artifact but does not publish a release.

## Development

See [AGENTS.md](AGENTS.md). This addon is in beta; test `/fem buffs`, item selection, manual activation, aura refresh, combat lockdown, and buff coexistence on the live Forever client before distributing it widely.
