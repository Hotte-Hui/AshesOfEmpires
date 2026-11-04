"""foley.py -- physically-inspired generators shared by the SFX and the ambience loops.

Footsteps (grain clouds through stone / snow / heel resonators), paper (crackle + swish),
wood and metal impacts (modal), stick-slip creaks, the Berlin tram gong, a distant locomotive
horn, buffer-bump chains, wind (STFT noise with gust-driven spectra), a passing tram and an
UNINTELLIGIBLE formant "announcement" babble (random vowel formants on a glottal pulse train --
no recorded or synthesised words, no language).
All generators take an np.random.Generator so every asset is deterministic.
"""
from __future__ import annotations

import numpy as np

from dsp import (SR, TAU, secs, eq, fftconv, place, pan2, smoothstep, rms, stft_noise, stft_filter,
                 smooth_periodic, make_ir, resonators, soft_clip, db2a, to_stereo, fade, filt)
from instruments import (modal, impact, random_modes, noise_burst, bell_modes, make_table, wt_read,
                         ctrl_noise, piano_note)


def norm_peak(x: np.ndarray, p: float = 1.0) -> np.ndarray:
    m = float(np.max(np.abs(x)))
    return x * (p / m) if m > 0 else x


# =========================================================================== rooms
def ir_archive(seed: int = 900) -> np.ndarray:
    return make_ir(length=1.4, rt_low=0.85, rt_high=0.45, predelay=0.006, er_taps=16, er_span=0.035,
                   er_gain=0.45, seed=seed, lowcut=90, highcut=8000, build=0.004)


def ir_outdoor_far(seed: int = 901) -> np.ndarray:
    return make_ir(length=4.0, rt_low=2.4, rt_high=0.9, predelay=0.03, er_taps=6, er_span=0.09, er_gain=0.15,
                   seed=seed, lowcut=60, highcut=5000, build=0.03,
                   slap=[(0.31, 0.55, 2200), (0.57, 0.40, 1800), (0.93, 0.28, 1400), (1.42, 0.18, 1100),
                         (2.05, 0.10, 900)])


def ir_street(seed: int = 902) -> np.ndarray:
    return make_ir(length=3.0, rt_low=1.8, rt_high=0.8, predelay=0.02, er_taps=8, er_span=0.06, er_gain=0.25,
                   seed=seed, lowcut=60, highcut=6500, build=0.02,
                   slap=[(0.17, 0.45, 3000), (0.41, 0.35, 2200), (0.78, 0.22, 1600), (1.3, 0.12, 1200)])


def ir_small(seed: int = 903) -> np.ndarray:
    return make_ir(length=0.6, rt_low=0.35, rt_high=0.22, predelay=0.003, er_taps=10, er_span=0.02,
                   er_gain=0.5, seed=seed, lowcut=120, highcut=9000, build=0.002)


def in_room(x: np.ndarray, ir: np.ndarray, wet: float, tail: bool = True) -> np.ndarray:
    """One-shot through a room: stereo out, with tail."""
    xs = to_stereo(x if x.ndim == 2 else x)
    w = fftconv(xs, ir, circular=False, full=True)
    out = wet * w
    out[:xs.shape[0]] += xs
    return out if tail else out[:xs.shape[0]]


# =========================================================================== grains
def grain_cloud(rng: np.random.Generator, dur: float, rate_env: np.ndarray, f_lo: float, f_hi: float,
                t60_lo: float = 0.002, t60_hi: float = 0.008, n_res: int = 4, alpha: float = 1.6) -> np.ndarray:
    """Sparse random impulses (Poisson, rate_env per sample in Hz) with Pareto amplitudes, each
    subset driven through a different short resonator bank (stones / ice / fibres)."""
    n = secs(dur)
    p = np.clip(rate_env[:n] / SR, 0, 1)
    hits = rng.random(n) < p
    amps = (rng.pareto(alpha, n) + 1.0) ** -1.0 * rng.choice([-1.0, 1.0], n)
    amps *= np.sqrt(np.clip(rate_env[:n] / max(float(np.max(rate_env[:n])), 1e-9), 0.0, 1.0))
    imp = np.where(hits, amps, 0.0)
    out = np.zeros(n)
    which = rng.integers(0, n_res, n)
    for r in range(n_res):
        sub = np.where(which == r, imp, 0.0)
        if not sub.any():
            continue
        modes = []
        for _ in range(3):
            f = float(np.exp(rng.uniform(np.log(f_lo), np.log(f_hi))))
            modes.append((f, float(np.exp(rng.uniform(np.log(t60_lo), np.log(t60_hi)))), rng.uniform(0.5, 1.0)))
        out += resonators(sub, modes)
    return out


def bump(n: int, attack: float, decay: float, peak_at: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR - peak_at
    up = smoothstep((t + attack) / max(attack, 1e-4))
    down = np.exp(-np.maximum(t, 0) / max(decay, 1e-4))
    return up * down


# =========================================================================== footsteps
def footstep(rng: np.random.Generator, surface: str, weight: float = 1.0, creak: bool = False) -> np.ndarray:
    """One step (heel + roll + toe), mono, ~0.35-0.5 s."""
    dur = 0.5
    n = secs(dur)
    t = np.arange(n) / SR
    toe = rng.uniform(0.075, 0.11)
    out = np.zeros(n)
    if surface == 'gravel':
        rate = 2200 * bump(n, 0.004, 0.045) + 1100 * bump(n, 0.01, 0.05, peak_at=toe)
        g = grain_cloud(rng, dur, rate * weight, 900, 7000, 0.0015, 0.006)
        g /= max(rms(g[:secs(0.2)]), 1e-9)
        out += 0.30 * g
        out += 0.9 * norm_peak(modal([(rng.uniform(70, 95), 1.0, 0.07), (rng.uniform(150, 190), 0.4, 0.05)], dur,
                                    seed=int(rng.integers(1 << 30)), attack=0.004)) * 0.35
        out += 0.25 * norm_peak(noise_burst(dur, rng, 80, 600, 0.03, attack=0.002))
    elif surface == 'snow':
        rate = 1400 * bump(n, 0.03, 0.07, peak_at=0.03) + 900 * bump(n, 0.02, 0.06, peak_at=toe + 0.04)
        g = grain_cloud(rng, dur, rate * weight, 500, 3200, 0.002, 0.009, alpha=2.2)
        g /= max(rms(g[:secs(0.25)]), 1e-9)
        out += 0.30 * g
        # cold-snow squeak: stick-slip at ~1-1.6 kHz with drifting rate
        sq = creak_train(rng, 0.14, rng.uniform(900, 1200), rng.uniform(1300, 1700),
                         [(rng.uniform(1600, 2400), 0.006, 1.0), (rng.uniform(2800, 3600), 0.004, 0.5)], jitter=0.15)
        sq = norm_peak(sq) * bump(len(sq), 0.03, 0.05, peak_at=0.05)
        place(out, 0.10 * sq, secs(0.02), circular=False)
        out += 0.22 * norm_peak(noise_burst(dur, rng, 60, 400, 0.05, attack=0.01))
        out = eq(out, ('lp', 5500, 2), circular=False)
    elif surface == 'concrete':
        heel = impact(rng, [(rng.uniform(420, 520), 1.0, 0.035), (rng.uniform(900, 1100), 0.7, 0.028),
                            (rng.uniform(1700, 2100), 0.5, 0.02), (rng.uniform(2900, 3500), 0.35, 0.015),
                            (rng.uniform(150, 190), 0.6, 0.03)], 0.2, hard=0.75, noise_lo=800, noise_hi=9000,
                      noise_amt=0.6, noise_decay=0.004)
        out[:len(heel)] += heel
        toe_hit = impact(rng, [(rng.uniform(600, 750), 1.0, 0.025), (rng.uniform(1300, 1600), 0.6, 0.02),
                               (rng.uniform(2500, 3000), 0.4, 0.012)], 0.12, hard=0.5, noise_lo=1000,
                         noise_hi=8000, noise_amt=0.5, noise_decay=0.003)
        place(out, 0.45 * toe_hit, secs(toe), circular=False)
        scuff = noise_burst(0.07, rng, 1500, 6500, 0.035, attack=0.01)
        place(out, 0.07 * norm_peak(scuff), secs(toe + 0.01), circular=False)
        out = in_room(out, ir_small(int(rng.integers(1 << 20))), 0.10, tail=False).mean(axis=1)
    elif surface == 'wood':
        boards = [(rng.uniform(110, 140), 1.0, 0.12), (rng.uniform(230, 280), 0.7, 0.09),
                  (rng.uniform(420, 520), 0.5, 0.07), (rng.uniform(800, 950), 0.3, 0.05),
                  (rng.uniform(1500, 1800), 0.2, 0.03)]
        heel = impact(rng, boards, 0.35, hard=0.45, noise_lo=300, noise_hi=6000, noise_amt=0.35,
                      noise_decay=0.006)
        out[:len(heel)] += heel
        toe_hit = impact(rng, boards, 0.25, hard=0.35, noise_lo=400, noise_hi=5000, noise_amt=0.3, noise_decay=0.005)
        place(out, 0.4 * toe_hit, secs(toe), circular=False)
        if creak:
            c = creak_train(rng, 0.22, rng.uniform(140, 180), rng.uniform(210, 260),
                            [(rng.uniform(420, 520), 0.03, 1.0), (rng.uniform(900, 1100), 0.02, 0.6),
                             (rng.uniform(1700, 2000), 0.012, 0.3)], jitter=0.25)
            c = norm_peak(c) * bump(len(c), 0.05, 0.08, peak_at=0.08)
            place(out, 0.16 * c, secs(toe + 0.02), circular=False)
        out = in_room(out, ir_small(int(rng.integers(1 << 20))), 0.12, tail=False).mean(axis=1)
    else:
        raise ValueError(surface)
    rel = toe + (0.16 if surface in ('gravel', 'snow') else 0.22)
    out *= np.where(t < rel, 1.0, np.exp(-(t - rel) / 0.035))
    out = fade(out, 0.0, 0.08)
    return out


# =========================================================================== creak / stick-slip
def creak_train(rng: np.random.Generator, dur: float, rate0: float, rate1: float, modes, jitter: float = 0.2) -> np.ndarray:
    """Stick-slip: impulse train whose rate glides rate0->rate1 (with jitter) through resonators."""
    n = secs(dur)
    r = np.linspace(rate0, rate1, n) * (1.0 + jitter * ctrl_noise(n, 25.0, rng) * 0.5)
    ph = np.cumsum(np.maximum(r, 1.0)) / SR
    k = np.floor(ph)
    imp = np.zeros(n)
    idx = np.nonzero(np.diff(k, prepend=k[0]) > 0)[0]
    imp[idx] = rng.uniform(0.4, 1.0, len(idx))
    return resonators(imp, modes)


# =========================================================================== metal
def metal_clank(rng: np.random.Generator, kind: str) -> np.ndarray:
    if kind == 'light':
        modes = random_modes(rng, 420, 6200, 12, 0.08, 0.45, tilt=0.35)
        y = impact(rng, modes, 1.4, hard=0.7, noise_lo=1500, noise_hi=10000, noise_amt=0.35, noise_decay=0.004)
        y2 = impact(rng, random_modes(rng, 500, 5000, 8, 0.05, 0.3), 1.0, hard=0.5, noise_amt=0.3)
        place(y, 0.35 * y2, secs(rng.uniform(0.07, 0.12)), circular=False)
    elif kind == 'heavy':
        modes = random_modes(rng, 85, 2600, 14, 0.25, 1.4, tilt=0.45)
        y = impact(rng, modes, 2.2, hard=0.45, noise_lo=150, noise_hi=5000, noise_amt=0.4, noise_decay=0.01)
        n = len(y)
        t = np.arange(n) / SR
        thud = np.sin(TAU * rng.uniform(48, 60) * t) * np.exp(-t / 0.09) * smoothstep(t / 0.003)
        y += 0.7 * thud
    elif kind == 'ring':        # shares the tram-gong partials -> match-cut bridge to the Berlin bell
        modes = [(f, a * 0.55, T * 0.8) for (f, a, T) in bell_modes(820.0, 'tram')]
        modes += random_modes(rng, 140, 1600, 8, 0.08, 0.4, tilt=0.4)
        y = impact(rng, modes, 2.8, hard=0.5, noise_lo=300, noise_hi=7000, noise_amt=0.35, noise_decay=0.006)
    else:
        raise ValueError(kind)
    return fade(norm_peak(y), 0.0, 0.1)


def tram_bell(rng: np.random.Generator, strikes: int = 2, f1: float = 820.0, gap: float = 0.24,
              dur: float = 3.4) -> np.ndarray:
    """Foot-gong of a tram: dome-bell partials, two clapper strikes ('ding-ding')."""
    n = secs(dur)
    out = np.zeros(n)
    modes = bell_modes(f1, 'tram')
    for i in range(strikes):
        ms = [(f * (1 + rng.normal(0, 0.0004)), a * rng.uniform(0.85, 1.0), T) for (f, a, T) in modes]
        y = modal(ms, dur - i * gap, seed=int(rng.integers(1 << 30)), attack=0.0004)
        click = noise_burst(0.008, rng, 2000, 10000, 0.0025)
        y[:len(click)] += 0.25 * norm_peak(click)
        place(out, y * (1.0 if i == 0 else 0.82), secs(i * gap), circular=False)
    # mount rattle, very faint
    rat = noise_burst(0.12, rng, 600, 3500, 0.06)
    out[:len(rat)] += 0.02 * norm_peak(rat)
    return fade(norm_peak(out), 0.0, 0.3)


# =========================================================================== wood / desk
def wood_knock(rng: np.random.Generator, f0: float = 120.0, dur: float = 0.6, hard: float = 0.4) -> np.ndarray:
    modes = [(f0 * r * rng.uniform(0.97, 1.03), a, T) for (r, a, T) in
             [(1.0, 1.0, 0.16), (1.95, 0.7, 0.12), (3.4, 0.5, 0.09), (5.8, 0.35, 0.06), (9.6, 0.2, 0.04)]]
    return impact(rng, modes, dur, hard=hard, noise_lo=200, noise_hi=5000, noise_amt=0.3, noise_decay=0.008)


def stamp(rng: np.random.Generator) -> np.ndarray:
    dur = 0.9
    n = secs(dur)
    desk = wood_knock(rng, 112.0, dur, hard=0.35)
    y = 1.0 * desk
    slap = noise_burst(0.05, rng, 200, 2600, 0.02, attack=0.0008)
    y[:len(slap)] += 0.55 * norm_peak(slap)
    handle = modal([(1650, 0.6, 0.03), (2480, 0.4, 0.022), (3900, 0.2, 0.015)], 0.1, seed=int(rng.integers(1 << 30)))
    y[:len(handle)] += 0.18 * handle
    t = np.arange(n) / SR
    y += 0.35 * np.sin(TAU * 62 * t) * np.exp(-t / 0.05) * smoothstep(t / 0.002)
    tack = noise_burst(0.01, rng, 2000, 7000, 0.003)
    place(y, 0.05 * norm_peak(tack), secs(0.16), circular=False)
    return norm_peak(y)


# =========================================================================== paper
def paper_rustle(rng: np.random.Generator, dur: float = 1.0, intensity: float = 0.6, gestures: int = 3) -> np.ndarray:
    n = secs(dur)
    env = np.zeros(n)
    for _ in range(gestures):
        c = rng.uniform(0.25 * dur, 0.75 * dur)
        w = rng.uniform(0.12, 0.3) * min(1.0, dur / 0.6)
        t = np.arange(n) / SR
        env += rng.uniform(0.5, 1.0) * np.exp(-0.5 * ((t - c) / (w / 2.5)) ** 2)
    env /= env.max()
    rate = (700 + 2600 * intensity) * env ** 1.5
    cr = grain_cloud(rng, dur, rate, 1800, 8500, 0.0008, 0.003, n_res=6, alpha=1.8)
    cr /= max(rms(cr), 1e-9)
    sw = noise_burst(dur, rng, 1200, 7000, 1e6, attack=0.0)
    sw = sw / max(rms(sw), 1e-9) * env
    y = 0.55 * cr * np.sqrt(env + 0.05) + 0.42 * sw
    y = eq(y, ('hp', 600, 2), ('lp', 9000, 2), circular=False)
    return fade(norm_peak(y), 0.01, 0.05)


def page_turn(rng: np.random.Generator) -> np.ndarray:
    dur = 0.85
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    lift = paper_rustle(rng, 0.18, 0.4, 1)
    y[:len(lift)] += 0.4 * lift
    # flip swoosh with rising band and flutter
    a, b = 0.12, 0.55
    m = (t >= a) & (t < b)
    tt = (t[m] - a) / (b - a)
    z = rng.standard_normal(m.sum())
    sw = stft_filter(np.pad(z, (0, (-len(z)) % 441)), lambda tc, f: (
        np.exp(-0.5 * ((np.log2(np.maximum(f[None, :], 20) / (1200 + 2600 * np.clip(tc[:, None] / ((b - a)), 0, 1))) / 0.9) ** 2))),
        nfft=1764, hop=441)[:m.sum()]
    flutter = 1.0 + 0.5 * np.sin(TAU * (26 - 10 * tt) * tt * (b - a)) * (1 - tt)
    sw = sw / max(rms(sw), 1e-9) * np.sin(np.pi * tt) ** 1.3 * flutter
    y[m] += 0.35 * sw
    land = noise_burst(0.04, rng, 150, 3000, 0.012, attack=0.001)
    place(y, 0.6 * norm_peak(land), secs(0.56), circular=False)
    th = np.sin(TAU * 180 * t[:secs(0.05)]) * np.exp(-t[:secs(0.05)] / 0.012)
    place(y, 0.2 * th, secs(0.56), circular=False)
    return fade(norm_peak(y), 0.005, 0.08)


def card_place(rng: np.random.Generator, heavy: float = 0.5) -> np.ndarray:
    dur = 0.4
    n = secs(dur)
    y = np.zeros(n)
    slide = noise_burst(0.09, rng, 1500, 6000, 0.08, attack=0.03)
    y[:len(slide)] += 0.12 * norm_peak(slide)
    tap = noise_burst(0.03, rng, 250, 5000, 0.006, attack=0.0006)
    place(y, 0.8 * norm_peak(tap), secs(0.08), circular=False)
    t = np.arange(secs(0.06)) / SR
    th = np.sin(TAU * rng.uniform(150, 200) * t) * np.exp(-t / 0.014)
    place(y, (0.3 + 0.3 * heavy) * th, secs(0.08), circular=False)
    return fade(norm_peak(y), 0.0, 0.05)


# =========================================================================== door / drawer
def door_open(rng: np.random.Generator) -> np.ndarray:
    dur = 1.6
    n = secs(dur)
    y = np.zeros(n)
    latch = impact(rng, random_modes(rng, 1800, 7000, 8, 0.02, 0.06), 0.15, hard=0.8, noise_amt=0.5,
                   noise_decay=0.002)
    y[:len(latch)] += 0.5 * latch
    spring = impact(rng, random_modes(rng, 1200, 5000, 6, 0.02, 0.05), 0.12, hard=0.6, noise_amt=0.4)
    place(y, 0.3 * spring, secs(0.06), circular=False)
    cr = creak_train(rng, 0.8, 70, 140, [(rng.uniform(560, 640), 0.05, 1.0), (rng.uniform(1050, 1200), 0.035, 0.6),
                                        (rng.uniform(1800, 2100), 0.02, 0.35), (rng.uniform(320, 380), 0.06, 0.4)],
                     jitter=0.35)
    cr = norm_peak(cr) * bump(len(cr), 0.15, 0.3, peak_at=0.3)
    place(y, 0.32 * cr, secs(0.18), circular=False)
    air = noise_burst(1.0, rng, 60, 500, 0.6, attack=0.4)
    place(y, 0.12 * norm_peak(air), secs(0.2), circular=False)
    body = wood_knock(rng, 95.0, 0.4, hard=0.2)
    place(y, 0.25 * body, secs(0.02), circular=False)
    y = in_room(y, ir_archive(int(rng.integers(1 << 20))), 0.18, tail=False).mean(axis=1)
    return fade(norm_peak(y), 0.0, 0.25)


def drawer_slide(rng: np.random.Generator) -> np.ndarray:
    dur = 1.0
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    a, b = 0.02, 0.62
    env = np.where((t > a) & (t < b), np.sin(np.pi * np.clip((t - a) / (b - a), 0, 1)) ** 0.7, 0.0)
    fr = noise_burst(dur, rng, 250, 2600, 1e6, attack=0.0)
    rough = 1.0 + 0.45 * ctrl_noise(n, 45.0, rng)
    y += 0.3 * norm_peak(fr) * env * rough
    rate = 25.0 * env
    clicks = grain_cloud(rng, dur, rate, 1500, 4500, 0.002, 0.006, n_res=2)
    y += 0.25 * norm_peak(clicks)
    stop = wood_knock(rng, 150.0, 0.35, hard=0.45)
    place(y, 0.75 * stop, secs(b - 0.01), circular=False)
    y = in_room(y, ir_archive(int(rng.integers(1 << 20))), 0.15, tail=False).mean(axis=1)
    return fade(norm_peak(y), 0.0, 0.1)


# =========================================================================== UI / text
def ui_tick(rng: np.random.Generator, f: float = 2400.0, dur: float = 0.07, body: float = 0.4) -> np.ndarray:
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.sin(TAU * f * t) * np.exp(-t / 0.012) + body * np.sin(TAU * f * 0.5 * t) * np.exp(-t / 0.02)
    click = noise_burst(0.004, rng, 1500, 7000, 0.0012)
    y[:len(click)] += 0.35 * norm_peak(click)
    y *= smoothstep(t / 0.0006)
    return fade(norm_peak(y), 0.0, 0.02)


def type_tick(rng: np.random.Generator, pitch: float = 1.0) -> np.ndarray:
    dur = 0.06
    modes = [(1250 * pitch, 0.6, 0.012), (2300 * pitch, 1.0, 0.009), (3700 * pitch, 0.5, 0.006),
             (520 * pitch, 0.35, 0.015)]
    y = impact(rng, modes, dur, hard=0.55, noise_lo=1500, noise_hi=7000, noise_amt=0.3, noise_decay=0.0015)
    y = eq(y, ('lp', 7000, 2), circular=False)
    return fade(norm_peak(y), 0.0, 0.015)


# =========================================================================== horn / shunting
def horn(rng: np.random.Generator, f0: float, dur: float, chord: tuple = (1.0,), wobble: float = 0.004) -> np.ndarray:
    """Locomotive air horn (typhon) tone, dry, mono.  chord = frequency ratios of extra bells."""
    n = secs(dur + 0.6)
    t = np.arange(n) / SR
    env = smoothstep(t / 0.18) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.12))
    out = np.zeros(n)
    for j, r in enumerate(chord):
        f = f0 * r
        K = int(min(24, 9000 / f))
        k = np.arange(1, K + 1)
        fk = k * f
        amps = k ** -0.9 * (1 + 1.6 * np.exp(-0.5 * (np.log2(fk / 750) / 0.6) ** 2)) * (1 + 0.8 * np.exp(-0.5 * (np.log2(fk / 1700) / 0.4) ** 2))
        tab = make_table(amps)
        bend = -0.035 * np.exp(-t / 0.12) - 0.03 * smoothstep((t - dur + 0.05) / 0.25)
        fl = f * (1 + bend + wobble * ctrl_noise(n, 4.0, rng))
        ph = np.cumsum(fl) / SR + rng.random()
        out += wt_read(tab, ph) / (j + 1) ** 0.3
    breath = noise_burst(dur + 0.6, rng, 300, 3000, 1e6, attack=0.0)
    out = out / max(np.max(np.abs(out)), 1e-9) + 0.04 * breath / max(np.max(np.abs(breath)), 1e-9)
    return out * env


def far_horn(rng: np.random.Generator, f0: float, dur: float, chord=(1.0,), ir=None) -> np.ndarray:
    """Horn heard across a city: low-passed, wind-modulated, through facade echoes (stereo)."""
    h = horn(rng, f0, dur, chord)
    n = len(h)
    h *= 1.0 + 0.25 * ctrl_noise(n, 1.5, rng)
    h = eq(h, ('hp', 150, 2), ('lp', 1300, 2), circular=False)
    ir = ir if ir is not None else ir_outdoor_far(int(rng.integers(1 << 20)))
    st = pan2(h, rng.uniform(-0.4, 0.4))
    w = fftconv(st, ir, circular=False, full=True)
    out = 0.9 * w
    out[:n] += 0.35 * st
    return out


def buffer_bump(rng: np.random.Generator) -> np.ndarray:
    """One wagon buffer impact: heavy steel ring + low thud + coupling rattle (mono, dry)."""
    y = metal_clank(rng, 'heavy')
    if rng.random() < 0.7:
        r = metal_clank(rng, 'light')
        place(y, 0.25 * r, secs(rng.uniform(0.05, 0.15)), circular=False)
    return y


def shunting_chain(rng: np.random.Generator, bumps: int, spacing: float, decay: float = 0.75) -> np.ndarray:
    """Impact travelling down a line of wagons: bumps with growing distance (dry, mono)."""
    total = secs(spacing * bumps + 2.5)
    out = np.zeros(total)
    t = 0.0
    for i in range(bumps):
        b = buffer_bump(rng)
        b = eq(b, ('lp', 3000 * (0.75 ** i) + 500, 2), circular=False)
        place(out, b * (decay ** i), secs(t), circular=False)
        t += spacing * rng.uniform(0.75, 1.25)
    # rolling rumble under the chain
    rum = noise_burst(spacing * bumps + 1.5, rng, 30, 220, 1e6, attack=0.0)
    rn = len(rum)
    env = bump(rn, 0.3, spacing * bumps * 0.5, peak_at=0.4)
    out[:rn] += 0.12 * norm_peak(rum) * env
    return out


# =========================================================================== wind
def wind(n: int, rng: np.random.Generator, gust: np.ndarray, lp_base: float = 350.0, lp_gust: float = 1400.0,
         whistle: float = 0.0, whistle_f: tuple = (520.0, 900.0), hush: float = 0.0, corr: float = 0.35,
         pan_sweep: float = 0.25, hp: float = 40.0, tilt: float = -0.5) -> np.ndarray:
    """Periodic stereo wind with gust-driven level and brightness (STFT noise).  gust: (n,) in ~[0, 1.5]."""
    hop, nfft = 441, 1764
    assert n % hop == 0
    F = n // hop
    gi = gust[(np.arange(F) * hop + nfft // 2) % n]
    sweep = smooth_periodic(n, max(3, n // SR // 6), rng)[(np.arange(F) * hop + nfft // 2) % n]

    def G(tc, f):
        fc = lp_base + lp_gust * np.clip(gi, 0, 1.6)[:, None]
        lf = np.maximum(f[None, :], 15.0)
        base = (lf / 100.0) ** tilt / np.sqrt(1 + (lf / fc) ** 3) / np.sqrt(1 + (hp / lf) ** 4)
        mag = base * (0.15 + gi[:, None]) ** 1.1
        if whistle > 0:
            fw = whistle_f[0] + (whistle_f[1] - whistle_f[0]) * np.clip(gi, 0, 1.4)[:, None] / 1.4
            pk = np.exp(-0.5 * ((lf - fw) / (fw * 0.035)) ** 2) + 0.5 * np.exp(-0.5 * ((lf - 2.02 * fw) / (fw * 0.06)) ** 2)
            mag = mag + whistle * pk * np.clip(gi - 0.45, 0, None)[:, None] ** 1.6 * base.max(axis=1, keepdims=True)
        if hush > 0:
            hb = np.exp(-0.5 * (np.log2(lf / 5200.0) / 0.9) ** 2)
            mag = mag + hush * hb * (0.5 + 0.5 * np.clip(gi, 0, 1.4))[:, None]
        L = mag * (1.0 + pan_sweep * sweep)[:, None]
        R = mag * (1.0 - pan_sweep * sweep)[:, None]
        return np.stack([L, R], axis=2)
    return stft_noise(n, G, rng, ch=2, nfft=nfft, hop=hop, corr=corr)


def gust_curve(n: int, rng: np.random.Generator, events, base: float = 0.35, turb: float = 0.08,
               turb_rate: float = 0.6) -> np.ndarray:
    """Periodic gust envelope.  events: [(time_s, strength, rise_s, fall_s)]."""
    g = np.zeros(n)
    for (t0, s, rise, fall) in events:
        m = secs(rise + 5 * fall)
        tt = np.arange(m) / SR
        shape = np.where(tt < rise, smoothstep(tt / rise), np.exp(-(tt - rise) / fall))
        place(g, s * shape, secs(t0), circular=True)
    tb = smooth_periodic(n, int(n / SR * turb_rate), rng)
    return np.clip(base + g + turb * tb, 0.02, None)


# =========================================================================== tram pass (exterior)
def tram_pass(rng: np.random.Generator, dur: float = 16.0, closest: float = 8.0, dist: float = 1.0) -> np.ndarray:
    """A tram passing at a distance: wheel rumble, rail-joint clacks, motor whine, wire hiss; stereo."""
    n = secs(dur)
    t = np.arange(n) / SR
    prox = 1.0 / (1.0 + ((t - closest) / (2.6 * dist)) ** 2)            # 0..1 proximity
    pan = np.tanh((t - closest) / (2.5 * dist)) * 0.8
    rum = noise_burst(dur, rng, 35, 500, 1e6, attack=0.0)
    rum = norm_peak(rum) * (0.6 + 0.4 * ctrl_noise(n, 3.0, rng) * 0.3)
    y = 0.5 * rum * prox ** 1.2
    # rail-joint clacks (pairs of axles)
    tc = 0.6
    while tc < dur - 0.5:
        for off in (0.0, 0.11):
            k = impact(rng, random_modes(rng, 180, 2600, 8, 0.03, 0.15), 0.3, hard=0.4, noise_amt=0.4)
            place(y, 0.22 * k * float(np.interp(tc + off, t, prox)) ** 1.5, secs(tc + off), circular=False)
        tc += rng.uniform(0.95, 1.15)
    # motor whine with doppler
    v = 0.012 * np.tanh(-(t - closest) / 1.5)
    f = 340.0 * (1 + v) * (1 + 0.15 * smoothstep((t - 2.0) / 10.0))
    ph = np.cumsum(f) / SR
    wh = np.sin(TAU * ph) + 0.4 * np.sin(TAU * 2 * ph) + 0.2 * np.sin(TAU * 3.01 * ph)
    y += 0.05 * wh * prox ** 2
    hiss = noise_burst(dur, rng, 2500, 7000, 1e6, attack=0.0)
    y += 0.03 * norm_peak(hiss) * prox ** 6
    y = eq(y, ('lp', 2500, 2), circular=False)
    return pan2(y, pan)


# =========================================================================== formant babble
VOWELS = [(730, 1090, 2440), (530, 1840, 2480), (270, 2290, 3010), (570, 840, 2410), (300, 870, 2240),
          (500, 1500, 2500), (660, 1720, 2410), (400, 1600, 2300)]


def babble(rng: np.random.Generator, dur: float, f0: float = 120.0, rate: float = 4.8, pause=(0.45, 1.1),
           phrase=(1.5, 3.2)) -> np.ndarray:
    """Speech-LIKE prosody without any language: random vowel formant targets on a glottal pulse
    train, fricative/plosive noise at syllable onsets, phrase declination.  Unintelligible by
    construction (no phoneme sequence corresponds to words).  Mono, dry."""
    n = secs(dur)
    n = n + (-n) % 441
    ctrl = int(n / SR * 200) + 2
    tt = np.arange(ctrl) / 200.0
    amp = np.zeros(ctrl); nz = np.zeros(ctrl); pitch = np.ones(ctrl)
    F = np.zeros((ctrl, 3)); F[:] = VOWELS[5]
    t = 0.15
    while t < dur - 0.5:
        L = rng.uniform(*phrase)
        end = min(dur - 0.3, t + L)
        s = t
        k = 0
        while s < end:
            d = rng.uniform(0.11, 0.26)
            v = VOWELS[rng.integers(len(VOWELS))]
            stress = rng.random() < 0.3
            i0, i1 = int(s * 200), int(min(end, s + d) * 200)
            if i1 <= i0 + 2:
                break
            seg = np.arange(i0, i1)
            u = (seg - i0) / max(1, (i1 - i0))
            linked = rng.random() < 0.3                       # some syllables run together (no closure)
            a = np.sin(np.pi * np.clip(u * 1.1, 0, 1)) ** (0.45 if linked else 0.9)
            amp[seg] = np.maximum(amp[seg], a * (1.0 if stress else 0.72))
            on = seg[u < 0.22]
            if rng.random() < 0.55:
                nz[on] = rng.uniform(0.3, 0.8)
            # intonation: phrase declination, accent bump on stressed syllables, final fall
            decl = 1.12 - 0.20 * (s - t) / max(L, 1e-3)
            acc = 0.09 * np.sin(np.pi * u) if stress else 0.015 * np.sin(np.pi * u)
            fall = -0.10 * smoothstep((u - 0.3) / 0.7) if s + d >= end else 0.0
            pitch[seg] = decl * (1.0 + acc + fall)
            F[seg] = np.array(v) * rng.uniform(0.95, 1.05)
            s += d
            k += 1
        t = end + rng.uniform(*pause)
    # smooth control curves (coarticulation)
    def sm(x, w=6):
        kern = np.ones(w) / w
        if x.ndim == 1:
            return np.convolve(np.pad(x, (w, w), mode='edge'), kern, mode='same')[w:-w]
        return np.stack([sm(x[:, j], w) for j in range(x.shape[1])], axis=1)
    amp = sm(amp, 5); nz = sm(nz, 3); pitch = sm(pitch, 16); F = sm(F, 10)
    ts = np.arange(n) / SR
    A = np.interp(ts, tt, amp); NZ = np.interp(ts, tt, nz); P = np.interp(ts, tt, pitch)
    f0t = f0 * P * (1 + 0.01 * ctrl_noise(n, 5.0, rng))
    K = int(7000 / (f0 * 1.3))
    k = np.arange(1, K + 1)
    tab = make_table(k ** -1.0 * (1 / (1 + (k * f0 / 2500.0) ** 2)))
    voiced = wt_read(tab, np.cumsum(f0t) / SR) * A
    noise = rng.standard_normal(n) * NZ * 0.35          # fricatives sit where voicing is low
    src = voiced + noise
    hop, nfft = 441, 1764
    fr_idx = np.minimum(((np.arange(n // hop) * hop + nfft // 2) / (SR / 200.0)).astype(int), ctrl - 1)
    Ff = F[fr_idx]

    def G(tc, f):
        lf = f[None, :]
        g = np.zeros((len(tc), len(f)))
        for j, bw in enumerate((90.0, 120.0, 170.0)):
            fc = Ff[:len(tc), j][:, None]
            g += (1.0 / (j + 1)) / (1.0 + ((lf - fc) / (bw / 2)) ** 2)
        return g + 0.02
    y = stft_filter(src, G, nfft=nfft, hop=hop)
    return y[:secs(dur)]


def loudspeaker(x: np.ndarray, rng: np.random.Generator, drive: float = 2.2) -> np.ndarray:
    """1960s horn PA: narrow band, a little cone/horn distortion."""
    y = eq(x, ('hp', 380, 3), ('lp', 3200, 3), ('bell', 1500, 4.0, 1.0), circular=False)
    y = soft_clip(norm_peak(y) * 0.9, drive)
    return eq(y, ('hp', 300, 2), ('lp', 3800, 2), circular=False)
