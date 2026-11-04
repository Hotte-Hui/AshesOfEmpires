extends Node2D
## Pixel-crisp snowfall in screen space of the world view (two depth bands, wind sway).
## Flakes are squares of 1 world px (far) or 2 world px (near). Their positions are kept in world px relative to
## the view and drawn on the viewport pixel grid (1/k world px in the high-resolution path, whole px in the
## low-res path) -> crisp flakes that fall smoothly at any render scale. Camera moves push the flakes with a
## little parallax (far 0.55 x, near 1.2 x the camera motion) so the snow sits inside the scene instead of
## sticking to the glass.

var density := 0.6
var wind := 6.0
var color_far := Color("#9fb0ad")
var color_near := Color("#e6ece4")
var _flakes: Array = []
var _last_cam := Vector2.INF
var _k := 1.0
const VIEW := Vector2(642, 362)          # view incl. the 1 px overscan margin, world px
const PAR_NEAR := 1.2
const PAR_FAR := 0.55


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
	var cam: Vector2 = Game.camera.drawn if Game.camera else Vector2.ZERO
	_k = 1.0
	if Game.camera and Game.camera.has_method("px_scale"):
		_k = maxf(1.0, Game.camera.px_scale())
	global_position = (cam - Vector2.ONE) if _k > 1.0 else (cam.floor() - Vector2.ONE)
	var dcam := Vector2.ZERO if _last_cam.x == INF else cam - _last_cam
	if dcam.length() > 48.0:         # cut / snap: no streaks
		dcam = Vector2.ZERO
	_last_cam = cam
	for f in _flakes:
		f["ph"] += delta * 1.3
		var near: bool = f["near"]
		var k := 1.0 if near else 0.55
		f["p"].y += f["v"] * delta
		f["p"].x += (wind * k + sin(f["ph"]) * f["amp"] * 0.6) * delta
		f["p"] -= dcam * (PAR_NEAR if near else PAR_FAR)
		if f["p"].y > VIEW.y:
			f["p"].y -= VIEW.y + 4.0
			f["p"].x = randf() * VIEW.x
		elif f["p"].y < -4.0:
			f["p"].y += VIEW.y + 4.0
		f["p"].x = fposmod(f["p"].x, VIEW.x)
	queue_redraw()


func _draw() -> void:
	for f in _flakes:
		var p: Vector2 = (f["p"] * _k).floor() / _k
		if f["near"]:
			draw_rect(Rect2(p, Vector2(2, 2)), color_near)
		else:
			draw_rect(Rect2(p, Vector2(1, 1)), color_far)
