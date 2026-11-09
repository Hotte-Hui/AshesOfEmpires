extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## LS_C3_Fire (12 s) — the registry catches fire (C3P2_DESIGN §2.9).  Nobody is hurt on screen; the arsonist is
## never identifiable (a backlit silhouette in a long coat and a porter's cap, seen from behind).
##   f1  0-3     the green lamp flickers over the sorting table; a wisp of smoke in its light; Konrad looks up
##   f2  3-6     the Magazin aisle: a figure slips out through the lit service door at the end, the C-17 boxes
##               catch, the orange glow grows between the shelves
##   f3  6-8.5   the ramp door from inside: the cold gap light, a shadow passes outside, the iron bolt slides home
##   f4  8.5-12  the card hall burning: the fire runs along the cabinets (right -> left), smoke rolls under the
##               vault toward the camera, embers; Alexei at the table, a silhouette against the fire
## Line: cin.c3p2.fire.time.
## Round 10: the hall is a ray-cast vaulted cellar (cabinets on three walls, the barred window's snow light); the
## service door throws its light and the figure's long shadow down the aisle; smoke creeps in over the ramp door.
## Round 11: the hall itself is darker and the fire's light (f4_lit = burning hall minus unlit hall) is revealed
## behind the front, so the flames stay the brightest thing in the frame; the ramp door's gap light varies along
## its length and spills cold light onto the jamb and the floor, the snow blown in is snow.
## Round 13: the fire is pixel art -- every flame, puff of smoke, spark and pool of fire light comes from the pixel
## fire kit (tools/pixelgen/pixel_fire.py -> assets/fx/pixel_fire/, played by scripts/render/pixel_fire.gd: whole
## pixels, never scaled, no alpha fades).  f1: wisps in the lamp's green.  f2: every box catches as a small flame
## and steps up to a larger sheet; the fire's light (f2_glow) spreads from the boxes as a dithered pool that grows
## in steps; puffs climb to the vault and roll toward the camera.  f3: the warm pool on the door grows in six
## stages.  f4: a wall of fire (tiles) rises out of the cabinets' foot line behind the running front, towers of
## flame stand behind it, the largest flames on the side walls in front; f4_lit follows the front as a dithered
## wipe (the table gets its own lit layer, so the flames between hall and table stay pure palette); a bank of
## smoke hangs under the vault, puffs climb into it; sparks rise on arcs and cool, paper burns out.
## Fire light never strobes: pools step at most PF.LIGHT_HZ times a second, never a full-screen flash; reduced
## motion halves the flames' and the light's rate and the travel of smoke and sparks.
## Art: tools/pixelgen/env_c3p2_cine_fire.py (+ _registry, _life; build_fx for the kit-made sheets) ->
## assets/cinematics/c3p2/fire/.

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
## f2: the heart of the burning boxes (the fire's light spreads from here)
const F2_HEART := Vector2(424, 176)
## f3: the smoke creeps in under the lintel from the left: start, speed (px/s), its foot line
const CREEP := [6.6, 128.0, 94.0]
## f4: the foot line of the wall of fire (behind the table's far edge); it starts to rise WALL_LAG px behind the
## front (nearer the front only the single flames have caught) and stands at full height WALL_RAMP px further
const WALL_Y := 247.0
const WALL_LAG := 34.0
const WALL_RAMP := 104.0
## f4: the fire's light behind the front has a dithered edge this wide
const LIT_SOFT := 72.0
## f4: the smoke under the vault runs ahead of the fire by this much; the bank's foot line
const SMOKE_LEAD := 110.0
const BANK_Y := 100.0
const KIT := ["flame_xs", "flame_s", "flame_m", "flame_l", "flame_xl", "flame_xxl", "wall_a", "wall_b", "puff_m",
	"puff_l", "puff_xl", "bank_a", "bank_b", "veil_a", "veil_b", "glow_s", "glow_m", "glow_l"]

var f1: Node2D
var f2: Node2D
var f3: Node2D
var f4: Node2D
var _cone: Sprite2D
var _konrad: Sprite2D
var _f1fx: Node2D
var _f2glow: Sprite2D
var _f2reveal: ShaderMaterial
var _door: Sprite2D
var _f2fx: Node2D
var _f3warm: Sprite2D
var _f3fx: Node2D
## f4: the fire's light on the hall (f4_lit, wiped in behind the front); the name is the tests' handle on it
var _f4glow: Sprite2D
var _f4reveal: ShaderMaterial
var _f4lit_table: Sprite2D
var _f4cone: Sprite2D
var _f4fire: Node2D
var _alexei: Sprite2D
var _f4fx: Node2D
var _f4bank: Node2D
var _f3root: Node2D
var _paper: Texture2D
var _f2light: Node2D
var _f2smoke: Node2D
var _f2heat: Node2D
var _f2order: Array = []
var _f4heat: Node2D
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
	need_kit(KIT)
	own_sheet("c3p2_wisp_s", "fire/wisp_s.png", 8)
	own_sheet("c3p2_wisp_m", "fire/wisp_m.png", 10)
	_paper = tex("fire/paper.png")
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
	_f2glow = sprite("fire/f2_glow.png", Vector2.ZERO, f2)
	_f2reveal = PF.reveal_material()
	_f2glow.material = _f2reveal
	_f2heat = _fx_node(f2, "F2Heat", _draw_f2_heat)
	_f2heat.material = additive()
	_f2fx = _fx_node(f2, "F2Fx", _draw_f2)
	_f2smoke = _fx_node(f2, "F2Smoke", _draw_f2_smoke)
	# the boxes higher up the shelves first, so the nearer flames stand in front
	var anchors: Array = layout.get("f2_fire", [])
	for i in anchors.size():
		_f2order.append(i)
	_f2order.sort_custom(func(a: int, b: int) -> bool: return float(anchors[a][1]) < float(anchors[b][1]))
	f3 = group("RampDoor")
	_f3root = Node2D.new()
	_f3root.name = "Shake"
	f3.add_child(_f3root)
	sprite("fire/f3_bg.png", Vector2.ZERO, _f3root)
	_f3warm = sprite("fire/f3_warm.png", _lv("f3_warm_at"), _f3root, 6, true)
	_f3glow = _fx_node(_f3root, "GapGlow", _draw_f3_glow)
	_f3glow.material = additive()
	_f3fx = _fx_node(_f3root, "F3Fx", _draw_f3)
	f4 = group("HallBurning")
	sprite("fire/f4_bg.png", Vector2.ZERO, f4)
	_f4reveal = PF.reveal_material()
	_f4glow = sprite("fire/f4_lit.png", Vector2.ZERO, f4)
	_f4glow.material = _f4reveal
	_f4heat = _fx_node(f4, "Heat", _draw_f4_heat)
	_f4heat.material = additive()
	_f4fire = _fx_node(f4, "Fire", _draw_f4_fire)
	sprite("fire/f4_table.png", _lv("f4_table_at"), f4)
	_f4lit_table = sprite("fire/f4_lit_table.png", _lv("f4_table_at"), f4)
	_f4lit_table.material = _f4reveal
	_f4cone = sprite("fire/lamp_cone.png", Vector2.ZERO, f4, 1, true)
	_alexei = sprite("fire/f4_alexei.png", _lv("f4_alexei"), f4, 2)
	_f4bank = _fx_node(f4, "SmokeBank", _draw_f4_bank)
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
	# f2: the doorway; the fire's light spreads from the boxes as they catch -- a dithered pool that grows in
	# steps of 8 px and breathes by one step
	var df := 0
	if time >= DOOR[3]:
		df = 3
	elif time >= DOOR[2]:
		df = 2
	elif time >= DOOR[1]:
		df = 1
	_door.frame = df
	_f2glow.visible = time >= CATCH - 0.1
	var reach := snappedf(26.0 + 600.0 * ramp01(time, CATCH - 0.1, 6.0), 8.0) + 8.0 * light_step(time, 3)
	PF.set_reveal(_f2reveal, F2_HEART, Vector2.ZERO, Vector2(reach, reach * 0.8), 0.7)
	_f2fx.queue_redraw()
	_f2light.queue_redraw()
	_f2heat.queue_redraw()
	_f2smoke.queue_redraw()
	# f3: the fire behind the camera warms the door more and more (the pool's stages); the bolt jolts the door once
	_f3warm.frame = clampi(2 + int(ramp01(time, 6.0, 8.5) * 3.99) + mini(0, light_step(time, 5)), 0, 5)
	var jolt := 0.0
	if not rm and time >= BOLT[1] and time < BOLT[1] + 0.12:
		jolt = 1.0
	_f3root.position = Vector2(jolt, 0)
	_f3fx.queue_redraw()
	_f3glow.queue_redraw()
	# f4: the fire's light follows the front as a dithered wipe (whole pixels)
	var burnt := _burning_fraction(time)
	var lit_from := 840.0
	PF.set_reveal(_f4reveal, Vector2(lit_from, 180), Vector2(lit_from - (_front(time) + LIT_SOFT), 4000),
		Vector2(LIT_SOFT, 1), 1.0)
	_f4cone.modulate = Color(1, 1, 1, 0.35 - 0.2 * burnt)
	_alexei.frame = 0 if time < 10.4 else 1
	_f4fire.queue_redraw()
	_f4fx.queue_redraw()
	_f4heat.queue_redraw()
	_f4bank.queue_redraw()


func _front(time: float) -> float:
	return 680.0 - maxf(0.0, time - float(RUN[0])) * float(RUN[1]) * (0.8 if reduced_motion() else 1.0)


func _burning_fraction(time: float) -> float:
	return clampf((680.0 - _front(time)) / 700.0, 0.0, 1.0)


# ------------------------------------------------------------------ draw
func _draw_f1() -> void:
	if not f1.visible:
		return
	# thin wisps of smoke curl into the lamp's light from the right, a little more of it each second
	PF.plume(_f1fx, {"sheets": ["c3p2_wisp_m", "c3p2_wisp_s", "c3p2_wisp_m"], "from": Vector2(556, 112),
		"spread": Vector2(6, 10), "count": 6, "life": 2.6, "rise": 7.0, "slow": 0.0, "drift": Vector2(-48, 0),
		"sway": 5.0, "t0": 0.5, "seed": 11, "rate": motion_k()}, t)
	# dust motes in the cone
	for i in 12:
		var ph := float(i) * 2.3
		var mx := 300.0 + sin(ph + t * 0.6) * (40.0 + i * 6.0)
		var my := 120.0 + fposmod(i * 17.0 + t * 6.0 * motion_k(), 110.0)
		_f1fx.draw_rect(Rect2(Vector2(floorf(mx), floorf(my)), Vector2.ONE), Color(0.7, 0.9, 0.75, 0.5))


## f2: the burning boxes on the right shelves -- each catches as a small flame and steps up to a larger sheet,
## every second one climbs tall: [flame sheet, light sheet, the flame's height] ([] = not burning yet)
func _f2_fire_state(i: int) -> Array:
	var age := t - (CATCH + i * 0.32)
	if age < 0.0:
		return []
	if age < 0.2:
		return ["flame_xs", "glow_s", 12.0]
	if age < 0.5:
		return ["flame_s", "glow_s", 20.0]
	if age < 1.0:
		return ["flame_m", "glow_m", 36.0]
	if age < 1.8 or i % 2 == 1:
		return ["flame_l", "glow_l", 62.0]
	return ["flame_xl", "glow_l", 100.0]


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
	for i in _f2order:
		var st := _f2_fire_state(i)
		if st.is_empty():
			continue
		var a: Array = anchors[i]
		PF.flame(_f2fx, str(st[0]), Vector2(float(a[0]), float(a[1]) + 2.0), t, i, fire_rate())
	PF.sparks(_f2fx, {"rect": Rect2(398, 150, 46, 62), "count": 9, "life": 0.9, "rise": 50.0, "kick": 10.0,
		"t0": CATCH + 0.5, "seed": 27, "rate": motion_k()}, t)


## f2: the fire's light on the shelves around every burning box (additive pools that breathe)
func _draw_f2_heat() -> void:
	if not f2.visible:
		return
	var anchors: Array = layout.get("f2_fire", [])
	for i in anchors.size():
		var st := _f2_fire_state(i)
		if st.is_empty():
			continue
		var a: Array = anchors[i]
		PF.light(_f2heat, str(st[1]), Vector2(float(a[0]), float(a[1]) - float(st[2]) * 0.45), t, i, fire_rate())


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


## f2: puffs climb from the burning boxes to the aisle's vault and roll along it toward the camera
func _draw_f2_smoke() -> void:
	if not f2.visible:
		return
	var k := motion_k()
	PF.plume(_f2smoke, {"sheets": ["puff_l", "puff_xl"], "from": Vector2(440, 88), "spread": Vector2(18, 6),
		"count": 4, "life": 2.6, "rise": 5.0, "drift": Vector2(28, 0), "t0": CATCH + 1.1, "seed": 23, "rate": k}, t)
	PF.plume(_f2smoke, {"sheets": ["puff_m", "puff_l", "puff_m"], "from": Vector2(424, 148), "spread": Vector2(14, 14),
		"count": 7, "life": 2.0, "rise": 60.0, "slow": 1.1, "drift": Vector2(6, 0), "bend": 10.0, "t0": CATCH + 0.3,
		"seed": 21, "rate": k}, t)


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
	# smoke creeps in from the left under the lintel, further and further: a bank behind a rolling head
	if t >= float(CREEP[0]):
		smoke_front(_f3fx, -50.0 + (t - float(CREEP[0])) * float(CREEP[1]) * motion_k(), 1.0, float(CREEP[2]), t, true)
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


## f4: a single flame on an anchor grows by stepping up the kit's sizes; kind (layout f4_fire: 0 mid / 1 big /
## 2 wide / 3 small) says how far
static func _f4_stage(age: float, kind: int) -> String:
	if age < 0.0:
		return ""
	if age < 0.15:
		return "flame_s"
	if age < 0.35 or kind == 3:
		return "flame_m"
	if age < 0.6 or kind == 2:
		return "flame_l"
	if age < 0.9 or kind == 0:
		return "flame_xl"
	return "flame_xxl"


## f4: the fire runs right -> left.  Behind the front every anchor catches as a small flame and steps up; the
## wall of fire rises out of the cabinets' foot line (WALL_RAMP px behind the front it stands at full height),
## towers stand behind it, the side walls' flames (lower, nearer the camera) in front
func _draw_f4_fire() -> void:
	if not f4.visible:
		return
	var rate := fire_rate()
	var pts: Array = layout.get("f4_fire", [])
	for pass_ in 2:
		for i in pts.size():
			var p: Array = pts[i]
			var x := float(p[0])
			var side := x > 556.0 or x < 92.0
			if side != (pass_ == 1):
				continue
			var s := _f4_stage(t - _lit_time(x), int(p[2]) if p.size() > 2 else 0)
			if s != "":
				PF.flame(_f4fire, s, Vector2(x, float(p[1]) if side else WALL_Y), t, i, rate)
		if pass_ == 0:
			PF.wall(_f4fire, ["wall_a", "wall_b"], 0.0, 640.0, WALL_Y, t, {"rate": rate, "shift": 37,
				"front": roundf(_front(t) + WALL_LAG), "ramp": WALL_RAMP, "side": 1.0})


## f4: the fire's light on the cabinets and the vault around the tallest flames (additive pools that breathe,
## under the flames so these stay pure palette)
func _draw_f4_heat() -> void:
	if not f4.visible:
		return
	var pts: Array = layout.get("f4_fire", [])
	for i in pts.size():
		var p: Array = pts[i]
		var kind := int(p[2]) if p.size() > 2 else 0
		var age := t - _lit_time(float(p[0]))
		if kind > 1 or age < 0.35:
			continue
		PF.light(_f4heat, "glow_l" if age >= 0.6 else "glow_m", Vector2(float(p[0]), 150.0 if kind == 1 else 176.0),
			t, i, fire_rate())


## f4: the smoke under the vault runs ahead of the fire -- a rolling head of big puffs, behind it a veil, then
## the bank (the veil is the bank's own billows with dither holes, so the two join)
func _draw_f4_bank() -> void:
	if f4.visible and _front(t) - SMOKE_LEAD < 700.0:
		smoke_front(_f4bank, _front(t) - SMOKE_LEAD, -1.0, BANK_Y, t)


func _draw_f4_fx() -> void:
	if not f4.visible:
		return
	var k := motion_k()
	var fr := _front(t)
	# puffs climb from the burning cabinets into the bank; the big ones roll on toward the camera
	for i in 7:
		var x := 612.0 - i * 92.0
		PF.plume(_f4fx, {"sheets": ["puff_m", "puff_l", "puff_m"], "from": Vector2(x, 142), "spread": Vector2(38, 12),
			"count": 6, "life": 2.0, "rise": 40.0, "slow": 1.0, "drift": Vector2(-10, 0), "t0": _lit_time(x) + 0.4,
			"seed": 61 + i * 7, "rate": k}, t)
	PF.plume(_f4fx, {"sheets": ["puff_xl", "puff_l"], "from": Vector2(400, BANK_Y), "spread": Vector2(210, 6), "count": 4,
		"life": 3.0, "rise": -6.0, "drift": Vector2(-18, 0), "t0": 9.6, "seed": 67, "rate": k}, t)
	# sparks rise from the fire line on arcs and cool
	for i in 4:
		var x0 := 480.0 - i * 160.0
		PF.sparks(_f4fx, {"rect": Rect2(x0, 150, 160, 70), "count": 9, "life": 1.7, "rise": 76.0, "kick": 14.0,
			"wind": -8.0, "gravity": 22.0, "t0": _lit_time(x0 + 160.0) + 0.2, "seed": 71 + i * 5, "rate": k}, t)
	# burning paper lifting off the drawers, tumbling up; it burns out as a last glowing scrap
	if _paper:
		for i in 12:
			var px := 640.0 - fposmod(i * 61.0, 650.0)
			if px < fr:
				continue
			var age := fposmod(t * 0.5 + i * 0.21, 2.2)
			var p := Vector2(px + sin(age * 3.0 + i) * 10.0, 220.0 - age * 70.0 * k)
			if age < 1.7:
				draw_frame(_f4fx, _paper, 6, int(floor(t * 8.0 + i)) % 6, p)
			else:
				_f4fx.draw_rect(Rect2(p.floor() - Vector2(1, 2), Vector2(2, 1)), PF.SPARK[4 if age < 1.95 else 5])
