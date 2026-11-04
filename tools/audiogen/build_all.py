"""build_all.py -- regenerate the complete ASHES OF EMPIRES soundscape (deterministic).

    py -3 -P tools/audiogen/build_all.py                 # everything (+ analysis, previews, .import)
    py -3 -P tools/audiogen/build_all.py --only mus_karsk,amb_karsk_yard
    py -3 -P tools/audiogen/build_all.py --jobs 8 --no-spectro
    py -3 -P tools/audiogen/build_all.py --godot          # also run Godot --import + headless test

Outputs: assets/audio/{amb,music,sfx}/*.wav (44.1 kHz / 16-bit PCM, loops carry a RIFF 'smpl'
chunk), *.wav.import (compress/mode=0 -> lossless PCM in Godot), assets/audio/_preview/*.png
spectrograms + analysis.json + audio_manifest.json (loop points, durations, levels).
No network, no external samples: every sound is synthesised by tools/audiogen/*.py.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AUDIO = os.path.join(ROOT, 'assets', 'audio')
GODOT = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Godot',
                     'Godot_v4.7.2-stable_win64_console.exe')


def registry() -> dict:
    """name -> (module, kind) for every asset."""
    import music
    reg = {name: ('music', 'music') for name in music.TRACKS}
    try:
        import ambience
        reg.update({name: ('ambience', 'amb') for name in ambience.TRACKS})
    except ImportError:
        pass
    try:
        import sfx
        reg.update({name: ('sfx', 'sfx') for name in sfx.SOUNDS})
    except ImportError:
        pass
    return reg


def build_one(name: str, module: str, kind: str) -> dict:
    import importlib
    import dsp
    mod = importlib.import_module(module)
    t0 = time.time()
    table = mod.TRACKS if hasattr(mod, 'TRACKS') else mod.SOUNDS
    results = table[name]()
    # a builder returns (signal, loop) or a list of (name, signal, loop) for variants
    if isinstance(results, list):
        items = results
    else:
        sig, loop = results
        items = [(name, sig, loop)]
    written = []
    for (nm, sig, loop) in items:
        path = os.path.join(AUDIO, kind, nm + '.wav')
        st = dsp.write_wav(path, sig, loop=loop, seed=zlib.crc32(nm.encode()))
        written.append({'name': nm, 'path': path, 'loop': loop, **st})
    return {'name': name, 'seconds': round(time.time() - t0, 1), 'files': written}


IMPORT_TEMPLATE = '[remap]\n\nimporter="wav"\ntype="AudioStreamWAV"\n\n[params]\n\ncompress/mode=0\n'


def ensure_import_files() -> int:
    """Lossless PCM import for every WAV (keeps existing uid; only patches compress/mode)."""
    changed = 0
    for kind in ('amb', 'music', 'sfx'):
        d = os.path.join(AUDIO, kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.wav'):
                continue
            imp = os.path.join(d, fn + '.import')
            if not os.path.exists(imp):
                with open(imp, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(IMPORT_TEMPLATE)
                changed += 1
                continue
            txt = open(imp, encoding='utf-8').read()
            if 'compress/mode=0' not in txt:
                if 'compress/mode=' in txt:
                    import re
                    txt = re.sub(r'compress/mode=\d+', 'compress/mode=0', txt)
                else:
                    txt = txt.rstrip('\n') + '\ncompress/mode=0\n'
                with open(imp, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(txt)
                changed += 1
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='', help='comma separated asset names (builder names)')
    ap.add_argument('--jobs', type=int, default=min(12, os.cpu_count() or 4))
    ap.add_argument('--no-spectro', action='store_true')
    ap.add_argument('--no-analysis', action='store_true')
    ap.add_argument('--godot', action='store_true', help='run Godot --import and the headless test')
    args = ap.parse_args()
    reg = registry()
    names = [n for n in reg] if not args.only else [n.strip() for n in args.only.split(',') if n.strip()]
    for n in names:
        if n not in reg:
            sys.exit(f'unknown asset {n!r}; known: {", ".join(sorted(reg))}')
    t0 = time.time()
    built = []
    # heavy jobs first for better packing
    order = sorted(names, key=lambda n: (reg[n][1] == 'sfx', n))
    with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        futs = {ex.submit(build_one, n, *reg[n]): n for n in order}
        failed = []
        for fu in as_completed(futs):
            try:
                r = fu.result()
            except Exception as e:  # report and continue with the other assets
                import traceback
                failed.append(futs[fu])
                print(f'  FAILED {futs[fu]}: {e!r}')
                traceback.print_exception(e)
                continue
            built.append(r)
            print(f"  built {r['name']:<22} {r['seconds']:>6.1f}s  -> {len(r['files'])} file(s)", flush=True)
    print(f'synthesis done in {time.time() - t0:.1f}s' + (f'  FAILED: {failed}' if failed else ''))
    n_imp = ensure_import_files()
    print(f'.import files written/patched: {n_imp}')
    if not args.no_analysis:
        import analyze
        analyze.ensure_preview_dir()
        files = [(f['name'], f['path'], reg[r['name']][1]) for r in built for f in r['files']]
        spectro_kinds = set() if args.no_spectro else {'music', 'amb'}
        jobs = []
        with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as ex:
            for (nm, p, kind) in files:
                jobs.append(ex.submit(_analyze_job, nm, p, kind in spectro_kinds or nm == 'fire_crackle_loop',
                                      kind in ('music', 'amb')))
            results = [j.result() for j in jobs]
        rows = update_analysis(results)
        print_table(results)
        if not args.no_spectro and any(reg[r['name']][1] == 'sfx' for r in built):
            sfx_dir = os.path.join(AUDIO, 'sfx')
            sheet = [os.path.join(sfx_dir, f) for f in sorted(os.listdir(sfx_dir))
                     if f.endswith('.wav') and 'loop' not in f]
            analyze.render_sheet(sheet, os.path.join(analyze.PREVIEW, 'sfx_sheet.png'), cols=5, cw=300, chh=130)
        update_manifest_doc(rows)
    if args.godot:
        run_godot()
    print(f'total {time.time() - t0:.1f}s')


def _analyze_job(name: str, path: str, spectro: bool, bands: bool) -> dict:
    import analyze
    r = analyze.analyze_file(path)
    r['name'] = name
    if bands:
        b = analyze.band_shares(path)
        r['lufs_approx'] = float(b.pop('lufs_approx'))
        r['band_energy_pct'] = {k: float(v) for k, v in b.items()}
    if spectro:
        analyze.render_spectrogram(path, os.path.join(analyze.PREVIEW, name + '.png'),
                                   f"{name}   RMS {r['rms_dbfs']} dBFS   peak {r['peak_dbfs']} dBFS   {r['seconds']} s")
    return r


DOC = os.path.join(ROOT, 'documentation', 'asset_manifest_parts', 'audio.md')
MARK_A = '<!-- metrics:begin (written by tools/audiogen/build_all.py) -->'
MARK_B = '<!-- metrics:end -->'


def update_manifest_doc(rows: list[dict]) -> None:
    """Rewrite the measured-levels table inside documentation/asset_manifest_parts/audio.md."""
    if not os.path.exists(DOC):
        return
    txt = open(DOC, encoding='utf-8').read()
    if MARK_A not in txt or MARK_B not in txt:
        return
    lines = ['| file | ch | s | loop (frames) | RMS dBFS | max 400 ms RMS | peak dBFS | true peak | clipped | DC | >16 kHz dB | seam (jump x median step / HF pct / curvature pct) |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: r['file']):
        loop = f"{r['loop'][0]}..{r['loop'][1]}" if r.get('loop') else '-'
        seam = (f"{r['seam_jump_vs_median_step']} / p{r['seam_hf_percentile']} / p{r['seam_curvature_percentile']}"
                if r.get('loop') else '-')
        dc = max(abs(v) for v in r['dc_offset'])
        lines.append(f"| {r['file'].replace('assets/audio/', '')} | {r['channels']} | {r['seconds']} | {loop} | "
                     f"{r['rms_dbfs']} | {r['max_rms400ms_dbfs']} | {r['peak_dbfs']} | {r['true_peak_dbfs']} | "
                     f"{r['clipped_samples']} | {dc:.1e} | {r['hf_above_16k_db']} | {seam} |")
    a = txt.index(MARK_A) + len(MARK_A)
    b = txt.index(MARK_B)
    txt = txt[:a] + '\n' + '\n'.join(lines) + '\n' + txt[b:]
    with open(DOC, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)


def update_analysis(results: list[dict]) -> None:
    import analyze
    p = os.path.join(analyze.PREVIEW, 'analysis.json')
    data = {}
    if os.path.exists(p):
        try:
            data = {r['name']: r for r in json.load(open(p, encoding='utf-8'))}
        except Exception:
            data = {}
    for r in results:
        data[r['name']] = r
    rows = [data[k] for k in sorted(data)]
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=1)
    # small runtime manifest (loop points etc.) next to the assets
    man = {}
    for r in rows:
        kind = r['file'].split('/')[-2]
        man[r['name']] = {'path': 'res://' + r['file'], 'kind': kind, 'seconds': r['seconds'],
                          'channels': r['channels'], 'loop': r['loop'], 'rms_dbfs': r['rms_dbfs'],
                          'peak_dbfs': r['peak_dbfs']}
    with open(os.path.join(AUDIO, 'audio_manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(man, f, indent=1)
    return rows


def print_table(results: list[dict]) -> None:
    hdr = f"{'name':<22}{'ch':>3}{'sec':>8}{'RMS':>8}{'stRMS':>7}{'peak':>7}{'tpk':>7}{'clip':>5}{'dc':>9}{'>16k':>7}  seam"
    print(hdr)
    for r in sorted(results, key=lambda r: r['file']):
        seam = ''
        if r.get('loop'):
            seam = (f"jump {r['seam_jump_vs_median_step']}x  hf {r['seam_hf_ratio_vs_median']}x"
                    f" (p{r['seam_hf_percentile']})  curv p{r['seam_curvature_percentile']}")
        dc = max(abs(v) for v in r['dc_offset'])
        print(f"{r['name']:<22}{r['channels']:>3}{r['seconds']:>8.2f}{r['rms_dbfs']:>8.1f}{r['max_rms400ms_dbfs']:>7.1f}"
              f"{r['peak_dbfs']:>7.1f}{r['true_peak_dbfs']:>7.1f}{r['clipped_samples']:>5}{dc:>9.1e}{r['hf_above_16k_db']:>7.0f}  {seam}")


def run_godot() -> None:
    if not os.path.exists(GODOT):
        print('Godot console exe not found:', GODOT)
        return
    for attempt in range(3):
        p = subprocess.run([GODOT, '--headless', '--path', ROOT, '--import'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=900)
        errs = [ln for ln in (p.stdout + p.stderr).splitlines() if 'ERROR' in ln and 'audio' in ln.lower()]
        print(f'godot --import exit {p.returncode}; audio-related errors: {len(errs)}')
        for e in errs[:20]:
            print('   ', e)
        if p.returncode == 0:
            break
    p = subprocess.run([GODOT, '--headless', '--path', ROOT, '--script', 'res://tools/audiogen/test_audio_headless.gd'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    out = (p.stdout + p.stderr).splitlines()
    for ln in out[-60:]:
        print('   ', ln)
    print('headless audio test exit code', p.returncode)


if __name__ == '__main__':
    main()
