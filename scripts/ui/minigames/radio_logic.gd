extends RefCounted
## Berlin "Das Radio" — tuning and the porter's rhythm (pure logic, used by radio_game.gd and the tests).
## The needle runs over the medium-wave scale (0..1). The Reichssender sits on the red line (REICH), the foreign
## station on the pencil dot (FOREIGN, narrow: it needs fine tuning), two faint Reich stations in between.
## The porter reads his paper (away), lowers it (warning, WARN s) and looks over (LOOK s). If he looks while the
## needle is off the red line, Konrad is "caught": gently -- the needle goes back to the Reichssender and 40 % of
## the listening is lost, nothing else. Listening accrues while the foreign station is clear and the porter is
## not looking; LISTEN_NEED seconds of it solve the mini-game. step() is deterministic (tests drive it).

const REICH := 0.24          # mirrored in tools/pixelgen/gen_minigames.py (red line / pencil dot)
const FOREIGN := 0.83
const FAINT := [0.46, 0.63]
const W_REICH := 0.045
const W_FOREIGN := 0.032
const W_FAINT := 0.026
const CLEAR := 0.8
const REICH_BAND := 0.03
const LISTEN_NEED := 5.0
const AWAY := [8.5, 7.0, 9.0, 6.5]
const WARN := 1.7
const LOOK := 2.6
const TAP_STEP := 0.004
const SPEED_MIN := 0.07
const SPEED_MAX := 0.34
const RAMP := 0.9
const CAUGHT_LOSS := 0.4

var needle := REICH
var progress := 0.0
var porter := "reading"      # reading | lowering | looking
var porter_t := 0.0          # seconds left in the porter's state
var cycle := 0
var caught := 0
var hold := 0.0
var done := false
var _caught_this_look := false


func _init() -> void:
	reset()


func reset() -> void:
	needle = REICH
	progress = 0.0
	porter = "reading"
	porter_t = AWAY[0]
	cycle = 0
	caught = 0
	hold = 0.0
	done = false
	_caught_this_look = false


static func peak(center: float, width: float, pos: float) -> float:
	var d := (pos - center) / width
	return clampf(1.0 - d * d, 0.0, 1.0)


func foreign_signal() -> float:
	return peak(FOREIGN, W_FOREIGN, needle)


func reich_signal() -> float:
	return peak(REICH, W_REICH, needle)


func faint_signal() -> float:
	var s := 0.0
	for f in FAINT:
		s = maxf(s, 0.45 * peak(float(f), W_FAINT, needle))
	return s


func strength() -> float:
	return maxf(maxf(foreign_signal(), reich_signal()), faint_signal())


func on_reich() -> bool:
	return absf(needle - REICH) <= REICH_BAND


## Nearest station centre and width (for the heterodyne whistle).
func nearest_station() -> Array:
	var best := [REICH, W_REICH]
	var bd := absf(needle - REICH)
	for c in [[FOREIGN, W_FOREIGN], [FAINT[0], W_FAINT], [FAINT[1], W_FAINT]]:
		if absf(needle - float(c[0])) < bd:
			bd = absf(needle - float(c[0]))
			best = c
	return best


func nudge(dir: int) -> void:
	needle = clampf(needle + dir * TAP_STEP, 0.0, 1.0)


## Held turning: slow at first, faster the longer the key is held.
func turn(dir: int, dt: float) -> void:
	hold += dt
	var sp := lerpf(SPEED_MIN, SPEED_MAX, clampf(hold / RAMP, 0.0, 1.0))
	needle = clampf(needle + dir * sp * dt, 0.0, 1.0)


func release() -> void:
	hold = 0.0


func set_needle(v: float) -> void:
	needle = clampf(v, 0.0, 1.0)


## The radio's station key: straight back to the Reichssender.
func preset() -> void:
	needle = REICH
	hold = 0.0


## Advances the porter and the listening; returns events: warn, look, away, caught, solved.
func step(dt: float) -> Array:
	var ev: Array = []
	if done:
		return ev
	porter_t -= dt
	if porter_t <= 0.0:
		match porter:
			"reading":
				porter = "lowering"
				porter_t = WARN
				ev.append("warn")
			"lowering":
				porter = "looking"
				porter_t = LOOK
				_caught_this_look = false
				ev.append("look")
			_:
				porter = "reading"
				cycle += 1
				porter_t = float(AWAY[cycle % AWAY.size()])
				ev.append("away")
	if porter == "looking":
		if not on_reich() and not _caught_this_look:
			_caught_this_look = true
			caught += 1
			progress = maxf(0.0, progress - CAUGHT_LOSS)
			preset()
			ev.append("caught")
	elif foreign_signal() >= CLEAR:
		progress = minf(1.0, progress + dt / LISTEN_NEED)
		if progress >= 1.0:
			done = true
			ev.append("solved")
	return ev
