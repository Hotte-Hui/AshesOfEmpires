extends "res://scripts/ui/minigames/minigame_base.gd"
## Annex mini-game „Die Datenstelle“ (scenes/ui/minigames/DataTerminal.tscn, explore entry berlin.annex.term_files,
## third step of the side task „Planspiel Abgang“ at the data desk of Nebenstelle Süd, L_C4_Annex scene D; §12.8).
## Sunday, 6.12: between the machine room and the household index stands the data desk — vector display,
## teleprinter, tape cabinet, card reader. Konrad logs in with the operator number he read on the duty roster
## (Fräulein Kunze's), reads what the tape holds about Süd 8 — the transfer lists C-17/45 and C-17/44, Kommissar
## Wendt's memo, the operator's log, the post scheme — and releases the locked program „Planspiel Abgang“ with the
## case number the memo means: the household whose „Verbleib“ is still open in the list (cross-reference of two
## files; a wrong case is a refusal, hints after two per Settings `puzzle_hints`).
## Rule: terminal_logic.gd (menu-driven: nothing but the number is ever typed, so it plays on a pad). The picture is
## a text raster in the game's own pixel capitals shown through crt_kit.gd's phosphor (x3; larger text: a smaller
## raster at x4, so the letters grow with the text scale).
## Sounds (tools/audiogen/mg_audio_terminal.py): mg_term_hum (loop), mg_term_relay, mg_term_key, mg_term_ok,
## mg_term_refuse, mg_term_tape.
## Keys: 0-9 type the number · Left/Right choose a digit, Up/Down turn it · Up/Down choose a line (scroll a file) ·
## E, Enter, Space or pad A confirm · Backspace, Esc or pad B one step back (Esc at the menu gives up) · R or pad Y
## logs out and starts over. Mouse: click a digit, a line or the button „Eingabe“; wheel turns / scrolls; right
## click goes back.

const Logic := preload("res://scripts/ui/minigames/terminal_logic.gd")
const Crt := preload("res://scripts/ui/minigames/crt_kit.gd")
const ART := Vector2i(384, 172)
const ART_COMPACT := Vector2i(300, 106)
const SND := "res://assets/audio/sfx/"
const BLINK := 0.42
const SIDE_W := 430

var logic = Logic.new()
var S := 3
var compact := false
var art := ART
var _stage: Control
var _tube: TextureRect
var _tex: ImageTexture
var _caret_on := true
var _blink_left := BLINK
var _dirty := true
var _hum: AudioStreamPlayer
var _input_guard := 0.0
var _topic_fails := {}


class View extends Control:
	var game: Node

	func _draw() -> void:
		game.call("draw_stage", self)

	func _gui_input(event: InputEvent) -> void:
		game.call("stage_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.term.kicker", "mg.term.title", "mg.term.subtitle", "mg.term.instruction")
	compact = Kit.text_scale() > 1.01
	S = 4 if compact else 3
	art = ART_COMPACT if compact else ART
	if compact:          # larger text: the flavour lines give way to the tube, the status and the hint
		_subtitle.visible = false
		_instr.visible = false
	logic.tr_fn = func(k: String, a: Dictionary) -> String: return Kit.t(k, a)
	var row := Kit.hbox(36)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	Kit.full_rect(row)
	area.add_child(row)
	var v := View.new()
	v.game = self
	v.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	v.custom_minimum_size = Crt.housing_size(art, S)
	v.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	row.add_child(v)
	_stage = v
	_tube = TextureRect.new()
	_tube.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_tube.stretch_mode = TextureRect.STRETCH_SCALE
	_tube.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tube.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var r := Crt.tube_rect(art, S)
	_tube.position = r.position
	_tube.size = r.size
	_tube.material = Crt.tube_material(art, Kit.high_contrast())
	v.add_child(_tube)
	area.custom_minimum_size.y = v.custom_minimum_size.y
	if not compact:      # the flavour and the instruction stand beside the tube, so the raster can be taller
		var side := Kit.vbox(18)
		side.custom_minimum_size.x = SIDE_W
		side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		for l in [_subtitle, _instr]:
			l.get_parent().remove_child(l)
			side.add_child(l)
		row.add_child(side)
	_add_button(Kit.t("mg.term.btn.ok"), func(): _act("ok"), 250, true)
	_hum = _loop_player(SND + "mg_term_hum.wav")


func open(context: Dictionary = {}) -> void:
	super.open(context)
	_input_guard = 0.3
	if int(Kit.setting("puzzle_hints", 1)) == 2:
		show_hint(1)
	set_status(Kit.t("mg.term.status.login"))
	if not bool(ctx.get("auto", false)) and _hum != null and _hum.stream != null:
		_hum.volume_db = -26.0
		_hum.play()


func _on_end() -> void:
	if _hum != null:
		_hum.stop()


func _reset_game() -> void:
	logic.reset()
	_topic_fails = {}
	_dirty = true


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	_hint_box.visible = false
	hint_level = 0
	if int(Kit.setting("puzzle_hints", 1)) == 2:
		show_hint(1)
	set_status(Kit.t("mg.term.status.restart"))
	_status_hold = 1.6


# ================================================================ actions
func _act(what: String, arg := 0) -> void:
	if solved or ended:
		return
	var ev := ""
	match what:
		"digit":
			ev = logic.digit(arg)
		"up":
			ev = logic.move(0, -1)
		"down":
			ev = logic.move(0, 1)
		"left":
			ev = logic.move(-1, 0)
		"right":
			ev = logic.move(1, 0)
		"ok":
			ev = logic.ok()
		"back":
			ev = logic.back()
	_after(ev)


func _after(ev: String) -> void:
	if ev == "":
		return
	_dirty = true
	_caret_on = true
	_blink_left = BLINK
	match ev:
		"key":
			_sfx("mg_term_key", -8.0)
		"move":
			_sfx("mg_term_relay", -14.0)
		"enter", "open", "back", "locked":
			_sfx("mg_term_relay", -9.0)
			clear_status_hold()
		"login_ok":
			_sfx("mg_term_ok", -6.0)
			_hint_box.visible = false
			hint_level = 0
			if int(Kit.setting("puzzle_hints", 1)) == 2:
				show_hint(1)
			set_status(Kit.t("mg.term.status.menu"))
			_status_hold = 2.4
		"login_fail":
			_sfx("mg_term_refuse", -8.0)
			register_fail(Kit.t("mg.term.status.refused"))
		"release_fail":
			_sfx("mg_term_refuse", -8.0)
			register_fail(Kit.t("mg.term.status.release_fail"))
		"release_unknown":
			_sfx("mg_term_refuse", -12.0)
			set_status(Kit.t("mg.term.status.release_unknown"))
			_status_hold = STATUS_HOLD
		"release_ok":
			_sfx("mg_term_tape", -6.0)
			mark_solved(Kit.t("mg.term.solved"))


## Which riddle the player is at: the number or the release.
func topic() -> String:
	return "login" if logic.phase == "login" else "release"


func _hint_text(level: int) -> String:
	if logic.released:
		return ""
	return Kit.t("mg.term.hint.%s.%d" % [topic(), clampi(level, 1, 2)])


## Settings "puzzle_hints" (like the other puzzles): 0 never, 1 after two refusals of the same riddle (default), 2 at
## once and one level more with every refusal.
func register_fail(text: String) -> void:
	fails += 1
	var tp := topic()
	_topic_fails[tp] = int(_topic_fails.get(tp, 0)) + 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	var mode := int(Kit.setting("puzzle_hints", 1))
	var n := int(_topic_fails[tp])
	if mode == 1 and n >= HINT_AFTER:
		show_hint(n - HINT_AFTER + 1)
	elif mode == 2:
		show_hint(n + 1)


func _cancel_step() -> bool:
	var ev: String = logic.back()
	if ev == "":
		return false
	_after(ev)
	return true


func _controls() -> Array:
	if logic.phase == "login":
		return [["0–9", Kit.t("mg.term.ctrl.digit")],
			[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("mg.term.ctrl.place")],
			[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN), Kit.t("mg.term.ctrl.turn")],
			[Kit.action_key_text("interact"), Kit.t("mg.term.ctrl.login")],
			["R", Kit.t("mg.common.ctrl.restart")]]
	return [[Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN), Kit.t("mg.term.ctrl.line")],
		[Kit.action_key_text("interact"), Kit.t("mg.term.ctrl.ok")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("mg.term.ctrl.back")],
		["R", Kit.t("mg.common.ctrl.restart")]]


# ================================================================ per frame
func _tick(delta: float) -> void:
	_input_guard = maxf(0.0, _input_guard - delta)
	if not Kit.reduced_motion():
		_blink_left -= delta
		if _blink_left <= 0.0:
			_blink_left = BLINK
			_caret_on = not _caret_on
			if logic.phase == "login":
				_dirty = true
	elif not _caret_on:
		_caret_on = true
		_dirty = true
	if not solved:
		status_auto(Kit.t("mg.term.status." + ("login" if logic.phase == "login" else "idle")))
	if _dirty:
		refresh()
	Crt.snap(_tube, S, Crt.tube_rect(art, S).position)


## Letters the logic's screen into the tube's texture.
func refresh() -> void:
	_dirty = false
	var g := Crt.grid(art)
	var scr: Dictionary = logic.screen(g.x, g.y)
	var runs: Array = scr["runs"]
	var caret = scr.get("caret")
	if caret != null and _caret_on:
		runs.append({"box": [3 + int(caret[0]) * Crt.CELL.x, 3 + int(caret[1]) * Crt.CELL.y + 9, 5, 1], "lv": 3})
	var img := Crt.raster(runs, art)
	if _tex == null:
		_tex = ImageTexture.create_from_image(img)
		_tube.texture = _tex
	else:
		_tex.update(img)


func draw_stage(v: Control) -> void:
	Crt.draw_housing(v, art, S, "SG 1", 1, Kit.high_contrast())


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event, true)
	var pb := _pad(event)
	if event is InputEventKey and (event as InputEventKey).pressed and not (event as InputEventKey).echo:
		if k >= KEY_0 and k <= KEY_9:
			_act("digit", k - KEY_0)
			return true
		if k >= KEY_KP_0 and k <= KEY_KP_9:
			_act("digit", k - KEY_KP_0)
			return true
		if k == KEY_R:
			restart()
			return true
		if k == KEY_BACKSPACE:
			_act("back")
			return true
	if pb == JOY_BUTTON_Y:
		restart()
		return true
	if _is(event, ["ui_up", "move_up"], true):
		_act("up")
		return true
	if _is(event, ["ui_down", "move_down"], true):
		_act("down")
		return true
	if _is(event, ["ui_left", "move_left"], true):
		_act("left")
		return true
	if _is(event, ["ui_right", "move_right"], true):
		_act("right")
		return true
	if event is InputEventKey and (event as InputEventKey).echo:
		return true
	if _is(event, ["ui_accept", "interact"]) or k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE or k == KEY_E \
			or pb == JOY_BUTTON_A:
		if _input_guard <= 0.0:
			_act("ok")
		return true
	return false


## Text cell under a point of the stage (screen px): Vector2i(col, row), (-1, -1) outside the glass.
func cell_at(p: Vector2) -> Vector2i:
	var r := Crt.tube_rect(art, S)
	if not r.has_point(p):
		return Vector2i(-1, -1)
	var a := (p - r.position) / float(S)
	return Vector2i(int(floor((a.x - 3.0) / float(Crt.CELL.x))), int(floor((a.y - 3.0) / float(Crt.CELL.y))))


func stage_input(event: InputEvent) -> void:
	if ended or solved or not (event is InputEventMouseButton) or not (event as InputEventMouseButton).pressed:
		return
	var mb := event as InputEventMouseButton
	match mb.button_index:
		MOUSE_BUTTON_WHEEL_UP:
			_act("up")
		MOUSE_BUTTON_WHEEL_DOWN:
			_act("down")
		MOUSE_BUTTON_RIGHT:
			_act("back")
		MOUSE_BUTTON_LEFT:
			var c := cell_at(mb.position)
			if c.x >= 0:
				_after(logic.click(c.x, c.y))


# ================================================================ demo (synthetic keys only)
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	await _until(func(): return _input_guard <= 0.0, 2.0)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 60000:
		match str(logic.phase):
			"login":
				var wrong := -1
				for i in 4:
					if int(logic.digits[i]) != int(Logic.OPERATOR[i]):
						wrong = i
						break
				if wrong < 0:
					await _tap(KEY_ENTER)
				else:
					var guard := 0
					while int(logic.digit_cursor) != wrong and guard < 6 and not ended:
						await _tap(KEY_RIGHT if int(logic.digit_cursor) < wrong else KEY_LEFT)
						guard += 1
					await _tap(KEY_0 + int(Logic.OPERATOR[wrong]))
			"menu":
				await _demo_pick(Logic.COMMANDS.find("open"))
			"open":
				await _demo_pick(Logic.FILES.size() if logic.known_cases else Logic.FILES.find(Logic.CASE_FILE))
			"release":
				var target := 0
				var list: Array = logic.cases()
				for i in list.size():
					if str(list[i]["id"]) == Logic.ANSWER:
						target = i
				await _demo_pick(target)
			_:
				await _tap(KEY_BACKSPACE)
		await _frames(2)
	await _until(func(): return solved, 4.0)


func _demo_pick(target: int) -> void:
	var guard := 0
	while int(logic.cursor) != target and guard < 12 and not ended:
		await _tap(KEY_DOWN if int(logic.cursor) < target else KEY_UP)
		guard += 1
	await _tap(KEY_ENTER)
