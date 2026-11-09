extends RefCounted
## Languages (TECHNICAL_ARCHITECTURE §12.14): German is the source, English lays data/locale/en_<name>.json over each
## de_<name>.json (en_v3.json over the strings of data/v3/locale_de.json). Covers the switch and its fallback to German
## for a missing key, the live re-translation of texts on screen, placeholder parity of every key both languages have,
## the "language" setting (first-launch pick, persistence in a temporary file, CLI overrides never written), German in
## every automated run, the settings row „Sprache / Language“ and the typography of the fonts in use.

const TKit := preload("res://tests/support/test_kit.gd")
const UKit := preload("res://scripts/ui/ui_kit.gd")
const LocScript := preload("res://scripts/story/loc.gd")
const SettingsScript := preload("res://scripts/core/settings.gd")
const BootFlow := preload("res://scripts/ui/boot_flow.gd")
const PixelFont := preload("res://scripts/ui/pixel_font.gd")
const TMP_DIR := "user://_test_localisation"
const TMP_SETTINGS := TMP_DIR + "/settings.cfg"
const LOCALE_DIR := "res://data/locale"
## English typography (and the German marks) every font in use must draw itself: “ ” ‘ ’ — … „ ‚ –
const MARKS := [0x201C, 0x201D, 0x2018, 0x2019, 0x2014, 0x2026, 0x201E, 0x201A, 0x2013]
const BBCODE := "\\[/?(b|i|u|s|color|font_size|font|url|center|right|left|fill|indent|ul|ol|lb|rb|wave|shake|tornado|rainbow|pulse|fade|img|code|outline_color|outline_size|bgcolor|fgcolor|hint|table|cell|p)(=[^\\]]*)?\\]"

var kit: TKit


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"language": "de", "text_scale": 1.0, "high_contrast": false, "reduced_motion": false}
	var sets: Array = []

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		sets.append([key, v])
		changed.emit(key, v)


func run() -> Array:
	kit = TKit.new()
	kit.run_case("switch_and_german_fallback", _switch)
	kit.run_case("retranslate_texts_on_screen", _retranslate)
	kit.run_case("real_tables_keep_every_key", _real_tables)
	kit.run_case("placeholder_parity_de_en", _parity)
	kit.run_case("setting_persists_in_temp_file", _persistence)
	kit.run_case("automation_stays_german", _automation)
	kit.run_case("settings_row_sprache_language", _settings_row)
	kit.run_case("live_switch_main_menu", _live_switch)
	kit.run_case("autoload_back_to_german", _restore)
	kit.run_case("typography_in_every_font", _typography)
	UKit.overrides.erase("Settings")
	kit.cleanup()
	_remove_tmp()
	return kit.failures


# ---------------------------------------------------------------- helpers
func _write_json(path: String, data: Dictionary) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(data, " "))
	f.close()


func _remove_tmp() -> void:
	var d := DirAccess.open(TMP_DIR)
	if d == null:
		return
	for f in d.get_files():
		d.remove(f)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_DIR))


func _fixture_loc() -> Node:
	DirAccess.make_dir_recursive_absolute(TMP_DIR)
	_write_json(TMP_DIR + "/de_t.json", {"locale": "de-DE", "strings": {"t.a": "Hallo {name}", "t.b": "Nur deutsch",
		"t.c": "Zurück", "t.d": "Straße", "t.e": "Gleich"}})
	_write_json(TMP_DIR + "/en_t.json", {"locale": "en", "strings": {"t.a": "Hello {name}", "t.c": "Back",
		"t.d": "Street", "t.e": "Gleich", "t.stray": "not in German"}})
	var loc: Node = kit.track(LocScript.new())
	loc.locale_dir = TMP_DIR
	loc.reload()
	return loc


## Placeholders a translation must keep: {name} fields, printf marks, BBCode tags and the number of line breaks.
func _marks(s: String) -> Dictionary:
	var out := {}
	for spec in [["braces", "\\{[A-Za-z0-9_]*\\}"], ["printf", "%[-+0#]?[0-9]*(\\.[0-9]+)?[sdifxXc]"], ["bbcode", BBCODE]]:
		var re := RegEx.new()
		re.compile(spec[1])
		var found: Array = []
		for m in re.search_all(s):
			found.append(m.get_string())
		found.sort()
		out[spec[0]] = found
	out["newlines"] = s.count("\n")
	return out


func _table(path: String) -> Dictionary:
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not (d is Dictionary):
		return {}
	var t = (d as Dictionary).get("strings", d)
	return t if t is Dictionary else {}


# ---------------------------------------------------------------- cases
func _switch() -> bool:
	var loc := _fixture_loc()
	kit.eq(loc.language, "de", "a fresh Loc speaks German")
	kit.eq(loc.t("t.a", {"name": "Alexei"}), "Hallo Alexei", "German source text")
	var n_over: int = loc.overrides.size()
	var heard: Array = []
	loc.language_changed.connect(func(l: String): heard.append(l))
	loc.set_language("en")
	kit.eq(loc.language, "en", "switched to English")
	kit.eq(heard, ["en"], "language_changed emitted once")
	kit.eq(loc.t("t.a", {"name": "Alexei"}), "Hello Alexei", "English text, placeholder filled")
	kit.eq(loc.t("t.b"), "Nur deutsch", "a key without translation falls back to German")
	kit.eq(loc.t("t.missing"), "[t.missing]", "an unknown key stays visible")
	kit.ok(not loc.has("t.stray"), "a key only the English file has is ignored")
	kit.eq(loc.translated_by("t.a"), TMP_DIR + "/en_t.json", "translated_by names the twin file")
	kit.eq(loc.translated_by("t.b"), "", "untranslated key")
	kit.ok("t.b" in loc.untranslated(), "untranslated() lists the German fallbacks")
	kit.eq(loc.source_of("t.a"), TMP_DIR + "/de_t.json", "source_of stays the German file")
	kit.eq(loc.overrides.size(), n_over, "the overlay is no key collision")
	loc.set_language("fr")
	kit.eq(loc.language, "en", "an unknown language code is ignored")
	loc.set_language("en")
	kit.eq(heard.size(), 1, "no signal when nothing changes")
	loc.set_language("de")
	kit.eq(loc.t("t.a", {"name": "Konrad"}), "Hallo Konrad", "back to German")
	kit.eq(loc.untranslated(), [], "German has no fallbacks")
	kit.eq(loc.twin_path(LocScript.V3_FILE, "en"), TMP_DIR + "/en_v3.json", "story strings → en_v3.json")
	kit.eq(loc.twin_path(TMP_DIR + "/de_t.json", "en"), TMP_DIR + "/en_t.json", "de_x.json → en_x.json")
	return true


func _retranslate() -> bool:
	var loc := _fixture_loc()
	var box := VBoxContainer.new()
	kit.track(box)
	var texts := ["Zurück", "ZURÜCK", "STRASSE", "Gleich", "Nur deutsch", "Etwas anderes", ""]
	for t in texts:
		var l := Label.new()
		l.text = t
		box.add_child(l)
	var b := Button.new()
	b.text = "Straße"
	box.add_child(b)
	var r := RichTextLabel.new()
	r.text = "Zurück"
	box.add_child(r)
	var old: Dictionary = loc.get("_strings").duplicate()
	loc.set_language("en")   # not in the tree: no walk of its own
	var n: int = loc.retranslate(box, old)
	var got: Array = []
	for c in box.get_children():
		got.append(str(c.get("text")))
	kit.eq(got, ["Back", "BACK", "STREET", "Gleich", "Nur deutsch", "Etwas anderes", "", "Street", "Back"],
		"plain and capital texts follow, the rest stays")
	kit.eq(n, 5, "five texts changed")
	return true


func _real_tables() -> bool:
	var de: Node = kit.track(LocScript.new())
	de.reload()
	var en: Node = kit.track(LocScript.new())
	en.language = "en"
	en.reload()
	kit.eq(en.keys(), de.keys(), "English has exactly the German keys (every gap falls back)")
	kit.eq(en.overrides, de.overrides, "the overlay adds no key collisions")
	kit.eq(de.t("ui.settings.language"), "Sprache / Language", "German row label")
	kit.eq(en.t("ui.settings.language"), "Language / Sprache", "English row label (en_lang.json)")
	kit.eq(en.t("splash.studio"), de.t("splash.studio"), "the studio name is the same in both languages")
	kit.eq(de.t("splash.studio"), "Midnight Anvil", "studio name")
	var total: int = de.keys().size()
	var open_keys: Array = en.untranslated()
	print("  test_localisation: %d keys, %d translated into English, %d fall back to German" % [total,
		total - open_keys.size(), open_keys.size()])
	return true


func _parity() -> bool:
	var dir := DirAccess.open(LOCALE_DIR)
	kit.ok(dir != null, "locale folder")
	if dir == null:
		return true
	var files: Array = []
	for f in dir.get_files():
		if f.begins_with("en_") and f.ends_with(".json"):
			files.append(f)
	files.sort()
	kit.ok("en_lang.json" in files, "en_lang.json exists")
	var checked := 0
	for f in files:
		var en_path: String = LOCALE_DIR + "/" + f
		var de_path: String = LocScript.V3_FILE if f == "en_v3.json" else LOCALE_DIR + "/de_" + f.substr(3)
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(en_path))
		if not kit.ok(parsed is Dictionary, f + " is valid JSON (an object)"):
			continue
		if not kit.ok(FileAccess.file_exists(de_path), f + " has a German twin " + de_path):
			continue
		var en := _table(en_path)
		var de := _table(de_path)
		var extra: Array = []
		for k in en:
			if not de.has(k):
				extra.append(k)
		kit.eq(extra.slice(0, 8), [], f + ": keys the German twin does not have (typos?)")
		var bad: Array = []
		for k in en:
			if not de.has(k):
				continue
			checked += 1
			if not (en[k] is String):
				bad.append("%s (not a string)" % k)
				continue
			var a := _marks(str(de[k]))
			var b := _marks(str(en[k]))
			if not TKit.strict_eq(a, b):
				bad.append("%s de=%s en=%s" % [k, JSON.stringify(a), JSON.stringify(b)])
		kit.eq(bad.slice(0, 6), [], "%s: placeholders ({name}, printf, BBCode, line breaks) differ (%d keys)" % [f, bad.size()])
	kit.ok(checked > 0, "compared %d keys" % checked)
	return true


func _persistence() -> bool:
	var S := SettingsScript
	kit.eq(S.default_language("de"), "de", "German OS → German")
	kit.eq(S.default_language("DE"), "de", "case does not matter")
	for os_lang in ["en", "fr", "ru", ""]:
		kit.eq(S.default_language(os_lang), "en", "OS '%s' → English" % os_lang)
	kit.eq(S.DEFAULTS.get("language"), "de", "default value in DEFAULTS")
	DirAccess.make_dir_recursive_absolute(TMP_DIR)
	if FileAccess.file_exists(TMP_SETTINGS):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SETTINGS))
	var pick := S.default_language(OS.get_locale_language())
	# a player's first launch: picked from the OS, only that key written
	var a: Node = kit.track(S.new())
	a.path = TMP_SETTINGS
	a.load_settings()
	kit.ok(a.language_picked, "no file: first launch")
	kit.eq(a.get_value("language"), pick, "picked from the OS locale")
	a.apply_run_overrides(PackedStringArray(), PackedStringArray(["--path", "C:/Spiele/AshesOfEmpires"]), "Windows")
	var cfg := ConfigFile.new()
	kit.eq(cfg.load(TMP_SETTINGS), OK, "first launch wrote the file")
	kit.eq(cfg.get_value("settings", "language", ""), pick, "…with the picked language")
	kit.eq(cfg.get_section_keys("settings"), PackedStringArray(["language"]), "…and nothing else")
	# the player switches to English (Settings API) — a new session reads it back
	a.set_value("language", "en")
	var b: Node = kit.track(S.new())
	b.path = TMP_SETTINGS
	b.load_settings()
	kit.ok(not b.language_picked, "the language is on disk now")
	kit.eq(b.get_value("language"), "en", "a new session reads English")
	# a driver run on that profile plays German and never writes it
	var c: Node = kit.track(S.new())
	c.path = TMP_SETTINGS
	c.load_settings()
	c.apply_run_overrides(PackedStringArray(["--autoplay=share_with_irina,preserve_evidence"]), PackedStringArray(), "Windows")
	kit.eq(c.get_value("language"), "de", "automated run: German")
	c.set_value("text_scale", 1.25)
	cfg = ConfigFile.new()
	cfg.load(TMP_SETTINGS)
	kit.eq(cfg.get_value("settings", "language", ""), "en", "the player's English stays on disk")
	kit.eq(cfg.get_value("settings", "text_scale", 0.0), 1.25, "other settings are still written")
	# --lang=en (checks) is not written either
	var d: Node = kit.track(S.new())
	d.path = TMP_SETTINGS
	d.set_value("language", "de")
	d.apply_run_overrides(PackedStringArray(["--lang=en"]), PackedStringArray(), "Windows")
	kit.eq(d.get_value("language"), "en", "--lang=en forces English")
	d.set_value("vsync", false)
	cfg = ConfigFile.new()
	cfg.load(TMP_SETTINGS)
	kit.eq(cfg.get_value("settings", "language", ""), "de", "--lang=en is never persisted")
	# a fresh profile in a driver run: no language is written at all (the player's first launch still picks)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SETTINGS))
	var e: Node = kit.track(S.new())
	e.path = TMP_SETTINGS
	e.load_settings()
	e.apply_run_overrides(PackedStringArray(["--inputplay=share_with_irina,preserve_evidence"]), PackedStringArray(),
		"Windows")
	kit.ok(not FileAccess.file_exists(TMP_SETTINGS), "an automated first run writes no file")
	e.set_value("text_scale", 1.5)
	cfg = ConfigFile.new()
	cfg.load(TMP_SETTINGS)
	kit.ok(not cfg.has_section_key("settings", "language"), "…and never a language")
	# an unknown value on disk counts as not chosen
	cfg.set_value("settings", "language", "fr")
	cfg.save(TMP_SETTINGS)
	var f: Node = kit.track(S.new())
	f.path = TMP_SETTINGS
	f.load_settings()
	kit.ok(f.language_picked and f.get_value("language") == pick, "unknown code on disk → picked again")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SETTINGS))
	return true


func _automation() -> bool:
	var S := SettingsScript
	var eng := PackedStringArray(["--path", "C:/Spiele/AshesOfEmpires"])
	kit.eq(S.forced_language(PackedStringArray(), eng, "Windows"), "", "a player's launch uses the setting")
	var cases := [
		[["--lang=en"], eng, "Windows", "en"], [["--lang=EN"], eng, "Windows", "en"], [["--lang=fr"], eng, "Windows", "de"],
		[["--autoplay=share_with_irina,preserve_evidence"], eng, "Windows", "de"],
		[["--inputplay=a,b", "--lang=en"], eng, "Windows", "en"], [["--splash-shots=C:/tmp/s"], eng, "Windows", "de"],
		[["--splash-shots=C:/tmp/s", "--lang=en"], eng, "Windows", "en"], [["--capture=C:/tmp/x.png"], eng, "Windows", "de"],
		[[], PackedStringArray(["--script", "res://tests/run_all.gd"]), "Windows", "de"], [[], eng, "headless", "de"],
		[[], PackedStringArray(["--path", ".", "res://tests/visual/UIPreview.tscn"]), "Windows", "de"],
	]
	for c in cases:
		kit.eq(S.forced_language(PackedStringArray(c[0]), c[1], c[2]), c[3], "forced_language %s %s %s" % [c[0], c[1], c[2]])
	kit.ok(BootFlow.is_player_launch(PackedStringArray(["--lang=en"]), eng, "Windows", true), "--lang keeps a player launch")
	kit.ok(BootFlow.is_player_launch(PackedStringArray(["--splash-shots=C:/tmp/s", "--lang=en"]), eng, "Windows", true),
		"English check run of the boot sequence")
	kit.ok(not BootFlow.is_player_launch(PackedStringArray(["--autoplay=a,b", "--lang=en"]), eng, "Windows", true),
		"a driver stays a driver")
	# this very run (a --script main loop) plays German, whatever the player chose
	var forced_here := S.forced_language(OS.get_cmdline_user_args(), OS.get_cmdline_args(), DisplayServer.get_name())
	var lang_arg := false
	for a in OS.get_cmdline_user_args():
		lang_arg = lang_arg or a.begins_with("--lang=")
	if not lang_arg:
		kit.eq(forced_here, "de", "the test run is forced to German")
		kit.eq(Settings.get_value("language"), "de", "Settings autoload: German")
		kit.eq(Loc.language, "de", "Loc autoload: German")
		kit.eq(Loc.t("ui.settings.language"), "Sprache / Language", "Loc autoload serves the German table")
	kit.eq(Settings.path, S.PATH, "the autoload keeps the player's file (tests use temporary files)")
	return true


func _settings_row() -> bool:
	var mock := MockSettings.new()
	kit.track(mock)
	UKit.overrides["Settings"] = mock
	var sm: Control = (load("res://scenes/ui/SettingsMenu.tscn") as PackedScene).instantiate()
	kit.mount(sm)
	sm.open("display")
	var rows: VBoxContainer = sm.get("_rows_box")
	var first: HBoxContainer = null
	for h in rows.get_children():
		if h is HBoxContainer:
			first = h
			break
	if not kit.ok(first != null, "the display tab has rows"):
		return true
	kit.eq(str(first.get_meta("desc", "")), "ui.settings.desc.language", "first row of the display tab: language")
	kit.eq((first.get_child(0) as Label).text, UKit.t("ui.settings.language"), "label „Sprache / Language“")
	var step: Button = first.get_child(1) as Button
	kit.eq(step.get("options"), [["de", "Deutsch"], ["en", "English"]], "both languages in their own name")
	kit.eq(step.text, "Deutsch", "shows the current language")
	kit.eq(step.focus_mode, Control.FOCUS_ALL, "reachable with keys and pad")
	step.call("step", 1)
	kit.eq(mock.sets.back() if not mock.sets.is_empty() else [], ["language", "en"], "right/next writes the setting")
	step.call("_pressed")
	kit.eq(mock.values["language"], "de", "a click cycles back to German")
	kit.ok(sm.has_method("_on_language_changed"), "the menu relabels itself on a switch")
	sm.close()
	UKit.overrides.erase("Settings")
	return true


## The real Loc autoload switches live: plain texts of a mounted main menu follow at once, the formatted footer via
## _on_language_changed (UIRoot's propagate_call), and everything returns to German.
func _live_switch() -> bool:
	var mock := MockSettings.new()
	kit.track(mock)
	UKit.overrides["Settings"] = mock
	var mm: Control = (load("res://scenes/ui/MainMenu.tscn") as PackedScene).instantiate()
	kit.mount(mm)
	var probe := Label.new()
	probe.text = Loc.t("ui.settings.language")
	kit.mount(probe)
	var buttons: Dictionary = mm.get("_buttons")
	var new_btn: Button = buttons["new"]
	var de_new := new_btn.text
	kit.eq(de_new, Loc.t("ui.new_game"), "German entry")
	var heard: Array = []
	var cb := func(l: String): heard.append(l)
	Loc.language_changed.connect(cb)
	Loc.set_language("en")
	kit.eq(heard, ["en"], "language_changed")
	kit.eq(probe.text, "Language / Sprache", "a plain text on screen follows at once")
	kit.eq(new_btn.text, Loc.t("ui.new_game"), "main menu entry in the new language")
	mm.call("_on_language_changed")
	var footer: Label = mm.get("_footer")
	kit.eq(footer.text, Loc.t("ui.menu.footer", {"version": str(ProjectSettings.get_setting("application/config/version",
		"0.1.0"))}), "formatted footer redone by the hook")
	Loc.set_language("de")
	Loc.language_changed.disconnect(cb)
	kit.eq(probe.text, "Sprache / Language", "back to German on screen")
	kit.eq(new_btn.text, de_new, "entry back to German")
	UKit.overrides.erase("Settings")
	kit.ok(ResourceLoader.exists("res://scenes/ui/UIRoot.tscn") and
		(load("res://scripts/ui/ui_root.gd") as Script).get_script_method_list().any(
			func(m): return m["name"] == "_on_loc_language_changed"), "UIRoot relays the switch to the panels")
	kit.ok((load("res://scripts/ui/pause_menu.gd") as Script).get_script_method_list().any(
		func(m): return m["name"] == "_on_language_changed"), "the pause menu redoes its formatted lines")
	return true


func _restore() -> bool:
	if Loc.language != "de":
		Loc.set_language("de")
	kit.eq(Loc.language, "de", "the Loc autoload is German again for the following tests")
	kit.eq(Loc.t("ui.settings.language"), "Sprache / Language", "German table restored")
	return true


func _typography() -> bool:
	var dir := DirAccess.open("res://assets/fonts")
	var n := 0
	for f in dir.get_files():
		if not f.ends_with(".tres"):
			continue
		var font := load("res://assets/fonts/" + f) as Font
		if not kit.ok(font != null, f + " loads"):
			continue
		var faces: Array = [font]
		if font is FontVariation and (font as FontVariation).base_font != null:
			faces.append((font as FontVariation).base_font)
		for face in faces:
			var miss: Array = []
			for c in MARKS:
				if not (face as Font).has_char(c):
					miss.append("U+%04X" % c)
			kit.eq(miss, [], "%s (%s) draws “ ” ‘ ’ — … „ ‚ –" % [f, (face as Resource).resource_path.get_file()])
		n += 1
	kit.ok(n >= 10, "checked %d font resources" % n)
	kit.ok(PixelFont.supports("“Made with” ‘Godot’ — … „Karsk“ ‚C-17‘ – \"ok\" don’t"), "pixel capitals know the marks")
	var img := PixelFont.render("—…“”‘’", {"tracking": 1})
	kit.ok(img != null and img.get_height() == PixelFont.ROWS + 4, "the marks letter on the 8-row grid")
	kit.ok(PixelFont.supports(Loc.t("splash.made_with")) and PixelFont.supports(Loc.t("splash.engine"))
		and PixelFont.supports(Loc.t("splash.studio")), "the boot cards letter their texts")
	var en: Node = kit.track(LocScript.new())
	en.language = "en"
	en.reload()
	for key in ["splash.studio", "splash.made_with", "splash.engine"]:
		kit.ok(PixelFont.supports(en.t(key)), "English %s can be lettered: %s" % [key, en.t(key)])
	return true
