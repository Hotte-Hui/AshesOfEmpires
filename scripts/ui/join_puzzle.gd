extends "res://scripts/ui/ui_modal.gd"
## „Die Hälften“ (pz_c4_halves / objective c4g_solve_halves, documentation/C4P2_DESIGN.md §2.7) — Alexei at the
## table of the sand house in the Karsk depot, under the hanging lamp.  On the table: the Russian half of card
## No. 0417, borrowed for one hour from Lev's box „С-17/45 ПРИНЯТЬ“ (five notches on its left edge, the right half
## of the round stamp „C-17“ in Cyrillic letters).  On the open guidebook lies the German half from Berlin, upside
## down as Konrad laid it in (five teeth, the left half of the stamp in German letters, the ruled lines of the
## form).  The player turns and moves the German half until tooth meets notch, line meets line and the stamp
## closes into a circle — Konrad's mechanic of Chapter 2 in Alexei's hands.
## Geometry and art: assets/ui/documents/karsk_c4p2_halves.json + karsk_c4p2_halves_{de,ru}.png and
## assets/ui/puzzle/c4p2_halves_*.png (tools/pixelgen/gen_ui_c4p2.py paints the card whole and cuts it, and
## verifies that exactly one pose joins it and that no other pose joins even one tooth).
##
## Registered by data/chapters/c4p2.json (puzzles.c4g_solve_halves); ChapterExt.puzzle_ui instances this scene once
## under UIRoot, sets `ui_root`, Game calls open(obj_id) and awaits `closed`.  Works stand-alone (tests) as well.
##
## Key contract (= RoutePuzzle / BlueprintPuzzle; scripts/core/inputplay.gd relies on it): property `is_open`;
## arrows / WASD move the half one cell (RIGHT = offset_x + 1, DOWN = offset_y + 1), R turns it +90°
## (rotation_steps + 1 mod 4), Shift+R −90°, Backspace takes back the last move (consumed before UIRoot's cancel),
## Enter („Anlegen“) submits {rotation_steps, offset_x, offset_y} (ints) through Story.solve_puzzle unless the GUI
## focus is on another action button (then Enter presses that button; the modal opens with the focus on „Anlegen“),
## Esc closes.  Pad: D-pad / left stick move, RB/LB turn, A checks, X back to the start pose, Y takes back the last
## move, Back/Select closes; B is left to UIRoot (cancel -> close).  Mouse: drag the half (snaps to the cells),
## wheel or right-click turns it, buttons Drehen · Zurücksetzen · Anlegen · Schließen.
## Wrong answers cost nothing (the half stays where it is): `ui.c4p2.halves.wrong_turned` while the teeth point
## away from the notches (the writing upside down), `ui.c4p2.halves.wrong_sideways` while they point up or down,
## else `ui.c4p2.halves.wrong` — derived from the marks' geometry, never from the answer.  Marks are shape-coded
## (teeth = triangles, notches = cut-outs, stamp halves = semicircles, line ends = ticks); a tooth that sits in its
## notch gets amber corner brackets and the side panel counts them.  Success: the teeth click in one by one, the
## stamp closes into a circle, Ekdahl takes two photographs (two soft flashes; none with reduced motion), stamp +
## text, `solved(obj_id)` once, the modal closes after a reading beat (≤ SUCCESS_BEAT_MAX) or on confirm.

signal solved(obj_id: String)

const PX := 3
const DOCS := "res://assets/ui/documents/"
const ART := "res://assets/ui/puzzle/"
const LAYOUT := "res://assets/ui/documents/karsk_c4p2_halves.json"
const SUCCESS_GUARD_MS := 600
const SUCCESS_BEAT_MAX := 7.0
const CLICK_STEP := 0.14
const HISTORY_MAX := 64


## The sand-house table: the Russian half (fixed), the German half (turned in quarter steps around its centre,
## moved in whole cells), alignment brackets and the success beat (clicks, the closed stamp, two flashes).
class JoinBoard extends Control:
	signal changed
	signal joined_changed(teeth: int)
	signal drag_started
	signal turn_requested(steps: int)

	const UIKit := preload("res://scripts/ui/ui_kit.gd")
	const P := 3
	const FRAME := Color("120c08")
	const DOT := Color(1.0, 0.9, 0.7, 0.09)
	const DOT_HC := Color(1.0, 0.95, 0.8, 0.24)
	const SHADOW := Color(0, 0, 0, 0.36)
	const HOVER := Color(0.94, 0.77, 0.53, 0.85)
	const HOVER_HC := Color(1.0, 1.0, 1.0, 0.95)

	var cell := 16
	var board_cells := Vector2i(20, 14)
	var base_at := Vector2i(12, 5)
	var over_at := Vector2i(1, 4)
	var half_cells := Vector2i(7, 5)
	var pad := 6
	## Art px between the German half's paper and the table's edge (the frame never cuts the paper or its writing).
	var edge_margin := 8.0
	var lamp := Vector2(214, 116)
	var rotation_steps := 0
	var offset := Vector2i.ZERO
	## The offset range of the CURRENT rotation (see off_range); kept for the tests and the clamp.
	var off_min := Vector2i(0, -3)
	var off_max := Vector2i(11, 4)
	var tex_table: Texture2D
	var tex_base: Texture2D
	var tex_over: Texture2D
	var tex_snap: Texture2D
	var tex_ring: Texture2D
	var tex_click: Texture2D
	## kind -> [{id, at: Vector2 (body art px), dir: Vector2i (inward normal)}]
	var base_marks := {}
	var over_marks := {}
	var pairs: Array = [["tooth", "notch"], ["stamp_half", "stamp_half"], ["line_end", "line_end"]]
	var locked := false
	var clicks_shown := 0
	var ring_shown := false
	## Camera flash over the table (0 … 0.4); setting it redraws.
	var flash := 0.0:
		set(v):
			flash = v
			queue_redraw()
	var hover := false
	var hc := false
	var _dragging := false
	var _drag_from := Vector2.ZERO
	var _drag_offset := Vector2i.ZERO
	var _teeth := 0

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
		var r := off_range(rotation_steps)
		off_min = r[0]
		off_max = r[1]
		_teeth = teeth_joined()
		queue_redraw()

	## [min, max] offsets that keep the WHOLE German half, turned by `steps`, on the table with edge_margin art px
	## to spare (round 10: the old centre-only limits let the frame cut through its writing).
	func off_range(steps: int) -> Array:
		var hx := half_cells.x * 0.5
		var hy := half_cells.y * 0.5
		if posmod(steps, 2) == 1:
			var t := hx
			hx = hy
			hy = t
		var m := edge_margin / float(cell)
		var c0 := Vector2(over_at) + Vector2(half_cells) * 0.5
		var lo := Vector2i(ceili(hx + m - c0.x - 0.000001), ceili(hy + m - c0.y - 0.000001))
		var hi := Vector2i(floori(board_cells.x - hx - m - c0.x + 0.000001), floori(board_cells.y - hy - m - c0.y + 0.000001))
		return [lo, hi]

	func cp() -> float:
		return float(cell * P)

	func body() -> Vector2:
		return Vector2(half_cells * cell)

	func angle() -> float:
		return rotation_steps * PI * 0.5

	func over_center(off := Vector2i(-9999, 0)) -> Vector2:
		var o := offset if off.x == -9999 else off
		return (Vector2(over_at + o) + Vector2(half_cells) * 0.5) * cp()

	## German half body px (as stored, continuous) -> board px for a pose (current pose by default).
	func over_point(local: Vector2, steps := -1, off := Vector2i(-9999, 0)) -> Vector2:
		var s := rotation_steps if steps < 0 else steps
		return over_center(off) + ((local - body() * 0.5) * P).rotated(s * PI * 0.5)

	func base_point(at: Vector2) -> Vector2:
		return Vector2(base_at) * cp() + at * P

	func _rot_dir(d: Vector2i, steps: int) -> Vector2i:
		var v := d
		for i in posmod(steps, 4):
			v = Vector2i(-v.y, v.x)
		return v

	func _partner(kind_b: String, id: String) -> Dictionary:
		for m in base_marks.get(kind_b, []):
			if str(m["id"]) == id:
				return m
		return {}

	## How many marks of each kind meet their partner in a pose.
	func joined_counts(steps := -1, off := Vector2i(-9999, 0)) -> Dictionary:
		var s := rotation_steps if steps < 0 else steps
		var out := {}
		for pr in pairs:
			var n := 0
			for mo in over_marks.get(pr[0], []):
				var mb := _partner(pr[1], str(mo["id"]))
				if mb.is_empty():
					continue
				var p := over_point(mo["at"], s, off)
				var q := base_point(mb["at"])
				if p.distance_to(q) < 1.5 and _rot_dir(mo["dir"], s) == -Vector2i(mb["dir"]):
					n += 1
			out[pr[0]] = n
		return out

	func tooth_joined(i: int) -> bool:
		var teeth: Array = over_marks.get("tooth", [])
		if i < 0 or i >= teeth.size():
			return false
		var mo: Dictionary = teeth[i]
		var mb := _partner("notch", str(mo["id"]))
		return not mb.is_empty() and over_point(mo["at"]).distance_to(base_point(mb["at"])) < 1.5 \
			and _rot_dir(mo["dir"], rotation_steps) == -Vector2i(mb["dir"])

	func teeth_joined() -> int:
		return int(joined_counts().get("tooth", 0))

	func stamp_closed() -> bool:
		return int(joined_counts().get("stamp_half", 0)) >= over_marks.get("stamp_half", []).size() \
			and not over_marks.get("stamp_half", []).is_empty()

	## Geometry only: can SOME offset put every tooth into its notch in this orientation?  (The answer itself
	## is only ever checked by Story.solve_puzzle.)
	func rotation_fits(steps: int) -> bool:
		var teeth: Array = over_marks.get("tooth", [])
		if teeth.is_empty():
			return false
		var first := Vector2.INF
		for mo in teeth:
			var mb := _partner("notch", str(mo["id"]))
			if mb.is_empty() or _rot_dir(mo["dir"], steps) != -Vector2i(mb["dir"]):
				return false
			var delta := base_point(mb["at"]) - over_point(mo["at"], steps, Vector2i.ZERO)
			if first == Vector2.INF:
				first = delta
			elif first.distance_to(delta) > 1.5:
				return false
		return true

	## True while the teeth point up or down (the writing stands sideways).
	func teeth_sideways(steps: int) -> bool:
		var teeth: Array = over_marks.get("tooth", [])
		if teeth.is_empty():
			return false
		return _rot_dir(teeth[0]["dir"], steps).x == 0

	func set_state(rot: int, off: Vector2i) -> void:
		rotation_steps = posmod(rot, 4)
		var r := off_range(rotation_steps)
		off_min = r[0]
		off_max = r[1]
		offset = Vector2i(clampi(off.x, off_min.x, off_max.x), clampi(off.y, off_min.y, off_max.y))
		var n := teeth_joined()
		var grew := n > _teeth
		_teeth = n
		queue_redraw()
		changed.emit()
		if grew:
			joined_changed.emit(n)

	## Light of the hanging lamp on the moving paper (same falloff as the table art).
	func _lamp_light(center_px: Vector2) -> Color:
		var a := center_px / P
		var d := Vector2((a.x - lamp.x) / 1.3, (a.y - lamp.y) * 1.05).length()
		var l := pow(clampf(1.0 - d / 190.0, 0.0, 1.0), 1.25)
		var f := clampf(0.5 + 0.62 * l, 0.5, 1.08)
		if hc:
			f = maxf(f, 0.92)
		return Color(f, f * 0.98, f * 0.92)

	func _draw() -> void:
		var c := cp()
		var full := Rect2(Vector2.ZERO, size)
		if tex_table != null:
			draw_texture_rect(tex_table, full, false)
		else:
			draw_rect(full, Color("2e1d12"))
		var dot := DOT_HC if hc else DOT
		for x in range(1, board_cells.x):
			for y in range(1, board_cells.y):
				draw_rect(Rect2(x * c - 1, y * c - 1, 3, 3), dot)
		# the German half's shadow falls on the TABLE while the halves lie side by side (both papers flat on the
		# wood: the seam and the stamp's „1“ stay clean); only a half lying ON the other casts its shadow onto it
		var ct := over_center()
		var bsz := body() * P
		var tr := Rect2(-bsz * 0.5 - Vector2(pad, pad) * P, bsz + Vector2(pad, pad) * 2.0 * P)
		var on_top := over_lies_on_base()
		if tex_over != null and not on_top:
			_draw_over_shadow(ct, tr)
		# the Russian half (fixed)
		if tex_base != null:
			var rb := Rect2(Vector2(base_at) * c, Vector2(tex_base.get_size()) * P)
			draw_texture_rect(tex_base, Rect2(rb.position + Vector2(6, 6), rb.size), false, SHADOW)
			draw_texture_rect(tex_base, rb, false, _lamp_light(rb.get_center()))
		# the German half (turned and moved)
		if tex_over != null:
			if on_top:
				_draw_over_shadow(ct, tr)
			draw_set_transform(ct, angle(), Vector2.ONE)
			draw_texture_rect(tex_over, tr, false, _lamp_light(ct))
			if (hover or _dragging) and not locked:
				draw_rect(Rect2(-bsz * 0.5, bsz).grow(4), HOVER_HC if hc else HOVER, false, 3.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		# a tooth in its notch: corner brackets (shape cue)
		if tex_snap != null and not locked:
			var teeth: Array = over_marks.get("tooth", [])
			for i in teeth.size():
				if tooth_joined(i):
					var q := base_point(_partner("notch", str(teeth[i]["id"]))["at"]) - Vector2(2, 0) * P
					draw_texture_rect(tex_snap, Rect2(q - Vector2(tex_snap.get_size()) * P * 0.5, Vector2(tex_snap.get_size()) * P), false)
		# success: the teeth click in, the stamp closes, two photographs
		if tex_click != null:
			var notches: Array = base_marks.get("notch", [])
			for i in mini(clicks_shown, notches.size()):
				var q2 := base_point(notches[i]["at"]) - Vector2(2, 0) * P
				draw_texture_rect(tex_click, Rect2(q2 - Vector2(tex_click.get_size()) * P * 0.5, Vector2(tex_click.get_size()) * P), false)
		if ring_shown and tex_ring != null and not base_marks.get("stamp_half", []).is_empty():
			var sc := base_point(base_marks["stamp_half"][0]["at"])
			draw_texture_rect(tex_ring, Rect2(sc - Vector2(tex_ring.get_size()) * P * 0.5, Vector2(tex_ring.get_size()) * P), false)
		if flash > 0.0:
			draw_rect(full, Color(1.0, 0.98, 0.94, clampf(flash, 0.0, 0.4)))
		draw_rect(Rect2(3, 3, size.x - 6, size.y - 6), FRAME, false, 6.0)

	func _draw_over_shadow(ct: Vector2, tr: Rect2) -> void:
		draw_set_transform(ct + Vector2(9, 9), angle(), Vector2.ONE)
		draw_texture_rect(tex_over, tr, false, SHADOW)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	## The German body rect on the board (px; turns are quarter turns, so it stays axis-aligned).
	func over_rect(steps := -1, off := Vector2i(-9999, 0)) -> Rect2:
		var s := rotation_steps if steps < 0 else steps
		var sz := body() * P
		if posmod(s, 2) == 1:
			sz = Vector2(sz.y, sz.x)
		return Rect2(over_center(off) - sz * 0.5, sz)

	func base_rect() -> Rect2:
		return Rect2(Vector2(base_at) * cp(), body() * P)

	## True while the German half lies ON the Russian one (more than the teeth reach across the seam).
	func over_lies_on_base() -> bool:
		var i := over_rect().intersection(base_rect())
		return i.size.x > 6.0 * P and i.size.y > 6.0 * P

	func _gui_input(event: InputEvent) -> void:
		if locked or tex_over == null:
			return
		if event is InputEventMouseButton:
			var mb := event as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_LEFT:
				if mb.pressed and hit_over(mb.position):
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
			var over := hit_over(mm.position)
			if over != hover:
				hover = over
				queue_redraw()
			mouse_default_cursor_shape = Control.CURSOR_MOVE if (_dragging or over) else Control.CURSOR_ARROW
			if _dragging:
				drag_to(mm.position)
				accept_event()

	## Drag (mouse): the half follows in whole cells from where the drag started.
	func drag_to(p: Vector2) -> void:
		var d := (p - _drag_from) / cp()
		var n := _drag_offset + Vector2i(roundi(d.x), roundi(d.y))
		if n != offset:
			set_state(rotation_steps, n)
			UIKit.ui_sound("tick")

	func begin_drag(p: Vector2) -> bool:
		if locked or not hit_over(p):
			return false
		_dragging = true
		_drag_from = p
		_drag_offset = offset
		drag_started.emit()
		return true

	func end_drag() -> void:
		_dragging = false
		queue_redraw()

	func is_dragging() -> bool:
		return _dragging

	func hit_over(p: Vector2) -> bool:
		var ct := over_center()
		var local := (p - ct).rotated(-angle())
		return Rect2(-body() * P * 0.5, body() * P).grow(6).has_point(local)


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
var _board: JoinBoard
var _panel: PanelContainer
var _root_box: VBoxContainer
var _side: VBoxContainer
var _instr: Label
var _legend_labels: Array[Label] = []
var _legend_rows: Array[Control] = []
var _state_label: Label
var _joined_label: Label
var _stamp_label: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _success_box: PanelContainer
var _success_label: Label
var _photo_label: Label
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
	head.add_child(Kit.label(Kit.t("ui.c4p2.halves.title"), "HeadingLabel"))
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	push.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(push)
	var sub := Kit.label(Kit.t("ui.c4p2.halves.subtitle"), "DimLabel")
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
	_board = JoinBoard.new()
	_board.name = "Board"
	_board.changed.connect(_on_board_changed)
	_board.joined_changed.connect(func(_n: int) -> void: Kit.ui_sound_first(["c4p2_tooth", "snap"]))
	_board.drag_started.connect(_push_history)
	_board.turn_requested.connect(func(steps: int) -> void: rotate(steps))
	_board.tooltip_text = Kit.t("ui.c4p2.halves.board_tip")
	_board.size_flags_horizontal = Control.SIZE_SHRINK_CENTER     # pixel art stays at exactly x3
	left.add_child(_board)
	var actions := Kit.hbox(16)
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(actions)
	_rotate_btn = Kit.button(Kit.t("ui.c4p2.halves.btn.rotate"), "", 200)
	_rotate_btn.pressed.connect(func() -> void: rotate(1))
	_reset_btn = Kit.button(Kit.t("ui.c4p2.halves.btn.reset"), "", 200)
	_reset_btn.pressed.connect(func() -> void: reset_pose())
	_check_btn = Kit.button(Kit.t("ui.c4p2.halves.btn.check"), "", 200)
	_check_btn.pressed.connect(func() -> void: submit())
	_close_btn = Kit.button(Kit.t("ui.c4p2.halves.btn.close"), "", 200)
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
			Kit.t("ui.c4p2.halves.hint_move")],
		["R", Kit.t("ui.c4p2.halves.hint_rotate")], [Kit.t("ui.key.mouse"), Kit.t("ui.c4p2.halves.hint_drag")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.c4p2.halves.hint_undo")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.c4p2.halves.hint_check")], [Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]])
	_controls.tooltip_text = Kit.t("ui.c4p2.halves.controls")
	_controls.mouse_filter = Control.MOUSE_FILTER_PASS
	_root_box.add_child(_controls)
	_load_layout()
	_build_legend_icons()
	_refresh()
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)


func _gap(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


var _legend_icons: Array[TextureRect] = []


func _build_side(v: VBoxContainer) -> void:
	_instr = Kit.wrap_label(Kit.t("ui.c4p2.halves.instruction"), "BodyLabel")
	_instr.name = "Instruction"
	Kit.scalable(_instr, 26)
	v.add_child(_instr)
	for key in ["ui.c4p2.halves.legend.teeth", "ui.c4p2.halves.legend.stamp", "ui.c4p2.halves.legend.lines"]:
		var lr := Kit.hbox(18)
		var chip := Kit.panel("PaperCardPanel")
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var icon := TextureRect.new()
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.custom_minimum_size = Vector2(54, 54)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		chip.add_child(icon)
		lr.add_child(chip)
		_legend_icons.append(icon)
		var ll := Kit.wrap_label(Kit.t(key), "BodyLabel")
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
	_joined_label = Kit.label("", "BodyLabel")
	_joined_label.name = "Joined"
	Kit.scalable(_joined_label, 24)
	v.add_child(_joined_label)
	_stamp_label = Kit.label("", "BodyLabel")
	_stamp_label.name = "StampState"
	Kit.scalable(_stamp_label, 24)
	v.add_child(_stamp_label)
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
	_hint_label = Kit.wrap_label(Kit.t("ui.c4p2.halves.hint"), "BodyLabel")
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
	var stamp := _make_stamp(Kit.t("ui.c4p2.halves.stamp").to_upper().replace("ß", "SS"))
	stamp.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	sv.add_child(stamp)
	_success_label = Kit.wrap_label(Kit.t("ui.c4p2.halves.success"), "TypeLabel")
	_success_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_success_label, 22)
	sv.add_child(_success_label)
	_photo_label = Kit.wrap_label(Kit.t("ui.c4p2.halves.photos"), "TypeDim")
	_photo_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_photo_label, 20)
	sv.add_child(_photo_label)
	_success_box.visible = false
	v.add_child(_success_box)


## Legend icons drawn by the generator (shape, not colour): a tooth meeting its notch, a stamp half, a line end.
func _build_legend_icons() -> void:
	var leg: Dictionary = _layout.get("legend", {}) if _layout.get("legend") is Dictionary else {}
	var files := {"tooth": "c4p2_halves_legend_teeth.png", "stamp": "c4p2_halves_legend_stamp.png",
		"lines": "c4p2_halves_legend_lines.png"}
	var keys := ["tooth", "stamp", "lines"]
	for i in mini(keys.size(), _legend_icons.size()):
		var f = leg.get(keys[i], files[keys[i]])
		_legend_icons[i].texture = Kit.optional_tex(ART + str(f if f is String else files[keys[i]]))


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


func _v2(v, fallback := Vector2.ZERO) -> Vector2:
	if v is Array and v.size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return fallback


func _marks(src) -> Dictionary:
	var out := {}
	if not (src is Dictionary):
		return out
	for kind in src:
		var arr: Array = []
		for m in src[kind]:
			arr.append({"id": str(m.get("id", "")), "at": _v2(m.get("at")), "dir": _v2i(m.get("dir"), Vector2i.RIGHT)})
		out[str(kind)] = arr
	return out


## Reads karsk_c4p2_halves.json (cells, files, marks, start pose, board) into the table.
func _load_layout() -> void:
	var b := _board
	b.cell = int(_layout.get("cell_px", 16))
	var board: Dictionary = _layout.get("board", {}) if _layout.get("board") is Dictionary else {}
	var base: Dictionary = _layout.get("base", {}) if _layout.get("base") is Dictionary else {}
	var over: Dictionary = _layout.get("overlay", {}) if _layout.get("overlay") is Dictionary else {}
	var marks: Dictionary = _layout.get("marks", {}) if _layout.get("marks") is Dictionary else {}
	b.board_cells = _v2i(board.get("cells"), Vector2i(20, 14))
	b.edge_margin = float(board.get("edge_margin_px", 8))
	b.lamp = _v2(board.get("lamp"), Vector2(214, 116))
	b.base_at = _v2i(base.get("at"), Vector2i(12, 5))
	b.over_at = _v2i(over.get("at"), Vector2i(1, 4))
	b.half_cells = _v2i(over.get("cells"), Vector2i(7, 5))
	b.pad = int(over.get("pad", 6))
	b.tex_table = Kit.optional_tex(ART + str(board.get("file", "c4p2_halves_table.png")))
	b.tex_base = Kit.optional_tex(DOCS + str(base.get("file", "karsk_c4p2_halves_ru.png")))
	b.tex_over = Kit.optional_tex(DOCS + str(over.get("file", "karsk_c4p2_halves_de.png")))
	b.tex_snap = Kit.optional_tex(ART + str(marks.get("snap", "c4p2_halves_snap.png")))
	b.tex_ring = Kit.optional_tex(ART + str(marks.get("ring", "c4p2_halves_ring.png")))
	b.tex_click = Kit.optional_tex(ART + str(marks.get("click", "c4p2_halves_click.png")))
	b.base_marks = _marks(base.get("marks"))
	b.over_marks = _marks(over.get("marks"))
	if _layout.get("pairs") is Array and not (_layout["pairs"] as Array).is_empty():
		b.pairs = _layout["pairs"]
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
	_board.clicks_shown = 0
	_board.ring_shown = false
	_board.flash = 0.0
	_close_btn.text = Kit.t("ui.c4p2.halves.btn.close")
	_set_feedback("")
	_board.set_state(int(_start["rotation_steps"]), Vector2i(int(_start["offset_x"]), int(_start["offset_y"])))
	_refresh()
	open_modal()


## The pose the player would submit now.
func pose() -> Dictionary:
	return {"rotation_steps": int(_board.rotation_steps), "offset_x": int(_board.offset.x), "offset_y": int(_board.offset.y)}


func is_done() -> bool:
	return _done


func joined() -> int:
	return _board.teeth_joined()


func stamp_closed() -> bool:
	return _board.stamp_closed()


func clicks_shown() -> int:
	return _board.clicks_shown


func ring_shown() -> bool:
	return _board.ring_shown


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
	_board.set_state(_board.rotation_steps, _board.offset + d)
	if pose() == before:
		return false
	history.append(before)
	if history.size() > HISTORY_MAX:
		history.pop_front()
	Kit.ui_sound("tick")
	return true


## A quarter turn clockwise (+1) or back (−1) around the half's centre.
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


## „Zurücksetzen“ / pad X: the half back on the guidebook, the way it came out of it.
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


## Enter / pad A / „Anlegen“. Returns the engine result.
func submit() -> Dictionary:
	if _done:
		return {}
	var answer := pose()
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	if r == null or not ok:
		_set_feedback(Kit.t("ui.c4p2.halves.error", {"error": _error_text(r)}))
		Kit.ui_sound("fail")
		return r if r is Dictionary else {"ok": false, "error": "no Story service"}
	var is_solved: bool = bool(r) if r is bool else bool((r as Dictionary).get("solved", false))
	if is_solved:
		_on_solved()
	else:
		_fails += 1
		Kit.ui_sound("fail")
		_set_feedback(Kit.t(wrong_key()))
		_nudge()
		_refresh()
	return r if r is Dictionary else {"ok": true, "solved": is_solved}


## The words for a wrong pose — from the marks' geometry, never from the answer.
func wrong_key() -> String:
	var r := _board.rotation_steps
	if _board.rotation_fits(r):
		return "ui.c4p2.halves.wrong"
	if _board.teeth_sideways(r):
		return "ui.c4p2.halves.wrong_sideways"
	return "ui.c4p2.halves.wrong_turned"


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
	Kit.ui_sound_first(["c4p2_halves_snap", "snap"])
	if not Kit.reduced_motion():
		Kit.appear(_success_box, 0.22)
	_close_btn.text = Kit.t("ui.c4p2.halves.btn.continue")
	_close_btn.grab_focus.call_deferred()
	solved_count += 1
	solved.emit(obj_id)
	_beat_token += 1
	var token := _beat_token
	var n := (_board.base_marks.get("notch", []) as Array).size()
	if Kit.reduced_motion() or not is_inside_tree():
		_board.clicks_shown = n
		_board.ring_shown = true
		_board.queue_redraw()
		Kit.ui_sound_first(["c4p2_stamp_close", "c4cine_stamp_ru", "stamp_thud"])
	else:
		for i in n:
			get_tree().create_timer(0.25 + CLICK_STEP * i, true).timeout.connect(_reveal_click.bind(i, token), CONNECT_ONE_SHOT)
		var t_ring := 0.4 + CLICK_STEP * n
		get_tree().create_timer(t_ring, true).timeout.connect(_reveal_ring.bind(token), CONNECT_ONE_SHOT)
		for k in 2:                          # Ekdahl's two photographs
			get_tree().create_timer(t_ring + 0.75 + 0.6 * k, true).timeout.connect(_photo.bind(token), CONNECT_ONE_SHOT)
	if is_inside_tree():
		get_tree().create_timer(success_beat(), true).timeout.connect(_on_beat.bind(token), CONNECT_ONE_SHOT)


func _reveal_click(i: int, token: int) -> void:
	if token != _beat_token or not _done:
		return
	_board.clicks_shown = maxi(_board.clicks_shown, i + 1)
	_board.queue_redraw()
	Kit.ui_sound("tick")


func _reveal_ring(token: int) -> void:
	if token != _beat_token or not _done:
		return
	_board.ring_shown = true
	_board.queue_redraw()
	Kit.ui_sound_first(["c4p2_stamp_close", "c4cine_stamp_ru", "stamp_thud"])


func _photo(token: int) -> void:
	if token != _beat_token or not _done or not _board.is_inside_tree():
		return
	Kit.ui_sound_first(["c4p2_shutter", "plaza_shutter", "tick"])
	var tw := _board.create_tween()
	tw.tween_property(_board, "flash", 0.32, 0.05)
	tw.tween_property(_board, "flash", 0.0, 0.22)


## Seconds the solved modal stays open by itself (≤ SUCCESS_BEAT_MAX); any confirm closes it earlier.
func success_beat() -> float:
	return clampf(2.0 + Kit.t("ui.c4p2.halves.success").length() * 0.03, 3.0, SUCCESS_BEAT_MAX)


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
	_state_label.text = Kit.t("ui.c4p2.halves.state", {"rot": _board.rotation_steps * 90, "x": "%+d" % off.x,
		"y": "%+d" % off.y})
	_state_label.add_theme_color_override("font_color", Kit.C_TEXT if hc else Kit.C_TEXT_DIM)
	var n := _board.teeth_joined()
	var total := (_board.over_marks.get("tooth", []) as Array).size()
	_joined_label.text = Kit.t("ui.c4p2.halves.joined", {"n": n, "total": total})
	_joined_label.add_theme_color_override("font_color", Kit.C_AMBER if n > 0 else (Kit.C_TEXT if hc else Kit.C_TEXT_DIM))
	var closed := _board.stamp_closed()
	_stamp_label.text = Kit.t("ui.c4p2.halves.stamp_closed" if closed else "ui.c4p2.halves.stamp_open")
	_stamp_label.add_theme_color_override("font_color", Kit.C_AMBER if closed else (Kit.C_TEXT if hc else Kit.C_TEXT_DIM))
	_rotate_btn.disabled = _done
	_reset_btn.disabled = _done
	_check_btn.disabled = _done
	_hint_box.visible = _hint_visible()
	_success_box.visible = _done
	_tip.text = Kit.t("ui.c4p2.halves.tip_pad" if Kit.last_input_pad else "ui.c4p2.halves.tip_mouse")
	var wide := Kit.text_scale() > 1.1
	var busy := _feedback.visible or _hint_box.visible
	_tip.visible = not _done and not (wide and busy)
	# the success card takes the instruction's place at every text size (round 10: at 100 % the solved state ran
	# 40 px past the 1080-px screen); at 125 % / 150 % notes and hint get its room as well
	_instr.visible = not _done and not (wide and busy)
	for r in _legend_rows:                               # 125 % / 150 % solved: the success card needs the room
		r.visible = not (wide and (_done or (busy and Kit.text_scale() > 1.3)))


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
	_board.flash = 0.0


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


## Controller (C4P2_DESIGN §2.7 = RoutePuzzle): D-pad moves, RB/LB turn, A checks, X start pose, Y takes back the
## last move, Back closes; B is left to UIRoot (cancel -> handle_cancel -> close).
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
## Text colour / background pairs this puzzle draws or shows (checked by tests/test_c4p2_puzzle_ui.gd).
func contrast_pairs() -> Array:
	var hc := Kit.high_contrast()
	var surf: Dictionary = _layout.get("surfaces", {}) if _layout.get("surfaces") is Dictionary else {}
	var paper := Color(str(surf.get("paper", "#E6DEC2")))
	return [
		{"what": "typed card text on the paper", "fg": Kit.C_INK, "bg": paper},
		{"what": "pose line", "fg": Kit.C_TEXT if hc else Kit.C_TEXT_DIM, "bg": Kit.C_NAVY},
		{"what": "joined count", "fg": Kit.C_AMBER, "bg": Kit.C_NAVY},
		{"what": "stamp state", "fg": Kit.C_TEXT if hc else Kit.C_TEXT_DIM, "bg": Kit.C_NAVY},
		{"what": "success text on the paper card", "fg": Kit.C_INK, "bg": Kit.C_PAPER},
	]
