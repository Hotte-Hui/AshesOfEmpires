extends Node2D
## Pigeons on the OUTSIDE sill of a window (exp_pigeons).  Drawn at z -59: behind the room layer (z -50) and
## in front of the outer sill layer (z -60), so they are only seen through the glass.  They bob, peck, ruffle
## and coo; when the player comes close to the window they flutter off upward (out of sight behind the wall
## above the window) and come back after a while once the player has moved on.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")
const CELL := Vector2i(12, 10)
const F := {"idle_a": 0, "idle_b": 1, "peck_a": 2, "peck_b": 3, "ruffle": 4, "turn": 5,
	"fly1": 6, "fly2": 7, "fly3": 8, "fly4": 9}

@export var sheet_path := ""
@export var count := 3
@export var span := 30.0              ## sill length the birds use (px, from the node position to the right)
@export var scare_distance := 44.0
@export var coo_path := ""
@export var flutter_path := ""

var birds: Array = []                 # [{spr, x, state, t, fly_t, home_x, flip}]
var present := true
var _away_t := 0.0
var _coo_t := 6.0
var _coo: AudioStreamPlayer2D
var _flutter: AudioStreamPlayer2D
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	z_index = -59
	_rng.seed = 7411
	var tex := U.tex(sheet_path)
	for i in count:
		var s := Sprite2D.new()
		s.texture = tex
		s.hframes = 10
		s.centered = false
		s.light_mask = 0
		add_child(s)
		U.texel(s, Vector2.ZERO, Vector2(CELL))
		var hx := span * (float(i) + 0.5) / float(count) + _rng.randf_range(-3.0, 3.0)
		var b := {"spr": s, "x": hx, "home_x": hx, "state": "idle", "t": _rng.randf_range(0.2, 2.0),
			"fly_t": 0.0, "flip": _rng.randf() < 0.5, "y": 0.0, "vx": 0.0}
		birds.append(b)
		_place(b, "idle_a")
	_coo = U.make_sound(self, coo_path, -14.0, 320.0, 1.6)
	_flutter = U.make_sound(self, flutter_path, -8.0, 420.0, 1.4)


func _place(b: Dictionary, frame: String) -> void:
	var s: Sprite2D = b["spr"]
	s.frame = F.get(frame, 0)
	s.flip_h = b["flip"]
	s.position = Vector2(roundf(b["x"]) - CELL.x * 0.5, roundf(b["y"]) - CELL.y + 1)


func _process(delta: float) -> void:
	var pp = U.player_pos(self)
	var near := pp != null and absf((pp as Vector2).x - (global_position.x + span * 0.5)) < scare_distance
	if present and near:
		_take_off()
	elif not present:
		_away_t -= delta
		if _away_t <= 0.0 and not near:
			_return()
	for b in birds:
		_step_bird(b, delta)
	if present:
		_coo_t -= delta
		if _coo_t <= 0.0:
			_coo_t = _rng.randf_range(7.0, 18.0)
			if _coo:
				_coo.pitch_scale = _rng.randf_range(0.92, 1.08)
				_coo.play()


func _take_off() -> void:
	present = false
	_away_t = _rng.randf_range(22.0, 38.0)
	for b in birds:
		b["state"] = "fly_off"
		b["fly_t"] = _rng.randf_range(0.0, 0.25)
		b["vx"] = _rng.randf_range(-14.0, 14.0)
	if _flutter:
		_flutter.play()


func _return() -> void:
	present = true
	for b in birds:
		b["state"] = "fly_in"
		b["fly_t"] = _rng.randf_range(0.0, 0.8)
		b["y"] = -70.0 - _rng.randf_range(0.0, 20.0)
		b["x"] = float(b["home_x"]) + _rng.randf_range(-10.0, 10.0)
	_coo_t = _rng.randf_range(3.0, 8.0)


func _step_bird(b: Dictionary, delta: float) -> void:
	var st: String = b["state"]
	if st == "fly_off":
		b["fly_t"] = float(b["fly_t"]) - delta
		if float(b["fly_t"]) > 0.0:
			_place(b, "ruffle")
			return
		b["y"] = float(b["y"]) - 52.0 * delta
		b["x"] = float(b["x"]) + float(b["vx"]) * delta
		var ph := int(Time.get_ticks_msec() / 70) % 4
		_place(b, "fly%d" % (ph + 1))
		if float(b["y"]) < -90.0:
			b["state"] = "away"
			(b["spr"] as Sprite2D).visible = false
		return
	if st == "away":
		return
	if st == "fly_in":
		(b["spr"] as Sprite2D).visible = true
		b["fly_t"] = float(b["fly_t"]) - delta
		if float(b["fly_t"]) > 0.0:
			(b["spr"] as Sprite2D).visible = false
			return
		b["x"] = lerpf(float(b["x"]), float(b["home_x"]), minf(1.0, delta * 2.0))
		b["y"] = minf(0.0, float(b["y"]) + 46.0 * delta)
		var ph := int(Time.get_ticks_msec() / 80) % 4
		_place(b, "fly%d" % (ph + 1))
		if float(b["y"]) >= 0.0:
			b["state"] = "idle"
			b["t"] = _rng.randf_range(0.5, 1.5)
		return
	# idle behaviours on the sill
	b["t"] = float(b["t"]) - delta
	if float(b["t"]) <= 0.0:
		var r := _rng.randf()
		if r < 0.35:
			b["state"] = "peck"
			b["t"] = _rng.randf_range(0.6, 1.4)
		elif r < 0.5:
			b["state"] = "ruffle"
			b["t"] = 0.35
		elif r < 0.65:
			b["flip"] = not b["flip"]
			b["state"] = "turn"
			b["t"] = 0.2
		elif r < 0.78:
			b["x"] = clampf(float(b["x"]) + (2.0 if not b["flip"] else -2.0), 2.0, span - 2.0)
			b["state"] = "idle"
			b["t"] = _rng.randf_range(0.4, 1.0)
		else:
			b["state"] = "idle"
			b["t"] = _rng.randf_range(1.0, 3.5)
	match str(b["state"]):
		"peck":
			_place(b, "peck_a" if (int(Time.get_ticks_msec() / 160) % 2) == 0 else "peck_b")
		"ruffle":
			_place(b, "ruffle")
		"turn":
			_place(b, "turn")
		_:
			_place(b, "idle_a" if (int(Time.get_ticks_msec() / 900) % 3) != 2 else "idle_b")
