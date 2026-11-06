extends "res://scripts/ui/minigames/minigame_base.gd"
## Karsk "Rangieren" (scenes/ui/minigames/Shunting.tscn, explore entry karsk.shunting, §12.8).
## The yard seen from above (assets/ui/minigames/shunt_*.png, stored x3; geometry from shunt_layout.json):
## Alexei helps the shunter put the evening train together on siding 1 exactly as the waybill says.
## Logic: shunting_logic.gd. Keys: Up/Down (W/S, d-pad) route, 1/2 throw a set of points, Right/Enter/E drive in;
## coupled up: Left/Right choose the coupling to open, Enter/E pull out; R / pad Y start over; Esc gives up.
## Mouse: click a lever, a siding, a coupling; the buttons. Wrong moves (too long for the headshunt, too many for a
## siding) are refused with the reason; after two of them (or many trips) a hint appears, the third level of
## hints names the next sensible trip (computed by the solver).

const Logic := preload("res://scripts/ui/minigames/shunting_logic.gd")
const S := 3
const WAGON_TEX := {"K": "shunt_wagon_tank.png", "U": "shunt_wagon_coal.png", "P": "shunt_wagon_flat.png",
	"G": "shunt_wagon_box.png"}
const SPEED := 150.0          # art px / s
const ENGINE_HOME := 19.0
const FIRST_WAGON := 58.0
const HALF_GAP := 39.0        # engine centre <-> first wagon centre
const CHIMNEY := 10.0         # art px ahead of the engine centre

var logic = Logic.new()
var layout: Dictionary = {}
var _route_len: Dictionary = {}
var _yard: Control
var _tex: Dictionary = {}
var _veh: Dictionary = {}      # id -> {"route", "s", "s0", "s1"}
var _busy := false
var _anim_t := 0.0
var _anim_dur := 0.0
var _anim_done: Callable
var _puffs: Array = []
var _puff_t := 0.0
var _trips_label: Label
var _act_btn: Button
var _optimal := 6


class YardView extends Control:
	var game: Node

	func _draw() -> void:
		game.draw_yard(self)

	func _gui_input(event: InputEvent) -> void:
		game.yard_input(event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.shunt.kicker", "mg.shunt.title", "mg.shunt.subtitle", "mg.shunt.instruction")
	var lj = Kit.json(DIR + "shunt_layout.json")
	layout = lj if lj is Dictionary else {}
	for t in ["1", "2", "3"]:
		_route_len[t] = _poly_len(_route(t))
	for k in ["shunt_yard.png", "shunt_engine.png", "shunt_lever_0.png", "shunt_lever_1.png"] + WAGON_TEX.values():
		_tex[k] = Kit.optional_tex(DIR + k)
	var row := Kit.hbox(36)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	_yard = YardView.new()
	_yard.game = self
	_yard.mouse_filter = Control.MOUSE_FILTER_STOP
	var ysz: Vector2 = _tex["shunt_yard.png"].get_size() if _tex["shunt_yard.png"] != null else Vector2(1080, 504)
	_yard.custom_minimum_size = ysz
	_yard.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_yard)
	# the shunter's waybill (goal picture: siding 1 from the points to the buffer stop)
	var card := Kit.panel("PaperCardPanel")
	card.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	card.custom_minimum_size.x = 440
	row.add_child(card)
	var col := Kit.vbox(10)
	card.add_child(col)
	col.add_child(Kit.label(Kit.t("mg.shunt.waybill.kicker").to_upper().replace("ß", "SS"), "PaperKicker"))
	var wt := Kit.label(Kit.t("mg.shunt.waybill.title"), "", 30, Kit.C_INK)
	wt.add_theme_font_override("font", Kit.font("fv_serif_bold"))
	col.add_child(wt)
	var pic := Kit.hbox(4)
	pic.alignment = BoxContainer.ALIGNMENT_CENTER
	for ch in Logic.GOAL:
		var tr := TextureRect.new()
		tr.texture = _tex[WAGON_TEX[ch]]
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		tr.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		tr.custom_minimum_size = Vector2(108, 36)
		pic.add_child(tr)
	var stop := ColorRect.new()
	stop.color = Kit.C_STAMP
	stop.custom_minimum_size = Vector2(9, 36)
	pic.add_child(stop)
	col.add_child(pic)
	var names := Kit.hbox(4)
	names.alignment = BoxContainer.ALIGNMENT_CENTER
	for ch in Logic.GOAL:
		var nl := Kit.label(Kit.t("mg.shunt.wagon." + ch), "", 17, Kit.C_INK_DIM)
		nl.custom_minimum_size.x = 108
		nl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		names.add_child(nl)
	var sl := Kit.label("", "", 17, Kit.C_INK_DIM)
	sl.custom_minimum_size.x = 9
	names.add_child(sl)
	col.add_child(names)
	var note := Kit.wrap_label(Kit.t("mg.shunt.waybill.note"), "PaperBody")
	Kit.scalable(note, 23)
	note.custom_minimum_size.x = 400
	col.add_child(note)
	col.add_child(Kit.rule(Kit.C_PAPER_D, 2))
	_trips_label = Kit.label("", "PaperKicker")
	col.add_child(_trips_label)
	_act_btn = _add_button(Kit.t("mg.shunt.btn.enter"), _act, 300, true)
	_optimal = logic.solve().size()


func _poly_len(poly: Array) -> float:
	var l := 0.0
	for i in range(1, poly.size()):
		l += Vector2(poly[i][0], poly[i][1]).distance_to(Vector2(poly[i - 1][0], poly[i - 1][1]))
	return l


func _route(t: String) -> Array:
	var r = layout.get("routes", {})
	return r.get(t, [[14, 40], [296, 40]]) if r is Dictionary else [[14, 40], [296, 40]]


## Art-px point and heading at arc length s along route t.
func point_at(t: String, s: float) -> Array:
	var poly := _route(t)
	var acc := 0.0
	for i in range(1, poly.size()):
		var a := Vector2(poly[i - 1][0], poly[i - 1][1])
		var b := Vector2(poly[i][0], poly[i][1])
		var l := a.distance_to(b)
		if s <= acc + l or i == poly.size() - 1:
			var f := clampf((s - acc) / maxf(l, 0.001), 0.0, 1.0)
			return [a.lerp(b, f), (b - a).angle()]
		acc += l
	return [Vector2(poly[0][0], poly[0][1]), 0.0]


# ================================================================ state -> vehicle positions
func _targets() -> Dictionary:
	var out := {}
	var t := logic.route()
	var h := str(logic.tracks["H"])
	for sd in ["1", "2", "3"]:
		var w := str(logic.tracks[sd])
		if logic.phase == "in" and sd == t:
			continue
		for j in w.length():
			out[w[j]] = [sd, float(_route_len[sd]) - 20.0 - 40.0 * (w.length() - 1 - j)]
	if logic.phase == "in":
		var comb: String = logic.combined()
		var k := comb.length()
		for i in k:
			out[comb[i]] = [t, float(_route_len[t]) - 20.0 - 40.0 * (k - 1 - i)]
		out["E"] = [t, (float(out[comb[0]][1]) - HALF_GAP) if k > 0 else float(_route_len[t]) - 19.0]
	else:
		out["E"] = [t, ENGINE_HOME]
		for i in h.length():
			out[h[i]] = [t, FIRST_WAGON + 40.0 * i]
	return out


func _snap_vehicles() -> void:
	_veh.clear()
	var tg := _targets()
	for id in tg:
		_veh[id] = {"route": tg[id][0], "s": tg[id][1], "s0": tg[id][1], "s1": tg[id][1]}
	_busy = false
	if _yard:
		_yard.queue_redraw()


func _animate_to_targets(done: Callable) -> void:
	var tg := _targets()
	var far := 0.0
	for id in tg:
		var v: Dictionary = _veh.get(id, {"route": tg[id][0], "s": tg[id][1]})
		v["route"] = tg[id][0]
		v["s0"] = float(v["s"])
		v["s1"] = float(tg[id][1])
		_veh[id] = v
		far = maxf(far, absf(float(v["s1"]) - float(v["s0"])))
	_anim_t = 0.0
	_anim_dur = clampf(far / SPEED, 0.35, 2.2)
	_anim_done = done
	_busy = true
	_sfx("mg_shunt", -4.0)


func _tick(delta: float) -> void:
	if _busy:
		_anim_t += delta
		var f := clampf(_anim_t / _anim_dur, 0.0, 1.0)
		var e := f * f * (3.0 - 2.0 * f)
		for id in _veh:
			var v: Dictionary = _veh[id]
			v["s"] = lerpf(float(v["s0"]), float(v["s1"]), e)
		_puff_t -= delta
		if _puff_t <= 0.0 and _veh.has("E"):
			_puff_t = 0.16
			var pe: Array = point_at(str(_veh["E"]["route"]), float(_veh["E"]["s"]) + CHIMNEY)
			_puffs.append({"p": pe[0], "age": 0.0})
		if f >= 1.0:
			_busy = false
			if _anim_done.is_valid():
				var cb := _anim_done
				_anim_done = Callable()
				cb.call()
	for p in _puffs:
		p["age"] = float(p["age"]) + delta
	_puffs = _puffs.filter(func(p): return float(p["age"]) < 1.1)
	if _yard and (_busy or not _puffs.is_empty()):
		_yard.queue_redraw()


# ================================================================ actions
func _reset_game() -> void:
	logic.reset()
	_puffs.clear()
	_snap_vehicles()
	_update_ui()


func _act() -> void:
	if _busy or solved:
		return
	if logic.phase == "home":
		_enter()
	else:
		_leave()


func _cycle_route(d: int) -> void:
	var order := ["1", "2", "3"]
	var i := (order.find(logic.route()) + d + 3) % 3
	_set_route(order[i])


func _set_route(t: String) -> void:
	if logic.phase != "home" or t == logic.route():
		return
	logic.set_route(t)
	_sfx("mg_points", -3.0)
	_update_ui()


func _throw(n: int) -> void:
	if logic.phase != "home":
		set_status(Kit.t("mg.shunt.fail.points_busy"))
		return
	logic.throw_points(n)
	_sfx("mg_points", -3.0)
	_update_ui()


func _enter() -> void:
	if not logic.enter():
		return
	clear_status_hold()
	_animate_to_targets(func():
		_sfx("mg_couple", -2.0)
		_update_ui())
	_update_ui()


func _set_cut(m: int) -> void:
	if logic.phase != "in":
		return
	var before: int = logic.cut
	logic.set_cut(m)
	if logic.cut != before:
		Kit.ui_sound("move")
	_update_ui()


func _leave() -> void:
	var t: String = logic.route()
	var comb_len: int = logic.combined().length()
	var r: Dictionary = logic.leave()
	if not bool(r.get("ok", false)):
		match str(r.get("reason", "")):
			"headshunt":
				register_fail(Kit.t("mg.shunt.fail.headshunt"))
			"siding":
				register_fail(Kit.t("mg.shunt.fail.siding", {"n": t, "cap": Logic.CAP[t]}))
		return
	clear_status_hold()
	if logic.tracks["H"].length() < comb_len:
		_sfx("mg_couple", -9.0)
	_animate_to_targets(func():
		if bool(r.get("solved", false)):
			mark_solved(Kit.t("mg.shunt.solved"))
		elif logic.trips >= _optimal + 5 and hint_level < 3:
			show_hint(maxi(hint_level + 1, 1))
		_update_ui())
	_update_ui()


func _update_ui() -> void:
	if _trips_label:
		_trips_label.text = Kit.t("mg.shunt.trips", {"n": logic.trips}).to_upper().replace("ß", "SS")
	if _act_btn:
		_act_btn.text = Kit.t("mg.shunt.btn.enter" if logic.phase == "home" else "mg.shunt.btn.leave")
	if not solved and not _busy:
		if logic.phase == "home":
			status_auto(Kit.t("mg.shunt.status.home", {"n": logic.route(), "k": str(logic.tracks["H"]).length()}))
		else:
			var comb: String = logic.combined()
			status_auto(Kit.t("mg.shunt.status.in", {"m": logic.cut, "k": comb.length(), "n": logic.route()}))
	if hint_level >= 3:
		show_hint(hint_level)
	if _yard:
		_yard.queue_redraw()


func register_fail(text: String) -> void:
	super.register_fail(text)
	if _yard:
		_yard.queue_redraw()


func _hint_text(level: int) -> String:
	if level <= 1:
		return Kit.t("mg.shunt.hint.1")
	if level == 2:
		return Kit.t("mg.shunt.hint.2")
	if logic.phase != "home":
		return Kit.t("mg.shunt.hint.leave_first")
	var plan: Array = logic.solve()
	if plan.is_empty():
		return Kit.t("mg.shunt.hint.2")
	return Kit.t("mg.shunt.hint.next", {"n": plan[0][0], "m": plan[0][1]})


func _controls() -> Array:
	if logic.phase == "home":
		return [[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN), Kit.t("mg.shunt.ctrl.route")],
			["1|2", Kit.t("mg.shunt.ctrl.points")],
			[Kit.key_name(KEY_RIGHT) + "|" + Kit.action_key_text("interact"), Kit.t("mg.shunt.ctrl.enter")],
			["R", Kit.t("mg.common.ctrl.restart")]]
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.shunt.ctrl.cut")],
		[Kit.action_key_text("interact"), Kit.t("mg.shunt.ctrl.leave")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var game_key := event is InputEventKey or event is InputEventJoypadButton or event is InputEventJoypadMotion
	if _busy:
		return game_key and not event.is_action_pressed("cancel")
	if k == KEY_R or _pad(event) == JOY_BUTTON_Y:
		restart()
		return true
	if logic.phase == "home":
		if _is(event, ["ui_up", "move_up"]):
			_cycle_route(-1)
			return true
		if _is(event, ["ui_down", "move_down"]):
			_cycle_route(1)
			return true
		if k == KEY_1 or k == KEY_KP_1:
			_throw(1)
			return true
		if k == KEY_2 or k == KEY_KP_2:
			_throw(2)
			return true
		if _is(event, ["ui_right", "move_right", "ui_accept", "interact"]):
			_enter()
			return true
	else:
		if _is(event, ["ui_left", "move_left"], true):
			_set_cut(logic.cut - 1)
			return true
		if _is(event, ["ui_right", "move_right"], true):
			_set_cut(logic.cut + 1)
			return true
		if _is(event, ["ui_accept", "interact"]):
			_leave()
			return true
		if k == KEY_1 or k == KEY_2:
			_throw(1)
			return true
	return false


## Mouse on the yard: levers, sidings (home), couplings (coupled up).
func yard_input(event: InputEvent) -> void:
	if not (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT):
		return
	if _busy or solved or ended:
		return
	var p: Vector2 = (event as InputEventMouseButton).position / S
	var levers = layout.get("levers", {})
	if levers is Dictionary:
		for n in levers:
			var lp := Vector2(levers[n][0], levers[n][1])
			if Rect2(lp - Vector2(3, 3), Vector2(20, 28)).has_point(p):
				_throw(int(n))
				return
	if logic.phase == "home":
		for t in ["1", "2", "3"]:
			var poly := _route(t)
			var y := float(poly[poly.size() - 1][1])
			if absf(p.y - y) < 9.0 and p.x > float(layout.get("switch_points", {}).get("2", [200, 84])[0]) - (60.0 if t == "1" else 0.0):
				_set_route(t)
				return
	else:
		# nearest coupling gap along the consist
		var comb: String = logic.combined()
		var best := -1
		var bd := 18.0
		for m in range(0, comb.length() + 1):
			var g := _gap_point(m)
			if g == Vector2.INF:
				continue
			var d := g.distance_to(p)
			if d < bd:
				bd = d
				best = m
		if best >= 0:
			_set_cut(best)


## Art-px point of the coupling that opens for cut m (between the engine/kept wagons and the rest).
func _gap_point(m: int) -> Vector2:
	var comb: String = logic.combined()
	if logic.phase != "in" or m < 0 or m > comb.length():
		return Vector2.INF
	var t := logic.route()
	var s_back := float(_veh["E"]["s"]) if m == 0 else float(_veh[comb[m - 1]]["s"])
	var half_back := 17.0 if m == 0 else 18.0
	var s_gap := s_back + half_back + 2.0
	return point_at(t, s_gap)[0]


# ================================================================ drawing
func draw_yard(v: Control) -> void:
	var yt: Texture2D = _tex.get("shunt_yard.png")
	if yt != null:
		v.draw_texture(yt, Vector2.ZERO)
	var font := v.get_theme_font("font", "Label")
	# routed path ("Fahrstrasse"): dashed amber line through the points into the siding
	if logic.phase == "home" and not _busy:
		var t := logic.route()
		var L := float(_route_len[t])
		var s := 112.0
		while s < L - 6.0:
			var a: Vector2 = point_at(t, s)[0] * S
			var b: Vector2 = point_at(t, minf(s + 5.0, L))[0] * S
			v.draw_line(a, b, Color(Kit.C_AMBER, 0.85), 3.0)
			s += 9.0
	# levers with their key
	var levers = layout.get("levers", {})
	if levers is Dictionary:
		for n in levers:
			var thrown: bool = logic.w1 if n == "1" else logic.w2
			var lt: Texture2D = _tex.get("shunt_lever_%d.png" % (1 if thrown else 0))
			var lp := Vector2(levers[n][0], levers[n][1]) * S
			if lt != null:
				v.draw_texture(lt, lp)
			var kp := lp + Vector2(48, 30)
			v.draw_rect(Rect2(kp, Vector2(30, 32)), Color(Kit.C_NIGHT, 0.85))
			v.draw_rect(Rect2(kp, Vector2(30, 32)), Kit.C_COPPER, false, 2.0)
			v.draw_string(font, kp + Vector2(0, 25), str(n), HORIZONTAL_ALIGNMENT_CENTER, 30, 22, Kit.C_TEXT_BRIGHT)
	# siding labels (number + capacity)
	for t in ["1", "2", "3"]:
		var poly := _route(t)
		var end := Vector2(poly[poly.size() - 1][0], poly[poly.size() - 1][1]) * S
		var cap_text := Kit.t("mg.shunt.track_cap", {"n": t, "cap": Logic.CAP[t]})
		v.draw_string(font, end + Vector2(-330, 52), cap_text, HORIZONTAL_ALIGNMENT_RIGHT, 300, 19, Kit.C_INK_B)
	var h0: Array = _route("1")[0]
	v.draw_string(font, Vector2(float(h0[0]), float(h0[1])) * S + Vector2(0, 52), Kit.t("mg.shunt.headshunt"),
		HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Kit.C_INK_B)
	# vehicles
	for id in _veh:
		var vv: Dictionary = _veh[id]
		var tex: Texture2D = _tex.get("shunt_engine.png") if id == "E" else _tex.get(WAGON_TEX.get(id, ""))
		if tex == null:
			continue
		var pa: Array = point_at(str(vv["route"]), float(vv["s"]))
		var pos: Vector2 = pa[0]
		var ang: float = pa[1]
		if absf(ang) < 0.01:
			pos = Vector2(roundf(pos.x * S) / S, roundf(pos.y * S) / S)
		v.draw_set_transform(pos * S, ang, Vector2.ONE)
		v.draw_texture(tex, -tex.get_size() / 2.0)
		v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# steam puffs
	for p in _puffs:
		var age := float(p["age"])
		var c := Color(Kit.C_PAPER, 0.75 * (1.0 - age / 1.1))
		var pp: Vector2 = (p["p"] as Vector2) * S + Vector2(age * 10.0, -age * 26.0)
		var r := 6.0 + age * 14.0
		pp = (pp / S).round() * S
		v.draw_circle(pp, r, c)
	# coupled up: the open coupling and what stays / goes
	if logic.phase == "in" and not _busy:
		var g := _gap_point(logic.cut)
		if g != Vector2.INF:
			var gp := g * S
			v.draw_rect(Rect2(gp + Vector2(-3, -33), Vector2(6, 66)), Kit.C_STAMP)
			var tri := PackedVector2Array([gp + Vector2(-12, -48), gp + Vector2(12, -48), gp + Vector2(0, -34)])
			v.draw_colored_polygon(tri, Kit.C_STAMP)
			var bg := Color(Kit.C_NIGHT, 0.8)
			var lt := Kit.t("mg.shunt.goes")
			var rt := Kit.t("mg.shunt.stays")
			var lw := font.get_string_size(lt, HORIZONTAL_ALIGNMENT_LEFT, -1, 19).x
			var rw := font.get_string_size(rt, HORIZONTAL_ALIGNMENT_LEFT, -1, 19).x
			v.draw_rect(Rect2(gp + Vector2(-lw - 26, -80), Vector2(lw + 12, 28)), bg)
			v.draw_string(font, gp + Vector2(-lw - 20, -59), lt, HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Kit.C_AMBER)
			v.draw_rect(Rect2(gp + Vector2(14, -80), Vector2(rw + 12, 28)), bg)
			v.draw_string(font, gp + Vector2(20, -59), rt, HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Kit.C_TEXT)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	await _until(func(): return not _busy, 5.0)
	await _tap(KEY_R)
	await _until(func(): return not _busy, 5.0)
	var plan: Array = logic.solve()
	for mv in plan:
		if ended or solved:
			return
		var guard := 0
		while logic.route() != str(mv[0]) and guard < 6:
			await _tap(KEY_DOWN)
			guard += 1
		await _tap(KEY_RIGHT)
		await _until(func(): return not _busy, 6.0)
		guard = 0
		while logic.phase == "in" and logic.cut != int(mv[1]) and guard < 10:
			await _tap(KEY_LEFT if logic.cut > int(mv[1]) else KEY_RIGHT)
			guard += 1
		await _tap(KEY_ENTER)
		await _until(func(): return not _busy, 6.0)
