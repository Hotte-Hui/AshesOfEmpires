"""mg_audio_relay -- original synthesized sounds for the Chapter-3 mini-game "Das Relaispult" (§12.8).

Run:  py -3 -P tools/audiogen/mg_audio_relay.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/mg_relay_*.wav (44.1 kHz, 16-bit, mono):
  mg_relay_hall      LOOP 12 s: the Großer Saal heard from the interpreters' corridor -- a murmur of many voices
                     (formant babble, no words), chairs, paper, a cough, the soft room tone of a big hall
  mg_relay_voice_fr  LOOP 8 s: the chair at the microphone as the desk monitor gives it back (older man, calm)
  mg_relay_voice_ru  LOOP 8 s: the Soviet delegate (a woman, measured, darker vowels)
  mg_relay_voice_de  LOOP 8 s: the Reich delegate (a man, clipped consonants)
                     The voices are prosody only (glottal source + vowel formants + consonant noise); they carry no
                     language and no words. The UI fades them with the speaker and bends their pitch with the tempo.
  mg_relay_plug      a crossbar pin pushed into its socket: contact scrape + seat
  mg_relay_switch    a desk relay pulling in (round start)
  mg_relay_lamp_yellow  bakelite push button + the soft buzz of the signal lamp relay
  mg_relay_lamp_red     the same, heavier and lower
  mg_relay_lost      a channel dropping out (crackle, falling hiss, silence)
  mg_relay_bell      the chair's small brass hand bell, two strokes
  mg_relay_click     a dull button press that does nothing (lamp not needed)
Loops are built periodic (circular filtering and placement) and carry a RIFF 'smpl' chunk (Godot's WAV importer,
loop_mode 'detect' -> forward loop).
"""
from __future__ import annotations

import math
import os
import struct
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


def band(x: np.ndarray, lo: float, hi: float, order: int = 4) -> np.ndarray:
    """circular FFT band-pass (periodic -> keeps loops seamless)"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    g = 1.0 / np.sqrt(1.0 + (np.maximum(lo, 1e-3) / np.maximum(f, 1e-3)) ** order) if lo > 0 else np.ones_like(f)
    g = g / np.sqrt(1.0 + (f / hi) ** order)
    return np.fft.irfft(X * g, len(x))


def reverb(x: np.ndarray, rt: float, mix: float, seed: str, pre: float = 0.012) -> np.ndarray:
    """circular convolution with an exponentially decaying noise tail (a big, soft room)"""
    r = rng(seed)
    n = len(x)
    m = min(n, int(rt * 1.4 * SR))
    ir = r.standard_normal(m) * np.exp(-6.9 * np.arange(m) / (rt * SR))
    ir = band(np.concatenate([ir, np.zeros(n - m)]), 120, 5000)[:n]
    ir = np.roll(ir, int(pre * SR))
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    wet = np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(ir), n)
    return (1 - mix) * x + mix * wet * (np.std(x) / (np.std(wet) + 1e-9))


def place(dst, src, at_sec, gain=1.0, wrap=False):
    i = int(round(at_sec * SR))
    if wrap:
        idx = (np.arange(len(src)) + i) % len(dst)
        np.add.at(dst, idx, src * gain)
        return
    j = min(len(dst), i + len(src))
    if j > i:
        dst[i:j] += src[:j - i] * gain


def fade(x, fin=0.002, fout=0.02):
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def mode(t, f, decay, amp=1.0):
    return amp * np.sin(2 * math.pi * f * t) * np.exp(-6.9 * t / decay)


def write_wav(name: str, x: np.ndarray, loop: bool = False, peak_db: float = -3.0) -> str:
    os.makedirs(OUT, exist_ok=True)
    y = x * (10 ** (peak_db / 20.0)) / (np.max(np.abs(x)) + 1e-9)
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if loop:
        n = len(pcm)
        smpl = struct.pack('<9I', 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack('<6I', 0, 0, 0, n - 1, 0, 0)
        with open(path, 'r+b') as f:
            data = f.read()
            data += b'smpl' + struct.pack('<I', len(smpl)) + smpl
            data = data[:4] + struct.pack('<I', len(data) - 8) + data[8:]
            f.seek(0)
            f.write(data)
    print('wrote', os.path.relpath(path, ROOT), '%.2f s' % (len(pcm) / SR), 'loop' if loop else '')
    return path


# =========================================================================== voices (prosody, no words)
VOWELS = {   # rough formant sets F1, F2, F3 (Hz) -- generic vowel colours, no language model
    'a': (750, 1250, 2600), 'e': (480, 1950, 2600), 'i': (300, 2250, 3000), 'o': (500, 900, 2500),
    'u': (330, 800, 2300), 'y': (330, 1700, 2400), 'ae': (650, 1650, 2500), 'schwa': (520, 1450, 2500),
}
SPEAKERS = {
    # f0 base, f0 range (semitones), syllables/s, vowel weights, consonant noise share, formant scale, phrase shape
    'fr': {'f0': 112.0, 'range': 3.0, 'rate': 4.6, 'vowels': ['e', 'a', 'y', 'o', 'i', 'schwa', 'ae'],
           'noise': 0.35, 'fscale': 0.97, 'rise': 1.0, 'seed': 'voice.chair'},
    'ru': {'f0': 196.0, 'range': 3.6, 'rate': 4.2, 'vowels': ['a', 'o', 'u', 'i', 'schwa', 'e'],
           'noise': 0.42, 'fscale': 1.12, 'rise': -0.4, 'seed': 'voice.soviet'},
    'de': {'f0': 124.0, 'range': 2.6, 'rate': 4.4, 'vowels': ['a', 'e', 'i', 'o', 'u', 'schwa', 'ae'],
           'noise': 0.55, 'fscale': 1.0, 'rise': -0.8, 'seed': 'voice.reich'},
}


def _formant_gain(freq: np.ndarray, formants, bw=(90.0, 120.0, 160.0)) -> np.ndarray:
    g = np.zeros_like(freq)
    for (fc, b, a) in zip(formants, bw, (1.0, 0.7, 0.35)):
        g += a / (1.0 + ((freq - fc) / b) ** 2)
    return g


def voice_raw(p: dict, sec: float, seed: str) -> np.ndarray:
    """A dry voice: phrases of syllables (glottal source with formant-weighted harmonics, consonant noise at the
    onsets), declination and stress in the pitch; loop-exact (the plan is stretched to end at `sec`)."""
    r = rng(seed)
    n = int(sec * SR)
    # --- syllable plan: phrases of 5-11 syllables with short pauses; the plan wraps around the loop
    syl = []
    at = 0.0
    while at < sec:
        k = int(r.integers(5, 12))
        for s in range(k):
            dur = r.uniform(0.75, 1.3) / p['rate']
            syl.append({'t0': at, 'dur': dur, 'v': p['vowels'][int(r.integers(0, len(p['vowels'])))],
                        'stress': r.random() < 0.28, 'cons': r.random() < 0.8, 'phrase': (k, s)})
            at += dur
        at += r.uniform(0.18, 0.42)
    scale = sec / at
    for s in syl:
        s['t0'] *= scale
        s['dur'] *= scale
    semis = np.zeros(n)
    amp = np.zeros(n)
    f1 = np.full(n, 500.0)
    f2 = np.full(n, 1500.0)
    f3 = np.full(n, 2500.0)
    for s in syl:
        i0, i1 = int(s['t0'] * SR), min(n, int((s['t0'] + s['dur']) * SR))
        if i1 <= i0:
            continue
        k, idx = s['phrase']
        pos = idx / max(1, k - 1)
        base = p['range'] * (0.6 - pos * 0.9)                         # declination
        if idx >= k - 2:
            base += p['rise'] * p['range'] * 0.5 * (idx - (k - 3))       # phrase-final rise (fr) or fall (de/ru)
        if s['stress']:
            base += p['range'] * 0.45
        m = i1 - i0
        tt = np.linspace(0, 1, m)
        semis[i0:i1] = base + 0.6 * np.sin(tt * math.pi) * (1 if s['stress'] else 0.4)
        env = np.minimum(1.0, tt / 0.12) * np.minimum(1.0, (1 - tt) / 0.25)
        amp[i0:i1] = env * (1.0 if s['stress'] else 0.78)
        fm = VOWELS[s['v']]
        f1[i0:i1] = fm[0] * p['fscale']
        f2[i0:i1] = fm[1] * p['fscale']
        f3[i0:i1] = fm[2] * p['fscale']

    def smooth(x, ms):
        k = int(ms / 1000.0 * SR)
        ker = np.hanning(2 * k + 1)
        ker /= ker.sum()
        K = np.fft.rfft(np.roll(np.concatenate([ker, np.zeros(n - len(ker))]), -k))
        return np.fft.irfft(np.fft.rfft(x) * K, n)
    semis = smooth(semis, 40)
    f1, f2, f3 = smooth(f1, 25), smooth(f2, 25), smooth(f3, 25)
    amp = np.clip(smooth(amp, 12), 0.0, 1.0)
    jitter = smooth(r.standard_normal(n), 8) * 0.08
    f0 = p['f0'] * 2.0 ** ((semis + jitter) / 12.0)
    phase = np.cumsum(f0) / SR
    phase *= round(phase[-1]) / phase[-1]          # whole cycles over the loop
    y = np.zeros(n)
    hmax = int(4600 / p['f0'])
    for h in range(1, hmax + 1):
        fh = f0 * h
        g = _formant_gain(fh, (f1, f2, f3), (70.0, 95.0, 140.0)) * (h ** -1.55)
        g[fh > 5200] = 0.0
        y += g * np.sin(2 * math.pi * h * phase)
    breath = band(r.standard_normal(n), 400, 4000) * 0.02
    y = (y + breath * np.std(y) / (np.std(breath) + 1e-9) * 0.08) * amp
    noise = np.zeros(n)
    for s in syl:
        if not s['cons']:
            continue
        L = int(r.uniform(0.03, 0.07) * SR)
        burst = r.standard_normal(L) * np.hanning(L)
        lo, hi = (2400, 6500) if r.random() < 0.5 else (1300, 3800)
        burst = band(np.concatenate([burst, np.zeros(2048)]), lo, hi)[:L]
        place(noise, burst, s['t0'] - L / SR * 0.4, 1.0, wrap=True)
    return y / (np.std(y) + 1e-9) + noise / (np.std(noise) + 1e-9) * 0.12 * p['noise']


def voice(lang: str, sec: float = 8.0) -> np.ndarray:
    p = SPEAKERS[lang]
    y = voice_raw(p, sec, p['seed'])
    # through the desk monitor: telephone band, a little grit, a small room
    y = band(y, 280, 3400, 8)
    y = np.tanh(y * 1.3) / 1.3
    return reverb(y, 0.4, 0.14, p['seed'] + '.room')


# =========================================================================== the hall
def hall(sec: float = 12.0) -> np.ndarray:
    r = rng('relay.hall')
    n = int(sec * SR)
    x = np.zeros(n)
    # the delegations murmur: a dozen far voices (no words), each at its own pitch and pace
    for k in range(12):
        rk = rng('relay.hall.v%d' % k)
        p = {'f0': float(rk.uniform(95, 230)), 'range': float(rk.uniform(2.0, 4.0)), 'rate': float(rk.uniform(3.8, 5.0)),
             'vowels': list(VOWELS), 'noise': 0.5, 'fscale': float(rk.uniform(0.92, 1.15)), 'rise': float(rk.uniform(-0.8, 0.8))}
        v = voice_raw(p, sec, 'relay.hall.voice%d' % k)
        x += np.roll(v, int(rk.integers(0, n))) * float(rk.uniform(0.25, 1.0))
    x = band(x, 120, 2400)
    # room tone: low rumble of a big hall + ventilation hiss
    rt = band(r.standard_normal(n), 30, 180) * 0.6 + band(r.standard_normal(n), 800, 4000) * 0.05
    x = x / (np.std(x) + 1e-9) + rt / (np.std(rt) + 1e-9) * 0.35
    # chairs, paper, a cough, a pencil (wrap-placed)
    for (t0, kind) in ((1.3, 'paper'), (3.9, 'chair'), (6.2, 'cough'), (8.4, 'paper'), (10.1, 'pencil'), (11.2, 'chair')):
        if kind == 'paper':
            L = int(0.35 * SR)
            s = band(r.standard_normal(L), 1500, 7000) * np.hanning(L) * (0.5 + 0.5 * np.abs(np.sin(np.arange(L) / SR * 40)))
            place(x, s * 1.2, t0, 1.0, wrap=True)
        elif kind == 'chair':
            tt = t_axis(0.4)
            s = np.sin(2 * math.pi * (180 + 60 * tt) * tt) * np.exp(-tt / 0.15) * 0.8
            s += band(r.standard_normal(len(tt)), 300, 1500) * np.exp(-tt / 0.1) * 0.6
            place(x, s * 1.4, t0, 1.0, wrap=True)
        elif kind == 'cough':
            tt = t_axis(0.5)
            env = np.exp(-((tt - 0.05) / 0.04) ** 2) + 0.7 * np.exp(-((tt - 0.22) / 0.05) ** 2)
            s = band(r.standard_normal(len(tt)), 250, 2500) * env
            place(x, s * 1.6, t0, 1.0, wrap=True)
        else:
            L = int(0.25 * SR)
            s = band(r.standard_normal(L), 3000, 9000) * np.exp(-np.arange(L) / (0.02 * SR))
            place(x, s * 0.8, t0, 1.0, wrap=True)
    x = reverb(x, 1.9, 0.55, 'relay.hall.room', 0.03)
    x = band(x, 60, 3200)                      # behind glass
    return x


# =========================================================================== one-shots
def plug():
    r = rng('relay.plug')
    x = np.zeros(int(0.3 * SR))
    L = int(0.03 * SR)
    scrape = band(r.standard_normal(L), 2500, 9000) * np.hanning(L) * 0.5
    place(x, scrape, 0.0)
    t = t_axis(0.2)
    seat = mode(t, 1850, 0.05, 0.5) + mode(t, 2930, 0.03, 0.35) + mode(t, 640, 0.07, 0.6)
    seat += band(r.standard_normal(len(t)), 600, 5000) * np.exp(-t / 0.004)
    place(x, seat, 0.028, 1.0)
    thunk = mode(t_axis(0.12), 180, 0.06, 0.6)
    place(x, thunk, 0.03, 1.0)
    return fade(x)


def switch():
    r = rng('relay.switch')
    x = np.zeros(int(0.45 * SR))
    t = t_axis(0.25)
    clack = mode(t, 980, 0.04, 0.8) + mode(t, 2400, 0.025, 0.4) + mode(t, 310, 0.08, 0.6)
    clack += band(r.standard_normal(len(t)), 900, 7000) * np.exp(-t / 0.003)
    place(x, clack, 0.0)
    place(x, clack * 0.45, 0.012)
    hum_t = t_axis(0.38)
    hum = (np.sin(2 * math.pi * 100 * hum_t) + 0.4 * np.sin(2 * math.pi * 200 * hum_t)) * np.exp(-hum_t / 0.14) * 0.12
    place(x, hum, 0.01)
    return fade(x)


def _button(seed, f_click, buzz_f, buzz_len, gain):
    r = rng(seed)
    x = np.zeros(int((buzz_len + 0.15) * SR))
    t = t_axis(0.12)
    click = mode(t, f_click, 0.025, 0.8) + mode(t, f_click * 2.3, 0.015, 0.4)
    click += band(r.standard_normal(len(t)), 1000, 6000) * np.exp(-t / 0.002) * 0.8
    place(x, click, 0.0)
    bt = t_axis(buzz_len)
    env = np.minimum(1.0, bt / 0.02) * np.exp(-bt / (buzz_len * 0.6))
    buzz = np.sign(np.sin(2 * math.pi * buzz_f * bt)) * 0.2 + np.sin(2 * math.pi * buzz_f * 2 * bt) * 0.25
    buzz = band(buzz, 80, 1800) * env * gain
    place(x, buzz, 0.02)
    return fade(x)


def lamp_yellow():
    return _button('relay.lamp.y', 1500, 100, 0.32, 0.7)


def lamp_red():
    x = _button('relay.lamp.r', 1100, 75, 0.45, 1.0)
    t = t_axis(0.2)
    rel = mode(t, 760, 0.04, 0.5) + mode(t, 1900, 0.02, 0.3)
    place(x, rel, 0.05)
    return fade(x)


def lost():
    r = rng('relay.lost')
    x = np.zeros(int(0.7 * SR))
    L = int(0.12 * SR)
    crackle = np.zeros(L)
    for _ in range(18):
        i = int(r.integers(0, L - 40))
        crackle[i:i + 30] += r.standard_normal(30) * np.exp(-np.arange(30) / 6.0) * r.uniform(0.4, 1.0)
    place(x, band(crackle, 800, 8000), 0.0, 1.0)
    t = t_axis(0.5)
    hiss = band(r.standard_normal(len(t)), 400, 4000) * np.exp(-t / 0.12) * 0.5
    # falling: a sweeping low-pass imitation by mixing two bands with time-varying weight
    hiss2 = band(r.standard_normal(len(t)), 200, 1200) * (1 - np.exp(-t / 0.2)) * np.exp(-t / 0.25) * 0.4
    place(x, hiss + hiss2, 0.08)
    tone = np.sin(2 * math.pi * (900 - 500 * t) * t) * np.exp(-t / 0.1) * 0.15
    place(x, tone, 0.08)
    return fade(x)


def bell():
    x = np.zeros(int(2.2 * SR))
    t = t_axis(1.9)
    ratios = (1.0, 2.0, 2.76, 4.07, 5.43, 6.8)
    f0 = 1180.0
    stroke = sum(mode(t, f0 * q, 1.6 / (1 + 0.5 * i), 1.0 / (1 + 0.6 * i)) for i, q in enumerate(ratios))
    stroke += mode(t, f0 * 1.002, 1.4, 0.5)                 # slight beating
    stroke *= np.minimum(1.0, t / 0.002)
    place(x, stroke, 0.0, 1.0)
    place(x, stroke * 0.8, 0.42, 1.0)
    x = reverb(x, 1.2, 0.3, 'relay.bell.room')
    return fade(x, 0.001, 0.2)


def click():
    r = rng('relay.click')
    x = np.zeros(int(0.12 * SR))
    t = t_axis(0.1)
    c = mode(t, 900, 0.02, 0.6) + band(r.standard_normal(len(t)), 600, 3000) * np.exp(-t / 0.002) * 0.5
    place(x, c, 0.0)
    return fade(x)


def main():
    write_wav('mg_relay_hall', hall(), loop=True, peak_db=-6.0)
    for lang in ('fr', 'ru', 'de'):
        write_wav('mg_relay_voice_' + lang, voice(lang), loop=True, peak_db=-4.0)
    write_wav('mg_relay_plug', plug(), peak_db=-4.0)
    write_wav('mg_relay_switch', switch(), peak_db=-6.0)
    write_wav('mg_relay_lamp_yellow', lamp_yellow(), peak_db=-5.0)
    write_wav('mg_relay_lamp_red', lamp_red(), peak_db=-4.0)
    write_wav('mg_relay_lost', lost(), peak_db=-5.0)
    write_wav('mg_relay_bell', bell(), peak_db=-5.0)
    write_wav('mg_relay_click', click(), peak_db=-8.0)


if __name__ == '__main__':
    main()
