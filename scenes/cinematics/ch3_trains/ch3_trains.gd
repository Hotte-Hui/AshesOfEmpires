extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## LS_C3_Trains (36 s, round 10 rework) — the Chapter 2 -> 3 character switch „Konrads Zugfenster -> Alexeis
## Zugfenster“ (STORY_BIBLE §6, C3_DESIGN §2.9).  Art: tools/pixelgen/env_veltrava_cine*.py -> assets/cinematics/ch3/trains/.
##   t1  0-8 s     night, the German delegation's saloon car: Konrad at the window, the reading lamp, his hand at
##                 the cup; outside the western farmland (a village with its steeple, a car on the road), poles and
##                 wires, the floodlit Line with a searchlight; a lineside lamp and a small station rush past
##                 without a stop (their light sweeps through the car), a signal shows green
##   t2  8-10 s    match cut through the window frame: a level crossing (red lamps blinking) passes, its floodlight
##                 floods the glass, the room behind changes (glass opening and iron sash are identical in both cars)
##   t3  10-18 s   the Soviet car: Alexei at the window, his hand at the tea glass (the spoon rattles with every
##                 joint); outside the eastern land (izbas with smoking chimneys, the onion dome), a truss bridge over
##                 a frozen river thunders past, the Line from the other side
##   t3b 18-23.5   NEW: the Line before dawn from high above: the floodlit double fence runs to the horizon where the
##                 Free City glows; Konrad's train left of it, Alexei's right, both racing toward the same light
##   t4  23.5-36   dawn over Veltrava (crane shot): low on the river (ice, floes, crows, the arches, the woman with the
##                 sled on the bank), the two trains meet over the middle arch, whistles, the crows lift; the camera
##                 rises and the city stands over the bridge: palais dome in the first sun, towers, the station, the
##                 old town putting out its lights, chimney smoke, a tram on the quay, gulls
## Inner lines (configure(ctx).flags): Konrad evidence > suspicion > base, Alexei irina > secrecy > base,
## then cin.c3.trains.place.  Reduced motion: half the travel speed, no jolts/sway, a soft flare, fewer flakes, no
## crane (t4 holds the middle view), gentler dissolves.

const FX := preload("res://scenes/cinematics/ch3_common/pixel_fx.gd")

## glass opening / exterior box — must match env_veltrava_cine.py (GLASS, EXT; checked by the test
## against assets/cinematics/ch3/layout.json)
const GLASS := Rect2i(172, 84, 296, 142)
const EXT := Rect2i(164, 76, 312, 158)
const CUT := 9.0                      # the room changes here (inside the flare)
const T1_END := 8.0
const T3_START := 10.0
const T3_END := 18.0                  # the compartments end (t3b begins)
const T4_START := 23.5
const DUR := 36.0
const SHOTS := [["t1", 0.0, 8.0], ["t2", 8.0, 10.0], ["t3", 10.0, 18.0], ["t3b", 18.0, 23.5], ["t4", 23.5, 36.0]]
## parallax speeds (px/s at full motion): far fence, plain, embankment, telegraph poles
const SPEED := {"far": 5.0, "mid": 26.0, "near": 150.0, "pole": 250.0}
const POLE_SPACING := 360.0
const POLE_INS := [[1, 19], [14, 19], [3, 31], [12, 31]]   # insulator tops, local to the pole sprite
const POLE_Y := 74
## rail joints: period and phase of the double knock for each car (the bed sounds are cut to the same beat)
const JOINT := {"k": [0.3, 1.55], "a": [9.4, 1.8]}
## a lineside lamp passing the window (time of passing the glass centre) in each car
const PASS_LAMP := {"k": 2.7, "a": 15.3}
## a small station rushing past Konrad's car (time its centre passes the glass centre), its speed
const PASS_STATION := 5.4
const STATION_V := 270.0
## the truss bridge over a frozen river under Alexei's car: times its entry / exit portal passes the glass centre
## (world-locked: every layer sees the bridge's span at its own depth; AD round 2: 2 s, the river fits under it)
const TRUSS := [11.7, 13.7]
const TRUSS_V := 320.0
## signals showing green, passing the glass centre
const SIGNALS := {"k": 7.15, "a": 16.7}
## dissolves t3 -> t3b and t3b -> t4
const LINE_IN := [17.3, 18.3]
const LINE_IN_RM := [16.9, 18.6]
const DAWN_IN := [23.0, 24.0]
const DAWN_IN_RM := [22.6, 24.4]
## t4 crane (absolute times), and the fixed crane position with reduced motion
const CRANE := [28.7, 34.6]
const CRANE_RM := 0.55

var line_konrad := "cin.c3.trains.konrad.base"
var line_alexei := "cin.c3.trains.alexei.base"
const LINE_PLACE := "cin.c3.trains.place"

var win: Node2D
var ext: Node2D
var room_k: Node2D
var room_a: Node2D
var line: Node2D
var dawn: Node2D
var _sky: Sprite2D
var _far_de: Sprite2D
var _far_su: Sprite2D
var _mid_de: Sprite2D
var _mid_su: Sprite2D
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
var _events: Node2D
var _station: Sprite2D
var _river: Node2D                 # AD round 2: the river in perspective (rows scrolled at their own depth)
var _river_tex: Texture2D
var _river_obj: Texture2D
var _riv: Dictionary = {}
var _near_b: Sprite2D              # the embankment right of the bridge gap (the near strip shows on both sides)
var _patch_a2: Sprite2D
var _midlife: Node2D
var _roomlife_k: Node2D
var _roomlife_a: Node2D
var _layout: Dictionary = {}
# t3b
var _line_mats: Array = []
var _l3_trains: Node2D
var _l3_search: Node2D
var _l3_snow: Node2D
# t4
var _dawn_mats: Array = []
var _d4: Dictionary = {}
var _p_sky: Sprite2D
var _p_sun: Sprite2D
var _p_city: Sprite2D
var _p_dome: Sprite2D
var _p_bridge: Sprite2D
var _p_parapet: Sprite2D
var _p_lampglow: Sprite2D
var _p_bank: Sprite2D
var _citylife: Node2D
var _riverlife: Node2D
var _train_de: Sprite2D
var _train_su: Sprite2D
var _smoke: Node2D
var _lamps: Node2D
var _bank: Node2D
var _tram_tex: Texture2D
var _gull_tex: Texture2D
var _chim_tex: Texture2D
var _d4_snow: Node2D
var _off := {"sky": 0.0, "city": 0.0, "bridge": 0.0, "bank": 0.0}
var _people: Array = []          # the extras of t4 (figures stream sheets, placed per plane by layout.json)


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
		{"t": PASS_STATION - 1.0, "bed": "c3cine_station_rush", "db": -7.0},  # a station rushes past, its bell
		{"t": 8.05, "bed": "c3cine_crossing", "db": -5.0},                 # bell + rush of the level crossing
		{"t": CUT, "bed": "c3cine_ride_su", "db": -4.0},                   # the Soviet car: rattlier, the spoon
		{"t": 10.5, "say": line_alexei, "dur": 6.8},
		{"t": TRUSS[0] - 0.15, "bed": "c3cine_truss", "db": -6.0},         # the girders of the river bridge
		{"t": PASS_LAMP["a"] - 0.5, "sfx": "c3cine_pass", "db": -13.0, "pv": 0.04},
		{"t": 17.3, "bed": "c3cine_line_night", "db": -5.0},               # wind over the Line, two trains far off
		{"t": 19.2, "music": "mus_veltrava", "fade": 6.0},
		{"t": 23.1, "bed": "c3cine_bridge", "db": -3.0},                   # two trains on the stone bridge
		{"t": 27.6, "bed": "cine_a1m1_whistle_far", "db": -6.0},           # Alexei's engine (the Karsk whistle)
		{"t": 28.9, "bed": "c3cine_whistle_de", "db": -9.0},               # Konrad's engine answers, lower
		{"t": 29.6, "say": LINE_PLACE, "dur": 5.2},
		{"t": 30.6, "bed": "c3cine_city_morning", "db": -8.0},             # bells and a tram in the waking city
	]
	return c


# ------------------------------------------------------------------ build
func _build() -> void:
	var p := ASSETS + "layout.json"
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			_layout = d.get("trains", {})
	_d4 = _layout.get("d4", {})
	win = group("Window")
	ext = group("Exterior", win)
	var ex := Vector2(EXT.position)
	_sky = sprite("trains/ext_sky.png", ex, ext)
	_far_de = strip("trains/ext_far_de.png", Vector2(ex.x, 136), EXT.size.x, ext)
	_far_su = strip("trains/ext_far_su.png", Vector2(ex.x, 136), EXT.size.x, ext)
	_far_su.flip_h = true
	_beams = _drawer("Searchlight", ext, _draw_beams)
	_beams.material = additive()
	# the villages' strips are painted for rows mid_y0.. (AD round 2: they were placed 32 px too low, behind the
	# embankment and the sill, so only roof tips showed)
	var mid_y := float(_layout.get("mid_y0", 150))
	_mid_de = strip("trains/ext_mid_de.png", Vector2(ex.x, mid_y), EXT.size.x, ext)
	_mid_su = strip("trains/ext_mid_su.png", Vector2(ex.x, mid_y), EXT.size.x, ext)
	_midlife = _drawer("MidLife", ext, _draw_midlife)
	_snow_far = FX.new()
	_snow_far.name = "SnowFar"
	ext.add_child(_snow_far)
	_riv = _layout.get("river", {})
	_river_tex = tex("trains/pass_river.png")
	_river_obj = tex("trains/pass_river_obj.png")
	_river = _drawer("River", ext, _draw_river)
	_near = strip("trains/ext_near.png", Vector2(ex.x, 212), EXT.size.x, ext)
	_near_b = strip("trains/ext_near.png", Vector2(ex.x, 212), EXT.size.x, ext)
	_near_b.visible = false
	_patch_k = sprite("trains/patch_warm.png", Vector2.ZERO, ext, 1, true)
	_patch_a = sprite("trains/patch_cold.png", Vector2.ZERO, ext, 1, true)
	_patch_a2 = sprite("trains/patch_cold.png", Vector2.ZERO, ext, 1, true)
	for ps in [_patch_a, _patch_a2]:
		ps.region_enabled = true
		ps.region_rect = Rect2(0, 0, VIEW.x, VIEW.y)
	_patch_a2.visible = false
	_station = sprite("trains/pass_station.png", Vector2(0, EXT.position.y), ext)
	_poles = _drawer("Poles", ext, _draw_poles)
	_pole_tex = tex("trains/pole.png")
	_passer = _drawer("PassingLamp", ext, _draw_passer)
	_events = _drawer("Events", ext, _draw_events)
	_snow_near = FX.new()
	_snow_near.name = "SnowNear"
	ext.add_child(_snow_near)
	_sweep = sprite("trains/sweep.png", Vector2(0, EXT.position.y), ext, 1, true)
	_flare = sprite("trains/flare.png", Vector2.ZERO, ext, 1, true)
	room_k = group("RoomKonrad", win)
	sprite("trains/refl_konrad.png", Vector2.ZERO, room_k, 1, true)
	sprite("trains/int_konrad.png", Vector2.ZERO, room_k)
	_roomlife_k = _drawer("RoomLifeK", room_k, _draw_roomlife_k)
	_fig_k = sprite("trains/fig_konrad.png", Vector2.ZERO, room_k, 4)
	_glow_k = sprite("trains/glow_lamp.png", Vector2.ZERO, room_k, 1, true)
	_rflare_k = sprite("trains/roomflare_k.png", Vector2.ZERO, room_k, 1, true)
	room_a = group("RoomAlexei", win)
	sprite("trains/refl_alexei.png", Vector2.ZERO, room_a, 1, true)
	sprite("trains/int_alexei.png", Vector2.ZERO, room_a)
	_spoon = sprite("trains/spoon.png", Vector2.ZERO, room_a, 2)
	_roomlife_a = _drawer("RoomLifeA", room_a, _draw_roomlife_a)
	_fig_a = sprite("trains/fig_alexei.png", Vector2.ZERO, room_a, 4)
	_glow_a = sprite("trains/glow_tea.png", Vector2.ZERO, room_a, 1, true)
	_steam = sprite("trains/steam_tea.png", Vector2.ZERO, room_a, 6)
	_rflare_a = sprite("trains/roomflare_a.png", Vector2.ZERO, room_a, 1, true)
	for pair in [[_fig_k, "fig_konrad"], [_fig_a, "fig_alexei"], [_glow_k, "glow_lamp"], [_glow_a, "glow_tea"],
			[_steam, "steam_tea"], [_sweep, "sweep"], [_spoon, "spoon"]]:
		var v = _layout.get(pair[1])
		if v is Array and v.size() >= 2 and pair[0]:
			(pair[0] as Sprite2D).position = Vector2(float(v[0]), float(v[1]))
	_build_line()
	_build_dawn()
	_setup_snow()


func _build_line() -> void:
	line = group("Line")
	var mat := dissolve_material(false)
	var mat_add := dissolve_material(true)
	_line_mats = [mat, mat_add]
	var bg := sprite("trains/l3_bg.png", Vector2.ZERO, line)
	_l3_trains = _drawer("LineTrains", line, _draw_line_trains)
	var fg := sprite("trains/l3_fg.png", Vector2.ZERO, line)
	var gl := sprite("trains/l3_glow.png", Vector2.ZERO, line)
	_l3_search = _drawer("LineSearch", line, _draw_line_search)
	_l3_snow = FX.new()
	_l3_snow.name = "LineSnow"
	line.add_child(_l3_snow)
	for n in [bg, _l3_trains, fg, _l3_snow]:
		(n as CanvasItem).material = mat
	for n in [gl, _l3_search]:
		(n as CanvasItem).material = mat_add


func _build_dawn() -> void:
	dawn = group("Dawn")
	var mat := dissolve_material(false)
	var mat_add := dissolve_material(true)
	_dawn_mats = [mat, mat_add]
	_p_sky = sprite("trains/d4_sky.png", Vector2.ZERO, dawn)
	_p_sun = sprite("trains/d4_sun_glow.png", Vector2.ZERO, dawn)
	_p_city = sprite("trains/d4_city.png", Vector2.ZERO, dawn)
	_p_dome = sprite("trains/d4_dome_glow.png", Vector2.ZERO, dawn)
	_citylife = _drawer("CityLife", dawn, _draw_citylife)
	_p_bridge = sprite("trains/d4_bridge.png", Vector2.ZERO, dawn)
	_riverlife = _drawer("RiverLife", dawn, _draw_riverlife)
	_train_de = sprite("trains/train_de.png", Vector2.ZERO, dawn, 1, false, 2)
	_train_su = sprite("trains/train_su.png", Vector2.ZERO, dawn, 1, false, 2)
	_smoke = _drawer("Smoke", dawn, _draw_smoke)
	_p_parapet = sprite("trains/d4_parapet.png", Vector2.ZERO, dawn)
	_lamps = _drawer("Headlamps", dawn, _draw_lamps)
	_p_lampglow = sprite("trains/d4_lamp_glow.png", Vector2.ZERO, dawn)
	_p_bank = sprite("trains/d4_bank.png", Vector2.ZERO, dawn)
	_bank = _drawer("Bank", dawn, _draw_bank)
	_d4_snow = FX.new()
	_d4_snow.name = "DawnSnow"
	dawn.add_child(_d4_snow)
	for n in [_p_sky, _p_city, _citylife, _p_bridge, _riverlife, _train_de, _train_su, _smoke, _p_parapet, _p_bank,
			_bank, _d4_snow]:
		(n as CanvasItem).material = mat
	for n in [_p_sun, _p_dome, _lamps, _p_lampglow]:
		(n as CanvasItem).material = mat_add
	for d in _layout.get("people", []):
		var ptx := tex(str((d as Dictionary).get("tex", "")))
		if ptx:
			_people.append({"tex": ptx, "d": d})
	_tram_tex = tex("trains/d4_tram.png")
	_gull_tex = tex("trains/d4_gull.png")
	_chim_tex = tex("trains/d4_chimney_smoke.png")


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
	_l3_snow.setup_snow(Rect2(0, 40, 640, 280), [
		{"count": int(70 * k), "v": Vector2(4, 14), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 1.5},
		{"count": int(26 * k), "v": Vector2(7, 30), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#a1aab7"), "sway": 2.5}], 3103)
	_d4_snow.setup_snow(Rect2(0, 40, 640, 280), [
		{"count": int(16 * k), "v": Vector2(3, 9), "vjit": 0.4, "size": Vector2(1, 1), "color": Color("#c2c9d2"), "sway": 2.0}], 3104)


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


func _dissolve(time: float, d: Array) -> float:
	return clampf((time - float(d[0])) / (float(d[1]) - float(d[0])), 0.0, 1.0)


func _apply(time: float) -> void:
	if win == null:
		return
	var rm := reduced_motion()
	var side_a := time >= CUT
	var tr := _travel(time)
	var dl: Array = LINE_IN_RM if rm else LINE_IN
	var dd: Array = DAWN_IN_RM if rm else DAWN_IN
	var prog_line := _dissolve(time, dl)
	var prog_dawn := _dissolve(time, dd)
	win.visible = prog_line < 1.0
	room_k.visible = not side_a
	room_a.visible = side_a
	_far_de.visible = not side_a
	_far_su.visible = side_a
	_mid_de.visible = not side_a
	_mid_su.visible = side_a
	_patch_k.visible = not side_a
	_patch_a.visible = side_a
	for pair in [[_far_de, "far"], [_far_su, "far"], [_mid_de, "mid"], [_mid_su, "mid"], [_near, "near"]]:
		var s: Sprite2D = pair[0]
		var off := float(SPEED[pair[1]]) * tr + (37.0 if side_a else 0.0)
		s.flip_h = side_a
		set_scroll(s, off)
	_sky.flip_h = side_a
	_split_near(time, side_a, tr)
	_apply_events(time, side_a)
	# snow streams with the travel direction
	var dir := 1.0 if side_a else -1.0
	for sn in [_snow_far, _snow_near]:
		for f in sn.flakes:
			f["v"].x = absf(f["v"].x) * dir
		sn.set_time(tr + (11.0 if side_a else 0.0))
	_poles.queue_redraw()
	_beams.queue_redraw()
	_passer.queue_redraw()
	_events.queue_redraw()
	_midlife.queue_redraw()
	_roomlife_k.queue_redraw()
	_roomlife_a.queue_redraw()
	# the car rocks: a slow 1 px roll of the landscape in the window, the room knocks over the joints
	var jolt := 0
	var roll := 0.0
	if not rm and time < T3_END:
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
	# lamp / tea glow flicker (subtle, never strobing); passing lights sweep through the room
	var fl := 0.035 * (0.4 if rm else 1.0)
	_glow_k.modulate = Color(1, 1, 1, 0.94 + fl * hnoise(time * 2.7, 7))
	_glow_a.modulate = Color(1, 1, 1, 0.9 + fl * hnoise(time * 2.3, 9))
	if _steam.texture:
		_steam.frame = int(floor(time * (4.0 if rm else 6.0))) % 6
	_apply_flare(time, rm)
	# t3 -> t3b -> t4 dissolves
	line.visible = prog_line > 0.0 and prog_dawn < 1.0
	set_dissolve(_line_mats, prog_line)
	_l3_snow.set_time(time * (0.6 if rm else 1.0))
	_l3_trains.queue_redraw()
	_l3_search.queue_redraw()
	dawn.visible = prog_dawn > 0.0
	set_dissolve(_dawn_mats, prog_dawn)
	_apply_dawn(time, rm)


## 0..1 brightness of the passing lights (lineside lamp, station lamps) inside the car
func _pass_light(time: float) -> float:
	var best := 0.0
	var tc: float = PASS_LAMP["a"] if time >= CUT else PASS_LAMP["k"]
	var span := 0.55 / _motion()
	best = clampf(1.0 - absf(time - tc) / span, 0.0, 1.0)
	if time < CUT:
		for lt in _station_lamp_times():
			best = maxf(best, 0.8 * clampf(1.0 - absf(time - float(lt)) / (0.22 / _motion()), 0.0, 1.0))
	return best


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
	# the room flare: the crossing (t2) or, weaker, the passing lamps
	var room := maxf(peak * 0.85, _pass_light(time) * (0.22 if rm else 0.34))
	_rflare_k.visible = room > 0.001
	_rflare_a.visible = room > 0.001
	_rflare_k.modulate = Color(1, 1, 1, room)
	_rflare_a.modulate = Color(1, 1, 1, room)


# ------------------------------------------------------------------ window events (station, river bridge)
## screen x of the station sprite's left edge (it rushes right -> left past Konrad's window)
func _station_x(time: float) -> float:
	var w := float(_station.texture.get_width()) if _station and _station.texture else 440.0
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	return cx - w * 0.5 - (time - PASS_STATION) * STATION_V * _motion()


func _station_lamp_times() -> Array:
	var out: Array = []
	var lamps: Array = _layout.get("station_lamps", [])
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	var w := float(_station.texture.get_width()) if _station and _station.texture else 440.0
	for lx in lamps:
		# the lamp at sprite x passes the glass centre when _station_x(t) + lx == cx
		out.append(PASS_STATION + (float(lx) - w * 0.5) / (STATION_V * _motion()))
	return out


func _apply_events(time: float, side_a: bool) -> void:
	if _station and _station.texture:
		var sx := _station_x(time)
		_station.visible = not side_a and sx < EXT.end.x and sx + _station.texture.get_width() > EXT.position.x
		_station.position.x = roundf(sx)
	if _river:
		# the frozen river below the truss bridge (drawn in perspective, see _draw_river)
		_river.visible = side_a and time < T3_END
		_river.queue_redraw()


## times the entry / exit portal passes the glass centre: TRUSS at full motion; with reduced motion the slower train
## takes longer over the same bridge (centred on the same moment, so the river under it stays in step)
func _truss_times() -> Vector2:
	var tc := (float(TRUSS[0]) + float(TRUSS[1])) * 0.5
	var h := (float(TRUSS[1]) - float(TRUSS[0])) * 0.5 / _motion()
	return Vector2(tc - h, tc + h)


## screen x range [exit end, entry end] of the truss bridge at a layer moving v px/s on Alexei's side (content runs
## right): the bridge is world-locked, its portals pass the glass centre at _truss_times() (entry, exit)
func _bridge_gap(time: float, v: float) -> Vector2:
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	var tt := _truss_times()
	return Vector2(roundf(cx + (time - tt.y) * v), roundf(cx + (time - tt.x) * v))


## AD round 2: while the car is on the bridge there is no embankment below the window: the near strip and the light
## of the car's windows on its snow show only outside the bridge's span at the near layer's depth (left and right
## pieces: at this depth the bridge is shorter than the window)
func _split_near(time: float, side_a: bool, tr: float) -> void:
	var x0 := float(EXT.position.x)
	var x1 := float(EXT.end.x)
	var g := Vector2(x1 + 1.0, x1 + 1.0)
	if side_a:
		g = _bridge_gap(time, float(SPEED["near"]) * _motion())
	var off := float(SPEED["near"]) * tr + (37.0 if side_a else 0.0)
	var tw := float(_near.texture.get_width()) if _near and _near.texture else 640.0
	var rx := fposmod(floorf(off), tw)
	_near_b.flip_h = side_a
	_piece(_near, x0, minf(g.x, x1), rx, side_a, true)
	_piece(_near_b, maxf(g.y, x0), x1, rx, side_a, true)
	if side_a:
		_piece(_patch_a, x0, minf(g.x, x1), 0.0, false, false)
		_piece(_patch_a2, maxf(g.y, x0), x1, 0.0, false, false)
	else:
		_patch_a.visible = false
		_patch_a2.visible = false


## show screen columns [a, b) of a strip sprite (scroll: region offset rx of the full-window strip, mirrored on the A
## side) or of a full-frame static sprite (scroll false)
func _piece(s: Sprite2D, a: float, b: float, rx: float, flipped: bool, scroll: bool) -> void:
	if s == null or s.texture == null:
		return
	a = roundf(a)
	b = roundf(b)
	if b - a < 1.0:
		s.visible = false
		return
	s.visible = true
	var r := s.region_rect
	if scroll:
		var i0 := a - float(EXT.position.x)
		var i1 := b - float(EXT.position.x)
		r.position.x = fposmod(rx + (float(EXT.size.x) - i1 if flipped else i0), float(s.texture.get_width()))
	else:
		r.position.x = a
	r.size.x = b - a
	s.region_rect = r
	s.position.x = a


## AD round 2: the frozen river from the bridge, in perspective.  pass_river.png is the ground seen with the river's
## centre under the glass centre; every row slides right at the speed of its own depth (k = 1 at the bottom row), so
## the valley swings past like a wiper and enters at the window's edge -- no pop, no seams.  Rows above the bend share
## the bend's depth (the willows stand there); upright things on the ice are drawn at the depth of their foot.
func _river_k(y: float) -> float:
	var hy := float(_riv.get("hy", 188.0))
	var bot := float(_riv.get("bot", 229.0))
	return (maxf(y, float(_riv.get("bend", 203))) + 0.5 - hy) / (bot + 0.5 - hy)


func _river_shift(time: float) -> float:
	return (time - (float(TRUSS[0]) + float(TRUSS[1])) * 0.5) * float(_riv.get("v", 140.0)) * _motion()


func _draw_river() -> void:
	var time := t
	if _river_tex == null or time < CUT or time >= T3_END:
		return
	var clip := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	var s := _river_shift(time)
	var y0 := int(_riv.get("y0", 189))
	var icx := float(_riv.get("cx", 260))
	var half := float(_riv.get("half", 166))
	var tw := float(_river_tex.get_width())
	for r in _river_tex.get_height():
		var y := float(y0 + r)
		var k := _river_k(y)
		var off := cx - icx + roundf(s * k)
		var a := maxf(maxf(0.0, roundf(icx - half * k) - 2.0) + off, clip.position.x)
		var b := minf(minf(tw, roundf(icx + half * k) + 2.0) + off, clip.end.x)
		if b > a:
			_river.draw_texture_rect_region(_river_tex, Rect2(a, y, b - a, 1), Rect2(a - off, r, b - a, 1))
	if _river_obj == null:
		return
	var hy := float(_riv.get("hy", 188.0))
	var bot := float(_riv.get("bot", 229.0))
	for o in _riv.get("objs", []):
		var dd := float(o[5])
		var foot := floorf(hy - 0.5 + (bot + 0.5 - hy) / dd)
		var k := _river_k(foot)
		var cw := float(o[2])
		var ch := float(o[3])
		var x := roundf(cx + float(o[4]) / dd + roundf(s * k) - cw * 0.5)
		_blit(_river, _river_obj, Rect2(x, foot - ch + 1.0, cw, ch), Rect2(float(o[1]), 0, cw, ch), clip)


static func _blit(ci: CanvasItem, tx: Texture2D, dst: Rect2, src: Rect2, clip: Rect2) -> void:
	var c := dst.intersection(clip)
	if c.size.x < 1.0 or c.size.y < 1.0:
		return
	ci.draw_texture_rect_region(tx, c, Rect2(src.position + (c.position - dst.position), c.size))


## the lineside events drawn at runtime: signals (green), the level crossing's red lamps, the truss girders
func _draw_events() -> void:
	var time := t
	if time >= T3_END:
		return
	var clip := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	var v := float(SPEED["pole"]) * _motion()
	var dark := Color("#0c111c")
	# signals: a lattice mast with a green lamp (and its halo) rushing past
	var side_a := time >= CUT
	var ts: float = SIGNALS["a"] if side_a else SIGNALS["k"]
	var x := cx - (time - ts) * v if not side_a else cx + (time - ts) * v
	if x > clip.position.x - 30 and x < clip.end.x + 30:
		for y in range(98, int(clip.end.y)):
			var r := Rect2(Vector2(roundf(x), y), Vector2(2, 1))
			if clip.encloses(r):
				_events.draw_rect(r, dark)
		var head := Rect2(Vector2(roundf(x) - 3, 92), Vector2(8, 10))
		if clip.encloses(head):
			_events.draw_rect(head, dark)
			_events.draw_rect(Rect2(head.position + Vector2(2, 2), Vector2(3, 3)), Color("#2b4541"))
			_events.draw_rect(Rect2(head.position + Vector2(2, 6), Vector2(3, 3)), Color("#7ce0a8"))
			_events.draw_rect(Rect2(head.position + Vector2(3, 7), Vector2(1, 1)), Color("#e6fff0"))
		_halo(_events, Vector2(roundf(x) + 1, 99), 9, Color(0.45, 0.95, 0.65, 0.5), clip)
	# the level crossing (t2): two red lamps on a post with the cross sign, blinking alternately
	if time > 7.6 and time < 9.6:
		var xc := cx - (time - 8.75) * v if time < CUT else cx + (time - 9.2) * v
		if xc > clip.position.x - 40 and xc < clip.end.x + 40:
			for y in range(118, int(clip.end.y)):
				var r := Rect2(Vector2(roundf(xc), y), Vector2(2, 1))
				if clip.encloses(r):
					_events.draw_rect(r, dark)
			var on := int(floor(time * 3.0)) % 2
			for k in 2:
				var lp := Vector2(roundf(xc) - 6 + k * 10, 126)
				if clip.has_point(lp):
					var lit := (k == on)
					_events.draw_rect(Rect2(lp, Vector2(3, 3)), Color("#c8503c") if lit else Color("#4a1712"))
					if lit:
						_halo(_events, lp + Vector2(1, 1), 8, Color(1.0, 0.35, 0.25, 0.55), clip)
			# the cross sign
			FX.line(_events, Vector2(roundf(xc) - 7, 108), Vector2(roundf(xc) + 9, 116), Color("#c2c9d2"))
			FX.line(_events, Vector2(roundf(xc) - 7, 116), Vector2(roundf(xc) + 9, 108), Color("#c2c9d2"))
	# the truss bridge thunders past Alexei's window.  AD round 2: world-locked -- the entry portal sweeps in from the
	# window's edge (it no longer pops in over the whole glass), ten bays, inclined end posts, the exit portal leaves
	if side_a:
		var gap := _bridge_gap(time, TRUSS_V * _motion())
		if gap.y > clip.position.x and gap.x < clip.end.x:
			_draw_truss(gap, clip)


## the girders between the exit end gap.x and the entry end gap.y (screen x), clipped to the window
func _draw_truss(gap: Vector2, clip: Rect2) -> void:
	var steel := Color("#15171c")
	var lit := Color("#3a4859")
	var top_y := float(clip.position.y) + 4.0
	var bot_y := float(clip.end.y) - 10.0
	var n := 13
	var bay := (gap.y - gap.x) / float(n)
	var lo := maxf(gap.x - 3.0, clip.position.x)
	var hi := minf(gap.y + 3.0, clip.end.x)
	# chords: the bottom chord runs the whole bridge, the top chord stops a bay short of each portal
	_hrect(Rect2(gap.x, bot_y, gap.y - gap.x, 10), steel, clip)
	_hrect(Rect2(gap.x, bot_y, gap.y - gap.x, 1), lit, clip)
	_hrect(Rect2(gap.x + bay, top_y - 4, gap.y - gap.x - 2.0 * bay, 6), steel, clip)
	_hrect(Rect2(gap.x + bay, top_y + 2, gap.y - gap.x - 2.0 * bay, 1), lit, clip)
	for i in range(0, n + 1):
		var bx := roundf(gap.x + float(i) * bay)
		if bx < clip.position.x - bay - 4.0 or bx > clip.end.x + bay + 4.0:
			continue
		if i == 0 or i == n:
			# the inclined end post of the portal: from the bearing up to the first panel point of the top chord
			var tx := roundf(bx + (bay if i == 0 else -bay))
			for w in 5:
				_seg(Vector2(bx + w - 2, bot_y), Vector2(tx + w - 2, top_y - 3), steel, lo, hi)
			var e := 2.0 if i == 0 else -2.0
			_seg(Vector2(bx + e, bot_y), Vector2(tx + e, top_y - 3), lit, lo, hi)
			continue
		for w in 4:
			_seg(Vector2(bx + w - 1, top_y), Vector2(bx + w - 1, bot_y), steel, lo, hi)
		_seg(Vector2(bx + 2, top_y), Vector2(bx + 2, bot_y), lit, lo, hi)
		if i < n - 1:
			var nx := roundf(gap.x + float(i + 1) * bay)
			var mx := roundf((bx + nx) * 0.5)
			for w in 3:
				_seg(Vector2(bx + w, top_y), Vector2(mx + w, bot_y), steel, lo, hi)
				_seg(Vector2(nx + w - 2, top_y), Vector2(mx + w - 2, bot_y), steel, lo, hi)
	# rivets along the bottom chord catching the lamp light of the car (they travel with the bridge)
	var rx := gap.x + 4.0
	while rx < gap.y - 2.0:
		if rx >= clip.position.x and rx < clip.end.x:
			_events.draw_rect(Rect2(roundf(rx), bot_y + 4, 1, 1), lit)
		rx += 9.0


func _hrect(r: Rect2, col: Color, clip: Rect2) -> void:
	var c := Rect2(r.position.round(), r.size.round()).intersection(clip)
	if c.size.x >= 1.0 and c.size.y >= 1.0:
		_events.draw_rect(c, col)


## a Bresenham segment clipped to lo <= x < hi (the bridge's span inside the window)
func _seg(a: Vector2, b: Vector2, col: Color, lo: float, hi: float) -> void:
	if a.x > b.x:
		var tmp := a
		a = b
		b = tmp
	if b.x < lo or a.x >= hi:
		return
	if absf(b.x - a.x) < 0.5:
		FX.line(_events, a, b, col)
		return
	var ta := clampf((lo - a.x) / (b.x - a.x), 0.0, 1.0)
	var tb := clampf((hi - 1.0 - a.x) / (b.x - a.x), 0.0, 1.0)
	if tb < ta:
		return
	FX.line(_events, a.lerp(b, ta), a.lerp(b, tb), col)


func _halo(ci: CanvasItem, c: Vector2, r: int, col: Color, clip: Rect2) -> void:
	for dy in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var e := float(dx * dx + dy * dy) / float(r * r)
			if e > 1.0:
				continue
			var pp := c + Vector2(dx, dy)
			if not clip.has_point(pp):
				continue
			var lv := 1.0 - e
			var th := (float((int(pp.x) % 4) * 4 + (int(pp.y) % 4)) + 0.5) / 16.0
			if lv * 0.85 > th:
				ci.draw_rect(Rect2(pp, Vector2.ONE), Color(col.r, col.g, col.b, col.a * (0.4 + lv * 0.6)))


## life in the middle distance: chimney smoke over the eastern village, a car's lamps on the western road
func _draw_midlife() -> void:
	var time := t
	if time >= T3_END:
		return
	var side_a := time >= CUT
	var clip := Rect2(Vector2(EXT.position), Vector2(EXT.size))
	var off := float(SPEED["mid"]) * _travel(time) + (37.0 if side_a else 0.0)
	if not side_a:
		var road: Array = _layout.get("mid_de_road", [])
		if road.size() >= 2:
			# a car on the farm road, its lamps throwing a short cone; it drives the same way, slower
			var sx := float(road[0]) + time * 9.0 * _motion()
			var x := _strip_x(sx, off, false)
			var y := float(road[1])
			if clip.has_point(Vector2(x, y)):
				_events_cone(_midlife, Vector2(x, y), -1.0, clip)
				_midlife.draw_rect(Rect2(Vector2(roundf(x), y), Vector2(1, 1)), Color("#fce2b0"))
				_midlife.draw_rect(Rect2(Vector2(roundf(x) + 3, y), Vector2(1, 1)), Color("#4a1712"))
	# the village chimneys smoke on both sides (wood fires in the east, coal in the west)
	var chims: Array = _layout.get("mid_su_chimneys" if side_a else "mid_de_chimneys", [])
	var smoke := Color(0.55, 0.6, 0.68, 0.55) if side_a else Color(0.45, 0.5, 0.58, 0.5)
	for i in chims.size():
		var c: Array = chims[i]
		for k in 5:
			var age := fposmod(time * 0.9 + float(k) * 0.8 + float(i) * 0.31, 4.0)
			var sx := float(c[0]) + age * 2.2 * (1.0 if side_a else -1.0)
			var x := _strip_x(sx, off, side_a)
			var y := float(c[1]) - age * 3.2
			var r := 1.0 + age * 0.45
			var pp := Vector2(roundf(x - r), roundf(y - r * 0.6))
			if clip.has_point(pp):
				_midlife.draw_rect(Rect2(pp, Vector2(roundi(r * 2.0), maxi(1, roundi(r * 1.2)))),
					Color(smoke.r, smoke.g, smoke.b, smoke.a * (1.0 - age / 4.0)))


func _events_cone(ci: CanvasItem, p: Vector2, dir: float, clip: Rect2) -> void:
	for k in range(1, 12):
		for dy in range(-((k + 2) / 4), (k + 2) / 4 + 1):
			var pp := Vector2(roundf(p.x + dir * k), p.y + dy)
			var th := (float(((k + 3) % 4) * 4 + ((dy + 5) % 4)) + 0.5) / 16.0
			if clip.has_point(pp) and (1.0 - float(k) / 12.0) * 0.8 > th:
				ci.draw_rect(Rect2(pp, Vector2.ONE), Color(0.95, 0.8, 0.55, 0.45))


## Konrad's car: the coffee steaming, the lamp's fringe and the curtain tassels swinging with the joints
func _draw_roomlife_k() -> void:
	var time := t
	if time >= CUT:
		return
	var rm := reduced_motion()
	var cup: Array = _layout.get("k_cup", [352, 226])
	var steam := Color(0.85, 0.78, 0.66, 0.35)
	for k in 4:
		var age := fposmod(time * 0.7 + k * 0.5, 2.0)
		var x := float(cup[0]) + sin(age * 3.0 + k) * 1.5 + age * 1.2
		var y := float(cup[1]) - 2.0 - age * 7.0
		if age < 1.7:
			_roomlife_k.draw_rect(Rect2(Vector2(roundf(x), roundf(y)), Vector2(1, 2)),
				Color(steam.r, steam.g, steam.b, steam.a * (1.0 - age / 1.7)))
	var sw := 0.0 if rm else float(_jolt(time - 0.08, false)) + 0.6 * sin(TAU * time / 1.55)
	for tsl in _layout.get("k_tassels", []):
		var p0 := Vector2(float(tsl[0]), float(tsl[1]))
		var p1 := p0 + Vector2(roundf(sw), 7)
		FX.line(_roomlife_k, p0, p1, Color("#9c7630"))
		_roomlife_k.draw_rect(Rect2(p1 + Vector2(-1, 0), Vector2(3, 4)), Color("#c49a48"))
		_roomlife_k.draw_rect(Rect2(p1 + Vector2(-1, 3), Vector2(3, 1)), Color("#73531f"))


## Alexei's car: the towel on the berth ladder and the hanging net bag swing with the joints
func _draw_roomlife_a() -> void:
	var time := t
	if time < CUT:
		return
	var rm := reduced_motion()
	var sw := 0.0 if rm else float(_jolt(time - 0.06, true)) + 0.8 * sin(TAU * time / 1.8 + 0.4)
	for tw in _layout.get("a_swing", []):
		var p0 := Vector2(float(tw[0]), float(tw[1]))
		var ln := float(tw[2])
		var col := Color(str(tw[3])) if tw.size() > 3 else Color("#a1aab7")
		for k in int(ln):
			var u := float(k) / ln
			var x := p0.x + roundf(sw * u * 1.4)
			_roomlife_a.draw_rect(Rect2(Vector2(x, p0.y + k), Vector2(float(tw[4]) if tw.size() > 4 else 4.0, 1)), col)


# ------------------------------------------------------------------ exterior drawing
func _draw_poles() -> void:
	if _pole_tex == null:
		return
	var time := t
	if time >= T3_END:
		return
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
	var cx := float(GLASS.position.x + GLASS.size.x / 2)
	for x in xs:
		if x > clip.position.x - pw and x < clip.end.x:
			if side_a:
				# no poles on the bridge (world-locked like the girders): only the wires run on its girders
				var tc := time + (cx - (float(x) + pw * 0.5)) / (float(SPEED["pole"]) * _motion())
				var tt := _truss_times()
				if tc > tt.x - 0.08 and tc < tt.y + 0.08:
					continue
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
	if time >= T3_END:
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
	if time >= T3_END or (time > 7.8 and time < 10.2):
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


# ------------------------------------------------------------------ t3b: the Line before dawn
func _lp() -> Dictionary:
	return _layout.get("line", {}).get("proj", {"vpx": 320.0, "vpy": 122.0, "f": 400.0, "eye": 16.0})


func _lproj(L: Dictionary, x: float, y: float, z: float) -> Vector2:
	var zz := maxf(z, 0.5)
	return Vector2(float(L["vpx"]) + float(L["f"]) * x / zz, float(L["vpy"]) - float(L["f"]) * (y - float(L["eye"])) / zz)


## rear z (metres from the camera) of Konrad's (x) and Alexei's (y) last car
func line_rear_z(time: float) -> Vector2:
	var u := maxf(0.0, time - LINE_IN[0])
	var k := 0.8 if reduced_motion() else 1.0
	return Vector2(44.0 + u * 21.0 * k, 50.0 + u * 23.5 * k)


func _draw_line_trains() -> void:
	if not line or not line.visible:
		return
	var L := _lp()
	var zr := line_rear_z(t)
	var xs: Array = _layout.get("line", {}).get("track_x", [-42.0, 42.0])
	# far train first (painter's order): both are about equally far, draw Alexei's (right) after Konrad's
	_line_train(L, float(xs[0]), zr.x, 0)
	_line_train(L, float(xs[1]), zr.y, 1)


func _line_train(L: Dictionary, tx: float, zr: float, side: int) -> void:
	var inner := 1.0 if tx < 0.0 else -1.0             # the side facing the Line (and us)
	var half := 1.5
	var xs_in := tx + inner * half
	var xs_out := tx - inner * half
	var body := Color("#2a3646") if side == 0 else Color("#1e302e")
	var lit := Color("#3a4859") if side == 0 else Color("#2b4541")
	var roof := Color("#8593a3")
	var dark := Color("#0c111c")
	var win_on := Color("#d08f55")
	var win_hot := Color("#edb777")
	# cars from the front (far) to the rear (near): loco, tender, 6 coaches
	var cars: Array = []
	var z := zr
	for c in 6:
		cars.append([z, z + 24.0, "coach", c])
		z += 25.0
	cars.append([z, z + 8.0, "tender", 6])
	z += 8.5
	cars.append([z, z + 19.0, "loco", 7])
	cars.reverse()
	for car in cars:
		var z0: float = car[0]
		var z1: float = car[1]
		var kind: String = car[2]
		var idx: int = car[3]
		var top := 4.2 if kind != "tender" else 3.4
		# visible side
		var q := PackedVector2Array([_lproj(L, xs_in, 0.6, z0).round(), _lproj(L, xs_in, top, z0).round(),
			_lproj(L, xs_in, top, z1).round(), _lproj(L, xs_in, 0.6, z1).round()])
		draw_poly_safe(_l3_trains, q, lit if kind == "coach" else dark)
		# roof (snow) seen from above
		var rq := PackedVector2Array([_lproj(L, xs_in, top, z0).round(), _lproj(L, xs_out, top, z0).round(),
			_lproj(L, xs_out, top, z1).round(), _lproj(L, xs_in, top, z1).round()])
		draw_poly_safe(_l3_trains, rq, roof if kind != "loco" else body)
		# underframe line
		FX.line(_l3_trains, _lproj(L, xs_in, 0.6, z0), _lproj(L, xs_in, 0.6, z1), dark)
		if kind == "coach":
			var sealed := side == 1 and idx == 5                # Alexei's wagon 4 at his tail: no windows
			var salon := side == 0 and idx == 2
			if not sealed:
				var wz := z0 + 1.5
				var k := 0
				while wz + 1.1 < z1 - 1.0:
					var on := salon or ((idx * 3 + k) % 4 != 1)
					if on:
						var a := _lproj(L, xs_in, 1.9, wz).round()
						var b := _lproj(L, xs_in, 3.2, wz + 1.2).round()
						var lo := Vector2(minf(a.x, b.x), minf(a.y, b.y))
						var hi := Vector2(maxf(a.x, b.x), maxf(a.y, b.y))
						_l3_trains.draw_rect(Rect2(lo, Vector2(maxf(1.0, hi.x - lo.x), maxf(1.0, hi.y - lo.y))),
							win_hot if salon else win_on)
					wz += 2.2
					k += 1
			else:
				var sp := _lproj(L, xs_in, 1.9, z0 + 12.0).round()
				_l3_trains.draw_rect(Rect2(sp, Vector2.ONE), Color("#c49a48"))
		elif kind == "loco":
			# firebox glow under the cab, the plume (drawn below)
			var fb := _lproj(L, xs_in, 1.0, z0 + 2.0).round()
			_l3_trains.draw_rect(Rect2(fb, Vector2(2, 1)), Color("#d08f55"))
	# rear face of the last car with the two red tail lamps
	var rear := PackedVector2Array([_lproj(L, xs_in, 0.6, zr).round(), _lproj(L, xs_in, 4.2, zr).round(),
		_lproj(L, xs_out, 4.2, zr).round(), _lproj(L, xs_out, 0.6, zr).round()])
	draw_poly_safe(_l3_trains, rear, dark)
	for lx in [xs_in, xs_out]:
		var lp := _lproj(L, lx + (0.4 if lx < tx else -0.4), 1.0, zr).round()
		var r := clampf(float(L["f"]) * 0.12 / zr, 0.0, 2.0)
		_l3_trains.draw_rect(Rect2(lp - Vector2(floorf(r), floorf(r)), Vector2(floorf(r) * 2.0 + 1.0, floorf(r) * 2.0 + 1.0)),
			Color("#c8503c"))
	# the plume: puffs from the chimney drifting back and up, warm underneath near the engine
	var zc := zr + 6.0 * 25.0 + 8.5 + 16.0
	var col_lo := Color(0.75, 0.55, 0.38, 0.75)
	var col_hi := Color(0.62, 0.68, 0.78, 0.6)
	for k in 14:
		var age := fposmod(t * 1.3 + float(k) * 0.43, 6.0)
		var pz := zc - age * 9.0
		if pz < zr * 0.9:
			continue
		var py := 5.0 + age * 2.2
		var px := tx + (age * 0.8 if side == 1 else -age * 0.8) * 0.5
		var c := _lproj(L, px, py, pz)
		var rr := maxf(1.0, float(L["f"]) * (0.9 + age * 0.55) / pz)
		var col := col_lo.lerp(col_hi, clampf(age / 2.0, 0.0, 1.0))
		col.a *= 1.0 - age / 6.0
		_dither_disc(_l3_trains, c, rr, col, k)


static func draw_poly_safe(ci: CanvasItem, q: PackedVector2Array, col: Color) -> void:
	# degenerate quads (far away) collapse to a line; skip the polygon then
	var area := 0.0
	for i in q.size():
		var a := q[i]
		var b := q[(i + 1) % q.size()]
		area += a.x * b.y - b.x * a.y
	if absf(area) < 1.0:
		FX.line(ci, q[0], q[2], col)
		return
	ci.draw_colored_polygon(q, col)


func _dither_disc(ci: CanvasItem, c: Vector2, r: float, col: Color, seed: int) -> void:
	var ir := int(ceil(r))
	for dy in range(-ir, ir + 1):
		for dx in range(-ir, ir + 1):
			var d := sqrt(float(dx * dx + dy * dy)) / maxf(r, 0.5)
			if d > 1.0:
				continue
			var pp := Vector2(roundf(c.x) + dx, roundf(c.y) + dy)
			var th := (float((int(pp.x + seed) % 4) * 4 + (int(pp.y) % 4)) + 0.5) / 16.0
			if (1.0 - d * d) * 1.1 > th:
				ci.draw_rect(Rect2(pp, Vector2.ONE), col)


## the watchtowers' searchlights sweep over the fields toward the tracks
func _draw_line_search() -> void:
	if not line or not line.visible:
		return
	var L := _lp()
	# a border patrol's car coming down the road between the fences toward us: two lamps and their cones
	var pz := 520.0 - maxf(0.0, t - LINE_IN[0]) * 62.0 * _motion()
	if pz > 30.0:
		for sx in [-0.7, 0.7]:
			var hp := _lproj(L, sx, 0.9, pz).round()
			var r := maxf(1.0, float(L["f"]) * 0.18 / pz)
			_l3_search.draw_rect(Rect2(hp - Vector2(floorf(r * 0.5), floorf(r * 0.5)), Vector2(maxf(1.0, r), maxf(1.0, r))),
				Color(0.95, 0.9, 0.75, 0.95))
		for k in range(1, 9):
			var cz := pz - float(k) * 4.0
			if cz < 8.0:
				break
			var c := _lproj(L, 0.0, 0.0, cz).round()
			var hw := maxf(1.0, float(L["f"]) * (0.9 + k * 0.25) / cz)
			_l3_search.draw_rect(Rect2(Vector2(c.x - hw, c.y), Vector2(hw * 2.0, 1)), Color(0.9, 0.85, 0.7, 0.16 - k * 0.015))
	var towers: Array = _layout.get("line", {}).get("towers", [])
	var col := Color(0.55, 0.62, 0.75, 0.24)
	for i in towers.size():
		var tw: Array = towers[i]
		var src := _lproj(L, float(tw[0]), 11.5, float(tw[1]))
		var sweep := sin(t * 0.7 * _motion() + float(i) * 1.7)
		var gz := float(tw[1]) + 30.0 + float(i) * 12.0
		var gx := sweep * 55.0
		var dst := _lproj(L, gx, 0.0, gz)
		var steps := int(maxf(absf(dst.y - src.y), 1.0))
		for k in steps:
			var u := float(k) / float(steps)
			var cx := lerpf(src.x, dst.x, u)
			var hw := 0.5 + u * maxf(2.0, float(L["f"]) * 3.0 / gz)
			var y := roundf(lerpf(src.y, dst.y, u))
			_l3_search.draw_rect(Rect2(Vector2(roundf(cx - hw), y), Vector2(maxf(1.0, roundf(hw * 2.0)), 1)), col)
		var rx := maxf(3.0, float(L["f"]) * 5.0 / gz)
		var ry := maxf(1.0, rx * float(L["eye"]) / gz)
		for dy in range(-int(ry), int(ry) + 1):
			for dx in range(-int(rx), int(rx) + 1):
				var e := (dx * dx) / (rx * rx) + (dy * dy) / maxf(ry * ry, 0.5)
				if e <= 1.0 and ((dx + dy) & 1) == 0:
					_l3_search.draw_rect(Rect2(dst.round() + Vector2(dx, dy), Vector2.ONE), Color(0.6, 0.66, 0.78, 0.2))


# ------------------------------------------------------------------ t4: dawn over Veltrava (crane)
const T_MEET := 28.1
const MEET_X := 320.0


func _crane(time: float) -> float:
	if reduced_motion():
		return CRANE_RM
	return ramp01(time, float(CRANE[0]), float(CRANE[1]))


func _planes(time: float) -> void:
	var e := _crane(time)
	var pl: Dictionary = _d4.get("planes", {"sky": 40, "city": 105, "bridge": 140, "bank": 225})
	for k in ["sky", "city", "bridge", "bank"]:
		_off[k] = roundf(-float(pl.get(k, 0)) * (1.0 - e))


## train fronts over the shot (x of the leading buffer): Konrad's from the west, Alexei's from the east; they
## meet over the middle arch at T_MEET and pass each other, slowing a little toward the city.
func _train_fronts(time: float) -> Vector2:
	var v0 := 46.0
	var v1 := 22.0
	var t0 := DAWN_IN[0] - 0.6
	var total := DUR - t0
	var u := clampf((time - t0) / total, 0.0, 1.0)
	var s := (v0 * u + (v1 - v0) * u * u * 0.5) * total
	var um := (T_MEET - t0) / total
	var sm := (v0 * um + (v1 - v0) * um * um * 0.5) * total
	var de := MEET_X + (s - sm)
	var su := MEET_X - (s - sm)
	return Vector2(de, su)


func _apply_dawn(time: float, _rm: bool) -> void:
	if not dawn.visible:
		return
	_planes(time)
	_p_sky.position.y = _off["sky"]
	_p_sun.position.y = _off["sky"]
	_p_city.position.y = _off["city"]
	_p_dome.position.y = _off["city"]
	_p_bridge.position.y = _off["bridge"]
	_p_parapet.position.y = _off["bridge"]
	_p_lampglow.position.y = _off["bridge"]
	_p_bank.position.y = _off["bank"]
	var e := _crane(time)
	_p_sun.modulate = Color(1, 1, 1, 0.35 + 0.65 * ramp01(time, 24.0, 34.0))
	_p_dome.modulate = Color(1, 1, 1, ramp01(time, 29.5, 35.0))
	_p_lampglow.modulate = Color(1, 1, 1, 1.0 - 0.6 * e)
	var f := _train_fronts(time)
	var de_rail := float(_d4.get("de_rail", 281))
	var su_rail := float(_d4.get("su_rail", 291))
	var lde: Dictionary = _layout.get("train_de", {})
	var lsu: Dictionary = _layout.get("train_su", {})
	if _train_de.texture:
		_train_de.position = Vector2(roundf(f.x - float(lde.get("front", _train_de.texture.get_width()))),
			de_rail - 28.0 + _off["bridge"])
		_train_de.frame = int(floor(time * 4.0)) % 2      # pennants flutter
	if _train_su.texture:
		_train_su.position = Vector2(roundf(f.y - float(lsu.get("front", 0))), su_rail - 28.0 + _off["bridge"])
		_train_su.frame = 0
	_d4_snow.set_time(time)
	_citylife.queue_redraw()
	_riverlife.queue_redraw()
	_smoke.queue_redraw()
	_lamps.queue_redraw()
	_bank.queue_redraw()


var _smoke_atlas: Texture2D = null
func _smoke_tex() -> Texture2D:
	if _smoke_atlas == null:
		_smoke_atlas = tex("trains/smoke.png")
	return _smoke_atlas


## how hard the engines work: full steam over the bridge and through the meeting; then the drivers shut off and
## coast into the station, the plumes thin to a wisp at the chimney (AD round 2: the old steam drifts off and the
## final frame shows the trains on the bridge and the old town putting out its lights)
func _steam_power(time: float) -> float:
	return 1.0 - 0.85 * ramp01(time, T_MEET + 1.0, T_MEET + 3.6)


## steam puffs from both chimneys: spawned at fixed times, each puff a pure function of its age; they trail
## behind their engine, rise and spread, drift east on the morning air and dissolve (the two plumes run together
## over the middle arch, then thin out); puffs vary in growth, drift and frame, so no two are the same
func _draw_smoke() -> void:
	var atlas: Texture2D = _smoke_tex()
	if atlas == null:
		return
	var n := int(_layout.get("smoke", {}).get("frames", 8))
	var fw := atlas.get_width() / n
	var fh := atlas.get_height()
	var life := 4.6
	var every := 0.24
	var t_first := DAWN_IN[0] - 2.4
	var rails := [float(_d4.get("de_rail", 281)), float(_d4.get("su_rail", 291))]
	for side in [0, 1]:
		var Ls: Dictionary = _layout.get("train_de" if side == 0 else "train_su", {})
		var ch: Array = Ls.get("chimney", [0, 0])
		var front := float(Ls.get("front", 0))
		var top: float = float(rails[side]) - 28.0 + float(_off["bridge"])
		var k0 := maxi(0, int(floor((t - life - t_first) / every)))
		var k1 := int(floor((t - t_first) / every))
		for k in range(k0, k1 + 1):
			var born := t_first + k * every + (0.11 if side == 1 else 0.0)
			var age := t - born
			if age < 0.0:
				continue
			var pw := _steam_power(born)
			if pw < 0.55 and k % 3 != 0:
				continue                                  # coasting: only a puff now and then
			var jit := _h(k * 3 + side * 101, 57)
			var jit2 := _h(k * 7 + side * 53, 91)
			var lf := life * (0.45 + 0.55 * pw) * (0.85 + 0.15 * jit2)
			if age > lf:
				continue
			var u := age / lf
			var fr := _train_fronts(born)
			var cx := (fr.x - front + float(ch[0])) if side == 0 else (fr.y - front + float(ch[0]))
			var dirx := -1.0 if side == 0 else 1.0
			var trail := dirx * (5.0 * age) + (7.0 + jit2 * 2.5) * age + jit * 3.0
			var rise := ((14.0 + jit * 3.0) * age - 0.55 * age * age) * (0.55 + 0.45 * pw)
			var p := Vector2(cx + trail - fw * 0.5, top + float(ch[1]) - 4.0 - rise - fh * 0.5)
			var fi := clampi(int(u * float(n - 1) * (0.5 + 0.5 * pw) + 0.5 + (0.6 if jit2 > 0.4 else 0.0)), 0, n - 1)
			var a := 1.0 - ramp01(u, 0.4, 1.0)
			_smoke.draw_texture_rect_region(atlas, Rect2(p.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh),
				Color(1, 1, 1, a))


## headlamps of both engines (additive): a hot core and a short dithered beam ahead
func _draw_lamps() -> void:
	var f := _train_fronts(t)
	var rails := [float(_d4.get("de_rail", 281)), float(_d4.get("su_rail", 291))]
	for side in [0, 1]:
		var Ls: Dictionary = _layout.get("train_de" if side == 0 else "train_su", {})
		var hl: Array = Ls.get("headlamp", [0, 12])
		var front := float(Ls.get("front", 0))
		var x := ((f.x if side == 0 else f.y) - front + float(hl[0]))
		var y: float = float(rails[side]) - 28.0 + float(_off["bridge"]) + float(hl[1])
		var dir := 1.0 if side == 0 else -1.0
		for k in range(1, 14):
			for dy in range(-1, 2):
				var th := (float(((k + 3) % 4) * 4 + ((dy + 5) % 4)) + 0.5) / 16.0
				if (1.0 - float(k) / 14.0) * 0.8 > th:
					_lamps.draw_rect(Rect2(Vector2(roundf(x + dir * k), y + dy), Vector2.ONE), Color(0.35, 0.3, 0.22))
		_lamps.draw_rect(Rect2(Vector2(roundf(x) - 1, y - 1), Vector2(3, 3)), Color(0.45, 0.4, 0.3))


## the waking city (city plane): windows going dark one by one, chimney smoke, a tram on the quay, gulls
func _draw_citylife() -> void:
	var oy: float = _off["city"]
	var u := t - T4_START
	var night := Color("#1a2431")
	for w in _layout.get("d4_lit_windows", []):
		if u > float(w[4]):
			_citylife.draw_rect(Rect2(float(w[0]), float(w[1]) + oy, float(w[2]), float(w[3])), night)
	if _chim_tex:
		var n := int(_layout.get("chimney_smoke", {}).get("frames", 6))
		var fw := _chim_tex.get_width() / n
		var fh := _chim_tex.get_height()
		var chims: Array = _layout.get("d4_chimneys", [])
		var sp := 0.6 if reduced_motion() else 1.0
		for i in chims.size():
			var c: Array = chims[i]
			for k in range(4):
				var age := fposmod(t * sp + float(k) * 1.4 + float(i) * 0.37, 5.6)
				var p := Vector2(float(c[0]) + age * age * 0.3 - fw * 0.5, float(c[1]) + oy - 2.0 - age * 3.6 - fh * 0.5)
				var fi := clampi(int(age / 5.6 * float(n)), 0, n - 1)
				_citylife.draw_texture_rect_region(_chim_tex, Rect2(p.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh))
	if _tram_tex:
		var tl: Dictionary = _layout.get("d4_tram", {})
		var fwt := _tram_tex.get_width() / 2
		var x := 40.0 + u * 20.0 * _motion()
		var fr := 1 if hnoise(t * 7.0, 31) > 0.55 else 0
		_citylife.draw_texture_rect_region(_tram_tex, Rect2(Vector2(roundf(x), float(tl.get("y", 228)) + oy),
			Vector2(fwt, _tram_tex.get_height())), Rect2(fr * fwt, 0, fwt, _tram_tex.get_height()))
	_draw_people(_citylife, "city", oy)
	if _gull_tex:
		var gw := _gull_tex.get_width() / 4
		for b in 7:
			var ph := float(b) * 0.9
			var cxg := 250.0 + float(b * 37 % 160)
			var cyg := 70.0 + float(b * 13 % 40)
			var p := Vector2(cxg + sin(u * 0.45 + ph) * 60.0, cyg + oy + cos(u * 0.45 + ph) * 14.0)
			var fi := int(floor(u * 6.0 + b)) % 4
			_citylife.draw_texture_rect_region(_gull_tex, Rect2(p.round(), Vector2(gw, _gull_tex.get_height())),
				Rect2(fi * gw, 0, gw, _gull_tex.get_height()))


## the river (bridge plane): glints in the channel, floes drifting, the crows lifting off the ice at the whistle
func _draw_riverlife() -> void:
	var oy: float = _off["bridge"]
	var glints: Array = _layout.get("d4_glints", [])
	var step := int(floor(t * 6.0))
	for i in glints.size():
		var g: Array = glints[i]
		if (_h(step + i * 7, 41) + 1.0) * 0.5 > 0.55:
			_riverlife.draw_rect(Rect2(float(g[0]), float(g[1]) + oy, float(g[2]) if g.size() > 2 else 2.0, 1),
				Color("#e8dcd6") if i % 3 == 0 else Color("#a1aab7"))
	_draw_people(_riverlife, "bridge", oy)
	var u := t - T4_START
	var wy := float(_d4.get("water_y", 344))
	for i in 6:
		var fx := fposmod(150.0 + float(i) * 71.0 + u * (3.0 + float(i % 3)) * _motion(), 470.0) + 120.0
		var fy := wy + 14.0 + float((i * 17) % 60)
		var fw := 6.0 + float((i * 5) % 9)
		_riverlife.draw_rect(Rect2(roundf(fx), fy + oy, fw, 1), Color("#a1aab7"))
		_riverlife.draw_rect(Rect2(roundf(fx) + 1, fy + oy - 1, fw - 2, 1), Color("#dee2e7"))
	var crow := Color("#0c111c")
	var whistle := 27.75
	for b in 11:
		var rest := Vector2(30.0 + float((b * 37) % 80), wy + 26.0 + float((b * 13) % 14))
		var lift := whistle + float(b) * 0.08 + float((b * 7) % 5) * 0.05
		var bt := t - lift
		var p := rest + Vector2(0, oy)
		var up := false
		if bt > 0.0:
			p += Vector2(bt * (26.0 + b * 3.0), -bt * (30.0 - bt * 1.4) + sin(bt * 3.0 + b) * 2.0)
			up = int(floor(bt * 8.0 + b)) % 2 == 0
		if p.y < 30.0 or p.x > 660.0:
			continue
		var q := p.round()
		_riverlife.draw_rect(Rect2(q, Vector2(2, 1)), crow)
		if bt > 0.0:
			_riverlife.draw_rect(Rect2(q + Vector2(-2, -1 if up else 1), Vector2(2, 1)), crow)
			_riverlife.draw_rect(Rect2(q + Vector2(2, -1 if up else 1), Vector2(2, 1)), crow)
		else:
			_riverlife.draw_rect(Rect2(q + Vector2(0, -1), Vector2(1, 1)), crow)


## the near bank (bank plane): the woman pulling her milk sled along the promenade, the sweeper at the lamp
func _draw_bank() -> void:
	_draw_people(_bank, "bank", float(_off["bank"]))


## the extras of a plane: walk cycles move at their own pace (half with reduced motion), idles just breathe
func _draw_people(ci: CanvasItem, plane: String, oy: float) -> void:
	for e in _people:
		var d: Dictionary = e["d"]
		if str(d.get("plane", "")) != plane:
			continue
		var tx: Texture2D = e["tex"]
		var tt := maxf(0.0, t - float(d.get("t0", 0.0)))
		var n := maxi(1, int(d.get("frames", 1)))
		var fw := int(d.get("w", tx.get_width() / n))
		var fh := int(d.get("h", tx.get_height()))
		var vx := float(d.get("vx", 0.0))
		var x := float(d.get("x", 0.0)) + tt * vx * _motion()
		var rate := float(d.get("fps", 6.0)) * (_motion() if vx != 0.0 else 1.0)
		var fi := int(floor(tt * rate)) % n
		ci.draw_texture_rect_region(tx, Rect2(Vector2(roundf(x), float(d.get("y", 0.0)) + oy), Vector2(fw, fh)),
			Rect2(fi * fw, 0, fw, fh))
