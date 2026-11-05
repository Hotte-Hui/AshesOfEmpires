extends "res://scripts/levels/karsk/karsk_actor.gd"
## The parade on the avenue behind the barrier (L_M1_Plaza, owner plaza-env, TECHNICAL_ARCHITECTURE §12.2
## "actors"): an endless procession moving left -> right in step — standard bearers, blocks of anonymous
## helmeted troops (4 ranks x 9 files), tanks in between, pauses. Drawn between the ground layer (z -16) and the
## guards/barrier layer (z -14): props.z = -15. Sheets from tools/pixelgen/env_plaza_sprites.py; the standard's
## cloth is an insignia site and is resolved through Symbols.pick (§12.4).
## Sound: the distant drum/boots loop (Audio.sfx_loop "plaza_march_loop", its level follows the nearest block)
## and a tank rumble (plaza_tank_pass) when a tank comes on screen. Never touches Story / Explore state.

var block := ""
var standard := ""
var tank := ""
var puff := ""
var feet_y := 220.0                      ## world y of the front rank's feet
var speed := 20.0                        ## world px / s
var span: Array = [-260.0, 2240.0]       ## x range the procession wraps through (beyond the visible world)
var march_fps := 7.0                     ## 8-frame step cycle, all blocks in step
## S = standard bearer, B = marching block, T = tank, number = gap in px. Repeated twice around the loop.
var pattern: Array = ["S", "B", "B", "B", 60, "T", 36, "T", 90, "S", "B", "B", 150]
var loop_id := "plaza_march_loop"
var tank_sfx := "plaza_tank_pass"

const LOOP_KEY := "plaza_march"
var _items: Array = []                   # {node, off, kind, w, h, frames, seen}
var _len := 2500.0
var _t := 0.0
var _vol := -60.0
var _vol_sent := -99.0
var _vol_t := 0.0
var _puff_tex: Texture2D
var _puff_t := 0.0


func _setup() -> void:
	var tex := {"B": load_tex(Symbols.pick(block)), "S": load_tex(Symbols.pick(standard)),
		"T": load_tex(Symbols.pick(tank))}
	_puff_tex = load_tex(puff)
	var x := 0.0
	for _rep in 2:
		for p in pattern:
			if p is String:
				var t: Texture2D = tex.get(p)
				if t == null:
					continue
				var fr := 4 if p == "T" else 8
				var s := make_strip(t, fr, true)
				var w := t.get_width() / float(fr)
				_items.append({"node": s, "off": x, "kind": p, "w": w, "h": float(t.get_height()),
					"frames": fr, "seen": false})
				x += w + (4.0 if p == "S" else 10.0)
			else:
				x += float(p)
	_len = maxf(x, float(span[1]) - float(span[0]))
	_t = 37.0                            # start mid-procession: something is always passing at level start
	_place()


func _tick(delta: float) -> void:
	_t += delta
	_place()
	_update_sound(delta)


func _place() -> void:
	var frame_m := int(_t * march_fps) % 8
	var frame_t := int(_t * speed) % 4
	var cam := cam_pos()
	var x0 := float(span[0])
	_puff_t -= get_process_delta_time()
	for it in _items:
		var s: Sprite2D = it["node"]
		var x := x0 + fposmod(float(it["off"]) + _t * speed, _len)
		var y := feet_y - float(it["h"]) + (2.0 if it["kind"] == "T" else 0.0)
		s.position = Vector2(x, y).round()
		s.frame = frame_t if it["kind"] == "T" else frame_m
		if it["kind"] == "T":
			var vis := x + float(it["w"]) > cam.x - 30.0 and x < cam.x + 670.0
			if vis and not it["seen"]:
				sfx(tank_sfx, dist_db(Vector2(x + 40.0, feet_y), -10.0, -24.0, 500.0), 0.04)
			it["seen"] = vis
			if vis and _puff_t <= 0.0 and _puff_tex != null:
				spawn_puff(_puff_tex, 6, s.position + Vector2(2, 15), Vector2(-7, -6), 1.6)
	if _puff_t <= 0.0:
		_puff_t = 0.4


## The loop's level follows the nearest marching unit (screen-centre distance); updated in 1-dB steps so the
## Audio fader is not restarted every frame.
func _update_sound(delta: float) -> void:
	var c := cam_pos().x + 320.0
	var d := 99999.0
	for it in _items:
		if it["kind"] == "T":
			continue
		var x := float(span[0]) + fposmod(float(it["off"]) + _t * speed, _len) + float(it["w"]) * 0.5
		d = minf(d, absf(x - c))
	var target := lerpf(-9.0, -26.0, clampf(d / 900.0, 0.0, 1.0))
	_vol = lerpf(_vol, target, clampf(delta * 1.5, 0.0, 1.0)) if _vol > -59.0 else target
	_vol_t -= delta
	if _vol_t <= 0.0 and absf(_vol - _vol_sent) >= 1.0:
		_vol_t = 0.25
		_vol_sent = _vol
		var a := get_node_or_null("/root/Audio")
		if a != null and a.has_method("sfx_loop"):
			a.sfx_loop(loop_id, LOOP_KEY, _vol, 0.6)


func _exit_tree() -> void:
	var a := get_node_or_null("/root/Audio")
	if a != null and a.has_method("stop_sfx_loop"):
		a.stop_sfx_loop(LOOP_KEY, 1.2)
