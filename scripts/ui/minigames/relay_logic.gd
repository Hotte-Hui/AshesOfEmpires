extends RefCounted
## „Das Relaispult" (explore entry veltrava.hall.relay, TECHNICAL_ARCHITECTURE §12.8) -- pure logic, used by
## relay_game.gd and tests/test_minigames_r7_relay.gd. Deterministic: step(dt) is the only clock; the player acts
## through plug(row, col), select(row), yellow(), red() and advance().
##
## The commission's simultaneous-interpretation desk in the interpreters' corridor of the Palais (model: the
## booth-and-lamp systems of the post-war conferences). Floor languages: German (Reichsdelegation), Russian
## (Sowjetische Delegation), French (the chair; the commission's working language). Three booths (art: L_C3_Hall,
## C3_DESIGN §4.2): Kabine 1 · FR (works into French, gives the German retour while the floor speaks French),
## Kabine 2 · RU⇄DE (both directions), Kabine 3 · EN (the observers). A booth that does not understand the floor
## takes the RELAY of a booth that does: it listens to that booth's output instead of the floor -- a second-hand
## voice, so it falls behind sooner (lower capacity).
## Four delegation channels (rows) DE / RU / FR / EN; each is plugged into one of four sources (columns):
## SAAL (the floor original), K1, K2, K3. A row is right when the source speaks the row's language right now.
## Backlog (Rückstand) per booth 0..1 grows while the speaker is faster than the booth can follow; at 1 the
## interpreter loses the thread (a few seconds of silence on that booth and on every booth that relays from it).
## Yellow lamp: the speaker slows down for a while (ignored when nobody is behind); red lamp: the speaker stops for
## a moment and the booths catch up (ignored when nobody is far behind). Three scripted rounds with rising tempo;
## a round passes with PASS of the speech time understood on all four channels, otherwise it is repeated (never a
## limit, never a penalty beyond that). After round 3 the chair adjourns: a quiet beat, then "solved".
## No microphone numbers, no agenda numbers or times, nothing about Anlage C (keeps the protocol puzzle intact).

const ROWS := ["de", "ru", "fr", "en"]          # the language each delegation channel needs (row order)
const SOURCES := ["saal", "k1", "k2", "k3"]     # crossbar columns
const BOOTHS := ["k1", "k2", "k3"]
## Languages each booth's interpreters take directly from the floor.
const HEARS := {"k1": ["fr", "de"], "k2": ["ru", "de"], "k3": ["fr", "de"]}
## Booth language: what it speaks into; RETOUR: what it speaks while the floor already speaks its language.
const INTO := {"k1": "fr", "k2": "ru", "k3": "en"}
const RETOUR := {"k1": "de", "k2": "de", "k3": ""}
const SPEAKER_LANG := {"chair": "fr", "soviet": "ru", "reich": "de"}

const CAP_DIRECT := 1.0
const CAP_RELAY := 0.82
const K_UP := 0.5           # backlog per second per unit of tempo above capacity
const K_DOWN := 0.32        # recovery per second per unit of capacity left over
const YELLOW_TEMPO := 0.72  # the speaker's tempo while the yellow lamp is lit (content advances at that rate too)
const YELLOW_TIME := 6.0
const RED_TIME := 2.6
const LOST_TIME := 3.5
const LOST_RESUME := 0.3    # backlog when the interpreter picks the thread up again
const YELLOW_MIN := 0.2     # below this nobody needs a slower speaker (the lamp is ignored)
const RED_MIN := 0.4        # below this an interruption is not justified (ignored)
const ZONE_YELLOW := 0.45   # meter zones (UI, hints, demo)
const ZONE_RED := 0.75
const PASS := 0.68
const MAX_LOST := 4          # this many lost threads in one round and the chair has the passage repeated
const Q_YELLOW := 0.9      # row quality while its booth is in the yellow zone
const Q_RED := 0.45        # ... and in the red zone (the interpreter drops words)
const INTRO_TIME := 4.5
const SUMMARY_TIME := 3.6
const BEAT_TIME := 9.0
const BEAT_LINES := 6
const MAX_STEP := 0.1

## Rounds: title/tempo keys, announcement length, grace at each speech start, initial plugs (round 1 only; later
## rounds keep the desk as the player left it) and the turns: speaker, duration (content seconds at tempo 1),
## tempo segments [[content time, tempo], ...], announce (seconds the chair needs to give the floor; 0 = the turn
## follows at once), interject (a heckle: very short warning). Text keys: mg.relay.r<n>.t<m>.
const ROUNDS := [
	{"key": "r1", "grace": 1.2, "start_plugs": [1, 2, 0, 0], "turns": [
		{"who": "chair", "dur": 6.0, "tempo": [[0.0, 0.85]], "announce": 0.0},
		{"who": "soviet", "dur": 10.0, "tempo": [[0.0, 1.0], [3.2, 1.32], [7.2, 1.0]], "announce": 2.6},
		{"who": "reich", "dur": 8.0, "tempo": [[0.0, 1.0]], "announce": 2.6},
		{"who": "chair", "dur": 5.0, "tempo": [[0.0, 0.85]], "announce": 2.6}]},
	{"key": "r2", "grace": 1.0, "turns": [
		{"who": "reich", "dur": 7.5, "tempo": [[0.0, 1.1], [2.6, 1.45], [6.0, 1.1]], "announce": 0.0},
		{"who": "soviet", "dur": 7.0, "tempo": [[0.0, 1.18]], "announce": 2.0},
		{"who": "chair", "dur": 4.5, "tempo": [[0.0, 0.9]], "announce": 2.0},
		{"who": "reich", "dur": 6.0, "tempo": [[0.0, 1.5]], "announce": 2.0},
		{"who": "soviet", "dur": 6.0, "tempo": [[0.0, 1.3]], "announce": 2.0}]},
	{"key": "r3", "grace": 0.8, "turns": [
		{"who": "chair", "dur": 5.0, "tempo": [[0.0, 1.05]], "announce": 0.0},
		{"who": "soviet", "dur": 6.5, "tempo": [[0.0, 1.25], [2.4, 1.55]], "announce": 1.4},
		{"who": "reich", "dur": 3.5, "tempo": [[0.0, 1.4]], "announce": 0.5, "interject": true},
		{"who": "chair", "dur": 4.0, "tempo": [[0.0, 1.2]], "announce": 0.6, "interject": true},
		{"who": "soviet", "dur": 5.5, "tempo": [[0.0, 1.4]], "announce": 1.4},
		{"who": "reich", "dur": 4.5, "tempo": [[0.0, 1.3]], "announce": 1.4},
		{"who": "chair", "dur": 4.5, "tempo": [[0.0, 0.8]], "announce": 1.4}]},
]

var phase := "intro"          # intro | announce | speech | summary | beat | done
var phase_t := 0.0
var round_i := 0
var turn_i := 0
var speech_t := 0.0           # content time of the current speech
var plugs: Array = [1, 2, 0, 0]
var sel := 0                  # selected row (UI cursor, kept here so tests and the demo can read it)
var backlog: Array = [0.0, 0.0, 0.0]
var lost: Array = [0.0, 0.0, 0.0]
var yellow_left := 0.0
var pause_left := 0.0
var good := 0.0               # channel-seconds understood this round
var total := 0.0              # channel-seconds counted this round
var last_ratio := 0.0
var last_passed := false
var last_fail := ""           # why the last round was repeated: "ratio" | "lost" | ""
var rounds_passed := 0
var attempts := 0             # round attempts (incl. repeats)
var lost_count := 0
var round_lost := 0           # threads lost in the current round attempt
var unnecessary := 0
var lamps_used := 0
var done := false


func _init() -> void:
	reset()


func reset() -> void:
	phase = "intro"
	phase_t = 0.0
	round_i = 0
	turn_i = 0
	speech_t = 0.0
	plugs = (ROUNDS[0]["start_plugs"] as Array).duplicate()
	sel = 3
	_reset_round_state()
	last_ratio = 0.0
	last_passed = false
	last_fail = ""
	rounds_passed = 0
	attempts = 1
	lost_count = 0
	unnecessary = 0
	lamps_used = 0
	done = false
	_ev = []


## Starts the current round again from its intro (plugs stay; passed rounds stay passed). Counts as an attempt.
func restart_round() -> void:
	if done or phase == "beat":
		return
	attempts += 1
	last_fail = ""
	_reset_round_state()
	_set_phase("intro")


func _reset_round_state() -> void:
	backlog = [0.0, 0.0, 0.0]
	lost = [0.0, 0.0, 0.0]
	yellow_left = 0.0
	pause_left = 0.0
	good = 0.0
	total = 0.0
	turn_i = 0
	speech_t = 0.0
	round_lost = 0


# ================================================================ queries
func round_def() -> Dictionary:
	return ROUNDS[clampi(round_i, 0, ROUNDS.size() - 1)]


func turns() -> Array:
	return round_def()["turns"]


func turn() -> Dictionary:
	var ts := turns()
	return ts[clampi(turn_i, 0, ts.size() - 1)]


## Text key of the current turn's speech (mg.relay.r1.t2 ...).
func turn_key(r := -1, t := -1) -> String:
	var ri := round_i if r < 0 else r
	var ti := turn_i if t < 0 else t
	return "mg.relay.%s.t%d" % [str(ROUNDS[ri]["key"]), ti + 1]


func speaker() -> String:
	return str(turn().get("who", "chair"))


func speaker_lang(who := "") -> String:
	return str(SPEAKER_LANG.get(speaker() if who == "" else who, "fr"))


## Language spoken on the floor right now ("" = nobody: intro, announcement, red-lamp pause, summary, beat).
func floor_lang() -> String:
	if phase != "speech" or pause_left > 0.0:
		return ""
	return speaker_lang()


## The floor language the desk must be set for: during an announcement the coming speaker's, else the current.
func target_lang() -> String:
	if phase == "speech" or phase == "announce":
		return speaker_lang()
	if phase == "intro":
		return speaker_lang(str((turns()[0] as Dictionary).get("who", "chair")))
	return ""


func tempo_at(t: float) -> float:
	var tp := 1.0
	for seg in turn().get("tempo", [[0.0, 1.0]]):
		if t >= float(seg[0]):
			tp = float(seg[1])
	return tp


## Nominal tempo of the speech right now (without the yellow lamp), 0 when nobody speaks.
func tempo() -> float:
	return tempo_at(speech_t) if phase == "speech" else 0.0


## The tempo the booths have to follow right now.
func effective_tempo() -> float:
	if floor_lang() == "":
		return 0.0
	return tempo() * (YELLOW_TEMPO if yellow_left > 0.0 else 1.0)


## Booth k's output language for floor language fl ("" while the floor is silent).
func booth_out(k: int, fl := "-") -> String:
	var f := floor_lang() if fl == "-" else fl
	if f == "":
		return ""
	var b: String = BOOTHS[k]
	return str(RETOUR[b]) if f == str(INTO[b]) else str(INTO[b])


## True if booth k cannot take floor language fl directly (it works from another booth's output).
func is_relay(k: int, fl := "-") -> bool:
	var f := floor_lang() if fl == "-" else fl
	return f != "" and not (f in (HEARS[BOOTHS[k]] as Array))


## The booth k listens to while on relay (-1 = it hears the floor itself): a booth that hears the floor directly
## and whose output k understands.
func pivot(k: int, fl := "-") -> int:
	var f := floor_lang() if fl == "-" else fl
	if not is_relay(k, f):
		return -1
	for j in BOOTHS.size():
		if j != k and not is_relay(j, f) and booth_out(j, f) in (HEARS[BOOTHS[k]] as Array):
			return j
	return -1


## Booth k produces no speech right now (nobody on the floor, thread lost, or its relay source is silent).
func booth_silent(k: int, depth := 0) -> bool:
	if floor_lang() == "" or float(lost[k]) > 0.0:
		return true
	var p := pivot(k)
	return p >= 0 and depth < 3 and booth_silent(p, depth + 1)


func capacity(k: int) -> float:
	return CAP_RELAY if is_relay(k) else CAP_DIRECT


## Language row r hears right now ("" = silence).
func heard(r: int) -> String:
	var c := int(plugs[r])
	if c == 0:
		return floor_lang()
	if booth_silent(c - 1):
		return ""
	return booth_out(c - 1)


func row_ok(r: int) -> bool:
	return heard(r) == str(ROWS[r])


## How much of the speech row r gets across right now: 0 wrong language or silence; 1 the floor itself or a
## booth that keeps up; a booth deep in the red zone drops words (Q_RED), in the yellow zone a few (Q_YELLOW).
func row_quality(r: int) -> float:
	if not row_ok(r):
		return 0.0
	var c := int(plugs[r])
	if c == 0:
		return 1.0
	var b := float(backlog[c - 1])
	return Q_RED if b >= ZONE_RED else (Q_YELLOW if b >= ZONE_YELLOW else 1.0)


## The column row r needs for floor language fl (fl "" -> -1).
func correct_col(r: int, fl := "-") -> int:
	var f := floor_lang() if fl == "-" else fl
	if f == "":
		return -1
	var need: String = ROWS[r]
	if need == f:
		return 0
	for k in BOOTHS.size():
		if booth_out(k, f) == need:
			return k + 1
	return -1


## True if every row is plugged right for floor language fl.
func desk_right(fl: String) -> bool:
	if fl == "":
		return false
	for r in ROWS.size():
		if int(plugs[r]) != correct_col(r, fl):
			return false
	return true


func max_backlog() -> float:
	var m := 0.0
	for k in BOOTHS.size():
		if float(lost[k]) <= 0.0:
			m = maxf(m, float(backlog[k]))
	return m


## Share of the counted speech time understood so far this round (1 before anything was counted).
func ratio() -> float:
	return good / total if total > 0.0 else 1.0


func zone(k: int) -> String:
	if float(lost[k]) > 0.0:
		return "lost"
	var b := float(backlog[k])
	return "red" if b >= ZONE_RED else ("yellow" if b >= ZONE_YELLOW else "ok")


## Content progress of the current speech 0..1.
func speech_progress() -> float:
	if phase != "speech":
		return 0.0
	return clampf(speech_t / maxf(0.01, float(turn().get("dur", 1.0))), 0.0, 1.0)


func announce_left() -> float:
	return maxf(0.0, float(turn().get("announce", 0.0)) - phase_t) if phase == "announce" else 0.0


func is_interjection() -> bool:
	return bool(turn().get("interject", false))


# ================================================================ actions
func select(r: int) -> void:
	sel = clampi(r, 0, ROWS.size() - 1)


func move_sel(d: int) -> void:
	select(wrapi(sel + d, 0, ROWS.size()))


## Plugs row r into column c. Returns true if something changed.
func plug(r: int, c: int) -> bool:
	if done or phase == "beat":
		return false
	r = clampi(r, 0, ROWS.size() - 1)
	c = clampi(c, 0, SOURCES.size() - 1)
	sel = r
	if int(plugs[r]) == c:
		return false
	plugs[r] = c
	return true


## Moves the selected row's plug one column left/right (stops at the ends).
func shift(d: int) -> bool:
	return plug(sel, clampi(int(plugs[sel]) + d, 0, SOURCES.size() - 1))


## Yellow lamp. Returns "yellow" (lit), "yellow_ignored" (nobody behind) or "" (nobody speaking).
func yellow() -> String:
	if phase != "speech" or pause_left > 0.0:
		return ""
	if max_backlog() < YELLOW_MIN:
		unnecessary += 1
		return "yellow_ignored"
	yellow_left = YELLOW_TIME
	lamps_used += 1
	return "yellow"


## Red lamp. Returns "red" (the speaker stops), "red_ignored" (nobody far behind) or "".
func red() -> String:
	if phase != "speech" or pause_left > 0.0:
		return ""
	if max_backlog() < RED_MIN:
		unnecessary += 1
		return "red_ignored"
	pause_left = RED_TIME
	lamps_used += 1
	return "red"


## Confirm: skips the intro and the round summary; in the final beat it first shows every line, then ends.
## Returns true if it did something (its events arrive with the next step()).
func advance() -> bool:
	match phase:
		"intro":
			_begin_first_turn()
			return true
		"summary":
			_after_summary()
			return true
		"beat":
			if beat_lines() < BEAT_LINES:
				phase_t = maxf(phase_t, BEAT_TIME * float(BEAT_LINES) / float(BEAT_LINES + 1))
			else:
				_finish()
			return true
	return false


# ================================================================ clock
## Advances by dt; returns the events since the last call (actions queue theirs too): round_start, announce,
## speech, lost:<k>, lost_end:<k>, yellow_end, red_end, round_passed, round_failed, adjourned, solved.
var _ev: Array = []


func step(dt: float) -> Array:
	if done:
		return _flush()
	dt = clampf(dt, 0.0, MAX_STEP)
	phase_t += dt
	match phase:
		"intro":
			if phase_t >= INTRO_TIME:
				_begin_first_turn()
		"announce":
			_booths(dt)
			if phase_t >= float(turn().get("announce", 0.0)):
				_set_phase("speech")
				speech_t = 0.0
				_ev.append("speech")
		"speech":
			_speech(dt)
		"summary":
			if phase_t >= SUMMARY_TIME:
				_after_summary()
		"beat":
			if phase_t >= BEAT_TIME:
				_finish()
	return _flush()


func _flush() -> Array:
	var out := _ev
	_ev = []
	return out


func _set_phase(p: String) -> void:
	phase = p
	phase_t = 0.0


func _begin_first_turn() -> void:
	turn_i = 0
	speech_t = 0.0
	_ev.append("round_start")
	if float(turn().get("announce", 0.0)) > 0.0:
		_set_phase("announce")
		_ev.append("announce")
	else:
		_set_phase("speech")
		_ev.append("speech")


func _speech(dt: float) -> void:
	var paused := pause_left > 0.0
	if paused:
		pause_left = maxf(0.0, pause_left - dt)
		if pause_left <= 0.0:
			_ev.append("red_end")
	# score before the booths move on (the state the delegations heard during this frame)
	if not paused and speech_t >= float(round_def().get("grace", 1.0)):
		var n := 0.0
		for r in ROWS.size():
			n += row_quality(r)
		good += dt * n
		total += dt * ROWS.size()
	_booths(dt)
	if not paused:
		var rate := YELLOW_TEMPO if yellow_left > 0.0 else 1.0
		speech_t += dt * rate
		if yellow_left > 0.0:
			yellow_left = maxf(0.0, yellow_left - dt)
			if yellow_left <= 0.0:
				_ev.append("yellow_end")
	if speech_t >= float(turn().get("dur", 1.0)):
		_next_turn()


func _booths(dt: float) -> void:
	var tau := effective_tempo()
	for k in BOOTHS.size():
		if float(lost[k]) > 0.0:
			lost[k] = maxf(0.0, float(lost[k]) - dt)
			if float(lost[k]) <= 0.0:
				backlog[k] = LOST_RESUME
				_ev.append("lost_end:%d" % k)
			continue
		var cap := capacity(k)
		var input := tau
		if booth_silent(k):
			input = 0.0
		var b := float(backlog[k])
		if input > cap:
			b += K_UP * (input - cap) * dt
		else:
			b = maxf(0.0, b - K_DOWN * (cap - input) * dt)
		if b >= 1.0:
			b = 1.0
			lost[k] = LOST_TIME
			lost_count += 1
			round_lost += 1
			_ev.append("lost:%d" % k)
		backlog[k] = b


func _next_turn() -> void:
	yellow_left = 0.0
	pause_left = 0.0
	if turn_i + 1 >= turns().size():
		_end_round()
		return
	turn_i += 1
	speech_t = 0.0
	if float(turn().get("announce", 0.0)) > 0.0:
		_set_phase("announce")
		_ev.append("announce")
	else:
		_set_phase("speech")
		_ev.append("speech")


func _end_round() -> void:
	last_ratio = ratio()
	last_passed = last_ratio >= PASS and round_lost < MAX_LOST
	last_fail = "" if last_passed else ("lost" if round_lost >= MAX_LOST else "ratio")
	_set_phase("summary")
	if last_passed:
		rounds_passed += 1
		_ev.append("round_passed")
	else:
		_ev.append("round_failed")


func _after_summary() -> void:
	if last_passed and round_i + 1 >= ROUNDS.size():
		_set_phase("beat")
		_ev.append("adjourned")
		return
	if last_passed:
		round_i += 1
	attempts += 1
	_reset_round_state()
	_set_phase("intro")


func _finish() -> void:
	if done:
		return
	_set_phase("done")
	done = true
	_ev.append("solved")


## Index (0..BEAT_LINES) of the beat lines visible so far (the UI reveals them one by one).
func beat_lines() -> int:
	if phase != "beat":
		return BEAT_LINES if done else 0
	return clampi(int(phase_t / (BEAT_TIME / float(BEAT_LINES + 1))) + 1, 1, BEAT_LINES)
