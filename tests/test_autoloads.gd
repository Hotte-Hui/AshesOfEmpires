extends RefCounted
## Integration smoke test of the REAL autoloads (project.godot): Story, Saves and Loc are registered with
## the expected scripts, initialise without errors and expose what scripts/core/game.gd uses
## (Object.get("current_scene"), current_dialogue_line without "error", Saves.get("last_loaded_extra") ...).
## All other tests instantiate the scripts directly; this one only reads the live autoloads, it never saves.

const Kit := preload("res://tests/support/test_kit.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("project_registers_autoloads", _registered)
	kit.run_case("live_autoloads_ready", _live)
	kit.run_case("game_gd_access_patterns", _game_patterns)
	kit.cleanup()
	return kit.failures


func _registered() -> bool:
	var cfg := ConfigFile.new()
	kit.eq(cfg.load("res://project.godot"), OK, "project.godot readable")
	kit.eq(cfg.get_value("autoload", "Story", ""), "*res://scripts/story/story_engine.gd", "Story autoload")
	kit.eq(cfg.get_value("autoload", "Saves", ""), "*res://scripts/core/save_system.gd", "Saves autoload")
	kit.eq(cfg.get_value("autoload", "Loc", ""), "*res://scripts/story/loc.gd", "Loc autoload")
	var order: PackedStringArray = cfg.get_section_keys("autoload")
	kit.ok(order.find("Story") < order.find("Saves"), "Story is created before Saves")
	return true


func _live() -> bool:
	var root: Window = (Engine.get_main_loop() as SceneTree).root
	var story := root.get_node_or_null("Story")
	var saves := root.get_node_or_null("Saves")
	var loc := root.get_node_or_null("Loc")
	if story == null or saves == null or loc == null:
		print("      note: autoloads not instantiated in this run mode — live checks skipped")
		return true
	kit.eq(story.data_ok(), true, "Story autoload loaded data/v3")
	kit.ok(story.has_signal("objective_completed") and story.has_signal("state_replaced"), "Story signals")
	kit.eq(saves.base_dir, "user://saves", "Saves default directory")
	kit.ok(saves.get("story") == story, "Saves resolved the Story autoload")
	kit.ok(story.state_replaced.is_connected(saves._on_story_replaced), "Saves listens to state_replaced")
	kit.eq(loc.t("sys.journal.title"), "Tagebuch", "Loc autoload merged de_system.json")
	return true


func _game_patterns() -> bool:
	var g := kit.story()
	kit.eq(g.get("current_scene"), "L_A1_Railyard", "Story.get(\"current_scene\") (game.gd _story_scene)")
	kit.eq(g.get("active_character"), "alexei", "Story.get(\"active_character\")")
	for m in ["new_game", "is_available", "objective_state", "inspect", "start_dialogue", "current_dialogue_line",
			"advance_dialogue", "solve_puzzle", "puzzle_hint_available", "puzzle_attempts", "choose", "pending_cinematics",
			"consume_cinematic", "finale", "flag", "has_item", "inventory", "choice_history", "save_json", "load_json",
			"journal", "item_def", "snapshot", "available", "relationship", "relationships"]:
		kit.ok(g.has_method(m), "Story.%s exists" % m)
	g.start_dialogue("a1_talk_irina")
	var line: Dictionary = g.current_dialogue_line("a1_talk_irina")
	kit.ok(not line.is_empty() and not line.has("error"), "valid line has no 'error' key (game.gd loop)")
	var s := kit.saves()
	for m in ["save", "load", "list_slots", "autosave", "has_any", "delete", "quicksave", "quickload", "latest"]:
		kit.ok(s.has_method(m), "Saves.%s exists" % m)
	kit.ok(s.has_signal("saved") and s.has_signal("loaded"), "Saves signals")
	kit.eq(s.get("last_loaded_extra"), {}, "Saves.get(\"last_loaded_extra\") (game.gd _on_loaded_slot)")
	return true
