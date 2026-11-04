extends "res://scripts/levels/karsk/karsk_actor.gd"
## A goods train passing on the far embankment (mid plane, parallax 0.45) about every 40–50 s, alternating
## direction: steam locomotive with tender + 6–9 mixed wagons, a lingering smoke plume, a distant rumble and
## whistle.
## Positions are layer coordinates at camera x 0 (like scene.json layer "pos"); `home` y is the rail.

var loco := ""
var wagons: Array = []
var puff := ""
var span: Array = [-40.0, 1010.0]       ## layer x range the train travels through (beyond the visible band)
var speed := 34.0                       ## layer px / s
var interval: Array = [36.0, 48.0]      ## start-to-start seconds
var first_delay := 5.0
var chimney: Array = [5.0, -14.0]       ## chimney top relative to the loco's front end / the rail
var wagons_min := 6.0
var wagons_max := 9.0

var _cars: Node2D
var _sprites: Array = []
var _loco_spr: Sprite2D
var _puff_tex: Texture2D
var _wag_tex: Array = []
var _loco_tex: Texture2D
var _dir := -1.0                        ## -1 = moving left (loco art faces left)
var _x := 0.0
var _len := 0.0
var _active := false
var _wait := 5.0
var _puff_t := 0.0
var _run := 0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 4040
	_loco_tex = load_tex(loco)
	for w in wagons:
		var t := load_tex(str(w))
		if t:
			_wag_tex.append(t)
	_puff_tex = load_tex(puff)
	_cars = Node2D.new()
	add_child(_cars)
	_wait = first_delay


func _tick(delta: float) -> void:
	if _loco_tex == null:
		return
	if not _active:
		_wait -= delta
		if _wait <= 0.0:
			_start()
		return
	_x += _dir * speed * delta
	_cars.position = Vector2(_x, 0).round()
	# smoke: puffs stay in layer space (left behind by the moving loco) and drift with the wind
	_puff_t -= delta
	if _puff_t <= 0.0 and _puff_tex:
		_puff_t = 0.2
		var cx := float(chimney[0])
		var mouth := Vector2(_x + (cx if _dir < 0.0 else _len - 1.0 - cx), float(chimney[1]))
		spawn_puff(_puff_tex, 8, mouth, Vector2(8.0 - _dir * 5.0, -11.0), 3.8)
	var done := (_dir < 0.0 and _x + _len < float(span[0])) or (_dir > 0.0 and _x > float(span[1]))
	if done:
		_active = false
		_cars.visible = false
		_wait = _rng.randf_range(float(interval[0]), float(interval[1])) - (float(span[1]) - float(span[0]) + _len) / speed
		_wait = maxf(_wait, 8.0)


func _start() -> void:
	_run += 1
	_dir = -1.0 if _run % 2 == 1 else 1.0
	for s in _sprites:
		(s as Node).queue_free()
	_sprites.clear()
	# consist: loco + wagons (deterministic per run)
	var parts: Array = [_loco_tex]
	var n := _rng.randi_range(int(wagons_min), int(wagons_max))
	for i in n:
		parts.append(_wag_tex[_rng.randi() % _wag_tex.size()] if not _wag_tex.is_empty() else _loco_tex)
	if _dir > 0.0:
		parts.reverse()                 # moving right: the loco leads at the right end
	var x := 0.0
	for t in parts:
		var s := Sprite2D.new()
		s.texture = t
		s.centered = false
		s.flip_h = _dir > 0.0
		s.position = Vector2(x, -t.get_height() + 1)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_cars.add_child(s)
		texel(s)
		_sprites.append(s)
		x += t.get_width() - 1
	_len = x
	_x = float(span[1]) if _dir < 0.0 else float(span[0]) - _len
	if _run == 1:
		# the first train enters the current view right away (players should notice it early)
		var view_x := cam_pos().x * parallax
		_x = minf(_x, view_x + 650.0)
	_cars.position = Vector2(_x, 0).round()
	_cars.visible = true
	_active = true
	_puff_t = 0.0
	sfx("karsk_train_far", -15.0, 0.04)
