extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Number (13 s) — the first match cut, on the wagon number C-17/45 (C4_DESIGN §2.9).
##   n1  0-4      Service tunnel 3: Alexei's lamp along the planks of wagon 24 318; the fresh red-brown paint,
##                the tin stencil still taped on, the wet C-17/45, a drip runs down; chalk: „ВТ 23.40“ (pan)
##   n2  4-5.5    macro: the stencilled 45, wet; the drip                               -- hard cut on the 45 --
##   n3  5.5-9.5  Berlin at dawn: the SAME 45 black on a pine crate, snow in the air (n3a, to 6.7) -> the loading
##                hatch: the lorry's tail lights, the stack of crates goes down the shaft (n3b)
##   n4  9.5-13   the tram loop Süd 8: the first tram of line 74 rings and stops; Konrad at the shelter
## Lines: the time in Karsk, Alexei's line, the time in Berlin (same moment: Moscow time is Berlin + 2).

const DUR := 13.0
const SHOTS := [["n1", 0.0, 4.0], ["n2", 4.0, 5.5], ["n3", 5.5, 9.5], ["n4", 9.5, 13.0]]
const LINES := ["cin.c4.number.karsk", "cin.c4.number.alexei", "cin.c4.number.berlin"]
const N1_PAN := [-40.0, -400.0]        # plate x offset from .. to (reduced motion halves the travel)
const N3_CUT := 6.7                    # n3a macro -> n3b hatch
const N3_LOWER := [7.1, 9.3, 150.0]    # the stack goes down: from, to, depth px
const TRAM_IN := [9.9, 12.3, 660.0]    # the tram enters: from, stops at, start x
const TRAM_BELL := 11.4                # its bell (c4cine_tram, tests compare)

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
var _drip1: Node2D
var _glints: Sprite2D
var _drip2: Node2D
var _flakes: Node2D
var _flake_tex: Texture2D
var _stack: Sprite2D
var _chain: Node2D
var _tails: Array = []
var _exhaust: Node2D
var _exhaust_tex: Texture2D
var _snow3: Node2D
var _tram: Sprite2D
var _konrad: Sprite2D
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
	n1 = group("Tunnel")
	_plate1 = sprite("number/n1_wagon.png", Vector2.ZERO, n1)
	_drip1 = fx(n1, "Drip", _draw_drip1)
	_glow1 = sprite("number/n1_glow.png", Vector2.ZERO, n1, 1, true)
	_dark1 = sprite("number/n1_dark.png", Vector2.ZERO, n1)
	n2 = group("Macro")
	sprite("number/n2_macro.png", Vector2.ZERO, n2)
	_glints = sprite("number/n2_glints.png", Vector2.ZERO, n2, 1, true)
	_drip2 = fx(n2, "Drip", _draw_drip2)
	n3a = group("Crate")
	sprite("number/n3a_macro.png", Vector2.ZERO, n3a)
	_flakes = fx(n3a, "Flakes", _draw_flakes)
	n3b = group("Hatch")
	sprite("number/n3b_hatch.png", Vector2.ZERO, n3b)
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
	n4 = group("Loop")
	sprite("places/loop_dawn.png", Vector2.ZERO, n4)
	sprite("places/loop_glow_dawn.png", Vector2.ZERO, n4, 1, true)
	_konrad = fig("number/n4_konrad.png", n4)
	_tram = sprite("places/tram_left.png", Vector2.ZERO, n4)
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
	return Vector2(roundf(220.0 + 150.0 * u * motion_k()), roundf(178.0 + sin(time * 1.3) * 3.0 * motion_k()))


func stack_y(time: float) -> float:
	var top := lv(L4, "n3_stack", Vector2(382, 160)).y
	return roundf(top + float(N3_LOWER[2]) * ease01(time, float(N3_LOWER[0]), float(N3_LOWER[1])))


func tram_x(time: float) -> float:
	var stop := 352.0
	var u := ease_out(time, float(TRAM_IN[0]), float(TRAM_IN[1]))
	return roundf(float(TRAM_IN[2]) + (stop - float(TRAM_IN[2])) * u)


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
	_drip1.queue_redraw()
	# n2: the glints breathe with the flame (slow), the drip keeps running
	_glints.modulate = Color(1, 1, 1, clampf(0.55 + 0.35 * fire_wobble(time, 53, 0.4) - 0.35, 0.0, 1.0))
	_drip2.queue_redraw()
	_flakes.queue_redraw()
	# n3b: the stack goes down the shaft, the tail lights idle, exhaust
	var sx := lv(L4, "n3_stack", Vector2(382, 160)).x
	_stack.position = Vector2(sx, stack_y(time))
	for s in _tails:
		(s as Sprite2D).modulate = Color(1, 1, 1, 0.75 + 0.2 * hnoise(time * 1.5, 57))
	_chain.queue_redraw()
	_exhaust.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))
	# n4: the tram comes in and stops; Konrad waits at the shelter, looking at it
	_tram.position = Vector2(tram_x(time), 300.0 - 96.0 + 8.0)
	var ik: Dictionary = L4.get("n4_konrad", {})
	var fi := 0 if rm else int(floor(maxf(0.0, time - 9.5) * 5.0))
	fig_frame(_konrad, ik, "idle_side", fi, Vector2(236, float(LP.get("feet", 300))))
	_snow4.set_time(time * (0.6 if rm else 1.0))


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
	var n := int(absf(top.y - a.y) / 3.0)
	for i in n:
		var p := a.lerp(top, float(i) / maxf(1.0, float(n)))
		_chain.draw_rect(Rect2(p.round(), Vector2(2, 2)), Color("#5a6266") if i % 2 == 0 else Color("#3d4645"))


func _draw_exhaust() -> void:
	if not n3b.visible or _exhaust_tex == null:
		return
	var e := lv(L4, "n3_exhaust", Vector2(232, 262))
	var k := motion_k()
	for i in 3:
		var age := fposmod(t * 0.7 + i * 0.33, 1.0)
		var p := e + Vector2(age * 34.0 * k, -age * 18.0 * k)
		draw_frame(_exhaust, _exhaust_tex, 6, int(age * 5.0), p, false, Color(1, 1, 1, 0.7 * (1.0 - age)))
