extends Node2D
## The data desk of Nebenstelle Süd („Datenstelle“, L_C4_Annex scene D): a 1964 data-processing desk between the
## machine room and the household index — tape cabinet, vector display („Sichtgerät“), teleprinter, card reader —
## and the duty roster on its clipboard beside the second ladder. Instanced by the level from the "actors" list of
## assets/environments/berlin_annex/scene.json ("scene_id": L_C4_AnnexB; the entry and the art come from
## tools/pixelgen/gen_annex_terminal.py, which keeps the folder's other content: env_keep). Self-contained on purpose:
## the art (cut from a bake of the hall, so it carries the room's light), its small life (cursor, lamps, reels) and
## the two exploration spots of the side task „Planspiel Abgang“ (§12.9) live here, so a re-run of the annex
## generator keeps all of it and the level file needs no node.
##   Spot_Desk    exp_terminal         chain term_desk -> term_files (mini-game DataTerminal) -> planspiel (mini-game
##                                     PlanspielAbgang)
##   Spot_Roster  exp_terminal_roster  term_roster (the operator number)
## Both are lever_spot.gd nodes like every Chapter-4 find: open after c4b_inspect_crates, and in the memory of
## L_C4_AnnexB. Positions: terminal/layout.json (world px). Never touches Story.

const TexelLightLib := preload("res://scripts/render/texel_light.gd")
const LayerStackLib := preload("res://scripts/levels/layer_stack.gd")
const SPOT := preload("res://scripts/ui/minigames/lever_spot.gd")
const DIR := "res://assets/environments/berlin_annex/terminal/"
const CHAIN := ["berlin.annex.term_desk", "berlin.annex.term_files", "berlin.annex.planspiel"]
const ROSTER := "berlin.annex.term_roster"
const OPEN_AFTER := "c4b_inspect_crates"
const MEMORY_SCENE := "L_C4_AnnexB"
const GREEN := Color("86a28a")
const GREEN_HOT := Color("c4d8c4")
const AMBER := Color("e6b44c")

var layout := {}
var desk_spot: Node2D
var roster_spot: Node2D
var _life: Node2D
var _t := 0.0
var _phase := -1


class Life extends Node2D:
	var desk: Node

	func _draw() -> void:
		desk.call("draw_life", self)


func _ready() -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(DIR + "layout.json")) if FileAccess.file_exists(DIR + "layout.json") else null
	layout = data if data is Dictionary else {}
	for part in ["desk", "roster"]:
		_add_piece(part)
	var life := Life.new()
	life.desk = self
	life.name = "Life"
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	life.material = mat
	add_child(life)
	_life = life
	var spots: Dictionary = layout.get("spots", {})
	desk_spot = _add_spot("Spot_Desk", "exp_terminal", CHAIN[0], PackedStringArray(CHAIN), 22.0, spots)
	roster_spot = _add_spot("Spot_Roster", "exp_terminal_roster", ROSTER, PackedStringArray(), 20.0, spots)


static func _v2(v, fallback := Vector2.ZERO) -> Vector2:
	return Vector2(float(v[0]), float(v[1])) if v is Array and (v as Array).size() >= 2 else fallback


## A cut-out of the baked hall as a lit sprite (and its emission glow), at its world position.
func _add_piece(part: String) -> void:
	var info: Dictionary = layout.get(part, {})
	if info.is_empty():
		return
	var path := DIR + str(info.get("file", part + ".png"))
	var tex := LayerStackLib.canvas_tex(path, true)
	if tex == null:
		return
	var at := _v2(info.get("pos"))
	var spr := Sprite2D.new()
	spr.name = part.capitalize()
	spr.texture = tex
	spr.centered = false
	spr.position = at - position
	add_child(spr)
	TexelLightLib.apply(spr, at)
	var e := LayerStackLib.tex(LayerStackLib.map_path(path, "_e"))
	if e != null:
		var glow := Sprite2D.new()
		glow.name = part.capitalize() + "Glow"
		glow.texture = e
		glow.centered = false
		glow.position = spr.position
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		glow.material = mat
		glow.modulate = Color(1, 1, 1, 0.3)
		add_child(glow)


func _add_spot(node_name: String, hotspot: String, id: String, chain: PackedStringArray, r: float, spots: Dictionary) -> Node2D:
	var n: Node2D = SPOT.new()
	n.name = node_name
	n.set("kind", "discover")
	n.set("hotspot_id", hotspot)
	n.set("explore_id", id)
	n.set("explore_chain", chain)
	n.set("radius", r)
	n.set("once", true)
	n.set("after_objective", OPEN_AFTER)
	n.set("memory_scenes", PackedStringArray([MEMORY_SCENE]))
	n.position = _v2(spots.get(hotspot), position + Vector2(0, 12)) - position
	add_child(n)
	return n


## 0 untouched · 1 logged in and released (the tape of the program runs) · 2 the run is over.
func stage() -> int:
	var ex := get_node_or_null("/root/Explore")
	if ex == null or not ex.has_method("is_found"):
		return 0
	if ex.is_found(CHAIN[2]):
		return 2
	return 1 if ex.is_found(CHAIN[1]) else 0


func _process(delta: float) -> void:
	_t += delta
	var st := get_node_or_null("/root/Settings")
	var calm: bool = st != null and st.has_method("get_value") and bool(st.get_value("reduced_motion"))
	var ph := 0 if calm else int(_t * 2.5) % 4
	if ph != _phase:
		_phase = ph
		if _life != null:
			_life.queue_redraw()


## The desk's small life, in world px relative to this node: the cursor on the round tube, the lamps of the tape
## cabinet, the reels (they only turn once the program has been released).
func draw_life(ci: CanvasItem) -> void:
	var life: Dictionary = layout.get("life", {})
	if life.is_empty():
		return
	var st := stage()
	var cur := _v2(life.get("cursor")) - position
	if _phase % 2 == 0:
		ci.draw_rect(Rect2(cur, Vector2(2, 1)), GREEN_HOT)
	if st >= 1:
		var line := _v2(life.get("trace")) - position
		ci.draw_rect(Rect2(line, Vector2(5, 1)), GREEN)
		ci.draw_rect(Rect2(line + Vector2(1, 2), Vector2(3, 1)), GREEN)
	var lamp := _v2(life.get("lamp")) - position
	ci.draw_rect(Rect2(lamp, Vector2(1, 1)), AMBER if (st == 1 and _phase < 2) else GREEN)
	if st == 1:
		for key in ["reel_a", "reel_b"]:
			var c := _v2(life.get(key)) - position
			var arm: Vector2 = [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)][_phase]
			ci.draw_rect(Rect2(c + arm, Vector2(1, 1)), GREEN_HOT)
