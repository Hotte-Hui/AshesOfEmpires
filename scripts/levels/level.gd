class_name Level
extends Node2D
## Base class for every 2D level (TECHNICAL_ARCHITECTURE §3). The .tscn only needs the root with this
## script and its Interactable / NPC children under "Playfield"; backdrop, props, lights, FX, walk limits,
## spawns and hotspot positions come from the art manifest so artists can move things without code.

const LayerStack := preload("res://scripts/levels/layer_stack.gd")

@export var level_id := ""
@export var protagonist := "alexei"
@export_enum("oblique", "side", "3d", "cinematic") var mode := "oblique"
@export_file("*.json") var art_manifest := ""
@export var ambience := ""
@export var music := ""
@export var footstep_surface := "gravel"
@export var floor_y := 300.0          ## side mode: feet line if no walkable polygon is given
@export var grade_preset := ""        ## key in data/grades.json (falls back to manifest palette)
@export var intro_pan := false        ## first visit: establishing pan from intro_from to the player
@export var intro_from := Vector2.ZERO
@export var intro_duration := 6.0

var manifest: Dictionary = {}
var backdrop: Node2D
var playfield: Node2D
var lights: Node2D
var fx: Node2D


func _ready() -> void:
	backdrop = _ensure("Backdrop", LayerStack)
	backdrop.z_index = 0
	playfield = _ensure("Playfield")
	playfield.y_sort_enabled = true
	lights = _ensure("Lights")
	fx = _ensure("FX")
	if art_manifest != "" and FileAccess.file_exists(art_manifest):
		var data = JSON.parse_string(FileAccess.get_file_as_string(art_manifest))
		if typeof(data) == TYPE_DICTIONARY:
			manifest = data
	_merge_explore_hotspots()
	backdrop.build(manifest, art_manifest.get_base_dir(), playfield, lights, fx)
	_build_walk_limits()
	_spawn_actors()
	_place_hotspot_children()
	var cm: String = str(manifest.get("canvas_modulate", ""))
	if cm != "":
		var mod := CanvasModulate.new()
		mod.color = Color(cm)
		add_child(mod)


func _ensure(n: String, script: Script = null) -> Node2D:
	var node := get_node_or_null(n) as Node2D
	if node == null:
		node = Node2D.new()
		node.name = n
		if script:
			node.set_script(script)
		add_child(node)
		move_child(node, 0 if n == "Backdrop" else get_child_count() - 1)
	elif script and node.get_script() == null:
		node.set_script(script)
	return node


func _build_walk_limits() -> void:
	var poly: Array = manifest.get("walkable", [])
	if poly.size() < 3:
		return
	var body := StaticBody2D.new()
	body.name = "WalkLimits"
	var cp := CollisionPolygon2D.new()
	cp.build_mode = CollisionPolygon2D.BUILD_SEGMENTS
	var pts := PackedVector2Array()
	for q in poly:
		pts.append(LayerStack._v2(q))
	pts.append(pts[0])
	cp.polygon = pts
	body.add_child(cp)
	add_child(body)


## §12: exploration hotspots live in a sibling file owned by the content author, so art (scene.json) and
## exploration content can change independently: <manifest dir>/explore_hotspots.json =
## {"hotspots": {"name": [x, y]}, "spawns": {...}}. Names must not collide with scene.json (scene.json wins).
func _merge_explore_hotspots() -> void:
	if art_manifest == "":
		return
	var path := art_manifest.get_base_dir() + "/explore_hotspots.json"
	if not FileAccess.file_exists(path):
		return
	var extra = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(extra) != TYPE_DICTIONARY:
		push_warning("Level: cannot parse " + path)
		return
	for section in ["hotspots", "spawns"]:
		var dst: Dictionary = manifest.get(section, {})
		var src = extra.get(section, {})
		if src is Dictionary:
			for k in src:
				if not dst.has(k):
					dst[k] = src[k]
		manifest[section] = dst


## §12: interactive ambient actors declared by the art manifest (crows that fly off, a cat, a passing tram…):
## "actors": [{"scene": "res://…tscn", "pos": [x, y], "props": {property: value}}] → instanced into the
## y-sorted Playfield. Each actor scene is self-contained (its own script/animation).
func _spawn_actors() -> void:
	for a in manifest.get("actors", []):
		if not (a is Dictionary) or not ResourceLoader.exists(str(a.get("scene", ""))):
			continue
		var node: Node = load(str(a["scene"])).instantiate()
		if node is Node2D:
			(node as Node2D).position = LayerStack._v2(a.get("pos", [0, 0]))
		var props = a.get("props", {})
		if props is Dictionary:
			for k in props:
				node.set(k, props[k])
		playfield.add_child(node)


## Interactables / NPCs with a `hotspot_id` snap to the manifest's hotspot coordinates.
func _place_hotspot_children() -> void:
	var hs: Dictionary = manifest.get("hotspots", {})
	for c in playfield.get_children():
		var hid = c.get("hotspot_id")
		if hid != null and str(hid) != "" and hs.has(str(hid)):
			c.position = LayerStack._v2(hs[str(hid)]) + (c.get("hotspot_offset") if c.get("hotspot_offset") != null else Vector2.ZERO)


func get_spawn(spawn_name: String) -> Vector2:
	var sp: Dictionary = manifest.get("spawns", {})
	if sp.has(spawn_name):
		return LayerStack._v2(sp[spawn_name])
	if not sp.is_empty():
		return LayerStack._v2(sp.values()[0])
	return Vector2(120, floor_y)


func get_hotspot(id: String) -> Vector2:
	var hs: Dictionary = manifest.get("hotspots", {})
	return LayerStack._v2(hs[id]) if hs.has(id) else Vector2.ZERO


func get_camera_bounds() -> Rect2:
	var cam: Dictionary = manifest.get("camera", {})
	var b: Array = cam.get("bounds", [])
	if b.size() == 4:   # [x, y, width, height] (Rect2 convention)
		return Rect2(float(b[0]), float(b[1]), float(b[2]), float(b[3]))
	var ws: Array = manifest.get("world_size", [640, 360])
	return Rect2(0, 0, float(ws[0]), float(ws[1]))


func get_palette_name() -> String:
	return str(manifest.get("palette", ""))
