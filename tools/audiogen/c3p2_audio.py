"""c3p2_audio.py -- Chapter 3, part 2 ("Der eiserne Frieden": the night, the registry, the archive fire, the quay):
original synthesised sound (documentation/C3P2_DESIGN.md section 8 + the round-8 audio brief).

    py -3 -P tools/audiogen/c3p2_audio.py                          # build all + .import + analysis
    py -3 -P tools/audiogen/c3p2_audio.py --only amb_veltrava_fire # subset (comma separated builder names)
    py -3 -P tools/audiogen/c3p2_audio.py --list                   # what exists and where it is wired
    py -3 -P tools/audiogen/c3p2_audio.py --no-spectro             # skip the spectrogram PNGs

LEVEL AMBIENCES (assets/audio/amb, 60 s stereo loops, ids fixed by the design)
  amb_veltrava_registry  the souterrain at night (L_C3_Registry, scenes A/B): room tone of the old boiler cellar,
                         the city far away, wind and snow at the high windows, radiator ticks and one gurgle,
                         the porter's radio low in the glazed booth (Radio Veltrava's night waltz), the steps of a
                         guard crossing the yard snow above the windows, the house settling, one far train
  amb_veltrava_fire      the registry burning (switch settings of scenes C/D): a breathing roar, crackle, ember
                         hiss, timber groaning and cracking, heat-cracked glass, debris falling far off, the
                         palais' electric fire bell ringing muffled through the walls (in spells), the brigade's hand bell
                         outside once -- dense but even, no stabs, so text and choices stay in front
  amb_veltrava_quay      the riverside quay before dawn (L_C3_Quay): wind over the frozen river, the burning
                         wing far left, the ladder engine's pump idling, hoses, the ice singing and booming, the
                         engine's bell, a second brigade's two-tone horn far across the town
MUSIC (assets/audio/music, loops; the loop point sits in a rest)
  mus_c3p2_fire          tense, not action: a low A pulse that leans on Bb (the Veltrava rub), a slow chromatic
                         rise in the violas, string harmonics flickering, low brass breathing, the V motif broken
                         off -- no drums, no hits (72 bpm, 80 beats, 66.7 s)
  mus_c3p2_halves        quiet, for the quay and the division of the file: the two-language motif V divided --
                         the piano says the first half, the viola the second; then swapped; then the piano alone
                         and the answer does not come (56 bpm, 96 beats, 102.9 s)
SFX (assets/audio/sfx; beds are loops, the rest one-shots)
  c3p2_fire_low / _mid / _high   fire beds in three intensities (20 s stereo loops) for cinematics and layering
  c3p2_roof_creak_1..3   burning timber under load        c3p2_glass_1..3      heat-cracked panes, shards
  c3p2_fire_bell         the ladder engine's bell          c3p2_sirens_far      1964 two-tone horns across the town
  c3p2_yard_night        the snowy yard at night (30 s stereo loop: wind, flakes, the bracket lamp, the town)
  c3p2_radio_waltz       the porter's radio close up (60 s mono loop, the same waltz as in the ambience)
  c3p2_radio_interval    Radio Veltrava's interval signal (the V motif on a music box)  4 s
  c3p2_radio_news_ru / _de  newsreader murmur through the set, two prosody profiles, unintelligible by construction
  c3p2_radio_tune        the dial turning: static, heterodyne whistle, fragments (the match cut of LS_C3_Radio)
  c3p2_note_slide        a folded note sliding under a hotel door
  c3p2_fire_catch        the stacks catching (LS_C3_Fire f2)    c3p2_bolt          the ramp door's iron bolt (f3)
  c3p2_desk_push         the oak desk scraped off the chute     c3p2_door_jam      the jammed 1909 iron door
  c3p2_hatch_open / _slam  the coal hatch in the yard (LS_C3_Escape e2 / e3)
  c3p2_window_burst      the souterrain windows bursting (e4)

Everything reuses dsp / instruments / foley / ambience / music / c3_audio by import (none of them is modified;
build_all.py's registry does not know this module: run this file directly).  Seeds derive from
zlib.crc32(name) (c3_audio.seed_of), so every run is bit-identical.  Unintelligible voices only (prosody
profiles over random vowel targets): no words, no real broadcast, no real anthem, no real siren recording.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

from dsp import (SR, TAU, secs, eq, fftconv, place, pan2, smooth_periodic, shaped_noise, mag_bp, rms,  # noqa: E402
                 db2a, smoothstep, make_ir, soft_clip, fade, midi_hz, write_wav, limiter, normalize_rms,
                 normalize_peak, remove_dc, to_stereo, glue, width)
from instruments import (impact, random_modes, noise_burst, ctrl_noise, modal, bell_modes,  # noqa: E402
                         celesta_note)
from foley import (wind, gust_curve, footstep, creak_train, norm_peak, bump, ir_outdoor_far,  # noqa: E402
                   ir_small, grain_cloud, paper_rustle, far_horn, horn)
from ambience import Mix, N, active_rms, periodic_tone  # noqa: E402
from music import Track, hall_ir, STR_EQ, STR_HI_EQ, BRASS_EQ, MUTED_EQ, CEL_EQ  # noqa: E402
import c3_audio as C3A  # noqa: E402  (far, voice, radiator_gurgle, motif V, analysis helpers)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AUDIO = os.path.join(ROOT, 'assets', 'audio')
seed_of = C3A.seed_of
far = C3A.far


def R(name: str, k: int = 0) -> np.random.Generator:
    return np.random.default_rng(seed_of(name, k))


def ev(x: np.ndarray) -> np.ndarray:
    """Peak-normalised mono/stereo event."""
    p = float(np.max(np.abs(x)))
    return x / p if p > 0 else x


def one_shot(x: np.ndarray, peak_db: float, fin: float = 0.002, fout: float = 0.08, stereo: bool = True) -> np.ndarray:
    y = to_stereo(x) if stereo else (x.mean(axis=1) if x.ndim == 2 else x)
    y = remove_dc(y, circular=False)
    y = fade(y, fin, fout)
    return limiter(normalize_peak(y, peak_db), peak_db + 0.3)


def loop_master(x: np.ndarray, target: float, ceiling: float = -3.0, lp: float = 13000.0, hp: float = 24.0) -> np.ndarray:
    y = eq(x, ('hp', hp, 2), ('lp', lp, 2), circular=True)
    y = remove_dc(y, circular=True)
    y = normalize_rms(y, target)
    return limiter(y, ceiling, circular=True)


def radio_set(x: np.ndarray, rng: np.random.Generator, lo: float = 320.0, hi: float = 3300.0, drive: float = 1.8,
              static: float = 0.018, hum: float = 0.006, circular: bool = False) -> np.ndarray:
    """A 1950s valve set: mono, small speaker (band-limited, a cabinet bump), soft valve saturation, a little
    static and mains hum.  Returns mono."""
    m = x.mean(axis=1) if x.ndim == 2 else np.asarray(x, float)
    n = len(m)
    y = eq(m, ('hp', lo, 4), ('lp', hi, 4), ('bell', 1150.0, 3.5, 1.0), ('bell', 520.0, 2.0, 0.8),
           circular=circular)
    y = soft_clip(y / max(float(np.max(np.abs(y))), 1e-9) * 0.9, drive)
    if circular:
        hiss = shaped_noise(n, rng, lambda f: mag_bp(f, 1800.0, 6000.0, 2))
        h50 = 0.6 * periodic_tone(n, 50.0, rng) + 0.3 * periodic_tone(n, 100.0, rng)
    else:
        hiss = eq(rng.standard_normal(n), ('hp', 1800.0, 2), ('lp', 6000.0, 2), circular=False)
        hiss /= max(rms(hiss), 1e-9)
        t = np.arange(n) / SR
        h50 = 0.6 * np.sin(TAU * 50.0 * t) + 0.3 * np.sin(TAU * 100.0 * t)
    return y + static * hiss * (1.0 + 0.5 * np.abs(ctrl_noise(n, 9.0, rng))) + hum * h50


# =============================================================================== shared sources
def fire_bed(rng: np.random.Generator, n: int, k: float) -> np.ndarray:
    """Circular stereo fire of intensity k (0.2 smouldering .. 1.0 a room in flames): a breathing low roar, a
    gusty mid 'whoosh', ember hiss, crackle (rate grows with k) and pops with a short wooden resonance."""
    T = n / SR
    roar = shaped_noise(n, rng, lambda f: mag_bp(f, 32.0, 220.0 + 320.0 * k, 2), ch=2, corr=0.55)
    roar *= (1.0 + (0.22 + 0.18 * k) * smooth_periodic(n, max(3, int(T * 0.8)), rng))[:, None]
    wh = shaped_noise(n, rng, lambda f: mag_bp(f, 260.0, 1500.0 + 900.0 * k, 2), ch=2, corr=0.3)
    wh *= np.clip(0.55 + 0.55 * smooth_periodic(n, max(3, int(T * 1.6)), rng), 0.04, None)[:, None]
    hiss = shaped_noise(n, rng, lambda f: mag_bp(f, 2400.0, 7800.0, 2), ch=2, corr=0.2)
    hiss *= (0.55 + 0.45 * np.abs(smooth_periodic(n, max(3, int(T * 3)), rng)))[:, None]
    crk = np.zeros((n, 2))
    rate = 2.5 + 20.0 * k ** 1.3
    t = rng.uniform(0.0, 0.3)
    while t < T:
        if rng.random() < 0.05 + 0.10 * k:
            e = impact(rng, random_modes(rng, 520.0, 4200.0, 5, 0.006, 0.04), 0.1, hard=0.8, noise_amt=0.9,
                       noise_decay=0.004)
            a = rng.uniform(1.2, 2.6)
        else:
            e = noise_burst(rng.uniform(0.002, 0.009), rng, 900.0, 9500.0, rng.uniform(0.0006, 0.003), attack=0.0002)
            a = rng.uniform(0.2, 1.0) ** 2 * 1.3
        place(crk, pan2(ev(e) * a, rng.uniform(-0.55, 0.55)), secs(t), circular=True)
        t += rng.exponential(1.0 / rate)
    # sap: short whistling squeals in the hotter fires
    for _ in range(int(T * 0.25 * k)):
        L = rng.uniform(0.25, 0.7)
        m = secs(L)
        tt = np.arange(m) / SR
        f = rng.uniform(1900.0, 3400.0) * (1.0 + 0.08 * np.sin(TAU * rng.uniform(3, 7) * tt))
        sq = np.sin(TAU * np.cumsum(f) / SR) * np.sin(np.pi * tt / L) ** 2 * 0.25
        place(crk, pan2(sq, rng.uniform(-0.5, 0.5)), secs(rng.uniform(0, T)), circular=True)
    # every stem at unit RMS, mixed in dB: crackle-led when smouldering, roar-led when the room is ablaze
    crk /= max(rms(crk), 1e-12)
    y = (db2a(-15.0 + 15.0 * k) * roar + db2a(-30.0 + 24.0 * k) * wh + db2a(-19.0 + 4.0 * k) * hiss +
         db2a(-3.5 - 3.0 * k) * crk)
    return eq(y, ('hp', 28.0, 2), ('lp', 11000.0, 2), circular=True)


def timber_groan(rng: np.random.Generator, dur: float, low: bool = True) -> np.ndarray:
    """Burning timber under load: stick-slip creak through wooden resonances + a slowly gliding groan. Mono."""
    base = rng.uniform(70.0, 110.0) if low else rng.uniform(140.0, 220.0)
    modes = [(base * r, rng.uniform(0.04, 0.09), a) for r, a in ((1.0, 1.0), (2.31, 0.6), (3.9, 0.35), (6.2, 0.2))]
    c = creak_train(rng, dur, rng.uniform(5.0, 9.0), rng.uniform(11.0, 18.0), modes, jitter=0.35)
    n = len(c)
    tt = np.arange(n) / SR
    f = base * 1.5 * (1.0 + 0.12 * np.sin(np.pi * tt / dur) + 0.02 * ctrl_noise(n, 3.0, rng))
    g = np.sin(TAU * np.cumsum(f) / SR) + 0.4 * np.sin(TAU * np.cumsum(2.02 * f) / SR)
    g = eq(g * (0.3 + 0.7 * np.abs(ctrl_noise(n, 6.0, rng))), ('lp', 900.0, 2), circular=False)
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 0.8
    return ev(ev(c) + 0.35 * ev(g)) * env


def wood_crack(rng: np.random.Generator) -> np.ndarray:
    """A beam splitting: sharp crack, a splintering tail and a few falling pieces. Mono, ~1.6 s."""
    out = np.zeros(secs(1.8))
    c = impact(rng, random_modes(rng, 180.0, 2600.0, 8, 0.02, 0.12), 0.5, hard=0.95, noise_amt=1.2,
               noise_decay=0.012)
    place(out, ev(c), 0, circular=False)
    spl = noise_burst(0.5, rng, 600.0, 7000.0, 0.25, attack=0.004)
    place(out, 0.3 * ev(spl * (0.4 + 0.6 * np.abs(ctrl_noise(len(spl), 40.0, rng)))), secs(0.02), circular=False)
    for i in range(int(rng.integers(3, 6))):
        k = impact(rng, random_modes(rng, 150.0, 1800.0, 4, 0.02, 0.08), 0.25, hard=0.5, noise_amt=0.6)
        place(out, rng.uniform(0.15, 0.4) * ev(k), secs(0.35 + 0.18 * i + rng.uniform(0, 0.1)), circular=False)
    return out


def glass_crack(rng: np.random.Generator, shards: int = 9, fall: float = 0.55) -> np.ndarray:
    """A pane cracking in the heat (two tight ticks, a split) and shards falling onto stone. Mono."""
    out = np.zeros(secs(2.6))
    for i, t0 in enumerate((0.0, rng.uniform(0.05, 0.12))):
        tk = impact(rng, random_modes(rng, 2500.0, 9000.0, 6, 0.004, 0.02), 0.08, hard=1.0, noise_amt=0.5,
                    noise_lo=3000.0, noise_hi=12000.0, noise_decay=0.0015)
        place(out, (0.55 if i == 0 else 1.0) * ev(tk), secs(t0), circular=False)
    for i in range(shards):
        sh = impact(rng, random_modes(rng, 1800.0, 9500.0, 5, 0.02, 0.18), 0.4, hard=0.9, noise_amt=0.25)
        t0 = fall + rng.exponential(0.22) + 0.04 * i
        place(out, rng.uniform(0.15, 0.6) * ev(sh), secs(t0), circular=False)
    return eq(out, ('hp', 500.0, 2), circular=False)


def alarm_bell(rng: np.random.Generator, n: int, rate: float = 17.0) -> np.ndarray:
    """An electric fire-alarm bell (hammer at `rate` Hz on a steel gong), circular, mono."""
    gong = modal([(1180.0, 1.0, 0.7), (1180.0 * 2.76, 0.5, 0.35), (1180.0 * 5.4, 0.25, 0.18), (640.0, 0.3, 0.5)],
                 0.6, seed=int(rng.integers(1 << 30)))
    imp = np.zeros(n)
    per = SR / rate
    k = np.arange(int(n / per))
    imp[(k * per).astype(int) % n] = 0.8 + 0.2 * rng.random(len(k))
    return fftconv(imp, gong, circular=True)


def hand_bell(rng: np.random.Generator, strikes: int, rate: float = 2.4, f1: float = 610.0) -> np.ndarray:
    """The ladder engine's brass bell rung by hand (uneven strikes, the clapper sometimes doubling). Mono."""
    out = np.zeros(secs(strikes / rate + 2.4))
    t = 0.0
    modes = bell_modes(f1, 'church')
    for i in range(strikes):
        b = modal([(f * rng.uniform(0.997, 1.003), a, T60 * 0.8) for f, a, T60 in modes], 2.2,
                  seed=int(rng.integers(1 << 30)))
        b[:secs(0.004)] *= np.linspace(0.3, 1.0, secs(0.004))
        place(out, rng.uniform(0.75, 1.0) * ev(b), secs(t), circular=False)
        if rng.random() < 0.3:
            place(out, 0.35 * ev(b), secs(t + 0.07), circular=False)
        t += (1.0 / rate) * rng.uniform(0.85, 1.15)
    return out


def two_tone(rng: np.random.Generator, dur: float, f_lo: float = 438.0, f_hi: float = 586.0, period: float = 1.3,
             approach: float = 0.5) -> np.ndarray:
    """A brigade's pneumatic two-tone horn of the period (a fourth, alternating; generic, not a brand) with a
    slow Doppler drift as it passes far away. Mono, dry."""
    n = secs(dur)
    tt = np.arange(n) / SR
    which = (np.floor(tt / (period / 2.0)) % 2).astype(bool)
    f = np.where(which, f_hi, f_lo).astype(float)
    k = int(secs(0.05))
    f = np.convolve(np.pad(f, (k, k), mode='edge'), np.ones(k) / k, mode='same')[k:-k]
    dop = 1.0 + 0.018 * np.tanh((approach * dur - tt) / (0.18 * dur))
    f = f * dop * (1.0 + 0.003 * ctrl_noise(n, 3.0, rng))
    ph = np.cumsum(f) / SR
    y = np.zeros(n)
    for h in range(1, 14):
        amp = h ** -1.0 * (1.0 + 1.4 * np.exp(-0.5 * (np.log2(h * 500.0 / 1300.0) / 0.5) ** 2))
        y += amp * np.sin(TAU * h * ph + rng.uniform(0, TAU))
    y += 0.05 * eq(rng.standard_normal(n), ('hp', 400.0, 2), ('lp', 3000.0, 2), circular=False)
    return ev(y) * (smoothstep(np.clip(tt / 0.4, 0, 1)) * smoothstep(np.clip((dur - tt) / 0.6, 0, 1)))


def ice_sing(rng: np.random.Generator) -> np.ndarray:
    """Lake/river ice under tension: the dispersive 'pew' (a falling chirp) and a low boom under it. Mono."""
    L = rng.uniform(0.35, 0.7)
    n = secs(L + 0.6)
    tt = np.arange(n) / SR
    f0, f1 = rng.uniform(2600.0, 4200.0), rng.uniform(260.0, 480.0)
    f = f1 + (f0 - f1) * np.exp(-tt / (L * 0.28))
    chirp = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-tt / (L * 0.55)) * smoothstep(np.clip(tt / 0.004, 0, 1))
    boom = eq(rng.standard_normal(n), ('lp', 120.0, 4), ('hp', 25.0, 2), circular=False)
    boom = ev(boom) * np.exp(-tt / 0.35) * smoothstep(np.clip(tt / 0.02, 0, 1))
    tick = noise_burst(0.02, rng, 2000.0, 9000.0, 0.006)
    out = 0.8 * ev(chirp) + 0.6 * boom
    out[:len(tick)] += 0.3 * ev(tick)
    return out


def snow_steps(rng: np.random.Generator, steps: int, interval: float, p0: float, p1: float) -> np.ndarray:
    out = np.zeros((secs(steps * interval * 1.1 + 0.8), 2))
    t = 0.0
    for i in range(steps):
        s = footstep(rng, 'snow', weight=1.0)
        place(out, pan2(ev(s) * (0.85 if i % 2 else 1.0), p0 + (p1 - p0) * i / max(1, steps - 1)), secs(t),
              circular=False)
        t += interval * (1.0 + rng.normal(0.0, 0.03))
    return out


def ir_registry(seed: int) -> np.ndarray:
    """Vaulted souterrain: brick vaults, oak cabinets and paper (dense, darker than the palais foyer)."""
    return make_ir(length=2.2, rt_low=1.5, rt_high=0.55, predelay=0.012, er_taps=14, er_span=0.05, er_gain=0.4,
                   seed=seed, lowcut=60.0, highcut=6500.0, build=0.01)


def ir_quay(seed: int) -> np.ndarray:
    """The river: open, long, a slap off the palais wall and one off the far bank."""
    return make_ir(length=4.5, rt_low=2.6, rt_high=0.9, predelay=0.03, er_taps=5, er_span=0.08, er_gain=0.14,
                   seed=seed, lowcut=50.0, highcut=5200.0, build=0.03,
                   slap=[(0.22, 0.42, 2600.0), (0.61, 0.30, 1800.0), (1.35, 0.22, 1200.0), (2.4, 0.12, 900.0)])


# =============================================================================== the night waltz
# Radio Veltrava's night programme: an original salon waltz in F (48 bars of 3/4 = 144 beats = 60.0 s at 144 bpm),
# A (16) B in D minor (16) A (16).  Melody: (beat-in-bar, beats, midi); chords: bass + off-beat voicing.
WALTZ_A = [
    [(0, 3, 72)], [(0, 1, 69), (1, 1, 72), (2, 1, 77)], [(0, 3, 76)], [(0, 1, 74), (1, 1, 72), (2, 1, 70)],
    [(0, 3, 67)], [(0, 1, 70), (1, 1, 74), (2, 1, 79)], [(0, 2, 77), (2, 1, 76)], [(0, 3, 77)],
    [(0, 3, 72)], [(0, 1, 69), (1, 1, 72), (2, 1, 75)], [(0, 3, 74)], [(0, 1, 70), (1, 1, 74), (2, 1, 77)],
    [(0, 2, 81), (2, 1, 77)], [(0, 2, 79), (2, 1, 76)], [(0, 3, 77)], [(0, 2, 65)],
]
WALTZ_B = [
    [(0, 3, 74)], [(0, 1, 77), (1, 1, 76), (2, 1, 74)], [(0, 3, 73)], [(0, 1, 76), (1, 1, 79), (2, 1, 76)],
    [(0, 3, 77)], [(0, 1, 74), (1, 1, 69), (2, 1, 74)], [(0, 2, 79), (2, 1, 77)], [(0, 2, 76), (2, 1, 70)],
    [(0, 3, 69)], [(0, 1, 72), (1, 1, 77), (2, 1, 81)], [(0, 3, 79)], [(0, 1, 76), (1, 1, 72), (2, 1, 70)],
    [(0, 3, 69)], [(0, 1, 66), (1, 1, 69), (2, 1, 72)], [(0, 2, 70), (2, 1, 76)], [(0, 3, 77)],
]
CH = {'F': (41, [57, 60, 65]), 'C7': (48, [58, 60, 64]), 'F7': (41, [57, 63, 65]), 'Bb': (46, [58, 62, 65]),
      'Dm': (50, [57, 62, 65]), 'A7': (45, [55, 61, 64]), 'G7': (43, [55, 59, 65]), 'D7': (50, [57, 60, 66]),
      'Gm': (43, [55, 58, 62]), 'FC': (48, [57, 60, 65])}
CHORDS_A = ['F', 'F', 'C7', 'C7', 'C7', 'C7', 'F', 'F', 'F', 'F7', 'Bb', 'Bb', 'FC', 'C7', 'F', 'F']
CHORDS_B = ['Dm', 'Dm', 'A7', 'A7', 'Dm', 'Dm', 'G7', 'C7', 'F', 'F', 'C7', 'C7', 'F', 'D7', 'Gm', 'F']


def night_waltz() -> np.ndarray:
    """The studio recording (stereo, 60 s circular) before it goes through anybody's radio."""
    name = 'c3p2_night_waltz'
    T = Track(name, bpm=144, beats=144, loop=True, seed=seed_of(name))
    bars = list(zip(WALTZ_A, CHORDS_A)) + list(zip(WALTZ_B, CHORDS_B)) + list(zip(WALTZ_A, CHORDS_A))
    for i, (mel, ch) in enumerate(bars):
        b0 = 3 * i
        bass, voicing = CH[ch]
        T.piano([(b0, 1, bass)], vel=0.42, stem='bass', felt=0.4, decay=0.7, legato=0.9)
        for off in (1, 2):
            T.piano([(b0 + off, 1, m) for m in voicing], vel=0.26, stem='comp', felt=0.5, decay=0.5, legato=0.6)
        for (b, d, m) in mel:
            T.strings(b0 + b, d * 0.95, [m], vel=0.42, stem='violin', attack=0.09, release=0.45, bright=0.55,
                      voices=2, vib=7.0, pan=0.1)
            if i % 16 >= 8:      # second half of every period: the piano doubles the tune an octave lower
                T.piano([(b0 + b, d, m - 12)], vel=0.22, stem='double', felt=0.55, decay=0.8)
    ir = hall_ir(seed_of(name, 1), rt_low=1.6, rt_high=0.8, predelay=0.02)
    mix = {'bass': (-2.0, 0.15, ()), 'comp': (-6.0, 0.2, ()), 'violin': (0.0, 0.25, STR_EQ),
           'double': (-9.0, 0.2, ())}
    return T.mixdown(mix, ir, target_rms=-20.0, master_lp=9000.0)


# =============================================================================== ambiences
def amb_veltrava_registry():
    name = 'amb_veltrava_registry'
    rng = R(name)
    M = Mix()
    # room tone of the old boiler cellar: air, a faint 50 Hz transformer hum, the city far above
    air = shaped_noise(N, rng, lambda f: mag_bp(f, 40.0, 900.0, 2) * (np.maximum(f, 20.0) / 100.0) ** -0.4, ch=2,
                       corr=0.5)
    M.bed(air, -6.0)
    hum = np.stack([periodic_tone(N, 50.0, rng) + 0.5 * periodic_tone(N, 100.0, rng) +
                    0.2 * periodic_tone(N, 150.0, rng)] * 2, axis=1)
    M.bed(hum, -21.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 25.0, 170.0, 2), ch=2, corr=0.7)
    city *= (1.0 + 0.3 * smooth_periodic(N, 10, rng))[:, None]
    M.bed(city, -10.0)
    # wind and snow at the high windows (through glass: dull, a thin whistle in the frames)
    g = gust_curve(N, rng, [(4.0, 0.7, 1.5, 2.5), (21.0, 0.9, 2.0, 3.0), (39.5, 0.6, 1.2, 2.0), (52.0, 1.0, 2.5, 3.5)],
                   base=0.3, turb=0.07)
    w = wind(N, rng, g, lp_base=220.0, lp_gust=700.0, whistle=0.25, whistle_f=(640.0, 980.0), corr=0.3)
    M.bed(w, -9.0)
    flakes = grain_cloud(rng, N / SR, np.full(N, 9.0), 3500.0, 9000.0, 0.001, 0.003)
    M.bed(np.stack([flakes, np.roll(flakes, secs(1.7))], axis=1), -26.0)
    # the porter's radio in the glazed booth: the night waltz, small speaker, booth glass, from the left
    waltz = radio_set(night_waltz(), rng, lo=380.0, hi=2900.0, drive=1.5, static=0.02, hum=0.004, circular=True)
    booth = fftconv(pan2(waltz, -0.35), ir_small(seed_of(name, 2)), circular=True)
    M.bed(0.6 * pan2(waltz, -0.35) + booth, -11.0)
    # radiator: expansion ticks (iron) and one long gurgle
    room = ir_registry(seed_of(name, 3))
    for t in (2.3, 6.1, 6.4, 11.8, 17.2, 25.0, 29.4, 34.7, 44.1, 44.35, 49.9, 57.3):
        tk = impact(rng, random_modes(rng, 1600.0, 5200.0, 5, 0.01, 0.05), 0.15, hard=0.75, noise_amt=0.3)
        M.event(far(tk, room, wet=0.35, dry=1.0, pan=rng.uniform(-0.2, 0.6)), t, -9.0 + rng.uniform(-3, 2),
                mode='peak')
    M.event(far(C3A.radiator_gurgle(rng, 2.6), room, wet=0.4, dry=1.0, pan=0.45), 31.2, -13.0)
    # a guard crosses the yard above the windows (muffled crunching from left to right)
    steps = snow_steps(rng, 9, 0.62, -0.7, 0.7)
    steps = eq(steps, ('lp', 1600.0, 2), ('hp', 90.0, 2), circular=False)
    M.event(steps, 37.6, -12.0)
    # the house settles: oak cabinets, the ladder rail
    for t, lowf in ((14.6, True), (47.2, False)):
        M.event(far(timber_groan(rng, 1.4, low=lowf), room, wet=0.4, dry=1.0, pan=rng.uniform(-0.3, 0.3)), t, -15.0)
    # one far train from the station (the 0.52 goods train)
    M.event(far_horn(rng, 311.0, 1.6, chord=(1.0, 1.26)) * 0.5, 22.4, -16.0)
    return M.master(-26.0, lp=11500.0), (0, N)


def amb_veltrava_fire():
    name = 'amb_veltrava_fire'
    rng = R(name)
    M = Mix()
    room = ir_registry(seed_of(name, 1))
    M.bed(eq(fire_bed(rng, N, 0.62), ('bell', 3000.0, -4.0, 1.3), circular=True), 0.0)
    # the palais' electric fire bell, two floors up and through brick: low, steady, never sharp
    bell = alarm_bell(rng, N)
    bell = eq(bell, ('lp', 650.0, 4), ('hp', 180.0, 2), circular=True)
    bell *= (1.0 + 0.35 * smooth_periodic(N, 6, rng))
    ph = np.arange(N) % secs(15.0)                    # it rings in 10-s spells with 5-s pauses (4 per loop)
    bell *= np.clip(np.minimum(ph / secs(0.08), (secs(10.0) - ph) / secs(0.08)), 0.0, 1.0)
    M.bed(np.stack([bell, np.roll(bell, secs(0.013))], axis=1), -21.0)
    # timber groaning in the heat, beams cracking, debris far off
    for t, lowf, rel in ((5.2, True, -6.0), (18.9, False, -8.0), (31.7, True, -5.0), (46.3, False, -8.0),
                         (55.0, True, -7.0)):
        M.event(far(timber_groan(rng, rng.uniform(1.6, 2.6), low=lowf), room, wet=0.45, dry=1.0,
                    pan=rng.uniform(-0.5, 0.5)), t, rel)
    for t, pan in ((24.6, 0.5), (50.8, -0.35)):
        M.event(far(wood_crack(rng), room, wet=0.5, dry=1.0, pan=pan, lp=5200.0), t, 2.0)
    for t in (9.8, 38.4):
        thud = eq(noise_burst(0.6, rng, 30.0, 300.0, 0.25, attack=0.003), ('lp', 260.0, 2), circular=False)
        M.event(far(ev(thud), room, wet=0.6, dry=0.8, pan=rng.uniform(-0.4, 0.4)), t, -3.0)
    # heat-cracked panes of the high windows / a framed plan
    for t, pan, rel in ((14.0, 0.55, -2.0), (42.9, -0.5, 0.0)):
        M.event(far(glass_crack(rng, shards=7), room, wet=0.4, dry=1.0, pan=pan), t, rel)
    # the brigade's hand bell outside, muffled by the walls (they are coming)
    hb = eq(hand_bell(rng, 7, rate=2.3), ('lp', 1400.0, 2), ('hp', 250.0, 2), circular=False)
    M.event(far(hb, ir_outdoor_far(seed_of(name, 2)), wet=0.8, dry=0.3, pan=-0.6), 27.5, -12.0)
    out = M.master(-22.5, lp=11500.0)
    return glue(out, -22.5 + 5.0, ratio=1.8, circular=True), (0, N)


def amb_veltrava_quay():
    name = 'amb_veltrava_quay'
    rng = R(name)
    M = Mix()
    riv = ir_quay(seed_of(name, 1))
    g = gust_curve(N, rng, [(6.0, 0.9, 2.0, 3.0), (19.5, 0.6, 1.5, 2.0), (33.0, 1.1, 2.5, 4.0), (49.0, 0.8, 2.0, 3.0)],
                   base=0.4, turb=0.09)
    M.bed(wind(N, rng, g, lp_base=320.0, lp_gust=1300.0, whistle=0.0, hush=0.08, corr=0.25, pan_sweep=0.35), 0.0)
    # the burning wing, far left: low roar and a far crackle that the wind carries
    fire = fire_bed(rng, N, 0.85)
    fire = eq(fire, ('lp', 1500.0, 2), circular=True)
    fire[:, 1] *= 0.45
    M.bed(fire, -6.0)
    # the ladder engine's pump idling (left of centre), hoses hissing
    tt = np.arange(N) / SR
    ph = np.cumsum(np.full(N, 31.5)) / SR
    pump = sum((1.0 / h) * np.sin(TAU * h * ph * (round(31.5 * N / SR) / (31.5 * N / SR)) + rng.uniform(0, TAU))
               for h in range(1, 9))
    pump = eq(pump * (1.0 + 0.15 * smooth_periodic(N, 30, rng)), ('lp', 420.0, 2), circular=True)
    M.bed(pan2(pump, -0.45), -15.0)
    spray = shaped_noise(N, rng, lambda f: mag_bp(f, 900.0, 6000.0, 2), ch=2, corr=0.4)
    spray *= np.clip(0.6 + 0.5 * smooth_periodic(N, 12, rng), 0.1, None)[:, None]
    spray[:, 1] *= 0.6
    M.bed(spray, -25.0)
    # the river ice sings and booms
    for t, pan, rel in ((3.4, 0.3, -6.0), (12.9, 0.6, -9.0), (26.1, 0.1, -5.0), (27.0, 0.5, -11.0), (41.8, 0.7, -7.0),
                        (53.3, 0.2, -8.0)):
        M.event(far(ice_sing(rng), riv, wet=0.5, dry=1.0, pan=pan, lp=6000.0), t, rel)
    # the engine's bell (someone rings it to clear the bridge), and a second brigade's horn across the town
    hb = hand_bell(rng, 6, rate=2.6, f1=640.0)
    M.event(far(hb, riv, wet=0.55, dry=0.6, pan=-0.5, lp=4500.0), 16.8, -8.0)
    sir = eq(two_tone(rng, 11.0, approach=0.55), ('lp', 1700.0, 2), ('hp', 250.0, 2), circular=False)
    M.event(far(sir, ir_outdoor_far(seed_of(name, 2)), wet=0.9, dry=0.15, pan=0.55), 35.0, -12.0)
    # firemen's boots on the snow, a hose coupling knocked (left)
    M.event(eq(snow_steps(rng, 6, 0.55, -0.6, -0.3), ('lp', 2500.0, 2), circular=False), 23.3, -14.0)
    knock = impact(rng, random_modes(rng, 400.0, 3500.0, 6, 0.03, 0.2), 0.6, hard=0.7)
    M.event(far(knock, riv, wet=0.5, dry=1.0, pan=-0.5), 45.6, -6.0, mode='peak')
    return M.master(-24.0, lp=9500.0), (0, N)


# =============================================================================== fire beds / yard
def _fire_loop(name: str, k: float, target: float):
    n = secs(20.0)
    y = fire_bed(R(name), n, k)
    return loop_master(y, target, ceiling=-3.0), (0, n)


def c3p2_fire_low():
    return _fire_loop('c3p2_fire_low', 0.22, -31.0)


def c3p2_fire_mid():
    return _fire_loop('c3p2_fire_mid', 0.6, -25.0)


def c3p2_fire_high():
    return _fire_loop('c3p2_fire_high', 1.0, -21.0)


def c3p2_yard_night():
    name = 'c3p2_yard_night'
    rng = R(name)
    n = secs(30.0)
    M = Mix(n)
    g = gust_curve(n, rng, [(5.0, 0.6, 1.5, 2.0), (18.0, 0.8, 2.0, 2.5)], base=0.32, turb=0.06)
    M.bed(wind(n, rng, g, lp_base=260.0, lp_gust=900.0, whistle=0.15, whistle_f=(700.0, 1050.0), hush=0.06), 0.0)
    city = shaped_noise(n, rng, lambda f: mag_bp(f, 25.0, 160.0, 2), ch=2, corr=0.7)
    M.bed(city, -8.0)
    lamp = np.stack([0.7 * periodic_tone(n, 100.0, rng) + 0.3 * periodic_tone(n, 200.0, rng)] * 2, axis=1)
    M.bed(pan2(lamp[:, 0], 0.3), -26.0)
    flakes = grain_cloud(rng, n / SR, np.full(n, 14.0), 4000.0, 9500.0, 0.001, 0.003)
    M.bed(np.stack([flakes, np.roll(flakes, secs(0.9))], axis=1), -29.0)
    M.event(far_horn(rng, 311.0, 1.4, chord=(1.0, 1.26)) * 0.5, 11.0, -14.0)
    return M.master(-27.0, lp=9000.0), (0, n)


# =============================================================================== radio
def c3p2_radio_waltz():
    name = 'c3p2_radio_waltz'
    rng = R(name)
    y = radio_set(night_waltz(), rng, lo=330.0, hi=3400.0, drive=1.6, static=0.016, hum=0.005, circular=True)
    y = fftconv(y, ir_small(seed_of(name, 1)).mean(axis=1), circular=True) * 0.35 + y
    return loop_master(y, -24.0, ceiling=-4.0, hp=60.0, lp=7000.0), (0, len(y))


def c3p2_radio_interval():
    """Radio Veltrava's interval signal: the city's two-language motif V (E C B A . E) on a music box, twice,
    the second time ending on the open note. 4.0 s."""
    name = 'c3p2_radio_interval'
    rng = R(name)
    n = secs(4.0)
    out = np.zeros((n, 2))
    beat = 0.27
    seq = [(0, 76), (1, 84), (1.5, 83), (2, 81), (3.5, 76), (5, 76), (6, 84), (6.5, 83), (7, 81), (8.5, 76)]
    for b, m in seq:
        c = celesta_note(m, vel=0.55, seed=int(rng.integers(1 << 30)), pan=0.0, bright=0.6)
        place(out, c, secs(0.12 + b * beat), circular=False)
    y = radio_set(out, rng, lo=420.0, hi=3600.0, drive=1.4, static=0.03, hum=0.004)
    y = fade(y, 0.005, 0.5)
    return one_shot(y, -8.0, stereo=False), None


def _news(name: str, f0: float, prof: str):
    rng = R(name)
    dur = 6.5
    v = C3A.voice(rng, dur, f0, prof, pause=(0.22, 0.55), phrase=(1.4, 2.6))
    studio = make_ir(length=0.5, rt_low=0.3, rt_high=0.18, predelay=0.003, er_taps=8, er_span=0.015, er_gain=0.4,
                     seed=seed_of(name, 1))
    v = v + 0.15 * fftconv(v, studio.mean(axis=1), circular=False)[:len(v)]
    y = radio_set(v, rng, lo=300.0, hi=3400.0, drive=1.5, static=0.022, hum=0.004)
    return one_shot(fade(y, 0.05, 0.4), -9.0, stereo=False), None


def c3p2_radio_news_ru():
    return _news('c3p2_radio_news_ru', 104.0, 'even')


def c3p2_radio_news_de():
    return _news('c3p2_radio_news_de', 112.0, 'clipped')


def c3p2_radio_tune():
    """The tuning dial: static rushing, a heterodyne whistle sliding through, two half-syllables of other
    stations, then the carrier settles. 1.4 s."""
    name = 'c3p2_radio_tune'
    rng = R(name)
    n = secs(1.4)
    tt = np.arange(n) / SR
    st = eq(rng.standard_normal(n), ('hp', 600.0, 2), ('lp', 5500.0, 2), circular=False)
    st = ev(st) * (0.35 + 0.65 * np.abs(ctrl_noise(n, 25.0, rng))) * np.clip(1.15 - tt / 1.2, 0.0, 1.0)
    f = 2600.0 * np.exp(-tt / 0.35) + 450.0 + 900.0 * smoothstep(np.clip((tt - 0.55) / 0.4, 0, 1))
    wh = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-((tt - 0.45) / 0.35) ** 2)
    frag = np.zeros(n)
    for t0, f0, prof in ((0.18, 130.0, 'lilt'), (0.62, 180.0, 'slow')):
        v = C3A.voice(rng, 0.35, f0, prof, pause=(0.05, 0.1), phrase=(0.2, 0.3))
        place(frag, ev(v) * np.hanning(len(v)), secs(t0), circular=False)
    y = radio_set(0.5 * st + 0.35 * wh + 0.4 * frag, rng, lo=350.0, hi=4000.0, drive=1.3, static=0.0, hum=0.003)
    return one_shot(fade(y, 0.01, 0.15), -10.0, stereo=False), None


# =============================================================================== cinematic / scene one-shots
def c3p2_note_slide():
    """A folded note pushed under a hotel-room door: paper over the threshold, a soft stop. 1.1 s."""
    name = 'c3p2_note_slide'
    rng = R(name)
    n = secs(1.1)
    tt = np.arange(n) / SR
    fr = eq(rng.standard_normal(n), ('hp', 1500.0, 2), ('lp', 7500.0, 2), ('bell', 3200.0, 4.0, 1.0),
            circular=False)
    env = smoothstep(np.clip(tt / 0.12, 0, 1)) * np.clip(1.0 - (tt - 0.15) / 0.55, 0.0, 1.0) ** 1.5
    fr = ev(fr) * env * (0.7 + 0.3 * np.abs(ctrl_noise(n, 30.0, rng)))
    rus = paper_rustle(rng, 0.4, 0.35, 1)
    out = 0.8 * fr
    place(out, 0.4 * ev(rus), secs(0.55), circular=False)
    tap = impact(rng, random_modes(rng, 300.0, 2500.0, 4, 0.01, 0.04), 0.1, hard=0.3, noise_amt=0.4)
    place(out, 0.25 * ev(tap), secs(0.7), circular=False)
    return one_shot(in_room(out, R(name, 1)), -12.0), None


def in_room(x: np.ndarray, rng: np.random.Generator, wet: float = 0.25) -> np.ndarray:
    ir = ir_small(int(rng.integers(1 << 20)))
    xs = to_stereo(x)
    w = fftconv(xs, ir, circular=False, full=True)
    out = wet * w
    out[:len(xs)] += xs
    return out


def c3p2_fire_catch():
    """The C-17 stacks catch: a soft whoomph of air, the paper crackling up, the first roar. 3.2 s."""
    name = 'c3p2_fire_catch'
    rng = R(name)
    n = secs(3.2)
    tt = np.arange(n) / SR
    wh = eq(rng.standard_normal((n, 2)), ('hp', 60.0, 2), ('lp', 900.0, 2), circular=False)
    wh = ev(wh) * (smoothstep(np.clip(tt / 0.18, 0, 1)) * np.exp(-np.maximum(tt - 0.18, 0) / 0.6))[:, None]
    bed = fire_bed(rng, n, 0.5)
    bed = ev(bed) * (smoothstep(np.clip((tt - 0.1) / 0.9, 0, 1)))[:, None]
    out = 0.9 * wh + 0.8 * bed
    return one_shot(far(out, ir_registry(seed_of(name, 1)), wet=0.35, dry=1.0), -6.0, fout=0.6), None


def c3p2_bolt():
    """From inside the ramp door: the iron bolt drawn home outside -- a scrape and a clunk through the oak. 1.3 s."""
    name = 'c3p2_bolt'
    rng = R(name)
    out = np.zeros(secs(1.4))
    modes = [(1150.0, 0.03, 1.0), (2720.0, 0.02, 0.6), (4310.0, 0.015, 0.4), (640.0, 0.05, 0.5)]
    scr = creak_train(rng, 0.42, 60.0, 140.0, modes, jitter=0.5)
    scr = ev(scr) * np.sin(np.pi * np.linspace(0, 1, len(scr))) ** 0.5
    place(out, 0.55 * scr, secs(0.05), circular=False)
    clunk = impact(rng, [(180.0, 1.0, 0.25), (420.0, 0.6, 0.16), (905.0, 0.4, 0.1), (1650.0, 0.2, 0.06)], 0.8,
                   hard=0.6, noise_amt=0.5, noise_decay=0.006)
    place(out, ev(clunk), secs(0.48), circular=False)
    door = eq(noise_burst(0.3, rng, 40.0, 250.0, 0.15, attack=0.002), ('lp', 200.0, 2), circular=False)
    place(out, 0.5 * ev(door), secs(0.48), circular=False)
    out = eq(out, ('lp', 3800.0, 2), circular=False)
    return one_shot(far(out, ir_registry(seed_of(name, 1)), wet=0.3, dry=1.0, pan=-0.2), -5.0), None


def c3p2_desk_push():
    """The oak intake desk dragged off the chute door: wood on stone, a stutter, the last shove. 2.1 s."""
    name = 'c3p2_desk_push'
    rng = R(name)
    out = np.zeros(secs(2.2))
    modes = [(92.0, 0.06, 1.0), (215.0, 0.05, 0.7), (480.0, 0.04, 0.45), (1100.0, 0.02, 0.25)]
    for t0, dur, r0, r1 in ((0.0, 0.5, 18.0, 30.0), (0.62, 0.9, 25.0, 40.0)):
        c = creak_train(rng, dur, r0, r1, modes, jitter=0.45)
        rum = eq(rng.standard_normal(len(c)), ('lp', 400.0, 2), ('hp', 40.0, 2), circular=False)
        seg = ev(c) + 0.5 * ev(rum)
        seg *= np.sin(np.pi * np.linspace(0, 1, len(seg))) ** 0.4
        place(out, seg, secs(t0), circular=False)
    bump_ = impact(rng, random_modes(rng, 90.0, 900.0, 6, 0.06, 0.25), 0.6, hard=0.4, noise_amt=0.6)
    place(out, 0.9 * ev(bump_), secs(1.55), circular=False)
    return one_shot(far(out, ir_registry(seed_of(name, 1)), wet=0.35, dry=1.0), -5.0), None


def c3p2_door_jam():
    """The small 1909 iron door: the latch gives, the leaf grinds on its sill and sticks; a shoulder; a few
    centimetres more. 1.7 s."""
    name = 'c3p2_door_jam'
    rng = R(name)
    out = np.zeros(secs(1.8))
    latch = impact(rng, [(760.0, 1.0, 0.12), (1910.0, 0.5, 0.07), (3400.0, 0.3, 0.04)], 0.3, hard=0.8)
    place(out, 0.7 * ev(latch), 0, circular=False)
    modes = [(310.0, 0.05, 1.0), (870.0, 0.04, 0.7), (1630.0, 0.03, 0.4), (2950.0, 0.02, 0.25)]
    g1 = creak_train(rng, 0.45, 35.0, 18.0, modes, jitter=0.5)
    place(out, 0.8 * ev(g1), secs(0.12), circular=False)
    thud = impact(rng, random_modes(rng, 70.0, 600.0, 6, 0.1, 0.4), 0.8, hard=0.3, noise_amt=0.7, noise_decay=0.02)
    place(out, ev(thud), secs(0.78), circular=False)
    g2 = creak_train(rng, 0.5, 22.0, 9.0, modes, jitter=0.6)
    place(out, 0.7 * ev(g2), secs(0.95), circular=False)
    return one_shot(far(out, ir_registry(seed_of(name, 1)), wet=0.3, dry=1.0, pan=-0.15), -5.0), None


def c3p2_hatch_open():
    """Outside in the yard: the iron coal hatch forced up from below, a rusty hinge, the lid falling back onto the
    snow-covered stone; smoke rushing out. 1.9 s."""
    name = 'c3p2_hatch_open'
    rng = R(name)
    out = np.zeros(secs(2.0))
    modes = [(420.0, 0.05, 1.0), (1180.0, 0.04, 0.6), (2350.0, 0.03, 0.4)]
    hinge = creak_train(rng, 0.6, 28.0, 10.0, modes, jitter=0.4)
    place(out, 0.6 * ev(hinge), 0, circular=False)
    lid = impact(rng, [(150.0, 1.0, 0.5), (338.0, 0.7, 0.35), (612.0, 0.5, 0.25), (1190.0, 0.25, 0.12)], 1.0,
                 hard=0.5, noise_amt=0.6, noise_lo=80.0, noise_hi=2500.0, noise_decay=0.01)
    place(out, ev(lid), secs(0.62), circular=False)
    puff = eq(rng.standard_normal(secs(1.1)), ('hp', 150.0, 2), ('lp', 2200.0, 2), circular=False)
    puff = ev(puff) * np.exp(-np.linspace(0, 4, len(puff))) * smoothstep(np.clip(np.linspace(0, 8, len(puff)), 0, 1))
    place(out, 0.35 * puff, secs(0.66), circular=False)
    return one_shot(far(out, ir_outdoor_far(seed_of(name, 1)), wet=0.35, dry=1.0, pan=-0.1), -4.0), None


def c3p2_hatch_slam():
    """The hatch slammed shut on the smoke: a heavy iron slam, the frame rattling, the yard answering. 1.6 s."""
    name = 'c3p2_hatch_slam'
    rng = R(name)
    out = np.zeros(secs(1.7))
    lid = impact(rng, [(118.0, 1.0, 0.6), (266.0, 0.8, 0.45), (540.0, 0.55, 0.3), (980.0, 0.3, 0.18),
                       (1870.0, 0.15, 0.1)], 1.2, hard=0.75, noise_amt=0.8, noise_lo=60.0, noise_hi=4000.0,
                 noise_decay=0.012)
    place(out, ev(lid), 0, circular=False)
    for i in range(4):
        r = impact(rng, random_modes(rng, 500.0, 3000.0, 4, 0.02, 0.08), 0.2, hard=0.7)
        place(out, 0.18 * ev(r) * (0.7 ** i), secs(0.09 + 0.07 * i), circular=False)
    return one_shot(far(out, ir_outdoor_far(seed_of(name, 1)), wet=0.45, dry=1.0), -3.0), None


def c3p2_window_burst():
    """The souterrain windows of the east wing bursting in the heat: a crack, glass flung onto the yard, flame
    breathing out. 2.6 s."""
    name = 'c3p2_window_burst'
    rng = R(name)
    n = secs(2.7)
    out = np.zeros((n, 2))
    burst = impact(rng, random_modes(rng, 1500.0, 9000.0, 9, 0.01, 0.06), 0.3, hard=1.0, noise_amt=1.5,
                   noise_lo=1500.0, noise_hi=12000.0, noise_decay=0.02)
    place(out, pan2(ev(burst), -0.1), 0, circular=False)
    for i in range(16):
        sh = impact(rng, random_modes(rng, 2000.0, 9500.0, 5, 0.02, 0.15), 0.35, hard=0.9, noise_amt=0.3)
        place(out, pan2(rng.uniform(0.1, 0.45) * ev(sh), rng.uniform(-0.7, 0.7)),
              secs(0.25 + rng.exponential(0.3) + 0.03 * i), circular=False)
    tt = np.arange(n) / SR
    whoo = eq(rng.standard_normal((n, 2)), ('hp', 120.0, 2), ('lp', 1800.0, 2), circular=False)
    whoo = ev(whoo) * (smoothstep(np.clip((tt - 0.05) / 0.35, 0, 1)) * np.exp(-np.maximum(tt - 0.4, 0) / 0.7))[:, None]
    out += 0.6 * whoo
    return one_shot(far(out, ir_outdoor_far(seed_of(name, 1)), wet=0.5, dry=1.0), -4.0, fout=0.4), None


def c3p2_roof_creak():
    outs = []
    for i, (dur, low) in enumerate(((2.4, True), (1.8, False), (3.2, True)), start=1):
        nm = f'c3p2_roof_creak_{i}'
        rng = R(nm)
        x = timber_groan(rng, dur, low=low)
        if i == 3:
            tail = np.zeros(len(x) + secs(0.6))
            tail[:len(x)] = x
            place(tail, 0.35 * ev(wood_crack(rng))[:secs(1.2)], len(x) - secs(0.3), circular=False)
            x = tail
        outs.append((nm, one_shot(far(x, ir_registry(seed_of(nm, 1)), wet=0.4, dry=1.0, pan=rng.uniform(-0.3, 0.3)),
                                  -6.0 - i, fout=0.3), None))
    return outs


def c3p2_glass():
    outs = []
    for i, (shards, fall) in enumerate(((9, 0.5), (5, 0.35), (13, 0.6)), start=1):
        nm = f'c3p2_glass_{i}'
        rng = R(nm)
        x = glass_crack(rng, shards=shards, fall=fall)
        outs.append((nm, one_shot(far(x, ir_registry(seed_of(nm, 1)), wet=0.35, dry=1.0, pan=rng.uniform(-0.4, 0.4)),
                                  -6.0, fout=0.3), None))
    return outs


def c3p2_fire_bell():
    """The ladder engine's bell rung by hand, across the yard. 3.6 s."""
    name = 'c3p2_fire_bell'
    rng = R(name)
    b = hand_bell(rng, 8, rate=2.5, f1=640.0)[:secs(3.6)]
    return one_shot(far(b, ir_outdoor_far(seed_of(name, 1)), wet=0.45, dry=1.0, lp=7000.0), -6.0, fout=0.6), None


def c3p2_sirens_far():
    """Two brigades' two-tone horns of 1964 crossing the town far away, one higher and closer. 10 s."""
    name = 'c3p2_sirens_far'
    rng = R(name)
    a = eq(two_tone(rng, 9.5, 438.0, 586.0, 1.3, approach=0.6), ('lp', 2000.0, 2), ('hp', 220.0, 2), circular=False)
    b = eq(two_tone(rng, 7.0, 466.0, 622.0, 1.2, approach=0.3), ('lp', 1500.0, 2), ('hp', 260.0, 2), circular=False)
    x = np.zeros((secs(10.0), 2))
    place(x, pan2(a, 0.4), 0, circular=False)
    place(x, pan2(0.5 * b, -0.5), secs(2.4), circular=False)
    y = far(x, ir_outdoor_far(seed_of(name, 1)), wet=0.95, dry=0.2)
    return one_shot(y[:secs(10.0)], -9.0, fin=0.3, fout=1.2), None


# =============================================================================== music
def mus_c3p2_fire():
    """Tense, never an action cue: 72 bpm, 20 bars (80 beats).  A low pulse on A that leans on Bb, violas rising
    by semitones and falling back, string harmonics flickering, low brass breathing, the V motif breaking off."""
    name = 'mus_c3p2_fire'
    T = Track(name, bpm=72, beats=80, loop=True, seed=seed_of(name))
    for b in range(0, 80, 16):
        T.strings(b, 17.0, [33, 40], vel=0.42, stem='drone', attack=2.2, release=2.8, bright=0.25, vib=3.5, voices=4)
    # the pulse: two soft strokes per bar (heartbeat), the second leaning on Bb in the middle section
    for bar in range(20):
        b0 = 4 * bar
        lean = 46 if 6 <= bar < 14 else 45
        if bar in (9, 19):
            continue
        T.piano([(b0, 1, 45)], vel=0.30, stem='pulse', felt=1.0, decay=0.6, legato=0.6)
        T.piano([(b0 + 0.75, 1, lean)], vel=0.22, stem='pulse', felt=1.0, decay=0.5, legato=0.5)
        T.piano([(b0 + 2, 1, 52)], vel=0.15, stem='pulse', felt=1.0, decay=0.4, legato=0.5)
    # violas: A3 -> Bb3 -> B3 -> C4 (four bars each) -> back down over the last four bars (the loop breathes)
    rise = [(0, 57), (16, 58), (32, 59), (48, 60), (64, 58)]
    for b, m in rise:
        T.strings(b, 16.4, [m, m - 7], vel=0.30, stem='violas', attack=3.0, release=3.0, bright=0.35, vib=5.0,
                  voices=3, swell=0.35 if b < 64 else -0.3)
    # flicker: harmonics high up, short and irregular (sparks), never a melody
    for b, m in ((3, 88), (9.5, 91), (14, 88), (22.5, 93), (27, 89), (35.5, 91), (41, 88), (49.5, 94), (55, 89),
                 (61.5, 92), (70, 88), (75.5, 91)):
        T.strings(b, 1.4, [m], vel=0.10, stem='flicker', harmonic=True, attack=0.25, release=0.9, vib=2.0, voices=2)
    # low brass breathing in the middle (Bb under the A drone)
    T.brass(24, 12.0, [34], vel=0.24, attack=3.0, release=3.0, bright=0.15, swell=0.4)
    T.brass(40, 10.0, [33, 40], vel=0.22, attack=2.5, release=3.0, bright=0.15, swell=0.2)
    # the motif begins and breaks off twice (the sentence left open), the second time a semitone higher
    C3A.solo_line(T, C3A.V_A_STOP, 18, vel=0.30)
    C3A.solo_line(T, [(b, d, m + 1) for (b, d, m) in C3A.V_A_STOP], 50, vel=0.32)
    ir = hall_ir(seed_of(name, 1), rt_low=3.0, rt_high=1.2, predelay=0.03)
    mix = {'drone': (-1.0, 0.25, C3A.DRONE_EQ), 'pulse': (-3.0, 0.2, MUTED_EQ), 'violas': (-4.0, 0.3, STR_EQ),
           'flicker': (-15.0, 0.45, STR_HI_EQ), 'brass': (-10.0, 0.25, BRASS_EQ), 'solo': (-4.0, 0.3, C3A.SOLO_EQ)}
    out = T.mixdown(mix, ir, target_rms=-21.0, master_lp=9000.0)
    out = np.roll(out, int(round(0.5 * T.spb * SR)), axis=0)      # the loop point sits in the rest of bar 20
    return out, (0, out.shape[0])


def mus_c3p2_halves():
    """Quiet: 56 bpm, 24 bars.  The two-language motif V divided between the felt piano and the viola: first
    half / second half, then swapped, then the piano alone -- and the answer does not come.  Snow (celesta)."""
    name = 'mus_c3p2_halves'
    T = Track(name, bpm=56, beats=96, loop=True, seed=seed_of(name))
    for b in range(0, 96, 16):
        T.strings(b, 17.5, [33, 40], vel=0.30, stem='drone', attack=3.5, release=3.5, bright=0.2, vib=3.0, voices=4)
    pads = [(0, [52, 57, 64]), (16, [53, 57, 60]), (32, [50, 53, 57]), (48, [52, 56, 59]), (64, [53, 57, 64]),
            (80, [52, 57, 59])]
    for b, ch in pads:
        T.strings(b + 0.5, 15.5, ch, vel=0.20, attack=3.5, release=3.5, bright=0.28, voices=3, vib=4.0,
                  bass_boost=1.0)
    first = [(0, 1, 52), (1, 1.5, 60)]                        # E3 C4
    second_v = [(0, 1, 58), (1, 2, 57), (4, 2, 52)]           # Bb3 A3 . E3  (Veltrava: the changed note)
    second_p = [(0, 1, 59), (1, 2, 57), (4, 2, 52)]           # B3 A3 . E3
    T.piano(first, vel=0.36, beat0=8, felt=0.75, decay=0.95, pan=-0.15)
    C3A.solo_line(T, second_v, 11, vel=0.30)
    C3A.solo_line(T, first, 40, vel=0.30)
    T.piano(second_p, vel=0.34, beat0=43, felt=0.75, decay=0.95, pan=-0.15)
    T.piano(first, vel=0.32, beat0=72, felt=0.78, decay=1.0, pan=-0.15)     # ... and nobody answers
    for b, m in ((5, 88), (23, 91), (30, 86), (54, 88), (61, 93), (79, 86), (86, 88), (92, 91)):
        T.celesta([(b, 1, m)], vel=0.16, pan=0.3, bright=0.35)
    ir = hall_ir(seed_of(name, 1), rt_low=3.6, rt_high=1.5, predelay=0.035)
    mix = {'drone': (-2.0, 0.3, C3A.DRONE_EQ), 'strings': (-6.0, 0.35, STR_EQ), 'solo': (-3.0, 0.32, C3A.SOLO_EQ),
           'piano': (-1.0, 0.32, C3A.FELT_EQ), 'celesta': (-13.0, 0.45, CEL_EQ)}
    out = T.mixdown(mix, ir, target_rms=-23.0, master_lp=8500.0)
    out = np.roll(out, int(round(0.5 * T.spb * SR)), axis=0)
    return out, (0, out.shape[0])


# =============================================================================== registry
BUILDERS = {
    'amb_veltrava_registry': ('amb', amb_veltrava_registry),
    'amb_veltrava_fire': ('amb', amb_veltrava_fire),
    'amb_veltrava_quay': ('amb', amb_veltrava_quay),
    'mus_c3p2_fire': ('music', mus_c3p2_fire),
    'mus_c3p2_halves': ('music', mus_c3p2_halves),
    'c3p2_fire_low': ('sfx', c3p2_fire_low),
    'c3p2_fire_mid': ('sfx', c3p2_fire_mid),
    'c3p2_fire_high': ('sfx', c3p2_fire_high),
    'c3p2_yard_night': ('sfx', c3p2_yard_night),
    'c3p2_radio_waltz': ('sfx', c3p2_radio_waltz),
    'c3p2_radio_interval': ('sfx', c3p2_radio_interval),
    'c3p2_radio_news_ru': ('sfx', c3p2_radio_news_ru),
    'c3p2_radio_news_de': ('sfx', c3p2_radio_news_de),
    'c3p2_radio_tune': ('sfx', c3p2_radio_tune),
    'c3p2_note_slide': ('sfx', c3p2_note_slide),
    'c3p2_fire_catch': ('sfx', c3p2_fire_catch),
    'c3p2_bolt': ('sfx', c3p2_bolt),
    'c3p2_desk_push': ('sfx', c3p2_desk_push),
    'c3p2_door_jam': ('sfx', c3p2_door_jam),
    'c3p2_hatch_open': ('sfx', c3p2_hatch_open),
    'c3p2_hatch_slam': ('sfx', c3p2_hatch_slam),
    'c3p2_window_burst': ('sfx', c3p2_window_burst),
    'c3p2_roof_creak': ('sfx', c3p2_roof_creak),
    'c3p2_glass': ('sfx', c3p2_glass),
    'c3p2_fire_bell': ('sfx', c3p2_fire_bell),
    'c3p2_sirens_far': ('sfx', c3p2_sirens_far),
}
# where each sound is (or should be) wired -- the --list output and documentation/asset_manifest_parts/c3p2_cast_audio.md
WIRING = {
    'amb_veltrava_registry': 'L_C3_Registry.tscn ambience (scenes A, B)',
    'amb_veltrava_fire': 'c3.json switches L_C3_RegistryC / D "ambience"',
    'amb_veltrava_quay': 'L_C3_Quay.tscn ambience',
    'mus_c3p2_fire': 'c3.json switches L_C3_RegistryC / D "music" (integration note)',
    'mus_c3p2_halves': 'L_C3_Quay.tscn music; LS_C3_Halves keeps it',
}
# loudness envelope the checks enforce: (min RMS, max RMS, max peak) in dBFS
TARGETS = {'amb': (-28.0, -21.0, -2.5), 'music': (-25.0, -19.0, -0.8), 'loop': (-36.0, -19.0, -2.5),
           'sfx': (-45.0, -9.0, -2.5)}


def outputs_of(name: str):
    """Builder name -> list of (file name, signal, loop)."""
    kind, fn = BUILDERS[name]
    r = fn()
    if isinstance(r, list):
        return kind, r
    sig, loop = r
    return kind, [(name, sig, loop)]


def wav_path(kind: str, name: str) -> str:
    return os.path.join(AUDIO, kind, name + '.wav')


def build_one(name: str) -> list[dict]:
    t0 = time.time()
    kind, outs = outputs_of(name)
    rows = []
    for fname, sig, loop in outs:
        path = wav_path(kind, fname)
        st = write_wav(path, sig, loop=loop, seed=zlib.crc32(fname.encode()))
        rows.append({'name': fname, 'kind': kind, 'path': path, 'loop': loop, 'seconds': round(time.time() - t0, 1),
                     **st})
    return rows


def check_rows(rows: list[dict]) -> list[str]:
    """Numeric acceptance (nobody listens before the lead): level window per kind, no clipping, seamless loops
    (the step across the seam is an ordinary step, RMS continuous), loops of whole length, one-shots fade out."""
    from dsp import read_wav
    fails = []
    for r in rows:
        x, sr, loop = read_wav(r['path'])
        kind = r['kind'] if r['kind'] != 'sfx' or not loop else 'loop'
        lo, hi, pk = TARGETS[kind]
        rm = float(20 * np.log10(max(rms(x), 1e-12)))
        peak = float(20 * np.log10(max(float(np.max(np.abs(x))), 1e-12)))
        if not lo <= rm <= hi:
            fails.append(f"{r['name']}: RMS {rm:.1f} dBFS outside [{lo}, {hi}]")
        if peak > pk:
            fails.append(f"{r['name']}: peak {peak:.1f} dBFS above {pk}")
        if r['clipped_samples']:
            fails.append(f"{r['name']}: {r['clipped_samples']} clipped samples")
        if sr != SR:
            fails.append(f"{r['name']}: {sr} Hz")
        if loop:
            if loop != (0, len(x)):
                fails.append(f"{r['name']}: loop {loop} does not span the file ({len(x)} frames)")
            s = C3A.seam_continuity(x)
            if abs(s['rms_delta_db']) > 3.0 or s['step_vs_local_median'] > 6.0:
                fails.append(f"{r['name']}: seam {s}")
        else:
            tail = x[-secs(0.01):]
            if float(np.max(np.abs(tail))) > 0.01:
                fails.append(f"{r['name']}: one-shot does not end in silence")
    return fails


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--only', default='', help='comma separated builder names: ' + ', '.join(BUILDERS))
    ap.add_argument('--jobs', type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--no-analysis', action='store_true')
    ap.add_argument('--no-spectro', action='store_true')
    args = ap.parse_args()
    if args.list:
        for n, (k, _) in BUILDERS.items():
            print(f'{k:6s} {n:24s} {WIRING.get(n, "cinematics / level scripts (manifest part)")}')
        return
    names = [n.strip() for n in args.only.split(',') if n.strip()] or list(BUILDERS)
    for n in names:
        if n not in BUILDERS:
            sys.exit(f'unknown builder {n!r}; known: {", ".join(BUILDERS)}')
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max(1, min(args.jobs, len(names)))) as ex:
        built = [r for rows in ex.map(build_one, names) for r in rows]
    for b in built:
        print(f"  built {b['name']:<24}{b['seconds']:>6.1f}s  {b['frames']:>8} fr x {b['channels']} ch  "
              f"loop {b['loop']}  clipped {b['clipped_samples']}")
        if C3A.ensure_import(b['path']):
            print(f"  wrote {os.path.relpath(b['path'], ROOT)}.import")
    print(f'synthesis done in {time.time() - t0:.1f}s')
    fails = check_rows(built)
    if not args.no_analysis:
        import analyze
        preview = None
        if not args.no_spectro:
            preview = analyze.PREVIEW
            analyze.ensure_preview_dir()
        rows = [C3A.analyse(b['path'], b['name'], preview if b['kind'] != 'sfx' or b['loop'] else None) for b in built]
        C3A.print_rows(rows)
        os.makedirs(analyze.PREVIEW, exist_ok=True)
        with open(os.path.join(analyze.PREVIEW, 'c3p2_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=1, default=str)
    for f in fails:
        print('  FAIL', f)
    print('OK: c3p2 audio checks pass' if not fails else f'FAIL: {len(fails)} c3p2 audio checks')
    print(f'total {time.time() - t0:.1f}s')
    if fails:
        sys.exit(1)


if __name__ == '__main__':
    main()
