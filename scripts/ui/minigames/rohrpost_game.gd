extends "res://scripts/ui/minigames/minigame_base.gd"
## Berlin "Rohrpost" (scenes/ui/minigames/Rohrpost.tscn, explore entry berlin.rohrpost, §12.8).
## At the information desk of the reading room hangs the switch board of the archive's house tube system (1938).
## Since the renovation nothing from the porter's lodge arrives here. Three capsules, three boards of rising
## difficulty: turn the diverter knobs so that the capsule from the lodge reaches the reading room, then call it.
## The capsule rushes through the brass tubes; a wrong setting sends it to another office (it comes back), jams it
## in a knob or sticks it in a frozen line. What each capsule brings is shown on the desk beside the board.
## Logic: rohrpost_logic.gd (boards from assets/ui/minigames/rohrpost/rohrpost_layout.json). Art: tools/pixelgen/
## gen_mg_rohrpost.py (stored x3; drawn x3 or x2 when the panel is short). Sounds: mg_tube_* (mg_audio_r7_kb.py).
## Keys: arrows / WASD / d-pad choose a knob, Space / E / pad A turn it, Enter / pad X / pad Y call the capsule,
## R puts the knobs of this board back, Esc / pad B gives up. Mouse: click a knob (right click turns it back),
## the button calls the capsule.

const Logic := preload("res://scripts/ui/minigames/rohrpost_logic.gd")
const ART := "res://assets/ui/minigames/rohrpost/"
const SPEED := 150.0             # art px per second
const DELIVERED_HOLD := 2.6      # the note is read before the next capsule comes
const RETURN_HOLD := 1.4         # a wrong capsule comes back
const HINT_RESERVE := 84.0
const OPEN_GUARD := 0.35

var logic = Logic.new()
var selected := 0
var stage: Control
var _tex: Dictionary = {}
var _tight_font: FontVariation = null   # plates whose name would run off the board (see _plate)
var _send_btn: Button
var _p_rush: AudioStreamPlayer
var _px := 3
var _k := 1.0
var _board_pos := Vector2.ZERO
var _side_rect := Rect2()
var _state := "ready"            # ready -> travel -> (delivered | returning) -> ready
var _state_t := 0.0
var _run: Dictionary = {}
var _pts := PackedVector2Array()
var _seg_len: Array = []
var _len := 0.0
var _dist := 0.0
var _lit: Dictionary = {}        # station id -> seconds its lamp stays lit
var _turn_flash: Dictionary = {} # diverter -> seconds
var _hover := -1
var _anim := 0.0
var _board_fails := 0
var _guard := 0.0
var _hc := false
var _note_t := 0.0               # seconds since the newest note appeared
var _compact := false            # tight panel: older notes on one line (empty slips are one line anyway)


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
	set_texts("mg.tube.kicker", "mg.tube.title", "mg.tube.subtitle", "mg.tube.instruction")
	for b in logic.boards:
		var n := "rohrpost_board_%d" % int(b.get("id", 1))
		_tex[n] = Kit.optional_tex(ART + n + ".png")
	for k in ["rohrpost_knob", "rohrpost_capsule", "rohrpost_lamp"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	_hc = Kit.high_contrast()
	stage = Stage.new()
	stage.game = self
	stage.mouse_filter = Control.MOUSE_FILTER_STOP
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	Kit.full_rect(stage)
	area.add_child(stage)
	_send_btn = _add_button(Kit.t("mg.tube.btn.send"), send_capsule, 300, true)
	_p_rush = _loop_player("res://assets/audio/sfx/mg_tube_rush.wav")


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_guard = OPEN_GUARD
	if not bool(context.get("auto", false)):
		_hint_now()


func _on_open() -> void:
	if _p_rush != null and _p_rush.stream != null and not _p_rush.playing:
		_p_rush.play()


func _on_end() -> void:
	if _p_rush != null:
		_p_rush.stop()


func _reset_game() -> void:
	logic.reset()
	selected = 0
	_state = "ready"
	_state_t = 0.0
	_run = {}
	_pts = PackedVector2Array()
	_lit = {}
	_board_fails = 0
	_note_t = 0.0
	relayout()


## R / "Neu anfangen": only the knobs of the current board go back (delivered capsules stay delivered).
func restart() -> void:
	if solved or ended or _state != "ready":
		return
	Kit.ui_sound("page")
	logic.reset_board()
	set_status("")
	_redraw()


# ================================================================ layout
func _board_size() -> Vector2:
	var bs: Array = logic.data.get("board_size", [286, 142])
	return Vector2(float(bs[0]), float(bs[1]))


func relayout() -> void:
	if stage == null:
		return
	var avail := stage.size
	var reserve := 0.0 if (_hint_box != null and _hint_box.visible) else HINT_RESERVE
	var bsz := _board_size()
	var side_min := 520.0
	var gap := 56.0
	var lead := 40.0                  # room for the plates that stand out on the left
	_px = 3
	for p in [3, 2, 1]:                # x1 only as the very last resort (a tiny panel)
		_px = p
		if lead + bsz.x * int(p) + gap + side_min <= avail.x and bsz.y * int(p) <= avail.y - reserve:
			break
	var side_w := clampf(avail.x - lead - bsz.x * _px - gap - 40.0, side_min, 760.0)
	var w := lead + bsz.x * _px + gap + side_w
	var h := bsz.y * _px
	var ox := floorf(maxf(0.0, (avail.x - w) / 2.0)) + lead
	var oy := floorf(maxf(0.0, (avail.y - reserve - h) / 2.0))
	_board_pos = Vector2(ox, oy)
	_side_rect = Rect2(Vector2(ox + bsz.x * _px + gap, oy), Vector2(side_w, maxf(h, avail.y - reserve - oy)))
	# the side column keeps at least the normal text size; when that does not fit it switches to a compact
	# list (older notes on one line) before anything shrinks below 100 %
	var hgt := _side_rect.size.y
	_compact = false
	_k = Kit.text_scale()
	while _k > 1.0 and _side_height(_k) > hgt:
		_k -= 0.05
	if _side_height(_k) > hgt:
		_compact = true
		_k = Kit.text_scale()
		while _k > 0.8 and _side_height(_k) > hgt:
			_k -= 0.05
	_redraw()


func _fs(base: float) -> int:
	return maxi(9, int(roundf(base * _k * _px / 3.0)))


## Labels on the board (station plates, knob numbers) never get smaller than their normal size, even at x2.
func _fs_board(base: float) -> int:
	return maxi(int(base), _fs(base))


func _s(v: float) -> float:
	return roundf(v * _px / 3.0)


func _art(p: Vector2) -> Vector2:
	return _board_pos + p * _px


func _side_height(k: float) -> float:
	var f := Kit.font("fv_serif")
	var w := _side_rect.size.x - 48.0
	var hgt := 24.0 + 30.0 * k + 12.0
	hgt += f.get_multiline_string_size(Kit.t("mg.tube.route"), HORIZONTAL_ALIGNMENT_LEFT, w, int(22 * k)).y + 8.0
	hgt += f.get_multiline_string_size(_board_note(), HORIZONTAL_ALIGNMENT_LEFT, w, int(19 * k)).y + 24.0
	hgt += 20.0 * k + 10.0                                   # "Angekommen"
	var tallest := 0.0
	for bi in logic.boards.size():
		var txt := Kit.t(str(logic.boards[bi].get("content", "")))
		var th := f.get_multiline_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, w - 24.0, int(19 * k)).y + 32.0
		tallest = maxf(tallest, th)
		if not _compact:
			hgt += th
	if _compact:                                             # older notes on one line, the newest in full
		hgt += (logic.boards.size() - 1) * (19.0 * k + 32.0) + tallest
	return hgt


func _board_note() -> String:
	return Kit.t(str(logic.board().get("note", "")))


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_guard = maxf(0.0, _guard - delta)
	_note_t += delta
	for k in _lit.keys():
		_lit[k] = float(_lit[k]) - delta
		if float(_lit[k]) <= 0.0:
			_lit.erase(k)
	for k in _turn_flash.keys():
		_turn_flash[k] = float(_turn_flash[k]) - delta
		if float(_turn_flash[k]) <= 0.0:
			_turn_flash.erase(k)
	_state_t += delta
	match _state:
		"travel":
			var ease_v := clampf(_state_t / 0.3, 0.25, 1.0)
			_dist = minf(_len, _dist + SPEED * ease_v * delta)
			if _dist >= _len:
				_end_travel()
		"delivered":
			if _state_t >= DELIVERED_HOLD:
				if logic.next_board():
					_state = "ready"
					_state_t = 0.0
					selected = 0
					_board_fails = 0
					if _hint_box != null:
						_hint_box.visible = false
					hint_level = 0
					Kit.ui_sound("page")
					clear_status_hold()
					set_status(Kit.t("mg.tube.status.next"))
					_status_hold = 1.8
					_hint_now()
					relayout()
				elif not solved:
					mark_solved(Kit.t("mg.tube.solved"))
		"returning":
			if _state_t >= RETURN_HOLD:
				_state = "ready"
				_state_t = 0.0
	if _p_rush != null:
		var target := -6.0 if _state == "travel" else -70.0
		_p_rush.volume_db = move_toward(_p_rush.volume_db, target, (90.0 if _state == "travel" else 45.0) * delta)
		_p_rush.pitch_scale = 0.9 + 0.2 * clampf(_state_t / 0.6, 0.0, 1.0) if _state == "travel" else 1.0
	if hint_level >= 2 and _hint_box != null and _hint_box.visible:
		_hint_label.text = _hint_text(hint_level)
	if _send_btn != null:
		_send_btn.disabled = _state != "ready" or solved
	_update_status()
	_redraw()


func _update_status() -> void:
	if solved:
		return
	match _state:
		"ready":
			status_auto(Kit.t("mg.tube.status.ready"))
		"travel":
			status_auto(Kit.t("mg.tube.status.travel"))


func _redraw() -> void:
	if stage != null:
		stage.queue_redraw()


# ================================================================ actions
func turn_selected(dir := 1) -> void:
	if ended or solved or _state != "ready" or logic.diverters().is_empty():
		return
	logic.turn(selected, dir)
	_turn_flash[selected] = 0.25
	_sfx("mg_tube_turn", -2.0)
	clear_status_hold()
	_redraw()


func send_capsule() -> void:
	if ended or solved or _state != "ready":
		return
	_run = logic.send()
	_pts = logic.polyline(_run)
	_seg_len = []
	_len = 0.0
	for i in range(1, _pts.size()):
		var l := _pts[i - 1].distance_to(_pts[i])
		_seg_len.append(l)
		_len += l
	_dist = 0.0
	_state = "travel"
	_state_t = 0.0
	_sfx("mg_tube_bell", -6.0)
	_sfx("mg_tube_send", -2.0)
	clear_status_hold()


func _end_travel() -> void:
	var res := str(_run.get("result", ""))
	var station := str(_run.get("station", ""))
	if res == "arrive":
		_lit[station] = 2.4
		_sfx("mg_tube_arrive", -1.0)
	else:
		_sfx("mg_tube_stuck", -2.0)
	if bool(_run.get("ok", false)):
		_state = "delivered"
		_state_t = 0.0
		_note_t = 0.0
		Kit.ui_sound("page")
		clear_status_hold()
		set_status(Kit.t("mg.tube.status.arrived"))
		_status_hold = DELIVERED_HOLD
		relayout()
		return
	_state = "returning"
	_state_t = 0.0
	var text := ""
	match res:
		"arrive":
			text = Kit.t("mg.tube.fail." + station) if Kit.has_key("mg.tube.fail." + station) else Kit.t("mg.tube.fail.lost")
		"jam":
			text = Kit.t("mg.tube.fail.jam", {"n": int(_run.get("diverter", 0)) + 1})
		"frozen":
			text = Kit.t("mg.tube.fail.frozen")
		_:
			text = Kit.t("mg.tube.fail.lost")
	register_fail(text)


func register_fail(text: String) -> void:
	fails += 1
	_board_fails += 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	var after := _hints_after()
	if after >= 0 and _board_fails >= after:
		var was := _hint_box.visible
		show_hint(maxi(1, _board_fails - after + 1))
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
	if level <= 1:
		return Kit.t("mg.tube.hint.1")
	var wrong: Array = logic.wrong_diverters()
	if wrong.is_empty():
		return Kit.t("mg.tube.hint.3")
	return Kit.t("mg.tube.hint.2", {"n": int(wrong[0]) + 1})


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT) + "|" + Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN),
			Kit.t("mg.tube.ctrl.select")],
		[Kit.key_name(KEY_SPACE), Kit.t("mg.tube.ctrl.turn")],
		[Kit.key_name(KEY_ENTER), Kit.t("mg.tube.ctrl.send")],
		["R", Kit.t("mg.tube.ctrl.reset")]]


# ================================================================ input
func _div_pos(di: int) -> Vector2:
	return logic.cell_center(logic.diverter_cell(di))


## Nearest knob in direction `dir` from the selected one (-1: none there).
func nav_target(from: int, dir: Vector2) -> int:
	var best := -1
	var best_score := INF
	var p0 := _div_pos(from)
	for i in logic.diverters().size():
		if i == from:
			continue
		var d := _div_pos(i) - p0
		var along := d.dot(dir)
		if along <= 0.5:
			continue
		var perp := absf(d.cross(dir))
		var score := along + perp * 2.2
		if score < best_score:
			best_score = score
			best = i
	if best < 0 and logic.diverters().size() > 1:
		# nothing that way: step through the knobs in reading order, so every knob can always be reached
		var order := _reading_order()
		var step := 1 if (dir == Vector2.RIGHT or dir == Vector2.DOWN) else -1
		best = int(order[posmod(order.find(from) + step, order.size())])
	return best


func _reading_order() -> Array:
	var order: Array = range(logic.diverters().size())
	order.sort_custom(func(a, b):
		var ca: Vector2i = logic.diverter_cell(a)
		var cb: Vector2i = logic.diverter_cell(b)
		return ca.y < cb.y or (ca.y == cb.y and ca.x < cb.x))
	return order


func _game_input(event: InputEvent) -> bool:
	if _guard > 0.0 and (event is InputEventKey or event is InputEventJoypadButton) and event.is_pressed():
		return true
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R:
		restart()
		return true
	if k == KEY_ENTER or k == KEY_KP_ENTER or pb == JOY_BUTTON_X or pb == JOY_BUTTON_Y:
		send_capsule()
		return true
	var d := Vector2.ZERO
	if _is(event, ["ui_left", "move_left"], true):
		d = Vector2.LEFT
	elif _is(event, ["ui_right", "move_right"], true):
		d = Vector2.RIGHT
	elif _is(event, ["ui_up", "move_up"], true):
		d = Vector2.UP
	elif _is(event, ["ui_down", "move_down"], true):
		d = Vector2.DOWN
	if d != Vector2.ZERO:
		if _state == "ready":
			var nt := nav_target(selected, d)
			if nt >= 0:
				selected = nt
				Kit.ui_sound("tick")
			_redraw()
		return true
	if _is(event, ["interact", "ui_accept"]):
		turn_selected(1)
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _knob_at(p: Vector2) -> int:
	for i in logic.diverters().size():
		if p.distance_to(_art(_div_pos(i))) <= 11.0 * _px:
			return i
	return -1


func stage_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseMotion:
		var h := _knob_at((event as InputEventMouseMotion).position)
		if h != _hover:
			_hover = h
			_redraw()
	elif event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		var mb := event as InputEventMouseButton
		var kn := _knob_at(mb.position)
		if kn >= 0 and _state == "ready":
			selected = kn
			if mb.button_index == MOUSE_BUTTON_LEFT:
				turn_selected(1)
			elif mb.button_index == MOUSE_BUTTON_RIGHT:
				turn_selected(-1)


# ================================================================ drawing
func _col(normal: Color, hc: Color) -> Color:
	return hc if _hc else normal


func draw_stage(v: Control) -> void:
	var b := logic.board()
	if b.is_empty():
		return
	var bt: Texture2D = _tex.get("rohrpost_board_%d" % int(b.get("id", 1)))
	var bsz := _board_size()
	if bt != null:
		v.draw_texture_rect(bt, Rect2(_board_pos, bsz * _px), false)
	_draw_stations(v)
	_draw_knobs(v)
	_draw_capsule(v)
	_draw_side(v)


func _plate(v: Control, anchor: Vector2, side: String, text: String, target: bool, lit: bool) -> void:
	var f: Font = Kit.font("fv_label")
	var fs := _fs_board(19)
	var tw := f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var pad := _s(10)
	var ph := float(fs) + _s(12)
	var gap := _s(10)
	if side == "E" and anchor.x + gap + tw + pad * 2.0 + _s(16) > _board_pos.x + _board_size().x * _px:
		# a long name (e.g. the English „Reading room“) stays on the board: tighter letters, never a smaller size
		f = _tight_label_font(f)
		tw = f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var pw := tw + pad * 2.0 + _s(16)
	var r := Rect2()
	match side:
		"E":
			r = Rect2(Vector2(anchor.x + gap, anchor.y - ph / 2.0), Vector2(pw, ph))
		"W":
			r = Rect2(Vector2(anchor.x - gap - pw, anchor.y - ph / 2.0), Vector2(pw, ph))
		_:
			r = Rect2(Vector2(anchor.x + _s(16), anchor.y - ph / 2.0), Vector2(pw, ph))
	r.position = r.position.round()
	var fill := _col(Kit.C_PAPER, Color.WHITE)
	v.draw_rect(Rect2(r.position + Vector2(_s(3), _s(3)), r.size), Color(0, 0, 0, 0.45))
	v.draw_rect(r, fill)
	var border := _col(Color("c29245"), Color.BLACK) if target else _col(Kit.C_INK_DIM, Color.BLACK)
	v.draw_rect(r, border, false, maxf(2.0, _s(3) if target else _s(2)))
	# pilot lamp at the left end of the plate
	var lt: Texture2D = _tex.get("rohrpost_lamp")
	var lamp_c := Vector2(r.position.x + pad + _s(4), r.get_center().y)
	if lt != null:
		var lsz := Vector2(8, 8) * _px
		v.draw_texture_rect_region(lt, Rect2(lamp_c - lsz / 2.0, lsz), Rect2(Vector2(24 if lit else 0, 0), Vector2(24, 24)))
	if lit:
		v.draw_circle(lamp_c, _s(18), Color(Kit.C_AMBER, 0.25))
	v.draw_string(f, Vector2(r.position.x + pad + _s(16), r.position.y + _s(6) + fs * 0.85), text, HORIZONTAL_ALIGNMENT_LEFT,
		-1, fs, _col(Kit.C_INK, Color.BLACK))


## The plate font with the letter spacing of the board's own lettering removed (built once).
func _tight_label_font(base: Font) -> Font:
	if _tight_font == null:
		_tight_font = FontVariation.new()
		_tight_font.base_font = base
		_tight_font.spacing_glyph = 0
		if base is FontVariation:
			_tight_font.base_font = (base as FontVariation).base_font
			_tight_font.variation_opentype = (base as FontVariation).variation_opentype
			_tight_font.fallbacks = (base as FontVariation).fallbacks
	return _tight_font


func _draw_stations(v: Control) -> void:
	var b := logic.board()
	var src: Dictionary = b.get("source", {})
	if not src.is_empty():
		var m := logic.source_mouth()
		_plate(v, _art(m), str(src["side"]), Kit.t("mg.tube.station.source"), false, _state == "travel" and _state_t < 0.5)
	for s in b.get("stations", []):
		var id := str(s["id"])
		var mp := logic.mouth(Vector2i(int(s["cell"][0]), int(s["cell"][1])), str(s["side"]))
		_plate(v, _art(mp), str(s["side"]), Kit.t("mg.tube.station." + id), id == logic.target(), _lit.has(id))


func _draw_knobs(v: Control) -> void:
	var kt: Texture2D = _tex.get("rohrpost_knob")
	var frames: Array = logic.data.get("knob_frames", ["WE", "NS", "NE", "ES", "SW", "WN"])
	var ks := float(logic.data.get("knob_size", 18))
	var f := Kit.font("fv_label")
	var fs := _fs_board(16)
	var wrong: Array = logic.wrong_diverters() if hint_level >= 2 and _state == "ready" else []
	for i in logic.diverters().size():
		var c := _art(_div_pos(i))
		var pr := logic.pair(i)
		var fi := frames.find(pr)
		if fi < 0:
			fi = frames.find(pr[1] + pr[0])
		if kt != null and fi >= 0:
			var dst := Rect2((c - Vector2(ks, ks) * _px / 2.0).round(), Vector2(ks, ks) * _px)
			v.draw_texture_rect_region(kt, dst, Rect2(Vector2(fi * ks * 3.0, 0), Vector2(ks, ks) * 3.0))
		var ring := 12.5 * _px
		if not wrong.is_empty() and int(wrong[0]) == i:
			v.draw_arc(c, ring + _s(4), 0, TAU, 40, Color(Kit.C_STAMP, 0.55 + 0.4 * _wave(6.0)), maxf(2.0, _s(4)))
		if i == selected and _state == "ready" and not solved:
			var a := 0.75 + 0.25 * _wave(5.0)
			v.draw_arc(c, ring, 0, TAU, 48, Color(0, 0, 0, 0.6), maxf(5.0, _s(8)))
			v.draw_arc(c, ring, 0, TAU, 48, Color(_col(Kit.C_AMBER, Color("ffd84a")), a), maxf(3.0, _s(5)))
		elif i == _hover:
			v.draw_arc(c, ring, 0, TAU, 40, Color(Kit.C_PAPER, 0.5), maxf(2.0, _s(2)))
		if _turn_flash.has(i):
			v.draw_arc(c, ring - _s(6), 0, TAU, 40, Color(Kit.C_AMBER, float(_turn_flash[i]) / 0.25), maxf(2.0, _s(3)))
		# knob number on a small enamel tag left of the housing (clear of the station plates above and below)
		var lab := str(i + 1)
		var tw := f.get_string_size(lab, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var nr := Rect2(Vector2(c.x - 17.5 * _px - tw / 2.0 - _s(5), c.y - float(fs) * 0.62), Vector2(tw + _s(10), float(fs) * 1.24)).abs()
		nr.position = nr.position.round()
		v.draw_rect(nr, _col(Color(Kit.C_NIGHT, 0.85), Color.BLACK))
		v.draw_rect(nr, Color(_col(Color("c29245"), Color("ffd84a")), 0.8), false, maxf(1.0, _s(2)))
		v.draw_string(f, Vector2(nr.position.x, c.y + float(fs) * 0.36), lab, HORIZONTAL_ALIGNMENT_CENTER, nr.size.x, fs,
			_col(Kit.C_AMBER, Color("ffd84a")))


func _capsule_at(d: float) -> Array:
	## [position, direction] at distance d along the run
	var acc := 0.0
	for i in _seg_len.size():
		var l: float = _seg_len[i]
		if acc + l >= d or i == _seg_len.size() - 1:
			var t := clampf((d - acc) / maxf(0.001, l), 0.0, 1.0)
			return [_pts[i].lerp(_pts[i + 1], t), (_pts[i + 1] - _pts[i]).normalized()]
		acc += l
	return [_pts[0] if _pts.size() > 0 else Vector2.ZERO, Vector2.RIGHT]


func _draw_capsule(v: Control) -> void:
	if _pts.size() < 2 or not (_state in ["travel", "delivered", "returning"]):
		return
	var alpha := 1.0
	if _state == "returning":
		alpha = clampf(1.0 - (_state_t - 0.5) / 0.6, 0.0, 1.0)
	elif _state == "delivered":
		alpha = clampf(1.0 - (_state_t - 0.9) / 0.5, 0.0, 1.0)
	if alpha <= 0.0:
		return
	var pd: Array = _capsule_at(_dist)
	var p: Vector2 = pd[0]
	var dir: Vector2 = pd[1]
	if _state == "returning" and str(_run.get("result", "")) != "arrive":
		p += Vector2(_wave(40.0), 0) * (0.6 if _state_t < 0.4 else 0.0)
	var ct: Texture2D = _tex.get("rohrpost_capsule")
	var cs := float(logic.data.get("capsule_size", 12))
	var frame := 0 if absf(dir.x) >= absf(dir.y) else 1
	var at := (_art(p.round()) - Vector2(cs, cs) * _px / 2.0).round()
	v.draw_circle(_art(p), 9.0 * _px, Color(Kit.C_AMBER, 0.16 * alpha))
	v.draw_circle(_art(p), 6.0 * _px, Color(Kit.C_AMBER, 0.18 * alpha))
	if ct != null:
		v.draw_texture_rect_region(ct, Rect2(at, Vector2(cs, cs) * _px), Rect2(Vector2(frame * cs * 3.0, 0), Vector2(cs, cs) * 3.0),
			Color(1, 1, 1, alpha))
	# a short rush of air behind it
	if _state == "travel":
		for k in range(1, 4):
			var q: Array = _capsule_at(maxf(0.0, _dist - k * 5.0))
			v.draw_circle(_art(q[0]), _s(3) * (1.0 - k * 0.22), Color(Kit.C_PAPER, 0.18 - k * 0.04))


func _draw_side(v: Control) -> void:
	var r := _side_rect
	var f_k := Kit.font("fv_label")
	var f_b := Kit.font("fv_serif")
	var f_i := Kit.font("fv_serif_italic")
	var paper := _col(Kit.C_PAPER, Color.WHITE)
	var ink := _col(Kit.C_INK, Color.BLACK)
	var inkd := _col(Kit.C_INK_DIM, Color("202020"))
	var pad := 24.0
	var w := r.size.x - pad * 2.0
	var y := r.position.y
	# card: which capsule, the route, the board note
	var fsk := int(roundf(20 * _k))
	var fsr := int(roundf(22 * _k))
	var fsn := int(roundf(19 * _k))
	var note := _board_note()
	var h1 := 24.0 + fsk + 12.0 + f_b.get_multiline_string_size(Kit.t("mg.tube.route"), HORIZONTAL_ALIGNMENT_LEFT, w, fsr).y + 8.0 \
		+ f_b.get_multiline_string_size(note, HORIZONTAL_ALIGNMENT_LEFT, w, fsn).y + 18.0
	var card := Rect2(Vector2(r.position.x, y), Vector2(r.size.x, h1))
	v.draw_rect(Rect2(card.position + Vector2(6, 6), card.size), Color(0, 0, 0, 0.35))
	v.draw_rect(card, paper)
	v.draw_rect(card, _col(Kit.C_PAPER_D, Color.BLACK), false, 2.0)
	var yy := y + 20.0 + fsk
	var shown_n := mini(logic.board_i + 1, logic.board_count())
	v.draw_string(f_k, Vector2(r.position.x + pad, yy), Kit.t("mg.tube.capsule", {"n": shown_n, "total": logic.board_count()}).to_upper().replace("ß", "SS"),
		HORIZONTAL_ALIGNMENT_LEFT, w, fsk, _col(Kit.C_COPPER_D, Color.BLACK))
	yy += 12.0
	v.draw_multiline_string(f_b, Vector2(r.position.x + pad, yy + fsr), Kit.t("mg.tube.route"), HORIZONTAL_ALIGNMENT_LEFT, w, fsr,
		-1, ink)
	yy += f_b.get_multiline_string_size(Kit.t("mg.tube.route"), HORIZONTAL_ALIGNMENT_LEFT, w, fsr).y + 8.0
	v.draw_multiline_string(f_i, Vector2(r.position.x + pad, yy + fsn), note, HORIZONTAL_ALIGNMENT_LEFT, w, fsn, -1, inkd)
	y += h1 + 22.0
	# what the capsules brought: one slip per capsule, empty until it has arrived
	v.draw_string(f_k, Vector2(r.position.x, y + fsk), Kit.t("mg.tube.delivered").to_upper().replace("ß", "SS"), HORIZONTAL_ALIGNMENT_LEFT, -1, fsk,
		_col(Kit.C_COPPER_L, Color.WHITE))
	y += fsk + 10.0
	var shown := _notes_shown()
	for n in logic.board_count():
		if n < shown:
			var bi: int = logic.delivered[n]
			var txt := Kit.t(str(logic.boards[bi].get("content", "")))
			var newest: bool = n == shown - 1
			var lines := 1 if (_compact and not newest) else -1
			var th := f_i.get_multiline_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, w - 24.0, fsn, lines).y
			var slip := Rect2(Vector2(r.position.x + 12.0, y), Vector2(r.size.x - 12.0, th + 22.0))
			var a := clampf(_note_t / 0.35, 0.0, 1.0) if newest else 1.0
			if not Kit.reduced_motion():
				slip.position.x += (1.0 - a) * 40.0
			v.draw_rect(Rect2(slip.position + Vector2(4, 4), slip.size), Color(0, 0, 0, 0.3 * a))
			v.draw_rect(slip, Color(_col(Kit.C_PAPER_M, Color.WHITE), a))
			v.draw_rect(Rect2(slip.position, Vector2(6, slip.size.y)), Color(_col(Color("c29245"), Color.BLACK), a))
			v.draw_multiline_string(f_i, Vector2(slip.position.x + 20.0, slip.position.y + 10.0 + fsn * 0.9), txt,
				HORIZONTAL_ALIGNMENT_LEFT, w - 24.0, fsn, lines, Color(ink, a))
			y += slip.size.y + 10.0
		else:
			var ph := float(fsn) + 24.0
			var empty := Rect2(Vector2(r.position.x + 12.0, y), Vector2(r.size.x - 12.0, ph))
			v.draw_rect(empty, Color(_col(Kit.C_PAPER, Color.WHITE), 0.05))
			_dashed_rect(v, empty, Color(_col(Kit.C_PAPER_D, Color.WHITE), 0.45))
			var slot_key := "mg.tube.slot.travel" if _state == "travel" and n == logic.board_i else "mg.tube.slot"
			v.draw_string(f_i, Vector2(empty.position.x + 20.0, empty.position.y + 12.0 + fsn * 0.8),
				Kit.t(slot_key, {"n": n + 1}), HORIZONTAL_ALIGNMENT_LEFT, w - 24.0, fsn, Color(_col(Kit.C_TEXT_DIM, Color.WHITE), 0.8))
			y += ph + 10.0


## Notes on the desk: every delivered capsule, except the one still rushing to the reading room.
func _notes_shown() -> int:
	var n: int = logic.delivered.size()
	if _state == "travel" and bool(_run.get("ok", false)):
		n -= 1
	return maxi(0, n)


func _dashed_rect(v: Control, r: Rect2, col: Color) -> void:
	var dash := 10.0
	var x := r.position.x
	while x < r.end.x:
		var x2 := minf(x + dash, r.end.x)
		v.draw_line(Vector2(x, r.position.y), Vector2(x2, r.position.y), col, 2.0)
		v.draw_line(Vector2(x, r.end.y), Vector2(x2, r.end.y), col, 2.0)
		x += dash * 2.0
	var y := r.position.y
	while y < r.end.y:
		var y2 := minf(y + dash, r.end.y)
		v.draw_line(Vector2(r.position.x, y), Vector2(r.position.x, y2), col, 2.0)
		v.draw_line(Vector2(r.end.x, y), Vector2(r.end.x, y2), col, 2.0)
		y += dash * 2.0



## Pulsing highlights; constant when the player asked for reduced motion.
func _wave(speed: float) -> float:
	return 0.0 if Kit.reduced_motion() else sin(_anim * speed)

# ================================================================ synthetic solve (real-input driver)
## Arrow key that brings the selection from `from` closest to `target` (the target itself if one key reaches it).
func nav_key_toward(from: int, target: int) -> int:
	var keys := {KEY_RIGHT: Vector2.RIGHT, KEY_LEFT: Vector2.LEFT, KEY_UP: Vector2.UP, KEY_DOWN: Vector2.DOWN}
	var best_key := -1
	var best_d := _div_pos(from).distance_to(_div_pos(target))
	for k in keys:
		var nt := nav_target(from, keys[k])
		if nt == target:
			return int(k)
		if nt >= 0 and _div_pos(nt).distance_to(_div_pos(target)) < best_d:
			best_d = _div_pos(nt).distance_to(_div_pos(target))
			best_key = int(k)
	return best_key if best_key >= 0 else KEY_RIGHT


func _select(target: int) -> void:
	var guard := 0
	while selected != target and guard < 16 and not ended:
		var key := nav_key_toward(selected, target)
		if key < 0:
			return
		await _tap(key)
		guard += 1


func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 120000:
		if _state != "ready" or _guard > 0.0:
			await _frames(2)
			continue
		var need: Array = logic.turns_needed()
		for di in need.size():
			if int(need[di]) == 0:
				continue
			await _select(di)
			for n in int(need[di]):
				await _tap(KEY_SPACE)
		await _tap(KEY_ENTER)
		await _until(func(): return _state != "travel", 10.0)
		await _until(func(): return _state == "ready" or solved, 6.0)
