extends "res://scripts/ui/ui_modal.gd"
## DiscoveryView (scenes/ui/DiscoveryView.tscn; UIRoot property `discovery`) — presents an exploration find
## (TECHNICAL_ARCHITECTURE §12):
##   page 1   the in-world find, in the protagonist's notebook: kind + place, title, the optional close-up
##            (x3, a deckle-edged print taped in), the note on squared paper (Alexei, Karsk) or ruled paper
##            (Konrad, Berlin). Ordinary finds get a soft chime.
##   page 2+  only when the entry links real-history cards: a clearly separated "REALE GESCHICHTE" card in a
##            neutral archive style (cool paper, slate band, no regime symbols): year, title, text, sources
##            (labels, URLs as plain text) and a one-line note that this is real history outside the game's
##            fiction. Never celebrated: neutral paper sound, no flourish, darker neutral backdrop.
## API: open(explore_id, cards_new := []), open_cards(card_ids, mark_new := false), close(), next(), prev();
##      signals closed (from the modal base, once per open) and page_changed(index).
## Input: E / Enter / Space / A = next (long pages scroll first; closes on the last page), Esc / B = close,
##        Left / Q / LB = previous page, Right / RB = next page, Up / Down = scroll; mouse on the buttons
##        and the wheel. Respects text scale (Kit.scalable), high contrast and reduced motion.

signal page_changed(index: int)

## The key press that opened the view (or a mashed one) must not skip the first page unread.
const OPEN_GUARD_MS := 300
const IMG_MAX := Vector2(960, 600)
## Notebook width next to a photo: whatever the row leaves free, kept between these (line length ~45-65 chars).
const NOTE_W_MIN := 600.0
const NOTE_W_MAX := 860.0
const ROW_W := 1760.0
const NOTE_W_ALONE := 980.0
const CARD_W := 1240.0
const FOOTER_H := 196.0
const STAGE_H := 1080.0 - FOOTER_H
const DIM_FIND := Color(0.016, 0.035, 0.05, 0.82)
const DIM_CARD := Color(0.02, 0.024, 0.028, 0.92)
const DIM_HC := Color(0.0, 0.0, 0.0, 0.94)
## Archive card colours (karsk snow / wall ramps): neutral, no accent hue.
const C_ARCH_INK := Color("1a1c2a")
const C_ARCH_DIM := Color("4a5a5b")
const C_ARCH_RULE := Color("a3b1ad")
const C_ARCH_RULE_L := Color("c4cfc8")
const C_ARCH_BAND := Color("dee5dc")
const C_ARCH_BAND_DIM := Color("a3b1ad")
const C_ARCH_URL := Color("3e546b")
## Notebook inks: Alexei writes with blue-black ink, Konrad with black drawing ink.
const C_INK_ALEXEI := Color("2b3c50")
const C_INK_KONRAD := Color("1a1c2a")

var suppress_toasts := true
var explore_id := ""
## [{type: "find" | "card" | "missing", id: String, new: bool}]
var pages: Array = []
var page := -1
var cards_new: Array = []

var _opened_ms := 0
var _dim: ColorRect
var _stage: Control
var _page_root: Control = null
var _page_panel: Control = null
var _scroll: ScrollContainer = null
var _more: TextureRect = null
## Line pitch of the page's main text (scroll viewport and steps snap to whole lines).
var _line_h := 0.0
var _footer: VBoxContainer
var _row: HBoxContainer
var _prev_btn: Button
var _next_btn: Button
var _dots: HBoxContainer
var _filed: Label
var _hints: Control = null
var _dim_tween: Tween
var _scroll_tween: Tween


# ================================================================ ruled / squared notebook paper
## Container for the one wrapping body Label of a notebook page: lays it out with side paddings and reports
## the line pitch. The page panel draws the ruling behind it (_draw_ruling), aligned to the label's real
## baselines, so handwriting sits on the lines at every text scale and while scrolling.
class RuledBox extends Container:
	var pad_left := 36.0
	var pad_right := 30.0
	var extra_lines := 1

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _label() -> Label:
		for c in get_children():
			if c is Label:
				return c
		return null

	func label_node() -> Label:
		return _label()

	func pitch() -> float:
		var l := _label()
		if l == null:
			return 48.0
		var f := l.get_theme_font("font")
		var fs := l.get_theme_font_size("font_size")
		return f.get_height(fs) + l.get_theme_constant("line_spacing")

	func _get_minimum_size() -> Vector2:
		var l := _label()
		if l == null:
			return Vector2.ZERO
		var m := l.get_combined_minimum_size()
		return Vector2(m.x + pad_left + pad_right, m.y + pitch() * extra_lines)

	func _notification(what: int) -> void:
		if what == NOTIFICATION_SORT_CHILDREN:
			var l := _label()
			if l != null:
				var w := maxf(10.0, size.x - pad_left - pad_right)
				fit_child_in_rect(l, Rect2(pad_left, 0, w, l.get_combined_minimum_size().y))


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	_dim = Kit.dimmer(DIM_FIND.a)
	_dim.color = DIM_FIND
	add_child(_dim)
	_stage = Control.new()
	_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(_stage)
	_stage.offset_bottom = -FOOTER_H
	add_child(_stage)
	_footer = Kit.vbox(12)
	_footer.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_footer.offset_left = -640
	_footer.offset_right = 640
	_footer.offset_top = -FOOTER_H
	_footer.offset_bottom = -22
	_footer.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_footer.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_footer.alignment = BoxContainer.ALIGNMENT_END
	add_child(_footer)
	_filed = Kit.label("", "DimLabel", 0)
	_filed.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(_filed, 23)
	_footer.add_child(_filed)
	_row = Kit.hbox(34)
	_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_footer.add_child(_row)
	_prev_btn = Kit.button(Kit.t("ui.discovery.back"), "", 210)
	_prev_btn.pressed.connect(prev)
	_row.add_child(_prev_btn)
	_dots = Kit.hbox(12)
	_dots.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_row.add_child(_dots)
	_next_btn = Kit.button("", "", 260)
	_next_btn.pressed.connect(next)
	_row.add_child(_next_btn)


## Shows a find (explore entry id). cards_new = history card ids unlocked by this find right now (marked as
## newly filed; all cards the entry links are shown as following pages).
func open(id: String, new_cards: Array = []) -> void:
	explore_id = id
	cards_new = []
	for c in new_cards:
		cards_new.append(str(c))
	pages.clear()
	var e := _entry(id)
	if e.is_empty():
		if cards_new.is_empty():
			pages.append({"type": "missing", "id": id, "new": false})
		push_warning("DiscoveryView: unknown explore id '%s'" % id)
	else:
		pages.append({"type": "find", "id": id, "new": false})
	var linked: Array = _call("cards_of", [id], [])
	for c in cards_new:
		if not (c in linked):
			linked.append(c)
	for c in linked:
		var cid := str(c)
		if _card(cid).is_empty():
			continue
		if bool(_call("is_card_found", [cid], false)) or cid in cards_new:
			pages.append({"type": "card", "id": cid, "new": cid in cards_new})
	_open_pages()


## Shows real-history cards only (journal "Geschichte" tab, cards unlocked by a chat).
func open_cards(ids: Array, mark_new := false) -> void:
	explore_id = ""
	cards_new = []
	pages.clear()
	for c in ids:
		var cid := str(c)
		if not _card(cid).is_empty():
			pages.append({"type": "card", "id": cid, "new": mark_new})
			if mark_new:
				cards_new.append(cid)
	if pages.is_empty():
		pages.append({"type": "missing", "id": ", ".join(PackedStringArray(ids.map(func(x): return str(x)))), "new": false})
	_open_pages()


func open_card(card_id: String) -> void:
	open_cards([card_id])


func page_count() -> int:
	return pages.size()


func is_last_page() -> bool:
	return page >= pages.size() - 1


func current_type() -> String:
	return str(pages[page]["type"]) if page >= 0 and page < pages.size() else ""


func _open_pages() -> void:
	page = -1
	_opened_ms = Time.get_ticks_msec()
	open_modal()
	_show_page(0, 0)
	match current_type():
		"find":
			Kit.ui_sound("discovery")
		"card":
			Kit.ui_sound("history")
		_:
			Kit.ui_sound("page")


# ================================================================ navigation
func next() -> void:
	if not is_open:
		return
	if _scroll_by_page(1):
		return
	if page < pages.size() - 1:
		Kit.ui_sound("history" if str(pages[page + 1]["type"]) == "card" else "page")
		_show_page(page + 1, 1)
	else:
		Kit.ui_sound("history" if current_type() == "card" else "page")
		close()


func prev() -> void:
	if not is_open or page <= 0:
		return
	Kit.ui_sound("page")
	_show_page(page - 1, -1)


## Scrolls a long page by ~80 % of its height. Returns true when it scrolled.
func _scroll_by_page(dir: int) -> bool:
	if _scroll == null or not is_instance_valid(_scroll):
		return false
	var bar := _scroll.get_v_scroll_bar()
	var max_v := maxf(0.0, bar.max_value - bar.page)
	var cur := float(_scroll.scroll_vertical)
	var step := _scroll.size.y * 0.8
	var lh := _pitch_now(_scroll.get_child(0) as Control) if _scroll.get_child_count() > 0 else 0.0
	if lh > 8.0:
		step = maxf(lh, floorf(_scroll.size.y * 0.8 / lh) * lh)   # whole lines; one line of overlap
	if dir > 0 and cur < max_v - 2.0:
		_scroll_to(minf(max_v, cur + step))
		return true
	if dir < 0 and cur > 2.0:
		_scroll_to(maxf(0.0, cur - step))
		return true
	return false


func _scroll_to(v: float) -> void:
	if _scroll_tween != null and _scroll_tween.is_valid():
		_scroll_tween.kill()
	if Kit.reduced_motion():
		_scroll.scroll_vertical = int(v)
		return
	_scroll_tween = create_tween()
	_scroll_tween.tween_property(_scroll, "scroll_vertical", int(v), 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


func _show_page(i: int, dir: int) -> void:
	if pages.is_empty():
		return
	i = clampi(i, 0, pages.size() - 1)
	var old := _page_root
	page = i
	_scroll = null
	_more = null
	_line_h = 0.0
	var p: Dictionary = pages[i]
	match str(p["type"]):
		"find":
			_page_root = _build_find(str(p["id"]))
		"card":
			_page_root = _build_card(str(p["id"]))
		_:
			_page_root = _build_missing(str(p["id"]))
	_stage.add_child(_page_root)
	_update_footer()
	_animate(old, _page_root, dir)
	_fit_scroll.call_deferred()
	page_changed.emit(page)


func _animate(old: Control, nw: Control, dir: int) -> void:
	var rm := Kit.reduced_motion()
	var card := current_type() == "card"
	if _dim_tween != null and _dim_tween.is_valid():
		_dim_tween.kill()
	_dim_tween = create_tween()
	_dim_tween.tween_property(_dim, "color", DIM_HC if Kit.high_contrast() else (DIM_CARD if card else DIM_FIND), 0.3)
	if old != null and is_instance_valid(old):
		old.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var tw := old.create_tween().set_parallel(true)
		tw.tween_property(old, "modulate:a", 0.0, 0.12 if rm else 0.16)
		if not rm and dir != 0:
			tw.tween_method(_slide.bind(old), Vector2.ZERO, Vector2(-40.0 * dir, 0.0), 0.16) 				.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
		tw.chain().tween_callback(old.queue_free)
	nw.modulate.a = 0.0
	var t2 := nw.create_tween().set_parallel(true)
	var delay := 0.08 if old != null else 0.0
	t2.tween_property(nw, "modulate:a", 1.0, 0.16 if rm else 0.24).set_delay(delay)
	if not rm:
		var from := Vector2(48.0 * dir, 0.0) if dir != 0 else Vector2(0, 18)
		_slide(from, nw)
		t2.tween_method(_slide.bind(nw), from, Vector2.ZERO, 0.28).set_delay(delay) 			.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


## Moves a full-rect page by shifting all four offsets (never `position`: on an anchored control that would
## bake a transient minimum size into the offsets).
func _slide(v: Vector2, c: Control) -> void:
	if c == null or not is_instance_valid(c):
		return
	c.offset_left = roundf(v.x)
	c.offset_right = roundf(v.x)
	c.offset_top = roundf(v.y)
	c.offset_bottom = roundf(v.y)


func _update_footer() -> void:
	var n := pages.size()
	var multi := n > 1
	_prev_btn.visible = multi
	_prev_btn.disabled = page <= 0
	_dots.visible = multi
	for c in _dots.get_children():
		_dots.remove_child(c)
		c.queue_free()
	if multi:
		for k in n:
			var is_card := str(pages[k]["type"]) == "card"
			var on := k == page
			var name := ("icons/page_on_neutral.png" if is_card else "icons/page_on.png") if on else "icons/page_off.png"
			_dots.add_child(Kit.ex_sprite(name))
	if page >= n - 1:
		_next_btn.text = Kit.t("ui.discovery.close")
	elif str(pages[page]["type"]) != "card" and str(pages[page + 1]["type"]) == "card":
		_next_btn.text = Kit.t("ui.discovery.next_history")
	else:
		_next_btn.text = Kit.t("ui.discovery.next")
	var p: Dictionary = pages[page] if page >= 0 and page < n else {}
	_filed.text = Kit.t("ui.history.filed") if str(p.get("type", "")) == "card" and bool(p.get("new", false)) else ""
	_filed.modulate.a = 1.0 if _filed.text != "" else 0.0
	if _hints != null and is_instance_valid(_hints):
		_footer.remove_child(_hints)
		_hints.queue_free()
	var k_next := Kit.action_key_text("interact")
	var pairs: Array = []
	if page < n - 1:
		pairs.append([k_next, Kit.t("ui.explore.hint.next")])
		pairs.append([Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")])
	else:
		pairs.append([k_next + "|" + Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")])
	if multi:
		pairs.insert(0, [Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("ui.explore.hint.pages")])
	_hints = Kit.controls_row(pairs)
	_footer.add_child(_hints)


# ================================================================ page: find (notebook)
func _build_find(id: String) -> Control:
	var e := _entry(id)
	var center := _center()
	var row := Kit.hbox(66)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_child(row)
	var img_path := str(_call("entry_image", [id], ""))
	if img_path == "" and str(e.get("image", "")) != "":
		img_path = Symbols.pick(str(e["image"]))
	var tex := Kit.optional_tex(img_path) if img_path != "" else null
	var photo_h := 0.0
	var note_w := NOTE_W_ALONE
	if tex != null:
		var holder := _photo(tex)
		row.add_child(holder)
		photo_h = holder.custom_minimum_size.y - 18.0
		note_w = clampf(ROW_W - holder.custom_minimum_size.x - 66.0, NOTE_W_MIN, NOTE_W_MAX)
	var note := _notebook(e, note_w, photo_h)
	row.add_child(note)
	_page_panel = note
	return center


func _photo(tex: Texture2D) -> Control:
	var sz := tex.get_size()
	var s := 3
	while s > 1 and (sz.x * s > IMG_MAX.x or sz.y * s > IMG_MAX.y):
		s -= 1
	var px := sz * s
	if px.x > IMG_MAX.x or px.y > IMG_MAX.y:   # oversized source: keep proportions, never upscale blurry
		var k := minf(IMG_MAX.x / sz.x, IMG_MAX.y / sz.y)
		px = (sz * k).floor()
	var mount_sz := px + Vector2(42, 45)
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.custom_minimum_size = mount_sz + Vector2(0, 18)
	holder.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var mount := PanelContainer.new()
	mount.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mount.add_theme_stylebox_override("panel", Kit.ex_style("frames/photo_mount.png", [21, 21, 21, 24], [21, 21, 21, 24], true, true))
	mount.position = Vector2(0, 18)
	mount.size = mount_sz
	holder.add_child(mount)
	var img := Kit.pixel_image(tex, s)
	img.custom_minimum_size = px
	mount.add_child(img)
	var tl := Kit.ex_sprite("icons/tape_l.png")
	tl.position = Vector2(-27, 0)
	tl.size = Vector2(66, 36)
	holder.add_child(tl)
	var tr := Kit.ex_sprite("icons/tape_r.png")
	tr.position = Vector2(mount_sz.x - 39, 0)
	tr.size = Vector2(66, 36)
	holder.add_child(tr)
	return holder


func _notebook(e: Dictionary, width: float, min_h: float) -> PanelContainer:
	var hc := Kit.high_contrast()
	var grid := str(e.get("area", "")) == "karsk"
	var ink := Kit.C_INK if hc else (C_INK_ALEXEI if grid else C_INK_KONRAD)
	var panel := PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel", Kit.ex_style("frames/notebook.png", [30, 18, 21, 24], [30, 42, 21, 45], false, true))
	panel.custom_minimum_size = Vector2(width, min_h)
	panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var v := Kit.vbox(8)
	panel.add_child(v)
	var kind := str(e.get("kind", "detail"))
	var head := Kit.margin(36, 0, 30, 0)
	var hrow := Kit.hbox(14)
	head.add_child(hrow)
	var ic := Kit.ex_sprite(Kit.explore_kind_icon(kind))
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hrow.add_child(ic)
	var kick := Kit.label(Kit.explore_kind_label(kind).to_upper(), "PaperKicker")
	kick.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hrow.add_child(kick)
	# the place reads like the dateline of a notebook entry (top right, in the writer's ink)
	var place := Kit.wrap_label(Kit.explore_place(e), "", 0, Color(ink, 0.78))
	place.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	place.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	place.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	place.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	Kit.scalable(place, 23)
	hrow.add_child(place)
	v.add_child(head)
	var tm := Kit.margin(36, 4, 30, 10)
	var title := Kit.wrap_label(Kit.explore_title(e), "", 0, ink)
	title.add_theme_font_override("font", Kit.font("fv_serif_bold_italic"))
	Kit.scalable(title, 40)
	tm.add_child(title)
	v.add_child(tm)
	var ruled := RuledBox.new()
	ruled.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ruled.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var body := Kit.wrap_label(_find_text(e), "", 0, ink)
	body.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	body.add_theme_constant_override("line_spacing", 10)
	Kit.scalable(body, 31)
	ruled.add_child(body)
	v.add_child(_scroll_for(ruled))
	_line_h = ruled.pitch()
	panel.draw.connect(_draw_ruling.bind(panel, ruled, grid, hc))
	ruled.sort_children.connect(panel.queue_redraw)
	_scroll.get_v_scroll_bar().value_changed.connect(func(_v): panel.queue_redraw())
	return panel


## Notebook ruling drawn on the page panel (behind its children): squared paper for Alexei (Karsk), ruled
## lines for Konrad (Berlin), from the body to the bottom of the sheet, aligned to the body label's
## baselines (they move with the scroll); the red margin line runs the full height of the page.
## Geometry follows frames/notebook.png at x3: gutter shading ends at x 18, paper edge at w-6,
## the dog-ear starts 24 px above the bottom.
func _draw_ruling(panel: PanelContainer, ruled: RuledBox, grid: bool, hc: bool) -> void:
	if not is_instance_valid(panel) or not is_instance_valid(ruled):
		return
	var l := ruled.label_node()
	var sc := ruled.get_parent() as Control
	if l == null or sc == null or not l.is_inside_tree():
		return
	var f := l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	var pitch := ruled.pitch()
	var inv := panel.get_global_transform().affine_inverse()
	var lpos: Vector2 = inv * l.global_position
	var base0 := lpos.y + f.get_ascent(fs)
	var top := (inv * sc.global_position).y - 6.0
	var bottom := panel.size.y - 30.0
	var x0 := 18.0
	var x1 := panel.size.x - 6.0
	var line := Color(0.655, 0.737, 0.796, 0.42 if hc else (0.55 if grid else 0.8))
	var margin := Color(0.659, 0.22, 0.18, 0.32 if hc else 0.55)
	var mx := roundf(lpos.x - 18.0)
	var step := pitch * 0.5 if grid else pitch
	var y := base0
	while y - step >= top:
		y -= step
	while y < top:
		y += step
	while y <= bottom:
		panel.draw_rect(Rect2(x0, roundf(y), x1 - x0, 3), line)
		y += step
	if grid:
		var x := mx
		while x - step >= x0:
			x -= step
		while x <= x1 - 3.0:
			if absf(x - mx) > 1.0:
				panel.draw_rect(Rect2(roundf(x), roundf(top), 3, bottom - top + 3.0), line)
			x += step
	panel.draw_rect(Rect2(mx, 9, 3, bottom - 6.0), margin)


## Body text of a find; chats (no text_key) are re-read as a short transcript.
func _find_text(e: Dictionary) -> String:
	if e.has("text"):
		return str(e["text"])
	var k := str(e.get("text_key", ""))
	if k != "":
		return Kit.t(k)
	var out: PackedStringArray = []
	var lines = e.get("lines", [])
	if lines is Array:
		for l in lines:
			if l is Dictionary:
				out.append("%s: %s" % [Kit.char_name(str(l.get("speaker", ""))), Kit.t(str(l.get("key", "")))])
	return "\n".join(out)


func _build_missing(id: String) -> Control:
	var center := _center()
	var e := {"kind": "detail", "area": "", "title_key": "ui.discovery.missing", "id": id,
		"text": Kit.t("ui.discovery.missing_text", {"id": id})}
	var note := _notebook(e, 760.0, 0.0)
	center.add_child(note)
	_page_panel = note
	return center


# ================================================================ page: real-history card (archive)
func _build_card(cid: String) -> Control:
	var c := _card(cid)
	var hc := Kit.high_contrast()
	var ink := Color.BLACK if hc else C_ARCH_INK
	var dim := Color("24373a") if hc else C_ARCH_DIM
	var center := _center()
	var panel := PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel", Kit.ex_style("frames/archive_card_hc.png" if hc else "frames/archive_card.png",
		[24, 48, 24, 24], [57, 3, 57, 36]))
	panel.custom_minimum_size.x = CARD_W
	center.add_child(panel)
	_page_panel = panel
	var v := Kit.vbox(0)
	panel.add_child(v)
	# slate band: REALE GESCHICHTE · side
	var band := Kit.hbox(18)
	band.custom_minimum_size.y = 36
	v.add_child(band)
	var bl := Kit.label(Kit.t("ui.history.kicker").to_upper(), "KickerLabel", 22, C_ARCH_BAND)
	bl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	band.add_child(bl)
	var gap := Control.new()
	gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	band.add_child(gap)
	var side := Kit.label(Kit.history_side_label(str(c.get("side", ""))).to_upper(), "HintLabel", 20, C_ARCH_BAND_DIM)
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	band.add_child(side)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 34))
	# year + title
	var hrow := Kit.hbox(32)
	v.add_child(hrow)
	var year := Kit.label(str(c.get("year", "")), "", 0, dim)
	year.add_theme_font_override("font", Kit.font("fv_heading"))
	Kit.scalable(year, 46)
	year.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hrow.add_child(year)
	var title := Kit.wrap_label(Kit.t(str(c.get("title_key", ""))), "", 0, ink)
	title.add_theme_font_override("font", Kit.font("fv_serif_bold"))
	Kit.scalable(title, 38)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hrow.add_child(title)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 16))
	v.add_child(Kit.rule(C_ARCH_RULE if not hc else Color.BLACK, 3))
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 20))
	# text + sources (scrolls when long / at 150 % text)
	var body := Kit.vbox(10)
	var text := Kit.wrap_label(Kit.t(str(c.get("text_key", ""))), "", 0, ink)
	text.add_theme_font_override("font", Kit.font("fv_serif"))
	text.add_theme_constant_override("line_spacing", 8)
	Kit.scalable(text, 29)
	body.add_child(text)
	text.set_meta("pitch_label", true)
	var srcs = c.get("sources", [])
	if srcs is Array and not srcs.is_empty():
		body.add_child(Kit.rule(Color(0, 0, 0, 0), 14))
		var sk := Kit.label(Kit.t("ui.history.sources").to_upper(), "HintLabel", 0, dim)
		Kit.scalable(sk, 20)
		body.add_child(sk)
		for s in srcs:
			if not (s is Dictionary):
				continue
			var sv := Kit.vbox(0)
			var sl := Kit.wrap_label(str(s.get("label", "")), "", 0, ink)
			sl.add_theme_font_override("font", Kit.font("fv_serif_italic"))
			Kit.scalable(sl, 24)
			sv.add_child(sl)
			var url := str(s.get("url", ""))
			if url != "":
				var ul := Kit.wrap_label(url, "", 0, C_ARCH_URL if not hc else ink)
				ul.autowrap_mode = TextServer.AUTOWRAP_ARBITRARY
				ul.add_theme_font_override("font", Kit.font("fv_mono"))
				Kit.scalable(ul, 20)
				sv.add_child(ul)
			body.add_child(sv)
	v.add_child(_scroll_for(body))
	# the one-line separation note (always visible, outside the scroll area)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 14))
	v.add_child(Kit.rule(C_ARCH_RULE_L if not hc else Color.BLACK, 3))
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 12))
	var note := Kit.wrap_label(Kit.t("ui.history.note"), "", 0, dim)
	note.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	Kit.scalable(note, 23)
	v.add_child(note)
	return center


# ================================================================ helpers
func _center() -> CenterContainer:
	var center := CenterContainer.new()
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(center)
	return center


## Wraps page content in a vertical ScrollContainer plus a "more below" marker. Sized by _fit_scroll().
func _scroll_for(content: Control) -> Control:
	var box := Kit.vbox(4)
	box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.follow_focus = false
	sc.mouse_filter = Control.MOUSE_FILTER_PASS
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if content is RuledBox:
		content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.add_child(content)
	box.add_child(sc)
	var mr := Kit.hbox(0)
	mr.alignment = BoxContainer.ALIGNMENT_END
	var more := Kit.ex_sprite("icons/more_down.png")
	more.custom_minimum_size = Vector2(21, 12)
	more.modulate.a = 0.0
	mr.add_child(more)
	box.add_child(mr)
	_scroll = sc
	_more = more
	content.minimum_size_changed.connect(_fit_scroll_deferred)
	sc.get_v_scroll_bar().value_changed.connect(func(_v): _update_more())
	sc.get_v_scroll_bar().changed.connect(_update_more)
	return box


func _fit_scroll_deferred() -> void:
	_fit_scroll.call_deferred()


## Gives the scroll area its content height, capped so the page always fits above the footer.
func _fit_scroll() -> void:
	if _scroll == null or not is_instance_valid(_scroll) or _scroll.get_child_count() == 0:
		return
	var content := _scroll.get_child(0) as Control
	var want := content.get_combined_minimum_size().y
	var other := 0.0
	if _page_panel != null and is_instance_valid(_page_panel) and _page_panel.get_child_count() > 0:
		# height of everything on the page except the scroll area (ignores the photo-height minimum)
		var sb := _page_panel.get_theme_stylebox("panel")
		var inner := (_page_panel.get_child(0) as Control).get_combined_minimum_size().y
		other = inner - _scroll.custom_minimum_size.y + (sb.get_minimum_size().y if sb != null else 0.0)
	var max_h := maxf(120.0, STAGE_H - 72.0 - other)
	var h := clampf(want, 40.0, max_h)
	var lh := _pitch_now(content)
	if want > max_h and lh > 8.0:
		h = maxf(lh, floorf(max_h / lh) * lh)   # show whole lines only
	if absf(_scroll.custom_minimum_size.y - h) > 0.5:
		_scroll.custom_minimum_size.y = h
	_update_more.call_deferred()


## Current line pitch of the page's main text (follows the text scale).
func _pitch_now(content: Control) -> float:
	if content is RuledBox:
		return (content as RuledBox).pitch()
	for c in content.get_children():
		if c is Label and c.has_meta("pitch_label"):
			var f := (c as Label).get_theme_font("font")
			return f.get_height((c as Label).get_theme_font_size("font_size")) + (c as Label).get_theme_constant("line_spacing")
	return _line_h


func _update_more() -> void:
	if _scroll == null or not is_instance_valid(_scroll) or _more == null or not is_instance_valid(_more):
		return
	var bar := _scroll.get_v_scroll_bar()
	var more_below := bar.max_value - bar.page - float(_scroll.scroll_vertical) > 2.0
	_more.modulate.a = 1.0 if more_below else 0.0


func _ex() -> Object:
	return Kit.explore()


func _call(method: String, args: Array, fallback):
	var ex := _ex()
	if ex == null or not ex.has_method(method):
		return fallback
	return ex.callv(method, args)


func _entry(id: String) -> Dictionary:
	var r = _call("entry", [id], {})
	return r if r is Dictionary else {}


func _card(cid: String) -> Dictionary:
	var r = _call("card", [cid], {})
	return r if r is Dictionary else {}


# ================================================================ modal hooks
func _on_close() -> void:
	if _scroll_tween != null and _scroll_tween.is_valid():
		_scroll_tween.kill()
	if _page_root != null and is_instance_valid(_page_root):
		_page_root.queue_free()
	_page_root = null
	_page_panel = null
	_scroll = null
	_more = null
	page = -1


func _on_contrast_changed() -> void:
	if is_open and page >= 0:
		var keep := page
		if _page_root != null and is_instance_valid(_page_root):
			_page_root.queue_free()
			_page_root = null
		_show_page(keep, 0)


func focus_default() -> void:
	if _next_btn != null and _next_btn.is_visible_in_tree():
		_next_btn.grab_focus()


func modal_input(event: InputEvent) -> bool:
	if not is_open:
		return false
	var advance := event.is_action_pressed("interact") or event.is_action_pressed("advance") \
		or event.is_action_pressed("ui_accept")
	if advance:
		if Time.get_ticks_msec() - _opened_ms < OPEN_GUARD_MS:
			return true
		var f := get_viewport().gui_get_focus_owner()
		if f == _prev_btn and not _prev_btn.disabled and not (event is InputEventKey and (event as InputEventKey).physical_keycode == KEY_E):
			prev()
		else:
			next()
		return true
	if event is InputEventKey and event.pressed and not event.echo:
		var k := (event as InputEventKey).physical_keycode
		if k == KEY_Q or k == KEY_PAGEUP:
			prev()
			return true
		if k == KEY_PAGEDOWN:
			_page_forward()
			return true
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_LEFT_SHOULDER:
			prev()
			return true
		if event.button_index == JOY_BUTTON_RIGHT_SHOULDER:
			_page_forward()
			return true
	if event.is_action_pressed("ui_left") or event.is_action_pressed("move_left"):
		prev()
		return true
	if event.is_action_pressed("ui_right") or event.is_action_pressed("move_right"):
		_page_forward()
		return true
	if event.is_action_pressed("ui_down", true) or event.is_action_pressed("move_down", true):
		_nudge(90.0)
		return true
	if event.is_action_pressed("ui_up", true) or event.is_action_pressed("move_up", true):
		_nudge(-90.0)
		return true
	return false


## Right / RB: next page without closing on the last one.
func _page_forward() -> void:
	if page < pages.size() - 1:
		Kit.ui_sound("history" if str(pages[page + 1]["type"]) == "card" else "page")
		_show_page(page + 1, 1)


func _nudge(dy: float) -> void:
	if _scroll == null or not is_instance_valid(_scroll):
		return
	_scroll.scroll_vertical = int(clampf(_scroll.scroll_vertical + dy, 0.0, _scroll.get_v_scroll_bar().max_value))
