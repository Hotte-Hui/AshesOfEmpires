extends Node
## Main scene root. Owns the pixel world viewport, the HD UI layer and the overlay layer.
## All game flow lives in the Game autoload (scripts/core/game.gd).

@onready var world: SubViewport = $World
@onready var level_root: Node = $World/LevelRoot
@onready var camera: Camera2D = $World/Camera
@onready var grade: ColorRect = $World/Post/Grade
@onready var view: Control = $WorldView
@onready var ui_layer: CanvasLayer = $UI
@onready var overlay: CanvasLayer = $Overlay


func _ready() -> void:
	view.setup(world)
	Game.register_main(self)
