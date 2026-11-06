extends RefCounted
## Rule of the mini-game "Der Hebelrahmen" (scenes/ui/minigames/LeverFrame.tscn, explore entry
## karsk.tunnels.lever_frame at exp_lever_frame in L_C4_Tunnels, TECHNICAL_ARCHITECTURE §12.8, documentation/C4_DESIGN.md
## §6). A fictional 1941 mechanical lever frame beside switch W2 in Service Tunnel 3 under the Karsk freight yard -- a
## teaching frame, not a copy of a real type. Eight levers, each either normal (back) or reversed (pulled):
##   w1  points at the tunnel mouth      normal = track 1, reversed = track 2
##   w2  points at the exit end          normal = track 1, reversed = track 2
##   w3  exit points                     normal = main line, reversed = track 0 (the track without a number)
##   a   route lever "entry track 1"     needs w1 normal
##   b   route lever "exit main line"    needs w1 reversed (flank protection for track 1), w2 normal, w3 normal
##   c   route lever without a plate     needs w1 reversed, w2 normal, w3 reversed
##   s1  entry signal                    needs route a
##   s2  exit signal                     needs route b or c
## Interlocking (the frame's mechanical locks, shown as the "Verschlusstafel"): a pulled route lever holds its points;
## b and c exclude each other (both leave track 1 over w2); a pulled signal holds its route lever; a signal goes back
## to danger at any time. Three orders from the night shift's route book; an order is carried out when exactly its
## route and its signal are pulled (no other route or signal lever). The points are not checked: the locks already
## make them right. Pure: no nodes, no randomness; next_move() (breadth-first, lever order on ties) serves the hints
## and the input driver.

const LEVERS := ["w1", "w2", "w3", "a", "b", "c", "s1", "s2"]
const KIND := {"w1": "points", "w2": "points", "w3": "points", "a": "route", "b": "route", "c": "route",
	"s1": "signal", "s2": "signal"}
## Route lever -> {points lever: must be reversed?}
const NEEDS := {"a": {"w1": false}, "b": {"w1": true, "w2": false, "w3": false},
	"c": {"w1": true, "w2": false, "w3": true}}
const SIGNAL_OF := {"a": "s1", "b": "s2", "c": "s2"}
const ROUTES_OF := {"s1": ["a"], "s2": ["b", "c"]}
const CONFLICTS := {"a": [], "b": ["c"], "c": ["b"]}
## How the night shift left the frame: every points lever reversed, no route, both signals at danger.
const START := {"w1": true, "w2": true, "w3": true}
const ORDERS := [
	{"id": "entry", "route": "a", "signal": "s1"},
	{"id": "main", "route": "b", "signal": "s2"},
	{"id": "zero", "route": "c", "signal": "s2"},
]

var pulled: Dictionary = {}
var order := 0
## True between the move that carried out an order and next_order() (the game holds a short beat there).
var order_complete := false
var done := false
var moves := 0
var refusals := 0


func _init() -> void:
	reset()


func reset() -> void:
	pulled = {}
	for id in LEVERS:
		pulled[id] = bool(START.get(id, false))
	order = 0
	order_complete = false
	done = false
	moves = 0
	refusals = 0


static func index_of(id: String) -> int:
	return LEVERS.find(id)


## Number on the lever's plate (1-8).
static func number_of(id: String) -> int:
	return LEVERS.find(id) + 1


func is_pulled(id: String) -> bool:
	return bool(pulled.get(id, false))


func current() -> Dictionary:
	return ORDERS[mini(order, ORDERS.size() - 1)]


## Would toggling lever `id` be allowed now? {ok, reason, by}: reason "" | "points_locked" (by = the route holding it)
## | "route_conflict" (by = the other route) | "route_points" (by = the first points lever lying wrong) | "route_held"
## (by = the signal holding it) | "signal_no_route" | "unknown".
func check(id: String) -> Dictionary:
	return _check_in(pulled, id)


static func _check_in(st: Dictionary, id: String) -> Dictionary:
	if not KIND.has(id):
		return {"ok": false, "reason": "unknown", "by": ""}
	var on := bool(st.get(id, false))
	match str(KIND[id]):
		"points":
			for r in ["a", "b", "c"]:
				if bool(st.get(r, false)) and (NEEDS[r] as Dictionary).has(id):
					return {"ok": false, "reason": "points_locked", "by": r}
		"route":
			if on:
				var s := str(SIGNAL_OF[id])
				if bool(st.get(s, false)):
					return {"ok": false, "reason": "route_held", "by": s}
			else:
				for o in CONFLICTS[id]:
					if bool(st.get(o, false)):
						return {"ok": false, "reason": "route_conflict", "by": str(o)}
				var needs: Dictionary = NEEDS[id]
				for p in ["w1", "w2", "w3"]:
					if needs.has(p) and bool(st.get(p, false)) != bool(needs[p]):
						return {"ok": false, "reason": "route_points", "by": p}
		"signal":
			if not on:
				var any := false
				for r in ROUTES_OF[id]:
					any = any or bool(st.get(r, false))
				if not any:
					return {"ok": false, "reason": "signal_no_route", "by": ""}
	return {"ok": true, "reason": "", "by": ""}


## Toggles lever `id` when the locks allow it. {ok, reason, by, pulled, round_done, solved}. A refusal changes
## nothing but the refusal counter; nothing moves while an order is complete (order_complete) or after the last one.
func toggle(id: String) -> Dictionary:
	if done or order_complete:
		return {"ok": false, "reason": "busy", "by": "", "pulled": is_pulled(id), "order_done": false, "solved": done}
	var c := check(id)
	if not bool(c["ok"]):
		refusals += 1
		c["pulled"] = is_pulled(id)
		c["order_done"] = false
		c["solved"] = false
		return c
	pulled[id] = not is_pulled(id)
	moves += 1
	var met := order_met()
	if met:
		order_complete = true
	return {"ok": true, "reason": "", "by": "", "pulled": is_pulled(id), "order_done": met,
		"solved": met and order == ORDERS.size() - 1}


## The current order is carried out: its route and its signal pulled, every other route and signal lever back.
func order_met() -> bool:
	return _met_in(pulled, current())


static func _met_in(st: Dictionary, rd: Dictionary) -> bool:
	for id in ["a", "b", "c", "s1", "s2"]:
		var want: bool = id == str(rd["route"]) or id == str(rd["signal"])
		if bool(st.get(id, false)) != want:
			return false
	return true


## After a carried-out order: the next one (or the end).
func next_order() -> void:
	if not order_complete:
		return
	order_complete = false
	if order >= ORDERS.size() - 1:
		done = true
		return
	order += 1


## The lever to move next on a shortest way to the current order ("" when it is carried out or nothing helps).
func next_move() -> String:
	var path := plan()
	return str(path[0]) if not path.is_empty() else ""


## Shortest list of lever toggles from the current position to the current order (breadth-first over the 256
## positions, levers tried in frame order, so the plan is deterministic).
func plan() -> Array:
	var goal := current()
	if _met_in(pulled, goal):
		return []
	var start := _encode(pulled)
	var prev := {start: [-1, ""]}
	var queue: Array = [start]
	var head := 0
	while head < queue.size():
		var code: int = queue[head]
		head += 1
		var st := _decode(code)
		for id in LEVERS:
			if not bool(_check_in(st, id)["ok"]):
				continue
			var nx := code ^ (1 << LEVERS.find(id))
			if prev.has(nx):
				continue
			prev[nx] = [code, id]
			if _met_in(_decode(nx), goal):
				var path: Array = []
				var at := nx
				while at != start:
					path.push_front(str(prev[at][1]))
					at = int(prev[at][0])
				return path
			queue.append(nx)
	return []


static func _encode(st: Dictionary) -> int:
	var code := 0
	for i in LEVERS.size():
		if bool(st.get(LEVERS[i], false)):
			code |= 1 << i
	return code


static func _decode(code: int) -> Dictionary:
	var st := {}
	for i in LEVERS.size():
		st[LEVERS[i]] = (code >> i) & 1 == 1
	return st


## Levers that cannot move right now (the plates show a lock pip): {id: reason}.
func locked() -> Dictionary:
	var out := {}
	for id in LEVERS:
		var c := check(id)
		if not bool(c["ok"]):
			out[id] = str(c["reason"])
	return out


## The whole solution from the night shift's position (for tests / documentation): one list per order.
static func solution() -> Array:
	var lg = load("res://scripts/ui/minigames/lever_logic.gd").new()
	var out: Array = []
	for i in ORDERS.size():
		var p: Array = lg.plan()
		out.append(p)
		for id in p:
			lg.toggle(str(id))
		lg.next_order()
	return out
