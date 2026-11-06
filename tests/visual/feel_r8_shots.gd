extends Node
## Visual check of the round-8 feel pass (owner feel_r8): ambient walkers, the car-3 thaw, decor loops.
## Boots the real Main scene in capture mode (Game: no autosave, no intro, no focus pause), loads --scene,
## then per shot places the player, moves the camera and waits real seconds (walkers keep walking).
##   godot --path . res://tests/visual/feel_r8_shots.tscn -- --scene=L_C3_Station --char=alexei \
##         --capture=<dir>/boot.png --frames=100000 --fr-out=<dir> \
##         --fr-shots=label:camx:playerx:playery:seconds[:thaw|thawed],...
## Action "thaw" starts the StationThaw sequence (presentation only: Explore is not touched) before waiting;
## "thawed" shows the final state. UI actions (a mock memory list via UIKit.overrides, text scale set in memory
## only -- user://settings.cfg is never written): "memview150" (main-menu MemoryView at 150 % text, one press of
## Down), "membroken" (the same view, choosing a card whose recorded state is broken), "journal_late" (journal
## with late-game tab counters), "dlg=<speaker>;<key>;<expr>" (the DialogueBox speaking that line). Exit code 0 =
## every shot taken.

const MAIN := "res://scenes/main/Main.tscn"
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const SCENES := ["L_A1_Railyard", "L_M1_Archive", "L_M1_Plaza", "L_C3_Station", "L_C3_Hall"]


class MockMem extends RefCounted:
	var raw: Dictionary = {}

	func snapshot_raw(id: String) -> String:
		return str(raw.get(id, "{}"))


class MockGame extends Node:
	var memories := MockMem.new()

	func memory_scenes(_context := "game") -> Array:
		var out: Array = []
		for i in SCENES.size():
			var id: String = SCENES[i]
			out.append({"id": id, "unlocked": true, "current": false, "place": UIKit.t("ui.memories.place." + id),
				"date": UIKit.t("ui.memories.date." + id) if UIKit.has_key("ui.memories.date." + id) else "",
				"chapter": "Kapitel %d" % (1 if i == 0 else (2 if i < 3 else 3)),
				"who": "alexei" if id in ["L_A1_Railyard", "L_C3_Station"] else "konrad",
				"thumb": "res://assets/ui/memories/%s.png" % id, "found": 4 + i * 3, "total": 25})
		return out

	func memory_films(_context := "game") -> Array:
		return []

	func can_travel(_from_menu := false) -> bool:
		return true

	func travel_to_memory(_id: String, _from_menu := false) -> bool:
		return false

var out_dir := ""
var shots_spec: Array = []
var shots := 0
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--fr-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--fr-shots="):
			shots_spec = Array(a.substr(11).split(",", false))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://feel_r8_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 60.0
	for s in shots_spec:
		var p: PackedStringArray = str(s).split(":")
		limit += 6.0 + (float(p[4]) if p.size() > 4 else 1.0)
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("FR_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	if get_node_or_null("/root/Game") == null:
		print("FR_PROBLEM the Game autoload is missing (a project script failed to parse?)")
		get_tree().quit(2)
		return
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join(label + ".png")
	img.save_png(path)
	shots += 1
	print("FR_SHOT ", path)


func _thaw_actor() -> Node:
	var pf: Node = Game.level.get_node_or_null("Playfield") if Game.level else null
	if pf == null:
		return null
	for c in pf.get_children():
		if c.has_method("play_thaw"):
			return c
	return null


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	for i in 20:
		await get_tree().process_frame
	for spec in shots_spec:
		var p: PackedStringArray = str(spec).split(":")
		if p.size() < 5:
			problems.append("bad shot spec " + str(spec))
			continue
		var hud = Game.ui.get("hud") if Game.ui else null
		if hud and hud.has_method("hide_hud"):
			hud.hide_hud()
		Game.player.global_position = Vector2(float(p[2]), float(p[3]))
		Game.camera.cinematic = true
		Game.camera.set_top_left(Vector2(float(p[1]), 0.0))
		if p.size() > 5 and p[5].begins_with("dlg="):
			# dlg=<speaker>;<locale key>;<expression>: the real DialogueBox with that speaker's portrait
			var d: PackedStringArray = p[5].substr(4).split(";")
			Game.ui.dialogue.show_line(d[0], Loc.t(d[1]), d[2] if d.size() > 2 else "neutral")
		elif p.size() > 5 and p[5] in ["memview150", "membroken", "journal_late"]:
			await _ui_action(p[5])
		elif p.size() > 5:
			var th := _thaw_actor()
			if th == null:
				problems.append("no StationThaw actor in this level")
			elif p[5] == "thaw":
				th.play_thaw()
			elif p[5] == "thawed":
				th.set_thawed()
		var until := Time.get_ticks_msec() + int(float(p[4]) * 1000.0)
		while Time.get_ticks_msec() < until:
			await get_tree().process_frame
		await _shot(p[0])
	_finish()


func _ui_action(kind: String) -> void:
	var st := get_node_or_null("/root/Settings")
	if kind == "journal_late":
		Game.ui.open_journal("tasks")
		var j: Control = Game.ui.journal
		j._tab_counts = {"objectives": 3, "tasks": 6, "evidence": 21, "people": 24, "decisions": 6,
			"discoveries": 131, "history": 23}
		j._fit_tabs()
		return
	if st != null:
		st.values["text_scale"] = 1.5            # this run only, never saved
		UIKit.refresh_text_scale()
	var mock := MockGame.new()
	add_child(mock)
	if kind == "membroken":
		mock.memories.raw = {"L_C3_Hall": "{ kaputt"}
	UIKit.overrides["Game"] = mock
	Game.ui.open_memories("menu")
	for i in 12:
		await get_tree().process_frame
	var down := InputEventAction.new()
	down.action = "ui_down"
	down.pressed = true
	Input.parse_input_event(down)
	for i in 4:
		await get_tree().process_frame
	var up := InputEventAction.new()
	up.action = "ui_down"
	up.pressed = false
	Input.parse_input_event(up)
	if kind == "membroken":
		var v: Control = Game.ui.memories
		v.select("L_C3_Hall")
		v.activate("L_C3_Hall")


func _finish() -> void:
	for pr in problems:
		print("FR_PROBLEM ", pr)
	print("FR_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
