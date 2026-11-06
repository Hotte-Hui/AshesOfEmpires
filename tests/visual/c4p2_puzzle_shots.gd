extends Control
## Screenshots of every state of the Chapter-4-part-2 puzzle UIs (JoinPuzzle „Die Hälften“, HousePuzzle „Haus 14“)
## in the real UI theme at 1920x1080 with real rendering and real tweens/timers (reduced motion off).  Each puzzle is
## driven against a FRESH Story engine instance (never the autoload) played to its objective through the public API,
## with mock Settings/Audio injected through ui_kit overrides — nothing is written to user://.  Inputs go through
## modal_input exactly as UIRoot forwards them (mouse through the board's _gui_input).
##   godot --path . res://tests/visual/C4P2PuzzleShots.tscn -- --out=C:/abs/dir
## Exit code 0 = every check passed (a light subset of tests/test_c4p2_puzzle_ui.gd).

const UIKit := preload("res://scripts/ui/ui_kit.gd")
const TKit := preload("res://tests/support/test_kit.gd")
const Spec := preload("res://tests/test_c4_puzzle_ui.gd")
const Spec2 := preload("res://tests/test_c4p2_puzzle_ui.gd")
const JOIN := preload("res://scenes/ui/JoinPuzzle.tscn")
const HOUSE := preload("res://scenes/ui/HousePuzzle.tscn")

var out_dir := ""
var failures: Array = []
var kit: TKit
var settings: Node
var audio: Node
var stage: Control
var _pz: Control


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(1920, 1080))
	get_tree().create_timer(300.0, true).timeout.connect(func(): print("SHOTS TIMEOUT"); get_tree().quit(2))
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
	if _pz != null and _pz.is_open:
		_pz.modal_input(Spec.key_event(code, true, shift))


## A fresh stage with the theme UIRoot would apply, the puzzle under it.
func _mount(scene: PackedScene, story: Node, hc := false, scale := 1.0, hints := 1) -> Control:
	if stage != null:
		stage.queue_free()
	settings.values["high_contrast"] = hc
	settings.values["text_scale"] = scale
	settings.values["puzzle_hints"] = hints
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
	await _join_states()
	await _house_states()
	UIKit.overrides = {}
	kit.cleanup()
	print("SHOTS DONE, %d failure(s)" % failures.size())
	get_tree().quit(0 if failures.is_empty() else 1)


func _join_states() -> void:
	var g := kit.story()
	check(Spec2.play_to_halves(kit, g, true), "real Story route to the join")
	var pz := _mount(JOIN, g)
	pz.open("c4g_solve_halves")
	await _wait(0.5)
	await _shot("j01_start")
	_key(KEY_ENTER)
	await _wait(0.4)
	check(pz.feedback_text() == UIKit.t("ui.c4p2.halves.wrong_turned"), "start pose: upside down")
	await _shot("j02_wrong_turned")
	_key(KEY_R)
	_key(KEY_ENTER)
	await _wait(0.4)
	check(pz.hint_shown(), "hint after two failures")
	await _shot("j03_sideways_hint")
	_key(KEY_R)
	for k in [KEY_RIGHT, KEY_RIGHT, KEY_RIGHT]:
		_key(k)
	var b = pz._board
	b.hover = true
	b.queue_redraw()
	await _wait(0.2)
	await _shot("j04_turned_moving")
	b.hover = false
	_key(KEY_RIGHT)
	_key(KEY_DOWN)
	await _wait(0.25)
	check(pz.joined() == 5 and pz.stamp_closed(), "aligned: five teeth, the stamp closed")
	await _shot("j05_aligned")
	_key(KEY_ENTER)
	await _wait(0.62)
	await _shot("j06_clicks")
	await _wait(0.5)
	await _shot("j07_stamp_closed")
	await _wait(0.58)
	await _shot("j08_photo")
	await _wait(1.4)
	check(pz.is_done() and pz.clicks_shown() == 5 and pz.ring_shown(), "solved: clicks and the closed ring")
	await _shot("j09_solved")
	var g2 := kit.story()
	Spec2.play_to_halves(kit, g2, true)
	var pz2 := _mount(JOIN, g2, true, 1.5, 2)
	pz2.open("c4g_solve_halves")
	_key(KEY_R)
	_key(KEY_ENTER)
	await _wait(0.5)
	await _shot("j10_hc_150_note_hint")
	# round 10 review: the half at the table's edge in every turn (the frame never cuts its paper)
	var g3 := kit.story()
	Spec2.play_to_halves(kit, g3, true)
	var pz3 := _mount(JOIN, g3)
	pz3.open("c4g_solve_halves")
	var b3 = pz3._board
	for st in [[0, Vector2i(99, 99), "j11_edge_max_r0"], [1, Vector2i(99, 99), "j12_edge_max_r1"],
			[1, Vector2i(-99, -99), "j13_edge_min_r1"], [2, Vector2i(-99, -99), "j14_edge_min_r2"]]:
		b3.set_state(int(st[0]), st[1])
		await _wait(0.15)
		var paper: Rect2 = b3.over_rect().grow(15.0)
		check(Rect2(Vector2.ZERO, b3.size).grow(-6.0).encloses(paper), "%s: the half stays on the table" % st[2])
		await _shot(str(st[2]))
	# the solved state at every text size (round 10: it ran off the screen at 100 %)
	for sc in [1.25, 1.5]:
		var g4 := kit.story()
		Spec2.play_to_halves(kit, g4, true)
		var pz4 := _mount(JOIN, g4, false, sc)
		pz4.open("c4g_solve_halves")
		for k in [KEY_R, KEY_R, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_DOWN, KEY_ENTER]:
			_key(k)
		await _wait(2.6)
		await _shot("j15_success_%d" % int(sc * 100))


func _house_states() -> void:
	var g := kit.story()
	check(Spec2.play_to_house(kit, g, true), "real Story route to the house")
	var pz := _mount(HOUSE, g)
	pz.open("c4h_solve_house")
	await _wait(0.5)
	await _shot("h01_start")
	_key(KEY_L)
	await _wait(0.7)
	await _shot("h02_lights")
	_key(KEY_L)
	_key(KEY_K)
	await _wait(0.3)
	await _shot("h03_cards")
	_key(KEY_K)
	for k in [KEY_UP, KEY_LEFT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN]:
		_key(k)
	_key(KEY_ENTER)
	await _wait(0.42)
	check(pz.is_walking(), "the markers walk")
	await _shot("h04_walk")
	await _wait(0.9)
	check(pz.stop_room() == "ve" and pz.feedback_text() == UIKit.t("ui.c4p2.house.stop.ve"), "stopped at the passage, in words")
	await _shot("h05_stop_passage")
	_key(KEY_R)
	_key(KEY_DOWN)
	_key(KEY_ENTER)
	await _wait(0.6)
	check(pz.hint_shown() and pz.stop_room() == "s2", "second failure: Pohl, hint shown")
	await _shot("h06_pohl_hint")
	_key(KEY_R)
	for k in [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN]:
		_key(k)
	var b = pz._board
	var r: Rect2 = b.rooms["ws"]["rect"]
	var mm := InputEventMouseMotion.new()
	mm.position = (r.position + r.size * 0.5) * 3.0
	b._gui_input(mm)
	await _wait(0.3)
	await _shot("h07_route_hover_workshop")
	_key(KEY_RIGHT)
	_key(KEY_ENTER)
	await _wait(0.45)
	await _shot("h08_success_walk")
	await _wait(1.6)
	check(pz.is_done() and pz.success_stage() == 3, "solved: the workshop lit and ringed")
	await _shot("h09_solved")
	var g2 := kit.story()
	Spec2.play_to_house(kit, g2, true)
	var pz2 := _mount(HOUSE, g2, true, 1.5, 2)
	pz2.open("c4h_solve_house")
	_key(KEY_K)
	_key(KEY_L)
	_key(KEY_DOWN)
	_key(KEY_ENTER)
	await _wait(0.8)
	await _shot("h10_hc_150_cards_lights")
	# round 10 review: the stop at the lodge (from the cellar), the passage with the cards at 125 %, the success at
	# 150 %, the way into the back cellar
	var g3 := kit.story()
	Spec2.play_to_house(kit, g3, true)
	var pz3 := _mount(HOUSE, g3)
	pz3.open("c4h_solve_house")
	for k in [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_LEFT, KEY_UP]:
		_key(k)
	check(pz3.head() == "se", "a way up from the cellar into the lodge")
	_key(KEY_ENTER)
	await _wait(1.3)
	check(pz3.stop_room() == "se", "stopped at the lodge")
	await _shot("h11_stop_lodge")
	var g4 := kit.story()
	Spec2.play_to_house(kit, g4, true)
	var pz4 := _mount(HOUSE, g4, false, 1.25)
	pz4.open("c4h_solve_house")
	_key(KEY_K)
	for k in [KEY_UP, KEY_LEFT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN]:
		_key(k)
	_key(KEY_ENTER)
	await _wait(1.3)
	await _shot("h12_125_cards_stop_ve")
	var g5 := kit.story()
	Spec2.play_to_house(kit, g5, true)
	var pz5 := _mount(HOUSE, g5)
	pz5.open("c4h_solve_house")
	for k in [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN]:
		_key(k)
	await _wait(0.3)
	await _shot("h13_head_back_cellar")
	var g6 := kit.story()
	Spec2.play_to_house(kit, g6, true)
	var pz6 := _mount(HOUSE, g6, false, 1.5)
	pz6.open("c4h_solve_house")
	for k in [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_RIGHT, KEY_ENTER]:
		_key(k)
	await _wait(2.4)
	await _shot("h14_success_150")
