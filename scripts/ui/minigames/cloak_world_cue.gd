extends Sprite2D
## World cue of the Chapter-3 mini-game "Die Garderobe" (L_C3_Hall): Herr Wenzel, garderobier since 1927, behind
## the cloakroom counter next to exp_cloak_tokens — polishing a brass hook plate, blinking now and then, lifting
## the plate to the light every few seconds. Decoration only: the interaction is the discover hotspot beside him;
## never touches Story or Explore. Art: assets/ui/minigames/cloak/world_wenzel.png (3 frames, 20x30).

var _t := 0.0


func _ready() -> void:
	hframes = 3


func _process(delta: float) -> void:
	_t += delta
	var c := fmod(_t, 7.3)
	if c > 6.0:
		frame = 2
	elif fmod(_t, 3.1) > 2.95:
		frame = 1
	else:
		frame = 0
