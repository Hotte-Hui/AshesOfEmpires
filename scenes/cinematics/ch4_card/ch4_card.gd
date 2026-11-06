extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Card (11 s) — the second match cut, on the torn registry card No. 0417 (C4_DESIGN §2.9).
##   c1  0-3.5    Konrad lifts the German half out of the snow beside the split crate; his right thumb runs down
##                the perforated edge
##   c2  3.5-5    macro: the perforation of the German half, the thumb's shadow along it
##                                                     -- hard cut, mirrored: the same holes, the other half --
##   c3  5-9      the Russian half's perforation, Alexei's finger's shadow (c3a, to 6.2) -> the desk of the siding
##                office: the card, his hand, the kerosene lamp, the stencils on the wall (c3b)
##   c4  9-11     over his shoulder: he looks up from the card to the wagon beyond the booth window
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
var _shadow2: Sprite2D
var _shadow3: Sprite2D
var _hand3: Sprite2D
var _flame: Sprite2D
var _lampglow: Sprite2D
var _alexei: Sprite2D


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
	c1 = group("Snow")
	sprite("card/c1_bg.png", Vector2.ZERO, c1)
	_card = group("HeldCard", c1)
	var la := lv(L4, "c1_lhand_at", Vector2(113, 22))
	var ca := lv(L4, "card_at", Vector2(230, 104))
	_lhand = sprite("card/c1_lhand.png", la, _card)
	_card_spr = sprite("card/card_de.png", ca, _card)
	_lthumb = sprite("card/c1_lthumb.png", la, _card)
	_rhand = sprite("card/c1_rhand.png", Vector2.ZERO, c1)
	c2 = group("MacroDE")
	sprite("card/c2_macro.png", Vector2.ZERO, c2)
	_shadow2 = sprite("card/shadow.png", Vector2.ZERO, c2)
	c3a = group("MacroRU")
	sprite("card/c3a_macro.png", Vector2.ZERO, c3a)
	_shadow3 = sprite("card/shadow.png", Vector2.ZERO, c3a)
	c3b = group("Desk")
	sprite("card/c3b_desk.png", Vector2.ZERO, c3b)
	sprite("card/card_ru.png", lv(L4, "ru_at", Vector2(300, 150)), c3b)
	_hand3 = sprite("card/c3_hand.png", lv(L4, "c3_hand_at", Vector2(128, 100)), c3b)
	_lampglow = sprite("card/lamp_glow.png", Vector2.ZERO, c3b, 1, true)
	_flame = sprite("card/flame.png", Vector2.ZERO, c3b, 4)
	c4 = group("Window")
	sprite("card/c4_bg.png", Vector2.ZERO, c4)
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


## macros: the shadow of the thumb / finger moving down along the edge (same speed both sides of the cut).
func shadow_y(time: float, t0: float, t1: float) -> float:
	return roundf(-20.0 + 200.0 * ease01(time, t0, t1))


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
	# c2 / c3a: the shadows (German half: paper left of the edge; Russian half: right of it)
	var ex := float(L4.get("edge_x", 330))
	_shadow2.position = Vector2(ex - 96.0, shadow_y(time, 3.5, 5.0))
	_shadow3.position = Vector2(ex - 24.0, shadow_y(time, 5.0, C3_CUT + 0.3))
	# c3b: the hand slides a little along the edge; the flame (slow), its light breathes
	var h3 := lv(L4, "c3_hand_at", Vector2(128, 100))
	_hand3.position = h3 + Vector2(0, roundf(10.0 * ease01(time, C3_CUT, 8.6) * motion_k()))
	var lamp := lv(L4, "c3_lamp", Vector2(548, 92))
	_flame.position = lamp - Vector2(5, 10)
	_flame.frame = 0 if rm else int(floor(time * 6.0)) % 4
	_lampglow.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 61, 0.09), 0.0, 1.0))
	# c4: he looks up
	_alexei.frame = 1 if time >= C4_LOOK else 0
