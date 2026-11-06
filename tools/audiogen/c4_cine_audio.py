"""c4_cine_audio -- original synthesised sound for the five Chapter-4 cinematics (owner: cine stream, round 9).

Self-contained numpy synthesis on the helpers of tools/audiogen/c3_cine_audio.py (band-pass, envelopes, panning,
generated rooms, WAV writer, train elements) and c3p2_cine_audio.py (snow steps, creaks, wind, metal hits,
crackles) -- both imported read-only.  Deterministic (seeds = crc32 of the sound's name), 44.1 kHz / 16-bit,
nothing sampled or downloaded.  Writes assets/audio/sfx/c4cine_*.wav.

  LS_C4_Homeward  station (the shed at dawn: two engines breathing, a whistle far off, two carriage doors slam at
                  DOOR_SLAMS), rails (two ride rhythms, the Reich carriage left, the broad gauge right), yard
                  (night wind, a shunter far off, Alexei's steps in the snow, the relay of the signal)
  LS_C4_Number    tunnel (drips, a fan in an air shaft, steps on gravel, the lamp's bail), drip (the macro: one
                  wet tick, the hum), hatch (Berlin dawn: the lorry idling, the hoist's chain paying out, crates),
                  tram (line 74 comes round the loop: wheel squeal, motor dying, the bell at TRAM_BELL, the stop)
  LS_C4_Card      card_snow (wind, a glove in the snow, the card lifted, the thumb on the holes), perf / perf_ru
                  (macro: the tip runs over the perforation -- ticks between PERF_TICKS), office (kerosene lamp,
                  the wall clock, a train overhead: dust trickles)
  LS_C4_Stamp     desk (pencil strokes, the card slid into the box), stamp_ru / stamp_de (the stamp comes down at
                  STAMP_HIT: wood on wood in Karsk, bakelite on linoleum in Berlin), annex (two big fans, muffled
                  typewriters, the perforator's clack at LEVER_CLACK, a tube capsule)
  LS_C4_Voices    column (the iron door, steps, the city's morning rumble), tram_leave (the motor winds up, the car
                  rolls away to the right), bell (one strike of the tram bell; the picture rings it once or twice),
                  yard_night (the cellar door, steps on stone then snow, wind, a lantern's bail), lamp_out (the work
                  lamp's hum, its flicker at LAMP_FLICKS, then the drip in the dark), tuesday (a far train)

Run:  py -3 -P tools/audiogen/c4_cine_audio.py [--only name,name]   (then the shared --import)
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3_cine_audio as A  # noqa: E402  (read-only)
import c3p2_cine_audio as B  # noqa: E402  (read-only: crunch, creak, wind, metal_hit, crackles)

SR = A.SR
n_of, band, lp, hp, decay, place, pan, fades, norm, room, rng = (
    A.n_of, A.band, A.lp, A.hp, A.decay, A.place, A.pan, A.fades, A.norm, A.room, A.rng)

# times shared with the pictures (scenes/cinematics/ch4_*/ch4_*.gd; checked by tests/test_c4_cinematics.gd),
# given in FILM time; every bed below subtracts its own start
DOOR_SLAMS = (3.75, 4.05)                     # ch4_homeward.gd DOOR_SLAMS (bed c4cine_station at 0.0)
TRAM_BELL = 11.4                              # ch4_number.gd TRAM_BELL (bed c4cine_tram at 9.5)
PERF_TICKS = (3.6, 4.85)                      # ch4_card.gd PERF_TICKS (bed c4cine_perf at 3.5)
STAMP_HIT = (3.86, 5.36)                      # ch4_stamp.gd STAMP_RU[1], STAMP_DE[1] (beds at 3.5 / 5.0)
LEVER_CLACK = 7.42                            # ch4_stamp.gd LEVER[1] (bed c4cine_annex at 6.6)
LAMP_FLICKS = (18.2, 18.45, 18.9)             # ch4_voices.gd LAMP_FLICKS (bed c4cine_lamp_out at 15.0)


def write(name, x):
    return A.write(name, x)


def silence(sec, ch=2):
    return np.zeros((n_of(sec), ch)) if ch == 2 else np.zeros(n_of(sec))


def hum(sec, f=50.0, gain=1.0):
    t = np.arange(n_of(sec)) / SR
    return (np.sin(2 * np.pi * f * t) * 0.6 + np.sin(2 * np.pi * 2 * f * t) * 0.3 +
            np.sin(2 * np.pi * 3 * f * t) * 0.1) * gain


def drip(r, f=1700.0, gain=1.0):
    """A water / paint drop: a short rising 'plink' with a tiny splash."""
    m = n_of(0.12)
    t = np.arange(m) / SR
    fr = f * (1 + 2.2 * t / 0.12)
    x = np.sin(np.cumsum(2 * np.pi * fr / SR)) * decay(m, 0.025, 0.001)
    x += band(r.standard_normal(m), 2000, 7000) * decay(m, 0.004, 0.0003) * 0.4
    return x * gain


def steps(r, sec, t0, per, kind='snow', gain=1.0, pans=(0.0, 0.0), until=None):
    """A walk: one step every `per` seconds from t0 (snow crunch / gravel / stone)."""
    x = np.zeros((n_of(sec), 2))
    tt = t0
    k = 0
    end = sec - 0.15 if until is None else until
    while tt < end:
        u = (tt - t0) / max(0.001, end - t0)
        p = pans[0] + (pans[1] - pans[0]) * u
        if kind == 'snow':
            s = B.crunch(r, gain)
        elif kind == 'gravel':
            s = B.crunch(r, gain, dark=0.6) + band(r.standard_normal(n_of(0.16)), 900, 3000) * \
                decay(n_of(0.16), 0.03, 0.002) * 0.3 * gain
        else:
            m = n_of(0.14)
            s = (lp(r.standard_normal(m), 400) * decay(m, 0.03, 0.002) +
                 band(r.standard_normal(m), 1500, 5000) * decay(m, 0.008, 0.0005) * 0.4) * gain
        place(x, pan(s * (0.85 + 0.15 * (k % 2)), p), tt)
        tt += per
        k += 1
    return x


def door_slam(r, gain=1.0, metal=True):
    m = n_of(0.9)
    t = np.arange(m) / SR
    x = lp(r.standard_normal(m), 300) * decay(m, 0.08, 0.002) * 1.2
    x += np.sin(2 * np.pi * 92 * t) * decay(m, 0.12, 0.002) * 0.8
    if metal:
        x += B.metal_hit(r, (310, 740, 1490), 0.18, 0.4, 0.9)[:m]
    return x * gain


def whistle(r, f=620.0, sec=1.4, gain=1.0):
    """A distant steam whistle: two detuned reed tones with a breathy onset."""
    m = n_of(sec)
    t = np.arange(m) / SR
    env = np.clip(t / 0.12, 0, 1) * np.clip((sec - t) / 0.4, 0, 1)
    x = (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * f * 1.26 * t) +
         0.3 * np.sin(2 * np.pi * f * 2.01 * t)) * env
    x += band(r.standard_normal(m), f * 0.8, f * 3.0) * env * 0.25
    return band(x, 300, 3500) * gain * 0.4


def bell(r, f0=1480.0, gain=1.0):
    """The tram's foot-operated bell: a bright double-dome strike with a long ring."""
    m = n_of(1.4)
    t = np.arange(m) / SR
    x = np.zeros(m)
    for f, d, g in ((f0, 0.55, 1.0), (f0 * 2.02, 0.32, 0.45), (f0 * 2.98, 0.18, 0.25), (f0 * 4.2, 0.08, 0.12),
                    (f0 * 1.003, 0.6, 0.5)):
        x += g * np.sin(2 * np.pi * f * t + r.uniform(0, 6.28)) * decay(m, d, 0.0005)
    x += band(r.standard_normal(m), 2500, 8000) * decay(m, 0.004, 0.0002) * 0.6
    return x * gain


def thump(r, body=110.0, wood=True, gain=1.0):
    """A rubber stamp hitting a pad: a dull body thump, the board's knock, a little paper slap."""
    m = n_of(0.5)
    t = np.arange(m) / SR
    x = np.sin(2 * np.pi * body * t * (1 - 0.3 * t)) * decay(m, 0.05, 0.001)
    x += lp(r.standard_normal(m), 600 if wood else 1400) * decay(m, 0.025, 0.0005) * 1.2
    x += band(r.standard_normal(m), 2000, 6000) * decay(m, 0.004, 0.0002) * (0.3 if wood else 0.6)
    if not wood:
        x += np.sin(2 * np.pi * 420 * t) * decay(m, 0.03, 0.0005) * 0.3        # the bakelite's click
    return x * gain


def paper(r, sec=0.4, gain=1.0):
    m = n_of(sec)
    x = band(r.standard_normal(m), 1200, 7000) * (np.abs(B.wind(r, sec, 3, 40, 0.8)) + 0.2)
    return x * np.hanning(m) * gain * 0.6


def pencil(r, sec, rate=7.0, gain=1.0):
    x = np.zeros(n_of(sec))
    tt = 0.0
    while tt < sec - 0.12:
        L = n_of(r.uniform(0.06, 0.12))
        s = band(r.standard_normal(L), 2500, 9000) * np.hanning(L) * r.uniform(0.5, 1.0)
        place(x, s, tt)
        tt += 1.0 / rate * r.uniform(0.6, 1.3)
    return x * gain * 0.4


def ticks(r, sec, t0, t1, count, gain=1.0, f=(1800, 6000)):
    """The thumb / fingertip running over the holes: small dry clicks evenly between t0 and t1."""
    x = np.zeros(n_of(sec))
    for i in range(count):
        tt = t0 + (t1 - t0) * i / max(1, count - 1)
        L = n_of(0.012)
        place(x, band(r.standard_normal(L), f[0], f[1]) * decay(L, 0.003, 0.0002) * r.uniform(0.6, 1.0), tt)
    return x * gain


def overhead_train(r, sec, at=0.4, gain=1.0):
    """A train passing over the vault: a swelling sub rumble, the joints' thuds, dust trickling after."""
    m = n_of(sec)
    t = np.arange(m) / SR
    env = np.clip((t - at) / 1.2, 0, 1) * np.clip((sec - t) / 1.6, 0, 1)
    x = lp(A.brown(m, r), 90) * env * 1.4
    tj = at + 0.5
    while tj < sec - 0.6:
        place(x, A.knock(r, 0.7, 0.1, 54.0) * 0.8, tj)
        place(x, A.knock(r, 0.6, 0.1, 56.0) * 0.8, tj + 0.18)
        tj += 0.62
    dust = band(r.standard_normal(m), 3000, 9000) * np.clip((t - at - 1.0) / 1.0, 0, 1) * env * 0.05
    return (x + dust) * gain


# --------------------------------------------------------------------------- LS_C4_Homeward
def station():
    r = rng('c4cine_station')
    sec = 5.2
    x = np.zeros((n_of(sec), 2))
    for p, start in ((-0.6, 0.2), (0.6, 0.55)):                       # two engines breathing at the far end
        tt = start
        while tt < sec - 0.3:
            place(x, pan(A.chuff(r, 1.4, 700.0) * 0.25, p), tt)
            tt += r.uniform(1.4, 2.0)
    hiss = band(r.standard_normal(n_of(sec)), 2000, 7000) * 0.04
    x += pan(hiss, 0.0)
    place(x, pan(whistle(r, 560.0, 1.6, 0.5), 0.5), 1.1)
    for i, at in enumerate(DOOR_SLAMS):
        place(x, pan(door_slam(r, 0.8), -0.4 if i == 0 else 0.4), at)
    x += steps(r, sec, 0.35, 0.42, 'stone', 0.25, (-0.1, 0.0), until=2.9)
    x = room(x, 'c4cine_station', 2.8, 2.4, 1.4, 0.45, predelay=0.03)
    return norm(fades(x, 0.4, 0.5), -7.0)


def rails():
    r = rng('c4cine_rails')
    sec = 4.2
    m = n_of(sec)
    x = np.zeros((m, 2))
    for ch, (start, per, body) in ((0, (0.15, 0.78, 66.0)), (1, (0.4, 0.92, 74.0))):  # Reich left, broad gauge right
        mono = lp(A.brown(m, r), 150) * 0.4
        tj = start
        while tj < sec - 0.1:
            place(mono, A.knock(r, 0.9, 0.25, body), tj)
            place(mono, A.knock(r, 0.75, 0.2, body * 1.04), tj + 0.12)
            tj += per
        x[:, ch] += mono
        x[:, 1 - ch] += mono * 0.18
    x = room(x, 'c4cine_rails', 0.5, 0.3, 0.12, 0.2)
    return norm(fades(x, 0.25, 0.5), -7.0)


def yard():
    r = rng('c4cine_yard')
    sec = 5.2
    m = n_of(sec)
    x = pan(B.wind(r, sec, 120, 900, 0.4) * 0.35, 0.0)
    place(x, pan(B.metal_hit(r, (180, 430, 920), 0.4, 0.25, 1.2) * 0.4, -0.8), 1.6)   # a coupling far off
    place(x, pan(A.knock(r, 0.4, 0.4, 60.0), 0.6), 0.3)                                 # the relay clicks
    x += steps(r, sec, 0.15, 0.4, 'snow', 0.7, (-0.3, 0.3), until=4.4)
    x = room(x, 'c4cine_yard', 3.0, 1.6, 0.8, 0.25, predelay=0.02)
    return norm(fades(x, 0.3, 0.5), -8.0)


# --------------------------------------------------------------------------- LS_C4_Number
def tunnel():
    r = rng('c4cine_tunnel')
    sec = 4.2
    m = n_of(sec)
    t = np.arange(m) / SR
    fan = band(r.standard_normal(m), 80, 400) * (0.6 + 0.2 * np.sin(2 * np.pi * 6.0 * t)) * 0.25
    x = pan(fan, 0.4)
    for at, p in ((0.5, -0.5), (1.7, 0.3), (2.9, -0.2), (3.6, 0.6)):
        place(x, pan(drip(r, 1500 + 300 * p, 0.5), p), at)
    x += steps(r, sec, 0.2, 0.55, 'gravel', 0.5, (-0.2, 0.2))
    place(x, pan(B.creak(r, 0.5, (700, 520), 0.15), -0.1), 1.1)                          # the lamp's bail
    x = room(x, 'c4cine_tunnel', 3.6, 2.2, 1.4, 0.5, predelay=0.03)
    return norm(fades(x, 0.3, 0.4), -9.0)


def drip_macro():
    r = rng('c4cine_drip')
    sec = 1.6
    x = pan(lp(A.brown(n_of(sec), r), 120) * 0.15, 0.0)
    place(x, pan(drip(r, 900.0, 0.6), 0.1), 0.55)
    x = room(x, 'c4cine_drip', 2.0, 1.4, 0.8, 0.4)
    return norm(fades(x, 0.05, 0.3), -14.0)


def hatch():
    r = rng('c4cine_hatch')
    sec = 4.2
    m = n_of(sec)
    t = np.arange(m) / SR
    diesel = lp(np.sign(np.sin(2 * np.pi * 26.0 * t)) * 0.5 + A.brown(m, r) * 0.6, 260) * 0.5
    x = pan(diesel, -0.6)
    chain = np.zeros(m)
    tt = 1.5
    while tt < 3.9:
        L = n_of(0.03)
        place(chain, band(r.standard_normal(L), 1500, 6000) * decay(L, 0.01, 0.001) * r.uniform(0.3, 0.8), tt)
        tt += r.uniform(0.05, 0.09)
    x += pan(chain, 0.2)
    place(x, pan(A.knock(r, 0.6, 0.1, 80.0), 0.2), 1.4)                                   # the stack lifts off
    x += pan(B.wind(r, sec, 150, 1200, 0.4) * 0.15, 0.0)
    x = room(x, 'c4cine_hatch', 1.8, 1.0, 0.5, 0.25)
    return norm(fades(x, 0.15, 0.5), -8.0)


def tram():
    r = rng('c4cine_tram')
    sec = 3.6
    m = n_of(sec)
    t = np.arange(m) / SR
    approach = np.clip(t / 2.6, 0, 1)
    motor_f = 220 * (1.0 - 0.6 * approach)
    motor = np.sin(np.cumsum(2 * np.pi * motor_f / SR)) * (0.4 * (1 - approach) + 0.05)
    rumble = lp(A.brown(m, r), 140) * (0.3 + 0.7 * approach) * np.clip((2.9 - t) / 0.6, 0, 1)
    squeal = np.sin(np.cumsum(2 * np.pi * (2900 + 200 * np.sin(2 * np.pi * 3 * t)) / SR)) * \
        np.clip((t - 0.6) / 0.4, 0, 1) * np.clip((1.9 - t) / 0.5, 0, 1) * 0.08
    x = np.stack([(motor + rumble + squeal) * (0.4 + 0.6 * (1 - approach)), motor + rumble + squeal], 1)
    place(x, pan(bell(r, 1480.0, 0.7), 0.3), TRAM_BELL - 9.5)
    place(x, pan(band(r.standard_normal(n_of(0.6)), 1500, 6000) * decay(n_of(0.6), 0.2, 0.01) * 0.2, 0.2), 2.8)
    x = room(x, 'c4cine_tram', 2.4, 1.2, 0.6, 0.25)
    return norm(fades(x, 0.3, 0.4), -6.0)


# --------------------------------------------------------------------------- LS_C4_Card
def card_snow():
    r = rng('c4cine_card_snow')
    sec = 3.6
    x = pan(B.wind(r, sec, 150, 1400, 0.45) * 0.3, 0.0)
    place(x, pan(B.crunch(r, 0.8, dark=0.7), -0.3), 0.15)
    place(x, pan(paper(r, 0.5, 0.8), -0.1), 0.6)
    place(x, pan(ticks(r, 2.0, 0.0, 1.8, 14, 0.5), 0.2), 1.5)
    return norm(fades(x, 0.2, 0.4), -10.0)


def perf(name, room_len, warm):
    r = rng(name)
    sec = 1.6
    x = pan(ticks(r, sec, PERF_TICKS[0] - 3.5, PERF_TICKS[1] - 3.5, 9, 1.0, (1200, 4200) if warm else (1800, 6500)), 0.0)
    x += pan(lp(A.brown(n_of(sec), r), 200) * 0.05, 0.0)
    x = room(x, name, room_len, 0.6, 0.3, 0.2)
    return norm(fades(x, 0.05, 0.25), -11.0)


def office():
    r = rng('c4cine_office')
    sec = 4.9
    m = n_of(sec)
    t = np.arange(m) / SR
    lamp = band(r.standard_normal(m), 1200, 4000) * (0.05 + 0.01 * np.sin(2 * np.pi * 0.7 * t))
    x = pan(lamp, 0.5)
    for k in range(int(sec / 0.5)):
        place(x, pan(A.knock(r, 0.12, 0.8, 900.0), -0.5), 0.2 + k * 0.5)                  # the wall clock
    x += pan(overhead_train(r, sec, 0.8, 0.8), 0.0)
    x = room(x, 'c4cine_office', 1.4, 0.7, 0.35, 0.25)
    return norm(fades(x, 0.2, 0.5), -8.0)


# --------------------------------------------------------------------------- LS_C4_Stamp
def desk():
    r = rng('c4cine_desk')
    sec = 3.6
    x = pan(pencil(r, sec, 7.0, 0.8), -0.3)
    place(x, pan(paper(r, 1.6, 0.6), 0.3), 0.6)
    place(x, pan(A.knock(r, 0.3, 0.2, 140.0), 0.3), 2.55)                                   # the card drops in
    x += pan(band(r.standard_normal(n_of(sec)), 1200, 4000) * 0.03, 0.4)
    x = room(x, 'c4cine_desk', 1.4, 0.7, 0.35, 0.2)
    return norm(fades(x, 0.2, 0.3), -10.0)


def stamp(name, at, wood):
    r = rng(name)
    sec = 1.6
    x = np.zeros((n_of(sec), 2))
    whoosh = band(r.standard_normal(n_of(0.25)), 400, 2000) * np.hanning(n_of(0.25)) * 0.12
    place(x, pan(whoosh, 0.0), at - 0.22)
    place(x, pan(thump(r, 110.0 if wood else 150.0, wood, 1.0), 0.0), at)
    place(x, pan(paper(r, 0.12, 0.4), 0.0), at + 0.33)                                      # it lifts off
    if not wood:
        x += pan(band(r.standard_normal(n_of(sec)), 90, 500) * 0.06, 0.0)                    # the annex fans
    x = room(x, name, 1.6 if wood else 2.6, 0.6, 0.3, 0.2 if wood else 0.3)
    return norm(fades(x, 0.02, 0.3), -5.0)


def annex():
    r = rng('c4cine_annex')
    sec = 4.6
    m = n_of(sec)
    t = np.arange(m) / SR
    fans = band(r.standard_normal(m), 70, 380) * (0.7 + 0.15 * np.sin(2 * np.pi * 4.6 * t)) * 0.35
    x = np.stack([fans, np.roll(fans, n_of(0.02))], 1)
    typing = np.zeros(m)
    tt = 0.1
    while tt < sec:
        L = n_of(0.02)
        place(typing, band(r.standard_normal(L), 600, 2500) * decay(L, 0.006, 0.0005) * r.uniform(0.3, 1.0), tt)
        tt += r.uniform(0.08, 0.2) + (0.6 if r.random() < 0.06 else 0.0)
    x += pan(lp(typing, 1800) * 0.4, 0.6)
    clack = B.metal_hit(r, (240, 610, 1320), 0.12, 0.8, 0.6)
    th = thump(r, 90.0, False, 0.6)
    clack[:len(th)] += th[:len(clack)]
    place(x, pan(clack, -0.3), LEVER_CLACK - 6.6)
    place(x, pan(paper(r, 0.2, 0.5), -0.3), LEVER_CLACK - 6.6 + 0.12)
    tube = band(r.standard_normal(n_of(0.6)), 300, 2400) * np.hanning(n_of(0.6)) * 0.25
    place(x, pan(tube, 0.7), 3.2)
    x = room(x, 'c4cine_annex', 3.2, 1.4, 0.7, 0.35, predelay=0.02)
    return norm(fades(x, 0.15, 0.5), -8.0)


# --------------------------------------------------------------------------- LS_C4_Voices
def column():
    r = rng('c4cine_column')
    sec = 5.2
    x = pan(lp(A.brown(n_of(sec), r), 110) * 0.3, 0.0)                                   # the city's rumble
    x += pan(B.wind(r, sec, 150, 1100, 0.4) * 0.2, 0.0)
    place(x, pan(B.creak(r, 0.7, (240, 150), 0.5), 0.0), 0.3)                            # the iron door
    x += steps(r, sec, 1.4, 0.45, 'snow', 0.6, (0.0, -0.6), until=4.8)
    place(x, pan(bell(r, 1320.0, 0.12), -0.9), 3.6)                                      # a tram far off
    x = room(x, 'c4cine_column', 2.6, 1.4, 0.7, 0.25)
    return norm(fades(x, 0.3, 0.5), -8.0)


def tram_leave():
    r = rng('c4cine_tram_leave')
    sec = 5.2
    m = n_of(sec)
    t = np.arange(m) / SR
    go = np.clip((t - 0.3) / 4.7, 0, 1)
    motor = np.sin(np.cumsum(2 * np.pi * (90 + 260 * go) / SR)) * 0.35 * (1 - go * 0.7)
    rum = lp(A.brown(m, r), 160) * (0.8 - go * 0.6)
    mono = motor + rum
    x = np.stack([mono * (1 - go * 0.8), mono * (0.6 + 0.4 * go)], 1)
    x += pan(B.wind(r, sec, 150, 1100, 0.4) * 0.12, 0.0)
    x = room(x, 'c4cine_tram_leave', 2.4, 1.2, 0.6, 0.25)
    return norm(fades(x, 0.2, 0.8), -7.0)


def tram_bell():
    r = rng('c4cine_bell')
    x = pan(bell(r, 1480.0, 1.0), 0.2)
    x = room(x, 'c4cine_bell', 2.4, 1.2, 0.6, 0.3)
    return norm(fades(x, 0.0, 0.3), -6.0)


def yard_night():
    r = rng('c4cine_yard_night')
    sec = 5.2
    x = pan(B.wind(r, sec, 120, 900, 0.4) * 0.3, 0.0)
    place(x, pan(B.creak(r, 0.6, (300, 180), 0.4), 0.4), 0.1)                            # the cellar door
    x += steps(r, sec, 0.25, 0.36, 'stone', 0.5, (0.4, 0.2), until=1.4)
    x += steps(r, sec, 1.45, 0.4, 'snow', 0.6, (0.2, -0.3), until=2.9)
    x += steps(r, sec, 0.95, 0.5, 'stone', 0.35, (0.5, 0.3), until=2.2)                  # Lev, slower
    place(x, pan(B.creak(r, 0.4, (900, 700), 0.12), 0.3), 1.2)                           # the lantern's bail
    place(x, pan(paper(r, 0.3, 0.5), 0.0), 3.1)                                           # the notebook page
    x = room(x, 'c4cine_yard_night', 3.0, 1.6, 0.8, 0.25)
    return norm(fades(x, 0.2, 0.5), -8.0)


def lamp_out():
    r = rng('c4cine_lamp_out')
    sec = 5.2
    m = n_of(sec)
    t = np.arange(m) / SR
    f0, f1, f2 = (v - 15.0 for v in LAMP_FLICKS)
    on = ((t < f0) | ((t >= f1) & (t < f2))).astype(float)
    h = hum(sec, 50.0, 0.18) * on + band(r.standard_normal(m), 3000, 8000) * 0.01 * on
    x = pan(h, 0.0)
    for at in (f0, f1, f2):
        place(x, pan(B.crackles(r, 0.12, 120.0, 0.6), 0.0), at - 0.02)
        place(x, pan(A.knock(r, 0.2, 0.6, 400.0), 0.0), at)
    for at in (f2 + 0.5, f2 + 1.3):
        place(x, pan(drip(r, 1300.0, 0.25), -0.4), at)
    x = room(x, 'c4cine_lamp_out', 3.6, 2.2, 1.2, 0.45, predelay=0.03)
    return norm(fades(x, 0.2, 0.3), -9.0)


def tuesday():
    r = rng('c4cine_tuesday')
    sec = 4.2
    m = n_of(sec)
    t = np.arange(m) / SR
    env = np.clip(t / 1.4, 0, 1) * np.clip((sec - t) / 1.6, 0, 1)
    x = lp(A.brown(m, r), 70) * env * 0.8
    tj = 0.8
    while tj < sec - 1.0:
        place(x, A.knock(r, 0.25, 0.05, 48.0), tj)
        tj += 0.9
    st = np.stack([x, x * 0.9], 1)
    st = room(st, 'c4cine_tuesday', 3.6, 2.4, 1.2, 0.5)
    return norm(fades(st, 0.5, 0.8), -14.0)


SOUNDS = {
    'c4cine_station': station, 'c4cine_rails': rails, 'c4cine_yard': yard,
    'c4cine_tunnel': tunnel, 'c4cine_drip': drip_macro, 'c4cine_hatch': hatch, 'c4cine_tram': tram,
    'c4cine_card_snow': card_snow, 'c4cine_perf': lambda: perf('c4cine_perf', 0.8, False),
    'c4cine_perf_ru': lambda: perf('c4cine_perf_ru', 1.2, True), 'c4cine_office': office,
    'c4cine_desk': desk, 'c4cine_stamp_ru': lambda: stamp('c4cine_stamp_ru', STAMP_HIT[0] - 3.5, True),
    'c4cine_stamp_de': lambda: stamp('c4cine_stamp_de', STAMP_HIT[1] - 5.0, False), 'c4cine_annex': annex,
    'c4cine_column': column, 'c4cine_tram_leave': tram_leave, 'c4cine_bell': tram_bell,
    'c4cine_yard_night': yard_night, 'c4cine_lamp_out': lamp_out, 'c4cine_tuesday': tuesday,
}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args(argv)
    names = [s for s in a.only.split(',') if s] or list(SOUNDS)
    for nm in names:
        print(write(nm, SOUNDS[nm]()))


if __name__ == '__main__':
    main()
