extends Control
## Pixel snow for the title screen: flakes live on the 640x360 world grid and are drawn as 3x3 / 6x6
## screen squares (1 or 2 world pixels), two depth layers, slow fall with gentle sway.
## Reduced motion: the flakes are drawn but stand still.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const PX := 3
const W := 640
const H := 360

var count := 170
var _flakes: Array = []      # [x, y, speed, sway_phase, size, alpha]
var _t := 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS
	var rng := RandomNumberGenerator.new()
	rng.seed = 1964
	for i in count:
		var near := rng.randf() < 0.28
		_flakes.append([rng.randf() * W, rng.randf() * H, rng.randf_range(9.0, 15.0) if near else rng.randf_range(4.0, 8.0),
			rng.randf() * TAU, 2 if near else 1, rng.randf_range(0.55, 0.9) if near else rng.randf_range(0.25, 0.55)])


func _process(delta: float) -> void:
	if not is_visible_in_tree() or Kit.reduced_motion():
		return
	_t += delta
	for f in _flakes:
		f[1] += f[2] * delta
		f[0] += sin(_t * 0.6 + f[3]) * 2.2 * delta * (1.6 if f[4] == 2 else 1.0) + 1.3 * delta
		if f[1] > H + 2:
			f[1] = -2.0
			f[0] = fposmod(f[0] + 97.0, float(W))
		if f[0] > W + 2:
			f[0] -= W + 4
	queue_redraw()


func _draw() -> void:
	for f in _flakes:
		var s: int = f[4] * PX
		var p := Vector2(floorf(f[0]) * PX, floorf(f[1]) * PX)
		draw_rect(Rect2(p, Vector2(s, s)), Color(0.86, 0.9, 0.88, f[5]))
