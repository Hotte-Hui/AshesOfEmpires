extends RefCounted
## Consistency of the plaza exploration content (owner: plaza-explore, TECHNICAL_ARCHITECTURE §12):
## data/explore/plaza.json  <->  data/locale/de_explore_plaza.json  <->  scenes/levels/L_M1_Plaza.tscn
## <->  hotspots in assets/environments/hall_plaza/scene.json ∪ explore_hotspots.json (scene.json wins)
## <->  existing real-history card ids and close-up images (≤ 320×200, neutral file + optional _hist variant).
## While the art manifest (hall_plaza/scene.json, owner: env) is not there yet, the position checks print a
## note instead of failing.

const Kit := preload("res://tests/support/test_kit.gd")

const DATA := "res://data/explore/plaza.json"
const LOCALE := "res://data/locale/de_explore_plaza.json"
const SCENE := "res://scenes/levels/L_M1_Plaza.tscn"
const MANIFEST := "res://assets/environments/hall_plaza/scene.json"
const EXTRA_HOTSPOTS := "res://assets/environments/hall_plaza/explore_hotspots.json"
const ARCHIVE_MANIFEST := "res://assets/environments/berlin_archive/scene.json"
const HISTORY_REICH := "res://data/explore/history_reich.json"
const INTERACTABLE := "res://scripts/actors/interactable.gd"
const LEVEL := "L_M1_Plaza"

const KINDS := ["detail", "secret", "easter_egg", "chat"]
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
const SPEAKERS := ["konrad", "photographer", "berlin_mother"]
## Hotspots the env owner provides in hall_plaza/scene.json; every one carries a find or a chat.
const CONTRACT_HOTSPOTS := ["exp_pz_tribune", "exp_pz_loudspeaker", "exp_pz_vendor", "exp_pz_family_door",
	"exp_pz_barrier", "exp_pz_guard", "exp_pz_poster", "exp_pz_tank", "exp_pz_tram_stop", "exp_pz_children",
	"exp_pz_banner", "exp_pz_window", "exp_pz_rubble", "exp_pz_photographer"]
## Real-history links (existing cards only, §12.3; no new cards for the plaza).
const HISTORY_LINKS := {"plaza.tribune": "hist.reich.germania", "plaza.family_door": "hist.reich.evictions",
	"plaza.tram_stop": "hist.reich.reichsbahn", "plaza.rubble": "hist.reich.forced_labor"}
const HIST_VARIANTS := ["plaza.poster", "plaza.banner", "plaza.family_door"]   # §12.4: regime iconography → _hist file
## Keys of this file that are not entry keys, and who uses them.
const EXTRA_KEYS := {"explore.plaza.exit.prompt": "ExitArchive prompt", "char.photographer.name": "chat speaker name",
	"ui.explore.area.plaza": "journal area name"}
const MIN_GAP := 26.0            # interaction spot <-> interaction spot (px)

var kit: Kit
var data: Dictionary = {}
var strings: Dictionary = {}
var nodes: Array = []          # [{name, script, props}]
var hotspots: Dictionary = {}  # merged, scene.json wins
var manifest: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	kit.run_case("data_file", _data_file)
	kit.run_case("locale_keys_and_lengths", _locale)
	kit.run_case("chats", _chats)
	kit.run_case("history_links", _history)
	kit.run_case("images", _images)
	kit.run_case("scene_nodes", _scene_nodes)
	kit.run_case("hotspots_and_spacing", _hotspots)
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
	if not kit.ok(d is Dictionary, "plaza.json parses") or not kit.ok(l is Dictionary, "locale file parses"):
		return false
	data = d
	strings = l.get("strings", {})
	var m = _json(MANIFEST)
	manifest = m if m is Dictionary else {}
	hotspots = (manifest.get("hotspots", {}) as Dictionary).duplicate()
	var extra = _json(EXTRA_HOTSPOTS)
	if extra is Dictionary and extra.get("hotspots", {}) is Dictionary:
		for k in extra["hotspots"]:
			if not hotspots.has(k):
				hotspots[k] = extra["hotspots"][k]
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
		nodes.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props,
			"parent": str(st.get_node_path(i, true))})
	return true


func _entries() -> Array:
	return data.get("entries", [])


func _entry(id: String) -> Dictionary:
	for e in _entries():
		if str(e.get("id", "")) == id:
			return e
	return {}


func _interactables() -> Array:
	return nodes.filter(func(n): return n["script"] == INTERACTABLE)


static func _pt(v) -> Vector2:
	return Vector2(float(v[0]), float(v[1])) if v is Array and v.size() >= 2 else Vector2.INF


# ------------------------------------------------------------------ cases
func _data_file() -> bool:
	if not _load_all():
		return true
	kit.eq(str(data.get("area", "")), "plaza", "area name")
	var ids := {}
	var by_kind := {}
	for e in _entries():
		var id := str(e.get("id", ""))
		kit.ok(id.begins_with("plaza."), "id '%s' is prefixed 'plaza.'" % id)
		kit.ok(not ids.has(id), "id '%s' is unique" % id)
		ids[id] = true
		var kind := str(e.get("kind", ""))
		kit.ok(kind in KINDS, "%s: kind '%s' is allowed" % [id, kind])
		by_kind[kind] = int(by_kind.get(kind, 0)) + 1
		kit.eq(str(e.get("level", "")), LEVEL, "%s: level" % id)
		var stem := id.trim_prefix("plaza.")
		for k in ["title", "text", "prompt"]:
			kit.eq(str(e.get(k + "_key", "")), "explore.plaza.%s.%s" % [stem, k], "%s: %s_key naming" % [id, k])
		if kind != "chat":
			kit.ok(not e.has("lines"), "%s: only chats have lines" % id)
		if kind == "easter_egg":   # §12.7: jokes never sit on atrocity topics
			kit.ok((e.get("history", []) as Array).is_empty(), "%s: easter eggs carry no history card" % id)
	var discover := _entries().size() - int(by_kind.get("chat", 0))
	kit.ok(discover >= 12 and discover <= 17, "12–17 discover entries (have %d)" % discover)
	kit.eq(int(by_kind.get("chat", 0)), 2, "two chats")
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
				kit.ok(s.length() >= 4 and s.length() <= 220, "%s: line length 4–220 (%d)" % [id, s.length()])
		else:
			kit.ok(text.length() >= 250 and text.length() <= 520, "%s: find text 250–520, fits the notebook page (%d)" % [id, text.length()])
	for key in EXTRA_KEYS:
		used[key] = true
		kit.ok(strings.has(key), "%s key '%s' present" % [EXTRA_KEYS[key], key])
	kit.eq(str(strings.get("explore.plaza.exit.prompt", "")), "Zurück ins Archiv", "exit prompt text")
	for key in strings:
		kit.ok(used.has(key), "string '%s' is used" % key)
		var s := str(strings[key])
		kit.ok(not s.contains("[") and not s.contains("{") and s.strip_edges() == s, "string '%s' is clean" % key)
		kit.ok(not s.contains("!"), "string '%s' is never exclamatory (tone §12.7)" % key)
	var loc: Node = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for key in strings:
		kit.eq(str(loc.source_of(key)), LOCALE, "Loc serves '%s' from de_explore_plaza.json" % key)
	return true


func _chats() -> bool:
	if not _load_all():
		return true
	var loc: Node = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for e in _entries():
		if str(e.get("kind", "")) != "chat":
			continue
		var id := str(e["id"])
		var lines: Array = e.get("lines", [])
		kit.ok(lines.size() >= 5, "%s: at least 5 lines" % id)
		var konrad := false
		for l in lines:
			var sp := str(l.get("speaker", ""))
			kit.ok(sp in SPEAKERS, "%s: speaker '%s' allowed" % [id, sp])
			kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression '%s' exists" % [id, l.get("expr", "")])
			kit.ok(loc.has("char.%s.name" % sp), "%s: speaker '%s' has a display name" % [id, sp])
			konrad = konrad or sp == "konrad"
		kit.ok(konrad, "%s: Konrad takes part" % id)
	kit.ok(not _entry("plaza.photographer").is_empty(), "chat plaza.photographer exists")
	kit.ok(not _entry("plaza.neighbour").is_empty(), "chat plaza.neighbour (spectator from the cleared block) exists")
	return true


func _history() -> bool:
	if not _load_all():
		return true
	var hr = _json(HISTORY_REICH)
	var have := {}
	if kit.ok(hr is Dictionary, "history_reich.json present"):
		for c in hr.get("cards", []):
			have[str(c.get("id", ""))] = true
	for e in _entries():
		var id := str(e["id"])
		var hist: Array = e.get("history", [])
		if HISTORY_LINKS.has(id):
			kit.eq(hist, [HISTORY_LINKS[id]], "%s links exactly its card" % id)
		else:
			kit.ok(hist.is_empty(), "%s: no history card outside the agreed links" % id)
		for c in hist:
			kit.ok(have.has(str(c)), "%s: card %s exists (no new cards)" % [id, c])
	return true


func _images() -> bool:
	if not _load_all():
		return true
	var count := 0
	for e in _entries():
		var img := str(e.get("image", ""))
		var id := str(e["id"])
		if img == "":
			kit.ok(not (id in HIST_VARIANTS), "%s needs a close-up" % id)
			continue
		count += 1
		kit.ok(img.begins_with("res://assets/explore/plaza/") and img.ends_with(".png"), "%s: image path" % id)
		if not kit.ok(FileAccess.file_exists(img), "%s: image %s exists" % [id, img]):
			continue
		var im := Image.load_from_file(ProjectSettings.globalize_path(img))
		if not kit.ok(im != null and not im.is_empty(), "%s: image decodes" % id):
			continue
		kit.ok(im.get_width() <= 320 and im.get_height() <= 200 and im.get_width() >= 160,
			"%s: close-up size %dx%d within 160..320 x ..200" % [id, im.get_width(), im.get_height()])
		var hist_path := img.get_basename() + "_hist.png"
		kit.eq(FileAccess.file_exists(hist_path), id in HIST_VARIANTS, "%s: _hist variant only for regime iconography" % id)
		if FileAccess.file_exists(hist_path):
			var hi := Image.load_from_file(ProjectSettings.globalize_path(hist_path))
			kit.ok(hi != null and hi.get_size() == im.get_size(), "%s: _hist variant has the same size" % id)
	kit.ok(count >= 9, "close-ups for most finds (have %d)" % count)
	return true


func _scene_nodes() -> bool:
	if not _load_all():
		return true
	var root: Dictionary = nodes[0]["props"]
	var want := {"level_id": LEVEL, "protagonist": "konrad", "mode": "oblique",
		"art_manifest": MANIFEST, "ambience": "amb_berlin_street", "footstep_surface": "snow", "grade_preset": "berlin"}
	kit.eq(nodes[0]["script"], "res://scripts/levels/level.gd", "root uses level.gd")
	for k in want:
		kit.eq(str(root.get(k, "")), want[k], "root %s" % k)
	kit.eq(str(root.get("music", "")), "", "no music: the parade is the sound")
	var by_name := {}
	for n in nodes:
		by_name[n["name"]] = n
	kit.ok(by_name.has("Playfield") and bool(by_name["Playfield"]["props"].get("y_sort_enabled", false)), "y-sorted Playfield")
	# the single exit back into the archive
	var exits := _interactables().filter(func(n): return str(n["props"].get("kind", "")) == "exit")
	if kit.eq(exits.size(), 1, "exactly one exit interactable"):
		var p: Dictionary = exits[0]["props"]
		kit.eq(str(p.get("hotspot_id", "")), "exit_archive", "exit hotspot")
		kit.eq(str(p.get("target_level", "")), "L_M1_Archive", "exit target_level")
		kit.eq(str(p.get("target_spawn", "")), "SP_M1_Arrival", "exit target_spawn")
		kit.eq(str(p.get("prompt_key", "")), "explore.plaza.exit.prompt", "exit prompt_key")
		kit.ok(str(exits[0]["parent"]).ends_with("Playfield"), "exit lives under Playfield (%s)" % exits[0]["parent"])
		var am = _json(ARCHIVE_MANIFEST)
		if am is Dictionary:
			kit.ok((am.get("spawns", {}) as Dictionary).has("SP_M1_Arrival"), "archive spawn SP_M1_Arrival exists")
	# every entry is placed by exactly one node; every exploration node points at a real entry
	var placed := {}
	for n in _interactables():
		var p: Dictionary = n["props"]
		var kind := str(p.get("kind", "inspect"))
		if kind == "exit":
			continue
		kit.ok(kind == "discover" or kind == "chat", "%s: only exploration nodes on the plaza (kind %s)" % [n["name"], kind])
		kit.ok(str(p.get("objective_id", "")) == "", "%s: no story objective" % n["name"])
		var eid := str(p.get("explore_id", ""))
		var e := _entry(eid)
		if not kit.ok(not e.is_empty(), "%s: explore_id '%s' exists in plaza.json" % [n["name"], eid]):
			continue
		kit.eq(kind, "chat" if str(e["kind"]) == "chat" else "discover", "%s: node kind matches entry kind" % n["name"])
		kit.ok(not placed.has(eid), "%s placed only once" % eid)
		placed[eid] = n["name"]
	for e in _entries():
		kit.ok(placed.has(str(e["id"])), "%s is placed in the level" % e["id"])
	# chat partners: npc_id speaks in the chat and stands at the chat spot as an NPC (the evicted family)
	var npc_at := {}
	for n in nodes:
		if n["script"] == "res://scripts/actors/npc.gd":
			npc_at[str(n["props"].get("char_id", ""))] = str(n["props"].get("hotspot_id", ""))
	for c in ["berlin_mother", "berlin_father", "berlin_child"]:
		kit.ok(npc_at.has(c), "family NPC %s present" % c)
	for n in _interactables():
		var nid := str(n["props"].get("npc_id", ""))
		if nid == "":
			continue
		var speakers := (_entry(str(n["props"].get("explore_id", ""))).get("lines", []) as Array).map(
			func(l): return str(l.get("speaker", "")))
		kit.ok(nid in speakers, "%s: npc_id '%s' speaks in the chat" % [n["name"], nid])
		kit.eq(str(npc_at.get(nid, "")), str(n["props"].get("hotspot_id", "")), "%s: NPC %s stands at the chat spot" % [n["name"], nid])
	var used := {}
	for n in _interactables():
		used[str(n["props"].get("hotspot_id", ""))] = true
	for h in CONTRACT_HOTSPOTS:
		kit.ok(used.has(h), "contract hotspot %s is used by a node" % h)
	return true


func _hotspots() -> bool:
	if not _load_all():
		return true
	if manifest.is_empty():
		print("      note: %s not present yet — hotspot positions and spacing not checked" % MANIFEST)
		kit.ok(true, "skipped until the art manifest exists")
		return true
	var walk: PackedVector2Array = []
	for q in manifest.get("walkable", []):
		walk.append(_pt(q))
	var spots: Array = []
	for n in _interactables():
		var hid := str(n["props"].get("hotspot_id", ""))
		if not kit.ok(hotspots.has(hid), "%s: hotspot '%s' exists in scene.json ∪ explore_hotspots.json" % [n["name"], hid]):
			continue
		var off = n["props"].get("hotspot_offset", Vector2.ZERO)
		var p: Vector2 = _pt(hotspots[hid]) + (off if off is Vector2 else Vector2.ZERO)
		spots.append({"name": n["name"], "pos": p})
		if walk.size() >= 3:
			kit.ok(Geometry2D.is_point_in_polygon(p, walk), "%s (%s) stands inside the walkable area" % [n["name"], p])
	for i in spots.size():
		for j in range(i + 1, spots.size()):
			var d: float = spots[i]["pos"].distance_to(spots[j]["pos"])
			kit.ok(d >= MIN_GAP, "%s and %s are %.0f px apart (min %d)" % [spots[i]["name"], spots[j]["name"], d, int(MIN_GAP)])
	return true


## The Explore autoload's own validation must not complain about this file.
func _explore_validation() -> bool:
	if not _load_all():
		return true
	var ex: Node = kit.track(load("res://scripts/core/explore.gd").new())
	if not ex.has_method("load_data") or not ex.has_method("validate"):
		kit.ok(true, "skipped (no load_data/validate)")
		return true
	ex.set("print_warnings", false)
	ex.load_data(data, "plaza.json")
	var hr = _json(HISTORY_REICH)
	if hr is Dictionary:
		ex.load_data(hr, "history_reich.json")
	for w in ex.validate():
		if str(w).contains("plaza."):
			kit.fail("Explore validation: " + str(w))
	kit.ok(true, "validated")
	return true
