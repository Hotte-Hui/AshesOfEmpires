extends RefCounted
## Flashbacks — the flashback films of four real-history cards (TECHNICAL_ARCHITECTURE §12.15).
## A film belongs to exactly one card (data/flashbacks/flashbacks.json): the card shows „Rückblende ansehen“ once it
## is found, the memories page „Filmsequenzen“ lists the film after the story films. Films are §12.5 scenes
## (scenes/cinematics/flashback_*/, base flashback_common/flashback_film.gd) shown by FlashbackView
## (scripts/ui/flashback_view.gd), a modal above whatever is open: the card or the film list stays where it was and
## gets its focus back. Nothing here knows the Story engine: no flags, no objectives, no save data — the Story
## state is never read or written, a level is never unloaded, nothing is forced on the player.
## Static and stateless apart from the two cached data files.

const DATA := "res://data/flashbacks/flashbacks.json"
const LAYOUT := "res://assets/cinematics/flashback/layout.json"
const VIEW_SCRIPT := "res://scripts/ui/flashback_view.gd"
const VIEW_NAME := "FlashbackView"

static var _films: Array = []
static var _layout: Dictionary = {}
static var _loaded := false


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_films = []
	_layout = {}
	var d = _read(DATA)
	if d is Dictionary and d.get("films") is Array:
		for f in d["films"]:
			if f is Dictionary and str(f.get("id", "")) != "" and str(f.get("card", "")) != "":
				_films.append(f)
	var l = _read(LAYOUT)
	if l is Dictionary:
		_layout = l


static func _read(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


## Forgets the cached files (tools and tests after a generator run).
static func reload() -> void:
	_loaded = false
	_load()


## Every film sheet, in file order: {id, key, card, scene, bed, place, shots: [{id, dur, line?, on?}]}.
static func all() -> Array:
	_load()
	return _films


static func film(id: String) -> Dictionary:
	for f in all():
		if str(f["id"]) == id:
			return f
	return {}


static func is_film(id: String) -> bool:
	return not film(id).is_empty()


## The film of a history card ({} for the cards that have none).
static func for_card(card_id: String) -> Dictionary:
	for f in all():
		if str(f["card"]) == card_id:
			return f
	return {}


## True when the film's scene is there to be played.
static func exists(id: String) -> bool:
	var f := film(id)
	return not f.is_empty() and ResourceLoader.exists(str(f.get("scene", "")))


## Seconds a film lasts: the sum of its shots.
static func duration(id: String) -> float:
	var total := 0.0
	for s in film(id).get("shots", []):
		total += float((s as Dictionary).get("dur", 0.0))
	return total


## The generator's layout.json (plates, drift anchors, overlays, the ramp).
static func layout() -> Dictionary:
	_load()
	return _layout


## A film may be watched once its card is found: in the running game (Explore) or, from the main menu, in any game
## the profile remembers (Memories.explore_state).
static func card_found(game: Node, card_id: String, from_menu := false) -> bool:
	if from_menu:
		var mem = game.get("memories") if game != null else null
		if mem == null or not mem.has_method("explore_state"):
			return false
		var st = mem.explore_state()
		return st is Dictionary and (st.get("cards", []) as Array).has(card_id)
	var ml := Engine.get_main_loop() as SceneTree
	var ex: Node = ml.root.get_node_or_null("Explore") if ml != null and ml.root != null else null
	return ex != null and ex.has_method("is_card_found") and bool(ex.is_card_found(card_id))


## Rows for Game.memory_films(): {id, unlocked, title, sub} — a locked film carries no words (no spoiler).
static func films(game: Node, from_menu := false) -> Array:
	var out: Array = []
	var ml := Engine.get_main_loop() as SceneTree
	var loc: Node = ml.root.get_node_or_null("Loc") if ml != null and ml.root != null else null
	for f in all():
		var id := str(f["id"])
		if not exists(id):
			continue
		var open := card_found(game, str(f["card"]), from_menu)
		var title := ""
		var sub := ""
		if open and loc != null:
			title = str(loc.t("ui.memories.film." + id))
			if bool(loc.has("ui.memories.film_sub." + id)):
				sub = str(loc.t("ui.memories.film_sub." + id))
		out.append({"id": id, "unlocked": open, "title": title, "sub": sub})
	return out


## The FlashbackView under `host` (UIRoot: one modal on its stack; any other Control: stand-alone, tests), made on
## first use.
static func view(host: Node) -> Control:
	if host == null or not host.is_inside_tree():
		return null
	var v := host.get_node_or_null(VIEW_NAME) as Control
	if v != null:
		return v
	v = (load(VIEW_SCRIPT) as GDScript).new() as Control
	v.name = VIEW_NAME
	if host.has_method("push_modal"):
		v.set("ui_root", host)
	host.add_child(v)
	return v


## Plays the film above `host` and returns once it is over or skipped (false: nothing was played).
static func play(host: Node, id: String) -> bool:
	var v := view(host)
	if v == null or bool(v.get("is_open")) or not bool(v.call("play", id)):
		return false
	await v.closed
	return true


## Game.rewatch_film() for a flashback (memories page, in the game or from the main menu): the same modal above the
## list — no fade to a level, no Story snapshot, the list is there again afterwards.
static func rewatch(game: Node, id: String, from_menu := false) -> bool:
	var f := film(id)
	if game == null or f.is_empty() or not exists(id) or not card_found(game, str(f["card"]), from_menu):
		return false
	var ui = game.get("ui")
	if not (ui is Node):
		return false
	return await play(ui, id)
