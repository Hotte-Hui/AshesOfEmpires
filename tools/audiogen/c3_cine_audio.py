"""c3_cine_audio -- original synthesised sound for the three Chapter-3 cinematics (owner: cinematics stream).

Self-contained numpy synthesis (reuses tools/audiogen/dsp.py for the WAV writer and generated impulse
responses; nothing is sampled or downloaded), deterministic (seeds = crc32 of the sound's name),
44.1 kHz / 16-bit.  Writes assets/audio/sfx/c3cine_*.wav.  Levels follow the existing SFX (peaks -3..-12 dBFS).

  LS_C3_Trains (beds are cut to the picture: their rail joints land on the visual jolts of the car)
    c3cine_ride_de        the German saloon car at night: soft rumble, padded joints ta-tam every 1.55 s,
                          the wind at the glass, the panelling creaking                       stereo 9.6 s
    c3cine_ride_su        the Soviet car: harder joints every 1.8 s, loose fittings rattling, the spoon
                          clinking in the tea glass on every knock                            stereo 9.4 s
    c3cine_pass           a lineside lamp post rushing past the window                        stereo 1.2 s
    c3cine_crossing       a floodlit level crossing at speed: its bell swells and drops in pitch, the rush
                          of air (the match cut)                                              stereo 2.4 s
    c3cine_bridge         dawn: two engines on the stone bridge, exhaust beats from both sides slowing, the
                          hollow rumble of the arches, the wheel clatter, the river valley    stereo 13.2 s
    c3cine_whistle_de     Konrad's engine answering, lower and farther than the Karsk whistle stereo 3.0 s
    c3cine_station_rush   (round 10) a small station rushing past the saloon car: platform echo, its bell,
                          three lamps                                                         stereo 2.8 s
    c3cine_truss          (round 10) the truss bridge over the frozen river under the Soviet car stereo 3.0 s
    c3cine_line_night     (round 10) the Line before dawn: wind, floodlight hum, two trains far off stereo 7.2 s
    c3cine_city_morning   (round 10) the waking city at dawn: two bells, a tram, crows        stereo 5.8 s
  LS_C3_ToHall
    c3cine_clock_tick     the seconds of the platform clock, under the canopy                 stereo 0.6 s
    c3cine_clock_clack    the minute hand jumping to 9:40 (railway clock), iron and echo     stereo 1.2 s
    c3cine_palais_chime   one soft strike of the palais clock's gong spring                   stereo 3.0 s
    c3cine_step_marble_1..3  leather heels on the marble of the foyer                         stereo 0.8 s
  LS_C3_Close
    c3cine_depart_night   the special train pulling out without a whistle: hiss, couplings, heavy beats
                          receding into the night                                             stereo 6.5 s
    c3cine_flaps          the split-flap indicator clearing its row                           stereo 1.0 s

Run:  py -3 -P tools/audiogen/c3_cine_audio.py      (then the shared --import, see TECHNICAL_ARCHITECTURE §1)
"""
from __future__ import annotations

import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsp  # noqa: E402

SR = dsp.SR
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')

# rail joints of the two cars, relative to each bed's start (must equal JOINT in ch3_trains.gd:
#   K: 0.3 + n * 1.55 from t = 0;  A: 9.4 + n * 1.8 from t = 9.0 -> 0.4 + n * 1.8 in the file)
JOINT_DE = (0.30, 1.55)
JOINT_SU = (0.40, 1.80)
# round 10: the bridge bed starts at 23.1 s of LS_C3_Trains, the trains meet over the middle arch at 28.1 s
BRIDGE_MEET = 28.1 - 23.1
KNOCK_GAP = 0.16


def rng(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF)


def n_of(sec: float) -> int:
    return int(round(sec * SR))


def t_axis(sec: float) -> np.ndarray:
    return np.arange(n_of(sec)) / SR


def band(x: np.ndarray, lo: float, hi: float, soft: float = 0.2) -> np.ndarray:
    """Zero-phase FFT band-pass with raised skirts (works on mono or (n, 2))."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    g = np.ones_like(f)
    if lo > 0:
        w = max(1.0, lo * soft)
        g *= np.clip((f - (lo - w)) / (2 * w), 0, 1)
    if hi < SR / 2:
        w = max(1.0, hi * soft)
        g *= np.clip(((hi + w) - f) / (2 * w), 0, 1)
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, x.shape[0], axis=0)


def lp(x, hi, soft=0.3):
    return band(x, 0, hi, soft)


def hp(x, lo, soft=0.3):
    return band(x, lo, SR / 2, soft)


def decay(n: int, tau: float, attack: float = 0.002) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(tau, 1e-4))


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0):
    i = n_of(at)
    if i >= buf.shape[0] or i + sig.shape[0] <= 0:
        return
    j0 = max(0, -i)
    i = max(0, i)
    m = min(buf.shape[0] - i, sig.shape[0] - j0)
    if buf.ndim == 2 and sig.ndim == 1:
        buf[i:i + m] += gain * sig[j0:j0 + m, None]
    else:
        buf[i:i + m] += gain * sig[j0:j0 + m]


def pan(x: np.ndarray, p) -> np.ndarray:
    """mono -> stereo, p in -1..1 (scalar or per-sample), equal power."""
    p = np.broadcast_to(np.asarray(p, float), x.shape)
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def fades(x: np.ndarray, fin: float, fout: float) -> np.ndarray:
    x = x.copy()
    n = x.shape[0]
    a, b = n_of(fin), n_of(fout)
    if a > 0:
        r = np.linspace(0, 1, a) ** 1.5
        x[:a] *= r[:, None] if x.ndim == 2 else r
    if b > 0:
        r = np.linspace(1, 0, b) ** 1.5
        x[n - b:] *= r[:, None] if x.ndim == 2 else r
    return x


def norm(x: np.ndarray, peak_db: float) -> np.ndarray:
    p = np.abs(x).max() + 1e-12
    return x / p * 10 ** (peak_db / 20)


def room(x: np.ndarray, name: str, length, rt_low, rt_high, wet, predelay=0.01, slap=None, er_gain=0.6):
    ir = dsp.make_ir(length=length, rt_low=rt_low, rt_high=rt_high, predelay=predelay,
                     seed=zlib.crc32(('ir' + name).encode()) & 0x7FFFFFFF, slap=slap, er_gain=er_gain)
    y = dsp.reverb(x, ir, wet=wet, dry=1.0, circular=False, tail=False)
    return y


def write(name: str, x: np.ndarray) -> dict:
    st = dsp.write_wav(os.path.join(OUT, name + '.wav'), np.clip(x, -1, 1),
                       seed=zlib.crc32(name.encode()) & 0x7FFF)
    return {'file': 'assets/audio/sfx/%s.wav' % name, 'seconds': round(x.shape[0] / SR, 2),
            'peak_db': round(20 * np.log10(np.abs(x).max() + 1e-12), 1), **st}


def brown(n: int, r: np.random.Generator) -> np.ndarray:
    w = r.standard_normal(n)
    b = np.cumsum(w)
    b = hp(b, 18.0)
    return b / (np.abs(b).max() + 1e-9)


# --------------------------------------------------------------------------- elements
def knock(r, weight=1.0, hard=0.3, body_hz=72.0):
    """One wheel over a rail joint as heard inside the car: a low thump and a short metallic tick."""
    n = n_of(0.35)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * body_hz * t * (1 - 0.25 * t)) * decay(n, 0.055, 0.003)
    thump += lp(r.standard_normal(n), 260) * decay(n, 0.03, 0.001) * 0.9
    tick = band(r.standard_normal(n), 1800, 5200) * decay(n, 0.006, 0.0005)
    return (thump * weight + tick * hard * weight) * 0.8


def clink(r, gain=1.0, base=3150.0):
    """A tea spoon knocking against the glass in a nickel holder: three inharmonic partials, fast decay."""
    n = n_of(0.3)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, (f, d, g) in enumerate(((base, 0.11, 1.0), (base * 1.52, 0.07, 0.6), (base * 2.31, 0.04, 0.35))):
        out += g * np.sin(2 * np.pi * f * (1 + r.uniform(-0.01, 0.01)) * t + r.uniform(0, 6.28)) * decay(n, d, 0.0004)
    return out * gain * 0.5


def chuff(r, size=1.0, dark=900.0):
    """One exhaust beat of a steam engine (a burst of steam through the chimney)."""
    n = n_of(0.5)
    env = decay(n, 0.11 * size, 0.012)
    x = lp(r.standard_normal(n), dark) * env
    x += lp(r.standard_normal(n), 220) * decay(n, 0.06, 0.006) * 0.8
    return x


def bell_strike(r, f0=1240.0, dur=0.24):
    n = n_of(dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, d, g in ((f0, 0.16, 1.0), (f0 * 1.73, 0.09, 0.5), (f0 * 2.74, 0.05, 0.3), (f0 * 4.1, 0.03, 0.15)):
        out += g * np.sin(2 * np.pi * f * t + r.uniform(0, 6.28)) * decay(n, d, 0.0006)
    return out


# --------------------------------------------------------------------------- the trains
def ride(name, sec, joint, rattle=0.0, spoon=False, body_hz=72.0, warmth=160.0, fin=0.6, fout=0.7):
    r = rng(name)
    n = n_of(sec)
    t = np.arange(n) / SR
    # rumble of the bogies through the floor, breathing with the track
    rum = lp(brown(n, r), warmth) * (0.75 + 0.25 * np.sin(2 * np.pi * t / 3.4 + 0.7))
    hiss = band(r.standard_normal(n), 700, 2600) * 0.05
    wind = band(r.standard_normal(n), 260, 1300) * (0.04 + 0.03 * np.sin(2 * np.pi * t / 5.1) ** 2)
    mono = rum * 0.55 + hiss + wind
    # the joints: two knocks per joint (front and rear bogie of the next car under us)
    tj = joint[0]
    k = 0
    while tj < sec - 0.1:
        g = 1.0 + 0.08 * np.sin(k * 1.7)
        place(mono, knock(r, 0.9 * g, hard=0.25 + rattle, body_hz=body_hz), tj)
        place(mono, knock(r, 0.75 * g, hard=0.2 + rattle, body_hz=body_hz * 1.04), tj + KNOCK_GAP)
        if spoon:
            place(mono, clink(r, 0.55), tj + 0.03)
            place(mono, clink(r, 0.32, 3300.0), tj + KNOCK_GAP + 0.03)
        tj += joint[1]
        k += 1
    if rattle > 0:
        # loose window fittings and the luggage rack: dense small clicks riding on the rumble
        clicks = np.zeros(n)
        tt = 0.0
        while tt < sec:
            tt += r.uniform(0.03, 0.11)
            place(clicks, band(r.standard_normal(n_of(0.01)), 1500, 4200) * r.uniform(0.2, 1.0), tt)
        mono += clicks * rattle * 0.25 * (0.6 + 0.4 * np.abs(rum) / (np.abs(rum).max() + 1e-9))
    # the panelling creaks twice (wood under strain)
    for c in range(2):
        at = r.uniform(1.0, sec - 2.0)
        m = n_of(0.5)
        cr = band(r.standard_normal(m), 380, 900) * np.sin(np.linspace(0, np.pi, m)) ** 2
        cr *= 0.5 + 0.5 * np.sin(2 * np.pi * 23 * np.arange(m) / SR)
        place(mono, cr * 0.12, at)
    st = np.stack([mono * 0.96, mono], 1)
    st[:, 0] += band(r.standard_normal(n), 300, 1100) * 0.015
    st = room(st, name, 0.5, 0.28, 0.12, 0.25)
    st = fades(st, fin, fout)
    return norm(st, -6.0)


def ride_de():
    return ride('c3cine_ride_de', 9.6, JOINT_DE, rattle=0.0, spoon=False, body_hz=66.0, warmth=150.0,
                fin=0.7, fout=0.75)


def ride_su():
    return ride('c3cine_ride_su', 9.4, JOINT_SU, rattle=0.55, spoon=True, body_hz=80.0, warmth=190.0,
                fin=0.12, fout=1.0)


def pass_lamp():
    r = rng('c3cine_pass')
    n = n_of(1.2)
    t = np.arange(n) / SR
    env = np.exp(-((t - 0.5) / 0.13) ** 2)
    x = r.standard_normal(n)
    lo = band(x, 400, 900) * np.clip(t / 0.5, 0, 1)
    hi = band(x, 1000, 2600) * np.clip(1 - t / 0.5, 0, 1)
    w = (lo + hi) * env * 0.7
    w += lp(r.standard_normal(n), 120) * np.exp(-((t - 0.5) / 0.05) ** 2) * 0.6     # the pressure pulse
    st = pan(w, np.clip((0.5 - t) * 1.6, -0.7, 0.7))
    return norm(fades(st, 0.02, 0.2), -10.0)


def crossing():
    r = rng('c3cine_crossing')
    sec = 2.4
    n = n_of(sec)
    t = np.arange(n) / SR
    closest = 0.85
    out = np.zeros((n, 2))
    k = 0
    tt = 0.0
    while tt < sec - 0.2:
        rel = tt - closest
        dop = 1.0 + 0.045 * np.tanh(-rel * 3.0)                  # pitch drops as we pass the crossing
        amp = 1.0 / (1.0 + (rel / 0.32) ** 2)
        s = bell_strike(r, 1240.0 * dop, 0.26)
        place(out, pan(s * amp, np.clip(-rel * 1.4, -0.8, 0.8)), tt)
        tt += 1 / 6.5
        k += 1
    rush = band(r.standard_normal(n), 250, 3000) * np.exp(-((t - closest) / 0.22) ** 2) * 0.55
    out += pan(rush, np.clip((closest - t) * 1.2, -0.6, 0.6))
    out += pan(lp(r.standard_normal(n), 140) * np.exp(-((t - closest) / 0.12) ** 2) * 0.5, 0.0)
    out = room(out, 'c3cine_crossing', 1.2, 0.9, 0.5, 0.18)
    return norm(fades(out, 0.05, 0.5), -5.0)


def bridge():
    r = rng('c3cine_bridge')
    sec = 13.2
    n = n_of(sec)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    meet = BRIDGE_MEET
    # exhaust beats: the near engine (Alexei's, from the right) and the far one (Konrad's, from the left)
    for who, p0, p1, gain, dark, rate0, rate1, ph in (('near', 0.75, -0.35, 1.0, 1000.0, 3.6, 2.9, 0.0),
                                                      ('far', -0.75, 0.35, 0.55, 650.0, 3.2, 2.6, 0.13)):
        tt = 0.2 + ph
        while tt < sec - 0.2:
            u = tt / sec
            rate = rate0 + (rate1 - rate0) * u
            prox = 1.0 / (1.0 + ((tt - meet) / 2.4) ** 2)
            s = chuff(r, 1.0 + 0.4 * prox, dark * (0.8 + 0.4 * prox))
            pp = p0 + (p1 - p0) * np.clip(tt / sec * 1.1, 0, 1)
            place(out, pan(s * gain * (0.45 + 0.55 * prox), pp), tt)
            tt += 1.0 / rate
    # the hollow rumble of wheels on the arches, swelling to the meeting point
    rum = lp(brown(n, r), 140) * (0.25 + 0.75 / (1.0 + ((t - meet) / 2.6) ** 2))
    out += pan(rum * 0.7, 0.0)
    # wheel clatter over the joints of both tracks (groups of four clicks)
    for side, pp in ((0, 0.4), (1, -0.4)):
        tt = 0.5 + side * 0.21
        while tt < sec - 0.3:
            for j in range(4):
                c = band(r.standard_normal(n_of(0.02)), 900, 3800) * decay(n_of(0.02), 0.004, 0.0005)
                place(out, pan(c * 0.18 * (0.5 + 0.5 / (1 + ((tt - meet) / 2.0) ** 2)), pp), tt + j * 0.075 + (j // 2) * 0.12)
            tt += 0.58 + 0.04 * side
    out = room(out, 'c3cine_bridge', 3.0, 2.2, 1.0, 0.35, predelay=0.03,
               slap=[(0.23, 0.35, 1800.0), (0.41, 0.22, 1200.0)])
    return norm(fades(out, 0.9, 1.6), -4.0)


def whistle_de():
    """A lower, steadier chime whistle far away across the river (two notes a minor third apart)."""
    r = rng('c3cine_whistle_de')
    sec = 3.0
    n = n_of(sec)
    t = np.arange(n) / SR
    env = np.clip(t / 0.12, 0, 1) * np.clip((1.55 - t) / 0.35, 0, 1)
    glide = 1.0 - 0.03 * np.exp(-t / 0.08)
    sig = np.zeros(n)
    for f0, g in ((392.0, 1.0), (466.2, 0.7)):
        ph = 2 * np.pi * np.cumsum(f0 * glide * (1 + 0.003 * np.sin(2 * np.pi * 5.2 * t))) / SR
        for h, hg in ((1, 1.0), (2, 0.35), (3, 0.18), (4, 0.06)):
            sig += g * hg * np.sin(h * ph)
    sig += band(r.standard_normal(n), 300, 2400) * 0.25            # the steam in it
    sig *= env
    sig = lp(sig, 2400)
    st = pan(sig, -0.45)
    st = room(st, 'c3cine_whistle_de', 3.0, 2.6, 1.2, 0.8, predelay=0.04, slap=[(0.31, 0.4, 1500.0)])
    return norm(fades(st, 0.01, 0.6), -9.0)


# --------------------------------------------------------------------------- the clocks
def _station(x, name, wet=0.3):
    return room(x, name, 2.2, 1.8, 0.9, wet, predelay=0.02)


def clock_tick():
    r = rng('c3cine_clock_tick')
    n = n_of(0.6)
    t = np.arange(n) / SR
    c = band(r.standard_normal(n), 2200, 6500) * decay(n, 0.003, 0.0003)
    body = np.sin(2 * np.pi * 820 * t) * decay(n, 0.02, 0.0008) * 0.5
    x = pan(c + body, 0.05)
    return norm(fades(_station(x, 'c3cine_clock_tick', 0.22), 0.0, 0.2), -12.0)


def clock_clack():
    r = rng('c3cine_clock_clack')
    n = n_of(1.2)
    t = np.arange(n) / SR
    c = band(r.standard_normal(n), 1600, 6000) * decay(n, 0.004, 0.0003)
    thud = np.sin(2 * np.pi * 190 * t * (1 - 0.3 * t)) * decay(n, 0.05, 0.001) * 0.9
    ring = (np.sin(2 * np.pi * 1910 * t) * 0.5 + np.sin(2 * np.pi * 2730 * t) * 0.3) * decay(n, 0.25, 0.001) * 0.35
    x = pan(c + thud + ring, 0.0)
    return norm(fades(_station(x, 'c3cine_clock_clack', 0.35), 0.0, 0.35), -4.0)


def palais_chime():
    r = rng('c3cine_palais_chime')
    sec = 3.0
    n = n_of(sec)
    t = np.arange(n) / SR
    f0 = 523.25
    x = np.zeros(n)
    for ratio, d, g in ((1.0, 2.0, 1.0), (2.76, 0.9, 0.42), (5.40, 0.45, 0.2), (8.93, 0.25, 0.08), (0.5, 1.4, 0.12)):
        x += g * np.sin(2 * np.pi * f0 * ratio * t + r.uniform(0, 6.28)) * decay(n, d, 0.006)
    x *= 1.0 + 0.04 * np.sin(2 * np.pi * 4.6 * t)                     # the spring's slow beating
    st = pan(x, 0.0)
    st = room(st, 'c3cine_palais_chime', 2.4, 1.8, 1.0, 0.4, predelay=0.015)
    return norm(fades(st, 0.0, 0.6), -9.0)


def step_marble(i):
    name = 'c3cine_step_marble_%d' % i
    r = rng(name)
    n = n_of(0.8)
    t = np.arange(n) / SR
    heel = band(r.standard_normal(n), 1400 + i * 120, 5200) * decay(n, 0.004, 0.0004)
    sole = band(r.standard_normal(n), 300, 1800) * decay(n, 0.018, 0.004) * 0.35
    thump = np.sin(2 * np.pi * (115 + 6 * i) * t) * decay(n, 0.035, 0.002) * 0.5
    x = np.zeros(n)
    place(x, sole, 0.0)
    place(x, heel + thump, 0.012)
    st = pan(x, -0.2 + 0.1 * i)
    st = room(st, name, 2.4, 2.0, 1.1, 0.4, predelay=0.02)
    return norm(fades(st, 0.0, 0.3), -9.0)


# --------------------------------------------------------------------------- the night (Close)
def depart_night():
    r = rng('c3cine_depart_night')
    sec = 6.5
    n = n_of(sec)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    # cylinder cocks venting (the engine is out of sight ahead, the hiss comes along the platform)
    hiss = band(r.standard_normal(n), 2500, 9000) * np.clip(t / 0.05, 0, 1) * np.exp(-t / 0.9) * 0.4
    out += pan(hiss, 0.25)
    # couplings snatching taut one after another, back to the last car near us
    for k, at in enumerate((0.35, 0.62, 0.88, 1.12)):
        m = n_of(0.5)
        tt = np.arange(m) / SR
        cl = (band(r.standard_normal(m), 400, 2400) * decay(m, 0.03, 0.001) +
              np.sin(2 * np.pi * (140 - k * 8) * tt) * decay(m, 0.08, 0.002) * 0.6)
        place(out, pan(cl * (0.35 + 0.18 * k), 0.15 + 0.05 * k), at)
    # heavy exhaust beats accelerating, every beat a little farther away (darker, quieter)
    tt = 0.5
    rate = 1.1
    while tt < sec - 0.3:
        dist = 1.0 + tt * 0.55
        s = chuff(r, 1.3, 900.0 / dist ** 0.6)
        place(out, pan(s * 0.9 / dist, 0.1), tt)
        rate = min(3.2, rate * 1.13)
        tt += 1.0 / rate
    # the wheels over the points, receding
    tt = 1.4
    while tt < sec - 0.4:
        dist = 1.0 + tt * 0.7
        for j in range(2):
            c = band(r.standard_normal(n_of(0.03)), 700, 3000) * decay(n_of(0.03), 0.006, 0.0005)
            place(out, pan(c * 0.28 / dist, 0.2), tt + j * 0.11)
        tt += 0.42
    out = room(out, 'c3cine_depart_night', 2.6, 2.0, 1.0, 0.32, predelay=0.02, slap=[(0.18, 0.25, 2000.0)])
    return norm(fades(out, 0.0, 1.4), -6.0)


def flaps():
    r = rng('c3cine_flaps')
    sec = 1.0
    n = n_of(sec)
    x = np.zeros(n)
    tt = 0.0
    rate = 38.0
    while tt < 0.75:
        m = n_of(0.012)
        c = band(r.standard_normal(m), 1100, 4200) * decay(m, 0.0025, 0.0003)
        c += np.sin(2 * np.pi * 2750 * np.arange(m) / SR) * decay(m, 0.003, 0.0003) * 0.3
        place(x, c * r.uniform(0.6, 1.0), tt)
        tt += 1.0 / rate
        rate *= 0.975
    place(x, band(r.standard_normal(n_of(0.02)), 800, 3000) * decay(n_of(0.02), 0.006, 0.0004) * 1.4, 0.8)
    st = pan(x, -0.55)
    st = room(st, 'c3cine_flaps', 1.6, 1.4, 0.8, 0.25)
    return norm(fades(st, 0.0, 0.15), -10.0)


# --------------------------------------------------------------------------- round 10: the journey
def station_rush():
    """Konrad's car runs through a small station without a stop (bed at 4.4 s of the film): the platform wall
    throws the rumble back (louder, brighter), the station bell rings and drops in pitch as it passes, three
    platform lamps whip past, then the open plain again."""
    r = rng('c3cine_station_rush')
    sec = 2.8
    n = n_of(sec)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    near = np.clip((t - 0.15) / 0.25, 0, 1) * np.clip((2.15 - t) / 0.3, 0, 1)        # alongside the platform
    wall = band(r.standard_normal(n), 300, 2600) * near * 0.35 + lp(brown(n, r), 220) * near * 0.5
    out += pan(wall, 0.0)
    for lt in (0.27, 0.93, 1.59):                                                   # the platform lamps
        pulse = lp(r.standard_normal(n), 160) * np.exp(-((t - lt) / 0.05) ** 2) * 0.55
        swish = band(r.standard_normal(n), 900, 3200) * np.exp(-((t - lt) / 0.09) ** 2) * 0.3
        out += pan(pulse + swish, 0.0)
    closest = 0.95                                                                   # the station bell
    tt = 0.05
    k = 0
    while tt < sec - 0.3:
        rel = tt - closest
        dop = 1.0 + 0.05 * np.tanh(-rel * 3.0)
        amp = 1.0 / (1.0 + (rel / 0.45) ** 2)
        s_ = bell_strike(r, 980.0 * dop, 0.3)
        place(out, pan(s_ * amp * 0.7, float(np.clip(-rel * 1.2, -0.8, 0.8))), tt)
        tt += 0.24 if k % 3 != 2 else 0.36
        k += 1
    out = room(out, 'c3cine_station_rush', 1.4, 1.0, 0.5, 0.22)
    return norm(fades(out, 0.08, 0.6), -7.0)


def truss():
    """Alexei's car on the truss bridge over the frozen river (bed at 11.55 s; AD round 2: the bridge is 2.0 s long,
    its portals pass the glass at 11.7 / 13.7 s): the hollow steel drumming, a girder beat on every bay (13 bays),
    the wheels ringing on the deck, the gorge's echo when it ends."""
    r = rng('c3cine_truss')
    sec = 3.0
    n = n_of(sec)
    t = np.arange(n) / SR
    on = np.clip((t - 0.1) / 0.12, 0, 1) * np.clip((2.2 - t) / 0.12, 0, 1)
    drum = lp(brown(n, r), 180) * on * 0.8
    ring = np.zeros(n)
    for f, g in ((311.0, 1.0), (467.0, 0.6), (701.0, 0.35)):
        ring += g * np.sin(2 * np.pi * f * t + r.uniform(0, 6.28))
    ring *= 0.05 * on * (0.6 + 0.4 * np.sin(2 * np.pi * 7.0 * t) ** 2)
    x = drum + ring
    bay = 2.0 / 13.0
    tt = 0.15
    while tt < 2.2:
        m = n_of(0.12)
        hit = lp(r.standard_normal(m), 400) * decay(m, 0.03, 0.002) * 0.7
        hit += band(r.standard_normal(m), 1500, 4500) * decay(m, 0.008, 0.0005) * 0.25
        place(x, hit, tt)
        tt += bay
    st = np.stack([x, x * 0.92], 1)
    st += pan(band(r.standard_normal(n), 500, 2000) * on * 0.08, 0.3)
    st = room(st, 'c3cine_truss', 2.2, 1.6, 0.8, 0.3, predelay=0.02, slap=[(0.21, 0.35, 1600.0)])
    return norm(fades(st, 0.05, 0.7), -6.0)


def line_night():
    """The Line before dawn from high above (bed at 17.3 s): wind over the open snow, the hum of the floodlight
    masts, the two trains far off on either side -- their beats left and right, receding."""
    r = rng('c3cine_line_night')
    sec = 7.2
    n = n_of(sec)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * t / 4.3 + 0.4) ** 2
    wl = band(r.standard_normal(n), 180, 1400) * (0.18 + 0.22 * gust)
    wr = band(r.standard_normal(n), 220, 1700) * (0.18 + 0.22 * np.roll(gust, n_of(1.1)))
    out[:, 0] += wl
    out[:, 1] += wr
    hum = (np.sin(2 * np.pi * 100.0 * t) * 0.5 + np.sin(2 * np.pi * 200.0 * t) * 0.25) * 0.025
    out += pan(hum, 0.0)
    for side, p_, rate, ph in ((0, -0.85, 3.3, 0.0), (1, 0.85, 3.6, 0.11)):
        tt = 0.3 + ph
        while tt < sec - 0.3:
            dist = 1.0 + tt * 0.35
            s_ = chuff(r, 0.8, 600.0 / dist ** 0.5)
            place(out, pan(s_ * 0.22 / dist, p_), tt)
            tt += 1.0 / rate
        for k in range(int(sec / 0.9)):                                            # far wheel clatter
            at = 0.5 + k * 0.9 + side * 0.33
            m = n_of(0.03)
            c = band(r.standard_normal(m), 600, 2400) * decay(m, 0.006, 0.0005)
            place(out, pan(c * 0.06 / (1 + at * 0.3), p_), at)
    out = room(out, 'c3cine_line_night', 3.2, 2.6, 1.4, 0.45, predelay=0.05)
    return norm(fades(out, 0.9, 1.4), -9.0)


def city_morning():
    """The waking Free City over the river (bed at 30.6 s): two church bells far apart, a tram's double ring on
    the quay, crows, and the low murmur of the streets."""
    r = rng('c3cine_city_morning')
    sec = 5.8
    n = n_of(sec)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    mur = lp(brown(n, r), 300) * 0.25 + band(r.standard_normal(n), 300, 1200) * 0.04
    out += pan(mur, 0.0)
    for (f0, p_, at0, every, cnt, g) in ((392.0, -0.5, 0.2, 1.55, 4, 0.5), (311.0, 0.55, 0.9, 1.9, 3, 0.4)):
        for k in range(cnt):
            m = n_of(3.0)
            tt = np.arange(m) / SR
            b = np.zeros(m)
            for ratio, d, gg in ((1.0, 1.6, 1.0), (2.0, 0.9, 0.4), (2.4, 0.7, 0.35), (3.0, 0.5, 0.2), (0.5, 2.2, 0.3)):
                b += gg * np.sin(2 * np.pi * f0 * ratio * tt + r.uniform(0, 6.28)) * decay(m, d, 0.004)
            place(out, pan(lp(b, 2600) * g, p_), at0 + k * every)
    for at in (2.6, 2.85):                                                         # the tram bell
        place(out, pan(bell_strike(r, 1560.0, 0.22) * 0.35, 0.3), at)
    for at, p_ in ((1.3, -0.3), (1.55, -0.35), (3.9, 0.2)):                        # crows
        m = n_of(0.3)
        tt = np.arange(m) / SR
        c = band(r.standard_normal(m), 700, 2200) * np.sin(np.pi * np.clip(tt / 0.22, 0, 1)) ** 0.5
        c *= 0.6 + 0.4 * np.sin(2 * np.pi * 38 * tt)
        place(out, pan(c * 0.22, p_), at)
    out = room(out, 'c3cine_city_morning', 3.5, 3.0, 1.5, 0.55, predelay=0.06)
    return norm(fades(out, 0.8, 1.6), -9.0)


SOUNDS = {
    'c3cine_ride_de': ride_de, 'c3cine_ride_su': ride_su, 'c3cine_pass': pass_lamp, 'c3cine_crossing': crossing,
    'c3cine_bridge': bridge, 'c3cine_whistle_de': whistle_de, 'c3cine_clock_tick': clock_tick,
    'c3cine_clock_clack': clock_clack, 'c3cine_palais_chime': palais_chime,
    'c3cine_step_marble_1': lambda: step_marble(1), 'c3cine_step_marble_2': lambda: step_marble(2),
    'c3cine_step_marble_3': lambda: step_marble(3), 'c3cine_depart_night': depart_night, 'c3cine_flaps': flaps,
    'c3cine_station_rush': station_rush, 'c3cine_truss': truss, 'c3cine_line_night': line_night,
    'c3cine_city_morning': city_morning,
}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args(argv)
    names = [s for s in a.only.split(',') if s] or list(SOUNDS)
    for nm in names:
        info = write(nm, SOUNDS[nm]())
        print(info)


if __name__ == '__main__':
    main()
