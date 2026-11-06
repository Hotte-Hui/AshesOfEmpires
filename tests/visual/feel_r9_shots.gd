extends Node
## Visual check of the round-9 feel pass 2 (owner feel_r9): quay walkers, the side task „Eine Decke für Frau
## Brunner“ (prompt mark, journal), toasts held by a modal, any level at 1440p / 2160p.
## Boots the real Main scene in capture mode (Game: no autosave, no intro, no focus pause), loads --scene,
## then per shot places the player, moves the camera and waits real seconds (walkers keep walking).
##   godot --path . res://tests/visual/feel_r9_shots.tscn -- --scene=L_C3_Quay --char=alexei \
##         --capture=<dir>/boot.png --frames=100000 --f9-out=<dir> [--f9-size=2560x1440] \
##         [--f9-sizes=2560x1440;3840x2160] --f9-shots=label:camx:playerx:playery:seconds[:action],...
## camx "-" keeps the gameplay camera on the player, playerx "-" leaves the player at the spawn; --f9-sizes takes
## every shot once per window size (<label>_<w>x<h>.png: 1440p -> world scale 4, 2160p -> 6).
## Actions: "hud" (keep the HUD on: objective tracker, prompts), "task" (Explore state in memory only: Frau
## Brunner's chat and the task's ask found -> the locker shows the task mark), "journal" (the journal on the
## „Aufgaben“ tab with the quay task active), "toast_modal" (a toast, then the journal opens over it: the shot shows
## the held state), "toast_back" (as before, the journal closes again: the toast is back with its time left).
## Explore state is restored and nothing is ever saved (capture mode). Exit code 0 = every shot taken.

const MAIN := "res://scenes/main/Main.tscn"
const UIKit := preload("res://scripts/ui/ui_kit.gd")

var out_dir := ""
var shots_spec: Array = []
var shots := 0
var problems: Array = []
var size := Vector2i.ZERO
var sizes: Array = []           ## --f9-sizes=2560x1440;3840x2160: every shot once per window size (label_<w>x<h>)
var _ex_saved: Dictionary = {}


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--f9-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--f9-shots="):
			shots_spec = Array(a.substr(11).split(",", false))
		elif a.begins_with("--f9-size="):
			var wh: PackedStringArray = a.substr(10).split("x")
			size = Vector2i(int(wh[0]), int(wh[1]))
		elif a.begins_with("--f9-sizes="):
			for s in a.substr(11).split(";", false):
				var wh2: PackedStringArray = s.split("x")
				sizes.append(Vector2i(int(wh2[0]), int(wh2[1])))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://feel_r9_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 60.0
	for s in shots_spec:
		var p: PackedStringArray = str(s).split(":")
		limit += 8.0 + (float(p[4]) if p.size() > 4 else 1.0)
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("F9_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	if get_node_or_null("/root/Game") == null:
		print("F9_PROBLEM the Game autoload is missing (a project script failed to parse?)")
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
	print("F9_SHOT ", path, " ", img.get_size(), " k=", Game.view.world_scale if Game.view else -1)


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	if size != Vector2i.ZERO:
		get_window().size = size
		for i in 10:
			await get_tree().process_frame
		print("F9_WINDOW ", get_window().size, " viewport ", get_viewport().get_visible_rect().size)
	for i in 20:
		await get_tree().process_frame
	var ex := get_node_or_null("/root/Explore")
	if ex != null:
		_ex_saved = ex.state()
	for spec in shots_spec:
		var p: PackedStringArray = str(spec).split(":")
		if p.size() < 5:
			problems.append("bad shot spec " + str(spec))
			continue
		var action := p[5] if p.size() > 5 else ""
		var hud = Game.ui.get("hud") if Game.ui else null
		if hud and hud.has_method("hide_hud") and action == "":
			hud.hide_hud()
		elif hud and hud.has_method("show_hud"):
			hud.show_hud()
		if p[2] != "-":
			Game.player.global_position = Vector2(float(p[2]), float(p[3]))
		if p[1] != "-":                 # "-": the gameplay camera keeps following the player
			Game.camera.cinematic = true
			Game.camera.set_top_left(Vector2(float(p[1]), 0.0))
		if action.begins_with("disc=") or action.begins_with("insp="):
			# disc=<explore id>@<text scale> / insp=<item id>@<text scale>: the close-up / document view at that
			# text scale (Settings in memory only -- user://settings.cfg is never written)
			var parts: PackedStringArray = action.substr(5).split("@")
			var st := get_node_or_null("/root/Settings")
			if st != null:
				st.values["text_scale"] = float(parts[1]) if parts.size() > 1 else 1.0
				UIKit.refresh_text_scale()
			if action.begins_with("disc="):
				Game.ui.discovery.open(parts[0], [])
			else:
				Game.ui.inspect.open(parts[0])
		if action.begins_with("walker="):
			# walker=<id>@<segment>: puts that ambient walker halfway along path segment i -> i+1 (negative: heading
			# back from i+1 to i), e.g. the station porter on his steep segment for the walk_front / walk_back rows
			var wp: PackedStringArray = action.substr(7).split("@")
			_place_walker(wp[0], int(wp[1]) if wp.size() > 1 else 0)
		if action in ["task", "journal"] and ex != null:
			ex.restore({"found": ["veltrava.quay.chat_typist", "veltrava.task.blanket.ask"], "cards": []})
		if action == "journal":
			Game.ui.open_journal("tasks")
		elif action.begins_with("toast"):
			Game.toast(Loc.t("ui.toast.task_new", {"name": Loc.t("task.veltrava.blanket.title")}))
			for i in 30:
				await get_tree().process_frame
			Game.ui.open_journal("tasks")
			for i in 40:
				await get_tree().process_frame
			if action == "toast_back":
				var j: Control = Game.ui.journal
				if j != null and j.has_method("close"):
					j.close()
				elif Game.ui.has_method("pop_modal"):
					Game.ui.pop_modal(j)
		var until := Time.get_ticks_msec() + int(float(p[4]) * 1000.0)
		while Time.get_ticks_msec() < until:
			await get_tree().process_frame
		if sizes.is_empty():
			await _shot(p[0])
		for sz in sizes:
			get_window().size = sz
			for i in 12:
				await get_tree().process_frame
			await _shot("%s_%dx%d" % [p[0], sz.x, sz.y])
		if action == "journal" and Game.ui.journal != null:
			Game.ui.pop_modal(Game.ui.journal)
		if action.begins_with("disc=") and Game.ui.discovery != null:
			Game.ui.pop_modal(Game.ui.discovery)
		if action.begins_with("insp=") and Game.ui.inspect != null:
			Game.ui.pop_modal(Game.ui.inspect)
	_finish()


func _place_walker(id: String, seg: int) -> void:
	var pf: Node = Game.level.get_node_or_null("Playfield") if Game.level else null
	for c in (pf.get_children() if pf != null else []):
		if not ("list" in c):
			continue
		for w in c.get("list"):
			if str(w.id) != id:
				continue
			var i := absi(seg)
			var back := seg < 0
			w.from_i = i + 1 if back else i
			w.to_i = i if back else i + 1
			w.base = w.pts[i].lerp(w.pts[i + 1], 0.5)
			w.offset = 0.0
			w.offset_target = 0.0
			w.state = "walk"
			print("F9_WALKER ", id, " segment ", seg, " at ", w.base)
			return
	problems.append("walker %s not found" % id)


func _finish() -> void:
	var ex := get_node_or_null("/root/Explore")
	if ex != null and not _ex_saved.is_empty():
		ex.restore(_ex_saved)
	for pr in problems:
		print("F9_PROBLEM ", pr)
	print("F9_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
