"""c4p2_audio.py -- Chapter 4, part 2 („Stimmen unter Beton“, second half): original synthesised sound for the Karsk
locomotive depot (the coal stage at dawn, the showcase on platform 1 in the evening), the Berlin Ostbahnhof under its
glass roof and the courtyard of Kolonnenstraße 14 at night, the part's music and the two puzzles' sounds
(documentation/C4P2_DESIGN.md section 8, audio brief; the films' own cues belong to the cine stream).

    py -3 -P tools/audiogen/c4p2_audio.py                          # build all + .import + analysis + numeric checks
    py -3 -P tools/audiogen/c4p2_audio.py --only amb_karsk_depot   # subset (comma separated builder names)
    py -3 -P tools/audiogen/c4p2_audio.py --list                   # what exists and where it is (to be) wired
    py -3 -P tools/audiogen/c4p2_audio.py --no-spectro             # skip the spectrogram PNGs

LEVEL AMBIENCES (assets/audio/amb, 60 s stereo loops; ids fixed by the contract, wired by c4p2.json "switches")
  amb_karsk_depot      the depot before dawn (L_C4P2_KarskA): the coal stage's work gang shovelling in a ragged line
                       (scrape, lift, the load rattling into the tender), a standing engine's blower and its safety
                       valve lifting twice, the guard's barrel fire, a yard dog, the canteen radio far off behind a
                       window, sparrows in the roundhouse eaves, a fitter's hammer, a goods train passing behind
  amb_karsk_platform   platform 1 and the depot's showcase in the evening (L_C4P2_KarskB): the depot band rehearsing
                       the Accord march far off (it breaks off, the baton taps, again from the top), the westbound
                       express's air pumps, station announcements in a Russian cadence (no words), a crowd of
                       officials, press and workers, snow ticking on the iron canopy, now and then a slide of it
  amb_berlin_station   the Ostbahnhof under glass at night (L_C4P2_BerlinA): the hall's long echo, announcements in
                       a German cadence (no words) after the gong, the express's steam and air pump, luggage carts,
                       pigeons up in the roof, the kiosk's bell, cutlery and cups in the dining car, a tram ringing
                       on the forecourt, steps on stone
  amb_berlin_courtyard the courtyard of No. 14 at night (L_C4P2_BerlinB): Lenz's radio playing a dance tune behind
                       a window (till midnight), the Schulz baby fussing for a moment, a card game behind another
                       window, a dog far off, the S-Bahn crossing its viaduct, wind in the gate passage, a gutter
                       dripping into the yard, and under everything the Hall's distant hum
MUSIC (assets/audio/music)
  mus_c4p2_karsk       loop: the bayan breath of part 1, slower (45 bpm), over low strings in D Aeolian; the K motif
                       comes back augmented in the cellos.  In KarskB the band of amb_karsk_platform plays its
                       march against it (F major: the same notes as D Aeolian, the other face of them)
  mus_c4p2_berlin      loop: piano and low strings in G Aeolian, the 3+3+2 clockwork pulse of part 1 on a muted
                       piano, quieter and slower (63 bpm), B on the piano and a viola line
  mus_c4p2_clock       one-shot cue of LS_C4P2_Clock (24 s, played from the film's first frame): both themes on one
                       clock -- the tick every second from k1, B (Berlin, 23.40), the drone (Kordon-17), K on the
                       felt piano and the bayan (Karsk, 1.40), both together where B bends Eb to E, and on k5 the
                       tick stops (the 21st tick, at CLOCK_STOP, never comes); silence
SFX (assets/audio/sfx, one-shots; ids = the ones the puzzle UIs ask for -- scripts/ui/join_puzzle.gd and
house_puzzle.gd call them through Kit.ui_sound_first chains; C4P2_DESIGN section 2.7)
  c4p2_halves_snap     JoinPuzzle, the solving moment: the German half slid home against the Russian one, pressed flat
  c4p2_tooth_1..3      JoinPuzzle: one tooth seating in its notch (the five clicks of the success, CLICK_STEP apart)
  c4p2_stamp_close     JoinPuzzle: the stamp closes into a circle -- a soft press, then two brass tones a quarter-tone
                       apart that beat, slow down and meet in one (one card, two halves)
  c4p2_shutter         JoinPuzzle: Ekdahl photographs the joined card -- a rangefinder's cloth shutter and the film
                       advanced (fits the 0.6 s between the two photographs)
  c4p2_steps_1..3      HousePuzzle: the Probegang sets off -- careful steps on the old wooden stairs at night, one
                       creak (random variants: Audio picks one); also an UP move
  c4p2_steps_down_1..3 HousePuzzle: the same going down, quicker, heel first
  c4p2_attic_door      HousePuzzle: the drying loft's plank door -- latch, a long hinge squeal, the cold loft, a
                       pigeon flapping off in the dark
  c4p2_spyhole         HousePuzzle: Frau Pohl's spy-hole cover sliding aside behind her door (the walk stops at s2)
  c4p2_door            HousePuzzle: they are down -- the bolt drawn on Pietsch's cellar door, the heavy door dragged
                       open over the stone sill, the cellar's hollow answer
  c4p2_pencil          HousePuzzle: Konrad's red pencil rings the workshop on the plan
  c4p2_knock           HousePuzzle: a move without a passage -- a knuckle against the wall, softly

Everything reuses dsp / instruments / foley / ambience / music / c3_audio / c3p2_audio / c4_audio by import (none of
them is modified; build_all.py's registry does not know this module: run this file directly).  Seeds derive from
zlib.crc32(name) (c3_audio.seed_of), so every run is bit-identical.  Voices are prosody profiles over random vowel
targets (c3_audio.voice): no words, no language.  The march is original (composed here: a provincial band's tune,
thin and a little out of tune in the cold -- no anthem, no quotation, no cymbal, nothing triumphant); the dance tune
on Lenz's radio is original too.
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
                 db2a, smoothstep, make_ir, fade, midi_hz, write_wav, limiter, normalize_peak, remove_dc,
                 to_stereo, soft_clip)
from instruments import (impact, random_modes, noise_burst, ctrl_noise, modal, make_table, wt_read,  # noqa: E402
                         brass_note, bell_modes)
from foley import (wind, gust_curve, norm_peak, bump, ir_outdoor_far, grain_cloud, tram_bell, wood_knock,  # noqa: E402
                   metal_clank, shunting_chain, creak_train, loudspeaker, footstep)
from ambience import Mix, N, periodic_tone, clock_tick  # noqa: E402
from music import (Track, hall_ir, K_A, K_B, B_1, B_2, tr, STR_EQ, STR_HI_EQ, BRASS_EQ, MUTED_EQ,  # noqa: E402
                   CEL_EQ, PLUCK_EQ)
import c3_audio as C3A  # noqa: E402  (seed_of, far, voice, talkers, luggage_cart, pigeons, walker, loco_breath ...)
import c3p2_audio as P2A  # noqa: E402  (R, one_shot, radio_set, fire_bed, snow_steps, check_rows)
import c4_audio as C4A  # noqa: E402  (the bayan: reed_note / bayan_breath, machine_tick, drip, hum, ir_cellar)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AUDIO = os.path.join(ROOT, 'assets', 'audio')
seed_of = C3A.seed_of
far = C3A.far
R = P2A.R
one_shot = P2A.one_shot
overlay = C3A.overlay

# LS_C4P2_Clock (C4P2_DESIGN 2.9): shot starts k1..k5 and the film's end (s).  The tick runs from k1 and stops on k5:
# ticks at 0, 1, ... CLOCK_STOP - 1; the one at CLOCK_STOP never comes.  The cue starts with the film (t = 0).
CLOCK_SHOTS = (0.0, 5.0, 11.0, 16.0, 20.0, 24.0)
CLOCK_STOP = 20.0
CLOCK_LEN = 24.5


# =============================================================================== rooms
def ir_depot(seed: int) -> np.ndarray:
    """The coal stage between the roundhouse and the sheds: open sky, one slap from the roundhouse wall."""
    return make_ir(length=2.6, rt_low=1.5, rt_high=0.55, predelay=0.02, er_taps=5, er_span=0.05, er_gain=0.16,
                   seed=seed, lowcut=60.0, highcut=6500.0, build=0.02, slap=[(0.11, 0.30, 3200.0), (0.26, 0.16, 2200.0)])


def ir_platform(seed: int) -> np.ndarray:
    """Platform 1 under its iron canopy, the depot sheds across the tracks."""
    return make_ir(length=3.0, rt_low=1.8, rt_high=0.7, predelay=0.015, er_taps=6, er_span=0.04, er_gain=0.2,
                   seed=seed, lowcut=55.0, highcut=6500.0, build=0.02, slap=[(0.05, 0.22, 3800.0), (0.38, 0.14, 2000.0)])


def ir_ostbahnhof(seed: int) -> np.ndarray:
    """The Ostbahnhof's glass-roofed hall: long, grey, full of reflections."""
    return make_ir(length=5.2, rt_low=3.6, rt_high=1.6, predelay=0.035, er_taps=16, er_span=0.12, er_gain=0.35,
                   seed=seed, lowcut=50.0, highcut=7000.0, build=0.03, slap=[(0.21, 0.18, 2600.0), (0.47, 0.10, 1800.0)])


def ir_court(seed: int) -> np.ndarray:
    """The closed courtyard: five storeys of plaster on four sides -- a flutter between the walls, a short tail."""
    return make_ir(length=2.4, rt_low=1.3, rt_high=0.6, predelay=0.01, er_taps=8, er_span=0.05, er_gain=0.25,
                   seed=seed, lowcut=60.0, highcut=7000.0, build=0.01,
                   slap=[(0.064, 0.30, 4200.0), (0.128, 0.20, 3600.0), (0.192, 0.12, 3000.0), (0.256, 0.07, 2400.0)])


def ir_stair(seed: int) -> np.ndarray:
    """The wooden stairwell of a tenement wing: small, woody, a little flutter up the well."""
    return make_ir(length=1.4, rt_low=0.9, rt_high=0.35, predelay=0.006, er_taps=10, er_span=0.03, er_gain=0.4,
                   seed=seed, lowcut=70.0, highcut=6000.0, build=0.006, slap=[(0.03, 0.2, 3000.0), (0.06, 0.12, 2400.0)])


def ir_attic(seed: int) -> np.ndarray:
    """The drying loft under the roof: wooden, large, dry and cold."""
    return make_ir(length=2.0, rt_low=1.3, rt_high=0.5, predelay=0.012, er_taps=8, er_span=0.05, er_gain=0.3,
                   seed=seed, lowcut=70.0, highcut=6500.0, build=0.01)


# =============================================================================== sources: Karsk depot
def coal_scrape(rng: np.random.Generator) -> np.ndarray:
    """The blade driven into the coal pile: gritty friction, lumps shifting against the steel (mono, 0.5 s)."""
    n = secs(0.5)
    t = np.arange(n) / SR
    env = smoothstep(t / 0.04) * np.clip((0.44 - t) / 0.14, 0.0, 1.0)
    fr = noise_burst(0.5, rng, 700.0, 6500.0, 1e6, attack=0.0)
    fr = eq(fr, ('bell', rng.uniform(2100.0, 2700.0), 4.0, 1.0), circular=False) * env
    lumps = grain_cloud(rng, 0.5, 260.0 * env + 2.0, 900.0, 5200.0, 0.003, 0.014)
    ring = modal([(rng.uniform(1900, 2300), 0.4, 0.08), (rng.uniform(3500, 4100), 0.25, 0.05)], 0.5,
                 seed=int(rng.integers(1 << 30)), attack=0.01) * env
    return 0.55 * norm_peak(fr) + 0.75 * norm_peak(lumps) + 0.12 * norm_peak(ring)


def coal_throw(rng: np.random.Generator) -> np.ndarray:
    """The load sliding off the blade and landing in the tender: a rattling cascade on steel, a low thump."""
    dur = 0.9
    n = secs(dur)
    t = np.arange(n) / SR
    rate = 900.0 * smoothstep(t / 0.05) * np.exp(-t / 0.22) + 3.0
    casc = grain_cloud(rng, dur, rate, 500.0, 4200.0, 0.006, 0.03)
    thump = modal([(rng.uniform(70, 90), 1.0, 0.12), (rng.uniform(160, 200), 0.5, 0.08)], dur,
                  seed=int(rng.integers(1 << 30)), attack=0.004)
    y = 0.9 * norm_peak(casc) + 0.35 * norm_peak(thump)
    return fade(y, 0.0, 0.2)


def shovel_stroke(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    """One shovelful: the scrape (0 s), the lift, the throw (~0.9 s); sometimes the blade knocks the tender's rim."""
    y = np.zeros(secs(2.0))
    place(y, weight * coal_scrape(rng), 0, circular=False)
    tt = rng.uniform(0.82, 1.0)
    place(y, weight * 0.9 * coal_throw(rng), secs(tt), circular=False)
    if rng.random() < 0.35:
        rim = impact(rng, random_modes(rng, 600.0, 3800.0, 6, 0.05, 0.25), 0.4, hard=0.6, noise_amt=0.2)
        place(y, weight * 0.3 * rim, secs(tt - 0.04), circular=False)
    return y


def shovel_gang(rng: np.random.Generator, n: int, ir: np.ndarray, workers) -> np.ndarray:
    """Kolonne 4 at the coal stage: each worker (period s, pan, distance 0..1) shovels on their own ragged rhythm,
    some resting now and then (a breath, a back straightened).  Circular stereo bed."""
    buf = np.zeros((n, 2))
    for period, pan, dist in workers:
        t = rng.uniform(0.0, period)
        dry = np.zeros(n)
        while t < n / SR:
            if rng.random() < 0.12:              # a pause: straighten the back
                t += period * rng.uniform(1.2, 2.0)
                continue
            st = shovel_stroke(rng, rng.uniform(0.75, 1.0))
            place(dry, st, secs(t), circular=True)
            t += period * rng.uniform(0.86, 1.14)
        dry = eq(dry, ('lp', 7000.0 - 4500.0 * dist, 2), circular=True)
        st2 = pan2(dry, pan)
        buf += st2 * (1.0 - 0.6 * dist) + (0.25 + 0.6 * dist) * fftconv(st2, ir, circular=True)
    return buf


def safety_valve(rng: np.random.Generator, dur: float = 3.4) -> np.ndarray:
    """A standing engine's safety valve lifting: a roar with a whistling edge, fluttering, then it seats with a
    click and the roar collapses (mono, dry)."""
    n = secs(dur + 0.6)
    t = np.arange(n) / SR
    z = noise_burst(dur + 0.6, rng, 450.0, 11000.0, 1e6, attack=0.0)
    z = eq(z, ('bell', 3100.0, 6.0, 0.5), ('bell', 1250.0, 3.0, 0.8), ('tilt', -1.0, 2000.0), circular=False)
    env = smoothstep(t / 0.10) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.05))
    flutter = 1.0 + 0.18 * ctrl_noise(n, 13.0, rng)
    f = 3150.0 * (1.0 + 0.004 * ctrl_noise(n, 3.0, rng))
    whistle = 0.18 * np.sin(TAU * np.cumsum(f) / SR) * env
    y = norm_peak(z) * env * flutter + whistle
    seat = impact(rng, random_modes(rng, 900.0, 5000.0, 6, 0.01, 0.05), 0.15, hard=0.8, noise_amt=0.2)
    place(y, 0.35 * seat, secs(dur), circular=False)
    return fade(y, 0.0, 0.1)


def blower(n: int, rng: np.random.Generator) -> np.ndarray:
    """A standing engine's blower roaring in the smokebox, heard across the yard (circular, mono)."""
    z = shaped_noise(n, rng, lambda f: mag_bp(f, 110.0, 3400.0, 2) *
                     (1.0 + 2.2 * np.exp(-0.5 * ((f - 640.0) / 170.0) ** 2)))
    z = z[:, 0] if z.ndim == 2 else z
    return z / max(rms(z), 1e-9) * (1.0 + 0.14 * smooth_periodic(n, 30, rng))


def dog_bark(rng: np.random.Generator, f0: float = 380.0, barks: int = 2) -> np.ndarray:
    """A yard dog: short 'wuff' bursts -- a harmonic voice with a quick pitch fall and a rasp, formants of a big
    dog's throat (mono, dry)."""
    out = np.zeros(secs(0.45 * barks + 0.5))
    t0 = 0.0
    for _ in range(barks):
        d = rng.uniform(0.14, 0.22)
        m = secs(d)
        tb = np.arange(m) / SR
        f = f0 * rng.uniform(0.92, 1.08) * (1.25 - 0.45 * tb / d)
        ph = np.cumsum(f) / SR
        src = sum(h ** -1.1 * np.sin(TAU * h * ph) for h in range(1, 15))
        src = src + 0.45 * rng.standard_normal(m)
        env = smoothstep(tb / 0.012) * np.exp(-tb / (d * 0.45))
        y = eq(src * env, ('bell', 520.0, 9.0, 0.6), ('bell', 1150.0, 7.0, 0.6), ('bell', 2500.0, 4.0, 0.7),
               ('lp', 4200.0, 2), ('hp', 150.0, 2), circular=False)
        place(out, norm_peak(y) * rng.uniform(0.8, 1.0), secs(t0), circular=False)
        t0 += rng.uniform(0.3, 0.45)
    return fade(out, 0.0, 0.1)


def sparrows(rng: np.random.Generator, chirps: int = 7) -> np.ndarray:
    """House sparrows in the eaves: a little cluster of 'tschilp' chirps (mono, dry)."""
    out = np.zeros(secs(0.22 * chirps + 0.4))
    t0 = 0.0
    for _ in range(chirps):
        d = rng.uniform(0.05, 0.11)
        m = secs(d)
        u = np.arange(m) / m
        fc = rng.uniform(3200.0, 4800.0)
        f = fc * (1.0 - 0.28 * u + 0.35 * np.sin(np.pi * u) ** 2)
        ph = np.cumsum(f) / SR
        y = (np.sin(TAU * ph) + 0.3 * np.sin(TAU * 2 * ph)) * np.sin(np.pi * u) ** 0.7
        place(out, y * rng.uniform(0.5, 1.0), secs(t0), circular=False)
        t0 += d + rng.uniform(0.06, 0.24)
    return out


def hammer_far(rng: np.random.Generator, blows: int = 4) -> np.ndarray:
    """A fitter in the roundhouse knocking a pin home: hammer blows on steel (mono, dry)."""
    out = np.zeros(secs(0.62 * blows + 0.8))
    for k in range(blows):
        h = impact(rng, random_modes(rng, 500.0, 4200.0, 8, 0.08, 0.5), 0.8, hard=0.85, noise_amt=0.25)
        place(out, h * (1.0 if k < blows - 1 else 1.2), secs(k * rng.uniform(0.55, 0.68)), circular=False)
    return out


def freight_pass(rng: np.random.Generator, dur: float = 18.0, wagons: int = 16) -> np.ndarray:
    """A goods train passing on the main line behind the depot: rumble that swells and recedes, the wheelsets
    over the rail joints (a travelling double knock), a flange squeal on the curve, couplings jangling (mono)."""
    n = secs(dur)
    t = np.arange(n) / SR
    mid = dur * 0.5
    env = bump(n, mid * 0.9, mid * 0.9, peak_at=mid)
    rum = noise_burst(dur, rng, 25.0, 380.0, 1e6, attack=0.0)
    y = 0.6 * norm_peak(rum) * env * (0.85 + 0.15 * ctrl_noise(n, 2.0, rng))
    tc = 1.0
    seq = [0.0, 0.2, 0.4, 1.1, 1.3, 1.5] + [2.4 + i * 0.95 + o for i in range(wagons) for o in (0.0, 0.62)]
    for s in seq:
        tt = tc + s
        if not 0.05 < tt < dur - 0.5:
            continue
        g = float(np.interp(tt, t, env))
        for k, off in enumerate((0.0, 0.05)):
            kn = impact(rng, random_modes(rng, 120.0, 1800.0, 7, 0.03, 0.14), 0.25, hard=0.5, noise_amt=0.3)
            place(y, 0.28 * g * kn * (1.0 if k == 0 else 0.75), secs(tt + off), circular=False)
    sq = np.sin(TAU * np.cumsum(2650.0 * (1.0 + 0.01 * ctrl_noise(n, 1.2, rng))) / SR)
    y += 0.03 * sq * np.clip(env - 0.55, 0.0, None) * (0.5 + 0.5 * ctrl_noise(n, 0.7, rng))
    for k in range(5):
        tt = mid + rng.uniform(-3.0, 4.0)
        ck = metal_clank(rng, 'light')
        place(y, 0.1 * ck * float(np.interp(tt, t, env)), secs(tt), circular=False)
    return fade(eq(y, ('lp', 2600.0, 2), ('hp', 25.0, 2), circular=False), 0.4, 1.5)


def radio_broadcast(rng: np.random.Generator, n: int, f0: float, prof: str) -> np.ndarray:
    """A canteen loudspeaker / wireless: an announcer (prosody only, no words) through a small valve set,
    heard through a closed window across the yard (circular, mono)."""
    v = C3A.voice(rng, n / SR, f0, prof, pause=(0.4, 1.6), phrase=(1.6, 4.2))
    v = np.roll(v, int(rng.integers(n)))
    y = P2A.radio_set(v, rng, circular=True)
    return eq(y, ('lp', 1600.0, 2), ('hp', 220.0, 2), circular=True)


# =============================================================================== sources: the platform
# The Accord march (original): a provincial depot band's tune in F major, 2/4 at 112 bpm -- cornet tune, alto horns
# on the off-beats, tuba on the downbeat, side drum and bass drum.  (beat, dur, midi); a bar = 2 beats.
MARCH_A = [(0, 0.75, 72), (0.75, 0.25, 72), (1, 1, 77), (2, 0.5, 81), (2.5, 0.5, 79), (3, 0.5, 77), (3.5, 0.5, 76),
           (4, 1, 74), (5, 0.75, 70), (5.75, 0.25, 74), (6, 1.5, 72)]
MARCH_B = [(8, 0.75, 72), (8.75, 0.25, 74), (9, 0.5, 76), (9.5, 0.5, 77), (10, 1, 79), (11, 0.75, 81),
           (11.75, 0.25, 79), (12, 0.5, 77), (12.5, 0.5, 76), (13, 0.5, 74), (13.5, 0.5, 76), (14, 1.5, 77)]
MARCH_CHORDS = ['F', 'C7', 'Bb', 'C', 'F', 'C', 'BbC7', 'F']          # one per bar of the 8-bar strain
MARCH_HARM = {'F': (41, [57, 60, 65]), 'C7': (36, [58, 60, 64]), 'Bb': (46, [58, 62, 65]), 'C': (36, [55, 60, 64]),
              'BbC7': (46, [58, 62, 65])}


def band_strain(bars, seed: int, tempo: float = 112.0, cut: float | None = None, crack: float | None = None) -> np.ndarray:
    """`bars` bars of the march strain (index into the 8 bars; repeats allowed) by the depot band: a little out of
    tune in the cold (cornet sharp, the horns flat), loose ensemble.  cut = stop after that many beats (the
    conductor breaks off), crack = beat at which a horn cracks a note.  Stereo, dry-ish (a small outdoor room)."""
    beats = 2 * len(bars) + 3
    T = Track(f'band_{seed}', bpm=tempo, beats=beats, loop=False, seed=seed, tail=2.0)
    tune = MARCH_A + MARCH_B
    for i, b in enumerate(bars):
        b0 = 2 * i
        for (bt, d, m) in tune:
            if 2 * b <= bt < 2 * b + 2:
                beat = b0 + bt - 2 * b
                if cut is not None and beat >= cut:
                    continue
                sig = brass_note(m + 0.12, d * T.spb * 0.92, vel=0.62, attack=0.04, release=0.18, players=2,
                                 seed=T.sd(), bright=0.85, scoop=6.0, formant=1150.0, pan=0.05)
                T.put('cornet', beat, sig, jitter=0.012)
        ch = MARCH_HARM[MARCH_CHORDS[b % 8]]
        bass, voicing = ch
        if MARCH_CHORDS[b % 8] == 'BbC7':
            parts = [(0, 46, [58, 62, 65]), (1, 36, [58, 60, 64])]
        else:
            parts = [(0, bass, voicing), (1, bass + 7 if bass < 40 else bass - 5, voicing)]
        for off, bs, vc in parts:
            beat = b0 + off
            if cut is not None and beat >= cut:
                continue
            T.put('tuba', beat, brass_note(bs - 12 - 0.1, 0.42 * T.spb, vel=0.7, attack=0.03, release=0.15,
                                           players=1, seed=T.sd(), bright=0.45, formant=380.0), jitter=0.015)
            for m in vc:
                T.put('horns', beat + 0.5, brass_note(m - 0.15, 0.3 * T.spb, vel=0.42, attack=0.03, release=0.12,
                                                      players=1, seed=T.sd(), bright=0.55, formant=700.0,
                                                      pan=0.15 * (m - 60) / 5.0), jitter=0.02)
            # drums: bass drum on the downbeat, side drum on the off-beat
            rng = np.random.default_rng(T.sd())
            if off == 0:
                bd = modal([(rng.uniform(52, 58), 1.0, 0.35), (rng.uniform(96, 110), 0.4, 0.2)], 0.6, seed=T.sd(),
                           attack=0.003)
                place_ = to_stereo(norm_peak(bd)) * 0.9
                T.put('drums', beat, place_, jitter=0.008)
            sd = noise_burst(0.18, rng, 900.0, 7000.0, 0.09) + 0.4 * modal([(rng.uniform(180, 210), 1.0, 0.08)],
                                                                         0.18, seed=T.sd())
            T.put('drums', beat + 0.5, to_stereo(norm_peak(sd)) * 0.5, jitter=0.01)
    if crack is not None:
        rng = np.random.default_rng(T.sd())
        n = secs(0.35)
        tt = np.arange(n) / SR
        f = midi_hz(76) * (1.0 + 0.06 * np.sin(TAU * 11.0 * tt)) * (1.0 - 0.04 * tt / 0.35)
        cr = soft_clip(np.sin(TAU * np.cumsum(f) / SR) * 2.5, 2.0) * np.exp(-tt / 0.2) * smoothstep(tt / 0.01)
        T.put('cornet', crack, pan2(0.5 * cr, 0.1), jitter=0.0)
    ir = make_ir(length=1.2, rt_low=0.8, rt_high=0.35, predelay=0.01, er_taps=6, er_span=0.03, er_gain=0.25,
                 seed=seed + 7, lowcut=70.0, highcut=6000.0, build=0.01)
    mix = {'cornet': (0.0, 0.2, (('hp', 200, 2), ('lp', 6000, 2))), 'horns': (-7.0, 0.2, BRASS_EQ),
           'tuba': (-4.0, 0.15, (('hp', 35, 2), ('lp', 1800, 2))), 'drums': (-8.0, 0.15, (('hp', 40, 2),))}
    return T.mixdown(mix, ir, target_rms=-20.0, master_lp=8000.0)


def rehearsal(rng: np.random.Generator, seed: int) -> np.ndarray:
    """The band rehearsing: the strain from the top, broken off with a cracked note, two baton taps on the music
    stand and the bandmaster's voice (no words), then the strain again, whole.  Stereo, ~26 s."""
    a = band_strain([0, 1, 2, 3, 4, 5], seed, cut=10.5, crack=9.75)
    b = band_strain([0, 1, 2, 3, 4, 5, 6, 7], seed + 1)
    spb = 60.0 / 112.0
    out = np.zeros((secs(30.0), 2))
    place(out, a, 0, circular=False)
    t1 = 10.5 * spb + 1.4
    for k in range(2):
        tap = impact(rng, random_modes(rng, 1500.0, 6000.0, 5, 0.02, 0.08), 0.15, hard=0.9, noise_amt=0.3)
        place(out, pan2(0.25 * tap, 0.0), secs(t1 + k * 0.32), circular=False)
    v = C3A.voice(rng, 2.6, 118.0, 'clipped', pause=(0.2, 0.4), phrase=(1.0, 2.2))
    place(out, pan2(0.5 * norm_peak(eq(v, ('hp', 140.0, 2), ('lp', 3000.0, 2), circular=False)), -0.1),
          secs(t1 + 1.0), circular=False)
    for k in range(2):
        tap = impact(rng, random_modes(rng, 1500.0, 6000.0, 5, 0.02, 0.08), 0.15, hard=0.9, noise_amt=0.3)
        place(out, pan2(0.25 * tap, 0.0), secs(t1 + 4.3 + k * spb), circular=False)
    place(out, b, secs(t1 + 4.3 + 2 * spb), circular=False)
    return out


def announcement(rng: np.random.Generator, f0: float, prof: str, chime_notes, dur: float = 5.5,
                 gap: float = 0.64) -> np.ndarray:
    """A station announcement: the chime, then a voice (prosody only, no words) through 1960s horn speakers at
    several distances.  Stereo, dry (the hall / the platform comes later)."""
    pre = np.zeros(secs(0.8 + gap * len(chime_notes)))
    for k, m in enumerate(chime_notes):
        place(pre, (1.0 - 0.08 * k) * C3A.chime_bar(rng, m), secs(gap * k), circular=False)
    v = C3A.voice(rng, dur, f0, prof, pause=(0.3, 0.7), phrase=(1.6, 2.8))
    y = np.zeros(len(pre) + len(v) + secs(0.3))
    place(y, 0.8 * norm_peak(pre), 0, circular=False)
    place(y, norm_peak(v), len(pre) - secs(0.5), circular=False)
    y = loudspeaker(y, rng, drive=2.0)
    out = np.zeros((len(y) + secs(0.3), 2))
    for (dl, pan, g) in [(0.0, -0.35, 1.0), (0.068, 0.4, 0.7), (0.15, 0.85, 0.45), (0.23, -0.85, 0.32)]:
        place(out, pan2(y * g, pan), secs(dl), circular=False)
    return out


def snow_on_iron(n: int, rng: np.random.Generator) -> np.ndarray:
    """Fine snow ticking on the iron canopy above the platform: a soft high grain (circular, stereo)."""
    rate = 60.0 * (1.0 + 0.4 * smooth_periodic(n, 12, rng))
    g = grain_cloud(rng, n / SR, rate, 3500.0, 9000.0, 0.001, 0.003)
    s = shaped_noise(n, rng, lambda f: mag_bp(f, 3000.0, 10000.0, 2), ch=2, corr=0.3)
    return 0.6 * pan2(norm_peak(g), 0.2) + 0.008 * s / max(rms(s), 1e-9)


def snow_slide(rng: np.random.Generator) -> np.ndarray:
    """A slab of snow sliding off the canopy's edge and falling onto the platform (mono, ~1.6 s)."""
    n = secs(1.8)
    t = np.arange(n) / SR
    rush = noise_burst(1.8, rng, 300.0, 4000.0, 1e6, attack=0.0)
    env = smoothstep(t / 0.3) * np.clip((1.05 - t) / 0.25, 0.0, 1.0)
    y = 0.5 * norm_peak(rush) * env
    fall = P2A.snow_steps(rng, 1, 0.2, 0.0, 0.0)
    fall = fall.mean(axis=1) if fall.ndim == 2 else fall
    place(y, 1.2 * norm_peak(fall[:secs(0.6)]), secs(1.1), circular=False)
    return fade(y, 0.0, 0.2)


# =============================================================================== sources: Berlin
def cutlery(rng: np.random.Generator, dur: float = 5.0, clinks: int = 11) -> np.ndarray:
    """The dining car: forks and knives on porcelain, a cup set down on its saucer, a spoon in a glass (mono)."""
    y = np.zeros(secs(dur + 0.5))
    for _ in range(clinks):
        tt = rng.uniform(0.0, dur)
        kind = rng.random()
        if kind < 0.5:             # cutlery on a plate
            k = impact(rng, random_modes(rng, 2400.0, 9000.0, 6, 0.02, 0.12), 0.25, hard=0.9, noise_amt=0.15)
            g = 0.5
        elif kind < 0.8:           # cup on saucer
            k = impact(rng, random_modes(rng, 1400.0, 5200.0, 7, 0.05, 0.25), 0.45, hard=0.7, noise_amt=0.1)
            g = 0.7
        else:                      # spoon in a tea glass
            k = impact(rng, [(rng.uniform(3200, 3600), 1.0, 0.5), (rng.uniform(5200, 5900), 0.5, 0.3)], 0.6,
                       hard=0.9, noise_amt=0.05)
            g = 0.45
        place(y, g * k, secs(tt), circular=False)
    return y


def counter_bell(rng: np.random.Generator) -> np.ndarray:
    """The kiosk's counter bell: one tap on a small dome bell (mono, ~1.4 s)."""
    y = modal(bell_modes(rng.uniform(2050.0, 2150.0), 'hand'), 1.4, seed=int(rng.integers(1 << 30)), attack=0.001)
    m = noise_burst(0.01, rng, 2000.0, 9000.0, 0.003)
    y[:len(m)] += 0.15 * norm_peak(m)
    return fade(norm_peak(y), 0.0, 0.3)


def sbahn_pass(rng: np.random.Generator, dur: float = 15.0) -> np.ndarray:
    """An S-Bahn train crossing its brick viaduct a few streets away: the motors' whine rising and falling, the
    wheels drumming over the joints, the viaduct's hollow rumble (mono, far)."""
    n = secs(dur)
    t = np.arange(n) / SR
    mid = dur * 0.45
    env = bump(n, mid * 0.8, (dur - mid) * 0.75, peak_at=mid)
    rum = noise_burst(dur, rng, 30.0, 300.0, 1e6, attack=0.0)
    y = 0.65 * norm_peak(rum) * env
    f = 520.0 * (1.0 + 0.25 * smoothstep(t / mid)) * (1.0 - 0.012 * np.tanh((t - mid) / 1.5))
    ph = np.cumsum(f) / SR
    wh = np.sin(TAU * ph) + 0.35 * np.sin(TAU * 2 * ph) + 0.18 * np.sin(TAU * 3.02 * ph)
    y += 0.05 * wh * env ** 1.5
    tc = 0.8
    while tc < dur - 0.5:
        for off in (0.0, 0.09):
            kn = impact(rng, random_modes(rng, 160.0, 1600.0, 6, 0.03, 0.12), 0.22, hard=0.4, noise_amt=0.3)
            place(y, 0.2 * kn * float(np.interp(tc + off, t, env)) ** 1.4, secs(tc + off), circular=False)
        tc += rng.uniform(0.38, 0.46)
    return fade(eq(y, ('lp', 2200.0, 2), ('hp', 28.0, 2), circular=False), 0.5, 2.0)


def baby_fuss(rng: np.random.Generator) -> np.ndarray:
    """The Schulz baby waking for a moment behind the first-floor window: a few fretful cries, a hiccup, quiet again
    (somebody picks it up).  Mono, dry; muffled by the glass later."""
    out = np.zeros(secs(5.0))
    t0 = 0.2
    for k, (d, f0) in enumerate([(0.42, 430.0), (0.36, 470.0), (0.85, 500.0), (0.5, 455.0), (0.3, 420.0)]):
        m = secs(d)
        u = np.arange(m) / m
        f = f0 * rng.uniform(0.96, 1.04) * (1.0 + 0.12 * np.sin(np.pi * u) - 0.08 * u) \
            * (1.0 + 0.012 * np.sin(TAU * 6.0 * u * d))
        ph = np.cumsum(f) / SR
        src = sum(h ** -1.0 * np.sin(TAU * h * ph) for h in range(1, 12))
        env = np.sin(np.pi * np.clip(u * 1.05, 0, 1)) ** 0.6
        y = eq(src * env, ('bell', 1100.0, 8.0, 0.7), ('bell', 2700.0, 6.0, 0.7), ('hp', 250.0, 2),
               ('lp', 5000.0, 2), circular=False)
        place(out, norm_peak(y) * (0.6 + 0.4 * (k == 2)), secs(t0), circular=False)
        t0 += d + rng.uniform(0.25, 0.55)
    return fade(out, 0.0, 0.3)


def card_game(rng: np.random.Generator, dur: float = 7.0) -> np.ndarray:
    """A card game behind a lit window: cards slapped on the oilcloth, a fist on the table, voices and one laugh
    (no words).  Mono."""
    y = np.zeros(secs(dur))
    for k in range(6):
        tt = 0.4 + k * rng.uniform(0.7, 1.0)
        if tt > dur - 0.5:
            break
        s = noise_burst(0.06, rng, 600.0, 6000.0, 0.03) + 0.4 * modal([(rng.uniform(180, 240), 1.0, 0.06)], 0.06,
                                                                     seed=int(rng.integers(1 << 30)))
        place(y, 0.55 * norm_peak(s), secs(tt), circular=False)
    fist = wood_knock(rng, 95.0, 0.4, 0.3)
    place(y, 0.8 * norm_peak(fist), secs(dur * 0.62), circular=False)
    v = C3A.voice(rng, dur, 112.0, 'even', pause=(0.3, 1.0), phrase=(0.8, 2.0))
    v2 = C3A.voice(rng, dur, 132.0, 'lilt', pause=(0.6, 1.4), phrase=(0.6, 1.4))
    y += 0.35 * norm_peak(v) + 0.25 * norm_peak(v2)
    # a short laugh: voiced 'ha' pulses
    m = secs(0.9)
    tb = np.arange(m) / SR
    pulses = np.clip(np.sin(TAU * 5.5 * tb), 0.0, None) ** 2 * np.exp(-tb / 0.5)
    f = 150.0 * (1.0 + 0.1 * np.sin(TAU * 5.5 * tb))
    lg = sum(h ** -1.0 * np.sin(TAU * h * np.cumsum(f) / SR) for h in range(1, 10)) * pulses
    lg = eq(lg + 0.3 * rng.standard_normal(m) * pulses, ('bell', 700.0, 6.0, 0.8), ('lp', 3500.0, 2),
            circular=False)
    place(y, 0.5 * norm_peak(lg), secs(dur * 0.66), circular=False)
    return fade(y, 0.2, 0.4)


def gutter_drips(n: int, rng: np.random.Generator, ir: np.ndarray) -> np.ndarray:
    """A broken gutter dripping into the yard: a drop every ~1.7 s into a puddle, now and then onto the tin of the
    rain barrel (circular, stereo)."""
    y = np.zeros(n)
    t = 0.6
    while t < n / SR - 0.3:
        if rng.random() < 0.18:
            d = impact(rng, random_modes(rng, 900.0, 3800.0, 5, 0.05, 0.2), 0.3, hard=0.7, noise_amt=0.1)
            place(y, 0.5 * d, secs(t), circular=True)
        else:
            place(y, C4A.drip(rng, 900.0 * rng.uniform(0.96, 1.04)), secs(t), circular=True)
        t += rng.uniform(1.55, 1.9)
    st = pan2(y, 0.35)
    return st + 0.6 * fftconv(st, ir, circular=True)


def hall_hum(n: int, rng: np.random.Generator) -> np.ndarray:
    """The Great Hall's distant hum over the roofs: its ventilation and transformers, a low chord that beats very
    slowly, a breath of air on top (circular, mono)."""
    y = np.zeros(n)
    for f, a in ((49.0, 1.0), (98.3, 0.6), (146.7, 0.35), (196.5, 0.25)):
        y += a * periodic_tone(n, f, rng, fm=0.002 * smooth_periodic(n, 5, rng))   # a slow drift: the beating
    y *= 1.0 + 0.2 * smooth_periodic(n, 6, rng)
    air = shaped_noise(n, rng, lambda f: mag_bp(f, 60.0, 400.0, 2))
    air = air[:, 0] if air.ndim == 2 else air
    return y / max(rms(y), 1e-9) + 0.6 * air / max(rms(air), 1e-9)


# Lenz's radio: an original slow foxtrot (F major, 128 bpm, 32 bars of 4/4 = 60 s, circular) -- muted trumpet tune,
# piano comping, walking bass, brushes.  (bar, beat, dur, midi) per phrase.
FOX_TUNE = [(0, 0, 1.5, 72), (0, 1.5, 0.5, 74), (0, 2, 2, 77), (1, 0, 1, 76), (1, 1, 1, 74), (1, 2, 2, 72),
            (2, 0, 1.5, 70), (2, 1.5, 0.5, 72), (2, 2, 1, 74), (2, 3, 1, 70), (3, 0, 4, 69),
            (4, 0, 1.5, 72), (4, 1.5, 0.5, 74), (4, 2, 2, 77), (5, 0, 1, 81), (5, 1, 1, 79), (5, 2, 2, 77),
            (6, 0, 1, 76), (6, 1, 1, 74), (6, 2, 1, 76), (6, 3, 1, 79), (7, 0, 4, 77)]
FOX_CHORDS = ['F', 'Dm', 'Gm', 'C7', 'F', 'D7', 'Gm', 'C7']
FOX_HARM = {'F': (41, [57, 60, 64]), 'Dm': (38, [57, 60, 65]), 'Gm': (43, [58, 62, 65]), 'C7': (36, [58, 60, 64]),
            'D7': (38, [57, 60, 66])}


def radio_foxtrot() -> np.ndarray:
    """The studio recording of the dance tune (stereo, 60 s circular) before it goes through Lenz's radio."""
    name = 'c4p2_foxtrot'
    T = Track(name, bpm=128, beats=128, loop=True, seed=seed_of(name))
    rng = np.random.default_rng(seed_of(name, 2))
    for rep in range(4):
        for (bar, bt, d, m) in FOX_TUNE:
            b = (rep * 8 + bar) * 4 + bt
            sig = brass_note(m, d * T.spb * 0.9, vel=0.45, attack=0.05, release=0.3, players=1, seed=T.sd(),
                             bright=0.5, scoop=8.0, formant=1300.0)
            T.put('trumpet', b, sig, jitter=0.01)
    for bar in range(32):
        bass, voicing = FOX_HARM[FOX_CHORDS[bar % 8]]
        b0 = bar * 4
        for k, off in enumerate((0, 1, 2, 3)):
            m = bass + (0, 7, 12, 7)[k]
            T.piano([(b0 + off, 1, m)], vel=0.4, stem='bass', felt=0.6, decay=0.5, legato=0.8)
        for off in (1, 3):
            T.piano([(b0 + off, 0.5, m) for m in voicing], vel=0.22, stem='comp', felt=0.5, decay=0.4, legato=0.5)
        for off in (0, 1, 2, 3):
            br = noise_burst(0.12, rng, 2500.0, 9000.0, 0.08)
            T.put('brush', b0 + off, to_stereo(norm_peak(br)) * (0.5 if off % 2 else 0.3), jitter=0.01)
    ir = hall_ir(seed_of(name, 1), rt_low=1.4, rt_high=0.7, predelay=0.02)
    mix = {'trumpet': (0.0, 0.25, (('hp', 250, 2), ('lp', 5000, 2))), 'bass': (-3.0, 0.1, ()),
           'comp': (-7.0, 0.2, ()), 'brush': (-14.0, 0.15, (('hp', 2000, 2),))}
    return T.mixdown(mix, ir, target_rms=-20.0, master_lp=8000.0)


# =============================================================================== ambiences
def amb_karsk_depot():
    name = 'amb_karsk_depot'
    rng = R(name)
    M = Mix()
    yard = ir_depot(seed_of(name, 1))
    farir = ir_outdoor_far(seed_of(name, 2))
    # dawn air over the yard: a cold wind with gusts, a whistle in the signal wires, the town far off
    g = gust_curve(N, rng, [(5.0, 0.6, 2.0, 3.0), (22.0, 0.45, 1.8, 2.6), (37.5, 0.7, 2.4, 3.2), (52.0, 0.5, 1.8, 2.6)],
                   base=0.3, turb=0.07)
    w = wind(N, rng, g, lp_base=280.0, lp_gust=900.0, whistle=0.2, whistle_f=(820.0, 1240.0), corr=0.45,
             pan_sweep=0.25)
    M.bed(w, -8.0)
    town = shaped_noise(N, rng, lambda f: mag_bp(f, 30.0, 220.0, 2), ch=2, corr=0.8)
    town *= (1.0 + 0.25 * smooth_periodic(N, 8, rng))[:, None]
    M.bed(town, -13.0)
    # the standing engine at the roundhouse (left): its blower roaring
    bl = blower(N, rng)
    st = pan2(eq(bl, ('lp', 2600.0, 2), circular=True), -0.6)
    M.bed(st + 0.6 * fftconv(st, yard, circular=True), -12.0)
    # Kolonne 4 at the coal stage (centre-right): six workers, one rhythm each
    gang = shovel_gang(rng, N, yard, [(3.4, 0.05, 0.25), (3.9, 0.3, 0.4), (3.1, -0.15, 0.55), (4.3, 0.5, 0.6),
                                      (3.6, 0.7, 0.75), (4.0, -0.4, 0.8)])
    M.bed(gang, -6.0)
    # the guard's barrel fire (right, near)
    fire = P2A.fire_bed(rng, N, 0.3)
    fire = eq(fire, ('lp', 3200.0, 2), circular=True)
    fire[:, 0] *= 0.45
    M.bed(fire, -15.0)
    # the safety valve lifting twice
    for t0, d in ((14.2, 3.2), (44.6, 4.2)):
        M.event(far(safety_valve(rng, d), yard, lp=7500.0, wet=0.7, dry=0.7, pan=-0.55), t0, -2.0)
    # a yard dog (far, left), twice
    for t0, b in ((8.4, 2), (33.0, 3)):
        M.event(far(dog_bark(rng, rng.uniform(340.0, 400.0), b), farir, lp=2800.0, wet=1.0, dry=0.3, pan=-0.75), t0,
                -3.0, mode='peak')
    # the canteen radio: an announcer behind a closed window (far right)
    rad = radio_broadcast(rng, N, 128.0, 'slow')
    M.bed(pan2(rad, 0.75) + 0.4 * fftconv(pan2(rad, 0.75), yard, circular=True), -24.0)
    # sparrows in the roundhouse eaves
    for t0, pan in ((3.1, -0.4), (19.4, -0.2), (27.6, 0.3), (48.2, -0.5), (56.0, 0.1)):
        M.event(far(sparrows(rng, int(rng.integers(4, 9))), yard, lp=8000.0, wet=0.35, dry=1.0, pan=pan), t0,
                -2.0, mode='peak')
    # a fitter's hammer in the roundhouse, couplings bumping in the yard
    M.event(far(hammer_far(rng, 4), yard, lp=4000.0, wet=0.8, dry=0.4, pan=-0.35), 25.5, 0.0, mode='peak')
    M.event(far(shunting_chain(rng, 3, 0.6), farir, lp=1800.0, wet=1.0, dry=0.3, pan=0.45), 40.0, 2.0)
    # a goods train on the main line behind the depot
    M.event(far(freight_pass(rng, 18.0, 16), farir, lp=1500.0, wet=0.9, dry=0.5, pan=0.2), 0.0, -3.0)
    # boots on frozen cinders: somebody crosses the yard
    M.event(far(C3A.walker(rng, 12, 0.6, -0.5, 0.3), yard, lp=3000.0, wet=0.8, dry=0.4), 50.5, -2.0)
    return M.master(-25.0, lp=11000.0), (0, N)


def amb_karsk_platform():
    name = 'amb_karsk_platform'
    rng = R(name)
    M = Mix()
    plat = ir_platform(seed_of(name, 1))
    farir = ir_outdoor_far(seed_of(name, 2))
    # the evening: still air with a little wind, snow falling on the iron canopy
    g = gust_curve(N, rng, [(9.0, 0.35, 2.0, 3.0), (31.0, 0.45, 2.4, 3.4), (49.0, 0.3, 2.0, 3.0)], base=0.22,
                   turb=0.05)
    w = wind(N, rng, g, lp_base=240.0, lp_gust=700.0, whistle=0.05, whistle_f=(500.0, 700.0), corr=0.5,
             pan_sweep=0.2)
    M.bed(w, -10.0)
    M.bed(snow_on_iron(N, rng), -22.0)
    town = shaped_noise(N, rng, lambda f: mag_bp(f, 30.0, 200.0, 2), ch=2, corr=0.8)
    M.bed(town, -14.0)
    # the westbound express on platform 1 (left): air pumps breathing, a steady steam leak
    period = 60.0 / 17.0
    for k in range(17):
        b = C3A.loco_breath(rng, rng.uniform(0.8, 1.0))
        M.event(far(b, plat, lp=4200.0, wet=0.5, dry=0.8, pan=-0.6), 0.5 + k * period + rng.normal(0.0, 0.15),
                -5.0 + rng.uniform(-1.0, 0.5))
    leak = shaped_noise(N, rng, lambda f: mag_bp(f, 2000.0, 9000.0, 2))
    leak = leak[:, 0] if leak.ndim == 2 else leak
    leak *= 1.0 + 0.2 * smooth_periodic(N, 20, rng)
    M.bed(pan2(leak, -0.7), -20.0)
    # the crowd: officials, the press, workers kept back at the barrier -- talkers in two cadences
    profs = ['slow', 'even', 'clipped', 'lilt']
    specs = []
    for i, f0 in enumerate([98, 106, 112, 121, 128, 136, 186, 198, 214, 226]):
        dist = rng.uniform(0.2, 1.0)
        specs.append((f0 * (1.0 + rng.normal(0.0, 0.02)), profs[(i * 3 + int(rng.integers(4))) % 4], -2.0 - 8.0 * dist,
                      float(np.clip(rng.normal(0.15, 0.45), -0.8, 0.9)), 3200.0 - 1800.0 * dist, (0.6, 2.6),
                      (1.0, 3.2)))
    crowd = C3A.talkers(rng, N, specs)
    M.bed(0.5 * crowd + 0.8 * fftconv(crowd, plat, circular=True), -7.0)
    # the depot band rehearsing the march across the tracks (far right)
    reh = rehearsal(rng, seed_of(name, 3))
    M.event(far(reh.mean(axis=1), farir, lp=3000.0, wet=1.0, dry=0.35, pan=0.55), 4.0, -4.0)
    reh2 = band_strain([4, 5, 6, 7, 0, 1, 2, 3], seed_of(name, 4))
    M.event(far(reh2.mean(axis=1), farir, lp=3000.0, wet=1.0, dry=0.35, pan=0.55), 39.0, -4.0)
    # announcements on the platform loudspeakers (a woman's voice, a Russian cadence -- no words)
    for t0 in (13.0, 47.5):
        an = announcement(rng, 196.0, 'slow', [79, 76], dur=5.0)
        M.event(far(an, plat, wet=0.9, dry=0.5), t0, -3.0)
    # snow sliding off the canopy, steps in the snow, a camera shutter in the press group
    for t0, pan in ((22.6, 0.3), (55.4, -0.25)):
        M.event(far(snow_slide(rng), plat, lp=5000.0, wet=0.5, dry=0.8, pan=pan), t0, -6.0)
    M.event(far(P2A.snow_steps(rng, 9, 0.62, 0.6, -0.2).mean(axis=1), plat, lp=4000.0, wet=0.5, dry=0.8), 28.0,
            -6.0)
    sh = impact(rng, random_modes(rng, 2000.0, 7000.0, 5, 0.01, 0.04), 0.1, hard=0.9, noise_amt=0.4)
    M.event(far(sh, plat, lp=8000.0, wet=0.4, dry=0.8, pan=0.2), 35.2, -2.0, mode='peak')
    return M.master(-25.0, lp=11000.0), (0, N)


def amb_berlin_station():
    name = 'amb_berlin_station'
    rng = R(name)
    M = Mix()
    hall = ir_ostbahnhof(seed_of(name, 1))
    square = C3A.ir_station(seed_of(name, 2))
    farir = ir_outdoor_far(seed_of(name, 3))
    # the hall's air: a grey hush under the glass, the city outside
    air = shaped_noise(N, rng, lambda f: mag_bp(f, 40.0, 1500.0, 2) * (np.maximum(f, 20.0) / 200.0) ** -0.5, ch=2,
                       corr=0.5)
    air *= (1.0 + 0.12 * smooth_periodic(N, 9, rng))[:, None]
    M.bed(air, -5.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 28.0, 200.0, 2), ch=2, corr=0.8)
    M.bed(city, -12.0)
    # the crowd of the evening express: travellers, porters, soldiers on leave -- a German cadence
    profs = ['clipped', 'even', 'clipped', 'lilt']
    specs = []
    for i, f0 in enumerate([96, 104, 110, 118, 126, 134, 142, 184, 196, 206, 218, 234]):
        dist = rng.uniform(0.2, 1.0)
        specs.append((f0 * (1.0 + rng.normal(0.0, 0.02)), profs[(i + int(rng.integers(4))) % 4], -2.0 - 8.0 * dist,
                      float(np.clip(rng.normal(-0.1, 0.45), -0.85, 0.85)), 3400.0 - 2000.0 * dist, (0.5, 2.4),
                      (1.0, 3.4)))
    crowd = C3A.talkers(rng, N, specs)
    M.bed(0.35 * crowd + fftconv(crowd, hall, circular=True), -5.0)
    # the express's engine under the roof (left): steam hiss, the air pump
    hiss = shaped_noise(N, rng, lambda f: mag_bp(f, 1800.0, 8500.0, 2))
    hiss = hiss[:, 0] if hiss.ndim == 2 else hiss
    hiss *= (1.0 + 0.2 * smooth_periodic(N, 25, rng))
    hs = pan2(hiss, -0.7)
    M.bed(0.5 * hs + 0.7 * fftconv(hs, hall, circular=True), -15.0)
    period = 60.0 / 15.0
    for k in range(15):
        b = C3A.loco_breath(rng, rng.uniform(0.75, 0.95))
        M.event(far(b, hall, lp=4000.0, wet=0.8, dry=0.5, pan=-0.65), 1.2 + k * period + rng.normal(0.0, 0.2),
                -6.0 + rng.uniform(-1.0, 0.5))
    M.event(far(C3A.steam_release(rng, 3.0), hall, lp=7000.0, wet=0.9, dry=0.5, pan=-0.7), 41.0, -6.0)
    # announcements under the glass (a man's voice, a German cadence -- no words), after the gong
    for t0 in (6.0, 36.5):
        an = announcement(rng, 122.0, 'clipped', [72, 76, 79], dur=5.5, gap=0.42)
        M.event(far(an, hall, wet=1.0, dry=0.3), t0, -3.0)
    # luggage carts, steps on stone, pigeons in the roof girders
    M.event(far(C3A.luggage_cart(rng), hall, lp=5000.0, wet=0.8, dry=0.6), 16.5, -6.0)
    M.event(far(C3A.luggage_cart(rng), hall, lp=4200.0, wet=0.9, dry=0.5), 49.0, -8.0)
    M.event(far(C3A.walker(rng, 14, 0.52, -0.5, 0.4), hall, lp=4600.0, wet=1.0, dry=0.35), 2.0, 2.0)
    M.event(far(C3A.walker(rng, 12, 0.44, 0.6, -0.2, heels=True), hall, lp=5200.0, wet=1.0, dry=0.4), 27.0, 1.0)
    M.event(far(C3A.walker(rng, 16, 0.6, 0.2, 0.8), hall, lp=3800.0, wet=1.0, dry=0.3), 44.0, 0.0)
    M.event(far(C3A.pigeons(rng, [(0.0, 8, -0.3, True)]), hall, lp=6000.0, wet=1.0, dry=0.5), 11.4, -7.0)
    M.event(far(C3A.pigeons(rng, [(0.0, 12, 0.2, False), (0.15, 10, 0.4, False)]), hall, lp=6500.0, wet=1.0,
                dry=0.5), 31.8, -5.0)
    # the kiosk's counter bell (right), the dining car's cutlery behind its windows (left)
    for t0 in (20.2, 53.7):
        M.event(far(counter_bell(rng), hall, lp=7000.0, wet=0.7, dry=0.7, pan=0.55), t0, 2.0, mode='peak')
    for t0 in (9.5, 33.0, 46.0):
        cu = eq(cutlery(rng, 4.0, int(rng.integers(7, 12))), ('lp', 3500.0, 2), circular=False)
        M.event(far(cu, hall, wet=0.6, dry=0.6, pan=-0.35), t0, -2.0, mode='peak')
    # a tram ringing out on the forecourt (far right, through the doors)
    tb = tram_bell(rng, 2, 760.0)
    M.event(far(tb, square, lp=2400.0, hp=260.0, wet=0.9, dry=0.4, pan=0.8), 24.6, 2.0, mode='peak')
    M.event(far(tram_bell(rng, 1, 760.0), farir, lp=2000.0, hp=260.0, wet=1.0, dry=0.3, pan=0.85), 57.0, -2.0,
            mode='peak')
    return M.master(-24.0, lp=11500.0), (0, N)


def amb_berlin_courtyard():
    name = 'amb_berlin_courtyard'
    rng = R(name)
    M = Mix()
    court = ir_court(seed_of(name, 1))
    farir = ir_outdoor_far(seed_of(name, 2))
    # the night over the roofs: the Hall's distant hum, the city's low breath
    M.bed(pan2(eq(hall_hum(N, rng), ('lp', 700.0, 2), circular=True), 0.1), -15.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 25.0, 180.0, 2), ch=2, corr=0.85)
    M.bed(city, -11.0)
    # wind in the gate passage (left): a low draught whistling in the gap of the gate
    g = gust_curve(N, rng, [(7.0, 0.55, 2.0, 3.0), (26.0, 0.7, 2.4, 3.4), (45.0, 0.5, 2.0, 3.0)], base=0.25,
                   turb=0.06)
    w = wind(N, rng, g, lp_base=220.0, lp_gust=760.0, whistle=0.22, whistle_f=(560.0, 820.0), corr=0.6,
             pan_sweep=0.15)
    w[:, 1] *= 0.6
    M.bed(w + 0.4 * fftconv(w, court, circular=True), -9.0)
    # Lenz's radio, third floor of the front house: the dance tune through a small set and the window glass
    fox = P2A.radio_set(radio_foxtrot(), rng, circular=True)
    fox = eq(fox, ('lp', 2200.0, 2), ('hp', 260.0, 2), circular=True)
    fs = pan2(fox, -0.35)
    M.bed(0.4 * fs + fftconv(fs, court, circular=True), -16.0)
    # the gutter dripping into the yard (right)
    M.bed(gutter_drips(N, rng, court), -20.0)
    # the Schulz baby (first floor, behind glass), once
    bb = eq(baby_fuss(rng), ('lp', 1800.0, 2), circular=False)
    M.event(far(bb, court, wet=0.7, dry=0.6, pan=-0.15), 18.5, -12.0)
    # the card game behind a lit window (back house)
    cg = eq(card_game(rng, 7.0), ('lp', 2000.0, 2), circular=False)
    M.event(far(cg, court, wet=0.7, dry=0.6, pan=0.4), 33.0, -14.0)
    # a dog far off, twice
    for t0, b in ((11.0, 2), (52.0, 2)):
        M.event(far(dog_bark(rng, rng.uniform(420.0, 470.0), b), farir, lp=2000.0, wet=1.0, dry=0.2, pan=0.6), t0,
                -5.0, mode='peak')
    # the S-Bahn crossing its viaduct a few streets away
    for t0 in (2.0, 38.0):
        sb = sbahn_pass(rng, 15.0)
        M.event(far(sb, farir, lp=1600.0, wet=1.0, dry=0.4, pan=0.3), t0, -5.0)
    # a window shut somewhere above, a cough, a toilet's chain in the back house
    M.event(far(wood_knock(rng, 140.0, 0.5, 0.5), court, wet=0.8, dry=0.5, pan=0.25), 24.4, 0.0, mode='peak')
    ch = impact(rng, random_modes(rng, 900.0, 4500.0, 6, 0.04, 0.2), 0.4, hard=0.6, noise_amt=0.3)
    M.event(far(ch, court, lp=3000.0, wet=0.8, dry=0.4, pan=0.5), 46.6, -6.0, mode='peak')
    return M.master(-26.0, lp=10000.0), (0, N)


# =============================================================================== music
LOW_STR_EQ = C4A.LOW_STR_EQ
REED_EQ = C4A.REED_EQ


def mus_c4p2_karsk():
    """The bayan breath of part 1, slower, over low strings in D Aeolian; K returns augmented in the cellos."""
    name = 'mus_c4p2_karsk'
    T = Track(name, bpm=45, beats=64, loop=True, seed=seed_of(name))
    plan = [(0, [26, 38, 45], 8.6), (8, [26, 38, 45, 53], 8.6), (16, [22, 34, 41, 50], 8.6),
            (24, [31, 38, 46, 50], 8.6), (32, [26, 38, 45], 8.6), (40, [22, 34, 41, 53], 8.6),
            (48, [28, 40, 47, 52], 8.6), (56, [21, 33, 40, 49], 8.6)]
    for b, ch, d in plan:
        T.strings(b, d, ch, vel=0.38, stem='low', attack=3.0, release=3.6, bright=0.22, vib=3.0, voices=3,
                  bass_boost=1.1)
    # the bayan: a breath per phrase, slower than part 1 (the bellows drawn out), the reversal later in the breath
    C4A.bayan_breath(T, 2.0, 9.0, [50, 53, 57], vel=0.34, reversal=0.58)          # Dm
    C4A.bayan_breath(T, 18.0, 9.0, [46, 50, 57], vel=0.32, reversal=0.6)          # Bbmaj7 colour (Bb D A)
    C4A.bayan_breath(T, 34.0, 9.0, [50, 52, 57], vel=0.33, reversal=0.58)         # Dsus2
    C4A.bayan_breath(T, 50.0, 7.5, [45, 52, 57], vel=0.28, reversal=0.62)         # A E A: open, into the loop
    # K, augmented, in the cellos (second half): the question only -- the answer stays in part 1
    for (bt, d, m) in K_A:
        T.strings(32.5 + 2 * bt, 2 * d * 0.95, [m - 24], vel=0.30, stem='cello', attack=1.2, release=2.0,
                  bright=0.32, vib=5.0, voices=2)
    # felt piano: three low notes, far apart; a high harmonic shimmer near the loop point
    T.piano([(12, 2, 38), (28, 2, 34), (44, 2, 38)], vel=0.28, felt=0.9, decay=0.9, pan=0.1)
    T.strings(56, 7.0, [81], vel=0.10, stem='hi', harmonic=True, attack=3.0, release=2.0, vib=2.0)
    ir = hall_ir(seed_of(name, 1), rt_low=3.2, rt_high=1.2, predelay=0.03)
    mix = {'low': (0.0, 0.28, LOW_STR_EQ), 'cello': (-2.0, 0.3, STR_EQ), 'bayan': (-2.5, 0.22, REED_EQ),
           'piano': (-8.0, 0.32, C3A.FELT_EQ), 'hi': (-17.0, 0.45, STR_HI_EQ)}
    out = T.mixdown(mix, ir, target_rms=-22.0, master_lp=8000.0)
    out = np.roll(out, int(round(0.5 * T.spb * SR)), axis=0)       # the loop point sits in a rest
    return out, (0, out.shape[0])


MACHINE_ACC = C4A.MACHINE_ACC


def mus_c4p2_berlin():
    """Piano and low strings in G Aeolian; the clockwork pulse of part 1 (3+3+2) on a muted piano, softer and
    slower; B on the piano, a viola line; the machine tick only on the downbeats."""
    name = 'mus_c4p2_berlin'
    T = Track(name, bpm=63, beats=64, loop=True, seed=seed_of(name))
    rng = np.random.default_rng(seed_of(name, 2))
    bars = [('Gm', 55, 62), ('Gm', 55, 62), ('Eb', 51, 58), ('Eb', 51, 58), ('Cm', 48, 55), ('Cm', 48, 55),
            ('Dsus', 50, 57), ('Dsus', 50, 57), ('Gm', 55, 62), ('Gm', 55, 62), ('Ab', 56, 63), ('Eb', 51, 58),
            ('Cm', 48, 55), ('Cm', 48, 55), ('Dsus', 50, 57), ('Gm', 55, 62)]
    for i, (_, lo, hi) in enumerate(bars):
        b0 = 4 * i
        for k in range(8):
            m = lo if k in (0, 3, 6) else hi
            T.piano([(b0 + 0.5 * k, 0.5, m)], vel=MACHINE_ACC[k] * 0.85, stem='pulse', felt=1.0, decay=0.32,
                    legato=0.5)
        sig = to_stereo(C4A.machine_tick(rng, heavy=(i % 2 == 0)))
        T.put('machine', b0, sig * 0.9, jitter=0.002)
    lows = [(0, [31, 43]), (8, [27, 39]), (16, [24, 36]), (24, [26, 38]), (32, [31, 43]), (40, [32, 44]),
            (44, [27, 39]), (48, [24, 36]), (56, [26, 38]), (60, [31, 43])]
    for b, ch in lows:
        T.strings(b, 7.6 if b not in (40, 44, 60) else 3.8, ch, vel=0.36, stem='low', attack=1.6, release=2.4,
                  bright=0.2, vib=3.0, voices=3, bass_boost=1.0)
    # the viola: a slow counter-line in the middle register
    for b, m in ((8, 62), (16, 63), (24, 62), (28, 60), (40, 63), (48, 60), (56, 62)):
        T.strings(b + 0.5, 3.6, [m], vel=0.2, stem='viola', attack=1.0, release=1.8, bright=0.3, vib=4.5, voices=2)
    # B on the piano (middle) and B_2 low, both a little slower than the pulse
    T.piano(tr(B_1, octave=0), vel=0.30, beat0=16, felt=0.85, decay=0.8, pan=0.15, stem='theme')
    T.piano(tr(B_2, octave=-1), vel=0.30, beat0=44, felt=0.95, decay=0.7, pan=0.1, stem='theme', legato=0.9)
    ir = hall_ir(seed_of(name, 1), rt_low=2.6, rt_high=1.1, predelay=0.03)
    mix = {'pulse': (-2.0, 0.18, MUTED_EQ), 'machine': (-16.0, 0.12, (('hp', 200, 2), ('lp', 7000, 2))),
           'low': (-1.0, 0.25, LOW_STR_EQ), 'viola': (-8.0, 0.3, STR_EQ), 'theme': (-2.0, 0.3, C3A.FELT_EQ)}
    out = T.mixdown(mix, ir, target_rms=-21.0, master_lp=9000.0)
    out = np.roll(out, int(round(0.25 * T.spb * SR)), axis=0)      # the loop point sits between two pulses
    return out, (0, out.shape[0])


def mus_c4p2_clock():
    """LS_C4P2_Clock (one-shot, from the film's first frame): one clock for both cities.  k1 Berlin: the tick
    begins, the clockwork pulse and B on the celesta; k2 Kordon-17 from far: the drone grows, the G pedal under
    it; k3 Karsk: the bayan breathes, K on the felt piano; k4: both together, B bends its Eb to E; k5: the tick
    stops (CLOCK_STOP), a last low dyad dies away, silence."""
    name = 'mus_c4p2_clock'
    k1, k2, k3, k4, k5, end = CLOCK_SHOTS
    T = Track(name, bpm=60, beats=CLOCK_LEN, loop=False, seed=seed_of(name), tail=0.0)
    rng = np.random.default_rng(seed_of(name, 2))
    for i in range(int(CLOCK_STOP)):
        tk = clock_tick(np.random.default_rng(seed_of(name, 10 + i % 6)), i % 2 == 1)
        T.put('clock', i, to_stereo(tk) * (1.0 if i % 2 == 0 else 0.84), jitter=0.0)
    # k1 -- Berlin, 23.40: the clockwork pulse, B's opening on the celesta
    for k in range(8):
        T.piano([(k1 + 0.5 + 0.5 * k, 0.5, 55 if k in (0, 3, 6) else 62)], vel=MACHINE_ACC[k] * 0.7, stem='pulse',
                felt=1.0, decay=0.3, legato=0.5)
    T.celesta(tr(B_1[:5], beat0=k1 + 1.0), vel=0.30, pan=0.22)
    # k2 -- Kordon-17 from far: the drone grows under the G pedal
    T.strings(k2, 7.5, [38, 45], vel=0.34, stem='drone', attack=3.0, release=3.0, bright=0.2, vib=3.0, voices=4,
              swell=0.6)
    T.brass(k2 + 1.0, 5.5, [31, 43], vel=0.24, stem='pedal', attack=2.0, release=2.5, bright=0.14)
    T.strings(k2 + 2.0, 5.0, [74, 75], vel=0.07, stem='hi', harmonic=True, attack=2.5, release=2.0, vib=1.5)
    # k3 -- Karsk, 1.40: the bayan breathes, K on the felt piano
    C4A.bayan_breath(T, k3, 5.5, [50, 53, 57], vel=0.30, reversal=0.6)
    T.piano(tr(K_A[:4], beat0=k3 + 0.5), vel=0.36, felt=0.8, decay=0.95, pan=-0.12)
    # k4 -- both on one clock: K's answer on the piano, B's close on the celesta with its Eb bent to E
    # (both phrases end on the last tick, CLOCK_STOP - 1: nothing new sounds where the tick stops)
    T.piano(tr(K_B[2:], beat0=k4 - 3.0), vel=0.32, felt=0.8, decay=0.95, pan=-0.12)
    b2 = [(b, d, 64 if m == 63 else m) for (b, d, m) in B_2[4:]]
    T.celesta(tr(b2, beat0=k4 - 5.0, octave=1), vel=0.26, pan=0.22)
    T.strings(k3 + 1.0, 8.0, [38, 45], vel=0.26, stem='drone', attack=2.0, release=1.6, bright=0.2, vib=3.0, voices=4)
    # k5 -- the tick stops: one low dyad from both keys (D and G) left to die away, then nothing
    T.piano([(k5 - 1.0, 2.0, 38), (k5 - 1.0, 2.0, 43)], vel=0.24, felt=0.95, decay=0.8, pan=0.0, stem='last')
    ir = hall_ir(seed_of(name, 1), rt_low=3.0, rt_high=1.2, predelay=0.03, length=3.0)
    mix = {'clock': (0.0, 0.12, (('hp', 300, 2), ('lp', 8000, 2))), 'pulse': (-7.0, 0.18, MUTED_EQ),
           'celesta': (-4.0, 0.38, CEL_EQ), 'drone': (-4.5, 0.28, C3A.DRONE_EQ), 'pedal': (-10.0, 0.22, BRASS_EQ),
           'hi': (-18.0, 0.45, STR_HI_EQ), 'bayan': (-4.0, 0.22, REED_EQ), 'piano': (-1.0, 0.3, C3A.FELT_EQ),
           'last': (-6.0, 0.35, C3A.FELT_EQ)}
    out = T.mixdown(mix, ir, target_rms=-21.0, master_lp=9000.0, rms_from=(0.0, CLOCK_STOP))
    # after the tick stops, everything fades out by 22.6 s: k5's black has silence
    t = np.arange(out.shape[0]) / SR
    g = np.clip((22.6 - t) / (22.6 - CLOCK_STOP - 0.4), 0.0, 1.0) ** 1.6
    g[t < CLOCK_STOP + 0.4] = 1.0
    out = out * g[:, None]
    _ = rng
    return out[:secs(CLOCK_LEN)], None


# =============================================================================== one-shots
def c4p2_halves_snap():
    """The German half slid home against the Russian one on the sand house's table: paper on paper, the card's edge
    stopping against the other, the palm pressing the joined card flat (the teeth follow: c4p2_tooth)."""
    rng = R('c4p2_halves_snap')
    y = np.zeros(secs(0.9))
    slide = noise_burst(0.3, rng, 1200.0, 9000.0, 1e6, attack=0.0)
    n = len(slide)
    t = np.arange(n) / SR
    slide *= smoothstep(t / 0.06) * np.clip((0.3 - t) / 0.08, 0.0, 1.0) * (0.8 + 0.2 * ctrl_noise(n, 30.0, rng))
    place(y, 0.3 * norm_peak(slide), 0, circular=False)
    edge = impact(rng, random_modes(rng, 1800.0, 6000.0, 4, 0.008, 0.03), 0.06, hard=0.7, noise_amt=0.4)
    place(y, 0.45 * edge, secs(0.27), circular=False)
    press = wood_knock(rng, 150.0, 0.35, 0.15)
    place(y, 0.5 * norm_peak(press), secs(0.34), circular=False)
    room = make_ir(length=0.6, rt_low=0.4, rt_high=0.2, predelay=0.004, er_taps=6, er_span=0.015, er_gain=0.3,
                   seed=seed_of('c4p2_halves_snap', 1), lowcut=80.0, highcut=7000.0, build=0.004)
    st = far(y, room, wet=0.25, dry=1.0, pan=0.0)
    return one_shot(st[:secs(1.2)], -7.0, fout=0.15), None


def c4p2_tooth():
    """One tooth of the German half seating in its notch: a tiny crisp click of stiff card, a papery body (three
    variants; the success reveals five of them CLICK_STEP = 0.14 s apart)."""
    outs = []
    for v in range(3):
        rng = R('c4p2_tooth', v)
        y = np.zeros(secs(0.3))
        ck = impact(rng, random_modes(rng, 2400.0, 7600.0, 4, 0.006, 0.025), 0.06, hard=0.9, noise_amt=0.45)
        place(y, ck, 0, circular=False)
        body = noise_burst(0.05, rng, 500.0, 3500.0, 0.025, attack=0.001)
        place(y, 0.35 * norm_peak(body), secs(0.002), circular=False)
        st = pan2(y, 0.0)
        outs.append((f'c4p2_tooth_{v + 1}', one_shot(st, -10.0 - 1.0 * v, fout=0.08), None))
    return outs


def c4p2_stamp_close():
    """The stamp closes into a circle: a soft press of the rubber, then two brass tones a quarter-tone apart that
    beat -- slower and slower -- and meet in one, ringing out (one card, two halves)."""
    rng = R('c4p2_stamp_close')
    dur = 3.2
    n = secs(dur)
    t = np.arange(n) / SR
    press = noise_burst(0.08, rng, 150.0, 2500.0, 0.05, attack=0.002)
    press = norm_peak(press) * 0.5
    thump = modal([(110.0, 1.0, 0.12), (230.0, 0.4, 0.08)], 0.3, seed=int(rng.integers(1 << 30)), attack=0.003)
    f0 = float(midi_hz(74))
    meet = smoothstep(np.clip((t - 0.15) / 1.3, 0.0, 1.0))
    f_b = f0 * (1.0 + 0.029 * (1.0 - meet))                           # a quarter-tone above, gliding down to f0
    env = smoothstep(np.clip((t - 0.12) / 0.03, 0.0, 1.0)) * np.exp(-np.maximum(t - 0.15, 0.0) / 1.1)
    partials = [(1.0, 1.0), (2.76, 0.35), (5.4, 0.12), (8.9, 0.05)]       # a struck brass ring
    y = np.zeros(n)
    for r, a in partials:
        y += a * np.sin(TAU * f0 * r * t) * env ** (1.0 + 0.4 * r)
        y += a * np.sin(TAU * np.cumsum(f_b * r) / SR + 0.7) * env ** (1.0 + 0.4 * r)
    y = 0.22 * y / max(float(np.max(np.abs(y))), 1e-9)
    place(y, press, secs(0.1), circular=False)
    place(y, 0.6 * norm_peak(thump), secs(0.1), circular=False)
    room = make_ir(length=1.6, rt_low=1.0, rt_high=0.5, predelay=0.01, er_taps=6, er_span=0.02, er_gain=0.25,
                   seed=seed_of('c4p2_stamp_close', 1), lowcut=80.0, highcut=8000.0, build=0.008)
    st = far(y, room, wet=0.35, dry=1.0, pan=0.0)
    return one_shot(st[:secs(dur + 0.6)], -8.0, fout=0.5), None


def _stairs(name: str, up: bool):
    """Three careful steps on the old wooden stairs at night (a child and a man trying not to be heard): soft
    soles, the treads answering, now and then a creak; up = slower and heavier, down = quicker, heel first."""
    outs = []
    room = ir_stair(seed_of(name, 1))
    for v in range(3):
        rng = R(name, v)
        y = np.zeros(secs(2.2))
        t = 0.02
        interval = rng.uniform(0.42, 0.5) if up else rng.uniform(0.32, 0.38)
        creak_at = int(rng.integers(0, 3))
        for k in range(3):
            st = footstep(rng, 'wood', weight=(0.75 if up else 0.6) * rng.uniform(0.85, 1.0), creak=(k == creak_at))
            st = st.mean(axis=1) if st.ndim == 2 else st
            place(y, norm_peak(st) * (0.8 + 0.2 * (k == 1)), secs(t), circular=False)
            # the tread's hollow answer under the step
            tr_ = modal([(rng.uniform(95, 125), 1.0, 0.12), (rng.uniform(210, 260), 0.4, 0.07)], 0.3,
                        seed=int(rng.integers(1 << 30)), attack=0.004)
            place(y, 0.15 * norm_peak(tr_), secs(t + 0.01), circular=False)
            # the sole scuffing the worn edge of the tread
            sc = noise_burst(0.06, rng, 1200.0, 6000.0, 0.035, attack=0.004)
            place(y, 0.22 * norm_peak(sc), secs(t + (0.0 if up else 0.02)), circular=False)
            t += interval * rng.uniform(0.92, 1.08)
        y = eq(y, ('lp', 5500.0, 2), ('hp', 60.0, 2), circular=False)
        st2 = far(y, room, wet=0.35, dry=1.0, pan=0.0)
        outs.append((f'{name}_{v + 1}', one_shot(st2[:secs(2.4)], -11.0, fout=0.3), None))
    return outs


def c4p2_steps():
    return _stairs('c4p2_steps', True)


def c4p2_steps_down():
    return _stairs('c4p2_steps_down', False)


def c4p2_attic_door():
    """The drying loft's plank door: the thumb latch lifted, a long hinge squeal (stopped halfway, carefully), the
    door against a beam; inside the cold loft a pigeon flaps away in the dark."""
    rng = R('c4p2_attic_door')
    y = np.zeros(secs(3.4))
    latch = impact(rng, random_modes(rng, 1200.0, 6000.0, 6, 0.02, 0.08), 0.25, hard=0.8, noise_amt=0.25)
    place(y, 0.6 * latch, 0, circular=False)
    spring = impact(rng, random_modes(rng, 2200.0, 5200.0, 3, 0.04, 0.12), 0.2, hard=0.7, noise_amt=0.1)
    place(y, 0.25 * spring, secs(0.09), circular=False)
    sq = creak_train(rng, 1.1, 34.0, 12.0, [(rng.uniform(640, 720), 0.06, 1.0), (rng.uniform(1300, 1450), 0.05, 0.6),
                                            (rng.uniform(2100, 2300), 0.04, 0.3)])
    sq = sq * bump(len(sq), 0.15, 0.4, peak_at=0.35)
    place(y, 0.55 * norm_peak(sq), secs(0.25), circular=False)
    sq2 = creak_train(rng, 0.5, 18.0, 8.0, [(rng.uniform(600, 680), 0.06, 1.0), (rng.uniform(1250, 1400), 0.05, 0.5)])
    place(y, 0.35 * norm_peak(sq2), secs(1.6), circular=False)
    bump_ = wood_knock(rng, 110.0, 0.5, 0.3)
    place(y, 0.4 * norm_peak(bump_), secs(2.15), circular=False)
    draft = noise_burst(1.6, rng, 200.0, 1800.0, 1e6, attack=0.0)
    tt = np.arange(len(draft)) / SR
    draft *= smoothstep(tt / 0.4) * np.clip((1.6 - tt) / 0.6, 0.0, 1.0)
    place(y, 0.12 * norm_peak(draft), secs(0.5), circular=False)
    wing = C3A.wing_flaps(rng, 7, rate=(7.0, 9.0), claps=2, fall=0.8)
    place(y, 0.35 * norm_peak(eq(wing, ('lp', 4000.0, 2), circular=False)), secs(1.9), circular=False)
    st = far(y, ir_attic(seed_of('c4p2_attic_door', 1)), wet=0.45, dry=1.0, pan=0.0)
    return one_shot(st[:secs(4.0)], -7.0, fout=0.5), None


def c4p2_spyhole():
    """Frau Pohl's spy-hole: behind her door the little brass cover is pushed aside on its pivot (a thin scrape and
    a click), a floorboard under her slipper."""
    rng = R('c4p2_spyhole')
    y = np.zeros(secs(1.3))
    sc = noise_burst(0.14, rng, 2500.0, 9000.0, 1e6, attack=0.0)
    tt = np.arange(len(sc)) / SR
    sc *= smoothstep(tt / 0.02) * np.clip((0.14 - tt) / 0.04, 0.0, 1.0)
    ring = modal([(rng.uniform(4300, 4700), 1.0, 0.05), (rng.uniform(6800, 7300), 0.5, 0.03)], 0.14,
                 seed=int(rng.integers(1 << 30)))
    place(y, 0.35 * norm_peak(sc) + 0.2 * norm_peak(ring), secs(0.05), circular=False)
    ck = impact(rng, random_modes(rng, 2500.0, 8000.0, 4, 0.01, 0.04), 0.1, hard=0.9, noise_amt=0.3)
    place(y, 0.55 * ck, secs(0.2), circular=False)
    board = creak_train(rng, 0.25, 30.0, 18.0, [(rng.uniform(380, 440), 0.06, 1.0), (rng.uniform(900, 1000), 0.05, 0.5)])
    place(y, 0.12 * norm_peak(board), secs(0.55), circular=False)
    y = eq(y, ('lp', 6000.0, 2), circular=False)          # through the door
    room = ir_stair(seed_of('c4p2_spyhole', 1))
    st = far(y, room, wet=0.3, dry=1.0, pan=0.0)
    return one_shot(st[:secs(1.5)], -9.0, fout=0.2), None


def c4p2_door():
    """Pietsch's cellar door: the bolt drawn back (iron on iron, a rattle), the heavy board door dragged open over
    the stone sill, the cellar answering hollow."""
    rng = R('c4p2_door')
    y = np.zeros(secs(3.6))
    bolt = noise_burst(0.32, rng, 900.0, 7000.0, 1e6, attack=0.0)
    tt = np.arange(len(bolt)) / SR
    bolt *= smoothstep(tt / 0.03) * np.clip((0.32 - tt) / 0.06, 0.0, 1.0)
    bolt = eq(bolt, ('bell', 2600.0, 5.0, 1.0), circular=False)
    place(y, 0.4 * norm_peak(bolt), 0, circular=False)
    for k, tt0 in enumerate((0.02, 0.17, 0.3)):
        ck = impact(rng, random_modes(rng, 700.0, 4200.0, 6, 0.03, 0.15), 0.25, hard=0.75, noise_amt=0.25)
        place(y, (0.35 + 0.25 * (k == 2)) * ck, secs(tt0), circular=False)
    groan = creak_train(rng, 1.4, 22.0, 9.0, [(rng.uniform(180, 220), 0.06, 1.0), (rng.uniform(420, 480), 0.05, 0.6),
                                              (rng.uniform(900, 980), 0.04, 0.3)])
    place(y, 0.5 * norm_peak(groan * bump(len(groan), 0.2, 0.6, peak_at=0.4)), secs(0.55), circular=False)
    drag = noise_burst(1.2, rng, 150.0, 2500.0, 1e6, attack=0.0)
    td = np.arange(len(drag)) / SR
    drag *= smoothstep(td / 0.15) * np.clip((1.2 - td) / 0.3, 0.0, 1.0) * (0.7 + 0.3 * ctrl_noise(len(drag), 18.0, rng))
    place(y, 0.3 * norm_peak(drag), secs(0.6), circular=False)
    stop = wood_knock(rng, 85.0, 0.6, 0.35)
    place(y, 0.45 * norm_peak(stop), secs(1.95), circular=False)
    st = far(y, C4A.ir_cellar(seed_of('c4p2_door', 1)), wet=0.55, dry=1.0, pan=0.0)
    return one_shot(st[:secs(3.8)], -6.0, fout=0.5), None


def c4p2_knock():
    """No way there: a knuckle against the wall of the stairwell, softly (it is 22.40 and the house listens)."""
    rng = R('c4p2_knock')
    k = wood_knock(rng, 130.0, 0.45, 0.2)
    k = eq(k, ('lp', 2500.0, 2), circular=False)
    room = ir_stair(seed_of('c4p2_knock', 1))
    st = far(norm_peak(k), room, wet=0.3, dry=1.0, pan=0.0)
    return one_shot(st[:secs(0.8)], -10.0, fout=0.2), None


def c4p2_shutter():
    """Ekdahl's rangefinder: the cloth focal-plane shutter (two curtains, a crisp double tick), then the film advanced
    with the lever (a short ratchet) -- done within the 0.6 s between his two photographs."""
    rng = R('c4p2_shutter')
    y = np.zeros(secs(0.75))
    for k, (tt, g) in enumerate(((0.0, 1.0), (0.012, 0.7))):
        ck = impact(rng, random_modes(rng, 1800.0, 7000.0, 5, 0.008, 0.03), 0.08, hard=0.9, noise_amt=0.4)
        place(y, g * ck, secs(tt), circular=False)
    body = modal([(rng.uniform(420, 480), 1.0, 0.03), (rng.uniform(1100, 1250), 0.5, 0.02)], 0.08,
                 seed=int(rng.integers(1 << 30)), attack=0.001)
    place(y, 0.3 * norm_peak(body), 0, circular=False)
    t0 = 0.2
    for k in range(9):                       # the advance lever's ratchet
        r = impact(rng, random_modes(rng, 2500.0, 6500.0, 3, 0.004, 0.012), 0.03, hard=0.8, noise_amt=0.5)
        place(y, 0.22 * r * (1.0 - 0.04 * k), secs(t0 + 0.026 * k), circular=False)
    place(y, 0.3 * impact(rng, random_modes(rng, 1500.0, 5000.0, 4, 0.01, 0.04), 0.06, hard=0.7, noise_amt=0.3),
          secs(t0 + 0.26), circular=False)
    st = far(y, make_ir(length=0.8, rt_low=0.6, rt_high=0.3, predelay=0.005, er_taps=6, er_span=0.02, er_gain=0.25,
                        seed=seed_of('c4p2_shutter', 1), lowcut=80.0, highcut=8000.0, build=0.005), wet=0.25, dry=1.0,
             pan=0.15)
    return one_shot(st[:secs(0.9)], -9.0, fout=0.12), None


def c4p2_pencil():
    """Konrad's red pencil ringing the workshop on the plan: the soft lead dragged round once on paper over the
    drawing board -- the stroke's grain rises and falls with the curve, a little tap where it closes."""
    rng = R('c4p2_pencil')
    dur = 0.75
    n = secs(dur)
    t = np.arange(n) / SR
    g = noise_burst(dur, rng, 1500.0, 9000.0, 1e6, attack=0.0)
    g = eq(g, ('bell', 4200.0, 4.0, 1.0), circular=False)
    speed = 0.55 + 0.45 * np.abs(np.sin(TAU * t / 0.62))                 # round the curve: faster on the sides
    env = smoothstep(t / 0.04) * np.clip((0.66 - t) / 0.06, 0.0, 1.0) * speed
    grain = 1.0 + 0.6 * np.clip(ctrl_noise(n, 60.0, rng), 0.0, None)
    y = norm_peak(g) * env * grain * 0.5
    tap = impact(rng, random_modes(rng, 900.0, 3000.0, 4, 0.01, 0.04), 0.06, hard=0.5, noise_amt=0.3)
    place(y, 0.25 * tap, secs(0.64), circular=False)
    st = pan2(eq(y, ('hp', 900.0, 2), circular=False), 0.1)
    return one_shot(st, -12.0, fout=0.1), None


# =============================================================================== registry
BUILDERS = {
    'amb_karsk_depot': ('amb', amb_karsk_depot),
    'amb_karsk_platform': ('amb', amb_karsk_platform),
    'amb_berlin_station': ('amb', amb_berlin_station),
    'amb_berlin_courtyard': ('amb', amb_berlin_courtyard),
    'mus_c4p2_karsk': ('music', mus_c4p2_karsk),
    'mus_c4p2_berlin': ('music', mus_c4p2_berlin),
    'mus_c4p2_clock': ('music', mus_c4p2_clock),
    'c4p2_halves_snap': ('sfx', c4p2_halves_snap),
    'c4p2_tooth': ('sfx', c4p2_tooth),
    'c4p2_stamp_close': ('sfx', c4p2_stamp_close),
    'c4p2_shutter': ('sfx', c4p2_shutter),
    'c4p2_steps': ('sfx', c4p2_steps),
    'c4p2_steps_down': ('sfx', c4p2_steps_down),
    'c4p2_attic_door': ('sfx', c4p2_attic_door),
    'c4p2_spyhole': ('sfx', c4p2_spyhole),
    'c4p2_door': ('sfx', c4p2_door),
    'c4p2_pencil': ('sfx', c4p2_pencil),
    'c4p2_knock': ('sfx', c4p2_knock),
}
# where each sound is (or should be) wired -- the --list output and documentation/asset_manifest_parts/c4p2_cast_audio.md
WIRING = {
    'amb_karsk_depot': 'L_C4P2_Karsk.tscn ambience; c4p2.json switches L_C4P2_KarskA "ambience"; LS_C4P2_Depot p1',
    'amb_karsk_platform': 'c4p2.json switches L_C4P2_KarskB "ambience"; LS_C4P2_Book b4',
    'amb_berlin_station': 'L_C4P2_Berlin.tscn ambience; c4p2.json switches L_C4P2_BerlinA "ambience"; LS_C4P2_Steam m4',
    'amb_berlin_courtyard': 'c4p2.json switches L_C4P2_BerlinB "ambience"; LS_C4P2_Express x4',
    'mus_c4p2_karsk': 'L_C4P2_Karsk.tscn music; c4p2.json switches KarskA / KarskB "music"; LS_C4P2_Depot p2',
    'mus_c4p2_berlin': 'L_C4P2_Berlin.tscn music; c4p2.json switches BerlinA / BerlinB "music"; LS_C4P2_Steam m4',
    'mus_c4p2_clock': 'LS_C4P2_Clock: {"t": 0.0, "music": "mus_c4p2_clock"} from the first frame (one-shot cue)',
    'c4p2_halves_snap': 'JoinPuzzle: the solving moment (before the teeth) -- integration patch',
    'c4p2_tooth': 'JoinPuzzle _reveal_click: one tooth per notch (variants _1.._3) -- integration patch',
    'c4p2_stamp_close': 'JoinPuzzle _reveal_ring: Kit.ui_sound_first(["c4p2_stamp_close", ...]) (called already)',
    'c4p2_shutter': 'JoinPuzzle _photo: Kit.ui_sound_first(["c4p2_shutter", ...]) (called already)',
    'c4p2_steps': 'HousePuzzle _walk: Kit.ui_sound_first(["c4p2_steps", ...]) (called already); UP moves',
    'c4p2_steps_down': 'HousePuzzle: DOWN moves (variants _1.._3) -- integration patch',
    'c4p2_attic_door': 'HousePuzzle: a move into / along the drying lofts (vd / sd / hd) -- integration patch',
    'c4p2_spyhole': 'HousePuzzle _on_walk_finished: the walk stops at s2 (Frau Pohl) -- integration patch',
    'c4p2_door': 'HousePuzzle _reveal_workshop: Kit.ui_sound_first(["c4p2_door", ...]) (called already)',
    'c4p2_pencil': 'HousePuzzle _reveal_circle: Kit.ui_sound_first(["c4p2_pencil", ...]) (called already)',
    'c4p2_knock': 'HousePuzzle _no_way: Kit.ui_sound_first(["ui_knock", "c4p2_knock", ...]) (called already)',
}
# loudness envelope the checks enforce: (min RMS, max RMS, max peak) in dBFS (the round-8 windows)
TARGETS = P2A.TARGETS


def outputs_of(name: str):
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
    return P2A.check_rows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--only', default='', help='comma separated builder names: ' + ', '.join(BUILDERS))
    ap.add_argument('--jobs', type=int, default=min(6, os.cpu_count() or 1))
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--no-analysis', action='store_true')
    ap.add_argument('--no-spectro', action='store_true')
    args = ap.parse_args()
    if args.list:
        for n, (k, _) in BUILDERS.items():
            print(f'{k:6s} {n:22s} {WIRING.get(n, "")}')
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
        with open(os.path.join(analyze.PREVIEW, 'c4p2_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=1, default=str)
    for f in fails:
        print('  FAIL', f)
    print('OK: c4p2 audio checks pass' if not fails else f'FAIL: {len(fails)} c4p2 audio checks')
    print(f'total {time.time() - t0:.1f}s')
    if fails:
        sys.exit(1)


if __name__ == '__main__':
    main()
