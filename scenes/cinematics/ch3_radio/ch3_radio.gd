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
## Art: tools/pixelgen/env_c3p2_cine_radio.py -> assets/cinematics/c3p2/radio/ (+ layout.json "radio").

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
const WALK_START := 26.9
const DOORS_OPEN := 26.6
const DOORS_SHUT := 28.6

const LINE_TIME := "cin.c3p2.radio.time"
const LINE_RU := "cin.c3p2.radio.ru"
const LINE_DE := "cin.c3p2.radio.de"
const LINE_NOTE := "cin.c3p2.radio.note"
## reading time per line (seconds)
const LINE_DUR := {"cin.c3p2.radio.time": 3.0, "cin.c3p2.radio.ru": 6.0, "cin.c3p2.radio.de": 5.5,
	"cin.c3p2.radio.note": 2.9, "cin.c3p2.radio.alexei.base": 3.0, "cin.c3p2.radio.alexei.cafe": 3.6,
	"cin.c3p2.radio.alexei.alone": 3.0, "cin.c3p2.radio.konrad.base": 3.0, "cin.c3p2.radio.konrad.share": 4.0,
	"cin.c3p2.radio.konrad.search": 3.4, "cin.c3p2.radio.konrad.report": 3.0}

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
	var L: Array = [_l(LINE_TIME, 0.5), _l(LINE_RU, 3.7)]
	if a_radio:
		L.append(_l(line_alexei, 9.8))
	L.append(_l(LINE_DE, 12.9 if a_radio else 11.0))
	if k_radio:
		L.append(_l(line_konrad, 17.6))
	L.append(_l(LINE_NOTE, 19.7))
	if not a_radio:
		L.append(_l(line_alexei, 23.0))
	if not k_radio:
		L.append(_l(line_konrad, 23.0))
	_line_cues = schedule(L)
	for c in _line_cues:
		if c["say"] == LINE_DE:
			pencil_stop = float(c["t"]) + float(c["dur"]) * 0.62
	pencil_stop = clampf(pencil_stop, 13.0, 16.6)


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
	sprite("radio/square_bg.png", Vector2.ZERO, square)
	_door_k = sprite("radio/door_konrad.png", _lv("door_konrad"), square)
	_door_a = sprite("radio/door_alexei.png", _lv("door_alexei"), square)
	_win_k = sprite("radio/win_konrad.png", _lv("win_konrad"), square)
	_win_a = sprite("radio/win_alexei.png", _lv("win_alexei"), square)
	_sq_glow = sprite("radio/square_glow.png", Vector2.ZERO, square, 1, true)
	_walk_k = tex("radio/walker_konrad.png")
	_walk_a = tex("radio/walker_alexei.png")
	_walkers = Node2D.new()
	_walkers.name = "Walkers"
	_walkers.draw.connect(_draw_walkers)
	square.add_child(_walkers)
	_snow_sq = snow(square, Rect2(0, 0, 640, 360), [
		{"count": 110, "v": Vector2(4, 13), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 50, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0},
		{"count": 16, "v": Vector2(9, 40), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#dee2e7"), "sway": 4.0}], 8101)
	_steam_tex = tex("radio/steam.png")
	_steam = Node2D.new()
	_steam.name = "Steam"
	_steam.draw.connect(_draw_steam)
	square.add_child(_steam)
	# r2: Alexei's room
	room_a = group("RoomAlexei")
	sprite("radio/room_alexei.png", Vector2.ZERO, room_a)
	_snow_a = snow(room_a, Rect2(168, 52, 324, 162), [
		{"count": 40, "v": Vector2(-3, 12), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 16, "v": Vector2(-5, 22), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 2.5}],
		8102, Rect2(172, 56, 316, 146))
	_radio_a = sprite("radio/radio.png", _lv("radio"), room_a)
	_dglow_a = sprite("radio/dial_glow.png", Vector2.ZERO, room_a, 1, true)
	_eye_a = sprite("radio/magic_eye.png", _lv("magic_eye") - Vector2(3, 3), room_a, 3, true)
	_needle_a = _needle_node(room_a)
	_tea = sprite("radio/steam_tea.png", _lv("steam_tea"), room_a, 6)
	_arm = sprite("radio/arm_alexei.png", _lv("arm_alexei"), room_a, 4)
	_fig_a = sprite("radio/fig_alexei.png", _lv("fig_alexei"), room_a, 2)
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
	_hand = sprite("radio/hand_konrad.png", _lv("hand_konrad"), room_k, 5)
	_fig_k = sprite("radio/fig_konrad.png", _lv("fig_konrad"), room_k, 2)
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
	note = group("Note")
	_note_close = sprite("radio/note_close.png", Vector2.ZERO, note)
	_motes = Node2D.new()
	_motes.name = "Motes"
	_motes.draw.connect(_draw_motes)
	note.add_child(_motes)
	# r5: the café
	cafe = group("Cafe")
	sprite("radio/cafe.png", Vector2.ZERO, cafe)
	var cw: Array = layout.get("cafe_win", [43, 61, 597, 196])
	_snow_c = snow(cafe, Rect2(40, 40, 560, 160), [
		{"count": 60, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.0},
		{"count": 24, "v": Vector2(7, 26), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0}],
		8104, Rect2(float(cw[0]), float(cw[1]), float(cw[2]) - float(cw[0]), float(cw[3]) - float(cw[1])))
	_clock = Node2D.new()
	_clock.name = "ClockHands"
	_clock.draw.connect(_draw_clock)
	cafe.add_child(_clock)
	_cafe_glow = sprite("radio/cafe_glow.png", Vector2.ZERO, cafe, 1, true)


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
	_door_k.visible = r6 and time >= DOORS_OPEN and time < DOORS_SHUT
	_door_a.visible = r6 and time >= DOORS_OPEN + 0.08 and time < DOORS_SHUT + 0.2
	_sq_glow.modulate = Color(1, 1, 1, 1.0 if not r6 else 0.75)
	_snow_sq.set_time(time * (0.6 if rm else 1.0))
	_steam.queue_redraw()
	_walkers.queue_redraw()
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
	var af := 0
	if time >= ARM[2]:
		af = 3
	elif time >= ARM[1]:
		af = 2
	elif time >= ARM[0]:
		af = 1
	_arm.frame = af
	_fig_a.frame = int(floor((time + 0.4) / 2.1)) % 2 if not rm else 0
	_fig_k.frame = int(floor((time + 1.1) / 2.3)) % 2 if not rm else 0
	if time < pencil_stop:
		_hand.frame = int(floor((time - 10.5) * 6.0 * (0.6 if rm else 1.0))) % 4 if time >= 10.5 else 0
	else:
		_hand.frame = 4
	_scribble.queue_redraw()
	# r4: notes slide in under both doors (left first), the shadows of the feet in the light of the gaps
	_slide(_note_l, 0, time, 17.75)
	_slide(_note_r, 1, time, 18.3)
	_gap.queue_redraw()
	if note.visible:
		var drift := clampf((time - NOTE_CLOSE) / 3.0, 0.0, 1.0) * 3.0 * k
		_note_close.position = Vector2(roundf(-drift), 0)
	_motes.queue_redraw()
	# r5
	_snow_c.set_time(time * (0.6 if rm else 1.0))
	_clock.queue_redraw()
	_cafe_glow.modulate = Color(1, 1, 1, 0.94 + 0.04 * hnoise(time * 2.4, 31) * (0.4 if rm else 1.0))


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
	if _steam_tex == null or not square.visible or t >= 4.6:
		return
	var n := 6
	var fw := _steam_tex.get_width() / n
	var fh := _steam_tex.get_height()
	var k := motion_k()
	var puffs := [[-40.0, 262.0, 0.0], [90.0, 280.0, 0.9], [230.0, 268.0, 1.7], [-120.0, 290.0, 2.4], [380.0, 286.0, 3.1]]
	for pf in puffs:
		var age: float = t + float(pf[2])
		var x: float = float(pf[0]) + age * 26.0 * k
		var y: float = float(pf[1]) - age * 7.0 * k
		var fi := clampi(int(age / 1.1), 0, n - 1)
		_steam.draw_texture_rect_region(_steam_tex, Rect2(Vector2(roundf(x), roundf(y)), Vector2(fw, fh)),
			Rect2(fi * fw, 0, fw, fh))


func _draw_walkers() -> void:
	if not square.visible or t < WALK_START - 0.6:
		return
	var walked := maxf(0.0, t - WALK_START) * motion_k()
	for who in ["konrad", "alexei"]:
		var path: Array = layout.get("path_" + who, [])
		var prints: Array = layout.get("prints_" + who, [])
		if path.is_empty():
			continue
		# footprints behind him
		for pr in prints:
			if float(pr[2]) <= walked:
				_walkers.draw_rect(Rect2(Vector2(floorf(float(pr[0])), floorf(float(pr[1]))), Vector2(2, 1)), Color("#1e2836"))
		var tex2: Texture2D = _walk_k if who == "konrad" else _walk_a
		var fi := walked / 0.1
		var i0 := clampi(int(floor(fi)), 0, path.size() - 1)
		var i1 := clampi(i0 + 1, 0, path.size() - 1)
		var f := fi - floorf(fi)
		var p0: Array = path[i0]
		var p1: Array = path[i1]
		var pos := Vector2(lerpf(float(p0[0]), float(p1[0]), f), lerpf(float(p0[1]), float(p1[1]), f))
		var step := int(floor(walked * 4.2)) % 4 if walked > 0.0 else 0
		if t < WALK_START:
			continue                       # still inside the doorway
		draw_frame(_walkers, tex2, 4, step, pos + Vector2(0, 1))


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
			var x: float = cx + float(s) * 9.0
			_gap.draw_rect(Rect2(Vector2(roundf(x - 6), floor_y - 4), Vector2(12, 4)), Color("#0c0a09"))
			_gap.draw_rect(Rect2(Vector2(roundf(x - 8), floor_y), Vector2(16, 3)), Color(0.05, 0.035, 0.03, 0.55))


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
	_clock.draw_rect(Rect2(c.floor() - Vector2(1, 1), Vector2(2, 2)), Color("#8a2a20"))
