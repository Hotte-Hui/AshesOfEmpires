"""berlin_env_sfx -- original synthesized sound effects for the living details of the Berlin archive (M1).

Run:  py -3 -P tools/audiogen/berlin_env_sfx.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/berlin_*.wav (44.1 kHz, 16-bit, mono -- positional AudioStreamPlayer2D sources).
Loops (tram rumble, radio) are built periodic (FFT-domain noise shaping, whole-cycle partials) and carry a RIFF
'smpl' chunk, which Godot's WAV importer (loop_mode 'detect') turns into a forward loop.
Self-contained on purpose: the shared audiogen modules belong to the audio area.
"""
from __future__ import annotations

import math
import os
import struct
import sys
import wave
import zlib

import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


def t_axis(sec: float) -> np.ndarray:
    return np.arange(int(round(sec * SR)), dtype=np.float64) / SR


def shape_noise(n: int, lo: float, hi: float, r, tilt: float = 0.0, periodic: bool = True) -> np.ndarray:
    """white noise band-limited to [lo, hi] Hz in the FFT domain (periodic -> seamless loops); tilt dB/oct."""
    x = r.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = np.ones_like(f)
    edge = 0.25
    g *= np.clip((np.log2(np.maximum(f, 1.0)) - math.log2(max(lo, 1.0)) + edge) / (2 * edge), 0, 1)
    g *= np.clip((math.log2(hi) - np.log2(np.maximum(f, 1.0)) + edge) / (2 * edge), 0, 1)
    if tilt:
        g *= (np.maximum(f, 20.0) / 1000.0) ** (tilt / 6.02)
    y = np.fft.irfft(X * g, n)
    return y / (np.max(np.abs(y)) + 1e-9)


def lowpass(x: np.ndarray, fc: float) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    X *= 1.0 / np.sqrt(1.0 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def env_adsr(n, a, d, s_level, r, sustain_until=None):
    t = np.arange(n) / SR
    e = np.ones(n)
    e[t < a] = t[t < a] / max(a, 1e-4)
    su = sustain_until if sustain_until is not None else (n / SR - r)
    m = (t >= a) & (t < a + d)
    e[m] = 1 - (1 - s_level) * (t[m] - a) / max(d, 1e-4)
    e[(t >= a + d) & (t < su)] = s_level
    m = t >= su
    e[m] = s_level * np.clip(1 - (t[m] - su) / max(r, 1e-4), 0, 1)
    return e


def mode(t, f, decay, amp=1.0, phase=0.0):
    """exponentially decaying partial (struck resonance); decay = seconds to -60 dB"""
    return amp * np.sin(2 * math.pi * f * t + phase) * np.exp(-6.9 * t / decay)


def place(dst, src, at_sec, gain=1.0):
    i = int(round(at_sec * SR))
    j = min(len(dst), i + len(src))
    if j > i:
        dst[i:j] += src[:j - i] * gain


def normalize(x, peak_db=-3.0):
    pk = np.max(np.abs(x)) + 1e-9
    return x * (10 ** (peak_db / 20.0)) / pk


def fade(x, fin=0.004, fout=0.02):
    n = len(x)
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def write_wav(name: str, x: np.ndarray, loop: bool = False, peak_db: float = -3.0) -> str:
    os.makedirs(OUT, exist_ok=True)
    y = normalize(x, peak_db)
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if loop:
        # append a RIFF 'smpl' chunk with one forward loop over the whole file
        n = len(pcm)
        smpl = struct.pack('<9I', 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack('<6I', 0, 0, 0, n - 1, 0, 0)
        with open(path, 'r+b') as f:
            data = f.read()
            data += b'smpl' + struct.pack('<I', len(smpl)) + smpl
            data = data[:4] + struct.pack('<I', len(data) - 8) + data[8:]
            f.seek(0)
            f.write(data)
    return path


# =========================================================================== sounds
def tram_rumble():
    """seamless 4 s loop: low rumble + motor hum + rail-joint double clicks, muffled by the window"""
    sec = 4.0
    n = int(sec * SR)
    t = t_axis(sec)
    r = rng('tram_rumble')
    x = 0.55 * shape_noise(n, 25, 180, r, tilt=-3)
    x += 0.18 * shape_noise(n, 180, 900, r, tilt=-4)
    # motor / gear: whole cycles in 4 s (periodic)
    for f, a in ((48.0, 0.22), (96.0, 0.10), (520.0, 0.035), (1040.0, 0.012)):
        x += a * np.sin(2 * math.pi * f * t) * (1 + 0.25 * np.sin(2 * math.pi * 0.5 * t))
    # rail joints: ta-dam every second (two axles of a bogie)
    click = np.zeros(int(0.25 * SR))
    tc = np.arange(len(click)) / SR
    click += mode(tc, 160, 0.18, 0.9) + mode(tc, 410, 0.09, 0.5) + mode(tc, 1150, 0.04, 0.25)
    click *= np.minimum(1.0, tc / 0.002)
    for k in range(4):
        place(x, click, k * 1.0 + 0.05, 0.55)
        place(x, click, k * 1.0 + 0.19, 0.45)
    x = lowpass(x, 1900)
    return x


def tram_bell():
    sec = 1.6
    out = np.zeros(int(sec * SR))
    t = t_axis(1.3)
    f0 = 1180.0
    strike = sum(mode(t, f0 * k, d, a) for k, d, a in ((1.0, 1.1, 1.0), (2.02, 0.8, 0.45), (2.74, 0.6, 0.3),
                                                         (3.93, 0.45, 0.18), (5.4, 0.3, 0.08)))
    strike *= np.minimum(1.0, t / 0.0015)
    place(out, strike, 0.0, 1.0)
    place(out, strike, 0.27, 0.85)
    return fade(lowpass(out, 3000), 0.001, 0.15)


def pigeon_coo():
    sec = 1.5
    t = t_axis(sec)
    # three syllables: "hu -- RUUU -- u"
    syl = [(0.00, 0.22, 300, 330), (0.30, 0.55, 330, 380), (0.92, 0.42, 320, 270)]
    x = np.zeros_like(t)
    r = rng('coo')
    for (st, du, f1, f2) in syl:
        m = (t >= st) & (t < st + du)
        tt = t[m] - st
        f = f1 + (f2 - f1) * (tt / du)
        ph = 2 * math.pi * np.cumsum(f) / SR
        trem = 0.6 + 0.4 * np.sin(2 * math.pi * 26 * tt)                   # throat tremolo
        e = np.sin(math.pi * tt / du) ** 0.7
        tone = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
        x[m] += tone * trem * e
    x += 0.04 * shape_noise(len(t), 200, 1200, r) * (x != 0)
    return fade(lowpass(x, 1500), 0.01, 0.05)


def pigeon_flutter():
    sec = 1.1
    n = int(sec * SR)
    x = np.zeros(n)
    r = rng('flutter')
    tt = 0.0
    rate = 15.0
    k = 0
    while tt < 0.95:
        burst = shape_noise(int(0.03 * SR), 400, 3600, r, periodic=False)
        tb = np.arange(len(burst)) / SR
        burst *= np.exp(-tb / 0.008) * np.minimum(1.0, tb / 0.001)
        amp = (1.0 - tt) ** 1.3 * (0.7 + 0.3 * r.random())
        place(x, burst, tt, amp)
        tt += 1.0 / rate + r.uniform(-0.006, 0.006)
        rate = max(7.0, rate - 0.55)
        k += 1
    return fade(x, 0.001, 0.05)


def mouse_squeak():
    sec = 0.45
    t = t_axis(sec)
    x = np.zeros_like(t)
    for (st, du, f1, f2) in ((0.0, 0.07, 3300, 4300), (0.12, 0.05, 3600, 4100), (0.22, 0.09, 3200, 4600)):
        m = (t >= st) & (t < st + du)
        tt = t[m] - st
        f = f1 + (f2 - f1) * np.sin(math.pi * tt / du) + 180 * np.sin(2 * math.pi * 45 * tt)
        ph = 2 * math.pi * np.cumsum(f) / SR
        x[m] += np.sin(ph) * np.sin(math.pi * tt / du) ** 0.5
    return fade(x, 0.001, 0.02)


def clock_click(f_ring, seed):
    sec = 0.09
    t = t_axis(sec)
    r = rng(seed)
    x = shape_noise(len(t), 1500, 9000, r, periodic=False) * np.exp(-t / 0.0015)
    x += mode(t, f_ring, 0.05, 0.5) + mode(t, f_ring * 1.6, 0.03, 0.25) + mode(t, 420, 0.04, 0.35)
    return fade(x, 0.0005, 0.01)


def clock_chime():
    sec = 3.6
    out = np.zeros(int(sec * SR))
    t = t_axis(2.9)
    for (at, f) in ((0.0, 659.25), (0.75, 523.25)):
        note = mode(t, f, 2.4, 1.0) + mode(t, f * 2.76, 1.1, 0.35) + mode(t, f * 5.40, 0.5, 0.12)
        note *= np.minimum(1.0, t / 0.002)
        place(out, note, at, 1.0)
    return fade(out, 0.001, 0.3)


def radiator_knock():
    sec = 1.2
    out = np.zeros(int(sec * SR))
    t = t_axis(0.35)
    r = rng('knock')
    for at, g in ((0.0, 1.0), (0.17, 0.8), (0.44, 0.9), (0.61, 0.55)):
        k = mode(t, 310 * r.uniform(0.97, 1.03), 0.16, 0.8) + mode(t, 742, 0.1, 0.5) + mode(t, 1290, 0.07, 0.3)
        k += mode(t, 92, 0.12, 0.6)
        k *= np.minimum(1.0, t / 0.0008)
        place(out, k, at, g)
    return fade(lowpass(out, 3500), 0.0005, 0.08)


def radiator_hiss():
    sec = 1.8
    n = int(sec * SR)
    r = rng('hiss')
    x = shape_noise(n, 1800, 8000, r, periodic=False)
    t = np.arange(n) / SR
    sputter = 0.75 + 0.25 * np.sign(np.sin(2 * math.pi * 7.3 * t + 2 * np.sin(2 * math.pi * 1.1 * t)))
    x *= env_adsr(n, 0.08, 0.2, 0.6, 0.6) * sputter
    return fade(x, 0.003, 0.08)


def radio_loop():
    """10 s seamless loop: a little waltz from a small speaker in the next room (band-limited, crackle)"""
    sec = 10.0
    n = int(sec * SR)
    t = t_axis(sec)
    beat = sec / 15.0                                   # 3/4, five bars
    x = np.zeros(n)
    chords = [(261.63, 329.63, 392.0), (261.63, 329.63, 392.0), (196.0, 246.94, 349.23), (196.0, 246.94, 349.23),
              (261.63, 329.63, 392.0)]
    bass = [130.81, 130.81, 98.0, 98.0, 130.81]
    melody = [659.25, 587.33, 523.25, 587.33, 659.25, 659.25, 698.46, 659.25, 587.33, 493.88, 523.25, 587.33,
              523.25, 493.88, 523.25]

    def tone(f, dur, amp, partials=((1, 1.0), (2, 0.45), (3, 0.25), (4, 0.12))):
        tt = np.arange(int(dur * SR)) / SR
        y = sum(a * np.sin(2 * math.pi * f * k * tt) for k, a in partials)
        return y * amp * np.exp(-tt / (dur * 0.9)) * np.minimum(1.0, tt / 0.01)
    for b in range(15):
        bar, pos = divmod(b, 3)
        st = b * beat
        if pos == 0:
            place(x, tone(bass[bar], beat * 0.95, 0.5), st)
        else:
            for f in chords[bar]:
                place(x, tone(f, beat * 0.6, 0.16), st)
        place(x, tone(melody[b], beat * 0.92, 0.32, ((1, 1.0), (2, 0.6), (3, 0.3), (5, 0.1))), st)
    # wrap the tails of the last notes into the start (seamless)
    tail = np.zeros(n)
    x = np.concatenate([x, tail])
    x = x[:n] + x[n:2 * n]
    # small speaker + through the lodge glass: band-pass, a little hiss and crackle (periodic)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    X *= np.clip((f - 250) / 200, 0, 1) * 1.0 / np.sqrt(1.0 + (f / 2300.0) ** 6)
    x = np.fft.irfft(X, n)
    r = rng('radio')
    x = x / (np.max(np.abs(x)) + 1e-9)
    x += 0.05 * shape_noise(n, 2000, 7000, r)
    for k in range(18):
        place(x, np.array([0.5, -0.4, 0.2]) * r.uniform(0.2, 0.6), r.uniform(0, sec - 0.01))
    return x


def paper_flutter():
    sec = 0.6
    n = int(sec * SR)
    x = np.zeros(n)
    r = rng('paper')
    for k in range(22):
        b = shape_noise(int(0.02 * SR), 1500, 9000, r, periodic=False)
        tb = np.arange(len(b)) / SR
        b *= np.exp(-tb / r.uniform(0.002, 0.008))
        place(x, b, r.uniform(0.0, 0.5), r.uniform(0.2, 1.0) * (1 - k / 30))
    return fade(x, 0.002, 0.05)


def tube_capsule():
    sec = 1.5
    n = int(sec * SR)
    t = np.arange(n) / SR
    r = rng('tube')
    x = np.zeros(n)
    # whoosh: noise through a band that sweeps upward while the capsule approaches
    w = r.standard_normal(n)
    out = np.zeros(n)
    seg = int(0.05 * SR)
    for i in range(0, int(0.82 * SR), seg):
        fc = 250 + 2600 * (i / (0.82 * SR)) ** 1.6
        chunk = w[i:i + seg * 2]
        if len(chunk) < 8:
            break
        C = np.fft.rfft(chunk)
        f = np.fft.rfftfreq(len(chunk), 1.0 / SR)
        C *= np.exp(-((np.log2(np.maximum(f, 1)) - math.log2(fc)) ** 2) / 0.5)
        y = np.fft.irfft(C, len(chunk)) * np.hanning(len(chunk))
        out[i:i + len(y)] += y * (i / (0.82 * SR)) ** 1.2
    x += out / (np.max(np.abs(out)) + 1e-9) * 0.7
    # clunk at the station + rattle in the basket
    tt = np.arange(int(0.4 * SR)) / SR
    clunk = mode(tt, 118, 0.2, 1.0) + mode(tt, 1820, 0.06, 0.5) + mode(tt, 2930, 0.04, 0.3)
    clunk *= np.minimum(1.0, tt / 0.0005)
    place(x, clunk, 0.84, 1.0)
    rattle = mode(tt, 2400, 0.03, 0.4) + mode(tt, 3100, 0.025, 0.3)
    place(x, rattle, 1.0, 0.5)
    place(x, rattle, 1.07, 0.3)
    return fade(x, 0.01, 0.05)


SOUNDS = [
    ('berlin_tram_rumble', tram_rumble, True, -4.0),
    ('berlin_tram_bell', tram_bell, False, -3.0),
    ('berlin_pigeon_coo', pigeon_coo, False, -4.0),
    ('berlin_pigeon_flutter', pigeon_flutter, False, -3.0),
    ('berlin_mouse_squeak', mouse_squeak, False, -6.0),
    ('berlin_clock_tick', lambda: clock_click(2200, 'tick'), False, -4.0),
    ('berlin_clock_tock', lambda: clock_click(1780, 'tock'), False, -4.0),
    ('berlin_clock_chime', clock_chime, False, -3.0),
    ('berlin_radiator_knock', radiator_knock, False, -3.0),
    ('berlin_radiator_hiss', radiator_hiss, False, -6.0),
    ('berlin_radio_loop', radio_loop, True, -6.0),
    ('berlin_paper_flutter', paper_flutter, False, -6.0),
    ('berlin_tube_capsule', tube_capsule, False, -3.0),
]


def main(argv):
    out = []
    for name, fn, loop, peak in SOUNDS:
        p = write_wav(name, fn(), loop=loop, peak_db=peak)
        out.append(p)
        with wave.open(p, 'rb') as w:
            print('  %-24s %5.2f s%s' % (name, w.getnframes() / SR, '  (loop)' if loop else ''))
    print('[berlin_env_sfx] %d files -> %s' % (len(out), OUT))


if __name__ == '__main__':
    main(sys.argv[1:])
