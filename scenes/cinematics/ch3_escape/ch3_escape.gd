extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## LS_C3_Escape (16 s) — out through the 1909 coal chute (C3P2_DESIGN §2.9).  No injury shown: soot, coughing,
## the cold.
##   e1  0-4     up the chute: coal dust in the light, the file shoved ahead toward the square of snow light
##   e2  4-8     the yard: the iron hatch flips open, smoke pours out, Konrad crawls out with the file
##   e3  8-12    a: Alexei's hand out of the smoke, Konrad's hand takes it, he pulls (8-10.2)
##               b: the hatch slams; both on their backs in the snow, coughing, their breath rising (10.2-12)
##   e4  12-16   the east wing from the lane: the souterrain windows burst orange one after another, smoke and
##               snow, the fire brigade's bells approaching
## No inner lines (the picture and the sound carry it).  Reduced motion: half travel, no window flash frames.
## Round 10: snow falls into the chute from the square of light, the yard has its coal heap, barrels, the gate and
## the lane's lamp, the window and the hatch glow and flicker; sparks rise out of the hatch; in the lane the windows
## burst with flames licking out and glass glinting into the snow, onlookers watch the wing and two firemen run in
## as the bells come close (a slow blue beacon from the right).
## Round 11: the iron lid is opaque cast iron (tread plate under melting snow; open, its ribbed sooted underside
## with the cast date); all smoke is soft and volumetric; in the lane each burst window throws its flames up the
## facade and a column of smoke that merges into one mass under the cornice (the snow falls in front of it), the
## glass flies out in glinting shards that stay twinkling in the snow, the onlookers flinch, step back, point and
## wave, and the fire engine noses into the lane from the right, its blue beacon turning on the cab and washing
## the snow and the facade.
## Art: tools/pixelgen/env_c3p2_cine_fire.py (+ _yard, _life) -> assets/cinematics/c3p2/escape/.

const DUR := 16.0
const SHOTS := [["e1", 0.0, 4.0], ["e2", 4.0, 8.0], ["e3", 8.0, 12.0], ["e4", 12.0, 16.0]]
const E3B := 10.2                     # e3: the hands -> lying in the snow
const PUSHES := [0.35, 1.55, 2.75]    # e1: the file is shoved up the slide
const LID := [4.35, 4.65]             # e2: the lid lifts, flips open
## round 11 (figures stream): e2 -- out to the shoulders, to the waist, a knee on the rim, on all fours beside the
## hatch, two crawl steps (no jump); e3a -- the hand rises, opens, Konrad's hand comes in, closes, the pull in 3 steps
const KONRAD := [4.95, 5.45, 5.95, 6.45, 6.95, 7.45]
const HANDS := [8.0, 8.5, 8.95, 9.2, 9.45, 9.75, 10.0]
const SLAM := 10.45
const BURST0 := 12.35                 # e4: first window bursts; the others follow every BURST_GAP
const BURST_GAP := 0.42
const BURST_ORDER := [3, 2, 4, 1, 5, 0, 6]
const ENGINE := [14.5, 15.7, 664.0, 560.0, 318.0]   # e4: the engine noses in: t0, t1, x from, x to, wheels' y
const BEACON_HZ := 0.9                               # its beacon turns (well under 3 Hz)

var e1: Node2D
var e2: Node2D
var e3a: Node2D
var e3b: Node2D
var e4: Node2D
var _light1: Sprite2D
var _file: Sprite2D
var _e1fx: Node2D
var _hatch: Sprite2D
var _konrad: Sprite2D
var _e2fx: Node2D
var _snow2: Node2D
var _hands: Sprite2D
var _e3afx: Node2D
var _e3glow: Sprite2D
var _hatch_b: Sprite2D
var _men: Sprite2D
var _e3bfx: Node2D
var _snow3: Node2D
var _e4glow: Sprite2D
var _windows: Array = []
var _e4fx: Node2D
var _snow4: Node2D
var _smoke: Texture2D
var _breath: Texture2D
var _flame_s: Texture2D
var _e2lamp: Sprite2D
var _e4people: Node2D
var _people: Array = []
var _beacon: Node2D
var _flame_out: Texture2D
var _halo: Texture2D
var _engine: Node2D
var _engine_tex: Texture2D
var _beacon_tex: Texture2D
var _wash_tex: Texture2D
var _e4heat: Node2D
var _e4smoke: Node2D
var _people_tex: Dictionary = {}


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return []


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c3p2cine_chute", "db": -6.0},
		{"t": LID[0] - 0.05, "bed": "c3p2cine_hatch_open", "db": -4.0},
		{"t": KONRAD[0], "bed": "c3p2cine_cough_k", "db": -8.0},
		{"t": HANDS[0], "bed": "c3p2cine_pull", "db": -7.0},
		{"t": SLAM - 0.02, "sfx": "c3p2cine_hatch_slam", "db": -3.0, "pv": 0.02},
		{"t": SLAM + 0.2, "bed": "c3p2cine_cough_both", "db": -7.0},
		{"t": BURST0 - 0.05, "bed": "c3p2cine_burst", "db": -5.0},
		{"t": 12.6, "bed": "c3p2cine_brigade", "db": -9.0},
	]


# ------------------------------------------------------------------ build
func _build() -> void:
	layout = _layout_section("escape")
	_smoke = tex("escape/smoke.png")
	_breath = tex("escape/breath.png")
	_flame_s = tex("escape/flame_s.png")
	e1 = group("Chute")
	sprite("escape/e1_bg.png", Vector2.ZERO, e1)
	_light1 = sprite("escape/e1_light.png", Vector2.ZERO, e1, 1, true)
	_e1fx = _fx(e1, "Dust", _draw_e1)
	_file = sprite("escape/e1_file.png", Vector2.ZERO, e1, 2)
	e2 = group("Yard")
	sprite("escape/e2_bg.png", Vector2.ZERO, e2)
	_e2lamp = sprite("escape/e2_lamp.png", Vector2.ZERO, e2, 1, true)
	_hatch = sprite("escape/e2_hatch.png", _lv("hatch_at"), e2, 3)
	_e2fx = _fx(e2, "Smoke", _draw_e2)
	_konrad = sprite("escape/e2_konrad.png", _lv("e2_konrad"), e2, KONRAD.size())
	_snow2 = snow(e2, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(6, 16), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 30, "v": Vector2(9, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9201)
	e3a = group("Hands")
	sprite("escape/e3a_bg.png", Vector2.ZERO, e3a)
	_e3glow = sprite("escape/e3a_glow.png", Vector2.ZERO, e3a, 1, true)
	_e3afx = _fx(e3a, "Smoke", _draw_e3a)
	_hands = sprite("escape/e3a_hands.png", _lv("e3_hands"), e3a, HANDS.size())
	e3b = group("Snow")
	sprite("escape/e3b_bg.png", Vector2.ZERO, e3b)
	_hatch_b = sprite("escape/e3b_hatch.png", _lv("e3b_hatch"), e3b, 2)
	_men = sprite("escape/e3b_men.png", _lv("e3b_men"), e3b, 2)
	_e3bfx = _fx(e3b, "Breath", _draw_e3b)
	_snow3 = snow(e3b, Rect2(0, 0, 640, 360), [
		{"count": 70, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 26, "v": Vector2(8, 28), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9202)
	e4 = group("EastWing")
	sprite("escape/e4_bg.png", Vector2.ZERO, e4)
	_e4glow = sprite("escape/e4_glow.png", Vector2.ZERO, e4, 1, true)
	for w in layout.get("e4_windows", []):
		_windows.append(sprite("escape/e4_window.png", Vector2(float(w[0]), float(w[1])), e4, 3))
	_flame_out = tex("escape/flame_out.png")
	_halo = tex("escape/fire_halo.png")
	_engine_tex = tex("escape/engine.png")
	_beacon_tex = tex("escape/beacon.png")
	_wash_tex = tex("escape/beacon_wash.png")
	_e4fx = _fx(e4, "Flames", _draw_e4)
	_e4heat = _fx(e4, "Heat", _draw_e4_heat)
	_e4heat.material = additive()
	for d in layout.get("e4_people", []):
		var tx2 := tex(str(d["file"]))
		if tx2:
			_people.append({"tex": tx2, "d": d})
		for sq_ in (d as Dictionary).get("seq", []):
			var f := str(sq_["file"])
			if not _people_tex.has(f):
				_people_tex[f] = tex(f)
	_e4people = _fx(e4, "People", _draw_people)
	_engine = _fx(e4, "Engine", _draw_engine)
	_e4smoke = _fx(e4, "SmokeMass", _draw_e4_smoke)
	_beacon = _fx(e4, "Beacon", _draw_beacon)
	_beacon.material = additive()
	_snow4 = snow(e4, Rect2(0, 0, 640, 360), [
		{"count": 110, "v": Vector2(4, 13), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 40, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0},
		{"count": 12, "v": Vector2(9, 38), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#dee2e7"), "sway": 4.0}], 9203)


func _fx(parent: Node, n: String, fn: Callable) -> Node2D:
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
	if e1 == null:
		return
	var sh := shot_at(time)
	e1.visible = sh == "e1"
	e2.visible = sh == "e2"
	e3a.visible = sh == "e3" and time < E3B
	e3b.visible = sh == "e3" and time >= E3B
	e4.visible = sh == "e4"
	var rm := reduced_motion()
	var k := motion_k()
	# e1: the file goes up the slide in three shoves; the lid lifts at the end (more light)
	var up := 0.0
	var shoving := false
	for p in PUSHES:
		up += ramp01(time, p, p + 0.4) * 16.0 * k
		if time >= p and time < p + 0.4:
			shoving = true
	_file.frame = 1 if shoving else 0
	if _file.texture:
		var fw := _file.texture.get_width() / 2
		var fh := _file.texture.get_height()
		_file.position = Vector2(roundf(320.0 - fw * 0.5), roundf(334.0 - fh - up))
	_light1.modulate = Color(1, 1, 1, 0.7 + 0.3 * ramp01(time, 3.2, 3.9))
	_e1fx.queue_redraw()
	# e2: the lid, Konrad
	_hatch.frame = 0 if time < LID[0] else (1 if time < LID[1] else 2)
	var kf := -1
	for i in KONRAD.size():
		if time >= KONRAD[i]:
			kf = i
	_konrad.visible = kf >= 0
	_konrad.frame = maxi(kf, 0)
	_snow2.set_time(time * (0.6 if rm else 1.0))
	_e2lamp.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 25, 0.1), 0.0, 1.0))
	_e2fx.queue_redraw()
	# e3a: the hand rises out of the smoke, is taken, both pulled up
	var hf := 0
	for i in HANDS.size():
		if time >= HANDS[i]:
			hf = i
	_hands.frame = hf
	var rise := (1.0 - ramp01(time, HANDS[0], HANDS[1])) * 46.0
	_hands.position = _lv("e3_hands") + Vector2(0, roundf(rise))
	_e3glow.modulate = Color(1, 1, 1, clampf(0.85 * fire_wobble(time, 21), 0.0, 1.0))
	_e3afx.queue_redraw()
	# e3b: the slam, the men breathing hard (coughing: quick heaves)
	_hatch_b.frame = 0 if time < SLAM else 1
	var rate := 1.6 if rm else 3.0
	_men.frame = int(floor((time - E3B) * rate)) % 2 if time >= E3B else 0
	_snow3.set_time(time * (0.6 if rm else 1.0))
	_e3bfx.queue_redraw()
	# e4: the windows burst one after another
	var burning := 0
	for j in _windows.size():
		var order: int = BURST_ORDER.find(j) if BURST_ORDER.has(j) else j
		var tb := BURST0 + order * BURST_GAP
		var s := _windows[j] as Sprite2D
		if time < tb:
			s.frame = 0
		elif time < tb + 0.12 and not rm:
			s.frame = 1
		else:
			s.frame = 2
		if time >= tb:
			burning += 1
	var frac := float(burning) / maxf(1.0, float(_windows.size()))
	_e4glow.modulate = Color(1, 1, 1, clampf(frac * fire_wobble(time, 23), 0.0, 1.0))
	_snow4.set_time(time * (0.6 if rm else 1.0))
	_e4fx.queue_redraw()
	_e4heat.queue_redraw()
	_e4smoke.queue_redraw()
	_e4people.queue_redraw()
	_engine.queue_redraw()
	_beacon.queue_redraw()


# ------------------------------------------------------------------ e4 life
## onlookers in the lane watching the wing, each reacting to the burst nearest to them (a take sequence from the
## generator: flinch, hands to the face, a step back, pointing, walking to wave the engine in); two firemen run in
## from the right as the bells come close
func _draw_people() -> void:
	if not e4.visible:
		return
	var rmk := 0.6 if reduced_motion() else 1.0
	for pp in _people:
		var d: Dictionary = pp["d"]
		var tx2: Texture2D = pp["tex"]
		var n := int(d.get("n", 1))
		var fps := float(d.get("fps", 0))
		var t0 := float(d.get("t0", 12.0))
		var at: Array = d["at"]
		var to: Array = d.get("to", at)
		var t1 := float(d.get("t1", t0 + 1.5))
		var seq: Array = d.get("seq", [])
		for take in seq:
			if t >= float(take["t0"]):
				var f := str(take["file"])
				tx2 = _people_tex.get(f, tx2)
				n = int(take["n"])
				fps = float(take["fps"])
				t0 = float(take["t0"])
				at = take["at"]
				to = take["to"]
				t1 = float(take["t1"])
		if t < t0:
			continue
		var pos := Vector2(float(at[0]), float(at[1])).lerp(Vector2(float(to[0]), float(to[1])), ramp01(t, t0, maxf(t0 + 0.01, t1)))
		var fr := int(floor((t - t0) * fps * rmk)) % maxi(1, n) if fps > 0.0 else 0
		draw_frame(_e4people, tx2, n, fr, pos.round(), bool(d.get("flip", false)))


## the fire engine noses into the lane from the right, its headlamp's light on the snow
func _draw_engine() -> void:
	if not e4.visible or _engine_tex == null or t < float(ENGINE[0]):
		return
	var u := ramp01(t, float(ENGINE[0]), float(ENGINE[1]))
	var x := lerpf(float(ENGINE[2]), float(ENGINE[3]), u)
	var fw := _engine_tex.get_width() / 2
	var fh := _engine_tex.get_height()
	var facing := _beacon_phase() > 0.5
	_engine.draw_texture_rect_region(_engine_tex, Rect2(Vector2(roundf(x), float(ENGINE[4]) - fh), Vector2(fw, fh)),
		Rect2((0 if facing else 1) * fw, 0, fw, fh))


## 0..1 brightness of the turning beacon as it faces the camera
func _beacon_phase() -> float:
	return 0.5 + 0.5 * sin((t - float(ENGINE[0])) * TAU * BEACON_HZ)


## the beacon: a blue glow at the lamp on the cab and a soft wash sweeping the snow and the facade as it turns
func _draw_beacon() -> void:
	if not e4.visible or t < float(ENGINE[0]) or _beacon_tex == null:
		return
	var u := ramp01(t, float(ENGINE[0]), float(ENGINE[1]))
	var x := lerpf(float(ENGINE[2]), float(ENGINE[3]), u)
	var lamp := Vector2(x + 76.0, float(ENGINE[4]) - 64.0)
	var ph := _beacon_phase()
	var k := (0.25 + 0.75 * ph) * (0.6 if reduced_motion() else 1.0) * clampf((t - float(ENGINE[0])) / 0.4, 0.0, 1.0)
	_beacon.draw_texture_rect(_beacon_tex, Rect2(lamp - Vector2(32, 32), Vector2(64, 64)), false, Color(1, 1, 1, k))
	if _wash_tex:
		# the beam swings across: a wash centred where it points (left over the facade .. down on the snow)
		var sw := sin((t - float(ENGINE[0])) * TAU * BEACON_HZ * 0.5)
		var c := lamp + Vector2(-150.0 + sw * 120.0, 10.0 + absf(sw) * 30.0)
		_beacon.draw_texture_rect(_wash_tex, Rect2(c - Vector2(150, 70), Vector2(300, 140)), false, Color(1, 1, 1, 0.8 * k))
		_beacon.draw_texture_rect(_wash_tex, Rect2(lamp - Vector2(110, 40), Vector2(220, 100)), false, Color(1, 1, 1, 0.5 * k))


# ------------------------------------------------------------------ draw
func _draw_e1() -> void:
	if not e1.visible:
		return
	var k := motion_k()
	var hatch: Array = layout.get("e1_hatch", [320, 110, 23])
	var hx := float(hatch[0])
	var hy := float(hatch[1])
	# coal dust drifting in the light shaft
	for i in 48:
		var ph := float(i) * 2.13
		var depth := fposmod(i * 0.137, 1.0)
		var spread := 20.0 + depth * 150.0
		var x := hx + sin(ph) * spread + sin(t * 0.7 + ph) * 4.0 * k
		var y := hy + 10.0 + depth * 200.0 - fposmod(t * (6.0 + i % 5) * k, 30.0)
		var a := 0.25 + 0.5 * (1.0 - depth)
		_e1fx.draw_rect(Rect2(Vector2(floorf(x), floorf(y)), Vector2.ONE), Color(0.75, 0.78, 0.84, a))
	# snowflakes falling in through the gap of the lid, coming down the chute toward the camera
	var s_ := float(hatch[2])
	for i in 26:
		var age := fposmod(t * 0.42 + i * 0.0385, 1.0)
		var ang := float(i) * 2.399
		var r := age * age * 260.0 * k
		var p := Vector2(hx + cos(ang) * (s_ * 0.6 + r * 0.9), hy - s_ + 6.0 + sin(ang) * s_ * 0.3 + r * 0.8)
		var sz := 1.0 if age < 0.6 else 2.0
		_e1fx.draw_rect(Rect2(p.floor(), Vector2(sz, sz)), Color(0.86, 0.9, 0.95, 0.85 * (1.0 - age * 0.5)))
	# smoke curling up the chute past the file, toward the light
	if _smoke:
		for j in 3:
			var age := fposmod(t * 0.5 + j * 0.33, 1.0)
			var x2 := hx + (j - 1) * 60.0 * (1.0 - age)
			var y2 := 330.0 - age * 200.0 * k
			draw_frame(_e1fx, _smoke, 8, int(age * 7.0), Vector2(x2, y2), false, Color(0.85, 0.82, 0.8, 0.7 * (1.0 - age)))


func _draw_e2() -> void:
	if not e2.visible or _smoke == null or t < LID[0]:
		return
	var k := motion_k()
	var h: Dictionary = layout.get("hatch", {})
	var back: Array = h.get("back", [250, 390, 218])
	var cx := (float(back[0]) + float(back[1])) * 0.5
	var cy := float(back[2]) + 14.0
	for i in 10:
		var born := LID[0] + i * 0.3
		var age := t - born
		if age < 0.0:
			continue
		age = fposmod(age, 2.6)
		# out of the mouth in front of the lid, then away from it with the draught (to the right, toward us)
		var x := cx - 30.0 + fposmod(i * 37.0, 70.0) + (age * 26.0 + age * age * 8.0) * k
		var y := cy + 12.0 - age * 40.0 * k
		draw_frame(_e2fx, _smoke, 8, clampi(int(age / 0.33), 0, 7), Vector2(x, y), false,
			Color(1.0, 0.94, 0.9, clampf(age / 0.25, 0.0, 1.0) * 0.95 * (1.0 - age / 2.6)))


func _draw_e3a() -> void:
	if not e3a.visible or _smoke == null:
		return
	var k := motion_k()
	for i in 12:
		var age := fposmod(t * 0.55 + i * 0.083, 1.0)
		var x := 160.0 + fposmod(i * 71.0, 330.0) + sin(t + i) * 10.0
		var y := 360.0 - age * 300.0 * k
		draw_frame(_e3afx, _smoke, 8, int(age * 7.0), Vector2(x, y), false, Color(1.0, 0.9, 0.85, 0.85 * (1.0 - age)))
	for j in 18:
		var age2 := fposmod(t * 0.7 + j * 0.0557, 1.0)
		var sp := Vector2(240.0 + fposmod(j * 53.0, 170.0) + sin(t * 3.0 + j) * 6.0, 330.0 - age2 * 280.0 * k)
		_e3afx.draw_rect(Rect2(sp.floor(), Vector2.ONE), Color(1.0, 0.72, 0.32, 0.9 * (1.0 - age2)))


func _draw_e3b() -> void:
	if not e3b.visible:
		return
	var k := motion_k()
	# the slam throws up a little snow; smoke seeps from under the lid
	if _breath and t >= SLAM and t < SLAM + 0.8:
		var hp := _lv("e3b_hatch") + Vector2(72, 60)
		draw_frame(_e3bfx, _breath, 6, clampi(int((t - SLAM) / 0.13), 0, 5), hp, false, Color(1, 1, 1, 0.9))
	if _smoke and t >= SLAM:
		for i in 3:
			var age := fposmod(t * 0.4 + i * 0.33, 1.0)
			var hp2 := _lv("e3b_hatch") + Vector2(30 + i * 40, 58)
			draw_frame(_e3bfx, _smoke, 8, int(age * 4.0), hp2 - Vector2(0, age * 30.0 * k), false, Color(0.9, 0.9, 0.9, 0.6 * (1.0 - age)))
	# their breath: quick puffs while they cough, slower toward the end
	if _breath:
		var pts: Array = layout.get("e3b_breath", [[286, 258], [366, 258]])
		for j in pts.size():
			var q: Array = pts[j]
			var period := 0.7 + j * 0.15
			var age := fposmod(t - E3B + j * 0.31, period) / period
			var p := Vector2(float(q[0]), float(q[1]) - age * 16.0 * k)
			draw_frame(_e3bfx, _breath, 6, int(age * 5.0), p, false, Color(1, 1, 1, 0.8 * (1.0 - age)))


## time window j bursts (BURST_ORDER), -1 if it never does
func _burst_time(j: int) -> float:
	var order: int = BURST_ORDER.find(j) if BURST_ORDER.has(j) else j
	return BURST0 + order * BURST_GAP


func _draw_e4() -> void:
	if not e4.visible:
		return
	var k := motion_k()
	var ws: Array = layout.get("e4_windows", [])
	for j in ws.size():
		var tb := _burst_time(j)
		if t < tb:
			continue
		var w: Array = ws[j]
		var wx := float(w[0])
		var wy := float(w[1])
		var age := t - tb
		# flames inside the window, then out over the lintel and up the facade
		if _flame_s and age >= 0.18:
			draw_frame(_e4fx, _flame_s, 8, flame_frame(t, 8, j * 0.41), Vector2(wx + 16.0, wy + 28.0))
		if _flame_out and age >= 0.35:
			var gk := clampf((age - 0.35) / 0.6, 0.3, 1.0)
			var fw := _flame_out.get_width() / 8
			var fh := _flame_out.get_height()
			var h := roundf(fh * gk)
			_e4fx.draw_texture_rect_region(_flame_out, Rect2(Vector2(roundf(wx + 16.0 - fw * 0.5), roundf(wy + 8.0 - h)), Vector2(fw, h)),
				Rect2(flame_frame(t, 8, j * 0.53 + 0.3) * fw, 0, fw, fh))
		# the glass: shards fly out glinting and land in the snow, where they keep catching the firelight
		for g in 16:
			var gx0 := wx + 2.0 + g * 1.9
			var vx := (float(g) - 7.5) * 11.0 + sin(g * 2.1) * 6.0
			var vy := -46.0 - fposmod(g * 37.0, 50.0)
			var land := 266.0 + fposmod(g * 17.0 + j * 5.0, 30.0)
			var ag := age - g * 0.015
			if ag < 0.0:
				continue
			var p := Vector2(gx0 + vx * ag * k, wy + 20.0 + (vy * ag + 260.0 * ag * ag) * k)
			var landed := p.y >= land
			if landed:
				p.y = land
				var tl := ag
				p.x = gx0 + vx * tl * k * 0.9
			var tw := 0.5 + 0.5 * sin(t * 7.0 + g * 1.7 + j)
			var col := Color(0.95, 0.97, 1.0, 1.0) if tw > 0.5 else Color(1.0, 0.72, 0.42, 0.9)
			if landed:
				col.a *= 0.45 + 0.55 * tw
			var sz := 2.0 if (g % 2 == 0 and (not landed or tw > 0.8)) else 1.0
			_e4fx.draw_rect(Rect2(p.floor(), Vector2(sz, sz)), col)
			if landed and tw > 0.85:
				# a glint: a tiny cross of light on the snow
				_e4fx.draw_rect(Rect2(p.floor() + Vector2(-1, 0), Vector2(3, 1)), Color(1, 1, 1, 0.55))
				_e4fx.draw_rect(Rect2(p.floor() + Vector2(0, -1), Vector2(1, 3)), Color(1, 1, 1, 0.55))


## warm blooms around the burning windows (additive)
func _draw_e4_heat() -> void:
	if not e4.visible or _halo == null:
		return
	var ws: Array = layout.get("e4_windows", [])
	for j in ws.size():
		var tb := _burst_time(j)
		if t < tb:
			continue
		var w: Array = ws[j]
		var gk := clampf((t - tb) / 0.5, 0.0, 1.0)
		var flash := clampf(1.0 - (t - tb) / 0.25, 0.0, 1.0) * (0.0 if reduced_motion() else 1.0)
		var a := (0.55 * gk + 0.4 * flash) * fire_wobble(t, 80 + j, 0.15)
		_e4heat.draw_texture_rect(_halo, Rect2(Vector2(float(w[0]) - 30.0, float(w[1]) - 58.0), Vector2(96, 110)), false,
			Color(1, 1, 1, clampf(a, 0.0, 1.0)))


## smoke: a column from every burning window rolls up the facade, drifting with the wind, and gathers into one
## mass under the cornice and over the roof; the snow falls in front of it
func _draw_e4_smoke() -> void:
	if not e4.visible or _smoke == null:
		return
	var k := motion_k()
	var ws: Array = layout.get("e4_windows", [])
	var n_burning := 0
	for j in ws.size():
		var tb := _burst_time(j)
		if t < tb:
			continue
		n_burning += 1
		var w: Array = ws[j]
		for i in 7:
			var life := 2.6
			var age := fposmod(t - tb - i * 0.37, life)
			if t - tb < i * 0.37:
				continue
			var u := age / life
			var x := float(w[0]) + 16.0 + age * 14.0 * k + sin(i * 1.3 + j) * 6.0
			var y := float(w[1]) - 34.0 - (age * 64.0 - age * age * 6.0) * k
			var sc := 0.4 + u * 1.1
			var a := clampf(age / 0.45, 0.0, 1.0) * (0.9 - 0.4 * u)
			_draw_scaled(_e4smoke, _smoke, 8, clampi(int(u * 8.0), 0, 7), Vector2(x, y), sc, Color(1, 1, 1, a))
	# the mass under the cornice and over the roof, thickening as more windows burn
	for i in 10:
		var born := BURST0 + 0.3 + i * 0.3
		var age2 := t - born
		if age2 < 0.0 or n_burning < 1:
			continue
		var x2 := 30.0 + fposmod(i * 67.0 + age2 * 12.0 * k, 640.0)
		var y2 := 92.0 - minf(age2, 2.0) * 10.0 * k + sin(i * 2.3) * 8.0
		var a2 := clampf(age2 / 0.8, 0.0, 1.0) * clampf(float(n_burning) / 5.0, 0.25, 1.0) * 0.62
		_draw_scaled(_e4smoke, _smoke, 8, 6 + (i % 2), Vector2(x2, y2), 1.7 + 0.2 * float(i % 3), Color(1, 1, 1, a2))


## Frame `i` of an n-frame sheet scaled by `sc` around `center` (soft smoke grows as it rises).
static func _draw_scaled(ci: CanvasItem, sheet: Texture2D, n: int, i: int, center: Vector2, sc: float,
		mod := Color(1, 1, 1, 1)) -> void:
	if sheet == null:
		return
	var fw := sheet.get_width() / maxi(1, n)
	var fh := sheet.get_height()
	var sz := (Vector2(fw, fh) * sc).round()
	ci.draw_texture_rect_region(sheet, Rect2((center - sz * 0.5).round(), sz), Rect2(posmod(i, n) * fw, 0, fw, fh), mod)
