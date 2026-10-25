# Pokéspaces 0.1.0 readiness review

Review date: 2026-10-24

## Recommendation

Ready for an initial public **0.1.0** release for users of Omarchy's current Quickshell plugin system. No known release-blocking defects remain in the reviewed implementation after the corrections below.

This recommendation is scoped to a small, early release with explicit compatibility requirements. It does not establish compatibility with all Omarchy versions, themes, or bar orientations. The repository still needs to be committed and published before its public install instructions can work; no commit, tag, push, or GitHub release was performed during this review.

## Issues found and corrected

- PR review identified extra escaping in the workspace dispatcher expression. It passed literal backslashes through shell quoting, causing Hyprland to reject click/accessibility activation. The shared handler now quotes the Lua workspace string once and leaves shell escaping to `Util.shellQuote`. The original expression was reproduced as a parser error; the corrected expression was accepted by the running compositor.

- `team apply` previously treated a missing or null `team` as a request to retain the current team and could report success for `{}`. It now validates the imported team before persistence. Missing, null, malformed, and incomplete teams fail without writing a team file.
- CLI name normalization previously removed both Nidoran gender symbols, making the two names indistinguishable. Female and male names now resolve separately, including spelled-out aliases.
- Installer CLI conflicts are now detected before copying plugin files. Existing unrelated commands are preserved.
- The local installer excludes documentation captures from its runtime copy. Only cropped UI screenshots and a short GIF are included in the repository; no runtime sprite collection is bundled.

## Evidence

| Area | Verification |
| --- | --- |
| Installation | Ran installer against a temporary user configuration with a stock workspace widget. Verified replacement position, preservation of unrelated layout/settings, backup creation, executable CLI link, and repeated installation. Shell IPC calls were intercepted in this isolated check. |
| Restoration | Ran `--restore` against that temporary configuration and verified the stock widget returned. The real desktop was not reset. |
| First run | Used fresh temporary configuration/cache directories and downloaded all twelve default assets from the pinned source revision without errors. |
| Animation | All six default Pokémon produced two composited animation frames. Earlier live checks also covered indexed-color, partial-frame Sandile playback. |
| Offline use | Repeated state loading with network access blocked by an unreachable proxy; all twelve cached default assets remained available without errors. |
| CLI | Checked inspection/search, names and IDs, single-slot updates, complete-team import, invalid input rejection, exit codes, and concurrent edits in isolated configurations. |
| Persistence | Verified atomic saved-team writes and that concurrent single-slot changes retained both edits. Live picker saving and multi-monitor state were verified during development. |
| Live UI | Inspected the current picker, Pokémon/Poké Ball search, keyboard navigation, Escape dismissal, previews, and bar alignment. No new plugin QML errors appeared in the inspected shell logs. |
| Multiple monitors | Observed the same assignments across three monitors, each showing its own active workspace Pokémon. |
| Syntax/schema | Python AST parsing, Qt QML parser checks, and Omarchy manifest validation passed. Manifest version is `0.1.0`. |
| Distribution | Reviewed source, installer, CLI, catalog, licensing notices, README, and cropped documentation media. No code comments or test files were added. |

## Supported environment and limits

- Live verification used Omarchy **4.0.6-1**, its bundled Quickshell **0.3.2**, Python **3.14.8**, and three monitors with horizontal bars.
- A clean user configuration and cache were exercised, but this was not a separate physical machine or fresh OS installation. Public GitHub cloning cannot be verified until this implementation is published.
- Vertical layout code exists but has not been visually verified. The README states that limitation.
- Python 3.10 is the documented minimum based on API usage; execution was verified with Python 3.14.8.
- Uncached selections need internet access. Download failures preserve valid team saves and use fallback indicators; retry by reopening the picker.
- The full 649-entry catalog was not downloaded during this review. Default assets and selected custom previews were exercised.
- Picker Save replaces all six slots. Concurrent agent edits and an already-dirty picker use last-save-wins behavior; cancel/reopen before continuing edits after an external change.
- Nested QML components sometimes remain cached after hot reload. The documented recovery is `omarchy restart shell`.
- Shiny Pokémon are unsupported. Existing sprite attribution and artwork ownership notices remain separate from the code license.

## Release scope

The release consists of the workspace widget, team picker, agent-facing CLI, selected-asset downloader/cache, local installer/restorer, availability catalog, notices, and illustrated documentation. It adds no package dependencies beyond the documented Omarchy environment, Python, and Git.
