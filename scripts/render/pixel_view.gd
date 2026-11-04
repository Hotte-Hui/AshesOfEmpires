extends Control
## Displays the 642x362 world SubViewport at integer scale (x3 on the 1920x1080 UI canvas, which the
## canvas_items stretch maps to x3 @1080p, x4 @1440p, x6 @2160p).  The camera keeps the viewport on whole
## pixels; the sub-pixel remainder of the camera position is applied here at display scale, giving smooth
## pans without pixel crawl (TECHNICAL_ARCHITECTURE §2).

const SCALE := 3.0

@onready var display: TextureRect = $Display
var subpixel := true
var _fraction := Vector2.ZERO
var _shake := Vector2.ZERO


func setup(vp: SubViewport) -> void:
	display.texture = vp.get_texture()
	display.size = Vector2(vp.size) * SCALE
	set_fraction(Vector2.ZERO)


func set_fraction(f: Vector2) -> void:
	_fraction = f if subpixel else Vector2.ZERO
	display.position = -(Vector2.ONE + _fraction) * SCALE + _shake


## UI-canvas position of a world pixel position, given the camera's continuous top-left.
func world_to_ui(world_pos: Vector2, cam_top_left: Vector2) -> Vector2:
	return (world_pos - cam_top_left) * SCALE


func set_shake(offset: Vector2) -> void:
	_shake = offset.round()
	set_fraction(_fraction)
