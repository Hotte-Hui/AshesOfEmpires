extends RefCounted
## Story NPCs inside a memory (TECHNICAL_ARCHITECTURE §12.10/§12.11, scripts/actors/story_npc.gd show_after /
## hide_after). In a level file shared by several Story scenes the NPCs read the rule of the level's gated art
## (scripts/levels/c3p2_archive/registry_level.gd objective_done): inside the memory of scene X only objectives of
## scenes BEFORE X count, X's own and later ones do not — whatever the live Story has done since:
##  * the cellar memory (L_C4_TunnelsA) has Lev at his desk after the whole chapter (his hide_after c4c_inspect_card
##    belongs to the later siding scene); his siding post stays empty
##  * the siding memory (L_C4_TunnelsB) has Lev at the siding (show_after c4a_open_door: the cellar came before)
##  * a new game and a finished Chapter 4 give the same cast in every memory of a shared level file
##  * every conversation twin (Game._spawn_memory_hotspots) and every chat spot of the remembered scene
##    (lever_spot.npc_present) meets its NPC there
##  * live play is unchanged (the live Story decides, also when an objective completes while the level is loaded)
##  * the registry's memories keep their cast (no authored Story NPC, Game's stand-in for the partner) and looks
##  * a level of one Story scene keeps the live Story (Elena at the café, Alexei in the hall: their talks' twins)
## The levels are mounted the way Game._load_level does (Game._adopt_scene, memory mode set before the level enters
## the tree), as in tests/test_memory_twins.gd. Restores Story and Game.level / memory_mode / memory_scene.

const Kit := preload("res://tests/support/test_kit.gd")
const LeverSpot := preload("res://scripts/ui/minigames/lever_spot.gd")
const SHARED_C4 := ["L_C4_TunnelsA", "L_C4_AnnexA", "L_C4_TunnelsB", "L_C4_AnnexB"]
const REGISTRY := {"L_C3_RegistryA": "a", "L_C3_RegistryB": "b", "L_C3_RegistryC": "c", "L_C3_RegistryD": "d"}

var kit
var game: Node
var st: Node
var _keep := {}


func run() -> Array:
	kit = Kit.new()
	game = Kit.root().get_node_or_null("Game")
	st = Kit.root().get_node_or_null("Story")
	if game == null or st == null or not game.has_method("_spawn_memory_hotspots"):
		print("      note: autoloads missing, memory NPC checks skipped")
		return kit.failures
	_keep = {"story": st.save_json(), "level": game.level, "mm": game.memory_mode, "ms": game.memory_scene}
	kit.run_case("c4_tunnels_lev_stands_in_the_remembered_scene", _tunnels)
	kit.run_case("shared_memories_ignore_the_live_story", _ignore_live)
	kit.run_case("twins_and_chats_meet_their_npc", _twins_meet_npcs)
	kit.run_case("live_play_follows_the_story", _live)
	kit.run_case("registry_memories_keep_their_cast", _registry)
	kit.run_case("single_scene_levels_keep_the_live_story", _single)
	_restore()
	kit.cleanup()
	return kit.failures


func _restore() -> void:
	game.level = _keep["level"]
	game.memory_mode = _keep["mm"]
	game.memory_scene = _keep["ms"]
	if not st.load_json(str(_keep["story"])).get("ok", false):
		st.new_game()


## The live Story at the end of `stage` ("" = a new game).
func _story_at(stage: String) -> void:
	st.new_game()
	if stage != "":
		kit.play_until(st, stage)


## Mounts the level file of Story scene `sid` like Game._load_level (memory mode and scene set first, so the NPCs
## see them in their _ready; Game._adopt_scene; Game.level). Unmount with _unmount().
func _mount(sid: String, memory: bool) -> Node:
	var path: String = game.level_file(sid)
	if not kit.ok(path != "" and ResourceLoader.exists(path), "%s: a level file (%s)" % [sid, path]):
		return null
	game.memory_mode = memory
	game.memory_scene = sid if memory else ""
	var lvl: Node = (load(path) as PackedScene).instantiate()
	game._adopt_scene(lvl, sid)
	lvl.set("ambience", "")
	lvl.set("music", "")
	Kit.root().add_child(lvl)
	game.level = lvl
	return lvl


func _unmount(lvl: Node) -> void:
	game.level = _keep["level"]
	game.memory_mode = _keep["mm"]
	game.memory_scene = _keep["ms"]
	if lvl != null and is_instance_valid(lvl):
		lvl.get_parent().remove_child(lvl)
		lvl.free()


static func _here(n: Node) -> bool:
	return n != null and bool(n.is_present()) and (n as CanvasItem).visible and n.is_in_group("npcs")


## {node name: present} of every StoryNPC of the level.
func _cast(lvl: Node) -> Dictionary:
	var out := {}
	for n in lvl.find_children("*", "", true, false):
		if n.has_method("is_present") and n.has_method("set_suppressed"):
			out[str(n.name)] = _here(n)
	return out


func _npc(lvl: Node, node_name: String) -> Node:
	return lvl.get_node_or_null("Playfield/" + node_name)


## The cast of the memory of `sid` under the present live Story.
func _memory_cast(sid: String) -> Dictionary:
	var lvl := _mount(sid, true)
	var c := _cast(lvl) if lvl != null else {}
	_unmount(lvl)
	return c


# ------------------------------------------------------------------ cases
func _tunnels() -> bool:
	_story_at("c4d")      # the reported case: the whole chapter is played, then the cellar is remembered
	var a := _mount("L_C4_TunnelsA", true)
	if a != null:
		var lev := _npc(a, "LevCellar")
		kit.ok(lev != null and str(lev.get("hide_after")) == "c4c_inspect_card", "LevCellar leaves after c4c_inspect_card (live)")
		kit.eq(str(st.objective_state("c4c_inspect_card")), "complete", "the live Story has the card inspected")
		kit.ok(_here(lev), "cellar memory after Chapter 4: Lev stands at his desk")
		kit.ok(not _here(_npc(a, "LevSiding")), "cellar memory: his siding post is empty (c4a_open_door is the cellar's own)")
		var lc: Vector2 = (lev as Node2D).position if lev != null else Vector2.ZERO
		kit.ok(lc.distance_to(a.get_hotspot("lev_cellar")) <= 40.0, "cellar memory: Lev at lev_cellar (%s)" % lc)
	_unmount(a)
	var b := _mount("L_C4_TunnelsB", true)
	if b != null:
		var lev_b := _npc(b, "LevSiding")
		kit.ok(_here(lev_b), "siding memory: Lev stands at the siding (the cellar's c4a_open_door came before)")
		var ls: Vector2 = (lev_b as Node2D).position if lev_b != null else Vector2.ZERO
		kit.ok(ls.distance_to(b.get_hotspot("lev_siding")) <= 40.0, "siding memory: Lev at lev_siding (%s)" % ls)
		kit.ok(ls.x > 720.0, "siding memory: Lev in the siding's walk area (x %.0f > 720)" % ls.x)
	_unmount(b)
	return true


func _ignore_live() -> bool:
	_story_at("")
	var fresh := {}
	for sid in SHARED_C4 + REGISTRY.keys():
		fresh[sid] = _memory_cast(str(sid))
	_story_at("c4d")
	for sid in SHARED_C4 + REGISTRY.keys():
		kit.eq(_memory_cast(str(sid)), fresh[sid], "%s: the same cast after a new game and after Chapter 4" % sid)
	kit.eq(fresh.get("L_C4_TunnelsA", {}), {"LevCellar": true, "LevSiding": false}, "cellar memory cast")
	kit.eq(fresh.get("L_C4_TunnelsB", {}), {"LevCellar": true, "LevSiding": true},
		"siding memory cast (the cellar's Lev stands behind the shut door wall, off its walk area)")
	kit.eq(fresh.get("L_C4_AnnexA", {}), {"MartaTram": true, "Registrar": true, "GuardAnnex": true}, "tram loop memory cast")
	kit.eq(fresh.get("L_C4_AnnexB", {}), {"MartaTram": true, "Registrar": true, "GuardAnnex": true}, "annex memory cast")
	return true


## Every twin that replays a conversation stands within reach of a present NPC of that speaker; every chat spot of
## the remembered scene with an NPC finds him there (lever_spot.npc_present).
func _meet(sid: String, lvl: Node) -> void:
	game._spawn_memory_hotspots()
	var twins: Array = game.memory_twins()
	kit.ok(not twins.is_empty(), "%s: the memory has twins" % sid)
	for tw in twins:
		var who := str(tw.get("npc_id"))
		if who == "":
			continue
		var best := INF
		for n in Kit.tree().get_nodes_in_group("npcs"):
			if lvl.is_ancestor_of(n) and str(n.get("char_id")) == who and (n as CanvasItem).is_visible_in_tree():
				best = minf(best, (n as Node2D).global_position.distance_to((tw as Node2D).global_position))
		kit.ok(best <= LeverSpot.NPC_REACH, "%s: twin %s (%s) meets %s (nearest present: %s px)" % [sid, tw.name,
			tw.get_meta("memory_objectives"), who, "none" if best == INF else str(int(best))])
	for n in lvl.find_children("*", "", true, false):
		if not n.has_method("npc_present") or str(n.get("npc_id")) == "" or str(n.get("kind")) != "chat":
			continue
		var ms: PackedStringArray = n.get("memory_scenes")
		if not ms.is_empty() and not (sid in ms):
			continue
		kit.ok(bool(n.npc_present()), "%s: chat %s finds %s at the spot" % [sid, n.name, n.get("npc_id")])


func _twins_meet_npcs() -> bool:
	_story_at("c4d")
	for sid in SHARED_C4:
		var lvl := _mount(str(sid), true)
		if lvl != null:
			_meet(str(sid), lvl)
		_unmount(lvl)
	return true


func _live() -> bool:
	_story_at("")
	var a := _mount("L_C4_TunnelsA", false)
	if a != null:
		kit.eq(_cast(a), {"LevCellar": true, "LevSiding": false}, "new game, cellar: Lev at his desk, not yet at the siding")
	_unmount(a)
	_story_at("c4b")      # the cellar and the tram loop played; the siding starts
	var b := _mount("L_C4_TunnelsB", false)
	if b != null:
		kit.eq(_cast(b), {"LevCellar": true, "LevSiding": true}, "siding starts: Lev at the siding (the cellar's Lev not yet gone)")
		kit.step(st.inspect("c4c_inspect_card"), "inspect the card")
		kit.eq(_cast(b), {"LevCellar": false, "LevSiding": true}, "card inspected: the cellar's Lev leaves at once (live)")
	_unmount(b)
	_story_at("c4d")
	var b2 := _mount("L_C4_TunnelsB", false)
	if b2 != null:
		kit.eq(_cast(b2), {"LevCellar": false, "LevSiding": true}, "a load after the chapter: the live Story decides")
	_unmount(b2)
	return true


func _registry() -> bool:
	for stage in ["", "c4d"]:
		_story_at(stage)
		for sid in REGISTRY:
			var lvl := _mount(str(sid), true)
			if lvl == null:
				continue
			kit.eq(_cast(lvl), {}, "%s: no authored Story NPC in the registry" % sid)
			kit.eq(str(lvl.call("look")), str(REGISTRY[sid]), "%s memory (%s): look %s" % [sid, stage if stage != "" else "new game", REGISTRY[sid]])
			var who: String = game.scene_partner(str(sid))
			var sw: Dictionary = game.ext.switch_settings(str(sid))
			if kit.ok(who != "" and game._has_spawn(str(sw.get("partner_spawn", ""))),
					"%s: a partner (%s) with a spot" % [sid, who]):
				var si: Node = game._make_stand_in(who, lvl.call("get_spawn", str(sw["partner_spawn"])), sw)
				kit.ok(_here(si), "%s memory: Game's stand-in %s is there" % [sid, who])
			_unmount(lvl)
	return true


func _single() -> bool:
	_story_at("c4d")
	var want := {"L_C3_Station": {"ElenaControl": false, "ElenaCafe": true}, "L_C3_Hall": {"ElenaArrival": false, "Alexei": true}}
	for sid in want:
		kit.ok(not game.is_switch_scene(str(sid)), "%s plays alone in its level file" % sid)
		var lvl := _mount(str(sid), true)
		if lvl == null:
			continue
		var c := _cast(lvl)
		for nm in want[sid]:
			kit.eq(c.get(nm), want[sid][nm], "%s memory: %s %s (the live Story: who stood there at the scene's end)" % [sid, nm, "there" if want[sid][nm] else "gone"])
		_meet(str(sid), lvl)
		_unmount(lvl)
	return true
