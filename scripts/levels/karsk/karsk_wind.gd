extends "res://scripts/levels/karsk/karsk_actor.gd"
## Wind gusts for Karsk: every 9–20 s a gust (≈3.5 s) blows spindrift along the ground band and off the roof
## edges listed in `roofs`, plays a gust sound and raises the shared `gust` value (0..1) that the laundry,
## the mitten and the cache cloth read (preload this script and read `Wind.gust`).
## Pixel-crisp: 1–2 px opaque streaks in snow colours, drawn in world space just under the falling snow (z 39).

static var gust := 0.0          ## current gust strength 0..1 (shared)
static var t_global := 0.0      ## seconds since the wind actor started (shared phase for idle sway)

var roofs: Array = []           ## [[x0, x1, y], ...] world-space roof edges that shed snow in gusts
var min_gap := 9.0
var max_gap := 20.0

const COLS := [Color("#F1F4EC"), Color("#DEE5DC"), Color("#C4CFC8"), Color("#A3B1AD")]
const DURATION := 3.6

var _next := 4.0
var _t_gust := -1.0
var _parts: Array = []          # [{p: Vector2, v: Vector2, age, life, len}]
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	z_index = 39
	light_mask = 0
	_rng.seed = 6411
	gust = 0.0
	t_global = 0.0
	_next = _rng.randf_range(3.0, 6.0)


func _exit_tree() -> void:
	gust = 0.0


func _tick(delta: float) -> void:
	t_global += delta
	var rm := reduced_motion()
	# --- gust envelope
	if _t_gust < 0.0:
		_next -= delta
		if _next <= 0.0:
			_t_gust = 0.0
			sfx("karsk_wind_gust", -9.0, 0.12)
	else:
		_t_gust += delta
		if _t_gust >= DURATION:
			_t_gust = -1.0
			_next = _rng.randf_range(min_gap, max_gap)
	var env := 0.0
	if _t_gust >= 0.0:
		var t := _t_gust
		env = clampf(t / 0.6, 0.0, 1.0) if t < 0.6 else (1.0 if t < 2.2 else clampf(1.0 - (t - 2.2) / 1.4, 0.0, 1.0))
		env *= 0.85 + 0.15 * sin(t * 9.0)
	gust = env
	# --- spawn particles (world space; this node stays at the origin)
	var c := cam_pos()
	var rate := (6.0 + 260.0 * env) * (0.5 if rm else 1.0)
	var n := int(rate * delta + _rng.randf())
	for i in n:
		# ground spindrift: a low band over the tracks and the platform, densest near the ground
		var yy := 352.0 - pow(_rng.randf(), 1.8) * 92.0
		var p := Vector2(c.x + _rng.randf_range(-80.0, 600.0), yy)
		var sp := _rng.randf_range(80.0, 170.0) * (0.3 + env)
		_parts.append({"p": p, "v": Vector2(sp, _rng.randf_range(-5.0, 4.0)), "age": 0.0,
			"life": _rng.randf_range(0.6, 1.5), "len": 1 + int(env * 5.0 * _rng.randf())})
	if env > 0.25 and not roofs.is_empty():
		var m := int((90.0 * env) * delta * (0.5 if rm else 1.0) + _rng.randf())
		for i in m:
			var r: Array = roofs[_rng.randi() % roofs.size()]
			var x := _rng.randf_range(float(r[0]), float(r[1]))
			if x < c.x - 20.0 or x > c.x + 660.0:
				continue
			_parts.append({"p": Vector2(x, float(r[2]) - _rng.randf_range(0.0, 2.0)),
				"v": Vector2(_rng.randf_range(40.0, 90.0) * env, _rng.randf_range(6.0, 22.0)), "age": 0.0,
				"life": _rng.randf_range(0.8, 1.8), "len": 1})
	# --- integrate
	var keep: Array = []
	for q in _parts:
		q["age"] += delta
		if q["age"] >= q["life"]:
			continue
		var v: Vector2 = q["v"]
		v.y += 10.0 * delta
		q["v"] = v
		q["p"] = (q["p"] as Vector2) + v * delta
		keep.append(q)
	if keep.size() > 600:
		keep = keep.slice(keep.size() - 600)
	_parts = keep
	queue_redraw()


func _draw() -> void:
	for q in _parts:
		var k: float = q["age"] / q["life"]
		var col: Color = COLS[mini(int(k * 3.2), 3)]
		var p: Vector2 = (q["p"] as Vector2).floor()
		draw_rect(Rect2(p, Vector2(int(q["len"]), 1)), col)
