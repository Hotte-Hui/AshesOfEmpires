extends RefCounted
## Chapter-3 part-2 joint evidence check UI (scenes/ui/CheckPuzzle.tscn, scripts/ui/check_puzzle.gd,
## documentation/C3P2_DESIGN.md §2.7): registered for c3d_solve_check and instanced by ChapterExt like the
## protocol puzzle; driven here stand-alone (headless) against a REAL Story engine instance (public API only)
## plus mock Settings/Audio injected through ui_kit overrides. Covers: open on the real route, incomplete
## submit = no attempt, wrong order = one attempt with the cards kept, hint after two failures (puzzle_hints
## 0/1/2), keys 1-4 by the ORIGINAL tray order, Backspace/R, mouse rows + drag and drop, the exact key
## sequence of scripts/core/inputplay.gd, correct order = objective complete + matching marks + Kordon brace +
## `solved` once, 125 % / 150 % (the board fits 1920x1080, the Lupe shows the focused card scaled), WCAG
## contrast of every text the board draws itself (also in high contrast), shape-not-colour glyphs, engine
## errors, Esc, Loc keys and the board art metadata.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const SCENE := "res://scenes/ui/CheckPuzzle.tscn"
const SCRIPT := "res://scripts/ui/check_puzzle.gd"
const BOARD := "res://assets/ui/puzzle/c3p2_board.json"
const OBJ := "c3d_solve_check"
const SOLUTION := ["in_c17_44", "out_2340", "par_4", "january"]
const DISPLAY := ["out_2340", "january", "in_c17_44", "par_4"]
const ROW_ITEMS := ["ev_c3_weighbill", "ev_c3_departures", "ev_c3_travel_order", "ev_timetable"]


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
	kit.run_case("scene_registered_and_instanced_by_chapter_ext", _registered)
	kit.run_case("real_story_route_opens_the_check", _route)
	kit.run_case("incomplete_submit_counts_no_attempt", _incomplete)
	kit.run_case("wrong_order_counts_one_attempt_and_keeps_cards", _wrong)
	kit.run_case("hint_follows_settings_and_attempts", _hints)
	kit.run_case("keys_use_the_original_tray_order", _keys)
	kit.run_case("mouse_rows_and_drag_and_drop", _mouse)
	kit.run_case("controller_a_x_y_b", _controller)
	kit.run_case("inputplay_key_sequence_solves", _inputplay_sequence)
	kit.run_case("correct_order_marks_both_halves_once", _correct)
	kit.run_case("text_scale_125_150_fits_and_lupe", _text_scale)
	kit.run_case("contrast_and_shape_not_colour", _contrast)
	kit.run_case("escape_forgets_the_row_then_closes", _escape)
	kit.run_case("locked_without_clues_shows_engine_error", _locked)
	kit.run_case("refused_or_missing_story_never_breaks", _refused)
	kit.run_case("loc_keys_exist", _loc_keys)
	kit.run_case("board_art_and_metadata", _board_art)
	UIKit.overrides = _saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Plays the canonical route through the public Story API up to c3d_solve_check. with_clues = false stops
## after registry A (intake book, drawer and the comparison NOT done -> the check stays locked).
## Also used by the visual preview of the board.
static func play_to_check(k: TKit, g: Node, with_clues := true) -> bool:
	k.play_until(g, "c3c")
	if with_clues:
		g.inspect("c3d_inspect_intake")
		g.inspect("c3d_inspect_drawer")
		k.play_dialogue(g, "c3d_talk_compare")
	return g.is_available(OBJ) == with_clues and g.objective_state("c3c_talk_konrad") == "complete"


func _story(with_clues := true) -> Node:
	var g := kit.story()
	kit.ok(play_to_check(kit, g, with_clues), "route to the check (clues: %s)" % with_clues)
	return g


func _make(story, hints := 1) -> Control:
	var settings := MockSettings.new()
	settings.values["puzzle_hints"] = hints
	kit.track(settings)
	var audio := MockAudio.new()
	kit.track(audio)
	UIKit.overrides = {"Story": story, "Settings": settings, "Audio": audio}
	var pz: Control = load(SCENE).instantiate()
	kit.track(pz)
	(Engine.get_main_loop() as SceneTree).root.add_child(pz)
	return pz


static func key_event(code: int, pressed := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = code as Key
	ev.physical_keycode = code as Key
	ev.pressed = pressed
	return ev


func _fill(pz: Control, ids: Array) -> void:
	for id in ids:
		pz.place(str(id))


## Lays the whole board out synchronously at 1920x1080 (tests run inside one frame): the panel gets its
## anchored rect, then every container sorts top-down; repeated so wrapped labels settle on their width.
static func force_layout(pz: Control) -> void:
	if pz.theme == null:
		pz.theme = UIKit.theme(UIKit.high_contrast())   # what UIRoot applies to every modal
	pz.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	pz.size = Vector2(1920, 1080)
	var panel: Control = pz.get("_panel")
	panel.set_anchors_preset(Control.PRESET_TOP_LEFT)    # explicit rect below (no anchor override warning)
	for _pass in 4:
		panel.position = Vector2(28, 10)
		panel.size = Vector2(1920 - 56, 1080 - 20)
		_sort(panel)


static func _sort(n: Node) -> void:
	if n is Container:
		n.notification(Container.NOTIFICATION_SORT_CHILDREN)
	for c in n.get_children():
		if c is Label or c is RichTextLabel:      # re-break wrapped lines at the width just assigned
			c.notification(Control.NOTIFICATION_THEME_CHANGED)
		_sort(c)


static func luminance(c: Color) -> float:
	var f := func(v: float) -> float: return v / 12.92 if v <= 0.04045 else pow((v + 0.055) / 1.055, 2.4)
	return 0.2126 * f.call(c.r) + 0.7152 * f.call(c.g) + 0.0722 * f.call(c.b)


static func contrast(a: Color, b: Color) -> float:
	var la := luminance(a)
	var lb := luminance(b)
	return (maxf(la, lb) + 0.05) / (minf(la, lb) + 0.05)


# ------------------------------------------------------------------ cases
func _registered() -> bool:
	var c3 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c3.json"))
	kit.eq(str(c3.get("puzzles", {}).get(OBJ, "")), SCENE, "data/chapters/c3.json registers the scene")
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
	var node: Node = ext.puzzle_ui(game, OBJ)
	kit.ok(node != null and node.get_script() == load(SCRIPT), "ChapterExt.puzzle_ui instances CheckPuzzle")
	if node == null:
		return true
	kit.ok(node.get_parent() == root and node.get_index() < root.toast_layer.get_index(), "added under UIRoot before the toasts")
	kit.ok(node.get("ui_root") == root, "ui_root set")
	kit.ok(ext.puzzle_ui(game, OBJ) == node, "instanced once")
	kit.ok(node.has_signal("solved") and node.has_signal("closed"), "signals solved + closed")
	kit.eq(node.get("suppress_toasts"), true, "suppress_toasts")
	kit.eq(node.get("symbols"), DISPLAY, "default tray order = display_symbols of pz_c3_check")
	kit.eq(node.get("is_open"), false, "is_open false until opened")
	kit.eq(node.visible, false, "hidden until opened")
	kit.ok(str(node.get_script().resource_path).ends_with("check_puzzle.gd"), "inputplay finds it by script suffix check_puzzle.gd")
	return true


func _route() -> bool:
	var g := _story(true)
	var p: Dictionary = g.puzzle_for(OBJ)
	kit.eq(p.get("display_symbols"), DISPLAY, "display_symbols of pz_c3_check")
	kit.ok(not p.has("solution"), "the UI never sees the solution")
	var pz := _make(g)
	pz.open(OBJ)
	kit.ok(pz.is_open and pz.visible, "open() shows the modal")
	kit.eq(pz.symbols, DISPLAY, "tray follows display_symbols")
	kit.eq(pz.slots, ["", "", "", ""], "four empty rows")
	var tray: Array = []
	for cell in pz._tray_col.get_children():
		for c in cell.get_children():
			if c is Button:
				tray.append(str(c.name).trim_prefix("Card_"))
	kit.eq(tray, DISPLAY, "tray buttons in display order")
	var rows: Array = []
	for i in 4:
		rows.append(pz._paper_cells[i].get_node("Label").text)
	kit.eq(rows, [UIKit.t("ui.c3p2.check.row.weighbill"), UIKit.t("ui.c3p2.check.row.departures"),
		UIKit.t("ui.c3p2.check.row.travel_order"), UIKit.t("ui.c3p2.check.row.timetable")],
		"the four fixed rows of Alexei's freight chain, in order")
	for i in 4:
		var strip: TextureRect = pz._paper_cells[i].get_node("Strip")
		kit.ok(strip.texture != null and strip.size == strip.texture.get_size() * 3.0, "row %d strip shown at exactly x3" % (i + 1))
	kit.eq(pz.marks_shown(), 0, "no matching marks before the solution")
	kit.ok(not pz.kordon_shown() and pz._tray_col.visible, "tray visible, brace hidden")
	kit.eq(pz._state_label.text, UIKit.t("ui.c3p2.check.state", {"n": 0, "total": 4}), "state 0 of 4")
	return true


func _incomplete() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	_fill(pz, ["in_c17_44", "out_2340"])
	var r: Dictionary = pz.submit()
	kit.eq(r, {}, "nothing submitted")
	kit.eq(g.puzzle_attempts(OBJ), 0, "no attempt counted")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3p2.check.incomplete"), "incomplete note")
	kit.ok(pz._notes_row.visible, "the note is on screen")
	kit.eq(pz.slots, ["in_c17_44", "out_2340", "", ""], "cards stay")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter is consumed")
	kit.eq(g.puzzle_attempts(OBJ), 0, "Enter with free rows: still no attempt")
	kit.ok(pz.is_open and not pz.is_done(), "still open")
	return true


func _wrong() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	_fill(pz, DISPLAY)
	var r: Dictionary = pz.submit()
	kit.ok(r.get("ok", false) and not r.get("solved", true), "engine answers wrong, ok")
	kit.eq(g.puzzle_attempts(OBJ), 1, "one attempt counted by the engine")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3p2.check.wrong"), "neutral wrong note")
	kit.eq(pz.slots, DISPLAY, "cards stay for editing")
	kit.ok(not pz.is_done() and pz.is_open, "check continues")
	kit.ok(not pz.hint_shown(), "no hint after one failure (puzzle_hints = 1)")
	kit.eq(g.objective_state(OBJ), "available", "objective still open")
	kit.eq(pz.marks_shown(), 0, "a wrong order shows no marks")
	kit.ok(pz.take_back(0), "a filled row can be cleared")
	kit.eq(pz.feedback_text(), "", "editing clears the note")
	return true


func _hints() -> bool:
	var g := _story(true)
	var pz := _make(g, 1)
	pz.open(OBJ)
	_fill(pz, DISPLAY)
	pz.submit()
	pz.undo()
	pz.undo()
	_fill(pz, ["par_4", "in_c17_44"])
	pz.submit()
	kit.eq(g.puzzle_attempts(OBJ), 2, "two failed attempts")
	kit.ok(g.puzzle_hint_available(OBJ), "engine offers the hint")
	kit.ok(pz.hint_shown(), "hint visible after two failures (puzzle_hints = 1)")
	kit.eq(pz._hint_label.text, UIKit.t("ui.c3p2.check.hint"), "hint text (C3P2_DESIGN §2.7)")
	kit.ok(pz._notes_row.visible and pz.feedback_text() != "", "wrong note and hint both on screen")
	UIKit.overrides["Settings"].values["puzzle_hints"] = 0
	pz._refresh()
	kit.ok(not pz.hint_shown(), "puzzle_hints = 0: never")
	var g2 := _story(true)
	var pz2 := _make(g2, 2)
	pz2.open(OBJ)
	kit.ok(pz2.hint_shown(), "puzzle_hints = 2: immediately")
	return true


func _keys() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	kit.ok(pz.modal_input(key_event(KEY_3)), "key 3 consumed")
	kit.eq(pz.slots, ["in_c17_44", "", "", ""], "key 3 = third tray card (in_c17_44) into the first row")
	pz.modal_input(key_event(KEY_1))
	kit.eq(pz.slots, ["in_c17_44", "out_2340", "", ""], "key 1 = first tray card even after a placement")
	pz.modal_input(key_event(KEY_3))
	kit.eq(pz.slots, ["in_c17_44", "out_2340", "", ""], "a laid card cannot be laid twice")
	kit.ok(pz.modal_input(key_event(KEY_BACKSPACE)), "Backspace consumed (it is also bound to cancel)")
	kit.eq(pz.slots, ["in_c17_44", "", "", ""], "Backspace takes back the card laid last")
	kit.ok(pz.is_open, "Backspace never closes the check")
	pz.modal_input(key_event(KEY_KP_4))
	kit.eq(pz.slots, ["in_c17_44", "par_4", "", ""], "keypad 4 = par_4")
	pz.take_back(0)
	pz.modal_input(key_event(KEY_2))
	kit.eq(pz.slots, ["january", "par_4", "", ""], "the next empty row from the top is filled first")
	pz.modal_input(key_event(KEY_BACKSPACE))
	kit.eq(pz.slots, ["", "par_4", "", ""], "the last laid card (january) goes back first")
	kit.eq(pz.history, ["par_4"], "placement history")
	kit.ok(pz.modal_input(key_event(KEY_9)), "a key beyond the tray is consumed")
	kit.eq(pz.slots, ["", "par_4", "", ""], "… and lays nothing")
	kit.ok(pz.modal_input(key_event(KEY_R)), "R consumed")
	kit.eq(pz.slots, ["", "", "", ""], "R clears the board")
	kit.ok(not pz.modal_input(key_event(KEY_ESCAPE)), "Esc is left to UIRoot -> handle_cancel")
	kit.ok(not pz.modal_input(key_event(KEY_3, false)), "key releases are ignored")
	kit.eq(pz.slots, ["", "", "", ""], "release did not lay a card")
	return true


func _mouse() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	# click an empty row first: it is chosen for the next card (by click, by key, by tray click)
	pz._slot_buttons[2].pressed.emit()
	kit.eq(pz.armed, 2, "click on an empty row chooses it")
	kit.ok(pz._slot_armed[2].visible, "the chosen row is outlined")
	kit.eq(pz._state_label.text, UIKit.t("ui.c3p2.check.state_armed", {"n": 3}), "state names the chosen paper")
	pz._tray_buttons["par_4"].pressed.emit()
	kit.eq(pz.slots, ["", "", "par_4", ""], "a tray click lays into the chosen row")
	kit.eq(pz.armed, -1, "the choice is used up")
	pz.arm(3)
	pz.modal_input(key_event(KEY_2))
	kit.eq(pz.slots, ["", "", "par_4", "january"], "a key lays into the chosen row as well")
	pz._tray_buttons["out_2340"].pressed.emit()
	kit.eq(pz.slots, ["out_2340", "", "par_4", "january"], "without a choice: the next empty row from the top")
	pz.arm(1)
	kit.ok(pz.arm(1) and pz.armed == -1, "a second click on the chosen row forgets it")
	kit.ok(not pz.arm(0), "a filled row cannot be chosen")
	# a filled row: click takes the card back
	pz._slot_buttons[0].pressed.emit()
	kit.eq(pz.slots, ["", "", "par_4", "january"], "click on a filled row takes its card back")
	# drag and drop through the forwarded drop handlers
	var data := {"aoe_c3p2_card": "in_c17_44", "from": -1}
	kit.ok(pz._can_drop_slot(Vector2.ZERO, data, 3), "a tray card can be dropped on an occupied row")
	kit.ok(pz._slot_armed[3].visible, "the row under the dragged card is outlined")
	pz._drop_on_slot(Vector2.ZERO, data, 3)
	kit.eq(pz.slots, ["", "", "par_4", "in_c17_44"], "drop on an occupied row: the occupant goes back to the tray")
	kit.ok(not ("january" in pz.history), "the sent-back card left the history")
	kit.ok(not pz._slot_armed[3].visible, "outline gone after the drop")
	pz._drop_on_slot(Vector2.ZERO, {"aoe_c3p2_card": "par_4", "from": 2}, 0)
	kit.eq(pz.slots, ["par_4", "", "", "in_c17_44"], "row to row: the card moves")
	pz._drop_on_slot(Vector2.ZERO, {"aoe_c3p2_card": "in_c17_44", "from": 3}, 0)
	kit.eq(pz.slots, ["in_c17_44", "", "", "par_4"], "row to an occupied row: the two swap")
	kit.ok(not pz._can_drop_slot(Vector2.ZERO, {"foo": 1}, 1), "foreign drag data is refused")
	kit.ok(pz._can_drop_tray(Vector2.ZERO, {"aoe_c3p2_card": "par_4", "from": 3}), "a row card can go back onto the tray")
	pz._drop_on_tray(Vector2.ZERO, {"aoe_c3p2_card": "par_4", "from": 3})
	kit.eq(pz.slots, ["in_c17_44", "", "", ""], "drop on the tray takes it back")
	kit.ok(not pz._can_drop_tray(Vector2.ZERO, {"aoe_c3p2_card": "out_2340", "from": -1}), "tray to tray is no drop")
	kit.eq(pz._drag_from_tray(Vector2.ZERO, "in_c17_44", pz._tray_buttons["in_c17_44"]), null, "a laid card cannot be dragged from the tray")
	var d2 = pz._drag_from_tray(Vector2(10, 10), "out_2340", pz._tray_buttons["out_2340"])
	kit.eq(d2, {"aoe_c3p2_card": "out_2340", "from": -1}, "drag data of a tray card")
	pz._tray_buttons["out_2340"].pressed.emit()
	kit.eq(pz.slots, ["in_c17_44", "", "", ""], "a click that ends a drag lays nothing")
	pz.notification(Node.NOTIFICATION_DRAG_END)
	kit.ok(not pz._dragging, "drag state cleared at the end of the drag")
	kit.eq(g.puzzle_attempts(OBJ), 0, "mouse handling never submits")
	return true


static func pad_event(button: int, pressed := true) -> InputEventJoypadButton:
	var ev := InputEventJoypadButton.new()
	ev.button_index = button as JoyButton
	ev.pressed = pressed
	return ev


## Pad A is "interact"/"advance" in this game (not ui_accept): the check presses the focused control itself.
func _controller() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	pz._slot_buttons[2].grab_focus()
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_A)), "A consumed")
	kit.eq(pz.armed, 2, "A on an empty row chooses it")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_A, false)), "the A release is swallowed too")
	pz._tray_buttons["january"].grab_focus()
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.slots, ["", "", "january", ""], "A on a tray card lays it into the chosen row")
	pz._tray_buttons["par_4"].grab_focus()
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.slots, ["par_4", "", "january", ""], "A on a tray card without a choice: next empty row")
	pz._slot_buttons[0].grab_focus()
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.slots, ["", "", "january", ""], "A on a filled row takes its card back")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_X)), "X consumed")
	kit.eq(pz.slots, ["", "", "", ""], "X takes back the last entry")
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_Y)), "Y consumed")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3p2.check.incomplete"), "Y checks (incomplete: no attempt)")
	kit.eq(g.puzzle_attempts(OBJ), 0, "no attempt")
	pz._tray_buttons["out_2340"].grab_focus()
	pz._tray_buttons["out_2340"].disabled = true
	pz.modal_input(pad_event(JOY_BUTTON_A))
	kit.eq(pz.slots, ["", "", "", ""], "A never presses a disabled control")
	pz._tray_buttons["out_2340"].disabled = false
	kit.ok(not pz.modal_input(pad_event(JOY_BUTTON_B)), "B is left to UIRoot (cancel -> handle_cancel)")
	kit.ok(not pz.modal_input(pad_event(JOY_BUTTON_DPAD_LEFT)), "the D-pad is left to the GUI focus")
	pz.arm(1)
	kit.ok(pz.handle_cancel() and pz.is_open and pz.armed == -1, "B: forgets the chosen row first")
	for sym in SOLUTION:
		pz.place(sym)
	pz.modal_input(pad_event(JOY_BUTTON_Y))
	kit.ok(pz.is_done(), "Y checks the full board: solved")
	pz._solved_at -= 1000
	kit.ok(pz.modal_input(pad_event(JOY_BUTTON_A)) and not pz.is_open, "A after the success guard closes")
	return true


## Exactly what scripts/core/inputplay.gd::_check_puzzle presses: 1 2 3 4 Enter (tray order = wrong), 4x
## Backspace, the solution by its position in `symbols`, Enter.
func _inputplay_sequence() -> bool:
	var g := _story(true)
	var pz := _make(g)
	var count := [0]
	pz.solved.connect(func(_id: String) -> void: count[0] += 1)
	pz.open(OBJ)
	kit.ok(pz.get("is_open") == true, "is_open after open()")
	var shown: Array = pz.get("symbols") if pz.get("symbols") is Array else []
	kit.eq(shown, DISPLAY, "symbols readable by the driver")
	for k in [KEY_1, KEY_2, KEY_3, KEY_4]:
		kit.ok(pz.modal_input(key_event(k)), "number key consumed")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter consumed")
	kit.ne(g.objective_state(OBJ), "complete", "the tray order is wrong")
	kit.eq(g.puzzle_attempts(OBJ), 1, "one attempt")
	for i in 4:
		pz.modal_input(key_event(KEY_BACKSPACE))
	kit.eq(pz.slots, ["", "", "", ""], "4x Backspace clears the board")
	for sym in SOLUTION:
		pz.modal_input(key_event(KEY_1 + shown.find(sym)))
	kit.eq(pz.slots, SOLUTION, "solution laid by keys")
	pz.modal_input(key_event(KEY_ENTER))
	kit.eq(g.objective_state(OBJ), "complete", "objective complete through Story.solve_puzzle")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.success_beat() < 8.0, "auto-close inside the 8 s the driver waits")
	return true


func _correct() -> bool:
	var g := _story(true)
	var pz := _make(g)
	var count := [0]
	pz.solved.connect(func(id: String) -> void:
		count[0] += 1
		kit.eq(id, OBJ, "solved(obj_id)"))
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(OBJ)
	pz.arm(3)
	pz.place("january")                           # rows in any order: the answer is the board top -> bottom
	pz.arm(1)
	pz.place("out_2340")
	_fill(pz, ["in_c17_44", "par_4"])
	kit.eq(pz.slots, SOLUTION, "board top -> bottom")
	pz.submit()
	kit.eq(g.objective_state(OBJ), "complete", "objective complete in the Story engine")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.is_done() and pz.success_shown(), "success shown")
	kit.eq(pz._success_label.text, UIKit.t("ui.c3p2.check.success"), "success text (C3P2_DESIGN §2.7)")
	kit.eq(pz.marks_shown(), 4, "the matching marks on all four papers (reduced motion: at once)")
	for i in 4:
		var t: String = pz._slot_texts[i].text
		kit.ok(t.contains("[u]"), "row %d: the shared words are underlined on the entry" % (i + 1))
	kit.ok(pz._slot_texts[2].text.contains("„Begleitgut“[/u]"), "par_4: „Begleitgut“ marked")
	kit.ok(pz.kordon_shown() and not pz._tray_col.visible, "the brace bundles the four rows: Kordon-17")
	kit.eq(pz._state_label.text, UIKit.t("ui.c3p2.check.state_done"), "state: done")
	kit.eq(pz._close_btn.text, UIKit.t("ui.c3p2.check.continue"), "close button becomes Weiter")
	kit.ok(not pz.hint_shown() and not pz.lupe_shown(), "no hint, no Lupe after success")
	kit.eq(pz.submit(), {}, "a second submit does nothing")
	kit.ok(not pz.place("par_4") and not pz.undo() and not pz.reset_order() and not pz.arm(0), "board locked after success")
	kit.ok(not pz.drop_card("par_4", 2, 0), "no drag and drop after success")
	kit.eq(count[0], 1, "still exactly one solved signal")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)) and pz.is_open, "Enter right after success is swallowed (guard)")
	var beat: float = pz.success_beat()
	kit.ok(beat >= 3.0 and beat <= 7.5, "auto-close beat %.2f s: a reading pause, inside the driver's 8 s" % beat)
	pz._solved_at -= 1000
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter after the guard confirms")
	kit.ok(not pz.is_open and not pz.visible, "closed on confirm")
	kit.eq(closed[0], 1, "closed emitted once")
	pz.open(OBJ)
	kit.ok(not pz.is_done() and pz.slots == ["", "", "", ""] and pz.marks_shown() == 0, "reopening starts clean")
	kit.ok(pz._tray_col.visible and not pz.kordon_shown(), "tray back, brace hidden")
	return true


## 125 % / 150 %: every scalable text follows the setting, the whole modal still fits 1920x1080 (with the
## wrong note AND the hint on screen, and with the success text), the notes go side by side, and the Lupe
## shows the focused card / row in the scaled size. 100 %: no Lupe (the card faces are enough).
func _text_scale() -> bool:
	var g := _story(true)
	var pz := _make(g, 2)                         # hint at once: the tallest notes
	pz.open(OBJ)
	_fill(pz, DISPLAY)
	pz.submit()
	var s = UIKit.overrides["Settings"]
	for scale in [1.0, 1.25, 1.5]:
		s.set_value("text_scale", scale)
		UIKit.refresh_text_scale()                # what UIRoot does on Settings.changed
		kit.eq(pz._hint_label.get_theme_font_size("font_size"), int(round(22 * scale)), "hint follows %d %%" % int(scale * 100))
		kit.eq(pz._feedback.get_theme_font_size("font_size"), int(round(24 * scale)), "wrong note follows %d %%" % int(scale * 100))
		kit.eq(pz._notes_row.vertical, scale < 1.1, "notes stacked at 100 %, side by side above")
		force_layout(pz)
		var need: Vector2 = pz._panel.get_combined_minimum_size()
		kit.ok(need.y <= 1080 - 20 and need.x <= 1920 - 56, "%d %%: fits 1920x1080 with note + hint (needs %s)" % [int(scale * 100), need])
		kit.ok(pz._hint_label.get_line_count() <= pz._hint_label.get_visible_line_count() + 0, "%d %%: hint not clipped" % int(scale * 100))
	# the Lupe
	s.set_value("text_scale", 1.0)
	UIKit.refresh_text_scale()
	pz.reset_order()
	pz._tray_buttons["january"].grab_focus()
	kit.ok(not pz.lupe_shown(), "100 %: no Lupe")
	s.set_value("text_scale", 1.5)
	UIKit.refresh_text_scale()
	kit.ok(pz.lupe_shown(), "150 %: the Lupe follows the focused card at once")
	kit.ok(pz.lupe_text().contains(UIKit.t("ui.c3p2.check.card.january")), "Lupe = full text of the focused entry")
	kit.eq(pz._lupe_text.get_theme_font_size("font_size"), 33, "Lupe text at 150 %")
	pz._slot_buttons[1].grab_focus()
	kit.ok(pz.lupe_text().contains(UIKit.t("ui.c3p2.check.row.departures")) and
		pz.lupe_text().contains(UIKit.t("ui.c3p2.check.lupe.empty")), "Lupe on an empty row: the paper + no entry yet")
	pz.place("out_2340")
	pz._slot_buttons[0].grab_focus()
	kit.ok(pz.lupe_text().contains(UIKit.t("ui.c3p2.check.card.out_2340")), "Lupe on a filled row: paper and entry side by side")
	pz._show_lupe(pz._paper_cells[3], "row", 3)
	kit.ok(pz.lupe_text().contains(UIKit.t("ui.c3p2.check.row.timetable")), "Lupe on a paper (mouse over the strip)")
	pz._hide_lupe(pz._paper_cells[3])
	kit.ok(not pz.lupe_shown(), "leaving hides the Lupe")
	# success at 150 %: still fits
	pz.reset_order()
	_fill(pz, SOLUTION)
	pz.submit()
	force_layout(pz)
	var need2: Vector2 = pz._panel.get_combined_minimum_size()
	kit.ok(pz.success_shown() and need2.y <= 1080 - 20, "150 %%: the success text fits (needs %s)" % need2)
	kit.ok(not pz.lupe_shown(), "no Lupe after success")
	return true


## WCAG 2.x: every text the board draws itself >= 4.5:1 (>= 7:1 with high contrast); the backgrounds are the
## real art colours (board json surfaces, re-measured from the PNG). Cards differ by glyph SHAPE.
func _contrast() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	var b = JSON.parse_string(FileAccess.get_file_as_string(BOARD))
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c3p2_card_par_4.png"))
	var tr: Array = b["card"]["text"]
	var cols := {}
	for y in range(int(tr[1]), int(tr[1]) + int(tr[3])):
		for x in range(int(tr[0]), int(tr[0]) + int(tr[2])):
			var h := img.get_pixel(x, y).to_html(false)
			cols[h] = int(cols.get(h, 0)) + 1
	var darkest := Color.WHITE
	for h in cols:
		if luminance(Color(h)) < luminance(darkest):
			darkest = Color(h)
	var pairs: Array = pz.contrast_pairs()
	kit.ok(pairs.size() >= 6, "contrast pairs reported")
	for p in pairs:
		var r := contrast(p["fg"], p["bg"])
		kit.ok(r >= 4.5, "%s: %.2f : 1 >= 4.5" % [p["what"], r])
	kit.ok(contrast(load(SCRIPT).INK, darkest) >= 7.0, "entry text vs the darkest paper pixel of the text field: %.2f" % contrast(load(SCRIPT).INK, darkest))
	UIKit.overrides["Settings"].set_value("high_contrast", true)
	for p in pz.contrast_pairs():
		var r := contrast(p["fg"], p["bg"])
		kit.ok(r >= 7.0, "high contrast — %s: %.2f : 1 >= 7" % [p["what"], r])
	_fill(pz, SOLUTION)
	pz.submit()
	kit.ok(pz._slot_texts[0].text.contains(load(SCRIPT).PENCIL_HC.to_html(false)), "high contrast: the darker pencil marks the shared words")
	# shape, not colour: the four glyph boxes differ as silhouettes
	var masks := {}
	var gb: Array = b["card"]["glyph_box"]
	for cid in SOLUTION:
		var ci := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c3p2_card_%s.png" % cid))
		var m := ""
		for y in range(int(gb[1]), int(gb[1]) + int(gb[3])):
			for x in range(int(gb[0]), int(gb[0]) + int(gb[2])):
				m += "1" if luminance(ci.get_pixel(x, y)) < 0.05 else "0"
		masks[cid] = m
	var uniq := {}
	for cid in masks:
		uniq[masks[cid]] = cid
	kit.eq(uniq.size(), 4, "four different glyph silhouettes (ring, cross, star, bowtie)")
	kit.eq(_glyph_ids(b["card"]["glyphs"]), SOLUTION.duplicate(), "every entry has a glyph")
	return true


static func _glyph_ids(d: Dictionary) -> Array:
	var out: Array = []
	for cid in SOLUTION:
		if d.has(cid):
			out.append(cid)
	return out


func _escape() -> bool:
	var g := _story(true)
	var pz := _make(g)
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(OBJ)
	_fill(pz, ["in_c17_44"])
	pz.arm(2)
	kit.ok(pz.handle_cancel(), "first Esc/B handled")
	kit.ok(pz.is_open and pz.armed == -1, "… forgets the chosen row, the check stays open")
	kit.ok(pz.handle_cancel(), "second Esc/cancel handled")
	kit.ok(not pz.is_open and not pz.visible, "Esc closes")
	kit.eq(closed[0], 1, "closed emitted")
	kit.eq(g.puzzle_attempts(OBJ), 0, "closing is not an attempt")
	kit.eq(g.objective_state(OBJ), "available", "objective still available")
	return true


func _locked() -> bool:
	var g := _story(false)
	kit.eq(g.objective_state(OBJ), "locked", "without the comparison the check is locked")
	var pz := _make(g)
	pz.open(OBJ)
	_fill(pz, SOLUTION)
	var r: Dictionary = pz.submit()
	kit.eq(r.get("ok"), false, "engine refuses")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3p2.check.error", {"error": UIKit.t("sys.err.locked")}), "localised engine error shown")
	kit.eq(g.puzzle_attempts(OBJ), 0, "no attempt")
	kit.ok(pz.is_open and not pz.is_done(), "nothing breaks: still open, not solved")
	kit.eq(pz.slots, SOLUTION, "cards stay")
	kit.ok(pz.handle_cancel() and not pz.is_open, "can be closed")
	return true


func _refused() -> bool:
	var st := RefusingStory.new()
	kit.track(st)
	var pz := _make(st)
	pz.open(OBJ)
	kit.eq(pz.symbols, DISPLAY, "display order from data/v3 when the Story has no puzzle_for")
	_fill(pz, SOLUTION)
	pz.submit()
	kit.eq(st.calls, 1, "submitted once")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3p2.check.error", {"error": UIKit.t("sys.err.missing_clues")}),
		"missing clues: localised engine message")
	kit.ok(not pz.is_done() and pz.is_open, "still open")
	UIKit.overrides["Story"] = null
	pz.submit()
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3p2.check.error", {"error": UIKit.t("ui.common.unavailable")}),
		"no Story: 'Nicht verfügbar'")
	kit.ok(not pz.is_done(), "not solved")
	return true


func _loc_keys() -> bool:
	var loc: Node = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var re := RegEx.new()
	re.compile("\"(ui\\.[a-z0-9_.]+)\"")
	var wanted := {}
	for m in re.search_all(FileAccess.get_file_as_string(SCRIPT)):
		var k := m.get_string(1)
		if not k.ends_with("."):
			wanted[k] = true
	for sym in SOLUTION:
		wanted["ui.c3p2.check.card." + sym] = true
	for r in ["weighbill", "departures", "travel_order", "timetable"]:
		wanted["ui.c3p2.check.row." + r] = true
	kit.ok(wanted.size() >= 40, "keys collected (%d)" % wanted.size())
	kit.eq(loc.missing(wanted.keys()), [], "Loc keys used by the check")
	kit.eq(loc.t("ui.c3p2.check.hint"), "Lies Alexeis Zeilen einzeln und such im Eingangsbuch dieselbe Zahl: Plombe, Uhrzeit, Anzahl der Wagen. Für den Reiseauftrag hilft Elenas Randnotiz zu Paragraph vier.", "hint text (C3P2_DESIGN §2.7)")
	kit.eq(loc.t("ui.c3p2.check.success"), "Jede Fahrt hat zwei Papiere. Auf der Waage steht Akten, in der Registratur Begleitgut, in der russischen Spalte Personen. Und alle Wege enden am selben Ort: Kordon-17, Erfassungsraum.", "success text (C3P2_DESIGN §2.7)")
	for k in ["ui.c3p2.check.check", "ui.c3p2.check.undo", "ui.c3p2.check.reset", "ui.c3p2.check.close"]:
		kit.eq(loc.t(k), loc.t(k.replace("c3p2.check", "c3.protocol")), "same button words as the protocol puzzle: " + k)
	var all_text := ""
	for k in loc.keys():
		if str(k).begins_with("ui.c3p2.check."):
			all_text += loc.t(k) + "\n"
	kit.ok(all_text.contains("Alexei") and not all_text.contains("\"") and not all_text.contains(" - "),
		"German typography („…“, –); the protagonists by their names (the old-name scan is test_rename_guard.gd)")
	for sym in SOLUTION:
		var t: String = loc.t("ui.c3p2.check.card." + sym)
		var found := 0
		for w in load(SCRIPT).MATCH_WORDS[sym]:
			if t.contains(str(w)):
				found += 1
		kit.ok(found >= 1, "%s: the shared words are in the entry text" % sym)
	return true


func _board_art() -> bool:
	var b = JSON.parse_string(FileAccess.get_file_as_string(BOARD))
	kit.ok(b is Dictionary, "board json parses")
	kit.eq([b.get("puzzle_id"), b.get("objective"), int(b.get("display_scale", 0))], ["pz_c3_check", OBJ, 3], "board identity")
	var pzj = JSON.parse_string(FileAccess.get_file_as_string("res://data/v3/puzzles.json"))
	var p: Dictionary = {}
	for x in pzj["puzzles"]:
		if x["id"] == "pz_c3_check":
			p = x
	var pairs: Array = []
	var items: Array = []
	var lay: Dictionary = b["layout"]
	for r in b["rows"]:
		pairs.append(str(r["pairs_with"]))
		items.append(str(r["item"]))
		var path := "res://assets/ui/puzzle/" + str(r["file"])
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		var mimg := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/" + str(r["mark_file"])))
		kit.ok(img != null and not img.is_empty() and mimg != null and not mimg.is_empty(), str(r["id"]) + ": strip + marks exist")
		if img == null or img.is_empty():
			continue
		kit.eq([img.get_width(), img.get_height()], [int(r["size"][0]), int(r["size"][1])], str(r["id"]) + ": size")
		kit.eq([mimg.get_width(), mimg.get_height()], [img.get_width(), img.get_height()], str(r["id"]) + ": marks match the strip")
		kit.ok(img.get_height() + int(lay["label_h"]) <= int(lay["row_h"]), str(r["id"]) + ": strip + label fit the row")
		kit.ok(img.get_width() <= int(lay["paper_w"]), str(r["id"]) + ": strip fits the paper column")
		var inside := true
		for m in r["marks"]:
			var rc: Array = m["rect"]
			inside = inside and rc[0] >= 0 and rc[1] >= 0 and rc[0] + rc[2] <= img.get_width() and rc[1] + rc[3] <= img.get_height()
		kit.ok(inside and r["marks"].size() >= 2, str(r["id"]) + ": every mark sits on the strip")
		var doc := UIKit.doc_for_item(str(r["item"]))
		kit.eq(doc, str(r["doc"]), str(r["id"]) + ": cut from the inspect document of " + str(r["item"]))
	kit.eq(items, ROW_ITEMS, "rows = Alexei's freight chain in the order of C3P2_DESIGN §2.7")
	kit.eq(pairs, p.get("solution"), "each row's partner = the canonical solution")
	kit.eq(b["solution_check"]["display_symbols"], p.get("display_symbols"), "board generated against the current display order")
	for cid in SOLUTION:
		var ci := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c3p2_card_%s.png" % cid))
		kit.eq([ci.get_width(), ci.get_height()], [int(b["card"]["size"][0]), int(b["card"]["size"][1])], cid + ": card size")
	var sl := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c3p2_slot.png"))
	kit.eq([sl.get_width(), sl.get_height()], [int(b["card"]["size"][0]), int(b["card"]["size"][1])], "slot = card size")
	var br := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/puzzle/c3p2_bracket.png"))
	kit.ok(br.get_height() <= 4 * int(lay["row_h"]) + 3 * int(lay["row_gap"]), "the brace spans the four rows")
	kit.ok(FileAccess.file_exists("res://documentation/asset_manifest_parts/c3p2_puzzle.md"), "provenance part exists")
	return true
