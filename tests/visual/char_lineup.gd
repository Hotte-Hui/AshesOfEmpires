extends Node
## In-game character lineup (owner: characters). Boots the REAL Main scene into a level (real lighting, grade,
## palette snap, per-texel lighting, hi-res world path), hides the level's own NPCs and stands the requested
## characters side by side on the floor through scripts/actors/npc.gd, then saves screenshots:
##   <out>/<tag>_full.png      the composed 1920x1080 window
##   <out>/<tag>_crop.png      the lineup strip, cropped and enlarged (nearest) for review
## With --cl-talk the row talks (talk_side) for the second shot; --cl-front shows idle_front / talk_front.
##   godot --path . res://tests/visual/char_lineup.tscn -- --scene=L_C3_Station --capture=<dir>/boot.png \
##         --frames=100000 --cl-out=<dir> [--cl-tag=station] [--cl-ids=a,b,c] [--cl-x0=40] [--cl-step=34]
##         [--cl-y=300] [--cl-cam=0,0] [--cl-talk] [--cl-front] [--cl-zoom=2]
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing.)
## Exit code 0 = all shots written. Never writes saves or settings (capture mode).

const MAIN := "res://scenes/main/Main.tscn"
const NPC := preload("res://scripts/actors/npc.gd")
const DEFAULT_IDS := ["alexei", "konrad", "irina", "emil", "elena", "border_officer", "conductor", "voronova",
	"kessler", "typist", "journalist", "babushka"]

var out_dir := ""
var tag := "lineup"
var ids: Array = DEFAULT_IDS
var x0 := 40.0
var step := 34.0
var floor_y := -1.0
var cam := Vector2(-1, -1)
var talk := false
var front := false
var zoom := 2
var npcs: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--cl-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--cl-tag="):
			tag = a.substr(9)
		elif a.begins_with("--cl-ids="):
			ids = Array(a.substr(9).split(",", false))
		elif a.begins_with("--cl-x0="):
			x0 = float(a.substr(8))
		elif a.begins_with("--cl-step="):
			step = float(a.substr(10))
		elif a.begins_with("--cl-y="):
			floor_y = float(a.substr(7))
		elif a.begins_with("--cl-cam="):
			var c := a.substr(9).split(",")
			cam = Vector2(float(c[0]), float(c[1]))
		elif a == "--cl-talk":
			talk = true
		elif a == "--cl-front":
			front = true
		elif a.begins_with("--cl-zoom="):
			zoom = maxi(1, int(a.substr(10)))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://char_lineup")
	DirAccess.make_dir_recursive_absolute(out_dir)
	get_tree().create_timer(60.0).timeout.connect(func(): print("CHAR_LINEUP TIMEOUT"); get_tree().quit(2))
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		print("CHAR_LINEUP FAIL: level / player never appeared")
		get_tree().quit(1)
		return
	await _frames(20)
	var pf: Node2D = Game.level.get_node_or_null("Playfield")
	if pf == null:
		pf = Game.level
	for n in get_tree().get_nodes_in_group("npcs"):
		(n as Node2D).visible = false
	var y: float = floor_y if floor_y > 0.0 else float(Game.player.position.y)
	Game.player.position = Vector2(-400, y)        # out of the frame
	for i in ids.size():
		var n: Node2D = NPC.new()
		n.char_id = str(ids[i])
		n.look_at_player = false
		n.idle_variants = false
		n.turn_to_talk = false
		if front:
			n.idle_anim = "idle_front"
		n.position = Vector2(x0 + i * step, y)
		pf.add_child(n)
		npcs.append(n)
	var c := cam if cam.x >= 0.0 else Vector2(maxf(0.0, x0 - 24.0), 0.0)
	Game.camera.cinematic = true
	Game.camera.set_top_left(c)
	await _frames(40)
	await _shot(tag + "_idle", c, y)
	if talk:
		for n in npcs:
			n.set_talking(true)
		await _frames(14)
		await _shot(tag + "_talk", c, y)
	print("CHAR_LINEUP PASS ", out_dir)
	get_tree().quit(0)


func _shot(label: String, c: Vector2, y: float) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir.path_join(label + "_full.png"))
	# crop the row: world -> screen at the current world scale
	var k := float(Game.view.world_scale) if Game.view and "world_scale" in Game.view else 3.0
	var top := int(maxf(0.0, (y - 60.0 - c.y) * k))
	var left := int(maxf(0.0, (x0 - 20.0 - c.x) * k))
	var w := int(minf(img.get_width() - left, (ids.size() * step + 24.0) * k))
	var h := int(minf(img.get_height() - top, 72.0 * k))
	if w > 0 and h > 0:
		var crop := img.get_region(Rect2i(left, top, w, h))
		if zoom > 1:
			crop.resize(w * zoom, h * zoom, Image.INTERPOLATE_NEAREST)
		crop.save_png(out_dir.path_join(label + "_crop.png"))
	print("CHAR_LINEUP SHOT ", label)
