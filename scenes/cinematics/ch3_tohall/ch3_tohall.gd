extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## LS_C3_ToHall (~6 s) — Alexei's station hands over to Konrad's palais on a single time (C3_DESIGN §2.9).
##   k1 0-3 s  the wrought-iron platform clock at 9:39:57, snow, drifting steam; the minute hand jumps to
##             9:40 with a clack
##   k2 3-6 s  match cut to the gilded Jugendstil wall clock of the palais at 9:40 (same face, same centre,
##             same hand angles), a soft bell bridges the cut; Konrad's silhouette walks in below it
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
var _layout: Dictionary = {}


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0


func chosen_lines() -> Array:
	return [LINE_TIME]


func get_shot_id() -> String:
	return "k1" if t < CUT else "k2"


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 2.0},
		{"t": 0.0, "amb": "amb_karsk_yard", "fade": 1.0},
		{"t": 0.4, "sfx": "type_tick", "db": -14.0},
		{"t": 1.4, "sfx": "type_tick", "db": -14.0},
		{"t": 2.4, "sfx": "type_tick", "db": -5.0, "pv": 0.0},
		{"t": 2.42, "sfx": "card_place", "db": -12.0},
		{"t": CUT, "sfx": "tram_bell", "db": -15.0, "pv": 0.0},
		{"t": CUT, "amb": "amb_berlin_archive", "fade": 0.7},
		{"t": 3.25, "say": LINE_TIME, "dur": 2.6},
		{"t": 3.95, "sfx": "step_wood", "db": -17.0},
		{"t": 4.5, "sfx": "step_wood", "db": -16.0},
		{"t": 5.05, "sfx": "step_wood", "db": -15.0},
		{"t": 5.6, "sfx": "step_wood", "db": -15.0},
	]


func _build() -> void:
	var p := ASSETS + "layout.json"
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			_layout = d.get("tohall", {})
	k1 = group("StationClock")
	sprite("tohall/k1_bg.png", Vector2.ZERO, k1)
	_steam_tex = tex("tohall/steam_puffs.png")
	_steam = Node2D.new()
	_steam.name = "Steam"
	_steam.draw.connect(_draw_steam)
	k1.add_child(_steam)
	sprite("tohall/k1_clock.png", Vector2.ZERO, k1)
	_hands1 = Node2D.new()
	_hands1.name = "Hands"
	_hands1.draw.connect(_draw_hands.bind(_hands1, false))
	k1.add_child(_hands1)
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
	_dust = Node2D.new()
	_dust.name = "Dust"
	_dust.draw.connect(_draw_dust)
	k2.add_child(_dust)
	_konrad = sprite("tohall/k2_konrad.png", Vector2.ZERO, k2, 2)


func _apply(time: float) -> void:
	if k1 == null:
		return
	var rm := reduced_motion()
	k1.visible = time < CUT
	k2.visible = time >= CUT
	_snow.set_time(time * (0.6 if rm else 1.0))
	_steam.queue_redraw()
	_hands1.queue_redraw()
	_hands2.queue_redraw()
	_dust.queue_redraw()
	# pendulum: 8 pre-drawn angles, one full swing per 1.2 s (ping-pong)
	if _pendulum.texture:
		var ph := fposmod((time - CUT) / 1.2, 1.0)
		var s := sin(ph * TAU)
		_pendulum.frame = clampi(int(roundf((s * 0.5 + 0.5) * 7.0)), 0, 7)
	# Konrad: a foreground silhouette entering from the left under the clock
	if _konrad.texture:
		var w := float(_konrad.texture.get_width()) / 2.0
		var u := ramp01(time, 3.55, DUR + 0.5)
		var x := lerpf(-w - 4.0, 250.0 - w * 0.5, u) if not rm else lerpf(-w * 0.4, 150.0 - w * 0.5, ramp01(time, 3.4, DUR + 1.0))
		var y := float(_layout.get("konrad_y", 360 - _konrad.texture.get_height()))
		var step := int(floor((time - 3.55) / 0.275))
		_konrad.position = Vector2(roundf(x), y + (1.0 if step % 2 == 1 else 0.0))
		_konrad.frame = 1 if step % 2 == 1 else 0


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
	# a few large puffs drifting left -> right across the canopy, thinning out
	var puffs := [[-180.0, 92.0, 0], [60.0, 206.0, 1], [300.0, 120.0, 2], [-40.0, 250.0, 3], [470.0, 230.0, 1]]
	for i in puffs.size():
		var pf: Array = puffs[i]
		var x: float = pf[0] + t * 34.0 * sp + i * 6.0
		var y: float = pf[1] - t * 4.0 * sp
		var fi := (int(pf[2]) + int(floor(t * 1.5))) % n
		_steam.draw_texture_rect_region(_steam_tex, Rect2(Vector2(roundf(x), roundf(y)), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh))


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
