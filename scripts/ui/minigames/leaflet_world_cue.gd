extends Sprite2D
## World cue of the plaza mini-game "Das Blatt im Schnee" (L_M1_Plaza, beside exp_pz_leaflet): the typed sheet
## lies in the snow and lifts a corner now and then (world_leaflet.png, 2 frames) until Konrad has picked it up
## (Explore find plaza.leaflet); then it is gone. Polls twice a second, never touches Story.

@export var explore_id := "plaza.leaflet"
var _t := 0.0
var _poll := 0.0


func _ready() -> void:
	hframes = 2
	_sync()


func _process(delta: float) -> void:
	_t += delta
	frame = 1 if fmod(_t, 3.7) > 3.1 else 0
	_poll -= delta
	if _poll <= 0.0:
		_poll = 0.5
		_sync()


func _sync() -> void:
	var ex := get_node_or_null("/root/Explore")
	visible = not (ex != null and ex.has_method("is_found") and bool(ex.is_found(explore_id)))
