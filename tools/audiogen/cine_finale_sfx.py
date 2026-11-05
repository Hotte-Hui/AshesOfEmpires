"""cine_finale_sfx -- sound for the X1 finale montage (owner: trans-finale).

Writes assets/audio/sfx/cine_finale_*.wav (44.1 kHz, 16-bit).  100 % synthesised, original, deterministic
(seeds from crc32 of the file names).  Uses the project's audio toolkit read-only (dsp / instruments / foley /
music.Track and the K / B motifs composed by the audio specialist).

  score            47.5 s cue, 60 bpm so beats = montage seconds: B (Berlin, Konrad) on muted piano over a low G
                   pedal; a cold harmonic for the snow; K (Karsk, Alexei) on felt piano in D; question / answer
                   heads in the rhyme cuts; both heads together while C-17 is drawn; the A/Bb rub when the line
                   reaches Berlin; the music drops out with the lamps, a high harmonic + low D remain.
  room_berlin / room_karsk   20 s seamless loops (window wind, radiator ticks / stove crackle, far shunting)
  tick, tock       pendulum clock escapement (Berlin)          telegraph   block-instrument sounder clicks (Karsk)
  type_1..4        typewriter key strikes      bell / carriage / pull   end-of-line bell, return, sheet pulled out
  fold, cloth      paper crease, wool & satin  knock, door_shut, pencil, book, key   Karsk desk and door
  pen              a line drawn on paper (5.6 s)   switch_b / switch_k   the two lamp switches   snowgust   veil
Run: py -3 -P tools/audiogen/cine_finale_sfx.py
"""
from __future__ import annotations

import math
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import (SR, TAU, secs, eq, place, pan2, normalize_peak, fade, to_stereo, smoothstep, write_wav,  # noqa: E402
                 make_ir, reverb, stft_noise, smooth_periodic)
from instruments import impact, modal, noise_burst, random_modes, bell_modes  # noqa: E402
from foley import wood_knock, paper_rustle, type_tick, wind, gust_curve, norm_peak, in_room, ir_archive  # noqa: E402
import music as M  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')
DUR = 47.5


def R(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode('utf-8')))


def fin(x: np.ndarray, peak_db: float, tail: float = 0.02, lp: float = 11000.0) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = eq(x, ('lp', lp, 4), ('hp', 30.0, 2), circular=False)
    x = x - np.mean(x, axis=0)
    a = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    x = normalize_peak(x, peak_db)
    a = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    above = np.nonzero(a > 10 ** (-80 / 20))[0]
    end = min(len(x), (above[-1] + secs(0.03)) if above.size else len(x))
    x = fade(x[:end], 0.0, min(tail, end / SR / 4))
    return normalize_peak(x, peak_db)


# ------------------------------------------------------------------------------------------- clock / telegraph
def tick(kind: str) -> np.ndarray:
    rng = R('cine_finale_' + kind)
    f = 2350.0 if kind == 'tick' else 1780.0
    y = impact(rng, [(f, 1.0, 0.035), (f * 1.62, 0.6, 0.025), (f * 2.71, 0.35, 0.015), (f * 0.38, 0.4, 0.05)],
               0.35, hard=0.6, noise_lo=1500, noise_hi=8000, noise_amt=0.35, noise_decay=0.004)
    body = wood_knock(rng, 340.0 if kind == 'tick' else 290.0, 0.35, hard=0.2)
    y = y + 0.45 * body[:len(y)]
    y = in_room(y, ir_archive(), 0.18)
    return fin(y, -8.0, 0.05)


def telegraph() -> np.ndarray:
    rng = R('cine_finale_telegraph')
    a = impact(rng, [(1450, 1.0, 0.03), (2900, 0.6, 0.02), (4100, 0.35, 0.012), (720, 0.5, 0.04)], 0.18, hard=0.8,
               noise_lo=1800, noise_hi=9000, noise_amt=0.4, noise_decay=0.003)
    b2 = impact(rng, [(1210, 0.7, 0.025), (2500, 0.5, 0.018), (610, 0.4, 0.03)], 0.14, hard=0.6,
                noise_lo=1500, noise_hi=8000, noise_amt=0.3, noise_decay=0.003)
    y = np.zeros(secs(0.3))
    place(y, a, 0, circular=False)
    place(y, 0.55 * b2, secs(0.045), circular=False)
    return fin(y, -9.0, 0.04)


# ------------------------------------------------------------------------------------------- typewriter
def type_key(i: int) -> np.ndarray:
    rng = R('cine_finale_type_%d' % i)
    p = [1.0, 0.94, 1.06, 0.98][i]
    strike = impact(rng, [(980 * p, 0.8, 0.02), (1900 * p, 1.0, 0.014), (3300 * p, 0.6, 0.009), (430 * p, 0.6, 0.03)],
                    0.12, hard=0.75, noise_lo=1200, noise_hi=7500, noise_amt=0.45, noise_decay=0.0025)
    thump = wood_knock(rng, 150.0 * p, 0.12, hard=0.45)
    key = type_tick(rng, 0.8 * p)
    y = np.zeros(secs(0.16))
    place(y, 0.6 * thump, 0, circular=False)
    place(y, key * 0.5, 0, circular=False)
    place(y, strike, secs(0.012), circular=False)
    return fin(in_room(y, ir_archive(), 0.06, tail=False), -9.0, 0.03)


def bell() -> np.ndarray:
    rng = R('cine_finale_bell')
    y = modal([(2860, 1.0, 0.9), (2860 * 2.41, 0.35, 0.5), (2860 * 3.9, 0.15, 0.3), (2860 * 0.5, 0.1, 0.4)], 1.0,
              seed=int(rng.integers(1 << 30)), attack=0.001)
    return fin(y, -12.0, 0.2)


def carriage() -> np.ndarray:
    rng = R('cine_finale_carriage')
    n = secs(0.55)
    y = np.zeros(n)
    # ratchet: accelerating clicks while the carriage slides, then the stop clunk
    t = 0.0
    k = 0
    while t < 0.34:
        c = impact(rng, [(2600 + 200 * (k % 3), 0.7, 0.01), (5200, 0.3, 0.006)], 0.04, hard=0.7, noise_lo=2000,
                   noise_hi=9000, noise_amt=0.4, noise_decay=0.002)
        place(y, c * (0.35 + 0.4 * t / 0.34), secs(t), circular=False)
        t += 0.032 - 0.012 * (t / 0.34)
        k += 1
    slide = noise_burst(0.34, rng, 600, 4000, 0.4, attack=0.02)
    place(y, 0.12 * norm_peak(slide), 0, circular=False)
    stop = impact(rng, [(420, 1.0, 0.06), (980, 0.6, 0.04), (2100, 0.35, 0.02)], 0.2, hard=0.5)
    place(y, 0.9 * stop, secs(0.34), circular=False)
    return fin(in_room(y, ir_archive(), 0.12), -9.0, 0.05)


def pull() -> np.ndarray:
    rng = R('cine_finale_pull')
    n = secs(0.8)
    y = np.zeros(n)
    t = 0.02
    while t < 0.6:
        c = impact(rng, [(3100, 0.6, 0.006), (5400, 0.3, 0.004)], 0.02, hard=0.8, noise_lo=2500, noise_hi=9500,
                   noise_amt=0.5, noise_decay=0.0015)
        place(y, c * 0.5, secs(t), circular=False)
        t += 0.018 + 0.01 * rng.random()
    sl = paper_rustle(rng, 0.7, 0.75, 2)
    place(y, 0.7 * sl, 0, circular=False)
    return fin(in_room(y, ir_archive(), 0.12), -10.0, 0.08)


# ------------------------------------------------------------------------------------------- paper / cloth
def fold() -> np.ndarray:
    rng = R('cine_finale_fold')
    y = paper_rustle(rng, 0.45, 0.8, 2)
    press = noise_burst(0.08, rng, 150, 2000, 0.05, attack=0.003)
    place(y, 0.35 * norm_peak(press), secs(0.3), circular=False)
    return fin(y, -10.0, 0.05)


def cloth() -> np.ndarray:
    rng = R('cine_finale_cloth')
    n = secs(0.7)
    t = np.arange(n) / SR
    env = np.exp(-0.5 * ((t - 0.28) / 0.12) ** 2) + 0.5 * np.exp(-0.5 * ((t - 0.5) / 0.08) ** 2)
    x = rng.standard_normal(n) * env
    x = eq(x, ('hp', 300, 2), ('lp', 3200, 2), ('bell', 900, 3.0, 1.0), circular=False)
    sat = rng.standard_normal(n) * env * (rng.random(n) < 0.02)
    sat = eq(sat, ('hp', 2500, 2), ('lp', 9000, 2), circular=False)
    return fin(x + 0.3 * sat, -12.0, 0.08)


# ------------------------------------------------------------------------------------------- Karsk desk + door
def knock() -> np.ndarray:
    rng = R('cine_finale_knock')
    y = wood_knock(rng, 96.0, 0.5, hard=0.7)
    door = modal([(78, 0.6, 0.18), (155, 0.4, 0.12), (310, 0.25, 0.08)], 0.5, seed=int(rng.integers(1 << 30)))
    y = y + 0.5 * door[:len(y)]
    small = make_ir(length=0.9, rt_low=0.5, rt_high=0.3, predelay=0.006, seed=77)
    return fin(in_room(y, small, 0.25), -6.0, 0.08)


def door_shut() -> np.ndarray:
    rng = R('cine_finale_door_shut')
    thud = wood_knock(rng, 70.0, 0.8, hard=0.6)
    latch = impact(rng, [(1800, 0.8, 0.04), (3100, 0.5, 0.03), (900, 0.4, 0.05)], 0.3, hard=0.7)
    y = np.zeros(secs(1.0))
    place(y, thud, 0, circular=False)
    place(y, 0.7 * latch, secs(0.05), circular=False)
    air = noise_burst(0.25, rng, 80, 900, 0.2, attack=0.04)
    place(y, 0.25 * norm_peak(air), 0, circular=False)
    small = make_ir(length=1.0, rt_low=0.6, rt_high=0.3, predelay=0.006, seed=78)
    return fin(in_room(y, small, 0.3), -8.0, 0.15)


def pencil() -> np.ndarray:
    rng = R('cine_finale_pencil')
    tap = impact(rng, [(1600, 0.7, 0.02), (3200, 0.4, 0.012), (700, 0.4, 0.03)], 0.2, hard=0.5)
    y = np.zeros(secs(0.45))
    place(y, tap, 0, circular=False)
    roll = noise_burst(0.25, rng, 500, 3000, 0.25, attack=0.02)
    place(y, 0.15 * norm_peak(roll), secs(0.03), circular=False)
    tap2 = impact(rng, [(1500, 0.5, 0.015), (3000, 0.3, 0.01)], 0.1, hard=0.4)
    place(y, 0.35 * tap2, secs(0.22), circular=False)
    return fin(y, -12.0, 0.06)


def book() -> np.ndarray:
    rng = R('cine_finale_book')
    thump = wood_knock(rng, 105.0, 0.5, hard=0.35)
    air = noise_burst(0.12, rng, 150, 2500, 0.08, attack=0.01)
    pages = paper_rustle(rng, 0.25, 0.5, 1)
    y = np.zeros(secs(0.6))
    place(y, 0.4 * pages, 0, circular=False)
    place(y, thump, secs(0.12), circular=False)
    place(y, 0.4 * norm_peak(air), secs(0.1), circular=False)
    return fin(y, -7.0, 0.08)


def key() -> np.ndarray:
    rng = R('cine_finale_key')
    y = np.zeros(secs(0.45))
    for (t, f, a) in ((0.0, 2400, 0.6), (0.17, 1900, 1.0)):
        c = impact(rng, [(f, 1.0, 0.03), (f * 1.7, 0.6, 0.02), (f * 2.9, 0.3, 0.012)], 0.2, hard=0.8)
        place(y, a * c, secs(t), circular=False)
    scrape = noise_burst(0.15, rng, 2000, 8000, 0.15, attack=0.01)
    place(y, 0.12 * norm_peak(scrape), secs(0.02), circular=False)
    return fin(y, -9.0, 0.05)


# ------------------------------------------------------------------------------------------- map / lamps / veil
def pen() -> np.ndarray:
    """A line drawn slowly on paper over 5.6 s: fine scratch with stroke accents."""
    rng = R('cine_finale_pen')
    n = secs(6.0)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = eq(x, ('hp', 1800, 2), ('lp', 7000, 2), circular=False)
    grain = (rng.random(n) < 0.03) * rng.standard_normal(n)
    grain = eq(grain, ('hp', 2500, 2), circular=False)
    env = smoothstep(t / 0.3) * np.clip((5.8 - t) / 0.4, 0, 1)
    wob = 0.65 + 0.35 * np.sin(TAU * 1.3 * t + 0.4) * np.sin(TAU * 0.37 * t)
    y = (0.6 * x + 0.8 * grain) * env * wob
    return fin(to_stereo(y), -18.0, 0.3)


def switch(kind: str) -> np.ndarray:
    rng = R('cine_finale_switch_' + kind)
    if kind == 'b':      # bakelite rotary switch on the architect lamp
        c = impact(rng, [(1900, 1.0, 0.03), (3300, 0.6, 0.02), (850, 0.5, 0.05)], 0.3, hard=0.6)
    else:                # metal toggle on the enamel lamp
        c = impact(rng, [(2700, 1.0, 0.04), (4300, 0.6, 0.025), (1250, 0.5, 0.05)], 0.3, hard=0.85)
    y = np.zeros(secs(1.4))
    place(y, c, 0, circular=False)
    tink = modal([(5200 if kind == 'b' else 4700, 0.08, 0.5), (7300, 0.03, 0.3)], 0.8, seed=int(rng.integers(1 << 30)))
    place(y, tink, secs(0.25), circular=False)
    small = make_ir(length=1.2, rt_low=0.7, rt_high=0.4, predelay=0.005, seed=81 if kind == 'b' else 82)
    return fin(in_room(y, small, 0.22), -6.0, 0.3)


def snowgust() -> np.ndarray:
    rng = R('cine_finale_snowgust')
    n = secs(3.0)
    n -= n % 441
    g = gust_curve(n, rng, [(0.4, 1.0, 0.8, 0.7)], base=0.15, turb=0.05)
    y = wind(n, rng, g, lp_base=400, lp_gust=1600, hush=0.8)
    t = np.arange(n) / SR
    env = smoothstep(t / 0.5) * np.clip((3.0 - t) / 1.2, 0, 1)
    return fin(y * env[:, None], -10.0, 0.3)


# ------------------------------------------------------------------------------------------- room tones (loops)
def room(kind: str) -> np.ndarray:
    rng = R('cine_finale_room_' + kind)
    n = secs(20.0)
    n -= n % 441
    g = gust_curve(n, rng, [(3.0, 0.5, 1.5, 1.6), (11.0, 0.7, 1.2, 2.0), (16.5, 0.4, 1.0, 1.2)], base=0.3, turb=0.07)
    w = wind(n, rng, g, lp_base=260 if kind == 'berlin' else 320, lp_gust=900, whistle=0.25 if kind == 'karsk' else 0.0,
             whistle_f=(640.0, 980.0))
    w = eq(w, ('lp', 2400, 2), circular=True) * 0.55
    ev = np.zeros(n)
    if kind == 'berlin':
        # radiator ticks + a far city hum
        for t0 in (1.7, 4.9, 9.3, 13.8, 18.1):
            c = impact(rng, [(1100, 0.5, 0.02), (2300, 0.3, 0.012)], 0.1, hard=0.5)
            place(ev, 0.25 * c, secs(t0), circular=True)
        t = np.arange(n) / SR
        hum = 0.03 * np.sin(TAU * 50.0 * t) + 0.02 * np.sin(TAU * 100.0 * t)
        ev += hum
    else:
        # stove crackle (sparse pops) + a far buffer bump of shunting wagons
        t = 0.3
        while t < 19.6:
            p = noise_burst(0.02, rng, 700, 6000, 0.01)
            place(ev, rng.uniform(0.05, 0.22) * norm_peak(p), secs(t), circular=True)
            t += rng.exponential(0.35)
        bump = impact(rng, [(55, 1.0, 0.4), (96, 0.6, 0.3), (180, 0.3, 0.2)], 1.2, hard=0.3)
        place(ev, 0.18 * bump, secs(7.5), circular=True)
        place(ev, 0.12 * bump, secs(8.3), circular=True)
    y = w + to_stereo(ev) * 0.8
    y = y - np.mean(y, axis=0)
    return normalize_peak(y, -12.0)


# ------------------------------------------------------------------------------------------- score
def score() -> np.ndarray:
    T = M.Track('cine_finale_score', bpm=60, beats=DUR, loop=False, seed=7101, tail=0.0)
    T.n = secs(DUR)
    # --- Berlin (0 - 13): low G pedal in the brass, Gm(add9) strings, B motif on muted piano
    T.brass(0.0, 13.4, [31, 43], vel=0.30, attack=3.0, release=2.5, bright=0.2, swell=0.3)
    T.strings(0.5, 12.5, [43, 50, 58, 62], vel=0.34, attack=2.6, release=2.6)
    T.piano(M.B_2, vel=0.36, beat0=1.0, felt=0.75, pedal=True, max_len=4.0)
    # --- the snow (12.6 - 16.6): a cold harmonic bridges into D
    T.strings(12.2, 4.6, [86], vel=0.12, stem='strings_hi', harmonic=True, attack=1.4, release=2.0)
    T.strings(14.4, 13.8, [38, 45, 50, 53, 64], vel=0.36, attack=2.2, release=2.8)       # Dm(add9)
    # --- Karsk (16.2 - 28.4): K motif on felt piano, plucked low D
    T.piano(M.K_A, vel=0.40, beat0=17.0, felt=0.6)
    T.pluck([(0, 2, 38), (4, 2, 38), (8, 2, 41)], vel=0.35, beat0=20.5)
    T.piano([(0, 1.5, 74), (1.5, 0.5, 69), (2, 2, 67)], vel=0.34, beat0=25.5, felt=0.65)   # K_B begins ...
    # --- rhyme (28.4 - 34.4): heads answer each other, then together
    T.celesta([(0, 1, 67), (1, 1, 70), (2, 1, 69)], vel=0.36, beat0=28.8)                # B head (Berlin)
    T.piano([(0, 1.5, 74), (1.5, 0.5, 69), (2, 1, 76)], vel=0.36, beat0=30.0)           # K head (Karsk)
    T.celesta([(0, 1, 67), (1, 1, 70)], vel=0.32, beat0=31.0)
    T.piano([(0, 1, 74), (1, 1, 69)], vel=0.32, beat0=31.8)
    T.strings(28.2, 6.6, [43, 50, 57, 62, 69], vel=0.36, attack=2.0, release=2.4)          # Gm9 (shared colour)
    T.piano([(0, 1.5, 74), (1.5, 1.5, 69)], vel=0.34, beat0=32.8, pedal=True)
    T.celesta([(0, 1, 67), (1, 2, 70)], vel=0.32, beat0=32.8)
    # --- the map (33.6 - 41.4): the route is drawn; strings rise Gm(add9)/D -> Bbmaj7/D; heads interleave
    T.strings(34.4, 6.6, [38, 43, 58, 69], vel=0.44, attack=2.0, release=1.4)
    T.strings(40.4, 1.2, [38, 46, 53, 57], vel=0.46, attack=0.6, release=0.5)            # Bbmaj7/D at the arrival
    T.brass(34.8, 6.4, [38, 45], vel=0.30, attack=2.5, release=0.6, bright=0.25, swell=0.5)
    T.piano(M.K_B[:4], vel=0.36, beat0=35.2, felt=0.6)
    T.celesta(M.B_1[:6], vel=0.34, beat0=36.0)
    T.piano([(0, 1.5, 74), (1.5, 2.0, 69)], vel=0.40, beat0=40.4, pedal=True, max_len=1.2)   # the meeting ...
    T.celesta([(0, 1, 67), (1, 2.0, 70)], vel=0.38, beat0=40.4)                           # ... A against Bb
    # --- lamps out (41.4 / 42.2): only the cold harmonic and the low D remain
    T.strings(41.2, 6.2, [88], vel=0.12, stem='strings_hi', harmonic=True, attack=0.8, release=3.0)
    T.strings(42.0, 5.4, [26, 38], vel=0.30, stem='strings_lo', attack=1.2, release=3.0)
    ir = M.hall_ir(7102, rt_low=3.6, rt_high=1.5)
    mix = {'strings': (0.0, 0.32, M.STR_EQ), 'strings_hi': (-12.0, 0.5, M.STR_HI_EQ),
           'strings_lo': (-6.0, 0.3, M.STR_EQ), 'piano': (-0.5, 0.32, M.PIANO_EQ), 'celesta': (-2.5, 0.36, M.CEL_EQ),
           'brass': (-7.0, 0.25, M.BRASS_EQ), 'pluck': (-6.0, 0.25, M.PLUCK_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0, end_fade=2.0)
    # duck everything that still rings after the lamps go out (41.4 s) except the harmonic/low D stems:
    # done in the arrangement (short releases); the master just fades at the end
    return out


# ------------------------------------------------------------------------------------------- build
def build() -> dict:
    os.makedirs(OUT, exist_ok=True)
    files = {
        'cine_finale_tick': tick('tick'), 'cine_finale_tock': tick('tock'), 'cine_finale_telegraph': telegraph(),
        'cine_finale_bell': bell(), 'cine_finale_carriage': carriage(), 'cine_finale_pull': pull(),
        'cine_finale_fold': fold(), 'cine_finale_cloth': cloth(), 'cine_finale_knock': knock(),
        'cine_finale_door_shut': door_shut(), 'cine_finale_pencil': pencil(), 'cine_finale_book': book(),
        'cine_finale_key': key(), 'cine_finale_pen': pen(), 'cine_finale_switch_b': switch('b'),
        'cine_finale_switch_k': switch('k'), 'cine_finale_snowgust': snowgust(),
    }
    for i in range(4):
        files['cine_finale_type_%d' % (i + 1)] = type_key(i)
    loops = {'cine_finale_room_berlin': room('berlin'), 'cine_finale_room_karsk': room('karsk')}
    stats = {}
    for name, x in files.items():
        stats[name] = write_wav(os.path.join(OUT, name + '.wav'), x)
    for name, x in loops.items():
        stats[name] = write_wav(os.path.join(OUT, name + '.wav'), x, loop=(0, len(x)))
    sc = score()
    stats['cine_finale_score'] = write_wav(os.path.join(OUT, 'cine_finale_score.wav'), sc)
    return stats


if __name__ == '__main__':
    st = build()
    for k_, v in sorted(st.items()):
        print(k_, {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()} if isinstance(v, dict) else v)
