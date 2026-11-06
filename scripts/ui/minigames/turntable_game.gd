extends "res://scripts/ui/minigames/minigame_base.gd"
## Depot mini-game „Die Drehscheibe“ (scenes/ui/minigames/Turntable.tscn, explore entry karsk.depot.turntable at
## exp_turntable in L_C4P2_Karsk, scene B; §12.8, documentation/C4P2_DESIGN.md §6). Tuesday evening, Karsk depot: the
## press minder wants the sooty shunting engine („Kukuschka“) out of the Swede's photograph, and Grigori, who drives the
## turntable, plays tuba in the band. Alexei turns the 30-m bridge with the engine on it, brakes it out and pulls the
## engine into stall 7 once the rails meet. Rule and physics: turntable_logic.gd (a heavy bridge that coasts far, a
## brake, a tap that sets it a few centimetres; a pull is refused — a bump, the engine rolls back — while the bridge
## moves, when the rails miss, or at another stall). The stage is drawn here in art px (x3, x2 for larger text): the pit
## seen from above with its scale, the bridge, the engine, the roundhouse stalls and the entry track, and a loupe on the
## rail joint ahead of the chimney end („fluchtet“ / „… daneben“).
## Sounds: mg_c4p2_tt_start / mg_c4p2_tt_brake / mg_c4p2_tt_bump / mg_c4p2_tt_lock and the loop mg_c4p2_tt_roll
## (tools/audiogen/mg_audio_c4p2.py).
## Keys: ← / → (A / D, pad d-pad, LB / RB) turn — a tap sets the bridge a few centimetres, holding drives it ·
## Space or pad A brakes while held · E, Enter or pad X pulls the engine („Lok vorziehen“) · R or pad Y starts over ·
## Esc gives up. Mouse: drag the bridge round the pit, the right button brakes while held, the wheel nudges, the
## buttons „Lok vorziehen“ and „Bremsen“ (held).

const Logic := preload("res://scripts/ui/minigames/turntable_logic.gd")
const STAGE := Vector2(400, 150)
## Art-px geometry of the stage (the tests use it).
const PIT_C := Vector2(118, 88)
const PIT_R := 50.0
const STALL_IN := 51.0
const STALL_OUT := 64.0
const GATE_OUT := 70.0
const ROOF_OUT := 84.0
const LOUPE := Rect2(236, 12, 154, 92)
const LOUPE_PX_PER_CM := 0.5
const DRAG_GAIN := 0.45

const COL_GROUND := Color("2a2d2c")
const COL_GROUND2 := Color("323633")
const COL_SNOW := Color("d9dde0")
const COL_SNOW_DIM := Color("9ea7ad")
const COL_PIT := Color("16191a")
const COL_PIT_RIM := Color("5c6266")
const COL_RAIL := Color("aeb6bb")
const COL_RAIL_DIM := Color("6d757a")
const COL_SLEEPER := Color("4a3b2c")
const COL_BRIDGE := [Color("101314"), Color("2c3236"), Color("47515a"), Color("6e7a84")]
const COL_ENGINE := Color("141617")
const COL_ENGINE_HI := Color("3b4246")
const COL_BRASS := Color("c9a35a")
const COL_RED := Color("c23a2e")
const COL_GREEN := Color("6fd08c")
const COL_AMBER := Color("e9b46e")
const COL_WHITE := Color("f5efda")
const COL_LABEL := Color("b3a98d")
const COL_GATE := Color("3a2a22")
const COL_GATE_LIT := Color("e8b45a")
const COL_SCALE := Color("c8c1a6")
const COL_ROOF := Color("2b2422")
const COL_ROOF_RIB := Color("3d3431")
const COL_EAVES := Color("5a4d44")
const COL_PLATE := Color("d9d2bc")
const COL_GLOW := Color("f0a050")
const COL_INK_DARK := Color("1a1714")

var logic = Logic.new()
## Art scale: x3, or x2 in the compact layout for larger text (set in _build_play).
var S := 3
var compact := false
var _scene: Control
var _area: Control
var _side: Control
var _left: Control
var _head: Label
var _angle_label: Label
var _target_label: Label
var _speed_label: Label
var _note_label: Label
var _btn_pull: Button
var _btn_brake: Button
var _t := 0.0
var _input_guard := 0.0
## Held inputs (each source tracked on its own so a release only lifts what it pressed).
var _held := {}                      # "key_l", "key_r", "pad_l", "pad_r" -> true
var _brake_held := {}                # "key", "pad", "mouse", "button" -> true
var _dragging := false
var _drag_prev := 0.0
var _bump_t := 0.0
var _roll_t := -1.0
var _roll_player: AudioStreamPlayer
var _was_moving := false
var _bg: ImageTexture


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_scene", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("scene_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.turntable.kicker", "mg.turntable.title", "mg.turntable.subtitle", "mg.turntable.instruction")
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
	_head = Kit.wrap_label(Kit.t("mg.turntable.side.head").to_upper().replace("ß", "SS"), "KickerLabel")
	side.add_child(_head)
	var plate := Kit.panel("PlatePanel")
	side.add_child(plate)
	var col := Kit.vbox(2)
	plate.add_child(col)
	_angle_label = Kit.label("", "HeadingLabel")
	Kit.scalable(_angle_label, 27)
	col.add_child(_angle_label)
	_target_label = Kit.label("", "BodyLabel")
	Kit.scalable(_target_label, 21)
	col.add_child(_target_label)
	_speed_label = Kit.label("", "KickerLabel")
	col.add_child(_speed_label)
	_note_label = Kit.wrap_label(Kit.t("mg.turntable.side.note"), "DimLabel")
	Kit.scalable(_note_label, 20)
	_note_label.visible = not compact
	side.add_child(_note_label)
	_btn_brake = _add_button(Kit.t("mg.turntable.btn.brake"), func(): pass, 260, true)
	_btn_brake.button_down.connect(func(): _set_brake("button", true))
	_btn_brake.button_up.connect(func(): _set_brake("button", false))
	_btn_pull = _add_button(Kit.t("mg.turntable.btn.pull"), pull, 300, true)
	_roll_player = _loop_player("res://assets/audio/sfx/mg_c4p2_tt_roll.wav")
	if _roll_player.stream is AudioStreamWAV:          # the 'smpl' chunk loops it; make sure on any import
		var w := _roll_player.stream as AudioStreamWAV
		if w.loop_mode == AudioStreamWAV.LOOP_DISABLED:
			w.loop_mode = AudioStreamWAV.LOOP_FORWARD
			w.loop_begin = 0
			w.loop_end = int(round(w.get_length() * w.mix_rate))


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.3
	set_status(Kit.t("mg.turntable.status.start"))
	_status_hold = 2.6
	if _roll_player != null and _roll_player.stream != null and not bool(ctx.get("auto", false)):
		_roll_player.play()


func _reset_game() -> void:
	logic.reset()
	_held = {}
	_brake_held = {}
	_dragging = false
	_bump_t = 0.0
	_roll_t = -1.0
	_update_ui()


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	set_status(Kit.t("mg.turntable.status.start"))
	_status_hold = 1.4


func _on_end() -> void:
	if _roll_player != null:
		_roll_player.stop()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		_release_all()


func _release_all() -> void:
	_held = {}
	_brake_held = {}
	_dragging = false
	logic.set_motor(0)
	logic.set_brake(false)


# ================================================================ actions
## Hold / release one direction source; the motor follows the most recent held direction.
func _set_dir(source: String, dir: int, down: bool) -> void:
	if solved or ended:
		return
	if down:
		var was_idle: bool = logic.motor == 0
		clear_status_hold()
		_held[source] = dir
		logic.set_motor(dir)
		if was_idle:
			_sfx("mg_c4p2_tt_start", -8.0)
	else:
		_held.erase(source)
		var still_dir := 0
		for s in _held:
			still_dir = int(_held[s])
		logic.set_motor(still_dir)


func _set_brake(source: String, on: bool) -> void:
	if solved or ended:
		return
	if on:
		clear_status_hold()
		if _brake_held.is_empty() and not logic.is_still():
			_sfx("mg_c4p2_tt_brake", -6.0)
		_brake_held[source] = true
	else:
		_brake_held.erase(source)
	logic.set_brake(not _brake_held.is_empty())


## „Lok vorziehen“: only a standing bridge on stall 7's rails; otherwise a gentle bump and a refusal.
func pull() -> void:
	if solved or ended or _input_guard > 0.0:
		return
	var r: Dictionary = logic.pull()
	if bool(r.get("ok", false)):
		_release_all()
		_roll_t = 0.0
		_sfx("mg_c4p2_tt_lock", -2.0)
		mark_solved(Kit.t("mg.turntable.solved"))
		_update_ui()
		return
	_bump_t = 0.45
	_sfx("mg_c4p2_tt_bump", -4.0)
	match str(r.get("reason", "")):
		"moving":
			register_fail(Kit.t("mg.turntable.fail.moving"))
		"entry":
			register_fail(Kit.t("mg.turntable.fail.entry"))
		"wrong":
			register_fail(Kit.t("mg.turntable.fail.wrong", {"n": int(r.get("track", 0))}))
		_:
			if absf(float(r.get("err", 0.0))) > 1.5:
				register_fail(Kit.t("mg.turntable.fail.between"))
			else:
				register_fail(Kit.t("mg.turntable.fail.gap", {"cm": _cm_text(float(r.get("cm", 0.0)))}))
	_update_ui()


static func _cm_text(cm: float) -> String:
	if cm >= 100.0:
		return ("%.1f m" % (cm / 100.0)).replace(".", ",")
	return "%d cm" % int(round(cm))


static func _deg_text(d: float) -> String:
	return ("%.1f" % d).replace(".", ",")


# ================================================================ hints
func _hint_text(level: int) -> String:
	if logic.done:
		return ""
	if level >= 2:
		return Kit.t("mg.turntable.hint.next", {"deg": _deg_text(Logic.target_angle()), "now": _deg_text(logic.angle)})
	return Kit.t("mg.turntable.hint.1")


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
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.turntable.ctrl.turn")],
		[Kit.key_name(KEY_SPACE), Kit.t("mg.turntable.ctrl.brake")],
		[Kit.action_key_text("interact"), Kit.t("mg.turntable.ctrl.pull")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_t += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	_bump_t = maxf(0.0, _bump_t - delta)
	logic.step(delta)
	if _roll_t >= 0.0:
		_roll_t += delta
	var moving: bool = not logic.is_still()
	if _roll_player != null and _roll_player.playing:
		var spd: float = absf(logic.vel) / Logic.MAX_SPEED
		var target_db: float = -80.0 if (spd < 0.01 or ended) else lerpf(-26.0, -6.0, clampf(spd, 0.0, 1.0))
		_roll_player.volume_db = lerpf(_roll_player.volume_db, target_db, clampf(delta * 8.0, 0.0, 1.0))
	if not solved:
		if moving:
			var key := "mg.turntable.status.braking" if logic.braking else ("mg.turntable.status.turning"
				if logic.motor != 0 else "mg.turntable.status.coasting")
			status_auto(Kit.t(key, {"speed": _deg_text(absf(logic.vel))}))
		elif _was_moving or _status_hold <= 0.0:
			status_auto(Kit.t("mg.turntable.status.idle", {"where": where_text()}))
	_was_moving = moving
	_update_ui()
	_fit_height()
	if _scene != null:
		_scene.queue_redraw()


## Where the chimney end stands, in words: „vor Stand 5“, „an der Zufahrt“, „zwischen den Gleisen“.
func where_text() -> String:
	var nt: Dictionary = logic.nearest_track()
	if absf(float(nt["err"])) > 1.5:
		return Kit.t("mg.turntable.between")
	if int(nt["track"]) == 0:
		return Kit.t("mg.turntable.entry")
	return Kit.t("mg.turntable.stall", {"n": int(nt["track"])})


func _fit_height() -> void:
	if _area == null or _side == null or _left == null:
		return
	var need := maxf(_left.get_combined_minimum_size().y, _side.get_combined_minimum_size().y)
	if absf(_area.custom_minimum_size.y - need) > 0.5:
		_area.custom_minimum_size.y = need


func _update_ui() -> void:
	if _angle_label == null:
		return
	_angle_label.text = Kit.t("mg.turntable.side.angle", {"deg": _deg_text(logic.angle)})
	_target_label.text = Kit.t("mg.turntable.side.target", {"deg": _deg_text(Logic.target_angle())})
	_speed_label.text = Kit.t("mg.turntable.side.speed", {"speed": _deg_text(absf(logic.vel))})
	if _hint_box != null and _hint_box.visible and not logic.done:
		_hint_label.text = _hint_text(maxi(1, hint_level))


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	if event is InputEventKey:
		var ke := event as InputEventKey
		var code := int(ke.physical_keycode) if ke.physical_keycode != 0 else int(ke.keycode)
		if ke.echo:
			return true
		match code:
			KEY_LEFT, KEY_A:
				_set_dir("key_l", 1, ke.pressed)
				return true
			KEY_RIGHT, KEY_D:
				_set_dir("key_r", -1, ke.pressed)
				return true
			KEY_SPACE:
				_set_brake("key", ke.pressed)
				return true
		if not ke.pressed:
			return false
		if code == KEY_R:
			restart()
			return true
		if code == KEY_E or code == KEY_ENTER or code == KEY_KP_ENTER:
			pull()
			return true
		return false
	if event is InputEventJoypadButton:
		var jb := event as InputEventJoypadButton
		match jb.button_index:
			JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_DPAD_LEFT:
				_set_dir("pad_l", 1, jb.pressed)
				return true
			JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_DPAD_RIGHT:
				_set_dir("pad_r", -1, jb.pressed)
				return true
			JOY_BUTTON_A:
				_set_brake("pad", jb.pressed)
				return true
			JOY_BUTTON_X:
				if jb.pressed:
					pull()
				return true
			JOY_BUTTON_Y:
				if jb.pressed:
					restart()
				return true
		return false
	if event is InputEventJoypadMotion:
		var jm := event as InputEventJoypadMotion
		if jm.axis == JOY_AXIS_LEFT_X:
			_set_dir("pad_l", 1, jm.axis_value < -0.5)
			_set_dir("pad_r", -1, jm.axis_value > 0.5)
			return true
	return false


## Mouse angle around the pit centre (degrees, 0 = east, counter-clockwise) for a point in art px.
static func mouse_angle(p: Vector2) -> float:
	var d := p - PIT_C
	return Logic.wrap360(rad_to_deg(atan2(-d.y, d.x)))


func scene_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		var p := mb.position / S
		match mb.button_index:
			MOUSE_BUTTON_LEFT:
				if mb.pressed and LOUPE.has_point(p):
					pull()
				elif mb.pressed and p.distance_to(PIT_C) <= GATE_OUT:
					_dragging = true
					_drag_prev = mouse_angle(p)
				elif not mb.pressed:
					_dragging = false
			MOUSE_BUTTON_RIGHT:
				_set_brake("mouse", mb.pressed)
			MOUSE_BUTTON_WHEEL_UP:
				if mb.pressed:
					logic.push(Logic.NUDGE)
			MOUSE_BUTTON_WHEEL_DOWN:
				if mb.pressed:
					logic.push(-Logic.NUDGE)
	elif event is InputEventMouseMotion and _dragging:
		var a := mouse_angle((event as InputEventMouseMotion).position / S)
		logic.push(Logic.shortest(_drag_prev, a) * DRAG_GAIN)
		_drag_prev = a


# ================================================================ drawing (art px, x S)
static func _dir(a_deg: float) -> Vector2:
	var r := deg_to_rad(a_deg)
	return Vector2(cos(r), -sin(r))


static func _img_px(img: Image, q: Vector2, col: Color) -> void:
	var p := Vector2i(q.round())
	if p.x >= 0 and p.y >= 0 and p.x < img.get_width() and p.y < img.get_height():
		img.set_pixelv(p, col)


static func _img_line(img: Image, a: Vector2, b: Vector2, col: Color) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1:
		_img_px(img, a.lerp(b, float(i) / float(maxi(1, n))), col)


static func _img_disc(img: Image, c: Vector2, r: float, col: Color) -> void:
	var ri := int(ceil(r))
	for y in range(-ri, ri + 1):
		for x in range(-ri, ri + 1):
			if float(x * x + y * y) <= r * r:
				_img_px(img, c + Vector2(x, y), col)


static func _img_ring(img: Image, c: Vector2, r: float, col: Color) -> void:
	var n := int(ceil(TAU * r * 1.5))
	for i in n:
		var a := TAU * float(i) / float(n)
		_img_px(img, c + Vector2(cos(a), sin(a)) * r, col)


## A straight track from radius r0 to r1 at angle a: sleepers every 4 px and two rails (gauge 4 art px).
static func _img_track(img: Image, a: float, r0: float, r1: float, rail: Color) -> void:
	var d := _dir(a)
	var n := Vector2(-d.y, d.x)
	var r := r0
	while r <= r1:
		var c := PIT_C + d * r
		_img_line(img, c - n * 4.0, c + n * 4.0, COL_SLEEPER)
		r += 4.0
	_img_line(img, PIT_C + d * r0 - n * 2.0, PIT_C + d * r1 - n * 2.0, rail)
	_img_line(img, PIT_C + d * r0 + n * 2.0, PIT_C + d * r1 + n * 2.0, rail)


## The yard, the roundhouse, the tracks and the pit with its scale: drawn once (deterministic). The yard is lived
## in: a stack of sleepers under snow, the shunters' brazier, a floodlight mast and its pool of light, footprints from
## the yard to the pit, snow banked along the edge; the roundhouse roof with ribs and snow over the stalls.
static func build_background() -> ImageTexture:
	var img := Image.create(int(STAGE.x), int(STAGE.y), false, Image.FORMAT_RGBA8)
	img.fill(COL_GROUND)
	for i in 140:
		_img_px(img, Vector2(float((i * 73) % int(STAGE.x)), float((i * 41 + i * i * 3) % int(STAGE.y))), COL_GROUND2)
		_img_px(img, Vector2(float((i * 73) % int(STAGE.x)) + 1.0, float((i * 41 + i * i * 3) % int(STAGE.y))), COL_GROUND2)
	for i in 110:
		_img_px(img, Vector2(float((i * 97 + 13) % int(STAGE.x)), float((i * 29 + 7) % int(STAGE.y))), COL_SNOW_DIM)
	# the floodlight's pool on the snow (lighter ground), its mast and lamp
	for y in range(96, 150):
		for x in range(150, 232):
			var q := Vector2((float(x) - 192.0) / 42.0, (float(y) - 126.0) / 22.0)
			if q.length_squared() <= 1.0 and (x * 7 + y * 3) % 5 != 0:
				img.set_pixel(x, y, img.get_pixel(x, y).lerp(COL_SNOW_DIM, 0.22 * (1.0 - q.length_squared())))
	_img_line(img, Vector2(214, 132), Vector2(214, 141), COL_BRIDGE[2])
	_img_disc(img, Vector2(214, 131), 2.0, Color("e8d7a0"))
	# a stack of sleepers, snow on the top one; the shunters' brazier with its glow
	for k in 4:
		var y0 := 122 + k * 5
		for x in range(12, 46):
			for dy in 4:
				img.set_pixel(x, y0 + dy, COL_SLEEPER if dy > 0 else Color("6b5440"))
		_img_line(img, Vector2(12, y0 + 3), Vector2(45, y0 + 3), Color("2e241a"))
	_img_line(img, Vector2(13, 121), Vector2(44, 121), COL_SNOW)
	_img_disc(img, Vector2(56, 132), 4.0, COL_BRIDGE[1])
	_img_disc(img, Vector2(56, 131), 2.5, COL_GLOW)
	_img_disc(img, Vector2(56, 131), 1.2, Color("ffe2a0"))
	for k in 12:
		var a := float(k) * TAU / 12.0
		_img_px(img, Vector2(56, 131) + Vector2(cos(a), sin(a)) * 6.0, COL_GROUND.lerp(COL_GLOW, 0.25))
	# footprints from the yard to the pit rim, and snow banked along the bottom edge
	for k in 9:
		var f := Vector2(160.0 - float(k) * 2.5, 149.0 - float(k) * 1.6)
		_img_px(img, f, COL_SNOW_DIM.darkened(0.25))
		_img_px(img, f + Vector2(2, 1), COL_SNOW_DIM.darkened(0.25))
	for x in int(STAGE.x):
		var hgt := 2 + int(absf(sin(float(x) * 0.23) * 2.0 + sin(float(x) * 0.07) * 1.5))
		for y in range(int(STAGE.y) - hgt, int(STAGE.y)):
			img.set_pixel(x, y, COL_SNOW_DIM if y > int(STAGE.y) - hgt else COL_SNOW)
	# the roundhouse roof over the stalls: tar, ribs between the stalls, snow in the gutters, the eaves
	for y in int(STAGE.y):
		for x in int(STAGE.x):
			var d := Vector2(float(x), float(y)) - PIT_C
			var r := d.length()
			if r < GATE_OUT or r > ROOF_OUT:
				continue
			var ang := Logic.wrap360(rad_to_deg(atan2(-d.y, d.x)))
			if ang < 18.0 or ang > 162.0:
				continue
			var col := COL_ROOF
			if fmod(ang + 7.5, 15.0) < 1.6:
				col = COL_ROOF_RIB
			elif (x * 13 + y * 7) % 11 == 0 or (r > ROOF_OUT - 2.0 and (x + y) % 3 != 0):
				col = COL_SNOW_DIM
			img.set_pixel(x, y, col)
	for k in range(18, 163):
		_img_px(img, PIT_C + _dir(float(k)) * GATE_OUT, COL_EAVES)
	for n in Logic.STALLS:
		_img_track(img, float(Logic.STALLS[n]), STALL_IN, STALL_OUT, COL_RAIL if int(n) == Logic.TARGET else COL_RAIL_DIM)
	_img_track(img, Logic.ENTRY, STALL_IN, STAGE.y - PIT_C.y + 4.0, COL_RAIL_DIM)
	# the pit: dark floor, the circular running rail, the rim and the scale (ticks every 5°, longer every 15°)
	_img_disc(img, PIT_C, PIT_R + 1.0, COL_PIT)
	_img_ring(img, PIT_C, PIT_R + 1.0, COL_PIT_RIM)
	_img_ring(img, PIT_C, PIT_R - 4.0, COL_RAIL_DIM)
	for k in 72:
		var d := _dir(float(k) * 5.0)
		var long := k % 3 == 0
		_img_line(img, PIT_C + d * (PIT_R - (3.0 if long else 1.0)), PIT_C + d * PIT_R, COL_SCALE if long else COL_PIT_RIM)
	_img_disc(img, PIT_C, 5.0, COL_BRIDGE[2])
	_img_disc(img, PIT_C, 2.0, COL_BRIDGE[3])
	return ImageTexture.create_from_image(img)


func _px_line(v: Control, a: Vector2, b: Vector2, col: Color, thick := 1) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1:
		var q := a.lerp(b, float(i) / float(maxi(1, n))).round()
		v.draw_rect(Rect2(q.x, q.y, thick, thick), col)


## A band across direction `fwd` from -w to +w (sideways) and from f0 to f1 (along): a rotated pixel rectangle.
func _band(v: Control, c: Vector2, fwd: Vector2, f0: float, f1: float, w: int, col: Color, edge := Color(0, 0, 0, 0)) -> void:
	var side := Vector2(-fwd.y, fwd.x)
	for k in range(-w, w + 1):
		var cc := edge if (edge.a > 0.0 and absi(k) == w) else col
		_px_line(v, c + fwd * f0 + side * float(k), c + fwd * f1 + side * float(k), cc, 1)


func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var hc := Kit.high_contrast()
	var calm := Kit.reduced_motion()
	if _bg == null:
		_bg = build_background()
	v.draw_texture(_bg, Vector2.ZERO)
	# the stall gates; stall 7's lit for the minder's photograph until the engine is in and the gate shut
	for n in Logic.STALLS:
		var d := _dir(float(Logic.STALLS[n]))
		var lit := int(n) == Logic.TARGET and not (solved and _roll_t > 1.4)
		_band(v, PIT_C, d, STALL_OUT, GATE_OUT, 5, COL_GATE_LIT if lit else COL_GATE, COL_BRIDGE[0])
		if lit:
			_band(v, PIT_C, d, STALL_IN + 2.0, STALL_OUT, 5, Color(COL_GATE_LIT, 0.16))
		# the stall's number plate on the eaves
		var pc := (PIT_C + d * (GATE_OUT + 6.0)).round()
		v.draw_rect(Rect2(pc - Vector2(4, 3), Vector2(8, 7)), COL_BRIDGE[0])
		v.draw_rect(Rect2(pc - Vector2(3, 2), Vector2(6, 5)), COL_GATE_LIT if lit else COL_PLATE)
	# the bridge with the engine (a bump jolts the engine along the bridge; after the pull it rolls into the stall)
	var fwd := _dir(logic.angle)
	var side := Vector2(-fwd.y, fwd.x)
	var half := PIT_R - 2.0
	_band(v, PIT_C, fwd, -half, half, 5, COL_BRIDGE[1], COL_BRIDGE[0])
	for k in range(-int(half), int(half) + 1, 6):
		_px_line(v, PIT_C + fwd * float(k) - side * 4.0, PIT_C + fwd * float(k) + side * 4.0, COL_BRIDGE[2], 1)
	_px_line(v, PIT_C - fwd * half - side * 2.0, PIT_C + fwd * half - side * 2.0, COL_RAIL, 1)
	_px_line(v, PIT_C - fwd * half + side * 2.0, PIT_C + fwd * half + side * 2.0, COL_RAIL, 1)
	# the operator's hut at the tail end, an empty stool, his cap on the controller
	var hut := PIT_C - fwd * (half - 5.0) + side * 9.0
	_band(v, hut, fwd, -3.0, 3.0, 3, COL_BRIDGE[3], COL_BRIDGE[0])
	v.draw_rect(Rect2(hut.round() - Vector2(1, 1), Vector2(2, 2)), COL_RED)
	var jolt := 0.0
	if _bump_t > 0.0 and not calm:
		jolt = sin(_bump_t * 40.0) * 1.5
	var roll := 0.0
	if _roll_t >= 0.0:
		roll = clampf(_roll_t / 1.4, 0.0, 1.0) * (STALL_OUT - 4.0)
	var e0 := PIT_C + fwd * (jolt + roll)
	if roll < STALL_OUT - 6.0:
		# the engine from above: tank boiler, smokebox and chimney ahead, cab and coal bunker behind
		_band(v, e0, fwd, -22.0, 18.0, 4, COL_ENGINE, COL_ENGINE_HI)
		_px_line(v, e0 - fwd * 22.0, e0 + fwd * 18.0, COL_ENGINE_HI, 1)
		_band(v, e0, fwd, -18.0, -11.0, 4, COL_ENGINE_HI, COL_BRIDGE[3])
		_band(v, e0, fwd, -22.0, -19.0, 3, Color("0a0b0b"))
		var chim := e0 + fwd * 14.0
		v.draw_rect(Rect2(chim.round() - Vector2(1, 1), Vector2(3, 3)), COL_BRIDGE[0])
		v.draw_rect(Rect2(chim.round(), Vector2(1, 1)), COL_BRASS)
		if not calm:
			for k in 4:
				var tt := fmod(_t * 0.8 + float(k) * 0.25, 1.0)
				var puff := (chim + Vector2(tt * 10.0, -tt * 14.0)).round()
				var rr := 1.0 + tt * 2.0
				v.draw_rect(Rect2(puff - Vector2(rr, rr), Vector2(rr * 2.0, rr * 2.0)), Color(COL_SNOW, 0.32 * (1.0 - tt)))
	# the pointer on the scale at the chimney end
	var tip := PIT_C + fwd * (PIT_R + 1.0)
	v.draw_rect(Rect2(tip.round() - Vector2(1, 1), Vector2(3, 3)), COL_WHITE if hc else COL_AMBER)
	_draw_loupe(v, hc)
	# labels (screen pixels, theme font)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var font := v.get_theme_default_font()
	if font == null:
		return
	var fs := 15 if S == 2 else 19
	for n in Logic.STALLS:
		var p := (PIT_C + _dir(float(Logic.STALLS[n])) * (GATE_OUT + 6.0)).round() + Vector2(0.0, 0.5)
		v.draw_string(font, Vector2(p.x * S - 12.0, p.y * S + float(fs - 4) * 0.36), str(n), HORIZONTAL_ALIGNMENT_CENTER, 24.0,
			fs - 4, COL_INK_DARK)
	var ep := PIT_C + _dir(Logic.ENTRY) * (PIT_R + 9.0)
	v.draw_string(font, Vector2(ep.x * S + 18.0, ep.y * S + float(fs) * 0.4), Kit.t("mg.turntable.label.entry"),
		HORIZONTAL_ALIGNMENT_LEFT, 200.0, fs - 2, COL_LABEL if not hc else COL_WHITE)
	var ok: bool = logic.aligned() and logic.is_still()
	var far: bool = absf(logic.err_to_target()) > 3.0
	var txt := Kit.t("mg.turntable.loupe.ok") if ok else (Kit.t("mg.turntable.loupe.far",
		{"deg": _deg_text(absf(logic.err_to_target()))}) if far else Kit.t("mg.turntable.loupe.off",
		{"cm": _cm_text(Logic.cm_of(logic.err_to_target()))}))
	v.draw_string(font, Vector2(LOUPE.position.x * S, (LOUPE.end.y + 5.0) * S + float(fs) * 0.6),
		Kit.t("mg.turntable.loupe") + " · " + txt, HORIZONTAL_ALIGNMENT_LEFT, LOUPE.size.x * S, fs,
		(COL_GREEN if ok else COL_LABEL) if not hc else COL_WHITE)
	var nt: Dictionary = logic.nearest_track()
	if int(nt["track"]) != Logic.TARGET and absf(float(nt["err"])) <= 1.5:
		v.draw_string(font, Vector2(LOUPE.position.x * S, (LOUPE.end.y + 13.0) * S + float(fs) * 0.6),
			Kit.t("mg.turntable.loupe.here", {"where": where_text()}), HORIZONTAL_ALIGNMENT_LEFT, LOUPE.size.x * S, fs - 2,
			COL_LABEL if not hc else COL_WHITE)


## The loupe: stall 7's rail ends fixed on the left, the bridge's rail ends coming in from the right, shifted sideways
## by the angle error at the rim (LOUPE_PX_PER_CM, 0.5 art px per cm); a green frame when they meet.
func _draw_loupe(v: Control, hc: bool) -> void:
	var r := LOUPE
	v.draw_rect(r, COL_BRIDGE[0])
	v.draw_rect(r, COL_PIT_RIM, false, 1.0)
	var mid := r.position + r.size * 0.5
	var gauge := 22.0
	for x in range(int(r.position.x) + 4, int(mid.x) - 1, 9):
		v.draw_rect(Rect2(x, mid.y - gauge * 0.5 - 6.0, 4, gauge + 12.0), COL_SLEEPER)
	for s in [-1.0, 1.0]:
		var y: float = mid.y + s * gauge * 0.5
		v.draw_rect(Rect2(r.position.x + 2.0, y - 2.0, mid.x - r.position.x - 3.0, 4.0), COL_RAIL)
		v.draw_rect(Rect2(r.position.x + 2.0, y - 2.0, mid.x - r.position.x - 3.0, 1.0), COL_WHITE)
	var cm := deg_to_rad(logic.err_to_target()) * Logic.RIM_M * 100.0
	var off := clampf(-cm * LOUPE_PX_PER_CM, -r.size.y * 0.5 - 8.0, r.size.y * 0.5 + 8.0)
	var gap := 1.0 if logic.aligned() else 2.0
	var blur := clampf(absf(logic.vel) * 0.6, 0.0, 6.0)
	for s in [-1.0, 1.0]:
		var y: float = mid.y + s * gauge * 0.5 + off
		if y < r.position.y + 2.0 or y > r.end.y - 4.0:
			continue
		v.draw_rect(Rect2(mid.x + gap, y - 2.0, r.end.x - mid.x - gap - 2.0, 4.0), COL_BRIDGE[3])
		v.draw_rect(Rect2(mid.x + gap, y - 2.0, r.end.x - mid.x - gap - 2.0, 1.0), COL_RAIL)
		if blur > 0.5:
			v.draw_rect(Rect2(mid.x + gap, y - 2.0 - blur, 12.0, blur * 2.0 + 4.0), Color(COL_RAIL, 0.18))
	v.draw_rect(Rect2(mid.x - 3.0, r.end.y - 9.0, 6.0, 5.0), COL_BRIDGE[2])
	if logic.aligned() and logic.is_still():
		v.draw_rect(r.grow(-1.0), COL_WHITE if hc else COL_GREEN, false, 1.0)
		v.draw_rect(Rect2(mid.x - 1.0, r.end.y - 12.0, 2.0, 8.0), COL_WHITE if hc else COL_GREEN)


# ================================================================ synthetic solve (real-input driver)
## Drives the bridge to stall 7 and pulls the engine, through synthetic key events only: hold the turning key, brake
## with Space when the stopping distance is reached, set the last centimetres with short holds or taps, then E.
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 90000:
		var e: float = logic.err_to_target()
		var dir := 1 if e > 0.0 else -1
		var key := KEY_LEFT if dir > 0 else KEY_RIGHT
		if not logic.is_still():
			# moving: brake to a stop before deciding again
			_key_event(KEY_SPACE, true)
			await _until(func(): return logic.is_still(), 4.0)
			_key_event(KEY_SPACE, false)
			await _frames(2)
			continue
		if absf(e) <= Logic.TOL * 0.6:
			await _tap(KEY_E)
			await _frames(3)
			continue
		if absf(e) > 6.0:
			# drive: hold until the braking distance (plus a margin) reaches the remaining way, then brake
			_key_event(key, true)
			await _until(func(): return _demo_brake_point(dir), 30.0)
			_key_event(key, false)
			await _frames(1)
			_key_event(KEY_SPACE, true)
			await _until(func(): return logic.is_still(), 4.0)
			_key_event(KEY_SPACE, false)
			await _frames(2)
			continue
		# the last degrees: a hold just long enough to coast there, or a tap for the last centimetres
		var need := sqrt(2.0 * Logic.FRICTION * absf(e))
		if need <= Logic.NUDGE * 1.05:
			await _tap(key)
		else:
			_key_event(key, true)
			await _until(func(): return _demo_fast_enough(dir), 3.0)
			_key_event(key, false)
		await _until(func(): return logic.is_still(), 6.0)
		await _frames(2)
	await _until(func(): return solved, 4.0)


## The drive phase ends where the braking distance (plus a margin) reaches the remaining way, or past the stall.
func _demo_brake_point(dir: int) -> bool:
	var e: float = logic.err_to_target()
	return absf(e) <= logic.coast_distance(true) + 2.0 or e * float(dir) < 0.0


## A short hold ends once the bridge would coast exactly to stall 7 (or has passed it).
func _demo_fast_enough(dir: int) -> bool:
	var e: float = logic.err_to_target()
	return absf(logic.vel) >= sqrt(2.0 * Logic.FRICTION * absf(e)) or e * float(dir) <= 0.0
