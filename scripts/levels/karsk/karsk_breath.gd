extends "res://scripts/levels/karsk/karsk_actor.gd"
## Breath clouds of people baked into the Karsk art (family on the platform, tea vendor in the hatch):
## every few seconds a tiny pale puff leaves each mouth point and drifts off with the wind.
## Place the node at the y of the figures it belongs to (y-sorting) or give it an absolute `z`.

const Wind := preload("res://scripts/levels/karsk/karsk_wind.gd")

var points: Array = []          ## world points (mouths)
var sprite := ""                ## square puff strip (6 frames)
var interval := 4.5

var _tex: Texture2D
var _next: Array = []
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = int(position.x) * 31 + int(position.y)
	_tex = load_tex(sprite)
	for i in points.size():
		_next.append(_rng.randf_range(0.4, interval) + i * 1.3)


func _tick(delta: float) -> void:
	if _tex == null:
		return
	for i in points.size():
		_next[i] -= delta
		if _next[i] <= 0.0:
			_next[i] = interval * _rng.randf_range(0.75, 1.3)
			var m := Vector2(float(points[i][0]), float(points[i][1])) - position
			if on_screen(m + position, 30.0):
				spawn_puff(_tex, 6, m + Vector2(1, -1), Vector2(_rng.randf_range(4.0, 8.0) + Wind.gust * 18.0, -5.0), 1.2)
