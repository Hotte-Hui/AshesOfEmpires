extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## Flashback film of one real-history card (TECHNICAL_ARCHITECTURE §12.15) — the script of the four scenes
## scenes/cinematics/flashback_<name>/Flashback<Name>.tscn; each scene only sets `film_id`.
## Owner: flashback stream.  A §12.5 scene on the common runtime (finished exactly once, idempotent skip(),
## configure / play / seek / advance, reduced motion); every frame is a pure function of the timeline.
##   sheet    data/flashbacks/flashbacks.json: the shots in order with their seconds, the place-and-date caption
##            (first shot) and at most one line for each later shot, the lamp windows of the Nuremberg desk
##   art      assets/cinematics/flashback/ (tools/pixelgen/env_flashback.py): one painted 512 x 368 plate per shot
##            in a 13-step sepia ramp, layout.json with the drift anchors
##   picture  an old 4:3 gate (480 x 360 world px, black pillars left and right); each shot drifts slowly across
##            its plate in single screen pixels, dips through black in four hard steps at both ends, and wears the
##            film: a gate weave of whole pixels, a faint flicker, one light and one dark scratch, dust — all
##            hard-edged, nothing blurred. Reduced motion: half the drift, no weave, no flicker, no scratches.
##   words    caption_state() tells the presenter (scripts/ui/flashback_view.gd) what to show at time t; the same
##            keys are `say` cues, so a run through the game director would use the ordinary subtitle box.
## Nothing here touches the Story: the film has no flags, no choices and no cue that plays through Audio.

const Flashbacks := preload("res://scripts/core/flashbacks.gd")
const FB_ASSETS := "res://assets/cinematics/flashback/"
const GATE := Rect2(80, 0, 480, 360)
const DIP := 0.4                 # seconds of the dip through black at each end of a shot
const DIP_STEPS := 4.0           # ... in this many hard steps
const WEAVE_HZ := 4.0            # the gate weave may jump this often, by whole world pixels
const FLICKER_HZ := 12.0
const SNAP := 3.0                # drift positions snap to 1/3 world px (one screen pixel at x3)
const PLACE_IN := 0.5            # the place-and-date caption appears this long after the first shot starts
const LINE_IN := 0.35            # a line appears this long after its shot starts
const TEXT_OUT := 0.3            # ... and is gone this long before the shot ends
const TEXT_RAMP := 0.25

## The film to show (id in data/flashbacks/flashbacks.json).
@export var film_id := ""

var sheet: Dictionary = {}
## [{id, t0, t1, line, sprite, from, to, overlays: [{id, sprite, on: [[a, b]]}]}]
var shots: Array = []
var place_key := ""

var _pictures: Node2D
var _cover: Polygon2D
var _scratches: Array = []
var _dust: Array = []


func _build() -> void:
	grade_preset = ""
	sheet = Flashbacks.film(film_id)
	var lay: Dictionary = Flashbacks.layout()
	var geo_all: Dictionary = {}
	var lfs = lay.get("films", {})
	if lfs is Dictionary and lfs.get(str(sheet.get("key", ""))) is Dictionary:
		var lf: Dictionary = lfs[str(sheet["key"])]
		if lf.get("shots") is Dictionary:
			geo_all = lf["shots"]
	_pictures = group("Pictures")
	var t0 := 0.0
	for s in sheet.get("shots", []):
		if not (s is Dictionary):
			continue
		var sid := str(s.get("id", ""))
		var geo: Dictionary = geo_all[sid] if geo_all.get(sid) is Dictionary else {}
		var sp := _fb_sprite(str(geo.get("tex", "")), _pictures)
		sp.visible = false
		var shot := {"id": sid, "t0": t0, "t1": t0 + maxf(0.1, float(s.get("dur", 5.0))), "line": str(s.get("line", "")),
			"sprite": sp, "from": _v2(geo.get("from")), "to": _v2(geo.get("to")), "overlays": []}
		var on: Dictionary = s["on"] if s.get("on") is Dictionary else {}
		for o in geo.get("overlays", []):
			if not (o is Dictionary):
				continue
			var ov := _fb_sprite(str(o.get("tex", "")), sp)       # a child of the plate: it drifts with it
			ov.position = _v2(o.get("pos"))
			ov.visible = false
			var oid := str(o.get("id", ""))
			(shot["overlays"] as Array).append({"id": oid, "sprite": ov, "on": on[oid] if on.get(oid) is Array else []})
		shots.append(shot)
		t0 = float(shot["t1"])
	duration = maxf(t0, 0.1)
	max_duration = duration + 4.0
	place_key = str(sheet.get("place", ""))
	var look: Dictionary = lay["look"] if lay.get("look") is Dictionary else {}
	var wear := group("Wear")
	for rel in look.get("scratches", []):
		var sc := _fb_sprite(str(rel), wear)
		sc.visible = false
		_scratches.append(sc)
	for i in 3:
		var d := _fb_sprite(str(look.get("dust", "")), wear)
		d.hframes = maxi(1, int(look.get("dust_frames", 1)))
		d.visible = false
		_dust.append(d)
	_cover = _rect(GATE, Color(0, 0, 0, 0))                      # the dip through black
	var gate := _fb_sprite(str(look.get("gate", "")), self)
	gate.position = GATE.position
	_rect(Rect2(-8, -8, GATE.position.x + 8, 376), Color.BLACK)   # the pillars beside the 4:3 gate
	_rect(Rect2(GATE.end.x, -8, 648 - GATE.end.x, 376), Color.BLACK)
	_rect(Rect2(-8, -8, 656, 8), Color.BLACK)                    # the plates are taller than the gate
	_rect(Rect2(-8, 360, 656, 8), Color.BLACK)
	if _configured:                                              # configured before the scene entered the tree
		_cues = _make_cues()
		_cues.sort_custom(func(a, b): return float(a["t"]) < float(b["t"]))


func _make_cues() -> Array:
	var cues: Array = []
	if shots.is_empty():
		return cues
	if place_key != "":
		var w := place_window()
		cues.append({"t": w.x, "say": place_key, "dur": w.y - w.x})
	for i in shots.size():
		if str(shots[i]["line"]) != "":
			var lw := line_window(i)
			cues.append({"t": lw.x, "say": str(shots[i]["line"]), "dur": lw.y - lw.x})
	return cues


## Caption keys in the order they appear: the place-and-date caption, then the lines.
func chosen_lines() -> Array:
	var out: Array = []
	if place_key != "":
		out.append(place_key)
	for sh in shots:
		if str(sh["line"]) != "":
			out.append(str(sh["line"]))
	return out


func get_shot_id() -> String:
	return str(shots[shot_index(t)]["id"]) if not shots.is_empty() else ""


## Index of the shot on screen at `time`.
func shot_index(time: float) -> int:
	var cur := 0
	for i in shots.size():
		if time >= float(shots[i]["t0"]):
			cur = i
	return cur


## Seconds (from, to) the place-and-date caption is on screen: within the first shot.
func place_window() -> Vector2:
	if shots.is_empty():
		return Vector2.ZERO
	return Vector2(float(shots[0]["t0"]) + PLACE_IN, float(shots[0]["t1"]) - TEXT_OUT)


## Seconds (from, to) the line of shot `i` is on screen.
func line_window(i: int) -> Vector2:
	return Vector2(float(shots[i]["t0"]) + LINE_IN, float(shots[i]["t1"]) - TEXT_OUT)


## What the presenter shows at `time` (default: now): {place, place_a, line, line_a} — keys and their opacity.
func caption_state(time := -1.0) -> Dictionary:
	var tt := t if time < 0.0 else time
	var out := {"place": "", "place_a": 0.0, "line": "", "line_a": 0.0}
	if shots.is_empty():
		return out
	if place_key != "":
		out["place"] = place_key
		out["place_a"] = _text_alpha(tt, place_window())
	var i := shot_index(tt)
	if str(shots[i]["line"]) != "":
		out["line"] = str(shots[i]["line"])
		out["line_a"] = _text_alpha(tt, line_window(i))
	return out


## Top-left of the gate on the plate of shot `i` at progress u (0..1), in plate pixels, snapped to screen pixels.
func drift(i: int, u: float, rm: bool) -> Vector2:
	var from: Vector2 = shots[i]["from"]
	var to: Vector2 = shots[i]["to"]
	if rm:
		to = from.lerp(to, 0.5)
	return (from.lerp(to, clampf(u, 0.0, 1.0)) * SNAP).round() / SNAP


## The gate weave at `time`: whole world pixels, mostly none.
func weave(time: float) -> Vector2:
	var k := floori(time * WEAVE_HZ)
	var hx := _h(k, 23)
	var hy := _h(k, 11)
	return Vector2(1.0 if hx > 0.93 else (-1.0 if hx < -0.93 else 0.0), 1.0 if hy > 0.8 else (-1.0 if hy < -0.8 else 0.0))


func _apply(time: float) -> void:
	if shots.is_empty():
		return
	var rm := reduced_motion()
	var cur := shot_index(time)
	for i in shots.size():
		var sh: Dictionary = shots[i]
		var sp: Sprite2D = sh["sprite"]
		sp.visible = i == cur
		if i != cur:
			continue
		var t0 := float(sh["t0"])
		var t1 := float(sh["t1"])
		sp.position = GATE.position - drift(i, (time - t0) / (t1 - t0), rm) + (Vector2.ZERO if rm else weave(time))
		for o in sh["overlays"]:
			(o["sprite"] as Sprite2D).visible = _within(time - t0, o["on"])
		var edge := minf(time - t0, t1 - time)
		_cover.color.a = ceilf(clampf(1.0 - edge / DIP, 0.0, 1.0) * DIP_STEPS) / DIP_STEPS
	var k := 1.0 if rm else 1.0 - 0.045 * absf(_h(floori(time * FLICKER_HZ), 7))
	_pictures.modulate = Color(k, k, k)
	_wear(time, rm)


## Scratches and dust: there for a moment, at places a hash of the time picks.
func _wear(time: float, rm: bool) -> void:
	var lit := _cover.color.a < 0.5
	for i in _scratches.size():
		var sc: Sprite2D = _scratches[i]
		var k := floori(time * 2.2 + i * 0.41)
		var on := not rm and lit and sc.texture != null and _h(k, 31 + i * 7) > 0.62
		sc.visible = on
		if on:
			var x := floorf((_h(k, 47 + i * 5) * 0.5 + 0.5) * (GATE.size.x - 48.0)) + 24.0
			var y := floorf((_h(k, 59 + i * 3) * 0.5 + 0.5) * maxf(0.0, GATE.size.y - sc.texture.get_height()))
			sc.position = GATE.position + Vector2(x + (1.0 if _h(floori(time * 12.0), 61 + i) > 0.6 else 0.0), y)
	for i in _dust.size():
		var d: Sprite2D = _dust[i]
		var k := floori(time * 12.0)
		var on := not rm and lit and d.texture != null and _h(k, 71 + i * 13) > 0.86
		d.visible = on
		if on:
			d.frame = absi(k + i) % d.hframes
			d.position = GATE.position + Vector2(floorf((_h(k, 83 + i) * 0.5 + 0.5) * (GATE.size.x - 8.0)),
				floorf((_h(k, 97 + i) * 0.5 + 0.5) * (GATE.size.y - 8.0)))


func _text_alpha(time: float, w: Vector2) -> float:
	if time < w.x or time > w.y:
		return 0.0
	return clampf(minf(time - w.x, w.y - time) / TEXT_RAMP, 0.0, 1.0)


static func _within(time: float, windows) -> bool:
	if windows is Array:
		for w in windows:
			if w is Array and w.size() >= 2 and time >= float(w[0]) and time < float(w[1]):
				return true
	return false


static func _v2(v) -> Vector2:
	return Vector2(float(v[0]), float(v[1])) if v is Array and v.size() >= 2 else Vector2.ZERO


func _rect(r: Rect2, col: Color) -> Polygon2D:
	var p := Polygon2D.new()
	p.polygon = PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)])
	p.color = col
	add_child(p)
	return p


func _fb_sprite(rel: String, parent: Node) -> Sprite2D:
	var s := Sprite2D.new()
	s.centered = false
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.texture = fb_tex(rel) if rel != "" else null
	parent.add_child(s)
	return s


## A texture of assets/cinematics/flashback/, imported or (fresh generator run) straight from the PNG.
func fb_tex(rel: String) -> Texture2D:
	var path := FB_ASSETS + rel
	if ResourceLoader.exists(path):
		var r = load(path)
		if r is Texture2D:
			return r
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	if not missing.has(path):
		missing.append(path)
	return null
