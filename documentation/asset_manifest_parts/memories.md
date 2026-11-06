# Asset manifest — Memories („Erinnerungen“, area: memories)

Owner: memories specialist · Date: 2026-11-06 · Engine: Godot 4.7.2. Everything below is **original work** made by
project scripts from the game itself (no downloads, no traced or sampled material, no AI image/audio models).
Contract: `documentation/TECHNICAL_ARCHITECTURE.md` §12.10.

## 1. Assets
| File | Size / format | Generator | Notes |
|---|---|---|---|
| `assets/ui/memories/L_A1_Railyard.png` | 320×180 RGB | `tools/pixelgen/gen_ui_memories.py` from `src/raw_L_A1_Railyard.png` | Sepia print for the MemoryView card: crop (236,126) of the 640×360 world frame, 1 world px = 1 print px. |
| `assets/ui/memories/L_M1_Archive.png` | 320×180 RGB | same, `src/raw_L_M1_Archive.png` | crop (196,146): drafting table, lamp, window light. |
| `assets/ui/memories/L_M1_Plaza.png` | 320×180 RGB | same, `src/raw_L_M1_Plaza.png` | crop (214,92): dome, plain eagle (neutral twin), ranks. |
| `assets/ui/memories/L_C3_Station.png` | 320×180 RGB | same, `src/raw_L_C3_Station.png` | crop (120,56): clock tower, arch window, departures board. |
| `assets/ui/memories/L_C3_Hall.png` | 320×180 RGB | same, `src/raw_L_C3_Hall.png` | crop (150,50): staircase, chandelier, gallery door. |
| `assets/ui/memories/L_C3_RegistryA.png` | 320×180 RGB | same, `src/raw_L_C3_RegistryA.png` | crop (150,124): Alexei in the snowy yard at night, yard lamp, cart with crates (round 8). |
| `assets/ui/memories/L_C3_RegistryB.png` | 320×180 RGB | same, `src/raw_L_C3_RegistryB.png` | crop (236,124): Konrad and Alexei at the sorting table under the green lamp (round 8). |
| `assets/ui/memories/L_C3_RegistryC.png` | 320×180 RGB | same, `src/raw_L_C3_RegistryC.png` | crop (320,124): Alexei (soot look) by the card cabinet, the fire front (round 8). |
| `assets/ui/memories/L_C3_RegistryD.png` | 320×180 RGB | same, `src/raw_L_C3_RegistryD.png` | crop (100,124): Konrad before the lit porter's booth, fire to the right (round 8). |
| `assets/ui/memories/L_C3_Quay.png` | 320×180 RGB | same, `src/raw_L_C3_Quay.png` | crop (225,124): the burning wing, fire engine, Alexei under a lantern by the river (round 8). |
| `assets/ui/memories/L_C4_TunnelsA.png` | 320×180 RGB | same, `src/raw_L_C4_TunnelsA.png` | crop (260,128): the archive cellar, Alexei and Lev at the desk under the green-shaded lamp, samovar and stove (round 9 fix, camera 40 inside camera_zones `L_C4_TunnelsA`). |
| `assets/ui/memories/L_C4_AnnexA.png` | 320×180 RGB | same, `src/raw_L_C4_AnnexA.png` | crop (130,128): the tram loop Süd 8 at dawn, the lit timetable case, Konrad and Marta at tram 74 (round 9 fix, camera 120). |
| `assets/ui/memories/L_C4_TunnelsB.png` | 320×180 RGB | same, `src/raw_L_C4_TunnelsB.png` | crop (218,128): the transfer siding, wagon 24 318 with the fresh stencil C-17/45, Alexei at x 1712 facing Lev at his siding post (round 9 fix, camera 1280; the harness loads each scene as a memory of itself). |
| `assets/ui/memories/L_C4_AnnexB.png` | 320×180 RGB | same, `src/raw_L_C4_AnnexB.png` | crop (262,128): Nebenstelle Süd, the tube station, the bench „Warten bis zum Aufruf“ under the number 17, the counter „Auskunft · Abgleich“ with Fengler behind it, Konrad (round 9 fix, camera 1200). |
| `assets/ui/memories/icon_memory.png` | 39×39 RGBA (13×13 drawn ×3) | same | Pocket watch at nine o'clock, amber arc + arrow tip on the rim (time running back). UI kit palette. |
| `assets/ui/memories/manifest.json` | JSON | same | Files, sizes, crops, sources. |
| `assets/ui/memories/src/raw_<scene>.png` (14) | 640×360 RGB, `.gdignore` (not imported) | `tests/visual/memory_thumbs.tscn` | In-game captures (`PixelView.capture_world_image`, graded, one sample per texel) at fixed camera/player spots, **`--symbols=0`**: the neutral insignia twins — real regime insignia never appear in a menu (§12.4). |
| `assets/audio/sfx/mem_rewind.wav` | 2.9 s, 44.1 kHz 16-bit stereo | `tools/audiogen/memories_audio.py` | Pocket-clock ticks time-reversed and speeding up (winding back), reversed airy swell with a soft release, faint tape-wow drone sinking 196→176 Hz, hushed low settle. Peak −5 dBFS, RMS −26 dBFS. No chime, no fanfare. |
| `assets/audio/sfx/mem_return.wav` | 2.6 s, same format | same | The same clock forward, fast at first, settling into tick-tock; the swell from its peak fading out; drone rising back. Peak −5 dBFS, RMS −31 dBFS. |

Determinism: `gen_ui_memories.py` and `memories_audio.py` are seeded (zlib.crc32 of the names) and write byte-identical
files on every run (checked twice: md5 of both WAVs and all PNGs unchanged). The raw captures are renderings of the
running game (snow, walkers, smoke move), so a re-capture gives slightly different frames; the print step from a given
raw frame is deterministic.

Reproduce:
```bash
GODOT="$LOCALAPPDATA/Programs/Godot/Godot_v4.7.2-stable_win64_console.exe"
"$GODOT" --path . res://tests/visual/memory_thumbs.tscn -- --scene=L_A1_Railyard --capture=C:/tmp/boot.png \
    --frames=100000 --mt-out=C:/Spiele/AshesOfEmpires/assets/ui/memories/src --symbols=0
py -3 -P tools/pixelgen/gen_ui_memories.py
py -3 -P tools/audiogen/memories_audio.py
# then the shared --import (lock .import_lock)
```
`--mt-survey=1` captures a 320-px camera sweep per level (to choose the spots in `SHOTS` / `CROPS`).

## 2. Code / data
* `scripts/core/memories.gd` (helper), `scripts/core/game.gd` (memory mode, transitions, films), `scripts/core/memory_drive.gd`
  (E2E helpers + `--memory-demo`), `scripts/ui/memory_view.gd` + `scenes/ui/MemoryView.tscn`, HUD badge (`hud.gd`),
  pause / main menu entries, save guard (`save_system.gd`, `save_load_menu.gd`).
* `data/grades.json` → `"memory"` overlay preset. Strings: `data/locale/de_memories.json` (UI, places, months, prompts,
  remembered lines, film titles, `sys.save.err.memory`).
* Profile file at runtime: `user://profile.json` (not shipped).

## 3. Content notes
Remembered lines are first person, past tense, in the protagonists' voices; they only state what the player did
(the decision taken, the puzzle solved) — nothing new is invented. Dates are months („Januar 1964“, „Februar 1964“),
no invented days. No reward language; the finds counter is the same neutral counter as elsewhere.
