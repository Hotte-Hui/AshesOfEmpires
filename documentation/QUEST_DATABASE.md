# QUEST DATABASE — Vertical Slice (A1 · M1 · X1)

Status: AUTHORED 2026-11-04 by the story_engine area from the canonical data `data/v3/*.json` and the preproduction
narrative (`preproduction/narrative/CHOICE_CONSEQUENCE_MATRIX_V4.md`, `VERTICAL_SLICE_SCRIPT_V3.md`,
`FUTURE_CHAPTER_ARCS.md`, `CHAPTER_OUTLINE.md`). German player text is quoted from `data/v3/locale_de.json`.
The German protagonist is **Konrad Adler** (id `konrad`; renamed from the preproduction draft name on the user's
request of 2026-11-04). Runtime: `scripts/story/story_engine.gd` (autoload `Story`), saves: `scripts/core/save_system.gd`
(autoload `Saves`). Verified by `tests/test_quest_database.gd` (every id below exists in the data and vice versa) and
`tests/test_reference_parity.gd` (runtime behaviour identical to `preproduction/tools/story_engine_v4.py`).

---

## 0. Runtime rules (apply to every entry below)

| Rule | Behaviour (identical to the Python reference) |
|---|---|
| Objective states | `locked → available → complete`; never regress except `Story.new_game()`. |
| Availability | An objective is **available** iff (1) its quest's `scene` is the current scene, (2) the quest's `requires_events` are all completed, (3) all objectives in its `requires` are complete, (4) it is not complete. Locked objectives show no interaction prompt (TECHNICAL_ARCHITECTURE §5.2). |
| Completion paths | `inspect` → `Story.inspect(id)`. `dialogue` → `start_dialogue` + `advance_dialogue` until the **terminal node** (only then complete). `puzzle` → `solve_puzzle(id, typed answer)` with all clue items in the inventory. `choice` → `choose(id, choice_id)` with exactly one valid choice id. Nothing else can complete an objective. |
| Transaction | On completion, in this order and exactly once: effects → objective recorded → item granted (if not yet owned) → choice recorded → if the quest is now complete: completion event (once) → scene switches to the scene's `next_scene`, protagonist becomes that scene's `protagonist`. Failed calls change nothing. |
| Effects | Integer flags: `{"delta": n}`, clamped to `[min, max]`. Boolean flags: `{"set": bool}`. |
| Puzzles | Unlimited retries, no penalty. A wrong but well-typed answer counts one attempt; a malformed answer is rejected and not counted. The hint becomes available at `hint_after_attempts` failures (`Story.puzzle_hint_available`). |
| Cinematics | Queued when their trigger objective/event completes; `consume_cinematic(id, skipped)` marks them seen once. **Skipping has no story effect** (scene changes happen at the event, not in the cinematic). |
| Finale | `Story.finale()` requires current scene `L_X1_Montage` and every event in `slice_end_requires`; adds `slice_completed` and sets `slice_finished` once; idempotent afterwards; sets `finale_viewed`. Watching the cinematics is not required. |

Signals (`Story`): `objective_completed(id)`, `item_granted(id)`, `flag_changed(name, value)`, `event_fired(id)`,
`cinematic_queued(id)`, `scene_changed(scene_id)` — emitted after the transaction is committed; plus
`state_replaced(reason)` after `new_game()` / `load_json()`.

---

## 1. Scene flow

| Order | Scene | Title (de) | Protagonist | Camera | Entry spawn | Quest | Exit event | Next scene | Render profile |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `L_A1_Railyard` | Verladebahnhof Karsk (fiktiv) | `alexei` | `oblique_2_5d` | `SP_A1_Platform` | `q_a1_last_signal` | `a1_completed` | `L_M1_Archive` | `rp_soviet_dusk` |
| 2 | `L_M1_Archive` | Berliner Bauarchiv (alternative Geschichte) | `konrad` | `side_on_2d_plus_3d_reveal` | `SP_M1_Office` | `q_m1_wrong_blueprint` | `m1_completed` | `L_X1_Montage` | `rp_berlin_copper` |
| 3 | `L_X1_Montage` | Zwei Städte – ein Dokument | `none` | `cinematic` | `none` | — | `slice_completed` | — | `rp_transition` |

Start scene: `L_A1_Railyard`. Protagonist switches happen **only** through the completion events (no swap menu).
Chapter keys for save slots / HUD: `ui.chapter_a1` „Das letzte Signal“, `ui.chapter_m1` „Die falsche Zeichnung“;
the montage uses its scene title `world.x1.title`.

---

## 2. Quests

| Quest | Title (de) | Character | Scene | Gate (`requires_events`) | Completion event |
|---|---|---|---|---|---|
| `q_a1_last_signal` | Das letzte Signal (`ui.chapter_a1`) | `alexei` | `L_A1_Railyard` | — | `a1_completed` |
| `q_m1_wrong_blueprint` | Die falsche Zeichnung (`ui.chapter_m1`) | `konrad` | `L_M1_Archive` | `a1_completed` | `m1_completed` |

### 2.1 A1 — „Das letzte Signal“ (Alexei, Karsk)

```
a1_talk_irina ─┬─> a1_inspect_seal ──────┐
               └─> a1_inspect_timetable ─┴─> a1_solve_signal ─> a1_inspect_ledger ─> a1_choose ══> a1_completed
```

| Objective | Type | Objective text (de) | Requires | Grants | Effects | Details |
|---|---|---|---|---|---|---|
| `a1_talk_irina` | dialogue | Sprich mit Irina über die fehlenden Waggons. | — | — | — | `dlg_a1_irina`, 5 nodes |
| `a1_inspect_seal` | inspect | Untersuche das beschädigte Siegel. | `a1_talk_irina` | `ev_damaged_seal` | — | any order with the timetable |
| `a1_inspect_timetable` | inspect | Vergleiche den Fahrplan. | `a1_talk_irina` | `ev_timetable` | — | any order with the seal |
| `a1_solve_signal` | puzzle | Löse das fiktive Signal-Rätsel am stillgelegten Übungskasten. | `a1_inspect_seal`, `a1_inspect_timetable` | — | `signal_restored = true` | `pz_signal` |
| `a1_inspect_ledger` | inspect | Prüfe das geänderte Frachtbuch. | `a1_solve_signal` | `ev_ledger` | `c17_confirmed = true` | |
| `a1_choose` | choice | Entscheide, was du Irina erzählst. | `a1_inspect_ledger` | — | per choice (§7) | `share_with_irina` / `keep_private` |

### 2.2 M1 — „Die falsche Zeichnung“ (Konrad, Berlin)

```
m1_inspect_plan_a ─┐
m1_inspect_plan_b ─┴─> m1_align_plans ─> m1_talk_emil ─> m1_choose ══> m1_completed
```

| Objective | Type | Objective text (de) | Requires | Grants | Effects | Details |
|---|---|---|---|---|---|---|
| `m1_inspect_plan_a` | inspect | Untersuche den genehmigten Bauplan. | — | `ev_plan_a` | — | any order with plan B |
| `m1_inspect_plan_b` | inspect | Untersuche den älteren Bauplan. | — | `ev_plan_b` | — | any order with plan A |
| `m1_align_plans` | puzzle | Lege beide Zeichnungen übereinander. | `m1_inspect_plan_a`, `m1_inspect_plan_b` | — | `blueprint_match_confirmed = true` | `pz_blueprint`; queues `LS_M1_Hall` |
| `m1_talk_emil` | dialogue | Sprich mit Emil über die Abweichung. | `m1_align_plans` | `ev_emil_note` | — | `dlg_m1_emil`, 5 nodes; item granted at the terminal node |
| `m1_choose` | choice | Entscheide, was mit dem Hinweis geschieht. | `m1_talk_emil` | — | per choice (§7) | `preserve_evidence` / `request_explanation` |

---

## 3. Dialogues

Lines advance one node per `advance_dialogue`; a dialogue saved mid-way resumes at the exact node; restarting an
unfinished dialogue resumes (never resets). Expressions per line are presentation data in `game.gd`.

**`dlg_a1_irina`** (objective `a1_talk_irina`, entry `irina_01`)

| Node | Speaker | Text key | Line (de) |
|---|---|---|---|
| `irina_01` | irina | `dlg.irina.01` | Der Zug kam pünktlich. Die Wagen in den Papieren kamen nicht mit. |
| `alexei_01` | alexei | `dlg.alexei.01` | Was fehlt genau? |
| `irina_02` | irina | `dlg.irina.02` | Drei Nummern. Und ein Ziel, das auf keiner öffentlichen Karte steht. |
| `alexei_02` | alexei | `dlg.alexei.02` | Gib mir den Fahrplan und das Siegel. Ich prüfe es selbst. |
| `irina_03` (end) | irina | `dlg.irina.03` | Dann schau zweimal hin. Einmal für die Akte, einmal für die Menschen. |

**`dlg_m1_emil`** (objective `m1_talk_emil`, entry `emil_01`; completing it grants `ev_emil_note`)

| Node | Speaker | Text key | Line (de) |
|---|---|---|---|
| `emil_01` | emil | `dlg.emil.01` | Es gibt die Pläne, nach denen gebaut wird. Und die, die man abheftet. |
| `konrad_01` | konrad | `dlg.konrad.01` | Beide tragen dieselbe Genehmigung. Das ist unmöglich. |
| `emil_02` | emil | `dlg.emil.02` | Unmöglich ist im Archiv nur, was niemand eintragen darf. |
| `konrad_02` | konrad | `dlg.konrad.02` | Hier ist eine zweite Wand. Dahinter führt ein Korridor weiter. |
| `emil_03` (end) | emil | `dlg.emil.03` | Die Kennung C-17 ist kein Raum. Sie ist eine Serie von Verträgen. |

Choice reaction lines (played by the director after the choice; not story state): `dlg.irina.branch_a`,
`dlg.irina.branch_b`, `dlg.konrad.branch_a`, `dlg.konrad.branch_b` (§7.1).

Journal „Personen“: non-protagonist speakers of every dialogue node the player has reached — `irina` from her first
line, `emil` from his first line (names/notes: `sys.journal.person.<id>.name|note`).

---

## 4. Puzzles

| Puzzle | Objective | Type | Clue items (must be owned) | Shown | Solution | Hint after | Notes |
|---|---|---|---|---|---|---|---|
| `pz_signal` | `a1_solve_signal` | `symbol_order` | `ev_damaged_seal`, `ev_timetable` | `triangle, square, circle` | `["square", "circle", "triangle"]` | 2 failures | Fictional, disconnected teaching board — not a real rail signalling procedure. Answer: Array/PackedStringArray of symbol ids; lists of the wrong length count as attempts. |
| `pz_blueprint` | `m1_align_plans` | `overlay_alignment` | `ev_plan_a`, `ev_plan_b` | two plan sheets on a grid | `{"rotation_steps": 0, "offset_x": 2, "offset_y": -1}` | 2 failures | Simplified fictional overlay. Answer: Dictionary with exactly these three keys, **integer** values only (floats/bools are rejected, not counted). |

Both: `retry_unlimited = true`, `max_penalty 0` / `snap_tolerance 0`; success sets the objective's boolean flag once.
UI may combine the hint flag with the player option `Settings.puzzle_hints` (0 off / 1 after 2 fails / 2 immediately).
`Story.puzzle_for(objective)` returns the definition **without** the solution.

---

## 5. Evidence (inventory)

| Item | Name (de) | Description (de) | Category | Scene | Granted by |
|---|---|---|---|---|---|
| `ev_damaged_seal` | Beschädigtes Siegel | Die Nummer wurde doppelt gestempelt. Unter dem Abrieb steht C-17. | physical_clue | `L_A1_Railyard` | `a1_inspect_seal` |
| `ev_timetable` | Dienstfahrplan | Drei Wagen wurden umgebucht, ohne dass ein Zielbahnhof genannt wird. | document | `L_A1_Railyard` | `a1_inspect_timetable` |
| `ev_ledger` | Frachtbuch | Eine neue Zeile trägt dieselbe Kennung C-17. Der Empfänger ist geschwärzt. | document | `L_A1_Railyard` | `a1_inspect_ledger` |
| `ev_plan_a` | Genehmigter Plan | Der öffentliche Grundriss zeigt einen abgeschlossenen Versorgungstrakt. | document | `L_M1_Archive` | `m1_inspect_plan_a` |
| `ev_plan_b` | Archivierter Vorentwurf | Im früheren Entwurf verläuft hinter der Wand ein Korridor. | document | `L_M1_Archive` | `m1_inspect_plan_b` |
| `ev_emil_note` | Emils Notiz | Die Archivnummer verweist auf eine grenzübergreifende Bauserie: C-17. | document | `L_M1_Archive` | `m1_talk_emil` |

Items are granted once, in acquisition order (= journal order). Inventory survives the protagonist switch.

---

## 6. Flags and events

| Flag | Type | Default | Range | Changed by | Meaning |
|---|---|---|---|---|---|
| `irina_trust` | integer | 0 | 0–3 | `a1_choose = share_with_irina` (+1) | Irina's trust in Alexei; Chapter-3 depot witness (§7.3) |
| `alexei_secrecy` | integer | 0 | 0–3 | `a1_choose = keep_private` (+1) | Alexei keeps evidence to himself; short-term protection, later accountability |
| `konrad_evidence` | integer | 0 | 0–3 | `m1_choose = preserve_evidence` (+1) | Konrad holds an independent copy of the record |
| `office_suspicion` | integer | 0 | 0–3 | `m1_choose = request_explanation` (+1) | The archive administration is alerted by the official request |
| `civilian_welfare` | integer | 0 | 0–3 | — (not changed in the slice) | Reserved for concrete civilian-protection actions in Chapters 4–5 |
| `c17_confirmed` | boolean | false | — | `a1_inspect_ledger` | The C-17 entry is confirmed in the freight ledger |
| `signal_restored` | boolean | false | — | `a1_solve_signal` | Teaching-board puzzle solved |
| `blueprint_match_confirmed` | boolean | false | — | `m1_align_plans` | Overlay reveals the corridor behind the wall |
| `slice_finished` | boolean | false | — | `Story.finale()` (once) | Demo end reached |

No moral score: every branch writes its **own** meter (CHOICE_CONSEQUENCE_MATRIX_V4: „no numerical Good/Evil alignment“).
Accessors: `Story.flag(name)`, `Story.flags()`, `Story.relationship(name)`, `Story.relationships()`.

| Event | Fired when | Consequences |
|---|---|---|
| `a1_completed` | last A1 objective (`a1_choose`) completes | scene → `L_M1_Archive`, protagonist → `konrad`, queues `LS_A1_ToM1`, unlocks `q_m1_wrong_blueprint` |
| `m1_completed` | last M1 objective (`m1_choose`) completes | scene → `L_X1_Montage`, protagonist → `none`, queues `LS_X1_Final`, finale gate open |
| `slice_completed` | `Story.finale()` (first call) | sets `slice_finished = true`; `finale_viewed = true` |

---

## 7. Choices and consequences

### 7.1 The two decisions of the slice

| Objective | Choice id | Text (de) | Effect | Reaction line (de) |
|---|---|---|---|---|
| `a1_choose` „Entscheide, was du Irina erzählst.“ | `share_with_irina` | Irina die vollständige Abweichung zeigen | `irina_trust +1` | Irina: „Ich sage dir Bescheid, bevor ich etwas melde.“ (`dlg.irina.branch_a`) |
| | `keep_private` | Den Hinweis vorerst für dich behalten | `alexei_secrecy +1` | Irina: „Je weniger du weißt, desto sicherer bist du vielleicht.“ (`dlg.irina.branch_b`) |
| `m1_choose` „Entscheide, was mit dem Hinweis geschieht.“ | `preserve_evidence` | Eine eigene Kopie des Vermerks sichern | `konrad_evidence +1` | Konrad: „Ich behalte eine Kopie. Das Original bleibt hier.“ (`dlg.konrad.branch_a`) |
| | `request_explanation` | Eine offizielle Stellungnahme verlangen | `office_suspicion +1` | Konrad: „Ich stelle eine offizielle Anfrage. Es muss einen Vermerk geben.“ (`dlg.konrad.branch_b`) |

Each decision is applied exactly once, is irreversible within the save branch, is recorded in `choice_history` and in
the journal (`journal().decisions`), and **does not change progression gating** (all four combinations unlock the same
objectives in the same order — `tests/test_branches.gd`).

### 7.2 Branch matrix (immediate slice state → planned Chapter 3)

| Alexei | Konrad | Slice end state | Chapter 3 planned response | Later cost (planned, not promised) |
|---|---|---|---|---|
| shares with Irina | keeps a copy | `irina_trust=1`, `konrad_evidence=1` | Irina can corroborate the freight discrepancy; Konrad brings an independently preserved record. | People who helped carry the risk of being identified. |
| shares with Irina | files an official request | `irina_trust=1`, `office_suspicion=1` | Depot witness plus paper trail, but the archive is alerted. | Fast verification may be traded for scrutiny. |
| keeps it private | keeps a copy | `alexei_secrecy=1`, `konrad_evidence=1` | Strong documentary match, weak early trust between sources. | Delay in warning affected civilians. |
| keeps it private | files an official request | `alexei_secrecy=1`, `office_suspicion=1` | Official correspondence links the sites while Alexei's motive remains unclear. | Procedure protects a trail but enables obstruction. |

All four end states are distinct saves; the finale and the montage are the same for all of them (verified).

### 7.3 Planned Chapter-3 callbacks — PLANNED, NOT IMPLEMENTED

Chapter 3 „Der eiserne Frieden“: Alexei and Konrad arrive separately in a neutral border conference town (Alexei by
rail, Konrad with an official delegation) and investigate the vanished interpreter's notes; the interpreter Elena knows
only fragments. Their first in-person meeting happens **here, not in the slice**; cooperation is limited, tense and
mistrustful, and each holds only part of the evidence. The hooks below are the contract for that chapter: every
slice decision has at least one callback (matrix acceptance check „Every choice is acknowledged in the journal and has
at least one planned later callback“).

| Hook | Condition (slice save) | Planned response in Chapter 3 | Planned cost / tension |
|---|---|---|---|
| `C3_IRINA_WITNESS` | `irina_trust >= 1` | Irina testifies to the missing wagons and the C-17 stamp as a depot witness; her statement corroborates Alexei's ledger. More credible depot cooperation later — but no automatic „good“ ending. | Irina and the rail team risk being identified. |
| `C3_ALEXEI_SILENCE` | `alexei_secrecy >= 1` | Irina is guarded towards Alexei (she may refuse to cooperate after a breach of confidence); Alexei's motive appears unclear to the others. | Short-term protection, long-term accountability; delay in warning affected civilians. |
| `C3_KONRAD_COPY` | `konrad_evidence >= 1` | Konrad carries an independently preserved copy of the memo; together with the ledger it gives a strong documentary match between the two sites. | Possession of the copy is a security risk for Konrad and for Emil. |
| `C3_ARCHIVE_ALERTED` | `office_suspicion >= 1` | Konrad's official request has created a paper trail that links the sites through correspondence; the archive administration is alerted and watches him. | Scrutiny and obstruction; Emil's archive access is endangered. No direct game over. |
| `C3_EVIDENCE_BASE` | `c17_confirmed and blueprint_match_confirmed` (always true at slice end) | Both investigators hold their half of the C-17 contract series: freight ledger + timetable + seal (Alexei) and the two plan versions + Emil's note (Konrad). | — |
| `C4_C5_CIVILIANS` | `civilian_welfare` (reserved, 0 in the slice) | Concrete protection actions in Chapters 4–5 (housing district, displaced residents) raise this meter. | Protecting people versus speed of publication. |

Combination flavour for Chapter 3 (from §7.2): `irina_trust + konrad_evidence` → corroborated testimony **and** an
independent record; `irina_trust + office_suspicion` → witness plus paper trail under observation;
`alexei_secrecy + konrad_evidence` → documents match, trust between the sources is weak; `alexei_secrecy +
office_suspicion` → the official trail links the sites while Alexei's role stays unclear.

Implementation note for Chapter 3: read the meters with `Story.relationship(name)` (or `flag(name)`); add new flags to
`data/v3/flags.json` with defaults so the save migration keeps old slice saves valid. Do not add a combined „morality“
score.

### 7.4 Character arcs the consequences serve (from the consequence matrix)

* **Alexei Morozov:** duty to keep civilian rail transport running vs. silence about coercive diversion; learns that
  reporting to authority alone does not settle responsibility.
* **Konrad Adler:** moves from professional neutrality to acknowledging that drawings can facilitate removal and
  control — neither an unearned instant reformer nor an uncritical agent.
* **Irina Belova:** a full colleague with agency; may refuse cooperation after a breach of confidence.
* **Emil Hartmann:** imperfect archivist constrained by prior compromises; his help never absolves complicity.
* **Marta, Elena, Lev:** reserved for later chapters; no slice content is fabricated for them.

Narrative acceptance checks: no hero solves the transnational conspiracy alone — each finds **part** of the story; the
fictional Great Hall exists only in the alternate timeline and is framed critically; Nazi persecution and Soviet
repression are not used as interchangeable aesthetic motifs.

---

## 8. Cinematics

| Sequence | Trigger | Skip policy (data) | Shots | Engine semantics |
|---|---|---|---|---|
| `LS_A1_ToM1` | event `a1_completed` | `dispatch_next_scene_only_once` | s1 C-17 cargo stamp close-up (4 s), s2 match cut to the C-17 annotation on the Berlin blueprint (2 s), s3 wide of the archive, control to Konrad (3 s) | queued once; the scene already switched at the event |
| `LS_M1_Hall` | objective `m1_align_plans` | `visual_only` | h1 camera leaves the drawing through the archive window (3 s), h2 the Great Hall's distant silhouette with ordinary people in the foreground (5 s), h3 return to the workbench (3 s) | queued once; no state change |
| `LS_X1_Final` | event `m1_completed` | `mark_finale_complete_once` | x1 Alexei files the document (4 s), x2 Konrad folds the matching memorandum (4 s), x3 neutral-border schematic (4 s), x4 demo end (3 s) | queued once; the finale itself is `Story.finale()` |

`pending_cinematics()` lists unlocked, unseen sequences in data order; `consume_cinematic(id, skipped)` — played or
skipped — leads to the identical story state (tests: `test_branches.gd` skip/timing equivalence).

---

## 9. Save data

**Story payload** (`Story.save_json()`, byte-identical to the Python reference's `json.dumps(sort_keys, indent=2)`):
`format` = `ashes_of_empires_story_reference_v4`, `save_version` = 3, `flags`, `completed_objectives` (in order),
`completed_events`, `inventory`, `choice_history`, `current_scene`, `active_character`, `dialogue_progress`
(objective → node), `puzzle_attempts`, `cinematics_seen`, `finale_viewed`.

**Validation** (`Story.load_json` / `validate_save_json`, transactional, max 128 KiB): the objective history is
**replayed** through the real gates in a fresh engine; the save is rejected if any objective is unknown, duplicated,
out of order or in the wrong scene, a choice is missing/invalid or the choice history does not match, any flag, event,
item, scene or protagonist contradicts the replay (events and inventory may be in any order), a dialogue cursor is not
on an available dialogue or names an unknown node, a puzzle counter is not an int in 0–100000 for a puzzle objective,
cinematic ids are unknown/duplicated/not yet triggered, `finale_viewed` is not a bool or is true before the finale, the
version/format is unknown, or the text is not a JSON object. Unknown extra fields are ignored and reported as warnings.

**Migration**: v0.3 saves (`save_version` 2, see `tests/support/legacy_runtime_v2.gd`) are replayed the same way;
missing flags take their defaults; presentation state starts empty (all triggered cinematics are pending again,
`finale_viewed` follows a recorded `slice_completed`). Saves still carrying the pre-rename protagonist id are rejected
as inconsistent.

**Slots** (`Saves`): `1`, `2`, `3`, `auto`, `quick` → `user://saves/<slot>.json` containing `meta` (`version` 1,
`timestamp`, `chapter_key`, `character`, `scene`, `playtime_s`, `label`), `story` (payload above) and `extra`
(presentation data from `Game.save_extra()`). Writes go to `<slot>.json.tmp`, are verified, the previous file is kept
as `<slot>.json.bak`, then the tmp replaces the slot. Loading validates completely before the live state changes.

---

## 10. Verification

`"$LOCALAPPDATA/Programs/Godot/Godot_v4.7.2-stable_win64_console.exe" --headless --path C:/Spiele/AshesOfEmpires --script res://tests/run_all.gd`

| Test file | Covers |
|---|---|
| `test_story_engine_v4.gd`, `test_data_and_runtime.gd`, `test_integrity_v4.gd` | 1:1 ports of the 34 Python tests in `preproduction/tests/` |
| `test_reference_parity.gd` | routes, legacy saves, API traces and ~3 100 mutated saves replayed against fixture output of the Python reference (`tests/reference/make_python_reference.py`) |
| `test_branches.gd`, `test_signals.gd`, `test_journal.gd`, `test_engine_api.gd` | four branches, skip/timing equivalence, gating identity, signal stream, once-only effects, journal, API robustness, seeded fuzzing |
| `test_saves.gd` | slots, atomic write, `.bak`, corrupt/tampered/oversized files, legacy payloads |
| `test_loc.gd`, `test_rename_guard.gd`, `test_quest_database.gd`, `test_json_compat.gd` | German strings, the Konrad rename, this document, the JSON layer |
