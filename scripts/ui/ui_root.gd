extends Control
## UIRoot (scenes/ui/UIRoot.tscn) — aggregates every HD UI scene (TECHNICAL_ARCHITECTURE §6) and is
## instanced by Main under the `UI` CanvasLayer. Responsibilities:
## * exposes the panels as properties: hud, dialogue, inspect, signal_puzzle, blueprint_puzzle, journal,
##   discovery (DiscoveryView, §12 exploration finds + real-history cards), pause_menu, main_menu,
##   settings_menu, saveload_menu, credits, confirm, subtitles, fade
## * modal stack: push_modal()/pop_modal(); the top modal gets input first (in _input, before the GUI);
##   pausing modals set get_tree().paused (all UI runs with PROCESS_MODE_ALWAYS)
## * applies theme.tres / theme_hc.tres and live text scaling from Settings
## * keeps the HUD in sync with Story signals (objective tracker, journal toasts), tells the HUD which
##   interactable is focused (Game.focus_changed -> found / not-yet-found prompt marker) and toasts real-history
##   cards that were unlocked without being shown (e.g. by a chat; never celebratory, kind "history")
## World-level shortcuts (pause, journal) are opened by Game via open_pause()/open_journal(); UIRoot only
## routes input while a modal is open, so it never fights the scene director.

const Kit := preload("res://scripts/ui/ui_kit.gd")

signal modal_changed(top: Control)

@onready var hud: Control = $HUD
@onready var dialogue: Control = $DialogueBox
@onready var inspect: Control = $InspectView
@onready var signal_puzzle: Control = $SignalPuzzle
@onready var blueprint_puzzle: Control = $BlueprintPuzzle
@onready var journal: Control = $Journal
@onready var discovery: Control = $DiscoveryView
@onready var pause_menu: Control = $PauseMenu
@onready var main_menu: Control = $MainMenu
@onready var settings_menu: Control = $SettingsMenu
@onready var saveload_menu: Control = $SaveLoadMenu
@onready var credits: Control = $Credits
@onready var confirm: Control = $ConfirmDialog
@onready var toast_layer: Control = $ToastLayer
@onready var subtitles: Control = $Subtitles
@onready var fade: Control = $Fade

## true while a cinematic runs (HUD hidden, letterbox); set through set_cinematic().
var cinematic_mode := false
var _stack: Array[Control] = []
var _paused_by_ui := false
var _pending_cards: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(self)
	_apply_theme()
	for c in get_children():
		if c is Control and "ui_root" in c:
			c.set("ui_root", self)
	if hud.has_method("set_toast_layer"):
		hud.set_toast_layer(toast_layer)
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)
	connect_story()
	connect_explore()
	_connect_game.call_deferred()
	modal_changed.connect(hud.on_modal_changed)


## (Re)connects the HUD to the Story signals (call again if the Story service is replaced).
func connect_story() -> void:
	var st := Kit.svc("Story")
	if st == null:
		return
	if st.has_signal("objective_completed") and not st.objective_completed.is_connected(_on_objective_completed):
		st.objective_completed.connect(_on_objective_completed)
	if st.has_signal("scene_changed") and not st.scene_changed.is_connected(_on_scene_changed):
		st.scene_changed.connect(_on_scene_changed)


func _on_scene_changed(_id) -> void:
	hud.refresh()


## (Re)connects to the Explore service (§12): cards unlocked without a DiscoveryView page get a quiet toast.
func connect_explore() -> void:
	var ex := Kit.svc("Explore")
	if ex == null:
		return
	if ex.has_signal("history_unlocked") and not ex.history_unlocked.is_connected(_on_history_unlocked):
		ex.history_unlocked.connect(_on_history_unlocked)


## The HUD marks prompts of found / not-yet-found exploration hotspots; it learns the focused target here.
func _connect_game() -> void:
	var g := Kit.svc("Game")
	if g == null or not g.has_signal("focus_changed") or not hud.has_method("set_prompt_target"):
		return
	if not g.focus_changed.is_connected(hud.set_prompt_target):
		g.focus_changed.connect(hud.set_prompt_target)


func _on_history_unlocked(card_id: String) -> void:
	if _pending_cards.is_empty():
		_flush_history.call_deferred()
	if not (card_id in _pending_cards):
		_pending_cards.append(card_id)


## Runs at the end of the frame: Game opens the DiscoveryView synchronously right after Explore.find(), so a
## card shown there is skipped; anything else (a chat, a script) is announced as a neutral toast.
func _flush_history() -> void:
	var shown: Array = []
	if discovery != null and discovery.get("is_open") == true:
		for p in discovery.get("pages"):
			if str(p.get("type", "")) == "card":
				shown.append(str(p.get("id", "")))
	var ex := Kit.svc("Explore")
	for cid in _pending_cards:
		if cid in shown:
			continue
		var c: Dictionary = ex.card(cid) if ex != null and ex.has_method("card") else {}
		var name := Kit.t(str(c["title_key"])) if c.has("title_key") else str(cid)
		var fmt := "ui.toast.history" if Kit.has_key("ui.toast.history") else "ui.explore.toast.history"
		hud.toast(Kit.t(fmt, {"name": name}), "history")
	_pending_cards.clear()


# ================================================================ modal stack
func push_modal(m: Control) -> void:
	if m == null:
		return
	var prev := top_modal()
	if m in _stack:
		_stack.erase(m)
	elif prev != null and prev != m:
		prev._modal_covered()
	_stack.append(m)
	move_child(m, toast_layer.get_index() - 1 if m.get_index() < toast_layer.get_index() else toast_layer.get_index())
	if not m.is_open:
		m._modal_shown()
	_update_pause()
	modal_changed.emit(m)


func pop_modal(m: Control = null) -> void:
	if m == null:
		m = top_modal()
	if m == null:
		return
	var was_top := m == top_modal()
	_stack.erase(m)
	if m.is_open:
		m._modal_hidden()
	if was_top and top_modal() != null:
		top_modal()._modal_uncovered()
	_update_pause()
	modal_changed.emit(top_modal())


func top_modal() -> Control:
	while not _stack.is_empty() and not is_instance_valid(_stack.back()):
		_stack.pop_back()
	return _stack.back() if not _stack.is_empty() else null


func is_modal_open() -> bool:
	return top_modal() != null


func is_open(panel: Control) -> bool:
	return panel in _stack


## True while the world must not react to player input (any modal incl. dialogue).
func blocks_world_input() -> bool:
	return is_modal_open()


func close_all() -> void:
	while not _stack.is_empty():
		var m: Control = _stack.pop_back()
		if is_instance_valid(m) and m.is_open:
			m._modal_hidden()
	if hud.has_method("hide_prompt"):
		hud.hide_prompt()
	_update_pause()
	modal_changed.emit(null)


func _update_pause() -> void:
	var want := false
	for m in _stack:
		if is_instance_valid(m) and m.pauses_game:
			want = true
	if want and not get_tree().paused:
		get_tree().paused = true
		_paused_by_ui = true
	elif not want and _paused_by_ui:
		get_tree().paused = false
		_paused_by_ui = false


# ================================================================ input routing
func _input(event: InputEvent) -> void:
	_track_device(event)
	var top := top_modal()
	if top == null:
		return
	if top.modal_input(event):
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("cancel") or event.is_action_pressed("ui_cancel"):
		if top.handle_cancel():
			get_viewport().set_input_as_handled()
			return
	if _wasd_navigation(event):
		get_viewport().set_input_as_handled()


func _track_device(event: InputEvent) -> void:
	var pad := Kit.last_input_pad
	if event is InputEventJoypadButton:
		pad = true
	elif event is InputEventJoypadMotion and absf((event as InputEventJoypadMotion).axis_value) > 0.5:
		pad = true
	elif event is InputEventKey or event is InputEventMouseButton:
		pad = false
	if pad != Kit.last_input_pad:
		Kit.last_input_pad = pad
		if hud.has_method("refresh_prompt_key"):
			hud.refresh_prompt_key()


## WASD (move_*) navigates menus like the arrow keys.
func _wasd_navigation(event: InputEvent) -> bool:
	if not (event is InputEventKey) or not event.is_pressed():
		return false
	var map := {"move_up": "ui_up", "move_down": "ui_down", "move_left": "ui_left", "move_right": "ui_right"}
	for a in map:
		if event.is_action_pressed(a, true) and not event.is_action(map[a]):
			var ev := InputEventAction.new()
			ev.action = map[a]
			ev.pressed = true
			Input.parse_input_event(ev)
			return true
	return false


# ================================================================ public API (used by Game)
func show_main_menu() -> void:
	close_all()
	set_cinematic(false)
	if hud.has_method("hide_hud"):
		hud.hide_hud()
	main_menu.open()


func open_pause() -> void:
	if cinematic_mode or is_open(pause_menu):
		return
	pause_menu.open()


func open_journal(tab := "") -> void:
	if cinematic_mode:
		return
	if is_open(journal):
		journal.close()
		return
	journal.open(tab)


## Re-opens an exploration find (and its real-history pages) — e.g. from the journal.
func open_discovery(explore_id: String) -> void:
	discovery.open(explore_id)


func open_settings() -> void:
	settings_menu.open()


func open_saveload(mode := "load", in_game := true) -> void:
	saveload_menu.open(mode, in_game)


func open_credits() -> void:
	credits.open()


func ask_confirm(text: String, yes_text := "", no_text := "", default_yes := false) -> bool:
	return await confirm.ask(text, yes_text, no_text, default_yes)


func set_cinematic(on: bool) -> void:
	cinematic_mode = on
	if on:
		if hud.has_method("hide_hud"):
			hud.hide_hud()
	if fade.has_method("letterbox"):
		fade.letterbox(on)


func show_subtitle(text: String, duration := 0.0, speaker := "") -> void:
	subtitles.show_subtitle(text, duration, speaker)


func toast(text: String, kind := "") -> void:
	hud.toast(text, kind)


# ================================================================ reactions
func _apply_theme() -> void:
	var th := Kit.theme(Kit.high_contrast())
	if th != null:
		theme = th


func _on_setting_changed(key: String, _value) -> void:
	match key:
		"text_scale":
			Kit.refresh_text_scale()
		"high_contrast":
			_apply_theme()
			propagate_call("_on_contrast_changed")
		"subtitles":
			if not bool(Kit.setting("subtitles", true)) and subtitles.has_method("hide_subtitle"):
				subtitles.hide_subtitle()
		"reduced_motion":
			propagate_call("_on_reduced_motion_changed")


func _on_objective_completed(oid: String) -> void:
	hud.refresh()
	var d := Kit.objective_def(str(oid))
	match str(d.get("type", "")):
		"choice":
			hud.toast(Kit.t("ui.toast.decision"), "decision")
		"dialogue":
			var conv := Kit.conversation(str(d.get("dialogue_id", "")))
			var seen := {}
			for n in conv.get("nodes", []):
				var sp := str(n.get("speaker", ""))
				if sp != "" and not (sp in Kit.PROTAGONISTS) and not seen.has(sp):
					seen[sp] = true
					hud.toast(Kit.t("ui.toast.person", {"name": Kit.char_name(sp)}), "person")
