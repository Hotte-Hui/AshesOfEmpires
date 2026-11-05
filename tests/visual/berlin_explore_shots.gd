extends SceneTree
## Windowed capture harness for the Berlin archive exploration content (owner: berlin-explore).
## Boots the real Main scene with the level, completes chapter 1 in the in-memory Story (so the archive is the
## story's current scene and nothing reloads), then walks Konrad to every exploration spot of L_M1_Archive and
## captures the frame with its interaction prompt; finally opens a few finds and chats through Game.interact()
## (the real presentation path) and captures the discovery view / dialogue box.
## Writes NO saves: Main boots with --capture (Game never autosaves in capture mode); --frames keeps Game's own
## capture flow from quitting before this harness is done.
##
## godot --path . --script res://tests/visual/berlin_explore_shots.gd -- --scene=L_M1_Archive --char=konrad
##       --spawn=SP_M1_Arrival --capture=<dir>/_unused.png --frames=999999 --shots=<dir> [--symbols=0|1]
##       [--open=berlin.photo,berlin.porter] [--prompts=0]

const SPOTS := [
	"TalkPorter", "ExpRadio", "ExpClock", "ExpPigeons", "ExpPhoto", "ExpLibShelf1", "ExpLibShelf2", "ExpHeater",
	"ExpCardCatalogue", "TalkLibrarian", "ExpGlobe", "ExpLibShelf3", "ExpReadingTable", "ExpLibShelf4",
	"ExpLibShelf5", "ExpLibHidden", "ExpCoatStand", "ObsBrandtDesk", "ObsWindow", "ExpPosterAufbau", "ExpMouse",
	"ExpPneumaticTube", "ExpNotice", "TalkEmilTea", "ExpMasterPlan"]

var _args := {}
var _out := ""
var _log: Array = []


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			_args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	_out = str(_args.get("shots", "user://berlin_explore_shots"))
	DirAccess.make_dir_recursive_absolute(_out)
	var main: Node = load("res://scenes/main/Main.tscn").instantiate()
	root.add_child(main)
	_run.call_deferred()


func _game() -> Node:
	return root.get_node("Game")


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var path := _out.path_join(name + ".png")
	img.save_png(path)
	print("SHOT ", path)


func _run() -> void:
	var g := _game()
	var guard := 0
	while (g.level == null or g.player == null) and guard < 900:
		guard += 1
		await process_frame
	if g.level == null or g.player == null:
		printerr("HARNESS: level did not load")
		quit(1)
		return
	_finish_chapter_one()
	await _frames(30)
	var lvl: Node = g.level
	var pl: Node = g.player
	var nodes := {}
	for c in lvl.playfield.get_children():
		nodes[c.name] = c
	print("LEVEL ", lvl.level_id, " story scene ", root.get_node("Story").current_scene, " player ", pl.global_position)
	if str(_args.get("prompts", "1")) != "0":
		for nm in SPOTS:
			if not nodes.has(nm):
				_log.append("MISSING node " + nm)
				continue
			var it: Node2D = nodes[nm]
			pl.position = Vector2(it.global_position.x, pl.position.y)
			g.camera.snap_now()
			await _frames(14)
			var f = pl.focus
			var fname: String = str(f.name) if f != null else "<none>"
			var ptxt: String = str(f.prompt_text()) if f != null else ""
			_log.append("%-18s x=%5d focus=%-18s prompt=%s" % [nm, int(it.global_position.x), fname, ptxt])
			await _shot("prompt_" + nm)
	for id in str(_args.get("open", "")).split(",", false):
		await _open(nodes, id)
	for l in _log:
		print("SPOT ", l)
	quit(0)


## Completes chapter 1 in the in-memory Story through its public API (no saves): the archive becomes the
## current scene, exactly as after the real transition.
func _finish_chapter_one() -> void:
	var st: Node = root.get_node("Story")
	st.start_dialogue("a1_talk_irina")
	var n := 0
	while st.state["dialogue_progress"].has("a1_talk_irina") and n < 50:
		st.advance_dialogue("a1_talk_irina")
		n += 1
	st.inspect("a1_inspect_seal")
	st.inspect("a1_inspect_timetable")
	st.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"])
	st.inspect("a1_inspect_ledger")
	st.choose("a1_choose", "share_with_irina")
	for c in st.pending_cinematics():
		st.consume_cinematic(c, true)


## Walks to the node that presents explore id `id` and triggers it through Game.interact (the real path).
func _open(nodes: Dictionary, id: String) -> void:
	var g := _game()
	var target: Node2D = null
	for nm in nodes:
		if str(nodes[nm].get("explore_id")) == id or str(nm) == id:
			target = nodes[nm]
	if target == null:
		_log.append("OPEN missing " + id)
		return
	var pl: Node = g.player
	pl.position = Vector2(target.global_position.x, pl.position.y)
	g.camera.snap_now()
	await _frames(12)
	if pl.focus != target:
		_log.append("OPEN %s: focus is %s, not the target" % [id, pl.focus.name if pl.focus else "<none>"])
	g.interact(target)
	var view: Node = g.ui.get("discovery")
	var dlg: Node = g.ui.get("dialogue")
	if str(target.get("kind")) == "discover":
		await _frames(70)
		await _shot("open_" + id.replace(".", "_"))
		var page := 1
		while view.get("is_open") == true and page < 4:
			if view.has_method("is_last_page") and view.is_last_page():
				break
			view.next()
			page += 1
			await _frames(50)
			await _shot("open_%s_p%d" % [id.replace(".", "_"), page])
		view.close()
	else:
		var line := 0
		while g.busy and line < 14:
			line += 1
			await _frames(150)
			if line <= 3 or str(_args.get("all_lines", "0")) == "1":
				await _shot("open_%s_l%d" % [id.replace(".", "_"), line])
			dlg.emit_signal("advanced")
	await _frames(30)
	_log.append("OPEN %s done; found=%s counts=%s" % [id, root.get_node("Explore").is_found(id) if id.begins_with("berlin.") else "-",
		root.get_node("Explore").counts("L_M1_Archive")])
