extends "res://scripts/ui/ui_modal.gd"
## „Die Nummernkette“ (pz_c4_numbers / objective c4c_solve_numbers, documentation/C4_DESIGN.md §2.7) — Alexei at
## the transfer siding.  One wagon, four paint layers: a slate in the siding hut shows Service Tunnel 3 in chalk
## (freight yard, switch posts W1–W4 with an iron hook each, the siding).  Under every post the log line of the
## switch book (date + remark, no number).  The tray holds the four layers as number plates; the player hangs on
## every post the plate the wagon wore there.  „Lampe“ holds every plate against the hand lamp (Gegenlicht): the
## face turns to a ghost and the older number under the paint shows — under „24 318“ only bare metal.  The wagon
## token rolls to the post where a plate is hung and shows its number.  „Probefahrt“ submits the post order
## through Story.solve_puzzle; the wagon then rolls from the yard through the posts and stops at the first post
## whose plate does not lie over the plate before it (reason in words), or rolls into the siding (success).
##
## Registered by data/chapters/c4.json (puzzles.c4c_solve_numbers); ChapterExt.puzzle_ui instances this scene once
## under UIRoot, sets `ui_root`, Game calls open(obj_id) and awaits `closed`.  Works stand-alone (tests) as well.
##
## Key contract (= CheckPuzzle + L; scripts/core/inputplay.gd relies on it): property `is_open`, property `symbols`
## (the tray in display order), key N (1–4) hangs symbols[N - 1] on the next empty post (or the post chosen
## before), Backspace takes back the plate hung last, R clears every post, L toggles the lamp (presentation
## only), Enter checks — only with every post filled, else the „incomplete“ note (no attempt) — Esc closes.
## Pad: D-pad ←/→ (and LB/RB) choose a tray plate, A hangs it (A on a post: take back / choose it), B takes back
## the last plate, X lamp, Y check, Back/Select closes; D-pad ↑/↓ move the focus to posts and buttons.
## Mouse: click a plate, then a post (or drag & drop; post to post swaps); click / right-click a hung plate
## returns it; a click on an empty post chooses it for the next plate; hovering a plate shows its layer under
## the paint in the side panel; a button for every key.
## Wrong answers cost nothing: the plates stay, the engine counts the attempt, the hint appears per
## Settings.puzzle_hints (0 off · 1 after Story.puzzle_hint_available · 2 at once).  Success: the wagon rolls
## through all four posts (a chalk tick at each) into the siding, stamp + text, `solved(obj_id)` once; the modal
## closes after a reading beat (≤ SUCCESS_BEAT_MAX) or earlier on confirm.  Plates are told apart by their
## number and type (enamel / stencil / brush, never by colour alone); the side panel repeats every number as
## text, scaled with the text size.  Pixel art (assets/ui/puzzle/c4_*, tools/pixelgen/gen_ui_c4.py) is drawn
## 1:1 and shown at exactly x3, so every digit stroke is ≥ 3 px.

signal solved(obj_id: String)

const PX := 3
const ART := "res://assets/ui/puzzle/"
const BOARD_JSON := "res://assets/ui/puzzle/c4_numbers_board.json"
const DEFAULT_SYMBOLS := ["c1745", "n47702", "n24318", "c1742"]
const POSTS := 4
const SIDING := 4
const YARD := -1
## World data of the four paint layers (also in the board json, which wins): face number and the plate whose
## face lies under the paint ("" = bare metal).  Used for the lamp and for the reason of a stopped trial run.
const FALLBACK_PLATES := {
	"n24318": {"face": "24 318", "under": "", "kind": "enamel", "file": "c4_plate_n24318.png",
		"lit_file": "c4_plate_n24318_lit.png", "num_file": "c4_num_n24318.png"},
	"c1742": {"face": "C-17/42", "under": "n24318", "kind": "stencil", "file": "c4_plate_c1742.png",
		"lit_file": "c4_plate_c1742_lit.png", "num_file": "c4_num_c1742.png"},
	"n47702": {"face": "47 702", "under": "c1742", "kind": "brush", "file": "c4_plate_n47702.png",
		"lit_file": "c4_plate_n47702_lit.png", "num_file": "c4_num_n47702.png"},
	"c1745": {"face": "C-17/45", "under": "n47702", "kind": "stencil_wet", "file": "c4_plate_c1745.png",
		"lit_file": "c4_plate_c1745_lit.png", "num_file": "c4_num_c1745.png"},
}
const SUCCESS_GUARD_MS := 600
## Upper bound of the success beat (seconds); the input driver waits 10 s.
const SUCCESS_BEAT_MAX := 7.0
## Seconds per post while the wagon rolls through the tunnel.
const ROLL_STEP := 0.34
const CHALK := Color("d3d3c6")
const CHALK_HC := Color("f5efda")
const STAMP_RED := Color("a8382e")

var suppress_toasts := true
var obj_id := ""
## The tray in display order (Story.puzzle_for(obj_id).display_symbols).
var symbols: Array = DEFAULT_SYMBOLS.duplicate()
## Plate on each switch post W1 … W4 ("" = empty hook).
var slots: Array = ["", "", "", ""]
## Plates in the order they were hung (Backspace takes back the last one).
var history: Array = []
## Post chosen for the next plate (click / A on an empty hook), -1 = none.
var armed := -1
## Plate taken up with the mouse (click a plate, then a post), "" = none.
var held := ""
## „Lampe“: the plates are held against the light; presentation only, kept while the game runs.
var lamp := false
## Post where the last trial run stopped (-1 = none).
var halt_post := -1
var solved_count := 0

var _puzzle: Dictionary = {}
var _meta: Dictionary = {}
var _plates: Dictionary = {}
var _fails := 0
var _done := false
var _solved_at := 0
var _beat_token := 0
var _run_token := 0
var _ticks := 0
var _halt_visible := false
var _wagon_at := YARD
var _wagon_sym := ""
var _wagon_tween: Tween
var _dragging := false
var _drag_end_ms := -1000
var _drop_hover := -1
var _info_kind := ""
var _info_key: Variant = null
var _tray_built: Array = []
var _panel: PanelContainer
var _root_box: VBoxContainer
var _instr: Label
var _board: Control
var _post_buttons: Array[Button] = []
var _post_plates: Array[TextureRect] = []
var _post_wires: Array[TextureRect] = []
var _post_glows: Array[TextureRect] = []
var _post_marks: Array[Control] = []
var _post_names: Array[Label] = []
var _post_logs: Array[Label] = []
var _tick_nodes: Array[TextureRect] = []
var _board_labels: Array[Label] = []
var _halt: TextureRect
var _wagon: Control
var _wagon_num: TextureRect
var _lamp_icon: TextureRect
var _tray_col: VBoxContainer
var _tray_kicker: Label
var _tray_grid: GridContainer
var _tray_buttons: Dictionary = {}
var _tray_plates: Dictionary = {}
var _tray_glows: Dictionary = {}
var _tray_marks: Dictionary = {}
var _tray_kinds: Dictionary = {}
var _notes: VBoxContainer
var _state_label: Label
var _lamp_box: VBoxContainer
var _lamp_head: Label
var _lamp_grid: GridContainer
var _lamp_rows: Array[Label] = []
var _info: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _success_box: PanelContainer
var _success_label: Label
var _tip: Label
var _actions: GridContainer
var _check_btn: Button
var _lamp_btn: Button
var _undo_btn: Button
var _reset_btn: Button
var _close_btn: Button
var _controls: Control


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	var meta = Kit.json(BOARD_JSON)
	_meta = meta if meta is Dictionary else {}
	var pl = _meta.get("plates", {})
	_plates = pl if pl is Dictionary and pl.size() == POSTS else FALLBACK_PLATES.duplicate(true)
	add_child(Kit.dimmer(0.82))
	_panel = Kit.panel()
	Kit.full_rect(_panel)
	_panel.offset_left = 28
	_panel.offset_right = -28
	_panel.offset_top = 10
	_panel.offset_bottom = -10
	add_child(_panel)
	_root_box = Kit.vbox(0)
	_panel.add_child(_root_box)
	var head := Kit.hbox(28)
	_root_box.add_child(head)
	head.add_child(Kit.label(Kit.t("ui.c4.numbers.title"), "HeadingLabel"))
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	push.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(push)
	var sub := Kit.label(Kit.t("ui.c4.numbers.subtitle"), "DimLabel")
	sub.size_flags_vertical = Control.SIZE_SHRINK_END
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(sub)
	_root_box.add_child(HSeparator.new())
	_instr = Kit.wrap_label(Kit.t("ui.c4.numbers.instruction"), "BodyLabel")
	_instr.name = "Instruction"
	Kit.scalable(_instr, 26)
	_root_box.add_child(_instr)
	_root_box.add_child(_gap(8))
	_build_board()
	_root_box.add_child(_build_post_row())
	_root_box.add_child(_gap(10))
	var bottom := Kit.hbox(24)
	bottom.name = "Bottom"
	bottom.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root_box.add_child(bottom)
	_tray_col = Kit.vbox(8)
	_tray_col.name = "Tray"
	_tray_col.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	bottom.add_child(_tray_col)
	_tray_kicker = _kicker(Kit.t("ui.c4.numbers.tray"))
	_tray_col.add_child(_tray_kicker)
	_tray_grid = GridContainer.new()
	_tray_grid.columns = 2
	_tray_grid.add_theme_constant_override("h_separation", 22)
	_tray_grid.add_theme_constant_override("v_separation", 8)
	_tray_grid.mouse_filter = Control.MOUSE_FILTER_PASS
	_tray_col.add_child(_tray_grid)
	_build_lamp_list(_tray_col)
	_notes = Kit.vbox(10)
	_notes.name = "Notes"
	_notes.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bottom.add_child(_notes)
	_build_notes(_notes)
	_actions = GridContainer.new()
	_actions.columns = 2
	_actions.add_theme_constant_override("h_separation", 16)
	_actions.add_theme_constant_override("v_separation", 14)
	_actions.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	_actions.custom_minimum_size.x = 380
	bottom.add_child(_actions)
	_check_btn = Kit.button(Kit.t("ui.c4.numbers.btn.check"))
	_check_btn.pressed.connect(func() -> void: submit())
	_lamp_btn = Kit.button(Kit.t("ui.c4.numbers.btn.lamp"))
	_lamp_btn.toggle_mode = true
	_lamp_btn.toggled.connect(_on_lamp_toggled)
	_undo_btn = Kit.button(Kit.t("ui.c4.numbers.btn.undo"))
	_undo_btn.pressed.connect(func() -> void: undo())
	_reset_btn = Kit.button(Kit.t("ui.c4.numbers.btn.reset"))
	_reset_btn.pressed.connect(func() -> void: reset_order())
	_close_btn = Kit.button(Kit.t("ui.c4.numbers.btn.close"))
	_close_btn.pressed.connect(close)
	for b in [_check_btn, _lamp_btn, _undo_btn, _reset_btn, _close_btn]:
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_actions.add_child(b)
	_root_box.add_child(_gap(8))
	_controls = Kit.controls_row([["1–4", Kit.t("ui.c4.numbers.hint_place")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.c4.numbers.hint_undo")],
		["R", Kit.t("ui.c4.numbers.hint_reset")], ["L", Kit.t("ui.c4.numbers.hint_lamp")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.c4.numbers.hint_check")],
		[Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]])
	_controls.tooltip_text = Kit.t("ui.c4.numbers.controls")
	_controls.mouse_filter = Control.MOUSE_FILTER_PASS
	_root_box.add_child(_controls)
	_build_tray()
	_wagon_to(YARD, "", false)
	_refresh()
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)


func _gap(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _kicker(text: String) -> Label:
	var l := Kit.label(text.to_upper().replace("ß", "SS"), "KickerLabel")
	l.clip_text = true
	return l


func _mb(section: String, key: String, fallback):
	var s = _meta.get(section, {})
	return s.get(key, fallback) if s is Dictionary else fallback


func _v2(a) -> Vector2:
	return Vector2(float(a[0]), float(a[1])) if a is Array and a.size() >= 2 else Vector2.ZERO


func _tex(file: String) -> Texture2D:
	return Kit.tex(ART + file)


func _plate_size() -> Vector2:
	return _v2(_mb("plate", "size", [88, 25])) * PX


func _post_x(i: int) -> float:
	var xs = _mb("board", "posts_x", [125, 235, 345, 455])
	return float(xs[i]) if xs is Array and i < xs.size() else 125.0 + 110.0 * i


func _plate_y() -> float:
	return float(_mb("board", "plate_y", 12))


## Plate rect of post i on the board (screen px).
func post_rect(i: int) -> Rect2:
	var ps := _plate_size()
	return Rect2(Vector2(_post_x(i) * PX - ps.x * 0.5, _plate_y() * PX), ps)


func _build_board() -> void:
	var bs := _v2(_mb("board", "size", [592, 112])) * PX
	_board = Control.new()
	_board.name = "Board"
	_board.custom_minimum_size = bs
	_board.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_board.mouse_filter = Control.MOUSE_FILTER_PASS
	_root_box.add_child(_board)
	var bg := Kit.pixel_image(_tex(str(_mb("board", "file", "c4_numbers_board.png"))), PX)
	bg.name = "Slate"
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.size = bs
	_board.add_child(bg)
	var labels: Dictionary = _mb("board", "labels", {}) if _mb("board", "labels", {}) is Dictionary else {}
	for k in ["yard", "siding", "tunnel"]:
		var l := Kit.label(Kit.t("ui.c4.numbers." + k), "", 18, CHALK)
		l.name = "Label_" + k
		l.position = _v2(labels.get(k, [8, 51])) * PX
		_board.add_child(l)
		_board_labels.append(l)
	var ps := _plate_size()
	var glow_sz := _v2(_mb("glow", "size", [102, 37])) * PX
	var wire_sz := _v2(_mb("wire", "size", [88, 9])) * PX
	var tick_sz := _v2(_mb("tick", "size", [13, 11])) * PX
	for i in POSTS:
		var r := post_rect(i)
		var glow := Kit.pixel_image(_tex(str(_mb("glow", "file", "c4_glow.png"))), PX)
		glow.stretch_mode = TextureRect.STRETCH_SCALE
		glow.size = glow_sz
		glow.position = r.get_center() - glow_sz * 0.5
		glow.visible = false
		_board.add_child(glow)
		_post_glows.append(glow)
		var wire := Kit.pixel_image(_tex(str(_mb("wire", "file", "c4_wire.png"))), PX)
		wire.stretch_mode = TextureRect.STRETCH_SCALE
		wire.size = wire_sz
		wire.position = Vector2(r.position.x, r.position.y - wire_sz.y + PX)
		wire.visible = false
		_board.add_child(wire)
		_post_wires.append(wire)
		var b := Kit.button("", "CardButton")
		b.name = "Post%d" % (i + 1)
		b.custom_minimum_size = ps
		b.size = ps
		b.position = r.position
		b.pressed.connect(_on_post_pressed.bind(i))
		b.gui_input.connect(_on_post_gui_input.bind(i))
		b.mouse_entered.connect(_hover_focus.bind(b))
		b.focus_entered.connect(_show_info.bind("post", i))
		b.focus_exited.connect(_clear_info.bind("post", i))
		b.set_drag_forwarding(_drag_from_post.bind(i, b), _can_drop_post.bind(i), _drop_on_post.bind(i))
		_board.add_child(b)
		var plate := Kit.pixel_image(null, PX)
		plate.name = "Plate"
		plate.stretch_mode = TextureRect.STRETCH_SCALE
		plate.size = ps
		plate.visible = false
		b.add_child(plate)
		var mark := _outline(ps, Kit.C_AMBER)
		mark.name = "Mark"
		b.add_child(mark)
		_add_focus_frame(b)
		_post_buttons.append(b)
		_post_plates.append(plate)
		_post_marks.append(mark)
		var tk := Kit.pixel_image(_tex(str(_mb("tick", "file", "c4_tick.png"))), PX)
		tk.stretch_mode = TextureRect.STRETCH_SCALE
		tk.size = tick_sz
		tk.position = Vector2(r.get_center().x - tick_sz.x * 0.5, r.end.y + 3 * PX)
		tk.visible = false
		_board.add_child(tk)
		_tick_nodes.append(tk)
	var hs := _v2(_mb("halt", "size", [19, 19])) * PX
	_halt = Kit.pixel_image(_tex(str(_mb("halt", "file", "c4_halt.png"))), PX)
	_halt.name = "Halt"
	_halt.stretch_mode = TextureRect.STRETCH_SCALE
	_halt.size = hs
	_halt.visible = false
	_board.add_child(_halt)
	var ws := _v2(_mb("wagon", "size", [66, 28])) * PX
	_wagon = Control.new()
	_wagon.name = "Wagon"
	_wagon.size = ws
	_wagon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_board.add_child(_wagon)
	var wi := Kit.pixel_image(_tex(str(_mb("wagon", "file", "c4_wagon.png"))), PX)
	wi.stretch_mode = TextureRect.STRETCH_SCALE
	wi.size = ws
	_wagon.add_child(wi)
	_wagon_num = Kit.pixel_image(null, PX)
	_wagon_num.name = "Number"
	_wagon_num.stretch_mode = TextureRect.STRETCH_SCALE
	_wagon_num.position = _v2(_mb("wagon", "number_at", [5, 8])) * PX
	_wagon_num.size = _v2(_mb("wagon", "number_size", [31, 7])) * PX
	_wagon.add_child(_wagon_num)
	var lsz := _v2(_mb("lamp", "size", [14, 20])) * PX
	_lamp_icon = Kit.pixel_image(_tex(str(_mb("lamp", "off", "c4_lamp_off.png"))), PX)
	_lamp_icon.name = "Lamp"
	_lamp_icon.stretch_mode = TextureRect.STRETCH_SCALE
	_lamp_icon.size = lsz
	_lamp_icon.position = Vector2(bs.x - lsz.x - 7 * PX, 5 * PX)
	_board.add_child(_lamp_icon)


## Post names and the switch book's log lines, one column under every post (fixed type, like the plates; the
## side panel repeats the focused post in the scaled size).
func _build_post_row() -> Control:
	var bs := _v2(_mb("board", "size", [592, 112])) * PX
	var row := Control.new()
	row.name = "PostRow"
	row.custom_minimum_size = Vector2(bs.x, 62)
	row.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var w := 108.0 * PX
	for i in POSTS:
		var col := Kit.vbox(2)
		col.position = Vector2(_post_x(i) * PX - w * 0.5, 0)
		col.size = Vector2(w, 60)
		col.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(col)
		var n := Kit.label(Kit.t("ui.c4.numbers.post.%d" % (i + 1)), "BodyLabel", 20, Kit.C_AMBER)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		n.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		n.custom_minimum_size.x = w
		col.add_child(n)
		var lg := Kit.label(Kit.t("ui.c4.numbers.log.%d" % (i + 1)), "DimLabel", 19)
		lg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lg.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lg.custom_minimum_size.x = w
		col.add_child(lg)
		_post_names.append(n)
		_post_logs.append(lg)
	return row


func _build_tray() -> void:
	if _tray_built == symbols and _tray_grid.get_child_count() == symbols.size():
		return
	for c in _tray_grid.get_children():
		_tray_grid.remove_child(c)
		c.queue_free()
	_tray_buttons.clear()
	_tray_plates.clear()
	_tray_glows.clear()
	_tray_marks.clear()
	_tray_kinds.clear()
	_tray_built = symbols.duplicate()
	var ps := _plate_size()
	var glow_sz := _v2(_mb("glow", "size", [102, 37])) * PX
	var i := 0
	for s in symbols:
		var sym := str(s)
		i += 1
		var cell := Kit.hbox(8)
		cell.name = "Cell_" + sym
		cell.mouse_filter = Control.MOUSE_FILTER_PASS
		_tray_grid.add_child(cell)
		var chip := Kit.panel("KeyChipPanel")
		chip.name = "Key"
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		chip.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		var kl := Kit.label(Kit.key_name(KEY_1 + i - 1), "KeyHintLabel")
		kl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		kl.custom_minimum_size.x = 12
		chip.add_child(kl)
		cell.add_child(chip)
		var col := Kit.vbox(2)
		col.mouse_filter = Control.MOUSE_FILTER_PASS
		cell.add_child(col)
		var b := Kit.button("", "CardButton")
		b.name = "Plate_" + sym
		b.custom_minimum_size = ps
		b.pressed.connect(_on_plate_pressed.bind(sym))
		b.gui_input.connect(_on_plate_gui_input.bind(sym))
		b.mouse_entered.connect(_hover_focus.bind(b))
		b.focus_entered.connect(_show_info.bind("plate", sym))
		b.focus_exited.connect(_clear_info.bind("plate", sym))
		b.set_drag_forwarding(_drag_from_tray.bind(sym, b), _can_drop_tray, _drop_on_tray)
		col.add_child(b)
		var glow := Kit.pixel_image(_tex(str(_mb("glow", "file", "c4_glow.png"))), PX)
		glow.stretch_mode = TextureRect.STRETCH_SCALE
		glow.size = glow_sz
		glow.position = ps * 0.5 - glow_sz * 0.5
		glow.visible = false
		b.add_child(glow)
		var img := Kit.pixel_image(_tex(_plate_file(sym, false)), PX)
		img.name = "Face"
		img.stretch_mode = TextureRect.STRETCH_SCALE
		img.size = ps
		b.add_child(img)
		var mark := _outline(ps, Kit.C_AMBER)
		mark.name = "Held"
		b.add_child(mark)
		_add_focus_frame(b)
		var kind := Kit.label(Kit.t("ui.c4.numbers.kind." + sym), "DimLabel", 18)
		kind.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		kind.custom_minimum_size.x = ps.x
		col.add_child(kind)
		_tray_buttons[sym] = b
		_tray_plates[sym] = img
		_tray_glows[sym] = glow
		_tray_marks[sym] = mark
		_tray_kinds[sym] = kind


## Gegenlicht as text (accessibility): under every tray plate the number under its paint; two columns at
## 100 %, one at 125 % / 150 %.
func _build_lamp_list(parent: VBoxContainer) -> void:
	_lamp_box = Kit.vbox(4)
	_lamp_box.name = "LampList"
	parent.add_child(_lamp_box)
	_lamp_head = _kicker(Kit.t("ui.c4.numbers.lamp_on"))
	_lamp_head.add_theme_color_override("font_color", Kit.C_AMBER)
	_lamp_box.add_child(_lamp_head)
	_lamp_grid = GridContainer.new()
	_lamp_grid.columns = 2
	_lamp_grid.add_theme_constant_override("h_separation", 26)
	_lamp_grid.add_theme_constant_override("v_separation", 2)
	_lamp_grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_lamp_box.add_child(_lamp_grid)
	for i in POSTS:
		var l := Kit.label("", "BodyLabel")
		Kit.scalable(l, 22)
		_lamp_grid.add_child(l)
		_lamp_rows.append(l)


func _build_notes(parent: VBoxContainer) -> void:
	_state_label = Kit.label("", "KickerLabel")
	_state_label.name = "State"
	parent.add_child(_state_label)
	_feedback = Kit.wrap_label("", "BodyLabel")
	_feedback.name = "Feedback"
	_feedback.visible = false
	Kit.scalable(_feedback, 24)
	parent.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	_hint_box.name = "Hint"
	var hh := Kit.hbox(14)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hh.add_child(hic)
	_hint_label = Kit.wrap_label(Kit.t("ui.c4.numbers.hint"), "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 22)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	parent.add_child(_hint_box)
	_info = Kit.wrap_label("", "BodyLabel")
	_info.name = "Info"
	_info.add_theme_color_override("font_color", Kit.C_TEXT_BRIGHT)
	Kit.scalable(_info, 24)
	_info.visible = false
	parent.add_child(_info)
	_tip = Kit.wrap_label("", "ControlHintLabel")
	_tip.name = "Tip"
	parent.add_child(_tip)
	_success_box = Kit.panel("PaperCardPanel")
	_success_box.name = "Success"
	_success_box.add_theme_stylebox_override("panel", _paper_box())
	var sv := Kit.hbox(24)
	_success_box.add_child(sv)
	var stamp := _make_stamp(Kit.t("ui.c4.numbers.stamp").to_upper().replace("ß", "SS"))
	stamp.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sv.add_child(stamp)
	_success_label = Kit.wrap_label(Kit.t("ui.c4.numbers.success"), "TypeLabel")
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
	st.set_content_margin(SIDE_LEFT, 26)
	st.set_content_margin(SIDE_RIGHT, 26)
	st.set_content_margin(SIDE_TOP, 16)
	st.set_content_margin(SIDE_BOTTOM, 18)
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
	if f != null:
		var fs := 27
		while fs > 16 and f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > 214.0:
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


func _outline(sz: Vector2, col: Color) -> Panel:
	var p := Panel.new()
	var st := StyleBoxFlat.new()
	st.draw_center = false
	st.border_color = col
	st.set_border_width_all(3)
	p.add_theme_stylebox_override("panel", st)
	p.position = Vector2(-6, -6)
	p.size = sz + Vector2(12, 12)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.visible = false
	return p


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
	f.position = Vector2(-9, -9)
	f.size = b.custom_minimum_size + Vector2(18, 18)
	f.visible = false
	b.add_child(f)
	b.focus_entered.connect(func() -> void: f.visible = true)
	b.focus_exited.connect(func() -> void: f.visible = false)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())


# ================================================================ plate data
func _plate(sym: String) -> Dictionary:
	var p = _plates.get(sym, FALLBACK_PLATES.get(sym, {}))
	return p if p is Dictionary else {}


func _plate_file(sym: String, lit: bool) -> String:
	var p := _plate(sym)
	return str(p.get("lit_file" if lit else "file", "c4_plate_%s%s.png" % [sym, "_lit" if lit else ""]))


## The number painted on a plate („C-17/45“), from Loc (ui.c4.numbers.face.<sym>) or the board json.
func face(sym: String) -> String:
	var k := "ui.c4.numbers.face." + sym
	return Kit.t(k) if Kit.has_key(k) else str(_plate(sym).get("face", sym))


## The plate whose face lies under this plate's paint ("" = bare metal).
func under_of(sym: String) -> String:
	return str(_plate(sym).get("under", ""))


func post_id(i: int) -> String:
	return Kit.t("ui.c4.numbers.post_id.%d" % (i + 1))


## First post whose plate does not lie over the plate on the post before it (the trial run stops there):
## {} when the chain holds, else {post, kind: first | wrong | bare, piece, under, prev}.
func chain_break(order: Array) -> Dictionary:
	for i in order.size():
		var sym := str(order[i])
		var under := under_of(sym)
		if i == 0:
			if under != "":
				return {"post": 0, "kind": "first", "piece": sym, "under": under, "prev": ""}
		elif under != str(order[i - 1]):
			return {"post": i, "kind": "bare" if under == "" else "wrong", "piece": sym, "under": under,
				"prev": str(order[i - 1])}
	return {}


func _wrong_text(br: Dictionary) -> String:
	if br.is_empty():
		return Kit.t("ui.c4.numbers.wrong_generic")
	var piece := face(str(br["piece"]))
	match str(br["kind"]):
		"first":
			return Kit.t("ui.c4.numbers.wrong_first", {"piece": piece, "under": face(str(br["under"]))})
		"bare":
			return Kit.t("ui.c4.numbers.wrong_bare", {"post": post_id(int(br["post"])), "piece": piece,
				"prev": face(str(br["prev"]))})
	return Kit.t("ui.c4.numbers.wrong", {"post": post_id(int(br["post"])), "piece": piece,
		"under": face(str(br["under"])), "prev": face(str(br["prev"]))})


func _under_text(sym: String) -> String:
	var u := under_of(sym)
	return Kit.t("ui.c4.numbers.bare") if u == "" else "„%s“" % face(u)


# ================================================================ open / state
func open(id: String) -> void:
	obj_id = id
	var p = Kit.call_svc("Story", "puzzle_for", [id], null)
	_puzzle = p if p is Dictionary and not p.is_empty() else Kit.puzzle_for_objective(id)
	var ds = _puzzle.get("display_symbols", DEFAULT_SYMBOLS)
	symbols = (ds as Array).duplicate() if ds is Array and ds.size() == POSTS else DEFAULT_SYMBOLS.duplicate()
	slots = ["", "", "", ""]
	history.clear()
	armed = -1
	held = ""
	halt_post = -1
	_halt_visible = false
	_fails = 0
	_done = false
	_ticks = 0
	_beat_token += 1
	_run_token += 1
	_close_btn.text = Kit.t("ui.c4.numbers.btn.close")
	_set_feedback("")
	_build_tray()
	_wagon_to(YARD, "", false)
	_refresh()
	open_modal()


func is_done() -> bool:
	return _done


func filled_count() -> int:
	var n := 0
	for s in slots:
		if str(s) != "":
			n += 1
	return n


func feedback_text() -> String:
	return _feedback.text if _feedback != null and _feedback.visible else ""


func hint_shown() -> bool:
	return _hint_box != null and _hint_box.visible


func success_shown() -> bool:
	return _success_box != null and _success_box.visible


func info_text() -> String:
	return _info.text if _info != null and _info.visible else ""


func lamp_list_shown() -> bool:
	return _lamp_box != null and _lamp_box.visible


func lamp_list_text() -> PackedStringArray:
	var out := PackedStringArray()
	for l in _lamp_rows:
		out.append(l.text)
	return out


## Posts that carry the chalk tick of a finished run (0 … 4).
func ticks_shown() -> int:
	var n := 0
	for t in _tick_nodes:
		if t.visible:
			n += 1
	return n


func halt_shown() -> bool:
	return _halt != null and _halt.visible


## Where the wagon token stands: -1 yard, 0 … 3 posts, 4 siding.
func wagon_at() -> int:
	return _wagon_at


func wagon_number() -> String:
	return _wagon_sym


func tip_text() -> String:
	return _tip.text if _tip != null and _tip.visible else ""


func _first_free() -> int:
	for i in slots.size():
		if str(slots[i]) == "":
			return i
	return -1


func _target_post() -> int:
	if armed >= 0 and armed < slots.size() and str(slots[armed]) == "":
		return armed
	return _first_free()


# ================================================================ actions
## Key N (1-based): the plate at position N of the tray (display order).
func place_key(n: int) -> bool:
	if n < 1 or n > symbols.size():
		return false
	return place(str(symbols[n - 1]))


## Hangs the plate on the chosen post, else on the next empty post from W1.  False when it already hangs or
## every post is taken.
func place(sym: String) -> bool:
	if _done or not (sym in symbols) or sym in slots:
		return false
	var i := _target_post()
	if i < 0:
		return false
	_lay(sym, i)
	return true


## Mouse: takes a plate up (click on a tray plate); the next click on a post hangs it.  Again = put it down.
func pick(sym: String) -> bool:
	if _done or not (sym in symbols) or sym in slots:
		return false
	held = "" if held == sym else sym
	Kit.ui_sound("move")
	_refresh()
	return true


## Hangs `sym` on post i (the post's plate goes back to the tray; a plate from another post swaps).
func hang(sym: String, i: int) -> bool:
	if _done or i < 0 or i >= POSTS or not (sym in symbols):
		return false
	var from := slots.find(sym)
	if from >= 0:
		return drop_plate(sym, from, i)
	var occupant := str(slots[i])
	if occupant != "":
		history.erase(occupant)
	_lay(sym, i)
	return true


func _lay(sym: String, i: int) -> void:
	slots[i] = sym
	history.erase(sym)
	history.append(sym)
	armed = -1
	held = ""
	_board_changed()
	Kit.ui_sound("card")
	_wagon_to(i, sym)
	_refresh()
	if _post_plates[i].is_inside_tree() and not Kit.reduced_motion():
		Kit.appear(_post_plates[i], 0.14)
	if _first_free() < 0:
		_check_btn.grab_focus.call_deferred()
	else:
		_focus_next_plate()


## Chooses an empty post for the next plate; again on the same post = forget.
func arm(i: int) -> bool:
	if _done or i < 0 or i >= POSTS or str(slots[i]) != "":
		return false
	armed = -1 if armed == i else i
	Kit.ui_sound("move")
	_refresh()
	if armed >= 0:
		_focus_next_plate()
	return true


## Takes the plate of post i back to the tray.
func take_back(i: int) -> bool:
	if _done or i < 0 or i >= POSTS or str(slots[i]) == "":
		return false
	var sym := str(slots[i])
	slots[i] = ""
	history.erase(sym)
	_board_changed()
	Kit.ui_sound("back")
	_wagon_to_last()
	_refresh()
	_focus_plate(sym)
	return true


## Backspace / pad B / „Rückgängig“: takes back the plate hung last.
func undo() -> bool:
	if _done or history.is_empty():
		return false
	var sym := str(history.pop_back())
	var i := slots.find(sym)
	if i >= 0:
		slots[i] = ""
	_board_changed()
	Kit.ui_sound("back")
	_wagon_to_last()
	_refresh()
	_focus_plate(sym)
	return true


## R / „Neu ordnen“: every plate back to the tray.
func reset_order() -> bool:
	if _done or (history.is_empty() and armed < 0 and held == ""):
		return false
	slots = ["", "", "", ""]
	history.clear()
	armed = -1
	held = ""
	_board_changed()
	Kit.ui_sound("page")
	_wagon_to(YARD, "")
	_refresh()
	_focus_next_plate()
	return true


## L / pad X / „Lampe“: Gegenlicht on or off (presentation only — never part of the answer).
func toggle_lamp() -> bool:
	lamp = not lamp
	Kit.ui_sound("tick" if lamp else "move")
	_refresh()
	return lamp


func _on_lamp_toggled(on: bool) -> void:
	if on != lamp:
		toggle_lamp()


## Drag and drop: `from` = -1 for the tray, else the post the plate is lifted from.  An occupied target sends
## its plate back to the tray (from the tray) or swaps it into the source post (post to post).
func drop_plate(sym: String, from: int, to: int) -> bool:
	if _done or to < 0 or to >= POSTS or not (sym in symbols):
		return false
	if from >= 0:
		if from >= POSTS or str(slots[from]) != sym or from == to:
			return false
		var other := str(slots[to])
		slots[to] = sym
		slots[from] = other
		armed = -1
		held = ""
		_board_changed()
		Kit.ui_sound("card")
		_wagon_to(to, sym)
		_refresh()
		return true
	if sym in slots:
		return false
	var occupant := str(slots[to])
	if occupant != "":
		history.erase(occupant)
	_lay(sym, to)
	return true


## Every change of the board ends a running trial run and clears its stop mark and note.
func _board_changed() -> void:
	_run_token += 1
	halt_post = -1
	_halt_visible = false
	_ticks = 0
	_set_feedback("")


## Enter / pad Y / „Probefahrt“. Returns the engine result ({} when nothing was submitted).
func submit() -> Dictionary:
	if _done:
		return {}
	if _first_free() >= 0:
		_set_feedback(Kit.t("ui.c4.numbers.incomplete"))
		Kit.ui_sound("tick")
		_focus_next_plate()
		return {}
	var answer: Array = slots.duplicate()
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	if r == null or not ok:
		_set_feedback(Kit.t("ui.c4.numbers.error", {"error": _error_text(r)}))
		Kit.ui_sound("fail")
		return r if r is Dictionary else {"ok": false, "error": "no Story service"}
	var is_solved: bool = bool(r) if r is bool else bool((r as Dictionary).get("solved", false))
	if is_solved:
		_on_solved()
	else:
		_fails += 1
		Kit.ui_sound("fail")
		var br := chain_break(answer)
		halt_post = int(br.get("post", POSTS - 1))
		_set_feedback(_wrong_text(br))
		_start_run(halt_post, false)
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
	held = ""
	halt_post = -1
	_halt_visible = false
	_solved_at = Time.get_ticks_msec()
	_set_feedback("")
	_info_kind = ""
	_refresh()
	Kit.ui_sound("stamp_thud")
	if not Kit.reduced_motion():
		Kit.appear(_success_box, 0.22)
	_close_btn.text = Kit.t("ui.c4.numbers.btn.continue")
	_close_btn.grab_focus.call_deferred()
	solved_count += 1
	solved.emit(obj_id)
	_beat_token += 1
	_start_run(POSTS - 1, true)
	if is_inside_tree():
		get_tree().create_timer(success_beat(), true).timeout.connect(_on_beat.bind(_beat_token), CONNECT_ONE_SHOT)


## Seconds the solved modal stays open by itself (reading beat for the run and the text), ≤ SUCCESS_BEAT_MAX;
## any confirm (Enter / Space / Esc / A / B / Back / „Weiter“) closes it earlier.
func success_beat() -> float:
	return clampf(2.0 + Kit.t("ui.c4.numbers.success").length() * 0.03, 3.0, SUCCESS_BEAT_MAX)


func _on_beat(token: int) -> void:
	if token == _beat_token and _done and is_open:
		close()


# ================================================================ the wagon token and the trial run
func _wagon_pos(at: int) -> Vector2:
	var ws := _v2(_mb("wagon", "size", [66, 28]))
	var ty := float(_mb("board", "track_y", 88))
	var x := float(_mb("board", "yard_x", 34))
	if at == SIDING:
		x = float(_mb("board", "siding_x", 548))
		ty = float(_mb("board", "siding_y", 100))
	elif at >= 0:
		x = _post_x(at)
	return Vector2(x - floorf(ws.x * 0.5), ty - ws.y + 1.0) * PX


func _wagon_to(at: int, sym: String, animate := true) -> void:
	_wagon_at = at
	_wagon_sym = sym
	if _wagon == null:
		return
	var tx: Texture2D = _tex(str(_plate(sym).get("num_file", "c4_num_%s.png" % sym))) if sym != "" else null
	_wagon_num.texture = tx
	_wagon_num.visible = tx != null
	var target := _wagon_pos(at)
	if _wagon_tween != null and _wagon_tween.is_valid():
		_wagon_tween.kill()
	if not animate or Kit.reduced_motion() or not _wagon.is_inside_tree():
		_wagon.position = target
		return
	_wagon_tween = _wagon.create_tween()
	var d := clampf(absf(target.x - _wagon.position.x) / 1100.0, 0.12, 0.42)
	_wagon_tween.tween_property(_wagon, "position", target, d).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


func _wagon_to_last() -> void:
	for k in range(history.size() - 1, -1, -1):
		var i := slots.find(str(history[k]))
		if i >= 0:
			_wagon_to(i, str(history[k]))
			return
	_wagon_to(YARD, "")


## The wagon starts at the yard and rolls post by post: to the stop post (wrong) or through all posts into the
## siding (success).  Any board change cancels it.
func _start_run(stop_at: int, success: bool) -> void:
	_run_token += 1
	var token := _run_token
	_ticks = 0
	_halt_visible = false
	_wagon_to(YARD, "", false)
	var n := POSTS if success else clampi(stop_at + 1, 1, POSTS)
	if Kit.reduced_motion() or not is_inside_tree():
		for i in n:
			_run_step(token, i, success)
		if success:
			_run_step(token, SIDING, true)
		return
	for i in n:
		get_tree().create_timer(0.2 + ROLL_STEP * i, true).timeout.connect(_run_step.bind(token, i, success), CONNECT_ONE_SHOT)
	if success:
		get_tree().create_timer(0.3 + ROLL_STEP * POSTS, true).timeout.connect(_run_step.bind(token, SIDING, true), CONNECT_ONE_SHOT)


func _run_step(token: int, i: int, success: bool) -> void:
	if token != _run_token:
		return
	if i >= SIDING:
		_wagon_to(SIDING, str(slots[POSTS - 1]))
		Kit.ui_sound("success_signal")
		return
	_wagon_to(i, str(slots[i]))
	if success:
		_ticks = maxi(_ticks, i + 1)
		_tick_nodes[i].visible = true
		if _tick_nodes[i].is_inside_tree() and not Kit.reduced_motion():
			Kit.appear(_tick_nodes[i], 0.18)
		Kit.ui_sound("tick")
	elif i == halt_post:
		_halt_visible = true
		_refresh_marks()
		if _wagon.is_inside_tree() and not Kit.reduced_motion():
			var base := _wagon_pos(i)
			var tw := _wagon.create_tween()
			tw.tween_interval(0.3)
			for dx in [9, -7, 4, 0]:
				tw.tween_property(_wagon, "position:x", base.x + float(dx), 0.05)


func _set_feedback(text: String) -> void:
	if _feedback == null:
		return
	_feedback.text = text
	_feedback.visible = text != ""
	_refresh_notes()


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


# ================================================================ refresh
func _refresh() -> void:
	if _post_buttons.is_empty():
		return
	var hc := Kit.high_contrast()
	for i in POSTS:
		var sym := str(slots[i])
		var filled := sym != ""
		var b := _post_buttons[i]
		_post_plates[i].visible = filled
		_post_wires[i].visible = filled
		_post_glows[i].visible = filled and lamp and not _done
		if filled:
			_post_plates[i].texture = _tex(_plate_file(sym, lamp and not _done))   # solved: the four faces in order
			b.tooltip_text = Kit.t("ui.c4.numbers.post_tip_filled", {"post": post_id(i), "face": face(sym)})
		else:
			b.tooltip_text = Kit.t("ui.c4.numbers.post_tip", {"post": post_id(i)})
		var can := not _done
		if not can and b.has_focus():
			_focus_next_plate.call_deferred()
		b.focus_mode = Control.FOCUS_ALL if can else Control.FOCUS_NONE
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if can else Control.CURSOR_ARROW
	for s in _tray_buttons:
		var sym := str(s)
		var b: Button = _tray_buttons[sym]
		var used: bool = sym in slots
		var avail := not used and not _done
		if not avail and b.has_focus():
			_focus_next_plate.call_deferred()
		b.disabled = not avail
		b.focus_mode = Control.FOCUS_ALL if avail else Control.FOCUS_NONE
		b.modulate = Color(1, 1, 1, (0.34 if hc else 0.22)) if used else Color.WHITE
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if avail else Control.CURSOR_ARROW
		b.tooltip_text = Kit.t("ui.c4.numbers.plate_tip", {"face": face(sym)})
		(_tray_plates[sym] as TextureRect).texture = _tex(_plate_file(sym, lamp))
		(_tray_glows[sym] as Control).visible = lamp and not used
		(_tray_kinds[sym] as Label).add_theme_color_override("font_color", Kit.C_TEXT if hc else Kit.C_TEXT_DIM)
	for l in _board_labels:
		l.add_theme_color_override("font_color", CHALK_HC if hc else CHALK)
	for l in _post_logs:
		l.add_theme_color_override("font_color", Kit.C_TEXT if hc else Kit.C_TEXT_DIM)
	_lamp_icon.texture = _tex(str(_mb("lamp", "on" if lamp else "off", "c4_lamp_%s.png" % ("on" if lamp else "off"))))
	_lamp_btn.set_pressed_no_signal(lamp)
	_lamp_btn.tooltip_text = Kit.t("ui.c4.numbers.lamp_on" if lamp else "ui.c4.numbers.lamp_off")
	for i in POSTS:
		var sym := str(symbols[i]) if i < symbols.size() else ""
		_lamp_rows[i].text = Kit.t("ui.c4.numbers.lamp_row", {"face": face(sym), "under": _under_text(sym)}) if sym != "" else ""
		_lamp_rows[i].add_theme_color_override("font_color", Kit.C_TEXT_BRIGHT if hc else Kit.C_TEXT)
	_refresh_marks()
	var n := filled_count()
	if _done:
		_state_label.text = Kit.t("ui.c4.numbers.state_done")
	elif held != "":
		_state_label.text = Kit.t("ui.c4.numbers.state_held", {"face": face(held)})
	elif armed >= 0:
		_state_label.text = Kit.t("ui.c4.numbers.state_armed", {"post": post_id(armed)})
	elif n == POSTS:
		_state_label.text = Kit.t("ui.c4.numbers.state_full")
	else:
		_state_label.text = Kit.t("ui.c4.numbers.state", {"n": n, "total": POSTS})
	var hot := (held != "" or armed >= 0) and not _done
	_state_label.add_theme_color_override("font_color", Kit.C_AMBER if hot else (Kit.C_TEXT if hc else Kit.C_TEXT_DIM))
	_undo_btn.disabled = _done or history.is_empty()
	_reset_btn.disabled = _done or (history.is_empty() and armed < 0 and held == "")
	_check_btn.disabled = _done
	_lamp_btn.disabled = _done
	_hint_box.visible = _hint_visible()
	_success_box.visible = _done
	_refresh_info()
	_refresh_notes()


## Outlines (chosen post, drop target, plate in hand), ticks and the stop mark.
func _refresh_marks() -> void:
	if _post_marks.is_empty():
		return
	for i in POSTS:
		var target := held != "" and not _done
		_post_marks[i].visible = not _done and (armed == i or _drop_hover == i or (target and str(slots[i]) == ""))
	for s in _tray_marks:
		(_tray_marks[s] as Control).visible = held == str(s) and not _done
	for i in _tick_nodes.size():
		_tick_nodes[i].visible = _done and i < _ticks
	var show_halt := _halt_visible and halt_post >= 0 and halt_post < POSTS and not _done
	_halt.visible = show_halt
	if show_halt:
		var r := post_rect(halt_post)
		_halt.position = Vector2(r.get_center().x - _halt.size.x * 0.5, r.end.y + 1 * PX)


func _refresh_notes() -> void:
	if _tip == null or _hint_box == null:
		return
	var wide := Kit.text_scale() > 1.1
	_lamp_box.visible = lamp and not _done
	_lamp_grid.columns = 1 if wide else 2
	_tray_col.visible = not _done                  # after the run the success text gets the whole row
	_tray_kicker.visible = not wide
	_actions.columns = 1 if wide else 2            # 125 % / 150 %: the notes get the width
	_actions.custom_minimum_size.x = 210 if wide else 380
	for k in _tray_kinds:                          # 125 % / 150 %: the lamp list and the side panel name the type
		(_tray_kinds[k] as Control).visible = not wide
	_tip.text = Kit.t("ui.c4.numbers.tip_pad" if Kit.last_input_pad else "ui.c4.numbers.tip_mouse")
	var busy := _feedback.visible or _hint_box.visible
	if wide and _hint_box.visible:          # 125 % / 150 %: the hint wins the room over the hover note
		_info.visible = false
	_tip.visible = not _done and not busy and not (wide and _info.visible)
	_instr.visible = not (wide and (busy or _done))


func _show_info(kind: String, key) -> void:
	_info_kind = kind
	_info_key = key
	_refresh_info()


func _clear_info(kind: String, key) -> void:
	if _info_kind == kind and _info_key == key:
		_info_kind = ""
		_info_key = null
		_refresh_info()


## Side panel: the focused / hovered plate with the number under its paint, or the focused post with its log
## line (scaled with the text size).
func _refresh_info() -> void:
	if _info == null:
		return
	var txt := ""
	if not _done:
		if _info_kind == "plate" and _info_key != null:
			var sym := str(_info_key)
			txt = "%s\n%s" % [Kit.t("ui.c4.numbers.card." + sym), Kit.t("ui.c4.numbers.under." + sym)]
		elif _info_kind == "post" and _info_key != null:
			var i := int(_info_key)
			txt = Kit.t("ui.c4.numbers.info_post", {"post": Kit.t("ui.c4.numbers.post.%d" % (i + 1)),
				"log": Kit.t("ui.c4.numbers.log.%d" % (i + 1))})
			var sym := str(slots[i])
			if sym != "":
				txt += "\n" + Kit.t("ui.c4.numbers.info_hung", {"face": face(sym), "under": _under_text(sym)})
	_info.text = txt
	_info.visible = txt != ""
	_refresh_notes()


func _on_setting_changed(key: String, _value) -> void:
	if key in ["text_scale", "high_contrast"]:
		_refresh()


# ================================================================ focus
func _hover_focus(b: Button) -> void:
	if b.focus_mode != Control.FOCUS_NONE and is_open and not _dragging:
		b.grab_focus()


func _focus_plate(sym: String) -> void:
	var b: Button = _tray_buttons.get(sym)
	if b != null and b.focus_mode != Control.FOCUS_NONE and b.is_inside_tree():
		b.grab_focus.call_deferred()
	else:
		_focus_next_plate()


func _focus_next_plate() -> void:
	if not is_inside_tree():
		return
	if _done:
		_close_btn.grab_focus.call_deferred()
		return
	for s in symbols:
		var b: Button = _tray_buttons.get(str(s))
		if b != null and b.focus_mode != Control.FOCUS_NONE:
			b.grab_focus.call_deferred()
			return
	_check_btn.grab_focus.call_deferred()


## Pad ←/→ (LB/RB): the next / previous plate still in the tray (wraps around).
func select_plate(dir: int) -> String:
	var avail: Array = []
	for s in symbols:
		var b: Button = _tray_buttons.get(str(s))
		if b != null and not b.disabled:
			avail.append(str(s))
	if avail.is_empty():
		if is_inside_tree():
			_check_btn.grab_focus()
		return ""
	var cur := -1
	var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	for k in avail.size():
		if _tray_buttons[avail[k]] == f:
			cur = k
	var nxt := (0 if dir > 0 else avail.size() - 1) if cur < 0 else posmod(cur + dir, avail.size())
	var sym := str(avail[nxt])
	if is_inside_tree():
		(_tray_buttons[sym] as Button).grab_focus()
	Kit.ui_sound("move")
	return sym


func focus_default() -> void:
	_focus_next_plate()


func _on_open() -> void:
	Kit.ui_sound("paper")
	_refresh()


func _on_close() -> void:
	_beat_token += 1
	_run_token += 1
	held = ""
	_info_kind = ""


# ================================================================ mouse: click, right-click, drag and drop
func _recent_drag() -> bool:
	return _dragging or Time.get_ticks_msec() - _drag_end_ms < 150


func _on_plate_pressed(sym: String) -> void:
	if _recent_drag() or _done or sym in slots:
		return
	if armed >= 0:
		place(sym)
	else:
		pick(sym)


func _on_post_pressed(i: int) -> void:
	if _recent_drag() or _done:
		return
	if held != "":
		hang(held, i)
	elif str(slots[i]) != "":
		take_back(i)
	else:
		arm(i)


func _on_post_gui_input(event: InputEvent, i: int) -> void:
	if event is InputEventMouseButton and event.pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_RIGHT:
		if str(slots[i]) != "":
			take_back(i)
		elif held != "" or armed >= 0:
			held = ""
			armed = -1
			_refresh()
		if is_inside_tree():
			get_viewport().set_input_as_handled()


func _on_plate_gui_input(event: InputEvent, _sym: String) -> void:
	if event is InputEventMouseButton and event.pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_RIGHT:
		if held != "":
			held = ""
			Kit.ui_sound("back")
			_refresh()
		if is_inside_tree():
			get_viewport().set_input_as_handled()


func _drag_from_tray(at: Vector2, sym: String, src: Control) -> Variant:
	if _done or sym in slots:
		return null
	_dragging = true
	held = ""
	_set_preview(src, sym, at)
	return {"aoe_c4_plate": sym, "from": -1}


func _drag_from_post(at: Vector2, i: int, src: Control) -> Variant:
	if _done or str(slots[i]) == "":
		return null
	_dragging = true
	_set_preview(src, str(slots[i]), at)
	return {"aoe_c4_plate": str(slots[i]), "from": i}


func _set_preview(src: Control, sym: String, at: Vector2) -> void:
	if src.is_inside_tree() and src.get_viewport().gui_is_dragging():
		src.set_drag_preview(_drag_preview(sym, at))


func _drag_preview(sym: String, at: Vector2) -> Control:
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ps := _plate_size()
	var c := Control.new()
	c.position = -at
	c.size = ps
	c.rotation = deg_to_rad(-2.0)
	holder.add_child(c)
	var shadow := ColorRect.new()
	shadow.color = Color(0, 0, 0, 0.4)
	shadow.position = Vector2(9, 9)
	shadow.size = ps
	c.add_child(shadow)
	var img := Kit.pixel_image(_tex(_plate_file(sym, lamp)), PX)
	img.stretch_mode = TextureRect.STRETCH_SCALE
	img.size = ps
	c.add_child(img)
	return holder


func _is_plate_data(data) -> bool:
	return data is Dictionary and data.has("aoe_c4_plate") and data.has("from")


func _can_drop_post(_at: Vector2, data, i: int) -> bool:
	var ok := not _done and _is_plate_data(data) and int(data["from"]) != i
	_set_drop_hover(i if ok else -1)
	return ok


func _drop_on_post(_at: Vector2, data, i: int) -> void:
	_set_drop_hover(-1)
	if _is_plate_data(data):
		drop_plate(str(data["aoe_c4_plate"]), int(data["from"]), i)


func _can_drop_tray(_at: Vector2, data) -> bool:
	_set_drop_hover(-1)
	return not _done and _is_plate_data(data) and int(data["from"]) >= 0


func _drop_on_tray(_at: Vector2, data) -> void:
	if _is_plate_data(data) and int(data["from"]) >= 0:
		take_back(int(data["from"]))


func _set_drop_hover(i: int) -> void:
	if _drop_hover == i:
		return
	_drop_hover = i
	_refresh_marks()


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
	if k == KEY_L:
		toggle_lamp()
		return true
	if k == KEY_ENTER or k == KEY_KP_ENTER:
		var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
		if f != null and f in [_lamp_btn, _undo_btn, _reset_btn, _close_btn]:
			return false                # Enter on another action button presses that button
		submit()
		return true
	return false


## Controller (C4_DESIGN §2.7): ←/→ and LB/RB choose a tray plate, A hangs it (or acts on the focused post /
## button), B takes back the last plate, X lamp, Y trial run, Back/Select closes.  ↑/↓ stay with the GUI focus.
func _pad_input(jb: InputEventJoypadButton) -> bool:
	var mine := [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_X, JOY_BUTTON_Y, JOY_BUTTON_BACK, JOY_BUTTON_DPAD_LEFT,
		JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER]
	if not jb.pressed:
		return jb.button_index in mine
	match jb.button_index:
		JOY_BUTTON_A:
			_pad_accept()
			return true
		JOY_BUTTON_B:
			undo()
			return true
		JOY_BUTTON_X:
			toggle_lamp()
			return true
		JOY_BUTTON_Y:
			submit()
			return true
		JOY_BUTTON_BACK:
			Kit.ui_sound("back")
			close()
			return true
		JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_LEFT_SHOULDER:
			select_plate(-1)
			return true
		JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_RIGHT_SHOULDER:
			select_plate(1)
			return true
	return false


func _pad_accept() -> void:
	var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	if f == null or not is_ancestor_of(f):
		return
	for s in _tray_buttons:
		if _tray_buttons[s] == f:
			if not (f as Button).disabled:
				place(str(s))
			return
	var i := _post_buttons.find(f)
	if i >= 0:
		if held != "":
			hang(held, i)
		elif str(slots[i]) != "":
			take_back(i)
		else:
			arm(i)
		return
	if f is BaseButton and not (f as BaseButton).disabled:
		if (f as BaseButton).toggle_mode:
			(f as BaseButton).button_pressed = not (f as BaseButton).button_pressed
		else:
			(f as BaseButton).pressed.emit()


## After success: confirm / cancel (after a short guard) closes; everything else is swallowed.
func _done_input(event: InputEvent) -> bool:
	var confirm := false
	if event is InputEventKey and event.pressed and not event.echo:
		var ke := event as InputEventKey
		var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
		confirm = k in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_ESCAPE, KEY_BACKSPACE]
	elif event is InputEventJoypadButton and event.pressed:
		confirm = (event as InputEventJoypadButton).button_index in [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_BACK]
	elif event is InputEventMouseButton:
		return false                    # the „Weiter“ button stays clickable
	if not confirm:
		return event is InputEventKey or event is InputEventJoypadButton
	if Time.get_ticks_msec() - _solved_at >= SUCCESS_GUARD_MS and is_open:
		close()
	return true


## Esc: first put down a plate in hand, then forget a chosen post, then close.
func handle_cancel() -> bool:
	if _done and Time.get_ticks_msec() - _solved_at < SUCCESS_GUARD_MS:
		return true
	if not _done and (held != "" or armed >= 0):
		held = ""
		armed = -1
		Kit.ui_sound("back")
		_refresh()
		return true
	return super.handle_cancel()


# ================================================================ accessibility report (tests)
## Text colour / background pairs of everything this board draws itself (WCAG contrast is checked by
## tests/test_c4_puzzle_ui.gd against the real art colours from the board json).
func contrast_pairs() -> Array:
	var hc := Kit.high_contrast()
	var surf: Dictionary = _meta.get("surfaces", {}) if _meta.get("surfaces") is Dictionary else {}
	var slate := Color(str(surf.get("slate", "#2A3A3D")))
	return [
		{"what": "chalk label on the slate", "fg": CHALK_HC if hc else CHALK, "bg": slate},
		{"what": "post name", "fg": Kit.C_AMBER, "bg": Kit.C_NAVY},
		{"what": "switch book line", "fg": Kit.C_TEXT if hc else Kit.C_TEXT_DIM, "bg": Kit.C_NAVY},
		{"what": "plate type caption", "fg": Kit.C_TEXT if hc else Kit.C_TEXT_DIM, "bg": Kit.C_NAVY},
		{"what": "lamp list", "fg": Kit.C_TEXT_BRIGHT if hc else Kit.C_TEXT, "bg": Kit.C_NAVY},
		{"what": "side panel info", "fg": Kit.C_TEXT_BRIGHT, "bg": Kit.C_NAVY},
	]
