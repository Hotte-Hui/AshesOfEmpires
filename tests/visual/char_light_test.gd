extends Node
## Visual test harness (owner: characters / chars-sprites): normal-map mirroring of character sprites.
## Every character is drawn twice through scripts/actors/sprite_rig.gd -- facing right and facing left
## (flip_h) -- under a dark CanvasModulate with ONE PointLight2D, first on the left, then on the right.
## A correctly mirrored normal map lights the side that faces the lamp in BOTH facings.  The harness
## measures, per sprite, the mean brightness of its left vs. right half (relative to the unlit diffuse),
## prints PASS/FAIL and saves the frames (1:1 and 6x nearest) to --out=DIR.
## Run windowed (headless has no renderer):
##   "$LOCALAPPDATA/Programs/Godot/Godot_v4.7.2-stable_win64_console.exe" --path C:/Spiele/AshesOfEmpires \
##       res://tests/visual/CharLightTest.tscn -- --out=C:/tmp/lighttest [--ids=alexei,konrad] [--texel]

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const TexelLightLib := preload("res://scripts/render/texel_light.gd")
const H := 140

var out_dir := ""
var texel := false                     ## --texel: apply the per-texel lighting material (as player / npc do)
var ids: Array = ["alexei", "konrad", "irina", "vendor", "librarian", "porter", "worker_b"]
var vp: SubViewport
var light: PointLight2D
var rigs: Array = []
var fails := 0
var W := 400                           ## grows with the number of characters (2 facings x 26 px + gap each)


func _ready() -> void:
	get_tree().create_timer(30.0).timeout.connect(func(): print("TIMEOUT"); get_tree().quit(2))
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--ids="):
			ids = Array(a.substr(6).split(","))
		elif a == "--texel":
			texel = true
	W = maxi(400, 30 + ids.size() * 56)
	vp = SubViewport.new()
	vp.size = Vector2i(W, H)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(vp)
	var bg := ColorRect.new()
	bg.color = Color(0.55, 0.55, 0.55)
	bg.size = Vector2(W, H)
	bg.light_mask = 0
	vp.add_child(bg)
	var cm := CanvasModulate.new()
	cm.color = Color(0.32, 0.32, 0.34)
	vp.add_child(cm)
	var x := 22.0
	for id in ids:
		for left in [false, true]:
			var r: Node2D = SpriteRig.new()
			r.position = Vector2(x, 100)
			vp.add_child(r)
			r.load_character(str(id))
			if texel:
				TexelLightLib.apply_tree(r)
			r.variants_enabled = false
			r.set_flip(left)
			rigs.append({"rig": r, "id": id, "left": left})
			x += 26.0
		x += 4.0
	light = PointLight2D.new()
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 1))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.width = 64
	gt.height = 64
	light.texture = gt
	light.texture_scale = 40.0         # uniform over the whole strip (half-size 1280 px): only the direction matters
	light.energy = 1.6
	light.height = 6.0
	vp.add_child(light)
	var view := TextureRect.new()
	view.texture = vp.get_texture()
	view.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	view.size = Vector2(W * 3, H * 3)
	view.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(view)
	_run.call_deferred()


func _run() -> void:
	var res := {}
	for side in ["left", "right"]:
		# the lamp sits far to one side at the characters' chest height -> light direction ~horizontal
		light.position = Vector2(-120.0 if side == "left" else W + 120.0, 78)
		for i in 6:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		res[side] = img
		if out_dir != "":
			DirAccess.make_dir_recursive_absolute(out_dir)
			img.save_png(out_dir.path_join("light_%s.png" % side))
			var big := img.duplicate()
			big.resize(W * 6, H * 6, Image.INTERPOLATE_NEAREST)
			big.save_png(out_dir.path_join("light_%s_6x.png" % side))
	for e in rigs:
		var r: Node2D = e["rig"]
		var x0 := int(r.position.x) - 9
		var bl := _halves(res["left"], x0)
		var br := _halves(res["right"], x0)
		# lamp on the left must brighten the left half more than the lamp on the right does, and vice versa
		var ok: bool = bl.x > br.x and br.y > bl.y
		var tag := "%s facing %s" % [e["id"], "left " if e["left"] else "right"]
		print("%-24s lampL: L=%.3f R=%.3f | lampR: L=%.3f R=%.3f -> %s" % [tag, bl.x, bl.y, br.x, br.y, "PASS" if ok else "FAIL"])
		if not ok:
			fails += 1
	print("CHAR_LIGHT_TEST ", "PASS" if fails == 0 else "FAIL (%d)" % fails)
	get_tree().quit(0 if fails == 0 else 1)


## Mean luminance of the sprite's left and right halves (columns x0..x0+8 and x0+10..x0+18, rows 54..100).
func _halves(img: Image, x0: int) -> Vector2:
	var sums := Vector2.ZERO
	var cnt := Vector2.ZERO
	var bgc := Color(0.55, 0.55, 0.55) * Color(0.32, 0.32, 0.34)
	for y in range(54, 100):
		for dx in range(0, 18):
			var x := x0 + dx
			if x < 0 or x >= img.get_width():
				continue
			var c := img.get_pixel(x, y)
			if absf(c.r - bgc.r) < 0.02 and absf(c.g - bgc.g) < 0.02 and absf(c.b - bgc.b) < 0.02:
				continue     # background
			var l := c.get_luminance()
			if dx < 9:
				sums.x += l
				cnt.x += 1
			else:
				sums.y += l
				cnt.y += 1
	return Vector2(sums.x / maxf(1.0, cnt.x), sums.y / maxf(1.0, cnt.y))
