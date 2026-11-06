extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## LS_C3_Fire (12 s) — the registry catches fire (C3P2_DESIGN §2.9).  Nobody is hurt on screen; the arsonist is
## never identifiable (a backlit silhouette in a long coat and a porter's cap, seen from behind).
##   f1  0-3     the green lamp flickers over the sorting table; a wisp of smoke in its light; Konrad looks up
##   f2  3-6     the Magazin aisle: a figure slips out through the lit service door at the end, the C-17 boxes
##               catch, the orange glow grows between the shelves
##   f3  6-8.5   the ramp door from inside: the cold gap light, a shadow passes outside, the iron bolt slides home
##   f4  8.5-12  the card hall burning: the fire runs along the cabinets (right -> left), smoke rolls under the
##               vault toward the camera, embers; Alexei at the table, a silhouette against the fire
## Line: cin.c3p2.fire.time.  Fire light: flame sheets cycle their shapes, the brightness only wobbles slowly
## (< 3 Hz, fire_wobble), never a full-screen flash; reduced motion halves the flame rate and the wobble.
## Round 10: the hall is a ray-cast vaulted cellar (cabinets on three walls, the barred window's snow light); the
## first smoke curls thin into the lamp's light; the service door throws its light and the figure's long shadow
## down the aisle, smoke rolls along the aisle's vault; smoke creeps in over the ramp door as the glow grows; the
## burning hall has a revealed band of embers behind the fire front, tall flames, burning paper rising and a
## rolling smoke layer under the vault.
## Round 11: fire that reads as fire -- clusters of licking tongues with white-hot cores and a translucent red
## fringe (no dark rim), merged into one wall of uneven height that rises behind the table's far edge (f4_table is a
## layer in front of it) and grows where the front has just passed; the hall itself is darker and the fire's light
## (f4_lit = burning hall minus unlit hall) is revealed behind the front with a soft edge, so the flames stay the
## brightest thing in the frame; additive halos bloom around every cluster; soft volumetric smoke (no dithered
## blotches) rolls along the aisle and under the vault toward the camera; the ramp door's gap light varies along
## its length and spills cold light onto the jamb and the floor, the snow blown in is snow.
## Art: tools/pixelgen/env_c3p2_cine_fire.py (+ _registry, _life) -> assets/cinematics/c3p2/fire/.

const DUR := 12.0
const SHOTS := [["f1", 0.0, 3.0], ["f2", 3.0, 6.0], ["f3", 6.0, 8.5], ["f4", 8.5, 12.0]]
const LINE_TIME := "cin.c3p2.fire.time"
const LOOK_UP := 1.75                 # Konrad lifts his head
## round 11: the f1 sheet's frames 1..3 (lifting, up, turned toward the smell of smoke) start at these times
const LOOK_KEYS := [1.75, 1.9, 2.3]
const DOOR := [3.0, 3.45, 3.85, 4.3]  # figure in the doorway, half out, empty lit doorway, door shut
const CATCH := 3.55                   # the first C-17 box catches
const SHADOW := [6.35, 6.95]          # someone passes outside the ramp door
const BOLT := [7.2, 7.55]             # the bolt slides home
const RUN := [8.3, 220.0]             # f4 fire front: start time, speed (px/s, right -> left)
## f1 lamp flicker dips (== LAMP_DIPS in tools/audiogen/c3p2_cine_audio.py: the crackles of c3p2cine_lamp)
const LAMP_DIPS := [0.55, 1.05, 1.4, 2.4]

var f1: Node2D
var f2: Node2D
var f3: Node2D
var f4: Node2D
var _cone: Sprite2D
var _konrad: Sprite2D
var _f1fx: Node2D
var _f2glow: Sprite2D
var _door: Sprite2D
var _f2fx: Node2D
var _f3warm: Sprite2D
var _f3fx: Node2D
var _f4glow: Sprite2D
var _f4cone: Sprite2D
var _f4fire: Node2D
var _alexei: Sprite2D
var _f4fx: Node2D
var _smoke: Texture2D
var _ember: Texture2D
var _f3root: Node2D
var _smoke_hot: Texture2D
var _paper: Texture2D
var _band: Sprite2D
var _f2light: Node2D
var _f2smoke: Node2D
var _f2heat: Node2D
var _f2fire_s: Texture2D
var _f2fire_m: Texture2D
var _f2fire_l: Texture2D
var _f4lit: Node2D
var _f4lit_tex: Texture2D
var _f4heat: Node2D
var _halo: Texture2D
var _kinds: Array = []
var _f3glow: Node2D


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0
	_shots = SHOTS


func chosen_lines() -> Array:
	return [LINE_TIME]


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 1.5},
		{"t": 0.0, "amb": "", "fade": 1.0},
		{"t": 0.0, "bed": "c3p2cine_lamp", "db": -8.0},
		{"t": 0.4, "say": LINE_TIME, "dur": 2.2},
		{"t": 3.0, "bed": "c3p2cine_ignite", "db": -5.0},
		{"t": DOOR[3] - 0.05, "sfx": "c3p2cine_service_door", "db": -11.0, "pv": 0.02},
		{"t": SHADOW[0] - 0.2, "bed": "c3p2cine_steps_out", "db": -10.0},
		{"t": BOLT[0] - 0.05, "bed": "c3p2cine_bolt", "db": -3.0},
		{"t": 8.5, "bed": "c3p2cine_roar", "db": -4.0},
	]


# ------------------------------------------------------------------ build
func _build() -> void:
	layout = _layout_section("fire")
	_smoke = tex("fire/smoke.png")
	_ember = tex("fire/ember.png")
	_smoke_hot = tex("fire/smoke_hot.png")
	_paper = tex("fire/paper.png")
	_halo = tex("fire/fire_halo.png")
	_f2fire_s = tex("fire/f2_fire_s.png")
	_f2fire_m = tex("fire/f2_fire_m.png")
	_f2fire_l = tex("fire/f2_fire_l.png")
	for kd in layout.get("f4_kinds", []):
		_kinds.append({"tex": tex(str(kd[0])), "w": int(kd[1]), "h": int(kd[2])})
	f1 = group("SortingTable")
	sprite("fire/f1_bg.png", Vector2.ZERO, f1)
	_cone = sprite("fire/lamp_cone.png", Vector2.ZERO, f1, 1, true)
	_konrad = sprite("fire/f1_konrad.png", _lv("f1_konrad"), f1, LOOK_KEYS.size() + 1)
	_f1fx = _fx_node(f1, "F1Fx", _draw_f1)
	f2 = group("Stacks")
	sprite("fire/f2_bg.png", Vector2.ZERO, f2)
	_f2light = _fx_node(f2, "DoorLight", _draw_f2_light)
	_f2light.material = additive()
	_door = sprite("fire/f2_door.png", _lv("f2_door_at"), f2, 4)
	_f2glow = sprite("fire/f2_glow.png", Vector2.ZERO, f2, 1, true)
	_f2fx = _fx_node(f2, "F2Fx", _draw_f2)
	_f2heat = _fx_node(f2, "F2Heat", _draw_f2_heat)
	_f2heat.material = additive()
	_f2smoke = _fx_node(f2, "F2Smoke", _draw_f2_smoke)
	f3 = group("RampDoor")
	_f3root = Node2D.new()
	_f3root.name = "Shake"
	f3.add_child(_f3root)
	sprite("fire/f3_bg.png", Vector2.ZERO, _f3root)
	_f3warm = sprite("fire/f3_warm.png", Vector2.ZERO, _f3root, 1, true)
	_f3glow = _fx_node(_f3root, "GapGlow", _draw_f3_glow)
	_f3glow.material = additive()
	_f3fx = _fx_node(_f3root, "F3Fx", _draw_f3)
	f4 = group("HallBurning")
	sprite("fire/f4_bg.png", Vector2.ZERO, f4)
	_f4fire = _fx_node(f4, "Fire", _draw_f4_fire)
	sprite("fire/f4_table.png", _lv("f4_table_at"), f4)
	_f4glow = sprite("fire/f4_glow.png", Vector2.ZERO, f4, 1, true)
	_band = sprite("fire/fire_band.png", Vector2(0, 150), f4, 1, true)
	_band.region_enabled = true
	_f4lit_tex = tex("fire/f4_lit.png")
	_f4lit = _fx_node(f4, "FireLight", _draw_f4_lit)
	_f4lit.material = additive()
	_f4heat = _fx_node(f4, "Heat", _draw_f4_heat)
	_f4heat.material = additive()
	_f4cone = sprite("fire/lamp_cone.png", Vector2.ZERO, f4, 1, true)
	_alexei = sprite("fire/f4_alexei.png", _lv("f4_alexei"), f4, 2)
	_f4fx = _fx_node(f4, "SmokeEmbers", _draw_f4_fx)


func _fx_node(parent: Node, n: String, fn: Callable) -> Node2D:
	var d := Node2D.new()
	d.name = n
	d.draw.connect(fn)
	parent.add_child(d)
	return d


func _lv(key: String) -> Vector2:
	var v = layout.get(key)
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return Vector2.ZERO


# ------------------------------------------------------------------ frame
func _apply(time: float) -> void:
	if f1 == null:
		return
	var sh := shot_at(time)
	f1.visible = sh == "f1"
	f2.visible = sh == "f2"
	f3.visible = sh == "f3"
	f4.visible = sh == "f4"
	var rm := reduced_motion()
	# f1: the lamp flickers (three short dips, each ~0.15 s; softened with reduced motion)
	var dip := 0.0
	for c in LAMP_DIPS:
		dip = maxf(dip, 1.0 - absf(time - c) / 0.08)
	_cone.modulate = Color(1, 1, 1, 1.0 - clampf(dip, 0.0, 1.0) * (0.12 if rm else 0.38))
	var kf := 0
	for i in LOOK_KEYS.size():
		if time >= float(LOOK_KEYS[i]):
			kf = i + 1
	_konrad.frame = mini(kf, _konrad.hframes - 1)
	_f1fx.queue_redraw()
	# f2: the doorway, the glow growing as the boxes catch
	var df := 0
	if time >= DOOR[3]:
		df = 3
	elif time >= DOOR[2]:
		df = 2
	elif time >= DOOR[1]:
		df = 1
	_door.frame = df
	var grow := ramp01(time, CATCH - 0.1, 6.0)
	_f2glow.modulate = Color(1, 1, 1, clampf((0.08 + 0.92 * grow) * fire_wobble(time, 3), 0.0, 1.0) if time >= CATCH - 0.1 else 0.0)
	_f2fx.queue_redraw()
	_f2light.queue_redraw()
	_f2heat.queue_redraw()
	_f2smoke.queue_redraw()
	# f3: the fire behind the camera warms the door more and more; the bolt jolts the door once
	_f3warm.modulate = Color(1, 1, 1, clampf((0.35 + 0.65 * ramp01(time, 6.0, 8.5)) * fire_wobble(time, 5), 0.0, 1.0))
	var jolt := 0.0
	if not rm and time >= BOLT[1] and time < BOLT[1] + 0.12:
		jolt = 1.0
	_f3root.position = Vector2(jolt, 0)
	_f3fx.queue_redraw()
	_f3glow.queue_redraw()
	# f4
	var burnt := _burning_fraction(time)
	_f4glow.modulate = Color(1, 1, 1, clampf((0.45 + 0.55 * burnt) * fire_wobble(time, 9), 0.0, 1.0))
	_f4cone.modulate = Color(1, 1, 1, 0.35 - 0.2 * burnt)
	_alexei.frame = 0 if time < 10.4 else 1
	_f4fire.queue_redraw()
	_f4fx.queue_redraw()
	_f4lit.queue_redraw()
	_f4heat.queue_redraw()
	# the heat band behind the fire front (revealed from the right as the fire runs left)
	if _band.texture:
		var fr0 := clampf(_front(time), 0.0, 640.0)
		_band.region_rect = Rect2(fr0, 0, 640.0 - fr0, _band.texture.get_height())
		_band.position = Vector2(roundf(fr0), 150)
		_band.visible = fr0 < 639.0
		_band.modulate = Color(1, 1, 1, clampf(0.75 * fire_wobble(time, 13, 0.1), 0.0, 1.0))


func _front(time: float) -> float:
	return 680.0 - maxf(0.0, time - float(RUN[0])) * float(RUN[1]) * (0.8 if reduced_motion() else 1.0)


func _burning_fraction(time: float) -> float:
	return clampf((680.0 - _front(time)) / 700.0, 0.0, 1.0)


# ------------------------------------------------------------------ draw
## Frame `i` of an n-frame sheet, bottom-centre at `pos`, grown to `k` of its height (a fire catching).
static func _draw_grown(ci: CanvasItem, sheet: Texture2D, n: int, i: int, pos: Vector2, k: float,
		mod := Color(1, 1, 1, 1)) -> void:
	if sheet == null:
		return
	var fw := sheet.get_width() / maxi(1, n)
	var fh := sheet.get_height()
	var h := maxf(1.0, roundf(fh * clampf(k, 0.05, 1.0)))
	var at := Vector2(roundf(pos.x - fw * 0.5), roundf(pos.y - h))
	ci.draw_texture_rect_region(sheet, Rect2(at, Vector2(fw, h)), Rect2(posmod(i, n) * fw, 0, fw, fh), mod)


## Frame `i` of an n-frame sheet scaled by `sc` around `center` (soft smoke grows as it nears the camera).
static func _draw_scaled(ci: CanvasItem, sheet: Texture2D, n: int, i: int, center: Vector2, sc: float,
		mod := Color(1, 1, 1, 1)) -> void:
	if sheet == null:
		return
	var fw := sheet.get_width() / maxi(1, n)
	var fh := sheet.get_height()
	var sz := (Vector2(fw, fh) * sc).round()
	ci.draw_texture_rect_region(sheet, Rect2((center - sz * 0.5).round(), sz), Rect2(posmod(i, n) * fw, 0, fw, fh), mod)


func _draw_f1() -> void:
	if not f1.visible:
		return
	# thin wisps of smoke curl into the lamp's light from the right, a little more of it each second
	if _smoke and t > 0.5:
		var n := 8
		for i in 4:
			var age := t - 0.5 - i * 0.5
			if age < 0.0:
				continue
			var x := 540.0 - age * 42.0 * motion_k() - i * 16.0
			var y := 110.0 + sin(age * 1.7 + i) * 8.0 - age * 5.0 * motion_k()
			var fi := clampi(int(age / 0.4), 0, n - 1)
			var a := clampf(age / 1.0, 0.0, 1.0) * (0.75 - i * 0.12)
			_draw_scaled(_f1fx, _smoke, n, fi, Vector2(x, y), 1.0 + age * 0.25, Color(1, 1, 1, a))
	# dust motes in the cone
	for i in 12:
		var ph := float(i) * 2.3
		var mx := 300.0 + sin(ph + t * 0.6) * (40.0 + i * 6.0)
		var my := 120.0 + fposmod(i * 17.0 + t * 6.0 * motion_k(), 110.0)
		_f1fx.draw_rect(Rect2(Vector2(floorf(mx), floorf(my)), Vector2.ONE), Color(0.7, 0.9, 0.75, 0.5))


## f2: the burning boxes on the right shelves -- each catches small, grows, every second one climbs tall
func _f2_fire_state(i: int) -> Array:
	var age := t - (CATCH + i * 0.32)
	if age < 0.0:
		return []
	if age < 0.55:
		return [_f2fire_s, clampf(0.45 + age / 0.35, 0.45, 1.0), age]
	if age < 1.3 or i % 2 == 1:
		return [_f2fire_m, clampf(0.55 + (age - 0.55) / 0.45, 0.55, 1.0), age]
	return [_f2fire_l, clampf(0.6 + (age - 1.3) / 0.6, 0.6, 1.0), age]


func _draw_f2() -> void:
	if not f2.visible:
		return
	if t < DOOR[2] and t >= DOOR[0]:
		var d: Array = layout.get("f2_door", [303, 133, 336, 203])
		var cx := (float(d[0]) + float(d[2])) * 0.5 + (0.0 if t < DOOR[1] else 9.0)
		var yb := float(d[3])
		_f2fx.draw_colored_polygon(PackedVector2Array([Vector2(cx - 4, yb), Vector2(cx + 4, yb), Vector2(cx + 34, 360),
			Vector2(cx - 26, 360)]), Color(0.03, 0.02, 0.02, 0.5))
	var anchors: Array = layout.get("f2_fire", [])
	for i in anchors.size():
		var st := _f2_fire_state(i)
		if st.is_empty():
			continue
		var a: Array = anchors[i]
		_draw_grown(_f2fx, st[0], 8, flame_frame(t, 8, i * 0.37), Vector2(float(a[0]), float(a[1]) + 2.0), float(st[1]))


## f2: a warm bloom around every burning box (additive)
func _draw_f2_heat() -> void:
	if not f2.visible or _halo == null:
		return
	var anchors: Array = layout.get("f2_fire", [])
	for i in anchors.size():
		var st := _f2_fire_state(i)
		if st.is_empty():
			continue
		var a: Array = anchors[i]
		var tx: Texture2D = st[0]
		var w := float(tx.get_width() / 8) * 2.2 if tx else 60.0
		var h := float(tx.get_height()) * 1.5 * float(st[1]) if tx else 60.0
		var g := clampf(float(st[2]) / 0.6, 0.0, 1.0)
		_f2heat.draw_texture_rect(_halo, Rect2(Vector2(float(a[0]) - w * 0.5, float(a[1]) + 6.0 - h), Vector2(w, h)),
			false, Color(1, 1, 1, 0.5 * g * fire_wobble(t, 60 + i, 0.15)))


## f2: the lit doorway throws a wedge of light down the aisle; while the figure stands in it, its long shadow
func _draw_f2_light() -> void:
	if not f2.visible or t >= DOOR[3]:
		return
	var d: Array = layout.get("f2_door", [303, 133, 336, 203])
	var x0 := float(d[0])
	var x1 := float(d[2])
	var yb := float(d[3])
	var a := 0.16 * clampf((DOOR[3] - t) / 0.25, 0.0, 1.0)
	var wedge := PackedVector2Array([Vector2(x0, yb), Vector2(x1, yb), Vector2(x1 + 120, 360), Vector2(x0 - 120, 360)])
	_f2light.draw_colored_polygon(wedge, Color(0.95 * a, 0.68 * a, 0.36 * a, 1.0))


## f2: soft smoke climbs from the burning boxes to the aisle's vault and rolls along it toward the camera
func _draw_f2_smoke() -> void:
	if not f2.visible or _smoke_hot == null or t < CATCH + 0.3:
		return
	var k := motion_k()
	for i in 12:
		var born := CATCH + 0.3 + i * 0.21
		var age := t - born
		if age < 0.0:
			continue
		var src := Vector2(428.0 + float(i % 3) * 9.0, 168.0 - float(i % 4) * 14.0)
		var p := src + Vector2(age * 24.0 + sin(age * 1.9 + i) * 6.0,
			-minf(age, 0.8) * 72.0 - maxf(0.0, age - 0.8) * 22.0) * k
		var sc := 0.42 + age * 0.5
		var a := clampf(age / 0.3, 0.0, 1.0) * clampf(1.0 - (age - 2.2) / 1.0, 0.0, 1.0) * 0.92
		_draw_scaled(_f2smoke, _smoke_hot, 8, clampi(int(age / 0.35), 0, 7), p, sc, Color(1, 1, 1, a))


## f3: the cold light of the yard through the gap, darkened while someone passes outside
func _gap_light() -> float:
	var pass_k := 0.0
	if t >= SHADOW[0] and t < SHADOW[1]:
		pass_k = sin((t - SHADOW[0]) / (SHADOW[1] - SHADOW[0]) * PI)
	return 1.0 - pass_k * 0.85


## f3: soft cold light spilling from the gap onto the jamb, the door's edge and the floor (additive)
func _draw_f3_glow() -> void:
	if not f3.visible:
		return
	var g: Array = layout.get("f3_gap", [470, 0, 473, 292])
	var gx := float(g[0]) + 1.5
	var gy1 := float(g[3])
	var lk := _gap_light()
	var cold := Color(0.30, 0.36, 0.46)
	# a soft band along the gap, brightest at the height of the yard lamp outside
	for j in 6:
		var w := 2.0 + j * 3.0
		var a := (0.30 - j * 0.045) * lk
		for sgm in 12:
			var y0 := gy1 * sgm / 12.0
			var y1 := gy1 * (sgm + 1) / 12.0
			var mid := 1.0 - absf((y0 + y1) * 0.5 - 150.0) / 170.0
			var c := cold * (a * (0.45 + 0.55 * clampf(mid, 0.0, 1.0)))
			_f3glow.draw_rect(Rect2(gx - w, y0, w * 2.0, y1 - y0), Color(c.r, c.g, c.b, 1.0))
	# a fan of light on the floor in front of the bottom gap
	var fl: Array = layout.get("f3_floor", [150, 292, 473, 295])
	var x0 := float(fl[0])
	var x1 := float(fl[2])
	var fy := float(fl[1]) + 2.0
	for j in 5:
		var a2 := (0.16 - j * 0.028) * lk
		var c2 := cold * a2
		_f3glow.draw_colored_polygon(PackedVector2Array([Vector2(x0 + 10, fy), Vector2(x1, fy),
			Vector2(x1 + 6 + j * 4, fy + 6 + j * 7), Vector2(x0 - 10 - j * 8, fy + 6 + j * 7)]), Color(c2.r, c2.g, c2.b, 1.0))


func _draw_f3() -> void:
	if not f3.visible:
		return
	var g: Array = layout.get("f3_gap", [470, 0, 473, 292])
	var gx := float(g[0])
	var gy1 := float(g[3])
	var lk := _gap_light()
	var dark := Color("#1a2431")
	# the vertical gap: brightness along its length (the yard lamp at mid height, the snow outside lower down),
	# snowflakes passing outside flick across it
	var y := 0.0
	while y < gy1:
		var mid := clampf(1.0 - absf(y - 150.0) / 170.0, 0.0, 1.0)
		var b := (0.42 + 0.5 * mid + 0.08 * hnoise(y * 0.15, 71)) * lk
		var flake := hnoise(y * 0.09 - t * 3.0, 73) > 0.82
		var c := dark.lerp(Color("#c2c9d2"), clampf(b, 0.0, 1.0))
		if flake:
			c = c.lerp(Color("#f2f3f5"), 0.6 * lk)
		_f3fx.draw_rect(Rect2(gx, y, 3, 4), Color(c, 0.55))
		_f3fx.draw_rect(Rect2(gx + 1, y, 1, 4), c.lerp(Color("#dee2e7"), 0.5 * mid * lk))
		y += 4.0
	# the bottom gap: uneven, snow piled outside blocks parts of it
	var fl: Array = layout.get("f3_floor", [150, 292, 473, 295])
	var x := float(fl[0])
	while x < float(fl[2]):
		var b2 := (0.55 + 0.45 * hnoise(x * 0.05, 79)) * lk
		var blocked := hnoise(x * 0.11, 83) > 0.55
		var c3 := dark.lerp(Color("#a1aab7"), clampf(b2, 0.0, 1.0))
		if blocked:
			c3 = dark.lerp(Color("#4f5e70"), 0.6)
		_f3fx.draw_rect(Rect2(x, float(fl[1]), 6, 1), c3)
		_f3fx.draw_rect(Rect2(x, float(fl[1]) + 1, 6, 1), Color(c3, 0.5))
		x += 6.0
	# the shadow of the feet passing along the bottom gap (right to left)
	if lk < 1.0:
		var u := (t - SHADOW[0]) / (SHADOW[1] - SHADOW[0])
		var fx := lerpf(float(fl[2]) + 20.0, float(fl[0]) - 40.0, u)
		_f3fx.draw_rect(Rect2(fx, float(fl[1]), 30, 2), Color("#0c111c"))
	# the bolt: its shadow slides across the gap and onto the edge of the door
	if t >= BOLT[0]:
		var bk := ramp01(t, BOLT[0], BOLT[1])
		var by := 132.0
		var blen := roundf(bk * 30.0)
		_f3fx.draw_rect(Rect2(gx, by - 2, 3, 12), Color("#05070c"))
		_f3fx.draw_rect(Rect2(gx - blen + 3, by, blen, 8), Color(0.02, 0.03, 0.05, 0.8))
		_f3fx.draw_rect(Rect2(gx - blen + 3, by + 8, blen, 1), Color(0.6, 0.66, 0.74, 0.35))
	# smoke creeps in from the left under the lintel, thicker toward the end of the shot
	if _smoke_hot and t > 6.6:
		for i in 6:
			var age := t - 6.6 - i * 0.28
			if age < 0.0:
				continue
			var p := Vector2(-30.0 + age * 66.0 * motion_k() + i * 24.0, 44.0 + i * 5.0 + sin(age + i) * 4.0)
			_draw_scaled(_f3fx, _smoke_hot, 8, clampi(int(age / 0.3), 0, 7), p, 1.1 + age * 0.3,
				Color(1, 1, 1, clampf(age * 0.6, 0.0, 0.85)))
	# snow blown through the bottom gap, drifting into the room (cold white, never warm)
	for i in 18:
		var ph := float(i) * 1.37
		var age := fposmod(t * 0.9 + i * 0.19, 1.6)
		var sx := float(fl[0]) + fposmod(i * 61.0, float(fl[2]) - float(fl[0]))
		var sy := float(fl[1]) + 2.0 + age * 18.0 * motion_k()
		sx -= age * 22.0 * motion_k() + sin(ph + t * 3.0) * 2.0
		_f3fx.draw_rect(Rect2(Vector2(floorf(sx), floorf(sy)), Vector2.ONE),
			Color(0.88, 0.92, 0.97, clampf(1.0 - age / 1.6, 0.0, 1.0) * lk))


func _lit_time(x: float) -> float:
	return float(RUN[0]) + (680.0 - x) / (float(RUN[1]) * (0.8 if reduced_motion() else 1.0))


## f4: the fire runs right -> left; every cluster catches small, then rises to its full height behind the table
func _draw_f4_fire() -> void:
	if not f4.visible or _kinds.size() < 4:
		return
	var pts: Array = layout.get("f4_fire", [])
	for i in pts.size():
		var p: Array = pts[i]
		var x := float(p[0])
		var age := t - _lit_time(x)
		if age < 0.0:
			continue
		var kd: Dictionary = _kinds[clampi(int(p[2]) if p.size() > 2 else 0, 0, _kinds.size() - 1)]
		var k := clampf(0.4 + (age - 0.22) / 0.55 * 0.6, 0.4, 1.0)
		if age < 0.22:
			kd = _kinds[3]
			k = 0.45 + 0.55 * age / 0.22
		_draw_grown(_f4fire, kd["tex"], 8, flame_frame(t, 8, i * 0.29), Vector2(x, float(p[1])), k)


## f4: the burning cabinets' light, revealed behind the fire front with a soft edge (additive)
func _draw_f4_lit() -> void:
	if not f4.visible or _f4lit_tex == null:
		return
	var fr := _front(t)
	var soft := 72.0
	var a_all := clampf(0.94 * fire_wobble(t, 9, 0.06), 0.0, 1.0)
	var x0 := clampf(fr + soft, 0.0, 640.0)
	if x0 < 640.0:
		_f4lit.draw_texture_rect_region(_f4lit_tex, Rect2(x0, 0, 640.0 - x0, 360), Rect2(x0, 0, 640.0 - x0, 360),
			Color(1, 1, 1, a_all))
	for j in 9:
		var xa := maxf(0.0, fr + j * soft / 9.0)
		var xb := minf(640.0, fr + (j + 1) * soft / 9.0)
		if xb <= xa:
			continue
		_f4lit.draw_texture_rect_region(_f4lit_tex, Rect2(xa, 0, xb - xa, 360), Rect2(xa, 0, xb - xa, 360),
			Color(1, 1, 1, a_all * (float(j) + 0.5) / 9.0))


## f4: a warm bloom around every burning cluster (additive), so the flames glow into the smoke and the cabinets
func _draw_f4_heat() -> void:
	if not f4.visible or _halo == null or _kinds.size() < 4:
		return
	var pts: Array = layout.get("f4_fire", [])
	for i in pts.size():
		var p: Array = pts[i]
		var age := t - _lit_time(float(p[0]))
		if age < 0.0:
			continue
		var kd: Dictionary = _kinds[clampi(int(p[2]), 0, _kinds.size() - 1)]
		var gk := clampf(age / 0.8, 0.0, 1.0)
		var w := float(kd["w"]) * 1.8
		var h := float(kd["h"]) * 1.3 * (0.45 + 0.55 * gk)
		_f4heat.draw_texture_rect(_halo, Rect2(Vector2(float(p[0]) - w * 0.5, float(p[1]) - h * 0.92), Vector2(w, h)),
			false, Color(1, 1, 1, 0.42 * gk * fire_wobble(t, 50 + i, 0.15)))
	# embers rising from the fire line (additive: they glow, they never darken the flames)
	if _ember:
		var k := motion_k()
		var fr := _front(t)
		for i in 30:
			var ph := float(i) * 1.91
			var x0 := 640.0 - fposmod(i * 47.0, 660.0)
			if x0 < fr:
				continue
			var age := fposmod(t * 0.8 + i * 0.13, 1.8)
			var x := x0 + sin(ph + t * 2.0) * 6.0
			var y := 210.0 - age * 80.0 * k
			draw_frame(_f4heat, _ember, 4, int(floor(t * 3.0 + i)) % 4, Vector2(x, y), false, Color(1, 1, 1, clampf(1.0 - age / 1.8, 0.0, 1.0)))


func _draw_f4_fx() -> void:
	if not f4.visible:
		return
	var k := motion_k()
	var fr := _front(t)
	# smoke: rises from the burning cabinets to the vault, then rolls along it toward the camera, growing
	if _smoke_hot:
		for i in 24:
			var born := 8.2 + i * 0.15
			var age := t - born
			if age < 0.0:
				continue
			var x := 640.0 - fposmod(i * 83.0, 700.0) + sin(i * 1.7 + t * 0.5) * 10.0
			if x < fr - 40.0:
				continue
			var y := 150.0 - 84.0 * minf(age / 0.9, 1.0) * k + maxf(0.0, age - 0.9) * 16.0 * k
			var sc := 0.7 + minf(age, 3.0) * 0.55
			var a := clampf(age / 0.4, 0.0, 1.0) * 0.9
			_draw_scaled(_f4fx, _smoke_hot, 8, clampi(int(age / 0.4), 0, 7), Vector2(x, y), sc, Color(1, 1, 1, a))
	# burning paper lifting off the drawers, tumbling up
	if _paper:
		for i in 12:
			var x0 := 640.0 - fposmod(i * 61.0, 650.0)
			if x0 < fr:
				continue
			var age := fposmod(t * 0.5 + i * 0.21, 2.2)
			var p := Vector2(x0 + sin(age * 3.0 + i) * 10.0, 220.0 - age * 70.0 * k)
			# lit by the fire behind it: the scrap glows warm, never a dark fleck on the flames
			draw_frame(_f4fx, _paper, 6, int(floor(t * 8.0 + i)) % 6, p, false,
				Color(1.7, 1.3, 0.95, clampf(1.0 - age / 2.2, 0.0, 1.0)))
