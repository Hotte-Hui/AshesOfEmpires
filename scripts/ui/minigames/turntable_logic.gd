extends RefCounted
## Rule of „Die Drehscheibe“ (scenes/ui/minigames/Turntable.tscn, explore entry karsk.depot.turntable at exp_turntable
## in L_C4P2_Karsk, scene B; documentation/C4P2_DESIGN.md §6, TECHNICAL_ARCHITECTURE §12.8). Tuesday evening at the Karsk
## depot: the press minder wants the sooty shunting engine („Kukuschka“) out of the photograph; the turntable man plays
## tuba in the band. Alexei turns the 30-m bridge with the engine on it and puts it into stall 7.
## Physics of a heavy bridge on a motor controller, pure and deterministic (tests drive step() directly):
##  * angles on the turntable's scale (Teilkreis) in degrees, 0 = east, counter-clockwise positive; the engine's chimney
##    end points along `angle` and only that end has to meet a track („Lok vorziehen“ pulls it forward);
##  * tracks: the entry track (Zufahrt) at 270°, stalls 1–9 of the roundhouse at 30° … 150° (15° apart), stall 7 at 120°;
##  * the motor: pressing a direction gives a small impulse (NUDGE — a tap sets the bridge a few centimetres), holding it
##    longer than HOLD_DELAY accelerates (ACCEL) up to MAX_SPEED; released, the bridge coasts and friction (FRICTION)
##    slows it very gently — with the engine on it the bridge weighs more than a hundred tonnes; the brake (BRAKE) stops it;
##  * pull(): only a standing bridge (|vel| <= STILL) whose chimney end lies within TOL of a track can pull; the right
##    track is stall 7. A refusal never moves anything (the engine bumps against the rail edge and rolls back).
## Distances at the rim are shown in centimetres (RIM_M: half the bridge, 15 m).

const ENTRY := 270.0
const STALLS := {1: 30.0, 2: 45.0, 3: 60.0, 4: 75.0, 5: 90.0, 6: 105.0, 7: 120.0, 8: 135.0, 9: 150.0}
const TARGET := 7
const TOL := 0.2
const STILL := 0.25
const MAX_SPEED := 18.0
const ACCEL := 8.0
const FRICTION := 1.6
const BRAKE := 20.0
const NUDGE := 0.7
const HOLD_DELAY := 0.18
const RIM_M := 15.0

var angle := ENTRY
var vel := 0.0
var motor := 0            # -1 clockwise, +1 counter-clockwise, 0 released
var braking := false
var hold_t := 0.0
var done := false
var pulls := 0            # refused pulls (the scene counts failures itself)
var travelled := 0.0      # total degrees turned (for tests / stats)


func reset() -> void:
	angle = ENTRY
	vel = 0.0
	motor = 0
	braking = false
	hold_t = 0.0
	done = false
	pulls = 0
	travelled = 0.0


## -180 < d <= 180: the shortest signed way from `from` to `to` (degrees).
static func shortest(from: float, to: float) -> float:
	var d := fmod(to - from, 360.0)
	if d > 180.0:
		d -= 360.0
	elif d <= -180.0:
		d += 360.0
	return d


static func wrap360(a: float) -> float:
	var w := fmod(a, 360.0)
	return w + 360.0 if w < 0.0 else w


static func target_angle() -> float:
	return float(STALLS[TARGET])


## Centimetres at the rim for an angle error in degrees.
static func cm_of(err_deg: float) -> float:
	return absf(deg_to_rad(err_deg)) * RIM_M * 100.0


## Press / release the controller: dir -1, 0 or +1. Pressing gives the impulse at once.
func set_motor(dir: int) -> void:
	dir = clampi(dir, -1, 1)
	if done or dir == motor:
		return
	motor = dir
	hold_t = 0.0
	if dir != 0:
		vel = clampf(vel + NUDGE * float(dir), -MAX_SPEED, MAX_SPEED)


func set_brake(on: bool) -> void:
	braking = on and not done


## A push of the bridge by hand (mouse drag): an impulse in degrees per second, limited.
func push(dv: float) -> void:
	if done:
		return
	vel = clampf(vel + clampf(dv, -2.0, 2.0), -MAX_SPEED, MAX_SPEED)


func step(dt: float) -> void:
	if done or dt <= 0.0:
		return
	var driving := false
	if motor != 0:
		hold_t += dt
		if hold_t >= HOLD_DELAY:
			driving = true
			vel = clampf(vel + float(motor) * ACCEL * dt, -MAX_SPEED, MAX_SPEED)
	var dec := BRAKE if braking else (0.0 if driving else FRICTION)
	if dec > 0.0:
		vel = move_toward(vel, 0.0, dec * dt)
	var da := vel * dt
	travelled += absf(da)
	angle = wrap360(angle + da)


func is_still() -> bool:
	return absf(vel) <= STILL


## The track nearest to the chimney end: {"track": stall number or 0 for the entry, "angle", "err" (track - angle)}.
func nearest_track() -> Dictionary:
	var best := {"track": 0, "angle": ENTRY, "err": shortest(angle, ENTRY)}
	for n in STALLS:
		var e := shortest(angle, float(STALLS[n]))
		if absf(e) < absf(float(best["err"])):
			best = {"track": int(n), "angle": float(STALLS[n]), "err": e}
	return best


## Signed degrees from the chimney end to stall 7 along the shorter way.
func err_to_target() -> float:
	return shortest(angle, target_angle())


## True when the chimney end stands on stall 7's rails (within TOL).
func aligned() -> bool:
	return absf(err_to_target()) <= TOL


## „Lok vorziehen“: {ok, reason: "" | moving | gap | wrong | entry, track, err, cm}.
func pull() -> Dictionary:
	var nt := nearest_track()
	var out := {"ok": false, "reason": "", "track": int(nt["track"]), "err": float(nt["err"]),
		"cm": cm_of(float(nt["err"]))}
	if done:
		out["ok"] = true
		return out
	if not is_still():
		out["reason"] = "moving"
	elif absf(float(nt["err"])) > TOL:
		out["reason"] = "gap"
	elif int(nt["track"]) == 0:
		out["reason"] = "entry"
	elif int(nt["track"]) != TARGET:
		out["reason"] = "wrong"
	else:
		out["ok"] = true
		done = true
		vel = 0.0
		motor = 0
		braking = false
		angle = target_angle()
		return out
	pulls += 1
	return out


## Distance the bridge still runs at the current speed: coasting (FRICTION) or braking (BRAKE).
func coast_distance(with_brake := false) -> float:
	var d := BRAKE if with_brake else FRICTION
	return vel * vel / (2.0 * d)


## The next sensible move toward stall 7 (hints, tests): {"do": "drive"|"brake"|"wait"|"tap"|"pull", "dir"}.
## Far away: drive until the braking distance reaches the stall; nearer: brake while coasting would overshoot, drive
## while it would fall short, otherwise let it coast; standing within a tap's reach: tap; on the rails: pull.
func next_move() -> Dictionary:
	if done:
		return {}
	var e := err_to_target()
	var dir := 1 if e > 0.0 else -1
	var dist := absf(e)
	if is_still():
		if dist <= TOL * 0.6:
			return {"do": "pull", "dir": dir}
		if dist <= 0.3:
			return {"do": "tap", "dir": dir}
		return {"do": "drive", "dir": dir}
	if vel * float(dir) < 0.0:
		return {"do": "brake", "dir": dir}
	if dist > coast_distance(true) + 1.0:
		return {"do": "drive", "dir": dir}
	var coast := coast_distance(false)
	if coast > dist + TOL * 0.5:
		return {"do": "brake", "dir": dir}
	if coast < dist - TOL * 0.5:
		return {"do": "drive", "dir": dir}
	return {"do": "wait", "dir": dir}
