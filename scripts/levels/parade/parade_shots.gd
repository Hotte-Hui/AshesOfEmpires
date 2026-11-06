extends RefCounted
## Shot table of L_M1_Parade (owner: parade).  Same camera rules as the hall reveal (hall_camera_rig.gd): the
## camera NEVER rotates (verticals stay vertical, the hall's facade stays parallel to the image plane); "tilts"
## are lens shifts (+y = horizon moves down, i.e. looking up), moves are translations.  Hard cuts between shots,
## slow eased moves inside them.  No heroic low angles on individuals: the low shots sit at the crowd's eye level
## behind the barrier and the guards, the troops are always a mass at a distance.
## Units: metres / lens-shift pixels.  Plaza axis x = 45 (hall_builder.HX), the hall's podium front at z = -1000.

## id, start, end, p0, p1, s0 (lens shift), s1, ease ("smooth" | "linear" | "crane": already rising on the cut, at
## CRANE_V0 x the mean speed, easing out into the final pose), min_depth (hide crowd figures nearer than this: the
## camera stands inside the crowd), shake (px, tanks)
const SHOTS := [
	# p1 high wide: crane-tilt from the floodlit dome down onto the plaza packed with formations
	{"id": "p1", "start": 0.0, "end": 6.5, "p0": Vector3(30.0, 150.0, -555.0), "p1": Vector3(36.0, 140.0, -580.0),
		"s0": Vector2(0, 40), "s1": Vector2(0, -250), "ease": "smooth", "min_depth": 0.0},
	# p2 low tracking shot at the crowd's eye level behind the barrier: the column marches past, guards wipe through
	{"id": "p2", "start": 6.5, "end": 12.5, "p0": Vector3(79.0, 1.5, -846.0), "p1": Vector3(83.8, 1.5, -846.0),
		"s0": Vector2(0, 22), "s1": Vector2(0, 22), "ease": "linear", "min_depth": 9.0},
	# p3 knee height at the barrier: tanks and half-tracks roll through, snow dust, the image shakes
	{"id": "p3", "start": 12.5, "end": 18.5, "p0": Vector3(-37.0, 1.35, -848.0), "p1": Vector3(-37.0, 1.35, -849.0),
		"s0": Vector2(0, 30), "s1": Vector2(0, 30), "ease": "smooth", "min_depth": 7.0, "shake": 1.0},
	# p4 from the portico eagle down to the tribune: grey officials, loudspeakers
	{"id": "p4", "start": 18.5, "end": 24.5, "p0": Vector3(45.0, 15.0, -806.0), "p1": Vector3(45.0, 11.0, -846.0),
		"s0": Vector2(0, 150), "s1": Vector2(0, 62), "ease": "smooth", "min_depth": 0.0},
	# p5 inside the crowd: backs, the evicted family at the barrier, the guards facing THEM
	{"id": "p5", "start": 24.5, "end": 30.5, "p0": Vector3(64.0, 1.55, -821.75), "p1": Vector3(65.5, 1.55, -824.25),
		"s0": Vector2(0, 14), "s1": Vector2(0, 14), "ease": "smooth", "min_depth": 4.5},
	# p6 the dome under the searchlight pillars, a jet formation thunders over it
	{"id": "p6", "start": 30.5, "end": 35.5, "p0": Vector3(45.0, 40.0, -330.0), "p1": Vector3(45.0, 42.0, -345.0),
		"s0": Vector2(0, 150), "s1": Vector2(0, 150), "ease": "smooth", "min_depth": 0.0},
	# p7 Konrad at the back edge of the crowd (inner voice): from a little above and behind him, over the sea of heads
	# to the hall.  The camera slides slowly sideways at a constant ~31 m from him, so his 1:1 sprite keeps its true
	# size against the crowd (parallax instead of a push-in); his feet stay at ~row 286 of 362, clear of the subtitle
	# plate; his lone trail comes in along the crowd's back edge from the left; the top edge passes below the plaza
	# banners' emblems (no emblem cut in half)
	{"id": "p7", "start": 35.5, "end": 40.5, "p0": Vector3(-102.3, 7.25, -761.0), "p1": Vector3(-100.7, 7.25, -761.0),
		"s0": Vector2(0, -93), "s1": Vector2(0, -93), "ease": "smooth", "min_depth": 0.0},
	# p8 the cleared street: from the sealed door up along the emptied windows; the spectacle is far away -- the whole
	# avenue up to the hall is the parade route (hall_avenue.gd + the avenue crowd of parade_set.gd)
	{"id": "p8", "start": 40.5, "end": 47.0, "p0": Vector3(-6.5, 1.3, -24.0), "p1": Vector3(-6.5, 30.0, -6.0),
		"s0": Vector2(0, 30), "s1": Vector2(0, -40), "ease": "crane", "min_depth": 0.0},
]
## Pose used to calibrate the facade's pilaster rhythm (hall_builder): the dome shot.
const CAL_SHOT := 5
## "crane" ease: start speed as a share of the mean speed (the crane is already rising on the cut, so the spectacle
## grows over the horizon within the first second; the peak speed stays below the smooth ease's 1.5)
const CRANE_V0 := 0.7


## Ease of a shot: u in 0..1 -> share of the move.
static func ease_of(kind: String, u: float) -> float:
	if kind == "linear":
		return u
	if kind == "crane":
		return CRANE_V0 * u + (3.0 - 2.0 * CRANE_V0) * u * u + (CRANE_V0 - 2.0) * u * u * u
	return u * u * (3.0 - 2.0 * u)


func duration() -> float:
	return float(SHOTS[SHOTS.size() - 1]["end"])


func shot_index(t: float) -> int:
	for i in SHOTS.size():
		if t < float(SHOTS[i]["end"]):
			return i
	return SHOTS.size() - 1


## Returns {"pos": Vector3, "shift": Vector2, "shot": int, "id": String, "min_depth": float}
func sample(t: float) -> Dictionary:
	t = clampf(t, 0.0, duration())
	var i := shot_index(t)
	var s: Dictionary = SHOTS[i]
	var u := clampf((t - float(s["start"])) / maxf(float(s["end"]) - float(s["start"]), 0.001), 0.0, 1.0)
	var e := ease_of(str(s["ease"]), u)
	var pos: Vector3 = (s["p0"] as Vector3).lerp(s["p1"], e)
	var shift: Vector2 = (s["s0"] as Vector2).lerp(s["s1"], e)
	var shake := float(s.get("shake", 0.0))
	if shake > 0.0:
		# tracks on cobbles: whole-pixel jolts, strongest while a hull passes the lens (12.9 - 18.2 s)
		var k := smoothstep(12.7, 13.4, t) * (1.0 - smoothstep(17.6, 18.3, t))
		shift += Vector2(roundf(sin(t * 41.0) * shake * k * 0.6), roundf(sin(t * 57.0 + 1.3) * shake * k))
	return {"pos": pos, "shift": shift, "shot": i, "id": str(s["id"]), "min_depth": float(s.get("min_depth", 0.0))}
