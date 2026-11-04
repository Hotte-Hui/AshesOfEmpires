"""ambience.py -- 60 s seamless stereo ambience loops (synthesised, original).

Seamlessness by construction: beds are periodic FFT/STFT noise, modulators are periodic smooth
curves, every event is placed on a circular timeline, reverbs are circular convolutions and
tonal components use whole numbers of cycles per loop.  Target level ~ -24 dBFS RMS.

amb_karsk_yard      cold wind + gusts/whistle, snow hush, distant shunting chains (buffer bumps),
                    two far locomotive horns (~25-35 s apart), metallic creaks, a far muffled
                    station announcement (formant babble, no language), low industrial rumble.
amb_berlin_archive  room tone, wall clock (60 ticks), radiator ticks + gurgle, muffled tram
                    (rumble + gong) and cars through the windows, paper at other desks, a faint
                    typewriter in another room.
amb_berlin_street   urban wind, catenary wire singing + electrical hum, a passing tram with its
                    gong, distant hall loudspeakers (unintelligible babble with facade echoes).
amb_transition      low airy drone on D with a faint bowed-metal shimmer (tram-gong partials:
                    the "metal timbre" bridge between Karsk and Berlin from the scene atlas).
"""
from __future__ import annotations

import numpy as np

from dsp import (SR, TAU, secs, eq, fftconv, place, pan2, smooth_periodic, shaped_noise, mag_bp, mag_lp,
                 mag_hp, mag_tilt, rms, db2a, normalize_rms, remove_dc, limiter, to_stereo, smoothstep)
from instruments import ctrl_noise, impact, random_modes, noise_burst, modal
from foley import (wind, gust_curve, shunting_chain, far_horn, creak_train, babble, loudspeaker,
                   ir_outdoor_far, ir_archive, ir_street, tram_pass, tram_bell, paper_rustle, norm_peak,
                   metal_clank, bump, type_tick)

LOOP = 60.0
N = secs(LOOP)            # 2 646 000 samples (multiple of the 441-sample STFT hop)


# ----------------------------------------------------------------------------- helpers
def active_rms(x: np.ndarray, floor_db: float = -30.0) -> float:
    m = np.mean(np.atleast_2d(x.T).T ** 2, axis=1) if x.ndim == 2 else x ** 2
    win = secs(0.1)
    c = np.concatenate([[0.0], np.cumsum(m)])
    st = (c[win:] - c[:-win]) / win if len(m) > win else np.array([m.mean()])
    thr = st.max() * 10 ** (floor_db / 10)
    a = st[st > thr]
    return float(np.sqrt(a.mean())) if a.size else float(np.sqrt(m.mean()))


class Mix:
    """Circular stereo mix with levels relative to a reference bed RMS (dB)."""

    def __init__(self, n: int = N):
        self.n = n
        self.buf = np.zeros((n, 2))

    def bed(self, x: np.ndarray, rel_db: float) -> None:
        x = to_stereo(x)
        self.buf += x * (db2a(rel_db) / max(rms(x), 1e-12))

    def event(self, x: np.ndarray, t: float, rel_db: float, mode: str = 'rms') -> None:
        """mode 'rms': active RMS of the event = rel_db; 'peak': peak = rel_db (re bed RMS 1.0)."""
        x = to_stereo(x)
        ref = active_rms(x) if mode == 'rms' else float(np.max(np.abs(x)))
        place(self.buf, x * (db2a(rel_db) / max(ref, 1e-12)), secs(t), circular=True)

    def master(self, target: float = -24.0, lp: float = 14000.0) -> np.ndarray:
        y = eq(self.buf, ('hp', 22, 2), ('lp', lp, 2), circular=True)
        y = remove_dc(y, circular=True)
        y = normalize_rms(y, target)
        return limiter(y, -3.0, circular=True)


def distant(x: np.ndarray, rng: np.random.Generator, lp: float, ir: np.ndarray, wet: float, dry: float,
            pan: float = 0.0) -> np.ndarray:
    """Mono dry event -> far stereo event (lowpass, pan, room/outdoor IR, tail kept)."""
    y = eq(x, ('lp', lp, 2), circular=False) if lp else x
    st = pan2(y, pan)
    w = fftconv(st, ir, circular=False, full=True)
    out = wet * w
    out[:st.shape[0]] += dry * st
    return out


def periodic_tone(n: int, f_hz: float, rng: np.random.Generator, fm: np.ndarray | None = None) -> np.ndarray:
    """Sine with a whole number of cycles per loop (optionally frequency-modulated by fm, a
    relative deviation curve), so phase is continuous across the seam."""
    inst = f_hz * (1.0 + (fm if fm is not None else 0.0))
    total = np.sum(inst) / SR
    inst = inst * (max(1.0, np.round(total)) / total)
    ph = np.cumsum(inst) / SR
    ph -= ph[-1]                      # ph[-1] is an integer -> 0 ; continuous wrap
    return np.sin(TAU * ph + rng.uniform(0, TAU))


# ----------------------------------------------------------------------------- karsk yard
def amb_karsk_yard():
    rng = np.random.default_rng(1101)
    M = Mix()
    gust = gust_curve(N, rng, [(3.5, 0.75, 1.6, 2.6), (12.5, 0.5, 2.2, 3.2), (20.5, 0.95, 1.3, 2.4),
                               (30.5, 0.4, 2.6, 3.6), (37.5, 0.85, 1.5, 2.9), (46.5, 0.6, 2.0, 3.0),
                               (53.5, 0.45, 1.8, 2.6)], base=0.34, turb=0.09, turb_rate=0.7)
    w = wind(N, rng, gust, lp_base=330.0, lp_gust=1500.0, whistle=0.22, whistle_f=(470.0, 820.0), corr=0.3,
             hp=75.0, tilt=-0.3)
    M.bed(w, 0.0)
    hush = shaped_noise(N, rng, lambda f: mag_bp(f, 2400.0, 9000.0, 2), ch=2, corr=0.1)
    hmod = 0.55 + 0.45 * np.clip(gust / gust.max(), 0, 1)
    M.bed(hush * hmod[:, None], -19.0)
    rumble = shaped_noise(N, rng, lambda f: mag_bp(f, 28.0, 140.0, 2), ch=2, corr=0.7)
    rumble *= (1.0 + 0.3 * smooth_periodic(N, 6, rng))[:, None]
    M.bed(rumble, -16.0)
    far = ir_outdoor_far(1102)
    # shunting: buffer-bump chains travelling down the wagons
    for (t, bumps, sp, pan, lvl) in [(7.5, 3, 0.55, -0.35, 1.0), (25.8, 5, 0.42, 0.25, 2.0),
                                     (43.6, 2, 0.7, -0.15, -1.0)]:
        ch = shunting_chain(rng, bumps, sp)
        M.event(distant(ch, rng, 3200.0, far, 1.0, 0.5, pan), t, lvl)
    M.event(distant(metal_clank(rng, 'light'), rng, 3500.0, far, 1.0, 0.45, 0.5), 52.4, -4.0)
    # far horns
    M.event(far_horn(rng, 311.0, 2.3, (1.0,), ir=far), 9.0, -2.0)
    h2 = far_horn(rng, 262.0, 1.2, (1.0, 1.19), ir=far)
    h3 = far_horn(rng, 262.0, 0.55, (1.0, 1.19), ir=far)
    M.event(h2, 34.4, -3.0)
    M.event(h3, 36.1, -6.0)
    # metallic creaks (wagons, a crane hook)
    for (t, d, r0, r1, pan) in [(16.2, 0.9, 38, 75, 0.45), (29.6, 1.3, 55, 30, -0.5), (41.0, 0.7, 60, 110, 0.2),
                                (57.2, 1.0, 45, 80, -0.25)]:
        modes = [(rng.uniform(280, 380), 0.08, 1.0), (rng.uniform(700, 900), 0.06, 0.7),
                 (rng.uniform(1300, 1700), 0.04, 0.5), (rng.uniform(2300, 2900), 0.03, 0.25)]
        c = creak_train(rng, d, r0, r1, modes, jitter=0.3) * bump(secs(d), d * 0.3, d * 0.35, peak_at=d * 0.35)
        M.event(distant(c, rng, 3000.0, far, 0.7, 0.6, pan), t, -13.0)
    # far station announcement (unintelligible, muffled, echoing)
    pa = loudspeaker(babble(rng, 4.6, f0=112.0), rng)
    M.event(distant(pa, rng, 1700.0, far, 1.3, 0.25, 0.3), 47.2, -3.0)
    out = M.master(-24.0, lp=12000.0)
    return out, (0, N)


# ----------------------------------------------------------------------------- berlin archive
def clock_tick(rng: np.random.Generator, tock: bool) -> np.ndarray:
    k = 0.9 if tock else 1.0
    modes = [(1850 * k, 1.0, 0.03), (2950 * k, 0.6, 0.022), (4350 * k, 0.35, 0.014), (760 * k, 0.4, 0.05),
             (1230 * k, 0.3, 0.04)]
    y = impact(rng, modes, 0.18, hard=0.8, noise_lo=2000, noise_hi=9000, noise_amt=0.25, noise_decay=0.0012)
    return y


def amb_berlin_archive():
    rng = np.random.default_rng(2201)
    M = Mix()
    room = shaped_noise(N, rng, lambda f: mag_tilt(f, -4.5, 100.0) * mag_bp(f, 35.0, 700.0, 2)
                        + 0.015 * mag_bp(f, 3000.0, 7000.0, 2), ch=2, corr=0.55)
    M.bed(room, 0.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 30.0, 260.0, 2), ch=2, corr=0.8)
    city *= (1.0 + 0.35 * smooth_periodic(N, 8, rng))[:, None]
    M.bed(city, -6.0)
    room_ir = ir_archive(2202)
    # wall clock: 60 ticks per loop (1 Hz), tick/tock alternate, on the left wall
    ticks = np.zeros(N)
    for i in range(60):
        place(ticks, clock_tick(np.random.default_rng(2300 + i % 6), i % 2 == 1) * (1.0 if i % 2 == 0 else 0.86),
              secs(i * 1.0 + 0.25), circular=True)
    tk = pan2(ticks, -0.45)
    tk = tk + 0.35 * fftconv(tk, room_ir, circular=True)
    M.buf += tk * (db2a(21.0) / float(np.max(np.abs(tk))))
    # radiator ticks (thermal) + one gurgle
    for (t, pk) in [(3.1, 12.0), (3.42, 9.0), (11.8, 11.0), (19.2, 13.0), (19.47, 10.0), (19.66, 8.5),
                    (33.0, 11.0), (44.7, 12.0), (52.3, 10.0)]:
        tink = impact(rng, random_modes(rng, 1500, 5200, 6, 0.015, 0.06), 0.15, hard=0.7, noise_amt=0.3)
        M.event(distant(tink, rng, 0, room_ir, 0.3, 1.0, 0.55), t, pk, mode='peak')
    gur = np.zeros(secs(2.4))
    tt = 0.05
    while tt < 2.2:
        f = rng.uniform(220, 520)
        L = secs(rng.uniform(0.03, 0.07))
        tb = np.arange(L) / SR
        bub = np.sin(TAU * np.cumsum(f * (1 + 0.6 * tb / tb[-1])) / SR) * np.exp(-tb / 0.02)
        place(gur, bub * rng.uniform(0.3, 1.0), secs(tt), circular=False)
        tt += rng.exponential(0.09)
    gur = eq(gur, ('lp', 1500, 2), circular=False)
    M.event(distant(gur, rng, 0, room_ir, 0.35, 1.0, 0.55), 27.0, 0.0)
    # outside through closed windows: tram rumble + its gong, two cars
    tp = tram_pass(rng, 14.0, 7.0, dist=2.0)
    tp = eq(tp, ('lp', 650, 3), circular=False)
    M.event(tp + 0.4 * fftconv(tp, room_ir, circular=False), 18.0, -1.0)
    bell = tram_bell(rng, 2, 820.0)
    bell = eq(bell, ('lp', 950, 3), ('hp', 250, 2), circular=False)
    M.event(distant(bell, rng, 0, room_ir, 0.6, 1.0, 0.35), 24.3, 11.0, mode='peak')
    for (t, d, pan) in [(5.0, 7.0, -0.3), (40.0, 6.0, 0.35)]:
        car = noise_burst(d, rng, 35.0, 420.0, 1e6, attack=0.0)
        n = len(car)
        car = car * bump(n, d * 0.45, d * 0.18, peak_at=d * 0.5)
        M.event(pan2(car, np.linspace(pan, -pan, n)), t, -3.0)
    # paper at other desks
    for (t, d, pan) in [(14.5, 1.0, -0.2), (37.0, 0.8, 0.3), (55.0, 1.2, 0.1)]:
        p = paper_rustle(rng, d, 0.5, 3)
        M.event(distant(p, rng, 6000.0, room_ir, 0.4, 1.0, pan), t, 15.0, mode='peak')
    # faint typewriter in another room
    tw = np.zeros(secs(3.4))
    tt = 0.05
    for i in range(15):
        k = type_tick(rng, rng.uniform(0.75, 0.95))
        place(tw, k * rng.uniform(0.6, 1.0), secs(tt), circular=False)
        tt += rng.uniform(0.11, 0.2) if rng.random() > 0.15 else rng.uniform(0.3, 0.45)
    ret = impact(rng, random_modes(rng, 300, 2400, 8, 0.05, 0.2), 0.4, hard=0.4)
    place(tw, 0.8 * ret, secs(tt + 0.25), circular=False)
    tw = eq(tw, ('lp', 1400, 3), circular=False)
    M.event(distant(tw, rng, 0, room_ir, 0.8, 0.5, -0.6), 48.5, 8.0, mode='peak')
    out = M.master(-25.0, lp=11000.0)
    return out, (0, N)


# ----------------------------------------------------------------------------- berlin street
def amb_berlin_street():
    rng = np.random.default_rng(3301)
    M = Mix()
    gust = gust_curve(N, rng, [(5.0, 0.45, 2.5, 3.5), (18.0, 0.55, 2.0, 3.0), (33.0, 0.4, 3.0, 4.0),
                               (46.0, 0.6, 2.2, 3.2)], base=0.3, turb=0.07, turb_rate=0.5)
    w = wind(N, rng, gust, lp_base=280.0, lp_gust=1000.0, whistle=0.10, whistle_f=(640.0, 1000.0), corr=0.4,
             hp=75.0, tilt=-0.3)
    M.bed(w, 0.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 28.0, 240.0, 2), ch=2, corr=0.75)
    city *= (1.0 + 0.3 * smooth_periodic(N, 10, rng))[:, None]
    M.bed(city, -10.0)
    # catenary wires singing (aeolian, follows the wind) + faint electrical hum
    gn = (gust - gust.mean()) / (gust.std() + 1e-9)
    wires = np.zeros(N)
    for (f, a) in [(146.0, 1.0), (151.5, 0.8), (292.0, 0.25), (303.0, 0.2), (438.0, 0.08)]:
        wires += a * periodic_tone(N, f, rng, fm=0.025 * gn)
    wires *= np.clip(gust / gust.max(), 0, 1) ** 1.5
    M.bed(pan2(wires, 0.15), -11.0)
    hum = sum(a * periodic_tone(N, f, rng) for (f, a) in [(100.0, 1.0), (150.0, 0.5), (200.0, 0.35), (300.0, 0.2)])
    M.bed(pan2(hum, -0.1), -26.0)
    sir = ir_street(3302)
    tp = tram_pass(rng, 16.0, 8.5, dist=1.3)
    M.event(tp + 0.35 * fftconv(tp, sir, circular=False), 19.0, 1.0)
    bell = tram_bell(rng, 2, 820.0)
    M.event(distant(bell, rng, 4500.0, sir, 0.5, 1.0, -0.1), 25.2, 10.0, mode='peak')
    # distant loudspeakers from the hall: phrases with long facade echoes, unintelligible
    for (t, d, seed_off) in [(4.0, 6.5, 1), (35.5, 12.0, 2)]:
        b = loudspeaker(babble(np.random.default_rng(3400 + seed_off), d, f0=104.0), rng, drive=2.6)
        M.event(distant(b, rng, 1900.0, sir, 1.4, 0.22, 0.35), t, -2.0)
    out = M.master(-24.0, lp=12000.0)
    return out, (0, N)


# ----------------------------------------------------------------------------- transition
def amb_transition():
    rng = np.random.default_rng(4401)
    M = Mix()
    air = shaped_noise(N, rng, lambda f: mag_tilt(f, -2.0, 200.0) * mag_bp(f, 90.0, 650.0, 2), ch=2, corr=0.3)
    breath = 0.6 + 0.4 * (0.5 + 0.5 * np.sin(TAU * 3 * np.arange(N) / N + 0.7)) \
        + 0.1 * smooth_periodic(N, 9, rng)
    M.bed(air * breath[:, None], -2.0)
    hi = shaped_noise(N, rng, lambda f: mag_bp(f, 2500.0, 8000.0, 2), ch=2, corr=0.1)
    hb = 0.5 + 0.5 * np.sin(TAU * 2 * np.arange(N) / N + 2.1)
    M.bed(hi * hb[:, None], -19.0)
    drone = np.zeros((N, 2))
    t = np.arange(N) / N
    for (f, a, p) in [(73.4, 1.0, -0.2), (73.5, 0.8, 0.2), (110.0, 0.55, -0.35), (110.1, 0.45, 0.35),
                      (146.833, 0.35, 0.0), (36.7, 0.5, 0.0)]:
        sw = 0.65 + 0.35 * np.sin(TAU * (1 + (f % 3 == 0)) * t + rng.uniform(0, TAU))
        drone += pan2(periodic_tone(N, f, rng) * sw * a, p)
    M.bed(drone, 1.0)
    # faint bowed-metal shimmer on the tram-gong partials (820 Hz family)
    sh = np.zeros((N, 2))
    for (r, a) in [(1.0, 1.0), (1.51, 0.6), (2.13, 0.4)]:
        env = np.clip(np.sin(TAU * 1 * t + rng.uniform(0, TAU)), 0, None) ** 3
        sh += pan2(periodic_tone(N, 820.0 * r, rng, fm=0.0006 * smooth_periodic(N, 12, rng)) * env * a,
                   rng.uniform(-0.5, 0.5))
    M.bed(sh, -20.0)
    out = M.master(-24.0, lp=10000.0)
    return out, (0, N)


TRACKS = {
    'amb_karsk_yard': amb_karsk_yard,
    'amb_berlin_archive': amb_berlin_archive,
    'amb_berlin_street': amb_berlin_street,
    'amb_transition': amb_transition,
}
