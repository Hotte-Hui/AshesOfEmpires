extends "res://scripts/ui/minigames/minigame_base.gd"
## Bahnhof Veltrava "Die Fallblatttafel" (scenes/ui/minigames/FlapBoard.tscn, explore entry
## veltrava.station.flap_board, §12.8). The arrivals board on canopy column 3 hangs in its top row — at the
## train Alexei came on. He opens the service hatch and turns the six flap drums (hour, tens, units, from, via,
## platform) by hand until the line reads as in the printed timetable: 8:41 · MOSKVA über KARSK · Gleis 5.
## Drums only fall forward and four of them are coupled (flap_logic.gd); the line engages by itself once every
## flap is right. „Probelauf" (Enter) runs the motor once and names what still differs (a failure, like a
## knocked-off drum; two of them bring the hint). Art: assets/ui/minigames/flap/ (tools/pixelgen/gen_mg_flap.py,
## 1:1 art px, drawn x3); flap_faces_hc.png in the high-contrast setting. Sounds: mg_flap_* (tools/audiogen/
## mg_audio_r7_v.py).
## Keys: Left/Right (A/D, d-pad) choose a drum · Up/W, Space/E or pad A turn it one flap (hold to keep turning) ·
## Enter or pad X: Probelauf · R or pad Y: start over · Down: (nothing — the flaps only fall one way) · Esc gives
## up. Mouse: click (and hold) a drum of the top row or of the open hatch; wheel over it turns it.

const Logic := preload("res://scripts/ui/minigames/flap_logic.gd")
const ART := "res://assets/ui/minigames/flap/"
const FLIP_T := 0.07
const REPEAT_FIRST := 0.34
const REPEAT_EVERY := 0.1
const STUCK := [2, 4]          # units and via hang half-fallen until first touched
const COL_AMBER := Color("edb777")
const COL_AMBER_D := Color("a8643a")
const COL_RED := Color("c8503c")
const COL_IRON := [Color("15171c"), Color("22262d"), Color("323840"), Color("464d55"), Color("5e666e")]
const COL_NIGHT0 := Color("070a12")
const COL_SNOW := Color("f2f3f5")

var logic = Logic.new()
## Art scale: x3, or x2 in the compact layout for larger text (set in _build_play).
var S := 3
var compact := false
var layout: Dictionary = {}
var cursor := 0
var shown: Array = []          # flap index each drum of row 1 currently shows (lags the logic while flipping)
var _queue: Array = []         # pending flips per drum
var _flip: Array = []          # flip progress 0..1 per drum
var _phase: Array = []         # hatch cylinder scroll per drum (art px)
var _stuck: Dictionary = {}
var _tex: Dictionary = {}
var _board_view: Control
var _hatch_view: Control
var _drum_title: Label
var _drum_seq: Label
var _notes: VBoxContainer
var _note_labels: Dictionary = {}
var _held := false
var _repeat := 0.0
var _mouse_hold := false
var _anim := 0.0
var _engaged := -1.0
var _clacks_this_frame := 0
var _input_guard := 0.0


class View extends Control:
	var game: Node
	var kind := ""

	func _draw() -> void:
		game.call("draw_" + kind, self)

	func _gui_input(event: InputEvent) -> void:
		game.view_input(self, event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.flap.kicker", "mg.flap.title", "mg.flap.subtitle", "mg.flap.instruction")
	# larger text (125 / 150 %): the pixel art drops to x2, the timetable runs in two halves, the notes card goes
	# (its content stays in the status line and in the lit couplings of the hatch) -- nothing overflows the panel
	compact = Kit.text_scale() > 1.01
	S = 2 if compact else 3
	if compact:      # the subtitle's clue (Alexei's own train) moves into the instruction
		_subtitle.visible = false
		_instr.text = Kit.t("mg.flap.instruction_compact")
	var lj = Kit.json(ART + "flap_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["flap_board", "flap_hatch", "flap_faces", "flap_faces_hc"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	var row := Kit.hbox(30)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	# left: the board and, below it, the open service hatch of the top row
	var left := Kit.vbox(8)
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(left)
	var sz: Array = layout.get("size", [252, 110])
	_board_view = _view("board", Vector2(float(sz[0]), float(sz[1])))
	left.add_child(_board_view)
	var hs: Array = layout.get("hatch_size", [252, 34])
	_hatch_view = _view("hatch", Vector2(float(hs[0]), float(hs[1])))
	left.add_child(_hatch_view)
	if not compact:
		var cap := Kit.label(Kit.t("mg.flap.hatch"), "DimLabel")
		Kit.scalable(cap, 19)
		cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		left.add_child(cap)
	# middle: the printed timetable
	var sheet := _build_sheet()
	sheet.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sheet.custom_minimum_size.x = 900 if compact else 500
	row.add_child(sheet)
	if compact:
		_add_button(Kit.t("mg.flap.btn.probe"), probe, 260, true)
		return
	# right: Alexei's notes (the chosen drum and the couplings he has seen work)
	var info := Kit.panel("PlatePanel")
	info.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	info.custom_minimum_size = Vector2(380, 0)
	row.add_child(info)
	var col := Kit.vbox(6)
	info.add_child(col)
	col.add_child(Kit.label(Kit.t("mg.flap.notes.title").to_upper().replace("ß", "SS"), "KickerLabel"))
	_drum_title = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_drum_title, 22)
	_drum_title.add_theme_color_override("font_color", Kit.C_COPPER_L)
	col.add_child(_drum_title)
	_drum_seq = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_drum_seq, 21)
	col.add_child(_drum_seq)
	col.add_child(Kit.rule(Kit.C_COPPER_D, 2))
	var ct := Kit.label(Kit.t("mg.flap.notes.couplings"), "DimLabel")
	Kit.scalable(ct, 20)
	col.add_child(ct)
	_notes = Kit.vbox(2)
	col.add_child(_notes)
	_add_button(Kit.t("mg.flap.btn.probe"), probe, 260, true)


func _view(kind: String, art_size: Vector2) -> Control:
	var v := View.new()
	v.game = self
	v.kind = kind
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	v.custom_minimum_size = art_size * S
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	return v


func _build_sheet() -> Control:
	var card := Kit.panel("PaperCardPanel")
	var col := Kit.vbox(4)
	card.add_child(col)
	col.add_child(Kit.label(Kit.t("mg.flap.sheet.kicker").to_upper().replace("ß", "SS"), "PaperKicker"))
	if not compact:
		var sub := Kit.wrap_label(Kit.t("mg.flap.sheet.sub"), "PaperBody")
		Kit.scalable(sub, 19)
		col.add_child(sub)
	col.add_child(Kit.rule(Kit.C_PAPER_D, 2))
	# one table (or, in the compact layout, two halves side by side)
	var halves := 2 if compact else 1
	var per := int(ceil(float(Logic.SHEET.size()) / halves))
	var tables := Kit.hbox(44)
	col.add_child(tables)
	for hf in halves:
		var grid := GridContainer.new()
		grid.columns = 5
		grid.add_theme_constant_override("h_separation", 18)
		grid.add_theme_constant_override("v_separation", 0)
		tables.add_child(grid)
		for k in ["time", "from", "via", "track", "note"]:
			grid.add_child(Kit.label(Kit.t("mg.flap.sheet.head." + k), "PaperKicker"))
		for ri in range(hf * per, mini((hf + 1) * per, Logic.SHEET.size())):
			var r: Array = Logic.SHEET[ri]
			var vals := [str(r[0]), _city(str(r[1])), _city(str(r[2])) if str(r[2]) != "" else "–", str(r[3]),
				Kit.t("mg.flap.sheet.note." + str(r[4])) if str(r[4]) != "" else ""]
			for i in vals.size():
				var l := Kit.label(str(vals[i]), "PaperBody")
				Kit.scalable(l, 21)
				if i == 0 or i == 3:
					l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
				grid.add_child(l)
	col.add_child(Kit.rule(Kit.C_PAPER_D, 2))
	for k in (["mg.flap.sheet.foot.compact"] if compact else ["mg.flap.sheet.foot.1", "mg.flap.sheet.foot.2"]):
		var f := Kit.wrap_label(Kit.t(k), "PaperBody")
		Kit.scalable(f, 18)
		col.add_child(f)
	return card


## Timetable spelling of a board name (the sheet is set in mixed case: MOSKVA -> Moskva, ZÜRICH -> Zürich).
static func _city(board_name: String) -> String:
	return board_name.substr(0, 1) + board_name.substr(1).to_lower()


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.25


func _reset_game() -> void:
	logic.reset()
	shown = logic.pos.duplicate()
	_queue = []
	_flip = []
	_phase = []
	for i in Logic.IDS.size():
		_queue.append(0)
		_flip.append(0.0)
		_phase.append(float(logic.pos[i] * 3))
	_stuck = {}
	for i in STUCK:
		_stuck[i] = true
	cursor = 0
	_engaged = -1.0
	_mouse_hold = false
	_held = false
	_update_ui()


# ================================================================ actions
func turn_selected() -> void:
	if solved or ended:
		return
	var moves: Array = logic.turn(cursor)
	_stuck.erase(cursor)
	for m in moves:
		var d := int(m["drum"])
		_queue[d] = int(_queue[d]) + 1
		_stuck.erase(d)
	_sfx("mg_flap_turn", -9.0)
	var hit: Array = Logic.disturbed(moves)
	if not hit.is_empty():
		register_fail(_coupling_text(hit[0], true))
	else:
		for m in moves:
			if str(m["kind"]) != "turn":
				var key := "%s>%s" % [Logic.IDS[int(m["by"])], Logic.IDS[int(m["drum"])]]
				var knocked := bool(m["was_ok"]) and not bool(m["now_ok"])
				if not _note_labels.has(key) or knocked:
					clear_status_hold()
					set_status(_coupling_text(m, false))
					_status_hold = 2.6
					break
	_update_ui()


func _coupling_text(m: Dictionary, fail: bool) -> String:
	var driver := _drum_name(int(m["by"]))
	var driven := _drum_name(int(m["drum"]))
	if str(m["kind"]) == "carry":
		return Kit.t("mg.flap.fail.carry" if fail else "mg.flap.status.carry")
	return Kit.t("mg.flap.fail.drag" if fail else "mg.flap.status.drag", {"driver": driver, "driven": driven})


## „Probelauf": the motor runs once; the line engages only if every flap matches the timetable.
func probe() -> void:
	if solved or ended:
		return
	if logic.is_solved():
		return                         # engages by itself as soon as the flips have settled
	_sfx("mg_flap_rattle", -4.0)
	var r: int = logic.sheet_match()
	if r >= 0 and r != Logic.TARGET_SHEET_ROW:
		register_fail(Kit.t("mg.flap.fail.other_train", {"from": _city(str(Logic.SHEET[r][1])), "track": str(Logic.SHEET[r][3])}))
		return
	var names: Array = []
	for i in logic.wrong():
		names.append(_drum_name(int(i)))
	register_fail(Kit.t("mg.flap.fail.probe", {"fields": ", ".join(names)}))


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	set_status(Kit.t("mg.flap.status.restart"))
	_status_hold = 2.0


func _drum_name(i: int) -> String:
	return Kit.t("mg.flap.drum." + str(Logic.IDS[clampi(i, 0, Logic.IDS.size() - 1)]))


func _flap_name(i: int, idx: int) -> String:
	var t := str(Logic.FLAPS[i][idx])
	if t == "":
		return Kit.t("mg.flap.blank")
	return t


func _hint_text(level: int) -> String:
	if level <= 1:
		return Kit.t("mg.flap.hint.1")
	if level == 2:
		return Kit.t("mg.flap.hint.2")
	var d: int = logic.next_drum()
	if d < 0:
		return Kit.t("mg.flap.hint.2")
	return Kit.t("mg.flap.hint.next", {"name": _drum_name(d), "flap": _flap_name(d, Logic.TARGET[d])})


## Settings "puzzle_hints" (like the other puzzles): 0 never a hint, 1 after two failures (default), 2 the first
## hint at once and one level more with every failure.
func register_fail(text: String) -> void:
	var mode := int(Kit.setting("puzzle_hints", 1))
	if mode == 1:
		super.register_fail(text)
		return
	fails += 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	if mode == 2:
		show_hint(fails + 1)


func _hint_at_open() -> void:
	if int(Kit.setting("puzzle_hints", 1)) == 2:
		show_hint(1)


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.flap.ctrl.select")],
		[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_SPACE), Kit.t("mg.flap.ctrl.turn")],
		[Kit.key_name(KEY_ENTER), Kit.t("mg.flap.ctrl.probe")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	_clacks_this_frame = 0
	var settled := true
	for i in Logic.IDS.size():
		if int(_queue[i]) <= 0:
			_flip[i] = 0.0
			continue
		settled = false
		var speed := 1.0 if int(_queue[i]) <= 2 else 2.2
		if Kit.reduced_motion():
			speed *= 1.6
		_flip[i] = float(_flip[i]) + delta * speed / FLIP_T
		_phase[i] = float(_phase[i]) + delta * speed / FLIP_T * 3.0
		while float(_flip[i]) >= 1.0 and int(_queue[i]) > 0:
			_flip[i] = float(_flip[i]) - 1.0
			_queue[i] = int(_queue[i]) - 1
			shown[i] = (int(shown[i]) + 1) % Logic.flap_count(i)
			if _clacks_this_frame < 2:
				_clacks_this_frame += 1
				_sfx("mg_flap_clack", -7.0 if _clacks_this_frame == 1 else -11.0)
		if int(_queue[i]) <= 0:
			_flip[i] = 0.0
			_phase[i] = float(int(shown[i]) * 3)
	# held turning: only after a turn press inside the mini-game (a key still held from opening it does nothing)
	if not solved:
		if _held and not _turn_held():
			_held = false
		if _mouse_hold and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			_mouse_hold = false        # released outside the board
		if (_held and _turn_held()) or _mouse_hold:
			_repeat -= delta
			if _repeat <= 0.0:
				_repeat = REPEAT_EVERY
				turn_selected()
		else:
			_repeat = REPEAT_FIRST
		if settled and logic.is_solved():
			_engage()
	if _engaged >= 0.0:
		_engaged += delta
	if not solved:
		status_auto(Kit.t("mg.flap.status.idle"))
	_redraw()


func _turn_held() -> bool:
	if _input_guard > 0.0:
		return false
	for a in ["ui_up", "move_up"]:
		if InputMap.has_action(a) and Input.is_action_pressed(a):
			return true
	return Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_E) \
		or Input.is_joy_button_pressed(0, JOY_BUTTON_A)


func _engage() -> void:
	if solved:
		return
	_engaged = 0.0
	_mouse_hold = false
	_sfx("mg_flap_engage", -2.0)
	mark_solved(Kit.t("mg.flap.solved"))


func _update_ui() -> void:
	if _hint_box != null and _hint_box.visible and hint_level >= 3:
		_hint_label.text = _hint_text(hint_level)      # the step hint follows the board
	if _drum_title == null:          # compact layout: no notes card (the hatch and the status line carry it)
		_redraw()
		return
	_drum_title.text = Kit.t("mg.flap.drum.title", {"name": _drum_name(cursor), "n": Logic.flap_count(cursor)})
	var seq: Array = []
	if cursor <= 2 or cursor == 5:     # numbers: the range says it all
		seq.append("%s–%s" % [_flap_name(cursor, 0), _flap_name(cursor, Logic.flap_count(cursor) - 1)])
	else:
		for k in Logic.flap_count(cursor):
			seq.append(_flap_name(cursor, k))
	_drum_seq.text = Kit.t("mg.flap.drum.sequence", {"list": " · ".join(seq), "now": _flap_name(cursor, int(logic.pos[cursor]))})
	for key in logic.known:
		if not _note_labels.has(key):
			var l := Kit.wrap_label(Kit.t("mg.flap.note." + str(key).replace(">", "_")), "BodyLabel")
			Kit.scalable(l, 21)
			l.add_theme_color_override("font_color", Kit.C_AMBER)
			_notes.add_child(l)
			_note_labels[key] = l
	if _note_labels.is_empty() and _notes.get_child_count() == 0:
		var e := Kit.label(Kit.t("mg.flap.notes.empty"), "DimLabel")
		Kit.scalable(e, 21)
		e.name = "Empty"
		_notes.add_child(e)
	elif not _note_labels.is_empty():
		var em := _notes.get_node_or_null("Empty")
		if em != null:
			em.queue_free()
	_redraw()


func _redraw() -> void:
	for v in [_board_view, _hatch_view]:
		if v != null:
			v.queue_redraw()


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y:
		restart()
		return true
	if k == KEY_ENTER or k == KEY_KP_ENTER or pb == JOY_BUTTON_X:
		probe()
		return true
	if _is(event, ["ui_left", "move_left"], true):
		_move_cursor(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		_move_cursor(1)
		return true
	if _is(event, ["ui_down", "move_down"]):
		set_status(Kit.t("mg.flap.status.only_forward"))
		_status_hold = 2.0
		return true
	if k == KEY_UP or k == KEY_W or k == KEY_SPACE or k == KEY_E or pb == JOY_BUTTON_A \
			or _is(event, ["ui_up", "move_up"]):
		if _input_guard <= 0.0:
			turn_selected()
			_repeat = REPEAT_FIRST
			_held = true
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _move_cursor(d: int) -> void:
	var c := clampi(cursor + d, 0, Logic.IDS.size() - 1)
	if c != cursor:
		cursor = c
		Kit.ui_sound("tick")
		_update_ui()


func _drum_at(v: Control, p: Vector2) -> int:
	var a := p / S
	for i in Logic.IDS.size():
		var dr: Dictionary = _drum(i)
		var x := float(dr.get("x", 0))
		var w := float(dr.get("w", 10))
		var y0: float
		var h: float
		if v == _board_view:
			y0 = float((layout.get("row_y", [33]) as Array)[0])
			h = float(layout.get("face_h", 18))
		else:
			var hr: Array = (layout.get("hatch_drums", {}) as Dictionary).get(Logic.IDS[i], [x, 9, w, 17])
			y0 = float(hr[1])
			h = float(hr[3])
		if Rect2(x - 1, y0 - 2, w + 2, h + 4).has_point(a):
			return i
	return -1


func view_input(v: Control, event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and not mb.pressed:
			_mouse_hold = false
			return
		if not mb.pressed:
			return
		var i := _drum_at(v, mb.position)
		if i < 0:
			return
		if cursor != i:
			cursor = i
			_update_ui()
		if mb.button_index == MOUSE_BUTTON_LEFT:
			turn_selected()
			_mouse_hold = true
			_repeat = REPEAT_FIRST
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP or mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			turn_selected()
	elif event is InputEventMouseMotion and not _mouse_hold:
		var j := _drum_at(v, (event as InputEventMouseMotion).position)
		if j >= 0 and j != cursor:
			cursor = j
			_update_ui()


# ================================================================ drawing (art px, x3)
func _drum(i: int) -> Dictionary:
	var ds: Array = layout.get("drums", [])
	return ds[i] if i < ds.size() else {}


func _faces() -> Texture2D:
	if Kit.high_contrast() and _tex.get("flap_faces_hc") != null:
		return _tex["flap_faces_hc"]
	return _tex.get("flap_faces")


func _face_src(i: int, idx: int, top: bool) -> Rect2:
	var dr := _drum(i)
	var w := float(dr.get("w", 10))
	var fh := float(layout.get("face_h", 18))
	var sp := float(layout.get("split", 9))
	var x := idx * w
	var y := float(dr.get("sheet_row", i)) * fh
	return Rect2(x, y, w, sp) if top else Rect2(x, y + sp, w, fh - sp)


func _draw_flap(v: Control, i: int, x: float, y: float) -> void:
	var tex := _faces()
	if tex == null:
		return
	var dr := _drum(i)
	var w := float(dr.get("w", 10))
	var fh := float(layout.get("face_h", 18))
	var sp := float(layout.get("split", 9))
	var n := Logic.flap_count(i)
	var cur := int(shown[i]) if i < shown.size() else 0
	var p := float(_flip[i]) if i < _flip.size() else 0.0
	if _stuck.has(i):
		p = 0.42
	if int(_queue[i]) <= 0 and not _stuck.has(i):
		v.draw_texture_rect_region(tex, Rect2(x, y, w, sp), _face_src(i, cur, true))
		v.draw_texture_rect_region(tex, Rect2(x, y + sp, w, fh - sp), _face_src(i, cur, false))
		return
	var nxt := (cur + 1) % n
	# behind: the next card's top half above the split, the current card's bottom half below it
	v.draw_texture_rect_region(tex, Rect2(x, y, w, sp), _face_src(i, nxt, true))
	v.draw_texture_rect_region(tex, Rect2(x, y + sp, w, fh - sp), _face_src(i, cur, false))
	var shade := Color(0.55, 0.55, 0.6)
	if p < 0.5:      # the current top half falls towards the viewer (compressed onto the split line)
		var h := roundf(sp * (1.0 - 2.0 * p))
		if h >= 1.0:
			v.draw_texture_rect_region(tex, Rect2(x, y + sp - h, w, h), _face_src(i, cur, true),
				Color(1, 1, 1).lerp(shade, p * 1.4))
	else:            # its back is the next card's bottom half, unfolding below the split
		var h2 := roundf((fh - sp) * (2.0 * p - 1.0))
		if h2 >= 1.0:
			v.draw_texture_rect_region(tex, Rect2(x, y + sp, w, h2), _face_src(i, nxt, false),
				shade.lerp(Color(1, 1, 1), (p - 0.5) * 2.0))
	if _stuck.has(i):   # the stuck card trembles a little
		var jig := 1.0 if fmod(_anim * 7.0 + i, 3.0) < 0.4 else 0.0
		v.draw_rect(Rect2(x, y + sp - 1 - jig, w, 1), Color(COL_IRON[3], 0.8))


func draw_board(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var bt: Texture2D = _tex.get("flap_board")
	if bt != null:
		v.draw_texture(bt, Vector2.ZERO)
	else:
		v.draw_rect(Rect2(Vector2.ZERO, v.size / S), COL_IRON[1])
	var y0 := float((layout.get("row_y", [33]) as Array)[0])
	var bounce := 0.0
	if _engaged >= 0.0 and _engaged < 0.12 and not Kit.reduced_motion():
		bounce = -1.0
	for i in Logic.IDS.size():
		var dr := _drum(i)
		_draw_flap(v, i, float(dr.get("x", 0)), y0 + bounce)
	# row lamp: red blinking while jammed, steady amber once engaged
	var lr: Array = layout.get("row_lamp", [7, 7, 3, 4])
	var lamp := Rect2(float(lr[0]), y0 + float(lr[1]), float(lr[2]), float(lr[3]))
	if solved:
		v.draw_rect(lamp, COL_AMBER)
	elif fmod(_anim, 1.6) < 0.8:
		v.draw_rect(lamp, COL_RED)
	# the new KARSK card gleams once when the line engages
	if _engaged >= 0.0 and _engaged < 1.2:
		var vi := Logic.index_of("via")
		var dv := _drum(vi)
		var a := clampf(1.0 - _engaged / 1.2, 0.0, 1.0)
		v.draw_rect(Rect2(float(dv.get("x", 0)) - 1, y0 - 1, float(dv.get("w", 10)) + 2, 20), Color(COL_SNOW, 0.55 * a), false, 1.0)
	# cursor: amber frame around the chosen drum and a notch below it
	if not solved:
		var dc := _drum(cursor)
		var cx := float(dc.get("x", 0))
		var cw := float(dc.get("w", 10))
		var hc := Kit.high_contrast()
		var col := COL_SNOW if hc else COL_AMBER
		v.draw_rect(Rect2(cx - 1.5, y0 - 1.5, cw + 3, 21), col, false, 1.0)
		if hc:
			v.draw_rect(Rect2(cx - 2.5, y0 - 2.5, cw + 5, 23), Color(0, 0, 0), false, 1.0)
		var mx := roundf(cx + cw / 2.0)
		v.draw_colored_polygon(PackedVector2Array([Vector2(mx - 2, y0 + 21), Vector2(mx + 3, y0 + 21), Vector2(mx + 0.5, y0 + 18.5)]), col)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func draw_hatch(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var ht: Texture2D = _tex.get("flap_hatch")
	if ht != null:
		v.draw_texture(ht, Vector2.ZERO)
	var hd: Dictionary = layout.get("hatch_drums", {})
	for i in Logic.IDS.size():
		var r: Array = hd.get(Logic.IDS[i], [_drum(i).get("x", 0), 9, _drum(i).get("w", 10), 17])
		var x := float(r[0])
		var y := float(r[1])
		var w := float(r[2])
		var h := float(r[3])
		# a drum of cards seen edge-on: lit from above, card edges every 3 px scroll as it turns (whole art px)
		v.draw_rect(Rect2(x, y, w, h), COL_IRON[2])
		v.draw_rect(Rect2(x, y + h * 0.6, w, h * 0.4), COL_IRON[1])
		var ph := int(floor(float(_phase[i]) if i < _phase.size() else 0.0)) % 3
		var yy := y + 1 + ph
		while yy < y + h - 1:
			var top := yy < y + h * 0.5
			v.draw_rect(Rect2(x, yy, w, 1), COL_IRON[4] if top else COL_IRON[3])
			yy += 3
		v.draw_rect(Rect2(x, y, w, 1), Color("8593a3"))
		v.draw_rect(Rect2(x, y + h - 1, w, 1), COL_NIGHT0)
		# the card that faces the window is the one on the board: a cream line marks it
		v.draw_rect(Rect2(x + 1, y + 2, w - 2, 1), Color("9e9076") if int(_queue[i]) <= 0 else COL_IRON[4])
		if i == cursor and not solved:
			v.draw_rect(Rect2(x - 1, y - 1, w + 2, h + 2), COL_SNOW if Kit.high_contrast() else COL_AMBER, false, 1.0)
	# couplings Alexei has seen work light up
	for c in layout.get("couplings", []):
		var key := "%s>%s" % [str(c.get("from", "")), str(c.get("to", ""))]
		if logic.known.has(key):
			var cr: Array = c.get("rect", [0, 0, 1, 1])
			v.draw_rect(Rect2(float(cr[0]), float(cr[1]), float(cr[2]), float(cr[3])), COL_AMBER, false, 1.0)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 90000:
		var d: int = logic.next_drum()
		if d < 0:
			await _frames(2)
			continue
		while cursor != d and not ended and Time.get_ticks_msec() - t0 < 90000:
			await _tap(KEY_RIGHT if cursor < d else KEY_LEFT)
		var guard := 0
		while not logic.on_target(d) and not ended and guard < 30:
			await _tap(KEY_UP)
			guard += 1
	await _until(func(): return solved, 4.0)
