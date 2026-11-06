extends SceneTree
## In-game capture of the two Chapter-3 mini-games at their real spots (owner: minigames r7, §12.8).
## Boots the real Main scene with the level, advances the in-memory Story through the public API (A1 + M1, plus
## C3a for the palace) so the level is the story's current scene and nothing reloads, places the protagonist on
## the hotspot and captures: the prompt with the world cue, the mini-game opened through Game.interact() (the
## real path: Game._do_discover -> _run_minigame), the solved state after demo_solve() (synthetic keys only),
## the DiscoveryView pages of the find, and the world afterwards (the restored board / Wenzel at the counter).
## Writes NO saves (Main boots in capture mode; --frames keeps Game's own capture flow from quitting first).
##
## godot --path . --script res://tests/visual/minigames_r7_v_ingame.gd -- --scene=L_C3_Station --char=alexei
##       --capture=<dir>/_unused.png --frames=999999 --shots=<dir>
## godot --path . --script res://tests/visual/minigames_r7_v_ingame.gd -- --scene=L_C3_Hall --char=konrad
##       --capture=<dir>/_unused.png --frames=999999 --shots=<dir>

const TK := preload("res://tests/support/test_kit.gd")
const SPOTS := {"L_C3_Station": ["Find_FlapBoard", "veltrava.station.flap_board", "station"],
	"L_C3_Hall": ["Find_CloakTokens", "veltrava.hall.cloak_tokens", "hall"]}

var _args := {}
var _out := ""


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			_args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	_out = str(_args.get("shots", "user://minigames_r7_v_ingame"))
	DirAccess.make_dir_recursive_absolute(_out)
	var main: Node = load("res://scenes/main/Main.tscn").instantiate()
	root.add_child(main)
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var path := _out.path_join(name + ".png")
	img.save_png(path)
	print("SHOT ", path)


func _advance_story(level_id: String) -> void:
	var st: Node = root.get_node("Story")
	var tk := TK.new()
	tk.play_a1(st)
	tk.play_m1(st)
	for c in st.pending_cinematics():
		st.consume_cinematic(c, true)
	if level_id == "L_C3_Hall":
		tk.play_c3a(st)
		for c in st.pending_cinematics():
			st.consume_cinematic(c, true)
	if not tk.failures.is_empty():
		printerr("HARNESS story: ", tk.failures)
	print("STORY scene now ", st.current_scene)


func _run() -> void:
	var g: Node = root.get_node("Game")
	var guard := 0
	while (g.level == null or g.player == null) and guard < 900:
		guard += 1
		await process_frame
	if g.level == null:
		printerr("HARNESS: level did not load")
		quit(1)
		return
	var lid := str(g.level.level_id)
	if not SPOTS.has(lid):
		printerr("HARNESS: unknown level ", lid)
		quit(1)
		return
	_advance_story(lid)
	await _frames(30)
	var spec: Array = SPOTS[lid]
	var it: Node2D = g.level.playfield.get_node_or_null(str(spec[0]))
	if it == null:
		printerr("HARNESS: no node ", spec[0])
		quit(1)
		return
	var pl: Node2D = g.player
	pl.position = it.global_position + Vector2(-2, 1)
	g.camera.snap_now()
	await _frames(20)
	var f = pl.get("focus")
	print("FOCUS ", f.name if f != null else "<none>", " prompt=", f.prompt_text() if f != null else "")
	await _shot("ig_%s_1_prompt" % spec[2])
	g.interact(it)
	var mg: Node = null
	guard = 0
	while mg == null and guard < 240:
		guard += 1
		await process_frame
		for n in get_nodes_in_group("minigame"):
			if is_instance_valid(n) and n.get("is_open") == true:
				mg = n
	if mg == null:
		printerr("HARNESS: the mini-game did not open")
		quit(1)
		return
	await _frames(40)
	await _shot("ig_%s_2_minigame" % spec[2])
	await mg.demo_solve()
	await _frames(10)
	await _shot("ig_%s_3_solved" % spec[2])
	var view: Node = g.ui.get("discovery")
	guard = 0
	while not (view != null and view.get("is_open") == true) and guard < 600:
		guard += 1
		await process_frame
	await _frames(70)
	await _shot("ig_%s_4_find" % spec[2])
	var page := 1
	while view != null and view.get("is_open") == true and page < 4:
		if view.has_method("is_last_page") and view.is_last_page():
			break
		view.next()
		page += 1
		await _frames(50)
		await _shot("ig_%s_4_find_p%d" % [spec[2], page])
	if view != null and view.get("is_open") == true:
		view.close()
	guard = 0
	while g.busy and guard < 300:
		guard += 1
		await process_frame
	await _frames(60)
	await _shot("ig_%s_5_after" % spec[2])
	var ex: Node = root.get_node("Explore")
	print("RESULT found=%s counts=%s busy=%s" % [ex.is_found(str(spec[1])), ex.counts(lid), g.busy])
	quit(0)
