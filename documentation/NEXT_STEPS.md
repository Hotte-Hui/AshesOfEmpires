# NEXT STEPS — Ashes of Empires: The Last Winter

State after round 9 (2026-11-06): Chapters 1–3 complete, Chapter 4 part 1 „Stimmen unter Beton“ playable (Karsk tunnels
and transfer siding with Lev Sokolov, Berlin tram loop Süd 8 with Marta Vogel and the registry annex „Nebenstelle Süd“,
decision c4d: name Marta or protect her). New: the evidence board „Die Akte C-17“ in the journal, feel pass 2 (quay
walkers, the blanket task, distinct umlauts, 150 % text fit). 151 finds, 35 chats, 12 mini-games, 9 tasks, 25 history
cards, 7 decisions. Main path ≈ 49 min, everything ≈ 3 h 40 min (estimates from `tools/docs/estimate_playtime.py`; no
human playtest yet). Open work, in priority order. The user asked to stop after round 9; round 10 below is a plan, not
started.

## 1. Round 10 (proposal): save migration, Chapter 4 part 2, polish from the round-9 reports
- **Save migration first (prerequisite for every later chapter):** v3 payloads fill missing Story flags with their
  defaults before `validate_save_json`, with tests on saves of every earlier shape (round 7 / 8 / 9 forms, finished
  playthroughs, memory snapshots) and on the user's real saves (copies). Only then add the STORY_BIBLE §7 flags
  (`alexei_konrad_trust`, `marta_trust`, `people_protected`, …).
- **Chapter 4 part 2 (STORY_BIBLE §6 row 4, `preproduction/narrative/FUTURE_CHAPTER_ARCS.md` „Kapitel 4“), contract
  `documentation/C4P2_DESIGN.md` written first:** the archive path and the transport path are joined — the two halves of
  card 0417 and the run „C-17/45, Tuesday 23.40“ (the chalk „ВТ 23.40“ on wagon 24 318) meet; the witness decision
  has consequences (named: Wendt's questioning, Marta's route; protected: the deadline, Konrad under suspicion);
  decision: protecting people vs. speed of publication. One new puzzle type, one in-level switch scene on a shared
  object, new cast only where the story needs it, memories / board / history cards for the new places.
- **Polish from the round-9 reports:**
  - seven cast-audio cues (`c4_stencil_brush`, `c4_card_tear`, `c4_stamp_accept`, `c4_stamp_dispatch`,
    `c4_bell_once`, `c4_bell_twice`, `c4_lamp_out`) are generated but unused — the films use their own `c4cine_*`
    sounds; wire the better one per beat or drop the rest;
  - evidence board: the detail strip's thread list ends in „…“ on cards with three or more thread groups (the cork
    shows them all) — show a count or let the strip page; close-ups for the Chapter-3-part-2 / Chapter-4 items that
    still open their board picture instead of a document;
  - generator hazard: `env_veltrava_hall.py`, `env_veltrava_station.py`, `env_c3p2_quay.py` and `env_berlin.py` delete
    every PNG in their env folder and rewrite `scene.json` — they would drop the round-8/9 walker rigs and the
    hand-added `actors` blocks; make them preserve both before anyone reruns them;
  - films: the stamp fists in LS_C4_Stamp are blocky, Konrad is small in s4 / n4, Fengler appears only as hands;
  - InspectView: the notice and plan captions move into the record card at 150 % (by design, check readability);
  - Game ignores the `"grade"` key of c4.json switches on a level load (the annex sets its looks itself);
  - `documentation/screenshots/c4_annex_b_*` predate the counter fix; L_M1_HallReveal / L_M1_Parade have no hi-res
    capture frame.

## 2. Human playtest and listening pass (cannot be automated)
- Play the exported build with keyboard and a physical controller (pad A confirms in menus since round 8; never tried
  on hardware).
- Judge camera feel (the ≈ 1.2 s switch glide in the registry), walk speed, pacing of the cinematics, readability of
  hidden finds, puzzle and mini-game difficulty (Relaispult round 3, „Gegenprobe“ at 150 %, the new „Linie 74“ and
  „Die Nummernkette“, the Hebelrahmen and the Lüftungsklappen), text speed, the evidence board at 150 %.
- **Listen**: all 13 music cues, 13 ambiences and 259 SFX are synthesized and were only checked numerically — mix against
  dialogue; never heard by a person: the fire and quay sounds, the Chapter-4 music (the synthetic bayan in
  `mus_c4_karsk`), the trains over the Karsk tunnels, the annex fans and tube capsules.

## 3. Known polish items (older reports)
- Characters: faces share one lighting setup; women's faces still a little angular; `talk_back` only for the two
  protagonists; Kessler's rimless glasses have thin rims; the Berlin mother's hair looks helmet-like; Fengler's
  portrait came out leaner than „well fed“.
- Station: island walkers are simple procedural figures; pigeons vanish under the canopy.
- Registry: the torch beam in scene A is a fixed veil; heat shimmer is subtle; a save taken while the stand-in walks
  restores him at the end of his walk.
- Mini-games: Morse / Rohrpost switch to ×2 pixel art at 125 / 150 % text; the cloakroom rack shows five coats, the
  hall counter six.
- 3D hall: near objects can crawl during the crane / push; parade tribune officials are tiny (~14 px).

## 4. Content for the full game (STORY_BIBLE §6)
- **Chapters 5–6** and the assembled endings (§8: Öffentliche Akte, Stille Sicherungen, Brüchige Reform, Getrennte
  Wege, Gebrochenes Vertrauen) with epilogues — after the save migration (§1).
- Story hooks to carry forward: the „Hanna“ thread in Berlin (house number 14, the porter's message; Ilse sits beside
  Hanna in class — c4d protect line) sets up the Chapter-5 decision about the neighbours' file; Lev's fourteen names
  „in two papers“; Elena's disappearance after the radio night.
- English localisation (Loc supports more files; add a language setting); mouse click-to-walk.

## 5. Process
- Keep all test layers green after every change: `tests/run_all.gd`, `--autoplay` (7 choices per route since round 9;
  play / skip, `--autoplay-explore`, `--autoplay-memories`), `--inputplay` (`--inputplay-explore`,
  `--inputplay-memories`). Re-export and run the exe before calling anything done. The drivers keep their saves in
  `user://e2e/saves`; back up the game's user folder first anyway and restore it afterwards (the user plays the same
  build).
- Round recipe that worked in rounds 8–9: contract document first, parallel build streams with one owner per file,
  four review lenses with adversarial verification, a small integration fix pass with its own review, then the lead's
  full test layers. Briefs stay tight, outputs filtered.
