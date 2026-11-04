extends RefCounted
## Consistency of the Berlin archive exploration content (owner: berlin-explore, TECHNICAL_ARCHITECTURE §12):
## data/explore/berlin.json  <->  data/locale/de_explore_berlin.json  <->  scenes/levels/L_M1_Archive.tscn
## <->  hotspots in assets/environments/berlin_archive/scene.json ∪ explore_hotspots.json (scene.json wins)
## <->  real-history card ids (§12.3) and close-up images (≤ 320×200, neutral file + optional _hist variant).
## Also guards the canonical story nodes of M1 and keeps every exploration spot clear of the story spots.

const Kit := preload("res://tests/support/test_kit.gd")

const DATA := "res://data/explore/berlin.json"
const LOCALE := "res://data/locale/de_explore_berlin.json"
const SCENE := "res://scenes/levels/L_M1_Archive.tscn"
const MANIFEST := "res://assets/environments/berlin_archive/scene.json"
const EXTRA_HOTSPOTS := "res://assets/environments/berlin_archive/explore_hotspots.json"
const HISTORY_REICH := "res://data/explore/history_reich.json"
const INTERACTABLE := "res://scripts/actors/interactable.gd"
const NPC := "res://scripts/actors/npc.gd"
const LEVEL := "L_M1_Archive"

const KINDS := ["detail", "secret", "easter_egg", "chat"]
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
const SPEAKERS := ["konrad", "porter", "librarian", "emil"]
## §12.2: hotspots the art owner provides and this content relies on.
const CONTRACT_HOTSPOTS := ["exp_lib_shelf_1", "exp_lib_shelf_2", "exp_lib_shelf_3", "exp_lib_shelf_4",
	"exp_lib_shelf_5", "exp_lib_hidden", "exp_card_catalogue", "exp_librarian_desk", "exp_reading_table",
	"exp_globe", "exp_poster_aufbau", "exp_photo", "exp_master_plan", "exp_pneumatic_tube", "exp_radio",
	"exp_mouse", "exp_pigeons", "exp_coat_stand", "exp_porter", "exp_clock", "exp_heater"]
## §12.3: fixed real-history links of the Berlin finds (entry id -> card id).
const HISTORY_LINKS := {
	"berlin.poster_aufbau": "hist.reich.germania", "berlin.photo": "hist.reich.evictions",
	"berlin.master_plan": "hist.reich.schwerbelastungskoerper", "berlin.lib_shelf_1": "hist.reich.wannsee",
	"berlin.lib_shelf_2": "hist.reich.reichsbahn", "berlin.lib_shelf_3": "hist.reich.generalplan_ost",
	"berlin.lib_shelf_4": "hist.reich.t4", "berlin.lib_shelf_5": "hist.reich.forced_labor"}
## Canonical M1 story nodes (node name -> [objective id, kind, hotspot]).
const STORY_NODES := {"PlanA": ["m1_inspect_plan_a", "inspect", "plan_a"],
	"PlanB": ["m1_inspect_plan_b", "inspect", "plan_b"], "Overlay": ["m1_align_plans", "puzzle", "overlay_table"],
	"TalkEmil": ["m1_talk_emil", "dialogue", "emil"], "ChoiceEmil": ["m1_choose", "choice", "emil"]}
const MIN_GAP_STORY := 24.0      # exploration spot <-> story spot (px)
const MIN_GAP_EXPLORE := 14.0    # exploration spot <-> exploration spot (px)

var kit: Kit
var data: Dictionary = {}
var strings: Dictionary = {}
var nodes: Array = []          # [{name, script, props}]
var hotspots: Dictionary = {}  # merged, scene.json wins
var spawns: Dictionary = {}
var manifest: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	kit.run_case("data_file", _data_file)
	kit.run_case("locale_keys_and_lengths", _locale)
	kit.run_case("chats", _chats)
	kit.run_case("history_links", _history)
	kit.run_case("images", _images)
	kit.run_case("scene_nodes", _scene_nodes)
	kit.run_case("hotspots_exist", _hotspots_exist)
	kit.run_case("spacing_and_reach", _spacing)
	kit.run_case("explore_validation", _explore_validation)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ loading helpers
static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _load_all() -> bool:
	if not data.is_empty():
		return true
	var d = _json(DATA)
	var l = _json(LOCALE)
	if not kit.ok(d is Dictionary, "berlin.json parses") or not kit.ok(l is Dictionary, "locale file parses"):
		return false
	data = d
	strings = l.get("strings", {})
	manifest = _json(MANIFEST) if _json(MANIFEST) is Dictionary else {}
	var extra = _json(EXTRA_HOTSPOTS)
	extra = extra if extra is Dictionary else {}
	for section in ["hotspots", "spawns"]:
		var merged: Dictionary = (manifest.get(section, {}) as Dictionary).duplicate()
		var src = extra.get(section, {})
		if src is Dictionary:
			for k in src:
				if not merged.has(k):
					merged[k] = src[k]
		if section == "hotspots":
			hotspots = merged
		else:
			spawns = merged
	var ps := load(SCENE) as PackedScene
	if not kit.ok(ps != null, "level scene loads"):
		return false
	var st := ps.get_state()
	for i in st.get_node_count():
		var props := {}
		var script_path := ""
		for j in st.get_node_property_count(i):
			var pn := str(st.get_node_property_name(i, j))
			var pv = st.get_node_property_value(i, j)
			if pn == "script" and pv is Script:
				script_path = (pv as Script).resource_path
			else:
				props[pn] = pv
		nodes.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props})
	return true


func _entries() -> Array:
	return data.get("entries", [])


func _entry(id: String) -> Dictionary:
	for e in _entries():
		if str(e.get("id", "")) == id:
			return e
	return {}


func _interactables() -> Array:
	var out: Array = []
	for n in nodes:
		if n["script"] == INTERACTABLE:
			out.append(n)
	return out


static func _pt(v) -> Vector2:
	return Vector2(float(v[0]), float(v[1])) if v is Array and v.size() >= 2 else Vector2.INF


## Effective world position of an interactable/NPC node: manifest hotspot + hotspot_offset.
func _pos(n: Dictionary) -> Vector2:
	var hid := str(n["props"].get("hotspot_id", ""))
	if hid == "" or not hotspots.has(hid):
		return Vector2.INF
	var off = n["props"].get("hotspot_offset", Vector2.ZERO)
	return _pt(hotspots[hid]) + (off if off is Vector2 else Vector2.ZERO)


# ------------------------------------------------------------------ cases
func _data_file() -> bool:
	if not _load_all():
		return true
	kit.eq(str(data.get("area", "")), "berlin", "area name")
	var ids := {}
	var by_kind := {}
	for e in _entries():
		var id := str(e.get("id", ""))
		kit.ok(id.begins_with("berlin."), "id '%s' is prefixed 'berlin.'" % id)
		kit.ok(not ids.has(id), "id '%s' is unique" % id)
		ids[id] = true
		var kind := str(e.get("kind", ""))
		kit.ok(kind in KINDS, "%s: kind '%s' is allowed" % [id, kind])
		by_kind[kind] = int(by_kind.get(kind, 0)) + 1
		kit.eq(str(e.get("level", "")), LEVEL, "%s: level" % id)
		var stem := id.trim_prefix("berlin.")
		for k in ["title", "text", "prompt"]:
			kit.eq(str(e.get(k + "_key", "")), "explore.berlin.%s.%s" % [stem, k], "%s: %s_key follows the naming scheme" % [id, k])
		if kind != "chat":
			kit.ok(not e.has("lines"), "%s: only chats have lines" % id)
		if kind == "easter_egg":   # §12.7: jokes never sit on atrocity topics
			kit.ok((e.get("history", []) as Array).is_empty(), "%s: easter eggs carry no history card" % id)
	var discover := _entries().size() - int(by_kind.get("chat", 0))
	kit.ok(discover >= 16 and discover <= 20, "16–20 discover entries (have %d)" % discover)
	kit.ok(int(by_kind.get("chat", 0)) >= 3, "at least 3 chats (have %d)" % int(by_kind.get("chat", 0)))
	kit.ok(int(by_kind.get("secret", 0)) >= 3, "at least 3 secrets")
	kit.ok(int(by_kind.get("easter_egg", 0)) >= 2, "at least 2 easter eggs")
	for must in ["berlin.lib_hidden", "berlin.pneumatic_tube", "berlin.card_catalogue"]:
		kit.eq(str(_entry(must).get("kind", "")), "secret", "%s is a secret" % must)
	for egg in ["berlin.mouse", "berlin.radio", "berlin.pigeons"]:
		kit.eq(str(_entry(egg).get("kind", "")), "easter_egg", "%s is an easter egg" % egg)
	return true


func _locale() -> bool:
	if not _load_all():
		return true
	var used := {}
	for e in _entries():
		var id := str(e["id"])
		for k in ["title_key", "text_key", "prompt_key"]:
			var key := str(e.get(k, ""))
			used[key] = true
			kit.ok(strings.has(key), "%s: %s '%s' has a German string" % [id, k, key])
		for l in e.get("lines", []):
			used[str(l.get("key", ""))] = true
			kit.ok(strings.has(str(l.get("key", ""))), "%s: line key '%s' has a German string" % [id, l.get("key", "")])
		var title := str(strings.get(str(e.get("title_key", "")), ""))
		var prompt := str(strings.get(str(e.get("prompt_key", "")), ""))
		var text := str(strings.get(str(e.get("text_key", "")), ""))
		kit.ok(title.length() >= 3 and title.length() <= 32, "%s: title length 3–32 (%d)" % [id, title.length()])
		kit.ok(prompt.length() >= 5 and prompt.length() <= 32, "%s: prompt length 5–32 (%d)" % [id, prompt.length()])
		if str(e.get("kind", "")) == "chat":
			kit.ok(text.length() >= 40 and text.length() <= 200, "%s: chat summary length 40–200" % id)
			for l in e.get("lines", []):
				var s := str(strings.get(str(l.get("key", "")), ""))
				kit.ok(s.length() >= 4 and s.length() <= 220, "%s: line '%s' length 4–220 (%d)" % [id, l.get("key", ""), s.length()])
		else:
			kit.ok(text.length() >= 250 and text.length() <= 520, "%s: find text length 250–520, fits the notebook page unscrolled (%d)" % [id, text.length()])
	# observe spots of this area may use keys from this file too (one spoken thought: prompt + text)
	for n in _interactables():
		var ok_key := str(n["props"].get("observe_key", ""))
		if str(n["props"].get("kind", "")) == "observe" and ok_key.begins_with("explore.berlin."):
			for suffix in [".prompt", ".text"]:
				used[ok_key + suffix] = true
				kit.ok(strings.has(ok_key + suffix), "%s: observe key %s%s has a German string" % [n["name"], ok_key, suffix])
			var t := str(strings.get(ok_key + ".text", ""))
			kit.ok(t.length() >= 120 and t.length() <= 450, "%s: observe text length 120–450 (%d)" % [n["name"], t.length()])
	for key in strings:
		kit.ok(used.has(key), "string '%s' is used by an entry" % key)
		var s := str(strings[key])
		kit.ok(not s.contains("[") and not s.contains("{") and s.strip_edges() == s, "string '%s' is clean" % key)
	# The merged Loc table must serve these keys from this file (no other area overrides them).
	var loc: Node = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for key in strings:
		kit.eq(str(loc.source_of(key)), LOCALE, "Loc serves '%s' from de_explore_berlin.json" % key)
	return true


func _chats() -> bool:
	if not _load_all():
		return true
	var chats := {}
	for e in _entries():
		if str(e.get("kind", "")) != "chat":
			continue
		var id := str(e["id"])
		chats[id] = true
		var lines: Array = e.get("lines", [])
		kit.ok(lines.size() >= 5, "%s: at least 5 lines" % id)
		var konrad_speaks := false
		for l in lines:
			var sp := str(l.get("speaker", ""))
			kit.ok(sp in SPEAKERS, "%s: speaker '%s' is a §12.6 Berlin speaker" % [id, sp])
			kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression '%s' exists" % [id, l.get("expr", "")])
			konrad_speaks = konrad_speaks or sp == "konrad"
		kit.ok(konrad_speaks, "%s: Konrad takes part" % id)
	for must in ["berlin.porter", "berlin.librarian", "berlin.emil_tea"]:
		kit.ok(chats.has(must), "chat %s exists" % must)
	kit.eq(str((_entry("berlin.porter").get("lines", [{}]) as Array)[0].get("speaker", "")), "porter",
		"the porter opens the chapter's first chat (greeting)")
	# The Emil small talk must never pre-empt the canonical Emil dialogue (C-17 / the plans / the corridor).
	for l in _entry("berlin.emil_tea").get("lines", []):
		var s := str(strings.get(str(l.get("key", "")), "")).to_lower()
		for banned in ["c-17", "korridor", "plan", "wand", "serie", "vertr"]:
			kit.ok(not s.contains(banned), "Emil small talk avoids '%s'" % banned)
	return true


func _history() -> bool:
	if not _load_all():
		return true
	var linked := {}
	for e in _entries():
		var id := str(e["id"])
		var hist: Array = e.get("history", [])
		if HISTORY_LINKS.has(id):
			kit.eq(hist, [HISTORY_LINKS[id]], "%s links exactly its §12.3 card" % id)
		else:
			kit.ok(hist.is_empty(), "%s: no history card outside the §12.3 table" % id)
		for c in hist:
			linked[str(c)] = true
	for c in HISTORY_LINKS.values():
		kit.ok(linked.has(c), "card %s is linked" % c)
	var hr = _json(HISTORY_REICH)
	if hr is Dictionary:
		var have := {}
		for c in hr.get("cards", []):
			have[str(c.get("id", ""))] = true
		for c in linked:
			kit.ok(have.has(c), "card %s exists in history_reich.json" % c)
	else:
		print("      note: %s not present yet — card ids checked against §12.3 only" % HISTORY_REICH)
	return true


func _images() -> bool:
	if not _load_all():
		return true
	var count := 0
	for e in _entries():
		var img := str(e.get("image", ""))
		if img == "":
			continue
		count += 1
		kit.ok(img.begins_with("res://assets/explore/berlin/") and img.ends_with(".png"), "%s: image path" % e["id"])
		if not kit.ok(FileAccess.file_exists(img), "%s: image %s exists" % [e["id"], img]):
			continue
		var im := Image.load_from_file(ProjectSettings.globalize_path(img))
		if not kit.ok(im != null and not im.is_empty(), "%s: image decodes" % e["id"]):
			continue
		kit.ok(im.get_width() <= 320 and im.get_height() <= 200 and im.get_width() >= 160,
			"%s: close-up size %dx%d within 160..320 x ..200" % [e["id"], im.get_width(), im.get_height()])
		var hist_path := img.get_basename() + "_hist.png"
		if FileAccess.file_exists(hist_path):
			var hi := Image.load_from_file(ProjectSettings.globalize_path(hist_path))
			kit.ok(hi != null and hi.get_size() == im.get_size(), "%s: _hist variant has the same size" % e["id"])
	kit.ok(count >= 12, "at least 12 close-ups (have %d)" % count)
	return true


func _scene_nodes() -> bool:
	if not _load_all():
		return true
	var by_name := {}
	for n in nodes:
		by_name[n["name"]] = n
	# canonical story interactables unchanged
	for nm in STORY_NODES:
		var spec: Array = STORY_NODES[nm]
		if not kit.ok(by_name.has(nm), "story node %s present" % nm):
			continue
		var p: Dictionary = by_name[nm]["props"]
		kit.eq(by_name[nm]["script"], INTERACTABLE, "%s is an Interactable" % nm)
		kit.eq(str(p.get("objective_id", "")), spec[0], "%s objective" % nm)
		kit.eq(str(p.get("kind", "")), spec[1], "%s kind" % nm)
		kit.eq(str(p.get("hotspot_id", "")), spec[2], "%s hotspot" % nm)
	kit.ok(by_name.has("Emil") and str(by_name["Emil"]["props"].get("char_id", "")) == "emil", "Emil NPC present")
	for pair in [["Porter", "porter", "exp_porter"], ["Librarian", "librarian", "exp_librarian_desk"]]:
		if kit.ok(by_name.has(pair[0]), "NPC node %s present" % pair[0]):
			kit.eq(by_name[pair[0]]["script"], NPC, "%s uses npc.gd" % pair[0])
			kit.eq(str(by_name[pair[0]]["props"].get("char_id", "")), pair[1], "%s char_id" % pair[0])
			kit.eq(str(by_name[pair[0]]["props"].get("hotspot_id", "")), pair[2], "%s stands at its hotspot" % pair[0])
	# every entry is placed by exactly one node; every exploration node points at a real entry
	var placed := {}
	for n in _interactables():
		var p: Dictionary = n["props"]
		var kind := str(p.get("kind", "inspect"))
		if kind == "observe":
			var ok_key := str(p.get("observe_key", ""))
			kit.ok(ok_key != "obs.berlin.photo" and ok_key != "obs.berlin.notice",
				"%s: old observe spot was replaced by a discover entry" % n["name"])
		if kind != "discover" and kind != "chat":
			continue
		var eid := str(p.get("explore_id", ""))
		var e := _entry(eid)
		if not kit.ok(not e.is_empty(), "%s: explore_id '%s' exists in berlin.json" % [n["name"], eid]):
			continue
		kit.eq(kind, "chat" if str(e["kind"]) == "chat" else "discover", "%s: node kind matches entry kind" % n["name"])
		kit.ok(not placed.has(eid), "%s placed only once" % eid)
		placed[eid] = n["name"]
		if kind == "chat":
			var speakers := {}
			for l in e.get("lines", []):
				speakers[str(l.get("speaker", ""))] = true
			kit.ok(speakers.has(str(p.get("npc_id", ""))), "%s: npc_id '%s' speaks in the chat" % [n["name"], p.get("npc_id", "")])
	for e in _entries():
		kit.ok(placed.has(str(e["id"])), "%s is placed in the level" % e["id"])
	return true


func _hotspots_exist() -> bool:
	if not _load_all():
		return true
	var used := {}
	for n in nodes:
		var hid := str(n["props"].get("hotspot_id", ""))
		if hid != "":
			used[hid] = true
			kit.ok(hotspots.has(hid), "%s: hotspot '%s' exists in scene.json ∪ explore_hotspots.json" % [n["name"], hid])
	for h in CONTRACT_HOTSPOTS:
		kit.ok(used.has(h), "§12.2 hotspot %s is used by a node" % h)
	kit.ok(spawns.has("SP_M1_Arrival"), "spawn SP_M1_Arrival exists")
	kit.ok(spawns.has("SP_M1_Office"), "spawn SP_M1_Office still exists")
	return true


func _spacing() -> bool:
	if not _load_all():
		return true
	var story: Array = []
	var explore: Array = []
	for n in _interactables():
		var kind := str(n["props"].get("kind", "inspect"))
		var p := _pos(n)
		if p == Vector2.INF:
			continue
		var item := {"name": n["name"], "pos": p, "radius": float(n["props"].get("radius", 30.0))}
		if kind in ["inspect", "dialogue", "puzzle", "choice"]:
			story.append(item)
		elif kind in ["discover", "chat", "observe"]:
			explore.append(item)
	kit.ok(story.size() == 5 and explore.size() >= 20, "positions resolved (%d story, %d optional)" % [story.size(), explore.size()])
	for a in explore:
		for s in story:
			kit.ok(a["pos"].distance_to(s["pos"]) >= MIN_GAP_STORY,
				"%s keeps %d px from story spot %s (%.0f)" % [a["name"], int(MIN_GAP_STORY), s["name"], a["pos"].distance_to(s["pos"])])
	for i in explore.size():
		for j in range(i + 1, explore.size()):
			var d: float = explore[i]["pos"].distance_to(explore[j]["pos"])
			kit.ok(d >= MIN_GAP_EXPLORE, "%s and %s are %.0f px apart (min %d)" % [explore[i]["name"], explore[j]["name"], d, int(MIN_GAP_EXPLORE)])
	# reach: side mode keeps the feet on the spawn line, so every spot must be within its radius of that line
	var feet_y := _pt(spawns.get("SP_M1_Office", [0, 300])).y
	var x_min := -INF
	var x_max := INF
	var walk: Array = manifest.get("walkable", [])
	if walk.size() >= 3:
		x_min = INF
		x_max = -INF
		for q in walk:
			x_min = minf(x_min, float(q[0]))
			x_max = maxf(x_max, float(q[0]))
	for a in explore:
		kit.ok(absf(a["pos"].y - feet_y) < a["radius"] - 1.0, "%s is reachable from the feet line (dy %.0f, r %.0f)" % [a["name"], absf(a["pos"].y - feet_y), a["radius"]])
		kit.ok(a["pos"].x >= x_min - 4.0 and a["pos"].x <= x_max + 4.0, "%s lies inside the walkable x range" % a["name"])
	return true


## The Explore autoload's own validation must not complain about this file (missing history cards are
## tolerated while the history specialists' files are not there yet).
func _explore_validation() -> bool:
	if not _load_all():
		return true
	var ex: Node = kit.track(load("res://scripts/core/explore.gd").new())
	if not ex.has_method("load_data") or not ex.has_method("validate"):
		print("      note: Explore has no load_data/validate yet — skipped")
		kit.ok(true, "skipped")
		return true
	ex.set("print_warnings", false)
	ex.load_data(data, "berlin.json")
	var hr = _json(HISTORY_REICH)
	if hr is Dictionary:
		ex.load_data(hr, "history_reich.json")
	for w in ex.validate():
		var s := str(w)
		if not s.contains("berlin."):
			continue   # other areas' cards (history files) are not this test's business
		if not (hr is Dictionary) and s.contains("history card"):
			continue
		kit.fail("Explore validation: " + s)
	kit.ok(true, "validated")
	return true
