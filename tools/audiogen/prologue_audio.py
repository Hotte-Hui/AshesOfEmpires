"""prologue_audio -- the score of the prologue LS_Prologue (scenes/cinematics/prologue, round 11).

Run:  py -3 -P tools/audiogen/prologue_audio.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/music/mus_prologue.wav (~64 s, 44.1 kHz stereo, one-shot, not looped).  Built from the
game's own motifs and instruments (music.py, read-only): a calm string ground in D minor under the Line, the map
gets single piano notes as pins and a soft pluck pulse when the trains run again, the papers sink onto an Eb colour
and a low pedal when the stamp lands, Berlin brings B (Konrad's motif) on celesta over G minor, Karsk K (Alexei's)
on felt piano -- the score ends open on A sus2, the cut to Chapter 1 resolves nothing.
Timeline in seconds = the film's (prologue.gd SHOTS): p1 0-13, p2 13-32.6, p3 32.6-41, p4 41-49, p5 49-60.
"""
from __future__ import annotations

import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import dsp  # noqa: E402
from music import (Track, hall_ir, K_A, B_1, DM9, BBM7, ASUS2, STR_EQ, STR_HI_EQ, PIANO_EQ, CEL_EQ,  # noqa: E402
                   PLUCK_EQ)

ROOT = os.path.dirname(os.path.dirname(HERE))
BPM = 63.0


def b(sec: float) -> float:
    """Beat of a film time in seconds."""
    return sec * BPM / 60.0


def mus_prologue():
    T = Track('mus_prologue', bpm=BPM, beats=63, loop=False, seed=111, tail=4.0)
    # p1 the Line: D minor ground, a cold harmonic above
    T.strings(0, b(13.6), DM9[:5], vel=0.30, attack=3.2, release=3.0)
    T.strings(b(2.0), b(11.0), [81], vel=0.10, stem='strings_hi', harmonic=True, attack=3.0, vib=3.5)
    T.piano([(0, 3, 62), (3, 4, 69)], vel=0.30, beat0=b(3.2), felt=0.75)
    # p2 the map: Bbmaj7 -> Gm, pins on the piano, the corridors rise, the trains pulse
    T.strings(b(13.0), b(9.0), BBM7[:5], vel=0.32, attack=2.5)
    T.strings(b(21.8), b(11.0), [43, 50, 58, 62, 69], vel=0.32, attack=2.2)
    T.piano([(0, 2, 74)], vel=0.30, beat0=b(14.0), felt=0.7)
    T.piano([(0, 1.5, 69), (1.5, 3, 76)], vel=0.32, beat0=b(18.8), felt=0.7)
    T.piano([(0, 1, 74), (1, 1, 76), (2, 3, 77)], vel=0.32, beat0=b(23.8), felt=0.7)
    T.pluck([(i, 0.8, 38 if i % 2 == 0 else 45) for i in range(7)], vel=0.34, beat0=b(28.8), t60=2.0)
    # p3 the papers: Eb colour, the stamp lands on a low pedal, then held breath
    T.strings(b(32.6), b(4.6), [39, 46, 55, 62], vel=0.30, attack=1.6, release=1.6)
    T.strings(b(37.0), b(4.2), [26, 38], vel=0.34, attack=0.4, release=2.6)
    T.strings(b(37.8), b(3.2), [86], vel=0.08, stem='strings_hi', harmonic=True, attack=1.6, vib=3.0)
    # p4 Berlin: B on celesta over G minor
    T.strings(b(41.0), b(8.2), [43, 50, 58, 62], vel=0.32, attack=1.8)
    T.celesta(B_1[:7], vel=0.36, beat0=b(41.8))
    # p5 Karsk: K on felt piano over D minor, ending open
    T.strings(b(49.0), b(6.4), DM9, vel=0.34, attack=2.0)
    T.piano(K_A, vel=0.40, beat0=b(49.6), felt=0.7)
    T.strings(b(55.2), b(4.6), ASUS2, vel=0.30, attack=1.8, release=3.6)
    T.strings(b(55.4), b(4.4), [88], vel=0.08, stem='strings_hi', harmonic=True, attack=2.0, vib=3.0)
    ir = hall_ir(1111, rt_low=3.8, rt_high=1.6)
    mix = {'strings': (0.0, 0.34, STR_EQ), 'strings_hi': (-12.0, 0.5, STR_HI_EQ),
           'piano': (-1.0, 0.34, PIANO_EQ), 'celesta': (-3.0, 0.38, CEL_EQ), 'pluck': (-8.0, 0.30, PLUCK_EQ)}
    return T.mixdown(mix, ir, target_rms=-21.0, end_fade=3.0)


def main():
    out = mus_prologue()
    path = os.path.join(ROOT, 'assets', 'audio', 'music', 'mus_prologue.wav')
    st = dsp.write_wav(path, out, loop=None, seed=zlib.crc32(b'mus_prologue'))
    print(path, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in st.items()})


if __name__ == '__main__':
    main()
