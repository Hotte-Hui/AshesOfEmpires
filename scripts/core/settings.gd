extends Node
## Player options + input map (rebindable). Persisted in user://settings.cfg.
signal changed(key: String, value)

const PATH := "user://settings.cfg"
const DEFAULTS := {
	"fullscreen": true, "vsync": true,
	"master_volume": 0.9, "music_volume": 0.75, "ambience_volume": 0.85, "sfx_volume": 0.9, "ui_volume": 0.8,
	"text_scale": 1.0,            # 1.0 / 1.25 / 1.5
	"subtitles": true, "dialogue_speed": 1.0,   # 0 = instant
	"high_contrast": false, "reduced_motion": false,
	"pixel_post": 1.0,            # 0..1 strength of palette snap / grain
	"puzzle_hints": 1,            # 0 off, 1 after 2 fails (default), 2 immediate
	"historical_symbols": true,   # real regime insignia (swastika, hammer & sickle) in a critical, historical-
	                              # artistic context (StGB §86 Abs. 4); off = fictional emblems (see Symbols.pick)
	"demo_notice_seen": false,    # §12.13: the demo letter was confirmed once (main menu shows it on first opening)
}
## action -> default keys (physical keycodes) + joypad buttons
const ACTIONS := {
	"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
	"move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
	"run": [KEY_SHIFT], "interact": [KEY_E, KEY_SPACE, KEY_ENTER],
	"cancel": [KEY_ESCAPE, KEY_BACKSPACE], "journal": [KEY_J, KEY_TAB],
	"pause": [KEY_ESCAPE], "skip": [KEY_ESCAPE], "advance": [KEY_SPACE, KEY_ENTER, KEY_E],
	"photo_mode": [KEY_P],
}
const PAD := {
	"interact": [JOY_BUTTON_A], "advance": [JOY_BUTTON_A], "cancel": [JOY_BUTTON_B],
	"journal": [JOY_BUTTON_BACK], "pause": [JOY_BUTTON_START], "skip": [JOY_BUTTON_Y],
	"run": [JOY_BUTTON_LEFT_SHOULDER], "photo_mode": [JOY_BUTTON_RIGHT_STICK],
}

var values: Dictionary = DEFAULTS.duplicate(true)
## The settings file; tests point a fresh instance at a temporary file (never the player's settings.cfg).
var path := PATH
var _runtime_overrides: Dictionary = {}   # forced for this run only (CLI), never written to disk
var _persisted: Dictionary = {}           # on-disk values of overridden keys

func _ready() -> void:
	_build_input_map()
	load_settings()
	# Test/capture override, never persisted: `-- --symbols=0|1` forces the historical-insignia setting for this
	# run only (lets several tools capture both variants without touching the player's settings file).
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--symbols="):
			_runtime_overrides["historical_symbols"] = a.get_slice("=", 1) != "0"
	for k in _runtime_overrides:
		_persisted[k] = values.get(k, DEFAULTS.get(k))
		values[k] = _runtime_overrides[k]
	apply_all()

func _build_input_map() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.25)
		InputMap.action_erase_events(action)
		for k in ACTIONS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)
		for b in PAD.get(action, []):
			var jb := InputEventJoypadButton.new()
			jb.button_index = b
			InputMap.action_add_event(action, jb)
	# Pad A presses the focused button in every menu: Godot's built-in ui_accept has no pad button (Enter, Kp Enter,
	# Space only). Modals that also read "interact"/"advance" (pad A too) treat both as one press.
	var has_a := false
	for e in InputMap.action_get_events("ui_accept"):
		if e is InputEventJoypadButton and (e as InputEventJoypadButton).button_index == JOY_BUTTON_A:
			has_a = true
	if not has_a:
		var ja := InputEventJoypadButton.new()
		ja.button_index = JOY_BUTTON_A
		InputMap.action_add_event("ui_accept", ja)
	var axes := {"move_left": [JOY_AXIS_LEFT_X, -1.0], "move_right": [JOY_AXIS_LEFT_X, 1.0],
		"move_up": [JOY_AXIS_LEFT_Y, -1.0], "move_down": [JOY_AXIS_LEFT_Y, 1.0]}
	for action in axes:
		var jm := InputEventJoypadMotion.new()
		jm.axis = axes[action][0]
		jm.axis_value = axes[action][1]
		InputMap.action_add_event(action, jm)

func rebind(action: String, keycode: Key) -> void:
	for ev in InputMap.action_get_events(action):
		if ev is InputEventKey:
			InputMap.action_erase_event(action, ev)
			break
	var e := InputEventKey.new()
	e.physical_keycode = keycode
	InputMap.action_add_event(action, e)
	values["bind_" + action] = int(keycode)
	save_settings()

func get_value(key: String):
	return values.get(key, DEFAULTS.get(key))

func set_value(key: String, value) -> void:
	values[key] = value
	apply(key)
	save_settings()
	changed.emit(key, value)

func apply_all() -> void:
	for k in values:
		apply(k)

func apply(key: String) -> void:
	match key:
		"fullscreen":
			if DisplayServer.get_name() != "headless":
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if values[key] else DisplayServer.WINDOW_MODE_WINDOWED)
		"vsync":
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if values[key] else DisplayServer.VSYNC_DISABLED)
		_:
			if key.ends_with("_volume"):
				var short := key.trim_suffix("_volume")
				var bus: String = {"master": "Master", "music": "Music", "ambience": "Ambience", "sfx": "SFX", "ui": "UI"}.get(short, short.capitalize())
				var idx := AudioServer.get_bus_index(bus)
				if idx >= 0:
					AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(0.0001, float(values[key]))))
			elif key.begins_with("bind_"):
				pass

func save_settings() -> void:
	var cfg := ConfigFile.new()
	for k in values:
		# a CLI-forced value (e.g. --symbols=0) is never persisted; the player's own value stays on disk
		cfg.set_value("settings", k, _persisted[k] if _runtime_overrides.has(k) and _persisted.has(k) else values[k])
	cfg.save(path)

func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(path) != OK:
		return
	for k in cfg.get_section_keys("settings"):
		values[k] = cfg.get_value("settings", k)
	for k in values.keys():
		if str(k).begins_with("bind_"):
			var action := str(k).trim_prefix("bind_")
			if InputMap.has_action(action):
				rebind(action, values[k])
