extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## LS_C3_Trains (~24 s) — the Chapter 2 -> 3 character switch „Konrads Zugfenster -> Alexeis Zugfenster“
## (STORY_BIBLE §6, C3_DESIGN §2.9).  Art: tools/pixelgen/env_veltrava_cine.py -> assets/cinematics/ch3/trains/.
##   t1  0-8 s   night, the German delegation's saloon car: Konrad at the window, lamp, drafting tube in the
##               rack, his reflection in the glass; outside the snow plain, telegraph poles, the floodlit Line
##   t2  8-10 s  match cut through the window frame: a passing light floods the glass, the room behind
##               changes (the glass opening and its iron sash are pixel-identical in both cars)
##   t3  10-18 s the Soviet car: Alexei at the window, tea glass in a metal holder; the same plain from the
##               other side (mirrored, scrolling the other way)
##   t4  18-24 s dawn: both trains converge on the three-arch river bridge of Veltrava
## Inner lines (configure(ctx).flags): Konrad evidence > suspicion > base, Alexei irina > secrecy > base,
## then cin.c3.trains.place.

const FX := preload("res://scenes/cinematics/ch3_common/pixel_fx.gd")
const DISSOLVE := preload("res://scenes/cinematics/ch3_common/c3_dissolve.gdshader")

## glass opening / exterior box — must match env_veltrava_cine.py (GLASS, EXT; checked by the test
## against assets/cinematics/ch3/layout.json)
const GLASS := Rect2i(172, 84, 296, 142)
const EXT := Rect2i(164, 76, 312, 158)
const CUT := 9.0                      # the room changes here (inside the flare)
const T1_END := 8.0
const T3_START := 10.0
const T4_START := 18.0
const DUR := 24.0
const SHOTS := [["t1", 0.0, 8.0], ["t2", 8.0, 10.0], ["t3", 10.0, 18.0], ["t4", 18.0, 24.0]]
## parallax speeds (px/s at full motion): far fence, plain, embankment, telegraph poles
const SPEED := {"far": 5.0, "mid": 26.0, "near": 150.0, "pole": 250.0}
const POLE_SPACING := 360.0
const POLE_INS := [[1, 19], [14, 19], [3, 31], [12, 31]]   # insulator tops, local to the pole sprite
const POLE_Y := 74

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
var _rflare_k: Sprite2D
var _rflare_a: Sprite2D
var _dawn_mat: ShaderMaterial
var _bridge_bg: Sprite2D
var _train_de: Sprite2D
var _train_su: Sprite2D
var _dawn_glow: Sprite2D
var _bridge_fg: Sprite2D
var _smoke: Node2D
var _life: Node2D
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
		{"t": 0.0, "amb": "amb_transition", "fade": 1.5},
		{"t": 0.0, "music": "mus_menu", "fade": 3.0},
		{"t": 0.5, "sfx": "wind_gust", "db": -15.0},
		{"t": 1.0, "say": line_konrad, "dur": 6.4},
		{"t": 8.15, "sfx": "train_horn_far", "db": -3.0},       # one horn spans the cut: heard in both cars
		{"t": 8.55, "sfx": "wind_gust", "db": -10.0},
		{"t": 10.5, "say": line_alexei, "dur": 6.8},
		{"t": 18.4, "sfx": "train_horn_far", "db": -7.0, "pv": 0.02},
		{"t": 19.0, "say": LINE_PLACE, "dur": 4.6},
		{"t": 20.5, "sfx": "train_horn_far", "db": -10.0, "pv": 0.12},
	]
	# rail joints ("ta-tam"): a soft double knock with every jolt of the car
	for j in _jolt_times(0.3, CUT, 1.55):
		c.append({"t": j, "sfx": "step_wood", "db": -24.0, "pv": 0.06})
	for j in _jolt_times(CUT + 0.4, 17.6, 1.8):
		c.append({"t": j, "sfx": "step_wood", "db": -25.0, "pv": 0.06})
	return c


static func _jolt_times(a: float, b: float, period: float) -> Array:
	var out: Array = []
	var x := a
	while x < b:
		out.append(x)
		out.append(x + 0.16)
		x += period
	return out


# ------------------------------------------------------------------ build
func _build() -> void:
	win = group("Window")
	ext = group("Exterior", win)
	var ex := Vector2(EXT.position)
	_sky = sprite("trains/ext_sky.png", ex, ext)
	_far_de = strip("trains/ext_far_de.png", Vector2(ex.x, 136), EXT.size.x, ext)
	_far_su = strip("trains/ext_far_su.png", Vector2(ex.x, 136), EXT.size.x, ext)
	_far_su.flip_h = true
	_mid = strip("trains/ext_mid.png", Vector2(ex.x, 186), EXT.size.x, ext)
	_snow_far = FX.new()
	_snow_far.name = "SnowFar"
	ext.add_child(_snow_far)
	_near = strip("trains/ext_near.png", Vector2(ex.x, 212), EXT.size.x, ext)
	_patch_k = sprite("trains/patch_warm.png", ex, ext, 1, true)
	_patch_a = sprite("trains/patch_cold.png", ex, ext, 1, true)
	_poles = Node2D.new()
	_poles.name = "Poles"
	_poles.draw.connect(_draw_poles)
	ext.add_child(_poles)
	_pole_tex = tex("trains/pole.png")
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
	_fig_a = sprite("trains/fig_alexei.png", Vector2.ZERO, room_a, 4)
	_glow_a = sprite("trains/glow_tea.png", Vector2.ZERO, room_a, 1, true)
	_steam = sprite("trains/steam_tea.png", Vector2.ZERO, room_a, 6)
	_rflare_a = sprite("trains/roomflare_a.png", Vector2.ZERO, room_a, 1, true)
	_place_from_layout()
	# dawn: one dissolving group (children share the parent's dither material)
	dawn = group("Dawn")
	_dawn_mat = ShaderMaterial.new()
	_dawn_mat.shader = DISSOLVE
	dawn.material = _dawn_mat
	_bridge_bg = sprite("trains/bridge_bg.png", Vector2.ZERO, dawn)
	_dawn_glow = sprite("trains/dawn_glow.png", Vector2.ZERO, dawn)
	_train_de = sprite("trains/train_de.png", Vector2.ZERO, dawn, 1, false, 2)
	_train_su = sprite("trains/train_su.png", Vector2.ZERO, dawn, 1, false, 2)
	_smoke = Node2D.new()
	_smoke.name = "Smoke"
	_smoke.draw.connect(_draw_smoke)
	dawn.add_child(_smoke)
	_life = Node2D.new()
	_life.name = "Life"
	_life.draw.connect(_draw_life)
	dawn.add_child(_life)
	_bridge_fg = sprite("trains/bridge_fg.png", Vector2.ZERO, dawn)
	for n in dawn.get_children():
		(n as CanvasItem).use_parent_material = true
	_setup_snow()


func _place_from_layout() -> void:
	# positions of the sprites whose art boxes are not full-frame come from the generator's layout
	var p := ASSETS + "layout.json"
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			_layout = d.get("trains", {})
	for pair in [[_fig_k, "fig_konrad"], [_fig_a, "fig_alexei"], [_glow_k, "glow_lamp"], [_glow_a, "glow_tea"],
			[_steam, "steam_tea"], [_sweep, "sweep"]]:
		var v = _layout.get(pair[1])
		if v is Array and v.size() >= 2 and pair[0]:
			(pair[0] as Sprite2D).position = Vector2(float(v[0]), float(v[1]))


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


func _apply(time: float) -> void:
	if win == null:
		return
	var rm := reduced_motion()
	var side_a := time >= CUT
	var tr := _travel(time)
	win.visible = time < T4_START + 0.6
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
	# rail-joint jolt of the room (never with reduced motion)
	var jolt := 0.0
	if not rm and time < T4_START:
		var ph := fposmod(time - (0.3 if not side_a else CUT + 0.4), 1.55 if not side_a else 1.8)
		if ph < 0.07 or (ph > 0.16 and ph < 0.22):
			jolt = 1.0
	room_k.position.y = jolt
	room_a.position.y = jolt
	# figures: breathing (1 px) + a later small head turn toward the glass
	var breath := 1 if sin(TAU * time / 3.8) > 0.55 else 0
	_fig_k.frame = clampi((2 if time > 4.6 else 0) + breath, 0, 3) if _fig_k.texture else 0
	_fig_a.frame = clampi((2 if time > 14.3 else 0) + breath, 0, 3) if _fig_a.texture else 0
	# lamp / tea glow flicker (subtle, never strobing)
	var fl := 0.035 * (0.4 if rm else 1.0)
	_glow_k.modulate = Color(1, 1, 1, 0.94 + fl * hnoise(time * 2.7, 7))
	_glow_a.modulate = Color(1, 1, 1, 0.9 + fl * hnoise(time * 2.3, 9))
	if _steam.texture:
		_steam.frame = int(floor(time * (4.0 if rm else 6.0))) % 6
	# t2: the passing light
	_apply_flare(time, rm)
	# t3 -> t4 dissolve, then the dawn shot
	var d0 := 16.9 if rm else 17.3
	var d1 := 18.6 if rm else 18.3
	var prog := clampf((time - d0) / (d1 - d0), 0.0, 1.0)
	dawn.visible = prog > 0.0
	_dawn_mat.set_shader_parameter("progress", prog)
	_apply_dawn(time, rm)


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
	_rflare_k.visible = peak > 0.001
	_rflare_a.visible = peak > 0.001
	_rflare_k.modulate = Color(1, 1, 1, peak * 0.85)
	_rflare_a.modulate = Color(1, 1, 1, peak * 0.85)


# ------------------------------------------------------------------ dawn (t4)
## train front positions over the shot: Konrad's from the left, Alexei's from the right; they come level
## under the palais dome as the shot ends (slowing toward the station).
func _train_fronts(time: float) -> Vector2:
	var u := clampf((time - 17.3) / (DUR - 17.3), 0.0, 1.0)
	var e := 1.0 - pow(1.0 - u, 1.7)
	var de_front := lerpf(-40.0, 334.0, e)
	var su_front := lerpf(680.0, 306.0, e)
	return Vector2(de_front, su_front)


func _apply_dawn(time: float, _rm: bool) -> void:
	if not dawn.visible:
		return
	var f := _train_fronts(time)
	var lde: Dictionary = _layout.get("train_de", {})
	var lsu: Dictionary = _layout.get("train_su", {})
	if _train_de.texture:
		_train_de.position = Vector2(roundf(f.x - float(lde.get("front", _train_de.texture.get_width()))),
			float(lde.get("y", 190)))
		_train_de.frame = int(floor(time * 5.0)) % 2      # pennants flutter, wheel spokes
	if _train_su.texture:
		_train_su.position = Vector2(roundf(f.y - float(lsu.get("front", 0))), float(lsu.get("y", 194)))
		_train_su.frame = int(floor(time * 5.0 + 0.5)) % 2
	_dawn_glow.modulate = Color(1, 1, 1, ramp01(time, 18.0, 23.5))
	_smoke.queue_redraw()
	_life.queue_redraw()


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


## smoke puffs from both chimneys: spawned at fixed times, each puff a pure function of its age.
func _draw_smoke() -> void:
	var atlas: Texture2D = _smoke_tex()
	if atlas == null:
		return
	var n := int(_layout.get("smoke", {}).get("frames", 6))
	var fw := atlas.get_width() / n
	var fh := atlas.get_height()
	var lde: Dictionary = _layout.get("train_de", {})
	var lsu: Dictionary = _layout.get("train_su", {})
	for side in [0, 1]:
		var chim_dx := float((lde if side == 0 else lsu).get("chimney", [0, 0])[0])
		var chim_y := float((lde if side == 0 else lsu).get("y", 190)) + float((lde if side == 0 else lsu).get("chimney", [0, 0])[1])
		var k0 := int(floor((t - 6.0 - 17.3) / 0.32))
		for k in range(maxi(0, k0), int(floor((t - 17.3) / 0.32)) + 1):
			var born := 17.3 + k * 0.32 + (0.13 if side == 1 else 0.0)
			var age := t - born
			if age < 0.0 or age > 6.0:
				continue
			var fr := _train_fronts(born)
			var cx := (fr.x - float(lde.get("front", 0)) + chim_dx) if side == 0 else (fr.y - float(lsu.get("front", 0)) + chim_dx)
			var drift := (-1.0 if side == 0 else 1.0) * 9.0 * age + 4.0 * age      # trails behind, a breeze to the right
			var p := Vector2(cx + drift - fw * 0.5, chim_y - 7.0 * age - age * age * 0.8 - fh * 0.5)
			var fi := clampi(int(age / 6.0 * n), 0, n - 1)
			_smoke.draw_texture_rect_region(atlas, Rect2(p.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh))


var _smoke_atlas: Texture2D = null
func _smoke_tex() -> Texture2D:
	if _smoke_atlas == null:
		_smoke_atlas = tex("trains/smoke.png")
	return _smoke_atlas


## river glints and a few crows over the water (deterministic hash per time step)
func _draw_life() -> void:
	var glints: Array = _layout.get("glints", [])
	var step := int(floor(t * 6.0))
	for i in glints.size():
		var g: Array = glints[i]
		if (_h(step + i * 7, 41) + 1.0) * 0.5 > 0.55:
			_life.draw_rect(Rect2(float(g[0]), float(g[1]), float(g[2]) if g.size() > 2 else 2.0, 1), Color("#fce2b0") if i % 3 == 0 else Color("#d3cdd3"))
	var crow := Color("#121a26")
	for b in 4:
		var bt := t - 19.0 - b * 0.35
		if bt < 0.0 or bt > 5.5:
			continue
		var x := 120.0 + bt * 38.0 + b * 9.0
		var y := 118.0 - bt * 3.0 + sin(bt * 1.7 + b) * 2.0 + b * 3.0
		var up := int(floor(bt * 7.0 + b)) % 2 == 0
		var p := Vector2(roundf(x), roundf(y))
		_life.draw_rect(Rect2(p, Vector2(2, 1)), crow)
		_life.draw_rect(Rect2(p + Vector2(-2, -1 if up else 1), Vector2(2, 1)), crow)
		_life.draw_rect(Rect2(p + Vector2(2, -1 if up else 1), Vector2(2, 1)), crow)
