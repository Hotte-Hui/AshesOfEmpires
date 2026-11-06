extends RefCounted
## Chapter-3 mini-game „Das Relaispult" (owner: minigames_r7_relay, TECHNICAL_ARCHITECTURE §12.8): the booth/relay
## tables are right for every floor language, a careful player and a slower one both get through the three rounds,
## wrong play is refused gently (a channel left wrong fails the passage, ignoring the lamps loses threads, lamps
## nobody needs are ignored), the backlog behaves (relay booths fall behind sooner, yellow slows, red pauses, a lost
## thread silences the booth and the booths relaying from it), auto mode and the keyboard work, demo_solve uses
## synthetic keys only, and the data (find, strings, hotspot, level nodes, art, audio) is complete and calm.

const Kit := preload("res://tests/support/test_kit.gd")
const Logic := preload("res://scripts/ui/minigames/relay_logic.gd")
const LOGIC := "res://scripts/ui/minigames/relay_logic.gd"
const SCENE := "res://scenes/ui/minigames/RelayDesk.tscn"
const GAME := "res://scripts/ui/minigames/relay_game.gd"
const SPOT := "res://scripts/ui/minigames/relay_spot.gd"
const PROP := "res://scripts/ui/minigames/relay_world_desk.gd"
const DATA := "res://data/explore/minigames_r7_relay.json"
const STRINGS := "res://data/locale/de_minigames_r7_relay.json"
const HISTORY := "res://data/explore/c3_history_reich.json"
const LEVEL := "res://scenes/levels/L_C3_Hall.tscn"
const ENV := "res://assets/environments/veltrava_hall/"
const ART := "res://assets/ui/minigames/relay/"
const SFX := "res://assets/audio/sfx/"
const ID := "veltrava.hall.relay"
const HOTSPOT := "exp_relay_desk"
const DT := 1.0 / 60.0

var kit: Kit
var strings: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var sj = _json(STRINGS)
	strings = sj.get("strings", {}) if sj is Dictionary else {}
	kit.run_case("booth_and_relay_tables", _tables)
	kit.run_case("careful_and_slower_players_get_through", _players)
	kit.run_case("wrong_play_refused_gently", _refused)
	kit.run_case("backlog_lamps_and_lost_threads", _backlog)
	kit.run_case("auto_mode", _auto)
	kit.run_case("keys_hint_and_give_up", _ui)
	kit.run_case("demo_solve_synthetic_keys_only", _demo_source)
	kit.run_case("find_and_strings", _data)
	kit.run_case("level_hotspot_and_nodes", _level)
	kit.run_case("art_layout_and_audio", _assets)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


# ================================================================ logic
func _tables() -> bool:
	var lg = load(LOGIC).new()
	# floor -> [k1 out, k2 out, k3 out], [pivots], [correct column per row DE RU FR EN]
	var want := {
		"de": [["fr", "ru", "en"], [-1, -1, -1], [0, 2, 1, 3]],
		"ru": [["fr", "de", "en"], [1, -1, 1], [2, 0, 1, 3]],
		"fr": [["de", "ru", "en"], [-1, 0, -1], [1, 2, 0, 3]],
	}
	for fl in want:
		var outs: Array = []
		var pv: Array = []
		var cols: Array = []
		for k in 3:
			outs.append(lg.booth_out(k, fl))
			pv.append(lg.pivot(k, fl))
		for r in 4:
			cols.append(lg.correct_col(r, fl))
		kit.eq(outs, want[fl][0], "floor %s: booth outputs" % fl)
		kit.eq(pv, want[fl][1], "floor %s: relay pivots (Kabine 1 and 3 relay Kabine 2 on Russian, Kabine 2 relays the retour of Kabine 1 on French)" % fl)
		kit.eq(cols, want[fl][2], "floor %s: the one right socket per channel" % fl)
		for k in 3:
			kit.eq(lg.is_relay(k, fl), int(want[fl][1][k]) >= 0, "floor %s: booth %d relay flag" % [fl, k + 1])
	kit.eq(lg.correct_col(0, ""), -1, "no floor language, no right socket")
	# the scripted rounds rise in tempo and shorten the warnings; every speaker has a floor language
	var max_t: Array = []
	var ann: Array = []
	for rd in Logic.ROUNDS:
		var m := 0.0
		var a := 0.0
		var n := 0
		kit.ok((rd["turns"] as Array).size() >= 4, "round %s has at least four turns" % rd["key"])
		for t in rd["turns"]:
			kit.ok(Logic.SPEAKER_LANG.has(str(t["who"])), "speaker %s has a floor language" % t["who"])
			for seg in t["tempo"]:
				m = maxf(m, float(seg[1]))
			if float(t["announce"]) > 0.0:
				a += float(t["announce"])
				n += 1
		max_t.append(m)
		ann.append(a / maxf(1, n))
	kit.ok(max_t[0] < max_t[1] and max_t[1] < max_t[2], "the tempo rises from round to round %s" % [max_t])
	kit.ok(ann[0] > ann[1] and ann[1] > ann[2], "the chair's warnings get shorter %s" % [ann])
	# every language change of the script is a real change of the desk (two speakers in a row never share a language)
	for rd in Logic.ROUNDS:
		var prev := ""
		for t in rd["turns"]:
			var l: String = Logic.SPEAKER_LANG[str(t["who"])]
			kit.ne(l, prev, "round %s: consecutive speakers change the floor language" % rd["key"])
			prev = l
	return true


## A scripted player: re-plugs `react` s after the target language changes (one socket every `per_plug` s), gives
## yellow / red when the worst needle reaches `yel` / `red` (-1 = never), confirms intros and summaries.
func _play(lg, react: float, per_plug: float, yel: float, red: float, max_attempts := 8) -> Dictionary:
	var t := 0.0
	var since := 0.0
	var cd := 0.0
	var last := "?"
	var rounds: Array = []
	var events: Array = []
	while not lg.done and t < 900.0 and lg.attempts <= max_attempts:
		var fl: String = lg.target_lang()
		if fl != last:
			last = fl
			since = 0.0
		since += DT
		cd -= DT
		if fl != "" and since >= react and cd <= 0.0:
			for r in 4:
				var c: int = lg.correct_col(r, fl)
				if c >= 0 and int(lg.plugs[r]) != c:
					lg.plug(r, c)
					cd = per_plug
					break
		var m: float = lg.max_backlog()
		if yel > 0.0 and m >= yel and lg.yellow_left <= 0.0:
			lg.yellow()
		if red > 0.0 and m >= red and lg.pause_left <= 0.0:
			lg.red()
		for e in lg.step(DT):
			events.append(str(e))
			if str(e) == "round_passed" or str(e) == "round_failed":
				rounds.append([lg.round_i, str(e), lg.last_ratio, lg.round_lost])
		if lg.phase in ["intro", "summary", "beat"] and lg.phase_t > 0.8:
			lg.advance()
		t += DT
	for e in lg.step(DT):          # the events of the last action arrive with the next step (like the UI's next frame)
		events.append(str(e))
	return {"t": t, "rounds": rounds, "events": events}


func _players() -> bool:
	var lg = load(LOGIC).new()
	var res := _play(lg, 0.5, 0.25, Logic.ZONE_YELLOW, 0.8)
	kit.ok(lg.done, "a careful player finishes the session (%.1f s)" % res["t"])
	kit.eq(lg.rounds_passed, 3, "three rounds passed")
	kit.eq(lg.attempts, 3, "no round repeated")
	kit.eq(lg.lost_count, 0, "no thread lost")
	kit.eq(lg.unnecessary, 0, "no lamp pressed for nothing")
	for rr in res["rounds"]:
		kit.ok(float(rr[2]) >= 0.9, "round %d understood %.0f %%" % [int(rr[0]) + 1, float(rr[2]) * 100.0])
	kit.ok(float(res["t"]) > 90.0 and float(res["t"]) < 200.0, "about two to three minutes of play (%.1f s)" % res["t"])
	var ev: Array = res["events"]
	kit.ok(ev.has("adjourned") and ev.find("adjourned") < ev.find("solved"), "the chair adjourns before the end")
	kit.eq(ev.count("solved"), 1, "solved exactly once")
	kit.ok(lg.step(DT).is_empty(), "nothing happens after the end")
	kit.ok(not lg.plug(0, 2), "the desk is done")
	# a slower player (late reactions, late lamps) still gets through -- forgiving
	var lg2 = load(LOGIC).new()
	var res2 := _play(lg2, 1.5, 0.6, 0.6, 0.9)
	kit.ok(lg2.done, "a slower player finishes too (%d attempts, %.1f s)" % [lg2.attempts, res2["t"]])
	kit.ok(lg2.attempts <= 4, "with at most one repeat (%d attempts)" % lg2.attempts)
	return true


func _refused() -> bool:
	# never re-plugging: the first passage is not understood and repeated -- nothing else is lost
	var lg = load(LOGIC).new()
	var res := _play(lg, 999.0, 1.0, -1.0, -1.0, 2)
	kit.ok(not lg.done, "the session is not over")
	kit.ok(res["rounds"].size() >= 1 and str(res["rounds"][0][1]) == "round_failed", "round 1 failed")
	kit.eq(lg.round_i, 0, "still round 1")
	kit.ok(lg.attempts >= 2, "the passage is repeated (%d attempts)" % lg.attempts)
	# ignoring the lamps: round 1 forgives it, round 2 repeats because interpreters lose the thread
	var lg2 = load(LOGIC).new()
	var res2 := _play(lg2, 0.5, 0.25, -1.0, -1.0, 2)
	var rs: Array = res2["rounds"]
	kit.ok(rs.size() >= 2, "two rounds played (%d)" % rs.size())
	if rs.size() >= 2:
		kit.eq(str(rs[0][1]), "round_passed", "round 1 forgives missing lamps")
		kit.eq(str(rs[1][1]), "round_failed", "round 2 does not")
		kit.ok(int(rs[1][3]) >= Logic.MAX_LOST, "because threads were lost (%d)" % int(rs[1][3]))
		kit.eq(lg2.last_fail, "lost", "reason: lost threads")
	kit.ok(lg2.lost_count > 0, "lost threads were counted")
	# lamps nobody needs, lamps outside a speech
	var lg3 = load(LOGIC).new()
	kit.eq(lg3.yellow(), "", "no lamp before anyone speaks")
	kit.eq(lg3.red(), "", "no red before anyone speaks")
	lg3.advance()
	lg3.step(DT)
	kit.eq(lg3.phase, "speech", "the chair opens round 1 at once")
	kit.eq(lg3.yellow(), "yellow_ignored", "yellow is ignored while every booth keeps up")
	kit.eq(lg3.red(), "red_ignored", "red is ignored while nobody is far behind")
	kit.eq(lg3.unnecessary, 2, "both counted as unnecessary")
	kit.eq(lg3.yellow_left, 0.0, "the speaker did not slow down")
	# restart of the current round keeps the passed ones
	var lg4 = load(LOGIC).new()
	_play(lg4, 0.5, 0.25, Logic.ZONE_YELLOW, 0.8, 1)
	kit.eq(lg4.round_i, 1, "careful play reached round 2")
	var att: int = lg4.attempts
	lg4.restart_round()
	kit.eq([lg4.round_i, lg4.phase, lg4.attempts], [1, "intro", att + 1], "restart repeats round 2 from its intro")
	return true


func _speech(lg, ri: int, ti: int, t: float) -> void:
	lg.round_i = ri
	lg.turn_i = ti
	lg.phase = "speech"
	lg.phase_t = 0.0
	lg.speech_t = t
	lg.backlog = [0.0, 0.0, 0.0]
	lg.lost = [0.0, 0.0, 0.0]


func _backlog() -> bool:
	# round 1, the Soviet delegate's numbers (Russian, tempo 1.32): Kabine 1 and 3 work on relay
	var lg = load(LOGIC).new()
	_speech(lg, 0, 1, 3.3)
	for i in int(2.0 / DT):
		lg.step(DT)
	kit.ok(float(lg.backlog[0]) > float(lg.backlog[1]) and float(lg.backlog[2]) > float(lg.backlog[1]),
		"relay booths fall behind sooner %s" % [lg.backlog])
	kit.ok(float(lg.backlog[1]) > 0.0, "the direct booth falls behind a little too")
	var lg_y = load(LOGIC).new()
	_speech(lg_y, 0, 1, 3.3)
	lg_y.backlog = [0.3, 0.3, 0.3]
	kit.eq(lg_y.yellow(), "yellow", "yellow is taken when a booth is behind")
	for i in int(2.0 / DT):
		lg_y.step(DT)
	var lg_n = load(LOGIC).new()
	_speech(lg_n, 0, 1, 3.3)
	lg_n.backlog = [0.3, 0.3, 0.3]
	for i in int(2.0 / DT):
		lg_n.step(DT)
	kit.ok(float(lg_y.backlog[0]) < float(lg_n.backlog[0]), "yellow slows the growth (%.2f < %.2f)" % [lg_y.backlog[0], lg_n.backlog[0]])
	kit.ok(lg_y.speech_t < lg_n.speech_t, "and the speech takes longer")
	# red: the speaker stops, nobody is scored, the booths catch up
	var lg_r = load(LOGIC).new()
	_speech(lg_r, 0, 1, 4.0)
	lg_r.backlog = [0.7, 0.2, 0.7]
	kit.eq(lg_r.red(), "red", "red is taken when a booth is far behind")
	kit.eq(lg_r.floor_lang(), "", "the floor is silent")
	var tot: float = lg_r.total
	var st: float = lg_r.speech_t
	for i in int(1.0 / DT):
		lg_r.step(DT)
	kit.eq(lg_r.total, tot, "no scoring during the pause")
	kit.eq(lg_r.speech_t, st, "the speech waits")
	kit.ok(float(lg_r.backlog[0]) < 0.7, "the booths catch up (%.2f)" % lg_r.backlog[0])
	var ev: Array = []
	for i in int(2.0 / DT):
		ev += lg_r.step(DT)
	kit.ok(ev.has("red_end") and lg_r.floor_lang() == "ru", "after the pause the delegate speaks on")
	# a lost thread: Kabine 2 on Russian -> Kabine 1 and 3 (relaying from it) fall silent too
	var lg_l = load(LOGIC).new()
	_speech(lg_l, 0, 1, 4.0)
	lg_l.plugs = [2, 0, 1, 3]
	lg_l.backlog = [0.1, 0.999, 0.1]
	var ev2: Array = lg_l.step(DT)
	kit.ok(ev2.has("lost:1"), "Kabine 2 loses the thread")
	kit.eq(float(lg_l.lost[1]), Logic.LOST_TIME, "for LOST_TIME seconds")
	kit.ok(lg_l.booth_silent(0) and lg_l.booth_silent(2), "the booths relaying from it are silent as well")
	kit.eq([lg_l.heard(0), lg_l.heard(1), lg_l.heard(2), lg_l.heard(3)], ["", "ru", "", ""], "only the floor channel still hears something")
	kit.eq(lg_l.row_quality(0), 0.0, "a silent channel understands nothing")
	var ev3: Array = []
	for i in int((Logic.LOST_TIME + 0.2) / DT):
		ev3 += lg_l.step(DT)
	kit.ok(ev3.has("lost_end:1"), "the interpreter picks the thread up again")
	kit.ok(not lg_l.booth_silent(1), "Kabine 2 speaks again")
	# quality: a booth deep in the red zone drops words
	var lg_q = load(LOGIC).new()
	_speech(lg_q, 0, 2, 2.0)                 # Reichsdelegation, German: Kabine 1 -> FR
	lg_q.plugs = [0, 2, 1, 3]
	lg_q.backlog = [0.8, 0.5, 0.1]
	kit.eq([lg_q.row_quality(0), lg_q.row_quality(2), lg_q.row_quality(1), lg_q.row_quality(3)],
		[1.0, Logic.Q_RED, Logic.Q_YELLOW, 1.0], "row quality follows the zone of its booth")
	return true


# ================================================================ UI
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
	mg.open({"explore_id": ID, "auto": true})
	kit.ok(mg.is_open, "opens")
	mg._process(0.1)
	kit.eq(got, [], "not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	mg._process(0.1)
	kit.eq(got, [true], "finished exactly once")
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
	mg.open({"explore_id": ID, "auto": false})
	kit.eq(mg.logic.phase, "intro", "opens on the round card")
	kit.eq(mg.logic.sel, 3, "the cursor starts on the channel that is still wrong (EN)")
	kit.ok(mg.modal_input(_key(KEY_4)), "a digit is consumed")
	kit.eq(int(mg.logic.plugs[3]), 3, "4 plugs the selected channel into Kabine 3")
	kit.ok(mg.modal_input(_key(KEY_UP)), "Up is consumed")
	kit.eq(mg.logic.sel, 2, "Up selects the channel above")
	kit.ok(mg.modal_input(_key(KEY_RIGHT)), "Right is consumed")
	kit.eq(int(mg.logic.plugs[2]), 1, "Right moves the FR plug from Saal to Kabine 1")
	kit.ok(mg.modal_input(_key(KEY_LEFT)), "Left is consumed")
	kit.eq(int(mg.logic.plugs[2]), 0, "Left moves it back")
	kit.ok(mg.modal_input(_key(KEY_SPACE)), "Space is consumed")
	kit.ok(mg.logic.phase != "intro", "Space starts the round")
	for i in 30:
		mg._process(DT)
	kit.ok(not mg.solved and mg.fails == 0, "a few frames of the chair neither solve nor fail")
	kit.ok(mg.modal_input(_key(KEY_G)), "G is consumed")
	kit.ok(mg._status.text == str(strings.get("mg.relay.status.yellow_ignored", "?")), "an unneeded yellow lamp is explained")
	kit.eq(mg.logic.yellow_left, 0.0, "and changes nothing")
	kit.ok(mg.modal_input(_key(KEY_R)), "R is consumed")
	# two refusals show the hint; the plug hint switches the guide lights on (hints at their default setting, in
	# memory only -- the player's settings file is never written)
	var st: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Settings")
	var had = st.values.get("puzzle_hints", 1) if st != null else null
	if st != null:
		st.values["puzzle_hints"] = 1
	mg._hint_kind = "plug"
	for n in 2:
		mg.register_fail("x")
	kit.ok(mg._hint_box.visible and str(mg._hint_label.text).begins_with("Tipp"), "hint after two refusals")
	kit.ok(mg._guides, "the guide lights are on")
	kit.ok(not mg._instr.visible, "the hint takes the instruction's place")
	kit.eq(str(mg._hint_text(3)), str(strings.get("mg.relay.hint.announce", "?")), "the third hint explains the announcements")
	mg._hint_kind = "lamp"
	kit.eq(str(mg._hint_text(1)), str(strings.get("mg.relay.hint.lamp", "?")), "lost threads lead to the lamp hint")
	if st != null:
		st.values["puzzle_hints"] = had
	kit.ok(mg._controls().size() >= 5, "the key hints list channel, plug, sockets, yellow, red")
	# mouse: a click on a socket plugs that channel there, a click on a lamp presses it
	var lay: Dictionary = mg.layout
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(float(lay["cols"][2]["socket_x"]), float(lay["rows"][0]["socket_y"])) * 3.0
	mg.desk_input(click)
	kit.eq([mg.logic.sel, int(mg.logic.plugs[0])], [0, 2], "clicking socket DE/Kabine 2 plugs it there")
	var unneeded: int = mg.logic.unnecessary
	click.position = Vector2(float(lay["lamps"][0]["centre"][0]), float(lay["lamps"][0]["centre"][1])) * 3.0
	mg.desk_input(click)
	kit.eq(mg.logic.unnecessary, unneeded + 1, "clicking the yellow lamp presses it")
	# give up: no find, finished(false) once
	var res: Array = []
	mg.finished.connect(func(ok: bool): res.append(ok))
	mg.handle_cancel()
	kit.eq(res, [false], "Esc gives up without a find")
	mg.handle_cancel()
	kit.eq(res, [false], "and only once")
	kit.ok(FileAccess.get_file_as_string(GAME).begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""),
		"extends minigame_base.gd")
	return true


func _demo_source() -> bool:
	var src := FileAccess.get_file_as_string(GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.step(") and not body.contains("logic.plug(")
		and not body.contains("logic.yellow(") and not body.contains("logic.red(") and not body.contains("logic.advance(")
		and not body.contains("mark_solved("), "demo_solve drives the game through synthetic key events only")
	return true


# ================================================================ data
func _all_used_keys() -> Array:
	var keys := {}
	var rx := RegEx.new()
	rx.compile("\"(mg\\.relay\\.[a-z0-9_.]+)\"")
	for m in rx.search_all(FileAccess.get_file_as_string(GAME)):
		var k := m.get_string(1)
		if not k.ends_with("."):
			keys[k] = true
	for rd in Logic.ROUNDS:
		for suffix in ["title", "note", "done"]:
			keys["mg.relay.%s.%s" % [rd["key"], suffix]] = true
		for i in (rd["turns"] as Array).size():
			keys["mg.relay.%s.t%d" % [rd["key"], i + 1]] = true
	for i in Logic.BEAT_LINES:
		keys["mg.relay.beat.%d" % (i + 1)] = true
	for l in ["de", "ru", "fr", "en"]:
		for p in ["lang", "code", "row"]:
			keys["mg.relay.%s.%s" % [p, l]] = true
	for w in Logic.SPEAKER_LANG:
		keys["mg.relay.who." + str(w)] = true
	for b in ["k1", "k2", "k3"]:
		keys["mg.relay.booth." + b] = true
	for t in ["calm", "normal", "brisk", "fast", "slowed", "stopped"]:
		keys["mg.relay.tempo." + t] = true
	for s in ["yellow", "yellow_ignored", "red", "red_ignored"]:
		keys["mg.relay.status." + s] = true
	return keys.keys()


func _data() -> bool:
	var d = _json(DATA)
	if not kit.ok(d is Dictionary, "minigames_r7_relay.json parses"):
		return true
	kit.eq(str(d.get("area", "")), "veltrava", "area veltrava (journal groups it with the palais)")
	var es: Array = d.get("entries", [])
	kit.eq(es.size(), 1, "one find")
	var e: Dictionary = es[0] if not es.is_empty() else {}
	kit.eq([str(e.get("id", "")), str(e.get("kind", "")), str(e.get("level", ""))], [ID, "detail", "L_C3_Hall"], "id, kind, level")
	kit.eq(str(e.get("minigame", "")), SCENE, "the find opens the mini-game")
	kit.ok(ResourceLoader.exists(SCENE), "mini-game scene exists")
	var img := str(e.get("image", ""))
	var im := Image.load_from_file(ProjectSettings.globalize_path(img)) if FileAccess.file_exists(img) else null
	kit.ok(im != null and im.get_width() <= 320 and im.get_height() <= 200, "close-up %s exists and fits 320x200" % img)
	kit.ok(not FileAccess.file_exists(img.get_basename() + "_hist.png"), "no insignia variant")
	var hist: Array = e.get("history", [])
	var cards := {}
	var hd = _json(HISTORY)
	for c in (hd.get("cards", []) if hd is Dictionary else []):
		cards[str(c.get("id", ""))] = true
	kit.eq(hist, ["hist.reich.nuremberg_interpreters"], "links the real-history card on simultaneous interpreting")
	for h in hist:
		kit.ok(cards.has(str(h)), "history card %s exists" % h)
	# strings
	var ss: Dictionary = strings
	kit.ok(ss.size() > 80, "string table loaded (%d)" % ss.size())
	for k in _all_used_keys():
		kit.ok(ss.has(k), "string %s exists" % k)
	for k in ["title_key", "text_key", "prompt_key"]:
		kit.ok(ss.has(str(e.get(k, ""))), "find %s has text" % k)
	var txt := str(ss.get(str(e.get("text_key", "")), ""))
	kit.ok(txt.length() >= 250 and txt.length() <= 520, "find text in Konrad's voice (%d chars)" % txt.length())
	var forbidden := ["Anlage", "Elena", "C-17", "Begleit", "Sekretariat"]   # (the pre-rename name is guarded by test_rename_guard)
	var mic := RegEx.new()
	mic.compile("Mikrofon\\s*\\d")
	for key in ss:
		var v := str(ss[key])
		kit.ok(str(key).begins_with("mg.relay.") or str(key).begins_with("explore.veltrava.hall.relay."), "%s is namespaced" % key)
		kit.ok(not v.contains("!"), "%s stays calm (no exclamation mark)" % key)
		kit.ok(not v.contains("\""), "%s uses typographic quotes" % key)
		kit.eq(v.count("„"), v.count("“"), "%s: German quotes are balanced" % key)
		kit.ok(mic.search(v) == null, "%s names no microphone number (the protocol puzzle stays intact)" % key)
		for f in forbidden:
			kit.ok(not v.contains(f), "%s does not mention '%s'" % [key, f])
	return true


func _level() -> bool:
	var x = _json(ENV + "explore_hotspots.json")
	var m = _json(ENV + "scene.json")
	var extra: Dictionary = x.get("hotspots", {}) if x is Dictionary else {}
	var main: Dictionary = m.get("hotspots", {}) if m is Dictionary else {}
	if not kit.ok(extra.has(HOTSPOT), "%s declared in explore_hotspots.json" % HOTSPOT):
		return true
	kit.ok(not main.has(HOTSPOT), "no name clash with scene.json")
	var p := Vector2(float(extra[HOTSPOT][0]), float(extra[HOTSPOT][1]))
	var poly := PackedVector2Array()
	for q in (m.get("walkable", []) if m is Dictionary else []):
		poly.append(Vector2(float(q[0]), float(q[1])))
	kit.ok(poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, poly), "the hotspot lies on the walkable floor")
	var all := main.duplicate()
	all.merge(extra, false)
	for k in all:
		if str(k) == HOTSPOT:
			continue
		var o := Vector2(float(all[k][0]), float(all[k][1]))
		kit.ok(p.distance_to(o) >= 26.0, "%s keeps 26 px from %s (%.0f)" % [HOTSPOT, k, p.distance_to(o)])
	var lvl := FileAccess.get_file_as_string(LEVEL)
	var a := lvl.find("[node name=\"Find_RelayDesk\"")
	kit.ok(a >= 0, "L_C3_Hall places the relay desk interactable")
	if a >= 0:
		var block := lvl.substr(a, lvl.find("\n\n", a) - a)
		for want in ["hotspot_id = \"%s\"" % HOTSPOT, "explore_id = \"%s\"" % ID, "kind = \"discover\"",
				"after_objective = \"c3b_arrival\"", "until_objective = \"c3b_inspect_booth\"", "once = true"]:
			kit.ok(block.contains(want), "Find_RelayDesk: %s" % want)
	kit.ok(lvl.contains("path=\"%s\"" % SPOT) and lvl.contains("path=\"%s\"" % PROP), "spot and prop scripts referenced")
	kit.ok(lvl.contains("[node name=\"RelayDeskProp\" type=\"Sprite2D\""), "the desk prop stands in the corridor")
	var spot_src := FileAccess.get_file_as_string(SPOT)
	kit.ok(spot_src.contains("memory_mode") and spot_src.contains("super.is_active()"), "the spot opens in a memory and otherwise follows its gates")
	var sp: Node = load(SPOT).new()
	kit.ok(sp.has_method("is_active") and "after_objective" in sp and "until_objective" in sp, "the spot is a gated interactable")
	sp.free()
	return true


func _wav(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var b := f.get_buffer(f.get_length())
	var out := {"riff": b.slice(0, 4).get_string_from_ascii(), "wave": b.slice(8, 12).get_string_from_ascii()}
	var i := 12
	while i + 8 <= b.size():
		var id := b.slice(i, i + 4).get_string_from_ascii()
		var sz := b.decode_u32(i + 4)
		if id == "fmt ":
			out["channels"] = b.decode_u16(i + 10)
			out["rate"] = b.decode_u32(i + 12)
			out["bits"] = b.decode_u16(i + 22)
		elif id == "data":
			out["frames"] = sz / 2
		out[id] = true
		i += 8 + sz + (sz % 2)
	return out


func _assets() -> bool:
	var lay = _json(ART + "relay_layout.json")
	if not kit.ok(lay is Dictionary, "relay_layout.json parses"):
		return true
	var size := Vector2(float(lay["size"][0]), float(lay["size"][1]))
	var cells: Dictionary = lay.get("cells", {})
	var expect := {"relay_desk.png": size,
		"relay_pins.png": Vector2(float(cells["pin"][0]) * 3, float(cells["pin"][1])),
		"relay_lamps.png": Vector2(float(cells["lamp"][0]) * 6, float(cells["lamp"][1])),
		"relay_icons.png": Vector2(float(cells["icon"][0]) * 6, float(cells["icon"][1])),
		"relay_booths.png": Vector2(float(cells["booth"][0]) * 5, float(cells["booth"][1]) * 4),
		"relay_interpreter.png": Vector2(float(cells["interpreter"][0]) * 2, float(cells["interpreter"][1])),
		"world_desk.png": Vector2(176, 38), "world_desk_n.png": Vector2(176, 38), "world_desk_e.png": Vector2(176, 38)}
	for f in expect:
		var im := Image.load_from_file(ProjectSettings.globalize_path(ART + f)) if FileAccess.file_exists(ART + f) else null
		if kit.ok(im != null, "art %s exists" % f):
			kit.eq(Vector2(im.get_size()), expect[f], "%s size" % f)
	kit.eq([(lay["cols"] as Array).size(), (lay["rows"] as Array).size(), (lay["lamps"] as Array).size()], [4, 4, 2],
		"four sources, four channels, two lamps")
	kit.eq(lay["zones"], [Logic.ZONE_YELLOW, Logic.ZONE_RED], "painted meter zones match the logic")
	var bounds := Rect2(Vector2.ZERO, size)
	var rects: Array = [lay["floor"]["rect"], lay["floor"]["kicker"], lay["floor"]["speech"], lay["floor"]["right"]]
	for c in lay["cols"]:
		rects += [c["plate"], c["window"], c["name"], c["out"], c["via"]]
		if c["meter"] is Array:
			rects.append(c["meter"])
	for r in lay["rows"]:
		rects += [r["tag"], r["code"], r["name"], r["state"]]
	for l in lay["lamps"]:
		rects.append(l["label"])
	var outside := 0
	for r in rects:
		if not bounds.encloses(Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))):
			outside += 1
	kit.eq(outside, 0, "every rect of the layout lies on the desk")
	kit.ok(lay["cols"][0]["meter"] == null and lay["cols"][1]["meter"] is Array, "the Saal has no backlog meter, the booths do")
	# audio
	for n in ["mg_relay_hall", "mg_relay_voice_fr", "mg_relay_voice_ru", "mg_relay_voice_de", "mg_relay_plug",
			"mg_relay_switch", "mg_relay_lamp_yellow", "mg_relay_lamp_red", "mg_relay_lost", "mg_relay_bell", "mg_relay_click"]:
		var w := _wav(SFX + n + ".wav")
		if not kit.ok(not w.is_empty(), "sound %s exists" % n):
			continue
		kit.eq([w.get("riff"), w.get("wave"), w.get("rate"), w.get("bits"), w.get("channels")], ["RIFF", "WAVE", 44100, 16, 1],
			"%s: 44.1 kHz / 16 bit / mono" % n)
		var loop: bool = str(n) == "mg_relay_hall" or str(n).begins_with("mg_relay_voice_")
		kit.eq(w.has("smpl"), loop, "%s: loop chunk only on the loops" % n)
		kit.ok(ResourceLoader.exists(SFX + n + ".wav"), "%s imported" % n)
	return true
