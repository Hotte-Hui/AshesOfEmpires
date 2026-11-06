# NEXT STEPS — Ashes of Empires: The Last Winter

State after round 10 (2026-11-07): Chapters 1–4 complete — Chapter 4 part 2 joined the archive and the transport
path (Karsk depot, Berlin Ostbahnhof, Kolonnenstraße 14; decision c4g). The user's screenshot feedback and a
cinematics overhaul (13 films) are in; saves fill missing Story flags with defaults. 185 finds, 46 chats, 14
mini-games, 11 tasks, 29 history cards, 8 decisions. Main path ≈ 64 min, everything ≈ 4 h 35 min (estimates; no
human playtest yet). Open work, in priority order.

## 1. Round 11 (proposal): Chapter 5 „Der Preis des Friedens“, part 1 — and the user's verdict on the films
- **First, the user's keep / revert list** for the reworked cinematics (before/after sheets sent 2026-11-06): revert
  single films or shots from git (`4e9ba05` = round 9) where the user prefers the old version.
- **Chapter 5 part 1** (STORY_BIBLE §6 row 5, FUTURE_CHAPTER_ARCS „Kapitel 5“): the infrastructure also has real
  civilian use; an abrupt collapse would endanger residents, silence would too — contract `C5_DESIGN.md` first; the
  c4g decision (publish_now / protect_first) and `people_protected` drive the opening; the Hanna thread (house 14).
- **Open polish:** the photographer in a C4P2 film is drawn from a stand-in until its rig spec exists; close-ups for
  the Chapter-3-part-2 / Chapter-4 items that open their board picture; `env_c4_tunnels.py` / `env_c3p2_archive.py`
  through `env_keep.py` before anyone adds walkers there; hi-res capture frames for L_M1_HallReveal / L_M1_Parade.
- **Budget:** the user asked to keep rounds cheap — one workflow at a time, art directors only where the user looks
  (cinematics, places), lean final checks instead of 12-agent review phases, before/after sheets instead of repeated
  captures. No fiction disclaimers in new texts.

## 1b. Round 10 (done 2026-11-07, plan as it was): save migration, Chapter 4 part 2, polish from the round-9 reports
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
  - **done (round 10):** the seven cast-audio cues — `c4_stamp_accept` / `c4_stamp_dispatch` are re-voiced as surface
    layers over the `c4cine_*` beds and `c4_card_tear` sits on the perforator in LS_C4_Stamp s3b;
    `c4_stencil_brush`, `c4_bell_once`, `c4_bell_twice` and `c4_lamp_out` are dropped (generator, test, manifest,
    disk);
  - **done (round 10):** the evidence board's detail strip pages its threads in whole groups („+n weitere“, kicker
    „ROTE FÄDEN: 7 · 1/3“; F, pad X, a click or the wheel turn the pages). Still open: close-ups for the
    Chapter-3-part-2 / Chapter-4 items that still open their board picture instead of a document;
  - **done (round 10) for hall / station / quay:** the generator hazard — `tools/pixelgen/env_keep.py`: a generator
    removes only the PNGs its own last run recorded and merges `scene.json` / `provenance.json`. **Done (round 10,
    lead):** `env_berlin.py` (`KEEP.merge_scene` / `KEEP.write_json`: `berlin_archive/scene.json` keeps the round-8
    AmbientWalkers actor; it deletes nothing, so `walkers/` stays; its plan JSON and manifest part are written with LF —
    a re-run in a scratch copy is byte-identical, `polish_r10.md`). Still open: `env_c4_tunnels.py` /
    `env_c3p2_archive.py` before anyone adds walkers or actors to their folders;
  - films: the stamp fists in LS_C4_Stamp are blocky, Konrad is small in s4 / n4, Fengler appears only as hands;
  - InspectView: the notice and plan captions move into the record card at 150 % (by design, check readability);
  - **done (round 10):** Game applies a switch's `"grade"` on a level load (`Game._apply_switch_grade`, unless the
    level has grade looks);
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
- Round 10, never heard either: the stamp layers in LS_C4_Stamp (−5 dB over the beds) and the card tear (−6 dB); the
  band rehearsing the march in `amb_karsk_platform`, the radio level in `amb_berlin_courtyard`, the clock's tick under
  the drone in LS_C4P2_Clock. Board paging with F / pad X has not been tried on hardware.

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
