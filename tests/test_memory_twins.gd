extends RefCounted
## Memory twins (TECHNICAL_ARCHITECTURE §12.10/§12.11, Game._spawn_memory_hotspots): inside a memory every story
## hotspot of the remembered scene gets exactly one read-only twin, and a conversation and the decision taken with the
## same person in the same Story scene share one twin. A level file shared by several Story scenes (L_C3_Registry: A–D,
## L_C4_Tunnels: A + C, L_C4_Annex: B + D) remembers only the objectives of the scene the memory is of:
##  * the cellar memory (L_C4_TunnelsA) has Lev's twin at his desk (inside the cellar's walk area) with the two cellar
##    talks and nothing of the siding; the siding memory (L_C4_TunnelsB) replays only the siding talk
##  * no twin of a shared level mixes objectives of two scenes or shows another scene's objective, and every story
##    hotspot of the remembered scene is replayed by exactly one twin
##  * a level of one scene keeps a twin for every story hotspot, conversations still merge with their decision
## The levels are mounted the way Game._load_level does (Game._adopt_scene) and the real Game._spawn_memory_hotspots()
## runs on them. Writes nothing: Game.level / memory_mode / memory_scene are restored, the levels are freed.

const Kit := preload("res://tests/support/test_kit.gd")
const Memories := preload("res://scripts/core/memories.gd")
const SINGLE := ["L_A1_Railyard", "L_C3_Station"]

var kit


func run() -> Array:
	kit = Kit.new()
	var game: Node = Kit.root().get_node_or_null("Game")
	var st: Node = Kit.root().get_node_or_null("Story")
	if game == null or st == null or not game.has_method("_spawn_memory_hotspots"):
		print("      note: autoloads missing, memory twin checks skipped")
		return kit.failures
	kit.run_case("c4_tunnels_lev_twin_per_scene", _tunnels.bind(game, st))
	kit.run_case("shared_levels_never_mix_scenes", _shared.bind(game, st))
	kit.run_case("single_scene_levels_keep_every_twin", _single.bind(game, st))
	kit.cleanup()
	return kit.failures


## Mounts the level file of Story scene `sid` like Game._load_level (memory mode, Game._adopt_scene), spawns the twins
## with the real Game._spawn_memory_hotspots() and returns {"twins": [{name, npc, oids, kind, pos}],
## "story": [{oid, kind, npc, scene}] (the level's story hotspots), "hotspots": {id: Vector2}}.
func _memory_of(game: Node, st: Node, sid: String, hotspot_ids: Array = []) -> Dictionary:
	var out := {"twins": [], "story": [], "hotspots": {}}
	var path: String = game.level_file(sid)
	if not kit.ok(path != "" and ResourceLoader.exists(path), "%s: a level file (%s)" % [sid, path]):
		return out
	var keep := {"level": game.level, "mm": game.memory_mode, "ms": game.memory_scene}
	game.memory_mode = true
	game.memory_scene = sid
	var lvl: Node = (load(path) as PackedScene).instantiate()
	game._adopt_scene(lvl, sid)
	lvl.set("ambience", "")
	lvl.set("music", "")
	Kit.root().add_child(lvl)
	game.level = lvl
	game._spawn_memory_hotspots()
	for tw in game.memory_twins():
		out["twins"].append({"name": str(tw.name), "npc": str(tw.get("npc_id")), "kind": str(tw.get_meta("memory_kind", "")),
			"oids": Array(tw.get_meta("memory_objectives")).duplicate(), "pos": (tw as Node2D).position})
	for it in Kit.tree().get_nodes_in_group("interactables"):
		if not is_instance_valid(it) or not lvl.is_ancestor_of(it) or it.has_meta("memory_objectives"):
			continue
		var oid := str(it.get("objective_id"))
		if oid != "" and str(it.get("kind")) in Memories.STORY_KINDS:
			out["story"].append({"oid": oid, "kind": str(it.get("kind")), "npc": str(it.get("npc_id")),
				"scene": str(st.quest_for(oid).get("scene", ""))})
	for h in hotspot_ids:
		out["hotspots"][h] = lvl.get_hotspot(str(h))
	game.level = keep["level"]
	game.memory_mode = keep["mm"]
	game.memory_scene = keep["ms"]
	lvl.get_parent().remove_child(lvl)
	lvl.free()
	return out


func _twin_with(twins: Array, oid: String) -> Dictionary:
	for t in twins:
		if (t["oids"] as Array).has(oid):
			return t
	return {}


## The contract every memory keeps: each replayed story hotspot of `sid` (all of them when `own_only` is false) is
## carried by exactly one twin, no twin carries anything else, and the dialogue / choice objectives of one person in
## one scene share a single twin.
func _contract(sid: String, m: Dictionary, own_only: bool) -> void:
	var expected := {}
	var by_npc := {}
	for s in m["story"]:
		if own_only and str(s["scene"]) != sid:
			continue
		expected[str(s["oid"])] = true
		if str(s["npc"]) != "" and str(s["kind"]) in ["dialogue", "choice"]:
			var key := "%s@%s" % [s["npc"], s["scene"]]
			if not by_npc.has(key):
				by_npc[key] = []
			by_npc[key].append(str(s["oid"]))
	var seen := {}
	for t in m["twins"]:
		var scenes := {}
		for oid in t["oids"]:
			seen[str(oid)] = int(seen.get(str(oid), 0)) + 1
			kit.ok(expected.has(str(oid)), "%s: twin %s replays %s, which is not a story hotspot of this memory" % [sid, t["name"], oid])
			for s in m["story"]:
				if str(s["oid"]) == str(oid):
					scenes[str(s["scene"])] = true
		kit.ok(scenes.size() <= 1, "%s: twin %s mixes the scenes %s (%s)" % [sid, t["name"], Kit.sorted(scenes), t["oids"]])
	for oid in expected:
		kit.eq(int(seen.get(oid, 0)), 1, "%s: %s is replayed by exactly one twin" % [sid, oid])
	for key in by_npc:
		var t := _twin_with(m["twins"], str(by_npc[key][0]))
		kit.eq(Kit.sorted(t.get("oids", [])), Kit.sorted(by_npc[key]), "%s: one twin for the talks with %s" % [sid, key])


func _tunnels(game: Node, st: Node) -> bool:
	kit.ok(game.is_switch_scene("L_C4_TunnelsA") and game.is_switch_scene("L_C4_TunnelsB"),
		"the cellar and the siding share L_C4_Tunnels (§12.11)")
	# the cellar memory: camera zone 0–720, the cellar door shut -- Lev's twin must stand at his desk
	var a := _memory_of(game, st, "L_C4_TunnelsA", ["lev_cellar"])
	kit.ok(not (a["twins"] as Array).is_empty(), "the cellar memory has twins")
	var lev_a := _twin_with(a["twins"], "c4a_talk_lev")
	kit.eq(Kit.sorted(lev_a.get("oids", [])), ["c4a_talk_lev", "c4a_talk_tunnel"], "cellar memory: Lev's twin replays the two cellar talks")
	kit.eq(str(lev_a.get("kind", "")), "dialogue", "cellar memory: Lev's twin is a conversation")
	var pa: Vector2 = lev_a.get("pos", Vector2(-9999, 0))
	kit.ok(pa.x < 700.0, "cellar memory: Lev's twin stands inside the cellar's walk area (x %.0f < 700)" % pa.x)
	kit.ok(pa.distance_to(a["hotspots"]["lev_cellar"]) <= 40.0, "cellar memory: Lev's twin at his desk (lev_cellar %s, twin %s)" % [a["hotspots"]["lev_cellar"], pa])
	for t in a["twins"]:
		for oid in t["oids"]:
			kit.ok(not str(oid).begins_with("c4c_"), "cellar memory: twin %s replays the siding objective %s" % [t["name"], oid])
	_contract("L_C4_TunnelsA", a, true)
	# the siding memory: only the siding talk, at the siding
	var b := _memory_of(game, st, "L_C4_TunnelsB", ["lev_siding"])
	var lev_b := _twin_with(b["twins"], "c4c_talk_lev")
	kit.eq(lev_b.get("oids", []), ["c4c_talk_lev"], "siding memory: Lev's twin replays only the siding talk")
	kit.ok((lev_b.get("pos", Vector2(-9999, 0)) as Vector2).distance_to(b["hotspots"]["lev_siding"]) <= 40.0,
		"siding memory: Lev's twin at the siding")
	for t in b["twins"]:
		for oid in t["oids"]:
			kit.ok(not str(oid).begins_with("c4a_"), "siding memory: twin %s replays the cellar objective %s" % [t["name"], oid])
	_contract("L_C4_TunnelsB", b, true)
	# the replay of the siding twin holds the siding conversation only (none of the 17 cellar lines before it)
	var ctx := {"protagonist": "alexei", "choices": {}, "flags": {}, "ext": game.ext, "reactions": game.REACTIONS,
		"line_expr": game.LINE_EXPR}
	kit.eq(game.memories.echo_plan(lev_b.get("oids", []), ctx).size(), game.memories.echo_plan(["c4c_talk_lev"], ctx).size(),
		"siding memory: the Lev replay is the siding talk alone")
	kit.ok(game.memories.echo_plan(["c4c_talk_lev"], ctx).size() > 0, "the siding talk has lines to replay")
	return true


func _shared(game: Node, st: Node) -> bool:
	var seen := {}
	for sid in Kit.CHAIN:
		if str(sid) == "L_C4_TunnelsA" or str(sid) == "L_C4_TunnelsB" or not game.is_switch_scene(str(sid)):
			continue   # the tunnels have their own case
		var m := _memory_of(game, st, str(sid))
		seen[str(sid)] = m
		kit.ok(not (m["twins"] as Array).is_empty(), "%s: the memory has twins" % sid)
		_contract(str(sid), m, true)
	for sid in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD", "L_C4_AnnexA", "L_C4_AnnexB"]:
		kit.ok(seen.has(sid), "%s plays in a shared level file (§12.11)" % sid)
	# the registry merges that went across scenes before: Konrad at the card files (A) vs. in the smoke (C), Alexei
	# at the sorting table (B) vs. at the desk and the chute (D)
	var expect := {"L_C3_RegistryA": ["c3c_talk_konrad"], "L_C3_RegistryC": ["c3e_reach_konrad"],
		"L_C3_RegistryB": ["c3d_choose", "c3d_talk_compare", "c3d_talk_partner"], "L_C3_RegistryD": ["c3f_climb", "c3f_push_desk"]}
	for sid in expect:
		var t := _twin_with(seen.get(sid, {}).get("twins", []), str(expect[sid][0]))
		kit.eq(Kit.sorted(t.get("oids", [])), expect[sid], "%s: the conversation twin replays this scene only" % sid)
	return true


func _single(game: Node, st: Node) -> bool:
	var station := {}
	for sid in SINGLE:
		kit.ok(not game.is_switch_scene(str(sid)), "%s plays alone in its level file" % sid)
		var m := _memory_of(game, st, str(sid))
		kit.ok(not (m["twins"] as Array).is_empty(), "%s: the memory has twins" % sid)
		_contract(str(sid), m, false)
		if str(sid) == "L_C3_Station":
			station = m
	# the station: the decision taken with a person is part of that person's conversation twin
	var merged := false
	for t in station.get("twins", []):
		var kinds := {}
		for s in station["story"]:
			if (t["oids"] as Array).has(s["oid"]):
				kinds[str(s["kind"])] = true
		merged = merged or (kinds.has("dialogue") and kinds.has("choice"))
	kit.ok(merged, "L_C3_Station: a conversation and the decision taken there share one twin")
	return true
