# Vertical slice — playable screenplay / quest script draft

## Scene A1 — The Last Signal (Alexei, 8–10 min)
**View:** oblique 2.5D, rain-damp rail yard, dark green-gray palette, amber windows.
**Objective:** speak to dispatcher Irina; restore a switch-box circuit via a simple non-timed routing puzzle; inspect a cargo ledger.

IRINA: "The trains still arrive. The numbers on their papers don't."
ALEXEI: "Which numbers?"
IRINA: "Carriages, cargo, destinations. Pick one."

Player inspects three physical clues: a damaged seal, a revised ledger, and a timetable. One contains the routing code C-17.

ALEXEI: "C-17 doesn't exist on our network."
IRINA: "Then why did three wagons leave for it yesterday?"

**Choice:** Tell Irina everything / Keep the discrepancy private.
**State:** `irina_trust` +1 or `alexei_secrecy` +1.
**End:** camera frames the C-17 stamp; ambient train whistle becomes Berlin tram bell.

## Scene M1 — The Wrong Blueprint (Matthias, 8–10 min)
**View:** side-on 2D office corridor, transition to pixel-rendered 3D hall approach.
**Objective:** inspect two floorplans; compare mismatched annotations; speak with archivist Emil.

EMIL: "There are drawings we build from, and drawings we file."
MATTHIAS: "Those should be the same drawings."
EMIL: "Then you've never worked in this office."

Player aligns two blueprint overlays. A hidden service passage and the same code C-17 become visible.

**Choice:** Photograph the annotation / Request an official explanation.
**State:** `matthias_evidence` +1 or `office_suspicion` +1.
**End:** camera rises to reveal the Great Hall's overwhelming scale, then returns to an ordinary resident's shuttered apartment.

## Scene X1 — Two Trains, One Record (3–5 min)
**View:** cinematic split-location montage, not simultaneous character control.
An announcer reads the same diplomatic declaration in different languages. Alexei and Matthias independently fold documents with identical stamps. The scene ends on a neutral-border rail map.

**Slice finish:** title card, save checkpoint, main menu. This is a complete short demo ending, not an abrupt crash or unfinished level.

## Functional acceptance criteria
- Both characters can move and interact.
- Both investigations can be completed without developer commands.
- One player choice per character persists after save/reload.
- Camera transitions and scene switch work without visual discontinuity.
- No placeholder UI is mistaken for final UI.
