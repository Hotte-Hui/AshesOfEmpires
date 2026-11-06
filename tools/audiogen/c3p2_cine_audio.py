"""c3p2_cine_audio -- original synthesised sound for the four Chapter-3 part-2 cinematics (owner: cinematics stream).

Self-contained numpy synthesis on the helpers of tools/audiogen/c3_cine_audio.py (band-pass, envelopes, panning,
generated rooms, WAV writer; imported read-only), deterministic (seeds = crc32 of the sound's name), 44.1 kHz /
16-bit, nothing sampled or downloaded.  Writes assets/audio/sfx/c3p2cine_*.wav (peaks -3..-12 dBFS like the other
SFX).  The radio voices are wordless formant babble through a small loudspeaker: the words are the subtitles.

  LS_C3_Radio   interval (the Radio Veltrava signal, an original four-note celesta motif), news_ru / news_de
                (announcer babble, two voices), tune (dial sweep: whistles, static), pencil (graphite strokes,
                loopable), corridor (steps on a runner, two notes slid under two doors), cafe (empty room: fridge
                hum, wall clock), doors (two hotel doors at once, the wind), snowsteps (two men walking)
  LS_C3_Fire    lamp (mains buzz with the flicker crackles at the picture's dips), ignite (the boxes catch),
                service_door, steps_out (outside, muffled), bolt (iron bolt slid home), roar
  LS_C3_Escape  chute (scraping up the slide on the three shoves), hatch_open, cough_k, pull, hatch_slam,
                cough_both, burst (souterrain windows, one every BURST_GAP), brigade (bells approaching)
  LS_C3_Halves  quay (wind over the ice, the fire far off), steps_apart (diverging), ice (creaks and booms),
                board (a split-flap row flipping in the station hall)

Run:  py -3 -P tools/audiogen/c3p2_cine_audio.py [--only name,name]   (then the shared --import)
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3_cine_audio as A  # noqa: E402  (read-only: band, decay, place, pan, fades, norm, room, write, ...)

SR = A.SR
n_of, t_axis, band, lp, hp, decay, place, pan, fades, norm, room, rng = (
    A.n_of, A.t_axis, A.band, A.lp, A.hp, A.decay, A.place, A.pan, A.fades, A.norm, A.room, A.rng)

# times shared with the pictures (scenes/cinematics/ch3_*/ch3_*.gd; checked by tests/test_c3p2_cinematics.gd)
LAMP_DIPS = (0.55, 1.05, 1.4, 2.4)           # ch3_fire.gd: the lamp's flicker dips (bed starts at 0.0)
CHUTE_PUSHES = (0.35, 1.55, 2.75)            # ch3_escape.gd PUSHES (bed starts at 0.0)
BURST_GAP = 0.42                              # ch3_escape.gd BURST_GAP


def write(name, x):
    return A.write(name, x)


# --------------------------------------------------------------------------------------------- building blocks
def radio_speaker(x, name, hum=0.03, static=0.02):
    """A small Bakelite set: band 280-3400 Hz, soft clipping, mains hum and a little static."""
    r = rng(name + 'spk')
    y = band(x, 280, 3400, 0.3)
    y = np.tanh(y * 2.2) / 2.2
    t = np.arange(len(y)) / SR
    y += hum * (np.sin(2 * np.pi * 50 * t) * 0.6 + np.sin(2 * np.pi * 100 * t) * 0.4)
    y += static * band(r.standard_normal(len(y)), 1500, 7000)
    return y


def babble(name, sec, f0=118.0, rate=5.2, phrase=(1.6, 2.6), pause=(0.18, 0.4), bright=1.0):
    """Wordless announcer speech: voiced syllables with moving formants, consonant noise, phrase prosody."""
    r = rng(name)
    n = n_of(sec)
    out = np.zeros(n)
    vowels = [(730, 1090, 2440), (530, 1840, 2480), (270, 2290, 3010), (570, 840, 2410), (300, 870, 2240),
              (440, 1020, 2240)]
    tt = 0.12
    while tt < sec - 0.3:
        plen = r.uniform(*phrase)
        pend = min(sec - 0.2, tt + plen)
        pitch0 = f0 * r.uniform(1.02, 1.12)
        while tt < pend:
            d = r.uniform(0.75, 1.25) / rate
            m = n_of(d)
            u = (tt - (pend - plen)) / max(plen, 1e-3)
            pf = pitch0 * (1.0 - 0.16 * np.clip(u, 0, 1)) * (1 + 0.04 * r.standard_normal())
            ph = np.cumsum(np.full(m, pf / SR)) * 2 * np.pi
            src = np.zeros(m)
            for k in range(1, 18):
                src += np.sin(ph * k) / k
            f1, f2, f3 = vowels[r.integers(0, len(vowels))]
            v = band(src, f1 * 0.8, f1 * 1.25, 0.4) * 1.0 + band(src, f2 * 0.85, f2 * 1.15, 0.3) * 0.55 * bright \
                + band(src, f3 * 0.9, f3 * 1.1, 0.3) * 0.25 * bright
            env = np.clip(np.minimum(np.arange(m) / (0.02 * SR), (m - np.arange(m)) / (0.035 * SR)), 0, 1)
            v *= env * r.uniform(0.6, 1.0)
            place(out, v, tt)
            if r.random() < 0.55:                                      # a consonant in front of the next vowel
                cm = n_of(r.uniform(0.02, 0.06))
                c = band(r.standard_normal(cm), r.uniform(2000, 4500), 7500) * decay(cm, 0.02, 0.003) * 0.35
                place(out, c, tt + d - 0.02)
            tt += d
        tt += r.uniform(*pause)
    return out


def crunch(r, gain=1.0, dark=1.0):
    """One step in fresh snow: a short granular squeak-crunch."""
    m = n_of(0.16)
    g = np.zeros(m)
    k = r.integers(14, 26)
    for _ in range(k):
        i = r.integers(0, m - 200)
        L = r.integers(30, 160)
        g[i:i + L] += r.standard_normal(L) * np.hanning(L) * r.uniform(0.3, 1.0)
    g = band(g, 400 * dark, 5200 * dark, 0.4) * decay(m, 0.07, 0.01)
    g += band(r.standard_normal(m), 60, 300) * decay(m, 0.03, 0.004) * 0.6
    return g * gain


def cough(r, f=520.0, gain=1.0):
    """A cough: a sharp voiced noise burst with a throat formant, then a short rasp."""
    m = n_of(0.34)
    nz = r.standard_normal(m)
    v = band(nz, f * 0.7, f * 2.6, 0.4) + band(nz, 1800, 3200, 0.3) * 0.4
    env = decay(m, 0.07, 0.004)
    t = np.arange(m) / SR
    voice = np.sin(2 * np.pi * (f * 0.42) * t + 0.4 * np.sin(2 * np.pi * 37 * t)) * decay(m, 0.05, 0.003) * 0.4
    return (v * env + voice) * gain


def metal_hit(r, f=(210, 520, 1130, 1870), tau=0.35, gain=1.0, dur=1.0):
    m = n_of(dur)
    t = np.arange(m) / SR
    x = np.zeros(m)
    for i, fr in enumerate(f):
        x += np.sin(2 * np.pi * fr * (1 + 0.002 * r.standard_normal()) * t) * np.exp(-t / (tau / (1 + i * 0.6))) / (1 + i * 0.5)
    x += band(r.standard_normal(m), 300, 4000) * decay(m, 0.012, 0.0005) * 1.6
    x += band(r.standard_normal(m), 40, 180) * decay(m, 0.06, 0.002) * 1.4
    return x * gain


def creak(r, sec, f=(180, 90), gain=1.0):
    """A hinge/friction creak: a gliding stick-slip pulse train through a resonance."""
    m = n_of(sec)
    t = np.arange(m) / SR
    fr = np.linspace(f[0], f[1], m) * (1 + 0.08 * np.sin(2 * np.pi * 3.0 * t))
    ph = np.cumsum(fr / SR)
    pulses = (np.mod(ph, 1.0) < 0.06).astype(float) * (0.6 + 0.4 * r.random(m))
    y = band(pulses, 500, 2600, 0.3) * np.hanning(m) * gain
    return y


def wind(r, sec, lo=120, hi=900, gust=0.35):
    m = n_of(sec)
    x = band(A.brown(m, r) if hasattr(A, 'brown') else r.standard_normal(m), lo, hi, 0.4)
    t = np.arange(m) / SR
    mod = 0.65 + gust * np.sin(2 * np.pi * 0.21 * t + r.uniform(0, 6)) + 0.2 * np.sin(2 * np.pi * 0.53 * t)
    x = x / (np.abs(x).max() + 1e-9) * np.clip(mod, 0.1, None)
    return x


def crackles(r, sec, rate=18.0, gain=1.0, grow=False):
    m = n_of(sec)
    x = np.zeros(m)
    tt = 0.0
    while tt < sec:
        g = r.uniform(0.2, 1.0) * gain * ((tt / sec) if grow else 1.0)
        L = n_of(r.uniform(0.002, 0.012))
        place(x, band(r.standard_normal(L), 1200, 9000) * decay(L, 0.003, 0.0002) * g, tt)
        tt += r.exponential(1.0 / rate)
    return x


# --------------------------------------------------------------------------------------------- LS_C3_Radio
def interval():
    """Radio Veltrava's interval signal: G5 E5 A5 D5 on a celesta-like tone, twice, through the set, across the
    square (wet)."""
    r = rng('c3p2cine_interval')
    sec = 3.8
    x = np.zeros(n_of(sec))
    notes = (784.0, 659.3, 880.0, 587.3)
    tt = 0.25
    for rep in range(2):
        for f in notes:
            m = n_of(0.9)
            t = np.arange(m) / SR
            tone = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / 0.08)
                    + 0.18 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t / 0.05)) * decay(m, 0.45, 0.002)
            place(x, tone * (0.9 if rep == 0 else 0.75), tt)
            tt += 0.36
        tt += 0.2
    y = radio_speaker(x, 'c3p2cine_interval', hum=0.01, static=0.01)
    st = pan(y, 0.0)
    st = room(st, 'c3p2cine_interval', 2.6, 2.4, 1.2, 0.55, predelay=0.03, slap=[(0.21, 0.3, 1800.0)])
    return norm(fades(st, 0.05, 0.6), -9.0)


def news(name, sec, f0, bright, p):
    v = babble(name, sec, f0=f0, bright=bright)
    y = radio_speaker(v, name)
    st = pan(y, p)
    st = room(st, name, 0.6, 0.35, 0.2, 0.18, predelay=0.004)
    return norm(fades(st, 0.08, 0.5), -6.0)


def tune():
    r = rng('c3p2cine_tune')
    sec = 1.25
    m = n_of(sec)
    t = np.arange(m) / SR
    f = 2600 - 2000 * np.sin(np.clip(t / sec, 0, 1) * np.pi * 0.9)
    whistle = np.sin(np.cumsum(2 * np.pi * f / SR)) * 0.25
    stat = band(r.standard_normal(m), 600, 6000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t)))
    frag = babble('c3p2cine_tune_v', sec, f0=140, rate=7.0) * (np.abs(t - 0.7) < 0.18)
    y = radio_speaker(whistle + stat * 0.6 + frag * 0.7, 'c3p2cine_tune', static=0.0)
    return norm(fades(pan(y, 0.0), 0.02, 0.15), -8.0)


def pencil():
    """2.0 s of writing (loopable: silent edges): strokes of graphite on paper, a pause between words."""
    r = rng('c3p2cine_pencil')
    sec = 2.0
    x = np.zeros(n_of(sec))
    tt = 0.08
    while tt < sec - 0.25:
        d = r.uniform(0.05, 0.16)
        m = n_of(d)
        s = band(r.standard_normal(m), 1800, 7000, 0.4) * np.hanning(m) * r.uniform(0.4, 1.0)
        s *= 1 + 0.5 * np.sin(2 * np.pi * r.uniform(18, 40) * np.arange(m) / SR)
        place(x, s, tt)
        tt += d + (r.uniform(0.18, 0.32) if r.random() < 0.2 else r.uniform(0.01, 0.05))
    x = band(x, 900, 8000)
    return norm(fades(pan(x, 0.25), 0.02, 0.05), -12.0)


def corridor():
    r = rng('c3p2cine_corridor')
    sec = 2.8
    x = np.zeros((n_of(sec), 2))
    for i, tt in enumerate((0.0, 0.32, 0.64, 1.38, 1.7)):
        st = band(r.standard_normal(n_of(0.1)), 50, 420) * decay(n_of(0.1), 0.03, 0.003)
        place(x, pan(st * 0.6, -0.4 + i * 0.2), tt)
    for tt, p in ((0.45, -0.7), (1.0, 0.7)):                          # the two notes slide under the doors
        m = n_of(0.42)
        s = band(r.standard_normal(m), 1500, 6500, 0.4) * np.hanning(m) * 0.5
        place(x, pan(s, p), tt)
    x = room(x, 'c3p2cine_corridor', 1.0, 0.7, 0.4, 0.3)
    return norm(fades(x, 0.05, 0.4), -10.0)


def cafe():
    r = rng('c3p2cine_cafe')
    sec = 4.0
    m = n_of(sec)
    t = np.arange(m) / SR
    hum = (np.sin(2 * np.pi * 98 * t) * 0.4 + np.sin(2 * np.pi * 196 * t) * 0.18 + np.sin(2 * np.pi * 294 * t) * 0.08)
    hum *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.4 * t)
    x = np.zeros((m, 2))
    x += pan(hum * 0.25, 0.6)
    for k in range(4):                                                  # the wall clock
        tick = band(r.standard_normal(n_of(0.02)), 2000, 6000) * decay(n_of(0.02), 0.004, 0.0003)
        place(x, pan(tick * (0.5 if k % 2 else 0.35), -0.5), 0.3 + k * 1.0)
    x += pan(wind(r, sec, 200, 1200, 0.3) * 0.12, -0.2)
    x = room(x, 'c3p2cine_cafe', 1.4, 1.0, 0.6, 0.35)
    return norm(fades(x, 0.4, 0.6), -14.0)


def doors():
    r = rng('c3p2cine_doors')
    sec = 2.0
    x = np.zeros((n_of(sec), 2))
    for p, d in ((-0.75, 0.0), (0.75, 0.04)):
        latch = metal_hit(r, (1800, 3300, 5200), 0.03, 0.5, 0.2)
        place(x, pan(latch, p), 0.1 + d)
        place(x, pan(creak(r, 0.7, (260, 140), 0.5), p), 0.18 + d)
    x += pan(wind(r, sec, 300, 2400, 0.4) * np.clip(t_axis(sec) / 0.6, 0, 1) * 0.35, 0.0)
    return norm(fades(x, 0.0, 0.5), -8.0)


def snowsteps():
    r = rng('c3p2cine_snowsteps')
    sec = 4.2
    x = np.zeros((n_of(sec), 2))
    for p, start, per, g in ((-0.6, 0.05, 0.52, 1.0), (0.6, 0.2, 0.56, 0.9)):
        tt = start
        k = 0
        while tt < sec - 0.2:
            place(x, pan(crunch(r, g * (1 - tt / sec * 0.5)), p * (1 - tt / sec * 0.4)), tt)
            tt += per * (1 + 0.04 * r.standard_normal())
            k += 1
    x += pan(wind(r, sec, 200, 1500, 0.3) * 0.1, 0.0)
    return norm(fades(x, 0.05, 0.5), -6.0)


# --------------------------------------------------------------------------------------------- LS_C3_Fire
def lamp():
    r = rng('c3p2cine_lamp')
    sec = 3.0
    m = n_of(sec)
    t = np.arange(m) / SR
    buzz = (np.sign(np.sin(2 * np.pi * 100 * t)) * 0.12 + np.sin(2 * np.pi * 50 * t) * 0.25)
    buzz = band(buzz, 80, 2400) * 0.5
    x = pan(buzz, 0.1)
    for d in LAMP_DIPS:
        c = band(r.standard_normal(n_of(0.09)), 800, 6000) * decay(n_of(0.09), 0.02, 0.001)
        place(x, pan(c * 1.5, 0.1), d - 0.02)
        g = np.ones(m)
        i0, i1 = n_of(d - 0.08), n_of(d + 0.08)
        g[i0:i1] = 0.3
        x = x * g[:, None]
    x = room(x, 'c3p2cine_lamp', 1.6, 1.4, 0.8, 0.3)
    return norm(fades(x, 0.1, 0.4), -14.0)


def ignite():
    r = rng('c3p2cine_ignite')
    sec = 3.0
    m = n_of(sec)
    x = np.zeros((m, 2))
    wh = band(r.standard_normal(m), 60, 700) * np.clip((t_axis(sec) - 0.5) / 0.25, 0, 1) * \
        np.exp(-np.clip(t_axis(sec) - 0.75, 0, None) / 1.2)
    x += pan(wh * 0.8, 0.4)
    x += pan(crackles(r, sec, 26, 0.7, grow=True), 0.5)
    x += pan(band(A.brown(m, r) if hasattr(A, 'brown') else r.standard_normal(m), 40, 260) *
             np.clip(t_axis(sec) / 3.0, 0, 1) * 0.6, 0.3)
    x = room(x, 'c3p2cine_ignite', 1.4, 1.2, 0.6, 0.35)
    return norm(fades(x, 0.0, 0.3), -7.0)


def service_door():
    r = rng('c3p2cine_service_door')
    x = np.zeros((n_of(1.2), 2))
    place(x, pan(creak(r, 0.35, (220, 160), 0.4), -0.1), 0.0)
    place(x, pan(metal_hit(r, (160, 420, 900), 0.12, 0.9, 0.5), -0.1), 0.32)
    x = room(x, 'c3p2cine_service_door', 1.8, 1.6, 0.8, 0.45, predelay=0.02)
    return norm(fades(x, 0.0, 0.3), -12.0)


def steps_out():
    r = rng('c3p2cine_steps_out')
    sec = 1.4
    x = np.zeros((n_of(sec), 2))
    for i, tt in enumerate((0.05, 0.5, 0.95)):
        place(x, pan(lp(crunch(r, 0.9), 900), 0.7 - i * 0.5), tt)
    return norm(fades(x, 0.0, 0.2), -14.0)


def bolt():
    r = rng('c3p2cine_bolt')
    sec = 1.2
    x = np.zeros((n_of(sec), 2))
    m = n_of(0.34)
    t = np.arange(m) / SR
    scrape = band(r.standard_normal(m), 700, 2600, 0.3) * (0.6 + 0.4 * np.sin(2 * np.pi * 34 * t)) * np.hanning(m)
    scrape += np.sin(2 * np.pi * (900 + 400 * t / 0.34) * t) * 0.15 * np.hanning(m)
    place(x, pan(scrape * 0.7, 0.6), 0.02)
    place(x, pan(metal_hit(r, (240, 610, 1370, 2210), 0.4, 1.2, 0.9), 0.6), 0.34)
    x = room(x, 'c3p2cine_bolt', 1.2, 1.1, 0.6, 0.35)
    return norm(fades(x, 0.0, 0.3), -4.0)


def roar():
    r = rng('c3p2cine_roar')
    sec = 3.8
    m = n_of(sec)
    t = t_axis(sec)
    body = band(A.brown(m, r) if hasattr(A, 'brown') else r.standard_normal(m), 35, 420, 0.4)
    body = body / (np.abs(body).max() + 1e-9) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t))
    x = pan(body * 1.6, 0.0)
    x += pan(crackles(r, sec, 34, 0.5), 0.3)
    x += pan(crackles(r, sec, 22, 0.4), -0.4)
    wh = band(r.standard_normal(m), 400, 3000) * np.clip(t / sec, 0, 1) ** 2 * 0.3
    x += pan(wh, 0.0)
    x = room(x, 'c3p2cine_roar', 1.6, 1.3, 0.6, 0.3)
    return norm(fades(x, 0.1, 0.5), -5.0)


# --------------------------------------------------------------------------------------------- LS_C3_Escape
def chute():
    r = rng('c3p2cine_chute')
    sec = 4.0
    x = np.zeros((n_of(sec), 2))
    for p in CHUTE_PUSHES:
        m = n_of(0.42)
        s = band(r.standard_normal(m), 400, 3200, 0.3) * np.hanning(m) * 0.9
        place(x, pan(s, 0.0), p)
        place(x, pan(cough(r, 380, 0.35), 0.1), p + 0.6)                  # muffled effort / cough
    x += pan(crackles(r, sec, 12, 0.25), -0.2)                             # coal grit trickling down
    x = room(x, 'c3p2cine_chute', 0.5, 0.45, 0.25, 0.45, predelay=0.003, slap=[(0.012, 0.5, 2500.0)])
    return norm(fades(x, 0.05, 0.3), -8.0)


def hatch_open():
    r = rng('c3p2cine_hatch_open')
    x = np.zeros((n_of(1.6), 2))
    place(x, pan(creak(r, 0.32, (140, 70), 0.7), 0.0), 0.0)
    place(x, pan(metal_hit(r, (130, 340, 760, 1410), 0.55, 1.4, 1.2), 0.1), 0.3)
    whoosh = band(r.standard_normal(n_of(0.9)), 200, 1500) * np.hanning(n_of(0.9)) * 0.4
    place(x, pan(whoosh, 0.0), 0.05)
    return norm(fades(x, 0.0, 0.4), -5.0)


def coughs(name, voices, sec):
    r = rng(name)
    x = np.zeros((n_of(sec), 2))
    for (p, f, starts) in voices:
        for tt in starts:
            place(x, pan(cough(r, f, r.uniform(0.7, 1.0)), p), tt)
        # wheezing breath between the coughs
        m = n_of(sec)
        br = band(r.standard_normal(m), 900, 3200) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * t_axis(sec))) * 0.06
        x += pan(br, p)
    x = room(x, name, 1.0, 0.6, 0.3, 0.12)
    return norm(fades(x, 0.0, 0.4), -9.0)


def pull():
    r = rng('c3p2cine_pull')
    sec = 2.2
    x = np.zeros((n_of(sec), 2))
    m = n_of(0.5)
    t = np.arange(m) / SR
    grunt = band(np.sin(2 * np.pi * 105 * t + 3 * np.sin(2 * np.pi * 6 * t)) + r.standard_normal(m) * 0.3, 90, 900) * np.hanning(m)
    place(x, pan(grunt * 0.6, 0.2), 1.2)
    cloth = band(r.standard_normal(n_of(0.6)), 1500, 6000) * np.hanning(n_of(0.6)) * 0.3
    place(x, pan(cloth, 0.0), 1.3)
    place(x, pan(crunch(r, 1.0, 0.8), 0.1), 1.75)
    gasp = band(r.standard_normal(n_of(0.3)), 700, 2600) * np.hanning(n_of(0.3)) * 0.4
    place(x, pan(gasp, -0.2), 1.9)
    return norm(fades(x, 0.0, 0.3), -9.0)


def hatch_slam():
    r = rng('c3p2cine_hatch_slam')
    x = np.zeros((n_of(1.4), 2))
    place(x, pan(metal_hit(r, (95, 260, 610, 1180), 0.6, 1.6, 1.3), 0.0), 0.0)
    thump = band(r.standard_normal(n_of(0.2)), 40, 300) * decay(n_of(0.2), 0.05, 0.002) * 1.5
    place(x, pan(thump, 0.0), 0.0)
    x = room(x, 'c3p2cine_hatch_slam', 1.6, 1.2, 0.6, 0.3)
    return norm(fades(x, 0.0, 0.3), -3.0)


def burst():
    r = rng('c3p2cine_burst')
    sec = 3.6
    x = np.zeros((n_of(sec), 2))
    for i in range(7):
        tt = i * BURST_GAP
        p = (i % 7) / 3.0 - 1.0
        m = n_of(0.5)
        crack = band(r.standard_normal(m), 2500, 9000) * decay(m, 0.03, 0.0005)
        tink = np.zeros(m)
        for _ in range(10):
            k = r.integers(0, m - 800)
            L = 600
            tink[k:k + L] += np.sin(2 * np.pi * r.uniform(3000, 7000) * np.arange(L) / SR) * decay(L, 0.01, 0.0003) * 0.3
        whoomph = band(r.standard_normal(m), 40, 400) * decay(m, 0.15, 0.01)
        place(x, pan(crack * 0.8 + tink + whoomph * 0.9, p * 0.8), tt)
    x += pan(crackles(r, sec, 20, 0.4, grow=True), 0.0)
    x = room(x, 'c3p2cine_burst', 1.8, 1.4, 0.7, 0.3)
    return norm(fades(x, 0.0, 0.5), -6.0)


def brigade():
    """Fire-brigade bells approaching from the right: a mechanical bell struck ~7 times a second."""
    r = rng('c3p2cine_brigade')
    sec = 3.4
    x = np.zeros((n_of(sec), 2))
    tt = 0.0
    while tt < sec - 0.2:
        u = tt / sec
        g = 0.15 + 0.85 * u
        f = 1480.0 * (1.0 + 0.012 * (1 - u))
        s = A.bell_strike(r, f, 0.22) if hasattr(A, 'bell_strike') else np.sin(2 * np.pi * f * t_axis(0.22)) * decay(n_of(0.22), 0.06)
        place(x, pan(s * g, 0.9 - u * 0.6), tt)
        tt += 1.0 / 7.0 * (1 + 0.03 * r.standard_normal())
    x = room(x, 'c3p2cine_brigade', 2.4, 2.0, 1.0, 0.5, predelay=0.02)
    return norm(fades(x, 0.3, 0.3), -10.0)


# --------------------------------------------------------------------------------------------- LS_C3_Halves
def quay():
    r = rng('c3p2cine_quay')
    sec = 6.2
    m = n_of(sec)
    x = np.zeros((m, 2))
    x += pan(wind(r, sec, 150, 1400, 0.45) * 0.6, -0.1)
    x += pan(band(A.brown(m, r) if hasattr(A, 'brown') else r.standard_normal(m), 30, 200) * 0.6, -0.7)  # the fire, far left
    x += pan(crackles(r, sec, 8, 0.15), -0.8)
    place(x, pan(creak(r, 0.8, (90, 60), 0.3), 0.3), 3.6)
    return norm(fades(x, 0.6, 0.6), -11.0)


def steps_apart():
    r = rng('c3p2cine_steps_apart')
    sec = 5.0
    x = np.zeros((n_of(sec), 2))
    for p_end, start, per in ((0.9, 0.25, 0.5), (-0.9, 0.45, 0.54)):
        tt = start
        while tt < sec - 0.2:
            u = tt / sec
            place(x, pan(crunch(r, 1.0 - u * 0.75), p_end * (0.2 + 0.8 * u)), tt)
            tt += per
    x += pan(wind(r, sec, 150, 1200, 0.4) * 0.12, 0.0)
    return norm(fades(x, 0.1, 0.6), -7.0)


def ice():
    """River ice under strain: a few descending 'pew' booms that travel along the sheet, creaks, wind."""
    r = rng('c3p2cine_ice')
    sec = 6.2
    m = n_of(sec)
    x = np.zeros((m, 2))
    for tt, p in ((0.8, -0.5), (2.9, 0.4), (4.6, -0.1)):
        L = n_of(0.9)
        t = np.arange(L) / SR
        f = 2400 * np.exp(-t / 0.12) + 140
        boom = np.sin(np.cumsum(2 * np.pi * f / SR)) * decay(L, 0.25, 0.002)
        boom = band(boom, 80, 4000) * 0.6
        place(x, pan(boom, p), tt)
    x += pan(wind(r, sec, 150, 1100, 0.4) * 0.35, 0.0)
    x = room(x, 'c3p2cine_ice', 2.8, 2.2, 1.2, 0.4, predelay=0.03)
    return norm(fades(x, 0.5, 0.6), -10.0)


def board():
    r = rng('c3p2cine_board')
    sec = 2.6
    x = np.zeros((n_of(sec), 2))
    tt = 0.1
    rate = 30.0
    while tt < 2.3:
        m = n_of(0.012)
        c = band(r.standard_normal(m), 1100, 4200) * decay(m, 0.0025, 0.0003)
        c += np.sin(2 * np.pi * 2750 * np.arange(m) / SR) * decay(m, 0.003, 0.0003) * 0.3
        place(x, pan(c * r.uniform(0.5, 1.0), -0.6 + tt / 2.3 * 1.2), tt)
        tt += 1.0 / rate * r.uniform(0.6, 1.4)
    x = room(x, 'c3p2cine_board', 2.6, 2.2, 1.0, 0.45, predelay=0.03)
    return norm(fades(x, 0.0, 0.3), -9.0)


SOUNDS = {
    'c3p2cine_interval': interval,
    'c3p2cine_news_ru': lambda: news('c3p2cine_news_ru', 6.9, 112.0, 0.9, -0.1),
    'c3p2cine_news_de': lambda: news('c3p2cine_news_de', 6.8, 124.0, 1.1, 0.1),
    'c3p2cine_tune': tune, 'c3p2cine_pencil': pencil, 'c3p2cine_corridor': corridor, 'c3p2cine_cafe': cafe,
    'c3p2cine_doors': doors, 'c3p2cine_snowsteps': snowsteps,
    'c3p2cine_lamp': lamp, 'c3p2cine_ignite': ignite, 'c3p2cine_service_door': service_door,
    'c3p2cine_steps_out': steps_out, 'c3p2cine_bolt': bolt, 'c3p2cine_roar': roar,
    'c3p2cine_chute': chute, 'c3p2cine_hatch_open': hatch_open,
    'c3p2cine_cough_k': lambda: coughs('c3p2cine_cough_k', [(0.0, 560.0, (0.1, 0.55, 0.95, 1.6))], 2.6),
    'c3p2cine_pull': pull, 'c3p2cine_hatch_slam': hatch_slam,
    'c3p2cine_cough_both': lambda: coughs('c3p2cine_cough_both', [(-0.45, 560.0, (0.05, 0.6, 1.3)),
                                                                   (0.45, 470.0, (0.3, 0.9, 1.55))], 2.1),
    'c3p2cine_burst': burst, 'c3p2cine_brigade': brigade,
    'c3p2cine_quay': quay, 'c3p2cine_steps_apart': steps_apart, 'c3p2cine_ice': ice, 'c3p2cine_board': board,
}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args(argv)
    names = [s for s in a.only.split(',') if s] or list(SOUNDS)
    for nm in names:
        print(write(nm, SOUNDS[nm]()))


if __name__ == '__main__':
    main()
