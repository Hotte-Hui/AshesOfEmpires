extends RefCounted
## Plaza "Das Blatt im Schnee" (explore entry plaza.leaflet, §12.8) -- pure logic, used by leaflet_game.gd and
## tests/test_minigames_plaza.gd. Deterministic: step(dt, dir, bend_held) is the only clock.
## The pavement lane in front of the barrier runs 0..1. Konrad walks along it; a typed sheet lies in the snow and
## is pushed by gusts (fixed schedule) unless Konrad stands on it. Two posts behind the barrier take turns: each
## watches the parade ("away"), turns his head ("turn", the warning) and lets his gaze sweep along the lane
## ("sweep") before turning back. Holding "bend" lowers Konrad (bend 0..1); fully bent over the sheet he has it.
## If a gaze passes over him while he is bent, he is noticed -- gently: he straightens up, the post looks at him
## for a moment ("stare"), nothing is lost. One notice per sweep. Never punishing, no limits.

const WALK := 0.2              # lane units per second
const BEND_IN := 1.1           # seconds to bend down fully
const BEND_OUT := 0.35         # seconds to straighten up
const BENT := 0.2              # bent this far, a passing gaze notices him
const MOVE_MAX_BEND := 0.05    # walking only while (almost) upright
const REACH := 0.04            # fully bent within this distance of the sheet: picked up
const FOOT := 0.045            # standing this close, the foot holds the sheet against the wind
const GAZE_HALF := 0.11        # half width of a gaze on the lane
const START_K := 0.08
const START_SHEET := 0.55
const SHEET_RANGE := [0.14, 0.92]
## Both posts share a 16 s cycle; per cycle (3 variants) each one turns at its own time.
const PERIOD := 16.0
const TURN := 1.1
const SWEEP := 3.1
const STARE := 1.4
const TURN_AT := [[2.0, 3.0, 2.5], [6.0, 7.5, 5.5]]          # [guard][cycle % 3], seconds into the cycle
const SWEEP_FROM := [0.0, 1.0]
const SWEEP_TO := [0.66, 0.34]
const GUST_FIRST := 4.2
const GUST_EVERY := 5.6
const GUST_LEN := 0.7
const GUST_PUSH := [0.09, -0.07, 0.11, -0.08]

var k := START_K
var facing := 1
var bend := 0.0
var sheet := START_SHEET
var t := 0.0
var gt: Array = [0.0, 0.0]      # each post's own clock (stops while he stares)
var stare: Array = [0.0, 0.0]
var noticed := 0
var done := false
var gusting := false
var pinned := false
var moving := false
var _sweep_seen: Array = [-1, -1]   # cycle index of the sweep that already noticed him
var _last_state: Array = ["away", "away"]
var _gust_idx := -1
var _nothing_said := false


func _init() -> void:
	reset()


func reset() -> void:
	k = START_K
	facing = 1
	bend = 0.0
	sheet = START_SHEET
	t = 0.0
	gt = [0.0, 0.0]
	stare = [0.0, 0.0]
	noticed = 0
	done = false
	gusting = false
	pinned = false
	moving = false
	_sweep_seen = [-1, -1]
	_last_state = ["away", "away"]
	_gust_idx = -1
	_nothing_said = false


## [state, progress 0..1, cycle] of post g ("away" | "turn" | "sweep" | "stare").
func guard_state(g: int) -> Array:
	if float(stare[g]) > 0.0:
		return ["stare", 1.0, int(floor(float(gt[g]) / PERIOD))]
	var c := int(floor(float(gt[g]) / PERIOD))
	var tc := float(gt[g]) - c * PERIOD
	var start := float(TURN_AT[g][c % 3])
	if tc >= start and tc < start + TURN:
		return ["turn", (tc - start) / TURN, c]
	if tc >= start + TURN and tc < start + TURN + SWEEP:
		return ["sweep", (tc - start - TURN) / SWEEP, c]
	return ["away", 0.0, c]


## Where post g looks on the lane (-1 = not at the lane).
func gaze(g: int) -> float:
	var s: Array = guard_state(g)
	if s[0] == "stare":
		return k
	if s[0] != "sweep":
		return -1.0
	var p: float = float(s[1])
	p = p * p * (3.0 - 2.0 * p)
	return lerpf(float(SWEEP_FROM[g]), float(SWEEP_TO[g]), p)


func watched() -> bool:
	for g in 2:
		var gz := gaze(g)
		if gz >= 0.0 and absf(gz - k) <= GAZE_HALF:
			return true
	return false


## Seconds until the next post turns away from the parade (0 while one is not watching the parade).
func calm_left() -> float:
	var best := 999.0
	for g in 2:
		if guard_state(g)[0] != "away":
			return 0.0
		var c := int(floor(float(gt[g]) / PERIOD))
		var tc := float(gt[g]) - c * PERIOD
		var start := float(TURN_AT[g][c % 3])
		var left := start - tc if tc < start else PERIOD - tc + float(TURN_AT[g][(c + 1) % 3])
		best = minf(best, left)
	return best


## True while both posts look at the parade (the safe moment).
func calm() -> bool:
	return guard_state(0)[0] == "away" and guard_state(1)[0] == "away"


func over_sheet() -> bool:
	return absf(k - sheet) <= REACH


func on_sheet() -> bool:
	return absf(k - sheet) <= FOOT


## Advances everything by dt with the player's input; returns events:
## turn, sweep, away, gust, pinned, noticed, nothing, solved.
func step(dt: float, dir: int, bend_held: bool) -> Array:
	var ev: Array = []
	if done:
		return ev
	t += dt
	# --- Konrad
	moving = false
	if bend_held and float(stare[0]) <= 0.0 and float(stare[1]) <= 0.0:   # nobody bends while being looked at
		bend = minf(1.0, bend + dt / BEND_IN)
	else:
		bend = maxf(0.0, bend - dt / BEND_OUT)
		_nothing_said = false
	if dir != 0 and bend <= MOVE_MAX_BEND:
		facing = 1 if dir > 0 else -1
		var nk := clampf(k + dir * WALK * dt, 0.0, 1.0)
		moving = not is_equal_approx(nk, k)
		k = nk
	# --- wind
	var gi := int(floor((t - GUST_FIRST) / GUST_EVERY)) if t >= GUST_FIRST else -1
	var in_gust := gi >= 0 and (t - GUST_FIRST - gi * GUST_EVERY) < GUST_LEN
	if in_gust and gi != _gust_idx:
		_gust_idx = gi
		ev.append("pinned" if on_sheet() else "gust")
	gusting = in_gust
	pinned = in_gust and on_sheet()
	if in_gust and not pinned:
		var push := float(GUST_PUSH[gi % GUST_PUSH.size()])
		var ns := clampf(sheet + push * dt / GUST_LEN, float(SHEET_RANGE[0]), float(SHEET_RANGE[1]))
		# the sheet stops against Konrad's shoe
		if absf(ns - k) <= FOOT and absf(sheet - k) > FOOT:
			ns = sheet
		sheet = ns
	# --- the posts
	for g in 2:
		if float(stare[g]) > 0.0:
			stare[g] = maxf(0.0, float(stare[g]) - dt)
			if float(stare[g]) <= 0.0:
				_last_state[g] = "sweep"
			continue
		gt[g] = float(gt[g]) + dt
		var s: String = str(guard_state(g)[0])
		if s != _last_state[g]:
			ev.append(s)
			_last_state[g] = s
	# --- noticed? (gently)
	if bend > BENT:
		for g in 2:
			var st: Array = guard_state(g)
			if st[0] != "sweep" or int(_sweep_seen[g]) == int(st[2]):
				continue
			var gz := gaze(g)
			if absf(gz - k) <= GAZE_HALF:
				_sweep_seen[g] = int(st[2])
				stare[g] = STARE
				_last_state[g] = "stare"
				noticed += 1
				bend = 0.0
				ev.append("noticed")
				return ev
	# --- picked up?
	if bend >= 1.0:
		if over_sheet():
			done = true
			ev.append("solved")
		elif not _nothing_said:
			_nothing_said = true
			ev.append("nothing")
	return ev
