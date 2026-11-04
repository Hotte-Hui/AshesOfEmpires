extends "res://scripts/ui/ui_modal.gd"
## Settings: every key of scripts/core/settings.gd — fullscreen, vsync, pixel_post, the five volumes,
## text_scale (100/125/150 %, applied live), subtitles, dialogue_speed, high_contrast, reduced_motion,
## puzzle_hints — plus key rebinding for the main actions (Settings.rebind). Values are written through
## Settings.set_value (persisted by Settings). Left/right change the focused value; a line at the bottom
## explains the focused option.

const TABS := ["display", "audio", "access", "controls"]
const BIND_ACTIONS := ["move_left", "move_right", "move_up", "move_down", "run", "interact", "advance", "journal"]


class StepperButton extends Button:
	## One focusable control for discrete options: click/Enter = next, left/right = previous/next.
	signal value_picked(value)
	var options: Array = []          # [[value, label], ...]
	var index := 0
	var arrow_l: Texture2D
	var arrow_r: Texture2D

	func setup(opts: Array, current) -> void:
		options = opts
		index = 0
		var best := INF
		for i in options.size():
			var v = options[i][0]
			var d := absf(float(v) - float(current)) if (v is float or v is int) and (current is float or current is int) else (0.0 if v == current else 1.0)
			if d < best:
				best = d
				index = i
		_sync()

	func _sync() -> void:
		text = str(options[index][1]) if not options.is_empty() else ""

	func step(d: int) -> void:
		if options.is_empty() or disabled:
			return
		index = posmod(index + d, options.size())
		_sync()
		value_picked.emit(options[index][0])

	func _pressed() -> void:
		step(1)

	func _gui_input(e: InputEvent) -> void:
		if e.is_action_pressed("ui_left", true):
			step(-1)
			accept_event()
		elif e.is_action_pressed("ui_right", true):
			step(1)
			accept_event()

	func _draw() -> void:
		if arrow_l != null:
			draw_texture(arrow_l, Vector2(16, (size.y - arrow_l.get_height()) * 0.5).round())
		if arrow_r != null:
			draw_texture(arrow_r, Vector2(size.x - 16 - arrow_r.get_width(), (size.y - arrow_r.get_height()) * 0.5).round())


var current_tab := "display"
var _tab_buttons: Dictionary = {}
var _group := ButtonGroup.new()
var _rows_box: VBoxContainer
var _desc: Label
var _capturing := ""
var _capture_btn: Button = null
var _bind_buttons: Dictionary = {}
var _back_btn: Button
var _reset_btn: Button


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.7))
	var p := Kit.panel("SolidPanel")
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.offset_left = -690
	p.offset_right = 690
	p.offset_top = -500
	p.offset_bottom = 500
	add_child(p)
	var v := Kit.vbox(12)
	p.add_child(v)
	v.add_child(Kit.label(Kit.t("ui.settings.title"), "HeadingLabel"))
	var tabs := Kit.hbox(6)
	v.add_child(tabs)
	for id in TABS:
		var b := Kit.button(Kit.t("ui.settings.tab." + id).to_upper(), "TabButton")
		b.toggle_mode = true
		b.button_group = _group
		b.pressed.connect(show_tab.bind(id))
		tabs.add_child(b)
		_tab_buttons[id] = b
	var line := HSeparator.new()
	line.theme_type_variation = "FaintSeparator"
	line.add_theme_constant_override("separation", 0)
	v.add_child(line)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(scroll)
	var pad := Kit.margin(12, 18, 24, 12)
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(pad)
	_rows_box = Kit.vbox(6)
	_rows_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pad.add_child(_rows_box)
	v.add_child(HSeparator.new())
	_desc = Kit.wrap_label("", "DimLabel")
	_desc.custom_minimum_size.y = 40
	Kit.scalable(_desc, 25)
	v.add_child(_desc)
	var foot := Kit.hbox(18)
	foot.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(foot)
	_reset_btn = Kit.button(Kit.t("ui.settings.reset_bindings"), "", 260)
	_reset_btn.pressed.connect(_reset_bindings)
	foot.add_child(_reset_btn)
	_back_btn = Kit.button(Kit.t("ui.back"), "", 220)
	_back_btn.pressed.connect(close)
	foot.add_child(_back_btn)


func open(tab := "") -> void:
	if tab in TABS:
		current_tab = tab
	open_modal()
	show_tab(current_tab)


func show_tab(id: String) -> void:
	current_tab = id
	_cancel_capture()
	(_tab_buttons[id] as Button).button_pressed = true
	for c in _rows_box.get_children():
		_rows_box.remove_child(c)
		c.queue_free()
	_bind_buttons.clear()
	_reset_btn.visible = id == "controls"
	var have := Kit.svc("Settings") != null and Kit.has_svc("Settings", "set_value")
	match id:
		"display":
			_toggle_row("fullscreen")
			_toggle_row("vsync")
			_slider_row("pixel_post")
		"audio":
			for k in ["master_volume", "music_volume", "ambience_volume", "sfx_volume", "ui_volume"]:
				_slider_row(k)
		"access":
			_stepper_row("text_scale", [[1.0, "100 %"], [1.25, "125 %"], [1.5, "150 %"]])
			_toggle_row("subtitles")
			_stepper_row("dialogue_speed", [[0.6, Kit.t("ui.settings.speed.slow")], [1.0, Kit.t("ui.settings.speed.normal")],
				[1.6, Kit.t("ui.settings.speed.fast")], [0.0, Kit.t("ui.settings.speed.instant")]])
			_toggle_row("high_contrast")
			_toggle_row("reduced_motion")
			_stepper_row("puzzle_hints", [[0, Kit.t("ui.settings.hints.off")], [1, Kit.t("ui.settings.hints.after")],
				[2, Kit.t("ui.settings.hints.immediate")]])
		"controls":
			for a in BIND_ACTIONS:
				_bind_row(a)
			var note := Kit.wrap_label(Kit.t("ui.settings.bind_note"), "DimLabel")
			_rows_box.add_child(note)
	if not have:
		_rows_box.add_child(Kit.label(Kit.t("ui.settings.unavailable"), "DimLabel"))
	_desc.text = ""
	for h in _rows_box.get_children():
		if h.has_meta("desc"):
			_desc.text = Kit.t(str(h.get_meta("desc")))
			break
	if is_open:
		_focus_first_row.call_deferred()


func _row(key_label: String, desc_key: String) -> HBoxContainer:
	var h := Kit.hbox(24)
	h.custom_minimum_size.y = 62
	var l := Kit.label(Kit.t(key_label), "BodyLabel")
	l.custom_minimum_size.x = 560
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	Kit.scalable(l, 30)
	h.add_child(l)
	h.set_meta("desc", desc_key)
	_rows_box.add_child(h)
	return h


func _hook_desc(c: Control, desc_key: String) -> void:
	c.focus_entered.connect(func(): _desc.text = Kit.t(desc_key))
	c.mouse_entered.connect(func(): _desc.text = Kit.t(desc_key))


func _toggle_row(key: String) -> void:
	var h := _row("ui.settings." + key, "ui.settings.desc." + key)
	var cb := CheckBox.new()
	cb.button_pressed = bool(Kit.setting(key, false))
	cb.text = Kit.t("ui.common.on") if cb.button_pressed else Kit.t("ui.common.off")
	cb.focus_mode = Control.FOCUS_ALL
	cb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	cb.disabled = not Kit.has_svc("Settings", "set_value")
	cb.toggled.connect(func(on: bool):
		cb.text = Kit.t("ui.common.on") if on else Kit.t("ui.common.off")
		Kit.ui_sound("tick")
		Kit.set_setting(key, on))
	_hook_desc(cb, "ui.settings.desc." + key)
	h.add_child(cb)


func _slider_row(key: String) -> void:
	var h := _row("ui.settings." + key, "ui.settings.desc." + key)
	var s := HSlider.new()
	s.min_value = 0
	s.max_value = 100
	s.step = 5
	s.custom_minimum_size = Vector2(420, 42)
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	s.focus_mode = Control.FOCUS_ALL
	s.value = roundf(float(Kit.setting(key, 1.0)) * 100.0)
	s.editable = Kit.has_svc("Settings", "set_value")
	var val := Kit.label(Kit.t("ui.common.percent", {"v": int(s.value)}), "KickerLabel", 24)
	val.custom_minimum_size.x = 100
	val.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	val.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	s.value_changed.connect(func(x: float):
		val.text = Kit.t("ui.common.percent", {"v": int(x)})
		Kit.set_setting(key, x / 100.0))
	_hook_desc(s, "ui.settings.desc." + key)
	h.add_child(s)
	h.add_child(val)


func _stepper_row(key: String, opts: Array) -> void:
	var h := _row("ui.settings." + key, "ui.settings.desc." + key)
	var b := StepperButton.new()
	b.theme_type_variation = "FieldButton"
	b.custom_minimum_size = Vector2(460, 0)
	b.focus_mode = Control.FOCUS_ALL
	b.arrow_l = Kit.tex("res://assets/ui/icons/arrow_left.png")
	b.arrow_r = Kit.tex("res://assets/ui/icons/arrow_right.png")
	b.setup(opts, Kit.setting(key, opts[0][0]))
	b.disabled = not Kit.has_svc("Settings", "set_value")
	b.value_picked.connect(func(value):
		Kit.ui_sound("tick")
		Kit.set_setting(key, value))
	_hook_desc(b, "ui.settings.desc." + key)
	h.add_child(b)


func _bind_row(action: String) -> void:
	var h := _row("ui.settings.bind." + action, "ui.settings.desc.bind")
	var b := Kit.button(Kit.action_key_text(action), "FieldButton", 300)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.disabled = not Kit.has_svc("Settings", "rebind")
	b.pressed.connect(_begin_capture.bind(action, b))
	_hook_desc(b, "ui.settings.desc.bind")
	h.add_child(b)
	_bind_buttons[action] = b


# ================================================================ key capture
func _begin_capture(action: String, b: Button) -> void:
	_cancel_capture()
	_capturing = action
	_capture_btn = b
	b.text = Kit.t("ui.settings.press_key")


func _cancel_capture() -> void:
	if _capture_btn != null and is_instance_valid(_capture_btn):
		_capture_btn.text = Kit.action_key_text(_capturing)
	_capturing = ""
	_capture_btn = null


func modal_input(event: InputEvent) -> bool:
	if _capturing != "":
		if event is InputEventKey and event.pressed and not event.echo:
			var k := (event as InputEventKey).physical_keycode
			if k == KEY_ESCAPE:
				_cancel_capture()
				return true
			if k != KEY_NONE:
				var s := Kit.svc("Settings")
				if s != null and s.has_method("rebind"):
					s.rebind(_capturing, k)
				Kit.ui_sound("confirm")
				var b := _capture_btn
				_capture_btn = null
				_capturing = ""
				_refresh_bindings()
				if b != null:
					b.grab_focus.call_deferred()
			return true
		if event is InputEventMouseButton and event.pressed:
			_cancel_capture()
		return false
	if event is InputEventKey and event.pressed and not event.echo:
		var k2 := (event as InputEventKey).physical_keycode
		if k2 == KEY_Q or k2 == KEY_PAGEUP:
			_cycle(-1)
			return true
		if k2 == KEY_E or k2 == KEY_PAGEDOWN:
			_cycle(1)
			return true
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_LEFT_SHOULDER:
			_cycle(-1)
			return true
		if event.button_index == JOY_BUTTON_RIGHT_SHOULDER:
			_cycle(1)
			return true
	return false


func _cycle(d: int) -> void:
	var i := posmod(TABS.find(current_tab) + d, TABS.size())
	show_tab(TABS[i])
	(_tab_buttons[TABS[i]] as Button).grab_focus()


func _refresh_bindings() -> void:
	for a in _bind_buttons:
		(_bind_buttons[a] as Button).text = Kit.action_key_text(a)


func _reset_bindings() -> void:
	var s := Kit.svc("Settings")
	if s == null:
		return
	if s.has_method("reset_bindings"):
		s.reset_bindings()
	else:
		if "values" in s and s.values is Dictionary:
			for k in s.values.keys():
				if str(k).begins_with("bind_"):
					s.values.erase(k)
		if s.has_method("_build_input_map"):
			s._build_input_map()
		if s.has_method("save_settings"):
			s.save_settings()
	Kit.ui_sound("confirm")
	_refresh_bindings()


func handle_cancel() -> bool:
	if _capturing != "":
		_cancel_capture()
		return true
	return super.handle_cancel()


func _focus_first_row() -> void:
	for h in _rows_box.get_children():
		if h is HBoxContainer:
			for c in h.get_children():
				if c is Control and (c as Control).focus_mode == Control.FOCUS_ALL:
					(c as Control).grab_focus()
					return
	(_tab_buttons[current_tab] as Button).grab_focus()


func focus_default() -> void:
	_focus_first_row()

