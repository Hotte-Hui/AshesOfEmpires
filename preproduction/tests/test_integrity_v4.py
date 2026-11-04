import unittest
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validate_v3 import load_data
from tools.validate_integrity_v4 import deep_validate
class DeepIntegrityTests(unittest.TestCase):
 def setUp(self):self.data=load_data()
 def test_deep_valid(self):self.assertGreaterEqual(deep_validate()['assets'],25)
 def test_reject_impossible_scene_link(self):
  self.data['scenes']['scenes'][0]['next_scene']='L_X1_Montage'
  with self.assertRaises(ValueError):deep_validate(self.data)
 def test_reject_cross_scene_item(self):
  self.data['items']['items'][0]['scene']='L_M1_Archive'
  with self.assertRaises(ValueError):deep_validate(self.data)
 def test_reject_unsolvable_puzzle(self):
  self.data['puzzles']['puzzles'][0]['solution']=['moon','circle','triangle']
  with self.assertRaises(ValueError):deep_validate(self.data)
 def test_reject_inaccessible_clue(self):
  self.data['quests']['quests'][0]['objectives'][3]['requires']=['a1_inspect_timetable']
  with self.assertRaises(ValueError):deep_validate(self.data)
 def test_reject_looping_dialogue(self):
  self.data['dialogue']['conversations'][0]['nodes'][-1].pop('end')
  self.data['dialogue']['conversations'][0]['nodes'][-1]['next']='irina_01'
  with self.assertRaises(ValueError):deep_validate(self.data)
 def test_reject_wrong_quest_protagonist(self):
  self.data['scenes']['scenes'][1]['protagonist']='alexei'
  with self.assertRaises(ValueError):deep_validate(self.data)
if __name__=='__main__':unittest.main()
