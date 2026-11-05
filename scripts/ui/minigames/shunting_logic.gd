extends RefCounted
## Karsk "Rangieren" — pure puzzle logic (no nodes; used by shunting_game.gd and tests/test_minigames.gd).
## A small inglenook: the shunting engine stands on the headshunt "H" (room for the engine + 2 wagons); two hand
## points lead to siding 1 (3 wagons, the evening train), siding 2 (2) and siding 3 (2).
## Wagons: K tank, U coal, P panels (flat), G covered. Strings list the wagons of a track: H from the engine
## outwards, sidings from the points (throat) to the buffer stop.
## One trip: set the points, drive in (the automatic coupler picks up everything standing there), choose where to
## open the coupling (cut = wagons the engine keeps, counted from the engine) and pull back to the headshunt.
## Goal: siding 1 holds GOAL (throat -> buffer stop), i.e. from the buffer stop: tank, coal, panels.

const CAP := {"H": 2, "1": 3, "2": 2, "3": 2}
const START := {"H": "", "1": "KU", "2": "PG", "3": ""}
const GOAL := "PUK"
const SIDINGS := ["1", "2", "3"]

var tracks: Dictionary = {}
var w1 := false          # points 1: false = straight to siding 1, true = thrown towards points 2
var w2 := false          # points 2: false = straight to siding 2, true = thrown to siding 3
var phase := "home"      # "home" (engine on the headshunt) | "in" (coupled up in the siding)
var cut := 0             # phase "in": wagons the engine keeps
var trips := 0


func _init() -> void:
	reset()


func reset() -> void:
	tracks = START.duplicate()
	w1 = false
	w2 = false
	phase = "home"
	cut = 0
	trips = 0


func route() -> String:
	if not w1:
		return "1"
	return "3" if w2 else "2"


## Points can only be thrown while the engine is home (nothing stands on them).
func throw_points(n: int) -> bool:
	if phase != "home":
		return false
	if n == 1:
		w1 = not w1
	elif n == 2:
		w2 = not w2
	else:
		return false
	return true


## Sets both points for a siding ("1".."3").
func set_route(t: String) -> bool:
	if phase != "home" or not t in SIDINGS:
		return false
	w1 = t != "1"
	if t != "1":
		w2 = t == "3"
	return true


func combined() -> String:
	return str(tracks["H"]) + (str(tracks[route()]) if phase == "in" else "")


## Drive into the routed siding and couple up.
func enter() -> bool:
	if phase != "home":
		return false
	phase = "in"
	cut = str(tracks["H"]).length()
	return true


func set_cut(m: int) -> void:
	if phase == "in":
		cut = clampi(m, 0, combined().length())


## Pull back with `cut` wagons. Returns {ok, reason ("headshunt"|"siding"|""), changed, solved}.
func leave() -> Dictionary:
	if phase != "in":
		return {"ok": false, "reason": "phase", "changed": false, "solved": is_solved()}
	var comb := combined()
	var t := route()
	if cut > int(CAP["H"]):
		return {"ok": false, "reason": "headshunt", "changed": false, "solved": false}
	if comb.length() - cut > int(CAP[t]):
		return {"ok": false, "reason": "siding", "changed": false, "solved": false}
	var changed := comb.substr(0, cut) != str(tracks["H"])
	tracks["H"] = comb.substr(0, cut)
	tracks[t] = comb.substr(cut)
	phase = "home"
	cut = 0
	if changed:
		trips += 1
	return {"ok": true, "reason": "", "changed": changed, "solved": is_solved()}


func is_solved() -> bool:
	return str(tracks["1"]) == GOAL


func key() -> String:
	return "%s|%s|%s|%s" % [tracks["H"], tracks["1"], tracks["2"], tracks["3"]]


## Shortest plan from the current home state: [[siding, wagons_kept], ...] (empty when solved or unsolvable).
func solve() -> Array:
	if is_solved():
		return []
	var start := {"H": str(tracks["H"]), "1": str(tracks["1"]), "2": str(tracks["2"]), "3": str(tracks["3"])}
	var q: Array = [start]
	var prev := {_k(start): null}
	var head := 0
	while head < q.size():
		var s: Dictionary = q[head]
		head += 1
		if str(s["1"]) == GOAL:
			var path: Array = []
			var k := _k(s)
			while prev[k] != null:
				path.push_front(prev[k][1])
				k = prev[k][0]
			return path
		for t in SIDINGS:
			var comb: String = str(s["H"]) + str(s[t])
			for m in range(0, mini(int(CAP["H"]), comb.length()) + 1):
				var rest := comb.substr(m)
				if rest.length() > int(CAP[t]):
					continue
				if m == str(s["H"]).length() and rest == str(s[t]):
					continue
				var n := s.duplicate()
				n["H"] = comb.substr(0, m)
				n[t] = rest
				var nk := _k(n)
				if not prev.has(nk):
					prev[nk] = [_k(s), [t, m]]
					q.append(n)
	return []


static func _k(s: Dictionary) -> String:
	return "%s|%s|%s|%s" % [s["H"], s["1"], s["2"], s["3"]]
