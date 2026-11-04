class_name TexelLight
extends RefCounted
## Materials for pixel-art sprites in the high-resolution world path (owner: render-camera).
##  * coded (scripts/render/pixel_sprite.gdshader) for OPAQUE sprites: per-texel 2D lighting + the sprite's own
##    texel-anchored Bayer threshold written to the framebuffer alpha, which post_grade.gdshader uses for the
##    palette-snap dither -> the dither sticks to each layer/actor (no crawl during pans, no slivers).
##  * plain (scripts/render/texel_light.gdshader) for translucent sprites: per-texel lighting only.
## Usage: TexelLight.apply(sprite, anchor)   (only touches CanvasItems without a material of their own)

const CODED_SHADER := preload("res://scripts/render/pixel_sprite.gdshader")
const PLAIN_SHADER := preload("res://scripts/render/texel_light.gdshader")
static var _coded: ShaderMaterial
static var _plain: ShaderMaterial
static var _opaque_cache: Dictionary = {}


static func coded_material() -> ShaderMaterial:
	if _coded == null:
		_coded = ShaderMaterial.new()
		_coded.shader = CODED_SHADER
	return _coded


static func material() -> ShaderMaterial:
	if _plain == null:
		_plain = ShaderMaterial.new()
		_plain.shader = PLAIN_SHADER
	return _plain


## True if the texture's alpha is binary (pixel art without soft edges) -> safe to draw without blending.
static func is_opaque_pixel_art(t: Texture2D) -> bool:
	if t == null:
		return false
	if t is CanvasTexture:
		t = (t as CanvasTexture).diffuse_texture
		if t == null:
			return false
	var key := t.resource_path if t.resource_path != "" else str(t.get_instance_id())
	if _opaque_cache.has(key):
		return _opaque_cache[key]
	var ok := false
	var img := t.get_image()
	if img:
		if img.is_compressed():
			img.decompress()
		ok = img.detect_alpha() != Image.ALPHA_BLEND
	_opaque_cache[key] = ok
	return ok


## Assigns a material to `item` if it has none: the coded material for opaque, fully visible sprites (lit or
## not), else the plain per-texel lighting material for lit sprites. `anchor` = world texel position of the
## texture's (0, 0) (keeps the dither phase continuous across sprites of one plane); `cell` = sheet cell size.
static func apply(item: CanvasItem, anchor := Vector2.ZERO, cell := Vector2.ZERO) -> void:
	if item == null or item.material != null:
		return
	var tex: Texture2D = item.get("texture") if "texture" in item else null
	if tex != null and is_opaque_pixel_art(tex) and _visible_alpha(item) >= 0.999:
		item.material = coded_material()
		item.set_instance_shader_parameter("dither_anchor", anchor)
		item.set_instance_shader_parameter("dither_cell", cell)
	elif item.light_mask != 0:
		item.material = material()


## Switches between coded (opaque) and plain (blended) at runtime, e.g. while an actor is faded.
static func set_blended(item: CanvasItem, blended: bool) -> void:
	if item == null:
		return
	if blended and item.material == _coded and _coded != null:
		item.material = material()
	elif not blended and item.material == _plain and _plain != null:
		item.material = coded_material()


static func is_coded(item: CanvasItem) -> bool:
	return item != null and _coded != null and item.material == _coded


## Applies to every Sprite2D below `root` (inclusive) that qualifies (anchor 0).
static func apply_tree(root: Node, cell := Vector2.ZERO) -> void:
	if root is Sprite2D:
		apply(root as CanvasItem, Vector2.ZERO, cell)
	for c in root.get_children():
		apply_tree(c, cell)


## Product of the modulate alpha of `item` and its CanvasItem ancestors.
static func _visible_alpha(item: CanvasItem) -> float:
	var a := item.self_modulate.a * item.modulate.a
	var n := item.get_parent()
	while n is CanvasItem:
		a *= (n as CanvasItem).modulate.a
		n = n.get_parent()
	return a
