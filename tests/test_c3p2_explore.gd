extends RefCounted
## Chapter 3 part 2 exploration (documentation/C3P2_DESIGN.md §7, TECHNICAL_ARCHITECTURE §12.1/§12.3/§12.8/§12.9;
## owner: exploration c3p2): the finds and chats of the registry (one level file for the Story scenes
## L_C3_RegistryA–D, entries under the level key L_C3_RegistryA) and the quay, the side task „Die Pforte“, the two
## real-history cards and the mini-game „Die Suchkartei“ (scenes/ui/minigames/Kartei.tscn).
##  * data: files, ids, kinds, levels, texts (German style, lengths), chats (speakers, expressions), cards (sources,
##    450–800 characters, unlocked where §7 places them), Explore validation of the real data
##  * placement: every entry placed exactly once by a node of its level, hotspots resolve (scene.json + the env's
##    explore_hotspots.json), walk area, spacing to story spots / partner spots / other finds, the gates (Alexei
##    until c3c_talk_konrad, Konrad after c3c_talk_konrad until c3d_choose, memory scenes), chains start right
##  * the side task: order enforced by requires, the drivers' loop of scene A completes it in step order, states
##  * the mini-game: rule (gaps, refusals, every floor order solvable), scene auto mode, keys, hints, cancel,
##    full solve by keys only, compact layout for larger text, art/layout/sounds, the world cue
## Writes nothing: Explore / Settings / Game values touched here are restored before the case ends.

const Kit := preload("res://tests/support/test_kit.gd")
const Logic := preload("res://scripts/ui/minigames/kartei_logic.gd")
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const EXPLORE := "res://scripts/core/explore.gd"
const SCENE := "res://scenes/ui/minigames/Kartei.tscn"
const GAME := "res://scripts/ui/minigames/kartei_game.gd"
const SPOT := "res://scripts/ui/minigames/kartei_spot.gd"
const ART := "res://assets/ui/minigames/kartei/"
const LOCALE := "res://data/locale/de_explore_c3p2.json"
const HISTORY_LOCALE := "res://data/locale/de_history_c3p2.json"
const FILES := ["c3p2_registry.json", "c3p2_quay.json", "c3p2_history_reich.json", "c3p2_history_soviet.json"]
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
const LEVELS := {
	"L_C3_RegistryA": {"path": "res://scenes/levels/L_C3_Registry.tscn", "env": "veltrava_registry", "prefix": "veltrava.registry.",
		"story": ["crates", "ramp_door", "alexei_chute", "chute_door", "intake_desk", "fire_case", "porter_booth",
			"konrad_booth", "konrad_cards", "alexei_table", "sorting_table", "drawer_c17", "plan_wall"], "min": 16},
	"L_C3_Quay": {"path": "res://scenes/levels/L_C3_Quay.tscn", "env": "veltrava_quay", "prefix": "veltrava.quay.",
		"story": ["bench", "konrad_quay"], "npcs": ["typist_quay", "guard_quay", "kessler_quay", "voronova_quay",
			"journalist_quay"], "min": 8},
}
const GAP_STORY := 24.0
const GAP_FIND := 14.0
const HISTORY_AT := {"hist.soviet.filtration": "veltrava.registry.card_alexei", "hist.reich.census_1939": "veltrava.registry.card_konrad"}
const TASK := "veltrava.task.porter"
const TASK_STEPS := ["veltrava.registry.thermos", "veltrava.registry.radio", "veltrava.registry.keys", "veltrava.registry.porter_note"]
const SFX := ["mg_c3p2_card_take", "mg_c3p2_card_file", "mg_c3p2_rattle", "mg_c3p2_drawer_shut"]

var kit: Kit
var loc: Node
var real: Node                     # a private Explore instance with the real data
var data: Dictionary = {}          # file -> parsed
var entries: Dictionary = {}       # id -> entry (my files)
var cards: Dictionary = {}         # id -> card (my files)
var strings: Dictionary = {}       # my locale strings
var nodes: Dictionary = {}         # level -> [{name, script, props}]
var hotspots: Dictionary = {}      # level -> merged hotspots
var manifests: Dictionary = {}     # level -> scene.json


class MockEx extends RefCounted:
	var found := {}
	var req := {}

	func is_found(id: String) -> bool:
		return found.has(id)

	func can_find(id: String) -> bool:
		for r in req.get(id, []):
			if not found.has(str(r)):
				return false
		return true


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var settings: Node = Kit.root().get_node_or_null("Settings")
	var saved := {}
	if settings != null:
		for k in ["puzzle_hints", "text_scale", "high_contrast"]:
			saved[k] = settings.values.get(k)
		settings.values["puzzle_hints"] = 1
		settings.values["text_scale"] = 1.0
		settings.values["high_contrast"] = false
	kit.run_case("data_files_ids_and_texts", _data)
	kit.run_case("history_cards", _history)
	kit.run_case("explore_validation_of_the_real_data", _validation)
	kit.run_case("placement_hotspots_and_spacing", _placement)
	kit.run_case("gates_voices_and_memories", _gates)
	kit.run_case("side_task_porter", _task)
	kit.run_case("kartei_logic", _logic)
	kit.run_case("kartei_scene_auto_keys_hints_cancel", _scene_keys)
	kit.run_case("kartei_scene_full_solve_by_keys", _scene_full)
	if settings != null:
		kit.run_case("kartei_compact_layout_and_contrast", _compact.bind(settings))
		kit.run_case("kartei_hint_setting_modes", _hint_modes.bind(settings))
	kit.run_case("kartei_art_layout_sounds_and_world_cue", _assets)
	if settings != null:
		for k in saved:
			if saved[k] == null:
				settings.values.erase(k)
			else:
				settings.values[k] = saved[k]
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _key(k: int, down := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = down
	return ev


func _instance() -> Node:
	var mg: Node = load(SCENE).instantiate()
	Kit.root().add_child(mg)
	kit.track(mg)
	return mg


func _steps(mg: Node, seconds: float, dt := 0.05) -> void:
	for i in int(ceil(seconds / dt)):
		mg._process(dt)


# ================================================================ data
func _data() -> bool:
	for f in FILES:
		var d = _json("res://data/explore/" + f)
		if kit.ok(d is Dictionary, "%s parses" % f):
			data[f] = d
	var lf = _json(LOCALE)
	if kit.ok(lf is Dictionary and lf.get("strings") is Dictionary, "de_explore_c3p2.json parses"):
		strings = lf["strings"]
	var hf = _json(HISTORY_LOCALE)
	if kit.ok(hf is Dictionary and hf.get("strings") is Dictionary, "de_history_c3p2.json parses"):
		strings.merge(hf["strings"])
	for f in data:
		for e in data[f].get("entries", []):
			kit.ok(not entries.has(str(e.get("id", ""))), "entry %s defined once" % e.get("id"))
			entries[str(e.get("id", ""))] = e
		for c in data[f].get("cards", []):
			cards[str(c.get("id", ""))] = c
	var per := {}
	for id in entries:
		var e: Dictionary = entries[id]
		var lvl := str(e.get("level", ""))
		per[lvl] = int(per.get(lvl, 0)) + 1
		if not kit.ok(LEVELS.has(lvl), "%s: level %s is a part-2 level key %s" % [id, lvl, LEVELS.keys()]):
			continue
		kit.ok(str(id).begins_with(LEVELS[lvl]["prefix"]), "%s: id follows %s<name>" % [id, LEVELS[lvl]["prefix"]])
		kit.eq(str(_area_of(id)), "veltrava", "%s: area veltrava" % id)
		kit.ok(str(e.get("kind")) in ["detail", "secret", "easter_egg", "chat"], "%s: kind %s" % [id, e.get("kind")])
		for k in ["title_key", "prompt_key", "text_key"]:
			var key := str(e.get(k, ""))
			if kit.ok(loc.has(key) and loc.t(key).strip_edges() != "", "%s: %s %s has German text" % [id, k, key]):
				kit.ok(loc.source_of(key).ends_with("de_explore_c3p2.json"), "%s comes from de_explore_c3p2.json" % key)
		kit.ok(loc.t(str(e.get("title_key"))).length() <= 32, "%s: title at most 32 characters" % id)
		kit.ok(loc.t(str(e.get("prompt_key"))).length() <= 32, "%s: prompt at most 32 characters" % id)
		kit.ok(loc.t(str(e.get("text_key"))).length() <= (420 if str(e.get("kind")) != "chat" else 260), "%s: text length %d" % [id, loc.t(str(e.get("text_key"))).length()])
		if e.has("image"):
			kit.ok(ResourceLoader.exists(str(e["image"])), "%s: image %s exists" % [id, e["image"]])
		if e.has("minigame"):
			kit.eq(str(e["minigame"]), SCENE, "%s: the mini-game scene" % id)
		if str(e.get("kind")) == "chat":
			var lines: Array = e.get("lines", [])
			kit.ok(lines.size() >= 4 and lines.size() <= 9, "%s: 4-9 lines (%d)" % [id, lines.size()])
			var speakers := {}
			for l in lines:
				var sp := str(l.get("speaker", ""))
				speakers[sp] = true
				kit.ok(DirAccess.dir_exists_absolute("res://assets/characters/" + sp), "%s: speaker %s has a character folder" % [id, sp])
				kit.ok(loc.has("char.%s.name" % sp), "%s: speaker %s has a German name" % [id, sp])
				kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression %s" % [id, l.get("expr")])
				kit.ok(loc.has(str(l.get("key", ""))) and loc.t(str(l["key"])).length() <= 200, "%s: line %s resolves (<= 200)" % [id, l.get("key")])
			kit.ok(speakers.has("alexei"), "%s: Alexei (the quay's protagonist) speaks" % id)
			kit.ok(speakers.size() >= 2, "%s: a conversation, not a monologue" % id)
		else:
			kit.ok(not e.has("lines"), "%s: only chats carry lines" % id)
	for lvl in LEVELS:
		kit.ok(int(per.get(lvl, 0)) >= 8, "%s has at least 8 finds/chats (%d)" % [lvl, per.get(lvl, 0)])
	kit.eq(per.get("L_C3_RegistryA", 0), 18, "registry: 18 entries (9 Alexei incl. the task, 9 Konrad incl. the mini-game)")
	kit.eq(per.get("L_C3_Quay", 0), 10, "quay: 7 finds and 3 chats")
	# German typography and the rename guard over every string of my locale files
	for k in strings:
		var s := str(strings[k])
		kit.ok(s.strip_edges() != "" and s == s.strip_edges(), "'%s' is not empty and has no stray spaces" % k)
		kit.ok(not s.contains("\""), "'%s': German quotes, not ASCII" % k)
		kit.ok(not s.contains(" - ") and not s.contains("--"), "'%s': dash as ' – '" % k)
		kit.ok(not s.contains("..."), "'%s': ellipsis as '…'" % k)
		kit.ok(s.count("„") == s.count("“") and s.count("‚") == s.count("‘"), "'%s': balanced German quotes" % k)
	var old: String = load("res://tests/test_rename_guard.gd").old_id().to_lower()
	if kit.ok(old != "", "pre-rename id derivable"):
		var raw := FileAccess.get_file_as_string(LOCALE).to_lower() + FileAccess.get_file_as_string(HISTORY_LOCALE).to_lower()
		for f in FILES:
			raw += FileAccess.get_file_as_string("res://data/explore/" + f).to_lower()
		kit.ok(not raw.contains(old), "texts and data never use the pre-rename name")
	# the Veltrava currency is the Krone (exchange office at the station), never francs
	kit.ok(not JSON.stringify(strings).contains("Frank"), "no francs in Veltrava")
	return true


func _area_of(id: String) -> String:
	for f in data:
		for e in data[f].get("entries", []):
			if str(e.get("id", "")) == id:
				return str(e.get("area", data[f].get("area", "")))
	return ""


func _history() -> bool:
	kit.eq(Kit.sorted(cards.keys()), Kit.sorted(HISTORY_AT.keys()), "two new real-history cards")
	for cid in HISTORY_AT:
		var c: Dictionary = cards.get(cid, {})
		if not kit.ok(not c.is_empty(), "card %s exists" % cid):
			continue
		kit.eq(str(c.get("side", "")), str(cid).split(".")[1], "%s: side" % cid)
		kit.ok(str(c.get("year", "")).length() == 4, "%s: year" % cid)
		var n: int = loc.t(str(c.get("text_key", ""))).length()
		kit.ok(n >= 450 and n <= 800, "%s: text length %d within 450-800" % [cid, n])
		kit.ok(loc.source_of(str(c.get("text_key", ""))).ends_with("de_history_c3p2.json"), "%s: text from de_history_c3p2.json" % cid)
		var web := 0
		for s in c.get("sources", []):
			kit.ok(s is Dictionary and str(s.get("label", "")).strip_edges() != "", "%s: every source has a label" % cid)
			var url := str(s.get("url", "")) if s is Dictionary else ""
			kit.ok(url == "" or url.begins_with("https://"), "%s: source url %s" % [cid, url])
			if url != "":
				web += 1
		kit.ok(web >= 2, "%s: at least two independent web sources (%d)" % [cid, web])
		var at: Dictionary = entries.get(HISTORY_AT[cid], {})
		kit.ok((at.get("history", []) as Array).has(cid), "%s is unlocked by %s" % [cid, HISTORY_AT[cid]])
	# never on a joke spot; only the two own-card finds unlock cards
	for id in entries:
		if not (id in HISTORY_AT.values()):
			kit.ok((entries[id].get("history", []) as Array).is_empty(), "%s unlocks no card" % id)
	return true


func _validation() -> bool:
	real = kit.track(load(EXPLORE).new())
	real.print_warnings = false
	real.notify_tasks = false
	real.reload()
	var mine: Array = []
	for w in real.warnings:
		var s := str(w)
		var hit := s.contains("c3p2_") or s.contains(TASK)
		for id in entries:
			hit = hit or s.contains("'%s'" % id) or s.contains(str(id) + ":")
		for cid in cards:
			hit = hit or s.contains(cid)
		if hit:
			mine.append(s)
	kit.eq(mine, [], "Explore validation: no problem in the part-2 data")
	for id in entries:
		kit.ok(real.has_entry(id), "Explore loaded %s" % id)
	for cid in cards:
		kit.ok(real.has_card(cid), "Explore loaded card %s" % cid)
	kit.eq(real.counts("L_C3_RegistryA")["total"], 18, "counts(level key) sees every registry find")
	kit.eq(real.counts("L_C3_Quay")["total"], 10, "counts(quay)")
	kit.eq(real.tasks_for("L_C3_RegistryA").map(func(t): return str(t["id"])), [TASK], "the registry's one side task")
	return true


# ================================================================ placement
static func _nodes_of(ps: PackedScene) -> Array:
	var out: Array = []
	var st: SceneState = ps.get_state()
	for i in st.get_node_count():
		var props := {}
		var script_path := ""
		for j in st.get_node_property_count(i):
			var pn := str(st.get_node_property_name(i, j))
			var pv = st.get_node_property_value(i, j)
			if pn == "script":
				script_path = pv.resource_path if pv is Resource else ""
			else:
				props[pn] = pv
		out.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props})
	return out


func _explore_nodes(lid: String) -> Array:
	return (nodes.get(lid, []) as Array).filter(func(n): return str(n["props"].get("kind", "")) in ["discover", "chat"])


func _pos(lid: String, hid: String) -> Vector2:
	var h = (hotspots.get(lid, {}) as Dictionary).get(hid, null)
	return Vector2(float(h[0]), float(h[1])) if h is Array and h.size() >= 2 else Vector2.INF


func _placement() -> bool:
	for lid in LEVELS:
		var spec: Dictionary = LEVELS[lid]
		var ps = load(str(spec["path"]))
		if not kit.ok(ps is PackedScene, "%s loads" % spec["path"]):
			continue
		nodes[lid] = _nodes_of(ps)
		var env := "res://assets/environments/%s/" % spec["env"]
		var man = _json(env + "scene.json")
		manifests[lid] = man if man is Dictionary else {}
		var hs := {}
		var x = _json(env + "explore_hotspots.json")
		if kit.ok(x is Dictionary and x.get("hotspots") is Dictionary, "%sexplore_hotspots.json parses" % env):
			hs.merge(x["hotspots"], true)
		if manifests[lid].get("hotspots") is Dictionary:
			hs.merge(manifests[lid]["hotspots"], true)        # scene.json wins (Level._merge_explore_hotspots)
		hotspots[lid] = hs
	var count := {}
	for lid in nodes:
		var spec: Dictionary = LEVELS[lid]
		var walk := PackedVector2Array()
		for q in manifests[lid].get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		var finds := _explore_nodes(lid)
		kit.ok(finds.size() >= int(spec["min"]) - 2, "%s: exploration nodes placed (%d)" % [lid, finds.size()])
		for n in finds:
			var p: Dictionary = n["props"]
			var who := "%s/%s" % [lid, n["name"]]
			var chain: Array = Array(p.get("explore_chain", PackedStringArray()))
			var ids: Array = chain if not chain.is_empty() else [str(p.get("explore_id", ""))]
			for id in ids:
				count[str(id)] = (count.get(str(id), []) as Array) + [who]
				if kit.ok(entries.has(str(id)), "%s: entry %s exists" % [who, id]):
					kit.eq(str(entries[str(id)]["level"]), lid, "%s: %s belongs to this level key" % [who, id])
			var first := str(p.get("explore_id", ""))
			if entries.has(first):
				kit.eq(str(p.get("kind")), "chat" if str(entries[first]["kind"]) == "chat" else "discover", "%s: node kind matches %s" % [who, first])
			if not chain.is_empty():
				var fresh := MockEx.new()
				for id in entries:
					fresh.req[id] = entries[id].get("requires", [])
				kit.eq(first, INTERACTABLE.pick_chain_step(PackedStringArray(chain), fresh), "%s: explore_id is the chain's entry in a new game" % who)
			kit.ok(bool(p.get("once", false)), "%s: once" % who)
			var pos := _pos(lid, str(p.get("hotspot_id", "")))
			if not kit.ok(pos.is_finite(), "%s: hotspot %s resolves" % [who, p.get("hotspot_id")]):
				continue
			if walk.size() >= 3:
				kit.ok(Geometry2D.is_point_in_polygon(pos, walk), "%s at %s lies in the walk area" % [who, pos])
			var on_npc: bool = str(p.get("kind")) == "chat" and str(p.get("hotspot_id")) in spec.get("npcs", [])
			for s in spec["story"] + (spec.get("npcs", []) if not on_npc else []):
				var sp := _pos(lid, str(s))
				if sp.is_finite():
					kit.ok(pos.distance_to(sp) >= GAP_STORY, "%s keeps %d px from %s (%.1f)" % [who, int(GAP_STORY), s, pos.distance_to(sp)])
			if on_npc:
				kit.ok(str(p.get("npc_id", "")) != "", "%s: a chat on an NPC anchor turns that NPC" % who)
				var npc := str(p.get("npc_id", ""))
				for id in ids:
					var sps: Array = (entries.get(str(id), {}).get("lines", []) as Array).map(func(l): return str(l.get("speaker", "")))
					kit.ok(npc in sps, "%s: npc %s speaks in %s" % [who, npc, id])
			for o in finds:
				var op := _pos(lid, str(o["props"].get("hotspot_id", "")))
				if o["name"] == n["name"] or not op.is_finite() or str(o["props"].get("hotspot_id")) == str(p.get("hotspot_id")):
					continue
				kit.ok(pos.distance_to(op) >= GAP_FIND, "%s keeps %d px from %s (%.1f)" % [who, int(GAP_FIND), o["name"], pos.distance_to(op)])
	for id in entries:
		kit.eq((count.get(id, []) as Array).size(), 1, "%s placed exactly once %s" % [id, count.get(id, [])])
	# the explore stream's own hotspots: only exp_* names, never a story name of §5
	for lid in LEVELS:
		var x = _json("res://assets/environments/%s/explore_hotspots.json" % LEVELS[lid]["env"])
		for h in (x.get("hotspots", {}) if x is Dictionary else {}):
			kit.ok(str(h).begins_with("exp_"), "%s: explore hotspot %s is an exp_* name" % [lid, h])
	return true


# ================================================================ gates, voices, memories
func _gates() -> bool:
	var reg: Array = _explore_nodes("L_C3_RegistryA")
	kit.ok(not reg.is_empty(), "registry exploration nodes parsed")
	var scenes = _json("res://data/v3/scenes.json")
	var who := {}
	for s in (scenes.get("scenes", []) if scenes is Dictionary else []):
		who[str(s.get("id", ""))] = str(s.get("protagonist", ""))
	kit.eq([who.get("L_C3_RegistryA"), who.get("L_C3_RegistryB")], ["alexei", "konrad"], "A is Alexei's, B is Konrad's")
	for n in reg:
		var p: Dictionary = n["props"]
		var x := _pos("L_C3_RegistryA", str(p.get("hotspot_id", ""))).x
		kit.eq(n["script"], SPOT, "%s: registry spot script (memory-aware gates)" % n["name"])
		if x < 680.0:
			kit.eq([str(p.get("after_objective", "")), str(p.get("until_objective", ""))], ["", "c3c_talk_konrad"], "%s (yard/Annahme): Alexei's until he meets Konrad" % n["name"])
			kit.eq(Array(p.get("memory_scenes", PackedStringArray())), ["L_C3_RegistryA"], "%s: remembered in A" % n["name"])
		else:
			kit.ok(x >= 690.0, "%s: card hall or further" % n["name"])
			kit.eq([str(p.get("after_objective", "")), str(p.get("until_objective", ""))], ["c3c_talk_konrad", "c3d_choose"], "%s (card hall …): Konrad's until Blatt 7 is decided" % n["name"])
			kit.eq(Array(p.get("memory_scenes", PackedStringArray())), ["L_C3_RegistryB"], "%s: remembered in B" % n["name"])
	# partner spots: the NPC partner of a scene never stands on a find of that scene
	var sp: Dictionary = manifests.get("L_C3_RegistryA", {}).get("spawns", {})
	for n in reg:
		var p: Dictionary = n["props"]
		var pos := _pos("L_C3_RegistryA", str(p.get("hotspot_id", "")))
		var partner := "SP_C3_KonradCards" if str(p.get("until_objective")) == "c3c_talk_konrad" and str(p.get("after_objective", "")) == "" else "SP_C3_AlexeiTable"
		if sp.get(partner) is Array:
			kit.ok(pos.distance_to(Vector2(float(sp[partner][0]), float(sp[partner][1]))) >= 20.0, "%s keeps clear of the partner at %s" % [n["name"], partner])
	# live: a spot follows Story gates outside memories and the remembered scene inside one
	var game: Node = Kit.root().get_node_or_null("Game")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	var st: Node = Kit.root().get_node_or_null("Story")
	if game == null or ex == null or st == null or not ("memory_mode" in game):
		print("      note: autoloads missing, live gate check skipped")
		return true
	var before: Dictionary = ex.state()
	ex.restore({"found": [], "cards": []})
	var a_spot: Node = load(SPOT).new()
	a_spot.kind = "discover"
	a_spot.explore_id = "veltrava.registry.gate_sign"
	a_spot.once = true
	a_spot.until_objective = "c3c_talk_konrad"
	a_spot.memory_scenes = PackedStringArray(["L_C3_RegistryA"])
	var b_spot: Node = load(SPOT).new()
	b_spot.kind = "discover"
	b_spot.explore_id = "veltrava.registry.kartei"
	b_spot.once = true
	b_spot.after_objective = "c3c_talk_konrad"
	b_spot.until_objective = "c3d_choose"
	b_spot.memory_scenes = PackedStringArray(["L_C3_RegistryB"])
	kit.mount(a_spot)
	kit.mount(b_spot)
	var met := str(st.objective_state("c3c_talk_konrad")) == "complete"
	if not met:
		kit.ok(a_spot.is_active() and not b_spot.is_active(), "running game before the meeting: Alexei's find open, Konrad's closed")
	var mm = game.memory_mode
	var ms = game.memory_scene
	game.memory_mode = true
	game.memory_scene = "L_C3_RegistryB"
	var in_b := [a_spot.is_active(), b_spot.is_active()]
	game.memory_scene = "L_C3_RegistryA"
	var in_a := [a_spot.is_active(), b_spot.is_active()]
	game.memory_scene = "L_C3_RegistryC"
	var in_c := [a_spot.is_active(), b_spot.is_active()]
	game.memory_mode = mm
	game.memory_scene = ms
	kit.eq(in_b, [false, true], "memory of B: Konrad's finds (the mini-game) open, Alexei's closed")
	kit.eq(in_a, [true, false], "memory of A: Alexei's finds open, Konrad's closed")
	kit.eq(in_c, [false, false], "memory of the fire: nothing to find")
	ex.restore(before)
	return true


# ================================================================ side task
func _task() -> bool:
	if real == null:
		return true
	var t: Dictionary = real.task(TASK)
	if not kit.ok(not t.is_empty(), "task %s exists" % TASK):
		return true
	kit.eq(str(t.get("level", "")), "L_C3_RegistryA", "task level key")
	kit.eq(real.task_steps(TASK), TASK_STEPS, "thermos -> radio -> key board -> back to the booth")
	for k in ["title_key", "summary_key"]:
		kit.ok(loc.has(str(t.get(k, ""))) and loc.source_of(str(t[k])).ends_with("de_explore_c3p2.json"), "%s has text in de_explore_c3p2.json" % k)
	kit.ok(loc.t(str(t["title_key"])).length() <= 32, "task title at most 32 characters")
	kit.ok(loc.t(str(t["summary_key"])).length() <= 200, "task summary at most 200 characters")
	for s in t.get("steps", []):
		kit.ok(loc.has(str(s.get("hint_key", ""))) and loc.t(str(s["hint_key"])).length() <= 120, "hint %s resolves (<= 120)" % s.get("hint_key"))
	for i in range(1, TASK_STEPS.size()):
		kit.eq(real.requires_of(TASK_STEPS[i]), [TASK_STEPS[i - 1]], "%s requires the step before" % TASK_STEPS[i])
	kit.eq(real.requires_of(TASK_STEPS[0]), [], "the thermos starts the task")
	# states on the private instance
	real.restore({"found": [], "cards": []})
	kit.eq(str(real.task_state(TASK)["state"]), "not_started", "not started in a new game")
	kit.ok(not real.can_find(TASK_STEPS[1]), "the radio waits for the thermos")
	for i in TASK_STEPS.size():
		var r: Dictionary = real.find(TASK_STEPS[i])
		kit.ok(bool(r.get("ok", false)) and bool(r.get("new", false)), "step %s found in order" % TASK_STEPS[i])
		kit.eq(str(real.task_state(TASK)["state"]), "done" if i == TASK_STEPS.size() - 1 else "active", "state after %s" % TASK_STEPS[i])
	real.restore({"found": [], "cards": []})
	# the drivers' loop on the parsed scene, story gates as in the final pass of each registry scene
	var quests = _json("res://data/v3/quests.json")
	var objs := {}
	for q in (quests.get("quests", []) if quests is Dictionary else []):
		objs[str(q.get("scene", ""))] = (q.get("objectives", []) as Array).map(func(o): return str(o["id"]))
	var m := MockEx.new()
	for id in entries:
		m.req[id] = entries[id].get("requires", [])
	var all_found := {}
	for sid in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
		var done := {}
		for prev in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
			var ol: Array = objs.get(prev, [])
			if prev == sid:
				for i in ol.size() - 1:
					done[ol[i]] = true
				break
			for o in ol:
				done[o] = true
		var order := _drive(_explore_nodes("L_C3_RegistryA"), m, done)
		for id in order:
			all_found[id] = sid
		if sid == "L_C3_RegistryA":
			kit.eq(order.filter(func(x): return x in TASK_STEPS), TASK_STEPS, "scene A: the drivers' loop completes „Die Pforte“ in step order")
		if sid in ["L_C3_RegistryC", "L_C3_RegistryD"]:
			kit.eq(order, [], "%s (fire): nothing new to find" % sid)
	for id in entries:
		if str(entries[id]["level"]) == "L_C3_RegistryA":
			kit.ok(all_found.has(id), "%s is reached in its scene" % id)
	var mq := MockEx.new()
	var q_order := _drive(_explore_nodes("L_C3_Quay"), mq, {})
	kit.eq(q_order.size(), 10, "quay: the loop reaches every find and chat")
	return true


func _drive(ns: Array, m: MockEx, done: Dictionary) -> Array:
	var order: Array = []
	var progressed := true
	var guard := 0
	while progressed and guard < 100:
		guard += 1
		progressed = false
		for n in ns:
			var p: Dictionary = n["props"]
			if str(p.get("after_objective", "")) != "" and not done.has(str(p["after_objective"])):
				continue
			if str(p.get("until_objective", "")) != "" and done.has(str(p["until_objective"])):
				continue
			var chain := PackedStringArray(p.get("explore_chain", PackedStringArray()))
			var cur := INTERACTABLE.pick_chain_step(chain, m) if not chain.is_empty() else str(p.get("explore_id", ""))
			if cur == "" or m.found.has(cur) or not m.can_find(cur):
				continue
			m.found[cur] = true
			order.append(cur)
			progressed = true
	return order


# ================================================================ mini-game: rule
func _logic() -> bool:
	var lg = Logic.new()
	kit.eq(lg.drawer, Logic.START, "the drawer after the fall")
	kit.eq(lg.floor, Logic.FLOOR, "nine cards on the floor")
	var all: Array = Logic.solved_order()
	kit.eq(all.size(), 15, "three guides and twelve cards")
	var keys := {}
	for id in Logic.CARDS:
		var c: Dictionary = Logic.CARDS[id]
		keys[str(Logic.key(id))] = true
		kit.eq(str(Logic.LETTERS.get(Logic.written_letter(id), "")), str(c["origin"]), "%s: written letter %s means %s" % [id, Logic.written_letter(id), c["origin"]])
		kit.eq(c["code"], "%s %02d/%02d" % [Logic.written_letter(id), int(c["year"]), int(c["num"])], "%s: code matches year and number" % id)
		kit.eq(Logic.written_letter(id) in ["Б", "К", "В"], str(c["lang"]) == "ru", "%s: Cyrillic letter exactly on the Russian cards" % id)
	kit.eq(keys.size(), Logic.CARDS.size(), "every card has its own key")
	kit.eq(Logic.CARDS.values().filter(func(c): return str(c["lang"]) == "ru").size(), 5, "five Russian cards")
	kit.eq(Logic.FLOOR.filter(func(i): return Logic.written_letter(str(i)) == "В").size(), 2, "two В traps on the floor")
	kit.eq(Logic.FLOOR.filter(func(i): return str(Logic.CARDS[i]["result"]) == "address").size(), 1, "one card says „Anschrift übermittelt“, and it lies on the floor")
	# refusals name the rule that is broken
	lg.take("lacis")                     # В 62/08 -> V; into the B section
	kit.eq(lg.insert(1)["reason"], "cyr_v", "В filed under B: the B/V trap")
	kit.eq(lg.held, "lacis", "a refused card stays in the hand")
	kit.eq(lg.insert(5)["ok"], true, "В 62/08 belongs right behind guide V")
	lg.take("wiebe")                     # Б 63/04 -> B
	kit.eq(lg.insert(3)["reason"], "cyr_b", "Б filed under K")
	lg.take("sorokin")                   # К 61/17 -> K
	kit.eq(lg.insert(lg.drawer.size())["reason"], "cyr_k", "К filed at the end (V)")
	lg.take("kulikowa")                  # K 63/09 (German clerk)
	kit.eq(lg.insert(0)["reason"], "origin", "a Latin card in front of guide B")
	kit.eq(lg.insert(3)["reason"], "year", "K 63/09 in front of K 62/05: the year decides")
	lg.reset()
	lg.take("hartl")                     # В 63/15: V section [guide_V, petrauskas V 63/11]
	kit.eq(lg.insert(5)["reason"], "number", "В 63/15 in front of V 63/11: same year, the number decides")
	kit.eq(lg.insert(6)["ok"], true, "В 63/15 behind V 63/11")
	kit.eq(lg.insert(2)["reason"], "nothing_held", "nothing in the hand")
	kit.ok(not lg.take("kranz"), "a card that never fell cannot be taken")
	# every order of the floor works: forward, backward, rotated, interleaved
	for order in [Logic.FLOOR, _rev(Logic.FLOOR), Logic.FLOOR.slice(4) + Logic.FLOOR.slice(0, 4),
			["hartl", "sell", "lacis", "wiebe", "kowalenko", "hrubes", "sorokin", "wanek", "kulikowa"]]:
		var g = Logic.new()
		for id in order:
			g.take(str(id))
			var r: Dictionary = g.insert(g.valid_gap(str(id)))
			kit.ok(bool(r["ok"]), "%s filed at its gap" % id)
		kit.ok(g.done and g.is_sorted(), "order %s: the drawer is complete and sorted" % [order.slice(0, 3)])
		kit.eq(g.drawer, all, "the final order is the commission's")
	return true


static func _rev(a: Array) -> Array:
	var b := a.duplicate()
	b.reverse()
	return b


# ================================================================ mini-game: scene
func _scene_keys() -> bool:
	var mg := _instance()
	kit.ok(mg.is_in_group("minigame"), "Kartei joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "veltrava.registry.kartei", "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var kg := _instance()
	var res: Array = []
	kg.finished.connect(func(ok: bool): res.append(ok))
	kg.open({"explore_id": "veltrava.registry.kartei", "auto": false})
	_steps(kg, 0.4)
	kit.eq(kg.shown_card(), "kulikowa", "the cursor starts on K 63/09")
	kit.ok(str(kg._code_label.text) == "K 63/09" and str(kg._text_label.text).contains("Kulikowa"), "the side panel reads the card")
	kg.modal_input(_key(KEY_RIGHT))
	kit.eq(kg.shown_card(), "lacis", "Right moves along the floor")
	kit.ok(str(kg._lang_label.text).contains("Russisch") and str(kg._lang_label.text).contains("ВЕЛЬТРАВА"), "a Russian card says so, its origin as written")
	kit.ok(kg.modal_input(_key(KEY_E)), "E is consumed")
	kit.eq(kg.logic.held, "lacis", "E takes the card")
	kit.eq(str(kg._btn_main.text), "Einstecken", "the main button files now")
	kg.caret = 1
	kg.modal_input(_key(KEY_ENTER))
	kit.eq(kg.fails, 1, "В under B is refused (a failure)")
	kit.ok(str(kg._status.text).contains("Veltrava"), "the refusal explains the Cyrillic V")
	kit.eq(kg.logic.held, "lacis", "the card stays in the hand")
	kg.modal_input(_key(KEY_LEFT))
	kit.eq(kg.caret, 0, "Left moves the caret")
	kg.modal_input(_key(KEY_SPACE))
	kit.ok(kg.fails == 2 and kg._hint_box.visible, "a hint after two refusals")
	kit.ok(str(kg._hint_label.text).contains("Б ist B"), "the first hint: rule and alphabet")
	kg.modal_input(_key(KEY_BACKSPACE))
	kit.eq(kg.logic.held, "", "Backspace puts the card back")
	kg.modal_input(_key(KEY_E))
	kit.ok(kg.handle_cancel(), "Esc handled")
	kit.eq([kg.logic.held, res], ["", []], "Esc with a card in the hand only puts it back")
	kg.show_hint(2)
	kit.ok(str(kg._hint_label.text).contains("gehört zwischen"), "the second hint names the gap")
	kit.ok(kg.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc without a card gives up without a find")
	return true


func _scene_full() -> bool:
	var kg := _instance()
	var res: Array = []
	kg.finished.connect(func(ok: bool): res.append(ok))
	kg.open({"explore_id": "veltrava.registry.kartei", "auto": false})
	_steps(kg, 0.4)
	var guard := 0
	while not kg.solved and guard < 40:
		guard += 1
		kg.modal_input(_key(KEY_E))
		var target: int = kg.logic.valid_gap(kg.logic.held)
		var g2 := 0
		while kg.caret != target and g2 < 30:
			kg.modal_input(_key(KEY_RIGHT if kg.caret < target else KEY_LEFT))
			g2 += 1
		kg.modal_input(_key(KEY_E))
		_steps(kg, 0.25)
	kit.ok(kg.solved, "all nine cards by keys alone")
	kit.eq(kg.fails, 0, "no refusal on the right path")
	kit.eq(kg.logic.drawer, Logic.solved_order(), "the drawer is in order")
	kit.ok(str(kg._status.text).contains("Namen"), "Konrad's last line")
	_steps(kg, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(kg, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.insert(") and not body.contains("place(") and not body.contains("mark_solved("),
		"demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "Kartei extends minigame_base.gd")
	return true


func _compact(settings: Node) -> bool:
	settings.values["text_scale"] = 1.5
	settings.values["high_contrast"] = true
	var kg := _instance()
	kg.open({"explore_id": "veltrava.registry.kartei", "auto": false})
	_steps(kg, 0.4)
	kit.ok(kg.compact and kg.S == 2, "larger text: compact layout, art x2")
	var sz: Array = kg.layout.get("size", [0, 0])
	kit.eq(kg._scene.custom_minimum_size, Vector2(float(sz[0]), float(sz[1])) * 2.0, "the stage shrinks to x2")
	kit.ok(not kg._subtitle.visible, "the flavour subtitle gives way to the text")
	kit.ok(kg._scene.custom_minimum_size.x + 860.0 + 36.0 <= 1800.0, "stage and side panel fit the panel width")
	kg.modal_input(_key(KEY_E))
	kg._scene.queue_redraw()
	kit.eq(kg.logic.held, "kulikowa", "high contrast plays the same")
	settings.values["text_scale"] = 1.0
	settings.values["high_contrast"] = false
	var n := _instance()
	n.open({"explore_id": "veltrava.registry.kartei", "auto": false})
	kit.ok(not n.compact and n.S == 3, "default text: art x3")
	kit.ok(n._scene.custom_minimum_size.x + 500.0 + 36.0 <= 1800.0, "x3 stage and side panel fit the panel width")
	kit.ok(n._scene.custom_minimum_size.y <= 450.0, "x3 stage leaves room for header, status, hint and buttons")
	return true


func _hint_modes(settings: Node) -> bool:
	settings.values["puzzle_hints"] = 0
	var a := _instance()
	a.open({"explore_id": "veltrava.registry.kartei", "auto": false})
	_steps(a, 0.4)
	a.modal_input(_key(KEY_E))
	for i in 3:
		a.caret = 0
		a.modal_input(_key(KEY_ENTER))
	kit.ok(a.fails == 3 and not a._hint_box.visible, "puzzle_hints 0: no hint even after three refusals")
	settings.values["puzzle_hints"] = 2
	var b := _instance()
	b.open({"explore_id": "veltrava.registry.kartei", "auto": false})
	kit.ok(b._hint_box.visible, "puzzle_hints 2: the first hint at once")
	settings.values["puzzle_hints"] = 1
	return true


# ================================================================ art, layout, sounds, world cue
func _assets() -> bool:
	var lay = _json(ART + "kartei_layout.json")
	if not kit.ok(lay is Dictionary, "kartei_layout.json parses"):
		return true
	var sizes := {"kartei_back": Vector2i(400, 136), "kartei_front": Vector2i(400, 136), "kartei_tabs": Vector2i(22 * 15, 36),
		"kartei_faces": Vector2i(46 * 9, 30), "world_drawer": Vector2i(68, 12)}
	for n in sizes:
		var p := ART + str(n) + ".png"
		if kit.ok(ResourceLoader.exists(p), "%s imported" % p):
			kit.eq(Vector2i((load(p) as Texture2D).get_size()), sizes[n], "%s size" % n)
	var cl := ART + "kartei_closeup.png"
	if kit.ok(ResourceLoader.exists(cl), "close-up imported"):
		var s := (load(cl) as Texture2D).get_size()
		kit.ok(s.x <= 320 and s.y <= 200, "close-up fits 320x200 (%s)" % s)
	kit.eq(Kit.sorted(lay.get("tabs", [])), Kit.sorted(Logic.GUIDES.keys() + Logic.CARDS.keys()), "a tab for every guide and card")
	kit.eq(lay.get("faces", []), Logic.FLOOR, "a face for every floor card, in floor order")
	kit.eq(lay.get("solved", []), Logic.solved_order(), "the generator's order is the rule's")
	for id in Logic.CARDS:
		kit.eq(str((lay.get("codes", {}) as Dictionary).get(id, "")), str(Logic.CARDS[id]["code"]), "%s: the art writes the rule's code" % id)
	var rects: Array = []
	var fc: Array = lay.get("face_cell", [46, 30])
	for id in Logic.FLOOR:
		var p: Array = (lay.get("floor", {}) as Dictionary).get(id, [-999, -999]) as Array
		var r := Rect2(float(p[0]), float(p[1]), float(fc[0]), float(fc[1]))
		kit.ok(Rect2(0, float(lay.get("front_y", 42)) + 24.0, 400, 136).encloses(Rect2(float(p[0]), float(p[1]), float(fc[0]), float(fc[1]))), "%s lies on the floor, below the drawer" % id)
		for o in rects:
			kit.ok(not r.intersects(o), "%s does not overlap another card" % id)
		rects.append(r)
	var x0 := float(lay.get("x0", 22)) + 15.0 * float(lay.get("slot_w", 22)) + 12.0
	kit.ok(x0 <= 386.0, "a full drawer plus the open gap stays inside the drawer walls (%.0f)" % x0)
	for s in SFX:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % s), "sound %s imported" % s)
	# world cue: frame 0 until the find, then 1 (the drawer is back in its cabinet)
	var cue: Node = (load("res://scripts/ui/minigames/kartei_world_cue.gd") as GDScript).new()
	cue.texture = load(ART + "world_drawer.png")
	kit.mount(cue)
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if ex != null:
		var before: Dictionary = ex.state()
		ex.restore({"found": [], "cards": []})
		cue._sync()
		kit.eq([cue.frame, cue.restored], [0, false], "world cue: the fallen drawer")
		ex.restore({"found": ["veltrava.registry.kartei"], "cards": []})
		cue._sync()
		kit.eq([cue.frame, cue.restored], [1, true], "world cue: put back after the find")
		ex.restore(before)
	# the cue stands at the find, on the floor line
	var ps = load(LEVELS["L_C3_RegistryA"]["path"])
	for n in (_nodes_of(ps) if ps is PackedScene else []):
		if n["name"] == "KarteiCue":
			var at: Vector2 = n["props"].get("position", Vector2.ZERO)
			var hp := _pos("L_C3_RegistryA", "exp_kartei")
			kit.ok(hp.is_finite() and absf(at.x - hp.x) <= 24.0 and at.y <= hp.y, "the world cue sits beside exp_kartei, behind the feet line")
	return true
