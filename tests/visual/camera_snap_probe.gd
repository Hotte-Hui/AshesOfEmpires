extends Node
## Engine probe (owner: render-camera): where does Godot put a nearest-filtered sprite at sub-pixel positions
## inside a zoomed SubViewport, for each combination of snap_2d_transforms_to_pixel / snap_2d_vertices_to_pixel
## and with / without a y-sorted parent?  Prints the left edge (viewport px) for x = 100 + i/6.
##   godot --path . res://tests/visual/camera_snap_probe.tscn

var vp: SubViewport
var cam: Camera2D
var holder: Node2D
var spr: Sprite2D


func _ready() -> void:
	vp = SubViewport.new()
	vp.size = Vector2i(642 * 3, 362 * 3)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(vp)
	cam = Camera2D.new()
	cam.anchor_mode = Camera2D.ANCHOR_MODE_FIXED_TOP_LEFT
	cam.zoom = Vector2(3, 3)
	vp.add_child(cam)
	cam.make_current()
	holder = Node2D.new()
	vp.add_child(holder)
	var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	img.fill(Color(1, 1, 1, 1))
	spr = Sprite2D.new()
	spr.texture = ImageTexture.create_from_image(img)
	spr.centered = false
	holder.add_child(spr)
	_run.call_deferred()


func _edge() -> int:
	await RenderingServer.frame_post_draw
	var im := vp.get_texture().get_image()
	for x in im.get_width():
		if im.get_pixel(x, 30).r > 0.5:
			return x
	return -1


func _run() -> void:
	for ysort in [false, true]:
		holder.y_sort_enabled = ysort
		for tsnap in [false, true]:
			for vsnap in [false, true]:
				vp.snap_2d_transforms_to_pixel = tsnap
				vp.snap_2d_vertices_to_pixel = vsnap
				for camx in [0.0, 0.3333333]:
					cam.position = Vector2(camx, 0)
					var out: Array = []
					for i in 13:
						spr.position = Vector2(100.0 + i / 6.0, 5.0)
						for j in 2:
							await get_tree().process_frame
						out.append(await _edge())
					print("PROBE ysort=%s tsnap=%s vsnap=%s cam=%.3f edges=%s" % [ysort, tsnap, vsnap, camx, str(out)])
	get_tree().quit()
