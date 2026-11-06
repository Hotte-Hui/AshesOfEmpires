extends "res://scenes/cinematics/ch4p2_common/c4p2_cinematic.gd"
## LS_C4P2_Book (12 s) — Berlin -> Karsk, Monday -> Tuesday: THE shared object of round 10 (C4P2_DESIGN §2.9).
## Ekdahl's guidebook is the same object on both sides of the cut: on the tables one 3-D model seen from above
## (tools/pixelgen/env_c4p2_cine_book3d.py), in the macros one profile drawing (env_c4p2_cine_book.py) — the
## closing book in Berlin and the opening book in Karsk are the same pixels at the same place.
##   b1  0-3.5    close, the dining car from above: Konrad's bare hand slides the German half of card 0417 (upside
##                down) and the folded tracing onto page 213 (SLIDE_T) and withdraws (WITHDRAW_T); Ekdahl's grey
##                glove lifts the right half and swings it up (CLOSE_T); the man from the kiosk in the black window
##   b2  3.5-5    macro_locked, the book in profile at table height: the upper half comes down, the card's corner
##                between the pages, it shuts at BOOK_SHUT, a breath of dust
##                                   -- hard cut: the same camera, the same book, the same corner --
##   b3  5-9      macro_to_medium: Karsk, the canteen: the cover lifts under the grey glove (BOOK_OPEN); hard cut on
##                the movement (CUT_B3) to the canteen table from above while the camera settles back (SETTLE):
##                the book open at 212, the glove holds the page, Alexei's hand lies where Konrad's lay, his
##                fingers run along the card's perforation (FINGERS_RUN), tea steaming
##   b4  9-12     establishing: the depot showcase under floodlights -- the polished engine with ribbons, the works
##                band in two rows strikes up (MARCH_T0; the drum on the beat), the minder lights a cigarette
##                (MATCH_T), Ekdahl, the photographer, the depot chief, Alexei in front; behind the tarpaulin the
##                shadows of Kolonne 4 shovelling; control to Alexei
## Lines: Konrad's thought (b1), the place card (b3).  Beds (tools/audiogen/c4p2_cine_audio.py): c4p2cine_dining
## (cutlery, the onion-skin paper at SLIDE_T), c4p2cine_shut (the thud at BOOK_SHUT), c4p2cine_canteen (the cover
## at BOOK_OPEN, tea glasses), c4p2cine_band (the march from MARCH_T0, the match at MATCH_T[0]).

const DUR := 12.0
const SHOTS := [["b1", 0.0, 3.5], ["b2", 3.5, 5.0], ["b3", 5.0, 9.0], ["b4", 9.0, 12.0]]
const LINES := ["cin.c4p2.book.konrad", "cin.c4p2.book.karsk"]
const SLIDE_T := [0.3, 1.5]
const WITHDRAW_T := [1.6, 2.3]
const CLOSE_T := [2.6, 3.5]
const SHUT_FROM := 3.5
const BOOK_SHUT := 4.15
const OPEN_T := [5.05, 5.6]
const BOOK_OPEN := 5.12
const CUT_B3 := 5.62
const SETTLE := [5.62, 6.4, 10.0]
const FINGERS_RUN := 7.0
const RUN_LEN := 1.1
const MARCH_T0 := 9.15
const MARCH_BPM := 112.0
const MATCH_T := [10.05, 10.95]

var B: Dictionary = {}
var b1: Node2D
var b2: Node2D
var b3a: Node2D
var b3b: Node2D
var b4: Node2D
var _book1: Sprite2D
var _card: Sprite2D
var _trace: Sprite2D
var _khand: Sprite2D
var _glove1: Sprite2D
var _book2: Sprite2D
var _motes: Sprite2D
var _book3: Sprite2D
var _glove3a: Sprite2D
var _fingers: Sprite2D
var _band: Array = []
var _extras: Array = []
var _minder: Sprite2D
var _ekdahl: Sprite2D
var _alexei: Sprite2D
var _shadows: Array = []
var _beams: Sprite2D
var _fx3: Node2D
var _snow4: Node2D
var _t_tea: Texture2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return LINES.duplicate()


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 1.2},
		{"t": 0.0, "bed": "c4p2cine_dining", "db": -5.0},
		{"t": SHUT_FROM, "bed": "c4p2cine_shut", "db": -3.0},
		{"t": 5.0, "bed": "c4p2cine_canteen", "db": -5.0},
		{"t": MARCH_T0, "bed": "c4p2cine_band", "db": -3.0},
	]
	c += schedule([{"key": LINES[0], "at": 0.25, "dur": line_dur(LINES[0])},
		{"key": LINES[1], "at": 5.25, "dur": line_dur(LINES[1])}])
	c += optional_amb(5.0, "", 0.6)
	c += optional_amb(9.0, "amb_karsk_platform", 1.5)
	return c


## the book's frame in b1: 0 open (the card still a sprite) .. 6 the right half up at 80 degrees
func b1_frame(time: float) -> int:
	if time < float(CLOSE_T[0]):
		return 0
	return 1 + clampi(int(floor(ease_in(time, float(CLOSE_T[0]), float(CLOSE_T[1])) * 6.0)), 0, 5)


## the book's frame in the macros: 0 open 30 degrees .. 5 shut; b2 closes it, b3a opens it again
func macro_frame(time: float) -> int:
	if time < 5.0:
		return clampi(int(floor(ease_in(time, SHUT_FROM, BOOK_SHUT) * 5.0 + 0.0001)), 0, 5) if time < BOOK_SHUT else 5
	return 5 - clampi(int(floor(ease_out(time, float(OPEN_T[0]), float(OPEN_T[1])) * 5.0 + 0.0001)), 0, 5)


## the card's top-left during b1 (slides in from the right with Konrad's fingertips on its edge)
func card_pos(time: float) -> Vector2:
	var cs: Array = B.get("card_scr", [344, 196])
	var u := ease_out(time, float(SLIDE_T[0]), float(SLIDE_T[1]))
	return Vector2(float(cs[0]) + roundf(150.0 * (1.0 - u)), float(cs[1]) + roundf(30.0 * (1.0 - u)))


## b3b: the camera settles back after the cut (px the table still sits low)
func settle_dy(time: float) -> float:
	return roundf(float(SETTLE[2]) * (1.0 - ease_out(time, float(SETTLE[0]), float(SETTLE[1]))) * motion_k())


func march_frame(time: float) -> int:
	if time < MARCH_T0:
		return 0
	return int(floor((time - MARCH_T0) * MARCH_BPM / 60.0 * 2.0)) % 4


func _xy(a: Array) -> Vector2:
	return Vector2(float(a[0]), float(a[1]))


func _build() -> void:
	B = _layout_section("book")
	# ---------------------------------------------------------------- b1
	b1 = group("DiningCar")
	sprite("book/b1_bg.png", Vector2.ZERO, b1)
	sprite("book/b1_refl.png", Vector2(470, 50), b1)
	_book1 = cells("book/b1_book.png", b1, 640)
	_trace = sprite("book/tracing.png", Vector2.ZERO, b1)
	_card = sprite("book/card.png", Vector2.ZERO, b1)
	_glove1 = cells("book/b1_glove.png", b1, 520)
	_khand = cells("book/b1_khand.png", b1, 520)
	# ---------------------------------------------------------------- b2
	b2 = group("ShutBerlin")
	sprite("book/b2_bg.png", Vector2.ZERO, b2)
	_book2 = cells("book/b2_book.png", b2, 640)
	_motes = cells("book/motes.png", b2, 160, Vector2(440, 222))
	# ---------------------------------------------------------------- b3a (the macro) and b3b (the table)
	b3a = group("OpenKarsk")
	sprite("book/b3a_bg.png", Vector2.ZERO, b3a)
	_book3 = cells("book/b3a_book.png", b3a, 640)
	_glove3a = cells("book/b3a_glove.png", b3a, 300)
	b3b = group("Canteen")
	sprite("book/b3_bg.png", Vector2.ZERO, b3b)
	var gt: Array = B.get("gtip", [[430, 360], [430, 360], [430, 360], [430, 360]])
	var gr: Array = B.get("glove_rest", [262, 214])
	sprite("book/b3_glove.png", _xy(gr) - _xy(gt[0]), b3b)
	_fingers = cells("book/b3_alexei.png", b3b, 520)
	_fx3 = fx(b3b, "Tea", _draw_tea)
	# ---------------------------------------------------------------- b4
	b4 = group("Showcase")
	sprite("book/b4_bg.png", Vector2.ZERO, b4)
	_beams = glow("book/b4_beams.png", b4)
	var tp: Array = B.get("b4_tarp", [520, 640, 150, 262])
	for k in 3:
		_shadows.append(cells("book/b4_shadow_%d.png" % k, b4, 48, Vector2(float(tp[0]) + 22.0 + k * 38.0,
			float(tp[3]) - 72.0)))
	var pp: Dictionary = B.get("b4_people", {})
	var keys: Array = pp.keys()
	keys.sort_custom(func(a, b): return float(pp[a][1]) < float(pp[b][1]))
	for key in keys:
		var e: Array = pp[key]
		var cw := int(e[3]) if e.size() > 3 else 32
		var s := cells("book/b4_%s.png" % key, b4, cw, Vector2(float(e[0]), float(e[1])))
		if str(key).begins_with("band_"):
			_band.append(s)
		elif str(key).begins_with("extra_"):
			_extras.append(s)
		elif key == "ekdahl":
			_ekdahl = s
		elif key == "minder":
			_minder = s
		elif key == "alexei":
			_alexei = s
	glow("book/b4_halos.png", b4)
	_snow4 = snow(b4, Rect2(-20, 30, 680, 300), [
		{"count": 50, "v": Vector2(-6, 16), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#aab4c4"), "sway": 2.0},
		{"count": 18, "v": Vector2(-10, 28), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#e6ecf2"), "sway": 3.0},
	], 4401)
	_t_tea = tex("book/tea_steam.png")


func _apply(time: float) -> void:
	if b1 == null:
		return
	var sh := shot_at(time)
	b1.visible = sh == "b1"
	b2.visible = sh == "b2"
	b3a.visible = sh == "b3" and time < CUT_B3
	b3b.visible = sh == "b3" and time >= CUT_B3
	b4.visible = sh == "b4"
	var gt: Array = B.get("gtip", [[430, 360], [430, 360], [430, 360], [430, 360]])
	var gr: Array = B.get("glove_rest", [262, 214])
	var kt: Array = B.get("ktip", [62, 70])
	var cs: Array = B.get("card_scr", [344, 196])
	# b1: the book, the card + tracing sliding in, Konrad's hand, Ekdahl's glove
	var f1 := b1_frame(time)
	_book1.frame = f1
	var cp := card_pos(time)
	_card.visible = f1 == 0
	_trace.visible = f1 == 0
	_card.position = cp
	var ts: Array = B.get("trace_scr", [334, 252])
	_trace.position = cp + _xy(ts) - _xy(cs)
	var wd := ease_in(time, float(WITHDRAW_T[0]), float(WITHDRAW_T[1]))
	_khand.visible = time < float(WITHDRAW_T[1]) + 0.05
	_khand.frame = 1 if time >= float(WITHDRAW_T[0]) else 0
	_khand.position = cp + Vector2(58.0, 22.0) - _xy(kt) + Vector2(roundf(120.0 * wd), roundf(90.0 * wd))
	var edges: Array = B.get("edge_b1", [])
	if f1 >= 1 and edges.size() > f1:
		_glove1.frame = 2
		_glove1.position = _xy(edges[f1]) - _xy(gt[2])
	elif time >= 2.1 and edges.size() > 0:
		_glove1.frame = 1
		var u := ease01(time, 2.1, float(CLOSE_T[0]))
		_glove1.position = (_xy(gr).lerp(_xy(edges[0]), u) - _xy(gt[1])).round()
	else:
		_glove1.frame = 0
		_glove1.position = _xy(gr) - _xy(gt[0])
	# b2: the last degrees and the shut; the dust
	_book2.frame = macro_frame(time)
	_motes.visible = time >= BOOK_SHUT
	_motes.frame = once_frame(time, BOOK_SHUT, BOOK_SHUT + 0.8, 8)
	# b3a: the same book opening under the glove (its fingertips under the upper block's fore-edge)
	var f3 := macro_frame(time)
	_book3.frame = f3
	var em: Array = B.get("edge_m", [])
	var gs: Array = B.get("gtip_side", [])
	_glove3a.frame = f3
	if em.size() > f3 and gs.size() > f3:
		_glove3a.position = _xy(em[f3]) - _xy(gs[f3])
	# b3b: the camera settles; Alexei's fingers run along the perforation of the German half
	b3b.position = Vector2(0.0, settle_dy(time))
	var at: Array = B.get("atip", [62, 70])
	var run := ease01(time, FINGERS_RUN, FINGERS_RUN + RUN_LEN)
	_fingers.frame = 1 if time >= FINGERS_RUN else 0
	_fingers.position = (_xy(cs) + Vector2(6.0, 12.0 + 18.0 * run) - _xy(at)).round()
	# b4: the band on the beat, the shadows behind the canvas, the match, the people breathing
	var mf := march_frame(time)
	for i in _band.size():
		(_band[i] as Sprite2D).frame = (mf + (0 if i % 2 == 0 else 1)) % 4
	for i in _extras.size():
		var ex: Sprite2D = _extras[i]
		ex.frame = p2_loop_frame(time, 3.0, maxi(1, ex.hframes), i * 2)
	for k in _shadows.size():
		(_shadows[k] as Sprite2D).frame = p2_loop_frame(time, 8.0 * motion_k(), 8, k * 3)
	if _minder:
		_minder.frame = 0 if time < float(MATCH_T[0]) else once_frame(time, float(MATCH_T[0]), float(MATCH_T[1]), 6)
	if _ekdahl:
		_ekdahl.frame = p2_loop_frame(time, 4.0, maxi(1, _ekdahl.hframes))
	if _alexei:
		_alexei.frame = p2_loop_frame(time, 4.0, maxi(1, _alexei.hframes), 3)
	_beams.modulate = Color(1, 1, 1, clampf(0.9 + 0.06 * hnoise(time * 0.7, 19), 0.0, 1.0))
	_snow4.set_time(time)
	_fx3.queue_redraw()


func _draw_tea() -> void:
	var time := t
	if time < CUT_B3 or time >= 9.0:
		return
	for i in 2:
		var p := Vector2(112, 160) if i == 0 else Vector2(538, 114)
		puffs(_fx3, _t_tea, 8, time, 2.0 + i * 0.4, 12.0, 0.6, 2.2, p, Vector2(2, -9), 491 + i, Color(1, 1, 1, 0.5),
			Vector2(1, 1))
