extends Control
## Screen fades and cinematic letterbox bars (2.39:1, 138 px at 1080p).
## API: await fade_out(t), await fade_in(t), set_black(on), letterbox(on, t), is_letterboxed().
## Reduced motion: bars fade instead of sliding.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const BAR := 138.0

signal fade_finished

var ui_root: Node = null
var _black: ColorRect
var _top: ColorRect
var _bottom: ColorRect
var _letterboxed := false
var _fade_tw: Tween
var _bar_tw: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(self)
	_top = _bar()
	_top.position = Vector2(0, -BAR)
	_bottom = _bar()
	_bottom.position = Vector2(0, 1080)
	_black = ColorRect.new()
	_black.color = Color(0.008, 0.016, 0.024, 0.0)
	Kit.full_rect(_black)
	_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_black)


func _bar() -> ColorRect:
	var r := ColorRect.new()
	r.color = Color.BLACK
	r.size = Vector2(1920, BAR)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.visible = false
	add_child(r)
	return r


func fade_out(t := 0.6) -> void:
	await _fade_to(1.0, t)


func fade_in(t := 0.6) -> void:
	await _fade_to(0.0, t)


func _fade_to(a: float, t: float) -> void:
	if _fade_tw != null and _fade_tw.is_valid():
		_fade_tw.kill()
	_black.mouse_filter = Control.MOUSE_FILTER_STOP if a > 0.5 else Control.MOUSE_FILTER_IGNORE
	if t <= 0.0:
		_black.color.a = a
		fade_finished.emit()
		return
	_fade_tw = create_tween()
	_fade_tw.tween_property(_black, "color:a", a, t)
	await _fade_tw.finished
	fade_finished.emit()


func set_black(on: bool) -> void:
	if _fade_tw != null and _fade_tw.is_valid():
		_fade_tw.kill()
	_black.color.a = 1.0 if on else 0.0
	_black.mouse_filter = Control.MOUSE_FILTER_STOP if on else Control.MOUSE_FILTER_IGNORE


func is_black() -> bool:
	return _black.color.a > 0.99


func letterbox(on := true, t := 0.6) -> void:
	_letterboxed = on
	if _bar_tw != null and _bar_tw.is_valid():
		_bar_tw.kill()
	_top.visible = true
	_bottom.visible = true
	var rm := Kit.reduced_motion()
	var top_y := 0.0 if on else -BAR
	var bot_y := 1080.0 - BAR if on else 1080.0
	if t <= 0.0:
		_top.position.y = top_y
		_bottom.position.y = bot_y
		_top.visible = on
		_bottom.visible = on
		return
	_bar_tw = create_tween().set_parallel(true)
	if rm:
		_top.position.y = 0.0
		_bottom.position.y = 1080.0 - BAR
		if on:
			_top.modulate.a = 0.0
			_bottom.modulate.a = 0.0
		_bar_tw.tween_property(_top, "modulate:a", 1.0 if on else 0.0, t * 0.6)
		_bar_tw.tween_property(_bottom, "modulate:a", 1.0 if on else 0.0, t * 0.6)
	else:
		_top.modulate.a = 1.0
		_bottom.modulate.a = 1.0
		_bar_tw.tween_property(_top, "position:y", top_y, t).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
		_bar_tw.tween_property(_bottom, "position:y", bot_y, t).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	if not on:
		_bar_tw.chain().tween_callback(func():
			_top.visible = false
			_bottom.visible = false)


func show_letterbox(t := 0.6) -> void:
	letterbox(true, t)


func hide_letterbox(t := 0.6) -> void:
	letterbox(false, t)


func is_letterboxed() -> bool:
	return _letterboxed
