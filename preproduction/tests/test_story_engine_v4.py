"""Game-state reference regression tests; no UE5/GPU claims."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.story_engine_v4 import StoryEngine, StoryError, play_verified_route
from tools.simulate_slice import play_route as legacy_play


class StoryV4Tests(unittest.TestCase):
    def setUp(self):
        self.r=StoryEngine()

    def get_to_signal(self):
        self.r.start_dialogue('a1_talk_irina')
        while 'a1_talk_irina' in self.r.state['dialogue_progress']:
            self.r.advance_dialogue('a1_talk_irina')
        self.r.inspect('a1_inspect_seal'); self.r.inspect('a1_inspect_timetable')

    def test_fresh_gates(self):
        self.assertEqual(self.r.available(), ['a1_talk_irina'])
        with self.assertRaises(StoryError): self.r.inspect('a1_inspect_seal')
        with self.assertRaises(StoryError): self.r.solve_puzzle('a1_solve_signal', ['square','circle','triangle'])
        with self.assertRaises(StoryError): self.r.finale()

    def test_explicit_dialogue(self):
        line=self.r.start_dialogue('a1_talk_irina'); self.assertEqual(line['id'],'irina_01')
        self.assertEqual(self.r.current_dialogue_line('a1_talk_irina')['id'],'irina_01')
        self.assertNotIn('a1_talk_irina', self.r.state['completed_objectives'])
        count=0
        while 'a1_talk_irina' in self.r.state['dialogue_progress']:
            self.r.advance_dialogue('a1_talk_irina'); count+=1
        self.assertEqual(count, 5)
        self.assertIn('a1_talk_irina', self.r.state['completed_objectives'])
        with self.assertRaises(StoryError): self.r.advance_dialogue('a1_talk_irina')

    def test_dialogue_resume_exact_node(self):
        self.r.start_dialogue('a1_talk_irina'); self.r.advance_dialogue('a1_talk_irina')
        save=self.r.save_json(); s=StoryEngine();s.load_json(save)
        self.assertEqual(s.current_dialogue_line('a1_talk_irina')['id'],'alexei_01')
        self.assertNotIn('a1_talk_irina',s.state['completed_objectives'])

    def test_puzzle_wrong_then_hint(self):
        self.get_to_signal()
        self.assertFalse(self.r.puzzle_hint_available('a1_solve_signal'))
        self.assertFalse(self.r.solve_puzzle('a1_solve_signal', ['circle','square','triangle']))
        self.assertFalse(self.r.puzzle_hint_available('a1_solve_signal'))
        self.assertFalse(self.r.solve_puzzle('a1_solve_signal', ['circle','triangle','square']))
        self.assertTrue(self.r.puzzle_hint_available('a1_solve_signal'))
        self.assertEqual(self.r.state['puzzle_attempts']['a1_solve_signal'],2)
        self.assertTrue(self.r.solve_puzzle('a1_solve_signal', ['square','circle','triangle']))
        self.assertTrue(self.r.state['flags']['signal_restored'])
        with self.assertRaises(StoryError): self.r.solve_puzzle('a1_solve_signal', ['square','circle','triangle'])

    def test_puzzle_payload_is_typed(self):
        self.get_to_signal()
        for invalid in [1,'square,circle,triangle',{'a':0},[False,'circle','triangle']]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(StoryError): self.r.solve_puzzle('a1_solve_signal', invalid)

    def test_valid_branch_combinations(self):
        for a in ('share_with_irina','keep_private'):
            for m in ('preserve_evidence','request_explanation'):
                with self.subTest(a=a,m=m):
                    r=play_verified_route(a,m)
                    self.assertEqual(r.state['completed_events'],['a1_completed','m1_completed','slice_completed'])
                    self.assertEqual(len(r.state['inventory']),6)
                    self.assertEqual(len(r.state['completed_objectives']),11)
                    self.assertEqual(r.state['flags']['slice_finished'],True)
                    self.assertEqual(r.state['choice_history'],{'a1_choose':a,'m1_choose':m})
                    self.assertEqual(r.pending_cinematics(),[])
                    reload=StoryEngine();self.assertEqual(reload.load_json(r.save_json()),r.snapshot())

    def test_fade_skip_does_not_skip_story(self):
        a=play_verified_route(skip=False)
        b=play_verified_route(skip=True)
        self.assertEqual(a.snapshot(),b.snapshot())

    def test_cinematics_available_only_when_triggered(self):
        with self.assertRaises(StoryError): self.r.consume_cinematic('LS_A1_ToM1')
        self.get_to_signal()
        self.r.solve_puzzle('a1_solve_signal',['square','circle','triangle'])
        self.r.inspect('a1_inspect_ledger');self.r.choose('a1_choose','share_with_irina')
        self.assertEqual(self.r.pending_cinematics(),['LS_A1_ToM1'])
        self.r.consume_cinematic('LS_A1_ToM1', skipped=True)
        self.assertEqual(self.r.pending_cinematics(),[])
        with self.assertRaises(StoryError): self.r.consume_cinematic('LS_A1_ToM1')

    def test_invalid_choice_no_mutation(self):
        self.get_to_signal();self.r.solve_puzzle('a1_solve_signal',['square','circle','triangle']);self.r.inspect('a1_inspect_ledger')
        original=self.r.snapshot()
        with self.assertRaises(StoryError): self.r.choose('a1_choose','unspecified')
        self.assertEqual(self.r.snapshot(),original)

    def test_invalid_save_is_atomic(self):
        original=self.r.snapshot()
        cases=['','[]','{}','{"save_version":999}','{'+'x'*200000+'}']
        for case in cases:
            with self.subTest(case=case[:20]):
                with self.assertRaises(StoryError): self.r.load_json(case)
                self.assertEqual(self.r.snapshot(),original)

    def test_bad_save_corruption_detected(self):
        valid=json.loads(play_verified_route().save_json())
        edits=[
            ('flags',lambda x: x['flags'].__setitem__('c17_confirmed', False)),
            ('events',lambda x: x['completed_events'].remove('a1_completed')),
            ('unknown_item',lambda x: x['inventory'].append('forged')),
            ('wrong_scene',lambda x: x.__setitem__('current_scene','L_A1_Railyard')),
            ('character',lambda x: x.__setitem__('active_character','alexei')),
            ('tampered_choice',lambda x: x['choice_history'].__setitem__('m1_choose','fake')),
            ('dup_objective',lambda x: x['completed_objectives'].append('a1_choose')),
            ('bad_sequence',lambda x: x['cinematics_seen'].append('invalid')),
            ('unexpected_finale',lambda x: x.__setitem__('finale_viewed','yes')),
        ]
        for label,mutation in edits:
            with self.subTest(label=label):
                record=deepcopy(valid);mutation(record)
                with self.assertRaises(StoryError): self.r.load_json(json.dumps(record))

    def test_v03_save_migration(self):
        old=legacy_play().save_json()
        r=StoryEngine();state=r.load_json(old)
        self.assertEqual(state['save_version'],3)
        self.assertEqual(state['flags']['irina_trust'],1)
        self.assertEqual(state['completed_events'],['a1_completed','m1_completed','slice_completed'])
        self.assertEqual(r.pending_cinematics(),['LS_A1_ToM1','LS_M1_Hall','LS_X1_Final'])
        self.assertEqual(StoryEngine().load_json(r.save_json()),state)

    def test_unknown_presentation_cursor_rejected(self):
        game=StoryEngine();game.start_dialogue('a1_talk_irina');doc=json.loads(game.save_json())
        doc['dialogue_progress']['a1_talk_irina']='missing_node'
        with self.assertRaises(StoryError): StoryEngine().load_json(json.dumps(doc))

    def test_preserve_attempts_on_reload(self):
        self.get_to_signal();self.r.solve_puzzle('a1_solve_signal',['triangle','square','circle'])
        loaded=StoryEngine();loaded.load_json(self.r.save_json())
        self.assertEqual(loaded.state['puzzle_attempts']['a1_solve_signal'],1)


if __name__=='__main__': unittest.main()
