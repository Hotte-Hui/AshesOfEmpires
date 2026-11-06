extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## LS_C3_Close (~12 s) — the night after the palais (C3_DESIGN §2.9).  Quiet, ominous, no spectacle.
##   n1 0-6 s   platform 5, 23:40: the special train with dark windows pulls away without a whistle; its red
##              tail lamps recede under the canopy lamps into the snow; the split-flap indicator clears its
##              row as if the train had never been listed
##   n2 6-12 s  the station square: two hotel façades, one lit window each, far apart; Konrad and Alexei
##              step to their windows; one distant whistle (the same as in Karsk); both turn toward it
## Subtitles: cin.c3.close.train, cin.c3.close.after.  Art: assets/cinematics/ch3/close/.
## The departing train is drawn at runtime in the same pinhole projection the generator used for the
## platform (PROJ == LAYOUT['close']['proj']), as plain 1 px polygons -> it shrinks without scaled sprites.

const FX := preload("res://scenes/cinematics/ch3_common/pixel_fx.gd")
const DISSOLVE := preload("res://scenes/cinematics/ch3_common/c3_dissolve.gdshader")

const DUR := 12.0
const N2 := 6.0
const SHOTS := [["n1", 0.0, 6.0], ["n2", 6.0, 12.0]]
const LINE_TRAIN := "cin.c3.close.train"
const LINE_AFTER := "cin.c3.close.after"
## pinhole camera on platform 5 (metres; x right, y up, z forward) -> world px
const PROJ := {"vpx": 236.0, "vpy": 168.0, "f": 420.0, "eye": 1.7}
const TRAIN_X := [1.45, 4.35]          # left (visible) side and right side of the car body
const TRAIN_Y := [-0.75, 3.3]          # underframe .. roof
const CAR_LEN := 26.4
const CAR_GAP := 0.8
const LAMPS_Z := [6.0, 16.0, 26.0, 36.0, 46.0, 56.0]
const BOARD_FLIP := [4.45, 4.95]

var n1: Node2D
var n2: Node2D
var _n2_mat: ShaderMaterial
var _train: Node2D
var _steam: Node2D
var _steam_tex: Texture2D
var _board: Sprite2D
var _snow1: Node2D
var _snow2: Node2D
var _win_k: Sprite2D
var _win_a: Sprite2D
var _lamp_glow: Sprite2D
var _life: Node2D
var _layout: Dictionary = {}


func _init() -> void:
	duration = DUR
	max_duration = DUR + 3.0


func chosen_lines() -> Array:
	return [LINE_TRAIN, LINE_AFTER]


func get_shot_id() -> String:
	return "n1" if t < N2 else "n2"


func _make_cues() -> Array:
	return [
		{"t": 0.0, "music": "", "fade": 2.5},
		{"t": 0.0, "amb": "amb_transition", "fade": 1.5},
		{"t": 0.05, "bed": "c3cine_depart_night", "db": -2.0},             # no whistle: it simply leaves
		{"t": 0.8, "say": LINE_TRAIN, "dur": 4.8},
		{"t": 1.3, "sfx": "wind_gust", "db": -16.0},
		{"t": BOARD_FLIP[0] - 0.05, "sfx": "c3cine_flaps", "db": -4.0, "pv": 0.03},  # the row clears
		{"t": 8.4, "bed": "cine_a1m1_whistle_far", "db": -4.0},            # one whistle: the one from Karsk
		{"t": 9.0, "say": LINE_AFTER, "dur": 3.0},
		{"t": 10.2, "sfx": "wind_gust", "db": -18.0},
	]


func _build() -> void:
	var p := ASSETS + "layout.json"
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			_layout = d.get("close", {})
	n1 = group("Platform5")
	sprite("close/n1_bg.png", Vector2.ZERO, n1)
	_train = Node2D.new()
	_train.name = "Train"
	_train.draw.connect(_draw_train)
	n1.add_child(_train)
	sprite("close/n1_mid.png", Vector2.ZERO, n1)      # canopy columns / lamp posts in front of the track
	_steam_tex = tex("close/steam.png")
	_steam = Node2D.new()
	_steam.name = "Steam"
	_steam.draw.connect(_draw_steam)
	n1.add_child(_steam)
	_snow1 = FX.new()
	_snow1.name = "Snow"
	n1.add_child(_snow1)
	var k := 0.6 if reduced_motion() else 1.0
	_snow1.setup_snow(Rect2(250, 0, 390, 300), [
		{"count": int(60 * k), "v": Vector2(-4, 18), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#687789"), "sway": 2.0},
		{"count": int(22 * k), "v": Vector2(-6, 34), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#c2c9d2"), "sway": 3.0}], 5101)
	sprite("close/n1_fg.png", Vector2.ZERO, n1)
	_board = sprite("close/board.png", Vector2.ZERO, n1, 1, false, 4)
	var bp = _layout.get("board")
	if bp is Array and bp.size() >= 2:
		_board.position = Vector2(float(bp[0]), float(bp[1]))
	n2 = group("Square")
	_n2_mat = ShaderMaterial.new()
	_n2_mat.shader = DISSOLVE
	n2.material = _n2_mat
	sprite("close/n2_bg.png", Vector2.ZERO, n2)
	_win_k = sprite("close/n2_win_konrad.png", Vector2.ZERO, n2, 3)
	_win_a = sprite("close/n2_win_alexei.png", Vector2.ZERO, n2, 3)
	for pair in [[_win_k, "win_konrad"], [_win_a, "win_alexei"]]:
		var v = _layout.get(pair[1])
		if v is Array and v.size() >= 2:
			(pair[0] as Sprite2D).position = Vector2(float(v[0]), float(v[1]))
	_lamp_glow = sprite("close/n2_lamp_glow.png", Vector2.ZERO, n2, 1, true)
	_life = Node2D.new()
	_life.name = "Life"
	_life.draw.connect(_draw_life)
	n2.add_child(_life)
	_snow2 = FX.new()
	_snow2.name = "Snow"
	n2.add_child(_snow2)
	_snow2.setup_snow(Rect2(0, 0, 640, 360), [
		{"count": int(90 * k), "v": Vector2(5, 14), "vjit": 0.35, "size": Vector2(1, 1), "color": Color("#4f5e70"), "sway": 2.5},
		{"count": int(40 * k), "v": Vector2(8, 26), "vjit": 0.3, "size": Vector2(1, 1), "color": Color("#a1aab7"), "sway": 3.0},
		{"count": int(12 * k), "v": Vector2(10, 40), "vjit": 0.3, "size": Vector2(2, 2), "color": Color("#dee2e7"), "sway": 4.0}], 5102)
	for c in n2.get_children():
		if c != _lamp_glow:
			(c as CanvasItem).use_parent_material = true


func _apply(time: float) -> void:
	if n1 == null:
		return
	var rm := reduced_motion()
	var d0 := 5.5 if rm else 5.7
	var d1 := 6.6 if rm else 6.3
	var prog := clampf((time - d0) / (d1 - d0), 0.0, 1.0)
	n1.visible = prog < 1.0
	n2.visible = prog > 0.0
	_n2_mat.set_shader_parameter("progress", prog)
	_lamp_glow.visible = prog >= 1.0
	_train.queue_redraw()
	_steam.queue_redraw()
	_snow1.set_time(time * (0.6 if rm else 1.0))
	_snow2.set_time(time * (0.6 if rm else 1.0))
	_life.queue_redraw()
	# split-flap board: two flap frames, then the cleared row (one clean change with reduced motion)
	if _board.texture:
		var f := 0
		if time >= BOARD_FLIP[1]:
			f = 3
		elif time >= BOARD_FLIP[0] and not rm:
			f = 1 + int(floor((time - BOARD_FLIP[0]) / 0.12)) % 2
		_board.frame = f
	# n2: Konrad steps to his window, then Alexei; the whistle; both turn toward it
	_win_k.frame = 0 if time < 6.9 else (1 if time < 8.75 else 2)
	_win_a.frame = 0 if time < 7.45 else (1 if time < 9.05 else 2)
	_lamp_glow.modulate = Color(1, 1, 1, 0.92 + 0.05 * hnoise(time * 2.1, 3) * (0.4 if rm else 1.0))


# ------------------------------------------------------------------ the departing train
func train_rear_z(time: float) -> float:
	var k := 0.75 if reduced_motion() else 1.0
	return 12.0 + (1.4 * time + 1.75 * time * time) * k


func _proj(x: float, y: float, z: float) -> Vector2:
	var zz := maxf(z, 0.3)
	return Vector2(PROJ["vpx"] + PROJ["f"] * x / zz, PROJ["vpy"] - PROJ["f"] * (y - PROJ["eye"]) / zz)


func _quad(x: float, y0: float, y1: float, z0: float, z1: float) -> PackedVector2Array:
	return PackedVector2Array([_proj(x, y0, z0).round(), _proj(x, y1, z0).round(), _proj(x, y1, z1).round(),
		_proj(x, y0, z1).round()])


func _lamp_light(z: float) -> float:
	var best := 0.0
	for lz in LAMPS_Z:
		best = maxf(best, clampf(1.0 - absf(z - lz) / 4.5, 0.0, 1.0))
	return best


func _draw_train() -> void:
	if t >= N2:
		return
	var zr := train_rear_z(t)
	if zr > 900.0:
		return
	var xl: float = TRAIN_X[0]
	var xr: float = TRAIN_X[1]
	var yb: float = TRAIN_Y[0]
	var yt: float = TRAIN_Y[1]
	var zf := zr + 6.0 * (CAR_LEN + CAR_GAP)
	var body := Color("#0c111c")
	var dark := Color("#070a12")
	# visible side of all cars (one dark band receding to the vanishing point)
	_train.draw_colored_polygon(_quad(xl, yb, yt, zr, zf), body)
	# underframe + bogies (darker), roof edge catching the canopy lamps
	_train.draw_colored_polygon(_quad(xl, yb, yb + 0.55, zr, zf), dark)
	for c in 6:
		var z0 := zr + c * (CAR_LEN + CAR_GAP)
		var z1 := z0 + CAR_LEN
		# car gap (bellows)
		_train.draw_colored_polygon(_quad(xl + 0.15, yb + 0.4, yt - 0.25, z1, z1 + CAR_GAP), dark)
		# bogies
		for bz in [z0 + 3.0, z1 - 3.0]:
			_train.draw_colored_polygon(_quad(xl + 0.05, yb - 0.25, yb + 0.45, bz - 1.3, bz + 1.3), Color("#121a26"))
		# windows: the courier wagon (c == 1) has none -> a sealed van in the middle of the train
		if c != 1:
			var wz := z0 + 1.7
			while wz + 1.2 < z1 - 1.0:
				var li := _lamp_light(wz + 0.6)
				var frame_col := Color("#1a2431").lerp(Color("#4f5e70"), li)
				_train.draw_colored_polygon(_quad(xl, 1.0, 1.95, wz, wz + 1.2), frame_col)
				_train.draw_colored_polygon(_quad(xl, 1.08, 1.87, wz + 0.08, wz + 1.12), Color("#070a12") if li < 0.6 else Color("#121a26"))
				wz += 2.2
		else:
			# lead seal plate and the brass frame of the weighing ticket, catching a lamp
			var li := _lamp_light(z0 + 13.0)
			_train.draw_colored_polygon(_quad(xl, 0.9, 1.4, z0 + 12.4, z0 + 13.6), Color("#22262d").lerp(Color("#9c7630"), li))
		# roof edge highlight where a lamp is near
		var hz := z0
		while hz < z1:
			var li := _lamp_light(hz)
			if li > 0.05:
				var a := _proj(xl, yt, hz).round()
				var b := _proj(xl, yt, hz + 0.7).round()
				FX.line(_train, a, b, Color("#2a3646").lerp(Color("#8593a3"), li))
			hz += 0.7
	# rear face of the last car (rounded roof), gangway door, buffers, tail lamps
	var rf := PackedVector2Array()
	for p in [[xl, yb], [xl, yt - 0.35], [xl + 0.4, yt - 0.05], [(xl + xr) * 0.5, yt + 0.12],
			[xr - 0.4, yt - 0.05], [xr, yt - 0.35], [xr, yb]]:
		rf.append(_proj(p[0], p[1], zr).round())
	_train.draw_colored_polygon(rf, dark)
	var cx := (xl + xr) * 0.5
	var door := _quad_face(cx - 0.45, cx + 0.45, 0.15, 2.4, zr)
	_train.draw_polyline(door, Color("#1a2431"), 1.0)
	# lit left edge of the rear face (platform lamps)
	FX.line(_train, _proj(xl, yb + 0.3, zr), _proj(xl, yt - 0.4, zr), Color("#2a3646"))
	for bx in [xl + 0.55, xr - 0.55]:
		var bp := _proj(bx, 0.05, zr - 0.25).round()
		var r := maxf(1.0, PROJ["f"] * 0.22 / zr)
		_train.draw_rect(Rect2(bp - Vector2(r, r * 0.6), Vector2(r * 2.0, r * 1.2)), Color("#15171c"))
	for lx in [xl + 0.5, xr - 0.5]:
		_tail_lamp(_proj(lx, 0.55, zr).round(), zr)
	# red light reflected along the rails behind the train
	for rx in [2.18, 3.62]:
		var p0 := _proj(rx, -1.0, maxf(2.6, zr - 9.0))
		var p1 := _proj(rx, -1.0, zr - 0.4)
		FX.line(_train, p0, p1, Color("#4a1712"))


func _quad_face(x0: float, x1: float, y0: float, y1: float, z: float) -> PackedVector2Array:
	return PackedVector2Array([_proj(x0, y0, z).round(), _proj(x0, y1, z).round(), _proj(x1, y1, z).round(),
		_proj(x1, y0, z).round(), _proj(x0, y0, z).round()])


func _tail_lamp(p: Vector2, z: float) -> void:
	var r := clampf(PROJ["f"] * 0.11 / z, 0.0, 4.0)
	var glow := int(clampf(PROJ["f"] * 0.5 / z, 1.0, 9.0))
	# dithered halo (whole pixels), then the core
	for dy in range(-glow, glow + 1):
		for dx in range(-glow, glow + 1):
			var d := sqrt(float(dx * dx + dy * dy)) / float(glow)
			if d <= 1.0 and ((dx + dy) & 1) == 0 and d > 0.35:
				_train.draw_rect(Rect2(p + Vector2(dx, dy), Vector2.ONE), Color("#4a1712"))
	_train.draw_rect(Rect2(p - Vector2(floorf(r), floorf(r)), Vector2(floorf(r) * 2.0 + 1.0, floorf(r) * 2.0 + 1.0)), Color("#c8503c"))
	if r >= 1.5:
		_train.draw_rect(Rect2(p, Vector2.ONE), Color("#f0c487"))


func _draw_steam() -> void:
	if _steam_tex == null or t >= N2 + 0.5:
		return
	var n := int(_layout.get("steam_frames", 4))
	var fw := _steam_tex.get_width() / n
	var fh := _steam_tex.get_height()
	var sp := 0.5 if reduced_motion() else 1.0
	var puffs := [[300.0, 62.0, 0, 0.0], [380.0, 96.0, 1, 0.3], [250.0, 104.0, 2, 0.6], [440.0, 70.0, 3, 0.2]]
	for pf in puffs:
		var age: float = t + float(pf[3])
		var x: float = float(pf[0]) - age * 9.0 * sp
		var y: float = float(pf[1]) - age * 2.0 * sp
		var fi := clampi(int(pf[2]) + int(age / 2.2), 0, n - 1)
		_steam.draw_texture_rect_region(_steam_tex, Rect2(Vector2(roundf(x), roundf(y)), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh))


## n2: the parked car under the trees with a cigarette glowing behind the windscreen (one pixel, slow)
func _draw_life() -> void:
	if t < N2 - 0.4:
		return
	var ember = _layout.get("ember")
	if ember is Array and ember.size() >= 2:
		var glow := 0.5 + 0.5 * sin((t - N2) * 1.3)
		var col := Color("#a8643a").lerp(Color("#edb777"), glow)
		_life.draw_rect(Rect2(float(ember[0]), float(ember[1]), 1, 1), col)
