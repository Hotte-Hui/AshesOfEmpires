extends RefCounted
## Chapter-4-part-2 puzzle UIs (documentation/C4P2_DESIGN.md §2.7): the join „Die Hälften“ (scenes/ui/JoinPuzzle.tscn,
## c4g_solve_halves) and the house „Haus 14“ (scenes/ui/HousePuzzle.tscn, c4h_solve_house).  Both are registered in
## data/chapters/c4p2.json, instanced by ChapterExt and driven here stand-alone (headless) against a REAL Story engine
## instance (public API only) plus mock Settings/Audio injected through ui_kit overrides (helper classes of
## tests/test_c4_puzzle_ui.gd).  Covers per puzzle: registration, the real route opens it, keys / pad / mouse
## contracts, the exact key sequences of scripts/core/inputplay.gd, wrong answers (no Story change except the
## attempt, the reason in words), hints (puzzle_hints 0/1/2 and after two failures), success (marks, `solved` once,
## beat ≤ 7 s, confirm closes after the guard), 125 % / 150 % (fits 1920x1080), WCAG contrast (also high contrast),
## engine refusals, the geometry / passage data of tools/pixelgen/gen_ui_c4p2.py against data/v3/puzzles.json and
## the contract, shape-coded marks, the walk never swallowing input, and every Loc key of the two UIs.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const Spec := preload("res://tests/test_c4_puzzle_ui.gd")
const J_SCENE := "res://scenes/ui/JoinPuzzle.tscn"
const J_SCRIPT := "res://scripts/ui/join_puzzle.gd"
const J_LAYOUT := "res://assets/ui/documents/karsk_c4p2_halves.json"
const J_OBJ := "c4g_solve_halves"
const J_SOLUTION := {"rotation_steps": 2, "offset_x": 4, "offset_y": 1}
const J_START := {"rotation_steps": 0, "offset_x": 0, "offset_y": 0}
const H_SCENE := "res://scenes/ui/HousePuzzle.tscn"
const H_SCRIPT := "res://scripts/ui/house_puzzle.gd"
const H_LAYOUT := "res://assets/ui/puzzle/c4p2_house.json"
const H_OBJ := "c4h_solve_house"
const H_SOLUTION := ["s3", "sd", "hd", "h3", "h2", "h1", "he", "hk", "ws"]
const H_ROOMS := ["vk", "ve", "v1", "v2", "v3", "vd", "sk", "se", "s1", "s2", "s3", "sd", "hk", "he", "h1", "h2", "h3",
	"hd", "ws"]
const H_UNSAFE := ["s2", "se", "ve"]

var kit: TKit
var _saved: Dictionary = {}


func run() -> Array:
	kit = TKit.new()
	_saved = UIKit.overrides.duplicate()
	kit.run_case("join_registered_and_instanced_by_chapter_ext", _j_registered)
	kit.run_case("join_real_route_opens_at_the_start_pose", _j_route)
	kit.run_case("join_keys_move_turn_undo_enter_esc", _j_keys)
	kit.run_case("join_wrong_feedback_turned_sideways_offset", _j_wrong)
	kit.run_case("join_hint_follows_settings_and_attempts", _j_hints)
	kit.run_case("join_controller_contract", _j_controller)
	kit.run_case("join_mouse_drag_wheel_buttons", _j_mouse)
	kit.run_case("join_inputplay_key_sequence_solves", _j_inputplay)
	kit.run_case("join_geometry_only_the_solution_joins", _j_geometry)
	kit.run_case("join_correct_pose_clicks_stamp_photos_once", _j_correct)
	kit.run_case("join_text_scale_125_150_fits", _j_text_scale)
	kit.run_case("join_contrast_and_shapes", _j_contrast)
	kit.run_case("join_refused_or_locked_never_breaks", _j_refused)
	kit.run_case("house_registered_and_instanced_by_chapter_ext", _h_registered)
	kit.run_case("house_real_route_opens_in_hannas_flat", _h_route)
	kit.run_case("house_keys_move_cut_undo_reset_k_l_enter_esc", _h_keys)
	kit.run_case("house_walk_stops_with_its_reason", _h_stops)
	kit.run_case("house_third_failure_leaves_ilse_on_the_safe_landing", _h_trim)
	kit.run_case("house_hint_follows_settings_and_attempts", _h_hints)
	kit.run_case("house_controller_contract", _h_controller)
	kit.run_case("house_mouse_click_drag_rightclick_hover_buttons", _h_mouse)
	kit.run_case("house_inputplay_key_sequence_solves", _h_inputplay)
	kit.run_case("house_walk_never_swallows_input", _h_walk_input)
	kit.run_case("house_graph_is_the_contract_and_only_one_way_is_safe", _h_graph)
	kit.run_case("house_figures_stand_on_floors_and_walk_the_stairs", _h_figures)
	kit.run_case("house_stop_mark_cards_and_ring_never_cover", _h_overlays)
	kit.run_case("house_correct_way_lights_the_workshop_once", _h_correct)
	kit.run_case("house_text_scale_125_150_fits", _h_text_scale)
	kit.run_case("house_contrast_and_shape_coded_watchers", _h_contrast)
	kit.run_case("house_refused_or_locked_never_breaks", _h_refused)
	kit.run_case("art_files_and_layout_metadata", _art)
	kit.run_case("loc_keys_exist_german_quotes", _loc_keys)
	UIKit.overrides = _saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Plays the canonical route through the public Story API up to the join (Ekdahl, the book, Lev's half).
static func play_to_halves(k: TKit, g: Node, with_clues := true) -> bool:
	k.play_until(g, "c4f")
	k.play_dialogue(g, "c4g_talk_ekdahl")
	g.inspect("c4g_inspect_book")
	if with_clues:
		k.play_dialogue(g, "c4g_talk_lev")
	return g.is_available(J_OBJ) == with_clues


## … up to the house (the notice in the passage, Hanna, Kuhnert's card box).
static func play_to_house(k: TKit, g: Node, with_clues := true) -> bool:
	k.play_until(g, "c4g")
	g.inspect("c4h_inspect_gate")
	k.play_dialogue(g, "c4h_talk_hanna")
	if with_clues:
		g.inspect("c4h_inspect_cards")
	return g.is_available(H_OBJ) == with_clues


func _story_j(with_clues := true) -> Node:
	var g := kit.story()
	kit.ok(play_to_halves(kit, g, with_clues), "route to the join (clues: %s)" % with_clues)
	return g


func _story_h(with_clues := true) -> Node:
	var g := kit.story()
	kit.ok(play_to_house(kit, g, with_clues), "route to the house (clues: %s)" % with_clues)
	return g


func _make(scene: String, story, hints := 1, reduced := true) -> Control:
	var settings: Node = Spec.MockSettings.new()
	settings.values["puzzle_hints"] = hints
	settings.values["reduced_motion"] = reduced
	kit.track(settings)
	var audio: Node = Spec.MockAudio.new()
	kit.track(audio)
	UIKit.overrides = {"Story": story, "Settings": settings, "Audio": audio}
	var pz: Control = load(scene).instantiate()
	kit.track(pz)
	(Engine.get_main_loop() as SceneTree).root.add_child(pz)
	return pz


func _key(pz: Control, code: int, shift := false) -> bool:
	return pz.modal_input(Spec.key_event(code, true, shift))


func _pad(pz: Control, b: int, pressed := true) -> bool:
	return pz.modal_input(Spec.pad_event(b, pressed))


func _registered(obj: String, scene: String, script: String, suffix: String) -> Node:
	var c4p2 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c4p2.json"))
	kit.eq(str(c4p2.get("puzzles", {}).get(obj, "")), scene, "data/chapters/c4p2.json registers %s" % scene)
	var root: Control = Spec.FakeRoot.new()
	kit.track(root)
	root.toast_layer = Control.new()
	root.add_child(root.toast_layer)
	var game: Node = Spec.FakeGame.new()
	kit.track(game)
	game.ui = root
	UIKit.overrides = {"Settings": Spec.MockSettings.new(), "Audio": Spec.MockAudio.new()}
	kit.track(UIKit.overrides["Settings"])
	kit.track(UIKit.overrides["Audio"])
	var ext := ChapterExt.new()
	var node: Node = ext.puzzle_ui(game, obj)
	kit.ok(node != null and node.get_script() == load(script), "ChapterExt.puzzle_ui instances %s" % scene)
	if node == null:
		return null
	kit.ok(node.get_parent() == root and node.get_index() < root.toast_layer.get_index(), "added under UIRoot before the toasts")
	kit.ok(node.get("ui_root") == root, "ui_root set")
	kit.ok(ext.puzzle_ui(game, obj) == node, "instanced once")
	kit.ok(node.has_method("open") and node.has_signal("solved") and node.has_signal("closed"), "open(), solved, closed")
	kit.eq(node.get("suppress_toasts"), true, "suppress_toasts")
	kit.eq(node.get("is_open"), false, "is_open false until opened")
	kit.eq(node.visible, false, "hidden until opened")
	kit.ok(str(node.get_script().resource_path).ends_with(suffix), "inputplay finds it by the script suffix %s" % suffix)
	return node


func _fits(pz: Control, what: String) -> void:
	Spec.force_layout(pz)
	var need: Vector2 = pz._panel.get_combined_minimum_size()
	kit.ok(need.y <= 1080 - 20 and need.x <= 1920 - 56, "%s fits 1920x1080 (needs %s)" % [what, need])


func _image(path: String) -> Image:
	return Image.load_from_file(ProjectSettings.globalize_path(path))


# ================================================================== JoinPuzzle „Die Hälften“
func _j_registered() -> bool:
	_registered(J_OBJ, J_SCENE, J_SCRIPT, "join_puzzle.gd")
	return true


func _j_route() -> bool:
	var g := _story_j(true)
	var p: Dictionary = g.puzzle_for(J_OBJ)
	kit.ok(not p.has("solution"), "the UI never sees the solution")
	kit.eq(p.get("clue_item_ids"), ["ev_c4_guidebook", "ev_c4_card_ru_original"], "clue items: the guidebook, Lev's half")
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	kit.ok(pz.is_open and pz.visible, "open() shows the modal")
	kit.eq(pz.pose(), J_START, "start pose {0, 0, 0} (C4P2_DESIGN §2.7): upside down, on the book")
	kit.eq([pz.joined(), pz.stamp_closed()], [0, false], "no tooth in a notch, the stamp in two halves")
	var b = pz._board
	kit.ok(b.tex_table != null and b.tex_base != null and b.tex_over != null, "table and both halves loaded")
	kit.eq(b.size, Vector2(960, 672), "table 20x14 cells at 16 px x3")
	kit.eq([(b.over_marks["tooth"] as Array).size(), (b.base_marks["notch"] as Array).size()], [5, 5], "five teeth, five notches")
	kit.eq(pz._state_label.text, UIKit.t("ui.c4p2.halves.state", {"rot": 0, "x": "+0", "y": "+0"}), "pose line")
	kit.eq(pz._joined_label.text, UIKit.t("ui.c4p2.halves.joined", {"n": 0, "total": 5}), "0 of 5")
	kit.eq(pz._stamp_label.text, UIKit.t("ui.c4p2.halves.stamp_open"), "stamp: two halves")
	kit.ok(pz.tip_text() != "", "the mouse way is said once")
	for ic in pz._legend_icons:
		kit.ok(ic.texture != null, "legend icon (drawn by the generator)")
	return true


func _j_keys() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	kit.ok(_key(pz, KEY_RIGHT), "→ consumed")
	kit.eq(pz.pose(), {"rotation_steps": 0, "offset_x": 1, "offset_y": 0}, "RIGHT = offset_x + 1")
	_key(pz, KEY_DOWN)
	kit.eq(pz.pose()["offset_y"], 1, "DOWN = offset_y + 1")
	_key(pz, KEY_A)
	_key(pz, KEY_W)
	kit.eq(pz.pose(), J_START, "WASD move too")
	_key(pz, KEY_R)
	kit.eq(pz.pose()["rotation_steps"], 1, "R = +90°")
	_key(pz, KEY_R, true)
	kit.eq(pz.pose()["rotation_steps"], 0, "Shift+R = −90°")
	_key(pz, KEY_R, true)
	kit.eq(pz.pose()["rotation_steps"], 3, "… mod 4")
	kit.ok(_key(pz, KEY_BACKSPACE), "Backspace consumed (also bound to cancel)")
	kit.eq(pz.pose(), J_START, "Backspace takes back the last move")
	kit.ok(pz.is_open, "Backspace never closes")
	var held: InputEventKey = Spec.key_event(KEY_RIGHT)
	held.echo = true
	pz.modal_input(held)
	kit.eq(pz.pose()["offset_x"], 1, "a held arrow repeats")
	pz.undo()
	kit.ok(_key(pz, KEY_ENTER), "Enter consumed")
	kit.eq(g.puzzle_attempts(J_OBJ), 1, "Enter on the start pose = one attempt")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.halves.wrong_turned"), "start pose: the writing upside down")
	kit.eq(pz.pose(), J_START, "the half stays where it is")
	pz._rotate_btn.grab_focus()
	kit.ok(not _key(pz, KEY_ENTER), "Enter on „Drehen“ is left to the button")
	kit.eq(g.puzzle_attempts(J_OBJ), 1, "… and is no attempt")
	kit.ok(not _key(pz, KEY_ESCAPE), "Esc is left to UIRoot -> handle_cancel")
	kit.ok(pz.handle_cancel() and not pz.is_open, "Esc closes")
	kit.eq(g.objective_state(J_OBJ), "available", "closing is not an attempt")
	return true


func _j_wrong() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	pz.rotate(1)
	var r: Dictionary = pz.submit()
	kit.eq([r.get("solved"), g.puzzle_attempts(J_OBJ)], [false, 1], "a quarter turn: attempt 1")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.halves.wrong_sideways"), "teeth up or down: the writing stands sideways")
	pz.rotate(1)
	kit.eq(pz.feedback_text(), "", "turning clears the note")
	pz.submit()
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.halves.wrong"), "turned right but not laid against: teeth beside the notches")
	kit.eq(pz.pose()["rotation_steps"], 2, "the half stays as it is")
	pz.move(Vector2i(4, 0))
	pz.submit()
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.halves.wrong"), "edge to edge but one row off")
	kit.eq(pz.joined(), 0, "one row off joins no tooth")
	kit.eq(g.objective_state(J_OBJ), "available", "Story unchanged apart from the attempts")
	kit.eq(g.puzzle_attempts(J_OBJ), 3, "three attempts")
	kit.ok(not pz.is_done(), "not solved")
	return true


func _j_hints() -> bool:
	for mode in [0, 1, 2]:
		var g := _story_j(true)
		var pz := _make(J_SCENE, g, mode)
		pz.open(J_OBJ)
		kit.eq(pz.hint_shown(), mode == 2, "mode %d: at once only for 2" % mode)
		pz.submit()
		kit.eq(pz.hint_shown(), mode == 2, "mode %d after one failure" % mode)
		pz.submit()
		kit.eq(pz.hint_shown(), mode >= 1, "mode %d after two failures" % mode)
		kit.eq(pz._hint_label.text, UIKit.t("ui.c4p2.halves.hint"), "hint text")
	return true


func _j_controller() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	kit.ok(_pad(pz, JOY_BUTTON_DPAD_RIGHT), "D-pad consumed")
	_pad(pz, JOY_BUTTON_DPAD_DOWN)
	kit.eq(pz.pose(), {"rotation_steps": 0, "offset_x": 1, "offset_y": 1}, "D-pad moves")
	_pad(pz, JOY_BUTTON_RIGHT_SHOULDER)
	kit.eq(pz.pose()["rotation_steps"], 1, "RB turns +90°")
	_pad(pz, JOY_BUTTON_LEFT_SHOULDER)
	kit.eq(pz.pose()["rotation_steps"], 0, "LB turns back")
	kit.ok(_pad(pz, JOY_BUTTON_Y), "Y consumed")
	kit.eq(pz.pose()["rotation_steps"], 1, "Y takes back the last move")
	kit.ok(_pad(pz, JOY_BUTTON_X), "X consumed")
	kit.eq(pz.pose(), J_START, "X: back on the book")
	kit.ok(_pad(pz, JOY_BUTTON_X, false), "releases swallowed")
	kit.ok(_pad(pz, JOY_BUTTON_A), "A consumed")
	kit.eq(g.puzzle_attempts(J_OBJ), 1, "A lays it against")
	kit.ok(not _pad(pz, JOY_BUTTON_B), "B is left to UIRoot (cancel -> handle_cancel)")
	for k in [JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_RIGHT,
			JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_A]:
		_pad(pz, k)
	kit.eq(g.objective_state(J_OBJ), "complete", "joined by pad alone")
	pz._solved_at -= 1000
	kit.ok(_pad(pz, JOY_BUTTON_B) and not pz.is_open, "B after the guard closes")
	var h := _story_j(true)
	var pz2 := _make(J_SCENE, h)
	pz2.open(J_OBJ)
	kit.ok(_pad(pz2, JOY_BUTTON_BACK) and not pz2.is_open, "Back closes")
	var st := InputEventJoypadMotion.new()
	st.axis = JOY_AXIS_LEFT_X
	st.axis_value = 1.0
	pz2.open(J_OBJ)
	if InputMap.has_action("ui_right") and st.is_action_pressed("ui_right"):
		kit.ok(pz2.modal_input(st) and pz2.pose()["offset_x"] == 1, "left stick moves")
	return true


func _j_mouse() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	var b = pz._board
	var cp: float = b.cp()
	var c: Vector2 = b.over_center()
	kit.ok(b.hit_over(c) and not b.hit_over(Vector2(4, 4)), "the half is hit, the table corner is not")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, c))
	kit.ok(b.is_dragging(), "press on the half starts a drag")
	var mm := InputEventMouseMotion.new()
	mm.position = c + Vector2(cp * 2.4, cp * 0.6)
	b._gui_input(mm)
	kit.eq(pz.pose(), {"rotation_steps": 0, "offset_x": 2, "offset_y": 1}, "drag snaps to whole cells")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, mm.position, false))
	kit.ok(not b.is_dragging(), "release ends the drag")
	kit.eq(pz.history.size(), 1, "one drag = one step back")
	pz.undo()
	kit.eq(pz.pose(), J_START, "Backspace after a drag: back where it started")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_WHEEL_DOWN, c))
	kit.eq(pz.pose()["rotation_steps"], 1, "wheel down turns clockwise")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_WHEEL_UP, c))
	kit.eq(pz.pose()["rotation_steps"], 0, "wheel up turns back")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_RIGHT, c))
	kit.eq(pz.pose()["rotation_steps"], 1, "right-click turns")
	pz._reset_btn.pressed.emit()
	kit.eq(pz.pose(), J_START, "„Zurücksetzen“")
	pz._rotate_btn.pressed.emit()
	pz._rotate_btn.pressed.emit()
	kit.eq(pz.pose()["rotation_steps"], 2, "„Drehen“ twice: the writing stands")
	kit.eq(g.puzzle_attempts(J_OBJ), 0, "no attempt from mouse handling")
	b.begin_drag(b.over_center())
	b.drag_to(b.over_center() + Vector2(cp * 4, cp * 1))
	b.end_drag()
	kit.eq(pz.pose(), J_SOLUTION, "dragged against the Russian half")
	kit.eq([pz.joined(), pz.stamp_closed()], [5, true], "five of five, the stamp a circle")
	pz._check_btn.pressed.emit()
	kit.eq(g.objective_state(J_OBJ), "complete", "„Anlegen“ solves — mouse only")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, b.over_center()))
	kit.ok(not b.is_dragging(), "the joined half does not move")
	pz._close_btn.pressed.emit()
	kit.ok(not pz.is_open, "„Weiter“ closes")
	return true


## Exactly what scripts/core/inputplay.gd::_join_puzzle presses: Enter on the start pose (wrong), then R, R, →×4, ↓
## and Enter.
func _j_inputplay() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	var count := [0]
	pz.solved.connect(func(_id: String) -> void: count[0] += 1)
	pz.open(J_OBJ)
	kit.ok(pz.get("is_open") == true, "is_open after open()")
	kit.ok(str(pz.get_script().resource_path).ends_with("join_puzzle.gd"), "the driver's suffix list finds it")
	kit.ok(_key(pz, KEY_ENTER), "Enter consumed")
	kit.ne(g.objective_state(J_OBJ), "complete", "the start pose is wrong")
	kit.eq(g.puzzle_attempts(J_OBJ), 1, "one attempt")
	for k in [KEY_R, KEY_R, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_DOWN]:
		kit.ok(_key(pz, k), "key consumed")
	kit.eq(pz.pose(), J_SOLUTION, "R, R, →×4, ↓ = the solution pose")
	_key(pz, KEY_ENTER)
	kit.eq(g.objective_state(J_OBJ), "complete", "objective complete through Story.solve_puzzle")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.success_beat() <= 7.0, "auto-close within 7 s (the driver waits 8 s): %.1f" % pz.success_beat())
	return true


func _j_geometry() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	var b = pz._board
	var fits: Array = []
	for r in 4:
		fits.append(b.rotation_fits(r))
	kit.eq(fits, [false, false, true, false], "only half a turn lets the teeth face the notches")
	var full: Array = []
	var partial := 0
	for r in 4:
		var rr: Array = b.off_range(r)
		for x in range(rr[0].x, rr[1].x + 1):
			for y in range(rr[0].y, rr[1].y + 1):
				var j: Dictionary = b.joined_counts(r, Vector2i(x, y))
				if int(j["tooth"]) == 5 and int(j["stamp_half"]) == 1:
					full.append({"rotation_steps": r, "offset_x": x, "offset_y": y})
				elif int(j["tooth"]) > 0 or int(j["stamp_half"]) > 0:
					partial += 1
	kit.eq(full, [J_SOLUTION], "exactly one reachable pose joins every tooth and the stamp — the engine's solution")
	kit.eq(partial, 0, "no other pose joins even one tooth (the count never misleads)")
	b.set_state(2, Vector2i(4, 1))
	kit.eq(b.joined_counts(), {"tooth": 5, "stamp_half": 1, "line_end": 5}, "the solution: teeth, stamp and all five lines meet")
	b.set_state(0, Vector2i(99, -99))
	kit.ok(b.offset.x == b.off_max.x and b.offset.y == b.off_min.y, "offsets clamp at the table's edge")
	# round 10 review: at every extreme pose, in every turn, the whole German half (with its pad) stays on the
	# table and clear of the frame -- the frame never cuts its paper or its writing
	var table := Rect2(Vector2.ZERO, b.size).grow(-6.0)
	var on_table := true
	for r in 4:
		for corner in [Vector2i(-99, -99), Vector2i(99, -99), Vector2i(-99, 99), Vector2i(99, 99)]:
			b.set_state(r, corner)
			var paper: Rect2 = b.over_rect().grow(5.0 * 3.0)       # the red C-17 tab sticks out 5 px
			if not table.encloses(paper):
				on_table = false
				kit.ok(false, "turn %d, offset %s: the German half leaves the table %s" % [r, b.offset, paper])
	kit.ok(on_table, "every extreme pose keeps the German half on the table")
	b.set_state(0, Vector2i(11, -3))
	b.set_state(1, b.offset)
	kit.eq(b.offset, Vector2i(11, -2), "turning at the edge nudges the half back onto the table")
	b.set_state(2, Vector2i(4, 1))
	kit.ok(not b.over_lies_on_base(), "joined halves lie side by side (no shadow across the seam)")
	b.set_state(2, Vector2i(8, 1))
	kit.ok(b.over_lies_on_base(), "a half laid over the other casts its shadow on it")
	var lay = JSON.parse_string(FileAccess.get_file_as_string(J_LAYOUT))
	var st: Dictionary = lay.get("start", {})
	kit.eq({"rotation_steps": int(st.get("rotation_steps", -1)), "offset_x": int(st.get("offset_x", -1)),
		"offset_y": int(st.get("offset_y", -1))}, J_START, "layout start pose")
	kit.eq(int(lay.get("pose_check", {}).get("start_joined", -1)), 0, "the generator verified the start")
	var offs: Array = lay.get("offsets", [])
	kit.eq(offs.size(), 4, "the generator wrote one offset range per turn")
	for o in offs:
		var rr: Array = b.off_range(int(o.get("rotation_steps", -1)))
		kit.eq([int(o["min"][0]), int(o["min"][1]), int(o["max"][0]), int(o["max"][1])], [rr[0].x, rr[0].y, rr[1].x, rr[1].y],
			"UI and generator agree on the offsets of turn %d" % int(o.get("rotation_steps", -1)))
	kit.ok(not lay.has("solution"), "the layout does not carry the answer")
	return true


func _j_correct() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	var count := [0]
	pz.solved.connect(func(id: String) -> void:
		count[0] += 1
		kit.eq(id, J_OBJ, "solved(obj_id)"))
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(J_OBJ)
	pz.rotate(2)
	pz.move(Vector2i(4, 1))
	kit.eq(pz.pose(), J_SOLUTION, "pose")
	kit.eq(pz._joined_label.text, UIKit.t("ui.c4p2.halves.joined", {"n": 5, "total": 5}), "5 of 5 before laying it against")
	kit.eq(pz._stamp_label.text, UIKit.t("ui.c4p2.halves.stamp_closed"), "the stamp closes")
	var r: Dictionary = pz.submit()
	kit.eq([r.get("ok"), r.get("solved")], [true, true], "engine: solved")
	kit.ok(pz.is_done() and pz.success_shown(), "success shown")
	kit.eq([pz.clicks_shown(), pz.ring_shown()], [5, true], "five teeth click in, the stamp ring closes (reduced motion: at once)")
	kit.eq(pz._success_label.text, UIKit.t("ui.c4p2.halves.success"), "success text")
	kit.eq(pz._photo_label.text, UIKit.t("ui.c4p2.halves.photos"), "Ekdahl's two photographs")
	kit.eq(pz._close_btn.text, UIKit.t("ui.c4p2.halves.btn.continue"), "„Weiter“")
	kit.eq(count[0], 1, "solved once")
	kit.ok(not pz.move(Vector2i.LEFT) and not pz.rotate(1) and pz.pose() == J_SOLUTION, "the joined half is locked")
	kit.eq(pz.submit(), {}, "a second submit does nothing")
	kit.ok(_key(pz, KEY_ENTER) and pz.is_open, "Enter inside the guard is swallowed")
	pz._on_beat(pz._beat_token)
	kit.ok(not pz.is_open and closed[0] == 1, "closes by itself after the beat")
	kit.ok(g.has_item("ev_c4_card_ru_original"), "Lev's half is still the player's evidence")
	return true


func _j_text_scale() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g, 2)
	pz.open(J_OBJ)
	pz.submit()
	var s = UIKit.overrides["Settings"]
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()
		kit.eq(pz._feedback.get_theme_font_size("font_size"), int(round(24 * scale)), "note follows %d %%" % int(scale * 100))
		kit.eq(pz._instr.get_theme_font_size("font_size"), int(round(26 * scale)), "instruction follows")
		_fits(pz, "%d %% with note + hint" % int(scale * 100))
	pz.rotate(2)
	pz.move(Vector2i(4, 1))
	pz.submit()
	kit.ok(pz.success_shown(), "success shown")
	# round 10 review: the solved state ran 40 px past the screen at the DEFAULT 100 %
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()
		pz._refresh()
		_fits(pz, "%d %% with the success text" % int(scale * 100))
		kit.ok(pz.success_shown() and not pz._instr.visible, "%d %%: the success card takes the instruction's place" % int(scale * 100))
	for hc in [false, true]:
		s.set_value("high_contrast", hc)
		pz.theme = UIKit.theme(hc)
		s.set_value("text_scale", 1.0)
		UIKit.refresh_text_scale()
		pz._refresh()
		_fits(pz, "100 %% success, high contrast %s" % hc)
	pz.theme = null
	s.set_value("high_contrast", false)
	return true


func _j_contrast() -> bool:
	var g := _story_j(true)
	var pz := _make(J_SCENE, g)
	pz.open(J_OBJ)
	for p in pz.contrast_pairs():
		kit.ok(Spec.contrast(p["fg"], p["bg"]) >= 4.5, "%s: %.2f : 1 >= 4.5" % [p["what"], Spec.contrast(p["fg"], p["bg"])])
	UIKit.overrides["Settings"].set_value("high_contrast", true)
	for p in pz.contrast_pairs():
		kit.ok(Spec.contrast(p["fg"], p["bg"]) >= 7.0, "high contrast — %s: %.2f : 1 >= 7" % [p["what"], Spec.contrast(p["fg"], p["bg"])])
	# shape, not colour: German paper reaches past its body edge (teeth), the Russian edge is cut in (notches)
	var de := _image("res://assets/ui/documents/karsk_c4p2_halves_de.png")
	var ru := _image("res://assets/ui/documents/karsk_c4p2_halves_ru.png")
	kit.eq([de.get_width(), de.get_height(), ru.get_width(), ru.get_height()], [124, 92, 112, 80], "sheet sizes (German padded 6 px)")
	var b = pz._board
	for i in 5:
		var t: Vector2 = b.over_marks["tooth"][i]["at"]
		var n: Vector2 = b.base_marks["notch"][i]["at"]
		var tp := Vector2i(int(6 + t.x + 1), int(6 + t.y))          # inside the tooth, 1 px from its tip (stored, padded)
		var npx := Vector2i(int(n.x - 2), int(n.y))                 # inside the notch
		kit.ok(de.get_pixelv(tp).a > 0.5, "tooth %d: paper beyond the German edge" % (i + 1))
		kit.ok(ru.get_pixelv(npx).a < 0.1, "notch %d: cut into the Russian edge" % (i + 1))
	kit.ok(ru.get_pixel(60, 30).a > 0.9 and de.get_pixel(60, 46).a > 0.9, "the sheets are opaque paper")
	# the German half is stored upside down: its red C-17 tab hangs at the bottom
	var red_bottom := 0
	for x in range(0, 124):
		for y in range(84, 92):
			var c := de.get_pixel(x, y)
			if c.a > 0.5 and c.r > 0.5 and c.g < 0.35:
				red_bottom += 1
	kit.ok(red_bottom > 30, "the red C-17 tab at the bottom: laid in upside down (%d red px)" % red_bottom)
	return true


func _j_refused() -> bool:
	var rs: Node = Spec.RefusingStory.new()
	kit.track(rs)
	var pz := _make(J_SCENE, rs)
	pz.open(J_OBJ)
	var r: Dictionary = pz.submit()
	kit.eq(r.get("ok"), false, "engine refusal passed through")
	kit.ok(pz.feedback_text() != "" and not pz.is_done() and pz.is_open, "refusal named, nothing solved")
	var g := _story_j(false)
	var pz2 := _make(J_SCENE, g)
	pz2.open(J_OBJ)
	var r2: Dictionary = pz2.submit()
	kit.eq(r2.get("error_key"), "sys.err.locked", "locked before Lev lends his half")
	kit.eq(g.puzzle_attempts(J_OBJ), 0, "no attempt counted")
	kit.ok(pz2.feedback_text() != "", "the lock is named")
	return true


# ================================================================== HousePuzzle „Haus 14“
func _h_registered() -> bool:
	_registered(H_OBJ, H_SCENE, H_SCRIPT, "house_puzzle.gd")
	return true


func _h_route() -> bool:
	var g := _story_h(true)
	var p: Dictionary = g.puzzle_for(H_OBJ)
	kit.ok(not p.has("solution"), "the UI never sees the solution")
	kit.eq(p.get("clue_item_ids"), ["ev_c4_house_notice", "ev_c4_house_cards"], "clue items: the notice, the card box")
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	kit.ok(pz.is_open and pz.visible, "open() shows the modal")
	kit.eq([pz.route_ids(), pz.head()], [["s3"], "s3"], "the route starts as [s3], the head on s3")
	var b = pz._board
	kit.eq(b.size, Vector2(948, 738), "the house 316x246 art px at x3")
	kit.eq(Kit_sorted(b.rooms.keys()), Kit_sorted(H_ROOMS), "19 rooms")
	kit.ok(b.tex_board != null and b.tex_night != null and b.tex_konrad != null and b.tex_ilse != null, "renderings and markers loaded")
	kit.eq([pz.cards_on(), pz.lights_on()], [false, false], "Kartei and Licht start off")
	kit.eq(pz._state_label.text, UIKit.t("ui.c4p2.house.state_start"), "Ilse waits in Hanna's flat")
	kit.eq(pz._info_title.text, UIKit.t("ui.c4p2.house.room.s3"), "side panel: the room Ilse stands in")
	kit.eq(pz._info_note.text, UIKit.t("ui.c4p2.house.card", {"note": UIKit.t("ui.c4p2.house.note.s3")}), "… Kuhnert's card")
	kit.ok(pz._info_exits.visible and pz._info_exits.text.contains(UIKit.t("ui.c4p2.house.short.sd"))
		and pz._info_exits.text.contains(UIKit.t("ui.c4p2.house.short.s2")), "… and the passages from here (up: loft, down: Pohl)")
	kit.ok(pz.tip_text() != "", "the mouse way is said once")
	return true


func _h_keys() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	kit.ok(_key(pz, KEY_LEFT), "← consumed")
	kit.eq(pz.route_ids(), ["s3"], "no passage to the left of Hanna's flat")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.house.no_way"), "refused with a soft knock")
	_key(pz, KEY_DOWN)
	kit.eq(pz.route_ids(), ["s3", "s2"], "DOWN: the stairs down to Frau Pohl")
	kit.eq(pz.feedback_text(), "", "a step clears the note")
	_key(pz, KEY_UP)
	kit.eq(pz.route_ids(), ["s3"], "back onto the previous room = undo")
	_key(pz, KEY_W)
	_key(pz, KEY_D)
	kit.eq(pz.route_ids(), ["s3", "sd", "hd"], "W, D: up to the loft, across to the back wing's")
	_key(pz, KEY_S)
	_key(pz, KEY_S)
	kit.eq(pz.head(), "h2", "S: down the back stairs")
	pz.go_to("sd")
	kit.eq(pz.route_ids(), ["s3", "sd"], "onto a room of the route cuts back to it")
	kit.ok(_key(pz, KEY_BACKSPACE), "Backspace consumed (also bound to cancel)")
	kit.eq(pz.route_ids(), ["s3"], "Backspace undoes the last step")
	kit.ok(pz.is_open, "Backspace never closes")
	_key(pz, KEY_UP)
	_key(pz, KEY_RIGHT)
	_key(pz, KEY_R)
	kit.eq(pz.route_ids(), ["s3"], "R: back to Hanna's flat")
	kit.ok(_key(pz, KEY_K) and pz.cards_on(), "K: Kuhnert's card box on")
	kit.eq(pz._cards_btn.text, UIKit.t("ui.c4p2.house.cards_on"), "… said on its button")
	kit.ok(_key(pz, KEY_L) and pz.lights_on(), "L: the 22.40 lights on")
	kit.eq(pz._lights_btn.text, UIKit.t("ui.c4p2.house.lights_on"), "… said on its button")
	_key(pz, KEY_K)
	_key(pz, KEY_L)
	kit.eq([pz.cards_on(), pz.lights_on()], [false, false], "K and L toggle")
	kit.eq(g.puzzle_attempts(H_OBJ), 0, "presentation keys are no attempt")
	kit.ok(_key(pz, KEY_ENTER), "Enter consumed")
	kit.eq(g.puzzle_attempts(H_OBJ), 1, "Enter = one attempt, at once")
	pz._reset_btn.grab_focus()
	kit.ok(not _key(pz, KEY_ENTER), "Enter on „Neu“ is left to the button")
	kit.eq(g.puzzle_attempts(H_OBJ), 1, "… and is no attempt")
	kit.ok(not _key(pz, KEY_ESCAPE), "Esc is left to UIRoot -> handle_cancel")
	kit.ok(pz.handle_cancel() and not pz.is_open, "Esc closes")
	kit.eq(g.objective_state(H_OBJ), "available", "closing is not an attempt")
	return true


func _h_stops() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	var cases := [
		[["s3", "s2"], 1, "ui.c4p2.house.stop.s2", "s2"],
		[["s3", "sd", "vd", "v3", "v2", "v1", "ve"], 6, "ui.c4p2.house.stop.ve", "ve"],
		[["s3", "sd", "hd", "h3", "h2", "h1", "he", "hk", "sk", "se"], 9, "ui.c4p2.house.stop.se", "se"],
		[["s3", "s2", "s1", "se", "sk", "hk", "ws"], 1, "ui.c4p2.house.stop.s2", "s2"],
		[["s3"], 0, "ui.c4p2.house.stop.flat", "s3"],
		[["s3", "sd", "hd", "h3"], 3, "ui.c4p2.house.stop.flat", "h3"],
		[["s3", "sd", "hd", "h3", "h2", "h1", "he", "hk"], 7, "ui.c4p2.house.stop.short", "hk"],
		[["s3", "sd"], 1, "ui.c4p2.house.stop.short", "sd"],
	]
	for c in cases:
		var s: Dictionary = pz.walk_stop(c[0])
		kit.eq([s.get("index"), s.get("key"), s.get("room")], [c[1], c[2], c[3]], "walk %s stops at %s" % [Kit_fmt(c[0]), c[3]])
	var ok: Dictionary = pz.walk_stop(H_SOLUTION)
	kit.ok(bool(ok.get("goal", false)) and str(ok.get("key")) == "", "the answer walks into the workshop")
	# through the UI: the reason in words, the watcher learned, the route kept
	_key(pz, KEY_DOWN)
	_key(pz, KEY_ENTER)
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.house.stop.s2"), "Frau Pohl's spy hole, in words")
	kit.eq([pz.stop_room(), pz.learned_rooms()], ["s2", ["s2"]], "stop mark and the eye stay on Pohl's landing")
	kit.eq(pz.route_ids(), ["s3", "s2"], "the first failure keeps the route")
	kit.eq(g.objective_state(H_OBJ), "available", "Story unchanged apart from the attempt")
	_key(pz, KEY_UP)
	_key(pz, KEY_ENTER)
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.house.stop.flat", {"room": UIKit.t("ui.c4p2.house.room.s3")}),
		"staying in Hanna's flat: the household card, with the room's name")
	kit.eq(g.puzzle_attempts(H_OBJ), 2, "two attempts")
	return true


func _h_trim() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	for k in [KEY_UP, KEY_LEFT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN]:
		_key(pz, k)
	kit.eq(pz.route_ids(), ["s3", "sd", "vd", "v3", "v2", "v1", "ve"], "across the front loft and down to the passage")
	_key(pz, KEY_ENTER)
	kit.eq(pz.route_ids().size(), 7, "failure 1 keeps the route")
	_key(pz, KEY_ENTER)
	kit.eq(pz.route_ids().size(), 7, "failure 2 keeps the route")
	_key(pz, KEY_ENTER)
	kit.eq(pz.route_ids(), ["s3", "sd", "vd", "v3", "v2", "v1"], "failure 3: Ilse waits on the last safe landing")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.house.stop.ve"), "Kuhnert in the passage, in words")
	kit.eq(g.puzzle_attempts(H_OBJ), 3, "three attempts")
	return true


func _h_hints() -> bool:
	for mode in [0, 1, 2]:
		var g := _story_h(true)
		var pz := _make(H_SCENE, g, mode)
		pz.open(H_OBJ)
		kit.eq(pz.hint_shown(), mode == 2, "mode %d: at once only for 2" % mode)
		pz.submit()
		kit.eq(pz.hint_shown(), mode == 2, "mode %d after one failure" % mode)
		pz.submit()
		kit.eq(pz.hint_shown(), mode >= 1, "mode %d after two failures" % mode)
		kit.eq(pz._hint_label.text, UIKit.t("ui.c4p2.house.hint"), "hint text")
	return true


func _h_controller() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	kit.ok(_pad(pz, JOY_BUTTON_DPAD_DOWN), "D-pad consumed")
	kit.eq(pz.route_ids(), ["s3", "s2"], "D-pad moves the head")
	kit.ok(_pad(pz, JOY_BUTTON_B), "B consumed (takes back a step, not the modal)")
	kit.eq(pz.route_ids(), ["s3"], "B: one step back")
	kit.ok(pz.is_open, "B never closes while walking the house")
	_pad(pz, JOY_BUTTON_DPAD_UP)
	_pad(pz, JOY_BUTTON_RIGHT_SHOULDER)
	kit.eq(pz.route_ids(), ["s3"], "RB: Neu")
	kit.ok(_pad(pz, JOY_BUTTON_X) and pz.cards_on(), "X: Kartei")
	kit.ok(_pad(pz, JOY_BUTTON_LEFT_SHOULDER) and pz.lights_on(), "LB: Licht")
	kit.ok(_pad(pz, JOY_BUTTON_X, false), "releases swallowed")
	kit.ok(_pad(pz, JOY_BUTTON_Y), "Y consumed")
	kit.eq(g.puzzle_attempts(H_OBJ), 1, "Y: Probegang")
	kit.ok(_pad(pz, JOY_BUTTON_A), "A consumed")
	kit.eq(g.puzzle_attempts(H_OBJ), 2, "A: Probegang")
	for k in [JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_DPAD_DOWN,
			JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_A]:
		_pad(pz, k)
	kit.eq(g.objective_state(H_OBJ), "complete", "solved by pad alone")
	pz._solved_at -= 1000
	kit.ok(_pad(pz, JOY_BUTTON_B) and not pz.is_open, "B after the guard closes")
	var h := _story_h(true)
	var pz2 := _make(H_SCENE, h)
	pz2.open(H_OBJ)
	kit.ok(_pad(pz2, JOY_BUTTON_BACK) and not pz2.is_open, "Back closes")
	return true


func _room_center(b, id: String) -> Vector2:
	var r: Rect2 = b.rooms[id]["rect"]
	return (r.position + r.size * 0.5) * 3.0


func _motion(pos: Vector2, held: bool) -> InputEventMouseMotion:
	var mm := InputEventMouseMotion.new()
	mm.position = pos
	mm.button_mask = MOUSE_BUTTON_MASK_LEFT if held else 0
	return mm


func _h_mouse() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	var b = pz._board
	for id in H_ROOMS:
		kit.eq(b.room_at(_room_center(b, id)), id, "%s is hit at its centre" % id)
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "sd")))
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "sd"), false))
	kit.eq(pz.route_ids(), ["s3", "sd"], "click a neighbour: one step")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "h1")))
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "h1"), false))
	kit.eq(pz.route_ids(), ["s3", "sd"], "a room further away is no step")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4p2.house.no_way"), "… the soft knock")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "hd")))
	for id in ["h3", "h2", "h1", "he"]:
		b._gui_input(_motion(_room_center(b, id), true))
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "he"), false))
	kit.eq(pz.route_ids(), ["s3", "sd", "hd", "h3", "h2", "h1", "he"], "drag down the back stairs with the button held")
	b._gui_input(_motion(_room_center(b, "hk"), false))
	kit.eq(pz.route_ids().size(), 7, "moving without the button only hovers")
	kit.eq(pz._info_title.text, UIKit.t("ui.c4p2.house.room.hk"), "hover: the side panel names the room")
	kit.eq(pz._info_window.text, UIKit.t("ui.c4p2.house.window_line", {"text": UIKit.t("ui.c4p2.house.window.hk")}), "… and its window at 22.40")
	kit.ok(not pz._info_exits.visible, "passages only for the room Ilse stands in")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "hd")))
	kit.eq(pz.route_ids(), ["s3", "sd", "hd"], "click a room of the route: cut back there")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_RIGHT, _room_center(b, "hd")))
	kit.eq(pz.route_ids(), ["s3", "sd"], "right-click: one step back")
	pz._reset_btn.pressed.emit()
	kit.eq(pz.route_ids(), ["s3"], "„Neu“")
	pz._cards_btn.button_pressed = true
	kit.ok(pz.cards_on(), "„Kartei“ toggles")
	pz._lights_btn.button_pressed = true
	kit.ok(pz.lights_on(), "„Licht“ toggles")
	pz.go_to("sd")
	pz._undo_btn.pressed.emit()
	kit.eq(pz.route_ids(), ["s3"], "„Zurück“")
	kit.eq(g.puzzle_attempts(H_OBJ), 0, "no attempt from mouse handling")
	for id in ["sd", "hd", "h3", "h2", "h1", "he", "hk", "ws"]:
		b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, id)))
		b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, id), false))
	kit.eq(pz.route_ids(), H_SOLUTION, "clicked room by room down to the workshop")
	pz._check_btn.pressed.emit()
	kit.eq(g.objective_state(H_OBJ), "complete", "„Probegang“ solves — mouse only")
	b._gui_input(Spec.mouse_button(MOUSE_BUTTON_LEFT, _room_center(b, "hk")))
	kit.eq(pz.route_ids(), H_SOLUTION, "the solved route is locked")
	pz._close_btn.pressed.emit()
	kit.ok(not pz.is_open, "„Weiter“ closes")
	return true


## Exactly what scripts/core/inputplay.gd::_house_puzzle presses: ↓ + Enter (past Frau Pohl), R, then ↑ → ↓×5 → and
## Enter.
func _h_inputplay() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	var count := [0]
	pz.solved.connect(func(_id: String) -> void: count[0] += 1)
	pz.open(H_OBJ)
	kit.ok(pz.get("is_open") == true, "is_open after open()")
	kit.ok(str(pz.get_script().resource_path).ends_with("house_puzzle.gd"), "the driver's suffix finds it")
	_key(pz, KEY_DOWN)
	kit.ok(_key(pz, KEY_ENTER), "Enter consumed")
	kit.ne(g.objective_state(H_OBJ), "complete", "the way past Frau Pohl is wrong")
	kit.eq(g.puzzle_attempts(H_OBJ), 1, "one attempt")
	for k in [KEY_R, KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_DOWN, KEY_RIGHT]:
		kit.ok(_key(pz, k), "key consumed")
	kit.eq(pz.route_ids(), H_SOLUTION, "R, ↑ → ↓×5 → = the solution")
	_key(pz, KEY_ENTER)
	kit.eq(g.objective_state(H_OBJ), "complete", "objective complete through Story.solve_puzzle")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.success_beat() <= 7.0, "auto-close within 7 s (the driver waits 12 s): %.1f" % pz.success_beat())
	return true


func _h_walk_input() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g, 1, false)
	pz.open(H_OBJ)
	for k in [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_DOWN]:
		_key(pz, k)
	kit.eq(pz.head(), "h2", "a way down the back wing")
	_key(pz, KEY_ENTER)
	kit.ok(pz.is_walking(), "with motion the markers walk the route")
	kit.eq(g.puzzle_attempts(H_OBJ), 1, "the attempt is counted at once, not after the walk")
	var walk_steps: float = pz._board.walk_duration()
	kit.ok(walk_steps <= 1.0 + 0.001 and walk_steps > 0.2, "the walk takes ≤ 1 s (%.2f s)" % walk_steps)
	kit.ok(_key(pz, KEY_R), "a key during the walk is consumed …")
	kit.ok(not pz.is_walking(), "… ends the walk …")
	kit.eq(pz.route_ids(), ["s3"], "… and is then applied (R)")
	_key(pz, KEY_DOWN)
	_key(pz, KEY_ENTER)
	kit.ok(pz.is_walking(), "walking past Pohl")
	pz._board._process(2.0)
	kit.ok(not pz.is_walking(), "the walk ends by itself")
	kit.eq([pz.stop_room(), pz.feedback_text()], ["s2", UIKit.t("ui.c4p2.house.stop.s2")], "it stops at the spy hole, in words")
	kit.ok(pz.handle_cancel() and not pz.is_open, "Esc closes (also during a walk)")
	return true


func _h_graph() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	var lay = JSON.parse_string(FileAccess.get_file_as_string(H_LAYOUT))
	kit.eq(Kit_sorted(lay.get("unsafe", [])), Kit_sorted(H_UNSAFE), "unsafe rooms of the contract")
	kit.eq([lay.get("start"), lay.get("goal")], ["s3", "ws"], "start in Hanna's flat, goal the workshop")
	var want := []
	for w in ["v", "s", "h"]:
		var chain := [w + "k", w + "e", w + "1", w + "2", w + "3", w + "d"]
		for i in 5:
			want.append(Kit_sorted([chain[i], chain[i + 1]]))
	for e in [["vd", "sd"], ["sd", "hd"], ["vk", "sk"], ["sk", "hk"], ["hk", "ws"]]:
		want.append(Kit_sorted(e))
	var have := []
	for e in lay.get("edges", []):
		have.append(Kit_sorted(e))
	kit.eq(Kit_sorted_pairs(have), Kit_sorted_pairs(want), "exactly the contract's passages (stairs, lofts, cellar corridor, workshop stair)")
	for pr in [["ve", "se"], ["se", "he"], ["ve", "he"], ["s1", "h1"], ["v3", "s3"]]:
		kit.ok(not (pz.neighbours(pr[0]) as Array).has(pr[1]), "no passage %s – %s (the courtyard is seen from the lodge)" % pr)
	for id in H_ROOMS:
		var ds := {}
		for n in pz.neighbours(id):
			var d: String = pz._dir_between(id, n)
			kit.ok(d != "" and not ds.has(d), "%s: one passage per arrow (%s -> %s)" % [id, d, n])
			ds[d] = n
	kit.eq([pz.neighbour("s3", "down"), pz.neighbour("hk", "right"), pz.neighbour("sd", "right"), pz.neighbour("s3", "left")],
		["s2", "ws", "hd", ""], "arrows: ↓ from s3 = Pohl, → from the back cellar = the workshop, → along the lofts")
	var ways: Array = []
	var stack: Array = [["s3"]]
	while not stack.is_empty():
		var path: Array = stack.pop_back()
		if path[-1] == "ws":
			ways.append(path)
			continue
		for n in pz.neighbours(path[-1]):
			if not path.has(n) and not H_UNSAFE.has(n):
				stack.append(path + [n])
	kit.eq(ways, [H_SOLUTION], "the UI's passages leave exactly one safe way: the answer")
	var p: Dictionary = g.puzzle_for(H_OBJ)
	kit.eq(Kit_sorted(p.get("display_symbols", [])), Kit_sorted(H_SOLUTION), "the engine's display symbols are rooms of the house")
	return true


func _h_correct() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	var count := [0]
	pz.solved.connect(func(id: String) -> void:
		count[0] += 1
		kit.eq(id, H_OBJ, "solved(obj_id)"))
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(H_OBJ)
	for id in H_SOLUTION.slice(1):
		kit.ok(pz.go_to(id), "step to %s" % id)
	var r: Dictionary = pz.submit()
	kit.eq([r.get("ok"), r.get("solved")], [true, true], "engine: solved")
	kit.ok(pz.is_done() and pz.success_shown(), "success shown")
	kit.eq(pz.success_stage(), 3, "Pietsch's workshop lit, Konrad's red pencil rings it (reduced motion: at once)")
	kit.eq(pz._success_label.text, UIKit.t("ui.c4p2.house.success"), "success text")
	kit.eq(pz._close_btn.text, UIKit.t("ui.c4p2.house.btn.continue"), "„Weiter“")
	kit.eq(count[0], 1, "solved once")
	kit.ok(not pz.step("left") and not pz.undo() and not pz.reset_route() and pz.route_ids() == H_SOLUTION, "the way is locked")
	kit.eq(pz.submit(), {}, "a second submit does nothing")
	kit.ok(_key(pz, KEY_ENTER) and pz.is_open, "Enter inside the guard is swallowed")
	pz._on_beat(pz._beat_token)
	kit.ok(not pz.is_open and closed[0] == 1, "closes by itself after the beat")
	kit.eq(g.available(), ["c4h_talk_wendt"], "Wendt next")
	return true


func _h_text_scale() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g, 2)
	pz.open(H_OBJ)
	_key(pz, KEY_DOWN)
	pz.submit()
	var s = UIKit.overrides["Settings"]
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()
		kit.eq(pz._feedback.get_theme_font_size("font_size"), int(round(23 * scale)), "note follows %d %%" % int(scale * 100))
		kit.eq(pz._info_note.get_theme_font_size("font_size"), int(round(21 * scale)), "card note follows")
		kit.eq(pz._board.text_scale, scale, "the board's nameplates follow")
		_fits(pz, "%d %% with note + hint + room info" % int(scale * 100))
		pz.set_cards(true)
		_fits(pz, "%d %% with Kuhnert's cards" % int(scale * 100))
		pz.set_cards(false)
	pz.reset_route()
	for id in H_SOLUTION.slice(1):
		pz.go_to(id)
	pz.submit()
	kit.ok(pz.success_shown(), "success shown")
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()
		pz._refresh()
		_fits(pz, "%d %% with the success text" % int(scale * 100))
		kit.ok(pz.success_shown() and not pz._instr.visible, "%d %%: the success card takes the instruction's place" % int(scale * 100))
	return true


func _h_contrast() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g)
	pz.open(H_OBJ)
	for p in pz.contrast_pairs():
		kit.ok(Spec.contrast(p["fg"], p["bg"]) >= 4.5, "%s: %.2f : 1 >= 4.5" % [p["what"], Spec.contrast(p["fg"], p["bg"])])
	UIKit.overrides["Settings"].set_value("high_contrast", true)
	for p in pz.contrast_pairs():
		kit.ok(Spec.contrast(p["fg"], p["bg"]) >= 7.0, "high contrast — %s: %.2f : 1 >= 7" % [p["what"], Spec.contrast(p["fg"], p["bg"])])
	# the watchers are told apart by shape: eye, lamp, cap and the stop bar are different silhouettes
	var masks := {}
	for k in ["eye", "lamp", "hat", "stop"]:
		var img := _image("res://assets/ui/puzzle/c4p2_house_%s.png" % k)
		var m := ""
		for y in range(3, 12):
			for x in range(3, 12):
				var c := img.get_pixel(x, y)
				m += "1" if c.a > 0.5 and Spec.luminance(c) < 0.2 else "0"
		masks[k] = m
	kit.ok(masks["eye"] != masks["lamp"] and masks["eye"] != masks["hat"] and masks["lamp"] != masks["hat"], "eye, lamp and cap differ in shape")
	var stop := _image("res://assets/ui/puzzle/c4p2_house_stop.png")
	var bar := 0
	for x in range(3, 12):
		bar += 1 if Spec.luminance(stop.get_pixel(x, 7)) > 0.6 else 0
	var plate := stop.get_pixel(7, 3)
	kit.ok(bar >= 7 and plate.r > plate.g * 1.6, "the stop mark is a light bar across a red disc (%d bar px)" % bar)
	var b = pz._board
	kit.eq(Kit_sorted(b.watch.keys()), Kit_sorted(H_UNSAFE), "a mark for every watcher")
	kit.eq([b.watch["s2"]["mark"], b.watch["se"]["mark"], b.watch["ve"]["mark"]], ["eye", "lamp", "hat"], "Pohl: eye, the lodge: lamp, the passage: cap")
	kit.ok(b.hc, "the board follows high contrast")
	return true


func _h_refused() -> bool:
	var rs: Node = Spec.RefusingStory.new()
	kit.track(rs)
	var pz := _make(H_SCENE, rs)
	pz.open(H_OBJ)
	var r: Dictionary = pz.submit()
	kit.eq(r.get("ok"), false, "engine refusal passed through")
	kit.ok(pz.feedback_text() != "" and not pz.is_done() and pz.is_open, "refusal named, nothing solved")
	kit.ok(not pz.is_walking() and pz.stop_room() == "", "no walk for a refused route")
	var g := _story_h(false)
	var pz2 := _make(H_SCENE, g)
	pz2.open(H_OBJ)
	var r2: Dictionary = pz2.submit()
	kit.eq(r2.get("error_key"), "sys.err.locked", "locked before the card box is read")
	kit.eq(g.puzzle_attempts(H_OBJ), 0, "no attempt counted")
	kit.ok(pz2.feedback_text() != "", "the lock is named")
	return true


## Round 10 review: the figures stand on floors (never in a slab, never floating) and walk the stairs.
func _h_figures() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g, 1, false)
	pz.open(H_OBJ)
	var b = pz._board
	var lay = JSON.parse_string(FileAccess.get_file_as_string(H_LAYOUT))
	var edges: Array = lay.get("edges", [])
	var ways: Array = lay.get("paths", [])
	kit.eq(ways.size(), edges.size(), "one way per passage")
	var bad := []
	for i in mini(edges.size(), ways.size()):
		var w: Array = ways[i]
		var a := str(edges[i][0])
		var c := str(edges[i][1])
		if Vector2(float(w[0][0]), float(w[0][1])) != b.stand_of(a) or Vector2(float(w[w.size() - 1][0]), float(w[w.size() - 1][1])) != b.stand_of(c):
			bad.append(a + ">" + c)
		for k in range(1, w.size()):
			var dx := absf(float(w[k][0]) - float(w[k - 1][0]))
			var dy := absf(float(w[k][1]) - float(w[k - 1][1]))
			if dy > 0.0 and (dx < 8.0 or dy / dx > 1.8):
				bad.append("%s>%s step %d" % [a, c, k])
	kit.eq(bad, [], "every way runs from place to place, level or along a flight")
	for id in b.rooms:                                   # every place is inside its room, on its floor
		var st: Vector2 = b.stand_of(id)
		var r: Rect2 = b.rooms[id]["rect"]
		kit.ok(r.has_point(st - Vector2(0, 1)), "%s: the place %s is inside the room" % [id, st])
	var routes := [H_SOLUTION, ["s3", "s2", "s1", "se"], ["s3", "sd", "vd", "v3", "v2", "v1", "ve", "vk", "sk"]]
	for rt in routes:
		pz.reset_route()
		for i in range(1, rt.size()):
			kit.ok(pz.go_to(str(rt[i])), "route step to %s" % rt[i])
			var m: Dictionary = b.figures()
			var head := str(rt[i])
			kit.eq(m["ilse"], b.stand_of(head), "%s: Ilse stands at her place on the floor" % head)
			var pts: PackedVector2Array = b.way_points(pz.route_ids(), pz.route_ids().size() - 1)
			kit.ok(_on_poly(pts, m["konrad"]), "%s: Konrad stands on the way behind her %s" % [head, m["konrad"]])
			kit.ok(Vector2(m["konrad"]).distance_to(m["ilse"]) >= 8.0, "%s: Konrad a step behind, not in Ilse (%.1f px)" % [head, Vector2(m["konrad"]).distance_to(m["ilse"])])
	pz.reset_route()
	var m0: Dictionary = b.figures()
	kit.eq(Vector2(m0["ilse"]).y, Vector2(m0["konrad"]).y, "start: side by side on Hanna's landing")
	kit.ok(int(m0["ilse_face"]) == -int(m0["konrad_face"]), "start: face to face")
	for k in H_SOLUTION.slice(1):
		pz.go_to(k)
	b.start_walk(pz.route_ids(), pz.route_ids().size() - 1)
	var off := 0
	var pts2: PackedVector2Array = b.walk_pts
	var kp := PackedVector2Array([Vector2(b.rooms["s3"]["mate"])])
	kp.append_array(pts2)
	for i in 41:
		b.walk_s = b.walk_len * float(i) / 40.0
		var mm: Dictionary = b.figures()
		off += 0 if _on_poly(pts2, mm["ilse"]) else 1
		off += 0 if _on_poly(kp, mm["konrad"]) else 1
	kit.eq(off, 0, "walking: both figures on the stairs and floors all the way")
	kit.ok(b.walk_duration() <= 1.0, "the whole way down takes ≤ 1 s (%.2f s)" % b.walk_duration())
	b.finish_walk()
	kit.eq(b.figures()["ilse"], b.stand_of("ws"), "they arrive in the workshop")
	return true


static func _on_poly(pts: PackedVector2Array, p: Vector2) -> bool:
	if pts.size() == 1:
		return pts[0].distance_to(p) < 0.5
	for i in range(1, pts.size()):
		if Geometry2D.get_closest_point_to_segment(p, pts[i - 1], pts[i]).distance_to(p) < 0.5:
			return true
	return false


## Round 10 review: the stop mark never covers a figure; Kuhnert's cards keep their marks off the writing and use one
## note size (long notes wrap); the red ring stays on the board.
func _h_overlays() -> bool:
	var g := _story_h(true)
	var pz := _make(H_SCENE, g, 1, true)
	var b = pz._board
	var s = UIKit.overrides["Settings"]
	var cases := {"s2": ["s3", "s2"], "se": ["s3", "s2", "s1", "se"], "ve": ["s3", "sd", "vd", "v3", "v2", "v1", "ve"],
		"flat": ["s3", "sd", "hd", "h3", "h2"], "short": ["s3", "sd", "hd", "h3", "h2", "h1", "he", "hk"]}
	for hc in [false, true]:
		s.set_value("high_contrast", hc)
		for scale in [1.0, 1.5]:
			s.set_value("text_scale", scale)
			UIKit.refresh_text_scale()
			for key in cases:
				pz.open(H_OBJ)
				for id in cases[key].slice(1):
					pz.go_to(id)
				pz.set_cards(key in ["se", "ve"])
				pz.submit()
				kit.ok(pz.stop_room() != "", "%s: the walk stopped" % key)
				var ms: Vector2 = b.mark_size("stop")
				var sr := Rect2(b.stop_mark_at() - ms * 0.5, ms)
				var hit := false
				for r in b.figure_rects():
					hit = hit or sr.intersects(r)
				kit.ok(not hit, "%s (hc %s, %d %%): the stop mark keeps clear of Ilse and Konrad" % [key, hc, int(scale * 100)])
				var over_text := ""
				for id in b.rooms:
					var lr: Rect2 = b.card_rect(id) if b.cards else b.label_rect(id)
					if lr.size.x > 0.0 and sr.intersects(lr):
						over_text = id
				kit.eq(over_text, "", "%s (hc %s, %d %%): the stop mark keeps off the nameplates and cards" % [key, hc, int(scale * 100)])
				kit.ok(Rect2(Vector2.ZERO, b.size).encloses(sr), "%s: the stop mark is on the board" % key)
				pz.close()
	pz.open(H_OBJ)
	pz.set_cards(true)
	for hc in [false, true]:
		s.set_value("high_contrast", hc)
		pz._refresh()
		for scale in [1.0, 1.25, 1.5]:
			s.set_value("text_scale", scale)
			UIKit.refresh_text_scale()
			pz._refresh()
			var sizes := {}
			for id in b.rooms:
				var cl: Dictionary = b.card_layout(id)
				sizes[int(cl["note_fs"])] = true
				kit.ok(Rect2(Vector2.ZERO, b.size).encloses(cl["card"]), "%s: the card stays on the board" % id)
				if b.watch.has(id):
					var msz: Vector2 = b.mark_size(str(b.watch[id]["mark"]))
					var mr := Rect2(b.card_mark_at(id) - msz * 0.5, msz)
					kit.ok(not mr.intersects(cl["text"]), "%s (hc %s, %d %%): the mark hangs clear of the card's writing" % [id, hc, int(scale * 100)])
			kit.eq(sizes.size(), 1, "one note size on every card at %d %% (long notes wrap, none shrinks)" % int(scale * 100))
	s.set_value("high_contrast", false)
	s.set_value("text_scale", 1.0)
	UIKit.refresh_text_scale()
	var cs := Vector2(b.tex_circle.get_size()) * 3.0 if b.tex_circle != null else Vector2.ZERO
	var cr := Rect2(b.circle_at * 3.0 - cs * 0.5, cs)
	kit.ok(cs.x > 0.0 and Rect2(Vector2.ZERO, b.size).encloses(cr), "Konrad's red ring stays on the board %s" % cr)
	kit.ok(cr.encloses(b.room_rect_px("ws").grow(-6.0)), "… and rings the workshop")
	return true


# ================================================================== art + texts
func _art() -> bool:
	for f in ["res://assets/ui/documents/karsk_c4p2_halves_de.png", "res://assets/ui/documents/karsk_c4p2_halves_ru.png",
			"res://assets/ui/puzzle/c4p2_halves_table.png", "res://assets/ui/puzzle/c4p2_halves_snap.png",
			"res://assets/ui/puzzle/c4p2_halves_ring.png", "res://assets/ui/puzzle/c4p2_halves_click.png",
			"res://assets/ui/puzzle/c4p2_house_board.png", "res://assets/ui/puzzle/c4p2_house_night.png",
			"res://assets/ui/puzzle/c4p2_house_anim.png", "res://assets/ui/puzzle/c4p2_house_konrad.png",
			"res://assets/ui/puzzle/c4p2_house_ilse.png", "res://assets/ui/puzzle/c4p2_house_eye.png",
			"res://assets/ui/puzzle/c4p2_house_lamp.png", "res://assets/ui/puzzle/c4p2_house_hat.png",
			"res://assets/ui/puzzle/c4p2_house_stop.png", "res://assets/ui/puzzle/c4p2_house_circle.png",
			"res://assets/ui/puzzle/c4p2_house_ws_lit.png", J_LAYOUT, H_LAYOUT]:
		kit.ok(FileAccess.file_exists(f), "%s exists (tools/pixelgen/gen_ui_c4p2.py)" % f)
	var jl = JSON.parse_string(FileAccess.get_file_as_string(J_LAYOUT))
	kit.eq([jl.get("generator"), jl.get("puzzle_id"), jl.get("objective")], ["tools/pixelgen/gen_ui_c4p2.py", "pz_c4_halves", J_OBJ], "join layout provenance")
	kit.eq(jl.get("pose_check", {}).get("rotation_fits"), [false, false, true, false], "the generator found one fitting rotation")
	var tab := _image("res://assets/ui/puzzle/c4p2_halves_table.png")
	kit.eq([tab.get_width(), tab.get_height()], [320, 224], "the table is the board (20x14 cells of 16 px)")
	var hl = JSON.parse_string(FileAccess.get_file_as_string(H_LAYOUT))
	kit.eq([hl.get("generator"), hl.get("puzzle_id"), hl.get("objective")], ["tools/pixelgen/gen_ui_c4p2.py", "pz_c4_house", H_OBJ], "house layout provenance")
	kit.eq(int(hl.get("graph_check", {}).get("safe_paths", -1)), 1, "the generator found one safe way")
	var board := _image("res://assets/ui/puzzle/c4p2_house_board.png")
	var night := _image("res://assets/ui/puzzle/c4p2_house_night.png")
	kit.eq([board.get_width(), board.get_height(), night.get_width(), night.get_height()], [316, 246, 316, 246], "two renderings of one house")
	# 22.40: lit windows are warm and bright, dark windows dark — checked at the window centres of the layout
	var lit: Array = hl.get("lit", [])
	for id in hl.get("rooms", {}):
		for w in hl["rooms"][id].get("windows", []):
			var l := 0.0
			var warm := 0
			var iw := int(w[2]) - 2
			var ih := int(w[3]) - 2
			for y in range(int(w[1]) + 1, int(w[1]) + 1 + ih):
				for x in range(int(w[0]) + 1, int(w[0]) + 1 + iw):
					var c := night.get_pixel(x, y)
					l += Spec.luminance(c)
					warm += 1 if c.r > c.b else 0
			l /= float(iw * ih)
			if lit.has(id):
				kit.ok(l > 0.10 and warm > iw * ih / 2, "%s: lit at 22.40 (mean lum %.3f)" % [id, l])
			elif (hl.get("dim", []) as Array).has(id):
				kit.ok(l > 0.03 and l < 0.12 and warm > iw * ih / 3, "%s: a dim light behind the curtain (mean lum %.3f)" % [id, l])
			else:
				kit.ok(l < 0.05, "%s: dark at 22.40 (mean lum %.3f)" % [id, l])
	kit.eq(hl.get("dim", []), ["s2"], "Pohl's window is dim at 22.40, as the courtyard shows it")
	# the walking figures: standing + a four-frame walk, shaded (not flat fills), feet on the frame's shoe row
	var figs: Dictionary = hl.get("figures", {})
	for who in ["konrad", "ilse"]:
		var fd: Dictionary = figs.get(who, {})
		var fimg := _image("res://assets/ui/puzzle/" + str(fd.get("file", "")))
		var fw2 := int(fd.get("frame", [0, 0])[0])
		var fh2 := int(fd.get("frame", [0, 0])[1])
		var n := int(fd.get("frames", 0))
		kit.ok(fimg != null and n >= 5 and fimg.get_width() == fw2 * n and fimg.get_height() == fh2,
			"%s: %d frames of %dx%d" % [who, n, fw2, fh2])
		if fimg == null:
			continue
		for i in n:
			var cols := {}
			var rows_used := {}
			for y in fh2:
				for x in fw2:
					var c := fimg.get_pixel(i * fw2 + x, y)
					if c.a > 0.5:
						cols[c.to_html(false)] = true
						rows_used[y] = true
			kit.ok(cols.size() >= (14 if who == "konrad" else 12), "%s frame %d: shaded, with a face (%d colours)" % [who, i, cols.size()])
			kit.ok(rows_used.has(int(fd["feet"][1])) and not rows_used.has(int(fd["feet"][1]) + 2), "%s frame %d: the shoes stand on the feet row" % [who, i])
	var anim := _image("res://assets/ui/puzzle/c4p2_house_anim.png")
	var af: Array = hl.get("marks", {}).get("anim_frame", [15, 21])
	var fw := int(af[0])
	var fh := int(af[1])
	kit.eq([anim.get_width(), anim.get_height()], [fw * 2 * (hl.get("anims", []) as Array).size(), fh], "two frames per animated window")
	for a in hl.get("anims", []):
		var f0: int = a["frames"][0]
		var f1: int = a["frames"][1]
		kit.eq([int(a["rect"][2]), int(a["rect"][3])], [fw, fh], "%s: frame = window size" % a["window"])
		var diff := 0
		for y in fh:
			for x in fw:
				if anim.get_pixel(f0 * fw + x, y) != anim.get_pixel(f1 * fw + x, y):
					diff += 1
		kit.ok(diff > 0, "%s: the two frames differ (%d px)" % [a["window"], diff])
	return true


func _loc_keys() -> bool:
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var keys := []
	for k in ["title", "subtitle", "instruction", "legend.teeth", "legend.stamp", "legend.lines", "wrong", "wrong_turned",
			"wrong_sideways", "hint", "success", "btn.check", "btn.rotate", "btn.reset", "btn.close", "btn.continue",
			"state", "joined", "stamp_open", "stamp_closed", "tip_mouse", "tip_pad", "error", "stamp", "photos",
			"hint_move", "hint_rotate", "hint_drag", "hint_undo", "hint_check", "controls", "board_tip"]:
		keys.append("ui.c4p2.halves." + k)
	for k in ["title", "subtitle", "instruction", "hint", "success", "no_way", "stop.s2", "stop.se", "stop.ve",
			"stop.flat", "stop.short", "btn.check", "btn.undo", "btn.reset", "btn.cards", "btn.lights", "btn.close",
			"btn.continue", "cards_on", "cards_off", "lights_on", "lights_off", "legend.eye", "legend.lamp",
			"legend.hat", "state", "state_start", "walking", "card", "window_line", "exits", "wrong", "error", "stamp",
			"tip_mouse", "tip_pad", "hint_move", "hint_undo", "hint_reset", "hint_cards", "hint_lights", "hint_check",
			"controls", "board_tip", "place", "wing.v", "wing.s", "wing.h", "wing.w"]:
		keys.append("ui.c4p2.house." + k)
	for id in H_ROOMS:
		for k in ["room.", "note.", "short.", "tag.", "window."]:
			keys.append("ui.c4p2.house." + k + id)
	for f in ["d", "3", "2", "1", "e", "k"]:
		keys.append("ui.c4p2.house.floor." + f)
		keys.append("ui.c4p2.house.floor_short." + f)
	for k in keys:
		kit.ok(loc.has(k) and loc.t(k).strip_edges() != "", "Loc key %s" % k)
	for k in keys:
		var t: String = loc.t(k)
		kit.ok(not t.contains("\""), "%s: German quotes only" % k)
	var own = JSON.parse_string(FileAccess.get_file_as_string("res://data/locale/de_c4p2_puzzles.json"))
	var story = JSON.parse_string(FileAccess.get_file_as_string("res://data/locale/de_c4p2_ui.json"))
	var dup := []
	for k in own.get("strings", {}):
		if story.get("strings", {}).has(k):
			dup.append(k)
	kit.eq(dup, [], "the puzzle stream's file only adds keys (the story's texts stay the story's)")
	for k in ["window.s3", "window.ws", "window.ve"]:
		kit.ok(loc.t("ui.c4p2.house." + k).length() <= 140, "%s: one short line" % k)
	return true


# ------------------------------------------------------------------ small pure helpers
static func Kit_sorted(v) -> Array:
	var a: Array = (v as Array).map(func(x) -> String: return str(x))
	a.sort()
	return a


static func Kit_sorted_pairs(v: Array) -> Array:
	var a: Array = v.map(func(p) -> String: return "%s-%s" % [p[0], p[1]])
	a.sort()
	return a


static func Kit_fmt(v) -> String:
	return JSON.stringify(v)
