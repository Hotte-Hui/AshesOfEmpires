extends "res://scripts/levels/karsk/karsk_cat.gd"
## L_C4P2_Karsk, scene A: the yard dog asleep on the warm rim of the ash pit (C4P2_DESIGN §4.1, exp_ash_pit_dog).
## The Chapter-1 cat's behaviour (karsk_cat.gd: sleeps and breathes; lifts its head, watches, blinks, twitches an ear
## and wags when Alexei comes near; settles back after he has gone) with the dog's frames
## (tools/pixelgen/env_c4p2_karsk_fx.py dog(): sleep_a, sleep_b, head_mid, head_up, blink, ear, tail — 24 x 12, the
## same anchor). A dog does not purr: the cat's sound is left out. Never touches Story.


func sfx(id: String, volume_db := 0.0, pitch_var := 0.06) -> void:
	if id == "karsk_cat_mrrp":
		return
	super.sfx(id, volume_db, pitch_var)
