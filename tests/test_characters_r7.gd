extends RefCounted
## Characters, round 7 (owner: characters; documentation/asset_manifest_parts/characters_r7.md, portraits_r7.md):
##  * the Chapter-3 cast is on the round-2 rig: 8-frame idle / talk, blink / glance / gesture variants, front idle
##    + front talk and a walk row for every one of the seven, cell / origin contract unchanged
##  * every NPC with a front view has talk_front, the protagonists also talk_back; existing rows keep their index
##  * front / back walks keep one foot on the origin row in every frame (the figure no longer floats mid-stride)
##  * every dialogue speaker (incl. the Chapter-3 seven) has a living portrait: portrait_anim.png grid + anim block
##  * rig: view_hint maps "*_side" requests to the facing view, walking turns show walk_front and survive row
##    changes, turning back mid-turn cancels; player: soft turns, faces the camera for a target below it
##  * front-on NPCs talk front-on; NPC talk release accepts any talk row

const Kit := preload("res://tests/support/test_kit.gd")
const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const NPC := preload("res://scripts/actors/npc.gd")
const CHAR := "res://assets/characters/"
const C3 := ["elena", "border_officer", "conductor", "voronova", "kessler", "typist", "journalist"]
const R2_NPC := ["irina", "emil", "worker_a", "babushka", "child_a", "berlin_father", "berlin_mother", "berlin_child",
	"clerk", "guard", "librarian", "porter", "vendor", "worker_b"]
const PROTAG := ["alexei", "konrad"]
const SPEAKERS := ["alexei", "konrad", "irina", "emil", "vendor", "worker_a", "babushka", "librarian", "porter",
	"photographer", "elena", "border_officer", "conductor", "voronova", "kessler", "typist", "journalist"]
## the 9 contract rows of TECHNICAL_ARCHITECTURE §4 keep their row index on the protagonists' sheets
const CONTRACT := {"idle_side": 0, "walk_side": 1, "idle_front": 2, "walk_front": 3, "idle_back": 4, "walk_back": 5,
	"inspect_side": 6, "interact_side": 7, "talk_side": 8}

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("c3_cast_on_round2_rig", _c3_rows)
	kit.run_case("talk_front_rows", _talk_front)
	kit.run_case("front_back_walk_grounded", _walk_grounded)
	kit.run_case("living_portraits", _portraits)
	kit.run_case("rig_view_hint_and_turns", _rig)
	kit.run_case("player_soft_turn_and_view", _player)
	kit.run_case("npc_front_talk", _npc_front)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _sheet(id: String) -> Dictionary:
	var d = _json(CHAR + id + "/sheet.json")
	return d if d is Dictionary else {}


func _c3_rows() -> bool:
	for id in C3:
		var s := _sheet(id)
		if not kit.ok(not s.is_empty(), "%s: sheet.json" % id):
			continue
		kit.eq(s.get("cell"), [32.0, 56.0], "%s: cell" % id)
		kit.eq(s.get("origin"), [16.0, 54.0], "%s: origin" % id)
		var an: Dictionary = s.get("anims", {})
		for a in ["idle_side", "walk_side", "idle_front", "talk_side", "blink_side", "look_side", "gesture_side",
				"blink_front", "talk_front"]:
			kit.ok(an.has(a), "%s: row %s" % [id, a])
		kit.eq(int(an.get("idle_side", {}).get("frames", 0)), 8, "%s: idle_side frames" % id)
		kit.eq(int(an.get("talk_side", {}).get("frames", 0)), 8, "%s: talk_side frames" % id)
		kit.eq(an.get("idle_side", {}).get("variants", []), ["blink_side", "blink_side", "look_side", "gesture_side"],
			"%s: idle variants" % id)
		kit.ok(float(s.get("ground_speed", {}).get("walk_side", 0.0)) > 0.0, "%s: walk ground speed" % id)
		kit.ok(FileAccess.file_exists(CHAR + id + "/sheet_n.png"), "%s: normal map" % id)
	return true


func _talk_front() -> bool:
	for id in R2_NPC + C3 + PROTAG:
		var an: Dictionary = _sheet(id).get("anims", {})
		if an.has("idle_front"):
			kit.ok(an.has("talk_front"), "%s: talk_front next to idle_front" % id)
			kit.eq(int(an.get("talk_front", {}).get("frames", 0)), 8, "%s: talk_front frames" % id)
	for id in PROTAG:
		var an: Dictionary = _sheet(id).get("anims", {})
		kit.ok(an.has("talk_back"), "%s: talk_back" % id)
		for a in CONTRACT:
			kit.eq(int(an.get(a, {}).get("row", -1)), CONTRACT[a], "%s: contract row %s keeps its index" % [id, a])
	return true


## One foot on the origin row (54) in every front / back walk frame (alpha of the cell's bottom rows).
func _walk_grounded() -> bool:
	for id in PROTAG:
		var s := _sheet(id)
		var img := Image.load_from_file(ProjectSettings.globalize_path(CHAR + id + "/sheet.png"))
		if not kit.ok(img != null and not img.is_empty(), "%s: sheet.png loads" % id):
			continue
		for a in ["walk_front", "walk_back"]:
			var r := int(s["anims"][a]["row"])
			for f in int(s["anims"][a]["frames"]):
				var lowest := -1
				for y in range(55, -1, -1):
					for x in 32:
						if img.get_pixel(f * 32 + x, r * 56 + y).a > 0.5:
							lowest = y
							break
					if lowest >= 0:
						break
				kit.eq(lowest, 54, "%s %s[%d]: lowest opaque row (feet on the origin)" % [id, a, f])
	return true


func _portraits() -> bool:
	for id in SPEAKERS:
		var p = _json(CHAR + id + "/portrait.json")
		if not kit.ok(p is Dictionary, "%s: portrait.json" % id):
			continue
		kit.eq(p.get("size"), [112.0, 112.0], "%s: portrait size" % id)
		kit.eq(p.get("expressions"), ["neutral", "concerned", "determined", "surprised"], "%s: expressions" % id)
		var anim: Dictionary = p.get("anim", {}) if p.get("anim") is Dictionary else {}
		kit.eq(str(anim.get("file", "")), "portrait_anim.png", "%s: living portrait (anim block)" % id)
		var img := Image.load_from_file(ProjectSettings.globalize_path(CHAR + id + "/portrait_anim.png"))
		if kit.ok(img != null and not img.is_empty(), "%s: portrait_anim.png loads" % id):
			kit.eq([img.get_width(), img.get_height()], [448, 112 * (anim.get("rows", []) as Array).size()],
				"%s: portrait grid size" % id)
			# the talk row differs from the rest row (the mouth opens) and the blink row too (the eyes close)
			kit.ok(_differs(img, 0, 2), "%s: talk_open differs from rest" % id)
			kit.ok(_differs(img, 0, 3), "%s: blink differs from rest" % id)
	return true


static func _differs(img: Image, row_a: int, row_b: int) -> bool:
	var n := 0
	for y in range(20, 100):
		for x in range(20, 100):
			if img.get_pixel(x, row_a * 112 + y) != img.get_pixel(x, row_b * 112 + y):
				n += 1
	return n >= 6


func _rig() -> bool:
	var r: Node2D = kit.mount(SpriteRig.new())
	kit.ok(r.load_character("alexei"), "alexei loads")
	r.variants_enabled = false
	r.view_hint = "front"
	r.play("talk_side")
	kit.eq(r.anim, "talk_front", "view_hint front: talk_side -> talk_front")
	r.play("idle_side")
	kit.eq(r.anim, "idle_front", "view_hint front: idle_side -> idle_front")
	r.view_hint = "back"
	r.play("talk_side")
	kit.eq(r.anim, "talk_back", "view_hint back: talk_side -> talk_back")
	r.view_hint = ""
	r.play("walk_side")
	var cols: int = r.sprite.hframes
	var wf := int(r.sheet["anims"]["walk_front"]["row"])
	kit.ok(r.turn_to(true, 0.1, "walk_front"), "walking turn starts")
	kit.eq(int(r.sprite.frame / cols), wf, "walking turn shows walk_front")
	r.play("idle_side")
	kit.ok(r.is_turning() and int(r.sprite.frame / cols) == wf, "row change keeps the turn frame")
	kit.ok(r.turn_to(false), "turning back accepted")
	kit.ok(not r.is_turning() and not r.is_flipped(), "turning back mid-turn cancels")
	kit.ok(r.turn_to(true), "turn again")
	for i in 6:
		r._process(0.05)
	kit.ok(r.is_flipped() and not r.is_turning(), "turn completes")
	# a sheet without talk_back falls back to idle_back, not to the side view
	var n: Node2D = kit.mount(SpriteRig.new())
	n.load_character("irina")
	n.play("talk_back")
	kit.eq(n.anim, "idle_side", "irina has no back rows: talk_back resolves via idle_back to idle_side")
	return true


func _player() -> bool:
	var pl: Node2D = load("res://scripts/actors/player.gd").new()
	pl.setup("alexei", "oblique", Vector2(200, 300), "gravel")
	kit.mount(pl)
	pl.face(-1.0)
	kit.ok(pl.rig.is_turning() and not pl.rig.is_flipped(), "player: soft turn (front frame first)")
	for i in 6:
		pl.rig._process(0.05)
	kit.ok(pl.rig.is_flipped(), "player: mirrored after the turn")
	kit.eq(pl.get_facing(), -1.0, "player: facing left")
	pl.face(1.0, false)
	kit.ok(not pl.rig.is_flipped() and not pl.rig.is_turning(), "player: instant face on request")
	pl.face_point(Vector2(203, 330))
	kit.eq(pl.get_view(), "front", "player: faces the camera for a point below")
	pl.rig.play("talk_side")
	kit.eq(pl.rig.anim, "talk_front", "player: talks front-on while facing the camera")
	pl.face_point(Vector2(196, 270))
	kit.eq(pl.get_view(), "back", "player: faces away for a point above")
	pl.face_point(Vector2(160, 304))
	kit.eq(pl.get_view(), "side", "player: sideways for a point beside it")
	kit.ok(pl.rig.is_turning() or pl.rig.is_flipped(), "player: turns towards a point on the left")
	var side_pl: Node2D = load("res://scripts/actors/player.gd").new()
	side_pl.setup("konrad", "side", Vector2(200, 300), "parquet")
	kit.mount(side_pl)
	side_pl.face_point(Vector2(202, 340))
	kit.eq(side_pl.get_view(), "side", "side levels never switch to the front view")
	return true


func _npc_front() -> bool:
	var n: Node2D = NPC.new()
	n.char_id = "kessler"
	n.idle_anim = "idle_front"
	n.turn_to_talk = false
	n.look_at_player = false
	kit.mount(n)
	kit.eq(n.rig.anim, "idle_front", "front-on idle")
	n.set_talking(true)
	kit.eq(n.rig.anim, "talk_front", "front-on npc talks with talk_front")
	n.set_talking(false)
	for i in 30:
		n.rig._process(0.05)
		n._process(0.05)
	kit.eq(n.rig.anim, "idle_front", "settles back into idle_front")
	return true
