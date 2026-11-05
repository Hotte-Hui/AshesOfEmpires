extends RefCounted
## Plaza mini-game "Das Blatt im Schnee" (owner: plaza-polish, TECHNICAL_ARCHITECTURE §12.8) and the two quiet
## plaza easter eggs: the logic accepts the solution (sheet picked up while both posts watch the parade), refuses
## wrong input (bending under a passing gaze: gently noticed; bending beside the sheet: nothing), the wind and the
## foot behave, auto mode resolves, the scene/data/strings/art are valid, and demo_solve uses synthetic keys only.

const Kit := preload("res://tests/support/test_kit.gd")
const LOGIC := "res://scripts/ui/minigames/leaflet_logic.gd"
const Logic := preload("res://scripts/ui/minigames/leaflet_logic.gd")
const SCENE := "res://scenes/ui/minigames/LeafletSnow.tscn"
const GAME := "res://scripts/ui/minigames/leaflet_game.gd"
const DATA := "res://data/explore/plaza.json"
const STRINGS := "res://data/locale/de_minigame_plaza.json"
const FINDS := "res://data/locale/de_explore_plaza.json"
const LEVEL := "res://scenes/levels/L_M1_Plaza.tscn"
const HOTSPOTS := "res://assets/environments/hall_plaza/explore_hotspots.json"
const ART := "res://assets/ui/minigames/plaza/"
const NEW := {"plaza.leaflet": ["detail", "exp_pz_leaflet"], "plaza.frost_heart": ["easter_egg", "exp_pz_frost_heart"],
	"plaza.paws": ["easter_egg", "exp_pz_paws"]}
const DT := 0.05

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("solution_accepted", _solution)
	kit.run_case("wrong_input_refused", _refused)
	kit.run_case("wind_and_foot", _wind)
	kit.run_case("auto_mode", _auto)
	kit.run_case("ui_keys_and_give_up", _ui)
	kit.run_case("data_valid", _data)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


## Walks to the sheet and bends only while both posts watch the parade long enough; returns seconds used.
func _play(lg) -> float:
	var t := 0.0
	var bending := false
	while not lg.done and t < 60.0:
		var dir := 0
		var d: float = lg.sheet - lg.k
		if not bending and absf(d) > Logic.REACH * 0.5:
			dir = 1 if d > 0.0 else -1
		elif not bending:
			bending = lg.calm_left() > Logic.BEND_IN + 0.3
		elif lg.calm_left() <= 0.0:
			bending = false
		lg.step(DT, dir, bending)
		t += DT
	return t


func _solution() -> bool:
	var lg = load(LOGIC).new()
	var t := _play(lg)
	kit.ok(lg.done, "the sheet is picked up while both posts watch the parade (%.1f s)" % t)
	kit.eq(lg.noticed, 0, "a careful player is never noticed")
	kit.ok(t < 30.0, "solvable within half a minute (%.1f s)" % t)
	kit.ok(lg.step(DT, 0, false).is_empty(), "nothing happens after the solve")
	# the posts really alternate: each one turns and sweeps within the first cycle, and a calm window exists
	var lg2 = load(LOGIC).new()
	var seen := {}
	var calm_long := 0.0
	var calm_run := 0.0
	for i in int(Logic.PERIOD / DT):
		lg2.step(DT, 0, false)
		for g in 2:
			seen["%d:%s" % [g, lg2.guard_state(g)[0]]] = true
		calm_run = calm_run + DT if lg2.calm() else 0.0
		calm_long = maxf(calm_long, calm_run)
	for key in ["0:turn", "0:sweep", "1:turn", "1:sweep"]:
		kit.ok(seen.has(key), "within one cycle: post %s" % key)
	kit.ok(calm_long >= Logic.BEND_IN + 2.0, "a calm window of %.1f s lets Konrad bend in time" % calm_long)
	return true


func _refused() -> bool:
	# bending while a gaze passes over Konrad: noticed (gently), nothing solved, nothing lost but the bend
	var lg = load(LOGIC).new()
	var guard := 0
	while lg.guard_state(0)[0] != "sweep" and guard < 400:
		lg.step(DT, 0, false)
		guard += 1
	kit.eq(str(lg.guard_state(0)[0]), "sweep", "the left post starts his sweep")
	lg.k = lg.gaze(0)
	lg.sheet = lg.k
	var ev: Array = []
	for i in 30:
		ev += lg.step(DT, 0, true)
		if "noticed" in ev:
			break
	kit.ok("noticed" in ev, "bending under the gaze is noticed")
	kit.ok(not lg.done, "and does not pick the sheet up")
	kit.eq(lg.noticed, 1, "one notice")
	kit.eq(lg.bend, 0.0, "Konrad straightens up")
	kit.eq(str(lg.guard_state(0)[0]), "stare", "the post looks at him a moment")
	var before: float = lg.bend
	lg.step(DT, 0, true)
	kit.eq(lg.bend, before, "nobody bends while being looked at")
	lg.step(DT, 1, false)
	kit.ok(not lg.done, "still not solved")
	# bending beside the sheet: only snow
	var lg2 = load(LOGIC).new()
	lg2.k = 0.1
	lg2.sheet = 0.6
	var ev2: Array = []
	for i in int(1.3 / DT):
		ev2 += lg2.step(DT, 0, true)
	kit.ok("nothing" in ev2 and not lg2.done, "bending beside the sheet finds only snow")
	kit.eq(lg2.k, 0.1, "no walking while bent")
	return true


func _wind() -> bool:
	var lg = load(LOGIC).new()
	var s0: float = lg.sheet
	var ev: Array = []
	for i in int((Logic.GUST_FIRST + Logic.GUST_LEN + 0.1) / DT):
		ev += lg.step(DT, 0, false)
	kit.ok("gust" in ev, "a gust comes")
	kit.ok(absf(lg.sheet - s0) > 0.05, "the gust pushes the sheet (%.2f -> %.2f)" % [s0, lg.sheet])
	var lg2 = load(LOGIC).new()
	lg2.k = lg2.sheet
	var s1: float = lg2.sheet
	var ev2: Array = []
	for i in int((Logic.GUST_FIRST + Logic.GUST_LEN + 0.1) / DT):
		ev2 += lg2.step(DT, 0, false)
	kit.ok("pinned" in ev2, "standing on the sheet pins it")
	kit.eq(lg2.sheet, s1, "the foot holds the sheet against the wind")
	return true


func _instance() -> Node:
	var mg: Node = load(SCENE).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(mg)
	kit.track(mg)
	return mg


func _auto() -> bool:
	var mg := _instance()
	kit.ok(mg.is_in_group("minigame"), "joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "plaza.leaflet", "auto": true})
	kit.ok(mg.is_open, "opens")
	mg._process(0.1)
	kit.eq(got, [], "not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	kit.ok(not mg.is_open, "closes itself")
	return true


func _key(k: int) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = true
	return ev


func _ui() -> bool:
	var mg := _instance()
	mg.open({"explore_id": "plaza.leaflet", "auto": false})
	kit.ok(mg.modal_input(_key(KEY_RIGHT)), "Right is consumed (walking is polled)")
	kit.ok(mg.modal_input(_key(KEY_DOWN)), "Down is consumed (bending is polled)")
	for i in 20:
		mg._process(DT)
	kit.ok(not mg.solved and mg.fails == 0, "idle frames neither solve nor fail")
	# two notices show the hint, never more than that
	mg.logic.k = 0.3
	for n in 2:
		mg.register_fail("x")
	kit.ok(mg._hint_box.visible and mg._hint_label.text != "", "hint after two refusals")
	kit.ok(str(mg._hint_text(1)).begins_with("Tipp"), "hint text from Loc")
	var res: Array = []
	mg.finished.connect(func(ok: bool): res.append(ok))
	mg.handle_cancel()
	kit.eq(res, [false], "Esc gives up without a find")
	var src := FileAccess.get_file_as_string(GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_key_event(") and not body.contains("logic.step(") and not body.contains("mark_solved("),
		"demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "extends minigame_base.gd")
	return true


func _data() -> bool:
	var d = _json(DATA)
	if not kit.ok(d is Dictionary, "plaza.json parses"):
		return true
	var by_id := {}
	for e in d.get("entries", []):
		by_id[str(e.get("id", ""))] = e
	var finds = _json(FINDS)
	var fs: Dictionary = finds.get("strings", {}) if finds is Dictionary else {}
	for id in NEW:
		var e: Dictionary = by_id.get(id, {})
		if not kit.ok(not e.is_empty(), "%s exists" % id):
			continue
		kit.eq(str(e.get("kind", "")), NEW[id][0], "%s kind" % id)
		kit.ok((e.get("history", []) as Array).is_empty(), "%s carries no history card" % id)
		var img := str(e.get("image", ""))
		kit.ok(FileAccess.file_exists(img), "%s close-up %s exists" % [id, img])
		kit.ok(not FileAccess.file_exists(img.get_basename() + "_hist.png"), "%s: no insignia variant" % id)
		var txt := str(fs.get(str(e.get("text_key", "")), ""))
		kit.ok(txt.length() >= 250 and txt.length() <= 520 and not txt.contains("!"), "%s find text (%d chars)" % [id, txt.length()])
	kit.eq(str(by_id.get("plaza.leaflet", {}).get("minigame", "")), SCENE, "plaza.leaflet opens the mini-game")
	kit.ok(ResourceLoader.exists(SCENE), "mini-game scene exists")
	# strings: every mg.leaflet key used by the script exists and stays calm
	var mg = _json(STRINGS)
	var ms: Dictionary = mg.get("strings", {}) if mg is Dictionary else {}
	var src := FileAccess.get_file_as_string(GAME)
	var rx := RegEx.new()
	rx.compile("\"(mg\\.leaflet\\.[a-z_.0-9]+)\"")
	for m in rx.search_all(src):
		var key := m.get_string(1)
		if key.ends_with("."):
			continue
		kit.ok(ms.has(key), "string %s exists" % key)
	for st in ["away", "turn", "sweep", "stare"]:
		kit.ok(ms.has("mg.leaflet.guard." + st), "guard state %s has a label" % st)
	for key in ms:
		kit.ok(str(key).begins_with("mg.leaflet.") and not str(ms[key]).contains("!"), "%s is calm and namespaced" % key)
	for key in ["mg.leaflet.hint.1", "mg.leaflet.hint.2", "mg.leaflet.wind.calm", "mg.leaflet.wind.gust",
			"mg.leaflet.guard.left", "mg.leaflet.guard.right"]:
		kit.ok(ms.has(key), "string %s exists" % key)
	# level nodes + hotspots
	var h = _json(HOTSPOTS)
	var spots: Dictionary = h.get("hotspots", {}) if h is Dictionary else {}
	var lvl := FileAccess.get_file_as_string(LEVEL)
	for id in NEW:
		var hid: String = NEW[id][1]
		kit.ok(spots.has(hid), "hotspot %s declared" % hid)
		kit.ok(lvl.contains("hotspot_id = \"%s\"" % hid) and lvl.contains("explore_id = \"%s\"" % id),
			"L_M1_Plaza places %s at %s" % [id, hid])
	kit.ok(lvl.contains("leaflet_world_cue.gd") and lvl.contains("paw_trail.png"), "world cue and paw trail placed")
	# art
	for f in ["leaflet_back.png", "leaflet_march.png", "leaflet_barrier.png", "leaflet_front.png", "leaflet_bend.png",
			"leaflet_sheet.png", "world_leaflet.png", "leaflet_layout.json"]:
		kit.ok(FileAccess.file_exists(ART + f), "art %s exists" % f)
	var lay = _json(ART + "leaflet_layout.json")
	kit.ok(lay is Dictionary and (lay.get("lane", []) as Array).size() == 2, "layout has the lane")
	# the press photographer's portrait (chat speaker of plaza.photographer)
	var pj = _json("res://assets/characters/photographer/portrait.json")
	kit.ok(pj is Dictionary and (pj.get("expressions", []) as Array).size() == 4 and pj.has("anim"),
		"photographer portrait.json: 4 expressions + talk/blink anim")
	kit.ok(FileAccess.file_exists("res://assets/characters/photographer/portrait.png")
		and FileAccess.file_exists("res://assets/characters/photographer/portrait_anim.png"), "photographer portrait pngs")
	return true
