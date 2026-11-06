extends "res://scripts/levels/karsk/karsk_actor.gd"
## Pigeons at the snowy rear edge of the Veltrava platform (exp_pigeons; find text: two of them tug at a
## sandwich from the delegation's provisions, a third waits at the edge until both are exhausted).
## They peck, bob, take a step and tug; a WALKING observer is tolerated (the find is "Tauben beobachten"),
## somebody running past inside `run_radius` or stepping right into them (`scare_radius`) makes the flock
## clatter up to the canopy girder (they vanish under the roof) and glide back down 16–28 s later.
## Sheet (tools/pixelgen/env_veltrava_station_life.py pigeon_sheet): 11 frames 12x10, feet at (5, 9),
## facing right. Base class: scripts/levels/karsk/karsk_actor.gd (parallax, texel material, sfx helpers).

var sprite := ""
var bread := ""
var bread_pos: Array = [476, 279]
var spots: Array = []               ## [[x, y], ...] world feet positions on the platform
var tuggers := 2                    ## the first n spots tug at the sandwich (they face each other)
var scare_radius := 13.0
var run_radius := 52.0
var roost_y := 26.0                 ## world y of the canopy girder they fly up to

const IDLE_A := 0
const IDLE_B := 1
const PECK_A := 2
const PECK_B := 3
const TUG := 4
const WALK := 5
const TAKEOFF := 6
const WINGS := [7, 8, 9, 8]
const GLIDE := 10
const CELL := Vector2(12, 10)

var _birds: Array = []
var _bread: Sprite2D
var _coo_t := 5.0
var _flap_cool := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 4807
	var tex := load_tex(sprite)
	if tex == null:
		push_warning("StationPigeons: missing sprite " + sprite)
		return
	var bt := load_tex(bread)
	if bt != null:
		_bread = make_strip(bt, 1)
		_bread.position = (Vector2(float(bread_pos[0]), float(bread_pos[1])) - position + Vector2(-3, -2)).round()
	for i in spots.size():
		var sp := Vector2(float(spots[i][0]), float(spots[i][1]))
		var s := make_strip(tex, 11)
		var face := 1
		if i < tuggers:
			face = 1 if sp.x < float(bread_pos[0]) else -1      # tuggers face the sandwich (and each other)
		elif sp.x > float(bread_pos[0]):
			face = -1
		var b := {"spr": s, "home": sp, "pos": sp, "state": "ground", "face": face, "t": 0.0,
			"next": _rng.randf_range(0.3, 2.0), "frame": IDLE_A, "vel": Vector2.ZERO, "tug": i < tuggers,
			"wobble": 0.0}
		_birds.append(b)
		_show(b, IDLE_A)


func _show(b: Dictionary, frame: int) -> void:
	var s: Sprite2D = b["spr"]
	b["frame"] = frame
	s.frame = frame
	s.flip_h = int(b["face"]) < 0
	s.offset = Vector2(-6.0 if s.flip_h else -5.0, -9.0)
	s.position = ((b["pos"] as Vector2) + Vector2(float(b["wobble"]), 0.0) - position).round()


func _tick(delta: float) -> void:
	if _birds.is_empty():
		return
	_flap_cool = maxf(0.0, _flap_cool - delta)
	var pp := player_pos()
	var running := player_speed() > 62.0
	var takeoff := false
	for b in _birds:
		var home: Vector2 = b["home"]
		var d := INF
		if pp != Vector2.INF:
			d = Vector2(pp.x - home.x, (pp.y - home.y) * 1.4).length()
		match String(b["state"]):
			"ground":
				if d < scare_radius or (running and d < run_radius):
					b["state"] = "alarm"
					b["t"] = _rng.randf_range(0.0, 0.35)
					b["face"] = -1 if pp.x > home.x else 1
					_show(b, IDLE_B)
				else:
					_ground(b, delta)
			"alarm":
				b["t"] = float(b["t"]) - delta
				if float(b["t"]) <= 0.0:
					b["state"] = "fly"
					b["t"] = 0.0
					b["wobble"] = 0.0
					b["vel"] = Vector2(float(b["face"]) * _rng.randf_range(18.0, 34.0), -_rng.randf_range(70.0, 95.0))
					takeoff = true
			"fly":
				b["t"] = float(b["t"]) + delta
				var v: Vector2 = b["vel"]
				v = v.lerp(Vector2(float(b["face"]) * 40.0, -70.0), 1.4 * delta)
				b["vel"] = v
				b["pos"] = (b["pos"] as Vector2) + v * delta
				var t: float = b["t"]
				_show(b, TAKEOFF if t < 0.1 else WINGS[int(t * 14.0) % 4])
				if (b["pos"] as Vector2).y < roost_y + 4.0 or t > 5.0:
					b["state"] = "away"
					b["t"] = _rng.randf_range(16.0, 28.0)
					(b["spr"] as Sprite2D).visible = false
			"away":
				b["t"] = float(b["t"]) - delta
				if float(b["t"]) <= 0.0:
					if d > scare_radius * 2.5 and not running:
						var side := -1.0 if _rng.randf() < 0.5 else 1.0
						b["pos"] = home + Vector2(side * _rng.randf_range(40.0, 90.0), roost_y - home.y + 2.0)
						b["face"] = -1 if side > 0.0 else 1
						b["vel"] = Vector2(-side * 30.0, 40.0)
						b["state"] = "return"
						b["t"] = 0.0
						(b["spr"] as Sprite2D).visible = true
					else:
						b["t"] = 2.0
			"return":
				b["t"] = float(b["t"]) + delta
				if d < scare_radius or (running and d < run_radius):
					b["state"] = "fly"
					b["t"] = 0.2
					continue
				var to := home - (b["pos"] as Vector2)
				var dist := to.length()
				if dist < 1.5:
					b["pos"] = home
					b["state"] = "ground"
					b["face"] = _home_face(b)
					b["next"] = _rng.randf_range(0.5, 1.5)
					_show(b, IDLE_A)
					continue
				var speed := clampf(dist * 2.2, 14.0, 70.0)
				var v2: Vector2 = (b["vel"] as Vector2).lerp(to.normalized() * speed, 3.0 * delta)
				b["vel"] = v2
				b["pos"] = (b["pos"] as Vector2) + v2 * delta
				if absf(v2.x) > 1.0:
					b["face"] = 1 if v2.x > 0.0 else -1
				_show(b, GLIDE if dist < 22.0 else WINGS[int(float(b["t"]) * 12.0) % 4])
	if takeoff and _flap_cool <= 0.0:
		_flap_cool = 2.5
		var mid: Vector2 = _birds[0]["home"]
		if on_screen(mid, 40.0):
			sfx("berlin_pigeon_flutter", dist_db(mid, -6.0, -20.0), 0.08)
	_coo_t -= delta
	if _coo_t <= 0.0:
		_coo_t = _rng.randf_range(8.0, 17.0)
		var any_down := false
		for b in _birds:
			if String(b["state"]) == "ground":
				any_down = true
		var m2: Vector2 = _birds[0]["home"]
		if any_down and on_screen(m2, 20.0):
			sfx("berlin_pigeon_coo", dist_db(m2, -14.0, -26.0), 0.08)


func _home_face(b: Dictionary) -> int:
	var home: Vector2 = b["home"]
	if bool(b["tug"]):
		return 1 if home.x < float(bread_pos[0]) else -1
	return -1 if home.x > float(bread_pos[0]) else 1


## Ground routine: tuggers alternate tug / peck at the sandwich with a pixel of back-and-forth, the others
## peck, bob, take a step or turn round now and then.
func _ground(b: Dictionary, delta: float) -> void:
	b["next"] = float(b["next"]) - delta
	if bool(b["tug"]):
		var ph := fmod(float(b["t"]) + delta, 10.0)
		b["t"] = ph
		var pull := sin(ph * 5.5 + (0.0 if int(b["face"]) > 0 else 1.7))
		b["wobble"] = -float(b["face"]) * (1.0 if pull > 0.35 else 0.0)
		_show(b, TUG if pull > -0.2 else PECK_B)
		return
	if float(b["next"]) > 0.0:
		return
	b["next"] = _rng.randf_range(0.5, 2.2)
	var r := _rng.randf()
	if r < 0.35:
		_show(b, PECK_A if _rng.randf() < 0.5 else PECK_B)
	elif r < 0.6:
		_show(b, IDLE_B)
	elif r < 0.8:
		_show(b, IDLE_A)
	elif r < 0.92:
		var step := float(b["face"]) * 2.0
		var hp: Vector2 = b["home"]
		var np: Vector2 = (b["pos"] as Vector2) + Vector2(step, 0)
		if absf(np.x - hp.x) <= 4.0:
			b["pos"] = np
		_show(b, WALK)
	else:
		b["face"] = -int(b["face"])
		_show(b, IDLE_A)
