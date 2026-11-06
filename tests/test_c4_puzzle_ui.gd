extends RefCounted
## Chapter-4 puzzle UIs (documentation/C4_DESIGN.md §2.7): the number chain „Die Nummernkette“
## (scenes/ui/TracePuzzle.tscn, c4c_solve_numbers) and the route overlay „Linie 74“ (scenes/ui/RoutePuzzle.tscn,
## c4b_solve_routes).  Both are registered in data/chapters/c4.json, instanced by ChapterExt and driven here
## stand-alone (headless) against a REAL Story engine instance (public API only) plus mock Settings/Audio injected
## through ui_kit overrides.  Covers per puzzle: registration, the real route opens it, keys / pad / mouse
## contracts, the exact key sequence of scripts/core/inputplay.gd, wrong answers (no Story change except the
## attempt, words for the reason), hints (puzzle_hints 0/1/2 and after two failures), success (marks, `solved`
## once, beat ≤ 7 s, confirm closes after the guard), 125 % / 150 % (fits 1920x1080), WCAG contrast of every text
## the board draws itself (also in high contrast), engine refusals, Loc keys and the art + layout metadata of
## tools/pixelgen/gen_ui_c4.py (the paint-layer chain and the overlay geometry match data/v3/puzzles.json).

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const T_SCENE := "res://scenes/ui/TracePuzzle.tscn"
const T_SCRIPT := "res://scripts/ui/trace_puzzle.gd"
const T_BOARD := "res://assets/ui/puzzle/c4_numbers_board.json"
const T_OBJ := "c4c_solve_numbers"
const T_SOLUTION := ["n24318", "c1742", "n47702", "c1745"]
const T_DISPLAY := ["c1745", "n47702", "n24318", "c1742"]
const R_SCENE := "res://scenes/ui/RoutePuzzle.tscn"
const R_SCRIPT := "res://scripts/ui/route_puzzle.gd"
const R_LAYOUT := "res://assets/ui/documents/berlin_c4_routes.json"
const R_OBJ := "c4b_solve_routes"
const R_SOLUTION := {"rotation_steps": 1, "offset_x": 3, "offset_y": -2}
const R_START := {"rotation_steps": 0, "offset_x": 0, "offset_y": 0}


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"puzzle_hints": 1, "reduced_motion": true, "text_scale": 1.0, "high_contrast": false}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


class MockAudio extends Node:
	var played: Array = []

	func ui(id) -> void:
		played.append(str(id))


## The engine refuses although the objective is open (inventory without the clue items).
class RefusingStory extends Node:
	var calls := 0

	func puzzle_hint_available(_id) -> bool:
		return false

	func solve_puzzle(_id, _answer) -> Dictionary:
		calls += 1
		return {"ok": false, "error": "Missing clues for puzzle", "error_key": "sys.err.missing_clues"}


class FakeRoot extends Control:
	var toast_layer: Control


class FakeGame extends Node:
	var ui: Node


var kit: TKit
var _saved: Dictionary = {}


func run() -> Array:
	kit = TKit.new()
	_saved = UIKit.overrides.duplicate()
	kit.run_case("trace_registered_and_instanced_by_chapter_ext", _t_registered)
	kit.run_case("trace_real_route_opens_the_board", _t_route)
	kit.run_case("trace_incomplete_submit_counts_no_attempt", _t_incomplete)
	kit.run_case("trace_wrong_chain_one_attempt_plates_kept_reason_named", _t_wrong)
	kit.run_case("trace_hint_follows_settings_and_attempts", _t_hints)
	kit.run_case("trace_keys_1_4_backspace_r_l_enter", _t_keys)
	kit.run_case("trace_lamp_is_presentation_only", _t_lamp)
	kit.run_case("trace_mouse_pick_post_drag_right_click_hover", _t_mouse)
	kit.run_case("trace_controller_contract", _t_controller)
	kit.run_case("trace_inputplay_key_sequence_solves", _t_inputplay)
	kit.run_case("trace_correct_chain_rolls_into_the_siding_once", _t_correct)
	kit.run_case("trace_text_scale_125_150_fits", _t_text_scale)
	kit.run_case("trace_contrast_and_number_strokes", _t_contrast)
	kit.run_case("trace_refused_or_missing_story_never_breaks", _t_refused)
	kit.run_case("trace_art_and_paint_layer_chain", _t_art)
	kit.run_case("route_registered_and_instanced_by_chapter_ext", _r_registered)
	kit.run_case("route_real_route_opens_at_the_start_pose", _r_route)
	kit.run_case("route_keys_move_turn_undo_enter_esc", _r_keys)
	kit.run_case("route_wrong_feedback_turned_vs_offset", _r_wrong)
	kit.run_case("route_hint_follows_settings_and_attempts", _r_hints)
	kit.run_case("route_controller_contract", _r_controller)
	kit.run_case("route_mouse_drag_wheel_buttons", _r_mouse)
	kit.run_case("route_inputplay_key_sequence_solves", _r_inputplay)
	kit.run_case("route_geometry_only_the_solution_aligns", _r_geometry)
	kit.run_case("route_correct_pose_marks_pairs_and_signature_once", _r_correct)
	kit.run_case("route_text_scale_125_150_fits", _r_text_scale)
	kit.run_case("route_contrast", _r_contrast)
	kit.run_case("route_refused_or_missing_story_never_breaks", _r_refused)
	kit.run_case("loc_keys_exist", _loc_keys)
	UIKit.overrides = _saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Plays the canonical route through the public Story API up to the number chain (card + stencils inspected).
static func play_to_numbers(k: TKit, g: Node, with_clues := true) -> bool:
	k.play_until(g, "c4b")
	if with_clues:
		g.inspect("c4c_inspect_card")
		g.inspect("c4c_inspect_stencils")
	return g.is_available(T_OBJ) == with_clues


## … up to the route overlay (notice read, Marta's route board received).
static func play_to_routes(k: TKit, g: Node, with_clues := true) -> bool:
	k.play_until(g, "c4a")
	g.inspect("c4b_inspect_notice")
	if with_clues:
		k.play_dialogue(g, "c4b_talk_marta")
	return g.is_available(R_OBJ) == with_clues


func _story_t(with_clues := true) -> Node:
	var g := kit.story()
	kit.ok(play_to_numbers(kit, g, with_clues), "route to the number chain (clues: %s)" % with_clues)
	return g


func _story_r(with_clues := true) -> Node:
	var g := kit.story()
	kit.ok(play_to_routes(kit, g, with_clues), "route to the overlay (clues: %s)" % with_clues)
	return g


func _make(scene: String, story, hints := 1) -> Control:
	var settings := MockSettings.new()
	settings.values["puzzle_hints"] = hints
	kit.track(settings)
	var audio := MockAudio.new()
	kit.track(audio)
	UIKit.overrides = {"Story": story, "Settings": settings, "Audio": audio}
	var pz: Control = load(scene).instantiate()
	kit.track(pz)
	(Engine.get_main_loop() as SceneTree).root.add_child(pz)
	return pz


static func key_event(code: int, pressed := true, shift := false) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = code as Key
	ev.physical_keycode = code as Key
	ev.pressed = pressed
	ev.shift_pressed = shift
	return ev


static func pad_event(button: int, pressed := true) -> InputEventJoypadButton:
	var ev := InputEventJoypadButton.new()
	ev.button_index = button as JoyButton
	ev.pressed = pressed
	return ev


static func mouse_button(button: int, pos: Vector2, pressed := true) -> InputEventMouseButton:
	var ev := InputEventMouseButton.new()
	ev.button_index = button as MouseButton
	ev.position = pos
	ev.pressed = pressed
	return ev


func _fill(pz: Control, ids: Array) -> void:
	for id in ids:
		pz.place(str(id))


## Lays the modal out synchronously at 1920x1080 (tests run inside one frame).
static func force_layout(pz: Control) -> void:
	if pz.theme == null:
		pz.theme = UIKit.theme(UIKit.high_contrast())
	pz.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	pz.size = Vector2(1920, 1080)
	var panel: Control = pz.get("_panel")
	panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	for _pass in 4:
		panel.position = Vector2(28, 10)
		panel.size = Vector2(1920 - 56, 1080 - 20)
		_sort(panel)


static func _sort(n: Node) -> void:
	if n is Container:
		n.notification(Container.NOTIFICATION_SORT_CHILDREN)
	for c in n.get_children():
		if c is Label or c is RichTextLabel:
			c.notification(Control.NOTIFICATION_THEME_CHANGED)
		_sort(c)


static func luminance(c: Color) -> float:
	var f := func(v: float) -> float: return v / 12.92 if v <= 0.04045 else pow((v + 0.055) / 1.055, 2.4)
	return 0.2126 * f.call(c.r) + 0.7152 * f.call(c.g) + 0.0722 * f.call(c.b)


static func contrast(a: Color, b: Color) -> float:
	var la := luminance(a)
	var lb := luminance(b)
	return (maxf(la, lb) + 0.05) / (minf(la, lb) + 0.05)


func _registered_common(obj: String, scene: String, script: String, suffix: String) -> Node:
	var c4 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c4.json"))
	kit.eq(str(c4.get("puzzles", {}).get(obj, "")), scene, "data/chapters/c4.json registers %s" % scene)
	var root := FakeRoot.new()
	kit.track(root)
	root.toast_layer = Control.new()
	root.add_child(root.toast_layer)
	var game := FakeGame.new()
	kit.track(game)
	game.ui = root
	UIKit.overrides = {"Settings": MockSettings.new(), "Audio": MockAudio.new()}
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


# ================================================================== TracePuzzle
func _t_registered() -> bool:
	var node := _registered_common(T_OBJ, T_SCENE, T_SCRIPT, "trace_puzzle.gd")
	if node != null:
		kit.eq(node.get("symbols"), T_DISPLAY, "default tray order = display_symbols of pz_c4_numbers")
	return true


func _t_route() -> bool:
	var g := _story_t(true)
	var p: Dictionary = g.puzzle_for(T_OBJ)
	kit.eq(p.get("display_symbols"), T_DISPLAY, "display_symbols of pz_c4_numbers")
	kit.ok(not p.has("solution"), "the UI never sees the solution")
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	kit.ok(pz.is_open and pz.visible, "open() shows the modal")
	kit.eq(pz.symbols, T_DISPLAY, "tray follows display_symbols")
	kit.eq(pz.slots, ["", "", "", ""], "four empty hooks")
	var tray: Array = []
	for cell in pz._tray_grid.get_children():
		for b in cell.find_children("Plate_*", "Button", true, false):
			tray.append(str(b.name).trim_prefix("Plate_"))
	kit.eq(tray, T_DISPLAY, "tray plates in display order")
	for i in 4:
		kit.eq(pz._post_names[i].text, UIKit.t("ui.c4.numbers.post.%d" % (i + 1)), "post %d named" % (i + 1))
		kit.eq(pz._post_logs[i].text, UIKit.t("ui.c4.numbers.log.%d" % (i + 1)), "post %d: switch book line" % (i + 1))
		var r: Rect2 = pz.post_rect(i)
		kit.eq(r.size, Vector2(264, 75), "post %d plate place 88x25 at x3" % (i + 1))
	var slate: TextureRect = pz._board.get_node("Slate")
	kit.ok(slate.texture != null and slate.size == slate.texture.get_size() * 3.0, "slate shown at exactly x3")
	kit.eq(pz.wagon_at(), -1, "the wagon waits at the yard")
	kit.eq(pz.wagon_number(), "", "… without a number")
	kit.ok(not pz.lamp and not pz.lamp_list_shown(), "lamp off, no list")
	kit.eq(pz._state_label.text, UIKit.t("ui.c4.numbers.state", {"n": 0, "total": 4}), "state 0 of 4")
	kit.ok(pz.tip_text() != "", "the mouse / pad way is said once")
	return true


func _t_incomplete() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	_fill(pz, ["n24318", "c1742"])
	var r: Dictionary = pz.submit()
	kit.eq(r, {}, "nothing submitted")
	kit.eq(g.puzzle_attempts(T_OBJ), 0, "no attempt")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.numbers.incomplete"), "incomplete note")
	kit.eq(pz.slots, ["n24318", "c1742", "", ""], "plates stay")
	return true


func _t_wrong() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	_fill(pz, T_DISPLAY)
	kit.eq(pz.slots, T_DISPLAY, "tray order hung W1 … W4")
	var r: Dictionary = pz.submit()
	kit.eq([r.get("ok"), r.get("solved"), g.puzzle_attempts(T_OBJ)], [true, false, 1], "one attempt, not solved")
	kit.eq(g.objective_state(T_OBJ), "available", "Story unchanged apart from the attempt")
	kit.eq(pz.slots, T_DISPLAY, "the plates stay on the hooks")
	kit.eq(pz.halt_post, 0, "the trial run stops at W 1 (C-17/45 lies over an older number)")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.numbers.wrong_first", {"piece": "C-17/45", "under": "47 702"}), "reason in words")
	kit.ok(pz.halt_shown(), "red chalk ring with a cross at the stop")
	kit.eq(pz.wagon_at(), 0, "the wagon stands at W 1")
	kit.ok(not pz.is_done() and not pz.success_shown(), "not solved")
	# a chain that breaks later: W 2
	pz.reset_order()
	kit.ok(not pz.halt_shown() and pz.feedback_text() == "", "a board change clears stop mark and note")
	_fill(pz, ["n24318", "n47702", "c1742", "c1745"])
	pz.submit()
	kit.eq(g.puzzle_attempts(T_OBJ), 2, "second attempt")
	kit.eq(pz.halt_post, 1, "stops at W 2")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.numbers.wrong", {"post": "W 2", "piece": "47 702", "under": "C-17/42",
		"prev": "24 318"}), "W 2: under „47 702“ lies „C-17/42“, not „24 318“")
	kit.ok(pz.feedback_text().contains("„") and pz.feedback_text().contains("“"), "German quotes")
	kit.eq(pz.wagon_at(), 1, "the wagon rolled to W 2 and stopped")
	# every possible break kind has words
	kit.ok(pz._wrong_text({"post": 2, "kind": "bare", "piece": "n24318", "under": "", "prev": "c1742"}).contains("24 318"), "bare-metal reason")
	kit.eq(pz._wrong_text({}), UIKit.t("ui.c4.numbers.wrong_generic"), "generic reason")
	kit.eq(pz.chain_break(T_SOLUTION), {}, "the true chain has no break (lamp table)")
	return true


func _t_hints() -> bool:
	for mode in [0, 1, 2]:
		var g := _story_t(true)
		var pz := _make(T_SCENE, g, mode)
		pz.open(T_OBJ)
		kit.eq(pz.hint_shown(), mode == 2, "mode %d: hint at once only for 2" % mode)
		_fill(pz, T_DISPLAY)
		pz.submit()
		kit.eq(pz.hint_shown(), mode == 2, "mode %d after one failure" % mode)
		pz.submit()
		kit.eq(g.puzzle_hint_available(T_OBJ), true, "engine: hint after two failures")
		kit.eq(pz.hint_shown(), mode >= 1, "mode %d after two failures" % mode)
		kit.eq(pz._hint_label.text, UIKit.t("ui.c4.numbers.hint"), "hint text")
	return true


func _t_keys() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	kit.ok(pz.modal_input(key_event(KEY_3)), "key 3 consumed")
	kit.eq(pz.slots, ["n24318", "", "", ""], "key 3 = third tray plate (24 318) on W 1")
	kit.eq([pz.wagon_at(), pz.wagon_number()], [0, "n24318"], "the wagon rolls to W 1 and shows 24 318")
	pz.modal_input(key_event(KEY_4))
	kit.eq(pz.slots, ["n24318", "c1742", "", ""], "key 4 on the next empty post")
	pz.modal_input(key_event(KEY_3))
	kit.eq(pz.slots, ["n24318", "c1742", "", ""], "a hung plate cannot be hung twice")
	kit.ok(pz.modal_input(key_event(KEY_BACKSPACE)), "Backspace consumed (it is also bound to cancel)")
	kit.eq(pz.slots, ["n24318", "", "", ""], "Backspace takes back the plate hung last")
	kit.eq(pz.wagon_at(), 0, "the wagon rolls back to the last plate")
	kit.ok(pz.is_open, "Backspace never closes")
	pz.modal_input(key_event(KEY_KP_2))
	kit.eq(pz.slots, ["n24318", "n47702", "", ""], "keypad 2 = 47 702")
	kit.ok(pz.modal_input(key_event(KEY_9)), "a key beyond the tray is consumed")
	kit.eq(pz.filled_count(), 2, "… and hangs nothing")
	kit.ok(pz.modal_input(key_event(KEY_L)), "L consumed")
	kit.ok(pz.lamp and pz.lamp_list_shown(), "L: lamp on, the layers listed")
	pz.modal_input(key_event(KEY_L))
	kit.ok(not pz.lamp, "L again: lamp off")
	kit.ok(pz.modal_input(key_event(KEY_R)), "R consumed")
	kit.eq(pz.slots, ["", "", "", ""], "R clears every hook")
	kit.eq(pz.wagon_at(), -1, "the wagon back at the yard")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter consumed")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.numbers.incomplete"), "Enter on an incomplete board: note, no attempt")
	kit.ok(not pz.modal_input(key_event(KEY_ESCAPE)), "Esc is left to UIRoot -> handle_cancel")
	kit.ok(not pz.modal_input(key_event(KEY_3, false)), "key releases are ignored")
	kit.eq(g.puzzle_attempts(T_OBJ), 0, "no attempt from keys alone")
	pz.arm(2)
	pz.modal_input(key_event(KEY_1))
	kit.eq(pz.slots, ["", "", "c1745", ""], "a number key hangs on the chosen post")
	pz.arm(3)
	kit.ok(pz.handle_cancel() and pz.is_open and pz.armed == -1, "Esc: first forgets the chosen post")
	kit.ok(pz.handle_cancel() and not pz.is_open, "Esc again closes")
	kit.eq(g.objective_state(T_OBJ), "available", "closing is not an attempt")
	return true


func _t_lamp() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	_fill(pz, ["c1742"])
	var face_tex: Texture2D = pz._post_plates[0].texture
	pz.toggle_lamp()
	kit.ok(pz._post_plates[0].texture != face_tex, "the hung plate shows its lit layer")
	kit.ok(str(pz._post_plates[0].texture.resource_path).ends_with("c4_plate_c1742_lit.png"), "… c4_plate_c1742_lit.png")
	kit.ok(pz._post_glows[0].visible and not pz._post_glows[1].visible, "glow behind hung plates only")
	kit.ok(str((pz._tray_plates["c1745"] as TextureRect).texture.resource_path).ends_with("_lit.png"), "tray plates lit too")
	kit.ok(str(pz._lamp_icon.texture.resource_path).ends_with("c4_lamp_on.png"), "the hand lamp on the board burns")
	var rows: PackedStringArray = pz.lamp_list_text()
	kit.eq(rows[0], UIKit.t("ui.c4.numbers.lamp_row", {"face": "C-17/45", "under": "„47 702“"}), "list: under C-17/45 lies 47 702")
	kit.eq(rows[2], UIKit.t("ui.c4.numbers.lamp_row", {"face": "24 318", "under": UIKit.t("ui.c4.numbers.bare")}), "list: under 24 318 bare metal")
	kit.eq(g.puzzle_attempts(T_OBJ), 0, "the lamp is no attempt")
	kit.eq(pz.slots, ["c1742", "", "", ""], "the lamp changes no plate")
	pz.close()
	pz.open(T_OBJ)
	kit.ok(pz.lamp, "the lamp may stay on (accessibility) across openings")
	return true


func _t_mouse() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	pz._tray_buttons["n47702"].pressed.emit()
	kit.eq(pz.held, "n47702", "click on a plate takes it up")
	kit.ok((pz._tray_marks["n47702"] as Control).visible, "… outlined in the tray")
	kit.ok(pz._post_marks[0].visible and pz._post_marks[3].visible, "empty posts are outlined as targets")
	kit.eq(pz._state_label.text, UIKit.t("ui.c4.numbers.state_held", {"face": "47 702"}), "state names the plate in hand")
	pz._post_buttons[2].pressed.emit()
	kit.eq(pz.slots, ["", "", "n47702", ""], "click on a post hangs it there")
	kit.eq(pz.held, "", "hand empty")
	pz._tray_buttons["c1745"].pressed.emit()
	pz._tray_buttons["c1745"].pressed.emit()
	kit.eq(pz.held, "", "a second click puts the plate down")
	pz._post_buttons[1].pressed.emit()
	kit.eq(pz.armed, 1, "click on an empty post with an empty hand chooses it")
	pz._tray_buttons["c1745"].pressed.emit()
	kit.eq(pz.slots, ["", "c1745", "n47702", ""], "a plate click goes to the chosen post")
	pz._post_buttons[1].pressed.emit()
	kit.eq(pz.slots, ["", "", "n47702", ""], "click on a hung plate returns it")
	pz._on_post_gui_input(mouse_button(MOUSE_BUTTON_RIGHT, Vector2(5, 5)), 2)
	kit.eq(pz.slots, ["", "", "", ""], "right-click on a hung plate returns it")
	# drag and drop through the forwarded handlers
	var d = pz._drag_from_tray(Vector2(10, 10), "n24318", pz._tray_buttons["n24318"])
	kit.eq(d, {"aoe_c4_plate": "n24318", "from": -1}, "drag data of a tray plate")
	kit.ok(pz._can_drop_post(Vector2.ZERO, d, 0), "a tray plate can be dropped on a post")
	kit.ok(pz._post_marks[0].visible, "the post under the plate is outlined")
	pz._drop_on_post(Vector2.ZERO, d, 0)
	kit.eq(pz.slots, ["n24318", "", "", ""], "dropped on W 1")
	pz._tray_buttons["c1742"].pressed.emit()
	kit.eq(pz.held, "", "a click that ends a drag takes nothing up")
	pz.notification(Node.NOTIFICATION_DRAG_END)
	pz._drag_end_ms -= 1000
	pz._drop_on_post(Vector2.ZERO, {"aoe_c4_plate": "c1742", "from": -1}, 0)
	kit.eq(pz.slots, ["c1742", "", "", ""], "drop on an occupied post: the occupant goes back")
	kit.ok(not ("n24318" in pz.history), "the sent-back plate left the history")
	pz.place("n24318")
	pz._drop_on_post(Vector2.ZERO, {"aoe_c4_plate": "c1742", "from": 0}, 1)
	kit.eq(pz.slots, ["n24318", "c1742", "", ""], "post to post: the two swap")
	kit.ok(pz._can_drop_tray(Vector2.ZERO, {"aoe_c4_plate": "c1742", "from": 1}), "a hung plate can go back onto the tray")
	pz._drop_on_tray(Vector2.ZERO, {"aoe_c4_plate": "c1742", "from": 1})
	kit.eq(pz.slots, ["n24318", "", "", ""], "drop on the tray takes it back")
	kit.ok(not pz._can_drop_post(Vector2.ZERO, {"foo": 1}, 1), "foreign drag data is refused")
	kit.eq(pz._drag_from_tray(Vector2.ZERO, "n24318", pz._tray_buttons["n24318"]), null, "a hung plate cannot be dragged from the tray")
	pz.notification(Node.NOTIFICATION_DRAG_END)
	# hover = the layer under the paint in the side panel
	pz._show_info("plate", "c1745")
	kit.ok(pz.info_text().contains(UIKit.t("ui.c4.numbers.under.c1745")), "hovering a plate shows its under-layer")
	pz._clear_info("plate", "c1745")
	kit.eq(pz.info_text(), "", "leaving clears it")
	pz._show_info("post", 0)
	kit.ok(pz.info_text().contains(UIKit.t("ui.c4.numbers.log.1")) and pz.info_text().contains("24 318"), "a post: log line and its plate")
	for b in [pz._check_btn, pz._lamp_btn, pz._undo_btn, pz._reset_btn, pz._close_btn]:
		kit.ok(b is Button and b.text != "", "button %s" % b.text)
	pz._lamp_btn.button_pressed = true
	kit.ok(pz.lamp, "the „Lampe“ button toggles the lamp")
	pz._undo_btn.pressed.emit()
	kit.eq(pz.slots, ["", "", "", ""], "„Rückgängig“")
	kit.eq(g.puzzle_attempts(T_OBJ), 0, "mouse handling never submits")
	return true


func _t_controller() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	var vp := pz.get_viewport()
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_DPAD_RIGHT)), "D-pad → consumed")
	kit.eq(vp.gui_get_focus_owner(), pz._tray_buttons[T_DISPLAY[0]], "→ without focus: the first tray plate")
	pz.modal_input(pad_event(JOY_BUTTON_DPAD_RIGHT))
	kit.eq(vp.gui_get_focus_owner(), pz._tray_buttons[T_DISPLAY[1]], "→ the next plate")
	pz.modal_input(pad_event(JOY_BUTTON_LEFT_SHOULDER))
	pz.modal_input(pad_event(JOY_BUTTON_LEFT_SHOULDER))
	kit.eq(vp.gui_get_focus_owner(), pz._tray_buttons[T_DISPLAY[3]], "LB = ←, wraps around")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_A)), "A consumed")
	kit.eq(pz.slots, [T_DISPLAY[3], "", "", ""], "A hangs the chosen plate on the next empty post")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_A, false)), "the A release is swallowed too")
	pz.modal_input(pad_event(JOY_BUTTON_RIGHT_SHOULDER))
	kit.eq(vp.gui_get_focus_owner(), pz._tray_buttons[T_DISPLAY[0]], "RB = →, skipping hung plates")
	pz._post_buttons[2].grab_focus()
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.armed, 2, "A on an empty post chooses it")
	pz._tray_buttons["n47702"].grab_focus()
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.slots, [T_DISPLAY[3], "", "n47702", ""], "… and the next plate goes there")
	pz._post_buttons[0].grab_focus()
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.slots, ["", "", "n47702", ""], "A on a hung plate takes it back")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_B)), "B consumed (never closes)")
	kit.eq(pz.slots, ["", "", "", ""], "B takes back the last plate")
	kit.ok(pz.is_open, "still open")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_X)) and pz.lamp, "X: lamp")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_Y)), "Y consumed")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.numbers.incomplete"), "Y checks (incomplete: no attempt)")
	kit.ok(not pz.modal_input(pad_event(JOY_BUTTON_DPAD_UP)), "D-pad ↑ is left to the GUI focus")
	pz._tray_buttons["c1745"].grab_focus()
	pz._tray_buttons["c1745"].disabled = true
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.filled_count(), 0, "A never presses a disabled plate")
	pz._tray_buttons["c1745"].disabled = false
	for sym in T_SOLUTION:
		pz.place(sym)
	pz.modal_input(pad_event(JOY_BUTTON_Y))
	kit.ok(pz.is_done(), "Y on the true chain: solved")
	pz._solved_at -= 1000
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_BACK)) and not pz.is_open, "Back after the guard closes")
	var h := _story_t(true)
	var pz2 := _make(T_SCENE, h)
	pz2.open(T_OBJ)
	kit.ok(pz2.modal_input(pad_event(JOY_BUTTON_BACK)) and not pz2.is_open, "Back/Select closes the open board")
	kit.eq(h.puzzle_attempts(T_OBJ), 0, "closing is no attempt")
	return true


## Exactly what scripts/core/inputplay.gd::_trace_puzzle presses: L, 1 2 3 4 Enter (tray order = wrong), 4x
## Backspace, the solution by its position in `symbols`, Enter.
func _t_inputplay() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	var count := [0]
	pz.solved.connect(func(_id: String) -> void: count[0] += 1)
	pz.open(T_OBJ)
	kit.ok(pz.get("is_open") == true, "is_open after open()")
	var shown: Array = pz.get("symbols") if pz.get("symbols") is Array else []
	kit.eq(shown, T_DISPLAY, "symbols readable by the driver")
	kit.ok(pz.modal_input(key_event(KEY_L)), "L consumed")
	for k in [KEY_1, KEY_2, KEY_3, KEY_4]:
		kit.ok(pz.modal_input(key_event(k)), "number key consumed")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter consumed")
	kit.ne(g.objective_state(T_OBJ), "complete", "the tray order is a wrong chain")
	kit.eq(g.puzzle_attempts(T_OBJ), 1, "one attempt")
	for i in 4:
		pz.modal_input(key_event(KEY_BACKSPACE))
	kit.eq(pz.slots, ["", "", "", ""], "4x Backspace clears the hooks")
	for sym in T_SOLUTION:
		pz.modal_input(key_event(KEY_1 + shown.find(sym)))
	kit.eq(pz.slots, T_SOLUTION, "solution hung by keys")
	pz.modal_input(key_event(KEY_ENTER))
	kit.eq(g.objective_state(T_OBJ), "complete", "objective complete through Story.solve_puzzle")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.success_beat() <= 7.0, "auto-close within 7 s (the driver waits 10 s): %.1f" % pz.success_beat())
	return true


func _t_correct() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	var count := [0]
	pz.solved.connect(func(id: String) -> void:
		count[0] += 1
		kit.eq(id, T_OBJ, "solved(obj_id)"))
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(T_OBJ)
	_fill(pz, T_SOLUTION)
	kit.eq(pz._state_label.text, UIKit.t("ui.c4.numbers.state_full"), "all four posts taken")
	var r: Dictionary = pz.submit()
	kit.eq([r.get("ok"), r.get("solved")], [true, true], "engine: solved")
	kit.eq(g.objective_state(T_OBJ), "complete", "objective complete")
	kit.ok(pz.is_done() and pz.success_shown(), "success shown")
	kit.eq(pz.ticks_shown(), 4, "a chalk tick at every post (reduced motion: at once)")
	kit.eq([pz.wagon_at(), pz.wagon_number()], [4, "c1745"], "the wagon stands in the siding as C-17/45")
	kit.ok(not pz.halt_shown(), "no stop mark")
	kit.eq(pz._success_label.text, UIKit.t("ui.c4.numbers.success"), "success text")
	kit.eq(pz._close_btn.text, UIKit.t("ui.c4.numbers.btn.continue"), "„Weiter“")
	kit.eq(count[0], 1, "solved once")
	kit.eq(pz.submit(), {}, "a second submit does nothing")
	kit.ok(not pz.place_key(1) and not pz.undo() and not pz.reset_order(), "the solved board is locked")
	kit.eq(count[0], 1, "still once")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)) and pz.is_open, "Enter inside the guard is swallowed")
	pz._on_beat(pz._beat_token)
	kit.ok(not pz.is_open and closed[0] == 1, "closes by itself after the beat")
	kit.ok(pz.success_beat() >= 3.0 and pz.success_beat() <= 7.0, "beat 3 … 7 s")
	return true


func _t_text_scale() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g, 2)
	pz.open(T_OBJ)
	_fill(pz, T_DISPLAY)
	pz.submit()
	pz.toggle_lamp()
	pz._show_info("plate", "c1745")
	var s = UIKit.overrides["Settings"]
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()
		kit.eq(pz._feedback.get_theme_font_size("font_size"), int(round(24 * scale)), "wrong note follows %d %%" % int(scale * 100))
		kit.eq(pz._info.get_theme_font_size("font_size"), int(round(24 * scale)), "side panel follows %d %%" % int(scale * 100))
		kit.eq(pz._lamp_rows[0].get_theme_font_size("font_size"), int(round(22 * scale)), "lamp list follows")
		force_layout(pz)
		var need: Vector2 = pz._panel.get_combined_minimum_size()
		kit.ok(need.y <= 1080 - 20 and need.x <= 1920 - 56, "%d %%: fits 1920x1080 with note + hint + lamp + info (needs %s)" % [int(scale * 100), need])
	pz.reset_order()
	_fill(pz, T_SOLUTION)
	pz.submit()
	force_layout(pz)
	var need2: Vector2 = pz._panel.get_combined_minimum_size()
	kit.ok(pz.success_shown() and need2.y <= 1080 - 20, "150 %%: the success text fits (needs %s)" % need2)
	return true


## WCAG 2.x: every text the board draws itself >= 4.5:1 (>= 7:1 with high contrast).  Plates differ by number
## and type (enamel / stencil / brush), never by colour alone; digits are 1 art px = 3 screen px strokes.
func _t_contrast() -> bool:
	var g := _story_t(true)
	var pz := _make(T_SCENE, g)
	pz.open(T_OBJ)
	var pairs: Array = pz.contrast_pairs()
	kit.ok(pairs.size() >= 5, "contrast pairs reported")
	for p in pairs:
		kit.ok(contrast(p["fg"], p["bg"]) >= 4.5, "%s: %.2f : 1 >= 4.5" % [p["what"], contrast(p["fg"], p["bg"])])
	UIKit.overrides["Settings"].set_value("high_contrast", true)
	for p in pz.contrast_pairs():
		kit.ok(contrast(p["fg"], p["bg"]) >= 7.0, "high contrast — %s: %.2f : 1 >= 7" % [p["what"], contrast(p["fg"], p["bg"])])
	# the slate behind the chalk words, re-measured from the PNG
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c4_numbers_board.png"))
	var lum := 0.0
	var n := 0
	for y in range(50, 80, 3):
		for x in range(200, 260, 3):
			lum = maxf(lum, luminance(img.get_pixel(x, y)))
			n += 1
	kit.ok(n > 0 and (0.64 + 0.05) / (lum + 0.05) >= 4.5, "chalk vs the lightest slate pixel between the posts")
	# every face number is set in light paint on a dark plate (or dark under the lamp): >= 3:1 per plate
	for sym in T_SOLUTION:
		var pi := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c4_plate_%s.png" % sym))
		var lo := 1.0
		var hi := 0.0
		for y in range(5, 20):
			for x in range(14, 74):
				var c := pi.get_pixel(x, y)
				if c.a > 0.5:
					lo = minf(lo, luminance(c))
					hi = maxf(hi, luminance(c))
		kit.ok((hi + 0.05) / (lo + 0.05) >= 3.0, "%s: digits vs plate %.2f : 1" % [sym, (hi + 0.05) / (lo + 0.05)])
	return true


func _t_refused() -> bool:
	var rs := RefusingStory.new()
	kit.track(rs)
	var pz := _make(T_SCENE, rs)
	pz.open(T_OBJ)
	kit.eq(pz.symbols, T_DISPLAY, "without Story.puzzle_for: the data file's display order")
	_fill(pz, T_SOLUTION)
	var r: Dictionary = pz.submit()
	kit.eq(r.get("ok"), false, "engine refusal passed through")
	kit.ok(pz.feedback_text().contains(UIKit.t("sys.err.missing_clues")) or pz.feedback_text() != "", "refusal named")
	kit.ok(not pz.is_done() and pz.is_open, "board stays open, nothing solved")
	kit.eq(pz.slots, T_SOLUTION, "plates stay")
	UIKit.overrides = {"Settings": UIKit.overrides["Settings"], "Audio": UIKit.overrides["Audio"], "Story": null}
	var pz2: Control = load(T_SCENE).instantiate()
	kit.track(pz2)
	(Engine.get_main_loop() as SceneTree).root.add_child(pz2)
	pz2.open(T_OBJ)
	_fill(pz2, T_SOLUTION)
	var r2: Dictionary = pz2.submit()
	kit.eq(r2.get("ok"), false, "no Story service: no crash, nothing solved")
	return true


func _t_art() -> bool:
	var b = JSON.parse_string(FileAccess.get_file_as_string(T_BOARD))
	kit.ok(b is Dictionary, "board json parses")
	if not (b is Dictionary):
		return true
	kit.eq([b.get("puzzle_id"), b.get("objective"), int(b.get("display_scale", 0))], ["pz_c4_numbers", T_OBJ, 3], "board json header")
	kit.eq(b.get("generator"), "tools/pixelgen/gen_ui_c4.py", "generator named")
	var plates: Dictionary = b["plates"]
	kit.eq(TKit.sorted(plates.keys()), TKit.sorted(T_SOLUTION), "four plates")
	# the chain the lamp shows: every plate lies over the one before it, the first on bare metal
	kit.eq(str(plates[T_SOLUTION[0]]["under"]), "", "24 318 lies on bare metal")
	for i in range(1, 4):
		kit.eq(str(plates[T_SOLUTION[i]]["under"]), T_SOLUTION[i - 1], "%s lies over %s" % [T_SOLUTION[i], T_SOLUTION[i - 1]])
	kit.eq(T_SOLUTION, TKit.C4_NUMBERS, "kit solution = the art's chain")
	var faces := {}
	for sym in plates:
		var p: Dictionary = plates[sym]
		kit.eq(UIKit.t("ui.c4.numbers.face." + sym), str(p["face"]), "%s: face key = art number" % sym)
		kit.ok(UIKit.t("ui.c4.numbers.card." + sym).contains(str(p["face"])), "%s: the card text names the number" % sym)
		faces[str(p["face"])] = true
		for k in ["file", "lit_file", "num_file"]:
			var path := "res://assets/ui/puzzle/" + str(p[k])
			var tx: Texture2D = load(path) if ResourceLoader.exists(path) else null
			kit.ok(tx != null, "%s exists" % path)
			if tx != null and k != "num_file":
				kit.eq(tx.get_size(), Vector2(88, 25), "%s 88x25" % path)
	kit.eq(faces.size(), 4, "four different numbers")
	for f in ["board", "wagon", "wire", "tick", "halt", "glow"]:
		var path := "res://assets/ui/puzzle/" + str(b[f]["file"])
		var tx: Texture2D = load(path) if ResourceLoader.exists(path) else null
		kit.ok(tx != null and tx.get_size() == Vector2(float(b[f]["size"][0]), float(b[f]["size"][1])), "%s at its listed size" % path)
	for f in ["on", "off"]:
		kit.ok(ResourceLoader.exists("res://assets/ui/puzzle/" + str(b["lamp"][f])), "lamp %s" % f)
	kit.eq((b["board"]["posts_x"] as Array).size(), 4, "four posts")
	kit.ok(str(b.get("world_note", "")).contains("Fictional"), "world note")
	return true


# ================================================================== RoutePuzzle
func _r_registered() -> bool:
	_registered_common(R_OBJ, R_SCENE, R_SCRIPT, "route_puzzle.gd")
	return true


func _r_route() -> bool:
	var g := _story_r(true)
	var p: Dictionary = g.puzzle_for(R_OBJ)
	kit.ok(not p.has("solution"), "the UI never sees the solution")
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	kit.ok(pz.is_open and pz.visible, "open() shows the modal")
	kit.eq(pz.pose(), R_START, "start pose {0, 0, 0} (C4_DESIGN §2.7)")
	kit.eq(pz.aligned(), 0, "no detour on a shaft at the start")
	var b = pz._board
	kit.eq([b.rings.size(), b.pairs.size()], [3, 3], "three shafts, three detours")
	kit.ok(b.tex_plan != null and b.tex_trace != null, "plan and tracing paper loaded")
	kit.eq(b.size, Vector2(864, 672), "light table 18x14 cells at 16 px x3")
	kit.eq([b.rings[0]["label"], b.pairs[0]["label"]], [UIKit.t("ui.c4.routes.shaft.1"), UIKit.t("ui.c4.routes.match.1")], "HD words from Loc")
	kit.eq(b.title_lines.size(), 3, "title block: three lines")
	kit.eq(b.title_lines[2]["text"], UIKit.t("ui.c4.routes.plan.sign"), "… signed gez. K. A.")
	kit.eq(pz._state_label.text, UIKit.t("ui.c4.routes.state", {"rot": 0, "x": "+0", "y": "+0"}), "pose line")
	kit.eq(pz._aligned_label.text, UIKit.t("ui.c4.routes.aligned", {"n": 0, "total": 3}), "0 of 3")
	kit.ok(pz.tip_text() != "", "the mouse way is said once")
	return true


func _r_keys() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	kit.ok(pz.modal_input(key_event(KEY_RIGHT)), "→ consumed")
	kit.eq(pz.pose(), {"rotation_steps": 0, "offset_x": 1, "offset_y": 0}, "RIGHT = offset_x + 1")
	pz.modal_input(key_event(KEY_UP))
	kit.eq(pz.pose()["offset_y"], -1, "UP = offset_y − 1")
	pz.modal_input(key_event(KEY_A))
	pz.modal_input(key_event(KEY_S))
	kit.eq(pz.pose(), R_START, "WASD move too")
	pz.modal_input(key_event(KEY_R))
	kit.eq(pz.pose()["rotation_steps"], 1, "R = +90°")
	pz.modal_input(key_event(KEY_R, true, true))
	kit.eq(pz.pose()["rotation_steps"], 0, "Shift+R = −90°")
	pz.modal_input(key_event(KEY_R, true, true))
	kit.eq(pz.pose()["rotation_steps"], 3, "… mod 4")
	kit.ok(pz.modal_input(key_event(KEY_BACKSPACE)), "Backspace consumed (also bound to cancel)")
	kit.eq(pz.pose(), R_START, "Backspace takes back the last move")
	kit.ok(pz.is_open, "Backspace never closes")
	var held := key_event(KEY_RIGHT)
	held.echo = true
	pz.modal_input(held)
	kit.eq(pz.pose()["offset_x"], 1, "a held arrow repeats")
	pz.undo()
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter consumed")
	kit.eq(g.puzzle_attempts(R_OBJ), 1, "Enter on the start pose = one attempt")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.routes.wrong_turned"), "start pose: the paper is turned wrong")
	kit.ok(not pz.modal_input(key_event(KEY_ESCAPE)), "Esc is left to UIRoot -> handle_cancel")
	kit.ok(pz.handle_cancel() and not pz.is_open, "Esc closes")
	kit.eq(g.objective_state(R_OBJ), "available", "closing is not an attempt")
	return true


func _r_wrong() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	pz.rotate(1)
	var r: Dictionary = pz.submit()
	kit.eq([r.get("solved"), g.puzzle_attempts(R_OBJ)], [false, 1], "turned right, not moved: attempt 1")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.routes.wrong"), "orientation fits: „neben den Schächten“")
	kit.eq(pz.pose()["rotation_steps"], 1, "the paper stays where it is")
	pz.move(Vector2i.RIGHT)
	kit.eq(pz.feedback_text(), "", "moving clears the note")
	pz.rotate(1)
	pz.submit()
	kit.eq(pz.feedback_text(), UIKit.t("ui.c4.routes.wrong_turned"), "turned twice: Marta's direction note")
	kit.eq(g.objective_state(R_OBJ), "available", "Story unchanged apart from the attempts")
	kit.ok(not pz.is_done(), "not solved")
	return true


func _r_hints() -> bool:
	for mode in [0, 1, 2]:
		var g := _story_r(true)
		var pz := _make(R_SCENE, g, mode)
		pz.open(R_OBJ)
		kit.eq(pz.hint_shown(), mode == 2, "mode %d: at once only for 2" % mode)
		pz.submit()
		kit.eq(pz.hint_shown(), mode == 2, "mode %d after one failure" % mode)
		pz.submit()
		kit.eq(pz.hint_shown(), mode >= 1, "mode %d after two failures" % mode)
		kit.eq(pz._hint_label.text, UIKit.t("ui.c4.routes.hint"), "hint text")
	return true


func _r_controller() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_DPAD_RIGHT)), "D-pad consumed")
	pz.modal_input(pad_event(JOY_BUTTON_DPAD_UP))
	kit.eq(pz.pose(), {"rotation_steps": 0, "offset_x": 1, "offset_y": -1}, "D-pad moves")
	pz.modal_input(pad_event(JOY_BUTTON_RIGHT_SHOULDER))
	kit.eq(pz.pose()["rotation_steps"], 1, "RB turns +90°")
	pz.modal_input(pad_event(JOY_BUTTON_LEFT_SHOULDER))
	kit.eq(pz.pose()["rotation_steps"], 0, "LB turns back")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_Y)), "Y consumed")
	kit.eq(pz.pose()["rotation_steps"], 1, "Y takes back the last move")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_X)), "X consumed")
	kit.eq(pz.pose(), R_START, "X: back to the start pose")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_X, false)), "releases swallowed")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_A)), "A consumed")
	kit.eq(g.puzzle_attempts(R_OBJ), 1, "A checks")
	kit.ok(not pz.modal_input(pad_event(JOY_BUTTON_B)), "B is left to UIRoot (cancel -> handle_cancel)")
	for k in [JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_RIGHT,
			JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_UP, JOY_BUTTON_A]:
		pz.modal_input(pad_event(k))
	kit.eq(g.objective_state(R_OBJ), "complete", "solved by pad alone")
	pz._solved_at -= 1000
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_B)) and not pz.is_open, "B after the guard closes")
	var h := _story_r(true)
	var pz2 := _make(R_SCENE, h)
	pz2.open(R_OBJ)
	kit.ok(pz2.modal_input(pad_event(JOY_BUTTON_BACK)) and not pz2.is_open, "Back closes")
	return true


func _r_mouse() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	var b = pz._board
	var cp: float = b.cp()
	var c: Vector2 = b.trace_center()
	kit.ok(b.hit_trace(c) and not b.hit_trace(Vector2(4, 4)), "the paper is hit, the frame is not")
	b._gui_input(mouse_button(MOUSE_BUTTON_LEFT, c))
	kit.ok(b._dragging, "press on the paper starts a drag")
	var mm := InputEventMouseMotion.new()
	mm.position = c + Vector2(cp * 2.4, -cp * 0.6)
	b._gui_input(mm)
	kit.eq(pz.pose(), {"rotation_steps": 0, "offset_x": 2, "offset_y": -1}, "drag snaps to whole cells")
	b._gui_input(mouse_button(MOUSE_BUTTON_LEFT, mm.position, false))
	kit.ok(not b._dragging, "release ends the drag")
	kit.eq(pz.history.size(), 1, "one drag = one step back")
	pz.undo()
	kit.eq(pz.pose(), R_START, "Backspace after a drag: back where it started")
	b._gui_input(mouse_button(MOUSE_BUTTON_WHEEL_DOWN, c))
	kit.eq(pz.pose()["rotation_steps"], 1, "wheel down turns clockwise")
	b._gui_input(mouse_button(MOUSE_BUTTON_WHEEL_UP, c))
	kit.eq(pz.pose()["rotation_steps"], 0, "wheel up turns back")
	b._gui_input(mouse_button(MOUSE_BUTTON_RIGHT, c))
	kit.eq(pz.pose()["rotation_steps"], 1, "right-click turns")
	pz._reset_btn.pressed.emit()
	kit.eq(pz.pose(), R_START, "„Zurücksetzen“")
	pz._rotate_btn.pressed.emit()
	kit.eq(pz.pose()["rotation_steps"], 1, "„Drehen“")
	kit.eq(g.puzzle_attempts(R_OBJ), 0, "no attempt from mouse handling")
	b.begin_drag(b.trace_center())
	b.drag_to(b.trace_center() + Vector2(cp * 3, -cp * 2))
	b.end_drag()
	kit.eq(pz.pose(), R_SOLUTION, "dragged onto the shafts")
	kit.eq(pz.aligned(), 3, "three of three")
	pz._check_btn.pressed.emit()
	kit.eq(g.objective_state(R_OBJ), "complete", "„Abgleichen“ solves — mouse only")
	b._gui_input(mouse_button(MOUSE_BUTTON_LEFT, b.trace_center()))
	kit.ok(not b._dragging, "the solved paper does not move")
	pz._close_btn.pressed.emit()
	kit.ok(not pz.is_open, "„Weiter“ closes")
	return true


## Exactly what scripts/core/inputplay.gd::_route_puzzle presses: Enter on the start pose (wrong), then R,
## →×3, ↑×2 and Enter.
func _r_inputplay() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	var count := [0]
	pz.solved.connect(func(_id: String) -> void: count[0] += 1)
	pz.open(R_OBJ)
	kit.ok(pz.get("is_open") == true, "is_open after open()")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter consumed")
	kit.ne(g.objective_state(R_OBJ), "complete", "the start pose is wrong")
	kit.eq(g.puzzle_attempts(R_OBJ), 1, "one attempt")
	for k in [KEY_R, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_UP, KEY_UP]:
		kit.ok(pz.modal_input(key_event(k)), "key consumed")
	kit.eq(pz.pose(), R_SOLUTION, "R, →×3, ↑×2 = the solution pose")
	pz.modal_input(key_event(KEY_ENTER))
	kit.eq(g.objective_state(R_OBJ), "complete", "objective complete through Story.solve_puzzle")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.success_beat() <= 7.0, "auto-close within 7 s (the driver waits 8 s): %.1f" % pz.success_beat())
	return true


func _r_geometry() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	var b = pz._board
	var fits: Array = []
	for r in 4:
		fits.append(b.rotation_fits(r))
	kit.eq(fits, [false, true, false, false], "only one quarter turn lets every detour meet a shaft")
	var full: Array = []
	for r in 4:
		for x in range(b.off_min.x, b.off_max.x + 1):
			for y in range(b.off_min.y, b.off_max.y + 1):
				b.set_state(r, Vector2i(x, y))
				if b.aligned_count() == 3:
					full.append({"rotation_steps": r, "offset_x": x, "offset_y": y})
	kit.eq(full, [R_SOLUTION], "exactly one reachable pose aligns all three pairs — the engine's solution")
	b.set_state(1, Vector2i(3, -2))
	for i in 3:
		kit.ok(b.pair_aligned(i), "pair %d: diamond on its ring" % (i + 1))
	b.set_state(0, Vector2i(99, -99))
	kit.ok(b.offset.x == b.off_max.x and b.offset.y == b.off_min.y, "offsets clamp at the table's edge")
	var lay = JSON.parse_string(FileAccess.get_file_as_string(R_LAYOUT))
	var st: Dictionary = lay.get("start", {})
	kit.eq({"rotation_steps": int(st.get("rotation_steps", -1)), "offset_x": int(st.get("offset_x", -1)),
		"offset_y": int(st.get("offset_y", -1))}, R_START, "layout start pose")
	kit.eq(int(lay.get("pose_check", {}).get("start_aligned", -1)), 0, "the generator verified the start")
	kit.ok(not lay.has("solution"), "the layout does not carry the answer")
	return true


func _r_correct() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	var count := [0]
	pz.solved.connect(func(id: String) -> void:
		count[0] += 1
		kit.eq(id, R_OBJ, "solved(obj_id)"))
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(R_OBJ)
	pz.rotate(1)
	pz.move(Vector2i(3, -2))
	kit.eq(pz.pose(), R_SOLUTION, "pose")
	kit.eq(pz._aligned_label.text, UIKit.t("ui.c4.routes.aligned", {"n": 3, "total": 3}), "3 of 3 before checking")
	var r: Dictionary = pz.submit()
	kit.eq([r.get("ok"), r.get("solved")], [true, true], "engine: solved")
	kit.ok(pz.is_done() and pz.success_shown(), "success shown")
	kit.eq(pz.matches_shown(), 3, "the red pencil circles all three pairs (reduced motion: at once)")
	kit.ok(pz.sign_shown(), "… and underlines gez. K. A.")
	kit.eq(pz._success_label.text, UIKit.t("ui.c4.routes.success"), "success text")
	kit.eq(pz._close_btn.text, UIKit.t("ui.c4.routes.btn.continue"), "„Weiter“")
	kit.eq(count[0], 1, "solved once")
	kit.ok(not pz.move(Vector2i.LEFT) and not pz.rotate(1) and pz.pose() == R_SOLUTION, "the solved paper is locked")
	kit.eq(pz.submit(), {}, "a second submit does nothing")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)) and pz.is_open, "Enter inside the guard is swallowed")
	pz._on_beat(pz._beat_token)
	kit.ok(not pz.is_open and closed[0] == 1, "closes by itself after the beat")
	return true


func _r_text_scale() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g, 2)
	pz.open(R_OBJ)
	pz.submit()
	var s = UIKit.overrides["Settings"]
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()
		kit.eq(pz._feedback.get_theme_font_size("font_size"), int(round(24 * scale)), "note follows %d %%" % int(scale * 100))
		kit.eq(pz._instr.get_theme_font_size("font_size"), int(round(26 * scale)), "instruction follows")
		force_layout(pz)
		var need: Vector2 = pz._panel.get_combined_minimum_size()
		kit.ok(need.y <= 1080 - 20 and need.x <= 1920 - 56, "%d %%: fits 1920x1080 with note + hint (needs %s)" % [int(scale * 100), need])
	pz.rotate(1)
	pz.move(Vector2i(3, -2))
	pz.submit()
	force_layout(pz)
	var need2: Vector2 = pz._panel.get_combined_minimum_size()
	kit.ok(pz.success_shown() and need2.y <= 1080 - 20, "150 %%: the success text fits (needs %s)" % need2)
	return true


func _r_contrast() -> bool:
	var g := _story_r(true)
	var pz := _make(R_SCENE, g)
	pz.open(R_OBJ)
	for p in pz.contrast_pairs():
		kit.ok(contrast(p["fg"], p["bg"]) >= 4.5, "%s: %.2f : 1 >= 4.5" % [p["what"], contrast(p["fg"], p["bg"])])
	UIKit.overrides["Settings"].set_value("high_contrast", true)
	for p in pz.contrast_pairs():
		kit.ok(contrast(p["fg"], p["bg"]) >= 7.0, "high contrast — %s: %.2f : 1 >= 7" % [p["what"], contrast(p["fg"], p["bg"])])
	# shape, not colour: ring (shaft) and diamond (detour) silhouettes differ
	var plan := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/documents/berlin_c4_routes_plan.png"))
	var trace := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/documents/berlin_c4_routes_trace.png"))
	var ring := ""
	var dia := ""
	for y in range(-6, 7):
		for x in range(-6, 7):
			ring += "1" if luminance(plan.get_pixel(152 + x, 24 + y)) < 0.05 else "0"
			var tc := trace.get_pixel(24 + x, 24 + y)
			dia += "1" if tc.a > 0.7 and luminance(tc) < 0.08 else "0"
	kit.ok(ring.count("1") > 20 and dia.count("1") > 12, "both marks drawn dark")
	kit.ne(ring, dia, "ring and diamond are different shapes")
	kit.ok(ring.substr(6 * 13 + 6, 1) == "1" and dia.substr(6 * 13 + 6, 1) == "0", "ring has a centre dot, the diamond is hollow")
	return true


func _r_refused() -> bool:
	var rs := RefusingStory.new()
	kit.track(rs)
	var pz := _make(R_SCENE, rs)
	pz.open(R_OBJ)
	var r: Dictionary = pz.submit()
	kit.eq(r.get("ok"), false, "engine refusal passed through")
	kit.ok(pz.feedback_text() != "" and not pz.is_done() and pz.is_open, "refusal named, nothing solved")
	var g := _story_r(false)
	var pz2 := _make(R_SCENE, g)
	pz2.open(R_OBJ)
	var r2: Dictionary = pz2.submit()
	kit.eq(r2.get("error_key"), "sys.err.locked", "locked before Marta gave her route")
	kit.eq(g.puzzle_attempts(R_OBJ), 0, "no attempt counted")
	kit.ok(pz2.feedback_text().contains(UIKit.t("sys.err.locked")) or pz2.feedback_text() != "", "the lock is named")
	return true


func _loc_keys() -> bool:
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var keys := []
	for k in ["title", "subtitle", "instruction", "lamp_on", "lamp_off", "wrong", "wrong_first", "wrong_bare",
			"wrong_generic", "incomplete", "hint", "success", "btn.check", "btn.undo", "btn.reset", "btn.lamp",
			"btn.close", "btn.continue", "yard", "siding", "tunnel", "tray", "state", "state_full", "state_armed",
			"state_held", "state_done", "tip_mouse", "tip_pad", "lamp_row", "bare", "error", "stamp", "hint_place",
			"hint_undo", "hint_reset", "hint_lamp", "hint_check", "controls", "post_tip", "post_tip_filled",
			"plate_tip", "info_post", "info_hung"]:
		keys.append("ui.c4.numbers." + k)
	for i in 4:
		for k in ["post.%d", "log.%d", "post_id.%d"]:
			keys.append("ui.c4.numbers." + k % (i + 1))
	for sym in T_SOLUTION:
		for k in ["face.", "kind.", "card.", "under."]:
			keys.append("ui.c4.numbers." + k + sym)
	for k in ["title", "subtitle", "instruction", "legend.shaft", "legend.loop", "wrong", "wrong_turned", "hint",
			"success", "btn.check", "btn.rotate", "btn.reset", "btn.close", "btn.continue", "state", "aligned",
			"tip_mouse", "tip_pad", "plan.title", "plan.sub", "plan.sign", "stamp", "error", "hint_move",
			"hint_rotate", "hint_drag", "hint_undo", "hint_check", "controls", "board_tip"]:
		keys.append("ui.c4.routes." + k)
	for i in 3:
		keys.append("ui.c4.routes.shaft.%d" % (i + 1))
		keys.append("ui.c4.routes.match.%d" % (i + 1))
	for k in keys:
		kit.ok(loc.has(k) and loc.t(k).strip_edges() != "", "Loc key %s" % k)
	for k in keys:
		var t: String = loc.t(k)
		kit.ok(not t.contains("\""), "%s: German quotes only" % k)
	return true
