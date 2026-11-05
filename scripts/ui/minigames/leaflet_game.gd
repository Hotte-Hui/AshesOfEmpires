extends "res://scripts/ui/minigames/minigame_base.gd"
## Plaza "Das Blatt im Schnee" (scenes/ui/minigames/LeafletSnow.tscn, explore entry plaza.leaflet, §12.8).
## At the barrier during the parade a typed carbon copy ("WER FEHLT?") drifts through the snow. Konrad walks along
## the pavement, may hold the sheet with his foot against the wind and bends down for it while neither post looks
## over the crowd. Being noticed is gentle: he straightens up, the post looks at him a moment, nothing is lost.
## Logic: leaflet_logic.gd. Art: assets/ui/minigames/plaza/ (tools/pixelgen/gen_minigame_plaza.py, 1:1 art px,
## drawn x3) plus the existing sprite sheets of konrad and guard and Konrad's portrait (read-only).
## Keys: Left/Right (A/D, d-pad, stick) walk; hold Down (S) or E/Space (pad A) to bend; Esc gives up.
## Mouse: click on the pavement to walk there, hold the button on Konrad to bend.

const Logic := preload("res://scripts/ui/minigames/leaflet_logic.gd")
const S := 3
const ART := "res://assets/ui/minigames/plaza/"
const KONRAD := "res://assets/characters/konrad/"
const GUARD := "res://assets/characters/guard/"
const BEND_KEYS := ["ui_down", "move_down", "interact"]

var logic = Logic.new()
var layout: Dictionary = {}
var _tex: Dictionary = {}
var _ksheet: Dictionary = {}
var _gsheet: Dictionary = {}
var _view: Control
var _portrait: Control
var _guard_labels: Array = []
var _wind_label: Label
var _anim := 0.0
var _input_guard := 0.0
var _surprised := 0.0
var _walk_target := -1.0
var _mouse_bend := false
var _taken := 0.0          # seconds since the sheet was picked up (it rises into the coat)


class View extends Control:
	var game: Node
	var kind := ""

	func _draw() -> void:
		game.call("draw_" + kind, self)

	func _gui_input(event: InputEvent) -> void:
		if kind == "scene":
			game.scene_input(event)


func _build_play(area: Control) -> void:
	set_texts("mg.leaflet.kicker", "mg.leaflet.title", "mg.leaflet.subtitle", "mg.leaflet.instruction")
	var lj = Kit.json(ART + "leaflet_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["leaflet_back", "leaflet_march", "leaflet_barrier", "leaflet_front", "leaflet_bend", "leaflet_sheet"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	_tex["konrad"] = Kit.optional_tex(KONRAD + "sheet.png")
	_tex["guard"] = Kit.optional_tex(GUARD + "sheet.png")
	_tex["portrait"] = Kit.optional_tex(KONRAD + "portrait.png")
	var kj = Kit.json(KONRAD + "sheet.json")
	_ksheet = kj if kj is Dictionary else {}
	var gj = Kit.json(GUARD + "sheet.json")
	_gsheet = gj if gj is Dictionary else {}
	var row := Kit.hbox(48)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var sz: Array = layout.get("size", [300, 124])
	_view = View.new()
	_view.game = self
	_view.kind = "scene"
	_view.clip_contents = true
	_view.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_view.mouse_filter = Control.MOUSE_FILTER_STOP
	_view.custom_minimum_size = Vector2(float(sz[0]), float(sz[1])) * S
	_view.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_view)
	var side := Kit.vbox(10)
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(side)
	var frame := Kit.panel("PortraitPanel")
	frame.size_flags_horizontal = Control.SIZE_SHRINK_CENTER   # the frame hugs the portrait, labels may be wider
	side.add_child(frame)
	_portrait = View.new()
	_portrait.game = self
	_portrait.kind = "portrait"
	_portrait.clip_contents = true
	_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_portrait.custom_minimum_size = Vector2(224, 224)
	_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_portrait)
	for g in 2:
		var l := Kit.label("", "KickerLabel")
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		side.add_child(l)
		_guard_labels.append(l)
	_wind_label = Kit.label("", "DimLabel")
	_wind_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	side.add_child(_wind_label)


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_input_guard = 0.4


func _reset_game() -> void:
	logic.reset()
	_anim = 0.0
	_surprised = 0.0
	_walk_target = -1.0
	_mouse_bend = false
	_taken = 0.0
	_update_labels()
	_redraw()


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_input_guard = maxf(0.0, _input_guard - delta)
	_surprised = maxf(0.0, _surprised - delta)
	if solved:
		_taken += delta
		logic.bend = maxf(0.0, logic.bend - delta / Logic.BEND_OUT)
	else:
		var l := _held(["ui_left", "move_left"])
		var r := _held(["ui_right", "move_right"])
		var dir := 0
		if l != r:
			dir = -1 if l else 1
			_walk_target = -1.0
		elif _walk_target >= 0.0:
			var d: float = _walk_target - logic.k
			if absf(d) <= 0.006:
				_walk_target = -1.0
			else:
				dir = 1 if d > 0.0 else -1
		var bend_held := _input_guard <= 0.0 and (_mouse_bend or _held(BEND_KEYS))
		for e in logic.step(delta, dir, bend_held):
			match str(e):
				"gust":
					Kit.ui_sound_first(["paper_rustle", "page_turn"])
				"pinned":
					clear_status_hold()
				"noticed":
					_surprised = 1.6
					_mouse_bend = false
					register_fail(Kit.t("mg.leaflet.fail.noticed"))
				"nothing":
					set_status(Kit.t("mg.leaflet.status.nothing"))
					_status_hold = 1.8
				"solved":
					Kit.ui_sound_first(["paper_rustle", "page_turn"])
					mark_solved(Kit.t("mg.leaflet.solved"))
	_update_labels()
	_redraw()


func _held(actions: Array) -> bool:
	for a in actions:
		if InputMap.has_action(a) and Input.is_action_pressed(a):
			return true
	return false


func _update_labels() -> void:
	for g in _guard_labels.size():
		var st := str(logic.guard_state(g)[0])
		var lab: Label = _guard_labels[g]
		lab.text = (Kit.t("mg.leaflet.guard." + ("left" if g == 0 else "right")) + " · "
			+ Kit.t("mg.leaflet.guard." + st)).to_upper()
		var c := Kit.C_TEXT_DIM
		match st:
			"turn":
				c = Kit.C_AMBER
			"sweep":
				c = Kit.C_COPPER_L
			"stare":
				c = Kit.C_STAMP
		lab.add_theme_color_override("font_color", c)
	if _wind_label:
		_wind_label.text = (Kit.t("mg.leaflet.wind") + " · " + Kit.t("mg.leaflet.wind." + ("gust" if logic.gusting else "calm"))).to_upper()
	if solved:
		return
	var states := [str(logic.guard_state(0)[0]), str(logic.guard_state(1)[0])]
	if logic.bend > 0.05:
		status_auto(Kit.t("mg.leaflet.status.bend"))
	elif logic.pinned:
		status_auto(Kit.t("mg.leaflet.status.pinned"))
	elif logic.gusting:
		status_auto(Kit.t("mg.leaflet.status.gust"))
	elif "sweep" in states:
		status_auto(Kit.t("mg.leaflet.status.sweep"))
	elif "turn" in states:
		status_auto(Kit.t("mg.leaflet.status.turn"))
	elif logic.on_sheet():
		status_auto(Kit.t("mg.leaflet.status.foot"))
	else:
		status_auto(Kit.t("mg.leaflet.status.walk"))


func _redraw() -> void:
	for v in [_view, _portrait]:
		if v != null:
			v.queue_redraw()


func _hint_text(level: int) -> String:
	return Kit.t("mg.leaflet.hint.%d" % clampi(level, 1, 2))


func _controls() -> Array:
	return [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.leaflet.ctrl.walk")],
		[Kit.key_name(KEY_DOWN), Kit.t("mg.leaflet.ctrl.bend")]]


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	if _is(event, ["ui_left", "move_left", "ui_right", "move_right", "ui_down", "move_down", "interact"], true):
		return true          # polled in _tick; consumed here so nothing behind the modal reacts
	if event is InputEventKey and event.echo:
		return true
	return false


func lane_x(v: float) -> float:
	var ln: Array = layout.get("lane", [40, 260])
	return lerpf(float(ln[0]), float(ln[1]), v)


func scene_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := event as InputEventMouseButton
		if not mb.pressed:
			_mouse_bend = false
			return
		var p := mb.position / S
		var ln: Array = layout.get("lane", [40, 260])
		if p.y >= 60.0 and absf(p.x - lane_x(logic.k)) <= 10.0:
			_mouse_bend = true
			_walk_target = -1.0
		elif p.y >= 60.0:
			_walk_target = clampf((p.x - float(ln[0])) / maxf(1.0, float(ln[1]) - float(ln[0])), 0.0, 1.0)


# ================================================================ drawing (art px, x3)
func _cell(sheet: Dictionary, anim: String) -> Array:
	var a: Dictionary = (sheet.get("anims", {}) as Dictionary).get(anim, {})
	return [int(a.get("row", 0)), int(a.get("frames", 1)), float(a.get("fps", 6.0))]


func _draw_frame(v: Control, tex: Texture2D, cell: Vector2, origin: Vector2, col: int, row: int, feet: Vector2,
		flip: bool, mod := Color.WHITE) -> void:
	if tex == null:
		return
	var src := Rect2(Vector2(col, row) * cell, cell)
	var x0 := feet.x - (cell.x - origin.x if flip else origin.x)
	var dst := Rect2(Vector2(roundf(x0), roundf(feet.y - origin.y)), cell)
	if flip:
		dst = Rect2(dst.position + Vector2(cell.x, 0), Vector2(-cell.x, cell.y))
	v.draw_texture_rect_region(tex, dst, src, mod)


func draw_scene(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var bt: Texture2D = _tex.get("leaflet_back")
	if bt != null:
		v.draw_texture(bt, Vector2.ZERO)
	else:
		v.draw_rect(Rect2(Vector2.ZERO, v.size / S), Kit.C_NAVY)
	var mt: Texture2D = _tex.get("leaflet_march")
	if mt != null:
		var off := fposmod(_anim * float(layout.get("march_speed", 7.0)), float(mt.get_width()))
		var my := float(layout.get("march_y", 40))
		v.draw_texture(mt, Vector2(roundf(-off), my))
		v.draw_texture(mt, Vector2(roundf(-off) + mt.get_width(), my))
	for g in 2:
		_draw_guard(v, g)
	var br: Texture2D = _tex.get("leaflet_barrier")
	if br != null:
		v.draw_texture(br, Vector2(0, float(layout.get("barrier_y", 62))))
	for g in 2:
		_draw_gaze(v, g)
	_draw_sheet(v)
	_draw_konrad(v)
	var ft: Texture2D = _tex.get("leaflet_front")
	if ft != null:
		v.draw_texture(ft, Vector2.ZERO)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _guard_pos(g: int) -> Vector2:
	var gs: Array = layout.get("guards", [[92, 80], [212, 80]])
	return Vector2(float(gs[g][0]), float(gs[g][1]))


func _draw_guard(v: Control, g: int) -> void:
	var st: Array = logic.guard_state(g)
	var cell := Vector2(32, 56)
	var origin := Vector2(16, 54)
	if _gsheet.has("cell"):
		cell = Vector2(float(_gsheet["cell"][0]), float(_gsheet["cell"][1]))
		origin = Vector2(float(_gsheet["origin"][0]), float(_gsheet["origin"][1]))
	var anim := "idle_side"
	var fi := 0
	match str(st[0]):
		"away":
			var c := _cell(_gsheet, "idle_side")
			fi = int(_anim * float(c[2]) + g * 3) % int(c[1])
		"turn":
			anim = "look_side"
			var c2 := _cell(_gsheet, anim)
			fi = clampi(int(float(st[1]) * float(c2[1])), 0, int(c2[1]) - 1)
		_:
			anim = "idle_front"
			var c3 := _cell(_gsheet, anim)
			fi = int(_anim * float(c3[2])) % int(c3[1])
	var rc := _cell(_gsheet, anim)
	var flip := g == 0 and anim != "idle_front"   # the left post looks left down the avenue, the right one right
	_draw_frame(v, _tex.get("guard"), cell, origin, fi, int(rc[0]), _guard_pos(g), flip, Color(0.8, 0.8, 0.88))


func _draw_gaze(v: Control, g: int) -> void:
	var gz: float = logic.gaze(g)
	if gz < 0.0:
		return
	var eye := _guard_pos(g) + Vector2(0, float(layout.get("eye_dy", -44)))
	var cx := lane_x(gz)
	var hw := Logic.GAZE_HALF * (lane_x(1.0) - lane_x(0.0))
	var y := float(layout.get("feet_y", 114)) + 3.0
	var stare := str(logic.guard_state(g)[0]) == "stare"
	var col := Color(0.95, 0.62, 0.45, 0.16) if stare else Color(1.0, 0.88, 0.66, 0.09)
	v.draw_colored_polygon(PackedVector2Array([eye, Vector2(cx - hw, y), Vector2(cx + hw, y)]), col)
	var pts := PackedVector2Array()
	for i in 20:
		var a := TAU * i / 20.0
		pts.append(Vector2(cx + cos(a) * hw, y - 3.0 + sin(a) * 6.0))
	v.draw_colored_polygon(pts, Color(col, col.a + 0.08))


func _draw_sheet(v: Control) -> void:
	var st: Texture2D = _tex.get("leaflet_sheet")
	if st == null:
		return
	var sy := float(layout.get("sheet_y", 113))
	var pos := Vector2(roundf(lane_x(logic.sheet) - 6.0), sy - 7.0)
	var fi := 0
	if solved:
		if _taken > 0.5:
			return
		fi = 2
		pos = Vector2(roundf(lane_x(logic.k) + 2.0 * logic.facing - 6.0), roundf(sy - 7.0 - 28.0 * _taken / 0.5))
	elif logic.gusting:
		fi = 1 if logic.pinned else (1 + int(_anim * 10.0) % 2)
	v.draw_texture_rect_region(st, Rect2(pos, Vector2(12, 8)), Rect2(fi * 12, 0, 12, 8))


func _draw_konrad(v: Control) -> void:
	var feet := Vector2(roundf(lane_x(logic.k)), float(layout.get("feet_y", 114)))
	var flip: bool = logic.facing < 0
	if logic.bend > 0.05:
		var bi := 0 if logic.bend < 0.4 else (1 if logic.bend < 0.8 else 2)
		var bc: Array = layout.get("bend_cell", [40, 56])
		var bo: Array = layout.get("bend_origin", [16, 54])
		_draw_frame(v, _tex.get("leaflet_bend"), Vector2(float(bc[0]), float(bc[1])), Vector2(float(bo[0]), float(bo[1])),
			bi, 0, feet, flip)
		return
	var cell := Vector2(32, 56)
	var origin := Vector2(16, 54)
	if _ksheet.has("cell"):
		cell = Vector2(float(_ksheet["cell"][0]), float(_ksheet["cell"][1]))
		origin = Vector2(float(_ksheet["origin"][0]), float(_ksheet["origin"][1]))
	var anim := "walk_side" if logic.moving and not solved else "idle_side"
	var c := _cell(_ksheet, anim)
	var fps := float(c[2])
	if anim == "walk_side":   # feet stay planted: playback follows the walking speed
		var gs = _ksheet.get("ground_speed", {})
		var base := float(gs.get("walk_side", 35.0)) if gs is Dictionary else 35.0
		fps = fps * Logic.WALK * (lane_x(1.0) - lane_x(0.0)) / maxf(1.0, base)
	var fi := int(_anim * fps) % int(c[1])
	_draw_frame(v, _tex.get("konrad"), cell, origin, fi, int(c[0]), feet, flip)


func draw_portrait(v: Control) -> void:
	var pt: Texture2D = _tex.get("portrait")
	var expr := 0
	if _surprised > 0.0:
		expr = 3
	elif solved or logic.bend > 0.05:
		expr = 2
	elif not logic.calm():
		expr = 1
	if pt != null:
		v.draw_texture_rect_region(pt, Rect2(Vector2.ZERO, Vector2(224, 224)), Rect2(expr * 112, 0, 112, 112))
	else:
		v.draw_rect(Rect2(Vector2.ZERO, Vector2(224, 224)), Kit.C_NAVY)


# ================================================================ synthetic solve (real-input driver)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 90000:
		var d: float = logic.sheet - logic.k
		if absf(d) > Logic.REACH * 0.5:
			var key := KEY_RIGHT if d > 0.0 else KEY_LEFT
			_key_event(key, true)
			await _until(func(): return absf(logic.sheet - logic.k) <= Logic.REACH * 0.5 \
				or signf(logic.sheet - logic.k) != signf(d), 8.0)
			_key_event(key, false)
			await _frames(2)
			continue
		if logic.calm_left() < Logic.BEND_IN + 0.4:
			await _frames(2)
			continue
		_key_event(KEY_DOWN, true)
		await _until(func(): return solved or logic.calm_left() <= 0.0 or not logic.over_sheet(), 3.0)
		_key_event(KEY_DOWN, false)
		await _frames(3)
