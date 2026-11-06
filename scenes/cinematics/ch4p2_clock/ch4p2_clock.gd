extends "res://scenes/cinematics/ch4p2_common/c4p2_cinematic.gd"
## LS_C4P2_Clock (24 s) — Berlin, Kordon-17, Karsk at 23.40 Korridorzeit (C4P2_DESIGN §2.9).  Music mus_c4p2_clock
## throughout (both themes on one clock); its tick runs from k1 and stops on k5 -- when the music file is missing,
## the film's own tick bed (c4p2cine_tick, 1 Hz like the dispatch clock's second hand) stands in.
##   k1  0-5     Berlin, 23.40: the courtyard of No. 14 from above, the side wing square on; the car doors
##               (CAR_DOORS), the black car rolls out left into the gate passage (CAR_T); the candle in the
##               cobbler's basement window where Ilse sleeps; then the camera tilts up (K1_TILT) to the first floor,
##               Hanna's window stays lit
##   k2  5-11    Kordon-17 wide and from far.  publish_now: the flashbulb at the fence (FLASH_T), a man with a
##               notebook, the door stays shut, two figures are led back into the German hall.  protect_first: Tür Ost
##               opens (DOOR_OPEN), two figures cross its light into the wagon, the door closes (DOOR_SHUT).
##               No faces, no force shown, nobody inside a wagon.
##   k3  11-16   Karsk, 1.40: the dispatch office -- Alexei at the window (Lev's lamp across the yard), Irina at the
##               teleprinter, the tape typing (TYPE_T0, TYPE_CPS) in telegraph Russian; the second hand ticks
##   k4  16-20   Irina's desk under the lamp: the German half of card 0417 beside the film canister (protect_first)
##               or beside Lev's empty folder (publish_now)
##   k5  20-24   black; the tick stops; the end of the fourth chapter
## Lines: the Berlin card, Konrad's thought (c4d_choose), the Kordon card, the Karsk card, Alexei's thought (c4g),
## the end card.

const DUR := 24.0
const SHOTS := [["k1", 0.0, 5.0], ["k2", 5.0, 11.0], ["k3", 11.0, 16.0], ["k4", 16.0, 20.0], ["k5", 20.0, 24.0]]
const L_BERLIN := "cin.c4p2.clock.berlin"
const L_KONRAD_NAME := "cin.c4p2.clock.konrad_name"
const L_KONRAD_PROTECT := "cin.c4p2.clock.konrad_protect"
const L_KORDON := "cin.c4p2.clock.kordon"
const L_KARSK := "cin.c4p2.clock.karsk"
const L_PUBLISH := "cin.c4p2.clock.publish"
const L_PROTECT := "cin.c4p2.clock.protect"
const L_END := "cin.c4p2.clock.end"
const CAR_DOORS := [0.3, 0.55]
const CAR_T := [0.9, 3.4]
const FLASH_T := 7.35
const DOOR_OPEN := 6.2
const DOOR_SHUT := 9.7
const LED_BACK := [8.0, 10.6]       # publish_now: the two are led back west into the German hall
const CROSS := [6.6, 9.2]           # protect_first: the two cross the light into the wagon
const TYPE_T0 := 11.6
const TYPE_CPS := 7.0
const TICK_END := 20.0
const K1_TILT := [3.3, 5.0, 160.0, 40.0]   # k1: the plate's offset from t0 to t1 (the camera tilts up)

var C: Dictionary = {}
var k1: Node2D
var k2: Node2D
var k3: Node2D
var k4: Node2D
var k5: Node2D
var _car: Sprite2D
var _glass: Sprite2D
var _passage: Sprite2D
var _candle: Sprite2D
var _door: Sprite2D
var _flash: Sprite2D
var _people: Array = []
var _escort: Sprite2D
var _witness: Sprite2D
var _tapes: Dictionary = {}
var _fill: Node2D
var _alexei: Sprite2D
var _irina: Sprite2D
var _hand: Node2D
var _levglow: Sprite2D
var _canister: Sprite2D
var _folder: Sprite2D
var _motes: Node2D
var _fx4: Node2D
var _snow1: Node2D
var _snow2: Node2D
var _t_tea: Texture2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func _konrad_line() -> String:
	return L_KONRAD_PROTECT if c4d() == "protect_marta" else L_KONRAD_NAME


func _alexei_line() -> String:
	return L_PROTECT if c4g() == "protect_first" else L_PUBLISH


func chosen_lines() -> Array:
	return [L_BERLIN, _konrad_line(), L_KORDON, L_KARSK, _alexei_line(), L_END]


func music_present() -> bool:
	return ResourceLoader.exists("res://assets/audio/music/mus_c4p2_clock.wav")


func _make_cues() -> Array:
	var g := c4g()
	var c: Array = [
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c4p2cine_k14", "db": -4.0},
		{"t": 5.0, "bed": "c4p2cine_kordon_" + ("protect" if g == "protect_first" else "publish"), "db": -3.0},
		{"t": 11.0, "bed": "c4p2cine_tty_" + ("protect" if g == "protect_first" else "publish"), "db": -4.0},
		{"t": 16.0, "bed": "c4p2cine_desk", "db": -6.0},
	]
	if music_present():
		# the cast stream's cue: its tick at 0, 1 .. 19 s (on the dispatch clock's second hand), none at TICK_END,
		# then it dies away by itself -- the film never cuts it
		c.append({"t": 0.0, "music": "mus_c4p2_clock", "fade": 0.05})
	else:
		c.append({"t": 0.0, "music": "", "fade": 1.0})
		c.append({"t": 0.0, "bed": "c4p2cine_tick", "db": -8.0})
	c += schedule([
		{"key": L_BERLIN, "at": 0.3, "dur": line_dur(L_BERLIN)},
		{"key": _konrad_line(), "at": 1.8, "dur": line_dur(_konrad_line(), 1.4, 6.0)},
		{"key": L_KORDON, "at": 6.2, "dur": line_dur(L_KORDON)},
		{"key": L_KARSK, "at": 11.3, "dur": line_dur(L_KARSK)},
		{"key": _alexei_line(), "at": 16.1, "dur": line_dur(_alexei_line(), 1.4, 6.0)},
		{"key": L_END, "at": 20.6, "dur": line_dur(L_END, 1.4, 3.2)},
	])
	return c


## k1: the plate's vertical offset (the camera tilts up from the yard to the first floor); with reduced motion
## the camera does not travel at all -- it holds on the yard and cuts to the first floor at the tilt's middle
func k1_offset(time: float) -> float:
	if reduced_motion():
		return K1_TILT[3] if time >= (K1_TILT[0] + K1_TILT[1]) * 0.5 else K1_TILT[2]
	return roundf(lerpf(K1_TILT[2], K1_TILT[3], ease01(time, K1_TILT[0], K1_TILT[1])))


## k1: the car's progress 0..1 along its path into the arch
func car_u(time: float) -> float:
	return ease01(time, float(CAR_T[0]), float(CAR_T[1]))


## k2: is Tür Ost open (protect_first only)?
func door_open(time: float) -> bool:
	return c4g() == "protect_first" and time >= DOOR_OPEN and time < DOOR_SHUT


## k3: characters typed on the tape so far
func typed(time: float) -> int:
	var txt := str((C.get("text", {}) as Dictionary).get(c4g(), ""))
	if time < TYPE_T0:
		return 0
	return mini(txt.length(), int(floor((time - TYPE_T0) * TYPE_CPS)) + 1)


## Film times of the teleprinter's key strikes (the sound tool cuts c4p2cine_tty_<variant> on them).
func type_times(variant: String) -> Array:
	var txt := str((C.get("text", {}) as Dictionary).get(variant, ""))
	var out: Array = []
	for i in txt.length():
		if txt[i] != " ":
			out.append(snappedf(TYPE_T0 + float(i) / TYPE_CPS, 0.001))
	return out


func _build() -> void:
	C = _layout_section("clock")
	# ---------------------------------------------------------------- k1
	k1 = group("Courtyard")
	sprite("clock/k1_bg.png", Vector2.ZERO, k1)
	var cc: Array = C.get("car_cell", [200, 70])
	_car = cells("clock/car.png", k1, int(cc[0]))
	sprite("clock/k1_front.png", Vector2.ZERO, k1)
	_passage = glow("clock/passage_glow.png", k1)
	_candle = glow("clock/k1_glow.png", k1)
	_snow1 = snow(k1, Rect2(-20, 30, 680, 300), [
		{"count": 60, "v": Vector2(-3, 12), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#8a9ab8"), "sway": 2.0},
		{"count": 22, "v": Vector2(-5, 20), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#dce4f0"), "sway": 3.0},
	], 4601)
	# ---------------------------------------------------------------- k2
	k2 = group("Kordon")
	sprite("clock/k2_bg.png", Vector2.ZERO, k2)
	glow("clock/k2_beams.png", k2)
	_door = glow("clock/k2_door.png", k2)
	for i in 2:
		_people.append(cells("clock/k2_person.png", k2, 16))
	_escort = cells("clock/k2_escort.png", k2, 16)
	_witness = cells("clock/k2_witness.png", k2, 16, Vector2(372, 222))
	_flash = cells("clock/flash.png", k2, 100, Vector2(338, 172), true)
	_snow2 = snow(k2, Rect2(-20, 30, 680, 300), [
		{"count": 40, "v": Vector2(-4, 10), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#6a7a96"), "sway": 2.0},
	], 4602)
	# ---------------------------------------------------------------- k3
	k3 = group("Dispatch")
	sprite("clock/k3_bg.png", Vector2.ZERO, k3)
	_levglow = glow("clock/k3_lev_glow.png", k3)
	var al: Array = C.get("alexei", [112, 112])
	_alexei = cells("clock/k3_alexei.png", k3, 112, Vector2(float(al[0]), float(al[1])))
	_glass = sprite("clock/k3_glass.png", Vector2.ZERO, k3)
	var ir: Array = C.get("irina", [262, 150])
	_irina = cells("clock/k3_irina.png", k3, 112, Vector2(float(ir[0]), float(ir[1])))
	sprite("clock/k3_front.png", Vector2.ZERO, k3)
	for v in ["publish_now", "protect_first"]:
		var tp := sprite("clock/tape_%s.png" % v, Vector2.ZERO, k3)
		tp.region_enabled = true
		_tapes[v] = tp
	_hand = fx(k3, "SecondHand", _draw_hand)
	glow("clock/k3_lamp_glow.png", k3)
	# ---------------------------------------------------------------- k4
	k4 = group("Desk")
	sprite("clock/k4_bg.png", Vector2.ZERO, k4)
	var kc: Array = C.get("k4_card", [250, 170])
	sprite("clock/k4_card.png", Vector2(float(kc[0]), float(kc[1])), k4)
	var kt: Array = C.get("k4_thing", [390, 160])
	_canister = sprite("clock/k4_canister.png", Vector2(float(kt[0]), float(kt[1])), k4)
	_folder = sprite("clock/k4_folder.png", Vector2(float(kt[0]) - 30.0, float(kt[1]) - 10.0), k4)
	_fx4 = fx(k4, "Steam", _draw_k4)
	glow("clock/k4_glow.png", k4)
	_motes = fx(k4, "Motes", _draw_motes)
	# ---------------------------------------------------------------- k5
	k5 = group("Black")
	_fill = fx(k5, "Fill", _draw_fill)
	_t_tea = tex("clock/tea_steam.png")


func _apply(time: float) -> void:
	if k1 == null:
		return
	var sh := shot_at(time)
	k1.visible = sh == "k1"
	k2.visible = sh == "k2"
	k3.visible = sh == "k3"
	k4.visible = sh == "k4"
	k5.visible = sh == "k5"
	var g := c4g()
	# k1: the car rolls into the arch and is gone; its lights in the passage fade
	k1.position = Vector2(0.0, -k1_offset(time))
	var cp: Array = C.get("car_path", [[560, 476], [-150, 476]])
	var cc: Array = C.get("car_cell", [200, 70])
	var u := car_u(time)
	_car.visible = time < float(CAR_T[1])
	_car.frame = posmod(int(floor(u * 18.0)), 6)
	var p := Vector2(float(cp[0][0]), float(cp[0][1])).lerp(Vector2(float(cp[1][0]), float(cp[1][1])), u)
	_car.position = Vector2(roundf(p.x - float(cc[0]) / 2.0), roundf(p.y - float(cc[1])))
	_passage.visible = time >= float(CAR_T[1]) - 0.6
	_passage.modulate = Color(1, 1, 1, clampf(1.0 - (time - float(CAR_T[1])) / 1.4, 0.0, 1.0))
	_candle.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 31, 0.18), 0.0, 1.0))
	# k2: the door, the people, the witness, the flash
	_door.visible = door_open(time)
	var de: Array = C.get("door_e", [452, 216, 462, 226])
	var dx := float(de[0]) + 2.0
	var floor_y := float(de[3]) - 14.0
	if g == "protect_first":
		_witness.visible = false
		var w: Array = C.get("wagon", [500, 560, 208, 226])
		for i in 2:
			var s: Sprite2D = _people[i]
			var t0 := float(CROSS[0]) + i * 0.5
			var uu := clampf((time - t0) / (float(CROSS[1]) - float(CROSS[0]) - 0.5), 0.0, 1.0)
			s.visible = time >= DOOR_OPEN + 0.2 and uu < 1.0
			s.flip_h = true
			s.position = Vector2(roundf(lerpf(dx, float(w[0]) + 26.0, uu)) - 8.0, floor_y)
			s.frame = p2_loop_frame(time, 4.0, 2, i)
		_escort.visible = time >= DOOR_OPEN + 0.1 and time < DOOR_SHUT
		_escort.flip_h = true
		_escort.position = Vector2(dx - 12.0, floor_y)
		_escort.frame = 0
		_flash.visible = false
	else:
		_witness.visible = true
		_witness.frame = 1 if time >= FLASH_T - 0.35 and time < FLASH_T + 1.2 else 0
		var hall: Array = C.get("hall", [250, 470, 196, 226])
		for i in 2:
			var s: Sprite2D = _people[i]
			var uu := clampf((time - float(LED_BACK[0]) - i * 0.4) / (float(LED_BACK[1]) - float(LED_BACK[0]) - 0.4), 0.0, 1.0)
			s.visible = time >= float(LED_BACK[0]) - 0.2 and uu < 1.0
			s.flip_h = false
			s.position = Vector2(roundf(lerpf(dx - 20.0, float(hall[0]) + 46.0, uu)) - 8.0, floor_y)
			s.frame = p2_loop_frame(time, 4.0, 2, i)
		var ue := clampf((time - float(LED_BACK[0]) - 0.9) / (float(LED_BACK[1]) - float(LED_BACK[0]) - 0.9), 0.0, 1.0)
		_escort.visible = time >= float(LED_BACK[0]) and ue < 1.0
		_escort.flip_h = false
		_escort.position = Vector2(roundf(lerpf(dx - 4.0, float(hall[0]) + 46.0, ue)) - 8.0, floor_y)
		_escort.frame = p2_loop_frame(time, 4.0, 2)
		var rm := reduced_motion()
		var fa := time - FLASH_T
		_flash.visible = fa >= 0.0 and fa < (0.9 if rm else 0.36)
		_flash.frame = 2 if rm else clampi(int(floor(fa / 0.12)), 0, 2)
		_flash.modulate = Color(1, 1, 1, 0.55 * (1.0 - clampf(fa / 0.9, 0.0, 1.0)) if rm else 1.0)
	# k3: the tape grows out of the slot, Irina reads it, the second hand ticks
	var xs: Array = (C.get("tape_x", {}) as Dictionary).get(g, [])
	var n := typed(time)
	var tw := float(xs[n - 1]) + 2.0 if n > 0 and xs.size() >= n else 0.0
	var tt: Array = C.get("tty", [500, 196])
	for v in _tapes:
		var tp: Sprite2D = _tapes[v]
		tp.visible = v == g and n > 0
		tp.region_rect = Rect2(0, 0, maxf(1.0, tw), 11)
		tp.position = Vector2(float(tt[0]) - tw - 12.0, float(tt[1]) - 1.0)
	_irina.frame = (once_frame(time, 12.4, 13.4, 6)) if time < 14.4 else 6 + p2_loop_frame(time, 4.0, 4)
	_alexei.frame = p2_loop_frame(time, 4.0, maxi(1, _alexei.hframes))
	_levglow.modulate = Color(1, 1, 1, clampf(0.85 + 0.08 * hnoise(time * 1.6, 37), 0.0, 1.0))
	# k4: the decision on the desk
	_canister.visible = g == "protect_first"
	_folder.visible = g != "protect_first"
	for s in [_snow1, _snow2]:
		s.set_time(time)
	for n2 in [_hand, _fx4, _motes]:
		n2.queue_redraw()


## the second hand of the dispatch clock: one tick per second (pure function of t)
func second_angle(time: float) -> float:
	return deg_to_rad(6.0 * floor(time) + 120.0)


func _draw_hand() -> void:
	var c: Array = C.get("clock_c", [330, 104])
	var a := second_angle(t)
	var o := Vector2(float(c[0]), float(c[1]))
	FX.line(_hand, o, o + Vector2(sin(a), -cos(a)) * 17.0, Color("#9a1e16"))


func _draw_fill() -> void:
	_fill.draw_rect(Rect2(-20, -20, 680, 400), Color.BLACK)


func _draw_k4() -> void:
	if t < 16.0 or t >= 20.0:
		return
	puffs(_fx4, _t_tea, 8, t, 13.0, 21.0, 0.6, 2.4, Vector2(560, 92), Vector2(2, -9), 611, Color(1, 1, 1, 0.5),
		Vector2(1, 1))


func _draw_motes() -> void:
	if t < 16.0 or t >= 20.0:
		return
	var k := motion_k()
	for i in 16:
		var x := 200.0 + fposmod(hnoise(i * 1.3, 621) * 200.0 + t * (3.0 + i % 4) * k, 300.0)
		var y := 90.0 + fposmod(hnoise(i * 2.1, 623) * 120.0 + sin(t * 0.7 + i) * 6.0 * k, 160.0)
		var a := clampf(0.35 + 0.3 * hnoise(t * 0.5 + i, 625), 0.0, 1.0)
		_motes.draw_rect(Rect2(roundf(x), roundf(y), 1, 1), Color(1.0, 0.9, 0.7, a))
