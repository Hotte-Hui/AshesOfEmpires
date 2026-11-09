extends "res://scripts/ui/ui_modal.gd"
## FlashbackView — shows one flashback film of a real-history card (TECHNICAL_ARCHITECTURE §12.15).
## A modal made on first use by Flashbacks.view() (scripts/core/flashbacks.gd) under UIRoot: it lies above the card
## (DiscoveryView) or the film list (MemoryView) that started it, pauses nothing new and changes nothing below —
## when the film ends or is skipped the modal closes and the view underneath has its focus back.
##   picture   the film scene (scenes/cinematics/flashback_*/, use_director = false) drawn x3 on a black screen:
##             a 4:3 gate of 1440 x 1080 px, nearest filtering, movement in single screen pixels
##   words     outside the fiction like the cards themselves: „REALE GESCHICHTE“ and the place-and-date caption
##             top left, the sober line bottom centre, both on dark plates inside the gate; they follow the text
##             scale (100 / 125 / 150 %) and wrap in balanced lines (tests/test_flashbacks.gd)
##   sound     the film's bed (assets/audio/sfx/<bed>.wav) on its own player; music, ambience and looping world
##             sounds are turned down while the film runs and come back afterwards (bus volumes restored exactly)
##   input     Esc / B / Y or any key that advances (E, Space, Enter, A) skips after a short guard; the mouse uses
##             „Überspringen“ bottom right. Nothing reaches the views below while the film runs.
## API: play(film_id) -> bool, skip(); signals closed (modal base) and film_finished(film_id, skipped).

signal film_finished(film_id: String, skipped: bool)

const Flashbacks := preload("res://scripts/core/flashbacks.gd")
## The press that started the film (or a mashed one) must not skip it at once.
const OPEN_GUARD_MS := 350
const SCREEN := Vector2(1920, 1080)
const WORLD_SCALE := 3.0
## The film gate on the screen: 480 x 360 world px at x3.
const GATE := Rect2(240, 0, 1440, 1080)
const MARGIN := 42.0
const LINE_BOTTOM := 60.0
const LINE_MAX_W := 1180.0
const PLACE_MAX_W := 1040.0
const PAD := Vector2(22, 12)
const BED_DB := -3.0
const DUCK_BUSES := ["Music", "Ambience", "SFX"]
const DUCK_DB := -60.0
const C_TEXT := Color("ecd9b9")
const C_KICK := Color("c4a888")
const C_PLATE := Color(0.03, 0.02, 0.015, 0.78)

var film_id := ""
var film: Node2D = null
var skipped := false

var _screen: Control
var _holder: Node2D
var _slate: Panel
var _kicker: Label
var _place: Label
var _line_bg: Panel
var _line: Label
var _skip_row: Control
var _bed: AudioStreamPlayer = null
var _bus_keep: Dictionary = {}
var _bus_tween: Tween = null
var _duck_k := 0.0
var _opened_ms := 0
var _closing := false
var _shown := ["", ""]


func _ready() -> void:
	pauses_game = true
	closes_on_cancel = false
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	Kit.full_rect(bg)
	bg.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(bg)
	_screen = Control.new()
	Kit.full_rect(_screen)
	_screen.clip_contents = true
	_screen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_screen.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_screen)
	_holder = Node2D.new()
	_holder.scale = Vector2(WORLD_SCALE, WORLD_SCALE)
	_screen.add_child(_holder)
	_slate = _plate()
	_kicker = Kit.label("", "KickerLabel", 0, C_KICK)
	Kit.scalable(_kicker, 20)
	_slate.add_child(_kicker)
	_place = Kit.label("", "", 0, C_TEXT)
	_place.add_theme_font_override("font", Kit.font("fv_serif"))
	Kit.scalable(_place, 30)
	_slate.add_child(_place)
	_line_bg = _plate()
	_line = Kit.label("", "", 0, C_TEXT)
	_line.add_theme_font_override("font", Kit.font("fv_serif"))
	_line.add_theme_constant_override("line_spacing", 6)
	_line.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(_line, 31)
	_line_bg.add_child(_line)
	_skip_row = Control.new()
	_skip_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_skip_row)


func _exit_tree() -> void:
	if not _bus_keep.is_empty():           # never leave the world's buses turned down
		_set_duck(0.0)
		_bus_keep.clear()


func _plate() -> Panel:
	var p := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = C_PLATE
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.visible = false
	add_child(p)
	return p


# ================================================================ playing
## Starts the film `film_id` above whatever is open. False when it cannot be played (unknown, no scene, busy).
func play(id: String) -> bool:
	var f := Flashbacks.film(id)
	if is_open or f.is_empty() or not Flashbacks.exists(id):
		return false
	var packed = load(str(f["scene"]))
	if not (packed is PackedScene):
		return false
	_clear_film()
	film_id = id
	skipped = false
	_closing = false
	_shown = ["", ""]
	film = (packed as PackedScene).instantiate() as Node2D
	film.set("use_director", false)        # no Game camera, no HUD subtitle box: this view presents the film
	_holder.position = _origin()
	_holder.add_child(film)
	film.call("configure", {"choices": {}, "flags": {}, "symbols": true})
	film.connect("finished", _on_film_finished, CONNECT_ONE_SHOT)
	_screen.modulate = Color.WHITE
	show_captions("", "")
	_build_skip()
	_opened_ms = Time.get_ticks_msec()
	open_modal()
	_duck(true)
	_start_bed(str(f.get("bed", "")))
	film.call("play")
	return true


## Ends the running film now (idempotent).
func skip() -> void:
	if not is_open or _closing or film == null or not is_instance_valid(film):
		return
	skipped = true
	film.call("skip")                      # -> finished -> _on_film_finished


func _on_film_finished() -> void:
	if _closing:
		return
	_closing = true
	_slate.visible = false
	_line_bg.visible = false
	_fade_bed(0.3)
	_duck(false)
	if is_inside_tree():
		var tw := create_tween()
		tw.tween_property(_screen, "modulate", Color.BLACK, 0.12)
		tw.tween_callback(_done)
	else:
		_done()


func _done() -> void:
	if not is_open:
		return
	film_finished.emit(film_id, skipped)
	close()


func _process(_delta: float) -> void:
	if not is_open or _closing or film == null or not is_instance_valid(film):
		return
	var st: Dictionary = film.call("caption_state")
	var pk := str(st.get("place", ""))
	var lk := str(st.get("line", ""))
	show_captions(Kit.t(pk) if pk != "" else "", Kit.t(lk) if lk != "" else "",
		float(st.get("place_a", 0.0)), float(st.get("line_a", 0.0)))


# ================================================================ captions
## Shows the place-and-date caption and the line (texts as given; "" hides one) at the given opacities.
func show_captions(place_text: String, line_text: String, place_a := 1.0, line_a := 1.0) -> void:
	var g := gate_rect()
	if place_text != _shown[0]:
		_shown[0] = place_text
		_place.text = place_text
		_kicker.text = Kit.t("ui.history.kicker").to_upper().replace("ß", "SS") if place_text != "" else ""
		if place_text != "":
			var ks := _fit(_kicker, PLACE_MAX_W)
			var ps := _fit(_place, PLACE_MAX_W)
			_kicker.position = PAD
			_place.position = PAD + Vector2(0, ks.y + 4.0)
			_slate.size = Vector2(maxf(ks.x, ps.x), ks.y + 4.0 + ps.y) + PAD * 2.0
			_slate.position = g.position + Vector2(MARGIN, MARGIN)
	if line_text != _shown[1]:
		_shown[1] = line_text
		_line.text = line_text
		if line_text != "":
			var ls := _fit(_line, LINE_MAX_W)
			_line.position = PAD
			_line_bg.size = ls + PAD * 2.0
			_line_bg.position = Vector2(roundf(g.position.x + (g.size.x - _line_bg.size.x) * 0.5),
				g.end.y - LINE_BOTTOM - _line_bg.size.y)
	_slate.visible = place_text != "" and place_a > 0.0
	_slate.modulate.a = clampf(place_a, 0.0, 1.0)
	_line_bg.visible = line_text != "" and line_a > 0.0
	_line_bg.modulate.a = clampf(line_a, 0.0, 1.0)


## Sizes a caption label: one line when it fits max_w, else balanced lines of about equal length.
func _fit(l: Label, max_w: float) -> Vector2:
	var f := l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	var one := ceilf(f.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x) + 6.0
	var w := one
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	if one > max_w:
		var n := ceilf(one / max_w)
		w = minf(max_w, ceilf(one / n * 1.08) + 30.0)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var want := maxi(1, int(ceilf(one / max_w)))
	for _i in 16:                              # widen until the text needs no more lines than its length asks for
		l.custom_minimum_size = Vector2(w, 0)
		l.size = Vector2(w, 0)
		l.size = Vector2(w, l.get_minimum_size().y)
		if l.get_line_count() <= want or w >= max_w:
			break
		w = minf(max_w, w + 36.0)
	return l.size


func gate_rect() -> Rect2:
	return Rect2(_origin() + GATE.position, GATE.size)


func slate_rect() -> Rect2:
	return Rect2(_slate.position, _slate.size)


func line_rect() -> Rect2:
	return Rect2(_line_bg.position, _line_bg.size)


func line_count() -> int:
	return _line.get_line_count()


## Top-left of the 1920 x 1080 film screen inside this control (zero on the game's canvas).
func _origin() -> Vector2:
	var sz := size if size.x > 0.0 and size.y > 0.0 else SCREEN
	return ((sz - SCREEN) * 0.5).floor()


func _build_skip() -> void:
	for c in _skip_row.get_children():
		_skip_row.remove_child(c)
		c.queue_free()
	var key := Kit.pad_button_name(JOY_BUTTON_B) if Kit.last_input_pad else Kit.key_name(KEY_ESCAPE)
	var hint := Kit.controls_row([[key, Kit.t("ui.flashback.skip")]])
	_skip_row.add_child(hint)
	var sz := hint.get_combined_minimum_size()
	hint.size = sz
	var b := Button.new()                  # the mouse skips here; keys and pad need no focus
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.position = Vector2(-14, -10)
	b.size = sz + Vector2(28, 20)
	b.pressed.connect(skip)
	_skip_row.add_child(b)
	_skip_row.size = sz
	_skip_row.position = (_origin() + SCREEN - sz - Vector2(30, 28)).floor()


# ================================================================ sound
func _start_bed(id: String) -> void:
	_stop_bed()
	var path := "res://assets/audio/sfx/%s.wav" % id
	if id == "" or not ResourceLoader.exists(path):
		return
	var stream = load(path)
	if not (stream is AudioStream):
		return
	_bed = AudioStreamPlayer.new()
	_bed.stream = stream
	# the world's buses are turned down while the film runs: the bed goes to Master and follows the SFX slider itself
	_bed.bus = "Master"
	_bed.volume_db = BED_DB + float(_bus_keep.get("SFX", 0.0))
	add_child(_bed)
	_bed.play()


func _fade_bed(seconds: float) -> void:
	var b := _bed
	_bed = null
	if b == null or not is_instance_valid(b):
		return
	if not is_inside_tree() or not b.playing:
		b.queue_free()
		return
	var tw := create_tween()
	tw.tween_property(b, "volume_db", -60.0, seconds)
	tw.tween_callback(b.queue_free)


func _stop_bed() -> void:
	if _bed != null and is_instance_valid(_bed):
		_bed.stop()
		_bed.queue_free()
	_bed = null


## Turns music, ambience and the looping world sounds down (on) or back to exactly where they were (off).
func _duck(on: bool) -> void:
	if _bus_tween != null and _bus_tween.is_valid():
		_bus_tween.kill()
	if on and _bus_keep.is_empty():
		for b in DUCK_BUSES:
			var i := AudioServer.get_bus_index(b)
			if i >= 0:
				_bus_keep[b] = AudioServer.get_bus_volume_db(i)
	if _bus_keep.is_empty():
		return
	if not is_inside_tree():
		_set_duck(1.0 if on else 0.0)
		if not on:
			_bus_keep.clear()
		return
	_bus_tween = create_tween()
	_bus_tween.tween_method(_set_duck, _duck_k, 1.0 if on else 0.0, 0.4 if on else 0.6)
	if not on:
		_bus_tween.tween_callback(_duck_done)


func _duck_done() -> void:
	_bus_keep.clear()


func _set_duck(k: float) -> void:
	_duck_k = k
	for b in _bus_keep:
		var i := AudioServer.get_bus_index(b)
		if i >= 0:
			var keep := float(_bus_keep[b])
			AudioServer.set_bus_volume_db(i, lerpf(keep, minf(keep, DUCK_DB), k))


## True while the world's buses are turned down by this view (tests).
func is_ducking() -> bool:
	return not _bus_keep.is_empty()


# ================================================================ modal hooks
func _clear_film() -> void:
	if film != null and is_instance_valid(film):
		if film.is_connected("finished", _on_film_finished):
			film.disconnect("finished", _on_film_finished)
		film.queue_free()
	film = null


func _on_close() -> void:
	_clear_film()
	_stop_bed()
	if not _closing:                       # closed from outside (UIRoot.close_all): give the sound back at once
		_duck(false)
	_slate.visible = false
	_line_bg.visible = false
	_closing = false


func handle_cancel() -> bool:
	if Time.get_ticks_msec() - _opened_ms >= OPEN_GUARD_MS:
		skip()
	return true


func modal_input(event: InputEvent) -> bool:
	if not is_open:
		return false
	if event is InputEventMouse:
		return false                       # „Überspringen“ takes the click; the black backdrop stops the rest
	for a in ["interact", "advance", "ui_accept", "cancel", "ui_cancel", "skip"]:
		if InputMap.has_action(a) and event.is_action_pressed(a):
			if Time.get_ticks_msec() - _opened_ms >= OPEN_GUARD_MS:
				skip()
			return true
	return true                            # nothing reaches the views below while the film runs
