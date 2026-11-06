extends "res://scripts/ui/ui_modal.gd"
## Blueprint overlay puzzle (pz_blueprint): plan B (earlier draft, tracing paper) over plan A (approved)
## on the grid defined by assets/ui/documents/berlin_plans.json (cell size, files, landmarks, start).
## Falls back to the 16 px grid placeholder plans in assets/ui/puzzle/ when the documents are missing.
## Arrows/WASD/D-pad move one cell (snap), R / Shift+R (RB / LB) rotate 90 degrees, drag with the mouse,
## "Abgleichen" submits {rotation_steps, offset_x, offset_y} via Story.solve_puzzle. No penalties; hint after
## the configured failures. Marks: A = ring, B = diamond (shape-coded, colour independent).

signal solved(obj_id: String)

const BoardScript := preload("res://scripts/ui/blueprint_board.gd")
const DOCS := "res://assets/ui/documents/"
const PLACEHOLDER_DIR := "res://assets/ui/puzzle/"

var suppress_toasts := true
var obj_id := ""
var _puzzle: Dictionary = {}
## Default start: plan B upside down on top of A (rotation is clearly wrong, sheet stays on the table).
var _start := {"rotation_steps": 2, "offset_x": 0, "offset_y": 0}
var _fails := 0
var _done := false
var _using_placeholder := false
var _board: Control
var _board_panel: PanelContainer
var _state_label: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _placeholder_note: Label
var _confirm_btn: Button
var _rotate_btn: Button
var _reset_btn: Button
var _close_btn: Button


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.74))
	var row := Kit.hbox(24)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	row.offset_left = 36
	row.offset_right = -36
	row.offset_top = 40
	row.offset_bottom = -40
	add_child(row)
	# left column: light table + actions
	var left := Kit.vbox(14)
	left.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_child(left)
	_board_panel = Kit.panel()
	left.add_child(_board_panel)
	var bv := Kit.vbox(10)
	_board_panel.add_child(bv)
	_board = BoardScript.new()
	_board.changed.connect(_on_board_changed)
	_board.mark_aligned.connect(func(_n): Kit.ui_sound("snap"))
	bv.add_child(_board)
	_placeholder_note = Kit.label(Kit.t("ui.blueprint.placeholder"), "ControlHintLabel")
	_placeholder_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bv.add_child(_placeholder_note)
	var actions := Kit.hbox(16)
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(actions)
	_rotate_btn = Kit.button(Kit.t("ui.blueprint.rotate"), "", 220)
	_rotate_btn.pressed.connect(func(): _board.rotate_by(1))
	actions.add_child(_rotate_btn)
	_reset_btn = Kit.button(Kit.t("ui.blueprint.reset"), "", 220)
	_reset_btn.pressed.connect(_reset_state)
	actions.add_child(_reset_btn)
	_confirm_btn = Kit.button(Kit.t("ui.blueprint.confirm"), "", 220)
	_confirm_btn.pressed.connect(submit)
	actions.add_child(_confirm_btn)
	_close_btn = Kit.button(Kit.t("ui.common.close"), "", 220)
	_close_btn.pressed.connect(close)
	actions.add_child(_close_btn)
	left.add_child(Kit.controls_row([
		["%s|%s|%s|%s" % [Kit.t("ui.key.left"), Kit.t("ui.key.right"), Kit.t("ui.key.up"), Kit.t("ui.key.down")], Kit.t("ui.hint.move")],
		["R", Kit.t("ui.hint.rotate")], [Kit.t("ui.key.mouse"), Kit.t("ui.hint.drag")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.hint.confirm")], [Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]]))
	# right column: brief, legend, state, feedback, hint
	var side := Kit.panel()
	side.custom_minimum_size = Vector2(600, 960)   # fixed height: the layout never jumps when hints appear
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(side)
	var v := Kit.vbox(14)
	side.add_child(v)
	v.add_child(Kit.label(Kit.t("ui.blueprint.title"), "HeadingLabel"))
	v.add_child(Kit.wrap_label(Kit.t("ui.blueprint.subtitle"), "DimLabel"))
	v.add_child(HSeparator.new())
	var instr := Kit.wrap_label(Kit.t("ui.blueprint.instruction"), "BodyLabel")
	Kit.scalable(instr, 27)
	v.add_child(instr)
	for leg in [["mark_a", "ui.blueprint.legend_a"], ["mark_b", "ui.blueprint.legend_b"]]:
		var lr := Kit.hbox(18)
		var chip := Kit.panel("PaperCardPanel")
		chip.add_theme_stylebox_override("panel", _chip_box())
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var ic := Kit.sprite("res://assets/ui/puzzle/%s.png" % leg[0])
		ic.custom_minimum_size = Vector2(54, 54)
		chip.add_child(ic)
		lr.add_child(chip)
		var ll := Kit.label(Kit.t(leg[1]), "BodyLabel", 27)
		ll.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		lr.add_child(ll)
		v.add_child(lr)
	var sep := HSeparator.new()
	sep.theme_type_variation = "FaintSeparator"
	v.add_child(sep)
	_state_label = Kit.label("", "KickerLabel", 24)
	v.add_child(_state_label)
	_feedback = Kit.wrap_label("", "BodyLabel")
	_feedback.custom_minimum_size.y = 36
	Kit.scalable(_feedback, 26)
	v.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	var hh := Kit.hbox(14)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hh.add_child(hic)
	_hint_label = Kit.wrap_label(Kit.t("ui.blueprint.hint"), "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 24)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	v.add_child(_hint_box)


func _chip_box() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/paper_card.png")
	for side_i in 4:
		st.set_texture_margin(side_i, 9)
		st.set_content_margin(side_i, 9)
	return st


func open(id: String) -> void:
	obj_id = id
	_puzzle = Kit.puzzle_for_objective(id)
	_fails = 0
	_done = false
	_board.locked = false
	_feedback.text = ""
	_load_plans()
	_reset_state()
	open_modal()


func _load_plans() -> void:
	var meta = Kit.json(DOCS + "berlin_plans.json")
	if not (meta is Dictionary):
		meta = {}
	var cell := int(meta.get("cell_px", meta.get("cell", meta.get("cell_size", 16))))
	var pa = meta.get("plan_a", meta.get("a", "berlin_plan_a.png"))
	var pb = meta.get("plan_b", meta.get("b", "berlin_plan_b.png"))
	var ta := Kit.optional_tex(DOCS + _file_of(pa))
	# the overlay prefers the line-only sheet (transparent paper) so plan A stays readable underneath
	var tb: Texture2D = null
	var b_opaque := false
	if pb is Dictionary and pb.has("lines"):
		tb = Kit.optional_tex(DOCS + str(pb["lines"]).get_file())
	if tb == null:
		tb = Kit.optional_tex(DOCS + _file_of(pb))
		b_opaque = tb != null
	var marks: Array = _parse_landmarks(meta.get("landmarks", []))
	if marks.is_empty() and pa is Dictionary and pb is Dictionary:
		marks = _pair_landmarks(pa.get("landmarks", {}), pb.get("landmarks", {}))
	var origin := _v2i(meta.get("b_origin", [0, 0]))
	_using_placeholder = ta == null or tb == null
	if _using_placeholder:
		var pm = Kit.json(PLACEHOLDER_DIR + "plan_placeholder.json")
		pm = pm if pm is Dictionary else {}
		ta = Kit.tex(PLACEHOLDER_DIR + "plan_placeholder_a.png")
		tb = Kit.tex(PLACEHOLDER_DIR + "plan_placeholder_b.png")
		cell = int(pm.get("cell", 16))
		marks = _parse_landmarks(pm.get("landmarks", []))
		origin = Vector2i.ZERO
	var st = meta.get("start", {})
	if st is Dictionary and not st.is_empty():
		_start = {"rotation_steps": int(st.get("rotation_steps", 1)), "offset_x": int(st.get("offset_x", 0)),
			"offset_y": int(st.get("offset_y", 0))}
	_board.max_cells = Vector2i(22, 14)
	_board.setup(ta, tb, cell, marks, origin, b_opaque and not _using_placeholder)
	_placeholder_note.visible = _using_placeholder


func _file_of(v) -> String:
	if v is Dictionary:
		return str(v.get("file", v.get("image", "")))
	var s := str(v)
	return s.get_file() if s.begins_with("res://") else s


func _v2i(v) -> Vector2i:
	if v is Array and v.size() >= 2:
		return Vector2i(int(v[0]), int(v[1]))
	if v is Dictionary:
		return Vector2i(int(v.get("x", 0)), int(v.get("y", 0)))
	return Vector2i.ZERO


func _parse_landmarks(arr) -> Array:
	var out: Array = []
	if not (arr is Array):
		return out
	for e in arr:
		if e is Dictionary and e.has("a") and e.has("b"):
			var a: Array = e["a"]
			var b: Array = e["b"]
			out.append({"name": str(e.get("name", "")), "a": Vector2(float(a[0]) + 0.5, float(a[1]) + 0.5),
				"b": Vector2(float(b[0]) + 0.5, float(b[1]) + 0.5)})
	return out


## {name: {cell: [x, y], size: [w, h]}} for A and B -> [{name, a: centre, b: centre}] in cells.
func _pair_landmarks(la, lb) -> Array:
	var out: Array = []
	if not (la is Dictionary and lb is Dictionary):
		return out
	for k in la:
		if not lb.has(k):
			continue
		var ca = _centre(la[k])
		var cb = _centre(lb[k])
		if ca != null and cb != null:
			out.append({"name": str(k), "a": ca, "b": cb})
	return out


func _centre(e):
	if not (e is Dictionary) or not (e.get("cell") is Array):
		return null
	var c: Array = e["cell"]
	var s: Array = e.get("size", [1, 1])
	return Vector2(float(c[0]) + float(s[0]) * 0.5, float(c[1]) + float(s[1]) * 0.5)


func _reset_state() -> void:
	if _done:
		return
	_board.set_state(int(_start["rotation_steps"]), Vector2i(int(_start["offset_x"]), int(_start["offset_y"])))


func _on_board_changed() -> void:
	var off: Vector2i = _board.offset
	_state_label.text = Kit.t("ui.blueprint.state", {"rot": _board.rotation_steps * 90,
		"x": ("%+d" % off.x), "y": ("%+d" % off.y)}).to_upper().replace("ß", "SS")
	_refresh_hint()


func submit() -> void:
	if _done:
		return
	var answer := {"rotation_steps": int(_board.rotation_steps), "offset_x": int(_board.offset.x),
		"offset_y": int(_board.offset.y)}
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	var is_solved: bool = bool(r) if r is bool else (ok and bool((r as Dictionary).get("solved", false)))
	if r == null or not ok:
		var e := Kit.err_text(r)
		_set_feedback(Kit.t("ui.blueprint.error", {"error": e if e != "" else Kit.t("ui.common.unavailable")}), false)
		return
	if is_solved:
		_done = true
		_board.locked = true
		_set_feedback(Kit.t("ui.blueprint.solved"), true)
		Kit.ui_sound("success_plan")
		_refresh_hint()
		_confirm_btn.disabled = true
		solved.emit(obj_id)
		await get_tree().create_timer(2.0 if not Kit.reduced_motion() else 1.3).timeout
		if is_open:
			close()
		return
	_fails += 1
	Kit.ui_sound("fail")
	_set_feedback(Kit.t("ui.blueprint.wrong"), false)
	_refresh_hint()


func _set_feedback(text: String, good: bool) -> void:
	_feedback.text = text
	_feedback.add_theme_color_override("font_color", Kit.C_AMBER if good else Kit.C_TEXT)


func _refresh_hint() -> void:
	var mode := int(Kit.setting("puzzle_hints", 1))
	var vis := false
	if mode >= 2:
		vis = true
	elif mode == 1:
		var r = Kit.call_svc("Story", "puzzle_hint_available", [obj_id], null)
		if r is bool:
			vis = r
		elif r is Dictionary:
			vis = bool(r.get("available", r.get("hint", false)))
		else:
			vis = _fails >= int(_puzzle.get("hint_after_attempts", 2))
	_hint_box.visible = vis and not _done


func _on_open() -> void:
	_confirm_btn.disabled = false
	_refresh_hint()


func focus_default() -> void:
	_confirm_btn.grab_focus()


func modal_input(event: InputEvent) -> bool:
	if _done:
		return false
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_RIGHT_SHOULDER:
			_board.rotate_by(1)
			return true
		if event.button_index == JOY_BUTTON_LEFT_SHOULDER:
			_board.rotate_by(-1)
			return true
	if event is InputEventKey and event.pressed and (event as InputEventKey).physical_keycode == KEY_R:
		_board.rotate_by(-1 if (event as InputEventKey).shift_pressed else 1)
		Kit.ui_sound("tick")
		return true
	var dirs := {"ui_left": Vector2i.LEFT, "ui_right": Vector2i.RIGHT, "ui_up": Vector2i.UP, "ui_down": Vector2i.DOWN,
		"move_left": Vector2i.LEFT, "move_right": Vector2i.RIGHT, "move_up": Vector2i.UP, "move_down": Vector2i.DOWN}
	for a in dirs:
		if InputMap.has_action(a) and event.is_action_pressed(a, true):
			_board.nudge(dirs[a])
			Kit.ui_sound("tick")
			return true
	return false
