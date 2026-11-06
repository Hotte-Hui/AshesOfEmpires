extends "res://scripts/ui/ui_modal.gd"
## Pause menu: Fortsetzen, Tagebuch, Erinnerungen, Speichern, Laden, Einstellungen, Hauptmenü, Beenden.
## Signals for Game: main_menu_requested, quit_requested (plus load_requested/loaded relayed by SaveLoadMenu).
## Every entry works stand-alone too (fallbacks when nothing is connected) — no dead buttons.
## Under the location it shows the overall exploration progress (Explore, §12): finds and real-history cards.
## Memories (§12.10): „Erinnerungen“ opens the MemoryView; inside a memory the entry becomes „In die Gegenwart
## zurückkehren“ (Game.return_from_memory(), or `memory_return_requested` when connected) and the header names
## the memory; „Hauptmenü“ warns that finds of the visit are only kept by returning first.

signal main_menu_requested
signal quit_requested
signal resumed
signal memory_return_requested

var _buttons: Dictionary = {}
var _who: Label
var _where: Label
var _chapter: Label
var _explore_box: VBoxContainer
var _explore_label: Label
var _history_label: Label
## The menu column. Eight entries (with „Erinnerungen“, §12.10): the panel keeps 48 px to the screen edges and the
## entries sit without extra gaps (each MenuEntry already carries its own padding) — so the whole column, its
## frame and the Esc hint stay on a 1080-px screen.
var _panel: PanelContainer
const EDGE := 48


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.55))
	var p := Kit.panel()
	p.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	p.offset_left = 72
	p.offset_right = 672
	p.offset_top = EDGE
	p.offset_bottom = -EDGE
	add_child(p)
	_panel = p
	var v := Kit.vbox(8)
	p.add_child(v)
	v.add_child(Kit.label(Kit.t("ui.pause.title").to_upper().replace("ß", "SS"), "HeadingLabel", 56))
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
	plate.offset_bottom = -EDGE
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
		["memories", "ui.memories.pause.open", _memories],
		["save", "ui.save", _save],
		["load", "ui.load", _load],
		["settings", "ui.pause.settings", _settings],
		["menu", "ui.pause.main_menu", _main_menu],
		["quit", "ui.pause.quit", _quit],
	]
	var col := Kit.vbox(0)
	v.add_child(col)
	for e in entries:
		var b := Kit.button(Kit.t(e[1]), "MenuEntry")
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.pressed.connect(e[2])
		b.mouse_entered.connect(b.grab_focus)
		b.focus_entered.connect(Kit.ui_sound.bind("move"))
		col.add_child(b)
		_buttons[e[0]] = b
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(spacer)
	v.add_child(Kit.controls_row([[Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.resume")]], BoxContainer.ALIGNMENT_BEGIN))


func open() -> void:
	var st := Kit.svc("Story")
	var who = st.get("active_character") if st != null else null
	_who.text = Kit.t("ui.pause.playing_as", {"name": Kit.char_name(str(who))}).to_upper().replace("ß", "SS") if who != null and str(who) not in ["", "none"] else ""
	var scene = st.get("current_scene") if st != null else null
	var q := Kit.quest_for_scene(str(scene)) if scene != null else {}
	_chapter.text = Kit.t(str(q["title_key"])) if q.has("title_key") else ""
	var sc := Kit.scene_def(str(scene)) if scene != null else {}
	_where.text = Kit.t(str(sc["title_key"])) if sc.has("title_key") else ""
	var can_save := Kit.has_svc("Saves", "save") or Kit.has_svc("Saves", "save_slot")
	(_buttons["save"] as Button).disabled = not can_save
	(_buttons["save"] as Button).tooltip_text = "" if can_save else Kit.t("ui.saveload.unavailable")
	(_buttons["load"] as Button).disabled = not Kit.has_svc("Saves", "list_slots")
	_refresh_memory()
	_refresh_explore()
	open_modal()


## §12.10: inside a memory the header names it and the entry leads back to the present (or to the main menu).
func _refresh_memory() -> void:
	var info = Kit.call_svc("Game", "memory_info", [], {})
	var inside: bool = info is Dictionary and not (info as Dictionary).is_empty()
	var b := _buttons["memories"] as Button
	b.visible = inside or Kit.has_svc("Game", "memory_scenes")
	if not inside:
		b.text = Kit.t("ui.memories.pause.open")
		return
	b.text = Kit.t("ui.memories.pause.return_menu" if bool(info.get("from_menu", false)) else "ui.memories.pause.return")
	var who := str(info.get("who", ""))
	_who.text = Kit.t("ui.memories.pause.kicker", {"name": Kit.char_name(who)}).to_upper().replace("ß", "SS") if who != "" else \
		Kit.t("ui.memories.badge").to_upper().replace("ß", "SS")
	_chapter.text = str(info.get("chapter", ""))
	var parts: Array = []
	for k in ["place", "date"]:
		if str(info.get(k, "")) != "":
			parts.append(str(info[k]))
	_where.text = "  ·  ".join(parts)


func is_in_memory() -> bool:
	var info = Kit.call_svc("Game", "memory_info", [], {})
	return info is Dictionary and not (info as Dictionary).is_empty()


func _memories() -> void:
	if is_in_memory():
		Kit.ui_sound("confirm")
		close()
		if get_signal_connection_list("memory_return_requested").is_empty():
			var g := Kit.svc("Game")
			if g != null and g.has_method("return_from_memory"):
				g.return_from_memory()
		else:
			memory_return_requested.emit()
		return
	if ui_root != null and ui_root.has_method("open_memories"):
		ui_root.open_memories("game")


func _refresh_explore() -> void:
	var pr := Kit.explore_progress()
	_explore_box.get_parent().visible = int(pr["total"]) > 0 or int(pr["cards_total"]) > 0
	_explore_label.text = Kit.t("ui.pause.explore", {"n": pr["found"], "total": pr["total"]}).to_upper().replace("ß", "SS")
	_history_label.text = Kit.t("ui.pause.history", {"n": pr["cards_found"], "total": pr["cards_total"]}).to_upper().replace("ß", "SS")
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
		var info = Kit.call_svc("Game", "memory_info", [], {})
		var key := "ui.pause.confirm_menu"
		if info is Dictionary and not (info as Dictionary).is_empty():
			key = "ui.memories.confirm_menu_from_menu" if bool(info.get("from_menu", false)) else "ui.memories.confirm_menu"
		yes = await ui_root.ask_confirm(Kit.t(key))
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
