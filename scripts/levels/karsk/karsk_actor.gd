extends Node2D
## Shared base of the Karsk ambient actors (TECHNICAL_ARCHITECTURE §12.2 "actors"): self-contained scenes that
## Level instances into the y-sorted Playfield from assets/environments/karsk_railyard/scene.json. They never
## touch Story or Explore state; they only read the player position, the camera, the wind and the settings.
## Art comes from tools/pixelgen/env_karsk_sprites.py (frame strips) — see documentation/asset_manifest_parts.
##
## Common props (set by Level from the manifest before _ready):
##   parallax  < 1.0 puts the actor on a background plane: position = home + camera * (1 - parallax)
##   z         absolute draw order (the Playfield is z 0; -13 = just in front of the yard_back layer)

var parallax := 1.0
var z := 0.0
var home := Vector2.ZERO
var _puffs: Array = []          # [{node: Sprite2D, vel: Vector2, age: float, life: float, frames: int}]
const TEXEL_LIGHT := "res://scripts/render/texel_light.gd"
static var _texel_lib: Script = null


func _ready() -> void:
	home = position
	z_index = int(z)
	process_priority = 10       # after the camera (same as LayerStack)
	_setup()


## Override in subclasses instead of _ready.
func _setup() -> void:
	pass


func _process(delta: float) -> void:
	if parallax < 1.0:
		position = _parallax_position()
	_update_puffs(delta)
	_tick(delta)


## Same placement rule as LayerStack._update_parallax: on screen the actor sits at (home - cam * parallax),
## rounded to the viewport pixel grid (k px per world px in the high-resolution world path), so background
## actors stay locked to the layer they belong to (laundry line, lit windows, embankment) while panning.
func _parallax_position() -> Vector2:
	var c := cam_pos()
	var p := Vector2(parallax, 0.0)
	var k := 1.0
	var g := game()
	if g != null:
		var cam = g.get("camera")
		if cam != null and is_instance_valid(cam) and cam.has_method("px_scale"):
			k = maxf(1.0, float(cam.px_scale()))
	if k <= 1.0:
		return (home + c * (Vector2.ONE - p)).round()
	return c + ((home - c * p) * k + Vector2(0.5, 0.5)).floor() / k


## Per-texel lighting / texel-anchored dither material of the high-resolution world path (render-camera's
## scripts/render/texel_light.gd), so actor sprites shade and dither exactly like layers and props.
## No-op when that helper is missing or the item already has a material (additive glows keep theirs).
func texel(item: CanvasItem, cell := Vector2.ZERO, anchor := Vector2.ZERO) -> void:
	if item == null or item.material != null:
		return
	if _texel_lib == null and ResourceLoader.exists(TEXEL_LIGHT):
		_texel_lib = load(TEXEL_LIGHT)
	if _texel_lib != null and _texel_lib.has_script_method("apply"):
		_texel_lib.apply(item, anchor, cell)


## Override in subclasses instead of _process.
func _tick(_delta: float) -> void:
	pass


# ------------------------------------------------------------------ environment access
func game() -> Node:
	return get_node_or_null("/root/Game")


func cam_pos() -> Vector2:
	var g := game()
	if g != null:
		var c = g.get("camera")
		if c != null and is_instance_valid(c):
			return c.drawn
	return Vector2.ZERO


## Player feet in world pixels (this actor's parent space = the Playfield), or Vector2.INF when there is no
## player (cinematics, captures without player).
func player_pos() -> Vector2:
	var g := game()
	if g != null:
		var p = g.get("player")
		if p != null and is_instance_valid(p) and p is Node2D:
			var par := get_parent() as Node2D
			var gp: Vector2 = (p as Node2D).global_position
			return par.to_local(gp) if par != null else gp
	return Vector2.INF


func player_speed() -> float:
	var g := game()
	if g != null:
		var p = g.get("player")
		if p != null and is_instance_valid(p) and p is CharacterBody2D:
			return (p as CharacterBody2D).velocity.length()
	return 0.0


func reduced_motion() -> bool:
	var s := get_node_or_null("/root/Settings")
	return s != null and bool(s.get_value("reduced_motion"))


## True when world point p (playfield plane) is inside the visible window (+ margin).
func on_screen(p: Vector2, margin := 24.0) -> bool:
	var c := cam_pos()
	return p.x > c.x - margin and p.x < c.x + 640.0 + margin and p.y > c.y - margin and p.y < c.y + 360.0 + margin


func sfx(id: String, volume_db := 0.0, pitch_var := 0.06) -> void:
	var a := get_node_or_null("/root/Audio")
	if a != null and a.has_method("sfx"):
		a.sfx(id, volume_db, pitch_var)


## Distance attenuation for one-shot sounds of things at world point p (screen-centre based, never silent
## when on screen).
func dist_db(p: Vector2, near_db := -6.0, far_db := -22.0, falloff := 420.0) -> float:
	var c := cam_pos() + Vector2(320, 180)
	var d := absf(p.x - c.x)
	return lerpf(near_db, far_db, clampf(d / falloff, 0.0, 1.0))


# ------------------------------------------------------------------ textures
static func load_tex(path: String) -> Texture2D:
	if path == "":
		return null
	if ResourceLoader.exists(path):
		return load(path) as Texture2D
	if FileAccess.file_exists(path):   # not imported yet (dev run) -> raw load
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	return null


static func canvas_tex(path: String, with_normal := true) -> Texture2D:
	var d := load_tex(path)
	if d == null or not with_normal:
		return d
	var n := load_tex(path.get_basename() + "_n.png")
	if n == null:
		return d
	var ct := CanvasTexture.new()
	ct.diffuse_texture = d
	ct.normal_texture = n
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return ct


## A frame-strip sprite (top-left anchored) as a child.
func make_strip(tex: Texture2D, frames: int, lit := true) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex
	s.centered = false
	s.hframes = maxi(1, frames)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if not lit:
		s.light_mask = 0
	add_child(s)
	if tex != null:
		texel(s, Vector2(tex.get_width() / float(maxi(1, frames)), tex.get_height()) if frames > 1 else Vector2.ZERO)
	return s


## Additive, unshaded copy for emissive pixels (<file>_e.png), like LayerStack's emission sprites.
func make_glow(path: String, frames: int, strength: float) -> Sprite2D:
	var e := load_tex(path.get_basename() + "_e.png")
	if e == null:
		return null
	var s := Sprite2D.new()
	s.texture = e
	s.centered = false
	s.hframes = maxi(1, frames)
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	s.material = mat
	s.modulate = Color(1, 1, 1, strength)
	add_child(s)
	return s


# ------------------------------------------------------------------ small puffs (breath, smoke, steam)
## Spawns a one-shot puff from a square frame strip; `at` is the puff centre in this node's local space.
func spawn_puff(tex: Texture2D, frames: int, at: Vector2, vel: Vector2, life: float, lit := false) -> void:
	if tex == null:
		return
	var s := Sprite2D.new()
	s.texture = tex
	s.centered = false
	s.hframes = maxi(1, frames)
	s.light_mask = 1 if lit else 0
	var cell := Vector2(tex.get_width() / float(frames), tex.get_height())
	s.offset = (-cell * 0.5).round()
	s.position = at.round()
	add_child(s)
	texel(s, cell)
	_puffs.append({"node": s, "pos": at, "vel": vel, "age": 0.0, "life": life, "frames": frames})


func _update_puffs(delta: float) -> void:
	if _puffs.is_empty():
		return
	var keep: Array = []
	for p in _puffs:
		p["age"] += delta
		var s: Sprite2D = p["node"]
		if p["age"] >= p["life"] or not is_instance_valid(s):
			if is_instance_valid(s):
				s.queue_free()
			continue
		p["pos"] += p["vel"] * delta
		p["vel"] *= pow(0.55, delta)            # puffs slow down as they spread
		s.position = (p["pos"] as Vector2).round()
		s.frame = mini(int(p["age"] / p["life"] * p["frames"]), p["frames"] - 1)
		keep.append(p)
	_puffs = keep
