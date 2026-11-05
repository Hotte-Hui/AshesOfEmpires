extends "res://scripts/levels/karsk/karsk_actor.gd"
## Hooded crows on the PA cable between the signal box and the loudspeaker pole (exp_crows).
## Idle: breathe, look round, preen, caw. Player within `nervous_radius`: they turn to watch, hop and caw.
## Player within `scare_radius` (or running inside `nervous_radius`): they take off one after another, flap
## away out of the frame and come back to their perches 22–40 s later once the player has moved off.
## Frames (env_karsk_sprites.CROW_FRAMES): idle_a, idle_b, look, caw, preen, hop, takeoff, fly_up, fly_mid,
## fly_down, glide — cell 14x12, feet at (6, 11), facing right.

var perches: Array = []         ## [[x, y], ...] world points on the cable (feet)
var sprite := ""
var scare_radius := 34.0
var nervous_radius := 80.0
var return_min := 22.0
var return_max := 40.0

const IDLE_A := 0
const IDLE_B := 1
const LOOK := 2
const CAW := 3
const PREEN := 4
const HOP := 5
const TAKEOFF := 6
const WINGS := [7, 8, 9, 8]
const GLIDE := 10
const GROUND_Y := 256.0         ## y of the back strip under the cable (distance anchor)

var _crows: Array = []
var _caw_cool := 2.0
var _flap_cool := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 2207
	var tex := canvas_tex(sprite, true)
	if tex == null:
		push_warning("KarskCrows: missing sprite " + sprite)
		return
	for i in perches.size():
		var pp := Vector2(float(perches[i][0]), float(perches[i][1]))
		var s := make_strip(tex, 11)
		var c := {"spr": s, "perch": pp, "pos": pp, "state": "perch", "act": "", "act_t": 0.0,
			"next": _rng.randf_range(0.6, 3.5), "face": 1 if i % 2 == 0 else -1, "vel": Vector2.ZERO,
			"t": 0.0, "delay": 0.0, "lift": 0.0}
		_crows.append(c)
		_show(c, IDLE_A)


func _show(c: Dictionary, frame: int) -> void:
	var s: Sprite2D = c["spr"]
	s.frame = frame
	s.flip_h = int(c["face"]) < 0
	s.offset = Vector2(-7.0 if s.flip_h else -6.0, -11.0)
	s.position = ((c["pos"] as Vector2) + Vector2(0, -float(c["lift"])) - position).round()


func _tick(delta: float) -> void:
	if _crows.is_empty():
		return
	_caw_cool = maxf(0.0, _caw_cool - delta)
	_flap_cool = maxf(0.0, _flap_cool - delta)
	var pp := player_pos()
	var running := player_speed() > 62.0
	var any_takeoff := false
	for c in _crows:
		var st: String = c["state"]
		var perch: Vector2 = c["perch"]
		var d := INF
		if pp != Vector2.INF:
			d = Vector2(pp.x - perch.x, (pp.y - GROUND_Y) * 0.8).length()
		match st:
			"perch":
				if d < scare_radius or (running and d < nervous_radius):
					c["state"] = "alarm"
					c["delay"] = _rng.randf_range(0.0, 0.5)
					c["face"] = -1 if pp.x > perch.x else 1     # turn away from the player
					_show(c, LOOK)
				else:
					_idle(c, delta, d < nervous_radius, pp)
			"alarm":
				c["delay"] = float(c["delay"]) - delta
				if float(c["delay"]) <= 0.0:
					c["state"] = "fly"
					c["t"] = 0.0
					c["lift"] = 0.0
					c["vel"] = Vector2(float(c["face"]) * 22.0, -48.0)
					any_takeoff = true
			"fly":
				c["t"] = float(c["t"]) + delta
				var v: Vector2 = c["vel"]
				v = v.lerp(Vector2(float(c["face"]) * 90.0, -34.0), 1.6 * delta)
				c["vel"] = v
				c["pos"] = (c["pos"] as Vector2) + v * delta
				var t: float = c["t"]
				_show(c, TAKEOFF if t < 0.12 else WINGS[int(t * 12.0) % 4])
				var cp := cam_pos()
				var p: Vector2 = c["pos"]
				if p.y < cp.y - 30.0 or p.x < cp.x - 50.0 or p.x > cp.x + 690.0 or t > 8.0:
					c["state"] = "away"
					c["t"] = _rng.randf_range(return_min, return_max)
					(c["spr"] as Sprite2D).visible = false
			"away":
				c["t"] = float(c["t"]) - delta
				if float(c["t"]) <= 0.0:
					if d > nervous_radius + 40.0:
						var side := -1.0 if _rng.randf() < 0.5 else 1.0
						c["pos"] = perch + Vector2(side * _rng.randf_range(200.0, 260.0), -_rng.randf_range(110.0, 150.0))
						c["face"] = -1 if side > 0 else 1
						c["vel"] = Vector2(-side * 60.0, 30.0)
						c["state"] = "return"
						c["t"] = 0.0
						(c["spr"] as Sprite2D).visible = true
					else:
						c["t"] = 1.0
			"return":
				c["t"] = float(c["t"]) + delta
				var to := perch - (c["pos"] as Vector2)
				var dist := to.length()
				if d < scare_radius:              # spooked again on the way in
					c["state"] = "fly"
					c["t"] = 0.2
					c["face"] = -1 if pp.x > perch.x else 1
					continue
				if dist < 1.5:
					c["pos"] = perch
					c["state"] = "perch"
					c["act"] = "land"
					c["act_t"] = 0.25
					c["next"] = _rng.randf_range(1.0, 3.0)
					_show(c, HOP)
					continue
				var speed := clampf(dist * 2.4, 16.0, 75.0)
				var v2: Vector2 = (c["vel"] as Vector2).lerp(to.normalized() * speed, 3.0 * delta)
				c["vel"] = v2
				c["pos"] = (c["pos"] as Vector2) + v2 * delta
				if absf(v2.x) > 1.0:
					c["face"] = 1 if v2.x > 0.0 else -1
				_show(c, GLIDE if dist < 34.0 else WINGS[int(float(c["t"]) * 11.0) % 4])
	if any_takeoff and _flap_cool <= 0.0:
		_flap_cool = 3.0
		var mid: Vector2 = _crows[_crows.size() / 2]["perch"]
		if on_screen(mid, 40.0):
			sfx("karsk_crow_flap", dist_db(mid, -5.0, -18.0))
			if _caw_cool <= 0.0:
				_caw_cool = 1.5
				sfx("karsk_crow_caw", dist_db(mid, -7.0, -20.0), 0.1)


func _idle(c: Dictionary, delta: float, nervous: bool, pp: Vector2) -> void:
	c["lift"] = 0.0
	if String(c["act"]) != "":
		c["act_t"] = float(c["act_t"]) - delta
		if String(c["act"]) == "hop":
			var k := 1.0 - clampf(float(c["act_t"]) / 0.3, 0.0, 1.0)
			c["lift"] = round(sin(k * PI) * 3.0)
		if float(c["act_t"]) <= 0.0:
			c["act"] = ""
			_show(c, IDLE_A)
		else:
			return
	c["next"] = float(c["next"]) - delta * (2.2 if nervous else 1.0)
	if float(c["next"]) > 0.0:
		return
	c["next"] = _rng.randf_range(1.2, 4.5)
	if nervous and pp != Vector2.INF:
		c["face"] = 1 if pp.x > (c["perch"] as Vector2).x else -1
	var r := _rng.randf()
	var act := "breathe"
	if nervous:
		act = "hop" if r < 0.35 else ("caw" if r < 0.6 else "look")
	else:
		if r < 0.38:
			act = "breathe"
		elif r < 0.62:
			act = "look"
		elif r < 0.8:
			act = "preen"
		elif r < 0.9:
			act = "caw"
		else:
			act = "turn"
	match act:
		"breathe":
			c["act"] = act
			c["act_t"] = 0.5
			_show(c, IDLE_B)
		"look":
			c["act"] = act
			c["act_t"] = _rng.randf_range(0.7, 1.8)
			_show(c, LOOK)
		"preen":
			c["act"] = act
			c["act_t"] = _rng.randf_range(0.8, 1.6)
			_show(c, PREEN)
		"hop":
			c["act"] = act
			c["act_t"] = 0.3
			_show(c, HOP)
		"turn":
			c["face"] = -int(c["face"])
			_show(c, IDLE_A)
		"caw":
			c["act"] = act
			c["act_t"] = 0.4
			_show(c, CAW)
			var perch: Vector2 = c["perch"]
			if _caw_cool <= 0.0 and on_screen(perch, 60.0):
				_caw_cool = _rng.randf_range(2.5, 5.0)
				sfx("karsk_crow_caw", dist_db(perch, -9.0, -22.0), 0.1)
