extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Stamp (11 s) — the third match cut, on the rubber-stamp gesture (C4_DESIGN §2.9).
##   s1  0-3.5    the siding office desk from above: Alexei copies the card into his notebook (the pencil line
##                grows), Lev's hand slides the Russian half back into the box „C-17/45 – ПРИНЯТЬ“
##   s2  3.5-5    overhead: Lev's stamp comes down beside the box -- ПРИНЯТЬ (violet)
##                                                    -- hard cut on the stamp: same place, same frame --
##   s3  5-9      the registrar's stamp comes down -- ABGANG (red) (s3a, to 6.6) -> the counter „Auskunft ·
##                Abgleich“: Fengler's hands, the perforating machine splits a card in two (s3b)
##   s4  9-11     the foot of the shaft ladder between the card cabinets: Konrad, the German half in his coat --
##                medium (s4a, to 10.2: waist-up, figures stream's s4_konrad_medium; his gloved hand goes to the
##                coat over the card, he looks up the shaft into the daylight, snow sinking down it) -> the level's
##                annex at the game's scale (s4b): he looks up the ladder; control to Konrad
## Polish pass: Lev's cigarette smokes and the tea steams on the desk; each stamp lands with a small jolt; the
## counter stands in front of the level's card hall with its typists at work behind the frosted glass, the
## tubes humming; in s4 the level's annex, daylight and a few snowflakes falling down the shaft, dust in the
## tubes' light, Konrad looking up the ladder.
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
const S4_WIDE := 10.2                  # s4a medium -> s4b the annex at the game's scale (control to Konrad)
const S4M_DRIFT := 8.0                 # the medium's camera creeps this far to the right (parallax; rm halves it)

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
var s4m: Node2D
var _hall4m: Sprite2D
var _niche4m: Sprite2D
var _konrad4m: Sprite2D
var _fx4m: Node2D
var _slot: Node2D
var _fx1: Node2D
var _back3: Sprite2D
var _typists: Array = []
var _fx4: Node2D
var _smoke_tex: Texture2D
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
		{"t": 0.0, "bed": "c4cine_desk", "db": -6.0},
		say_at(LINES[0], 0.4),
		{"t": 3.5, "bed": "c4cine_stamp_ru", "db": -4.0},
		{"t": 5.0, "bed": "c4cine_stamp_de", "db": -4.0},
		say_at(LINES[1], 5.3, 1.4, 1.6),
		{"t": S3_CUT, "bed": "c4cine_annex", "db": -6.0},
	]


func _build() -> void:
	L4 = _layout_section("stamp")
	_smoke_tex = tex("places/smoke_light.png")
	_steam_tex = tex("places/steam_warm.png")
	_motes_tex = tex("places/motes.png")
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
	_fx1 = fx(s1, "SmokeAndTea", _draw_s1)
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
	_back3 = sprite("stamp/s3b_back.png", Vector2.ZERO, s3b)
	for ty in L4.get("s3_typists", []):
		var tsp := sprite("stamp/typist_%s.png" % str(ty[2]), Vector2(float(ty[0]), float(ty[1])), s3b, 16)
		_typists.append(tsp)
	sprite("stamp/s3b_counter.png", Vector2.ZERO, s3b)
	var sp := lv(L4, "s3_split", Vector2(78, 214))
	_split_l = sprite("stamp/split.png", sp, s3b, 2)
	_split_r = sprite("stamp/split.png", sp + Vector2(34, 0), s3b, 2)
	_split_r.frame = 1
	var piv := lv(L4, "s3_perf", Vector2(96, 120))
	_lever = sprite("stamp/lever.png", piv - lv(L4, "lever_pivot", Vector2(12, 12)), s3b, 3)
	_hands3 = sprite("stamp/s3b_hands.png", lv(L4, "s3b_hands_at", Vector2(170, 140)), s3b)
	s4m = group("LadderMedium")
	_hall4m = sprite("stamp/s4m_hall.png", Vector2.ZERO, s4m)
	_niche4m = sprite("stamp/s4m_niche.png", Vector2.ZERO, s4m)
	_konrad4m = sprite("stamp/s4_konrad_med.png", lv(L4, "s4m_at", Vector2(186, 44)), s4m, 2)
	_fx4m = fx(s4m, "ShaftLight", _draw_s4m)
	s4 = group("Ladder")
	sprite("stamp/s4_ladder.png", Vector2.ZERO, s4)
	_fx4 = fx(s4, "Shaft", _draw_s4)
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
	s4m.visible = sh == "s4" and time < S4_WIDE
	s4.visible = sh == "s4" and time >= S4_WIDE
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
	_hands3.position = lv(L4, "s3b_hands_at", Vector2(170, 140))      # the whole figure: no jump (round 10)
	for i in _typists.size():
		(_typists[i] as Sprite2D).frame = loop_frame(time, 16, 6.0, 0.37 * i)
	_back3.modulate = Color(1, 1, 1, 1) if rm else Color(1, 1, 1, clampf(0.97 + 0.03 * hnoise(time * 2.0, 75), 0, 1))
	_fx1.queue_redraw()
	# s2 / s3a: each stamp lands with a small jolt of the frame (the impressions stay where they are)
	s2.position = Vector2(0, jolt(time, STAMP_RU))
	s3a.position = Vector2(0, jolt(time, STAMP_DE))
	# s4a: medium -- his gloved hand goes to the coat over the card, he looks up the shaft; the camera creeps
	var cm := s4m_cam(time)
	_hall4m.position = Vector2(roundf(-cm * 0.35), 0)
	_niche4m.position = Vector2(roundf(-cm * 0.85), 0)
	var breath := 0.0 if rm else roundf(sin((time - 9.0) * 2.6) * 0.6)
	_konrad4m.position = lv(L4, "s4m_at", Vector2(186, 44)) + Vector2(roundf(-cm), breath)
	_konrad4m.frame = 1 if time >= S4_TOUCH else 0
	_fx4m.queue_redraw()
	# s4b: Konrad at the foot of the ladder at the game's scale, looking up the shaft (control to him)
	var ik: Dictionary = L4.get("s4_konrad", {})
	var kx := float(L4.get("s4_konrad_x", 214))
	var feet := float(LP.get("feet", 300))
	if time >= S4_WIDE and ik.has("look_side"):
		fig_frame(_konrad, ik, "look_side", 0 if rm else int(floor((time - S4_WIDE) * 5.0)), Vector2(kx, feet))
	elif time >= S4_TOUCH and time < S4_TOUCH + 0.75:
		fig_frame(_konrad, ik, "inspect_side", int(floor((time - S4_TOUCH) * 8.0)), Vector2(kx, feet))
	else:
		fig_frame(_konrad, ik, "idle_side", 0 if rm else int(floor(maxf(0.0, time - 9.0) * 5.0)), Vector2(kx, feet))
	_fx4.queue_redraw()


## s4a: the medium's camera x (creeps to the right; reduced motion halves it).
func s4m_cam(time: float) -> float:
	return S4M_DRIFT * motion_k() * ease01(time, 9.0, S4_WIDE)


## s4a: daylight down the shaft -- flakes sinking past the ladder, catching the light; dust in the tubes' light.
func _draw_s4m() -> void:
	if not s4m.visible:
		return
	var sh := lv(L4, "s4m_shaft", Vector2(108, 46))
	var k := motion_k()
	var cx := sh.x - s4m_cam(t) * 0.85
	for i in 14:
		var period := 2.6 + h01(i, 821) * 1.8
		var age := fposmod(t / period + h01(i, 823), 1.0)
		var x := cx - 70.0 + h01(i, 825) * 140.0 + sin(age * 7.0 + i) * 4.0 * k
		var y := sh.y + age * 280.0
		var a := clampf((1.0 - age) * 2.5, 0.0, 1.0) * (0.55 + 0.45 * clampf(1.0 - (y - 46.0) / 200.0, 0.0, 1.0))
		var sz := 1 + int(i % 4 == 0)
		_fx4m.draw_rect(Rect2(Vector2(roundf(x), roundf(y)), Vector2(sz, sz)), Color(0.88, 0.92, 0.97, a))
	draw_motes(_fx4m, _motes_tex, Rect2(240.0, 60.0, 400.0, 220.0), Vector2(470, 80), 230.0, t, 18, 8131, 0.45)


## The frame's jolt when a stamp lands (px down; reduced motion: none).
func jolt(time: float, m: Array) -> float:
	if reduced_motion():
		return 0.0
	var c := float(m[1])
	if time >= c and time < c + 0.05:
		return 2.0
	if time >= c + 0.05 and time < c + 0.1:
		return 1.0
	return 0.0


func _draw_s1() -> void:
	if not s1.visible:
		return
	var em := lv(L4, "s1_ember", Vector2(566, 289))
	draw_puffs(_fx1, _smoke_tex, 8, em, t, 4, 3.4, 70.0, -22.0, 0.42, 0.0, 5.0)
	var tea := lv(L4, "s1_tea", Vector2(466, 244))
	draw_puffs(_fx1, _steam_tex, 8, tea, t, 3, 2.6, 34.0, 8.0, 0.35, 0.5, 3.0)


func _draw_s4() -> void:
	if not s4.visible:
		return
	# daylight down the shaft: a few flakes sink along the ladder, dust turns in the tubes' light
	var sl := lv(L4, "s4_shaft_light", Vector2(128, 46))
	var k := motion_k()
	for i in 9:
		var period := 3.0 + h01(i, 811) * 2.0
		var age := fposmod(t / period + h01(i, 813), 1.0)
		var x := sl.x - 18.0 + h01(i, 815) * 36.0 + sin(age * 6.0 + i) * 3.0 * k
		var y := sl.y + age * 250.0
		var a := 0.9 * clampf((1.0 - age) * 3.0, 0.0, 1.0)
		_fx4.draw_rect(Rect2(Vector2(roundf(x), roundf(y)), Vector2(1 + i % 2, 1 + i % 2)), Color(0.86, 0.9, 0.96, a))
	draw_motes(_fx4, _motes_tex, Rect2(sl.x - 40.0, sl.y, 220.0, 250.0), sl + Vector2(20, 90), 170.0, t, 16, 8121,
		0.55)


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
