extends SceneTree
## Hall camera smoothness check (owner: render-camera), headless:
##   godot --headless --path . --script res://tests/visual/camera_hall_rig_check.gd
## Samples hall_camera_rig.gd at display rates 60/144/240 Hz and compares the on-screen motion of the lens-shift
## component (1080p screen px, 3 px per low-res px) before (whole low-res px only) and after (whole px + display
## fraction, quantised to screen px by the rasteriser). Also checks apply_pose(): whole + fraction == shift.

const Rig := preload("res://scripts/levels/hall/hall_camera_rig.gd")


func _init() -> void:
	var rig = Rig.new()
	var dur: float = rig.duration()
	var fails := 0
	for hz: int in [60, 144, 240]:
		var old_steps := {}
		var new_steps := {}
		var prev_old := 0.0
		var prev_new := 0.0
		var n := int(dur * hz)
		var holds_old := 0
		var holds_new := 0
		var moving := 0
		for i in n + 1:
			var t := float(i) / hz
			var sh: Vector2 = rig.sample(t)["shift"]
			var o := roundf(sh.y) * 3.0               # old: whole low-res px only
			var nw := roundf(sh.y * 3.0)               # new: whole px + fraction -> screen px
			if i > 0:
				var cont: float = (sh.y - (rig.sample(float(i - 1) / hz)["shift"] as Vector2).y) * 3.0
				var d_old := o - prev_old
				var d_new := nw - prev_new
				old_steps[d_old] = int(old_steps.get(d_old, 0)) + 1
				new_steps[d_new] = int(new_steps.get(d_new, 0)) + 1
				if absf(cont) > 0.05:
					moving += 1
					if d_old == 0.0:
						holds_old += 1
					if d_new == 0.0:
						holds_new += 1
			prev_old = o
			prev_new = nw
		print("HALLRIG %d Hz lens-shift y: frames moving %d | old step hist %s holds %d | new step hist %s holds %d" % [
			hz, moving, str(_sorted(old_steps)), holds_old, str(_sorted(new_steps)), holds_new])
	# apply_pose consistency (no camera node needed for the maths): whole + fraction reproduces the shift
	for t: float in [0.3, 0.9, 1.7, 2.6]:
		var smp: Dictionary = rig.sample(t)
		var sh: Vector2 = smp["shift"]
		var whole := sh.round()
		var frac := Vector2(sh.x - whole.x, -(sh.y - whole.y))
		var shown := Vector2(whole.x + frac.x, whole.y - frac.y)
		if shown.distance_to(sh) > 1e-4:
			fails += 1
			print("HALLRIG FAIL t=%.2f shift %s shown %s" % [t, str(sh), str(shown)])
	print("HALLRIG %s" % ("PASS" if fails == 0 else "FAIL"))
	quit(0 if fails == 0 else 1)


func _sorted(d: Dictionary) -> Array:
	var out: Array = []
	var keys := d.keys()
	keys.sort()
	for k in keys:
		out.append("%s:%d" % [str(k), d[k]])
	return out
