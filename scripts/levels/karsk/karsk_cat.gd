extends "res://scripts/levels/karsk/karsk_actor.gd"
## Ginger cat curled up by the fire barrel (exp_cat). Sleeps (slow breathing); when the player comes within
## `wake_radius` it lifts its head, watches with fire-lit eyes, blinks, twitches an ear, flicks its tail —
## and settles back to sleep a little after the player has gone.
## Frames (env_karsk_sprites.CAT_FRAMES): sleep_a, sleep_b, head_mid, head_up, blink, ear, tail — 18x11,
## feet/ground at (10, 10). The eyes are emissive (cat_e.png).

var sprite := ""
var wake_radius := 46.0

const SLEEP_A := 0
const SLEEP_B := 1
const HEAD_MID := 2
const HEAD_UP := 3
const BLINK := 4
const EAR := 5
const TAIL := 6

var _spr: Sprite2D
var _glow: Sprite2D
var _state := "sleep"
var _t := 0.0
var _act_t := 0.0
var _next := 2.0
var _away := 0.0
var _mrrp_cool := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 1007
	var tex := canvas_tex(sprite, true)
	if tex == null:
		push_warning("KarskCat: missing sprite " + sprite)
		return
	_spr = make_strip(tex, 7)
	_spr.offset = Vector2(-10, -10)
	_glow = make_glow(sprite, 7, 0.55)
	if _glow:
		_glow.offset = _spr.offset
	_frame(SLEEP_A)


func _frame(f: int) -> void:
	if _spr == null:
		return
	_spr.frame = f
	if _glow:
		_glow.frame = f
		_glow.visible = f == HEAD_UP or f == EAR or f == TAIL


func _tick(delta: float) -> void:
	if _spr == null:
		return
	_t += delta
	_mrrp_cool = maxf(0.0, _mrrp_cool - delta)
	var pp := player_pos()
	var d := INF if pp == Vector2.INF else pp.distance_to(position)
	match _state:
		"sleep":
			_frame(SLEEP_B if fmod(_t, 2.8) > 1.6 else SLEEP_A)   # slow breathing
			if d < wake_radius:
				_state = "waking"
				_act_t = 0.0
		"waking":
			_act_t += delta
			_frame(HEAD_MID if _act_t < 0.3 else HEAD_UP)
			if _act_t >= 0.3:
				_state = "awake"
				_next = _rng.randf_range(1.0, 2.5)
				_away = 0.0
				if _mrrp_cool <= 0.0:
					_mrrp_cool = 20.0
					sfx("karsk_cat_mrrp", dist_db(position, -10.0, -24.0), 0.08)
		"awake":
			if d > wake_radius + 18.0:
				_away += delta
			else:
				_away = 0.0
			if _away > 2.5:
				_state = "settling"
				_act_t = 0.0
				return
			if _act_t > 0.0:
				_act_t -= delta
				if _act_t <= 0.0:
					_frame(HEAD_UP)
				return
			_next -= delta
			if _next <= 0.0:
				_next = _rng.randf_range(1.4, 3.6)
				var r := _rng.randf()
				if r < 0.45:
					_frame(BLINK)
					_act_t = 0.14
				elif r < 0.7:
					_frame(EAR)
					_act_t = 0.22
				else:
					_frame(TAIL)
					_act_t = 0.45
		"settling":
			_act_t += delta
			_frame(HEAD_MID if _act_t < 0.35 else SLEEP_A)
			if _act_t >= 0.35:
				_state = "sleep"
				_t = 0.0
			if d < wake_radius:
				_state = "waking"
				_act_t = 0.2
