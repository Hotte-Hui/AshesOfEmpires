extends Node3D
## People and other pixel sprites of the Great Hall reveal (owner: hall / great_hall_3d).
## Sprite3D billboards with pixel-art frames, lit by the toon light model (pixel3d_sprite.gdshader).
## * Family/guard: res://assets/characters/<role>/sheet.png + sheet.json (row "idle_side", animated) when
##   present, else the placeholders in res://assets/architecture/great_hall/people/<role>.png.
## * Street life (walkers, queue, patrol, sweeper, birds, smoke, steam, the eagles): sheets from
##   res://assets/architecture/great_hall/life/ (life.json) or any character sheet, given in the spec.
## * set_people_sprites({role: path}) overrides a role with a sheet.png (sheet.json next to it) or any PNG.
## Texel lock: while `lock` is on, every sprite is resized so 1 texel = 1 screen pixel at its current depth
## and its feet are snapped to whole screen pixels (no mixels, no sub-pixel crawl).  While off (fast crane in
## h1) the sprites keep the world size calibrated at the reference camera pose.
##
## Spec keys (all optional except role/pos):
##   role: String, pos: Vector3 (feet), flip: bool, tint: Color, self_light: float, flag: float (post band),
##   file: String (PNG; a sheet when "cell" or a sheet.json is given), cell: Vector2i, origin: Vector2i,
##   row: int, anim: String (sheet.json anim), frames: int, fps: float, phase: float (s),
##   path: Array[Vector3] (feet positions), speed: float (m/s), t0: float (start time on the path),
##   loop_path: bool, walk_gs: float (sheet ground speed px/s at the nominal fps), stride_ref_depth: float,
##   show: Vector2 (visible from x to y seconds), dissolve: Vector4 (fade-in t0,t1, fade-out t2,t3),
##   frame_fn: Callable(t) -> int (custom frame), pos_fn: Callable(t) -> Vector3 (custom motion),
##   face_motion: bool (flip by screen direction of travel, default true for paths)

const SPRITE_SHADER := preload("res://assets/shaders/pixel3d_sprite.gdshader")
const PLACEHOLDER_DIR := "res://assets/architecture/great_hall/people/"
const CHAR_DIR := "res://assets/characters/"

## Each actor: {role, node, mat, feet, flip, ps_ref, src, spec, region0, cell, frames, fps, ...}
var actors: Array = []
var overrides: Dictionary = {}
var _spec: Array = []
var _tex_cache: Dictionary = {}
var _json_cache: Dictionary = {}
var time := 0.0


func setup(spec: Array) -> void:
	_spec = spec
	_rebuild()


## Merges role overrides; an empty string or null value removes the override for that role.
func set_overrides(paths: Dictionary) -> void:
	for k in paths:
		var v = paths[k]
		if v == null or str(v) == "":
			overrides.erase(k)
		else:
			overrides[k] = str(v)
	_rebuild()


func _tex(path: String) -> Texture2D:
	path = Symbols.pick(path)   # §12.4: e.g. the guard's armband variant
	if _tex_cache.has(path):
		return _tex_cache[path]
	var t: Texture2D = load(path) if ResourceLoader.exists(path) else null
	_tex_cache[path] = t
	return t


func _json(path: String) -> Dictionary:
	if _json_cache.has(path):
		return _json_cache[path]
	var d := {}
	if FileAccess.file_exists(path):
		var data = JSON.parse_string(FileAccess.get_file_as_string(path))
		if typeof(data) == TYPE_DICTIONARY:
			d = data
	_json_cache[path] = d
	return d


func _rebuild() -> void:
	for a in actors:
		var n: Node = a["node"]
		remove_child(n)          # detach now so old and new sprites never overlap for a frame
		n.queue_free()
	actors.clear()
	for e in _spec:
		var role: String = e["role"]
		var frame := _load_frame(role, e)
		if frame.is_empty():
			push_warning("HallPeople: no sprite for role " + role)
			continue
		var spr := Sprite3D.new()
		spr.name = "Actor_" + role + "_" + str(actors.size())
		spr.texture = frame["tex"]
		spr.region_enabled = true
		spr.region_rect = frame["region"]
		spr.centered = false
		var origin: Vector2 = frame["origin"]
		var rh: float = (frame["region"] as Rect2).size.y
		var rw: float = (frame["region"] as Rect2).size.x
		# feet pixel (origin) sits on the node position: its bottom edge on y=0, its left edge on x=0
		var flip := bool(e.get("flip", false))
		spr.offset = Vector2(-origin.x, -(rh - origin.y - 1.0))
		if flip:
			spr.offset.x = -(rw - origin.x - 1.0)
		spr.flip_h = flip
		spr.billboard = BaseMaterial3D.BILLBOARD_DISABLED   # billboarding happens in the shader
		spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		spr.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
		spr.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		spr.layers = 1 | 4        # world layer + people layer (character key lights)
		if e.has("layers"):
			spr.layers = int(e["layers"])
		var mat := ShaderMaterial.new()
		mat.shader = SPRITE_SHADER
		mat.set_shader_parameter("sprite_tex", frame["tex"])
		if frame.get("normal") != null:
			mat.set_shader_parameter("sprite_normal", frame["normal"])
			mat.set_shader_parameter("use_normal", true)
		mat.set_shader_parameter("flip", flip)
		mat.set_shader_parameter("tint", e.get("tint", Color.WHITE))
		mat.set_shader_parameter("self_light", float(e.get("self_light", 0.0)))
		if e.has("flag"):
			mat.set_shader_parameter("flag", float(e["flag"]))
		if e.has("unshaded"):
			mat.set_shader_parameter("unshaded", float(e["unshaded"]))
		if e.has("dither_alpha"):
			mat.set_shader_parameter("dissolve", float(e["dither_alpha"]))
		spr.material_override = mat
		add_child(spr)
		spr.global_position = e["pos"]
		var path: Array = e.get("path", [])
		var lens: Array = []
		var total := 0.0
		if path.size() >= 2:
			lens.append(0.0)
			for i in range(1, path.size()):
				total += (path[i] as Vector3).distance_to(path[i - 1])
				lens.append(total)
		actors.append({"role": role, "node": spr, "mat": mat, "feet": e["pos"], "flip": flip,
			"base_flip": flip, "ps_ref": 0.01, "src": frame["src"], "spec": e, "region0": frame["region"],
			"origin": origin, "frames": int(frame.get("frames", 1)), "fps": float(frame.get("fps", 0.0)),
			"cell_w": rw, "path": path, "lens": lens, "total": total, "frame": -1, "visible": true,
			"walk_gs": float(e.get("walk_gs", frame.get("walk_gs", 0.0)))})


## Loads the sprite frame for a role. Returns {tex, normal, region: Rect2, origin: Vector2, src, frames, fps}.
func _load_frame(role: String, e: Dictionary) -> Dictionary:
	var file_override := str(e.get("file", ""))
	var path := ""
	if overrides.has(role):
		path = str(overrides[role])
	elif file_override == "" and ResourceLoader.exists(CHAR_DIR + role + "/sheet.png"):
		path = CHAR_DIR + role + "/sheet.png"
	elif str(e.get("sheet", "")) != "" and ResourceLoader.exists(str(e["sheet"])):
		path = str(e["sheet"])
	if path != "" and ResourceLoader.exists(path):
		var d := _frame_from_sheet(path, e)
		if not d.is_empty():
			return d
	var ph := file_override if file_override != "" else PLACEHOLDER_DIR + role + ".png"
	if ResourceLoader.exists(ph):
		var tex := _tex(ph)
		var nrm := _tex(ph.get_basename() + "_n.png")
		if e.has("cell"):
			var cell := Vector2(e["cell"])
			var row := int(e.get("row", 0))
			var org := Vector2(e.get("origin", Vector2i(int(cell.x) / 2, int(cell.y) - 1)))
			return {"tex": tex, "normal": nrm, "region": Rect2(Vector2(0, row * cell.y), cell), "origin": org,
				"src": ph, "frames": int(e.get("frames", 1)), "fps": float(e.get("fps", 0.0))}
		var sz := Vector2(tex.get_width(), tex.get_height())
		return {"tex": tex, "normal": nrm, "region": Rect2(Vector2.ZERO, sz),
			"origin": Vector2(floorf(sz.x * 0.5), sz.y - 1.0), "src": ph, "frames": 1, "fps": 0.0}
	return {}


func _frame_from_sheet(png_path: String, e: Dictionary) -> Dictionary:
	var tex := _tex(png_path)
	if tex == null:
		return {}
	var data := _json(png_path.get_basename() + ".json")
	var cell := Vector2(tex.get_width(), tex.get_height())
	var origin := Vector2(floorf(cell.x * 0.5), cell.y - 1.0)
	var row := 0
	var frames := 1
	var fps := 0.0
	var gs := 0.0
	if not data.is_empty():
		var c: Array = data.get("cell", [])
		if c.size() == 2:
			cell = Vector2(float(c[0]), float(c[1]))
		var o: Array = data.get("origin", [])
		if o.size() == 2:
			origin = Vector2(float(o[0]), float(o[1]))
		var anims: Dictionary = data.get("anims", {})
		var want := str(e.get("anim", "idle_side"))
		var an: Dictionary = {}
		if anims.has(want):
			an = anims[want]
		elif anims.has("idle_side"):
			an = anims["idle_side"]
		elif not anims.is_empty():
			an = anims.values()[0]
		row = int(an.get("row", 0))
		frames = int(an.get("frames", 1))
		fps = float(an.get("fps", 0.0))
		var gsd: Dictionary = data.get("ground_speed", {})
		gs = float(gsd.get(want, 0.0))
	if e.has("row"):
		row = int(e["row"])
	if e.has("frames"):
		frames = int(e["frames"])
	if e.has("fps"):
		fps = float(e["fps"])
	var nrm := _tex(png_path.get_basename() + "_n.png")
	return {"tex": tex, "normal": nrm, "region": Rect2(Vector2(0, row * cell.y), cell), "origin": origin,
		"src": png_path, "frames": maxi(frames, 1), "fps": fps, "walk_gs": gs}


## Calibrate world sizes at the reference camera pose.  `rig` (hall_camera_rig.gd) must have that pose
## applied (its analytic projection is used because Camera3D.project_position ignores frustum offsets).
func calibrate(rig) -> void:
	for a in actors:
		var pr: Vector3 = rig.project(_feet_at(a, float((a["spec"] as Dictionary).get("ref_t", 3.0))))
		a["ps_ref"] = rig.pixel_size_at(maxf(pr.z, 0.1))
		(a["node"] as Sprite3D).pixel_size = a["ps_ref"]


func _feet_at(a: Dictionary, t: float) -> Vector3:
	var e: Dictionary = a["spec"]
	if e.has("pos_fn"):
		return (e["pos_fn"] as Callable).call(t)
	var path: Array = a["path"]
	if path.size() < 2:
		return a["feet"]
	var s := _dist_at(a, t)
	var lens: Array = a["lens"]
	var i := 1
	while i < lens.size() - 1 and float(lens[i]) < s:
		i += 1
	var l0: float = lens[i - 1]
	var l1: float = lens[i]
	var k := 0.0 if l1 - l0 < 1e-5 else clampf((s - l0) / (l1 - l0), 0.0, 1.0)
	return (path[i - 1] as Vector3).lerp(path[i], k)


func _dist_at(a: Dictionary, t: float) -> float:
	var e: Dictionary = a["spec"]
	var total: float = a["total"]
	var s := (t - float(e.get("t0", 0.0))) * float(e.get("speed", 1.2)) + float(e.get("s0", 0.0))
	if bool(e.get("loop_path", false)) and total > 0.0:
		s = fposmod(s, total)
	return clampf(s, 0.0, total)


func _frame_at(a: Dictionary, t: float, depth: float, rig) -> int:
	var e: Dictionary = a["spec"]
	var n: int = a["frames"]
	if n <= 1:
		return 0
	if e.has("frame_fn"):
		return int((e["frame_fn"] as Callable).call(t)) % n
	var path: Array = a["path"]
	var gs: float = a["walk_gs"]
	if path.size() >= 2 and gs > 0.0:
		# feet stay planted: frames advance with the distance walked, measured in sprite pixels at the
		# walker's reference depth (texel lock: 1 sprite px = 1 screen px = depth / f metres)
		var dref := float(e.get("stride_ref_depth", depth))
		var px_per_m: float = rig.focal_px(rig.cur_vp.y) / maxf(dref, 0.1)
		var s := _dist_at(a, t)
		var fps: float = maxf(a["fps"], 1.0)
		var fr := s * px_per_m * fps / gs + float(e.get("phase", 0.0)) * fps
		return int(floor(fr)) % n
	var f2: float = a["fps"]
	return int(floor((t + float(e.get("phase", 0.0))) * f2)) % n


## Per frame, after the camera moved.  lock = texel lock (1 texel = 1 px, feet on whole pixels).
func update_sprites(rig, lock: bool, t: float = -1.0) -> void:
	if t >= 0.0:
		time = t
	for a in actors:
		var spr: Sprite3D = a["node"]
		var e: Dictionary = a["spec"]
		# visibility window
		var vis := true
		if e.has("show"):
			var sw: Vector2 = e["show"]
			vis = time >= sw.x and time <= sw.y
		if vis != bool(a["visible"]):
			spr.visible = vis
			a["visible"] = vis
		if not vis:
			continue
		var feet := _feet_at(a, time)
		a["feet"] = feet
		var pr: Vector3 = rig.project(feet)
		# facing: sheets face right; flip when travelling left on screen
		var path: Array = a["path"]
		if bool(e.get("face_motion", path.size() >= 2 or e.has("pos_fn"))):
			var ahead: Vector3 = rig.project(_feet_at(a, time + 0.05))
			var dx := ahead.x - pr.x
			if absf(dx) > 0.001:
				var want_flip := dx < 0.0
				if bool(e.get("flip", false)):
					want_flip = not want_flip
				_set_flip(a, want_flip)
		# animation frame
		var fr := _frame_at(a, time, maxf(pr.z, 0.1), rig)
		if fr != int(a["frame"]):
			a["frame"] = fr
			var r0: Rect2 = a["region0"]
			spr.region_rect = Rect2(Vector2(r0.position.x + fr * r0.size.x, r0.position.y), r0.size)
		# dithered fade (dissolve) in/out
		if e.has("dissolve"):
			var dv: Vector4 = e["dissolve"]
			var amt := 0.0
			if time < dv.y:
				amt = 1.0 - clampf((time - dv.x) / maxf(dv.y - dv.x, 0.001), 0.0, 1.0)
			elif time > dv.z:
				amt = clampf((time - dv.z) / maxf(dv.w - dv.z, 0.001), 0.0, 1.0)
			(a["mat"] as ShaderMaterial).set_shader_parameter("dissolve", amt)
		if (not lock and not bool(e.get("always_lock", false))) or bool(e.get("no_lock", false)):
			spr.pixel_size = a["ps_ref"]
			spr.global_position = feet
			continue
		if pr.z <= 0.2:
			continue
		var w: Vector3 = rig.unproject(roundf(pr.x), roundf(pr.y), pr.z)
		spr.pixel_size = rig.pixel_size_at(pr.z)
		spr.global_position = w


func _set_flip(a: Dictionary, flip: bool) -> void:
	if bool(a["flip"]) == flip:
		return
	a["flip"] = flip
	var spr: Sprite3D = a["node"]
	var origin: Vector2 = a["origin"]
	var rw: float = a["cell_w"]
	spr.flip_h = flip
	spr.offset.x = -(rw - origin.x - 1.0) if flip else -origin.x
	(a["mat"] as ShaderMaterial).set_shader_parameter("flip", flip)


func get_sources() -> Dictionary:
	var d := {}
	for a in actors:
		d[a["role"]] = a["src"]
	return d


func count_visible() -> int:
	var n := 0
	for a in actors:
		if bool(a["visible"]):
			n += 1
	return n
