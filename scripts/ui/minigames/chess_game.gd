extends "res://scripts/ui/minigames/minigame_base.gd"
## Karsk "Die Schachpartie" (scenes/ui/minigames/ChessProblem.tscn, explore entry karsk.chess, §12.8).
## The peg-chess game of the day and night shift, laid out on a crate lid next to the cache under the signal-box
## stairs (assets/ui/minigames/chess_*.png, stored x3). Mate in two for the day shift (White); logic and the
## hard-coded solution lines live in chess_logic.gd, the night shift answers by itself.
## Keys: arrows / WASD / d-pad move the cursor, Enter / Space / E / A pick up and set down, Esc puts a picked-up
## piece back (else gives up), R / pad Y sets the position up again. Mouse: click a piece, click its square.

const Logic := preload("res://scripts/ui/minigames/chess_logic.gd")
const SQ := 19
const OFF := 10
const S := 3
const CELL := Vector2(18, 20)
const ORDER := "KQRBNP"
const SLIDE := 0.24
const REPLY_DELAY := 0.9

var logic = Logic.new()
var cursor := Vector2i(4, 0)
var selected := ""
var _board_view: Control
var _tex_board: Texture2D
var _tex_pieces: Texture2D
var _anim: Dictionary = {}       # {"piece", "from", "to", "t"}
var _reply_in := -1.0
var _moves_label: Label
var _turn_label: Label
var _hover := Vector2i(-1, -1)


class BoardView extends Control:
	var game: Node

	func _draw() -> void:
		game.draw_board(self)

	func _gui_input(event: InputEvent) -> void:
		game.board_input(event)


func _build_play(area: Control) -> void:
	set_texts("mg.chess.kicker", "mg.chess.title", "mg.chess.subtitle", "mg.chess.instruction")
	_tex_board = Kit.optional_tex(DIR + "chess_board.png")
	_tex_pieces = Kit.optional_tex(DIR + "chess_pieces.png")
	var row := Kit.hbox(48)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	_board_view = BoardView.new()
	_board_view.game = self
	_board_view.mouse_filter = Control.MOUSE_FILTER_STOP
	_board_view.custom_minimum_size = _tex_board.get_size() if _tex_board != null else Vector2(516, 516)
	_board_view.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_board_view)
	var side := Kit.vbox(16)
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	side.custom_minimum_size.x = 520
	row.add_child(side)
	_turn_label = Kit.label("", "KickerLabel")
	side.add_child(_turn_label)
	var sides := Kit.wrap_label(Kit.t("mg.chess.sides"), "BodyLabel")
	Kit.scalable(sides, 25)
	side.add_child(sides)
	var card := Kit.panel("PaperCardPanel")
	side.add_child(card)
	var col := Kit.vbox(8)
	card.add_child(col)
	col.add_child(Kit.label(Kit.t("mg.chess.note.kicker").to_upper().replace("ß", "SS"), "PaperKicker"))
	var note := Kit.wrap_label(Kit.t("mg.chess.note"), "PaperBody")
	Kit.scalable(note, 24)
	col.add_child(note)
	col.add_child(Kit.rule(Kit.C_PAPER_D, 2))
	col.add_child(Kit.label(Kit.t("mg.chess.moves").to_upper().replace("ß", "SS"), "PaperKicker"))
	_moves_label = Kit.label("", "", 30, Kit.C_INK)
	_moves_label.add_theme_font_override("font", Kit.font("fv_serif_bold"))
	_moves_label.custom_minimum_size.y = 44
	col.add_child(_moves_label)


func _reset_game() -> void:
	logic.reset()
	selected = ""
	cursor = Vector2i(4, 0)
	_anim = {}
	_reply_in = -1.0
	_update_ui()


func _update_ui() -> void:
	var parts: Array = []
	for k in logic.history:
		parts.append(Kit.t(str(k)))
	if _moves_label:
		_moves_label.text = "  ".join(parts) if not parts.is_empty() else "…"
	if _turn_label:
		_turn_label.text = Kit.t("mg.chess.turn.night" if logic.phase == 1 else "mg.chess.turn.day").to_upper().replace("ß", "SS")
	if not solved:
		if logic.phase == 1:
			status_auto(Kit.t("mg.chess.status.reply"))
		elif selected != "":
			clear_status_hold()
			set_status(Kit.t("mg.chess.status.target", {"piece": _piece_name(logic.piece_at(selected))}))
		elif logic.phase == 2:
			status_auto(Kit.t("mg.chess.status.second"))
		else:
			status_auto(Kit.t("mg.chess.status.pick"))
	if _board_view:
		_board_view.queue_redraw()


func _piece_name(p: String) -> String:
	return Kit.t("mg.chess.piece." + (p[1] if p.length() > 1 else "P"))


# ================================================================ moves
func _activate(sq: String) -> void:
	if _anim.size() > 0 or logic.phase == 1 or solved:
		return
	var p := logic.piece_at(sq)
	if selected == "":
		if p == "":
			return
		if p[0] != "w":
			register_fail(Kit.t("mg.chess.fail.night"))
			return
		selected = sq
		Kit.ui_sound("move")
		_update_ui()
		return
	if sq == selected:
		selected = ""
		_update_ui()
		return
	if p != "" and p[0] == "w":       # switch to another day-shift piece
		selected = sq
		Kit.ui_sound("move")
		_update_ui()
		return
	var from := selected
	var piece := logic.piece_at(from)
	var r: Dictionary = logic.try_move(from, sq)
	selected = ""
	if not bool(r.get("ok", false)):
		var reason := str(r.get("reason", "nomate"))
		if reason == "illegal":
			register_fail(Kit.t("mg.chess.fail.illegal", {"piece": _piece_name(piece)}))
		else:
			register_fail(Kit.t("mg.chess.fail." + reason))
		_update_ui()
		return
	_start_anim(piece, from, sq)
	if bool(r.get("mate", false)):
		mark_solved(Kit.t("mg.chess.solved"))
	elif logic.phase == 1:
		clear_status_hold()
		_reply_in = REPLY_DELAY
	_update_ui()


func _start_anim(piece: String, from: String, to: String) -> void:
	_anim = {"piece": piece, "from": from, "to": to, "t": 0.0}


func _tick(delta: float) -> void:
	if _anim.size() > 0:
		_anim["t"] = float(_anim["t"]) + delta
		if float(_anim["t"]) >= SLIDE:
			_anim = {}
			_sfx("mg_chess_tap", -2.0)
		if _board_view:
			_board_view.queue_redraw()
	if _reply_in >= 0.0 and _anim.size() == 0:
		_reply_in -= delta
		if _reply_in < 0.0:
			var piece := logic.piece_at(Logic.REPLY[0])
			var mv: Array = logic.reply()
			if mv.size() == 2:
				_start_anim(piece, mv[0], mv[1])
			_update_ui()


func _cancel_step() -> bool:
	if selected != "":
		selected = ""
		Kit.ui_sound("back")
		_update_ui()
		return true
	return false


func _hint_text(level: int) -> String:
	if logic.phase >= 2:
		return Kit.t("mg.chess.hint.b1" if level <= 1 else "mg.chess.hint.b2")
	return Kit.t("mg.chess.hint.%d" % clampi(level, 1, 3))


func register_fail(text: String) -> void:
	super.register_fail(text)
	if _board_view:
		_board_view.queue_redraw()


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT) + "|" + Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN),
			Kit.t("mg.chess.ctrl.cursor")],
		[Kit.action_key_text("interact"), Kit.t("mg.chess.ctrl.pick")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	if k == KEY_R or _pad(event) == JOY_BUTTON_Y:
		restart()
		return true
	var d := Vector2i.ZERO
	if _is(event, ["ui_left", "move_left"], true):
		d = Vector2i(-1, 0)
	elif _is(event, ["ui_right", "move_right"], true):
		d = Vector2i(1, 0)
	elif _is(event, ["ui_up", "move_up"], true):
		d = Vector2i(0, 1)
	elif _is(event, ["ui_down", "move_down"], true):
		d = Vector2i(0, -1)
	if d != Vector2i.ZERO:
		cursor = Vector2i(clampi(cursor.x + d.x, 0, 7), clampi(cursor.y + d.y, 0, 7))
		Kit.ui_sound("tick")
		if _board_view:
			_board_view.queue_redraw()
		return true
	if _is(event, ["ui_accept", "interact"]):
		_activate(Logic.sq_name(cursor.x, cursor.y))
		return true
	return false


func _square_at(p: Vector2) -> Vector2i:
	var a := p / S - Vector2(OFF, OFF)
	var f := int(floor(a.x / SQ))
	var r := 7 - int(floor(a.y / SQ))
	if f < 0 or f > 7 or r < 0 or r > 7:
		return Vector2i(-1, -1)
	return Vector2i(f, r)


func board_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseMotion:
		var s := _square_at((event as InputEventMouseMotion).position)
		if s != _hover:
			_hover = s
			if s.x >= 0:
				cursor = s
			_board_view.queue_redraw()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var s2 := _square_at((event as InputEventMouseButton).position)
		if s2.x >= 0:
			cursor = s2
			_activate(Logic.sq_name(s2.x, s2.y))
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
		_cancel_step()


# ================================================================ drawing
func _sq_rect(f: int, r: int) -> Rect2:
	return Rect2(Vector2(OFF + f * SQ, OFF + (7 - r) * SQ) * S, Vector2(SQ, SQ) * S)


func _draw_piece(v: Control, piece: String, top_left: Vector2) -> void:
	if _tex_pieces == null or piece.length() < 2:
		return
	var i := ORDER.find(piece[1])
	var row := 0 if piece[0] == "w" else 1
	var src := Rect2(Vector2(i * CELL.x, row * CELL.y) * S, CELL * S)
	v.draw_texture_rect_region(_tex_pieces, Rect2(top_left, CELL * S), src)


func _piece_pos(sq: String) -> Vector2:
	var c := Logic.coords(sq)
	return _sq_rect(c.x, c.y).position + Vector2(0, -2 * S)


func draw_board(v: Control) -> void:
	if _tex_board != null:
		v.draw_texture(_tex_board, Vector2.ZERO)
	var font := v.get_theme_font("font", "Label")
	# coordinates on the crate frame
	for i in 8:
		var rr := _sq_rect(i, 0)
		v.draw_string(font, Vector2(rr.position.x, (OFF + 8 * SQ) * S + 26), Logic.FILES[i], HORIZONTAL_ALIGNMENT_CENTER,
			SQ * S, 18, Color(Kit.C_PAPER, 0.8))
		var rl := _sq_rect(0, i)
		v.draw_string(font, Vector2(2, rl.position.y + SQ * S * 0.5 + 7), str(i + 1), HORIZONTAL_ALIGNMENT_CENTER,
			OFF * S - 4, 18, Color(Kit.C_PAPER, 0.8))
	# last move
	if logic.last_move.size() == 2:
		for s in logic.last_move:
			var c := Logic.coords(str(s))
			v.draw_rect(_sq_rect(c.x, c.y), Color(Kit.C_AMBER, 0.22))
	# selection + its targets
	if selected != "":
		var cs := Logic.coords(selected)
		v.draw_rect(_sq_rect(cs.x, cs.y), Color(Kit.C_AMBER, 0.42))
		for t in logic.targets(selected):
			var ct := Logic.coords(str(t))
			var rc := _sq_rect(ct.x, ct.y)
			v.draw_rect(Rect2(rc.get_center() - Vector2(6, 6), Vector2(12, 12)), Color(Kit.C_NIGHT, 0.55))
	# pieces (the moving one last)
	var moving := ""
	if _anim.size() > 0:
		moving = str(_anim["to"])
	for s in logic.board:
		if str(s) == moving:
			continue
		_draw_piece(v, str(logic.board[s]), _piece_pos(str(s)))
	if moving != "":
		var f := clampf(float(_anim["t"]) / SLIDE, 0.0, 1.0)
		f = f * f * (3.0 - 2.0 * f)
		var p: Vector2 = _piece_pos(str(_anim["from"])).lerp(_piece_pos(moving), f)
		p = (p / S).round() * S
		_draw_piece(v, str(_anim["piece"]), p + Vector2(0, -sin(f * PI) * 18.0))
	# cursor
	if not solved:
		var cr := _sq_rect(cursor.x, cursor.y)
		v.draw_rect(cr.grow(-2), Kit.C_COPPER_L, false, 4.0)
	# mate stamp
	if solved:
		var txt := Kit.t("mg.chess.mate")
		var fs := 64
		var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var c0 := v.size / 2.0
		v.draw_set_transform(c0, -0.12, Vector2.ONE)
		var box := Rect2(Vector2(-w / 2 - 24, -48), Vector2(w + 48, 84))
		v.draw_rect(box, Color(Kit.C_PAPER, 0.88))
		v.draw_rect(box, Kit.C_STAMP, false, 5.0)
		v.draw_string(font, Vector2(-w / 2, 18), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Kit.C_STAMP)
		v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# ================================================================ synthetic solve (real-input driver)
func _cursor_to(target: String) -> void:
	var c := Logic.coords(target)
	var guard := 0
	while cursor != c and guard < 20 and not ended:
		if cursor.x < c.x:
			await _tap(KEY_RIGHT)
		elif cursor.x > c.x:
			await _tap(KEY_LEFT)
		elif cursor.y < c.y:
			await _tap(KEY_UP)
		else:
			await _tap(KEY_DOWN)
		guard += 1


func demo_solve() -> void:
	await _tap(KEY_R)
	for mv in [Logic.KEY_MOVE, Logic.MATE]:
		if ended or solved:
			return
		await _until(func(): return _anim.size() == 0 and logic.phase != 1, 6.0)
		await _cursor_to(str(mv[0]))
		await _tap(KEY_ENTER)
		await _cursor_to(str(mv[1]))
		await _tap(KEY_ENTER)
