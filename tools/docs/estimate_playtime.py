"""Rough playtime estimate from the game data (no human measurement — documentation only).

Run:  py -3 -P tools/docs/estimate_playtime.py [--json]

Model (deliberately simple and conservative):
  * reading: 14 characters per second (German, typewriter text, a player who reads) + 0.6 s per line to advance
  * inspect / observe objective: 15 s; choice: 20 s; story puzzle: 100 s
  * walking: 1.4 × the level's playable width at 45 px/s (back and forth between objectives)
  * cinematics: measured lengths of the shipped sequences (constants below; Chapter 3 read from layout.json if present)
  * optional finds: their text + 8 s to walk there and look; chats: their lines; mini-games: 90 s each;
    history cards: their text; side tasks: their steps' texts + 30 s of walking per step
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CPS = 14.0
LINE_OVERHEAD = 0.6
WALK_SPEED = 45.0

# measured lengths (seconds) of the presentation pieces outside the walkable levels
CINEMATICS = {
    "LS_A1_ToM1": 43.0,
    "LS_M1_Hall": 24.0,
    "LS_M1_Parade": 47.0,
    "LS_X1_Final": 47.5,
    "LS_C3_Trains": 25.5,
    "LS_C3_ToHall": 6.0,
    "LS_C3_Close": 12.0,
    "end_card": 12.0,
    "credits_roll": 84.0,
}
LEVEL_INTRO = 7.0   # intro pan / chapter card per level


def _j(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_locale():
    strings = {}
    strings.update(_j(os.path.join(ROOT, "data", "v3", "locale_de.json")).get("strings", {}))
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "locale", "de_*.json"))):
        d = _j(p)
        strings.update(d.get("strings", d) if isinstance(d, dict) else {})
    return strings


def read_s(strings, key):
    t = strings.get(key, "")
    if not isinstance(t, str):
        return 0.0
    return len(t) / CPS + LINE_OVERHEAD


def level_widths():
    out = {}
    for tscn in glob.glob(os.path.join(ROOT, "scenes", "levels", "L_*.tscn")):
        lid = os.path.splitext(os.path.basename(tscn))[0]
        txt = open(tscn, encoding="utf-8").read()
        manifest = None
        for line in txt.splitlines():
            if line.startswith("art_manifest = "):
                manifest = line.split('"')[1].replace("res://", "")
        if not manifest:
            continue
        p = os.path.join(ROOT, manifest)
        if not os.path.exists(p):
            continue
        m = _j(p)
        ws = m.get("world_size")
        w = ws[0] if isinstance(ws, list) and ws else 0
        xs = []

        def collect(node):
            # walkable: one polygon [[x, y], ...], a list of polygons, or {"points": [...]} dictionaries
            if isinstance(node, dict):
                collect(node.get("points", []))
            elif isinstance(node, list):
                if len(node) >= 2 and all(isinstance(v, (int, float)) for v in node[:2]):
                    xs.append(float(node[0]))
                else:
                    for sub in node:
                        collect(sub)

        collect(m.get("walkable"))
        if xs:
            w = max(xs) - min(xs)
        out[lid] = float(w or 0)
    return out


def main():
    strings = load_locale()
    report = {"main": {}, "optional": {}}

    # ---- main path: story dialogue, objectives, walking, cinematics
    dlg = _j(os.path.join(ROOT, "data", "v3", "dialogue.json"))["conversations"]
    dlg_s = sum(read_s(strings, n.get("text_key", "")) for c in dlg for n in c.get("nodes", []))
    quests = _j(os.path.join(ROOT, "data", "v3", "quests.json"))["quests"]
    obj_s = 0.0
    scenes = set()
    for q in quests:
        scenes.add(q.get("scene"))
        for o in q.get("objectives", []):
            t = o.get("type")
            obj_s += {"inspect": 15.0, "observe": 15.0, "choice": 20.0, "puzzle": 100.0}.get(t, 0.0)
    widths = level_widths()
    walk_s = sum(1.4 * widths.get(s, 0.0) / WALK_SPEED for s in scenes if s)
    cin_s = sum(CINEMATICS.values()) + LEVEL_INTRO * len([s for s in scenes if s])
    report["main"] = {"dialogue": dlg_s, "objectives_and_puzzles": obj_s, "walking": walk_s, "cinematics_and_cards": cin_s}

    # ---- optional: finds, chats, mini-games, history cards, side tasks
    finds_s = chats_s = mg_s = cards_s = tasks_s = 0.0
    n_finds = n_chats = n_mg = n_cards = n_tasks = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "explore", "*.json"))):
        d = _j(p)
        ents = d.get("entries", [])
        if isinstance(ents, dict):
            ents = list(ents.values())
        for e in ents:
            if e.get("kind") == "chat":
                n_chats += 1
                chats_s += sum(read_s(strings, l.get("key", "")) for l in e.get("lines", [])) + 8.0
            else:
                n_finds += 1
                finds_s += read_s(strings, e.get("title_key", "")) + read_s(strings, e.get("text_key", "")) + 8.0
            if e.get("minigame"):
                n_mg += 1
                mg_s += 90.0
        cards = d.get("cards", [])
        if isinstance(cards, dict):
            cards = list(cards.values())
        for c in cards:
            n_cards += 1
            cards_s += read_s(strings, c.get("text_key", "")) + read_s(strings, c.get("title_key", ""))
        for t in d.get("tasks", []) or []:
            n_tasks += 1
            tasks_s += 30.0 * len(t.get("steps", []))
    report["optional"] = {"finds": finds_s, "chats": chats_s, "minigames": mg_s, "history_cards": cards_s, "side_tasks_walking": tasks_s}
    report["counts"] = {"finds": n_finds, "chats": n_chats, "minigames": n_mg, "history_cards": n_cards, "tasks": n_tasks,
                        "levels": sorted(s for s in scenes if s)}
    main_min = sum(report["main"].values()) / 60.0
    opt_min = sum(report["optional"].values()) / 60.0
    report["minutes"] = {"main_path": round(main_min, 1), "optional": round(opt_min, 1), "all": round(main_min + opt_min, 1)}
    if "--json" in sys.argv:
        print(json.dumps(report, indent=1, ensure_ascii=False))
        return
    print("Main path   %5.1f min  (%s)" % (main_min, ", ".join("%s %.1f" % (k, v / 60.0) for k, v in report["main"].items())))
    print("Optional    %5.1f min  (%s)" % (opt_min, ", ".join("%s %.1f" % (k, v / 60.0) for k, v in report["optional"].items())))
    print("Everything  %5.1f min" % (main_min + opt_min))
    print("Counts:", report["counts"])


if __name__ == "__main__":
    main()
