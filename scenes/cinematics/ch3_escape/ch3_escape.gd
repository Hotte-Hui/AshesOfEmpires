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
## Art: tools/pixelgen/env_c3p2_cine_fire.py -> assets/cinematics/c3p2/escape/ (+ layout.json "escape").

const DUR := 16.0
const SHOTS := [["e1", 0.0, 4.0], ["e2", 4.0, 8.0], ["e3", 8.0, 12.0], ["e4", 12.0, 16.0]]
const E3B := 10.2                     # e3: the hands -> lying in the snow
const PUSHES := [0.35, 1.55, 2.75]    # e1: the file is shoved up the slide
const LID := [4.35, 4.65]             # e2: the lid lifts, flips open
const KONRAD := [4.95, 5.7, 6.5, 7.25]
const HANDS := [8.0, 8.5, 9.15, 9.6]
const SLAM := 10.45
const BURST0 := 12.35                 # e4: first window bursts; the others follow every BURST_GAP
const BURST_GAP := 0.42
const BURST_ORDER := [3, 2, 4, 1, 5, 0, 6]

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
	e1 = group("Chute")
	sprite("escape/e1_bg.png", Vector2.ZERO, e1)
	_light1 = sprite("escape/e1_light.png", Vector2.ZERO, e1, 1, true)
	_e1fx = _fx(e1, "Dust", _draw_e1)
	_file = sprite("escape/e1_file.png", Vector2.ZERO, e1, 2)
	e2 = group("Yard")
	sprite("escape/e2_bg.png", Vector2.ZERO, e2)
	sprite("escape/e2_lamp.png", Vector2.ZERO, e2, 1, true)
	_hatch = sprite("escape/e2_hatch.png", _lv("hatch_at"), e2, 3)
	_e2fx = _fx(e2, "Smoke", _draw_e2)
	_konrad = sprite("escape/e2_konrad.png", _lv("e2_konrad"), e2, 4)
	_snow2 = snow(e2, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(6, 16), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 30, "v": Vector2(9, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9201)
	e3a = group("Hands")
	sprite("escape/e3a_bg.png", Vector2.ZERO, e3a)
	_e3glow = sprite("escape/e3a_glow.png", Vector2.ZERO, e3a, 1, true)
	_e3afx = _fx(e3a, "Smoke", _draw_e3a)
	_hands = sprite("escape/e3a_hands.png", _lv("e3_hands"), e3a, 4)
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
	_e4fx = _fx(e4, "Smoke", _draw_e4)
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
		var x := cx - 40.0 + fposmod(i * 37.0, 90.0) + age * 18.0 * k
		var y := cy - age * 44.0 * k
		draw_frame(_e2fx, _smoke, 8, clampi(int(age / 0.33), 0, 7), Vector2(x, y), false, Color(1.0, 0.94, 0.9, 0.9 * (1.0 - age / 2.6)))


func _draw_e3a() -> void:
	if not e3a.visible or _smoke == null:
		return
	var k := motion_k()
	for i in 12:
		var age := fposmod(t * 0.55 + i * 0.083, 1.0)
		var x := 160.0 + fposmod(i * 71.0, 330.0) + sin(t + i) * 10.0
		var y := 360.0 - age * 300.0 * k
		draw_frame(_e3afx, _smoke, 8, int(age * 7.0), Vector2(x, y), false, Color(1.0, 0.9, 0.85, 0.85 * (1.0 - age)))


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
		var pts: Array = layout.get("e3b_breath", [[306, 258], [346, 258]])
		for j in pts.size():
			var q: Array = pts[j]
			var period := 0.7 + j * 0.15
			var age := fposmod(t - E3B + j * 0.31, period) / period
			var p := Vector2(float(q[0]), float(q[1]) - age * 16.0 * k)
			draw_frame(_e3bfx, _breath, 6, int(age * 5.0), p, false, Color(1, 1, 1, 0.8 * (1.0 - age)))


func _draw_e4() -> void:
	if not e4.visible or _smoke == null:
		return
	var k := motion_k()
	var ws: Array = layout.get("e4_windows", [])
	for j in ws.size():
		var order: int = BURST_ORDER.find(j) if BURST_ORDER.has(j) else j
		var tb := BURST0 + order * BURST_GAP
		if t < tb:
			continue
		var w: Array = ws[j]
		for i in 3:
			var age := fposmod(t - tb + i * 0.6, 1.8)
			if t - tb < i * 0.6:
				continue
			var x := float(w[0]) + 16.0 + age * 8.0
			var y := float(w[1]) + 4.0 - age * 70.0 * k
			draw_frame(_e4fx, _smoke, 8, clampi(int(age / 0.25), 0, 7), Vector2(x, y), false, Color(1.0, 0.9, 0.85, 0.85 * (1.0 - age / 1.8)))
