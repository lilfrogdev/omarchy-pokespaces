# Pokéspaces

Your Pokémon team in Omarchy's workspace bar. Six configurable slots, shared across monitors, with each monitor's active Pokémon animated independently.

![Animated Pokéspaces workspace indicators](docs/media/workspaces.gif)

**0.1.0** · 649 Pokémon · 27 Poké Balls · No shiny variants

## Install

Requires Omarchy Quattro's Quickshell shell, Hyprland Lua dispatchers, Python 3.10+, and Git. Older Waybar setups are unsupported.

```bash
omarchy plugin add https://github.com/lilfrogdev/omarchy-pokespaces.git --yes
python3 ~/.config/omarchy/plugins/lilfrogdev.pokespaces/scripts/install.py
```

Run both commands as your normal user. Setup replaces the stock workspace indicator, backs up `shell.json`, preserves the rest of your bar, and installs the CLI in `~/.local/bin/`. No sudo or Python packages needed. `--enable` alone would add another widget rather than replace the stock one.

<details>
<summary>Fallback: clone manually</summary>

Use this for a custom `XDG_CONFIG_HOME` or when native installation is unavailable. Clone anywhere:

```bash
git clone https://github.com/lilfrogdev/omarchy-pokespaces.git
cd omarchy-pokespaces
python3 scripts/install.py
```

</details>

## Use

- **Left-click** to switch workspace; **right-click** to edit that slot.
- **Active + occupied:** animated Pokémon. **Inactive + occupied:** Poké Ball. **Empty:** white dot.
- Workspaces 7+ use ordinary numbers. Hover for workspace and Pokémon names.

![Team picker with Pokémon search and previews](docs/media/team-picker.png)

Choose a slot, search **Pokémon** or **Poké Balls**, and select a result. **Save** applies the whole team to every monitor. **Cancel**, Escape, or clicking outside discards edits. Duplicates are allowed.

<details>
<summary>Poké Ball search</summary>

![Searching for Luxury Ball](docs/media/ball-search.png)

</details>

## Agent / CLI

Ask your agent: “Put Umbreon in slot 3 with a Luxury Ball.” Or run:

```bash
pokespaces team show --json
pokespaces pokemon search umbreon --json
pokespaces balls list --json
pokespaces team set --slot 3 --pokemon umbreon --ball luxury-ball --json
```

Names or Pokédex IDs work; omitted fields stay unchanged. Export with `pokespaces team show --json > team.json`; import with `pokespaces team apply --file team.json --json`. See [AGENTS.md](AGENTS.md) for automation details. Keep `~/.local/bin` on your `PATH`.

## Update / restore

For native installations:

```bash
omarchy plugin update lilfrogdev.pokespaces
python3 ~/.config/omarchy/plugins/lilfrogdev.pokespaces/scripts/install.py
```

For a manual checkout, run `git pull --ff-only` and `python3 scripts/install.py` from its directory.

Restore the stock indicator without deleting your team or cache:

```bash
python3 "${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/plugins/lilfrogdev.pokespaces/scripts/install.py" --restore
```

## Notes

- Only selected assets download; cached sprites work offline. Missing Pokémon fall back to their ball, then a dot. Reopen the picker to retry downloads.
- Team: `~/.config/omarchy-pokespaces/team.json`. Cache: `~/.cache/omarchy-pokespaces/`. Both respect their XDG variables.
- If an agent changes your team while the picker has unsaved edits, cancel and reopen before continuing.
- Stale UI after an update? Run `omarchy restart shell`.
- Verified on Omarchy 4.0.6-1 / Quickshell 0.3.2 across three monitors. Vertical bars remain visually unverified.

## Credits

Code: [MIT](LICENSE). Omarchy-derived code: [Omarchy MIT notice](OMARCHY-LICENSE).

Sprites: [PokéAPI/sprites](https://github.com/PokeAPI/sprites), pinned to `97a7832d307311c0e1c6ea9035308bf80cc94f81`. English names come from PokéAPI. The [upstream notice](data/SPRITES-LICENCE.txt) specifies CC0 for the repository and Pokémon Company copyright for image contents. Artwork in downloads and documentation retains its ownership; the code license does not cover Pokémon artwork or trademarks. Runtime sprites are not bundled.

Unofficial fan project, unaffiliated with The Pokémon Company, Nintendo, Game Freak, or Creatures.
