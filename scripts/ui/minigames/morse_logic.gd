extends RefCounted
## Pure logic of the Karsk mini-game "Der Morsetaster" (scenes/ui/minigames/MorseKey.tscn, morse_game.gd, §12.8).
## The dispatcher's telegram arrives as a timed transmission in Russian Morse (international timing: dot 1 unit,
## dash 3, gap inside a letter 1, between letters 3, between words 7). Routine groups ("auto") are taken down by
## Alexei by ear as they arrive; the TARGET groups are decoded by the player letter by letter with the wall chart
## (only letters that have already arrived). Then the receipt ACK is keyed on the key: a press shorter than DASH_AT
## is a dot, a longer one a dash, pauses never matter, a wrong element only restarts the current letter; the line
## answers REPLY and the game is solved. No time limit, nothing is ever lost.
## Driven by step(delta) (tests call it directly); every mutating call returns a small result Dictionary.

## The wall chart in display order (7 x 6): [letter, code, international (Latin) equivalent of the same code].
const TABLE := [
	["А", ".-", "A"], ["Б", "-...", "B"], ["В", ".--", "W"], ["Г", "--.", "G"], ["Д", "-..", "D"], ["Е", ".", "E"],
	["Ж", "...-", "V"], ["З", "--..", "Z"], ["И", "..", "I"], ["Й", ".---", "J"], ["К", "-.-", "K"], ["Л", ".-..", "L"],
	["М", "--", "M"], ["Н", "-.", "N"], ["О", "---", "O"], ["П", ".--.", "P"], ["Р", ".-.", "R"], ["С", "...", "S"],
	["Т", "-", "T"], ["У", "..-", "U"], ["Ф", "..-.", "F"], ["Х", "....", "H"], ["Ц", "-.-.", "C"], ["Ч", "---.", "Ö"],
	["Ш", "----", "CH"], ["Щ", "--.-", "Q"], ["Ъ", "--.--", "Ñ"], ["Ы", "-.--", "Y"], ["Ь", "-..-", "X"],
	["Э", "..-..", "É"], ["Ю", "..--", "Ü"], ["Я", ".-.-", "Ä"], ["1", ".----", "1"], ["2", "..---", "2"],
	["3", "...--", "3"], ["4", "....-", "4"], ["5", ".....", "5"], ["6", "-....", "6"], ["7", "--...", "7"],
	["8", "---..", "8"], ["9", "----.", "9"], ["0", "-----", "0"],
]
const COLS := 7
const ROWS := 6
## The incoming telegram (after the line that was already taken down before the duty officer went for tea).
const GROUPS := [{"text": "ВАГ", "auto": true}, {"text": "24311", "auto": true},
	{"text": "НЕ", "auto": false}, {"text": "ВЗВЕШИВАТЬ", "auto": false}]
## Receipt: ПР = «принял», received.
const ACK := "ПР"
## The line's answer to the receipt.
const REPLY := "Р"
const ROUTINE_UNIT := 0.06       # routine is sent fast
const TARGET_UNIT := 0.095       # the unusual words come slower, as if the sender wanted to be sure
const REPLY_UNIT := 0.07
const LEAD_IN := 1.5             # the call bell rings before the first element
const DASH_AT := 0.26            # a press this long or longer is a dash

var t := 0.0
var letters: Array = []          # [{ch, code, group, auto, t0, t1, els: [[on, off], ...]}]
var targets: Array = []          # letter indexes of the groups to decode (in order)
var cursor := 0                  # next target (index into targets)
var decoded := ""
var phase := "decode"            # decode -> answer -> reply -> done
var end_t := 0.0                 # end of the transmission
var ack_codes: Array = []        # [[letter, code], ...] of ACK
var ack_letter := 0
var ack_elem := 0
var reply_t := -1.0
var reply_els: Array = []
var wrong_picks := 0
var wrong_keys := 0
var _announced := {}             # letter index -> true once "arrived" was emitted
var _bell_done := false


func _init() -> void:
	reset()


static func code_of(ch: String) -> String:
	for row in TABLE:
		if str(row[0]) == ch:
			return str(row[1])
	return ""


static func table_index(ch: String) -> int:
	for i in TABLE.size():
		if str(TABLE[i][0]) == ch:
			return i
	return -1


static func cell_of(i: int) -> Vector2i:
	return Vector2i(i % COLS, i / COLS)


## Element on/off times of `code` starting at `start` with `unit` seconds per dot.
static func timeline(code: String, unit: float, start := 0.0) -> Array:
	var out: Array = []
	var at := start
	for i in code.length():
		var ln := unit if code[i] == "." else unit * 3.0
		out.append([at, at + ln])
		at += ln + unit
	return out


func reset() -> void:
	t = 0.0
	letters.clear()
	targets.clear()
	cursor = 0
	decoded = ""
	phase = "decode"
	ack_letter = 0
	ack_elem = 0
	reply_t = -1.0
	reply_els = []
	wrong_picks = 0
	wrong_keys = 0
	_announced = {}
	_bell_done = false
	var at := LEAD_IN
	for gi in GROUPS.size():
		var g: Dictionary = GROUPS[gi]
		var unit := ROUTINE_UNIT if bool(g["auto"]) else TARGET_UNIT
		var txt := str(g["text"])
		for li in txt.length():
			var ch := txt[li]
			var code := code_of(ch)
			var els := timeline(code, unit, at)
			var t1: float = float(els[-1][1])
			if not bool(g["auto"]):
				targets.append(letters.size())
			letters.append({"ch": ch, "code": code, "group": gi, "auto": bool(g["auto"]), "t0": at, "t1": t1, "els": els})
			at = t1 + unit * (3.0 if li < txt.length() - 1 else 7.0)
	end_t = float(letters[-1]["t1"])
	ack_codes.clear()
	for i in ACK.length():
		ack_codes.append([ACK[i], code_of(ACK[i])])


# ================================================================ time
## Advances the clock; returns events in order: "bell", "on", "off", "arrived:<i>", "end", "reply_on", "reply_off",
## "done". Large deltas are fine (several elements may pass at once).
func step(delta: float) -> Array:
	var ev: Array = []
	var t0 := t
	t += delta
	if not _bell_done:
		_bell_done = true
		ev.append("bell")
	for i in letters.size():
		var l: Dictionary = letters[i]
		if float(l["t1"]) < t0 - 0.0001 and _announced.has(i):
			continue
		for e in l["els"]:
			if float(e[0]) > t0 and float(e[0]) <= t:
				ev.append("on")
			if float(e[1]) > t0 and float(e[1]) <= t:
				ev.append("off")
		if not _announced.has(i) and t >= float(l["t1"]):
			_announced[i] = true
			ev.append("arrived:%d" % i)
	if t0 < end_t and t >= end_t:
		ev.append("end")
	if phase == "reply":
		var r0 := reply_t
		reply_t += delta
		for e in reply_els:
			if float(e[0]) > r0 and float(e[0]) <= reply_t:
				ev.append("reply_on")
			if float(e[1]) > r0 and float(e[1]) <= reply_t:
				ev.append("reply_off")
		if reply_t >= float(reply_els[-1][1]) + 0.35:
			phase = "done"
			ev.append("done")
	return ev


func transmitting() -> bool:
	return t < end_t


## The line is "on" (sounder down, lamp lit) at the current time.
func signal_on() -> bool:
	for l in letters:
		if t < float(l["t0"]) or t > float(l["t1"]):
			continue
		for e in l["els"]:
			if t >= float(e[0]) and t < float(e[1]):
				return true
	if phase == "reply":
		for e in reply_els:
			if reply_t >= float(e[0]) and reply_t < float(e[1]):
				return true
	return false


func arrived(li: int) -> bool:
	return li >= 0 and li < letters.size() and t >= float(letters[li]["t1"])


## Letter index of the target to decode next (-1 when all are decoded).
func current_letter() -> int:
	return int(targets[cursor]) if cursor < targets.size() else -1


func wanted_code() -> String:
	var li := current_letter()
	return str(letters[li]["code"]) if li >= 0 else ""


func can_pick() -> bool:
	return phase == "decode" and arrived(current_letter())


# ================================================================ decoding
## The player picks `ch` from the chart for the current target. {ok, reason, code, other}: reason "phase",
## "wait" (the letter has not arrived yet) or "wrong" (code = the code on the tape, other = the picked letter's).
func pick(ch: String) -> Dictionary:
	if phase != "decode":
		return {"ok": false, "reason": "phase"}
	var li := current_letter()
	if not arrived(li):
		return {"ok": false, "reason": "wait"}
	var want := str(letters[li]["code"])
	if ch != str(letters[li]["ch"]):
		wrong_picks += 1
		return {"ok": false, "reason": "wrong", "code": want, "other": code_of(ch)}
	decoded += ch
	cursor += 1
	var done := cursor >= targets.size()
	if done:
		phase = "answer"
	return {"ok": true, "done": done, "letter": li}


## Decoded text of a group so far ("" for nothing).
func group_text(gi: int) -> String:
	var s := ""
	for i in letters.size():
		var l: Dictionary = letters[i]
		if int(l["group"]) != gi:
			continue
		if bool(l["auto"]):
			if arrived(i):
				s += str(l["ch"])
		else:
			var k := targets.find(i)
			if k >= 0 and k < cursor:
				s += str(l["ch"])
	return s


func letter_known(li: int) -> bool:
	var l: Dictionary = letters[li]
	if bool(l["auto"]):
		return arrived(li)
	var k := targets.find(li)
	return k >= 0 and k < cursor


# ================================================================ keying the receipt
## Expected next element of the receipt ("." / "-"), "" when complete.
func ack_expected() -> String:
	if ack_letter >= ack_codes.size():
		return ""
	return str(ack_codes[ack_letter][1])[ack_elem]


## One press of the key, `duration` seconds long. {ok, element, reason ("phase", "dot" = a dot was wanted,
## "dash" = a dash was wanted), letter, letter_done, done}.
func key(duration: float) -> Dictionary:
	var e := "." if duration < DASH_AT else "-"
	if phase != "answer":
		return {"ok": false, "reason": "phase", "element": e}
	var want := ack_expected()
	var ch := str(ack_codes[ack_letter][0])
	if e != want:
		wrong_keys += 1
		ack_elem = 0
		return {"ok": false, "reason": "dot" if want == "." else "dash", "element": e, "letter": ch}
	ack_elem += 1
	var letter_done := ack_elem >= str(ack_codes[ack_letter][1]).length()
	if letter_done:
		ack_letter += 1
		ack_elem = 0
	var done := ack_letter >= ack_codes.size()
	if done:
		phase = "reply"
		reply_t = -0.45
		reply_els = timeline(code_of(REPLY), REPLY_UNIT, 0.0)
	return {"ok": true, "element": e, "letter": ch, "letter_done": letter_done, "done": done}


## How many elements of the receipt are confirmed (for the boxes on the form).
func ack_confirmed() -> int:
	var n := 0
	for i in ack_letter:
		n += str(ack_codes[i][1]).length()
	return n + ack_elem


func ack_total() -> int:
	var n := 0
	for a in ack_codes:
		n += str(a[1]).length()
	return n
