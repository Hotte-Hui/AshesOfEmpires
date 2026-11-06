extends RefCounted
## Memories („Erinnerungen“, TECHNICAL_ARCHITECTURE §12.10): travel back into completed scenes.
## Pure data/logic helper of the scene director — Game owns one instance (`Game.memories`); it never changes
## Story state:
##  * memory scene table (story order): every walkable scene of data/v3/scenes.json (protagonist ≠ none, with an
##    exit_on_event) plus the optional side levels of SIDE_LEVELS, which unlock together with their parent scene
##  * unlock rules: in the game a scene is a memory once its exit event happened in the live Story state
##    (Story.has_event(exit_on_event)); from the main menu, once it was ever completed (global profile)
##  * the global profile `user://profile.json` (NOT part of any save): per completed scene the Story state at the
##    moment of completion, and the union of every exploration find recorded with it (for main-menu memories)
##  * read-only "echo" plans for story hotspots inside a memory (documents, replayed dialogue lines, what was
##    decided) and the memory colour grade (an overlay on the level grade)
## Profile format (version 1, written atomically like the save slots):
##   {"version": 1, "completed": {"<scene id>": {"t": unix seconds, "story": <Story.save_json() object>}},
##    "explore": {"found": [ids], "cards": [ids]}}

const ENGINE := preload("res://scripts/story/story_engine.gd")
const SAVES := preload("res://scripts/core/save_system.gd")

const PROFILE_PATH := "user://profile.json"
const PROFILE_VERSION := 1
const MAX_PROFILE_BYTES := 1024 * 1024
const SCENES_PATH := "res://data/v3/scenes.json"
const QUESTS_PATH := "res://data/v3/quests.json"
const DIALOGUE_PATH := "res://data/v3/dialogue.json"
const THUMB_DIR := "res://assets/ui/memories/"
## Walkable levels outside the Story scene chain: {id: {parent, protagonist, spawn}} — unlocked with the parent.
const SIDE_LEVELS := {"L_M1_Plaza": {"parent": "L_M1_Archive", "protagonist": "konrad", "spawn": "SP_Plaza_Start"}}
## Interactable kinds that belong to the Story engine (never called inside a memory).
const STORY_KINDS := ["inspect", "dialogue", "puzzle", "choice"]
## Grade fields written by Game._apply_grade (vectors and numbers).
const GRADE_VEC := ["lift", "gamma", "gain", "tint"]
const GRADE_NUM := ["saturation", "vignette", "grain"]

var path := PROFILE_PATH
var data: Dictionary = {}
## Last problem found while reading the profile ("" = fine). A broken profile is never fatal.
var last_error := ""
var _scenes: Array = []
var _objectives: Dictionary = {}
var _conversations: Dictionary = {}


func _init(profile_path := PROFILE_PATH) -> void:
	path = profile_path
	data = _empty()


static func _empty() -> Dictionary:
	return {"version": PROFILE_VERSION, "completed": {}, "explore": {"found": [], "cards": []}}


static func _json(p: String):
	if not FileAccess.file_exists(p):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(p))


static func _loc() -> Node:
	var ml := Engine.get_main_loop() as SceneTree
	return ml.root.get_node_or_null("Loc") if ml != null and ml.root != null else null


static func has_text(key: String) -> bool:
	var l := _loc()
	return l != null and l.has_method("has") and bool(l.has(key))


static func text(key: String, args: Dictionary = {}) -> String:
	var l := _loc()
	if l != null and l.has_method("t"):
		return str(l.t(key, args))
	return key.format(args) if not args.is_empty() else key


# ================================================================ scene table
## [{id, unlock, protagonist, chapter_key, title_key, spawn, side, parent, thumb, order}] in story order.
func scenes() -> Array:
	if not _scenes.is_empty():
		return _scenes
	var sd = _json(SCENES_PATH)
	var qd = _json(QUESTS_PATH)
	var quest_title := {}
	if qd is Dictionary:
		for q in qd.get("quests", []):
			if q is Dictionary:
				quest_title[str(q.get("scene", ""))] = str(q.get("title_key", ""))
	if not (sd is Dictionary):
		return _scenes
	var chapters: Array = []   # distinct quest titles in story order = chapter numbers (both C3 halves share one)
	for s in sd.get("scenes", []):
		if not (s is Dictionary):
			continue
		var who := str(s.get("protagonist", ""))
		var ev = s.get("exit_on_event")
		if who in ["", "none"] or not (ev is String) or str(ev) == "":
			continue
		var id := str(s.get("id", ""))
		var ck := str(quest_title.get(id, ""))
		if ck != "" and not chapters.has(ck):
			chapters.append(ck)
		var no := chapters.find(ck) + 1
		_scenes.append({"id": id, "unlock": str(ev), "protagonist": who, "chapter_key": ck, "chapter_no": no,
			"title_key": str(s.get("title_key", "")), "spawn": "", "side": false, "parent": "",
			"thumb": THUMB_DIR + id + ".png", "order": _scenes.size()})
		for side in SIDE_LEVELS:
			var sl: Dictionary = SIDE_LEVELS[side]
			if str(sl.get("parent", "")) == id:
				_scenes.append({"id": side, "unlock": str(ev), "protagonist": str(sl.get("protagonist", who)),
					"chapter_key": ck, "chapter_no": no, "title_key": "", "spawn": str(sl.get("spawn", "")),
					"side": true, "parent": id, "thumb": THUMB_DIR + side + ".png", "order": _scenes.size()})
	return _scenes


func scene(id: String) -> Dictionary:
	for s in scenes():
		if s["id"] == id:
			return s
	return {}


func is_memory_scene(id: String) -> bool:
	return not scene(id).is_empty()


## Place shown on cards / the travel card ("Verladebahnhof Karsk").
func place(id: String) -> String:
	if has_text("ui.memories.place." + id):
		return text("ui.memories.place." + id)
	var s := scene(id)
	return text(str(s["title_key"])) if s.has("title_key") and str(s["title_key"]) != "" else id


## Date line ("Karsk · Januar 1964"), "" when none is authored.
func date_line(id: String) -> String:
	return text("ui.memories.date." + id) if has_text("ui.memories.date." + id) else ""


## Chapter kicker ("Kapitel 1 · Das letzte Signal"), "" when the scene has no quest.
func chapter_line(id: String) -> String:
	var s := scene(id)
	if s.is_empty() or str(s.get("chapter_key", "")) == "":
		return ""
	return text("ui.memories.chapter", {"n": int(s.get("chapter_no", 0)), "title": text(str(s["chapter_key"]))})


## Unlocked in the running game: the scene's exit event happened in the live Story state.
func unlocked_by_story(id: String, story: Object) -> bool:
	var s := scene(id)
	if s.is_empty() or story == null or not story.has_method("has_event"):
		return false
	return bool(story.has_event(str(s["unlock"])))


## Unlocked from the main menu: completed at least once (any playthrough).
func unlocked_by_profile(id: String) -> bool:
	return (data.get("completed", {}) as Dictionary).has(id)


# ================================================================ profile
func any() -> bool:
	return not (data.get("completed", {}) as Dictionary).is_empty()


func completed_ids() -> Array:
	var out: Array = []
	for s in scenes():
		if unlocked_by_profile(str(s["id"])):
			out.append(s["id"])
	return out


func load_profile() -> void:
	data = _empty()
	last_error = ""
	if not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		last_error = "cannot open " + path
		return
	if f.get_length() > MAX_PROFILE_BYTES:
		f.close()
		last_error = "profile too large"
		return
	var raw := f.get_buffer(f.get_length()).get_string_from_utf8()
	f.close()
	var parsed: Dictionary = ENGINE.json_parse(raw)
	var d = parsed.get("value") if parsed.get("ok", false) else null
	if not (d is Dictionary) or typeof(d.get("version")) != TYPE_INT or int(d["version"]) != PROFILE_VERSION:
		last_error = "unsupported or malformed profile"
		return
	var comp = d.get("completed", {})
	if comp is Dictionary:
		for id in comp:
			var e = comp[id]
			if e is Dictionary and e.get("story") is Dictionary and is_memory_scene(str(id)):
				data["completed"][str(id)] = {"t": float(e.get("t", 0.0)) if (e.get("t") is float or e.get("t") is int) else 0.0,
					"story": e["story"]}
	var ex = d.get("explore", {})
	if ex is Dictionary:
		merge_explore(ex)


func save_profile() -> bool:
	var w: Dictionary = SAVES._write_atomic(path, ENGINE.json_dumps(data, 1))
	if not w.get("ok", false):
		last_error = str(w.get("error", ""))
		push_warning("Memories: profile not written: " + last_error)
		return false
	return true


## Records the Story state (Story.save_json() text) at the completion of `id` (and of its side levels).
## Returns true when the profile changed. Does not write the file (save_profile()).
func record(id: String, story_raw: String) -> bool:
	if not is_memory_scene(id):
		return false
	var parsed: Dictionary = ENGINE.json_parse(story_raw)
	if not parsed.get("ok", false) or not (parsed["value"] is Dictionary):
		return false
	var entry := {"t": snappedf(Time.get_unix_time_from_system(), 0.001), "story": parsed["value"]}
	data["completed"][id] = entry
	for side in SIDE_LEVELS:
		if str(SIDE_LEVELS[side].get("parent", "")) == id:
			data["completed"][side] = entry.duplicate(true)
	return true


## Adds every memory scene completed in `story_raw` that the profile does not know yet (saves from before this
## feature, loaded saves). Existing entries (recorded at the moment of completion) are never replaced.
func seed_from_story(story_raw: String) -> int:
	var parsed: Dictionary = ENGINE.json_parse(story_raw)
	if not parsed.get("ok", false) or not (parsed["value"] is Dictionary):
		return 0
	var events = parsed["value"].get("completed_events", [])
	if not (events is Array):
		return 0
	var n := 0
	for s in scenes():
		var id := str(s["id"])
		if not unlocked_by_profile(id) and (events as Array).has(str(s["unlock"])):
			data["completed"][id] = {"t": snappedf(Time.get_unix_time_from_system(), 0.001), "story": parsed["value"]}
			n += 1
	return n


## Story state text (save_json format) recorded for `id`, "" when unknown.
func snapshot_raw(id: String) -> String:
	var e = (data.get("completed", {}) as Dictionary).get(id)
	if not (e is Dictionary) or not (e.get("story") is Dictionary):
		return ""
	return ENGINE.json_dumps(e["story"], 2)


## Flags that were true while the scene was played: the profile snapshot of the scene when it belongs to the
## running playthrough (its decisions agree with the live ones), else the live flags. Keeps flag-dependent line
## variants of a replayed dialogue as they were spoken (a later choice may have changed a flag since).
func memory_flags(id: String, live_flags: Dictionary, live_choices: Dictionary) -> Dictionary:
	var e = (data.get("completed", {}) as Dictionary).get(id)
	if not (e is Dictionary) or not (e.get("story") is Dictionary):
		return live_flags
	var st: Dictionary = e["story"]
	var ch = st.get("choice_history", {})
	var fl = st.get("flags", {})
	if not (ch is Dictionary) or not (fl is Dictionary):
		return live_flags
	for k in ch:
		if str(live_choices.get(k, "")) != str(ch[k]):
			return live_flags
	return fl


func explore_state() -> Dictionary:
	var ex: Dictionary = data.get("explore", {})
	return {"found": (ex.get("found", []) as Array).duplicate(), "cards": (ex.get("cards", []) as Array).duplicate()}


## Union with an Explore.state() dictionary (order kept, new ids appended). Returns true when something was added.
func merge_explore(st) -> bool:
	if not (st is Dictionary):
		return false
	var changed := false
	var ex: Dictionary = data["explore"]
	for k in ["found", "cards"]:
		var dst: Array = ex.get(k, [])
		var src = st.get(k, [])
		if src is Array:
			for id in src:
				if (id is String or id is StringName) and not dst.has(str(id)):
					dst.append(str(id))
					changed = true
		ex[k] = dst
	return changed


func clear() -> void:
	data = _empty()


# ================================================================ echo plans (story hotspots inside a memory)
func _objective(oid: String) -> Dictionary:
	if _objectives.is_empty():
		var qd = _json(QUESTS_PATH)
		if qd is Dictionary:
			for q in qd.get("quests", []):
				for o in q.get("objectives", []):
					if o is Dictionary:
						_objectives[str(o.get("id", ""))] = o
	return _objectives.get(oid, {})


func _conversation(did: String) -> Dictionary:
	if _conversations.is_empty():
		var dd = _json(DIALOGUE_PATH)
		if dd is Dictionary:
			for c in dd.get("conversations", []):
				if c is Dictionary:
					_conversations[str(c.get("id", ""))] = c
	return _conversations.get(did, {})


## Objective ids of `ids` in quest order (a hotspot that unites a dialogue with the decision taken there).
func in_quest_order(ids: Array) -> Array:
	var order := []
	var qd = _json(QUESTS_PATH)
	if qd is Dictionary:
		for q in qd.get("quests", []):
			for o in q.get("objectives", []):
				if ids.has(str(o.get("id", ""))):
					order.append(str(o["id"]))
	for id in ids:
		if not order.has(str(id)):
			order.append(str(id))
	return order


## Read-only plan of what a story hotspot shows inside a memory. `objective_ids`: the hotspot's objectives (any
## order). ctx = {protagonist, choices (Story.choice_history()), flags, ext (ChapterExt or null),
## reactions ({objective: {choice: [speaker, key, expr]}}), line_expr ({node: expr})}.
## Steps: {"type": "line", "speaker", "key", "text", "expr"} | {"type": "inspect", "item"}.
func echo_plan(objective_ids: Array, ctx: Dictionary) -> Array:
	var steps: Array = []
	var me := str(ctx.get("protagonist", "alexei"))
	var flags: Dictionary = ctx.get("flags", {}) if ctx.get("flags") is Dictionary else {}
	var ext = ctx.get("ext")
	for oid in in_quest_order(objective_ids):
		var o := _objective(str(oid))
		match str(o.get("type", "")):
			"inspect":
				var item := str(o.get("grant_item", ""))
				if item != "":
					steps.append({"type": "inspect", "item": item})
				else:
					steps.append(_line(me, "ui.memories.echo.inspect", {}, "neutral"))
			"dialogue":
				steps.append_array(_dialogue_steps(o, flags, ext, ctx.get("line_expr", {})))
			"choice":
				steps.append_array(_choice_steps(str(oid), o, me, ctx, flags, ext))
			"puzzle":
				var k := "ui.memories.echo." + str(oid)
				steps.append(_line(me, k if has_text(k) else "ui.memories.echo.puzzle",
					{"task": text(str(o.get("text_key", "")))}, "neutral"))
	return steps


func _line(speaker: String, key: String, args: Dictionary, expr: String) -> Dictionary:
	return {"type": "line", "speaker": speaker, "key": key, "text": text(key, args), "expr": expr}


func _dialogue_steps(o: Dictionary, flags: Dictionary, ext, line_expr) -> Array:
	var out: Array = []
	var conv := _conversation(str(o.get("dialogue_id", "")))
	var nodes := {}
	for n in conv.get("nodes", []):
		if n is Dictionary:
			nodes[str(n.get("id", ""))] = n
	var cur := str(conv.get("entry_node", ""))
	var guard := 0
	while cur != "" and nodes.has(cur) and guard < 64:
		guard += 1
		var n: Dictionary = nodes[cur]
		var key := str(n.get("text_key", ""))
		if ext != null and ext.has_method("line_key"):
			key = str(ext.line_key(cur, key, flags))
		var expr := "neutral"
		if line_expr is Dictionary and (line_expr as Dictionary).has(cur):
			expr = str(line_expr[cur])
		elif ext != null and ext.has_method("expr_for"):
			expr = str(ext.expr_for(cur))
		out.append(_line(str(n.get("speaker", "")), key, {}, expr))
		if bool(n.get("end", false)):
			break
		cur = str(n.get("next", "")) if n.get("next") != null else ""
	return out


func _choice_steps(oid: String, o: Dictionary, me: String, ctx: Dictionary, flags: Dictionary, ext) -> Array:
	var out: Array = []
	var choices: Dictionary = ctx.get("choices", {}) if ctx.get("choices") is Dictionary else {}
	var cid := str(choices.get(oid, ""))
	if cid == "":
		out.append(_line(me, "ui.memories.decided_none", {}, "neutral"))
		return out
	var dk := "ui.memories.decided." + cid
	if has_text(dk):
		out.append(_line(me, dk, {}, "concerned"))
	else:
		var ctext := cid
		for c in o.get("choices", []):
			if c is Dictionary and str(c.get("id", "")) == cid:
				ctext = text(str(c.get("text_key", "")))
		if ext != null and ext.has_method("choice_options"):
			var opts: Array = ext.choice_options(oid, [{"id": cid, "text": ctext}], flags)
			if not opts.is_empty():
				ctext = str(opts[0].get("text", ctext))
		out.append(_line(me, "ui.memories.decided", {"choice": ctext.trim_suffix(".")}, "concerned"))
	var react: Array = []
	var table = ctx.get("reactions", {})
	if table is Dictionary and table.get(oid, {}) is Dictionary:
		react = table.get(oid, {}).get(cid, [])
	if react.is_empty() and ext != null and ext.has_method("reaction"):
		react = ext.reaction(oid, cid, flags)
	if react.size() == 3:
		out.append(_line(str(react[0]), str(react[1]), {}, str(react[2])))
	return out


# ================================================================ memory grade
## Level grade (data/grades.json preset) → the same grade seen as a memory. The "memory" preset is an overlay:
## lift adds, gamma/gain/tint multiply, saturation multiplies, vignette = max(level, preset), grain adds,
## palette and palette_strength stay the level's (pixel-art palette snap unchanged).
static func overlay_grade(base: Dictionary, mem: Dictionary) -> Dictionary:
	var out := base.duplicate(true)
	if mem.is_empty():
		return out
	for k in GRADE_VEC:
		var b: Array = base.get(k, [0.0, 0.0, 0.0] if k == "lift" else [1.0, 1.0, 1.0])
		var m: Array = mem.get(k, [0.0, 0.0, 0.0] if k == "lift" else [1.0, 1.0, 1.0])
		var v: Array = []
		for i in 3:
			v.append(float(b[i]) + float(m[i]) if k == "lift" else float(b[i]) * float(m[i]))
		out[k] = v
	out["saturation"] = float(base.get("saturation", 1.0)) * float(mem.get("saturation", 1.0))
	out["vignette"] = maxf(float(base.get("vignette", 0.22)), float(mem.get("vignette", 0.0)))
	out["grain"] = float(base.get("grain", 0.0)) + float(mem.get("grain", 0.0))
	return out


## Shader values of a grade dictionary (as Game._apply_grade writes them; grain without the pixel_post factor).
static func grade_values(g: Dictionary) -> Dictionary:
	var out := {}
	for k in GRADE_VEC:
		var v: Array = g.get(k, [0.0, 0.0, 0.0] if k == "lift" else [1.0, 1.0, 1.0])
		out[k] = Vector3(float(v[0]), float(v[1]), float(v[2]))
	out["saturation"] = float(g.get("saturation", 1.0))
	out["vignette"] = float(g.get("vignette", 0.22))
	out["grain"] = float(g.get("grain", 0.0))
	return out


static func lerp_values(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var out := {}
	for k in a:
		if b.has(k):
			out[k] = lerp(a[k], b[k], t)
		else:
			out[k] = a[k]
	return out
