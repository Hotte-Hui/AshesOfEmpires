extends Control
## Portrait harness (tests/visual/portrait_harness.tscn) for the living dialogue portraits.
## Shows the REAL DialogueBox (scenes/ui/DialogueBox.tscn) for every chat speaker and expression over an
## in-game backdrop, checks the portrait behaviour and saves 1920x1080 screenshots:
##   * talking mouth follows the typewriter, rests during punctuation pauses and when the line is complete
##   * the eyes blink every few seconds (and open again), the expression column never changes within a line
##   * speakers without a portrait keep the silhouette placeholder; old static strips stay static
##   * dock_top / toast suppression and the choice guard (CHOICE_GUARD_MS) are unchanged
## Run windowed (screenshots) or headless (checks only):
##   godot --path . res://tests/visual/portrait_harness.tscn -- --out=<dir> [--bg-karsk=<png>] [--bg-berlin=<png>]
##        [--only=konrad,irina] [--sheet]
## Never writes saves or settings. Exit code: 0 = all checks passed, 1 = a check failed.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const DLG := preload("res://scenes/ui/DialogueBox.tscn")
const SPEAKERS := ["alexei", "konrad", "irina", "emil", "vendor", "worker_a", "babushka", "librarian", "porter"]
const BERLIN := ["konrad", "emil", "librarian", "porter"]
const EXPRS := ["neutral", "concerned", "determined", "surprised"]
const FALLBACK_LINE := {
	"alexei": "dlg.alexei.02", "konrad": "dlg.konrad.01", "irina": "dlg.irina.02", "emil": "dlg.emil.03",
}

var dlg: Control
var out_dir := ""
var only: Array = []
var headless := false
var failures: Array = []
var shots := 0
var backdrop: TextureRect
var bg := {}
var lines := {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	headless = DisplayServer.get_name() == "headless"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--bg-karsk="):
			bg["karsk"] = _load_png(a.substr(11))
		elif a.begins_with("--bg-berlin="):
			bg["berlin"] = _load_png(a.substr(12))
		elif a.begins_with("--only="):
			only = Array(a.substr(7).split(","))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://portrait_harness")
	DirAccess.make_dir_recursive_absolute(out_dir)
	_setup_window()
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		s.values = s.DEFAULTS.duplicate(true)   # deterministic, in memory only (never saved here)
	theme = Kit.theme()
	backdrop = TextureRect.new()
	backdrop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_SCALE
	backdrop.size = Vector2(1920, 1080)
	add_child(backdrop)
	dlg = DLG.instantiate()
	add_child(dlg)
	_collect_lines()
	_run.call_deferred()


func _setup_window() -> void:
	if headless:
		return
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	var scr := DisplayServer.screen_get_size()
	if scr.x <= 1920 or scr.y <= 1130:
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
		DisplayServer.window_set_position(Vector2i.ZERO)
	DisplayServer.window_set_size(Vector2i(1920, 1080))


func _load_png(path: String) -> Texture2D:
	if not FileAccess.file_exists(path):
		return null
	var img := Image.load_from_file(path)
	return ImageTexture.create_from_image(img) if img != null and not img.is_empty() else null


## One real in-game line per speaker: the exploration chats (data/explore/*.json) or the slice dialogue.
func _collect_lines() -> void:
	for f in ["res://data/explore/karsk.json", "res://data/explore/berlin.json"]:
		var d = Kit.json(f)
		if not (d is Dictionary):
			continue
		for e in d.get("entries", []):
			for l in e.get("lines", []):
				var sp := str(l.get("speaker", ""))
				if sp != "" and not lines.has(sp) and Kit.has_key(str(l.get("key", ""))):
					lines[sp] = str(l["key"])
	for sp in FALLBACK_LINE:
		if not lines.has(sp):
			lines[sp] = FALLBACK_LINE[sp]


func _line(sp: String) -> String:
	return Kit.t(str(lines.get(sp, "dlg.konrad.01")))


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
	var path := out_dir.path_join("%03d_%s.png" % [shots, name])
	img.save_png(path)
	print("SHOT ", path)


func _set_backdrop(sp: String) -> void:
	var key := "berlin" if sp in BERLIN else "karsk"
	backdrop.texture = bg.get(key)
	backdrop.visible = backdrop.texture != null


# ------------------------------------------------------------------------------------------- run
func _run() -> void:
	await frames(3)
	print("-- behaviour checks")
	await _behaviour()
	print("-- screenshots")
	var who: Array = SPEAKERS if only.is_empty() else only
	for sp in who:
		_set_backdrop(sp)
		for e in EXPRS:
			await _pose(sp, e, "rest", "%s_%s" % [sp, e])
		await _pose(sp, "neutral", "talk", "%s_neutral_talk" % sp)
		await _pose(sp, "neutral", "blink", "%s_neutral_blink" % sp)
	dlg.close()
	print("PORTRAIT HARNESS: %d checks failed, %d shots" % [failures.size(), shots])
	get_tree().quit(1 if failures.size() > 0 else 0)


## Deterministic frame for a screenshot: full line shown, then mouth / eyes forced for the pose.
func _pose(sp: String, expr: String, pose: String, name: String) -> void:
	dlg.dock_top = false
	var was_open: bool = dlg.is_open
	dlg.show_line(sp, _line(sp), expr)
	if not was_open:
		await get_tree().create_timer(0.35, true).timeout   # let the open tween (Kit.appear) finish
	dlg.skip_typing()
	dlg._p_eyes_closed = pose == "blink"
	dlg._p_blink_t = -100.0            # no spontaneous blink during the shot
	dlg._p_blink_left = 0.0
	dlg._p_mouth = 2 if pose == "talk" else 0
	dlg._apply_portrait_frame()
	await frames(2)
	var st: Dictionary = dlg.portrait_state()
	check(st["animated"], "%s/%s uses the animation grid" % [sp, expr])
	await shot(name)


func _behaviour() -> void:
	# 1) mouth follows the typewriter and rests at the end
	_set_backdrop("konrad")
	dlg.show_line("konrad", _line("konrad"), "concerned")
	var st: Dictionary = dlg.portrait_state()
	check(st["animated"], "konrad portrait has an animation grid")
	var col0: int = st["column"]
	check(col0 == EXPRS.find("concerned"), "expression column = concerned")
	var seen := {}
	var cols := {}
	var rest_in_pause := true
	for _i in 120:
		await get_tree().process_frame
		var s2: Dictionary = dlg.portrait_state()
		seen[s2["mouth"]] = true
		cols[s2["column"]] = true
		if dlg._delay > 0.05 and dlg.is_typing() and s2["mouth"] != 0:
			rest_in_pause = false
		if not dlg.is_typing():
			break
	check(seen.size() >= 2, "mouth changes while typing (states seen: %s)" % str(seen.keys()))
	check(cols.size() == 1, "expression column constant during the line")
	check(rest_in_pause, "mouth rests during punctuation pauses")
	dlg.skip_typing()
	await frames(2)
	check(dlg.portrait_state()["mouth"] == 0, "mouth rests when the line is complete")
	# 2) blink within a few seconds, eyes open again
	var closed := false
	var reopened := false
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 7000:
		await get_tree().process_frame
		if dlg.portrait_state()["eyes_closed"]:
			closed = true
		elif closed:
			reopened = true
			break
	check(closed and reopened, "eyes blink and open again")
	# 3) region always inside the grid
	var r: Rect2 = dlg.portrait_state()["region"]
	check(r.size == Vector2(112, 112), "frame region is 112x112")
	# 4) placeholder for a speaker without portrait files
	dlg.show_line("guard", Kit.t("dlg.konrad.02"), "neutral")
	await frames(2)
	check(dlg.portrait_state()["placeholder"], "speaker without portrait keeps the silhouette placeholder")
	await shot("placeholder_guard")
	# 5) dock_top + toast suppression unchanged
	dlg.dock_top = true
	await frames(2)
	check(dlg.suppress_toasts, "dock_top suppresses toasts")
	dlg.show_line("emil", _line("emil"), "neutral")
	dlg.skip_typing()
	await frames(2)
	await shot("dock_top_emil")
	dlg.dock_top = false
	check(not dlg.suppress_toasts, "bottom dock releases toasts")
	# 6) choice guard: a confirm press right after the choices appear is ignored
	var picked := [""]
	var cb := func(id): picked[0] = id
	dlg.chosen.connect(cb)
	dlg.show_line("alexei", Kit.t("obj.a1_choice") if Kit.has_key("obj.a1_choice") else _line("alexei"), "concerned")
	dlg.show_choices([{"id": "a", "text": "choice.share_irina"}, {"id": "b", "text": "choice.keep_secret"}])
	dlg.skip_typing()
	await frames(1)
	var ev := InputEventAction.new()
	ev.action = "advance"
	ev.pressed = true
	dlg.modal_input(ev)
	await frames(2)
	check(picked[0] == "", "choice guard ignores an immediate confirm")
	dlg.chosen.disconnect(cb)
	await shot("choices_alexei")
	dlg.close()
	await frames(2)
	# 7) static strip fallback (no "anim" block) stays static
	var e2: Dictionary = dlg._portrait_entry("konrad").duplicate()
	e2["anim_tex"] = null
	e2["id"] = "konrad_static_test"
	dlg._portrait_cache["konrad_static_test"] = e2
	dlg.show_line("konrad_static_test", _line("konrad"), "surprised")
	var moved := false
	for _i in 40:
		await get_tree().process_frame
		if dlg.portrait_state()["region"].position.y != 0:
			moved = true
	check(not dlg.portrait_state()["animated"] and not moved, "strip without anim block stays static (row 0)")
	dlg.skip_typing()
	dlg.close()
	await frames(2)
