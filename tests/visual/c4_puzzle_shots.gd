extends Control
## Screenshots of every state of the Chapter-4 puzzle UIs (TracePuzzle „Die Nummernkette“, RoutePuzzle „Linie 74“)
## in the real UI theme at 1920x1080 with real rendering and real tweens/timers (reduced motion off).  Each puzzle
## is driven against a FRESH Story engine instance (never the autoload) played to its objective through the
## public API, with mock Settings/Audio injected through ui_kit overrides — nothing is written to user://.
## Inputs go through modal_input exactly as UIRoot forwards them.
##   godot --path . res://tests/visual/C4PuzzleShots.tscn -- --out=C:/abs/dir
## Exit code 0 = every check passed (the checks are a light subset of tests/test_c4_puzzle_ui.gd).

const UIKit := preload("res://scripts/ui/ui_kit.gd")
const TKit := preload("res://tests/support/test_kit.gd")
const Spec := preload("res://tests/test_c4_puzzle_ui.gd")
const TRACE := preload("res://scenes/ui/TracePuzzle.tscn")
const ROUTE := preload("res://scenes/ui/RoutePuzzle.tscn")

var out_dir := ""
var failures: Array = []
var kit: TKit
var settings: Node
var audio: Node
var stage: Control


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(1920, 1080))
	get_tree().create_timer(150.0, true).timeout.connect(func(): print("SHOTS TIMEOUT"); get_tree().quit(2))
	var fill := ColorRect.new()
	fill.color = Color("10181f")
	fill.size = Vector2(1920, 1080)
	add_child(fill)
	kit = TKit.new()
	settings = Spec.MockSettings.new()
	settings.values["reduced_motion"] = false
	add_child(settings)
	audio = Spec.MockAudio.new()
	add_child(audio)
	_run.call_deferred()


func check(cond: bool, what: String) -> void:
	print(("  PASS " if cond else "  FAIL ") + what)
	if not cond:
		failures.append(what)


func _wait(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func _shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	if out_dir == "" or DisplayServer.get_name() == "headless":
		return
	var img := get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(out_dir)
	img.save_png(out_dir.path_join(name + ".png"))
	print("SHOT ", name)


func _key(code: int, shift := false) -> void:
	_puzzle_input(Spec.key_event(code, true, shift))


var _pz: Control


func _puzzle_input(ev: InputEvent) -> void:
	if _pz != null and _pz.is_open:
		_pz.modal_input(ev)


## A fresh stage with the theme UIRoot would apply, the puzzle under it.
func _mount(scene: PackedScene, story: Node, hc := false, scale := 1.0) -> Control:
	if stage != null:
		stage.queue_free()
	settings.values["high_contrast"] = hc
	settings.values["text_scale"] = scale
	settings.values["puzzle_hints"] = 1
	UIKit.overrides = {"Story": story, "Settings": settings, "Audio": audio}
	stage = Control.new()
	stage.size = Vector2(1920, 1080)
	stage.theme = UIKit.theme(hc)
	add_child(stage)
	var pz: Control = scene.instantiate()
	stage.add_child(pz)
	UIKit.refresh_text_scale()
	_pz = pz
	return pz


func _run() -> void:
	await _trace_states()
	await _route_states()
	UIKit.overrides = {}
	kit.cleanup()
	print("SHOTS DONE, %d failure(s)" % failures.size())
	get_tree().quit(0 if failures.is_empty() else 1)


func _trace_states() -> void:
	var g := kit.story()
	check(Spec.play_to_numbers(kit, g, true), "real Story route to the number chain")
	var pz := _mount(TRACE, g)
	pz.open("c4c_solve_numbers")
	await _wait(0.5)
	await _shot("trace_01_start")
	_key(KEY_L)
	await _wait(0.3)
	await _shot("trace_02_lamp")
	_key(KEY_L)
	for k in [KEY_1, KEY_2, KEY_3, KEY_4]:
		_key(k)
		await _wait(0.12)
	_key(KEY_ENTER)
	await _wait(1.0)
	check(pz.halt_shown() and pz.feedback_text() != "", "wrong chain: stop mark + reason")
	await _shot("trace_03_wrong")
	_key(KEY_R)
	for sym in ["n24318", "c1742", "c1745", "n47702"]:     # breaks at W 3
		pz.place(sym)
	_key(KEY_ENTER)
	await _wait(1.2)
	check(pz.hint_shown(), "hint after two failures")
	await _shot("trace_04_hint_halt_w3")
	for i in 4:
		_key(KEY_BACKSPACE)
	pz.pick("n24318")
	pz._show_info("plate", "c1745")
	await _wait(0.3)
	await _shot("trace_05_held_hover")
	pz.hang("n24318", 0)
	pz.place("c1742")
	pz.place("n47702")
	pz.toggle_lamp()
	pz.place("c1745")
	await _wait(0.5)
	await _shot("trace_06_full_lamp")
	_key(KEY_ENTER)
	await _wait(0.75)
	await _shot("trace_07_run")
	await _wait(1.8)
	check(pz.is_done() and pz.ticks_shown() == 4 and pz.wagon_at() == 4, "solved: four ticks, wagon in the siding")
	await _shot("trace_08_solved")
	await _wait(5.0)
	check(not pz.is_open, "closed by itself within the beat")
	# 150 % + high contrast with note, hint, lamp list and side info
	var h := kit.story()
	Spec.play_to_numbers(kit, h, true)
	var pz2 := _mount(TRACE, h, true, 1.5)
	pz2.open("c4c_solve_numbers")
	for k in [KEY_1, KEY_2, KEY_3, KEY_4]:
		_key(k)
	_key(KEY_ENTER)
	_key(KEY_ENTER)
	_key(KEY_L)
	pz2._post_buttons[1].grab_focus()
	await _wait(1.6)
	await _shot("trace_09_150_hc")
	pz2.close()


func _route_states() -> void:
	var g := kit.story()
	check(Spec.play_to_routes(kit, g, true), "real Story route to the overlay")
	var pz := _mount(ROUTE, g)
	pz.open("c4b_solve_routes")
	await _wait(0.5)
	await _shot("route_01_start")
	_key(KEY_ENTER)
	await _wait(0.4)
	check(pz.feedback_text() != "", "start pose: turned-wrong note")
	await _shot("route_02_wrong_turned")
	_key(KEY_R)
	_key(KEY_RIGHT)
	_key(KEY_UP)
	_key(KEY_ENTER)
	await _wait(0.4)
	check(pz.hint_shown(), "hint after two failures")
	await _shot("route_03_wrong_hint")
	_key(KEY_RIGHT)
	await _wait(0.2)
	await _shot("route_04_two_aligned")
	_key(KEY_RIGHT)
	_key(KEY_UP)
	await _wait(0.3)
	check(pz.aligned() == 3, "three of three aligned")
	await _shot("route_05_aligned")
	_key(KEY_ENTER)
	await _wait(0.9)
	await _shot("route_06_solving")
	await _wait(1.4)
	check(pz.matches_shown() == 3 and pz.sign_shown(), "pencil on all pairs + signature")
	await _shot("route_07_solved")
	await _wait(5.0)
	check(not pz.is_open, "closed by itself within the beat")
	var h := kit.story()
	Spec.play_to_routes(kit, h, true)
	var pz2 := _mount(ROUTE, h, true, 1.5)
	pz2.open("c4b_solve_routes")
	_key(KEY_ENTER)
	_key(KEY_ENTER)
	_key(KEY_R)
	await _wait(0.4)
	await _shot("route_08_150_hc")
	pz2.close()
