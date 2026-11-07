extends RefCounted
## Boot sequence + demo notice (TECHNICAL_ARCHITECTURE §12.13, round 11): the launch gate (only a real player's launch
## plays the splash / shows the notice; drivers, captures, harnesses, --script and headless never), the card order and
## timing, skipping (first press = next card, second press = the rest; only real presses count), the notice flag
## persisted through the Settings API in a TEMPORARY settings file (never the player's settings.cfg), the letter
## (texts, input guard, 100–150 % text fits the frame), the credits entry, the pixel lettering and the art / audio.

const TKit := preload("res://tests/support/test_kit.gd")
const UKit := preload("res://scripts/ui/ui_kit.gd")
const BootFlow := preload("res://scripts/ui/boot_flow.gd")
const PixelFont := preload("res://scripts/ui/pixel_font.gd")
const Splash := preload("res://scripts/ui/boot_splash.gd")
const SPLASH_SCENE := "res://scenes/ui/BootSplash.tscn"
const NOTICE_SCENE := "res://scenes/ui/DemoNotice.tscn"
const SettingsScript := preload("res://scripts/core/settings.gd")
const TMP_SETTINGS := "user://_test_splash/settings.cfg"
const DT := 0.05

var kit: TKit


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"text_scale": 1.0, "high_contrast": false, "reduced_motion": false, "demo_notice_seen": false}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


func run() -> Array:
	kit = TKit.new()
	var keep := [BootFlow.player_launch, BootFlow.notice_opened]
	kit.run_case("launch_gate", _gate)
	kit.run_case("card_order_and_timing", _order)
	kit.run_case("first_press_skips_the_card", _skip_one)
	kit.run_case("second_press_skips_the_rest", _skip_rest)
	kit.run_case("only_real_presses_count", _presses)
	kit.run_case("notice_flag_persists_in_settings_file", _flag)
	kit.run_case("notice_never_in_driver_mode", _driver_mode)
	kit.run_case("letter_texts_guard_and_close", _letter)
	kit.run_case("letter_fits_100_125_150", _letter_sizes)
	kit.run_case("credits_and_ui_root_entry", _entries)
	kit.run_case("pixel_lettering", _lettering)
	kit.run_case("art_and_audio", _assets)
	BootFlow.player_launch = keep[0]
	BootFlow.notice_opened = keep[1]
	UKit.overrides.erase("Settings")
	kit.cleanup()
	return kit.failures


func _gate() -> bool:
	var eng := PackedStringArray(["--path", "C:/Spiele/AshesOfEmpires"])
	kit.ok(BootFlow.is_player_launch(PackedStringArray(), eng, "Windows", true), "plain launch = player launch")
	kit.ok(BootFlow.is_player_launch(PackedStringArray(["--splash-shots=C:/tmp/s"]), eng, "Windows", true),
		"--splash-shots is the check run of the real boot")
	for a in ["--autoplay=share_with_irina,preserve_evidence", "--inputplay=a,b", "--capture=C:/tmp/x.png",
			"--capture-world=C:/tmp/w.png", "--cinematic=none", "--scene=L_A1_Railyard", "--memory-demo=x",
			"--switch-demo=1", "--autoplay-skip", "--profile=user://p.json", "--symbols=0"]:
		kit.ok(not BootFlow.is_player_launch(PackedStringArray([a]), eng, "Windows", true), "no splash with " + a)
	kit.ok(not BootFlow.is_player_launch(PackedStringArray(["--splash-shots=x", "--autoplay=a,b"]), eng, "Windows",
		true), "a driver argument wins over --splash-shots")
	kit.ok(not BootFlow.is_player_launch(PackedStringArray(), PackedStringArray(["--script", "res://t.gd"]), "Windows",
		true), "no splash for a --script main loop")
	kit.ok(not BootFlow.is_player_launch(PackedStringArray(), eng, "headless", true), "no splash headless")
	kit.ok(not BootFlow.is_player_launch(PackedStringArray(), eng, "Windows", false),
		"no splash when Main is instanced by a harness scene")
	# this very run (headless --script) is never a player launch
	var n := kit.mount(Node.new())
	kit.ok(not BootFlow.decide(n), "decide() in the test run = false")
	kit.ok(not BootFlow.player_launch, "player_launch stays false in tests")
	kit.ok(not BootFlow.notice_due(kit.track(MockSettings.new())), "no notice in tests")
	return true


func _splash() -> Node:
	var s: Node = (load(SPLASH_SCENE) as PackedScene).instantiate()
	s.set("quiet", true)
	s.set("auto_free", false)
	kit.mount(s)
	return s


## Runs the splash until it ends; presses = {card: seconds into that card}. Returns {cards, total, per_card, finished}.
func _drive(s: Node, presses := {}, limit := 30.0) -> Dictionary:
	var fin := [0]
	s.finished.connect(func(): fin[0] += 1)
	s.start()
	var t := 0.0
	var per := {}
	var pressed := {}
	while s.get("running") and t < limit:
		var c := str(s.get("card"))
		if presses.has(c) and not pressed.has(c) and float(s.get("card_time")) >= float(presses[c]):
			pressed[c] = true
			s.press()
		s.advance(DT)
		per[c] = float(per.get(c, 0.0)) + DT
		t += DT
	return {"cards": Array(s.get("cards")), "total": t, "per": per, "finished": fin[0], "done": s.get("done")}


func _order() -> bool:
	var s := _splash()
	kit.ok(bool(s.get("visible")), "splash layer visible before the run")
	var r := _drive(s)
	kit.eq(r["cards"], ["black", "studio", "engine", "title"], "card order: black, studio, engine, title")
	var expect := Splash.BLACK
	for c in [Splash.STUDIO, Splash.ENGINE, Splash.TITLE]:
		expect += float(c[0]) + float(c[1]) + float(c[2])
	kit.ok(absf(float(r["total"]) - expect) < 0.35, "natural run %.2f s ≈ %.2f s" % [r["total"], expect])
	kit.ok(expect >= 10.0 and expect <= 14.0, "the whole boot stays between 10 and 14 s (%.1f)" % expect)
	kit.ok(Splash.TITLE[0] + Splash.TITLE[1] + Splash.TITLE[2] >= 5.0, "title picture shows 5–7 s")
	kit.ok(float(r["per"].get("studio", 0.0)) >= 2.4, "studio card ~2.7 s")
	kit.eq(r["finished"], 1, "finished emitted once")
	kit.ok(bool(r["done"]), "done after the run")
	kit.eq(s.get("card"), "", "no card on screen at the end")
	kit.ok(not s.get("visible"), "the layer hides itself on black")
	kit.ok(Splash.LOGO_AT < Splash.TITLE[0] + Splash.TITLE[1] and Splash.GLINT_AT > Splash.LOGO_AT,
		"title, then glint, before the fade-out")
	return true


func _skip_one() -> bool:
	var s := _splash()
	var r := _drive(s, {"studio": 1.0})
	kit.eq(r["cards"], ["black", "studio", "engine", "title"], "one press skips only the studio card")
	kit.ok(float(r["per"]["studio"]) <= 1.0 + Splash.SKIP_FADE + 2 * DT + 0.01,
		"studio card ends right after the press (%.2f s)" % r["per"]["studio"])
	kit.ok(float(r["per"]["title"]) >= 6.0, "the title picture then plays in full")
	return true


func _skip_rest() -> bool:
	var s := _splash()
	var r := _drive(s, {"studio": 0.8, "engine": 0.3})
	kit.eq(r["cards"], ["black", "studio", "engine"], "second press skips the rest (no title)")
	kit.ok(float(r["per"]["engine"]) <= 0.3 + Splash.SKIP_FADE + 2 * DT + 0.01, "ends right after the second press")
	var s2 := _splash()
	s2.start()
	s2.press()
	s2.press()
	var t := 0.0
	while s2.get("running") and t < 5.0:
		s2.advance(DT)
		t += DT
	kit.eq(Array(s2.get("cards")), ["black"], "two quick presses on the black skip everything")
	kit.ok(t <= Splash.SKIP_FADE + 2 * DT + 0.01, "…within the skip fade (%.2f s)" % t)
	return true


func _presses() -> bool:
	var k := InputEventKey.new()
	k.pressed = true
	k.physical_keycode = KEY_SPACE
	kit.ok(Splash.is_press(k), "key down counts")
	var echo := k.duplicate() as InputEventKey
	echo.echo = true
	kit.ok(not Splash.is_press(echo), "key repeat does not count")
	var up := InputEventKey.new()
	up.pressed = false
	kit.ok(not Splash.is_press(up), "key release does not count")
	var mb := InputEventMouseButton.new()
	mb.pressed = true
	mb.button_index = MOUSE_BUTTON_LEFT
	kit.ok(Splash.is_press(mb), "click counts")
	var jb := InputEventJoypadButton.new()
	jb.pressed = true
	jb.button_index = JOY_BUTTON_A
	kit.ok(Splash.is_press(jb), "pad button counts")
	kit.ok(not Splash.is_press(InputEventMouseMotion.new()), "mouse motion does not count")
	var jm := InputEventJoypadMotion.new()
	jm.axis_value = 1.0
	kit.ok(not Splash.is_press(jm), "stick motion does not count")
	var s := _splash()
	s.start()
	s._input(k)
	kit.eq(s.get("presses"), 1, "_input routes a key press to press()")
	s._input(echo)
	kit.eq(s.get("presses"), 1, "…and ignores the repeat")
	return true


func _flag() -> bool:
	var S := SettingsScript
	kit.eq(Settings.path, S.PATH, "the Settings autoload keeps the player's file")
	DirAccess.make_dir_recursive_absolute(TMP_SETTINGS.get_base_dir())
	if FileAccess.file_exists(TMP_SETTINGS):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SETTINGS))
	var a: Node = S.new()
	a.path = TMP_SETTINGS
	a.load_settings()
	kit.ok(not BootFlow.notice_seen(a), "fresh settings: notice not seen")
	BootFlow.player_launch = true
	BootFlow.notice_opened = false
	kit.ok(BootFlow.notice_due(a), "player launch + not seen = due")
	BootFlow.notice_opened = true
	kit.ok(not BootFlow.notice_due(a), "never twice in one session")
	BootFlow.notice_opened = false
	BootFlow.mark_notice_seen(a)
	kit.ok(FileAccess.file_exists(TMP_SETTINGS), "flag written to the temporary settings file")
	var cfg := ConfigFile.new()
	kit.eq(cfg.load(TMP_SETTINGS), OK, "temporary file readable")
	kit.eq(cfg.get_value("settings", BootFlow.NOTICE_KEY, false), true, "demo_notice_seen = true on disk")
	var b: Node = S.new()
	b.path = TMP_SETTINGS
	b.load_settings()
	kit.ok(BootFlow.notice_seen(b), "a new session reads the flag")
	kit.ok(not BootFlow.notice_due(b), "…and does not show the letter again")
	kit.eq(b.get_value("text_scale"), 1.0, "other settings untouched")
	BootFlow.player_launch = false
	a.free()
	b.free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SETTINGS))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SETTINGS.get_base_dir()))
	kit.ok(S.DEFAULTS.has(BootFlow.NOTICE_KEY) and S.DEFAULTS[BootFlow.NOTICE_KEY] == false, "default: not seen")
	return true


func _driver_mode() -> bool:
	var mock := MockSettings.new()
	kit.track(mock)
	UKit.overrides["Settings"] = mock
	BootFlow.player_launch = false
	BootFlow.notice_opened = false
	var mm: Control = (load("res://scenes/ui/MainMenu.tscn") as PackedScene).instantiate()
	kit.mount(mm)
	mm.open()
	kit.ok(not BootFlow.notice_opened, "main menu in a driver / test run opens no letter")
	mm.close()
	BootFlow.player_launch = true
	mm.open()
	kit.ok(BootFlow.notice_opened, "main menu of a player launch asks for the letter on its first opening")
	mm.close()
	BootFlow.notice_opened = false
	mock.values["demo_notice_seen"] = true
	mm.open()
	kit.ok(not BootFlow.notice_opened, "…but not once it was confirmed")
	mm.close()
	BootFlow.player_launch = false
	UKit.overrides.erase("Settings")
	var src := FileAccess.get_file_as_string("res://scripts/core/main.gd")
	kit.ok(src.contains("BootFlow.decide(self)") and src.find("BootFlow.decide(self)") < src.find("Game.register_main(self)"),
		"Main decides before registering with Game")
	return true


func _notice(ts := 1.0) -> Control:
	var mock := MockSettings.new()
	mock.values["text_scale"] = ts
	kit.track(mock)
	UKit.overrides["Settings"] = mock
	var n: Control = (load(NOTICE_SCENE) as PackedScene).instantiate()
	n.theme = UKit.theme()               # as under UIRoot (paper margins, fonts)
	kit.mount(n)
	return n


func _letter() -> bool:
	var n := _notice()
	var mock: Node = UKit.overrides["Settings"]
	n.open(true)
	kit.ok(n.is_open, "letter open")
	kit.ok(n.guarded(), "first opening: presses are swallowed while the letter arrives")
	var k := InputEventKey.new()
	k.pressed = true
	k.physical_keycode = KEY_ENTER
	kit.ok(n.modal_input(k), "a mashed Enter is swallowed")
	n._confirm()
	kit.ok(n.is_open, "„Los geht's“ during the guard does nothing")
	n.set("_guard_until", 0)
	kit.ok(not n.modal_input(k), "after the guard keys reach the button")
	var body: String = n.get("_body").text
	for w in ["Demo", "Kapitel 1 bis 4", "Stunde", "Grafik", "Musik", "Texte", "Kapitel", "Danke", "Rückmeldung"]:
		kit.ok(body.contains(w), "letter mentions „%s“" % w)
	for bad in ["fiktiv", "Fiktion", "alternative Geschichte", "erfunden"]:
		kit.ok(not body.to_lower().contains(bad.to_lower()), "no fiction note („%s“)" % bad)
	kit.ok(str(n.get("_sign").text).contains(UKit.t("splash.studio")), "signed with the studio name")
	kit.ok(str(n.get("_sign").text).contains("Grüße"), "warm greetings")
	kit.ok(str(n.get("_kicker").text).contains(str(ProjectSettings.get_setting("application/config/version"))),
		"kicker shows the version")
	kit.eq(n.get("_ok").text, UKit.t("ui.demo.ok"), "one clear button")
	kit.ok(str(n.get("_ok").text).begins_with("Los geht"), "button „Los geht's“")
	n._confirm()
	kit.ok(not n.is_open, "„Los geht's“ closes it")
	kit.eq(mock.values["demo_notice_seen"], true, "closing sets the flag through Settings")
	mock.values["demo_notice_seen"] = false
	n.open(false)
	kit.ok(n.guarded(), "from the credits: a short guard only")
	n.set("_guard_until", 0)
	kit.ok(n.handle_cancel(), "Esc / B handled")
	kit.ok(not n.is_open, "Esc / B close it as well")
	kit.eq(mock.values["demo_notice_seen"], true, "…and set the flag")
	UKit.overrides.erase("Settings")
	return true


## Height of a wrapping label at a width (Label shapes its lines for its current width; no container pass needed).
func _label_h(l: Label, w: float) -> float:
	l.size = Vector2(w, 0)
	return l.get_minimum_size().y


func _letter_sizes() -> bool:
	for ts in [1.0, 1.25, 1.5]:
		var n := _notice(ts)
		n.open(false)
		var paper: PanelContainer = n.get("_paper")
		var w: float = n.sheet_width(ts)
		kit.eq(paper.custom_minimum_size.x, w, "sheet width at %d %%" % int(ts * 100))
		kit.ok(w <= 1920.0 - 160.0, "sheet keeps a margin at %d %% (%d px)" % [int(ts * 100), int(w)])
		var sb := paper.get_theme_stylebox("panel")
		var inner := w - sb.get_margin(SIDE_LEFT) - sb.get_margin(SIDE_RIGHT)
		var head: Label = n.get("_kicker")
		var h: float = sb.get_margin(SIDE_TOP) + sb.get_margin(SIDE_BOTTOM) + maxf(head.get_minimum_size().y, 30.0) 			+ 4.0 * float(n.get("GAP")) + 4.0
		for key in ["_heading", "_body"]:
			var l: Label = n.get(key)
			kit.eq(l.get_theme_font_size("font_size"), int(round(float(l.get_meta("aoe_base_size")) * ts)),
				"%s follows the text scale" % key)
			h += _label_h(l, inner)
		var ok_btn: Button = n.get("_ok")
		var sign: Label = n.get("_sign")
		h += maxf(_label_h(sign, inner - ok_btn.get_combined_minimum_size().x - 24.0), ok_btn.get_combined_minimum_size().y)
		kit.ok(h <= 1080.0 - 60.0, "the letter fits the frame at %d %% (%d px)" % [int(ts * 100), int(h)])
		n.set("_guard_until", 0)
		n.close()
		UKit.overrides.erase("Settings")
	UKit.refresh_text_scale()
	return true


func _entries() -> bool:
	var src := FileAccess.get_file_as_string("res://scripts/ui/ui_root.gd")
	kit.ok(src.contains("func open_demo_notice(first_run := false) -> void:"), "UIRoot.open_demo_notice()")
	kit.ok(src.contains("_add_demo_notice()"), "UIRoot instances the letter")
	var cr: Control = (load("res://scenes/ui/Credits.tscn") as PackedScene).instantiate()
	kit.mount(cr)
	var found := false
	for b in cr.find_children("*", "Button", true, false):
		if (b as Button).text == UKit.t("ui.demo.credits_button"):
			found = true
	kit.ok(found, "„Mitwirkende“ has the button „%s“" % UKit.t("ui.demo.credits_button"))
	return true


func _lettering() -> bool:
	for key in ["splash.studio", "splash.made_with", "splash.engine"]:
		kit.ok(UKit.has_key(key), key + " exists")
		kit.ok(PixelFont.supports(UKit.t(key)), key + " can be lettered in pixel capitals")
	kit.eq(UKit.t("splash.studio"), "HOTTE-HUI", "studio name")
	var loc := UKit.svc("Loc")
	if loc != null and loc.has_method("source_of"):
		kit.eq(loc.source_of("splash.studio"), "res://data/locale/de_splash.json", "the studio name lives in ONE key")
	var img := PixelFont.render("HOTTE-HUI", {"tracking": 1})
	kit.ok(img != null and img.get_height() == PixelFont.ROWS + 4, "1x lettering is 8 rows + padding")
	var big := PixelFont.render("ÄÖÜ GODOT", {"smooth": true, "bold": true, "outline": Color.BLACK, "shadow": Color.BLACK,
		"ramp": [Color.WHITE, Color.GRAY], "bevel": true})
	kit.ok(big != null and big.get_height() == PixelFont.ROWS * 2 + 4, "Scale2x lettering doubles the rows")
	kit.ok(PixelFont.render("HOTTE·HUI ✓", {}) == null, "unknown characters → null (Label fallback)")
	var s := _splash()
	var studio: Control = s.get("_studio")
	var pix := 0
	for r in studio.find_children("*", "TextureRect", true, false):
		if (r as TextureRect).texture is ImageTexture:
			pix += 1
	kit.ok(pix >= 1, "studio name drawn as pixel lettering")
	var engine: Control = s.get("_engine")
	for r in engine.find_children("*", "TextureRect", true, false):
		var t := (r as TextureRect).texture
		kit.ok(t is ImageTexture or (t != null and t.resource_path.begins_with("res://assets/ui/")),
			"engine card uses only our lettering / UI kit art (no third-party logo)")
	return true


func _assets() -> bool:
	var sizes := {"title_scene.png": Vector2i(640, 420), "title_lamp.png": Vector2i(640, 420),
		"studio_mark.png": Vector2i(40, 40), "studio_glow.png": Vector2i(40, 40)}
	for f in sizes:
		var t: Texture2D = load(Splash.DIR + f)
		kit.ok(t != null, f + " imported")
		if t != null:
			kit.eq(Vector2i(t.get_size()), sizes[f], f + " size")
	var logo: Texture2D = load(Splash.DIR + "title_logo.png")
	var sub: Texture2D = load(Splash.DIR + "title_sub.png")
	kit.ok(logo != null and logo.get_width() >= 320 and logo.get_width() <= 600, "title lettering is wide and inside the frame")
	kit.ok(sub != null and sub.get_width() < logo.get_width(), "subtitle narrower than the title")
	var gen := FileAccess.get_file_as_string("res://tools/pixelgen/gen_title_splash.py")
	kit.ok(gen.contains("TILT = %d" % Splash.TILT_ROWS), "tilt rows match the generator")
	kit.ok(gen.contains("HZ = 232"), "horizon row documented in the generator")
	for a in ["res://assets/audio/music/mus_title_sting.wav", "res://assets/audio/sfx/splash_ember.wav"]:
		var st: AudioStream = load(a)
		kit.ok(st != null, a.get_file() + " imported")
		if st != null:
			kit.ok(st.get_length() > 2.5 and st.get_length() < 12.0, a.get_file() + " length %.1f s" % st.get_length())
	var ag := FileAccess.get_file_as_string("res://tools/audiogen/title_audio.py")
	kit.ok(ag.contains("STROKE = %.2f" % Splash.LOGO_AT), "the sting's stroke lands when the title appears")
	return true
