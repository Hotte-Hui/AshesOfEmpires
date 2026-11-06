extends "res://scripts/levels/karsk/karsk_crows.gd"
## L_C4P2_Karsk, scene A: sparrows on the canteen hatch and the roundhouse cornice (C4P2_DESIGN §4.1). The
## Chapter-1 crows' behaviour (karsk_crows.gd: idle, look round, preen, hop; nervous, then they lift and come back
## 22–40 s later) with sparrow frames (tools/pixelgen/env_c4p2_karsk_fx.py sparrows(), the crows' 14 x 12 layout).
## Sparrows do not caw: the crows' calls are left out, their wing beats are quieter. Never touches Story.


func sfx(id: String, volume_db := 0.0, pitch_var := 0.06) -> void:
	if id == "karsk_crow_caw":
		return
	super.sfx(id, volume_db - 8.0 if id == "karsk_crow_flap" else volume_db, pitch_var + 0.1)
