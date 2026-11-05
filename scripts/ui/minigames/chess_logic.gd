extends RefCounted
## Karsk "Die Schachpartie" — the shift game under the signal-box stairs as a mate-in-2 problem (pure logic,
## used by chess_game.gd and tests/test_minigames.gd). The day shift (White) is to move; the night shift has more
## material and its own checks in reserve, so only a forcing line works:
##   1. Qc4-g8+  Re8xg8 (forced: g8 is covered by the knight, the king has no square)  2. Nh6-f7# (smothered mate)
## Every other White move is refused with a reason (illegal geometry, night-shift piece, too slow, Nf7+ Kg8 ...).
## Board: {"e4": "wK"} — colour w/b + K Q R B N P. Only White moves are generated; Black's reply is scripted.

const START := {"g1": "wK", "c4": "wQ", "h6": "wN", "f2": "wP", "g2": "wP", "h2": "wP",
	"h8": "bK", "e8": "bR", "a8": "bR", "b2": "bQ", "a7": "bP", "b7": "bP", "g7": "bP", "h7": "bP"}
const KEY_MOVE := ["c4", "g8"]
const REPLY := ["e8", "g8"]
const MATE := ["h6", "f7"]
const FILES := "abcdefgh"

var board: Dictionary = {}
var phase := 0            # 0 key move, 1 night shift replies, 2 mating move, 3 mate
var last_move: Array = []
var history: Array = []   # notation keys of the moves played (mg.chess.line.*)


func _init() -> void:
	reset()


func reset() -> void:
	board = START.duplicate()
	phase = 0
	last_move = []
	history = []


func piece_at(sq: String) -> String:
	return str(board.get(sq, ""))


static func sq_name(f: int, r: int) -> String:
	return FILES[f] + str(r + 1)


static func coords(sq: String) -> Vector2i:
	return Vector2i(FILES.find(sq[0]), int(sq.substr(1)) - 1)


static func on_board(c: Vector2i) -> bool:
	return c.x >= 0 and c.x < 8 and c.y >= 0 and c.y < 8


func _path_clear(a: Vector2i, b: Vector2i, bd: Dictionary) -> bool:
	var d := Vector2i(signi(b.x - a.x), signi(b.y - a.y))
	var c := a + d
	while c != b:
		if bd.has(sq_name(c.x, c.y)):
			return false
		c += d
	return true


## Geometry + blocking + no own capture (no king-safety check: not needed for the problem's feedback).
func pseudo_legal(from: String, to: String, bd: Dictionary = {}) -> bool:
	if bd.is_empty():
		bd = board
	var p := str(bd.get(from, ""))
	if p == "" or from == to:
		return false
	var a := coords(from)
	var b := coords(to)
	if not on_board(a) or not on_board(b):
		return false
	var tgt := str(bd.get(to, ""))
	if tgt != "" and tgt[0] == p[0]:
		return false
	var dx := b.x - a.x
	var dy := b.y - a.y
	match p[1]:
		"N":
			return (absi(dx) == 1 and absi(dy) == 2) or (absi(dx) == 2 and absi(dy) == 1)
		"K":
			return maxi(absi(dx), absi(dy)) == 1
		"R":
			return (dx == 0 or dy == 0) and _path_clear(a, b, bd)
		"B":
			return absi(dx) == absi(dy) and _path_clear(a, b, bd)
		"Q":
			return (dx == 0 or dy == 0 or absi(dx) == absi(dy)) and _path_clear(a, b, bd)
		"P":
			var fwd := 1 if p[0] == "w" else -1
			if dx == 0 and dy == fwd and tgt == "":
				return true
			if dx == 0 and dy == 2 * fwd and tgt == "" and a.y == (1 if fwd == 1 else 6):
				return _path_clear(a, b, bd)
			return absi(dx) == 1 and dy == fwd and tgt != ""
	return false


func targets(from: String) -> Array:
	var out: Array = []
	for f in 8:
		for r in 8:
			var s := sq_name(f, r)
			if pseudo_legal(from, s):
				out.append(s)
	return out


## Does White give check after from->to?
func gives_check(from: String, to: String) -> bool:
	var bd := board.duplicate()
	bd[to] = bd[from]
	bd.erase(from)
	var king := ""
	for s in bd:
		if str(bd[s]) == "bK":
			king = s
	if king == "":
		return false
	for s in bd:
		if str(bd[s])[0] == "w" and pseudo_legal(s, king, bd):
			return true
	return false


## Player move. Returns {ok, reason, mate}; reasons: wait, empty, night, illegal, slow, nf7, check, nomate, nxg8.
func try_move(from: String, to: String) -> Dictionary:
	if phase != 0 and phase != 2:
		return {"ok": false, "reason": "wait", "mate": false}
	var p := piece_at(from)
	if p == "":
		return {"ok": false, "reason": "empty", "mate": false}
	if p[0] != "w":
		return {"ok": false, "reason": "night", "mate": false}
	if not pseudo_legal(from, to):
		return {"ok": false, "reason": "illegal", "mate": false}
	if phase == 0:
		if [from, to] == KEY_MOVE:
			_apply(from, to)
			history.append("mg.chess.line.1w")
			phase = 1
			return {"ok": true, "reason": "", "mate": false}
		if [from, to] == MATE:
			return {"ok": false, "reason": "nf7", "mate": false}
		return {"ok": false, "reason": "check" if gives_check(from, to) else "slow", "mate": false}
	if [from, to] == MATE:
		_apply(from, to)
		history.append("mg.chess.line.2w")
		phase = 3
		return {"ok": true, "reason": "", "mate": true}
	if from == "h6" and to == "g8":
		return {"ok": false, "reason": "nxg8", "mate": false}
	return {"ok": false, "reason": "nomate", "mate": false}


## The night shift's forced reply (phase 1 -> 2). Returns [from, to].
func reply() -> Array:
	if phase != 1:
		return []
	_apply(REPLY[0], REPLY[1])
	history.append("mg.chess.line.1b")
	phase = 2
	return REPLY


func is_mate() -> bool:
	return phase == 3


func _apply(from: String, to: String) -> void:
	board[to] = board[from]
	board.erase(from)
	last_move = [from, to]
