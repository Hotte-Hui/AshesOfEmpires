extends Node2D
## Deterministic snowfall for the finale montage (owner: trans-finale).
## Every flake's position is a pure function of the montage time, so the montage can be seeked and
## captured frame-exactly.  Flakes are 1 px (far) or 2 px (near) squares on whole pixels, drawn inside
## `rect` (world px of the set).  Two depths: far flakes are smaller, slower and darker.
## `density` (0..1+) scales how many flakes are visible -- the snow veil transition raises it.

var rect := Rect2(0, 0, 640, 360)
var count := 120
var seed_value := 1
var speed := Vector2(9.0, 20.0)       # px/s (min, max)
var sway := 3.0                       # px
var wind := -3.0                      # px/s sideways drift
var colors: Array[Color] = [Color("#8F8A92"), Color("#D2CCCB")]
var near_ratio := 0.3
var density := 1.0
var time := 0.0
var _flakes: Array = []               # [x0, y0, speed, phase, freq, near]


func setup(d: Dictionary) -> void:
	var r: Array = d.get("rect", [0, 0, 640, 360])
	rect = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
	count = int(d.get("count", 120))
	seed_value = int(d.get("seed", 1))
	var sp: Array = d.get("speed", [9, 20])
	speed = Vector2(float(sp[0]), float(sp[1]))
	sway = float(d.get("sway", 3.0))
	wind = float(d.get("wind", -3.0))
	near_ratio = float(d.get("near", 0.3))
	density = float(d.get("density", 1.0))
	var cols: Array = d.get("colors", [])
	if not cols.is_empty():
		colors.clear()
		for c in cols:
			colors.append(Color(str(c)))
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	_flakes.clear()
	for i in count:
		var near := rng.randf() < near_ratio
		_flakes.append([rng.randf() * rect.size.x, rng.randf() * rect.size.y,
			rng.randf_range(speed.x, speed.y) * (1.35 if near else 1.0), rng.randf() * TAU,
			rng.randf_range(0.6, 1.4), near, rng.randf()])


func set_time(t: float) -> void:
	time = t
	queue_redraw()


func _draw() -> void:
	if _flakes.is_empty():
		return
	var w := rect.size.x
	var h := rect.size.y
	var far_c: Color = colors[0]
	var near_c: Color = colors[colors.size() - 1]
	for f in _flakes:
		if float(f[6]) > density:
			continue
		var near: bool = f[5]
		var y := fposmod(float(f[1]) + float(f[2]) * time, h)
		var x := fposmod(float(f[0]) + wind * time * (1.3 if near else 1.0) \
			+ sin(float(f[3]) + time * float(f[4])) * sway, w)
		var p := Vector2(floorf(rect.position.x + x), floorf(rect.position.y + y))
		if near:
			draw_rect(Rect2(p, Vector2(2, 2)), near_c)
		else:
			draw_rect(Rect2(p, Vector2(1, 1)), far_c)
