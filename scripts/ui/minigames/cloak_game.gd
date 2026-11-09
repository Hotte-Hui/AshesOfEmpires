extends "res://scripts/ui/minigames/minigame_base.gd"
## Palais "Die Garderobe" (scenes/ui/minigames/Cloakroom.tscn, explore entry veltrava.hall.cloak_tokens, §12.8).
## Session break at the cloakroom of the Palais: Herr Wenzel has hung the coats on the wrong hooks, the guests hold
## their brass checks. Konrad picks the coat (round 1) and then the hat (round 2) each guest describes — by pin,
## newspaper and scarf; the hook numbers mislead. Warm and a little comic; Elena Weiss's coat (check 27) stays.
## Logic: cloak_logic.gd. Art: assets/ui/minigames/cloak/ (tools/pixelgen/gen_mg_cloak.py, 1:1 art px, drawn x3).
## Sounds: mg_cloak_* (tools/audiogen/mg_audio_r7_v.py).
## Keys: Left/Right (A/D, d-pad) choose a coat / hat · Enter, Space, E or pad A hand it over · R or pad Y starts the
## round over · Esc gives up. Mouse: point at a coat or hat, click to hand it over.

const Logic := preload("res://scripts/ui/minigames/cloak_logic.gd")
const ART := "res://assets/ui/minigames/cloak/"
const EXPR := {"neutral": 0, "pleased": 1, "puzzled": 2}
const THANKS_T := 1.5
const WENZEL_T := 2.4
const LIFT_T := 0.5
const SLIDE_T := 0.3
const COL_AMBER := Color("e9b46e")
const COL_WHITE := Color("f5efda")

var logic = Logic.new()
## Art scale: x3, or x2 in the compact layout for larger text (set in _build_play).
var S := 3
var compact := false
var layout: Dictionary = {}
var cursor := 0
var _tex: Dictionary = {}
var _scene: Control
var _bust: Control
var _token_icon: Control
var _round_label: Label
var _name_label: Label
var _role_label: Label
var _pin_label: Label
var _say_label: Label
var _item_title: Label
var _item_desc: Label
var _phase := "ask"            # ask | thanks | wenzel | end
var _phase_t := 0.0
var _last: Dictionary = {}     # result of the last successful give()
var _shown_guest := ""
var _slide := 0.0
var _expr := "neutral"
var _expr_t := 0.0
var _lift: Dictionary = {}     # "coat:camel" -> seconds since it left the hook
var _shake := 0.0
var _wenzel_talk := 0.0
var _anim := 0.0
var _input_guard := 0.0
var _round_shown := 0          # the round the side panel shows (lags the logic during the thanks of a round's last guest)
var _last_item := ""
var _last_kind := ""


class View extends Control:
	var game: Node
	var kind := ""

	func _draw() -> void:
		game.call("draw_" + kind, self)

	func _gui_input(event: InputEvent) -> void:
		if kind == "scene":
			game.scene_input(event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.cloak.kicker", "mg.cloak.title", "mg.cloak.subtitle", "mg.cloak.instruction")
	var lj = Kit.json(ART + "cloak_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["cloak_back", "cloak_front", "cloak_coats", "cloak_hats", "cloak_guests", "cloak_wenzel", "cloak_tokens"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	# larger text (125 / 150 %): the pixel art drops to x2 and the item card moves under the scene
	compact = Kit.text_scale() > 1.01
	S = 2 if compact else 3
	if compact:      # flavour only; the guest's own words then go to the status line, not the side panel
		_subtitle.visible = false
	var row := Kit.hbox(40)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var left := Kit.vbox(10)
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(left)
	var sz: Array = layout.get("size", [320, 150])
	_scene = _view("scene", Vector2(float(sz[0]), float(sz[1])))
	_scene.mouse_filter = Control.MOUSE_FILTER_STOP
	left.add_child(_scene)
	var side := Kit.vbox(10)
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	side.custom_minimum_size.x = 900 if compact else 640
	row.add_child(side)
	_round_label = Kit.label("", "KickerLabel")
	if not compact:
		side.add_child(_round_label)
	var top := Kit.hbox(20)
	side.add_child(top)
	var frame := Kit.panel("PortraitPanel")
	frame.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	top.add_child(frame)
	var gc: Array = layout.get("guest_cell", [64, 72])
	_bust = _view("bust", Vector2(float(gc[0]), float(gc[1])))
	_bust.clip_contents = true
	_bust.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_bust)
	var who := Kit.vbox(4)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(who)
	if compact:
		who.add_child(_round_label)
	_name_label = Kit.label("", "HeadingLabel")
	Kit.scalable(_name_label, 32)
	who.add_child(_name_label)
	_role_label = Kit.label("", "DimLabel")
	Kit.scalable(_role_label, 21)
	who.add_child(_role_label)
	_pin_label = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_pin_label, 21)
	who.add_child(_pin_label)
	var tk := Kit.hbox(10)
	who.add_child(tk)
	_token_icon = _view("token", Vector2(14, 14))
	_token_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tk.add_child(_token_icon)
	var tl := Kit.label("", "KickerLabel")
	tl.name = "TokenLabel"
	tl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	tk.add_child(tl)
	_say_label = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_say_label, 23)
	_say_label.custom_minimum_size.y = 64
	_say_label.visible = not compact
	side.add_child(_say_label)
	var card := Kit.panel("PlatePanel")
	side.add_child(card)
	var col := Kit.vbox(4)
	card.add_child(col)
	_item_title = Kit.label("", "KickerLabel")
	_item_title.visible = not compact      # compact: the hook number leads the description instead
	col.add_child(_item_title)
	_item_desc = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_item_desc, 21)
	col.add_child(_item_desc)
	_add_button(Kit.t("mg.cloak.btn.give"), give_selected, 280, true)


func _view(kind: String, art_size: Vector2) -> Control:
	var v := View.new()
	v.game = self
	v.kind = kind
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.custom_minimum_size = art_size * S
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return v


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_hint_at_open()
	_input_guard = 0.3
	_wenzel_say("mg.cloak.wenzel.start", 2.0)


func _reset_game() -> void:
	logic.reset()
	_phase = "ask"
	_phase_t = 0.0
	_lift = {}
	_expr = "neutral"
	_expr_t = 0.0
	cursor = 0
	_guest_enter()
	_update_ui()


## "Neu anfangen": the current round starts over (coats of a finished round stay handed out).
func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	logic.reset_round()
	for key in _lift.keys():
		if str(key).begins_with(logic.kind() + ":"):
			_lift.erase(key)
	_phase = "ask"
	cursor = 0
	_clamp_cursor(1)
	_guest_enter()
	_update_ui()
	set_status(Kit.t("mg.cloak.wenzel.start"))
	_status_hold = 1.5


func _guest_enter() -> void:
	_shown_guest = logic.guest()
	_round_shown = mini(logic.round_i, Logic.ROUNDS.size() - 1)
	_slide = SLIDE_T
	_expr = "neutral"
	if _shown_guest != "":
		_sfx("mg_cloak_token", -6.0)


func _wenzel_say(key: String, hold: float) -> void:
	clear_status_hold()
	set_status(Kit.t("mg.cloak.say_fmt", {"name": Kit.t("mg.cloak.wenzel.name"), "line": Kit.t(key)}))
	_status_hold = hold
	_wenzel_talk = minf(hold, 2.0)


func _say(guest: String, key: String) -> String:
	return Kit.t("mg.cloak.say_fmt", {"name": Kit.t("mg.cloak.guest.%s.name" % guest), "line": Kit.t("mg.cloak.say." + key)})


# ================================================================ actions
func give_selected() -> void:
	if solved or ended or _phase != "ask":
		return
	var items: Array = logic.items()
	if cursor < 0 or cursor >= items.size():
		return
	var item := str(items[cursor])
	var r: Dictionary = logic.give(item)
	match str(r.get("reason", "")):
		"taken":
			set_status(Kit.t("mg.cloak.status.taken"))
			_status_hold = 1.4
		"wrong":
			_expr = "puzzled"
			_expr_t = 1.8
			_shake = 0.35
			register_fail(_say(str(r["guest"]), str(r["key"])))
		"":
			_last = r
			_last_item = item
			_last_kind = "coat" if int(r.get("round", 1)) == 1 else "hat"
			_lift[_last_kind + ":" + item] = 0.0
			_sfx("mg_cloak_coat" if int(r.get("round", 1)) == 1 else "mg_cloak_hat", -3.0)
			_expr = "pleased"
			_expr_t = THANKS_T + 0.4
			clear_status_hold()
			set_status(_say(str(r["guest"]), str(r["key"])))
			_status_hold = THANKS_T + 0.6
			_phase = "thanks"
			_phase_t = THANKS_T
	_update_ui()


func _advance_after_thanks() -> void:
	if logic.done:
		_phase = "end"
		_shown_guest = ""
		_wenzel_talk = 2.4
		_sfx("mg_cloak_bell", -4.0)
		mark_solved(Kit.t("mg.cloak.say_fmt", {"name": Kit.t("mg.cloak.wenzel.name"), "line": Kit.t("mg.cloak.wenzel.end")}))
		_update_ui()
		return
	if bool(_last.get("round_done", false)):
		_phase = "wenzel"
		_phase_t = WENZEL_T
		_shown_guest = ""
		_sfx("mg_cloak_bell", -5.0)
		_wenzel_say("mg.cloak.wenzel.hats", WENZEL_T + 0.8)
		cursor = 0
		_clamp_cursor(1)
		_update_ui()
		return
	_phase = "ask"
	_clamp_cursor(1)
	_guest_enter()
	_update_ui()


func _clamp_cursor(dir: int) -> void:
	var items: Array = logic.items()
	if items.is_empty():
		return
	cursor = clampi(cursor, 0, items.size() - 1)
	var guard := 0
	while not logic.available(str(items[cursor])) and guard < items.size() * 2:
		cursor = posmod(cursor + dir, items.size())
		guard += 1


func _move(d: int) -> void:
	var items: Array = logic.items()
	var c := cursor
	for i in items.size():
		c = clampi(c + d, 0, items.size() - 1)
		if logic.available(str(items[c])):
			break
	if logic.available(str(items[c])) and c != cursor:
		cursor = c
		Kit.ui_sound("tick")
		_update_ui()


func _hint_text(level: int) -> String:
	if logic.done:
		return ""
	if level >= 3:
		var w := logic.wanted()
		var name := Kit.t("mg.cloak.guest.%s.name" % logic.guest())
		return Kit.t("mg.cloak.hint.next", {"name": name, "item": _item_name(logic.kind(), w, true)})
	if logic.kind() == "hat":
		return Kit.t("mg.cloak.hint.hats")
	return Kit.t("mg.cloak.hint.%d" % clampi(level, 1, 2))


func _item_name(k: String, item: String, with_hook := false) -> String:
	var n := Kit.t("mg.cloak.%s.%s.name" % [k, item])
	if k == "coat" and with_hook:
		return "%s (%s)" % [n, Kit.t("mg.cloak.hook", {"n": Logic.hook_of(item)})]
	return n


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
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.cloak.ctrl.choose")],
		[Kit.action_key_text("interact"), Kit.t("mg.cloak.ctrl.give")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	_slide = maxf(0.0, _slide - delta)
	_shake = maxf(0.0, _shake - delta)
	_wenzel_talk = maxf(0.0, _wenzel_talk - delta)
	if _expr_t > 0.0:
		_expr_t -= delta
		if _expr_t <= 0.0:
			_expr = "neutral"
	for key in _lift.keys():
		_lift[key] = float(_lift[key]) + delta
	if _phase == "thanks" or _phase == "wenzel":
		_phase_t -= delta
		if _phase_t <= 0.0:
			if _phase == "thanks":
				_advance_after_thanks()
			else:
				_phase = "ask"
				_guest_enter()
				_update_ui()
	if _phase == "ask" and not solved and logic.guest() != "":
		if compact:
			status_auto(_say(logic.guest(), "%s.ask%d" % [logic.guest(), logic.round_i + 1]))
		else:
			status_auto(Kit.t("mg.cloak.status.ask", {"name": Kit.t("mg.cloak.guest.%s.name" % logic.guest()),
				"n": str(Logic.GUESTS[logic.guest()]["token"])}))
	for v in [_scene, _bust]:
		if v != null:
			v.queue_redraw()


func _update_ui() -> void:
	if _round_label == null:
		return
	if _hint_box != null and _hint_box.visible and not logic.done:
		_hint_label.text = _hint_text(maxi(1, hint_level))   # follows the guest and the round
	var r := _round_shown
	var total: int = (Logic.ROUNDS[r]["guests"] as Array).size()
	var n := total
	if r == logic.round_i and not logic.done:
		n = mini(logic.guest_i + 1, total)
	_round_label.text = (Kit.t("mg.cloak.round.%d" % (r + 1)) + " · " + Kit.t("mg.cloak.progress", {"n": n, "total": total})).to_upper().replace("ß", "SS")
	var g := _shown_guest
	var tl: Label = _token_icon.get_parent().get_node_or_null("TokenLabel")
	if g == "":
		_name_label.text = Kit.t("mg.cloak.wenzel.name")
		_role_label.text = Kit.t("mg.cloak.wenzel.role")
		_pin_label.text = ""
		_say_label.text = Kit.quoted(Kit.t("mg.cloak.wenzel.end" if logic.done else "mg.cloak.wenzel.hats"))
		if tl != null:
			tl.text = ""
	else:
		_name_label.text = Kit.t("mg.cloak.guest.%s.name" % g)
		_role_label.text = Kit.t("mg.cloak.guest.%s.role" % g)
		_pin_label.text = Kit.t("mg.cloak.guest.%s.%s" % [g, "wears" if _wears_coat() else "pin"])
		var line := "%s.ask%d" % [g, r + 1]
		if _phase == "thanks":
			line = str(_last.get("key", line))
		_say_label.text = Kit.quoted(Kit.t("mg.cloak.say." + line))
		if tl != null:
			tl.text = Kit.t("mg.cloak.token", {"n": str(Logic.GUESTS[g]["token"])}).to_upper().replace("ß", "SS")
	var it := ""
	var k := logic.kind()
	if _phase == "thanks" and _last_item != "":
		it = _last_item
		k = _last_kind
	else:
		var items: Array = logic.items()
		if cursor >= 0 and cursor < items.size():
			it = str(items[cursor])
	if it != "":
		var title := _item_name(k, it)
		if k == "coat":
			title = Kit.t("mg.cloak.hook", {"n": Logic.hook_of(it)}) + " · " + title
		_item_title.text = title.to_upper().replace("ß", "SS")
		_item_desc.text = Kit.t("mg.cloak.%s.%s.desc" % [k, it])
		if compact and k == "coat":
			_item_desc.text = Kit.t("mg.cloak.hook", {"n": Logic.hook_of(it)}) + " · " + _item_desc.text
	if _token_icon != null:
		_token_icon.queue_redraw()


## Guests wear their coat in round 2, and from the moment they receive it in round 1.
func _wears_coat() -> bool:
	return _round_shown >= 1 or (_phase == "thanks" and _last_kind == "coat")


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event)
	var pb := _pad(event)
	if k == KEY_R or pb == JOY_BUTTON_Y:
		restart()
		return true
	if _is(event, ["ui_left", "move_left"], true):
		if _phase == "ask":
			_move(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		if _phase == "ask":
			_move(1)
		return true
	if _is(event, ["ui_accept", "interact"]) or k == KEY_ENTER or k == KEY_SPACE or pb == JOY_BUTTON_A:
		if _input_guard <= 0.0:
			give_selected()
		return true
	if _is(event, ["ui_up", "move_up", "ui_down", "move_down"], true):
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _item_rect(k: String, i: int) -> Rect2:
	if k == "coat":
		var hx := float((layout.get("hooks_x", []) as Array)[i])
		var top := float(layout.get("coat_top", 46))
		return Rect2(hx - 18, top + 4, 36, float(layout.get("counter_y", 116)) - top - 4)
	var sx := float((layout.get("hats_x", []) as Array)[i])
	var sy := float(layout.get("shelf_y", 30))
	return Rect2(sx - 13, sy - 15, 26, 15)


func scene_input(event: InputEvent) -> void:
	if ended or solved or _phase != "ask":
		return
	var p: Vector2
	if event is InputEventMouseMotion:
		p = (event as InputEventMouseMotion).position / S
	elif event is InputEventMouseButton and event.pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		p = (event as InputEventMouseButton).position / S
	else:
		return
	var items: Array = logic.items()
	for i in items.size():
		if not logic.available(str(items[i])):
			continue
		if _item_rect(logic.kind(), i).has_point(p):
			if cursor != i:
				cursor = i
				_update_ui()
			if event is InputEventMouseButton:
				give_selected()
			return


# ================================================================ drawing (art px, x3)
func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var bt: Texture2D = _tex.get("cloak_back")
	if bt != null:
		v.draw_texture(bt, Vector2.ZERO)
	var hc := Kit.high_contrast()
	# coats on the rail (round 1 hands them out; Elena's stays)
	var ct: Texture2D = _tex.get("cloak_coats")
	var cc: Array = layout.get("coat_cell", [40, 78])
	var top := float(layout.get("coat_top", 46))
	var hooks: Array = layout.get("hooks_x", [])
	for i in Logic.COATS.size():
		var key := "coat:" + str(Logic.COATS[i])
		var dy := 0.0
		var alpha := 1.0
		if logic.taken.has(key):
			if not _lift.has(key) or float(_lift[key]) >= LIFT_T:
				continue
			var f := float(_lift[key]) / LIFT_T
			dy = -roundf(10.0 * f)
			alpha = 1.0 - f
		var sx := 0.0
		if _shake > 0.0 and logic.kind() == "coat" and i == cursor:
			sx = 1.0 if fmod(_shake * 30.0, 2.0) < 1.0 else -1.0
		if ct != null and i < hooks.size():
			v.draw_texture_rect_region(ct, Rect2(float(hooks[i]) - float(cc[0]) / 2.0 + sx, top + dy, float(cc[0]), float(cc[1])),
				Rect2(i * float(cc[0]), 0, float(cc[0]), float(cc[1])), Color(1, 1, 1, alpha))
	# hats on the shelf
	var ht: Texture2D = _tex.get("cloak_hats")
	var hcell: Array = layout.get("hat_cell", [28, 16])
	var shelf := float(layout.get("shelf_y", 30))
	var hxs: Array = layout.get("hats_x", [])
	for i in Logic.HATS.size():
		var key2 := "hat:" + str(Logic.HATS[i])
		var dy2 := 0.0
		var a2 := 1.0
		if logic.taken.has(key2):
			if not _lift.has(key2) or float(_lift[key2]) >= LIFT_T:
				continue
			var f2 := float(_lift[key2]) / LIFT_T
			dy2 = -roundf(8.0 * f2)
			a2 = 1.0 - f2
		var sx2 := 0.0
		if _shake > 0.0 and logic.kind() == "hat" and i == cursor:
			sx2 = 1.0 if fmod(_shake * 30.0, 2.0) < 1.0 else -1.0
		if ht != null and i < hxs.size():
			v.draw_texture_rect_region(ht, Rect2(float(hxs[i]) - float(hcell[0]) / 2.0 + sx2, shelf - float(hcell[1]) + dy2,
				float(hcell[0]), float(hcell[1])), Rect2(i * float(hcell[0]), 0, float(hcell[0]), float(hcell[1])), Color(1, 1, 1, a2))
	# Herr Wenzel behind the counter: polishing, blinking now and then, talking when he speaks
	var wt: Texture2D = _tex.get("cloak_wenzel")
	if wt != null:
		var wc: Array = layout.get("wenzel_cell", [46, 60])
		var wa: Array = layout.get("wenzel_at", [2, 58])
		var fi := 0
		if _wenzel_talk > 0.0:
			fi = 2 if fmod(_anim * 6.0, 2.0) < 1.0 else 0
		elif fmod(_anim, 4.3) > 4.1:
			fi = 1
		var bob := -1.0 if (fi == 0 and fmod(_anim * 1.4, 2.0) < 1.0 and not Kit.reduced_motion()) else 0.0
		v.draw_texture_rect_region(wt, Rect2(float(wa[0]), float(wa[1]) + bob, float(wc[0]), float(wc[1])),
			Rect2(fi * float(wc[0]), 0, float(wc[0]), float(wc[1])))
	var ft: Texture2D = _tex.get("cloak_front")
	if ft != null:
		v.draw_texture(ft, Vector2.ZERO)
	# the guest's brass check on the counter
	if _shown_guest != "" and _phase != "end":
		_draw_token(v, Vector2(layout.get("token_at", [226, 104])[0], layout.get("token_at", [226, 104])[1]), _shown_guest)
	# cursor around the chosen coat / hat
	if _phase == "ask" and not solved:
		var items: Array = logic.items()
		if cursor >= 0 and cursor < items.size() and logic.available(str(items[cursor])):
			var r := _item_rect(logic.kind(), cursor)
			var col := COL_WHITE if hc else COL_AMBER
			v.draw_rect(r.grow(1.5), col, false, 1.0)
			if hc:
				v.draw_rect(r.grow(2.5), Color(0, 0, 0), false, 1.0)
			var mx := roundf(r.get_center().x)
			var my := r.position.y - 3.0 if logic.kind() == "coat" else r.end.y + 9.0
			if logic.kind() == "coat":
				v.draw_colored_polygon(PackedVector2Array([Vector2(mx - 3, my - 3), Vector2(mx + 4, my - 3), Vector2(mx + 0.5, my + 0.5)]), col)
			else:
				v.draw_colored_polygon(PackedVector2Array([Vector2(mx - 3, my), Vector2(mx + 4, my), Vector2(mx + 0.5, my - 3.5)]), col)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_token(v: Control, at: Vector2, guest: String) -> void:
	var tt: Texture2D = _tex.get("cloak_tokens")
	if tt == null:
		return
	var idx := (layout.get("tokens", Logic.HOOK_NUMBERS) as Array).find(str(Logic.GUESTS[guest]["token"]))
	if idx < 0:
		return
	v.draw_texture_rect_region(tt, Rect2(at, Vector2(14, 14)), Rect2(idx * 14, 0, 14, 14))


func draw_token(v: Control) -> void:
	if _shown_guest == "":
		return
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	_draw_token(v, Vector2.ZERO, _shown_guest)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func draw_bust(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var gc: Array = layout.get("guest_cell", [64, 72])
	var w := float(gc[0])
	var h := float(gc[1])
	v.draw_rect(Rect2(0, 0, w, h), Color("10181f"))
	v.draw_rect(Rect2(0, h * 0.55, w, h * 0.45), Color("172229"))
	var gt: Texture2D = _tex.get("cloak_guests")
	if _shown_guest != "" and gt != null:
		var row := (layout.get("guests", ["imhof", "orlova", "duval", "bauer"]) as Array).find(_shown_guest)
		var colx := int(EXPR.get(_expr, 0)) + (3 if _wears_coat() else 0)
		var off := roundf(40.0 * (_slide / SLIDE_T)) if not Kit.reduced_motion() else 0.0
		v.draw_texture_rect_region(gt, Rect2(off, 0, w, h), Rect2(colx * w, row * h, w, h))
	elif _tex.get("cloak_wenzel") != null:
		# between rounds and at the end Herr Wenzel turns to Konrad
		var wt: Texture2D = _tex["cloak_wenzel"]
		var fi := 2 if (_wenzel_talk > 0.0 and fmod(_anim * 6.0, 2.0) < 1.0) else 0
		v.draw_texture_rect_region(wt, Rect2(9, 10, 46, 60), Rect2(fi * 46, 0, 46, 60))
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 90000:
		if _phase != "ask" or _input_guard > 0.0:
			await _frames(2)
			continue
		var target: int = logic.items().find(logic.wanted())
		if target < 0:
			await _frames(2)
			continue
		var guard := 0
		while cursor != target and guard < 12 and not ended:
			await _tap(KEY_RIGHT if cursor < target else KEY_LEFT)
			guard += 1
		await _tap(KEY_ENTER)
		await _until(func(): return _phase != "ask" or solved, 2.0)
	await _until(func(): return solved, 4.0)
