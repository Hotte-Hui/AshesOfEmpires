extends Control
## Shows the World SubViewport (TECHNICAL_ARCHITECTURE §2, round-2 render contract in
## documentation/asset_manifest_parts/render-camera.md). Two render paths:
##
## * hi-res (2D levels and 2D cinematics, default): the viewport renders the world window plus a 1 world px
##   overscan margin at k viewport pixels per world pixel, k = world_scale (3 @1080p, 4 @1440p, 6 @2160p —
##   chosen so the viewport maps 1:1 onto physical screen pixels; other window sizes fall back to the largest
##   integer k that fits and the canvas stretch). Camera2D zoom = k. Camera and actors therefore move in single
##   screen pixels, every texel is a crisp k x k block, and the world-pixel-scale post effects (palette snap +
##   Bayer dither, grain, vignette dither) run on the 640x360 grid (post_grade.gdshader px_scale/dither_origin).
##   World renders raw and transparent (opaque sprites write their texel dither code into alpha); the post runs
##   in a second stage (Graded SubViewport, GradeStage TextureRect with the shared grade material) whose texture
##   the Display shows.
## * low-res (3D levels such as the Great Hall, and legacy --capture-world runs): 642x362 viewport shown at x3
##   with the sub-pixel remainder of the camera/lens as a display offset (set_fraction) — the palette-exact 3D
##   pixel post keeps its 1 px = 1 world px contract.
##
## Public API (kept): setup, set_fraction, world_to_ui, set_shake; new: is_hires, set_hires, world_scale,
## capture_world_image, resolution_changed.

signal resolution_changed(world_scale: int)

const SCALE := 3.0                     ## UI canvas units per world pixel (1920x1080 canvas / 640x360 world)
const WORLD := Vector2i(640, 360)
const MARGIN := 1                      ## world px of overscan on each side (sub-pixel offsets, shake)
const GRAIN_HZ := 8.0
const TexelLightLib := preload("res://scripts/render/texel_light.gd")

@onready var display: TextureRect = $Display
var subpixel := true
var world_scale := 3                   ## k: viewport px per world px in the hi-res path
var _hires := true
var _want_hires := true
var _legacy_capture := false
var _vp: SubViewport
var _graded: SubViewport
var _stage: TextureRect
var _grade: ColorRect
var _cam: Node
var _fraction := Vector2.ZERO
var _shake := Vector2.ZERO
var _grain_t := 0.0
var _coded_watch: Array[Sprite2D] = []   # world sprites with the texel-coded material (fade watch)


func setup(vp: SubViewport, graded: SubViewport = null) -> void:
	_vp = vp
	_graded = graded
	if _graded:
		_stage = _graded.get_node_or_null("GradeStage") as TextureRect
		if _stage:
			_stage.texture = vp.get_texture()
			_stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	display.texture = vp.get_texture()
	display.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_grade = vp.get_node_or_null("Post/Grade") as ColorRect
	_cam = vp.get_node_or_null("Camera")
	_legacy_capture = _detect_legacy_world_capture()
	var w := get_window()
	if w and not w.size_changed.is_connected(_update_resolution):
		w.size_changed.connect(_update_resolution)
	if not get_tree().node_added.is_connected(_on_node_added):
		get_tree().node_added.connect(_on_node_added)
	_update_resolution()


## True while the world renders in the high-resolution 2D path.
func is_hires() -> bool:
	return _hires


## Main switches to the low-res path while a 3D level is in the world viewport.
func set_hires(on: bool) -> void:
	_want_hires = on
	_apply_path()


func set_fraction(f: Vector2) -> void:
	_fraction = f if (subpixel and not _hires) else Vector2.ZERO
	_place_display()


## UI-canvas position of a world pixel position, given the camera's top-left (Game.world_to_ui).
func world_to_ui(world_pos: Vector2, cam_top_left: Vector2) -> Vector2:
	return (world_pos - cam_top_left) * SCALE


## Screen shake in UI canvas units (rounded to whole canvas px; up to MARGIN * SCALE px is hidden by the margin).
func set_shake(offset: Vector2) -> void:
	_shake = offset.round()
	_place_display()


## The visible 640x360 world window in world pixels, graded (one sample per texel, k x k block centres).
func capture_world_image() -> Image:
	var src: SubViewport = _graded if (_hires and _stage) else _vp
	var img := src.get_texture().get_image()
	if not _hires:
		return img.get_region(Rect2i(MARGIN, MARGIN, WORLD.x, WORLD.y))
	var k := world_scale
	var off := k * MARGIN                     # nearest resize samples each k x k block at its centre
	var region := img.get_region(Rect2i(off, off, WORLD.x * k, WORLD.y * k))
	region.resize(WORLD.x, WORLD.y, Image.INTERPOLATE_NEAREST)
	return region


# ------------------------------------------------------------------------------------------------ internals
func _update_resolution() -> void:
	var k := 3
	var w := get_window()
	if w:
		var xf: Transform2D = w.get_stretch_transform() if w.has_method("get_stretch_transform") else Transform2D()
		var ks := xf.get_scale().x * SCALE
		var o := xf.origin
		if absf(ks - roundf(ks)) < 0.01 and roundf(ks) >= 1.0 and absf(o.x - roundf(o.x)) < 0.01 \
				and absf(o.y - roundf(o.y)) < 0.01:
			k = int(roundf(ks))             # exact 1:1 mapping onto physical pixels
		else:
			k = maxi(1, int(floorf(ks + 0.001)))   # nearest integer render, stretched by the canvas
	world_scale = clampi(k, 1, 12)
	_apply_path()


func _apply_path() -> void:
	if _vp == null:
		return
	_hires = _want_hires and not _legacy_capture
	var staged := _hires and _graded != null and _stage != null
	var k := world_scale if _hires else 1
	var size := (WORLD + Vector2i(MARGIN, MARGIN) * 2) * k
	if _vp.size != size:
		_vp.size = size
	# Hi-res: no transform snapping. Godot rounds y-sorted children's LOCAL transforms to whole units when it is
	# on (-> actors inside the y-sorted Playfield would snap to whole world px); vertex snapping alone places
	# every quad on the viewport pixel grid (1/k world px) after the camera transform, so texels stay crisp.
	_vp.snap_2d_transforms_to_pixel = not _hires
	_vp.snap_2d_vertices_to_pixel = true
	# Hi-res: keep the framebuffer alpha (texel dither codes of pixel_sprite.gdshader; an opaque viewport forces
	# alpha to 1 in the screen-texture copy). The post writes alpha 1, so the shown picture stays opaque.
	_vp.transparent_bg = staged
	if staged:
		if _graded.size != size:
			_graded.size = size
		_stage.position = Vector2.ZERO
		_stage.size = Vector2(size)
		_graded.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		display.texture = _graded.get_texture()
	else:
		if _graded:
			_graded.render_target_update_mode = SubViewport.UPDATE_DISABLED
		display.texture = _vp.get_texture()
	display.size = Vector2(WORLD + Vector2i(MARGIN, MARGIN) * 2) * SCALE
	if _grade:
		_grade.position = Vector2.ZERO
		_grade.size = Vector2(size)
		_grade.visible = not staged          # in-viewport post only in the low-res path
		var mat := _grade.material as ShaderMaterial
		if mat:
			mat.set_shader_parameter("px_scale", float(k))
			mat.set_shader_parameter("dither_origin", Vector2.ZERO)
			mat.set_shader_parameter("from_texture", staged)
	_fraction = Vector2.ZERO
	_place_display()
	_autoscale_canvas_layers()
	if _cam and _cam.has_method("refresh"):
		_cam.refresh()
	resolution_changed.emit(world_scale)


func _place_display() -> void:
	display.position = -(Vector2.ONE * MARGIN + _fraction) * SCALE + _shake


func _process(delta: float) -> void:
	for i in range(_coded_watch.size() - 1, -1, -1):
		var spr := _coded_watch[i]
		if not is_instance_valid(spr):
			_coded_watch.remove_at(i)
		else:
			TexelLightLib.set_blended(spr, TexelLightLib._visible_alpha(spr) < 0.999)
	if _grade == null:
		return
	var mat := _grade.material as ShaderMaterial
	if mat == null:
		return
	if _hires and _cam:
		var k := float(world_scale)
		var d: Vector2 = _cam.get("drawn")
		mat.set_shader_parameter("dither_origin", (d * k).round() - Vector2.ONE * k * MARGIN)
	if not bool(Settings.get_value("reduced_motion")):
		_grain_t += delta
		mat.set_shader_parameter("grain_seed", float(int(_grain_t * GRAIN_HZ) % 97))


## Compatibility shim for content drawn in screen space INSIDE the world viewport (a CanvasLayer under a level
## or cinematic, laid out for 640x360): scaled by k so it keeps covering the same part of the picture.
## Opt out with node meta "pv_no_autoscale" (e.g. content that already multiplies by Game.view.world_scale).
func _autoscale_canvas_layers() -> void:
	if _vp == null:
		return
	var lr := _vp.get_node_or_null("LevelRoot")
	if lr:
		_scale_layers_in(lr)


func _scale_layers_in(n: Node) -> void:
	for c in n.get_children():
		if c is CanvasLayer:
			var cl := c as CanvasLayer
			if not cl.has_meta("pv_no_autoscale"):
				var k := float(world_scale if _hires else 1)
				var base: Vector2 = cl.get_meta("pv_base_scale", cl.scale)
				cl.set_meta("pv_base_scale", base)
				cl.scale = base * k
		_scale_layers_in(c)


## Every Sprite2D entering the world viewport (layers, props, actors, NPC rigs, cinematic sets, later spawns)
## gets the pixel-art material (per-texel light; opaque sprites also the texel-anchored dither code) unless it
## brings its own; coded sprites are watched and fall back to normal blending while they are faded
## (modulate alpha < 1), so fades keep working. CanvasLayers added later inside the level root are autoscaled.
func _on_node_added(n: Node) -> void:
	if _vp == null or not (n is Sprite2D or n is AnimatedSprite2D or n is CanvasLayer):
		return
	if not _vp.is_ancestor_of(n):
		return
	if n is CanvasLayer:
		_autoscale_canvas_layers.call_deferred()
	else:
		_style_world_sprite.call_deferred(n)        # textures are usually assigned right after add_child()


func _style_world_sprite(n) -> void:   # untyped on purpose: deferred calls may deliver an already-freed node
	if not is_instance_valid(n) or not (n is Node) or not n.is_inside_tree():
		return
	var item := n as CanvasItem
	if item.material == null:
		var cell = n.get_parent().get("_cell") if n.get_parent() else null   # sprite_rig sheet cell
		TexelLightLib.apply(item, Vector2.ZERO, cell if cell is Vector2 else Vector2.ZERO)
	if n is Sprite2D and TexelLightLib.is_coded(item) and not _coded_watch.has(n):
		_coded_watch.append(n as Sprite2D)


## Called by Main when something enters the world (new levels/cinematics may carry CanvasLayers).
func on_world_child_added(_n: Node) -> void:
	_autoscale_canvas_layers.call_deferred()


## Legacy compatibility: until Game._capture_flow uses capture_world_image(), a --capture-world run crops
## Rect2i(1, 1, 640, 360) from the world texture itself, so such runs render the 642x362 path.
func _detect_legacy_world_capture() -> bool:
	var wants := false
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--capture-world"):
			wants = true
	if not wants:
		return false
	var g := get_node_or_null("/root/Game")
	if g and g.get_script() and str(g.get_script().source_code).contains("capture_world_image"):
		return false
	return true
