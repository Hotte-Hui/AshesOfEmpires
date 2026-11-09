extends "res://scripts/ui/ui_modal.gd"
## Joint evidence check „Gegenprobe“ (pz_c3_check / objective c3d_solve_check, documentation/C3P2_DESIGN.md
## §2.7) — the first thing Alexei and Konrad do together. The two halves lie side by side: LEFT the four
## papers of Alexei's freight chain in their fixed order (strips cut from the very inspect documents the
## player read), in the MIDDLE one slot per paper, RIGHT the tray with four entries of the registry's intake
## book and the protocol (Konrad's half). The player lays to each paper the entry that describes the same
## journey; each pair shares exactly one fact. The answer is the card order top -> bottom.
##
## Registered by data/chapters/c3.json (puzzles.c3d_solve_check); ChapterExt.puzzle_ui instances this scene
## once under UIRoot (modal stack), sets `ui_root`, Game calls open(obj_id) and awaits `closed`. Works
## stand-alone (tests) as well: then open()/close() just show/hide.
##
## Key contract (= ProtocolPuzzle; scripts/core/inputplay.gd relies on it): property `is_open`, property
## `symbols` (the tray in display order), key N lays symbols[N - 1] into the next empty row (top first),
## Backspace takes back the card laid last, R clears, Enter submits Story.solve_puzzle(obj_id, [card ids in
## row order]) — only with every row filled, otherwise the „incomplete“ note (no attempt) — Esc closes.
## Mouse: click a tray card = next empty row (or the row chosen before), drag a card onto any row (an
## occupied row sends its card back; row to row swaps), click a filled row = take its card back, click an
## empty row = choose it for the next card. Pad / arrows: focus moves over tray, rows and buttons; pad A (or
## Space) does what a click does, X takes back, Y checks; cancel / B first forgets a chosen row, then closes.
## Wrong answers cost nothing: neutral note, the cards stay, the engine counts the attempt; the hint appears
## per Settings.puzzle_hints (0 off · 1 after Story.puzzle_hint_available · 2 at once).
## Success: the matching marks appear on both halves (red pencil on each paper, the shared words underlined
## on each entry), a brace bundles the four rows into Kordon-17, stamp + success text, `solved(obj_id)`
## once; the modal closes after a reading beat (≤ SUCCESS_BEAT_MAX) or earlier on confirm.
## Text scale: card faces use fixed type (like the protocol name plates); at 125 % / 150 % the „Lupe“ shows
## the focused card / row in the scaled size, the notes wrap side by side. Cards are told apart by text AND
## shape glyph (ring / cross / star / bowtie) — never by colour. Pixel art (assets/ui/puzzle/c3p2_*,
## tools/pixelgen/gen_ui_c3p2.py) is drawn 1:1 and shown at exactly x3.

signal solved(obj_id: String)

const PX := 3
const ART := "res://assets/ui/puzzle/"
const BOARD_JSON := "res://assets/ui/puzzle/c3p2_board.json"
const DEFAULT_SYMBOLS := ["out_2340", "january", "in_c17_44", "par_4"]
const ROWS := ["weighbill", "departures", "travel_order", "timetable"]
const SLOT_COUNT := 4
const INK := Color("1a1c2a")
const PENCIL := Color("a8382e")
const PENCIL_HC := Color("7a2a26")
const LINK := Color("62716e")
const LINK_DONE := Color("dca16e")
const PAPER := Color("e6dec2")
const PAPER_EDGE := Color("b0aa93")
## The one shared fact of each pair as it is written on the entry (underlined after the solution). Words,
## not positions: a word the text does not contain only loses its underline. German first, then the English wording.
const MATCH_WORDS := {"in_c17_44": ["Plombe C-17/44", "2410 kg", "seal C-17/44"],
	"out_2340": ["23.40 Uhr", "Gleis 5", "23:40", "platform 5"],
	"par_4": ["„Begleitgut“", "„begleitete Personen“", "“escorted goods”", "“escorted persons”"],
	"january": ["drei Wagen", "three wagons"]}
const CARD_FONT := 19
const LABEL_FONT := 19
const LINK_W := 54
const TRAY_GAP := 30
## Swallow confirm/cancel presses this long after success, so a key still held for „Prüfen“ cannot skip it.
const SUCCESS_GUARD_MS := 600
## Longest reading beat before the solved modal closes by itself. The real-input driver
## (scripts/core/inputplay.gd) waits 8 s for `closed` after the correct order — stay well inside that.
const SUCCESS_BEAT_MAX := 7.0
## Delay between the matching marks of two rows after the solution (0 with reduced motion).
const MARK_STEP := 0.34

var suppress_toasts := true
var obj_id := ""
## Tray order (display_symbols of the puzzle). Key N always means symbols[N - 1].
var symbols: Array = DEFAULT_SYMBOLS.duplicate()
## Row contents top to bottom; "" = empty.
var slots: Array = ["", "", "", ""]
## Ids of the cards on the board in the order they were laid (Backspace takes back the last one).
var history: Array = []
## Row chosen for the next card (click / accept on an empty row), -1 = the next empty row from the top.
var armed := -1
## Read-only: the laid cards in row order (empty rows skipped).
var order: Array:
	get:
		var out: Array = []
		for s in slots:
			if str(s) != "":
				out.append(str(s))
		return out
var solved_count := 0

var _puzzle: Dictionary = {}
var _meta: Dictionary = {}
var _rows_meta: Array = []
var _fails := 0
var _done := false
var _marks_shown := 0
var _solved_at := 0
var _beat_token := 0
var _dragging := false
var _drag_end_ms := -1000
var _drop_hover := -1
var _lupe_for: Control = null
var _lupe_kind := ""
var _panel: PanelContainer
var _root_box: VBoxContainer
var _board: HBoxContainer
var _paper_cells: Array[Control] = []
var _row_marks: Array[TextureRect] = []
var _slot_col: VBoxContainer
var _slot_buttons: Array[Button] = []
var _slot_cards: Array[TextureRect] = []
var _slot_texts: Array[RichTextLabel] = []
var _slot_captions: Array[Label] = []
var _slot_armed: Array[NinePatchRect] = []
var _tray_holder: Control
var _tray_buttons: Dictionary = {}
var _tray_texts: Dictionary = {}
var _tray_built: Array = []
var _tray_col: VBoxContainer
var _kordon: Control
var _state_label: Label
var _notes_row: BoxContainer
var _notes_col: VBoxContainer
var _instr: Label
var _tip: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _success_box: PanelContainer
var _success_label: Label
var _undo_btn: Button
var _reset_btn: Button
var _check_btn: Button
var _close_btn: Button
var _actions: GridContainer
var _footer: HBoxContainer
var _controls: Control
var _lupe: PanelContainer
var _lupe_kicker: Label
var _lupe_text: Label
var _lupe_kicker2: Label
var _lupe_text2: Label


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	var meta = Kit.json(BOARD_JSON)
	_meta = meta if meta is Dictionary else {}
	_rows_meta = _meta.get("rows", []) if _meta.get("rows") is Array else []
	add_child(Kit.dimmer(0.8))
	_panel = Kit.panel()
	Kit.full_rect(_panel)
	_panel.offset_left = 28
	_panel.offset_right = -28
	_panel.offset_top = 10
	_panel.offset_bottom = -10
	add_child(_panel)
	_root_box = Kit.vbox(0)
	_panel.add_child(_root_box)
	# --- header: title + subtitle on one line, copper rule, instruction
	var head := Kit.hbox(28)
	_root_box.add_child(head)
	head.add_child(Kit.label(Kit.t("ui.c3p2.check.title"), "HeadingLabel"))
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	push.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(push)
	var sub := Kit.label(Kit.t("ui.c3p2.check.subtitle"), "DimLabel")
	sub.size_flags_vertical = Control.SIZE_SHRINK_END
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(sub)
	_root_box.add_child(HSeparator.new())
	_instr = Kit.wrap_label(Kit.t("ui.c3p2.check.instruction"), "BodyLabel")
	_instr.name = "Instruction"
	Kit.scalable(_instr, 26)
	_root_box.add_child(_instr)
	_root_box.add_child(_gap(8))
	# --- the two halves on one table: papers | rows (slots) | tray
	_board = Kit.hbox(0)
	_board.name = "Board"
	_root_box.add_child(_board)
	_build_papers()
	_build_slots()
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(TRAY_GAP, 0)
	gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_board.add_child(gap)
	_build_tray_column()
	_root_box.add_child(_gap(10))
	# --- notes (feedback / hint / success) + actions under the tray
	var bottom := Kit.hbox(TRAY_GAP)
	bottom.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root_box.add_child(bottom)
	_notes_col = Kit.vbox(12)
	_notes_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bottom.add_child(_notes_col)
	_build_notes(_notes_col)
	_actions = GridContainer.new()
	_actions.columns = 2
	_actions.add_theme_constant_override("h_separation", 16)
	_actions.add_theme_constant_override("v_separation", 14)
	_actions.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_actions.custom_minimum_size.x = _card_size().x
	_actions.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	bottom.add_child(_actions)
	_undo_btn = Kit.button(Kit.t("ui.c3p2.check.undo"))
	_undo_btn.pressed.connect(undo)
	_reset_btn = Kit.button(Kit.t("ui.c3p2.check.reset"))
	_reset_btn.pressed.connect(reset_order)
	_check_btn = Kit.button(Kit.t("ui.c3p2.check.check"))
	_check_btn.pressed.connect(submit)
	_close_btn = Kit.button(Kit.t("ui.c3p2.check.close"))
	_close_btn.pressed.connect(close)
	for b in [_undo_btn, _reset_btn, _check_btn, _close_btn]:
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_actions.add_child(b)
	_root_box.add_child(_gap(8))
	# --- footer: input hints
	_footer = Kit.hbox(24)
	_root_box.add_child(_footer)
	_controls = Kit.controls_row([["1–4", Kit.t("ui.c3p2.check.hint_place")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.c3p2.check.hint_undo")],
		["R", Kit.t("ui.c3p2.check.hint_reorder")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.c3p2.check.hint_check")],
		[Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]])
	_controls.tooltip_text = Kit.t("ui.c3p2.check.controls")
	_controls.mouse_filter = Control.MOUSE_FILTER_PASS
	_controls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_footer.add_child(_controls)
	_build_lupe()
	_build_tray()
	_apply_layout()
	_refresh()
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)


func _gap(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _m(section: String, key: String, fallback):
	var s = _meta.get(section, {})
	return s.get(key, fallback) if s is Dictionary else fallback


func _rect(a, scale := PX) -> Rect2:
	if a is Array and a.size() >= 4:
		return Rect2(float(a[0]) * scale, float(a[1]) * scale, float(a[2]) * scale, float(a[3]) * scale)
	return Rect2()


func _card_size() -> Vector2:
	var s = _m("card", "size", [152, 34])
	return Vector2(int(s[0]), int(s[1])) * PX


func _row_h() -> float:
	return float(_m("layout", "row_h", 39)) * PX


func _row_gap() -> int:
	return int(_m("layout", "row_gap", 2)) * PX


func _label_h() -> float:
	return float(_m("layout", "label_h", 7)) * PX


func _paper_w() -> float:
	return float(_m("layout", "paper_w", 242)) * PX + LINK_W


func _card_top() -> float:
	return floorf((_row_h() - _card_size().y) * 0.5)


func _row_meta(i: int) -> Dictionary:
	return _rows_meta[i] if i >= 0 and i < _rows_meta.size() and _rows_meta[i] is Dictionary else {}


## Column header with a fixed height, so the four rows of the three columns line up.
func _column_head(text: String, variation := "KickerLabel") -> Label:
	var l := Kit.label(text, variation)
	l.custom_minimum_size.y = 30
	l.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	l.clip_text = true
	return l


# ---------------------------------------------------------------- left: Alexei's papers
func _build_papers() -> void:
	var col := Kit.vbox(_row_gap())
	col.name = "Papers"
	_board.add_child(col)
	col.add_child(_column_head(Kit.t("ui.c3p2.check.column.alexei").to_upper().replace("ß", "SS")))
	for i in SLOT_COUNT:
		var rm := _row_meta(i)
		var cell := Control.new()
		cell.name = "Paper%d" % (i + 1)
		cell.custom_minimum_size = Vector2(_paper_w(), _row_h())
		cell.mouse_filter = Control.MOUSE_FILTER_PASS
		cell.tooltip_text = row_text(i)
		col.add_child(cell)
		var chip := _number_chip(str(i + 1), "PlatePanel")
		chip.position = Vector2(0, -2)
		cell.add_child(chip)
		var lab := Kit.label(row_text(i), "BodyLabel", LABEL_FONT)
		lab.name = "Label"
		lab.position = Vector2(36, -3)
		lab.size = Vector2(_paper_w() - 40, _label_h())
		lab.clip_text = true
		lab.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		cell.add_child(lab)
		var size_px := Vector2(rm.get("size", [200, 30])[0], rm.get("size", [200, 30])[1]) * PX
		var shadow := ColorRect.new()
		shadow.color = Color(0, 0, 0, 0.42)
		shadow.position = Vector2(6, _label_h() + 6)
		shadow.size = size_px
		shadow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cell.add_child(shadow)
		var strip := Kit.pixel_image(Kit.tex(ART + str(rm.get("file", "c3p2_row_%s.png" % ROWS[i]))), PX)
		strip.name = "Strip"
		strip.stretch_mode = TextureRect.STRETCH_SCALE
		strip.position = Vector2(0, _label_h())
		strip.size = size_px
		cell.add_child(strip)
		var mark := Kit.pixel_image(Kit.tex(ART + str(rm.get("mark_file", "c3p2_mark_%s.png" % ROWS[i]))), PX)
		mark.name = "Mark"
		mark.stretch_mode = TextureRect.STRETCH_SCALE
		mark.position = strip.position
		mark.size = size_px
		mark.visible = false
		cell.add_child(mark)
		cell.draw.connect(_draw_link.bind(cell, i, size_px.x))
		cell.mouse_entered.connect(_show_lupe.bind(cell, "row", i))
		cell.mouse_exited.connect(_hide_lupe.bind(cell))
		_paper_cells.append(cell)
		_row_marks.append(mark)


## Dashed pencil leader from the end of the paper strip to its row (solid with „=“ once the check holds).
func _draw_link(cell: Control, i: int, strip_w: float) -> void:
	var y := floorf(_card_top() + _card_size().y * 0.5) - 1.0
	var x0 := strip_w + 12.0
	var x1 := cell.size.x - 6.0
	if x1 - x0 < 18.0:
		return
	var done := _done and i < _marks_shown
	var col := LINK_DONE if done else LINK
	if done:
		cell.draw_rect(Rect2(x0, y, x1 - x0 - 6.0, 3), col)
		var mx := floorf((x0 + x1) * 0.5 / 3.0) * 3.0
		cell.draw_rect(Rect2(mx - 6, y - 9, 15, 3), col)
		cell.draw_rect(Rect2(mx - 6, y + 9, 15, 3), col)
	else:
		var x := x0
		while x < x1 - 12.0:
			cell.draw_rect(Rect2(x, y, 6, 3), col)
			x += 12.0
	for k in 4:          # arrow head, 3 px steps
		cell.draw_rect(Rect2(x1 - 12.0 + k * 3.0, y - 9.0 + k * 3.0, 3, 21.0 - k * 6.0), col)


# ---------------------------------------------------------------- middle: the rows (slots)
func _build_slots() -> void:
	_slot_col = Kit.vbox(_row_gap())
	_slot_col.name = "Rows"
	_board.add_child(_slot_col)
	_state_label = _column_head("", "DimLabel")
	_slot_col.add_child(_state_label)
	var cs := _card_size()
	for i in SLOT_COUNT:
		var cell := Control.new()
		cell.custom_minimum_size = Vector2(cs.x, _row_h())
		cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_slot_col.add_child(cell)
		var b := Kit.button("", "CardButton")
		b.name = "Slot%d" % (i + 1)
		b.custom_minimum_size = cs
		b.size = cs
		b.position = Vector2(0, _card_top())
		b.pressed.connect(_on_slot_pressed.bind(i))
		b.mouse_entered.connect(_hover_focus.bind(b))
		b.focus_entered.connect(_show_lupe.bind(b, "slot", i))
		b.focus_exited.connect(_hide_lupe.bind(b))
		b.set_drag_forwarding(_drag_from_slot.bind(i, b), _can_drop_slot.bind(i), _drop_on_slot.bind(i))
		cell.add_child(b)
		var frame := Kit.pixel_image(Kit.tex(ART + str(_m("slot", "file", "c3p2_slot.png"))), PX)
		frame.stretch_mode = TextureRect.STRETCH_SCALE
		frame.size = cs
		b.add_child(frame)
		var cap := Kit.label("", "KickerLabel", 20, Kit.C_TEXT_DIM)
		cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cap.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		cap.position = Vector2(_rect(_m("card", "text", [21, 3, 128, 29])).position.x, 0)
		cap.size = Vector2(cs.x - cap.position.x - 12, cs.y)
		b.add_child(cap)
		var card := Kit.pixel_image(null, PX)
		card.stretch_mode = TextureRect.STRETCH_SCALE
		card.size = cs
		card.visible = false
		b.add_child(card)
		var txt := _card_text_label(cs)
		txt.visible = false
		b.add_child(txt)
		var armed_frame := _frame_rect(cs, Color(1, 0.86, 0.62, 1))
		armed_frame.name = "Armed"
		b.add_child(armed_frame)
		_add_focus_frame(b)
		_slot_buttons.append(b)
		_slot_cards.append(card)
		_slot_texts.append(txt)
		_slot_captions.append(cap)
		_slot_armed.append(armed_frame)


# ---------------------------------------------------------------- right: the tray (Konrad's half)
func _build_tray_column() -> void:
	var col := Kit.vbox(0)
	col.name = "TrayColumn"
	_board.add_child(col)
	col.add_child(_column_head(Kit.t("ui.c3p2.check.column.registry").to_upper().replace("ß", "SS")))
	_tray_holder = Control.new()
	_tray_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rows_h := _row_h() * SLOT_COUNT + _row_gap() * (SLOT_COUNT - 1)
	_tray_holder.custom_minimum_size = Vector2(_card_size().x, rows_h + _row_gap())
	col.add_child(_tray_holder)
	_tray_col = Kit.vbox(_row_gap())
	_tray_col.position = Vector2(0, float(_row_gap()))
	_tray_holder.add_child(_tray_col)
	# the end of the check: a brace over the four rows, one place
	_kordon = Control.new()
	_kordon.name = "Kordon"
	_kordon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_kordon.size = Vector2(_card_size().x, rows_h)
	_kordon.position = Vector2(0, float(_row_gap()))
	_kordon.visible = false
	_tray_holder.add_child(_kordon)
	var br := Kit.pixel_image(Kit.tex(ART + str(_m("bracket", "file", "c3p2_bracket.png"))), PX)
	br.stretch_mode = TextureRect.STRETCH_SCALE
	var bs = _m("bracket", "size", [13, 161])
	br.size = Vector2(int(bs[0]), int(bs[1])) * PX
	br.position = Vector2(0, floorf((_kordon.size.y - br.size.y) * 0.5))
	_kordon.add_child(br)
	var kv := Kit.vbox(6)
	kv.position = Vector2(br.size.x + 24, 0)
	kv.size = Vector2(_kordon.size.x - br.size.x - 24, _kordon.size.y)
	kv.alignment = BoxContainer.ALIGNMENT_CENTER
	_kordon.add_child(kv)
	var k1 := Kit.label(Kit.t("ui.c3p2.check.kordon"), "HeadingLabel", 0, Kit.C_COPPER_L)
	k1.name = "KordonTitle"
	kv.add_child(k1)
	var k2 := Kit.label(Kit.t("ui.c3p2.check.kordon_sub").to_upper().replace("ß", "SS"), "KickerLabel")
	kv.add_child(k2)
	var k3 := Kit.wrap_label(Kit.t("ui.c3p2.check.kordon_note"), "BodyLabel", 24)
	k3.custom_minimum_size.x = kv.size.x
	kv.add_child(k3)


func _build_tray() -> void:
	if _tray_built == symbols and _tray_col.get_child_count() == symbols.size():
		return
	for c in _tray_col.get_children():
		_tray_col.remove_child(c)
		c.queue_free()
	_tray_buttons.clear()
	_tray_texts.clear()
	_tray_built = symbols.duplicate()
	var cs := _card_size()
	var i := 0
	for sym in symbols:
		i += 1
		var cell := Control.new()
		cell.custom_minimum_size = Vector2(cs.x, _row_h())
		cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_tray_col.add_child(cell)
		var b := Kit.button("", "CardButton")
		b.name = "Card_" + str(sym)
		b.custom_minimum_size = cs
		b.size = cs
		b.position = Vector2(0, _card_top())
		b.tooltip_text = Kit.t("ui.c3p2.check.card_tip", {"name": card_name(str(sym))})
		b.pressed.connect(_on_card_pressed.bind(str(sym)))
		b.mouse_entered.connect(_hover_focus.bind(b))
		b.focus_entered.connect(_show_lupe.bind(b, "card", i - 1))
		b.focus_exited.connect(_hide_lupe.bind(b))
		b.set_drag_forwarding(_drag_from_tray.bind(str(sym), b), _can_drop_tray, _drop_on_tray)
		cell.add_child(b)
		var img := Kit.pixel_image(Kit.tex(_card_file(str(sym))), PX)
		img.stretch_mode = TextureRect.STRETCH_SCALE
		img.size = cs
		b.add_child(img)
		var txt := _card_text_label(cs)
		txt.text = _card_bbcode(str(sym), false)
		b.add_child(txt)
		_add_focus_frame(b)
		var chip := _number_chip(Kit.key_name(KEY_1 + i - 1), "KeyChipPanel", "KeyHintLabel")
		chip.position = Vector2(-12, -15)
		chip.name = "Key"
		b.add_child(chip)
		_tray_buttons[str(sym)] = b
		_tray_texts[str(sym)] = txt


func _number_chip(text: String, panel_var: String, label_var := "KickerLabel") -> Control:
	var chip := Kit.panel(panel_var)
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if panel_var == "PlatePanel":
		chip.add_theme_stylebox_override("panel", _plate_small())
	var l := Kit.label(text, label_var, 19 if label_var == "KickerLabel" else 0)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.custom_minimum_size.x = 12
	chip.add_child(l)
	return chip


func _plate_small() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/plate.png")
	st.set_texture_margin(SIDE_LEFT, 15)
	st.set_texture_margin(SIDE_TOP, 9)
	st.set_texture_margin(SIDE_RIGHT, 9)
	st.set_texture_margin(SIDE_BOTTOM, 9)
	st.set_content_margin(SIDE_LEFT, 13)
	st.set_content_margin(SIDE_TOP, 1)
	st.set_content_margin(SIDE_RIGHT, 9)
	st.set_content_margin(SIDE_BOTTOM, 1)
	return st


## The typed entry on an index card (registry typewriter), fixed size like the protocol name plates.
func _card_text_label(cs: Vector2) -> RichTextLabel:
	var tr := _rect(_m("card", "text", [21, 3, 128, 29]))
	if tr.size == Vector2.ZERO:
		tr = Rect2(63, 9, cs.x - 72, cs.y - 15)
	var l := RichTextLabel.new()
	l.bbcode_enabled = true
	l.scroll_active = false
	l.fit_content = false
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("normal_font", Kit.font("fv_type"))
	l.add_theme_font_size_override("normal_font_size", CARD_FONT)
	l.add_theme_color_override("default_color", INK)
	l.add_theme_constant_override("line_separation", -2)
	l.position = tr.position
	l.size = tr.size
	l.name = "Text"
	return l


func _card_bbcode(sym: String, highlight: bool) -> String:
	var t := card_name(sym).replace("[", "[lb]")
	if not highlight:
		return t
	var col := (PENCIL_HC if Kit.high_contrast() else PENCIL).to_html(false)
	for w in MATCH_WORDS.get(sym, []):
		var ww := str(w).replace("[", "[lb]")
		if t.contains(ww):
			t = t.replace(ww, "[color=#%s][u]%s[/u][/color]" % [col, ww])
	return t


## Amber outline around a card: the row chosen for the next card / the row under a dragged card.
func _frame_rect(cs: Vector2, tint: Color) -> NinePatchRect:
	var f := NinePatchRect.new()
	f.texture = Kit.tex("res://assets/ui/frames/button_focus.png")
	f.patch_margin_left = 9
	f.patch_margin_top = 9
	f.patch_margin_right = 9
	f.patch_margin_bottom = 9
	f.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	f.mouse_filter = Control.MOUSE_FILTER_IGNORE
	f.position = Vector2(-3, -3)
	f.size = cs + Vector2(6, 6)
	f.modulate = tint
	f.visible = false
	return f


## Amber focus frame on top of the card art (the theme's focus style would be hidden by the children).
func _add_focus_frame(b: Button) -> void:
	var f := NinePatchRect.new()
	f.name = "Focus"
	f.texture = Kit.tex("res://assets/ui/frames/button_focus.png")
	f.patch_margin_left = 9
	f.patch_margin_top = 9
	f.patch_margin_right = 9
	f.patch_margin_bottom = 9
	f.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	f.mouse_filter = Control.MOUSE_FILTER_IGNORE
	f.position = Vector2(-6, -6)
	f.size = b.custom_minimum_size + Vector2(12, 12)
	f.visible = false
	b.add_child(f)
	b.focus_entered.connect(func() -> void: f.visible = true)
	b.focus_exited.connect(func() -> void: f.visible = false)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())


func _card_file(sym: String) -> String:
	var files = _m("card", "files", {})
	if files is Dictionary and files.has(sym):
		return ART + str(files[sym])
	return ART + "c3p2_card_%s.png" % sym


func card_name(sym: String) -> String:
	return Kit.t("ui.c3p2.check.card." + sym)


func row_text(i: int) -> String:
	return Kit.t("ui.c3p2.check.row." + str(ROWS[i])) if i >= 0 and i < ROWS.size() else ""


# ---------------------------------------------------------------- notes, success, lupe
func _build_notes(parent: VBoxContainer) -> void:
	_tip = Kit.wrap_label("", "ControlHintLabel")
	_tip.name = "Tip"
	parent.add_child(_tip)
	_notes_row = BoxContainer.new()
	_notes_row.add_theme_constant_override("separation", 24)
	_notes_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_notes_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(_notes_row)
	_feedback = Kit.wrap_label("", "BodyLabel")
	_feedback.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_feedback.size_flags_stretch_ratio = 0.6
	_feedback.visible = false
	Kit.scalable(_feedback, 24)
	_notes_row.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	_hint_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_hint_box.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	var hh := Kit.hbox(14)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hh.add_child(hic)
	_hint_label = Kit.wrap_label(Kit.t("ui.c3p2.check.hint"), "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 22)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	_notes_row.add_child(_hint_box)
	_success_box = Kit.panel("PaperCardPanel")
	_success_box.add_theme_stylebox_override("panel", _paper_box())
	_success_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sv := Kit.hbox(24)
	_success_box.add_child(sv)
	var stamp := _make_stamp(Kit.t("ui.c3p2.check.stamp").to_upper().replace("ß", "SS"))
	stamp.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sv.add_child(stamp)
	_success_label = Kit.wrap_label(Kit.t("ui.c3p2.check.success"), "TypeLabel")
	_success_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_success_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	Kit.scalable(_success_label, 22)
	sv.add_child(_success_label)
	_success_box.visible = false
	parent.add_child(_success_box)


func _paper_box() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/paper.png")
	for side in 4:
		st.set_texture_margin(side, 21)
	st.set_content_margin(SIDE_LEFT, 30)
	st.set_content_margin(SIDE_RIGHT, 30)
	st.set_content_margin(SIDE_TOP, 18)
	st.set_content_margin(SIDE_BOTTOM, 20)
	return st


func _make_stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(252, 78)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_evidence.png")
	frame.size = Vector2(252, 78)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 27)
	var f := l.get_theme_font("font")
	if f != null:                       # a long word shrinks until it sits inside the frame
		var fs := 27
		while fs > 18 and f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > 214.0:
			fs -= 1
		l.add_theme_font_size_override("font_size", fs)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(252, 78)
	l.pivot_offset = Vector2(126, 39)
	l.rotation = deg_to_rad(-3.0)
	l.modulate = Color(1, 1, 1, 0.92)
	c.add_child(l)
	return c


## „Lupe“: at 125 % / 150 % text the focused card or row is shown once more in the chosen size (the card faces
## keep fixed type so the board never outgrows the screen). Floats over the board, never takes focus.
func _build_lupe() -> void:
	_lupe = Kit.panel("PaperCardPanel")
	_lupe.name = "Lupe"
	_lupe.add_theme_stylebox_override("panel", _paper_box())
	_lupe.top_level = true
	_lupe.z_index = 40
	_lupe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_lupe.custom_minimum_size.x = _card_size().x
	_lupe.visible = false
	add_child(_lupe)
	var v := Kit.vbox(6)
	_lupe.add_child(v)
	_lupe_kicker = Kit.label("", "KickerLabel", 0, Kit.C_COPPER_D)
	Kit.scalable(_lupe_kicker, 20)
	v.add_child(_lupe_kicker)
	_lupe_text = Kit.wrap_label("", "TypeLabel", 0, INK)
	Kit.scalable(_lupe_text, 22)
	v.add_child(_lupe_text)
	_lupe_kicker2 = Kit.label("", "KickerLabel", 0, Kit.C_COPPER_D)
	Kit.scalable(_lupe_kicker2, 20)
	v.add_child(_lupe_kicker2)
	_lupe_text2 = Kit.wrap_label("", "TypeLabel", 0, INK)
	Kit.scalable(_lupe_text2, 22)
	v.add_child(_lupe_text2)
	for l in [_lupe_kicker, _lupe_text, _lupe_kicker2, _lupe_text2]:
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _lupe_kicker_color() -> Color:
	return INK if Kit.high_contrast() else Kit.C_COPPER_D


func lupe_wanted() -> bool:
	return Kit.text_scale() > 1.05


func lupe_shown() -> bool:
	return _lupe != null and _lupe.visible


func lupe_text() -> String:
	if not lupe_shown():
		return ""
	var parts: Array = []
	for l in [_lupe_kicker, _lupe_text, _lupe_kicker2, _lupe_text2]:
		if l.visible and l.text != "":
			parts.append(l.text)
	return "\n".join(parts)


func _show_lupe(anchor: Control, kind: String, i: int) -> void:
	if not lupe_wanted() or not is_open or _done:
		return
	var up := func(s: String) -> String: return s.to_upper().replace("ß", "SS")
	_lupe_kicker2.visible = false
	_lupe_text2.visible = false
	match kind:
		"card":
			var sym := str(symbols[i]) if i >= 0 and i < symbols.size() else ""
			_lupe_kicker.text = up.call(Kit.t("ui.c3p2.check.lupe.entry", {"key": Kit.key_name(KEY_1 + i)}))
			_lupe_text.text = card_name(sym)
		"slot", "row":
			_lupe_kicker.text = up.call(Kit.t("ui.c3p2.check.lupe.paper", {"n": i + 1}))
			_lupe_text.text = row_text(i)
			var sym := str(slots[i]) if kind == "slot" or str(slots[i]) != "" else ""
			if sym != "":
				_lupe_kicker2.text = up.call(Kit.t("ui.c3p2.check.lupe.laid"))
				_lupe_text2.text = card_name(sym)
			elif kind == "slot":
				_lupe_kicker2.text = ""
				_lupe_text2.text = Kit.t("ui.c3p2.check.lupe.empty")
			_lupe_kicker2.visible = _lupe_kicker2.text != ""
			_lupe_text2.visible = _lupe_text2.text != ""
	for l in [_lupe_kicker, _lupe_kicker2]:
		l.add_theme_color_override("font_color", _lupe_kicker_color())
	_lupe_for = anchor
	_lupe_kind = kind
	_lupe.visible = true
	_lupe.reset_size()
	_place_lupe.call_deferred(anchor)


func _place_lupe(anchor: Control) -> void:
	if not is_instance_valid(anchor) or _lupe_for != anchor or not _lupe.visible or not anchor.is_inside_tree():
		return
	_lupe.reset_size()
	_lupe.position = lupe_position(anchor.get_global_rect(), _lupe_kind, _lupe.size)


## Where the Lupe sits: never over the paper strips (that is what the player compares with). An entry of the
## tray is read over the rows column, a row (paper + laid entry) over the tray column — same row height,
## clamped to the screen.
func lupe_position(r: Rect2, kind: String, sz: Vector2) -> Vector2:
	var vp := get_viewport_rect().size if is_inside_tree() else Vector2(1920, 1080)
	var x := r.position.x
	if kind == "slot" and _tray_holder != null:
		x = _tray_holder.get_global_rect().position.x
	elif not _slot_buttons.is_empty():
		x = _slot_buttons[0].get_global_rect().position.x
	var y := clampf(r.get_center().y - sz.y * 0.5, 16.0, maxf(16.0, vp.y - sz.y - 16.0))
	return Vector2(clampf(x, 16.0, maxf(16.0, vp.x - sz.x - 16.0)), y)


func _hide_lupe(anchor: Control) -> void:
	if _lupe_for == anchor:
		_lupe_for = null
		_lupe.visible = false


func _refresh_lupe() -> void:
	if _lupe == null:
		return
	if not lupe_wanted() or _done:
		_lupe.visible = false
		_lupe_for = null
		return
	var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	if f != null and f in _slot_buttons:
		_show_lupe(f, "slot", _slot_buttons.find(f))
	elif f != null and f in _tray_buttons.values():
		_show_lupe(f, "card", symbols.find(str(f.name).trim_prefix("Card_")))


# ================================================================ layout / settings
## 100 %: the instruction is the line under the title (like the protocol puzzle), wrong note and hint stack
## across the notes width. 125 % / 150 %: the board keeps its fixed height, so the instruction moves into the
## notes and gives way to the wrong note / hint / success text (the board never jumps), wrong note and hint
## sit side by side. Called on open() and on Settings "text_scale".
func _apply_layout() -> void:
	var wide := is_wide()
	var target: Control = _notes_col if wide else _root_box
	if _instr.get_parent() != target:
		_instr.get_parent().remove_child(_instr)
		target.add_child(_instr)
		target.move_child(_instr, 0 if wide else 2)      # 2 = under the title row and its rule
	_notes_row.vertical = not wide
	_refresh_notes()
	_refresh_lupe()


func is_wide() -> bool:
	return Kit.text_scale() > 1.1


## Which note is on screen; at 125 % / 150 % the instruction only while nothing else needs the space.
func _refresh_notes() -> void:
	if _notes_row == null or _hint_box == null or _instr == null:
		return
	_notes_row.visible = _feedback.visible or _hint_box.visible
	_instr.visible = not is_wide() or not (_notes_row.visible or _done)
	if _tip != null:
		_tip.text = Kit.t("ui.c3p2.check.tip_pad" if Kit.last_input_pad else "ui.c3p2.check.tip_mouse")
		_tip.visible = not is_wide() and not _notes_row.visible and not _done


## The mouse / controller way of playing, said once under the board (the footer lists the keys).
func tip_text() -> String:
	return _tip.text if _tip != null and _tip.visible else ""


func instruction_shown() -> bool:
	return _instr != null and _instr.visible and _instr.is_visible_in_tree()


func _on_setting_changed(key: String, _value) -> void:
	match key:
		"text_scale":
			_apply_layout()
		"high_contrast":
			_refresh()


# ================================================================ open / state
func open(id: String) -> void:
	obj_id = id
	var p = Kit.call_svc("Story", "puzzle_for", [id], null)
	_puzzle = p if p is Dictionary and not p.is_empty() else Kit.puzzle_for_objective(id)
	var ds = _puzzle.get("display_symbols", DEFAULT_SYMBOLS)
	symbols = (ds as Array).duplicate() if ds is Array and ds.size() == SLOT_COUNT else DEFAULT_SYMBOLS.duplicate()
	slots = ["", "", "", ""]
	history.clear()
	armed = -1
	_fails = 0
	_done = false
	_marks_shown = 0
	_beat_token += 1
	_close_btn.text = Kit.t("ui.c3p2.check.close")
	_set_feedback("")
	_build_tray()
	_apply_layout()
	_refresh()
	open_modal()


func is_done() -> bool:
	return _done


func filled_count() -> int:
	return order.size()


func feedback_text() -> String:
	return _feedback.text if _feedback != null and _feedback.visible else ""


func hint_shown() -> bool:
	return _hint_box != null and _hint_box.visible


func success_shown() -> bool:
	return _success_box != null and _success_box.visible


## Rows whose matching marks are visible (0 … 4) — they appear one after the other after the solution.
func marks_shown() -> int:
	var n := 0
	for m in _row_marks:
		if m.visible:
			n += 1
	return n


func kordon_shown() -> bool:
	return _kordon != null and _kordon.visible


func _first_free() -> int:
	for i in slots.size():
		if str(slots[i]) == "":
			return i
	return -1


func _target_row() -> int:
	if armed >= 0 and armed < slots.size() and str(slots[armed]) == "":
		return armed
	return _first_free()


# ================================================================ actions
## Key N (1-based): the card at position N of the original tray order.
func place_key(n: int) -> bool:
	if n < 1 or n > symbols.size():
		return false
	return place(str(symbols[n - 1]))


## Lays the card into the chosen row, else into the next empty row from the top. False when it is already
## on the board or every row is taken.
func place(sym: String) -> bool:
	if _done or not (sym in symbols) or sym in slots:
		return false
	var i := _target_row()
	if i < 0:
		return false
	_lay(sym, i)
	return true


func _lay(sym: String, i: int) -> void:
	slots[i] = sym
	history.erase(sym)
	history.append(sym)
	armed = -1
	Kit.ui_sound("card")
	_set_feedback("")
	_refresh()
	if _slot_cards[i].is_inside_tree() and not Kit.reduced_motion():
		Kit.appear(_slot_cards[i], 0.14)
		Kit.appear(_slot_texts[i], 0.14)
	if _first_free() < 0:
		_check_btn.grab_focus.call_deferred()
	else:
		_focus_next_card()


## Chooses an empty row for the next card (click / accept on an empty row); again on the same row = forget.
func arm(i: int) -> bool:
	if _done or i < 0 or i >= slots.size() or str(slots[i]) != "":
		return false
	armed = -1 if armed == i else i
	Kit.ui_sound("move")
	_set_feedback("")
	_refresh()
	if armed >= 0:
		_focus_next_card()
	return true


## Takes the card of row i back to the tray (mouse click / accept on a filled row).
func take_back(i: int) -> bool:
	if _done or i < 0 or i >= slots.size() or str(slots[i]) == "":
		return false
	var sym := str(slots[i])
	slots[i] = ""
	history.erase(sym)
	Kit.ui_sound("back")
	_set_feedback("")
	_refresh()
	_focus_card(sym)
	return true


## Backspace / „Rückgängig“: takes back the card laid last.
func undo() -> bool:
	if _done or history.is_empty():
		return false
	var sym := str(history.pop_back())
	var i := slots.find(sym)
	if i >= 0:
		slots[i] = ""
	Kit.ui_sound("back")
	_set_feedback("")
	_refresh()
	_focus_card(sym)
	return true


## R / „Neu ordnen“: every card back to the tray.
func reset_order() -> bool:
	if _done or (history.is_empty() and armed < 0):
		return false
	slots = ["", "", "", ""]
	history.clear()
	armed = -1
	Kit.ui_sound("page")
	_set_feedback("")
	_refresh()
	_focus_next_card()
	return true


## Drag and drop (mouse): `from` = -1 for the tray, else the row the card is lifted from. An occupied target
## row sends its card back to the tray (from the tray) or swaps it into the source row (row to row).
func drop_card(sym: String, from: int, to: int) -> bool:
	if _done or to < 0 or to >= slots.size() or not (sym in symbols):
		return false
	if from >= 0:
		if from >= slots.size() or str(slots[from]) != sym:
			return false
		if from == to:
			return false
		var other := str(slots[to])
		slots[to] = sym
		slots[from] = other
		armed = -1
		Kit.ui_sound("card")
		_set_feedback("")
		_refresh()
		return true
	if sym in slots:
		return false
	var occupant := str(slots[to])
	if occupant != "":
		history.erase(occupant)
	_lay(sym, to)
	return true


## Enter / „Prüfen“. Returns the engine result ({} when nothing was submitted).
func submit() -> Dictionary:
	if _done:
		return {}
	if _first_free() >= 0:
		_set_feedback(Kit.t("ui.c3p2.check.incomplete"))
		Kit.ui_sound("tick")
		_focus_next_card()
		return {}
	var answer: Array = slots.duplicate()
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	if r == null or not ok:
		_set_feedback(Kit.t("ui.c3p2.check.error", {"error": _error_text(r)}))
		Kit.ui_sound("fail")
		return r if r is Dictionary else {"ok": false, "error": "no Story service"}
	var is_solved: bool = bool(r) if r is bool else bool((r as Dictionary).get("solved", false))
	if is_solved:
		_on_solved()
	else:
		_fails += 1
		Kit.ui_sound("fail")
		_set_feedback(Kit.t("ui.c3p2.check.wrong"))
		_nudge()
		_refresh()
	return r if r is Dictionary else {"ok": true, "solved": is_solved}


func _error_text(r) -> String:
	if r is Dictionary:
		var k := str(r.get("error_key", ""))
		if k != "" and Kit.has_key(k):
			return Kit.t(k)
		var e := str(r.get("error", ""))
		if e != "":
			return e
	return Kit.t("ui.common.unavailable")


func _on_solved() -> void:
	_done = true
	armed = -1
	_solved_at = Time.get_ticks_msec()
	_set_feedback("")
	_lupe.visible = false
	_refresh()
	Kit.ui_sound("stamp_thud")
	if not Kit.reduced_motion():
		Kit.appear(_success_box, 0.22)
	_close_btn.text = Kit.t("ui.c3p2.check.continue")
	_close_btn.grab_focus.call_deferred()
	solved_count += 1
	solved.emit(obj_id)
	_beat_token += 1
	var token := _beat_token
	if Kit.reduced_motion() or not is_inside_tree():
		for i in SLOT_COUNT:
			_reveal_mark(i, token)
		_reveal_kordon(token)
	else:
		for i in SLOT_COUNT:
			get_tree().create_timer(0.25 + MARK_STEP * i, true).timeout.connect(_reveal_mark.bind(i, token), CONNECT_ONE_SHOT)
		get_tree().create_timer(0.35 + MARK_STEP * SLOT_COUNT, true).timeout.connect(_reveal_kordon.bind(token), CONNECT_ONE_SHOT)
	if is_inside_tree():
		get_tree().create_timer(success_beat(), true).timeout.connect(_on_beat.bind(token), CONNECT_ONE_SHOT)


## One pair after the other: the red pencil on Alexei's paper, the shared words underlined on the entry,
## the leader turns into „=“.
func _reveal_mark(i: int, token: int) -> void:
	if token != _beat_token or not _done or i >= _row_marks.size():
		return
	_row_marks[i].visible = true
	_marks_shown = maxi(_marks_shown, i + 1)
	var sym := str(slots[i])
	if sym != "":
		_slot_texts[i].text = _card_bbcode(sym, true)
	_paper_cells[i].queue_redraw()
	if _row_marks[i].is_inside_tree() and not Kit.reduced_motion():
		Kit.appear(_row_marks[i], 0.2)
	Kit.ui_sound("tick")


func _reveal_kordon(token: int) -> void:
	if token != _beat_token or not _done:
		return
	_tray_col.visible = false
	_kordon.visible = true
	if _kordon.is_inside_tree() and not Kit.reduced_motion():
		Kit.appear(_kordon, 0.3)


## Seconds the solved modal stays open by itself: a reading beat for the marks and the success text, capped
## at SUCCESS_BEAT_MAX; any confirm (Enter / Space / Esc / A / B / „Weiter“) closes it earlier.
func success_beat() -> float:
	return clampf(2.0 + Kit.t("ui.c3p2.check.success").length() * 0.03, 3.0, SUCCESS_BEAT_MAX)


func _on_beat(token: int) -> void:
	if token == _beat_token and _done and is_open:
		close()


func _set_feedback(text: String) -> void:
	if _feedback == null:
		return
	_feedback.text = text
	_feedback.visible = text != ""
	_refresh_notes()


func _nudge() -> void:
	if Kit.reduced_motion() or _slot_col == null or not _slot_col.is_inside_tree():
		return
	var base := _slot_col.position.x
	var tw := _slot_col.create_tween()
	for dx in [6, -6, 3, 0]:
		tw.tween_property(_slot_col, "position:x", base + float(dx), 0.05)


func _hint_visible() -> bool:
	if _done:
		return false
	var mode := int(Kit.setting("puzzle_hints", 1))
	if mode <= 0:
		return false
	if mode >= 2:
		return true
	var r = Kit.call_svc("Story", "puzzle_hint_available", [obj_id], null)
	if r is bool:
		return r
	if r is Dictionary:
		return bool(r.get("available", r.get("hint", false)))
	return _fails >= int(_puzzle.get("hint_after_attempts", 2))


func _refresh() -> void:
	if _slot_buttons.is_empty():
		return
	var hc := Kit.high_contrast()
	for i in _slot_buttons.size():
		var sym := str(slots[i])
		var filled := sym != ""
		var b := _slot_buttons[i]
		_slot_cards[i].visible = filled
		_slot_texts[i].visible = filled
		_slot_captions[i].visible = not filled
		_slot_armed[i].visible = not _done and (armed == i or _drop_hover == i)
		if filled:
			_slot_cards[i].texture = Kit.tex(_card_file(sym))
			_slot_texts[i].text = _card_bbcode(sym, _done and i < _marks_shown)
			b.tooltip_text = Kit.t("ui.c3p2.check.slot_filled", {"n": i + 1, "name": card_name(sym)})
		else:
			_slot_captions[i].text = (Kit.t("ui.c3p2.check.slot_armed") if armed == i
				else Kit.t("ui.c3p2.check.slot", {"n": i + 1})).to_upper().replace("ß", "SS")
			_slot_captions[i].add_theme_color_override("font_color", Kit.C_AMBER if armed == i else Kit.C_TEXT_DIM)
			b.tooltip_text = Kit.t("ui.c3p2.check.slot_tip", {"n": i + 1})
		var can := not _done
		if not can and b.has_focus():
			_focus_next_card.call_deferred()
		b.focus_mode = Control.FOCUS_ALL if can else Control.FOCUS_NONE
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if can else Control.CURSOR_ARROW
	for sym in _tray_buttons:
		var b: Button = _tray_buttons[sym]
		var used: bool = sym in slots
		var avail := not used and not _done
		if not avail and b.has_focus():
			_focus_next_card.call_deferred()
		b.disabled = not avail
		b.focus_mode = Control.FOCUS_ALL if avail else Control.FOCUS_NONE
		b.modulate = Color(1, 1, 1, (0.34 if hc else 0.22)) if used else Color.WHITE
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if avail else Control.CURSOR_ARROW
	for i in _paper_cells.size():
		_row_marks[i].visible = _done and i < _marks_shown
		_paper_cells[i].queue_redraw()
	_tray_col.visible = not (_done and kordon_shown())
	if not _done:
		_kordon.visible = false
	var n := filled_count()
	if _done:
		_state_label.text = Kit.t("ui.c3p2.check.state_done")
	elif armed >= 0:
		_state_label.text = Kit.t("ui.c3p2.check.state_armed", {"n": armed + 1})
	elif n == SLOT_COUNT:
		_state_label.text = Kit.t("ui.c3p2.check.state_full")
	else:
		_state_label.text = Kit.t("ui.c3p2.check.state", {"n": n, "total": SLOT_COUNT})
	_state_label.add_theme_color_override("font_color", Kit.C_AMBER if armed >= 0 and not _done else Kit.C_TEXT_DIM)
	_undo_btn.disabled = _done or history.is_empty()
	_reset_btn.disabled = _done or (history.is_empty() and armed < 0)
	_check_btn.disabled = _done
	_hint_box.visible = _hint_visible()
	_success_box.visible = _done
	_refresh_notes()


func _hover_focus(b: Button) -> void:
	if b.focus_mode != Control.FOCUS_NONE and is_open and not _dragging:
		b.grab_focus()


func _focus_card(sym: String) -> void:
	var b: Button = _tray_buttons.get(sym)
	if b != null and b.focus_mode != Control.FOCUS_NONE and b.is_inside_tree():
		b.grab_focus.call_deferred()
	else:
		_focus_next_card()


func _focus_next_card() -> void:
	if not is_inside_tree():
		return
	if _done:
		_close_btn.grab_focus.call_deferred()
		return
	for sym in symbols:
		var b: Button = _tray_buttons.get(str(sym))
		if b != null and b.focus_mode != Control.FOCUS_NONE:
			b.grab_focus.call_deferred()
			return
	_check_btn.grab_focus.call_deferred()


func focus_default() -> void:
	_focus_next_card()


func _on_open() -> void:
	Kit.ui_sound("paper")
	_refresh()


func _on_close() -> void:
	_beat_token += 1
	_lupe.visible = false
	_lupe_for = null


# ================================================================ mouse: click + drag and drop
func _recent_drag() -> bool:
	return _dragging or Time.get_ticks_msec() - _drag_end_ms < 150


func _on_card_pressed(sym: String) -> void:
	if not _recent_drag():
		place(sym)


func _on_slot_pressed(i: int) -> void:
	if _recent_drag():
		return
	if str(slots[i]) != "":
		take_back(i)
	else:
		arm(i)


func _drag_from_tray(at: Vector2, sym: String, src: Control) -> Variant:
	if _done or sym in slots:
		return null
	_dragging = true
	_set_preview(src, sym, at)
	return {"aoe_c3p2_card": sym, "from": -1}


func _drag_from_slot(at: Vector2, i: int, src: Control) -> Variant:
	if _done or str(slots[i]) == "":
		return null
	_dragging = true
	_set_preview(src, str(slots[i]), at)
	return {"aoe_c3p2_card": str(slots[i]), "from": i}


## The preview exists only inside a real drag (the viewport refuses it otherwise).
func _set_preview(src: Control, sym: String, at: Vector2) -> void:
	if src.is_inside_tree() and src.get_viewport().gui_is_dragging():
		src.set_drag_preview(_drag_preview(sym, at))


func _drag_preview(sym: String, at: Vector2) -> Control:
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cs := _card_size()
	var c := Control.new()
	c.position = -at
	c.size = cs
	c.modulate = Color(1, 1, 1, 0.9)
	c.rotation = deg_to_rad(-1.5)
	holder.add_child(c)
	var shadow := ColorRect.new()
	shadow.color = Color(0, 0, 0, 0.4)
	shadow.position = Vector2(9, 9)
	shadow.size = cs
	c.add_child(shadow)
	var img := Kit.pixel_image(Kit.tex(_card_file(sym)), PX)
	img.stretch_mode = TextureRect.STRETCH_SCALE
	img.size = cs
	c.add_child(img)
	var txt := _card_text_label(cs)
	txt.text = _card_bbcode(sym, false)
	c.add_child(txt)
	return holder


func _is_card_data(data) -> bool:
	return data is Dictionary and data.has("aoe_c3p2_card") and data.has("from")


func _can_drop_slot(_at: Vector2, data, i: int) -> bool:
	var ok := not _done and _is_card_data(data) and int(data["from"]) != i
	_set_drop_hover(i if ok else -1)
	return ok


func _drop_on_slot(_at: Vector2, data, i: int) -> void:
	_set_drop_hover(-1)
	if _is_card_data(data):
		drop_card(str(data["aoe_c3p2_card"]), int(data["from"]), i)


func _can_drop_tray(_at: Vector2, data) -> bool:
	_set_drop_hover(-1)
	return not _done and _is_card_data(data) and int(data["from"]) >= 0


func _drop_on_tray(_at: Vector2, data) -> void:
	if _is_card_data(data) and int(data["from"]) >= 0:
		take_back(int(data["from"]))


func _set_drop_hover(i: int) -> void:
	if _drop_hover == i:
		return
	_drop_hover = i
	for k in _slot_armed.size():
		_slot_armed[k].visible = not _done and (armed == k or _drop_hover == k)


func _notification(what: int) -> void:
	if what == NOTIFICATION_DRAG_END:
		if _dragging:
			_drag_end_ms = Time.get_ticks_msec()
		_dragging = false
		_set_drop_hover(-1)


# ================================================================ input (called by UIRoot before the GUI)
func modal_input(event: InputEvent) -> bool:
	if _done:
		return _done_input(event)
	if event is InputEventJoypadButton:
		return _pad_input(event as InputEventJoypadButton)
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return false
	var ke := event as InputEventKey
	if ke.ctrl_pressed or ke.alt_pressed or ke.meta_pressed:
		return false
	var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
	if k >= KEY_1 and k <= KEY_9:
		place_key(int(k - KEY_1) + 1)
		return true
	if k >= KEY_KP_1 and k <= KEY_KP_9:
		place_key(int(k - KEY_KP_1) + 1)
		return true
	if k == KEY_BACKSPACE:          # also bound to "cancel": consume it before UIRoot closes the modal
		undo()
		return true
	if k == KEY_R:
		reset_order()
		return true
	if k == KEY_ENTER or k == KEY_KP_ENTER:
		var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
		if f != null and f in [_undo_btn, _reset_btn, _close_btn]:
			return false                # Enter on another action button presses that button
		submit()
		return true
	return false


## Controller: the game binds pad A to "interact"/"advance", not to ui_accept (Settings.PAD), so A presses the
## focused card / row / button here; X takes back the last entry, Y checks. B stays "cancel" (UIRoot ->
## handle_cancel: first forgets a chosen row, then closes). D-pad / stick focus moves through the GUI.
func _pad_input(jb: InputEventJoypadButton) -> bool:
	if not jb.pressed:
		return jb.button_index in [JOY_BUTTON_A, JOY_BUTTON_X, JOY_BUTTON_Y]
	match jb.button_index:
		JOY_BUTTON_A:
			var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
			if f is BaseButton and is_ancestor_of(f) and not (f as BaseButton).disabled:
				(f as BaseButton).pressed.emit()
			return true
		JOY_BUTTON_X:
			undo()
			return true
		JOY_BUTTON_Y:
			submit()
			return true
	return false


## After success: confirm/cancel (after a short guard) closes; everything else is swallowed.
func _done_input(event: InputEvent) -> bool:
	var confirm := false
	if event is InputEventKey and event.pressed and not event.echo:
		var ke := event as InputEventKey
		var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
		confirm = k in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_ESCAPE, KEY_BACKSPACE]
	elif event is InputEventJoypadButton and event.pressed:
		confirm = (event as InputEventJoypadButton).button_index in [JOY_BUTTON_A, JOY_BUTTON_B]
	elif event is InputEventMouseButton:
		return false                    # the „Weiter“ button stays clickable
	if not confirm:
		return event is InputEventKey or event is InputEventJoypadButton
	if Time.get_ticks_msec() - _solved_at >= SUCCESS_GUARD_MS and is_open:
		close()
	return true


## Esc / B: first forget a chosen row, then close.
func handle_cancel() -> bool:
	if _done and Time.get_ticks_msec() - _solved_at < SUCCESS_GUARD_MS:
		return true
	if not _done and armed >= 0:
		armed = -1
		Kit.ui_sound("back")
		_refresh()
		return true
	return super.handle_cancel()


# ================================================================ accessibility report (tests)
## Text colour / background pairs of everything this board draws itself (WCAG contrast is checked by
## tests/test_c3p2_puzzle_ui.gd against the real art colours from the board json).
func contrast_pairs() -> Array:
	var surf: Dictionary = _meta.get("surfaces", {}) if _meta.get("surfaces") is Dictionary else {}
	var card_bg := Color(str(surf.get("card_text", "#e6dec2")))
	var slot_bg := Color(str(surf.get("slot", "#06151d")))
	return [
		{"what": "entry text on the index card", "fg": INK, "bg": card_bg},
		{"what": "shared words after the solution", "fg": PENCIL_HC if Kit.high_contrast() else PENCIL, "bg": card_bg},
		{"what": "caption of an empty row", "fg": Kit.C_TEXT_DIM, "bg": slot_bg},
		{"what": "caption of the chosen row", "fg": Kit.C_AMBER, "bg": slot_bg},
		{"what": "Lupe kicker", "fg": _lupe_kicker_color(), "bg": PAPER},
		{"what": "Lupe text", "fg": INK, "bg": PAPER},
	]
