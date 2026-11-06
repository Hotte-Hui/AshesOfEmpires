extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Card (11 s) — the second match cut, on the torn registry card No. 0417 (C4_DESIGN §2.9).
##   c1  0-3.5    Konrad lifts the German half out of the snow beside the split crate; his right thumb runs down
##                the perforated edge
##   c2  3.5-5    macro: the perforation of the German half, Konrad's gloved thumb runs down it (the fingers behind
##                the card, cut by its torn edge), the dawn's snow out of focus beyond
##                                                     -- hard cut, mirrored: the same holes, the other half --
##   c3  5-9      the Russian half's perforation, Alexei's bare index finger along it (c3a, to 6.2) -> the desk of the siding
##                office: the card, his hand, the kerosene lamp, the stencils on the wall (c3b)
##   c4  9-11     over his shoulder: he looks up from the card to the wagon beyond the booth window -- the level's
##                siding hall under its work lamp, dust turning in the light, the kerosene lamp breathing behind him
## Polish pass: snow drifting over c1, the tea steaming and dust in the lamp light of c3b, the hall seen through
## the booth window in c4 (env_c4_cine_card.py, env_c4_cine_levelplates.py).  Round 10: the macro digits are the
## figures stream's thumb and finger (env_c4_cine_figs.c2_thumb / c3_finger) instead of a shadow; bokeh drifts
## behind the paper, big out-of-focus flakes in front of it (c2), dust in the lamp light (c3a); the kerosene flame
## is a real flame on the wick inside a lit chimney.
## Lines: Konrad reads the name; the time in Karsk.

const DUR := 11.0
const SHOTS := [["c1", 0.0, 3.5], ["c2", 3.5, 5.0], ["c3", 5.0, 9.0], ["c4", 9.0, 11.0]]
const LINES := ["cin.c4.card.konrad", "cin.c4.card.karsk"]
const C1_LIFT := [0.15, 1.05, 110.0]   # the card + left hand rise from the snow: from, to, depth
const C1_THUMB := [1.15, 1.5, 3.35]    # the right hand comes in, starts down the edge, reaches the bottom
const C3_CUT := 6.2                    # c3a macro -> c3b desk
const C4_LOOK := 9.55                  # Alexei lifts his head
const PERF_TICKS := [3.6, 4.85]        # the thumb runs over the macro holes (c4cine_perf; tests compare)

var L4: Dictionary = {}
var c1: Node2D
var c2: Node2D
var c3a: Node2D
var c3b: Node2D
var c4: Node2D
var _card: Node2D
var _lhand: Sprite2D
var _lthumb: Sprite2D
var _card_spr: Sprite2D
var _rhand: Sprite2D
var _digit2b: Sprite2D
var _digit2: Sprite2D
var _digit3: Sprite2D
var _bokeh_tex: Texture2D
var _flake_tex: Texture2D
var _fx2: Node2D
var _fx2f: Node2D
var _fx3a: Node2D
var _hand3: Sprite2D
var _flame: Sprite2D
var _lampglow: Sprite2D
var _alexei: Sprite2D
var _snow1: Node2D
var _fx3: Node2D
var _fx4: Node2D
var _lamp4: Sprite2D
var _steam_tex: Texture2D
var _motes_tex: Texture2D


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
		{"t": 0.0, "bed": "c4cine_card_snow", "db": -6.0},
		say_at(LINES[0], 0.5),
		{"t": 3.5, "bed": "c4cine_perf", "db": -6.0},
		{"t": 5.0, "bed": "c4cine_perf_ru", "db": -7.0},
		say_at(LINES[1], 5.3, 1.4, 1.6),
		{"t": 6.2, "bed": "c4cine_office", "db": -6.0},
	]


func _build() -> void:
	L4 = _layout_section("card")
	_steam_tex = tex("places/steam_warm.png")
	_motes_tex = tex("places/motes.png")
	c1 = group("Snow")
	sprite("card/c1_bg.png", Vector2.ZERO, c1)
	_card = group("HeldCard", c1)
	var la := lv(L4, "c1_lhand_at", Vector2(113, 22))
	var ca := lv(L4, "card_at", Vector2(230, 104))
	_lhand = sprite("card/c1_lhand.png", la, _card)
	_card_spr = sprite("card/card_de.png", ca, _card)
	_lthumb = sprite("card/c1_lthumb.png", la, _card)
	_rhand = sprite("card/c1_rhand.png", Vector2.ZERO, c1)
	_snow1 = snow(c1, Rect2(0, 0, 640, 360), [
		{"count": 50, "v": Vector2(10, 18), "vjit": 0.4, "size": Vector2(1, 1), "color": Color("#bfc9d5"), "sway": 3.0},
		{"count": 14, "v": Vector2(16, 34), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#e2e8ee"), "sway": 4.0}],
		9611)
	_bokeh_tex = tex("card/bokeh.png")
	_flake_tex = tex("number/flakes.png")
	c2 = group("MacroDE")
	sprite("card/c2_macro.png", Vector2.ZERO, c2)
	_fx2 = fx(c2, "Bokeh", _draw_bokeh2)
	_fx2.material = additive()
	_digit2b = sprite("card/c2_thumb_back.png", Vector2.ZERO, c2)        # the glove's fingers behind the card
	sprite("card/c2_paper.png", Vector2.ZERO, c2)                       # the torn paper cuts them
	_digit2 = sprite("card/c2_thumb.png", Vector2.ZERO, c2)             # the thumb on its face
	_fx2f = fx(c2, "Flakes", _draw_flakes2)
	_fx2f.material = additive()
	c3a = group("MacroRU")
	sprite("card/c3a_macro.png", Vector2.ZERO, c3a)
	_fx3a = fx(c3a, "BokehAndDust", _draw_c3a)
	_fx3a.material = additive()
	_digit3 = sprite("card/c3_finger.png", Vector2.ZERO, c3a)
	c3b = group("Desk")
	sprite("card/c3b_desk.png", Vector2.ZERO, c3b)
	sprite("card/card_ru.png", lv(L4, "ru_at", Vector2(300, 150)), c3b)
	_hand3 = sprite("card/c3_hand.png", lv(L4, "c3_hand_at", Vector2(128, 100)), c3b)
	_lampglow = sprite("card/lamp_glow.png", Vector2.ZERO, c3b, 1, true)
	_flame = sprite("card/flame.png", Vector2.ZERO, c3b, 4)
	_fx3 = fx(c3b, "TeaAndDust", _draw_c3b)
	c4 = group("Window")
	sprite("card/c4_bg.png", Vector2.ZERO, c4)
	_fx4 = fx(c4, "HallDust", _draw_c4)
	_lamp4 = sprite("card/c4_lampglow.png", Vector2.ZERO, c4, 1, true)
	_alexei = sprite("card/c4_alexei.png", lv(L4, "c4_alexei_at", Vector2(16, 96)), c4, 2)


## c1: how far the card group still is below its held position.
func lift_off(time: float) -> float:
	return roundf(float(C1_LIFT[2]) * motion_k() * (1.0 - ease_out(time, float(C1_LIFT[0]), float(C1_LIFT[1]))))


## c1: the thumb tip's y on the perforated edge.
func thumb_y(time: float) -> float:
	var ca := lv(L4, "card_at", Vector2(230, 104))
	var sz := lv(L4, "card_size", Vector2(176, 118))
	var u := ease01(time, float(C1_THUMB[1]), float(C1_THUMB[2]))
	return roundf(ca.y + 10.0 + (sz.y - 26.0) * u)


## macros: the thumb / finger moving down along the edge (same speed both sides of the cut).  The name is the
## round-9 one (the digit replaced the shadow sprite at the same y).
func shadow_y(time: float, t0: float, t1: float) -> float:
	return roundf(-20.0 + 200.0 * ease01(time, t0, t1))


## Top-left of a macro digit's canvas (side "de" / "ru") at `time`.
func digit_pos(side: String, time: float, t0: float, t1: float) -> Vector2:
	var md: Dictionary = L4.get("macro_digit", {})
	var o: Array = md.get(side, [290, 30] if side == "de" else [0, 30])
	return Vector2(float(o[0]), float(o[1]) + shadow_y(time, t0, t1))


func _apply(time: float) -> void:
	if c1 == null:
		return
	var sh := shot_at(time)
	c1.visible = sh == "c1"
	c2.visible = sh == "c2"
	c3a.visible = sh == "c3" and time < C3_CUT
	c3b.visible = sh == "c3" and time >= C3_CUT
	c4.visible = sh == "c4"
	var rm := reduced_motion()
	# c1
	_card.position = Vector2(0, lift_off(time))
	var ca := lv(L4, "card_at", Vector2(230, 104))
	var sz := lv(L4, "card_size", Vector2(176, 118))
	var tip := lv(L4, "c1_rhand_tip", Vector2(102, 76))
	var come := 1.0 - ease_out(time, float(C1_THUMB[0]), float(C1_THUMB[1]))
	_rhand.visible = time >= float(C1_THUMB[0])
	_rhand.position = Vector2(ca.x + sz.x - 4.0 - tip.x + roundf(120.0 * come * motion_k()), thumb_y(time) - tip.y)
	# c2 / c3a: the thumb (German half: paper left of the edge) and the finger (Russian half: right of it)
	var d2 := digit_pos("de", time, 3.5, 5.0)
	_digit2b.position = d2
	_digit2.position = d2
	_digit3.position = digit_pos("ru", time, 5.0, C3_CUT + 0.3)
	_fx2.queue_redraw()
	_fx2f.queue_redraw()
	_fx3a.queue_redraw()
	# c3b: the hand slides a little along the edge; the flame (slow), its light breathes
	var h3 := lv(L4, "c3_hand_at", Vector2(128, 100))
	_hand3.position = h3 + Vector2(0, roundf(10.0 * ease01(time, C3_CUT, 8.6) * motion_k()))
	var lamp := lv(L4, "c3_lamp", Vector2(548, 92))
	_flame.position = lv(L4, "c3_flame_at", lamp - Vector2(5, 10))
	_flame.frame = 0 if rm else posmod(int(floor(time * 7.0)) + int(hnoise(time * 3.0, 67) > 0.5), 4)
	_lampglow.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 61, 0.09), 0.0, 1.0))
	_fx3.queue_redraw()
	_snow1.set_time(time * (0.6 if rm else 1.0))
	# c4: he looks up; the lamp behind him breathes, dust turns in the hall's light beyond the glass
	_alexei.frame = 1 if time >= C4_LOOK else 0
	_lamp4.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 63, 0.10), 0.0, 1.0))
	_fx4.queue_redraw()


## c2: out-of-focus lights of the dawn beyond the card (behind the paper), drifting a little with the hand.
func _draw_bokeh2() -> void:
	if not c2.visible or _bokeh_tex == null:
		return
	var k := motion_k()
	var spots := [[424, 96, 2, 0.30], [566, 164, 2, 0.34], [486, 272, 1, 0.26], [612, 64, 0, 0.30],
		[384, 206, 0, 0.22], [520, 34, 1, 0.20], [618, 250, 1, 0.24]]
	for i in spots.size():
		var sp: Array = spots[i]
		var drift := Vector2(sin(t * 0.7 + i) * 3.0 - (t - 3.5) * 4.0, cos(t * 0.5 + i * 1.3) * 2.0) * k
		var a := float(sp[3]) * (0.85 + 0.15 * sin(t * 1.1 + i * 2.0))
		draw_cell(_fx2, _bokeh_tex, 3, int(sp[2]), Vector2(float(sp[0]) - 28.0, float(sp[1]) - 28.0) + drift,
			Color(0.62, 0.72, 0.92, a))


## c2: big soft flakes falling between the lens and the card (the snow of c1, out of focus).
func _draw_flakes2() -> void:
	if not c2.visible or _flake_tex == null:
		return
	var k := motion_k()
	for i in 7:
		var sz := 1 + i % 3
		var sp := (16.0 + sz * 8.0) * k
		var x := fposmod(h01(i, 2201) * 680.0 + sin(t * 0.8 + i) * 8.0 * k - (t - 3.5) * 6.0 * k, 680.0) - 20.0
		var y := fposmod(h01(i, 2203) * 380.0 + (t - 3.5) * sp, 380.0) - 20.0
		draw_cell(_fx2f, _flake_tex, 4, sz, Vector2(x, y), Color(1, 1, 1, 0.35 + 0.1 * sz))


## c3a: the lamp's light in the out-of-focus booth behind the card, dust turning in it.
func _draw_c3a() -> void:
	if not c3a.visible:
		return
	var k := motion_k()
	if _bokeh_tex != null:
		var spots := [[118, 98, 2, 0.30], [214, 244, 1, 0.24], [60, 282, 2, 0.26], [258, 150, 0, 0.18]]
		for i in spots.size():
			var sp: Array = spots[i]
			var drift := Vector2(sin(t * 0.6 + i) * 2.0 + (t - 5.0) * 3.0, cos(t * 0.45 + i) * 2.0) * k
			var a := float(sp[3]) * clampf(fire_wobble(t + i * 0.37, 65, 0.15), 0.6, 1.2)
			draw_cell(_fx3a, _bokeh_tex, 3, int(sp[2]), Vector2(float(sp[0]) - 28.0, float(sp[1]) - 28.0) + drift,
				Color(1.0, 0.72, 0.36, a))
	draw_motes(_fx3a, _motes_tex, Rect2(20.0, 40.0, 600.0, 280.0), Vector2(520, 120), 420.0, t, 22, 6311, 0.55)


func _draw_c3b() -> void:
	if not c3b.visible:
		return
	var tea := lv(L4, "c3_tea", Vector2(521, 186))
	draw_puffs(_fx3, _steam_tex, 8, tea, t, 3, 2.6, 40.0, 6.0, 0.45, 0.0, 3.0)
	var lamp := lv(L4, "c3_lamp", Vector2(548, 92))
	draw_motes(_fx3, _motes_tex, Rect2(lamp.x - 220.0, lamp.y - 50.0, 300.0, 200.0), lamp, 200.0, t, 18, 6301, 0.6)


func _draw_c4() -> void:
	if not c4.visible:
		return
	var w: Array = L4.get("c4_win", [250, 70, 600, 254])
	var r := Rect2(float(w[0]), float(w[1]), float(w[2]) - float(w[0]), float(w[3]) - float(w[1]))
	draw_motes(_fx4, _motes_tex, r, Vector2(r.position.x + r.size.x * 0.52, r.position.y + 30.0), 160.0, t, 22,
		6401, 0.5)
