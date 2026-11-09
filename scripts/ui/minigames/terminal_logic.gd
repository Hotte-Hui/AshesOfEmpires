extends RefCounted
## Rule of the mini-game „Die Datenstelle“ (scenes/ui/minigames/DataTerminal.tscn, explore entry
## berlin.annex.term_files at the data desk of Nebenstelle Süd, L_C4_Annex scene D; TECHNICAL_ARCHITECTURE §12.8).
## A 1964 data desk as a menu-driven text screen — nothing is typed but the operator number:
##   login    four digit wheels; the number is the one Konrad read on the duty roster (OPERATOR)
##   menu     the command set: LISTE (the tape's directory), ÖFFNEN (read a file), SUCHEN (a keyword in all files)
##   open     five files and the locked program „Planspiel Abgang“; choosing the program asks for its release
##   release  the case number of the household Wendt's memo means: the one whose „Verbleib“ is open in the transfer
##            list C-17/45 (ANSWER) — the cross-reference of two files; the case numbers are only offered once the
##            list has been read (or found by a search)
## Texts come from the locale through `tr_fn` (key, args) -> String, so the search works on what the player reads in
## either language; the file bodies are "mg.term.file.<id>" with one line per row (at most 46 characters).
## screen(cols, rows) lays the current state out as text runs for crt_kit.raster(); every action returns an event
## name for the game's sounds and status ("" = nothing happened).

const OPERATOR := "2741"
const ANSWER := "S8-067"
const FILES := ["ueb45", "ueb44", "vermerk", "buch", "schema"]
const PROGRAM := "abgang"
const COMMANDS := ["list", "open", "search"]
const KEYWORDS := 5
const CASE_PREFIX := "S8-"
const CASE_FILE := "ueb45"
const MAX_RESULTS := 9
const MAX_LINE := 46

var tr_fn := Callable()
var phase := "login"
var digits: Array = [0, 0, 0, 0]
var digit_cursor := 0
var cursor := 0
var view_file := ""
var view_top := 0
var view_mark := -1
var view_from := "open"
var view_rows := 8
var keyword := 0
var results: Array = []
var read := {}
var known_cases := false
var message := ""
var message_args := {}
var message_lv := 2
var fails := 0
## What the last refusal was about: "login" | "release".
var refused := ""
var released := false
var _return_cursor := 0
var _menu_cursor := 0
var _lay := {}


func txt(key: String, args := {}) -> String:
	if tr_fn.is_valid():
		return str(tr_fn.call(key, args))
	return key


func reset() -> void:
	phase = "login"
	digits = [0, 0, 0, 0]
	digit_cursor = 0
	cursor = 0
	view_file = ""
	view_top = 0
	view_mark = -1
	keyword = 0
	results = []
	read = {}
	known_cases = false
	message = ""
	message_args = {}
	message_lv = 2
	fails = 0
	refused = ""
	released = false


func entered() -> String:
	return "%d%d%d%d" % [int(digits[0]), int(digits[1]), int(digits[2]), int(digits[3])]


func file_lines(id: String) -> PackedStringArray:
	return txt("mg.term.file." + id).split("\n")


## The short name of a directory entry (its first word, e.g. UEB-45).
func short_name(id: String) -> String:
	var parts := txt("mg.term.dir." + id).split(" ", false)
	return parts[0] if parts.size() > 0 else id


## The households of the transfer list: [{"id": "S8-067", "label": "S8-067 LINDNER, A."}].
func cases() -> Array:
	var out: Array = []
	for line in file_lines(CASE_FILE):
		var parts := str(line).strip_edges().split(" ", false)
		if parts.size() >= 2 and str(parts[0]).begins_with(CASE_PREFIX):
			var label := str(parts[0]) + "  " + str(parts[1])
			if parts.size() >= 3:
				label += " " + str(parts[2])
			out.append({"id": str(parts[0]), "label": label})
	return out


func item_count() -> int:
	match phase:
		"menu":
			return COMMANDS.size()
		"open":
			return FILES.size() + 1
		"search":
			return KEYWORDS
		"results":
			return results.size()
		"release":
			return cases().size() if known_cases else 0
	return 0


static func _norm(s: String) -> String:
	return s.to_upper().replace("ß", "SS")


# ================================================================ actions
func digit(n: int) -> String:
	if phase != "login":
		return ""
	digits[digit_cursor] = clampi(n, 0, 9)
	digit_cursor = mini(3, digit_cursor + 1)
	return "key"


## dx: -1 left / +1 right, dy: -1 up / +1 down.
func move(dx: int, dy: int) -> String:
	match phase:
		"login":
			if dx != 0:
				digit_cursor = posmod(digit_cursor + dx, 4)
				return "move"
			if dy != 0:
				digits[digit_cursor] = posmod(int(digits[digit_cursor]) - dy, 10)
				return "key"
		"view":
			var n := file_lines(view_file).size()
			var top := clampi(view_top + dy, 0, maxi(0, n - view_rows))
			if top != view_top:
				view_top = top
				return "move"
		"done", "list":
			pass
		_:
			var count := item_count()
			if dy != 0 and count > 0:
				cursor = posmod(cursor + dy, count)
				return "move"
	return ""


func ok() -> String:
	match phase:
		"login":
			return _submit_login()
		"menu":
			_menu_cursor = cursor
			phase = COMMANDS[cursor]
			cursor = 0
			message = ""
			return "enter"
		"list":
			return back()
		"open":
			if cursor >= FILES.size():
				_return_cursor = cursor
				phase = "release"
				cursor = 0
				message = "" if known_cases else "mg.term.release.unknown"
				message_args = {}
				message_lv = 3
				return "locked"
			return _open(FILES[cursor], 0, -1, "open")
		"view":
			return back()
		"search":
			keyword = cursor
			_search()
			phase = "results"
			cursor = 0
			return "enter"
		"results":
			if results.is_empty():
				return back()
			var r: Dictionary = results[cursor]
			return _open(str(r["file"]), int(r["line"]), int(r["line"]), "results")
		"release":
			return _submit_release()
	return ""


## One step back; "" when there is nothing to go back to (login, menu: the caller gives up).
func back() -> String:
	match phase:
		"view":
			phase = view_from
			cursor = _return_cursor
			return "back"
		"list", "open", "search":
			phase = "menu"
			cursor = _menu_cursor
			message = ""
			return "back"
		"results":
			phase = "search"
			cursor = keyword
			return "back"
		"release":
			phase = "open"
			cursor = FILES.size()
			message = ""
			return "back"
	return ""


func _submit_login() -> String:
	if entered() == OPERATOR:
		phase = "menu"
		cursor = 0
		message = "mg.term.login.ok"
		message_args = {"nr": OPERATOR}
		message_lv = 2
		return "login_ok"
	fails += 1
	refused = "login"
	message = "mg.term.login.fail"
	message_args = {}
	message_lv = 3
	return "login_fail"


func _open(file: String, line: int, mark: int, from: String) -> String:
	view_file = file
	view_from = from
	_return_cursor = cursor
	view_mark = mark
	view_top = maxi(0, line - 1)
	phase = "view"
	message = ""
	read[file] = true
	if file == CASE_FILE:
		known_cases = true
	return "open"


func _search() -> void:
	results = []
	var kw := _norm(txt("mg.term.kw.%d" % (keyword + 1)))
	for f in FILES:
		var lines := file_lines(f)
		for i in lines.size():
			if results.size() >= MAX_RESULTS:
				return
			if _norm(str(lines[i])).contains(kw):
				results.append({"file": f, "line": i, "text": " ".join(str(lines[i]).split(" ", false))})
				if f == CASE_FILE and str(lines[i]).strip_edges().begins_with(CASE_PREFIX):
					known_cases = true


func _submit_release() -> String:
	var list := cases()
	if not known_cases or list.is_empty():
		message = "mg.term.release.unknown"
		message_args = {}
		message_lv = 3
		return "release_unknown"
	var c: Dictionary = list[clampi(cursor, 0, list.size() - 1)]
	if str(c["id"]) == ANSWER:
		released = true
		phase = "done"
		message = ""
		return "release_ok"
	fails += 1
	refused = "release"
	message = "mg.term.release.fail"
	message_args = {"id": str(c["id"])}
	message_lv = 3
	return "release_fail"


## A click on text cell (col, row) of the last screen(): picks a digit / an entry, leaves a file.
func click(col: int, row: int) -> String:
	match phase:
		"login":
			if row == int(_lay.get("digit_row", -1)):
				var i := (col - int(_lay.get("digit_col", 0)) + 1) / 2
				if i >= 0 and i < 4:
					if i == digit_cursor:
						return move(0, -1)
					digit_cursor = i
					return "move"
		"view", "list":
			return back()
		"done":
			return ""
		_:
			var idx := row - int(_lay.get("item_row", 0)) + int(_lay.get("item_first", 0))
			if idx >= 0 and idx < item_count() and row >= int(_lay.get("item_row", 0)):
				cursor = idx
				return ok()
	return ""


# ================================================================ picture
func _item(runs: Array, i: int, row: int, text: String, cols: int) -> void:
	var sel := i == cursor
	runs.append({"t": (("> " if sel else "  ") + text).left(cols), "c": 0, "r": row, "lv": 3 if sel else 2})


## The current state as text: {"runs": [{"t", "c", "r", "lv"}], "caret": [col, row] or null}.
func screen(cols: int, rows: int) -> Dictionary:
	var runs: Array = []
	var caret = null
	var head := txt("mg.term.head")
	var clock := txt("mg.term.clock")
	runs.append({"t": head.left(cols), "c": 0, "r": 0, "lv": 1})
	if head.length() + clock.length() + 2 <= cols:
		runs.append({"t": clock, "c": cols - clock.length(), "r": 0, "lv": 1})
	runs.append({"t": "-".repeat(cols), "c": 0, "r": 1, "lv": 1})
	var top := 2
	var foot := txt("mg.term.foot.ready")
	_lay = {"item_row": top + 1, "item_first": 0}
	match phase:
		"login":
			runs.append({"t": txt("mg.term.login.title"), "c": 0, "r": top, "lv": 2})
			var prompt := txt("mg.term.login.prompt")
			var r := top + 2
			runs.append({"t": prompt, "c": 0, "r": r, "lv": 3})
			var c0 := prompt.length() + 2
			for i in 4:
				runs.append({"t": str(int(digits[i])), "c": c0 + i * 2, "r": r, "lv": 3 if i == digit_cursor else 2})
			caret = [c0 + digit_cursor * 2, r]
			_lay["digit_col"] = c0
			_lay["digit_row"] = r
			foot = txt("mg.term.foot.login")
		"menu":
			runs.append({"t": txt("mg.term.menu.prompt"), "c": 0, "r": top, "lv": 2})
			for i in COMMANDS.size():
				_item(runs, i, top + 1 + i, txt("mg.term.menu." + str(COMMANDS[i])), cols)
		"list", "open":
			runs.append({"t": txt("mg.term.list.head" if phase == "list" else "mg.term.open.prompt").left(cols), "c": 0, "r": top, "lv": 2})
			for i in FILES.size() + 1:
				var fid: String = FILES[i] if i < FILES.size() else PROGRAM
				var line := txt("mg.term.dir." + fid)
				var row := top + 1 + i
				if phase == "open":
					_item(runs, i, row, line, cols)
				else:
					runs.append({"t": ("  " + line).left(cols), "c": 0, "r": row, "lv": 2})
				var tag := ""
				if i >= FILES.size():
					tag = txt("mg.term.tag.free" if released else "mg.term.tag.locked")
				elif read.has(fid):
					tag = txt("mg.term.tag.read")
				if tag != "" and line.length() + 4 + tag.length() <= cols:
					runs.append({"t": tag, "c": cols - tag.length(), "r": row, "lv": 1})
			if phase == "list":
				foot = txt("mg.term.foot.list")
		"view":
			var lines := file_lines(view_file)
			view_rows = maxi(1, rows - top - 1)
			view_top = clampi(view_top, 0, maxi(0, lines.size() - view_rows))
			var shown := mini(view_rows, lines.size() - view_top)
			for k in shown:
				var idx := view_top + k
				runs.append({"t": str(lines[idx]).left(cols), "c": 0, "r": top + k, "lv": 3 if (idx == 0 or idx == view_mark) else 2})
			foot = txt("mg.term.foot.view", {"a": view_top + 1, "b": view_top + shown, "n": lines.size()})
		"search":
			runs.append({"t": txt("mg.term.search.prompt"), "c": 0, "r": top, "lv": 2})
			for i in KEYWORDS:
				_item(runs, i, top + 1 + i, txt("mg.term.kw.%d" % (i + 1)), cols)
		"results":
			var kw := txt("mg.term.kw.%d" % (keyword + 1))
			if results.is_empty():
				runs.append({"t": txt("mg.term.results.none", {"kw": kw}).left(cols), "c": 0, "r": top, "lv": 2})
			else:
				runs.append({"t": txt("mg.term.results.head", {"n": results.size(), "kw": kw}).left(cols), "c": 0, "r": top, "lv": 2})
				var visible := maxi(1, rows - top - 2)
				var first := clampi(cursor - visible + 1, 0, maxi(0, results.size() - visible))
				_lay["item_first"] = first
				for k in mini(visible, results.size() - first):
					var res: Dictionary = results[first + k]
					_item(runs, first + k, top + 1 + k, "%s %s" % [short_name(str(res["file"])), str(res["text"])], cols)
		"release":
			runs.append({"t": txt("mg.term.release.prompt").left(cols), "c": 0, "r": top, "lv": 3})
			if known_cases:
				var list := cases()
				for i in list.size():
					_item(runs, i, top + 1 + i, str(list[i]["label"]), cols)
		"done":
			runs.append({"t": txt("mg.term.release.ok1", {"id": ANSWER}).left(cols), "c": 0, "r": top, "lv": 3})
			runs.append({"t": txt("mg.term.release.ok2").left(cols), "c": 0, "r": top + 1, "lv": 2})
			runs.append({"t": txt("mg.term.release.ok3").left(cols), "c": 0, "r": top + 3, "lv": 3})
			foot = txt("mg.term.foot.done")
	if message != "":
		runs.append({"t": txt(message, message_args).left(cols), "c": 0, "r": rows - 1, "lv": message_lv})
	else:
		runs.append({"t": foot.left(cols), "c": 0, "r": rows - 1, "lv": 1})
	return {"runs": runs, "caret": caret}
