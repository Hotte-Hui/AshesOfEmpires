extends RefCounted
## Pure logic of the Berlin mini-game "Rohrpost" (scenes/ui/minigames/Rohrpost.tscn, rohrpost_game.gd, §12.8).
## The archive's house tube system on the switch board in the reading room: three capsules from the porter's lodge,
## three boards (assets/ui/minigames/rohrpost/rohrpost_layout.json, written and verified by
## tools/pixelgen/gen_mg_rohrpost.py — the single source of the puzzle data). Tiles: h, v, curves NE/NW/SE/SW,
## x (crossing without a junction) and D (diverter: a knob that joins two of its tube stubs; turning cycles its
## states). A capsule enters at the source, follows the tubes and ends in a station (the reading room or a wrong
## one), jams in a diverter that does not join the tube it comes from, or sticks in a frozen line. Nothing is ever
## lost: a wrong capsule simply comes back. Every mutating call returns a small Dictionary.

const LAYOUT := "res://assets/ui/minigames/rohrpost/rohrpost_layout.json"
const OPEN := {"h": "WE", "v": "NS", "NE": "NE", "NW": "NW", "SE": "SE", "SW": "SW"}
const OPP := {"N": "S", "S": "N", "E": "W", "W": "E"}
const STEP := {"N": Vector2i(0, -1), "S": Vector2i(0, 1), "E": Vector2i(1, 0), "W": Vector2i(-1, 0)}

var data: Dictionary = {}
var boards: Array = []
var board_i := 0
var states: Array = []
var sends := 0
var wrong := 0
var delivered: Array = []        # board indexes whose capsule reached the target
var done := false


func _init(path := LAYOUT) -> void:
	load_layout(path)


func load_layout(path := LAYOUT) -> bool:
	data = {}
	boards = []
	if FileAccess.file_exists(path):
		var d = JSON.parse_string(FileAccess.get_file_as_string(path))
		if d is Dictionary:
			data = d
			boards = data.get("boards", [])
	reset()
	return not boards.is_empty()


func reset() -> void:
	board_i = 0
	sends = 0
	wrong = 0
	delivered = []
	done = false
	reset_board()


## Puts the knobs of the current board back where they were when it opened.
func reset_board() -> void:
	states = []
	for d in board().get("diverters", []):
		states.append(int(d.get("start", 0)))


func board() -> Dictionary:
	return boards[board_i] if board_i < boards.size() else {}


func board_count() -> int:
	return boards.size()


func cols() -> int:
	return int((data.get("grid", [8, 5]) as Array)[0])


func rows() -> int:
	return int((data.get("grid", [8, 5]) as Array)[1])


func diverters() -> Array:
	return board().get("diverters", [])


func diverter_cell(di: int) -> Vector2i:
	var c: Array = diverters()[di]["cell"]
	return Vector2i(int(c[0]), int(c[1]))


## Side pair the knob of diverter `di` joins now ("WE", "SW", …).
func pair(di: int, st: Array = []) -> String:
	var s: Array = st if not st.is_empty() else states
	var opts: Array = diverters()[di]["states"]
	return str(opts[int(s[di]) % opts.size()])


func turn(di: int, dir := 1) -> String:
	if done or di < 0 or di >= states.size():
		return ""
	var n: int = (diverters()[di]["states"] as Array).size()
	states[di] = posmod(int(states[di]) + dir, n)
	return pair(di)


func _diverter_at(cell: Vector2i) -> int:
	var ds := diverters()
	for i in ds.size():
		if diverter_cell(i) == cell:
			return i
	return -1


func _station_at(cell: Vector2i, side: String) -> String:
	for s in board().get("stations", []):
		if int(s["cell"][0]) == cell.x and int(s["cell"][1]) == cell.y and str(s["side"]) == side:
			return str(s["id"])
	return ""


func _frozen(cell: Vector2i) -> bool:
	for f in board().get("frozen", []):
		if int(f[0]) == cell.x and int(f[1]) == cell.y:
			return true
	return false


## Follows a capsule from the source with the knob states `st` (default: the current ones).
## {result: "arrive" | "jam" | "frozen" | "dead" | "open" | "loop", station, cell, diverter (jam), path}
## path = [{cell, enter, exit}] (exit "" where the capsule stops).
func simulate(st: Array = []) -> Dictionary:
	var s: Array = st if not st.is_empty() else states
	var b := board()
	if b.is_empty():
		return {"result": "open", "path": []}
	var src: Dictionary = b["source"]
	var cell := Vector2i(int(src["cell"][0]), int(src["cell"][1]))
	var enter := str(src["side"])
	var path: Array = []
	var seen := {}
	var tiles: Dictionary = b.get("tiles", {})
	while true:
		var key := "%d,%d:%s" % [cell.x, cell.y, enter]
		if seen.has(key):
			return {"result": "loop", "cell": cell, "path": path}
		seen[key] = true
		if _frozen(cell):
			path.append({"cell": cell, "enter": enter, "exit": ""})
			return {"result": "frozen", "cell": cell, "path": path}
		var out := ""
		var di := _diverter_at(cell)
		if di >= 0:
			var p := pair(di, s)
			if not p.contains(enter):
				path.append({"cell": cell, "enter": enter, "exit": ""})
				return {"result": "jam", "cell": cell, "diverter": di, "path": path}
			out = p[1] if p[0] == enter else p[0]
		else:
			var t := str(tiles.get("%d,%d" % [cell.x, cell.y], ""))
			if t == "":
				return {"result": "open", "cell": cell, "path": path}
			if t == "x":
				out = OPP[enter]
			else:
				var o := str(OPEN.get(t, ""))
				if not o.contains(enter):
					path.append({"cell": cell, "enter": enter, "exit": ""})
					return {"result": "dead", "cell": cell, "path": path}
				out = o[1] if o[0] == enter else o[0]
		path.append({"cell": cell, "enter": enter, "exit": out})
		var station := _station_at(cell, out)
		if station != "":
			return {"result": "arrive", "station": station, "cell": cell, "path": path}
		cell += STEP[out]
		if cell.x < 0 or cell.y < 0 or cell.x >= cols() or cell.y >= rows():
			return {"result": "open", "cell": cell, "path": path}
		enter = OPP[out]
	return {"result": "open", "path": path}


func target() -> String:
	return str(board().get("target", "lesesaal"))


## Sends the capsule with the current setting. {ok (reached the target), result, station, diverter, path, last}
func send() -> Dictionary:
	if done:
		return {"ok": false, "result": "done", "path": []}
	sends += 1
	var r := simulate()
	var ok := str(r.get("result", "")) == "arrive" and str(r.get("station", "")) == target()
	r["ok"] = ok
	if ok:
		delivered.append(board_i)
		r["last"] = board_i >= boards.size() - 1
	else:
		wrong += 1
	return r


## After a delivered capsule: the next board (false when that was the last one -> done).
func next_board() -> bool:
	if board_i >= boards.size() - 1:
		done = true
		return false
	board_i += 1
	reset_board()
	return true


## Every setting of the current board that reaches the target, fewest changes from `from` first: [[changes, states]].
func solutions(from: Array = []) -> Array:
	var base: Array = from if not from.is_empty() else states
	var ds := diverters()
	var out: Array = []
	var combo: Array = []
	for i in ds.size():
		combo.append(0)
	var total := 1
	for d in ds:
		total *= (d["states"] as Array).size()
	for n in total:
		var k := n
		for i in ds.size():
			var m: int = (ds[i]["states"] as Array).size()
			combo[i] = k % m
			k /= m
		var r := simulate(combo)
		if str(r.get("result", "")) == "arrive" and str(r.get("station", "")) == target():
			var ch := 0
			for i in ds.size():
				if int(combo[i]) != int(base[i]):
					ch += 1
			out.append([ch, combo.duplicate()])
	out.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	return out


## Diverters that still have to be turned for the nearest solution, in the order the capsule meets them.
func wrong_diverters() -> Array:
	var sols := solutions()
	if sols.is_empty():
		return []
	var best: Array = sols[0][1]
	var order: Array = []
	for step in simulate(best).get("path", []):
		var di := _diverter_at(step["cell"])
		if di >= 0 and not (di in order):
			order.append(di)
	var out: Array = []
	for di in order:
		if int(best[di]) != int(states[di]):
			out.append(di)
	for di in states.size():
		if int(best[di]) != int(states[di]) and not (di in out):
			out.append(di)
	return out


## Turns needed per diverter (clockwise) to reach the nearest solution.
func turns_needed() -> Array:
	var sols := solutions()
	var out: Array = []
	if sols.is_empty():
		return out
	var best: Array = sols[0][1]
	for di in states.size():
		var n: int = (diverters()[di]["states"] as Array).size()
		out.append(posmod(int(best[di]) - int(states[di]), n))
	return out


# ================================================================ geometry (art px of the board image)
func cell_size() -> float:
	return float(data.get("cell", 22))


func origin() -> Vector2:
	var o: Array = data.get("origin", [52, 16])
	return Vector2(float(o[0]), float(o[1]))


func side_mid(cell: Vector2i, side: String) -> Vector2:
	var c := cell_size()
	var p := origin() + Vector2(cell) * c
	match side:
		"N":
			return p + Vector2(c / 2.0, 0)
		"S":
			return p + Vector2(c / 2.0, c)
		"W":
			return p + Vector2(0, c / 2.0)
	return p + Vector2(c, c / 2.0)


func cell_center(cell: Vector2i) -> Vector2:
	return origin() + (Vector2(cell) + Vector2(0.5, 0.5)) * cell_size()


## Where a station's mouth opens (layout "mouth" = [W/E, N/S] art px outside the grid edge).
func mouth(cell: Vector2i, side: String) -> Vector2:
	var m := side_mid(cell, side)
	var d: Vector2i = STEP[side]
	var ml: Array = data.get("mouth", [10, 6])
	return m + Vector2(d) * float(ml[0] if side in ["W", "E"] else ml[1])


func station_mouth(id: String) -> Vector2:
	for s in board().get("stations", []):
		if str(s["id"]) == id:
			return mouth(Vector2i(int(s["cell"][0]), int(s["cell"][1])), str(s["side"]))
	return Vector2.ZERO


func source_mouth() -> Vector2:
	var src: Dictionary = board().get("source", {})
	if src.is_empty():
		return Vector2.ZERO
	return mouth(Vector2i(int(src["cell"][0]), int(src["cell"][1])), str(src["side"]))


## Polyline of a simulated run (art px), from the source mouth to the station mouth or the point where it stuck.
func polyline(run: Dictionary) -> PackedVector2Array:
	var pts := PackedVector2Array()
	pts.append(source_mouth())
	var path: Array = run.get("path", [])
	for i in path.size():
		var st: Dictionary = path[i]
		var cell: Vector2i = st["cell"]
		var a := str(st["enter"])
		var b := str(st["exit"])
		var pa := side_mid(cell, a)
		pts.append(pa)
		if b == "":
			# stuck: a jammed knob stops the capsule at its housing, a frozen line a little way in
			var stop_at := 0.28 if str(run.get("result", "")) == "jam" else 0.38
			pts.append(pa.lerp(cell_center(cell), stop_at * 2.0))
			break
		var pb := side_mid(cell, b)
		if OPP[a] == b:
			pts.append(pb)
		else:
			var c := cell_size()
			var corner := origin() + Vector2(cell) * c
			if a + b in ["NE", "EN"]:
				corner += Vector2(c, 0)
			elif a + b in ["SE", "ES"]:
				corner += Vector2(c, c)
			elif a + b in ["SW", "WS"]:
				corner += Vector2(0, c)
			var a0 := (pa - corner).angle()
			var a1 := (pb - corner).angle()
			var da := wrapf(a1 - a0, -PI, PI)
			for k in range(1, 9):
				var ang := a0 + da * k / 8.0
				pts.append(corner + Vector2(cos(ang), sin(ang)) * c / 2.0)
	if str(run.get("result", "")) == "arrive":
		pts.append(station_mouth(str(run.get("station", ""))))
	return pts
