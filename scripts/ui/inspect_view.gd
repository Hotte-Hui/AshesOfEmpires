extends "res://scripts/ui/ui_modal.gd"
## InspectView: open(item_id) shows the document image from assets/ui/documents/<doc>.png at integer scale
## (x3 when it fits — pixel layers are never scaled by non-integer factors) next to a typed paper record card
## with the localized item name/description, category and place of discovery. Missing images get an
## intentional placeholder frame. Also accepts an objective id (uses its grant_item) or a document name.

var suppress_toasts := true
var item_id := ""
var _stage: HBoxContainer
var _doc_holder: Control
var _doc_rect: TextureRect
var _doc_shadow: ColorRect
var _placeholder: PanelContainer
var _card: PanelContainer
var _kicker: Label
var _name: Label
var _desc: Label
var _meta: Label
var _stamp: Control
var _close_btn: Button
var _caption: Label
var _doc_col: VBoxContainer

const MAX_DOC := Vector2(1060, 760)


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.8))
	_stage = Kit.hbox(54)
	_stage.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(_stage)
	_stage.offset_left = 72
	_stage.offset_right = -72
	_stage.offset_top = 60
	_stage.offset_bottom = -120
	add_child(_stage)
	# --- document
	_doc_col = Kit.vbox(18)
	_doc_col.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_stage.add_child(_doc_col)
	_doc_holder = Control.new()
	_doc_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_doc_col.add_child(_doc_holder)
	_caption = Kit.wrap_label("", "ControlHintLabel")
	Kit.scalable(_caption, 23)
	_doc_col.add_child(_caption)
	_doc_shadow = ColorRect.new()
	_doc_shadow.color = Color(0, 0, 0, 0.45)
	_doc_shadow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_doc_holder.add_child(_doc_shadow)
	_doc_rect = Kit.pixel_image(null, 3)
	_doc_holder.add_child(_doc_rect)
	_placeholder = Kit.panel("PaperPanel")
	_placeholder.custom_minimum_size = Vector2(624, 450)
	_placeholder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var pv := Kit.vbox(18)
	pv.alignment = BoxContainer.ALIGNMENT_CENTER
	_placeholder.add_child(pv)
	var pic := Kit.sprite("icons/icon_evidence.png")
	pic.custom_minimum_size = Vector2(39, 39)
	pv.add_child(pic)
	var pl := Kit.label(Kit.t("ui.inspect.missing_image"), "TypeDim")
	pl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(pl)
	_doc_holder.add_child(_placeholder)
	# --- record card (paper, typewriter)
	_card = Kit.panel("PaperPanel")
	_card.custom_minimum_size = Vector2(640, 0)
	_card.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage.add_child(_card)
	var v := Kit.vbox(14)
	_card.add_child(v)
	var head := Kit.hbox(10)
	v.add_child(head)
	_kicker = Kit.label("", "PaperKicker")
	_kicker.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_kicker.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_kicker)
	_stamp = _make_stamp(Kit.t("ui.inspect.stamp").to_upper().replace("ß", "SS"))
	head.add_child(_stamp)
	_name = Kit.wrap_label("", "TypeHeading")
	Kit.scalable(_name, 36)
	v.add_child(_name)
	var sep := HSeparator.new()
	sep.theme_type_variation = "PaperSeparator"
	v.add_child(sep)
	_desc = Kit.wrap_label("", "TypeLabel")
	Kit.scalable(_desc, 29)
	v.add_child(_desc)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 12))
	_meta = Kit.wrap_label("", "TypeDim")
	Kit.scalable(_meta, 23)
	v.add_child(_meta)
	# --- footer
	var foot := Kit.hbox(18)
	foot.alignment = BoxContainer.ALIGNMENT_CENTER
	foot.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	foot.offset_left = -400
	foot.offset_right = 400
	foot.offset_top = -96
	foot.offset_bottom = -40
	add_child(foot)
	_close_btn = Kit.button(Kit.t("ui.common.close"), "", 220)
	_close_btn.pressed.connect(close)
	foot.add_child(_close_btn)


func _make_stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(252, 78)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_evidence.png")
	frame.position = Vector2.ZERO
	frame.size = Vector2(252, 78)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 27)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(252, 78)
	l.pivot_offset = Vector2(126, 39)
	l.rotation = deg_to_rad(-3.0)
	l.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	l.modulate = Color(1, 1, 1, 0.92)
	c.add_child(l)
	return c


## item_id: evidence item ("ev_damaged_seal"), objective id (uses grant_item) or a document name.
func open(id: String) -> void:
	var def := Kit.item_def(id)
	if def.is_empty():
		var od := Kit.objective_def(id)
		if od.has("grant_item"):
			id = str(od["grant_item"])
			def = Kit.item_def(id)
	item_id = id
	var doc := Kit.doc_for_item(id)
	if doc == "" and def.is_empty():
		doc = id
	var t2 := Kit.optional_tex(Kit.DOCS_DIR + doc + ".png") if doc != "" else null
	_show_document(t2)
	var alt := Kit.doc_alt_text(id, doc)
	_caption.text = alt
	_caption.visible = alt != "" and t2 != null
	_caption.custom_minimum_size.x = _doc_holder.custom_minimum_size.x - 12
	var cat := str(def.get("category", "document"))
	var kick_key := "ui.inspect.kicker." + cat
	_kicker.text = (Kit.t(kick_key) if Kit.has_key(kick_key) else Kit.t("ui.inspect.kicker.document")).to_upper().replace("ß", "SS")
	_name.text = Kit.t(str(def["name_key"])) if def.has("name_key") else Kit.t("ui.inspect.unknown")
	_desc.text = Kit.t(str(def["description_key"])) if def.has("description_key") else ""
	var sc := Kit.scene_def(str(def.get("scene", "")))
	_meta.text = Kit.t("ui.inspect.found_at", {"place": Kit.t(str(sc["title_key"]))}) if sc.has("title_key") else ""
	_meta.visible = _meta.text != ""
	open_modal()


func _show_document(t2: Texture2D) -> void:
	if t2 == null:
		_doc_rect.visible = false
		_doc_shadow.visible = false
		_placeholder.visible = true
		_placeholder.position = Vector2.ZERO
		_doc_holder.custom_minimum_size = _placeholder.custom_minimum_size
		return
	_placeholder.visible = false
	var sz := t2.get_size()
	var s := 3
	while s > 1 and (sz.x * s > MAX_DOC.x or sz.y * s > MAX_DOC.y):
		s -= 1
	var px := sz * s
	_doc_rect.texture = t2
	_doc_rect.custom_minimum_size = px
	_doc_rect.size = px
	_doc_rect.position = Vector2.ZERO
	_doc_rect.visible = true
	_doc_shadow.position = Vector2(12, 12)
	_doc_shadow.size = px
	_doc_shadow.visible = true
	_doc_holder.custom_minimum_size = px + Vector2(12, 12)


func _on_open() -> void:
	Kit.ui_sound("paper")
	if not Kit.reduced_motion():
		Kit.appear(_card, 0.24, Vector2(0, 24))
		Kit.appear(_doc_col, 0.2, Vector2(0, 12))


func focus_default() -> void:
	_close_btn.grab_focus()


func modal_input(event: InputEvent) -> bool:
	if event.is_action_pressed("interact") and not event.is_action_pressed("ui_accept"):
		close()
		return true
	return false
