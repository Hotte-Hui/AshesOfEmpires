extends RefCounted
## Rule of the annex mini-game „Die Lüftungsklappen“ (scripts/ui/minigames/vent_game.gd, scenes/ui/minigames/
## VentFlaps.tscn; explore entry berlin.annex.fans at exp_fans in L_C4_Annex, scene D; documentation/C4_DESIGN.md §6,
## TECHNICAL_ARCHITECTURE §12.8). Pure logic, no nodes: the game script draws it, the tests drive it.
##
## The machine room of Nebenstelle Süd: two fans blow into one plenum, three ducts leave it -- the card hall, the
## typists' room and the corridor of the Staatspolizei (its waiting room). Each duct has a butterfly flap with five
## positions (0 = zu … 4 = ganz auf). The fans deliver more air the more the system is open (a simple fan curve):
##     g_i = COND_i · pos_i,  G = Σ g_i,  flow_i = QMAX · g_i / (G + FAN_K)   (thousand m³/h)
## so every flap moves all three needles: opening one duct takes air from the other two. The corridor duct is twice as
## long (COND 0.5): its flap must stand wider than the typists' to carry the same air. Konrad's own sheet (Blatt 3)
## names the design flows TARGET; a flow within ±TOL of its target is „im grünen Feld“. Exactly one of the 125
## positions puts all three in their bands (checked by solutions(), tests/test_c4_explore.gd); the night shift left
## START (card hall right, typists' room far too much, corridor nothing), so the alarm rings. No dead end: every
## position reaches the solution one flap step at a time.

const FLAPS := ["hall", "typing", "corridor"]
const MAX_POS := 4
const COND := {"hall": 1.0, "typing": 1.0, "corridor": 0.5}
const QMAX := 30.0
const FAN_K := 2.0
const TARGET := {"hall": 12.0, "typing": 6.0, "corridor": 6.0}
const TOL := 1.0
const START := {"hall": 4, "typing": 4, "corridor": 0}
const SOLUTION := {"hall": 4, "typing": 2, "corridor": 4}

var pos: Dictionary = {}
var moves := 0
var done := false


func _init() -> void:
	reset()


func reset() -> void:
	pos = START.duplicate()
	moves = 0
	done = false


static func index_of(flap: String) -> int:
	return FLAPS.find(flap)


static func number_of(flap: String) -> int:
	return FLAPS.find(flap) + 1


## Airflow per duct (thousand m³/h) for a position dictionary (default: the current one).
static func flows_of(p: Dictionary) -> Dictionary:
	var g := {}
	var total := 0.0
	for f in FLAPS:
		g[f] = float(COND[f]) * float(p.get(f, 0))
		total += float(g[f])
	var out := {}
	for f in FLAPS:
		out[f] = QMAX * float(g[f]) / (total + FAN_K)
	return out


func flows() -> Dictionary:
	return flows_of(pos)


## Total air of both fans (thousand m³/h): drives the fan animation.
func total_flow() -> float:
	var s := 0.0
	var fl := flows()
	for f in FLAPS:
		s += float(fl[f])
	return s


## -1 too little air, 0 in the green band, +1 too much -- per duct.
static func state_of(p: Dictionary) -> Dictionary:
	var fl := flows_of(p)
	var out := {}
	for f in FLAPS:
		var d := float(fl[f]) - float(TARGET[f])
		out[f] = 0 if absf(d) <= TOL + 0.0001 else (1 if d > 0.0 else -1)
	return out


func states() -> Dictionary:
	return state_of(pos)


static func is_balanced(p: Dictionary) -> bool:
	for v in state_of(p).values():
		if int(v) != 0:
			return false
	return true


func balanced() -> bool:
	return is_balanced(pos)


## One step on a flap: d = +1 opens, -1 closes. {ok, flap, pos, reason ("open" / "closed" at the end stop)}.
func step(flap: String, d: int) -> Dictionary:
	if not COND.has(flap) or done:
		return {"ok": false, "flap": flap, "reason": "none"}
	var cur := int(pos[flap])
	var nv := clampi(cur + signi(d), 0, MAX_POS)
	if nv == cur:
		return {"ok": false, "flap": flap, "pos": cur, "reason": "open" if d > 0 else "closed"}
	pos[flap] = nv
	moves += 1
	return {"ok": true, "flap": flap, "pos": nv, "balanced": balanced()}


## The alarm is acknowledged: only in balance. {ok, worst (the duct furthest from its band), dir (-1 / +1)}.
func acknowledge() -> Dictionary:
	if done:
		return {"ok": true}
	if balanced():
		done = true
		return {"ok": true}
	var fl := flows()
	var worst := ""
	var worst_d := -1.0
	for f in FLAPS:
		var d := absf(float(fl[f]) - float(TARGET[f])) - TOL
		if d > worst_d:
			worst_d = d
			worst = f
	var st := states()
	return {"ok": false, "worst": worst, "dir": int(st[worst])}


## The next flap step toward the solution (first duct in order that differs): {flap, dir} or {} when there.
func next_move() -> Dictionary:
	for f in FLAPS:
		var want := int(SOLUTION[f])
		var cur := int(pos[f])
		if cur != want:
			return {"flap": f, "dir": 1 if want > cur else -1}
	return {}


## Every position whose three flows lie in their bands (the rule promises exactly one: SOLUTION).
static func solutions() -> Array:
	var out: Array = []
	for a in MAX_POS + 1:
		for b in MAX_POS + 1:
			for c in MAX_POS + 1:
				var p := {"hall": a, "typing": b, "corridor": c}
				if is_balanced(p):
					out.append(p)
	return out
