extends Node
## Visual check of the Karsk exploration layer (owner: karsk-explore). Boots the real Main scene into
## L_A1_Railyard in capture mode (Game: no autosave, no intro, no focus pause), places Alexei on a find's
## hotspot, captures the HUD prompt, then interacts through Game.interact() and captures the result
## (DiscoveryView page / chat lines / spoken fallback). Writes PNGs only into --kx-out=<absolute dir>.
##   godot --path . res://tests/visual/karsk_explore_shots.tscn -- --scene=L_A1_Railyard \
##         --capture=<dir>/boot.png --frames=100000 --kx-out=<dir> [--symbols=0|1] [--kx-only=ExpCat,ChatVendor]
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)
## Exit code 0 = every requested shot was taken and Alexei's focus matched the target; 1 otherwise.

const MAIN := "res://scenes/main/Main.tscn"
const DEFAULT_TARGETS := ["ChatVendor", "ChatFamily", "ExpSnowman", "ExpStairsUnder", "ExpNewspaper", "ExpCrows",
	"ExpWagonChalk", "ChatWorkers", "ExpCat", "ExpBanner", "ExpStash", "ExpKontoraShelf", "ExpDistantTrain"]

var out_dir := ""
var only: Array = []
var problems: Array = []
var shots := 0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--kx-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--kx-only="):
			only = Array(a.substr(10).split(",", false))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://karsk_explore_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join(label + ".png")
	img.save_png(path)
	shots += 1
	print("KX_SHOT ", path)


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	await _frames(30)
	var targets: Array = only if not only.is_empty() else DEFAULT_TARGETS
	for name in targets:
		var it: Node = Game.level.get_node_or_null("Playfield/" + str(name))
		if it == null:
			problems.append("no node Playfield/%s" % name)
			continue
		await _visit(it)
	_finish()


func _visit(it: Node) -> void:
	var p: Node2D = Game.player
	p.global_position = it.global_position + Vector2(-4, 2)
	Game.camera.snap_now()
	await _frames(20)
	if p.focus != it:
		problems.append("%s: focus is %s, not the find" % [it.name, p.focus.name if p.focus else "none"])
	await _shot("prompt_" + str(it.name))
	Game.interact(it)
	if str(it.get("kind")) == "chat":
		var dlg = Game.ui.get("dialogue") if Game.ui else null
		var n: int = Explore.chat_lines(str(it.get("explore_id"))).size()
		for i in n:
			await _frames(8)
			if dlg and dlg.has_method("skip_typing"):
				dlg.skip_typing()
			await _frames(4)
			if i == 0 or i == n - 1 or i == 3:
				await _shot("chat_%s_%d" % [it.name, i + 1])
			if dlg and dlg.has_signal("advanced"):
				dlg.emit_signal("advanced")
	else:
		await _frames(50)
		await _shot("view_" + str(it.name))
		var view = Game.ui.get("discovery") if Game.ui else null
		if view and view.get("is_open") == true:
			if view.has_method("page_count") and view.page_count() > 1:
				view.next()
				await _frames(40)
				await _shot("view_%s_card" % it.name)
			view.close()
		else:
			# spoken fallback (no DiscoveryView): advance the line
			var dlg = Game.ui.get("dialogue") if Game.ui else null
			if dlg and dlg.has_signal("advanced"):
				dlg.emit_signal("advanced")
	var guard := 0
	while Game.busy and guard < 300:
		guard += 1
		await get_tree().process_frame
	await _frames(40)    # interaction cooldown + toast


func _finish() -> void:
	for pr in problems:
		print("KX_PROBLEM ", pr)
	print("KX_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
