extends Node
## Scene director (TECHNICAL_ARCHITECTURE §5): loads levels, switches protagonists only at authored story
## boundaries (Story decides; Game presents), routes every interaction through the Story engine and the UI,
## plays skip-safe cinematics, autosaves, maps world pixels to UI coordinates and provides a --capture
## test mode for real rendered screenshots.

signal level_loaded(level: Node)
signal focus_changed(target: Node)

const LEVELS := {
	"L_A1_Railyard": "res://scenes/levels/L_A1_Railyard.tscn",
	"L_M1_Archive": "res://scenes/levels/L_M1_Archive.tscn",
	"L_M1_HallReveal": "res://scenes/levels/L_M1_HallReveal.tscn",
	"L_Test": "res://scenes/levels/L_Test.tscn",
}
const ENTRY_SPAWN := {"L_A1_Railyard": "SP_A1_Platform", "L_M1_Archive": "SP_M1_Office"}
const CHAPTER := {"L_A1_Railyard": ["ui.chapter_a1", "world.a1.title"], "L_M1_Archive": ["ui.chapter_m1", "world.m1.title"]}
const PLAYER := preload("res://scripts/actors/player.gd")
const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const STILLS := "res://assets/ui/documents/"
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
var interact_ready_at := 0      # ticks (ms); player interact presses before this are ignored
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


func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _process(delta: float) -> void:
	if level and not get_tree().paused and not in_cinematic:
		playtime += delta


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
	_load_ui()
	if args.has("capture") or args.has("capture-world"):
		get_window().mode = Window.MODE_WINDOWED
		get_window().size = Vector2i(1920, 1080)
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
	playtime = 0.0
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
	var extra = Saves.get("last_loaded_extra") if Saves.get("last_loaded_extra") != null else {}
	_pending_spawn_pos = null
	if extra is Dictionary and extra.has("player_pos") and str(extra.get("scene", "")) == _story_scene():
		_pending_spawn_pos = LayerStack._v2(extra["player_pos"])
	if extra is Dictionary and extra.has("playtime"):
		playtime = float(extra["playtime"])
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
	return d


func autosave(reason: String) -> void:
	# Never autosave the finished-demo state (montage scene): "Fortsetzen" must resume a playable moment.
	if Saves.has_method("autosave") and not args.has("capture") and _story_scene() != "L_X1_Montage":
		Saves.autosave(reason)


# ------------------------------------------------------------------ levels
func goto_level(id: String, spawn := "", fade := true) -> void:
	if id == "L_X1_Montage":   # montage is presentation-only; finale flow handles it
		await _finale_flow()
		return
	if fade:
		await fade_out(0.6)
	else:
		_fade.color.a = 0.0
	_unload_level()
	var path: String = LEVELS.get(id, "")
	if path == "" or not ResourceLoader.exists(path):
		push_error("Game: unknown level " + id)
		return
	level = load(path).instantiate()
	main.level_root.add_child(level)
	await get_tree().process_frame
	_setup_level(spawn)
	level_loaded.emit(level)
	var intro: bool = level.get("intro_pan") != null and level.intro_pan and not args.has("capture") and not auto and _first_visit()
	if intro:
		camera.cinematic = true
		camera.set_top_left(level.intro_from)
		input_locked = true
	if fade:
		await fade_in(0.9)
	if intro:
		await _intro_pan()
	if CHAPTER.has(id) and not args.has("capture"):
		_show_title(Loc.t(CHAPTER[id][0]), Loc.t(CHAPTER[id][1]))
	autosave("level_" + id)


func _first_visit() -> bool:
	if not Story.has_method("journal"):
		return true
	var quest_obj: Array = []
	for oid in objectives:
		quest_obj.append(oid)
	var j: Dictionary = Story.journal()
	for o in j.get("objectives", []):
		if str(o.get("state", "")) == "complete" and str(o.get("id", "")).begins_with(level.level_id.substr(2, 2).to_lower()):
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
		var sp := spawn if spawn != "" else str(ENTRY_SPAWN.get(level.level_id, ""))
		var pos: Vector2 = level.get_spawn(sp)
		if _pending_spawn_pos != null:
			pos = _pending_spawn_pos
			_pending_spawn_pos = null
		var cid := str(args.get("char", _story_character()))
		player = PLAYER.new()
		player.setup(cid, mode, pos, str(level.get("footstep_surface")))
		level.playfield.add_child(player)
		camera.enabled = true
		camera.release()
		camera.target = player
		camera.set_bounds(level.get_camera_bounds())
		camera.snap_now()
	Audio.play_ambience(str(level.get("ambience")), 1.5)
	Audio.play_music(str(level.get("music")), 2.5)
	_call(_ui("hud"), "show_hud")
	_refresh_objective()


func _apply_grade(lvl: Node) -> void:
	var key := ""
	if lvl.get("grade_preset") and str(lvl.get("grade_preset")) != "":
		key = str(lvl.get("grade_preset"))
	elif lvl.has_method("get_palette_name"):
		key = lvl.get_palette_name()
	var g: Dictionary = grades.get(key, grades.get("default", {}))
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
	_call(hud, "show_prompt", [p, target.prompt_text()])


func world_to_ui(world_pos: Vector2) -> Vector2:
	return view.world_to_ui(world_pos, camera.drawn) if view and camera else world_pos


func interact(it: Node) -> void:
	if busy or in_cinematic:
		return
	busy = true
	input_locked = true
	set_focus(null)
	match str(it.kind):
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
	busy = false
	input_locked = false
	# The key press that closed the last line/panel must not immediately trigger the next interaction.
	interact_ready_at = Time.get_ticks_msec() + 350
	await _after_story_change()


func _objective_item(obj_id: String) -> String:
	return str(objectives.get(obj_id, {}).get("grant_item", ""))


func _do_inspect(it: Node) -> void:
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
		await _speak(str(line.get("speaker", "")), Loc.t(str(line.get("text_key", ""))), LINE_EXPR.get(node_id, "neutral"))
		var adv = Story.advance_dialogue(oid)
		if not (adv is Dictionary) or not adv.get("ok", false) or adv.get("finished", false):
			break
	_end_speech()
	var item := _objective_item(oid)
	if item != "" and Story.has_method("has_item") and Story.has_item(item):
		toast_item(item)
	autosave("dialogue_" + oid)


func _do_puzzle(it: Node) -> void:
	var oid: String = it.objective_id
	var pz := _ui("signal_puzzle") if oid == "a1_solve_signal" else _ui("blueprint_puzzle")
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
	var oid: String = it.objective_id
	var obj: Dictionary = objectives.get(oid, {})
	var opts: Array = []
	for c in obj.get("choices", []):
		opts.append({"id": c["id"], "text": Loc.t(c["text_key"])})
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
	var react: Array = REACTIONS.get(oid, {}).get(str(cid), [])
	if react.size() == 3:
		await _speak(react[0], Loc.t(react[1]), react[2])
	_end_speech()
	autosave("choice_" + oid)


func _do_observe(it: Node) -> void:
	it.used = true
	var speaker: String = player.char_id if player else "alexei"
	await _speak(speaker, Loc.t(str(it.observe_key) + ".text"), "neutral")
	_end_speech()


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
	if not Story.has_method("pending_cinematics"):
		return
	for cid in Story.pending_cinematics():
		var skipped := await _play_cinematic_by_id(str(cid))
		Story.consume_cinematic(str(cid), skipped)
	var target := _story_scene()
	if level and str(level.get("level_id")) != target:
		if target == "L_X1_Montage":
			await _finale_flow()
		else:
			await goto_level(target, "", true)


func _play_cinematic_by_id(cid: String) -> bool:
	match cid:
		"LS_A1_ToM1":
			return await _cin_a1_to_m1()
		"LS_M1_Hall":
			return await _cin_hall()
		"LS_X1_Final":
			return await _cin_final()
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


func _cin_a1_to_m1() -> bool:
	_begin_cinematic()
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
	Audio.play_music("mus_hall_reveal", 0.3)
	Audio.play_ambience("amb_berlin_street", 0.6)
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
				subtitle(Loc.t(key), 3.6))
	var t := 0.0
	var said := false
	while not done[0] and t < 16.0:
		if _skip:
			if hall.has_method("skip"):
				hall.skip()
			break
		if not has_cues and t > 3.2 and not said:
			said = true
			subtitle(Loc.t("cinematic.hall_reveal"), 5.0)
		await get_tree().process_frame
		t += get_process_delta_time()
	await fade_out(0.7)
	hall.queue_free()
	camera.enabled = true
	if prev_level and is_instance_valid(prev_level):
		prev_level.visible = true
		prev_level.process_mode = Node.PROCESS_MODE_INHERIT
		_apply_grade(prev_level)
		Audio.play_ambience(str(prev_level.get("ambience")), 1.0)
		Audio.play_music(str(prev_level.get("music")), 2.0)
	var skipped := _end_cinematic()
	await fade_in(0.7)
	return skipped


func _cin_final() -> bool:
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
		var wi := world.get_texture().get_image()
		wi.get_region(Rect2i(1, 1, 640, 360)).save_png(str(args["capture-world"]))
		print("CAPTURED_WORLD ", args["capture-world"])
	print("FPS ", Engine.get_frames_per_second(), " frame_ms ", Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	get_tree().quit()
