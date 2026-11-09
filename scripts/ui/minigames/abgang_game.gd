extends "res://scripts/ui/minigames/minigame_base.gd"
## Annex mini-game „Planspiel Abgang“ (scenes/ui/minigames/PlanspielAbgang.tscn, explore entry
## berlin.annex.planspiel, last step of the side task of the same name at the data desk of Nebenstelle Süd,
## L_C4_Annex scene D; §12.8). The program Kommissar Wendt had loaded on tape 7: the State Police's own simulation of
## an arrest in the Süd-8 quarter, „Lage 3“ — a child, alone, who knows the houses. Eleven runs are in the operator's
## log, eleven arrests. Konrad plays run twelve and runs for the child: three short maps (the street at the tram
## loop, the courtyard, the stairwell and attic) past the posts of „Schema B“ to the gap in the net — the 1941
## air-raid breach in the fire wall that the machine knows from the building office's own plans and no post guards.
## No one is harmed and nothing is won but the way: the chill is playing the hunted inside the hunters' machine.
##
## Rule: abgang_logic.gd (grid steps, posts „im Takt“, sight beams, restart of the map when seen, a solver).
## Picture: REAL 3D — a Camera3D in a 400x150 SubViewport with its own world draws the map as lines only (walls as
## wire boxes, stairs, rafters; the posts, their beams and the figure rebuilt every frame in an ImmediateMesh), the
## head-up text is lettered into the same viewport, and crt_kit.gd's phosphor shader maps every art pixel to a
## palette step (green beam = the place and the figure, amber beam = the posts and what they see) with a one-pixel
## halo; shown x3 on the 640x360 grid. Reduced motion: no camera drift, no fly-in, no blinking. High contrast: black
## glass, brighter steps. Larger text: the flavour lines give way, the picture keeps its size.
## Hints (Settings `puzzle_hints`): after two arrests on a map a tip for that map, after the third the display
## draws a trace of the next safe way (dim = wait, bright = go).
## Sounds (tools/audiogen/mg_audio_terminal.py): mg_term_hum (loop), mg_term_relay (the beat), mg_abgang_step,
## mg_abgang_seen, mg_abgang_through, mg_abgang_print.
## Keys: arrows / WASD / d-pad / left stick walk (held = keep walking) · R or pad Y starts the map again · Esc gives
## up. Mouse: hold the button on the display — the figure walks toward the pointer.

const Logic := preload("res://scripts/ui/minigames/abgang_logic.gd")
const Crt := preload("res://scripts/ui/minigames/crt_kit.gd")
## The picture in art pixels: taller while the flavour texts stand beside the tube, the classic strip for larger text.
const ART := Vector2i(384, 172)
const ART_COMPACT := Vector2i(384, 150)
const SIDE_W := 430
const SND := "res://assets/audio/sfx/"
const FOV := 30.0
const PITCH := 50.0
## The camera tilts as flat as this when a flatter look shows the map larger in the wide glass.
const PITCHES := [50.0, 46.0, 42.0, 38.0]
const DIR_KEYS := [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_LEFT]
const SEEN_HOLD := 1.3
const NEXT_HOLD := 1.0
const INTRO_HOLD := 0.7
## The posts of „Postenschema B“ per map (the numbers the status line names).
const POST_NUMBER := [[1, 2], [3, 4], [5, 6]]

var logic = Logic.new()
var S := 3
var compact := false
var art := ART
var map_fails := 0
var trace_on := false
var _stage: Control
var _tube: TextureRect
var _vp: SubViewport
var _cam: Camera3D
var _cam_xf := Transform3D.IDENTITY
var _static_mi: MeshInstance3D
var _dyn_mi: MeshInstance3D
var _dyn: ImmediateMesh
var _mat: ShaderMaterial
var _hud: Node2D
var _sv := PackedVector3Array()
var _sc := PackedColorArray()
var _seen_keys := {}
var _acc := 0.0
var _hold := 0.0
var _hold_kind := ""
var _held := {}
var _held_order: Array = []
var _t := 0.0
var _hum: AudioStreamPlayer
var _last_beat := -1
var _trail: Array = []
var _centre := Vector3.ZERO
var _dist := 14.0
var _pitch := PITCH
var _lamp := 1
var _mouse_down := false


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_stage", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("stage_input", event)


class Hud extends Node2D:
	var game: Node

	func _draw() -> void:
		game.call("draw_hud", self)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.abgang.kicker", "mg.abgang.title", "mg.abgang.subtitle", "mg.abgang.instruction")
	compact = Kit.text_scale() > 1.01
	art = ART_COMPACT if compact else ART
	if compact:
		_subtitle.visible = false
		_instr.visible = false
	var row := Kit.hbox(36)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var v := View.new()
	v.game = self
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.custom_minimum_size = Crt.housing_size(art, S)
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	row.add_child(v)
	_stage = v
	area.custom_minimum_size.y = v.custom_minimum_size.y
	# the 3D picture: its own world, lines only, no smoothing of any kind
	_vp = SubViewport.new()
	_vp.size = art
	_vp.own_world_3d = true
	_vp.transparent_bg = false
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_vp.msaa_3d = Viewport.MSAA_DISABLED
	_vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	_vp.use_taa = false
	_vp.use_debanding = false
	_vp.gui_disable_input = true
	_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	v.add_child(_vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color.BLACK
	env.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	_cam = Camera3D.new()
	_cam.fov = FOV
	_cam.near = 0.2
	_cam.far = 120.0
	_vp.add_child(_cam)
	_cam.current = true
	_mat = Crt.line_material()
	_static_mi = MeshInstance3D.new()
	_static_mi.material_override = _mat
	_vp.add_child(_static_mi)
	_dyn = ImmediateMesh.new()
	_dyn_mi = MeshInstance3D.new()
	_dyn_mi.mesh = _dyn
	_dyn_mi.material_override = _mat
	_vp.add_child(_dyn_mi)
	var hud := Hud.new()
	hud.game = self
	_vp.add_child(hud)
	_hud = hud
	_tube = TextureRect.new()
	_tube.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_tube.stretch_mode = TextureRect.STRETCH_SCALE
	_tube.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tube.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var r := Crt.tube_rect(art, S)
	_tube.position = r.position
	_tube.size = r.size
	_tube.material = Crt.tube_material(art, Kit.high_contrast())
	_tube.texture = _vp.get_texture()
	v.add_child(_tube)
	if not compact:      # the flavour and the instruction stand beside the tube, so the picture can be taller
		var side := Kit.vbox(18)
		side.custom_minimum_size.x = SIDE_W
		side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		for l in [_subtitle, _instr]:
			l.get_parent().remove_child(l)
			side.add_child(l)
		row.add_child(side)
	_hum = _loop_player(SND + "mg_term_hum.wav")


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_load_map(0)
	set_status(Kit.t("mg.abgang.status.start"))
	_status_hold = 2.2
	if not bool(ctx.get("auto", false)) and _hum != null and _hum.stream != null:
		_hum.volume_db = -26.0
		_hum.play()


func _on_end() -> void:
	if _hum != null:
		_hum.stop()
	_held.clear()
	_held_order.clear()


## Back to the first map.
func _reset_game() -> void:
	_load_map(0)


func _load_map(i: int) -> void:
	logic.load_map(i)
	map_fails = 0
	trace_on = false
	_trail.clear()
	_last_beat = -1
	_acc = 0.0
	if _hint_box != null:
		_hint_box.visible = false
		hint_level = 0
		if is_open and int(Kit.setting("puzzle_hints", 1)) == 2:
			show_hint(1)
	_build_static()
	_fit_camera()
	_hold = 0.2 if Kit.reduced_motion() else INTRO_HOLD
	_hold_kind = "intro"
	logic.want = _wanted()
	_render()


## R: the same map from beat 0 (no arrest counted).
func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_drop_holds()
	logic.reset()
	_trail.clear()
	_last_beat = -1
	_hold = 0.0
	_hold_kind = ""
	set_status(Kit.t("mg.abgang.status.restart"))
	_status_hold = 1.6


func map_name() -> String:
	return Kit.t("mg.abgang.map." + str(logic.id))


# ================================================================ hints
func _hint_text(level: int) -> String:
	if level >= 2:
		return Kit.t("mg.abgang.hint.trace")
	return Kit.t("mg.abgang.hint." + str(logic.id))


func show_hint(level: int) -> void:
	super.show_hint(level)
	trace_on = level >= 2


## Settings "puzzle_hints": 0 never, 1 after two arrests on this map (default; the third draws the trace), 2 the
## map's tip at once and the trace after the first arrest.
func register_fail(text: String) -> void:
	fails += 1
	map_fails += 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	var mode := int(Kit.setting("puzzle_hints", 1))
	if mode == 1 and map_fails >= HINT_AFTER:
		show_hint(map_fails - HINT_AFTER + 1)
	elif mode == 2:
		show_hint(map_fails + 1)


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN) + "|" + Kit.key_name(KEY_RIGHT),
			Kit.t("mg.abgang.ctrl.move")],
		["R", Kit.t("mg.abgang.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_t += delta
	if not solved:
		if _hold > 0.0:
			_hold -= delta
			if _hold <= 0.0:
				_end_hold()
		else:
			_acc = minf(_acc + delta, 0.3)
			while _acc >= Logic.TICK and _hold <= 0.0 and not solved:
				_acc -= Logic.TICK
				_on_event(logic.step())
				var b: int = logic.tick / Logic.BEAT_TICKS
				if b != _last_beat:
					_last_beat = b
					if not bool(ctx.get("auto", false)):
						_sfx("mg_term_relay", -24.0)
		if not solved and _hold <= 0.0:
			status_auto(Kit.t("mg.abgang.status.map", {"n": int(logic.index) + 1, "name": map_name(),
				"goal": Kit.t("mg.abgang.goal." + str(logic.id))}))
	_render()


func _on_event(ev: String) -> void:
	match ev:
		"moved":
			_sfx("mg_abgang_step", -16.0)
			_trail.append(logic.from_cell)
			if _trail.size() > 3:
				_trail.pop_front()
		"seen":
			_sfx("mg_abgang_seen", -4.0)
			var nr: int = POST_NUMBER[int(logic.index)][clampi(int(logic.caught_by), 0, 1)]
			register_fail(Kit.t("mg.abgang.status.seen", {"p": nr}))
			_hold = SEEN_HOLD
			_hold_kind = "seen"
		"exit":
			if int(logic.index) < Logic.map_count() - 1:
				_sfx("mg_abgang_through", -6.0)
				set_status(Kit.t("mg.abgang.status.through"))
				_status_hold = NEXT_HOLD
				_hold = NEXT_HOLD
				_hold_kind = "next"
			else:
				_sfx("mg_abgang_print", -5.0)
				mark_solved(Kit.t("mg.abgang.solved"))


func _end_hold() -> void:
	var kind := _hold_kind
	_hold = 0.0
	_hold_kind = ""
	match kind:
		"seen":
			_drop_holds()
			logic.reset()
			_trail.clear()
			_last_beat = -1
		"next":
			_drop_holds()
			_load_map(int(logic.index) + 1)


# ================================================================ input
func _wanted() -> int:
	return int(_held[_held_order[_held_order.size() - 1]]) if not _held_order.is_empty() else -1


## A new map or a new attempt starts standing: a direction still held from before counts only when pressed again.
func _drop_holds() -> void:
	_held.clear()
	_held_order.clear()
	_mouse_down = false
	logic.want = -1


func _set_dir(src: String, dir: int, down: bool) -> void:
	_held_order.erase(src)
	if down:
		_held[src] = dir
		_held_order.append(src)
	else:
		_held.erase(src)
	logic.want = _wanted()


func _game_input(event: InputEvent) -> bool:
	if event is InputEventKey:
		var ke := event as InputEventKey
		var code := int(ke.physical_keycode) if ke.physical_keycode != 0 else int(ke.keycode)
		if ke.echo:
			return true
		match code:
			KEY_UP, KEY_W:
				_set_dir("k0", 0, ke.pressed)
				return true
			KEY_RIGHT, KEY_D:
				_set_dir("k1", 1, ke.pressed)
				return true
			KEY_DOWN, KEY_S:
				_set_dir("k2", 2, ke.pressed)
				return true
			KEY_LEFT, KEY_A:
				_set_dir("k3", 3, ke.pressed)
				return true
		if ke.pressed and code == KEY_R:
			restart()
			return true
		return false
	if event is InputEventJoypadButton:
		var jb := event as InputEventJoypadButton
		match jb.button_index:
			JOY_BUTTON_DPAD_UP:
				_set_dir("p0", 0, jb.pressed)
				return true
			JOY_BUTTON_DPAD_RIGHT:
				_set_dir("p1", 1, jb.pressed)
				return true
			JOY_BUTTON_DPAD_DOWN:
				_set_dir("p2", 2, jb.pressed)
				return true
			JOY_BUTTON_DPAD_LEFT:
				_set_dir("p3", 3, jb.pressed)
				return true
			JOY_BUTTON_Y:
				if jb.pressed:
					restart()
				return true
		return false
	if event is InputEventJoypadMotion:
		var jm := event as InputEventJoypadMotion
		if jm.axis == JOY_AXIS_LEFT_X:
			_set_dir("sx", 1 if jm.axis_value > 0.0 else 3, absf(jm.axis_value) > 0.55)
			return true
		if jm.axis == JOY_AXIS_LEFT_Y:
			_set_dir("sy", 2 if jm.axis_value > 0.0 else 0, absf(jm.axis_value) > 0.55)
			return true
	return false


## The direction from the figure toward a point of the stage (screen px), -1 on the figure itself.
func dir_toward(p: Vector2) -> int:
	var r := Crt.tube_rect(art, S)
	var at := (p - r.position) / float(S)
	var me := project(cell_pos(logic.cell, 0.0))
	var d := at - me
	if d.length() < 5.0:
		return -1
	if absf(d.x) > absf(d.y) * 1.6:
		return 1 if d.x > 0.0 else 3
	return 2 if d.y > 0.0 else 0


func stage_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		_mouse_down = (event as InputEventMouseButton).pressed
		var d := dir_toward((event as InputEventMouseButton).position)
		_set_dir("mouse", maxi(d, 0), _mouse_down and d >= 0)
	elif event is InputEventMouseMotion and _mouse_down:
		var d2 := dir_toward((event as InputEventMouseMotion).position)
		_set_dir("mouse", maxi(d2, 0), d2 >= 0)


# ================================================================ world (lines only)
## World position of a cell's middle at `up` above its floor.
func cell_pos(c: Vector2i, up := 0.0) -> Vector3:
	return Vector3(float(c.x) + 0.5, float(logic.lift_at(c)) * Logic.LIFT + up, float(c.y) + 0.5)


func _seg(a: Vector3, b: Vector3, lv: int) -> void:
	var key := "%d_%d_%d_%d_%d_%d" % [roundi(a.x * 50.0), roundi(a.y * 50.0), roundi(a.z * 50.0),
		roundi(b.x * 50.0), roundi(b.y * 50.0), roundi(b.z * 50.0)]
	if _seen_keys.has(key):
		return
	_seen_keys[key] = true
	var col := Crt.beam(lv)
	_sv.append(a)
	_sv.append(b)
	_sc.append(col)
	_sc.append(col)


func _build_static() -> void:
	_sv = PackedVector3Array()
	_sc = PackedColorArray()
	_seen_keys = {}
	var corner := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
	# the two corners of the edge toward N, E, S, W (indices into `corner`)
	var edge := [[0, 1], [1, 2], [2, 3], [3, 0]]
	for y in int(logic.h):
		for x in int(logic.w):
			var c := Vector2i(x, y)
			var ch: String = logic.char_at(c)
			if not logic.walkable(c):
				if "octL".contains(ch):          # free-standing cover: close its top
					var top: float = float(Logic.HEIGHT[ch]) + _base_of(c)
					for k in 4:
						var p0: Vector2 = corner[k]
						var p1: Vector2 = corner[(k + 1) % 4]
						_seg(Vector3(x + p0.x, top, y + p0.y), Vector3(x + p1.x, top, y + p1.y), 2)
				continue
			var fy: float = float(logic.lift_at(c)) * Logic.LIFT
			var stair := false
			for d in 4:
				var n: Vector2i = c + Logic.DIRS[d]
				var a: Vector2 = corner[edge[d][0]]
				var b: Vector2 = corner[edge[d][1]]
				var pa := Vector3(x + a.x, fy, y + a.y)
				var pb := Vector3(x + b.x, fy, y + b.y)
				if logic.walkable(n):
					var ny: float = float(logic.lift_at(n)) * Logic.LIFT
					if not is_equal_approx(ny, fy):
						stair = true
						_seg(pa, pb, 2)
						_seg(pa, Vector3(pa.x, ny, pa.z), 1)
						_seg(pb, Vector3(pb.x, ny, pb.z), 1)
					continue
				var hgt := 0.0
				if logic.inside(n):
					hgt = float(Logic.HEIGHT.get(logic.char_at(n), 1.0))
					if int(logic.lift_at(c)) >= 4 and logic.char_at(n) == "#":
						hgt = 0.45                # under the roof the walls are knee-high
				_seg(pa, pb, 1)
				if hgt > 0.0:
					_seg(Vector3(pa.x, fy + hgt, pa.z), Vector3(pb.x, fy + hgt, pb.z), 2)
					_seg(pa, Vector3(pa.x, fy + hgt, pa.z), 1)
					_seg(pb, Vector3(pb.x, fy + hgt, pb.z), 1)
					var storey := 1.0
					while storey < hgt - 0.3:
						_seg(Vector3(pa.x, fy + storey, pa.z), Vector3(pb.x, fy + storey, pb.z), 1)
						storey += 1.0
			# floor: small crosses at the corners, a full outline on stairs
			for k in 4:
				var q: Vector2 = corner[k]
				var px := float(x) + q.x
				var pz := float(y) + q.y
				_seg(Vector3(px - 0.09, fy, pz), Vector3(px + 0.09, fy, pz), 1)
				_seg(Vector3(px, fy, pz - 0.09), Vector3(px, fy, pz + 0.09), 1)
				if stair:
					var q2: Vector2 = corner[(k + 1) % 4]
					_seg(Vector3(px, fy, pz), Vector3(float(x) + q2.x, fy, float(y) + q2.y), 1)
	for dl in Logic.MAPS[int(logic.index)].get("decor", []):
		_seg(Vector3(float(dl[0]), float(dl[1]), float(dl[2])), Vector3(float(dl[3]), float(dl[4]), float(dl[5])), int(dl[6]))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = _sv
	arr[Mesh.ARRAY_COLOR] = _sc
	var m := ArrayMesh.new()
	if _sv.size() >= 2:
		m.add_surface_from_arrays(Mesh.PRIMITIVE_LINES, arr)
	if _static_mi != null:
		_static_mi.mesh = m


## Floor height under a solid cell: the highest floor next to it it stands on (a chimney stands on the attic).
func _base_of(c: Vector2i) -> float:
	var best := 0
	for d in 4:
		var n: Vector2i = c + Logic.DIRS[d]
		if logic.walkable(n):
			best = maxi(best, int(logic.lift_at(n)))
	return float(best) * Logic.LIFT


func line_count() -> int:
	return _sv.size() / 2


static func _look(pos: Vector3, target: Vector3) -> Transform3D:
	return Transform3D(Basis.looking_at(target - pos, Vector3.UP), pos)


## Screen position (art px) of a world point through the current camera.
func project(p: Vector3) -> Vector2:
	var l := _cam_xf.affine_inverse() * p
	var f := 1.0 / tan(deg_to_rad(FOV) * 0.5)
	var z := maxf(0.05, -l.z)
	var nx := l.x * f / (float(art.x) / float(art.y)) / z
	var ny := l.y * f / z
	return Vector2((nx * 0.5 + 0.5) * float(art.x), (0.5 - ny * 0.5) * float(art.y))


## The camera looks north over the whole map from the south; its distance is the nearest that keeps every corner
## of the map (and its tallest wall) inside the glass.
func _fit_camera() -> void:
	var top := 0.0
	for y in int(logic.h):
		for x in int(logic.w):
			var c := Vector2i(x, y)
			if logic.walkable(c):
				top = maxf(top, float(logic.lift_at(c)) * Logic.LIFT + 1.2)
			else:
				top = maxf(top, minf(2.2, float(Logic.HEIGHT.get(logic.char_at(c), 1.0))))
	_centre = Vector3(float(logic.w) * 0.5, top * 0.3, float(logic.h) * 0.5)
	_dist = 60.0
	_pitch = PITCH
	for pitch in PITCHES:
		var el := deg_to_rad(float(pitch))
		var dirv := Vector3(0.0, sin(el), cos(el))
		for k in range(20, 180):
			var d := float(k) * 0.25
			if d >= _dist:
				break
			_cam_xf = _look(_centre + dirv * d, _centre)
			var ok := true
			for cx in [0.0, float(logic.w)]:
				for cz in [0.0, float(logic.h)]:
					for cy in [0.0, top]:
						var s := project(Vector3(cx, cy, cz))
						if s.x < 5.0 or s.x > float(art.x) - 5.0 or s.y < 12.0 or s.y > float(art.y) - 11.0:
							ok = false
			if ok:
				_dist = d
				_pitch = float(pitch)
				break
	_cam_xf = _camera_now()
	if _mat != null:
		_mat.set_shader_parameter("far_dim", _dist + float(logic.h) * 0.12)


func _camera_now() -> Transform3D:
	var el := deg_to_rad(_pitch)
	var yaw := 0.0
	var d := _dist
	if not Kit.reduced_motion():
		yaw = sin(_t * 0.45) * deg_to_rad(2.2)
		if _hold_kind == "intro" and _hold > 0.0:
			var k := clampf(_hold / INTRO_HOLD, 0.0, 1.0)
			yaw += k * k * deg_to_rad(-26.0)
			d = _dist * (1.0 + 0.35 * k * k)
	var dirv := Vector3(sin(yaw) * cos(el), sin(el), cos(yaw) * cos(el))
	return _look(_centre + dirv * d, _centre)


func _dl(a: Vector3, b: Vector3, col: Color) -> void:
	_dyn.surface_set_color(col)
	_dyn.surface_add_vertex(a)
	_dyn.surface_set_color(col)
	_dyn.surface_add_vertex(b)


func _square(c: Vector3, half: float, col: Color) -> void:
	var p := [Vector3(c.x - half, c.y, c.z - half), Vector3(c.x + half, c.y, c.z - half),
		Vector3(c.x + half, c.y, c.z + half), Vector3(c.x - half, c.y, c.z + half)]
	for k in 4:
		_dl(p[k], p[(k + 1) % 4], col)


## Where post `i` stands right now (it walks to its new cell during the first part of a beat).
func post_pos(i: int) -> Vector3:
	var b: int = logic.beat()
	var now: Array = logic.post_state(i, b)
	var to := cell_pos(Vector2i(int(now[0]), int(now[1])))
	if Kit.reduced_motion() or logic.tick < Logic.BEAT_TICKS:
		return to
	var before: Array = logic.post_state(i, b - 1)
	var from := cell_pos(Vector2i(int(before[0]), int(before[1])))
	return from.lerp(to, clampf(float(logic.beat_phase()) / 0.4, 0.0, 1.0))


func figure_pos() -> Vector3:
	var to := cell_pos(logic.cell)
	if Kit.reduced_motion():
		return to
	return cell_pos(logic.from_cell).lerp(to, float(logic.step_phase()))


func _render() -> void:
	if _dyn == null:
		return
	_cam_xf = _camera_now()
	if _cam != null:
		_cam.transform = _cam_xf
	var calm := Kit.reduced_motion()
	var blink := calm or fmod(_t, 0.5) < 0.32
	var g1 := Crt.beam(1)
	var g2 := Crt.beam(2)
	var g3 := Crt.beam(3)
	var a1 := Crt.beam(1, true)
	var a2 := Crt.beam(2, true)
	var a3 := Crt.beam(3, true)
	_dyn.clear_surfaces()
	_dyn.surface_begin(Mesh.PRIMITIVE_LINES)
	var b: int = logic.beat()
	# what the posts see: every seen cell a hatched square on the second beam
	for i in logic.patrols.size():
		var hot: bool = logic.caught and int(logic.caught_by) == i
		var col := a3 if hot else a2
		for c in logic.beams[b][i]:
			var p := cell_pos(c, 0.02)
			_square(p, 0.38, col)
			_dl(Vector3(p.x - 0.38, p.y, p.z + 0.38), Vector3(p.x + 0.38, p.y, p.z - 0.38), col)
		# the last third of a beat announces the next sight: small crosses where it will fall
		if float(logic.beat_phase()) > 0.6 and not logic.caught:
			for c2 in logic.beams[(b + 1) % int(logic.period)][i]:
				var q := cell_pos(c2, 0.02)
				_dl(Vector3(q.x - 0.14, q.y, q.z), Vector3(q.x + 0.14, q.y, q.z), a1)
				_dl(Vector3(q.x, q.y, q.z - 0.14), Vector3(q.x, q.y, q.z + 0.14), a1)
		# the post: an obelisk with a stroke for its facing
		var st: Array = logic.post_state(i, b)
		var pp := post_pos(i)
		var apex := pp + Vector3(0.0, 1.0, 0.0)
		var base := [pp + Vector3(-0.2, 0.0, -0.2), pp + Vector3(0.2, 0.0, -0.2), pp + Vector3(0.2, 0.0, 0.2), pp + Vector3(-0.2, 0.0, 0.2)]
		for k in 4:
			_dl(base[k], base[(k + 1) % 4], a3)
			_dl(base[k], apex, a3)
		var fwd: Vector2i = Logic.DIRS[int(st[2])]
		_dl(pp + Vector3(0.0, 0.55, 0.0), pp + Vector3(float(fwd.x) * 0.6, 0.55, float(fwd.y) * 0.6), a3)
	# the gap: a frame that blinks
	var gp := cell_pos(logic.goal, 0.02)
	var gcol := g3 if blink else g2
	_square(gp, 0.42, gcol)
	_square(gp + Vector3(0.0, 0.9, 0.0), 0.42, gcol)
	for sx in [-0.42, 0.42]:
		for sz in [-0.42, 0.42]:
			_dl(gp + Vector3(sx, 0.0, sz), gp + Vector3(sx, 0.9, sz), gcol)
	# the trace of the hint: dim while it is time to wait, bright when it is time to go
	if trace_on and not logic.caught and not logic.through and _hold <= 0.0:
		var tcol := g3 if int(logic.demo_action(1)) >= 0 else g1
		var prev := cell_pos(logic.cell, 0.05)
		for c3 in logic.trace(10, 1):
			var nx := cell_pos(c3, 0.05)
			_dl(prev.lerp(nx, 0.3), prev.lerp(nx, 0.7), tcol)
			prev = nx
	# where the figure has been
	for c4 in _trail:
		var tp := cell_pos(c4, 0.02)
		_dl(Vector3(tp.x - 0.08, tp.y, tp.z), Vector3(tp.x + 0.08, tp.y, tp.z), g1)
	# the figure: small, a child's height
	var fp := figure_pos()
	var danger: bool = logic.in_danger() or logic.caught
	if not (danger and not blink):
		var mid := fp + Vector3(0.0, 0.3, 0.0)
		var ring := [mid + Vector3(-0.17, 0.0, 0.0), mid + Vector3(0.0, 0.0, -0.17), mid + Vector3(0.17, 0.0, 0.0), mid + Vector3(0.0, 0.0, 0.17)]
		for k in 4:
			_dl(ring[k], ring[(k + 1) % 4], g3)
			_dl(ring[k], fp + Vector3(0.0, 0.62, 0.0), g3)
			_dl(ring[k], fp + Vector3(0.0, 0.02, 0.0), g3)
	_square(fp + Vector3(0.0, 0.02, 0.0), 0.3, g2)
	if logic.caught and int(logic.caught_by) >= 0:
		_dl(post_pos(int(logic.caught_by)) + Vector3(0.0, 0.8, 0.0), fp + Vector3(0.0, 0.3, 0.0), a3)
	_dyn.surface_end()
	if _hud != null:
		_hud.queue_redraw()
	if _tube != null:
		Crt.snap(_tube, S, Crt.tube_rect(art, S).position)
	var lamp := 2 if _hold_kind == "seen" else 1
	if _tube != null and _tube.material != null:
		(_tube.material as ShaderMaterial).set_shader_parameter("alarm_on", 1.0 if lamp == 2 else 0.0)
	if lamp != _lamp:
		_lamp = lamp
		if _stage != null:
			_stage.queue_redraw()


func draw_stage(v: Control) -> void:
	Crt.draw_housing(v, art, S, "SG 1", _lamp, Kit.high_contrast())


## The head-up text, lettered into the 3D viewport so it glows like the lines.
func draw_hud(ci: CanvasItem) -> void:
	var g1 := Crt.beam(1)
	var g2 := Crt.beam(2)
	var g3 := Crt.beam(3)
	Crt.draw_text(ci, Kit.t("mg.abgang.hud.title"), Vector2(5, 2), g1)
	var ml := Kit.t("mg.abgang.hud.map", {"n": int(logic.index) + 1, "name": map_name()})
	Crt.draw_text(ci, ml, Vector2(art.x - 5 - Crt.text_width(ml), 2), g2)
	var bl := Kit.t("mg.abgang.hud.beat")
	var bw := Crt.draw_text(ci, bl, Vector2(5, art.y - 10), g1)
	var b4: int = (logic.tick / Logic.BEAT_TICKS) % 4
	for k in 4:
		var r := Rect2(5 + bw + 4 + k * 7, art.y - 9, 5, 6)
		if k == b4:
			ci.draw_rect(r, g3)
		else:
			ci.draw_rect(Rect2(r.position.x, r.position.y + 5, 5, 1), g1)
	var run := Kit.t("mg.abgang.hud.run")
	Crt.draw_text(ci, run, Vector2(art.x - 5 - Crt.text_width(run), art.y - 10), g1)
	if trace_on:
		var tl := Kit.t("mg.abgang.hud.trace")
		Crt.draw_text(ci, tl, Vector2((art.x - Crt.text_width(tl)) / 2, art.y - 10), g2)
	var blink := Kit.reduced_motion() or fmod(_t, 0.5) < 0.32
	var gl := Kit.t("mg.abgang.hud.gap")
	var gp := project(cell_pos(logic.goal, 1.25))
	gp.x = clampf(gp.x - float(Crt.text_width(gl)) * 0.5, 4.0, float(art.x - 4 - Crt.text_width(gl)))
	gp.y = clampf(gp.y - 8.0, 12.0, float(art.y) - 22.0)
	Crt.draw_text(ci, gl, gp.floor(), g3 if blink else g2)
	var big := ""
	var second := false
	if solved:
		big = Kit.t("mg.abgang.hud.done")
	elif _hold_kind == "seen":
		big = Kit.t("mg.abgang.hud.seen")
		second = true
	elif _hold_kind == "next":
		big = Kit.t("mg.abgang.hud.through")
	if big != "":
		var bwid := Crt.text_width(big)
		var at := Vector2((art.x - bwid) / 2, art.y / 2 - 5)
		ci.draw_rect(Rect2(at.x - 6, at.y - 4, bwid + 11, 16), Color.BLACK)
		var col := Crt.beam(3, second)
		ci.draw_rect(Rect2(at.x - 6, at.y - 4, bwid + 11, 1), col)
		ci.draw_rect(Rect2(at.x - 6, at.y + 11, bwid + 11, 1), col)
		Crt.draw_text(ci, big, at, col)


# ================================================================ demo (synthetic keys only)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	var held := -1
	while not solved and not ended and Time.get_ticks_msec() - t0 < 240000:
		var want := -1
		if _hold <= 0.0:
			want = int(logic.demo_action(1))
		if want != held:
			if held >= 0:
				_key_event(DIR_KEYS[held], false)
			if want >= 0:
				_key_event(DIR_KEYS[want], true)
			held = want
		await get_tree().process_frame
	if held >= 0:
		_key_event(DIR_KEYS[held], false)
	await _until(func(): return solved, 4.0)
