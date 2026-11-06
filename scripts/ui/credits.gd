extends "res://scripts/ui/ui_modal.gd"
## Credits: tools, generators, fonts with licences, asset provenance, AI-assisted development note and the
## alternative-history disclaimer, then "Quellen der historischen Karten" (every real-history card with its
## sources; same builder as the end credits, EndCredits.add_source_list). Slow auto-scroll (off with reduced
## motion; arrows / page keys / wheel always work); the footer button jumps to the sources and back.

const EndCredits := preload("res://scripts/ui/end_credits.gd")
const SECTIONS := [["ui.credits.h_project", "ui.credits.project"], ["ui.credits.h_tools", "ui.credits.tools"],
	["ui.credits.h_generators", "ui.credits.generators"], ["ui.credits.h_fonts", "ui.credits.fonts"],
	["ui.credits.h_assets", "ui.credits.assets"], ["ui.credits.h_ai", "ui.credits.ai"],
	["ui.credits.h_disclaimer", "ui.credits.disclaimer"]]

var _scroll: ScrollContainer
var _auto := 0.0
var _hold := 0.0
var _back: Button
var _src_section: VBoxContainer
var _src_list: VBoxContainer
var _src_hc := false
var _src_btn: Button
var _src_past := false


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
		head.add_child(Kit.label(Kit.t(s[0]).to_upper().replace("ß", "SS"), "KickerLabel", 24))
		sec.add_child(head)
		var txt := Kit.wrap_label(Kit.t(s[1], {"version": version}), "BodyLabel")
		Kit.scalable(txt, 29)
		sec.add_child(txt)
		body.add_child(sec)
	_src_section = Kit.vbox(8)
	var shead := Kit.hbox(14)
	var sorn := Kit.sprite("icons/ornament_diamond.png")
	sorn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	shead.add_child(sorn)
	shead.add_child(Kit.label(Kit.t("credits.end.h_sources").to_upper().replace("ß", "SS"), "KickerLabel", 24))
	_src_section.add_child(shead)
	var sintro := Kit.wrap_label(Kit.t("credits.end.sources_intro"), "BodyLabel")
	Kit.scalable(sintro, 29)
	_src_section.add_child(sintro)
	_src_list = Kit.vbox(0)
	_src_section.add_child(_src_list)
	body.add_child(_src_section)
	_fill_sources()
	var thanks := Kit.label(Kit.t("ui.credits.thanks"), "BodyLabel", 34)
	thanks.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	thanks.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(thanks)
	var foot := Kit.hbox(18)
	foot.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(foot)
	_src_btn = Kit.button(Kit.t("credits.src.jump"), "", 300)
	_src_btn.pressed.connect(_toggle_sources)
	foot.add_child(_src_btn)
	_back = Kit.button(Kit.t("ui.back"), "", 220)
	_back.pressed.connect(close)
	foot.add_child(_back)


func open() -> void:
	open_modal()


func _on_open() -> void:
	if Kit.high_contrast() != _src_hc:
		_fill_sources()
	_scroll.scroll_vertical = 0
	_auto = 0.0
	_hold = 2.5


## (Re)builds the source list (colours follow high contrast at build time).
func _fill_sources() -> void:
	for c in _src_list.get_children():
		_src_list.remove_child(c)
		c.queue_free()
	_src_hc = Kit.high_contrast()
	EndCredits.add_source_list(_src_list, _src_hc)


## Scroll position of the sources heading inside the scroll content (pad top margin 24).
func _sources_y() -> int:
	return int(_src_section.position.y) + 24 - 8


## Footer button: jump to the sources, or back to the top when already there.
func _toggle_sources() -> void:
	_hold = 8.0
	_scroll.scroll_vertical = _sources_y() if _scroll.scroll_vertical < _sources_y() - 4 else 0


func _process(delta: float) -> void:
	if not is_open:
		return
	var past := _scroll.scroll_vertical >= _sources_y() - 4
	if past != _src_past:
		_src_past = past
		_src_btn.text = Kit.t("credits.src.top" if past else "credits.src.jump")
	if Kit.reduced_motion():
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
	for a in ["ui_page_up", "ui_page_down"]:
		if InputMap.has_action(a) and event.is_action_pressed(a, true):
			_hold = 4.0
			_scroll.scroll_vertical += -600 if a == "ui_page_up" else 600
			return true
	return false


func focus_default() -> void:
	_back.grab_focus()
