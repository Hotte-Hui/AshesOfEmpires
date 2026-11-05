extends RefCounted
## Shared helpers for the Berlin archive ambient actors (scenes/levels/berlin/*.tscn).
## Actors are spawned by Level._spawn_actors() from berlin_archive/scene.json "actors" and must work without
## any other game code (headless tests instance them alone), so every lookup here is defensive.


## Top-left of what the world camera shows this frame (same value layer_stack.gd uses for parallax).
static func cam_top_left() -> Vector2:
	var root := (Engine.get_main_loop() as SceneTree).root if Engine.get_main_loop() is SceneTree else null
	if root == null:
		return Vector2.ZERO
	var g := root.get_node_or_null("/root/Game")
	if g == null:
		return Vector2.ZERO
	var cam = g.get("camera")
	if cam == null or not is_instance_valid(cam):
		return Vector2.ZERO
	var d = cam.get("drawn")
	if d is Vector2:
		return d
	if cam.has_method("top_left"):
		return cam.top_left()
	return (cam as Node2D).global_position + Vector2.ONE


## World position of the player, or null when there is none (cinematics, tests).
static func player_pos(node: Node) -> Variant:
	if node == null or not node.is_inside_tree():
		return null
	var p := node.get_tree().get_first_node_in_group("player") as Node2D
	return p.global_position if p else null


static func reduced_motion() -> bool:
	var root := (Engine.get_main_loop() as SceneTree).root if Engine.get_main_loop() is SceneTree else null
	var s = root.get_node_or_null("/root/Settings") if root else null
	return s != null and s.has_method("get_value") and bool(s.get_value("reduced_motion"))


## Texture by path: imported resource if available, raw PNG otherwise (fresh files before an --import).
static func tex(path: String) -> Texture2D:
	if path == "":
		return null
	if ResourceLoader.exists(path):
		return load(path) as Texture2D
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	return null


## Diffuse (+ optional normal map "<base>_n.png") as a CanvasTexture with nearest filtering.
static func canvas_tex(path: String, with_normal: bool) -> Texture2D:
	var d := tex(path)
	if d == null or not with_normal:
		return d
	var n := tex(path.get_basename() + "_n.png")
	if n == null:
		return d
	var ct := CanvasTexture.new()
	ct.diffuse_texture = d
	ct.normal_texture = n
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return ct


## Positional one-shot / loop player on the SFX bus (graceful no-op when the file does not exist yet).
static func make_sound(parent: Node, path: String, volume_db := 0.0, max_distance := 420.0,
		attenuation := 1.4, loop := false) -> AudioStreamPlayer2D:
	if path == "" or not ResourceLoader.exists(path):
		return null
	var stream = load(path)
	if stream == null:
		return null
	if loop and stream is AudioStreamWAV:
		var src := stream as AudioStreamWAV
		# the generator writes a RIFF 'smpl' loop the importer picks up; this is only a fallback
		if src.loop_mode == AudioStreamWAV.LOOP_DISABLED and src.format == AudioStreamWAV.FORMAT_16_BITS:
			var w := src.duplicate() as AudioStreamWAV
			w.loop_mode = AudioStreamWAV.LOOP_FORWARD
			w.loop_begin = 0
			w.loop_end = w.data.size() / (2 * (2 if w.stereo else 1))
			stream = w
	var s := AudioStreamPlayer2D.new()
	s.stream = stream
	s.bus = &"SFX"
	s.volume_db = volume_db
	s.max_distance = max_distance
	s.attenuation = attenuation
	parent.add_child(s)
	return s


## Gradient light texture shared by the actors' PointLight2Ds.
static func light_texture() -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.45, Color(1, 1, 1, 0.42))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.width = 128
	gt.height = 128
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.0, 0.5)
	return gt


## Gives a sprite the shared per-texel lighting / texel-anchored dither material of the render path
## (scripts/render/texel_light.gd, owner render-camera) so actors match layers and characters.  No-op if that
## library is absent or the sprite already has a material (e.g. an additive glow).
static func texel(item: CanvasItem, anchor := Vector2.ZERO, cell := Vector2.ZERO) -> void:
	const LIB := "res://scripts/render/texel_light.gd"
	if item == null or item.material != null or not ResourceLoader.exists(LIB):
		return
	var tl = load(LIB)
	if tl:
		tl.apply(item, anchor, cell)


static func v2(v, fallback := Vector2.ZERO) -> Vector2:
	if v is Vector2:
		return v
	if v is Array and v.size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return fallback
