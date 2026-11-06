extends Node
## Exploration layer (TECHNICAL_ARCHITECTURE §12): optional discoveries, secrets, easter eggs, chats and
## real-history cards. None of this touches the canonical Story state.
##
## Data: data/explore/*.json (one owner per file, read in file-name order)
##   area files    {"area": "karsk", "entries": [{id, kind, level, title_key, text_key, prompt_key?, image?,
##                  history?: [card ids], lines?: [{speaker, key, expr}] (kind "chat" only)}]}
##   history files {"side": "reich"|"soviet", "cards": [{id, side, title_key, text_key, year,
##                  sources: [{label, url}]}]}
##
## Public API (stable, §12.1): find(id) -> {ok, new, entry, cards_new}, is_found, entry, card, counts,
## history_counts, chat_lines, prompt_for, state()/restore()/reset(), signals found / history_unlocked /
## state_changed. Additions (explore-system round 2): validation on load (`warnings`), data-ordered listings
## (areas, entries_for, found_entries, cards_list, found_cards), per-area/level/kind/side counts, progress(),
## cards_of(), entry_image() (resolved through Symbols.pick), load_data() for tests and UI previews.
## Save format (Game.save_extra()["explore"]) is unchanged: {"found": [ids in find order], "cards": [ids]}.
##
## Side tasks („Aufgaben“, §12.9 — backward compatible, no save data beyond state()):
##   entries may carry "requires": [explore ids of the same level] — such an entry cannot be found (and its
##   interactable stays inactive) until every required id is found;
##   any area file may declare "tasks": [{id, area?, level, title_key, summary_key,
##     steps: [{explore_id, hint_key}], reward_cards?: [card ids]}].
##   A task's state is derived from the found step ids: "not_started" (no step found), "active" (current step =
##   first unfound step, its hint_key is the journal hint) or "done" (all steps found; reward cards unlock with
##   the find that completes it and are returned in that find's cards_new).
##   API: can_find(id), requires_of(id), tasks_for(level_or_area), task(id), task_state(id) -> {state, step,
##   hint_key, done_steps}, task_of(explore_id), task_counts(level_or_area), signal task_changed(id).
##   A find that starts / completes a task announces it through Game.toast() („Neue Aufgabe: …“ /
##   „Aufgabe erledigt: …“) once the interaction is over (`notify_tasks`; never on restore()).

signal found(id: String)
signal history_unlocked(card_id: String)
signal state_changed
## Emitted after reload()/load_data() (data changed, not progress).
signal data_reloaded
## §12.9: a task's derived state (state or current step) changed — by find(), restore() or reset().
signal task_changed(task_id: String)

const DIR := "res://data/explore/"
const KINDS := ["detail", "secret", "easter_egg", "chat"]
const SIDES := ["reich", "soviet"]
## Close-up images are pixel art shown at x3 (§12.1).
const MAX_IMAGE := Vector2i(320, 200)
## Derived task states (§12.9).
const TASK_NOT_STARTED := "not_started"
const TASK_ACTIVE := "active"
const TASK_DONE := "done"

## Problems found by the last reload()/load_data(): clear, one line each (also printed as warnings).
var warnings: Array[String] = []
## Print each new warning with push_warning (tests switch this off for deliberately broken data).
var print_warnings := true
## Toast „Neue Aufgabe“ / „Aufgabe erledigt“ through Game.toast() when a find changes a task (tests: off).
var notify_tasks := true

var _entries: Dictionary = {}     # id -> entry (insertion order = data order)
var _cards: Dictionary = {}       # card id -> card (data order)
var _found: Dictionary = {}       # id -> true (insertion order = find order; unknown ids are kept for saves)
var _cards_found: Dictionary = {} # card id -> true
var _areas: Array = []            # area names in data order
var _entry_src: Dictionary = {}   # id -> source file
var _card_src: Dictionary = {}    # card id -> source file
var _tasks: Dictionary = {}       # task id -> task (data order)
var _task_src: Dictionary = {}    # task id -> source file
var _step_task: Dictionary = {}   # explore id -> task id (first task that lists it as a step)
var _load_warnings: Array[String] = []


func _ready() -> void:
	reload()


# ================================================================ loading & validation
## Reads every *.json in `dir` (sorted by file name) and validates the result.
func reload(dir := DIR) -> void:
	clear_data()
	var d := DirAccess.open(dir)
	if d != null:
		var files: Array = Array(d.get_files())
		files.sort()
		for f in files:
			if not str(f).ends_with(".json"):
				continue
			var path := dir.path_join(str(f))
			var j := JSON.new()
			var err := j.parse(FileAccess.get_file_as_string(path))
			if err != OK:
				_warn_load("%s: invalid JSON (line %d: %s)" % [f, j.get_error_line(), j.get_error_message()])
				continue
			_ingest(j.data, str(f))
	_finish_load()


## Adds one area/history dictionary (same format as a file) and re-validates. For tests and UI previews.
func load_data(data, source := "memory") -> void:
	_ingest(data, source)
	_finish_load()


## Forgets all data (not the progress).
func clear_data() -> void:
	_entries.clear()
	_cards.clear()
	_areas.clear()
	_entry_src.clear()
	_card_src.clear()
	_tasks.clear()
	_task_src.clear()
	_step_task.clear()
	_load_warnings.clear()
	warnings.clear()


func _finish_load() -> void:
	var before := warnings.duplicate()
	_index_tasks()
	validate()
	if print_warnings:
		var fresh: Array[String] = []
		for w in warnings:
			if not (w in before):
				fresh.append(w)
		if fresh.size() <= 3:
			for w in fresh:
				push_warning("Explore: " + w)
		else:   # one compact report instead of a backtrace per line
			push_warning("Explore: %d data problem(s) in %s:\n  - %s" % [fresh.size(), DIR, "\n  - ".join(fresh)])
	data_reloaded.emit()


func _warn_load(msg: String) -> void:
	_load_warnings.append(msg)


func _ingest(data, source: String) -> void:
	if not (data is Dictionary):
		_warn_load("%s: top level must be an object" % source)
		return
	var area := str(data.get("area", source.get_basename()))
	var side := str(data.get("side", ""))
	var entries = data.get("entries", [])
	var cards = data.get("cards", [])
	var tasks = data.get("tasks", [])
	if not (entries is Array) or not (cards is Array):
		_warn_load("%s: 'entries' and 'cards' must be arrays" % source)
		return
	if not (tasks is Array):
		_warn_load("%s: 'tasks' must be an array" % source)
		tasks = []
	if entries.is_empty() and cards.is_empty() and tasks.is_empty():
		_warn_load("%s: neither 'entries' nor 'cards' found" % source)
	for t in tasks:
		if not (t is Dictionary) or str(t.get("id", "")) == "":
			_warn_load("%s: task without id skipped" % source)
			continue
		var tid := str(t["id"])
		if _tasks.has(tid):
			_warn_load("duplicate task id '%s' in %s (first defined in %s; ignored)" % [tid, source, _task_src[tid]])
			continue
		var tx: Dictionary = t.duplicate(true)
		tx["area"] = str(tx.get("area", area))
		_tasks[tid] = tx
		_task_src[tid] = source
	for e in entries:
		if not (e is Dictionary) or str(e.get("id", "")) == "":
			_warn_load("%s: entry without id skipped" % source)
			continue
		var id := str(e["id"])
		if _entries.has(id):
			_warn_load("duplicate entry id '%s' in %s (first defined in %s; ignored)" % [id, source, _entry_src[id]])
			continue
		var x: Dictionary = e.duplicate(true)
		x["area"] = str(x.get("area", area))
		_entries[id] = x
		_entry_src[id] = source
		if not (x["area"] in _areas):
			_areas.append(x["area"])
	for c in cards:
		if not (c is Dictionary) or str(c.get("id", "")) == "":
			_warn_load("%s: card without id skipped" % source)
			continue
		var cid := str(c["id"])
		if _cards.has(cid):
			_warn_load("duplicate card id '%s' in %s (first defined in %s; ignored)" % [cid, source, _card_src[cid]])
			continue
		var y: Dictionary = c.duplicate(true)
		if str(y.get("side", "")) == "" and side != "":
			y["side"] = side
		_cards[cid] = y
		_card_src[cid] = source


## Checks the loaded data; returns (and stores in `warnings`) one clear line per problem:
## unknown kinds, missing fields, Loc keys without text, dangling history ids, missing image files,
## malformed cards and cards that no entry links (they could never be found).
func validate() -> Array[String]:
	var out: Array[String] = _load_warnings.duplicate()
	var loc := _loc()
	var linked := {}
	for id in _entries:
		var e: Dictionary = _entries[id]
		var src := str(_entry_src.get(id, "?"))
		var where := "entry '%s' (%s)" % [id, src]
		var kind := str(e.get("kind", ""))
		if not (kind in KINDS):
			out.append("%s: unknown kind '%s' (allowed: %s)" % [where, kind, ", ".join(KINDS)])
		if str(e.get("level", "")) == "":
			out.append("%s: missing 'level'" % where)
		var keys := ["title_key"]
		if kind != "chat":
			keys.append("text_key")
		for k in keys:
			if str(e.get(k, "")) == "":
				out.append("%s: missing '%s'" % [where, k])
		for k in ["title_key", "text_key", "prompt_key"]:
			var key := str(e.get(k, ""))
			if key != "" and loc != null and not loc.has(key):
				out.append("%s: %s '%s' has no text in data/locale" % [where, k, key])
		var hist = e.get("history", [])
		if not (hist is Array):
			out.append("%s: 'history' must be an array of card ids" % where)
		else:
			for cid in hist:
				linked[str(cid)] = true
				if not _cards.has(str(cid)):
					out.append("%s: history card '%s' does not exist" % [where, cid])
		var img := str(e.get("image", ""))
		if img != "" and not (ResourceLoader.exists(img) or FileAccess.file_exists(img)):
			out.append("%s: image '%s' not found" % [where, img])
		var lines = e.get("lines", [])
		if kind == "chat":
			if not (lines is Array) or lines.is_empty():
				out.append("%s: chat without 'lines'" % where)
		if lines is Array:
			for i in lines.size():
				var l = lines[i]
				if not (l is Dictionary) or str(l.get("speaker", "")) == "" or str(l.get("key", "")) == "":
					out.append("%s: line %d needs 'speaker' and 'key'" % [where, i])
				elif loc != null and not loc.has(str(l["key"])):
					out.append("%s: line %d key '%s' has no text in data/locale" % [where, i, l["key"]])
		elif lines != null:
			out.append("%s: 'lines' must be an array" % where)
	for cid in _cards:
		var c: Dictionary = _cards[cid]
		var where := "card '%s' (%s)" % [cid, str(_card_src.get(cid, "?"))]
		if not (str(c.get("side", "")) in SIDES):
			out.append("%s: unknown side '%s' (allowed: %s)" % [where, c.get("side", ""), ", ".join(SIDES)])
		for k in ["title_key", "text_key"]:
			var key := str(c.get(k, ""))
			if key == "":
				out.append("%s: missing '%s'" % [where, k])
			elif loc != null and not loc.has(key):
				out.append("%s: %s '%s' has no text in data/locale" % [where, k, key])
		if str(c.get("year", "")) == "":
			out.append("%s: missing 'year'" % where)
		var srcs = c.get("sources", [])
		if not (srcs is Array) or srcs.is_empty():
			out.append("%s: needs at least one source {label, url}" % where)
		else:
			for s in srcs:
				if not (s is Dictionary) or str(s.get("label", "")) == "":
					out.append("%s: every source needs a 'label'" % where)
				elif s.has("url") and not (s["url"] is String):
					out.append("%s: source url must be a string" % where)
		if not _entries.is_empty() and not linked.has(cid) and not _is_reward_card(cid):
			out.append("%s: not linked by any entry (it can never be found)" % where)
	_validate_requires(out)
	_validate_tasks(out, loc)
	warnings = out
	return out


## §12.9 "requires": arrays of existing explore ids of the SAME level (an entry elsewhere could never be found
## from here), no self reference, no cycle (a cycle would lock every entry on it forever).
func _validate_requires(out: Array[String]) -> void:
	for id in _entries:
		var e: Dictionary = _entries[id]
		if not e.has("requires"):
			continue
		var where := "entry '%s' (%s)" % [id, str(_entry_src.get(id, "?"))]
		var req = e["requires"]
		if not (req is Array):
			out.append("%s: 'requires' must be an array of explore ids" % where)
			continue
		for r in req:
			var rid := str(r)
			if not (r is String or r is StringName) or rid == "":
				out.append("%s: 'requires' holds a non-id value %s" % [where, var_to_str(r)])
			elif rid == id:
				out.append("%s: requires itself" % where)
			elif not _entries.has(rid):
				out.append("%s: requires unknown explore id '%s'" % [where, rid])
			elif str(_entries[rid].get("level", "")) != str(e.get("level", "")):
				out.append("%s: requires '%s' of another level (%s) — it could never be found here" % [where, rid,
					_entries[rid].get("level", "")])
	# cycles: depth-first search over the requires graph (0 = new, 1 = on the stack, 2 = done)
	var mark := {}
	var cycles: Array = []
	for id in _entries:
		if int(mark.get(id, 0)) == 0:
			_find_cycles(str(id), mark, [], cycles)
	for cyc in cycles:
		out.append("requires cycle: %s (none of these can ever be found)" % " -> ".join(PackedStringArray(cyc)))


## One cycle per back edge of the depth-first search from `id` is appended to `cycles`. Every node is finished
## (mark 2) on the way out, also below a cycle: a later search from another root must never take a node of an
## earlier search for part of its own cycle (an entry that only depends on a cycle is not on one).
func _find_cycles(id: String, mark: Dictionary, stack: Array, cycles: Array) -> void:
	mark[id] = 1
	stack.append(id)
	for r in requires_of(id):
		if not _entries.has(r):
			continue
		var m := int(mark.get(r, 0))
		if m == 1:
			var cyc: Array = stack.slice(stack.find(r))
			cyc.append(r)
			cycles.append(cyc)
		elif m == 0:
			_find_cycles(r, mark, stack, cycles)
	stack.pop_back()
	mark[id] = 2


## All ids `id` depends on, directly or through other requirements (cycle-safe).
func _ancestors(id: String) -> Dictionary:
	var out := {}
	var todo: Array = requires_of(id)
	while not todo.is_empty():
		var r: String = todo.pop_back()
		if out.has(r):
			continue
		out[r] = true
		todo.append_array(requires_of(r))
	return out


## §12.9 tasks: known level, Loc keys, steps that exist in the task's level, each step in at most one task, the
## steps in a forced order (step i needs step i-1, directly or through other requirements, and never a later
## step), reward cards that exist.
func _validate_tasks(out: Array[String], loc: Node) -> void:
	var step_owner := {}
	for tid in _tasks:
		var t: Dictionary = _tasks[tid]
		var where := "task '%s' (%s)" % [tid, str(_task_src.get(tid, "?"))]
		var lvl := str(t.get("level", ""))
		if lvl == "":
			out.append("%s: missing 'level'" % where)
		for k in ["title_key", "summary_key"]:
			var key := str(t.get(k, ""))
			if key == "":
				out.append("%s: missing '%s'" % [where, k])
			elif loc != null and not loc.has(key):
				out.append("%s: %s '%s' has no text in data/locale" % [where, k, key])
		var steps = t.get("steps", [])
		if not (steps is Array) or steps.is_empty():
			out.append("%s: needs a non-empty 'steps' array" % where)
			steps = []
		var ids: Array = []
		for i in steps.size():
			var s = steps[i]
			if not (s is Dictionary) or str(s.get("explore_id", "")) == "":
				out.append("%s: step %d needs 'explore_id'" % [where, i])
				ids.append("")
				continue
			var sid := str(s["explore_id"])
			ids.append(sid)
			if not _entries.has(sid):
				out.append("%s: step %d '%s' is not an explore entry" % [where, i, sid])
			elif lvl != "" and str(_entries[sid].get("level", "")) != lvl:
				out.append("%s: step %d '%s' belongs to level %s, not %s" % [where, i, sid, _entries[sid].get("level", ""), lvl])
			if step_owner.has(sid) and str(step_owner[sid]) != str(tid):
				out.append("%s: step '%s' is already a step of task '%s'" % [where, sid, step_owner[sid]])
			elif ids.count(sid) > 1:
				out.append("%s: step '%s' is listed twice" % [where, sid])
			else:
				step_owner[sid] = tid
			var hint := str(s.get("hint_key", ""))
			if hint == "":
				out.append("%s: step %d needs 'hint_key'" % [where, i])
			elif loc != null and not loc.has(hint):
				out.append("%s: step %d hint_key '%s' has no text in data/locale" % [where, i, hint])
		for i in ids.size():
			if str(ids[i]) == "" or not _entries.has(str(ids[i])):
				continue
			var anc := _ancestors(str(ids[i]))
			for j in range(i, ids.size()):
				if str(ids[j]) != "" and anc.has(str(ids[j])):
					out.append("%s: step %d '%s' requires %s step %d '%s' (steps out of order)" % [where, i, ids[i],
						"itself as" if j == i else "the later", j, ids[j]])
			if i > 0 and str(ids[i - 1]) != "" and not anc.has(str(ids[i - 1])):
				out.append("%s: step %d '%s' does not require step %d '%s' (the order is not enforced)" % [where, i,
					ids[i], i - 1, ids[i - 1]])
		var rw = t.get("reward_cards", [])
		if not (rw is Array):
			out.append("%s: 'reward_cards' must be an array of card ids" % where)
		else:
			for cid in rw:
				if not _cards.has(str(cid)):
					out.append("%s: reward card '%s' does not exist" % [where, cid])


func _loc() -> Node:
	var ml := Engine.get_main_loop() as SceneTree
	return ml.root.get_node_or_null("Loc") if ml != null and ml.root != null else null


# ================================================================ data access
func has_entry(id: String) -> bool:
	return _entries.has(id)


func entry(id: String) -> Dictionary:
	return _entries.get(id, {})


func has_card(card_id: String) -> bool:
	return _cards.has(card_id)


func card(id: String) -> Dictionary:
	return _cards.get(id, {})


## Areas in data order ("karsk", "berlin", ...).
func areas() -> Array:
	return _areas.duplicate()


## Entries of an area ("karsk"), a level id ("L_A1_Railyard") or all (""), in data order; optional kind filter.
func entries_for(area_or_level := "", kind := "") -> Array:
	var out: Array = []
	for id in _entries:
		var e: Dictionary = _entries[id]
		if area_or_level != "" and str(e.get("area", "")) != area_or_level and str(e.get("level", "")) != area_or_level:
			continue
		if kind != "" and str(e.get("kind", "")) != kind:
			continue
		out.append(e)
	return out


## Found entries of an area / level / everything, in data order.
func found_entries(area_or_level := "") -> Array:
	var out: Array = []
	for e in entries_for(area_or_level):
		if _found.has(str(e["id"])):
			out.append(e)
	return out


## Cards in data order, optionally of one side ("reich" / "soviet").
func cards_list(side := "") -> Array:
	var out: Array = []
	for cid in _cards:
		if side == "" or str(_cards[cid].get("side", "")) == side:
			out.append(_cards[cid])
	return out


func found_cards(side := "") -> Array:
	var out: Array = []
	for c in cards_list(side):
		if _cards_found.has(str(c["id"])):
			out.append(c)
	return out


## History card ids an entry links that exist (in the entry's order).
func cards_of(id: String) -> Array:
	var out: Array = []
	var h = entry(id).get("history", [])
	if h is Array:
		for c in h:
			if _cards.has(str(c)) and not (str(c) in out):
				out.append(str(c))
	return out


## Close-up image path of an entry ("" = none), resolved through Symbols.pick (§12.4 _hist variants).
func entry_image(id: String) -> String:
	var p := str(entry(id).get("image", ""))
	if p == "":
		return ""
	return Symbols.pick(p)


func is_found(id: String) -> bool:
	return _found.has(id)


func is_card_found(card_id: String) -> bool:
	return _cards_found.has(card_id)


# ================================================================ requirements & tasks (§12.9)
## Explore ids an entry needs before it can be found (its "requires", data order; [] = none).
func requires_of(id: String) -> Array:
	var out: Array = []
	var req = entry(id).get("requires", [])
	if req is Array:
		for r in req:
			if (r is String or r is StringName) and str(r) != "" and not (str(r) in out):
				out.append(str(r))
	return out


## True when the entry exists and every id it requires is found (already found entries stay findable).
func can_find(id: String) -> bool:
	if not _entries.has(id):
		return false
	for r in requires_of(id):
		if not _found.has(r):
			return false
	return true


func has_task(task_id: String) -> bool:
	return _tasks.has(task_id)


func task(task_id: String) -> Dictionary:
	return _tasks.get(task_id, {})


## Tasks of a level id ("L_A1_Railyard"), an area ("karsk") or all (""), in data order.
func tasks_for(level_or_area := "") -> Array:
	var out: Array = []
	for tid in _tasks:
		var t: Dictionary = _tasks[tid]
		if level_or_area == "" or str(t.get("level", "")) == level_or_area or str(t.get("area", "")) == level_or_area:
			out.append(t)
	return out


## Step explore ids of a task, in step order.
func task_steps(task_id: String) -> Array:
	var out: Array = []
	var steps = task(task_id).get("steps", [])
	if steps is Array:
		for s in steps:
			if s is Dictionary and str(s.get("explore_id", "")) != "":
				out.append(str(s["explore_id"]))
	return out


## The task an explore entry is a step of ("" = none).
func task_of(explore_id: String) -> String:
	return str(_step_task.get(explore_id, ""))


## Derived state of a task — nothing of it is saved beyond the found ids:
## {state: not_started|active|done, step: index of the current step (= steps.size() when done),
##  hint_key: hint of the current step ("" when done), done_steps: found step ids in step order}.
## Unknown task id -> {state: "", step: -1, hint_key: "", done_steps: []}.
func task_state(task_id: String) -> Dictionary:
	if not _tasks.has(task_id):
		return {"state": "", "step": -1, "hint_key": "", "done_steps": []}
	var steps = _tasks[task_id].get("steps", [])
	if not (steps is Array):
		steps = []
	var done: Array = []
	var current := -1
	for i in steps.size():
		var sid := str(steps[i].get("explore_id", "")) if steps[i] is Dictionary else ""
		if sid != "" and _found.has(sid):
			done.append(sid)
		elif current < 0:
			current = i
	var st := TASK_NOT_STARTED
	if current < 0:
		st = TASK_DONE
		current = steps.size()
	elif not done.is_empty():
		st = TASK_ACTIVE
	var hint := ""
	if current < steps.size() and steps[current] is Dictionary:
		hint = str(steps[current].get("hint_key", ""))
	return {"state": st, "step": current, "hint_key": hint, "done_steps": done}


## {done, active, total} tasks of a level / area / everything.
func task_counts(level_or_area := "") -> Dictionary:
	var d := 0
	var a := 0
	var n := 0
	for t in tasks_for(level_or_area):
		n += 1
		match str(task_state(str(t["id"]))["state"]):
			TASK_DONE:
				d += 1
			TASK_ACTIVE:
				a += 1
	return {"done": d, "active": a, "total": n}


func _index_tasks() -> void:
	_step_task.clear()
	for tid in _tasks:
		for sid in task_steps(str(tid)):
			if not _step_task.has(sid):
				_step_task[sid] = str(tid)


func _is_reward_card(card_id: String) -> bool:
	for tid in _tasks:
		var rw = _tasks[tid].get("reward_cards", [])
		if rw is Array and (card_id in rw.map(func(x): return str(x))):
			return true
	return false


func _reward_cards(task_id: String) -> Array:
	var out: Array = []
	var rw = task(task_id).get("reward_cards", [])
	if rw is Array:
		for c in rw:
			if _cards.has(str(c)) and not (str(c) in out):
				out.append(str(c))
	return out


## [state, step] of every task, for change detection.
func _task_snapshot() -> Dictionary:
	var out := {}
	for tid in _tasks:
		var s := task_state(str(tid))
		out[tid] = [s["state"], s["step"]]
	return out


func _emit_task_changes(before: Dictionary) -> Array:
	var changed: Array = []
	for tid in _tasks:
		var s := task_state(str(tid))
		var b = before.get(tid, ["", -1])
		if str(b[0]) != str(s["state"]) or int(b[1]) != int(s["step"]):
			changed.append(str(tid))
	for tid in changed:
		task_changed.emit(tid)
	return changed


## „Neue Aufgabe: …“ / „Aufgabe erledigt: …“ through Game.toast(), after the interaction that caused it is over
## (so the find's own „Entdeckt“ toast comes first). Never in tests (no Game), never on restore().
func _announce_task(task_id: String, st: String) -> void:
	if not notify_tasks or not is_inside_tree():
		return
	var g := get_node_or_null("/root/Game")
	var loc := _loc()
	if g == null or not g.has_method("toast") or loc == null:
		return
	var key := "ui.toast.task_done" if st == TASK_DONE else "ui.toast.task_new"
	var title: String = loc.t(str(task(task_id).get("title_key", "")))
	var text: String = loc.t(key, {"name": title}) if loc.has(key) else title
	var waited := 0.0
	while g.get("busy") == true and waited < 120.0:
		await get_tree().process_frame
		waited += get_process_delta_time()
	g.toast(text)


# ================================================================ progress
## Marks an entry as found (idempotent). Returns {ok, new, entry, cards_new: [card ids unlocked now]}.
## Each card unlocks exactly once, even when several entries link it. §12.9: an entry whose "requires" are not
## all found yet is refused ({ok: false} with the usual shape); the find that completes a task also unlocks the
## task's reward_cards (part of cards_new).
func find(id: String) -> Dictionary:
	if not _entries.has(id) or (not _found.has(id) and not can_find(id)):
		return {"ok": false, "new": false, "entry": {}, "cards_new": []}
	var is_new := not _found.has(id)
	var tasks_before := _task_snapshot() if is_new and _step_task.has(id) else {}
	_found[id] = true
	var cards_new: Array = []
	for c in cards_of(id):
		if not _cards_found.has(c):
			_cards_found[c] = true
			cards_new.append(c)
	var changed: Array = []
	if not tasks_before.is_empty():
		for tid in _tasks:
			if str(tasks_before.get(tid, [""])[0]) != TASK_DONE and str(task_state(str(tid))["state"]) == TASK_DONE:
				for c in _reward_cards(str(tid)):
					if not _cards_found.has(c):
						_cards_found[c] = true
						cards_new.append(c)
	if is_new:
		found.emit(id)
	for c in cards_new:
		history_unlocked.emit(c)
	if not tasks_before.is_empty():
		changed = _emit_task_changes(tasks_before)
	if is_new or not cards_new.is_empty():
		state_changed.emit()
	for tid in changed:
		var was := str(tasks_before.get(tid, [""])[0])
		var now := str(task_state(str(tid))["state"])
		if now == TASK_DONE and was != TASK_DONE:
			_announce_task(str(tid), TASK_DONE)
		elif now == TASK_ACTIVE and was == TASK_NOT_STARTED:
			_announce_task(str(tid), TASK_ACTIVE)
	return {"ok": true, "new": is_new, "entry": _entries[id], "cards_new": cards_new}


## {found, total} for an area ("karsk"), a level id ("L_A1_Railyard") or everything (""); optional kind.
## Chats count too. Only entries that exist in the data are counted.
func counts(area_or_level := "", kind := "") -> Dictionary:
	var tot := 0
	var got := 0
	for e in entries_for(area_or_level, kind):
		tot += 1
		if _found.has(str(e["id"])):
			got += 1
	return {"found": got, "total": tot}


## {area: {found, total}} in data order.
func area_counts() -> Dictionary:
	var out := {}
	for a in _areas:
		out[a] = counts(a)
	return out


## {found, total} of real-history cards (all or one side). Unknown saved ids never count.
func history_counts(side := "") -> Dictionary:
	var tot := 0
	var got := 0
	for c in cards_list(side):
		tot += 1
		if _cards_found.has(str(c["id"])):
			got += 1
	return {"found": got, "total": tot}


## Everything at once (pause menu / journal header).
func progress() -> Dictionary:
	var e := counts()
	var h := history_counts()
	return {"found": e["found"], "total": e["total"], "cards_found": h["found"], "cards_total": h["total"]}


func chat_lines(id: String) -> Array:
	var e := entry(id)
	return e.get("lines", []) if e.get("lines", []) is Array else []


## Prompt label for an interactable (empty = default per kind).
func prompt_for(id: String) -> String:
	var e := entry(id)
	var k := str(e.get("prompt_key", ""))
	var loc := _loc()
	if k != "" and loc != null and loc.has(k):
		return loc.t(k)
	return ""


# ================================================================ persistence (save file extra.explore)
func state() -> Dictionary:
	return {"found": _found.keys(), "cards": _cards_found.keys()}


## Restores a state() dictionary. Unknown ids are kept (data may come back) but never counted; cards
## linked by found entries are re-attached silently, so a card can never be "unlocked" a second time.
func restore(d) -> void:
	var tasks_before := _task_snapshot()
	_found.clear()
	_cards_found.clear()
	if d is Dictionary:
		var f = d.get("found", [])
		if f is Array:
			for id in f:
				if id is String or id is StringName:
					_found[str(id)] = true
		var c = d.get("cards", [])
		if c is Array:
			for cid in c:
				if cid is String or cid is StringName:
					_cards_found[str(cid)] = true
	for id in _found:
		for cid in cards_of(str(id)):
			_cards_found[cid] = true
	for tid in _tasks:   # reward cards of finished tasks are re-attached the same silent way
		if str(task_state(str(tid))["state"]) == TASK_DONE:
			for cid in _reward_cards(str(tid)):
				_cards_found[cid] = true
	_emit_task_changes(tasks_before)
	state_changed.emit()


func reset() -> void:
	var tasks_before := _task_snapshot()
	_found.clear()
	_cards_found.clear()
	_emit_task_changes(tasks_before)
	state_changed.emit()
