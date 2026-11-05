extends SceneTree
## Headless probe for the skyline integration: do relative "../" layer paths resolve through ResourceLoader
## (needed for exported builds, where only imported resources are packed) and does Symbols.pick find mid_hist?
## godot --headless --path . --script res://tests/visual/skyline/path_probe.gd


func _init() -> void:
	var paths := [
		"res://assets/environments/karsk_skyline/mid.png",
		"res://assets/environments/karsk_railyard/../karsk_skyline/mid.png",
		"res://tests/visual/skyline/../../../assets/environments/karsk_skyline/mid.png",
		"res://tests/visual/skyline/../../../assets/environments/karsk_railyard/sky.png",
		"res://assets/environments/karsk_railyard/../karsk_skyline/mid_hist.png",
	]
	for p in paths:
		var t = load(p) if ResourceLoader.exists(p) else null
		print("PROBE exists=%s loaded=%s simplified=%s  %s" % [ResourceLoader.exists(p), t != null, p.simplify_path(), p])
	quit(0)
