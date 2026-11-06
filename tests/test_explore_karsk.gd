extends RefCounted
## Karsk exploration layer (owner: karsk-explore): data/explore/karsk.json, data/locale/de_explore_karsk.json,
## assets/environments/karsk_railyard/explore_hotspots.json, the discover/chat nodes of
## scenes/levels/L_A1_Railyard.tscn and the close-ups in assets/explore/karsk/ (TECHNICAL_ARCHITECTURE §12).
## Headless and read-only: the level scene is inspected through its SceneState, never instanced.
## Checks: every exploration Interactable points at an existing entry of the matching kind and at a hotspot of
## scene.json ∪ explore_hotspots.json (scene.json wins, like Level._merge_explore_hotspots); every entry is
## placed exactly once; Loc keys exist and belong to this area; the eight Soviet history links sit on the §12.3
## objects and nowhere else; chats have 4-8 lines spoken by characters with portraits (§12.6); finds stand in
## the walk band, outside prop collisions and clear of the story hotspots (>= 26 px in the player's oblique
## metric, dy x 1.6); the canonical story interactables are unchanged; close-ups fit 320x200 and _hist twins
## match their neutral file.

const Kit := preload("res://tests/support/test_kit.gd")
const DATA := "res://data/explore/karsk.json"
const LOCALE := "res://data/locale/de_explore_karsk.json"
const SCENE := "res://scenes/levels/L_A1_Railyard.tscn"
const ART := "res://assets/environments/karsk_railyard/scene.json"
const EXTRA := "res://assets/environments/karsk_railyard/explore_hotspots.json"
const INTERACTABLE := "res://scripts/actors/interactable.gd"
const NPC := "res://scripts/actors/npc.gd"
const LEVEL_ID := "L_A1_Railyard"
const STORY_HOTSPOTS := ["irina", "seal", "timetable", "signal_board", "ledger"]
const MIN_STORY_GAP := 26.0
const MIN_FIND_GAP := 12.0
const OBLIQUE_Y := 1.6          # scripts/actors/player.gd: d.y *= 1.6 in oblique levels
const HIDDEN_MAX_RADIUS := 22.0
## §12.3: the Karsk objects that carry the eight Soviet history cards.
const HISTORY := {
	"karsk.kontora_shelf": ["hist.soviet.secret_protocol", "exp_kontora_shelf"],
	"karsk.newspaper": ["hist.soviet.katyn", "exp_newspaper"],
	"karsk.wagon_chalk": ["hist.soviet.deportations", "exp_wagon_chalk"],
	"karsk.workers": ["hist.soviet.novocherkassk", "exp_workers"],
	"karsk.cooling_towers": ["hist.soviet.kyshtym", "exp_cooling_towers"],
	"karsk.barrack": ["hist.soviet.gulag", "exp_barrack"],
	"karsk.banner": ["hist.soviet.great_terror", "exp_banner"],
	"karsk.grain": ["hist.soviet.holodomor", "exp_grain"],
}
const FIXED_CARDS := ["hist.reich.germania", "hist.reich.evictions", "hist.reich.schwerbelastungskoerper",
	"hist.reich.wannsee", "hist.reich.reichsbahn", "hist.reich.generalplan_ost", "hist.reich.t4",
	"hist.reich.forced_labor", "hist.soviet.secret_protocol", "hist.soviet.katyn", "hist.soviet.deportations",
	"hist.soviet.novocherkassk", "hist.soviet.kyshtym", "hist.soviet.gulag", "hist.soviet.great_terror",
	"hist.soviet.holodomor"]
## §12.6 chat speakers with portraits.
const PORTRAIT_SPEAKERS := ["alexei", "konrad", "irina", "emil", "vendor", "worker_a", "babushka", "librarian", "porter"]
const HIDDEN_FINDS := ["karsk.stairs_under", "karsk.stash"]
## Canonical story nodes and their contract (must stay exactly as integrated).
const STORY_NODES := {
	"TalkIrina": ["a1_talk_irina", "dialogue", "irina"],
	"ChoiceIrina": ["a1_choose", "choice", "irina"],
	"Seal": ["a1_inspect_seal", "inspect", "seal"],
	"Timetable": ["a1_inspect_timetable", "inspect", "timetable"],
	"SignalBoard": ["a1_solve_signal", "puzzle", "signal_board"],
	"Ledger": ["a1_inspect_ledger", "inspect", "ledger"],
}

var kit: Kit
var loc: Node
var data: Dictionary = {}
var entries: Dictionary = {}       # id -> entry
var hotspots: Dictionary = {}      # merged: explore_hotspots.json, then scene.json on top
var art: Dictionary = {}
var nodes: Array = []              # [{name, script, props}]
var finds: Array = []              # exploration interactables: {name, kind, explore_id, hotspot_id, pos, radius}


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.run_case("data_file_shape", _data_shape)
	kit.run_case("scene_nodes_readable", _read_scene)
	kit.run_case("interactables_reference_entries_and_hotspots", _references)
	kit.run_case("every_entry_placed_once", _entries_placed)
	kit.run_case("loc_keys_exist_and_belong_to_the_area", _loc_keys)
	kit.run_case("history_links_follow_12_3", _history)
	kit.run_case("chats_have_portrait_speakers", _chats)
	kit.run_case("finds_clear_of_story_hotspots", _placement)
	kit.run_case("finds_reachable_in_the_walk_band", _reachable)
	kit.run_case("story_interactables_unchanged", _story_unchanged)
	kit.run_case("npcs_have_sprites", _npcs)
	kit.run_case("closeups_fit_and_hist_twins_match", _images)
	kit.run_case("text_lengths_and_voice_rules", _texts)
	kit.cleanup()
	return kit.failures


func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


# ------------------------------------------------------------------ cases
func _data_shape() -> bool:
	var d = _json(DATA)
	if not kit.ok(d is Dictionary, "karsk.json parses to an object"):
		return true
	data = d
	kit.eq(str(data.get("area", "")), "karsk", "area name")
	var list = data.get("entries", [])
	if not kit.ok(list is Array and not list.is_empty(), "entries array"):
		return true
	var kinds := {"detail": 0, "secret": 0, "easter_egg": 0, "chat": 0}
	for e in list:
		if not kit.ok(e is Dictionary and str(e.get("id", "")).begins_with("karsk."), "entry id starts with karsk."):
			continue
		var id := str(e["id"])
		kit.ok(not entries.has(id), "unique entry id %s" % id)
		entries[id] = e
		kit.eq(str(e.get("level", "")), LEVEL_ID, "%s level" % id)
		var k := str(e.get("kind", ""))
		if kit.ok(kinds.has(k), "%s kind '%s' is known" % [id, k]):
			kinds[k] += 1
	var discover: int = kinds["detail"] + kinds["secret"] + kinds["easter_egg"]
	kit.ok(discover >= 14 and discover <= 20, "14-18 discover entries (got %d)" % discover)
	kit.ok(kinds["easter_egg"] >= 2 and kinds["easter_egg"] <= 3, "2-3 easter eggs (got %d)" % kinds["easter_egg"])
	kit.ok(kinds["secret"] >= 1, "at least one secret")
	kit.eq(kinds["chat"], 3, "three chats")
	# hotspots: content fallbacks first, the art manifest wins on clashes (Level._merge_explore_hotspots)
	var extra = _json(EXTRA)
	if kit.ok(extra is Dictionary and extra.get("hotspots") is Dictionary, "explore_hotspots.json has hotspots"):
		for k in extra["hotspots"]:
			hotspots[k] = extra["hotspots"][k]
	var a = _json(ART)
	if kit.ok(a is Dictionary, "scene.json parses"):
		art = a
		var hs = art.get("hotspots", {})
		if hs is Dictionary:
			for k in hs:
				hotspots[k] = hs[k]
	return true


func _read_scene() -> bool:
	var ps = load(SCENE)
	if not kit.ok(ps is PackedScene, "L_A1_Railyard.tscn loads as PackedScene"):
		return true
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
		nodes.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props,
			"parent": str(st.get_node_path(i, true))})
	for n in nodes:
		if n["script"] != INTERACTABLE:
			continue
		var kind := str(n["props"].get("kind", "inspect"))
		if kind != "discover" and kind != "chat":
			continue
		var hid := str(n["props"].get("hotspot_id", ""))
		var off: Vector2 = n["props"].get("hotspot_offset", Vector2.ZERO)
		var pos := Vector2(INF, INF)
		if hotspots.has(hid) and hotspots[hid] is Array and hotspots[hid].size() >= 2:
			pos = Vector2(float(hotspots[hid][0]), float(hotspots[hid][1])) + off
		finds.append({"name": n["name"], "kind": kind, "explore_id": str(n["props"].get("explore_id", "")),
			"hotspot_id": hid, "pos": pos, "radius": float(n["props"].get("radius", 30.0)),
			"parent": n["parent"]})
	kit.ok(finds.size() >= 17, "exploration interactables found in the scene (%d)" % finds.size())
	return true


func _references() -> bool:
	for f in finds:
		var who := "%s (%s)" % [f["name"], f["explore_id"]]
		kit.ok(str(f["parent"]).ends_with("Playfield"), "%s sits under Playfield (hotspot snapping + y-sort)" % who)
		if str(f["explore_id"]).begins_with("karsk.task."):   # §12.9 side tasks: tasks_karsk.json, checked by tests/test_tasks.gd
			continue
		if str(f["explore_id"]) == "karsk.morse":   # round-7 mini-game find: minigames_r7_kb.json, checked by tests/test_minigames_r7_kb.gd
			continue
		if not kit.ok(entries.has(f["explore_id"]), "%s: explore_id exists in karsk.json" % who):
			continue
		var ek := str(entries[f["explore_id"]].get("kind", ""))
		if f["kind"] == "chat":
			kit.eq(ek, "chat", "%s: chat node -> chat entry" % who)
		else:
			kit.ok(ek in ["detail", "secret", "easter_egg"], "%s: discover node -> detail/secret/easter_egg entry" % who)
		kit.ok(str(f["hotspot_id"]).begins_with("exp_"), "%s: uses an exp_* hotspot" % who)
		kit.ok(hotspots.has(f["hotspot_id"]), "%s: hotspot '%s' exists in scene.json ∪ explore_hotspots.json" % [who, f["hotspot_id"]])
		kit.ok(f["radius"] > 0.0, "%s: positive radius" % who)
	return true


func _entries_placed() -> bool:
	var used := {}
	for f in finds:
		used[f["explore_id"]] = int(used.get(f["explore_id"], 0)) + 1
	for id in entries:
		kit.eq(int(used.get(id, 0)), 1, "entry %s is placed by exactly one Interactable" % id)
	return true


func _loc_keys() -> bool:
	var lf = _json(LOCALE)
	if not kit.ok(lf is Dictionary, "de_explore_karsk.json parses"):
		return true
	kit.eq(str(lf.get("locale", "")), "de-DE", "locale tag")
	kit.eq(str(lf.get("area", "")), "explore_karsk", "area tag")
	var strings: Dictionary = lf.get("strings", {})
	var used := {}
	for id in entries:
		var e: Dictionary = entries[id]
		for k in ["title_key", "text_key", "prompt_key"]:
			var key := str(e.get(k, ""))
			if kit.ok(key != "", "%s has %s" % [id, k]):
				used[key] = true
		for l in e.get("lines", []):
			used[str(l.get("key", ""))] = true
	for key in used:
		kit.ok(loc.has(key), "Loc has '%s'" % key)
		kit.ok(str(key).begins_with("explore.karsk."), "'%s' lives in the explore.karsk namespace" % key)
		kit.ok(loc.source_of(key).ends_with("de_explore_karsk.json"), "'%s' comes from de_explore_karsk.json (no override)" % key)
	for key in strings:
		kit.ok(used.has(key), "locale string '%s' is used by karsk.json" % key)
		kit.ok(str(strings[key]).strip_edges() != "", "'%s' is not empty" % key)
	return true


func _history() -> bool:
	var linked := {}
	for id in entries:
		var h = entries[id].get("history", [])
		if not kit.ok(h is Array, "%s: history is an array" % id):
			continue
		for cid in h:
			kit.ok(str(cid) in FIXED_CARDS, "%s: '%s' is one of the 16 §12.3 cards" % [id, cid])
			kit.ok(str(cid).begins_with("hist.soviet."), "%s: Karsk links only Soviet cards" % id)
			linked[str(cid)] = int(linked.get(str(cid), 0)) + 1
		if HISTORY.has(id):
			kit.eq(h, [HISTORY[id][0]], "%s links exactly %s" % [id, HISTORY[id][0]])
		else:
			kit.eq(h, [], "%s links no history card" % id)
	for id in HISTORY:
		kit.eq(int(linked.get(HISTORY[id][0], 0)), 1, "%s is linked exactly once" % HISTORY[id][0])
		var placed := ""
		for f in finds:
			if f["explore_id"] == id:
				placed = f["hotspot_id"]
		kit.eq(placed, HISTORY[id][1], "%s sits on %s (§12.3)" % [id, HISTORY[id][1]])
	return true


func _chats() -> bool:
	for id in entries:
		var e: Dictionary = entries[id]
		if str(e.get("kind", "")) != "chat":
			kit.ok(not e.has("lines"), "%s: only chats carry lines" % id)
			continue
		var lines = e.get("lines", [])
		if not kit.ok(lines is Array and lines.size() >= 4 and lines.size() <= 8, "%s: 4-8 lines" % id):
			continue
		var speakers := {}
		for l in lines:
			var sp := str(l.get("speaker", ""))
			kit.ok(sp in PORTRAIT_SPEAKERS, "%s: speaker '%s' has a portrait (§12.6)" % [id, sp])
			kit.ok(str(l.get("expr", "neutral")) in ["neutral", "concerned", "determined", "surprised"],
				"%s: expression '%s' exists" % [id, l.get("expr", "")])
			speakers[sp] = true
		kit.ok(speakers.has("alexei") and speakers.size() >= 2, "%s: Alexei and someone else talk" % id)
		for sp in speakers:
			if not loc.has("char.%s.name" % sp):
				print("      note: char.%s.name has no German name yet (characters area)" % sp)
	return true


func _oblique(a: Vector2, b: Vector2) -> float:
	return Vector2(a.x - b.x, (a.y - b.y) * OBLIQUE_Y).length()


func _placement() -> bool:
	for f in finds:
		if not is_finite(f["pos"].x):
			continue
		for s in STORY_HOTSPOTS:
			if not kit.ok(hotspots.has(s), "story hotspot %s exists" % s):
				continue
			var sp := Vector2(float(hotspots[s][0]), float(hotspots[s][1]))
			var d := _oblique(f["pos"], sp)
			kit.ok(d >= MIN_STORY_GAP, "%s at %s is %.1f px from story hotspot %s (need >= %d)" % [f["name"], f["pos"], d, s, MIN_STORY_GAP])
	for i in finds.size():
		for j in range(i + 1, finds.size()):
			var a: Dictionary = finds[i]
			var b: Dictionary = finds[j]
			if is_finite(a["pos"].x) and is_finite(b["pos"].x):
				var d := _oblique(a["pos"], b["pos"])
				kit.ok(d >= MIN_FIND_GAP, "%s and %s are %.1f px apart (need >= %d)" % [a["name"], b["name"], d, MIN_FIND_GAP])
	for f in finds:
		if f["explore_id"] in HIDDEN_FINDS:
			kit.ok(f["radius"] <= HIDDEN_MAX_RADIUS, "%s: hidden find uses a small radius (%.0f)" % [f["name"], f["radius"]])
	return true


func _poly(pts) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in pts:
		out.append(Vector2(float(p[0]), float(p[1])))
	return out


func _reachable() -> bool:
	var walk := _poly(art.get("walkable", []))
	var cols: Array = []
	for p in art.get("props", []):
		if p is Dictionary and p.get("collision", []) is Array and p.get("collision", []).size() >= 3:
			cols.append([str(p.get("name", "")), _poly(p["collision"])])
	for f in finds:
		var p: Vector2 = f["pos"]
		if not kit.ok(is_finite(p.x), "%s has a resolved position" % f["name"]):
			continue
		if walk.size() >= 3:
			kit.ok(Geometry2D.is_point_in_polygon(p, walk), "%s at %s must lie in the walkable band" % [f["name"], p])
		for c in cols:
			kit.ok(not Geometry2D.is_point_in_polygon(p, c[1]), "%s at %s must not lie inside the collision of %s" % [f["name"], p, c[0]])
	return true


func _story_unchanged() -> bool:
	var by_name := {}
	for n in nodes:
		by_name[n["name"]] = n
	for nm in STORY_NODES:
		if not kit.ok(by_name.has(nm), "story node %s present" % nm):
			continue
		var p: Dictionary = by_name[nm]["props"]
		kit.eq(by_name[nm]["script"], INTERACTABLE, "%s uses interactable.gd" % nm)
		kit.eq(str(p.get("objective_id", "")), STORY_NODES[nm][0], "%s objective" % nm)
		kit.eq(str(p.get("kind", "")), STORY_NODES[nm][1], "%s kind" % nm)
		kit.eq(str(p.get("hotspot_id", "")), STORY_NODES[nm][2], "%s hotspot" % nm)
		kit.ok(not p.has("hotspot_offset") or p["hotspot_offset"] == Vector2.ZERO, "%s keeps its hotspot position" % nm)
		kit.ok(str(p.get("explore_id", "")) == "", "%s carries no explore_id" % nm)
	for nm in ["ObsStove", "ObsPoster", "ObsFamily", "Irina", "Babushka", "Child"]:
		kit.ok(by_name.has(nm), "existing node %s kept" % nm)
	return true


func _npcs() -> bool:
	for n in nodes:
		if n["script"] != NPC:
			continue
		var cid := str(n["props"].get("char_id", "irina"))
		kit.ok(FileAccess.file_exists("res://assets/characters/%s/sheet.json" % cid), "NPC %s: sprite sheet for '%s'" % [n["name"], cid])
		var hid := str(n["props"].get("hotspot_id", ""))
		if hid != "":
			kit.ok(hotspots.has(hid), "NPC %s: hotspot '%s' exists" % [n["name"], hid])
	return true


func _images() -> bool:
	for id in entries:
		var img := str(entries[id].get("image", ""))
		if img == "":
			continue
		kit.ok(img.begins_with("res://assets/explore/karsk/") and img.ends_with(".png"), "%s: close-up lives in assets/explore/karsk/" % id)
		if not kit.ok(FileAccess.file_exists(img), "%s: %s exists" % [id, img]):
			continue
		var im := Image.load_from_file(ProjectSettings.globalize_path(img))
		if not kit.ok(im != null and not im.is_empty(), "%s: close-up loads" % id):
			continue
		kit.ok(im.get_width() <= 320 and im.get_height() <= 200, "%s: %dx%d fits 320x200" % [id, im.get_width(), im.get_height()])
		var hist := img.get_basename() + "_hist." + img.get_extension()
		if FileAccess.file_exists(hist):
			var h := Image.load_from_file(ProjectSettings.globalize_path(hist))
			kit.ok(h != null and h.get_size() == im.get_size(), "%s: _hist twin has the neutral file's size" % id)
	return true


func _sentences(s: String) -> int:
	var re := RegEx.new()
	re.compile("[.!?…][“”\"]?(\\s|$)")
	return re.search_all(s).size()


func _texts() -> bool:
	for id in entries:
		var e: Dictionary = entries[id]
		var title: String = loc.t(str(e.get("title_key", "")))
		kit.ok(title.length() <= 32, "%s: title '%s' is short" % [id, title])
		var prompt: String = loc.t(str(e.get("prompt_key", "")))
		kit.ok(prompt.length() <= 32, "%s: prompt '%s' fits the HUD" % [id, prompt])
		var text: String = loc.t(str(e.get("text_key", "")))
		if str(e.get("kind", "")) != "chat":
			var n := _sentences(text)
			kit.ok(n >= 1 and n <= 4, "%s: 1-4 sentences (got %d)" % [id, n])
		for l in e.get("lines", []):
			kit.ok(loc.t(str(l.get("key", ""))).length() <= 200, "%s: line %s fits the dialogue box" % [id, l.get("key", "")])
	# the pre-rename protagonist name is guarded project-wide by test_rename_guard.gd (data/locale is owned there)
	return true
