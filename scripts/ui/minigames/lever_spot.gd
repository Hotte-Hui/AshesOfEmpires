extends "res://scripts/ui/minigames/kartei_spot.gd"
## Exploration spot of the Chapter-4 levels (scenes/levels/L_C4_Tunnels.tscn: Story scenes A + C, L_C4_Annex.tscn:
## B + D; documentation/C4_DESIGN.md §4/§6) -- every C4 find, chat and side-task step uses it, the mini-game "Der
## Hebelrahmen" at exp_lever_frame included. The gates are those of kartei_spot.gd: the objective gates
## (after_objective / until_objective) in the running game, the remembered scene (`memory_scenes`) inside a memory.
## Added here: a chat on an NPC's spot (`npc_id`) is only offered while that NPC stands in the level, so nobody talks
## to an empty chair. Inside a memory the Story NPCs follow the remembered scene (StoryNPC reads the level's gated-art
## rule: objectives of earlier scenes count, its own and later ones not), so Lev is at his desk in every memory of the
## cellar and at the siding in the siding's — npc_present() asks the NPC and agrees with it. Never touches Story.

## How far the NPC may stand from the spot to count as the one this chat belongs to (world px).
const NPC_REACH := 60.0


func is_active() -> bool:
	if not super.is_active():
		return false
	if kind == "chat" and npc_id != "":
		return npc_present()
	return true


## True unless an NPC with this chat's npc_id stands at the spot and is absent (StoryNPC.is_present() false).
## Without such a node (tests, harness) the chat is not blocked.
func npc_present() -> bool:
	var p := get_parent()
	if p == null:
		return true
	var near := false
	for n in p.get_children():
		if n == self or not (n is Node2D) or str(n.get("char_id")) != npc_id:
			continue
		if (n as Node2D).position.distance_to(position) > NPC_REACH:
			continue
		near = true
		if not n.has_method("is_present") or bool(n.is_present()):
			return true
	return not near
