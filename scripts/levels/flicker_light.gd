extends PointLight2D
## Subtle, accessibility-safe flicker for practical lights (fire barrels, tired bulbs). Never strobes.

var base_energy := 1.0
var flicker := 0.0
var _t := 0.0
var _noise := FastNoiseLite.new()


func _ready() -> void:
	_noise.seed = randi()
	_noise.frequency = 1.7
	_t = randf() * 100.0


func _process(delta: float) -> void:
	if flicker <= 0.0:
		return
	_t += delta
	var amt := flicker * (0.35 if Settings.get_value("reduced_motion") else 1.0)
	energy = base_energy * (1.0 + _noise.get_noise_1d(_t * 6.0) * amt)
