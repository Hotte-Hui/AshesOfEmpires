extends Node
## Thumbnail captures for the „Erinnerungen“ cards (TECHNICAL_ARCHITECTURE §12.10). Boots the real Main scene in
## capture mode (no autosave, no intro pan, no chapter card, HUD hidden), loads every memory level, places the
## protagonist and the camera at a characteristic spot and saves the graded 640x360 world image
## (PixelView.capture_world_image, one sample per texel) as raw_<scene>.png. tools/pixelgen/gen_ui_memories.py
## then turns the raw frames into the sepia prints assets/ui/memories/<scene>.png (deterministic step).
## Each scene is loaded as a memory of itself (Game.memory_mode / memory_scene during the load), so the print shows
## the memory's cast — the Story NPCs read the remembered scene, not the capture's new game (StoryNPC: the siding's
## Lev stands at the siding) — and is then seen with the level's own grade again (the sepia is the generator's job).
##   godot --path . res://tests/visual/memory_thumbs.tscn -- --scene=L_A1_Railyard \
##         --capture=<dir>/boot.png --frames=100000 --mt-out=<dir> [--mt-survey=1] [--mt-only=L_A1_Railyard,…]
## --mt-survey=1 captures a camera sweep per level (survey_<scene>_<x>.png) to choose the spots below.
## The capture itself renders the running game (snow and walkers move), so the raw frames are not byte-identical
## between runs; the generator step is.

const MAIN := "res://scenes/main/Main.tscn"
## scene id: [camera top-left x, camera top-left y, player x, player y, face_left]
## (the print window inside each frame is chosen in tools/pixelgen/gen_ui_memories.py CROPS)
const SHOTS := {
	"L_A1_Railyard": [0, 0, 470, 297, false],
	"L_M1_Archive": [1280, 0, 1612, 300, false],
	"L_M1_Plaza": [320, 0, 676, 300, false],
	"L_C3_Station": [640, 0, 850, 300, false],
	"L_C3_Hall": [320, 0, 590, 300, true],
	# Chapter 3 part 2: four Story scenes in one level file (L_C3_Registry.tscn, look per scene) and the quay
	"L_C3_RegistryA": [0, 0, 340, 300, false],
	"L_C3_RegistryB": [640, 0, 1030, 300, true],
	"L_C3_RegistryC": [640, 0, 1208, 300, false],
	"L_C3_RegistryD": [320, 0, 604, 300, true],
	"L_C3_Quay": [0, 0, 452, 300, true],
	# Chapter 4 part 1: two level files, two Story scenes each, every camera inside its scene's camera_zones rect
	# (scene.json): the cellar with Lev at his desk, the siding with Alexei at wagon 24 318 (C-17/45) facing Lev at
	# his siding post (x 1790), the tram loop with Marta at tram 74, the annex counter with Fengler
	"L_C4_TunnelsA": [40, 0, 360, 300, false],
	"L_C4_TunnelsB": [1280, 0, 1712, 300, false],
	"L_C4_AnnexA": [120, 0, 330, 300, false],
	"L_C4_AnnexB": [1200, 0, 1580, 300, false],
	# Chapter 4 part 2 (round 10): again two level files, two Story scenes each, every camera inside its scene's
	# camera_zones rect: Alexei at the coal stage with Kolonne 4, Maria and the guard at the barrel fire; Konrad facing
	# Ekdahl at the dining car beside the courier car C-17; Alexei facing Ekdahl at the signal post (camera at the
	# zone's left edge 878 — at 1000 Ekdahl, x 996, falls outside), the model locomotive, the band; Konrad facing
	# Hanna at the stair door of the courtyard (the remembered state: Hanna still down, Wendt not yet there)
	"L_C4P2_KarskA": [160, 0, 470, 300, false],
	"L_C4P2_BerlinA": [139, 0, 735, 300, true],
	"L_C4P2_KarskB": [878, 0, 949, 300, false],
	"L_C4P2_BerlinB": [1099, 0, 1235, 300, false],
}

var out_dir := ""
var survey := false
var only: Array = []
var shots := 0
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--mt-out="):
			out_dir = a.substr(9)
		elif a == "--mt-survey=1":
			survey = true
		elif a.begins_with("--mt-only="):
			only = Array(a.substr(10).split(",", false))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://memory_thumbs")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 240.0 if survey else 120.0
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("MT_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	if get_node_or_null("/root/Game") == null:
		print("MT_PROBLEM the Game autoload is missing (a project script failed to parse?)")
		get_tree().quit(2)
		return
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _hide_hud() -> void:
	var hud = Game.ui.get("hud") if Game.ui else null
	if hud and hud.has_method("hide_hud"):
		hud.hide_hud()


func _save_world(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img: Image = Game.view.capture_world_image()
	var path := out_dir.path_join(name + ".png")
	img.save_png(path)
	shots += 1
	print("MT_SHOT ", path, " ", img.get_size())


## Who was there then: the memory table's protagonist of `id` (as Game._memory_protagonist inside a memory). Without
## it the player of a capture is the live Story's active character — Alexei in every scene after the new game.
func _protagonist(id: String) -> String:
	var m = Game.get("memories")
	if m == null or not m.has_method("scene"):
		return ""
	var who := str(m.scene(id).get("protagonist", ""))
	return "" if who in ["", "none"] else who


func _goto(id: String) -> bool:
	var who := _protagonist(id)
	if who != "":
		Game.args["char"] = who      # read by Game._setup_level (the `--char=` override)
	var here: bool = Game.level != null and str(Game.level.get("level_id")) == id and Game.player != null \
		and (who == "" or str(Game.player.get("char_id")) == who)
	if not here:
		# every scene loads afresh, like a memory (Game.travel_to_memory): another Story scene of the level file that
		# is already loaded (L_C3_RegistryA–D) would otherwise be handed over in place (§12.11, Game.switch_now).
		# Loaded as a memory of itself (the Story NPCs take the memory's cast while the level enters the tree), then
		# memory mode ends and the level's own grade comes back (no memory overlay in the raw frame).
		Game.set("_force_reload", true)
		Game.memory_mode = true
		Game.memory_scene = id
		await Game.goto_level(id, "", false)
		Game.memory_mode = false
		Game.memory_scene = ""
		if Game.level != null:
			Game._apply_grade(Game.level)
		var hud = Game.ui.get("hud") if Game.ui else null
		if hud and hud.has_method("set_memory"):
			hud.set_memory({})
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	return Game.level != null and Game.player != null and str(Game.level.get("level_id")) == id


func _run() -> void:
	await _frames(30)
	var ids: Array = only if not only.is_empty() else SHOTS.keys()
	for id in ids:
		if not SHOTS.has(id):
			problems.append("unknown scene " + str(id))
			continue
		if not await _goto(str(id)):
			problems.append("level %s did not load" % id)
			continue
		await _frames(30)
		_hide_hud()
		var s: Array = SHOTS[id]
		var p: Node2D = Game.player
		p.global_position = Vector2(float(s[2]), float(s[3]))
		if str(Game.player.get("mode")) == "side":
			p.position.y = float(Game.player.get("floor_y"))
		if p.has_method("face"):
			p.face(-1 if bool(s[4]) else 1)
		Game.camera.cinematic = true
		if survey:
			var b: Rect2 = Game.camera.bounds
			var x := b.position.x
			while x <= b.position.x + b.size.x - 640.0 + 0.5:
				Game.camera.set_top_left(Vector2(x, float(s[1])))
				p.global_position.x = x + 320.0
				await _frames(40)
				await _save_world("survey_%s_%04d" % [id, int(x)])
				x += 320.0
			continue
		Game.camera.set_top_left(Vector2(float(s[0]), float(s[1])))
		await _frames(90)
		await _save_world("raw_" + str(id))
	for pr in problems:
		print("MT_PROBLEM ", pr)
	print("MT_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
