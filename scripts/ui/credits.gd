extends "res://scripts/ui/ui_modal.gd"
## Credits: tools, generators, fonts with licences, asset provenance, AI-assisted development note and the
## alternative-history disclaimer. Slow auto-scroll (off with reduced motion; manual scroll always works).

const SECTIONS := [["ui.credits.h_project", "ui.credits.project"], ["ui.credits.h_tools", "ui.credits.tools"],
	["ui.credits.h_generators", "ui.credits.generators"], ["ui.credits.h_fonts", "ui.credits.fonts"],
	["ui.credits.h_assets", "ui.credits.assets"], ["ui.credits.h_ai", "ui.credits.ai"],
	["ui.credits.h_disclaimer", "ui.credits.disclaimer"]]

var _scroll: ScrollContainer
var _auto := 0.0
var _hold := 0.0
var _back: Button


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.82))
	var p := Kit.panel("SolidPanel")
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.offset_left = -600
	p.offset_right = 600
	p.offset_top = -470
	p.offset_bottom = 470
	add_child(p)
	var v := Kit.vbox(14)
	p.add_child(v)
	v.add_child(Kit.label(Kit.t("ui.credits.title"), "HeadingLabel"))
	v.add_child(HSeparator.new())
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(_scroll)
	var body := Kit.vbox(30)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var pad := Kit.margin(24, 24, 36, 120)
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pad.add_child(body)
	_scroll.add_child(pad)
	var version := str(ProjectSettings.get_setting("application/config/version", "0.1.0"))
	for s in SECTIONS:
		var sec := Kit.vbox(8)
		var head := Kit.hbox(14)
		var orn := Kit.sprite("icons/ornament_diamond.png")
		orn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		head.add_child(orn)
		head.add_child(Kit.label(Kit.t(s[0]).to_upper(), "KickerLabel", 24))
		sec.add_child(head)
		var txt := Kit.wrap_label(Kit.t(s[1], {"version": version}), "BodyLabel")
		Kit.scalable(txt, 29)
		sec.add_child(txt)
		body.add_child(sec)
	var thanks := Kit.label(Kit.t("ui.credits.thanks"), "BodyLabel", 34)
	thanks.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	thanks.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(thanks)
	var foot := Kit.hbox(0)
	foot.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(foot)
	_back = Kit.button(Kit.t("ui.back"), "", 220)
	_back.pressed.connect(close)
	foot.add_child(_back)


func open() -> void:
	open_modal()


func _on_open() -> void:
	_scroll.scroll_vertical = 0
	_auto = 0.0
	_hold = 2.5


func _process(delta: float) -> void:
	if not is_open or Kit.reduced_motion():
		return
	if _hold > 0.0:
		_hold -= delta
		return
	_auto += delta * 26.0
	if _auto >= 1.0:
		var step := int(_auto)
		_auto -= step
		_scroll.scroll_vertical += step


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		_hold = 4.0


func modal_input(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_up", true) or event.is_action_pressed("ui_down", true):
		_hold = 4.0
		_scroll.scroll_vertical += -60 if event.is_action_pressed("ui_up", true) else 60
		return true
	return false


func focus_default() -> void:
	_back.grab_focus()
