extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Voices (24 s) — the closing of Chapter 4 part 1 „Stimmen unter Beton“ (C4_DESIGN §2.9).  Nothing is
## resolved: the wagon still leaves on Tuesday.
##   v1  0-5      Berlin morning: Konrad climbs out of the service door of the advertising column S 2 -- with the
##                Lindner file under his coat (name_marta) or empty-handed (protect_marta)
##   v2  5-10     Marta's tram leaves the loop, Ilse at the last window; Konrad from behind in the foreground --
##                one bell (name_marta), or two bells and he raises his hand, Ilse hers on the glass (protect)
##   v3  10-15    Karsk: Alexei and Lev climb out of the cellar stair into the dark yard under the green signal
##                (to 13.0) -> insert: Alexei's notebook, four numbers, one wagon
##   v4  15-20    the siding: wagon C-17/45 alone under its work lamp; the lamp goes out
##   v5  20-24    black; the caption
## Lines: Konrad per ctx.choices.c4d_choose (name_marta / protect_marta; default protect: the line that
## exposes nobody), Alexei, then the caption.  Every context without c4d (tests, memories) plays the default.

const DUR := 24.0
const SHOTS := [["v1", 0.0, 5.0], ["v2", 5.0, 10.0], ["v3", 10.0, 15.0], ["v4", 15.0, 20.0], ["v5", 20.0, 24.0]]
const LINE_ALEXEI := "cin.c4.voices.alexei"
const LINE_TUESDAY := "cin.c4.voices.tuesday"
const V1_RISE := [0.5, 1.2]            # Konrad climbs the last rungs inside the column
const V1_WALK := 1.35                  # and walks off to the left
const BELLS := {"name_marta": [5.7], "protect_marta": [5.7, 6.45]}
const WAVE := [6.9, 7.1, 9.1, 9.3]     # protect: the arm goes up, is up, comes down, is down
const TRAM_GO := [5.3, 10.0]           # the tram pulls away (accelerating) between these times
const V3_UP := [10.25]                 # Alexei starts up the stair (he is at its head ~1.2 s later)
const V3_LEV := 0.75                   # Lev follows this much later, slower
const V3_CUT := 13.0                   # yard -> notebook insert
const LAMP_FLICKS := [18.2, 18.45, 18.9]   # the work lamp: off, on, off for good (c4cine_lamp_out; tests compare)

var line_c4d := "cin.c4.voices.konrad_protect"
var named := false
var L4: Dictionary = {}
var LP: Dictionary = {}
var v1: Node2D
var v2: Node2D
var v3: Node2D
var v3n: Node2D
var v4: Node2D
var v5: Node2D
var _k1: Sprite2D
var _file: Sprite2D
var _ground1: Sprite2D
var _steam1: Node2D
var _steam_tex: Texture2D
var _tram: Sprite2D
var _k2: Sprite2D
var _a3: Sprite2D
var _l3: Sprite2D
var _lantern: Sprite2D
var _warm3: Sprite2D
var _snow3: Node2D
var _note_fx: Node2D
var _lit4: Sprite2D
var _dark4: Sprite2D
var _glow4: Sprite2D
var _black: ColorRect


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func _on_configured() -> void:
	named = choice("c4d_choose") == "name_marta"
	line_c4d = "cin.c4.voices.konrad_name" if named else "cin.c4.voices.konrad_protect"


func chosen_lines() -> Array:
	return [line_c4d, LINE_ALEXEI, LINE_TUESDAY]


func bell_times() -> Array:
	return BELLS["name_marta" if named else "protect_marta"]


func _make_cues() -> Array:
	var c: Array = [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c4cine_column", "db": -6.0},
		say_at(line_c4d, 1.0),
		{"t": 5.0, "bed": "c4cine_tram_leave", "db": -6.0},
		{"t": 10.0, "bed": "c4cine_yard_night", "db": -6.0},
		say_at(LINE_ALEXEI, 10.6),
		{"t": 15.0, "bed": "c4cine_lamp_out", "db": -5.0},
		{"t": 20.0, "bed": "c4cine_tuesday", "db": -6.0},
		say_at(LINE_TUESDAY, 20.7, 2.4, 3.2),
	]
	for bt in bell_times():
		c.append({"t": float(bt), "sfx": "c4cine_bell", "db": -4.0, "pv": 0.0})
	c += optional_music(10.0, "mus_c4_voices", 3.0)
	return c


func _build() -> void:
	L4 = _layout_section("voices")
	LP = _layout_section("places")
	_steam_tex = tex("places/steam_light.png")
	var o1 := float(L4.get("v1_off", -330))
	v1 = group("Column")
	var plate1 := sprite("places/loop_morning.png", Vector2(o1, 0), v1)
	sprite("places/loop_glow_morning.png", Vector2(o1, 0), v1, 1, true)
	sprite("voices/v1_door.png", Vector2(o1, 0), v1)
	_k1 = fig("voices/v1_konrad.png", v1)
	_file = sprite("voices/v1_file.png", Vector2.ZERO, v1)
	# the ground strip in front of the door covers his feet while he climbs out
	var door: Array = LP.get("loop_door", [632, 236, 658, 300])
	_ground1 = sprite("places/loop_morning.png", Vector2(o1 + float(door[0]) - 4.0, float(door[3]) + 1.0), v1)
	_ground1.region_enabled = true
	_ground1.region_rect = Rect2(float(door[0]) - 4.0, float(door[3]) + 1.0, float(door[2]) - float(door[0]) + 8.0, 20.0)
	_steam1 = fx(v1, "Steam", _draw_steam1)
	if plate1:
		plate1.name = "Plate"
	var o2 := float(L4.get("v2_off", -150))
	v2 = group("TramLeaves")
	sprite("places/loop_morning.png", Vector2(o2, 0), v2)
	sprite("places/loop_glow_morning.png", Vector2(o2, 0), v2, 1, true)
	_tram = sprite("places/tram_right.png", Vector2.ZERO, v2, 2)
	_k2 = sprite("voices/v2_konrad.png", lv(L4, "v2_konrad_at", Vector2(14, 98)), v2, 3)
	v3 = group("Yard")
	sprite("places/yard.png", Vector2.ZERO, v3)
	sprite("places/yard_green.png", Vector2.ZERO, v3, 1, true)
	_warm3 = sprite("places/yard_warm.png", Vector2.ZERO, v3, 1, true)
	_l3 = fig("voices/v3_lev.png", v3)
	_lantern = sprite("voices/lantern.png", Vector2.ZERO, v3, 1, true)
	_a3 = fig("voices/v3_alexei.png", v3)
	sprite("places/yard_parapet.png", Vector2.ZERO, v3)
	_snow3 = snow(v3, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#465564"), "sway": 2.0},
		{"count": 30, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#7e8b96"), "sway": 3.0}],
		9601)
	v3n = group("Notebook")
	sprite("voices/v3_note.png", Vector2.ZERO, v3n)
	_note_fx = fx(v3n, "SnowOnPage", _draw_note)
	v4 = group("Siding")
	_lit4 = sprite("places/siding_lit.png", Vector2.ZERO, v4)
	_dark4 = sprite("places/siding_dark.png", Vector2.ZERO, v4)
	_glow4 = sprite("places/siding_glow.png", Vector2.ZERO, v4, 1, true)
	v5 = group("Black")
	_black = ColorRect.new()
	_black.color = Color.BLACK
	_black.size = Vector2(640, 360)
	_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v5.add_child(_black)


func tram_x(time: float) -> float:
	var start := float(LP.get("loop_w", 1000)) * 0.0 + 350.0 + float(L4.get("v2_off", -150))
	var u := clampf((time - float(TRAM_GO[0])) / (float(TRAM_GO[1]) - float(TRAM_GO[0])), 0.0, 1.0)
	return roundf(start + 520.0 * u * u * motion_k())


func wave_frame(time: float) -> int:
	if named:
		return 0
	if time < float(WAVE[0]) or time >= float(WAVE[3]):
		return 0
	if time < float(WAVE[1]) or time >= float(WAVE[2]):
		return 1
	return 2


func lamp_on(time: float) -> bool:
	if reduced_motion():
		return time < float(LAMP_FLICKS[1])            # one soft change, no flicker
	if time < float(LAMP_FLICKS[0]):
		return true
	if time < float(LAMP_FLICKS[1]):
		return false
	return time < float(LAMP_FLICKS[2])


func _apply(time: float) -> void:
	if v1 == null:
		return
	var sh := shot_at(time)
	v1.visible = sh == "v1"
	v2.visible = sh == "v2"
	v3.visible = sh == "v3" and time < V3_CUT
	v3n.visible = sh == "v3" and time >= V3_CUT
	v4.visible = sh == "v4"
	v5.visible = sh == "v5"
	var rm := reduced_motion()
	var feet := float(LP.get("feet", 300))
	# ---- v1: out of the column, off to the left
	var o1 := float(L4.get("v1_off", -330))
	var door: Array = LP.get("loop_door", [632, 236, 658, 300])
	var dx := o1 + (float(door[0]) + float(door[2])) * 0.5
	var ik: Dictionary = L4.get("v1_konrad", {})
	var rise := 16.0 * (1.0 - ease_out(time, float(V1_RISE[0]), float(V1_RISE[1])))
	_k1.visible = time >= float(V1_RISE[0])
	var wx: Array = walk_x(time, V1_WALK, dx, dx - 150.0)
	var kx := float(wx[0])
	if time < V1_WALK:
		fig_frame(_k1, ik, "idle_side_l", 0, Vector2(dx, feet + rise))
	else:
		fig_frame(_k1, ik, "walk_side_l" if bool(wx[1]) else "idle_side_l", walk_i(kx - dx), Vector2(kx, feet))
	_file.visible = named and _k1.visible
	_file.position = (_k1.position + Vector2(11, 25)).round()
	_steam1.queue_redraw()
	# ---- v2: the tram pulls away; one bell, or two and the raised hand
	_tram.position = Vector2(tram_x(time), feet - 96.0 + 8.0)
	_tram.frame = 1 if (not named and time >= float(WAVE[0]) + 0.1) else 0
	_k2.frame = wave_frame(time)
	# ---- v3: up the cellar stair, into the yard under the green signal
	var st: Array = LP.get("yard_stair", [414, 500])
	var sx := (float(st[0]) + float(st[1])) * 0.5 + 12.0
	var top := float(st[0])
	_place_climber(_a3, L4.get("v3_alexei", {}), time, float(V3_UP[0]), sx, top, feet, 45.0)
	_place_climber(_l3, L4.get("v3_lev", {}), time, float(V3_UP[0]) + V3_LEV, sx + 6.0, top, feet, 34.0)
	_lantern.visible = _l3.visible
	_lantern.position = (_l3.position + Vector2(-20, -2)).round()
	_lantern.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 71, 0.12), 0.0, 1.0))
	_warm3.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 73, 0.08), 0.0, 1.0))
	_snow3.set_time(time * (0.6 if rm else 1.0))
	_note_fx.queue_redraw()
	# ---- v4: the lamp goes out
	var on := lamp_on(time)
	_lit4.visible = on
	_dark4.visible = not on
	_glow4.visible = on


## v3: a figure climbs the stair (behind the parapet) from x0 up to its head at x_top, then walks on to the left.
func _place_climber(s: Sprite2D, idx: Dictionary, time: float, t0: float, x0: float, x_top: float, feet: float,
		speed: float) -> void:
	s.visible = time >= t0
	var walked := maxf(0.0, time - t0) * speed
	var x := x0 - walked
	var below := 18.0 * clampf((x - x_top) / maxf(1.0, x0 - x_top), 0.0, 1.0)
	fig_frame(s, idx, "walk_side_l", walk_i(walked), Vector2(roundf(x), roundf(feet + below)))


func _draw_steam1() -> void:
	if not v1.visible or _steam_tex == null:
		return
	var o1 := float(L4.get("v1_off", -330))
	var col: Array = LP.get("loop_column", [622, 670])
	var k := motion_k()
	for i in 4:
		var age := fposmod(t * 0.32 + i * 0.25, 1.0)
		var base := Vector2(o1 + (float(col[0]) + float(col[1])) * 0.5 + (i - 1.5) * 9.0, 296.0)
		var p := base + Vector2(sin(age * 3.0 + i) * 4.0 * k, -age * 60.0 * k)
		draw_frame(_steam1, _steam_tex, 8, int(age * 7.0), p, false, Color(1, 1, 1, 0.6 * (1.0 - age)))


## v3 insert: a few flakes land on the page and melt (each a pure function of t).
func _draw_note() -> void:
	if not v3n.visible:
		return
	for i in 9:
		var t0 := V3_CUT + 0.15 + i * 0.2
		if t < t0:
			continue
		var age := t - t0
		var p := Vector2(150.0 + fposmod(i * 83.0, 360.0), 70.0 + fposmod(i * 61.0, 230.0))
		var a := clampf(1.0 - age / 1.4, 0.0, 1.0)
		if a <= 0.0:
			continue
		_note_fx.draw_rect(Rect2(p, Vector2(2, 2)), Color(0.86, 0.95, 0.88, a))
		if age > 0.5:
			_note_fx.draw_rect(Rect2(p + Vector2(-1, 1), Vector2(4, 1)), Color(0.5, 0.7, 0.55, a * 0.6))
