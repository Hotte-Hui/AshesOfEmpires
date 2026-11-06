extends Node
## Scene director (TECHNICAL_ARCHITECTURE §5): loads levels, switches protagonists only at authored story
## boundaries (Story decides; Game presents), routes every interaction through the Story engine and the UI,
## plays skip-safe cinematics, autosaves, maps world pixels to UI coordinates and provides a --capture
## test mode for real rendered screenshots.
## Memories (§12.10, „Erinnerungen“): travel_to_memory() / return_from_memory() visit a completed scene with a
## „Zeitreise“ transition; inside a memory the Story state never changes (snapshot + every Story path blocked),
## exploration works normally and nothing is saved.

signal level_loaded(level: Node)
signal focus_changed(target: Node)
## Memory mode entered / left (§12.10). info = memory_info().
signal memory_changed(active: bool)

const LEVELS := {
	"L_A1_Railyard": "res://scenes/levels/L_A1_Railyard.tscn",
	"L_M1_Archive": "res://scenes/levels/L_M1_Archive.tscn",
	"L_M1_HallReveal": "res://scenes/levels/L_M1_HallReveal.tscn",
	"L_M1_Parade": "res://scenes/levels/L_M1_Parade.tscn",
	"L_M1_Plaza": "res://scenes/levels/L_M1_Plaza.tscn",
	"L_Test": "res://scenes/levels/L_Test.tscn",
}
const ENTRY_SPAWN := {"L_A1_Railyard": "SP_A1_Platform", "L_M1_Archive": "SP_M1_Arrival"}
const CHAPTER := {"L_A1_Railyard": ["ui.chapter_a1", "world.a1.title"], "L_M1_Archive": ["ui.chapter_m1", "world.m1.title"]}
const PLAYER := preload("res://scripts/actors/player.gd")
const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const STILLS := "res://assets/ui/documents/"
## Chapter 3+: data-driven director extensions (levels, line variants, reactions, puzzle UIs, §12.5 cinematics).
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const CIN_A1_M1 := "res://scenes/cinematics/a1m1/CinA1ToM1.tscn"
const FINALE_SCENE := "res://scenes/cinematics/finale/Finale.tscn"
## §12.10 memories: scene table, global profile (user://profile.json), read-only echo plans, memory grade.
const Memories := preload("res://scripts/core/memories.gd")
const ENGINE_JSON := preload("res://scripts/story/story_engine.gd")
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const Kit := preload("res://scripts/ui/ui_kit.gd")
const MEM_DARK := Color(0.055, 0.04, 0.028, 1.0)   # warm darkroom black of the „Zeitreise“ transition
const MEM_PROMPTS := {"inspect": "ui.memories.prompt.inspect", "dialogue": "ui.memories.prompt.dialogue",
	"puzzle": "ui.memories.prompt.puzzle", "choice": "ui.memories.prompt.choice"}
## Reaction line after each choice: [speaker, text key, expression]
const REACTIONS := {
	"a1_choose": {"share_with_irina": ["irina", "dlg.irina.branch_a", "determined"],
		"keep_private": ["irina", "dlg.irina.branch_b", "concerned"]},
	"m1_choose": {"preserve_evidence": ["konrad", "dlg.konrad.branch_a", "determined"],
		"request_explanation": ["konrad", "dlg.konrad.branch_b", "concerned"]},
}
## Default expression per speaker line (dialogue data has no expression field yet).
const LINE_EXPR := {"irina_01": "concerned", "irina_02": "concerned", "irina_03": "determined",
	"alexei_01": "concerned", "alexei_02": "determined", "emil_01": "neutral", "emil_02": "concerned",
	"emil_03": "determined", "konrad_01": "surprised", "konrad_02": "concerned"}

var main: Node = null
var world: SubViewport = null
var camera: Camera2D = null
var view: Control = null
var grade: ColorRect = null
var overlay: CanvasLayer = null
var ui: Node = null
var level: Node = null
var player: Node = null
var input_locked := false
var interact_ready_at := 0
var side_level := false         # an optional walkable level outside the Story scene chain (the parade plaza)
var _plaza_after_hall := false      # ticks (ms); player interact presses before this are ignored
var busy := false
var in_cinematic := false
var args: Dictionary = {}
var objectives: Dictionary = {}
var palettes: Dictionary = {}
var grades: Dictionary = {}
var playtime := 0.0
## E2E autoplay (scripts/core/autoplay.gd): UI waits are shortened, choices/puzzles answered by the driver.
var auto := false
var auto_choices: Dictionary = {}
var auto_skip := false
var ext = ChapterExt.new()
## §12.10 memories. memory_mode: a completed scene is being revisited (Story frozen, no saves, no cinematics).
var memories = Memories.new()
var memory_mode := false
var memory_scene := ""
var memory_from_menu := false     # travelled from the main menu: returning leads back to it
var memory_travelling := false    # a „Zeitreise“ transition is running (either direction)
var _mem_present: Dictionary = {} # what the return restores: story, level, pos, side_level, explore (menu) …
var _quiet_load := false          # next level load: no intro pan, chapter card, autosave or porter greeting
var _mem_film: CanvasLayer        # film flicker / scratches / dust of the transition
var _mem_film_parts: Array = []
var _mem_film_level := 0.0
var _mem_film_tick := 0
var _mem_film_tween: Tween        # the film fading out after an arrival (killed when the memory ends early)
var _mem_leaks := 0               # safety-net restores of the present Story state (tests; should stay 0)
var _mem_rng := RandomNumberGenerator.new()
var _mem_card: Control
var _mem_card_busy := false
var _mem_card_kicker: Label
var _mem_card_title: Label
var _mem_card_sub: Label

var _fade_layer: CanvasLayer
var _fade: ColorRect
var _still: TextureRect
var _caption: Label
var _title: Label
var _skip := false
var _focus: Node = null
var _pending_spawn_pos = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var q = _json("res://data/v3/quests.json")
	if q is Dictionary:
		for quest in q.get("quests", []):
			for o in quest.get("objectives", []):
				objectives[o["id"]] = o
	var p = _json("res://data/palettes.json")
	palettes = p if p is Dictionary else {}
	var g = _json("res://data/grades.json")
	grades = g if g is Dictionary else {}
	palettes.merge(ext.palettes, false)
	grades.merge(ext.grades, false)
	# §12.10: every scene completion is remembered in the global profile (main-menu „Erinnerungen“)
	if Story.has_signal("event_fired") and not Story.event_fired.is_connected(_on_story_event):
		Story.event_fired.connect(_on_story_event)


func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _process(delta: float) -> void:
	if level and not get_tree().paused and not in_cinematic:
		playtime += delta
	if _mem_film != null:
		# the film look belongs to the world: never drawn over a pause menu or another panel (§12.10)
		var film_on := _mem_film_level > 0.001 and not get_tree().paused
		if _mem_film.visible != film_on:
			_mem_film.visible = film_on
		if film_on:
			_mem_film_update()


# ------------------------------------------------------------------ boot
func register_main(m: Node) -> void:
	main = m
	world = m.world
	camera = m.camera
	view = m.view
	grade = m.grade
	overlay = m.overlay
	_build_overlay()
	_parse_args()
	_init_memories()
	_load_ui()
	if args.has("capture") or args.has("capture-world") or args.has("memory-demo"):
		get_window().mode = Window.MODE_WINDOWED
		get_window().size = Vector2i(1920, 1080)
	if args.has("memory-demo"):   # §12.10 check run with private saves/profile (scripts/core/memory_drive.gd)
		var md: Node = load("res://scripts/core/memory_drive.gd").new()
		add_child(md)
		md.demo.call_deferred(str(args["memory-demo"]), str(args.get("memory-shots", "")))
		return
	if args.has("autoplay"):
		var ap: Node = load("res://scripts/core/autoplay.gd").new()
		add_child(ap)
		ap.configure(str(args["autoplay"]), args.has("autoplay-skip"), str(args.get("autoplay-shots", "")))
		ap.run()
		return
	if args.has("inputplay"):   # real-input E2E: normal boot, then synthetic key presses only
		var ip: Node = load("res://scripts/core/inputplay.gd").new()
		add_child(ip)
		ip.configure(str(args["inputplay"]), args.has("inputplay-skip"), str(args.get("inputplay-shots", "")))
		ip.run.call_deferred()
	if args.has("scene"):
		if Story.has_method("new_game"):
			Story.new_game()
		await goto_level(str(args["scene"]), str(args.get("spawn", "")), false)
		if args.has("cam"):
			var c: PackedStringArray = str(args["cam"]).split(",")
			camera.cinematic = true
			camera.set_top_left(Vector2(float(c[0]), float(c[1])))
	elif args.has("cinematic"):
		if Story.has_method("new_game"):
			Story.new_game()
		_play_cinematic_by_id(str(args["cinematic"]))
	else:
		show_main_menu()
	if args.has("capture") or args.has("capture-world"):
		_capture_flow()


func _parse_args() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1] if kv.size() > 1 else "1"


func _load_ui() -> void:
	var path := "res://scenes/ui/UIRoot.tscn"
	if not ResourceLoader.exists(path):
		return
	ui = load(path).instantiate()
	main.ui_layer.add_child(ui)
	var mm = ui.get("main_menu")
	if mm:
		_connect(mm, "new_game_requested", _on_new_game)
		_connect(mm, "continue_requested", _on_continue)
		_connect(mm, "quit_requested", func(): get_tree().quit())
	for n in ["pause_menu", "saveload_menu"]:
		var node = ui.get(n)
		if node:
			_connect(node, "main_menu_requested", show_main_menu)
			_connect(node, "quit_requested", func(): get_tree().quit())
			_connect(node, "load_requested", _on_load_slot)
			_connect(node, "loaded", _on_loaded_slot)
	# NOTE: Saves.loaded is deliberately NOT connected here: Saves.load() emits it synchronously and
	# _on_load_slot() already continues with _on_loaded_slot() -> connecting it would load the level twice.


func _connect(obj: Object, sig: String, c: Callable) -> void:
	if obj and obj.has_signal(sig) and not obj.is_connected(sig, c):
		obj.connect(sig, c)


func _ui(n: String) -> Node:
	return ui.get(n) if ui else null


func _call(node, method: String, argv: Array = []):
	if node and node.has_method(method):
		return node.callv(method, argv)
	return null


# ------------------------------------------------------------------ menus / flow
func show_main_menu() -> void:
	# §12.10: leaving a memory for the menu restores the present Story state; nothing is saved (the present
	# autosave stays as it was — finds of an in-game memory are only kept by returning to the present).
	if memory_mode or not _mem_present.is_empty():
		_end_memory_state()
	in_cinematic = false
	_unload_level()
	Audio.play_music("mus_menu", 2.0)
	Audio.play_ambience("amb_transition", 2.0)
	var mm := _ui("main_menu")
	if mm:
		_call(ui, "show_main_menu")
		if not ui.has_method("show_main_menu"):
			_call(mm, "open")
	else:
		_on_new_game()
	await fade_in(0.6)


func _on_new_game() -> void:
	if Story.has_method("new_game"):
		Story.new_game()
	if Explore.has_method("reset"):
		Explore.reset()
	playtime = 0.0
	side_level = false   # a stale flag (plaza → Hauptmenü) would stop every later scene change (_after_story_change)
	_call(ui, "close_all")
	await _show_disclaimer()
	await goto_level(_story_scene(), "", true)


func _on_continue() -> void:
	var slot := _latest_slot()
	if slot != "":
		_on_load_slot(slot)


func _latest_slot() -> String:
	if not Saves.has_method("list_slots"):
		return ""
	var best := ""
	var best_t := -1.0
	for s in Saves.list_slots():
		if s.get("exists", false) and s.get("valid", true) and float(s.get("timestamp", 0)) > best_t:
			best_t = float(s.get("timestamp", 0))
			best = str(s.get("slot", ""))
	return best


func _on_load_slot(slot) -> void:
	if not Saves.has_method("load"):
		return
	var r = Saves.load(str(slot))
	if r is Dictionary and not r.get("ok", false):
		toast(Loc.t("ui.load_failed") if Loc.has("ui.load_failed") else str(r.get("error", "")))
		return
	_on_loaded_slot(slot)


func _on_loaded_slot(_slot = "") -> void:
	_call(ui, "close_all")
	get_tree().paused = false
	# §12.10: a save loaded inside a memory becomes the new present — memory mode ends without restoring the old one
	if memory_mode or not _mem_present.is_empty():
		_end_memory_state(false)
	# a loaded save always resumes in the Story scene chain, never on a side level: a flag left over from the plaza
	# (plaza → Hauptmenü / Laden) would make _after_story_change() skip every later scene change (soft-lock)
	side_level = false
	_plaza_after_hall = false
	var extra = Saves.get("last_loaded_extra") if Saves.get("last_loaded_extra") != null else {}
	_pending_spawn_pos = null
	if extra is Dictionary and extra.has("player_pos") and str(extra.get("scene", "")) == _story_scene():
		_pending_spawn_pos = LayerStack._v2(extra["player_pos"])
	if extra is Dictionary and extra.has("playtime"):
		playtime = float(extra["playtime"])
	if Explore.has_method("restore"):
		Explore.restore(extra.get("explore", {}) if extra is Dictionary else {})
	_profile_seed()      # §12.10: scenes completed in this save become memories in the main menu too
	await goto_level(_story_scene(), "", true)
	# A save taken while a transition was still queued: present it now instead of after the next action.
	if Story.has_method("pending_cinematics") and not Story.pending_cinematics().is_empty():
		await _after_story_change()


func _story_scene() -> String:
	var s = Story.get("current_scene")
	if s == null and Story.has_method("snapshot"):
		s = Story.snapshot().get("current_scene", "L_A1_Railyard")
	return str(s) if s != null else "L_A1_Railyard"


func _story_character() -> String:
	var c = Story.get("active_character")
	return str(c) if c != null and str(c) != "" else (level.protagonist if level else "alexei")


## Extra data stored by the save system next to the story payload (position restore, playtime).
func save_extra() -> Dictionary:
	var d := {"scene": level.level_id if level and level.get("level_id") else _story_scene(), "playtime": playtime}
	if player and is_instance_valid(player):
		d["player_pos"] = [player.position.x, player.position.y]
	if Explore.has_method("state"):
		d["explore"] = Explore.state()
	return d


func autosave(reason: String) -> void:
	# Never autosave the finished-demo state (montage scene): "Fortsetzen" must resume a playable moment.
	# Never inside a memory (§12.10): the present autosave must stay the present.
	if memory_mode:
		return
	if Saves.has_method("autosave") and not args.has("capture") and _story_scene() != "L_X1_Montage":
		Saves.autosave(reason)


## Loc key explaining why saving is impossible right now ("" = saving allowed). Read by Saves.save() and the
## save menu (§12.10: no autosave, quicksave or manual save inside a memory). A memory opened from the main menu
## has no present to return to and its finds never reach a save: it names its own reason when the text exists.
func save_block_key() -> String:
	if not memory_mode:
		return ""
	if memory_from_menu and Loc.has("sys.save.err.memory_menu"):
		return "sys.save.err.memory_menu"
	return "sys.save.err.memory"


# ------------------------------------------------------------------ levels
func goto_level(id: String, spawn := "", fade := true) -> void:
	if id == "L_X1_Montage":   # montage is presentation-only; finale flow handles it
		if memory_mode:      # §12.10: never inside a memory
			return
		await _finale_flow()
		return
	if fade:
		await fade_out(0.6)
	else:
		_fade.color.a = 0.0
	if not await _load_level(id, spawn):
		return
	# memories and return trips (§12.10) arrive quietly: no intro pan, chapter card, autosave or greeting
	var quiet := memory_mode or _quiet_load
	_quiet_load = false
	var intro: bool = level.get("intro_pan") != null and level.intro_pan and not args.has("capture") and not auto \
		and not quiet and _first_visit()
	if intro:
		camera.cinematic = true
		camera.set_top_left(level.intro_from)
		input_locked = true
	if fade:
		await fade_in(0.9)
	if intro:
		await _intro_pan()
	if quiet:
		return
	var card: Array = CHAPTER.get(id, ext.chapter_card(id))
	if card.size() == 2 and not args.has("capture"):
		_show_title(Loc.t(card[0]), Loc.t(card[1]))
	autosave("level_" + id)
	await _porter_greeting(id)


## Unloads the current level and instances `id` at `spawn` (no fades). False when the level is unknown.
func _load_level(id: String, spawn := "") -> bool:
	_unload_level()
	var path: String = LEVELS.get(id, ext.level_path(id))
	if path == "" and id.begins_with("res://"):   # dev/test: --scene=res://path/Level.tscn (art previews)
		path = id
	if path == "" or not ResourceLoader.exists(path):
		push_error("Game: unknown level " + id)
		return false
	level = load(path).instantiate()
	main.level_root.add_child(level)
	await get_tree().process_frame
	_setup_level(spawn)
	level_loaded.emit(level)
	return true


## Soft start of Konrad's chapter: the porter greets him once, right after he comes in through the stairwell
## door (optional chat — Explore only, never Story). Not in tests/captures; not if Konrad already walked off.
func _porter_greeting(id: String) -> void:
	if id != "L_M1_Archive" or args.has("capture") or args.has("capture-world") or auto or args.has("inputplay"):
		return
	if not Explore.has_method("is_found") or Explore.is_found("berlin.porter"):
		return
	var porter_chat: Node = level.playfield.get_node_or_null("TalkPorter") if level and level.get("playfield") else null
	if porter_chat == null or player == null:
		return
	await get_tree().create_timer(4.2).timeout   # let the chapter card play out first
	if not is_instance_valid(porter_chat) or not is_instance_valid(player) or busy or in_cinematic or get_tree().paused \
			or Explore.is_found("berlin.porter"):   # greeted by hand meanwhile: the chain has moved on (§12.9)
		return
	if absf(porter_chat.global_position.x - player.global_position.x) < 200.0:
		player.face(porter_chat.global_position.x - player.global_position.x)
		await interact(porter_chat)


func _first_visit() -> bool:
	if not Story.has_method("journal"):
		return true
	var quest_obj: Array = []
	for oid in objectives:
		quest_obj.append(oid)
	var j: Dictionary = Story.journal()
	for o in j.get("objectives", []):
		if str(o.get("state", "")) == "complete" and str(Story.quest_for(str(o.get("id", ""))).get("scene", "")) == str(level.level_id):
			return false
	return true


func _intro_pan() -> void:
	in_cinematic = true
	_skip = false
	_call(_ui("hud"), "hide_hud")
	var target: Vector2 = camera.clamp_pos(player.global_position + camera.follow_offset - camera.VIEW * 0.5) if player else camera.pos
	var dur: float = float(level.intro_duration) if level.get("intro_duration") else 6.0
	if Settings.get_value("reduced_motion"):
		dur *= 0.5
	var tw: Tween = camera.tween_to(target, dur)
	while tw.is_running() and not _skip:
		await get_tree().process_frame
	if tw.is_running():
		tw.kill()
	camera.release()
	camera.snap_now()
	_skip = false
	in_cinematic = false
	input_locked = false
	_call(_ui("hud"), "show_hud")


func _unload_level() -> void:
	set_focus(null)
	if player and is_instance_valid(player):
		player.queue_free()
	player = null
	if level and is_instance_valid(level):
		level.queue_free()
	level = null


func _setup_level(spawn: String) -> void:
	var mode: String = str(level.get("mode")) if level.get("mode") != null else "oblique"
	_apply_grade(level)
	if mode == "oblique" or mode == "side":
		var sp := spawn if spawn != "" else str(ENTRY_SPAWN.get(level.level_id, ext.spawn_for(level.level_id)))
		var pos: Vector2 = level.get_spawn(sp)
		if _pending_spawn_pos != null:
			pos = _pending_spawn_pos
			_pending_spawn_pos = null
		var cid := str(args.get("char", _story_character()))
		if memory_mode:   # §12.10: who was there then (the present protagonist may be the other one)
			cid = _memory_protagonist()
		player = PLAYER.new()
		player.setup(cid, mode, pos, str(level.get("footstep_surface")))
		level.playfield.add_child(player)
		camera.enabled = true
		camera.release()
		camera.target = player
		camera.set_bounds(level.get_camera_bounds())
		camera.snap_now()
	if memory_mode:
		_spawn_memory_hotspots()
	Audio.play_ambience(str(level.get("ambience")), 1.5)
	Audio.play_music(str(level.get("music")), 2.5)
	_call(_ui("hud"), "set_memory", [memory_info()])
	_call(_ui("hud"), "show_hud")
	_refresh_objective()


## Grade preset of a level / cinematic node (data/grades.json + chapter grades); inside a memory the level is
## seen through the "memory" overlay preset (§12.10).
func _grade_for(lvl: Node) -> Dictionary:
	var key := ""
	if lvl.get("grade_preset") and str(lvl.get("grade_preset")) != "":
		key = str(lvl.get("grade_preset"))
	elif lvl.has_method("get_palette_name"):
		key = lvl.get_palette_name()
	var g: Dictionary = grades.get(key, grades.get("default", {}))
	if memory_mode and lvl == level and grades.has("memory"):
		g = Memories.overlay_grade(g, grades["memory"])
		g["palette"] = str(grades.get(key, {}).get("palette", key))
	return g


func _apply_grade(lvl: Node) -> void:
	var key := ""
	if lvl.get("grade_preset") and str(lvl.get("grade_preset")) != "":
		key = str(lvl.get("grade_preset"))
	elif lvl.has_method("get_palette_name"):
		key = lvl.get_palette_name()
	var g: Dictionary = _grade_for(lvl)
	var mat := grade.material as ShaderMaterial
	for k in ["lift", "gamma", "gain", "tint"]:
		var v: Array = g.get(k, [0, 0, 0] if k == "lift" else [1, 1, 1])
		mat.set_shader_parameter(k, Vector3(v[0], v[1], v[2]))
	mat.set_shader_parameter("saturation", float(g.get("saturation", 1.0)))
	mat.set_shader_parameter("vignette", float(g.get("vignette", 0.22)))
	mat.set_shader_parameter("grain", float(g.get("grain", 0.0)) * float(Settings.get_value("pixel_post")))
	var pal_name := str(g.get("palette", key))
	var cols: Array = []
	var P = palettes.get(pal_name, {})
	if P is Dictionary:
		for ramp in P.values():
			for hexc in ramp:
				var c := Color(str(hexc))
				cols.append(Vector3(c.r, c.g, c.b))
	cols = cols.slice(0, 64)
	var strength := float(g.get("palette_strength", 0.0)) * float(Settings.get_value("pixel_post"))
	if str(lvl.get("mode")) == "3d":
		strength = 0.0
	mat.set_shader_parameter("palette_size", cols.size())
	if cols.size() > 0:
		while cols.size() < 64:
			cols.append(cols[0])
		mat.set_shader_parameter("palette", cols)
	mat.set_shader_parameter("palette_strength", strength if cols.size() > 1 else 0.0)


# ------------------------------------------------------------------ interaction
func set_focus(target: Node) -> void:
	_focus = target
	focus_changed.emit(target)
	var hud := _ui("hud")
	if target == null:
		_call(hud, "hide_prompt")
	else:
		update_prompt(target)


func update_prompt(target: Node) -> void:
	var hud := _ui("hud")
	if hud == null or target == null:
		return
	var p: Vector2 = world_to_ui(target.global_position - Vector2(0, target.get("prompt_height") if target.get("prompt_height") else 56.0))
	_call(hud, "show_prompt", [p, target.prompt_text(), "interact",
		target.prompt_state() if target.has_method("prompt_state") else ""])


func world_to_ui(world_pos: Vector2) -> Vector2:
	return view.world_to_ui(world_pos, camera.drawn) if view and camera else world_pos


func interact(it: Node) -> void:
	if busy or in_cinematic:
		return
	busy = true
	input_locked = true
	set_focus(null)
	# §12.10: inside a memory a story hotspot only remembers (read-only) — the Story engine is never called
	var echo: bool = memory_mode and (it.has_meta("memory_objectives") or str(it.kind) in Memories.STORY_KINDS)
	match "memory" if echo else str(it.kind):
		"memory":
			await _do_memory_echo(it)
		"inspect":
			await _do_inspect(it)
		"dialogue":
			await _do_dialogue(it)
		"puzzle":
			await _do_puzzle(it)
		"choice":
			await _do_choice(it)
		"observe":
			await _do_observe(it)
		"discover":
			await _do_discover(it)
		"chat":
			await _do_chat(it)
		"exit":
			await _do_exit(it)
	busy = false
	input_locked = false
	# The key press that closed the last line/panel must not immediately trigger the next interaction.
	interact_ready_at = Time.get_ticks_msec() + 350
	await _after_story_change()


func _objective_item(obj_id: String) -> String:
	return str(objectives.get(obj_id, {}).get("grant_item", ""))


func _do_inspect(it: Node) -> void:
	if memory_mode:      # §12.10 guard (routed to _do_memory_echo before; never reach Story inside a memory)
		return
	if player:
		player.play_action("inspect_side")
	Audio.sfx("paper_rustle_%d" % (randi() % 3 + 1))
	var r = Story.inspect(it.objective_id)
	if not (r is Dictionary and r.get("ok", false)):
		toast(Loc.t("ui.invalid_action"))
		return
	var item := _objective_item(it.objective_id)
	var insp := _ui("inspect")
	if insp and item != "":
		_call(insp, "open", [item])
		if auto:
			await get_tree().create_timer(0.3).timeout
			_call(insp, "close")
		else:
			await _await_closed(insp)
	toast_item(item)
	autosave("inspect_" + it.objective_id)


func _speak(speaker: String, text: String, expr := "neutral") -> void:
	var dlg := _ui("dialogue")
	for n in get_tree().get_nodes_in_group("npcs"):
		n.set_talking(n.char_id == speaker)
	if player:
		player.rig.play("talk_side" if speaker == player.char_id else "idle_side")
	if dlg == null:
		print("[%s] %s" % [speaker, text])
		await _wait(1.2)
		return
	_dock_dialogue(dlg, speaker)
	_call(dlg, "show_line", [speaker, text, expr])
	if auto:
		await get_tree().create_timer(0.25).timeout
	elif dlg.has_signal("advanced"):
		await dlg.advanced
	else:
		await _wait(2.0)


## Dock the dialogue box at the top when the people involved stand in the lower part of the frame
## (feet below ~60 % of the screen), otherwise at the bottom: the box must never hide who is talking.
func _dock_dialogue(dlg: Node, speaker: String) -> void:
	if dlg == null or not ("dock_top" in dlg):
		return
	var lowest := 0.0
	var who: Array = []
	if player and is_instance_valid(player):
		who.append(player)
	for n in get_tree().get_nodes_in_group("npcs"):
		if str(n.get("char_id")) == speaker:
			who.append(n)
	for n in who:
		lowest = maxf(lowest, world_to_ui((n as Node2D).global_position).y)
	dlg.dock_top = lowest > 640.0


func _end_speech() -> void:
	for n in get_tree().get_nodes_in_group("npcs"):
		n.set_talking(false)
	var dlg := _ui("dialogue")
	if dlg:
		if dlg.has_method("close"):
			dlg.close()
		elif dlg.has_method("hide_box"):
			dlg.hide_box()
		else:
			dlg.visible = false


func _do_dialogue(it: Node) -> void:
	if memory_mode:      # §12.10 guard: start_dialogue() already writes dialogue progress
		return
	var oid: String = it.objective_id
	var r = Story.start_dialogue(oid)
	if not (r is Dictionary and r.get("ok", false)):
		toast(Loc.t("ui.invalid_action"))
		return
	var guard := 0
	while guard < 64:
		guard += 1
		var line = Story.current_dialogue_line(oid)
		if not (line is Dictionary) or line.is_empty() or line.has("error"):
			break
		var node_id := str(line.get("node", ""))
		await _speak(str(line.get("speaker", "")), Loc.t(ext.line_key(node_id, str(line.get("text_key", "")))), LINE_EXPR.get(node_id, ext.expr_for(node_id)))
		var adv = Story.advance_dialogue(oid)
		if not (adv is Dictionary) or not adv.get("ok", false) or adv.get("finished", false):
			break
	_end_speech()
	var item := _objective_item(oid)
	if item != "" and Story.has_method("has_item") and Story.has_item(item):
		toast_item(item)
	autosave("dialogue_" + oid)


func _do_puzzle(it: Node) -> void:
	if memory_mode:      # §12.10 guard: puzzle UIs submit through Story.solve_puzzle
		return
	var oid: String = it.objective_id
	var pz: Node = ext.puzzle_ui(self, oid)
	if pz == null:
		pz = _ui("signal_puzzle") if oid == "a1_solve_signal" else _ui("blueprint_puzzle")
	if pz == null:
		toast("Rätsel-UI fehlt")
		return
	if player:
		player.play_action("interact_side")
	if auto:
		await _auto_solve(oid)
	else:
		_call(pz, "open", [oid])
		await _await_closed(pz)
	if Story.has_method("objective_state") and Story.objective_state(oid) == "complete":
		Audio.sfx("puzzle_success")
		autosave("puzzle_" + oid)


func _auto_solve(oid: String) -> void:
	var pid := str(objectives.get(oid, {}).get("puzzle_id", ""))
	var pz = _json("res://data/v3/puzzles.json")
	var sol = null
	if pz is Dictionary:
		for x in pz.get("puzzles", []):
			if x["id"] == pid:
				sol = x["solution"]
	if sol == null:
		return
	if sol is Dictionary:   # JSON numbers arrive as floats; the Story engine requires typed ints
		var typed := {}
		for k in sol:
			typed[k] = int(sol[k])
		sol = typed
	var wrong = ["triangle", "square", "circle"] if sol is Array else {"rotation_steps": 1, "offset_x": 0, "offset_y": 0}
	var r1 = Story.solve_puzzle(oid, wrong)
	if r1 is Dictionary and r1.get("solved", false):
		push_error("AUTOPLAY wrong puzzle answer was accepted for " + oid)
	await get_tree().create_timer(0.2).timeout
	Story.solve_puzzle(oid, sol)


func _do_choice(it: Node) -> void:
	if memory_mode:      # §12.10 guard: a decision is never taken again inside a memory
		return
	var oid: String = it.objective_id
	var obj: Dictionary = objectives.get(oid, {})
	var opts: Array = []
	for c in obj.get("choices", []):
		opts.append({"id": c["id"], "text": Loc.t(c["text_key"])})
	opts = ext.choice_options(oid, opts)
	var dlg := _ui("dialogue")
	if (dlg == null and not auto) or opts.is_empty():
		return
	var speaker: String = player.char_id if player else "alexei"
	_dock_dialogue(dlg, speaker)
	_call(dlg, "show_line", [speaker, Loc.t(str(obj.get("text_key", ""))), "concerned"])
	var cid = null
	if auto:
		cid = str(auto_choices.get(oid, opts[0]["id"]))
		await get_tree().create_timer(0.2).timeout
	else:
		_call(dlg, "show_choices", [opts])
		cid = await dlg.chosen
	var r = Story.choose(oid, str(cid))
	if not (r is Dictionary and r.get("ok", false)):
		_end_speech()
		toast(Loc.t("ui.invalid_action"))
		return
	Audio.sfx("stamp_thud", -6.0)
	var react: Array = REACTIONS.get(oid, {}).get(str(cid), ext.reaction(oid, str(cid)))
	if react.size() == 3:
		await _speak(react[0], Loc.t(react[1]), react[2])
	_end_speech()
	autosave("choice_" + oid)


func _do_observe(it: Node) -> void:
	it.used = true
	var speaker: String = player.char_id if player else "alexei"
	await _speak(speaker, Loc.t(str(it.observe_key) + ".text"), "neutral")
	_end_speech()


## §12 exploration find: Explore records it (never Story); the DiscoveryView presents the find and any
## real-history cards it unlocks. Falls back to a spoken line when the view is missing.
func _do_discover(it: Node) -> void:
	var id := str(it.get("explore_id"))
	if id == "" or not Explore.has_method("find"):
		return
	# §12.8 mini-game finds: the entry's "minigame" scene must be solved first (retry any time; Esc gives up)
	var mg_path := str(Explore.entry(id).get("minigame", ""))
	if mg_path != "" and not Explore.is_found(id):
		if not await _run_minigame(mg_path, id):
			return
	it.used = true
	if player:
		player.play_action("inspect_side")
	var r: Dictionary = Explore.find(id)
	var e: Dictionary = r.get("entry", {})
	var view := _ui("discovery")
	if view and view.has_method("open"):
		_call(view, "open", [id, r.get("cards_new", [])])
		if auto:
			await get_tree().create_timer(0.3).timeout
			_call(view, "close")
		else:
			await _await_closed(view)
	else:
		var speaker: String = player.char_id if player else "alexei"
		await _speak(speaker, Loc.t(str(e.get("text_key", ""))), "neutral")
		_end_speech()
	if r.get("new", false):
		var c: Dictionary = Explore.counts(str(e.get("level", "")))
		var fmt := Loc.t("ui.toast.discovery")
		toast(fmt.format({"name": Loc.t(str(e.get("title_key", ""))), "n": c.get("found", 0), "total": c.get("total", 0)}))


## §12.8 mini-game host: instances the scene under the UI, open(ctx), waits for finished(success).
## ctx = {"explore_id", "auto"}; in autoplay the mini-game resolves itself, the real-input driver calls demo_solve().
func _run_minigame(path: String, id: String) -> bool:
	if not ResourceLoader.exists(path) or ui == null:
		return true                       # never block a find on a missing scene
	var mg: Node = load(path).instantiate()
	ui.add_child(mg)
	var res := {"done": false, "ok": false}
	mg.finished.connect(func(success: bool):
		res["done"] = true
		res["ok"] = success, CONNECT_ONE_SHOT)
	if mg.has_method("open"):
		mg.open({"explore_id": id, "auto": auto})
	while not res["done"] and is_instance_valid(mg):
		await get_tree().process_frame
	if is_instance_valid(mg):
		mg.queue_free()
	if res["ok"]:
		Audio.sfx("puzzle_success")
	return bool(res["ok"])


## §12 optional conversation: lines come from the Explore entry (speaker, key, expr); NPCs face the player.
func _do_chat(it: Node) -> void:
	var id := str(it.get("explore_id"))
	if id == "" or not Explore.has_method("chat_lines"):
		return
	it.used = true
	for l in Explore.chat_lines(id):
		if l is Dictionary:
			await _speak(str(l.get("speaker", "")), Loc.t(str(l.get("key", ""))), str(l.get("expr", "neutral")))
	_end_speech()
	var r: Dictionary = Explore.find(id)
	# a chat can unlock real-history cards (e.g. the barrel workers → Novocherkassk 1962): show them like a find
	var cards: Array = r.get("cards_new", [])
	var view := _ui("discovery")
	if not cards.is_empty() and view and view.has_method("open_cards"):
		_call(view, "open_cards", [cards, true])
		if auto:
			await get_tree().create_timer(0.3).timeout
			_call(view, "close")
		else:
			await _await_closed(view)
	if r.get("new", false):
		var e: Dictionary = r.get("entry", {})
		var c: Dictionary = Explore.counts(str(e.get("level", "")))
		toast(Loc.t("ui.toast.discovery").format({"name": Loc.t(str(e.get("title_key", ""))),
			"n": c.get("found", 0), "total": c.get("total", 0)}))


func _await_closed(node: Node) -> void:
	if node.has_signal("closed"):
		await node.closed
		return
	while is_instance_valid(node) and node.visible:
		await get_tree().process_frame


func toast(text: String) -> void:
	var hud := _ui("hud")
	if hud and hud.has_method("toast"):
		hud.toast(text)
	else:
		print("[toast] ", text)


func toast_item(item: String) -> void:
	if item == "":
		return
	var key := ""
	if Story.has_method("item_def"):
		key = str(Story.item_def(item).get("name_key", ""))
	if key == "":
		var d = _json("res://data/v3/items.json")
		if d is Dictionary:
			for x in d.get("items", []):
				if x["id"] == item:
					key = x["name_key"]
	var fmt := Loc.t("ui.toast.evidence") if Loc.has("ui.toast.evidence") else "Neuer Beweis: {name}"
	toast(fmt.format({"name": Loc.t(key)}))


func _refresh_objective() -> void:
	_call(_ui("hud"), "refresh")


# ------------------------------------------------------------------ story consequences
func _after_story_change() -> void:
	_refresh_objective()
	if memory_mode or memory_travelling:   # §12.10: story cinematics and scene changes never run inside a memory
		return
	if not Story.has_method("pending_cinematics"):
		return
	for cid in Story.pending_cinematics():
		var skipped := await _play_cinematic_by_id(str(cid))
		Story.consume_cinematic(str(cid), skipped)
	if _plaza_after_hall:           # after the Great Hall chain: Konrad stands on the parade plaza (explorable)
		_plaza_after_hall = false
		side_level = true
		await goto_level("L_M1_Plaza", "SP_Plaza_Start", true)
		return
	var target := _story_scene()
	if level and str(level.get("level_id")) != target and not side_level:
		if target == "L_X1_Montage":
			await _finale_flow()
		else:
			await goto_level(target, "", true)


func _play_cinematic_by_id(cid: String) -> bool:
	if memory_mode:
		return false
	match cid:
		"LS_A1_ToM1":
			return await _cin_a1_to_m1()
		"LS_M1_Hall":
			return await _cin_hall()
		"LS_X1_Final":
			return await _cin_final()
	if ext.has_cinematic(cid):
		return await ext.play_cinematic(self, cid)
	return false


func _begin_cinematic() -> void:
	in_cinematic = true
	input_locked = true
	_skip = auto and auto_skip
	set_focus(null)
	_call(_ui("hud"), "hide_hud")
	_call(_ui("fade"), "letterbox", [true])


func _end_cinematic() -> bool:
	in_cinematic = false
	input_locked = false
	_call(_ui("fade"), "letterbox", [false])
	_call(_ui("hud"), "show_hud")
	var s := _skip
	_skip = false
	return s


## Ch1 → Ch2 protagonist switch (§12.5): the animated train departure → stamp → match dissolve → Berlin morning
## sequence (scenes/cinematics/a1m1). Leaves the screen black; goto_level() then fades M1 in at SP_M1_Arrival.
func _cin_a1_to_m1() -> bool:
	_begin_cinematic()
	if not ResourceLoader.exists(CIN_A1_M1):
		return await _cin_a1_to_m1_stills()
	Audio.stop_music(1.5)
	await fade_out(0.8)
	var prev_level := level
	if prev_level:
		prev_level.visible = false
		prev_level.process_mode = Node.PROCESS_MODE_DISABLED
	var cin: Node = load(CIN_A1_M1).instantiate()
	main.level_root.add_child(cin)
	cin.configure({"choices": Story.choice_history(), "flags": Story.flags() if Story.has_method("flags") else {},
		"symbols": Symbols.enabled()})
	var done := [false]
	cin.finished.connect(func(): done[0] = true, CONNECT_ONE_SHOT)
	cin.play()
	_fade.color.a = 0.0          # the cinematic fades in from its own black frame
	while not done[0]:
		if _skip and cin.has_method("skip"):
			cin.skip()
		await get_tree().process_frame
	_fade.color.a = 1.0          # stay black: goto_level() fades M1 in and shows the chapter card
	cin.queue_free()
	camera.release()
	return _end_cinematic()


## Fallback (round-1 version): two stills with a match cut.
func _cin_a1_to_m1_stills() -> bool:
	Audio.stop_music(1.5)
	await fade_out(0.8)
	_show_still(STILLS + "x1_stamp_closeup.png")
	Audio.sfx("stamp_thud")
	await fade_in(0.5)
	await _wait(3.4)
	_show_still(STILLS + "x1_blueprint_closeup.png")   # match cut: same C-17 position
	Audio.sfx("tram_bell")
	Audio.play_ambience("amb_berlin_archive", 0.8)
	await _wait(2.2)
	await fade_out(0.7)
	_hide_still()
	return _end_cinematic()


func _cin_hall() -> bool:
	var path: String = LEVELS["L_M1_HallReveal"]
	if not ResourceLoader.exists(path):
		return false
	_begin_cinematic()
	await fade_out(0.5)
	var prev_level := level
	if prev_level:
		prev_level.visible = false
		prev_level.process_mode = Node.PROCESS_MODE_DISABLED
	camera.enabled = false
	var hall: Node = load(path).instantiate()
	main.level_root.add_child(hall)
	_apply_grade(hall)
	_call(_ui("fade"), "letterbox", [false])   # full 16:9: the lantern eagle stays in frame during the long hold
	Audio.stop_music(1.5)                       # the reveal cue starts later so its swell lands on the final frame
	Audio.play_ambience("amb_berlin_street", 0.6)
	var hall_len: float = float(hall.get_duration()) if hall.has_method("get_duration") else 11.0
	var music_at := maxf(0.0, hall_len - 11.5)
	var music_started := false
	await fade_in(0.6)
	if hall.has_method("play"):
		hall.play()
	var done := [false]
	if hall.has_signal("finished"):
		hall.finished.connect(func(): done[0] = true, CONNECT_ONE_SHOT)
	# The hall reports its own timed cues; the loudspeaker lines are spoken text -> subtitles.
	var has_cues := hall.has_signal("cue")
	if has_cues:
		hall.cue.connect(func(key: String):
			if key.begins_with("hall.cue.loudspeaker") and Loc.has(key):
				subtitle(Loc.t(key), 3.6)
			elif key == "hall.cue.tram_bell":
				Audio.sfx("tram_bell", -6.0))
	var t := 0.0
	var said := false
	while not done[0] and t < 45.0:   # the hall reveal may run ~20–30 s
		if _skip:
			if hall.has_method("skip"):
				hall.skip()
			break
		if not has_cues and t > 3.2 and not said:
			said = true
			subtitle(Loc.t("cinematic.hall_reveal"), 5.0)
		if not music_started and t >= music_at:
			music_started = true
			Audio.play_music("mus_hall_reveal", 0.3)
		await get_tree().process_frame
		t += get_process_delta_time()
	await fade_out(0.7)
	hall.queue_free()
	await _cin_parade()   # second Great Hall scene (round 4): the parade on the plaza, same skip chain
	camera.enabled = true
	if _plaza_enabled():  # round 5: continue onto the walkable plaza instead of cutting back to the archive
		_plaza_after_hall = true
		return _end_cinematic()   # screen stays black; _after_story_change() loads the plaza
	if prev_level and is_instance_valid(prev_level):
		prev_level.visible = true
		prev_level.process_mode = Node.PROCESS_MODE_INHERIT
		_apply_grade(prev_level)
		Audio.play_ambience(str(prev_level.get("ambience")), 1.0)
		Audio.play_music(str(prev_level.get("music")), 2.0)
	var skipped := _end_cinematic()
	await fade_in(0.7)
	return skipped


## The walkable parade plaza is optional gameplay; automated runs only visit it in their explore modes.
func _plaza_enabled() -> bool:
	if not ResourceLoader.exists(str(LEVELS.get("L_M1_Plaza", ""))):
		return false
	if auto and not args.has("autoplay-explore"):
		return false
	if args.has("inputplay") and not args.has("inputplay-explore"):
		return false
	return true


## Exit of a side level (e.g. "Zurück ins Archiv"): back into the Story scene chain.
func _do_exit(it: Node) -> void:
	if memory_mode:      # §12.10: the exit of a side level seen as a memory leads back to the present
		await return_from_memory()
		return
	var target := str(it.get("target_level"))
	if target == "":
		return
	side_level = false
	await goto_level(target, str(it.get("target_spawn")), true)


## Later the same day: the regime's military parade on the plaza (scenes/levels/L_M1_Parade.tscn, 47 s, 8 shots).
## Played right after the reveal inside LS_M1_Hall; one skip press skips the whole Great Hall chain.
func _cin_parade() -> void:
	var path: String = LEVELS.get("L_M1_Parade", "")
	if _skip or path == "" or not ResourceLoader.exists(path):
		return
	var par: Node = load(path).instantiate()
	main.level_root.add_child(par)
	_apply_grade(par)
	if par.has_signal("cue"):
		par.cue.connect(func(k: String):
			if k.begins_with("parade.cue.") and Loc.has(k):
				subtitle(Loc.t(k), 4.8 if k == "parade.cue.konrad" else 3.8))
	await fade_in(0.6)
	Audio.play_music("mus_parade", 0.2)
	if par.has_method("play"):
		par.play()
	var done := [false]
	if par.has_signal("finished"):
		par.finished.connect(func(): done[0] = true, CONNECT_ONE_SHOT)
	var t := 0.0
	while not done[0] and t < 60.0:
		if _skip:
			if par.has_method("skip"):
				par.skip()
			break
		await get_tree().process_frame
		t += get_process_delta_time()
	await fade_out(0.7)
	par.queue_free()
	Audio.stop_music(0.6)


## X1 finale (§12.5): animated two-desk montage driven by both decisions (scenes/cinematics/finale).
## Leaves the screen black; _finale_flow() then fades in the end card.
func _cin_final() -> bool:
	if not ResourceLoader.exists(FINALE_SCENE):
		return await _cin_final_stills()
	_begin_cinematic()
	Audio.stop_music(1.2)
	Audio.stop_ambience(1.2)
	await fade_out(0.9)
	var prev_level := level
	if prev_level:
		prev_level.visible = false
		prev_level.process_mode = Node.PROCESS_MODE_DISABLED
	var fin: Node = load(FINALE_SCENE).instantiate()
	main.level_root.add_child(fin)
	fin.configure({
		"choices": Story.choice_history() if Story.has_method("choice_history") else {},
		"flags": Story.flags() if Story.has_method("flags") else {},
		"symbols": Symbols.enabled(),
		"reduced_motion": bool(Settings.get_value("reduced_motion")),
	})
	_apply_grade(fin)
	var done := [false]
	fin.finished.connect(func(): done[0] = true, CONNECT_ONE_SHOT)
	fin.play()
	await fade_in(0.8)
	while not done[0]:
		if _skip:
			fin.skip()
			break
		await get_tree().process_frame
	await fade_out(1.0)
	fin.queue_free()
	camera.release()
	if prev_level and is_instance_valid(prev_level):
		prev_level.visible = true
		prev_level.process_mode = Node.PROCESS_MODE_INHERIT
	return _end_cinematic()


## Fallback (round-1 version): three stills.
func _cin_final_stills() -> bool:
	_begin_cinematic()
	Audio.play_music("mus_finale_x1", 0.8)
	await fade_out(0.9)
	_show_still(STILLS + "x1_alexei_desk.png")
	await fade_in(0.8)
	await _wait(4.0)
	Audio.sfx("tram_bell", -8.0)
	await _crossfade_still(STILLS + "x1_konrad_desk.png", 0.6)
	await _wait(4.0)
	await _crossfade_still(STILLS + "x1_border_map.png", 0.8)
	subtitle(Loc.t("cinematic.final"), 5.0)
	await _wait(5.0)
	await fade_out(1.0)
	_hide_still()
	return _end_cinematic()


func _finale_flow() -> void:
	if Story.has_method("finale"):
		Story.finale(false)
	# No autosave here on purpose: "Fortsetzen" should resume the last *playable* moment (before the final
	# decision), not replay the end card.
	_unload_level()
	in_cinematic = true      # end card is skippable like any cinematic
	_skip = false
	Audio.play_ambience("amb_transition", 2.0)   # the finale's own score ends with the lamps going out
	_show_end_card()
	await fade_in(1.0)
	var t := 0.0 if not auto else 11.0
	while t < 12.0 and not _skip:
		await get_tree().process_frame
		t += get_process_delta_time()
	_skip = false
	await fade_out(1.0)
	_title.visible = false
	_caption.visible = false
	# closing credits roll with production credits and every source of the history cards (round 5)
	if not auto and ui and ui.has_method("play_end_credits"):
		await ui.play_end_credits()
	_skip = false
	in_cinematic = false
	if not auto:
		show_main_menu()


func _show_disclaimer() -> void:
	in_cinematic = true
	_skip = false
	await fade_out(0.5)
	_title.text = Loc.t("intro.disclaimer.title")
	_caption.text = Loc.t("intro.disclaimer.text")
	_title.visible = true
	_caption.visible = true
	_caption.modulate.a = 1.0
	await _wait(7.0)
	_title.visible = false
	_caption.visible = false
	_skip = false
	in_cinematic = false


func _show_end_card() -> void:
	var lines: Array = [Loc.t("ui.slice_end")]
	if Story.has_method("choice_history"):
		var ch: Dictionary = Story.choice_history()
		for oid in ch:
			for c in objectives.get(oid, {}).get("choices", []):
				if c["id"] == ch[oid]:
					lines.append("• " + Loc.t(c["text_key"]))
	_title.text = Loc.t("game.title")
	_title.visible = true
	_caption.text = "\n".join(lines)
	_caption.visible = true
	_caption.modulate.a = 1.0


# ------------------------------------------------------------------ overlay: fades, stills, captions
func _build_overlay() -> void:
	_still = TextureRect.new()
	_still.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_still.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_still.stretch_mode = TextureRect.STRETCH_SCALE
	_still.size = Vector2(1920, 1080)
	_still.visible = false
	_still.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.add_child(_still)
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 90
	_fade_layer.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_fade_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 1)
	_fade.size = Vector2(1920, 1080)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade_layer.add_child(_fade)
	_title = Label.new()
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.position = Vector2(0, 410)
	_title.size = Vector2(1920, 80)
	_title.add_theme_font_size_override("font_size", 46)
	_title.add_theme_color_override("font_color", Color("#E6DEC2"))
	_title.visible = false
	_fade_layer.add_child(_title)
	_caption = Label.new()
	_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_caption.position = Vector2(260, 500)
	_caption.size = Vector2(1400, 300)
	_caption.add_theme_font_size_override("font_size", 28)
	_caption.add_theme_color_override("font_color", Color("#BA775B"))
	_caption.visible = false
	_fade_layer.add_child(_caption)
	var theme_path := "res://assets/ui/theme.tres"
	if ResourceLoader.exists(theme_path):
		var th = load(theme_path)
		_title.theme = th
		_caption.theme = th
	_build_memory_overlay()


func fade_out(t: float) -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, t if not _skip else 0.05)
	await tw.finished


func fade_in(t: float) -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 0.0, t if not _skip else 0.05)
	await tw.finished


func _show_still(path: String) -> void:
	var t := LayerStack.tex(path)
	_still.texture = t
	_still.visible = t != null
	_still.modulate.a = 1.0


func _crossfade_still(path: String, t: float) -> void:
	var tw := create_tween()
	tw.tween_property(_still, "modulate:a", 0.0, t * 0.5 if not _skip else 0.01)
	await tw.finished
	_show_still(path)
	_still.modulate.a = 0.0
	tw = create_tween()
	tw.tween_property(_still, "modulate:a", 1.0, t * 0.5 if not _skip else 0.01)
	await tw.finished


func _hide_still() -> void:
	_still.visible = false
	_still.texture = null


func subtitle(text: String, dur: float) -> void:
	var sub := _ui("subtitles")
	if sub and sub.has_method("show_text"):
		sub.show_text(text, dur)
	elif sub and sub.has_method("show_subtitle"):
		sub.show_subtitle(text, dur)
	else:
		_caption.text = text
		_caption.visible = true
		get_tree().create_timer(dur).timeout.connect(func(): _caption.visible = false)


func _show_title(title: String, sub: String) -> void:
	var hud := _ui("hud")
	if hud and hud.has_method("show_chapter"):
		hud.show_chapter(title, sub)
		return
	_title.text = title
	_caption.text = sub
	_title.visible = true
	_caption.visible = true
	await get_tree().create_timer(3.5).timeout
	_title.visible = false
	_caption.visible = false


func _wait(t: float) -> void:
	var e := 0.0
	while e < t and not _skip:
		await get_tree().process_frame
		e += get_process_delta_time()


# ------------------------------------------------------------------ §12.10 memories („Erinnerungen“)
func _init_memories() -> void:
	if args.has("profile"):          # tests / check runs: a private profile file
		memories.path = str(args["profile"])
	memories.load_profile()
	if memories.last_error != "":
		push_warning("Memories: %s — the profile starts empty" % memories.last_error)
	if _profile_writes():
		_seed_profile_from_saves()


## The player's profile is written only by the exported game (feature "template"): never by development runs of
## the editor binary (tests, harnesses, E2E drivers share user:// with the player's build on this machine), never
## by automated runs or without a Main scene — unless a profile file is named with --profile=<path>.
func _profile_writes() -> bool:
	if args.has("profile"):
		return true
	if OS.has_feature("editor"):
		return false
	if main == null or not is_instance_valid(main):
		return false
	return not (auto or args.has("autoplay") or args.has("inputplay") or args.has("capture") \
		or args.has("capture-world") or args.has("memory-demo"))


## Saves made before this feature existed: their completed scenes become memories (and their finds count).
func _seed_profile_from_saves() -> void:
	if not Saves.has_method("list_slots") or not Saves.has_method("slot_path"):
		return
	var changed := false
	for s in Saves.list_slots():
		if not (s is Dictionary and bool(s.get("exists", false)) and bool(s.get("valid", false))):
			continue
		var c: Dictionary = Saves.read_container(Saves.slot_path(str(s.get("slot", ""))))
		if not c.get("ok", false):
			continue
		if memories.seed_from_story(str(c.get("story_raw", ""))) > 0:
			changed = true
		var ex = c.get("extra", {})
		if ex is Dictionary and memories.merge_explore(ex.get("explore", {})):
			changed = true
	if changed:
		memories.save_profile()


## Story.event_fired: a scene's exit event → remember the scene with the Story state of that moment.
func _on_story_event(id: String) -> void:
	if memory_mode or not _profile_writes():
		return
	for s in memories.scenes():
		if str(s["unlock"]) == id and not bool(s["side"]):
			memories.record(str(s["id"]), Story.save_json())
			memories.merge_explore(Explore.state())
			memories.save_profile()
			return


func _profile_seed() -> void:
	if not _profile_writes():
		return
	var a: bool = memories.seed_from_story(Story.save_json()) > 0
	var b: bool = memories.merge_explore(Explore.state())
	if a or b:
		memories.save_profile()


## True when the main menu may offer „Erinnerungen“ (some scene was completed at least once).
func memories_any() -> bool:
	return memories.any()


## {scene, place, date, chapter, who, from_menu} of the running memory ({} outside one).
func memory_info() -> Dictionary:
	if not memory_mode:
		return {}
	var s: Dictionary = memories.scene(memory_scene)
	return {"scene": memory_scene, "place": memories.place(memory_scene), "date": memories.date_line(memory_scene),
		"chapter": memories.chapter_line(memory_scene), "who": str(s.get("protagonist", "")),
		"from_menu": memory_from_menu}


## Cards of the MemoryView: one per walkable scene in story order. context "game": unlocked = completed in the
## running Story state; "menu": completed at least once (profile). Locked cards carry no names (no spoilers).
## The scene the player stands in right now is flagged `current` (not a memory while you are there).
func memory_scenes(context := "game") -> Array:
	var out: Array = []
	var menu := context == "menu"
	var here := str(level.get("level_id")) if not menu and level != null and is_instance_valid(level) else ""
	var ex_found: Array = memories.explore_state()["found"] if menu else []
	for s in memories.scenes():
		var id := str(s["id"])
		var open: bool = memories.unlocked_by_profile(id) if menu else memories.unlocked_by_story(id, Story)
		var found := 0
		var total := 0
		if open and Explore.has_method("entries_for"):
			if menu:
				for e in Explore.entries_for(id):
					total += 1
					if ex_found.has(str(e.get("id", ""))):
						found += 1
			else:
				var c: Dictionary = Explore.counts(id)
				found = int(c.get("found", 0))
				total = int(c.get("total", 0))
		out.append({"id": id, "unlocked": open, "current": open and id == here, "side": bool(s["side"]),
			"place": memories.place(id) if open else "", "date": memories.date_line(id) if open else "",
			"chapter": memories.chapter_line(id) if open else "", "who": str(s["protagonist"]) if open else "",
			"thumb": str(s["thumb"]) if open else "", "found": found, "total": total})
	return out


## Cinematics that can be watched again (MemoryView page „Filmsequenzen“), in story order. A film is unlocked
## once its trigger (data/v3/cinematics.json trigger_event / trigger_objective) happened — in the running Story
## state ("game") or in any state recorded in the profile ("menu") — and shown only when its scene exists.
func memory_films(context := "game") -> Array:
	var out: Array = []
	var menu := context == "menu"
	var states: Array = []
	if menu:
		for id in memories.completed_ids():
			var p: Dictionary = ENGINE_JSON.json_parse(memories.snapshot_raw(str(id)))
			if p.get("ok", false) and p["value"] is Dictionary:
				states.append(p["value"])
	else:
		states.append(Story.snapshot())
	var cd = _json("res://data/v3/cinematics.json")
	for seq in (cd.get("sequences", []) if cd is Dictionary else []):
		var cid := str(seq.get("id", ""))
		if not _film_exists(cid):
			continue
		var open := false
		for st in states:
			if _film_triggered(seq, st):
				open = true
		out.append({"id": cid, "unlocked": open, "title": Loc.t("ui.memories.film." + cid) if open else "",
			"sub": Loc.t("ui.memories.film_sub." + cid) if open and Loc.has("ui.memories.film_sub." + cid) else ""})
	return out


## True when the trigger of the cinematic `seq` (data/v3/cinematics.json entry) happened in the Story state `st`.
func _film_triggered(seq: Dictionary, st: Dictionary) -> bool:
	var ev = seq.get("trigger_event")
	var ob = seq.get("trigger_objective")
	return (ev is String and (st.get("completed_events", []) as Array).has(ev)) \
		or (ob is String and (st.get("completed_objectives", []) as Array).has(ob))


## Story state (save_json text) a film watched again from the main menu plays with: the first profile snapshot
## (story order) in which its trigger had happened — the film shows the decisions of the playthrough in which it
## was seen, not those of whatever state the menu holds (after a fresh start: none). "" when none has it.
func _film_snapshot(cid: String) -> String:
	var seq: Dictionary = {}
	var cd = _json("res://data/v3/cinematics.json")
	for s in (cd.get("sequences", []) if cd is Dictionary else []):
		if s is Dictionary and str(s.get("id", "")) == cid:
			seq = s
	if seq.is_empty():
		return ""
	for id in memories.completed_ids():
		var raw: String = memories.snapshot_raw(str(id))
		var p: Dictionary = ENGINE_JSON.json_parse(raw)
		if p.get("ok", false) and p["value"] is Dictionary and _film_triggered(seq, p["value"]):
			return raw
	return ""


func _film_exists(cid: String) -> bool:
	match cid:
		"LS_A1_ToM1":
			return ResourceLoader.exists(CIN_A1_M1)
		"LS_M1_Hall":
			return ResourceLoader.exists(str(LEVELS["L_M1_HallReveal"]))
		"LS_X1_Final":
			return ResourceLoader.exists(FINALE_SCENE)
	return ext.has_cinematic(cid)


## Plays a seen cinematic again (from the pause menu or the main menu) and comes back exactly like a memory
## return: Story untouched (nothing is consumed, snapshot checked), no saves meanwhile, the present level at the
## same position — or the main menu. Esc skips as always.
func rewatch_film(cid: String, from_menu := false) -> bool:
	if not can_travel(from_menu) or not _film_exists(cid):
		return false
	var ok_film := false
	for f in memory_films("menu" if from_menu else "game"):
		if str(f["id"]) == cid and bool(f["unlocked"]):
			ok_film = true
	if not ok_film:
		return false
	memory_travelling = true
	_call(ui, "close_all")
	get_tree().paused = false
	in_cinematic = true
	input_locked = true
	_skip = false
	set_focus(null)
	_call(_ui("hud"), "hide_hud")
	var present := {"story": Story.save_json(), "level": str(level.get("level_id")) if level != null else "",
		"side_level": side_level, "pos": player.position if player != null and is_instance_valid(player) else null}
	Audio.stop_music(0.8)
	await fade_out(0.7)
	_unload_level()
	memory_mode = true            # blocks saves and story consequences while the film runs
	memory_scene = ""
	_mem_present = {"story": present["story"], "inside": present["story"], "from_menu": from_menu,
		"explore": Explore.state()}
	# from the main menu the film runs with the Story state of the playthrough in which it was seen (decisions and
	# flags as then); _end_memory_state() puts the menu's state back afterwards
	if from_menu:
		var then := _film_snapshot(cid)
		if then != "" and Story.load_json(then).get("ok", false):
			_mem_present["inside"] = Story.save_json()
	camera.release()
	match cid:
		"LS_A1_ToM1":
			await _cin_a1_to_m1()
		"LS_M1_Hall":
			await _cin_hall()
		"LS_X1_Final":
			await _cin_final()
		_:
			await ext.play_cinematic(self, cid)
	_plaza_after_hall = false
	# the film's own _end_cinematic() unlocked input: keep it locked until the present is back and faded in
	in_cinematic = true
	input_locked = true
	set_focus(null)
	_hide_still()
	_call(_ui("subtitles"), "hide_subtitle")
	camera.enabled = true
	camera.release()
	_fade.color = Color(0, 0, 0, 1)
	_end_memory_state()
	_skip = false
	if from_menu or str(present["level"]) == "":
		in_cinematic = false
		input_locked = false
		memory_travelling = false
		await show_main_menu()
		return true
	side_level = bool(present["side_level"])
	_pending_spawn_pos = present["pos"]
	await _load_level(str(present["level"]), "")
	await fade_in(0.8)
	_skip = false                 # a skip press during the fade-in must not cut the next level fade short
	in_cinematic = false
	input_locked = false
	memory_travelling = false
	interact_ready_at = Time.get_ticks_msec() + 350
	_call(_ui("hud"), "show_hud")
	_refresh_objective()
	return true


## A „Zeitreise“ may start: free play (or the main menu), no cinematic, dialogue or transition running.
func can_travel(from_menu := false) -> bool:
	if memory_travelling or memory_mode or busy or in_cinematic:
		return false
	if from_menu:
		return level == null
	return level != null and is_instance_valid(level) and player != null and is_instance_valid(player) \
		and not input_locked


## Travels into the completed scene `id` (§12.10). In the game the present is remembered (Story snapshot, level,
## position, side-level flag) and restored by return_from_memory(); from the main menu the Story state recorded
## at the scene's completion is loaded for the visit and the menu returns afterwards. Returns false when the
## trip is not possible now (locked scene, the scene you stand in, cinematic, dialogue, transition).
func travel_to_memory(id: String, from_menu := false) -> bool:
	if not can_travel(from_menu) or not memories.is_memory_scene(id):
		return false
	var open: bool = memories.unlocked_by_profile(id) if from_menu else memories.unlocked_by_story(id, Story)
	if not open or (not from_menu and str(level.get("level_id")) == id):
		return false
	var past := ""
	if from_menu:
		past = memories.snapshot_raw(id)
		var check: Dictionary = Story.validate_save_json(past) if past != "" else {}
		if not check.get("ok", false):
			toast(Loc.t("ui.memories.broken"))
			return false
	memory_travelling = true
	_call(ui, "close_all")
	get_tree().paused = false
	in_cinematic = true
	input_locked = true
	_skip = false
	set_focus(null)
	_call(_ui("hud"), "hide_hud")
	_mem_present = {"story": Story.save_json(), "from_menu": from_menu,
		"level": str(level.get("level_id")) if level != null else "", "side_level": side_level,
		"pos": player.position if player != null and is_instance_valid(player) else null,
		"explore": Explore.state() if from_menu else {}}
	var rm := _mem_reduced()
	Audio.sfx("mem_rewind", -4.0, 0.0)
	Audio.stop_music(1.4 if not rm else 0.6)
	if level != null:
		await _mem_drain(1.6 if not rm else 0.5)
	await _mem_dark(0.8 if not rm else 0.35)
	_mem_film_set(0.0)
	# ---- the past
	if from_menu:
		Story.load_json(past)
		Explore.restore(memories.explore_state())   # everything found in any memory or playthrough shows as found
	_mem_present["inside"] = Story.save_json()      # the state that must not change while we are inside
	memory_mode = true
	memory_scene = id
	memory_from_menu = from_menu
	side_level = false
	_mem_card_show(Loc.t("ui.memories.card.kicker"), memories.place(id), memories.date_line(id))
	var sp := str(memories.scene(id).get("spawn", ""))
	if sp == "":
		sp = str(ENTRY_SPAWN.get(id, ext.spawn_for(id)))
	var ok: bool = await _load_level(id, sp)
	_call(_ui("hud"), "hide_hud")   # _setup_level showed it; it appears once the memory is in view
	await _mem_card_wait()
	if not ok:              # cannot happen with the shipped levels; never strand the player
		push_error("Memories: level %s could not be loaded" % id)
		await _mem_abort()
		return false
	memory_changed.emit(true)
	_mem_film_set(0.5 if not rm else 0.0)
	await _mem_card_hide(0.45 if not rm else 0.2)
	await fade_in(1.0 if not rm else 0.4)
	_fade.color = Color(0, 0, 0, 0)
	_mem_film_fade(1.4 if not rm else 0.1)
	_skip = false
	in_cinematic = false
	input_locked = false
	memory_travelling = false
	interact_ready_at = Time.get_ticks_msec() + 350
	_call(_ui("hud"), "show_hud")
	return true


## Leaves the memory with the reversed transition: back into the present (exact level, position, side-level flag,
## objectives, music, grade; playtime runs on) — or back to the main menu when the trip started there. Finds made
## in an in-game memory stay found and are saved with the present right away (autosave).
func return_from_memory() -> void:
	if not memory_mode or memory_travelling:
		return
	memory_travelling = true
	_call(ui, "close_all")
	get_tree().paused = false
	in_cinematic = true
	input_locked = true
	_skip = false
	set_focus(null)
	_call(_ui("hud"), "hide_hud")
	_mem_film_stop()              # an arrival's film fade still running would fight the drain below
	var rm := _mem_reduced()
	Audio.sfx("mem_return", -4.0, 0.0)
	Audio.stop_music(1.1 if not rm else 0.5)
	await _mem_drain(1.1 if not rm else 0.35)
	await _mem_dark(0.7 if not rm else 0.3)
	_mem_film_set(0.0)
	var present := _mem_present.duplicate()
	var from_menu := memory_from_menu
	var was_place: String = memories.place(memory_scene)
	_end_memory_state()
	memory_changed.emit(false)
	if from_menu:
		await _mem_card_show(Loc.t("ui.memories.card.ended"), was_place, "")
		await _mem_card_hide(0.4 if not rm else 0.2)
		_fade.color = Color(0, 0, 0, 1)
		_skip = false
		in_cinematic = false
		input_locked = false
		memory_travelling = false
		await show_main_menu()
		return
	var lid := str(present.get("level", ""))
	if lid == "":
		lid = _story_scene()
	_mem_card_show(Loc.t("ui.memories.card.present"), memories.place(lid) if memories.is_memory_scene(lid) \
		else Loc.t(str(Kit.scene_def(lid).get("title_key", "ui.memories.card.present"))), "")
	side_level = bool(present.get("side_level", false))
	_pending_spawn_pos = present.get("pos")
	var ok: bool = await _load_level(lid, "")
	_call(_ui("hud"), "hide_hud")
	await _mem_card_wait()
	if not ok:
		side_level = false
		_quiet_load = true
		await goto_level(_story_scene(), "", false)
	# the colour comes back while the present fades in
	var normal := _mem_values()
	var faded := _mem_look(lid, 0.6)
	_mem_write(faded)
	await _mem_card_hide(0.4 if not rm else 0.2)
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 0.0, 1.0 if not rm else 0.4)
	await _mem_tween_grade(faded, normal, 1.8 if not rm else 0.5)
	if tw.is_running():
		await tw.finished
	_fade.color = Color(0, 0, 0, 0)
	_skip = false
	in_cinematic = false
	input_locked = false
	memory_travelling = false
	interact_ready_at = Time.get_ticks_msec() + 350
	_call(_ui("hud"), "show_hud")
	_refresh_objective()
	autosave("memory_return")


## Leaves memory mode without a transition (return, main menu, loading a save). restore: put the present Story
## state back (safety net — inside a memory nothing may change it; from the main menu the recorded scene state is
## replaced by the menu's again). Finds of the visit are added to the profile; from the main menu the Explore
## state of the menu comes back (main-menu finds live on in the profile only).
func _end_memory_state(restore := true) -> void:
	var present := _mem_present
	var from_menu := bool(present.get("from_menu", false))
	# (not when a loaded save replaced the state on purpose: restore == false keeps it)
	if restore and memory_mode and present.has("inside") and Story.save_json() != str(present["inside"]):
		_mem_leaks += 1
		push_warning("Memories: the Story state changed inside a memory — the present state is restored")
	if restore and present.has("story") and Story.save_json() != str(present["story"]):
		var back: Dictionary = Story.load_json(str(present["story"]))
		if not back.get("ok", false):
			push_error("Memories: the present Story state could not be restored: " + str(back.get("error", "")))
	if memory_mode and memories.merge_explore(Explore.state()) and _profile_writes():
		memories.save_profile()
	if from_menu and restore:
		Explore.restore(present.get("explore", {}))
	memory_mode = false
	memory_scene = ""
	memory_from_menu = false
	_mem_present = {}
	_mem_film_stop()
	if _mem_card != null:
		_mem_card.visible = false
	_call(_ui("hud"), "set_memory", [{}])


## A trip that could not reach its level: back where it started, without a trace.
func _mem_abort() -> void:
	var present := _mem_present.duplicate()
	var from_menu := bool(present.get("from_menu", false))
	_end_memory_state()
	_mem_card.visible = false
	_fade.color = Color(0, 0, 0, 1)
	_skip = false
	in_cinematic = false
	input_locked = false
	memory_travelling = false
	if from_menu or str(present.get("level", "")) == "":
		await show_main_menu()
		return
	side_level = bool(present.get("side_level", false))
	_pending_spawn_pos = present.get("pos")
	_quiet_load = true
	await goto_level(str(present["level"]), "", false)


func _mem_reduced() -> bool:
	return auto or bool(Settings.get_value("reduced_motion"))


func _memory_protagonist() -> String:
	var who := str(memories.scene(memory_scene).get("protagonist", ""))
	if who in ["", "none"] and level != null:
		who = str(level.get("protagonist"))
	return who if not (who in ["", "none"]) else _story_character()


## Inside a memory every story hotspot of the level gets a read-only twin (kind "observe", always active; the
## originals stay silent because their objectives are complete). A conversation and the decision taken with the
## same person become one hotspot that replays both.
func _spawn_memory_hotspots() -> void:
	if level == null or level.get("playfield") == null:
		return
	var groups := {}
	var order: Array = []
	for it in get_tree().get_nodes_in_group("interactables"):
		if not is_instance_valid(it) or not level.is_ancestor_of(it):
			continue
		var k := str(it.get("kind"))
		var oid := str(it.get("objective_id"))
		if not (k in Memories.STORY_KINDS) or oid == "":
			continue
		var npc := str(it.get("npc_id"))
		var key := ("npc:" + npc) if npc != "" and k in ["dialogue", "choice"] else ("it:%d" % it.get_instance_id())
		if not groups.has(key):
			groups[key] = {"node": it, "oids": [], "kinds": []}
			order.append(key)
		groups[key]["oids"].append(oid)
		groups[key]["kinds"].append(k)
		if k == "dialogue":
			groups[key]["node"] = it   # the twin stands where the conversation was held
	# optional hotspots active right now (an optional chat may share the spot of a story conversation, e.g. the
	# border officer after the passport control): the twin then steps aside so both stay reachable
	var optional: Array = []
	for it in get_tree().get_nodes_in_group("interactables"):
		if is_instance_valid(it) and level.is_ancestor_of(it) and it.has_method("is_optional") and it.is_optional() \
				and it.is_active():
			optional.append(it)
	for key in order:
		var g: Dictionary = groups[key]
		var src: Node2D = g["node"]
		var kinds: Array = g["kinds"]
		var main_kind := "dialogue" if kinds.has("dialogue") else str(kinds[0])
		var p = INTERACTABLE.new()
		p.name = "Memory_" + str(src.name)
		p.kind = "observe"
		p.prompt_key = str(MEM_PROMPTS.get(main_kind, "ui.memories.prompt.inspect"))
		p.radius = float(src.get("radius"))
		p.prompt_height = float(src.get("prompt_height"))
		p.npc_id = str(src.get("npc_id"))
		p.position = _mem_twin_spot(src, optional)
		p.set_meta("memory_objectives", g["oids"])
		p.set_meta("memory_kind", main_kind)
		src.get_parent().add_child(p)


## A free spot for a twin: its original position, or 24 px to the side when an active optional hotspot stands
## (almost) on it — the side with more room to the other hotspots wins.
func _mem_twin_spot(src: Node2D, optional: Array) -> Vector2:
	var pos := src.position
	var parent := src.get_parent() as Node2D
	var near := func(q: Vector2, limit: float) -> bool:
		var gq: Vector2 = parent.to_global(q) if parent != null else q
		for it in optional:
			if (it as Node2D).global_position.distance_to(gq) < limit:
				return true
		return false
	if not near.call(pos, 12.0):
		return pos
	for dx in [24.0, -24.0, 40.0, -40.0]:
		if not near.call(pos + Vector2(dx, 0), 18.0):
			return pos + Vector2(dx, 0)
	return pos + Vector2(24, 0)


## The read-only twins of the story hotspots in the current memory level (E2E drivers, tests).
func memory_twins() -> Array:
	var out: Array = []
	if level == null or not is_instance_valid(level):
		return out
	for it in get_tree().get_nodes_in_group("interactables"):
		if is_instance_valid(it) and it.has_meta("memory_objectives") and level.is_ancestor_of(it):
			out.append(it)
	return out


## A story hotspot inside a memory: the document again (read-only), the conversation as it was spoken, what was
## decided there — all from the data and Story's read-only accessors (memories.gd echo_plan). Never calls Story.
func _do_memory_echo(it: Node) -> void:
	var oids: Array = it.get_meta("memory_objectives") if it.has_meta("memory_objectives") else [str(it.get("objective_id"))]
	var choices: Dictionary = Story.choice_history()
	var steps: Array = memories.echo_plan(oids, {"protagonist": player.char_id if player else _memory_protagonist(),
		"choices": choices, "flags": memories.memory_flags(memory_scene, Story.flags(), choices), "ext": ext,
		"reactions": REACTIONS, "line_expr": LINE_EXPR})
	for s in steps:
		match str(s.get("type", "")):
			"inspect":
				if player:
					player.play_action("inspect_side")
				Audio.sfx("paper_rustle_%d" % (randi() % 3 + 1))
				var insp := _ui("inspect")
				if insp:
					_call(insp, "open", [str(s.get("item", ""))])
					if auto:
						await get_tree().create_timer(0.3).timeout
						_call(insp, "close")
					else:
						await _await_closed(insp)
			"line":
				await _speak(str(s.get("speaker", "")), str(s.get("text", "")), str(s.get("expr", "neutral")))
	_end_speech()
	if "used" in it:
		it.set("used", true)   # the prompt now shows the quiet "seen" tick


# ---- transition pieces (grade drain, darkroom fade, film flicker, travel card)
func _mem_values() -> Dictionary:
	var mat := grade.material as ShaderMaterial
	var out := {}
	for k in Memories.GRADE_VEC:
		var v = mat.get_shader_parameter(k)
		out[k] = v if v is Vector3 else (Vector3.ZERO if k == "lift" else Vector3.ONE)
	for k in Memories.GRADE_NUM:
		var f = mat.get_shader_parameter(k)
		out[k] = float(f) if f != null else 0.0
	return out


func _mem_write(v: Dictionary) -> void:
	var mat := grade.material as ShaderMaterial
	for k in v:
		mat.set_shader_parameter(k, v[k])


## Memory look of a level (its grade through the memory preset), `extra` 0..1 drains it further (transition).
func _mem_look(lid := "", extra := 1.0) -> Dictionary:
	var g: Dictionary = {}
	if level != null and (lid == "" or str(level.get("level_id")) == lid):
		var key := str(level.get("grade_preset")) if level.get("grade_preset") else ""
		if key == "" and level.has_method("get_palette_name"):
			key = level.get_palette_name()
		g = grades.get(key, grades.get("default", {}))
	var v := Memories.grade_values(Memories.overlay_grade(g, grades.get("memory", {})))
	v["saturation"] = float(v["saturation"]) * (1.0 - 0.75 * extra)
	v["vignette"] = float(v["vignette"]) + 0.06 * extra
	v["grain"] = (float(v["grain"]) + 0.022 * extra) * float(Settings.get_value("pixel_post"))
	return v


func _mem_drain(dur: float) -> void:
	var from := _mem_values()
	var to := _mem_look("", 1.0)
	var film := not _mem_reduced()
	var t := 0.0
	while t < dur and not _skip:
		var k := smoothstep(0.0, 1.0, t / dur)
		_mem_write(Memories.lerp_values(from, to, k))
		_mem_film_set(k if film else 0.0)
		await get_tree().process_frame
		t += get_process_delta_time()
	_mem_write(to)


func _mem_tween_grade(from: Dictionary, to: Dictionary, dur: float) -> void:
	var t := 0.0
	while t < dur and not _skip:
		_mem_write(Memories.lerp_values(from, to, smoothstep(0.0, 1.0, t / dur)))
		await get_tree().process_frame
		t += get_process_delta_time()
	_mem_write(to)


func _mem_dark(dur: float) -> void:
	_fade.color = Color(MEM_DARK.r, MEM_DARK.g, MEM_DARK.b, _fade.color.a)
	await fade_out(dur)


func _mem_film_set(v: float) -> void:
	_mem_film_level = clampf(v, 0.0, 1.0)
	if _mem_film != null:
		_mem_film.visible = _mem_film_level > 0.001 and not get_tree().paused


func _mem_film_fade(dur: float) -> void:
	if _mem_film_tween != null and _mem_film_tween.is_valid():
		_mem_film_tween.kill()
	_mem_film_tween = create_tween()
	_mem_film_tween.tween_method(_mem_film_set, _mem_film_level, 0.0, maxf(dur, 0.01))


## Film look off at once (a memory ends or the return starts): a fade still running would bring it back.
func _mem_film_stop() -> void:
	if _mem_film_tween != null and _mem_film_tween.is_valid():
		_mem_film_tween.kill()
	_mem_film_tween = null
	_mem_film_set(0.0)


## Old-film look while the colour drains: a faint brightness flicker (never strobing), a few vertical scratches
## and dust specks on the 3-px world grid. Off with reduced motion.
func _mem_film_update() -> void:
	_mem_film_tick += 1
	var lv := _mem_film_level
	var flick: ColorRect = _mem_film_parts[0]
	if _mem_film_tick % 3 == 0:
		flick.color.a = lv * _mem_rng.randf_range(0.0, 0.05)
	for i in range(1, _mem_film_parts.size()):
		var r: ColorRect = _mem_film_parts[i]
		var scratch: bool = r.size.y > 100.0
		if (_mem_film_tick + i) % (4 if scratch else 3) != 0:
			continue
		var on := _mem_rng.randf() < lv * (0.55 if scratch else 0.4)
		r.visible = on
		if not on:
			continue
		if scratch:
			r.position = Vector2(floorf(_mem_rng.randf_range(90.0, 1830.0) / 3.0) * 3.0, 0)
			r.color.a = lv * _mem_rng.randf_range(0.07, 0.2)
		else:
			r.position = Vector2(floorf(_mem_rng.randf_range(0.0, 1917.0) / 3.0) * 3.0,
				floorf(_mem_rng.randf_range(0.0, 1077.0) / 3.0) * 3.0)
			r.color.a = lv * _mem_rng.randf_range(0.25, 0.6)


func _build_memory_overlay() -> void:
	_mem_rng.seed = 1964
	_mem_film = CanvasLayer.new()
	_mem_film.layer = 89
	_mem_film.process_mode = Node.PROCESS_MODE_ALWAYS
	_mem_film.visible = false
	add_child(_mem_film)
	var flick := ColorRect.new()
	flick.size = Vector2(1920, 1080)
	flick.color = Color(1.0, 0.9, 0.72, 0.0)
	flick.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mem_film.add_child(flick)
	_mem_film_parts = [flick]
	for i in 3:   # scratches: one world pixel wide, full height
		var s := ColorRect.new()
		s.size = Vector2(3, 1080)
		s.color = Color(0.96, 0.9, 0.76, 0.0)
		s.mouse_filter = Control.MOUSE_FILTER_IGNORE
		s.visible = false
		_mem_film.add_child(s)
		_mem_film_parts.append(s)
	for i in 14:  # dust: dark and light specks, 1-2 world pixels
		var d := ColorRect.new()
		d.size = Vector2(6 if i % 3 == 0 else 3, 3)
		d.color = Color(0.1, 0.07, 0.05, 0.0) if i % 2 == 0 else Color(0.95, 0.9, 0.78, 0.0)
		d.mouse_filter = Control.MOUSE_FILTER_IGNORE
		d.visible = false
		_mem_film.add_child(d)
		_mem_film_parts.append(d)
	# travel card (above the darkroom fade): ERINNERUNG · place · date
	_mem_card = Control.new()
	_mem_card.size = Vector2(1920, 1080)
	_mem_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mem_card.visible = false
	_fade_layer.add_child(_mem_card)
	var v := Kit.vbox(14)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.position = Vector2(260, 360)
	v.size = Vector2(1400, 360)
	_mem_card.add_child(v)
	_mem_card_kicker = Kit.label("", "KickerLabel")
	_mem_card_kicker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_mem_card_kicker)
	var rules := Kit.hbox(14)
	rules.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(rules)
	for i in 3:
		if i == 1:
			rules.add_child(Kit.sprite("icons/ornament_diamond.png"))
		else:
			var r := Kit.rule(Kit.C_COPPER, 3, 150)
			r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			rules.add_child(r)
	_mem_card_title = Kit.label("", "HeadingLabel", 62)
	_mem_card_title.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	_mem_card_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_mem_card_title)
	_mem_card_sub = Kit.label("", "DimLabel", 30)
	_mem_card_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_mem_card_sub)


## Shows the travel card over the darkroom fade and holds it; returns when the hold is over. Called without
## await, the level loads meanwhile and _mem_card_wait() waits for the rest of the hold.
func _mem_card_show(kicker: String, title: String, sub: String) -> void:
	if _mem_card == null:
		return
	_mem_card_busy = true
	_mem_card.theme = Kit.theme(Kit.high_contrast())
	_mem_card_kicker.text = kicker.to_upper().replace("ß", "SS")
	_mem_card_title.text = title
	_mem_card_sub.text = sub
	_mem_card_sub.visible = sub != ""
	_mem_card_sub.add_theme_color_override("font_color", Kit.C_TEXT)
	_mem_card.visible = true
	_mem_card.modulate.a = 0.0
	var rm := _mem_reduced()
	var tw := create_tween()
	tw.tween_property(_mem_card, "modulate:a", 1.0, 0.45 if not rm else 0.15)
	await tw.finished
	var hold := 1.4 if not rm else (0.1 if auto else 0.6)
	var t := 0.0
	while t < hold and not _skip:
		await get_tree().process_frame
		t += get_process_delta_time()
	_mem_card_busy = false


func _mem_card_wait() -> void:
	var guard := 0
	while _mem_card_busy and guard < 1200:
		guard += 1
		await get_tree().process_frame


func _mem_card_hide(dur: float) -> void:
	if _mem_card == null or not _mem_card.visible:
		return
	var tw := create_tween()
	tw.tween_property(_mem_card, "modulate:a", 0.0, dur if not _skip else 0.05)
	await tw.finished
	_mem_card.visible = false


# ------------------------------------------------------------------ input
func _notification(what: int) -> void:
	# Standard PC behaviour: alt-tabbing away during free play opens the pause menu (never in test modes).
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and level and is_instance_valid(level) and player \
			and not busy and not in_cinematic and not get_tree().paused and not auto \
			and not args.has("inputplay") and not args.has("capture") and not args.has("capture-world"):
		_call(ui, "open_pause")


func _unhandled_input(event: InputEvent) -> void:
	if in_cinematic:
		if event.is_action_pressed("skip") or event.is_action_pressed("advance"):
			_skip = true
			get_viewport().set_input_as_handled()
		return
	if level == null or busy:
		return
	if event.is_action_pressed("interact") and player and is_instance_valid(player) and player.has_method("try_interact"):
		if player.try_interact():
			get_viewport().set_input_as_handled()
			return
	if event.is_action_pressed("photo_mode") and not get_tree().paused and ui and ui.has_method("open_photo"):
		ui.open_photo()          # §12.9 photo mode (free camera, filters, frames, saves PNGs)
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("pause") and not get_tree().paused:
		if _call(ui, "open_pause") == null and ui and not ui.has_method("open_pause"):
			_call(_ui("pause_menu"), "open")
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("journal") and not get_tree().paused:
		if _call(ui, "open_journal") == null and ui and not ui.has_method("open_journal"):
			_call(_ui("journal"), "open")
		get_viewport().set_input_as_handled()


# ------------------------------------------------------------------ capture mode (tests / evidence)
func _capture_flow() -> void:
	var frames := int(args.get("frames", "90"))
	if args.has("walk") and player:
		var act := "move_right" if str(args["walk"]) != "left" else "move_left"
		Input.action_press(act)
	for i in frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	if args.has("capture"):
		var img := get_viewport().get_texture().get_image()
		img.save_png(str(args["capture"]))
		print("CAPTURED ", args["capture"], " ", img.get_size())
	if args.has("capture-world"):
		var wi: Image = view.capture_world_image() if view and view.has_method("capture_world_image") \
			else world.get_texture().get_image().get_region(Rect2i(1, 1, 640, 360))
		wi.save_png(str(args["capture-world"]))
		print("CAPTURED_WORLD ", args["capture-world"])
	print("FPS ", Engine.get_frames_per_second(), " frame_ms ", Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	get_tree().quit()
