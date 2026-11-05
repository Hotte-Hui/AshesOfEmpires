extends Node
## Main scene root. Owns the pixel world viewport, the HD UI layer and the overlay layer.
## All game flow lives in the Game autoload (scripts/core/game.gd).
## Render paths (scripts/render/pixel_view.gd): 2D content renders in the high-resolution path (World, raw,
## transparent -> Graded, post stage with the grade material -> Display); while a 3D level (Node3D root, e.g.
## L_M1_HallReveal) is inside LevelRoot the world viewport switches to the 642x362 low-res path (post inside
## World as before) so the 3D pixel post keeps its 1 px = 1 world px contract.
## `grade` stays the node whose ShaderMaterial Game._apply_grade() writes; the same material drives both
## post stages.

@onready var world: SubViewport = $World
@onready var level_root: Node = $World/LevelRoot
@onready var camera: Camera2D = $World/Camera
@onready var grade: ColorRect = $World/Post/Grade
@onready var view: Control = $WorldView
@onready var ui_layer: CanvasLayer = $UI
@onready var overlay: CanvasLayer = $Overlay
@onready var graded: SubViewport = $Graded          ## hi-res path: post stage (World texture -> grade)


func _ready() -> void:
	view.setup(world, graded)
	level_root.child_entered_tree.connect(_on_world_child_entered)
	level_root.child_exiting_tree.connect(_on_world_child_exiting)
	Game.register_main(self)


## Emitted before the child's _ready(): a 3D level already sees the 642x362 viewport when it configures itself.
func _on_world_child_entered(n: Node) -> void:
	if n is Node3D:
		view.set_hires(false)
	view.on_world_child_added(n)


func _on_world_child_exiting(n: Node) -> void:
	if not (n is Node3D):
		return
	for c in level_root.get_children():
		if c != n and c is Node3D and not c.is_queued_for_deletion():
			return
	view.set_hires(true)
