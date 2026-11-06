"""env_keep -- an environment generator rewrites ITS files in a shared env folder and keeps everything else
(round 10, documentation/NEXT_STEPS.md §1 „generator hazard“; used by env_veltrava_hall.py, env_veltrava_station.py,
env_c3p2_quay.py).

The env folders are shared: walkers_r8.py writes walkers/ (anonymous variant sheets and their rigs), the station's
env_veltrava_station_thaw.py writes thaw/, the feel passes of rounds 8 and 9 added "actors" entries to scene.json
(AmbientWalkers, StationThaw) and may add rows to provenance.json.  The generators used to delete every PNG of their
folder first and to write scene.json / provenance.json from scratch, so a re-run dropped all of that.  Now a generator
  * removes before its run only the PNGs its own previous run recorded (the provenance.json rows of its family; a
    folder without such a record loses nothing) -- its renamed or dropped outputs still never linger, and the .import
    sidecars stay, so re-written files keep their UIDs;
  * merges its scene.json over the previous one: every key it writes is its own; a key it does not write stays where
    it stood; a list it shares with other writers (``actors``) keeps the old entries whose identity (``scene``) it
    does not produce itself;
  * merges provenance.json: its own rows plus the previous rows of other generators whose files still exist;
  * writes scene.json only when its content changed (a hand-formatted block keeps its form while nothing changes).
Pure stdlib, deterministic and byte-stable: a re-run of an unchanged generator leaves its folder byte-identical.

    py -3 -P tools/pixelgen/env_keep.py --selftest     # the rules above on a temporary folder
"""
from __future__ import annotations

import json
import os

PNG = '.png'
SHARED_LISTS = {'actors': 'scene'}   # scene.json lists other writers extend -> the key that identifies an entry


def read_json(path: str):
    """The JSON object at `path`, or None (missing, unreadable, not an object)."""
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def rel(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace('\\', '/')


def is_own(row: dict, family) -> bool:
    """A provenance row written by the generator family (a generator path prefix or a tuple of them)."""
    return str(row.get('generator', '')).startswith(family)


def own_pngs(env_dir: str, root: str, family) -> list:
    """PNGs (absolute paths) inside env_dir that the family's previous run recorded in env_dir/provenance.json."""
    prov = read_json(os.path.join(env_dir, 'provenance.json')) or {}
    env_rel = rel(env_dir, root) + '/'
    out = set()
    for r in prov.get('files', []):
        if isinstance(r, dict) and is_own(r, family):
            p = str(r.get('path', ''))
            if p.startswith(env_rel) and p.endswith(PNG) and '_preview/' not in p:
                out.add(os.path.join(root, *p.split('/')))
    return sorted(out)


def remove_own_pngs(env_dir: str, root: str, family) -> list:
    """Removes the PNGs the family's previous run wrote (nothing else; .import sidecars stay). Returns them."""
    gone = []
    for p in own_pngs(env_dir, root, family):
        if os.path.isfile(p):
            os.remove(p)
            gone.append(p)
    return gone


def png_stamps(env_dir: str) -> dict:
    """{path: mtime_ns} of every PNG under env_dir -- a file the run writes changes its stamp."""
    out = {}
    for r, _d, fs in os.walk(env_dir):
        for f in fs:
            if f.endswith(PNG):
                p = os.path.join(r, f)
                out[p] = os.stat(p).st_mtime_ns
    return out


def written_since(env_dir: str, before: dict) -> list:
    """PNGs under env_dir written since `before` (png_stamps): new or re-written ones."""
    return sorted(p for p, t in png_stamps(env_dir).items() if before.get(p) != t)


def merge_scene(new: dict, old, shared_lists: dict | None = None) -> dict:
    """The generator's manifest `new` over the previous scene.json `old`: the keys of `new` are the generator's (its
    values win); a key only `old` has stays, placed after the key that preceded it in `old`; each list of
    `shared_lists` ({key: identity field}) keeps the old entries whose identity no entry of `new` has, each at its old
    index (so an unchanged generator gives back the old order)."""
    if not isinstance(old, dict):
        return new
    shared_lists = SHARED_LISTS if shared_lists is None else shared_lists
    merged = dict(new)
    for key, ident in shared_lists.items():
        if isinstance(new.get(key), list) and isinstance(old.get(key), list):
            mine = {json.dumps(e.get(ident), sort_keys=True) for e in new[key] if isinstance(e, dict)}
            lst = list(new[key])
            for i, e in enumerate(old[key]):
                if isinstance(e, dict) and json.dumps(e.get(ident), sort_keys=True) not in mine:
                    lst.insert(min(i, len(lst)), e)
            merged[key] = lst
    tail: dict = {}
    anchor = None
    for k in old:
        if k in merged:
            anchor = k
        else:
            tail.setdefault(anchor, []).append(k)
    out = {k: old[k] for k in tail.get(None, [])}
    for k, v in merged.items():
        out[k] = v
        for k2 in tail.get(k, []):
            out[k2] = old[k2]
    return out


def write_json(path: str, obj: dict) -> bool:
    """Writes `obj` the way the generators do (UTF-8, LF, indent 1) -- unless the file already holds exactly that
    content in that order: then it stays byte for byte (blocks other writers formatted by hand keep their form).
    Returns whether it wrote."""
    old = None
    try:
        with open(path, encoding='utf-8') as f:
            old = json.load(f)
    except (OSError, ValueError):
        pass
    if old is not None and json.dumps(old, ensure_ascii=False) == json.dumps(obj, ensure_ascii=False):
        return False
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
    return True


def merge_rows(rows: list, old, family, root: str) -> list:
    """provenance.json "files": the generator's `rows` plus the rows of the previous file `old` that OTHER
    generators wrote, as long as their file still exists (sorted by path, like the generators write them)."""
    have = {str(r.get('path', '')) for r in rows}
    keep = []
    for r in (old or {}).get('files', []):
        if not isinstance(r, dict) or is_own(r, family):
            continue
        p = str(r.get('path', ''))
        if p and p not in have and os.path.exists(os.path.join(root, *p.split('/'))):
            keep.append(r)
    return sorted(list(rows) + keep, key=lambda r: str(r.get('path', '')))


def lf_json(paths) -> None:
    """Rewrites the JSON files among `paths` with LF line ends (the repo's form, .gitattributes) when a helper wrote
    them with the platform's."""
    for p in paths:
        if str(p).endswith('.json') and os.path.isfile(p):
            with open(p, 'rb') as f:
                b = f.read()
            if b'\r\n' in b:
                with open(p, 'wb') as f:
                    f.write(b.replace(b'\r\n', b'\n'))


def selftest() -> None:
    """The rules on a temporary folder: own stale PNGs go, foreign files / keys / list entries / rows stay."""
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        env = os.path.join(root, 'assets', 'environments', 'x')
        for d in ('props', 'walkers'):
            os.makedirs(os.path.join(env, d))

        def touch(r):
            with open(os.path.join(env, *r.split('/')), 'wb') as f:
                f.write(b'png')
        for r in ('room.png', 'props/old.png', 'props/hand.png', 'walkers/w_rig.png'):
            touch(r)
        fam = 'tools/pixelgen/env_x'
        rows = [{'path': 'assets/environments/x/' + r, 'generator': fam + g, 'content': ''}
                for r, g in (('room.png', '.py'), ('props/old.png', '_props.py'), ('scene.json', '.py'))]
        rows.append({'path': 'assets/environments/x/walkers/w_rig.png', 'generator': 'tools/pixelgen/walkers_r8.py',
                     'content': 'rig'})
        rows.append({'path': 'assets/environments/x/walkers/gone.png', 'generator': 'tools/pixelgen/walkers_r8.py',
                     'content': 'a file that no longer exists'})
        prov = os.path.join(env, 'provenance.json')
        with open(prov, 'w', encoding='utf-8') as f:
            json.dump({'files': rows}, f)
        gone = sorted(rel(p, env) for p in remove_own_pngs(env, root, fam))
        assert gone == ['props/old.png', 'room.png'], gone
        assert os.path.exists(os.path.join(env, 'props', 'hand.png')), 'a PNG nobody recorded stays'
        assert os.path.exists(os.path.join(env, 'walkers', 'w_rig.png')), 'another generator\'s PNG stays'
        before = png_stamps(env)
        touch('room.png')
        assert [rel(p, env) for p in written_since(env, before)] == ['room.png']
        kept = merge_rows([{'path': 'assets/environments/x/room.png', 'generator': fam + '.py', 'content': ''}],
                          read_json(prov), fam, root)
        assert [r['path'].rsplit('/', 1)[-1] for r in kept] == ['room.png', 'w_rig.png'], kept
        old = {'id': 'x', 'layers': [1], 'actors': [{'scene': 'hand.tscn'}, {'scene': 'gen.tscn', 'v': 0}],
               'hand_key': {'a': 1}, 'notes': 'n'}
        new = {'id': 'x', 'layers': [2], 'actors': [{'scene': 'gen.tscn', 'v': 1}], 'notes': 'n2'}
        m = merge_scene(new, old)
        assert list(m) == ['id', 'layers', 'actors', 'hand_key', 'notes'], list(m)
        assert m['actors'] == [{'scene': 'hand.tscn'}, {'scene': 'gen.tscn', 'v': 1}], m['actors']
        assert m['layers'] == [2] and m['notes'] == 'n2' and m['hand_key'] == {'a': 1}
        assert merge_scene({'id': 'x', 'actors': [{'scene': 'a'}]}, {'id': 'x', 'actors': [{'scene': 'a', 'v': 9}]}) \
            == {'id': 'x', 'actors': [{'scene': 'a'}]}, 'the generator owns the scenes it writes'
        sj = os.path.join(env, 'scene.json')
        with open(sj, 'w', encoding='utf-8', newline='\n') as f:
            f.write('{"id": "x", "pos": [0, 0]}')
        assert not write_json(sj, {'id': 'x', 'pos': [0, 0]}), 'same content: untouched'
        with open(sj, encoding='utf-8') as f:
            assert f.read() == '{"id": "x", "pos": [0, 0]}'
        assert write_json(sj, {'id': 'x', 'pos': [0, 1]}), 'new content: written'
    print('env_keep selftest: OK')


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv[1:]:
        selftest()
    else:
        print(__doc__)
