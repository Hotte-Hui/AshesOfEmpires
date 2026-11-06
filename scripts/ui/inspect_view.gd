extends "res://scripts/ui/ui_modal.gd"
## InspectView: open(item_id) shows the document image from assets/ui/documents/<doc>.png at integer scale
## (x3 when it fits — pixel layers are never scaled by non-integer factors) next to a typed paper record card
## with the localized item name/description, category and place of discovery. Missing images get an
## intentional placeholder frame. Also accepts an objective id (uses its grant_item) or a document name.
## Text scale 125 / 150 %: the card widens with the text as far as the document beside it allows (_fit_layout),
## its text scrolls inside the card when it is still taller than the stage (fit_card: wheel, up / down, a "more
## below" mark, the first view ends between two lines), and a caption too long for the room under the document
## moves into the card -- nothing runs into the footer, nothing is cut off.

var suppress_toasts := true
var item_id := ""
var _stage: HBoxContainer
var _doc_holder: Control
var _doc_rect: TextureRect
var _doc_shadow: ColorRect
var _placeholder: PanelContainer
var _card: PanelContainer
var _card_scroll: ScrollContainer
var _card_body: VBoxContainer
var _more_row: HBoxContainer
var _more: TextureRect
var _card_w_max := CARD_W
var _kicker: Label
var _name: Label
var _desc: Label
var _meta: Label
var _stamp: Control
var _close_btn: Button
var _caption: Label
var _card_alt: Label
var _doc_col: VBoxContainer

const MAX_DOC := Vector2(1060, 760)
## Record card width at 100 % text; at 125 / 150 % it grows by the same factor (same characters per line).
const CARD_W := 640.0
## Widest record card (only when the text would otherwise scroll and the document leaves the room).
const CARD_W_MAX := 1100.0
## Stage margins (the footer with „Schließen“ starts 96 px above the bottom edge, below the stage).
const PAD_X := 72.0
const PAD_TOP := 60.0
const PAD_BOTTOM := 120.0


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.8))
	_stage = Kit.hbox(54)
	_stage.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(_stage)
	_stage.offset_left = PAD_X
	_stage.offset_right = -PAD_X
	_stage.offset_top = PAD_TOP
	_stage.offset_bottom = -PAD_BOTTOM
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
	_card.custom_minimum_size = Vector2(CARD_W, 0)
	_card.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage.add_child(_card)
	var cbox := Kit.vbox(4)
	_card.add_child(cbox)
	_card_scroll = ScrollContainer.new()
	_card_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_card_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER   # the "more below" mark instead
	_card_scroll.follow_focus = false
	_card_scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	cbox.add_child(_card_scroll)
	var v := Kit.vbox(14)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_card_scroll.add_child(v)
	_card_body = v
	_more_row = Kit.hbox(0)
	_more_row.alignment = BoxContainer.ALIGNMENT_END
	_more_row.visible = false
	_more = Kit.ex_sprite("icons/more_down.png")
	_more.custom_minimum_size = Vector2(21, 12)
	_more_row.add_child(_more)
	cbox.add_child(_more_row)
	v.minimum_size_changed.connect(_fit_card_deferred)
	_card_scroll.get_v_scroll_bar().value_changed.connect(func(_v): _update_more())
	_card_scroll.get_v_scroll_bar().changed.connect(_update_more)
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
	# the document's caption, when it is too long for the room under the document (125 / 150 %)
	_card_alt = Kit.wrap_label("", "TypeDim")
	Kit.scalable(_card_alt, 23)
	_card_alt.visible = false
	v.add_child(_card_alt)
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
	if t2 == null and not def.is_empty():
		# a clue without a document (cut hose, seal ...): the evidence board's own picture of it, not the placeholder
		t2 = Kit.optional_tex("res://assets/ui/board/thumbs/%s.png" % id)
	_show_document(t2)
	var alt := Kit.doc_alt_text(id, doc) if t2 != null else ""
	# the caption stays under the document while it fits there; else (long captions at 125 / 150 %) it moves
	# into the record card, which scrolls when it has to -- every word stays readable
	var under := alt != "" and _wrapped_height(_caption, alt, _doc_holder.custom_minimum_size.x, 1) <= _caption_room()
	_caption.text = alt if under else ""
	_caption.visible = under
	_caption.custom_minimum_size.x = _doc_holder.custom_minimum_size.x - 12
	_card_alt.text = alt if not under else ""
	_card_alt.visible = alt != "" and not under
	var cat := str(def.get("category", "document"))
	var kick_key := "ui.inspect.kicker." + cat
	_kicker.text = (Kit.t(kick_key) if Kit.has_key(kick_key) else Kit.t("ui.inspect.kicker.document")).to_upper().replace("ß", "SS")
	_name.text = Kit.t(str(def["name_key"])) if def.has("name_key") else Kit.t("ui.inspect.unknown")
	_desc.text = Kit.t(str(def["description_key"])) if def.has("description_key") else ""
	var sc := Kit.scene_def(str(def.get("scene", "")))
	_meta.text = Kit.t("ui.inspect.found_at", {"place": Kit.t(str(sc["title_key"]))}) if sc.has("title_key") else ""
	_meta.visible = _meta.text != ""
	_fit_layout()
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


## The stage rect (full screen minus the margins set in _ready); 1920x1080 before the first layout.
func _stage_size() -> Vector2:
	var full := size if size.x > 100.0 and size.y > 100.0 else Vector2(1920, 1080)
	return full - Vector2(PAD_X * 2.0, PAD_TOP + PAD_BOTTOM)


## Heights of the lines of `text` in the wrapping label `l` at the width `width`, broken and shaped the way the Label
## does it (same font chain, size, break and trim flags): a line that needs a fallback glyph („⇄“ comes from another
## font) is taller than the font height, so lines are never assumed to be uniform.
static func _line_heights(l: Label, text: String, width: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	var f := l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	if text == "":
		out.append(f.get_height(fs))
		return out
	var sb := l.get_theme_stylebox("normal")
	var p := TextParagraph.new()
	p.width = maxf(1.0, width - (sb.get_minimum_size().x if sb != null else 0.0))
	p.break_flags = TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE | l.autowrap_trim_flags
	p.add_string(text, f, fs)
	for i in p.get_line_count():
		out.append(p.get_line_size(i).y)
	return out


## Height of `text` in the wrapping label `l` at the width `width` (+ `slack` spare lines of the font height) --
## the sum of its real line heights and line spacing, independent of the current layout.
static func _wrapped_height(l: Label, text: String, width: float, slack := 0) -> float:
	var hs := _line_heights(l, text, width)
	var ls := float(l.get_theme_constant("line_spacing"))
	var sb := l.get_theme_stylebox("normal")
	var h := (sb.get_minimum_size().y if sb != null else 0.0) + maxf(0.0, hs.size() - 1.0) * ls
	for v in hs:
		h += v
	if slack > 0:
		h += slack * (l.get_theme_font("font").get_height(l.get_theme_font_size("font_size")) + ls)
	return h


## Room for the caption under the document (stage height minus image, shadow and the column's gap).
func _caption_room() -> float:
	return _stage_size().y - _doc_holder.custom_minimum_size.y - float(_doc_col.get_theme_constant("separation"))


## Height the card's text would need at the card width `card_w` (the scroll area adds nothing at full height).
func _body_height(card_w: float) -> float:
	var sb := _card.get_theme_stylebox("panel")
	var w := card_w - (sb.get_minimum_size().x if sb != null else 0.0)
	var h := 0.0
	var n := 0
	for c in _card_body.get_children():
		var ctl := c as Control
		if ctl == null or not ctl.visible:
			continue
		n += 1
		if ctl is Label and (ctl as Label).autowrap_mode != TextServer.AUTOWRAP_OFF:
			h += _wrapped_height(ctl as Label, (ctl as Label).text, w)
		else:
			h += ctl.get_combined_minimum_size().y
	return h + float(_card_body.get_theme_constant("separation")) * maxf(0.0, n - 1.0)


## Card width: grows with the text scale (same characters per line as at 100 %) and further, in steps, while the
## text would still be taller than the stage -- up to what the document beside it leaves (CARD_W_MAX at most);
## only then does it scroll (fit_card). Plus a hard line budget for the caption under the document.
func _fit_layout() -> void:
	var stage := _stage_size()
	var free_w := stage.x - _doc_holder.custom_minimum_size.x - float(_stage.get_theme_constant("separation"))
	_card_w_max = clampf(free_w, CARD_W, CARD_W_MAX)
	var sb := _card.get_theme_stylebox("panel")
	var cap := stage.y - (sb.get_minimum_size().y if sb != null else 0.0)
	var w := clampf(roundf(CARD_W * Kit.text_scale()), CARD_W, _card_w_max)
	while w < _card_w_max and _body_height(w) > cap:
		w = minf(_card_w_max, w + 40.0)
	_card.custom_minimum_size.x = w
	var ls := float(_caption.get_theme_constant("line_spacing"))
	var pitch := _caption.get_theme_font("font").get_height(_caption.get_theme_font_size("font_size")) + ls
	_caption.max_lines_visible = maxi(1, int(floorf((_caption_room() + ls) / pitch))) if pitch > 1.0 else -1
	_card_scroll.scroll_vertical = 0
	fit_card()


func _fit_card_deferred() -> void:
	fit_card.call_deferred()


## Gives the card's scroll area the height of its text, capped so the card always fits the stage: a long item
## text at 125 / 150 % scrolls inside the card instead of running under the footer.
func fit_card() -> void:
	if _card_scroll == null or not is_instance_valid(_card_scroll):
		return
	var want := _card_body.get_combined_minimum_size().y
	var sb := _card.get_theme_stylebox("panel")
	var cap := _stage_size().y - (sb.get_minimum_size().y if sb != null else 0.0)
	var over := want > cap + 0.5
	if _more_row.visible != over:
		_more_row.visible = over
	var h := ceilf(want)
	if over:
		cap -= _more_row.get_combined_minimum_size().y + float((_more_row.get_parent() as Control).get_theme_constant("separation"))
		h = floorf(_snap_cut(cap, _card.custom_minimum_size.x - (sb.get_minimum_size().x if sb != null else 0.0)))
	if absf(_card_scroll.custom_minimum_size.y - h) > 0.5:
		_card_scroll.custom_minimum_size.y = h
	_update_more.call_deferred()


## A scrolling card's first view ends in the gap between two lines, never through one: halfway between the bottom of
## the last whole line and the top of the next, so descenders above and accents below the cut stay whole. Every line
## is measured as the Label lays it out (_line_heights at the text width `text_w`, a taller fallback-glyph line
## included), so this does not wait for the layout.
func _snap_cut(h: float, text_w: float) -> float:
	var y := 0.0
	var last := 0.0          # bottom of the last whole line (or control) above the cut
	var sep := float(_card_body.get_theme_constant("separation"))
	for c in _card_body.get_children():
		var ctl := c as Control
		if ctl == null or not ctl.visible:
			continue
		var l := ctl as Label
		if l == null or l.autowrap_mode == TextServer.AUTOWRAP_OFF:
			var ch := ctl.get_combined_minimum_size().y
			last = minf(y + ch, h)
			y += ch + sep
			continue
		var lsb := l.get_theme_stylebox("normal")
		var ly := y + (lsb.get_margin(SIDE_TOP) if lsb != null else 0.0)
		var ls := float(l.get_theme_constant("line_spacing"))
		var clear := minf(2.0, ls * 0.5)      # a line counts as whole with this much paper below it (ink overhang)
		for lh in _line_heights(l, l.text, text_w):
			if ly + lh + clear > h:
				return floorf(minf(h, (last + ly) * 0.5))
			last = ly + lh
			ly = last + ls
		y += _wrapped_height(l, l.text, text_w) + sep
	return h


## Line pitch of a label (font height + line spacing at its current, scaled size).
static func _pitch(l: Label) -> float:
	return l.get_theme_font("font").get_height(l.get_theme_font_size("font_size")) + float(l.get_theme_constant("line_spacing"))


## true when the card text is taller than its scroll area (wheel / up / down scroll it).
func card_scrolls() -> bool:
	return _more_row != null and _more_row.visible


func _update_more() -> void:
	if _more == null or not is_instance_valid(_more):
		return
	var bar := _card_scroll.get_v_scroll_bar()
	_more.modulate.a = 1.0 if bar.max_value - bar.page - float(_card_scroll.scroll_vertical) > 2.0 else 0.0


func _nudge(dy: float) -> void:
	var bar := _card_scroll.get_v_scroll_bar()
	_card_scroll.scroll_vertical = int(clampf(_card_scroll.scroll_vertical + dy, 0.0, maxf(0.0, bar.max_value - bar.page)))


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
	if card_scrolls():
		var mb := event as InputEventMouseButton
		if mb != null and mb.pressed and (mb.button_index == MOUSE_BUTTON_WHEEL_DOWN or mb.button_index == MOUSE_BUTTON_WHEEL_UP):
			_nudge(_pitch(_desc) * (1.0 if mb.button_index == MOUSE_BUTTON_WHEEL_DOWN else -1.0))   # a line per notch
			return true
		if event.is_action_pressed("ui_down", true) or event.is_action_pressed("move_down", true):
			_nudge(2.0 * _pitch(_desc))
			return true
		if event.is_action_pressed("ui_up", true) or event.is_action_pressed("move_up", true):
			_nudge(-2.0 * _pitch(_desc))
			return true
	return false
