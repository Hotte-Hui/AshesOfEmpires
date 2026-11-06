extends Control
## Subtitles for camera moves and cutscenes: always on the same high-contrast navy plate, bottom centre
## (inside the lower letterbox bar while letterboxed). Respects Settings.subtitles unless forced.
## API: show_text(text, duration), show_subtitle(text, duration, speaker, force), hide_subtitle(), clear().

const Kit := preload("res://scripts/ui/ui_kit.gd")

var ui_root: Node = null
var _plate: PanelContainer
var _label: RichTextLabel
var _timer := 0.0
var _tween: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(self)
	_plate = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.016, 0.035, 0.05, 0.86)
	sb.content_margin_left = 30
	sb.content_margin_right = 30
	sb.content_margin_top = 12
	sb.content_margin_bottom = 14
	_plate.add_theme_stylebox_override("panel", sb)
	_plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_plate.visible = false
	add_child(_plate)
	_label = RichTextLabel.new()
	_label.bbcode_enabled = true
	_label.fit_content = true
	_label.scroll_active = false
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.custom_minimum_size.x = 400
	Kit.scalable(_label, 32)
	_plate.add_child(_label)


func show_text(text: String, duration := 0.0) -> void:
	show_subtitle(text, duration)


func show_subtitle(text: String, duration := 0.0, speaker := "", force := false) -> void:
	if not force and not bool(Kit.setting("subtitles", true)):
		return
	var body := Kit.resolve(text).replace("[", "[lb]")
	var bb := "[center]"
	if speaker != "":
		bb += "[color=#dca16e]%s[/color]   " % Kit.char_name(speaker).to_upper().replace("ß", "SS")
	bb += body + "[/center]"
	_label.text = bb
	var w := clampf(body.length() * 17.0 * Kit.text_scale() + 60.0, 420.0, 1400.0)
	_label.custom_minimum_size.x = w
	_plate.reset_size()
	_plate.visible = true
	_layout.call_deferred()
	_timer = duration if duration > 0.0 else clampf(2.4 + body.length() * 0.055, 2.5, 9.0)
	if _tween != null and _tween.is_valid():
		_tween.kill()
	_plate.modulate.a = 0.0
	_tween = create_tween()
	_tween.tween_property(_plate, "modulate:a", 1.0, 0.25)


func hide_subtitle() -> void:
	if not _plate.visible:
		return
	if _tween != null and _tween.is_valid():
		_tween.kill()
	_tween = create_tween()
	_tween.tween_property(_plate, "modulate:a", 0.0, 0.3)
	_tween.tween_callback(func(): _plate.visible = false)
	_timer = 0.0


func clear() -> void:
	_plate.visible = false
	_timer = 0.0


func is_showing() -> bool:
	return _plate.visible


func _layout() -> void:
	var sz := _plate.get_combined_minimum_size()
	_plate.size = sz
	var lb := false
	if ui_root != null and ui_root.get("fade") != null and ui_root.fade.has_method("is_letterboxed"):
		lb = ui_root.fade.is_letterboxed()
	var y := (1080.0 - 138.0 * 0.5 - sz.y * 0.5) if lb else (1080.0 - 84.0 - sz.y)
	_plate.position = Vector2(roundf((1920.0 - sz.x) * 0.5), roundf(y))


func _process(delta: float) -> void:
	if _timer > 0.0:
		_timer -= delta
		if _timer <= 0.0:
			hide_subtitle()
