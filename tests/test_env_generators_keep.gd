extends RefCounted
## Round 10 (NEXT_STEPS §1 „generator hazard“; owner: polish). The env folders are shared: walkers_r8.py writes the
## walker rigs into walkers/, env_veltrava_station_thaw.py the station's thaw/, the feel passes added "actors" entries
## (AmbientWalkers, StationThaw) to scene.json. env_veltrava_hall.py, env_veltrava_station.py and env_c3p2_quay.py used
## to delete every PNG of their folder and to write scene.json from scratch -- a re-run dropped all of that. Checked:
##  * the sources: no PNG sweep by file extension any more; the own-record removal, the scene merge, the byte-stable
##    writer and the provenance merge of tools/pixelgen/env_keep.py are used (its rules:
##    `py -3 -P tools/pixelgen/env_keep.py --selftest`; the byte-identical re-run proof:
##    documentation/asset_manifest_parts/polish_r10.md)
##  * the folders: every hand-added actor names a real scene (and walker data whose sheets and rigs exist), the
##    station's thaw art exists, every provenance row names a file that exists, and no generator's own row claims
##    a file of walkers/ or thaw/ (its next run would delete it).
## Round 10 lead pass: env_berlin.py (berlin_archive, the round-8 AmbientWalkers actor + walkers/) — it deletes nothing
## and keeps no provenance.json, so it only needs the scene merge and the byte-stable writer (MERGE_ONLY); its re-run
## in a scratch copy is byte-identical (documentation/asset_manifest_parts/polish_r10.md).

const Kit := preload("res://tests/support/test_kit.gd")
const GENS := {"env_veltrava_hall": "veltrava_hall", "env_veltrava_station": "veltrava_station",
	"env_c3p2_quay": "veltrava_quay"}
## generators that never delete a file (no own-record removal needed) but rewrite a shared scene.json
const MERGE_ONLY := {"env_berlin": "berlin_archive"}
## provenance "generator" prefixes of each generator's own rows (env_keep FAMILY)
const FAMILY := {"veltrava_hall": ["tools/pixelgen/env_veltrava_hall"],
	"veltrava_station": ["tools/pixelgen/env_veltrava_station.py", "tools/pixelgen/env_veltrava_station_life.py"],
	"veltrava_quay": ["tools/pixelgen/env_c3p2_quay"]}
const FOREIGN_DIRS := ["walkers/", "thaw/"]
const THAW := ["car3_peephole", "car3_thaw"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("generators_never_sweep_the_shared_folder", _sources)
	kit.run_case("hand_added_actors_and_rigs_are_there", _actors)
	kit.run_case("provenance_rows_real_and_own_rows_in_place", _provenance)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _sources() -> bool:
	var keep := FileAccess.get_file_as_string("res://tools/pixelgen/env_keep.py")
	kit.ok(keep.contains("SHARED_LISTS = {'actors': 'scene'}"), "env_keep.py: actors entries are identified by their scene")
	kit.ok(keep.contains("def selftest"), "env_keep.py carries its selftest")
	var sweep := RegEx.create_from_string("endswith\\('\\.png'\\)\\)?:\\s*\\n\\s*os\\.remove\\(")
	for g in GENS:
		var src := FileAccess.get_file_as_string("res://tools/pixelgen/%s.py" % g)
		if not kit.ok(src != "", "%s.py readable" % g):
			continue
		kit.ok(sweep.search(src) == null, "%s: no PNG is deleted by its extension any more" % g)
		for call in ["import env_keep as KEEP", "KEEP.remove_own_pngs(", "KEEP.merge_scene(", "KEEP.write_json(sj,",
				"KEEP.merge_rows("]:
			kit.ok(src.contains(call), "%s uses %s" % [g, call])
	for g in MERGE_ONLY:
		var src := FileAccess.get_file_as_string("res://tools/pixelgen/%s.py" % g)
		if not kit.ok(src != "", "%s.py readable" % g):
			continue
		for bad in ["os.remove(", "rmtree(", "json.dump(scene"]:
			kit.ok(not src.contains(bad), "%s: no %s (it deletes nothing, scene.json goes through env_keep)" % [g, bad])
		for call in ["import env_keep as KEEP", "KEEP.merge_scene(", "KEEP.write_json(sj,", "KEEP.lf_json("]:
			kit.ok(src.contains(call), "%s uses %s" % [g, call])
	return true


func _actors() -> bool:
	var walkers_seen := 0
	var folders: Dictionary = GENS.duplicate()
	folders.merge(MERGE_ONLY)
	for g in folders:
		var env: String = "res://assets/environments/%s/" % folders[g]
		var scene = _json(env + "scene.json")
		if not kit.ok(scene is Dictionary, "%s scene.json parses" % folders[g]):
			continue
		var scenes: Array = []
		for a in scene.get("actors", []):
			var path := str((a as Dictionary).get("scene", ""))
			scenes.append(path.get_file())
			kit.ok(ResourceLoader.exists(path), "%s: actor scene %s exists" % [folders[g], path])
			var data := str((a as Dictionary).get("props", {}).get("data", ""))
			if data == "":
				continue
			var w = _json(data)
			if not kit.ok(w is Dictionary, "%s: walker data %s parses" % [folders[g], data]):
				continue
			for wk in w.get("walkers", []):
				walkers_seen += 1
				var sheet := str((wk as Dictionary).get("sheet", ""))
				if sheet != "":
					kit.ok(FileAccess.file_exists(env + sheet), "%s: walker sheet %s" % [folders[g], sheet])
				var rig := str((wk as Dictionary).get("rig", ""))
				if kit.ok(rig != "" and FileAccess.file_exists(env + rig), "%s: walker rig %s" % [folders[g], rig]):
					var base := rig.get_basename()
					kit.ok(FileAccess.file_exists(env + base + ".png") and FileAccess.file_exists(env + base + "_n.png"),
						"%s: the rig's sheet and normal map %s(.png / _n.png)" % [folders[g], base])
		kit.ok("AmbientWalkers.tscn" in scenes, "%s: the ambient walkers' actor is in scene.json" % folders[g])
	kit.ok(walkers_seen >= 13, "walkers checked in the four folders (%d)" % walkers_seen)
	var st = _json("res://assets/environments/veltrava_station/scene.json")
	var names: Array = []
	for a in (st.get("actors", []) if st is Dictionary else []):
		names.append(str((a as Dictionary).get("scene", "")).get_file())
	kit.ok("StationThaw.tscn" in names, "station: the thaw actor is in scene.json")
	for t in THAW:
		for suf in ["", "_n", "_e"]:
			kit.ok(FileAccess.file_exists("res://assets/environments/veltrava_station/thaw/%s%s.png" % [t, suf]),
				"station: thaw/%s%s.png" % [t, suf])
	return true


func _provenance() -> bool:
	for g in GENS:
		var env: String = GENS[g]
		var prov = _json("res://assets/environments/%s/provenance.json" % env)
		if not kit.ok(prov is Dictionary and (prov.get("files", []) as Array).size() > 10, "%s: provenance.json lists its files" % env):
			continue
		var missing: Array = []
		var claims: Array = []
		var own := 0
		for r in prov["files"]:
			var path := str((r as Dictionary).get("path", ""))
			if not FileAccess.file_exists("res://" + path):
				missing.append(path)
			var gen := str((r as Dictionary).get("generator", ""))
			var mine := false
			for f in FAMILY[env]:
				mine = mine or gen.begins_with(str(f))
			if mine:
				own += 1
				for d in FOREIGN_DIRS:
					if path.contains("/%s/%s" % [env, d]):
						claims.append(path)
		kit.eq(missing, [], "%s: every provenance row names an existing file" % env)
		kit.eq(claims, [], "%s: the generator never records walkers/ or thaw/ as its own" % env)
		kit.ok(own > 10, "%s: the generator's own rows are its removal record (%d)" % [env, own])
	return true
