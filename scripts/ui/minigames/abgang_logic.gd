extends RefCounted
## Rule of the vector-display game „Planspiel Abgang“ (scenes/ui/minigames/PlanspielAbgang.tscn, explore entry
## berlin.annex.planspiel at the data desk of Nebenstelle Süd, L_C4_Annex scene D; TECHNICAL_ARCHITECTURE §12.8).
## The State Police's own simulation of an arrest in the Süd-8 quarter: the player steers the hunted figure through
## three small grid maps (street, courtyard, stairwell + attic) past posts that walk and turn „im Takt“.
##
## Time is counted in ticks (TICK s). A step of the figure takes STEP_TICKS, a beat of the posts BEAT_UNITS steps: a
## post changes its cell or its facing only on a beat, so its sight is constant during a beat. Sight is a beam along
## the facing: SIGHT cells long, one cell wide next to the post and three cells wide beyond; solid cells (houses,
## walls, bins, chimneys) and a height difference of more than one stair step cover. Standing in a seen cell (or on a
## post's cell) for more than GRACE_TICKS means „Zugriff“: the map starts again with the posts at beat 0, so every
## attempt meets the same rhythm. The figure may move between cells whose height differs by at most one step.
##
## Maps: `rows` ("." floor, "S" start, "E" the gap, SOLID chars), optional `lift` (digit = height in stair steps),
## `watchers` ({at, dir, script: ["go", x, y] one cell per beat facing the way, ["turn", dir, beats]}; the script
## must lead back to the first cell and facing), `decor` (render only: x, height, z of both ends in cell units and a
## brightness step). All of it is checked by tests/test_c4_terminal.gd: closed patrols, a start no post ever sees, a
## way through that tolerates a whole step of hesitation at every move (policy margin 1), and a naive run (the
## shortest way, at once) that is caught.
##
## The solver is a backward breadth-first search over (cell, step-unit mod period): policy(margin) gives the next
## move from every state; demo_action() is what the demo (synthetic keys) and the hint trace read. A state is
## usable when the cell is unseen from `margin` units before to `margin` units after.

const TICK := 0.05
const STEP_TICKS := 5
const BEAT_UNITS := 3
const BEAT_TICKS := STEP_TICKS * BEAT_UNITS
const SIGHT := 4
const GRACE_TICKS := 2
## World height of one stair step (the renderer's unit: one cell = 1.0).
const LIFT := 0.34
const DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]   # N E S W
const SOLID := "#HwoctL"
## Wall heights the renderer draws for the solid chars (world units).
const HEIGHT := {"#": 1.5, "H": 3.0, "w": 0.9, "o": 0.42, "c": 1.3, "t": 1.05, "L": 1.0}

const MAPS := [
	{"id": "street",
		"rows": [
			"HHHHHHHHHHHHHHHH",
			"HHHHHHHHHHHHEHHH",
			"..........o.....",
			"................",
			"................",
			"..tt...LL.......",
			"..tt............",
			"S..............."],
		"watchers": [
			{"at": [2, 4], "dir": 1, "script": [["go", 13, 4], ["turn", 3, 1], ["go", 2, 4], ["turn", 1, 1]]},
			{"at": [14, 2], "dir": 3, "script": [["turn", 2, 3], ["turn", 3, 3]]}],
		"decor": [[0.0, 0.0, 6.36, 12.4, 0.0, 6.36, 1], [0.0, 0.0, 6.64, 12.6, 0.0, 6.64, 1],
			[12.4, 0.0, 6.36, 14.2, 0.0, 5.3, 1], [12.6, 0.0, 6.64, 14.5, 0.0, 5.5, 1],
			[14.2, 0.0, 5.3, 14.6, 0.0, 3.4, 1], [14.5, 0.0, 5.5, 14.9, 0.0, 3.5, 1],
			[12.0, 0.0, 2.0, 12.0, 1.6, 2.0, 2], [13.0, 0.0, 2.0, 13.0, 1.6, 2.0, 2], [12.0, 1.6, 2.0, 13.0, 1.6, 2.0, 2]]},
	{"id": "yard",
		"rows": [
			"wwwwwwwwwwwwEw",
			"w............w",
			"w.##.....o...w",
			"w.##.........w",
			"w............w",
			"w...o.....##.w",
			"w.........##.w",
			"w.......o....w",
			"wSwwwwwwwwwwww"],
		"watchers": [
			{"at": [5, 4], "dir": 3, "script": [["turn", 3, 1], ["turn", 0, 2], ["turn", 1, 2], ["turn", 2, 2], ["turn", 3, 1]]},
			{"at": [12, 1], "dir": 2, "script": [["go", 12, 7], ["turn", 0, 1], ["go", 12, 1], ["turn", 2, 1]]}],
		"decor": [[6.5, 0.0, 6.5, 6.5, 0.8, 6.5, 1], [8.0, 0.0, 6.5, 8.0, 0.8, 6.5, 1], [6.5, 0.8, 6.5, 8.0, 0.8, 6.5, 2],
			[1.0, 1.2, 1.0, 9.0, 1.2, 1.0, 1],
			[12.0, 0.0, 1.0, 12.0, 1.3, 1.0, 2], [13.0, 0.0, 1.0, 13.0, 1.3, 1.0, 2], [12.0, 1.3, 1.0, 13.0, 1.3, 1.0, 2]]},
	{"id": "attic",
		"rows": [
			"##############",
			"#....c.......#",
			"E............#",
			"#....c..c....#",
			"##########.###",
			"#........#..##",
			"#........#.###",
			"#S.........###",
			"##############"],
		"lift": [
			"00000000000000",
			"05555555555550",
			"55555555555550",
			"05555555555550",
			"00000000004000",
			"00000000003300",
			"00000000002000",
			"00000000001000",
			"00000000000000"],
		"watchers": [
			{"at": [12, 3], "dir": 3, "script": [["go", 10, 3], ["go", 10, 5], ["turn", 2, 1], ["go", 10, 3], ["go", 12, 3], ["turn", 1, 2], ["turn", 3, 1]]},
			{"at": [2, 2], "dir": 1, "script": [["go", 9, 2], ["turn", 3, 1], ["go", 2, 2], ["turn", 1, 1]]}],
		"decor": [[1.0, 3.3, 2.5, 13.0, 3.3, 2.5, 1],
			[1.0, 1.7, 1.0, 1.0, 3.3, 2.5, 1], [1.0, 3.3, 2.5, 1.0, 1.7, 4.0, 1],
			[4.0, 1.7, 1.0, 4.0, 3.3, 2.5, 1], [4.0, 3.3, 2.5, 4.0, 1.7, 4.0, 1],
			[7.0, 1.7, 1.0, 7.0, 3.3, 2.5, 1], [7.0, 3.3, 2.5, 7.0, 1.7, 4.0, 1],
			[10.0, 1.7, 1.0, 10.0, 3.3, 2.5, 1], [10.0, 3.3, 2.5, 10.0, 1.7, 4.0, 1],
			[13.0, 1.7, 1.0, 13.0, 3.3, 2.5, 1], [13.0, 3.3, 2.5, 13.0, 1.7, 4.0, 1],
			[1.0, 1.7, 2.0, 1.0, 2.9, 2.0, 2], [1.0, 2.9, 2.0, 1.0, 2.9, 3.0, 2], [1.0, 2.9, 3.0, 1.0, 1.7, 3.0, 2]]}]

var index := -1
var id := ""
var w := 0
var h := 0
var rows: Array = []
var solid := PackedByteArray()
var lift := PackedInt32Array()
var start := Vector2i.ZERO
var goal := Vector2i.ZERO
## Per post: [x, y, dir] for every beat of its own period.
var patrols: Array = []
## Beats until every post is back where it started.
var period := 1
## Per beat: PackedByteArray per cell — 0 unseen, n seen by post n (1-based), 255 a post stands there.
var danger: Array = []
## Per beat: per post the cells of its beam (Array of Vector2i).
var beams: Array = []

var tick := 0
var cell := Vector2i.ZERO
var from_cell := Vector2i.ZERO
var move_left := 0
## Direction the player holds (-1 none); a step starts as soon as the last one is over.
var want := -1
var facing := 0
var caught := false
var caught_by := -1
var through := false
var steps := 0
var _danger_ticks := 0
var _policy := {}


func _init() -> void:
	load_map(0)


static func map_count() -> int:
	return MAPS.size()


func load_map(i: int) -> void:
	index = clampi(i, 0, MAPS.size() - 1)
	var m: Dictionary = MAPS[index]
	id = str(m["id"])
	rows = m["rows"]
	h = rows.size()
	w = str(rows[0]).length()
	solid = PackedByteArray()
	solid.resize(w * h)
	lift = PackedInt32Array()
	lift.resize(w * h)
	var lifts: Array = m.get("lift", [])
	for y in h:
		var line := str(rows[y])
		for x in w:
			var ch := line[x] if x < line.length() else "#"
			solid[y * w + x] = 1 if SOLID.contains(ch) else 0
			if ch == "S":
				start = Vector2i(x, y)
			elif ch == "E":
				goal = Vector2i(x, y)
			var lv := 0
			if y < lifts.size() and x < str(lifts[y]).length():
				lv = maxi(0, str(lifts[y])[x].to_int())
			lift[y * w + x] = lv
	patrols.clear()
	period = 1
	for wd in m.get("watchers", []):
		var p := expand_patrol(wd)
		patrols.append(p)
		period = _lcm(period, p.size())
	_precompute()
	_policy.clear()
	reset()


## Same map, posts back at beat 0.
func reset() -> void:
	tick = 0
	cell = start
	from_cell = start
	move_left = 0
	want = -1
	facing = 0
	caught = false
	caught_by = -1
	through = false
	steps = 0
	_danger_ticks = 0


static func _lcm(a: int, b: int) -> int:
	var x := a
	var y := b
	while y != 0:
		var t := y
		y = x % y
		x = t
	return a / x * b


## A post's script as one [x, y, dir] per beat; the closing state (equal to the first) is dropped.
static func expand_patrol(wd: Dictionary) -> Array:
	var pos := Vector2i(int(wd["at"][0]), int(wd["at"][1]))
	var dir := int(wd.get("dir", 0))
	var out: Array = [[pos.x, pos.y, dir]]
	for op in wd.get("script", []):
		if str(op[0]) == "go":
			var target := Vector2i(int(op[1]), int(op[2]))
			var guard := 0
			while pos != target and guard < 64:
				guard += 1
				var d := target - pos
				var sv := Vector2i(signi(d.x), 0) if d.x != 0 else Vector2i(0, signi(d.y))
				dir = DIRS.find(sv)
				pos += sv
				out.append([pos.x, pos.y, dir])
		elif str(op[0]) == "turn":
			dir = int(op[1])
			for k in int(op[2]):
				out.append([pos.x, pos.y, dir])
	if out.size() > 1 and out[out.size() - 1] == out[0]:
		out.pop_back()
	return out


## True when the script of post `i` leads back to its first cell and facing (the cycle closes).
func patrol_closed(i: int) -> bool:
	var wd: Dictionary = MAPS[index]["watchers"][i]
	var first := Vector2i(int(wd["at"][0]), int(wd["at"][1]))
	var pos := first
	var dir := int(wd.get("dir", 0))
	var n := 1
	for op in wd.get("script", []):
		if str(op[0]) == "go":
			var target := Vector2i(int(op[1]), int(op[2]))
			if target.x != pos.x and target.y != pos.y:
				return false
			n += absi(target.x - pos.x) + absi(target.y - pos.y)
			var d := target - pos
			if d != Vector2i.ZERO:
				dir = DIRS.find(Vector2i(signi(d.x), signi(d.y)))
			pos = target
		else:
			dir = int(op[1])
			n += int(op[2])
	var closed := pos == first and dir == int(wd.get("dir", 0))
	return closed and n - 1 == (patrols[i] as Array).size()


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < w and c.y < h


func walkable(c: Vector2i) -> bool:
	return inside(c) and solid[c.y * w + c.x] == 0


func lift_at(c: Vector2i) -> int:
	return int(lift[c.y * w + c.x]) if inside(c) else 0


func char_at(c: Vector2i) -> String:
	return str(rows[c.y])[c.x] if inside(c) else " "


## A step from a to its neighbour b is possible (floor on both sides, at most one stair step apart).
func passable(a: Vector2i, b: Vector2i) -> bool:
	return walkable(a) and walkable(b) and absi(lift_at(a) - lift_at(b)) <= 1


## Free line between two cells (Bresenham; the cells strictly between must not be solid).
func los(a: Vector2i, b: Vector2i) -> bool:
	var x0 := a.x
	var y0 := a.y
	var dx := absi(b.x - a.x)
	var dy := -absi(b.y - a.y)
	var sx := 1 if a.x < b.x else -1
	var sy := 1 if a.y < b.y else -1
	var err := dx + dy
	for guard in 64:
		if x0 == b.x and y0 == b.y:
			return true
		if not (x0 == a.x and y0 == a.y) and solid[y0 * w + x0] != 0:
			return false
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			x0 += sx
		if e2 <= dx:
			err += dx
			y0 += sy
	return false


## The cells a post at `pos` facing `dir` sees.
func beam_cells(pos: Vector2i, dir: int) -> Array:
	var out: Array = []
	var fwd: Vector2i = DIRS[dir]
	var side := Vector2i(-fwd.y, fwd.x)
	for f in range(1, SIGHT + 1):
		var half := 0 if f == 1 else 1
		for l in range(-half, half + 1):
			var c := pos + fwd * f + side * l
			if not walkable(c) or absi(lift_at(c) - lift_at(pos)) > 1:
				continue
			if los(pos, c):
				out.append(c)
	return out


func _precompute() -> void:
	danger.clear()
	beams.clear()
	for b in period:
		var d := PackedByteArray()
		d.resize(w * h)
		var per_post: Array = []
		for i in patrols.size():
			var st: Array = post_state(i, b)
			var pos := Vector2i(int(st[0]), int(st[1]))
			var cells := beam_cells(pos, int(st[2]))
			per_post.append(cells)
			for c in cells:
				if d[c.y * w + c.x] == 0:
					d[c.y * w + c.x] = i + 1
		for i in patrols.size():
			var st2: Array = post_state(i, b)
			d[int(st2[1]) * w + int(st2[0])] = 255
		danger.append(d)
		beams.append(per_post)


## [x, y, dir] of post `i` at beat `b` (any integer).
func post_state(i: int, b: int) -> Array:
	var p: Array = patrols[i]
	return p[posmod(b, p.size())]


func beat() -> int:
	return (tick / BEAT_TICKS) % period


## 0..1 inside the current beat.
func beat_phase() -> float:
	return float(tick % BEAT_TICKS) / float(BEAT_TICKS)


## 0..1 of the running step (1 = standing).
func step_phase() -> float:
	return 1.0 - float(move_left) / float(STEP_TICKS)


func seen_at(c: Vector2i, b: int) -> int:
	return int(danger[posmod(b, period)][c.y * w + c.x]) if inside(c) else 0


func post_on(c: Vector2i, b: int) -> int:
	for i in patrols.size():
		var st: Array = post_state(i, b)
		if int(st[0]) == c.x and int(st[1]) == c.y:
			return i
	return -1


## One tick. Returns "" | "moved" | "bump" | "seen" | "exit".
func step() -> String:
	if caught or through:
		return ""
	tick += 1
	var ev := ""
	if move_left > 0:
		move_left -= 1
		if move_left == 0 and cell == goal:
			through = true
			return "exit"
	if move_left == 0 and want >= 0:
		ev = _try_step(want)
	var b := beat()
	var dv := seen_at(cell, b)
	if dv != 0:
		_danger_ticks += 1
		if _danger_ticks > GRACE_TICKS:
			caught = true
			caught_by = post_on(cell, b) if dv == 255 else dv - 1
			return "seen"
	else:
		_danger_ticks = 0
	return ev


func _try_step(d: int) -> String:
	facing = d
	var target: Vector2i = cell + DIRS[d]
	if not passable(cell, target):
		return "bump"
	from_cell = cell
	cell = target
	move_left = STEP_TICKS
	steps += 1
	return "moved"


## True while the figure stands in a seen cell but the post has not reacted yet.
func in_danger() -> bool:
	return _danger_ticks > 0 and not caught


# ================================================================ solver
## {"act": PackedInt32Array, "dist": PackedInt32Array, "units": int} over state = unit * (w*h) + cell.
## act: -2 no way from here, -1 wait, 0..3 step N/E/S/W; dist: units to the gap (-1 none).
func policy(margin := 1) -> Dictionary:
	if _policy.has(margin):
		return _policy[margin]
	var pu := period * BEAT_UNITS
	var n := w * h
	var safe := PackedByteArray()
	safe.resize(pu * n)
	for u in pu:
		for c in n:
			if solid[c] != 0:
				continue
			var ok := 1
			for d in range(-margin, margin + 1):
				if danger[posmod(u + d, pu) / BEAT_UNITS][c] != 0:
					ok = 0
					break
			safe[u * n + c] = ok
	var act := PackedInt32Array()
	act.resize(pu * n)
	act.fill(-2)
	var dist := PackedInt32Array()
	dist.resize(pu * n)
	dist.fill(-1)
	var queue := PackedInt32Array()
	var g := goal.y * w + goal.x
	for u in pu:
		if safe[u * n + g] != 0:
			dist[u * n + g] = 0
			act[u * n + g] = -1
			queue.append(u * n + g)
	var head := 0
	while head < queue.size():
		var s := queue[head]
		head += 1
		var u := s / n
		var c := s % n
		var up := posmod(u - 1, pu)
		var cx := c % w
		var cy := c / w
		if safe[up * n + c] != 0:
			for d in 4:
				var px: int = cx - DIRS[d].x
				var py: int = cy - DIRS[d].y
				if px < 0 or py < 0 or px >= w or py >= h:
					continue
				var p := py * w + px
				if solid[p] != 0 or absi(lift[p] - lift[c]) > 1:
					continue
				var ps := up * n + p
				if safe[ps] == 0 or dist[ps] >= 0:
					continue
				dist[ps] = dist[s] + 1
				act[ps] = d
				queue.append(ps)
			var ws := up * n + c
			if dist[ws] < 0:
				dist[ws] = dist[s] + 1
				act[ws] = -1
				queue.append(ws)
	# equally fast ways: stand still first and run later (no stepping to and fro while a post passes)
	for s2 in pu * n:
		if act[s2] < 0 or dist[s2] <= 0:
			continue
		var wn := ((s2 / n + 1) % pu) * n + s2 % n
		if dist[wn] == dist[s2] - 1:
			act[s2] = -1
	var res := {"act": act, "dist": dist, "units": pu}
	_policy[margin] = res
	return res


## The step-unit the figure's next decision belongs to (rounded to the nearest unit boundary).
func decision_unit() -> int:
	return ((tick + move_left + STEP_TICKS / 2) / STEP_TICKS) % (period * BEAT_UNITS)


## What the solver would do now: -1 wait, 0..3 the direction to hold.
func demo_action(margin := 1) -> int:
	if caught or through:
		return -1
	var pol := policy(margin)
	var a := int(pol["act"][decision_unit() * w * h + cell.y * w + cell.x])
	return a if a >= 0 else -1


## The next cells of a safe way from here (for the hint), up to the first pause on the way or `max_cells`; a pause
## before the first step is skipped (demo_action() says whether it is time to go).
func trace(max_cells := 10, margin := 1) -> Array:
	var out: Array = []
	if caught or through:
		return out
	var pol := policy(margin)
	var pu := int(pol["units"])
	var n := w * h
	var u := decision_unit()
	var c := cell
	for guard in pu * 2:
		var a := int(pol["act"][u * n + c.y * w + c.x])
		if a == -2 or (a == -1 and not out.is_empty()):
			break
		u = (u + 1) % pu
		if a == -1:
			continue
		c += DIRS[a]
		out.append(c)
		if c == goal or out.size() >= max_cells:
			break
	return out


## The solver's run from the start at beat 0: {"ok", "units", "waits", "moves", "path": [Vector2i]}.
func solve_stats(margin := 1) -> Dictionary:
	var pol := policy(margin)
	var pu := int(pol["units"])
	var n := w * h
	var c := start
	var u := 0
	var waits := 0
	var moves := 0
	var path: Array = [c]
	while c != goal and moves + waits < pu * 6:
		var a := int(pol["act"][(u % pu) * n + c.y * w + c.x])
		if a == -2:
			return {"ok": false, "units": moves + waits, "waits": waits, "moves": moves, "path": path}
		if a == -1:
			waits += 1
		else:
			c += DIRS[a]
			moves += 1
			path.append(c)
		u += 1
	return {"ok": c == goal, "units": moves + waits, "waits": waits, "moves": moves, "path": path}


## The shortest way ignoring the posts (breadth-first), as directions.
func shortest_dirs() -> Array:
	var n := w * h
	var prev := PackedInt32Array()
	prev.resize(n)
	prev.fill(-1)
	var how := PackedInt32Array()
	how.resize(n)
	var s := start.y * w + start.x
	var queue := PackedInt32Array([s])
	prev[s] = s
	var head := 0
	while head < queue.size():
		var c := queue[head]
		head += 1
		var cv := Vector2i(c % w, c / w)
		if cv == goal:
			break
		for d in 4:
			var nv: Vector2i = cv + DIRS[d]
			if not passable(cv, nv) or prev[nv.y * w + nv.x] >= 0:
				continue
			prev[nv.y * w + nv.x] = c
			how[nv.y * w + nv.x] = d
			queue.append(nv.y * w + nv.x)
	var out: Array = []
	var c2 := goal.y * w + goal.x
	if prev[c2] < 0:
		return out
	while c2 != s:
		out.push_front(int(how[c2]))
		c2 = prev[c2]
	return out


## Walks `dirs` without a pause from beat 0 on a fresh copy of this map: "exit" | "seen" | "" (ran out).
func run_dirs(dirs: Array) -> String:
	var sim = get_script().new()
	sim.load_map(index)
	var i := 0
	sim.want = int(dirs[0]) if not dirs.is_empty() else -1
	for guard in 4000:
		var ev: String = sim.step()
		if ev == "moved":
			i += 1
			sim.want = int(dirs[i]) if i < dirs.size() else -1
		if ev == "seen" or ev == "exit":
			return ev
		if i >= dirs.size() and sim.move_left == 0:
			break
	return ""
