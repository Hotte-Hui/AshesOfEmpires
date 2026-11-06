extends "res://scenes/cinematics/ch4p2_common/c4p2_cinematic.gd"
## LS_C4P2_Depot (13 s) — Karsk, Monday 17 February 1964, 6.10, before dawn (C4P2_DESIGN §2.9).
##   p1  0-5    establishing: the depot under two floodlights; Kolonne 4 shovels coal down the heap into two open
##              wagons (eleven returnees in a line, one resting on his shovel behind the wagon), the young guard
##              warms his hands at a barrel fire; the roundhouse with one lit stall; at VALVE_LIFT the safety valve
##              of the engine in that stall lifts (steam bursts from its roof hood)
##   p2  5-9    side_on: Alexei carries his toolbox under the roundhouse arch (the in-game stride), his breath in
##              the cold; inside the stall the engine head-on under a work lamp, a fitter oiling the cylinder; the
##              banner ВОССТАНОВИМ ВМЕСТЕ patched with sacking; music mus_c4p2_karsk enters
##   p3  9-13   close: Irina's lit dispatch window; the telephone rings once (PHONE_RING), she looks up from the
##              ledger; the typed order on the sill; control to Alexei
## Lines: the place card.  Sound beds (tools/audiogen/c4p2_cine_audio.py): c4p2cine_depot (shovels at the three
## nearest workers' contact frames, the valve, the fire), c4p2cine_arch (Alexei's boots at his walk's contact
## frames), c4p2cine_window (samovar, the ring).

const DUR := 13.0
const SHOTS := [["p1", 0.0, 5.0], ["p2", 5.0, 9.0], ["p3", 9.0, 13.0]]
const LINES := ["cin.c4p2.depot.place"]
const VALVE_LIFT := 2.6            # the engine in the lit stall blows off (c4p2cine_depot)
const WALK_T0 := 5.0               # Alexei starts walking with p2
const PHONE_RING := 10.2           # one ring of the dispatch telephone (c4p2cine_window)
const IRINA_LOOK := 10.75          # she looks up from the ledger
const GUARD_FPS := 5.0
const REST_FPS := 2.5
const VENTS := [Vector2(462, 140), Vector2(518, 140), Vector2(574, 140)]

var D: Dictionary = {}
var p1: Node2D
var p2: Node2D
var p3: Node2D
var _gang: Array = []
var _gang_ph: Array = []
var _rest: Sprite2D
var _guard: Sprite2D
var _flame: Sprite2D
var _fireglow: Sprite2D
var _beams: Sprite2D
var _alexei: Sprite2D
var _fitter: Sprite2D
var _beam2: Sprite2D
var _lamp2: Sprite2D
var _irina: Sprite2D
var _lamp3: Sprite2D
var _steam1: Node2D
var _steam2: Node2D
var _steam3: Node2D
var _embers: Node2D
var _snow1: Node2D
var _snow2: Node2D
var _snow3: Node2D
var _t_vent: Texture2D
var _t_jet: Texture2D
var _t_breath: Texture2D
var _t_cock: Texture2D
var _t_samovar: Texture2D
var _t_embers: Texture2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return LINES.duplicate()


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "bed": "c4p2cine_depot", "db": -4.0},
		say_at(LINES[0], 0.5),
		{"t": 5.0, "bed": "c4p2cine_arch", "db": -5.0},
		{"t": 9.0, "bed": "c4p2cine_window", "db": -5.0},
	]
	c += optional_amb(0.0, "amb_karsk_depot", 2.5)
	c += optional_music(5.0, "mus_c4p2_karsk", 2.5)
	return c


## Film times at which the three nearest shovels bite (layout depot.bites == the sound tool's cuts).
func bite_times() -> Array:
	var out: Array = []
	var near: Array = D.get("near_gang", [])
	var gang: Array = D.get("p1_gang", [])
	var fps := float(D.get("cycle_fps", 8.0))
	var contact := int(D.get("contact_frame", 1))
	for i in near:
		var ph := int(gang[int(i)][2])
		var times: Array = []
		var k := 0
		while true:
			var tt := float(posmod(contact - ph, 8) + 8 * k) / fps
			if tt >= 5.0:
				break
			times.append(snappedf(tt, 0.001))
			k += 1
		out.append(times)
	return out


## Alexei's feet x on p2 (the in-game walk speed) and his walk frame.
func alexei_x(time: float) -> float:
	var w: Array = D.get("p2_walk", [96, 276])
	return float(walk_x(time, WALK_T0, float(w[0]), float(w[1]))[0])


## Film times his boots land (walk frames 0 and 4: every 18 px = 0.4 s).
func step_times() -> Array:
	var out: Array = []
	var w: Array = D.get("p2_walk", [96, 276])
	var span := absf(float(w[1]) - float(w[0]))
	var d := 0.0
	while d < span - 0.001:
		out.append(snappedf(WALK_T0 + d / WALK_SPEED, 0.001))
		d += STRIDE * 4.0
	return out


func _build() -> void:
	D = _layout_section("depot")
	# ---------------------------------------------------------------- p1
	p1 = group("Depot")
	sprite("depot/p1_bg.png", Vector2.ZERO, p1)
	_beams = glow("depot/p1_beams.png", p1)
	_steam1 = fx(p1, "Steam1", _draw_steam1)
	var gang: Array = D.get("p1_gang", [])
	for i in gang.size():
		var g: Array = gang[i]
		var s := cells("depot/gang_%02d.png" % i, p1, 48, Vector2(float(g[0]), float(g[1])))
		_gang.append(s)
		_gang_ph.append(int(g[2]))
	var rp: Array = D.get("p1_rest", [368, 212])
	_rest = cells("depot/gang_rest.png", p1, 48, Vector2(float(rp[0]), float(rp[1])))
	sprite("depot/p1_front.png", Vector2.ZERO, p1)
	var gp: Array = D.get("p1_guard", [576, 252, 6])
	_guard = cells("depot/guard.png", p1, 48, Vector2(float(gp[0]), float(gp[1])))
	var fp: Array = D.get("p1_fire", [569, 262])
	_flame = cells("depot/flame.png", p1, 18, Vector2(float(fp[0]) - 9.0, float(fp[1]) - 28.0))
	_t_embers = tex("depot/embers.png")
	_embers = fx(p1, "Embers", _draw_embers)
	_fireglow = glow("depot/p1_fireglow.png", p1)
	glow("depot/p1_halos.png", p1)
	_snow1 = snow(p1, Rect2(-20, 30, 680, 300), [
		{"count": 70, "v": Vector2(-6, 16), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#9aa6b8"), "sway": 2.0},
		{"count": 26, "v": Vector2(-10, 30), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#dfe6ee"), "sway": 3.0},
	], 4101)
	# ---------------------------------------------------------------- p2
	p2 = group("Arch")
	sprite("depot/p2_bg.png", Vector2.ZERO, p2)
	_beam2 = glow("depot/p2_beam.png", p2)
	var ft: Array = D.get("p2_fitter", [386, 238])
	_fitter = cells("depot/p2_fitter.png", p2, 48, Vector2(float(ft[0]), float(ft[1])))
	_steam2 = fx(p2, "Steam2", _draw_steam2)
	_alexei = cells("depot/p2_alexei.png", p2, 48)
	_lamp2 = glow("depot/p2_lampglow.png", p2)
	glow("depot/p2_doorglow.png", p2)
	_snow2 = snow(p2, Rect2(-20, 30, 680, 300), [
		{"count": 36, "v": Vector2(-5, 14), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#aab4c4"), "sway": 2.0},
		{"count": 14, "v": Vector2(-9, 26), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#e6ecf2"), "sway": 3.0},
	], 4102)
	# ---------------------------------------------------------------- p3
	p3 = group("Window")
	sprite("depot/p3_bg.png", Vector2.ZERO, p3)
	var ia: Array = D.get("p3_irina_at", [226, 112])
	_irina = cells("depot/p3_irina.png", p3, int(D.get("p3_irina_cell", 112)), Vector2(float(ia[0]), float(ia[1])))
	_steam3 = fx(p3, "Steam3", _draw_steam3)
	sprite("depot/p3_over.png", Vector2.ZERO, p3)
	_lamp3 = glow("depot/p3_lampglow.png", p3)
	_snow3 = snow(p3, Rect2(-20, 30, 680, 300), [
		{"count": 40, "v": Vector2(-4, 12), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#c8d0dc"), "sway": 3.0},
		{"count": 16, "v": Vector2(-7, 22), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#eef2f6"), "sway": 4.0},
	], 4103)
	_t_vent = tex("depot/vent_steam.png")
	_t_jet = tex("depot/valve_jet.png")
	_t_breath = tex("depot/breath.png")
	_t_cock = tex("depot/cock_steam.png")
	_t_samovar = tex("depot/samovar_steam.png")


func _apply(time: float) -> void:
	if p1 == null:
		return
	var sh := shot_at(time)
	p1.visible = sh == "p1"
	p2.visible = sh == "p2"
	p3.visible = sh == "p3"
	var rm := reduced_motion()
	# p1: the gang's shovel cycles (8 frames at 8 fps, each its own phase), the guard, the fire
	var fps := float(D.get("cycle_fps", 8.0))
	for i in _gang.size():
		(_gang[i] as Sprite2D).frame = p2_loop_frame(time, fps * (0.5 if rm else 1.0), 8, int(_gang_ph[i]))
	_rest.frame = p2_loop_frame(time, REST_FPS, 4)
	_guard.frame = p2_loop_frame(time, GUARD_FPS * (0.5 if rm else 1.0), maxi(1, _guard.hframes))
	_flame.frame = flame_frame(time, 8, 0.3)
	_fireglow.modulate = Color(1, 1, 1, clampf(0.82 * fire_wobble(time, 71, 0.16), 0.0, 1.0))
	_beams.modulate = Color(1, 1, 1, clampf(0.9 + 0.06 * hnoise(time * 0.7, 73), 0.0, 1.0))
	# p2: Alexei walks at the in-game speed (feet never slide), the fitter oils, the lamp sways a little
	var ax := alexei_x(time)
	var dist := absf(ax - float((D.get("p2_walk", [96, 276]) as Array)[0]))
	_alexei.frame = walk_i(dist) % maxi(1, _alexei.hframes)
	_alexei.position = Vector2(roundf(ax - 24.0), float(D.get("p2_floor", 300)) - 54.0)
	_fitter.frame = p2_loop_frame(time, 2.5, 3)
	var sway := roundf(sin(time * 1.3) * (0.5 if rm else 1.0))
	_beam2.position = Vector2(sway, 0)
	_lamp2.position = Vector2(sway, 0)
	_lamp2.modulate = Color(1, 1, 1, clampf(0.9 + 0.05 * hnoise(time * 1.1, 79), 0.0, 1.0))
	# p3: Irina looks up after the ring
	_irina.frame = 1 if time >= IRINA_LOOK else 0
	_lamp3.modulate = Color(1, 1, 1, clampf(0.92 + 0.04 * hnoise(time * 0.9, 83), 0.0, 1.0))
	for s in [_snow1, _snow2, _snow3]:
		s.set_time(time)
	for n in [_steam1, _steam2, _steam3, _embers]:
		n.queue_redraw()
	set_meta("t_draw", time)


func _now() -> float:
	return float(get_meta("t_draw", t))


func _draw_steam1() -> void:
	var time := _now()
	if time >= 5.0:
		return
	for i in VENTS.size():
		puffs(_steam1, _t_vent, 8, time, -3.0 + i * 0.7, 6.0, 1.1, 3.0, VENTS[i] + Vector2(0, 2), Vector2(-5, -9),
			301 + i, Color(1, 1, 1, 0.85))
	# the safety valve lifts: a dense burst for 1.4 s from the stall's hood
	var vent: Array = D.get("p1_vent", [518, 140])
	puffs(_steam1, _t_jet, 8, time, VALVE_LIFT, VALVE_LIFT + 1.4, 0.12, 1.3, Vector2(float(vent[0]), float(vent[1])),
		Vector2(-3, -40), 311, Color(1, 1, 1, 1), Vector2(2, 1))


func _draw_embers() -> void:
	var time := _now()
	if time >= 5.0 or _t_embers == null:
		return
	var fp: Array = D.get("p1_fire", [569, 262])
	var k := 0.5 if reduced_motion() else 1.0
	for i in 9:
		var life := 1.6 + 0.4 * absf(hnoise(i * 3.1, 91))
		var age := fposmod(time + i * 0.37, life)
		var x := float(fp[0]) + hnoise(i * 1.3, 93) * 6.0 + sin(age * 3.0 + i) * 2.0 * k
		var y := float(fp[1]) - 18.0 - age * 26.0 * k
		draw_frame(_embers, _t_embers, 4, i % 4, Vector2(roundf(x), roundf(y)), false,
			Color(1, 1, 1, clampf(1.2 - age / life, 0.0, 1.0)))


func _draw_steam2() -> void:
	var time := _now()
	if time < 5.0 or time >= 9.0:
		return
	var cyl: Array = D.get("p2_cyl", [[280, 244], [360, 244]])
	for i in cyl.size():
		var c: Array = cyl[i]
		puffs(_steam2, _t_cock, 8, time, 3.0 + i * 0.5, 10.0, 0.9, 2.4, Vector2(float(c[0]), float(c[1]) + 4),
			Vector2(-6 if i == 0 else 6, -6), 321 + i, Color(1, 1, 1, 0.45))
	# Alexei's breath: a small cloud at his mouth every 1.3 s, it drifts back as he walks
	var floor_y := float(D.get("p2_floor", 300))
	var t0 := WALK_T0 + 0.35
	var k := int(floor((time - t0) / 1.3))
	for j in [k - 1, k]:
		var born: float = t0 + float(j) * 1.3
		if born < t0 or time < born:
			continue
		var age: float = time - born
		if age < 0.9:
			var bx := alexei_x(born) + 7.0
			draw_frame(_steam2, _t_breath, 6, mini(5, int(age / 0.9 * 6)), Vector2(roundf(bx - age * 6.0),
				roundf(floor_y - 44.0 - age * 4.0)), false, Color(1, 1, 1, 0.9))


func _draw_steam3() -> void:
	var time := _now()
	if time < 9.0:
		return
	var sv: Array = D.get("p3_samovar", [426, 196])
	puffs(_steam3, _t_samovar, 8, time, 6.0, 14.0, 0.55, 2.2, Vector2(float(sv[0]), float(sv[1]) - 30.0),
		Vector2(1, -8), 331, Color(1, 1, 1, 0.55), Vector2(1, 1))
