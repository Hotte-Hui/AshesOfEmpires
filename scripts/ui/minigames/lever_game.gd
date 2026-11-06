extends "res://scripts/ui/minigames/minigame_base.gd"
## Tunnel mini-game "Der Hebelrahmen" (scenes/ui/minigames/LeverFrame.tscn, explore entry karsk.tunnels.lever_frame
## at exp_lever_frame in L_C4_Tunnels, §12.8, documentation/C4_DESIGN.md §6). Sunday, 7.30, Service Tunnel 3 under
## the Karsk freight yard: beside switch W2 a mechanical lever frame of 1941, the locks freshly greased, the night
## shift's route book jammed into it with three orders in pencil. Alexei -- a railway engineer -- carries them out the
## way the frame allows: points first, then the route lever, then the signal; back in reverse order. The third order
## names no route, only lever 6 without a plate; its route lights a track the books do not have: „КОРДОН 17“.
## Rule: lever_logic.gd. Art: assets/ui/minigames/lever/ (tools/pixelgen/gen_mg_c4_lever.py, 1:1 art px, drawn x3, x2
## for larger text); the lights over the art (route light, signal lamps, lock pips, levers, cursor) are drawn here.
## Colours outside the tunnels palette: the moon-white route light COL_ROUTE and the signal green COL_GREEN.
## Sounds: mg_c4_* (tools/audiogen/mg_audio_c4.py).
## Keys: Left/Right (A/D, d-pad) choose a lever · Up pulls it over, Down puts it back · E, Enter, Space or pad A
## toggle it · 1-8 toggle that lever directly · R or pad Y starts over · Esc gives up.
## Mouse: point at a lever and click to toggle it.

const Logic := preload("res://scripts/ui/minigames/lever_logic.gd")
const ART := "res://assets/ui/minigames/lever/"
const COL_AMBER := Color("e9b46e")
const COL_WHITE := Color("f5efda")
const COL_ROUTE := Color("eef2f5")
const COL_SET := Color("d8cfb2")          # tunnels paper[4]: the branch a points lever is set to
const COL_RED := Color("c8503c")          # tunnels red[3]
const COL_RED_DIM := Color("7a2218")      # tunnels red[1]
const COL_GREEN := Color("6fd08c")
const COL_BAR := [Color("22262d"), Color("464d55"), Color("5e666e")]          # tunnels iron[1], [3], [4]
const HANDLE := {"points": [Color("07080b"), Color("323840")], "route": [Color("8c5426"), Color("e0a85a")],
	"signal": [Color("7a2218"), Color("c8503c")]}
const SHORT := {"w1": "W1", "w2": "W2", "w3": "W3", "a": "a", "b": "b", "c": "c", "s1": "S1", "s2": "S2"}
const BEAT := 1.4
const ANIM_T := 0.16

var logic = Logic.new()
## Art scale: x3, or x2 in the compact layout for larger text (set in _build_play).
var S := 3
var compact := false
var layout: Dictionary = {}
var cursor := 0
var _tex: Dictionary = {}
var _scene: Control
var _progress: Label
var _order_label: Label
var _lever_label: Label
var _desc_label: Label
var _state_label: Label
var _table: GridContainer
var _btn_main: Button
var _anim: Dictionary = {}       # lever id -> shown position 0 (normal) .. 1 (reversed)
var _shake: Dictionary = {}      # lever id -> seconds of the refusal jolt left
var _beat := -1.0
var _t := 0.0
var _input_guard := 0.0
var _order_shown := -1
var _area: Control
var _side: Control
var _left: Control


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_scene", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("scene_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.lever.kicker", "mg.lever.title", "mg.lever.subtitle", "mg.lever.instruction")
	var lj = Kit.json(ART + "lever_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["lever_back", "lever_indicator"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	compact = Kit.text_scale() > 1.01
	S = 2 if compact else 3
	if compact:      # larger text: the side panel carries the order and the table, the flavour gives way
		_subtitle.visible = false
		_instr.visible = false
	var row := Kit.hbox(36)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var sz: Array = layout.get("size", [400, 148])
	var v := View.new()
	v.game = self
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.custom_minimum_size = Vector2(float(sz[0]), float(sz[1])) * S
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	_scene = v
	var left := Kit.vbox(8)
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(left)
	left.add_child(v)
	_left = left
	area.custom_minimum_size.y = float(sz[1]) * S
	_area = area
	var side := Kit.vbox(4)
	_side = side
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	side.custom_minimum_size.x = 860 if compact else 500
	row.add_child(side)
	_progress = Kit.wrap_label("", "KickerLabel")
	side.add_child(_progress)
	_order_label = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_order_label, 23)
	side.add_child(_order_label)
	var plate := Kit.panel("PlatePanel")
	side.add_child(plate)
	var col := Kit.vbox(2)
	plate.add_child(col)
	_lever_label = Kit.label("", "HeadingLabel")
	Kit.scalable(_lever_label, 27)
	col.add_child(_lever_label)
	_desc_label = Kit.wrap_label("", "DimLabel")
	Kit.scalable(_desc_label, 20)
	_desc_label.visible = not compact          # larger text: name and state are enough, the table says the rest
	col.add_child(_desc_label)
	_state_label = Kit.label("", "KickerLabel")
	col.add_child(_state_label)
	# the locking table, its legend in the heading (the panel keeps room for the hint at every text size)
	var th := Kit.wrap_label((Kit.t("mg.lever.table.title") + "  ·  " + Kit.t("mg.lever.table.legend")).to_upper()
		.replace("ß", "SS"), "KickerLabel")
	side.add_child(th)
	_table = GridContainer.new()
	_table.columns = 5
	_table.add_theme_constant_override("h_separation", 18)
	_table.add_theme_constant_override("v_separation", 0)
	side.add_child(_table)
	_fill_table()
	_btn_main = _add_button(Kit.t("mg.lever.btn.pull"), act, 250, true)


func _fill_table() -> void:
	var cells: Array = ["", "W1", "W2", "W3", Kit.t("mg.lever.table.signal")]
	for r in ["a", "b", "c"]:
		cells.append(Kit.t("mg.lever.table.route." + r))
		var needs: Dictionary = Logic.NEEDS[r]
		for p in ["w1", "w2", "w3"]:
			cells.append(("−" if bool(needs[p]) else "+") if needs.has(p) else "")
		cells.append(SHORT[str(Logic.SIGNAL_OF[r])])
	for i in cells.size():
		var l := Kit.label(str(cells[i]), "BodyLabel" if i >= 5 else "DimLabel")
		Kit.scalable(l, 19)
		if i % 5 != 0:
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_table.add_child(l)


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.3
	set_status(Kit.t("mg.lever.status.start"))
	_status_hold = 2.6


func _reset_game() -> void:
	logic.reset()
	cursor = 0
	_beat = -1.0
	_shake = {}
	_anim = {}
	for id in Logic.LEVERS:
		_anim[id] = 1.0 if logic.is_pulled(id) else 0.0
	_update_ui()


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	set_status(Kit.t("mg.lever.status.restart"))
	_status_hold = 1.4


# ================================================================ actions
func selected() -> String:
	return str(Logic.LEVERS[clampi(cursor, 0, Logic.LEVERS.size() - 1)])


## Toggle the lever under the cursor.
func act() -> void:
	pull_or_back(selected(), 0)


## dir 0 = toggle, 1 = only pull over, -1 = only put back.
func pull_or_back(id: String, dir: int) -> void:
	if solved or ended or logic.order_complete or _beat >= 0.0:
		return
	cursor = Logic.index_of(id)
	var on: bool = logic.is_pulled(id)
	if (dir == 1 and on) or (dir == -1 and not on):
		set_status(Kit.t("mg.lever.status.already_pulled" if on else "mg.lever.status.already_back",
			{"n": Logic.number_of(id)}))
		_status_hold = 1.0
		_update_ui()
		return
	var r: Dictionary = logic.toggle(id)
	if not bool(r.get("ok", false)):
		_shake[id] = 0.28
		_sfx("mg_c4_lever_locked", -2.0)
		register_fail(refusal_text(id, r))
		_update_ui()
		return
	_sfx("mg_c4_lever_pull" if bool(r["pulled"]) else "mg_c4_lever_back", -2.0)
	if bool(r.get("order_done", false)):
		_beat = BEAT
		_sfx("mg_c4_route_set", -4.0)
		clear_status_hold()
		set_status(Kit.t("mg.lever.done." + str(logic.current()["id"])))
		_status_hold = BEAT + 0.6
	else:
		set_status(Kit.t("mg.lever.status.pulled" if bool(r["pulled"]) else "mg.lever.status.back",
			{"n": Logic.number_of(id), "name": lever_name(id)}))
		_status_hold = 1.2
	_update_ui()


static func lever_name(id: String) -> String:
	return Kit.t("mg.lever.name." + id)


## The frame's reason, in words (the refusal line).
func refusal_text(id: String, r: Dictionary) -> String:
	var by := str(r.get("by", ""))
	match str(r.get("reason", "")):
		"points_locked":
			return Kit.t("mg.lever.fail.points_locked", {"w": lever_name(id), "r": by})
		"route_points":
			var need: bool = bool((Logic.NEEDS[id] as Dictionary).get(by, false))
			return Kit.t("mg.lever.fail.route_points", {"r": id, "w": lever_name(by),
				"lage": Kit.t("mg.lever.lage.minus" if need else "mg.lever.lage.plus")})
		"route_conflict":
			return Kit.t("mg.lever.fail.route_conflict", {"r": id, "o": by})
		"route_held":
			return Kit.t("mg.lever.fail.route_held", {"r": id, "s": lever_name(by)})
		"signal_no_route":
			return Kit.t("mg.lever.fail.signal_no_route", {"s": lever_name(id)})
	return Kit.t("mg.lever.status.idle")


func _cancel_step() -> bool:
	return false


func _move(d: int) -> void:
	if solved or ended:
		return
	cursor = clampi(cursor + d, 0, Logic.LEVERS.size() - 1)
	Kit.ui_sound("move")
	_update_ui()


# ================================================================ hints
func _hint_text(level: int) -> String:
	if logic.done:
		return ""
	if level >= 2:
		var nx: String = logic.next_move()
		if nx != "":
			return Kit.t("mg.lever.hint.next", {"n": Logic.number_of(nx), "name": lever_name(nx),
				"act": Kit.t("mg.lever.hint.act.back" if logic.is_pulled(nx) else "mg.lever.hint.act.pull")})
	return Kit.t("mg.lever.hint.1")


## Settings "puzzle_hints" (like the other puzzles): 0 never a hint, 1 after two refusals (default), 2 the first
## hint at once and one level more with every refusal.
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
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.lever.ctrl.choose")],
		[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN) + "|" + Kit.action_key_text("interact"), Kit.t("mg.lever.ctrl.toggle")],
		["1–8", Kit.t("mg.lever.ctrl.direct")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_t += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	for k in _shake.keys():
		_shake[k] = float(_shake[k]) - delta
		if float(_shake[k]) <= 0.0:
			_shake.erase(k)
	var step := 1.0 if Kit.reduced_motion() else delta / ANIM_T
	for id in Logic.LEVERS:
		var target := 1.0 if logic.is_pulled(id) else 0.0
		_anim[id] = move_toward(float(_anim.get(id, target)), target, step)
	if _beat >= 0.0:
		_beat -= delta
		if _beat < 0.0:
			_beat = -1.0
			var last: bool = logic.order >= Logic.ORDERS.size() - 1
			logic.next_order()
			if last or logic.done:
				mark_solved(Kit.t("mg.lever.solved"))
			else:
				set_status(Kit.t("mg.lever.status.next", {"n": logic.order + 1}))
				_status_hold = 1.6
			_update_ui()
	if not solved and _beat < 0.0:
		status_auto(Kit.t("mg.lever.status.idle"))
	_fit_height()
	if _scene != null:
		_scene.queue_redraw()


## The play area is as tall as the stage or the side column (order, lever plate, locking table), whichever needs
## more -- the status line below never runs into the table.
func _fit_height() -> void:
	if _area == null or _side == null or _left == null:
		return
	var need := maxf(_left.get_combined_minimum_size().y, _side.get_combined_minimum_size().y)
	if absf(_area.custom_minimum_size.y - need) > 0.5:
		_area.custom_minimum_size.y = need


func _update_ui() -> void:
	if _progress == null:
		return
	var total: int = Logic.ORDERS.size()
	var head := Kit.t("mg.lever.progress", {"n": mini(logic.order + 1, total), "total": total})
	if logic.done:
		head = Kit.t("mg.lever.progress_done")
	_progress.text = head.to_upper().replace("ß", "SS")
	_order_label.text = Kit.t("mg.lever.order." + str(logic.current()["id"]))
	if _order_shown != logic.order:
		_order_shown = logic.order
		Kit.appear(_order_label, 0.2)
	var id := selected()
	_lever_label.text = Kit.t("mg.lever.lever_fmt", {"n": Logic.number_of(id), "name": lever_name(id)})
	_desc_label.text = Kit.t("mg.lever.desc." + id)
	var kind := str(Logic.KIND[id])
	var st := Kit.t("mg.lever.state.%s.%d" % [kind, 1 if logic.is_pulled(id) else 0])
	var lk: Dictionary = logic.locked()
	var lock := Kit.t("mg.lever.locked") if lk.has(id) else Kit.t("mg.lever.free")
	_state_label.text = (st + "  ·  " + lock).to_upper().replace("ß", "SS")
	if _btn_main != null:
		_btn_main.text = Kit.t("mg.lever.btn.back" if logic.is_pulled(id) else "mg.lever.btn.pull")
	if _hint_box != null and _hint_box.visible and not logic.done:
		_hint_label.text = _hint_text(maxi(1, hint_level))


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y:
		restart()
		return true
	if k >= KEY_1 and k <= KEY_8:
		if _input_guard <= 0.0:
			pull_or_back(str(Logic.LEVERS[k - KEY_1]), 0)
		return true
	if k >= KEY_KP_1 and k <= KEY_KP_8:
		if _input_guard <= 0.0:
			pull_or_back(str(Logic.LEVERS[k - KEY_KP_1]), 0)
		return true
	if _is(event, ["ui_left", "move_left"], true):
		_move(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		_move(1)
		return true
	if _is(event, ["ui_up", "move_up"]):
		if _input_guard <= 0.0:
			pull_or_back(selected(), 1)
		return true
	if _is(event, ["ui_down", "move_down"]):
		if _input_guard <= 0.0:
			pull_or_back(selected(), -1)
		return true
	if _is(event, ["ui_accept", "interact"]) or k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE or k == KEY_E \
			or pb == JOY_BUTTON_A:
		if _input_guard <= 0.0:
			act()
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _lever_at(p: Vector2) -> int:
	var xs: Array = layout.get("lever_x", [])
	if p.y < 56.0 or p.y > float(layout.get("label_rect", [0, 121, 0, 14])[1]) + 16.0:
		return -1
	for i in xs.size():
		if absf(p.x - float(xs[i])) <= 16.0:
			return i
	return -1


func scene_input(event: InputEvent) -> void:
	if ended or solved:
		return
	var p: Vector2
	var click := false
	if event is InputEventMouseMotion:
		p = (event as InputEventMouseMotion).position / S
	elif event is InputEventMouseButton and event.pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		p = (event as InputEventMouseButton).position / S
		click = true
	else:
		return
	var i := _lever_at(p)
	if i < 0:
		return
	if i != cursor:
		cursor = i
		_update_ui()
	if click and _input_guard <= 0.0:
		act()


# ================================================================ drawing (art px, x S)
func _px_line(v: Control, pts: Array, col: Color, thick := 1, glow := Color(0, 0, 0, 0)) -> void:
	for j in range(pts.size() - 1):
		var a := Vector2(float(pts[j][0]), float(pts[j][1]))
		var b := Vector2(float(pts[j + 1][0]), float(pts[j + 1][1]))
		var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
		for i in n + 1:
			var q := a.lerp(b, float(i) / float(maxi(1, n))).round()
			if glow.a > 0.0:
				v.draw_rect(Rect2(q.x, q.y + float(thick), 1, 1), glow)
			v.draw_rect(Rect2(q.x, q.y, 1, thick), col)


func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var hc := Kit.high_contrast()
	var bt: Texture2D = _tex.get("lever_back")
	if bt != null:
		v.draw_texture(bt, Vector2.ZERO)
	# the diagram: where each points lever lies, the locked route, the signals, the route indicator
	var br: Dictionary = layout.get("branches", {})
	for w in br:
		var pair: Array = br[w]
		_px_line(v, pair[1 if logic.is_pulled(str(w)) else 0], COL_SET)
	var routes: Dictionary = layout.get("routes", {})
	var lit := ""
	for r in ["a", "b", "c"]:
		if logic.is_pulled(r) and routes.has(r):
			lit = r
			_px_line(v, routes[r], COL_ROUTE, 1, Color(COL_ROUTE, 0.35))
	var sig: Dictionary = layout.get("signals", {})
	for s in sig:
		var at: Array = sig[s]
		var go: bool = logic.is_pulled(str(s))
		var pulse := 1.0 if (go or Kit.reduced_motion()) else (0.85 + 0.15 * sin(_t * 3.0))
		v.draw_rect(Rect2(float(at[0]), float(at[1]), 3, 3), Color(COL_GREEN if go else COL_RED, pulse))
	var it: Texture2D = _tex.get("lever_indicator")
	var ind: Dictionary = layout.get("indicator", {})
	if lit != "" and it != null and not ind.is_empty():
		var cell: Array = ind.get("cell", [64, 9])
		var ci: int = (ind.get("order", ["a", "b", "c"]) as Array).find(lit)
		var ia: Array = ind.get("at", [16, 9])
		v.draw_texture_rect_region(it, Rect2(float(ia[0]), float(ia[1]), float(cell[0]), float(cell[1])),
			Rect2(float(ci) * float(cell[0]), 0, float(cell[0]), float(cell[1])))
	# the levers
	var xs: Array = layout.get("lever_x", [])
	var hy: Array = layout.get("handle_y", [64, 84])
	var slot := float(layout.get("slot_y", 100))
	var pip: Array = layout.get("pip", [5, 109])
	var locks: Dictionary = logic.locked()
	for i in mini(xs.size(), Logic.LEVERS.size()):
		var id := str(Logic.LEVERS[i])
		var x := float(xs[i])
		var pos := float(_anim.get(id, 0.0))
		if _shake.has(id) and not Kit.reduced_motion():
			x += 1.0 if fmod(float(_shake[id]) * 40.0, 2.0) < 1.0 else -1.0
		var h := roundf(lerpf(float(hy[0]), float(hy[1]), pos))
		var hw := 9.0 + roundf(2.0 * pos)
		v.draw_rect(Rect2(x - 1.0, h + 4.0, 3.0, slot - h - 3.0), COL_BAR[1])
		v.draw_rect(Rect2(x - 1.0, h + 4.0, 1.0, slot - h - 3.0), COL_BAR[2])
		v.draw_rect(Rect2(x + 1.0, h + 4.0, 1.0, slot - h - 3.0), COL_BAR[0])
		v.draw_rect(Rect2(x + 2.0, h + 5.0, 1.0, 6.0), COL_BAR[2])          # catch handle
		var hcol: Array = HANDLE[str(Logic.KIND[id])]
		v.draw_rect(Rect2(x - floorf(hw / 2.0), h, hw, 4.0), hcol[0])
		v.draw_rect(Rect2(x - floorf(hw / 2.0) + 1.0, h, hw - 2.0, 1.0), hcol[1])
		if locks.has(id):
			v.draw_rect(Rect2(x + float(pip[0]), float(pip[1]), 2, 2), COL_RED)
	# the cursor
	if not solved and not xs.is_empty():
		var cx := float(xs[clampi(cursor, 0, xs.size() - 1)])
		var col := COL_WHITE if hc else COL_AMBER
		var blink := 1.0 if (Kit.reduced_motion() or fmod(_t, 1.0) < 0.7) else 0.6
		var top := float(hy[0]) - 3.0
		if hc:
			v.draw_rect(Rect2(cx - 10.0, top - 1.0, 21.0, 61.0), Color(0, 0, 0), false, 1.0)
		v.draw_rect(Rect2(cx - 9.0, top, 19.0, 59.0), Color(col, blink), false, 1.0)
		v.draw_colored_polygon(PackedVector2Array([Vector2(cx - 3, top - 5), Vector2(cx + 4, top - 5),
			Vector2(cx + 0.5, top - 1.5)]), col)
	# the German labels under the plates (screen pixels, theme font)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var font := v.get_theme_default_font()
	var lr: Array = layout.get("label_rect", [44, 121, 312, 14])
	var fs := 15 if S == 2 else 22
	if font != null:
		for i in mini(xs.size(), Logic.LEVERS.size()):
			var id := str(Logic.LEVERS[i])
			var sel := i == cursor and not solved
			var tc := (COL_WHITE if hc else COL_AMBER) if sel else Color("b3a98d")
			var y := (float(lr[1]) + float(lr[3]) * 0.5) * S + float(fs) * 0.35
			v.draw_string(font, Vector2((float(xs[i]) - 12.0) * S, y), SHORT[id], HORIZONTAL_ALIGNMENT_CENTER,
				24.0 * S, fs, tc)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 90000:
		if logic.order_complete or _beat >= 0.0:
			await _frames(2)
			continue
		var nx: String = logic.next_move()
		if nx == "":
			await _frames(2)
			continue
		var target := Logic.index_of(nx)
		var guard := 0
		while cursor != target and guard < 12 and not ended:
			await _tap(KEY_RIGHT if cursor < target else KEY_LEFT)
			guard += 1
		await _tap(KEY_E)
		await _frames(2)
	await _until(func(): return solved, 4.0)
