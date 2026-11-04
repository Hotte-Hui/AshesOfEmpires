extends Control
## Light-table board of the overlay puzzle: draws the cutting-mat grid, plan A (fixed) and plan B
## (tracing overlay, rotated in 90 degree steps around its centre, moved in whole cells = snap) plus the
## registration marks (A = ring with cross, B = open diamond: distinguishable by shape, not colour).
## Plan images are 1:1 pixel art drawn at x3; 90 degree rotations keep the pixel grid intact.
## Mouse: drag plan B; movement snaps to the grid while dragging.

signal changed
signal mark_aligned(count: int)

const Kit := preload("res://scripts/ui/ui_kit.gd")
const PX := 3
const MAT := Color("0e1a20")
const MAT_EDGE := Color("06151d")
const GRID := Color("16282d")
const GRID_MAJOR := Color("1f363a")

var cell := 16
var tex_a: Texture2D
var tex_b: Texture2D
var landmarks: Array = []            # [{name, a: centre (cells), b: centre (cells)}]
var max_cells := Vector2i(22, 14)
var b_origin := Vector2i.ZERO        # B top-left in cells relative to A at offset (0, 0)
var a_cell := Vector2i(4, 2)         # A top-left on the board (cells)
var board_cells := Vector2i(22, 13)
var rotation_steps := 0
var offset := Vector2i.ZERO
var offset_limit := Vector2i(8, 6)
var b_opaque := false
var locked := false
var _dragging := false
var _drag_from := Vector2.ZERO
var _drag_offset := Vector2i.ZERO
var _aligned := 0
var _mark_a: Texture2D
var _mark_b: Texture2D


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	clip_contents = true
	_mark_a = Kit.tex("res://assets/ui/puzzle/mark_a.png")
	_mark_b = Kit.tex("res://assets/ui/puzzle/mark_b.png")


func setup(a: Texture2D, b: Texture2D, cell_px: int, marks: Array, origin := Vector2i.ZERO, opaque_b := false) -> void:
	tex_a = a
	tex_b = b
	cell = maxi(4, cell_px)
	landmarks = marks
	b_origin = origin
	b_opaque = opaque_b
	var ca := _cells_of(tex_a)
	var cb := _cells_of(tex_b)
	var need := Vector2i(maxi(ca.x, cb.x), maxi(ca.y, cb.y))
	board_cells = Vector2i(clampi(need.x + 4, 12, max_cells.x), clampi(need.y + 2, 8, max_cells.y))
	a_cell = Vector2i((board_cells.x - ca.x) / 2, (board_cells.y - ca.y) / 2)
	offset_limit = Vector2i(board_cells.x / 2, board_cells.y / 2)
	custom_minimum_size = Vector2(board_cells * cell * PX)
	size = custom_minimum_size
	queue_redraw()


func _cells_of(t2: Texture2D) -> Vector2i:
	if t2 == null:
		return Vector2i(8, 6)
	return Vector2i(ceili(t2.get_width() / float(cell)), ceili(t2.get_height() / float(cell)))


func set_state(rot: int, off: Vector2i) -> void:
	rotation_steps = posmod(rot, 4)
	offset = Vector2i(clampi(off.x, -offset_limit.x, offset_limit.x), clampi(off.y, -offset_limit.y, offset_limit.y))
	queue_redraw()
	changed.emit()


func nudge(d: Vector2i) -> void:
	if locked:
		return
	set_state(rotation_steps, offset + d)


func rotate_by(steps: int) -> void:
	if locked:
		return
	set_state(rotation_steps + steps, offset)


# ---------------------------------------------------------------- geometry (board-local pixels)
func cell_px() -> int:
	return cell * PX


func a_origin_px() -> Vector2:
	return Vector2(a_cell * cell_px())


func b_rect_unrotated() -> Rect2:
	var sz := tex_b.get_size() * PX if tex_b != null else Vector2(8, 6) * cell_px()
	return Rect2(a_origin_px() + Vector2(b_origin + offset) * cell_px(), sz)


func b_center() -> Vector2:
	var r := b_rect_unrotated()
	return (r.position + r.size * 0.5).round()


func b_angle() -> float:
	return rotation_steps * PI * 0.5


func b_point(local_cells: Vector2) -> Vector2:
	var r := b_rect_unrotated()
	var p := r.position + local_cells * cell_px()
	var c := b_center()
	return c + (p - c).rotated(b_angle())


func a_point(local_cells: Vector2) -> Vector2:
	return a_origin_px() + local_cells * cell_px()


func aligned_count() -> int:
	return _aligned


# ---------------------------------------------------------------- drawing
func _draw() -> void:
	var cp := cell_px()
	var full := Rect2(Vector2.ZERO, size)
	draw_rect(full, MAT)
	# 1 art-pixel (3 px) rules, every 4th cell brighter (cutting-mat look)
	for x in range(1, board_cells.x):
		draw_rect(Rect2(x * cp, 0, PX, size.y), GRID_MAJOR if (x - a_cell.x) % 4 == 0 else GRID)
	for y in range(1, board_cells.y):
		draw_rect(Rect2(0, y * cp, size.x, PX), GRID_MAJOR if (y - a_cell.y) % 4 == 0 else GRID)
	draw_rect(full, MAT_EDGE, false, 3.0)
	# plan A
	if tex_a != null:
		var ra := Rect2(a_origin_px(), tex_a.get_size() * PX)
		draw_rect(Rect2(ra.position + Vector2(9, 9), ra.size), Color(0, 0, 0, 0.35))
		draw_texture_rect(tex_a, ra, false)
	# plan B (tracing overlay)
	if tex_b != null:
		var rb := b_rect_unrotated()
		var c := b_center()
		draw_set_transform(c, b_angle(), Vector2.ONE)
		var local := Rect2(rb.position - c, rb.size)
		draw_rect(local, Color(0.80, 0.88, 0.95, 0.10 if b_opaque else 0.20))
		draw_texture_rect(tex_b, local, false, Color(1, 1, 1, 0.62 if b_opaque else 0.9))
		draw_rect(local, Color("58718a"), false, 3.0)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# registration marks
	var aligned := 0
	for lm in landmarks:
		var pa := a_point(lm["a"])
		var pb := b_point(lm["b"])
		if _mark_a != null:
			draw_texture(_mark_a, (pa - _mark_a.get_size() * 0.5).round())
		if _mark_b != null:
			draw_texture(_mark_b, (pb - _mark_b.get_size() * 0.5).round())
		if pa.distance_to(pb) < 1.5:
			aligned += 1
	if aligned != _aligned:
		var grew := aligned > _aligned
		_aligned = aligned
		if grew:
			mark_aligned.emit(aligned)


# ---------------------------------------------------------------- mouse drag (snapped)
func _gui_input(event: InputEvent) -> void:
	if locked or tex_b == null:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and _hit_b(event.position):
			_dragging = true
			_drag_from = event.position
			_drag_offset = offset
			accept_event()
		elif not event.pressed and _dragging:
			_dragging = false
			accept_event()
	elif event is InputEventMouseMotion:
		mouse_default_cursor_shape = Control.CURSOR_MOVE if (_dragging or _hit_b(event.position)) else Control.CURSOR_ARROW
		if _dragging:
			var d: Vector2 = (event.position - _drag_from) / float(cell_px())
			var n := _drag_offset + Vector2i(roundi(d.x), roundi(d.y))
			if n != offset:
				set_state(rotation_steps, n)
				Kit.ui_sound("tick")
			accept_event()


func _hit_b(p: Vector2) -> bool:
	var c := b_center()
	var local := (p - c).rotated(-b_angle()) + c
	return b_rect_unrotated().grow(6).has_point(local)
