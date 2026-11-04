#!/usr/bin/env python3
"""Auditable offline story reference v4 (stdlib only). NOT UE5 gameplay.

All player-driven actions are checked against canonical data/v3 IDs. Dialogues and
puzzles require completion of their actual interaction paths; simply declaring
an objective complete is deliberately impossible through the public API.
"""
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'v3'
FORMAT = 'ashes_of_empires_story_reference_v4'
VERSION = 3


def read(stem):
    return json.loads((DATA / (stem + '.json')).read_text(encoding='utf-8'))


class StoryError(ValueError):
    pass


class StoryEngine:
    def __init__(self):
        self.flags_def = read('flags')['flags']
        self.quests = read('quests')['quests']
        self.quests_def = read('quests')
        self.scenes = {s['id']: s for s in read('scenes')['scenes']}
        self.start_scene = read('scenes')['start_scene']
        self.items = {x['id']: x for x in read('items')['items']}
        self.puzzles = {x['id']: x for x in read('puzzles')['puzzles']}
        self.dialogues = {x['id']: x for x in read('dialogue')['conversations']}
        self.sequences = read('cinematics')['sequences']
        self.objectives = {o['id']: (q, o) for q in self.quests for o in q['objectives']}
        self.new_game()

    def new_game(self):
        self.state = {
            'format': FORMAT,
            'save_version': VERSION,
            'flags': {k: v['default'] for k, v in self.flags_def.items()},
            'completed_objectives': [], 'completed_events': [], 'inventory': [],
            'choice_history': {}, 'current_scene': self.start_scene,
            'active_character': self.scenes[self.start_scene]['protagonist'],
            'dialogue_progress': {}, 'puzzle_attempts': {},
            'cinematics_seen': [], 'finale_viewed': False,
        }
        return self.snapshot()

    def snapshot(self):
        return deepcopy(self.state)

    def available(self):
        done = set(self.state['completed_objectives'])
        ev = set(self.state['completed_events'])
        result = []
        for q in self.quests:
            if q['scene'] != self.state['current_scene'] or not set(q.get('requires_events', [])) <= ev:
                continue
            for obj in q['objectives']:
                if obj['id'] not in done and set(obj.get('requires', [])) <= done:
                    result.append(obj['id'])
        return result

    def _require(self, objective_id, kind):
        if objective_id not in self.objectives:
            raise StoryError('Unknown objective: ' + str(objective_id))
        q, obj = self.objectives[objective_id]
        if obj['type'] != kind:
            raise StoryError(f'{objective_id}: expected {kind}, got {obj["type"]}')
        if objective_id not in self.available():
            raise StoryError(f'{objective_id}: locked, wrong scene, or already completed')
        return q, obj

    def _apply_effects(self, effects):
        for name, spec in effects.items():
            meta = self.flags_def[name]
            if meta['type'] == 'boolean':
                self.state['flags'][name] = spec['set']
            else:
                new = self.state['flags'][name] + spec['delta']
                self.state['flags'][name] = max(meta['min'], min(meta['max'], new))

    def _queue_shots(self, trigger_type, trigger_id):
        # Order is authored in cinematics.json. A trigger is committed once.
        # Sequence IDs are NOT gameplay completion gates.
        return [s['id'] for s in self.sequences if s.get(trigger_type) == trigger_id]

    def _commit(self, objective_id, effects=None, choice_id=None):
        q, obj = self.objectives[objective_id]
        self._apply_effects(effects if effects is not None else obj.get('effects', {}))
        self.state['completed_objectives'].append(objective_id)
        item = obj.get('grant_item')
        if item and item not in self.state['inventory']:
            self.state['inventory'].append(item)
        if choice_id is not None:
            self.state['choice_history'][objective_id] = choice_id
        if all(o['id'] in self.state['completed_objectives'] for o in q['objectives']):
            event = q['completion_event']
            if event not in self.state['completed_events']:
                self.state['completed_events'].append(event)
                scene = self.scenes[q['scene']]
                assert scene['exit_on_event'] == event
                self.state['current_scene'] = scene['next_scene']
                self.state['active_character'] = self.scenes[scene['next_scene']]['protagonist']
        return self.snapshot()

    def inspect(self, objective_id):
        self._require(objective_id, 'inspect')
        return self._commit(objective_id)

    def start_dialogue(self, objective_id):
        _, obj = self._require(objective_id, 'dialogue')
        if objective_id not in self.state['dialogue_progress']:
            self.state['dialogue_progress'][objective_id] = self.dialogues[obj['dialogue_id']]['entry_node']
        return self.current_dialogue_line(objective_id)

    def current_dialogue_line(self, objective_id):
        if objective_id not in self.state['dialogue_progress']:
            raise StoryError('Dialogue not started')
        _, obj = self._require(objective_id, 'dialogue')
        node_id = self.state['dialogue_progress'][objective_id]
        return deepcopy(next(n for n in self.dialogues[obj['dialogue_id']]['nodes'] if n['id'] == node_id))

    def advance_dialogue(self, objective_id):
        line = self.current_dialogue_line(objective_id)
        if line.get('end', False):
            del self.state['dialogue_progress'][objective_id]
            self._commit(objective_id)
            return None
        self.state['dialogue_progress'][objective_id] = line['next']
        return self.current_dialogue_line(objective_id)

    def puzzle_hint_available(self, objective_id):
        _, obj = self._require(objective_id, 'puzzle')
        puzzle = self.puzzles[obj['puzzle_id']]
        return self.state['puzzle_attempts'].get(objective_id, 0) >= puzzle['hint_after_attempts']

    def solve_puzzle(self, objective_id, answer):
        _, obj = self._require(objective_id, 'puzzle')
        puzzle = self.puzzles[obj['puzzle_id']]
        if not set(puzzle['clue_item_ids']) <= set(self.state['inventory']):
            raise StoryError('Missing clues for puzzle')
        if puzzle['type'] == 'symbol_order':
            if not isinstance(answer, list) or not all(isinstance(x, str) for x in answer):
                raise StoryError('Symbol puzzle expects a list of symbols')
            correct = answer == puzzle['solution']
        elif puzzle['type'] == 'overlay_alignment':
            if not isinstance(answer, dict) or set(answer) != set(puzzle['solution']):
                raise StoryError('Overlay expects rotation_steps, offset_x, offset_y')
            if any(type(v) is not int for v in answer.values()):
                raise StoryError('Overlay coordinates must be integers')
            correct = answer == puzzle['solution']
        else:
            raise StoryError('Unsupported puzzle type')
        if correct:
            self._commit(objective_id)
            return True
        self.state['puzzle_attempts'][objective_id] = self.state['puzzle_attempts'].get(objective_id, 0) + 1
        return False

    def choose(self, objective_id, choice_id):
        _, obj = self._require(objective_id, 'choice')
        matches = [c for c in obj['choices'] if c['id'] == choice_id]
        if len(matches) != 1:
            raise StoryError('Invalid choice ID')
        return self._commit(objective_id, matches[0].get('effects', {}), choice_id)

    def pending_cinematics(self):
        seen = set(self.state['cinematics_seen'])
        obj = set(self.state['completed_objectives'])
        ev = set(self.state['completed_events'])
        return [s['id'] for s in self.sequences if s['id'] not in seen and (
            s.get('trigger_objective') in obj or s.get('trigger_event') in ev)]

    def consume_cinematic(self, cinematic_id, skipped=False):
        if cinematic_id not in self.pending_cinematics():
            raise StoryError('Cinematic not unlocked or already consumed')
        self.state['cinematics_seen'].append(cinematic_id)
        return self.snapshot()

    def finale(self, skipped=False):
        required = set(self.quests_def['slice_end_requires'])
        if self.state['current_scene'] != 'L_X1_Montage' or not required <= set(self.state['completed_events']):
            raise StoryError('Finale locked')
        if 'slice_completed' not in self.state['completed_events']:
            self.state['completed_events'].append('slice_completed')
            self.state['flags']['slice_finished'] = True
        self.state['finale_viewed'] = True
        return self.snapshot()

    def save_json(self):
        return json.dumps(self.state, ensure_ascii=False, sort_keys=True, indent=2)

    def load_json(self, raw):
        """Transactional load with replay-based anti-corruption validation.

        Accepts v0.3 save_version=2 as legacy migration, never fabricates proof of
        future objectives. v4 saves preserve mid-dialogue and puzzle-attempt state.
        """
        if len(raw.encode('utf-8')) > 128 * 1024:
            raise StoryError('Save too large')
        try:
            source = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise StoryError('Malformed JSON') from exc
        if not isinstance(source, dict):
            raise StoryError('Expected JSON object')
        ver = source.get('save_version')
        if type(ver) is not int or ver not in (2, 3):
            raise StoryError('Unsupported save version')
        if ver == 3 and source.get('format') != FORMAT:
            raise StoryError('Unknown save format')
        # Replay objective history to establish a valid state/scene/event/flag basis.
        replay = StoryEngine()
        actions = source.get('completed_objectives')
        choices = source.get('choice_history')
        if not isinstance(actions, list) or not all(isinstance(a,str) for a in actions):
            raise StoryError('Malformed completed objectives')
        if len(set(actions)) != len(actions):
            raise StoryError('Duplicate objectives')
        if not isinstance(choices,dict):
            raise StoryError('Malformed choice history')
        for objective_id in actions:
            if objective_id not in replay.objectives:
                raise StoryError('Unknown objective')
            q,obj = replay.objectives[objective_id]
            if objective_id not in replay.available():
                raise StoryError('Invalid quest order or scene transition')
            if obj['type'] == 'choice':
                selected = choices.get(objective_id)
                if selected not in {c['id'] for c in obj['choices']}:
                    raise StoryError('Choice missing/invalid')
                replay.choose(objective_id, selected)
            elif obj['type'] == 'inspect':
                replay.inspect(objective_id)
            elif obj['type'] == 'dialogue':
                replay.start_dialogue(objective_id)
                while objective_id in replay.state['dialogue_progress']:
                    replay.advance_dialogue(objective_id)
            elif obj['type'] == 'puzzle':
                replay.solve_puzzle(objective_id, deepcopy(replay.puzzles[obj['puzzle_id']]['solution']))
        if set(choices) != {o for o in actions if replay.objectives[o][1]['type']=='choice'}:
            raise StoryError('Choice history mismatch')
        if 'slice_completed' in source.get('completed_events', []):
            replay.finale()
        # Compare every authoritative component, refusing contradictory saves.
        for key in ('flags', 'completed_objectives','completed_events','inventory','choice_history','current_scene','active_character'):
            a,b=source.get(key),replay.state[key]
            # Legacy v2 could omit optional unused fields but must not contradict progress.
            if ver == 2 and key == 'flags' and isinstance(a,dict):
                a = {**{k: meta['default'] for k,meta in self.flags_def.items()}, **a}
            if a != b:
                if key in ('completed_events', 'inventory') and isinstance(a,list) and set(a)==set(b) and len(a)==len(b):
                    continue
                raise StoryError('Inconsistent save field: ' + key)
        if ver == 3:
            p = source.get('dialogue_progress', {})
            attempts = source.get('puzzle_attempts', {})
            seen = source.get('cinematics_seen', [])
            viewed = source.get('finale_viewed', False)
            if not isinstance(p,dict) or not isinstance(attempts,dict) or not isinstance(seen,list) or type(viewed) is not bool:
                raise StoryError('Malformed presentation state')
            for objective, node in p.items():
                if objective not in replay.available() or replay.objectives[objective][1]['type']!='dialogue':
                    raise StoryError('Invalid dialogue cursor')
                dlg = replay.dialogues[replay.objectives[objective][1]['dialogue_id']]
                if node not in {n['id'] for n in dlg['nodes']}:
                    raise StoryError('Invalid dialogue node')
            for objective, count in attempts.items():
                if objective not in replay.objectives or replay.objectives[objective][1]['type']!='puzzle':
                    raise StoryError('Invalid puzzle counter')
                if type(count) is not int or count < 0 or count > 100000:
                    raise StoryError('Invalid attempt count')
            if len(seen)!=len(set(seen)) or not set(seen)<=set(s['id'] for s in self.sequences):
                raise StoryError('Invalid cinematic IDs')
            for seq in self.sequences:
                if seq['id'] in seen and not (seq.get('trigger_event') in replay.state['completed_events'] or seq.get('trigger_objective') in replay.state['completed_objectives']):
                    raise StoryError('Cinematic was not triggered')
            if viewed and 'slice_completed' not in replay.state['completed_events']:
                raise StoryError('Invalid finale viewed')
            replay.state.update(dialogue_progress=p,puzzle_attempts=attempts,cinematics_seen=seen,finale_viewed=viewed)
        self.state = replay.snapshot()
        return self.snapshot()


def play_verified_route(a1='share_with_irina', m1='preserve_evidence', skip=False):
    """Exercise authentic in-data puzzle and dialogue flows; no objective bypass."""
    game = StoryEngine()
    game.start_dialogue('a1_talk_irina')
    while 'a1_talk_irina' in game.state['dialogue_progress']:
        game.advance_dialogue('a1_talk_irina')
    game.inspect('a1_inspect_seal'); game.inspect('a1_inspect_timetable')
    game.solve_puzzle('a1_solve_signal', ['square','circle','triangle'])
    game.inspect('a1_inspect_ledger'); game.choose('a1_choose',a1)
    game.inspect('m1_inspect_plan_a'); game.inspect('m1_inspect_plan_b')
    game.solve_puzzle('m1_align_plans', {'rotation_steps':0,'offset_x':2,'offset_y':-1})
    game.start_dialogue('m1_talk_emil')
    while 'm1_talk_emil' in game.state['dialogue_progress']:
        game.advance_dialogue('m1_talk_emil')
    game.choose('m1_choose',m1)
    for seq in list(game.pending_cinematics()):
        game.consume_cinematic(seq, skipped=skip)
    game.finale(skipped=skip)
    return game


if __name__ == '__main__':
    r = play_verified_route()
    print('PASS verified end-to-end route:',r.state['completed_events'])
    print('Save size:',len(r.save_json().encode('utf-8')))
