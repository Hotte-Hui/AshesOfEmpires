extends Node2D
## The platform clock of the Ostbahnhof, Korridorbahnsteig K (L_C4P2_BerlinA, exp_station_clock): the dial is baked
## into the station layer (tools/pixelgen/env_c4p2_berlin_station.py), this actor draws the hands as crisp 1-px
## pixel lines into a tiny image -- the minute hand JUMPS once a minute like a slave clock of the station's master
## clock, the slim red second hand sweeps and waits a moment at the top before the jump.  The time starts at
## `start` when the level opens (20.31 on Monday evening, C4P2_DESIGN §4.2) and runs in real time.
## Instanced by Level._spawn_actors from the scene.json "actors" entry (props: radius, start).  Purely decorative,
## deterministic, never touches Story or Explore.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")
const INK := Color("#141A21")
const RED := Color("#A8382E")

var radius := 7.0
var start := "20:31:12"
var second_hand := true

var _img: Image
var _tex: ImageTexture
var _hands: Sprite2D
var _t0_msec := -1
var _start_s := 0.0
var _last := -1


func _ready() -> void:
	z_index = -45
	var parts := start.split(":")
	_start_s = 0.0
	for i in parts.size():
		_start_s += float(parts[i]) * [3600.0, 60.0, 1.0][mini(i, 2)]
	_t0_msec = Time.get_ticks_msec()
	var n := int(ceil(radius)) * 2 + 3
	_img = Image.create(n, n, false, Image.FORMAT_RGBA8)
	_tex = ImageTexture.create_from_image(_img)
	_hands = Sprite2D.new()
	_hands.texture = _tex
	_hands.centered = false
	_hands.position = Vector2(-(n / 2), -(n / 2))
	add_child(_hands)
	_draw_hands(now())
	U.texel(_hands, global_position + _hands.position)


## Seconds since midnight shown on the dial right now.
func now() -> float:
	return _start_s + float(Time.get_ticks_msec() - _t0_msec) / 1000.0


func _process(_delta: float) -> void:
	var t := now()
	var key := int(floorf(t * 4.0))
	if key != _last:
		_last = key
		_draw_hands(t)


## The station clock's movement: the second hand runs a full turn in 58.5 s and rests at the top; the minute hand
## jumps on the full minute (so it always shows whole minutes).
func hand_angles(t: float) -> Dictionary:
	var secs: float = fmod(t, 43200.0)
	var whole_min: float = floorf(secs / 60.0)
	var in_min: float = secs - whole_min * 60.0
	return {"hour": fmod(whole_min / 720.0, 1.0) * TAU, "minute": fmod(whole_min, 60.0) / 60.0 * TAU,
		"second": minf(in_min / 58.5, 1.0) * TAU}


func _draw_hands(t: float) -> void:
	_img.fill(Color(0, 0, 0, 0))
	var c := Vector2(_img.get_width() / 2, _img.get_height() / 2)
	var a := hand_angles(t)
	_line(c, float(a["hour"]), radius * 0.5, INK)
	_line(c, float(a["minute"]), radius * 0.86, INK)
	if second_hand:
		_line(c, float(a["second"]), radius * 0.8, RED)
	_img.set_pixelv(Vector2i(c), INK)
	_tex.update(_img)


func _line(c: Vector2, ang: float, length: float, col: Color) -> void:
	var e := c + Vector2(sin(ang), -cos(ang)) * length
	var x0 := int(round(c.x))
	var y0 := int(round(c.y))
	var x1 := int(round(e.x))
	var y1 := int(round(e.y))
	var dx := absi(x1 - x0)
	var dy := -absi(y1 - y0)
	var sx := 1 if x0 < x1 else -1
	var sy := 1 if y0 < y1 else -1
	var err := dx + dy
	while true:
		if x0 >= 0 and y0 >= 0 and x0 < _img.get_width() and y0 < _img.get_height():
			_img.set_pixel(x0, y0, col)
		if x0 == x1 and y0 == y1:
			break
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			x0 += sx
		if e2 <= dx:
			err += dx
			y0 += sy
