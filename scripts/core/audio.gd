extends Node
## STUB — ambience/music/SFX manager (TECHNICAL_ARCHITECTURE §7).
func play_ambience(_name: String, _fade: float = 1.5) -> void: pass
func play_music(_name: String, _fade: float = 2.0) -> void: pass
func stop_music(_fade: float = 2.0) -> void: pass
func sfx(_name: String, _volume_db: float = 0.0, _pitch_var: float = 0.05) -> void: pass
func ui(_name: String) -> void: pass
