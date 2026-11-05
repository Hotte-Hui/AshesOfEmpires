# Asset manifest part — credits (end credits roll + source list)

Date: 2026-11-05. No new image, audio or font assets: everything is built at runtime from existing UI assets.

| Item | Path | Origin / generator | Licence |
|---|---|---|---|
| End credits scene | `scenes/ui/EndCredits.tscn`, `scripts/ui/end_credits.gd` | Hand-written GDScript. Reel built in code: title page, alternative-history note, production credits (`ui.credits.*`), "Quellen der historischen Karten" (all cards from `Explore.cards_list()` / `card()`), end page | Project code |
| Edge fades | runtime `GradientTexture2D` (background colour → transparent, 150 px top/bottom) | generated in `end_credits.gd` | Project code |
| Snow backdrop | `scripts/ui/snow_field.gd` (existing title-screen generator), alpha 0.35 (HC 0.2) | reused | Project code |
| Ornament | `assets/ui/icons/ornament_diamond.png` (existing) | reused | see `ui.md` |
| Fonts | `assets/fonts/fv_*.tres` (PT Serif, PT Mono, Oswald — existing) | reused | SIL OFL 1.1 |
| Music | `assets/audio/music/mus_menu.wav` (existing), played via `Audio.play_music` | reused | see `audio.md` |
| Text | `data/locale/de_credits.json` (`credits.end.*`, `credits.src.*`) | written for this round | Project text |
| Source labels / URLs | `data/explore/history_reich.json`, `history_soviet.json` (16 cards, 78 sources) | displayed as stored, not modified | Bibliographic references |

Main-menu "Mitwirkende" panel (`scripts/ui/credits.gd`) shows the same source list (shared builder
`EndCredits.add_source_list`) plus a footer button "Zu den Quellen" / "Zum Anfang".

Verification: `tests/test_end_credits.gd` (6 cases, 433 checks); windowed harness screenshots (start, production,
two source pages, end; normal and high contrast + text scale 1.5) taken outside the project (scratchpad).
