extends "res://scenes/cinematics/ch4p2_common/c4p2_cinematic.gd"
## LS_C4P2_Steam (12.5 s) — Karsk -> Berlin, Monday (C4P2_DESIGN §2.9).  The steam jet is ONE shape and ONE sound
## across the cut.
##   m1  0-4      side_on: the coal stage; coal rattles down the chute into the special-run engine's tender
##                (COAL_RUN), three men raise the last tarpaulin section on its poles (it cracks taut at
##                TARP_SNAPS), Alexei watches from the foreground; at the end the engine's valve starts to sizzle
##   m2  4-5.5    macro_locked: the twin pop valves blow off -- the white jet at JET_BASE (12-frame loop)
##                                                        -- hard cut, the jet keeps its frame and its place --
##   m3  5.5-9.5  macro_to_medium: the same jet over the brass valve of the express engine under the Ostbahnhof's
##                iron and glass roof (m3a) -> hard cut on the jet (CUT_M3) while the camera settles back
##                (SETTLE) -> the hall: the express at platform K, the board running to D 303 KARSK 21.10 (FLAP_T)
##   m4  9.5-12.5 establishing: platform K, the crowd, Marta at the buffet, the man at the kiosk; Konrad comes in
##                from the left (the in-game stride) and stops; control to Konrad
## Lines: Alexei's thought over m1-m2, the place card on m3.  Beds (tools/audiogen/c4p2_cine_audio.py):
## c4p2cine_coal (coal, tarpaulin snaps), c4p2cine_jet (one hiss from 4.0 s: open air, then the hall's echo from
## the cut on), c4p2cine_hall (the flaps at FLAP_T, an announcement, pigeons, a luggage cart).

const DUR := 12.5
const SHOTS := [["m1", 0.0, 4.0], ["m2", 4.0, 5.5], ["m3", 5.5, 9.5], ["m4", 9.5, 12.5]]
const LINES := ["cin.c4p2.steam.alexei", "cin.c4p2.steam.berlin"]
const JET_T0 := 4.0                 # the jet's loop clock starts with m2 and runs on through the cut
const JET_FPS := 12.0
const CUT := 5.5                    # Karsk valve -> Berlin valve (hard cut)
const CUT_M3 := 6.6                 # m3a macro -> m3b hall (hard cut on the jet)
const SETTLE := [6.6, 7.4, 8.0]     # the hall settles back after the cut (span, px)
const SIZZLE := 3.55                # m1: the first wisps at the valve before the cut to the macro
const KONRAD_T0 := 9.5

var S: Dictionary = {}
var m1: Node2D
var m2: Node2D
var m3a: Node2D
var hall: Node2D
var _tarp: Sprite2D
var _workers: Array = []
var _alexei: Sprite2D
var _jet2: Sprite2D
var _jet3: Sprite2D
var _board: Sprite2D
var _people: Array = []
var _people_fps: Array = []
var _konrad: Sprite2D
var _halo: Sprite2D
var _fx1: Node2D
var _fxh: Node2D
var _snow1: Node2D
var _t_dust: Texture2D
var _t_far: Texture2D
var _t_hsteam: Texture2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return LINES.duplicate()


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "bed": "c4p2cine_coal", "db": -4.0},
		{"t": JET_T0, "bed": "c4p2cine_jet", "db": -3.0},
		{"t": CUT, "bed": "c4p2cine_hall", "db": -5.0},
	]
	c += schedule([{"key": LINES[0], "at": 0.2, "dur": line_dur(LINES[0], 1.4, 6.0)},
		{"key": LINES[1], "at": CUT + 0.1, "dur": line_dur(LINES[1])}])
	c += optional_amb(0.0, "amb_karsk_depot", 1.5)
	c += optional_amb(CUT, "amb_berlin_station", 0.4)
	c += optional_music(9.5, "mus_c4p2_berlin", 2.0)
	return c


## frame of the shared jet loop at film time `time` (the same clock on both sides of the cut)
func jet_frame(time: float) -> int:
	return loop_frame(time, JET_FPS * motion_k(), 12, 0, JET_T0)


## frame of the rising tarpaulin (0 slack .. 5 taut; it jumps a step at each snap)
func tarp_frame(time: float) -> int:
	var tt: Array = S.get("tarp_t", [0.4, 3.5])
	var u := clampf((time - float(tt[0])) / (float(tt[1]) - float(tt[0])), 0.0, 1.0)
	var f := int(floor(u * 4.0))
	for sn in S.get("tarp_snaps", []):
		if time >= float(sn):
			f += 1
	return clampi(f, 0, 5)


## frame of the flipping board row (0 the old train .. 9 D 303 KARSK 21.10)
func board_frame(time: float) -> int:
	var ft: Array = S.get("flap_t", [6.85, 7.95])
	if time < float(ft[0]):
		return 0
	return clampi(1 + int(floor((time - float(ft[0])) / (float(ft[1]) - float(ft[0])) * 8.0)), 1, 9)


func konrad_x(time: float) -> float:
	var kx: Array = S.get("m4_konrad", [580, 690])
	return float(walk_x(time, KONRAD_T0, float(kx[0]), float(kx[1]))[0])


## Film times Konrad's shoes land on m4 (walk frames 0 and 4: every 18 px) until he stops.
func konrad_steps() -> Array:
	var kx: Array = S.get("m4_konrad", [580, 690])
	var span := absf(float(kx[1]) - float(kx[0]))
	var out: Array = []
	var d := 0.0
	while d < span - 0.001 and KONRAD_T0 + d / WALK_SPEED < DUR:
		out.append(snappedf(KONRAD_T0 + d / WALK_SPEED, 0.001))
		d += STRIDE * 4.0
	return out


## m3b: the camera settles back after the cut from the macro (px the hall still sits low)
func settle_dy(time: float) -> float:
	if time < CUT_M3 or time >= 9.5:
		return 0.0
	return roundf(float(SETTLE[2]) * (1.0 - ease_out(time, float(SETTLE[0]), float(SETTLE[1]))) * motion_k())


## hall group offset: m3b shows the hall from x 0, m4 from m4_ox
func hall_x(time: float) -> float:
	return -float(S.get("m4_ox", 560)) if time >= 9.5 else 0.0


func _build() -> void:
	S = _layout_section("steam")
	var jb: Array = S.get("jet_base", [320, 168])
	var js: Array = S.get("jet_size", [120, 240])
	var jpos := Vector2(float(jb[0]) - float(js[0]) / 2.0, float(jb[1]) - float(js[1]) + 1.0)
	# ---------------------------------------------------------------- m1
	m1 = group("CoalStage")
	sprite("steam/m1_bg.png", Vector2.ZERO, m1)
	var ta: Array = S.get("tarp_at", [570, 180])
	_tarp = cells("steam/tarp.png", m1, int(S.get("tarp_w", 64)), Vector2(float(ta[0]), float(ta[1])))
	var wk: Array = S.get("m1_workers", [])
	for i in wk.size():
		_workers.append(cells("steam/m1_worker_%d.png" % i, m1, 48, Vector2(float(wk[i][0]), float(wk[i][1]))))
	_fx1 = fx(m1, "CoalFx", _draw_m1)
	var al: Array = S.get("m1_alexei", [0, 146])
	_alexei = cells("steam/m1_alexei.png", m1, int(S.get("m1_alexei_cell", 240)), Vector2(float(al[0]), float(al[1])))
	_snow1 = snow(m1, Rect2(-20, 30, 680, 300), [
		{"count": 30, "v": Vector2(-8, 18), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#e2e8f0"), "sway": 2.0},
	], 4201)
	# ---------------------------------------------------------------- m2 (Karsk macro)
	m2 = group("ValveKarsk")
	sprite("steam/m2_bg.png", Vector2.ZERO, m2)
	_jet2 = cells("steam/jet.png", m2, int(js[0]), jpos)
	# ---------------------------------------------------------------- the hall (m3b + m4), under m3a
	hall = group("Hall")
	sprite("steam/hall.png", Vector2.ZERO, hall)
	_fxh = fx(hall, "HallFx", _draw_hall)
	var bra: Array = S.get("board_row_at", [448, 148])
	var bw := int((S.get("board", [448, 104, 624, 176]) as Array)[2]) - int((S.get("board", [448, 104, 624, 176]) as Array)[0])
	_board = cells("steam/board_row.png", hall, bw, Vector2(float(bra[0]), float(bra[1])))
	var pp: Array = S.get("m4_people", [])
	for i in pp.size():
		_people.append(cells("steam/m4_p%02d.png" % i, hall, 32, Vector2(float(pp[i][0]), float(pp[i][1]))))
		_people_fps.append(float(pp[i][2]))
	_konrad = cells("steam/m4_konrad.png", hall, 32)
	_halo = glow("steam/hall_glow.png", hall)
	sprite("steam/hall_lamps.png", Vector2.ZERO, hall)
	# ---------------------------------------------------------------- m3a (Berlin macro), cut away at CUT_M3
	m3a = group("ValveBerlin")
	sprite("steam/m3a_bg.png", Vector2.ZERO, m3a)
	_jet3 = cells("steam/jet.png", m3a, int(js[0]), jpos)
	_jet3.modulate = Color(1.0, 0.86, 0.68)
	_t_dust = tex("steam/dust.png")
	_t_far = tex("steam/jet_far.png")
	_t_hsteam = tex("steam/hall_steam.png")


func _apply(time: float) -> void:
	if m1 == null:
		return
	var sh := shot_at(time)
	m1.visible = sh == "m1"
	m2.visible = sh == "m2"
	hall.visible = sh == "m3" or sh == "m4"
	m3a.visible = sh == "m3" and time < CUT_M3
	# m1
	_tarp.frame = tarp_frame(time)
	for i in _workers.size():
		(_workers[i] as Sprite2D).frame = loop_frame(time, 2.0, 3, i)
	_alexei.frame = loop_frame(time, 2.0, maxi(1, _alexei.hframes))
	_snow1.set_time(time)
	# m2 / m3a: one jet clock across the cut
	_jet2.frame = jet_frame(time)
	_jet3.frame = jet_frame(time)
	# hall
	hall.position = Vector2(hall_x(time), settle_dy(time))
	_board.frame = board_frame(time)
	for i in _people.size():
		var s: Sprite2D = _people[i]
		s.frame = loop_frame(time, float(_people_fps[i]), maxi(1, s.hframes), i * 3)
	var kx := konrad_x(time)
	var kk: Array = S.get("m4_konrad", [580, 690])
	var walking: bool = time >= KONRAD_T0 and kx < float(kk[1]) - 0.01
	_konrad.frame = (walk_i(kx - float(kk[0])) % 8) if walking else 8 + loop_frame(time, 4.0, 8)
	_konrad.position = Vector2(roundf(kx - 16.0), float(S.get("m4_feet", 300)) - 54.0)
	_halo.modulate = Color(1, 1, 1, clampf(0.92 + 0.05 * hnoise(time * 0.8, 11), 0.0, 1.0))
	_fx1.queue_redraw()
	_fxh.queue_redraw()


func _draw_m1() -> void:
	var time := t
	if time >= 4.0:
		return
	var ch: Array = S.get("m1_chute", [356, 120, 372, 182])
	var tend: Array = S.get("m1_tender", [296, 412, 172])
	var run: Array = S.get("coal_run", [0.25, 3.7])
	var k := motion_k()
	# coal lumps sliding off the chute's lip and dropping into the tender (pure function of t)
	if time >= float(run[0]) and time < float(run[1]) + 0.4:
		var x0 := float(ch[2])
		var y0 := float(ch[3])
		var floor_y := float(tend[2]) + 2.0
		for i in 26:
			var life := 0.42 + 0.12 * absf(hnoise(i * 1.9, 41))
			var born := float(run[0]) + fposmod(i * 0.137, life)
			var age := fposmod(time - born, life)
			if time - float(run[0]) < age or time > float(run[1]) + age:
				continue
			var x := x0 + hnoise(i * 2.7, 43) * 5.0 + age * 14.0 * k
			var y := y0 + 60.0 * age * age * 4.0
			if y > floor_y:
				continue
			_fx1.draw_rect(Rect2(roundf(x), roundf(y), 2 if i % 3 == 0 else 1, 1), Color("#1e1e24") if i % 2 else Color("#34343c"))
		puffs(_fx1, _t_dust, 6, time, float(run[0]) + 0.2, float(run[1]), 0.45, 1.6,
			Vector2(x0 + 4.0, floor_y + 6.0), Vector2(6, -8), 451, Color(1, 1, 1, 0.6))
	# the valve starts to sizzle before the cut to the macro
	var vt: Array = S.get("m1_valve", [218, 186])
	puffs(_fx1, _t_far, 8, time, SIZZLE, 4.0, 0.12, 0.8, Vector2(float(vt[0]), float(vt[1])), Vector2(4, -30), 461,
		Color(1, 1, 1, 0.9), Vector2(1, 1))


func _draw_hall() -> void:
	var time := t
	if time < CUT:
		return
	var vt: Array = S.get("m3_valve", [270, 172])
	puffs(_fxh, _t_far, 8, time, CUT - 1.0, DUR, 0.11, 0.9, Vector2(float(vt[0]), float(vt[1])), Vector2(5, -46), 471,
		Color(1.0, 0.9, 0.75, 0.95), Vector2(1, 1))
	for i in 4:
		puffs(_fxh, _t_hsteam, 8, time, CUT - 4.0 + i * 0.9, DUR, 3.6, 4.5,
			Vector2(150.0 + i * 260.0, 200.0), Vector2(9, -5), 481 + i, Color(1, 1, 1, 0.35), Vector2(30, 8))
