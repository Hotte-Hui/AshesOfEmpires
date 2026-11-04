extends Node2D
## Pixel-crisp runtime drawing for the Chapter-3 cinematics: deterministic snow (a pure function of
## time, seeded once), and Bresenham helpers used by wires and clock hands.  Everything lands on whole
## world pixels (1 texel = 1 px), nothing is scaled or rotated.

var rect := Rect2(0, 0, 640, 360)
var flakes: Array = []
var time := 0.0
var visible_rect := Rect2()      # optional clip (flakes outside are skipped); empty = rect


## layers: [{count, v: Vector2 px/s, vjit: float (0..1), size: Vector2, color: Color, sway: px, streak: int}]
func setup_snow(r: Rect2, layers: Array, seed_value: int) -> void:
	rect = r
	flakes.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for L in layers:
		for i in int(L.get("count", 40)):
			var v: Vector2 = L.get("v", Vector2(0, 12))
			var j := float(L.get("vjit", 0.3))
			flakes.append({
				"p": Vector2(rng.randf() * r.size.x, rng.randf() * r.size.y) + r.position,
				"v": v * (1.0 + rng.randf_range(-j, j)),
				"size": L.get("size", Vector2(1, 1)),
				"col": L.get("color", Color("#c2c9d2")),
				"ph": rng.randf() * TAU,
				"fr": rng.randf_range(0.6, 1.4),
				"amp": float(L.get("sway", 2.0)) * rng.randf_range(0.5, 1.0),
				"streak": int(L.get("streak", 0)),
			})


func set_time(tt: float) -> void:
	time = tt
	queue_redraw()


func _draw() -> void:
	var clip := visible_rect if visible_rect.size != Vector2.ZERO else rect
	for f in flakes:
		var p: Vector2 = f["p"] + f["v"] * time + Vector2(sin(f["ph"] + time * f["fr"]) * f["amp"], 0.0)
		p.x = rect.position.x + fposmod(p.x - rect.position.x, rect.size.x)
		p.y = rect.position.y + fposmod(p.y - rect.position.y, rect.size.y)
		p = p.floor()
		if not clip.has_point(p):
			continue
		var sz: Vector2 = f["size"]
		var st: int = f["streak"]
		if st > 0:
			var dir := -signf(f["v"].x)
			draw_rect(Rect2(p, Vector2(st, 1)) if dir > 0 else Rect2(p - Vector2(st - 1, 0), Vector2(st, 1)), f["col"])
		else:
			draw_rect(Rect2(p, sz), f["col"])


## Bresenham line of 1 px squares into canvas item `ci` (call from inside ci._draw()).
static func line(ci: CanvasItem, a: Vector2, b: Vector2, col: Color, w := 1) -> void:
	var x0 := roundi(a.x)
	var y0 := roundi(a.y)
	var x1 := roundi(b.x)
	var y1 := roundi(b.y)
	var dx := absi(x1 - x0)
	var dy := -absi(y1 - y0)
	var sx := 1 if x0 < x1 else -1
	var sy := 1 if y0 < y1 else -1
	var err := dx + dy
	var guard := 0
	while guard < 4096:
		guard += 1
		ci.draw_rect(Rect2(x0, y0, w, w), col)
		if x0 == x1 and y0 == y1:
			break
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			x0 += sx
		if e2 <= dx:
			err += dx
			y0 += sy


## Sagging wire between two points (catenary approximated by a parabola), drawn as 1 px steps.
static func wire(ci: CanvasItem, a: Vector2, b: Vector2, sag: float, col: Color, clip := Rect2()) -> void:
	var n := maxi(2, int(absf(b.x - a.x)))
	var prev := Vector2(roundf(a.x), roundf(a.y))
	for i in range(1, n + 1):
		var u := float(i) / n
		var p := Vector2(lerpf(a.x, b.x, u), lerpf(a.y, b.y, u) + sag * 4.0 * u * (1.0 - u)).round()
		if clip.size == Vector2.ZERO or clip.has_point(p):
			if absf(p.y - prev.y) > 1.0:
				line(ci, prev, p, col)
			else:
				ci.draw_rect(Rect2(p, Vector2.ONE), col)
		prev = p
