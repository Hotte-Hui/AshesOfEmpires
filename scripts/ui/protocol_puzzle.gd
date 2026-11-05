extends "res://scripts/ui/ui_modal.gd"
## Protocol puzzle „Sitzordnung und Dolmetscherprotokoll" (pz_c3_protocol / objective c3b_solve_protocol,
## documentation/C3_DESIGN.md §2.7). Konrad spreads the seating plan of the Großer Saal (left) and Elena's
## booth log of Kabine 2 (right) on the table of the Protokollbüro and lays the four name cards in the order
## of the speeches on agenda item 4 „Anlage C". The log names only time and microphone; the plan prints
## only the microphone numbers 1, 2 and 12 plus the legend (clockwise from the chair) — the player counts.
##
## Registered by data/chapters/c3.json (puzzles.c3b_solve_protocol); ChapterExt.puzzle_ui instances this
## scene once under UIRoot (modal stack), sets `ui_root`, and Game calls open(obj_id) and awaits `closed`.
## Works stand-alone (tests) as well: then open()/close() just show/hide.
##
## Input: keys 1–4 put the card at position N of the ORIGINAL tray order (`symbols`, from
## display_symbols) into the next free slot · Backspace takes back the card placed last · R or
## „Neu ordnen" clears · Enter or „Prüfen" submits Story.solve_puzzle(obj_id, [ids in slot order]) — only
## with all four slots filled, otherwise the „incomplete" note (no attempt) · mouse: click a tray card to
## lay it, click a filled slot to take that card back · controller: ui_left/right/up/down move the focus,
## ui_accept lays/takes back/presses, ui_cancel closes · Esc closes (handle_cancel).
## Wrong answers cost nothing: neutral note, the cards stay for editing, the engine counts the attempt; the
## hint appears per Settings.puzzle_hints (0 off · 1 after Story.puzzle_hint_available · 2 at once).
## Success: stamp + success text, `solved(obj_id)` once, the modal closes after a reading beat (see
## success_beat(), at most SUCCESS_BEAT_MAX seconds) or earlier on confirm, so Game's `await closed` returns.
## Cards are told apart by name AND shape glyph (circle/square/triangle/diamond) — never by colour.
## Pixel art (assets/ui/puzzle/c3_*, tools/pixelgen/gen_ui_c3.py) is drawn 1:1 and shown at exactly x3.

signal solved(obj_id: String)

const PX := 3
const ART := "res://assets/ui/puzzle/"
const BOARD_JSON := "res://assets/ui/puzzle/c3_protocol_board.json"
const DEFAULT_SYMBOLS := ["soviet", "secretariat", "chair", "reich"]
const SLOT_COUNT := 4
const INK := Color("1a1c2a")
const INK_PEN := Color("2e3248")
const BLUE_INK := Color("2b3c50")
const BLUE_INK_L := Color("3e546b")
## Swallow confirm/cancel presses this long after success, so a key still held for „Prüfen" cannot skip it.
const SUCCESS_GUARD_MS := 600
## Longest reading beat before the solved modal closes by itself. The real-input driver
## (scripts/core/inputplay.gd) waits 8 s for `closed` after the correct order — stay well inside that.
const SUCCESS_BEAT_MAX := 5.5

var suppress_toasts := true
var obj_id := ""
## Tray order (display_symbols of the puzzle). Key N always means symbols[N - 1].
var symbols: Array = DEFAULT_SYMBOLS.duplicate()
## Slot contents left to right; "" = empty.
var slots: Array = ["", "", "", ""]
## Ids of the cards on the board in the order they were laid (Backspace takes back the last one).
var history: Array = []
## Read-only: the laid cards in slot order (empty slots skipped).
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
var _fails := 0
var _done := false
var _solved_at := 0
var _beat_token := 0
var _last_feedback := ""
var _panel: PanelContainer
var _plan_holder: Control
var _log_holder: Control
var _slot_holder: Control
var _slot_row: HBoxContainer
var _slot_buttons: Array[Button] = []
var _slot_cards: Array[TextureRect] = []
var _slot_names: Array[Label] = []
var _slot_captions: Array[Label] = []
var _tray: HBoxContainer
var _tray_buttons: Dictionary = {}
var _tray_built: Array = []
var _state_label: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _success_box: PanelContainer
var _success_label: Label
var _undo_btn: Button
var _reset_btn: Button
var _check_btn: Button
var _close_btn: Button
var _controls: Control
var _col_b: VBoxContainer
var _actions: GridContainer
var _footer: HBoxContainer


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	var meta = Kit.json(BOARD_JSON)
	_meta = meta if meta is Dictionary else {}
	add_child(Kit.dimmer(0.78))
	_panel = Kit.panel()
	Kit.full_rect(_panel)
	_panel.offset_left = 28
	_panel.offset_right = -28
	_panel.offset_top = 14
	_panel.offset_bottom = -14
	add_child(_panel)
	var root := Kit.vbox(0)
	_panel.add_child(root)
	# --- header: title + subtitle on one line, copper rule, instruction
	var head := Kit.hbox(28)
	root.add_child(head)
	var title := Kit.label(Kit.t("ui.c3.protocol.title"), "HeadingLabel")
	head.add_child(title)
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	push.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(push)
	var sub := Kit.label(Kit.t("ui.c3.protocol.subtitle"), "DimLabel")
	sub.size_flags_vertical = Control.SIZE_SHRINK_END
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(sub)
	root.add_child(HSeparator.new())
	var instr := Kit.wrap_label(Kit.t("ui.c3.protocol.instruction"), "BodyLabel")
	Kit.scalable(instr, 26)
	root.add_child(instr)
	root.add_child(_gap(12))
	# --- play area: documents + order row + tray (left), notes (right)
	var play := Kit.hbox(36)
	root.add_child(play)
	var col_a := Kit.vbox(0)
	play.add_child(col_a)
	var docs := Kit.hbox(24)
	col_a.add_child(docs)
	_plan_holder = _build_plan()
	docs.add_child(_plan_holder)
	_log_holder = _build_log()
	docs.add_child(_log_holder)
	col_a.add_child(_gap(24))
	_build_slots(col_a)
	col_a.add_child(_gap(24))
	_tray = Kit.hbox(_card_gap())
	col_a.add_child(_tray)
	_col_b = Kit.vbox(16)
	_col_b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	play.add_child(_col_b)
	_col_b.add_child(_build_notes())
	_actions = GridContainer.new()
	_actions.columns = 2
	_actions.add_theme_constant_override("h_separation", 16)
	_actions.add_theme_constant_override("v_separation", 14)
	_actions.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_col_b.add_child(_actions)
	var actions := _actions
	_undo_btn = Kit.button(Kit.t("ui.c3.protocol.undo"))
	_undo_btn.pressed.connect(undo)
	_reset_btn = Kit.button(Kit.t("ui.c3.protocol.reset"))
	_reset_btn.pressed.connect(reset_order)
	_check_btn = Kit.button(Kit.t("ui.c3.protocol.check"))
	_check_btn.pressed.connect(submit)
	_close_btn = Kit.button(Kit.t("ui.c3.protocol.close"))
	_close_btn.pressed.connect(close)
	for b in [_undo_btn, _reset_btn, _check_btn, _close_btn]:
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		actions.add_child(b)
	root.add_child(_gap(14))
	# --- footer: input hints (+ the actions when the text is scaled up, see _apply_layout)
	_footer = Kit.hbox(24)
	root.add_child(_footer)
	_controls = Kit.controls_row([["1–4", Kit.t("ui.c3.protocol.hint_place")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.c3.protocol.hint_undo")],
		["R", Kit.t("ui.c3.protocol.hint_reorder")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.c3.protocol.hint_check")],
		[Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]])
	_controls.tooltip_text = Kit.t("ui.c3.protocol.controls")
	_controls.mouse_filter = Control.MOUSE_FILTER_PASS
	_controls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_controls.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_footer.add_child(_controls)
	_build_tray()
	_apply_layout()
	_refresh()
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)


## Default (100 %): the four actions sit in a 2x2 grid under the notes column. With enlarged text (125 %
## and 150 %) the notes need the whole column (wrong-answer note + hint), so the actions move into the
## footer row. Called on open() and again whenever Settings "text_scale" changes (UIRoot rescales the labels).
func _apply_layout() -> void:
	var wide := Kit.text_scale() > 1.1
	var target: Control = _footer if wide else _col_b
	if _actions.get_parent() != target:
		_actions.get_parent().remove_child(_actions)
		target.add_child(_actions)
	_actions.columns = 4 if wide else 2
	_controls.alignment = BoxContainer.ALIGNMENT_BEGIN if wide else BoxContainer.ALIGNMENT_CENTER
	for b in [_undo_btn, _reset_btn, _check_btn, _close_btn]:
		b.custom_minimum_size.x = 196 if wide else 0
		b.size_flags_horizontal = Control.SIZE_FILL if wide else Control.SIZE_EXPAND_FILL


func _on_setting_changed(key: String, _value) -> void:
	if key == "text_scale":
		_apply_layout()


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


func _size_of(section: String, fallback: Vector2i) -> Vector2:
	var s = _m(section, "size", [fallback.x, fallback.y])
	return Vector2(int(s[0]), int(s[1])) * PX


func _card_size() -> Vector2:
	return _size_of("card", Vector2i(98, 28))


func _card_gap() -> int:
	# the four cards span exactly the width of the two documents (24 px between the sheets)
	var docs_w := _size_of("plan", Vector2i(232, 160)).x + 24 + _size_of("log", Vector2i(168, 160)).x
	return maxi(8, int((docs_w - 4 * _card_size().x) / 3))


## A 1:1 pixel image shown at exactly x3 (nearest), with a soft drop shadow like the inspect view.
func _sheet(path: String, size: Vector2) -> Control:
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.custom_minimum_size = size
	var shadow := ColorRect.new()
	shadow.color = Color(0, 0, 0, 0.42)
	shadow.position = Vector2(9, 9)
	shadow.size = size
	shadow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(shadow)
	var img := Kit.pixel_image(Kit.tex(path), PX)
	img.stretch_mode = TextureRect.STRETCH_SCALE
	img.position = Vector2.ZERO
	img.size = size
	holder.add_child(img)
	return holder


func _overlay(parent: Control, text: String, r: Rect2, font: String, size: int, color: Color,
		align := HORIZONTAL_ALIGNMENT_LEFT, wrap := false) -> Label:
	var l := Kit.label(text, "", size, color)
	l.add_theme_font_override("font", Kit.font(font))
	l.add_theme_constant_override("line_spacing", -2)
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.position = r.position
	l.size = r.size
	l.clip_text = false
	parent.add_child(l)
	return l


func _build_plan() -> Control:
	var size := _size_of("plan", Vector2i(232, 160))
	var h := _sheet(ART + str(_m("plan", "file", "c3_plan.png")), size)
	var labels: Dictionary = _m("plan", "labels", {})
	var specs := {
		"title": ["ui.c3.protocol.plan.title", "fv_heading", 25, BLUE_INK, HORIZONTAL_ALIGNMENT_LEFT],
		"subtitle": ["ui.c3.protocol.plan.subtitle", "fv_button", 16, BLUE_INK_L, HORIZONTAL_ALIGNMENT_RIGHT],
		"chair": ["ui.c3.protocol.plan.chair", "fv_button", 17, BLUE_INK, HORIZONTAL_ALIGNMENT_LEFT],
		"soviet": ["ui.c3.protocol.plan.soviet", "fv_button", 17, BLUE_INK, HORIZONTAL_ALIGNMENT_LEFT],
		"reich": ["ui.c3.protocol.plan.reich", "fv_button", 17, BLUE_INK, HORIZONTAL_ALIGNMENT_RIGHT],
		"observer_se": ["ui.c3.protocol.plan.observer_se", "fv_button", 16, BLUE_INK, HORIZONTAL_ALIGNMENT_LEFT],
		"observer_ch": ["ui.c3.protocol.plan.observer_ch", "fv_button", 16, BLUE_INK, HORIZONTAL_ALIGNMENT_RIGHT],
		"secretariat": ["ui.c3.protocol.plan.secretariat", "fv_button", 17, BLUE_INK, HORIZONTAL_ALIGNMENT_CENTER],
		"booths": ["ui.c3.protocol.plan.booths", "fv_button", 15, BLUE_INK_L, HORIZONTAL_ALIGNMENT_CENTER],
		"legend": ["ui.c3.protocol.legend", "fv_button", 16, BLUE_INK, HORIZONTAL_ALIGNMENT_LEFT],
	}
	for k in specs:
		if not labels.has(k):
			continue
		var sp: Array = specs[k]
		var r := _rect(labels[k])
		var wrap: bool = k in ["soviet", "observer_se", "observer_ch"]
		if k == "title" or k == "subtitle":
			r = r.grow_individual(0, 6, 0, 6)
		_overlay(h, Kit.t(sp[0]).to_upper(), r, sp[1], sp[2], sp[3], sp[4], wrap).name = "Plan_" + k
	# the only printed numbers: 1, 2, 12 inside their rings
	var tags: Dictionary = _m("plan", "tags", {})
	for t in tags:
		var r := _rect(tags[t]).grow_individual(0, -1, 0, 1)
		var l := _overlay(h, str(t), r, "fv_heading", 18, INK, HORIZONTAL_ALIGNMENT_CENTER)
		l.name = "Mic_" + str(t)
	return h


func _build_log() -> Control:
	var size := _size_of("log", Vector2i(168, 160))
	var h := _sheet(ART + str(_m("log", "file", "c3_log.png")), size)
	var title := _rect(_m("log", "title", [38, 4, 112, 11]))
	_overlay(h, Kit.t("ui.c3.protocol.log_title").to_upper(), title, "fv_button", 18, BLUE_INK).name = "LogTitle"
	var agenda := _rect(_m("log", "agenda", [22, 17, 138, 9]))
	_overlay(h, Kit.t("ui.c3.protocol.log.agenda"), agenda, "fv_type_bold", 17, INK).name = "LogAgenda"
	var cols: Dictionary = _m("log", "cols", {"time": 22, "mic": 46, "channel": 60, "remark": 30, "note": 30, "right": 160})
	var head := _rect(_m("log", "head", [22, 29, 138, 8]))
	for k in ["time", "mic", "channel"]:
		var x := float(cols.get(k, 22)) * PX
		var r := Rect2(x, head.position.y, size.x - x - 24, head.size.y)
		_overlay(h, Kit.t("ui.c3.protocol.log.col." + k).to_upper(), r, "fv_button", 14, BLUE_INK_L).name = "LogHead_" + k
	# rows: [{entry, kind (a time/mic/channel · b remark · n note), y}] at a fixed pitch of 8 art px
	var rows: Array = _m("log", "rows", [])
	var pitch := float(_m("log", "pitch", 8)) * PX
	var type_font := Kit.font("fv_type")
	var right := float(cols.get("right", 160)) * PX
	var i := 0
	while i < rows.size():
		var row: Dictionary = rows[i]
		var e := int(row.get("entry", 1))
		var kind := str(row.get("kind", "a"))
		var y := float(row.get("y", 0)) * PX
		if kind == "a":
			for k in ["time", "mic", "channel"]:
				var x := float(cols.get(k, 22)) * PX
				_typed(h, Kit.t("ui.c3.protocol.log.r%d.%s" % [e, k]), Vector2(x, y), right - x, pitch, 1,
					type_font).name = "Log_r%d_%s" % [e, k]
			i += 1
		elif kind == "b":
			var n := 1
			while i + n < rows.size() and int(rows[i + n].get("entry", 0)) == e and str(rows[i + n].get("kind", "")) == "b":
				n += 1
			var x := float(cols.get("remark", 30)) * PX
			_typed(h, Kit.t("ui.c3.protocol.log.r%d.remark" % e), Vector2(x, y), right - x, pitch, n,
				type_font).name = "Log_r%d_remark" % e
			i += n
		else:
			var x := float(cols.get("note", 30)) * PX
			var note := _overlay(h, Kit.t("ui.c3.protocol.log.note"), Rect2(x + 4, y + 1, right - x, pitch),
				"fv_serif_bold_italic", 19, INK_PEN)
			note.name = "Log_note"
			note.pivot_offset = Vector2(0, note.size.y * 0.5)
			note.rotation = deg_to_rad(-1.0)
			i += 1
	var ini := _overlay(h, Kit.t("ui.c3.protocol.log.initials"), Rect2(size.x - 120, size.y - 46, 96, 30),
		"fv_serif_bold_italic", 22, INK_PEN, HORIZONTAL_ALIGNMENT_RIGHT)
	ini.name = "LogInitials"
	ini.rotation = deg_to_rad(-3.0)
	return h


## Typed text sitting on the ruled lines: baseline 2 px above the rule of each 8-px row, `lines` rows tall.
func _typed(parent: Control, text: String, pos: Vector2, width: float, pitch: float, lines: int, font: Font) -> Label:
	var fs := 20
	var l := Kit.label(text, "", fs, INK)
	l.add_theme_font_override("font", font)
	var fh := font.get_height(fs)
	l.add_theme_constant_override("line_spacing", int(pitch - fh))
	if lines > 1:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.max_lines_visible = lines
	var ascent := font.get_ascent(fs)
	var rule := pitch - PX                                    # the rule is the last art row of the pitch
	l.position = Vector2(pos.x, pos.y + rule - 2 - ascent)
	l.size = Vector2(width, fh + (lines - 1) * pitch)
	parent.add_child(l)
	return l


func _build_slots(parent: Control) -> void:
	var cs := _card_size()
	var gap := _card_gap()
	_slot_holder = Control.new()
	_slot_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_slot_holder.custom_minimum_size = Vector2(cs.x * SLOT_COUNT + gap * (SLOT_COUNT - 1), cs.y)
	parent.add_child(_slot_holder)
	_slot_row = Kit.hbox(0)
	_slot_holder.add_child(_slot_row)
	var arrow := Kit.tex(ART + str(_m("seq_arrow", "file", "c3_seq_arrow.png")))
	for i in SLOT_COUNT:
		if i > 0:
			var a := Control.new()
			a.mouse_filter = Control.MOUSE_FILTER_IGNORE
			a.custom_minimum_size = Vector2(gap, cs.y)
			var ar := Kit.pixel_image(arrow, PX)
			ar.stretch_mode = TextureRect.STRETCH_SCALE
			if arrow != null:
				ar.size = arrow.get_size() * PX
				ar.position = Vector2(floorf((gap - ar.size.x) * 0.5), floorf((cs.y - ar.size.y) * 0.5))
			a.add_child(ar)
			_slot_row.add_child(a)
		var b := Kit.button("", "CardButton")
		b.name = "Slot%d" % (i + 1)
		b.custom_minimum_size = cs
		b.pressed.connect(take_back.bind(i))
		b.mouse_entered.connect(_hover_focus.bind(b))
		var frame := Kit.pixel_image(Kit.tex(ART + str(_m("slot", "file", "c3_slot.png"))), PX)
		frame.stretch_mode = TextureRect.STRETCH_SCALE
		frame.size = cs
		b.add_child(frame)
		var cap := Kit.label(Kit.t("ui.c3.protocol.slot", {"n": i + 1}).to_upper(), "KickerLabel", 21, Kit.C_TEXT_DIM)
		cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cap.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		cap.size = cs
		b.add_child(cap)
		var card := Kit.pixel_image(null, PX)
		card.stretch_mode = TextureRect.STRETCH_SCALE
		card.size = cs
		card.visible = false
		b.add_child(card)
		var nm := _card_name_label(cs)
		nm.visible = false
		b.add_child(nm)
		_add_focus_frame(b)
		b.add_child(_ordinal_chip(str(i + 1)))
		_slot_row.add_child(b)
		_slot_buttons.append(b)
		_slot_cards.append(card)
		_slot_names.append(nm)
		_slot_captions.append(cap)


## The name on a plate: typewriter capitals of the secretariat, two lines at most.
func _card_name_label(cs: Vector2) -> Label:
	var tr := _rect(_m("card", "text", [26, 5, 69, 20]))
	if tr.size == Vector2.ZERO:
		tr = Rect2(81, 15, cs.x - 93, 60)
	var l := Kit.label("", "", 20, INK)
	l.add_theme_font_override("font", Kit.font("fv_type_bold"))
	l.add_theme_constant_override("line_spacing", 0)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.max_lines_visible = 2
	l.position = tr.position
	l.size = tr.size
	return l


## Small tab at the top-left corner of a slot: the ordinal of the speech (not a key).
func _ordinal_chip(text: String) -> Control:
	var chip := Kit.panel("PlatePanel")
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_theme_stylebox_override("panel", _plate_small())
	var l := Kit.label(text + ".", "KickerLabel", 19)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	chip.add_child(l)
	chip.position = Vector2(-12, -15)
	chip.name = "Ordinal"
	return chip


func _plate_small() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/plate.png")
	st.set_texture_margin(SIDE_LEFT, 15)
	st.set_texture_margin(SIDE_TOP, 9)
	st.set_texture_margin(SIDE_RIGHT, 9)
	st.set_texture_margin(SIDE_BOTTOM, 9)
	st.set_content_margin(SIDE_LEFT, 15)
	st.set_content_margin(SIDE_TOP, 1)
	st.set_content_margin(SIDE_RIGHT, 8)
	st.set_content_margin(SIDE_BOTTOM, 1)
	return st


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


func _build_tray() -> void:
	if _tray_built == symbols and _tray.get_child_count() == symbols.size():
		return
	for c in _tray.get_children():
		_tray.remove_child(c)
		c.queue_free()
	_tray_buttons.clear()
	_tray_built = symbols.duplicate()
	var cs := _card_size()
	var i := 0
	for sym in symbols:
		i += 1
		var b := Kit.button("", "CardButton")
		b.name = "Card_" + str(sym)
		b.custom_minimum_size = cs
		b.tooltip_text = Kit.t("ui.c3.protocol.card_tip", {"name": card_name(str(sym))})
		b.pressed.connect(place.bind(str(sym)))
		b.mouse_entered.connect(_hover_focus.bind(b))
		var img := Kit.pixel_image(Kit.tex(_card_file(str(sym))), PX)
		img.stretch_mode = TextureRect.STRETCH_SCALE
		img.size = cs
		b.add_child(img)
		var nm := _card_name_label(cs)
		nm.text = card_name(str(sym))
		b.add_child(nm)
		_add_focus_frame(b)
		var chip := Kit.panel("KeyChipPanel")
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var kl := Kit.label(Kit.key_name(KEY_1 + i - 1), "KeyHintLabel")
		kl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		kl.custom_minimum_size.x = 12
		chip.add_child(kl)
		chip.position = Vector2(-12, -15)
		chip.name = "Key"
		b.add_child(chip)
		_tray.add_child(b)
		_tray_buttons[str(sym)] = b


func _card_file(sym: String) -> String:
	var files = _m("card", "files", {})
	if files is Dictionary and files.has(sym):
		return ART + str(files[sym])
	return ART + "c3_card_%s.png" % sym


func card_name(sym: String) -> String:
	return Kit.t("ui.c3.protocol.card." + sym)


func _build_notes() -> Control:
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.focus_mode = Control.FOCUS_NONE
	scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	var v := Kit.vbox(16)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(v)
	var kick := Kit.label(Kit.t("ui.c3.protocol.notes").to_upper(), "KickerLabel")
	v.add_child(kick)
	_state_label = Kit.label("", "DimLabel")
	v.add_child(_state_label)
	var sep := HSeparator.new()
	sep.theme_type_variation = "FaintSeparator"
	v.add_child(sep)
	_feedback = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_feedback, 24)
	v.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	var hh := Kit.hbox(14)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hh.add_child(hic)
	_hint_label = Kit.wrap_label(Kit.t("ui.c3.protocol.hint"), "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 22)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	v.add_child(_hint_box)
	_success_box = Kit.panel("PaperCardPanel")
	_success_box.add_theme_stylebox_override("panel", _paper_box())
	var sv := Kit.vbox(12)
	_success_box.add_child(sv)
	sv.add_child(_make_stamp(Kit.t("ui.c3.protocol.stamp").to_upper()))
	_success_label = Kit.wrap_label(Kit.t("ui.c3.protocol.success"), "TypeLabel")
	Kit.scalable(_success_label, 24)
	sv.add_child(_success_label)
	_success_box.visible = false
	v.add_child(_success_box)
	return scroll


func _paper_box() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/paper.png")
	for side in 4:
		st.set_texture_margin(side, 21)
	st.set_content_margin(SIDE_LEFT, 30)
	st.set_content_margin(SIDE_RIGHT, 30)
	st.set_content_margin(SIDE_TOP, 24)
	st.set_content_margin(SIDE_BOTTOM, 28)
	return st


func _make_stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(252, 78)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_evidence.png")
	frame.size = Vector2(252, 78)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 27)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(252, 78)
	l.pivot_offset = Vector2(126, 39)
	l.rotation = deg_to_rad(-3.0)
	l.modulate = Color(1, 1, 1, 0.92)
	c.add_child(l)
	return c


# ================================================================ open / state
func open(id: String) -> void:
	obj_id = id
	var p = Kit.call_svc("Story", "puzzle_for", [id], null)
	_puzzle = p if p is Dictionary and not p.is_empty() else Kit.puzzle_for_objective(id)
	var ds = _puzzle.get("display_symbols", DEFAULT_SYMBOLS)
	symbols = (ds as Array).duplicate() if ds is Array and ds.size() == SLOT_COUNT else DEFAULT_SYMBOLS.duplicate()
	slots = ["", "", "", ""]
	history.clear()
	_fails = 0
	_done = false
	_beat_token += 1
	_close_btn.text = Kit.t("ui.c3.protocol.close")
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
	return _feedback.text if _feedback != null else ""


func hint_shown() -> bool:
	return _hint_box != null and _hint_box.visible


func success_shown() -> bool:
	return _success_box != null and _success_box.visible


func _first_free() -> int:
	for i in slots.size():
		if str(slots[i]) == "":
			return i
	return -1


# ================================================================ actions
## Key N (1-based): the card at position N of the original tray order.
func place_key(n: int) -> bool:
	if n < 1 or n > symbols.size():
		return false
	return place(str(symbols[n - 1]))


## Lays the card into the next free slot. False when it is already on the board or every slot is taken.
func place(sym: String) -> bool:
	if _done or not (sym in symbols) or sym in slots:
		return false
	var i := _first_free()
	if i < 0:
		return false
	slots[i] = sym
	history.append(sym)
	Kit.ui_sound("card")
	_set_feedback("")
	_refresh()
	if _slot_cards[i].is_inside_tree() and not Kit.reduced_motion():
		Kit.appear(_slot_cards[i], 0.14)
		Kit.appear(_slot_names[i], 0.14)
	if _first_free() < 0:
		_check_btn.grab_focus.call_deferred()
	else:
		_focus_next_card()
	return true


## Takes the card of slot i back to the tray (mouse click / accept on a filled slot).
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


## Backspace / „Zurück": takes back the card laid last.
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


## R / „Neu ordnen": every card back to the tray.
func reset_order() -> bool:
	if _done or history.is_empty():
		return false
	slots = ["", "", "", ""]
	history.clear()
	Kit.ui_sound("page")
	_set_feedback("")
	_refresh()
	_focus_next_card()
	return true


## Enter / „Prüfen". Returns the engine result ({} when nothing was submitted).
func submit() -> Dictionary:
	if _done:
		return {}
	if _first_free() >= 0:
		_set_feedback(Kit.t("ui.c3.protocol.incomplete"))
		Kit.ui_sound("tick")
		_focus_next_card()
		return {}
	var answer: Array = slots.duplicate()
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	if r == null or not ok:
		_set_feedback(Kit.t("ui.c3.protocol.error", {"error": _error_text(r)}))
		Kit.ui_sound("fail")
		return r if r is Dictionary else {"ok": false, "error": "no Story service"}
	var is_solved: bool = bool(r) if r is bool else bool((r as Dictionary).get("solved", false))
	if is_solved:
		_on_solved()
	else:
		_fails += 1
		Kit.ui_sound("fail")
		_set_feedback(Kit.t("ui.c3.protocol.wrong"))
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
	_solved_at = Time.get_ticks_msec()
	_set_feedback("")
	_refresh()
	Kit.ui_sound("stamp_thud")
	if not Kit.reduced_motion():
		Kit.appear(_success_box, 0.22)
	_close_btn.text = Kit.t("ui.c3.protocol.continue")
	_close_btn.grab_focus.call_deferred()
	solved_count += 1
	solved.emit(obj_id)
	_beat_token += 1
	if is_inside_tree():
		get_tree().create_timer(success_beat(), true).timeout.connect(_on_beat.bind(_beat_token), CONNECT_ONE_SHOT)


## Seconds the solved modal stays open by itself: a reading beat for the success text (two sentences),
## capped at SUCCESS_BEAT_MAX; any confirm (Enter / Space / Esc / A / B / „Weiter") closes it earlier.
func success_beat() -> float:
	return clampf(1.5 + Kit.t("ui.c3.protocol.success").length() * 0.03, 3.0, SUCCESS_BEAT_MAX)


func _on_beat(token: int) -> void:
	if token == _beat_token and _done and is_open:
		close()


func _set_feedback(text: String) -> void:
	_last_feedback = text
	if _feedback == null:
		return
	_feedback.text = text
	_feedback.visible = text != ""
	_feedback.add_theme_color_override("font_color", Kit.C_TEXT)


func _nudge() -> void:
	if Kit.reduced_motion() or _slot_row == null or not _slot_row.is_inside_tree():
		return
	var tw := _slot_row.create_tween()
	for dx in [6, -6, 3, 0]:
		tw.tween_property(_slot_row, "position:x", float(dx), 0.05)


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
	for i in _slot_buttons.size():
		var sym := str(slots[i])
		var filled := sym != ""
		var b := _slot_buttons[i]
		_slot_cards[i].visible = filled
		_slot_names[i].visible = filled
		_slot_captions[i].visible = not filled
		var chip := b.get_node_or_null("Ordinal")
		if chip != null:
			chip.visible = filled
		if filled:
			_slot_cards[i].texture = Kit.tex(_card_file(sym))
			_slot_names[i].text = card_name(sym)
			b.tooltip_text = Kit.t("ui.c3.protocol.slot_filled", {"n": i + 1, "name": card_name(sym)})
		else:
			b.tooltip_text = Kit.t("ui.c3.protocol.slot", {"n": i + 1})
		var can := filled and not _done
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
		b.modulate = Color(1, 1, 1, 0.24) if used else Color.WHITE
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if avail else Control.CURSOR_ARROW
	var n := filled_count()
	_state_label.text = Kit.t("ui.c3.protocol.state_full") if n == SLOT_COUNT and not _done \
		else Kit.t("ui.c3.protocol.state", {"n": n, "total": SLOT_COUNT})
	_undo_btn.disabled = _done or history.is_empty()
	_reset_btn.disabled = _done or history.is_empty()
	_check_btn.disabled = _done
	_hint_box.visible = _hint_visible()
	_success_box.visible = _done


func _hover_focus(b: Button) -> void:
	if b.focus_mode != Control.FOCUS_NONE and is_open:
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


# ================================================================ input (called by UIRoot before the GUI)
func modal_input(event: InputEvent) -> bool:
	if _done:
		return _done_input(event)
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
		return false                    # the „Weiter" button stays clickable
	if not confirm:
		return event is InputEventKey or event is InputEventJoypadButton
	if Time.get_ticks_msec() - _solved_at >= SUCCESS_GUARD_MS and is_open:
		close()
	return true


func handle_cancel() -> bool:
	if _done and Time.get_ticks_msec() - _solved_at < SUCCESS_GUARD_MS:
		return true
	return super.handle_cancel()
