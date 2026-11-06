extends "res://scripts/ui/minigames/minigame_base.gd"
## Karsk "Der Morsetaster" (scenes/ui/minigames/MorseKey.tscn, explore entry karsk.morse, §12.8).
## The duty officer of the signal box has gone for tea; the telegraph rings. The Morse register prints the
## dispatcher's telegram on its tape while the sounder clicks and the call lamp flashes. Alexei takes the routine
## groups down by ear; the last two words are decoded by the player with the chart on the wall ("АЗБУКА МОРЗЕ"):
## look at the group on the tape, pick the field with the same pattern. Then the receipt ПР is keyed on the key
## (short press = dot, hold = dash, pauses never matter) and the line answers. Logic: morse_logic.gd.
## Art: assets/ui/minigames/morse/ (tools/pixelgen/gen_mg_morse.py, stored x3; drawn x3 or x2 when the panel is
## short, e.g. with a large text scale). Sounds: mg_morse_* (tools/audiogen/mg_audio_r7_kb.py).
## Keys: decode — arrows / WASD / d-pad move on the chart, Enter / Space / E / pad A write the letter, R / pad Y
## repeats the current letter; receipt — hold Space / Enter / E / pad A (or the mouse on the key), R plays the
## receipt once. Esc / pad B gives up (nothing is lost). Mouse: hover + click on the chart.

const Logic := preload("res://scripts/ui/minigames/morse_logic.gd")
const ART := "res://assets/ui/minigames/morse/"
const KEY_ACTIONS := ["interact", "ui_accept"]
const KEY_MAX := 2.5             # a press is released automatically after this long (lost key-up)
const OPEN_GUARD := 0.35         # key-downs right after opening belong to the key that opened the game
const TAPE_SPEED := 2.0 / Logic.ROUTINE_UNIT   # art px per second (a dot of the fast routine = 2 px)
const REPLAY_UNIT := 0.11
const HINT_RESERVE := 84.0       # keep room for the hint plate so the scale never jumps when it appears
const C_PENCIL := Color("4f534c")
const C_PRINT := Color("7a2a26")
const C_TAPE_INK := Color("2b3c50")
const TALL_FORM_TOP := 30.0      # art px: the form pulled up over the register for large text

var logic = Logic.new()
var layout: Dictionary = {}
var cursor := Vector2i(0, 0)
var stage: Control
var _tex: Dictionary = {}
var _repeat_btn: Button
var _p_inker: AudioStreamPlayer
var _px := 3                     # pixel scale of the art (3, or 2 when the panel is short)
var _k := 1.0                    # text scale used for the drawn texts (text_scale, shrunk to fit if needed)
var _origin := Vector2.ZERO
var _desk_pos := Vector2.ZERO
var _table_pos := Vector2.ZERO
var _press_t := -1.0             # >= 0 while the key is held
var _press_src := ""
var _guard := 0.0
var _anim := 0.0
var _flash: Dictionary = {}      # chart index -> seconds of the red "wrong" flash
var _elem_flash := 0.0           # receipt: wrong element flash
var _ok_flash := 0.0
var _replay: Array = []
var _replay_t := -1.0
var _local_on := false
var _phase_fails := 0
var _last_phase := ""
var _hover := -1
var _hc := false
var _written: Dictionary = {}    # letter index -> seconds since its pencil letter appeared
var _measuring := false          # _draw_form only measures (no drawing)
var _tall_form := false
var _tape_t := 0.0               # the register's clockwork: runs while signals come in, stops after them
var _tape_reply0 := -1.0


class Stage extends Control:
	var game: Node

	func _draw() -> void:
		game.draw_stage(self)

	func _gui_input(event: InputEvent) -> void:
		game.stage_input(event)

	func _notification(what: int) -> void:
		if what == NOTIFICATION_RESIZED:
			game.relayout()


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.morse.kicker", "mg.morse.title", "mg.morse.subtitle", "mg.morse.instruction")
	has_restart = false
	var lj = Kit.json(ART + "morse_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["morse_desk", "morse_table", "morse_sounder", "morse_key", "morse_lamp", "morse_tape"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	_hc = Kit.high_contrast()
	stage = Stage.new()
	stage.game = self
	stage.mouse_filter = Control.MOUSE_FILTER_STOP
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	Kit.full_rect(stage)
	area.add_child(stage)
	_repeat_btn = _add_button(Kit.t("mg.morse.btn.repeat"), _replay_current, 330, true)
	_p_inker = _loop_player("res://assets/audio/sfx/mg_morse_inker.wav")


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_guard = OPEN_GUARD
	if not bool(context.get("auto", false)):
		_hint_now()


func _on_open() -> void:
	if _p_inker != null and _p_inker.stream != null and not _p_inker.playing:
		_p_inker.play()


func _on_end() -> void:
	if _p_inker != null:
		_p_inker.stop()


func _reset_game() -> void:
	logic.reset()
	cursor = Vector2i(0, 0)
	_press_t = -1.0
	_flash = {}
	_written = {}
	_replay_t = -1.0
	_local_on = false
	_phase_fails = 0
	_last_phase = logic.phase
	_tape_t = 0.0
	_tape_reply0 = -1.0
	_redraw()


# ================================================================ layout (fits the panel: x3, else x2)
func relayout() -> void:
	if stage == null or layout.is_empty():
		return
	var avail := stage.size
	var reserve := 0.0 if (_hint_box != null and _hint_box.visible) else HINT_RESERVE
	var desk_sz: Array = layout.get("desk_size", [300, 144])
	var tab_sz: Array = layout.get("table_size", [222, 144])
	var gap := 40.0
	_px = 3
	for p in [3, 2, 1]:                # x1 only as the very last resort (a tiny panel)
		_px = p
		var w: float = (float(desk_sz[0]) + float(tab_sz[0])) * int(p) + gap
		var h: float = maxf(float(desk_sz[1]), float(tab_sz[1])) * int(p)
		if w <= avail.x and h <= avail.y - reserve:
			break
	var w2 := (float(desk_sz[0]) + float(tab_sz[0])) * _px + gap
	var h2 := maxf(float(desk_sz[1]), float(tab_sz[1])) * _px
	_origin = Vector2(floorf(maxf(0.0, (avail.x - w2) / 2.0)), floorf(maxf(0.0, (avail.y - reserve - h2) / 2.0)))
	_desk_pos = _origin
	_table_pos = _origin + Vector2(float(desk_sz[0]) * _px + gap, 0)
	# drawn text: honour the text scale; the form grows over the register before any text shrinks
	_k = Kit.text_scale()
	_tall_form = false
	if _form_height(_k) > _form_rect().size.y:
		_tall_form = true
	while _k > 0.8 and _form_height(_k) > _form_rect().size.y:
		_k -= 0.05
	_redraw()


func _s(v: float) -> float:
	return roundf(v * _px / 3.0)


func _fs(base: float) -> int:
	return maxi(9, int(roundf(base * _k * _px / 3.0)))


## Where the telegram form lies: on the desk in front of the apparatus, or — when a large text scale needs the
## room — pulled up over the register (the lamp, sounder and key stay visible).
func _form_rect() -> Rect2:
	var f: Array = layout.get("form", [8, 80, 232, 142])
	var top := float(f[1]) if not _tall_form else TALL_FORM_TOP
	return Rect2(_desk_pos + Vector2(float(f[0]), top) * _px, Vector2(float(f[2]) - float(f[0]), float(f[3]) - top) * _px)


func _form_height(k: float) -> float:
	var keep := _k
	_k = k
	_measuring = true
	var h := _draw_form(null)
	_measuring = false
	_k = keep
	return h


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_guard = maxf(0.0, _guard - delta)
	_ok_flash = maxf(0.0, _ok_flash - delta)
	_elem_flash = maxf(0.0, _elem_flash - delta)
	for k in _flash.keys():
		_flash[k] = float(_flash[k]) - delta
		if float(_flash[k]) <= 0.0:
			_flash.erase(k)
	for k in _written.keys():
		_written[k] = float(_written[k]) + delta
	if _press_t >= 0.0:
		_press_t += delta
		if _press_t > KEY_MAX:
			_key_release()
	_tick_replay(delta)
	if logic.t < logic.end_t + 0.6 or logic.phase == "reply":
		_tape_t += delta
	for e in logic.step(delta):
		var ev := str(e)
		if ev == "bell":
			_sfx("mg_morse_bell", -6.0)
		elif ev == "on" or ev == "reply_on":
			_sfx("mg_morse_down", -3.0)
		elif ev == "off" or ev == "reply_off":
			_sfx("mg_morse_up", -6.0)
		elif ev.begins_with("arrived:"):
			var li := int(ev.get_slice(":", 1))
			if bool(logic.letters[li]["auto"]):
				_written[li] = 0.0
		elif ev == "done":
			mark_solved(Kit.t("mg.morse.solved"))
	if _p_inker != null:
		var running: bool = logic.transmitting() or logic.phase == "reply"
		var target := -11.0 if running else -60.0
		_p_inker.volume_db = move_toward(_p_inker.volume_db, target, (60.0 if running else 40.0) * delta)
	if logic.phase != _last_phase:
		_on_phase(logic.phase)
	if _hint_box != null and _hint_box.visible and hint_level >= 1:
		_hint_label.text = _hint_text(hint_level)      # the hint follows the letter that is wanted now
	_update_status()
	_redraw()


func _on_phase(ph: String) -> void:
	_last_phase = ph
	_phase_fails = 0
	if _hint_box != null:
		_hint_box.visible = false
	hint_level = 0
	if ph == "reply":
		_tape_reply0 = _tape_t - logic.reply_t
	if ph == "answer":
		clear_status_hold()
		Kit.ui_sound("page")
		if _repeat_btn != null:
			_repeat_btn.text = Kit.t("mg.morse.btn.demo")
		_hint_now()
	relayout()


func _tick_replay(delta: float) -> void:
	if _replay_t < 0.0:
		return
	var r0 := _replay_t
	_replay_t += delta
	var on := false
	for e in _replay:
		if float(e[0]) > r0 and float(e[0]) <= _replay_t:
			_sfx("mg_morse_down", -5.0)
		if float(e[1]) > r0 and float(e[1]) <= _replay_t:
			_sfx("mg_morse_up", -8.0)
		if _replay_t >= float(e[0]) and _replay_t < float(e[1]):
			on = true
	_local_on = on
	if _replay.is_empty() or _replay_t > float(_replay[-1][1]) + 0.2:
		_replay_t = -1.0
		_local_on = false


func _update_status() -> void:
	if solved:
		return
	match logic.phase:
		"decode":
			if logic.can_pick():
				status_auto(Kit.t("mg.morse.status.pick", {"n": logic.cursor + 1, "total": logic.targets.size(),
					"code": pretty(logic.wanted_code())}))
			else:
				status_auto(Kit.t("mg.morse.status.listen"))
		"answer":
			status_auto(Kit.t("mg.morse.status.key", {"code": _ack_pretty()}))
		"reply":
			status_auto(Kit.t("mg.morse.status.reply"))


## "·–·" style rendering of a code (thin spaces between the elements).
static func pretty(code: String) -> String:
	var parts: PackedStringArray = []
	for i in code.length():
		parts.append("·" if code[i] == "." else "–")
	return " ".join(parts)


func _ack_pretty() -> String:
	var parts: PackedStringArray = []
	for a in logic.ack_codes:
		parts.append("%s %s" % [a[0], pretty(str(a[1]))])
	return "   ".join(parts)


func _redraw() -> void:
	if stage != null:
		stage.queue_redraw()


# ================================================================ actions
func _pick(i: int) -> void:
	if ended or solved or logic.phase != "decode":
		return
	if i < 0 or i >= Logic.TABLE.size():
		return
	if not logic.can_pick():
		set_status(Kit.t("mg.morse.status.listen"))
		_status_hold = 1.2
		return
	var ch := str(Logic.TABLE[i][0])
	var r: Dictionary = logic.pick(ch)
	if bool(r.get("ok", false)):
		_written[int(r["letter"])] = 0.0
		_ok_flash = 0.35
		Kit.ui_sound("tick")
		clear_status_hold()
	elif str(r.get("reason", "")) == "wrong":
		_flash[i] = 0.7
		register_fail(Kit.t("mg.morse.fail.letter", {"code": pretty(str(r["code"])), "letter": ch,
			"other": pretty(str(r["other"]))}))


func _key_press(src: String) -> void:
	if ended or solved or logic.phase != "answer" or _press_t >= 0.0 or _replay_t >= 0.0:
		return
	_press_t = 0.0
	_press_src = src
	_sfx("mg_morse_key_down", -2.0)
	_sfx("mg_morse_down", -10.0)


func _key_release() -> void:
	if _press_t < 0.0:
		return
	var d := _press_t
	_press_t = -1.0
	_sfx("mg_morse_key_up", -3.0)
	_sfx("mg_morse_up", -12.0)
	var r: Dictionary = logic.key(d)
	if not bool(r.get("ok", false)):
		var reason := str(r.get("reason", ""))
		if reason == "dot" or reason == "dash":
			_elem_flash = 0.6
			register_fail(Kit.t("mg.morse.fail." + reason, {"letter": str(r.get("letter", ""))}))
	else:
		_ok_flash = 0.25
		clear_status_hold()


func _replay_current() -> void:
	if ended or solved:
		return
	if logic.phase == "answer":
		if _press_t >= 0.0:
			return
		var codes: Array = []
		for a in logic.ack_codes:
			codes.append(str(a[1]))
		_start_replay(codes)
		return
	if logic.phase != "decode" or not logic.can_pick():
		return
	if logic.transmitting():
		set_status(Kit.t("mg.morse.status.busy"))
		_status_hold = 1.6
		return
	_start_replay([logic.wanted_code()])


func _start_replay(codes: Array) -> void:
	_replay = []
	var at := 0.25
	for c in codes:
		var tl: Array = Logic.timeline(str(c), REPLAY_UNIT, at)
		_replay.append_array(tl)
		at = float(tl[-1][1]) + REPLAY_UNIT * 3.0
	_replay_t = 0.0


func register_fail(text: String) -> void:
	fails += 1
	_phase_fails += 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	var after := _hints_after()
	if after >= 0 and _phase_fails >= after:
		var was := _hint_box.visible
		show_hint(maxi(1, _phase_fails - after + 1))
		if not was:
			relayout()


## Settings "puzzle_hints": 0 never, 1 after two refusals (default), 2 at once.
func _hints_after() -> int:
	match int(Kit.setting("puzzle_hints", 1)):
		0:
			return -1
		2:
			return 0
	return HINT_AFTER


func _hint_now() -> void:
	if _hints_after() == 0 and _hint_box != null and not _hint_box.visible:
		show_hint(1)
		relayout()


func _hint_text(level: int) -> String:
	if logic.phase == "decode":
		if level <= 1:
			return Kit.t("mg.morse.hint.1", {"n": logic.wanted_code().length()})
		return Kit.t("mg.morse.hint.2")
	return Kit.t("mg.morse.hint.key.1" if level <= 1 else "mg.morse.hint.key.2")


func _controls() -> Array:
	if logic.phase == "decode":
		return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT) + "|" + Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN),
				Kit.t("mg.morse.ctrl.pick")],
			[Kit.action_key_text("interact"), Kit.t("mg.morse.ctrl.write")],
			["R", Kit.t("mg.morse.ctrl.repeat")]]
	return [[Kit.key_name(KEY_SPACE), Kit.t("mg.morse.ctrl.key")], ["R", Kit.t("mg.morse.ctrl.demo")]]


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if logic.phase == "answer" or logic.phase == "reply":
		if _is(event, KEY_ACTIONS):
			if _guard <= 0.0:
				_key_press("key")
			return true
		for a in KEY_ACTIONS:
			if InputMap.has_action(a) and event.is_action_released(a):
				if _press_src == "key":
					_key_release()
				return true
		if k == KEY_R or pb == JOY_BUTTON_Y or pb == JOY_BUTTON_X:
			_replay_current()
			return true
		if event is InputEventKey:
			return not _is(event, ["cancel", "ui_cancel"])
		return false
	if k == KEY_R or pb == JOY_BUTTON_Y or pb == JOY_BUTTON_X:
		_replay_current()
		return true
	var d := Vector2i.ZERO
	if _is(event, ["ui_left", "move_left"], true):
		d = Vector2i(-1, 0)
	elif _is(event, ["ui_right", "move_right"], true):
		d = Vector2i(1, 0)
	elif _is(event, ["ui_up", "move_up"], true):
		d = Vector2i(0, -1)
	elif _is(event, ["ui_down", "move_down"], true):
		d = Vector2i(0, 1)
	if d != Vector2i.ZERO:
		cursor = Vector2i(posmod(cursor.x + d.x, Logic.COLS), posmod(cursor.y + d.y, Logic.ROWS))
		_hover = -1
		Kit.ui_sound("tick")
		_redraw()
		return true
	if _is(event, KEY_ACTIONS):
		if _guard <= 0.0:
			_pick(cursor.y * Logic.COLS + cursor.x)
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _cell_rect(i: int) -> Rect2:
	var g: Array = layout.get("table_grid", [6, 13, 30, 20])
	var c := Logic.cell_of(i)
	return Rect2(_table_pos + Vector2(float(g[0]) + c.x * float(g[2]), float(g[1]) + c.y * float(g[3])) * _px,
		Vector2(float(g[2]), float(g[3])) * _px)


func _key_rect() -> Rect2:
	var kp: Array = layout.get("key", [238, 94])
	var kf: Array = layout.get("key_frame", [54, 24])
	return Rect2(_desk_pos + Vector2(float(kp[0]), float(kp[1])) * _px, Vector2(float(kf[0]), float(kf[1])) * _px)


func stage_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseMotion:
		var hv := -1
		for i in Logic.TABLE.size():
			if _cell_rect(i).has_point((event as InputEventMouseMotion).position):
				hv = i
		if hv != _hover:
			_hover = hv
			if hv >= 0 and logic.phase == "decode":
				cursor = Logic.cell_of(hv)
			_redraw()
	elif event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			if logic.phase == "answer" and _key_rect().grow(6).has_point(mb.position):
				_key_press("mouse")
				return
			for i in Logic.TABLE.size():
				if _cell_rect(i).has_point(mb.position):
					cursor = Logic.cell_of(i)
					_pick(i)
					return
		elif _press_src == "mouse":
			_key_release()


# ================================================================ drawing
func _col(normal: Color, hc: Color) -> Color:
	return hc if _hc else normal


func draw_stage(v: Control) -> void:
	_draw_desk(v)
	_draw_form(v)
	_draw_table(v)


func _frame(tex: Texture2D, i: int, fw: float, fh: float) -> Rect2:
	return Rect2(Vector2(i * fw, 0) * 3.0, Vector2(fw, fh) * 3.0)


func _draw_sprite(v: Control, name: String, at_key: String, frame_key: String, f: int) -> void:
	var t: Texture2D = _tex.get(name)
	if t == null:
		return
	var at: Array = layout.get(at_key, [0, 0])
	var fr: Array = layout.get(frame_key, [16, 16])
	v.draw_texture_rect_region(t, Rect2(_desk_pos + Vector2(float(at[0]), float(at[1])) * _px,
		Vector2(float(fr[0]), float(fr[1])) * _px), _frame(t, f, float(fr[0]), float(fr[1])))


func _line_on() -> bool:
	return logic.signal_on() or _local_on or _press_t >= 0.0


func _draw_desk(v: Control) -> void:
	var dt: Texture2D = _tex.get("morse_desk")
	var dsz: Array = layout.get("desk_size", [300, 144])
	if dt != null:
		v.draw_texture_rect(dt, Rect2(_desk_pos, Vector2(float(dsz[0]), float(dsz[1])) * _px), false)
	else:
		v.draw_rect(Rect2(_desk_pos, Vector2(900, 432)), Kit.C_NAVY)
	# ink marks on the register's tape: they appear at the inking wheel and run to the right with the tape
	var tp: Array = layout.get("tape", [129, 52, 179, 55])
	var head := float(tp[0])
	var tend := float(tp[2])
	var my := float(tp[1]) + 1.0
	var ink := _col(C_TAPE_INK, Color.BLACK)
	var t: float = logic.t
	var lists: Array = []            # element times on the tape clock
	for l in logic.letters:
		if float(l["t0"]) <= t:
			lists.append(l["els"])
	if _tape_reply0 >= 0.0:
		var shifted: Array = []
		for e in logic.reply_els:
			shifted.append([float(e[0]) + _tape_reply0, float(e[1]) + _tape_reply0])
		lists.append(shifted)
	var now := _tape_t
	var signal_t: float = t if _tape_reply0 < 0.0 else _tape_reply0 + float(logic.reply_t)
	for els in lists:
		for e in els:
			var on := float(e[0])
			if on > now or on > maxf(signal_t, t):
				continue
			var off := minf(float(e[1]), now)
			var x_new := head + (now - off) * TAPE_SPEED
			var x_old := head + (now - on) * TAPE_SPEED
			if x_new > tend:
				continue
			x_old = minf(x_old, tend)
			var x0 := floorf(x_new)
			var x1 := maxf(x0 + 1.0, floorf(x_old))
			v.draw_rect(Rect2(_desk_pos + Vector2(x0, my) * _px, Vector2(x1 - x0, 2.0) * _px), ink)
	var on_now := _line_on()
	_draw_sprite(v, "morse_sounder", "sounder", "sounder_frame", 1 if on_now else 0)
	_draw_sprite(v, "morse_key", "key", "key_frame", 1 if _press_t >= 0.0 else 0)
	_draw_sprite(v, "morse_lamp", "lamp", "lamp_frame", 1 if on_now else 0)
	if on_now:
		var lp: Array = layout.get("lamp", [262, 5])
		var c := _desk_pos + (Vector2(float(lp[0]), float(lp[1])) + Vector2(10, 10)) * _px
		for i in 3:
			v.draw_circle(c, (16.0 + i * 10.0) * _px / 3.0, Color(Kit.C_AMBER, 0.16 - i * 0.045))
	# the key invites a press in the receipt phase
	if logic.phase == "answer" and not solved:
		var kr := _key_rect().grow(_s(6))
		var a := 0.45 + 0.35 * _wave(4.0)
		v.draw_rect(kr, Color(_col(Kit.C_COPPER_L, Color("ffd84a")), a), false, maxf(2.0, _s(4)))
		var f := Kit.font("fv_label")
		var lab := Kit.t("mg.morse.key").to_upper().replace("ß", "SS")
		v.draw_string(f, Vector2(kr.position.x, kr.position.y - _s(8)), lab, HORIZONTAL_ALIGNMENT_CENTER, kr.size.x,
			_fs(18), _col(Kit.C_AMBER, Color("ffd84a")))


# ---------------------------------------------------------------- the telegram form on the desk
## Drawing helpers that do nothing while the form is only being measured (_form_height uses the same code path).
func _r(v: Control, rect: Rect2, col: Color, filled := true, width := -1.0) -> void:
	if not _measuring:
		v.draw_rect(rect, col, filled, width)


func _t(v: Control, f: Font, pos: Vector2, text: String, align: int, width: float, size: int, col: Color) -> void:
	if not _measuring:
		v.draw_string(f, pos, text, align, width, size, col)


func _ln(v: Control, a: Vector2, b: Vector2, col: Color, width: float) -> void:
	if not _measuring:
		v.draw_line(a, b, col, width)


func _strip_layout(gi: int, x0: float) -> Array:
	## [{li, x0, x1, marks: [[x, w, element]]}] for the letters of group gi starting at x0 (screen px)
	var out: Array = []
	var x := x0
	var dot := _s(4)
	var dash := _s(12)
	var gap := _s(4)
	var lgap := _s(14)
	for li in logic.letters.size():
		var l: Dictionary = logic.letters[li]
		if int(l["group"]) != gi:
			continue
		var marks: Array = []
		var start := x
		var code := str(l["code"])
		for i in code.length():
			var w := dot if code[i] == "." else dash
			marks.append([x, w, i])
			x += w + (gap if i < code.length() - 1 else 0.0)
		out.append({"li": li, "x0": start, "x1": x, "marks": marks})
		x += lgap
	return out


func _draw_strip(v: Control, gi_list: Array, x0: float, y: float) -> Dictionary:
	## the glued tape strip of the groups (marks only where already received); returns {"pos": letter -> item, "end": x}
	var pos := {}
	var x := x0 + _s(8)
	var sh := _s(14)
	for gi in gi_list:
		var ll: Array = _strip_layout(int(gi), x)
		for item in ll:
			pos[int(item["li"])] = item
		if not ll.is_empty():
			x = float(ll[-1]["x1"]) + _s(22)
	var strip_end := x - _s(22) + _s(8)
	if _measuring:
		return {"pos": pos, "end": strip_end}
	var rect := Rect2(Vector2(x0, y), Vector2(strip_end - x0, sh))
	var tt: Texture2D = _tex.get("morse_tape")
	if tt != null and not _hc:
		v.draw_texture_rect(tt, rect, true)
	else:
		v.draw_rect(rect, Color.WHITE if _hc else Color("f1f4ec"))
	v.draw_rect(Rect2(rect.position + Vector2(0, rect.size.y), Vector2(rect.size.x, _s(2))), Color(0, 0, 0, 0.25))
	var ink := _col(C_TAPE_INK, Color.BLACK)
	var cur := logic.current_letter()
	if logic.phase == "decode" and pos.has(cur) and logic.arrived(cur):
		var it: Dictionary = pos[cur]
		var fr2 := Rect2(Vector2(float(it["x0"]) - _s(4), y - _s(3)), Vector2(float(it["x1"]) - float(it["x0"]) + _s(8), sh + _s(6)))
		v.draw_rect(fr2, Color(_col(Kit.C_AMBER, Color("ffd84a")), 0.35))
		v.draw_rect(fr2, _col(Kit.C_COPPER, Color.BLACK), false, maxf(2.0, _s(2)))
	for li in pos:
		var els: Array = logic.letters[li]["els"]
		for m in pos[li]["marks"]:
			var e: Array = els[int(m[2])]
			if logic.t < float(e[0]):
				continue
			var frac := 1.0
			if logic.t < float(e[1]):
				frac = clampf((logic.t - float(e[0])) / (float(e[1]) - float(e[0])), 0.0, 1.0)
			v.draw_rect(Rect2(Vector2(float(m[0]), y + (sh - _s(6)) / 2.0), Vector2(maxf(1.0, float(m[1]) * frac), _s(6))), ink)
	return {"pos": pos, "end": strip_end}


## Draws the telegram form (or only measures it when _measuring); returns the height it needs.
func _draw_form(v: Control) -> float:
	var fr := _form_rect()
	var paper := _col(Kit.C_PAPER, Color.WHITE)
	_r(v, Rect2(fr.position + Vector2(_s(6), _s(6)), fr.size), Color(0, 0, 0, 0.35))
	_r(v, fr, paper)
	_r(v, fr, _col(Kit.C_PAPER_D, Color.BLACK), false, maxf(1.0, _s(2)))
	var f_print := Kit.font("fv_mono")
	var f_pencil := Kit.font("fv_serif_italic")
	var f_gloss := Kit.font("fv_serif")
	var c_print := _col(C_PRINT, Color.BLACK)
	var c_pencil := _col(C_PENCIL, Color.BLACK)
	var c_gloss := _col(Kit.C_INK_DIM, Color("202020"))
	var sc := _px / 3.0
	var pad := _s(14)
	var x0 := fr.position.x + pad
	var x1 := fr.end.x - pad
	var y := fr.position.y + 6 * sc
	var fs1 := _fs(15)
	var fs2 := _fs(21)
	var fsg := _fs(17)
	var fs5 := _fs(15)
	# printed head
	_t(v, f_print, Vector2(x0, y + fs1), Kit.t("mg.morse.form.head"), HORIZONTAL_ALIGNMENT_LEFT, x1 - x0, fs1, c_print)
	_t(v, f_print, Vector2(x0, y + fs1), Kit.t("mg.morse.form.time"), HORIZONTAL_ALIGNMENT_RIGHT, x1 - x0, fs1, c_print)
	y += fs1 + 8 * sc
	_ln(v, Vector2(x0, y - 4 * sc), Vector2(x1, y - 4 * sc), Color(c_print, 0.5), maxf(1.0, _s(2)))
	# the line taken down before the duty officer went for tea, with Alexei's translation
	var l1 := Kit.t("mg.morse.form.line1")
	var g1 := Kit.t("mg.morse.gloss.1")
	_t(v, f_pencil, Vector2(x0, y + fs2), l1, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, c_pencil)
	var w1 := f_pencil.get_string_size(l1, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2).x
	var wg1 := f_gloss.get_string_size(g1, HORIZONTAL_ALIGNMENT_LEFT, -1, fsg).x
	if x0 + w1 + _s(24) + wg1 <= x1:
		_t(v, f_gloss, Vector2(x0, y + fs2), g1, HORIZONTAL_ALIGNMENT_RIGHT, x1 - x0, fsg, c_gloss)
		y += fs2 + 8 * sc
	else:
		y += fs2 + 3 * sc
		_t(v, f_gloss, Vector2(x0, y + fsg), g1, HORIZONTAL_ALIGNMENT_LEFT, x1 - x0, fsg, c_gloss)
		y += fsg + 8 * sc
	# routine strip (auto) with Alexei's pencil letters
	var sa := _draw_strip(v, [0, 1], x0 - _s(8), y)
	var pos_a: Dictionary = sa["pos"]
	var base_a := y + _s(14) + 4 * sc + fs2
	for li in pos_a:
		if not logic.letter_known(li):
			continue
		var item: Dictionary = pos_a[li]
		var cx := (float(item["x0"]) + float(item["x1"])) / 2.0
		var a := clampf(float(_written.get(li, 1.0)) / 0.25, 0.0, 1.0)
		_t(v, f_pencil, Vector2(cx - 30, base_a), str(logic.letters[li]["ch"]), HORIZONTAL_ALIGNMENT_CENTER, 60, fs2, Color(c_pencil, a))
	var g2 := Kit.t("mg.morse.gloss.2")
	var letters_end := x0
	for li in pos_a:
		letters_end = maxf(letters_end, (float(pos_a[li]["x0"]) + float(pos_a[li]["x1"])) / 2.0 + fs2 * 0.45)
	var g2_inline := letters_end + _s(20) + f_gloss.get_string_size(g2, HORIZONTAL_ALIGNMENT_LEFT, -1, fsg).x <= x1
	var show_g2 := logic.group_text(1) == "24311"
	y = base_a + 8 * sc
	if g2_inline:
		if show_g2:
			_t(v, f_gloss, Vector2(x0, base_a), g2, HORIZONTAL_ALIGNMENT_RIGHT, x1 - x0, fsg, c_gloss)
	else:
		if show_g2:
			_t(v, f_gloss, Vector2(x0, y - 4 * sc + fsg), g2, HORIZONTAL_ALIGNMENT_RIGHT, x1 - x0, fsg, c_gloss)
		y += fsg
	# target strip with the slots the player fills in
	var sb := _draw_strip(v, [2, 3], x0 - _s(8), y)
	var pos_b: Dictionary = sb["pos"]
	var slot_y := y + _s(14) + 3 * sc
	var slot_h := fs2 + 10 * sc
	var cur_li := logic.current_letter()
	var hl := _col(Kit.C_COPPER, Color("c08000"))
	var slots_end := x0
	for li in pos_b:
		var item2: Dictionary = pos_b[li]
		var w := maxf(float(item2["x1"]) - float(item2["x0"]) + _s(6), fs2 * 0.85 + _s(8))
		var cx2 := (float(item2["x0"]) + float(item2["x1"])) / 2.0
		var r := Rect2(Vector2(roundf(cx2 - w / 2.0), slot_y), Vector2(roundf(w), slot_h))
		slots_end = maxf(slots_end, r.end.x)
		_r(v, r, _col(Color(Kit.C_PAPER_M, 0.55), Color(0.92, 0.92, 0.92)))
		if li == cur_li and logic.phase == "decode":
			var pulse := 0.6 + 0.4 * _wave(5.0)
			_r(v, r, Color(hl, pulse if logic.arrived(li) else 0.35), false, maxf(2.0, _s(3)))
		else:
			_r(v, r, Color(_col(Kit.C_PAPER_D, Color.BLACK), 0.8), false, maxf(1.0, _s(1)))
		if logic.letter_known(li):
			var a2 := clampf(float(_written.get(li, 1.0)) / 0.2, 0.0, 1.0)
			_t(v, f_pencil, Vector2(r.position.x, r.position.y + fs2 + 3 * sc), str(logic.letters[li]["ch"]),
				HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs2, Color(_col(Kit.C_INK, Color.BLACK), a2))
	var g3 := Kit.t("mg.morse.gloss.3")
	var g3_inline := slots_end + _s(12) + f_gloss.get_string_size(g3, HORIZONTAL_ALIGNMENT_LEFT, -1, fsg).x <= x1
	y = slot_y + slot_h + 8 * sc
	if g3_inline:
		if logic.phase != "decode":
			_t(v, f_gloss, Vector2(x0, slot_y + fs2 + 3 * sc), g3, HORIZONTAL_ALIGNMENT_RIGHT, x1 - x0, fsg, _col(Kit.C_STAMP, Color.BLACK))
	else:
		if logic.phase != "decode":
			_t(v, f_gloss, Vector2(x0, y - 4 * sc + fsg), g3, HORIZONTAL_ALIGNMENT_RIGHT, x1 - x0, fsg, _col(Kit.C_STAMP, Color.BLACK))
		y += fsg
	# receipt row: ПРИНЯЛ + the element boxes of ПР + the press meter
	var lx := x0
	var bh := maxf(_s(13), roundf(fs5 * 0.8))
	var row_h := maxf(float(fs5), bh)
	var base5 := y + row_h
	_t(v, f_print, Vector2(lx, base5), Kit.t("mg.morse.form.received"), HORIZONTAL_ALIGNMENT_LEFT, -1, fs5, c_print)
	lx += f_print.get_string_size(Kit.t("mg.morse.form.received"), HORIZONTAL_ALIGNMENT_LEFT, -1, fs5).x + _s(14)
	var done_n: int = logic.ack_confirmed()
	var n := 0
	var by := base5 - bh
	var active: bool = logic.phase == "answer" and not solved
	for ai in logic.ack_codes.size():
		var code := str(logic.ack_codes[ai][1])
		_t(v, f_pencil, Vector2(lx, base5), str(logic.ack_codes[ai][0]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs5,
			Color(c_pencil, 1.0 if logic.ack_letter > ai or logic.phase in ["reply", "done"] else 0.55))
		lx += maxf(_s(22), fs5 * 1.1)
		for ei in code.length():
			var bw := bh if code[ei] == "." else roundf(bh * 2.6)
			var br := Rect2(Vector2(lx, by), Vector2(bw, bh))
			if n < done_n or logic.phase in ["reply", "done"]:
				_r(v, br, _col(C_TAPE_INK, Color.BLACK))
			else:
				_r(v, br, Color(_col(C_TAPE_INK, Color.BLACK), 0.18 if active else 0.1))
				if active and n == done_n:
					var col := Kit.C_STAMP if _elem_flash > 0.0 else hl
					_r(v, br.grow(_s(2)), Color(col, 0.6 + 0.4 * _wave(6.0)), false, maxf(2.0, _s(2)))
			lx += bw + _s(7)
			n += 1
		lx += _s(16)
	if active:
		var mw := _s(170)
		var mr := Rect2(Vector2(minf(lx + _s(10), x1 - mw - _s(70)), by), Vector2(mw, bh))
		_r(v, mr, Color(_col(Kit.C_PAPER_D, Color(0.8, 0.8, 0.8)), 0.8))
		var full := Logic.DASH_AT * 2.0
		var tick := mr.position.x + mw * (Logic.DASH_AT / full)
		if _press_t >= 0.0:
			var fw := mw * clampf(_press_t / full, 0.0, 1.0)
			var dash := _press_t >= Logic.DASH_AT
			_r(v, Rect2(mr.position, Vector2(fw, bh)), _col(Kit.C_STAMP if dash else Kit.C_COPPER, Color.BLACK))
		_ln(v, Vector2(tick, mr.position.y - _s(3)), Vector2(tick, mr.end.y + _s(3)), _col(Kit.C_INK, Color.BLACK), maxf(1.0, _s(2)))
		_r(v, mr, _col(Kit.C_INK_DIM, Color.BLACK), false, maxf(1.0, _s(1)))
		if _press_t >= 0.0:
			var lab := Kit.t("mg.morse.meter.dash" if _press_t >= Logic.DASH_AT else "mg.morse.meter.dot")
			_t(v, f_gloss, Vector2(mr.end.x + _s(10), base5), lab, HORIZONTAL_ALIGNMENT_LEFT, -1, fsg, c_gloss)
	elif logic.phase in ["reply", "done"]:
		_t(v, f_pencil, Vector2(lx + _s(10), base5), Kit.t("mg.morse.form.sign"), HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, c_pencil)
	return base5 + 7 * sc - fr.position.y


# ---------------------------------------------------------------- the chart on the wall
func _draw_pattern(v: Control, code: String, center_x: float, y: float, col: Color) -> void:
	var dot := _s(5)
	var dash := _s(13)
	var gap := _s(4)
	var w := 0.0
	for i in code.length():
		w += (dot if code[i] == "." else dash) + (gap if i > 0 else 0.0)
	var x := roundf(center_x - w / 2.0)
	for i in code.length():
		var ln := dot if code[i] == "." else dash
		v.draw_rect(Rect2(Vector2(x, y), Vector2(ln, dot)), col)
		x += ln + gap


func _draw_table(v: Control) -> void:
	var tt: Texture2D = _tex.get("morse_table")
	var tsz: Array = layout.get("table_size", [222, 144])
	var trect := Rect2(_table_pos, Vector2(float(tsz[0]), float(tsz[1])) * _px)
	if tt != null and not _hc:
		v.draw_texture_rect(tt, trect, false)
	else:
		v.draw_rect(trect, Color.WHITE if _hc else Kit.C_PAPER)
		if tt != null:
			v.draw_texture_rect(tt, trect, false, Color(1, 1, 1, 0.35))
	var f_letter := Kit.font("fv_serif_bold")
	var f_small := Kit.font("fv_mono")
	var ink := _col(Kit.C_INK, Color.BLACK)
	var dim := _col(Kit.C_INK_DIM, Color("303030"))
	var want := Logic.table_index(str(logic.letters[logic.current_letter()]["ch"])) if logic.current_letter() >= 0 else -1
	var ack_cells := []
	for a in logic.ack_codes:
		ack_cells.append(Logic.table_index(str(a[0])))
	for i in Logic.TABLE.size():
		var r := _cell_rect(i).grow(-_s(2))
		var row: Array = Logic.TABLE[i]
		if _hc:
			v.draw_rect(r, Color.WHITE)
		if hint_level >= 2 and logic.phase == "decode" and i == want and logic.can_pick():
			v.draw_rect(r, Color(Kit.C_AMBER, 0.45 + 0.25 * _wave(5.0)))
		if logic.phase == "answer" and i in ack_cells:
			v.draw_rect(r, Color(Kit.C_AMBER, 0.3))
		if _flash.has(i):
			v.draw_rect(r, Color(Kit.C_STAMP, 0.45 * clampf(float(_flash[i]) / 0.7, 0.0, 1.0)))
		var ls := mini(_fs(26), int(r.size.y * 0.62))
		v.draw_string(f_letter, Vector2(r.position.x + _s(6), r.position.y + ls * 0.95), str(row[0]), HORIZONTAL_ALIGNMENT_LEFT,
			-1, ls, ink)
		var ss := mini(_fs(12), int(r.size.y * 0.3))
		v.draw_string(f_small, Vector2(r.position.x, r.position.y + ss + _s(3)), str(row[2]), HORIZONTAL_ALIGNMENT_RIGHT,
			r.size.x - _s(5), ss, dim)
		_draw_pattern(v, str(row[1]), r.get_center().x, r.end.y - _s(9), ink)
	# cursor
	if logic.phase == "decode" and not solved:
		var cr := _cell_rect(cursor.y * Logic.COLS + cursor.x)
		v.draw_rect(cr.grow(_s(1)), _col(Kit.C_COPPER_L, Color("ffd84a")), false, maxf(3.0, _s(4)))
		if _hc:
			v.draw_rect(cr.grow(_s(4)), Color.BLACK, false, maxf(1.0, _s(2)))



## Pulsing highlights; constant when the player asked for reduced motion.
func _wave(speed: float) -> float:
	return 0.0 if Kit.reduced_motion() else sin(_anim * speed)

# ================================================================ synthetic solve (real-input driver)
func _cursor_to(c: Vector2i) -> void:
	var guard := 0
	while cursor != c and guard < 24 and not ended:
		if cursor.x < c.x:
			await _tap(KEY_RIGHT)
		elif cursor.x > c.x:
			await _tap(KEY_LEFT)
		elif cursor.y < c.y:
			await _tap(KEY_DOWN)
		else:
			await _tap(KEY_UP)
		guard += 1


func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	while logic.phase == "decode" and not ended and Time.get_ticks_msec() - t0 < 90000:
		if not logic.can_pick() or _guard > 0.0:
			await _frames(2)
			continue
		var li: int = logic.current_letter()
		var want := Logic.cell_of(Logic.table_index(str(logic.letters[li]["ch"])))
		await _cursor_to(want)
		await _tap(KEY_ENTER)
		await _frames(2)
	while logic.phase == "answer" and not ended and Time.get_ticks_msec() - t0 < 90000:
		var e: String = logic.ack_expected()
		var hold := 0.08 if e == "." else 0.45
		_key_event(KEY_SPACE, true)
		await _until(func(): return _press_t >= 0.0, 2.0)
		await _until(func(): return _press_t >= hold, hold + 3.0)
		_key_event(KEY_SPACE, false)
		await _until(func(): return _press_t < 0.0, 2.0)
		await _frames(6)
	await _until(func(): return solved, 6.0)
