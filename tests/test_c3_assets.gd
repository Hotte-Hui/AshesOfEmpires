extends RefCounted
## MERGE-TIME cross-stream checks for Chapter 3 (documentation/C3_DESIGN.md §4–§7). The files checked here are
## produced by the art, character, cinematic, puzzle-UI and exploration streams in parallel, so this file is
## EXPECTED to fail on a branch that does not contain them yet; every failure names the exact missing item.
##  * environments: assets/environments/veltrava_station|veltrava_hall/scene.json — final art (no "placeholder"),
##    every layer/prop/fx file, every hotspot of C3_DESIGN §4 inside the walkable polygon, the entry spawn
##  * characters: sheet.json + portrait.json (and their PNGs) for every Chapter-3 dialogue/chat/reaction speaker
##    and level NPC; every expression used for a speaker exists in its portrait
##  * evidence documents: every Chapter-3 item has an entry in some assets/ui/documents/*_documents.json with a PNG
##  * cinematics: every §12.5 scene of data/chapters/*.json — signal finished, configure(), play(), skip();
##    played headless in the tree: configure → play → skip → skip emits `finished` exactly once
##  * the protocol puzzle UI scene: open(obj_id) + signal solved
##  * exploration („Konsistenztest für alle neuen Erkundungseinträge“): data/explore/veltrava_*.json entries
##    (unique ids, kinds, levels, keys, history cards with sources, chat lines) and the discover/chat
##    interactables of scenes/levels/L_C3_*.tscn (existing entry + hotspot, every entry placed exactly once)

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
const KINDS := ["detail", "secret", "easter_egg", "chat"]
const LEVELS := {"L_C3_Station": "station", "L_C3_Hall": "hall"}
## Chapter 3 part 2 (C3P2_DESIGN.md §7): exploration entries of the registry (one level file for four scenes; its
## entries use the first scene id) and the quay may live in data/explore/veltrava_*.json too. Their ids and texts are
## checked here; documents, placement and counts belong to the part-2 streams' own tests.
const P2_LEVELS := {"L_C3_RegistryA": "registry", "L_C3_Quay": "quay"}
## Scenes registered for a round whose streams have not delivered yet are listed here: reported, not failed, until they
## exist (round 8 delivered all of LS_C3_Radio/Fire/Escape/Halves and c3d_solve_check, so the list is empty again).
const PENDING_R8: Array = []
## Round 9 (documentation/C4_DESIGN.md §10): the Chapter-4 cinematics and puzzle UIs are built by their own streams in
## parallel with the story data; reported, not failed, until they exist (then checked like every other scene here).
const PENDING_R9: Array = []
const DOCS_DIR := "res://assets/ui/documents/"
const EXPLORE_DIR := "res://data/explore/"
## C3_DESIGN §4 — names the content relies on (art ↔ content contract)
const ENVS := {
	"veltrava_station": {"level": "L_C3_Station", "spawn": "SP_C3_Platform", "hotspots": [
		"conductor", "weighbill", "departures", "control", "elena_cafe", "elena_control", "konrad_queue", "voronova",
		"exp_four_rails", "exp_luggage", "exp_pigeons", "exp_bogie", "exp_mitten", "exp_clock", "exp_kiosk", "exp_poster",
		"exp_return_notice", "exp_stove", "exp_exchange", "exp_tram", "exp_footprints"]},
	"veltrava_hall": {"level": "L_C3_Hall", "spawn": "SP_C3_Vestibule", "hotspots": [
		"kessler", "seating", "booth_log", "protocol_table", "booth_2", "alexei_meet", "elena_arrival", "voronova_bg",
		"typist", "journalist", "exp_flags", "exp_cloakroom", "exp_photos", "exp_chandelier", "exp_buffet", "exp_window",
		"exp_evac_plan", "exp_treaty_shelf", "exp_mimeograph", "exp_headsets"]},
}
## C3_DESIGN §6: number of exploration entries per level and the real-history cards with their find spot
const ENTRY_COUNTS := {"L_C3_Station": 15, "L_C3_Hall": 12}
## Further Chapter-3 entry files checked like data/explore/veltrava_*.json (not part of ENTRY_COUNTS): the
## mini-game finds of tests/test_minigames_r7_v.gd.
const EXTRA_ENTRY_FILES := ["minigames_r7_v.json"]
const HISTORY_AT := {"hist.soviet.repatriation": "exp_return_notice", "hist.soviet.handover_1940": "exp_treaty_shelf",
	"hist.reich.nuremberg_interpreters": "exp_headsets"}

var kit: Kit
var loc: Node
var data: Dictionary = {}
var chapter: Dictionary = {}
var level_nodes: Dictionary = {}   # level id -> [{name, props...}] parsed from the .tscn
var entries: Dictionary = {}       # explore id -> entry (all data/explore files)
var entry_file: Dictionary = {}    # explore id -> file
var cards: Dictionary = {}         # history card id -> card


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	data = ENGINE.load_data()["data"]
	var ext = load("res://scripts/core/chapter_ext.gd").new()
	for s in ["levels", "cinematics", "puzzles", "line_expr", "reactions"]:
		chapter[s] = ext.get(s)
	for lid in LEVELS:
		level_nodes[lid] = _parse_level(str(chapter["levels"].get(lid, "res://scenes/levels/%s.tscn" % lid)))
	_read_explore()
	kit.run_case("environment_manifests", _environments)
	kit.run_case("character_sheets_and_portraits", _characters)
	kit.run_case("evidence_documents", _documents)
	kit.run_case("cinematic_scenes_finish_exactly_once", _cinematics)
	kit.run_case("protocol_puzzle_ui", _puzzle_ui)
	kit.run_case("exploration_entries_consistent", _explore_entries)
	kit.run_case("exploration_interactables_placed_once", _explore_interactables)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ readers
static func _json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	var r: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string(path))
	return r["value"] if r["ok"] else null


## [{name, type, script, <property>: value}] for every [node] block of a .tscn (string/number properties).
static func _parse_level(path: String) -> Array:
	var out: Array = []
	if not FileAccess.file_exists(path):
		return out
	var scripts := {}
	var text := FileAccess.get_file_as_string(path)
	for m in RegEx.create_from_string("\\[ext_resource type=\"Script\" path=\"([^\"]+)\" id=\"([^\"]+)\"\\]").search_all(text):
		scripts[m.get_string(2)] = m.get_string(1)
	var prop := RegEx.create_from_string("^([a-z_]+) = (\"([^\"]*)\"|ExtResource\\(\"([^\"]+)\"\\)|[-0-9.]+|true|false)$")
	for block in text.split("\n[node "):
		if not block.begins_with("name=\""):
			continue
		var n := {"name": block.get_slice("\"", 1)}
		for line in block.split("\n"):
			var m := prop.search(line)
			if m == null:
				continue
			if m.get_string(4) != "":
				n[m.get_string(1)] = scripts.get(m.get_string(4), "")
			elif m.get_string(3) != "" or m.get_string(2).begins_with("\""):
				n[m.get_string(1)] = m.get_string(3)
			else:
				n[m.get_string(1)] = m.get_string(2)
		out.append(n)
	return out


func _read_explore() -> void:
	var d := DirAccess.open(EXPLORE_DIR)
	if d == null:
		return
	var names := Array(d.get_files())
	names.sort()
	for f in names:
		if not f.ends_with(".json"):
			continue
		var doc = _json(EXPLORE_DIR + f)
		if not (doc is Dictionary):
			continue
		for e in doc.get("entries", []):
			if e is Dictionary and e.has("id"):
				if entries.has(e["id"]):
					kit.fail("explore id %s defined twice (%s and %s)" % [e["id"], entry_file[e["id"]], f])
				var x: Dictionary = e.duplicate(true)
				x["area"] = str(x.get("area", doc.get("area", "")))
				entries[e["id"]] = x
				entry_file[e["id"]] = f
		for c in doc.get("cards", []):
			if c is Dictionary and c.has("id"):
				cards[c["id"]] = c


## Hotspots as the Level merges them: scene.json first, explore_hotspots.json only adds new names.
static func _hotspots(env_dir: String) -> Dictionary:
	var out := {}
	var m = _json(env_dir + "/scene.json")
	if m is Dictionary and m.get("hotspots") is Dictionary:
		out.merge(m["hotspots"])
	var x = _json(env_dir + "/explore_hotspots.json")
	if x is Dictionary and x.get("hotspots") is Dictionary:
		out.merge(x["hotspots"], false)
	return out


static func _c3_scene(scene_id: String) -> bool:
	return LEVELS.has(scene_id)


func _c3_speakers() -> Dictionary:
	var out := {}   # id -> first place that needs it (dialogue, reaction, chat, NPC)
	for q in data["quests"]["quests"]:
		if not _c3_scene(q["scene"]):
			continue
		for o in q["objectives"]:
			if o["type"] != "dialogue":
				continue
			for conv in data["dialogue"]["conversations"]:
				if conv["id"] == o["dialogue_id"]:
					for n in conv["nodes"]:
						if not out.has(n["speaker"]):
							out[n["speaker"]] = "dialogue " + conv["id"]
	for oid in chapter["reactions"]:
		if str(oid).begins_with("c4"):     # Chapter 4 speakers belong to the C4 streams' own tests (C4_DESIGN §5)
			continue
		for cid in chapter["reactions"][oid]:
			for v in chapter["reactions"][oid][cid]:
				if not out.has(str(v.get("speaker"))):
					out[str(v.get("speaker"))] = "reaction %s/%s" % [oid, cid]
	for id in entries:
		if str(entries[id].get("level", "")) in LEVELS:
			for line in entries[id].get("lines", []):
				if line is Dictionary and not out.has(str(line.get("speaker"))):
					out[str(line.get("speaker"))] = "chat " + id
	for lid in level_nodes:
		for n in level_nodes[lid]:
			if n.has("char_id") and not out.has(n["char_id"]):
				out[n["char_id"]] = "NPC %s in %s" % [n["name"], lid]
	return out


# ------------------------------------------------------------------ cases
func _environments() -> bool:
	for env in ENVS:
		var dir: String = "res://assets/environments/" + str(env)
		var spec: Dictionary = ENVS[env]
		var m = _json(dir + "/scene.json")
		if not kit.ok(m is Dictionary, "%s/scene.json missing or not valid JSON" % dir):
			continue
		kit.ok(not m.has("placeholder"), "%s/scene.json still carries the \"placeholder\" key (final art missing)" % dir)
		kit.eq(m.get("world_size"), [1920, 360], "%s world size (C3_DESIGN §4)" % env)
		kit.ok(m.get("layers") is Array and not m["layers"].is_empty(), "%s: no art layers" % env)
		var missing_files: Array = []
		for section in ["layers", "props", "fx"]:
			for L in m.get(section, []):
				if L is Dictionary and L.has("file") and not FileAccess.file_exists(dir + "/" + str(L["file"])):
					missing_files.append("%s/%s" % [section, L["file"]])
		kit.eq(missing_files, [], "%s: files named by scene.json that do not exist" % env)
		for a in m.get("actors", []):
			kit.ok(a is Dictionary and ResourceLoader.exists(str(a.get("scene", ""))), "%s: actor scene %s exists" % [env, Kit.fmt(a)])
		var poly := PackedVector2Array()
		for p in m.get("walkable", []):
			poly.append(Vector2(p[0], p[1]))
		kit.ok(poly.size() >= 3, "%s: walkable polygon" % env)
		var hs := _hotspots(dir)
		var missing: Array = []
		var outside: Array = []
		for name in spec["hotspots"]:
			if not hs.has(name):
				missing.append(name)
			elif poly.size() >= 3 and not Geometry2D.is_point_in_polygon(Vector2(hs[name][0], hs[name][1]), poly):
				outside.append("%s %s" % [name, hs[name]])
		kit.eq(missing, [], "%s: hotspots required by C3_DESIGN §4 missing" % env)
		kit.eq(outside, [], "%s: hotspots outside the walkable polygon" % env)
		var sp = m.get("spawns", {}).get(spec["spawn"])
		if kit.ok(sp is Array and sp.size() == 2, "%s: spawn %s present" % [env, spec["spawn"]]):
			kit.ok(poly.size() < 3 or Geometry2D.is_point_in_polygon(Vector2(sp[0], sp[1]), poly), "%s: spawn %s inside the walkable polygon" % [env, spec["spawn"]])
		# every hotspot a node of the level snaps to exists
		var unknown: Array = []
		for n in level_nodes.get(spec["level"], []):
			if n.has("hotspot_id") and not hs.has(n["hotspot_id"]):
				unknown.append("%s → %s" % [n["name"], n["hotspot_id"]])
		kit.eq(unknown, [], "%s: level nodes snap to hotspots the manifest does not define" % spec["level"])
	return true


func _characters() -> bool:
	var need := _c3_speakers()
	kit.ok(need.size() >= 9, "Chapter-3 characters collected (%d)" % need.size())
	for id in Kit.sorted(need):
		var dir: String = "res://assets/characters/%s" % id
		var sheet = _json(dir + "/sheet.json")
		var portrait = _json(dir + "/portrait.json")
		var why: String = need[id]
		if kit.ok(sheet is Dictionary, "%s/sheet.json missing (needed by %s)" % [dir, why]):
			kit.ok(FileAccess.file_exists(dir + "/sheet.png"), "%s/sheet.png missing" % dir)
			kit.ok(sheet.get("cell") is Array and sheet.get("origin") is Array and sheet.get("anims") is Dictionary, "%s/sheet.json: cell, origin, anims" % dir)
			var anims: Dictionary = sheet.get("anims", {}) if sheet.get("anims") is Dictionary else {}
			kit.ok(anims.has("idle_side") and anims.has("talk_side"), "%s/sheet.json: idle_side and talk_side rows (TECHNICAL_ARCHITECTURE §4)" % dir)
		if kit.ok(portrait is Dictionary, "%s/portrait.json missing (needed by %s)" % [dir, why]):
			kit.ok(FileAccess.file_exists(dir + "/portrait.png"), "%s/portrait.png missing" % dir)
			kit.eq(portrait.get("size"), [112, 112], "%s/portrait.json size" % dir)
			var have: Array = portrait.get("expressions", []) if portrait.get("expressions") is Array else []
			kit.eq(EXPRESSIONS.filter(func(e: String) -> bool: return not have.has(e)), [], "%s/portrait.json: expressions missing" % dir)
	# every expression the chapter uses for a speaker exists in that speaker's portrait
	var used := {}
	for q in data["quests"]["quests"]:
		if not _c3_scene(q["scene"]):
			continue
		for o in q["objectives"]:
			if o["type"] == "dialogue":
				for conv in data["dialogue"]["conversations"]:
					if conv["id"] == o["dialogue_id"]:
						for n in conv["nodes"]:
							used["%s|%s" % [n["speaker"], chapter["line_expr"].get(n["id"], "neutral")]] = n["id"]
	for key in Kit.sorted(used):
		var sp: String = key.get_slice("|", 0)
		var ex: String = key.get_slice("|", 1)
		var p = _json("res://assets/characters/%s/portrait.json" % sp)
		if p is Dictionary:
			kit.ok((p.get("expressions", []) as Array).has(ex), "portrait of %s lacks expression %s (line %s)" % [sp, ex, used[key]])
	return true


func _documents() -> bool:
	var index := {}
	var d := DirAccess.open(DOCS_DIR)
	if d != null:
		for f in d.get_files():
			if f.ends_with("_documents.json"):
				var doc = _json(DOCS_DIR + f)
				if not kit.ok(doc is Dictionary and doc.get("documents") is Array, "%s%s is a documents manifest" % [DOCS_DIR, f]):
					continue
				for e in doc["documents"]:
					if e is Dictionary and e.get("item_id") != null:
						index[str(e["item_id"])] = [e, f]
	for it in data["items"]["items"]:
		if not _c3_scene(it["scene"]):
			continue
		var hit = index.get(it["id"])
		if not kit.ok(hit != null, "no document for Chapter-3 item %s (item_id in assets/ui/documents/*_documents.json)" % it["id"]):
			continue
		var e: Dictionary = hit[0]
		var png: String = DOCS_DIR + str(e.get("id", "")) + ".png"
		kit.ok(FileAccess.file_exists(png), "%s: document image %s missing (InspectView loads <id>.png)" % [it["id"], png])
		if e.has("file"):
			kit.ok(FileAccess.file_exists(str(e["file"])), "%s: file %s missing (%s)" % [it["id"], e["file"], hit[1]])
		if e.has("alt_key"):
			kit.ok(loc.has(str(e["alt_key"])), "%s: alt text %s has no German string" % [it["id"], e["alt_key"]])
	return true


func _cinematics() -> bool:
	var contexts := _cinematic_contexts()
	for cid in chapter["cinematics"]:
		var path := str(chapter["cinematics"][cid])
		if (PENDING_R8.has(cid) or PENDING_R9.has(cid)) and not ResourceLoader.exists(path):
			print("      pending (round 9): %s -> %s" % [cid, path])
			continue
		if not kit.ok(ResourceLoader.exists(path), "%s: cinematic scene %s missing" % [cid, path]):
			continue
		var packed = load(path)
		if not kit.ok(packed is PackedScene, "%s: %s is a scene" % [cid, path]):
			continue
		for ctx in contexts:
			var cin: Node = (packed as PackedScene).instantiate()
			var label := "%s (%s)" % [cid, ctx["label"]]
			kit.ok(cin is Node2D, label + ": root is a Node2D (§12.5)")
			var api := true
			for m in ["configure", "play", "skip"]:
				api = kit.ok(cin.has_method(m), "%s: root has %s()" % [label, m]) and api
			api = kit.ok(cin.has_signal("finished"), label + ": root has signal finished") and api
			if not api:
				cin.free()
				break
			var count := [0]
			cin.finished.connect(func() -> void: count[0] += 1)
			kit.mount(cin)
			cin.configure({"choices": ctx["choices"], "flags": ctx["flags"], "symbols": ctx["symbols"]})
			cin.play()
			cin.skip()
			kit.eq(count[0], 1, label + ": skip() emits finished (synchronously)")
			cin.skip()
			kit.eq(count[0], 1, label + ": a second skip() does not emit finished again")
			cin.free()
	return true


## Story contexts the cinematics are configured with: two opposite playthroughs (and both symbol settings).
func _cinematic_contexts() -> Array:
	var out: Array = []
	for spec in [{"a1": "share_with_irina", "m1": "preserve_evidence", "c3a": "ask_elena", "c3b": "share_protocol", "symbols": true},
			{"a1": "keep_private", "m1": "request_explanation", "c3a": "note_alone", "c3b": "report_delegation", "symbols": false}]:
		var g := kit.story()
		kit.play_until(g, "c3b", spec)
		out.append({"label": "%s/%s/%s/%s" % [spec["a1"], spec["m1"], spec["c3a"], spec["c3b"]], "choices": g.choice_history(),
			"flags": g.flags(), "symbols": spec["symbols"]})
		g.free()
	return out


func _puzzle_ui() -> bool:
	for oid in chapter["puzzles"]:
		var path := str(chapter["puzzles"][oid])
		if (PENDING_R8.has(oid) or PENDING_R9.has(oid)) and not ResourceLoader.exists(path):
			print("      pending (round 9): %s -> %s" % [oid, path])
			continue
		if not kit.ok(ResourceLoader.exists(path), "%s: puzzle UI scene %s missing" % [oid, path]):
			continue
		var node: Node = (load(path) as PackedScene).instantiate()
		kit.ok(node.has_method("open"), "%s: %s has open(obj_id)" % [oid, path])
		kit.ok(node.has_signal("solved"), "%s: %s has signal solved" % [oid, path])
		node.free()
	return true


func _explore_entries() -> bool:
	for f in ["veltrava_station.json", "veltrava_hall.json", "c3_history_soviet.json", "c3_history_reich.json"]:
		kit.ok(FileAccess.file_exists(EXPLORE_DIR + f), "%s%s missing (C3_DESIGN §6)" % [EXPLORE_DIR, f])
	var per_level := {}
	for id in entries:
		if not (str(entry_file[id]).begins_with("veltrava_") or EXTRA_ENTRY_FILES.has(str(entry_file[id]))):
			continue
		var e: Dictionary = entries[id]
		var lvl := str(e.get("level", ""))
		if str(entry_file[id]).begins_with("veltrava_"):
			per_level[lvl] = per_level.get(lvl, 0) + 1
		kit.ok(KINDS.has(e.get("kind")), "%s: kind %s is one of %s" % [id, Kit.fmt(e.get("kind")), KINDS])
		if P2_LEVELS.has(lvl):
			kit.ok(str(id).begins_with("veltrava.%s." % P2_LEVELS[lvl]), "%s: id follows veltrava.%s.<name>" % [id, P2_LEVELS[lvl]])
			continue
		if not kit.ok(LEVELS.has(lvl), "%s: level %s is a Chapter-3 level %s" % [id, Kit.fmt(lvl), LEVELS.keys() + P2_LEVELS.keys()]):
			continue
		kit.ok(str(id).begins_with("veltrava.%s." % LEVELS[lvl]), "%s: id follows veltrava.%s.<name>" % [id, LEVELS[lvl]])
		kit.eq(e.get("area"), "veltrava", "%s: area" % id)
		var keys := ["title_key", "prompt_key"] + ([] if e.get("kind") == "chat" else ["text_key"])
		for k in keys:
			kit.ok(e.has(k) and loc.has(str(e[k])) and loc.t(str(e[k])).strip_edges() != "", "%s: %s %s resolves" % [id, k, Kit.fmt(e.get(k))])
		if e.get("kind") == "chat" and e.has("text_key"):
			kit.ok(loc.has(str(e["text_key"])), "%s: text_key resolves" % id)
		if e.has("image"):
			kit.ok(ResourceLoader.exists(str(e["image"])) or FileAccess.file_exists(str(e["image"])), "%s: image %s exists" % [id, e["image"]])
		for cid in e.get("history", []):
			var card = cards.get(cid)
			if kit.ok(card is Dictionary, "%s: history card %s exists in data/explore/*.json" % [id, cid]):
				var sources = card.get("sources", [])
				kit.ok(sources is Array and not sources.is_empty(), "card %s has at least one source" % cid)
				for s in (sources if sources is Array else []):
					var url := str(s.get("url", "")) if s is Dictionary else ""
					kit.ok(s is Dictionary and str(s.get("label", "")).strip_edges() != "", "card %s: source %s has a label" % [cid, Kit.fmt(s)])
					kit.ok(url == "" or url.begins_with("https://") or url.begins_with("http://"), "card %s: source url %s is a web address (or empty for print sources)" % [cid, url])
				for k in ["title_key", "text_key"]:
					kit.ok(loc.has(str(card.get(k, ""))), "card %s: %s resolves" % [cid, k])
		if e.get("kind") == "chat":
			var lines = e.get("lines", [])
			kit.ok(lines is Array and not lines.is_empty(), "%s: chat has lines" % id)
			for line in (lines if lines is Array else []):
				var sp := str(line.get("speaker", "")) if line is Dictionary else ""
				kit.ok(sp in data["flags"]["protagonists"] or loc.has("char.%s.name" % sp) or DirAccess.dir_exists_absolute("res://assets/characters/" + sp),
					"%s: chat speaker %s is a known character" % [id, Kit.fmt(sp)])
				kit.ok(line is Dictionary and loc.has(str(line.get("key", ""))), "%s: chat line key %s resolves" % [id, Kit.fmt(line.get("key") if line is Dictionary else line)])
				if line is Dictionary and line.has("expr"):
					kit.ok(EXPRESSIONS.has(line["expr"]), "%s: chat expression %s" % [id, line["expr"]])
		elif e.has("lines"):
			kit.fail("%s: only chat entries carry lines" % id)
	for lvl in ENTRY_COUNTS:
		kit.eq(per_level.get(lvl, 0), ENTRY_COUNTS[lvl], "exploration entries in %s (C3_DESIGN §6)" % lvl)
	# the three new real-history cards: sober, sourced, 450–800 characters, found where §6 places them
	for cid in HISTORY_AT:
		var card = cards.get(cid)
		if not kit.ok(card is Dictionary, "history card %s missing (data/explore/c3_history_<side>.json)" % cid):
			continue
		var n: int = loc.t(str(card.get("text_key", ""))).length()
		kit.ok(n >= 450 and n <= 800, "card %s text length %d within 450–800" % [cid, n])
		var placed := false
		for lid in level_nodes:
			for node in level_nodes[lid]:
				if node.get("hotspot_id") == HISTORY_AT[cid] and entries.get(node.get("explore_id", ""), {}).get("history", []).has(cid):
					placed = true
		kit.ok(placed, "card %s is unlocked by the find at %s" % [cid, HISTORY_AT[cid]])
	return true


func _explore_interactables() -> bool:
	var placed := {}
	for lid in level_nodes:
		var hs := _hotspots("res://assets/environments/" + ("veltrava_station" if lid == "L_C3_Station" else "veltrava_hall"))
		var n_found := 0
		for n in level_nodes[lid]:
			var kind := str(n.get("kind", ""))
			if kind != "discover" and kind != "chat":
				continue
			n_found += 1
			var xid := str(n.get("explore_id", ""))
			placed[xid] = placed.get(xid, []) + ["%s/%s" % [lid, n["name"]]]
			if kit.ok(entries.has(xid), "%s/%s: explore entry %s does not exist" % [lid, n["name"], xid]):
				kit.eq(entries[xid].get("level"), lid, "%s/%s: entry %s belongs to this level" % [lid, n["name"], xid])
				kit.eq(entries[xid].get("kind") == "chat", kind == "chat", "%s/%s: interactable kind %s matches entry kind %s" % [lid, n["name"], kind, entries[xid].get("kind")])
			kit.ok(hs.has(str(n.get("hotspot_id", ""))), "%s/%s: hotspot %s exists in the environment" % [lid, n["name"], n.get("hotspot_id")])
		kit.ok(n_found > 0, "%s has discover/chat interactables" % lid)
	for xid in placed:
		kit.eq(placed[xid].size(), 1, "explore entry %s placed by exactly one interactable %s" % [xid, placed[xid]])
	for id in entries:
		if str(entry_file[id]).begins_with("veltrava_") or EXTRA_ENTRY_FILES.has(str(entry_file[id])):
			kit.ok(placed.has(id), "veltrava entry %s is placed by an interactable" % id)
	return true
