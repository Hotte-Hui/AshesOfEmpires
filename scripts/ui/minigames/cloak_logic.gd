extends RefCounted
## Palais "Die Garderobe" — pure logic (used by cloak_game.gd and tests/test_minigames_r7_v.gd).
## Session break: everyone wants out at once and Herr Wenzel, garderobier since 1927, has hung the coats on the
## wrong hooks (the hook numbers no longer match the brass coat checks). Konrad hands out what belongs to whom,
## from small clues: the conference pin (shape: square Reich delegation, triangle Soviet delegation, diamond
## observers, circle commission), the newspaper in a pocket, the colour of a scarf.
##   Round 1 "Die Mäntel": four guests, five coats (one is Elena Weiss's and stays).
##   Round 2 "Die Hüte":   three of them come back for their hats, now wearing their coats; six hats.
## A wrong item is refused with a line that explains why (never a penalty; the game counts it for the hint).
## Mirrored in tools/pixelgen/gen_mg_cloak.py (COATS / HOOK_NUMBERS / HATS / TOKENS).

const COATS := ["loden", "camel", "elena", "navy", "karakul"]     # rack order, left -> right
const HOOK_NUMBERS := ["12", "7", "31", "44", "27"]               # the plates above those hooks
const HATS := ["ticket", "karakul", "beret", "pin", "ushanka", "green"]
const GUESTS := {
	"imhof": {"token": "12", "coat": "camel", "hat": "green", "pin": "diamond"},
	"orlova": {"token": "31", "coat": "karakul", "hat": "karakul", "pin": "triangle"},
	"duval": {"token": "7", "coat": "navy", "hat": "", "pin": "circle"},
	"bauer": {"token": "44", "coat": "loden", "hat": "pin", "pin": "square"},
}
const ROUNDS := [
	{"kind": "coat", "guests": ["imhof", "orlova", "duval", "bauer"]},
	{"kind": "hat", "guests": ["bauer", "imhof", "orlova"]},
]
## Special refusals "<guest>|<item>" -> line key (mg.cloak.say.<key>); otherwise mg.cloak.say.<guest>.wrong<round>.
const SPECIAL := {
	"imhof|loden": "imhof.hook12", "duval|elena": "duval.elena", "bauer|elena": "bauer.elena",
	"orlova|elena": "orlova.elena", "imhof|elena": "imhof.elena", "bauer|ticket": "bauer.ticket",
	"orlova|ushanka": "orlova.ushanka", "imhof|beret": "imhof.beret", "orlova|beret": "orlova.beret",
	"bauer|beret": "bauer.beret",
}
## What is left on the rack and the shelf at the end (Elena's coat and beret, two hats of delegates still talking).
const LEFT_COATS := ["elena"]
const LEFT_HATS := ["ticket", "beret", "ushanka"]
const ELENA_TOKEN := "27"

var round_i := 0
var guest_i := 0
var taken: Dictionary = {}     # "coat:camel" -> guest id
var refused := 0
var done := false


func _init() -> void:
	reset()


func reset() -> void:
	round_i = 0
	guest_i = 0
	taken = {}
	refused = 0
	done = false


## Starts the current round over (the coats of a finished round stay handed out).
func reset_round() -> void:
	var k := kind()
	for key in taken.keys():
		if str(key).begins_with(k + ":"):
			taken.erase(key)
	guest_i = 0


func kind() -> String:
	return str(ROUNDS[mini(round_i, ROUNDS.size() - 1)]["kind"])


func items() -> Array:
	return COATS if kind() == "coat" else HATS


func round_guests() -> Array:
	return ROUNDS[mini(round_i, ROUNDS.size() - 1)]["guests"]


func guest() -> String:
	if done:
		return ""
	return str(round_guests()[guest_i])


func available(item: String) -> bool:
	return not taken.has(kind() + ":" + item)


func available_items() -> Array:
	return items().filter(func(i): return available(str(i)))


## The item the current guest is looking for.
func wanted() -> String:
	var g := guest()
	return str(GUESTS[g][kind()]) if g != "" else ""


static func owner_of(item_kind: String, item: String) -> String:
	for g in GUESTS:
		if str(GUESTS[g][item_kind]) == item:
			return str(g)
	return ""


static func hook_of(coat: String) -> String:
	var i := COATS.find(coat)
	return str(HOOK_NUMBERS[i]) if i >= 0 else ""


## Hands `item` to the current guest. Returns {ok, guest, key (refusal / thanks line), round_done, solved,
## reason ("taken" | "wrong" | "done")}.
func give(item: String) -> Dictionary:
	if done:
		return {"ok": false, "reason": "done", "guest": "", "key": ""}
	var g := guest()
	if not available(item) or not items().has(item):
		return {"ok": false, "reason": "taken", "guest": g, "key": ""}
	if item != wanted():
		refused += 1
		var k := str(SPECIAL.get(g + "|" + item, "%s.wrong%d" % [g, round_i + 1]))
		return {"ok": false, "reason": "wrong", "guest": g, "key": k}
	taken[kind() + ":" + item] = g
	var thanks := "%s.thanks%d" % [g, round_i + 1]
	var r := round_i + 1
	guest_i += 1
	var round_done := false
	if guest_i >= round_guests().size():
		round_done = true
		guest_i = 0
		round_i += 1
		if round_i >= ROUNDS.size():
			done = true
	return {"ok": true, "reason": "", "guest": g, "key": thanks, "round": r, "round_done": round_done, "solved": done}


## The whole solution from the current state: [[kind, item], ...] in order (tests and the step hint).
func solution() -> Array:
	var out: Array = []
	for ri in range(round_i, ROUNDS.size()):
		var gs: Array = ROUNDS[ri]["guests"]
		var start := guest_i if ri == round_i else 0
		for gi in range(start, gs.size()):
			var k := str(ROUNDS[ri]["kind"])
			out.append([k, str(GUESTS[gs[gi]][k])])
	return out
