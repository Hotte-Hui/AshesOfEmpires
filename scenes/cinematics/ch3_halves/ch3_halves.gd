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
## Art: tools/pixelgen/env_c3p2_cine_quay.py -> assets/cinematics/c3p2/halves/ (+ layout.json "halves").

const DUR := 21.0
const SHOTS := [["h1", 0.0, 6.0], ["h2", 6.0, 11.0], ["h3", 11.0, 17.0], ["h4", 17.0, 21.0]]
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
var _smoke: Texture2D
var _flame_s: Texture2D
var _glyphs: Texture2D


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
	_smoke = tex("halves/smoke.png")
	_flame_s = tex("halves/flame_s.png")
	_glyphs = tex("halves/glyphs.png")
	h1 = group("Bench")
	sprite("halves/h1_bg.png", Vector2.ZERO, h1)
	_beams1 = _fx(h1, "Searchlights", _draw_beams1)
	_h1glow = sprite("halves/h1_glow.png", Vector2.ZERO, h1, 1, true)
	_stacks = _fx(h1, "Pages", _draw_stacks)
	_arm_a = sprite("halves/arms.png", _lv("arms_at"), h1, 3, false, 2)
	_arm_k = sprite("halves/arms.png", _lv("arms_at"), h1, 3, false, 2)
	_fig_a = sprite("halves/fig_alexei.png", _lv("fig_alexei"), h1, 2)
	_fig_k = sprite("halves/fig_konrad.png", _lv("fig_konrad"), h1, 2)
	_h1top = _fx(h1, "FoldBreath", _draw_h1top)
	_snow1 = snow(h1, Rect2(0, 0, 640, 360), [
		{"count": 80, "v": Vector2(8, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 26, "v": Vector2(11, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9301)
	h2 = group("Promenade")
	sprite("halves/h2_bg.png", Vector2.ZERO, h2)
	sprite("halves/h2_glow.png", Vector2.ZERO, h2, 1, true)
	_prints = _fx(h2, "Footprints", _draw_prints)
	_walk_a = sprite("halves/walk_alexei.png", Vector2.ZERO, h2, 6)
	_walk_k = sprite("halves/walk_konrad.png", Vector2.ZERO, h2, 6)
	_walk_k.flip_h = true
	_snow2 = snow(h2, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(9, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": 30, "v": Vector2(12, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 9302)
	h3 = group("River")
	sprite("halves/h3_bg.png", Vector2.ZERO, h3)
	_dawn = sprite("halves/h3_dawn.png", Vector2.ZERO, h3, 1, true)
	_h3glow = sprite("halves/h3_glow.png", Vector2.ZERO, h3, 1, true)
	_h3fx = _fx(h3, "SmokeBeams", _draw_h3)
	_snow3 = snow(h3, Rect2(0, 0, 640, 360), [
		{"count": 100, "v": Vector2(7, 12), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 30, "v": Vector2(10, 22), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0}], 9303)
	h4 = group("Board")
	sprite("halves/board_bg.png", Vector2.ZERO, h4)
	sprite("halves/board_glow.png", Vector2.ZERO, h4, 1, true)
	_board = _fx(h4, "FreshRow", _draw_board)


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
	# h1: the arms per choreography
	_arm_a.visible = false
	_arm_k.visible = false
	for m in moves:
		var s: Sprite2D = _arm_a if m["who"] == "a" else _arm_k
		var row := 0 if m["who"] == "a" else 1
		if time >= float(m["reach"]) and time < float(m["take"]):
			s.visible = true
			s.frame = row * 3 + (0 if m["mode"] == "near" else 1)
		elif time >= float(m["take"]) and time < float(m["hold_end"]):
			s.visible = true
			s.frame = row * 3 + 2
	_fig_a.frame = int(floor((time + 0.3) / 1.9)) % 2 if not rm else 0
	_fig_k.frame = int(floor((time + 1.0) / 2.1)) % 2 if not rm else 0
	_h1glow.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 31, 0.1), 0.0, 1.0))
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
	_snow2.set_time(time * (0.6 if rm else 1.0))
	# h3: dawn grows, the fire's glow wobbles
	_dawn.modulate = Color(1, 1, 1, ramp01(time, float(DAWN[0]), float(DAWN[1])) * 0.95)
	_h3glow.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 33), 0.0, 1.0))
	_h3fx.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))
	_board.queue_redraw()


# ------------------------------------------------------------------ h1
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
			var hand := LAP["k"] + Vector2(-26, -26 + age * 6.0)
			draw_frame(_h1top, _fold_tex, 4, fi, hand.round())
	# breath of both men in the cold
	if _breath:
		var k := motion_k()
		for j in 2:
			var base: Vector2 = _lv("fig_alexei") + Vector2(80, 30) if j == 0 else _lv("fig_konrad") + Vector2(66, 28)
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
	for i in towers.size():
		var tw: Array = towers[i]
		var a := _sweep_angle(t, i * 2.1)
		_beam(_beams1, Vector2(float(tw[0]) + 0.5, float(tw[1]) + 2.0), a, 150.0, 18.0, Color(0.8, 0.86, 0.95, 0.10))
		_beam(_beams1, Vector2(float(tw[0]) + 0.5, float(tw[1]) + 2.0), a, 120.0, 7.0, Color(0.85, 0.9, 1.0, 0.10))


# ------------------------------------------------------------------ h2
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
		_beam(_h3fx, Vector2(float(tw[0]) + 0.5, float(tw[1]) + 1.0), a, 230.0, 26.0, Color(0.8, 0.86, 0.95, 0.09))
		_beam(_h3fx, Vector2(float(tw[0]) + 0.5, float(tw[1]) + 1.0), a, 190.0, 9.0, Color(0.85, 0.9, 1.0, 0.10))
	# flames in the wing's windows and the smoke column leaning with the wind
	var fires: Array = layout.get("h3_fire", [])
	for j in fires.size():
		var f: Array = fires[j]
		if _flame_s:
			draw_frame(_h3fx, _flame_s, 8, flame_frame(t, 8, j * 0.31), Vector2(float(f[0]), float(f[1]) + 14.0))
		if _smoke:
			for i in 3:
				var age := fposmod(t * 0.35 + j * 0.21 + i * 0.33, 1.0)
				var p := Vector2(float(f[0]) + age * 60.0 * k, float(f[1]) - 6.0 - age * 90.0 * k)
				draw_frame(_h3fx, _smoke, 8, int(age * 7.0), p, false, Color(1.0, 0.86, 0.76, 0.8 * (1.0 - age)))


# ------------------------------------------------------------------ h4
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
