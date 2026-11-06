extends Node
## Visual harness for the side tasks (TECHNICAL_ARCHITECTURE §12.9, owner: tasks). Boots the real Main scene into a
## level in capture mode (no autosave, no intro pan), drives the Story through the public API so the level is the
## current story scene (and story-gated task chats are open), then plays one side task step by step through the
## normal Game.interact path: for every step a shot of the prompt (with its marker), the first line of the chat /
## the find page, and the moment after (toasts). Finally the journal opens on "Aufgaben". PNGs only go to
## --px-out=<absolute dir>; save slots are never touched (capture mode).
##   godot --path . res://tests/visual/tasks_shots.tscn -- --scene=L_A1_Railyard --capture=<dir>/boot.png \
##         --frames=100000 --px-out=<dir> --px-task=karsk.task.train [--px-mark=1] [--px-extra=berlin.task.mittens]
## --px-stop=<n> plays only the first n steps (the journal then shows the task open with its hint).
## --px-mark=1 draws the HUD's "task" prompt mark the way the proposed hud.gd patch does (integration notes), so
## the look can be judged before the patch lands. --px-extra: tasks finished silently before (journal "done" rows).

const MAIN := "res://scenes/main/Main.tscn"
const KIT := preload("res://tests/support/test_kit.gd")
const MARK := "res://assets/ui/tasks/mark_task.png"

var out_dir := ""
var task_id := ""
var extra: Array = []
var draw_mark := false
var stop_after := -1                 # --px-stop=<n>: play only n steps (journal shows the task open)
var problems: Array = []
var _shots := 0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		var kv := a.substr(2).split("=", true, 1) if a.begins_with("--") else PackedStringArray()
		if kv.size() < 2:
			continue
		match kv[0]:
			"px-out":
				out_dir = kv[1]
			"px-task":
				task_id = kv[1]
			"px-mark":
				draw_mark = kv[1] != "0"
			"px-extra":
				extra = Array(kv[1].split(",", false))
			"px-stop":
				stop_after = int(kv[1])
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://tasks_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(label: String) -> void:
	if draw_mark:
		_apply_mark()
	await RenderingServer.frame_post_draw
	_shots += 1
	var path := out_dir.path_join("%02d_%s.png" % [_shots, label])
	get_viewport().get_texture().get_image().save_png(path)
	print("PX_SHOT ", path)


## The proposed hud.gd patch: prompt state "task" shows mark_task.png (no dimming).
func _apply_mark() -> void:
	var hud = Game.ui.get("hud") if Game.ui else null
	var f = Game.get("_focus")
	if hud == null or f == null or not is_instance_valid(f) or not f.has_method("prompt_state"):
		return
	if str(f.prompt_state()) == "task" and ResourceLoader.exists(MARK):
		hud._prompt_mark.texture = load(MARK)
		hud._prompt_mark.visible = true


func _drive_story(level_id: String) -> void:
	var kit := KIT.new()
	var g: Node = Story
	var stages := {"L_A1_Railyard": [], "L_M1_Archive": ["a1"], "L_M1_Plaza": ["a1"], "L_C3_Station": ["a1", "m1"],
		"L_C3_Hall": ["a1", "m1", "c3a"]}
	for st in stages.get(level_id, []):
		match st:
			"a1":
				kit.play_a1(g)
			"m1":
				kit.play_m1(g)
			"c3a":
				kit.play_c3a(g)
		for s in g.pending_cinematics():
			kit.step(g.consume_cinematic(s, true), "cinematic " + s)
	if level_id == "L_C3_Station":
		kit.play_dialogue(g, "c3a_talk_conductor")      # opens the conductor's task chat (gated after his story talk)
	if level_id == "L_M1_Plaza":
		Game.side_level = true                          # an optional side level: no switch back to the story scene
	problems.append_array(kit.failures)


func _host(step_id: String) -> Node:
	for it in get_tree().get_nodes_in_group("interactables"):
		if not it.is_inside_tree():
			continue
		var chain = it.get("explore_chain")
		if str(it.get("explore_id")) == step_id or (chain != null and step_id in chain):
			return it
	return null


func _place(it: Node) -> void:
	var p = Game.player
	p.position = it.global_position + Vector2(-14, 2)
	if str(p.mode) == "side":
		p.position.y = p.floor_y
	p.face(1.0)
	Game.camera.snap_now()


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	var lid := str(Game.level.level_id)
	_drive_story(lid)
	Explore.reset()
	for t in extra:                                   # finished earlier (silently): "done" rows in the journal
		var was: bool = Explore.notify_tasks
		Explore.notify_tasks = false
		for sid in Explore.task_steps(str(t)):
			for r in Explore.requires_of(str(sid)):
				Explore.find(str(r))
			Explore.find(str(sid))
		Explore.notify_tasks = was
	await _frames(40)
	var steps: Array = Explore.task_steps(task_id)
	if steps.is_empty():
		problems.append("unknown task " + task_id)
		_finish()
		return
	for i in steps.size():
		if stop_after >= 0 and i >= stop_after:
			break
		var sid := str(steps[i])
		var it := _host(sid)
		if it == null:
			problems.append("no hotspot hosts " + sid)
			break
		var tries := 0
		while str(it.explore_id) != sid and tries < 8:   # a chain shows its own entry first (e.g. the greeting)
			tries += 1
			var cur := str(it.explore_id)
			if Explore.is_found(cur) or not it.is_active():
				break
			_place(it)
			await _frames(20)
			await _interact(it, "pre_" + cur.get_slice(".", cur.get_slice_count(".") - 1), false)
		if str(it.explore_id) != sid or not it.is_active():
			problems.append("step %s not current/active on %s (current %s)" % [sid, it.name, it.explore_id])
			break
		_place(it)
		await _frames(45)
		var tag := "step%d_%s" % [i + 1, sid.get_slice(".", sid.get_slice_count(".") - 1)]
		await _shot(tag + "_prompt")
		await _interact(it, tag, true)
		await _frames(50)
		await _shot(tag + "_after")
		if not Explore.is_found(sid):
			problems.append("step %s not recorded" % sid)
	var st: Dictionary = Explore.task_state(task_id)
	if str(st["state"]) != "done" and stop_after < 0:
		problems.append("task %s ends %s" % [task_id, st])
	await _frames(140)
	Game.ui.open_journal("tasks")
	await _frames(40)
	await _shot("journal_tasks")
	Game.ui.journal.close()
	_finish()


## Game.interact without a player: shots of the first chat line / the find page, then pages through.
func _interact(it: Node, tag: String, shoot: bool) -> void:
	var dlg = Game.ui.get("dialogue")
	var view = Game.ui.get("discovery")
	Game.interact(it)
	var lines := 0
	var t := 0
	while (Game.busy or t < 3) and t < 3000:
		t += 1
		await get_tree().process_frame
		if view != null and view.is_open:
			await _frames(25)
			if shoot:
				await _shot(tag + "_page")
			while view.is_open:
				view.next()
				await _frames(12)
			continue
		if dlg != null and dlg.is_open and dlg.has_signal("advanced"):
			lines += 1
			await _frames(12)
			if shoot and lines == 2:
				dlg.skip_typing()                        # the whole line, as after a first key press
				await _frames(20)
				await _shot(tag + "_line")
			dlg.advanced.emit()
			await _frames(4)


func _finish() -> void:
	for pr in problems:
		printerr("PX_PROBLEM ", pr)
	print("PX_DONE problems=", problems.size())
	get_tree().quit(1 if not problems.is_empty() else 0)
