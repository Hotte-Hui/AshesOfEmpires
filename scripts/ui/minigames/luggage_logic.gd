extends RefCounted
## Rule of „Die Gepäckwaage“ (scenes/ui/minigames/LuggageScale.tscn, explore entry berlin.ost.luggage_scale at
## exp_luggage_scale in L_C4P2_Berlin, scene A; documentation/C4P2_DESIGN.md §6, TECHNICAL_ARCHITECTURE §12.8).
## Monday evening, Ostbahnhof, the baggage counter of platform K: the family from the buffet travels to the mother's
## mother in Karsk; the clerk stamps only what is weighed, and the Corridor allows 20 kg a suitcase and 5 kg a parcel.
## A decimal platform scale with two sliding weights on its beam: the big one sits in notches of 5 kg (0–50 kg), the
## small one slides in steps of 0.1 kg (0–5 kg). The beam's tongue plays in at the mark when the weights equal the
## load; within half a kilo it shows how far off it is, beyond that it rests against its stop. Three weighings: the
## suitcase of presents (23.6 kg — too heavy, the mother repacks), the suitcase again (19.8 kg) and the parcel of what
## came out (3.8 kg) — the same 23.6 kg in a form the Corridor allows. Weights in hectograms (0.1 kg) as integers.

const ITEMS := [
	{"key": "mg.luggage.item.1", "hg": 236, "limit_hg": 200, "result": "mg.luggage.result.1"},
	{"key": "mg.luggage.item.2", "hg": 198, "limit_hg": 200, "result": "mg.luggage.result.2"},
	{"key": "mg.luggage.item.3", "hg": 38, "limit_hg": 50, "result": "mg.luggage.result.3"},
]
const COARSE_HG := 50          # one notch of the big weight: 5 kg
const COARSE_MAX := 10         # notches 0 … 10 = 0 … 50 kg
const FINE_MAX := 50           # steps 0 … 50 = 0 … 5.0 kg
const SWING_HG := 5            # the tongue's free range: ± 0.5 kg

var round_i := 0
var coarse := 0
var fine := 0
var done := false
var moves := 0
var results: Array = []        # [{round, hg, over}]


func reset() -> void:
	round_i = 0
	coarse = 0
	fine = 0
	done = false
	moves = 0
	results = []


func item() -> Dictionary:
	return ITEMS[clampi(round_i, 0, ITEMS.size() - 1)]


func load_hg() -> int:
	return int(item()["hg"])


func poise_hg() -> int:
	return coarse * COARSE_HG + fine


## Weights minus load in hectograms: < 0 too light (the tongue stands up), > 0 too heavy (down).
func diff_hg() -> int:
	return poise_hg() - load_hg()


func balanced() -> bool:
	return not done and diff_hg() == 0


## The tongue's position: -1 at the upper stop, 0 at the mark, +1 at the lower stop.
func tongue() -> float:
	return clampf(float(diff_hg()) / float(SWING_HG), -1.0, 1.0)


## One notch of the big weight: d = +1 / -1. {ok, reason: "" | end | done}.
func move_coarse(d: int) -> Dictionary:
	if done:
		return {"ok": false, "reason": "done"}
	var n := clampi(coarse + d, 0, COARSE_MAX)
	if n == coarse:
		return {"ok": false, "reason": "end"}
	coarse = n
	moves += 1
	return {"ok": true, "reason": ""}


## The small weight by `steps` tenths of a kilo (clamped at its ends; refused only when it cannot move at all).
func move_fine(d: int, steps := 1) -> Dictionary:
	if done:
		return {"ok": false, "reason": "done"}
	var n := clampi(fine + d * maxi(1, steps), 0, FINE_MAX)
	if n == fine:
		return {"ok": false, "reason": "end"}
	fine = n
	moves += 1
	return {"ok": true, "reason": ""}


func set_coarse(n: int) -> bool:
	n = clampi(n, 0, COARSE_MAX)
	if done or n == coarse:
		return false
	coarse = n
	moves += 1
	return true


func set_fine(n: int) -> bool:
	n = clampi(n, 0, FINE_MAX)
	if done or n == fine:
		return false
	fine = n
	moves += 1
	return true


## Reading the scale: only a tongue at the mark is a weighing. {ok, dir: "up" | "down", read_hg, round, over,
## finished}. A good reading records the item and puts the next one on the platform with both weights back at zero.
func read() -> Dictionary:
	var out := {"ok": false, "dir": "", "read_hg": poise_hg(), "round": round_i, "over": false, "finished": done}
	if done:
		return out
	var d := diff_hg()
	if d != 0:
		out["dir"] = "up" if d < 0 else "down"
		return out
	var it := item()
	out["ok"] = true
	out["over"] = int(it["hg"]) > int(it["limit_hg"])
	results.append({"round": round_i, "hg": int(it["hg"]), "over": out["over"]})
	round_i += 1
	coarse = 0
	fine = 0
	if round_i >= ITEMS.size():
		done = true
		round_i = ITEMS.size() - 1
	out["finished"] = done
	return out


## Where the weights belong for a load: the big one in the last notch that stays below it, the small one the rest.
static func target_for(hg: int) -> Dictionary:
	var c := mini(floori(float(hg) / float(COARSE_HG)), COARSE_MAX)
	return {"coarse": c, "fine": hg - c * COARSE_HG}


## The next sensible move (hints, the demo): {"beam": "coarse" | "fine" | "read", "dir", "steps"}.
func next_move() -> Dictionary:
	if done:
		return {}
	var t := target_for(load_hg())
	if coarse != int(t["coarse"]):
		return {"beam": "coarse", "dir": 1 if int(t["coarse"]) > coarse else -1, "steps": absi(int(t["coarse"]) - coarse)}
	if fine != int(t["fine"]):
		return {"beam": "fine", "dir": 1 if int(t["fine"]) > fine else -1, "steps": absi(int(t["fine"]) - fine)}
	return {"beam": "read", "dir": 0, "steps": 0}


## „23,6 kg“ — the German reading of hectograms.
static func kg_text(hg: int) -> String:
	return "%d,%d kg" % [floori(float(hg) / 10.0), hg % 10]
