extends Control
## Portrait check for the round-7 cast (owner: characters): the REAL DialogueBox (scenes/ui/DialogueBox.tscn)
## shows a real line of each speaker (data/v3/dialogue.json, the Chapter-3 chats) over an in-game backdrop:
##   * every speaker has a living portrait (animation grid in use), the mouth moves while the line types and
##     rests when it is complete, the expression column follows the line's expression
##   * screenshots: each speaker x 4 expressions at rest, plus talking / blinking poses
## Run windowed (screenshots) or headless (checks only):
##   godot --path . res://tests/visual/char_portraits.tscn -- --out=<dir> [--bg=<png>] [--only=elena,kessler]
## Never writes saves or settings. Exit code 0 = all checks passed.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const DLG := preload("res://scenes/ui/DialogueBox.tscn")
const SPEAKERS := ["elena", "border_officer", "conductor", "voronova", "kessler", "typist", "journalist", "alexei",
	"konrad", "irina", "emil", "vendor", "worker_a", "babushka", "librarian", "porter", "photographer"]
const EXPRS := ["neutral", "concerned", "determined", "surprised"]
const FALLBACK := "Wer den Fahrplan kennt, kennt auch die Lücken darin."

var dlg: Control
var out_dir := ""
var only: Array = []
var headless := false
var failures: Array = []
var shots := 0
var lines := {}
var backdrop: TextureRect


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	headless = DisplayServer.get_name() == "headless"
	var bg_path := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--bg="):
			bg_path = a.substr(5)
		elif a.begins_with("--only="):
			only = Array(a.substr(7).split(",", false))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://char_portraits")
	DirAccess.make_dir_recursive_absolute(out_dir)
	if not headless:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(1920, 1080))
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		s.values = s.DEFAULTS.duplicate(true)      # deterministic, in memory only (never saved here)
	theme = Kit.theme()
	backdrop = TextureRect.new()
	backdrop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_SCALE
	backdrop.size = Vector2(1920, 1080)
	if bg_path != "" and FileAccess.file_exists(bg_path):
		var img := Image.load_from_file(bg_path)
		if img != null and not img.is_empty():
			backdrop.texture = ImageTexture.create_from_image(img)
	add_child(backdrop)
	dlg = DLG.instantiate()
	add_child(dlg)
	_collect_lines()
	get_tree().create_timer(240.0, true).timeout.connect(func(): print("CHAR_PORTRAITS TIMEOUT"); get_tree().quit(2))
	_run.call_deferred()


## One real line per speaker: story dialogue first, then the exploration chats.
func _collect_lines() -> void:
	var d = Kit.json("res://data/v3/dialogue.json")
	if d is Dictionary:
		for conv in d.get("conversations", []):
			for n in conv.get("nodes", []):
				var sp := str(n.get("speaker", ""))
				var k := str(n.get("text_key", ""))
				if sp != "" and not lines.has(sp) and Kit.has_key(k):
					lines[sp] = k
	for f in ["res://data/explore/veltrava_station.json", "res://data/explore/veltrava_hall.json",
			"res://data/explore/karsk.json", "res://data/explore/berlin.json", "res://data/explore/plaza.json"]:
		var e = Kit.json(f)
		if not (e is Dictionary):
			continue
		for ent in e.get("entries", []):
			for l in ent.get("lines", []):
				var sp := str(l.get("speaker", ""))
				if sp != "" and not lines.has(sp) and Kit.has_key(str(l.get("key", ""))):
					lines[sp] = str(l["key"])


func _line(sp: String) -> String:
	return Kit.t(str(lines[sp])) if lines.has(sp) else FALLBACK


func check(cond: bool, what: String) -> void:
	print(("  PASS " if cond else "  FAIL ") + what)
	if not cond:
		failures.append(what)


func frames(n: int) -> void:
	for _i in n:
		await get_tree().process_frame


func shot(name: String) -> void:
	shots += 1
	if headless:
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir.path_join("%03d_%s.png" % [shots, name]))


func _run() -> void:
	await frames(3)
	var who: Array = SPEAKERS if only.is_empty() else only
	for sp in who:
		# behaviour: typing moves the mouth, the end of the line rests it, the column is the expression
		dlg.dock_top = false
		dlg.show_line(sp, _line(sp), "concerned")
		var st: Dictionary = dlg.portrait_state()
		check(bool(st.get("animated", false)), "%s: living portrait (animation grid)" % sp)
		check(int(st.get("column", -1)) == EXPRS.find("concerned"), "%s: expression column = concerned" % sp)
		var seen := {}
		for _i in 90:
			await get_tree().process_frame
			seen[dlg.portrait_state().get("mouth", 0)] = true
			if not dlg.is_typing():
				break
		check(seen.size() >= 2, "%s: mouth moves while the line types (%s)" % [sp, str(seen.keys())])
		dlg.skip_typing()
		await frames(2)
		check(int(dlg.portrait_state().get("mouth", -1)) == 0, "%s: mouth rests when the line is complete" % sp)
		for e in EXPRS:
			await _pose(sp, e, "rest")
		await _pose(sp, "neutral", "talk")
		await _pose(sp, "neutral", "blink")
	dlg.close()
	print("CHAR_PORTRAITS: %d checks failed, %d shots" % [failures.size(), shots])
	get_tree().quit(1 if failures.size() > 0 else 0)


func _pose(sp: String, expr: String, pose: String) -> void:
	var was_open: bool = dlg.is_open
	dlg.show_line(sp, _line(sp), expr)
	if not was_open:
		await get_tree().create_timer(0.35, true).timeout
	dlg.skip_typing()
	dlg._p_eyes_closed = pose == "blink"
	dlg._p_blink_t = -100.0
	dlg._p_blink_left = 0.0
	dlg._p_mouth = 2 if pose == "talk" else 0
	dlg._apply_portrait_frame()
	await frames(2)
	await shot("%s_%s_%s" % [sp, expr, pose])
