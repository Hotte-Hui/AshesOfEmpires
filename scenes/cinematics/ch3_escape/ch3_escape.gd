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
## the lane's lamp; in the lane glass glints into the snow, onlookers watch the wing and two firemen run in as the
## bells come close (a slow blue beacon from the right).
## Round 11: the iron lid is opaque cast iron (tread plate under melting snow; open, its ribbed sooted underside
## with the cast date); the glass flies out in glinting shards that stay twinkling in the snow, the onlookers
## flinch, step back, point and wave, and the fire engine noses into the lane from the right, its blue beacon
## turning on the cab and washing the snow and the facade.
## Round 13: the fire is pixel art -- every flame, puff of smoke, spark and pool of fire light comes from the pixel
## fire kit (tools/pixelgen/pixel_fire.py -> assets/fx/pixel_fire/, played by scripts/render/pixel_fire.gd: whole
## pixels, never scaled, no alpha fades).  e1: puffs shrink away up the chute.  e2: flames behind the yard
## window's bars, its light on the wall and the snow, puffs and sparks out of the hatch.  e3: the glow deep in the
## chute breathes in four frames, puffs and sparks rise past the hands; breath and the smoke from under the lid
## are small puffs.  e4: a window bursts (one hot frame), flames fill it behind the bars, step up over the lintel
## and lick up the facade with the draught; its light lies on the wall around it and on the snow in front as
## dithered pools; a column of puffs climbs the facade and spreads under the cornice into big, slow, grey
## billows that break up in the wind; sparks on arcs.
## Art: tools/pixelgen/env_c3p2_cine_fire.py (+ _yard, _life; build_fx for the kit-made sheets) ->
## assets/cinematics/c3p2/escape/.

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
## e4: a souterrain window's opening (layout e4_windows = its top-left), the lane's snow line, the iron bars
const WIN := Vector2(32, 28)
const SNOW_Y := 262.0
const BAR := Color("#140D0A")
const IRON := Color("#05070B")
## e3b: the souterrain window at the right of the snow shot (env_c3p2_cine_yard.e3b_bg)
const E3B_WINDOW := [486, 140, 556, 182]
const KIT := ["flame_s", "flame_m", "lick", "window", "low_a", "puff_s", "puff_m", "puff_l", "puff_xl",
	"puff_s_grey", "puff_m_grey", "puff_l_grey", "puff_xl_grey", "glow_m", "glow_l", "pool_m", "pool_l"]

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
var _e2heat: Node2D
var _e2win: Node2D
var _snow2: Node2D
var _hands: Sprite2D
var _e3afx: Node2D
var _e3glow: Sprite2D
var _hatch_b: Sprite2D
var _men: Sprite2D
var _e3bfx: Node2D
var _snow3: Node2D
var _e4fx: Node2D
var _snow4: Node2D
var _e4people: Node2D
var _people: Array = []
var _beacon: Node2D
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
	need_kit(KIT)
	own_sheet("c3p2_breath", "escape/breath.png", 6)
	e1 = group("Chute")
	sprite("escape/e1_bg.png", Vector2.ZERO, e1)
	_light1 = sprite("escape/e1_light.png", Vector2.ZERO, e1, 1, true)
	_e1fx = _fx(e1, "Dust", _draw_e1)
	_file = sprite("escape/e1_file.png", Vector2.ZERO, e1, 2)
	e2 = group("Yard")
	sprite("escape/e2_bg.png", Vector2.ZERO, e2)
	sprite("escape/e2_lamp.png", Vector2.ZERO, e2, 1, true)
	_e2heat = _fx(e2, "WindowLight", _draw_e2_heat)
	_e2heat.material = additive()
	_e2win = _fx(e2, "WindowFire", _draw_e2_window)
	_hatch = sprite("escape/e2_hatch.png", _lv("hatch_at"), e2, 3)
	_e2fx = _fx(e2, "Smoke", _draw_e2)
	_konrad = sprite("escape/e2_konrad.png", _lv("e2_konrad"), e2, KONRAD.size())
	_snow2 = snow(e2, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(6, 16), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 30, "v": Vector2(9, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9201)
	e3a = group("Hands")
	sprite("escape/e3a_bg.png", Vector2.ZERO, e3a)
	_e3glow = sprite("escape/e3a_glow.png", _lv("e3a_glow_at"), e3a, 4, true)
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
	_engine_tex = tex("escape/engine.png")
	_beacon_tex = tex("escape/beacon.png")
	_wash_tex = tex("escape/beacon_wash.png")
	_e4heat = _fx(e4, "FireLight", _draw_e4_heat)
	_e4heat.material = additive()
	_e4fx = _fx(e4, "Flames", _draw_e4)
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
	_e4smoke = _fx(e4, "Smoke", _draw_e4_smoke)
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
	_e2fx.queue_redraw()
	_e2heat.queue_redraw()
	_e2win.queue_redraw()
	# e3a: the hand rises out of the smoke, is taken, both pulled up; the glow below breathes in its frames
	var hf := 0
	for i in HANDS.size():
		if time >= HANDS[i]:
			hf = i
	_hands.frame = hf
	var rise := (1.0 - ramp01(time, HANDS[0], HANDS[1])) * 46.0
	_hands.position = _lv("e3_hands") + Vector2(0, roundf(rise))
	_e3glow.frame = posmod(int(floor(time * PF.LIGHT_HZ * fire_rate())), 4)
	_e3afx.queue_redraw()
	# e3b: the slam, the men breathing hard (coughing: quick heaves)
	_hatch_b.frame = 0 if time < SLAM else 1
	var rate := 1.6 if rm else 3.0
	_men.frame = int(floor((time - E3B) * rate)) % 2 if time >= E3B else 0
	_snow3.set_time(time * (0.6 if rm else 1.0))
	_e3bfx.queue_redraw()
	# e4: the windows burst one after another
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
## Fire filling a barred opening [x0, y0, x1, y1]: the kit's tiles standing on its sill, cut at its lintel, the
## iron bars (2 px every `pitch`, on the world's grid) in front.
func _window_fire(ci: CanvasItem, r: Array, tile: String, pitch: int, shift := 0, bar := IRON) -> void:
	var x0 := int(r[0])
	var y0 := int(r[1])
	var x1 := int(r[2])
	var y1 := int(r[3])
	PF.wall(ci, [tile], x0, x1, y1, t, {"rate": fire_rate(), "clip_top": y0, "shift": shift})
	var bx := x0 + posmod(-x0, pitch)
	while bx < x1:
		ci.draw_rect(Rect2(bx, y0, mini(2, x1 - bx), y1 - y0), bar)
		bx += pitch


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
	# smoke curling up the chute past the file, toward the light: every puff shrinks away into the distance
	# (three sheets, each run backwards from a full puff to its first tight ball)
	for j in 3:
		var age := fposmod(t * 0.5 + j * 0.33, 1.0)
		var c := Vector2(hx + (j - 1) * 60.0 * (1.0 - age), 312.0 - age * 180.0 * k)
		if age < 0.4:
			PF.puff(_e1fx, "puff_l", c, 0.44 * (1.0 - age / 0.4), j)
		elif age < 0.75:
			PF.puff(_e1fx, "puff_m", c, 0.44 * (1.0 - (age - 0.4) / 0.35), j)
		else:
			PF.puff(_e1fx, "puff_s", c, 0.44 * (1.0 - (age - 0.75) / 0.25), j)


## e2: the yard window's fire lights the wall around it and the snow below (additive pools that breathe)
func _draw_e2_heat() -> void:
	if not e2.visible:
		return
	var w: Array = layout.get("e2_window", [92, 148, 166, 196])
	var cx := (float(w[0]) + float(w[2])) * 0.5
	PF.light(_e2heat, "glow_l", Vector2(cx, float(w[1]) + 18.0), t, 1, fire_rate())
	PF.light(_e2heat, "pool_l", Vector2(cx, float(w[3]) + 30.0), t, 2, fire_rate())


func _draw_e2_window() -> void:
	if e2.visible:
		_window_fire(_e2win, layout.get("e2_window", [92, 148, 166, 196]), "low_a", 12, 20)


func _draw_e2() -> void:
	if not e2.visible or t < LID[0]:
		return
	var k := motion_k()
	var h: Dictionary = layout.get("hatch", {})
	var back: Array = h.get("back", [250, 390, 218])
	var cx := (float(back[0]) + float(back[1])) * 0.5
	var cy := float(back[2]) + 14.0
	# out of the mouth in front of the lid, then away from it with the draught (to the right, toward us)
	PF.plume(_e2fx, {"sheets": ["puff_m", "puff_l", "puff_l"], "from": Vector2(cx + 4.0, cy - 2.0), "spread": Vector2(34, 3),
		"count": 13, "life": 3.0, "rise": 42.0, "slow": 0.3, "drift": Vector2(22, 0), "bend": 12.0, "t0": LID[0],
		"seed": 43, "rate": k}, t)
	PF.sparks(_e2fx, {"rect": Rect2(cx - 34.0, cy - 2.0, 68, 8), "count": 8, "life": 1.1, "rise": 62.0, "kick": 12.0,
		"wind": 10.0, "t0": LID[1], "seed": 45, "rate": k}, t)


func _draw_e3a() -> void:
	if not e3a.visible:
		return
	var k := motion_k()
	# smoke and sparks rise out of the chute toward the camera, past the hands
	PF.plume(_e3afx, {"sheets": ["puff_l", "puff_xl", "puff_xl"], "from": Vector2(325, 376), "spread": Vector2(150, 6),
		"count": 13, "life": 1.8, "rise": 168.0, "slow": 0.2, "sway": 6.0, "t0": 6.0, "seed": 51, "rate": k}, t)
	PF.sparks(_e3afx, {"rect": Rect2(240, 322, 170, 12), "count": 16, "life": 1.3, "rise": 200.0, "kick": 14.0,
		"t0": 6.5, "seed": 53, "rate": k}, t)


func _draw_e3b() -> void:
	if not e3b.visible:
		return
	var k := motion_k()
	# the souterrain window at the right: flames behind its bars
	_window_fire(_e3bfx, E3B_WINDOW, "window", 11, 7)
	# the slam throws up a little snow; smoke seeps from under the lid
	var hp := _lv("e3b_hatch")
	if t >= SLAM and t < SLAM + 0.8:
		PF.puff(_e3bfx, "c3p2_breath", hp + Vector2(72, 51), (t - SLAM) / 0.8, 5)
	PF.plume(_e3bfx, {"sheets": ["puff_s_grey", "puff_m_grey", "puff_s_grey"], "from": hp + Vector2(70, 52),
		"spread": Vector2(42, 2), "count": 3, "life": 2.4, "rise": 13.0, "slow": 0.0, "drift": Vector2(3, 0), "t0": SLAM,
		"seed": 55, "rate": k}, t)
	# their breath: quick puffs while they cough, slower toward the end
	var pts: Array = layout.get("e3b_breath", [[286, 258], [366, 258]])
	for j in pts.size():
		var q: Array = pts[j]
		var period := 0.7 + j * 0.15
		var age := fposmod(t - E3B + j * 0.31, period) / period
		PF.puff(_e3bfx, "c3p2_breath", Vector2(float(q[0]), float(q[1]) - 9.0 - age * 16.0 * k), age, j)


## time window j bursts (BURST_ORDER), -1 if it never does
func _burst_time(j: int) -> float:
	var order: int = BURST_ORDER.find(j) if BURST_ORDER.has(j) else j
	return BURST0 + order * BURST_GAP


func _draw_e4() -> void:
	if not e4.visible:
		return
	var k := motion_k()
	var rate := fire_rate()
	var ws: Array = layout.get("e4_windows", [])
	for j in ws.size():
		var tb := _burst_time(j)
		if t < tb:
			continue
		var w: Array = ws[j]
		var wx := float(w[0])
		var wy := float(w[1])
		var age := t - tb
		# the opening: one hot frame as it bursts, then the burning room with flames behind the bars
		if age < 0.12 and not reduced_motion():
			_e4fx.draw_rect(Rect2(wx, wy, WIN.x, WIN.y), Color("#F2A044"))
			_e4fx.draw_rect(Rect2(wx + 5.0, wy + 9.0, WIN.x - 10.0, WIN.y - 13.0), Color("#FCE0A0"))
		else:
			_e4fx.draw_rect(Rect2(wx, wy, WIN.x, WIN.y), PF.SPARK[5])
			PF.wall(_e4fx, ["window"], wx, wx + WIN.x, wy + WIN.y, t, {"rate": rate, "clip_top": wy, "shift": j * 13,
				"phase": j * 3})
		for bx in [0, 8, 16, 24]:
			_e4fx.draw_rect(Rect2(wx + bx, wy, 2, WIN.y), BAR)
		_e4fx.draw_rect(Rect2(wx, wy, WIN.x, 1), BAR)
		# the light well's railing stands in front of the opening's foot
		_e4fx.draw_rect(Rect2(wx, 248, WIN.x, 2), IRON)
		var rx := int(wx) + posmod(-int(wx), 5)
		while rx < int(wx + WIN.x):
			_e4fx.draw_rect(Rect2(rx, 250, 1, 2), IRON)
			rx += 5
		# flames out over the lintel: small, larger, then licking up the facade with the draught
		if age >= 0.9:
			PF.flame(_e4fx, "lick", Vector2(wx + 20.0, wy + 3.0), t, j, rate, false)
		elif age >= 0.55:
			PF.flame(_e4fx, "flame_m", Vector2(wx + 16.0, wy + 3.0), t, j, rate)
		elif age >= 0.3:
			PF.flame(_e4fx, "flame_s", Vector2(wx + 16.0, wy + 3.0), t, j, rate)
		PF.sparks(_e4fx, {"rect": Rect2(wx + 4.0, wy - 34.0, 28, 30), "count": 5, "life": 1.1, "rise": 58.0, "kick": 10.0,
			"wind": 9.0, "t0": tb + 0.6, "seed": 90 + j * 3, "rate": k}, t)
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
				p.x = gx0 + vx * ag * k * 0.9
			var tw := 0.5 + 0.5 * sin(t * 7.0 + g * 1.7 + j)
			if landed and tw < 0.3:
				continue                      # a shard in the snow shows only while it catches the light
			var col := Color("#F2F3F5") if tw > 0.5 else Color("#EDB777")
			var sz := 2.0 if (g % 2 == 0 and (not landed or tw > 0.8)) else 1.0
			_e4fx.draw_rect(Rect2(p.floor(), Vector2(sz, sz)), col)
			if landed and tw > 0.85:
				# a glint: a tiny cross of light on the snow
				_e4fx.draw_rect(Rect2(p.floor() + Vector2(-1, 0), Vector2(3, 1)), Color("#DEE2E7"))
				_e4fx.draw_rect(Rect2(p.floor() + Vector2(0, -1), Vector2(1, 3)), Color("#DEE2E7"))


## the burning windows' light: on the wall around and above each (a larger pool for the burst's flash and once
## the flames lick up the facade) and on the snow in front of its light well -- additive pools that breathe
func _draw_e4_heat() -> void:
	if not e4.visible:
		return
	var rate := fire_rate()
	var ws: Array = layout.get("e4_windows", [])
	for j in ws.size():
		var tb := _burst_time(j)
		if t < tb:
			continue
		var w: Array = ws[j]
		var age := t - tb
		var big := age >= 0.9 or (age < 0.25 and not reduced_motion())
		var cx := float(w[0]) + WIN.x * 0.5
		PF.light(_e4heat, "glow_l" if big else "glow_m", Vector2(cx + 4.0, float(w[1]) - 20.0), t, j, rate)
		PF.light(_e4heat, "pool_l" if age >= 0.9 else "pool_m", Vector2(cx, SNOW_Y + 14.0), t, j + 20, rate)


## smoke: a column of puffs from every burning window climbs the facade, drifting with the wind; where the
## columns reach the cornice the smoke spreads into big slow billows (grey: away from the fire's light) that
## break up in the wind; the snow falls in front of it
func _draw_e4_smoke() -> void:
	if not e4.visible:
		return
	var k := motion_k()
	var ws: Array = layout.get("e4_windows", [])
	for pass_ in 2:
		for j in ws.size():
			var tb := _burst_time(j)
			if t < tb:
				continue
			var w: Array = ws[j]
			var from := Vector2(float(w[0]) + 24.0, float(w[1]) - 46.0)
			if pass_ == 0:
				PF.plume(_e4smoke, {"sheets": ["puff_xl_grey", "puff_l_grey", "puff_xl_grey"], "from": Vector2(from.x + 30.0, 106.0),
					"spread": Vector2(40, 12), "count": 3, "life": 3.4, "rise": 7.0, "slow": 0.0, "drift": Vector2(13, 0),
					"t0": tb + 1.9, "seed": 120 + j * 5, "rate": k}, t)
			else:
				PF.plume(_e4smoke, {"sheets": ["puff_m", "puff_l", "puff_l"], "from": from, "spread": Vector2(8, 6),
					"count": 8, "life": 2.6, "rise": 60.0, "slow": 0.5, "drift": Vector2(11, 0), "bend": 4.0,
					"t0": tb + 0.5, "seed": 80 + j * 3, "rate": k}, t)
