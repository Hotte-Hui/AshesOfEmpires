extends Sprite2D
## World prop of the mini-game "Das Relaispult" (L_C3_Hall, beside exp_relay_desk): the commission technician's desk
## in the interpreters' corridor (assets/ui/minigames/relay/world_desk.png, 4 lamp frames, with _n normal map and
## _e emission like the hall props). While the session runs (after c3b_arrival, before c3b_inspect_booth, or in a
## memory) the channel diodes flicker and the yellow lamp lights now and then; afterwards the desk rests. Feet at
## the node position (bottom centre). Polls Story twice a second, never changes it.

const TexelLightLib := preload("res://scripts/render/texel_light.gd")
const ART := "res://assets/ui/minigames/relay/"
const FRAMES := 4

var _t := 0.0
var _poll := 0.0
var _live := false
var _glow: Sprite2D


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var base: Texture2D = texture if texture != null else _load(ART + "world_desk.png")
	var n := _load(ART + "world_desk_n.png")
	if base != null and n != null:
		var ct := CanvasTexture.new()
		ct.diffuse_texture = base
		ct.normal_texture = n
		texture = ct
	elif base != null:
		texture = base
	hframes = FRAMES
	centered = true
	if texture != null:
		offset = Vector2(0, -roundf(texture.get_height() / 2.0))
	TexelLightLib.apply(self, position - Vector2(texture.get_width() / FRAMES / 2.0, texture.get_height()) if texture else position,
		Vector2(texture.get_width() / FRAMES, texture.get_height()) if texture else Vector2.ZERO)
	var e := _load(ART + "world_desk_e.png")
	if e != null:
		_glow = Sprite2D.new()
		_glow.texture = e
		_glow.hframes = FRAMES
		_glow.centered = true
		_glow.offset = offset
		_glow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_glow.light_mask = 0
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		_glow.material = mat
		_glow.modulate = Color(1, 1, 1, 0.55)
		add_child(_glow)
	_sync()


func _load(path: String) -> Texture2D:
	return load(path) as Texture2D if ResourceLoader.exists(path) else null


func _process(delta: float) -> void:
	_t += delta
	_poll -= delta
	if _poll <= 0.0:
		_poll = 0.5
		_sync()
	var f := 0
	if _live:
		var c := fmod(_t, 7.3)
		f = 2 if fmod(_t, 0.9) < 0.45 else 0
		if c > 5.6 and c < 6.8:
			f = 3 if f == 2 else 1          # the yellow lamp: a speaker is asked to slow down
	frame = f
	if _glow:
		_glow.frame = f


func _sync() -> void:
	var g := get_node_or_null("/root/Game")
	var mm = g.get("memory_mode") if g != null else null
	if mm is bool and mm:
		_live = true
		return
	var st := get_node_or_null("/root/Story")
	if st == null or not st.has_method("objective_state"):
		_live = false
		return
	_live = str(st.objective_state("c3b_arrival")) == "complete" and str(st.objective_state("c3b_inspect_booth")) != "complete"
