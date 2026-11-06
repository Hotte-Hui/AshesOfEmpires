extends Node2D
## The extras of a Chapter-3 part-1 cinematic shot (round 10, figures stream): travellers, porters, railwaymen,
## police of the Free City, delegates, the people on the river bank.  Art and the cast list come from
## tools/pixelgen/env_veltrava_cine_people.py (assets/cinematics/ch3/people/*.png + layout.json "<film>.people").
## Every figure is a pure function of the timeline time `t` (deterministic frames for seek() and the tests).
##
## Cast entry (Dictionary):
##   tex      atlas path relative to assets/cinematics/ch3/ (frames side by side)
##   frames   number of frames in the atlas
##   anchor   [ax, ay] the point of the frame that stands on the path (the soles)
##   path     [[t, x, y], ...] keyframes (absolute timeline seconds, world px); held before/after the ends
##   stride   px walked per walk cycle (frame follows the distance walked); 0 = animate by time with fps
##   fps      frames per second when stride is 0 (idle breathing, the lantern swaying)
##   show     [t0, t1] visible interval (optional)
##   mod      [r, g, b, a] modulate (optional, e.g. figures far away in the haze)
##   phase    frame offset (desynchronises equal sheets)
## Usage (in a scene script): var p := People.new(); p.setup(_layout.get("people_k1", []), tex); parent.add_child(p);
## then p.set_time(time) from _apply().

var entries: Array = []
var t := 0.0
## extra offset for every figure (camera moves, parallax planes)
var offset := Vector2.ZERO
var _tex: Dictionary = {}


func setup(list: Array, loader: Callable) -> void:
	entries = []
	for e in list:
		if not (e is Dictionary) or not (e as Dictionary).has("tex"):
			continue
		var d: Dictionary = e
		var rel := str(d["tex"])
		if not _tex.has(rel):
			_tex[rel] = loader.call(rel)
		entries.append(d)
	name = "People"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	light_mask = 0


func set_time(time: float) -> void:
	t = time
	queue_redraw()


## position on the path at time `time` and the distance walked so far
static func path_at(path: Array, time: float) -> Array:
	if path.is_empty():
		return [Vector2.ZERO, 0.0]
	var walked := 0.0
	var p0: Array = path[0]
	if time <= float(p0[0]) or path.size() == 1:
		return [Vector2(float(p0[1]), float(p0[2])), 0.0]
	for i in range(1, path.size()):
		var a: Array = path[i - 1]
		var b: Array = path[i]
		var pa := Vector2(float(a[1]), float(a[2]))
		var pb := Vector2(float(b[1]), float(b[2]))
		var seg := pa.distance_to(pb)
		if time <= float(b[0]):
			var u := clampf((time - float(a[0])) / maxf(0.0001, float(b[0]) - float(a[0])), 0.0, 1.0)
			return [pa.lerp(pb, u), walked + seg * u]
		walked += seg
	var last: Array = path[path.size() - 1]
	return [Vector2(float(last[1]), float(last[2])), walked]


func frame_of(e: Dictionary, walked: float) -> int:
	var n := maxi(1, int(e.get("frames", 1)))
	var stride := float(e.get("stride", 0.0))
	var ph := int(e.get("phase", 0))
	if stride > 0.0:
		return (int(floor(walked / stride * float(n))) + ph) % n
	return (int(floor(t * float(e.get("fps", 0.0)))) + ph) % n


func _draw() -> void:
	for e in entries:
		var d: Dictionary = e
		var sh: Array = d.get("show", [])
		if sh.size() == 2 and (t < float(sh[0]) or t > float(sh[1])):
			continue
		var tx: Texture2D = _tex.get(str(d["tex"]))
		if tx == null:
			continue
		var n := maxi(1, int(d.get("frames", 1)))
		var fw := tx.get_width() / n
		var fh := tx.get_height()
		var pw: Array = path_at(d.get("path", []), t)
		var anc: Array = d.get("anchor", [fw / 2, fh - 1])
		var pos := (pw[0] as Vector2) + offset - Vector2(float(anc[0]), float(anc[1]))
		var fi := frame_of(d, float(pw[1]))
		var col := Color(1, 1, 1, 1)
		var m: Array = d.get("mod", [])
		if m.size() >= 3:
			col = Color(float(m[0]), float(m[1]), float(m[2]), float(m[3]) if m.size() > 3 else 1.0)
		draw_texture_rect_region(tx, Rect2(pos.round(), Vector2(fw, fh)), Rect2(fi * fw, 0, fw, fh), col)
