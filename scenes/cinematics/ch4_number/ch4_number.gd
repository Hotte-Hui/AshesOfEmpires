extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Number (13 s) — the first match cut, on the wagon number C-17/45 (C4_DESIGN §2.9).
##   n1  0-4      Service tunnel 3: Alexei's lamp along the planks of wagon 24 318; the fresh red-brown paint,
##                the tin stencil still taped on, the wet C-17/45, a drip runs down; chalk: „ВТ 23.40“ (pan); dust
##                turns in the lamp's beam, water drips from the tunnel roof
##   n2  4-5.5    macro: the stencilled 45, wet; the drip                               -- hard cut on the 45 --
##   n3  5.5-9.5  Berlin at dawn: the SAME 45 black on a pine crate, snow in the air (n3a, to 6.7) -> the loading
##                hatch: the lorry's tail lights and exhaust, the stack of crates goes down the lit shaft on the
##                hoist, the blinking lamp on the site hoarding, the dome of the Great Hall far off (n3b)
##   n4  9.5-13   the tram loop Süd 8 as the level paints it: the first tram of line 74 rings and stops, sparks at its
##                bow; Konrad at the stop, a woman and her boy waiting at the shelter, a worker on early shift
##                coming along, crows lifting off the wire, the column's warm air steaming, the cranes' lamps
## Round 10: n1 shows the tunnel -- the wagon sits lower under the cast vault (cables, pipe, a dead bulkhead lamp,
## the tunnel's mark), the gap to the wagon before it at the start; Alexei's lamp is a warm beam out of the dark at
## the lower left that bobs with his steps, his breath drifts into it, the darkness never goes fully black; dust
## and drips catch the light.  n3b: the banksman beside the hatch signals the descent, the driver waits by his cab;
## the hand chain runs down into the shaft (pulled from below) and the lift chain's links travel with the load.
## Lines: the time in Karsk, Alexei's line, the time in Berlin (same moment: Moscow time is Berlin + 2).

const DUR := 13.0
const SHOTS := [["n1", 0.0, 4.0], ["n2", 4.0, 5.5], ["n3", 5.5, 9.5], ["n4", 9.5, 13.0]]
const LINES := ["cin.c4.number.karsk", "cin.c4.number.alexei", "cin.c4.number.berlin"]
const N1_PAN := [-40.0, -400.0]        # plate x offset from .. to (reduced motion halves the travel)
const N3_CUT := 6.7                    # n3a macro -> n3b hatch
const N3_LOWER := [7.1, 9.3, 150.0]    # the stack goes down: from, to, depth px
const TRAM_IN := [9.9, 12.3, 660.0]    # the tram enters: from, stops at, start x
const TRAM_BELL := 11.4                # its bell (c4cine_tram, tests compare)
const N4_DRIFT := 18.0                 # the establishing shot drifts this far to the right (parallax)
const CROWS_UP := 10.7                 # the crows on the wire lift off as the tram comes in

var L4: Dictionary = {}
var LP: Dictionary = {}
var n1: Node2D
var n2: Node2D
var n3a: Node2D
var n3b: Node2D
var n4: Node2D
var _plate1: Sprite2D
var _dark1: Sprite2D
var _glow1: Sprite2D
var _beam1: Sprite2D
var _breath1: Node2D
var _breath_tex: Texture2D
var _people3: Dictionary = {}
var _drip1: Node2D
var _motes1: Node2D
var _glints: Sprite2D
var _drip2: Node2D
var _flakes: Node2D
var _flake_tex: Texture2D
var _motes_tex: Texture2D
var _stack: Sprite2D
var _chain: Node2D
var _shaft: Sprite2D
var _tails: Array = []
var _exhaust: Node2D
var _exhaust_tex: Texture2D
var _snow3: Node2D
var _layers4: Dictionary = {}
var _fx4: Dictionary = {}
var _crow_tex: Texture2D
var _crows: Node2D
var _tram: Sprite2D
var _sparks: Node2D
var _konrad: Sprite2D
var _people: Dictionary = {}
var _snow4: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return LINES.duplicate()


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 1.2},
		{"t": 0.0, "amb": "", "fade": 0.8},
		{"t": 0.0, "bed": "c4cine_tunnel", "db": -6.0},
		say_at(LINES[0], 0.25, 1.4, 1.6),
		say_at(LINES[1], 1.75),
		{"t": 4.0, "bed": "c4cine_drip", "db": -8.0},
		{"t": 5.5, "bed": "c4cine_hatch", "db": -6.0},
		say_at(LINES[2], 5.8, 1.4, 1.6),
		{"t": 9.5, "bed": "c4cine_tram", "db": -5.0},
	]


func _build() -> void:
	L4 = _layout_section("number")
	LP = _layout_section("places")
	_flake_tex = tex("number/flakes.png")
	_exhaust_tex = tex("number/exhaust.png")
	_motes_tex = tex("places/motes.png")
	_crow_tex = tex("places/fx_crows.png")
	# ---- n1: the wagon side in the tunnel
	n1 = group("Tunnel")
	_breath_tex = tex("places/breath.png")
	_plate1 = sprite("number/n1_wagon.png", Vector2.ZERO, n1)
	_drip1 = fx(n1, "Drip", _draw_drip1)
	_glow1 = sprite("number/n1_glow.png", Vector2.ZERO, n1, 1, true)
	_dark1 = sprite("number/n1_dark.png", Vector2.ZERO, n1)
	_beam1 = sprite("number/n1_beam.png", Vector2.ZERO, n1, 1, true)
	_motes1 = fx(n1, "Motes", _draw_motes1)
	_breath1 = fx(n1, "Breath", _draw_breath1)
	# ---- n2 / n3a: the macros
	n2 = group("Macro")
	sprite("number/n2_macro.png", Vector2.ZERO, n2)
	_glints = sprite("number/n2_glints.png", Vector2.ZERO, n2, 1, true)
	_drip2 = fx(n2, "Drip", _draw_drip2)
	n3a = group("Crate")
	sprite("number/n3a_macro.png", Vector2.ZERO, n3a)
	_flakes = fx(n3a, "Flakes", _draw_flakes)
	# ---- n3b: the hatch at dawn
	n3b = group("Hatch")
	sprite("number/n3b_hatch.png", Vector2.ZERO, n3b)
	var hatch: Array = L4.get("n3_hatch", [360, 276, 520, 292])
	_shaft = sprite("number/n3b_shaft.png", Vector2((float(hatch[0]) + float(hatch[2])) * 0.5 - 110.0,
		float(hatch[1]) - 46.0), n3b, 1, true)
	var pidx: Dictionary = L4.get("n3_people", {})
	for key in ["driver", "banksman"]:
		if pidx.has(key):
			_people3[key] = fig("number/n3_%s.png" % key, n3b)
	_chain = fx(n3b, "Chain", _draw_chain)
	_stack = sprite("number/n3b_stack.png", Vector2.ZERO, n3b)
	sprite("number/n3b_lip.png", Vector2.ZERO, n3b)
	for p in L4.get("n3_tail", []):
		_tails.append(sprite("number/n3b_tail.png", Vector2(float(p[0]) - 32, float(p[1]) - 24), n3b, 1, true))
	_exhaust = fx(n3b, "Exhaust", _draw_exhaust)
	_snow3 = snow(n3b, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(8, 16), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#7e8ea4"), "sway": 2.0},
		{"count": 30, "v": Vector2(11, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#bfc9d5"), "sway": 3.0}],
		9501)
	# ---- n4: the loop in the level's own layers (dawn)
	n4 = group("Loop")
	for nm in ["sky", "dome"]:
		_layers4[nm] = sprite("places/loop_dawn_%s.png" % nm, Vector2.ZERO, n4)
	var fxm: Dictionary = LP.get("loop_fx", {})
	for nm in ["crane_light_0", "crane_light_1", "crane_light_2"]:
		var m: Dictionary = fxm.get(nm, {})
		_fx4[nm] = fx_sprite("places/fx_%s.png" % nm, int(m.get("frames", 4)), Vector2.ZERO, n4)
	for nm in ["far", "mid", "street"]:
		_layers4[nm] = sprite("places/loop_dawn_%s.png" % nm, Vector2.ZERO, n4)
	var ms: Dictionary = fxm.get("steam_s2", {})
	_fx4["steam_s2"] = fx_sprite("places/fx_steam_s2.png", int(ms.get("frames", 16)), Vector2.ZERO, n4)
	_crows = fx(n4, "Crows", _draw_crows)
	_tram = sprite("places/tram_left.png", Vector2.ZERO, n4)
	_sparks = fx(n4, "Sparks", _draw_sparks)
	for key in ["worker", "mother", "child"]:
		_people[key] = fig("number/n4_%s.png" % key, n4)
	_konrad = fig("number/n4_konrad.png", n4)
	_layers4["fg"] = sprite("places/loop_dawn_fg.png", Vector2.ZERO, n4)
	_layers4["glow"] = sprite("places/loop_dawn_glow.png", Vector2.ZERO, n4, 1, true)
	_snow4 = snow(n4, Rect2(0, 0, 640, 360), [
		{"count": 110, "v": Vector2(8, 15), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#7e8ea4"), "sway": 2.0},
		{"count": 36, "v": Vector2(11, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#bfc9d5"), "sway": 3.0}],
		9502)


func pan_x(time: float) -> float:
	var a := float(N1_PAN[0])
	var b := float(N1_PAN[1])
	return roundf(a + (b - a) * motion_k() * ease01(time, 0.0, 4.0))


func lamp_pos(time: float) -> Vector2:
	var u := ease01(time, 0.0, 4.0)
	var k := motion_k()
	var y := float(L4.get("n1_lamp_y", 178))
	# his slow sweep along the planks and the bob of his steps (about two a second)
	var bob := sin(time * 1.3) * 3.0 + absf(sin(time * PI * 1.8)) * 2.0 - 1.0
	return Vector2(roundf(220.0 + 150.0 * u * k), roundf(y + bob * k))


func stack_y(time: float) -> float:
	var top := lv(L4, "n3_stack", Vector2(382, 160)).y
	return roundf(top + float(N3_LOWER[2]) * ease01(time, float(N3_LOWER[0]), float(N3_LOWER[1])))


## Screen x of the tram's sprite (it comes in from the right and stops where the level's tram stands).
func tram_x(time: float) -> float:
	var stop := float(LP.get("loop_tram_stop_x", 362)) - 4.0
	var u := ease_out(time, float(TRAM_IN[0]), float(TRAM_IN[1]))
	return roundf(float(TRAM_IN[2]) + (stop - float(TRAM_IN[2])) * u) - n4_cam(time)


## n4: the establishing shot's slow drift (camera x in street px; reduced motion halves it).
func n4_cam(time: float) -> float:
	return roundf(N4_DRIFT * motion_k() * ease01(time, 9.5, 13.0))


func _apply(time: float) -> void:
	if n1 == null:
		return
	var sh := shot_at(time)
	n1.visible = sh == "n1"
	n2.visible = sh == "n2"
	n3a.visible = sh == "n3" and time < N3_CUT
	n3b.visible = sh == "n3" and time >= N3_CUT
	n4.visible = sh == "n4"
	var rm := reduced_motion()
	# n1: the pan along the planks, the lamp pool leading
	var px := pan_x(time)
	_plate1.position = Vector2(px, 0)
	var lp := lamp_pos(time)
	_dark1.position = lp - Vector2(640, 360)
	_glow1.position = lp - Vector2(180, 150)
	_glow1.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 51, 0.10), 0.0, 1.0))
	_beam1.position = lp - lv(L4, "n1_beam", Vector2(60, 270))
	_beam1.modulate = Color(1, 1, 1, clampf(0.85 + 0.15 * fire_wobble(time, 52, 0.4), 0.0, 1.0))
	_breath1.queue_redraw()
	_drip1.queue_redraw()
	_motes1.queue_redraw()
	# n2: the glints breathe with the flame (slow), the drip keeps running
	_glints.modulate = Color(1, 1, 1, clampf(0.55 + 0.35 * fire_wobble(time, 53, 0.4) - 0.35, 0.0, 1.0))
	_drip2.queue_redraw()
	_flakes.queue_redraw()
	# n3b: the stack goes down the shaft, the tail lights idle, exhaust, the shaft's light breathes
	var sx := lv(L4, "n3_stack", Vector2(382, 160)).x
	_stack.position = Vector2(sx, stack_y(time))
	_place_n3_people(time)
	for s in _tails:
		(s as Sprite2D).modulate = Color(1, 1, 1, 0.75 + 0.2 * hnoise(time * 1.5, 57))
	_shaft.modulate = Color(1, 1, 1, clampf(0.85 + 0.12 * hnoise(time * 1.1, 58), 0.0, 1.0))
	_chain.queue_redraw()
	_exhaust.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))
	# n4: the loop's layers drift a little (parallax), the fx run, the tram comes in, people wait
	var cam := n4_cam(time)
	var homes: Dictionary = LP.get("loop_layers", {})
	for nm in ["sky", "dome", "far", "mid", "street", "fg", "glow"]:
		var hm: Array = homes.get(nm, [0, 0, 1.0])
		(_layers4[nm] as Sprite2D).position = par_pos(Vector2(float(hm[0]), float(hm[1])), cam, float(hm[2]))
	var fxm: Dictionary = LP.get("loop_fx", {})
	for nm in _fx4:
		var m: Dictionary = fxm.get(nm, {})
		var pos: Array = m.get("pos", [0, 0])
		var s: Sprite2D = _fx4[nm]
		s.position = par_pos(Vector2(float(pos[0]), float(pos[1])), cam, float(m.get("parallax", 1.0)))
		s.frame = loop_frame(time, int(m.get("frames", 1)), float(m.get("fps", 6.0)), h01(nm.length(), 61))
	var top := float(LP.get("tram_top", 174))
	_tram.position = Vector2(tram_x(time), top)
	var feet := float(LP.get("feet", 300))
	var ik: Dictionary = L4.get("n4_konrad", {})
	var fi := 0 if rm else int(floor(maxf(0.0, time - 9.5) * 5.0))
	fig_frame(_konrad, ik, "look_side" if time > 12.1 else "idle_side", fi, Vector2(236.0 - cam, feet))
	_place_people(time, cam, feet)
	_crows.queue_redraw()
	_sparks.queue_redraw()
	_snow4.set_time(time * (0.6 if rm else 1.0))


func _place_people(time: float, cam: float, feet: float) -> void:
	var idx: Dictionary = L4.get("n4_people", {})
	var at: Dictionary = L4.get("n4_people_at", {})
	var rm := reduced_motion()
	# a woman and her boy at the shelter: they wait, then step toward the tram when it stops
	for key in ["mother", "child"]:
		var a: Array = at.get(key, [286, 300])
		var s: Sprite2D = _people[key]
		var x0 := float(a[0])
		var step := clampf((time - 12.45) * 30.0, 0.0, 14.0)
		var i0 := 0 if rm else int(floor(time * 4.0)) + (1 if key == "child" else 0)
		if step > 0.0 and step < 14.0:
			fig_frame(s, idx.get(key, {}), "walk_side", walk_i(step), Vector2(x0 + step - cam, feet))
		else:
			fig_frame(s, idx.get(key, {}), "idle_side", i0, Vector2(x0 + step - cam, feet))
	# a worker on early shift walks in from the left
	var wa: Array = at.get("worker", [196, 300])
	var wx: Array = walk_x(time, 9.6, -20.0, float(wa[0]))
	var w: Sprite2D = _people["worker"]
	if bool(wx[1]):
		fig_frame(w, idx.get("worker", {}), "walk_side", walk_i(float(wx[0]) + 20.0), Vector2(float(wx[0]) - cam, feet))
	else:
		fig_frame(w, idx.get("worker", {}), "idle_side", 0, Vector2(float(wx[0]) - cam, feet))


## The drip under the 5: length grows over the shot (plate coordinates, moves with the pan).
func drip_len(time: float, t0: float, t1: float, a: float, b: float) -> float:
	return a + (b - a) * clampf((time - t0) / (t1 - t0), 0.0, 1.0)


func _draw_drip1() -> void:
	if not n1.visible:
		return
	var d := lv(L4, "n1_drip", Vector2(900, 186))
	var len_ := drip_len(t, 0.0, 4.0, 4.0, 18.0)
	var x := d.x + _plate1.position.x
	_drip1.draw_rect(Rect2(Vector2(roundf(x), d.y), Vector2(2, roundf(len_))), Color("#d8ccaa"))
	_drip1.draw_rect(Rect2(Vector2(roundf(x) - 1, roundf(d.y + len_)), Vector2(4, 3)), Color("#b6a886"))
	_drip1.draw_rect(Rect2(Vector2(roundf(x), d.y), Vector2(1, roundf(len_))), Color("#eee4c8"))


func _draw_motes1() -> void:
	if not n1.visible:
		return
	# dust turning in the hand lamp's beam (thick near the pool, a few in the cone toward the lamp), water falling
	# from the vault through the light onto the wagon's roof
	var lp := lamp_pos(t)
	draw_motes(_motes1, _motes_tex, Rect2(lp.x - 190.0, lp.y - 130.0, 380.0, 260.0), lp, 175.0, t, 40, 5101, 1.0)
	draw_motes(_motes1, _motes_tex, Rect2(lp.x - 260.0, lp.y, 220.0, 120.0), lp + Vector2(-120, 60), 130.0, t, 14,
		5105, 0.9)
	var roof := float(L4.get("n1_lamp_y", 178)) - 106.0
	draw_drips(_motes1, lp.x - 170.0, lp.x + 170.0, 58.0, roof, t, 5, 5103, Color(1.0, 0.78, 0.48, 0.95))
	draw_drips(_motes1, lp.x - 260.0, lp.x + 260.0, 58.0, roof, t, 3, 5107, Color(0.55, 0.50, 0.46, 0.7))


## n1: Alexei's breath drifting into the beam from the lower left (he walks just out of the frame, the lamp low).
func _draw_breath1() -> void:
	if not n1.visible or _breath_tex == null:
		return
	var lp := lamp_pos(t)
	var k := motion_k()
	for j in 2:
		var period := 2.2
		var age := fposmod(t / period + 0.3 + j * 0.5, 1.0)
		if age > 0.65:
			continue
		var p := Vector2(lp.x - 230.0 + age * 70.0 * k + j * 10.0, lp.y + 70.0 - age * 40.0 * k)
		var a := 0.5 * (1.0 - age / 0.65) * clampf(age * 7.0, 0.0, 1.0)
		draw_frame(_breath1, _breath_tex, 6, int(age / 0.65 * 5.0), p, false, Color(1.0, 0.82, 0.6, a))


## n3b: the banksman beside the hatch signals the descent (looks down the shaft when the load is down); the
## driver waits by his cab.
func _place_n3_people(time: float) -> void:
	var idx: Dictionary = L4.get("n3_people", {})
	var at: Dictionary = L4.get("n3_people_at", {})
	var rm := reduced_motion()
	if _people3.has("banksman"):
		var b: Array = at.get("banksman", [292, 240])
		var bi: Dictionary = idx.get("banksman", {})
		var lowering := time >= float(N3_LOWER[0]) - 0.3 and time < float(N3_LOWER[1])
		var anim := "gesture_side" if lowering else ("look_side" if time >= float(N3_LOWER[1]) else "idle_side")
		var fi := 0 if rm else int(floor((time - N3_CUT) * (7.0 if lowering else 5.0)))
		fig_frame(_people3["banksman"], bi, anim, fi, Vector2(float(b[0]), float(b[1])))
	if _people3.has("driver"):
		var d: Array = at.get("driver", [22, 234])
		var di: Dictionary = idx.get("driver", {})
		var fd := 0 if rm else int(floor((time - N3_CUT) * 4.0)) + 1
		fig_frame(_people3["driver"], di, "look_side" if time > 8.4 else "idle_side", fd, Vector2(float(d[0]), float(d[1])))


func _draw_drip2() -> void:
	if not n2.visible:
		return
	var d := lv(L4, "macro_drip", Vector2(447, 266))
	var len_ := drip_len(t, 4.0, 5.5, 10.0, 40.0)
	_drip2.draw_rect(Rect2(Vector2(d.x - 3, d.y - 2), Vector2(7, roundf(len_))), Color("#d8ccaa"))
	_drip2.draw_rect(Rect2(Vector2(d.x - 5, roundf(d.y + len_ - 4)), Vector2(11, 8)), Color("#b6a886"))
	_drip2.draw_rect(Rect2(Vector2(d.x - 2, d.y - 2), Vector2(2, roundf(len_))), Color("#fff8e6"))


func _draw_flakes() -> void:
	if not n3a.visible or _flake_tex == null:
		return
	var k := motion_k()
	for i in 14:
		var sz := i % 4
		var sp := (18.0 + sz * 9.0) * k
		var x0 := fposmod(i * 97.3, 680.0) - 20.0
		var y0 := fposmod(i * 53.7, 400.0) - 20.0
		var p := Vector2(fposmod(x0 + (t - 5.5) * sp * 0.4, 680.0) - 20.0, fposmod(y0 + (t - 5.5) * sp, 400.0) - 20.0)
		_flakes.draw_texture_rect_region(_flake_tex, Rect2(p.round(), Vector2(28, 28)), Rect2(sz * 28, 0, 28, 28),
			Color(1, 1, 1, 0.8))


func _draw_chain() -> void:
	if not n3b.visible:
		return
	var a := lv(L4, "n3_chain", Vector2(441, 122))
	var top := Vector2(_stack.position.x + 58, _stack.position.y)
	# the lift chain: its links travel down with the load (phase = how far it has gone)
	var gone := _stack.position.y - lv(L4, "n3_stack", Vector2(382, 160)).y
	var ph := int(floor(gone / 3.0))
	var n := int(absf(top.y - a.y) / 3.0)
	for i in n:
		var p := a.lerp(top, float(i) / maxf(1.0, float(n)))
		_chain.draw_rect(Rect2(p.round(), Vector2(2, 2)), Color("#5a6266") if (i + ph) % 2 == 0 else Color("#3d4645"))
	# the hand chain: a loop from the block's wheel down into the shaft, pulled from below -- one strand runs
	# down, the other up while the load goes down
	var hc := lv(L4, "n3_hand_chain", Vector2(502, 124))
	var hatch: Array = L4.get("n3_hatch", [360, 276, 520, 292])
	var bottom := float(hatch[1]) + 2.0
	var run := int(floor(gone * 1.6 / 2.0))
	for strand in 2:
		var x := hc.x + strand * 4.0
		var dir := 1 if strand == 0 else -1
		var y := hc.y
		var li := 0
		while y < bottom:
			var c := Color("#6a7276") if posmod(li + run * dir, 2) == 0 else Color("#2e3434")
			_chain.draw_rect(Rect2(Vector2(x, y), Vector2(1, 2)), c)
			y += 2.0
			li += 1
	_chain.draw_rect(Rect2(hc + Vector2(-2, -2), Vector2(9, 3)), Color("#2a3032"))   # the hand wheel's guard
	# the lamp on the site hoarding blinks (once a second, never faster)
	var b := lv(L4, "n3_blinker", Vector2(602, 138))
	if fposmod(t, 1.0) < 0.5:
		_chain.draw_rect(Rect2(b - Vector2(2, 1), Vector2(5, 3)), Color("#f0a830"))
		_chain.draw_rect(Rect2(b - Vector2(1, 0), Vector2(3, 1)), Color("#ffe0a0"))


func _draw_exhaust() -> void:
	if not n3b.visible or _exhaust_tex == null:
		return
	var e := lv(L4, "n3_exhaust", Vector2(232, 262))
	var k := motion_k()
	for i in 3:
		var age := fposmod(t * 0.7 + i * 0.33, 1.0)
		var p := e + Vector2(age * 34.0 * k, -age * 18.0 * k)
		draw_frame(_exhaust, _exhaust_tex, 6, int(age * 5.0), p, false, Color(1, 1, 1, 0.7 * (1.0 - age)))


## Crows on the contact wire over the tram's stop; they lift off as the tram comes in (frames 0-6 perched,
## 7-10 flying, the level's crow sheet).
func _draw_crows() -> void:
	if not n4.visible or _crow_tex == null:
		return
	var wire := float(LP.get("loop_wire_y", 176))
	var cam := n4_cam(t)
	var n := maxi(1, _crow_tex.get_width() / 14)
	for i in 4:
		var x0 := 470.0 + i * 15.0 + h01(i, 71) * 6.0
		var t0 := CROWS_UP + i * 0.18
		if t < t0:
			var f := 0 if fposmod(t * 0.8 + h01(i, 73), 1.0) < 0.8 else 1 + (i % 3)
			draw_cell(_crows, _crow_tex, n, f, Vector2(x0 - cam - 7.0, wire - 11.0))
		else:
			var u := t - t0
			var p := Vector2(x0 - u * (60.0 + i * 8.0), wire - 11.0 - u * (46.0 + i * 6.0) + sin(u * 9.0) * 2.0)
			if p.y > -12.0:
				draw_cell(_crows, _crow_tex, n, 7 + int(floor(u * 10.0)) % 4, p - Vector2(cam, 0))


## Blue-white sparks where the tram's bow runs on the wire (only while it moves).
func _draw_sparks() -> void:
	if not n4.visible:
		return
	if t < float(TRAM_IN[0]) or t > float(TRAM_IN[1]) - 0.2:
		return
	var sz: Array = LP.get("tram_size", [250, 122])
	var bx := _tram.position.x + float(sz[0]) * 0.5 - 2.0
	var by := _tram.position.y + 1.0
	if hnoise(t * 23.0, 77) > 0.62:
		_sparks.draw_rect(Rect2(Vector2(bx - 1, by - 1), Vector2(3, 2)), Color("#d8e8ff"))
		_sparks.draw_rect(Rect2(Vector2(bx + 2, by - 3), Vector2(1, 1)), Color("#a8c8ff"))
