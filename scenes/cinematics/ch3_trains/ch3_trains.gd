extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## LS_C3_Trains (25.5 s) — the Chapter 2 -> 3 character switch „Konrads Zugfenster -> Alexeis Zugfenster“
## (STORY_BIBLE §6, C3_DESIGN §2.9).  Art: tools/pixelgen/env_veltrava_cine*.py -> assets/cinematics/ch3/trains/.
##   t1  0-8 s    night, the German delegation's saloon car: Konrad at the window, the reading lamp, his hand at
##                the cup, his face in the black glass; outside the snow plain, telegraph poles and wires, the
##                floodlit Line with a searchlight sweeping the strip; a lineside lamp throws its light through
##                the car; the car rocks over the rail joints
##   t2  8-10 s   match cut through the window frame: a floodlit level crossing passes, its light floods the glass,
##                the room behind changes (the glass opening and its iron sash are pixel-identical in both cars)
##   t3  10-18 s  the Soviet car: Alexei at the window, his hand at the tea glass in its holder (the spoon
##                rattles with every joint), the same plain from the other side, scrolling the other way
##   t4  18-25.5  dawn: Konrad's train from the west on the far track, Alexei's with the sealed wagon 4 from the
##                east on the near track; they meet over the middle arch, their plumes run together; crows lift
##                off the ice at the whistle, a woman pulls a sled along the bank
## Inner lines (configure(ctx).flags): Konrad evidence > suspicion > base, Alexei irina > secrecy > base,
## then cin.c3.trains.place.  Reduced motion: half the travel speed, no jolts/sway, a soft flare, fewer flakes.

const FX := preload("res://scenes/cinematics/ch3_common/pixel_fx.gd")

## glass opening / exterior box — must match env_veltrava_cine.py (GLASS, EXT; checked by the test
## against assets/cinematics/ch3/layout.json)
const GLASS := Rect2i(172, 84, 296, 142)
const EXT := Rect2i(164, 76, 312, 158)
const CUT := 9.0                      # the room changes here (inside the flare)
const T1_END := 8.0
const T3_START := 10.0
const T4_START := 18.0
const DUR := 25.5
const SHOTS := [["t1", 0.0, 8.0], ["t2", 8.0, 10.0], ["t3", 10.0, 18.0], ["t4", 18.0, 25.5]]
## parallax speeds (px/s at full motion): far fence, plain, embankment, telegraph poles
const SPEED := {"far": 5.0, "mid": 26.0, "near": 150.0, "pole": 250.0}
const POLE_SPACING := 360.0
const POLE_INS := [[1, 19], [14, 19], [3, 31], [12, 31]]   # insulator tops, local to the pole sprite
const POLE_Y := 74
## rail joints: period and phase of the double knock for each car (the bed sounds are cut to the same beat)
const JOINT := {"k": [0.3, 1.55], "a": [9.4, 1.8]}
## a lineside lamp passing the window (time of passing the glass centre) in each car
const PASS_LAMP := {"k": 3.4, "a": 13.6}
## dissolve t3 -> t4
const DAWN_IN := [17.3, 18.3]
const DAWN_IN_RM := [16.9, 18.6]

var line_konrad := "cin.c3.trains.konrad.base"
var line_alexei := "cin.c3.trains.alexei.base"
const LINE_PLACE := "cin.c3.trains.place"

var win: Node2D
var ext: Node2D
var room_k: Node2D
var room_a: Node2D
var dawn: Node2D
var _sky: Sprite2D
var _far_de: Sprite2D
var _far_su: Sprite2D
var _mid: Sprite2D
var _near: Sprite2D
var _patch_k: Sprite2D
var _patch_a: Sprite2D
var _beams: Node2D
var _poles: Node2D
var _pole_tex: Texture2D
var _snow_far: Node2D
var _snow_near: Node2D
var _sweep: Sprite2D
var _flare: Sprite2D
var _fig_k: Sprite2D
var _fig_a: Sprite2D
var _glow_k: Sprite2D
var _glow_a: Sprite2D
var _steam: Sprite2D
var _spoon: Sprite2D
var _rflare_k: Sprite2D
var _rflare_a: Sprite2D
var _passer: Node2D
var _dawn_mats: Array = []
var _bridge_bg: Sprite2D
var _train_de: Sprite2D
var _train_su: Sprite2D
var _dawn_glow: Sprite2D
var _bridge_fg: Sprite2D
var _fg_glow: Sprite2D
var _city_smoke: Node2D
var _smoke: Node2D
var _lamps: Node2D
var _life: Node2D
var _bank: Node2D
var _walker_tex: Texture2D
var _layout: Dictionary = {}


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0


# ------------------------------------------------------------------ lines
func _on_configured() -> void:
	if ge1(flags, "konrad_evidence"):
		line_konrad = "cin.c3.trains.konrad.evidence"
	elif ge1(flags, "office_suspicion"):
		line_konrad = "cin.c3.trains.konrad.suspicion"
	else:
		line_konrad = "cin.c3.trains.konrad.base"
	if ge1(flags, "irina_trust"):
		line_alexei = "cin.c3.trains.alexei.irina"
	elif ge1(flags, "alexei_secrecy"):
		line_alexei = "cin.c3.trains.alexei.secrecy"
	else:
		line_alexei = "cin.c3.trains.alexei.base"


func chosen_lines() -> Array:
	return [line_konrad, line_alexei, LINE_PLACE]


func get_shot_id() -> String:
	for s in SHOTS:
		if t < float(s[2]):
			return str(s[0])
	return "t4"


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 2.5},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c3cine_ride_de", "db": -4.0},                   # the saloon car: rumble + joints
		{"t": 1.0, "say": line_konrad, "dur": 6.4},
		{"t": PASS_LAMP["k"] - 0.5, "sfx": "c3cine_pass", "db": -12.0, "pv": 0.04},
		{"t": 8.05, "bed": "c3cine_crossing", "db": -5.0},                 # bell + rush of the level crossing
		{"t": CUT, "bed": "c3cine_ride_su", "db": -4.0},                   # the Soviet car: rattlier, the spoon
		{"t": 10.5, "say": line_alexei, "dur": 6.8},
		{"t": PASS_LAMP["a"] - 0.5, "sfx": "c3cine_pass", "db": -13.0, "pv": 0.04},
		{"t": 17.4, "bed": "c3cine_bridge", "db": -3.0},                   # two trains on the stone bridge
		{"t": 18.5, "bed": "cine_a1m1_whistle_far", "db": -6.0},           # Alexei's engine (the Karsk whistle)
		{"t": 19.0, "music": "mus_veltrava", "fade": 4.0},
		{"t": 19.6, "say": LINE_PLACE, "dur": 5.0},
		{"t": 20.7, "bed": "c3cine_whistle_de", "db": -9.0},               # Konrad's engine answers, lower
	]
	return c


# ------------------------------------------------------------------ build
func _build() -> void:
	var p := ASSETS + "layout.json"
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			_layout = d.get("trains", {})
	win = group("Window")
	ext = group("Exterior", win)
	var ex := Vector2(EXT.position)
	_sky = sprite("trains/ext_sky.png", ex, ext)
	_far_de = strip("trains/ext_far_de.png", Vector2(ex.x, 136), EXT.size.x, ext)
	_far_su = strip("trains/ext_far_su.png", Vector2(ex.x, 136), EXT.size.x, ext)
	_far_su.flip_h = true
	_beams = Node2D.new()
	_beams.name = "Searchlight"
	_beams.material = additive()
	_beams.draw.connect(_draw_beams)
	ext.add_child(_beams)
	_mid = strip("trains/ext_mid.png", Vector2(ex.x, 186), EXT.size.x, ext)
	_snow_far = FX.new()
	_snow_far.name = "SnowFar"
	ext.add_child(_snow_far)
	_near = strip("trains/ext_near.png", Vector2(ex.x, 212), EXT.size.x, ext)
	_patch_k = sprite("trains/patch_warm.png", Vector2.ZERO, ext, 1, true)
	_patch_a = sprite("trains/patch_cold.png", Vector2.ZERO, ext, 1, true)
	_poles = Node2D.new()
	_poles.name = "Poles"
	_poles.draw.connect(_draw_poles)
	ext.add_child(_poles)
	_pole_tex = tex("trains/pole.png")
	_passer = Node2D.new()
	_passer.name = "PassingLamp"
	_passer.draw.connect(_draw_passer)
	ext.add_child(_passer)
	_snow_near = FX.new()
	_snow_near.name = "SnowNear"
	ext.add_child(_snow_near)
	_sweep = sprite("trains/sweep.png", Vector2(0, EXT.position.y), ext, 1, true)
	_flare = sprite("trains/flare.png", Vector2.ZERO, ext, 1, true)
	room_k = group("RoomKonrad", win)
	sprite("trains/refl_konrad.png", Vector2.ZERO, room_k, 1, true)
	sprite("trains/int_konrad.png", Vector2.ZERO, room_k)
	_fig_k = sprite("trains/fig_konrad.png", Vector2.ZERO, room_k, 4)
	_glow_k = sprite("trains/glow_lamp.png", Vector2.ZERO, room_k, 1, true)
	_rflare_k = sprite("trains/roomflare_k.png", Vector2.ZERO, room_k, 1, true)
	room_a = group("RoomAlexei", win)
	sprite("trains/refl_alexei.png", Vector2.ZERO, room_a, 1, true)
	sprite("trains/int_alexei.png", Vector2.ZERO, room_a)
	_spoon = sprite("trains/spoon.png", Vector2.ZERO, room_a, 2)
	_fig_a = sprite("trains/fig_alexei.png", Vector2.ZERO, room_a, 4)
	_glow_a = sprite("trains/glow_tea.png", Vector2.ZERO, room_a, 1, true)
	_steam = sprite("trains/steam_tea.png", Vector2.ZERO, room_a, 6)
	_rflare_a = sprite("trains/roomflare_a.png", Vector2.ZERO, room_a, 1, true)
	for pair in [[_fig_k, "fig_konrad"], [_fig_a, "fig_alexei"], [_glow_k, "glow_lamp"], [_glow_a, "glow_tea"],
			[_steam, "steam_tea"], [_sweep, "sweep"], [_spoon, "spoon"]]:
		var v = _layout.get(pair[1])
		if v is Array and v.size() >= 2 and pair[0]:
			(pair[0] as Sprite2D).position = Vector2(float(v[0]), float(v[1]))
	# ---- dawn: every node of the group carries a dissolve material (additive twin for the glows)
	dawn = group("Dawn")
	var mat := dissolve_material(false)
	var mat_add := dissolve_material(true)
	_dawn_mats = [mat, mat_add]
	_bridge_bg = sprite("trains/bridge_bg.png", Vector2.ZERO, dawn)
	_dawn_glow = sprite("trains/dawn_glow.png", Vector2.ZERO, dawn)
	_city_smoke = _drawer("CitySmoke", dawn, _draw_city_smoke)
	_train_de = sprite("trains/train_de.png", Vector2.ZERO, dawn, 1, false, 2)
	_train_su = sprite("trains/train_su.png", Vector2.ZERO, dawn, 1, false, 2)
	_smoke = _drawer("Smoke", dawn, _draw_smoke)
	_life = _drawer("Life", dawn, _draw_life)
	_bridge_fg = sprite("trains/bridge_fg.png", Vector2.ZERO, dawn)
	_bank = _drawer("Bank", dawn, _draw_bank)
	_lamps = _drawer("Headlamps", dawn, _draw_lamps)
	_fg_glow = sprite("trains/fg_glow.png", Vector2.ZERO, dawn)
	for n in [_bridge_bg, _city_smoke, _train_de, _train_su, _smoke, _life, _bridge_fg, _bank]:
		(n as CanvasItem).material = mat
	for n in [_dawn_glow, _lamps, _fg_glow]:
		(n as CanvasItem).material = mat_add
	_walker_tex = tex("trains/walker.png")
	_setup_snow()


func _drawer(n: String, parent: Node, cb: Callable) -> Node2D:
	var d := Node2D.new()
	d.name = n
	d.draw.connect(cb)
	parent.add_child(d)
	return d


func _setup_snow() -> void:
	var r := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	var k := 0.5 if reduced_motion() else 1.0
	_snow_far.setup_snow(r, [{"count": int(46 * k), "v": Vector2(-70, 16), "vjit": 0.3, "size": Vector2(1, 1),
		"color": Color("#687789"), "sway": 1.5}], 3101)
	_snow_near.setup_snow(r, [{"count": int(26 * k), "v": Vector2(-230, 34), "vjit": 0.25, "size": Vector2(2, 1),
		"color": Color("#c2c9d2"), "sway": 2.0, "streak": 3}, {"count": int(18 * k), "v": Vector2(-150, 26),
		"vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 1.0}], 3102)


# ------------------------------------------------------------------ timeline
func _motion() -> float:
	return 0.5 if reduced_motion() else 1.0


## exterior travel (px of the slowest unit) for the current side; K scrolls content left, A right.
func _travel(time: float) -> float:
	return (time if time < CUT else time - CUT) * _motion()


## 1 while a rail joint knocks under the car (two short knocks per joint), else 0
func _jolt(time: float, side_a: bool) -> int:
	var j: Array = JOINT["a"] if side_a else JOINT["k"]
	var ph := fposmod(time - float(j[0]), float(j[1]))
	return 1 if ph < 0.07 or (ph > 0.16 and ph < 0.22) else 0


func _apply(time: float) -> void:
	if win == null:
		return
	var rm := reduced_motion()
	var side_a := time >= CUT
	var tr := _travel(time)
	win.visible = time < DAWN_IN[1] + 0.4
	room_k.visible = not side_a
	room_a.visible = side_a
	_far_de.visible = not side_a
	_far_su.visible = side_a
	_patch_k.visible = not side_a
	_patch_a.visible = side_a
	for pair in [[_far_de, "far"], [_far_su, "far"], [_mid, "mid"], [_near, "near"]]:
		var s: Sprite2D = pair[0]
		var off := float(SPEED[pair[1]]) * tr + (37.0 if side_a else 0.0)
		s.flip_h = side_a
		set_scroll(s, off)
	_sky.flip_h = side_a
	# snow streams with the travel direction
	var dir := 1.0 if side_a else -1.0
	for sn in [_snow_far, _snow_near]:
		for f in sn.flakes:
			f["v"].x = absf(f["v"].x) * dir
		sn.set_time(tr + (11.0 if side_a else 0.0))
	_poles.queue_redraw()
	_beams.queue_redraw()
	_passer.queue_redraw()
	# the car rocks: a slow 1 px roll of the landscape in the window, the room knocks over the joints
	var jolt := 0
	var roll := 0.0
	if not rm and time < T4_START:
		jolt = _jolt(time, side_a)
		roll = 1.0 if sin(TAU * time / (2.9 if side_a else 3.4) + 0.7) > 0.45 else 0.0
	room_k.position.y = jolt
	room_a.position.y = jolt
	ext.position.y = roll
	# figures: breathing (1 px) + a later small head turn toward the glass
	var breath := 1 if sin(TAU * time / 3.8) > 0.55 else 0
	_fig_k.frame = clampi((2 if time > 4.6 else 0) + breath, 0, 3) if _fig_k.texture else 0
	_fig_a.frame = clampi((2 if time > 14.3 else 0) + breath, 0, 3) if _fig_a.texture else 0
	# the spoon in Alexei's glass tips over with every knock
	if _spoon.texture:
		_spoon.frame = 1 if (side_a and not rm and _jolt(time + 0.03, true) == 1) else 0
	# lamp / tea glow flicker (subtle, never strobing); the passing lamp lights the room for a moment
	var fl := 0.035 * (0.4 if rm else 1.0)
	_glow_k.modulate = Color(1, 1, 1, 0.94 + fl * hnoise(time * 2.7, 7))
	_glow_a.modulate = Color(1, 1, 1, 0.9 + fl * hnoise(time * 2.3, 9))
	if _steam.texture:
		_steam.frame = int(floor(time * (4.0 if rm else 6.0))) % 6
	_apply_flare(time, rm)
	# t3 -> t4 dissolve, then the dawn shot
	var d: Array = DAWN_IN_RM if rm else DAWN_IN
	var prog := clampf((time - float(d[0])) / (float(d[1]) - float(d[0])), 0.0, 1.0)
	dawn.visible = prog > 0.0
	set_dissolve(_dawn_mats, prog)
	_apply_dawn(time, rm)


## 0..1 brightness of the passing lineside lamp's light inside the car
func _pass_light(time: float) -> float:
	var tc: float = PASS_LAMP["a"] if time >= CUT else PASS_LAMP["k"]
	var span := 0.55 / _motion()
	return clampf(1.0 - absf(time - tc) / span, 0.0, 1.0)


func _apply_flare(time: float, rm: bool) -> void:
	var peak := 0.0
	var sweep_x := 0.0
	var show_sweep := false
	if rm:
		peak = ramp01(time, 8.1, CUT) * (1.0 - ramp01(time, CUT, 9.9)) * 0.38
	else:
		peak = ramp01(time, 8.35, 8.92) * (1.0 - ramp01(time, 9.08, 9.7))
		if time > 8.0 and time < 10.0:
			show_sweep = true
			var w := _sweep.texture.get_width() if _sweep.texture else 120
			if time < CUT:     # K side: the light passes right -> left (against Konrad's travel)
				sweep_x = lerpf(GLASS.end.x + 10, GLASS.position.x + GLASS.size.x * 0.5 - w * 0.5, ramp01(time, 8.0, CUT))
			else:              # A side: it leaves to the right (Alexei's train runs the other way)
				sweep_x = lerpf(GLASS.position.x + GLASS.size.x * 0.5 - w * 0.5, GLASS.end.x + 10, ramp01(time, CUT, 9.95))
	_sweep.visible = show_sweep and _sweep.texture != null
	_sweep.position.x = roundf(sweep_x)
	_flare.visible = peak > 0.001
	_flare.modulate = Color(1, 1, 1, peak)
	# the room flare: the crossing (t2) or, weaker, the passing lineside lamp
	var room := maxf(peak * 0.85, _pass_light(time) * (0.22 if rm else 0.34))
	_rflare_k.visible = room > 0.001
	_rflare_a.visible = room > 0.001
	_rflare_k.modulate = Color(1, 1, 1, room)
	_rflare_a.modulate = Color(1, 1, 1, room)


# ------------------------------------------------------------------ exterior drawing
func _draw_poles() -> void:
	if _pole_tex == null:
		return
	var time := t
	var side_a := time >= CUT
	var tr := _travel(time)
	var clip := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	var pw := _pole_tex.get_width()
	var xs: Array = []
	var base := float(SPEED["pole"]) * tr
	var span := POLE_SPACING
	var first := floori((base - 40.0) / span) - 1
	for k in range(first, first + 4):
		var x := float(k) * span - base + 380.0
		if side_a:
			x = 2.0 * 320.0 - x - pw
		xs.append(roundf(x))
	xs.sort()
	var wire_col := Color("#2a3646")
	for i in xs.size() - 1:
		for ins in POLE_INS:
			var a := Vector2(xs[i] + ins[0], POLE_Y + ins[1])
			var b := Vector2(xs[i + 1] + ins[0], POLE_Y + ins[1])
			FX.wire(_poles, a, b, 15.0 + float(ins[1] - 19) * 0.3, wire_col, clip)
	for x in xs:
		if x > clip.position.x - pw and x < clip.end.x:
			_poles.draw_texture(_pole_tex, Vector2(x, POLE_Y))


## screen x of a strip-local x (tileable 640 px strips scrolled by `off`, mirrored on the A side)
static func _strip_x(sx: float, off: float, flipped: bool) -> float:
	var u := fposmod(sx - floorf(off), 640.0)
	if flipped:
		u = float(EXT.size.x) - 1.0 - u
	return float(EXT.position.x) + u


## the searchlight of a watchtower on the Line: a slow sweeping cone over the strip, its pool on the snow
func _draw_beams() -> void:
	var time := t
	if time >= T4_START:
		return
	var side_a := time >= CUT
	var key := "towers_su" if side_a else "towers_de"
	var towers: Array = _layout.get(key, [])
	var off := float(SPEED["far"]) * _travel(time) + (37.0 if side_a else 0.0)
	var clip := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	var col := Color(0.62, 0.68, 0.78, 0.16)
	var pool := Color(0.55, 0.6, 0.7, 0.22)
	for i in towers.size():
		var tw: Array = towers[i]
		var x0 := _strip_x(float(tw[0]), off, side_a)
		var y0 := 136.0 + float(tw[1]) + (ext.position.y if ext else 0.0)
		if x0 < clip.position.x - 60 or x0 > clip.end.x + 60:
			continue
		var sweep := sin(time * 0.55 * _motion() + float(i) * 2.1) * 0.9
		var gy := 186.0
		var gx := x0 + tan(sweep) * (gy - y0) * 1.6
		var steps := int(gy - y0)
		for k in range(steps):
			var u := float(k) / float(maxi(1, steps))
			var cx := lerpf(x0, gx, u)
			var hw := 0.5 + u * 4.5
			var y := roundf(y0 + k)
			var r := Rect2(Vector2(roundf(cx - hw), y), Vector2(maxf(1.0, roundf(hw * 2.0)), 1))
			if clip.encloses(r):
				_beams.draw_rect(r, col)
		# the lit pool on the snow (dithered ellipse)
		for dy in range(-2, 3):
			for dx in range(-9, 10):
				var e := (dx * dx) / 81.0 + (dy * dy) / 5.0
				if e <= 1.0 and ((dx + dy) & 1) == 0:
					var pp := Vector2(roundf(gx) + dx, roundf(gy) + dy)
					if clip.has_point(pp):
						_beams.draw_rect(Rect2(pp, Vector2.ONE), pool)


## a lineside lamp on its post rushing past (near-layer speed) with its halo; its light flicks through the car
func _draw_passer() -> void:
	var time := t
	if time >= T4_START or (time > 7.8 and time < 10.2):
		return
	var side_a := time >= CUT
	var tc: float = PASS_LAMP["a"] if side_a else PASS_LAMP["k"]
	var v := float(SPEED["pole"]) * _motion() * 1.15
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	var x := cx - (time - tc) * v if not side_a else cx + (time - tc) * v
	var clip := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	if x < clip.position.x - 30 or x > clip.end.x + 30:
		return
	var post := Color("#0c111c")
	var top := 112.0
	for y in range(int(top), int(clip.end.y)):
		var r := Rect2(Vector2(roundf(x), y), Vector2(3, 1))
		if clip.encloses(r):
			_passer.draw_rect(r, post)
	var head := Rect2(Vector2(roundf(x) - 3, top - 3), Vector2(9, 3))
	if clip.encloses(head):
		_passer.draw_rect(head, post)
	# the lamp and a dithered warm halo (motion-streaked sideways)
	for dy in range(-7, 8):
		for dx in range(-16, 17):
			var e := (dx * dx) / 256.0 + (dy * dy) / 49.0
			if e > 1.0:
				continue
			var pp := Vector2(roundf(x) + 1 + dx, top + 1 + dy)
			if not clip.has_point(pp):
				continue
			var lv := 1.0 - e
			var th := (float((int(pp.x) % 4) * 4 + (int(pp.y) % 4)) + 0.5) / 16.0
			if lv * 0.9 > th:
				_passer.draw_rect(Rect2(pp, Vector2.ONE), Color(0.93, 0.72, 0.47, 0.55 * lv + 0.15))
	_passer.draw_rect(Rect2(Vector2(roundf(x), top), Vector2(3, 2)), Color("#fce2b0"))


# ------------------------------------------------------------------ dawn (t4)
## train fronts over the shot (x of the leading buffer): Konrad's from the west, Alexei's from the east; they
## meet over the middle arch at T_MEET and pass each other, slowing a little toward the city.
const T_MEET := 21.6
const MEET_X := 320.0


func _train_fronts(time: float) -> Vector2:
	var v0 := 44.0
	var v1 := 33.0
	var t0 := DAWN_IN[0] - 0.6
	var u := clampf((time - t0) / (DUR - t0), 0.0, 1.0)
	# distance travelled since t0 for a speed falling linearly from v0 to v1
	var total := DUR - t0
	var s := (v0 * u + (v1 - v0) * u * u * 0.5) * total
	var um := (T_MEET - t0) / total
	var sm := (v0 * um + (v1 - v0) * um * um * 0.5) * total
	var de := MEET_X + (s - sm)
	var su := MEET_X - (s - sm)
	return Vector2(de, su)


func _apply_dawn(time: float, _rm: bool) -> void:
	if not dawn.visible:
		return
	var f := _train_fronts(time)
	var lde: Dictionary = _layout.get("train_de", {})
	var lsu: Dictionary = _layout.get("train_su", {})
	if _train_de.texture:
		_train_de.position = Vector2(roundf(f.x - float(lde.get("front", _train_de.texture.get_width()))),
			float(lde.get("y", 153)))
		_train_de.frame = int(floor(time * 4.0)) % 2      # pennants flutter
	if _train_su.texture:
		_train_su.position = Vector2(roundf(f.y - float(lsu.get("front", 0))), float(lsu.get("y", 163)))
		_train_su.frame = 0
	_dawn_glow.modulate = Color(1, 1, 1, ramp01(time, 18.0, 24.0))
	_city_smoke.queue_redraw()
	_smoke.queue_redraw()
	_lamps.queue_redraw()
	_life.queue_redraw()
	_bank.queue_redraw()


var _smoke_atlas: Texture2D = null
func _smoke_tex() -> Texture2D:
	if _smoke_atlas == null:
		_smoke_atlas = tex("trains/smoke.png")
	return _smoke_atlas


## steam puffs from both chimneys: spawned at fixed times, each puff a pure function of its age; they trail
## behind their engine, rise and spread, and drift east on the morning air -> the two plumes run together
func _draw_smoke() -> void:
	var atlas: Texture2D = _smoke_tex()
	if atlas == null:
		return
	var n := int(_layout.get("smoke", {}).get("frames", 8))
	var fw := atlas.get_width() / n
	var fh := atlas.get_height()
	var life := 5.6
	var every := 0.24
	var t_first := DAWN_IN[0] - 2.4
	for side in [0, 1]:
		var L: Dictionary = _layout.get("train_de" if side == 0 else "train_su", {})
		var ch: Array = L.get("chimney", [0, 0])
		var front := float(L.get("front", 0))
		var top := float(L.get("y", 160))
		var k0 := maxi(0, int(floor((t - life - t_first) / every)))
		var k1 := int(floor((t - t_first) / every))
		for k in range(k0, k1 + 1):
			var born := t_first + k * every + (0.11 if side == 1 else 0.0)
			var age := t - born
			if age < 0.0 or age > life:
				continue
			var fr := _train_fronts(born)
			var cx := (fr.x - front + float(ch[0])) if side == 0 else (fr.y - front + float(ch[0]))
			var dirx := -1.0 if side == 0 else 1.0                 # the plume trails behind the engine
			var jit := _h(k * 3 + side * 101, 57)                  # each puff a little different
			var trail := dirx * (5.0 * age) + 5.5 * age + jit * 2.0  # ... and drifts east
			var rise := (13.0 + jit * 2.0) * age - 0.85 * age * age
			var p := Vector2(cx + trail - fw * 0.5, top + float(ch[1]) - 4.0 - rise - fh * 0.5)
			var fi := clampi(int(age / life * n), 0, n - 1)
			_smoke.draw_texture_rect_region(atlas, Rect2(p.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh))


## thin chimney smoke over the old town: still air, the columns rise straight and lean east at the top
func _draw_city_smoke() -> void:
	var atlas: Texture2D = _smoke_tex()
	if atlas == null:
		return
	var n := int(_layout.get("smoke", {}).get("frames", 8))
	var fw := atlas.get_width() / n
	var fh := atlas.get_height()
	var chims: Array = _layout.get("chimneys", [])
	var sp := 0.6 if reduced_motion() else 1.0
	for i in chims.size():
		var c: Array = chims[i]
		for k in range(6):
			var age := fposmod(t * sp + float(k) * 1.1 + float(i) * 0.37, 6.6)
			var p := Vector2(float(c[0]) + age * age * 0.35 - fw * 0.5, float(c[1]) - age * 4.2 - fh * 0.5)
			var fi := clampi(int(age / 6.6 * 3.0), 0, 2)
			_city_smoke.draw_texture_rect_region(atlas, Rect2(p.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh),
				Color(1, 1, 1, 0.55))


## headlamps of both engines (additive): a hot core and a short dithered beam ahead
func _draw_lamps() -> void:
	var f := _train_fronts(t)
	for side in [0, 1]:
		var L: Dictionary = _layout.get("train_de" if side == 0 else "train_su", {})
		var hl: Array = L.get("headlamp", [0, 12])
		var front := float(L.get("front", 0))
		var x := ((f.x if side == 0 else f.y) - front + float(hl[0]))
		var y := float(L.get("y", 160)) + float(hl[1])
		var dir := 1.0 if side == 0 else -1.0
		for k in range(1, 14):
			for dy in range(-1, 2):
				var th := (float(((k + 3) % 4) * 4 + ((dy + 5) % 4)) + 0.5) / 16.0
				if (1.0 - float(k) / 14.0) * 0.8 > th:
					_lamps.draw_rect(Rect2(Vector2(roundf(x + dir * k), y + dy), Vector2.ONE), Color(0.35, 0.3, 0.22))
		_lamps.draw_rect(Rect2(Vector2(roundf(x) - 1, y - 1), Vector2(3, 3)), Color(0.45, 0.4, 0.3))


## river glints, the crows lifting off the ice at the whistle, the woman with the sled on the bank path
func _draw_life() -> void:
	var glints: Array = _layout.get("glints", [])
	var step := int(floor(t * 6.0))
	for i in glints.size():
		var g: Array = glints[i]
		if (_h(step + i * 7, 41) + 1.0) * 0.5 > 0.55:
			_life.draw_rect(Rect2(float(g[0]), float(g[1]), float(g[2]) if g.size() > 2 else 2.0, 1),
				Color("#e8dcd6") if i % 3 == 0 else Color("#a1aab7"))
	# crows: sitting on the ice, they lift at the whistle and beat away west over the bridge
	var crow := Color("#0c111c")
	for b in 9:
		var rest := Vector2(392.0 + float((b * 37) % 70), 266.0 + float((b * 13) % 9))
		var lift := 18.7 + float(b) * 0.09 + float((b * 7) % 5) * 0.05
		var bt := t - lift
		var p := rest
		var up := false
		if bt > 0.0:
			p = rest + Vector2(-bt * (34.0 + b * 2.0), -bt * (22.0 - bt * 1.6) + sin(bt * 3.0 + b) * 2.0)
			up = int(floor(bt * 8.0 + b)) % 2 == 0
		if p.y < 40.0 or p.x < -10.0:
			continue
		var q := p.round()
		_life.draw_rect(Rect2(q, Vector2(2, 1)), crow)
		if bt > 0.0:
			_life.draw_rect(Rect2(q + Vector2(-2, -1 if up else 1), Vector2(2, 1)), crow)
			_life.draw_rect(Rect2(q + Vector2(2, -1 if up else 1), Vector2(2, 1)), crow)
		else:
			_life.draw_rect(Rect2(q + Vector2(0, -1), Vector2(1, 1)), crow)


## the woman pulling a sled with a milk can along the promenade of the near bank (in front of its fence)
func _draw_bank() -> void:
	if _walker_tex == null:
		return
	var W: Dictionary = _layout.get("walker", {})
	var n := int(W.get("frames", 6))
	var fw := _walker_tex.get_width() / n
	var fh := _walker_tex.get_height()
	var x := 120.0 + (t - DAWN_IN[0]) * 8.0 * _motion()
	var fi := int(floor((t - DAWN_IN[0]) * 6.0 * _motion())) % n
	_bank.draw_texture_rect_region(_walker_tex, Rect2(Vector2(roundf(x), float(W.get("y", 277))), Vector2(fw, fh)),
		Rect2(fi * fw, 0, fw, fh))
