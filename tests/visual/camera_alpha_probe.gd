extends Node
## Engine probe (owner: render-camera): does framebuffer alpha written by a blend_disabled canvas_item shader
## survive into hint_screen_texture of a later full-screen ColorRect? Tested per transparent_bg and with a
## PointLight2D present. Prints the alpha the post sees under the sprite.
##   godot --path . res://tests/visual/camera_alpha_probe.tscn

const SPR := """shader_type canvas_item;
render_mode blend_disabled;
void fragment() { COLOR.a = 0.4; }
"""
const POST := """shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
void fragment() { vec4 s = texture(screen_tex, SCREEN_UV); COLOR = vec4(s.a, s.a, s.a, 1.0); }
"""


func _ready() -> void:
	_run.call_deferred()


func _case(transparent: bool, with_light: bool, with_layer: bool) -> String:
	var vp := SubViewport.new()
	vp.size = Vector2i(64, 64)
	vp.transparent_bg = transparent
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var img := Image.create(16, 16, false, Image.FORMAT_RGBA8)
	img.fill(Color(1, 1, 1, 1))
	var spr := Sprite2D.new()
	spr.texture = ImageTexture.create_from_image(img)
	spr.centered = false
	spr.position = Vector2(8, 8)
	var sm := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = SPR
	sm.shader = sh
	spr.material = sm
	vp.add_child(spr)
	if with_light:
		var l := PointLight2D.new()
		var g := GradientTexture2D.new()
		g.fill = GradientTexture2D.FILL_RADIAL
		l.texture = g
		l.position = Vector2(16, 16)
		vp.add_child(l)
	var post_parent: Node = vp
	if with_layer and transparent and with_light:
		# variant: no post at all -> read the render target alpha directly
		for i in 4:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var im0 := vp.get_texture().get_image()
		var r0 := "RAW target alpha inside %.3f outside %.3f" % [im0.get_pixel(12, 12).a, im0.get_pixel(40, 40).a]
		vp.queue_free()
		return r0
	if with_layer:
		var cl := CanvasLayer.new()
		cl.layer = 100
		vp.add_child(cl)
		post_parent = cl
	var cr := ColorRect.new()
	cr.size = Vector2(64, 64)
	var pm := ShaderMaterial.new()
	var ps := Shader.new()
	ps.code = POST
	pm.shader = ps
	cr.material = pm
	post_parent.add_child(cr)
	for i in 4:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var im := vp.get_texture().get_image()
	var res := "inside %.3f outside %.3f" % [im.get_pixel(12, 12).r, im.get_pixel(40, 40).r]
	vp.queue_free()
	return res


func _run() -> void:
	for tr in [false, true]:
		for li in [false, true]:
			for la in [false, true]:
				print("APROBE transparent_bg=%s light=%s post_on_canvaslayer=%s -> %s" % [tr, li, la, await _case(tr, li, la)])
	get_tree().quit()
