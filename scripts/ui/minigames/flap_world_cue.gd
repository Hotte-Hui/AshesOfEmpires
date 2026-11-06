extends Sprite2D
## World cue of the Chapter-3 mini-game "Die Fallblatttafel" (L_C3_Station, bolted to canopy column 3 above
## exp_flap_board): the arrivals board with its jammed top row (frames 0/1: a stuck card twitches now and then)
## until Alexei has restored the line (Explore find veltrava.station.flap_board) — then frame 2, 8:41 MOSKVA
## KARSK 5. Polls twice a second, never touches Story. Art: assets/ui/minigames/flap/world_flap_board.png.

@export var explore_id := "veltrava.station.flap_board"
var _t := 0.0
var _poll := 0.0
var _fixed := false


func _ready() -> void:
	hframes = 3
	_sync()


func _process(delta: float) -> void:
	_t += delta
	_poll -= delta
	if _poll <= 0.0:
		_poll = 0.5
		_sync()
	if not _fixed:
		frame = 1 if fmod(_t, 2.9) > 2.65 else 0


func _sync() -> void:
	var ex := get_node_or_null("/root/Explore")
	_fixed = ex != null and ex.has_method("is_found") and bool(ex.is_found(explore_id))
	if _fixed:
		frame = 2
