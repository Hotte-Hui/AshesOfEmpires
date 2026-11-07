extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_Prologue (60 s) — the prologue of a new game (round 11): how this winter came to be, in five painted shots,
## subtitles only, before Chapter 1 in Karsk.  Played by Game._cin_prologue() after the opening note of a NEW game
## (never on load, never by the Story engine) and offered again on the „Filmsequenzen“ page.  Runs on the §12.5
## runtime (ch3_common/c3_cinematic.gd) with the C4 helpers; art tools/pixelgen/env_prologue.py
## (assets/cinematics/prologue, anchors in layout.json), score tools/audiogen/prologue_audio.py (mus_prologue).
##   p1  0-13      dusk on the snowfield: the armistice Line, a watchtower against the last light (the camera drifts
##                 right; snow, the searchlight sweeps the strip, the tower window breathes)
##   p2  13-32.6   a paper map under a lamp: the Line is drawn from the Baltic down (13.4-16.6), Veltrava is ringed
##                 (18.8), the three corridors are drawn across it (23.8-27.6), small trains run on them (28.8-)
##   p3  32.6-41   a freight office desk, the Frachtbrief of Korridor II: the stamp comes down at 37.0 — C-17
##   p4  41-49     Berlin, a drafting hall at dawn: Konrad at the tall window, the Great Hall's dome in the haze
##   p5  49-60     Karsk, the yard at night: Alexei walks in under the floodlight; the signal turns green (54.6)
## Shot changes dip through black; the film begins and ends on black (the cut to Chapter 1).  No insignia in any
## shot and no choice or flag changes a frame (the same film in every playthrough).

const ASSETS_P := "res://assets/cinematics/prologue/"
const DUR := 60.0
const SHOTS := [["p1", 0.0, 13.0], ["p2", 13.0, 32.6], ["p3", 32.6, 41.0], ["p4", 41.0, 49.0], ["p5", 49.0, 60.0]]
## [subtitle key, start]; durations follow line_dur() (readable at READ_CPS)
const LINES := [
	["prologue.p1.europe", 1.0], ["prologue.p1.war", 3.0], ["prologue.p1.line", 6.2], ["prologue.p1.armistice", 10.2],
	["prologue.p2.empires", 13.8], ["prologue.p2.veltrava", 18.8], ["prologue.p2.accord", 23.8],
	["prologue.p2.trains", 28.8],
	["prologue.p3.papers", 33.2], ["prologue.p3.c17", 37.3],
	["prologue.p4.konrad", 41.6], ["prologue.p4.neutral", 45.7],
	["prologue.p5.alexei", 49.8], ["prologue.p5.politics", 53.4], ["prologue.p5.strangers", 56.4]]
## sounds of the film (all under assets/audio/sfx; tests check they exist): [time, id, dB]
const BEDS := [[0.4, "karsk_wind_gust_1", -13.0], [7.5, "karsk_wind_gust_2", -15.0], [13.2, "paper_rustle_1", -11.0],
	[23.8, "paper_rustle_2", -15.0], [28.8, "karsk_train_far", -15.0], [32.8, "paper_rustle_3", -12.0],
	[37.0, "stamp_thud", -6.0], [43.0, "berlin_tram_bell", -20.0], [55.0, "train_horn_far", -16.0]]
const DIP := 0.45                      ## black dip, each way, at every shot change
const FADE_IN := 0.9
const FADE_OUT := [59.0, 60.0]
const LINE_DRAW := [13.4, 16.6]        ## the Line is drawn on the map
const VELTRAVA_AT := 18.8              ## ringed on the map, its label appears
const CORRIDORS := [[23.8, 26.4], [24.4, 27.0], [25.0, 27.6]]
const TRAINS_FROM := 28.8
const TRAIN_SPEED := 24.0              ## px/s on the map
const STAMP := [36.4, 37.0, 37.3, 38.0]  ## comes in, lands (the imprint), lifts, gone
const STAMP_OFF := Vector2(-4, -6)       ## stamp sprite top-left over the imprint's (the block covers it)
const SIGNAL_GREEN := 54.6
const WALK_FROM := 49.4
const ALEXEI_SPEED := 34.5             ## the sheet's walk_side ground speed: px/s
const ALEXEI_STEP := 3.45              ## px per walk frame (10 fps)

var _pl: Dictionary = {}
var p1: Node2D
var p2: Node2D
var p3: Node2D
var p4: Node2D
var p5: Node2D
var _pan1: Node2D
var _pan3: Node2D
var _pan4: Node2D
var _pan5: Node2D
var _win1: Sprite2D
var _beam1: Node2D
var _snow1: Node2D
var _map: Node2D
var _label2: Sprite2D
var _imprint: Sprite2D
var _shadow3: Sprite2D
var _stamp3: Sprite2D
var _dust3: Node2D
var _konrad: Sprite2D
var _lamp4: Sprite2D
var _snow4: Node2D
var _smoke4: Node2D
var _cone5: Sprite2D
var _head5: Sprite2D
var _signal5: Sprite2D
var _steam5: Node2D
var _alexei: Sprite2D
var _alexei_idle: Sprite2D
var _snow5: Node2D
var _lit5: Node2D
var _dip: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 4.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return LINES.map(func(l: Array) -> String: return str(l[0]))


func _make_cues() -> Array:
	var c: Array = []
	c.append({"t": 0.0, "amb": "", "fade": 2.5})
	c.append_array(optional_music(0.0, "mus_prologue", 2.5))
	for b in BEDS:
		c.append({"t": float(b[0]), "bed": str(b[1]), "db": float(b[2])})
	c.append({"t": 49.2, "amb": "amb_karsk_yard", "fade": 3.0})
	for l in LINES:
		c.append(say_at(str(l[0]), float(l[1])))
	return c


## Texture under assets/cinematics/prologue/ (a res:// path is taken as it is); same bookkeeping as the base.
func tex(rel: String) -> Texture2D:
	var path := rel if rel.begins_with("res://") else ASSETS_P + rel
	if ResourceLoader.exists(path):
		var r = load(path)
		if r is Texture2D:
			return r
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	if not missing.has(path):
		missing.append(path)
	return null


## A section of assets/cinematics/prologue/layout.json (written by env_prologue.py).
func pl(section: String) -> Dictionary:
	if _pl.is_empty():
		var p := ASSETS_P + "layout.json"
		if FileAccess.file_exists(p):
			var d = JSON.parse_string(FileAccess.get_file_as_string(p))
			if d is Dictionary:
				_pl = d
	var s = _pl.get(section, {})
	return s if s is Dictionary else {}


func _pts(v) -> PackedVector2Array:
	var out := PackedVector2Array()
	if v is Array:
		for p in v:
			out.append(Vector2(float(p[0]), float(p[1])))
	return out


func _build() -> void:
	var L1 := pl("line")
	var L2 := pl("map")
	var L3 := pl("papers")
	var L4 := pl("berlin")
	var L5 := pl("karsk")
	# p1 the Line
	p1 = group("Line")
	_pan1 = group("Pan", p1)
	sprite("p1_line.png", Vector2.ZERO, _pan1)
	var w1: Array = L1.get("window", [405, 187, 423, 191])
	_win1 = sprite("p1_windowglow.png", Vector2((float(w1[0]) + float(w1[2])) * 0.5 - 24.0,
		(float(w1[1]) + float(w1[3])) * 0.5 - 12.0), _pan1, 1, true)
	_beam1 = fx(_pan1, "Beam", _draw_beam)
	_beam1.material = additive()
	_snow1 = snow(p1, Rect2(0, 0, 640, 360), [
		{"count": 70, "v": Vector2(-6, 16), "vjit": 0.4, "size": Vector2(1, 1), "color": Color("#c9cfdc"), "sway": 3.0},
		{"count": 18, "v": Vector2(-10, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#e6e9ef"), "sway": 4.0}],
		1101)
	# p2 the map
	p2 = group("Map")
	sprite("p2_map.png", Vector2.ZERO, p2)
	_map = fx(p2, "Drawing", _draw_map)
	_label2 = sprite("p2_veltrava.png", lv(L2, "label_at", Vector2(330, 202)), p2)
	# p3 the papers
	p3 = group("Papers")
	_pan3 = group("Pan", p3)
	sprite("p3_papers.png", Vector2.ZERO, _pan3)
	_imprint = sprite("p3_imprint.png", lv(L3, "imprint_at", Vector2(348, 166)), _pan3)
	_shadow3 = sprite("p3_shadow.png", Vector2.ZERO, _pan3)
	_stamp3 = sprite("p3_stamp.png", Vector2.ZERO, _pan3)
	_dust3 = fx(_pan3, "Dust", _draw_dust3)
	_dust3.material = additive()
	# p4 Berlin
	p4 = group("Berlin")
	_pan4 = group("Pan", p4)
	sprite("p4_berlin.png", Vector2.ZERO, _pan4)
	var gw := _window4()
	_snow4 = snow(_pan4, gw, [
		{"count": 40, "v": Vector2(5, 12), "vjit": 0.4, "size": Vector2(1, 1), "color": Color("#eef0f4"), "sway": 2.0}],
		1401, gw)
	_smoke4 = fx(_pan4, "Smoke", _draw_smoke4)
	_lamp4 = sprite("p4_lampglow.png", lv(L4, "lampglow_at", Vector2(550, 174)), _pan4, 1, true)
	_konrad = sprite("p4_konrad.png", Vector2.ZERO, _pan4, maxi(1, int(L4.get("konrad_frames", 1))))
	# p5 Karsk
	p5 = group("Karsk")
	_pan5 = group("Pan", p5)
	sprite("p5_karsk.png", Vector2.ZERO, _pan5)
	_cone5 = sprite("p5_cone.png", lv(L5, "cone_at", Vector2(69, 70)), _pan5, 1, true)
	_cone5.modulate = Color(1, 1, 1, 0.8)
	_head5 = sprite("p5_headlamp.png", lv(L5, "headlamp", Vector2(330, 194)) - Vector2(20, 15), _pan5, 1, true)
	_signal5 = sprite("p5_signal.png", lv(L5, "signal", Vector2(448, 154)) - Vector2(12, 12), _pan5, 2, true)
	_steam5 = fx(_pan5, "Steam", _draw_steam5)
	_lit5 = fx(_pan5, "LitSnow", _draw_lit5)
	_lit5.material = additive()
	_alexei = sprite("p5_alexei_walk.png", Vector2.ZERO, _pan5, maxi(1, int(L5.get("walk_frames", 1))))
	_alexei_idle = sprite("p5_alexei_idle.png", Vector2.ZERO, _pan5, maxi(1, int(L5.get("idle_frames", 1))))
	_alexei.flip_h = true
	_alexei_idle.flip_h = true
	_snow5 = snow(p5, Rect2(0, 0, 640, 360), [
		{"count": 60, "v": Vector2(-4, 18), "vjit": 0.4, "size": Vector2(1, 1), "color": Color("#8c97ad"), "sway": 3.0},
		{"count": 14, "v": Vector2(-6, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#b9c2d2"), "sway": 4.0}],
		1501)
	_dip = fx(self, "Dip", _draw_dip)


func _window4() -> Rect2:
	var w: Array = pl("berlin").get("window", [290, 64, 470, 296])
	return Rect2(float(w[0]) + 3.0, float(w[1]) + 3.0, float(w[2]) - float(w[0]) - 6.0, float(w[3]) - float(w[1]) - 3.0)


## Camera drift of a shot: the painting moves `dist` px (halved with reduced motion) linearly over [a, b].
func pan_x(time: float, a: float, b: float, dist: float) -> float:
	return roundf(dist * motion_k() * clampf((time - a) / maxf(0.001, b - a), 0.0, 1.0))


## Black of the dips (0..1) at `time`: film start, every shot change, film end.
func dip_alpha(time: float) -> float:
	var a := 1.0 - clampf(time / FADE_IN, 0.0, 1.0)
	for s in SHOTS.slice(1):
		a = maxf(a, 1.0 - clampf(absf(time - float(s[1])) / DIP, 0.0, 1.0))
	a = maxf(a, clampf((time - float(FADE_OUT[0])) / (float(FADE_OUT[1]) - float(FADE_OUT[0])), 0.0, 1.0))
	return a


## p3: top-left of the stamp sprite at `time` (off the desk before STAMP[0] and after STAMP[3]).
func stamp_pos(time: float) -> Vector2:
	var land := lv(pl("papers"), "imprint_at", Vector2(348, 166)) + STAMP_OFF
	var from := lv(pl("papers"), "stamp_from", Vector2(600, -60))
	if time < float(STAMP[1]):
		return from.lerp(land, ease_in(time, float(STAMP[0]), float(STAMP[1]))).round()
	if time < float(STAMP[2]):
		return land
	return land.lerp(from, ease_in(time, float(STAMP[2]), float(STAMP[3]))).round()


## p5: Alexei's feet x (bg coordinates) and whether he is still walking.
func alexei_at(time: float) -> Array:
	var w: Array = pl("karsk").get("walk", [612, 336, 304])
	var x0 := float(w[0])
	var x1 := float(w[1])
	var d := maxf(0.0, time - WALK_FROM) * ALEXEI_SPEED
	if d >= x0 - x1:
		return [x1, false]
	return [x0 - d, time >= WALK_FROM]


func _apply(time: float) -> void:
	if p1 == null:
		return
	var sh := shot_at(time)
	p1.visible = sh == "p1"
	p2.visible = sh == "p2"
	p3.visible = sh == "p3"
	p4.visible = sh == "p4"
	p5.visible = sh == "p5"
	var rm := reduced_motion()
	# p1: the camera drifts right; the window breathes
	_pan1.position.x = -pan_x(time, 0.0, 13.0, float(pl("line").get("pan", 40)))
	_win1.modulate.a = 0.85 if rm else 0.75 + 0.25 * sin(time * 2.3)
	_snow1.set_time(time * (0.6 if rm else 1.0))
	_beam1.queue_redraw()
	# p2: the label appears (two steps, pixel-hard)
	_label2.visible = time >= VELTRAVA_AT + 0.3
	_label2.modulate.a = 1.0 if time >= VELTRAVA_AT + 0.6 else 0.5
	_map.queue_redraw()
	# p3: the stamp comes down, its shadow tightens under it, the imprint stays
	var p3pan := float(pl("papers").get("pan", 20))
	_pan3.position.x = -pan_x(time, 32.6, 41.0, p3pan)
	var sp := stamp_pos(time)
	var land := lv(pl("papers"), "imprint_at", Vector2(348, 166)) + STAMP_OFF
	var gap := clampf(sp.distance_to(land) / 60.0, 0.0, 1.0)
	_stamp3.position = sp
	_stamp3.visible = time >= float(STAMP[0]) and time < float(STAMP[3])
	_shadow3.visible = _stamp3.visible
	_shadow3.position = sp + Vector2(-4, 0) + Vector2(10, 12) * gap
	_shadow3.modulate = Color(1, 1, 1, 0.45 - 0.25 * gap)
	_imprint.visible = time >= float(STAMP[1])
	_dust3.queue_redraw()
	# p4: Konrad at the window breathing (idle_back), snow and chimney smoke beyond the glass
	var L4 := pl("berlin")
	_pan4.position.x = -float(L4.get("pan", 40)) + pan_x(time, 41.0, 49.0, float(L4.get("pan", 40)) * 0.6)
	var feet := lv(L4, "konrad_feet", Vector2(392, 302))
	_konrad.position = feet - FEET_OFF
	_konrad.frame = 0 if rm else posmod(int(floor(time * 3.0)), maxi(1, _konrad.hframes))
	_snow4.set_time(time * (0.6 if rm else 1.0))
	_smoke4.queue_redraw()
	# p5: Alexei walks in from the right, stops; the signal clears; steam and lit snow
	var L5 := pl("karsk")
	_pan5.position.x = -float(L5.get("pan", 40)) + pan_x(time, 49.0, 58.0, float(L5.get("pan", 40)))
	var aw := alexei_at(time)
	var fy := float((L5.get("walk", [612, 336, 304]) as Array)[2])
	var fpos := Vector2(float(aw[0]), fy) - FEET_OFF
	_alexei.visible = bool(aw[1]) or time < WALK_FROM
	_alexei_idle.visible = not _alexei.visible
	_alexei.position = fpos.round()
	_alexei_idle.position = fpos.round()
	var walked := maxf(0.0, time - WALK_FROM) * ALEXEI_SPEED
	_alexei.frame = posmod(int(floor(walked / ALEXEI_STEP)), maxi(1, _alexei.hframes))
	_alexei_idle.frame = 0 if rm else posmod(int(floor(time * 2.0)), maxi(1, _alexei_idle.hframes))
	_signal5.frame = 1 if time >= SIGNAL_GREEN else 0
	_head5.modulate.a = 0.9 if rm else clampf(fire_wobble(time, 151, 0.05), 0.0, 1.0)
	_snow5.set_time(time * (0.6 if rm else 1.0))
	_steam5.queue_redraw()
	_lit5.queue_redraw()
	_dip.queue_redraw()


# ------------------------------------------------------------------------------------------------ drawing
## p1: the searchlight of the tower sweeps the control strip (a pale fan and its spot on the snow).
func _draw_beam() -> void:
	if not p1.visible:
		return
	var L1 := pl("line")
	var lamp := lv(L1, "lamp", Vector2(426, 180))
	var sweep := 0.0 if reduced_motion() else sin(t * 0.42 + 0.8)
	var spot := Vector2(lamp.x - 70.0 + 120.0 * sweep, 300.0 + 18.0 * cos(t * 0.42 + 0.8))
	var half := 16.0 + 6.0 * (spot.y - 280.0) / 40.0
	var fan := PackedVector2Array([lamp, spot + Vector2(-half, 0), spot + Vector2(half, 0)])
	_beam1.draw_colored_polygon(fan, Color(0.55, 0.52, 0.42, 0.16))
	var ell := PackedVector2Array()
	for i in 20:
		var a := TAU * i / 20.0
		ell.append(spot + Vector2(cos(a) * half * 1.3, sin(a) * half * 0.32))
	_beam1.draw_colored_polygon(ell, Color(0.62, 0.6, 0.5, 0.22))


func _poly_len(pts: PackedVector2Array) -> float:
	var n := 0.0
	for i in range(1, pts.size()):
		n += pts[i - 1].distance_to(pts[i])
	return n


## Point at distance d along a polyline (clamped).
func _poly_at(pts: PackedVector2Array, d: float) -> Vector2:
	var left := d
	for i in range(1, pts.size()):
		var seg := pts[i - 1].distance_to(pts[i])
		if left <= seg:
			return pts[i - 1].lerp(pts[i], left / maxf(seg, 0.001))
		left -= seg
	return pts[pts.size() - 1]


## The polyline from its start up to distance d.
func _poly_part(pts: PackedVector2Array, d: float) -> PackedVector2Array:
	var out := PackedVector2Array([pts[0]])
	var left := d
	for i in range(1, pts.size()):
		var seg := pts[i - 1].distance_to(pts[i])
		if left >= seg:
			out.append(pts[i])
			left -= seg
		else:
			out.append(pts[i - 1].lerp(pts[i], left / maxf(seg, 0.001)))
			break
	return out


## How much of the Line (0..1) and of corridor i (0..1) is drawn at `time`.
func line_drawn(time: float) -> float:
	return clampf((time - float(LINE_DRAW[0])) / (float(LINE_DRAW[1]) - float(LINE_DRAW[0])), 0.0, 1.0)


func corridor_drawn(i: int, time: float) -> float:
	var c: Array = CORRIDORS[i]
	return clampf((time - float(c[0])) / (float(c[1]) - float(c[0])), 0.0, 1.0)


## p2: the Line (dark red, ticks toward the east), Veltrava's ring, the corridors (railway dashes), the trains.
func _draw_map() -> void:
	if not p2.visible:
		return
	var L2 := pl("map")
	var red := Color("#8a2b24")
	var ink := Color("#2e211a")
	var paper := Color("#e9dfc4")
	var line := _pts(L2.get("line", []))
	if line.size() >= 2:
		var total := _poly_len(line)
		var drawn := total * line_drawn(t)
		if drawn > 0.5:
			var part := _poly_part(line, drawn)
			_map.draw_polyline(part, red, 2.0)
			var d := 4.0
			while d < drawn:
				var a := _poly_at(line, d)
				var b := _poly_at(line, d + 1.0)
				var nrm := (b - a).normalized().orthogonal()
				if nrm.x < 0.0:
					nrm = -nrm
				_map.draw_line(a.round(), (a + nrm * 4.0).round(), red, 1.0)
				d += 7.0
	var cors: Array = L2.get("corridors", [])
	for i in cors.size():
		var cp := _pts(cors[i])
		if cp.size() < 2:
			continue
		var tot := _poly_len(cp)
		var dd := tot * corridor_drawn(i, t)
		if dd <= 0.5:
			continue
		_map.draw_polyline(_poly_part(cp, dd), ink, 3.0)
		var s := 2.0
		while s + 4.0 < dd:
			var p0 := _poly_at(cp, s)
			var p1v := _poly_at(cp, s + 4.0)
			_map.draw_line(p0, p1v, paper, 1.0)
			s += 8.0
		if t >= TRAINS_FROM:
			for k in 2:
				var at := fposmod((t - TRAINS_FROM) * TRAIN_SPEED * (1.0 if reduced_motion() == false else 0.5)
					+ tot * (0.18 + 0.5 * k + 0.13 * i), tot)
				var tp := _poly_at(cp, at).round()
				_map.draw_rect(Rect2(tp - Vector2(2, 2), Vector2(5, 4)), Color("#7a1f1a"))
				_map.draw_rect(Rect2(tp - Vector2(1, 1), Vector2(3, 2)), Color("#c9533f"))
	if t >= VELTRAVA_AT:
		var v := lv(L2, "veltrava", Vector2(322, 196))
		var u := clampf((t - VELTRAVA_AT) / 0.6, 0.0, 1.0)
		_map.draw_arc(v, 6.5, -PI * 0.5, -PI * 0.5 + TAU * u, 28, ink, 1.0)
		if u >= 1.0:
			_map.draw_arc(v, 9.0, 0.0, TAU, 32, ink, 1.0)
			_map.draw_rect(Rect2(v - Vector2(1, 1), Vector2(3, 3)), red)


## p3: dust turning in the lamp light over the desk.
func _draw_dust3() -> void:
	if not p3.visible:
		return
	for i in 26:
		var sp := 4.0 + 6.0 * h01(i, 3301)
		var x := fposmod(h01(i, 3302) * 520.0 + sin(t * 0.4 + i) * 10.0 * motion_k() + (t - 32.6) * sp * 0.5, 520.0) + 60.0
		var y := fposmod(h01(i, 3303) * 300.0 - (t - 32.6) * sp * motion_k(), 300.0) + 40.0
		var lit := clampf(1.0 - Vector2(x, y).distance_to(Vector2(150, 60)) / 360.0, 0.0, 1.0)
		if lit > 0.05:
			_dust3.draw_rect(Rect2(Vector2(x, y).round(), Vector2.ONE), Color(0.9, 0.75, 0.5, 0.5 * lit))


## p4: smoke from the chimneys beyond the window (drawn only inside the glass).
func _draw_smoke4() -> void:
	if not p4.visible:
		return
	var g := _window4()
	var chim: Array = pl("berlin").get("chimneys", [])
	for ci in chim.size():
		var base := Vector2(float(chim[ci][0]), float(chim[ci][1]))
		for k in 6:
			var age := fposmod(t * 0.5 + k / 6.0 + h01(ci, 4401), 1.0)
			var p := base + Vector2(age * 26.0 * motion_k() + sin(age * 5.0 + ci) * 2.0, -age * 30.0)
			var r := 1.0 + age * 4.0
			var rc := Rect2((p - Vector2(r, r)).round(), Vector2(r, r) * 2.0)
			if g.encloses(rc):
				_smoke4.draw_rect(rc, Color(0.86, 0.87, 0.9, 0.42 * (1.0 - age)))


## p5: steam rising from the waiting locomotive.
func _draw_steam5() -> void:
	if not p5.visible:
		return
	var base := lv(pl("karsk"), "chimney", Vector2(330, 178))
	for k in 7:
		var age := fposmod(t * 0.35 + k / 7.0, 1.0)
		var p := base + Vector2(age * 18.0 * motion_k() + sin(age * 4.0 + k) * 2.0, -age * 42.0)
		var r := 1.5 + age * 6.0
		_steam5.draw_rect(Rect2((p - Vector2(r, r * 0.8)).round(), Vector2(r * 2.0, r * 1.6)),
			Color(0.42, 0.45, 0.52, 0.5 * (1.0 - age)))


## p5: flakes caught in the floodlight cone glitter.
func _draw_lit5() -> void:
	if not p5.visible:
		return
	var L5 := pl("karsk")
	var top := lv(L5, "flood", Vector2(178, 70))
	var ca := lv(L5, "cone_at", Vector2(69, 70))
	var bottom_y := ca.y + 236.0
	var k := motion_k()
	for i in 46:
		var sp := 14.0 + 12.0 * h01(i, 5501)
		var y := fposmod(h01(i, 5502) * 240.0 + t * sp * k, 236.0) + top.y
		var u := (y - top.y) / (bottom_y - top.y)
		var hw := 9.0 + 100.0 * u
		var x := top.x + (h01(i, 5503) * 2.0 - 1.0) * hw * 0.92 + sin(t * 0.9 + i) * 3.0 * k
		var a := 0.35 + 0.4 * h01(i, 5504)
		_lit5.draw_rect(Rect2(Vector2(x, y).round(), Vector2.ONE * (2.0 if i % 9 == 0 else 1.0)),
			Color(0.95, 0.92, 0.8, a * (1.0 - 0.5 * u)))


func _draw_dip() -> void:
	var a := dip_alpha(t)
	if a > 0.001:
		_dip.draw_rect(Rect2(-8, -8, 656, 376), Color(0, 0, 0, a))
