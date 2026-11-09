extends RefCounted
## Chapter 4 part 1 exploration (documentation/C4_DESIGN.md §4/§6/§7, TECHNICAL_ARCHITECTURE §12.1/§12.3/§12.8/§12.9;
## owner: exploration c4): the finds and chats of the two shared level files (L_C4_Tunnels: Story scenes A + C under the
## level key L_C4_TunnelsA; L_C4_Annex: B + D under L_C4_AnnexA), the side task „Ilses Puppe“, the three real-history
## cards and the mini-game „Der Hebelrahmen“ (scenes/ui/minigames/LeverFrame.tscn).
##  * data: files, ids, kinds, levels, the `scene` of every find, texts (German style, lengths), chats (speakers,
##    expressions, the protagonist of the walk area speaks), cards (sources only in the data, 450–800 characters,
##    unlocked where they belong), Explore validation of the real data
##  * placement: every entry placed exactly once in its level file, hotspots resolve (scene.json + explore_hotspots.json,
##    the info block of the art contract), walk band, walk area of the scene, blockers, spacing to story / NPC spots and
##    to the other finds; the gates of every node (after / until / memory_scenes) follow its scene
##  * the real Game path: both real level files mounted with the live Story at every exploration pass of the drivers
##    (C4_DESIGN §9), the drivers' loop on the real nodes (autoplay.pending_finds + Explore.find) reaches every find,
##    chat and task step in its own scene; memories open the remembered walk area, an absent NPC has no chat; the
##    memory cards count the finds of their level file
##  * the mini-game: the rule (locks, refusals, no dead end, the three orders), the scene (auto mode, keys, hints,
##    cancel, full solve by keys only, compact layout, hint modes), art / layout / sounds
## Writes nothing: Explore / Story / Settings / Game values touched here are restored before the case ends.

const Kit := preload("res://tests/support/test_kit.gd")
const Logic := preload("res://scripts/ui/minigames/lever_logic.gd")
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const AUTOPLAY := "res://scripts/core/autoplay.gd"
const EXPLORE := "res://scripts/core/explore.gd"
const SCENE := "res://scenes/ui/minigames/LeverFrame.tscn"
const GAME := "res://scripts/ui/minigames/lever_game.gd"
const SPOT := "res://scripts/ui/minigames/lever_spot.gd"
const ART := "res://assets/ui/minigames/lever/"
const LOCALE := "res://data/locale/de_explore_c4.json"
const HISTORY_LOCALE := "res://data/locale/de_history_c4.json"
const FILES := ["c4_tunnels.json", "c4_annex.json", "c4_history_soviet.json", "c4_history_reich.json"]
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
## New characters of Chapter 4 (cast stream): their sheets may still be on the way while this suite runs.
const NEW_CAST := ["lev", "marta", "registrar"]
const LEVELS := {
	"L_C4_TunnelsA": {"path": "res://scenes/levels/L_C4_Tunnels.tscn", "env": "karsk_tunnels", "prefix": "karsk.tunnels.",
		"area": "karsk", "scenes": ["L_C4_TunnelsA", "L_C4_TunnelsB"],
		"story": ["book_shelf", "desk_book", "lev_cellar", "lamp_table", "tunnel_door", "office_desk", "paint_stand",
			"wagon_side", "wagon_door", "lev_siding"], "npcs": ["lev_cellar", "lev_siding"], "total": 22},
	"L_C4_AnnexA": {"path": "res://scenes/levels/L_C4_Annex.tscn", "env": "berlin_annex", "prefix": "berlin.annex.",
		"area": "berlin", "scenes": ["L_C4_AnnexA", "L_C4_AnnexB"],
		"story": ["door_9", "timetable_case", "marta_tram", "column_s2", "loading_hatch", "drawer_s8", "plan_wall",
			"tube_station", "registrar_counter"], "npcs": ["marta_tram", "registrar_counter", "guard_annex"], "total": 18,
		"extra": 4},          # round 13: the data desk's four entries (c4_annex_terminal.json, tests/test_c4_terminal.gd)
}
## Per Story scene: who plays it, the x range of its walk area, the node gates, the remembered scene, how many entries.
const SCENES := {
	"L_C4_TunnelsA": {"who": "alexei", "x": [60.0, 690.0], "after": "", "until": "c4a_open_door", "count": 8,
		"chat_after": "c4a_talk_tunnel"},
	"L_C4_TunnelsB": {"who": "alexei", "x": [730.0, 1900.0], "after": "c4a_open_door", "until": "", "count": 14,
		"chat_until": "c4c_talk_lev"},
	"L_C4_AnnexA": {"who": "konrad", "x": [30.0, 810.0], "after": "", "until": "c4b_inspect_crates", "count": 11,
		"chat_after": "c4b_talk_ilse"},
	"L_C4_AnnexB": {"who": "konrad", "x": [890.0, 1900.0], "after": "c4b_inspect_crates", "until": "", "count": 7},
}
const GAP_STORY := 24.0
const GAP_FIND := 14.0
const HISTORY_AT := {"hist.soviet.order_270": "karsk.tunnels.lev_photo",
	"hist.soviet.special_settlements": "karsk.tunnels.stovepipes", "hist.reich.ostarbeiter": "berlin.annex.wallpaper",
	"hist.reich.denunciation": "berlin.annex.waiting_bench"}
const TASK := "berlin.task.doll"
const TASK_STEPS := ["berlin.annex.doll_ask", "berlin.annex.doll_cellar", "berlin.annex.doll_back"]
## The tunnels' side task „Wir sind vierzehn“ (C4_DESIGN §6): the names in wagon 24 318, left to right along it, then Lev.
const TASK2 := "karsk.task.fourteen"
const TASK2_STEPS := ["karsk.tunnels.names_beam", "karsk.tunnels.names_pipe", "karsk.tunnels.names_bench",
	"karsk.tunnels.names_rail", "karsk.tunnels.names_lev"]
const TASK2_SPOTS := {"karsk.tunnels.names_beam": "exp_task_beam", "karsk.tunnels.names_pipe": "exp_task_pipe",
	"karsk.tunnels.names_bench": "exp_task_bench", "karsk.tunnels.names_rail": "exp_task_rail",
	"karsk.tunnels.names_lev": "lev_siding"}
const SFX := ["mg_c4_lever_pull", "mg_c4_lever_back", "mg_c4_lever_locked", "mg_c4_route_set"]
## The annex mini-game „Die Lüftungsklappen“ (round-9 fix compl-01; C4_DESIGN §6: one mini-game per level).
const VentLogic := preload("res://scripts/ui/minigames/vent_logic.gd")
const VentGame := preload("res://scripts/ui/minigames/vent_game.gd")
const VENT_SCENE := "res://scenes/ui/minigames/VentFlaps.tscn"
const VENT_GAME := "res://scripts/ui/minigames/vent_game.gd"
const VENT_SFX := ["mg_c4_flap_open", "mg_c4_flap_close", "mg_c4_alarm_bell", "mg_c4_air_settled"]
## explore id -> its mini-game scene (one per level file)
const MINIGAMES := {"karsk.tunnels.lever_frame": "res://scenes/ui/minigames/LeverFrame.tscn",
	"berlin.annex.fans": "res://scenes/ui/minigames/VentFlaps.tscn"}
## The drivers' exploration passes in Chapter 4 (scripts/core/autoplay.gd EXPLORE_AT / FINAL_PASS): before which
## objective, in which Story scene and level file.
const PASSES := [["c4a_inspect_shelf", "L_C4_TunnelsA"], ["c4a_open_door", "L_C4_TunnelsA"],
	["c4b_inspect_notice", "L_C4_AnnexA"], ["c4b_inspect_crates", "L_C4_AnnexA"],
	["c4c_inspect_card", "L_C4_TunnelsB"], ["c4c_talk_lev", "L_C4_TunnelsB"],
	["c4d_inspect_drawer", "L_C4_AnnexB"], ["c4d_choose", "L_C4_AnnexB"]]
const C4_ROUTE := [["c4a_inspect_shelf", "inspect"], ["c4a_talk_lev", "dialogue"], ["c4a_inspect_book", "inspect"],
	["c4a_inspect_carbon", "inspect"], ["c4a_talk_tunnel", "dialogue"], ["c4a_open_door", "inspect"],
	["c4b_inspect_notice", "inspect"], ["c4b_talk_marta", "dialogue"], ["c4b_solve_routes", "puzzle"],
	["c4b_inspect_column", "inspect"], ["c4b_talk_ilse", "dialogue"], ["c4b_inspect_crates", "inspect"],
	["c4c_inspect_card", "inspect"], ["c4c_inspect_stencils", "inspect"], ["c4c_solve_numbers", "puzzle"],
	["c4c_inspect_wagon", "inspect"], ["c4c_talk_lev", "dialogue"], ["c4d_inspect_drawer", "inspect"],
	["c4d_inspect_plan", "inspect"], ["c4d_inspect_tube", "inspect"], ["c4d_talk_registrar", "dialogue"],
	["c4d_choose", "choice"]]

var kit: Kit
var loc: Node
var real: Node                     # a private Explore instance with the real data
var data: Dictionary = {}          # file -> parsed
var entries: Dictionary = {}       # id -> entry (my files)
var cards: Dictionary = {}         # id -> card (my files)
var strings: Dictionary = {}       # my locale strings
var nodes: Dictionary = {}         # level key -> [{name, script, props}]
var hotspots: Dictionary = {}      # level key -> merged hotspots
var manifests: Dictionary = {}     # level key -> scene.json
var xinfo: Dictionary = {}         # level key -> explore_hotspots.json info


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


## Stands in for a StoryNPC beside a chat spot (lever_spot.npc_present()).
class FakeNpc extends Node2D:
	var char_id := ""
	var present := true

	func is_present() -> bool:
		return present


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var settings: Node = Kit.root().get_node_or_null("Settings")
	var saved := {}
	if settings != null:
		for k in ["puzzle_hints", "text_scale", "high_contrast", "reduced_motion"]:
			saved[k] = settings.values.get(k)
		settings.values["puzzle_hints"] = 1
		settings.values["text_scale"] = 1.0
		settings.values["high_contrast"] = false
		settings.values["reduced_motion"] = false
	kit.run_case("data_files_ids_and_texts", _data)
	kit.run_case("history_cards", _history)
	kit.run_case("explore_validation_of_the_real_data", _validation)
	kit.run_case("placement_hotspots_and_spacing", _placement)
	kit.run_case("gates_follow_the_scene_of_every_find", _gates)
	kit.run_case("spot_memory_and_npc_presence", _spot_live)
	kit.run_case("side_task_doll", _task)
	kit.run_case("side_task_fourteen", _task_fourteen)
	kit.run_case("drivers_loop_on_the_parsed_levels", _drivers)
	kit.run_case("real_game_path_every_pass", _real_path)
	kit.run_case("memory_cards_count_the_level_file", _memory_counts)
	kit.run_case("lever_logic", _logic)
	kit.run_case("lever_scene_auto_keys_hints_cancel", _scene_keys)
	kit.run_case("lever_scene_full_solve_by_keys", _scene_full)
	if settings != null:
		kit.run_case("lever_compact_layout_and_contrast", _compact.bind(settings))
		kit.run_case("lever_hint_setting_modes", _hint_modes.bind(settings))
	kit.run_case("lever_art_layout_sounds_and_task_image", _assets)
	kit.run_case("vent_logic_one_balance_no_dead_end", _vent_logic)
	kit.run_case("vent_scene_auto_keys_mouse_hints_cancel", _vent_scene)
	kit.run_case("vent_scene_full_solve_by_keys", _vent_full)
	if settings != null:
		kit.run_case("vent_compact_contrast_and_hint_modes", _vent_compact.bind(settings))
	kit.run_case("vent_sounds_placement_and_texts", _vent_assets)
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


func _scene_of(id: String) -> String:
	return str(entries.get(id, {}).get("scene", ""))


# ================================================================ data
func _data() -> bool:
	for f in FILES:
		var d = _json("res://data/explore/" + f)
		if kit.ok(d is Dictionary, "%s parses" % f):
			data[f] = d
	var lf = _json(LOCALE)
	if kit.ok(lf is Dictionary and lf.get("strings") is Dictionary, "de_explore_c4.json parses"):
		strings = (lf["strings"] as Dictionary).duplicate()
	var hf = _json(HISTORY_LOCALE)
	if kit.ok(hf is Dictionary and hf.get("strings") is Dictionary, "de_history_c4.json parses"):
		strings.merge(hf["strings"])
	for f in data:
		for e in data[f].get("entries", []):
			kit.ok(not entries.has(str(e.get("id", ""))), "entry %s defined once" % e.get("id"))
			var ee: Dictionary = (e as Dictionary).duplicate(true)
			ee["_area"] = str(e.get("area", data[f].get("area", "")))
			entries[str(e.get("id", ""))] = ee
		for c in data[f].get("cards", []):
			cards[str(c.get("id", ""))] = c
	var per := {}
	for id in entries:
		var e: Dictionary = entries[id]
		var lvl := str(e.get("level", ""))
		if not kit.ok(LEVELS.has(lvl), "%s: level %s is a C4 level key %s" % [id, lvl, LEVELS.keys()]):
			continue
		var spec: Dictionary = LEVELS[lvl]
		kit.ok(str(id).begins_with(spec["prefix"]), "%s: id follows %s<name>" % [id, spec["prefix"]])
		kit.eq(str(e["_area"]), str(spec["area"]), "%s: area %s" % [id, spec["area"]])
		var sc := str(e.get("scene", ""))
		if not kit.ok(sc in spec["scenes"], "%s: scene %s is one of %s" % [id, sc, spec["scenes"]]):
			continue
		per[sc] = int(per.get(sc, 0)) + 1
		kit.ok(str(e.get("kind")) in ["detail", "secret", "easter_egg", "chat"], "%s: kind %s" % [id, e.get("kind")])
		for k in ["title_key", "prompt_key", "text_key"]:
			var key := str(e.get(k, ""))
			if kit.ok(loc.has(key) and loc.t(key).strip_edges() != "", "%s: %s %s has German text" % [id, k, key]):
				kit.ok(loc.source_of(key).ends_with("de_explore_c4.json"), "%s comes from de_explore_c4.json" % key)
		kit.ok(loc.t(str(e.get("title_key"))).length() <= 32, "%s: title at most 32 characters" % id)
		kit.ok(loc.t(str(e.get("prompt_key"))).length() <= 32, "%s: prompt at most 32 characters" % id)
		var tl: int = loc.t(str(e.get("text_key"))).length()
		kit.ok(tl <= (420 if str(e.get("kind")) != "chat" else 260), "%s: text length %d" % [id, tl])
		if e.has("image"):
			kit.ok(ResourceLoader.exists(str(e["image"])), "%s: image %s exists" % [id, e["image"]])
		kit.eq(str(e.get("minigame", "")), str(MINIGAMES.get(id, "")), "%s: the mini-game scene (one per level)" % id)
		if str(e.get("kind")) == "chat":
			var lines: Array = e.get("lines", [])
			kit.ok(lines.size() >= 4 and lines.size() <= 9, "%s: 4-9 lines (%d)" % [id, lines.size()])
			var speakers := {}
			for l in lines:
				var sp := str(l.get("speaker", ""))
				speakers[sp] = true
				if not (sp in NEW_CAST):
					kit.ok(DirAccess.dir_exists_absolute("res://assets/characters/" + sp), "%s: speaker %s has a character folder" % [id, sp])
				kit.ok(loc.has("char.%s.name" % sp), "%s: speaker %s has a German name" % [id, sp])
				kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression %s" % [id, l.get("expr")])
				kit.ok(loc.has(str(l.get("key", ""))) and loc.t(str(l["key"])).length() <= 200, "%s: line %s resolves (<= 200)" % [id, l.get("key")])
			kit.ok(speakers.has(str(SCENES[sc]["who"])), "%s: %s (who plays %s) speaks" % [id, SCENES[sc]["who"], sc])
			kit.ok(speakers.size() >= 2, "%s: a conversation, not a monologue" % id)
		else:
			kit.ok(not e.has("lines"), "%s: only chats carry lines" % id)
	for sc in SCENES:
		kit.eq(int(per.get(sc, 0)), int(SCENES[sc]["count"]), "%s: entries reached in this scene" % sc)
	# German typography and the rename guard over every string of my locale files
	for k in strings:
		var s := str(strings[k])
		kit.ok(s.strip_edges() != "" and s == s.strip_edges(), "'%s' is not empty and has no stray spaces" % k)
		kit.ok(not s.contains("\""), "'%s': German quotes, not ASCII" % k)
		kit.ok(not s.contains(" - ") and not s.contains("--"), "'%s': dash as ' – '" % k)
		kit.ok(not s.contains("..."), "'%s': ellipsis as '…'" % k)
		kit.ok(s.count("„") == s.count("“") and s.count("‚") == s.count("‘"), "'%s': balanced German quotes" % k)
		kit.ok(not s.contains("'"), "'%s': typographic apostrophe, not ASCII" % k)
	var old: String = load("res://tests/test_rename_guard.gd").old_id().to_lower()
	if kit.ok(old != "", "pre-rename id derivable"):
		var raw := FileAccess.get_file_as_string(LOCALE).to_lower() + FileAccess.get_file_as_string(HISTORY_LOCALE).to_lower()
		for f in FILES:
			raw += FileAccess.get_file_as_string("res://data/explore/" + f).to_lower()
		kit.ok(not raw.contains(old), "texts and data never use the pre-rename name")
	# every key of my locale is used (no orphan text): entries, chats, task, mini-game, places
	var used := {}
	for id in entries:
		for k in ["title_key", "prompt_key", "text_key"]:
			used[str(entries[id][k])] = true
		for l in entries[id].get("lines", []):
			used[str(l["key"])] = true
	for c in cards.values():
		used[str(c["title_key"])] = true
		used[str(c["text_key"])] = true
	for f in data:
		for t in data[f].get("tasks", []):
			used[str(t["title_key"])] = true
			used[str(t["summary_key"])] = true
			for s in t.get("steps", []):
				used[str(s["hint_key"])] = true
	var src := FileAccess.get_file_as_string(GAME)
	for k in strings:
		if str(k).begins_with("mg.lever.") or str(k).begins_with("mg.vent.") or str(k).begins_with("ui.explore.place."):
			continue
		kit.ok(used.has(k), "locale key %s is used" % k)
	for k in ["mg.lever.kicker", "mg.lever.title", "mg.lever.solved", "mg.lever.hint.1", "mg.lever.hint.next"]:
		kit.ok(src.contains("\"%s\"" % k), "the mini-game uses %s" % k)
	for lid in LEVELS:
		kit.ok(loc.has("ui.explore.place." + lid), "place line for %s" % lid)
	return true


func _history() -> bool:
	kit.eq(Kit.sorted(cards.keys()), Kit.sorted(HISTORY_AT.keys()), "four new real-history cards")
	var src: Array = []
	for f in ["c4_history_soviet.json", "c4_history_reich.json"]:
		src.append(str(data.get(f, {}).get("side", "")))
	kit.eq(src, ["soviet", "reich"], "one file per side")
	for cid in HISTORY_AT:
		var c: Dictionary = cards.get(cid, {})
		if not kit.ok(not c.is_empty(), "card %s exists" % cid):
			continue
		kit.eq(str(c.get("side", "")), str(cid).split(".")[1], "%s: side" % cid)
		kit.ok(str(c.get("year", "")).length() == 4, "%s: year" % cid)
		var txt: String = loc.t(str(c.get("text_key", "")))
		kit.ok(txt.length() >= 450 and txt.length() <= 800, "%s: text length %d within 450-800" % [cid, txt.length()])
		kit.ok(loc.source_of(str(c.get("text_key", ""))).ends_with("de_history_c4.json"), "%s: text from de_history_c4.json" % cid)
		kit.ok(not txt.contains("http") and not txt.contains("Quelle") and not txt.contains("Wikipedia"), "%s: no sources on the card" % cid)
		var web := 0
		for s in c.get("sources", []):
			kit.ok(s is Dictionary and str(s.get("label", "")).strip_edges() != "", "%s: every source has a label" % cid)
			var url := str(s.get("url", "")) if s is Dictionary else ""
			kit.ok(url == "" or url.begins_with("https://"), "%s: source url %s" % [cid, url])
			if url != "":
				web += 1
		kit.ok(web >= 3, "%s: at least three web sources (%d)" % [cid, web])
		var at: Dictionary = entries.get(HISTORY_AT[cid], {})
		kit.ok((at.get("history", []) as Array).has(cid), "%s is unlocked by %s" % [cid, HISTORY_AT[cid]])
		kit.eq(str(at.get("kind", "")), "detail", "%s: unlocked by a regular find, never a hidden one" % cid)
	for id in entries:
		if not (id in HISTORY_AT.values()):
			kit.ok((entries[id].get("history", []) as Array).is_empty(), "%s unlocks no card" % id)
	# the topics of earlier cards stay theirs: the new texts are no copies
	for old_key in ["hist.soviet.deportations.text", "hist.soviet.filtration.text", "hist.reich.forced_labor.text", "hist.reich.evictions.text"]:
		if loc.has(old_key):
			for cid in HISTORY_AT:
				kit.ne(loc.t(str(cards.get(cid, {}).get("text_key", ""))), loc.t(old_key), "%s is not %s" % [cid, old_key])
	return true


func _validation() -> bool:
	real = kit.track(load(EXPLORE).new())
	real.print_warnings = false
	real.notify_tasks = false
	real.reload()
	var mine: Array = []
	for w in real.warnings:
		var s := str(w)
		var hit := s.contains("c4_tunnels") or s.contains("c4_annex") or s.contains("c4_history") or s.contains(TASK)
		for id in entries:
			hit = hit or s.contains("'%s'" % id) or s.contains(str(id) + ":")
		for cid in cards:
			hit = hit or s.contains(cid)
		if hit:
			mine.append(s)
	kit.eq(mine, [], "Explore validation: no problem in the Chapter-4 data")
	for id in entries:
		kit.ok(real.has_entry(id), "Explore loaded %s" % id)
	for cid in cards:
		kit.ok(real.has_card(cid), "Explore loaded card %s" % cid)
	for lid in LEVELS:
		kit.eq(real.counts(lid)["total"], int(LEVELS[lid]["total"]) + int(LEVELS[lid].get("extra", 0)),
			"counts(%s) sees every find of the level file" % lid)
	kit.eq(real.tasks_for("L_C4_AnnexA").map(func(t): return str(t["id"])), [TASK, "berlin.task.planspiel"],
		"the annex's side tasks: Ilses Puppe (tram loop) and, since round 13, the data desk (tests/test_c4_terminal.gd)")
	kit.eq(real.tasks_for("L_C4_TunnelsA").map(func(t): return str(t["id"])), [TASK2], "the tunnels' one side task")
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


func _ids_of(n: Dictionary) -> Array:
	var chain: Array = Array(n["props"].get("explore_chain", PackedStringArray()))
	return chain if not chain.is_empty() else [str(n["props"].get("explore_id", ""))]


func _load_levels() -> void:
	if not nodes.is_empty():
		return
	for lid in LEVELS:
		var spec: Dictionary = LEVELS[lid]
		var ps = load(str(spec["path"]))
		if not (ps is PackedScene):
			continue
		nodes[lid] = _nodes_of(ps)
		var env := "res://assets/environments/%s/" % spec["env"]
		var man = _json(env + "scene.json")
		manifests[lid] = man if man is Dictionary else {}
		var hs := {}
		var x = _json(env + "explore_hotspots.json")
		if x is Dictionary and x.get("hotspots") is Dictionary:
			hs.merge(x["hotspots"], true)
			xinfo[lid] = x.get("info", {})
		if manifests[lid].get("hotspots") is Dictionary:
			hs.merge(manifests[lid]["hotspots"], true)        # scene.json wins (Level._merge_explore_hotspots)
		hotspots[lid] = hs


func _placement() -> bool:
	_load_levels()
	for lid in LEVELS:
		kit.ok(nodes.has(lid), "%s loads" % LEVELS[lid]["path"])
	var count := {}
	for lid in nodes:
		var spec: Dictionary = LEVELS[lid]
		var walk := PackedVector2Array()
		for q in manifests[lid].get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		var blockers: Array = []
		for b in manifests[lid].get("blockers", []):
			var r: Array = b.get("rect", []) if b is Dictionary else []
			if r.size() == 4:
				blockers.append(Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])))
		var finds := _explore_nodes(lid)
		kit.ok(finds.size() >= int(spec["total"]) - 2, "%s: exploration nodes placed (%d)" % [lid, finds.size()])
		for n in finds:
			var p: Dictionary = n["props"]
			var who := "%s/%s" % [lid, n["name"]]
			var ids := _ids_of(n)
			for id in ids:
				count[str(id)] = (count.get(str(id), []) as Array) + [who]
				if kit.ok(entries.has(str(id)), "%s: entry %s exists" % [who, id]):
					kit.eq(str(entries[str(id)]["level"]), lid, "%s: %s belongs to this level key" % [who, id])
			var first := str(p.get("explore_id", ""))
			if entries.has(first):
				kit.eq(str(p.get("kind")), "chat" if str(entries[first]["kind"]) == "chat" else "discover", "%s: node kind matches %s" % [who, first])
			if ids.size() > 1:
				var fresh := MockEx.new()
				for id in entries:
					fresh.req[id] = entries[id].get("requires", [])
				kit.eq(first, INTERACTABLE.pick_chain_step(PackedStringArray(ids), fresh), "%s: explore_id is the chain's entry in a new game" % who)
				var sc0 := _scene_of(str(ids[0]))
				for id in ids:
					kit.eq(_scene_of(str(id)), sc0, "%s: every entry of the chain plays in %s" % [who, sc0])
			kit.ok(bool(p.get("once", false)), "%s: once" % who)
			var hid := str(p.get("hotspot_id", ""))
			var pos := _pos(lid, hid)
			if not kit.ok(pos.is_finite(), "%s: hotspot %s resolves" % [who, hid]):
				continue
			if walk.size() >= 3:
				kit.ok(Geometry2D.is_point_in_polygon(pos, walk), "%s at %s lies in the walk band" % [who, pos])
			for b in blockers:
				kit.ok(pos.x < (b as Rect2).position.x - 6.0 or pos.x > (b as Rect2).end.x + 6.0, "%s keeps clear of the blocker %s" % [who, b])
			var sc := _scene_of(first)
			if SCENES.has(sc):
				var xr: Array = SCENES[sc]["x"]
				kit.ok(pos.x >= float(xr[0]) and pos.x <= float(xr[1]), "%s (x %d) lies in the walk area of %s %s" % [who, int(pos.x), sc, xr])
			var on_npc: bool = str(p.get("kind")) == "chat" and hid in spec["npcs"]
			if str(p.get("kind")) == "chat":
				kit.ok(on_npc, "%s: a chat stands on an NPC's spot" % who)
			for s in spec["story"] + spec["npcs"]:
				if on_npc and str(s) == hid:
					continue
				var sp := _pos(lid, str(s))
				if sp.is_finite():
					kit.ok(pos.distance_to(sp) >= GAP_STORY, "%s keeps %d px from %s (%.1f)" % [who, int(GAP_STORY), s, pos.distance_to(sp)])
			if on_npc:
				var npc := str(p.get("npc_id", ""))
				kit.ok(npc != "", "%s: a chat on an NPC anchor turns that NPC" % who)
				for id in ids:
					var sps: Array = (entries.get(str(id), {}).get("lines", []) as Array).map(func(l): return str(l.get("speaker", "")))
					kit.ok(npc in sps, "%s: npc %s speaks in %s" % [who, npc, id])
			else:
				var inf: Dictionary = (xinfo.get(lid, {}) as Dictionary).get(hid, {})
				if kit.ok(not inf.is_empty(), "%s: %s has an art-contract entry (info)" % [who, hid]):
					var fc: Array = inf.get("focus", [])
					kit.ok(fc.size() == 2 and absf(float(fc[0]) - pos.x) <= 48.0 and float(fc[1]) < 300.0, "%s: focus %s painted near the spot" % [who, fc])
					kit.ok(str(inf.get("what", "")).length() >= 20, "%s: the art contract says what to paint" % who)
			for o in finds:
				var op := _pos(lid, str(o["props"].get("hotspot_id", "")))
				if o["name"] == n["name"] or not op.is_finite() or str(o["props"].get("hotspot_id")) == hid:
					continue
				kit.ok(pos.distance_to(op) >= GAP_FIND, "%s keeps %d px from %s (%.1f)" % [who, int(GAP_FIND), o["name"], pos.distance_to(op)])
		# spawns: a find never stands on an entry point
		for spn in manifests[lid].get("spawns", {}):
			var sv = manifests[lid]["spawns"][spn]
			var spp := Vector2(float(sv[0]), float(sv[1]))
			for n in finds:
				var pp := _pos(lid, str(n["props"].get("hotspot_id", "")))
				if pp.is_finite():
					kit.ok(pp.distance_to(spp) >= 20.0, "%s keeps clear of the spawn %s" % [n["name"], spn])
	for id in entries:
		kit.eq((count.get(id, []) as Array).size(), 1, "%s placed exactly once %s" % [id, count.get(id, [])])
	# the explore stream's own hotspots: only exp_* names, never a story name of §4
	for lid in LEVELS:
		var x = _json("res://assets/environments/%s/explore_hotspots.json" % LEVELS[lid]["env"])
		for h in (x.get("hotspots", {}) if x is Dictionary else {}):
			kit.ok(str(h).begins_with("exp_"), "%s: explore hotspot %s is an exp_* name" % [lid, h])
			kit.ok(not (h in LEVELS[lid]["story"]), "%s: %s is no story name" % [lid, h])
	return true


# ================================================================ gates
func _gates() -> bool:
	_load_levels()
	var quests = _json("res://data/v3/quests.json")
	var known := {}
	for q in (quests.get("quests", []) if quests is Dictionary else []):
		for o in q.get("objectives", []):
			known[str(o.get("id", ""))] = true
	for lid in nodes:
		for n in _explore_nodes(lid):
			var p: Dictionary = n["props"]
			var who := "%s/%s" % [lid, n["name"]]
			kit.eq(n["script"], SPOT, "%s: the C4 spot script (memory-aware gates, NPC presence)" % who)
			var sc := _scene_of(str(_ids_of(n)[0]))
			if not SCENES.has(sc):
				continue
			var spec: Dictionary = SCENES[sc]
			var after: String = str(spec["after"])
			var until: String = str(spec["until"])
			if str(p.get("kind")) == "chat" and spec.has("chat_after"):
				after = str(spec["chat_after"])
			if str(p.get("kind")) == "chat" and spec.has("chat_until"):
				until = str(spec["chat_until"])
			kit.eq([str(p.get("after_objective", "")), str(p.get("until_objective", ""))], [after, until],
				"%s: open in %s (after / until)" % [who, sc])
			kit.eq(Array(p.get("memory_scenes", PackedStringArray())), [sc], "%s: remembered in %s" % [who, sc])
			for g in [str(p.get("after_objective", "")), str(p.get("until_objective", ""))]:
				if g != "":
					kit.ok(known.has(g), "%s: gate %s is a Story objective" % [who, g])
	return true


## Live: lever_spot follows the remembered scene inside a memory and hides a chat whose NPC is absent.
func _spot_live() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if game == null or ex == null or not ("memory_mode" in game):
		print("      note: autoloads missing, live spot check skipped")
		return true
	var before: Dictionary = ex.state()
	ex.restore({"found": [], "cards": []})
	var holder := Node2D.new()
	kit.mount(holder)
	var a_spot: Node = load(SPOT).new()
	a_spot.kind = "discover"
	a_spot.explore_id = "karsk.tunnels.samovar"
	a_spot.once = true
	a_spot.until_objective = "c4a_open_door"
	a_spot.memory_scenes = PackedStringArray(["L_C4_TunnelsA"])
	holder.add_child(a_spot)
	var c_spot: Node = load(SPOT).new()
	c_spot.kind = "discover"
	c_spot.explore_id = "karsk.tunnels.lever_frame"
	c_spot.once = true
	c_spot.after_objective = "c4a_open_door"
	c_spot.memory_scenes = PackedStringArray(["L_C4_TunnelsB"])
	holder.add_child(c_spot)
	var chat: Node = load(SPOT).new()
	chat.kind = "chat"
	chat.explore_id = "karsk.tunnels.chat_lev"
	chat.npc_id = "lev"
	chat.once = true
	chat.after_objective = "c4a_talk_tunnel"
	chat.until_objective = "c4a_open_door"
	chat.memory_scenes = PackedStringArray(["L_C4_TunnelsA"])
	chat.position = Vector2(428, 300)
	holder.add_child(chat)
	var lev := FakeNpc.new()
	lev.char_id = "lev"
	lev.position = Vector2(446, 300)
	holder.add_child(lev)
	var far := FakeNpc.new()             # Lev at the siding: same character, far away -- not this chat's NPC
	far.char_id = "lev"
	far.position = Vector2(1790, 300)
	holder.add_child(far)
	var mm = game.memory_mode
	var ms = game.memory_scene
	game.memory_mode = true
	game.memory_scene = "L_C4_TunnelsA"
	var in_a := [a_spot.is_active(), c_spot.is_active(), chat.is_active()]
	lev.present = false
	var gone: bool = chat.is_active()
	far.present = false
	lev.present = true
	var back: bool = chat.is_active()
	game.memory_scene = "L_C4_TunnelsB"
	var in_c := [a_spot.is_active(), c_spot.is_active(), chat.is_active()]
	game.memory_scene = "L_C4_AnnexA"
	var in_b := [a_spot.is_active(), c_spot.is_active(), chat.is_active()]
	holder.remove_child(lev)
	holder.remove_child(far)
	game.memory_scene = "L_C4_TunnelsA"
	var no_npc: bool = chat.is_active()
	lev.free()
	far.free()
	game.memory_mode = mm
	game.memory_scene = ms
	kit.eq(in_a, [true, false, true], "memory of the cellar: the cellar's finds and Lev's chat, not the siding")
	kit.ok(not gone, "an absent Lev (StoryNPC hidden) has no chat")
	kit.ok(back, "Lev at his desk again: the chat is back, whoever stands at the siding")
	kit.eq(in_c, [false, true, false], "memory of the siding: the siding's finds (the lever frame) only")
	kit.eq(in_b, [false, false, false], "memory of another level's scene: nothing here")
	kit.ok(no_npc, "without any NPC node (tests, harness) a chat is not blocked")
	ex.restore(before)
	return true


# ================================================================ side task
func _task() -> bool:
	if real == null:
		return true
	var t: Dictionary = real.task(TASK)
	if not kit.ok(not t.is_empty(), "task %s exists" % TASK):
		return true
	kit.eq(str(t.get("level", "")), "L_C4_AnnexA", "task level key")
	kit.eq(real.task_steps(TASK), TASK_STEPS, "Marta asks -> the cellar breakthrough, the doll -> back to the tram")
	for k in ["title_key", "summary_key"]:
		kit.ok(loc.has(str(t.get(k, ""))) and loc.source_of(str(t[k])).ends_with("de_explore_c4.json"), "%s has text in de_explore_c4.json" % k)
	kit.ok(loc.t(str(t["title_key"])).length() <= 32, "task title at most 32 characters")
	kit.ok(loc.t(str(t["summary_key"])).length() <= 200, "task summary at most 200 characters")
	for s in t.get("steps", []):
		kit.ok(loc.has(str(s.get("hint_key", ""))) and loc.t(str(s["hint_key"])).length() <= 120, "hint %s resolves (<= 120)" % s.get("hint_key"))
	kit.eq(real.requires_of(TASK_STEPS[0]), ["berlin.annex.chat_marta"], "the task starts after Marta's chat")
	for i in range(1, TASK_STEPS.size()):
		kit.eq(real.requires_of(TASK_STEPS[i]), [TASK_STEPS[i - 1]], "%s requires the step before" % TASK_STEPS[i])
	for id in TASK_STEPS:
		kit.eq(_scene_of(id), "L_C4_AnnexA", "%s: every step in one walk area (the loop)" % id)
	kit.ok(loc.has("ui.tasks.place.L_C4_AnnexA"), "the journal names the task's place")
	real.restore({"found": [], "cards": []})
	kit.eq(str(real.task_state(TASK)["state"]), "not_started", "not started in a new game")
	kit.ok(not real.can_find(TASK_STEPS[0]), "the task waits for Marta's chat")
	real.find("berlin.annex.chat_marta")
	for i in TASK_STEPS.size():
		var r: Dictionary = real.find(TASK_STEPS[i])
		kit.ok(bool(r.get("ok", false)) and bool(r.get("new", false)), "step %s found in order" % TASK_STEPS[i])
		kit.eq(str(real.task_state(TASK)["state"]), "done" if i == TASK_STEPS.size() - 1 else "active", "state after %s" % TASK_STEPS[i])
	kit.eq((real.task(TASK).get("reward_cards", []) as Array), [], "the reward is a human beat, no history card")
	real.restore({"found": [], "cards": []})
	return true


## „Wir sind vierzehn“ (round-9 fix compl-02): data, placement on wagon 24 318, the hand-in on Lev's spot (offered
## before his story talk when both are open), the state machine, and on the real level the player's focus rule.
func _task_fourteen() -> bool:
	if real == null:
		return true
	var t: Dictionary = real.task(TASK2)
	if not kit.ok(not t.is_empty(), "task %s exists" % TASK2):
		return true
	kit.eq(str(t.get("level", "")), "L_C4_TunnelsA", "task level key (the tunnels' file)")
	kit.eq(real.task_steps(TASK2), TASK2_STEPS, "roof beam -> stove pipe -> bench -> door rail -> Lev")
	for k in ["title_key", "summary_key"]:
		kit.ok(loc.has(str(t.get(k, ""))) and loc.source_of(str(t[k])).ends_with("de_explore_c4.json"), "%s has text in de_explore_c4.json" % k)
	kit.eq(loc.t(str(t["title_key"])), "Wir sind vierzehn", "the task's title (C4_DESIGN §6)")
	kit.ok(loc.t(str(t["summary_key"])).length() <= 200, "task summary at most 200 characters")
	for s in t.get("steps", []):
		kit.ok(loc.has(str(s.get("hint_key", ""))) and loc.t(str(s["hint_key"])).length() <= 120, "hint %s resolves (<= 120)" % s.get("hint_key"))
	kit.eq(real.requires_of(TASK2_STEPS[0]), [], "the first name can be read as soon as the siding is open")
	for i in range(1, TASK2_STEPS.size()):
		kit.eq(real.requires_of(TASK2_STEPS[i]), [TASK2_STEPS[i - 1]], "%s requires the step before" % TASK2_STEPS[i])
	for id in TASK2_STEPS:
		kit.eq(_scene_of(id), "L_C4_TunnelsB", "%s: every step in one walk area (the siding, scene C)" % id)
	var hand_in: Dictionary = entries.get(TASK2_STEPS[TASK2_STEPS.size() - 1], {})
	kit.eq(str(hand_in.get("kind", "")), "chat", "the last step is a chat with Lev")
	var lines: Array = hand_in.get("lines", [])
	if kit.ok(not lines.is_empty(), "the hand-in has lines"):
		var last: Dictionary = lines[lines.size() - 1]
		kit.eq(str(last.get("speaker", "")), "lev", "Lev has the last word")
		kit.ok(loc.t(str(last.get("key", ""))).ends_with("Vierzehn. Jetzt stehen sie in zwei Papieren."), "„Vierzehn. Jetzt stehen sie in zwei Papieren.“")
	# placement: four detail spots along the wagon (x 1550-1740), the hand-in on Lev's spot before his story talk
	_load_levels()
	var ns: Array = nodes.get("L_C4_TunnelsA", [])
	var names: Array = ns.map(func(n): return str(n["name"]))
	for id in TASK2_STEPS:
		var hit: Array = ns.filter(func(n): return str(n["props"].get("explore_id", "")) == id)
		if not kit.ok(hit.size() == 1, "%s has one node" % id):
			continue
		var p: Dictionary = hit[0]["props"]
		kit.eq(str(p.get("hotspot_id", "")), str(TASK2_SPOTS[id]), "%s stands at %s" % [id, TASK2_SPOTS[id]])
		var pos := _pos("L_C4_TunnelsA", str(TASK2_SPOTS[id]))
		if id != TASK2_STEPS[TASK2_STEPS.size() - 1]:
			kit.ok(str(hit[0]["name"]).begins_with("Task_"), "%s: a Task_* node" % id)
			kit.ok(pos.x >= 1550.0 and pos.x <= 1740.0, "%s (x %d) lies along wagon 24 318" % [id, int(pos.x)])
			for s in ["wagon_side", "wagon_door", "lev_siding"]:
				kit.ok(pos.distance_to(_pos("L_C4_TunnelsA", s)) >= GAP_STORY, "%s keeps %d px from %s" % [id, int(GAP_STORY), s])
		else:
			kit.eq([str(p.get("kind")), str(p.get("npc_id")), str(p.get("until_objective"))], ["chat", "lev", "c4c_talk_lev"],
				"the hand-in: a chat with Lev, open until his story talk")
			kit.ok(names.find(str(hit[0]["name"])) < names.find("S_c4c_talk_lev"),
				"%s precedes S_c4c_talk_lev in the level file (a ready hand-in is offered first)" % hit[0]["name"])
	# the state machine on the real data
	real.restore({"found": [], "cards": []})
	kit.eq(str(real.task_state(TASK2)["state"]), "not_started", "not started in a new game")
	kit.ok(real.can_find(TASK2_STEPS[0]) and not real.can_find(TASK2_STEPS[1]), "only the first name is findable at first")
	for i in TASK2_STEPS.size():
		var r: Dictionary = real.find(TASK2_STEPS[i])
		kit.ok(bool(r.get("ok", false)) and bool(r.get("new", false)), "step %s found in order" % TASK2_STEPS[i])
		kit.eq(str(real.task_state(TASK2)["state"]), "done" if i == TASK2_STEPS.size() - 1 else "active", "state after %s" % TASK2_STEPS[i])
	kit.eq((real.task(TASK2).get("reward_cards", []) as Array), [], "the reward is a human beat, no history card")
	real.restore({"found": [], "cards": []})
	_hand_in_focus()
	return true


## The player's focus rule (scripts/actors/player.gd _update_focus: nearest active interactable in range, the first
## of equally near ones in tree order) on the real level: Lev's story talk open, the four names read -- the hand-in
## comes first; once it is done the story talk is the focus again.
func _hand_in_focus() -> void:
	var st: Node = Kit.root().get_node_or_null("Story")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	var game: Node = Kit.root().get_node_or_null("Game")
	if st == null or ex == null or game == null:
		print("      note: autoloads missing, hand-in focus check skipped")
		return
	var keep := {"story": st.save_json(), "explore": ex.state(), "notify": ex.notify_tasks, "mm": game.memory_mode}
	ex.notify_tasks = false
	game.memory_mode = false
	_story_to(st, "c4c_talk_lev")
	ex.restore({"found": TASK2_STEPS.slice(0, 4), "cards": []})
	var lvl := _mount_level(str(LEVELS["L_C4_TunnelsA"]["path"]), "L_C4_TunnelsB")
	var chat: Node = null
	var talk: Node = null
	for it in _level_spots(lvl):
		if str(it.name) == "ChatLevSiding":
			chat = it
		elif str(it.name) == "S_c4c_talk_lev":
			talk = it
	if kit.ok(chat != null and talk != null, "the hand-in and Lev's story talk are in the level"):
		kit.ok(talk.is_active(), "Lev's story talk is open (c4c_inspect_wagon done)")
		kit.ok(chat.is_active(), "the hand-in is open too (four names read, Lev at the siding)")
		var at: Vector2 = (chat as Node2D).global_position + Vector2(-10, 0)
		kit.eq(_focus_at(lvl, at), chat, "standing at Lev: the hand-in is the focus first")
		chat.used = true
		ex.find(str(chat.explore_id))
		kit.eq(_focus_at(lvl, at), talk, "after the hand-in: Lev's story talk")
		kit.eq(str(ex.task_state(TASK2)["state"]), "done", "the task is done")
	_unmount_level(lvl)
	game.memory_mode = keep["mm"]
	if not st.load_json(str(keep["story"])).get("ok", false):
		st.new_game()
	ex.restore(keep["explore"])
	ex.notify_tasks = keep["notify"]


func _focus_at(lvl: Node, at: Vector2) -> Node:
	var best: Node = null
	var best_d := 1e9
	for it in Kit.tree().get_nodes_in_group("interactables"):
		if not is_instance_valid(it) or not lvl.is_ancestor_of(it) or not it.is_inside_tree() or not it.is_active():
			continue
		var d: float = ((it as Node2D).global_position - at).length()
		if d <= float(it.radius) and d < best_d:
			best_d = d
			best = it
	return best


## Objectives complete before the pass that runs before `oid` (all C4 objectives up to it, exclusive).
static func _done_before(oid: String) -> Dictionary:
	var done := {}
	for s in C4_ROUTE:
		if str(s[0]) == oid:
			break
		done[str(s[0])] = true
	return done


## The drivers' loop on parsed nodes (MockEx), gates as in the drivers' passes.
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


func _drivers() -> bool:
	_load_levels()
	var m := MockEx.new()
	for id in entries:
		m.req[id] = entries[id].get("requires", [])
	var first_seen := {}
	for ps in PASSES:
		var lid: String = "L_C4_TunnelsA" if str(ps[1]).begins_with("L_C4_Tunnels") else "L_C4_AnnexA"
		var order := _drive(_explore_nodes(lid), m, _done_before(str(ps[0])))
		for id in order:
			first_seen[id] = str(ps[1])
		if str(ps[0]) == "c4b_inspect_crates":
			kit.eq(order.filter(func(x): return x in TASK_STEPS), TASK_STEPS, "before the crates: the drivers' loop completes „Ilses Puppe“ in step order")
		if str(ps[0]) == "c4c_inspect_card":
			kit.eq(order.filter(func(x): return x in TASK2_STEPS), TASK2_STEPS, "at the siding's first pass: the drivers' loop completes „Wir sind vierzehn“ in step order")
	for id in entries:
		kit.eq(str(first_seen.get(id, "")), _scene_of(id), "%s is reached in its own scene" % id)
	return true


# ================================================================ the real Game path
## Plays the live Story to the pass before `oid` (a new game, the default route through Chapter 3).
func _story_to(st: Node, oid: String) -> void:
	st.new_game()
	kit.play_until(st, "c3g")
	for s in C4_ROUTE:
		if str(s[0]) == oid:
			return
		match str(s[1]):
			"inspect":
				kit.step(st.inspect(str(s[0])), "inspect " + str(s[0]))
			"dialogue":
				kit.play_dialogue(st, str(s[0]))
			"puzzle":
				var pay = Kit.C4_ROUTES.duplicate() if str(s[0]) == "c4b_solve_routes" else Kit.C4_NUMBERS.duplicate()
				kit.step(st.solve_puzzle(str(s[0]), pay), "solve " + str(s[0]))
			"choice":
				kit.step(st.choose(str(s[0]), "protect_marta"), "choose " + str(s[0]))


func _mount_level(path: String, lid: String) -> Node:
	var lvl: Node = (load(path) as PackedScene).instantiate()
	lvl.set("ambience", "")
	lvl.set("music", "")
	lvl.set("level_id", lid)
	Kit.root().add_child(lvl)
	return lvl


func _unmount_level(lvl: Node) -> void:
	if lvl != null and is_instance_valid(lvl):
		lvl.get_parent().remove_child(lvl)
		lvl.free()


func _level_spots(lvl: Node) -> Array:
	var out: Array = []
	for it in Kit.tree().get_nodes_in_group("interactables"):
		if is_instance_valid(it) and lvl.is_ancestor_of(it):
			out.append(it)
	return out


## The drivers' pass on the real nodes: autoplay.pending_finds + what Game._do_discover / _do_chat do with Explore.
func _real_pass(lvl: Node, ex: Node) -> Array:
	var ap: GDScript = load(AUTOPLAY)
	var order: Array = []
	var tried := {}
	var guard := 0
	while guard < 200:
		guard += 1
		var it: Node = null
		for cand in ap.pending_finds(_level_spots(lvl), ex):
			if not tried.has("%d:%s" % [cand.get_instance_id(), cand.explore_id]):
				it = cand
				break
		if it == null:
			break
		var id := str(it.explore_id)
		tried["%d:%s" % [it.get_instance_id(), id]] = true
		it.used = true
		var r: Dictionary = ex.find(id)
		if bool(r.get("ok", false)):
			order.append(id)
	return order


func _real_path() -> bool:
	var st: Node = Kit.root().get_node_or_null("Story")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	var game: Node = Kit.root().get_node_or_null("Game")
	if st == null or ex == null or game == null:
		print("      note: autoloads missing, real-path check skipped")
		return true
	var keep := {"story": st.save_json(), "explore": ex.state(), "notify": ex.notify_tasks, "mm": game.memory_mode,
		"ms": game.memory_scene}
	ex.notify_tasks = false
	game.memory_mode = false
	ex.restore({"found": [], "cards": []})
	var first_seen := {}
	for ps in PASSES:
		var lid: String = "L_C4_TunnelsA" if str(ps[1]).begins_with("L_C4_Tunnels") else "L_C4_AnnexA"
		_story_to(st, str(ps[0]))
		if not kit.ok(st.is_available(str(ps[0])), "the live Story stands before %s" % ps[0]):
			continue
		var lvl := _mount_level(str(LEVELS[lid]["path"]), str(ps[1]))
		var order := _real_pass(lvl, ex)
		for id in order:
			if not first_seen.has(id):
				first_seen[id] = str(ps[1])
		if str(ps[0]) == "c4b_inspect_crates":
			kit.eq(str(ex.task_state(TASK)["state"]), "done", "before the crates, on the real nodes: „Ilses Puppe“ done")
		if str(ps[0]) == "c4d_choose":
			kit.eq(str(ex.task_state(TASK)["state"]), "done", "the annex's final pass finds the task done")
		if str(ps[0]) == "c4c_talk_lev":
			kit.eq(str(ex.task_state(TASK2)["state"]), "done", "the tunnels' final pass finds „Wir sind vierzehn“ done")
		_unmount_level(lvl)
	for id in entries:
		kit.eq(str(first_seen.get(id, "")), _scene_of(id), "real path: %s found in its own scene" % id)
	kit.eq(st.save_json(), st.save_json(), "Story unchanged by exploring (sanity)")
	# a memory of the cellar after the siding: the cellar's finds open, Lev's desk empty -- no chat with nobody
	_story_to(st, "c4d_inspect_drawer")
	var lvl2 := _mount_level(str(LEVELS["L_C4_TunnelsA"]["path"]), "L_C4_TunnelsA")
	game.memory_mode = true
	game.memory_scene = "L_C4_TunnelsA"
	var act_a := {}
	for it in _level_spots(lvl2):
		if str(it.kind) in ["discover", "chat"] and it.is_active():
			act_a[str(it.explore_id)] = true
	game.memory_scene = "L_C4_TunnelsB"
	var act_c := {}
	for it in _level_spots(lvl2):
		if str(it.kind) in ["discover", "chat"] and it.is_active():
			act_c[str(it.explore_id)] = true
	game.memory_mode = false
	_unmount_level(lvl2)
	for id in entries:
		if str(entries[id]["level"]) != "L_C4_TunnelsA" or str(entries[id]["kind"]) == "chat":
			continue
		kit.eq(act_a.has(id), _scene_of(id) == "L_C4_TunnelsA", "memory of the cellar: %s open = %s" % [id, _scene_of(id) == "L_C4_TunnelsA"])
		kit.eq(act_c.has(id), _scene_of(id) == "L_C4_TunnelsB", "memory of the siding: %s open = %s" % [id, _scene_of(id) == "L_C4_TunnelsB"])
	var lev_shown := str(st.objective_state("c4c_inspect_card")) != "complete"
	kit.eq(act_a.has("karsk.tunnels.chat_lev"), lev_shown, "memory of the cellar: Lev's chat only while Lev sits at his desk")
	# restore
	game.memory_mode = keep["mm"]
	game.memory_scene = keep["ms"]
	if not st.load_json(str(keep["story"])).get("ok", false):
		st.new_game()
	ex.restore(keep["explore"])
	ex.notify_tasks = keep["notify"]
	return true


## The memory cards (Game.memory_scenes) count the finds of the scene's level file (ChapterExt.level_key): both
## scenes of a file show the same total -- every find of the file, whichever walk area holds it. With the proposed
## engine patch (game.gd counts only entries whose optional "scene" names the card's scene) each card counts its
## own walk area; the expectation follows whichever game.gd is installed.
func _memory_counts() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game")
	var st: Node = Kit.root().get_node_or_null("Story")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if game == null or st == null or ex == null or not game.has_method("memory_scenes"):
		print("      note: autoloads missing, memory count check skipped")
		return true
	var ext = game.get("ext")
	if ext != null and ext.has_method("level_key"):
		kit.eq(str(ext.level_key("L_C4_TunnelsB")), "L_C4_TunnelsA", "the siding counts under the tunnels' level key")
		kit.eq(str(ext.level_key("L_C4_AnnexB")), "L_C4_AnnexA", "the annex counts under the loop's level key")
	var keep := {"story": st.save_json(), "explore": ex.state(), "notify": ex.notify_tasks}
	ex.notify_tasks = false
	st.new_game()
	kit.play_until(st, "c4d")
	ex.restore({"found": ["karsk.tunnels.samovar", "karsk.tunnels.lever_frame", "berlin.annex.house_11"], "cards": []})
	var got := {}
	for c in game.memory_scenes("game"):
		got[str(c.get("id", ""))] = c
	var per_scene := FileAccess.get_file_as_string("res://scripts/core/game.gd").contains("e.get(\"scene\"")
	var want_scene := {"L_C4_TunnelsA": [1, 8], "L_C4_TunnelsB": [1, 14], "L_C4_AnnexA": [1, 11], "L_C4_AnnexB": [0, 11]}
	for sid in ["L_C4_TunnelsA", "L_C4_TunnelsB", "L_C4_AnnexA", "L_C4_AnnexB"]:
		var c: Dictionary = got.get(sid, {})
		if not kit.ok(not c.is_empty() and bool(c.get("unlocked", false)), "memory card %s is unlocked after Chapter 4" % sid):
			continue
		var tunnels: bool = str(sid).begins_with("L_C4_Tunnels")
		var want: Array = want_scene[sid] if per_scene else ([2, 22] if tunnels else [1, 22])
		kit.eq([int(c.get("found", -1)), int(c.get("total", -1))], want, "memory card %s counts %s" % [sid, "its walk area" if per_scene else "its level file"])
	if not st.load_json(str(keep["story"])).get("ok", false):
		st.new_game()
	ex.restore(keep["explore"])
	ex.notify_tasks = keep["notify"]
	return true


# ================================================================ mini-game: rule
func _logic() -> bool:
	var lg = Logic.new()
	kit.eq(Logic.LEVERS, ["w1", "w2", "w3", "a", "b", "c", "s1", "s2"], "eight levers in frame order")
	kit.eq([lg.is_pulled("w1"), lg.is_pulled("w2"), lg.is_pulled("w3"), lg.is_pulled("a"), lg.is_pulled("s1")],
		[true, true, true, false, false], "the night shift's position: points reversed, no route, signals at danger")
	kit.eq(lg.check("s1")["reason"], "signal_no_route", "a signal needs its route")
	kit.eq([lg.check("a")["reason"], lg.check("a")["by"]], ["route_points", "w1"], "route a needs points 1 normal")
	kit.ok(lg.check("w1")["ok"], "free points move")
	var before: Dictionary = lg.pulled.duplicate()
	var r: Dictionary = lg.toggle("s1")
	kit.ok(not r["ok"] and lg.refusals == 1 and lg.moves == 0, "a refusal counts, moves nothing")
	kit.eq(lg.pulled, before, "a refusal changes no lever")
	lg.toggle("w1")
	lg.toggle("a")
	kit.eq([lg.check("w1")["reason"], lg.check("w1")["by"]], ["points_locked", "a"], "route a holds points 1")
	r = lg.toggle("s1")
	kit.ok(r["ok"] and r["order_done"] and not r["solved"], "order 1 carried out by route a + signal 1")
	kit.ok(not lg.toggle("w2")["ok"], "nothing moves during the beat after an order")
	lg.next_order()
	kit.eq(lg.order, 1, "order 2 follows")
	kit.eq([lg.check("a")["reason"], lg.check("a")["by"]], ["route_held", "s1"], "the signal holds its route")
	lg.toggle("s1")
	lg.toggle("a")
	lg.toggle("w2")
	lg.toggle("w3")
	kit.eq([lg.check("b")["reason"], lg.check("b")["by"]], ["route_points", "w1"], "route b wants points 1 reversed (flank protection)")
	lg.toggle("w1")
	lg.toggle("b")
	kit.eq([lg.check("c")["reason"], lg.check("c")["by"]], ["route_conflict", "b"], "routes b and c exclude each other")
	kit.ok(lg.toggle("s2")["order_done"], "order 2 carried out by route b + signal 2")
	lg.next_order()
	kit.eq(lg.plan(), ["s2", "b", "w3", "c", "s2"], "order 3: signal back, route b off, points 3 over, route c, signal")
	for id in lg.plan():
		r = lg.toggle(str(id))
	kit.ok(r["solved"], "the third order solves the frame")
	lg.next_order()
	kit.ok(lg.done, "done after three orders")
	kit.eq(Logic.solution().map(func(p): return (p as Array).size()), [3, 7, 5], "shortest solution: 3 + 7 + 5 moves")
	# no dead end: from any of the 256 positions every order can still be carried out
	var dead := 0
	for code in 256:
		for o in Logic.ORDERS.size():
			var t = Logic.new()
			t.pulled = Logic._decode(code)
			t.order = o
			if not t.order_met() and t.plan().is_empty():
				dead += 1
	kit.eq(dead, 0, "no position of the frame is a dead end")
	var fresh = Logic.new()
	kit.eq(fresh.next_move(), "w1", "the first move from the night shift's position: points 1")
	kit.eq(Kit.sorted(fresh.locked().keys()), Kit.sorted(["a", "b", "c", "s1", "s2"]), "at the start only the points are free")
	return true


func _scene_keys() -> bool:
	var mg := _instance()
	kit.ok(mg.is_in_group("minigame"), "LeverFrame joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "karsk.tunnels.lever_frame", "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var lf := _instance()
	var res: Array = []
	lf.finished.connect(func(ok: bool): res.append(ok))
	lf.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	_steps(lf, 0.4)
	kit.eq(lf.selected(), "w1", "the cursor starts on lever 1")
	kit.ok(str(lf._lever_label.text).contains("Weiche 1"), "the side panel names the lever")
	kit.ok(str(lf._order_label.text).contains("Gleis 1"), "the side panel reads order 1")
	kit.eq(lf._table.get_child_count(), 20, "the locking table: header + three routes, five columns")
	lf.modal_input(_key(KEY_RIGHT))
	kit.eq(lf.selected(), "w2", "Right moves along the frame")
	lf.modal_input(_key(KEY_7))
	kit.eq(lf.fails, 1, "lever 7 (signal 1) without a route is refused (a failure)")
	kit.ok(str(lf._status.text).contains("klemmt"), "the refusal explains the lock")
	kit.eq([lf.selected(), lf.logic.is_pulled("s1")], ["s1", false], "a number key selects that lever; the signal stays")
	lf.modal_input(_key(KEY_UP))
	kit.ok(lf.fails == 2 and lf._hint_box.visible, "a hint after two refusals")
	kit.ok(str(lf._hint_label.text).contains("Verschlusstafel"), "the first hint: the rule")
	lf.modal_input(_key(KEY_1))
	kit.ok(not lf.logic.is_pulled("w1") and lf.selected() == "w1", "key 1 puts points 1 back (normal)")
	lf.modal_input(_key(KEY_DOWN))
	kit.ok(not lf.logic.is_pulled("w1"), "Down on a lever in normal changes nothing")
	kit.eq(lf.fails, 2, "and is no refusal")
	lf.modal_input(_key(KEY_R))
	kit.ok(lf.logic.is_pulled("w1") and lf.logic.moves == 0, "R starts over from the night shift's position")
	lf.show_hint(2)
	kit.ok(str(lf._hint_label.text).contains("Hebel 1"), "the second hint names the next lever")
	kit.ok(lf.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	return true


func _scene_full() -> bool:
	var lf := _instance()
	var res: Array = []
	lf.finished.connect(func(ok: bool): res.append(ok))
	lf.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	_steps(lf, 0.4)
	var guard := 0
	while not lf.solved and guard < 60:
		guard += 1
		if lf.logic.order_complete:
			_steps(lf, 0.5)
			continue
		var nx: String = lf.logic.next_move()
		var target := Logic.index_of(nx)
		var g2 := 0
		while lf.cursor != target and g2 < 12:
			lf.modal_input(_key(KEY_RIGHT if lf.cursor < target else KEY_LEFT))
			g2 += 1
		lf.modal_input(_key(KEY_E))
		_steps(lf, 0.2)
	kit.ok(lf.solved, "all three orders by keys alone")
	kit.eq(lf.fails, 0, "no refusal on the right path")
	kit.eq(lf.logic.moves, 15, "fifteen lever moves")
	kit.ok(str(lf._status.text).contains("Кордон 17"), "the reveal: track 0 leads to „Кордон 17“")
	_steps(lf, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(lf, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.toggle(") and not body.contains("pull_or_back(") and not body.contains("mark_solved("),
		"demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "LeverFrame extends minigame_base.gd")
	# mouse: a click on a lever toggles it
	var mf := _instance()
	mf.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	_steps(mf, 0.4)
	var xs: Array = mf.layout.get("lever_x", [])
	if kit.ok(xs.size() == 8, "layout: eight lever positions"):
		var mb := InputEventMouseButton.new()
		mb.button_index = MOUSE_BUTTON_LEFT
		mb.pressed = true
		mb.position = Vector2(float(xs[0]), 80.0) * mf.S
		mf.scene_input(mb)
		kit.ok(not mf.logic.is_pulled("w1"), "a click on lever 1 puts points 1 back")
		var mm := InputEventMouseMotion.new()
		mm.position = Vector2(float(xs[3]), 90.0) * mf.S
		mf.scene_input(mm)
		kit.eq(mf.selected(), "a", "pointing at lever 4 selects route a")
	return true


func _compact(settings: Node) -> bool:
	settings.values["text_scale"] = 1.5
	settings.values["high_contrast"] = true
	var lf := _instance()
	lf.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	_steps(lf, 0.4)
	kit.ok(lf.compact and lf.S == 2, "larger text: compact layout, art x2")
	var sz: Array = lf.layout.get("size", [0, 0])
	kit.eq(lf._scene.custom_minimum_size, Vector2(float(sz[0]), float(sz[1])) * 2.0, "the stage shrinks to x2")
	kit.ok(not lf._subtitle.visible, "the flavour subtitle gives way to the text")
	kit.ok(lf._scene.custom_minimum_size.x + 860.0 + 36.0 <= 1800.0, "stage and side panel fit the panel width")
	lf.modal_input(_key(KEY_1))
	lf._scene.queue_redraw()
	kit.ok(not lf.logic.is_pulled("w1"), "high contrast plays the same")
	settings.values["text_scale"] = 1.0
	settings.values["high_contrast"] = false
	var n := _instance()
	n.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	kit.ok(not n.compact and n.S == 3, "default text: art x3")
	kit.ok(n._scene.custom_minimum_size.x + 500.0 + 36.0 <= 1800.0, "x3 stage and side panel fit the panel width")
	kit.ok(n._scene.custom_minimum_size.y <= 450.0, "x3 stage leaves room for header, status, hint and buttons")
	return true


func _hint_modes(settings: Node) -> bool:
	settings.values["puzzle_hints"] = 0
	var a := _instance()
	a.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	_steps(a, 0.4)
	for i in 3:
		a.modal_input(_key(KEY_8))
	kit.ok(a.fails == 3 and not a._hint_box.visible, "puzzle_hints 0: no hint even after three refusals")
	settings.values["puzzle_hints"] = 2
	var b := _instance()
	b.open({"explore_id": "karsk.tunnels.lever_frame", "auto": false})
	kit.ok(b._hint_box.visible, "puzzle_hints 2: the first hint at once")
	settings.values["puzzle_hints"] = 1
	return true


# ================================================================ art, layout, sounds
func _assets() -> bool:
	var lay = _json(ART + "lever_layout.json")
	if not kit.ok(lay is Dictionary, "lever_layout.json parses"):
		return true
	var sizes := {"lever_back": Vector2i(400, 148), "lever_indicator": Vector2i(64 * 3, 9)}
	for n in sizes:
		var p := ART + str(n) + ".png"
		if kit.ok(ResourceLoader.exists(p), "%s imported" % p):
			kit.eq(Vector2i((load(p) as Texture2D).get_size()), sizes[n], "%s size" % n)
	for cl in [ART + "lever_closeup.png", "res://assets/explore/c4/ilse_drawing.png"]:
		if kit.ok(ResourceLoader.exists(cl), "%s imported" % cl):
			var s := (load(cl) as Texture2D).get_size()
			kit.ok(s.x <= 320 and s.y <= 200, "%s fits 320x200 (%s)" % [cl, s])
	kit.eq(lay.get("levers", []), Logic.LEVERS, "the generator's lever order is the rule's")
	var xs: Array = lay.get("lever_x", [])
	kit.eq(xs.size(), 8, "eight lever positions")
	for i in range(1, xs.size()):
		kit.ok(float(xs[i]) - float(xs[i - 1]) >= 32.0, "levers %d and %d stand apart (mouse targets of 32 art px)" % [i, i + 1])
	kit.eq(Kit.sorted((lay.get("routes", {}) as Dictionary).keys()), ["a", "b", "c"], "a lit route for every route lever")
	kit.eq(Kit.sorted((lay.get("branches", {}) as Dictionary).keys()), ["w1", "w2", "w3"], "two branches for every points lever")
	kit.eq(Kit.sorted((lay.get("signals", {}) as Dictionary).keys()), ["s1", "s2"], "a lamp for every signal")
	kit.eq(lay.get("indicator", {}).get("order", []), ["a", "b", "c"], "the indicator cells in route order")
	var hy: Array = lay.get("handle_y", [0, 0])
	var board: Array = lay.get("board", [0, 0, 0, 0])
	kit.ok(float(hy[0]) > float(board[1]) + float(board[3]), "the lever handles stand below the diagram board")
	for r in (lay.get("routes", {}) as Dictionary).values():
		for q in r:
			kit.ok(Rect2(float(board[0]), float(board[1]), float(board[2]), float(board[3])).has_point(Vector2(float(q[0]), float(q[1]))), "route point %s lies on the board" % [q])
	for s in SFX:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % s), "sound %s imported" % s)
	return true


# ================================================================ „Die Lüftungsklappen“ (round-9 fix compl-01)
func _vent_instance() -> Node:
	var mg: Node = load(VENT_SCENE).instantiate()
	Kit.root().add_child(mg)
	kit.track(mg)
	return mg


static func _vent_positions() -> Array:
	var out: Array = []
	for a in VentLogic.MAX_POS + 1:
		for b in VentLogic.MAX_POS + 1:
			for c in VentLogic.MAX_POS + 1:
				out.append({"hall": a, "typing": b, "corridor": c})
	return out


func _vent_logic() -> bool:
	var lg = VentLogic.new()
	kit.eq(VentLogic.FLAPS, ["hall", "typing", "corridor"], "three flaps: card hall, typists' room, corridor")
	kit.eq(VentLogic.solutions(), [VentLogic.SOLUTION], "exactly one of the 125 positions balances all three ducts")
	kit.ok(not lg.balanced(), "the night shift's setting rings the bell")
	kit.eq(lg.states(), {"hall": 0, "typing": 1, "corridor": -1}, "start: card hall right, typists' room too much, corridor none")
	var f0: Dictionary = lg.flows()
	var r: Dictionary = lg.step("corridor", 1)
	var f1: Dictionary = lg.flows()
	kit.ok(bool(r["ok"]) and float(f1["corridor"]) > float(f0["corridor"]) and float(f1["hall"]) < float(f0["hall"])
		and float(f1["typing"]) < float(f0["typing"]), "opening one duct takes air from the other two")
	lg.reset()
	var before: Dictionary = lg.pos.duplicate()
	var e1: Dictionary = lg.step("hall", 1)
	var e2: Dictionary = lg.step("corridor", -1)
	kit.eq([e1["ok"], e1["reason"], e2["ok"], e2["reason"]], [false, "open", false, "closed"], "the end stops refuse")
	kit.eq([lg.pos, lg.moves], [before, 0], "a refusal changes nothing")
	var a: Dictionary = lg.acknowledge()
	kit.eq([a["ok"], a["worst"], a["dir"]], [false, "typing", 1], "acknowledging out of balance names the worst duct")
	kit.ok(not lg.done, "the fault stays")
	kit.eq(float(VentLogic.COND["corridor"]) * 2.0, float(VentLogic.COND["typing"]), "the long corridor duct carries half per step")
	var worst := 0
	var all_ok := true
	for p in _vent_positions():
		lg.reset()
		lg.pos = (p as Dictionary).duplicate()
		var n := 0
		while not lg.next_move().is_empty() and n < 20:
			var nx: Dictionary = lg.next_move()
			if not bool(lg.step(str(nx["flap"]), int(nx["dir"]))["ok"]):
				all_ok = false
				break
			n += 1
		all_ok = all_ok and lg.balanced()
		worst = maxi(worst, n)
	kit.ok(all_ok, "no dead end: every one of the 125 positions reaches the balance")
	kit.ok(worst <= 12, "within twelve flap steps (%d)" % worst)
	lg.reset()
	lg.pos = VentLogic.SOLUTION.duplicate()
	kit.ok(bool(lg.acknowledge()["ok"]) and lg.done, "in balance the fault is acknowledged")
	kit.eq(bool(lg.step("hall", -1)["ok"]), false, "after that the flaps stay")
	return true


func _vent_scene() -> bool:
	var mg := _vent_instance()
	kit.ok(mg.is_in_group("minigame"), "VentFlaps joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "berlin.annex.fans", "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var vf := _vent_instance()
	var res: Array = []
	vf.finished.connect(func(ok: bool): res.append(ok))
	vf.open({"explore_id": "berlin.annex.fans", "auto": false})
	_steps(vf, 0.4)
	kit.eq(vf.selected(), "hall", "the cursor starts on flap 1")
	kit.ok(str(vf._flap_label.text).contains("Kartensaal"), "the side panel names the flap")
	kit.eq(vf._table.get_child_count(), 16, "the sheet: header + three ducts, four columns")
	kit.ok(str(vf._head.text).contains("STÖRUNG"), "the head reads the fault")
	vf.modal_input(_key(KEY_RIGHT))
	kit.eq(vf.selected(), "typing", "Right moves to the next flap")
	vf.modal_input(_key(KEY_E))
	kit.eq(vf.fails, 1, "acknowledging out of balance is refused (a failure)")
	kit.ok(str(vf._status.text).contains("Schreibstube") and str(vf._status.text).contains("zu viel"), "the refusal names the worst duct")
	vf.modal_input(_key(KEY_1))
	vf.modal_input(_key(KEY_UP))
	kit.eq([vf.selected(), vf.logic.moves], ["hall", 0], "flap 1 at its end stop: Up changes nothing")
	kit.eq(vf.fails, 1, "and is no failure")
	vf.modal_input(_key(KEY_ENTER))
	kit.ok(vf.fails == 2 and vf._hint_box.visible, "a hint after two refusals")
	kit.ok(str(vf._hint_label.text).contains("doppelt so lang"), "the first hint: the long corridor duct")
	vf.modal_input(_key(KEY_3))
	vf.modal_input(_key(KEY_UP))
	kit.eq([vf.selected(), int(vf.logic.pos["corridor"])], ["corridor", 1], "key 3 picks the corridor flap, Up opens it a step")
	vf.modal_input(_key(KEY_R))
	kit.ok(int(vf.logic.pos["corridor"]) == 0 and vf.logic.moves == 0, "R starts over from the night shift's setting")
	vf.show_hint(2)
	kit.ok(str(vf._hint_label.text).contains("Klappe 2"), "the second hint names the next flap")
	kit.ok(vf.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	# mouse: above a flap opens, below closes, the wheel turns, pointing selects
	var mf := _vent_instance()
	mf.open({"explore_id": "berlin.annex.fans", "auto": false})
	_steps(mf, 0.4)
	var x3 := float(VentGame.DUCT_X[2])
	var mb := InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = true
	mb.position = Vector2(x3, VentGame.FLAP_Y - 12.0) * mf.S
	mf.scene_input(mb)
	kit.eq([mf.selected(), int(mf.logic.pos["corridor"])], ["corridor", 1], "a click above flap 3 opens it a step")
	var wd := InputEventMouseButton.new()
	wd.button_index = MOUSE_BUTTON_WHEEL_DOWN
	wd.pressed = true
	wd.position = Vector2(x3, VentGame.FLAP_Y + 12.0) * mf.S
	mf.scene_input(wd)
	kit.eq(int(mf.logic.pos["corridor"]), 0, "the wheel down closes it again")
	var mm := InputEventMouseMotion.new()
	mm.position = Vector2(float(VentGame.DUCT_X[1]), 60.0) * mf.S
	mf.scene_input(mm)
	kit.eq(mf.selected(), "typing", "pointing at duct 2 selects its flap")
	var lb := InputEventMouseButton.new()
	lb.button_index = MOUSE_BUTTON_LEFT
	lb.pressed = true
	lb.position = Vector2(float(VentGame.DUCT_X[1]), VentGame.FLAP_Y + 14.0) * mf.S
	mf.scene_input(lb)
	kit.eq(int(mf.logic.pos["typing"]), 3, "a click below flap 2 closes it a step")
	return true


func _vent_full() -> bool:
	var vf := _vent_instance()
	var res: Array = []
	vf.finished.connect(func(ok: bool): res.append(ok))
	vf.open({"explore_id": "berlin.annex.fans", "auto": false})
	_steps(vf, 0.4)
	var guard := 0
	while not vf.solved and guard < 40:
		guard += 1
		var nx: Dictionary = vf.logic.next_move()
		if nx.is_empty():
			vf.modal_input(_key(KEY_E))
			continue
		var target := VentLogic.index_of(str(nx["flap"]))
		var g2 := 0
		while vf.cursor != target and g2 < 6:
			vf.modal_input(_key(KEY_RIGHT if vf.cursor < target else KEY_LEFT))
			g2 += 1
		vf.modal_input(_key(KEY_UP if int(nx["dir"]) > 0 else KEY_DOWN))
		_steps(vf, 0.1)
	kit.ok(vf.solved, "balanced and acknowledged by keys alone")
	kit.eq(vf.fails, 0, "no refusal on the right path")
	kit.eq(vf.logic.moves, 6, "six flap steps from the night shift's setting")
	kit.ok(str(vf._status.text).contains("14 Plätze"), "the reveal: „Gang – Warteraum, 14 Plätze“")
	_steps(vf, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(vf, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(VENT_GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.step(") and not body.contains("move_flap(")
		and not body.contains("acknowledge()") and not body.contains("mark_solved("),
		"demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "VentFlaps extends minigame_base.gd")
	return true


func _vent_compact(settings: Node) -> bool:
	settings.values["text_scale"] = 1.5
	settings.values["high_contrast"] = true
	var vf := _vent_instance()
	vf.open({"explore_id": "berlin.annex.fans", "auto": false})
	_steps(vf, 0.4)
	kit.ok(vf.compact and vf.S == 2, "larger text: compact layout, stage x2")
	kit.eq(vf._scene.custom_minimum_size, VentGame.STAGE * 2.0, "the stage shrinks to x2")
	kit.ok(not vf._subtitle.visible and not vf._instr.visible, "the flavour gives way to the text")
	kit.ok(vf._scene.custom_minimum_size.x + 820.0 + 36.0 <= 1800.0, "stage and side panel fit the panel width")
	vf.modal_input(_key(KEY_3))
	vf.modal_input(_key(KEY_UP))
	vf._scene.queue_redraw()
	kit.eq(int(vf.logic.pos["corridor"]), 1, "high contrast plays the same")
	settings.values["text_scale"] = 1.0
	settings.values["high_contrast"] = false
	var n := _vent_instance()
	n.open({"explore_id": "berlin.annex.fans", "auto": false})
	kit.ok(not n.compact and n.S == 3, "default text: stage x3")
	kit.ok(n._scene.custom_minimum_size.x + 500.0 + 36.0 <= 1800.0, "x3 stage and side panel fit the panel width")
	kit.ok(n._scene.custom_minimum_size.y <= 450.0, "x3 stage leaves room for header, status, hint and buttons")
	settings.values["puzzle_hints"] = 0
	var a := _vent_instance()
	a.open({"explore_id": "berlin.annex.fans", "auto": false})
	_steps(a, 0.4)
	for i in 3:
		a.modal_input(_key(KEY_E))
	kit.ok(a.fails == 3 and not a._hint_box.visible, "puzzle_hints 0: no hint even after three refusals")
	settings.values["puzzle_hints"] = 2
	var b := _vent_instance()
	b.open({"explore_id": "berlin.annex.fans", "auto": false})
	kit.ok(b._hint_box.visible, "puzzle_hints 2: the first hint at once")
	settings.values["puzzle_hints"] = 1
	return true


func _vent_assets() -> bool:
	for s in VENT_SFX:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % s), "sound %s imported" % s)
	var src := FileAccess.get_file_as_string(VENT_GAME)
	for s in VENT_SFX + ["mg_c4_lever_locked"]:
		kit.ok(src.contains("\"%s\"" % s), "the game plays %s" % s)
	kit.eq(str(entries.get("berlin.annex.fans", {}).get("minigame", "")), VENT_SCENE, "the fans find runs the mini-game")
	kit.eq(_scene_of("berlin.annex.fans"), "L_C4_AnnexB", "in the annex (scene D)")
	_load_levels()
	var hit: Array = (nodes.get("L_C4_AnnexA", []) as Array).filter(func(n): return str(n["props"].get("explore_id", "")) == "berlin.annex.fans")
	if kit.ok(hit.size() == 1, "one node for the fans"):
		kit.eq(str(hit[0]["props"].get("hotspot_id", "")), "exp_fans", "at exp_fans")
		kit.eq(_pos("L_C4_AnnexA", "exp_fans"), Vector2(992, 300), "the machine room behind the grille (992, 300)")
	for k in ["mg.vent.kicker", "mg.vent.title", "mg.vent.solved", "mg.vent.hint.1", "mg.vent.hint.next", "mg.vent.btn.ack"]:
		kit.ok(src.contains("\"%s\"" % k), "the mini-game uses %s" % k)
		kit.ok(loc.has(k) and loc.source_of(k).ends_with("de_explore_c4.json"), "%s has German text" % k)
	for f in VentLogic.FLAPS:
		for pre in ["mg.vent.name.", "mg.vent.desc."]:
			kit.ok(loc.has(pre + str(f)), "%s%s has German text" % [pre, f])
	for p in VentLogic.MAX_POS + 1:
		kit.ok(loc.has("mg.vent.pos.%d" % p), "flap position %d is named" % p)
	return true
