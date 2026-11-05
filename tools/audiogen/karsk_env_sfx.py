"""karsk_env_sfx -- one-shot sounds for the Karsk ambient actors (area env_karsk, round 2).

    py -3 -P tools/audiogen/karsk_env_sfx.py        -> assets/audio/sfx/karsk_*.wav (44.1 kHz, 16-bit)

  karsk_crow_caw_1..3   hooded crow 'kraa' calls (outdoor, distant facades)      Audio.sfx("karsk_crow_caw")
  karsk_crow_flap       a few crows taking off: wing whumps + feather rustle      KarskCrows
  karsk_cat_mrrp        soft rising trill of the cat by the barrel                KarskCat
  karsk_train_far       goods train on the far track (~20 s): rumble swell,       KarskTrain
                        steam chuffs, rail-joint clacks, a far whistle
  karsk_wind_gust_1..2  short gust (~3.6 s, stereo)                               KarskWind
  karsk_lamp_buzz       tired lamp: mains buzz stutter + relay tick                KarskLamp

Everything is synthesised from noise and oscillators with the shared toolkit (dsp.py, instruments.py,
foley.py are used read-only).  Deterministic: seeds from zlib.crc32 of the sound name.  Original work.
"""
from __future__ import annotations

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

from dsp import (SR, secs, eq, fftconv, place, pan2, normalize_peak, fade, smoothstep, write_wav,  # noqa: E402
                 to_stereo, peak_db, rms_db, make_ir)
from instruments import ctrl_noise, noise_burst, make_table, wt_read  # noqa: E402
from foley import far_horn, wind, gust_curve, norm_peak, ir_outdoor_far, metal_clank, bump  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')


def rng_for(name: str, k: int = 0) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode()) + 7919 * k)


def finish(x: np.ndarray, peak: float, fade_out: float = 0.05) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = eq(x, ('lp', 11000.0, 4), ('hp', 28.0, 2), circular=False)
    x = x - np.mean(x, axis=0)
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    m = a.max() if a.size else 0.0
    if m > 0:
        above = np.nonzero(a > m * 10 ** (-70 / 20))[0]
        x = x[:min(len(x), above[-1] + secs(0.03))]
    x = fade(x, 0.004, min(fade_out, len(x) / SR / 4))
    return normalize_peak(x, peak)


def ir_yard(seed: int) -> np.ndarray:
    """Open railway yard between low buildings: short, dry-ish space with two soft facade slaps."""
    return make_ir(length=1.6, rt_low=1.1, rt_high=0.5, predelay=0.015, er_taps=5, er_span=0.06, er_gain=0.2,
                   seed=seed, lowcut=120, highcut=6000, build=0.02, slap=[(0.21, 0.25, 2500), (0.46, 0.12, 1800)])


def outdoor(x: np.ndarray, rng, wet: float = 0.45, pan: float = 0.0, near: bool = False) -> np.ndarray:
    ir = ir_yard(int(rng.integers(1 << 20))) if near else ir_outdoor_far(int(rng.integers(1 << 20)))
    st = pan2(x, pan)
    w = fftconv(st, ir, circular=False, full=True)
    out = wet * w
    out[:len(st)] += (1.0 - wet * 0.5) * st
    return out


# ----------------------------------------------------------------------------- crows
def caw(rng, f0=640.0, dur=0.32, rasp=0.7) -> np.ndarray:
    """One hooded-crow 'kraa': nasal harmonic tone with a falling pitch, rough AM and breath noise."""
    n = secs(dur + 0.08)
    t = np.arange(n) / SR
    env = smoothstep(t / 0.018) * np.where(t < dur * 0.7, 1.0, np.exp(-(t - dur * 0.7) / 0.05))
    f = f0 * (1.0 + 0.08 * np.exp(-t / 0.05) - 0.12 * (t / dur) + 0.012 * ctrl_noise(n, 30.0, rng))
    K = int(9000 / f0)
    k = np.arange(1, K + 1)
    fk = k * f0
    amps = k ** -0.6 * (1 + 2.2 * np.exp(-0.5 * (np.log2(fk / 1300) / 0.45) ** 2)
                        + 1.4 * np.exp(-0.5 * (np.log2(fk / 2600) / 0.4) ** 2))
    tab = make_table(amps)
    ph = np.cumsum(f) / SR + rng.random()
    y = wt_read(tab, ph)
    am = 1.0 - rasp * 0.5 * (1 + np.sin(2 * np.pi * rng.uniform(70, 105) * t + rng.random() * 6.28))
    y = y * am
    nz = noise_burst(dur + 0.08, rng, 900, 4200, 1e6, attack=0.0)
    y = y / max(np.max(np.abs(y)), 1e-9) + 0.22 * nz / max(np.max(np.abs(nz)), 1e-9)
    return y * env


def crow_caws():
    out = []
    for i in range(3):
        r = rng_for('karsk_crow_caw', i)
        calls = [1, 2, 3][i]
        x = np.zeros(secs(1.6))
        tt = 0.02
        for c in range(calls):
            y = caw(r, f0=r.uniform(560, 700) * (0.97 ** c), dur=r.uniform(0.24, 0.36), rasp=r.uniform(0.5, 0.85))
            place(x, y * (0.9 ** c), secs(tt), circular=False)
            tt += r.uniform(0.38, 0.5)
        x = eq(x, ('hp', 380, 2), ('lp', 6000, 2), circular=False)
        out.append(('karsk_crow_caw_%d' % (i + 1), finish(outdoor(x, r, 0.24, r.uniform(-0.3, 0.3), near=True), -9.0)))
    return out


def crow_flap():
    r = rng_for('karsk_crow_flap')
    dur = 1.9
    x = np.zeros(secs(dur))
    for bird in range(3):
        t0 = 0.04 + bird * r.uniform(0.12, 0.26)
        rate = r.uniform(5.5, 7.0)
        nfl = int(r.integers(6, 10))
        for k in range(nfl):
            tk = t0 + k / rate * r.uniform(0.9, 1.1)
            g = (0.95 ** k) * (1.0 if bird == 0 else 0.7)
            w = noise_burst(0.07, r, 160, 1700, 0.06, attack=0.008)
            w = eq(w, ('bell', 420, 6.0, 1.0), circular=False)
            place(x, g * w / max(np.max(np.abs(w)), 1e-9), secs(tk), circular=False)
            if r.random() < 0.6:   # feather rustle
                fr = noise_burst(0.05, r, 2500, 8000, 0.04, attack=0.003)
                place(x, 0.18 * g * fr / max(np.max(np.abs(fr)), 1e-9), secs(tk + 0.02), circular=False)
    x = x * np.linspace(1.0, 0.45, len(x))
    return [('karsk_crow_flap', finish(outdoor(x, r, 0.2, 0.1, near=True), -10.0))]


# ----------------------------------------------------------------------------- cat
def cat_mrrp():
    r = rng_for('karsk_cat_mrrp')
    dur = 0.42
    n = secs(dur + 0.1)
    t = np.arange(n) / SR
    f = 260.0 + 170.0 * smoothstep(t / dur) + 8.0 * ctrl_noise(n, 12.0, r)
    k = np.arange(1, 30)
    fk = k * 300.0
    amps = k ** -1.0 * (1 + 2.0 * np.exp(-0.5 * (np.log2(fk / 900) / 0.5) ** 2))
    y = wt_read(make_table(amps), np.cumsum(f) / SR)
    trill = 0.55 + 0.45 * np.sin(2 * np.pi * 26.0 * t) ** 2          # the rolled 'rr'
    env = smoothstep(t / 0.03) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.04))
    y = y * trill * env
    y = eq(y, ('hp', 180, 2), ('lp', 3200, 2), circular=False)
    br = noise_burst(dur, r, 600, 3000, 1e6, attack=0.02)
    y[:len(br)] += 0.05 * br / max(np.max(np.abs(br)), 1e-9) * env[:len(br)]
    return [('karsk_cat_mrrp', finish(to_stereo(y), -14.0))]


# ----------------------------------------------------------------------------- train
def train_far():
    r = rng_for('karsk_train_far')
    dur = 20.0
    n = secs(dur)
    t = np.arange(n) / SR
    prox = np.exp(-0.5 * ((t - 9.0) / 4.2) ** 2)                      # swell as it passes the gap
    rum = noise_burst(dur, r, 25, 260, 1e6, attack=0.0)
    rum = norm_peak(rum) * (0.75 + 0.25 * ctrl_noise(n, 2.0, r) * 0.4)
    y = 0.55 * rum * (0.25 + prox)
    # steam chuffs (4 per wheel turn) settling into rhythm
    tc = 0.6
    k = 0
    while tc < dur - 1.0:
        g = (0.25 + prox[secs(tc)]) * (1.0 if k % 4 == 0 else 0.7)
        ch = noise_burst(0.16, r, 120, 1100, 0.12, attack=0.01)
        place(y, 0.35 * g * ch / max(np.max(np.abs(ch)), 1e-9), secs(tc), circular=False)
        tc += 0.29 * r.uniform(0.95, 1.05)
        k += 1
    # rail-joint clacks: wheel pairs over joints
    tj = 1.2
    while tj < dur - 1.0:
        for d in (0.0, 0.09):
            cl = metal_clank(r, 'light')
            cl = eq(cl, ('lp', 2200, 2), circular=False)
            place(y, 0.12 * (0.2 + prox[secs(tj + d)]) * cl / max(np.max(np.abs(cl)), 1e-9), secs(tj + d),
                  circular=False)
        tj += r.uniform(0.75, 0.95)
    # far whistle early on (two-tone), across the town
    wh = far_horn(r, 392.0, 1.4, chord=(1.0, 1.19))
    wh = wh.mean(axis=1) if wh.ndim == 2 else wh
    place(y, 0.45 * wh / max(np.max(np.abs(wh)), 1e-9), secs(2.2), circular=False)
    y = eq(y, ('hp', 30, 2), ('lp', 1800, 2), circular=False)
    y = y * smoothstep(t / 2.5) * smoothstep((dur - t) / 3.0)
    return [('karsk_train_far', finish(outdoor(y, r, 0.5, 0.0), -10.0, fade_out=1.5))]


# ----------------------------------------------------------------------------- wind gust
def wind_gusts():
    out = []
    for i in range(2):
        r = rng_for('karsk_wind_gust', i)
        dur = 4.41
        n = secs(dur)
        g = gust_curve(n, r, [(0.3, 1.1 + 0.2 * i, 0.7, 0.7)], base=0.08, turb=0.12, turb_rate=2.0)
        x = wind(n, r, g, lp_base=260.0, lp_gust=1700.0, whistle=0.25 if i else 0.0, hush=0.4)
        env = smoothstep(np.arange(n) / SR / 0.4) * smoothstep((dur - np.arange(n) / SR) / 1.2)
        x = x * env[:, None]
        out.append(('karsk_wind_gust_%d' % (i + 1), finish(x, -11.0, fade_out=0.6)))
    return out


# ----------------------------------------------------------------------------- lamp buzz
def lamp_buzz():
    r = rng_for('karsk_lamp_buzz')
    dur = 0.7
    n = secs(dur)
    t = np.arange(n) / SR
    k = np.arange(1, 40)
    amps = k ** -0.7 * (k % 2 == 0)
    amps[0] = 0.3
    y = wt_read(make_table(amps), 50.0 * t)                            # 100 Hz buzz (even harmonics)
    gate = (np.sin(2 * np.pi * 7.0 * t + r.random()) > -0.2).astype(float)
    gate = eq(gate, ('lp', 80, 2), circular=False)
    y = y * gate * smoothstep(t / 0.02) * smoothstep((dur - t) / 0.12)
    tick = metal_clank(r, 'light')
    tick = eq(tick, ('hp', 1500, 2), circular=False)
    place(y, 0.3 * tick[:secs(0.05)] / max(np.max(np.abs(tick)), 1e-9), secs(0.01), circular=False)
    y = eq(y, ('hp', 90, 2), ('lp', 5000, 2), circular=False)
    return [('karsk_lamp_buzz', finish(to_stereo(y), -16.0))]


def build():
    os.makedirs(OUT, exist_ok=True)
    made = []
    for fn in (crow_caws, crow_flap, cat_mrrp, train_far, wind_gusts, lamp_buzz):
        for name, x in fn():
            path = os.path.join(OUT, name + '.wav')
            st = write_wav(path, x)
            made.append((name, len(x) / SR, peak_db(x), rms_db(x), st['clipped_samples']))
    for (name, d, p, rm, cl) in made:
        print('%-22s %5.2fs  peak %6.1f dBFS  rms %6.1f dBFS  clipped %d' % (name, d, p, rm, cl))
    return made


if __name__ == '__main__':
    build()
