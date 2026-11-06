# Asset manifest — round 10 polish (NEXT_STEPS §1 „Polish from the round-9 reports“)

Area owner: polish specialist · Date: **2026-11-06, round 10** · Engine target: Godot 4.7.2

## Provenance & licence
Everything here is original project work, made by the project's own deterministic scripts (numpy / Pillow / stdlib;
no samples, no network, no third-party art, sound or text, no AI-generated pixels or audio). Project-owned, no
attribution needed.

## Files
| File | What | Made by |
|---|---|---|
| `assets/audio/sfx/c4_stamp_accept.wav`, `c4_stamp_dispatch.wav`, `c4_card_tear.wav` | re-voiced for LS_C4_Stamp (stamp surfaces over the film's beds; the perforator's tear on the picture's split) | `tools/audiogen/c4_audio.py` — details, levels and the per-beat comparison in `c4_cast_audio.md` („Round 10“) |
| removed: `sfx/c4_stencil_brush`, `c4_bell_once`, `c4_bell_twice`, `c4_lamp_out` (+ `.import`) | cast cues no picture shows (`c4_cast_audio.md`) | — |
| `data/locale/de_board_strip.json` | „+{n} weitere“, „Fäden blättern“ — the evidence board's thread pages | by hand |
| `assets/environments/veltrava_station/provenance.json` | the station generator's record of its own files (106 PNGs + `scene.json`; never `thaw/` or `walkers/`) — what its next run may remove first | `tools/pixelgen/env_veltrava_station.py` (output of a run, byte-identical otherwise) |
| `tools/pixelgen/env_keep.py` | the shared-folder rules of the three env generators (`--selftest`) | — |

## Generator hazard — the proof (2026-11-06)
`env_veltrava_hall.py`, `env_veltrava_station.py`, `env_c3p2_quay.py` were run in scratch copies of the worktree
(`tools/`, `data/`, `scenes/`, `assets/environments`, `assets/ui`, `assets/characters`; the repo itself untouched) and
every output folder diffed against the repo, byte for byte:
* **before** (round-9 code): hall lost `walkers/` (9 PNGs) and the `actors` block; station lost `thaw/` + `walkers/`
  (15 PNGs + 15 `.import`) and 2 of its 14 `actors` (AmbientWalkers, StationThaw); quay lost `walkers/` (10 rigs +
  10 `.import`) and its `actors` block. The hall's two document JSONs came out with CRLF line ends.
* **after** (two consecutive runs): every PNG, `.import`, `scene.json`, `provenance.json`, document and locale file
  byte-identical to the repo; the only new file is the station's `provenance.json` (now in the repo).
* **injected**, third run: a recorded but no longer produced hall prop is removed (and its row); a hand-made PNG in
  `props/`, a `walkers_r8.py` provenance row, a hand key in the quay's `scene.json` (kept in place) and a hand actor at
  index 5 of the station's list (kept at 5) all stay; walkers and thaw stay.
Guard: `tests/test_env_generators_keep.gd` (sources never sweep PNGs by extension; actors, walker rigs and thaw art
present; every provenance row real, no generator claims `walkers/` or `thaw/`).

**`env_berlin.py` (round 10, lead).** It never deleted files (`walkers/` and `walkers.json` of `walkers_r8.py` were
safe) but wrote `berlin_archive/scene.json` from scratch; now `KEEP.merge_scene` / `KEEP.write_json`, the plan
document JSON through `KEEP.lf_json` and `env_berlin.md` with LF. Proof in scratch copies of `tools/` +
`assets/environments/berlin_archive` (the repo untouched), diffed byte for byte:
* **before** (round-9 code): 94/94 PNGs identical, but `scene.json` lost the AmbientWalkers actor (11 → 10 actors);
  `assets/ui/documents/berlin_plans.json` and `env_berlin.md` came out with CRLF line ends.
* **after** (two consecutive runs): all 193 files of the folder (94 PNGs, every `.import`, `walkers/`, `walkers.json`,
  `scene.json` with its 11 actors) byte-identical to the repo, likewise the 10 documents and the manifest part.
* **injected**, third run: a hand actor at index 3 and a hand key after `windows` stay in place, a hand-edited value
  of a generator key comes back to the generator's, hand PNGs in `walkers/` and `props/` stay.
Guard: `test_env_generators_keep.gd` `MERGE_ONLY` (the env_keep calls, no `os.remove(` / `rmtree(` /
`json.dump(scene`; the berlin walkers' sheets and rigs exist).

## Reproduce
```bash
py -3 -P tools/pixelgen/env_keep.py --selftest
py -3 -P tools/audiogen/c4_audio.py --only c4_stamp_accept,c4_stamp_dispatch,c4_card_tear --no-analysis
# then the shared, locked import (TECHNICAL_ARCHITECTURE §1)
```
