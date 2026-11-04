extends Node2D
## Builds a level's parallax backdrop, y-sorted props, 2D lights and FX from an art manifest
## (assets/environments/<id>/scene.json — TECHNICAL_ARCHITECTURE §3.1) and keeps parallax layers
## positioned relative to the world camera every frame.

const SnowFx := preload("res://scripts/levels/fx_snow.gd")
const FlickerLight := preload("res://scripts/levels/flicker_light.gd")

var manifest: Dictionary = {}
var base_dir := ""
var layers_by_name: Dictionary = {}
var _parallax: Array = []          # [{node, home: Vector2, parallax: Vector2}]
var _anims: Array = []             # [{sprite, frames, fps, t}]
static var _light_tex: Texture2D


func _init() -> void:
	process_priority = 10   # after the camera


static func tex(path: String) -> Texture2D:
	if path == "":
		return null
	if ResourceLoader.exists(path):
		return load(path) as Texture2D
	if FileAccess.file_exists(path):   # not yet imported (dev run) -> load raw
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	return null


static func canvas_tex(path: String, with_normal: bool) -> Texture2D:
	var d := tex(path)
	if d == null:
		return null
	if not with_normal:
		return d
	var n := tex(path.get_basename() + "_n.png")
	if n == null:
		return d
	var ct := CanvasTexture.new()
	ct.diffuse_texture = d
	ct.normal_texture = n
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return ct


static func light_texture() -> Texture2D:
	if _light_tex == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.45, Color(1, 1, 1, 0.42))
		var gt := GradientTexture2D.new()
		gt.gradient = g
		gt.width = 256
		gt.height = 256
		gt.fill = GradientTexture2D.FILL_RADIAL
		gt.fill_from = Vector2(0.5, 0.5)
		gt.fill_to = Vector2(1.0, 0.5)
		_light_tex = gt
	return _light_tex


func build(m: Dictionary, dir: String, playfield: Node2D, lights_root: Node2D, fx_root: Node2D) -> void:
	manifest = m
	base_dir = dir
	for L in m.get("layers", []):
		_build_layer(L)
	for P in m.get("props", []):
		_build_prop(P, playfield)
	for li in m.get("lights", []):
		_build_light(li, lights_root)
	for fx in m.get("fx", []):
		_build_fx(fx, fx_root)


func _build_layer(L: Dictionary) -> void:
	var path := base_dir + "/" + str(L.get("file", ""))
	var t := canvas_tex(path, bool(L.get("normal", false)))
	if t == null:
		push_warning("LayerStack: missing layer " + path)
		return
	var holder := Node2D.new()
	holder.name = str(L.get("name", "layer"))
	holder.z_index = int(L.get("z", 0))
	var spr := Sprite2D.new()
	spr.texture = t
	spr.centered = false
	if not bool(L.get("lit", true)):
		spr.light_mask = 0
	holder.add_child(spr)
	var rep := int(L.get("repeat_x", 0))
	if rep > 0:   # tile horizontally (e.g. drifting cloud bands)
		for i in range(1, rep + 1):
			var s2 := spr.duplicate() as Sprite2D
			s2.position.x = t.get_width() * i
			holder.add_child(s2)
	if bool(L.get("emission", false)):
		var e := tex(path.get_basename() + "_e.png")
		if e:
			var es := Sprite2D.new()
			es.texture = e
			es.centered = false
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
			es.material = mat
			es.modulate = Color(1, 1, 1, float(L.get("emission_strength", 0.22)))
			holder.add_child(es)
	add_child(holder)
	var p: Array = L.get("parallax", [1, 1])
	var home := _v2(L.get("pos", [0, 0]))
	var par := Vector2(float(p[0]), float(p[1] if p.size() > 1 else p[0]))
	holder.position = home
	layers_by_name[holder.name] = holder
	_parallax.append({"node": holder, "home": home, "parallax": par})


func _build_prop(P: Dictionary, playfield: Node2D) -> void:
	var path := base_dir + "/" + str(P.get("file", ""))
	var t := canvas_tex(path, bool(P.get("normal", true)))
	if t == null:
		push_warning("LayerStack: missing prop " + path)
		return
	var pos := _v2(P.get("pos", [0, 0]))
	var base_y := float(P.get("base_y", pos.y + t.get_height()))
	var node := Node2D.new()
	node.name = str(P.get("name", "prop"))
	node.position = Vector2(pos.x, base_y)
	node.z_index = int(P.get("z", 0))
	var spr := Sprite2D.new()
	spr.texture = t
	spr.centered = false
	spr.offset = Vector2(0, pos.y - base_y)
	node.add_child(spr)
	if bool(P.get("emission", false)):
		var e := tex(path.get_basename() + "_e.png")
		if e:
			var es := Sprite2D.new()
			es.texture = e
			es.centered = false
			es.offset = spr.offset
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
			es.material = mat
			es.modulate.a = 0.22
			node.add_child(es)
	var col = P.get("collision", null)
	if col is Array and col.size() >= 3:
		var body := StaticBody2D.new()
		var cp := CollisionPolygon2D.new()
		var pts := PackedVector2Array()
		for q in col:
			pts.append(_v2(q) - node.position)
		cp.polygon = pts
		body.add_child(cp)
		node.add_child(body)
	playfield.add_child(node)


func _build_light(li: Dictionary, lights_root: Node2D) -> void:
	var l := PointLight2D.new()
	l.set_script(FlickerLight)
	l.texture = light_texture()
	l.color = Color(str(li.get("color", "#F0C487")))
	l.energy = float(li.get("energy", 1.0))
	l.texture_scale = float(li.get("radius", 80)) / 128.0
	l.height = float(li.get("height", 24))
	l.set("base_energy", l.energy)
	l.set("flicker", float(li.get("flicker", 0.0)))
	var pos := _v2(li.get("pos", [0, 0]))
	var on := str(li.get("on_layer", "playfield"))
	if layers_by_name.has(on):
		layers_by_name[on].add_child(l)
		l.position = pos - layers_by_name[on].position if bool(li.get("world_coords", true)) else pos
	else:
		lights_root.add_child(l)
		l.position = pos


func _build_fx(fx: Dictionary, fx_root: Node2D) -> void:
	match str(fx.get("type", "")):
		"snow":
			var s := SnowFx.new()
			s.density = float(fx.get("density", 0.6))
			s.wind = float(fx.get("wind", 6.0))
			s.color_far = Color(str(fx.get("color_far", "#9fb0ad")))
			s.color_near = Color(str(fx.get("color_near", "#e6ece4")))
			fx_root.add_child(s)
		"anim_sprite", "smoke", "steam":
			if not fx.has("file"):
				return
			var t := tex(base_dir + "/" + str(fx["file"]))
			if t == null:
				return
			var frames := maxi(1, int(fx.get("frames", 1)))
			var spr := Sprite2D.new()
			spr.texture = t
			spr.centered = false
			spr.hframes = frames
			if not bool(fx.get("lit", false)):
				spr.light_mask = 0
			var holder := Node2D.new()
			holder.z_index = int(fx.get("z", -20))
			holder.add_child(spr)
			add_child(holder)
			var home := _v2(fx.get("pos", [0, 0]))
			var pv = fx.get("parallax", 1.0)
			var par := Vector2(float(pv[0]), float(pv[1])) if pv is Array else Vector2(float(pv), float(pv))
			holder.position = home
			_parallax.append({"node": holder, "home": home, "parallax": par})
			_anims.append({"sprite": spr, "frames": frames, "fps": float(fx.get("fps", 6)), "t": randf() * 5.0})
		"fog_band":
			_build_fog(fx)


func _build_fog(fx: Dictionary) -> void:
	var w := int(fx.get("width", int(manifest.get("world_size", [1920, 360])[0])))
	var h := int(fx.get("height", 40))
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var c := Color(str(fx.get("color", "#AFC1AA")))
	var a := float(fx.get("alpha", 0.35))
	var bayer := [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]
	var noise := FastNoiseLite.new()
	noise.seed = int(fx.get("seed", 3))
	noise.frequency = 0.012
	for y in h:
		var vy := 1.0 - absf((float(y) / maxf(1.0, h - 1.0)) * 2.0 - 1.0)
		for x in w:
			var dens := vy * (0.65 + 0.35 * noise.get_noise_2d(x, y * 3.0)) * a
			var th: float = (float(bayer[(y % 4) * 4 + (x % 4)]) + 0.5) / 16.0
			var al := 0.0
			if dens * 2.0 > th:
				al = clampf(dens * 1.6, 0.12, 0.6)
			img.set_pixel(x, y, Color(c.r, c.g, c.b, al))
	var spr := Sprite2D.new()
	spr.texture = ImageTexture.create_from_image(img)
	spr.centered = false
	spr.light_mask = 0
	var holder := Node2D.new()
	holder.z_index = int(fx.get("z", -15))
	holder.add_child(spr)
	add_child(holder)
	var home := Vector2(float(fx.get("x", 0)), float(fx.get("y", 200)) - h * 0.5)
	var par := float(fx.get("parallax", 0.6))
	holder.position = home
	_parallax.append({"node": holder, "home": home, "parallax": Vector2(par, par)})


func _process(delta: float) -> void:
	var cam: Vector2 = Game.camera.drawn if Game.camera else Vector2.ZERO
	for e in _parallax:
		var p: Vector2 = e["parallax"]
		if p == Vector2.ONE:
			continue
		var home: Vector2 = e["home"]
		e["node"].position = (home + cam * (Vector2.ONE - p)).round()
	for a in _anims:
		a["t"] += delta
		a["sprite"].frame = int(a["t"] * a["fps"]) % int(a["frames"])


static func _v2(v) -> Vector2:
	if v is Array and v.size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	if v is Vector2:
		return v
	return Vector2.ZERO
