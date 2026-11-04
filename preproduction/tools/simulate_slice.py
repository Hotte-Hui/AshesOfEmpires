#!/usr/bin/env python3
"""Deterministic portable quest-state reference; NOT UE5 code or 3D gameplay."""
import json
import sys
from pathlib import Path
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'v3'


def read(name):
    return json.loads((DATA / (name + '.json')).read_text(encoding='utf-8'))


class StoryError(ValueError):
    pass


class StoryRuntime:
    def __init__(self):
        self.flag_def = read('flags')
        self.quests = read('quests')['quests']
        self.scene_defs = read('scenes')['scenes']
        self.defined_items = {i['id'] for i in read('items')['items']}
        self.obj_index = {o['id']:(q,o) for q in self.quests for o in q['objectives']}
        self.start_new()

    def start_new(self):
        self.state = dict(save_version=self.flag_def['save_version'],
                          flags={k: v['default'] for k,v in self.flag_def['flags'].items()},
                          completed_objectives=[], completed_events=[], inventory=[],
                          choice_history={}, current_scene='L_A1_Railyard',active_character='alexei')
        return deepcopy(self.state)

    def available(self):
        out = []
        finished = set(self.state['completed_objectives'])
        events = set(self.state['completed_events'])
        for q in self.quests:
            if q['scene'] != self.state['current_scene'] or not set(q.get('requires_events', [])) <= events:
                continue
            for obj in q['objectives']:
                if obj['id'] not in finished and set(obj.get('requires', [])) <= finished:
                    out.append(obj['id'])
        return out

    def _apply_effects(self,effects):
        for name, spec in effects.items():
            meta = self.flag_def['flags'][name]
            if meta['type']=='boolean':
                self.state['flags'][name] = spec['set']
            else:
                value = self.state['flags'][name] + spec['delta']
                self.state['flags'][name] = min(meta['max'],max(meta['min'],value))

    def perform(self, objective_id, choice_id=None):
        if objective_id not in self.obj_index:
            raise StoryError(f'Unknown objective: {objective_id}')
        if objective_id not in self.available():
            raise StoryError(f'Objective locked or already complete: {objective_id}')
        q,obj=self.obj_index[objective_id]
        if obj['type']=='choice':
            matches=[c for c in obj['choices'] if c['id']==choice_id]
            if len(matches)!=1:
                raise StoryError(f'A valid choice is required for {objective_id}')
            effects=matches[0]['effects']
        else:
            if choice_id is not None:
                raise StoryError(f'{objective_id} does not accept a choice')
            effects=obj.get('effects',{})
        # Transactional: all validations above precede state mutation.
        self._apply_effects(effects)
        self.state['completed_objectives'].append(objective_id)
        if obj.get('grant_item') not in (None,*self.state['inventory']):
            self.state['inventory'].append(obj['grant_item'])
        if obj['type']=='choice':
            self.state['choice_history'][objective_id]=choice_id
        ids={o['id'] for o in q['objectives']}
        if ids <= set(self.state['completed_objectives']):
            self._complete_event(q['completion_event'])
        return deepcopy(self.state)

    def _complete_event(self,event):
        if event not in self.state['completed_events']:
            self.state['completed_events'].append(event)
        if event == 'a1_completed':
            self.state['current_scene']='L_M1_Archive'
            self.state['active_character']='matthias'
        elif event == 'm1_completed':
            self.state['current_scene']='L_X1_Montage'
            self.state['active_character']='none'

    def finale(self, skip=False):
        if self.state['current_scene']!='L_X1_Montage':
            raise StoryError('Finale locked; complete both investigations')
        # Skip is presentation only; it cannot remove mandatory story state.
        self._complete_event('slice_completed')
        self._apply_effects({'slice_finished':{'set':True}})
        return deepcopy(self.state)

    def save_json(self):
        return json.dumps(self.state,ensure_ascii=False,indent=2,sort_keys=True)

    def load_json(self,text):
        state=json.loads(text)
        version=state.get('save_version',1)
        if version not in (1,2):
            raise StoryError('Unsupported save version')
        if not isinstance(state.get('flags'),dict):
            raise StoryError('Save missing flags')
        canonical={k:v['default'] for k,v in self.flag_def['flags'].items()}
        for name,val in state['flags'].items():
            if name not in canonical:
                if version==1:  # old files may have removed flags
                    continue
                raise StoryError(f'Unknown flag: {name}')
            schema=self.flag_def['flags'][name]
            if schema['type']=='boolean':
                if type(val) is not bool: raise StoryError(f'Flag {name} invalid bool')
            else:
                if type(val) is not int or not schema['min'] <= val <= schema['max']:
                    raise StoryError(f'Flag {name} invalid integer')
            canonical[name]=val
        events=state.get('completed_events',[])
        objectives=state.get('completed_objectives',[])
        inventory=state.get('inventory',[])
        choices=state.get('choice_history',{})
        if not all(isinstance(v,list) for v in (events,objectives,inventory)) or not isinstance(choices,dict):
            raise StoryError('Invalid saved collections')
        if len(events)!=len(set(events)) or len(objectives)!=len(set(objectives)):
            raise StoryError('Duplicated progress entries')
        if not set(events)<=set(self.flag_def['events']) or not set(objectives)<=set(self.obj_index) or not set(inventory)<=self.defined_items:
            raise StoryError('Unknown progression identifier')
        scene=state.get('current_scene')
        if not scene:
            scene='L_X1_Montage' if 'm1_completed' in events else 'L_M1_Archive' if 'a1_completed' in events else 'L_A1_Railyard'
        allowed_scenes={s['id'] for s in self.scene_defs}
        if scene not in allowed_scenes: raise StoryError('Unknown scene')
        expected_character={s['id']:s['protagonist'] for s in self.scene_defs}[scene]
        if version==2 and state.get('active_character',expected_character)!=expected_character:
            raise StoryError('Scene/character mismatch')
        for objective,choice in choices.items():
            if objective not in self.obj_index or objective not in objectives:
                raise StoryError('Dangling choice history')
            obj=self.obj_index[objective][1]
            if obj['type']!='choice' or choice not in {x['id'] for x in obj['choices']}:
                raise StoryError('Invalid saved choice')
        self.state=dict(save_version=2,flags=canonical,completed_objectives=list(objectives),
                        completed_events=list(events),inventory=list(inventory),choice_history=dict(choices),
                        current_scene=scene,active_character=expected_character)
        return deepcopy(self.state)


def play_route(a1='share_with_irina',m1='preserve_evidence',skip=False):
    game=StoryRuntime()
    order=['a1_talk_irina','a1_inspect_seal','a1_inspect_timetable','a1_solve_signal','a1_inspect_ledger',
           'a1_choose','m1_inspect_plan_a','m1_inspect_plan_b','m1_align_plans','m1_talk_emil','m1_choose']
    for objective in order:
        game.perform(objective, {'a1_choose':a1,'m1_choose':m1}.get(objective))
    game.finale(skip=skip)
    return game


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--demo':
        game=play_route()
        print('DEMO REFERENCE SIMULATION (not Unreal gameplay)')
        print('Final scene:',game.state['current_scene'])
        print('Events:',', '.join(game.state['completed_events']))
        print('Choices:',game.state['choice_history'])
        print('Evidence:',', '.join(game.state['inventory']))
        print('Saved state (first 300 characters):',game.save_json()[:300])
    else:
        print('Usage: python tools/simulate_slice.py --demo')
