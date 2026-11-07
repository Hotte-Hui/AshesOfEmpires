extends "res://scripts/ui/ui_modal.gd"
## Title screen: dithered night backdrop with a faint skyline of both empires (assets/ui/menu/menu_bg.png,
## 640x360 shown x3), slow pixel snow, title + subtitle, and the menu:
## Fortsetzen (only if Saves.has_any()), Neues Spiel, Laden, Erinnerungen (only once a scene was completed —
## Game.memories_any(), global profile, §12.10), Einstellungen, Mitwirkende, Beenden.
## Signals for Game: new_game_requested, continue_requested, quit_requested (fallbacks when unconnected).
## §12.13: the first opening of a real player's launch also brings the studio's demo letter (BootFlow.notice_due();
## never in automated runs) until it was confirmed once.

signal new_game_requested
signal continue_requested
signal quit_requested

const SnowField := preload("res://scripts/ui/snow_field.gd")
const BootFlow := preload("res://scripts/ui/boot_flow.gd")

var _buttons: Dictionary = {}
var _menu: VBoxContainer
var _title_block: VBoxContainer
var _footer: Label


func _ready() -> void:
	pauses_game = false
	closes_on_cancel = false
	var bg := Kit.pixel_image(Kit.tex("res://assets/ui/menu/menu_bg.png"), 3)
	Kit.full_rect(bg)
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(bg)
	var snow := SnowField.new()
	Kit.full_rect(snow)
	add_child(snow)
	_title_block = Kit.vbox(6)
	_title_block.position = Vector2(144, 132)
	add_child(_title_block)
	var kick := Kit.label(Kit.t("ui.menu.kicker").to_upper().replace("ß", "SS"), "KickerLabel", 24)
	_title_block.add_child(kick)
	var title := Kit.label(Kit.t("ui.menu.title"), "TitleLabel")
	_title_block.add_child(title)
	var sub_row := Kit.hbox(18)
	_title_block.add_child(sub_row)
	var r := Kit.rule(Kit.C_COPPER, 3, 84)
	r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sub_row.add_child(r)
	sub_row.add_child(Kit.label(Kit.t("ui.menu.subtitle"), "SubtitleLabel"))
	var orn := Kit.sprite("icons/ornament_diamond.png")
	orn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sub_row.add_child(orn)
	_menu = Kit.vbox(4)
	_menu.position = Vector2(132, 520)
	_menu.custom_minimum_size.x = 520
	add_child(_menu)
	var entries := [
		["continue", "ui.continue", _continue],
		["new", "ui.new_game", _new_game],
		["load", "ui.menu.load", _load],
		["memories", "ui.memories.menu", _memories],
		["settings", "ui.menu.settings", _settings],
		["credits", "ui.menu.credits", _credits],
		["quit", "ui.menu.quit", _quit],
	]
	for e in entries:
		var b := Kit.button(Kit.t(e[1]), "MenuEntry")
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.pressed.connect(e[2])
		b.mouse_entered.connect(b.grab_focus)
		b.focus_entered.connect(Kit.ui_sound.bind("move"))
		_menu.add_child(b)
		_buttons[e[0]] = b
	var version := str(ProjectSettings.get_setting("application/config/version", "0.1.0"))
	_footer = Kit.label(Kit.t("ui.menu.footer", {"version": version}), "ControlHintLabel")
	_footer.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_footer.offset_left = 144
	_footer.offset_right = 1144
	_footer.offset_top = -78
	_footer.offset_bottom = -42
	_footer.grow_vertical = Control.GROW_DIRECTION_BEGIN
	add_child(_footer)


func open() -> void:
	refresh()
	open_modal()


func refresh() -> void:
	var has_save := false
	var r = Kit.call_svc("Saves", "has_any", [], null)
	if r != null:
		has_save = bool(r)
	else:
		var slots = Kit.call_svc("Saves", "list_slots", [], [])
		for s in slots:
			if s is Dictionary and bool(s.get("exists", not bool(s.get("empty", true)))):
				has_save = true
	(_buttons["continue"] as Button).visible = has_save
	(_buttons["load"] as Button).disabled = not Kit.has_svc("Saves", "list_slots")
	(_buttons["memories"] as Button).visible = bool(Kit.call_svc("Game", "memories_any", [], false))
	# seven entries: the column starts higher so the last one keeps clear of the footer line
	var n := 0
	for k in _buttons:
		if (_buttons[k] as Button).visible:
			n += 1
	_menu.position.y = 520.0 - maxf(0.0, float(n - 6)) * 52.0


func _on_open() -> void:
	Kit.appear(_title_block, 0.9 if not Kit.reduced_motion() else 0.3)
	Kit.appear(_menu, 0.6, Vector2(-18, 0))
	if BootFlow.notice_due():
		BootFlow.notice_opened = true
		_open_notice.call_deferred()


## Deferred: the menu is on the stack before the letter covers it (the letter's own deferred focus call runs after
## the menu's, so „Los geht's“ ends up focused).
func _open_notice() -> void:
	if is_open and ui_root != null and ui_root.has_method("open_demo_notice") and ui_root.top_modal() == self:
		ui_root.open_demo_notice(true)


func focus_default() -> void:
	var b: Button = _buttons["continue"] if (_buttons["continue"] as Button).visible else _buttons["new"]
	b.grab_focus()


func _continue() -> void:
	Kit.ui_sound("confirm")
	if get_signal_connection_list("continue_requested").is_empty():
		close()
	continue_requested.emit()


func _new_game() -> void:
	Kit.ui_sound("confirm")
	if get_signal_connection_list("new_game_requested").is_empty():
		close()
	new_game_requested.emit()


func _load() -> void:
	if ui_root != null:
		ui_root.open_saveload("load", false)


## §12.10: memories of every scene completed at least once (return leads back here).
func _memories() -> void:
	if ui_root != null and ui_root.has_method("open_memories"):
		ui_root.open_memories("menu")


func _settings() -> void:
	if ui_root != null:
		ui_root.open_settings()


func _credits() -> void:
	if ui_root != null:
		ui_root.open_credits()


func _quit() -> void:
	if get_signal_connection_list("quit_requested").is_empty():
		get_tree().quit()
	else:
		quit_requested.emit()


func _modal_uncovered() -> void:
	refresh()
	super._modal_uncovered()
