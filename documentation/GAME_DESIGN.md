# GAME DESIGN — ASHES OF EMPIRES: THE LAST WINTER

Status: AUTHORED 2026-11-04. Platform Windows PC, Godot 4.7.2. Genre: cinematic narrative adventure with
investigation, exploration, light RPG state, puzzles and choices. No combat.

## Pillars
1. Exceptional pixel-art atmosphere. 2. Two distinct protagonists. 3. Believable alternative 1964.
4. Strong pacing. 5. Consequential, non-moralised choices. 6. Seamless cinematic presentation.
7. One coherent art language across 2D / 2.5D / 3D. 8. Reliability (no softlocks, safe saves).

## Core loop
Explore a dense authored location → talk and inspect → collect evidence → solve a grounded puzzle / repair →
decide → see persistent consequences → authored cinematic switch to the other protagonist.

## Presentation modes (shared 640×360 pixel world, see TECHNICAL_ARCHITECTURE §2)
* **A — side-on 2D:** interiors, trains, intimate scenes (Konrad's archive).
* **B — oblique 2.5D:** streets, yards, districts; free x/y movement with y-sorting (Karsk yard).
* **C — 3D pixel render:** monumental reveals and controlled camera moves (Great Hall).

## Controls (rebindable, keyboard/mouse/controller)
Move WASD/arrows/left stick · Run Shift/LB · Interact E/Space/Enter/A · Journal J/Tab/Back · Pause Esc/Start ·
Advance dialogue Space/Enter/E/click · Skip cinematic Esc/Y (skip never skips story state).

## Systems
| System | Implementation | Slice status |
|---|---|---|
| Player | `scripts/actors/player.gd` (oblique/side, 60 px/s walk, 120 run) | implemented |
| Interaction | `interactable.gd` — Story decides availability; locked = no prompt | implemented |
| Story / quests / flags / inventory / choices | `Story` autoload (port of the verified v4 reference engine) | in production |
| Dialogue | data/v3 dialogue + `DialogueBox` with portraits, history | in production |
| Investigation | Inspect view with document art + HD text; journal (goals, evidence, people, decisions) | in production |
| Puzzles | Signal teaching board (symbol order, hints, no penalty); blueprint overlay (grid, rotation, snap) | in production |
| Reconstruction | Signal power restored (slice); repair/route mechanics from Ch1 full chapter on | planned |
| NPCs | idle/wander/talk routines, story NPCs face the player | implemented (basic) |
| World | snow, fog, flicker lights, ambience per scene; day/night per chapter | partial |
| Save | 3 slots + auto + quick, atomic, validated, migration | in production |
| Cinematics | director in `game.gd`: match cut A1→M1, Great Hall 3D reveal, X1 montage; all skip-safe | implemented (needs art) |
| UI | main/pause/settings/save-load/journal/dialogue/inspect/puzzles/credits/subtitles | in production |
| Audio | synthesised ambience, music, SFX; buses | in production |

## Choices (slice)
* A1: share the discrepancy with Irina (`irina_trust+1`) **or** keep it private (`alexei_secrecy+1`).
* M1: keep a private copy (`konrad_evidence+1`) **or** demand an official statement (`office_suspicion+1`).
Four combinations, each acknowledged in the journal and the end card, each with planned Chapter-3 callbacks
(see QUEST_DATABASE.md and preproduction CHOICE_CONSEQUENCE_MATRIX_V4).

## Accessibility
Text scale 100/125/150 %, subtitles default on, dialogue speed, high contrast, reduced motion (camera, flicker),
pixel post-effect intensity, puzzle hint level, full rebinding, colour-independent puzzle markers, no flashing.

## Scope plan
Vertical slice first (20–30 min, both protagonists, transition, two investigations, two choices, save/load,
audio). Then chapters in order 1 → 6 using the same pipelines (pixelgen environments, character rig, Story data).
