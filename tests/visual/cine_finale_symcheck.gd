extends SceneTree
## Headless check (owner: trans-finale): every insignia layer of the finale exists as a neutral file and a
## _hist file, both import, and they really differ (the switch of TECHNICAL_ARCHITECTURE §12.4 has an effect).
## Run: godot --headless --path . --script res://tests/visual/cine_finale_symcheck.gd   (exit 1 on failure)

const BASE := "res://assets/cinematics/finale/"


func _init() -> void:
	var fails := 0
	var data = JSON.parse_string(FileAccess.get_file_as_string(BASE + "finale.json"))
	var pairs := []
	for sid in data["sets"]:
		for nd in data["sets"][sid]["nodes"]:
			if nd.has("hist"):
				pairs.append([str(nd.get("file", "")), str(nd["hist"])])
			if nd.has("hist_atlas"):
				pairs.append([str(nd.get("atlas", "")), str(nd["hist_atlas"])])
	for p in pairs:
		var a: Texture2D = load(BASE + p[0])
		var b: Texture2D = load(BASE + p[1])
		if a == null or b == null:
			print("FAIL missing ", p)
			fails += 1
			continue
		var ia := a.get_image()
		var ib := b.get_image()
		var diff := 0
		if ia.get_size() == ib.get_size():
			for y in ia.get_height():
				for x in ia.get_width():
					if not ia.get_pixel(x, y).is_equal_approx(ib.get_pixel(x, y)):
						diff += 1
		print("%s  vs  %s : %s, %d px differ  (%s / %s)" % [p[0], p[1], "same size" if ia.get_size() == ib.get_size() else "SIZE MISMATCH",
			diff, a.resource_path, b.resource_path])
		if diff == 0 or ia.get_size() != ib.get_size():
			fails += 1
	print("SYMCHECK pairs=%d fails=%d" % [pairs.size(), fails])
	quit(1 if fails > 0 else 0)
