extends Node2D
## A working wall clock (exp_clock: the regulator in the arrival hall; also the small office clock).
## The dial is baked into the room layer; this actor draws the hands as crisp 1-px pixel lines into a tiny image
## once per second, swings the pendulum and plays tick / tock and a soft chime every quarter hour.  Both clocks
## share one time: the afternoon of the scene, starting a few seconds before a quarter so a first-time visitor
## hears the chime.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")
const START_SECONDS := 16 * 3600 + 13 * 60 + 50     # 16:13:50 when the level opens
const INK := Color("#1A1C2A")
const RED := Color("#A8382E")
const BRASS := Color("#D79A62")

@export var radius := 8.0
@export var second_hand := true
@export var pendulum_path := ""
@export var pendulum_frames := 12
@export var pendulum_offset := [0, 0]
@export var pendulum_period := 2.0
@export var tick_path := ""
@export var tock_path := ""
@export var chime_path := ""

static var _t0_msec := -1

var _img: Image
var _tex: ImageTexture
var _hands: Sprite2D
var _pend: Sprite2D
var _tick: AudioStreamPlayer2D
var _tock: AudioStreamPlayer2D
var _chime: AudioStreamPlayer2D
var _last_sec := -1
var _last_half := -1


func _ready() -> void:
	z_index = -49
	if _t0_msec < 0:
		_t0_msec = Time.get_ticks_msec()
	var n := int(ceil(radius)) * 2 + 3
	_img = Image.create(n, n, false, Image.FORMAT_RGBA8)
	_tex = ImageTexture.create_from_image(_img)
	if pendulum_path != "":
		_pend = Sprite2D.new()
		_pend.texture = U.tex(pendulum_path)
		_pend.hframes = maxi(1, pendulum_frames)
		_pend.centered = false
		var o := U.v2(pendulum_offset)
		_pend.position = o
		add_child(_pend)
	_hands = Sprite2D.new()
	_hands.texture = _tex
	_hands.centered = false
	_hands.position = Vector2(-(n / 2), -(n / 2))
	add_child(_hands)
	_tick = U.make_sound(self, tick_path, -20.0, 220.0, 1.8)
	_tock = U.make_sound(self, tock_path, -21.0, 220.0, 1.8)
	_chime = U.make_sound(self, chime_path, -9.0, 900.0, 1.0)
	_draw_hands(_now())
	U.texel(_hands, global_position + _hands.position)
	if _pend:
		U.texel(_pend, global_position + _pend.position, Vector2(_pend.texture.get_width() / _pend.hframes,
				_pend.texture.get_height()) if _pend.texture else Vector2.ZERO)


func _now() -> float:
	return float(START_SECONDS) + float(Time.get_ticks_msec() - _t0_msec) / 1000.0


func _process(_delta: float) -> void:
	var t := _now()
	var sec := int(floor(t))
	if sec != _last_sec:
		_last_sec = sec
		_draw_hands(t)
		var s := sec % 60
		var m := (sec / 60) % 60
		if s == 0 and m % 15 == 0 and _chime:
			_chime.play()
	if _pend:
		var ph := fmod(t, pendulum_period) / pendulum_period
		_pend.frame = int(ph * pendulum_frames) % pendulum_frames
		var half := int(floor(t * 2.0 / pendulum_period))
		if half != _last_half:
			_last_half = half
			var p := _tick if half % 2 == 0 else _tock
			if p:
				p.play()


func _draw_hands(t: float) -> void:
	_img.fill(Color(0, 0, 0, 0))
	var c := Vector2(_img.get_width() / 2, _img.get_height() / 2)
	var secs := fmod(t, 43200.0)
	var hour_a := secs / 43200.0 * TAU
	var min_a := fmod(secs, 3600.0) / 3600.0 * TAU
	var sec_a := fmod(floor(secs), 60.0) / 60.0 * TAU
	_line(c, hour_a, radius * 0.5, INK)
	_line(c, min_a, radius * 0.82, INK)
	if second_hand:
		_line(c, sec_a, radius * 0.86, RED)
	_img.set_pixelv(Vector2i(c), BRASS if second_hand else INK)
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
