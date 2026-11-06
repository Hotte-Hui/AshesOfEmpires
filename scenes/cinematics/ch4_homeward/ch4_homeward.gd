extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Homeward (14 s) — homeward, each with his half of the file (C4_DESIGN §2.9).
##   w1  0-5     Veltrava station at first light, down the island platform: the westbound to Berlin (left), the
##               eastbound to Karsk (right); Konrad and Alexei walk up the platform side by side, part and board
##               on opposite sides; steam rises at the far end
##   w2  5-9     split windows: Konrad's carriage passes under the dome of the Great Hall (left), Alexei's crosses
##               the snow plain toward the cooling towers of Karsk (right) -- the landscapes run apart
##   w3  9-14    Karsk freight yard before dawn, the repaired signal green: Alexei walks to the lit cellar window
##               of the freight office (the level then opens in that cellar)
## Lines: Alexei's thought per ctx.choices.c3g_choose (split / swap / elena; default split), then the place.
## Art: tools/pixelgen/env_c4_cine_homeward.py + env_c4_cine_places.py -> assets/cinematics/c4/.

const DUR := 14.0
const SHOTS := [["w1", 0.0, 5.0], ["w2", 5.0, 9.0], ["w3", 9.0, 14.0]]
const LINE_PLACE := "cin.c4.homeward.place"
const W1_WALK := [0.3, 2.9]            # both walk up the platform
const W1_BOARD := [2.9, 3.3, 3.7]      # turn to the door, step up, inside
const W1_START_K := Vector2(304, 312)
const W1_START_A := Vector2(338, 312)
const W2_SPEED := [150.0, 10.0]        # near / far scroll px/s (reduced motion halves both)
const W3_T0 := 9.1                     # Alexei starts walking (in-game speed)
const DOOR_SLAMS := [3.75, 4.05]       # carriage doors (c4cine_station; tests compare with the audio tool)

var line_c3g := "cin.c4.homeward.alexei.split"
var L4: Dictionary = {}
var LP: Dictionary = {}
var w1: Node2D
var w2: Node2D
var w3: Node2D
var _k1: Sprite2D
var _a1: Sprite2D
var _steam1: Node2D
var _strips: Array = []
var _a3: Sprite2D
var _w3fx: Node2D
var _warm3: Sprite2D
var _snow3: Node2D
var _steam_tex: Texture2D
var _breath_tex: Texture2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func _on_configured() -> void:
	match choice("c3g_choose"):
		"swap_halves":
			line_c3g = "cin.c4.homeward.alexei.swap"
		"hide_for_elena":
			line_c3g = "cin.c4.homeward.alexei.elena"
		_:
			line_c3g = "cin.c4.homeward.alexei.split"


func chosen_lines() -> Array:
	return [line_c3g, LINE_PLACE]


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c4cine_station", "db": -6.0},
		say_at(line_c3g, 0.8),
		{"t": 5.0, "bed": "c4cine_rails", "db": -7.0},
		{"t": 9.0, "bed": "c4cine_yard", "db": -6.0},
		say_at(LINE_PLACE, 9.5),
	]


func _build() -> void:
	L4 = _layout_section("homeward")
	LP = _layout_section("places")
	_steam_tex = tex("places/steam.png")
	_breath_tex = tex("places/breath.png")
	w1 = group("Station")
	sprite("homeward/w1_station.png", Vector2.ZERO, w1)
	sprite("homeward/w1_glow.png", Vector2.ZERO, w1, 1, true)
	_steam1 = fx(w1, "Steam", _draw_steam1)
	_k1 = fig("homeward/w1_konrad.png", w1)
	_a1 = fig("homeward/w1_alexei.png", w1)
	w2 = group("Windows")
	var wk := lv(L4, "win_k", Vector2(36, 70))
	var wa := lv(L4, "win_a", Vector2(340, 70))
	var ww := 264
	sprite("homeward/w2_sky_berlin.png", wk, w2)
	_strips.append(window_strip("homeward/w2_far_berlin.png", wk, ww, w2))
	_strips.append(window_strip("homeward/w2_near_berlin.png", wk, ww, w2))
	sprite("homeward/w2_sky_karsk.png", wa, w2)
	_strips.append(window_strip("homeward/w2_far_karsk.png", wa, ww, w2))
	_strips.append(window_strip("homeward/w2_near_karsk.png", wa, ww, w2))
	sprite("homeward/w2_frames.png", Vector2.ZERO, w2)
	w3 = group("Yard")
	sprite("places/yard.png", Vector2.ZERO, w3)
	sprite("places/yard_green.png", Vector2.ZERO, w3, 1, true)
	_warm3 = sprite("places/yard_warm.png", Vector2.ZERO, w3, 1, true)
	_a3 = fig("homeward/w3_alexei.png", w3)
	_w3fx = fx(w3, "Breath", _draw_w3)
	sprite("places/yard_parapet.png", Vector2.ZERO, w3)
	_snow3 = snow(w3, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#465564"), "sway": 2.0},
		{"count": 30, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#7e8b96"), "sway": 3.0}],
		9401)


func _apply(time: float) -> void:
	if w1 == null:
		return
	var sh := shot_at(time)
	w1.visible = sh == "w1"
	w2.visible = sh == "w2"
	w3.visible = sh == "w3"
	var rm := reduced_motion()
	var k := motion_k()
	# ---- w1: up the platform, part, board
	var ik: Dictionary = L4.get("w1_konrad", {})
	var ia: Dictionary = L4.get("w1_alexei", {})
	var dk := lv(L4, "door_k", Vector2(248, 266))
	var da := lv(L4, "door_a", Vector2(392, 266))
	_place_boarder(_k1, ik, time, W1_START_K, dk, "walk_side_l", -1.0)
	_place_boarder(_a1, ia, time, W1_START_A, da, "walk_side", 1.0)
	_steam1.queue_redraw()
	# ---- w2: the two landscapes run apart
	var dt := maxf(0.0, time - 5.0)
	var near_v := float(W2_SPEED[0]) * k
	var far_v := float(W2_SPEED[1]) * k
	if _strips.size() == 4:
		set_scroll(_strips[0], 60.0 - dt * far_v)          # Berlin: scenery runs to the right
		set_scroll(_strips[1], -dt * near_v)
		set_scroll(_strips[2], 300.0 + dt * far_v)         # Karsk: scenery runs to the left
		set_scroll(_strips[3], dt * near_v * 1.1)
	# ---- w3: Alexei walks to the cellar window
	var walk: Array = L4.get("w3_walk", [230, 466])
	var x0 := float(walk[0]) + 38.0
	var x1 := float(walk[1])
	var wx: Array = walk_x(time, W3_T0, x0, x1)
	var feet := float(LP.get("feet", 300))
	var i3: Dictionary = L4.get("w3_alexei", {})
	if bool(wx[1]):
		fig_frame(_a3, i3, "walk_side", walk_i(float(wx[0]) - x0), Vector2(float(wx[0]), feet))
	elif time < W3_T0:
		fig_frame(_a3, i3, "idle_side", 0, Vector2(x0, feet))
	else:
		var since := time - (W3_T0 + (x1 - x0) / WALK_SPEED)
		var fi := 0 if rm else int(floor(since * 5.0))
		fig_frame(_a3, i3, "look_side" if since > 0.15 else "idle_side", fi, Vector2(x1, feet))
	_warm3.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 41, 0.08), 0.0, 1.0))
	_w3fx.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))


## w1: walk up the platform (back view), turn toward the door, step up, gone inside.
func _place_boarder(s: Sprite2D, idx: Dictionary, time: float, start: Vector2, door: Vector2, side_anim: String,
		dirx: float) -> void:
	var t0 := float(W1_WALK[0])
	var t1 := float(W1_WALK[1])
	var u := ease01(time, t0, t1)
	var stop := Vector2(door.x - dirx * 10.0, door.y + 4.0)
	var p := start.lerp(stop, u)
	s.visible = time < float(W1_BOARD[2])
	if time < t1:
		var walked := (time - t0) * 22.0 if time > t0 else 0.0
		fig_frame(s, idx, "walk_back", int(floor(walked / 2.6)) if time > t0 else 0, p)
	elif time < float(W1_BOARD[1]):
		fig_frame(s, idx, side_anim, 1, stop)
	else:
		var v := ease01(time, float(W1_BOARD[1]), float(W1_BOARD[2]))
		fig_frame(s, idx, side_anim, 3 + int(v * 3.0), stop + Vector2(dirx * 8.0 * v, -5.0 * v))


func _draw_steam1() -> void:
	if not w1.visible or _steam_tex == null:
		return
	var k := motion_k()
	var pts: Array = L4.get("w1_steam", [[262, 150], [378, 150]])
	for j in pts.size():
		var pp: Array = pts[j]
		for i in 4:
			var age := fposmod(t * 0.28 + j * 0.37 + i * 0.25, 1.0)
			var pos := Vector2(float(pp[0]) + (j * 2 - 1) * age * 18.0 * k, float(pp[1]) - age * 46.0 * k)
			draw_frame(_steam1, _steam_tex, 8, int(age * 7.0), pos, false, Color(1, 1, 1, 0.75 * (1.0 - age)))


func _draw_w3() -> void:
	if not w3.visible or _breath_tex == null:
		return
	var period := 2.3
	var age := fposmod(t + 0.4, period) / period
	if age > 0.6:
		return
	var head := _a3.position + Vector2(24, 14)
	var p := head + Vector2(age * 8.0, -age * 14.0 * motion_k())
	draw_frame(_w3fx, _breath_tex, 6, int(age / 0.6 * 5.0), p, false, Color(1, 1, 1, 0.5 * (1.0 - age / 0.6)))
