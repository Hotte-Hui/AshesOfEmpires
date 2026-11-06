extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## LS_C3_ToHall (~6 s) — Alexei's station hands over to Konrad's palais on a single time (C3_DESIGN §2.9).
##   k1 0-3 s  the cast-iron platform clock under the glazed canopy at 9:39:57, snow, drifting steam; the
##             seconds hand ticks, the minute hand jumps to 9:40 with a clack (railway clock)
##   k2 3-6 s  match cut to the gilded Jugendstil clock of the palais at 9:40 (same dial, same centre, same hand
##             angles), its pendulum swinging, a soft chime bridges the cut; Konrad's silhouette walks in below it
## Sound: the station ambience gives way to the palais; mus_veltrava keeps playing (both levels use it).
## Subtitle: cin.c3.tohall.time.  Art: assets/cinematics/ch3/tohall/ (tools/pixelgen/env_veltrava_cine.py).

const FX := preload("res://scenes/cinematics/ch3_common/pixel_fx.gd")

const DUR := 6.0
const CUT := 3.0
const SHOTS := [["k1", 0.0, 3.0], ["k2", 3.0, 6.0]]
## clock face shared by both shots (match cut) — must equal LAYOUT['tohall'] in the generator
const CENTER := Vector2(320, 170)
const LEN_HOUR := 27.0
const LEN_MIN := 40.0
const LEN_SEC := 43.0
const LINE_TIME := "cin.c3.tohall.time"
const SEC_TICKS := [0.4, 1.4, 2.4]       # :58, :59, :00 (+ the minute jump)
const STEP0 := 3.55                      # Konrad's first footfall under the palais clock
const STEP := 0.55

var k1: Node2D
var k2: Node2D
var _hands1: Node2D
var _hands2: Node2D
var _snow: Node2D
var _steam: Node2D
var _steam_tex: Texture2D
var _pendulum: Sprite2D
var _konrad: Sprite2D
var _dust: Node2D
var _glass1: Sprite2D
var _glass2: Sprite2D
var _layout: Dictionary = {}
var _k1life: Node2D
var _bird_tex: Texture2D
## round 10 (figures stream): travellers under the station clock, the usher and delegates in the palais
## (env_veltrava_cine_people.EXTRAS -> layout tohall.extras)
const People := preload("res://scenes/cinematics/ch3_common/c3_people.gd")
var _people_k1: Node2D
var _people_k2: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0


## the extras of one shot (names start with the shot id)
func _extras(prefix: String) -> Array:
	var out: Array = []
	for e in _layout.get("extras", []):
		if e is Dictionary and str((e as Dictionary).get("name", "")).begins_with(prefix):
			out.append(e)
	return out


func chosen_lines() -> Array:
	return [LINE_TIME]


func get_shot_id() -> String:
	return "k1" if t < CUT else "k2"


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "amb": "amb_veltrava_station", "fade": 0.8},
		{"t": SEC_TICKS[0], "sfx": "c3cine_clock_tick", "db": -10.0, "pv": 0.02},
		{"t": SEC_TICKS[1], "sfx": "c3cine_clock_tick", "db": -10.0, "pv": 0.02},
		{"t": SEC_TICKS[2], "sfx": "c3cine_clock_clack", "db": -6.0, "pv": 0.0},     # the minute hand jumps
		{"t": CUT, "sfx": "c3cine_palais_chime", "db": -8.0, "pv": 0.0},
		{"t": CUT, "amb": "amb_veltrava_palais", "fade": 0.7},
		{"t": 3.25, "say": LINE_TIME, "dur": 2.6},
	]
	# his footsteps on the marble (round 10b: five -- he walks until the shot ends, the near foot on STEP0)
	for k in 5:
		c.append({"t": STEP0 + k * STEP, "sfx": "c3cine_step_marble", "db": -13.0 + k * 0.7, "pv": 0.04})
	return c


func _build() -> void:
	var p := ASSETS + "layout.json"
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			_layout = d.get("tohall", {})
	k1 = group("StationClock")
	sprite("tohall/k1_bg.png", Vector2.ZERO, k1)
	_people_k1 = People.new()
	_people_k1.setup(_extras("k1_"), tex)
	k1.add_child(_people_k1)
	_steam_tex = tex("tohall/steam_puffs.png")
	_steam = Node2D.new()
	_steam.name = "Steam"
	_steam.draw.connect(_draw_steam)
	k1.add_child(_steam)
	_k1life = Node2D.new()                         # round 10: the carriage stove's smoke, pigeons under the canopy
	_k1life.name = "Life"
	_k1life.draw.connect(_draw_k1life)
	k1.add_child(_k1life)
	_bird_tex = tex("trains/d4_gull.png")
	sprite("tohall/k1_clock.png", Vector2.ZERO, k1)
	_hands1 = Node2D.new()
	_hands1.name = "Hands"
	_hands1.draw.connect(_draw_hands.bind(_hands1, false))
	k1.add_child(_hands1)
	_glass1 = sprite("tohall/k1_glass.png", Vector2.ZERO, k1, 1, true)
	_snow = FX.new()
	_snow.name = "Snow"
	k1.add_child(_snow)
	var k := 0.6 if reduced_motion() else 1.0
	_snow.setup_snow(Rect2(0, 0, 640, 360), [
		{"count": int(70 * k), "v": Vector2(6, 16), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#8593a3"), "sway": 2.0},
		{"count": int(34 * k), "v": Vector2(9, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#dee2e7"), "sway": 3.0}], 4101)
	k2 = group("PalaisClock")
	sprite("tohall/k2_bg.png", Vector2.ZERO, k2)
	_pendulum = sprite("tohall/pendulum.png", Vector2.ZERO, k2, 8)
	var pp = _layout.get("pendulum")
	if pp is Array and pp.size() >= 2:
		_pendulum.position = Vector2(float(pp[0]), float(pp[1]))
	sprite("tohall/k2_clock.png", Vector2.ZERO, k2)
	_hands2 = Node2D.new()
	_hands2.name = "Hands"
	_hands2.draw.connect(_draw_hands.bind(_hands2, true))
	k2.add_child(_hands2)
	_glass2 = sprite("tohall/k2_glass.png", Vector2.ZERO, k2, 1, true)
	_dust = Node2D.new()
	_dust.name = "Dust"
	_dust.draw.connect(_draw_dust)
	k2.add_child(_dust)
	_people_k2 = People.new()
	_people_k2.setup(_extras("k2_"), tex)
	k2.add_child(_people_k2)
	_konrad = sprite("tohall/k2_konrad.png", Vector2.ZERO, k2, int(_layout.get("konrad_frames", 2)))


func _apply(time: float) -> void:
	if k1 == null:
		return
	var rm := reduced_motion()
	k1.visible = time < CUT
	k2.visible = time >= CUT
	_snow.set_time(time * (0.6 if rm else 1.0))
	_steam.queue_redraw()
	_k1life.queue_redraw()
	_hands1.queue_redraw()
	_hands2.queue_redraw()
	_dust.queue_redraw()
	if _people_k1:
		_people_k1.set_time(time)
		_people_k2.set_time(time)
	# pendulum: 8 pre-drawn angles, one full swing per 1.2 s (ping-pong)
	if _pendulum.texture:
		var ph := fposmod((time - CUT) / 1.2, 1.0)
		var s := sin(ph * TAU)
		_pendulum.frame = clampi(int(roundf((s * 0.5 + 0.5) * 7.0)), 0, 7)
	# Konrad walks in from the left and is under the clock as the shot ends (round 10b: konrad_on_path; the
	# round-10 placement below only runs for layouts without a path)
	if _konrad.texture and not konrad_on_path(time):
		var nf := maxi(1, _konrad.hframes)
		var w := float(_konrad.texture.get_width()) / float(nf)
		# constant walking pace (he enters from the left edge and is under the clock as the shot ends)
		var v := 58.0 if not rm else 38.0
		var x := -w + 30.0 + (time - (STEP0 - 0.35)) * v
		var y := float(_layout.get("konrad_y", 360 - _konrad.texture.get_height()))
		_konrad.visible = time >= STEP0 - 0.35
		if nf >= 8:
			# round 10: a full walk cycle (two footfalls = one cycle; the rise and fall is in the frames)
			var cyc := fposmod((time - STEP0) / (2.0 * STEP), 1.0)
			_konrad.position = Vector2(roundf(x), y)
			_konrad.frame = clampi(int(floor(cyc * float(nf))), 0, nf - 1)
		else:
			var ph := fposmod((time - STEP0) / STEP, 1.0)
			var up := ph > 0.5                       # the body rises between the footfalls
			_konrad.position = Vector2(roundf(x), y + (0.0 if up else 1.0))
			_konrad.frame = 1 if up else 0


## Round 10b (figures stream): Konrad as a whole man walking along layout konrad_path ([[t, x, y], ...] of his
## soles; konrad_anchor = the soles in the frame).  He is already walking in from the left when the shot cuts in
## and is under the clock as it ends; the walk cycle follows the floor he covers (konrad_stride px per cycle,
## phased so his near foot strikes on STEP0 with the first footstep sound), so the planted foot never slides.
## He keeps his pace with reduced motion, like the extras around him (c3_people.gd) and in step with the footstep
## sounds.  Returns false (old layouts) to let the round-10 code place him.
func konrad_on_path(time: float) -> bool:
	var kp = _layout.get("konrad_path", [])
	if not (kp is Array) or (kp as Array).size() < 2:
		return false
	var nf := maxi(1, _konrad.hframes)
	var fw := float(_konrad.texture.get_width()) / float(nf)
	var anc: Array = _layout.get("konrad_anchor", [fw * 0.5, float(_konrad.texture.get_height()) - 1.0])
	var stride := maxf(1.0, float(_layout.get("konrad_stride", 88.0)))
	var t0 := float(kp[0][0])
	var pw: Array = People.path_at(kp, time)
	var ref: Array = People.path_at(kp, STEP0)
	_konrad.visible = time >= t0
	_konrad.position = ((pw[0] as Vector2) - Vector2(float(anc[0]), float(anc[1]))).round()
	var cyc := fposmod((float(pw[1]) - float(ref[1])) / stride, 1.0)
	_konrad.frame = clampi(int(floor(cyc * float(nf))), 0, nf - 1)
	return true


## Clock time shown (in seconds after 9:00:00) — railway clock: the seconds tick, the minute jumps at :00.
func shown_time(time: float) -> Vector3:
	var sec := 57
	for tk in SEC_TICKS:
		if time >= tk:
			sec += 1
	var minute := 39
	if sec >= 60:
		sec -= 60
		minute = 40
	if time >= CUT:
		minute = 40
		sec = 0
	return Vector3(9, minute, sec)


func _hand_angles(time: float) -> Vector3:
	var c := shown_time(time)
	var hour := (c.x + c.y / 60.0) * 30.0
	return Vector3(hour, c.y * 6.0, c.z * 6.0)


func _draw_hands(ci: Node2D, gilt: bool) -> void:
	var a := _hand_angles(t)
	var dark := Color("#15171c")
	var mid := Color("#323840")
	if gilt:
		dark = Color("#4a3415")
		mid = Color("#c49a48")
	_hand(ci, a.x, LEN_HOUR, 2, dark, mid, gilt)
	_hand(ci, a.y, LEN_MIN, 1, dark, mid, gilt)
	if not gilt:
		var d := _dir(a.z)
		FX.line(ci, CENTER - d * 9.0, CENTER + d * LEN_SEC, Color("#7a2218"))
		ci.draw_rect(Rect2((CENTER - d * 9.0).round() - Vector2(1, 1), Vector2(3, 3)), Color("#7a2218"))
	ci.draw_rect(Rect2(CENTER - Vector2(2, 2), Vector2(5, 5)), dark)
	ci.draw_rect(Rect2(CENTER - Vector2(1, 1), Vector2(3, 3)), mid if gilt else Color("#464d55"))


static func _dir(deg: float) -> Vector2:
	var r := deg_to_rad(deg)
	return Vector2(sin(r), -cos(r))


func _hand(ci: Node2D, deg: float, length: float, half: int, dark: Color, mid: Color, gilt: bool) -> void:
	var d := _dir(deg)
	var n := Vector2(-d.y, d.x)
	for k in range(-half, half + 1):
		var off := n * float(k) * 0.9
		FX.line(ci, CENTER + off - d * 6.0, CENTER + off + d * (length - absf(k) * 3.0), dark)
	if gilt:
		FX.line(ci, CENTER + n * 0.4 - d * 4.0, CENTER + d * (length - 2.0), mid)
		var tip := (CENTER + d * (length - 4.0)).round()
		ci.draw_rect(Rect2(tip - Vector2(1, 1), Vector2(3, 3)), mid)


func _draw_steam() -> void:
	if _steam_tex == null:
		return
	var n := int(_layout.get("steam_frames", 4))
	var fw := _steam_tex.get_width() / n
	var fh := _steam_tex.get_height()
	var rm := reduced_motion()
	var sp := 0.5 if rm else 1.0
	# a few large puffs drifting left -> right across the canopy.  AD round 2: each puff lives its own life (the
	# frames are one cloud at successive ages): it swells and thins continuously -- the frame steps are cross-faded
	# -- and fades in when born / out when spent, so nothing pops (the old loop snapped every puff back to its
	# smallest shape every 0.67 s).  [x at t=0, y at t=0, age at t=0 (s)]
	var life := 7.5
	var puffs := [[-180.0, 92.0, 4.2], [60.0, 206.0, 2.4], [300.0, 120.0, 5.6], [-40.0, 250.0, 0.9],
		[470.0, 230.0, 3.3], [150.0, 150.0, -0.8]]
	for i in puffs.size():
		var pf: Array = puffs[i]
		var age: float = float(pf[2]) + t * sp
		if age <= 0.0 or age >= life:
			continue
		var x: float = pf[0] + t * 34.0 * sp + i * 6.0
		var y: float = pf[1] - t * 4.0 * sp
		var f := age / life * float(n - 1)
		var f0 := mini(int(floor(f)), n - 1)
		var f1 := mini(f0 + 1, n - 1)
		var fr := f - float(f0)
		var a := ramp01(age, 0.0, 0.8) * (1.0 - ramp01(age, life - 1.6, life))
		var dst := Rect2(Vector2(roundf(x), roundf(y)), Vector2(fw, fh))
		_steam.draw_texture_rect_region(_steam_tex, dst, Rect2(f0 * fw, 0, fw, fh), Color(1, 1, 1, a * (1.0 - fr)))
		if f1 != f0 and fr > 0.0:
			_steam.draw_texture_rect_region(_steam_tex, dst, Rect2(f1 * fw, 0, fw, fh), Color(1, 1, 1, a * fr))


## dust motes drifting in the chandelier light of the palais
func _draw_dust() -> void:
	if t < CUT:
		return
	var rng_step := 0
	for i in 26:
		var bx := 120.0 + float((i * 97) % 400)
		var by := 70.0 + float((i * 53) % 200)
		var tt := t - CUT
		var x := bx + sin(tt * 0.6 + i) * 6.0 + tt * 2.0
		var y := by + tt * (1.5 + (i % 3)) + cos(tt * 0.8 + i * 1.3) * 3.0
		var twinkle := (_h(int(floor(tt * 4.0)) + i * 13, 77) + 1.0) * 0.5
		if twinkle > 0.35:
			_dust.draw_rect(Rect2(Vector2(roundf(x), roundf(y)), Vector2.ONE), Color("#e9b46e") if i % 2 == 0 else Color("#c88a4e"))
		rng_step += 1


## k1 (round 10): smoke from the carriage stove's chimney; pigeons start up from the canopy girder when the
## minute hand clacks over to 9:40 and wheel out under the glass
func _draw_k1life() -> void:
	if t >= CUT:
		return
	var rm := reduced_motion()
	var ch: Array = _layout.get("k1_chimney", [199, 234])
	for k in 6:
		var age := fposmod(t * (0.6 if rm else 1.0) * 0.9 + float(k) * 0.55, 3.3)
		var c := Vector2(float(ch[0]) + age * 5.0 + sin(age * 2.0 + k) * 1.2, float(ch[1]) - age * 9.0)
		var r := 1.2 + age * 1.5
		var col := Color(0.55, 0.6, 0.68, clampf(0.5 - age * 0.14, 0.0, 0.5))
		var ir := int(ceil(r))
		for dy in range(-ir, ir + 1):
			for dx in range(-ir, ir + 1):
				var d := sqrt(float(dx * dx + dy * dy)) / maxf(r, 0.5)
				var pp := Vector2(roundf(c.x) + dx, roundf(c.y) + dy)
				var th := (float((int(pp.x + k) % 4) * 4 + (int(pp.y) % 4)) + 0.5) / 16.0
				if d <= 1.0 and (1.0 - d * d) * 1.2 > th:
					_k1life.draw_rect(Rect2(pp, Vector2.ONE), col)
	if _bird_tex == null:
		return
	var fw := _bird_tex.get_width() / 4
	var fh := _bird_tex.get_height()
	var start := float(SEC_TICKS[2]) + 0.05
	for b in 5:
		var rest := Vector2(150.0 + float(b) * 23.0, 175.0 - float(b % 2) * 2.0)
		var bt := t - start - float(b) * 0.06
		var pos := rest
		var fi := 2
		if bt > 0.0:
			var sp := 0.6 if rm else 1.0
			pos = rest + Vector2(bt * (60.0 + b * 9.0) * sp, -bt * (34.0 - bt * 9.0) * sp + sin(bt * 5.0 + b) * 2.0)
			fi = int(floor(bt * 14.0 + b)) % 4
		elif b % 2 == 0:
			fi = 3 if fposmod(t * 1.3 + b, 1.0) > 0.85 else 2
		_k1life.draw_texture_rect_region(_bird_tex, Rect2(pos.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh))
