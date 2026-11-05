# Asset manifest — exploration UI (area: explore-system)

Owner: explore-system specialist · Date: 2026-11-04 · Engine: Godot 4.7.2 · Round 2 (TECHNICAL_ARCHITECTURE §12).

Everything listed here is **original work**, generated procedurally by a project script on 2026-11-04. No pixel, shape
or colour sample was taken from `documentation/references/` or any external source; no downloads, no AI media.
Palette values come from `tools/pixelgen/pg.py` (`karsk` snow / `archive` paper, wood, blue, ink ramps) and the
round-1 UI palette. Licence: original project work (same terms as the rest of the game).

## Generator

`tools/pixelgen/gen_ui_explore.py` — run `py -3 -P tools/pixelgen/gen_ui_explore.py`, then import (shared lock, see
TECHNICAL_ARCHITECTURE §1). Deterministic: seeds are `crc32` of the asset names (no `hash()`, no clock).
Every texture is drawn at 1:1 and stored at x3 nearest (StyleBoxTexture cannot scale; 1 art px = 3 screen px).
1:1 sources and a contact sheet land in `assets/ui/explore/src_1x/` (has `.gdignore`, never imported);
`assets/ui/explore/manifest.json` lists every file with its 1:1 size, scale and 9-patch margins.

## Files

| Path | Size (1:1) | Use |
|---|---|---|
| `assets/ui/explore/frames/notebook.png` | 31×26, 9-patch L10 T6 R7 B8, vertical TILE | Protagonist's notebook page (warm paper, sewn gutter with thread every 6 px, cover board, dog-eared corner). The ruling (squared paper for Alexei/Karsk, ruled lines for Konrad/Berlin) and the red margin line are drawn by `discovery_view.gd`, aligned to the text baselines. |
| `assets/ui/explore/frames/archive_card.png` | 24×32, 9-patch L8 T16 R8 B8 | "REALE GESCHICHTE" card: cool archive paper (karsk snow ramp), slate title band, hairline frame. Deliberately without any emblem, stamp or seal. |
| `assets/ui/explore/frames/archive_card_hc.png` | 24×32 | High-contrast variant (white paper, black frame). |
| `assets/ui/explore/frames/photo_mount.png` | 22×23, 9-patch L7 T7 R7 B8, both axes TILE (period 4 px) | Deckle-edged photo print for the close-up images (×3). |
| `assets/ui/explore/frames/bar_track.png`, `bar_fill.png`, `bar_fill_neutral.png` | 7×5, 9-patch margin 2 | Progress bars on paper (journal: finds per area = ink blue, history per side = neutral grey). |
| `assets/ui/explore/icons/icon_discovery.png` | 13×13 | HUD toast / pause plate: magnifying glass. |
| `assets/ui/explore/icons/icon_history.png` | 13×13 | HUD toast / pause plate: stack of archive index cards (greys only). |
| `assets/ui/explore/icons/kind_detail.png`, `kind_secret.png`, `kind_easter_egg.png`, `kind_chat.png`, `kind_history.png` | 13×13 | Ink icons on paper: magnifier, brick with hiding place, asterisk, speech bubble, index card. |
| `assets/ui/explore/icons/mark_new.png` | 9×9 | HUD prompt marker: not yet discovered (amber twinkle). |
| `assets/ui/explore/icons/mark_seen.png` | 7×7 | HUD prompt marker: already discovered (dim tick). |
| `assets/ui/explore/icons/page_on.png`, `page_off.png`, `page_on_neutral.png` | 5×5 | DiscoveryView page indicator (copper for the find, grey for history pages). |
| `assets/ui/explore/icons/more_down.png` | 7×4 | "more text below" chevron on long pages. |
| `assets/ui/explore/icons/tape_l.png`, `tape_r.png` | 22×12 | Translucent paper tape holding the photo in the notebook (pre-rotated at 1:1). |
| `tests/visual/explore_ui_mock_closeup.png` | 240×150 | **Test harness mock only** (tea glass in a holder by a frosted window), used by `tests/visual/explore_ui_preview.tscn`; not game content. |

## Code and data delivered with the art (not assets, listed for traceability)

`scripts/ui/discovery_view.gd` + `scenes/ui/DiscoveryView.tscn` (UIRoot `discovery`), `scripts/core/explore.gd`
(validation, listings, counts), journal tabs "Entdeckungen"/"Geschichte", HUD prompt markers and toast kinds
`discovery`/`history`, settings toggle "Historische Hoheitszeichen", pause progress plate, strings in
`data/locale/de_explore_ui.json`, tests `tests/test_explore.gd`, `tests/test_explore_data.gd`, harness
`tests/visual/explore_ui_preview.tscn/.gd`.
