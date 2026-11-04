"""Offline Python tests. No UE5 rendering or gameplay tests are run here."""
import unittest
import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.simulate_slice import StoryRuntime, StoryError, play_route
from tools.validate_v3 import validate, load_data


class TestAuthoringData(unittest.TestCase):
    def test_schema(self):
        report=validate(); self.assertEqual(report['quests'],2)
        self.assertEqual(report['scenes'],3)

    def test_detect_invalid_effect(self):
        data=load_data()
        data['quests']['quests'][0]['objectives'][-1]['choices'][0]['effects']['not_a_flag']={'delta':1}
        with self.assertRaises(ValueError): validate(data)

    def test_detect_objective_cycle(self):
        data=load_data()
        a=data['quests']['quests'][0]['objectives']
        a[0]['requires']=['a1_choose']
        with self.assertRaises(ValueError): validate(data)


class TestStateMachine(unittest.TestCase):
    def test_newgame(self):
        r=StoryRuntime()
        self.assertEqual(r.available(), ['a1_talk_irina'])
        self.assertEqual(r.state['current_scene'], 'L_A1_Railyard')
        self.assertEqual(r.state['flags']['irina_trust'],0)

    def test_four_branch_combinations(self):
        for a,af in [('share_with_irina','irina_trust'),('keep_private','alexei_secrecy')]:
            for m,mf in [('preserve_evidence','matthias_evidence'),('request_explanation','office_suspicion')]:
                with self.subTest(a=a,m=m):
                    r=play_route(a,m)
                    self.assertEqual(r.state['flags'][af],1)
                    self.assertEqual(r.state['flags'][mf],1)
                    self.assertEqual(r.state['completed_events'],['a1_completed','m1_completed','slice_completed'])
                    self.assertTrue(r.state['flags']['slice_finished'])
                    self.assertEqual(len(r.state['completed_objectives']),11)
                    self.assertEqual(len(r.state['inventory']),6)
                    self.assertEqual(r.state['active_character'],'none')

    def test_gate_and_invalid_choice(self):
        r=StoryRuntime()
        with self.assertRaises(StoryError):r.perform('a1_solve_signal')
        with self.assertRaises(StoryError):r.perform('a1_talk_irina','some-choice')
        r.perform('a1_talk_irina')
        r.perform('a1_inspect_seal')
        with self.assertRaises(StoryError):r.perform('a1_solve_signal')
        r.perform('a1_inspect_timetable');r.perform('a1_solve_signal');r.perform('a1_inspect_ledger')
        with self.assertRaises(StoryError):r.perform('a1_choose','invalid_choice')
        r.perform('a1_choose','share_with_irina')
        self.assertEqual(r.state['current_scene'],'L_M1_Archive')
        self.assertEqual(r.state['active_character'],'matthias')

    def test_idempotence_and_no_double_flag(self):
        r=play_route(); before=r.state['flags']['irina_trust']
        with self.assertRaises(StoryError):r.perform('a1_choose','share_with_irina')
        r.finale(); self.assertEqual(before,r.state['flags']['irina_trust'])
        self.assertEqual(r.state['completed_events'].count('slice_completed'),1)

    def test_save_reload(self):
        r=StoryRuntime();r.perform('a1_talk_irina');r.perform('a1_inspect_seal')
        snap=r.save_json(); other=StoryRuntime();other.load_json(snap)
        self.assertEqual(other.save_json(),snap)
        self.assertEqual(other.available(),['a1_inspect_timetable'])

    def test_save_reload_at_protagonist_boundary(self):
        r=StoryRuntime()
        for o in ['a1_talk_irina','a1_inspect_seal','a1_inspect_timetable','a1_solve_signal','a1_inspect_ledger']:
            r.perform(o)
        r.perform('a1_choose','keep_private')
        other=StoryRuntime();other.load_json(r.save_json())
        self.assertEqual(other.state['active_character'],'matthias')
        self.assertEqual(set(other.available()),{'m1_inspect_plan_a','m1_inspect_plan_b'})
        self.assertEqual(other.state['flags']['alexei_secrecy'],1)

    def test_skip_has_no_state_effect(self):
        a=play_route(skip=False); b=play_route(skip=True)
        self.assertEqual(a.save_json(),b.save_json())

    def test_migrate_v1(self):
        r=StoryRuntime(); legacy={'save_version':1,'flags':{'irina_trust':1},'completed_objectives':['a1_talk_irina'], 'completed_events':[],'inventory':[]}
        state=r.load_json(json.dumps(legacy))
        self.assertEqual(state['save_version'],2)
        self.assertEqual(state['flags']['irina_trust'],1)
        self.assertEqual(state['flags']['matthias_evidence'],0)
        self.assertEqual(state['active_character'],'alexei')

    def test_reject_corrupt_save(self):
        r=StoryRuntime(); save=json.loads(r.save_json())
        save['flags']['irina_trust']=999
        with self.assertRaises(StoryError):r.load_json(json.dumps(save))
        save=json.loads(r.save_json());save['current_scene']='not_a_map'
        with self.assertRaises(StoryError):r.load_json(json.dumps(save))

    def test_newgame_restarts_and_fixtures(self):
        r=play_route('keep_private','request_explanation')
        r.start_new()
        self.assertEqual(r.state['completed_events'],[])
        self.assertEqual(r.state['flags']['office_suspicion'],0)
        self.assertEqual(r.available(),['a1_talk_irina'])


if __name__=='__main__':unittest.main()
