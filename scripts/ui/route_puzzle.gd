extends "res://scripts/ui/ui_modal.gd"
## „Linie 74“ (pz_c4_routes / objective c4b_solve_routes, documentation/C4_DESIGN.md §2.7) — Konrad at the lit
## timetable case of the tram loop Süd 8, his light table.  Below: the site plan Süd 8 from the eviction notice
## (north up, three ventilation shafts S 1–S 3 as rings).  On top: Marta's tracing paper with line 74 as it ran
## in autumn and the detours of October, December and January (a diamond in each), drawn in driving direction —
## turned against the plan.  The player turns and moves the paper until every detour runs around a shaft.
## Geometry and art: assets/ui/documents/berlin_c4_routes.json + berlin_c4_routes_{plan,trace}.png
## (tools/pixelgen/gen_ui_c4.py verifies there that exactly one pose aligns all three pairs).
##
## Registered by data/chapters/c4.json (puzzles.c4b_solve_routes); ChapterExt.puzzle_ui instances this scene once
## under UIRoot, sets `ui_root`, Game calls open(obj_id) and awaits `closed`.  Works stand-alone (tests) as well.
##
## Key contract (= BlueprintPuzzle; scripts/core/inputplay.gd relies on it): property `is_open`; arrows / WASD
## move the paper one cell (RIGHT = offset_x + 1, UP = offset_y − 1), R turns it +90° (rotation_steps + 1 mod 4),
## Shift+R −90°, Backspace takes back the last move, Enter („Abgleichen“) submits {rotation_steps, offset_x,
## offset_y} (ints) through Story.solve_puzzle, Esc closes.  Pad: D-pad / left stick move, RB/LB turn, A checks,
## X back to the start pose, Y takes back the last move, B / Back close.  Mouse: drag the paper (snaps to the
## cells), wheel or right-click turns it, buttons Drehen · Zurücksetzen · Abgleichen · Schließen.
## Wrong answers cost nothing (the paper stays where it is): `ui.c4.routes.wrong_turned` while no detour CAN
## meet its shaft in this orientation (derived from the marks, not from the answer), else `ui.c4.routes.wrong`.
## Marks are shape-coded — ring (shaft) vs. hollow diamond (detour) — and a pair that lies on top of each other
## gets corner brackets; the side panel counts them.  Success: the red pencil circles the three pairs one by one
## („S 1 · Okt.“ …), then underlines „gez. K. A.“ in the plan's title block — Konrad drew the shafts.  Stamp +
## text, `solved(obj_id)` once, the modal closes after a reading beat (≤ SUCCESS_BEAT_MAX) or on confirm.

signal solved(obj_id: String)

const PX := 3
const DOCS := "res://assets/ui/documents/"
const ART := "res://assets/ui/puzzle/"
const LAYOUT := "res://assets/ui/documents/berlin_c4_routes.json"
const SUCCESS_GUARD_MS := 600
const SUCCESS_BEAT_MAX := 7.0
const MATCH_STEP := 0.42
const HISTORY_MAX := 64


## Light table: the plan (fixed), the tracing paper (turned in quarter steps around its centre, moved in whole
## cells), the HD words of the plan, alignment brackets and the success marks.
class RouteBoard extends Control:
	signal changed
	signal aligned_changed(count: int)
	signal drag_started
	signal turn_requested(steps: int)

	const UIKit := preload("res://scripts/ui/ui_kit.gd")
	const P := 3
	const GLASS := Color("3a3022")
	const GLASS_L := Color("5a4a31")
	const FRAME := Color("17120c")
	const GRID := Color(1.0, 0.9, 0.7, 0.07)
	const GRID_MAJOR := Color(1.0, 0.9, 0.7, 0.13)
	const PENCIL := Color("a8382e")
	const PENCIL_HC := Color("7a2a26")
	const INK := Color("1a1c2a")

	var cell := 16
	var board_cells := Vector2i(18, 14)
	var plan_at := Vector2i(2, 2)
	var plan_cells := Vector2i(14, 10)
	var trace_cells := Vector2i(10, 8)
	var b_origin := Vector2i(-1, 3)
	var rotation_steps := 0
	var offset := Vector2i.ZERO
	var off_min := Vector2i(-5, -8)
	var off_max := Vector2i(11, 4)
	var tex_plan: Texture2D
	var tex_trace: Texture2D
	var tex_snap: Texture2D
	var tex_match: Texture2D
	var tex_underline: Texture2D
	## [{id, cell: Vector2 (centre, plan cells), label}]
	var rings: Array = []
	## [{ring: index into rings, diamond: Vector2 (centre, trace cells), label}]
	var pairs: Array = []
	## [{rect: Rect2 (plan px), text}]
	var title_lines: Array = []
	var locked := false
	var matches_shown := 0
	var sign_shown := false
	var hover := false
	## High contrast: the darker pencil for the success labels.
	var hc := false
	var _dragging := false
	var _drag_from := Vector2.ZERO
	var _drag_offset := Vector2i.ZERO
	var _aligned := 0

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		clip_contents = true
		focus_mode = Control.FOCUS_NONE
		mouse_exited.connect(func() -> void:
			hover = false
			queue_redraw())

	func setup() -> void:
		custom_minimum_size = Vector2(board_cells * cell * P)
		size = custom_minimum_size
		var c0 := Vector2(plan_at + b_origin) + Vector2(trace_cells) * 0.5
		off_min = Vector2i(ceili(1.0 - c0.x), ceili(1.0 - c0.y))
		off_max = Vector2i(floori(board_cells.x - 1.0 - c0.x), floori(board_cells.y - 1.0 - c0.y))
		_aligned = _count_aligned()
		queue_redraw()

	func cp() -> float:
		return float(cell * P)

	func plan_origin() -> Vector2:
		return Vector2(plan_at) * cp()

	func trace_rect() -> Rect2:
		return Rect2(plan_origin() + Vector2(b_origin + offset) * cp(), Vector2(trace_cells) * cp())

	func trace_center() -> Vector2:
		var r := trace_rect()
		return r.position + r.size * 0.5

	func angle() -> float:
		return rotation_steps * PI * 0.5

	## Trace cells (unturned, from its top-left) -> board pixels for the current pose.
	func trace_point(local: Vector2) -> Vector2:
		var r := trace_rect()
		var c := trace_center()
		return c + (r.position + local * cp() - c).rotated(angle())

	func plan_point(cells: Vector2) -> Vector2:
		return plan_origin() + cells * cp()

	func ring_point(i: int) -> Vector2:
		return plan_point(rings[i]["cell"])

	func diamond_point(i: int) -> Vector2:
		return trace_point(pairs[i]["diamond"])

	func pair_aligned(i: int) -> bool:
		return diamond_point(i).distance_to(ring_point(int(pairs[i]["ring"]))) < 1.5

	func aligned_count() -> int:
		return _aligned

	func _count_aligned() -> int:
		var n := 0
		for i in pairs.size():
			if pair_aligned(i):
				n += 1
		return n

	## True when some offset could put every diamond on its ring in this orientation (geometry of the marks;
	## the answer itself is only ever checked by Story.solve_puzzle).
	func rotation_fits(steps: int) -> bool:
		if pairs.is_empty():
			return false
		var r0 := Rect2(plan_origin() + Vector2(b_origin) * cp(), Vector2(trace_cells) * cp())
		var c0 := r0.position + r0.size * 0.5
		var first := Vector2.INF
		for p in pairs:
			var d := c0 + (r0.position + Vector2(p["diamond"]) * cp() - c0).rotated(steps * PI * 0.5)
			var delta := plan_point(rings[int(p["ring"])]["cell"]) - d
			if first == Vector2.INF:
				first = delta
			elif first.distance_to(delta) > 1.5:
				return false
		return true

	func set_state(rot: int, off: Vector2i) -> void:
		rotation_steps = posmod(rot, 4)
		offset = Vector2i(clampi(off.x, off_min.x, off_max.x), clampi(off.y, off_min.y, off_max.y))
		var n := _count_aligned()
		var grew := n > _aligned
		_aligned = n
		queue_redraw()
		changed.emit()
		if grew:
			aligned_changed.emit(n)

	func _draw() -> void:
		var c := cp()
		var full := Rect2(Vector2.ZERO, size)
		draw_rect(full, FRAME)
		var glass := full.grow(-6.0)
		draw_rect(glass, GLASS)
		for k in 5:                                   # warm light from behind the glass, banded
			var g := glass.grow(-(k + 1) * glass.size.y * 0.075)
			draw_rect(g, Color(GLASS_L.r, GLASS_L.g, GLASS_L.b, 0.16 + 0.06 * k))
		for x in range(1, board_cells.x):
			draw_rect(Rect2(x * c, 6, P, size.y - 12), GRID_MAJOR if (x - plan_at.x) % 4 == 0 else GRID)
		for y in range(1, board_cells.y):
			draw_rect(Rect2(6, y * c, size.x - 12, P), GRID_MAJOR if (y - plan_at.y) % 4 == 0 else GRID)
		# the plan + its words (HD, fixed type like a document)
		if tex_plan != null:
			var rp := Rect2(plan_origin(), tex_plan.get_size() * P)
			draw_rect(Rect2(rp.position + Vector2(9, 9), rp.size), Color(0, 0, 0, 0.38))
			draw_texture_rect(tex_plan, rp, false)
		var font := get_theme_font("font", "TypeLabel")
		if font == null:
			font = ThemeDB.fallback_font
		for i in rings.size():
			var rp2 := ring_point(i) + Vector2(24, -18)
			draw_string(font, rp2, str(rings[i]["label"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, INK)
		for tl in title_lines:
			var r: Rect2 = tl["rect"]
			var pos := plan_origin() + (r.position + Vector2(0, r.size.y - 3)) * P
			draw_string(font, pos, str(tl["text"]), HORIZONTAL_ALIGNMENT_LEFT, r.size.x * P, 15, INK)
		# the tracing paper
		if tex_trace != null:
			var rb := trace_rect()
			var ct := trace_center()
			draw_set_transform(ct + Vector2(7, 7), angle(), Vector2.ONE)
			draw_rect(Rect2(rb.position - ct, rb.size), Color(0, 0, 0, 0.16))
			draw_set_transform(ct, angle(), Vector2.ONE)
			draw_texture_rect(tex_trace, Rect2(rb.position - ct, rb.size), false)
			if (hover or _dragging) and not locked:
				draw_rect(Rect2(rb.position - ct, rb.size).grow(3), Color(0.94, 0.77, 0.53, 0.85), false, 3.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		# a diamond on its ring: corner brackets (shape cue)
		if tex_snap != null and not locked:
			for i in pairs.size():
				if pair_aligned(i):
					var sp := ring_point(int(pairs[i]["ring"]))
					draw_texture_rect(tex_snap, Rect2(sp - tex_snap.get_size() * P * 0.5, tex_snap.get_size() * P), false)
		# success: the red pencil, pair by pair, then the signature
		for i in mini(matches_shown, pairs.size()):
			var mp := ring_point(int(pairs[i]["ring"]))
			if tex_match != null:
				draw_texture_rect(tex_match, Rect2(mp - tex_match.get_size() * P * 0.5, tex_match.get_size() * P), false)
			var lp := mp + Vector2(66, 6)
			if lp.x > size.x - 170:
				lp = mp + Vector2(-230, 6)
			draw_rect(Rect2(lp + Vector2(-6, -21), Vector2(176, 30)), Color(0.96, 0.94, 0.85, 0.9))
			draw_string(font, lp, str(pairs[i]["label"]), HORIZONTAL_ALIGNMENT_LEFT, 168, 20, PENCIL_HC if hc else PENCIL)
		if sign_shown and tex_underline != null and title_lines.size() >= 3:
			var r3: Rect2 = title_lines[2]["rect"]
			var up := plan_origin() + Vector2(r3.position.x - 1, r3.end.y - 2) * P
			draw_texture_rect(tex_underline, Rect2(up, tex_underline.get_size() * P), false)

	func _gui_input(event: InputEvent) -> void:
		if locked or tex_trace == null:
			return
		if event is InputEventMouseButton:
			var mb := event as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_LEFT:
				if mb.pressed and hit_trace(mb.position):
					_dragging = true
					_drag_from = mb.position
					_drag_offset = offset
					drag_started.emit()
					accept_event()
				elif not mb.pressed and _dragging:
					_dragging = false
					queue_redraw()
					accept_event()
			elif mb.pressed and mb.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN, MOUSE_BUTTON_RIGHT]:
				turn_requested.emit(-1 if mb.button_index == MOUSE_BUTTON_WHEEL_UP else 1)
				accept_event()
		elif event is InputEventMouseMotion:
			var mm := event as InputEventMouseMotion
			var over := hit_trace(mm.position)
			if over != hover:
				hover = over
				queue_redraw()
			mouse_default_cursor_shape = Control.CURSOR_MOVE if (_dragging or over) else Control.CURSOR_ARROW
			if _dragging:
				drag_to(mm.position)
				accept_event()

	## Drag (mouse): the paper follows in whole cells from where the drag started.
	func drag_to(p: Vector2) -> void:
		var d := (p - _drag_from) / cp()
		var n := _drag_offset + Vector2i(roundi(d.x), roundi(d.y))
		if n != offset:
			set_state(rotation_steps, n)
			UIKit.ui_sound("tick")

	func begin_drag(p: Vector2) -> bool:
		if locked or not hit_trace(p):
			return false
		_dragging = true
		_drag_from = p
		_drag_offset = offset
		drag_started.emit()
		return true

	func end_drag() -> void:
		_dragging = false
		queue_redraw()

	func hit_trace(p: Vector2) -> bool:
		var c := trace_center()
		var local := (p - c).rotated(-angle()) + c
		return trace_rect().grow(6).has_point(local)


var suppress_toasts := true
var obj_id := ""
## Earlier poses (Backspace / pad Y take back the last move).
var history: Array = []
var solved_count := 0

var _puzzle: Dictionary = {}
var _layout: Dictionary = {}
var _start := {"rotation_steps": 0, "offset_x": 0, "offset_y": 0}
var _fails := 0
var _done := false
var _solved_at := 0
var _beat_token := 0
var _board: RouteBoard
var _panel: PanelContainer
var _root_box: VBoxContainer
var _side: VBoxContainer
var _instr: Label
var _legend_labels: Array[Label] = []
var _legend_rows: Array[Control] = []
var _state_label: Label
var _aligned_label: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _success_box: PanelContainer
var _success_label: Label
var _tip: Label
var _rotate_btn: Button
var _reset_btn: Button
var _check_btn: Button
var _close_btn: Button
var _controls: Control


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	var lay = Kit.json(LAYOUT)
	_layout = lay if lay is Dictionary else {}
	add_child(Kit.dimmer(0.82))
	_panel = Kit.panel()
	Kit.full_rect(_panel)
	_panel.offset_left = 28
	_panel.offset_right = -28
	_panel.offset_top = 10
	_panel.offset_bottom = -10
	add_child(_panel)
	_root_box = Kit.vbox(0)
	_panel.add_child(_root_box)
	var head := Kit.hbox(28)
	_root_box.add_child(head)
	head.add_child(Kit.label(Kit.t("ui.c4.routes.title"), "HeadingLabel"))
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	push.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(push)
	var sub := Kit.label(Kit.t("ui.c4.routes.subtitle"), "DimLabel")
	sub.size_flags_vertical = Control.SIZE_SHRINK_END
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(sub)
	_root_box.add_child(HSeparator.new())
	_root_box.add_child(_gap(10))
	var row := Kit.hbox(32)
	row.name = "Content"
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root_box.add_child(row)
	var left := Kit.vbox(14)
	left.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(left)
	_board = RouteBoard.new()
	_board.name = "Board"
	_board.changed.connect(_on_board_changed)
	_board.aligned_changed.connect(func(_n: int) -> void: Kit.ui_sound("snap"))
	_board.drag_started.connect(_push_history)
	_board.turn_requested.connect(func(steps: int) -> void: rotate(steps))
	_board.tooltip_text = Kit.t("ui.c4.routes.board_tip")
	left.add_child(_board)
	var actions := Kit.hbox(16)
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(actions)
	_rotate_btn = Kit.button(Kit.t("ui.c4.routes.btn.rotate"), "", 200)
	_rotate_btn.pressed.connect(func() -> void: rotate(1))
	_reset_btn = Kit.button(Kit.t("ui.c4.routes.btn.reset"), "", 200)
	_reset_btn.pressed.connect(func() -> void: reset_pose())
	_check_btn = Kit.button(Kit.t("ui.c4.routes.btn.check"), "", 200)
	_check_btn.pressed.connect(func() -> void: submit())
	_close_btn = Kit.button(Kit.t("ui.c4.routes.btn.close"), "", 200)
	_close_btn.pressed.connect(close)
	for b in [_rotate_btn, _reset_btn, _check_btn, _close_btn]:
		actions.add_child(b)
	_side = Kit.vbox(14)
	_side.name = "Side"
	_side.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(_side)
	_build_side(_side)
	_root_box.add_child(_gap(8))
	_controls = Kit.controls_row([
		["%s|%s|%s|%s" % [Kit.t("ui.key.left"), Kit.t("ui.key.right"), Kit.t("ui.key.up"), Kit.t("ui.key.down")],
			Kit.t("ui.c4.routes.hint_move")],
		["R", Kit.t("ui.c4.routes.hint_rotate")], [Kit.t("ui.key.mouse"), Kit.t("ui.c4.routes.hint_drag")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.c4.routes.hint_undo")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.c4.routes.hint_check")], [Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]])
	_controls.tooltip_text = Kit.t("ui.c4.routes.controls")
	_controls.mouse_filter = Control.MOUSE_FILTER_PASS
	_root_box.add_child(_controls)
	_load_layout()
	_refresh()
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)


func _gap(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _build_side(v: VBoxContainer) -> void:
	_instr = Kit.wrap_label(Kit.t("ui.c4.routes.instruction"), "BodyLabel")
	_instr.name = "Instruction"
	Kit.scalable(_instr, 26)
	v.add_child(_instr)
	var plan_tex := Kit.optional_tex(DOCS + "berlin_c4_routes_plan.png")
	var trace_tex := Kit.optional_tex(DOCS + "berlin_c4_routes_trace.png")
	for leg in [["ring", "ui.c4.routes.legend.shaft"], ["diamond", "ui.c4.routes.legend.loop"]]:
		var lr := Kit.hbox(18)
		var chip := Kit.panel("PaperCardPanel")
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var icon := TextureRect.new()
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.stretch_mode = TextureRect.STRETCH_SCALE
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.custom_minimum_size = Vector2(51, 51)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var at := AtlasTexture.new()
		if leg[0] == "ring" and plan_tex != null:
			at.atlas = plan_tex
			at.region = Rect2(_legend_ring_px() - Vector2(8, 8), Vector2(17, 17))
		elif trace_tex != null:
			at.atlas = trace_tex
			at.region = Rect2(_legend_diamond_px() - Vector2(8, 8), Vector2(17, 17))
		icon.texture = at if at.atlas != null else null
		chip.add_child(icon)
		lr.add_child(chip)
		var ll := Kit.wrap_label(Kit.t(leg[1]), "BodyLabel")
		Kit.scalable(ll, 24)
		ll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ll.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		lr.add_child(ll)
		v.add_child(lr)
		_legend_labels.append(ll)
		_legend_rows.append(lr)
	var sep := HSeparator.new()
	sep.theme_type_variation = "FaintSeparator"
	v.add_child(sep)
	_state_label = Kit.label("", "KickerLabel")
	_state_label.name = "State"
	v.add_child(_state_label)
	_aligned_label = Kit.label("", "BodyLabel")
	_aligned_label.name = "Aligned"
	Kit.scalable(_aligned_label, 24)
	v.add_child(_aligned_label)
	_feedback = Kit.wrap_label("", "BodyLabel")
	_feedback.name = "Feedback"
	_feedback.visible = false
	Kit.scalable(_feedback, 24)
	v.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	_hint_box.name = "Hint"
	var hh := Kit.hbox(14)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hh.add_child(hic)
	_hint_label = Kit.wrap_label(Kit.t("ui.c4.routes.hint"), "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 22)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	v.add_child(_hint_box)
	_tip = Kit.wrap_label("", "ControlHintLabel")
	_tip.name = "Tip"
	v.add_child(_tip)
	_success_box = Kit.panel("PaperCardPanel")
	_success_box.name = "Success"
	_success_box.add_theme_stylebox_override("panel", _paper_box())
	var sv := Kit.vbox(10)
	_success_box.add_child(sv)
	var stamp := _make_stamp(Kit.t("ui.c4.routes.stamp").to_upper().replace("ß", "SS"))
	stamp.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	sv.add_child(stamp)
	_success_label = Kit.wrap_label(Kit.t("ui.c4.routes.success"), "TypeLabel")
	_success_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_success_label, 22)
	sv.add_child(_success_label)
	_success_box.visible = false
	v.add_child(_success_box)


func _legend_ring_px() -> Vector2:
	var rings = _layout.get("plan", {}).get("rings", []) if _layout.get("plan") is Dictionary else []
	var cell := float(_layout.get("cell_px", 16))
	if rings is Array and not rings.is_empty():
		var c: Array = rings[0]["cell"]
		return Vector2((float(c[0]) + 0.5) * cell - 0.5, (float(c[1]) + 0.5) * cell - 0.5).round()
	return Vector2(152, 24)


func _legend_diamond_px() -> Vector2:
	var loops = _layout.get("trace", {}).get("loops", []) if _layout.get("trace") is Dictionary else []
	var cell := float(_layout.get("cell_px", 16))
	if loops is Array and not loops.is_empty():
		var d: Array = loops[0]["diamond"]
		return Vector2((float(d[0]) + 0.5) * cell - 0.5, (float(d[1]) + 0.5) * cell - 0.5).round()
	return Vector2(24, 24)


func _paper_box() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/paper.png")
	for side in 4:
		st.set_texture_margin(side, 21)
	st.set_content_margin(SIDE_LEFT, 26)
	st.set_content_margin(SIDE_RIGHT, 26)
	st.set_content_margin(SIDE_TOP, 16)
	st.set_content_margin(SIDE_BOTTOM, 18)
	return st


func _make_stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(252, 78)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_evidence.png")
	frame.size = Vector2(252, 78)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 27)
	var f := l.get_theme_font("font")
	if f != null:
		var fs := 27
		while fs > 16 and f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > 214.0:
			fs -= 1
		l.add_theme_font_size_override("font_size", fs)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(252, 78)
	l.pivot_offset = Vector2(126, 39)
	l.rotation = deg_to_rad(-3.0)
	l.modulate = Color(1, 1, 1, 0.92)
	c.add_child(l)
	return c


func _v2i(v, fallback := Vector2i.ZERO) -> Vector2i:
	if v is Array and v.size() >= 2:
		return Vector2i(int(v[0]), int(v[1]))
	return fallback


## Reads berlin_c4_routes.json (cells, files, rings, diamonds, start, board) into the light table.
func _load_layout() -> void:
	var b := _board
	b.cell = int(_layout.get("cell_px", 16))
	b.board_cells = _v2i(_layout.get("board_cells"), Vector2i(18, 14))
	b.plan_at = _v2i(_layout.get("plan_at"), Vector2i(2, 2))
	b.b_origin = _v2i(_layout.get("b_origin"), Vector2i(-1, 3))
	var plan: Dictionary = _layout.get("plan", {}) if _layout.get("plan") is Dictionary else {}
	var trace: Dictionary = _layout.get("trace", {}) if _layout.get("trace") is Dictionary else {}
	var marks: Dictionary = _layout.get("marks", {}) if _layout.get("marks") is Dictionary else {}
	b.plan_cells = _v2i(plan.get("cells"), Vector2i(14, 10))
	b.trace_cells = _v2i(trace.get("cells"), Vector2i(10, 8))
	b.tex_plan = Kit.optional_tex(DOCS + str(plan.get("file", "berlin_c4_routes_plan.png")))
	b.tex_trace = Kit.optional_tex(DOCS + str(trace.get("file", "berlin_c4_routes_trace.png")))
	b.tex_snap = Kit.optional_tex(ART + str(marks.get("snap", "c4_route_snap.png")))
	b.tex_match = Kit.optional_tex(ART + str(marks.get("match", "c4_route_match.png")))
	b.tex_underline = Kit.optional_tex(ART + str(marks.get("underline", "c4_route_underline.png")))
	b.rings.clear()
	var ids: Array = []
	for r in plan.get("rings", []):
		var c: Array = r["cell"]
		b.rings.append({"id": str(r["id"]), "cell": Vector2(float(c[0]) + 0.5, float(c[1]) + 0.5),
			"label": Kit.t(str(r.get("label_key", "")))})
		ids.append(str(r["id"]))
	b.pairs.clear()
	var lm_keys := {}
	for lm in _layout.get("landmarks", []):
		lm_keys[str(lm.get("name", ""))] = str(lm.get("match_key", ""))
	for lp in trace.get("loops", []):
		var d: Array = lp["diamond"]
		var ri := ids.find(str(lp.get("pairs_with", "")))
		if ri < 0:
			continue
		var key := str(lm_keys.get("%s_%s" % [lp["pairs_with"], lp["id"]], ""))
		b.pairs.append({"ring": ri, "diamond": Vector2(float(d[0]) + 0.5, float(d[1]) + 0.5),
			"label": Kit.t(key) if key != "" else str(lp["id"])})
	b.title_lines.clear()
	var keys: Array = plan.get("title_keys", [])
	var lines: Array = plan.get("title_lines", [])
	for i in mini(keys.size(), lines.size()):
		var ln: Array = lines[i]
		b.title_lines.append({"rect": Rect2(float(ln[0]), float(ln[1]), float(ln[2]), float(ln[3])), "text": Kit.t(str(keys[i]))})
	var st = _layout.get("start", {})
	if st is Dictionary and not st.is_empty():
		_start = {"rotation_steps": int(st.get("rotation_steps", 0)), "offset_x": int(st.get("offset_x", 0)),
			"offset_y": int(st.get("offset_y", 0))}
	b.setup()


# ================================================================ open / state
func open(id: String) -> void:
	obj_id = id
	var p = Kit.call_svc("Story", "puzzle_for", [id], null)
	_puzzle = p if p is Dictionary and not p.is_empty() else Kit.puzzle_for_objective(id)
	_fails = 0
	_done = false
	_beat_token += 1
	history.clear()
	_board.locked = false
	_board.matches_shown = 0
	_board.sign_shown = false
	_close_btn.text = Kit.t("ui.c4.routes.btn.close")
	_set_feedback("")
	_board.set_state(int(_start["rotation_steps"]), Vector2i(int(_start["offset_x"]), int(_start["offset_y"])))
	_refresh()
	open_modal()


## The pose the player would submit now.
func pose() -> Dictionary:
	return {"rotation_steps": int(_board.rotation_steps), "offset_x": int(_board.offset.x), "offset_y": int(_board.offset.y)}


func is_done() -> bool:
	return _done


func aligned() -> int:
	return _board.aligned_count()


func matches_shown() -> int:
	return _board.matches_shown


func sign_shown() -> bool:
	return _board.sign_shown


func feedback_text() -> String:
	return _feedback.text if _feedback != null and _feedback.visible else ""


func hint_shown() -> bool:
	return _hint_box != null and _hint_box.visible


func success_shown() -> bool:
	return _success_box != null and _success_box.visible


func tip_text() -> String:
	return _tip.text if _tip != null and _tip.visible else ""


# ================================================================ actions
func _push_history() -> void:
	history.append(pose())
	if history.size() > HISTORY_MAX:
		history.pop_front()


## One cell (arrows / WASD / D-pad / stick).  False when locked or at the edge.
func move(d: Vector2i) -> bool:
	if _done:
		return false
	var before := pose()
	var target := _board.offset + d
	_board.set_state(_board.rotation_steps, target)
	if pose() == before:
		return false
	history.append(before)
	if history.size() > HISTORY_MAX:
		history.pop_front()
	Kit.ui_sound("tick")
	return true


## A quarter turn clockwise (+1) or back (−1) around the paper's centre.
func rotate(steps: int) -> bool:
	if _done or steps == 0:
		return false
	_push_history()
	_board.set_state(_board.rotation_steps + steps, _board.offset)
	Kit.ui_sound("move")
	return true


## Backspace / pad Y: the pose before the last move.
func undo() -> bool:
	if _done or history.is_empty():
		return false
	var p: Dictionary = history.pop_back()
	_board.set_state(int(p["rotation_steps"]), Vector2i(int(p["offset_x"]), int(p["offset_y"])))
	Kit.ui_sound("back")
	return true


## „Zurücksetzen“ / pad X: the paper back to where Konrad laid it first.
func reset_pose() -> bool:
	if _done:
		return false
	var s := {"rotation_steps": int(_start["rotation_steps"]), "offset_x": int(_start["offset_x"]), "offset_y": int(_start["offset_y"])}
	if pose() == s:
		return false
	_push_history()
	_board.set_state(s["rotation_steps"], Vector2i(s["offset_x"], s["offset_y"]))
	Kit.ui_sound("page")
	return true


func _on_board_changed() -> void:
	if not _done:
		_set_feedback("")
	_refresh()


## Enter / pad A / „Abgleichen“. Returns the engine result.
func submit() -> Dictionary:
	if _done:
		return {}
	var answer := pose()
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	if r == null or not ok:
		_set_feedback(Kit.t("ui.c4.routes.error", {"error": _error_text(r)}))
		Kit.ui_sound("fail")
		return r if r is Dictionary else {"ok": false, "error": "no Story service"}
	var is_solved: bool = bool(r) if r is bool else bool((r as Dictionary).get("solved", false))
	if is_solved:
		_on_solved()
	else:
		_fails += 1
		Kit.ui_sound("fail")
		_set_feedback(Kit.t("ui.c4.routes.wrong" if _board.rotation_fits(_board.rotation_steps) else "ui.c4.routes.wrong_turned"))
		_nudge()
		_refresh()
	return r if r is Dictionary else {"ok": true, "solved": is_solved}


func _error_text(r) -> String:
	if r is Dictionary:
		var k := str(r.get("error_key", ""))
		if k != "" and Kit.has_key(k):
			return Kit.t(k)
		var e := str(r.get("error", ""))
		if e != "":
			return e
	return Kit.t("ui.common.unavailable")


func _on_solved() -> void:
	_done = true
	_board.locked = true
	_board.end_drag()
	_solved_at = Time.get_ticks_msec()
	_set_feedback("")
	_refresh()
	Kit.ui_sound("snap")
	if not Kit.reduced_motion():
		Kit.appear(_success_box, 0.22)
	_close_btn.text = Kit.t("ui.c4.routes.btn.continue")
	_close_btn.grab_focus.call_deferred()
	solved_count += 1
	solved.emit(obj_id)
	_beat_token += 1
	var token := _beat_token
	if Kit.reduced_motion() or not is_inside_tree():
		for i in _board.pairs.size():
			_reveal_match(i, token)
		_reveal_sign(token)
	else:
		for i in _board.pairs.size():
			get_tree().create_timer(0.3 + MATCH_STEP * i, true).timeout.connect(_reveal_match.bind(i, token), CONNECT_ONE_SHOT)
		get_tree().create_timer(0.45 + MATCH_STEP * _board.pairs.size(), true).timeout.connect(_reveal_sign.bind(token), CONNECT_ONE_SHOT)
	if is_inside_tree():
		get_tree().create_timer(success_beat(), true).timeout.connect(_on_beat.bind(token), CONNECT_ONE_SHOT)


func _reveal_match(i: int, token: int) -> void:
	if token != _beat_token or not _done:
		return
	_board.matches_shown = maxi(_board.matches_shown, i + 1)
	_board.queue_redraw()
	Kit.ui_sound("tick")


func _reveal_sign(token: int) -> void:
	if token != _beat_token or not _done:
		return
	_board.sign_shown = true
	_board.queue_redraw()
	Kit.ui_sound("stamp_thud")


## Seconds the solved modal stays open by itself (≤ SUCCESS_BEAT_MAX); any confirm closes it earlier.
func success_beat() -> float:
	return clampf(2.0 + Kit.t("ui.c4.routes.success").length() * 0.03, 3.0, SUCCESS_BEAT_MAX)


func _on_beat(token: int) -> void:
	if token == _beat_token and _done and is_open:
		close()


func _set_feedback(text: String) -> void:
	if _feedback == null:
		return
	_feedback.text = text
	_feedback.visible = text != ""
	if _tip != null:
		_refresh()


func _nudge() -> void:
	if Kit.reduced_motion() or _board == null or not _board.is_inside_tree():
		return
	var base := _board.position.x
	var tw := _board.create_tween()
	for dx in [6, -6, 3, 0]:
		tw.tween_property(_board, "position:x", base + float(dx), 0.05)


func _hint_visible() -> bool:
	if _done:
		return false
	var mode := int(Kit.setting("puzzle_hints", 1))
	if mode <= 0:
		return false
	if mode >= 2:
		return true
	var r = Kit.call_svc("Story", "puzzle_hint_available", [obj_id], null)
	if r is bool:
		return r
	if r is Dictionary:
		return bool(r.get("available", r.get("hint", false)))
	return _fails >= int(_puzzle.get("hint_after_attempts", 2))


func _refresh() -> void:
	if _board == null or _state_label == null:
		return
	var hc := Kit.high_contrast()
	if _board.hc != hc:
		_board.hc = hc
		_board.queue_redraw()
	var off := _board.offset
	_state_label.text = Kit.t("ui.c4.routes.state", {"rot": _board.rotation_steps * 90, "x": "%+d" % off.x,
		"y": "%+d" % off.y})
	_state_label.add_theme_color_override("font_color", Kit.C_TEXT if hc else Kit.C_TEXT_DIM)
	var n := _board.aligned_count()
	_aligned_label.text = Kit.t("ui.c4.routes.aligned", {"n": n, "total": _board.pairs.size()})
	_aligned_label.add_theme_color_override("font_color", Kit.C_AMBER if n > 0 else (Kit.C_TEXT if hc else Kit.C_TEXT_DIM))
	_rotate_btn.disabled = _done
	_reset_btn.disabled = _done
	_check_btn.disabled = _done
	_hint_box.visible = _hint_visible()
	_success_box.visible = _done
	_tip.text = Kit.t("ui.c4.routes.tip_pad" if Kit.last_input_pad else "ui.c4.routes.tip_mouse")
	var wide := Kit.text_scale() > 1.1
	var busy := _feedback.visible or _hint_box.visible
	_tip.visible = not _done and not (wide and busy)
	_instr.visible = not (wide and (busy or _done))      # 125 % / 150 %: notes and hint get the room
	for r in _legend_rows:
		r.visible = not (wide and _done)


func _on_setting_changed(key: String, _value) -> void:
	if key in ["text_scale", "high_contrast"]:
		_refresh()


func focus_default() -> void:
	if _done:
		_close_btn.grab_focus()
	else:
		_check_btn.grab_focus()


func _on_open() -> void:
	Kit.ui_sound("paper")
	_refresh()


func _on_close() -> void:
	_beat_token += 1
	_board.end_drag()


# ================================================================ input (called by UIRoot before the GUI)
const DIRS := {"ui_left": Vector2i.LEFT, "ui_right": Vector2i.RIGHT, "ui_up": Vector2i.UP, "ui_down": Vector2i.DOWN}


func modal_input(event: InputEvent) -> bool:
	if _done:
		return _done_input(event)
	if event is InputEventJoypadButton:
		return _pad_input(event as InputEventJoypadButton)
	if event is InputEventJoypadMotion:
		for a in DIRS:
			if InputMap.has_action(a) and event.is_action_pressed(a):
				move(DIRS[a])
				return true
		return false
	if not (event is InputEventKey) or not event.pressed:
		return false
	var ke := event as InputEventKey
	if ke.ctrl_pressed or ke.alt_pressed or ke.meta_pressed:
		return false
	var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
	match k:
		KEY_LEFT, KEY_A:
			move(Vector2i.LEFT)
			return true
		KEY_RIGHT, KEY_D:
			move(Vector2i.RIGHT)
			return true
		KEY_UP, KEY_W:
			move(Vector2i.UP)
			return true
		KEY_DOWN, KEY_S:
			move(Vector2i.DOWN)
			return true
		KEY_R:
			if not ke.echo:
				rotate(-1 if ke.shift_pressed else 1)
			return true
		KEY_BACKSPACE:              # also bound to "cancel": consume it before UIRoot closes the modal
			if not ke.echo:
				undo()
			return true
		KEY_ENTER, KEY_KP_ENTER:
			if ke.echo:
				return true
			var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
			if f != null and f in [_rotate_btn, _reset_btn, _close_btn]:
				return false            # Enter on another action button presses that button
			submit()
			return true
	return false


## Controller (C4_DESIGN §2.7): D-pad moves, RB/LB turn, A checks, X start pose, Y takes back the last move,
## Back closes; B is left to UIRoot (cancel -> handle_cancel -> close).
func _pad_input(jb: InputEventJoypadButton) -> bool:
	var mine := [JOY_BUTTON_A, JOY_BUTTON_X, JOY_BUTTON_Y, JOY_BUTTON_BACK, JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT,
		JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER]
	if not jb.pressed:
		return jb.button_index in mine
	match jb.button_index:
		JOY_BUTTON_DPAD_LEFT:
			move(Vector2i.LEFT)
		JOY_BUTTON_DPAD_RIGHT:
			move(Vector2i.RIGHT)
		JOY_BUTTON_DPAD_UP:
			move(Vector2i.UP)
		JOY_BUTTON_DPAD_DOWN:
			move(Vector2i.DOWN)
		JOY_BUTTON_RIGHT_SHOULDER:
			rotate(1)
		JOY_BUTTON_LEFT_SHOULDER:
			rotate(-1)
		JOY_BUTTON_A:
			submit()
		JOY_BUTTON_X:
			reset_pose()
		JOY_BUTTON_Y:
			undo()
		JOY_BUTTON_BACK:
			Kit.ui_sound("back")
			close()
		_:
			return false
	return true


## After success: confirm / cancel (after a short guard) closes; everything else is swallowed.
func _done_input(event: InputEvent) -> bool:
	var confirm := false
	if event is InputEventKey and event.pressed and not event.echo:
		var ke := event as InputEventKey
		var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
		confirm = k in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_ESCAPE, KEY_BACKSPACE]
	elif event is InputEventJoypadButton and event.pressed:
		confirm = (event as InputEventJoypadButton).button_index in [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_BACK]
	elif event is InputEventMouseButton:
		return false                    # the „Weiter“ button stays clickable
	if not confirm:
		return event is InputEventKey or event is InputEventJoypadButton
	if Time.get_ticks_msec() - _solved_at >= SUCCESS_GUARD_MS and is_open:
		close()
	return true


func handle_cancel() -> bool:
	if _done and Time.get_ticks_msec() - _solved_at < SUCCESS_GUARD_MS:
		return true
	return super.handle_cancel()


# ================================================================ accessibility report (tests)
## Text colour / background pairs this puzzle draws itself (checked by tests/test_c4_puzzle_ui.gd).
func contrast_pairs() -> Array:
	var hc := Kit.high_contrast()
	var surf: Dictionary = _layout.get("surfaces", {}) if _layout.get("surfaces") is Dictionary else {}
	var paper := Color(str(surf.get("paper", "#F5EFDA")))
	return [
		{"what": "plan words (shaft labels, title block)", "fg": RouteBoard.INK, "bg": paper},
		{"what": "red pencil labels after the solution", "fg": RouteBoard.PENCIL_HC if hc else RouteBoard.PENCIL,
			"bg": Color(0.96, 0.94, 0.85)},
		{"what": "pose line", "fg": Kit.C_TEXT if hc else Kit.C_TEXT_DIM, "bg": Kit.C_NAVY},
		{"what": "aligned count", "fg": Kit.C_AMBER, "bg": Kit.C_NAVY},
	]
