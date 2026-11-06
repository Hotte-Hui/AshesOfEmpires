extends RefCounted
## InspectView (scripts/ui/inspect_view.gd) keeps the record card and the caption on the screen at 100 / 125 / 150 %
## text (text review r9, finding text-03: at 125 / 150 % the Chapter-4 record cards ran off the screen and
## „Schließen“ covered the card). Stand-alone and headless: mock Settings / Audio through the ui_kit overrides,
## the real theme, an explicit 1920x1080 rect and a forced layout (wrapped labels re-break at the width just
## assigned). For every item with a document image: the stage (1776x900 between the top margin and the footer)
## holds card and document, the caption shows every line (under the document; at 125 / 150 % a caption too long
## for that room moves into the card, at 100 % none does); the two C4 key cards (the longest item texts) need no
## scrolling at 100 / 125 % (the card widens with the text, 640 px at 100 %), at 150 % only a few lines; a card
## taller than the stage scrolls inside (wheel / down, "more below" mark) and still fits; the first view of every
## scrolling card ends a clear pixel or more between two line boxes read from the Labels themselves (review r9
## compl-07: a fallback-glyph line is taller, so lines are never assumed uniform). Writes nothing.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const SCENE := "res://scenes/ui/InspectView.tscn"
const SCALES := [1.0, 1.25, 1.5]
const KEY_CARDS := ["ev_c4_card_de", "ev_c4_card_ru"]
const STAGE := Vector2(1920 - 144, 1080 - 180)


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"reduced_motion": true, "text_scale": 1.0, "high_contrast": false}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


class MockAudio extends Node:
	func ui(_id) -> void:
		pass


var kit: TKit
var _settings: MockSettings


func run() -> Array:
	kit = TKit.new()
	var saved := UIKit.overrides.duplicate()
	_settings = MockSettings.new()
	kit.track(_settings)
	var audio := MockAudio.new()
	kit.track(audio)
	var o := saved.duplicate()
	o["Settings"] = _settings
	o["Audio"] = audio
	UIKit.overrides = o
	kit.run_case("every_document_fits_at_100_125_150", _all_fit)
	kit.run_case("c4_key_cards_need_no_scrolling", _key_cards)
	kit.run_case("tall_card_scrolls_inside_the_stage", _scrolls)
	kit.run_case("every_scrolling_card_ends_between_lines", _all_cuts)
	_scale(1.0)
	UIKit.overrides = saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _scale(s: float) -> void:
	_settings.values["text_scale"] = s
	UIKit.refresh_text_scale()                # what UIRoot does on Settings.changed


func _view() -> Control:
	var iv: Control = load(SCENE).instantiate()
	kit.mount(iv)
	iv.theme = UIKit.theme(false)             # what UIRoot applies to every modal
	return iv


## Lays the view out as on a 1920x1080 screen; fit_card() runs between the passes (in the game: deferred).
func _layout(iv: Control) -> void:
	iv.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	iv.size = Vector2(1920, 1080)
	var stage: Control = iv.get("_stage")
	stage.set_anchors_preset(Control.PRESET_TOP_LEFT)
	for _pass in 6:
		stage.position = Vector2(72, 60)
		stage.size = STAGE
		_sort(stage)
		iv.fit_card()


static func _sort(n: Node) -> void:
	if n is Container:
		n.notification(Container.NOTIFICATION_SORT_CHILDREN)
	for c in n.get_children():
		if c is Label or c is RichTextLabel:      # re-break wrapped lines at the width just assigned
			c.notification(Control.NOTIFICATION_THEME_CHANGED)
		_sort(c)


func _open(iv: Control, item: String, s: float) -> void:
	_scale(s)
	iv.open(item)
	_layout(iv)


func _items() -> Array:
	var out: Array = []
	for k in UIKit.doc_index().keys():
		if not str(k).begins_with("#"):
			out.append(str(k))
	out.sort()
	return out


## The laid-out line boxes [top, bottom] of the card's wrapping labels (body coordinates), read from the Labels
## themselves: each line's own height (a line with a fallback glyph is taller) plus the label's line spacing.
static func _line_boxes(body: Control) -> Array:
	var out: Array = []
	for c in body.get_children():
		var l := c as Label
		if l == null or not l.visible or l.autowrap_mode == TextServer.AUTOWRAP_OFF:
			continue
		var sb := l.get_theme_stylebox("normal")
		var y := l.position.y + (sb.get_margin(SIDE_TOP) if sb != null else 0.0)
		var ls := float(l.get_theme_constant("line_spacing"))
		for i in l.get_line_count():
			var h := float(l.get_line_height(i))
			out.append(Vector2(y, y + h))
			y += h + ls
	return out


## "" when the scrolling card's first view ends at least a pixel clear of every line box (descenders above the cut
## and accents below it stay whole), else what it cuts.
func _cut_problem(iv: Control) -> String:
	var sc: ScrollContainer = iv.get("_card_scroll")
	var h := sc.custom_minimum_size.y
	for b in _line_boxes(iv.get("_card_body")):
		if b.x < h + 1.0 and b.y > h - 1.0:
			return "the cut at %d meets the line %d–%d" % [int(h), int(b.x), int(b.y)]
	return ""


## Problems of the current layout ("" = fits): stage size, caption lines hidden or caption text lost.
func _misfit(iv: Control) -> String:
	var stage: Control = iv.get("_stage")
	var need: Vector2 = stage.get_combined_minimum_size()
	var bad: Array = []
	if need.x > STAGE.x + 0.5 or need.y > STAGE.y + 0.5:
		bad.append("stage needs %s > %s" % [need, STAGE])
	var cap: Label = iv.get("_caption")
	var card_alt: Label = iv.get("_card_alt")
	if cap.visible and cap.max_lines_visible >= 0 and cap.get_line_count() > cap.max_lines_visible:
		bad.append("caption %d lines, %d shown" % [cap.get_line_count(), cap.max_lines_visible])
	var alt := UIKit.doc_alt_text(str(iv.get("item_id")), UIKit.doc_for_item(str(iv.get("item_id"))))
	var shown := cap.text if cap.visible else (card_alt.text if card_alt.visible else "")
	if shown != alt:
		bad.append("caption text not shown")
	return ", ".join(bad)


# ------------------------------------------------------------------ cases
func _all_fit() -> bool:
	var iv := _view()
	var items := _items()
	kit.ok(items.size() >= 20 and items.has("ev_c4_card_de") and items.has("ev_c4_card_ru"), "documents found (%d)" % items.size())
	var bad: Array = []
	var moved: Array = []
	var card_alt: Label = iv.get("_card_alt")
	for s in SCALES:
		for it in items:
			_open(iv, it, s)
			var m := _misfit(iv)
			if m != "":
				bad.append("%s @%d%%: %s" % [it, int(s * 100), m])
			if card_alt.visible:
				moved.append("%s@%d" % [it, int(s * 100)])
			iv.close()
	kit.eq(bad, [], "every document and card fits 1920x1080 above the footer, every caption complete")
	kit.ok(not moved.any(func(x): return str(x).ends_with("@100")), "at 100 %% every caption stays under its document (%s)" % [moved])
	return true


func _key_cards() -> bool:
	var iv := _view()
	var card: Control = iv.get("_card")
	for it in KEY_CARDS:
		for s in SCALES:
			_open(iv, it, s)
			if s < 1.4:
				kit.ok(not iv.card_scrolls(), "%s @%d%%: the whole card text is visible without scrolling" % [it, int(s * 100)])
			else:
				# 150 %: the widest card beside the x3 document still runs a few lines over -> scrolls inside
				var sc: ScrollContainer = iv.get("_card_scroll")
				var body: Control = iv.get("_card_body")
				kit.ok(not iv.card_scrolls() or sc.custom_minimum_size.y >= 600.0, "%s @150%%: most of the card in view (%d px)" % [it, int(sc.custom_minimum_size.y)])
				kit.ok(body.get_combined_minimum_size().y - sc.custom_minimum_size.y <= 240.0, "%s @150%%: at most a few lines to scroll" % it)
				if iv.card_scrolls():
					var bad := _cut_problem(iv)
					kit.eq(bad, "", "%s @150%%: the first view ends in the gap between two lines" % it)
			kit.eq(_misfit(iv), "", "%s @%d%%: fits" % [it, int(s * 100)])
			if s == 1.0:
				kit.eq(card.custom_minimum_size.x, 640.0, "%s @100%%: the card keeps its 640 px" % it)
			else:
				kit.ok(card.custom_minimum_size.x > 640.0, "%s @%d%%: the card widens with the text (%d px)" % [it, int(s * 100), int(card.custom_minimum_size.x)])
			iv.close()
	return true


## compl-07: the first view of every scrolling record card (125 / 150 %) ends in a gap between two lines -- also
## where a line is taller than the font height (the booth log's caption: „⇄“ comes from a fallback font). The
## card's own measurement (_wrapped_height) matches every laid-out Label, so the cut never drifts from the text.
func _all_cuts() -> bool:
	var iv := _view()
	var body: Control = iv.get("_card_body")
	var scrolled: Array = []
	var bad: Array = []
	var drift: Array = []
	for s in [1.25, 1.5]:
		for it in _items():
			_open(iv, it, s)
			for c in body.get_children():
				var l := c as Label
				if l != null and l.visible and l.autowrap_mode != TextServer.AUTOWRAP_OFF:
					var want := l.get_combined_minimum_size().y
					var got: float = iv._wrapped_height(l, l.text, l.size.x)
					if absf(want - got) > 0.5:
						drift.append("%s @%d%%: %s… %.0f measured, %.0f laid out" % [it, int(s * 100), l.text.left(16), got, want])
			if iv.card_scrolls():
				scrolled.append("%s@%d" % [it, int(s * 100)])
				var p := _cut_problem(iv)
				if p != "":
					bad.append("%s @%d%%: %s" % [it, int(s * 100), p])
			iv.close()
	kit.eq(drift, [], "the card measures every label line by line exactly as it is laid out")
	kit.ok("ev_c3_booth_log@150" in scrolled and "ev_c4_card_de@150" in scrolled, "the booth log and Lindner's card scroll at 150 %% (%s)" % [scrolled])
	kit.eq(bad, [], "every scrolling card's first view ends between two lines")
	return true


func _scrolls() -> bool:
	var iv := _view()
	_open(iv, "ev_c4_card_de", 1.5)
	var desc: Label = iv.get("_desc")
	var long := ""
	for i in 4:
		long += UIKit.t("item.c4_card_de.description") + " "
	desc.text = long.strip_edges()
	_layout(iv)
	kit.ok(iv.card_scrolls(), "a card taller than the stage scrolls inside")
	kit.eq(_misfit(iv), "", "the long card still fits the stage")
	var sc: ScrollContainer = iv.get("_card_scroll")
	var more: Control = iv.get("_more")
	iv._update_more()
	kit.ok(more.modulate.a > 0.5, "the 'more below' mark shows at the top")
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN
	wheel.pressed = true
	kit.ok(iv.modal_input(wheel), "the wheel is taken by the card")
	kit.ok(sc.scroll_vertical > 0, "the wheel scrolls the card (%d)" % sc.scroll_vertical)
	var down := InputEventAction.new()
	down.action = "ui_down"
	down.pressed = true
	var before := sc.scroll_vertical
	kit.ok(iv.modal_input(down), "down is taken by the card")
	kit.ok(sc.scroll_vertical > before, "down scrolls on")
	for i in 80:
		iv.modal_input(down)
	iv._update_more()
	kit.ok(more.modulate.a < 0.5, "at the end the mark is gone")
	iv.close()
	_open(iv, "ev_c4_card_de", 1.0)
	kit.eq(sc.scroll_vertical, 0, "a new card starts at the top")
	kit.ok(not iv.card_scrolls(), "the short card does not scroll")
	var up := InputEventAction.new()
	up.action = "ui_up"
	up.pressed = true
	kit.ok(not iv.modal_input(up), "up / down stay free when nothing scrolls")
	iv.close()
	return true
