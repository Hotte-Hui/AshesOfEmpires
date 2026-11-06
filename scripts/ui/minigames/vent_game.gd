extends "res://scripts/ui/minigames/minigame_base.gd"
## Annex mini-game „Die Lüftungsklappen“ (scenes/ui/minigames/VentFlaps.tscn, explore entry berlin.annex.fans at
## exp_fans in L_C4_Annex, scene D; §12.8, documentation/C4_DESIGN.md §6). Sunday, 6.00, Nebenstelle Süd: behind the
## grille of the machine room the fault bell rings. Two fans blow into one plenum, three ducts leave it -- the card hall,
## the typists' room, the corridor of the Staatspolizei -- each with a butterfly flap on the desk. Over the desk hangs
## the ventilation sheet Konrad drew himself (Blatt 3) with the design flows. The night shift has turned the flaps:
## the typists' room gets twice its air, the corridor none. Konrad sets them until all three needles stand in their
## green bands and acknowledges the fault; the third duct's label says what the corridor's air is for.
## Rule: vent_logic.gd (every flap moves all three needles; the long corridor duct needs the widest flap; one
## solution among 125 positions, no dead end). The stage is drawn here (pixel art in art px, x3, x2 for larger text):
## fans, plenum, ducts with their flaps and handles, the three dials, the fault lamp and bell, the air in the ducts.
## Sounds: mg_c4_flap_open / mg_c4_flap_close / mg_c4_alarm_bell / mg_c4_air_settled (tools/audiogen/mg_audio_c4.py),
## the end stop reuses mg_c4_lever_locked.
## Keys: Left/Right (A/D, d-pad) choose a flap · Up opens it one step, Down closes it · 1-3 choose directly ·
## E, Enter, Space or pad A acknowledge the fault · R or pad Y starts over · Esc gives up.
## Mouse: point at a duct; click above its flap (or wheel up) opens, below it (wheel down, right click) closes; the
## button „Störung quittieren“ acknowledges.

const Logic := preload("res://scripts/ui/minigames/vent_logic.gd")
const STAGE := Vector2(400, 150)
## Art-px geometry of the stage (the tests click on it).
const DUCT_X := [168.0, 258.0, 348.0]
const DUCT_W := 24.0
const DUCT_TOP := 46.0
const FLAP_Y := 82.0
const PLENUM := Rect2(104, 116, 288, 26)
const DIAL_Y := 26.0
const DIAL_R := 13.0
const DIAL_MAX := 18.0               # thousand m³/h at full scale
const FAN_C := [Vector2(36, 118), Vector2(76, 118)]
const FAN_R := 17.0
const BELL := Vector2(40, 22)        # the rim of the fault bell
const COLUMN_HALF := 28.0            # half width of a duct's column (cursor, mouse target: duct + handle)

const COL_WALL := Color("1c2321")
const COL_WALL2 := Color("232d2a")
const COL_STEEL := [Color("15191c"), Color("2f373d"), Color("4a545c"), Color("6c7881"), Color("98a4ac")]
const COL_PAPER := Color("e6e1cf")
const COL_INK := Color("23272b")
const COL_GREEN := Color("6fd08c")
const COL_GREEN_BAND := Color("4f9e66")
const COL_RED := Color("e0483a")
const COL_RED_DIM := Color("4a1d18")
const COL_NEEDLE := Color("b3261e")
const COL_AIR := Color("d4ebe4")
const COL_AMBER := Color("e9b46e")
const COL_WHITE := Color("f5efda")
const COL_LABEL := Color("b3a98d")
const ANIM_T := 0.14
const BELL_EVERY := 9.0

var logic = Logic.new()
## Art scale: x3, or x2 in the compact layout for larger text (set in _build_play).
var S := 3
var compact := false
var cursor := 0
var _scene: Control
var _area: Control
var _side: Control
var _left: Control
var _head: Label
var _flap_label: Label
var _desc_label: Label
var _state_label: Label
var _table: GridContainer
var _cells: Dictionary = {}          # flap -> [ist Label, Lage Label]
var _btn_main: Button
var _anim: Dictionary = {}           # flap -> shown flap position 0..4 (float)
var _needle: Dictionary = {}         # flap -> shown flow (thousand m³/h)
var _shake: Dictionary = {}          # flap -> seconds of the end-stop jolt left
var _t := 0.0
var _fan_a := 0.0
var _bell_left := 0.0                # seconds of the bell's visible ringing left
var _bell_next := BELL_EVERY
var _input_guard := 0.0
var _hover := -1


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_scene", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("scene_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.vent.kicker", "mg.vent.title", "mg.vent.subtitle", "mg.vent.instruction")
	compact = Kit.text_scale() > 1.01
	S = 2 if compact else 3
	if compact:      # larger text: the side panel carries the sheet, the flavour gives way
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
	_head = Kit.wrap_label("", "KickerLabel")
	side.add_child(_head)
	var plate := Kit.panel("PlatePanel")
	side.add_child(plate)
	var col := Kit.vbox(2)
	plate.add_child(col)
	_flap_label = Kit.label("", "HeadingLabel")
	Kit.scalable(_flap_label, 27)
	col.add_child(_flap_label)
	_desc_label = Kit.wrap_label("", "DimLabel")
	Kit.scalable(_desc_label, 20)
	_desc_label.visible = not compact          # larger text: name and state are enough, the sheet says the rest
	col.add_child(_desc_label)
	_state_label = Kit.wrap_label("", "KickerLabel")
	col.add_child(_state_label)
	var th := Kit.wrap_label(Kit.t("mg.vent.sheet.title").to_upper().replace("ß", "SS"), "KickerLabel")
	side.add_child(th)
	_table = GridContainer.new()
	_table.columns = 4
	_table.add_theme_constant_override("h_separation", 22)
	_table.add_theme_constant_override("v_separation", 0)
	side.add_child(_table)
	_fill_table()
	_btn_main = _add_button(Kit.t("mg.vent.btn.ack"), acknowledge, 300, true)


func _fill_table() -> void:
	for k in ["mg.vent.sheet.duct", "mg.vent.sheet.target", "mg.vent.sheet.actual", "mg.vent.sheet.state"]:
		var h := Kit.label(Kit.t(k), "DimLabel")
		Kit.scalable(h, 19)
		_table.add_child(h)
	for f in Logic.FLAPS:
		var nl := Kit.label("%d · %s" % [Logic.number_of(f), flap_name(f)], "BodyLabel")
		Kit.scalable(nl, 19)
		_table.add_child(nl)
		var soll := Kit.label(_m3(float(Logic.TARGET[f])), "BodyLabel")
		Kit.scalable(soll, 19)
		_table.add_child(soll)
		var ist := Kit.label("", "BodyLabel")
		Kit.scalable(ist, 19)
		_table.add_child(ist)
		var lage := Kit.label("", "BodyLabel")
		Kit.scalable(lage, 19)
		_table.add_child(lage)
		_cells[f] = [ist, lage]


## Thousand m³/h as the sheet writes it: „12 000 m³/h“.
static func _m3(v: float) -> String:
	var n := int(round(v * 10.0)) * 100
	var s := str(n)
	if n >= 1000:
		s = "%d %03d" % [int(n / 1000.0), n % 1000]
	return s + " m³/h"


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.3
	_bell_left = 1.4
	_bell_next = BELL_EVERY
	if not bool(ctx.get("auto", false)):
		_sfx("mg_c4_alarm_bell", -10.0)
	set_status(Kit.t("mg.vent.status.start"))
	_status_hold = 2.6


func _reset_game() -> void:
	logic.reset()
	cursor = 0
	_shake = {}
	var fl: Dictionary = logic.flows()
	for f in Logic.FLAPS:
		_anim[f] = float(logic.pos[f])
		_needle[f] = float(fl[f])
	_update_ui()


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	set_status(Kit.t("mg.vent.status.restart"))
	_status_hold = 1.4


# ================================================================ actions
func selected() -> String:
	return str(Logic.FLAPS[clampi(cursor, 0, Logic.FLAPS.size() - 1)])


static func flap_name(f: String) -> String:
	return Kit.t("mg.vent.name." + f)


static func pos_name(p: int) -> String:
	return Kit.t("mg.vent.pos.%d" % clampi(p, 0, Logic.MAX_POS))


## One step on a flap: d = +1 opens, -1 closes.
func move_flap(f: String, d: int) -> void:
	if solved or ended:
		return
	cursor = Logic.index_of(f)
	var r: Dictionary = logic.step(f, d)
	if not bool(r.get("ok", false)):
		_shake[f] = 0.25
		_sfx("mg_c4_lever_locked", -6.0)
		set_status(Kit.t("mg.vent.status.end_open" if d > 0 else "mg.vent.status.end_closed",
			{"n": Logic.number_of(f), "name": flap_name(f)}))
		_status_hold = 1.2
		_update_ui()
		return
	_sfx("mg_c4_flap_open" if d > 0 else "mg_c4_flap_close", -4.0)
	if bool(r.get("balanced", false)):
		clear_status_hold()
		set_status(Kit.t("mg.vent.status.balanced"))
		_status_hold = 2.0
	else:
		set_status(Kit.t("mg.vent.status.moved", {"n": Logic.number_of(f), "name": flap_name(f),
			"pos": pos_name(int(r["pos"]))}))
		_status_hold = 1.0
	_update_ui()


## Acknowledge the fault: only with all three needles in their bands; otherwise a refusal names the worst duct.
func acknowledge() -> void:
	if solved or ended:
		return
	var r: Dictionary = logic.acknowledge()
	if bool(r.get("ok", false)):
		_bell_left = 0.0
		mark_solved(Kit.t("mg.vent.solved"))
		_update_ui()
		return
	_bell_left = 1.2
	_sfx("mg_c4_alarm_bell", -12.0)
	var w := str(r.get("worst", ""))
	register_fail(Kit.t("mg.vent.fail.%s" % ("low" if int(r.get("dir", -1)) < 0 else "high"),
		{"n": Logic.number_of(w), "name": flap_name(w)}))
	_update_ui()


func _on_solved() -> void:
	_sfx("mg_c4_air_settled", -4.0)


func _move(d: int) -> void:
	if solved or ended:
		return
	cursor = clampi(cursor + d, 0, Logic.FLAPS.size() - 1)
	Kit.ui_sound("move")
	_update_ui()


# ================================================================ hints
func _hint_text(level: int) -> String:
	if logic.done:
		return ""
	if level >= 2:
		var nx: Dictionary = logic.next_move()
		if not nx.is_empty():
			var f := str(nx["flap"])
			return Kit.t("mg.vent.hint.next", {"n": Logic.number_of(f), "name": flap_name(f),
				"act": Kit.t("mg.vent.hint.act.open" if int(nx["dir"]) > 0 else "mg.vent.hint.act.close")})
	return Kit.t("mg.vent.hint.1")


## Settings "puzzle_hints" (like the other puzzles): 0 never a hint, 1 after two refusals (default), 2 the first
## hint at once and one level more with every refusal.
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
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.vent.ctrl.choose")],
		[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN), Kit.t("mg.vent.ctrl.turn")],
		["1–3", Kit.t("mg.vent.ctrl.direct")],
		[Kit.action_key_text("interact"), Kit.t("mg.vent.ctrl.ack")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_t += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	for k in _shake.keys():
		_shake[k] = float(_shake[k]) - delta
		if float(_shake[k]) <= 0.0:
			_shake.erase(k)
	var calm := Kit.reduced_motion()
	var step := 99.0 if calm else delta * float(Logic.MAX_POS) / (ANIM_T * 2.0)
	var fl: Dictionary = logic.flows()
	var follow := 1.0 if calm else 1.0 - exp(-delta * 7.0)
	for f in Logic.FLAPS:
		_anim[f] = move_toward(float(_anim.get(f, 0.0)), float(logic.pos[f]), step)
		_needle[f] = lerpf(float(_needle.get(f, 0.0)), float(fl[f]), follow)
	_fan_a = fmod(_fan_a + delta * (1.2 + logic.total_flow() * 0.32), TAU)
	_bell_left = maxf(0.0, _bell_left - delta)
	if not solved and not logic.balanced():
		_bell_next -= delta
		if _bell_next <= 0.0:
			_bell_next = BELL_EVERY
			_bell_left = 1.0
			_sfx("mg_c4_alarm_bell", -16.0)
	else:
		_bell_next = BELL_EVERY
	if not solved:
		status_auto(Kit.t("mg.vent.status.balanced" if logic.balanced() else "mg.vent.status.idle"))
	_fit_height()
	if _scene != null:
		_scene.queue_redraw()


## The play area is as tall as the stage or the side column, whichever needs more.
func _fit_height() -> void:
	if _area == null or _side == null or _left == null:
		return
	var need := maxf(_left.get_combined_minimum_size().y, _side.get_combined_minimum_size().y)
	if absf(_area.custom_minimum_size.y - need) > 0.5:
		_area.custom_minimum_size.y = need


func _update_ui() -> void:
	if _head == null:
		return
	var ok: bool = logic.balanced()
	_head.text = Kit.t("mg.vent.head.ok" if (ok or logic.done) else "mg.vent.head.alarm").to_upper().replace("ß", "SS")
	var f := selected()
	_flap_label.text = Kit.t("mg.vent.flap_fmt", {"n": Logic.number_of(f), "name": flap_name(f)})
	_desc_label.text = Kit.t("mg.vent.desc." + f)
	var fl: Dictionary = logic.flows()
	var st: Dictionary = logic.states()
	_state_label.text = Kit.t("mg.vent.state_fmt", {"pos": pos_name(int(logic.pos[f])), "ist": _m3(float(fl[f]))}) \
		.to_upper().replace("ß", "SS")
	for g in Logic.FLAPS:
		var c: Array = _cells.get(g, [])
		if c.size() == 2:
			(c[0] as Label).text = _m3(float(fl[g]))
			(c[1] as Label).text = Kit.t("mg.vent.lage.%s" % ["low", "ok", "high"][int(st[g]) + 1])
	if _btn_main != null:
		_btn_main.disabled = false
	if _hint_box != null and _hint_box.visible and not logic.done:
		_hint_label.text = _hint_text(maxi(1, hint_level))


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y:
		restart()
		return true
	if k >= KEY_1 and k <= KEY_3:
		cursor = k - KEY_1
		Kit.ui_sound("move")
		_update_ui()
		return true
	if k >= KEY_KP_1 and k <= KEY_KP_3:
		cursor = k - KEY_KP_1
		Kit.ui_sound("move")
		_update_ui()
		return true
	if _is(event, ["ui_left", "move_left"], true):
		_move(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		_move(1)
		return true
	if _is(event, ["ui_up", "move_up"]):
		if _input_guard <= 0.0:
			move_flap(selected(), 1)
		return true
	if _is(event, ["ui_down", "move_down"]):
		if _input_guard <= 0.0:
			move_flap(selected(), -1)
		return true
	if _is(event, ["ui_accept", "interact"]) or k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE or k == KEY_E \
			or pb == JOY_BUTTON_A:
		if _input_guard <= 0.0:
			acknowledge()
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


## Index of the duct column under an art-px point (-1 = none).
func duct_at(p: Vector2) -> int:
	if p.y < DIAL_Y - DIAL_R - 4.0 or p.y > PLENUM.position.y:
		return -1
	for i in DUCT_X.size():
		if absf(p.x - float(DUCT_X[i])) <= COLUMN_HALF:
			return i
	return -1


func scene_input(event: InputEvent) -> void:
	if ended or solved:
		return
	var p := Vector2.INF
	var d := 0
	if event is InputEventMouseMotion:
		p = (event as InputEventMouseMotion).position / S
	elif event is InputEventMouseButton and event.pressed:
		var mb := event as InputEventMouseButton
		p = mb.position / S
		match mb.button_index:
			MOUSE_BUTTON_LEFT:
				d = 1 if p.y < FLAP_Y else -1
			MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_WHEEL_DOWN:
				d = -1
			MOUSE_BUTTON_WHEEL_UP:
				d = 1
	if not p.is_finite():
		return
	var i := duct_at(p)
	_hover = i
	if i < 0:
		return
	if i != cursor:
		cursor = i
		_update_ui()
	if d != 0 and _input_guard <= 0.0:
		move_flap(selected(), d)


# ================================================================ drawing (art px, x S)
func _px_line(v: Control, a: Vector2, b: Vector2, col: Color, thick := 1) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1:
		var q := a.lerp(b, float(i) / float(maxi(1, n))).round()
		v.draw_rect(Rect2(q.x, q.y, thick, thick), col)


func _px_circle(v: Control, c: Vector2, r: float, col: Color, filled := false) -> void:
	var ri := int(ceil(r))
	for y in range(-ri, ri + 1):
		for x in range(-ri, ri + 1):
			var d := sqrt(float(x * x + y * y))
			if (filled and d <= r) or (not filled and d <= r and d > r - 1.0):
				v.draw_rect(Rect2(c.x + x, c.y + y, 1, 1), col)


func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var hc := Kit.high_contrast()
	var calm := Kit.reduced_motion()
	# the machine-room wall: concrete panels under fluorescent light
	v.draw_rect(Rect2(Vector2.ZERO, STAGE), COL_WALL)
	for x in range(0, int(STAGE.x), 50):
		v.draw_rect(Rect2(x, 0, 1, STAGE.y), COL_WALL2)
	v.draw_rect(Rect2(0, 146, STAGE.x, 4), COL_STEEL[0])
	# fans in their housing, turning with the air they move
	v.draw_rect(Rect2(10, 94, 96, 50), COL_STEEL[1])
	v.draw_rect(Rect2(10, 94, 96, 1), COL_STEEL[3])
	for fc in FAN_C:
		var c: Vector2 = fc
		_px_circle(v, c, FAN_R, COL_STEEL[0], true)
		_px_circle(v, c, FAN_R, COL_STEEL[3])
		for k in 5:
			var a := _fan_a + float(k) * TAU / 5.0
			var tip: Vector2 = c + Vector2(cos(a), sin(a)) * (FAN_R - 3.0)
			var side: Vector2 = c + Vector2(cos(a + 0.35), sin(a + 0.35)) * (FAN_R - 6.0)
			_px_line(v, c, tip, COL_STEEL[4], 2)
			_px_line(v, c, side, COL_STEEL[3], 1)
		_px_circle(v, c, 3.0, COL_PAPER, true)
	# the plenum
	v.draw_rect(PLENUM, COL_STEEL[2])
	v.draw_rect(Rect2(PLENUM.position, Vector2(PLENUM.size.x, 1)), COL_STEEL[4])
	v.draw_rect(Rect2(PLENUM.position.x, PLENUM.end.y - 1, PLENUM.size.x, 1), COL_STEEL[0])
	for x in range(int(PLENUM.position.x) + 8, int(PLENUM.end.x), 24):
		v.draw_rect(Rect2(x, PLENUM.position.y + 3, 1, PLENUM.size.y - 6), COL_STEEL[1])
	v.draw_rect(Rect2(96, 108, 10, 30), COL_STEEL[2])
	# the ducts, their air, their flaps and handles, the dials
	var fl: Dictionary = logic.flows()
	var st: Dictionary = logic.states()
	for i in DUCT_X.size():
		var f := str(Logic.FLAPS[i])
		var x := float(DUCT_X[i])
		var x0 := x - DUCT_W * 0.5
		v.draw_rect(Rect2(x0, DUCT_TOP, DUCT_W, PLENUM.position.y - DUCT_TOP + 1), COL_STEEL[2])
		v.draw_rect(Rect2(x0, DUCT_TOP, 1, PLENUM.position.y - DUCT_TOP), COL_STEEL[4])
		v.draw_rect(Rect2(x0 + DUCT_W - 1, DUCT_TOP, 1, PLENUM.position.y - DUCT_TOP), COL_STEEL[0])
		v.draw_rect(Rect2(x0 + 3, DUCT_TOP + 2, DUCT_W - 6, PLENUM.position.y - DUCT_TOP - 2), COL_STEEL[1])
		for y in range(int(DUCT_TOP) + 12, int(PLENUM.position.y), 16):
			v.draw_rect(Rect2(x0, y, DUCT_W, 1), COL_STEEL[3])
		# air: dots rising with the flow (fewer and slower when the duct starves)
		var flow := float(_needle.get(f, 0.0))
		var n_air := int(clampf(flow * 0.7, 0.0, 10.0))
		var span := PLENUM.position.y - DUCT_TOP - 4.0
		for k in n_air:
			var travel := 0.0 if calm else _t * (6.0 + flow * 2.4)
			var y := PLENUM.position.y - 2.0 - fmod(travel + float(k) * span / float(maxi(1, n_air)), span)
			if absf(y - FLAP_Y) < 3.0:
				continue
			var dx := float((k * 7) % 13) - 6.0
			v.draw_rect(Rect2(x + dx, y, 1, 2), Color(COL_AIR, 0.55))
		# the butterfly flap (closed = across the duct, open = along it)
		var ang := deg_to_rad(80.0 * float(_anim.get(f, 0.0)) / float(Logic.MAX_POS))
		var jolt := 0.0
		if _shake.has(f) and not calm:
			jolt = 1.0 if fmod(float(_shake[f]) * 40.0, 2.0) < 1.0 else -1.0
		var piv := Vector2(x, FLAP_Y)
		var hv := Vector2(cos(ang), -sin(ang)) * (DUCT_W * 0.5 - 3.0)
		_px_line(v, piv - hv, piv + hv, COL_STEEL[4], 2)
		v.draw_rect(Rect2(x - 1, FLAP_Y - 1, 3, 3), COL_PAPER)
		# the handle on the desk side: a quadrant with five notches, the lever on the flap's angle
		var hq := Vector2(x + DUCT_W * 0.5 + 6.0 + jolt, FLAP_Y)
		for p in Logic.MAX_POS + 1:
			var na := deg_to_rad(80.0 * float(p) / float(Logic.MAX_POS))
			v.draw_rect(Rect2((hq + Vector2(cos(na), -sin(na)) * 9.0).round(), Vector2(1, 1)), COL_STEEL[4])
		var tip := hq + Vector2(cos(ang), -sin(ang)) * 7.0
		_px_line(v, hq, tip, COL_STEEL[3], 1)
		v.draw_rect(Rect2(tip.round() - Vector2(1, 1), Vector2(3, 3)), COL_RED if not hc else COL_WHITE)
		# the dial: green band = the design flow from Blatt 3, the needle follows the air
		var dc := Vector2(x, DIAL_Y)
		_px_circle(v, dc, DIAL_R, COL_PAPER, true)
		_px_circle(v, dc, DIAL_R, COL_STEEL[1])
		var lo := (float(Logic.TARGET[f]) - Logic.TOL) / DIAL_MAX
		var hi := (float(Logic.TARGET[f]) + Logic.TOL) / DIAL_MAX
		for s in 24:
			var tt := lerpf(lo, hi, float(s) / 23.0)
			var ba := deg_to_rad(-210.0 + 240.0 * tt)
			for rr in [DIAL_R - 2.0, DIAL_R - 3.0]:
				v.draw_rect(Rect2((dc + Vector2(cos(ba), sin(ba)) * rr).round(), Vector2(1, 1)), COL_GREEN_BAND)
		for s in 7:
			var ta := deg_to_rad(-210.0 + 240.0 * float(s) / 6.0)
			v.draw_rect(Rect2((dc + Vector2(cos(ta), sin(ta)) * (DIAL_R - 1.0)).round(), Vector2(1, 1)), COL_INK)
		var nt := clampf(float(_needle.get(f, 0.0)) / DIAL_MAX, 0.0, 1.05)
		var na2 := deg_to_rad(-210.0 + 240.0 * nt)
		_px_line(v, dc, dc + Vector2(cos(na2), sin(na2)) * (DIAL_R - 3.0), COL_INK if hc else COL_NEEDLE, 1)
		v.draw_rect(Rect2(dc - Vector2(1, 1), Vector2(2, 2)), COL_INK)
		# the duct's own lamp between dial and duct: green in its band, red otherwise
		var lamp_ok := int(st[f]) == 0
		v.draw_rect(Rect2(x - 3, DIAL_Y + DIAL_R + 1, 7, 4), COL_STEEL[1])
		v.draw_rect(Rect2(x - 2, DIAL_Y + DIAL_R + 2, 5, 2), COL_GREEN if lamp_ok else COL_RED)
		# the nameplate on the plenum
		v.draw_rect(Rect2(x - 34, PLENUM.position.y + 6, 68, 14), COL_STEEL[3])
		v.draw_rect(Rect2(x - 33, PLENUM.position.y + 7, 66, 12), COL_STEEL[0])
	# the fault bell and its lamp (rings while any duct is out of its band)
	var ringing := not solved and not logic.balanced()
	var wob := 0.0
	if _bell_left > 0.0 and not calm:
		wob = 1.0 if fmod(_t * 30.0, 2.0) < 1.0 else -1.0
	var bc := BELL + Vector2(wob, 0)
	v.draw_rect(Rect2(BELL.x - 1, 4, 3, 8), COL_STEEL[3])
	for y in range(0, 11):
		var w := int(round(sqrt(maxf(0.0, 121.0 - float((10 - y) * (10 - y))))))
		v.draw_rect(Rect2(bc.x - w, bc.y - 10 + y, w * 2 + 1, 1), Color("c9a35a") if y > 2 else Color("e6c27a"))
	v.draw_rect(Rect2(bc.x - 11, bc.y, 23, 2), Color("8a6a30"))
	v.draw_rect(Rect2(bc.x - 1 - wob * 2.0, bc.y + 2, 3, 3), COL_STEEL[1])
	var blink := ringing and (calm or fmod(_t, 0.8) < 0.45)
	_px_circle(v, Vector2(BELL.x, BELL.y + 14), 4.0, (COL_RED if blink else COL_RED_DIM) if not solved else COL_GREEN, true)
	# Blatt 3 pinned on the wall: the sheet Konrad drew
	v.draw_rect(Rect2(14, 56, 70, 24), COL_PAPER)
	v.draw_rect(Rect2(14, 56, 70, 1), Color("bfb8a2"))
	for r in 4:
		v.draw_rect(Rect2(18, 61 + r * 5, 40 + (r * 13) % 22, 1), Color("7f8a94"))
	v.draw_rect(Rect2(62, 59, 18, 18), Color("c9d6dc"))
	v.draw_rect(Rect2(64, 61, 14, 1), Color("4a6a86"))
	v.draw_rect(Rect2(64, 65, 1, 10), Color("4a6a86"))
	v.draw_rect(Rect2(71, 65, 1, 10), Color("4a6a86"))
	v.draw_rect(Rect2(77, 65, 1, 10), Color("4a6a86"))
	# the cursor around the chosen duct
	if not solved:
		var cx := float(DUCT_X[clampi(cursor, 0, DUCT_X.size() - 1)])
		var col := COL_WHITE if hc else COL_AMBER
		var pulse := 1.0 if (calm or fmod(_t, 1.0) < 0.7) else 0.6
		var top := DIAL_Y - DIAL_R - 3.0
		var rect := Rect2(cx - COLUMN_HALF, top, COLUMN_HALF * 2.0, PLENUM.position.y - top - 2.0)
		if hc:
			v.draw_rect(rect.grow(1.0), Color(0, 0, 0), false, 1.0)
		v.draw_rect(rect, Color(col, pulse), false, 1.0)
		# open above the flap, close below it (the mouse targets)
		v.draw_colored_polygon(PackedVector2Array([Vector2(cx - 24, FLAP_Y - 14), Vector2(cx - 19, FLAP_Y - 21),
			Vector2(cx - 14, FLAP_Y - 14)]), col)
		v.draw_colored_polygon(PackedVector2Array([Vector2(cx - 24, FLAP_Y + 14), Vector2(cx - 19, FLAP_Y + 21),
			Vector2(cx - 14, FLAP_Y + 14)]), col)
	# the German labels (screen pixels, theme font)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var font := v.get_theme_default_font()
	if font == null:
		return
	var fs := 15 if S == 2 else 20
	for i in DUCT_X.size():
		var f := str(Logic.FLAPS[i])
		var sel := i == cursor and not solved
		var tc := (COL_WHITE if hc else COL_AMBER) if sel else COL_LABEL
		var lx := (float(DUCT_X[i]) - 33.0) * S
		var ly := (PLENUM.position.y + 13.0) * S + float(fs) * 0.35
		v.draw_string(font, Vector2(lx, ly), "%d · %s" % [i + 1, flap_name(f)], HORIZONTAL_ALIGNMENT_CENTER,
			66.0 * S, fs, tc if not hc else COL_WHITE)
	var bl := Kit.t("mg.vent.lamp.ok" if (solved or logic.balanced()) else "mg.vent.lamp.alarm")
	v.draw_string(font, Vector2((BELL.x - 30.0) * S, (BELL.y + 28.0) * S), bl,
		HORIZONTAL_ALIGNMENT_CENTER, 60.0 * S, fs, COL_LABEL if not hc else COL_WHITE)
	v.draw_string(font, Vector2(14.0 * S, 89.0 * S), Kit.t("mg.vent.sheet.pin"), HORIZONTAL_ALIGNMENT_LEFT,
		80.0 * S, fs - 3, COL_LABEL if not hc else COL_WHITE)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 60000:
		var nx: Dictionary = logic.next_move()
		if nx.is_empty():
			await _tap(KEY_E)
			await _frames(2)
			continue
		var target := Logic.index_of(str(nx["flap"]))
		var guard := 0
		while cursor != target and guard < 8 and not ended:
			await _tap(KEY_RIGHT if cursor < target else KEY_LEFT)
			guard += 1
		await _tap(KEY_UP if int(nx["dir"]) > 0 else KEY_DOWN)
		await _frames(2)
	await _until(func(): return solved, 4.0)
