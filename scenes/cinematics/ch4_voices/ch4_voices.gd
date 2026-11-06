extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## LS_C4_Voices (24 s) — the closing of Chapter 4 part 1 „Stimmen unter Beton“ (C4_DESIGN §2.9).  Nothing is
## resolved: the wagon still leaves on Tuesday.
##   v1  0-5      Berlin morning, the loop as the level paints it (the poster of S 2 torn back): Konrad climbs out of
##                the column's open steel door -- with the Lindner file under his coat (name_marta) or empty-handed
##                (protect_marta) -- and walks off; the crows on the wire lift off, warm air steams from the grate
##   v2  5-10     Marta's tram 3518 leaves the loop, Ilse at the last window; Konrad from behind in the foreground,
##                the camera following the car a little -- one bell (name_marta), or two bells and he raises his
##                hand, Ilse her red mitten on the glass (protect)
##   v3  10-15    Karsk: Alexei and Lev climb out of the cellar stair into the yard under the green signal (to 13.0)
##                -> insert: Alexei's squared notebook in his hand (figures stream's v3_thumb), four numbers, one
##                wagon; held in the cold (it drifts a little in his hand, his breath crosses it), the yard's lights
##                out of focus behind, snow falling past the lens and landing on the page
## Round 10: the climbers are cut exactly by what hides them -- Konrad by the column door's opening while he is
## inside, Alexei and Lev by the foot of the stair's parapet (fig_frame_clip) -- no feet on the pavement / snow.
##   v4  15-20    the siding as the level paints it: wagon C-17/45 alone under its work lamp, dust in the light; the
##                lamp goes out, the filament dies, only the dawn at the portal remains
##   v5  20-24    black; the caption
## Lines: Konrad per ctx.choices.c4d_choose (name_marta / protect_marta; default protect: the line that
## exposes nobody), Alexei, then the caption.  Every context without c4d (tests, memories) plays the default.

const DUR := 24.0
const SHOTS := [["v1", 0.0, 5.0], ["v2", 5.0, 10.0], ["v3", 10.0, 15.0], ["v4", 15.0, 20.0], ["v5", 20.0, 24.0]]
const LINE_ALEXEI := "cin.c4.voices.alexei"
const LINE_TUESDAY := "cin.c4.voices.tuesday"
const V1_RISE := [0.5, 1.2]            # Konrad climbs the last rungs inside the column
const V1_WALK := 1.35                  # steps down out of the door and walks off to the left
const V1_STEP := 0.35                  # the step down from the sill to the pavement
const BELLS := {"name_marta": [5.7], "protect_marta": [5.7, 6.45]}
const WAVE := [6.9, 7.1, 9.1, 9.3]     # protect: the arm goes up, is up, comes down, is down
const TRAM_GO := [5.3, 10.0]           # the tram pulls away (accelerating) between these times
const V2_PAN := 56.0                   # the camera follows the tram this far (to the street's end; rm halves it)
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
var _l1: Dictionary = {}
var _l2: Dictionary = {}
var _fx1: Dictionary = {}
var _fx2: Dictionary = {}
var _door1: Sprite2D
var _k1: Sprite2D
var _file: Sprite2D
var _ground1: Sprite2D
var _crows1: Node2D
var _crow_tex: Texture2D
var _tram: Sprite2D
var _sparks2: Node2D
var _k2: Sprite2D
var _yard: Dictionary = {}
var _a3: Sprite2D
var _l3: Sprite2D
var _lantern: Sprite2D
var _warm3: Sprite2D
var _fx3: Node2D
var _snow1: Node2D
var _snow2: Node2D
var _snow3: Node2D
var _note_fx: Node2D
var _book: Node2D
var _note_bg_fx: Node2D
var _note_front: Node2D
var _breath_tex: Texture2D
var _bokeh_tex: Texture2D
var _flake_tex: Texture2D
var _lit4: Sprite2D
var _dark4: Sprite2D
var _glow4: Sprite2D
var _fx4: Node2D
var _smoke_tex: Texture2D
var _motes_tex: Texture2D
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


## The loop's layers (morning) into `parent`: back layers, crane lamps, the street, the column's steam.
func _loop_back(parent: Node2D, layers: Dictionary, fxs: Dictionary) -> void:
	var fxm: Dictionary = LP.get("loop_fx", {})
	for nm in ["sky", "dome"]:
		layers[nm] = sprite("places/loop_morning_%s.png" % nm, Vector2.ZERO, parent)
	for nm in ["crane_light_0", "crane_light_1", "crane_light_2"]:
		var m: Dictionary = fxm.get(nm, {})
		fxs[nm] = fx_sprite("places/fx_%s.png" % nm, int(m.get("frames", 4)), Vector2.ZERO, parent)
	for nm in ["far", "mid", "street"]:
		layers[nm] = sprite("places/loop_morning_%s.png" % nm, Vector2.ZERO, parent)
	var ms: Dictionary = fxm.get("steam_s2", {})
	fxs["steam_s2"] = fx_sprite("places/fx_steam_s2.png", int(ms.get("frames", 16)), Vector2.ZERO, parent)


func _loop_place(time: float, cam: float, layers: Dictionary, fxs: Dictionary) -> void:
	var homes: Dictionary = LP.get("loop_layers", {})
	for nm in layers:
		var hm: Array = homes.get(nm, [0, 0, 1.0])
		(layers[nm] as Sprite2D).position = par_pos(Vector2(float(hm[0]), float(hm[1])), cam, float(hm[2]))
	var fxm: Dictionary = LP.get("loop_fx", {})
	for nm in fxs:
		var m: Dictionary = fxm.get(nm, {})
		var pos: Array = m.get("pos", [0, 0])
		var s: Sprite2D = fxs[nm]
		s.position = par_pos(Vector2(float(pos[0]), float(pos[1])), cam, float(m.get("parallax", 1.0)))
		s.frame = loop_frame(time, int(m.get("frames", 1)), float(m.get("fps", 6.0)), h01(nm.length(), 91))


func _build() -> void:
	L4 = _layout_section("voices")
	LP = _layout_section("places")
	_smoke_tex = tex("places/smoke.png")
	_motes_tex = tex("places/motes.png")
	_crow_tex = tex("places/fx_crows.png")
	var feet := float(LP.get("feet", 300))
	# ---- v1: the loop in the morning, the column's open door
	v1 = group("Column")
	_loop_back(v1, _l1, _fx1)
	_door1 = sprite("voices/v1_door.png", Vector2.ZERO, v1)
	_k1 = fig("voices/v1_konrad.png", v1)
	_file = sprite("voices/v1_file.png", Vector2.ZERO, v1)
	# the plinth in front of the door covers his legs while he climbs the last rungs
	var door: Array = LP.get("loop_door", [638, 226, 654, 282])
	_ground1 = sprite("places/loop_morning_street.png", Vector2.ZERO, v1)
	_ground1.region_enabled = true
	_ground1.region_rect = Rect2(float(door[0]) - 6.0, float(door[3]), float(door[2]) - float(door[0]) + 12.0,
		feet - float(door[3]) + 2.0)
	_crows1 = fx(v1, "Crows", _draw_crows1)
	_l1["fg"] = sprite("places/loop_morning_fg.png", Vector2.ZERO, v1)
	_l1["glow"] = sprite("places/loop_morning_glow.png", Vector2.ZERO, v1, 1, true)
	_snow1 = snow(v1, Rect2(0, 0, 640, 360), [
		{"count": 70, "v": Vector2(6, 12), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#bfc9d5"), "sway": 2.0},
		{"count": 20, "v": Vector2(9, 20), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#e2e8ee"), "sway": 3.0}],
		9611)
	# ---- v2: the tram leaves; Konrad from behind in the foreground
	v2 = group("TramLeaves")
	_loop_back(v2, _l2, _fx2)
	_tram = sprite("places/tram_right.png", Vector2.ZERO, v2, 2)
	_sparks2 = fx(v2, "Sparks", _draw_sparks2)
	_l2["fg"] = sprite("places/loop_morning_fg.png", Vector2.ZERO, v2)
	_l2["glow"] = sprite("places/loop_morning_glow.png", Vector2.ZERO, v2, 1, true)
	_snow2 = snow(v2, Rect2(0, 0, 640, 360), [
		{"count": 70, "v": Vector2(6, 12), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#bfc9d5"), "sway": 2.0},
		{"count": 20, "v": Vector2(9, 20), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#e2e8ee"), "sway": 3.0}],
		9612)
	_k2 = sprite("voices/v2_konrad.png", lv(L4, "v2_konrad_at", Vector2(14, 98)), v2, 3)
	# ---- v3: the yard at night (camera at rest), the climbers behind the parapet
	v3 = group("Yard")
	for nm in ["sky", "far", "mid", "main"]:
		_yard[nm] = sprite("places/yard_l_%s.png" % nm, Vector2.ZERO, v3)
	sprite("places/yard_l_green.png", Vector2.ZERO, v3, 1, true)
	_warm3 = sprite("places/yard_l_warm.png", Vector2.ZERO, v3, 1, true)
	_l3 = fig("voices/v3_lev.png", v3)
	_lantern = sprite("voices/lantern.png", Vector2.ZERO, v3, 1, true)
	_a3 = fig("voices/v3_alexei.png", v3)
	sprite("places/yard_l_parapet.png", Vector2.ZERO, v3)
	_fx3 = fx(v3, "Lights", _draw_v3)
	_snow3 = snow(v3, Rect2(0, 0, 640, 360), [
		{"count": 90, "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#465564"), "sway": 2.0},
		{"count": 30, "v": Vector2(7, 24), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#7e8b96"), "sway": 3.0}],
		9601)
	v3n = group("Notebook")
	_breath_tex = tex("places/breath.png")
	_bokeh_tex = tex("card/bokeh.png")
	_flake_tex = tex("number/flakes.png")
	sprite("voices/v3_note_bg.png", Vector2.ZERO, v3n)
	_note_bg_fx = fx(v3n, "YardLights", _draw_note_bg)
	_note_bg_fx.material = additive()
	_book = group("Book", v3n)
	sprite("voices/v3_book.png", Vector2.ZERO, _book)
	_note_fx = fx(_book, "SnowOnPage", _draw_note)
	sprite("voices/v3_thumb.png", lv(L4, "v3t_at", Vector2(-40, 190)), _book)
	_note_front = fx(v3n, "BreathAndFlakes", _draw_note_front)
	_note_front.material = additive()
	# ---- v4: the siding hall, lit / dark
	v4 = group("Siding")
	_lit4 = sprite("places/siding_lit.png", Vector2.ZERO, v4)
	_dark4 = sprite("places/siding_dark.png", Vector2.ZERO, v4)
	_glow4 = sprite("places/siding_glow.png", Vector2.ZERO, v4, 1, true)
	_fx4 = fx(v4, "Lamp", _draw_v4)
	v5 = group("Black")
	_black = ColorRect.new()
	_black.color = Color.BLACK
	_black.size = Vector2(640, 360)
	_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v5.add_child(_black)


func v1_cam() -> float:
	return -float(L4.get("v1_off", -206))


## v2 camera x (street px): starts at -v2_off and follows the tram a little.
func v2_cam(time: float) -> float:
	var c := -float(L4.get("v2_off", -150)) + V2_PAN * motion_k() * ease01(time, 6.0, 10.0)
	return roundf(minf(c, float(LP.get("loop_w", 846)) - 640.0))


## Screen x of the leaving tram (accelerating away; the camera follows a little).
func tram_x(time: float) -> float:
	var stop := float(LP.get("loop_tram_stop_x", 362)) - 4.0
	var u := clampf((time - float(TRAM_GO[0])) / (float(TRAM_GO[1]) - float(TRAM_GO[0])), 0.0, 1.0)
	return roundf(stop + 520.0 * u * u * motion_k()) - v2_cam(time)


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
	# ---- v1: out of the column, down the step, off to the left
	var cam1 := v1_cam()
	_loop_place(time, cam1, _l1, _fx1)
	_door1.position = Vector2(-cam1, 0)
	var door: Array = LP.get("loop_door", [638, 226, 654, 282])
	var sill := float(door[3])
	_ground1.position = Vector2(float(door[0]) - 6.0 - cam1, sill)
	var dx := (float(door[0]) + float(door[2])) * 0.5 - cam1
	var ik: Dictionary = L4.get("v1_konrad", {})
	var rise := 40.0 * (1.0 - ease_out(time, float(V1_RISE[0]), float(V1_RISE[1])))
	_k1.visible = time >= float(V1_RISE[0])
	_file.visible = named and _k1.visible
	# inside the column he is seen only through the door's opening: nothing below the sill, nothing beside it
	var opening := Rect2(float(door[0]) - cam1, float(door[1]), float(door[2]) - float(door[0]), sill - float(door[1]))
	var kf: Vector2
	if time < V1_WALK:
		kf = Vector2(dx, sill + rise)
		fig_frame_clip(_k1, ik, "idle_side_l", 0, kf, opening)
	else:
		var step := ease01(time, V1_WALK, V1_WALK + V1_STEP)
		var wx: Array = walk_x(time, V1_WALK, dx, dx - 150.0)
		var kx := float(wx[0])
		kf = Vector2(kx, lerpf(sill, feet, step))
		fig_frame_clip(_k1, ik, "walk_side_l" if bool(wx[1]) else "idle_side_l", walk_i(kx - dx), kf, NO_CLIP)
	_ground1.visible = false
	sprite_clip(_file, 1, 0, (kf - FEET_OFF).round() + Vector2(11, 25), opening if time < V1_WALK else NO_CLIP)
	_crows1.queue_redraw()
	_snow1.set_time(time * (0.6 if rm else 1.0))
	# ---- v2: the tram pulls away; one bell, or two and the raised hand
	var cam2 := v2_cam(time)
	_loop_place(time, cam2, _l2, _fx2)
	_tram.position = Vector2(tram_x(time), float(LP.get("tram_top", 174)))
	_tram.frame = 1 if (not named and time >= float(WAVE[0]) + 0.1) else 0
	_k2.frame = wave_frame(time)
	_sparks2.queue_redraw()
	_snow2.set_time(time * (0.6 if rm else 1.0))
	# ---- v3: up the cellar stair, into the yard under the green signal
	var st: Array = LP.get("yard_stair", [414, 500])
	var sx := (float(st[0]) + float(st[1])) * 0.5 + 12.0
	var top := float(st[0])
	_place_climber(_a3, L4.get("v3_alexei", {}), time, float(V3_UP[0]), sx, top, feet, 45.0)
	var lev_tl := _place_climber(_l3, L4.get("v3_lev", {}), time, float(V3_UP[0]) + V3_LEV, sx + 6.0, top, feet, 34.0)
	_lantern.visible = time >= float(V3_UP[0]) + V3_LEV
	_lantern.position = (lev_tl + Vector2(-20, -2)).round()
	_lantern.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 71, 0.12), 0.0, 1.0))
	_warm3.modulate = Color(1, 1, 1, clampf(fire_wobble(time, 73, 0.08), 0.0, 1.0))
	_fx3.queue_redraw()
	_snow3.set_time(time * (0.6 if rm else 1.0))
	_note_fx.queue_redraw()
	_book.position = book_drift(time)
	_note_bg_fx.queue_redraw()
	_note_front.queue_redraw()
	# ---- v4: the lamp goes out
	var on := lamp_on(time)
	_lit4.visible = on
	_dark4.visible = not on
	_glow4.visible = on
	_fx4.queue_redraw()


## v3: a figure climbs the stair (behind the parapet) from x0 up to its head at x_top, then walks on to the left.
## Below the yard (on the stair) it is cut at the parapet's foot: the wall hides the legs, nothing shows on the
## snow in front of it.  Returns the cell's (unclipped) top-left.
func _place_climber(s: Sprite2D, idx: Dictionary, time: float, t0: float, x0: float, x_top: float, feet: float,
		speed: float) -> Vector2:
	s.visible = time >= t0
	var walked := maxf(0.0, time - t0) * speed
	var x := x0 - walked
	var below := 18.0 * clampf((x - x_top) / maxf(1.0, x0 - x_top), 0.0, 1.0)
	var pp: Array = LP.get("yard_parapet", [408, 262, 500, 312])
	var clip := Rect2(-4096.0, -4096.0, 8192.0, 4096.0 + float(pp[3]))
	var f := Vector2(roundf(x), roundf(feet + below))
	fig_frame_clip(s, idx, "walk_side_l", walk_i(walked), f, clip if below > 0.0 else NO_CLIP)
	return (f - FEET_OFF).round()


## v1: crows on the wire near the column; they lift off when the door moves and Konrad comes out.
func _draw_crows1() -> void:
	if not v1.visible or _crow_tex == null:
		return
	var m: Dictionary = (LP.get("loop_fx", {}) as Dictionary).get("crows", {})
	var perches: Array = m.get("perches", [[676, 176], [690, 176], [705, 176], [722, 176]])
	var n := maxi(1, _crow_tex.get_width() / 14)
	var cam := v1_cam()
	for i in perches.size():
		var pp: Array = perches[i]
		var p0 := Vector2(float(pp[0]) - cam - 7.0, float(pp[1]) - 11.0)
		var t0 := 0.95 + i * 0.16
		if t < t0:
			var f := 0 if fposmod(t * 0.9 + h01(i, 93), 1.0) < 0.75 else 1 + (i % 3)
			draw_cell(_crows1, _crow_tex, n, f, p0)
		else:
			var u := t - t0
			var p := p0 + Vector2(u * (70.0 + i * 10.0), -u * (40.0 + i * 8.0) + sin(u * 9.0) * 2.0)
			if p.y > -12.0 and p.x < 660.0:
				draw_cell(_crows1, _crow_tex, n, 7 + int(floor(u * 10.0)) % 4, p)


## v2: sparks at the tram's bow while it accelerates away.
func _draw_sparks2() -> void:
	if not v2.visible or t < float(TRAM_GO[0]) + 0.3:
		return
	var sz: Array = LP.get("tram_size", [250, 122])
	var bx := _tram.position.x + float(sz[0]) * 0.5 + 2.0
	var by := _tram.position.y + 1.0
	if bx < 0.0 or bx > 640.0:
		return
	if hnoise(t * 21.0, 97) > 0.6:
		_sparks2.draw_rect(Rect2(Vector2(bx - 1, by - 1), Vector2(3, 2)), Color("#d8e8ff"))
		_sparks2.draw_rect(Rect2(Vector2(bx - 3, by - 3), Vector2(1, 1)), Color("#a8c8ff"))


func _draw_v3() -> void:
	if not v3.visible:
		return
	var meta: Dictionary = LP.get("yard_layers", {})
	for r in meta.get("reds", []):
		if fposmod(t * 0.7 + float(r[0]) * 0.01, 1.0) < 0.55:
			_fx3.draw_rect(Rect2(Vector2(float(r[0]) - 1.5, float(r[1]) - 1.0).round(), Vector2(3, 2)), Color("#e0482c"))
	var ch: Array = meta.get("chimney", [504, 58])
	draw_puffs(_fx3, _smoke_tex, 8, Vector2(float(ch[0]), float(ch[1])), t, 4, 4.0, 46.0, 30.0, 0.55, 0.0, 3.0)
	var cones: Array = []
	for l in LP.get("yard_lamps", [[262, 104], [612, 96]]):
		cones.append([float(l[0]), float(l[1]) + 4.0, 34.0, 300.0])
	draw_lit_snow(_fx3, cones, t, 14, 531)
	var sg: Array = LP.get("yard_signal", [152, 158])
	draw_lit_snow(_fx3, [[float(sg[0]), float(sg[1]) + 4.0, 22.0, 240.0]], t, 8, 533, Color(0.55, 1.0, 0.65, 1.0))


## v3 insert: the notebook in his hand -- it drifts a little (held in the cold, lifted toward the light) and rocks
## with his breathing; whole pixels, reduced motion keeps only half the slow lift.
func book_drift(time: float) -> Vector2:
	var u := maxf(0.0, time - V3_CUT)
	var lift := -4.0 * ease01(time, V3_CUT, V3_CUT + 2.0)
	if reduced_motion():
		return Vector2(0, roundf(lift * 0.5))
	return Vector2(roundf(sin(u * 1.9) * 1.6 + sin(u * 0.7 + 1.0) * 1.0), roundf(lift + sin(u * 2.6 + 0.5) * 1.2))


## v3 insert, behind the book: the yard's lights out of focus (the office window warm, the signal green, the yard
## lamp), drifting the other way than the book (parallax).
func _draw_note_bg() -> void:
	if not v3n.visible or _bokeh_tex == null:
		return
	var k := motion_k()
	var u := maxf(0.0, t - V3_CUT)
	var spots := [[38, 132, 2, Color(1.0, 0.66, 0.30, 0.36)], [70, 238, 1, Color(1.0, 0.70, 0.36, 0.22)],
		[612, 70, 2, Color(0.40, 1.0, 0.55, 0.34)], [596, 196, 0, Color(0.40, 1.0, 0.55, 0.20)],
		[22, 60, 0, Color(1.0, 0.86, 0.60, 0.26)], [628, 286, 1, Color(0.70, 0.80, 0.95, 0.16)]]
	for i in spots.size():
		var sp: Array = spots[i]
		var drift := Vector2(-u * 2.0 + sin(u * 0.8 + i) * 1.5, cos(u * 0.6 + i) * 1.0) * k
		var c: Color = sp[3]
		c.a *= 0.85 + 0.15 * sin(t * 1.3 + i * 1.7)
		draw_cell(_note_bg_fx, _bokeh_tex, 3, int(sp[2]), Vector2(float(sp[0]) - 28.0, float(sp[1]) - 28.0) + drift, c)


## v3 insert, in front: his breath drifting up across the page, big flakes falling past the lens.
func _draw_note_front() -> void:
	if not v3n.visible:
		return
	var k := motion_k()
	if _breath_tex != null:
		for j in 2:
			var period := 2.4
			var age := fposmod((t - V3_CUT) / period + 0.15 + j * 0.5, 1.0)
			if age < 0.7:
				var p := Vector2(150.0 + j * 40.0 + age * 90.0 * k, 300.0 - age * 120.0 * k)
				var a := 0.42 * (1.0 - age / 0.7) * clampf(age * 8.0, 0.0, 1.0)
				draw_frame(_note_front, _breath_tex, 6, int(age / 0.7 * 5.0), p, false, Color(0.75, 0.95, 0.8, a))
	if _flake_tex != null:
		for i in 6:
			var sz := 1 + i % 3
			var sp := (14.0 + sz * 9.0) * k
			var x := fposmod(h01(i, 9131) * 680.0 + sin(t * 0.9 + i) * 6.0 * k + (t - V3_CUT) * 5.0 * k, 680.0) - 20.0
			var y := fposmod(h01(i, 9133) * 380.0 + (t - V3_CUT) * sp, 380.0) - 20.0
			draw_cell(_note_front, _flake_tex, 4, sz, Vector2(x, y), Color(0.75, 0.95, 0.80, 0.30 + 0.08 * sz))


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
			_note_fx.draw_rect(Rect2(p + Vector2(-1, 1), Vector2(4, 1)), Color(0.5, 0.7, 0.55, a))


## v4: dust turning in the work lamp's light while it burns; when it dies the filament glows out.
func _draw_v4() -> void:
	if not v4.visible:
		return
	var lamp := lv(LP, "siding_lamp", Vector2(366, 153))
	if lamp_on(t):
		draw_motes(_fx4, _motes_tex, Rect2(lamp.x - 120.0, lamp.y, 240.0, 150.0), lamp + Vector2(0, 50), 150.0, t, 24,
			9401, 0.7)
	else:
		var since := t - float(LAMP_FLICKS[2] if not reduced_motion() else LAMP_FLICKS[1])
		if since >= 0.0 and since < 0.9:
			var a := clampf(1.0 - since / 0.9, 0.0, 1.0)
			_fx4.draw_rect(Rect2(lamp + Vector2(-1, 0), Vector2(3, 2)), Color(0.95, 0.45, 0.15, a))
