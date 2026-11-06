extends RefCounted
## Bahnhof Veltrava "Die Fallblatttafel" — pure logic (used by flap_game.gd and tests/test_minigames_r7_v.gd).
## The top row of the arrivals board is jammed on Alexei's own train. Six flap drums (hour, minute tens, minute
## units, from, via, platform) each cycle a fixed list of flaps and only ever fall FORWARD. Four mechanical
## couplings make the order matter:
##   units -> tens  "carry"  (the units' driver pin takes the tens one flap along on 9 -> 0)
##   tens  -> hour  "drag"   (a bent flap hooks the hour drum: every tens flap also turns the hour)
##   from  -> via   "drag"   (every "aus" flap also turns "über")
##   track -> via   "drag"   (every "Gleis" flap also turns "über")
## Movements propagate (units -> tens -> hour). No cycles, so the line is always solvable: set the drivers
## before the driven drums (ORDER). The target is the special train of the printed timetable SHEET:
## 8:41 · MOSKVA über KARSK · Gleis 5. Mirrored in tools/pixelgen/gen_mg_flap.py (DRUMS / START / TARGET).

const IDS := ["hour", "tens", "units", "from", "via", "track"]
const FLAPS := [
	["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
		"20", "21", "22", "23"],
	["0", "1", "2", "3", "4", "5"],
	["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
	["", "BERLIN", "WIEN", "PRAG", "KORDON", "MINSK", "MOSKVA", "ZÜRICH", "STOCKHOLM", "HELSINKI"],
	["", "KORDON", "MINSK", "KARSK", "PRAG", "LINZ", "SMOLENSK", "KIEW"],
	["1", "2", "3", "4", "5", "6", "7", "8"],
]
const START := [17, 2, 7, 3, 0, 1]      # the jam: 17:27 · PRAG · – · Gleis 2
const TARGET := [8, 4, 1, 6, 3, 4]      # 8:41 · MOSKVA · KARSK · Gleis 5
const DRAG := {"tens": ["hour"], "from": ["via"], "track": ["via"]}
const CARRY := {"units": "tens"}
## A valid order: every driver before what it drives (the dynamic hint follows it).
const ORDER := ["units", "tens", "hour", "from", "track", "via"]
## The printed timetable (Ankunft): time, from, via, track, footnote. The board shows rows 2-4 of today
## (11.05, 14.30, 19.12); 9.17 runs on Sundays only, so it is not on the board on Wednesday 12 February.
const SHEET := [
	["7.52", "WIEN", "LINZ", "2", ""],
	["8.30", "BERLIN", "PRAG", "4", "1"],
	["8.41", "MOSKVA", "KARSK", "5", "1"],
	["9.17", "KORDON", "", "1", "2"],
	["11.05", "KORDON", "", "1", ""],
	["14.30", "WIEN", "LINZ", "2", ""],
	["19.12", "BERLIN", "PRAG", "4", ""],
	["21.17", "MOSKVA", "MINSK", "3", ""],
]
const TARGET_SHEET_ROW := 2

var pos: Array = START.duplicate()
var turns := 0
## Per drum: its current flap was set by hand (a direct turn). Only such a drum counts as "knocked off" when a
## coupling moves it away from the timetable flap -- a flap that came right by accident costs nothing.
var hand: Array = [false, false, false, false, false, false]
## Couplings the player has seen work ("units>tens", ...). Kept over a restart: Alexei does not forget.
var known: Dictionary = {}


func _init() -> void:
	reset()


func reset() -> void:
	pos = START.duplicate()
	turns = 0
	hand = [false, false, false, false, false, false]


static func index_of(id: String) -> int:
	return IDS.find(id)


static func flap_count(i: int) -> int:
	return (FLAPS[i] as Array).size()


func flap(i: int) -> String:
	return str(FLAPS[i][pos[i]])


static func target_flap(i: int) -> String:
	return str(FLAPS[i][TARGET[i]])


func on_target(i: int) -> bool:
	return int(pos[i]) == int(TARGET[i])


## Turns drum i one flap forward. Returns every movement in order:
## [{drum, from, to, by (driver index or -1), kind ("turn" | "drag" | "carry"), was_ok, now_ok, was_hand}]
func turn(i: int) -> Array:
	var moves: Array = []
	if i < 0 or i >= IDS.size():
		return moves
	_step(i, -1, "turn", moves)
	turns += 1
	return moves


func _step(i: int, by: int, kind: String, moves: Array) -> void:
	var was_ok := on_target(i)
	var was_hand := bool(hand[i])
	var a := int(pos[i])
	pos[i] = (a + 1) % flap_count(i)
	hand[i] = kind == "turn"
	moves.append({"drum": i, "from": a, "to": int(pos[i]), "by": by, "kind": kind, "was_ok": was_ok,
		"now_ok": on_target(i), "was_hand": was_hand})
	if by >= 0:
		known["%s>%s" % [IDS[by], IDS[i]]] = true
	var id: String = IDS[i]
	if CARRY.has(id) and int(pos[i]) == 0:
		_step(index_of(str(CARRY[id])), i, "carry", moves)
	for t in DRAG.get(id, []):
		_step(index_of(str(t)), i, "drag", moves)


## Moves of a turn() that knocked a drum off the flap the player had set by hand (each counts as a setback).
static func disturbed(moves: Array) -> Array:
	var out: Array = []
	for m in moves:
		if str(m["kind"]) != "turn" and bool(m["was_ok"]) and not bool(m["now_ok"]) and bool(m.get("was_hand", true)):
			out.append(m)
	return out


func is_solved() -> bool:
	for i in IDS.size():
		if not on_target(i):
			return false
	return true


## Drums that differ from the timetable line (indices).
func wrong() -> Array:
	var out: Array = []
	for i in IDS.size():
		if not on_target(i):
			out.append(i)
	return out


## Positions a timetable row would show on the board (-1 where the flap list has no such entry).
static func sheet_pos(row: Array) -> Array:
	var t := str(row[0]).split(".")
	var h := int(t[0])
	var m := int(t[1]) if t.size() > 1 else 0
	var vals := [str(h), str(m / 10), str(m % 10), str(row[1]), str(row[2]), str(row[3])]
	var out: Array = []
	for i in IDS.size():
		out.append((FLAPS[i] as Array).find(vals[i]))
	return out


## Index of the timetable row the board currently shows (-1: none).
func sheet_match() -> int:
	for r in SHEET.size():
		if sheet_pos(SHEET[r]) == pos:
			return r
	return -1


## Next drum in ORDER that is not on its flap (for the step hint; -1 when solved).
func next_drum() -> int:
	for id in ORDER:
		var i := index_of(str(id))
		if not on_target(i):
			return i
	return -1


## Forward distance of drum i to its target flap (ignoring couplings).
func distance(i: int) -> int:
	return posmod(int(TARGET[i]) - int(pos[i]), flap_count(i))


## A complete list of drum turns that solves the board from the current state (simulated on a copy).
func solve_plan() -> Array:
	var sim = (get_script() as GDScript).new()
	sim.pos = pos.duplicate()
	sim.hand = hand.duplicate()
	var plan: Array = []
	var guard := 0
	while not sim.is_solved() and guard < 400:
		var i: int = sim.next_drum()
		sim.turn(i)
		plan.append(i)
		guard += 1
	return plan


## Board text of the current line, e.g. "8:41 MOSKVA KARSK 5".
func line_text() -> String:
	var parts := ["%s:%s%s" % [flap(0), flap(1), flap(2)], flap(3), flap(4), flap(5)]
	return " ".join(parts.filter(func(s: String) -> bool: return s != ""))
