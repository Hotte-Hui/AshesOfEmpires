extends SceneTree
## Builds res://assets/ui/theme.tres + theme_hc.tres (high contrast) and the FontVariation resources in
## res://assets/fonts/ from the pixel-art UI kit (tools/pixelgen/gen_ui.py, textures stored at x3).
## Deterministic; rerun after changing the kit:
##   godot --headless --path . --import
##   godot --headless --path . --script res://scripts/ui/dev/build_theme.gd

const UI := "res://assets/ui/"
const FONTS := "res://assets/fonts/"

const TEXT := Color("e6dec2")
const TEXT_BRIGHT := Color("f5efda")
const TEXT_DIM := Color("a3aca2")
const DISABLED := Color("5f6b69")
const COPPER := Color("ba775b")
const COPPER_L := Color("dca16e")
const AMBER := Color("f0c487")
const AMBER_L := Color("fbe3ae")
const INK := Color("1a1c2a")
const INK_B := Color("2e3248")
const INK_DIM := Color("4d4a42")
const PAPER_D := Color("8e8a78")
const STAMP := Color("a8382e")

var fonts := {}


func _init() -> void:
	var ok := _make_fonts()
	if ok:
		ok = _save(_build(false), UI + "theme.tres") and _save(_build(true), UI + "theme_hc.tres")
	print("BUILD_THEME ", "OK" if ok else "FAILED")
	quit(0 if ok else 1)


func _save(r: Resource, path: String) -> bool:
	var e := ResourceSaver.save(r, path)
	if e != OK:
		push_error("cannot save %s (%d)" % [path, e])
		return false
	return true


# ------------------------------------------------------------------ fonts
func _ff(path: String) -> FontFile:
	var f := load(FONTS + path) as FontFile
	if f == null:
		push_error("font missing: " + path)
	return f


func _fv(name: String, base: FontFile, weight := 0, spacing := 0, embolden := 0.0) -> FontVariation:
	var mono := _ff("pt_mono/PTM55FT.ttf")
	var fv := FontVariation.new()
	fv.base_font = base
	if weight > 0:
		var ts := TextServerManager.get_primary_interface()
		fv.variation_opentype = {ts.name_to_tag("weight"): weight}
	if spacing != 0:
		fv.spacing_glyph = spacing
	if embolden != 0.0:
		fv.variation_embolden = embolden
	if mono != null and base != mono:
		fv.fallbacks = [mono]
	var path := FONTS + name + ".tres"
	if not _save(fv, path):
		return null
	var loaded := load(path) as FontVariation
	fonts[name] = loaded
	return loaded


func _make_fonts() -> bool:
	var serif := _ff("pt_serif/PT_Serif-Web-Regular.ttf")
	var serif_i := _ff("pt_serif/PT_Serif-Web-Italic.ttf")
	var serif_b := _ff("pt_serif/PT_Serif-Web-Bold.ttf")
	var serif_bi := _ff("pt_serif/PT_Serif-Web-BoldItalic.ttf")
	var oswald := _ff("oswald/Oswald-VariableFont_wght.ttf")
	var cp := _ff("courier_prime/CourierPrime-Regular.ttf")
	var cp_b := _ff("courier_prime/CourierPrime-Bold.ttf")
	var mono := _ff("pt_mono/PTM55FT.ttf")
	for f in [serif, serif_i, serif_b, serif_bi, oswald, cp, cp_b, mono]:
		if f == null:
			return false
	_fv("fv_serif", serif)
	_fv("fv_serif_italic", serif_i)
	_fv("fv_serif_bold", serif_b)
	_fv("fv_serif_bold_italic", serif_bi)
	_fv("fv_display", oswald, 500, 7)       # main title
	_fv("fv_heading", oswald, 500, 3)       # panel titles
	_fv("fv_label", oswald, 500, 4)         # small tracked capitals (kickers, speaker names, tabs)
	_fv("fv_button", oswald, 400, 2)        # buttons / menus
	_fv("fv_type", cp)                      # typewritten records
	_fv("fv_type_bold", cp_b)
	_fv("fv_mono", mono)
	return fonts.size() == 11


# ------------------------------------------------------------------ styleboxes
## margins in screen px (texture is stored at x3), content margins l,t,r,b
func _tb(file: String, m: Array, cm: Array = [], draw_center := true) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = load(UI + file) as Texture2D
	if sb.texture == null:
		push_error("missing texture " + file)
	sb.texture_margin_left = m[0]
	sb.texture_margin_top = m[1]
	sb.texture_margin_right = m[2]
	sb.texture_margin_bottom = m[3]
	var c: Array = cm if not cm.is_empty() else m
	sb.content_margin_left = c[0]
	sb.content_margin_top = c[1]
	sb.content_margin_right = c[2]
	sb.content_margin_bottom = c[3]
	sb.draw_center = draw_center
	return sb


func _empty(cm: Array) -> StyleBoxEmpty:
	var sb := StyleBoxEmpty.new()
	sb.content_margin_left = cm[0]
	sb.content_margin_top = cm[1]
	sb.content_margin_right = cm[2]
	sb.content_margin_bottom = cm[3]
	return sb


func _flat(col: Color, cm: Array = [0, 0, 0, 0]) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.content_margin_left = cm[0]
	sb.content_margin_top = cm[1]
	sb.content_margin_right = cm[2]
	sb.content_margin_bottom = cm[3]
	return sb


func _line(col: Color, thick: int) -> StyleBoxLine:
	var sb := StyleBoxLine.new()
	sb.color = col
	sb.thickness = thick
	return sb


func _button_colors(th: Theme, type: String, normal: Color, hot: Color, pressed: Color, disabled: Color) -> void:
	th.set_color("font_color", type, normal)
	th.set_color("font_hover_color", type, hot)
	th.set_color("font_focus_color", type, hot)
	th.set_color("font_pressed_color", type, pressed)
	th.set_color("font_hover_pressed_color", type, hot)
	th.set_color("font_disabled_color", type, disabled)
	th.set_color("font_outline_color", type, Color(0, 0, 0, 0))
	th.set_color("icon_normal_color", type, Color.WHITE)
	th.set_color("icon_hover_color", type, Color.WHITE)
	th.set_color("icon_focus_color", type, Color.WHITE)
	th.set_color("icon_pressed_color", type, Color.WHITE)
	th.set_color("icon_disabled_color", type, Color(1, 1, 1, 0.45))


func _label(th: Theme, name: String, font: String, size: int, col: Color, base := "Label") -> void:
	th.set_type_variation(name, base)
	th.set_font("font", name, fonts[font])
	th.set_font_size("font_size", name, size)
	th.set_color("font_color", name, col)


# ------------------------------------------------------------------ theme
func _build(hc: bool) -> Theme:
	var th := Theme.new()
	var text := TEXT_BRIGHT if hc else TEXT
	var dim := TEXT if hc else TEXT_DIM
	var accent := AMBER if hc else COPPER_L
	th.default_font = fonts["fv_serif"]
	th.default_font_size = 30

	# --- Label + variations
	th.set_color("font_color", "Label", text)
	th.set_color("font_shadow_color", "Label", Color(0, 0, 0, 0))
	th.set_constant("line_spacing", "Label", 4)
	_label(th, "TitleLabel", "fv_display", 132, TEXT_BRIGHT)
	_label(th, "SubtitleLabel", "fv_heading", 40, accent)
	_label(th, "HeadingLabel", "fv_heading", 50, TEXT_BRIGHT)
	_label(th, "KickerLabel", "fv_label", 22, accent)
	_label(th, "BodyLabel", "fv_serif", 30, text)
	_label(th, "DimLabel", "fv_serif_italic", 24, dim)
	_label(th, "HintLabel", "fv_label", 20, dim)
	_label(th, "SpeakerLabel", "fv_label", 28, AMBER if hc else COPPER_L)
	_label(th, "DialogueLabel", "fv_serif", 34, TEXT_BRIGHT)
	_label(th, "ObjectiveLabel", "fv_serif", 27, TEXT_BRIGHT if hc else TEXT)
	_label(th, "KeyLabel", "fv_button", 24, TEXT_BRIGHT)
	_label(th, "KeyHintLabel", "fv_button", 19, TEXT_BRIGHT)
	_label(th, "ControlHintLabel", "fv_serif_italic", 23, dim)
	_label(th, "TypeLabel", "fv_type", 28, INK)
	_label(th, "TypeHeading", "fv_type_bold", 36, INK)
	_label(th, "TypeDim", "fv_type", 23, INK_B if hc else INK_DIM)
	_label(th, "PaperKicker", "fv_label", 21, STAMP if not hc else Color("7a2a26"))
	_label(th, "PaperBody", "fv_serif", 28, INK)
	_label(th, "StampLabel", "fv_heading", 26, STAMP)
	th.set_constant("line_spacing", "TypeLabel", 6)
	th.set_constant("line_spacing", "DialogueLabel", 6)

	# --- panels
	th.set_stylebox("panel", "PanelContainer", _tb("frames/panel_hc.png" if hc else "frames/panel.png", [18, 18, 18, 18], [42, 36, 42, 36]))
	th.set_stylebox("panel", "Panel", _tb("frames/panel_hc.png" if hc else "frames/panel.png", [18, 18, 18, 18]))
	th.set_type_variation("PaperPanel", "PanelContainer")
	th.set_stylebox("panel", "PaperPanel", _tb("frames/paper.png", [21, 21, 21, 21], [54, 48, 54, 48]))
	th.set_type_variation("PaperCardPanel", "PanelContainer")
	th.set_stylebox("panel", "PaperCardPanel", _tb("frames/paper_card.png", [9, 9, 9, 9], [24, 16, 24, 16]))
	th.set_type_variation("PlatePanel", "PanelContainer")
	var plate := _tb("frames/plate.png", [15, 9, 9, 9], [34, 16, 30, 18])
	if hc:
		plate.modulate_color = Color(1, 1, 1, 1)
	th.set_stylebox("panel", "PlatePanel", plate)
	th.set_type_variation("PromptPanel", "PanelContainer")
	th.set_stylebox("panel", "PromptPanel", _tb("frames/prompt.png", [9, 9, 9, 9], [14, 10, 22, 10]))
	th.set_type_variation("KeycapPanel", "PanelContainer")
	th.set_stylebox("panel", "KeycapPanel", _tb("frames/keycap.png", [12, 12, 12, 15], [14, 4, 14, 14]))
	th.set_type_variation("KeyChipPanel", "PanelContainer")
	th.set_stylebox("panel", "KeyChipPanel", _tb("frames/keycap.png", [12, 12, 12, 15], [11, 3, 11, 13]))
	th.set_type_variation("PortraitPanel", "PanelContainer")
	th.set_stylebox("panel", "PortraitPanel", _tb("frames/portrait_frame.png", [12, 12, 12, 12], [12, 12, 12, 12], false))
	th.set_type_variation("SlotPanel", "PanelContainer")
	th.set_stylebox("panel", "SlotPanel", _tb("frames/slot.png", [9, 9, 9, 9], [24, 16, 24, 16]))
	th.set_type_variation("DialoguePanel", "PanelContainer")
	th.set_stylebox("panel", "DialoguePanel", _tb("frames/panel_hc.png" if hc else "frames/panel.png", [18, 18, 18, 18], [44, 24, 44, 22]))
	th.set_type_variation("SolidPanel", "PanelContainer")
	th.set_stylebox("panel", "SolidPanel", _tb("frames/panel_hc.png" if hc else "frames/panel_solid.png", [18, 18, 18, 18], [42, 36, 42, 36]))
	th.set_type_variation("BandPanel", "PanelContainer")
	th.set_stylebox("panel", "BandPanel", _tb("frames/band.png", [72, 18, 72, 18], [120, 30, 120, 30]))
	th.set_type_variation("ClearPanel", "PanelContainer")
	th.set_stylebox("panel", "ClearPanel", _empty([0, 0, 0, 0]))

	# --- default Button (bordered action button)
	var bcm := [26, 11, 26, 13]
	th.set_font("font", "Button", fonts["fv_button"])
	th.set_font_size("font_size", "Button", 28)
	_button_colors(th, "Button", text, AMBER_L if hc else AMBER, COPPER_L, DISABLED)
	th.set_stylebox("normal", "Button", _tb("frames/button_normal.png", [9, 9, 9, 9], bcm))
	th.set_stylebox("hover", "Button", _tb("frames/button_hover.png", [9, 9, 9, 9], bcm))
	th.set_stylebox("hover_pressed", "Button", _tb("frames/button_hover.png", [9, 9, 9, 9], bcm))
	th.set_stylebox("pressed", "Button", _tb("frames/button_pressed.png", [9, 9, 9, 9], bcm))
	th.set_stylebox("disabled", "Button", _tb("frames/button_disabled.png", [9, 9, 9, 9], bcm))
	th.set_stylebox("focus", "Button", _tb("frames/button_focus.png", [9, 9, 9, 9], bcm, false))
	th.set_constant("h_separation", "Button", 12)
	th.set_constant("outline_size", "Button", 0)

	# --- MenuButton: text list with copper index bar (main / pause menu)
	var mcm := [34, 7, 28, 9]
	th.set_type_variation("MenuEntry", "Button")
	th.set_font("font", "MenuEntry", fonts["fv_button"])
	th.set_font_size("font_size", "MenuEntry", 36)
	_button_colors(th, "MenuEntry", text, AMBER_L if hc else AMBER, COPPER_L, DISABLED)
	th.set_stylebox("normal", "MenuEntry", _empty(mcm))
	th.set_stylebox("hover", "MenuEntry", _empty(mcm))
	th.set_stylebox("hover_pressed", "MenuEntry", _tb("frames/menu_pressed.png", [12, 3, 3, 3], mcm))
	th.set_stylebox("pressed", "MenuEntry", _tb("frames/menu_pressed.png", [12, 3, 3, 3], mcm))
	th.set_stylebox("disabled", "MenuEntry", _empty(mcm))
	th.set_stylebox("focus", "MenuEntry", _tb("frames/menu_focus.png", [12, 3, 3, 3], mcm))

	# --- ChoiceButton: dialogue choices (serif, wraps)
	var ccm := [40, 10, 28, 12]
	th.set_type_variation("ChoiceButton", "Button")
	th.set_font("font", "ChoiceButton", fonts["fv_serif"])
	th.set_font_size("font_size", "ChoiceButton", 32)
	_button_colors(th, "ChoiceButton", text, AMBER_L if hc else AMBER, COPPER_L, DISABLED)
	th.set_stylebox("normal", "ChoiceButton", _empty(ccm))
	th.set_stylebox("hover", "ChoiceButton", _empty(ccm))
	th.set_stylebox("hover_pressed", "ChoiceButton", _tb("frames/menu_pressed.png", [12, 3, 3, 3], ccm))
	th.set_stylebox("pressed", "ChoiceButton", _tb("frames/menu_pressed.png", [12, 3, 3, 3], ccm))
	th.set_stylebox("disabled", "ChoiceButton", _empty(ccm))
	th.set_stylebox("focus", "ChoiceButton", _tb("frames/menu_focus.png", [12, 3, 3, 3], ccm))

	# --- ListButton: compact list rows (journal lists, credits) on navy
	var lcm := [30, 8, 20, 10]
	th.set_type_variation("ListButton", "Button")
	th.set_font("font", "ListButton", fonts["fv_serif"])
	th.set_font_size("font_size", "ListButton", 28)
	_button_colors(th, "ListButton", text, AMBER_L if hc else AMBER, COPPER_L, DISABLED)
	for s in ["normal", "hover", "disabled"]:
		th.set_stylebox(s, "ListButton", _empty(lcm))
	th.set_stylebox("pressed", "ListButton", _tb("frames/menu_focus.png", [12, 3, 3, 3], lcm))
	th.set_stylebox("hover_pressed", "ListButton", _tb("frames/menu_focus.png", [12, 3, 3, 3], lcm))
	th.set_stylebox("focus", "ListButton", _tb("frames/menu_focus.png", [12, 3, 3, 3], lcm))

	# --- PaperListButton: rows on paper (journal evidence / people)
	var pcm := [24, 9, 20, 11]
	th.set_type_variation("PaperListButton", "Button")
	th.set_font("font", "PaperListButton", fonts["fv_type"])
	th.set_font_size("font_size", "PaperListButton", 27)
	_button_colors(th, "PaperListButton", INK, Color("7a2a26"), Color("7a2a26"), INK_DIM)
	for s in ["normal", "hover", "disabled"]:
		th.set_stylebox(s, "PaperListButton", _empty(pcm))
	th.set_stylebox("pressed", "PaperListButton", _tb("frames/paper_card.png", [9, 9, 9, 9], pcm))
	th.set_stylebox("hover_pressed", "PaperListButton", _tb("frames/paper_card.png", [9, 9, 9, 9], pcm))
	th.set_stylebox("focus", "PaperListButton", _tb("frames/paper_row.png", [12, 3, 3, 3], pcm))

	# --- tabs (navy) and paper index tabs (journal dossier)
	var tcm := [30, 15, 30, 11]
	th.set_type_variation("TabButton", "Button")
	th.set_font("font", "TabButton", fonts["fv_label"])
	th.set_font_size("font_size", "TabButton", 24)
	_button_colors(th, "TabButton", dim, AMBER, TEXT_BRIGHT, DISABLED)
	th.set_stylebox("normal", "TabButton", _tb("frames/tab_normal.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("hover", "TabButton", _tb("frames/tab_hover.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("pressed", "TabButton", _tb("frames/tab_pressed.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("hover_pressed", "TabButton", _tb("frames/tab_pressed.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("disabled", "TabButton", _tb("frames/tab_normal.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("focus", "TabButton", _tb("frames/tab_focus.png", [12, 12, 12, 6], tcm, false))
	th.set_type_variation("PaperTabButton", "Button")
	th.set_font("font", "PaperTabButton", fonts["fv_label"])
	th.set_font_size("font_size", "PaperTabButton", 24)
	_button_colors(th, "PaperTabButton", INK_DIM if not hc else INK, Color("7a2a26"), INK, DISABLED)
	th.set_stylebox("normal", "PaperTabButton", _tb("frames/ptab_normal.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("hover", "PaperTabButton", _tb("frames/ptab_hover.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("pressed", "PaperTabButton", _tb("frames/ptab_pressed.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("hover_pressed", "PaperTabButton", _tb("frames/ptab_pressed.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("disabled", "PaperTabButton", _tb("frames/ptab_normal.png", [12, 12, 12, 6], tcm))
	th.set_stylebox("focus", "PaperTabButton", _tb("frames/ptab_focus.png", [12, 12, 12, 6], tcm, false))

	# --- SlotButton (save slots), CardButton (puzzle cards), SmallButton, LinkButton-like FlatButton
	var scm := [30, 18, 30, 18]
	th.set_type_variation("SlotButton", "Button")
	th.set_font("font", "SlotButton", fonts["fv_button"])
	th.set_font_size("font_size", "SlotButton", 28)
	_button_colors(th, "SlotButton", text, AMBER, COPPER_L, DISABLED)
	th.set_stylebox("normal", "SlotButton", _tb("frames/slot.png", [9, 9, 9, 9], scm))
	th.set_stylebox("hover", "SlotButton", _tb("frames/button_hover.png", [9, 9, 9, 9], scm))
	th.set_stylebox("pressed", "SlotButton", _tb("frames/button_hover.png", [9, 9, 9, 9], scm))
	th.set_stylebox("hover_pressed", "SlotButton", _tb("frames/button_hover.png", [9, 9, 9, 9], scm))
	th.set_stylebox("disabled", "SlotButton", _tb("frames/button_disabled.png", [9, 9, 9, 9], scm))
	th.set_stylebox("focus", "SlotButton", _tb("frames/button_focus.png", [9, 9, 9, 9], scm, false))
	# FieldButton: value fields in settings (steppers, key bindings) — compact SlotButton
	var fcm := [24, 9, 24, 11]
	th.set_type_variation("FieldButton", "Button")
	th.set_font("font", "FieldButton", fonts["fv_button"])
	th.set_font_size("font_size", "FieldButton", 27)
	_button_colors(th, "FieldButton", text, AMBER, COPPER_L, DISABLED)
	th.set_stylebox("normal", "FieldButton", _tb("frames/slot.png", [9, 9, 9, 9], fcm))
	th.set_stylebox("hover", "FieldButton", _tb("frames/button_hover.png", [9, 9, 9, 9], fcm))
	th.set_stylebox("pressed", "FieldButton", _tb("frames/button_hover.png", [9, 9, 9, 9], fcm))
	th.set_stylebox("hover_pressed", "FieldButton", _tb("frames/button_hover.png", [9, 9, 9, 9], fcm))
	th.set_stylebox("disabled", "FieldButton", _tb("frames/button_disabled.png", [9, 9, 9, 9], fcm))
	th.set_stylebox("focus", "FieldButton", _tb("frames/button_focus.png", [9, 9, 9, 9], fcm, false))
	th.set_type_variation("CardButton", "Button")
	for s in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
		th.set_stylebox(s, "CardButton", _empty([9, 9, 9, 9]))
	th.set_stylebox("focus", "CardButton", _tb("frames/button_focus.png", [9, 9, 9, 9], [9, 9, 9, 9], false))
	_button_colors(th, "CardButton", text, AMBER, COPPER_L, DISABLED)
	th.set_type_variation("SmallButton", "Button")
	th.set_font("font", "SmallButton", fonts["fv_label"])
	th.set_font_size("font_size", "SmallButton", 21)
	var smcm := [18, 7, 18, 9]
	th.set_stylebox("normal", "SmallButton", _tb("frames/button_normal.png", [9, 9, 9, 9], smcm))
	th.set_stylebox("hover", "SmallButton", _tb("frames/button_hover.png", [9, 9, 9, 9], smcm))
	th.set_stylebox("hover_pressed", "SmallButton", _tb("frames/button_hover.png", [9, 9, 9, 9], smcm))
	th.set_stylebox("pressed", "SmallButton", _tb("frames/button_pressed.png", [9, 9, 9, 9], smcm))
	th.set_stylebox("disabled", "SmallButton", _tb("frames/button_disabled.png", [9, 9, 9, 9], smcm))
	th.set_stylebox("focus", "SmallButton", _tb("frames/button_focus.png", [9, 9, 9, 9], smcm, false))
	_button_colors(th, "SmallButton", dim, AMBER, COPPER_L, DISABLED)

	# --- CheckBox (settings toggles)
	th.set_icon("checked", "CheckBox", load(UI + "icons/check_on.png"))
	th.set_icon("unchecked", "CheckBox", load(UI + "icons/check_off.png"))
	th.set_icon("checked_disabled", "CheckBox", load(UI + "icons/check_on_disabled.png"))
	th.set_icon("unchecked_disabled", "CheckBox", load(UI + "icons/check_off_disabled.png"))
	th.set_font("font", "CheckBox", fonts["fv_button"])
	th.set_font_size("font_size", "CheckBox", 26)
	_button_colors(th, "CheckBox", text, AMBER, COPPER_L, DISABLED)
	var ckcm := [14, 6, 18, 6]
	for s in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
		th.set_stylebox(s, "CheckBox", _empty(ckcm))
	th.set_stylebox("focus", "CheckBox", _tb("frames/button_focus.png", [9, 9, 9, 9], ckcm, false))
	th.set_constant("h_separation", "CheckBox", 14)

	# --- HSlider
	th.set_stylebox("slider", "HSlider", _tb("frames/slider_track.png", [6, 6, 6, 6], [0, 6, 0, 6]))
	th.set_stylebox("grabber_area", "HSlider", _tb("frames/slider_fill.png", [6, 6, 6, 6], [0, 6, 0, 6]))
	th.set_stylebox("grabber_area_highlight", "HSlider", _tb("frames/slider_fill.png", [6, 6, 6, 6], [0, 6, 0, 6]))
	th.set_icon("grabber", "HSlider", load(UI + "icons/slider_grabber.png"))
	th.set_icon("grabber_highlight", "HSlider", load(UI + "icons/slider_grabber_hl.png"))
	th.set_icon("grabber_disabled", "HSlider", load(UI + "icons/slider_grabber_off.png"))
	th.set_constant("center_grabber", "HSlider", 1)

	# --- scrolling
	th.set_stylebox("scroll", "VScrollBar", _tb("frames/scroll_track.png", [6, 6, 6, 6], [0, 0, 0, 0]))
	th.set_stylebox("scroll_focus", "VScrollBar", _tb("frames/scroll_track.png", [6, 6, 6, 6], [0, 0, 0, 0]))
	th.set_stylebox("grabber", "VScrollBar", _tb("frames/scroll_grabber.png", [6, 6, 6, 6], [0, 0, 0, 0]))
	th.set_stylebox("grabber_highlight", "VScrollBar", _tb("frames/scroll_grabber_hl.png", [6, 6, 6, 6], [0, 0, 0, 0]))
	th.set_stylebox("grabber_pressed", "VScrollBar", _tb("frames/scroll_grabber_hl.png", [6, 6, 6, 6], [0, 0, 0, 0]))
	var noicon := ImageTexture.create_from_image(Image.create(1, 1, false, Image.FORMAT_RGBA8))
	for i in ["increment", "increment_highlight", "increment_pressed", "decrement", "decrement_highlight", "decrement_pressed"]:
		th.set_icon(i, "VScrollBar", noicon)
	th.set_stylebox("panel", "ScrollContainer", _empty([0, 0, 0, 0]))
	th.set_stylebox("focus", "ScrollContainer", _empty([0, 0, 0, 0]))

	# --- separators
	th.set_stylebox("separator", "HSeparator", _line(COPPER, 3))
	th.set_constant("separation", "HSeparator", 18)
	th.set_type_variation("PaperSeparator", "HSeparator")
	th.set_stylebox("separator", "PaperSeparator", _line(PAPER_D, 3))
	th.set_type_variation("FaintSeparator", "HSeparator")
	th.set_stylebox("separator", "FaintSeparator", _line(Color("24373a"), 3))

	# --- rich text, tooltip, line edit
	th.set_font("normal_font", "RichTextLabel", fonts["fv_serif"])
	th.set_font("bold_font", "RichTextLabel", fonts["fv_serif_bold"])
	th.set_font("italics_font", "RichTextLabel", fonts["fv_serif_italic"])
	th.set_font("bold_italics_font", "RichTextLabel", fonts["fv_serif_bold_italic"])
	th.set_font("mono_font", "RichTextLabel", fonts["fv_type"])
	for k in ["normal_font_size", "bold_font_size", "italics_font_size", "bold_italics_font_size", "mono_font_size"]:
		th.set_font_size(k, "RichTextLabel", 30)
	th.set_color("default_color", "RichTextLabel", text)
	th.set_constant("line_separation", "RichTextLabel", 6)
	th.set_stylebox("normal", "RichTextLabel", _empty([0, 0, 0, 0]))
	th.set_stylebox("focus", "RichTextLabel", _empty([0, 0, 0, 0]))
	th.set_stylebox("panel", "TooltipPanel", _tb("frames/prompt.png", [9, 9, 9, 9], [16, 10, 16, 12]))
	th.set_font("font", "TooltipLabel", fonts["fv_serif"])
	th.set_font_size("font_size", "TooltipLabel", 24)
	th.set_color("font_color", "TooltipLabel", text)
	th.set_stylebox("normal", "LineEdit", _tb("frames/slot.png", [9, 9, 9, 9], [18, 10, 18, 10]))
	th.set_stylebox("focus", "LineEdit", _tb("frames/button_focus.png", [9, 9, 9, 9], [18, 10, 18, 10], false))
	th.set_color("font_color", "LineEdit", text)
	th.set_color("caret_color", "LineEdit", AMBER)
	return th
