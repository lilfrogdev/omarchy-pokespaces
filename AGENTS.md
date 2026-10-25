# Pokéspaces

Pokéspaces is a public Omarchy workspace indicator plugin.

- Plugin ID: `lilfrogdev.pokespaces`
- GitHub: https://github.com/lilfrogdev/omarchy-pokespaces
- Run development commands from the repository root.
- Resolve installation paths through `XDG_CONFIG_HOME`, defaulting to the current
  user's `.config` directory. The plugin lives under
  `omarchy/plugins/lilfrogdev.pokespaces/` within that directory.

## Working rules

- Inspect the current files and Git status before making changes.
- Do not write code comments or tests.
- Do not commit, push, publish, or change the agreed design without explicit
  instruction.
- Keep documentation and code user agnostic. Do not hardcode usernames, home
  directories, or checkout locations.
- Read the Omarchy skill and its `plugins.md` guide before desktop changes.
- Never modify `/usr/share/omarchy`; use it only as reference material.
- Source and installed copies are separate. After authorized source changes, run
  `python3 scripts/install.py` to update the installed copy.
- Avoid resetting shell configuration or restarting the shell unless needed.
- Keep changes focused on the requested improvement.

## Agreed behavior

Replace only the workspace indicator widget. Preserve the rest of the bar.

Every monitor shows six fixed-width Pokémon team slots with identical assignments.
Active means the workspace displayed on that monitor, independently of global
keyboard focus.

For slots 1–6:

| Workspace state | Indicator |
| --- | --- |
| Active and occupied | Assigned animated Gen V party icon |
| Inactive and occupied | Assigned Poké Ball PNG |
| Empty, active or inactive | White dot |

Existing workspaces numbered 7 or higher appear as ordinary numbers.

- Left-click switches workspace.
- Right-click opens the team picker with the clicked slot selected.
- Keep the six icon-only slots at the top, without visible slot labels.
- Place the shared search field beside the Pokémon/Poké Ball tabs.
- Keep the Pokémon and ball preview without a slot heading.
- Do not show an open-panel underline beneath the workspace widget.
- Use Omarchy UI components and theme tokens. Keep the picker free of redundant
  headings, close buttons, and download explanations.
- Align Pokémon and balls on the bar by their visible bottom edges.
- Hover labels show the workspace number and Pokémon name.
- Pokémon and balls are configurable per slot; duplicates are allowed.
- Save applies all six slots together.
- Cancel or closing the picker discards unsaved changes.
- Missing Pokémon assets fall back to the assigned ball, then a white dot.
- Missing assets must not prevent workspace switching.
- Shiny Pokémon are not supported. Do not add shiny controls, metadata, or asset
  selection logic.

## Default team

| Workspace | Pokémon | Ball |
| --- | --- | --- |
| 1 | Gengar | Master Ball |
| 2 | Dragonite | Dusk Ball |
| 3 | Sandile | Great Ball |
| 4 | Umbreon | Net Ball |
| 5 | Pikachu | Quick Ball |
| 6 | Eevee | Luxury Ball |

## Assets and persistence

Asset source: https://github.com/PokeAPI/sprites

Pinned revision: `97a7832d307311c0e1c6ea9035308bf80cc94f81`

Pokémon asset path:
`sprites/pokemon/versions/generation-v/icons/animated/{id}.png`

- Use animated party icons, not larger battle GIFs.
- Do not bundle sprite collections or selected sprite assets in the repository.
- Cropped screenshots and GIFs of the actual UI are allowed under `docs/media/`
  for documentation; keep personal desktop content out of these captures.
- Bundle only a small availability catalog.
- Download assets only for selected teams and selected previews.
- Store the cache under `omarchy-pokespaces/` within `XDG_CACHE_HOME`, defaulting
  to the current user's `.cache` directory.
- Store the team at `omarchy-pokespaces/team.json` within `XDG_CONFIG_HOME`,
  defaulting to the current user's `.config` directory.
- Cached assets must work offline.
- Save the complete team atomically.
- Preserve upstream attribution and distinguish code licensing from artwork
  ownership.

## Implementation map

- `Workspaces.qml`: per-monitor workspace widget.
- `TeamPicker.qml`: search, team editing, selected previews, Save and Cancel.
- `Backend.qml`: helper request queue, assets, state, and saved-team watching.
- `PixelSprite.qml`: cached frame playback.
- `Model.js`: workspace state and search helpers.
- `scripts/pokespaces.py`: standard-library downloads, cache, persistence, and
  APNG extraction/compositing.
- `scripts/install.py`: local installation and stock-widget restoration.
- `data/catalog.json`: available Pokémon and capture balls.

## Technical constraints

- Qt's PNG loader displays these APNG icons without animation. The helper
  extracts and composites frames into cached PNGs; QML plays their original
  timing.
- Preserve indexed-color and partial-frame APNG support; Sandile requires both.
- Use Omarchy's `Ui.KeyboardPanel` for reliable picker keyboard focus.
- Nested QML component changes may remain cached during hot reload. If installed
  files are current but behavior is stale, a shell restart may be necessary.
- Keep the Python helper standard-library only.

## Verification

Do not add tests. Use checks appropriate to the change, including manifest
validation, syntax checks, and focused manual verification.

For changes affecting the widget or picker, verify relevant behavior:

- Each monitor uses its own active workspace.
- Empty, occupied, and active indicators follow the agreed rules.
- Fixed slot widths prevent bar movement.
- Search and keyboard navigation work.
- Save applies the complete team across monitors.
- Cancel discards edits.
- Cached animations and fallback indicators work offline.
- The repository contains no bundled sprite assets; documentation captures are
  limited to `docs/media/`.

Do not claim live verification when the desktop session is unavailable.
Report what was checked and any remaining verification limits.

## Agent control

Use the supported CLI instead of editing the saved team JSON directly:

```bash
pokespaces team show --json
pokespaces pokemon search umbreon --json
pokespaces balls list --json
pokespaces team set --slot 3 --pokemon umbreon --ball luxury-ball --json
pokespaces team apply --file team.json --json
```

Before installation, invoke `python3 scripts/pokespaces.py` from the repository
root. The installer exposes `pokespaces` in the current user's `.local/bin/`.

- Inspect the team before changing it. Preserve assignments outside the request.
- Use `team set` for one slot; omitted fields retain their values.
- Use `team apply` for a full six-slot replacement. It accepts the JSON document
  returned by `team show` or a team array; `--file -` accepts stdin.
- Use JSON output for automation. Check `ok`, exit status, and download warnings.
- Exit codes: 0 means success, 1 means operation failure, 2 means command misuse.
- Asset download warnings do not mean the saved configuration failed.
- CLI edits must use the same validation, atomic persistence, and cache as the
  picker. File watching applies changes across monitors without restarting.

## Restore

Run `python3 scripts/install.py --restore` only when requested.

Restoration returns the stock workspace indicator while preserving the saved
team and asset cache.
