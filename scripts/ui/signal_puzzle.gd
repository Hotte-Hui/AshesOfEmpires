extends "res://scripts/ui/ui_modal.gd"
## Signal puzzle (pz_signal): a fictional, unpowered teaching box. The three symbol cards come from
## data/v3/puzzles.json display_symbols; the player fills the three slots by clicking cards or pressing 1-3,
## Backspace takes the last card back, "Neu ordnen" clears. "Prüfen" submits via
## Story.solve_puzzle(obj_id, ["square", "circle", "triangle"...]). Wrong answers cost nothing; after the
## configured failures (Story.puzzle_hint_available / Settings.puzzle_hints) a hint appears.

signal solved(obj_id: String)

const BOARD_SCALE := 3
var suppress_toasts := true
var obj_id := ""
var symbols: Array = ["triangle", "square", "circle"]
var order: Array = []
var _puzzle: Dictionary = {}
var _fails := 0
var _done := false
var _board: Control
var _slot_cards: Array[TextureRect] = []
var _lamp: TextureRect
var _tray: HBoxContainer
var _tray_buttons: Dictionary = {}
var _check_btn: Button
var _undo_btn: Button
var _reset_btn: Button
var _close_btn: Button
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _slots_meta: Array = []
var _content: VBoxContainer


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.72))
	var panel := Kit.panel()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.offset_left = -720
	panel.offset_right = 720
	panel.offset_top = -450
	panel.offset_bottom = 450
	add_child(panel)
	_content = Kit.vbox(14)
	panel.add_child(_content)
	_content.add_child(Kit.label(Kit.t("ui.signal.title"), "HeadingLabel"))
	_content.add_child(Kit.label(Kit.t("ui.signal.subtitle"), "DimLabel"))
	_content.add_child(HSeparator.new())
	var instr := Kit.wrap_label(Kit.t("ui.signal.instruction"), "BodyLabel")
	Kit.scalable(instr, 29)
	_content.add_child(instr)
	# play area: the training box (left) and the card tray (right)
	var play := Kit.hbox(64)
	play.alignment = BoxContainer.ALIGNMENT_CENTER
	_content.add_child(play)
	_board = Control.new()
	_board.mouse_filter = Control.MOUSE_FILTER_IGNORE
	play.add_child(_board)
	var bt := Kit.tex("res://assets/ui/puzzle/signal_board.png")
	var board_img := Kit.sprite("res://assets/ui/puzzle/signal_board.png")
	_board.add_child(board_img)
	var bsize := bt.get_size() if bt != null else Vector2(528, 276)
	board_img.size = bsize
	_board.custom_minimum_size = bsize
	var meta = Kit.json("res://assets/ui/puzzle/signal_board.json")
	_slots_meta = meta.get("slots", []) if meta is Dictionary else []
	if meta is Dictionary and meta.has("plate"):
		var pr: Array = meta["plate"]
		var plate := Kit.label(Kit.t("ui.signal.plate").to_upper().replace("ß", "SS"), "TypeLabel", 17)
		plate.add_theme_font_override("font", Kit.font("fv_type_bold"))
		plate.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		plate.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		plate.position = Vector2(int(pr[0]) * BOARD_SCALE, int(pr[1]) * BOARD_SCALE)
		plate.size = Vector2(int(pr[2]) * BOARD_SCALE, int(pr[3]) * BOARD_SCALE)
		_board.add_child(plate)
	for i in 3:
		var r := TextureRect.new()
		r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if i < _slots_meta.size():
			var sl: Array = _slots_meta[i]
			r.position = Vector2((int(sl[0]) + 2) * BOARD_SCALE, (int(sl[1]) + 3) * BOARD_SCALE)
		_board.add_child(r)
		_slot_cards.append(r)
	_lamp = Kit.sprite("res://assets/ui/puzzle/lamp_off.png")
	if meta is Dictionary and meta.has("lamp"):
		_lamp.position = Vector2((int(meta["lamp"][0]) - 7) * BOARD_SCALE, (int(meta["lamp"][1]) - 7) * BOARD_SCALE)
	_lamp.size = Vector2(45, 45)
	_board.add_child(_lamp)
	var tray_col := Kit.vbox(14)
	tray_col.alignment = BoxContainer.ALIGNMENT_CENTER
	play.add_child(tray_col)
	var tray_head := Kit.label(Kit.t("ui.signal.tray").to_upper().replace("ß", "SS"), "KickerLabel")
	tray_head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tray_col.add_child(tray_head)
	_tray = Kit.hbox(30)
	_tray.alignment = BoxContainer.ALIGNMENT_CENTER
	tray_col.add_child(_tray)
	# feedback + hint
	_feedback = Kit.wrap_label("", "BodyLabel")
	_feedback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_feedback.custom_minimum_size.y = 40
	Kit.scalable(_feedback, 28)
	_content.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	var hh := Kit.hbox(16)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hh.add_child(hic)
	_hint_label = Kit.wrap_label("", "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 26)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	_content.add_child(_hint_box)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content.add_child(spacer)
	var row := Kit.hbox(18)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	_content.add_child(row)
	_undo_btn = Kit.button(Kit.t("ui.signal.undo"), "", 230)
	_undo_btn.pressed.connect(undo)
	row.add_child(_undo_btn)
	_reset_btn = Kit.button(Kit.t("ui.signal.reset"), "", 230)
	_reset_btn.pressed.connect(reset_order)
	row.add_child(_reset_btn)
	_check_btn = Kit.button(Kit.t("ui.signal.check"), "", 230)
	_check_btn.pressed.connect(submit)
	row.add_child(_check_btn)
	_close_btn = Kit.button(Kit.t("ui.common.close"), "", 230)
	_close_btn.pressed.connect(close)
	row.add_child(_close_btn)
	_content.add_child(Kit.controls_row([["1|2|3", Kit.t("ui.hint.place_card")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.hint.undo")], [Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]]))


func open(id: String) -> void:
	obj_id = id
	_puzzle = Kit.puzzle_for_objective(id)
	var ds = _puzzle.get("display_symbols", ["triangle", "square", "circle"])
	symbols = ds if ds is Array and not ds.is_empty() else ["triangle", "square", "circle"]
	order.clear()
	_fails = 0
	_done = false
	_lamp.texture = Kit.tex("res://assets/ui/puzzle/lamp_off.png")
	_feedback.text = ""
	_build_tray()
	_refresh()
	open_modal()


func _build_tray() -> void:
	for c in _tray.get_children():
		c.queue_free()
	_tray_buttons.clear()
	var i := 0
	for sym in symbols:
		i += 1
		var col := Kit.vbox(6)
		var b := Kit.button("", "CardButton")
		b.icon = Kit.tex("res://assets/ui/puzzle/card_%s.png" % sym)
		b.tooltip_text = Kit.t("ui.signal.sym." + str(sym))
		b.pressed.connect(place.bind(str(sym)))
		b.mouse_entered.connect(b.grab_focus)
		col.add_child(b)
		var l := Kit.label("%d  ·  %s" % [i, Kit.t("ui.signal.sym." + str(sym))], "KickerLabel")
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(l)
		_tray.add_child(col)
		_tray_buttons[str(sym)] = b


# ================================================================ actions
func place(sym: String) -> void:
	if _done or sym in order or order.size() >= symbols.size():
		return
	order.append(sym)
	Kit.ui_sound("card")
	_feedback.text = ""
	_refresh()
	if order.size() == symbols.size():
		_check_btn.grab_focus()
	else:
		_focus_next_card()


func undo() -> void:
	if _done or order.is_empty():
		return
	var sym: String = order.pop_back()
	_refresh()
	if _tray_buttons.has(sym):
		(_tray_buttons[sym] as Button).grab_focus()


func reset_order() -> void:
	if _done:
		return
	order.clear()
	_feedback.text = ""
	_refresh()
	_focus_next_card()


func submit() -> void:
	if _done:
		return
	if order.size() < symbols.size():
		_set_feedback(Kit.t("ui.signal.incomplete"), false)
		return
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, order.duplicate()], null)
	var ok := r is bool or Kit.ok(r)
	var is_solved: bool = bool(r) if r is bool else (ok and bool((r as Dictionary).get("solved", false)))
	if r == null or not ok:
		var e := Kit.err_text(r)
		_set_feedback(Kit.t("ui.signal.error", {"error": e if e != "" else Kit.t("ui.common.unavailable")}), false)
		return
	if is_solved:
		_done = true
		_lamp.texture = Kit.tex("res://assets/ui/puzzle/lamp_on.png")
		_set_feedback(Kit.t("ui.signal.solved"), true)
		Kit.ui_sound("success_signal")
		_refresh()
		solved.emit(obj_id)
		await get_tree().create_timer(1.8 if not Kit.reduced_motion() else 1.2).timeout
		if is_open:
			close()
		return
	_fails += 1
	Kit.ui_sound("fail")
	_set_feedback(Kit.t("ui.signal.wrong"), false)
	_shake()
	order.clear()
	_refresh()
	_focus_next_card()


func _set_feedback(text: String, good: bool) -> void:
	_feedback.text = text
	_feedback.add_theme_color_override("font_color", Kit.C_AMBER if good else Kit.C_TEXT)


func _shake() -> void:
	if Kit.reduced_motion():
		return
	var p := _board.position
	var tw := _board.create_tween()
	for dx in [9, -9, 6, -6, 3, 0]:
		tw.tween_property(_board, "position:x", p.x + dx, 0.045)


func _hint_visible() -> bool:
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
	for i in _slot_cards.size():
		_slot_cards[i].texture = Kit.tex("res://assets/ui/puzzle/card_%s.png" % order[i]) if i < order.size() else null
		if i < _slot_cards.size():
			_slot_cards[i].size = Vector2(102, 138)
	for sym in _tray_buttons:
		var b: Button = _tray_buttons[sym]
		var used: bool = sym in order
		b.disabled = used or _done
		b.modulate = Color(1, 1, 1, 0.32) if used else Color.WHITE
	_check_btn.disabled = _done or order.size() < symbols.size()
	_undo_btn.disabled = _done or order.is_empty()
	_reset_btn.disabled = _done or order.is_empty()
	var hv := _hint_visible() and not _done
	_hint_box.visible = hv
	_hint_label.text = Kit.t("ui.signal.hint")


func _focus_next_card() -> void:
	for sym in symbols:
		var b: Button = _tray_buttons.get(str(sym))
		if b != null and not b.disabled:
			b.grab_focus.call_deferred()
			return
	_close_btn.grab_focus.call_deferred()


func focus_default() -> void:
	_focus_next_card()


func modal_input(event: InputEvent) -> bool:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return false
	var k := (event as InputEventKey).physical_keycode
	if k >= KEY_1 and k <= KEY_9:
		var i := int(k - KEY_1)
		if i < symbols.size():
			place(str(symbols[i]))
		return true
	if k >= KEY_KP_1 and k <= KEY_KP_9:
		var j := int(k - KEY_KP_1)
		if j < symbols.size():
			place(str(symbols[j]))
		return true
	if k == KEY_BACKSPACE:
		undo()
		return true
	return false
