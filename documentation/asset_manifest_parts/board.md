# Asset manifest — Evidence board „Die Akte C-17“ (area: board)

Owner: board specialist · Date: 2026-11-06 · Engine: Godot 4.7.2. Everything below is **original work** made by a
project script (no downloads, no traced or sampled reference material, no AI image models). The card pictures of
twelve items are 1:1 crops of the game's own inspect close-ups (`assets/ui/documents/*`, environment artists, rounds
1–7) — the same pixels the InspectView shows, never resampled. Contract: `documentation/TECHNICAL_ARCHITECTURE.md`
§12.12. Generator: `tools/pixelgen/gen_ui_board.py` (`py -3 -P tools/pixelgen/gen_ui_board.py`; deterministic, seeds =
crc32 of asset names). Every file is listed with its 1:1 size, scale and source in `assets/ui/board/manifest.json`;
1:1 sources in `assets/ui/board/src_1x/` (`.gdignore`, never imported). No emblem or insignia of any kind (the crops
avoid the stamps of the `_hist` close-ups; the generator writes a `_hist` crop only if a crop region differs).

## 1. Assets
| File | Size / format | Notes |
|---|---|---|
| `assets/ui/board/cork.png`, `cork_hc.png` | 192×192 RGBA (64×64 ×3) | tileable cork (periodic noise + granules); high-contrast twin dark and flat |
| `assets/ui/board/frame.png` | 90×90 (30×30 ×3), 9-patch margin 30 | archive-wood frame, mitred corners, transparent centre |
| `assets/ui/board/pin_alexei.png`, `pin_konrad.png`, `pin_red.png` | 27×30 (9×10 ×3) | push pins: steel = Alexei's finds, brass = Konrad's, red = the summary sheet |
| `assets/ui/board/card_paper.png`, `card_photo.png`, `card_burned.png` | 45×45 (15×15 ×3), 9-patch margin 15 | index card (documents), photo print (physical clues), scorched card (Blatt 7 after `admit_plan`) |
| `assets/ui/board/tag.png`, `note.png`, `ghost.png`, `focus.png`, `focus_hc.png` | 9-patches | thread caption tape, typed summary sheet (red margin rule), reserved place of an unfound item, focus rings |
| `assets/ui/board/unknown.png` | 54×66 (18×22 ×3) | empty pin with a blank „?“ tag (no spoiler) |
| `assets/ui/board/folder.png` | 372×258 (124×86 ×3) | closed manila file folder with the red C-17 stamp — the journal's cover page |
| `assets/ui/board/vtab_normal/hover/pressed/focus.png` | 33×48 | the round-1 paper tab `assets/ui/frames/ptab_*.png` turned 90° clockwise (exact): the journal divider „Akte“ |
| `assets/ui/board/thumbs/<item>.png` (12) | 162×72 (54×24 ×3) | detail crops of the inspect close-ups: Karsk seal / timetable / ledger, Berlin plans A/B, Emil's note, Veltrava weighbill / departures / travel order / seating / booth log / carbon (crop rects in `DOC_CROPS`) |
| `assets/ui/board/thumbs/<item>.png` (25) | 162×72 | original drawings for items without a close-up: Chapter 3 part 2 (cut seal, night book, intake book, Elena's scarf, the two halves, Blatt 7 + `_burned`, the file, bolted ramp door, cut hose, escort list) and Chapter 4 part 1 (book gap, cut signatures, carbons, tunnel plan, fresh tracks, eviction notice + site plan, Marta's route board, advertising column S 2, card 0417 both halves, stencils, wagon interior, drawer Süd 8, annex plan, tube slip) |
| `assets/ui/board/thumbs/_document.png`, `_physical_clue.png` | 162×72 | fallback pictures for a future item without a picture |

## 2. Palette
UI kit (`gen_ui.py` / `gen_ui_explore.py`): paper, ink, archive wood, steel and brass ramps, one red ramp for C-17
and the threads; the cork ramp is a muted brown so the red thread reads on it (and a dark flat cork in high contrast).
