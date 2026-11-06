extends RefCounted
## Rule of the mini-game "Die Suchkartei" (scenes/ui/minigames/Kartei.tscn, find veltrava.registry.kartei, §12.8).
## A drawer of the commission's tracing index has fallen; nine cards lie on the floor. The drawer holds the three
## guide cards (B, K, V) and three cards that stayed in. Konrad files the nine back, one at a time: a card goes into
## exactly one gap -- after every item that sorts before it. Order of the commission: origin (B < K < V), then year,
## then running number. Four cards were filled in by Russian-speaking clerks: their origin letter is Cyrillic
## (Б = B, К = K, В = V -- and В looks like a Latin B). A wrong gap is refused with the rule it breaks; the card
## stays in the hand. Pure: no nodes, no randomness; the art mirror is tools/pixelgen/gen_mg_c3p2_kartei.py.

const ORIGINS := ["B", "K", "V"]
## id -> code as written, origin, year, running number, language of the clerk, result stamp
const CARDS := {
	"kranz": {"code": "B 61/22", "origin": "B", "year": 61, "num": 22, "lang": "de", "result": "none"},
	"ryschkowa": {"code": "K 62/05", "origin": "K", "year": 62, "num": 5, "lang": "de", "result": "none"},
	"petrauskas": {"code": "V 63/11", "origin": "V", "year": 63, "num": 11, "lang": "de", "result": "forwarded"},
	"kulikowa": {"code": "K 63/09", "origin": "K", "year": 63, "num": 9, "lang": "de", "result": "none"},
	"lacis": {"code": "В 62/08", "origin": "V", "year": 62, "num": 8, "lang": "ru", "result": "none"},
	"hrubes": {"code": "B 64/02", "origin": "B", "year": 64, "num": 2, "lang": "de", "result": "pending"},
	"wiebe": {"code": "Б 63/04", "origin": "B", "year": 63, "num": 4, "lang": "ru", "result": "forwarded"},
	"sorokin": {"code": "К 61/17", "origin": "K", "year": 61, "num": 17, "lang": "ru", "result": "none"},
	"wanek": {"code": "V 64/03", "origin": "V", "year": 64, "num": 3, "lang": "de", "result": "address"},
	"sell": {"code": "B 62/30", "origin": "B", "year": 62, "num": 30, "lang": "de", "result": "none"},
	"hartl": {"code": "В 63/15", "origin": "V", "year": 63, "num": 15, "lang": "ru", "result": "none"},
	"kowalenko": {"code": "К 63/21", "origin": "K", "year": 63, "num": 21, "lang": "ru", "result": "none"},
}
const GUIDES := {"guide_B": "B", "guide_K": "K", "guide_V": "V"}
## The drawer after the fall (left = front of the drawer).
const START := ["guide_B", "kranz", "guide_K", "ryschkowa", "guide_V", "petrauskas"]
## The cards on the floor, in the order the floor shows them (cursor order).
const FLOOR := ["kulikowa", "lacis", "hrubes", "wiebe", "sorokin", "wanek", "sell", "hartl", "kowalenko"]
## The origin of each written letter (the clerk's alphabet decides how it looks, not what it means).
const LETTERS := {"B": "B", "K": "K", "V": "V", "Б": "B", "К": "K", "В": "V"}

var drawer: Array = []
var floor: Array = []
var held := ""
var done := false
var filed: Array = []        # card ids in the order they were filed


func _init() -> void:
	reset()


func reset() -> void:
	drawer = START.duplicate()
	floor = FLOOR.duplicate()
	held = ""
	done = false
	filed = []


static func is_guide(id: String) -> bool:
	return GUIDES.has(id)


## [origin index, year, number]; a guide sorts before every card of its origin.
static func key(id: String) -> Array:
	if GUIDES.has(id):
		return [ORIGINS.find(str(GUIDES[id])), -1, -1]
	var c: Dictionary = CARDS.get(id, {})
	return [ORIGINS.find(str(c.get("origin", ""))), int(c.get("year", 0)), int(c.get("num", 0))]


static func less(a: String, b: String) -> bool:
	var ka := key(a)
	var kb := key(b)
	for i in 3:
		if int(ka[i]) != int(kb[i]):
			return int(ka[i]) < int(kb[i])
	return false


static func code(id: String) -> String:
	return str(CARDS[id]["code"]) if CARDS.has(id) else ""


static func lang(id: String) -> String:
	return str(CARDS.get(id, {}).get("lang", ""))


static func origin(id: String) -> String:
	return str(GUIDES[id]) if GUIDES.has(id) else str(CARDS.get(id, {}).get("origin", ""))


## The letter as it is written on the card (Cyrillic for the Russian clerks).
static func written_letter(id: String) -> String:
	return code(id).substr(0, 1)


## The one gap (0 = before the first item, drawer.size() = after the last) where card `id` belongs right now.
func valid_gap(id: String) -> int:
	var n := 0
	for it in drawer:
		if less(str(it), id):
			n += 1
	return n


## Origin of the section a gap opens into: the last guide card before it ("" = in front of guide B).
func section_at(gap: int) -> String:
	var s := ""
	for i in mini(gap, drawer.size()):
		if is_guide(str(drawer[i])):
			s = origin(str(drawer[i]))
	return s


## [left item id or "", right item id or ""] of a gap.
func neighbors(gap: int) -> Array:
	var l := str(drawer[gap - 1]) if gap > 0 and gap <= drawer.size() else ""
	var r := str(drawer[gap]) if gap >= 0 and gap < drawer.size() else ""
	return [l, r]


func take(id: String) -> bool:
	if done or not (id in floor):
		return false
	held = id
	return true


func put_back() -> bool:
	if held == "":
		return false
	held = ""
	return true


## Files the held card at `gap`. {ok, reason, card, gap, valid}; reasons: "" (filed), "nothing_held", "origin",
## "cyr_v" (a Cyrillic В outside V -- the B/V trap), "cyr_b", "cyr_k" (other Cyrillic letters outside their
## section), "year", "number". A refused card stays in the hand.
func insert(gap: int) -> Dictionary:
	var out := {"ok": false, "reason": "nothing_held", "card": held, "gap": gap, "valid": -1}
	if held == "" or done:
		return out
	var v := valid_gap(held)
	out["valid"] = v
	if gap == v:
		drawer.insert(gap, held)
		floor.erase(held)
		filed.append(held)
		out["ok"] = true
		out["reason"] = ""
		held = ""
		done = floor.is_empty()
		return out
	out["reason"] = refusal(held, gap)
	return out


## Why card `id` cannot go into `gap` (the first rule it breaks).
func refusal(id: String, gap: int) -> String:
	var o := origin(id)
	if section_at(gap) != o:
		if lang(id) == "ru":
			match o:
				"V":
					return "cyr_v"
				"B":
					return "cyr_b"
				_:
					return "cyr_k"
		return "origin"
	var nb := neighbors(gap)
	var y := int(CARDS[id]["year"])
	var l := str(nb[0])
	var r := str(nb[1])
	if (l != "" and not is_guide(l) and int(CARDS[l]["year"]) > y) or \
			(r != "" and not is_guide(r) and origin(r) == o and int(CARDS[r]["year"]) < y):
		return "year"
	return "number"


## True when every card is in and the drawer is in commission order.
func is_sorted() -> bool:
	for i in range(1, drawer.size()):
		if not less(str(drawer[i - 1]), str(drawer[i])):
			return false
	return floor.is_empty() and held == ""


## The final order (for tests and the close-up): every item sorted.
static func solved_order() -> Array:
	var all: Array = GUIDES.keys() + CARDS.keys()
	all.sort_custom(func(a, b): return less(str(a), str(b)))
	return all
