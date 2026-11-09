extends RefCounted
## Round 13 (owner: terminal) — the data desk of Nebenstelle Süd (L_C4_Annex scene D, TECHNICAL_ARCHITECTURE §12.8 /
## §12.9): the side task „Planspiel Abgang“, the mini-game „Die Datenstelle“ (DataTerminal.tscn) and the wireframe
## 3D mini-game „Planspiel Abgang“ (PlanspielAbgang.tscn).
##  * data: four entries + the task in data/explore/c4_annex_terminal.json, every text in German and English
##    (data/locale/de_terminal.json / en_terminal.json), Explore validation clean, the task order enforced
##  * placement: the desk is an actor of the art manifest (scenes/levels/c4/AnnexTerminal.tscn) that carries its two
##    lever_spot.gd interactables — only in scene D, inside the walk band, >= 24 px from the story hotspots, >= 14 px
##    from every other find, clear of spawn and blocker; the art is palette-pure 'annex'
##  * reachability on the real nodes: the drivers' loop (autoplay.pending_finds + Explore.find) completes the task in
##    order, the gates follow the Story (after c4b_inspect_crates) and the remembered scene
##  * terminal: rule, both languages, every screen fits both rasters, keys / mouse / hints / cancel, full solve by keys
##  * Planspiel: closed patrols, unseen start, cover, a way through with a whole step of slack on every map, a naive
##    run is caught, restart when seen, hints (tip, then trace), a full run by synthetic keys alone, the 3D picture
##    (400x150 viewport, lines, x3 on the pixel grid, camera fit, reduced motion, high contrast)
##  * sounds, the close-up, the tube's letters.

const Kit := preload("res://tests/support/test_kit.gd")
const TermLogic := preload("res://scripts/ui/minigames/terminal_logic.gd")
const TermGame := preload("res://scripts/ui/minigames/terminal_game.gd")
const AbLogic := preload("res://scripts/ui/minigames/abgang_logic.gd")
const AbGame := preload("res://scripts/ui/minigames/abgang_game.gd")
const Crt := preload("res://scripts/ui/minigames/crt_kit.gd")
const AUTOPLAY := "res://scripts/core/autoplay.gd"
const EXPLORE := "res://scripts/core/explore.gd"
const LEVEL := "res://scenes/levels/L_C4_Annex.tscn"
const ACTOR := "res://scenes/levels/c4/AnnexTerminal.tscn"
const ENV := "res://assets/environments/berlin_annex/"
const DATA := "res://data/explore/c4_annex_terminal.json"
const TERM_SCENE := "res://scenes/ui/minigames/DataTerminal.tscn"
const AB_SCENE := "res://scenes/ui/minigames/PlanspielAbgang.tscn"
const TASK := "berlin.task.planspiel"
const STEPS := ["berlin.annex.term_desk", "berlin.annex.term_roster", "berlin.annex.term_files", "berlin.annex.planspiel"]
const SFX := ["mg_term_hum", "mg_term_relay", "mg_term_key", "mg_term_ok", "mg_term_refuse", "mg_term_tape",
	"mg_abgang_step", "mg_abgang_seen", "mg_abgang_through", "mg_abgang_print"]
const STORY_SPOTS := ["drawer_s8", "plan_wall", "tube_station", "registrar_counter", "guard_annex"]
const GAP_STORY := 24.0
const GAP_FIND := 14.0
const AREA_B := [890.0, 1900.0]
const RASTERS := [Vector2i(63, 16), Vector2i(49, 10)]

var kit: Kit
var de: Node
var en: Node
var data: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	de = kit.track(load("res://scripts/story/loc.gd").new())
	de.reload()
	en = kit.track(load("res://scripts/story/loc.gd").new())
	en.language = "en"
	en.reload()
	var settings: Node = Kit.root().get_node_or_null("Settings")
	var saved := {}
	if settings != null:
		for k in ["puzzle_hints", "text_scale", "high_contrast", "reduced_motion"]:
			saved[k] = settings.values.get(k)
		settings.values["puzzle_hints"] = 1
		settings.values["text_scale"] = 1.0
		settings.values["high_contrast"] = false
		settings.values["reduced_motion"] = false
	kit.run_case("data_task_and_texts_in_both_languages", _data)
	kit.run_case("explore_validation_and_task_order", _validation)
	kit.run_case("desk_actor_placement_spacing_and_art", _placement)
	kit.run_case("real_nodes_gates_drivers_loop_and_memory", _real_path)
	kit.run_case("terminal_rule_files_search_release", _term_logic)
	kit.run_case("terminal_screens_fit_both_rasters_both_languages", _term_screens)
	kit.run_case("terminal_scene_auto_keys_mouse_hints_cancel", _term_scene)
	kit.run_case("terminal_full_solve_by_keys", _term_full)
	kit.run_case("planspiel_maps_patrols_cover_and_solver", _ab_logic)
	kit.run_case("planspiel_scene_auto_seen_restart_hints_cancel", _ab_scene)
	kit.run_case("planspiel_full_run_by_keys", _ab_full)
	kit.run_case("planspiel_picture_is_3d_lines_on_the_pixel_grid", _ab_picture)
	if settings != null:
		kit.run_case("larger_text_contrast_reduced_motion_hint_modes", _access.bind(settings))
	kit.run_case("sounds_close_up_and_letters", _assets)
	if settings != null:
		for k in saved:
			if saved[k] == null:
				settings.values.erase(k)
			else:
				settings.values[k] = saved[k]
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _key(k: int, down := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = down
	return ev


func _mg(path: String) -> Node:
	var mg: Node = load(path).instantiate()
	Kit.root().add_child(mg)
	kit.track(mg)
	return mg


func _steps(mg: Node, seconds: float, dt := 0.05) -> void:
	for i in int(ceil(seconds / dt)):
		mg._process(dt)


func _entries() -> Dictionary:
	var out := {}
	for e in data.get("entries", []):
		out[str(e["id"])] = e
	return out


# ================================================================ data
func _data() -> bool:
	var d = _json(DATA)
	if not kit.ok(d is Dictionary, "c4_annex_terminal.json parses"):
		return true
	data = d
	kit.eq(str(data.get("area")), "berlin", "area berlin")
	var entries := _entries()
	kit.eq(entries.keys(), STEPS, "four entries, in the order of the task")
	var keys: Array = []
	for i in STEPS.size():
		var e: Dictionary = entries.get(STEPS[i], {})
		kit.eq([str(e.get("level")), str(e.get("scene"))], ["L_C4_AnnexA", "L_C4_AnnexB"], "%s: level key of the file, scene D" % STEPS[i])
		kit.eq(e.get("requires", []), [] if i == 0 else [STEPS[i - 1]], "%s requires the step before it" % STEPS[i])
		kit.ok(str(e.get("kind")) in ["detail", "secret"], "%s is a find" % STEPS[i])
		for k in ["title_key", "text_key", "prompt_key"]:
			keys.append(str(e.get(k, "")))
	kit.eq(str(entries[STEPS[2]].get("minigame")), TERM_SCENE, "the third step runs the terminal")
	kit.eq(str(entries[STEPS[3]].get("minigame")), AB_SCENE, "the last step runs the Planspiel")
	for p in [TERM_SCENE, AB_SCENE, ACTOR, str(entries[STEPS[3]].get("image", ""))]:
		kit.ok(ResourceLoader.exists(p), "%s exists" % p)
	var tasks: Array = data.get("tasks", [])
	if kit.eq(tasks.size(), 1, "one task"):
		var t: Dictionary = tasks[0]
		kit.eq([str(t.get("id")), str(t.get("level"))], [TASK, "L_C4_AnnexA"], "task id and level key")
		kit.eq((t.get("steps", []) as Array).map(func(s): return str(s["explore_id"])), STEPS, "the task's steps")
		keys.append(str(t.get("title_key")))
		keys.append(str(t.get("summary_key")))
		for s in t.get("steps", []):
			keys.append(str(s.get("hint_key")))
	for k in keys:
		kit.ok(de.has(k) and str(de.source_of(k)).ends_with("de_terminal.json"), "%s has German text" % k)
		kit.ok(str(en.translated_by(k)).ends_with("en_terminal.json"), "%s has English text" % k)
		kit.ok(str(de.t(k)).length() >= 6 and str(en.t(k)).length() >= 6, "%s is not empty" % k)
		kit.ok(not str(de.t(k)).contains("\"") and not str(en.t(k)).contains("\""), "%s uses typographic quotes" % k)
	for id in STEPS:
		for lang in [de, en]:
			kit.ok(str(lang.t(str(entries[id]["text_key"]))).length() <= 520, "%s: the find text fits the discovery page (%s)" % [id, lang.language])
	# the number the roster gives is the one the machine takes, in both languages
	for lang in [de, en]:
		kit.ok(str(lang.t("explore.berlin.annex.term_roster.text")).contains(TermLogic.OPERATOR), "the roster names the operator number (%s)" % lang.language)
		kit.ok(str(lang.t("explore.berlin.annex.term_files.text")).contains(TermLogic.ANSWER), "the find names the released case (%s)" % lang.language)
	# every key of the two tables is twinned (the localisation suite checks placeholders and line counts)
	var a = _json("res://data/locale/de_terminal.json")
	var b = _json("res://data/locale/en_terminal.json")
	if kit.ok(a is Dictionary and b is Dictionary, "both locale files parse"):
		kit.eq(Kit.sorted((a["strings"] as Dictionary).keys()), Kit.sorted((b["strings"] as Dictionary).keys()), "same keys in both languages")
		var same: Array = []
		for k in a["strings"]:
			if str(a["strings"][k]) == str(b["strings"].get(k, "")) and str(a["strings"][k]).length() > 12 \
					and not str(k).begins_with("mg.term.kw.") and k != "task.berlin.planspiel.title" and k != "mg.abgang.title":
				same.append(k)
		kit.eq(same, [], "no long text left untranslated")
	return true


func _validation() -> bool:
	var real: Node = kit.track(load(EXPLORE).new())
	real.print_warnings = false
	real.notify_tasks = false
	real.reload()
	var mine: Array = []
	for w in real.warnings:
		var s := str(w)
		if s.contains("c4_annex_terminal") or s.contains(TASK) or s.contains("berlin.annex.term_") or s.contains("berlin.annex.planspiel"):
			mine.append(s)
	kit.eq(mine, [], "Explore validation: no problem in the data desk's file")
	for id in STEPS:
		kit.ok(real.has_entry(id), "Explore loaded %s" % id)
	kit.eq(str(real.task_of(STEPS[1])), TASK, "the roster is a step of the task")
	kit.eq(real.tasks_for("L_C4_AnnexA").map(func(t): return str(t["id"])).has(TASK), true, "the task belongs to the annex level key")
	kit.eq(str(real.task_state(TASK)["state"]), "not_started", "not started")
	kit.eq(bool(real.find(STEPS[2]).get("ok", false)), false, "the terminal cannot be found before the roster")
	kit.eq(bool(real.can_find(STEPS[1])), false, "the roster gives no prompt before the desk has been looked at")
	var hints := ["roster", "files", "run"]
	for i in STEPS.size():
		kit.ok(bool(real.find(STEPS[i]).get("ok", false)), "step %d found" % (i + 1))
		var st: Dictionary = real.task_state(TASK)
		if i < STEPS.size() - 1:
			kit.eq([str(st["state"]), int(st["step"]), str(st["hint_key"])], ["active", i + 1, "task.berlin.planspiel.hint." + hints[i]],
				"after step %d the journal names the next one" % (i + 1))
		else:
			kit.eq(str(st["state"]), "done", "done after the run")
	return true


# ================================================================ placement
func _mount(lid: String) -> Node:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("ambience", "")
	lvl.set("music", "")
	lvl.set("level_id", lid)
	Kit.root().add_child(lvl)
	return lvl


func _unmount(lvl: Node) -> void:
	if lvl != null and is_instance_valid(lvl):
		lvl.get_parent().remove_child(lvl)
		lvl.free()


func _spots(lvl: Node) -> Array:
	var out: Array = []
	for it in Kit.tree().get_nodes_in_group("interactables"):
		if is_instance_valid(it) and lvl.is_ancestor_of(it):
			out.append(it)
	return out


func _placement() -> bool:
	var man = _json(ENV + "scene.json")
	var lay = _json(ENV + "terminal/layout.json")
	if not kit.ok(man is Dictionary and lay is Dictionary, "scene.json and terminal/layout.json parse"):
		return true
	var mine: Array = (man.get("actors", []) as Array).filter(func(a): return str(a.get("scene")) == ACTOR)
	if kit.eq(mine.size(), 1, "one actor entry for the desk"):
		kit.eq(str(mine[0].get("scene_id")), "L_C4_AnnexB", "only built in scene D")
		kit.ok(str(mine[0].get("gen", "")) != "env_c4_annex", "a foreign actor: env_c4_annex.py keeps it on a re-run")
	var gen := FileAccess.get_file_as_string("res://tools/pixelgen/gen_annex_terminal.py")
	for call in ["KEEP.remove_own_pngs(", "KEEP.merge_scene(", "KEEP.write_json(", "KEEP.is_own("]:
		kit.ok(gen.contains(call), "the generator uses %s" % call)
	kit.ok(not gen.contains("import env_c4_annex
") and not gen.contains("import env_c4_annex as") and not gen.contains("subprocess"),
		"it never runs the annex generator")
	var prov = _json(ENV + "provenance.json")
	var rows: Array = (prov.get("files", []) as Array).filter(func(r): return str(r.get("generator")) == "tools/pixelgen/gen_annex_terminal.py")
	kit.ok(rows.size() >= 4, "its provenance rows (%d)" % rows.size())
	for r in rows:
		kit.ok(FileAccess.file_exists("res://" + str(r["path"])), "%s exists" % r["path"])
		kit.ok(not str(r["generator"]).begins_with("tools/pixelgen/env_c4_annex"), "not a row the annex generator would delete")
	# the art: binary alpha, palette-pure, a normal map of the same size
	var allowed := {}
	for rn in man.get("meta", {}).get("palette_ramps", {}):
		for hx in man["meta"]["palette_ramps"][rn]:
			allowed[str(hx).to_upper().trim_prefix("#")] = true
	for part in ["desk", "roster"]:
		var img := Image.load_from_file(ProjectSettings.globalize_path(ENV + "terminal/%s.png" % part))
		var nimg := Image.load_from_file(ProjectSettings.globalize_path(ENV + "terminal/%s_n.png" % part))
		if not kit.ok(img != null and nimg != null, "%s.png and its normal map exist" % part):
			continue
		kit.eq(nimg.get_size(), img.get_size(), "%s: normal map matches" % part)
		kit.eq(Vector2i(int(lay[part]["size"][0]), int(lay[part]["size"][1])), img.get_size(), "%s: layout size" % part)
		var bad := 0
		var soft := 0
		var solid := 0
		for y in img.get_height():
			for x in img.get_width():
				var c := img.get_pixel(x, y)
				if c.a > 0.0 and c.a < 1.0:
					soft += 1
				if c.a >= 1.0:
					solid += 1
					if not allowed.has(c.to_html(false).to_upper()):
						bad += 1
		kit.eq([bad, soft], [0, 0], "%s: every pixel an 'annex' palette colour, binary alpha" % part)
		kit.ok(solid >= 150, "%s: something is painted (%d px)" % [part, solid])
	var dp: Array = lay["desk"]["pos"]
	kit.ok(float(dp[0]) >= 1060.0 and float(dp[0]) + float(lay["desk"]["size"][0]) <= 1127.0,
		"the desk stands between the machine room (x < 1060) and the drawer bank (x >= 1127)")
	kit.ok(float(dp[1]) + float(lay["desk"]["size"][1]) <= 290.0, "it ends on the floor line, behind the walk band")
	# the real level: the actor is there in scene D only, its spots stand where the layout says
	var loop := _mount("L_C4_AnnexA")
	kit.ok(loop.get_node_or_null("Playfield/AnnexTerminal") == null, "tram loop (scene B): no desk is built")
	_unmount(loop)
	var lvl := _mount("L_C4_AnnexB")
	var desk: Node = null
	for c in lvl.get_node("Playfield").get_children():
		if c.get_script() != null and str((c.get_script() as Script).resource_path).ends_with("annex_terminal.gd"):
			desk = c
	if not kit.ok(desk != null, "annex (scene D): the level spawns the desk actor"):
		_unmount(lvl)
		return true
	kit.ok(desk.get_node_or_null("Desk") is Sprite2D and (desk.get_node("Desk") as Sprite2D).texture is CanvasTexture, "the desk is a lit sprite with its normal map")
	kit.eq((desk.get_node("Desk") as Node2D).global_position, Vector2(float(dp[0]), float(dp[1])), "at its world position")
	kit.ok(desk.get_node_or_null("Roster") is Sprite2D, "the roster hangs there too")
	kit.ok((desk as Node2D).position.y < 296.0, "the actor sorts behind the walk band (y %d)" % int((desk as Node2D).position.y))
	var walk := PackedVector2Array()
	for q in man.get("walkable", []):
		walk.append(Vector2(float(q[0]), float(q[1])))
	var own: Array = [desk.get("desk_spot"), desk.get("roster_spot")]
	var names := ["exp_terminal", "exp_terminal_roster"]
	for i in 2:
		var it: Node2D = own[i]
		if not kit.ok(it != null and it.is_in_group("interactables"), "%s is an interactable" % names[i]):
			continue
		var pos := it.global_position
		kit.eq(str((it.get_script() as Script).resource_path), "res://scripts/ui/minigames/lever_spot.gd", "%s: the Chapter-4 spot script" % names[i])
		kit.eq(pos, Vector2(float(lay["spots"][names[i]][0]), float(lay["spots"][names[i]][1])), "%s stands where the layout says" % names[i])
		kit.eq(pos, Vector2(float(man["hotspots"][names[i]][0]), float(man["hotspots"][names[i]][1])), "%s is named in scene.json" % names[i])
		kit.ok(Geometry2D.is_point_in_polygon(pos, walk), "%s lies in the walk band" % names[i])
		kit.ok(pos.x >= AREA_B[0] and pos.x <= AREA_B[1], "%s lies in the annex's walk area" % names[i])
		kit.eq([str(it.get("kind")), bool(it.get("once")), str(it.get("after_objective")), Array(it.get("memory_scenes"))],
			["discover", true, "c4b_inspect_crates", ["L_C4_AnnexB"]], "%s: gates like every find of scene D" % names[i])
		for s in STORY_SPOTS:
			var sp := Vector2(float(man["hotspots"][s][0]), float(man["hotspots"][s][1]))
			kit.ok(pos.distance_to(sp) >= GAP_STORY, "%s keeps %d px from %s (%.0f)" % [names[i], int(GAP_STORY), s, pos.distance_to(sp)])
		for o in _spots(lvl):
			if o == it or not (str(o.get("kind")) in ["discover", "chat"]):
				continue
			kit.ok(pos.distance_to((o as Node2D).global_position) >= GAP_FIND, "%s keeps %d px from %s (%.0f)" % [names[i], int(GAP_FIND), o.name,
				pos.distance_to((o as Node2D).global_position)])
		for spn in man.get("spawns", {}):
			kit.ok(pos.distance_to(Vector2(float(man["spawns"][spn][0]), float(man["spawns"][spn][1]))) >= 20.0, "%s keeps clear of the spawn %s" % [names[i], spn])
		for bl in man.get("blockers", []):
			var r: Array = bl.get("rect", [])
			kit.ok(pos.x < float(r[0]) - 6.0 or pos.x > float(r[0]) + float(r[2]) + 6.0, "%s keeps clear of the blocker" % names[i])
	kit.eq(Array(own[0].get("explore_chain")), [STEPS[0], STEPS[2], STEPS[3]], "the desk hosts the chain desk -> terminal -> Planspiel")
	kit.eq([str(own[0].get("explore_id")), str(own[1].get("explore_id"))], [STEPS[0], STEPS[1]], "what the spots show in a new game")
	# the focus picture: the roster's painting is near its spot, the desk's too
	kit.ok(absf(float(lay["roster"]["pos"][0]) - own[1].global_position.x) <= 24.0, "the roster hangs where Konrad reads it")
	_unmount(lvl)
	return true


# ================================================================ the real nodes
func _real_path() -> bool:
	var st: Node = Kit.root().get_node_or_null("Story")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	var game: Node = Kit.root().get_node_or_null("Game")
	if st == null or ex == null or game == null:
		print("      note: autoloads missing, real-path check skipped")
		return true
	var keep := {"story": st.save_json(), "explore": ex.state(), "notify": ex.notify_tasks, "mm": game.memory_mode, "ms": game.memory_scene}
	ex.notify_tasks = false
	game.memory_mode = false
	ex.restore({"found": [], "cards": []})
	st.new_game()
	var lvl := _mount("L_C4_AnnexB")
	var mine: Array = _spots(lvl).filter(func(it): return str(it.get("hotspot_id")).begins_with("exp_terminal"))
	kit.eq(mine.size(), 2, "two spots of the desk on the real level")
	kit.eq(mine.filter(func(it): return it.is_active()).size(), 0, "before c4b_inspect_crates nothing is offered")
	kit.play_until(st, "c4b")
	kit.eq(str(st.objective_state("c4b_inspect_crates")), "complete", "the Story has climbed down the shaft")
	var before: String = st.save_json()
	kit.eq(mine.filter(func(it): return it.is_active()).map(func(it): return str(it.explore_id)), [STEPS[0]], "in scene D the desk is offered, the roster not yet")
	kit.eq(str(mine.filter(func(it): return it.is_active())[0].prompt_state()), "task", "its prompt carries the task mark")
	# the drivers' loop (autoplay.pending_finds + Explore.find), restricted to the desk's spots
	var ap: GDScript = load(AUTOPLAY)
	var order: Array = []
	var tried := {}
	for guard in 40:
		var it: Node = null
		for cand in ap.pending_finds(mine, ex):
			if not tried.has("%d:%s" % [cand.get_instance_id(), cand.explore_id]):
				it = cand
				break
		if it == null:
			break
		var id := str(it.explore_id)                   # the chain moves on as soon as the find is recorded
		tried["%d:%s" % [it.get_instance_id(), id]] = true
		it.used = true
		if bool(ex.find(id).get("ok", false)):
			order.append(id)
	kit.eq(order, STEPS, "the drivers' loop finds the four steps in the task's order")
	kit.eq(str(ex.task_state(TASK)["state"]), "done", "and the task is done")
	kit.eq(st.save_json(), before, "exploring the desk never touches the Story")
	kit.eq(mine.filter(func(it): return it.is_active()).size(), 0, "afterwards the once-spots are quiet")
	# a memory: the remembered scene decides
	ex.restore({"found": [], "cards": []})
	st.new_game()
	game.memory_mode = true
	game.memory_scene = "L_C4_AnnexB"
	kit.eq(mine.filter(func(it): return it.is_active()).map(func(it): return str(it.explore_id)), [STEPS[0]], "memory of the annex: the desk is open")
	game.memory_scene = "L_C4_AnnexA"
	kit.eq(mine.filter(func(it): return it.is_active()).size(), 0, "memory of the tram loop: it is not")
	game.memory_mode = keep["mm"]
	game.memory_scene = keep["ms"]
	_unmount(lvl)
	if not st.load_json(str(keep["story"])).get("ok", false):
		st.new_game()
	ex.restore(keep["explore"])
	ex.notify_tasks = keep["notify"]
	return true


# ================================================================ terminal: rule
func _term(lang: Node) -> RefCounted:
	var lg = TermLogic.new()
	lg.tr_fn = func(k: String, a: Dictionary) -> String: return str(lang.t(k, a))
	return lg


func _login(lg) -> void:
	for ch in TermLogic.OPERATOR:
		lg.digit(int(ch))
	lg.ok()


func _term_logic() -> bool:
	for lang in [de, en]:
		var tag := str(lang.language)
		var lg = _term(lang)
		kit.eq([lg.phase, lg.entered()], ["login", "0000"], "%s: starts at the login" % tag)
		lg.digit(1)
		lg.digit(2)
		kit.eq([lg.entered(), lg.digit_cursor], ["1200", 2], "%s: typed digits fill from the left" % tag)
		kit.eq([lg.ok(), lg.fails, lg.refused, lg.phase], ["login_fail", 1, "login", "login"], "%s: a wrong number is refused" % tag)
		lg.move(-1, 0)
		lg.move(0, -1)
		kit.eq(lg.entered(), "1300", "%s: Left chooses a digit, Up turns it" % tag)
		lg.reset()
		_login(lg)
		kit.eq([lg.phase, lg.fails], ["menu", 0], "%s: %s logs in" % [tag, TermLogic.OPERATOR])
		kit.eq(lg.item_count(), 3, "%s: three commands" % tag)
		# the files: line length, letters, the same shape in both languages
		for f in TermLogic.FILES:
			var lines: PackedStringArray = lg.file_lines(f)
			kit.ok(lines.size() >= 5 and lines.size() <= 12, "%s: file %s has %d lines" % [tag, f, lines.size()])
			kit.eq(lines.size(), _term(de).file_lines(f).size(), "%s: file %s has the German line count" % [tag, f])
			for line in lines:
				kit.ok(str(line).length() <= TermLogic.MAX_LINE, "%s: %s line fits %d columns: %s" % [tag, f, TermLogic.MAX_LINE, line])
				kit.ok(Crt.supports(str(line)), "%s: %s line can be lettered: %s" % [tag, f, line])
		var cases: Array = lg.cases()
		kit.eq(cases.map(func(c): return str(c["id"])), ["S8-031", "S8-044", "S8-052", "S8-067", "S8-073", "S8-080"], "%s: six households in the list" % tag)
		kit.ok(str(cases[3]["label"]).contains("LINDNER"), "%s: the answer is the Lindner household" % tag)
		# the cross-reference: keyword 3 (open) hits the list AND the memo
		lg.cursor = 2
		lg.ok()
		kit.eq(lg.phase, "search", "%s: SUCHEN asks for a keyword" % tag)
		lg.cursor = 2
		lg.ok()
		var files := {}
		for r in lg.results:
			files[str(r["file"])] = true
		kit.ok(files.has("ueb45") and files.has("vermerk"), "%s: the keyword „open“ is found in the list and in the memo %s" % [tag, files.keys()])
		kit.ok(lg.results.any(func(r): return str(r["text"]).begins_with(TermLogic.ANSWER)), "%s: one hit is the open household's row" % tag)
		kit.ok(lg.known_cases, "%s: a hit in the list loads the case numbers" % tag)
		kit.eq([lg.ok(), lg.phase, lg.view_from], ["open", "view", "results"], "%s: a hit opens its file" % tag)
		kit.eq([lg.back(), lg.phase, lg.back(), lg.phase, lg.back(), lg.phase], ["back", "results", "back", "search", "back", "menu"], "%s: back, step by step" % tag)
		kit.eq(lg.back(), "", "%s: at the menu there is nothing to go back to" % tag)
		# release: unknown before the list is read, refused for a complete household, granted for S8-067
		var fresh = _term(lang)
		_login(fresh)
		fresh.cursor = 1
		fresh.ok()
		fresh.cursor = TermLogic.FILES.size()
		kit.eq([fresh.ok(), fresh.phase, fresh.item_count()], ["locked", "release", 0], "%s: the program is locked, no case numbers yet" % tag)
		kit.eq([fresh.ok(), fresh.fails], ["release_unknown", 0], "%s: confirming without the list is no failure" % tag)
		fresh.back()
		fresh.cursor = 0
		kit.eq([fresh.ok(), fresh.view_file, fresh.known_cases, fresh.read.has("ueb45")], ["open", "ueb45", true, true], "%s: reading the list loads them" % tag)
		fresh.back()
		fresh.cursor = TermLogic.FILES.size()
		fresh.ok()
		kit.eq(fresh.item_count(), 6, "%s: six case numbers to choose from" % tag)
		fresh.cursor = 0
		kit.eq([fresh.ok(), fresh.fails, fresh.refused, fresh.released], ["release_fail", 1, "release", false], "%s: a complete household is refused" % tag)
		fresh.cursor = 3
		kit.eq([fresh.ok(), fresh.released, fresh.phase], ["release_ok", true, "done"], "%s: %s releases the program" % [tag, TermLogic.ANSWER])
		# the memo names the rule, the log the eleven runs, the scheme the unguarded breach
		kit.ok(" ".join(lg.file_lines("buch")).contains("11"), "%s: the log counts eleven runs" % tag)
		kit.ok(lg.file_lines("buch")[lg.file_lines("buch").size() - 1].contains(TermLogic.OPERATOR), "%s: its last line is today's login under the number" % tag)
		kit.ok(" ".join(lg.file_lines("schema")).contains("1941"), "%s: the scheme names the 1941 breach" % tag)
	return true


func _term_screens() -> bool:
	for lang in [de, en]:
		for g in RASTERS:
			var lg = _term(lang)
			var states: Array = []
			var shoot := func(label: String) -> void:
				var scr: Dictionary = lg.screen(g.x, g.y)
				states.append(label)
				for run in scr["runs"]:
					var ok: bool = int(run["r"]) >= 0 and int(run["r"]) < g.y and int(run["c"]) >= 0 \
						and int(run["c"]) + str(run["t"]).length() <= g.x
					if not ok:
						kit.fail("%s %s %s: text outside the raster: %s" % [lang.language, g, label, run])
					if not Crt.supports(str(run["t"])):
						kit.fail("%s %s: cannot be lettered: %s" % [lang.language, label, run["t"]])
				var rows := {}
				for run in scr["runs"]:
					var key := "%d" % int(run["r"])
					for other in rows.get(key, []):
						var a0 := int(run["c"])
						var a1 := a0 + str(run["t"]).length()
						if a0 < int(other[1]) and int(other[0]) < a1:
							kit.fail("%s %s %s: two texts overlap in row %s" % [lang.language, g, label, key])
					rows[key] = (rows.get(key, []) as Array) + [[int(run["c"]), int(run["c"]) + str(run["t"]).length()]]
			shoot.call("login")
			lg.ok()
			shoot.call("login refused")
			_login(lg)
			shoot.call("menu")
			lg.cursor = 0
			lg.ok()
			shoot.call("list")
			lg.back()
			lg.cursor = 1
			lg.ok()
			shoot.call("open")
			for i in TermLogic.FILES.size():
				lg.cursor = i
				lg.ok()
				shoot.call("view " + TermLogic.FILES[i])
				kit.ok(lg.view_rows >= 7, "%s %s: a file shows at least 7 rows (%d)" % [lang.language, g, lg.view_rows])
				for k in 12:
					lg.move(0, 1)
				shoot.call("view scrolled")
				var n: int = lg.file_lines(TermLogic.FILES[i]).size()
				kit.eq(lg.view_top, maxi(0, n - lg.view_rows), "%s %s: scrolling stops at the last line" % [lang.language, g])
				lg.back()
			lg.cursor = TermLogic.FILES.size()
			lg.ok()
			shoot.call("release")
			lg.cursor = 1
			lg.ok()
			shoot.call("release refused")
			lg.back()
			lg.back()
			lg.cursor = 2
			lg.ok()
			shoot.call("search")
			for kw in TermLogic.KEYWORDS:
				lg.cursor = kw
				lg.ok()
				shoot.call("results %d" % kw)
				kit.ok(not lg.results.is_empty(), "%s: keyword %d finds something" % [lang.language, kw + 1])
				for k in lg.results.size():
					lg.move(0, 1)
					shoot.call("results moved")
				lg.back()
			lg.back()
			lg.cursor = 1
			lg.ok()
			lg.cursor = TermLogic.FILES.size()
			lg.ok()
			lg.cursor = 3
			lg.ok()
			shoot.call("done")
			kit.ok(states.size() >= 20, "%s %s: every screen was laid out (%d)" % [lang.language, g, states.size()])
	kit.eq([Crt.grid(TermGame.ART), Crt.grid(TermGame.ART_COMPACT)], RASTERS, "the two rasters of the game")
	return true


# ================================================================ terminal: scene
func _term_scene() -> bool:
	var mg := _mg(TERM_SCENE)
	kit.ok(mg.is_in_group("minigame"), "DataTerminal joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": STEPS[2], "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var tg := _mg(TERM_SCENE)
	var res: Array = []
	tg.finished.connect(func(ok: bool): res.append(ok))
	tg.open({"explore_id": STEPS[2], "auto": false})
	_steps(tg, 0.4)
	kit.ok(tg._tube.texture is ImageTexture and (tg._tube.texture as Texture2D).get_size() == Vector2(TermGame.ART), "the picture is a 384x172 raster")
	kit.eq([tg._tube.size, tg.S], [Vector2(TermGame.ART) * 3.0, 3], "shown x3 (the game's pixel grid)")
	kit.ok(tg._tube.material is ShaderMaterial, "through the phosphor shader")
	tg.modal_input(_key(KEY_1))
	tg.modal_input(_key(KEY_9))
	kit.eq(tg.logic.entered(), "1900", "digit keys type the number")
	tg.modal_input(_key(KEY_E))
	kit.ok(tg.fails == 1 and not tg._hint_box.visible, "a wrong number is a refusal, no hint yet")
	kit.ok(str(tg._status.text).contains("unbekannt"), "the status quotes the machine")
	tg.modal_input(_key(KEY_ENTER))
	kit.ok(tg.fails == 2 and tg._hint_box.visible, "a hint after two refusals")
	kit.ok(str(tg._hint_label.text).contains("Dienstplan"), "the first hint: where the roster hangs")
	tg.modal_input(_key(KEY_ENTER))
	kit.ok(str(tg._hint_label.text).contains(TermLogic.OPERATOR), "the second hint names the number")
	tg.modal_input(_key(KEY_R))
	kit.eq([tg.logic.entered(), tg._hint_box.visible], ["0000", false], "R logs out and starts over")
	for ch in TermLogic.OPERATOR:
		tg.modal_input(_key(KEY_0 + int(ch)))
	tg.modal_input(_key(KEY_ENTER))
	kit.eq(tg.logic.phase, "menu", "the right number logs in")
	tg.modal_input(_key(KEY_DOWN))
	kit.eq(tg.logic.cursor, 1, "Down moves the line")
	tg.modal_input(_key(KEY_E))
	kit.eq(tg.logic.phase, "open", "E runs the command")
	kit.ok(tg.handle_cancel() and tg.logic.phase == "menu" and res.is_empty(), "Esc first goes one step back")
	# mouse: a click on a line runs it, the wheel moves, right click goes back
	_steps(tg, 0.1)
	var row := 3 + 1                                   # the second command
	var mb := InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = true
	mb.position = Crt.tube_rect(TermGame.ART, 3).position + Vector2(3 + 4 * 6 + 2, 3 + row * 10 + 4) * 3.0
	tg.stage_input(mb)
	kit.eq(tg.logic.phase, "open", "a click on ÖFFNEN opens the file list")
	var wd := InputEventMouseButton.new()
	wd.button_index = MOUSE_BUTTON_WHEEL_DOWN
	wd.pressed = true
	tg.stage_input(wd)
	kit.eq(tg.logic.cursor, 1, "the wheel moves the line")
	var rb := InputEventMouseButton.new()
	rb.button_index = MOUSE_BUTTON_RIGHT
	rb.pressed = true
	tg.stage_input(rb)
	kit.eq(tg.logic.phase, "menu", "right click goes back")
	kit.ok(tg.handle_cancel(), "Esc at the menu is handled")
	kit.eq(res, [false], "and gives up without a find")
	return true


func _term_full() -> bool:
	var tg := _mg(TERM_SCENE)
	var res: Array = []
	tg.finished.connect(func(ok: bool): res.append(ok))
	tg.open({"explore_id": STEPS[2], "auto": false})
	_steps(tg, 0.4)
	for ch in TermLogic.OPERATOR:
		tg.modal_input(_key(KEY_0 + int(ch)))
	tg.modal_input(_key(KEY_ENTER))
	tg.modal_input(_key(KEY_DOWN))
	tg.modal_input(_key(KEY_ENTER))                    # ÖFFNEN
	tg.modal_input(_key(KEY_ENTER))                    # the transfer list
	_steps(tg, 0.1)
	kit.eq([tg.logic.phase, tg.logic.view_file], ["view", "ueb45"], "the list is on the screen")
	tg.modal_input(_key(KEY_BACKSPACE))
	for i in TermLogic.FILES.size():
		tg.modal_input(_key(KEY_DOWN))
	tg.modal_input(_key(KEY_ENTER))                    # the locked program
	kit.eq(tg.logic.phase, "release", "the program asks for its release")
	for i in 3:
		tg.modal_input(_key(KEY_DOWN))
	tg.modal_input(_key(KEY_ENTER))
	kit.ok(tg.solved and tg.fails == 0, "released by keys alone, no refusal on the right way")
	kit.ok(str(tg._status.text).contains(TermLogic.ANSWER), "the status names the case")
	_steps(tg, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(tg, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string("res://scripts/ui/minigames/terminal_game.gd")
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.ok(") and not body.contains("logic.digit(") and not body.contains("_act(")
		and not body.contains("mark_solved("), "demo_solve drives the terminal through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "DataTerminal extends minigame_base.gd")
	return true


# ================================================================ Planspiel: rule
func _ab_logic() -> bool:
	var lg = AbLogic.new()
	kit.eq(AbLogic.map_count(), 3, "three maps")
	kit.eq(AbLogic.MAPS.map(func(m): return str(m["id"])), ["street", "yard", "attic"], "street, courtyard, stairwell and attic")
	kit.ok(is_equal_approx(AbLogic.TICK * AbLogic.STEP_TICKS, 0.25) and AbLogic.BEAT_TICKS == AbLogic.STEP_TICKS * 3, "a step 0.25 s, a beat three steps")
	var total := 0
	for i in AbLogic.map_count():
		lg.load_map(i)
		var tag := "map %d (%s)" % [i + 1, lg.id]
		for row in lg.rows:
			kit.eq(str(row).length(), lg.w, "%s: every row is %d wide" % [tag, lg.w])
		kit.ok(lg.w <= 16 and lg.h <= 10, "%s: a small map" % tag)
		kit.ok(lg.walkable(lg.start) and lg.walkable(lg.goal) and lg.start != lg.goal, "%s: start and gap are floor" % tag)
		kit.eq(lg.patrols.size(), 2, "%s: two posts" % tag)
		for p in lg.patrols.size():
			kit.ok(lg.patrol_closed(p), "%s: post %d's rhythm closes" % [tag, p + 1])
			var cycle: Array = lg.patrols[p]
			for b in cycle.size():
				var a: Array = cycle[b]
				var nx: Array = cycle[(b + 1) % cycle.size()]
				kit.ok(lg.walkable(Vector2i(int(a[0]), int(a[1]))), "%s: post %d stands on floor at beat %d" % [tag, p + 1, b])
				kit.ok(absi(int(a[0]) - int(nx[0])) + absi(int(a[1]) - int(nx[1])) <= 1, "%s: post %d walks one cell per beat" % [tag, p + 1])
		kit.ok(lg.period <= 60, "%s: the rhythm repeats within %d beats" % [tag, lg.period])
		var start_seen := 0
		var goal_free := 0
		for b in lg.period:
			start_seen += 1 if lg.seen_at(lg.start, b) != 0 else 0
			goal_free += 1 if lg.seen_at(lg.goal, b) == 0 else 0
			for p in lg.patrols.size():
				var cells: Array = lg.beams[b][p]
				kit.ok(cells.size() <= 10, "%s: a beam is at most ten cells" % tag)
				var st: Array = lg.post_state(p, b)
				for c in cells:
					if not (lg.walkable(c) and lg.los(Vector2i(int(st[0]), int(st[1])), c)
							and absi(lg.lift_at(c) - lg.lift_at(Vector2i(int(st[0]), int(st[1])))) <= 1):
						kit.fail("%s: post %d sees %s through cover at beat %d" % [tag, p + 1, c, b])
		kit.eq(start_seen, 0, "%s: no post ever sees the start" % tag)
		kit.ok(goal_free > 0, "%s: the gap is unseen at some beat" % tag)
		var s0: Dictionary = lg.solve_stats(0)
		var s1: Dictionary = lg.solve_stats(1)
		var s2: Dictionary = lg.solve_stats(2)
		kit.ok(bool(s0["ok"]) and bool(s1["ok"]), "%s: there is a way through, also with a whole step of hesitation at every move" % tag)
		kit.ok(bool(s2["ok"]), "%s: even with two steps (0.5 s) of slack — fair" % tag)
		kit.ok(int(s1["waits"]) >= 1, "%s: the way needs a wait (%d units)" % [tag, int(s1["waits"])])
		kit.ok(int(s1["units"]) * 0.25 <= 25.0, "%s: the solver needs %.1f s" % [tag, int(s1["units"]) * 0.25])
		var naive: Array = lg.shortest_dirs()
		kit.ok(naive.size() >= 12, "%s: the gap is at least 12 steps away (%d)" % [tag, naive.size()])
		kit.eq(lg.run_dirs(naive), "seen", "%s: the shortest way, walked at once, is caught" % tag)
		total += int(s1["units"])
	print("      note: the solver's run through the three maps takes %.1f s (%d steps of 0.25 s)" % [total * 0.25, total])
	kit.ok(total * 0.25 >= 15.0 and total * 0.25 <= 60.0, "the three maps together: a short game (solver %.1f s)" % (total * 0.25))
	# stepping, cover, arrest, restart
	lg.load_map(0)
	kit.eq(lg.char_at(Vector2i(10, 2)), "o", "map 1: the advertising column")
	kit.ok(not lg.walkable(Vector2i(10, 2)) and not lg.los(Vector2i(14, 2), Vector2i(9, 2)), "it blocks the way and the view")
	lg.want = 1
	var moved := 0
	for i in AbLogic.STEP_TICKS * 3:
		if lg.step() == "moved":
			moved += 1
	kit.eq([moved, lg.cell], [3, lg.start + Vector2i(3, 0)], "holding a direction: one cell every %d ticks" % AbLogic.STEP_TICKS)
	lg.want = 2
	var bumps := 0
	for i in AbLogic.STEP_TICKS * 2:
		if lg.step() == "bump":
			bumps += 1
	kit.ok(bumps >= 1 and lg.cell == lg.start + Vector2i(3, 0) and lg.move_left == 0, "the map's edge stops the figure")
	lg.reset()
	kit.eq([lg.tick, lg.cell, lg.want], [0, lg.start, -1], "reset: beat 0, at the start")
	var ev := ""
	var dirs: Array = lg.shortest_dirs()               # the shortest way at once: into a beam
	lg.want = int(dirs[0])
	for i in 2000:
		ev = lg.step()
		if ev == "moved":
			lg.want = int(dirs[lg.steps]) if lg.steps < dirs.size() else -1
		if ev == "seen" or ev == "exit":
			break
	kit.eq([ev, lg.caught], ["seen", true], "walking into a beam is an arrest")
	kit.ok(lg.caught_by in [0, 1] and lg.seen_at(lg.cell, lg.beat()) != 0, "by the post who sees that cell (post %d)" % (lg.caught_by + 1))
	kit.eq(lg.step(), "", "after the arrest nothing moves")
	# stairs: one step of height at a time, floors cover
	lg.load_map(2)
	kit.ok(lg.passable(Vector2i(9, 7), Vector2i(10, 7)) and lg.passable(Vector2i(10, 4), Vector2i(10, 3)), "the stairs connect hall and attic")
	kit.ok(lg.lift_at(Vector2i(10, 3)) - lg.lift_at(Vector2i(9, 7)) == 5, "five steps up")
	for b in lg.period:
		for x in range(1, 9):
			if lg.seen_at(Vector2i(x, 6), b) != 0:
				kit.fail("map 3: a post under the roof sees the hall floor at beat %d" % b)
	kit.ok(lg.trace(6, 1).size() >= 1, "the hint trace knows a next cell from the start")
	return true


# ================================================================ Planspiel: scene
func _hold_keys(ab: Node, held: int, want: int) -> int:
	if want != held:
		if held >= 0:
			ab.modal_input(_key(AbGame.DIR_KEYS[held], false))
		if want >= 0:
			ab.modal_input(_key(AbGame.DIR_KEYS[want], true))
	return want


func _ab_scene() -> bool:
	var mg := _mg(AB_SCENE)
	kit.ok(mg.is_in_group("minigame"), "PlanspielAbgang joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": STEPS[3], "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var ab := _mg(AB_SCENE)
	var res: Array = []
	ab.finished.connect(func(ok: bool): res.append(ok))
	ab.open({"explore_id": STEPS[3], "auto": false})
	kit.eq([ab.logic.index, ab.logic.tick], [0, 0], "opens on map 1 at beat 0")
	_steps(ab, 0.5)
	kit.eq(ab.logic.tick, 0, "the map is shown before the posts start (fly-in)")
	_steps(ab, 0.4)
	kit.ok(ab.logic.tick > 0, "then the beat runs")
	ab.modal_input(_key(KEY_RIGHT, true))
	_steps(ab, 0.3)
	ab.modal_input(_key(KEY_RIGHT, false))
	_steps(ab, 0.3)
	kit.ok(ab.logic.cell.x >= 1 and ab.logic.cell.y == ab.logic.start.y and ab.logic.move_left == 0, "Right held walks east, released stops (%s)" % ab.logic.cell)
	ab.modal_input(_key(KEY_A, true))
	_steps(ab, 0.3)
	ab.modal_input(_key(KEY_A, false))
	_steps(ab, 0.3)
	kit.ok(ab.logic.cell.x <= 1, "A walks west like Left")
	# three arrests: status names the post, the map starts again, then the tip, then the trace
	for n in 3:
		var dirs: Array = ab.logic.shortest_dirs()         # the shortest way, at once: into a beam
		var held := -1
		var guard := 0
		while not ab.logic.caught and guard < 1200:
			guard += 1
			held = _hold_keys(ab, held, int(dirs[ab.logic.steps]) if ab.logic.steps < dirs.size() else -1)
			ab._process(0.05)
		held = _hold_keys(ab, held, -1)
		kit.ok(ab.logic.caught, "arrest %d: the shortest way runs into a beam" % (n + 1))
		kit.eq([ab.fails, ab.map_fails], [n + 1, n + 1], "counted")
		kit.ok(str(ab._status.text).contains("Posten %d" % (int(ab.logic.caught_by) + 1)) and str(ab._status.text).contains("Zugriff"), "the status names the post")
		kit.eq(ab._lamp, 2, "the lamp of the housing turns amber")
		_steps(ab, AbGame.SEEN_HOLD + 0.1)
		kit.eq([ab.logic.caught, ab.logic.cell, ab.logic.index], [false, ab.logic.start, 0], "the same map starts again at beat 0")
		if n == 0:
			kit.ok(not ab._hint_box.visible and not ab.trace_on, "one arrest: no hint yet")
		elif n == 1:
			kit.ok(ab._hint_box.visible and str(ab._hint_label.text).contains("Fahrbahn") and not ab.trace_on, "two arrests: the tip for this map")
		else:
			kit.ok(ab.trace_on and str(ab._hint_label.text).contains("Spur"), "three arrests: the display draws the trace")
	ab.modal_input(_key(KEY_R))
	kit.eq([ab.fails, ab.logic.tick], [3, 0], "R starts the map again without counting an arrest")
	# the mouse: holding the button walks toward the pointer
	_steps(ab, 0.9)
	var me: Vector2 = ab.project(ab.cell_pos(ab.logic.cell, 0.0)) * 3.0 + Crt.tube_rect(ab.art, 3).position
	kit.eq([ab.dir_toward(me + Vector2(200, 0)), ab.dir_toward(me + Vector2(-200, 0)), ab.dir_toward(me + Vector2(0, -120)), ab.dir_toward(me)],
		[1, 3, 0, -1], "east, west, north of the figure; on it: nothing")
	var mb := InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = true
	mb.position = me + Vector2(200, 0)
	var x0: int = ab.logic.cell.x
	ab.stage_input(mb)
	_steps(ab, 0.3)
	mb = InputEventMouseButton.new()
	mb.button_index = MOUSE_BUTTON_LEFT
	mb.pressed = false
	mb.position = me + Vector2(200, 0)
	ab.stage_input(mb)
	_steps(ab, 0.3)
	kit.ok(ab.logic.cell.x > x0 and ab.logic.want == -1, "a held click walks east and stops on release")
	# a pad
	var jb := InputEventJoypadButton.new()
	jb.button_index = JOY_BUTTON_DPAD_LEFT
	jb.pressed = true
	ab.modal_input(jb)
	kit.eq(ab.logic.want, 3, "d-pad left is held")
	jb = InputEventJoypadButton.new()
	jb.button_index = JOY_BUTTON_DPAD_LEFT
	jb.pressed = false
	ab.modal_input(jb)
	kit.eq(ab.logic.want, -1, "and released")
	kit.ok(ab.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	return true


func _ab_full() -> bool:
	var ab := _mg(AB_SCENE)
	var res: Array = []
	ab.finished.connect(func(ok: bool): res.append(ok))
	ab.open({"explore_id": STEPS[3], "auto": false})
	var held := -1
	var maps := {}
	var guard := 0
	while not ab.solved and guard < 6000:
		guard += 1
		maps[int(ab.logic.index)] = true
		var want := -1
		if ab._hold <= 0.0:
			want = int(ab.logic.demo_action(1))
		held = _hold_keys(ab, held, want)
		ab._process(0.05)
	_hold_keys(ab, held, -1)
	kit.ok(ab.solved, "through all three maps by held keys alone (%d ticks)" % guard)
	kit.eq(ab.fails, 0, "never seen on the solver's way")
	kit.eq(maps.keys(), [0, 1, 2], "street, courtyard, attic")
	kit.ok(guard * 0.05 <= 60.0, "the demo's run takes %.1f s" % (guard * 0.05))
	kit.ok(str(ab._status.text).contains("Abgang") and str(ab._status.text).contains("Fernschreiber"), "the last line: the teleprinter starts")
	_steps(ab, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(ab, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string("res://scripts/ui/minigames/abgang_game.gd")
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_key_event(") and not body.contains("logic.step(") and not body.contains("logic.want =") and not body.contains("_set_dir(")
		and not body.contains("load_map(") and not body.contains("mark_solved("), "demo_solve drives the figure through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "PlanspielAbgang extends minigame_base.gd")
	return true


func _ab_picture() -> bool:
	var ab := _mg(AB_SCENE)
	ab.open({"explore_id": STEPS[3], "auto": false})
	_steps(ab, 0.9)
	var vp: SubViewport = ab._vp
	kit.eq([vp.size, vp.own_world_3d, vp.msaa_3d, vp.use_taa], [AbGame.ART, true, Viewport.MSAA_DISABLED, false], "a 384x172 SubViewport with its own 3D world, no smoothing")
	kit.ok(AbGame.ART.x * 3 + AbGame.SIDE_W + 36 + (Crt.SIDE + 2 * Crt.BEZEL) * 3 <= 1740, "tube and the texts beside it fit the panel width")
	kit.ok(ab._subtitle.get_parent() == ab._instr.get_parent() and ab._subtitle.get_parent().get_parent() == ab._stage.get_parent(), "flavour and instruction stand beside the tube")
	kit.ok(ab._cam is Camera3D and ab._cam.get_parent() == vp and ab._cam.projection == Camera3D.PROJECTION_PERSPECTIVE, "a perspective Camera3D draws it")
	kit.eq(ab._tube.size, Vector2(AbGame.ART) * 3.0, "shown x3: every art pixel is 3x3 screen pixels")
	ab._stage.position += Vector2(1, 2)                # wherever the layout puts the housing ...
	_steps(ab, 0.1)
	var gp: Vector2 = ab._tube.global_position
	kit.ok(is_zero_approx(fposmod(gp.x, 3.0)) and is_zero_approx(fposmod(gp.y, 3.0)), "... the picture snaps to the 640x360 pixel grid (%s)" % gp)
	kit.ok(ab._tube.position.distance_to(Vector2(Crt.BEZEL, Crt.BEZEL) * 3.0) < 3.0, "by less than one art pixel")
	kit.eq(ab._tube.texture_filter, CanvasItem.TEXTURE_FILTER_NEAREST, "nearest filter")
	kit.ok(ab._tube.material is ShaderMaterial and (ab._tube.material as ShaderMaterial).shader.code.contains("floor(UV * art)"), "the phosphor shader works per art pixel")
	kit.ok(not Crt.TUBE_SHADER.contains("smoothstep") and not Crt.TUBE_SHADER.contains("mix("), "palette steps only: no blend, no gradient")
	kit.ok(Crt.LINE_SHADER.contains("unshaded") and Crt.LINE_SHADER.contains("depth_test_disabled"), "the 3D lines are unshaded and never hidden")
	for i in AbLogic.map_count():
		ab._load_map(i)
		var mesh: Mesh = ab._static_mi.mesh
		kit.ok(mesh != null and mesh.get_surface_count() == 1 and ab.line_count() >= 120, "map %d: %d wire segments" % [i + 1, ab.line_count()])
		kit.eq([(ab._sv as PackedVector3Array).size(), (ab._sc as PackedColorArray).size()], [ab.line_count() * 2, ab.line_count() * 2], "map %d: a coloured line list" % (i + 1))
		var high := 0.0
		for v in (ab._sv as PackedVector3Array):
			high = maxf(high, v.y)
		kit.ok(high >= 1.0, "map %d: the wire has height (%.1f) — real 3D, not a plan" % [i + 1, high])
		_steps(ab, 1.0)
		for corner in [Vector3(0, 0, 0), Vector3(ab.logic.w, 0, 0), Vector3(0, 0, ab.logic.h), Vector3(ab.logic.w, 0, ab.logic.h)]:
			var s: Vector2 = ab.project(corner)
			kit.ok(s.x >= 0.0 and s.x <= float(ab.art.x) and s.y >= 8.0 and s.y <= float(ab.art.y) - 4.0, "map %d: corner %s is inside the glass (%s)" % [i + 1, corner, s])
		var far: Vector2 = ab.project(ab.cell_pos(Vector2i(0, 0), 0.0))
		var near: Vector2 = ab.project(ab.cell_pos(Vector2i(0, ab.logic.h - 1), 0.0))
		var far_r: Vector2 = ab.project(ab.cell_pos(Vector2i(ab.logic.w - 1, 0), 0.0))
		var near_r: Vector2 = ab.project(ab.cell_pos(Vector2i(ab.logic.w - 1, ab.logic.h - 1), 0.0))
		kit.ok(far.y < near.y and (near_r.x - near.x) > (far_r.x - far.x) + 8.0, "map %d: perspective — north is up and smaller" % (i + 1))
		kit.ok((ab._dyn as ImmediateMesh).get_surface_count() == 1, "map %d: posts, beams and figure are drawn" % (i + 1))
	ab._load_map(2)
	kit.ok(ab.cell_pos(Vector2i(10, 3), 0.0).y > ab.cell_pos(Vector2i(9, 7), 0.0).y + 1.5, "map 3: the attic lies above the hall")
	return true


# ================================================================ accessibility
func _access(settings: Node) -> bool:
	settings.values["text_scale"] = 1.5
	settings.values["high_contrast"] = true
	settings.values["reduced_motion"] = true
	var tg := _mg(TERM_SCENE)
	tg.open({"explore_id": STEPS[2], "auto": false})
	_steps(tg, 0.4)
	kit.ok(tg.compact and tg.S == 4 and tg.art == TermGame.ART_COMPACT, "larger text: a smaller raster at x4 — the letters grow")
	kit.ok(Crt.housing_size(tg.art, tg.S).x <= 1700.0 and Crt.housing_size(tg.art, tg.S).y <= 520.0, "the tube still fits the panel")
	kit.ok(not tg._subtitle.visible, "the flavour line gives way")
	for ch in TermLogic.OPERATOR:
		tg.modal_input(_key(KEY_0 + int(ch)))
	tg.modal_input(_key(KEY_ENTER))
	kit.eq(tg.logic.phase, "menu", "high contrast and large text play the same")
	var ab := _mg(AB_SCENE)
	ab.open({"explore_id": STEPS[3], "auto": false})
	_steps(ab, 0.3)
	kit.ok(ab.logic.tick > 0, "reduced motion: no fly-in before the beat")
	kit.ok(ab.compact and not ab._subtitle.visible and not ab._instr.visible, "larger text: the picture keeps its size, the flavour gives way")
	kit.ok(ab.art == AbGame.ART_COMPACT and Crt.housing_size(ab.art, 3).y <= 480.0, "the picture leaves room for the larger status, hint and buttons")
	var a: Transform3D = ab._camera_now()
	_steps(ab, 1.0)
	kit.eq(ab._camera_now(), a, "reduced motion: the camera stands still")
	ab.modal_input(_key(KEY_RIGHT, true))
	_steps(ab, 0.2)
	kit.eq(ab.figure_pos(), ab.cell_pos(ab.logic.cell), "reduced motion: the figure jumps from cell to cell")
	ab.modal_input(_key(KEY_RIGHT, false))
	kit.ok(Crt.palette(true)["bg"] == Color("000000") and Crt.palette(true)["g3"] != Crt.palette(false)["g3"], "high contrast: black glass, brighter steps")
	settings.values["text_scale"] = 1.0
	settings.values["high_contrast"] = false
	settings.values["reduced_motion"] = false
	var mv := _mg(AB_SCENE)
	mv.open({"explore_id": STEPS[3], "auto": false})
	_steps(mv, 1.0)
	var c0: Transform3D = mv._camera_now()
	_steps(mv, 1.5)
	kit.ok(mv._camera_now() != c0, "default: the camera drifts a little (the wire is 3D)")
	# hint modes
	settings.values["puzzle_hints"] = 0
	var n := _mg(TERM_SCENE)
	n.open({"explore_id": STEPS[2], "auto": false})
	_steps(n, 0.4)
	for i in 3:
		n.modal_input(_key(KEY_ENTER))
	kit.ok(n.fails == 3 and not n._hint_box.visible, "puzzle_hints 0: no hint even after three refusals")
	settings.values["puzzle_hints"] = 2
	var h := _mg(TERM_SCENE)
	h.open({"explore_id": STEPS[2], "auto": false})
	kit.ok(h._hint_box.visible, "puzzle_hints 2: the terminal's first hint at once")
	var h2 := _mg(AB_SCENE)
	h2.open({"explore_id": STEPS[3], "auto": false})
	kit.ok(h2._hint_box.visible and not h2.trace_on, "puzzle_hints 2: the map's tip at once")
	settings.values["puzzle_hints"] = 1
	return true


# ================================================================ assets
func _assets() -> bool:
	var srcs := FileAccess.get_file_as_string("res://scripts/ui/minigames/terminal_game.gd") \
		+ FileAccess.get_file_as_string("res://scripts/ui/minigames/abgang_game.gd")
	for s in SFX:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % s), "sound %s imported" % s)
		kit.ok(srcs.contains("\"%s\"" % s) or srcs.contains("\"%s.wav\"" % s), "a game plays %s" % s)
	var hum = load("res://assets/audio/sfx/mg_term_hum.wav")
	kit.ok(hum is AudioStreamWAV and (hum as AudioStreamWAV).loop_mode != AudioStreamWAV.LOOP_DISABLED, "the hum loops")
	kit.ok(hum is AudioStreamWAV and (hum as AudioStreamWAV).mix_rate == 44100, "44.1 kHz")
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/explore/c4/planspiel_strip.png"))
	kit.ok(img != null and img.get_width() <= 320 and img.get_height() <= 200, "the close-up fits the discovery page")
	kit.ok(img != null and img.detect_alpha() != Image.ALPHA_BLEND, "hard pixels")
	# every string the tube letters can be lettered, in both languages
	for lang in [de, en]:
		for k in lang.keys():
			var ks := str(k)
			if ks.begins_with("mg.term.") and not (ks.contains(".status.") or ks.contains(".hint.") or ks.contains(".ctrl.") or ks.contains(".btn.")
					or ks in ["mg.term.kicker", "mg.term.title", "mg.term.subtitle", "mg.term.instruction", "mg.term.solved"]):
				kit.ok(Crt.supports(str(lang.t(ks)).replace("{nr}", "1").replace("{id}", "1").replace("{kw}", "1").replace("{n}", "1")
					.replace("{a}", "1").replace("{b}", "1").replace("
", " ")), "%s can be lettered (%s)" % [ks, lang.language])
			if ks.begins_with("mg.abgang.hud.") or ks.begins_with("mg.abgang.map."):
				kit.ok(Crt.supports(str(lang.t(ks)).replace("{n}", "1").replace("{name}", "A")), "%s can be lettered (%s)" % [ks, lang.language])
		var ml := str(lang.t("mg.abgang.hud.map", {"n": 3, "name": lang.t("mg.abgang.map.attic")}))
		kit.ok(Crt.text_width(ml) + Crt.text_width(str(lang.t("mg.abgang.hud.title"))) + 16 <= AbGame.ART.x, "the head-up line fits the glass (%s)" % lang.language)
	kit.ok(Crt.supports("ÄÖÜß 0123456789 (>) = * # % _"), "umlauts and the desk's signs")
	kit.ok(not Crt.supports("→"), "an unknown sign is reported")
	var im := Crt.raster([{"t": "AB", "c": 0, "r": 0, "lv": 3}, {"box": [20, 2, 3, 2], "lv": 1}], Vector2i(40, 16))
	kit.eq(im.get_size(), Vector2i(40, 16), "the raster has the picture's size")
	kit.ok(im.get_pixel(3, 5).g > 0.9 and im.get_pixel(3, 5).r == 0.0 and im.get_pixel(21, 3).g > 0.2 and im.get_pixel(21, 3).g < 0.4,
		"beam strength in the green channel, in steps")
	return true
