extends RefCounted
## Chapter extensions for the scene director (Chapter 3 onward; documentation/C3_DESIGN.md §3).
## Loads every data/chapters/*.json and answers the few questions game.gd cannot answer from its slice
## constants: level scenes, entry spawns, chapter cards, palettes/grades, per-line text variants and
## expressions, choice-option texts, reaction lines, puzzle UIs per objective and §12.5 cinematic scenes.
## It NEVER changes Story state: it only chooses which text key, expression, UI or cinematic presents a step
## the Story engine has already decided. Conditions (`when`) read Story flags:
##   {"irina_trust": ">=1", "office_suspicion": "==0", "c17_confirmed": true}  — all must hold.
## Lists of variants are ordered: the first matching entry wins; an entry without `when` always matches.

const DIR := "res://data/chapters/"

var levels: Dictionary = {}
var entry_spawn: Dictionary = {}
var chapter_cards: Dictionary = {}
var palettes: Dictionary = {}
var grades: Dictionary = {}
var line_expr: Dictionary = {}
var line_variants: Dictionary = {}
var choice_text: Dictionary = {}
var reactions: Dictionary = {}
var puzzles: Dictionary = {}
var cinematics: Dictionary = {}
var switches: Dictionary = {}           ## §12.11 per-scene settings of in-level protagonist switches (read-only here)
var looks: Dictionary = {}              ## round 8: scene -> {character id: look sheet dir} (C3P2 §6)
var carry: Dictionary = {}              ## round 8: scene -> {character id: item id held in the hand}
var files: Array = []
var _puzzle_nodes: Dictionary = {}

const SECTIONS := ["levels", "entry_spawn", "chapter_cards", "palettes", "grades", "line_expr", "line_variants",
	"choice_text", "reactions", "puzzles", "cinematics", "switches", "looks", "carry"]


func _init() -> void:
	reload()


func reload() -> void:
	for s in SECTIONS:
		(get(s) as Dictionary).clear()
	files.clear()
	var d := DirAccess.open(DIR)
	if d == null:
		return
	var names := Array(d.get_files())
	names.sort()
	for f in names:
		if not f.ends_with(".json"):
			continue
		var data = JSON.parse_string(FileAccess.get_file_as_string(DIR + f))
		if typeof(data) != TYPE_DICTIONARY:
			push_warning("ChapterExt: cannot parse " + f)
			continue
		files.append(DIR + f)
		for s in SECTIONS:
			var src = data.get(s, {})
			if src is Dictionary:
				(get(s) as Dictionary).merge(src, true)


# ------------------------------------------------------------------ conditions
static func compare(value, spec) -> bool:
	if spec is bool:
		return bool(value) == spec
	if spec is float or spec is int:
		return value != null and float(value) == float(spec)
	var s := str(spec).strip_edges()
	for op in [">=", "<=", "==", "!=", ">", "<"]:
		if s.begins_with(op):
			if value == null or typeof(value) == TYPE_BOOL:
				return false
			var a := float(value)
			var b := float(s.substr(op.length()).strip_edges())
			match op:
				">=":
					return a >= b
				"<=":
					return a <= b
				"==":
					return a == b
				"!=":
					return a != b
				">":
					return a > b
				"<":
					return a < b
	return str(value) == s


static func matches(when, flags: Dictionary) -> bool:
	if when == null or not (when is Dictionary) or (when as Dictionary).is_empty():
		return true
	for k in when:
		var key := str(k)
		var value = flags.get(key)
		if value == null and key.begins_with(CHOICE_PREFIX):
			value = live_choice(key.substr(CHOICE_PREFIX.length()))
		if not compare(value, when[k]):
			return false
	return true


## C3P2_DESIGN §3.2: a condition key "choice.<objective_id>" compares with the recorded choice id. A flags dictionary
## may carry it (tests, memories); otherwise the live Story answers. "" while the objective is not decided.
const CHOICE_PREFIX := "choice."


static func live_choice(objective_id: String) -> String:
	var ml := Engine.get_main_loop()
	var st = ml.root.get_node_or_null("/root/Story") if ml is SceneTree else null
	if st and st.has_method("choice_history"):
		return str(st.choice_history().get(objective_id, ""))
	return ""


func current_flags() -> Dictionary:
	var st = Engine.get_main_loop().root.get_node_or_null("/root/Story") if Engine.get_main_loop() else null
	if st and st.has_method("flags"):
		return st.flags()
	return {}


## First variant whose `when` holds (flags default to the live Story flags), else {}.
func pick(variants, flags = null) -> Dictionary:
	if not (variants is Array):
		return {}
	var f: Dictionary = flags if flags is Dictionary else current_flags()
	for v in variants:
		if v is Dictionary and matches(v.get("when"), f):
			return v
	return {}


# ------------------------------------------------------------------ director queries
func level_path(id: String) -> String:
	return str(levels.get(id, ""))


func spawn_for(id: String) -> String:
	return str(entry_spawn.get(id, ""))


func chapter_card(id: String) -> Array:
	var c = chapter_cards.get(id, [])
	return c if c is Array and c.size() == 2 else []


## C3P2_DESIGN §3.2 — shared level files: every Story scene played in level file `path`, in the order of the
## chapter files' "levels" section.
func scenes_of_level(path: String) -> Array:
	var out: Array = []
	if path == "":
		return out
	for id in levels:
		if str(levels[id]) == path:
			out.append(str(id))
	return out


## The identity of the level a Story scene plays in: the FIRST scene id mapped to the same level file (Explore
## entries of a shared level use it as "level"); the id itself when no chapter file maps it.
func level_key(id: String) -> String:
	var s := scenes_of_level(level_path(id))
	return str(s[0]) if not s.is_empty() else id


## True when both Story scenes play in the same chapter level file.
func same_level(a: String, b: String) -> bool:
	return level_path(a) != "" and level_path(a) == level_path(b)


## §12.11 in-level protagonist switch: the optional settings of Story scene `id` (a copy; {} when none) —
## switch_spawn, partner, partner_spawn, partner_anim, partner_hide_after, glide, music, ambience
## (meaning: TECHNICAL_ARCHITECTURE §12.11; game.gd decides, this only reads).
func switch_settings(id: String) -> Dictionary:
	var s = switches.get(id, {})
	return (s as Dictionary).duplicate(true) if s is Dictionary else {}


## Round 8: character looks of Story scene `id` ({character id: sheet dir}, a copy; {} = base sheets).
func looks_for(id: String) -> Dictionary:
	var l = looks.get(id, {})
	return (l as Dictionary).duplicate() if l is Dictionary else {}


## Round 8: items the characters of scene `id` hold once they own them ({character id: item id}, a copy).
func carry_for(id: String) -> Dictionary:
	var c = carry.get(id, {})
	return (c as Dictionary).duplicate() if c is Dictionary else {}


## Spawn where control passes to the protagonist of scene `id` at an in-level switch ("" = default rule).
func switch_spawn(id: String) -> String:
	return str(switch_settings(id).get("switch_spawn", ""))


func line_key(node_id: String, text_key: String, flags = null) -> String:
	var v := pick(line_variants.get(node_id, []), flags)
	return str(v.get("key", text_key)) if not v.is_empty() else text_key


func expr_for(node_id: String, fallback := "neutral") -> String:
	return str(line_expr.get(node_id, fallback))


## opts = [{id, text}] built from the Story choice data; replaces the text of options that have a variant.
func choice_options(objective_id: String, opts: Array, flags = null) -> Array:
	var table = choice_text.get(objective_id, {})
	if not (table is Dictionary) or table.is_empty():
		return opts
	var out: Array = []
	for o in opts:
		var x: Dictionary = (o as Dictionary).duplicate()
		var v := pick(table.get(str(x.get("id", "")), []), flags)
		if not v.is_empty() and v.has("key"):
			x["text"] = Loc.t(str(v["key"]))
		out.append(x)
	return out


## [speaker, text key, expression] for the line spoken after a choice, or [] when none is authored.
func reaction(objective_id: String, choice_id: String, flags = null) -> Array:
	var v := pick(reactions.get(objective_id, {}).get(choice_id, []), flags)
	if v.is_empty():
		return []
	return [str(v.get("speaker", "")), str(v.get("key", "")), str(v.get("expr", "neutral"))]


# ------------------------------------------------------------------ puzzle UIs
## The UI scene registered for this puzzle objective, instanced once under UIRoot (so it joins the modal
## stack like the slice puzzles). null when no chapter registers this objective.
func puzzle_ui(game: Node, objective_id: String) -> Node:
	var path := str(puzzles.get(objective_id, ""))
	if path == "" or not ResourceLoader.exists(path):
		return null
	var node = _puzzle_nodes.get(path)
	if node != null and is_instance_valid(node):
		return node
	node = load(path).instantiate()
	var root: Node = game.get("ui")
	if root:
		root.add_child(node)
		var toasts = root.get("toast_layer")
		if toasts is Node and toasts.get_parent() == root:
			root.move_child(node, (toasts as Node).get_index())
		if "ui_root" in node:
			node.set("ui_root", root)
	else:
		game.add_child(node)
	_puzzle_nodes[path] = node
	return node


# ------------------------------------------------------------------ §12.5 cinematics
func has_cinematic(id: String) -> bool:
	var p := str(cinematics.get(id, ""))
	return p != "" and ResourceLoader.exists(p)


## Plays a §12.5 cinematic scene (signal finished, configure(ctx), play(), skip()) inside the world viewport
## under Game.level_root. Returns true when the player skipped it. The level that was running stays loaded
## (hidden and paused) and is shown again only if the story scene did not change at the trigger.
func play_cinematic(game: Node, id: String) -> bool:
	if not has_cinematic(id):
		return false
	game._begin_cinematic()
	await game.fade_out(0.6)
	var prev: Node = game.level
	if prev and is_instance_valid(prev):
		prev.visible = false
		prev.process_mode = Node.PROCESS_MODE_DISABLED
	var cam: Camera2D = game.camera
	var cin: Node = load(str(cinematics[id])).instantiate()
	game.main.level_root.add_child(cin)
	if cin.has_method("configure"):
		cin.configure({"choices": Story.choice_history(), "flags": Story.flags(), "symbols": Symbols.enabled()})
	game._apply_grade(cin)
	var done := [false]
	if cin.has_signal("finished"):
		cin.finished.connect(func(): done[0] = true, CONNECT_ONE_SHOT)
	await game.fade_in(0.6)
	if cin.has_method("play"):
		cin.play()
	var limit := float(cin.get("max_duration")) if cin.get("max_duration") != null else 60.0
	var t := 0.0
	while not done[0] and t < limit:
		if game._skip:
			if cin.has_method("skip"):
				cin.skip()
			break
		await game.get_tree().process_frame
		t += game.get_process_delta_time()
	await game.fade_out(0.6)
	cin.queue_free()
	if cam:
		cam.release()
	var back: bool = prev != null and is_instance_valid(prev) and str(prev.get("level_id")) == str(game._story_scene())
	if prev and is_instance_valid(prev):
		prev.visible = true
		prev.process_mode = Node.PROCESS_MODE_INHERIT
		game._apply_grade(prev)
		if back and cam:
			cam.set_bounds(prev.get_camera_bounds())
			cam.target = game.player
			cam.snap_now()
			Audio.play_ambience(str(prev.get("ambience")), 1.0)
			Audio.play_music(str(prev.get("music")), 2.0)
	var skipped: bool = game._end_cinematic()
	if back:
		await game.fade_in(0.7)
	return skipped
