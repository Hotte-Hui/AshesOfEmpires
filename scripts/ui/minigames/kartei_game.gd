extends "res://scripts/ui/minigames/minigame_base.gd"
## Registry "Die Suchkartei" (scenes/ui/minigames/Kartei.tscn, explore entry veltrava.registry.kartei, §12.8,
## documentation/C3P2_DESIGN.md §7). Night, the card hall of the commission's registry: beside drawer C-17 a drawer
## of the tracing index lies on the floor -- whoever emptied C-17 in a hurry tore it down. Konrad files the nine
## cards back: origin (B · K · V), year, running number. Four cards were written by Russian-speaking clerks; their
## origin letter is Cyrillic, and the В of Veltrava looks like a Latin B. While he sorts, the side panel reads each
## card: people who have been looking for someone across the Line since the armistice. Quiet, no timer, no penalty.
## Logic: kartei_logic.gd. Art: assets/ui/minigames/kartei/ (tools/pixelgen/gen_mg_c3p2_kartei.py, 1:1 art px,
## drawn x3, x2 for larger text). Sounds: mg_c3p2_* (tools/audiogen/mg_audio_c3p2.py).
## Keys: Left/Right (A/D, d-pad) choose a card on the floor / a gap in the drawer · E, Enter, Space or pad A take
## the card / file it · Backspace (or Esc while holding) puts it back · R or pad Y starts over · Esc gives up.
## Mouse: point at a card and click to take it, point into the drawer and click to file it, right click puts back.

const Logic := preload("res://scripts/ui/minigames/kartei_logic.gd")
const ART := "res://assets/ui/minigames/kartei/"
const COL_AMBER := Color("e9b46e")
const COL_WHITE := Color("f5efda")
const COL_RED := Color("c8503c")
const GAP_OPEN := 12.0
const DROP_T := 0.2
const CITY := {"B": {"de": "BERLIN", "ru": "БЕРЛИН"}, "K": {"de": "KARSK", "ru": "КАРСК"},
	"V": {"de": "VELTRAVA", "ru": "ВЕЛЬТРАВА"}}

var logic = Logic.new()
## Art scale: x3, or x2 in the compact layout for larger text (set in _build_play).
var S := 3
var compact := false
var layout: Dictionary = {}
var cursor := 0          # index into logic.floor (the card the floor cursor is on)
var caret := 0           # gap in the drawer while a card is held
var _tex: Dictionary = {}
var _scene: Control
var _progress: Label
var _legend: Label
var _code_label: Label
var _lang_label: Label
var _text_label: Label
var _result_label: Label
var _btn_main: Button
var _btn_back: Button
var _disp_x: Dictionary = {}     # drawer item id -> displayed x (slides when a gap opens)
var _drop: Dictionary = {}       # card id -> seconds since it was filed
var _shake := 0.0
var _anim := 0.0
var _input_guard := 0.0
var _last_card := ""


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_scene", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("scene_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.kartei.kicker", "mg.kartei.title", "mg.kartei.subtitle", "mg.kartei.instruction")
	var lj = Kit.json(ART + "kartei_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["kartei_back", "kartei_front", "kartei_tabs", "kartei_faces"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	compact = Kit.text_scale() > 1.01
	S = 2 if compact else 3
	if compact:      # larger text: the side panel carries the rule, so flavour and instruction give way
		_subtitle.visible = false
		_instr.visible = false
	var row := Kit.hbox(36)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var sz: Array = layout.get("size", [400, 136])
	var left := Kit.vbox(10)
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(left)
	var v := View.new()
	v.game = self
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.custom_minimum_size = Vector2(float(sz[0]), float(sz[1])) * S
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	_scene = v
	left.add_child(v)
	area.custom_minimum_size.y = float(sz[1]) * S       # the stage reserves its height in the panel's column
	var side := Kit.vbox(8)
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	side.custom_minimum_size.x = 860 if compact else 500
	row.add_child(side)
	_progress = Kit.wrap_label("", "KickerLabel")
	side.add_child(_progress)
	# the alphabet of the drawer: under the stage when the text is large (the side column is busy), else on top
	_legend = Kit.wrap_label(Kit.t("mg.kartei.legend"), "DimLabel")
	Kit.scalable(_legend, 21)
	if compact:
		_legend.custom_minimum_size.x = float(sz[0]) * S
		left.add_child(_legend)
	else:
		side.add_child(_legend)
	var card := Kit.panel("PlatePanel")
	side.add_child(card)
	var col := Kit.vbox(4)
	card.add_child(col)
	_code_label = Kit.label("", "HeadingLabel")
	Kit.scalable(_code_label, 36)
	col.add_child(_code_label)
	_lang_label = Kit.wrap_label("", "DimLabel")
	Kit.scalable(_lang_label, 21)
	col.add_child(_lang_label)
	_text_label = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_text_label, 21)
	col.add_child(_text_label)
	_result_label = Kit.label("", "KickerLabel")
	col.add_child(_result_label)
	_btn_back = _add_button(Kit.t("mg.kartei.btn.back"), put_back, 250, true)
	_btn_main = _add_button(Kit.t("mg.kartei.btn.take"), act, 250, true)


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.3
	set_status(Kit.t("mg.kartei.status.start"))
	_status_hold = 2.6


func _reset_game() -> void:
	logic.reset()
	cursor = 0
	caret = 0
	_drop = {}
	_disp_x = {}
	_shake = 0.0
	_snap_items()
	_update_ui()


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	set_status(Kit.t("mg.kartei.status.floor"))
	_status_hold = 1.2


# ================================================================ actions
## Take the card under the floor cursor, or file the held card at the caret.
func act() -> void:
	if solved or ended:
		return
	if logic.held != "":
		place(caret)
	elif not logic.floor.is_empty():
		take(str(logic.floor[clampi(cursor, 0, logic.floor.size() - 1)]))


func take(id: String) -> void:
	if solved or ended:
		return
	if logic.held != "" and logic.held != id:
		logic.put_back()
	if logic.take(id):
		cursor = logic.floor.find(id)
		caret = clampi(caret, 0, logic.drawer.size())
		_sfx("mg_c3p2_card_take", -4.0)
		clear_status_hold()
		_update_ui()


func put_back() -> void:
	if solved or ended:
		return
	if logic.put_back():
		_sfx("mg_c3p2_card_take", -9.0)
		set_status(Kit.t("mg.kartei.status.back"))
		_status_hold = 1.0
		_update_ui()


func place(gap: int) -> void:
	if solved or ended or logic.held == "":
		return
	var id: String = logic.held
	var r: Dictionary = logic.insert(gap)
	if bool(r.get("ok", false)):
		_drop[id] = 0.0
		_disp_x[id] = _item_target_x(logic.drawer.find(id))
		_sfx("mg_c3p2_card_file", -3.0)
		_last_card = id
		cursor = clampi(cursor, 0, maxi(0, logic.floor.size() - 1))
		if logic.done:
			_sfx("mg_c3p2_drawer_shut", -2.0)
			mark_solved(Kit.t("mg.kartei.solved"))
		else:
			clear_status_hold()
			set_status(Kit.t("mg.kartei.status.filed", {"code": Logic.code(id)}))
			_status_hold = 1.4
		_update_ui()
		return
	_shake = 0.3
	_sfx("mg_c3p2_rattle", -6.0)
	register_fail(Kit.t("mg.kartei.fail." + str(r.get("reason", "origin"))))
	_update_ui()


func _cancel_step() -> bool:
	if logic.held != "" and not solved:
		put_back()
		return true
	return false


func _move(d: int) -> void:
	if logic.held != "":
		var c := clampi(caret + d, 0, logic.drawer.size())
		if c != caret:
			caret = c
			Kit.ui_sound("tick")
		return
	if logic.floor.is_empty():
		return
	var n := clampi(cursor + d, 0, logic.floor.size() - 1)
	if n != cursor:
		cursor = n
		Kit.ui_sound("tick")
		_update_ui()


# ================================================================ hints
func _hint_text(level: int) -> String:
	if logic.done:
		return ""
	if level >= 2:
		var id: String = logic.held
		if id == "" and not logic.floor.is_empty():
			id = str(logic.floor[clampi(cursor, 0, logic.floor.size() - 1)])
		if id != "":
			var nb: Array = logic.neighbors(logic.valid_gap(id))
			return Kit.t("mg.kartei.hint.gap", {"code": Logic.code(id), "left": _item_label(str(nb[0])),
				"right": _item_label(str(nb[1]))})
	return Kit.t("mg.kartei.hint.1")


func _item_label(id: String) -> String:
	if id == "":
		return Kit.t("mg.kartei.end")
	if Logic.is_guide(id):
		return Kit.t("mg.kartei.guide", {"o": Logic.origin(id)})
	return "‚%s‘" % Logic.code(id)


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
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.kartei.ctrl.choose")],
		[Kit.action_key_text("interact"), Kit.t("mg.kartei.ctrl.take")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("mg.kartei.ctrl.back")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	_shake = maxf(0.0, _shake - delta)
	for k in _drop.keys():
		_drop[k] = float(_drop[k]) + delta
		if float(_drop[k]) > DROP_T:
			_drop.erase(k)
	var f := 1.0 if Kit.reduced_motion() else minf(1.0, delta * 14.0)
	for i in logic.drawer.size():
		var id := str(logic.drawer[i])
		var t := _item_target_x(i)
		_disp_x[id] = lerpf(float(_disp_x.get(id, t)), t, f)
	if not solved:
		if logic.held != "":
			status_auto(Kit.t("mg.kartei.status.hold", {"code": Logic.code(logic.held)}))
		else:
			status_auto(Kit.t("mg.kartei.status.floor"))
	if _scene != null:
		_scene.queue_redraw()


func _snap_items() -> void:
	for i in logic.drawer.size():
		_disp_x[str(logic.drawer[i])] = _item_target_x(i)


func _item_target_x(i: int) -> float:
	var x := float(layout.get("x0", 22)) + float(i) * float(layout.get("slot_w", 22))
	if logic.held != "" and i >= caret:
		x += GAP_OPEN
	return x


## The card the side panel reads: the one in the hand, else the one under the floor cursor, else the last filed.
func shown_card() -> String:
	if logic.held != "":
		return logic.held
	if not logic.floor.is_empty():
		return str(logic.floor[clampi(cursor, 0, logic.floor.size() - 1)])
	return _last_card


func _update_ui() -> void:
	if _progress == null:
		return
	var total: int = Logic.FLOOR.size()
	var state := Kit.t("mg.kartei.kicker.held" if logic.held != "" else "mg.kartei.kicker.floor")
	var rule := ("  ·  " + Kit.t("mg.kartei.rule_short")) if compact else ""      # x3: the instruction states the rule
	_progress.text = (Kit.t("mg.kartei.progress", {"n": logic.filed.size(), "total": total}) + rule + "  ·  " + state) 		.to_upper().replace("ß", "SS")
	var id := shown_card()
	if id != "" and Logic.CARDS.has(id):
		var c: Dictionary = Logic.CARDS[id]
		_code_label.text = str(c["code"])
		_lang_label.text = Kit.t("mg.kartei.lang." + str(c["lang"])) + " · " + 			Kit.t("mg.kartei.place_fmt", {"place": CITY[str(c["origin"])][str(c["lang"])]})
		_text_label.text = Kit.t("mg.kartei.card." + id) if Kit.has_key("mg.kartei.card." + id) else ""
		_result_label.text = Kit.t("mg.kartei.result_fmt", {"result": Kit.t("mg.kartei.result." + str(c["result"]))}).to_upper().replace("ß", "SS")
	if _btn_main != null:
		_btn_main.text = Kit.t("mg.kartei.btn.place" if logic.held != "" else "mg.kartei.btn.take")
		_btn_back.disabled = logic.held == ""
	if _hint_box != null and _hint_box.visible and not logic.done:
		_hint_label.text = _hint_text(maxi(1, hint_level))


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y:
		restart()
		return true
	if _is(event, ["ui_left", "move_left"], true):
		_move(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		_move(1)
		return true
	if k == KEY_BACKSPACE:
		put_back()
		return true
	if _is(event, ["ui_accept", "interact"]) or k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE or k == KEY_E \
			or pb == JOY_BUTTON_A:
		if _input_guard <= 0.0:
			act()
		return true
	if _is(event, ["ui_up", "move_up", "ui_down", "move_down"], true):
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _floor_rect(id: String) -> Rect2:
	var p: Array = (layout.get("floor", {}) as Dictionary).get(id, [0, 0])
	var fc: Array = layout.get("face_cell", [46, 30])
	var r := Rect2(float(p[0]), float(p[1]), float(fc[0]), float(fc[1]))
	if id == logic.held:
		r.position.y -= float(layout.get("lift", 8))
	return r


func _gap_at(x: float) -> int:
	var x0 := float(layout.get("x0", 22))
	var sw := float(layout.get("slot_w", 22))
	return clampi(int(round((x - x0) / sw)), 0, logic.drawer.size())


func scene_input(event: InputEvent) -> void:
	if ended or solved:
		return
	var p: Vector2
	var click := 0
	if event is InputEventMouseMotion:
		p = (event as InputEventMouseMotion).position / S
	elif event is InputEventMouseButton and event.pressed:
		var mb := event as InputEventMouseButton
		p = mb.position / S
		click = 1 if mb.button_index == MOUSE_BUTTON_LEFT else (2 if mb.button_index == MOUSE_BUTTON_RIGHT else 0)
		if click == 0:
			return
	else:
		return
	if click == 2:
		put_back()
		return
	# the drawer (top band): choose / use a gap while holding a card
	if p.y < float(layout.get("front_y", 42)) + 24.0:
		if logic.held != "":
			var g := _gap_at(p.x)
			if g != caret:
				caret = g
			if click == 1 and _input_guard <= 0.0:
				place(caret)
		return
	for i in range(logic.floor.size() - 1, -1, -1):
		var id := str(logic.floor[i])
		if _floor_rect(id).has_point(p):
			if logic.held == "" and cursor != i:
				cursor = i
				_update_ui()
			if click == 1 and _input_guard <= 0.0:
				if logic.held == id:
					put_back()
				else:
					take(id)
			return


# ================================================================ drawing (art px, x S)
func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var hc := Kit.high_contrast()
	var bt: Texture2D = _tex.get("kartei_back")
	if bt != null:
		v.draw_texture(bt, Vector2.ZERO)
	# the drawer: guides and cards, in order
	var tabs: Texture2D = _tex.get("kartei_tabs")
	var tc: Array = layout.get("tab_cell", [22, 36])
	var order: Array = layout.get("tabs", [])
	var ty := float(layout.get("tab_y", 6))
	var sx := 0.0
	if _shake > 0.0 and not Kit.reduced_motion():
		sx = 1.0 if fmod(_shake * 30.0, 2.0) < 1.0 else -1.0
	for i in logic.drawer.size():
		var id := str(logic.drawer[i])
		var cell := order.find(id)
		if tabs == null or cell < 0:
			continue
		var dy := 0.0
		if _drop.has(id) and not Kit.reduced_motion():
			dy = -roundf(10.0 * (1.0 - float(_drop[id]) / DROP_T))
		var x := roundf(float(_disp_x.get(id, _item_target_x(i)))) + sx
		v.draw_texture_rect_region(tabs, Rect2(x, ty + dy, float(tc[0]), float(tc[1])),
			Rect2(cell * float(tc[0]), 0, float(tc[0]), float(tc[1])))
	var ft: Texture2D = _tex.get("kartei_front")
	if ft != null:
		v.draw_texture(ft, Vector2.ZERO)
	# the caret: where the card in the hand would go
	if logic.held != "" and not solved:
		var cx := float(layout.get("x0", 22)) + float(caret) * float(layout.get("slot_w", 22)) + GAP_OPEN * 0.5 - 1.0
		var car: Array = layout.get("caret", [2, 44])
		var col := COL_WHITE if hc else COL_AMBER
		var blink := 1.0 if (Kit.reduced_motion() or fmod(_anim, 0.9) < 0.6) else 0.55
		if hc:
			v.draw_rect(Rect2(cx - 1.0, float(car[0]) - 1.0, 4.0, float(car[1]) - float(car[0]) + 2.0), Color(0, 0, 0))
		v.draw_rect(Rect2(cx, float(car[0]), 2.0, float(car[1]) - float(car[0])), Color(col, blink))
		v.draw_colored_polygon(PackedVector2Array([Vector2(cx - 3, 0), Vector2(cx + 5, 0), Vector2(cx + 1, 4)]), col)
	# the floor: every card still lying there; the one in the hand is lifted (drawn last)
	var faces: Texture2D = _tex.get("kartei_faces")
	var fcell: Array = layout.get("face_cell", [46, 30])
	var forder: Array = layout.get("faces", [])
	for id in logic.floor:
		if str(id) == logic.held:
			continue
		_draw_face(v, faces, forder, fcell, str(id), 0.0)
	if logic.held != "":
		var bob := 0.0 if Kit.reduced_motion() else (-1.0 if fmod(_anim * 1.6, 2.0) < 1.0 else 0.0)
		_draw_face(v, faces, forder, fcell, logic.held, bob)
	# the floor cursor
	if logic.held == "" and not solved and not logic.floor.is_empty():
		var r := _floor_rect(str(logic.floor[clampi(cursor, 0, logic.floor.size() - 1)]))
		var col2 := COL_WHITE if hc else COL_AMBER
		v.draw_rect(r.grow(1.5), col2, false, 1.0)
		if hc:
			v.draw_rect(r.grow(2.5), Color(0, 0, 0), false, 1.0)
		var mx := roundf(r.get_center().x)
		v.draw_colored_polygon(PackedVector2Array([Vector2(mx - 3, r.position.y - 6), Vector2(mx + 4, r.position.y - 6),
			Vector2(mx + 0.5, r.position.y - 2.5)]), col2)
	if logic.held != "":
		var hr := _floor_rect(logic.held)
		v.draw_rect(hr.grow(1.5), COL_WHITE if hc else COL_AMBER, false, 1.0)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_face(v: Control, faces: Texture2D, order: Array, fcell: Array, id: String, bob: float) -> void:
	var cell := order.find(id)
	if faces == null or cell < 0:
		return
	var r := _floor_rect(id)
	r.position.y += bob
	if id == logic.held:
		v.draw_rect(Rect2(r.position + Vector2(2, float(layout.get("lift", 8)) + 1.0), r.size), Color(0, 0, 0, 0.45))
	else:
		v.draw_rect(Rect2(r.position + Vector2(1, 1), r.size), Color(0, 0, 0, 0.35))
	v.draw_texture_rect_region(faces, r, Rect2(cell * float(fcell[0]), 0, float(fcell[0]), float(fcell[1])))


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 90000:
		if logic.held == "":
			await _tap(KEY_E)
			continue
		var target: int = logic.valid_gap(logic.held)
		var guard := 0
		while caret != target and guard < 30 and not ended:
			await _tap(KEY_RIGHT if caret < target else KEY_LEFT)
			guard += 1
		await _tap(KEY_E)
		await _frames(2)
	await _until(func(): return solved, 4.0)
