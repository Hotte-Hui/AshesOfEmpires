extends Node2D
## Pixel-crisp snowfall drawn in screen space of the world viewport (two depth bands, wind sway).
## Flakes are 1 px (far) or 2 px (near) squares on whole pixels -> no smeared particles.

var density := 0.6
var wind := 6.0
var color_far := Color("#9fb0ad")
var color_near := Color("#e6ece4")
var _flakes: Array = []
const VIEW := Vector2(642, 362)


func _ready() -> void:
	z_index = 40
	light_mask = 0
	var n := int(260 * density)
	for i in n:
		var near := randf() < 0.3
		_flakes.append({
			"p": Vector2(randf() * VIEW.x, randf() * VIEW.y),
			"v": randf_range(14.0, 22.0) if near else randf_range(6.0, 11.0),
			"near": near,
			"ph": randf() * TAU,
			"amp": randf_range(2.0, 6.0),
		})


func _process(delta: float) -> void:
	var cam: Vector2 = Game.camera.pos if Game.camera else Vector2.ZERO
	global_position = cam.floor() - Vector2.ONE
	for f in _flakes:
		f["ph"] += delta * 1.3
		var k := 1.0 if f["near"] else 0.55
		f["p"].y += f["v"] * delta
		f["p"].x += (wind * k + sin(f["ph"]) * f["amp"] * 0.6) * delta
		if f["p"].y > VIEW.y:
			f["p"].y -= VIEW.y + 4.0
			f["p"].x = randf() * VIEW.x
		f["p"].x = fposmod(f["p"].x, VIEW.x)
	queue_redraw()


func _draw() -> void:
	for f in _flakes:
		var p: Vector2 = f["p"].floor()
		if f["near"]:
			draw_rect(Rect2(p, Vector2(2, 2)), color_near)
		else:
			draw_rect(Rect2(p, Vector2(1, 1)), color_far)
