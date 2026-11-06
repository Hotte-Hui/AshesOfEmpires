extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Stamp (11 s) — the third match cut, on the rubber-stamp gesture (C4_DESIGN §2.9).
##   s1  0-3.5    the siding office desk from above: Alexei copies the card into his notebook (the pencil line
##                grows), Lev's hand slides the Russian half back into the box „C-17/45 – ПРИНЯТЬ“
##   s2  3.5-5    overhead: Lev's stamp comes down beside the box -- ПРИНЯТЬ (violet)
##                                                    -- hard cut on the stamp: same place, same frame --
##   s3  5-9      the registrar's stamp comes down -- ABGANG (red) (s3a, to 6.6) -> the counter „Auskunft ·
##                Abgleich“: Fengler's hands, the perforating machine splits a card in two (s3b)
##   s4  9-11     the foot of the shaft ladder between the card cabinets: Konrad, the German half in his coat
## Lines: Lev; the time in Berlin.

const DUR := 11.0
const SHOTS := [["s1", 0.0, 3.5], ["s2", 3.5, 5.0], ["s3", 5.0, 9.0], ["s4", 9.0, 11.0]]
const LINES := ["cin.c4.stamp.lev", "cin.c4.stamp.berlin"]
## stamp moves: [descend from, contact, lift from, gone]; thumps at the contact (c4cine_stamp_*; tests compare)
const STAMP_RU := [3.5, 3.86, 4.18, 4.55]
const STAMP_DE := [5.0, 5.36, 5.68, 6.05]
const S3_CUT := 6.6
const LEVER := [7.3, 7.42, 7.9, 8.05]  # the perforator's lever: starts down, down (the card splits), back up, up
const CARD_IN := [0.6, 2.3, 2.6]       # Lev's card: starts, at the slot, gone into the box
const NOTE_REVEAL := [[0.3, 1.7], [1.9, 3.3]]   # Alexei writes line 3, then line 4 (lines 1-2 already written)
const S4_TOUCH := 9.5                  # Konrad's hand to his coat (the card in it)

var L4: Dictionary = {}
var LP: Dictionary = {}
var s1: Node2D
var s2: Node2D
var s3a: Node2D
var s3b: Node2D
var s4: Node2D
var _notes_tex: Texture2D
var _notes: Node2D
var _card1: Sprite2D
var _lev: Sprite2D
var _pencil: Sprite2D
var _imp_ru: Sprite2D
var _stamp_ru: Sprite2D
var _hand_ru: Sprite2D
var _imp_de: Sprite2D
var _stamp_de: Sprite2D
var _hand_de: Sprite2D
var _lever: Sprite2D
var _split_l: Sprite2D
var _split_r: Sprite2D
var _hands3: Sprite2D
var _konrad: Sprite2D
var _slot: Node2D


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
		{"t": 0.0, "bed": "c4cine_desk", "db": -6.0},
		say_at(LINES[0], 0.4),
		{"t": 3.5, "bed": "c4cine_stamp_ru", "db": -4.0},
		{"t": 5.0, "bed": "c4cine_stamp_de", "db": -4.0},
		say_at(LINES[1], 5.3, 1.4, 1.6),
		{"t": S3_CUT, "bed": "c4cine_annex", "db": -6.0},
	]


func _build() -> void:
	L4 = _layout_section("stamp")
	LP = _layout_section("places")
	s1 = group("Desk")
	sprite("stamp/s1_desk.png", Vector2.ZERO, s1)
	_notes_tex = tex("stamp/s1_notes.png")
	_notes = fx(s1, "Notes", _draw_notes)
	_slot = fx(s1, "Slot", _draw_slot)
	_card1 = sprite("stamp/s1_card.png", Vector2.ZERO, s1)
	sprite("stamp/s1_boxfront.png", Vector2.ZERO, s1)
	_lev = sprite("stamp/s1_lev.png", Vector2.ZERO, s1)
	_pencil = sprite("stamp/s1_pencil.png", Vector2.ZERO, s1, 2)
	s2 = group("StampRU")
	sprite("stamp/s2_slip.png", Vector2.ZERO, s2)
	_imp_ru = sprite("stamp/imp_ru.png", Vector2.ZERO, s2)
	_stamp_ru = sprite("stamp/stamp_ru.png", Vector2.ZERO, s2)
	_hand_ru = sprite("stamp/hand_ru.png", Vector2.ZERO, s2)
	s3a = group("StampDE")
	sprite("stamp/s3a_card.png", Vector2.ZERO, s3a)
	_imp_de = sprite("stamp/imp_de.png", Vector2.ZERO, s3a)
	_stamp_de = sprite("stamp/stamp_de.png", Vector2.ZERO, s3a)
	_hand_de = sprite("stamp/hand_de.png", Vector2.ZERO, s3a)
	s3b = group("Counter")
	sprite("stamp/s3b_counter.png", Vector2.ZERO, s3b)
	var sp := lv(L4, "s3_split", Vector2(78, 214))
	_split_l = sprite("stamp/split.png", sp, s3b, 2)
	_split_r = sprite("stamp/split.png", sp + Vector2(34, 0), s3b, 2)
	_split_r.frame = 1
	var piv := lv(L4, "s3_perf", Vector2(96, 120))
	_lever = sprite("stamp/lever.png", piv - lv(L4, "lever_pivot", Vector2(12, 12)), s3b, 3)
	_hands3 = sprite("stamp/s3b_hands.png", lv(L4, "s3b_hands_at", Vector2(170, 140)), s3b)
	s4 = group("Ladder")
	sprite("stamp/s4_ladder.png", Vector2.ZERO, s4)
	_konrad = fig("stamp/s4_konrad.png", s4)


## Offset of a stamp above its contact point (overhead insert): down fast, hold, lift away (0 = pressed).
func stamp_off(time: float, m: Array) -> float:
	var up := -230.0
	if time < float(m[1]):
		return roundf(up * (1.0 - ease_in(time, float(m[0]), float(m[1]))))
	if time < float(m[2]):
		return 0.0
	return roundf(up * ease01(time, float(m[2]), float(m[3])))


func pressed(time: float, m: Array) -> bool:
	return time >= float(m[1])


func lever_frame(time: float) -> int:
	if time < float(LEVER[0]) or time >= float(LEVER[3]):
		return 0
	if time < float(LEVER[1]) or time >= float(LEVER[2]):
		return 1
	return 2


func card_pos(time: float) -> Vector2:
	var slot := lv(L4, "box_slot", Vector2(370, 86))
	var start := Vector2(338, 196)
	var stop := Vector2(slot.x - 33, slot.y - 6)
	return start.lerp(stop, ease01(time, float(CARD_IN[0]), float(CARD_IN[1]))).round()


func _apply(time: float) -> void:
	if s1 == null:
		return
	var sh := shot_at(time)
	s1.visible = sh == "s1"
	s2.visible = sh == "s2"
	s3a.visible = sh == "s3" and time < S3_CUT
	s3b.visible = sh == "s3" and time >= S3_CUT
	s4.visible = sh == "s4"
	var rm := reduced_motion()
	# s1: Lev's card goes into the box (the hand follows, then withdraws); the pencil writes
	var cp := card_pos(time)
	_card1.position = cp
	_card1.visible = time < float(CARD_IN[2])
	var tip := lv(L4, "lev_tip", Vector2(90, 114))
	var back := ease01(time, float(CARD_IN[2]), float(CARD_IN[2]) + 0.6) * 90.0
	_lev.position = Vector2(cp.x + 33.0 - tip.x, cp.y + 4.0 - tip.y - back).round()
	var pt := lv(L4, "pencil_tip", Vector2(60, 62))
	var pen := _pen_point(time)
	_pencil.position = (pen - pt).round()
	_pencil.frame = 0 if rm else int(floor(time * 7.0)) % 2
	_notes.queue_redraw()
	_slot.queue_redraw()
	# s2 / s3a: the stamps (same contact point, same frame -> the match cut)
	var c := lv(L4, "stamp_c", Vector2(320, 188))
	var isz := lv(L4, "imp_size", Vector2(232, 84))
	var ssz := lv(L4, "stamp_size", Vector2(236, 88))
	var knob := lv(L4, "hand_knob", Vector2(100, 150))
	for pair in [[_stamp_ru, _hand_ru, _imp_ru, STAMP_RU], [_stamp_de, _hand_de, _imp_de, STAMP_DE]]:
		var st: Sprite2D = pair[0]
		var hd: Sprite2D = pair[1]
		var im: Sprite2D = pair[2]
		var m: Array = pair[3]
		var off := stamp_off(time, m)
		st.position = (c - ssz * 0.5 + Vector2(0, off)).round()
		hd.position = (c - knob + Vector2(0, off - 6.0)).round()
		im.position = (c - isz * 0.5).round()
		im.visible = pressed(time, m)
	# s3b: the lever comes down, the card falls apart into its two halves
	_lever.frame = lever_frame(time)
	var gap := 0.0 if time < float(LEVER[1]) else roundf(5.0 * ease_out(time, float(LEVER[1]), float(LEVER[1]) + 0.35))
	var sp := lv(L4, "s3_split", Vector2(78, 214))
	_split_l.position = sp + Vector2(-gap, 0)
	_split_r.position = sp + Vector2(34.0 + gap, 0)
	_hands3.position = lv(L4, "s3b_hands_at", Vector2(170, 140)) + Vector2(0, -3.0 if (time > 6.85 and time < 7.0) else 0.0)
	# s4: Konrad at the foot of the ladder; his hand to the coat (inspect row) once
	var ik: Dictionary = L4.get("s4_konrad", {})
	var kx := float(L4.get("s4_konrad_x", 214))
	var feet := float(LP.get("feet", 300))
	if time >= S4_TOUCH and time < S4_TOUCH + 0.75:
		fig_frame(_konrad, ik, "inspect_side", int(floor((time - S4_TOUCH) * 8.0)), Vector2(kx, feet))
	else:
		fig_frame(_konrad, ik, "idle_side", 0 if rm else int(floor(maxf(0.0, time - 9.0) * 5.0)), Vector2(kx, feet))


## The pencil point: along line 3, then line 4 of the notebook, resting between them.
func _pen_point(time: float) -> Vector2:
	var spans: Array = L4.get("note_spans", [])
	if spans.size() < 4:
		return Vector2(120, 250)
	for i in 2:
		var r: Array = NOTE_REVEAL[i]
		var sp: Array = spans[2 + i]
		if time < float(r[1]) + (0.2 if i == 0 else 9.0):
			var u := clampf((time - float(r[0])) / (float(r[1]) - float(r[0])), 0.0, 1.0)
			return Vector2(lerpf(float(sp[0]), float(sp[2]), u), float(sp[3]) - 4.0)
	return Vector2(float(spans[3][2]), float(spans[3][3]) - 4.0)


func _draw_notes() -> void:
	if not s1.visible or _notes_tex == null:
		return
	var spans: Array = L4.get("note_spans", [])
	for i in spans.size():
		var sp: Array = spans[i]
		var x0 := float(sp[0])
		var w := float(sp[2]) - x0
		if i >= 2:
			var r: Array = NOTE_REVEAL[i - 2]
			w *= clampf((t - float(r[0])) / (float(r[1]) - float(r[0])), 0.0, 1.0)
		w = floorf(w)
		if w <= 0.0:
			continue
		var rect := Rect2(x0, float(sp[1]), w, float(sp[3]) - float(sp[1]))
		_notes.draw_texture_rect_region(_notes_tex, rect, rect)


func _draw_slot() -> void:
	if not s1.visible or t < float(CARD_IN[2]):
		return
	var slot := lv(L4, "box_slot", Vector2(370, 86))
	# the card now stands in the gap: its top edge shows between the others
	_slot.draw_rect(Rect2(Vector2(slot.x - 30, slot.y - 2), Vector2(60, 2)), Color("#c8b48e"))
	_slot.draw_rect(Rect2(Vector2(slot.x - 30, slot.y - 3), Vector2(60, 1)), Color("#e2d0aa"))
