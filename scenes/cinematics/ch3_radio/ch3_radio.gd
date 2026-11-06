extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## LS_C3_Radio (30.8 s) — the night after the first conference day (C3P2_DESIGN §2.9).  Quiet, intimate.
##   r1  0-4     the station square from the station roof: Hotel Europa (Konrad) and Hotel Nord (Alexei) face
##               each other across the snow, one lit window each; steam of the 23.40 drifts off; the interval
##               signal of Radio Veltrava
##   r2  4-10.5  Alexei's room: the Bakelite radio at the window, the tea glass, the Russian news; he reaches for
##               the tuning knob ("auf Deutsch sagen sie es anders") and turns it
##   r3  10.5-17.3  match cut on the dial: the needle completes its sweep in Konrad's room — the same radio model,
##               the German news; his pencil stops at "Begleitgut"
##   r4  17.3-22.3  split: the two doors from the floor, a shadow in the light of each gap, a folded note slides
##               under each; close-up of the note in two languages
##   r5  22.3-26.3  Café „Korridor": chairs on the tables, Elena's table with an untouched glass; the station
##               clock across the square says 0.10
##   r6  26.3-30.8  the same square: two hotel doors open at once, two men walk out into the snow, their
##               tracks converge on the dark east wing of the palais
## Inner lines (ctx.choices): Alexei c3a ask_elena -> cafe, note_alone -> alone, else base; Konrad c3b
## share_protocol -> share, search_elena -> search, report_delegation -> report, else base.  Lines about the
## radio follow the broadcasts, lines about Elena or the note follow the note (schedule()).
## Round 10: the square is layered (square_bg with margins, the roof parapet square_near in front): r1 cranes down
## onto it, r6 trucks right after the two men; steam of the 23.40 rises from behind the parapet, a taxi drives the far
## street.  The rooms have the chairs in front of the men, a coffee cup steaming in Konrad's room, a passing car's
## headlights sweep Alexei's ceiling; the keys hang in both locks; the café drifts (Elena's table in front), the
## station clock's second hand runs, the café cat sleeps on the bar.
## Round 11: the steam of the 23.40 billows up from the platforms behind the parapet in soft lit clouds (no dithered
## patches) and stays in front of the square; the lamp pools are lamp light on snow; r6 pushes in slowly toward the
## dark east wing: the doors open, the two men step out at a readable size, their shadows thrown ahead by the door
## light, then the picture dissolves a minute on -- two trodden tracks of footprints converge across the snow and
## the men, small now, reach the wing's dark door; the passing car's headlights sweep Alexei's walls and ceiling
## edge (never the glass); the café drifts in parallax past Elena's table and a car's light crosses the room.
## Art: tools/pixelgen/env_c3p2_cine_radio.py (+ _square, _rooms, _cafe, _life) -> assets/cinematics/c3p2/radio/.

const DUR := 30.8
const SHOTS := [["r1", 0.0, 4.0], ["r2", 4.0, 10.5], ["r3", 10.5, 17.3], ["r4", 17.3, 22.3], ["r5", 22.3, 26.3],
	["r6", 26.3, 30.8]]
const NOTE_CLOSE := 19.3             # r4: doors -> the note close-up
## radio dial (match cut): centre, needle angles (degrees clockwise from 12) of the two Veltrava services
const DIAL := Vector2(330, 182)
const DIAL_R := 24
const ANG_RU := -60.0
const ANG_DE := 40.0
const TUNE := [9.85, 10.85]          # the needle sweep (starts in r2, ends in r3)
const ARM := [9.15, 9.5, 9.8]        # reach, on the knob, turning
## round 11: the arm sheet's frames 1..5 (lift, on the way, nearly there, fingers on the knob, turning it)
const ARM_KEYS := [9.15, 9.3, 9.45, 9.6, 9.85]
## r3: Konrad's writing hand -- HAND_POS positions along pad_line x 2 strokes, then the positions with the pencil up
const HAND_POS := 6
const WALK_START := 26.9
const DOORS_OPEN := 26.6
const DOORS_SHUT := 28.6
## r6: the men walk out at WALK_SPEED m/s, then the picture dissolves (LATER = start, end) to a minute later, when
## they have walked LATE_FROM .. LATE_TO of their way to the wing; the camera pushes in toward the wing by PUSH
const WALK_SPEED := 2.6
const LATER := [28.55, 29.35]
const LATE_FROM := 0.80
const LATE_TO := 0.97
const PUSH := 0.16
const PUSH_AT := Vector2(372, 152)
const CAFE_CAR := [23.4, 24.9]       # r5: a car passes outside, its lights cross the café
const TAXI := [0.4, 3.95]            # r1: the taxi drives along the far street
const SWEEP := [5.4, 6.9]            # r2: a passing car's headlights sweep Alexei's ceiling
const SECONDS0 := 14.0               # r5: the station clock's second hand at the cut (0.10 and 14 s)

const LINE_TIME := "cin.c3p2.radio.time"
const LINE_RU := "cin.c3p2.radio.ru"
const LINE_DE := "cin.c3p2.radio.de"
const LINE_NOTE := "cin.c3p2.radio.note"
## reading time per line (seconds), every line at <= 19 characters per second.  Round 11: the two broadcasts
## are the condensed excerpts (72 characters each, 3.8 s), so each line plays over its own picture: the Russian
## news and Alexei's thought in his room (r2), the German news and Konrad's thought in his (r3), the note's text on
## the note's close-up (r4), the lines about Elena or the note over the café and the square (r5/r6).
const LINE_DUR := {"cin.c3p2.radio.time": 3.0, "cin.c3p2.radio.ru": 3.8, "cin.c3p2.radio.de": 3.8,
	"cin.c3p2.radio.note": 2.6, "cin.c3p2.radio.alexei.base": 2.8, "cin.c3p2.radio.alexei.cafe": 3.6,
	"cin.c3p2.radio.alexei.alone": 3.0, "cin.c3p2.radio.konrad.base": 2.7, "cin.c3p2.radio.konrad.share": 4.5,
	"cin.c3p2.radio.konrad.search": 3.4, "cin.c3p2.radio.konrad.report": 2.6}
## where each line wants to start (schedule() only ever pushes a line later)
const LINE_AT := {"time": 0.5, "ru": 3.65, "alexei_radio": 7.55, "de": 10.55, "konrad_radio": 14.45, "note": 19.4,
	"after_note": 22.35}

var line_alexei := "cin.c3p2.radio.alexei.base"
var line_konrad := "cin.c3p2.radio.konrad.base"
## when the pencil stops (the German line reaches "Begleitgut"); set by the line schedule
var pencil_stop := 14.6
var _line_cues: Array = []

var square: Node2D
var room_a: Node2D
var room_k: Node2D
var doors: Node2D
var note: Node2D
var cafe: Node2D
var _win_k: Sprite2D
var _win_a: Sprite2D
var _sq_glow: Sprite2D
var _steam: Node2D
var _steam_tex: Texture2D
var _door_k: Sprite2D
var _door_a: Sprite2D
var _walkers: Node2D
var _walk_k: Texture2D
var _walk_a: Texture2D
var _snow_sq: Node2D
var _radio_a: Sprite2D
var _radio_k: Sprite2D
var _dglow_a: Sprite2D
var _dglow_k: Sprite2D
var _eye_a: Sprite2D
var _eye_k: Sprite2D
var _needle_a: Node2D
var _needle_k: Node2D
var _arm: Sprite2D
var _fig_a: Sprite2D
var _fig_k: Sprite2D
var _tea: Sprite2D
var _hand: Sprite2D
var _scribble: Node2D
var _lamp: Sprite2D
var _snow_a: Node2D
var _snow_k: Node2D
var _gap: Node2D
var _note_l: Sprite2D
var _note_r: Sprite2D
var _note_close: Sprite2D
var _motes: Node2D
var _clock: Node2D
var _cafe_glow: Sprite2D
var _snow_c: Node2D
var _sq_mid: Node2D
var _sq_near: Node2D
var _taxi: Node2D
var _taxi_tex: Texture2D
var _chair_a: Sprite2D
var _chair_k: Sprite2D
var _cup: Sprite2D
var _sweep: Node2D
var _keys: Array = []
var _cafe_back: Node2D
var _cafe_front: Sprite2D
var _cat: Sprite2D
var _couple: Node2D
var _couple_m: Texture2D
var _couple_w: Texture2D
var _walk_far_k: Texture2D
var _walk_far_a: Texture2D
var _cafe_light: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


# ------------------------------------------------------------------ lines
func _on_configured() -> void:
	match choice("c3a_choose"):
		"ask_elena":
			line_alexei = "cin.c3p2.radio.alexei.cafe"
		"note_alone":
			line_alexei = "cin.c3p2.radio.alexei.alone"
		_:
			line_alexei = "cin.c3p2.radio.alexei.base"
	match choice("c3b_choose"):
		"share_protocol":
			line_konrad = "cin.c3p2.radio.konrad.share"
		"search_elena":
			line_konrad = "cin.c3p2.radio.konrad.search"
		"report_delegation":
			line_konrad = "cin.c3p2.radio.konrad.report"
		_:
			line_konrad = "cin.c3p2.radio.konrad.base"
	var a_radio := line_alexei.ends_with(".base")
	var k_radio := line_konrad.ends_with(".base") or line_konrad.ends_with(".report")
	var L: Array = [_l(LINE_TIME, LINE_AT["time"]), _l(LINE_RU, LINE_AT["ru"])]
	if a_radio:
		L.append(_l(line_alexei, LINE_AT["alexei_radio"]))
	L.append(_l(LINE_DE, LINE_AT["de"]))
	if k_radio:
		L.append(_l(line_konrad, LINE_AT["konrad_radio"]))
	L.append(_l(LINE_NOTE, LINE_AT["note"]))
	if not a_radio:
		L.append(_l(line_alexei, LINE_AT["after_note"]))
	if not k_radio:
		L.append(_l(line_konrad, LINE_AT["after_note"]))
	_line_cues = schedule(L)
	for c in _line_cues:
		if c["say"] == LINE_DE:
			# the pencil stops where the German line says "Begleitgut"
			pencil_stop = float(c["t"]) + float(c["dur"]) * 0.55
	pencil_stop = clampf(pencil_stop, 12.0, 16.6)


func _l(key: String, at: float) -> Dictionary:
	return {"key": key, "at": at, "dur": float(LINE_DUR.get(key, 3.0))}


func chosen_lines() -> Array:
	var out: Array = []
	for c in _line_cues:
		out.append(c["say"])
	return out


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 2.0},
		{"t": 0.0, "amb": "", "fade": 1.5},
		{"t": 0.0, "bed": "c3p2cine_interval", "db": -5.0},              # Radio Veltrava across the square
		{"t": 0.4, "sfx": "wind_gust", "db": -19.0},
		{"t": 3.6, "bed": "c3p2cine_news_ru", "db": -4.0},
		{"t": TUNE[0] - 0.05, "bed": "c3p2cine_tune", "db": -7.0},
		{"t": 10.5, "bed": "c3p2cine_news_de", "db": -4.0},
		{"t": 10.75, "loop": "c3p2cine_pencil", "key": "c3p2_pencil", "db": -11.0, "fade": 0.1},
		{"t": pencil_stop, "loop_stop": "c3p2_pencil", "fade": 0.06},
		{"t": 17.3, "bed": "c3p2cine_corridor", "db": -6.0},
		{"t": NOTE_CLOSE + 0.1, "sfx": "paper_rustle", "db": -9.0, "pv": 0.03},
		{"t": 22.3, "bed": "c3p2cine_cafe", "db": -7.0},
		{"t": 26.3, "bed": "c3p2cine_doors", "db": -5.0},
		{"t": WALK_START - 0.1, "bed": "c3p2cine_snowsteps", "db": -8.0},
	]
	c.append_array(_line_cues)
	return c


# ------------------------------------------------------------------ build
func _build() -> void:
	layout = _layout_section("radio")
	# r1 / r6: the square
	square = group("Square")
	_sq_mid = group("Mid", square)
	sprite("radio/square_bg.png", _lv("square_bg_at"), _sq_mid)
	_door_k = sprite("radio/door_konrad.png", _lv("door_konrad"), _sq_mid)
	_door_a = sprite("radio/door_alexei.png", _lv("door_alexei"), _sq_mid)
	_win_k = sprite("radio/win_konrad.png", _lv("win_konrad"), _sq_mid)
	_win_a = sprite("radio/win_alexei.png", _lv("win_alexei"), _sq_mid)
	_taxi_tex = tex("radio/taxi.png")
	_taxi = Node2D.new()
	_taxi.name = "Taxi"
	_taxi.draw.connect(_draw_taxi)
	_sq_mid.add_child(_taxi)
	_sq_glow = sprite("radio/square_glow.png", Vector2.ZERO, _sq_mid, 1, true)
	_walk_k = tex("radio/walker_konrad.png")
	_walk_a = tex("radio/walker_alexei.png")
	_walk_far_k = tex("radio/walker_far_konrad.png")
	_walk_far_a = tex("radio/walker_far_alexei.png")
	_walkers = Node2D.new()
	_walkers.name = "Walkers"
	_walkers.draw.connect(_draw_walkers)
	_sq_mid.add_child(_walkers)
	_couple_m = tex("radio/couple_man.png") if (layout.get("couple", {}) as Dictionary).size() > 0 else null
	_couple_w = tex("radio/couple_woman.png") if (layout.get("couple", {}) as Dictionary).size() > 0 else null
	_couple = Node2D.new()
	_couple.name = "Couple"
	_couple.draw.connect(_draw_couple)
	_sq_mid.add_child(_couple)
	_steam_tex = tex("radio/steam.png")
	_steam = Node2D.new()
	_steam.name = "Steam"
	_steam.draw.connect(_draw_steam)
	square.add_child(_steam)
	_sq_near = group("Near", square)
	sprite("radio/square_near.png", _lv("near_at"), _sq_near)
	sprite("radio/near_glow.png", _lv("near_lantern") - Vector2(60, 45), _sq_near, 1, true)
	_snow_sq = snow(square, Rect2(0, 0, 640, 360), [
		{"count": 110, "v": Vector2(4, 13), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 50, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0},
		{"count": 16, "v": Vector2(9, 40), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#dee2e7"), "sway": 4.0}], 8101)
	# r2: Alexei's room
	room_a = group("RoomAlexei")
	sprite("radio/room_alexei.png", Vector2.ZERO, room_a)
	_sweep = Node2D.new()
	_sweep.name = "HeadlightSweep"
	_sweep.material = additive()
	_sweep.draw.connect(_draw_sweep)
	room_a.add_child(_sweep)
	_snow_a = snow(room_a, Rect2(168, 52, 324, 162), [
		{"count": 40, "v": Vector2(-3, 12), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 16, "v": Vector2(-5, 22), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 2.5}],
		8102, Rect2(172, 56, 316, 146))
	_radio_a = sprite("radio/radio.png", _lv("radio"), room_a)
	_dglow_a = sprite("radio/dial_glow.png", Vector2.ZERO, room_a, 1, true)
	_eye_a = sprite("radio/magic_eye.png", _lv("magic_eye") - Vector2(3, 3), room_a, 3, true)
	_needle_a = _needle_node(room_a)
	_tea = sprite("radio/steam_tea.png", _lv("steam_tea"), room_a, 6)
	_arm = sprite("radio/arm_alexei.png", _lv("arm_alexei"), room_a, ARM_KEYS.size() + 1)
	_fig_a = sprite("radio/fig_alexei.png", _lv("fig_alexei"), room_a, 2)
	_chair_a = sprite("radio/chair_alexei.png", _lv("chair_alexei"), room_a)
	# r3: Konrad's room
	room_k = group("RoomKonrad")
	sprite("radio/room_konrad.png", Vector2.ZERO, room_k)
	_snow_k = snow(room_k, Rect2(168, 52, 324, 162), [
		{"count": 40, "v": Vector2(3, 12), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 16, "v": Vector2(5, 22), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 2.5}],
		8103, Rect2(172, 56, 316, 146))
	_radio_k = sprite("radio/radio.png", _lv("radio"), room_k)
	_dglow_k = sprite("radio/dial_glow.png", Vector2.ZERO, room_k, 1, true)
	_lamp = sprite("radio/lamp_glow.png", Vector2.ZERO, room_k, 1, true)
	_eye_k = sprite("radio/magic_eye.png", _lv("magic_eye") - Vector2(3, 3), room_k, 3, true)
	_needle_k = _needle_node(room_k)
	_scribble = Node2D.new()
	_scribble.name = "Scribble"
	_scribble.draw.connect(_draw_scribble)
	room_k.add_child(_scribble)
	_cup = sprite("radio/steam_tea.png", _lv("steam_cup"), room_k, 6)
	_hand = sprite("radio/hand_konrad.png", _lv("hand_konrad"), room_k, 3 * HAND_POS)
	_fig_k = sprite("radio/fig_konrad.png", _lv("fig_konrad"), room_k, 2)
	_chair_k = sprite("radio/chair_konrad.png", _lv("chair_konrad"), room_k)
	# r4: the doors, the note
	doors = group("Doors")
	sprite("radio/doors.png", Vector2.ZERO, doors)
	_note_l = sprite("radio/note_fold.png", Vector2.ZERO, doors)
	_note_r = sprite("radio/note_fold.png", Vector2.ZERO, doors)
	for n in [_note_l, _note_r]:
		n.region_enabled = true
	_gap = Node2D.new()
	_gap.name = "GapShadows"
	_gap.draw.connect(_draw_gap)
	doors.add_child(_gap)
	for k_ in ["key_214", "key_317"]:
		var ks := sprite("radio/keyfob.png", _lv(k_) - Vector2(9, 2), doors, 3, false, 2)
		ks.frame = 0 if k_ == "key_214" else 3
		_keys.append(ks)
	note = group("Note")
	_note_close = sprite("radio/note_close.png", Vector2.ZERO, note)
	_motes = Node2D.new()
	_motes.name = "Motes"
	_motes.draw.connect(_draw_motes)
	note.add_child(_motes)
	# r5: the café
	cafe = group("Cafe")
	_cafe_back = group("Back", cafe)
	sprite("radio/cafe.png", _lv("cafe_at"), _cafe_back)
	var cw: Array = layout.get("cafe_win", [43, 61, 597, 196])
	_snow_c = snow(_cafe_back, Rect2(40, 40, 560, 160), [
		{"count": 60, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 24, "v": Vector2(7, 26), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0}],
		8104, Rect2(float(cw[0]), float(cw[1]), float(cw[2]) - float(cw[0]), float(cw[3]) - float(cw[1])))
	_clock = Node2D.new()
	_clock.name = "ClockHands"
	_clock.draw.connect(_draw_clock)
	_cafe_back.add_child(_clock)
	_cafe_glow = sprite("radio/cafe_glow.png", Vector2.ZERO, _cafe_back, 1, true)
	_cat = sprite("radio/cat.png", _lv("cat_at"), _cafe_back, 2)
	_cafe_light = Node2D.new()
	_cafe_light.name = "CarLight"
	_cafe_light.material = additive()
	_cafe_light.draw.connect(_draw_cafe_light)
	cafe.add_child(_cafe_light)
	_cafe_front = sprite("radio/cafe_fg.png", _lv("cafe_fg_at"), cafe)


func _lv(key: String) -> Vector2:
	var v = layout.get(key)
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return Vector2.ZERO


func _needle_node(parent: Node) -> Node2D:
	var n := Node2D.new()
	n.name = "Needle"
	n.draw.connect(_draw_needle.bind(n))
	parent.add_child(n)
	return n


# ------------------------------------------------------------------ frame
func _apply(time: float) -> void:
	if square == null:
		return
	var sh := shot_at(time)
	square.visible = sh == "r1" or sh == "r6"
	room_a.visible = sh == "r2"
	room_k.visible = sh == "r3"
	doors.visible = sh == "r4" and time < NOTE_CLOSE
	note.visible = sh == "r4" and time >= NOTE_CLOSE
	cafe.visible = sh == "r5"
	var rm := reduced_motion()
	var k := motion_k()
	# r1/r6: lit windows (r1), the open doors (r6), steam, snow, walkers
	var r6 := sh == "r6"
	_win_k.visible = not r6
	_win_a.visible = not r6
	var later := ramp01(time, float(LATER[0]), float(LATER[1]))
	_door_k.visible = r6 and time >= DOORS_OPEN and later < 1.0
	_door_a.visible = r6 and time >= DOORS_OPEN + 0.08 and later < 1.0
	_door_k.modulate = Color(1, 1, 1, 1.0 - later)
	_door_a.modulate = Color(1, 1, 1, 1.0 - later)
	_sq_glow.modulate = Color(1, 1, 1, 1.0 if not r6 else 0.75)
	var cam := square_camera(time)
	_sq_mid.position = cam[0]
	_sq_near.position = cam[1]
	_steam.position = ((cam[0] + cam[1]) * 0.5).round()
	# r6: a slow push-in toward the dark east wing, the whole square (the parapet a little faster: parallax)
	var push := square_push(time)
	square.scale = Vector2(push, push)
	square.position = PUSH_AT - PUSH_AT * push
	_snow_sq.set_time(time * (0.6 if rm else 1.0))
	_steam.queue_redraw()
	_taxi.queue_redraw()
	_walkers.queue_redraw()
	_couple.queue_redraw()
	# r2/r3: the dial, the magic eye, the needle sweep (it starts in Alexei's room and ends in Konrad's)
	var tune := clampf((time - TUNE[0]) / (TUNE[1] - TUNE[0]), 0.0, 1.0)
	var searching := time >= TUNE[0] and time < TUNE[1]
	var eye := 2 if not searching else (0 if tune < 0.75 else 1)
	_eye_a.frame = eye
	_eye_k.frame = eye
	var glow := 0.92 + 0.05 * hnoise(time * 1.7, 11) * (0.4 if rm else 1.0)
	if searching and not rm:
		glow -= 0.18 * absf(sin(tune * PI * 3.0))
	_dglow_a.modulate = Color(1, 1, 1, glow)
	_dglow_k.modulate = Color(1, 1, 1, glow)
	_lamp.modulate = Color(1, 1, 1, 0.95)
	_needle_a.queue_redraw()
	_needle_k.queue_redraw()
	_snow_a.set_time(time * (0.6 if rm else 1.0))
	_snow_k.set_time(time * (0.6 if rm else 1.0))
	_tea.frame = int(floor(time * 5.0 * k)) % 6
	_cup.frame = int(floor(time * 4.0 * k + 3.0)) % 6
	_sweep.queue_redraw()
	# Alexei's right arm (the figures stream's sheet holds it in every frame, frame 0 = resting on the table):
	# lifts, reaches, closes on the knob, turns it
	var af := 0
	for i in ARM_KEYS.size():
		if time >= float(ARM_KEYS[i]):
			af = mini(i + 1, _arm.hframes - 1)
	_arm.frame = af
	_fig_a.frame = int(floor((time + 0.4) / 2.1)) % 2 if not rm else 0
	_fig_k.frame = int(floor((time + 1.1) / 2.3)) % 2 if not rm else 0
	_apply_pencil_hand(time, rm)
	_scribble.queue_redraw()
	# r4: notes slide in under both doors (left first), the shadows of the feet in the light of the gaps
	_slide(_note_l, 0, time, 17.75)
	_slide(_note_r, 1, time, 18.3)
	_gap.queue_redraw()
	for i in _keys.size():
		# the note pushed against the door's foot shivers the key's fob for a moment
		var t0 := 17.75 + i * 0.55 + 0.2
		var sw := 0
		if not rm and time >= t0 and time < t0 + 0.6:
			sw = [1, 2, 1, 0, 2, 0][clampi(int((time - t0) / 0.1), 0, 5)]
		(_keys[i] as Sprite2D).frame = i * 3 + sw
	if note.visible:
		var drift := clampf((time - NOTE_CLOSE) / 3.0, 0.0, 1.0) * 3.0 * k
		_note_close.position = Vector2(roundf(-drift), 0)
	_motes.queue_redraw()
	# r5
	_snow_c.set_time(time * (0.6 if rm else 1.0))
	_clock.queue_redraw()
	_cafe_glow.modulate = Color(1, 1, 1, 0.94 + 0.04 * hnoise(time * 2.4, 31) * (0.4 if rm else 1.0))
	# a slow lateral drift: the room 5 px, Elena's table in front 28 px (parallax), moving from the first frame
	var cu := clampf((time - 22.3) / 4.0, 0.0, 1.0)
	cu = cu * (2.0 - cu) * k
	_cafe_back.position = Vector2(roundf(-5.0 * cu), 0)
	_cafe_front.position = _lv("cafe_fg_at") + Vector2(roundf(-28.0 * cu), 0)
	_cafe_light.queue_redraw()
	_cat.frame = 1 if (not rm and fposmod(time, 2.6) > 2.15) else 0


## r6: the push-in toward the east wing (scale of the square group around PUSH_AT), 1 outside r6.
func square_push(time: float) -> float:
	if time < 26.3:
		return 1.0
	var u := clampf((time - 26.3) / 4.5, 0.0, 1.0)
	return 1.0 + PUSH * (u * u * (3.0 - 2.0 * u)) * motion_k()


## r1 cranes down onto the square, r6 trucks right after the two men: [mid offset, near offset] (parallax).
func square_camera(time: float) -> Array:
	var k := motion_k()
	if time < 4.5:
		var u := ramp01(time, 0.0, 4.0)
		return [Vector2(0, roundf(lerpf(5.0, 0.0, u) * k)), Vector2(0, roundf(lerpf(20.0, 0.0, u) * k))]
	var v := ramp01(time, 26.3, 30.8)
	return [Vector2(roundf(-7.0 * v * k), 0), Vector2(roundf(-22.0 * v * k), 0)]


func _slide(n: Sprite2D, side: int, time: float, t0: float) -> void:
	if n.texture == null:
		return
	var floor_y := float(layout.get("door_floor", 262))
	var cx: float = float((layout.get("door_cx", [160, 480]) as Array)[side])
	var h := n.texture.get_height()
	var w := n.texture.get_width()
	var u := ramp01(time, t0, t0 + 0.6)
	var d := roundf(u * (h + 10.0))                     # px of travel below the gap line
	var vis := clampi(int(d), 0, h)
	n.visible = vis > 0
	n.region_rect = Rect2(0, h - vis, w, vis)
	n.position = Vector2(roundf(cx - w * 0.5 + (side * 2 - 1) * 4.0), floor_y + maxf(0.0, d - h))


# ------------------------------------------------------------------ draw
## Needle angle (degrees clockwise from 12) at `time`: the same function in both rooms, so the sweep that
## starts at Alexei's knob ends on Konrad's dial (the match cut).
func needle_angle(time: float) -> float:
	return lerpf(ANG_RU, ANG_DE, ramp01(time, TUNE[0], TUNE[1]))


func _draw_needle(n: Node2D) -> void:
	var ang := needle_angle(t)
	var a := deg_to_rad(ang)
	var dir := Vector2(sin(a), -cos(a))
	var tip := DIAL + dir * float(DIAL_R - 3)
	var tail := DIAL - dir * 5.0
	# a 2 px needle: dark body, a red tip, a pale edge on the lit side so it reads on the cream glass
	var side := Vector2(-dir.y, dir.x)
	FX.line(n, tail + side, tip + side, Color("#d8c08a"))
	FX.line(n, tail, tip, Color("#1a0c08"))
	FX.line(n, tail - side * 0.6, tip - side * 0.6, Color("#1a0c08"))
	FX.line(n, DIAL + dir * float(DIAL_R - 9), tip, Color("#a8382e"))
	n.draw_rect(Rect2(DIAL.round() - Vector2(2, 2), Vector2(4, 4)), Color("#4a3415"))
	n.draw_rect(Rect2(DIAL.round() - Vector2(1, 1), Vector2(2, 2)), Color("#c49a48"))


func _draw_steam() -> void:
	if _steam_tex == null or not square.visible or t >= 4.0:
		return
	var n := 6
	var fw := float(_steam_tex.get_width() / n)
	var fh := float(_steam_tex.get_height())
	var k := motion_k()
	# the 23.40 pulling out below the parapet: its engine sends up a column of steam in beats, the platform roofs
	# breathe a lower haze; every cloud is born hidden behind the parapet (y > 330) and billows up into view,
	# drifting right with the wind and thinning out
	var src := [[150.0, 0.0, 1.0, 0.36], [300.0, 0.21, 0.75, 0.5], [470.0, 0.11, 0.6, 0.62], [600.0, 0.29, 0.45, 0.8]]
	for si in src.size():
		var sv: Array = src[si]
		var period: float = float(sv[3])
		for j in 18:
			var born := -4.2 + float(j) * period + float(sv[1])
			var age := t - born
			var life := 3.6 - float(si) * 0.3
			if age < 0.0 or age > life:
				continue
			var u := age / life
			var x := float(sv[0]) + age * 15.0 * k + sin(float(j) * 1.7 + float(si)) * 10.0
			var y := 352.0 - (age * 54.0 - age * age * 5.0) * k
			var sc := (0.55 + u * 0.95) * float(sv[2]) + 0.25
			var a := clampf(age / 0.35, 0.0, 1.0) * clampf((life - age) / 1.6, 0.0, 1.0) * (0.3 + 0.36 * float(sv[2])) * (1.0 - 0.35 * u)
			var fi := clampi(int(u * n), 0, n - 1)
			var sz := Vector2(fw, fh) * sc
			_steam.draw_texture_rect_region(_steam_tex, Rect2((Vector2(x, y) - sz * Vector2(0.5, 0.62)).round(), sz.round()),
				Rect2(fi * fw, 0, fw, fh), Color(1, 1, 1, a))


func _draw_taxi() -> void:
	if _taxi_tex == null or not square.visible or t < float(TAXI[0]) or t > float(TAXI[1]):
		return
	var p: Array = layout.get("taxi_path", [[200.0, 155.0], [440.0, 155.0]])
	var u := (t - float(TAXI[0])) / (float(TAXI[1]) - float(TAXI[0]))
	var pos := Vector2(lerpf(float(p[0][0]), float(p[1][0]), u), lerpf(float(p[0][1]), float(p[1][1]), u)).round()
	# the headlights' cone on the snow ahead and a brighter pool close to the car
	_taxi.draw_colored_polygon(PackedVector2Array([pos + Vector2(11, -3), pos + Vector2(46, -6), pos + Vector2(50, 1),
		pos + Vector2(11, 0)]), Color(1.0, 0.86, 0.58, 0.16))
	_taxi.draw_colored_polygon(PackedVector2Array([pos + Vector2(11, -2), pos + Vector2(28, -3), pos + Vector2(30, 0),
		pos + Vector2(11, 0)]), Color(1.0, 0.9, 0.66, 0.22))
	draw_frame(_taxi, _taxi_tex, 2, int(floor(t * 9.0)) % 2, pos)


## r1: a late couple crosses the near square arm in arm (the figures stream's townspeople)
func _draw_couple() -> void:
	var c: Dictionary = layout.get("couple", {})
	if c.is_empty() or _couple_m == null or not square.visible or t >= 4.0:
		return
	var path: Array = c["path"]
	var u := clampf(t / 4.0, 0.0, 1.0) * motion_k() + (0.0 if not reduced_motion() else 0.25)
	var pos := Vector2(lerpf(float(path[0][0]), float(path[1][0]), u), lerpf(float(path[0][1]), float(path[1][1]), u))
	var fr := int(floor(t * float(c.get("fps", 7.0)) * motion_k())) % 6
	# their shadows on the snow from the lamp behind them
	for off in [Vector2(0, 0), Vector2(-float(c.get("gap", 15.0)), 1)]:
		var fp: Vector2 = (pos + off).round()
		_couple.draw_colored_polygon(PackedVector2Array([fp + Vector2(-4, 0), fp + Vector2(4, 0), fp + Vector2(10, 4),
			fp + Vector2(-2, 4)]), Color(0.05, 0.07, 0.1, 0.4))
	if _couple_w:
		draw_frame(_couple, _couple_w, 6, (fr + 3) % 6, (pos + Vector2(-float(c.get("gap", 15.0)), 1)).round())
	draw_frame(_couple, _couple_m, 6, fr, pos.round())


## r2: a car passing below throws its headlights up through the window: a skewed, window-shaped patch of light
## (the four panes, the mullion's shadow) slides across the ceiling's edge and the walls left and right of the
## window -- clipped to the room's surfaces, never on the glass or the facade outside (additive, soft)
const ROOM_WIN := Rect2(168, 52, 324, 162)


func _draw_sweep() -> void:
	if not room_a.visible or t < float(SWEEP[0]) or t > float(SWEEP[1]):
		return
	var u := (t - float(SWEEP[0])) / (float(SWEEP[1]) - float(SWEEP[0]))
	var x := lerpf(760.0, -220.0, u * u * (3.0 - 2.0 * u))
	var a := sin(u * PI) * 0.8
	var win := PackedVector2Array([ROOM_WIN.position, ROOM_WIN.position + Vector2(ROOM_WIN.size.x, 0),
		ROOM_WIN.end, ROOM_WIN.position + Vector2(0, ROOM_WIN.size.y)])
	for i in 3:
		var w := 110.0 - i * 30.0
		var kk := a * (0.45 + i * 0.3)
		var c := Color(0.17 * kk, 0.15 * kk, 0.12 * kk, 1.0)
		# the patch is skewed: high on the ceiling's edge, sliding down the side walls
		for pane in 2:
			var px := x + (pane - 0.5) * (w * 0.55 + 6.0)
			var quad := PackedVector2Array([Vector2(px - w * 0.26, 40), Vector2(px + w * 0.26, 40),
				Vector2(px + w * 0.36 - 60, 250), Vector2(px - w * 0.36 - 60, 250)])
			for part in Geometry2D.clip_polygons(quad, win):
				if Geometry2D.is_polygon_clockwise(part):
					continue
				_sweep.draw_colored_polygon(part, c)


## r6: metres walked by each man at `time`: [the walk out of the door, a minute later (after the dissolve)]
func walked_m(time: float, who: String) -> Array:
	var D := float(layout.get("walk_" + who, 100.0))
	var early := maxf(0.0, time - WALK_START) * WALK_SPEED * motion_k()
	var u := clampf((time - float(LATER[0])) / (DUR - float(LATER[0])), 0.0, 1.0)
	var late := D * lerpf(LATE_FROM, LATE_TO, u * (2.0 - u))
	return [early, late]


func _path_at(path: Array, d: float) -> Array:
	# path points every 0.5 m: [x, y, figure height, metres]
	if path.is_empty():
		return [Vector2.ZERO, 10.0]
	var f := clampf(d / 0.5, 0.0, float(path.size() - 1))
	var i0 := int(floor(f))
	var i1 := mini(i0 + 1, path.size() - 1)
	var a: Array = path[i0]
	var b: Array = path[i1]
	var w := f - float(i0)
	return [Vector2(lerpf(float(a[0]), float(b[0]), w), lerpf(float(a[1]), float(b[1]), w)), lerpf(float(a[2]), float(b[2]), w)]


func _draw_walkers() -> void:
	if not square.visible or t < WALK_START - 0.6:
		return
	var later := ramp01(t, float(LATER[0]), float(LATER[1]))
	for who in ["konrad", "alexei"]:
		var path: Array = layout.get("path_" + who, [])
		if path.is_empty():
			continue
		var wm := walked_m(t, who)
		var early: float = wm[0]
		var late: float = wm[1]
		# the trodden furrow: a darker, bluer line through the snow, its far side catching the lamp light
		var trail: Array = layout.get("trail_" + who, [])
		for i in range(1, trail.size()):
			var q0: Array = trail[i - 1]
			var q1: Array = trail[i]
			var d1 := float(q1[3])
			var al := 0.0
			if d1 <= early:
				al = 1.0 - later
			if d1 <= late:
				al = maxf(al, later)
			if al <= 0.0:
				continue
			var p0 := Vector2(float(q0[0]), float(q0[1]))
			var p1 := Vector2(float(q1[0]), float(q1[1]))
			var dir := (p1 - p0).normalized() if p1.distance_to(p0) > 0.01 else Vector2(0, -1)
			var nrm := Vector2(-dir.y, dir.x)
			var h0 := float(q0[2])
			var h1 := float(q1[2])
			var hw0 := maxf(1.0, h0)
			var hw1 := maxf(1.0, h1)
			_walkers.draw_colored_polygon(PackedVector2Array([p0 - nrm * hw0, p0 + nrm * hw0, p1 + nrm * hw1, p1 - nrm * hw1]),
				Color(0.07, 0.1, 0.15, 0.62 * al))
			_walkers.draw_colored_polygon(PackedVector2Array([p0 + nrm * hw0, p0 + nrm * (hw0 + 0.7), p1 + nrm * (hw1 + 0.7), p1 + nrm * hw1]),
				Color(0.62, 0.66, 0.72, 0.16 * al))
		# the footprints in it: dark dents, left and right
		var prints: Array = layout.get("prints_" + who, [])
		for pr in prints:
			var d := float(pr[2])
			var al2 := 0.0
			if d <= early:
				al2 = 1.0 - later
			if d <= late:
				al2 = maxf(al2, later)
			if al2 <= 0.0:
				continue
			var sz := float(pr[3])
			var pw := maxf(1.0, roundf(sz))
			var ph := maxf(1.0, roundf(sz * 0.5))
			_walkers.draw_rect(Rect2(Vector2(floorf(float(pr[0]) - pw * 0.5), floorf(float(pr[1]))), Vector2(pw, ph)),
				Color(0.03, 0.05, 0.08, 0.9 * al2))
		if t < WALK_START:
			continue                       # still inside the doorway
		# the man as he steps out (fading with the dissolve) and a minute later, far off at the wing
		var near_tex: Texture2D = _walk_k if who == "konrad" else _walk_a
		var far_tex: Texture2D = _walk_far_k if who == "konrad" else _walk_far_a
		if later < 1.0:
			var pe: Array = _path_at(path, early)
			var pos: Vector2 = pe[0]
			var step := int(floor(early / 0.36)) % 6
			# the open door behind him throws his shadow ahead over the snow (longer as he leaves the light)
			var src := Vector2(float(path[0][0]), float(path[0][1]))
			var dir2 := (pos - src).normalized() if pos.distance_to(src) > 0.5 else Vector2(0.3, -1).normalized()
			var ln := clampf(10.0 + pos.distance_to(src) * 0.9, 10.0, 34.0)
			var side := Vector2(-dir2.y, dir2.x) * 2.0
			var sa := 0.5 * (1.0 - later)
			_walkers.draw_colored_polygon(PackedVector2Array([pos - side, pos + side, pos + dir2 * ln + side * 0.5,
				pos + dir2 * ln - side * 0.5]), Color(0.04, 0.05, 0.08, sa))
			draw_frame(_walkers, near_tex, 6, step, pos + Vector2(0, 1), false, Color(1, 1, 1, 1.0 - later))
		if later > 0.0 and far_tex:
			var pl: Array = _path_at(path, late)
			var stepf := int(floor(late / 0.5)) % 4
			if late >= float(layout.get("walk_" + who, 100.0)) * LATE_TO - 0.01:
				stepf = 0
			draw_frame(_walkers, far_tex, 4, stepf, (pl[0] as Vector2) + Vector2(0, 1), false, Color(1, 1, 1, later))


## r3: the pencil hand follows the growing line: the sheet's frame for the last position passed (two pen strokes
## alternate while he writes, the pencil lifted after pencil_stop), the sprite shifted by the rest of the way to
## the line's end, so the point stays on it.
func _apply_pencil_hand(time: float, rm: bool) -> void:
	if _hand == null or _hand.texture == null:
		return
	var pl: Array = layout.get("pad_line", [428, 230, 466])
	var x0 := float(pl[0])
	var x1 := float(pl[2])
	var npos := HAND_POS if _hand.hframes >= 3 * HAND_POS else 0
	if npos == 0:
		_hand.frame = 0 if time < pencil_stop else _hand.hframes - 1
		return
	var u := clampf((minf(time, pencil_stop) - 10.5) / 5.0, 0.0, 1.0)
	var fp := u * float(npos - 1)
	var i := clampi(int(floor(fp)), 0, npos - 1)
	var step := (x1 - x0) / float(npos - 1)
	if time < pencil_stop:
		var stroke := int(floor(maxf(0.0, time - 10.5) * 7.0 * (0.6 if rm else 1.0))) % 2 if time >= 10.5 else 0
		_hand.frame = i * 2 + stroke
	else:
		_hand.frame = 2 * npos + i
	_hand.position = _lv("hand_konrad") + Vector2(roundf((fp - float(i)) * step), 0)


func _draw_scribble() -> void:
	if not room_k.visible:
		return
	var pl: Array = layout.get("pad_line", [428, 230, 466])
	var x0 := float(pl[0])
	var y0 := float(pl[1])
	var x1 := float(pl[2])
	var u := clampf((minf(t, pencil_stop) - 10.5) / 5.0, 0.0, 1.0)
	var xe := lerpf(x0, x1, u)
	var x := x0
	var i := 0
	while x < xe:
		var dy := 1.0 if hnoise(x * 0.9, 5) > 0.2 else 0.0
		_scribble.draw_rect(Rect2(Vector2(floorf(x), y0 - dy), Vector2(1, 1)), Color("#3a3a42"))
		x += 1.0 if (i % 5) != 4 else 2.0
		i += 1


func _draw_gap() -> void:
	if not doors.visible:
		return
	var floor_y := float(layout.get("door_floor", 262))
	var cxs: Array = layout.get("door_cx", [160, 480])
	# the courier stops at each door, then walks on (two shoes in the light of the gap, their shadow on the floor)
	for side in [0, 1]:
		var t0 := 17.45 if side == 0 else 17.95
		var t1 := t0 + 0.95
		if t < t0 or t > t1:
			continue
		var u := (t - t0) / (t1 - t0)
		var cx: float = float(cxs[side]) + lerpf(70.0, -70.0, u) * (0.35 if u > 0.25 and u < 0.75 else 1.0)
		if u > 0.25 and u < 0.75:
			cx = float(cxs[side]) + 6.0
		for s in [-1, 1]:
			var x: float = roundf(cx + float(s) * 9.0)
			# sole and heel of each shoe in the bright gap, and the light they keep off the floor inside
			_gap.draw_rect(Rect2(Vector2(x - 7, floor_y - 4), Vector2(9, 4)), Color("#0c0a09"))
			_gap.draw_rect(Rect2(Vector2(x + 3, floor_y - 4), Vector2(4, 4)), Color("#0c0a09"))
			_gap.draw_colored_polygon(PackedVector2Array([Vector2(x - 8, floor_y), Vector2(x + 8, floor_y),
				Vector2(x + 15, floor_y + 30), Vector2(x - 15, floor_y + 30)]), Color(0.02, 0.015, 0.01, 0.42))


func _draw_motes() -> void:
	if not note.visible:
		return
	var k := motion_k()
	for i in 14:
		var ph := float(i) * 1.7
		var x := fposmod(150.0 + i * 37.0 + (t - NOTE_CLOSE) * (3.0 + i % 3) * k, 640.0)
		var y := 70.0 + fposmod(i * 23.0 - (t - NOTE_CLOSE) * 2.0 * k + sin(ph + t) * 3.0, 220.0)
		var a := 0.35 + 0.3 * sin(ph + t * 1.3)
		_motes.draw_rect(Rect2(Vector2(floorf(x), floorf(y)), Vector2(1, 1)), Color(0.93, 0.85, 0.65, a))


func _draw_clock() -> void:
	if not cafe.visible:
		return
	var c := _lv("clock") + Vector2(0.5, 0.5)
	var r := float(layout.get("clock_r", 21))
	var mins := 10.0
	var hrs := 0.0 + mins / 60.0
	var am := deg_to_rad(mins * 6.0)
	var ah := deg_to_rad(hrs * 30.0)
	FX.line(_clock, c, c + Vector2(sin(am), -cos(am)) * (r - 3.0), Color("#1a1a1c"), 1)
	FX.line(_clock, c, c + Vector2(sin(ah), -cos(ah)) * (r - 9.0), Color("#1a1a1c"), 2)
	var secs := SECONDS0 + maxf(0.0, t - 22.3)
	var asec := deg_to_rad(secs * 6.0)
	FX.line(_clock, c - Vector2(sin(asec), -cos(asec)) * 3.0, c + Vector2(sin(asec), -cos(asec)) * (r - 4.0),
		Color("#a8382e"), 1)
	_clock.draw_rect(Rect2(c.floor() - Vector2(1, 1), Vector2(2, 2)), Color("#8a2a20"))


## r5: a car passes outside; its headlights, through the three panes, cross the floor and the far wall (additive)
func _draw_cafe_light() -> void:
	if not cafe.visible or t < float(CAFE_CAR[0]) or t > float(CAFE_CAR[1]):
		return
	var u := (t - float(CAFE_CAR[0])) / (float(CAFE_CAR[1]) - float(CAFE_CAR[0]))
	var a := sin(u * PI) * 0.7 * (0.6 if reduced_motion() else 1.0)
	var sx := lerpf(-260.0, 900.0, u)
	for pane in [[43.0, 223.0], [229.0, 411.0], [417.0, 597.0]]:
		var x0 := maxf(float(pane[0]), sx - 150.0)
		var x1 := minf(float(pane[1]), sx + 150.0)
		if x1 <= x0:
			continue
		var cx := (x0 + x1) * 0.5
		var kk := a * clampf(1.0 - absf(cx - sx) / 150.0, 0.0, 1.0)
		var c := Color(0.20 * kk, 0.18 * kk, 0.13 * kk, 1.0)
		# on the floor: the pane's light skewed toward the camera (the inset never crosses over on a narrow sliver,
		# which would make a bow-tie polygon that cannot be triangulated)
		var ins := minf(4.0, (x1 - x0) * 0.25)
		_cafe_light.draw_colored_polygon(PackedVector2Array([Vector2(x0 + ins, 264), Vector2(x1 - ins, 264),
			Vector2(x1 + (x1 - 320) * 0.5, 352), Vector2(x0 + (x0 - 320) * 0.5, 352)]), c)
		# on the ceiling above the window, faint
		_cafe_light.draw_colored_polygon(PackedVector2Array([Vector2(x0, 52), Vector2(x1, 52), Vector2(x1 + 20, 40),
			Vector2(x0 + 20, 40)]), c * 0.6)
