extends "res://scripts/levels/c3p2_archive/registry_level.gd"
## L_C4_Annex — Konrad's two Chapter-4 places in ONE level file (C4_DESIGN §4.2): the tram loop „Wendeschleife Süd 8“
## at dawn (Story scene L_C4_AnnexA, x 18–822) and the „Nebenstelle Süd“ under it (L_C4_AnnexB, x 846–1902), separated
## by the permanent blocker `shaft_wall`. Art: assets/environments/berlin_annex (tools/pixelgen/env_c4_annex.py).
##
## Builds on the registry's gated art (registry_level.gd: "after" / "until" / "choice" gates with fades, blockers,
## looks) and adds, for two places that never see each other:
## * "scene": "<id>" | [ids] on layers / props / decals / fx / lights / looks (actors: "scene_id") — the entry is only
##   built when the level plays that Story scene. Decided once at load: every C4 scene starts with a level load
##   (C4_DESIGN §1; memories load the level too), so nothing switches in place.
## * "camera_zones": {scene id: [x, y, w, h]} — the camera stays inside the walk area of the scene played (the street
##   never shows underground, the annex never shows the sky); the full world stays in "camera.bounds".
## * its own quiet sound: the registry's porter radio is not here (the ambiences amb_berlin_loop / amb_berlin_annex
##   carry the place).
## Nothing here changes Story state.

const SCENE_SECTIONS := ["layers", "props", "decals", "fx", "lights", "looks"]


## Base-class hook (Level._ready → _merge_explore_hotspots → registry _split_gated): drop the entries of the other
## scene before anything is built.
func _split_gated() -> void:
	_filter_scenes()
	super._split_gated()


func _filter_scenes() -> void:
	for section in SCENE_SECTIONS:
		var arr = manifest.get(section, [])
		if not (arr is Array):
			continue
		var keep: Array = []
		for e in arr:
			if e is Dictionary and (e as Dictionary).has("scene") and not plays((e as Dictionary)["scene"]):
				continue
			keep.append(e)
		manifest[section] = keep
	var actors = manifest.get("actors", [])
	if actors is Array:
		var keep_a: Array = []
		for a in actors:
			if a is Dictionary and (a as Dictionary).has("scene_id") and not plays((a as Dictionary)["scene_id"]):
				continue
			keep_a.append(a)
		manifest["actors"] = keep_a


## True when the level plays Story scene `v` (an id or a list of ids).
func plays(v) -> bool:
	for s in _list(v):
		if str(s) == str(level_id):
			return true
	return false


## The walk area of the scene played (camera_zones); the whole world when the scene has no zone.
func get_camera_bounds() -> Rect2:
	var z = manifest.get("camera_zones", {})
	if z is Dictionary and (z as Dictionary).has(str(level_id)):
		var b = (z as Dictionary)[str(level_id)]
		if b is Array and (b as Array).size() == 4:
			return Rect2(float(b[0]), float(b[1]), float(b[2]), float(b[3]))
	return super.get_camera_bounds()


## No porter's radio, no fire: the place sounds through its ambience only.
func _sound_step(_delta: float) -> void:
	pass


## "loop" | "annex": the look of the scene played (tests, debug).
func look() -> String:
	return look_name if look_name != "" else "loop"
