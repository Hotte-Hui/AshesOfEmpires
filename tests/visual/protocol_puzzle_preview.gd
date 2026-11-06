extends Control
## Visual + behavioural preview of the Chapter-3 protocol puzzle (scenes/ui/ProtocolPuzzle.tscn) in the real
## UI theme at 1920x1080. Instances scenes/ui/UIRoot.tscn, adds the puzzle under it exactly like
## ChapterExt.puzzle_ui does (before the toast layer, `ui_root` set), drives the REAL Story autoload to
## c3b_solve_protocol through the public API, plays the puzzle with synthetic key presses that travel through
## UIRoot's modal routing (1-4, Backspace, R, Enter, Esc), switches text scale (125 % / 150 %) and high
## contrast live through Settings.changed, checks that the solved modal closes by itself without a confirm,
## saves screenshots and finally opens both inspect documents through the real InspectView.
##   xvfb-run -a -s "-screen 0 1920x1080x24" godot --path . --rendering-method gl_compatibility \
##       --rendering-driver opengl3 res://tests/visual/ProtocolPuzzlePreview.tscn -- --out=/abs/dir [--bg=/abs/world.png]
## --bg: a 640x360 world capture (e.g. --capture-world of a level) shown x3 behind the UI. With --headless
## only the checks run (no screenshots). Exit code 0 = every check passed.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const UIROOT := preload("res://scenes/ui/UIRoot.tscn")
const PUZZLE := preload("res://scenes/ui/ProtocolPuzzle.tscn")
const Route := preload("res://tests/test_c3_puzzle_ui.gd")
const OBJ := "c3b_solve_protocol"

var out_dir := ""
var bg_path := ""
var headless := false
var ui: Control
var pz: Control
var failures: Array = []
var shots := 0
var solved_signals := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	headless = DisplayServer.get_name() == "headless"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--bg="):
			bg_path = a.substr(5)
	if not headless:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(1920, 1080))
	get_tree().create_timer(120.0, true).timeout.connect(func(): print("PREVIEW TIMEOUT"); get_tree().quit(2))
	var bg := TextureRect.new()
	bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.size = Vector2(1920, 1080)
	if bg_path != "" and FileAccess.file_exists(bg_path):
		var img := Image.load_from_file(bg_path)
		if img != null and not img.is_empty():
			bg.texture = ImageTexture.create_from_image(img)
	add_child(bg)
	if bg.texture == null:
		var fill := ColorRect.new()
		fill.color = Color("10181f")
		fill.size = Vector2(1920, 1080)
		add_child(fill)
	Kit.overrides = {}
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		s.values = s.DEFAULTS.duplicate(true)      # in memory only, never saved here
	ui = UIROOT.instantiate()
	add_child(ui)
	pz = PUZZLE.instantiate()
	ui.add_child(pz)
	ui.move_child(pz, ui.toast_layer.get_index())
	pz.set("ui_root", ui)
	pz.solved.connect(func(_id): solved_signals += 1)
	_run.call_deferred()


func check(cond: bool, what: String) -> void:
	print(("  PASS " if cond else "  FAIL ") + what)
	if not cond:
		failures.append(what)


func wait(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func frames(n := 2) -> void:
	for i in n:
		await get_tree().process_frame


func key(code: int) -> void:
	var ev := InputEventKey.new()
	ev.keycode = code as Key
	ev.physical_keycode = code as Key
	ev.pressed = true
	Input.parse_input_event(ev)
	await frames(1)
	var up: InputEventKey = ev.duplicate()
	up.pressed = false
	Input.parse_input_event(up)
	await frames(2)


## Changes a setting in memory and emits Settings.changed exactly like the settings menu does — never saved.
func _set_setting(s: Node, key: String, value) -> void:
	s.values[key] = value
	if s.has_signal("changed"):
		s.changed.emit(key, value)


func shot(name: String) -> void:
	shots += 1
	if headless or out_dir == "":
		print("SHOT (skipped) ", name)
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join("%02d_%s.png" % [shots, name])
	DirAccess.make_dir_recursive_absolute(out_dir)
	img.save_png(path)
	print("SHOT ", path, " ", img.get_size())


func _run() -> void:
	await frames(3)
	var st := get_node_or_null("/root/Story")
	check(st != null and st.has_method("solve_puzzle"), "Story autoload present")
	if st == null:
		get_tree().quit(1)
		return
	st.new_game()
	check(Route.play_to_protocol(st, true), "real Story reaches c3b_solve_protocol (clues inspected)")
	var before: String = st.save_json()
	# ---------------------------------------------------------------- first look
	pz.open(OBJ)
	await wait(0.6)
	check(ui.top_modal() == pz and get_tree().paused, "puzzle is the top modal and pauses the game")
	check(pz.symbols == ["soviet", "secretariat", "chair", "reich"], "tray order = display_symbols")
	await shot("protocol_open")
	# keys: 3 = chair (third card of the ORIGINAL tray order), 4 = reich
	await key(KEY_3)
	await key(KEY_4)
	check(pz.slots == ["chair", "reich", "", ""], "keys 3 and 4 lay chair, reich")
	await key(KEY_ENTER)
	check(pz.feedback_text() == Kit.t("ui.c3.protocol.incomplete") and st.puzzle_attempts(OBJ) == 0,
		"Enter with two cards: incomplete note, no attempt")
	await wait(0.3)
	await shot("protocol_two_cards")
	# wrong order twice -> hint (puzzle_hints = 1)
	await key(KEY_1)          # soviet
	await key(KEY_2)          # secretariat -> chair, reich, soviet, secretariat (wrong)
	await key(KEY_ENTER)
	check(st.puzzle_attempts(OBJ) == 1 and pz.slots == ["chair", "reich", "soviet", "secretariat"],
		"wrong order: one attempt, cards stay")
	await key(KEY_BACKSPACE)
	await key(KEY_BACKSPACE)
	check(pz.slots == ["chair", "reich", "", ""] and pz.is_open, "Backspace takes back the last cards, modal stays open")
	await key(KEY_2)          # secretariat
	await key(KEY_1)          # soviet
	check(pz.slots == ["chair", "reich", "secretariat", "soviet"], "keys 2, 1 fill the free slots")
	# second wrong attempt: take the last two back (as a mouse click on the slots would) and swap them
	pz.take_back(2)
	pz.take_back(3)
	await key(KEY_1)
	await key(KEY_2)
	await key(KEY_ENTER)
	check(st.puzzle_attempts(OBJ) == 2 and pz.hint_shown(), "second wrong attempt: hint visible")
	await wait(0.4)
	await shot("protocol_wrong_hint")
	await key(KEY_R)
	check(pz.filled_count() == 0, "R clears the order")
	for k in [KEY_3, KEY_4, KEY_2, KEY_1]:
		await key(k)
	await key(KEY_ENTER)
	await frames(2)
	check(pz.is_done() and st.objective_state(OBJ) == "complete" and solved_signals == 1, "correct order solves once")
	check(bool(st.flag("protocol_matched")), "flag protocol_matched set")
	await wait(0.7)
	await shot("protocol_solved")
	await key(KEY_ENTER)
	await frames(3)
	check(not pz.is_open and ui.top_modal() == null and not get_tree().paused, "confirm closes after success")
	# ---------------------------------------------------------------- 125 % / 150 % text + high contrast (fresh state)
	var r = st.load_json(before)
	check(Kit.ok(r), "state reloaded before the solve")
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		_set_setting(s, "text_scale", 1.25)
		pz.open(OBJ)
		await wait(0.4)
		for k in [KEY_1, KEY_2, KEY_3, KEY_4]:
			await key(k)
		await key(KEY_ENTER)
		await key(KEY_ENTER)
		await wait(0.4)
		check(pz.hint_shown(), "hint shown at 125 %")
		check(pz._actions.get_parent() == pz._footer, "125 %: actions move into the footer row (the hint needs the column)")
		await shot("protocol_text125")
		_set_setting(s, "text_scale", 1.5)              # live, while open: UIRoot rescales, the puzzle re-lays out
		await wait(0.4)
		check(pz._actions.get_parent() == pz._footer, "150 %: actions stay in the footer row")
		await shot("protocol_text150")
		_set_setting(s, "text_scale", 1.0)
		check(pz._actions.get_parent() == pz._col_b, "100 %: actions back under the notes")
		_set_setting(s, "high_contrast", true)
		await wait(0.3)
		await shot("protocol_high_contrast")
		_set_setting(s, "high_contrast", false)
		s.values["puzzle_hints"] = 0
		pz._refresh()
		check(not pz.hint_shown(), "puzzle_hints = 0 hides the hint")
		s.values["puzzle_hints"] = 1
		await key(KEY_ESCAPE)
		await frames(3)
		check(not pz.is_open and ui.top_modal() == null, "Esc closes the puzzle through UIRoot")
		check(st.objective_state(OBJ) == "available", "closing without solving keeps the objective open")
	# ---------------------------------------------------------------- solved without a confirm: closes by itself
	pz.open(OBJ)
	await wait(0.3)
	for k in [KEY_3, KEY_4, KEY_2, KEY_1]:
		await key(k)
	await key(KEY_ENTER)
	check(pz.is_done() and st.objective_state(OBJ) == "complete", "solved again from the reloaded state")
	var t := 0.0
	while pz.is_open and t < 7.5:
		await wait(0.25)
		t += 0.25
	check(not pz.is_open and ui.top_modal() == null and not get_tree().paused,
		"closes by itself after %.2f s (beat %.2f s, the input driver waits 8 s)" % [t, pz.success_beat()])
	# ---------------------------------------------------------------- inspect documents through the real InspectView
	ui.inspect.open("ev_c3_seating")
	await wait(0.7)
	check(ui.inspect._doc_rect.visible and ui.inspect._doc_rect.texture != null, "InspectView shows the seating document")
	# the caption sits under the document, or (125 / 150 % text, long caption) in the record card
	check(ui.inspect._caption.text + ui.inspect._card_alt.text == Kit.t("doc.c3.seating.alt"), "seating alt text from the documents json")
	await shot("inspect_seating")
	ui.inspect.close()
	ui.inspect.open("ev_c3_booth_log")
	await wait(0.7)
	check(ui.inspect._doc_rect.texture != null and ui.inspect._caption.text + ui.inspect._card_alt.text == Kit.t("doc.c3.booth_log.alt"),
		"InspectView shows the booth log with its alt text")
	await shot("inspect_booth_log")
	ui.inspect.close()
	print("PROTOCOL PREVIEW done: %d shots, %d failures" % [shots, failures.size()])
	for f in failures:
		print("  failed: ", f)
	get_tree().quit(0 if failures.is_empty() else 1)
