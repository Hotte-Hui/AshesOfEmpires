extends RefCounted
## Journal sheets stay on the screen (art review r9): art-02 -- the „Beweise“ / „Personen“ detail scrolls inside the
## sheet with „Ansehen“ pinned below it (Lindner's card at 100 / 150 % pushed the sheet to y 1329 and „Ansehen“ off
## the screen); art-08 -- the „Akte“ folder label lists each city once and stays inside its 210 px strip; art-04 --
## a clue without a document image (the cut hose) shows its evidence-board picture in the journal and in the
## InspectView instead of the placeholder.  Headless: mock Settings / Audio / Story through the ui_kit overrides,
## the real theme, an explicit 1920x1080 rect and forced container sorting.  Writes nothing.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const JOURNAL_SCENE := "res://scenes/ui/Journal.tscn"
const INSPECT_SCENE := "res://scenes/ui/InspectView.tscn"
const THEME := "res://assets/ui/theme.tres"
## the journal's root column on a 1920x1080 screen (journal.gd _ready: offsets 210 / 54)
const ROOT_RECT := Rect2(210, 54, 1500, 972)


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
var _story: Node


func run() -> Array:
	kit = TKit.new()
	var saved := UIKit.overrides.duplicate()
	_settings = MockSettings.new()
	kit.track(_settings)
	var audio := MockAudio.new()
	kit.track(audio)
	_story = kit.story()
	kit.play_until(_story, "c4d")
	var o := saved.duplicate()
	o["Settings"] = _settings
	o["Audio"] = audio
	o["Story"] = _story
	UIKit.overrides = o
	kit.run_case("evidence_detail_scrolls_inside_the_sheet", _evidence_fit)
	kit.run_case("folder_label_each_city_once_inside_the_strip", _folder_label)
	kit.run_case("clue_without_document_shows_its_board_picture", _board_picture)
	_scale(1.0)
	UIKit.overrides = saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _scale(s: float) -> void:
	_settings.values["text_scale"] = s
	UIKit.refresh_text_scale()


static func _sort(n: Node) -> void:
	if n is Container:
		n.notification(Container.NOTIFICATION_SORT_CHILDREN)
	for c in n.get_children():
		if c is Label or c is RichTextLabel:
			c.notification(Control.NOTIFICATION_THEME_CHANGED)
		_sort(c)


func _journal() -> Control:
	var holder := Control.new()
	holder.theme = load(THEME)
	holder.size = Vector2(1920, 1080)
	kit.mount(holder)
	var j: Control = load(JOURNAL_SCENE).instantiate()
	holder.add_child(j)
	return j


## Lays the journal's root column out at its screen rect (forced sorting, a few passes for wrapped labels).
func _layout(j: Control) -> Control:
	j.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	j.size = Vector2(1920, 1080)
	var root: Control = null
	for c in j.get_children():
		if c is VBoxContainer:
			root = c
	if root == null:
		return null
	root.set_anchors_preset(Control.PRESET_TOP_LEFT)
	for _pass in 4:
		root.position = ROOT_RECT.position
		root.size = ROOT_RECT.size
		_sort(root)
	return root


func _find(n: Node, pred: Callable) -> Node:
	if pred.call(n):
		return n
	for c in n.get_children():
		var r := _find(c, pred)
		if r != null:
			return r
	return null


## _show_detail queue_frees the previous record (gone the next frame in the game): detach it now, headless.
static func _flush(n: Node) -> void:
	for c in n.get_children():
		if c.is_queued_for_deletion():
			n.remove_child(c)
		else:
			_flush(c)


static func _scroll_ancestor(n: Node) -> ScrollContainer:
	var p := n.get_parent()
	while p != null:
		if p is ScrollContainer:
			return p
		p = p.get_parent()
	return null


# ------------------------------------------------------------------ cases
func _evidence_fit() -> bool:
	for s in [1.0, 1.5]:
		_scale(s)
		var j := _journal()
		j.open("evidence")
		var entries: Array = j._data.get("evidence", [])
		var card: Dictionary = {}
		for e in entries:
			if str(e.get("id")) == "ev_c4_card_de":
				card = e
		if not kit.ok(not card.is_empty(), "%d %%: Lindner's card is in „Beweise“" % int(s * 100)):
			j.close()
			continue
		var body: Control = j._body
		var detail: VBoxContainer = _find(body, func(n): return n is VBoxContainer and n.has_meta("actions"))
		if not kit.ok(detail != null, "%d %%: the evidence tab has a detail column with a pinned action row" % int(s * 100)):
			j.close()
			continue
		j._show_detail(detail, "evidence", card)
		_flush(j)
		var root := _layout(j)
		kit.ok(root != null and root.get_combined_minimum_size().y <= ROOT_RECT.size.y + 0.5,
			"%d %%: the journal fits the screen with Lindner's card focused (needs %.0f of %.0f px)"
			% [int(s * 100), root.get_combined_minimum_size().y if root else -1.0, ROOT_RECT.size.y])
		var desc: Label = _find(detail, func(n): return n is Label and n.text == str(card.get("desc", "")))
		kit.ok(desc != null and _scroll_ancestor(desc) != null, "%d %%: the record text scrolls inside the sheet" % int(s * 100))
		var acts: HBoxContainer = detail.get_meta("actions")
		var view: Button = _find(acts, func(n): return n is Button and not n.is_queued_for_deletion())
		kit.ok(view != null and _scroll_ancestor(view) == null, "%d %%: „Ansehen“ is pinned below the scrolling detail" % int(s * 100))
		var sheet: Control = j._sheet
		kit.ok(sheet.position.y + sheet.size.y <= ROOT_RECT.size.y + 0.5, "%d %%: the sheet ends inside the root column" % int(s * 100))
		# the people tab uses the same column: no stale „Ansehen“ there
		j.show_tab("people")
		var pdetail: VBoxContainer = _find(j._body, func(n): return n is VBoxContainer and n.has_meta("actions"))
		kit.ok(pdetail != null, "%d %%: „Personen“ shares the scrolling detail column" % int(s * 100))
		j.close()
	_scale(1.0)
	return true


func _folder_label() -> bool:
	var J: Script = load("res://scripts/ui/journal.gd")
	var model := {"places": [{"known": true, "title_key": "board.place.karsk"}, {"known": true, "title_key": "board.place.berlin"},
		{"known": false, "title_key": "board.place.veltrava"}, {"known": true, "title_key": "board.place.karsk_c4"},
		{"known": true, "title_key": "board.place.berlin_c4"}]}
	var cities: Array = J.board_cities(model)
	var uniq := {}
	for c in cities:
		uniq[c] = true
		kit.ok(not str(c).contains(" · "), "„%s“ is a city, not a place within it" % c)
	kit.eq(uniq.size(), cities.size(), "each city once: %s" % [cities])
	for s in [1.0, 1.5]:
		_scale(s)
		var j := _journal()
		j.open("board")
		_layout(j)
		var lab: Label = _find(j._body, func(n): return n is Label and n.clip_text and n.position == Vector2(39, 105))
		if kit.ok(lab != null, "%d %%: the folder carries its place label" % int(s * 100)):
			kit.ok(lab.size.x <= 210.5, "%d %%: the label keeps to its 210 px strip (%.0f)" % [int(s * 100), lab.size.x])
			kit.eq(lab.text_overrun_behavior, TextServer.OVERRUN_TRIM_ELLIPSIS, "%d %%: a long list ends in an ellipsis" % int(s * 100))
			var parts: Array = Array(lab.text.split(" · "))
			var seen := {}
			for p in parts:
				seen[p] = true
			kit.eq(seen.size(), parts.size(), "%d %%: no city twice on the folder (%s)" % [int(s * 100), lab.text])
		j.close()
	_scale(1.0)
	return true


func _board_picture() -> bool:
	var item := "ev_c3_cut_hose"
	if UIKit.doc_for_item(item) != "":
		return true                                # it has a document by now: nothing to stand in for
	var thumb := "res://assets/ui/board/thumbs/%s.png" % item
	if not kit.ok(ResourceLoader.exists(thumb), "the board has a picture of %s" % item):
		return true
	var iv: Control = load(INSPECT_SCENE).instantiate()
	kit.mount(iv)
	iv.theme = UIKit.theme(false)
	iv.open(item)
	var rect: TextureRect = iv.get("_doc_rect")
	var ph: Control = iv.get("_placeholder")
	kit.ok(rect != null and rect.visible and rect.texture != null and rect.texture.resource_path == thumb,
		"InspectView shows the board picture of the cut hose")
	kit.ok(ph != null and not ph.visible, "no „Abbildung wird nachgereicht“ placeholder")
	iv.close()
	# the journal's evidence detail shows it too
	var g := kit.story()
	kit.play_until(g, "c3g")
	var o := UIKit.overrides.duplicate()
	o["Story"] = g
	UIKit.overrides = o
	var j := _journal()
	j.open("evidence")
	var hose: Dictionary = {}
	for e in j._data.get("evidence", []):
		if str(e.get("id")) == item:
			hose = e
	if kit.ok(not hose.is_empty(), "the cut hose is in „Beweise“ after Chapter 3"):
		var detail: VBoxContainer = _find(j._body, func(n): return n is VBoxContainer and n.has_meta("actions"))
		j._show_detail(detail, "evidence", hose)
		_flush(j)
		var img: TextureRect = _find(detail, func(n): return n is TextureRect and not n.is_queued_for_deletion() and n.texture != null)
		kit.ok(img != null and img.texture.resource_path == thumb, "the journal shows the board picture of the cut hose")
	j.close()
	o["Story"] = _story
	UIKit.overrides = o
	return true
