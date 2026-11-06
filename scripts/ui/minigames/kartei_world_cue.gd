extends Sprite2D
## World cue of the mini-game "Die Suchkartei" (L_C3_Registry, card hall, in front of the cabinets beside drawer
## C-17, exp_kartei): the fallen drawer and its scattered cards (frame 0) until Konrad has filed them (Explore find
## veltrava.registry.kartei) -- then frame 1 (empty: the drawer is back in its cabinet). Polls twice a second, never
## touches Story. Art: assets/ui/minigames/kartei/world_drawer.png (tools/pixelgen/gen_mg_c3p2_kartei.py).

@export var explore_id := "veltrava.registry.kartei"
var _poll := 0.0
var restored := false


func _ready() -> void:
	hframes = 2
	_sync()


func _process(delta: float) -> void:
	_poll -= delta
	if _poll <= 0.0:
		_poll = 0.5
		_sync()


func _sync() -> void:
	var ex := get_node_or_null("/root/Explore")
	restored = ex != null and ex.has_method("is_found") and bool(ex.is_found(explore_id))
	frame = 1 if restored else 0
