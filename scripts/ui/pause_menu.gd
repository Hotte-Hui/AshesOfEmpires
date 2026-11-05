extends "res://scripts/ui/ui_modal.gd"
## Pause menu: Fortsetzen, Tagebuch, Speichern, Laden, Einstellungen, Hauptmenü, Beenden.
## Signals for Game: main_menu_requested, quit_requested (plus load_requested/loaded relayed by SaveLoadMenu).
## Every entry works stand-alone too (fallbacks when nothing is connected) — no dead buttons.
## Under the location it shows the overall exploration progress (Explore, §12): finds and real-history cards.

signal main_menu_requested
signal quit_requested
signal resumed

var _buttons: Dictionary = {}
var _who: Label
var _where: Label
var _chapter: Label
var _explore_box: VBoxContainer
var _explore_label: Label
var _history_label: Label


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.55))
	var p := Kit.panel()
	p.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	p.offset_left = 72
	p.offset_right = 672
	p.offset_top = 72
	p.offset_bottom = -72
	add_child(p)
	var v := Kit.vbox(8)
	p.add_child(v)
	v.add_child(Kit.label(Kit.t("ui.pause.title").to_upper(), "HeadingLabel", 56))
	_who = Kit.label("", "KickerLabel")
	v.add_child(_who)
	_chapter = Kit.label("", "BodyLabel", 30)
	_chapter.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	v.add_child(_chapter)
	_where = Kit.label("", "DimLabel")
	v.add_child(_where)
	# exploration progress: a small plate at the bottom right, outside the menu column (keeps its layout)
	var plate := Kit.panel("PlatePanel")
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	plate.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	plate.grow_vertical = Control.GROW_DIRECTION_BEGIN
	plate.offset_right = -72
	plate.offset_bottom = -72
	add_child(plate)
	_explore_box = Kit.vbox(6)
	plate.add_child(_explore_box)
	for k in ["discovery", "history"]:
		var row := Kit.hbox(12)
		var ic := Kit.ex_sprite("icons/icon_%s.png" % k)
		ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(ic)
		var l := Kit.label("", "HintLabel")
		l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(l)
		_explore_box.add_child(row)
		if k == "discovery":
			_explore_label = l
		else:
			_history_label = l
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 10))
	v.add_child(HSeparator.new())
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 6))
	var entries := [
		["resume", "ui.pause.resume", _resume],
		["journal", "ui.journal", _journal],
		["save", "ui.save", _save],
		["load", "ui.load", _load],
		["settings", "ui.pause.settings", _settings],
		["menu", "ui.pause.main_menu", _main_menu],
		["quit", "ui.pause.quit", _quit],
	]
	for e in entries:
		var b := Kit.button(Kit.t(e[1]), "MenuEntry")
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.pressed.connect(e[2])
		b.mouse_entered.connect(b.grab_focus)
		b.focus_entered.connect(Kit.ui_sound.bind("move"))
		v.add_child(b)
		_buttons[e[0]] = b
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(spacer)
	v.add_child(Kit.controls_row([[Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.resume")]], BoxContainer.ALIGNMENT_BEGIN))


func open() -> void:
	var st := Kit.svc("Story")
	var who = st.get("active_character") if st != null else null
	_who.text = Kit.t("ui.pause.playing_as", {"name": Kit.char_name(str(who))}).to_upper() if who != null and str(who) not in ["", "none"] else ""
	var scene = st.get("current_scene") if st != null else null
	var q := Kit.quest_for_scene(str(scene)) if scene != null else {}
	_chapter.text = Kit.t(str(q["title_key"])) if q.has("title_key") else ""
	var sc := Kit.scene_def(str(scene)) if scene != null else {}
	_where.text = Kit.t(str(sc["title_key"])) if sc.has("title_key") else ""
	var can_save := Kit.has_svc("Saves", "save") or Kit.has_svc("Saves", "save_slot")
	(_buttons["save"] as Button).disabled = not can_save
	(_buttons["save"] as Button).tooltip_text = "" if can_save else Kit.t("ui.saveload.unavailable")
	(_buttons["load"] as Button).disabled = not Kit.has_svc("Saves", "list_slots")
	_refresh_explore()
	open_modal()


func _refresh_explore() -> void:
	var pr := Kit.explore_progress()
	_explore_box.get_parent().visible = int(pr["total"]) > 0 or int(pr["cards_total"]) > 0
	_explore_label.text = Kit.t("ui.pause.explore", {"n": pr["found"], "total": pr["total"]}).to_upper()
	_history_label.text = Kit.t("ui.pause.history", {"n": pr["cards_found"], "total": pr["cards_total"]}).to_upper()
	_history_label.get_parent().visible = int(pr["cards_total"]) > 0


func _resume() -> void:
	close()
	resumed.emit()


func _journal() -> void:
	if ui_root != null:
		ui_root.journal.open()


func _save() -> void:
	if ui_root != null:
		ui_root.open_saveload("save", true)


func _load() -> void:
	if ui_root != null:
		ui_root.open_saveload("load", true)


func _settings() -> void:
	if ui_root != null:
		ui_root.open_settings()


func _main_menu() -> void:
	var yes := true
	if ui_root != null:
		yes = await ui_root.ask_confirm(Kit.t("ui.pause.confirm_menu"))
	if not yes:
		return
	if get_signal_connection_list("main_menu_requested").is_empty():
		if ui_root != null:
			ui_root.show_main_menu()
	else:
		close()
		main_menu_requested.emit()


func _quit() -> void:
	var yes := true
	if ui_root != null:
		yes = await ui_root.ask_confirm(Kit.t("ui.pause.confirm_quit"))
	if not yes:
		return
	if get_signal_connection_list("quit_requested").is_empty():
		get_tree().quit()
	else:
		quit_requested.emit()


func modal_input(event: InputEvent) -> bool:
	if event.is_action_pressed("pause") and not event.is_action_pressed("cancel"):
		_resume()
		return true
	return false


func handle_cancel() -> bool:
	_resume()
	return true


func focus_default() -> void:
	(_buttons["resume"] as Button).grab_focus()
