extends Node2D
## A tram (motor car + trailer) passing in the street below the archive about every 45 s, alternating
## direction.  It lives on the parallax plane of the street (parallax ~0.2) and is drawn at z -89, between the
## tenements (ext_near, z -90) and the room layer (z -50), so it is only ever seen through the window glass:
## the pantograph sliding along the contact wire, the roof and -- through the taller reading-room windows --
## the lit windows with passengers.  While it passes, a warm glow slides along the windows, the pantograph
## sparks now and then and a positional rumble rolls through the floor.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")

@export var sheet_path := ""
@export var spark_path := ""
@export var sound_path := ""
@export var bell_path := "res://assets/audio/sfx/berlin_tram_bell.wav"
@export var parallax := 0.2
@export var top_y := 208.0            ## world y of the sprite's top row
@export var pantograph_x := 199.0     ## sprite-local x of the pantograph contact
@export var wire_y := 211.0           ## world y of the contact wire
@export var period := 45.0            ## seconds between two departures
@export var first_delay := 9.0
@export var speed := 46.0             ## layer-local px / s
@export var layer_width := 1100.0
@export var glass_rects: Array = []   ## [[x, y, w, h], ...] world rects of the window glass

var running := false
var _spr: Sprite2D
var _spark: Sprite2D
var _light: PointLight2D
var _flash: PointLight2D
var _snd: AudioStreamPlayer2D
var _bell: AudioStreamPlayer2D
var _t := 0.0
var _dir := 1.0
var _lx := 0.0
var _w := 276.0
var _spark_t := 2.0
var _spark_f := -1
var _bell_done := false
var _runs := 0


func _ready() -> void:
	process_priority = 10
	z_index = -89
	_spr = Sprite2D.new()
	_spr.centered = false
	_spr.light_mask = 0
	_spr.texture = U.tex(sheet_path)
	_spr.visible = false
	add_child(_spr)
	if _spr.texture:
		_w = float(_spr.texture.get_width())
	_spark = Sprite2D.new()
	_spark.texture = U.tex(spark_path)
	_spark.hframes = 4
	_spark.light_mask = 0
	_spark.visible = false
	add_child(_spark)
	U.texel(_spr)
	U.texel(_spark, Vector2.ZERO, Vector2(9, 7))
	_light = PointLight2D.new()
	_light.texture = U.light_texture()
	_light.color = Color("#F0C487")
	_light.energy = 0.0
	_light.texture_scale = 0.75
	_light.height = 34.0
	add_child(_light)
	_flash = PointLight2D.new()
	_flash.texture = _light.texture
	_flash.color = Color("#CFE0FF")
	_flash.energy = 0.0
	_flash.texture_scale = 0.9
	_flash.height = 40.0
	add_child(_flash)
	_snd = U.make_sound(self, sound_path, -9.0, 760.0, 1.3, true)
	_bell = U.make_sound(self, bell_path, -12.0, 900.0, 1.2)
	_t = first_delay


func _start() -> void:
	running = true
	_runs += 1
	_dir = 1.0 if _runs % 2 == 1 else -1.0
	_spr.flip_h = _dir < 0.0
	_lx = -_w - 40.0 if _dir > 0.0 else layer_width + 40.0
	_spr.visible = true
	_bell_done = false
	_spark_t = randf_range(1.0, 3.0)
	if _snd:
		_snd.play()


func _stop() -> void:
	running = false
	_spr.visible = false
	_spark.visible = false
	_light.energy = 0.0
	_flash.energy = 0.0
	if _snd:
		_snd.stop()
	var travel := (layer_width + _w + 80.0) / maxf(1.0, speed)
	_t = maxf(4.0, period * randf_range(0.85, 1.15) - travel)


func _process(delta: float) -> void:
	if not running:
		_t -= delta
		if _t <= 0.0:
			_start()
		return
	_lx += _dir * speed * delta
	if (_dir > 0.0 and _lx > layer_width + 40.0) or (_dir < 0.0 and _lx + _w < -40.0):
		_stop()
		return
	var cam := U.cam_top_left()
	var off := cam.x * (1.0 - parallax)
	var wx := roundf(_lx + off)                          # world x of the sprite's left edge
	_spr.position = Vector2(wx, top_y) - position
	var cx := wx + _w * 0.5
	var pant_x := wx + (pantograph_x if _dir > 0.0 else _w - pantograph_x)
	# sound follows the train (2D attenuation does the approach / recede)
	if _snd:
		_snd.position = Vector2(cx, 236.0) - position
	# bell once the front reaches the visible part of the street
	if not _bell_done and _bell and absf(cx - (cam.x + 320.0)) < 360.0:
		_bell_done = true
		_bell.position = Vector2(cx, 236.0) - position
		_bell.play()
	# warm glow through the glass while the lit windows pass a window
	var k := 0.0
	for r in glass_rects:
		if r is Array and r.size() >= 4:
			var a := float(r[0]) - 14.0
			var b := float(r[0]) + float(r[2]) + 14.0
			var near_x := clampf(cx, a, b)
			var span := absf(cx - near_x)
			var inside := maxf(0.0, 1.0 - span / (_w * 0.5))
			k = maxf(k, inside)
	_light.position = Vector2(clampf(cx, cam.x - 40.0, cam.x + 680.0), 244.0) - position
	_light.energy = 0.32 * k
	# pantograph sparks (short, irregular; the light flash is skipped with reduced motion)
	_spark_t -= delta
	if _spark_t <= 0.0 and _spark_f < 0:
		_spark_f = 0
		_spark_t = randf_range(2.0, 6.5)
	if _spark_f >= 0:
		_spark.visible = true
		_spark.frame = clampi(_spark_f / 2, 0, 3)
		_spark.position = Vector2(pant_x, wire_y) - position - Vector2(4, 3)
		_flash.position = Vector2(pant_x, wire_y + 6.0) - position
		_flash.energy = 0.0 if U.reduced_motion() else 0.55 * k * (1.0 - float(_spark_f) / 8.0)
		_spark_f += 1
		if _spark_f >= 8:
			_spark_f = -1
			_spark.visible = false
			_flash.energy = 0.0
