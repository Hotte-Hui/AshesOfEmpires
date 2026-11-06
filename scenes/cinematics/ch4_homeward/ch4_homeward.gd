extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Homeward (14 s) — homeward, each with his half of the file (C4_DESIGN §2.9).
##   w1  0-5     Veltrava station at first light, down platform 5 under the iron shed (a ray-cast plate in which the
##               game's own figures stand at their true size): the westbound to Berlin (left), the eastbound to Karsk
##               (right); Konrad and Alexei walk up the platform side by side, part and board on opposite sides, the
##               doors slam; around them the conductors at their doors, a mother and her boy hurrying to the Berlin
##               train, a porter crossing, an old woman with her bundles; the locomotives' steam at the far end,
##               steam leaking from the carriages' heating, the globes over the platform
##   w2  5-9     split windows: Konrad's compartment (walnut, brass, a reading lamp) passes under the dome of the Great
##               Hall -- tenements and catenary masts rush by; Alexei's (green panels, lace curtain, a glass of tea)
##               crosses the snow plain toward the cooling towers of Karsk -- birches, a village, telegraph poles;
##               three depths per window running apart, snow streaking the glass, the carriages swaying
##   w3  9-14    Karsk freight yard before dawn, the repaired signal green: Alexei walks to the lit cellar window of the
##               freight office, the camera tracking him across the layered yard (the level then opens in that cellar)
## Round 10: boarding is boarding -- each man walks to his door's threshold, steps up and in and is hidden by the
## near jamb of the opening (fig_frame_clip, layout w1_open_*), before his door slams; the mother and her boy board
## the next door of the Berlin train (open in the plate) the same way; the conductors stand clear of the openings.
## In w2 the tea glass stands whole on the sill, its spoon rattles in it; the men's faces float in their windows.
## Lines: Alexei's thought per ctx.choices.c3g_choose (split / swap / elena; default split), then the place.
## Art: tools/pixelgen/env_c4_cine_homeward.py, env_c4_cine_station.py, env_c4_cine_yard.py -> assets/cinematics/c4/.

const DUR := 14.0
const SHOTS := [["w1", 0.0, 5.0], ["w2", 5.0, 9.0], ["w3", 9.0, 14.0]]
const LINE_PLACE := "cin.c4.homeward.place"
const W1_WALK := [0.3, 1.9]            # both walk up the platform (from their start marks to the parting point)
const W1_PART := [1.9, 2.0]            # Konrad / Alexei turn toward their doors at these times
const W1_BOARD := [3.45, 3.55]         # each steps up into his door (Konrad, Alexei); gone 0.3 s later
const W1_UP := 15.0                    # px the two walk up the platform before they part
const W1_IN := 0.3                     # stepping up into the vestibule takes this long (then the jamb hides them)
const W2_SPEED := [150.0, 10.0]        # near / far scroll px/s (reduced motion halves both); mid runs at 60
const W3_T0 := 9.1                     # Alexei starts walking (in-game speed)
const W3_CAM := [9.3, 13.6]            # the camera tracks him between these times
const DOOR_SLAMS := [3.75, 4.05]       # carriage doors (c4cine_station; tests compare with the audio tool)

var line_c3g := "cin.c4.homeward.alexei.split"
var L4: Dictionary = {}
var LP: Dictionary = {}
var w1: Node2D
var w2: Node2D
var w3: Node2D
var _k1: Sprite2D
var _a1: Sprite2D
var _glow1: Sprite2D
var _steam1: Node2D
var _doors: Array = []
var _npc: Dictionary = {}
var _strips: Array = []
var _refl: Array = []
var _w2fx: Node2D
var _a3: Sprite2D
var _w3fx: Node2D
var _warm3: Sprite2D
var _snow3: Node2D
var _yard: Dictionary = {}
var _steam_tex: Texture2D
var _steam_light: Texture2D
var _breath_tex: Texture2D
var _smoke_tex: Texture2D
var _streak_tex: Texture2D


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
	_steam_light = tex("places/steam_light.png")
	_breath_tex = tex("places/breath.png")
	_smoke_tex = tex("places/smoke.png")
	_streak_tex = tex("homeward/w2_streaks.png")
	# ---- w1: the station
	w1 = group("Station")
	sprite("homeward/w1_station.png", Vector2.ZERO, w1)
	_glow1 = sprite("homeward/w1_glow.png", Vector2.ZERO, w1, 1, true)
	_steam1 = fx(w1, "Steam", _draw_steam1)
	_steam1.z_index = 1
	for key in ["k", "a"]:
		var d := sprite("homeward/w1_door_%s.png" % key, lv(L4, "w1_door_%s_at" % key), w1, 2)
		d.z_index = 2
		_doors.append(d)
	for key in ["conductor_k", "conductor_a", "porter", "mother", "child", "babushka"]:
		_npc[key] = fig("homeward/w1_%s.png" % key, w1)
	_k1 = fig("homeward/w1_konrad.png", w1)
	_a1 = fig("homeward/w1_alexei.png", w1)
	# ---- w2: the two windows, three depths each, the interiors over them
	w2 = group("Windows")
	var wk := lv(L4, "win_k", Vector2(36, 70))
	var wa := lv(L4, "win_a", Vector2(340, 70))
	var ww := 264
	for pair in [["berlin", wk], ["karsk", wa]]:
		var city: String = pair[0]
		var at: Vector2 = pair[1]
		sprite("homeward/w2_sky_%s.png" % city, at, w2)
		_strips.append(window_strip("homeward/w2_far_%s.png" % city, at, ww, w2))
		_strips.append(window_strip("homeward/w2_mid_%s.png" % city, at, ww, w2))
		_strips.append(window_strip("homeward/w2_near_%s.png" % city, at, ww, w2))
	for pair in [["berlin", wk], ["karsk", wa]]:
		var r := sprite("homeward/w2_refl_%s.png" % str(pair[0]), pair[1], w2, 1, true)
		_refl.append(r)
	_w2fx = fx(w2, "Glass", _draw_w2)
	sprite("homeward/w2_frames.png", Vector2.ZERO, w2)
	# ---- w3: the yard in parallax layers
	w3 = group("Yard")
	for nm in ["sky", "far", "mid", "main"]:
		_yard[nm] = sprite("places/yard_l_%s.png" % nm, Vector2.ZERO, w3)
	_yard["green"] = sprite("places/yard_l_green.png", Vector2.ZERO, w3, 1, true)
	_warm3 = sprite("places/yard_l_warm.png", Vector2.ZERO, w3, 1, true)
	_yard["warm"] = _warm3
	_a3 = fig("homeward/w3_alexei.png", w3)
	_w3fx = fx(w3, "Breath", _draw_w3)
	_yard["parapet"] = sprite("places/yard_l_parapet.png", Vector2.ZERO, w3)
	_snow3 = snow(w3, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#465564"), "sway": 2.0},
		{"count": 30, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#7e8b96"), "sway": 3.0}],
		9401)


# ------------------------------------------------------------------ w1 choreography (pure functions of t)
func _anim(key: String) -> Dictionary:
	var a: Dictionary = L4.get("w1_npc_anims", {})
	var d = a.get(key, {})
	return d if d is Dictionary else {}


func _npc_at(key: String, fallback: Vector2) -> Vector2:
	var n: Dictionary = L4.get("w1_npc", {})
	var v = n.get(key)
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return fallback


## Feet position of a boarding man at `time`: up the platform, then across to his door's threshold, then up the
## step into the vestibule (`inside`; default: half a metre in and up the step, toward his train's side).
func boarder_feet(time: float, start: Vector2, door: Vector2, t_part: float, t_board: float,
		inside := Vector2.INF) -> Vector2:
	var up := start + Vector2(0, -W1_UP)
	if time < t_part:
		return start.lerp(up, ease01(time, float(W1_WALK[0]), float(W1_WALK[1])))
	if time < t_board:
		var u := clampf((time - t_part) / (t_board - t_part), 0.0, 1.0)
		return up.lerp(door, u)
	var into := inside if inside.is_finite() else door + Vector2(signf(door.x - 320.0) * 20.0, -13.0)
	return door.lerp(into, ease01(time, t_board, t_board + W1_IN))


## What a boarder is seen through while he steps in: the door's opening [x0, y0, x1, y1]; the near jamb (the
## outer side: left for the Berlin train, right for the Karsk one) hides him, the far jamb closes in as he gets
## inside (v 0..1).
func door_clip(opening: Array, side: float, v: float) -> Rect2:
	var x0 := float(opening[0])
	var x1 := float(opening[2])
	var y0 := float(opening[1])
	var y1 := float(opening[3])
	if side < 0.0:
		var right := lerpf(x1 + 18.0, x1, v)
		return Rect2(x0, y0, right - x0, y1 - y0)
	var left := lerpf(x0 - 18.0, x0, v)
	return Rect2(left, y0, x1 - left, y1 - y0)


func _place_boarder(s: Sprite2D, idx: Dictionary, time: float, start: Vector2, door: Vector2, t_part: float,
		t_board: float, side_anim: String, inside := Vector2.INF, opening: Array = []) -> void:
	var p := boarder_feet(time, start, door, t_part, t_board, inside)
	s.visible = time < t_board + W1_IN + 0.05
	s.z_index = int(p.y) if time < t_board else int(door.y)
	if time < t_part:
		var walking := time > float(W1_WALK[0]) and time < float(W1_WALK[1])
		fig_frame_clip(s, idx, "walk_back", int(floor(time * 9.0)) if walking else 0, p, NO_CLIP)
	elif time < t_board:
		fig_frame_clip(s, idx, side_anim, walk_i(p.distance_to(start + Vector2(0, -W1_UP))), p, NO_CLIP)
	else:
		var v := ease01(time, t_board, t_board + W1_IN)
		var walked := p.distance_to(start + Vector2(0, -W1_UP)) + v * 20.0
		var clip := door_clip(opening, signf(door.x - 320.0), v) if opening.size() >= 4 else NO_CLIP
		fig_frame_clip(s, idx, side_anim, walk_i(walked), p, clip)


func _place_npcs(time: float) -> void:
	var rm := reduced_motion()
	var idle_i := 0 if rm else int(floor(time * 5.0))
	# the two conductors at their doors, each signalling once for departure
	var ck := _npc_at("conductor_k", Vector2(211, 299))
	var s: Sprite2D = _npc["conductor_k"]
	var g := time > 2.6 and time < 3.4
	fig_frame(s, _anim("conductor_k"), "gesture_side" if g else "idle_side",
		int(floor((time - 2.6) * 8.0)) if g else idle_i, ck)
	s.z_index = int(ck.y)
	var ca := _npc_at("conductor_a", Vector2(427, 295))
	s = _npc["conductor_a"]
	g = time > 2.9 and time < 3.7
	fig_frame(s, _anim("conductor_a"), "gesture_side_l" if g else "idle_side_l",
		int(floor((time - 2.9) * 8.0)) if g else idle_i + 2, ca)
	s.z_index = int(ca.y)
	# the porter crossing the near platform from the right
	var pp := _npc_at("porter", Vector2(366, 311))
	var px0 := pp.x + 74.0
	var wx: Array = walk_x(time, 0.2, px0, px0 - 400.0, 40.0)
	s = _npc["porter"]
	var feet := Vector2(float(wx[0]), pp.y + 1.0)
	fig_frame(s, _anim("porter"), "walk_side_l", walk_i(float(wx[0]) - px0), feet)
	s.visible = feet.x > -20.0
	s.z_index = int(feet.y)
	# a mother and her boy hurrying across to the next door of the Berlin train: up the step, in, gone
	var dm := lv(L4, "door_m", Vector2(225, 265))
	var im := lv(L4, "w1_in_m", Vector2(209, 254))
	var om: Array = L4.get("w1_open_m", [220, 187, 226, 273])
	for pair in [["mother", 0.3, 0.0, 70.0], ["child", 0.45, 16.0, 72.0]]:
		var key: String = pair[0]
		var t0: float = pair[1]
		var x0 := 395.0 + float(pair[2])
		var spd: float = pair[3]
		s = _npc[key]
		var span := x0 - dm.x
		var d := clampf((time - t0) * spd, 0.0, span)
		var t_in := t0 + span / spd
		s.visible = time < t_in + W1_IN + 0.05
		if time < t_in:
			var f := Vector2(x0 - d, roundf(lerpf(dm.y + 5.0, dm.y, d / maxf(1.0, span))))
			fig_frame_clip(s, _anim(key), "walk_side_l", walk_i(d), f, NO_CLIP)
			s.z_index = int(f.y)
		else:
			var v := ease01(time, t_in, t_in + W1_IN)
			fig_frame_clip(s, _anim(key), "walk_side_l", walk_i(span + v * 20.0), dm.lerp(im, v).round(),
				door_clip(om, -1.0, v))
			s.z_index = int(dm.y)
	# the old woman with her bundles waits by the Karsk train
	s = _npc["babushka"]
	var bf := _npc_at("babushka", Vector2(449, 315))
	fig_frame(s, _anim("babushka"), "idle_side", idle_i + 1, bf)
	s.z_index = int(bf.y)


func _apply(time: float) -> void:
	if w1 == null:
		return
	var sh := shot_at(time)
	w1.visible = sh == "w1"
	w2.visible = sh == "w2"
	w3.visible = sh == "w3"
	var rm := reduced_motion()
	var k := motion_k()
	# ---- w1: up the platform, part, board; the doors slam; the people around them
	var ik: Dictionary = L4.get("w1_konrad", {})
	var ia: Dictionary = L4.get("w1_alexei", {})
	var sk := lv(L4, "w1_start_k", Vector2(298, 307))
	var sa := lv(L4, "w1_start_a", Vector2(342, 307))
	var dk := lv(L4, "door_k", Vector2(208, 284))
	var da := lv(L4, "door_a", Vector2(432, 284))
	_place_boarder(_k1, ik, time, sk, dk, float(W1_PART[0]), float(W1_BOARD[0]), "walk_side_l",
		lv(L4, "w1_in_k", Vector2(188, 271)), L4.get("w1_open_k", [201, 192, 209, 295]))
	_place_boarder(_a1, ia, time, sa, da, float(W1_PART[1]), float(W1_BOARD[1]), "walk_side",
		lv(L4, "w1_in_a", Vector2(452, 271)), L4.get("w1_open_a", [431, 192, 439, 295]))
	for i in 2:
		(_doors[i] as Sprite2D).frame = 1 if time >= float(DOOR_SLAMS[i]) else 0
	_place_npcs(time)
	_glow1.modulate = Color(1, 1, 1, clampf(0.92 + 0.06 * hnoise(time * 1.3, 81), 0.0, 1.0))
	_steam1.queue_redraw()
	# ---- w2: the landscapes run apart (Berlin to the right, Karsk to the left), the carriages sway
	var dt := maxf(0.0, time - 5.0)
	var near_v := float(W2_SPEED[0]) * k
	var far_v := float(W2_SPEED[1]) * k
	var mid_v := 60.0 * k
	if _strips.size() == 6:
		set_scroll(_strips[0], 60.0 - dt * far_v)
		set_scroll(_strips[1], -dt * mid_v)
		set_scroll(_strips[2], -dt * near_v)
		set_scroll(_strips[3], 300.0 + dt * far_v)
		set_scroll(_strips[4], dt * mid_v * 1.1)
		set_scroll(_strips[5], dt * near_v * 1.1)
		var wk := lv(L4, "win_k", Vector2(36, 70))
		var wa := lv(L4, "win_a", Vector2(340, 70))
		var bob_k := 0.0 if rm else roundf(sin(dt * 7.0) * 0.6 + sin(dt * 2.3) * 0.5)
		var bob_a := 0.0 if rm else roundf(sin(dt * 6.1 + 1.0) * 0.6 + sin(dt * 2.9) * 0.5)
		for i in 3:
			(_strips[i] as Sprite2D).position = wk + Vector2(0, bob_k)
			(_strips[3 + i] as Sprite2D).position = wa + Vector2(0, bob_a)
		# the faces in the glass sway with the carriage a little less than the land (they are inside)
		if _refl.size() == 2:
			(_refl[0] as Sprite2D).position = wk + Vector2(0, roundf(bob_k * 0.5))
			(_refl[1] as Sprite2D).position = wa + Vector2(0, roundf(bob_a * 0.5))
			var fl := 0.0 if rm else 0.06 * sin(dt * 9.0)
			(_refl[0] as Sprite2D).modulate = Color(1, 1, 1, clampf(0.9 + fl, 0.0, 1.0))
			(_refl[1] as Sprite2D).modulate = Color(1, 1, 1, clampf(0.9 - fl, 0.0, 1.0))
	_w2fx.queue_redraw()
	# ---- w3: Alexei walks to the cellar window; the camera tracks him across the parallax layers
	var cam := yard_cam(time)
	var par: Dictionary = (LP.get("yard_layers", {}) as Dictionary).get("par", {})
	for nm in ["sky", "far", "mid", "main"]:
		(_yard[nm] as Sprite2D).position = par_pos(Vector2.ZERO, cam, float(par.get(nm, 1.0)))
	for nm in ["green", "warm", "parapet"]:
		(_yard[nm] as Sprite2D).position = par_pos(Vector2.ZERO, cam, 1.0)
	var walk: Array = L4.get("w3_walk", [230, 466])
	var x0 := float(walk[0]) + 38.0
	var x1 := float(walk[1])
	var wx: Array = walk_x(time, W3_T0, x0, x1)
	var feet := float(LP.get("feet", 300))
	var i3: Dictionary = L4.get("w3_alexei", {})
	if bool(wx[1]):
		fig_frame(_a3, i3, "walk_side", walk_i(float(wx[0]) - x0), Vector2(float(wx[0]) - cam, feet))
	elif time < W3_T0:
		fig_frame(_a3, i3, "idle_side", 0, Vector2(x0 - cam, feet))
	else:
		var since := time - (W3_T0 + (x1 - x0) / WALK_SPEED)
		var fi := 0 if rm else int(floor(since * 5.0))
		fig_frame(_a3, i3, "look_side" if since > 0.15 else "idle_side", fi, Vector2(x1 - cam, feet))
	_warm3.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 41, 0.08), 0.0, 1.0))
	_w3fx.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))


## w3 camera x (main-layer px): tracks Alexei to the window (reduced motion halves the travel).
func yard_cam(time: float) -> float:
	var c: Array = L4.get("w3_cam", [0, 64])
	return roundf(float(c[0]) + (float(c[1]) - float(c[0])) * motion_k() * ease01(time, float(W3_CAM[0]),
		float(W3_CAM[1])))


func _draw_steam1() -> void:
	if not w1.visible:
		return
	# the locomotives at the far end: big soft columns rising into the shed
	var pts: Array = L4.get("w1_steam", [[301, 156], [339, 156]])
	for j in pts.size():
		var pp: Array = pts[j]
		draw_puffs(_steam1, _steam_tex, 8, Vector2(float(pp[0]), float(pp[1])), t, 6, 3.6, 84.0,
			(j * 2 - 1) * 30.0, 0.75, j * 0.37, 5.0)
	# heating steam leaking at the carriages' bogies, sized by depth
	var under: Array = L4.get("w1_steam_under", [])
	for i in under.size():
		var u: Array = under[i]
		var at := Vector2(float(u[0]), float(u[1]))
		var near := at.y > 280.0
		var sheet := _steam_tex if near else _breath_tex
		var n := 8 if near else 6
		draw_puffs(_steam1, sheet, n, at, t, 3, 2.4 + i * 0.3, 26.0 if near else 12.0,
			(1.0 if at.x > 320.0 else -1.0) * (10.0 if near else 4.0), 0.5 if near else 0.45, i * 0.21, 2.0)


func _draw_w2() -> void:
	if not w2.visible or _streak_tex == null:
		return
	# snow streaks driven across the glass by the wind of the train (Karsk thick, Berlin a few)
	var k := motion_k()
	var wins := [[lv(L4, "win_k", Vector2(36, 70)), 7, 1.0], [lv(L4, "win_a", Vector2(340, 70)), 16, -1.0]]
	for wdat in wins:
		var at: Vector2 = wdat[0]
		var n: int = wdat[1]
		var dirx: float = wdat[2]
		for i in n:
			var period := 0.6 + h01(i, 911) * 0.5
			var age := fposmod(t / period + h01(i, 913), 1.0)
			var x := at.x + fposmod(h01(i, 917) * 264.0 + dirx * age * 220.0 * k, 264.0)
			var y := at.y + fposmod(h01(i, 919) * 220.0 + age * 60.0 * k, 220.0)
			draw_cell(_w2fx, _streak_tex, 6, i % 6, Vector2(x, y), Color(1, 1, 1, 0.55 * (1.0 - age)))
	# the spoon in the tea glass rattles with the rails: it stands in the glass (its foot hidden by the tea and
	# the holder in front) and its handle tips against the rim
	var sp := lv(L4, "tea_spoon", Vector2(557, 264))
	var j := 0.0 if reduced_motion() else roundf(hnoise(t * 14.0, 915) * 0.9)
	_w2fx.draw_rect(Rect2(sp + Vector2(0, 7), Vector2(1, 8)), Color("#b8b0a0"))
	_w2fx.draw_rect(Rect2(sp + Vector2(j, 0), Vector2(1, 7)), Color("#d2caba"))
	_w2fx.draw_rect(Rect2(sp + Vector2(j, 0), Vector2(1, 1)), Color("#f0eae0"))


func _draw_w3() -> void:
	if not w3.visible:
		return
	var cam := yard_cam(t)
	var meta: Dictionary = LP.get("yard_layers", {})
	var par: Dictionary = meta.get("par", {})
	# the plant's red lamps blink slowly on the far chimneys
	var fpar := float(par.get("far", 0.15))
	var reds: Array = meta.get("reds", [])
	for i in reds.size():
		var r: Array = reds[i]
		var on := fposmod(t * 0.7 + i * 0.31, 1.0) < 0.55
		if on:
			var p := Vector2(float(r[0]) - 1.5 - roundf(cam * fpar), float(r[1]) - 1.0)
			_w3fx.draw_rect(Rect2(p.round(), Vector2(3, 2)), Color("#e0482c"))
	# snow lit in the lamps' cones and in the signal's green
	var lamps: Array = LP.get("yard_lamps", [[262, 104], [612, 96]])
	var cones: Array = []
	for l in lamps:
		cones.append([float(l[0]) - cam, float(l[1]) + 4.0, 34.0, 300.0])
	draw_lit_snow(_w3fx, cones, t, 14, 431)
	var sg: Array = LP.get("yard_signal", [152, 158])
	draw_lit_snow(_w3fx, [[float(sg[0]) - cam, float(sg[1]) + 4.0, 22.0, 240.0]], t, 8, 433,
		Color(0.55, 1.0, 0.65, 1.0))
	# smoke from the office chimney
	var ch: Array = meta.get("chimney", [504, 58])
	draw_puffs(_w3fx, _smoke_tex, 8, Vector2(float(ch[0]) - cam, float(ch[1])), t, 4, 4.0, 46.0, 30.0, 0.55, 0.0,
		3.0)
	# Alexei's breath
	if _breath_tex == null:
		return
	var period := 2.3
	var age := fposmod(t + 0.4, period) / period
	if age > 0.6:
		return
	var head := _a3.position + Vector2(24, 14)
	var p := head + Vector2(age * 8.0, -age * 14.0 * motion_k())
	draw_frame(_w3fx, _breath_tex, 6, int(age / 0.6 * 5.0), p, false, Color(1, 1, 1, 0.5 * (1.0 - age / 0.6)))
