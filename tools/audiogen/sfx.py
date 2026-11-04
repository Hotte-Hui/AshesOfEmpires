"""sfx.py -- one-shot sound effects (and the 10 s fire loop).  All synthesised, original.

Every builder returns a list [(file_name, signal, loop)] (variants) or (signal, loop).
Peak targets are <= -6 dBFS (TECHNICAL_ARCHITECTURE §7 / audio brief); mono unless the sound is
inherently spatial (horn, gust, fire, musical cues).
"""
from __future__ import annotations

import numpy as np

from dsp import (SR, TAU, secs, eq, fftconv, place, pan2, normalize_peak, rms, fade, to_stereo,
                 shaped_noise, mag_bp, smooth_periodic, limiter, remove_dc, stft_noise, db2a, smoothstep)
from instruments import (piano_note, celesta_note, string_note, impact, random_modes, noise_burst, modal)
from foley import (footstep, paper_rustle, page_turn, stamp, metal_clank, tram_bell, door_open, drawer_slide,
                   card_place, ui_tick, type_tick, far_horn, wind, gust_curve, norm_peak, ir_archive, in_room,
                   grain_cloud, bump, make_ir)


def _fin(x: np.ndarray, peak_db: float, tail_fade: float = 0.02) -> np.ndarray:
    """Trim trailing silence (< -80 dBFS after scaling), fade, DC-free, set the peak."""
    x = np.asarray(x, dtype=float)
    x = eq(x, ('lp', 11000.0, 4), ('hp', 30.0, 2), circular=False)   # no harsh top, no rumble
    x = x - np.mean(x, axis=0)
    x = normalize_peak(x, peak_db)
    a = np.max(np.abs(np.atleast_2d(x.T).T), axis=1) if x.ndim == 2 else np.abs(x)
    above = np.nonzero(a > 10 ** (-80 / 20))[0]
    end = min(len(x), (above[-1] + secs(0.03)) if above.size else len(x))
    x = x[:end]
    x = fade(x, 0.0, min(tail_fade, len(x) / SR / 4))
    return normalize_peak(x, peak_db)


def variants(base: str, count: int, fn, peak_db: float):
    out = []
    for i in range(count):
        rng = np.random.default_rng(abs(hash_str(base)) + 97 * i)
        out.append((f'{base}_{i + 1}', _fin(fn(rng, i), peak_db), None))
    return out


def hash_str(s: str) -> int:
    h = 2166136261
    for ch in s.encode():
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


# ----------------------------------------------------------------------------- footsteps
def step_gravel():
    return variants('step_gravel', 4, lambda r, i: footstep(r, 'gravel', weight=0.85 + 0.1 * i), -12.0)


def step_snow():
    return variants('step_snow', 4, lambda r, i: footstep(r, 'snow', weight=0.9 + 0.07 * i), -13.0)


def step_concrete():
    return variants('step_concrete', 4, lambda r, i: footstep(r, 'concrete'), -12.0)


def step_wood():
    return variants('step_wood', 4, lambda r, i: footstep(r, 'wood', creak=(i == 2)), -12.0)


# ----------------------------------------------------------------------------- paper / desk
def paper():
    return variants('paper_rustle', 3, lambda r, i: paper_rustle(r, [0.9, 1.2, 0.7][i], [0.55, 0.7, 0.45][i],
                                                                     [3, 4, 2][i]), -14.0)


def pages():
    return variants('page_turn', 2, lambda r, i: page_turn(r), -14.0)


def stamp_thud():
    rng = np.random.default_rng(5101)
    y = stamp(rng)
    y = in_room(y, ir_archive(5102), 0.12, tail=True).mean(axis=1)
    return [('stamp_thud', _fin(y, -6.0, 0.05), None)]


def cards():
    return variants('card_place', 2, lambda r, i: card_place(r, heavy=0.3 + 0.4 * i), -14.0)


def door():
    return [('door_open', _fin(door_open(np.random.default_rng(5201)), -10.0, 0.1), None)]


def drawer():
    return [('drawer_slide', _fin(drawer_slide(np.random.default_rng(5301)), -11.0, 0.08), None)]


# ----------------------------------------------------------------------------- metal / bell
def clanks():
    kinds = ['light', 'heavy', 'ring']
    return variants('metal_clank', 3, lambda r, i: metal_clank(r, kinds[i]), -8.0)


def tram():
    y = tram_bell(np.random.default_rng(5401), 2, 820.0)
    return [('tram_bell', _fin(y, -9.0, 0.3), None)]


# ----------------------------------------------------------------------------- puzzle cues
def puzzle_success():
    """Subtle: celesta D5 -> A5 over a soft open fifth (strings), resolves to the 9th E5."""
    n = secs(3.6)
    y = np.zeros((n, 2))
    place(y, celesta_note(74, 0.5, seed=1, pan=0.1), 0, circular=False)
    place(y, celesta_note(81, 0.45, seed=2, pan=0.15), secs(0.16), circular=False)
    place(y, celesta_note(76, 0.32, seed=3, pan=0.2), secs(0.42), circular=False)
    place(y, piano_note(62, 0.32, hold=1.2, felt=0.8, seed=4, pan=-0.1), secs(0.02), circular=False)
    s = string_note(50, 1.3, vel=0.30, attack=0.35, release=1.2, seed=5, bright=0.4) + \
        string_note(57, 1.3, vel=0.26, attack=0.4, release=1.2, seed=6, bright=0.4)
    place(y, 0.6 * s, 0, circular=False)
    ir = make_ir(2.6, 2.0, 1.0, predelay=0.02, seed=5501, highcut=7000)
    w = fftconv(y, ir, circular=False)
    y = y + 0.28 * w
    y = eq(y, ('hp', 80, 2), ('lp', 9000, 2), circular=False)
    return [('puzzle_success', _fin(y, -10.0, 0.6), None)]


def puzzle_fail():
    """Soft, non-punishing: two muted piano notes stepping down (F4 -> E4), a wooden 'tock'."""
    n = secs(1.6)
    y = np.zeros((n, 2))
    place(y, piano_note(65, 0.36, hold=0.18, felt=1.0, seed=7, decay=0.5), 0, circular=False)
    place(y, piano_note(64, 0.32, hold=0.5, felt=1.0, seed=8, decay=0.5), secs(0.17), circular=False)
    rng = np.random.default_rng(5601)
    knock = impact(rng, [(210, 1.0, 0.06), (470, 0.6, 0.04), (980, 0.3, 0.025)], 0.2, hard=0.3, noise_amt=0.15)
    place(y, pan2(0.25 * knock, 0.0), 0, circular=False)
    ir = make_ir(1.6, 1.0, 0.6, predelay=0.01, seed=5602, highcut=6000)
    y = y + 0.2 * fftconv(y, ir, circular=False)
    y = eq(y, ('hp', 90, 2), ('lp', 5000, 2), circular=False)
    return [('puzzle_fail', _fin(y, -14.0, 0.3), None)]


# ----------------------------------------------------------------------------- UI
def ui():
    rng = np.random.default_rng(5701)
    mv = ui_tick(rng, 2350.0, 0.07, body=0.3)
    mv = eq(mv, ('hp', 400, 2), ('lp', 7000, 2), circular=False)
    sel = piano_note(74, 0.5, hold=0.12, felt=0.9, seed=11, decay=0.4)[:, 0] * 1.4
    sel[:secs(0.07)] += 0.35 * ui_tick(rng, 2600.0, 0.07, body=0.2)[:secs(0.07)]
    sel = in_room(sel, make_ir(0.9, 0.5, 0.3, predelay=0.004, seed=5702), 0.12, tail=True).mean(axis=1)
    bk = piano_note(67, 0.42, hold=0.1, felt=1.0, seed=12, decay=0.35)[:, 0] * 1.4
    bk[:secs(0.05)] += 0.25 * ui_tick(rng, 1800.0, 0.05, body=0.4)[:secs(0.05)]
    bk = in_room(bk, make_ir(0.9, 0.5, 0.3, predelay=0.004, seed=5703), 0.12, tail=True).mean(axis=1)
    return [('ui_move', _fin(mv, -20.0, 0.01), None), ('ui_select', _fin(sel, -15.0, 0.05), None),
            ('ui_back', _fin(bk, -17.0, 0.05), None)]


def type_ticks():
    pitches = [1.0, 1.08, 0.93]
    return variants('type_tick', 3, lambda r, i: type_tick(r, pitches[i]), -22.0)


# ----------------------------------------------------------------------------- outdoor one-shots
def train_horn():
    rng = np.random.default_rng(5801)
    y = far_horn(rng, 311.0, 2.2, (1.0,))
    return [('train_horn_far', _fin(y, -12.0, 0.5), None)]


def gust():
    rng = np.random.default_rng(5901)
    n = secs(4.41)          # multiple of the STFT hop
    g = gust_curve(n, rng, [(0.35, 1.1, 1.4, 0.7)], base=0.0, turb=0.06, turb_rate=3.0)
    g *= np.sin(np.pi * np.arange(n) / n) ** 0.8            # zero at both ends (one-shot)
    y = wind(n, rng, g, lp_base=280.0, lp_gust=1500.0, whistle=0.2, whistle_f=(500.0, 850.0), corr=0.25,
             pan_sweep=0.5)
    return [('wind_gust', _fin(fade(y, 0.05, 0.4), -12.0, 0.3), None)]


def fire_loop():
    """10 s seamless fire-barrel loop: low roar + hiss + crackles/pops (circular)."""
    rng = np.random.default_rng(6001)
    n = secs(10.0)
    roar = shaped_noise(n, rng, lambda f: mag_bp(f, 40.0, 320.0, 2), ch=2, corr=0.6)
    roar *= (1.0 + 0.35 * smooth_periodic(n, 30, rng))[:, None]
    hiss = shaped_noise(n, rng, lambda f: mag_bp(f, 1500.0, 6000.0, 2), ch=2, corr=0.3)
    hiss *= (0.6 + 0.4 * smooth_periodic(n, 50, rng) ** 2)[:, None]
    y = 0.5 * roar / rms(roar) + 0.08 * hiss / rms(hiss)
    # crackles: many small, a few big pops with a tiny resonance
    t = 0.0
    while t < 10.0:
        big = rng.random() < 0.12
        if big:
            ev = impact(rng, random_modes(rng, 700, 4500, 5, 0.006, 0.03), 0.08, hard=0.8, noise_amt=0.8,
                        noise_decay=0.004)
            amp = rng.uniform(1.5, 3.0)
        else:
            ev = noise_burst(rng.uniform(0.002, 0.008), rng, 1200, 9000, rng.uniform(0.0008, 0.003), attack=0.0002)
            ev = norm_peak(ev)
            amp = rng.uniform(0.2, 1.0) ** 2 * 1.4
        place(y, pan2(ev * amp, rng.uniform(-0.3, 0.3)), secs(t), circular=True)
        t += rng.exponential(1.0 / 9.0)
    y = eq(y, ('hp', 35, 2), ('lp', 9000, 2), circular=True)
    y = remove_dc(y, circular=True)
    y = normalize_peak(y, -8.0)
    y = limiter(y, -8.0, circular=True)
    return [('fire_crackle_loop', y, (0, n))]


SOUNDS = {
    'step_gravel': step_gravel, 'step_snow': step_snow, 'step_concrete': step_concrete, 'step_wood': step_wood,
    'paper_rustle': paper, 'page_turn': pages, 'stamp_thud': stamp_thud, 'metal_clank': clanks,
    'tram_bell': tram, 'door_open': door, 'drawer_slide': drawer, 'card_place': cards,
    'puzzle_success': puzzle_success, 'puzzle_fail': puzzle_fail, 'ui': ui, 'type_tick': type_ticks,
    'train_horn_far': train_horn, 'wind_gust': gust, 'fire_crackle_loop': fire_loop,
}
