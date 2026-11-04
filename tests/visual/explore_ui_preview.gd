extends Control
## Exploration UI harness (tests/visual/explore_ui_preview.tscn) — explore-system, round 2.
## Instances scenes/ui/UIRoot.tscn over a stand-in game frame, injects a MOCK Explore service (its own data,
## images and in-memory strings; the real data/explore files are not used) through ui_kit overrides, walks
## through every new UI state (HUD prompt markers + toasts, DiscoveryView find/history pages, journal tabs
## "Entdeckungen"/"Geschichte", pause progress, settings toggle), checks behaviour (paging, guard, Esc,
## closed once, pause, toasts suppressed while open, cards toast fallback) and saves 1920x1080 screenshots.
## Settings are changed IN MEMORY only (never Settings.set_value -> the player's settings file is untouched).
##   godot --path . res://tests/visual/explore_ui_preview.tscn -- --out=C:/path/to/dir [--only=find,card]
## Exit code: 0 = all checks passed, 1 = a check failed.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const UIROOT := preload("res://scenes/ui/UIRoot.tscn")
const EXPLORE := preload("res://scripts/core/explore.gd")
const MOCK_IMG := "res://tests/visual/explore_ui_mock_closeup.png"
const BG := "res://assets/ui/_preview/karsk_frame.png"

## Mock strings (German, in memory only). The history mock texts are accurate summaries; the real cards are
## written by the history specialists in data/locale/de_history_*.json.
const STRINGS := {
	"mock.tea.title": "Tee im Glashalter",
	"mock.tea.prompt": "Tee ansehen",
	"mock.tea.text": "Irinas Glas, noch warm. Der Halter ist aus Neusilber, mit Ähren und einem Traktor – Ausgabe zum Jubiläum der Bahnmeisterei. Unter dem Glas liegt die Zeitung von gestern. Jemand hat einen Artikel ausgeschnitten, sorgfältig, mit der Rasierklinge.",
	"mock.cat.title": "Die Kioskkatze",
	"mock.cat.text": "Sie heißt Pjatiletka, sagt die Verkäuferin. Wie der Fünfjahresplan: Sie wird jedes Jahr runder, und keiner weiß, wovon.",
	"mock.stash.title": "Hinter dem losen Ziegel",
	"mock.stash.text": "Ein Ziegel in der Stellwerkswand sitzt locker. Dahinter: eine Blechdose, drei Rubel, ein Foto ohne Namen.",
	"mock.workers.title": "Die Männer am Feuerfass",
	"mock.workers.l1": "Damals in der Stadt am Don, da haben sie auch erst geredet. Dann kamen die Lastwagen.",
	"mock.workers.l2": "Davon steht nichts in der Zeitung.",
	"mock.shelf.title": "Regal 1: Akten des Auswärtigen Amts",
	"mock.shelf.text": "Eine Lücke im Regal, wo die Signaturen springen. Im Verzeichnis steht nur: „Ausgesondert, Vorgang erledigt.“ Ich notiere die fehlenden Nummern. Es ist eine Ordnungsfrage, sage ich mir.",
	"mock.mouse.title": "Die Archivmaus",
	"mock.mouse.text": "Zwischen zwei Bauakten sitzt eine Maus und frisst an einem Genehmigungsbescheid von 1938. Sie hat keinen Antrag gestellt. Ich lasse sie gewähren; das Formular dafür gibt es noch nicht.",
	"mock.card.wannsee.title": "Das Protokoll der Wannsee-Konferenz",
	"mock.card.wannsee.text": "Am 20. Januar 1942 besprachen Staatssekretäre und SS-Führer in einer Villa am Großen Wannsee die Organisation des Mordes an den europäischen Juden. Das Protokoll wurde in 30 Ausfertigungen verteilt, die meisten später vernichtet. Erhalten blieb nur die 16. Ausfertigung: Mitarbeiter des amerikanischen Anklägers Robert Kempner fanden sie im März 1947 in Akten des Auswärtigen Amts. Das Dokument wurde zu einem zentralen Beweis dafür, dass der Völkermord von Ministerien und Behörden arbeitsteilig organisiert wurde.",
	"mock.card.katyn.title": "Katyn 1940 und das Eingeständnis von 1990",
	"mock.card.katyn.text": "Auf Beschluss des Politbüros vom 5. März 1940 erschoss das NKWD rund 22.000 polnische Kriegsgefangene und Häftlinge, darunter Offiziere, Polizisten und Angehörige der Intelligenz, im Wald von Katyn und an weiteren Orten. Die Sowjetunion schob die Tat jahrzehntelang der Wehrmacht zu; wer die Wahrheit aussprach, riskierte Verfolgung. Erst am 13. April 1990 räumte die Nachrichtenagentur TASS die Verantwortung des NKWD ein. 1992 wurden die Beschlussdokumente aus dem Präsidentenarchiv veröffentlicht.",
	"mock.card.x1.title": "Platzhalter Sowjetunion 2",
	"mock.card.x1.text": "–",
	"mock.card.x2.title": "Platzhalter Reich 2",
	"mock.card.x2.text": "–",
}


class FakeTarget extends Node:
	var state := ""
	func prompt_state() -> String:
		return state


var ui: Control
var ex: Node
var failures: Array = []
var shots := 0
var headless := false
var out_dir := ""
var only: PackedStringArray = []
## --real=id1,id2: render these entries of the REAL data/explore content (Explore autoload, in memory only)
var real_ids: PackedStringArray = []
var _bg: TextureRect


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	headless = DisplayServer.get_name() == "headless"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--only="):
			only = a.substr(7).split(",", false)
		elif a.begins_with("--real="):
			real_ids = a.substr(7).split(",", false)
	if out_dir == "":
		out_dir = OS.get_user_data_dir().path_join("explore_ui_preview")
	DirAccess.make_dir_recursive_absolute(out_dir)
	_setup_window()
	var loc := get_node_or_null("/root/Loc")
	if loc != null and "_strings" in loc:
		for k in STRINGS:
			loc._strings[k] = STRINGS[k]
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		s.values = s.DEFAULTS.duplicate(true)   # deterministic, in memory only (never saved here)
		if "_runtime_overrides" in s:           # keep CLI test overrides such as --symbols=0
			for k in s._runtime_overrides:
				s.values[k] = s._runtime_overrides[k]
	ex = EXPLORE.new()
	ex.name = "MockExplore"
	ex.print_warnings = false
	add_child(ex)
	ex.clear_data()   # _ready() loaded data/explore; the harness uses its own mock data only
	_mock_data()
	Kit.overrides = {} if not real_ids.is_empty() else {"Explore": ex}
	_bg = TextureRect.new()
	_bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_bg.stretch_mode = TextureRect.STRETCH_SCALE
	_bg.size = Vector2(1920, 1080)
	_bg.texture = _load_png(BG)
	add_child(_bg)
	ui = UIROOT.instantiate()
	add_child(ui)
	_run.call_deferred()


func _mock_data() -> void:
	ex.load_data({"area": "karsk", "entries": [
		{"id": "mock.karsk.tea", "kind": "detail", "level": "L_A1_Railyard", "title_key": "mock.tea.title",
			"text_key": "mock.tea.text", "prompt_key": "mock.tea.prompt", "image": MOCK_IMG, "history": ["hist.mock.katyn"]},
		{"id": "mock.karsk.cat", "kind": "easter_egg", "level": "L_A1_Railyard", "title_key": "mock.cat.title", "text_key": "mock.cat.text"},
		{"id": "mock.karsk.stash", "kind": "secret", "level": "L_A1_Railyard", "title_key": "mock.stash.title", "text_key": "mock.stash.text"},
		{"id": "mock.karsk.workers", "kind": "chat", "level": "L_A1_Railyard", "title_key": "mock.workers.title",
			"history": ["hist.mock.x1"], "lines": [{"speaker": "worker_a", "key": "mock.workers.l1"}, {"speaker": "alexei", "key": "mock.workers.l2"}]},
	]}, "mock_karsk.json")
	ex.load_data({"area": "berlin", "entries": [
		{"id": "mock.berlin.shelf", "kind": "detail", "level": "L_M1_Archive", "title_key": "mock.shelf.title",
			"text_key": "mock.shelf.text", "image": MOCK_IMG, "history": ["hist.mock.wannsee"]},
		{"id": "mock.berlin.mouse", "kind": "easter_egg", "level": "L_M1_Archive", "title_key": "mock.mouse.title", "text_key": "mock.mouse.text"},
		{"id": "mock.berlin.extra", "kind": "detail", "level": "L_M1_Archive", "title_key": "mock.mouse.title", "text_key": "mock.mouse.text",
			"history": ["hist.mock.x2"]},
	]}, "mock_berlin.json")
	ex.load_data({"side": "reich", "cards": [
		{"id": "hist.mock.wannsee", "title_key": "mock.card.wannsee.title", "text_key": "mock.card.wannsee.text", "year": "1947",
			"sources": [{"label": "Gedenk- und Bildungsstätte Haus der Wannsee-Konferenz", "url": "https://www.ghwk.de"},
				{"label": "Protokoll der Besprechung vom 20. Januar 1942 (16. Ausfertigung), Politisches Archiv des Auswärtigen Amts", "url": ""}]},
		{"id": "hist.mock.x2", "title_key": "mock.card.x2.title", "text_key": "mock.card.x2.text", "year": "–", "sources": [{"label": "–"}]},
	]}, "mock_history_reich.json")
	ex.load_data({"side": "soviet", "cards": [
		{"id": "hist.mock.katyn", "title_key": "mock.card.katyn.title", "text_key": "mock.card.katyn.text", "year": "1990",
			"sources": [{"label": "Erklärung der Nachrichtenagentur TASS vom 13. April 1990", "url": ""},
				{"label": "Institut für Nationales Gedenken (IPN), Warschau: Dossier Katyn", "url": "https://ipn.gov.pl/en"}]},
		{"id": "hist.mock.x1", "title_key": "mock.card.x1.title", "text_key": "mock.card.x1.text", "year": "–", "sources": [{"label": "–"}]},
	]}, "mock_history_soviet.json")
	check(ex.warnings.is_empty(), "mock data validates without warnings (%s)" % [ex.warnings])


func _setup_window() -> void:
	if headless:
		return
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	var scr := DisplayServer.screen_get_size()
	if scr.x <= 1920 or scr.y <= 1130:
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
		DisplayServer.window_set_position(Vector2i.ZERO)
	DisplayServer.window_set_size(Vector2i(1920, 1080))


func _load_png(path: String) -> Texture2D:
	var full := ProjectSettings.globalize_path(path)
	if not FileAccess.file_exists(full):
		return null
	var img := Image.load_from_file(full)
	return ImageTexture.create_from_image(img) if img != null and not img.is_empty() else null


func check(cond: bool, what: String) -> void:
	print(("  PASS " if cond else "  FAIL ") + what)
	if not cond:
		failures.append(what)


func wait(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func want(name: String) -> bool:
	return only.is_empty() or name in only


func shot(name: String) -> void:
	shots += 1
	if headless:
		print("SHOT (headless, skipped) ", name)
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join("%02d_%s.png" % [shots, name])
	img.save_png(path)
	print("SHOT ", path, " ", img.get_size())


func key(code: Key, pressed := true) -> void:
	var ev := InputEventKey.new()
	ev.physical_keycode = code
	ev.keycode = code
	ev.pressed = pressed
	Input.parse_input_event(ev)


func tap(code: Key) -> void:
	key(code, true)
	await get_tree().process_frame
	key(code, false)
	await get_tree().process_frame


func _dump(n: Node, depth := 0) -> void:
	if depth > 9:
		return
	if n is Control:
		var c := n as Control
		print("%s%s %s pos=%s size=%s min=%s" % ["  ".repeat(depth), c.name, c.get_class(), c.global_position, c.size, c.get_combined_minimum_size()])
	for ch in n.get_children():
		_dump(ch, depth + 1)


func set_text_scale(v: float) -> void:
	Kit.svc("Settings").values["text_scale"] = v
	Kit.refresh_text_scale()


func set_hc(on: bool) -> void:
	Kit.svc("Settings").values["high_contrast"] = on
	ui._on_setting_changed("high_contrast", on)


func _run_real() -> void:
	await wait(0.5)
	var real := get_node_or_null("/root/Explore")
	check(real != null, "real Explore autoload present")
	for id in real_ids:
		var r: Dictionary = real.find(id)
		check(r["ok"], "real entry '%s' exists" % id)
		ui.discovery.open(id, r["cards_new"])
		await wait(0.9)
		await shot("real_" + id.replace(".", "_"))
		while ui.discovery.is_open and not ui.discovery.is_last_page():
			ui.discovery._page_forward()
			await wait(0.7)
			await shot("real_" + id.replace(".", "_") + "_p%d" % ui.discovery.page)
		ui.discovery.close()
		await wait(0.3)
	ui.open_journal("discoveries")
	await wait(0.7)
	await shot("real_journal_discoveries")
	ui.journal.close()
	print("EXPLORE_UI_PREVIEW %s — %d shots, %d failure(s)" % ["OK" if failures.is_empty() else "FAILED", shots, failures.size()])
	Kit.clear_cache()
	get_tree().quit(0 if failures.is_empty() else 1)


func _run() -> void:
	if not real_ids.is_empty():
		await _run_real()
		return
	await wait(0.5)
	var dv = ui.discovery
	check(dv != null and ui.get("discovery") == dv, "UIRoot exposes `discovery`")
	check(dv.get("suppress_toasts") == true and dv.pauses_game, "DiscoveryView is modal, pauses, suppresses toasts")
	# ------------------------------------------------------------ HUD: prompt markers + toasts
	ui.hud.show_hud()
	var tgt := FakeTarget.new()
	add_child(tgt)
	tgt.state = "new"
	ui.hud.set_prompt_target(tgt)
	ui.hud.show_prompt(Vector2(760, 610), Kit.t("mock.tea.prompt"))
	check(ui.hud._prompt_mark.visible and ui.hud._prompt_state == "new", "prompt marks a not-yet-found find (from the target)")
	ex.find("mock.karsk.cat")
	var c: Dictionary = ex.counts("L_A1_Railyard")
	ui.hud.toast(Kit.t("ui.toast.discovery", {"name": Kit.t("mock.cat.title"), "n": c["found"], "total": c["total"]}))
	ui.hud.toast(Kit.t("ui.toast.history", {"name": Kit.t("mock.card.katyn.title")}))
	await wait(1.2)
	check(ui.hud._toast_box.get_child_count() == 2, "discovery + history toasts shown")
	if want("hud"):
		await shot("hud_prompt_new_toasts")
	tgt.state = "found"
	ui.hud.show_prompt(Vector2(760, 610), Kit.t("mock.tea.prompt"))
	check(ui.hud._prompt_state == "found", "prompt shows the already-found state")
	await wait(0.3)
	if want("hud"):
		await shot("hud_prompt_found")
	ui.hud.show_prompt(Vector2(760, 610), Kit.t("ui.prompt.inspect"), "interact", "none")
	check(not ui.hud._prompt_mark.visible, "story prompt stays plain")
	ui.hud.set_prompt_target(null)
	ui.hud.hide_prompt()
	await wait(4.6)
	# ------------------------------------------------------------ DiscoveryView: find with image + soviet card
	var r: Dictionary = ex.find("mock.karsk.tea")
	var closed_n := [0]
	dv.closed.connect(func(): closed_n[0] += 1)
	var pages_seen: Array = []
	dv.page_changed.connect(func(i): pages_seen.append(i))
	dv.open("mock.karsk.tea", r["cards_new"])
	ui.hud.toast("Toast während der Ansicht", "info")
	await wait(0.9)
	check(get_tree().paused, "find view pauses the world")
	check(dv.page_count() == 2 and dv.current_type() == "find", "find + one history page")
	check(not ui.hud._toast_box.visible, "toasts suppressed while the view is open")
	if want("debug"):
		_dump(dv)
	if want("find"):
		await shot("find_karsk_image")
	# input: the opening guard swallows an early press; E then pages forward
	dv._opened_ms = Time.get_ticks_msec()
	await tap(KEY_E)
	check(dv.page == 0, "opening guard: an immediate E press does not skip the page")
	dv._opened_ms = 0
	await tap(KEY_E)
	await wait(0.6)
	check(dv.page == 1 and dv.current_type() == "card", "E pages to the real-history card")
	if want("card"):
		await shot("card_soviet")
	await tap(KEY_LEFT)
	await wait(0.4)
	check(dv.page == 0, "Left goes back to the find")
	await tap(KEY_RIGHT)
	await wait(0.4)
	await tap(KEY_ESCAPE)
	await wait(0.4)
	check(not dv.is_open and closed_n[0] == 1, "Esc closes, closed emitted once")
	check(not get_tree().paused, "closing unpauses")
	await wait(0.6)
	# ------------------------------------------------------------ find without image (Berlin), then with image + reich card
	ex.find("mock.berlin.mouse")
	dv.open("mock.berlin.mouse", [])
	await wait(0.8)
	check(dv.page_count() == 1, "find without history = one page")
	if want("find"):
		await shot("find_berlin_noimage")
	dv._opened_ms = 0
	await tap(KEY_ENTER)
	await wait(0.4)
	check(not dv.is_open and closed_n[0] == 2, "Enter on the last page closes")
	var r2: Dictionary = ex.find("mock.berlin.shelf")
	dv.open("mock.berlin.shelf", r2["cards_new"])
	await wait(0.8)
	if want("find"):
		await shot("find_berlin_image")
	dv.next()
	await wait(0.7)
	if want("card"):
		await shot("card_reich_new")
	dv.close()
	await wait(0.4)
	# ------------------------------------------------------------ chat unlock without a view -> quiet history toast
	ui.hud.show_hud()
	var before: int = ui.hud._toast_box.get_child_count()
	ex.find("mock.karsk.workers")
	await wait(0.5)
	check(ui.hud._toast_box.get_child_count() > before, "card unlocked without a page -> history toast")
	await wait(5.0)
	# ------------------------------------------------------------ journal tabs
	ui.open_journal("discoveries")
	await wait(0.8)
	check(ui.journal.is_open and ui.journal.current_tab == "discoveries", "journal opens on Entdeckungen")
	check(ui.journal._progress.text != "", "journal header shows the exploration progress")
	if want("journal"):
		await shot("journal_discoveries")
	ui.journal._reopen_find("mock.karsk.tea")
	await wait(0.7)
	check(ui.top_modal() == dv and dv.current_type() == "find", "re-open a found entry from the journal")
	dv.close()
	await wait(0.4)
	check(ui.top_modal() == ui.journal, "journal back on top after closing the find")
	ui.journal.show_tab("history")
	await wait(0.6)
	if want("journal"):
		await shot("journal_history")
	ui.journal._read_card("hist.mock.wannsee")
	await wait(0.6)
	check(dv.page_count() == 1 and dv.current_type() == "card", "history card re-readable from the journal")
	dv.close()
	ui.journal.close()
	await wait(0.4)
	# ------------------------------------------------------------ pause + settings
	ui.open_pause()
	await wait(0.6)
	check(ui.pause_menu._explore_box.visible, "pause menu shows the exploration progress")
	if want("pause"):
		await shot("pause_progress")
	ui.open_settings()
	ui.settings_menu.show_tab("display")
	await wait(0.6)
	var found_toggle := false
	for h in ui.settings_menu._rows_box.get_children():
		if h.has_meta("desc") and str(h.get_meta("desc")) == "ui.settings.desc.historical_symbols":
			found_toggle = true
	check(found_toggle, "settings: Historische Hoheitszeichen toggle present")
	for h in ui.settings_menu._rows_box.get_children():
		if h.has_meta("desc") and str(h.get_meta("desc")) == "ui.settings.desc.historical_symbols":
			for cc in h.get_children():
				if cc is CheckBox:
					cc.grab_focus()
	await wait(0.3)
	if want("settings"):
		await shot("settings_display_symbols")
	ui.settings_menu.close()
	ui.pause_menu.close()
	await wait(0.4)
	# ------------------------------------------------------------ 150 % text
	set_text_scale(1.5)
	dv.open("mock.karsk.tea", [])
	await wait(0.9)
	if want("scale"):
		await shot("find_text150")
	var sc0: int = dv._scroll.scroll_vertical
	dv.next()
	await wait(0.6)
	if dv.current_type() == "find":
		check(dv._scroll.scroll_vertical > sc0, "150 %: next() first scrolls a long note")
		if want("scale"):
			await shot("find_text150_scrolled")
	var guard := 0
	while dv.current_type() == "find" and guard < 6:
		guard += 1
		dv.next()
		await wait(0.5)
	await wait(0.4)
	check(dv.current_type() == "card", "150 %: reading on reaches the history card")
	if want("scale"):
		await shot("card_text150")
	var more_seen: bool = dv._more != null and dv._more.modulate.a > 0.5
	var sc_before: int = dv._scroll.scroll_vertical if dv._scroll != null else 0
	dv.next()
	await wait(0.5)
	if more_seen:
		check(dv.current_type() == "card" and dv._scroll.scroll_vertical > sc_before, "150 %: next() scrolls a long card before closing")
		if want("scale"):
			await shot("card_text150_scrolled")
	dv.close()
	ui.open_journal("discoveries")
	await wait(0.7)
	if want("scale"):
		await shot("journal_discoveries_text150")
	ui.journal.show_tab("history")
	await wait(0.6)
	if want("scale"):
		await shot("journal_history_text150")
	ui.journal.close()
	set_text_scale(1.0)
	await wait(0.3)
	# ------------------------------------------------------------ high contrast
	set_hc(true)
	dv.open("mock.karsk.tea", [])
	await wait(0.8)
	if want("hc"):
		await shot("find_high_contrast")
	dv.next()
	await wait(0.7)
	if want("hc"):
		await shot("card_high_contrast")
	dv.close()
	ui.open_journal("history")
	await wait(0.6)
	if want("hc"):
		await shot("journal_history_high_contrast")
	ui.journal.close()
	set_hc(false)
	await wait(0.3)
	# ------------------------------------------------------------ unknown id + cards-only
	dv.open("mock.does.not.exist", [])
	await wait(0.6)
	check(dv.is_open and dv.current_type() == "missing", "unknown id shows a placeholder page (Game's await still ends)")
	if want("missing"):
		await shot("find_missing")
	dv.close()
	dv.open_cards(["hist.mock.katyn", "hist.mock.wannsee"])
	await wait(0.6)
	check(dv.page_count() == 2 and dv.current_type() == "card", "open_cards shows cards only")
	dv.close()
	await wait(0.3)
	print("EXPLORE_UI_PREVIEW %s — %d shots, %d failure(s)" % ["OK" if failures.is_empty() else "FAILED", shots, failures.size()])
	for f in failures:
		print("  - ", f)
	Kit.overrides = {}
	Kit.clear_cache()   # static texture caches would otherwise outlive the scene at exit
	await wait(1.2)     # let the last UI sound finish (a playing stream is reported as "in use" at exit)
	get_tree().quit(0 if failures.is_empty() else 1)
