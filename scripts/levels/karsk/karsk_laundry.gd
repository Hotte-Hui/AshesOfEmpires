extends "res://scripts/levels/karsk/karsk_actor.gd"
## Laundry on the barrack's line (near background, parallax 0.72): six pieces sway gently, each with its own
## phase, and blow out sideways and flutter when a gust comes (KarskWind.gust).
## Each item strip has 4 frames: 0 hanging, 1/2 blown right, 3 flapping back; it hangs from x=1, y=0.

const Wind := preload("res://scripts/levels/karsk/karsk_wind.gd")

var items: Array = []           ## [{file, cell: [w, h]}]
var pegs: Array = []            ## [[x, y], ...] layer coordinates at camera x 0

var _spr: Array = []
var _phase: Array = []


func _setup() -> void:
	for i in mini(items.size(), pegs.size()):
		var it: Dictionary = items[i]
		var tex := canvas_tex(str(it.get("file", "")), true)
		if tex == null:
			continue
		var s := make_strip(tex, 4)
		s.position = Vector2(float(pegs[i][0]) - 1.0, float(pegs[i][1])) - home
		_spr.append(s)
		_phase.append(float(i) * 1.37)


func _tick(_delta: float) -> void:
	var t: float = Wind.t_global
	var g: float = Wind.gust
	var rm := reduced_motion()
	for i in _spr.size():
		var s: Sprite2D = _spr[i]
		var ph: float = _phase[i]
		var f := 0
		if g > 0.3 and not rm:
			f = [1, 2, 2, 3][int(t * (7.0 + g * 5.0) + ph * 3.0) % 4]
		elif g > 0.12:
			f = 1 if sin(t * 3.0 + ph) > -0.2 else 0
		else:
			var sway := sin(t * 0.9 + ph) + 0.6 * sin(t * 2.3 + ph * 1.7)
			f = 1 if sway > 1.15 else (3 if sway < -1.35 else 0)
		s.frame = f
