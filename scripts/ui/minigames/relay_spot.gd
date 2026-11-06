extends "res://scripts/actors/gated_interactable.gd"
## Hotspot of the relay desk in the interpreters' corridor of the Palais (L_C3_Hall, exp_relay_desk; explore entry
## veltrava.hall.relay, mini-game scenes/ui/minigames/RelayDesk.tscn). The desk can only be taken over while the
## session runs: after Konrad has reported to Kessler (after_objective c3b_arrival) and until he finds booth 2 empty
## (until_objective c3b_inspect_booth) -- afterwards the session is over and the story belongs to the meeting at
## booth 3. Inside a memory of the palais (TECHNICAL_ARCHITECTURE §12.10, Game.memory_mode; the Story state there is
## the completed one) the session can be remembered once more, so the until-gate does not apply. Never touches Story.


func is_active() -> bool:
	var g := get_node_or_null("/root/Game")
	var mm = g.get("memory_mode") if g != null else null
	if mm is bool and mm:
		return kind == "discover" and explore_id != "" and not (once and used)
	return super.is_active()
