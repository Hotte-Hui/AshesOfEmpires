extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## LS_C3_Fire (12 s) — the registry catches fire (C3P2_DESIGN §2.9).  Nobody is hurt on screen; the arsonist is
## never identifiable (a backlit silhouette in a long coat and a porter's cap, seen from behind).
##   f1  0-3     the green lamp flickers over the sorting table; a wisp of smoke in its light; Konrad looks up
##   f2  3-6     the Magazin aisle: a figure slips out through the lit service door at the end, the C-17 boxes
##               catch, the orange glow grows between the shelves
##   f3  6-8.5   the ramp door from inside: the cold gap light, a shadow passes outside, the iron bolt slides home
##   f4  8.5-12  the card hall burning: the fire runs along the cabinets (right -> left), smoke rolls under the
##               vault toward the camera, embers; Alexei at the table, a silhouette against the fire
## Line: cin.c3p2.fire.time.  Fire light: flame sheets cycle their shapes, the brightness only wobbles slowly
## (< 3 Hz, fire_wobble), never a full-screen flash; reduced motion halves the flame rate and the wobble.
## Art: tools/pixelgen/env_c3p2_cine_fire.py -> assets/cinematics/c3p2/fire/ (+ layout.json "fire").

const DUR := 12.0
const SHOTS := [["f1", 0.0, 3.0], ["f2", 3.0, 6.0], ["f3", 6.0, 8.5], ["f4", 8.5, 12.0]]
const LINE_TIME := "cin.c3p2.fire.time"
const LOOK_UP := 1.75                 # Konrad lifts his head
const DOOR := [3.0, 3.45, 3.85, 4.3]  # figure in the doorway, half out, empty lit doorway, door shut
const CATCH := 3.55                   # the first C-17 box catches
const SHADOW := [6.35, 6.95]          # someone passes outside the ramp door
const BOLT := [7.2, 7.55]             # the bolt slides home
const RUN := [8.3, 220.0]             # f4 fire front: start time, speed (px/s, right -> left)
## f1 lamp flicker dips (== LAMP_DIPS in tools/audiogen/c3p2_cine_audio.py: the crackles of c3p2cine_lamp)
const LAMP_DIPS := [0.55, 1.05, 1.4, 2.4]

var f1: Node2D
var f2: Node2D
var f3: Node2D
var f4: Node2D
var _cone: Sprite2D
var _konrad: Sprite2D
var _f1fx: Node2D
var _f2glow: Sprite2D
var _door: Sprite2D
var _f2fx: Node2D
var _f3warm: Sprite2D
var _f3fx: Node2D
var _f4glow: Sprite2D
var _f4cone: Sprite2D
var _f4fire: Node2D
var _alexei: Sprite2D
var _f4fx: Node2D
var _flame: Texture2D
var _flame_s: Texture2D
var _flame_big: Texture2D
var _flame_wide: Texture2D
var _smoke: Texture2D
var _ember: Texture2D
var _f3root: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return [LINE_TIME]


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c3p2cine_lamp", "db": -8.0},
		{"t": 0.4, "say": LINE_TIME, "dur": 2.2},
		{"t": 3.0, "bed": "c3p2cine_ignite", "db": -5.0},
		{"t": DOOR[3] - 0.05, "sfx": "c3p2cine_service_door", "db": -11.0, "pv": 0.02},
		{"t": SHADOW[0] - 0.2, "bed": "c3p2cine_steps_out", "db": -10.0},
		{"t": BOLT[0] - 0.05, "bed": "c3p2cine_bolt", "db": -3.0},
		{"t": 8.5, "bed": "c3p2cine_roar", "db": -4.0},
	]


# ------------------------------------------------------------------ build
func _build() -> void:
	layout = _layout_section("fire")
	_flame = tex("fire/flame.png")
	_flame_s = tex("fire/flame_s.png")
	_flame_big = tex("fire/flame_big.png")
	_flame_wide = tex("fire/flame_wide.png")
	_smoke = tex("fire/smoke.png")
	_ember = tex("fire/ember.png")
	f1 = group("SortingTable")
	sprite("fire/f1_bg.png", Vector2.ZERO, f1)
	_cone = sprite("fire/lamp_cone.png", Vector2.ZERO, f1, 1, true)
	_konrad = sprite("fire/f1_konrad.png", _lv("f1_konrad"), f1, 2)
	_f1fx = _fx_node(f1, "F1Fx", _draw_f1)
	f2 = group("Stacks")
	sprite("fire/f2_bg.png", Vector2.ZERO, f2)
	_door = sprite("fire/f2_door.png", _lv("f2_door_at"), f2, 4)
	_f2glow = sprite("fire/f2_glow.png", Vector2.ZERO, f2, 1, true)
	_f2fx = _fx_node(f2, "F2Fx", _draw_f2)
	f3 = group("RampDoor")
	_f3root = Node2D.new()
	_f3root.name = "Shake"
	f3.add_child(_f3root)
	sprite("fire/f3_bg.png", Vector2.ZERO, _f3root)
	_f3warm = sprite("fire/f3_warm.png", Vector2.ZERO, _f3root, 1, true)
	_f3fx = _fx_node(_f3root, "F3Fx", _draw_f3)
	f4 = group("HallBurning")
	sprite("fire/f4_bg.png", Vector2.ZERO, f4)
	_f4glow = sprite("fire/f4_glow.png", Vector2.ZERO, f4, 1, true)
	_f4cone = sprite("fire/lamp_cone.png", Vector2.ZERO, f4, 1, true)
	_f4fire = _fx_node(f4, "Fire", _draw_f4_fire)
	_alexei = sprite("fire/f4_alexei.png", _lv("f4_alexei"), f4, 2)
	_f4fx = _fx_node(f4, "SmokeEmbers", _draw_f4_fx)


func _fx_node(parent: Node, n: String, fn: Callable) -> Node2D:
	var d := Node2D.new()
	d.name = n
	d.draw.connect(fn)
	parent.add_child(d)
	return d


func _lv(key: String) -> Vector2:
	var v = layout.get(key)
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return Vector2.ZERO


# ------------------------------------------------------------------ frame
func _apply(time: float) -> void:
	if f1 == null:
		return
	var sh := shot_at(time)
	f1.visible = sh == "f1"
	f2.visible = sh == "f2"
	f3.visible = sh == "f3"
	f4.visible = sh == "f4"
	var rm := reduced_motion()
	# f1: the lamp flickers (three short dips, each ~0.15 s; softened with reduced motion)
	var dip := 0.0
	for c in LAMP_DIPS:
		dip = maxf(dip, 1.0 - absf(time - c) / 0.08)
	_cone.modulate = Color(1, 1, 1, 1.0 - clampf(dip, 0.0, 1.0) * (0.12 if rm else 0.38))
	_konrad.frame = 0 if time < LOOK_UP else 1
	_f1fx.queue_redraw()
	# f2: the doorway, the glow growing as the boxes catch
	var df := 0
	if time >= DOOR[3]:
		df = 3
	elif time >= DOOR[2]:
		df = 2
	elif time >= DOOR[1]:
		df = 1
	_door.frame = df
	var grow := ramp01(time, CATCH - 0.4, 6.0)
	_f2glow.modulate = Color(1, 1, 1, (0.35 + 0.65 * grow) * fire_wobble(time, 3))
	_f2fx.queue_redraw()
	# f3: the fire behind the camera warms the door more and more; the bolt jolts the door once
	_f3warm.modulate = Color(1, 1, 1, clampf((0.35 + 0.65 * ramp01(time, 6.0, 8.5)) * fire_wobble(time, 5), 0.0, 1.0))
	var jolt := 0.0
	if not rm and time >= BOLT[1] and time < BOLT[1] + 0.12:
		jolt = 1.0
	_f3root.position = Vector2(jolt, 0)
	_f3fx.queue_redraw()
	# f4
	var burnt := _burning_fraction(time)
	_f4glow.modulate = Color(1, 1, 1, clampf((0.45 + 0.55 * burnt) * fire_wobble(time, 9), 0.0, 1.0))
	_f4cone.modulate = Color(1, 1, 1, 0.35 - 0.2 * burnt)
	_alexei.frame = 0 if time < 10.4 else 1
	_f4fire.queue_redraw()
	_f4fx.queue_redraw()


func _front(time: float) -> float:
	return 680.0 - maxf(0.0, time - float(RUN[0])) * float(RUN[1]) * (0.8 if reduced_motion() else 1.0)


func _burning_fraction(time: float) -> float:
	return clampf((680.0 - _front(time)) / 700.0, 0.0, 1.0)


# ------------------------------------------------------------------ draw
func _draw_f1() -> void:
	if not f1.visible:
		return
	# a wisp of smoke drifting into the lamp's light from the right, thin at first
	if _smoke and t > 0.6:
		var n := 8
		var age := t - 0.6
		var x := 470.0 - age * 34.0 * motion_k()
		var y := 118.0 - age * 6.0 * motion_k()
		var fi := clampi(int(age / 0.45), 0, n - 1)
		var a := clampf(age / 1.2, 0.0, 1.0) * 0.55
		draw_frame(_f1fx, _smoke, n, fi, Vector2(x, y), false, Color(0.75, 0.85, 0.78, a))
	# dust motes in the cone
	for i in 12:
		var ph := float(i) * 2.3
		var mx := 300.0 + sin(ph + t * 0.6) * (40.0 + i * 6.0)
		var my := 120.0 + fposmod(i * 17.0 + t * 6.0 * motion_k(), 110.0)
		_f1fx.draw_rect(Rect2(Vector2(floorf(mx), floorf(my)), Vector2.ONE), Color(0.7, 0.9, 0.75, 0.5))


func _draw_f2() -> void:
	if not f2.visible:
		return
	var anchors: Array = layout.get("f2_fire", [])
	for i in anchors.size():
		var a: Array = anchors[i]
		var t0 := CATCH + i * 0.32
		if t < t0:
			continue
		var big := t >= t0 + 0.55
		var tx: Texture2D = _flame if big else _flame_s
		draw_frame(_f2fx, tx, 8, flame_frame(t, 8, i * 0.37), Vector2(float(a[0]), float(a[1]) + 2.0))
	# smoke from the shelf, rising along the aisle's ceiling toward the camera
	if _smoke and t > CATCH + 0.6:
		for k in 4:
			var age := t - CATCH - 0.6 - k * 0.5
			if age < 0.0:
				continue
			var x := 420.0 - age * 10.0 + k * 6.0
			var y := 150.0 - age * 26.0 * motion_k()
			draw_frame(_f2fx, _smoke, 8, clampi(int(age / 0.35), 0, 7), Vector2(x, y), false, Color(0.55, 0.45, 0.4, 0.85))


func _draw_f3() -> void:
	if not f3.visible:
		return
	var g: Array = layout.get("f3_gap", [470, 0, 473, 292])
	var gx := float(g[0])
	var gy1 := float(g[3])
	var cold := Color("#a1aab7")
	var hot := Color("#dee2e7")
	# the vertical gap and the bottom gap: cold yard light, darkened while someone passes
	var pass_k := 0.0
	if t >= SHADOW[0] and t < SHADOW[1]:
		pass_k = sin((t - SHADOW[0]) / (SHADOW[1] - SHADOW[0]) * PI)
	var lit := cold.lerp(Color("#1a2431"), pass_k * 0.85)
	_f3fx.draw_rect(Rect2(gx - 1, 0, 5, gy1), Color(lit, 0.35))
	_f3fx.draw_rect(Rect2(gx, 0, 3, gy1), lit)
	_f3fx.draw_rect(Rect2(gx + 1, 0, 1, gy1), hot.lerp(Color("#1a2431"), pass_k * 0.85))
	var fl: Array = layout.get("f3_floor", [150, 292, 473, 295])
	var bottom := Rect2(float(fl[0]), float(fl[1]), float(fl[2]) - float(fl[0]), 2)
	_f3fx.draw_rect(bottom, lit)
	# the shadow of the feet passing along the bottom gap (right to left)
	if pass_k > 0.0:
		var u := (t - SHADOW[0]) / (SHADOW[1] - SHADOW[0])
		var fx := lerpf(float(fl[2]) + 20.0, float(fl[0]) - 40.0, u)
		_f3fx.draw_rect(Rect2(fx, float(fl[1]), 30, 2), Color("#0c111c"))
	# the bolt: its shadow slides across the gap and onto the edge of the door
	if t >= BOLT[0]:
		var b := ramp01(t, BOLT[0], BOLT[1])
		var by := 132.0
		var blen := roundf(b * 30.0)
		# the bolt crosses the gap (no light there any more) and throws its shadow onto the door's edge
		_f3fx.draw_rect(Rect2(gx, by - 2, 3, 12), Color("#05070c"))
		_f3fx.draw_rect(Rect2(gx - blen + 3, by, blen, 8), Color(0.02, 0.03, 0.05, 0.8))
		_f3fx.draw_rect(Rect2(gx - blen + 3, by + 8, blen, 1), Color(0.6, 0.66, 0.74, 0.35))
	# snow blown through the bottom gap, drifting into the room
	for i in 16:
		var ph := float(i) * 1.37
		var age := fposmod(t * 0.9 + i * 0.19, 1.6)
		var x := float(fl[0]) + fposmod(i * 61.0, float(fl[2]) - float(fl[0]))
		var y := float(fl[1]) + 2.0 + age * 18.0 * motion_k()
		x -= age * 22.0 * motion_k() + sin(ph + t * 3.0) * 2.0
		_f3fx.draw_rect(Rect2(Vector2(floorf(x), floorf(y)), Vector2.ONE), Color(0.86, 0.89, 0.92, clampf(1.0 - age / 1.6, 0.0, 1.0)))


func _draw_f4_fire() -> void:
	if not f4.visible:
		return
	var fr := _front(t)
	var pts: Array = layout.get("f4_fire", [])
	for i in pts.size():
		var p: Array = pts[i]
		var x := float(p[0])
		if x < fr:
			continue
		var lit_t := float(RUN[0]) + (680.0 - x) / (float(RUN[1]) * (0.8 if reduced_motion() else 1.0))
		var age := t - lit_t
		var size := int(p[2]) if p.size() > 2 else 1
		var tx: Texture2D = [_flame, _flame_big, _flame_wide][clampi(size, 0, 2)]
		if age < 0.35:
			tx = _flame_s
		draw_frame(_f4fire, tx, 8, flame_frame(t, 8, i * 0.29), Vector2(x, float(p[1]) + 2.0))


func _draw_f4_fx() -> void:
	if not f4.visible:
		return
	var k := motion_k()
	# smoke rolling under the vault toward the camera: puffs born at the fire line, sinking and growing
	if _smoke:
		for i in 14:
			var born := 8.3 + i * 0.24
			var age := t - born
			if age < 0.0:
				continue
			var x := 600.0 - fposmod(i * 83.0, 640.0) + sin(i * 1.7 + t * 0.5) * 8.0
			var y := 36.0 + age * 16.0 * k
			var fi := clampi(int(age / 0.4), 0, 7)
			draw_frame(_f4fx, _smoke, 8, fi, Vector2(x, y + 48.0), false, Color(0.62, 0.5, 0.45, 0.92))
	# embers rising from the fire line
	if _ember:
		var fr := _front(t)
		for i in 26:
			var ph := float(i) * 1.91
			var x0 := 640.0 - fposmod(i * 47.0, 660.0)
			if x0 < fr:
				continue
			var age := fposmod(t * 0.8 + i * 0.13, 1.8)
			var x := x0 + sin(ph + t * 2.0) * 6.0
			var y := 200.0 - age * 70.0 * k
			draw_frame(_f4fx, _ember, 4, int(floor(t * 3.0 + i)) % 4, Vector2(x, y), false, Color(1, 1, 1, clampf(1.0 - age / 1.8, 0.0, 1.0)))
