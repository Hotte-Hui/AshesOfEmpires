extends Node
## Structural check of layer_stack.gd round-2 features (owner: render-camera): Symbols.pick() for layers, props
## and decals (incl. `_hist_n` maps), decal placement on a layer / on the playfield / with own parallax, layer
## blend "add", per-texel materials. Runs headless (no rendering needed):
##   godot --headless --path . res://tests/visual/camera_decals.tscn -- --symbols=1 --decal-dir=<abs dir>
##   godot --headless --path . res://tests/visual/camera_decals.tscn -- --symbols=0 --decal-dir=<abs dir>
## <abs dir> holds the test PNGs (layer, decal(+_hist,+_n,+_hist_n), prop(+_hist), flag). Exit code 0 = pass.

const LayerStack := preload("res://scripts/levels/layer_stack.gd")

var fails: PackedStringArray = []


func _ready() -> void:
	var dir := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--decal-dir="):
			dir = a.get_slice("=", 1)
	var hist := Symbols.enabled()
	var m := {
		"world_size": [640, 360],
		"layers": [
			{"name": "far", "file": "layer.png", "pos": [10, 20], "parallax": [0.5, 0.0], "z": -50, "normal": true},
			{"name": "glow", "file": "layer.png", "pos": [0, 0], "parallax": [1, 1], "z": 5, "lit": false,
			 "blend": "add", "alpha": 0.5},
		],
		"props": [{"name": "crate", "file": "prop.png", "pos": [100, 200], "base_y": 216}],
		"decals": [
			{"name": "on_far", "file": "decal.png", "pos": [30, 40], "layer": "far", "z": 1},
			{"name": "on_play", "file": "decal.png", "pos": [300, 250], "layer": "playfield", "base_y": 262},
			{"name": "free", "file": "decal.png", "pos": [500, 60], "parallax": [0.25, 0.0], "z": -40},
			{"name": "flag", "file": "flag.png", "pos": [50, 50], "frames": 4, "fps": 6, "lit": false},
		],
	}
	var root := Node2D.new()
	add_child(root)
	var stack: Node2D = LayerStack.new()
	root.add_child(stack)
	var playfield := Node2D.new()
	playfield.y_sort_enabled = true
	root.add_child(playfield)
	var lights := Node2D.new()
	root.add_child(lights)
	var fx := Node2D.new()
	root.add_child(fx)
	stack.build(m, dir, playfield, lights, fx)
	# --- symbols on decals (diffuse + normal) and props
	var on_far: Node2D = stack.decals_by_name.get("on_far")
	_check(on_far != null, "decal on_far built")
	if on_far:
		var spr := on_far.get_child(0) as Sprite2D
		var t := spr.texture as CanvasTexture
		_check(t != null, "decal has CanvasTexture (normal map found)")
		if t:
			var c := t.diffuse_texture.get_image().get_pixel(0, 0)
			_check((c.g > 0.5) == hist, "decal diffuse is %s variant (got %s)" % ["_hist" if hist else "neutral", str(c)])
			var n := t.normal_texture.get_image().get_pixel(0, 0)
			var hist_n := absf(n.r - 120.0 / 255.0) < 0.01
			_check(hist_n == hist, "decal normal map is %s (got %s)" % ["_hist_n" if hist else "_n", str(n)])
		# placement: child of the 'far' layer holder, local = pos - layer home
		var far: Node2D = stack.layers_by_name.get("far")
		_check(on_far.get_parent() == far, "decal on_far is a child of layer 'far'")
		_check(on_far.position == Vector2(20, 20), "decal on_far local position %s == (20, 20)" % str(on_far.position))
		_check(on_far.z_index == 1, "decal z relative to layer")
	var on_play: Node2D = stack.decals_by_name.get("on_play")
	_check(on_play != null and on_play.get_parent() == playfield, "decal on_play in the y-sorted playfield")
	if on_play:
		_check(on_play.position == Vector2(300, 262), "decal on_play sort position %s" % str(on_play.position))
		var sp := on_play.get_child(0) as Sprite2D
		_check(sp.offset == Vector2(0, -12), "decal on_play sprite offset %s" % str(sp.offset))
	var free: Node2D = stack.decals_by_name.get("free")
	_check(free != null and free.get_parent().get_parent() == stack, "free decal has its own parallax holder")
	var found := false
	for e in stack._parallax:
		if e["node"] == (free.get_parent() if free else null):
			found = e["parallax"] == Vector2(0.25, 0.0)
	_check(found, "free decal registered with parallax (0.25, 0)")
	var flag: Node2D = stack.decals_by_name.get("flag")
	_check(flag != null and (flag.get_child(0) as Sprite2D).hframes == 4, "animated decal has 4 frames")
	_check(flag != null and (flag.get_child(0) as Sprite2D).light_mask == 0, "unlit decal")
	var crate := playfield.get_node_or_null("crate") as Node2D
	_check(crate != null, "prop built")
	if crate:
		var pt := (crate.get_child(0) as Sprite2D).texture
		var d := (pt as CanvasTexture).diffuse_texture if pt is CanvasTexture else pt
		var pc := d.get_image().get_pixel(0, 0)
		_check((pc.r > 0.9 and pc.g > 0.9) == hist, "prop is %s variant" % ["_hist" if hist else "neutral"])
	# --- layer blend add + alpha
	var glow: Node2D = stack.layers_by_name.get("glow")
	_check(glow != null and glow.modulate.a == 0.5, "layer alpha 0.5")
	if glow:
		var gm := (glow.get_child(0) as Sprite2D).material as CanvasItemMaterial
		_check(gm != null and gm.blend_mode == CanvasItemMaterial.BLEND_MODE_ADD, "layer blend add")
	# --- materials: opaque lit layer -> coded pixel material
	var farl: Node2D = stack.layers_by_name.get("far")
	if farl:
		var fm := (farl.get_child(0) as Sprite2D).material as ShaderMaterial
		_check(fm != null and fm.shader.resource_path.ends_with("pixel_sprite.gdshader"), "opaque layer uses pixel_sprite material")
	for f in fails:
		print("DECALS FAIL: ", f)
	print("DECALS symbols=%s: %s (%d checks failed)" % [hist, "PASS" if fails.is_empty() else "FAIL", fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)


func _check(ok: bool, what: String) -> void:
	if not ok:
		fails.append(what)
