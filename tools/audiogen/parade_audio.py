"""parade_audio.py -- music and sound cues for L_M1_Parade (owner: parade).  Synthesised from scratch with the
project's numpy DSP kit (dsp.py / instruments.py), deterministic, no samples.

  assets/audio/music/mus_parade.wav    47.0 s one-shot, starts with the level (t = 0):
        a cold drum pulse (bass drum on every beat at 57 bpm = half the 114-step cadence, a dry side-drum
        figure) over a low brass drone (C/Db cluster, a tritone pressing in at the tribune) -- never a
        triumphant march: no melody, no major third, no cymbal.  Drums thin to a heartbeat in the crowd
        shot, fall silent under the jets and Konrad's thought, and return far away and echoing over the
        cleared street.
  assets/audio/sfx/parade_boots.wav     6 s   hundreds of boots in step on packed snow
  assets/audio/sfx/parade_tanks.wav     7 s   diesel rumble, track clatter, rattling window glass
  assets/audio/sfx/parade_jets.wav      5 s   low jet formation passing over the plaza
  assets/audio/sfx/parade_pa_chime.wav  2.4 s two-tone loudspeaker gong with the plaza echo
Run: py -3 -P tools/audiogen/parade_audio.py
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import (SR, secs, eq, make_ir, reverb, limiter, normalize_rms, write_wav, place, to_stereo,  # noqa: E402
                 pan2, smoothstep)
from instruments import brass_note, string_note, noise_burst, impact, random_modes  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
MUS = os.path.join(ROOT, 'assets', 'audio', 'music')
SFX = os.path.join(ROOT, 'assets', 'audio', 'sfx')


def st(x):
    return to_stereo(x)


def bass_drum(rng, vel=1.0):
    body = impact(rng, random_modes(rng, 48.0, 140.0, 6, 0.35, 0.9, tilt=1.2), 1.6, hard=0.25,
                  noise_lo=60.0, noise_hi=1200.0, noise_amt=0.25, noise_decay=0.03)
    return eq(body, ('lp', 900.0, 2), circular=False) * vel


def side_drum(rng, vel=0.5, dur=0.18):
    z = noise_burst(dur, rng, 1400.0, 7000.0, dur * 0.8)
    ring = impact(rng, random_modes(rng, 180.0, 420.0, 4, 0.05, 0.15), 0.3, hard=0.6, noise_amt=0.1)
    return (z * 0.6 + ring[:len(z)] * 0.5) * vel


def mus_parade():
    T = 47.0
    n = secs(T)
    rng = np.random.default_rng(1964)
    drums = np.zeros((n, 2))
    far = np.zeros((n, 2))
    drone = np.zeros((n, 2))
    beat = 60.0 / 57.0
    t = 0.5
    k = 0
    while t < T - 0.5:
        if t < 24.5:
            v = 0.45 + 0.55 * smoothstep(min(1.0, t / 6.5))
            place(drums, pan2(bass_drum(rng, v), -0.05), secs(t), circular=False)
            # dry side-drum figure: "ta - ta-ta" on the off-beats, from the march on (6.5 s)
            if t >= 6.4:
                for d, vv in ((0.5, 0.35), (0.75, 0.22), (0.875, 0.26)):
                    place(drums, pan2(side_drum(rng, vv * v), 0.25), secs(t + d * beat), circular=False)
        elif t < 30.5:
            if k % 2 == 0:       # crowd shot: only a heartbeat-like bass drum, every second beat
                place(drums, pan2(bass_drum(rng, 0.55), 0.0), secs(t), circular=False)
        elif t >= 40.5:
            place(far, pan2(bass_drum(rng, 0.5), 0.3), secs(t), circular=False)
            if k % 2 == 1:
                place(far, pan2(side_drum(rng, 0.2), 0.35), secs(t + 0.5 * beat), circular=False)
        t += beat
        k += 1
    # low brass drone: C2 + Db2 from the start, Gb2 (tritone) pressing in at the tribune, all thinning out
    for (s0, dur, m, v) in [(0.0, 30.0, 36, 0.34), (2.0, 28.0, 37, 0.26), (18.5, 12.0, 42, 0.24),
                            (30.5, 10.0, 36, 0.2), (40.5, 6.4, 37, 0.14)]:
        sig = brass_note(m, dur, vel=v, attack=2.4, release=1.2, seed=int(rng.integers(1 << 30)), bright=0.45,
                         swell=1.2, pan=float(rng.uniform(-0.25, 0.25)))
        place(drone, st(sig), secs(s0), circular=False)
    # sub pedal C1
    tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * 32.703 * tt) * 0.09 * smoothstep(np.clip(tt / 4.0, 0, 1)) \
        * (1.0 - 0.6 * smoothstep(np.clip((tt - 40.0) / 6.0, 0, 1)))
    drone += st(sub)
    # Konrad's thought: one cold high harmonic, nothing else moves
    place(drone, st(string_note(79, 5.4, vel=0.1, attack=1.6, release=1.0, harmonic=True, seed=6401, vib=2.5,
                                swell=0.4)), secs(35.4), circular=False)
    ir = make_ir(length=4.0, rt_low=3.2, rt_high=1.4, predelay=0.04, seed=11)
    ir_far = make_ir(length=5.5, rt_low=4.6, rt_high=1.2, predelay=0.12, seed=12)
    mix = reverb(drums, ir, wet=0.28, dry=1.0, circular=False) + reverb(drone, ir, wet=0.35, dry=1.0,
                                                                        circular=False)
    farw = reverb(eq(far, ('lp', 1400.0, 2), circular=False), ir_far, wet=0.9, dry=0.25, circular=False)
    mix = mix + farw * 0.8
    fade = 1.0 - smoothstep(np.clip((tt - 45.6) / 1.4, 0, 1))
    mix = mix * fade[:, None]
    mix = eq(mix, ('hp', 28.0, 2), ('lp', 11000.0, 2), circular=False)
    mix = normalize_rms(mix, -21.0)
    return limiter(mix, -1.0)


def parade_boots():
    n = secs(6.0)
    rng = np.random.default_rng(1141)
    x = np.zeros((n, 2))
    step = 60.0 / 114.0
    t = 0.05
    while t < 5.8:
        for _ in range(28):            # a block in step: tiny spread, left/right files
            dt = float(rng.normal(0.0, 0.012))
            thud = impact(rng, random_modes(rng, 70.0, 220.0, 3, 0.05, 0.12), 0.25, hard=0.3, noise_amt=0.2)
            crunch = noise_burst(0.12, rng, 500.0, 4200.0, 0.07)
            sig = thud * 0.5
            sig[:len(crunch)] += crunch * 0.35
            place(x, pan2(sig * 0.12, float(rng.uniform(-0.7, 0.7))), secs(max(0.0, t + dt)), circular=False)
        # kit rattle on every step
        place(x, pan2(noise_burst(0.06, rng, 3000.0, 9000.0, 0.04) * 0.05, 0.1), secs(t + 0.02), circular=False)
        t += step
    env = smoothstep(np.clip(np.arange(n) / SR / 0.4, 0, 1)) * (1 - smoothstep(np.clip((np.arange(n) / SR - 5.2)
                                                                                         / 0.8, 0, 1)))
    x = x * env[:, None]
    x = reverb(x, make_ir(length=2.5, rt_low=2.0, rt_high=0.8, seed=21), wet=0.25, circular=False)
    return limiter(normalize_rms(x, -19.0), -1.0)


def parade_tanks():
    D = 7.0
    n = secs(D)
    rng = np.random.default_rng(1966)
    tt = np.arange(n) / SR
    swell = smoothstep(np.clip(tt / 2.2, 0, 1)) * (1 - 0.45 * smoothstep(np.clip((tt - 4.2) / 2.8, 0, 1)))
    # diesel: low firing harmonics + rumble
    f0 = 31.0 + 3.0 * np.sin(2 * np.pi * 0.21 * tt)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    eng = sum(np.sin(ph * h) / h ** 0.8 for h in range(1, 9)) * 0.08
    rumble = eq(rng.standard_normal(n), ('lp', 160.0, 2), ('hp', 25.0, 2), circular=False) * 0.25
    x = st((eng + rumble) * swell)
    # track clatter: link impacts at ~11 Hz with jitter, some squeal
    t = 0.0
    while t < D - 0.1:
        g = float(np.interp(t, tt[::441], swell[::441]))
        click = impact(rng, random_modes(rng, 700.0, 2600.0, 3, 0.02, 0.06), 0.08, hard=0.8, noise_amt=0.4)
        place(x, pan2(click * 0.09 * g, float(rng.uniform(-0.5, 0.5))), secs(t), circular=False)
        t += 1.0 / 11.0 + float(rng.normal(0, 0.006))
    sq = eq(rng.standard_normal(n), ('hp', 2400.0, 4), ('lp', 3400.0, 4), circular=False)
    x += st(sq * 0.03 * swell * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt) ** 2))
    # window glass rattling in bursts while the hull passes
    t = 1.6
    while t < 5.6:
        for _ in range(int(rng.integers(3, 7))):
            ring = impact(rng, random_modes(rng, 2600.0, 6200.0, 4, 0.03, 0.09), 0.12, hard=0.9, noise_amt=0.15)
            place(x, pan2(ring * 0.05, float(rng.uniform(-0.8, 0.8))), secs(t), circular=False)
            t += float(rng.uniform(0.035, 0.07))
        t += float(rng.uniform(0.25, 0.6))
    x = reverb(x, make_ir(length=2.5, rt_low=2.2, rt_high=0.9, seed=31), wet=0.22, circular=False)
    return limiter(normalize_rms(x, -17.0), -1.0)


def parade_jets():
    D = 5.0
    n = secs(D)
    rng = np.random.default_rng(1967)
    tt = np.arange(n) / SR
    env = np.exp(-((tt - 2.0) / 0.9) ** 2) * 0.9 + np.exp(-((tt - 2.6) / 1.6) ** 2) * 0.35
    lo = eq(rng.standard_normal(n), ('lp', 400.0, 2), circular=False)
    hi = eq(rng.standard_normal(n), ('hp', 900.0, 2), ('lp', 6000.0, 2), circular=False)
    whine = np.sin(2 * np.pi * np.cumsum(2200.0 - 500.0 * smoothstep(np.clip((tt - 1.5) / 1.5, 0, 1))) / SR)
    near = smoothstep(np.clip((tt - 0.8) / 1.2, 0, 1)) * (1 - smoothstep(np.clip((tt - 2.3) / 1.6, 0, 1)))
    sig = lo * 0.6 * env + hi * 0.25 * env * near + whine * 0.02 * near
    pan = np.clip((tt - 2.0) / 1.6, -1.0, 1.0)
    x = np.stack([sig * np.cos((pan + 1) * np.pi / 4), sig * np.sin((pan + 1) * np.pi / 4)], axis=1)
    x = reverb(x, make_ir(length=3.5, rt_low=3.0, rt_high=1.2, seed=41), wet=0.3, circular=False)
    return limiter(normalize_rms(x, -17.0), -1.0)


def parade_pa_chime():
    D = 2.4
    n = secs(D)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for (t0, f) in ((0.0, 554.37), (0.42, 440.0)):
        m = tt >= t0
        u = tt[m] - t0
        tone = sum(np.sin(2 * np.pi * f * h * u) * a for h, a in ((1, 1.0), (2, 0.35), (3, 0.12), (4.2, 0.08)))
        x[m] += tone * np.exp(-u / 0.55) * 0.3
    x = eq(x, ('hp', 420.0, 2), ('lp', 3200.0, 2), circular=False)      # horn loudspeaker band
    x = np.tanh(x * 2.2) * 0.5
    out = reverb(st(x), make_ir(length=3.0, rt_low=2.6, rt_high=1.6, predelay=0.09, seed=51), wet=0.5,
                 circular=False)
    return limiter(normalize_rms(out, -22.0), -1.0)


def main():
    os.makedirs(MUS, exist_ok=True)
    os.makedirs(SFX, exist_ok=True)
    jobs = [(os.path.join(MUS, 'mus_parade.wav'), mus_parade), (os.path.join(SFX, 'parade_boots.wav'), parade_boots),
            (os.path.join(SFX, 'parade_tanks.wav'), parade_tanks), (os.path.join(SFX, 'parade_jets.wav'), parade_jets),
            (os.path.join(SFX, 'parade_pa_chime.wav'), parade_pa_chime)]
    for path, fn in jobs:
        x = fn()
        info = write_wav(path, x)
        print(os.path.basename(path), '%.2f s' % (len(x) / SR), info)


if __name__ == '__main__':
    main()
