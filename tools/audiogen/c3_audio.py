"""c3_audio.py -- Chapter 3 "Der eiserne Frieden": the Veltrava soundscape (synthesised, original).

    python3 -P tools/audiogen/c3_audio.py                        # build all three + .import + analysis
    python3 -P tools/audiogen/c3_audio.py --only mus_veltrava    # subset (comma separated)
    python3 -P tools/audiogen/c3_audio.py --preview DIR          # spectrogram / seam PNGs into DIR
    python3 -P tools/audiogen/c3_audio.py --compare              # also measure the existing loops
    python3 -P tools/audiogen/c3_audio.py --godot                # also run `godot --headless --import`

amb_veltrava_station  60 s stereo loop.  A 19th-century station at a cold dawn under iron-and-glass
                      canopies: air of the train shed, wind under the canopy, the city beyond, a low
                      crowd murmur of several "languages" (formant babble with four prosody profiles --
                      random vowel targets, no words, unintelligible by construction), the standing
                      Soviet locomotive off-screen left (steam hiss, firebox roar, the slow breathing of
                      its air pump, one steam release), far wagon-coupling clanks, pigeons, footsteps on
                      stone, a porter's luggage cart, a tram bell outside the exit arch, a muffled
                      two-tone station chime through the PA horns (never followed by a voice), faint
                      creaks of the iron canopy.  Target -24 dBFS RMS like the other exteriors.
amb_veltrava_palais   60 s stereo loop.  Jugendstil conference palace (former Kurhaus), morning: large
                      room tone with a long soft reverb, the delegations murmuring behind the double
                      doors of the Grosser Saal (one door opens for six seconds and the murmur comes
                      through brighter), a typewriter burst with margin bell and carriage return from
                      the protocol office, a second short burst, a hand-cranked mimeograph far away,
                      the foyer clock, radiator ticks and a gurgle, a faint glass tinkle of the
                      chandelier in the draught.  No music.  Target -25 dBFS RMS like the archive.
mus_veltrava          90 s stereo loop (24 bars of 4/4, quarter = 64).  Exploration cue for the neutral
                      city, written to sit UNDER dialogue: mostly 50-500 Hz, sparse, no busy melody.
                      An open-fifth bowed drone on A (no third: neutral), slow string colours above it,
                      a muted-piano "clockwork" pulse on E3 (with hesitations, and a semitone push to F3
                      at the point of most tension) against a celesta gear turning every three beats,
                      and the two-language motif V: the felt piano states it (E3 C4 B3 A3 . E3) and a
                      solo viola "interprets" it two beats behind -- almost the same, but B becomes Bb
                      (the 0-accidental collection of Veltrava against the 1-flat world shared by the
                      K and B motifs; the A/Bb rub on which LS_X1_Final ended becomes the undercurrent
                      here).  Second statement: the viola leads and the piano leaves the changed note
                      out; third: the piano stops on B and the viola completes the phrase in Bb.

Everything reuses dsp / instruments / foley / ambience / music by import -- those modules are not
modified, and build_all.py's registry does not know this module: run this file directly.  Seeds derive
from zlib.crc32(name) (the dither seed exactly as in build_all), so every run is bit-identical.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

from dsp import (SR, TAU, secs, eq, fftconv, place, pan2, width, smooth_periodic, shaped_noise,  # noqa: E402
                 mag_bp, mag_tilt, rms, a2db, db2a, smoothstep, stft_filter, make_ir, soft_clip, fade,
                 midi_hz, write_wav, read_wav)
from instruments import (modal, impact, random_modes, noise_burst, ctrl_noise, make_table,  # noqa: E402
                         wt_read)
from foley import (wind, gust_curve, footstep, creak_train, metal_clank, shunting_chain, tram_bell,  # noqa: E402
                   tram_pass, door_open, wood_knock, norm_peak, bump, ir_street, ir_outdoor_far,
                   paper_rustle, VOWELS)
from ambience import Mix, N  # noqa: E402  (N = 60 s = 2 646 000 frames, a multiple of the STFT hop)
from music import Track, hall_ir, STR_EQ, STR_HI_EQ, BRASS_EQ, MUTED_EQ, CEL_EQ  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AUDIO = os.path.join(ROOT, 'assets', 'audio')
KIND = {'amb_veltrava_station': 'amb', 'amb_veltrava_palais': 'amb', 'mus_veltrava': 'music'}


def seed_of(name: str, k: int = 0) -> int:
    """Deterministic seed from the asset name (zlib.crc32, as build_all does for the dither)."""
    return (zlib.crc32(name.encode('utf-8')) + 7919 * k) & 0x7FFFFFFF


# =============================================================================== shared helpers
def far(x: np.ndarray, ir: np.ndarray, lp: float | None = None, hp: float | None = None, wet: float = 1.0,
        dry: float = 0.4, pan: float = 0.0) -> np.ndarray:
    """Dry event (mono or stereo) -> distant stereo event through a room / outdoor IR, tail kept."""
    bands = []
    if hp:
        bands.append(('hp', hp, 2))
    if lp:
        bands.append(('lp', lp, 2))
    y = eq(x, *bands, circular=False) if bands else np.asarray(x, dtype=float)
    st = pan2(y, pan) if y.ndim == 1 else y
    w = fftconv(st, ir, circular=False, full=True)
    out = wet * w
    out[:st.shape[0]] += dry * st
    return out


def mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) if x.ndim == 2 else x


def overlay(*parts) -> np.ndarray:
    """Sum stereo one-shots of different lengths (all start at 0)."""
    out = np.zeros((max(len(p) for p in parts), 2))
    for p in parts:
        out[:len(p)] += p
    return out


# 'Languages' = prosody profiles only: syllable length, stress, fricative onsets, declination, how
# often a phrase ends rising, accent size and vowel colour.  The vowel sequence is random, so no
# profile can ever form a word -- unintelligible by construction, and none imitates a real language.
PROSODY = {
    'even':    dict(syl=(0.10, 0.20), stress=0.20, fric=0.45, vowels=(0, 1, 2, 5, 6, 7), decl=0.14, rise=0.10,
                    acc=0.06, link=0.35),
    'lilt':    dict(syl=(0.12, 0.27), stress=0.35, fric=0.40, vowels=(0, 3, 4, 5, 7), decl=0.22, rise=0.30,
                    acc=0.12, link=0.25),
    'clipped': dict(syl=(0.09, 0.22), stress=0.30, fric=0.70, vowels=(1, 2, 4, 5, 6), decl=0.18, rise=0.05,
                    acc=0.09, link=0.20),
    'slow':    dict(syl=(0.14, 0.32), stress=0.28, fric=0.35, vowels=(0, 3, 4, 5, 6, 7), decl=0.20, rise=0.12,
                    acc=0.08, link=0.40),
}


def voice(rng: np.random.Generator, dur: float, f0: float, prof: str, pause=(0.6, 2.2), phrase=(1.2, 3.4)) -> np.ndarray:
    """One talker of a distant crowd (generalises foley.babble with a prosody profile): random vowel
    formant targets on a glottal pulse train, fricative noise at syllable onsets, phrase declination.
    No phoneme sequence, no words, no language.  Mono, dry, len == secs(dur)."""
    P = PROSODY[prof]
    n = secs(dur)
    n += (-n) % 441
    cr = 200.0
    ctrl = int(n / SR * cr) + 2
    tt = np.arange(ctrl) / cr
    amp = np.zeros(ctrl)
    nz = np.zeros(ctrl)
    pitch = np.ones(ctrl)
    F = np.zeros((ctrl, 3))
    F[:] = VOWELS[5]
    fs = 1.0 + 0.17 * float(np.clip((f0 - 120.0) / 90.0, 0.0, 1.0))      # higher voices: higher formants
    vow = [VOWELS[i] for i in P['vowels']]
    t = rng.uniform(0.15, 1.2)
    while t < dur - 0.6:
        L = rng.uniform(*phrase)
        end = min(dur - 0.35, t + L)
        s = t
        question = rng.random() < P['rise']
        while s < end:
            d = rng.uniform(*P['syl'])
            v = vow[int(rng.integers(len(vow)))]
            stress = rng.random() < P['stress']
            i0, i1 = int(s * cr), int(min(end, s + d) * cr)
            if i1 <= i0 + 2:
                break
            seg = np.arange(i0, i1)
            u = (seg - i0) / max(1, i1 - i0)
            linked = rng.random() < P['link']
            a = np.sin(np.pi * np.clip(u * 1.1, 0, 1)) ** (0.45 if linked else 0.9)
            amp[seg] = np.maximum(amp[seg], a * (1.0 if stress else 0.72))
            if rng.random() < P['fric']:
                nz[seg[u < 0.22]] = rng.uniform(0.3, 0.8)
            decl = 1.0 + P['decl'] * (0.5 - (s - t) / max(L, 1e-3))
            acc = (P['acc'] if stress else 0.015) * np.sin(np.pi * u)
            fin = (0.13 if question else -0.10) * smoothstep((u - 0.3) / 0.7) if s + d >= end else 0.0
            pitch[seg] = decl * (1.0 + acc + fin)
            F[seg] = np.array(v, dtype=float) * fs * rng.uniform(0.95, 1.05)
            s += d
        t = end + rng.uniform(*pause)

    def sm(x, w):
        k = np.ones(w) / w
        if x.ndim == 1:
            return np.convolve(np.pad(x, (w, w), mode='edge'), k, mode='same')[w:-w]
        return np.stack([sm(x[:, j], w) for j in range(x.shape[1])], axis=1)
    amp, nz, pitch, F = sm(amp, 5), sm(nz, 3), sm(pitch, 16), sm(F, 10)
    ts = np.arange(n) / SR
    A = np.interp(ts, tt, amp)
    NZ = np.interp(ts, tt, nz)
    f0t = f0 * np.interp(ts, tt, pitch) * (1.0 + 0.01 * ctrl_noise(n, 5.0, rng))
    K = int(7000 / (f0 * 1.3))
    k = np.arange(1, K + 1)
    tab = make_table(k ** -1.0 / (1.0 + (k * f0 / 2500.0) ** 2))
    src = wt_read(tab, np.cumsum(f0t) / SR) * A + rng.standard_normal(n) * NZ * 0.35
    hop, nfft = 441, 1764
    fr = np.minimum(((np.arange(n // hop) * hop + nfft // 2) / (SR / cr)).astype(int), ctrl - 1)
    Ff = F[fr]

    def G(tc, f):
        lf = f[None, :]
        g = np.zeros((len(tc), len(f)))
        for j, bw in enumerate((90.0, 120.0, 170.0)):
            fc = Ff[:len(tc), j][:, None]
            g += (1.0 / (j + 1)) / (1.0 + ((lf - fc) / (bw / 2)) ** 2)
        return g + 0.02
    return stft_filter(src, G, nfft=nfft, hop=hop)[:secs(dur)]


def talkers(rng: np.random.Generator, n: int, specs, hp: float = 140.0) -> np.ndarray:
    """Sum of distant talkers on a circular timeline.  specs: [(f0, profile, gain_db, pan, lp_hz,
    pause, phrase)].  Each voice is a whole loop, rolled to a random offset so the silent heads and
    tails of the phrases never line up at the seam."""
    buf = np.zeros((n, 2))
    for (f0, prof, g_db, pan, lp, pause, phrase) in specs:
        v = voice(rng, n / SR, f0, prof, pause=pause, phrase=phrase)
        v = eq(v, ('hp', hp, 2), ('lp', lp, 2), circular=True)
        v = np.roll(v, int(rng.integers(n)))
        buf += pan2(v * (db2a(g_db) / max(rms(v), 1e-12)), pan)
    return buf


# =============================================================================== rooms
def ir_station(seed: int) -> np.ndarray:
    """Iron-and-glass train shed: wide and decorrelated, glassy early field, discrete slaps off the
    station building and the far canopy end."""
    return make_ir(length=4.6, rt_low=2.9, rt_high=1.15, predelay=0.022, er_taps=12, er_span=0.08,
                   er_gain=0.32, seed=seed, lowcut=55.0, highcut=7500.0, build=0.018,
                   slap=[(0.115, 0.30, 4200), (0.26, 0.26, 3200), (0.43, 0.18, 2500), (0.71, 0.11, 1900),
                         (1.08, 0.07, 1500)])


def ir_palais(seed: int) -> np.ndarray:
    """Foyer and staircase of the palais: long, soft (dark) tail, slow build."""
    return make_ir(length=5.5, rt_low=3.7, rt_high=1.6, predelay=0.034, er_taps=14, er_span=0.095,
                   er_gain=0.26, seed=seed, lowcut=50.0, highcut=6200.0, build=0.03)


def ir_saal(seed: int) -> np.ndarray:
    """The Grosser Saal behind the double doors."""
    return make_ir(length=3.6, rt_low=2.4, rt_high=1.1, predelay=0.02, er_taps=12, er_span=0.06, er_gain=0.3,
                   seed=seed, lowcut=70.0, highcut=6000.0, build=0.02)


def ir_office(seed: int) -> np.ndarray:
    """Protocol office: small, panelled, shelves of treaty volumes."""
    return make_ir(length=1.0, rt_low=0.55, rt_high=0.32, predelay=0.004, er_taps=14, er_span=0.03,
                   er_gain=0.45, seed=seed, lowcut=100.0, highcut=8000.0, build=0.004)


# =============================================================================== station sources
def loco_breath(rng: np.random.Generator, strength: float = 1.0) -> np.ndarray:
    """One slow 'breath' of the standing locomotive's air pump: a soft double stroke (two low thuds,
    a valve click) with the exhaust exhaling through the pipe.  Mono, dry, ~2.9 s."""
    n = secs(2.9)
    y = np.zeros(n)
    for k, (t0, a) in enumerate([(0.0, 1.0), (rng.uniform(0.58, 0.72), 0.72)]):
        L = 1.9
        ex = noise_burst(L, rng, 200.0, 3600.0, 1e6, attack=0.0)
        ex = eq(ex, ('bell', rng.uniform(560.0, 720.0), 7.0, 0.9), ('bell', rng.uniform(1300.0, 1700.0), 3.5, 0.7),
                ('tilt', -2.5, 800.0), circular=False)
        ex = norm_peak(ex) * bump(secs(L), 0.14 + 0.05 * k, 0.40 + 0.1 * k, peak_at=0.16)
        place(y, a * 0.7 * ex, secs(t0), circular=False)
        th = modal([(rng.uniform(52.0, 64.0), 1.0, 0.22), (rng.uniform(118.0, 140.0), 0.45, 0.14),
                    (rng.uniform(300.0, 360.0), 0.2, 0.06)], 0.6, seed=int(rng.integers(1 << 30)), attack=0.006)
        place(y, a * 0.45 * norm_peak(th), secs(t0 + 0.02), circular=False)
        ck = impact(rng, random_modes(rng, 900.0, 4200.0, 6, 0.01, 0.05), 0.12, hard=0.5, noise_amt=0.3)
        place(y, a * 0.08 * ck, secs(t0 + 0.012), circular=False)
    return fade(y * strength, 0.0, 0.25)


def steam_release(rng: np.random.Generator, dur: float = 3.4) -> np.ndarray:
    """Cylinder cocks / blow-down: a big soft hiss with a turbulent flutter.  Mono, dry."""
    n = secs(dur)
    t = np.arange(n) / SR
    z = noise_burst(dur, rng, 900.0, 9000.0, 1e6, attack=0.0)
    z = eq(z, ('bell', 2600.0, 3.0, 1.2), ('tilt', -1.5, 3000.0), circular=False)
    env = smoothstep(t / 0.35) * np.exp(-np.maximum(t - 0.5, 0.0) / 1.1)
    flutter = 1.0 + 0.25 * ctrl_noise(n, 9.0, rng)
    return fade(norm_peak(z) * env * flutter, 0.0, 0.3)


def wing_flaps(rng: np.random.Generator, flaps: int, rate=(7.0, 9.5), claps: int = 2, fall: float = 0.9,
               land: bool = False) -> np.ndarray:
    """A pigeon's wing beats: feathery whoosh per beat (with feather flutter), the first beats of a
    take-off clap.  land=True: beats slow down and swell into a final braking flap.  Mono, dry."""
    r = np.linspace(rate[0], rate[1], flaps)
    if land:
        r = r[::-1]
    gaps = (1.0 / r) * (1.0 + 0.06 * rng.standard_normal(flaps))
    y = np.zeros(secs(float(gaps.sum()) + 0.35))
    t = 0.0
    for k in range(flaps):
        a = (fall ** k) if not land else (0.55 + 0.45 * k / max(1, flaps - 1))
        L = secs(0.1)
        tt = np.arange(L) / SR
        z = noise_burst(0.1, rng, 280.0, 4200.0, 1e6, attack=0.0)
        env = smoothstep(tt / 0.012) * np.exp(-tt / (0.03 if not (land and k == flaps - 1) else 0.06))
        fl = 1.0 + 0.45 * np.sin(TAU * rng.uniform(110.0, 170.0) * tt + rng.uniform(0, TAU))
        place(y, a * 0.8 * norm_peak(z * env * fl), secs(t), circular=False)
        if k < claps and not land:
            c = noise_burst(0.03, rng, 900.0, 7500.0, 0.012, attack=0.0008)
            place(y, a * 0.55 * norm_peak(c), secs(t + 0.004), circular=False)
        t += gaps[k]
    return y


def pigeons(rng: np.random.Generator, birds) -> np.ndarray:
    """birds: [(offset_s, flaps, pan, land)] -> stereo cluster."""
    parts = []
    for (off, fl, pan, land) in birds:
        w = wing_flaps(rng, fl, rate=(rng.uniform(6.5, 7.5), rng.uniform(8.8, 10.0)), claps=0 if land else 2,
                       fall=rng.uniform(0.86, 0.92), land=land)
        parts.append((secs(off), pan2(w, np.linspace(pan, pan + rng.uniform(-0.25, 0.25), len(w)))))
    out = np.zeros((max(s + len(w) for s, w in parts), 2))
    for s, w in parts:
        out[s:s + len(w)] += w
    return out


def walker(rng: np.random.Generator, steps: int, interval: float, p0: float, p1: float, heels: bool = False) -> np.ndarray:
    """Someone crossing the platform: leather soles on stone (foley 'concrete' step), panning p0->p1.
    heels=True: lighter, quicker, sharper clicks."""
    out = np.zeros((secs(steps * interval * 1.1 + 0.8), 2))
    t = 0.0
    for i in range(steps):
        s = footstep(rng, 'concrete', weight=0.9)
        if heels:
            s = eq(s, ('hp', 380.0, 2), ('bell', 3200.0, 4.0, 1.0), circular=False)
        g = (0.88 if i % 2 else 1.0) * rng.uniform(0.85, 1.05)
        place(out, pan2(s * g, p0 + (p1 - p0) * i / max(1, steps - 1)), secs(t), circular=False)
        t += interval * (1.0 + rng.normal(0.0, 0.025))
    return out


def luggage_cart(rng: np.random.Generator, dur: float = 7.2, closest: float = 3.6, p0: float = 0.75,
                 p1: float = -0.45) -> np.ndarray:
    """A porter's cart: iron-rimmed wheels rolling over the slab joints (two axles), a dry axle squeak
    once per wheel turn, luggage rattling on the bed.  Stereo, dry."""
    n = secs(dur)
    t = np.arange(n) / SR
    prox = 1.0 / (1.0 + ((t - closest) / 2.2) ** 2)
    roll = noise_burst(dur, rng, 45.0, 900.0, 1e6, attack=0.0)
    y = 0.30 * norm_peak(roll) * (1.0 + 0.5 * ctrl_noise(n, 40.0, rng)) * prox ** 1.2
    tc = 0.25
    while tc < dur - 0.35:
        for off, g in ((0.0, 1.0), (0.21, 0.8)):
            k = impact(rng, random_modes(rng, 140.0, 2200.0, 7, 0.02, 0.12), 0.25, hard=0.45, noise_amt=0.35)
            place(y, 0.26 * g * k * float(np.interp(tc + off, t, prox)) ** 1.3, secs(tc + off), circular=False)
        tc += rng.uniform(0.55, 0.75)
    tq = 0.6
    while tq < dur - 0.4:
        sq = creak_train(rng, 0.16, rng.uniform(600.0, 800.0), rng.uniform(900.0, 1100.0),
                         [(rng.uniform(1500.0, 1900.0), 0.01, 1.0), (rng.uniform(2900.0, 3400.0), 0.006, 0.4)],
                         jitter=0.2)
        sq = norm_peak(sq) * bump(len(sq), 0.04, 0.05, peak_at=0.06)
        place(y, 0.07 * sq * float(np.interp(tq, t, prox)) ** 1.5, secs(tq), circular=False)
        tq += rng.uniform(1.05, 1.25)
    tr = 0.2
    while tr < dur - 0.2:
        k = impact(rng, random_modes(rng, 250.0, 2600.0, 5, 0.02, 0.08), 0.15, hard=0.4, noise_amt=0.3)
        place(y, 0.06 * rng.uniform(0.4, 1.0) * k * float(np.interp(tr, t, prox)) ** 1.5, secs(tr), circular=False)
        tr += rng.exponential(0.35)
    y = eq(y, ('lp', 5000.0, 2), circular=False)
    return pan2(y, p0 + (p1 - p0) * smoothstep(t / dur))


def chime_bar(rng: np.random.Generator, midi: float, dur: float = 3.4) -> np.ndarray:
    """One struck chime bar of the station gong (tuned fundamental, octave from the resonator, flat
    4th partial, faint high mode) + soft mallet contact."""
    f = float(midi_hz(midi))
    y = modal([(f, 1.0, 2.6), (2.0 * f * 1.003, 0.08, 1.3), (3.93 * f, 0.14, 0.6), (9.2 * f, 0.03, 0.14)], dur,
              seed=int(rng.integers(1 << 30)), attack=0.0015)
    m = noise_burst(0.012, rng, 400.0, 3000.0, 0.004)
    y[:len(m)] += 0.12 * norm_peak(m)
    return fade(y, 0.0, 0.4)


def station_chime(rng: np.random.Generator) -> np.ndarray:
    """Two-tone 'ding-dong' (E5 -> C5) as heard through 1960s horn loudspeakers: band-limited, a
    little cone growl, several horns at different distances.  Stereo, dry (the hall comes later).
    No announcement follows."""
    y = np.zeros(secs(4.2))
    place(y, chime_bar(rng, 76), 0, circular=False)
    place(y, 0.92 * chime_bar(rng, 72), secs(0.64), circular=False)
    y = eq(y, ('hp', 330.0, 3), ('lp', 3300.0, 3), ('bell', 1250.0, 3.0, 1.0), circular=False)
    y = soft_clip(norm_peak(y) * 0.9, 1.4)
    y = eq(y, ('hp', 280.0, 2), ('lp', 2900.0, 2), circular=False)
    out = np.zeros((len(y) + secs(0.3), 2))
    for (dl, pan, g) in [(0.0, -0.4, 1.0), (0.072, 0.35, 0.72), (0.161, 0.85, 0.5), (0.243, -0.85, 0.34)]:
        place(out, pan2(y * g, pan), secs(dl), circular=False)
    return out


def canopy_creak(rng: np.random.Generator, dur: float, r0: float, r1: float) -> np.ndarray:
    """Cold iron of the canopy working in the wind (stick-slip through metallic modes).  Mono, dry."""
    modes = [(rng.uniform(240.0, 330.0), 0.09, 1.0), (rng.uniform(640.0, 820.0), 0.06, 0.6),
             (rng.uniform(1250.0, 1600.0), 0.04, 0.35), (rng.uniform(2300.0, 2800.0), 0.025, 0.2)]
    c = creak_train(rng, dur, r0, r1, modes, jitter=0.3)
    return norm_peak(c) * bump(secs(dur), dur * 0.3, dur * 0.35, peak_at=dur * 0.35)


# =============================================================================== amb_veltrava_station
def amb_veltrava_station():
    name = 'amb_veltrava_station'
    rng = np.random.default_rng(seed_of(name))
    M = Mix()
    hall = ir_station(seed_of(name, 1))
    yard = ir_outdoor_far(seed_of(name, 2))
    square = ir_street(seed_of(name, 3))
    # --- beds -------------------------------------------------------------------------------------
    air = shaped_noise(N, rng, lambda f: mag_tilt(f, -3.0, 150.0) * mag_bp(f, 40.0, 1400.0, 2)
                       + 0.02 * mag_bp(f, 2500.0, 8000.0, 2), ch=2, corr=0.4)
    air *= (1.0 + 0.12 * smooth_periodic(N, 9, rng))[:, None]
    M.bed(air, -4.0)
    gust = gust_curve(N, rng, [(4.0, 0.45, 2.2, 3.0), (17.0, 0.6, 1.8, 2.8), (29.5, 0.35, 2.6, 3.4),
                               (41.0, 0.55, 2.0, 3.0), (52.5, 0.4, 2.4, 3.2)], base=0.28, turb=0.07, turb_rate=0.6)
    w = wind(N, rng, gust, lp_base=260.0, lp_gust=900.0, whistle=0.07, whistle_f=(390.0, 620.0), corr=0.35,
             hp=60.0, tilt=-0.35, pan_sweep=0.3)
    M.bed(w, -3.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 28.0, 220.0, 2), ch=2, corr=0.8)
    city *= (1.0 + 0.3 * smooth_periodic(N, 7, rng))[:, None]
    M.bed(city, -10.0)
    # crowd: twelve distant talkers, four prosody profiles, mostly towards the concourse (right)
    profs = ['even', 'lilt', 'clipped', 'slow']
    specs = []
    for i, f0 in enumerate([96, 104, 110, 117, 124, 132, 141, 182, 196, 208, 221, 236]):
        dist = rng.uniform(0.15, 1.0)
        specs.append((f0 * (1.0 + rng.normal(0.0, 0.02)), profs[(i * 3 + int(rng.integers(4))) % 4],
                      -2.0 - 8.0 * dist, float(np.clip(rng.normal(0.2, 0.45), -0.8, 0.9)), 3300.0 - 2000.0 * dist,
                      (0.5, 2.8), (1.0, 3.6)))
    crowd = talkers(rng, N, specs)
    crowd = 0.4 * crowd + fftconv(crowd, hall, circular=True)
    M.bed(crowd, -5.5)
    # the standing locomotive, off-screen left: steam hiss and firebox roar
    hiss = shaped_noise(N, rng, lambda f: mag_bp(f, 1800.0, 8500.0, 2) * mag_tilt(f, -1.5, 4000.0), ch=1)
    hiss *= (1.0 + 0.18 * smooth_periodic(N, int(N / SR * 7), rng)) * (1.0 + 0.25 * smooth_periodic(N, 10, rng))
    hiss = pan2(hiss, -0.7)
    M.bed(0.6 * hiss + 0.5 * fftconv(hiss, hall, circular=True), -14.0)
    roar = shaped_noise(N, rng, lambda f: mag_bp(f, 35.0, 180.0, 2), ch=1)
    roar *= 1.0 + 0.2 * smooth_periodic(N, 25, rng)
    M.bed(pan2(roar, -0.55), -14.0)
    # --- events (all on the circular timeline) ----------------------------------------------------
    period = 60.0 / 18.0
    for k in range(18):                      # the air pump 'breathing' (about every 3.3 s)
        b = loco_breath(rng, rng.uniform(0.8, 1.0))
        M.event(far(b, hall, lp=4200.0, wet=0.6, dry=0.7, pan=-0.68), 0.7 + k * period + rng.normal(0.0, 0.18),
                -4.5 + rng.uniform(-1.0, 0.5))
    M.event(far(steam_release(rng), hall, lp=7000.0, wet=0.7, dry=0.6, pan=-0.75), 44.8, -7.0)
    # far wagon couplings (out in the yard)
    M.event(far(shunting_chain(rng, 3, 0.55), yard, lp=2400.0, wet=1.0, dry=0.35, pan=-0.35), 6.8, 1.5)
    clank = metal_clank(rng, 'heavy')
    place(clank, 0.3 * metal_clank(rng, 'light'), secs(0.12), circular=False)
    M.event(far(clank, yard, lp=2000.0, wet=1.0, dry=0.3, pan=0.28), 48.2, 0.0)
    # pigeons under the glass roof
    M.event(far(pigeons(rng, [(0.0, 7, -0.25, True)]), hall, lp=6000.0, wet=0.9, dry=0.6), 10.4, -6.0)
    M.event(far(pigeons(rng, [(0.0, 14, 0.1, False), (0.12, 12, 0.35, False), (0.31, 15, -0.15, False),
                              (0.47, 11, 0.5, False)]), hall, lp=6500.0, wet=0.9, dry=0.6), 26.5, -3.5)
    M.event(far(pigeons(rng, [(0.0, 9, 0.6, False)]), hall, lp=6000.0, wet=0.9, dry=0.6), 55.3, -7.0)
    # people crossing the platform (stone)
    M.event(far(walker(rng, 16, 0.56, -0.6, 0.2), hall, lp=4500.0, wet=1.0, dry=0.35), 2.5, 4.0)
    M.event(far(overlay(walker(rng, 17, 0.58, 0.75, -0.05), 0.8 * walker(rng, 17, 0.6, 0.65, -0.15)), hall,
                lp=3500.0, wet=1.0, dry=0.3), 19.0, 1.0)
    M.event(far(walker(rng, 14, 0.43, -0.2, 0.6, heels=True), hall, lp=5000.0, wet=1.0, dry=0.4), 41.5, 1.0)
    M.event(far(walker(rng, 11, 0.64, 0.3, 0.8), hall, lp=3000.0, wet=1.0, dry=0.25), 52.0, 0.5)
    # a porter's luggage cart, right to left
    M.event(far(luggage_cart(rng), hall, lp=5000.0, wet=0.7, dry=0.7), 31.0, -5.0)
    # outside the exit arch: a tram passes the square and rings
    tp = mono(tram_pass(rng, 12.0, 6.0, dist=2.5))
    M.event(far(tp, square, lp=420.0, wet=0.5, dry=0.8, pan=0.72), 34.0, -8.5)
    bell = tram_bell(rng, 2, 698.5)
    M.event(far(bell, square, lp=2200.0, hp=260.0, wet=0.8, dry=0.6, pan=0.78), 39.6, 11.0, mode='peak')
    # the muffled two-tone station chime (no voice announcement)
    M.event(far(station_chime(rng), hall, lp=2600.0, wet=1.3, dry=0.3), 21.5, 1.0)
    # the cold iron canopy working in the wind
    M.event(far(canopy_creak(rng, 1.1, 40.0, 70.0), hall, lp=3500.0, wet=0.9, dry=0.4, pan=0.15), 15.6, -7.0)
    M.event(far(canopy_creak(rng, 0.9, 65.0, 38.0), hall, lp=3200.0, wet=0.9, dry=0.4, pan=-0.3), 50.5, -7.0)
    out = M.master(-24.0, lp=12000.0)
    return out, (0, N)


# =============================================================================== palais sources
def delegations(rng: np.random.Generator, n: int, saal: np.ndarray) -> np.ndarray:
    """The opening session behind the double doors: the speaker at the rostrum microphone (through the
    hall's column loudspeakers) and delegates murmuring at the horseshoe table.  Stereo, narrow."""
    sp_spec = [(108.0, 'slow', 0.0, 0.05, 4200.0, (0.35, 1.1), (2.0, 4.5))]
    sp = talkers(rng, n, sp_spec, hp=160.0)
    sp = eq(sp, ('bell', 1600.0, 3.0, 1.0), circular=True)
    murmur = talkers(rng, n, [(98.0, 'even', -9.0, -0.3, 3000.0, (1.5, 5.0), (0.8, 2.2)),
                              (122.0, 'clipped', -10.0, 0.25, 3000.0, (1.5, 5.0), (0.8, 2.2)),
                              (131.0, 'lilt', -11.0, -0.1, 3000.0, (1.5, 5.0), (0.8, 2.2)),
                              (204.0, 'even', -12.0, 0.35, 3000.0, (1.5, 5.0), (0.8, 2.2)),
                              (115.0, 'slow', -12.0, 0.1, 3000.0, (1.5, 5.0), (0.8, 2.2))], hp=130.0)
    dry = sp + murmur
    out = width(0.5 * dry + fftconv(dry, saal, circular=True), 0.5)
    return out * np.array([0.92, 1.07])                  # the doors sit slightly right of centre


def door_filter(x: np.ndarray, t_open: float, t_close: float, closed_lp: float = 380.0, open_lp: float = 3200.0,
                closed_db: float = -10.0, ramp: float = 0.45) -> np.ndarray:
    """Heavy double door between the foyer and the Saal: closed = steep low-pass with a panel
    resonance and -10 dB; open (t_open..t_close) = almost the full spectrum."""
    def G(tc, f):
        o = smoothstep((tc - t_open) / ramp) * (1.0 - smoothstep((tc - t_close) / ramp))
        fc = closed_lp * (open_lp / closed_lp) ** o
        lf = np.maximum(f[None, :], 1.0)
        H = db2a(closed_db * (1.0 - o))[:, None] / np.sqrt(1.0 + (lf / fc[:, None]) ** 4)
        H = H * (1.0 + (1.0 - o)[:, None] * 0.6 * np.exp(-0.5 * (np.log2(lf / 240.0) / 0.5) ** 2))
        return H
    return stft_filter(x, G, nfft=1764, hop=441)


def door_close(rng: np.random.Generator) -> np.ndarray:
    """Heavy panelled door swinging shut: pushed air, the leaf hitting the frame, latch, rattle."""
    y = np.zeros(secs(1.4))
    air = noise_burst(0.35, rng, 50.0, 400.0, 0.25, attack=0.12)
    place(y, 0.25 * norm_peak(air), 0, circular=False)
    place(y, 1.0 * norm_peak(wood_knock(rng, 78.0, 0.9, hard=0.55)), secs(0.3), circular=False)
    place(y, 0.5 * norm_peak(wood_knock(rng, 150.0, 0.5, hard=0.6)), secs(0.302), circular=False)   # the panel
    latch = impact(rng, random_modes(rng, 1600.0, 6500.0, 8, 0.015, 0.05), 0.15, hard=0.8, noise_amt=0.5,
                   noise_decay=0.002)
    place(y, 0.35 * latch, secs(0.312), circular=False)
    rat = impact(rng, random_modes(rng, 400.0, 3000.0, 6, 0.02, 0.12), 0.3, hard=0.4)
    place(y, 0.12 * rat, secs(0.345), circular=False)
    return fade(y, 0.0, 0.2)


def typewriter(rng: np.random.Generator, chars: int, bell_at: int | None = None, ret: bool = True) -> np.ndarray:
    """1960s manual office typewriter: type-bar strikes on the platen (+ escapement tick), the duller
    space bar, the margin bell, then the carriage return (line-space ratchet, slide, stop).  Mono."""
    y = np.zeros(secs(chars * 0.5 + 2.5))
    t = 0.05
    since, word = 0, int(rng.integers(3, 8))
    for i in range(chars):
        if since >= word:                    # space bar
            k = impact(rng, [(rng.uniform(330.0, 420.0), 1.0, 0.03), (rng.uniform(780.0, 900.0), 0.6, 0.02),
                             (rng.uniform(1500.0, 1800.0), 0.3, 0.012)], 0.12, hard=0.35, noise_lo=500.0,
                       noise_hi=5000.0, noise_amt=0.25, noise_decay=0.003)
            place(y, 0.5 * k, secs(t), circular=False)
            since, word = 0, int(rng.integers(2, 9))
            t += rng.uniform(0.13, 0.26)
        else:                                # type bar
            k = impact(rng, [(rng.uniform(1900.0, 2500.0), 1.0, 0.011), (rng.uniform(3200.0, 4000.0), 0.6, 0.008),
                             (rng.uniform(950.0, 1250.0), 0.55, 0.016), (rng.uniform(250.0, 330.0), 0.8, 0.032),
                             (rng.uniform(130.0, 160.0), 0.5, 0.045)], 0.16, hard=0.75, noise_lo=1200.0,
                       noise_hi=9000.0, noise_amt=0.45, noise_decay=0.0016)
            place(y, rng.uniform(0.75, 1.0) * k, secs(t), circular=False)
            esc = impact(rng, random_modes(rng, 2600.0, 6500.0, 5, 0.004, 0.012), 0.04, hard=0.8, noise_amt=0.3,
                         noise_decay=0.001)
            place(y, 0.16 * esc, secs(t + rng.uniform(0.016, 0.024)), circular=False)
            since += 1
            gap = rng.uniform(0.10, 0.19)
            if rng.random() < 0.08:
                gap += rng.uniform(0.25, 0.6)  # the typist hesitates over a word
            t += gap
        if bell_at is not None and i == bell_at:
            bell = modal([(2480.0, 1.0, 0.9), (3790.0, 0.35, 0.5), (5650.0, 0.25, 0.3), (1240.0, 0.08, 0.6)], 1.0,
                         seed=int(rng.integers(1 << 30)), attack=0.0005)
            place(y, 0.22 * bell, secs(t - 0.06), circular=False)
    if ret:
        t += rng.uniform(0.35, 0.55)
        for j in range(9):
            c = impact(rng, random_modes(rng, 1800.0, 6000.0, 4, 0.004, 0.01), 0.03, hard=0.7, noise_amt=0.3,
                       noise_decay=0.001)
            place(y, 0.2 * c, secs(t + j * 0.017), circular=False)
        slide = norm_peak(noise_burst(0.42, rng, 300.0, 3500.0, 1e6, attack=0.05)) * bump(secs(0.42), 0.08, 0.25,
                                                                                           peak_at=0.1)
        place(y, 0.15 * slide, secs(t + 0.1), circular=False)
        stop = impact(rng, [(rng.uniform(180.0, 230.0), 1.0, 0.06), (rng.uniform(520.0, 640.0), 0.7, 0.04),
                            (rng.uniform(1300.0, 1600.0), 0.4, 0.025), (rng.uniform(2600.0, 3100.0), 0.25, 0.015)],
                      0.3, hard=0.6, noise_amt=0.4, noise_decay=0.003)
        place(y, 0.9 * stop, secs(t + 0.5), circular=False)
        t += 0.8
    return y[:secs(t + 0.4)]


def mimeograph(rng: np.random.Generator, cycles: int, period: float = 0.86) -> np.ndarray:
    """Hand-cranked rotary stencil duplicator: per turn a gear purr, the paper pick-up, the impression
    roller's soft thump with the gripper clack, the sheet landing on the stack.  Winds up and eases off."""
    y = np.zeros(secs(cycles * period * 1.4 + 1.5))
    t = 0.0
    for c in range(cycles):
        sp = 0.75 + 0.25 * smoothstep(c / 3.0) - 0.15 * smoothstep((c - cycles + 3) / 3.0)
        per = period / sp * (1.0 + rng.normal(0.0, 0.02))
        L = secs(per)
        tt = np.arange(L) / SR
        purr = norm_peak(noise_burst(per, rng, 80.0, 900.0, 1e6, attack=0.0))
        purr *= (0.5 + 0.5 * np.sin(np.pi * tt / per) ** 2) * (1.0 + 0.4 * np.sin(TAU * 31.0 * tt))
        place(y, 0.05 * purr, secs(t), circular=False)
        place(y, 0.30 * paper_rustle(rng, 0.14, 0.35, 1), secs(t + 0.18 * per), circular=False)
        th = modal([(rng.uniform(95.0, 115.0), 1.0, 0.09), (rng.uniform(210.0, 250.0), 0.5, 0.06),
                    (rng.uniform(520.0, 600.0), 0.25, 0.03)], 0.3, seed=int(rng.integers(1 << 30)), attack=0.004)
        place(y, 0.28 * norm_peak(th), secs(t + 0.45 * per), circular=False)
        ck = impact(rng, random_modes(rng, 700.0, 3600.0, 6, 0.01, 0.05), 0.1, hard=0.5, noise_amt=0.3)
        place(y, 0.22 * ck, secs(t + 0.47 * per), circular=False)
        sl = noise_burst(0.05, rng, 400.0, 4000.0, 0.025, attack=0.004)
        place(y, 0.16 * norm_peak(sl), secs(t + 0.8 * per), circular=False)
        t += per
    return y[:secs(t + 0.6)]


def hall_clock_tick(rng: np.random.Generator, tock: bool) -> np.ndarray:
    """Foyer wall clock: deeper and woodier than the archive clock (bigger case)."""
    k = 0.88 if tock else 1.0
    modes = [(1320.0 * k, 1.0, 0.035), (2150.0 * k, 0.55, 0.026), (3450.0 * k, 0.3, 0.016), (610.0 * k, 0.45, 0.055),
             (185.0 * k, 0.35, 0.09)]
    return impact(rng, modes, 0.25, hard=0.65, noise_lo=1500.0, noise_hi=7000.0, noise_amt=0.2, noise_decay=0.0015)


def radiator_gurgle(rng: np.random.Generator, dur: float = 2.2) -> np.ndarray:
    y = np.zeros(secs(dur + 0.2))
    tt = 0.05
    while tt < dur:
        f = rng.uniform(200.0, 480.0)
        L = secs(rng.uniform(0.03, 0.07))
        tb = np.arange(L) / SR
        bub = np.sin(TAU * np.cumsum(f * (1 + 0.6 * tb / tb[-1])) / SR) * np.exp(-tb / 0.02)
        place(y, bub * rng.uniform(0.3, 1.0), secs(tt), circular=False)
        tt += rng.exponential(0.1)
    return eq(y, ('lp', 1400.0, 2), circular=False)


# =============================================================================== amb_veltrava_palais
def amb_veltrava_palais():
    name = 'amb_veltrava_palais'
    rng = np.random.default_rng(seed_of(name))
    M = Mix()
    hall = ir_palais(seed_of(name, 1))
    saal = ir_saal(seed_of(name, 2))
    office = ir_office(seed_of(name, 3))
    # --- beds -------------------------------------------------------------------------------------
    room = shaped_noise(N, rng, lambda f: mag_tilt(f, -4.0, 90.0) * mag_bp(f, 28.0, 900.0, 2)
                        + 0.008 * mag_bp(f, 2500.0, 7000.0, 2), ch=2, corr=0.6)
    room *= (1.0 + 0.08 * smooth_periodic(N, 6, rng))[:, None]
    M.bed(room, -1.5)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 25.0, 170.0, 2), ch=2, corr=0.85)
    city *= (1.0 + 0.3 * smooth_periodic(N, 6, rng))[:, None]
    M.bed(city, -8.5)
    gust = gust_curve(N, rng, [(9.0, 0.4, 2.5, 3.5), (27.0, 0.5, 2.0, 3.0), (47.0, 0.35, 3.0, 4.0)], base=0.22,
                      turb=0.05, turb_rate=0.4)
    M.bed(wind(N, rng, gust, lp_base=160.0, lp_gust=420.0, whistle=0.05, whistle_f=(520.0, 760.0), corr=0.5,
               hp=50.0, tilt=-0.6), -14.0)
    # the delegations behind the double doors; the door stands open from T_OPEN to T_CLOSE
    t_open, t_close = 30.6, 36.9
    mur = door_filter(delegations(rng, N, saal), t_open, t_close)
    M.bed(0.75 * mur + 0.45 * fftconv(mur, hall, circular=True), -3.0)
    M.event(far(door_open(rng), hall, lp=7000.0, wet=0.6, dry=0.8, pan=0.12), t_open - 0.3, -1.0)
    M.event(far(door_close(rng), hall, lp=7000.0, wet=0.7, dry=0.8, pan=0.12), t_close + 0.15, 18.0, mode='peak')
    for (dt, f) in [(1.2, 4100.0), (1.55, 5300.0), (2.3, 4700.0), (2.6, 6100.0)]:     # chandelier in the draught
        g = modal([(f, 1.0, 0.3), (f * 2.71, 0.35, 0.15), (f * 1.49, 0.2, 0.2)], 0.4, seed=int(rng.integers(1 << 30)),
                  attack=0.0004)
        M.event(far(g, hall, wet=0.8, dry=0.5, pan=-0.05), t_open + dt, -2.0, mode='peak')
    # the foyer clock: 60 beats per loop
    ticks = np.zeros(N)
    for i in range(60):
        place(ticks, hall_clock_tick(np.random.default_rng(seed_of(name, 10 + i % 6)), i % 2 == 1)
              * (1.0 if i % 2 == 0 else 0.84), secs(i * 1.0 + 0.35), circular=True)
    tk = pan2(ticks, -0.35)
    tk = 0.7 * tk + 0.5 * fftconv(tk, hall, circular=True)
    M.buf += tk * (db2a(15.0) / float(np.max(np.abs(tk))))
    # typewriters in the protocol office (through its open door)
    tw = typewriter(rng, 26, bell_at=21, ret=True)
    tw = eq(tw, ('lp', 5500.0, 2), circular=False)
    tw = far(tw, office, wet=0.5, dry=1.0, pan=0.45)
    M.event(far(tw, hall, lp=4500.0, wet=0.55, dry=0.6), 5.2, 19.0, mode='peak')
    tw2 = far(eq(typewriter(rng, 13, ret=False), ('lp', 5500.0, 2), circular=False), office, wet=0.5, dry=1.0, pan=0.5)
    M.event(far(tw2, hall, lp=4500.0, wet=0.55, dry=0.6), 43.5, 15.0, mode='peak')
    # a mimeograph somewhere further down the corridor (runs across the loop point)
    mg = far(mimeograph(rng, 19), office, lp=2200.0, wet=0.6, dry=1.0, pan=0.6)
    M.event(far(mg, hall, wet=1.0, dry=0.35), 47.5, 1.0)
    # radiators under the tall windows + one gurgle
    for (t, pk, pan) in [(2.2, 9.0, -0.5), (2.48, 7.0, -0.5), (11.3, 8.5, 0.55), (19.9, 10.0, -0.2), (20.14, 8.0, -0.2),
                         (20.31, 6.5, -0.2), (38.6, 9.0, 0.5), (49.7, 9.5, -0.45), (56.4, 8.0, 0.4)]:
        tink = impact(rng, random_modes(rng, 1500.0, 5200.0, 6, 0.015, 0.06), 0.15, hard=0.7, noise_amt=0.3)
        M.event(far(tink, hall, wet=0.45, dry=1.0, pan=pan), t, pk + 2.0, mode='peak')
    M.event(far(radiator_gurgle(rng), hall, wet=0.5, dry=1.0, pan=0.5), 25.8, -6.0)
    out = M.master(-25.0, lp=11000.0)
    return out, (0, N)


# =============================================================================== mus_veltrava
# V (Veltrava, the two-language motif): (beat, dur, midi).  V_A is the statement (felt piano), V_B its
# "interpretation" (solo viola, two beats behind): same contour, but B3 -> Bb3 and the changed note is
# held longer.  The piano's third statement stops on B; the second leaves the changed note out.
V_A = [(0, 1, 52), (1, 1.5, 60), (2.5, 0.5, 59), (3, 2, 57), (6, 2, 52)]
V_B = [(0, 1, 52), (1, 1, 60), (2, 1, 58), (3, 2, 57), (6, 2, 52)]
V_A_GAP = [(0, 1, 52), (1, 1.5, 60), (3.5, 2.5, 57)]          # ... the word that is not said
V_A_STOP = [(0, 1, 52), (1, 1.5, 60), (2.5, 1.5, 59)]          # ... and the sentence left open
V_B_END = [(0, 1, 52), (1, 1, 60), (2, 1, 58), (3, 2.5, 57)]

# 8-beat colour slots above the A drone (A1 E2): neutral open fifths, F/D colours, the Bb pressure
# (A/Bb rub, the X1 ending), release into the first plain minor triad.
V_PLAN = [(0, [52, 57, 64], 0.30), (8, [52, 59, 64], 0.31), (16, [53, 57, 64], 0.33), (24, [50, 53, 60], 0.33),
          (32, [53, 60, 64], 0.35), (40, [55, 62, 64], 0.34), (48, [50, 58, 65], 0.37), (56, [53, 58, 62, 64], 0.40),
          (64, [52, 57, 60], 0.35), (72, [53, 57, 64], 0.33), (80, [52, 55, 60], 0.31), (88, [52, 59, 64], 0.30)]

DRONE_EQ = (('hp', 30, 2), ('ls', 90, -1.0), ('bell', 220, 1.0, 1.4), ('bell', 1500, -2.0, 1.5), ('lp', 6000, 2))
SOLO_EQ = (('hp', 90, 2), ('bell', 420, 1.5, 1.2), ('bell', 2600, -2.5, 1.5), ('lp', 6500, 2))
FELT_EQ = (('hp', 60, 2), ('bell', 2800, -1.5, 1.5), ('lp', 7000, 2))


def solo_line(T: Track, notes, beat0: float, vel: float, pan: float = 0.28) -> None:
    """Solo viola-like line (two-player 'ensemble' = one desk, wider vibrato), each note bowed."""
    for (b, d, m) in notes:
        T.strings(beat0 + b, d * 0.96, [m], vel=vel, stem='solo', attack=0.28, release=0.9, bright=0.42, pan=pan,
                  voices=2, vib=11.0, swell=0.12)


def mus_veltrava():
    name = 'mus_veltrava'
    T = Track(name, bpm=64, beats=96, loop=True, seed=seed_of(name))
    # bowed open-fifth drone on A in overlapping 16-beat breaths (never stops: the city waits)
    for b in range(0, 96, 16):
        T.strings(b, 18.0, [33, 40], vel=0.40, stem='drone', attack=2.6, release=3.2, bright=0.22, vib=4.0, voices=4)
    for (b, ch, v) in V_PLAN:
        T.strings(b, 8.7, ch, vel=v, attack=2.0, release=2.8, bright=0.33, voices=3, vib=6.0,
                  swell=0.25 if b == 56 else 0.0, bass_boost=1.15)
    T.strings(0, 15.0, [76], vel=0.10, stem='strings_hi', harmonic=True, attack=3.5, release=3.0, vib=3.0)
    T.strings(48, 15.0, [81], vel=0.11, stem='strings_hi', harmonic=True, attack=3.0, release=3.0, vib=3.0)
    # clockwork pulse: muted piano E3 tick-tock, A2 on the downbeats; hesitations at phrase ends and in
    # the pressure section, where the tick is pushed up a semitone to F3
    rests = {15, 31, 47, 51, 54, 63, 79, 95}
    for b in range(96):
        if b in rests:
            continue
        T.piano([(b, 1, 53 if 56 <= b < 64 else 52)], vel=0.25 if b % 2 == 0 else 0.19, felt=1.0, decay=0.42,
                stem='muted', legato=0.5, pan=-0.1)
        if b % 4 == 0:
            T.piano([(b, 1, 45)], vel=0.14, felt=1.0, decay=0.5, stem='muted', legato=0.6, pan=-0.15)
    # celesta gear: one tooth every three beats against the four-beat clock (absent under the pressure
    # section and the third statement)
    gear = list(range(4, 44, 3)) + list(range(82, 96, 3))
    cyc = [64, 69, 64, 71]
    for i, b in enumerate(gear):
        T.celesta([(b, 1, cyc[i % 4])], vel=0.24, pan=0.25, bright=0.4)
    # the two-language motif
    T.piano(V_A, vel=0.40, beat0=16, felt=0.72, decay=0.9, pan=-0.12)
    solo_line(T, V_B, 18, vel=0.34)
    solo_line(T, V_B, 48, vel=0.38)
    T.piano(V_A_GAP, vel=0.36, beat0=50, felt=0.75, decay=0.9, pan=-0.12)
    T.piano(V_A_STOP, vel=0.36, beat0=72, felt=0.75, decay=0.9, pan=-0.12)
    solo_line(T, V_B_END, 76, vel=0.32)
    # iron under the surface: a very soft low-brass A2, the Bb2 rub against it at the peak
    T.brass(48, 16.4, [45], vel=0.26, attack=2.5, release=3.0, bright=0.2, swell=0.3)
    T.brass(56, 8.2, [46], vel=0.18, attack=2.2, release=2.2, bright=0.18, swell=0.4)
    ir = hall_ir(seed_of(name, 1), rt_low=3.2, rt_high=1.4, predelay=0.03)
    mix = {'drone': (-1.0, 0.28, DRONE_EQ), 'strings': (-3.0, 0.32, STR_EQ), 'strings_hi': (-16.0, 0.5, STR_HI_EQ),
           'solo': (-3.0, 0.28, SOLO_EQ), 'piano': (-1.5, 0.30, FELT_EQ), 'muted': (-5.0, 0.22, MUTED_EQ),
           'celesta': (-11.0, 0.40, CEL_EQ), 'brass': (-11.0, 0.25, BRASS_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0, master_lp=10000.0)
    # a loop has no intrinsic start: open the file half a beat before the downbeat (inside the pulse rest
    # on beat 96), so the loop point never sits on a note onset.  Exact, because everything is circular.
    out = np.roll(out, int(round(0.5 * T.spb * SR)), axis=0)
    return out, (0, out.shape[0])


TRACKS = {
    'amb_veltrava_station': amb_veltrava_station,
    'amb_veltrava_palais': amb_veltrava_palais,
    'mus_veltrava': mus_veltrava,
}

REFERENCES = ['amb/amb_karsk_yard', 'amb/amb_berlin_archive', 'amb/amb_berlin_street', 'music/mus_karsk',
              'music/mus_berlin', 'music/mus_menu']


# =============================================================================== runner
def wav_path(name: str) -> str:
    return os.path.join(AUDIO, KIND[name], name + '.wav')


def build_one(name: str) -> dict:
    t0 = time.time()
    sig, loop = TRACKS[name]()
    path = wav_path(name)
    st = write_wav(path, sig, loop=loop, seed=zlib.crc32(name.encode()))
    return {'name': name, 'path': path, 'loop': loop, 'seconds': round(time.time() - t0, 1), **st}


def ensure_import(path: str) -> bool:
    """Lossless PCM import (build_all.IMPORT_TEMPLATE); keeps an existing uid, only patches compress/mode."""
    from build_all import IMPORT_TEMPLATE
    imp = path + '.import'
    if not os.path.exists(imp):
        with open(imp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(IMPORT_TEMPLATE)
        return True
    txt = open(imp, encoding='utf-8').read()
    if 'compress/mode=0' in txt:
        return False
    txt = re.sub(r'compress/mode=\d+', 'compress/mode=0', txt) if 'compress/mode=' in txt \
        else txt.rstrip('\n') + '\ncompress/mode=0\n'
    with open(imp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    return True


def seam_continuity(x: np.ndarray, ms: float = 50.0) -> dict:
    """Last vs first `ms` of the loop: RMS of both sides, and the sample step / second difference across
    the loop point as a percentile of the steps inside that +-ms window (a click would be ~p100)."""
    k = secs(ms / 1000.0)
    win = np.concatenate([x[-k:], x[:k]], axis=0)
    steps = np.abs(np.diff(win, axis=0)).max(axis=1)
    seam_step = steps[k - 1]
    d2 = np.abs(win[2:] - 2.0 * win[1:-1] + win[:-2]).max(axis=1)
    seam_d2 = max(d2[k - 2], d2[k - 1])
    r_end, r_start = float(a2db(rms(x[-k:]))), float(a2db(rms(x[:k])))
    return {'rms_last_dbfs': round(r_end, 2), 'rms_first_dbfs': round(r_start, 2),
            'rms_delta_db': round(r_start - r_end, 2),
            'step_pct_local': round(float(np.mean(steps < seam_step) * 100.0), 1),
            'step_vs_local_median': round(float(seam_step / (np.median(steps) + 1e-12)), 2),
            'curv_pct_local': round(float(np.mean(d2 < seam_d2) * 100.0), 1)}


def analyse(path: str, name: str, preview: str | None) -> dict:
    import analyze
    r = analyze.analyze_file(path)
    b = analyze.band_shares(path)
    r['name'] = name
    r['lufs_approx'] = float(b.pop('lufs_approx'))
    r['band_energy_pct'] = b
    r['bytes'] = os.path.getsize(path)
    if r.get('loop'):
        x, _, _ = read_wav(path)
        r['seam_50ms'] = seam_continuity(x)
    if preview:
        os.makedirs(preview, exist_ok=True)
        analyze.render_spectrogram(path, os.path.join(preview, name + '.png'),
                                   f"{name}   RMS {r['rms_dbfs']} dBFS   peak {r['peak_dbfs']} dBFS   {r['seconds']} s")
    return r


def print_rows(rows: list[dict]) -> None:
    print(f"{'file':<34}{'ch':>3}{'sec':>8}{'MB':>7}{'RMS':>7}{'st400':>7}{'peak':>7}{'tpk':>7}{'LUFS~':>7}"
          f"{'clip':>5}{'>16k':>6}{'cent':>6}")
    for r in rows:
        print(f"{r['file'].replace('assets/audio/', ''):<34}{r['channels']:>3}{r['seconds']:>8.2f}"
              f"{r['bytes'] / 1e6:>7.2f}{r['rms_dbfs']:>7.1f}{r['max_rms400ms_dbfs']:>7.1f}{r['peak_dbfs']:>7.1f}"
              f"{r['true_peak_dbfs']:>7.1f}{r['lufs_approx']:>7.1f}{r['clipped_samples']:>5}{r['hf_above_16k_db']:>6.0f}"
              f"{r['centroid_hz']:>6.0f}")
        if r.get('loop'):
            s = r.get('seam_50ms', {})
            print(f"    loop {r['loop'][0]}..{r['loop'][1]}  seam: jump {r['seam_jump_vs_median_step']}x median step, "
                  f"HF p{r['seam_hf_percentile']}, curvature p{r['seam_curvature_percentile']} | 50 ms: RMS "
                  f"{s.get('rms_last_dbfs')} -> {s.get('rms_first_dbfs')} dBFS (delta {s.get('rms_delta_db')} dB), "
                  f"step p{s.get('step_pct_local')} / {s.get('step_vs_local_median')}x local median, "
                  f"curvature p{s.get('curv_pct_local')}")
        print('    bands %: ' + '  '.join(f'{k} {v}' for k, v in r['band_energy_pct'].items()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--only', default='', help='comma separated names: ' + ', '.join(TRACKS))
    ap.add_argument('--jobs', type=int, default=min(3, os.cpu_count() or 1))
    ap.add_argument('--preview', default=None, help='folder for spectrogram/seam PNGs + c3_analysis.json '
                    '(default assets/audio/_preview, which carries a .gdignore and is not versioned)')
    ap.add_argument('--no-analysis', action='store_true')
    ap.add_argument('--no-spectro', action='store_true')
    ap.add_argument('--compare', action='store_true', help='also measure the existing ambience/music loops')
    ap.add_argument('--godot', action='store_true', help='run `godot --headless --path <root> --import` afterwards '
                    '(binary from $GODOT or PATH)')
    args = ap.parse_args()
    names = [n.strip() for n in args.only.split(',') if n.strip()] or list(TRACKS)
    for n in names:
        if n not in TRACKS:
            sys.exit(f'unknown asset {n!r}; known: {", ".join(TRACKS)}')
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max(1, min(args.jobs, len(names)))) as ex:
        built = list(ex.map(build_one, names))
    for b in built:
        print(f"  built {b['name']:<22}{b['seconds']:>7.1f}s  {b['frames']} frames x {b['channels']} ch, "
              f"loop {b['loop']}, clipped {b['clipped_samples']}  -> {os.path.relpath(b['path'], ROOT)}")
        if ensure_import(b['path']):
            print(f"  wrote {os.path.relpath(b['path'], ROOT)}.import (lossless PCM, compress/mode=0)")
    print(f'synthesis done in {time.time() - t0:.1f}s')
    if not args.no_analysis:
        import analyze
        preview = None
        if not args.no_spectro:
            preview = args.preview or analyze.PREVIEW
            if preview == analyze.PREVIEW:
                analyze.ensure_preview_dir()
        rows = [analyse(b['path'], b['name'], preview) for b in built]
        print_rows(rows)
        total = sum(os.path.getsize(wav_path(n)) for n in TRACKS if os.path.exists(wav_path(n)))
        print(f'total size of the Veltrava files: {total / 1e6:.2f} MB ({total / 2 ** 20:.2f} MiB)')
        if args.compare:
            ref = [analyse(os.path.join(AUDIO, p + '.wav'), os.path.basename(p), None) for p in REFERENCES]
            print('reference loops (existing score / ambience):')
            print_rows(ref)
        if preview:
            with open(os.path.join(preview, 'c3_analysis.json'), 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=1)
            print(f'previews: {preview}')
    if args.godot:
        exe = os.environ.get('GODOT') or shutil.which('godot')
        if not exe:
            print('godot not found ($GODOT / PATH)')
        else:
            p = subprocess.run([exe, '--headless', '--path', ROOT, '--import'], capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=900)
            errs = [ln for ln in (p.stdout + p.stderr).splitlines() if 'ERROR' in ln and 'veltrava' in ln.lower()]
            print(f'godot --import exit {p.returncode}; veltrava-related errors: {len(errs)}')
            for e in errs[:20]:
                print('   ', e)
    print(f'total {time.time() - t0:.1f}s')


if __name__ == '__main__':
    main()
