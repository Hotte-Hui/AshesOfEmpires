extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## LS_C3_Halves (21 s) — each keeps half (C3P2_DESIGN §2.9).  Nothing is resolved.
##   h1  0-6     the quay bench from behind: the two halves of the broken file between them, each takes his
##               pages — per ctx.choices.c3g_choose:
##                 split_by_language  Alexei the Russian pages (with the list of names), Konrad the German ones
##                 swap_halves        across: Konrad the Russian pages with Pjotr's name, Alexei the German ones
##                 hide_for_elena     Konrad first takes the list, folds it into his coat (for the cloakroom,
##                                    Marke 27), then the rest is split by language
##   h2  6-11    they walk apart along the quay: Alexei east (right) toward the station, Konrad west (left)
##   h3  11-17   wide: the burning wing mirrored in the ice, the Line's searchlights sweep, the first grey of dawn
##   h4  17-21   the departures board: a fresh row flips in, „Dienstag · 23.40 · Kordon-17 · Gleis 5"
## Lines: c3g (split / swap / elena), then c3d (pocket_plan -> plan_kept, else plan_burnt), then tuesday.
## Round 10: the men sit on the granite bench (slab and blocks in their camera), the searchlights' pools wander over the ice,
## the promenade has a foreground that drifts against the trees and lanterns, the walkers cast lantern shadows, the
## burning wing sends sparks and a leaning column of smoke, crows cross the dawn, pigeons sit on the board's frame
## and steam drifts through the station hall.
## Round 13: the wing's fire is the pixel fire kit (scripts/render/pixel_fire.gd: whole pixels, never scaled, no
## alpha fades) -- flames in its windows and on its roof, a plume of puffs per fire, the big column over the
## roof as puffs that climb, lean east and break up through their own dither, sparks on arcs; the fire's glow
## (h1_glow, h3_glow) breathes in whole steps (light_step), it never ramps.
## Art: tools/pixelgen/env_c3p2_cine_quay.py (+ _river, _life) -> assets/cinematics/c3p2/halves/ (+ layout.json).

const DUR := 21.0
const SHOTS := [["h1", 0.0, 6.0], ["h2", 6.0, 11.0], ["h3", 11.0, 17.0], ["h4", 17.0, 21.0]]
const KIT := ["flame_s", "flame_m", "puff_s", "puff_m", "puff_l", "puff_m_grey", "puff_l_grey", "puff_xl_grey"]
const LINE_TUESDAY := "cin.c3p2.halves.tuesday"
const WALK := [6.25, 6.45, 26.0]      # Alexei starts, Konrad starts, speed px/s
const DAWN := [11.4, 16.8]
const FLIP := [17.35, 0.04]           # the fresh row starts flipping, delay per character
const SWEEP_PERIOD := 7.5             # searchlights: one sweep >= 6 s
const LAP := {"a": Vector2(236, 262), "k": Vector2(404, 262)}

var line_c3g := "cin.c3p2.halves.split"
var line_c3d := "cin.c3p2.halves.plan_burnt"
## h1 choreography: [{who, mode (near/far), stack (ru/de/list), reach, take, hold_end}]
var moves: Array = []
var _fold_t := -1.0                   # hide_for_elena: when the list is in Konrad's hand
var _lean := {"a": 0, "k": 0}         # h1: 0 upright, 1 / 2 leaning half / fully over toward the far stack

var h1: Node2D
var h2: Node2D
var h3: Node2D
var h4: Node2D
var _h1glow: Sprite2D
var _beams1: Node2D
var _stacks: Node2D
var _arm_a: Sprite2D
var _arm_k: Sprite2D
var _fig_a: Sprite2D
var _fig_k: Sprite2D
var _h1top: Node2D
var _snow1: Node2D
var _walk_a: Sprite2D
var _walk_k: Sprite2D
var _prints: Node2D
var _snow2: Node2D
var _h3glow: Sprite2D
var _dawn: Sprite2D
var _h3fx: Node2D
var _snow3: Node2D
var _board: Node2D
var _stack_tex: Texture2D
var _fold_tex: Texture2D
var _breath: Texture2D
var _plume: Node2D
var _glyphs: Texture2D
var _h2near: Sprite2D
var _h2fx: Node2D
var _sky3: Node2D
var _hall: Node2D
var _crow: Texture2D
var _pigeon: Texture2D
var _steam: Texture2D
var _trav: Node2D
var _trav_tex: Array = []


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


# ------------------------------------------------------------------ lines + choreography
func _on_configured() -> void:
	var g := choice("c3g_choose")
	match g:
		"swap_halves":
			line_c3g = "cin.c3p2.halves.swap"
		"hide_for_elena":
			line_c3g = "cin.c3p2.halves.elena"
		_:
			line_c3g = "cin.c3p2.halves.split"
	line_c3d = "cin.c3p2.halves.plan_kept" if choice("c3d_choose") == "pocket_plan" else "cin.c3p2.halves.plan_burnt"
	_fold_t = -1.0
	match g:
		"swap_halves":
			moves = [_m("a", "far", "de", 1.4, 2.2, 3.1), _m("k", "far", "ru", 1.7, 2.5, 3.4)]
		"hide_for_elena":
			moves = [_m("k", "far", "list", 0.9, 1.5, 2.9), _m("a", "near", "ru", 3.0, 3.6, 4.3),
				_m("k", "near", "de", 3.4, 4.0, 4.7)]
			_fold_t = 1.5
		_:
			moves = [_m("a", "near", "ru", 1.4, 2.1, 3.0), _m("k", "near", "de", 2.3, 3.0, 3.9)]


func _m(who: String, mode: String, stack: String, reach: float, take: float, hold_end: float) -> Dictionary:
	return {"who": who, "mode": mode, "stack": stack, "reach": reach, "take": take, "hold_end": hold_end}


func chosen_lines() -> Array:
	return [line_c3g, line_c3d, LINE_TUESDAY]


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 2.0},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c3p2cine_quay", "db": -6.0},
		{"t": 0.7, "say": line_c3g, "dur": 4.8},
		{"t": 6.0, "bed": "c3p2cine_steps_apart", "db": -8.0},
		{"t": 6.5, "say": line_c3d, "dur": 3.9},
		{"t": 11.0, "bed": "c3p2cine_ice", "db": -6.0},
		{"t": FLIP[0] - 0.1, "bed": "c3p2cine_board", "db": -6.0},
		{"t": 17.9, "say": LINE_TUESDAY, "dur": 2.9},
	]
	for m in moves:
		c.append({"t": float(m["take"]) - 0.05, "sfx": "paper_rustle", "db": -12.0, "pv": 0.04})
	return c


# ------------------------------------------------------------------ build
func _build() -> void:
	layout = _layout_section("halves")
	_stack_tex = tex("halves/stacks.png")
	_fold_tex = tex("halves/list_fold.png")
	_breath = tex("halves/breath.png")
	need_kit(KIT)
	_glyphs = tex("halves/glyphs.png")
	h1 = group("Bench")
	sprite("halves/h1_bg.png", Vector2.ZERO, h1)
	_beams1 = _fx(h1, "Searchlights", _draw_beams1)
	_h1glow = sprite("halves/h1_glow.png", Vector2.ZERO, h1, 1, true)
	_stacks = _fx(h1, "Pages", _draw_stacks)
	_arm_a = sprite("halves/arms.png", _lv("arms_at"), h1, int(layout.get("arm_cols", 3)), false, 2)
	_arm_k = sprite("halves/arms.png", _lv("arms_at"), h1, int(layout.get("arm_cols", 3)), false, 2)
	_fig_a = sprite("halves/fig_alexei.png", _lv("fig_alexei"), h1, BODY_FRAMES)
	_fig_k = sprite("halves/fig_konrad.png", _lv("fig_konrad"), h1, BODY_FRAMES)
	_h1top = _fx(h1, "FoldBreath", _draw_h1top)
	_snow1 = snow(h1, Rect2(0, 0, 640, 360), [
		{"count": 80, "v": Vector2(8, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 26, "v": Vector2(11, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9301)
	h2 = group("Promenade")
	sprite("halves/h2_bg.png", Vector2.ZERO, h2)
	sprite("halves/h2_glow.png", Vector2.ZERO, h2, 1, true)
	_prints = _fx(h2, "Footprints", _draw_prints)
	_h2fx = _fx(h2, "Shadows", _draw_h2fx)
	_walk_a = sprite("halves/walk_alexei.png", Vector2.ZERO, h2, 6)
	_walk_k = sprite("halves/walk_konrad.png", Vector2.ZERO, h2, 6)
	_walk_k.flip_h = true
	_h2near = sprite("halves/h2_near.png", _lv("h2_near_at"), h2)
	_snow2 = snow(h2, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(9, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 30, "v": Vector2(12, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9302)
	h3 = group("River")
	sprite("halves/h3_bg.png", Vector2.ZERO, h3)
	_dawn = sprite("halves/h3_dawn.png", Vector2.ZERO, h3, 1, true)
	_plume = _fx(h3, "Plume", _draw_plume)
	_h3glow = sprite("halves/h3_glow.png", Vector2.ZERO, h3, 1, true)
	_h3fx = _fx(h3, "SmokeBeams", _draw_h3)
	_crow = tex("halves/crow.png")
	_sky3 = _fx(h3, "Crows", _draw_crows)
	_snow3 = snow(h3, Rect2(0, 0, 640, 360), [
		{"count": 100, "v": Vector2(7, 12), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 30, "v": Vector2(10, 22), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0}], 9303)
	h4 = group("Board")
	sprite("halves/board_bg.png", Vector2.ZERO, h4)
	sprite("halves/board_glow.png", Vector2.ZERO, h4, 1, true)
	_board = _fx(h4, "FreshRow", _draw_board)
	_pigeon = tex("halves/pigeon.png")
	_steam = tex("halves/steam.png")
	_hall = _fx(h4, "HallLife", _draw_hall)
	for tv in layout.get("travellers", []):
		var tt := tex(str(tv[0]))
		if tt:
			_trav_tex.append([tt, Vector2(float(tv[1]), float(tv[2]))])
	_trav = _fx(h4, "Travellers", _draw_travellers)


func _fx(parent: Node, n: String, fn: Callable) -> Node2D:
	var d := Node2D.new()
	d.name = n
	d.draw.connect(fn)
	parent.add_child(d)
	return d


func _lv(key: String) -> Vector2:
	var v = layout.get(key)
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return Vector2.ZERO


# ------------------------------------------------------------------ frame
func _apply(time: float) -> void:
	if h1 == null:
		return
	var sh := shot_at(time)
	h1.visible = sh == "h1"
	h2.visible = sh == "h2"
	h3.visible = sh == "h3"
	h4.visible = sh == "h4"
	var rm := reduced_motion()
	var k := motion_k()
	# h1: the arms per choreography (and the bodies: breath, or leaning over for the far stack)
	_apply_arms(time, rm)
	_h1glow.modulate = Color(1, 1, 1, 0.92 + 0.08 * light_step(time, 31))
	_stacks.queue_redraw()
	_h1top.queue_redraw()
	_beams1.queue_redraw()
	_snow1.set_time(time * (0.6 if rm else 1.0))
	# h2: they walk apart
	var py := float(layout.get("prom_y", 290))
	var da := maxf(0.0, time - float(WALK[0])) * float(WALK[2]) * k
	var dk := maxf(0.0, time - float(WALK[1])) * float(WALK[2]) * k
	_walk_a.position = Vector2(roundf(342.0 + da - 22.0), py - 72.0 + 2.0)
	_walk_k.position = Vector2(roundf(298.0 - dk - 22.0), py - 72.0 + 2.0)
	_walk_a.frame = int(floor(maxf(0.0, time - float(WALK[0])) * 8.0 * k)) % 6
	_walk_k.frame = int(floor(maxf(0.0, time - float(WALK[1])) * 8.0 * k + 3.0)) % 6
	_prints.queue_redraw()
	_h2fx.queue_redraw()
	_h2near.position = _lv("h2_near_at") + Vector2(roundf(-12.0 * ramp01(time, 6.0, 11.0) * k), 0)
	_snow2.set_time(time * (0.6 if rm else 1.0))
	# h3: dawn grows, the fire's glow wobbles
	_dawn.modulate = Color(1, 1, 1, ramp01(time, float(DAWN[0]), float(DAWN[1])))
	_plume.queue_redraw()
	_h3glow.modulate = Color(1, 1, 1, 0.9 + 0.1 * light_step(time, 33))
	_h3fx.queue_redraw()
	_sky3.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))
	_board.queue_redraw()
	_hall.queue_redraw()
	_trav.queue_redraw()


# ------------------------------------------------------------------ h1
## Round 11 (figures stream): each man's inner arm is one cell of arms.png per moment (layout halves.arm_cols
## cells per row): the reach in three steps (lifting out of the lap, the hand open over the pages, the hand on
## them), the pull with the pages -- the sprite is shifted by the rest of the stack's way, so the hand stays on the
## sliding pages --, the hold, and Konrad's list in his hand beside his hip while he folds it (cells 11-13).  While
## a man reaches across the bench for the other man's pages he leans over (body frames 2 / 3).
const BODY_FRAMES := 4
const PULL := 0.45                    # the taken stack's slide to the lap (as _draw_stacks)


func _apply_arms(time: float, rm: bool) -> void:
	var cols := int(layout.get("arm_cols", 3))
	var lean := {"a": 0, "k": 0}
	for s in [_arm_a, _arm_k]:
		(s as Sprite2D).visible = false
		(s as Sprite2D).position = _lv("arms_at")
	for m in moves:
		var who: String = m["who"]
		var s: Sprite2D = _arm_a if who == "a" else _arm_k
		var row := 0 if who == "a" else 1
		var reach := float(m["reach"])
		var take := float(m["take"])
		if time < reach or time >= float(m["hold_end"]):
			continue
		s.visible = true
		var far: bool = m["mode"] == "far"
		if cols < 14:
			s.frame = row * 3 + ((1 if far else 0) if time < take else 2)
			continue
		var col := 0
		if time < take:
			var v := (time - reach) / maxf(0.01, take - reach)
			var step := 0 if v < 0.3 else (1 if v < 0.72 else 2)
			col = (3 if far else 0) + step
			if far:
				lean[who] = 2 if step > 0 else 1
		elif m["stack"] == "list":
			var fi := int((time - take) / 0.38)
			col = 11 + fi if fi < 3 else 10
		else:
			var u := ramp01(time, take, take + PULL)
			var seat: Vector2 = _lv("stack_" + str(m["stack"]))
			var lap: Vector2 = LAP[who]
			var uk := 1.0
			if u < 1.0 / 6.0:
				col = (3 if far else 0) + 2
				uk = 0.0
			elif u < 0.5:
				col = 8 if far else 6
				uk = 1.0 / 3.0
			elif u < 5.0 / 6.0:
				col = 9 if far else 7
				uk = 2.0 / 3.0
			else:
				col = 10
			if far:
				lean[who] = 2 if u < 0.5 else (1 if u < 5.0 / 6.0 else 0)
			s.position = _lv("arms_at") + (seat.lerp(lap, u) - seat.lerp(lap, uk)).round()
		s.frame = row * cols + col
	_lean = lean
	for who in ["a", "k"]:
		var f: Sprite2D = _fig_a if who == "a" else _fig_k
		if int(lean[who]) > 0 and f.hframes >= BODY_FRAMES:
			f.frame = 1 + int(lean[who])
		elif who == "a":
			f.frame = int(floor((time + 0.3) / 1.9)) % 2 if not rm else 0
		else:
			f.frame = int(floor((time + 1.0) / 2.1)) % 2 if not rm else 0


func _stack_frame(stack: String) -> int:
	return {"ru": 0, "de": 1, "list": 2}.get(stack, 0)


func _draw_stacks() -> void:
	if not h1.visible or _stack_tex == null:
		return
	var seat := {"ru": _lv("stack_ru"), "de": _lv("stack_de")}
	var list_taken_alone := false
	for m in moves:
		if m["stack"] == "list":
			list_taken_alone = true
	for stack in ["ru", "de"]:
		var mv := _move_for(stack)
		var p: Vector2 = seat[stack]
		var hidden := false
		if not mv.is_empty():
			var u := ramp01(t, float(mv["take"]), float(mv["take"]) + 0.45)
			p = p.lerp(LAP[mv["who"]], u)
			hidden = u >= 1.0
		if hidden:
			continue
		draw_frame(_stacks, _stack_tex, 3, _stack_frame(stack), p.round())
		# the list lies on the Russian pages until it is taken (with them, or alone first)
		if stack == "ru":
			var on_top := true
			if list_taken_alone:
				var lm := _move_for("list")
				on_top = t < float(lm["take"])
			if on_top:
				draw_frame(_stacks, _stack_tex, 3, 2, (p + Vector2(2, -3)).round())


func _move_for(stack: String) -> Dictionary:
	for m in moves:
		if m["stack"] == stack:
			return m
	return {}


func _draw_h1top() -> void:
	if not h1.visible:
		return
	# hide_for_elena: the list in Konrad's hand, folded once, twice, gone into the coat
	if _fold_t >= 0.0 and _fold_tex and t >= _fold_t:
		var age := t - _fold_t
		var fi := clampi(int(age / 0.38), 0, 3)
		if fi < 3:
			# in Konrad's left hand beside his hip (the arm sheet's list cells hold it there)
			var hand := LAP["k"] + Vector2(-26, -26 + age * 6.0)
			if layout.has("list_fold_at"):
				hand = _lv("list_fold_at") + Vector2(0, 2 * fi)
			draw_frame(_h1top, _fold_tex, 4, fi, hand.round())
	# breath of both men in the cold
	if _breath:
		var k := motion_k()
		for j in 2:
			var base: Vector2 = _lv("fig_alexei") + Vector2(80, 30) if j == 0 else _lv("fig_konrad") + Vector2(66, 28)
			# leaning over for the far stack, his face moves toward the middle of the bench (16 / 31 px)
			var ln := clampi(int(_lean["a" if j == 0 else "k"]), 0, 2)
			var dx: float = 0.0 if ln == 0 else (17.0 if ln == 1 else 31.0)
			base.x += dx if j == 0 else -dx
			var period := 2.2 + j * 0.4
			var age := fposmod(t + j * 0.9, period) / period
			if age > 0.6:
				continue
			var p := base + Vector2((j * 2 - 1) * -4.0 * age, -age * 26.0 * k)
			draw_frame(_h1top, _breath, 6, int(age / 0.6 * 5.0), p, false, Color(1, 1, 1, 0.55 * (1.0 - age / 0.6)))


func _beam(ci: CanvasItem, from: Vector2, ang: float, reach: float, width: float, col: Color) -> void:
	var dir := Vector2(sin(ang), cos(ang))
	var side := Vector2(dir.y, -dir.x)
	var tip := from + dir * reach
	var pts := PackedVector2Array([from - side * 1.0, from + side * 1.0, tip + side * width, tip - side * width])
	ci.draw_colored_polygon(pts, col)


func _sweep_angle(time: float, phase: float) -> float:
	# slow pendulum across the ice (>= 6 s per sweep), reduced motion: even slower
	var per := SWEEP_PERIOD * (1.6 if reduced_motion() else 1.0)
	return sin(time / per * TAU + phase) * 0.9


func _draw_beams1() -> void:
	if not h1.visible:
		return
	var towers: Array = layout.get("towers", [[168, 94], [486, 90]])
	var ice: Array = layout.get("ice_y", [128, 196])
	for i in towers.size():
		var tw: Array = towers[i]
		var from := Vector2(float(tw[0]) + 0.5, float(tw[1]) + 2.0)
		var a := _sweep_angle(t, i * 2.1)
		# the beam reaches down to the ice and leaves a pale pool that wanders with the sweep
		var land := float(ice[0]) + 18.0 + 30.0 * (0.5 + 0.5 * sin(t * 0.37 + i * 1.7))
		var reach := (land - from.y) / maxf(0.2, cos(a))
		_beam(_beams1, from, a, reach, 12.0, Color(0.8, 0.86, 0.95, 0.09))
		_beam(_beams1, from, a, reach, 4.5, Color(0.85, 0.9, 1.0, 0.10))
		var tip := from + Vector2(sin(a), cos(a)) * reach
		_pool(_beams1, tip, 20.0, 4.0)


## a soft dithered-looking pool of searchlight on the ice (three nested ellipses)
func _pool(ci: CanvasItem, c: Vector2, rx: float, ry: float) -> void:
	for k in 3:
		var f := 1.0 - k * 0.3
		var pts := PackedVector2Array()
		for j in 16:
			var an := TAU * j / 16.0
			pts.append(c + Vector2(cos(an) * rx * f, sin(an) * ry * f))
		ci.draw_colored_polygon(pts, Color(0.85, 0.9, 1.0, 0.07 + k * 0.03))


# ------------------------------------------------------------------ h2
## the lanterns throw each walker's shadow on the snow (long when he is between two lanterns)
func _draw_h2fx() -> void:
	if not h2.visible:
		return
	var py := float(layout.get("prom_y", 290))
	var lanterns: Array = layout.get("lanterns", [96, 256, 416, 576])
	for wk in [_walk_a, _walk_k]:
		var fx := (wk as Sprite2D).position.x + 22.0
		var near := 9999.0
		for lx in lanterns:
			if absf(float(lx) - fx) < absf(near - fx):
				near = float(lx)
		var dirx := signf(fx - near)
		var ln := clampf(absf(fx - near) * 0.35, 6.0, 30.0)
		var pts := PackedVector2Array([Vector2(fx - 4, py + 1), Vector2(fx + 4, py + 1),
			Vector2(fx + 4 + dirx * ln, py + 4), Vector2(fx - 4 + dirx * ln, py + 4)])
		_h2fx.draw_colored_polygon(pts, Color(0.06, 0.08, 0.12, 0.45))


func _draw_prints() -> void:
	if not h2.visible:
		return
	var py := float(layout.get("prom_y", 290))
	var k := motion_k()
	var da := maxf(0.0, t - float(WALK[0])) * float(WALK[2]) * k
	var dk := maxf(0.0, t - float(WALK[1])) * float(WALK[2]) * k
	var x := 6.0
	var i := 0
	while x < da - 6.0:
		_prints.draw_rect(Rect2(Vector2(floorf(342.0 + x), py + (1 if i % 2 == 0 else 3)), Vector2(3, 1)), Color("#3a4859"))
		x += 9.0
		i += 1
	x = 6.0
	i = 0
	while x < dk - 6.0:
		_prints.draw_rect(Rect2(Vector2(floorf(298.0 - x) - 3, py + (1 if i % 2 == 0 else 3)), Vector2(3, 1)), Color("#3a4859"))
		x += 9.0
		i += 1


# ------------------------------------------------------------------ h3
func _draw_h3() -> void:
	if not h3.visible:
		return
	var k := motion_k()
	# searchlights from the far towers sweeping over the ice toward the viewer
	var towers: Array = layout.get("h3_towers", [[360, 110], [486, 110]])
	for i in towers.size():
		var tw: Array = towers[i]
		var a := _sweep_angle(t, 0.7 + i * 2.4) * 0.8
		var from := Vector2(float(tw[0]) + 0.5, float(tw[1]) + 1.0)
		var land := 214.0 + 40.0 * (0.5 + 0.5 * sin(t * 0.31 + i * 2.3))
		var reach := (land - from.y) / maxf(0.2, cos(a))
		_beam(_h3fx, from, a, reach, 20.0, Color(0.8, 0.86, 0.95, 0.09))
		_beam(_h3fx, from, a, reach, 7.0, Color(0.85, 0.9, 1.0, 0.10))
		_pool(_h3fx, from + Vector2(sin(a), cos(a)) * reach, 26.0, 5.0)
	# the wing burns (pixel fire kit): every fire's smoke leans east with the wind, then the flames in the windows
	# and the taller ones on the roof, sparks on arcs over the roof
	var fires: Array = layout.get("h3_fire", [])
	for j in fires.size():
		var f: Array = fires[j]
		PF.plume(_h3fx, {"from": Vector2(float(f[0]), float(f[1]) - 6.0), "spread": Vector2(2, 1), "count": 3,
			"life": 3.4, "rise": 32.0, "slow": 0.3, "bend": 20.0, "sheets": ["puff_m", "puff_s", "puff_m_grey"],
			"seed": 40 + j, "rate": k}, t)
	for j in fires.size():
		var f2: Array = fires[j]
		PF.flame(_h3fx, "flame_m" if float(f2[1]) < 90.0 else "flame_s", Vector2(float(f2[0]), float(f2[1]) + 14.0),
			t, j, fire_rate())
	PF.sparks(_h3fx, {"rect": Rect2(160, 90, 140, 10), "count": 22, "life": 2.2, "rise": 32.0, "kick": 5.0,
		"wind": 14.0, "seed": 7, "rate": k}, t)


## h3: the smoke column of the burning wing (pixel fire kit): big puffs climb from the roof's fire and the wind
## takes them east -- lit from below while they are young, the night's grey higher up; each one runs the life
## drawn into its sheet (it swells, then breaks up through the ordered dither), nothing is faded.
func _draw_plume() -> void:
	if not h3.visible:
		return
	var k := motion_k()
	PF.plume(_plume, {"from": Vector2(228, 92), "spread": Vector2(34, 6), "count": 10, "life": 9.0, "rise": 17.0,
		"slow": 0.35, "bend": 5.0, "sway": 3.0, "sheets": ["puff_xl_grey", "puff_l_grey", "puff_xl_grey"],
		"seed": 61, "rate": k}, t)
	PF.plume(_plume, {"from": Vector2(228, 96), "spread": Vector2(40, 4), "count": 7, "life": 4.5, "rise": 20.0,
		"slow": 0.3, "bend": 6.0, "sheets": ["puff_l", "puff_m", "puff_l"], "seed": 62, "rate": k}, t)

## three crows cross the first grey of dawn, wings beating at their own pace
func _draw_crows() -> void:
	if not h3.visible or _crow == null:
		return
	var k := motion_k()
	for i in 3:
		var t0 := 12.2 + i * 0.9
		if t < t0:
			continue
		var age := t - t0
		var p := Vector2(80.0 + i * 26.0 + age * 58.0 * k, 66.0 + i * 9.0 - age * 4.0 * k + sin(age * 2.0 + i) * 3.0)
		var fr := int(floor(age * (7.0 + i))) % 4
		draw_frame(_sky3, _crow, 4, fr, p.round(), false, Color(1, 1, 1, clampf(age / 0.4, 0.0, 1.0)))


# ------------------------------------------------------------------ h4
## pigeons on the board's top frame, steam from a locomotive drifting through the hall
func _draw_hall() -> void:
	if not h4.visible:
		return
	var ledge: Array = layout.get("board_ledge", [34, 64, 606])
	if _pigeon:
		for i in 3:
			var px := float(ledge[0]) + 70.0 + i * 190.0 + (i % 2) * 24.0
			var bob := 1 if fposmod(t * (0.7 + i * 0.23) + i * 0.4, 1.0) > 0.78 else 0
			draw_frame(_hall, _pigeon, 2, bob, Vector2(px, float(ledge[1]) + 1.0), i == 1)
	if _steam:
		var k := motion_k()
		var n := 6
		var fw := _steam.get_width() / n
		var fh := _steam.get_height()
		for i in 4:
			var age := fposmod(t * 0.22 + i * 0.25, 1.0)
			var x := -80.0 + i * 190.0 + age * 160.0 * k
			var y := 300.0 - age * 14.0
			_hall.draw_texture_rect_region(_steam, Rect2(Vector2(roundf(x), roundf(y)), Vector2(fw, fh)),
				Rect2(clampi(int(age * n), 0, n - 1) * fw, 0, fw, fh), Color(1, 1, 1, 0.5 * sin(age * PI)))


## two early travellers in front of the board, looking up at it (backs to us, lit by the hall's dawn)
func _draw_travellers() -> void:
	if not h4.visible:
		return
	for i in _trav_tex.size():
		var tv: Array = _trav_tex[i]
		var fr := 1 if (not reduced_motion() and fposmod(t * 0.45 + i * 0.5, 1.0) > 0.6) else 0
		draw_frame(_trav, tv[0], 2, fr, tv[1])


func _draw_board() -> void:
	if not h4.visible or _glyphs == null:
		return
	var charset := str(layout.get("charset", " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.·-:ÄÖÜ"))
	var cell: Array = layout.get("cell", [12, 18])
	var cw := float(cell[0])
	var chh := float(cell[1])
	var fresh := str(layout.get("fresh", "DIENSTAG · 23.40 · KORDON-17 · GLEIS 5"))
	var rows_y: Array = layout.get("rows_y", [122, 156, 190, 224, 258])
	var ry := float(rows_y[int(layout.get("fresh_row", 4))])
	var rx := float(layout.get("row_x", 64))
	var rm := reduced_motion()
	for i in fresh.length():
		var target := charset.find(fresh[i])
		if target < 0:
			target = 0
		var settle := float(FLIP[0]) + (0.35 if rm else i * float(FLIP[1]) + 0.25)
		var idx := 0
		var flap := 0
		if t < float(FLIP[0]):
			idx = 0
		elif t < settle:
			var tick := int(floor(t * (10.0 if rm else 22.0)))
			idx = 1 + absi(int(hnoise(float(tick) + i * 3.7, 77) * 1000.0)) % (charset.length() - 1)
			flap = tick % 2
		else:
			idx = target
		var src := Rect2(idx * cw, flap * chh, cw, chh)
		_board.draw_texture_rect_region(_glyphs, Rect2(Vector2(rx + i * cw, ry), Vector2(cw, chh)), src)
