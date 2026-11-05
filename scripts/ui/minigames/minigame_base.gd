extends "res://scripts/ui/ui_modal.gd"
## Base of the optional mini-games (TECHNICAL_ARCHITECTURE §12.8). Game instances the scene under the UI root,
## calls open(ctx) with ctx = {"explore_id", "auto"} and awaits `finished(success)`: success grants the find
## (DiscoveryView), failure / Esc grants nothing and the spot can be tried again any time.
## The base builds the shared chrome (kicker, title, subtitle, instruction, play area, status line, hint plate,
## buttons, key hints), routes input (UIRoot modal stack, or stand-alone via _input), counts failures and shows
## a hint after HINT_AFTER of them (never punishing: no limits, no penalties), holds the solved state for
## SOLVED_HOLD seconds (any confirm key continues at once) and resolves auto mode after AUTO_DELAY seconds.
## Subclasses override: _build_play(area), _reset_game(), _game_input(event) -> bool, _controls() -> Array,
## _hint_text(level) -> String, _tick(delta) and the async demo_solve() (synthetic key events only).
## All timers advance in _process(delta), so tests can drive time by calling _process directly.

signal finished(success: bool)

const DIR := "res://assets/ui/minigames/"
const SOLVED_HOLD := 2.4
const AUTO_DELAY := 0.2
const HINT_AFTER := 2
const PANEL_SIZE := Vector2(1800, 1036)

var ctx: Dictionary = {}
var explore_id := ""
var fails := 0
var solved := false
var hint_level := 0
var ended := false
var success_result := false
## Subclasses without a "start over" (the radio) clear this in _build_play.
var has_restart := true
var _hold_left := -1.0
var _auto_left := -1.0
var _solved_input_guard := 0.0
## A refusal stays readable this long before the idle status (status_auto) may replace it.
var _status_hold := 0.0
const STATUS_HOLD := 3.5

var play: Control
var _panel: PanelContainer
var _content: VBoxContainer
var _kicker: Label
var _title: Label
var _subtitle: Label
var _instr: Label
var _status: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _buttons: HBoxContainer
var _controls_box: VBoxContainer
var _controls_sig := ""


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	closes_on_cancel = true
	add_to_group("minigame")
	var hosted := get_parent() != null and get_parent().has_method("push_modal")
	if not hosted:                 # stand-alone (tests, harness): bring the UI theme along
		theme = Kit.theme(Kit.high_contrast())
	add_child(Kit.dimmer(0.8))
	_panel = Kit.panel()
	_panel.set_anchors_preset(Control.PRESET_CENTER)
	_panel.offset_left = -PANEL_SIZE.x / 2
	_panel.offset_right = PANEL_SIZE.x / 2
	_panel.offset_top = -PANEL_SIZE.y / 2
	_panel.offset_bottom = PANEL_SIZE.y / 2
	add_child(_panel)
	_content = Kit.vbox(8)
	_panel.add_child(_content)
	var head := Kit.hbox(24)
	_content.add_child(head)
	var titles := Kit.vbox(2)
	titles.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(titles)
	_kicker = Kit.label("", "KickerLabel")
	titles.add_child(_kicker)
	_title = Kit.label("", "HeadingLabel")
	titles.add_child(_title)
	_subtitle = Kit.wrap_label("", "DimLabel")
	Kit.scalable(_subtitle, 25)
	titles.add_child(_subtitle)
	_content.add_child(Kit.rule(Kit.C_COPPER, 3))
	_instr = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_instr, 27)
	_content.add_child(_instr)
	play = Control.new()
	play.mouse_filter = Control.MOUSE_FILTER_PASS
	play.size_flags_vertical = Control.SIZE_EXPAND_FILL
	play.clip_contents = false
	_content.add_child(play)
	_status = Kit.wrap_label("", "BodyLabel")
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status.custom_minimum_size.y = 38
	Kit.scalable(_status, 27)
	_content.add_child(_status)
	_hint_box = Kit.panel("PlatePanel")
	var hh := Kit.hbox(16)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hh.add_child(hic)
	_hint_label = Kit.wrap_label("", "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 25)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	_content.add_child(_hint_box)
	_buttons = Kit.hbox(18)
	_buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	_content.add_child(_buttons)
	_controls_box = Kit.vbox(0)
	_content.add_child(_controls_box)
	_build_play(play)
	if has_restart:
		_add_button(Kit.t("mg.common.restart"), restart, 250)
	_add_button(Kit.t("mg.common.giveup"), give_up, 250)
	_reset_game()
	_refresh_controls()


## Sets the header texts (Loc keys).
func set_texts(kicker_key: String, title_key: String, subtitle_key: String, instruction_key: String) -> void:
	_kicker.text = Kit.t(kicker_key).to_upper()
	_title.text = Kit.t(title_key)
	_subtitle.text = Kit.t(subtitle_key)
	_instr.text = Kit.t(instruction_key)


## Mouse-only button (keyboard and pad use the keys shown in the hint row).
func _add_button(text: String, cb: Callable, min_w := 230, front := false) -> Button:
	var b := Kit.button(text, "", min_w)
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(func():
		if not ended:
			cb.call())
	_buttons.add_child(b)
	if front:
		_buttons.move_child(b, 0)
	return b


func _refresh_controls() -> void:
	var pairs: Array = _controls()
	pairs.append([Kit.action_key_text("cancel"), Kit.t("mg.common.ctrl.giveup")])
	var sig := str(pairs)
	if sig == _controls_sig or _controls_box == null:
		return
	_controls_sig = sig
	for c in _controls_box.get_children():
		c.queue_free()
	_controls_box.add_child(Kit.controls_row(pairs))


# ================================================================ lifecycle (Game contract §12.8)
func open(context: Dictionary = {}) -> void:
	ctx = context
	explore_id = str(ctx.get("explore_id", ""))
	if ui_root == null and get_parent() != null and get_parent().has_method("push_modal"):
		ui_root = get_parent()
	ended = false
	open_modal()
	if bool(ctx.get("auto", false)):
		_auto_left = AUTO_DELAY


func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	_reset_game()
	set_status("")


## Mouse "Aufgeben": after a solve it only closes early (the find is kept).
func give_up() -> void:
	_finish(solved)


func handle_cancel() -> bool:
	if ended:
		return true
	if solved:
		_finish(true)
		return true
	if _cancel_step():
		return true
	Kit.ui_sound("back")
	_finish(false)
	return true


## Mark the puzzle solved: status text, sound, then finished(true) after SOLVED_HOLD (or the next confirm).
func mark_solved(text: String) -> void:
	if solved:
		return
	solved = true
	_hold_left = SOLVED_HOLD
	_solved_input_guard = 0.35
	set_status(text)
	_hint_box.visible = false
	_on_solved()


func register_fail(text: String) -> void:
	fails += 1
	Kit.ui_sound("fail")
	set_status(text)
	_status_hold = STATUS_HOLD
	if fails >= HINT_AFTER:
		show_hint(fails - HINT_AFTER + 1)


func show_hint(level: int) -> void:
	var t := _hint_text(level)
	if t == "":
		return
	hint_level = level
	_hint_label.text = t
	if not _hint_box.visible:
		_hint_box.visible = true
		Kit.appear(_hint_box, 0.2)


func set_status(text: String) -> void:
	if _status != null:
		_status.text = text


## Idle/state status: does not overwrite a fresh refusal.
func status_auto(text: String) -> void:
	if _status_hold <= 0.0:
		set_status(text)


func clear_status_hold() -> void:
	_status_hold = 0.0


func _finish(success: bool) -> void:
	if ended:
		return
	ended = true
	success_result = success
	_on_end()
	close()
	finished.emit(success)


func _process(delta: float) -> void:
	if ended:
		return
	if _auto_left >= 0.0:
		_auto_left -= delta
		if _auto_left < 0.0:
			_finish(true)
			return
	if _solved_input_guard > 0.0:
		_solved_input_guard -= delta
	_status_hold = maxf(0.0, _status_hold - delta)
	if solved:
		_hold_left -= delta
		if _hold_left <= 0.0:
			_finish(true)
			return
	_tick(delta)
	_refresh_controls()


# ================================================================ input
func modal_input(event: InputEvent) -> bool:
	if ended:
		return not (event is InputEventMouse)
	if event is InputEventMouse:
		return false
	if solved:
		if _solved_input_guard <= 0.0 and (_is(event, ["ui_accept", "interact", "cancel", "ui_cancel"])):
			_finish(true)
		return event is InputEventKey or event is InputEventJoypadButton
	if _auto_left >= 0.0:
		return true
	return _game_input(event)


## Stand-alone use (tests, harness without UIRoot): route input like UIRoot would.
func _input(event: InputEvent) -> void:
	if ui_root != null or not is_open:
		return
	if modal_input(event):
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("cancel") or event.is_action_pressed("ui_cancel"):
		if handle_cancel():
			get_viewport().set_input_as_handled()


## Pressed (not echo unless allow_echo) for any of the actions.
static func _is(event: InputEvent, actions: Array, allow_echo := false) -> bool:
	for a in actions:
		if InputMap.has_action(a) and event.is_action_pressed(a, allow_echo):
			return true
	return false


## Physical keycode of a pressed key event (0 otherwise; echo ignored unless allowed).
static func _key(event: InputEvent, allow_echo := false) -> int:
	if event is InputEventKey and event.pressed and (allow_echo or not event.echo):
		var k := event as InputEventKey
		return int(k.physical_keycode) if k.physical_keycode != 0 else int(k.keycode)
	return 0


static func _pad(event: InputEvent) -> int:
	if event is InputEventJoypadButton and event.pressed:
		return int((event as InputEventJoypadButton).button_index)
	return -1


# ================================================================ sound helpers
func _sfx(id: String, volume_db := 0.0) -> void:
	var a := Kit.svc("Audio")
	if a != null and a.has_method("sfx"):
		a.sfx(id, volume_db, 0.03)


## Looping stream player on the SFX bus (paused-tree safe); volume set by the game each frame.
func _loop_player(path: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.process_mode = Node.PROCESS_MODE_ALWAYS
	if AudioServer.get_bus_index("SFX") >= 0:
		p.bus = "SFX"
	if ResourceLoader.exists(path):
		p.stream = load(path)
	p.volume_db = -80.0
	add_child(p)
	return p


# ================================================================ synthetic input (demo_solve)
func _tap(k: int) -> void:
	_key_event(k, true)
	await _frames(2)
	_key_event(k, false)
	await _frames(2)


func _key_event(k: int, down: bool) -> void:
	var ev := InputEventKey.new()
	ev.set("keycode", k)
	ev.set("physical_keycode", k)
	ev.pressed = down
	Input.parse_input_event(ev)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _until(cond: Callable, timeout: float) -> bool:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int(timeout * 1000.0):
		if ended or cond.call():
			return true
		await get_tree().process_frame
	return bool(cond.call())


# ================================================================ overridables
func _build_play(_area: Control) -> void:
	pass


func _reset_game() -> void:
	pass


func _game_input(_event: InputEvent) -> bool:
	return false


## Esc first undoes a half-made action (e.g. a picked-up chess piece); return true when it did.
func _cancel_step() -> bool:
	return false


func _controls() -> Array:
	return []


func _hint_text(_level: int) -> String:
	return ""


func _tick(_delta: float) -> void:
	pass


func _on_solved() -> void:
	pass


func _on_end() -> void:
	pass


## Solves the puzzle through synthetic key events only (scripts/core/inputplay.gd calls it once).
func demo_solve() -> void:
	await _frames(1)
