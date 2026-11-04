extends "res://scripts/levels/karsk/karsk_actor.gd"
## Fire-barrel life, y-sorted with the barrel (node at its foot, base_y 304): flame tongues (fx strip),
## sparks that rise and drift with the wind (brighter in gusts), and the two workers' breath in the cold.
## The barrel prop itself (with the baked workers) and the flickering PointLight2D stay in scene.json.

const Wind := preload("res://scripts/levels/karsk/karsk_wind.gd")

var flames := ""
var flame_pos: Array = [975, 282]     ## world: flame strip origin (rim centre)
var mouths: Array = []                ## world points where the workers breathe out
var breath := ""                      ## breath puff strip (6 frames, square)
var fps := 10.0
var flame_frames := 8.0

const SPARK_COLS := [Color("#FBE3AE"), Color("#F0C487"), Color("#DCA16E"), Color("#BA775B")]

var _flame: Sprite2D
var _flame_glow: Sprite2D
var _sparks_node: Node2D
var _sparks: Array = []               # [{p, v, age, life}]
var _next_spark := 0.3
var _breath_tex: Texture2D
var _breath_next: Array = []
var _ft := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 975
	var origin := Vector2(float(flame_pos[0]), float(flame_pos[1]))
	var tex := load_tex(flames)
	if tex:
		var nf := int(flame_frames)
		_flame = make_strip(tex, nf, false)
		var cell := Vector2(tex.get_width() / float(nf), tex.get_height())
		_flame.position = (origin - position - Vector2(floorf(cell.x / 2.0), cell.y - 1.0)).round()
		_flame_glow = make_glow(flames, nf, 0.3)
		if _flame_glow:
			_flame_glow.position = _flame.position
	_sparks_node = Node2D.new()
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_sparks_node.material = mat
	_sparks_node.light_mask = 0
	add_child(_sparks_node)
	_sparks_node.draw.connect(_draw_sparks)
	_breath_tex = load_tex(breath)
	for i in mouths.size():
		_breath_next.append(_rng.randf_range(0.5, 3.5) + i * 1.7)


func _tick(delta: float) -> void:
	_ft += delta
	var f := int(_ft * fps) % maxi(1, int(flame_frames))
	if _flame:
		_flame.frame = f
	if _flame_glow:
		_flame_glow.frame = f
	# --- sparks
	var g: float = Wind.gust
	var rm := reduced_motion()
	_next_spark -= delta * (1.0 + g * 2.5)
	if _next_spark <= 0.0:
		_next_spark = _rng.randf_range(0.25, 0.9) * (1.6 if rm else 1.0)
		var origin := Vector2(float(flame_pos[0]), float(flame_pos[1])) - position
		for i in _rng.randi_range(1, 3):
			_sparks.append({"p": origin + Vector2(_rng.randf_range(-5.0, 5.0), -_rng.randf_range(4.0, 9.0)),
				"v": Vector2(_rng.randf_range(-4.0, 9.0), -_rng.randf_range(16.0, 30.0)), "age": 0.0,
				"life": _rng.randf_range(1.0, 2.2)})
	var keep: Array = []
	for s in _sparks:
		s["age"] += delta
		if s["age"] >= s["life"]:
			continue
		var v: Vector2 = s["v"]
		v.x += (6.0 + 40.0 * g) * delta + sin(float(s["age"]) * 7.0) * 10.0 * delta
		v.y *= pow(0.6, delta)
		s["v"] = v
		s["p"] = (s["p"] as Vector2) + v * delta
		keep.append(s)
	_sparks = keep
	_sparks_node.queue_redraw()
	# --- breath of the workers
	for i in mouths.size():
		_breath_next[i] -= delta
		if _breath_next[i] <= 0.0:
			_breath_next[i] = _rng.randf_range(3.2, 5.4)
			var m := Vector2(float(mouths[i][0]), float(mouths[i][1])) - position
			spawn_puff(_breath_tex, 6, m + Vector2(2, -1), Vector2(_rng.randf_range(5.0, 9.0) + g * 20.0, -6.0), 1.3)


func _draw_sparks() -> void:
	for s in _sparks:
		var k: float = s["age"] / s["life"]
		var c: Color = SPARK_COLS[mini(int(k * 4.0), 3)]
		_sparks_node.draw_rect(Rect2((s["p"] as Vector2).floor(), Vector2.ONE), c)
