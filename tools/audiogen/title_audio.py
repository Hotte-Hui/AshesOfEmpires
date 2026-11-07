"""title_audio -- original synthesized sounds of the boot sequence (TECHNICAL_ARCHITECTURE §12.13, round 11).

Run:  py -3 -P tools/audiogen/title_audio.py        (numpy only, deterministic, no samples, no network)

Writes (44.1 kHz, 16-bit, stereo, one-shots):
  assets/audio/music/mus_title_sting.wav  ~9 s   the title picture.  Snow wind and a low D drone (strings, brass pedal,
        a cold harmonic) open; a locomotive horn far across the snow (~0.9 s); the head of K (Karsk: D5 A4 E5, felt
        piano) is answered by the head of B (Berlin: G4 Bb4 A4, celesta) -- the two motifs of music.py; then ONE deep
        stroke exactly at 2.40 s, when the title appears (timpani + sub, low brass and full strings on D minor add9),
        and a long open D/A that rings into the menu theme (D Aeolian / G Dorian).  No fanfare, no march.
  assets/audio/sfx/splash_ember.wav       ~3 s   the studio card: a soft warm breath, embers crackling up out of it, a
        faint glassy shimmer as the flame rises; no melody.
Every value comes from fixed seeds: a re-run writes byte-identical files.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import SR, secs, pan2, eq, fade, normalize_peak, rms, write_wav, smoothstep  # noqa: E402
from instruments import modal, noise_burst  # noqa: E402
from music import Track, hall_ir, STR_EQ, STR_HI_EQ, BRASS_EQ, PIANO_EQ, CEL_EQ  # noqa: E402
import foley  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
STROKE = 2.40          # s: the title appears (scripts/ui/boot_splash.gd LOGO_AT)


def timpani(rng: np.random.Generator) -> np.ndarray:
    """One big low D stroke (membrane modes + mallet noise), mono."""
    f = 73.42
    modes = [(f, 1.0, 2.6), (f * 1.504, 0.55, 1.9), (f * 1.742, 0.32, 1.4), (f * 2.0, 0.26, 1.2),
             (f * 2.245, 0.16, 0.9), (f * 2.494, 0.10, 0.7), (f * 0.5, 0.45, 1.8)]
    hit = modal(modes, 3.6, seed=int(rng.integers(1 << 30)), attack=0.002)
    hit[:secs(0.03)] += 0.35 * noise_burst(0.03, rng, 60, 1800, 0.02)
    t = np.arange(secs(3.6)) / SR
    sub = np.sin(2 * np.pi * 36.71 * t) * np.exp(-t / 1.1) * smoothstep(t / 0.01)
    return hit + 0.6 * sub


def wind(rng: np.random.Generator, dur: float) -> np.ndarray:
    n = secs(dur)
    z = rng.standard_normal((n, 2))
    z = eq(z, ('hp', 140, 2), ('lp', 1100, 2), circular=False)
    t = np.arange(n) / SR
    gust = 0.55 + 0.3 * np.sin(2 * np.pi * 0.31 * t + 0.4) + 0.15 * np.sin(2 * np.pi * 0.83 * t)
    env = smoothstep(t / 0.8) * np.clip(1.0 - (t - (dur - 2.5)) / 2.5, 0.0, 1.0)
    return z * (gust * env)[:, None] / max(rms(z), 1e-9)


def mus_title_sting() -> np.ndarray:
    T = Track('mus_title_sting', bpm=60, beats=9.2, loop=False, seed=1101, tail=0.0)
    rng = np.random.default_rng(1101)
    # the drone: D2 / A2 from nothing, a brass pedal, one cold harmonic high above
    T.strings(0.0, STROKE, [38, 45], vel=0.34, attack=1.6, release=0.4, swell=0.6, bright=0.35, stem='drone')
    T.brass(0.5, STROKE - 0.5, [38], vel=0.24, attack=1.2, release=0.3, bright=0.2, swell=0.5, stem='drone')
    T.strings(0.3, STROKE - 0.2, [81], vel=0.09, stem='strings_hi', harmonic=True, attack=1.4, release=0.6)
    # K asks (felt piano), B answers (celesta)
    T.piano([(0.55, 0.42, 74), (0.98, 0.4, 69), (1.38, 0.9, 76)], vel=0.33)
    T.celesta([(1.62, 0.25, 67), (1.86, 0.25, 70), (2.08, 0.3, 69)], vel=0.30)
    # the stroke: D minor add9 (D2 A2 D3 F3 E4 A4), full strings and low brass, timpani + sub
    T.strings(STROKE, 4.8, [38, 45, 50, 53, 64, 69], vel=0.56, attack=0.15, release=2.4, bright=0.5)
    T.strings(STROKE + 0.1, 4.6, [86], vel=0.10, stem='strings_hi', harmonic=True, attack=0.8, release=2.0)
    T.brass(STROKE, 3.4, [38, 45, 50], vel=0.48, attack=0.06, release=2.2, bright=0.55)
    T.put('timp', STROKE, pan2(timpani(rng), 0.0))
    # the line: a locomotive horn far across the snow, and the wind
    T.put('horn', 0.9, foley.far_horn(rng, 220.0, 1.5, chord=(1.0, 1.335)))
    T.put('wind', 0.0, wind(rng, 7.5))
    ir = hall_ir(1101, rt_low=3.6, rt_high=1.4, length=4.0)
    mix = {'strings': (0.0, 0.32, STR_EQ), 'strings_hi': (-13.0, 0.5, STR_HI_EQ),
           'drone': (-11.0, 0.3, STR_EQ), 'piano': (-9.0, 0.36, PIANO_EQ), 'celesta': (-11.0, 0.4, CEL_EQ),
           'brass': (-4.0, 0.28, BRASS_EQ), 'timp': (-1.0, 0.22, (('hp', 28, 2), ('lp', 2400, 2))),
           'horn': (-17.0, 0.10, (('hp', 160, 2), ('lp', 1500, 2))),
           'wind': (-25.0, 0.0, (('hp', 150, 2), ('lp', 1000, 2)))}
    return T.mixdown(mix, ir, target_rms=-16.0, end_fade=2.8, rms_from=(STROKE, STROKE + 2.5))


def splash_ember() -> np.ndarray:
    rng = np.random.default_rng(4242)
    dur = 3.0
    n = secs(dur)
    t = np.arange(n) / SR
    # warm breath: low-passed noise swelling in and out
    breath = eq(rng.standard_normal(n), ('hp', 70, 2), ('lp', 420, 2), circular=False)
    breath /= max(rms(breath), 1e-9)
    breath *= smoothstep(t / 0.7) * np.clip(1.0 - (t - 1.5) / 1.4, 0.0, 1.0)
    # crackle: sparse snaps, densest as the flame rises
    rate = 6.0 + 34.0 * np.exp(-((t - 1.0) / 0.55) ** 2) + 10.0 * smoothstep(t / 0.4) * np.clip(1.6 - t / 1.8, 0, 1)
    crack = foley.grain_cloud(rng, dur, rate, 900.0, 5200.0, t60_lo=0.003, t60_hi=0.02)
    crack /= max(np.max(np.abs(crack)), 1e-9)
    # glassy shimmer: two faint high partials blooming with the flame
    shim = modal([(2349.3, 0.5, 1.4), (3520.0, 0.3, 1.1), (4698.6, 0.15, 0.8)], dur, seed=7, attack=0.25)
    sh = np.zeros(n)
    k = secs(0.75)
    sh[k:] = shim[:n - k]
    out = 0.55 * pan2(breath, -0.05) + 0.42 * pan2(crack, 0.12) + 0.05 * pan2(sh, -0.2)
    out = eq(out, ('hp', 40, 2), ('lp', 9000, 2), circular=False)
    out = fade(out, 0.01, 0.6)
    return normalize_peak(out, -9.0)


def main() -> None:
    for kind, name, fn in [('music', 'mus_title_sting', mus_title_sting), ('sfx', 'splash_ember', splash_ember)]:
        x = fn()
        path = os.path.join(ROOT, 'assets', 'audio', kind, name + '.wav')
        st = write_wav(path, x)
        print('wrote assets/audio/%s/%s.wav %.2f s, clipped %d' % (kind, name, st['frames'] / SR, st['clipped_samples']))


if __name__ == '__main__':
    main()
