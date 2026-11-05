extends "res://scripts/ui/minigames/minigame_base.gd"
## Berlin "Das Radio" (scenes/ui/minigames/RadioDial.tscn, explore entry berlin.radio_dial, §12.8).
## The 1955 set in the porter's lodge (assets/ui/minigames/radio*.png, stored x3; geometry radio_layout.json).
## Tune from the Reichssender (red line) to the pencil dot: static thins out, the magic eye closes, a jazz trio
## comes through (mg_radio_* loops, the official station plays berlin_radio_loop). Listen while the porter reads;
## when his paper sinks, the needle must be back on the red line (station key R). Logic: radio_logic.gd.
## Keys: Left/Right (A/D, d-pad, stick) turn — a tap is a fine step, holding turns faster; R / pad Y / pad X =
## station key; Esc gives up. Mouse: drag on the scale, wheel over the set, click the R key.

const Logic := preload("res://scripts/ui/minigames/radio_logic.gd")
const S := 3
const PORTRAIT := "res://assets/characters/porter/portrait.png"
const REICH_LOOP := "res://assets/audio/sfx/berlin_radio_loop.wav"

var logic = Logic.new()
var layout: Dictionary = {}
var _radio_view: Control
var _porter_view: Control
var _meter: Control
var _porter_label: Label
var _tex: Dictionary = {}
var _p_static: AudioStreamPlayer
var _p_jazz: AudioStreamPlayer
var _p_reich: AudioStreamPlayer
var _p_whistle: AudioStreamPlayer
var _paper_y := 40.0
var _surprised := 0.0
var _key_down := 0.0
var _dragging := false


class View extends Control:
	var game: Node
	var kind := ""

	func _draw() -> void:
		game.call("draw_" + kind, self)

	func _gui_input(event: InputEvent) -> void:
		if kind == "radio":
			game.radio_input(event)


func _build_play(area: Control) -> void:
	set_texts("mg.radio.kicker", "mg.radio.title", "mg.radio.subtitle", "mg.radio.instruction")
	has_restart = false
	var lj = Kit.json(DIR + "radio_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["radio.png", "radio_eye.png", "radio_knob.png", "radio_newspaper.png"]:
		_tex[k] = Kit.optional_tex(DIR + k)
	_tex["portrait"] = Kit.optional_tex(PORTRAIT)
	var row := Kit.hbox(56)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	_radio_view = View.new()
	_radio_view.game = self
	_radio_view.kind = "radio"
	_radio_view.mouse_filter = Control.MOUSE_FILTER_STOP
	_radio_view.custom_minimum_size = _tex["radio.png"].get_size() if _tex["radio.png"] != null else Vector2(864, 468)
	_radio_view.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_radio_view)
	var side := Kit.vbox(12)
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(side)
	var frame := Kit.panel("PortraitPanel")
	side.add_child(frame)
	_porter_view = View.new()
	_porter_view.game = self
	_porter_view.kind = "porter"
	_porter_view.clip_contents = true
	_porter_view.custom_minimum_size = Vector2(336, 336)
	_porter_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_porter_view)
	_porter_label = Kit.label("", "KickerLabel")
	_porter_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	side.add_child(_porter_label)
	var ml := Kit.label(Kit.t("mg.radio.listen").to_upper(), "DimLabel")
	ml.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	side.add_child(ml)
	_meter = View.new()
	_meter.game = self
	_meter.kind = "meter"
	_meter.custom_minimum_size = Vector2(336, 27)
	_meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side.add_child(_meter)
	_add_button(Kit.t("mg.radio.btn.preset"), _preset, 320, true)
	_p_static = _loop_player("res://assets/audio/sfx/mg_radio_static.wav")
	_p_jazz = _loop_player("res://assets/audio/sfx/mg_radio_jazz.wav")
	_p_reich = _loop_player(REICH_LOOP)
	_p_whistle = _loop_player("res://assets/audio/sfx/mg_radio_whistle.wav")


func _on_open() -> void:
	for p in [_p_static, _p_jazz, _p_reich, _p_whistle]:
		if p != null and p.stream != null and not p.playing:
			p.play()
	_update_audio()


func _on_end() -> void:
	for p in [_p_static, _p_jazz, _p_reich, _p_whistle]:
		if p != null:
			p.stop()


func _reset_game() -> void:
	logic.reset()
	_paper_y = 40.0
	_surprised = 0.0
	_update_labels()


func restart() -> void:
	_preset()        # the radio has no "start over": R is the station key


func _preset() -> void:
	if solved or ended:
		return
	logic.preset()
	_key_down = 0.25
	_sfx("mg_radio_key", -3.0)
	_redraw()


# ================================================================ per frame
func _tick(delta: float) -> void:
	_key_down = maxf(0.0, _key_down - delta)
	_surprised = maxf(0.0, _surprised - delta)
	if solved:
		logic.needle = move_toward(logic.needle, Logic.REICH, 0.45 * delta)
	else:
		var l := Input.is_action_pressed("ui_left") or Input.is_action_pressed("move_left")
		var r := Input.is_action_pressed("ui_right") or Input.is_action_pressed("move_right")
		if l != r and not _dragging:
			logic.turn(-1 if l else 1, delta)
		else:
			logic.release()
		for e in logic.step(delta):
			match str(e):
				"warn":
					Kit.ui_sound_first(["paper_rustle", "page_turn"])
				"caught":
					_surprised = 1.6
					_sfx("mg_radio_key", -3.0)
					register_fail(Kit.t("mg.radio.fail.caught"))
				"solved":
					mark_solved(Kit.t("mg.radio.solved"))
	# newspaper: up while reading, sinking during the warning, gone while he looks
	var target := 40.0
	if logic.porter == "lowering":
		target = lerpf(40.0, 86.0, 1.0 - logic.porter_t / Logic.WARN)
	elif logic.porter == "looking":
		target = 118.0
	if solved:
		target = 40.0
	_paper_y = move_toward(_paper_y, target, (140.0 if target < _paper_y else 60.0) * delta)
	_update_audio()
	_update_labels()
	_redraw()


func _update_audio() -> void:
	var fs := logic.foreign_signal()
	var rs := logic.reich_signal()
	var st := logic.strength()
	_vol(_p_jazz, fs * 0.95)
	_vol(_p_reich, rs * 0.8)
	_vol(_p_static, clampf(1.0 - st, 0.07, 1.0) * 0.75)
	var ns: Array = logic.nearest_station()
	var d := absf(logic.needle - float(ns[0])) / (3.0 * float(ns[1]))
	if d < 1.0 and st < 0.97 and not solved:
		_vol(_p_whistle, 0.4 * (1.0 - d) * (1.0 - st))
		if _p_whistle:
			_p_whistle.pitch_scale = 0.3 + 1.7 * d
	else:
		_vol(_p_whistle, 0.0)


func _vol(p: AudioStreamPlayer, lin: float) -> void:
	if p != null:
		p.volume_db = linear_to_db(maxf(lin, 0.0001))


func _update_labels() -> void:
	if _porter_label:
		_porter_label.text = (Kit.t("mg.radio.porter") + " · " + Kit.t("mg.radio.porter." + logic.porter)).to_upper()
		var c := Kit.C_TEXT_DIM
		if logic.porter == "lowering":
			c = Kit.C_AMBER
		elif logic.porter == "looking":
			c = Kit.C_COPPER_L
		_porter_label.add_theme_color_override("font_color", c)
	if solved:
		return
	if logic.foreign_signal() >= Logic.CLEAR:
		status_auto(Kit.t("mg.radio.status.foreign"))
	elif logic.foreign_signal() > 0.05:
		status_auto(Kit.t("mg.radio.status.near"))
	elif logic.on_reich():
		status_auto(Kit.t("mg.radio.status.reich"))
	else:
		status_auto(Kit.t("mg.radio.status.static"))


func _redraw() -> void:
	for v in [_radio_view, _porter_view, _meter]:
		if v != null:
			v.queue_redraw()


func _hint_text(level: int) -> String:
	return Kit.t("mg.radio.hint.%d" % clampi(level, 1, 2))


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.radio.ctrl.tune")],
		["R", Kit.t("mg.radio.ctrl.preset")]]


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y or pb == JOY_BUTTON_X:
		_preset()
		return true
	if _is(event, ["ui_left", "move_left"]):
		logic.nudge(-1)
		_redraw()
		return true
	if _is(event, ["ui_right", "move_right"]):
		logic.nudge(1)
		_redraw()
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _needle_from_x(x: float) -> float:
	var x0 := float(layout.get("scale_x0", 26)) * S
	var x1 := float(layout.get("scale_x1", 262)) * S
	return clampf((x - x0) / maxf(1.0, x1 - x0), 0.0, 1.0)


func radio_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseButton and event.pressed:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			logic.nudge(1)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			logic.nudge(-1)
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			var p := mb.position / S
			var keys = layout.get("keys", [])
			if keys is Array and keys.size() >= 5:
				var kr: Array = keys[4]
				if Rect2(kr[0], kr[1], kr[2], kr[3]).grow(2).has_point(p):
					_preset()
					return
			var sc = layout.get("scale", [22, 92, 266, 114])
			if Rect2(sc[0], sc[1] - 6, sc[2] - sc[0], sc[3] - sc[1] + 12).has_point(p):
				_dragging = true
				logic.set_needle(_needle_from_x(mb.position.x))
		_redraw()
	elif event is InputEventMouseButton and not event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_dragging = false
	elif event is InputEventMouseMotion and _dragging:
		logic.set_needle(_needle_from_x((event as InputEventMouseMotion).position.x))
		_redraw()


# ================================================================ drawing
func draw_radio(v: Control) -> void:
	var rt: Texture2D = _tex.get("radio.png")
	if rt != null:
		v.draw_texture(rt, Vector2.ZERO)
	var font := v.get_theme_font("font", "Label")
	var sc: Array = layout.get("scale", [22, 92, 266, 114])
	var x0 := float(layout.get("scale_x0", 26))
	var x1 := float(layout.get("scale_x1", 262))
	# station names on the glass (the far right is blank but for the pencil dot)
	var ink := Color(Kit.C_INK, 0.9)
	var names := [[Logic.REICH, "mg.radio.station.reich"], [Logic.FAINT[0], "mg.radio.station.breslau"],
		[Logic.FAINT[1], "mg.radio.station.wien"]]
	for n in names:
		var cx := (x0 + float(n[0]) * (x1 - x0)) * S
		v.draw_string(font, Vector2(cx - 150, (float(sc[1]) + 9) * S), Kit.t(str(n[1])), HORIZONTAL_ALIGNMENT_CENTER, 300, 17, ink)
	v.draw_string(font, Vector2((float(sc[0]) + 2) * S, (float(sc[1]) + 9) * S), Kit.t("mg.radio.band"), HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(Kit.C_INK_DIM, 0.9))
	# needle (one art pixel wide, on the art grid)
	var nx := roundf(x0 + logic.needle * (x1 - x0)) * S
	v.draw_rect(Rect2(nx, (float(sc[1]) + 1) * S, S, (float(sc[3]) - float(sc[1]) - 2) * S), Color("c0392b"))
	v.draw_rect(Rect2(nx + S, (float(sc[1]) + 1) * S, S, (float(sc[3]) - float(sc[1]) - 2) * S), Color(0, 0, 0, 0.18))
	# magic eye
	var et: Texture2D = _tex.get("radio_eye.png")
	if et != null:
		var fsz := et.get_height()
		var fi := clampi(roundi(logic.strength() * 7.0), 0, 7)
		var ec: Array = layout.get("eye", [236, 30])
		var at := Vector2(float(ec[0]), float(ec[1])) * S - Vector2(fsz, fsz) / 2.0
		v.draw_texture_rect_region(et, Rect2(at, Vector2(fsz, fsz)), Rect2(fi * fsz, 0, fsz, fsz))
	# tuning knob turns with the needle
	var kt: Texture2D = _tex.get("radio_knob.png")
	if kt != null:
		var ks := kt.get_height()
		var ki := int(floor(logic.needle * 40.0)) % 8
		var kc: Array = layout.get("knob", [258, 136])
		var kat := Vector2(float(kc[0]), float(kc[1])) * S - Vector2(ks, ks) / 2.0
		v.draw_texture_rect_region(kt, Rect2(kat, Vector2(ks, ks)), Rect2(ki * ks, 0, ks, ks))
	# key labels; the station key R is pressed briefly
	var keys = layout.get("keys", [])
	if keys is Array:
		for i in keys.size():
			var kr: Array = keys[i]
			var r := Rect2(Vector2(kr[0], kr[1]) * S, Vector2(kr[2], kr[3]) * S)
			if i == 4 and _key_down > 0.0:
				v.draw_rect(Rect2(r.position, Vector2(r.size.x, 6)), Color(Kit.C_NIGHT, 0.55))
			var lab := Kit.t("mg.radio.key.%d" % i)
			var col := Kit.C_STAMP if i == 4 else Kit.C_INK_B
			v.draw_string(font, r.position + Vector2(0, 30), lab, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 19, col)


func draw_porter(v: Control) -> void:
	var pt: Texture2D = _tex.get("portrait")
	var expr := 0
	if _surprised > 0.0:
		expr = 3 if _surprised > 0.8 else 1
	elif logic.porter == "looking":
		expr = 0
	if pt != null:
		v.draw_texture_rect_region(pt, Rect2(Vector2.ZERO, Vector2(336, 336)), Rect2(expr * 112, 0, 112, 112))
	else:
		v.draw_rect(Rect2(Vector2.ZERO, Vector2(336, 336)), Kit.C_NAVY)
	var nt: Texture2D = _tex.get("radio_newspaper.png")
	if nt != null:
		var y := roundf(_paper_y) * S
		v.draw_texture(nt, Vector2(4 * S, y))


func draw_meter(v: Control) -> void:
	var r := Rect2(Vector2.ZERO, v.size)
	v.draw_rect(r, Color(Kit.C_NIGHT, 0.9))
	var w := floorf((r.size.x - 6.0) * logic.progress / 3.0) * 3.0
	v.draw_rect(Rect2(Vector2(3, 3), Vector2(w, r.size.y - 6)), Kit.C_AMBER if not solved else Kit.C_COPPER_L)
	v.draw_rect(r, Kit.C_COPPER, false, 2.0)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	while not solved and not ended and Time.get_ticks_msec() - t0 < 120000:
		if logic.porter != "reading":
			if not logic.on_reich():
				await _tap(KEY_R)
			await _frames(2)
			continue
		var d: float = Logic.FOREIGN - float(logic.needle)
		if absf(d) > 0.006:
			var key := KEY_RIGHT if d > 0.0 else KEY_LEFT
			_key_event(key, true)
			await _until(func(): return absf(Logic.FOREIGN - logic.needle) <= 0.006 \
				or signf(Logic.FOREIGN - logic.needle) != signf(d) or logic.porter != "reading", 8.0)
			_key_event(key, false)
		await _frames(2)
