# NEXT STEPS — Ashes of Empires: The Last Winter

State after round 8 (2026-11-06): Chapters 1–3 complete — Chapter 3 now with part 2 (radio night, the joint evidence
check „Gegenprobe“, the registry fire with the first authored in-level protagonist switches, the night quay where each
man keeps half of the file). Memories (§12.10), side tasks (§12.9), 10 optional mini-games (§12.8), 116 finds,
27 chats, 21 history cards. Main path ≈ 35 min, everything ≈ 2 h 50 min for a completionist (estimates from
`tools/docs/estimate_playtime.py`; no human playtest yet). Open work, in priority order.

## 1. Round 9 (planned 2026-11-06): Chapter 4 part 1 „Stimmen unter Beton“ + „Die Akte C-17“ + feel pass 2
Canon: STORY_BIBLE §6 row 4 and the switch-moment line („Ch4 alternates on shared objects — the same wagon number, the
same registry card“), `preproduction/narrative/FUTURE_CHAPTER_ARCS.md` „Kapitel 4“ (testimony from residential
quarters shows C-17 enables surveillance and forced resettlement; an archive path and a transport path must be joined;
decision: protecting people vs. speed of publication), CHARACTER_BIBLE (Marta Vogel, Lev Sokolov, Ludwig Wendt, …).
- **Story (contract `documentation/C4_DESIGN.md`, written first):** both men travel home with their half; Alexei follows
  the sealed wagons through the service tunnels under the Karsk freight yard to a hidden transfer siding where wagon
  numbers are repainted; Konrad maps the registry annex under the Great Hall district and hears Marta Vogel's
  testimony about the evictions along her tram route; match cuts on shared objects between the cities; Konrad's
  decision: give the annex clerk Marta's name for the household records — or protect her. Earlier decisions felt in
  line variants. A new puzzle type (tracing a wagon through the tunnel switches by its plates / repainted numbers).
  No new Story flags (saves stay valid; decisions via choice_history and `choice.<objective>` conditions).
- **Build streams:** Karsk tunnels / transfer siding art, Berlin annex art, Chapter-4 cinematics, the puzzle UI, new
  cast (Marta Vogel, Lev Sokolov, …) with living portraits + music/ambience, exploration (finds, chats, a side task,
  a new mini-game, fact-checked history cards: the GBI's evictions of Jewish tenants in Berlin 1939–42 for the
  Germania plans; the Soviet special settlements and the returns after 1956).
- **„Die Akte C-17“ (new feature):** a corkboard tab in the journal — every owned evidence item of both men as a pinned
  card with its document art, red threads between items that prove the same link („derselbe Stempel“, „dieselbe
  Wagennummer“), a growing summary „Was die Akte bisher zeigt“, no spoilers for unknown items.
- **Feel pass 2:** walkers and the side task „Eine Decke für Frau Brunner“ on the quay; walkers avoid each other and
  walk diagonally; toasts keep their time while a menu holds them; the crude figures in LS_C3_Escape / LS_C3_Halves
  redrawn with the figure pipeline; distinct Ä/Ö/Ü in the small pixel font; 1440p / 4K checks.
- **Quality gates (new this round):** four review lenses after the build (text & history, code & saves, art & UI,
  completeness against the contract), every finding verified adversarially by a second agent before an owner fixes it;
  then the lead integrates and runs every test layer (unit, autoplay, inputplay, exported exe).
- Workflow script: session scratchpad `r9/round9.js`.

## 2. Human playtest and listening pass (cannot be automated)
- Play the exported build with keyboard and a physical controller (pad A now confirms in menus — round 8 fix; never
  tried on hardware).
- Judge camera feel (including the ≈ 1.2 s switch glide in the registry), walk speed, pacing of the cinematics,
  readability of hidden finds, puzzle and mini-game difficulty (Relaispult round 3 may be hectic; „Gegenprobe“ at
  150 % text is tight), text speed.
- **Listen**: all music, ambience and ~230 SFX are synthesized and were only checked numerically (levels, loops,
  onsets) — mix against dialogue; the fire ambience (crackle density, muffled bell), the quay and the two round-8
  music cues were never heard by a person.

## 3. Known polish items (from the round-7/8 reports, not yet in round 9)
- Characters: faces share one lighting setup; women's faces still a little angular; `talk_back` only for the two
  protagonists; Kessler's rimless glasses are drawn with thin rims; Berlin mother's hair looks helmet-like.
- Station: island walkers are simple procedural figures; pigeons vanish under the canopy.
- Registry: the torch beam in scene A is a fixed veil at Konrad's partner spot; heat shimmer is subtle; flaked
  limewash patches are generic. A save taken while the stand-in walks restores him at the end of his walk.
- Mini-games: Morse/Rohrpost switch to ×2 pixel art at 125/150 % text; the cloakroom rack shows five coats, the
  hall counter six.
- 3D hall: near objects can still crawl during the crane/push; parade tribune officials are tiny (~14 px).
- Old memory prints of the Berlin archive and plaza were captured with Alexei instead of Konrad (harness bug fixed in
  round 8; prints re-captured in the round-8 integration — check).

## 4. Content for the full game (STORY_BIBLE §6)
- **Chapter 4 part 2:** the archive path and the transport path joined; consequences of the witness decision.
- **Chapters 5–6** and the assembled endings (§8: Öffentliche Akte, Stille Sicherungen, Brüchige Reform, Getrennte
  Wege, Gebrochenes Vertrauen) with epilogues. Before a round adds Story flags (STORY_BIBLE §7: `alexei_konrad_trust`,
  `marta_trust`, `evidence_chain`, `people_protected` …), saves must fill missing flags with their defaults in v3
  payloads before `validate_save_json` (otherwise every existing save breaks).
- English localisation (Loc supports more files; add a language setting); mouse click-to-walk.
- Story hook to carry forward: the "Hanna" thread in Berlin (house number 14, the porter's message) sets up the
  Chapter-5 decision about the neighbours' file.

## 5. Process
- Keep all test layers green after every change: `tests/run_all.gd`, `--autoplay` (routes × play/skip,
  `--autoplay-explore`, `--autoplay-memories`), `--inputplay` (`--inputplay-explore`, `--inputplay-memories`).
  Re-export and run the exe before calling anything done. The drivers keep their saves in `user://e2e/saves`, but
  memories still write `user://profile.json` — back up the game's user folder first and restore it afterwards (the
  user plays the same build).
- Token budget: one big round per workflow, tight briefs, filtered output, review lenses with adversarial verification
  instead of repeated full passes.
