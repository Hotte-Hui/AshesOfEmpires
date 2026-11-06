extends "res://scenes/cinematics/ch4p2_common/c4p2_cinematic.gd"
## LS_C4P2_Express (13 s) — Karsk -> Berlin, Tuesday.  The decision is shown, never explained (C4P2_DESIGN §2.9).
##   x1  0-4      side_on: platform 1, 20.10 -- close at the sleeping car; Ekdahl at his window lifts the film
##                canister to the glass (publish_now) or shows his empty hand and nods (protect_first) at GESTURE_T;
##                the brakes come off (TRAIN_T0) and the car pulls away to the left, accelerating
##   x2  4-8      fixed: looking west down the line, the last car's end recedes to the vanishing point (perspective
##                scale per frame); Alexei and Lev at the platform's edge -- Lev buttons the carbons back into his
##                coat (protect_first, CARBONS_T) or stands with empty hands (publish_now); the band packs up
##   x3  8-9.5    macro_locked: the tail lamp; one last rail joint at KNOCK_T (the picture jolts a pixel)
##                                 -- hard cut on the red circle (same place, same size) --
##   x4  9.5-13   tracking: Berlin, Kolonnenstraße 22.10 -- the building site's warning lamp close (x4a); Konrad's
##                coat sweeps past the lens (WIPE); the street: the camera follows Konrad under the lamp into the
##                gate passage of No. 14 (the in-game stride); an S-Bahn crosses the viaduct far behind
## Lines: Alexei's thought chosen by c4g_choose on x2, the place card on x4.  Beds (tools/audiogen/
## c4p2_cine_audio.py): c4p2cine_express (whistle, brakes off, the couplings taking up slack), c4p2cine_recede
## (wheels fading, the band's cases), c4p2cine_knock (the joint at KNOCK_T), c4p2cine_street (Konrad's steps, the
## S-Bahn, a radio behind a window).

const DUR := 13.0
const SHOTS := [["x1", 0.0, 4.0], ["x2", 4.0, 8.0], ["x3", 8.0, 9.5], ["x4", 9.5, 13.0]]
const LINE_PUBLISH := "cin.c4p2.express.alexei_publish"
const LINE_PROTECT := "cin.c4p2.express.alexei_protect"
const LINE_BERLIN := "cin.c4p2.express.berlin"
const WHISTLE := 0.3
const TRAIN_T0 := 0.95
const COUPLINGS := [1.02, 1.24, 1.47, 1.73]
const KNOCK_T := 8.4
const WIPE := [10.25, 10.7]
const SBAHN_T := [10.9, 12.6]

var X: Dictionary = {}
var x1: Node2D
var x2: Node2D
var x3: Node2D
var x4a: Node2D
var x4: Node2D
var _car: Node2D
var _ekdahl: Sprite2D
var _trail: Sprite2D
var _lev: Sprite2D
var _alexei: Sprite2D
var _band2: Array = []
var _lamp3: Node2D
var _glow3: Sprite2D
var _glow4: Sprite2D
var _coat: Sprite2D
var _street: Node2D
var _konrad: Sprite2D
var _sbahn: Sprite2D
var _snow1: Node2D
var _snow2: Node2D
var _snow3: Node2D
var _snow4: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func _inner() -> String:
	return LINE_PROTECT if c4g() == "protect_first" else LINE_PUBLISH


func chosen_lines() -> Array:
	return [_inner(), LINE_BERLIN]


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "bed": "c4p2cine_express", "db": -3.0},
		{"t": 4.0, "bed": "c4p2cine_recede", "db": -4.0},
		{"t": 8.0, "bed": "c4p2cine_knock", "db": -3.0},
		{"t": 9.5, "bed": "c4p2cine_street", "db": -4.0},
	]
	c += schedule([{"key": _inner(), "at": 4.15, "dur": line_dur(_inner(), 1.4, 6.0)},
		{"key": LINE_BERLIN, "at": 9.65, "dur": line_dur(LINE_BERLIN)}])
	c += optional_amb(0.0, "amb_karsk_platform", 1.0)
	c += optional_amb(9.5, "amb_berlin_courtyard", 0.5)
	return c


## x1: the car's offset (it starts at TRAIN_T0 and accelerates to the left)
func car_x(time: float) -> float:
	var a := float(X.get("train_a", 26.0))
	var dt := maxf(0.0, time - float(X.get("train_t0", TRAIN_T0)))
	return roundf(-0.5 * a * dt * dt * motion_k())


## x1: Ekdahl's frame -- 0 hands down, 1 the canister up, 2 the empty hand, 3 the nod
func ekdahl_frame(time: float) -> int:
	if time < float(X.get("gesture_t", 0.6)):
		return 0
	if c4g() == "publish_now":
		return 1
	var nod: Array = X.get("nod_t", [1.55, 2.25])
	return 3 if time >= float(nod[0]) and time < float(nod[1]) else 2


## x2: the receding car's frame (perspective step) and its bottom-centre on the track
func trail_frame(time: float) -> int:
	var tt: Array = X.get("trail_t", [4.0, 8.0])
	var n := int(X.get("trail_n", 14))
	return clampi(int(floor(ease_out(time, float(tt[0]), float(tt[1])) * float(n - 1) + 0.0001)), 0, n - 1)


func trail_pos(i: int) -> Vector2:
	var vp: Array = X.get("vp", [138, 200])
	var tb: Array = X.get("track_b", [-60, 230])
	var ks: Array = X.get("trail_k", [])
	var k := float(ks[i]) if i < ks.size() else 0.1
	var mid := (float(tb[0]) + float(tb[1])) / 2.0
	return Vector2(float(vp[0]) + (mid - float(vp[0])) * k, float(vp[1]) + (360.0 - float(vp[1])) * k).round()


## x2: Lev's frame -- publish_now: 0..7 his empty hands rise into the picture, palms up, and sink (EMPTY_T);
## protect_first: 8..13 the white bundle of carbons goes back under his coat (CARBONS_T)
func lev_frame(time: float) -> int:
	if c4g() == "protect_first":
		var ct: Array = X.get("carbons_t", [4.6, 6.4])
		return 8 + once_frame(time, float(ct[0]), float(ct[1]), 6) if time >= float(ct[0]) else 8
	var et: Array = X.get("empty_t", [4.5, 6.9])
	if time < float(et[0]) or time >= float(et[1]):
		return 0
	return once_frame(time, float(et[0]), float(et[1]), 8)


## x4: Konrad's feet x (walking from the wipe's middle) and the camera's left edge in the street
func konrad_x(time: float) -> float:
	var kx: Array = X.get("x4_konrad", [586, 730])
	return float(walk_x(time, (WIPE[0] + WIPE[1]) / 2.0, float(kx[0]), float(kx[1]))[0])


## Film times Konrad's shoes land in the street (from the wipe's middle, every 18 px) until the film ends.
func konrad_steps() -> Array:
	var kx: Array = X.get("x4_konrad", [586, 730])
	var t0 := (WIPE[0] + WIPE[1]) / 2.0
	var span := absf(float(kx[1]) - float(kx[0]))
	var out: Array = []
	var d := 0.0
	while d < span - 0.001 and t0 + d / WALK_SPEED < DUR:
		out.append(snappedf(t0 + d / WALK_SPEED, 0.001))
		d += STRIDE * 4.0
	return out


func street_cam(time: float) -> float:
	return clampf(roundf(konrad_x(time) - 300.0), 0.0, float(X.get("street_w", 1100)) - 640.0)


func _build() -> void:
	X = _layout_section("express")
	# ---------------------------------------------------------------- x1
	x1 = group("Express")
	_car = Node2D.new()
	_car.name = "Car"
	x1.add_child(_car)
	sprite("express/x1_car.png", Vector2.ZERO, _car)
	var ea: Array = X.get("ekdahl_at", [238, 104])
	_ekdahl = sprite("express/x1_ekdahl.png", Vector2(float(ea[0]), float(ea[1])), _car)
	if _ekdahl.texture:
		_ekdahl.hframes = 4
	sprite("express/x1_frames.png", Vector2.ZERO, _car)
	sprite("express/x1_platform.png", Vector2.ZERO, x1)
	_snow1 = snow(x1, Rect2(-20, 30, 680, 300), [
		{"count": 44, "v": Vector2(-8, 18), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#c8d0dc"), "sway": 2.0},
		{"count": 14, "v": Vector2(-14, 34), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#eef2f6"), "sway": 3.0},
	], 4501)
	# ---------------------------------------------------------------- x2
	x2 = group("Platform")
	sprite("express/x2_bg.png", Vector2.ZERO, x2)
	var tc: Array = X.get("trail_cell", [174, 214])
	_trail = cells("express/x2_trail.png", x2, int(tc[0]))
	var bands: Array = X.get("x2_band", [])
	for k in bands.size():
		var e: Array = bands[k]
		_band2.append(cells("express/x2_band_%d.png" % k, x2, 32, Vector2(float(e[0]), float(e[1]))))
	var al: Array = X.get("x2_alexei", [82, 216])
	_alexei = cells("express/x2_alexei.png", x2, int(X.get("x2_alexei_cell", 240)), Vector2(float(al[0]), float(al[1])))
	var lv_: Array = X.get("x2_lev", [378, 206])
	var lc: Array = X.get("x2_lev_cell", [160, 140])
	_lev = cells("express/x2_lev.png", x2, int(lc[0]), Vector2(float(lv_[0]), float(lv_[1])))
	_snow2 = snow(x2, Rect2(-20, 30, 680, 300), [
		{"count": 50, "v": Vector2(-6, 16), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#aab4c4"), "sway": 2.0},
	], 4502)
	# ---------------------------------------------------------------- x3
	x3 = group("TailLamp")
	_lamp3 = Node2D.new()
	_lamp3.name = "Lamp"
	x3.add_child(_lamp3)
	sprite("express/x3_lamp.png", Vector2.ZERO, _lamp3)
	_glow3 = glow("express/lamp_glow.png", _lamp3)
	_snow3 = snow(x3, Rect2(-20, 30, 680, 300), [
		{"count": 30, "v": Vector2(-30, 22), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#d8dde4"), "sway": 3.0},
	], 4503)
	# ---------------------------------------------------------------- x4a + x4
	x4a = group("WarningLamp")
	sprite("express/x4_lamp.png", Vector2.ZERO, x4a)
	_glow4 = glow("express/lamp_glow.png", x4a)
	x4 = group("Street")
	_street = Node2D.new()
	_street.name = "Pan"
	x4.add_child(_street)
	sprite("express/x4_far.png", Vector2.ZERO, _street)
	_sbahn = sprite("express/x4_sbahn.png", Vector2(-240, 126), _street)
	sprite("express/x4_street.png", Vector2.ZERO, _street)
	_konrad = cells("express/x4_konrad.png", _street, 32)
	glow("express/x4_glow.png", _street)
	_snow4 = snow(x4, Rect2(-20, 30, 680, 300), [
		{"count": 46, "v": Vector2(-5, 14), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#9aa8c4"), "sway": 2.0},
		{"count": 16, "v": Vector2(-9, 24), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#dce4f0"), "sway": 3.0},
	], 4504)
	_coat = sprite("express/coat.png", Vector2(-900, 0), self)


func _apply(time: float) -> void:
	if x1 == null:
		return
	var sh := shot_at(time)
	var wipe_mid := (WIPE[0] + WIPE[1]) / 2.0
	x1.visible = sh == "x1"
	x2.visible = sh == "x2"
	x3.visible = sh == "x3"
	x4a.visible = sh == "x4" and time < wipe_mid
	x4.visible = sh == "x4" and time >= wipe_mid
	# x1
	_car.position = Vector2(car_x(time), 0)
	_ekdahl.frame = ekdahl_frame(time)
	# x2
	var fi := trail_frame(time)
	_trail.frame = fi
	var tc: Array = X.get("trail_cell", [174, 214])
	var tp := trail_pos(fi)
	_trail.position = Vector2(tp.x - roundf(float(tc[0]) / 2.0), tp.y - float(tc[1]))
	_lev.frame = lev_frame(time)
	_alexei.frame = p2_loop_frame(time, 2.0, maxi(1, _alexei.hframes), 2)
	for k in _band2.size():
		var b2: Sprite2D = _band2[k]
		b2.frame = p2_loop_frame(time, 3.0, maxi(1, b2.hframes), k * 3)
	# x3: the last rail joint
	var jolt := 1.0 if time >= KNOCK_T and time < KNOCK_T + 0.09 else 0.0
	_lamp3.position = Vector2(0, jolt)
	_glow3.modulate = Color(1, 1, 1, clampf(0.9 + 0.05 * hnoise(time * 1.4, 23), 0.0, 1.0))
	_glow4.modulate = Color(1, 1, 1, clampf(0.92 + 0.04 * hnoise(time * 1.2, 29), 0.0, 1.0))
	# x4: the coat sweeps past, then the street follows Konrad
	var wu := ease01(time, WIPE[0], WIPE[1])
	_coat.visible = time >= WIPE[0] and time < WIPE[1]
	_coat.position = Vector2(roundf(-900.0 + 1540.0 * wu), 0)
	var cam := street_cam(time)
	_street.position = Vector2(-cam, 0)
	var kx := konrad_x(time)
	var k0 := float((X.get("x4_konrad", [586, 730]) as Array)[0])
	_konrad.frame = walk_i(kx - k0) % maxi(1, _konrad.hframes)
	_konrad.position = Vector2(roundf(kx - 16.0), float(X.get("x4_feet", 300)) - 54.0)
	var gate: Array = X.get("gate", [700, 800])
	var inside := clampf((kx - float(gate[0])) / 30.0, 0.0, 1.0)
	_konrad.modulate = Color(1.0 - 0.55 * inside, 1.0 - 0.55 * inside, 1.0 - 0.5 * inside)
	var su := clampf((time - SBAHN_T[0]) / (SBAHN_T[1] - SBAHN_T[0]), 0.0, 1.0)
	_sbahn.visible = time >= SBAHN_T[0] and time <= SBAHN_T[1]
	_sbahn.position = Vector2(roundf(-240.0 + (float(X.get("street_w", 1100)) + 240.0) * su), 126)
	for s in [_snow1, _snow2, _snow3, _snow4]:
		s.set_time(time)
