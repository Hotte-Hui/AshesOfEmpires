extends CanvasLayer
## Boot sequence of a real player's launch (TECHNICAL_ARCHITECTURE §12.13, round 11). Main plays it BEFORE
## Game.register_main(); scripts/ui/boot_flow.gd decides, automated runs never see it.
##   black (0.8 s) → studio card „<splash.studio> präsentiert“ (ember emblem, rising sparks, ember crackle)
##   → engine card „Erstellt mit Godot Engine“ in our own pixel lettering (scripts/ui/pixel_font.gd; no logo)
##   → title picture (assets/ui/splash, tools/pixelgen/gen_title_splash.py): Karsk and the Great Hall divided by one
##     railway line, the train's lamp coming closer, falling ash and drifting embers, a slow tilt up to the sky where
##     the title appears on the sting's stroke (assets/audio/music/mus_title_sting.wav) and one glint runs over it
##   → black; Game then fades the main menu in.
## Every card fades in and out. Any key, mouse button or pad button skips the current card, the second press skips
## the rest. `await play()` returns on black; the sting rings on into the menu, then the node frees itself.
## A time-driven state machine: _process → advance(dt); tests drive advance() / press() directly.
## Reduced motion: no tilt, fewer motes.

signal finished

const Kit := preload("res://scripts/ui/ui_kit.gd")
const PixelFont := preload("res://scripts/ui/pixel_font.gd")
const BootFlow := preload("res://scripts/ui/boot_flow.gd")
const DIR := "res://assets/ui/splash/"
const STING := "res://assets/audio/music/mus_title_sting.wav"
const EMBER_SFX := "splash_ember"
const GLINT := "res://assets/shaders/splash_glint.gdshader"
const SHOTS_SCRIPT := "res://scripts/ui/dev/boot_shots.gd"
const ART := 3                      # screen px per art px of the title picture (640x360 view -> 1920x1080)
const MARK := 4                     # screen px per art px on the studio / engine cards
const TILT_ROWS := 60               # the title card starts this many art rows lower and tilts up (generator TILT)
const BLACK := 0.8
const STUDIO := [0.6, 1.5, 0.6]     # fade in, hold, fade out (s)
const ENGINE := [0.5, 1.1, 0.5]
const TITLE := [0.9, 4.5, 1.0]
const SKIP_FADE := 0.25
## title timeline (s from the start of the title card)
const TILT_END := 3.0
const LOGO_AT := 2.4
const SUB_AT := 3.0
const GLINT_AT := 3.4
const GLINT_DUR := 0.9
const EMBER_RAMP := [Color("fbe3ae"), Color("f0c487"), Color("dca16e"), Color("ba775b"), Color("7a3e26")]
const PAPER_RAMP := [Color("f5efda"), Color("e6dec2"), Color("cec6aa"), Color("b0aa93")]
const INK := Color("05090f")
const SHADOW := Color("020507")

var cards: Array[String] = []       # the cards in the order they were shown (tests, check run)
var card := ""                      # the card on screen now ("" before / after)
var card_time := 0.0                # seconds since the current card began
var presses := 0
var running := false
var done := false
var time_scale := 1.0
var quiet := false                  # tests: no sting, no ember sound
var auto_free := true               # tests keep the node after the end
var _skip_card := false
var _skip_all := false
var _veil: ColorRect
var _studio: Control
var _engine: Control
var _title: Control
var _glow: TextureRect
var _mark: TextureRect
var _scene: TextureRect
var _lamp: TextureRect
var _logo: TextureRect
var _sub: TextureRect
var _flash: ColorRect
var _ash: Motes
var _sparks: Motes
var _sting: AudioStreamPlayer
var _index := -1
var _phase := ""                    # "in" | "hold" | "out"
var _phase_t := 0.0
var _phase_dur := 0.0
var _out_from := 1.0


## Ash flakes falling and embers drifting up (title), or sparks rising from the studio ember. Drawn in whole art
## pixels (cell x cell screen px) on the art grid, so they belong to the pixel picture.
class Motes extends Control:
	var mode := "ash"
	var origin := Vector2(960, 540)
	var cell := 3.0
	var _p: Array = []
	var _rng := RandomNumberGenerator.new()
	var _t := 0.0

	func setup(m: String, n: int, seed_value: int, c: float) -> void:
		mode = m
		cell = c
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		_rng.seed = seed_value
		_p.clear()
		for i in n:
			_p.append(_spawn(true))

	func _spawn(initial: bool) -> Dictionary:
		var p := {"age": 0.0, "phase": _rng.randf() * TAU, "sway": _rng.randf_range(4.0, 16.0), "size": 1.0}
		if mode == "sparks":
			p["kind"] = "ember"
			p["pos"] = origin + Vector2(_rng.randf_range(-16, 16), _rng.randf_range(-4, 8))
			p["vel"] = Vector2(_rng.randf_range(-16, 26), _rng.randf_range(-80, -40))
			p["life"] = _rng.randf_range(0.8, 1.8)
			p["col"] = [Color("fbe3ae"), Color("f0c487"), Color("e5945a"), Color("d07744")][_rng.randi_range(0, 3)]
		elif _rng.randf() < 0.24:
			p["kind"] = "ember"
			p["pos"] = Vector2(_rng.randf_range(-120, 1900), _rng.randf_range(0, 1150) if initial else _rng.randf_range(1090, 1160))
			p["vel"] = Vector2(_rng.randf_range(14, 46), _rng.randf_range(-52, -20))
			p["life"] = _rng.randf_range(3.0, 7.0)
			p["col"] = [Color("f0ae6e"), Color("e5945a"), Color("d07744"), Color("fbe3ae")][_rng.randi_range(0, 3)]
		else:
			p["kind"] = "ash"
			p["pos"] = Vector2(_rng.randf_range(-240, 1900), _rng.randf_range(-40, 1080) if initial else _rng.randf_range(-60, -10))
			p["vel"] = Vector2(_rng.randf_range(6, 34), _rng.randf_range(24, 66))
			p["life"] = 99.0
			p["size"] = 2.0 if _rng.randf() < 0.12 else 1.0
			var col: Color = [Color("9a9b8b"), Color("7f8275"), Color("666a60"), Color("b0aa93")][_rng.randi_range(0, 3)]
			col.a = _rng.randf_range(0.45, 0.85)
			p["col"] = col
		if initial:
			p["age"] = _rng.randf_range(0.0, minf(float(p["life"]), 3.0))
		return p

	func _process(delta: float) -> void:
		if not is_visible_in_tree():
			return
		_t += delta
		for i in _p.size():
			var p: Dictionary = _p[i]
			p["age"] = float(p["age"]) + delta
			var v: Vector2 = p["vel"]
			p["pos"] = (p["pos"] as Vector2) + v * delta + Vector2(cos(_t * 1.4 + float(p["phase"])) * float(p["sway"]) * delta, 0.0)
			var pos: Vector2 = p["pos"]
			if float(p["age"]) > float(p["life"]) or pos.y > 1100.0 or pos.y < -80.0 or pos.x > 1960.0:
				_p[i] = _spawn(false)
		queue_redraw()

	func _draw() -> void:
		for p in _p:
			var c: Color = p["col"]
			if p["kind"] == "ember":
				var k := float(p["age"]) / float(p["life"])
				c.a = clampf(1.0 - k, 0.0, 1.0) * (0.7 + 0.3 * sin(_t * 17.0 + float(p["phase"])))
			var pos: Vector2 = p["pos"]
			var q := Vector2(floorf(pos.x / cell) * cell, floorf(pos.y / cell) * cell)
			draw_rect(Rect2(q, Vector2(cell, cell) * float(p["size"])), c)


func _ready() -> void:
	layer = 120
	process_mode = Node.PROCESS_MODE_ALWAYS
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	Kit.full_rect(bg)
	bg.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(bg)
	_studio = _build_studio()
	_engine = _build_engine()
	_title = _build_title()
	_veil = ColorRect.new()
	_veil.color = Color(0, 0, 0, 1)
	Kit.full_rect(_veil)
	_veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_veil)
	_sting = AudioStreamPlayer.new()
	_sting.bus = "Music" if AudioServer.get_bus_index("Music") >= 0 else "Master"
	add_child(_sting)
	if BootFlow.shots_dir() != "" and ResourceLoader.exists(SHOTS_SCRIPT):
		var shots: Node = load(SHOTS_SCRIPT).new()
		shots.set("splash", self)
		get_tree().root.add_child.call_deferred(shots)


# ---------------------------------------------------------------- cards
func _pix(path: String, scale: int) -> TextureRect:
	var t := Kit.tex(path)
	var r := TextureRect.new()
	r.texture = t
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if t != null:
		r.size = t.get_size() * scale
		r.custom_minimum_size = r.size
	return r


func _layer() -> Control:
	var c := Control.new()
	Kit.full_rect(c)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.visible = false
	add_child(c)
	return c


## Lettering from a locale key: our pixel capitals, or the title font when a character has no glyph (renamed studio).
func _lettering(text: String, scale: int, opts: Dictionary, fallback_size: int) -> Control:
	var r := PixelFont.rect(text, scale, opts)
	if r != null:
		r.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		return r
	var l := Kit.label(text.to_upper(), "TitleLabel", fallback_size, opts.get("ramp", [Color.WHITE])[0])
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	return l


func _column(parent: Control, sep: int) -> VBoxContainer:
	var cc := CenterContainer.new()
	Kit.full_rect(cc)
	cc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(cc)
	var v := Kit.vbox(sep)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	cc.add_child(v)
	return v


func _build_studio() -> Control:
	var c := _layer()
	var v := _column(c, 0)
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(40, 40) * MARK
	holder.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(holder)
	_glow = _pix(DIR + "studio_glow.png", MARK)
	holder.add_child(_glow)
	_mark = _pix(DIR + "studio_mark.png", MARK)
	holder.add_child(_mark)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 30))
	v.add_child(_lettering(Kit.t("splash.studio"), MARK, {"smooth": true, "bold": true, "tracking": 2,
		"ramp": EMBER_RAMP, "outline": INK, "shadow": SHADOW, "bevel": true}, 72))
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 14))
	var pres := Kit.label(Kit.t("splash.presents"), "", 36, Color("a3aca2"))
	pres.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	pres.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pres.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(pres)
	_sparks = Motes.new()
	Kit.full_rect(_sparks)
	c.add_child(_sparks)
	return c


func _build_engine() -> Control:
	var c := _layer()
	var v := _column(c, 22)
	v.add_child(_lettering(Kit.t("splash.made_with"), MARK, {"tracking": 2, "ramp": [Color("a3aca2")],
		"shadow": SHADOW}, 34))
	var row := Kit.hbox(16)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	row.add_child(Kit.rule(Kit.C_COPPER, 3, 120))
	var orn := Kit.sprite("icons/ornament_diamond.png")
	orn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(orn)
	row.add_child(Kit.rule(Kit.C_COPPER, 3, 120))
	for r in [row.get_child(0), row.get_child(2)]:
		(r as Control).size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.add_child(row)
	v.add_child(_lettering(Kit.t("splash.engine"), MARK, {"smooth": true, "bold": true, "tracking": 2,
		"ramp": PAPER_RAMP, "outline": INK, "shadow": SHADOW, "bevel": true}, 64))
	return c


func _build_title() -> Control:
	var c := _layer()
	c.clip_contents = true
	_scene = _pix(DIR + "title_scene.png", ART)
	c.add_child(_scene)
	_lamp = _pix(DIR + "title_lamp.png", ART)
	c.add_child(_lamp)
	_ash = Motes.new()
	Kit.full_rect(_ash)
	c.add_child(_ash)
	_flash = ColorRect.new()
	_flash.color = Color(0.94, 0.68, 0.43, 0.0)
	Kit.full_rect(_flash)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(_flash)
	_logo = _pix(DIR + "title_logo.png", ART)
	_logo.position = Vector2(_snap((1920.0 - _logo.size.x) / 2.0), 26 * ART)
	if ResourceLoader.exists(GLINT):
		var mat := ShaderMaterial.new()
		mat.shader = load(GLINT)
		mat.set_shader_parameter("sweep", -1.0)
		_logo.material = mat
	c.add_child(_logo)
	_sub = _pix(DIR + "title_sub.png", ART)
	_sub.position = Vector2(_snap((1920.0 - _sub.size.x) / 2.0), _logo.position.y + _logo.size.y + 2 * ART)
	c.add_child(_sub)
	return c


func _snap(x: float) -> float:
	return roundf(x / ART) * ART


# ---------------------------------------------------------------- sequence (a time-driven state machine)
## Plays the whole sequence; returns on black (the sting may still ring).
func play() -> void:
	if not running and not done:
		start()
	if running:
		await finished


func start() -> void:
	running = true
	done = false
	presses = 0
	_skip_all = false
	cards.clear()
	_veil.color.a = 1.0
	_index = -1
	_next_card()


## The card list in play order: [id, node, fade in, hold, fade out].
func _plan() -> Array:
	return [["black", null, 0.0, BLACK, 0.0], ["studio", _studio] + STUDIO, ["engine", _engine] + ENGINE,
		["title", _title] + TITLE]


func _next_card() -> void:
	if _index >= 0:
		var prev: Array = _plan()[_index]
		if prev[1] != null:
			(prev[1] as Control).visible = false
		if prev[0] == "title" and (_skip_card or _skip_all):
			_fade_sting(0.9)
	_index += 1
	if _skip_all or _index >= _plan().size():
		_finish()
		return
	var c: Array = _plan()[_index]
	card = str(c[0])
	card_time = 0.0
	_skip_card = false
	_phase = "in"
	_phase_t = 0.0
	_phase_dur = float(c[2])
	cards.append(card)
	if c[1] != null:
		(c[1] as Control).visible = true
	_card_started(card)


## Advances the sequence by dt seconds (called every frame; tests call it directly).
func advance(dt: float) -> void:
	if not running:
		return
	card_time += dt
	_phase_t += dt
	var c: Array = _plan()[_index]
	match _phase:
		"in":
			if _skip_card:
				_begin_out()
			elif _phase_t >= _phase_dur:
				_veil.color.a = 0.0
				_phase = "hold"
				_phase_t = 0.0
				_phase_dur = float(c[3])
			else:
				_veil.color.a = 1.0 - _phase_t / _phase_dur
		"hold":
			if _skip_card or _phase_t >= _phase_dur:
				_begin_out()
		"out":
			if _phase_t >= _phase_dur:
				_veil.color.a = 1.0
				_next_card()
			else:
				_veil.color.a = lerpf(_out_from, 1.0, _phase_t / _phase_dur)


func _begin_out() -> void:
	_phase = "out"
	_phase_t = 0.0
	_out_from = _veil.color.a
	_phase_dur = SKIP_FADE if _skip_card else float(_plan()[_index][4])
	if _phase_dur <= 0.0:
		_phase_dur = 0.0001


## A press skips the current card; the second press skips the rest.
func press() -> void:
	if not running:
		return
	presses += 1
	_skip_card = true
	if presses >= 2:
		_skip_all = true


func _finish() -> void:
	_veil.color.a = 1.0
	card = ""
	running = false
	done = true
	visible = false
	if auto_free:
		_release()
	finished.emit()


func _card_started(id: String) -> void:
	match id:
		"studio":
			_sparks.origin = _mark.get_global_rect().position + Vector2(19.5, 23.0) * MARK
			_sparks.setup("sparks", 6 if Kit.reduced_motion() else 16, 7, float(MARK))
			var a := Kit.svc("Audio")
			if not quiet and a != null and a.has_method("sfx"):
				a.sfx(EMBER_SFX, -2.0, 0.0)
		"title":
			_ash.setup("ash", 30 if Kit.reduced_motion() else 96, 1964, float(ART))
			_update_title(0.0)
			if not quiet and ResourceLoader.exists(STING):
				_sting.stream = load(STING)
				_sting.volume_db = -2.0
				_sting.play()


func _process(delta: float) -> void:
	if not running:
		return
	advance(delta * time_scale)
	if card == "studio":
		_sparks.origin = _mark.get_global_rect().position + Vector2(19.5, 23.0) * MARK
		var k := 0.5 + 0.5 * sin(card_time * 5.3)
		_glow.modulate.a = 0.45 + 0.55 * k * (0.85 + 0.15 * sin(card_time * 12.7))
	elif card == "title":
		_update_title(card_time)


func _update_title(t: float) -> void:
	var k := 1.0 if Kit.reduced_motion() else _ease(clampf(t / TILT_END, 0.0, 1.0))
	var y := roundf(-TILT_ROWS * ART * (1.0 - k))
	_scene.position.y = y
	_lamp.position.y = y
	var near := clampf((t - 0.3) / 4.2, 0.0, 1.0)
	_lamp.modulate.a = (0.3 + 0.7 * near) * (0.92 + 0.08 * sin(t * 13.0) * sin(t * 7.3))
	_logo.modulate.a = clampf((t - LOGO_AT) / 0.45, 0.0, 1.0)
	_sub.modulate.a = clampf((t - SUB_AT) / 0.6, 0.0, 1.0)
	_flash.color.a = 0.10 * clampf(1.0 - (t - LOGO_AT) / 0.7, 0.0, 1.0) if t >= LOGO_AT else 0.0
	if _logo.material is ShaderMaterial:
		var g := clampf((t - GLINT_AT) / GLINT_DUR, 0.0, 1.0)
		(_logo.material as ShaderMaterial).set_shader_parameter("sweep", lerpf(-0.3, 1.3, g) if t >= GLINT_AT else -1.0)


func _ease(x: float) -> float:
	return x * x * (3.0 - 2.0 * x)


# ---------------------------------------------------------------- input
func _input(event: InputEvent) -> void:
	if not running:
		return
	if is_press(event):
		press()
		get_viewport().set_input_as_handled()
	elif event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton:
		get_viewport().set_input_as_handled()


## A deliberate press: key down (no echo), mouse button down or pad button down; never motion or a release.
static func is_press(event: InputEvent) -> bool:
	if event is InputEventKey:
		return (event as InputEventKey).pressed and not (event as InputEventKey).echo
	if event is InputEventMouseButton:
		return (event as InputEventMouseButton).pressed
	if event is InputEventJoypadButton:
		return (event as InputEventJoypadButton).pressed
	return false


# ---------------------------------------------------------------- end
func _fade_sting(t: float) -> void:
	if _sting == null or not _sting.playing:
		return
	var tw := create_tween()
	tw.tween_property(_sting, "volume_db", -48.0, t)
	tw.tween_callback(_sting.stop)


## The sequence is over: the sting may ring on under the menu, then the node goes.
func _release() -> void:
	set_process_input(false)
	if _sting != null and _sting.playing:
		_sting.finished.connect(queue_free)
		var guard := Timer.new()             # never outlive the menu by more than the sting's length
		guard.one_shot = true
		guard.wait_time = 12.0
		guard.timeout.connect(queue_free)
		add_child(guard)
		guard.start()
	else:
		queue_free.call_deferred()
