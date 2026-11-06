extends "res://scripts/ui/minigames/minigame_base.gd"
## Station mini-game „Die Gepäckwaage“ (scenes/ui/minigames/LuggageScale.tscn, explore entry berlin.ost.luggage_scale at
## exp_luggage_scale in L_C4P2_Berlin, scene A; §12.8, documentation/C4P2_DESIGN.md §6). Monday, 20.30, Ostbahnhof: the
## clerk at the baggage counter of platform K stamps only what is weighed, and the family from the buffet cannot read
## the decimal scale. Konrad weighs the suitcase of presents for the grandmother in Karsk (too heavy for the Corridor's
## 20 kg), the suitcase again after the mother has repacked, and the parcel of what came out. Rule: luggage_logic.gd
## (a big sliding weight in 5-kg notches, a small one in 0.1-kg steps; the tongue plays in at the mark when they equal
## the load; a reading away from the mark is refused). The stage is drawn here in art px (x3, x2 for larger text): the
## tiled wall of the hall and the clerk's window, the platform with the suitcase or the parcel, the column, the beam with
## its two rails and weights, swinging on its pivot, and the tongue in its frame.
## Sounds: mg_c4p2_poise_coarse / mg_c4p2_poise_fine / mg_c4p2_beam_knock / mg_c4p2_stamp (tools/audiogen/mg_audio_c4p2.py).
## Keys: ← / → (A / D, d-pad) move the big weight a notch · ↑ / ↓ (W / S, d-pad) the small one a step, held it slides ·
## Page Up / Page Down (pad RB / LB) the small one a whole kilo · E, Enter, Space or pad A read the scale · R or pad Y
## both weights back to zero · Esc gives up. Mouse: click or drag a weight along its rail, the wheel over a rail moves
## it a step, the button „Ablesen“ reads.

const Logic := preload("res://scripts/ui/minigames/luggage_logic.gd")
const STAGE := Vector2(400, 150)
## Art-px geometry of the stage (the tests click on it).
const PIVOT := Vector2(160, 44)
const RAIL_X0 := 170.0
const RAIL_X1 := 370.0
const COARSE_Y := 38.0
const FINE_Y := 54.0
const RAIL_HIT := 7.0
const TONGUE_X := 384.0
const TONGUE_MID := 46.0
const TONGUE_SWING := 14.0
const PLATFORM := Rect2(24, 118, 128, 4)
const TILT_DEG := 2.2

const COL_WALL := Color("cfc6a8")
const COL_WALL2 := Color("bdb393")
const COL_TILE_LINE := Color("a99f80")
const COL_DADO := Color("4d5a4a")
const COL_DADO2 := Color("3e4a3c")
const COL_FLOOR := Color("6b665c")
const COL_FLOOR2 := Color("5b574e")
const COL_IRON := [Color("15181a"), Color("2b3034"), Color("474f55"), Color("6c767d")]
const COL_BRASS := Color("c9a35a")
const COL_BRASS_HI := Color("efd18c")
const COL_BRASS_LO := Color("8a6a30")
const COL_CASE := Color("7a4a2a")
const COL_CASE_HI := Color("9c6238")
const COL_CASE_LO := Color("4f2e18")
const COL_STRAP := Color("3a2416")
const COL_PAPER := Color("b89a6a")
const COL_PAPER_LO := Color("8f7550")
const COL_STRING := Color("e4dcc6")
const COL_LABEL_P := Color("ece4cc")
const COL_INK := Color("23272b")
const COL_GREEN := Color("6fd08c")
const COL_RED := Color("e0483a")
const COL_AMBER := Color("e9b46e")
const COL_WHITE := Color("f5efda")
const COL_LABEL := Color("3a3a34")
const COL_LABEL_DIM := Color("6a6658")

var logic = Logic.new()
var S := 3
var compact := false
var _scene: Control
var _area: Control
var _side: Control
var _left: Control
var _head: Label
var _rows: Array = []                # one Label per item of the slip
var _reading_label: Label
var _limit_label: Label
var _btn_read: Button
var _bg: ImageTexture
var _t := 0.0
var _input_guard := 0.0
var _tip := 0.0                      # shown tongue position (-1 up … +1 down), spring-damped
var _tip_v := 0.0
var _drag := ""                      # "coarse" / "fine" while the mouse holds a weight
var _swap_t := -1.0                  # the next item sliding onto the platform
var _knock_guard := 0.0
var _stamp_t := -1.0                 # the clerk's stamp coming down on the slip


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_scene", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("scene_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.luggage.kicker", "mg.luggage.title", "mg.luggage.subtitle", "mg.luggage.instruction")
	compact = Kit.text_scale() > 1.01
	S = 2 if compact else 3
	if compact:
		_subtitle.visible = false
		_instr.visible = false
	var row := Kit.hbox(36)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var v := View.new()
	v.game = self
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.custom_minimum_size = STAGE * S
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	_scene = v
	var left := Kit.vbox(8)
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(left)
	left.add_child(v)
	_left = left
	area.custom_minimum_size.y = STAGE.y * S
	_area = area
	var side := Kit.vbox(4)
	_side = side
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	side.custom_minimum_size.x = 820 if compact else 500
	row.add_child(side)
	_head = Kit.wrap_label(Kit.t("mg.luggage.slip.head").to_upper().replace("ß", "SS"), "KickerLabel")
	side.add_child(_head)
	var plate := Kit.panel("PlatePanel")
	side.add_child(plate)
	var col := Kit.vbox(2)
	plate.add_child(col)
	for i in Logic.ITEMS.size():
		var l := Kit.wrap_label("", "BodyLabel")
		Kit.scalable(l, 21)
		col.add_child(l)
		_rows.append(l)
	_reading_label = Kit.label("", "HeadingLabel")
	Kit.scalable(_reading_label, 27)
	side.add_child(_reading_label)
	_limit_label = Kit.label("", "KickerLabel")
	side.add_child(_limit_label)
	var legend := Kit.wrap_label(Kit.t("mg.luggage.beam.coarse") + "\n" + Kit.t("mg.luggage.beam.fine"), "DimLabel")
	Kit.scalable(legend, 19)
	legend.visible = not compact
	side.add_child(legend)
	_btn_read = _add_button(Kit.t("mg.luggage.btn.read"), read_scale, 300, true)


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.3
	_tip = logic.tongue()
	set_status(Kit.t("mg.luggage.status.start", {"item": item_name()}))
	_status_hold = 2.4


func _reset_game() -> void:
	logic.reset()
	_tip = logic.tongue()
	_tip_v = 0.0
	_swap_t = -1.0
	_drag = ""
	_update_ui()


## R / pad Y: both weights back to zero for the item on the platform (the weighed items stay weighed).
func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	logic.set_coarse(0)
	logic.set_fine(0)
	set_status(Kit.t("mg.luggage.status.start", {"item": item_name()}))
	_status_hold = 1.4
	_update_ui()


func item_name() -> String:
	return Kit.t(str(logic.item()["key"]))


# ================================================================ actions
func move_coarse(d: int) -> void:
	if solved or ended:
		return
	if bool(logic.move_coarse(d).get("ok", false)):
		_sfx("mg_c4p2_poise_coarse", -5.0)
		clear_status_hold()
	_update_ui()


func move_fine(d: int, steps := 1) -> void:
	if solved or ended:
		return
	if bool(logic.move_fine(d, steps).get("ok", false)):
		_sfx("mg_c4p2_poise_fine", -9.0)
		clear_status_hold()
	_update_ui()


## „Ablesen“: a tongue at the mark is a weighing — the slip gets its line and the next item goes on; otherwise the
## clerk shakes his head (a refusal naming where the tongue stands).
func read_scale() -> void:
	if solved or ended or _input_guard > 0.0:
		return
	var r: Dictionary = logic.read()
	if bool(r.get("ok", false)):
		_sfx("mg_c4p2_stamp", -3.0)
		_stamp_t = 0.0
		var res_key := str(Logic.ITEMS[int(r["round"])]["result"])
		if bool(r.get("finished", false)):
			mark_solved(Kit.t(res_key) + " " + Kit.t("mg.luggage.solved"))
		else:
			_swap_t = 0.0
			clear_status_hold()
			set_status(Kit.t(res_key))
			_status_hold = 4.0
		_update_ui()
		return
	register_fail(Kit.t("mg.luggage.fail", {"read": Logic.kg_text(int(r.get("read_hg", 0))),
		"dir": Kit.t("mg.luggage.dir." + str(r.get("dir", "up")))}))
	_update_ui()


# ================================================================ hints
func _hint_text(level: int) -> String:
	if logic.done:
		return ""
	if level >= 2:
		var t := Logic.target_for(logic.load_hg())
		return Kit.t("mg.luggage.hint.next", {"coarse": int(t["coarse"]) * 5,
			"fine": Logic.kg_text(int(t["fine"])).replace(" kg", "")})
	return Kit.t("mg.luggage.hint.1")


func register_fail(text: String) -> void:
	var mode := int(Kit.setting("puzzle_hints", 1))
	if mode == 1:
		super.register_fail(text)
		return
	fails += 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	if mode == 2:
		show_hint(fails + 1)


func _hint_at_open() -> void:
	if int(Kit.setting("puzzle_hints", 1)) == 2:
		show_hint(1)


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.luggage.ctrl.coarse")],
		[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN), Kit.t("mg.luggage.ctrl.fine")],
		[Kit.action_key_text("interact"), Kit.t("mg.luggage.ctrl.read")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_t += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	_knock_guard = maxf(0.0, _knock_guard - delta)
	if _swap_t >= 0.0:
		_swap_t += delta
		if _swap_t > 0.6:
			_swap_t = -1.0
	if _stamp_t >= 0.0:
		_stamp_t += delta
		if _stamp_t > 0.6:
			_stamp_t = -1.0
	var target := 0.0 if (solved or logic.done) else logic.tongue()
	if Kit.reduced_motion():
		_tip = target
		_tip_v = 0.0
	else:
		var acc := 70.0 * (target - _tip) - 8.0 * _tip_v
		_tip_v += acc * delta
		_tip += _tip_v * delta
		if absf(_tip) > 1.0:
			if absf(_tip_v) > 0.9 and _knock_guard <= 0.0:
				_sfx("mg_c4p2_beam_knock", -10.0)
				_knock_guard = 0.25
			_tip = signf(_tip)
			_tip_v *= -0.3
	if not solved:
		var d := logic.diff_hg()
		var key := "mg.luggage.status.level" if d == 0 else ("mg.luggage.status.near" if absi(d) <= 2 else
			("mg.luggage.status.up" if d < 0 else "mg.luggage.status.down"))
		status_auto(Kit.t(key))
	_fit_height()
	if _scene != null:
		_scene.queue_redraw()


func _fit_height() -> void:
	if _area == null or _side == null or _left == null:
		return
	var need := maxf(_left.get_combined_minimum_size().y, _side.get_combined_minimum_size().y)
	if absf(_area.custom_minimum_size.y - need) > 0.5:
		_area.custom_minimum_size.y = need


func _update_ui() -> void:
	if _reading_label == null:
		return
	for i in _rows.size():
		var it: Dictionary = Logic.ITEMS[i]
		var state := Kit.t("mg.luggage.slip.open")
		var kg := "—"
		for r in logic.results:
			if int(r["round"]) == i:
				kg = Logic.kg_text(int(r["hg"]))
				state = Kit.t("mg.luggage.slip.over" if bool(r["over"]) else "mg.luggage.slip.ok")
		var mark := "▸ " if (i == logic.round_i and not logic.done) else "  "
		(_rows[i] as Label).text = "%s%s: %s · %s" % [mark, Kit.t(str(it["key"])), kg, state]
	_reading_label.text = Kit.t("mg.luggage.reading", {"kg": Logic.kg_text(logic.poise_hg())})
	_limit_label.text = Kit.t("mg.luggage.slip.limit", {"kg": Logic.kg_text(int(logic.item()["limit_hg"]))}).to_upper()
	if _hint_box != null and _hint_box.visible and not logic.done:
		_hint_label.text = _hint_text(maxi(1, hint_level))


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event, true)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y:
		if not (event is InputEventKey and event.echo):
			restart()
		return true
	if k == KEY_PAGEUP or pb == JOY_BUTTON_RIGHT_SHOULDER:
		move_fine(1, 10)
		return true
	if k == KEY_PAGEDOWN or pb == JOY_BUTTON_LEFT_SHOULDER:
		move_fine(-1, 10)
		return true
	if _is(event, ["ui_left", "move_left"], true):
		move_coarse(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		move_coarse(1)
		return true
	if _is(event, ["ui_up", "move_up"], true):
		move_fine(1)
		return true
	if _is(event, ["ui_down", "move_down"], true):
		move_fine(-1)
		return true
	if k == KEY_E or k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE or pb == JOY_BUTTON_A \
			or _is(event, ["ui_accept", "interact"]):
		if not (event is InputEventKey and event.echo):
			read_scale()
		return true
	return false


## Beam tilt (screen y offset) at art x for the shown tongue position.
func _tilt_y(x: float) -> float:
	return (x - PIVOT.x) * tan(deg_to_rad(TILT_DEG * _tip))


static func coarse_x(n: int) -> float:
	return RAIL_X0 + (RAIL_X1 - RAIL_X0) * float(n) / float(Logic.COARSE_MAX)


static func fine_x(n: int) -> float:
	return RAIL_X0 + (RAIL_X1 - RAIL_X0) * float(n) / float(Logic.FINE_MAX)


## Which rail a point (art px) is on: "coarse", "fine" or "".
func rail_at(p: Vector2) -> String:
	if p.x < RAIL_X0 - 8.0 or p.x > RAIL_X1 + 8.0:
		return ""
	if absf(p.y - (COARSE_Y + _tilt_y(p.x))) <= RAIL_HIT:
		return "coarse"
	if absf(p.y - (FINE_Y + _tilt_y(p.x))) <= RAIL_HIT:
		return "fine"
	return ""


func _drag_to(rail: String, x: float) -> void:
	if rail == "coarse":
		var n := clampi(int(round((x - RAIL_X0) / (RAIL_X1 - RAIL_X0) * float(Logic.COARSE_MAX))), 0, Logic.COARSE_MAX)
		if logic.set_coarse(n):
			_sfx("mg_c4p2_poise_coarse", -5.0)
	elif rail == "fine":
		var n := clampi(int(round((x - RAIL_X0) / (RAIL_X1 - RAIL_X0) * float(Logic.FINE_MAX))), 0, Logic.FINE_MAX)
		if logic.set_fine(n):
			_sfx("mg_c4p2_poise_fine", -9.0)
	_update_ui()


func scene_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		var p := mb.position / S
		match mb.button_index:
			MOUSE_BUTTON_LEFT:
				if mb.pressed:
					_drag = rail_at(p)
					if _drag != "":
						_drag_to(_drag, p.x)
				else:
					_drag = ""
			MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN:
				if mb.pressed:
					var d := 1 if mb.button_index == MOUSE_BUTTON_WHEEL_UP else -1
					match rail_at(p):
						"coarse":
							move_coarse(d)
						"fine":
							move_fine(d)
	elif event is InputEventMouseMotion and _drag != "":
		_drag_to(_drag, (event as InputEventMouseMotion).position.x / S)


# ================================================================ drawing (art px, x S)
static func _img_rect(img: Image, r: Rect2, col: Color) -> void:
	var x0 := maxi(0, int(r.position.x))
	var y0 := maxi(0, int(r.position.y))
	var x1 := mini(img.get_width(), int(r.end.x))
	var y1 := mini(img.get_height(), int(r.end.y))
	for y in range(y0, y1):
		for x in range(x0, x1):
			img.set_pixel(x, y, col)


## The hall behind the scale, drawn once: tiled wall, the dado, stone floor, the enamel sign, the clerk's window.
static func build_background() -> ImageTexture:
	var img := Image.create(int(STAGE.x), int(STAGE.y), false, Image.FORMAT_RGBA8)
	img.fill(COL_WALL)
	for y in range(0, 100, 8):
		_img_rect(img, Rect2(0, y, STAGE.x, 1), COL_TILE_LINE)
		var off := 0 if floori(y / 8.0) % 2 == 0 else 6
		for x in range(off, int(STAGE.x), 12):
			_img_rect(img, Rect2(x, y, 1, 8), COL_TILE_LINE)
	for i in 40:
		_img_rect(img, Rect2(float((i * 53) % 400), float((i * 31) % 96), 3, 1), COL_WALL2)
	_img_rect(img, Rect2(0, 100, STAGE.x, 32), COL_DADO)
	_img_rect(img, Rect2(0, 100, STAGE.x, 2), COL_DADO2)
	for x in range(0, int(STAGE.x), 40):
		_img_rect(img, Rect2(x, 102, 1, 30), COL_DADO2)
	_img_rect(img, Rect2(0, 132, STAGE.x, 18), COL_FLOOR)
	for x in range(0, int(STAGE.x), 26):
		_img_rect(img, Rect2(x, 132, 1, 18), COL_FLOOR2)
	_img_rect(img, Rect2(0, 141, STAGE.x, 1), COL_FLOOR2)
	# the enamel sign „Gepäck“ (blue with a white rim) and a timetable poster with its columns
	_img_rect(img, Rect2(10, 10, 46, 16), Color("e8e2cc"))
	_img_rect(img, Rect2(11, 11, 44, 14), Color("2c4a7a"))
	_img_rect(img, Rect2(60, 8, 30, 40), Color("ebe4cc"))
	for r in 9:
		_img_rect(img, Rect2(63, 12 + r * 4, 10 + (r * 7) % 12, 1), Color("7a7466"))
		_img_rect(img, Rect2(78, 12 + r * 4, 8, 1), Color("7a7466"))
	# the station clock over the counter: 20.31
	var cc := Vector2(128, 20)
	for y in range(-8, 9):
		for x in range(-8, 9):
			var rr := sqrt(float(x * x + y * y))
			if rr <= 8.0:
				img.set_pixel(int(cc.x) + x, int(cc.y) + y, Color("23272b") if rr > 7.0 else Color("f1ead2"))
	for k in 12:
		var a := TAU * float(k) / 12.0
		img.set_pixelv(Vector2i((cc + Vector2(sin(a), -cos(a)) * 6.0).round()), Color("23272b"))
	for t in 6:
		var am := TAU * 31.0 / 60.0
		img.set_pixelv(Vector2i((cc + Vector2(sin(am), -cos(am)) * float(t)).round()), Color("23272b"))
	for t in 4:
		var ah := TAU * (8.0 + 31.0 / 60.0) / 12.0
		img.set_pixelv(Vector2i((cc + Vector2(sin(ah), -cos(ah)) * float(t)).round()), Color("23272b"))
	# the enamel plate with the Corridor's luggage rule (its words are drawn as text over it)
	_img_rect(img, Rect2(176, 70, 112, 26), Color("2c4a7a"))
	_img_rect(img, Rect2(177, 71, 110, 24), Color("f1ead2"))
	_img_rect(img, Rect2(179, 73, 106, 20), Color("e8e0c4"))
	for x in [178, 285]:
		_img_rect(img, Rect2(x, 72, 1, 1), Color("7a7466"))
		_img_rect(img, Rect2(x, 93, 1, 1), Color("7a7466"))
	# the clerk's counter window behind the beam end: the clerk in his cap, the grille, stamp pad and slips
	_img_rect(img, Rect2(296, 66, 100, 50), Color("3a3024"))
	_img_rect(img, Rect2(300, 70, 92, 40), Color("1c1a16"))
	_img_rect(img, Rect2(300, 70, 92, 6), Color("2a2620"))
	_img_rect(img, Rect2(329, 92, 30, 18), Color("2c3442"))
	_img_rect(img, Rect2(329, 92, 30, 1), Color("3c4658"))
	_img_rect(img, Rect2(342, 91, 6, 3), Color("e8e4d8"))
	_img_rect(img, Rect2(344, 94, 2, 6), Color("1b2028"))
	_img_rect(img, Rect2(341, 80, 9, 11), Color("c9a07a"))
	_img_rect(img, Rect2(341, 80, 2, 11), Color("a9805c"))
	_img_rect(img, Rect2(343, 84, 6, 1), Color("23272b"))
	_img_rect(img, Rect2(344, 88, 3, 1), Color("8a5a44"))
	_img_rect(img, Rect2(339, 76, 13, 5), Color("1d2433"))
	_img_rect(img, Rect2(338, 80, 15, 1), Color("0e1218"))
	_img_rect(img, Rect2(345, 77, 2, 2), COL_BRASS)
	_img_rect(img, Rect2(356, 103, 11, 5), Color("2c3442"))
	_img_rect(img, Rect2(366, 104, 4, 3), Color("c9a07a"))
	_img_rect(img, Rect2(310, 98, 12, 10), Color("8f8670"))
	_img_rect(img, Rect2(311, 99, 10, 1), COL_LABEL_P)
	for x in range(302, 392, 6):
		_img_rect(img, Rect2(x, 70, 1, 40), Color("5a5244"))
	_img_rect(img, Rect2(300, 88, 92, 1), Color("4a4236"))
	_img_rect(img, Rect2(292, 112, 108, 6), Color("5c4630"))
	_img_rect(img, Rect2(292, 112, 108, 1), Color("7a6040"))
	_img_rect(img, Rect2(300, 106, 14, 6), Color("2a2a2a"))
	_img_rect(img, Rect2(320, 104, 18, 8), COL_LABEL_P)
	_img_rect(img, Rect2(321, 105, 12, 1), Color("9a9280"))
	_img_rect(img, Rect2(342, 108, 12, 4), Color("8a2a24"))
	return ImageTexture.create_from_image(img)


func _px_line(v: Control, a: Vector2, b: Vector2, col: Color, thick := 1) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1:
		var q := a.lerp(b, float(i) / float(maxi(1, n))).round()
		v.draw_rect(Rect2(q.x, q.y, thick, thick), col)


func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var hc := Kit.high_contrast()
	if _bg == null:
		_bg = build_background()
	v.draw_texture(_bg, Vector2.ZERO)
	# the platform and its base
	var sink := 0.0 if logic.done else 1.0
	v.draw_rect(Rect2(PLATFORM.position.x - 2, PLATFORM.position.y + 4, PLATFORM.size.x + 4, 10), COL_IRON[1])
	v.draw_rect(Rect2(PLATFORM.position.x, PLATFORM.position.y + sink, PLATFORM.size.x, PLATFORM.size.y), COL_IRON[2])
	v.draw_rect(Rect2(PLATFORM.position.x, PLATFORM.position.y + sink, PLATFORM.size.x, 1), COL_IRON[3])
	for x in range(int(PLATFORM.position.x) + 6, int(PLATFORM.end.x), 10):
		v.draw_rect(Rect2(x, PLATFORM.position.y + sink + 1, 4, 2), COL_IRON[1])
	_draw_item(v, sink)
	# the column with its cast foot, the pivot and the lever to the platform
	v.draw_rect(Rect2(PIVOT.x - 4, PIVOT.y + 2, 8, 124 - PIVOT.y), COL_IRON[1])
	v.draw_rect(Rect2(PIVOT.x - 4, PIVOT.y + 2, 2, 124 - PIVOT.y), COL_IRON[2])
	v.draw_rect(Rect2(PIVOT.x - 9, 124, 18, 8), COL_IRON[0])
	v.draw_rect(Rect2(PIVOT.x - 7, 122, 14, 2), COL_IRON[2])
	# the beam: two rails pivoting together, notches and graduation, the weights riding on them
	var a0 := Vector2(PIVOT.x - 8.0, COARSE_Y + _tilt_y(PIVOT.x - 8.0))
	var a1 := Vector2(RAIL_X1 + 6.0, COARSE_Y + _tilt_y(RAIL_X1 + 6.0))
	var b0 := Vector2(PIVOT.x - 8.0, FINE_Y + _tilt_y(PIVOT.x - 8.0))
	var b1 := Vector2(RAIL_X1 + 6.0, FINE_Y + _tilt_y(RAIL_X1 + 6.0))
	for k in 3:
		_px_line(v, a0 + Vector2(0, k), a1 + Vector2(0, k), COL_IRON[1] if k > 0 else COL_IRON[3], 1)
		_px_line(v, b0 + Vector2(0, k), b1 + Vector2(0, k), COL_IRON[1] if k > 0 else COL_IRON[3], 1)
	_px_line(v, a1, b1 + Vector2(0, 2), COL_IRON[1], 2)
	_px_line(v, Vector2(PIVOT.x, COARSE_Y + _tilt_y(PIVOT.x)), Vector2(PIVOT.x, FINE_Y + _tilt_y(PIVOT.x) + 2), COL_IRON[0], 3)
	v.draw_rect(Rect2(PIVOT.x - 2, PIVOT.y - 2, 4, 4), COL_BRASS)
	for n in Logic.COARSE_MAX + 1:
		var x := coarse_x(n)
		v.draw_rect(Rect2(round(x), round(COARSE_Y + _tilt_y(x)) - 2, 1, 2), COL_IRON[3])
	for n in Logic.FINE_MAX + 1:
		var x := fine_x(n)
		var long := n % 10 == 0
		v.draw_rect(Rect2(round(x), round(FINE_Y + _tilt_y(x)) + 3, 1, 3 if long else 1), COL_IRON[3] if long else COL_IRON[2])
	# the big weight (straddles the upper rail) and the small one (rides the lower rail)
	var cx := coarse_x(logic.coarse)
	var cy := COARSE_Y + _tilt_y(cx)
	v.draw_rect(Rect2(round(cx) - 6, round(cy) - 7, 12, 12), COL_BRASS_LO)
	v.draw_rect(Rect2(round(cx) - 5, round(cy) - 6, 10, 10), COL_BRASS)
	v.draw_rect(Rect2(round(cx) - 5, round(cy) - 6, 10, 2), COL_BRASS_HI)
	v.draw_rect(Rect2(round(cx), round(cy) + 4, 1, 3), COL_INK)
	var fx := fine_x(logic.fine)
	var fy := FINE_Y + _tilt_y(fx)
	v.draw_rect(Rect2(round(fx) - 4, round(fy) - 5, 8, 8), COL_BRASS_LO)
	v.draw_rect(Rect2(round(fx) - 3, round(fy) - 4, 6, 6), COL_BRASS)
	v.draw_rect(Rect2(round(fx) - 3, round(fy) - 4, 6, 1), COL_BRASS_HI)
	v.draw_rect(Rect2(round(fx), round(fy) + 2, 1, 3), COL_INK)
	# the tongue in its frame: the mark in the middle, the stops above and below
	var frame := Rect2(TONGUE_X - 4, TONGUE_MID - TONGUE_SWING - 6, 10, TONGUE_SWING * 2.0 + 12.0)
	v.draw_rect(frame, COL_IRON[1])
	v.draw_rect(frame.grow(-1.0), COL_IRON[0])
	v.draw_rect(Rect2(frame.position.x - 3, TONGUE_MID, frame.size.x + 6, 1), COL_WHITE if hc else COL_GREEN)
	var ty := TONGUE_MID + _tip * TONGUE_SWING
	var on_mark: bool = logic.diff_hg() == 0 and not logic.done
	v.draw_rect(Rect2(TONGUE_X - 2, round(ty) - 1, 6, 3), (COL_WHITE if hc else COL_GREEN) if on_mark else (COL_WHITE if hc else COL_AMBER))
	_px_line(v, Vector2(RAIL_X1 + 6.0, FINE_Y + _tilt_y(RAIL_X1 + 6.0) - 6.0), Vector2(TONGUE_X - 2, round(ty)), COL_IRON[2], 1)
	# the clerk's arm and stamp coming down on the slip after a good reading
	if _stamp_t >= 0.0:
		var k := sin(PI * clampf(_stamp_t / 0.5, 0.0, 1.0))
		var sy := 96.0 + 9.0 * k
		v.draw_rect(Rect2(318, round(sy) - 9.0, 10, 9), Color("2c3442"))
		v.draw_rect(Rect2(319, round(sy) - 1.0, 8, 3), Color("c9a07a"))
		v.draw_rect(Rect2(320, round(sy) + 2.0, 6, 3), Color("2a2a2a"))
		if k > 0.9:
			v.draw_rect(Rect2(322, 108, 6, 2), Color("8a2a24"))
	# labels (screen pixels, theme font)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var font := v.get_theme_default_font()
	if font == null:
		return
	var fs := 13 if S == 2 else 17
	v.draw_string(font, Vector2(179.0 * S, 81.0 * S), Kit.t("mg.luggage.sign.1"), HORIZONTAL_ALIGNMENT_CENTER, 106.0 * S,
		fs - 1, Color("2c4a7a"))
	v.draw_string(font, Vector2(179.0 * S, 90.0 * S), Kit.t("mg.luggage.sign.2"), HORIZONTAL_ALIGNMENT_CENTER, 106.0 * S,
		fs - 3, Color("23272b"))
	var tc := COL_LABEL if not hc else COL_INK
	for n in range(0, Logic.COARSE_MAX + 1, 2):
		var x := coarse_x(n)
		v.draw_string(font, Vector2(x * S - 20.0, (COARSE_Y + _tilt_y(x) - 9.0) * S), str(n * 5), HORIZONTAL_ALIGNMENT_CENTER,
			40.0, fs, tc)
	for n in range(0, Logic.FINE_MAX + 1, 10):
		var x := fine_x(n)
		v.draw_string(font, Vector2(x * S - 20.0, (FINE_Y + _tilt_y(x) + 13.0) * S), str(floori(n / 10.0)), HORIZONTAL_ALIGNMENT_CENTER,
			40.0, fs, tc)
	v.draw_string(font, Vector2(12.0 * S, 21.0 * S), "GEPÄCK", HORIZONTAL_ALIGNMENT_CENTER, 42.0 * S, fs - 1, COL_WHITE)


## The suitcase (rounds 1 and 2; a little flatter once repacked) or the parcel (round 3), sliding on after a weighing.
func _draw_item(v: Control, sink: float) -> void:
	var slide := 0.0
	if _swap_t >= 0.0:
		slide = (1.0 - clampf(_swap_t / 0.5, 0.0, 1.0)) * 70.0
	var base_y := PLATFORM.position.y + sink
	var rnd: int = logic.round_i if not logic.done else Logic.ITEMS.size() - 1
	if rnd < 2:
		var h := 34.0 if rnd == 0 else 30.0
		var r := Rect2(46 + slide, base_y - h, 76, h)
		v.draw_rect(r, COL_CASE_LO)
		v.draw_rect(r.grow(-1.0), COL_CASE)
		v.draw_rect(Rect2(r.position.x + 1, r.position.y + 1, r.size.x - 2, 2), COL_CASE_HI)
		for sx in [16.0, 58.0]:
			v.draw_rect(Rect2(r.position.x + sx, r.position.y, 3, h), COL_STRAP)
			v.draw_rect(Rect2(r.position.x + sx - 1, r.position.y + h * 0.5 - 2, 5, 4), COL_BRASS_LO)
		v.draw_rect(Rect2(r.position.x + 30, r.position.y - 4, 16, 2), COL_STRAP)
		v.draw_rect(Rect2(r.position.x + 30, r.position.y - 4, 2, 4), COL_STRAP)
		v.draw_rect(Rect2(r.position.x + 44, r.position.y - 4, 2, 4), COL_STRAP)
		# the travel label „Karsk“ and a sticker of the Corridor
		v.draw_rect(Rect2(r.position.x + 22, r.position.y + 8, 14, 9), COL_LABEL_P)
		v.draw_rect(Rect2(r.position.x + 24, r.position.y + 11, 10, 1), COL_INK)
		v.draw_rect(Rect2(r.position.x + 24, r.position.y + 13, 7, 1), COL_INK)
		v.draw_rect(Rect2(r.position.x + 64, r.position.y + 20, 6, 6), Color("c9a35a"))
		if rnd == 1:
			v.draw_rect(Rect2(r.position.x + 40, r.position.y + 22, 8, 4), COL_CASE_LO)
	else:
		var r := Rect2(64 + slide, base_y - 24, 42, 24)
		v.draw_rect(r, COL_PAPER_LO)
		v.draw_rect(r.grow(-1.0), COL_PAPER)
		v.draw_rect(Rect2(r.position.x + 20, r.position.y, 2, r.size.y), COL_STRING)
		v.draw_rect(Rect2(r.position.x, r.position.y + 11, r.size.x, 2), COL_STRING)
		v.draw_rect(Rect2(r.position.x + 18, r.position.y + 9, 6, 6), COL_STRING)
		v.draw_rect(Rect2(r.position.x + 26, r.position.y + 15, 12, 7), COL_LABEL_P)
		v.draw_rect(Rect2(r.position.x + 28, r.position.y + 17, 8, 1), COL_INK)
		v.draw_rect(Rect2(r.position.x + 28, r.position.y + 19, 6, 1), COL_INK)


# ================================================================ synthetic solve (real-input driver)
## Weighs all three items through synthetic key events only: the big weight by ←/→, the small one by Page Up/Down
## (whole kilos) and ↑/↓, then E.
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 60000:
		var nx: Dictionary = logic.next_move()
		if nx.is_empty():
			break
		match str(nx["beam"]):
			"coarse":
				await _tap(KEY_RIGHT if int(nx["dir"]) > 0 else KEY_LEFT)
			"fine":
				if int(nx["steps"]) >= 10:
					await _tap(KEY_PAGEUP if int(nx["dir"]) > 0 else KEY_PAGEDOWN)
				else:
					await _tap(KEY_UP if int(nx["dir"]) > 0 else KEY_DOWN)
			_:
				await _tap(KEY_E)
				await _frames(3)
	await _until(func(): return solved, 4.0)
